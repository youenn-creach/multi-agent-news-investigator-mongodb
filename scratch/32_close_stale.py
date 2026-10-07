"""One-off: mark investigations that were left 'running' by a stopped process as failed."""
from datetime import datetime, timedelta, timezone
from investigator.db import get_db
r = get_db().investigations.update_many(
    {"status": "running", "created_at": {"$lt": datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=30)}},
    {"$set": {"status": "failed", "error": "interrupted: the process stopped before the investigation finished"}})
print("closed:", r.modified_count)
