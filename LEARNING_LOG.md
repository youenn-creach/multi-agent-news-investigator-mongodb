# Learning log

One line per session: what I learned, in my own words.

- 2026-10-05: An LLM provider is swappable. `get_llm(tier)` returns Gemini first, and LangChain's `with_fallbacks` silently tries Groq, then local Ollama if it errors (e.g. a 429 rate limit).
