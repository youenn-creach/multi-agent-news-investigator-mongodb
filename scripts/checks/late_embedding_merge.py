"""Claims stored without vectors (embedding service was down) must be merged once they are embedded."""
from datetime import datetime, timedelta, timezone
from investigator.db import get_db
from investigator.dedup import merge_existing
from investigator.memory import embed_new_claims

db = get_db()
backup = list(db.claims.find({}))
db.claims.delete_many({})
now = datetime.now(timezone.utc)
mk = lambda t, k, m, u: {"text": t, "key": k, "subject": "x", "type": "event", "status": "unverified", "evidence": [], "article_urls": [u], "created_at": now - timedelta(minutes=m)}
try:
    db.claims.insert_many([
        mk("The Bank of England kept its benchmark rate at 3.75% on Thursday.", "a", 5, "https://t.test/1"),
        mk("On Thursday the Bank of England left its benchmark interest rate unchanged at 3.75%.", "b", 1, "https://t.test/2"),
        mk("A magnitude 6.1 earthquake struck central Italy.", "c", 1, "https://t.test/2"),
    ])
    ids = embed_new_claims()
    merge_existing(apply=True, only_ids=set(ids), quiet=True)
    left = list(db.claims.find({}, {"text": 1, "article_urls": 1, "variants": 1}))
    print(f"embedded {len(ids)}; claims left: {len(left)} (expected 2)")
    for c in left: print("  ", len(c["article_urls"]), "article(s),", len(c.get("variants", [])), "variant(s):", c["text"][:60])
finally:
    db.claims.delete_many({})
    db.claims.insert_many(backup)
    print("real data restored:", db.claims.count_documents({}))
