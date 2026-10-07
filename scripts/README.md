# Scripts

Small helper scripts, separate from the unit tests in `tests/` (which are offline and run with `uv run pytest`).
Most of these talk to real services (MongoDB Atlas, LLM providers, Tavily, Voyage AI), so they need a filled-in `.env`
and may use a little free-tier quota. Run them from the project root.

| Folder | What | Example |
|---|---|---|
| `checks/` | Live checks of each piece against real services, written while building the project | `uv run python scripts/checks/llm_cascade.py` |
| `assets/` | Regenerate the README screenshots, demo GIF and social preview (need the app running and `playwright`) | `uv run --with playwright python scripts/assets/screenshots.py` |
| `calibration/` | The analysis behind the claim-deduplication thresholds | `uv run python scripts/calibration/dedup_thresholds.py` |
| `experiments/` | The very first Gemini API calls, kept as a record of where the project started | |

Some checks temporarily replace the contents of a collection and restore it afterwards (`dedup_behaviour.py`,
`late_embedding_merge.py`); do not run them against data you cannot afford to lose.
