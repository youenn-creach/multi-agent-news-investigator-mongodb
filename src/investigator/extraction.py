"""Analyst step: pull checkable claims and named entities out of an article.

Claims and entities live in their own collections (not embedded in the article)
because the same entity or claim shows up across many investigations.
"""
import re
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from investigator.db import get_db
from investigator.llm import get_structured_llm

ARTICLE_CHARS = 8_000

ClaimType = Literal["statistic", "quote", "event", "causal", "other"]
EntityType = Literal["person", "organization", "place", "other"]


class ExtractedClaim(BaseModel):
    text: str = Field(description="One self-contained, checkable factual statement, rewritten so it makes sense without the article.")
    subject: str = Field(description="Main entity the claim is about.")
    type: ClaimType


class ExtractedEntity(BaseModel):
    name: str = Field(description="Canonical full name.")
    type: EntityType
    aliases: list[str] = Field(default_factory=list, description="Other names used in the article.")


class Extraction(BaseModel):
    claims: list[ExtractedClaim] = Field(description="At most 8 of the most important checkable claims. Skip opinions and predictions.")
    entities: list[ExtractedEntity]


PROMPT = """You are a careful fact-checking analyst. From the news article below, extract:
1. The most important factual CLAIMS that could be verified against other sources (numbers, dates, quotes, events, causes). No opinions.
2. The named ENTITIES (people, organizations, places) involved.

Article title: {title}
Article text:
{text}"""


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()


def extract(title: str, text: str) -> Extraction:
    llm = get_structured_llm("smart", Extraction)
    return llm.invoke(PROMPT.format(title=title, text=text[:ARTICLE_CHARS]))


def save_extraction(article_url: str, extraction: Extraction) -> dict:
    """Upsert entities by normalized name; claims by normalized text. Returns counts."""
    db = get_db()
    now = datetime.now(timezone.utc)

    for e in extraction.entities:
        db.entities.update_one(
            {"key": normalize(e.name)},
            {
                "$set": {"name": e.name, "type": e.type},
                "$addToSet": {"aliases": {"$each": e.aliases}, "article_urls": article_url},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
    for c in extraction.claims:
        db.claims.update_one(
            {"key": normalize(c.text)},
            {
                "$set": {"text": c.text, "subject": c.subject, "type": c.type},
                "$addToSet": {"article_urls": article_url},
                "$setOnInsert": {"status": "unverified", "evidence": [], "created_at": now},
            },
            upsert=True,
        )
    return {"claims": len(extraction.claims), "entities": len(extraction.entities)}
