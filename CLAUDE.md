# Project notes for Claude

Multi-agent news investigator (LangGraph + MongoDB Atlas + Voyage embeddings), a public portfolio and learning project. Explain things in plain language, and after each slice say what to read and what the owner should be able to explain. Everything must stay on free tiers. Assume a low-spec laptop (12 GB RAM): local models are a fallback only.

## Working rules
- One branch + PR per slice. Commit locally at the end of each slice; ask before pushing; scan history for secrets before every push. `gh` is installed and logged in: create PRs when asked, never merge unless asked.
- Secrets live only in `.env` (gitignored). Never ask for keys to be pasted in chat; check presence with `grep -c`.
- Keep `LEARNING_LOG.md` updated (one line per slice).
- Test scripts live in `scratch/` (numbered). Link files by absolute path in chat.

## Architecture (see src/investigator/)
`llm.py` Gemini -> Groq -> Ollama cascade with timeouts; `db.py` Atlas; `tools/` article fetch + Tavily search (cached, credit counter); `extraction.py` claims/entities; `embeddings.py` Voyage via https://ai.mongodb.com/v1/embeddings (voyage-4-lite, 1024 dims, rate-limited: retry built in); `memory.py` Atlas Vector Search on claims; `dedup.py` semantic claim dedup (cosine bands + strict LLM judge + numbers guard); `graph.py` LangGraph hunter -> analyst -> searcher -> broaden -> historian -> skeptic -> writer; `investigation.py` runs and persists; `cli.py`.

## Status (2026-10-07)
PRs #1 (pipeline), #2 (Streamlit UI), #3 (README) are merged. Semantic claim dedup (`dedup.py`) is committed on `feature/semantic-dedup` (not pushed). Timeline page (`timeline.py`, `page_timeline` in app.py) and README additions were written on top of it but are UNTESTED and uncommitted: next session, run `scratch/12_ui_smoke.py`, test both timeline modes, commit, then push. Also pending: GitHub About description and topics (`gh repo edit`). Further ideas: demo mode for a public deployment, evaluation set, source-reliability scoring.

Project goal to keep in mind (subtly): the repo also showcases MongoDB Atlas, Vector Search and Voyage AI for agentic workloads.

## Quirks
`gemini-3.7-flash` / `3.8-flash` often return 503; smart tier uses `gemini-3.5-flash`. Groq structured output needs `method="json_schema"`.
Every LLM call is wrapped in `with_deadline` (llm.py): provider timeouts alone did not stop hangs.
