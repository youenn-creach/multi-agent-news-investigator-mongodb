"""Check Atlas connectivity, indexes, and save/read/dedupe of an article."""
from investigator.db import ensure_indexes, get_article, get_client, get_db, save_article

print("ping:", get_client().admin.command("ping"))
ensure_indexes()

url = "https://example.com/test-article"
save_article(url, "Test", "first version")
save_article(url, "Test", "second version")  # same URL: must update, not duplicate

print("copies stored:", get_db().articles.count_documents({"url": url}))
print("text now:", get_article(url)["text"])
print("indexes:", list(get_db().articles.index_information()))

get_db().articles.delete_one({"url": url})  # clean up the test document
