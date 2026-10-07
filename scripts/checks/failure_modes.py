"""Run the whole pipeline on inputs that should fail gracefully (no LLM calls are needed)."""
from investigator.db import get_db
from investigator.investigation import run_investigation

BAD = ["not-a-url", "https://example.invalid/nothing", "http://127.0.0.1:8501/", "  https://example.com  "]
for url in BAD:
    r = run_investigation(url)
    rep = r["report"]
    print(f"{url!r:42} -> {rep['verdict']:12} | {rep['summary'][:70]}")
for url in ("not-a-url", "https://example.invalid/nothing", "http://127.0.0.1:8501/", "https://example.com"):
    get_db().investigations.delete_many({"url": url})   # keep the History page clean
