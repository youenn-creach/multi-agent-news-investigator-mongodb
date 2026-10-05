"""Extract claims/entities from a real article, save them twice (must not duplicate)."""
from investigator.db import get_db
from investigator.extraction import extract, save_extraction
from investigator.tools.articles import fetch_article_data

URL = "https://en.wikipedia.org/wiki/2022_Russian_invasion_of_Ukraine"
art = fetch_article_data(URL)
assert art["ok"], art

result = extract(art["title"], art["text"])
print(f"{len(result.claims)} claims, {len(result.entities)} entities")
for c in result.claims[:5]:
    print(f"  [{c.type}] {c.text[:110]}")
print("  entities:", [e.name for e in result.entities][:8])

save_extraction(URL, result)
save_extraction(URL, result)  # same data again: counts must not grow
db = get_db()
print("stored claims:", db.claims.count_documents({}), "| stored entities:", db.entities.count_documents({}))

for col in ("claims", "entities", "articles"):
    db[col].delete_many({})  # clean test data
