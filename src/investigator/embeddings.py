"""Turn text into vectors with Voyage AI (served through MongoDB's endpoint)."""
import time
from typing import Literal

import requests
from investigator.settings import require_env

URL = "https://ai.mongodb.com/v1/embeddings"
MODEL = "voyage-4-lite"
DIMENSIONS = 1024
BATCH = 64


def _post_with_backoff(payload: dict, tries: int = 5) -> requests.Response:
    """The free tier allows only a few requests per minute: on 429, wait and retry."""
    for attempt in range(tries):
        try:
            resp = requests.post(
                URL, headers={"Authorization": f"Bearer {require_env('VOYAGE_API_KEY')}"}, json=payload, timeout=30
            )
        except (requests.Timeout, requests.ConnectionError):
            if attempt == tries - 1:
                raise
            time.sleep(3)  # transient network trouble: try again
            continue
        if resp.status_code != 429 or attempt == tries - 1:
            resp.raise_for_status()
            return resp
        try:
            wait = float(resp.headers.get("Retry-After", 21))
        except ValueError:
            wait = 21.0
        time.sleep(min(wait, 60))


def embed_texts(texts: list[str], input_type: Literal["document", "query"] = "document") -> list[list[float]]:
    """Embed texts. Use "document" for things you store and "query" for things you search with."""
    vectors: list[list[float]] = []
    for i in range(0, len(texts), BATCH):
        resp = _post_with_backoff({"input": texts[i : i + BATCH], "model": MODEL, "input_type": input_type})
        vectors += [d["embedding"] for d in sorted(resp.json()["data"], key=lambda d: d["index"])]
    if len(vectors) != len(texts):  # never silently drop or misalign claims
        raise ValueError(f"embedding service returned {len(vectors)} vectors for {len(texts)} texts")
    return vectors


def embed_text(text: str, input_type: Literal["document", "query"] = "document") -> list[float]:
    return embed_texts([text], input_type)[0]
