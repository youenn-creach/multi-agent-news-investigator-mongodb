"""Dedup behaviour on hand-made claims, in a throwaway state (existing data untouched)."""
from investigator.db import get_db
from investigator.extraction import Extraction, ExtractedClaim, save_extraction
from investigator.memory import embed_new_claims, ensure_vector_index

db = get_db()
saved = list(db.claims.find({}))      # back up real data
db.claims.delete_many({})
ensure_vector_index()

def run(label, texts, url):
    r = save_extraction(url, Extraction(claims=[ExtractedClaim(text=t, subject="x", type="event") for t in texts], entities=[]))
    print(f"{label}: {r['claims']} claims in, {r['merged']} merged, total stored = {db.claims.count_documents({})}")

try:
    run("1st article ", ["The ECB raised its key deposit rate by 25 basis points to 2.5% from 2.25%.",
                         "Eurozone inflation was 3.3% in August, with energy inflation at 14.3%.",
                         "The Bank of England kept its rate at 3.75%."], "https://t.test/a")
    print("   (waiting for the search index to catch up...)")
    import time; time.sleep(20)
    run("2nd article ", ["The European Central Bank voted to raise its key deposit rate by 25 basis points to 2.5% from 2.25%.",   # same, reworded -> merge
                         "Eurozone energy inflation increased to 14.3% in August from 10.3% in July.",                       # overlaps but different -> keep
                         "The ECB raised its key deposit rate by 25 basis points to 2.75% from 2.5%.",                       # different number -> keep
                         "A magnitude 6.1 earthquake struck central Italy."], "https://t.test/b")                            # unrelated -> keep
    for c in db.claims.find({}, {"text": 1, "article_urls": 1, "variants": 1}):
        print(f"   {len(c['article_urls'])} article(s), {len(c.get('variants', []))} variant(s): {c['text'][:70]}")
finally:
    db.claims.delete_many({})
    if saved: db.claims.insert_many(saved)   # restore real data
    print("real data restored:", db.claims.count_documents({}), "claims")
