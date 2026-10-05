from investigator.tools.search import search_data
from investigator.tools.articles import fetch_article_data
for r in search_data("European Central Bank interest rate decision", max_results=6)["results"]:
    a = fetch_article_data(r["url"])
    print("OK  " if a["ok"] else "FAIL", r["url"])
