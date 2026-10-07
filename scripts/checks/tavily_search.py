"""One real search twice (second must be cached, no credit spent), plus the credit counter."""
from investigator.db import get_db
from investigator.tools.search import _credits_used_this_month, search_news

before = _credits_used_this_month()
for attempt in (1, 2):
    r = search_news.invoke({"query": "European Central Bank interest rate decision"})
    print(f"try{attempt} ok={r['ok']} cached={r.get('cached')} results={len(r.get('results', []))}")
    if r["ok"] and r["results"]:
        first = r["results"][0]
        print("  first:", first["source"], "|", first["title"][:60])
print("credits spent by this test:", _credits_used_this_month() - before)

get_db().searches.delete_many({})  # clean test cache
