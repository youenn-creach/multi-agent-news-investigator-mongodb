from investigator.db import get_db
db = get_db()
print("claims:", db.claims.count_documents({}), "| merged (have variants):", db.claims.count_documents({"variants": {"$exists": True}}))
