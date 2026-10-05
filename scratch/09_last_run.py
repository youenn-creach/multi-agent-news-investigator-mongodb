from investigator.db import get_db
d = get_db().investigations.find_one(sort=[("created_at", -1)])
print(d["status"], "| errors:", d.get("errors"))
print("\nSOURCES:")
for s in d["sources"]: print(" ", s["source"], "|", s["title"][:70], "|", s["snippet"][:100].replace("\n"," "))
print("\nCLAIMS + VERDICTS:")
v = {x["claim_index"]: x for x in d["verdicts"]}
for i, c in enumerate(d["claims"]):
    print(f" {i}. {c['text'][:100]}\n    -> {v.get(i,{}).get('verdict')} {v.get(i,{}).get('note','')[:110]}")
