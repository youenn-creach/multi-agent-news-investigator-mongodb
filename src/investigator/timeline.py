"""Timelines of claims, built directly from MongoDB aggregation pipelines.

Each timeline is ONE pipeline: find the claims, join them to the articles that made
them (`$lookup`), and sort by date. The topic timeline starts with `$vectorSearch`, so
semantic search and ordinary queries run side by side in the same database and the
same query: no separate vector store to keep in sync.
"""
import json
import re

from investigator.db import get_db
from investigator.embeddings import embed_text
from investigator.memory import CLAIMS_INDEX

# Date of an event: the article's publication date if the extractor found one,
# otherwise the day we fetched it (flagged, so the UI can say so).
_HAS_PUBLISHED = {"$gte": [{"$strLenCP": {"$ifNull": ["$article.published", ""]}}, 10]}

_ATTACH_ARTICLES = [
    {"$unwind": "$article_urls"},  # one event per (claim, article) pair
    {"$lookup": {"from": "articles", "localField": "article_urls", "foreignField": "url", "as": "article"}},
    {"$unwind": "$article"},
    {"$addFields": {
        "date": {"$cond": [_HAS_PUBLISHED, {"$substrCP": ["$article.published", 0, 10]},
                           {"$dateToString": {"format": "%Y-%m-%d", "date": "$article.fetched_at"}}]},
        "date_is_estimate": {"$not": [_HAS_PUBLISHED]},
    }},
    {"$sort": {"date": 1, "created_at": 1}},
    {"$project": {
        "_id": 0, "text": 1, "status": 1, "date": 1, "date_is_estimate": 1, "score": 1,
        "article": {"url": "$article.url", "title": "$article.title", "source": "$article.source"},
    }},
]


def entity_pipeline(entity: dict) -> list[dict]:
    """Claims that mention an entity (by name or alias), as a dated timeline."""
    names = [n for n in [entity["name"], *entity.get("aliases", [])] if len(n) > 2]
    rx = {"$regex": "|".join(re.escape(n) for n in names), "$options": "i"}
    return [{"$match": {"$or": [{"text": rx}, {"variants": rx}, {"subject": rx}]}}, *_ATTACH_ARTICLES]


def topic_pipeline(topic: str, k: int = 20, min_score: float = 0.7) -> list[dict]:
    """Claims closest in MEANING to a free-text topic, as a dated timeline."""
    return [
        {"$vectorSearch": {"index": CLAIMS_INDEX, "path": "embedding", "queryVector": embed_text(topic, "query"),
                           "numCandidates": 100, "limit": k}},
        {"$addFields": {"score": {"$meta": "vectorSearchScore"}}},
        {"$match": {"score": {"$gte": min_score}}},
        *_ATTACH_ARTICLES,
    ]


def entities_with_claims() -> list[dict]:
    """Entities mentioned in at least one claim, most-mentioned first (empty timelines are not offered)."""
    db = get_db()
    haystack = [" ".join([c["text"], c.get("subject", ""), *c.get("variants", [])]).lower()
                for c in db.claims.find({}, {"text": 1, "subject": 1, "variants": 1})]
    out = []
    for e in db.entities.find({}, {"name": 1, "aliases": 1, "type": 1}):
        names = [n.lower() for n in [e["name"], *e.get("aliases", [])] if len(n) > 2]
        e["mentions"] = sum(any(n in h for n in names) for h in haystack)
        if e["mentions"]:
            out.append(e)
    return sorted(out, key=lambda e: -e["mentions"])


def run(pipeline: list[dict]) -> list[dict]:
    return list(get_db().claims.aggregate(pipeline))


def describe(pipeline: list[dict]) -> str:
    """The pipeline as readable JSON (the 1024-number query vector is elided)."""
    def clean(x):
        if isinstance(x, dict):
            return {k: ("<1024-dimension query vector>" if k == "queryVector" else clean(v)) for k, v in x.items()}
        if isinstance(x, list):
            return [clean(i) for i in x]
        return x
    return json.dumps(clean(pipeline), indent=2, default=str)
