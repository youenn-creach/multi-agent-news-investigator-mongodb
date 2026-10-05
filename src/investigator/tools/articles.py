"""Tool: fetch a news article by URL, extract clean text, cache it in MongoDB."""
from urllib.parse import urlparse

import trafilatura
from langchain_core.tools import tool

from investigator.db import get_article, save_article

MAX_CHARS = 12_000  # keep prompts small: free-tier token limits are tight
MIN_CHARS = 200  # below this the page is almost certainly a paywall/cookie wall


def fetch_article_data(url: str) -> dict:
    """Plain-Python version. Never raises: returns {"ok": False, "error": ...} on failure."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return {"ok": False, "url": url, "error": "Not a valid http(s) URL."}

    cached = get_article(url)
    if cached:
        return _result(cached, cached=True)

    html = trafilatura.fetch_url(url)
    if not html:
        return {"ok": False, "url": url, "error": "Could not download the page (blocked, offline, or not found)."}

    doc = trafilatura.bare_extraction(html, url=url, with_metadata=True)
    text = (doc.text if doc else None) or ""
    if len(text) < MIN_CHARS:
        return {"ok": False, "url": url, "error": "Page downloaded but no article text found (likely a paywall or JavaScript-only page)."}

    save_article(
        url,
        title=doc.title or "",
        text=text,
        author=doc.author,
        published=doc.date,
        source=doc.sitename or parsed.netloc,
    )
    return _result(get_article(url), cached=False)


def _result(article: dict, cached: bool) -> dict:
    text = article["text"]
    return {
        "ok": True,
        "url": article["url"],
        "title": article.get("title", ""),
        "source": article.get("source"),
        "author": article.get("author"),
        "published": article.get("published"),
        "text": text[:MAX_CHARS],
        "truncated": len(text) > MAX_CHARS,
        "cached": cached,
    }


@tool
def fetch_article(url: str) -> dict:
    """Download a news article and return its title, source, author, date and text.

    Use this FIRST when you are given an article URL to investigate, and again
    for any other article URL you want to read in full. Do not use it to search
    for articles. If it returns ok=False, read the error, and do not retry the
    same URL: continue with other sources instead.
    """
    return fetch_article_data(url)
