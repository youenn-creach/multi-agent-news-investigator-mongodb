"""MongoDB Atlas access: one shared client, plus helpers to save/read articles."""
import os
from datetime import datetime, timezone
from functools import lru_cache

from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient
from pymongo.database import Database

load_dotenv()

DB_NAME = "news_investigator"


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    """Create the client once; PyMongo manages its own connection pool."""
    return MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=8000)


def get_db() -> Database:
    return get_client()[DB_NAME]


def ensure_indexes() -> None:
    """Idempotent: safe to call on every startup."""
    get_db().articles.create_index([("url", ASCENDING)], unique=True)


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
