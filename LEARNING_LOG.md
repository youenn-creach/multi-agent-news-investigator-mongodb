# Learning log

One line per session: what I learned, in my own words.

- 2026-10-05: An LLM provider is swappable. `get_llm(tier)` returns Gemini first, and LangChain's `with_fallbacks` silently tries Groq, then local Ollama if it errors (e.g. a 429 rate limit).
- 2026-10-05: Saving with `update_one(..., upsert=True)` keyed on a unique `url` index means re-fetching an article updates it instead of duplicating it.
- 2026-10-05: A tool docstring is written for the LLM, not for humans: it says when to use the tool, and tools return errors as data instead of raising so the agent can adapt.
- 2026-10-05: Two tools can wrap one API (search_news vs find_original_source); the docstrings steer the agent. Caching every search in Mongo and counting credits protects the scarce 1,000/month quota.
- 2026-10-05: Structured output (a Pydantic schema) makes the LLM return data, not prose; apply it per provider before chaining fallbacks. Claims and entities get their own collections because many investigations point at the same ones.
- 2026-10-05: An embedding turns text into 1024 numbers so that similar MEANING is close; $vectorSearch finds nearest neighbours. "Eurozone central bank hikes borrowing costs" matched the ECB claim with zero shared keywords. Embedding APIs rate-limit too, so retry on 429.
- 2026-10-05: A LangGraph is shared state + nodes + edges. Order matters: I first searched with the article title and got junk; extracting claims FIRST and searching with them gave real corroboration. The skeptic saying "unclear" instead of inventing support was the system working correctly. Always set timeouts so a stuck provider falls through to the next.
- 2026-10-05: Memory works: the second article on the same story recalled the first one’s claims (similarity 0.77-0.84, one already marked corroborated). Limit: near-duplicate claims with different wording are stored separately; semantic dedup is a future improvement.
- 2026-10-05: Streamlit reruns the whole script on each interaction; a callback (on_step) lets the agent graph stream live progress into st.status. Text from LLMs/articles is untrusted, so I escape it before putting it in the embedded graph page.
- 2026-10-06: A README is the front door of a project: it should say what is different (grounded evidence, memory, free-tier resilience), show the architecture, and be honest about limits. A setup command makes the one-time Atlas index creation reproducible for others.
