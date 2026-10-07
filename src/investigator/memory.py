"""Memory: embed claims and find similar past claims with Atlas Vector Search."""
import time

from pymongo import UpdateOne
from pymongo.operations import SearchIndexModel

from investigator.db import get_db
from investigator.embeddings import DIMENSIONS, embed_text, embed_texts

CLAIMS_INDEX = "claims_vector"


def ensure_vector_index(timeout_s: int = 120) -> None:
    """Create the Atlas Vector Search index on claims.embedding (idempotent) and wait until it is queryable."""
    claims = get_db().claims
    claims.update_one({"_id": "__init__"}, {"$set": {"placeholder": True}}, upsert=True)  # collection must exist
    claims.delete_one({"_id": "__init__"})

    if not any(ix["name"] == CLAIMS_INDEX for ix in claims.list_search_indexes()):
        claims.create_search_index(
            SearchIndexModel(
                name=CLAIMS_INDEX,
                type="vectorSearch",
                definition={
                    "fields": [
                        {"type": "vector", "path": "embedding", "numDimensions": DIMENSIONS, "similarity": "cosine"}
                    ]
                },
            )
        )
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if any(ix["name"] == CLAIMS_INDEX and ix.get("queryable") for ix in claims.list_search_indexes()):
            return
        time.sleep(3)
    raise TimeoutError("Vector index not ready yet; try again in a minute.")


def embed_new_claims() -> list:
    """Embed every claim that has no vector yet. Returns the ids of the claims that were embedded."""
    claims = get_db().claims
    todo = list(claims.find({"embedding": {"$exists": False}}, {"text": 1}))
    if not todo:
        return []
    vectors = embed_texts([c["text"] for c in todo], "document")
    claims.bulk_write([UpdateOne({"_id": c["_id"]}, {"$set": {"embedding": v}}) for c, v in zip(todo, vectors, strict=True)])
    return [c["_id"] for c in todo]


def similar_claims(text: str, k: int = 5, min_score: float = 0.0, vector: list[float] | None = None) -> list[dict]:
    """Past claims closest in meaning to `text`, best first."""
    pipeline = [
        {
            "$vectorSearch": {
                "index": CLAIMS_INDEX,
                "path": "embedding",
                "queryVector": vector or embed_text(text, "query"),
                "numCandidates": 100,
                "limit": k,
            }
        },
        {"$project": {"_id": 0, "text": 1, "status": 1, "article_urls": 1, "score": {"$meta": "vectorSearchScore"}}},
    ]
    return [r for r in get_db().claims.aggregate(pipeline) if r["score"] >= min_score]
