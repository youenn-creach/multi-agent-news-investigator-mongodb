# Learning log

One line per session: what I learned, in my own words.

- 2026-10-05: An LLM provider is swappable. `get_llm(tier)` returns Gemini first, and LangChain's `with_fallbacks` silently tries Groq, then local Ollama if it errors (e.g. a 429 rate limit).
- 2026-10-05: Saving with `update_one(..., upsert=True)` keyed on a unique `url` index means re-fetching an article updates it instead of duplicating it.
- 2026-10-05: A tool docstring is written for the LLM, not for humans: it says when to use the tool, and tools return errors as data instead of raising so the agent can adapt.
