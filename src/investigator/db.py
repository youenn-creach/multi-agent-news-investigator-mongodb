"""MongoDB Atlas access: one shared client, plus helpers to save/read articles."""
from datetime import datetime, timezone
from functools import lru_cache

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database

from investigator.settings import require_env

DB_NAME = "news_investigator"


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    """Create the client once; PyMongo manages its own connection pool."""
    return MongoClient(require_env("MONGODB_URI"), serverSelectionTimeoutMS=8000)


def get_db() -> Database:
    return get_client()[DB_NAME]


def ensure_indexes() -> None:
    """Idempotent: safe to call on every startup."""
    db = get_db()
    db.articles.create_index([("url", ASCENDING)], unique=True)
    db.claims.create_index([("key", ASCENDING)], unique=True)  # claims are upserted by key
    db.entities.create_index([("key", ASCENDING)], unique=True)
    db.claims.create_index([("article_urls", ASCENDING)])  # timeline: claims -> articles
    db.investigations.create_index([("created_at", DESCENDING)])  # history page
    # MongoDB deletes cached searches by itself after 7 days (TTL index)
    db.searches.create_index([("created_at", ASCENDING)], expireAfterSeconds=7 * 24 * 3600)


def save_article(url: str, title: str, text: str, **extra) -> None:
    """Insert or update an article, keyed by its URL (so re-fetching never duplicates)."""
    now = datetime.now(timezone.utc)
    get_db().articles.update_one(
        {"url": url},
        {
            "$set": {"title": title, "text": text, "updated_at": now, **extra},
            "$setOnInsert": {"fetched_at": now},
        },
        upsert=True,
    )


def get_article(url: str) -> dict | None:
    return get_db().articles.find_one({"url": url})
