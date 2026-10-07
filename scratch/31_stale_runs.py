from investigator.db import get_db
for d in get_db().investigations.find({"status": {"$ne": "done"}}, {"url": 1, "status": 1, "created_at": 1}):
    print(d["status"], d["created_at"].strftime("%d %b %H:%M"), d["url"][:70])
