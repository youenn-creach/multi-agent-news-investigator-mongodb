# Project notes for Claude

Multi-agent news investigator (LangGraph + MongoDB Atlas + Voyage embeddings), a public portfolio and learning project. Explain things in plain language, and after each slice say what to read and what the owner should be able to explain. Everything must stay on free tiers. Assume a low-spec laptop (12 GB RAM): local models are a fallback only.

## Working rules
- One branch + PR per slice. Commit locally at the end of each slice; ask before pushing; scan history for secrets before every push. `gh` is installed and logged in: create PRs when asked, never merge unless asked.
- Secrets live only in `.env` (gitignored). Never ask for keys to be pasted in chat; check presence with `grep -c`.
- Keep `LEARNING_LOG.md` updated (one line per slice).
- Live check scripts live in `scripts/` (see scripts/README.md); offline unit tests in `tests/`. Link files by absolute path in chat.

## Architecture (see src/investigator/)
`llm.py` Gemini -> Groq -> Ollama cascade with timeouts; `db.py` Atlas; `tools/` article fetch + Tavily search (cached, credit counter); `extraction.py` claims/entities; `embeddings.py` Voyage via https://ai.mongodb.com/v1/embeddings (voyage-4-lite, 1024 dims, rate-limited: retry built in); `memory.py` Atlas Vector Search on claims; `dedup.py` semantic claim dedup (cosine bands + strict LLM judge + numbers guard); `graph.py` LangGraph hunter -> analyst -> searcher -> broaden -> historian -> skeptic -> writer; `investigation.py` runs and persists; `cli.py`.

## Status (2026-10-07)
PRs #1-#3 merged; PR for `feature/timeline` (dedup, Timeline, themed UI, GIF, audit fixes, 26 tests, MIT license, scripts/ reorganisation) opened. About description/topics set. Owner still has to upload `docs/img/social-preview.png` in repo Settings. Ideas: demo mode for a public deployment, evaluation set, source-reliability scoring.

Project goal to keep in mind (subtly): the repo also showcases MongoDB Atlas, Vector Search and Voyage AI for agentic workloads.

## Quirks
Tests are offline (no DB/keys); `scripts/checks/` are live checks. Run `uv run python -m investigator.setup` after pulling (indexes), `python -m investigator.dedup` for a duplicate dry-run.
`gemini-3.7-flash` / `3.8-flash` often return 503; smart tier uses `gemini-3.5-flash`. Groq structured output needs `method="json_schema"`.
Every LLM call is wrapped in `with_deadline` (llm.py): provider timeouts alone did not stop hangs.
