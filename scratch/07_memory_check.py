"""Store a few claims, embed them, and check that search works by MEANING, not keywords."""
from investigator.db import get_db
from investigator.extraction import Extraction, ExtractedClaim, save_extraction
from investigator.memory import embed_new_claims, ensure_vector_index, similar_claims

CLAIMS = [
    "The European Central Bank raised interest rates by 25 basis points in July.",
    "Inflation in the eurozone fell to 2.4 percent in June.",
    "A magnitude 6.1 earthquake struck central Italy on Tuesday.",
    "Apple announced a new iPhone with a faster chip.",
    "The football club signed a striker for 80 million euros.",
]
save_extraction("https://example.test/a", Extraction(
    claims=[ExtractedClaim(text=t, subject="x", type="event") for t in CLAIMS], entities=[]))

print("embedded:", embed_new_claims())
print("waiting for the vector index (first run takes a minute or two)...")
ensure_vector_index()

# Note: no keyword in common with the stored claims
for query in ["Eurozone central bank hikes borrowing costs", "Italian quake hits region", "Soccer transfer record fee"]:
    best = similar_claims(query, k=2)
    print(f"\n{query!r}")
    for r in best:
        print(f"  {r['score']:.2f}  {r['text']}")

get_db().claims.delete_many({})
get_db().entities.delete_many({})
