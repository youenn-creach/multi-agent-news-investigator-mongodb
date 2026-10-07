"""Fetch a real article twice (second time must come from the cache), plus bad inputs."""
import time

from investigator.db import get_db
from investigator.tools.articles import fetch_article

URLS = [
    "https://en.wikipedia.org/wiki/Fact-checking",  # real page
    "not-a-url",
    "https://example.invalid/nothing",  # cannot be downloaded
    "https://example.com",  # downloads, but has no article text
]

for url in URLS:
    for attempt in (1, 2):
        start = time.time()
        r = fetch_article.invoke({"url": url})
        took = time.time() - start
        if r["ok"]:
            print(f"OK   try{attempt} {took:4.1f}s cached={r['cached']} chars={len(r['text'])} title={r['title']!r}")
        else:
            print(f"FAIL try{attempt} {took:4.1f}s {r['error']}")
        if not r["ok"]:
            break

get_db().articles.delete_many({})  # clean up test data
