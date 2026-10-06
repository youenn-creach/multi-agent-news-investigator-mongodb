"""One-time setup: create the MongoDB indexes. Safe to run again.

Usage: uv run python -m investigator.setup
"""
from investigator.db import ensure_indexes, get_client
from investigator.memory import ensure_vector_index


def main() -> None:
    get_client().admin.command("ping")
    print("✓ Connected to MongoDB Atlas")
    ensure_indexes()
    print("✓ Unique index on articles.url")
    print("… Creating the Atlas Vector Search index (first time takes 1-2 minutes)")
    ensure_vector_index()
    print("✓ Vector Search index 'claims_vector' is ready")


if __name__ == "__main__":
    main()
