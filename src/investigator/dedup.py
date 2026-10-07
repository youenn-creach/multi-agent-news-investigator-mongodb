"""Semantic claim deduplication.

Two claims worded differently can state the same fact. Merging them keeps the
memory clean, but merging two *different* claims would corrupt a fact-checker, so:

  cosine >= AUTO_MERGE and same numbers  -> same claim (no LLM needed)
  GREY_ZONE <= cosine < AUTO_MERGE       -> a strict LLM judge decides
  below GREY_ZONE                        -> different claims

Thresholds were chosen by looking at real claim pairs (scratch/14_dup_explore.py).
Atlas reports cosine as (1 + cos) / 2, hence the conversion.
"""
import re

import numpy as np
from pydantic import BaseModel, Field

from investigator.db import get_db
from investigator.llm import get_structured_llm
from investigator.memory import CLAIMS_INDEX

AUTO_MERGE = 0.985
GREY_ZONE = 0.93
JUDGE_AT_MOST = 2  # LLM calls per new claim, at most


class SameClaim(BaseModel):
    same: bool = Field(description="True only if both statements assert exactly the same facts.")
    reason: str = Field(description="One short sentence.")


JUDGE_PROMPT = """Are these two statements from news articles the SAME claim?

A: {a}
B: {b}

Answer true only if they assert exactly the same facts: same entities, same numbers, same dates, same direction of change. If one contains an extra fact the other lacks (for example an earlier value, or an additional figure), or any number differs, answer false. Different wording alone does not make them different."""


def numbers(text: str) -> list[str]:
    """Digits in a text, as a sorted list: a cheap guard, since embeddings are weak on numbers."""
    return sorted(re.findall(r"\d+(?:[.,]\d+)?", text))


def cosine(a: list[float], b: list[float]) -> float:
    a, b = np.asarray(a), np.asarray(b)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def judge_same(a: str, b: str) -> bool:
    try:
        return get_structured_llm("cheap", SameClaim).invoke(JUDGE_PROMPT.format(a=a, b=b)).same
    except Exception:
        return False  # when in doubt, keep the claims separate


def is_duplicate(text: str, other_text: str, cos: float) -> bool:
    """The three-band rule above."""
    if cos >= AUTO_MERGE and numbers(text) == numbers(other_text):
        return True
    if cos >= GREY_ZONE:
        return judge_same(text, other_text)
    return False


def find_duplicate(text: str, vector: list[float]) -> dict | None:
    """Closest stored claim that is really the same claim, or None."""
    pipeline = [
        {"$vectorSearch": {"index": CLAIMS_INDEX, "path": "embedding", "queryVector": vector,
                           "numCandidates": 50, "limit": 3}},
        {"$project": {"text": 1, "article_urls": 1, "score": {"$meta": "vectorSearchScore"}}},
    ]
    judged = 0
    for hit in get_db().claims.aggregate(pipeline):
        cos = 2 * hit["score"] - 1
        if cos < GREY_ZONE:
            break  # results are sorted: nothing closer remains
        if cos < AUTO_MERGE or numbers(text) != numbers(hit["text"]):
            if judged >= JUDGE_AT_MOST:
                break
            judged += 1
        if is_duplicate(text, hit["text"], cos):
            return hit
    return None


# ---------- one-off clean-up of duplicates that were stored before dedup existed ----------
def merge_existing(apply: bool = False, only_ids: set | None = None, quiet: bool = False) -> list[list[dict]]:
    """Find groups of duplicate claims already in the database; merge them if apply=True.

    `only_ids` limits the search to pairs that involve at least one of those claims (used right
    after new claims were embedded late); the older claim of a group is always the one kept.

    Usage: uv run python -m investigator.dedup          (dry run: only prints the plan)
           uv run python -m investigator.dedup --apply  (merges)
    """
    from investigator.extraction import status_from_evidence

    coll = get_db().claims
    claims = list(coll.find({"embedding": {"$exists": True}}).sort("created_at", 1))
    parent = list(range(len(claims)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            if root(i) == root(j):
                continue
            if only_ids is not None and claims[i]["_id"] not in only_ids and claims[j]["_id"] not in only_ids:
                continue
            cos = cosine(claims[i]["embedding"], claims[j]["embedding"])
            if cos >= GREY_ZONE and is_duplicate(claims[i]["text"], claims[j]["text"], cos):
                parent[root(j)] = root(i)  # the older claim stays

    groups: dict[int, list[dict]] = {}
    for i, c in enumerate(claims):
        groups.setdefault(root(i), []).append(c)
    groups = [g for g in groups.values() if len(g) > 1]

    for g in groups:
        keep, rest = g[0], g[1:]
        if not quiet:
            print(f"KEEP  {keep['text'][:90]}")
            for r in rest:
                print(f"  ←   {r['text'][:90]}")
        if not apply:
            continue
        urls = sorted({u for c in g for u in c["article_urls"]})
        variants = sorted({v for c in g for v in c.get("variants", [])} | {r["text"] for r in rest})
        evidence = [e for c in g for e in c.get("evidence", [])]
        evidence = list({(e["verdict"], e["source"], e["article"]): e for e in evidence}.values())
        coll.update_one({"_id": keep["_id"]}, {"$set": {
            "article_urls": urls, "variants": variants, "evidence": evidence, "status": status_from_evidence(evidence)}})
        coll.delete_many({"_id": {"$in": [r["_id"] for r in rest]}})
    if not quiet:
        print(f"\n{len(groups)} group(s) of duplicates; {'merged' if apply else 'dry run: nothing changed (add --apply to merge)'}")
    return groups


def tidy_evidence(apply: bool = False) -> int:
    """Remove repeated evidence entries inside a claim (left by runs made before evidence was de-duplicated)."""
    from investigator.extraction import status_from_evidence

    coll, removed = get_db().claims, 0
    for c in coll.find({"evidence.1": {"$exists": True}}, {"evidence": 1}):
        unique = list({(e["verdict"], e["source"], e["article"]): e for e in c["evidence"]}.values())
        if len(unique) < len(c["evidence"]):
            removed += len(c["evidence"]) - len(unique)
            if apply:
                coll.update_one({"_id": c["_id"]}, {"$set": {"evidence": unique, "status": status_from_evidence(unique)}})
    print(f"{removed} repeated evidence entr{'y' if removed == 1 else 'ies'} {'removed' if apply else 'found (dry run)'}")
    return removed


if __name__ == "__main__":
    import sys

    merge_existing(apply="--apply" in sys.argv)
    tidy_evidence(apply="--apply" in sys.argv)
