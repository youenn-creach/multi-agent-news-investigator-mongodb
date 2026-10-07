"""Offline tests: no network, no MongoDB, no API keys needed. Run with: uv run pytest"""
import time

import pytest
from langchain_core.runnables import RunnableLambda

from investigator import dedup, graph, timeline
from investigator.extraction import Extraction, ExtractedClaim, normalize, status_from_evidence
from investigator.llm import with_deadline
from investigator.tools import search
from investigator.tools.articles import fetch_article_data, is_public_url


# ---------- text helpers ----------
def test_normalize_ignores_case_punctuation_and_spacing():
    assert normalize("The ECB  raised rates, to 2.5%!") == normalize("the ecb raised rates to 25")
    assert normalize("!!!") == ""


def test_numbers_guard_catches_different_figures():
    assert dedup.numbers("raised to 2.5% from 2.25%") != dedup.numbers("raised to 2.75% from 2.5%")
    assert dedup.numbers("rate was 2.5%") == dedup.numbers("The rate stood at 2.5 percent")


# ---------- claim status ----------
@pytest.mark.parametrize("verdicts,expected", [
    ([], "unverified"),
    (["unclear"], "unverified"),
    (["supports"], "corroborated"),
    (["supports", "supports"], "corroborated"),
    (["contradicts"], "contradicted"),
    (["supports", "contradicts"], "disputed"),
])
def test_status_from_evidence(verdicts, expected):
    assert status_from_evidence([{"verdict": v} for v in verdicts]) == expected


# ---------- source naming in notes ----------
SOURCES = [{"source": "euronews.com"}, {"source": "reuters.com"}, {"source": "cnbc.com"}]


def test_name_sources_rewrites_list_numbers():
    assert graph._name_sources("Sources [0] and [1] agree.", SOURCES) == "Sources euronews.com and reuters.com agree."
    assert graph._name_sources("Sources conflict (sources 1,2).", SOURCES) == "Sources conflict (reuters.com, cnbc.com)."


def test_name_sources_leaves_real_numbers_alone():
    note = "Deposit rate 2.5% (2.25%) unchanged; see source 9."
    assert graph._name_sources(note, SOURCES) == note


# ---------- deduplication rule ----------
def test_duplicate_rule_bands(monkeypatch):
    monkeypatch.setattr(dedup, "judge_same", lambda a, b: True)
    assert dedup.is_duplicate("rate 2.5%", "rate was 2.5%", 0.99)  # very close, same numbers: no judge needed
    assert not dedup.is_duplicate("rate 2.5%", "rate 2.5%", 0.50)  # too far apart, even if the judge would say yes
    assert dedup.is_duplicate("a", "b", 0.95)  # grey zone: the judge decides

    monkeypatch.setattr(dedup, "judge_same", lambda a, b: False)
    assert not dedup.is_duplicate("a", "b", 0.95)
    assert not dedup.is_duplicate("rate 2.5%", "rate 2.75%", 0.99)  # different numbers: goes to the judge, which refuses


def test_cosine():
    assert dedup.cosine([1, 0], [1, 0]) == pytest.approx(1.0)
    assert dedup.cosine([1, 0], [0, 1]) == pytest.approx(0.0)


# ---------- LLM deadline ----------
def test_stuck_provider_is_abandoned_and_fallback_answers():
    stuck = RunnableLambda(lambda x: time.sleep(30) or "never")
    ok = RunnableLambda(lambda x: "fallback")
    started = time.time()
    assert with_deadline(stuck, 1).with_fallbacks([with_deadline(ok, 1)]).invoke("hi") == "fallback"
    assert time.time() - started < 5


# ---------- article fetching guard ----------
@pytest.mark.parametrize("url", ["http://127.0.0.1/x", "http://localhost/x", "http://169.254.169.254/latest", "http://192.168.1.1/"])
def test_private_addresses_are_refused(url):
    assert not is_public_url(url)
    result = fetch_article_data(url)
    assert result["ok"] is False and "private" in result["error"].lower()


def test_bad_urls_are_rejected_without_touching_the_database():
    assert fetch_article_data("not-a-url")["ok"] is False
    assert fetch_article_data("ftp://example.com/file")["ok"] is False


# ---------- search helpers ----------
def test_domain_exclusion_matches_subdomains_but_not_lookalikes():
    assert search._is_domain("www.bbc.com", "bbc.com")
    assert search._is_domain("news.bbc.com", "bbc.com")
    assert not search._is_domain("notbbc.com", "bbc.com")
    assert not search._is_domain("bbc.com.evil.io", "bbc.com")
    assert not search._is_domain("anything.com", None)


# ---------- graph routing ----------
def test_thin_coverage_triggers_one_extra_search():
    assert graph.needs_more_sources({"claims": [{"text": "x"}], "sources": []}) == "broaden"
    assert graph.needs_more_sources({"claims": [{"text": "x"}], "sources": [{}, {}]}) == "historian"
    assert graph.needs_more_sources({"claims": [], "sources": []}) == "historian"  # nothing to search for


def test_unreadable_article_still_yields_a_report_without_any_llm_call():
    state = {"url": "u", "article": {"ok": False, "error": "blocked"}, "errors": []}
    report = graph.writer(state)["report"]
    assert report["verdict"] == "unverifiable" and "blocked" in report["summary"]


# ---------- timeline pipelines ----------
def test_entity_pipeline_escapes_regex_and_handles_no_names():
    import re

    pipe = timeline.entity_pipeline({"name": "AT&T (Inc.)", "aliases": []})
    assert pipe[0]["$match"]["$or"][0]["text"]["$regex"] == re.escape("AT&T (Inc.)")  # brackets and dots are literal
    assert timeline.entity_pipeline({"name": "ab", "aliases": []}) == [{"$match": {"_id": None}}]  # matches nothing


def test_pipeline_description_hides_the_vector():
    pipe = [{"$vectorSearch": {"queryVector": [0.1] * 1024, "limit": 3}}]
    text = timeline.describe(pipe)
    assert "0.1" not in text and "query vector" in text


# ---------- schemas ----------
def test_extraction_schema_rejects_unknown_claim_type():
    with pytest.raises(Exception):
        ExtractedClaim(text="x", subject="y", type="rumour")
    assert Extraction(claims=[], entities=[]).claims == []
