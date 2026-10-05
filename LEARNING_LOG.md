# Learning log

One line per session: what I learned, in my own words.

- 2026-10-05: An LLM provider is swappable. `get_llm(tier)` returns Gemini first, and LangChain's `with_fallbacks` silently tries Groq, then local Ollama if it errors (e.g. a 429 rate limit).
- 2026-10-05: Saving with `update_one(..., upsert=True)` keyed on a unique `url` index means re-fetching an article updates it instead of duplicating it.
- 2026-10-05: A tool docstring is written for the LLM, not for humans: it says when to use the tool, and tools return errors as data instead of raising so the agent can adapt.
- 2026-10-05: Two tools can wrap one API (search_news vs find_original_source); the docstrings steer the agent. Caching every search in Mongo and counting credits protects the scarce 1,000/month quota.
- 2026-10-05: Structured output (a Pydantic schema) makes the LLM return data, not prose; apply it per provider before chaining fallbacks. Claims and entities get their own collections because many investigations point at the same ones.
- 2026-10-05: An embedding turns text into 1024 numbers so that similar MEANING is close; $vectorSearch finds nearest neighbours. "Eurozone central bank hikes borrowing costs" matched the ECB claim with zero shared keywords. Embedding APIs rate-limit too, so retry on 429.
