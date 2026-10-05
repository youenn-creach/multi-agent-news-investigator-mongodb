"""Turn text into vectors with Voyage AI (served through MongoDB's endpoint)."""
import os
import time
from typing import Literal

import requests
from dotenv import load_dotenv

load_dotenv()

URL = "https://ai.mongodb.com/v1/embeddings"
MODEL = "voyage-4-lite"
DIMENSIONS = 1024
BATCH = 64


def _post_with_backoff(payload: dict, tries: int = 5) -> requests.Response:
    """The free tier allows only a few requests per minute: on 429, wait and retry."""
    for attempt in range(tries):
        resp = requests.post(
            URL,
            headers={"Authorization": f"Bearer {os.environ['VOYAGE_API_KEY']}"},
            json=payload,
            timeout=30,
        )
        if resp.status_code != 429 or attempt == tries - 1:
            resp.raise_for_status()
            return resp
        time.sleep(float(resp.headers.get("Retry-After", 21)))


def embed_texts(texts: list[str], input_type: Literal["document", "query"] = "document") -> list[list[float]]:
    """Embed texts. Use "document" for things you store and "query" for things you search with."""
    vectors: list[list[float]] = []
    for i in range(0, len(texts), BATCH):
        resp = _post_with_backoff({"input": texts[i : i + BATCH], "model": MODEL, "input_type": input_type})
        vectors += [d["embedding"] for d in sorted(resp.json()["data"], key=lambda d: d["index"])]
    return vectors


def embed_text(text: str, input_type: Literal["document", "query"] = "document") -> list[float]:
    return embed_texts([text], input_type)[0]
