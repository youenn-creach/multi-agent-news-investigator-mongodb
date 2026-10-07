from collections import Counter
from investigator.db import get_db
total = dups = 0
for c in get_db().claims.find({}, {"evidence": 1, "text": 1}):
    keys = Counter((e["verdict"], e["source"], e["article"]) for e in c.get("evidence", []))
    total += sum(keys.values()); dups += sum(n - 1 for n in keys.values() if n > 1)
print(f"evidence entries: {total}, duplicates within a claim: {dups}")
