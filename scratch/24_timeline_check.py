from investigator import timeline
from investigator.db import get_db

ents = list(get_db().entities.find({}).sort("article_urls", -1).limit(3))
for e in ents:
    ev = timeline.run(timeline.entity_pipeline(e))
    print(f"ENTITY {e['name']}: {len(ev)} events, dates {sorted({x['date'] for x in ev})}")
for topic in ["central bank raises borrowing costs", "football transfer"]:
    ev = timeline.run(timeline.topic_pipeline(topic))
    print(f"TOPIC {topic!r}: {len(ev)} events", [(x['date'], round(x['score'], 2), x['text'][:45]) for x in ev[:2]])
print(timeline.describe(timeline.topic_pipeline("x"))[:420])
