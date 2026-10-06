"""Look at real claim pairs: how similar are true duplicates vs. different claims?"""
import re
import numpy as np
from investigator.db import get_db

claims = list(get_db().claims.find({"embedding": {"$exists": True}}, {"text": 1, "embedding": 1, "article_urls": 1}))
E = np.array([c["embedding"] for c in claims]); E /= np.linalg.norm(E, axis=1, keepdims=True)
S = E @ E.T
nums = lambda t: sorted(re.findall(r"\d+(?:[.,]\d+)?", t))
pairs = [(S[i, j], i, j) for i in range(len(claims)) for j in range(i + 1, len(claims))]
pairs.sort(reverse=True)
print(f"{len(claims)} claims; top pairs by cosine (N = same numbers?)")
for s, i, j in pairs[:22]:
    same = "N=" if nums(claims[i]["text"]) == nums(claims[j]["text"]) else "N≠"
    print(f"{s:.3f} {same} | {claims[i]['text'][:75]}\n              | {claims[j]['text'][:75]}")
