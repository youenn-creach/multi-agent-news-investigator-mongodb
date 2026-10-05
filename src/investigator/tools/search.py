"""Tools: web search via Tavily. Every search is cached in MongoDB (credits are scarce)."""
import hashlib
import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from urllib.parse import urlparse

from dotenv import load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient

from investigator.db import get_db

load_dotenv()

CACHE_TTL = timedelta(days=7)
SNIPPET_CHARS = 500
MONTHLY_BUDGET = 1000  # free tier; we refuse to search past this


@lru_cache(maxsize=1)
def _client() -> TavilyClient:
    return TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def _credits_used_this_month() -> int:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    doc = get_db().usage.find_one({"_id": f"tavily-{month}"})
    return doc["credits"] if doc else 0


def _record_credit() -> None:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    get_db().usage.update_one({"_id": f"tavily-{month}"}, {"$inc": {"credits": 1}}, upsert=True)


def search_data(query: str, max_results: int = 5, exclude_domain: str | None = None) -> dict:
    """Plain-Python search. Never raises. Cached for CACHE_TTL."""
    key = hashlib.sha256(f"{query}|{max_results}|{exclude_domain}".encode()).hexdigest()
    now = datetime.now(timezone.utc)

    cached = get_db().searches.find_one({"_id": key})
    if cached and now - cached["created_at"].replace(tzinfo=timezone.utc) < CACHE_TTL:
        return {"ok": True, "cached": True, "query": query, "results": cached["results"]}

    if _credits_used_this_month() >= MONTHLY_BUDGET:
        return {"ok": False, "error": "Monthly search budget used up. Work with the sources you already have."}

    try:
        # Tavily's own exclude option degraded result quality, so over-fetch and filter locally.
        raw = _client().search(query, topic="news", max_results=max_results + (3 if exclude_domain else 0))
    except Exception as e:
        return {"ok": False, "error": f"Search failed: {type(e).__name__}"}
    _record_credit()

    results = [
        {
            "title": r.get("title", ""),
            "url": r["url"],
            "source": urlparse(r["url"]).netloc.removeprefix("www."),
            "snippet": r.get("content", "")[:SNIPPET_CHARS],
            "published": r.get("published_date"),
        }
        for r in raw.get("results", [])
        if not exclude_domain or exclude_domain not in urlparse(r["url"]).netloc
    ][:max_results]
    get_db().searches.replace_one(
        {"_id": key}, {"_id": key, "query": query, "results": results, "created_at": now}, upsert=True
    )
    return {"ok": True, "cached": False, "query": query, "results": results}


@tool
def search_news(query: str) -> dict:
    """Search recent news for coverage of a topic, event or claim.

    Use this to find what OTHER outlets reported about the same story, to
    corroborate or contradict a claim. Write a specific query (names, place,
    event), not a full sentence. Returns titles, sources and short snippets;
    use fetch_article to read one in full. Searches are limited: do not repeat
    a query, and make at most 3-4 searches per investigation.
    """
    return search_data(query)


@tool
def find_original_source(claim: str, article_domain: str) -> dict:
    """Look for the ORIGINAL source of a claim: a primary document, official
    statement, press release or the first outlet to report it.

    Use this when an article repeats a claim without a clear source. Pass the
    claim in a few words, and the domain of the article you are investigating
    (e.g. "bbc.co.uk") so that the article itself is excluded from results.
    """
    return search_data(f"{claim} official statement original report", exclude_domain=article_domain)
