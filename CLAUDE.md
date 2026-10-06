# Project notes for Claude

Multi-agent news investigator (LangGraph + MongoDB Atlas + Voyage embeddings), a public portfolio and learning project. Explain things in plain language, and after each slice say what to read and what the owner should be able to explain. Everything must stay on free tiers. Assume a low-spec laptop (12 GB RAM): local models are a fallback only.

## Working rules
- One branch + PR per slice. Commit locally at the end of each slice; ask before pushing; scan history for secrets before every push. `gh` is installed and logged in: create PRs when asked, never merge unless asked.
- Secrets live only in `.env` (gitignored). Never ask for keys to be pasted in chat; check presence with `grep -c`.
- Keep `LEARNING_LOG.md` updated (one line per slice).
- Test scripts live in `scratch/` (numbered). Link files by absolute path in chat.

## Architecture (see src/investigator/)
`llm.py` Gemini -> Groq -> Ollama cascade with timeouts; `db.py` Atlas; `tools/` article fetch + Tavily search (cached, credit counter); `extraction.py` claims/entities; `embeddings.py` Voyage via https://ai.mongodb.com/v1/embeddings (voyage-4-lite, 1024 dims, rate-limited: retry built in); `memory.py` Atlas Vector Search on claims; `graph.py` LangGraph hunter -> analyst -> searcher -> broaden -> historian -> skeptic -> writer; `investigation.py` runs and persists; `cli.py`.

## Status (2026-10-06)
PR #1 (pipeline) and PR #2 (Streamlit UI) are merged. Next: README with screenshot and architecture diagram, then optional semantic claim dedup (near-duplicate claims are stored separately today) and a Timeline page.

## Quirks
`gemini-3.7-flash` / `3.8-flash` often return 503; smart tier uses `gemini-3.5-flash`. Groq structured output needs `method="json_schema"`.
