from collections import Counter
from investigator.db import get_db
from investigator.investigation import run_investigation

URL = "https://www.cnbc.com/2026/09/10/ecb-interest-rate-hike-lagarde-iran.html"
def stats():
    ev = [(e["verdict"], e["source"], e["article"]) for c in get_db().claims.find({}, {"evidence": 1}) for e in c.get("evidence", [])]
    dups = sum(n - 1 for n in Counter(ev).values() if n > 1)
    return len(ev), dups, get_db().claims.count_documents({})
print("before: evidence entries, duplicate entries, claims =", stats())
r = run_investigation(URL)
print("after : evidence entries, duplicate entries, claims =", stats())
mem = r["report"]["previously_seen"]
print("memory items:", len(mem), "| any listing THIS article as earlier:", any(URL in m["earlier_articles"] for m in mem))
print("verdict:", r["report"]["verdict"], "| claims:", len(r["claims"]), "| verdicts:", len(r["verdicts"]), "| note sample:", r["verdicts"][0]["note"][:90] if r["verdicts"] else None)
