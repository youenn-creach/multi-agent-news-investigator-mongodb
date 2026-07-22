# AI News Investigator — Complete Build Plan

**For:** a Python developer with conceptual MongoDB knowledge, no Git/GitHub experience, learning agentic AI development
**Constraints:** $0 budget (free tiers only) · ~5h/week · Linux Mint, 2017 i3 quad-core, 12 GB RAM
**Framework choice:** LangChain / LangGraph
**Written:** July 2026 — free-tier limits quoted here were verified at time of writing, but they change (Google cut its quotas by more than half in December 2025 with no warning). Re-check the official pricing/limits pages the day you sign up.

**How to use this document:** Work top to bottom. Each phase has a *Goal*, a *Why* (the learning rationale — read it, it's the point), concrete *Steps* with time estimates, a *Checkpoint* (definition of done), *Self-test questions* (if you can't answer them, you copied code without learning — go back), and a suggested *commit*. Your very first Git commit in Phase 2 will be this file itself, saved as `docs/PLAN.md` in your repo, so you can tick the checkboxes as you go and anyone visiting your GitHub sees a builder who plans.

---

## Part 0 — Where you're going

At the end you will have a deployed, documented, public project where a user pastes a news article URL and watches a team of specialized agents investigate it: find the original source, gather independent coverage, extract factual claims, cross-check them against each other and against your database of past investigations, flag contradictions, and produce a sourced reliability report. Every investigation, claim, source, and entity is stored in MongoDB, so the system accumulates knowledge over time — the answer to "why couldn't this just be a ChatGPT conversation?"

You will also have: a GitHub profile with months of real commit history, a README with an architecture diagram and demo video, and three LinkedIn posts documenting the journey.

### The stack (and why each piece)

| Layer | Choice | Why this one, given $0 and your machine |
|---|---|---|
| LLM (primary) | **Gemini 2.5 Flash-Lite** via Google AI Studio | Highest free daily quota of any frontier lab (~1,000 requests/day as of mid-2026). No credit card. Agents burn many requests per run — daily quota is your real currency. |
| LLM (quality steps) | **Gemini 2.5 Flash** | Smarter, ~250 requests/day free. Use it for the hard steps (claim extraction, final report), Flash-Lite for the cheap ones. |
| LLM (cloud fallback) | **Groq** (Llama 3.3 70B, GPT-OSS, etc.) | Separate free quota (~30 req/min, ~1,000 req/day per model), no card, extremely fast, OpenAI-compatible. When Gemini says 429, your agent switches providers — a genuinely impressive engineering detail. |
| LLM (local fallback) | **Ollama** with **Phi-4 Mini** (3.8B, Q4_K_M) | No quota, no internet, no cost — ever. On your CPU-only i3, expect ~5–8 tokens/second: slow for demos, but a lifeline when your cloud quotas run dry during late-night coding. Swapping in is literally one string change in `get_llm()`. The three-tier routing story (cloud primary → cloud fallback → local) is itself impressive to explain. |
| Embeddings | **VoyageAI** (`voyage-4-lite`) via MongoDB Atlas | MongoDB acquired VoyageAI in 2024; the first 200 million free tokens per account make the free tier effectively unlimited for this project. Quality outperforms sentence-transformers significantly. The new `autoEmbed` feature (public preview, May 2026) can generate embeddings automatically on document insert — no external pipeline step. **Caveat:** check whether your Atlas account requires a credit card on file to access the Voyage embedding API, even within the free tier. If it does, fall back to **sentence-transformers** (`all-MiniLM-L6-v2`, runs locally, no quota, 384-dimensional vectors) — Phase 10 notes both paths. |
| Web search tool | **Tavily** (1,000 free credits/month) | Built for AI agents: returns clean text, not raw HTML, and it's the default search tool in the LangChain ecosystem, so every tutorial matches your stack. (Tavily also states it's free for students — check if that applies to you.) |
| Article extraction | **trafilatura** (Python library) | Local, free, best-in-class at turning a messy news page into clean text. |
| Database | **MongoDB Atlas Free cluster** (formerly "M0") | 512 MB free forever, no card — and crucially it includes **Atlas Vector Search**, so your RAG phase costs nothing. Cloud Mongo is also more portfolio-relevant than a local install. |
| Agent framework | **LangChain 1.0 `create_agent`** → **LangGraph 1.0 `StateGraph`** | Both hit stable 1.0 in October 2025. `create_agent` gets a working ReAct agent in a day; LangGraph is the low-level graph engine underneath it, which you'll graduate to for the multi-agent version. One stack, two levels of control. |
| Observability | **LangSmith** (free developer tier) | Shows you every prompt, tool call, and token your agent used. Debugging an agent without tracing is misery; with it, it's a learning accelerator. |
| UI | **Streamlit** | A real web UI in pure Python. No JavaScript detour. |
| Env & packages | **uv** + `pyproject.toml` | The modern Python toolchain (fast installer + lockfile). Employers increasingly expect it; beginners benefit most because it removes 90% of environment pain. |
| Editor | **VS Code** | Free, standard, great Python support on Linux Mint. |
| Hosting (optional) | **Streamlit Community Cloud** | Free hosting straight from your GitHub repo for the final demo. |

### Your hardware, honestly

Everything heavy (LLM inference, the primary database) runs in the cloud. Your machine runs Python scripts, a browser, and a local Ollama model — a 2017 i3 with 12 GB RAM handles all of that. The honest caveat on the local LLM: without a GPU, Ollama on your hardware will produce roughly 5–8 tokens/second on a 3.8B model. That's a 200-token response in 25–40 seconds — too slow to demo live, but perfectly fine as a development fallback when your cloud quotas are exhausted. Treat it as a late-night coding companion, not a primary.

### The daily budget that shapes the architecture

A single V1 investigation costs roughly 6–15 LLM calls and 2–4 web searches. Your free allowances (as of mid-2026):

| Resource | Free allowance | What that means for you |
|---|---|---|
| Gemini 2.5 Flash-Lite | ~15 req/min, ~1,000 req/day | Dozens of full investigations per day. Your workhorse. |
| Gemini 2.5 Flash | ~10 req/min, ~250 req/day | Reserve for the 2–3 "smart" steps per investigation. |
| Groq (per model) | ~30 req/min, ~1,000 req/day, low tokens/min | Cloud fallback. Its per-minute *token* cap is small, so send it summaries, not full articles. |
| Ollama (local) | Unlimited — no quota at all | Local fallback: no internet needed, no rate limits, just patience. Use it when cloud quotas are gone. |
| VoyageAI embeddings | 200 million free tokens per account | Effectively infinite for this project (embedding a 500-word article ≈ 500 tokens → you could embed 400,000 articles). |
| Tavily | 1,000 credits/month (basic search = 1 credit) | ~30 searches/day average. This is your scarcest resource → you will **cache every search result in MongoDB** (Phase 6). |
| Atlas Free cluster | 512 MB storage, ~500 connections | Thousands of text investigations. Plenty. |

Two habits fall out of this table, and both happen to be professional best practice: *cache aggressively* and *route each task to the cheapest model that can do it*. Free-tier constraints are secretly a good teacher. One caution: on Gemini's free tier, your prompts may be used by Google to improve its models — never paste anything private or sensitive.

### Time budget (at ~5h/week)

| Stage | Phases | Hours | Weeks (cumulative) |
|---|---|---|---|
| A — Foundations | 1–4 | ~17 h | 1–4 |
| B — Tools & the V1 agent | 5–9 | ~26 h | 5–10 · **🎉 first LinkedIn-postable milestone** |
| C — Memory & structured knowledge (V2+V3) | 10–12 | ~22 h | 11–15 |
| D — Multi-agent & showcase (V4) | 13–15 | ~22 h | 16–20 |
| **Total** | | **~87 h** | **~5 months** |

Estimates include realistic friction (things breaking, docs reading). If a phase takes 1.5× the estimate, that's normal, not failure. The design guarantees you have something demoable at week ~10, not just at the end.

---

## Part 1 — Ground rules (read once, live by them)

**The weekly rhythm.** Two sessions beat one: e.g., one 2 h session and one 3 h session. Agentic debugging needs a warm brain; five fragmented 1 h slots lose too much time to "where was I?". End every session by writing one line in `LEARNING_LOG.md`: what you did, what broke, what you understood. This file becomes your LinkedIn content and your interview prep for free.

**The Git habit.** Commit at the end of every session, minimum. Small commits with honest messages (`Add article extraction tool with error handling`, not `stuff`). Your contribution graph and commit history *are* part of the portfolio — recruiters do click on them.

**Definition of done.** A phase is done when its Checkpoint passes and you can answer its self-test questions out loud, without looking. Not before.

**How to use AI assistants (Claude included) without sabotaging the learning goal.** This project's value evaporates if an AI writes it for you — in an interview, "walk me through your contradiction detector" will expose that in ninety seconds. The rules: (1) type the code yourself, even when an AI showed you the shape of it; (2) ask "explain the concept, then let me try" before asking for code; (3) paste error messages freely — error translation is the single best use of AI while learning; (4) after finishing a feature, ask an AI to *review* your code and explain its criticism; (5) never commit a line you couldn't explain to a rubber duck.

**When you're stuck (>45 min on one bug):** read the error bottom-up, print the intermediate values, isolate the failure in a 10-line scratch file, and only then ask an AI or search. Struggling *briefly* is where learning happens; struggling for three hours is just morale damage. 45 minutes is the line.

**Scope discipline.** Every phase will tempt you with shiny extras. Write the idea in `docs/IDEAS.md`, then get back to the phase. The graveyard of portfolio projects is full of ambitious V1s that never shipped.

---

## Stage A — Foundations (Weeks 1–4, ~17 h)

### Phase 1 — Machine & toolchain setup (~3 h)

**Goal:** a Linux Mint machine ready for professional Python development.

**Why:** environment problems are the #1 place beginners silently quit. One clean setup session with modern tooling (uv) means you'll never fight "it works on my machine" alone at 11pm. It also teaches the terminal fluency that every developer job assumes.

**Steps:**

1. *(20 min)* Update the system and install the basics:
   ```bash
   sudo apt update && sudo apt upgrade
   sudo apt install git curl build-essential
   ```
2. *(10 min)* Check Python: `python3 --version`. Mint 21.x ships 3.10, Mint 22.x ships 3.12 — anything ≥3.10 is fine for this stack. Don't install another Python; uv can manage versions later if ever needed.
3. *(20 min)* Install **uv** (the package/environment manager you'll use all project long): follow the one-line installer on the uv documentation site (docs.astral.sh/uv), then open a new terminal and verify with `uv --version`. Read the 5-minute "Getting started" page — you only need `uv init`, `uv add`, `uv run`.
4. *(30 min)* Install **VS Code** (download the .deb from code.visualstudio.com, install with `sudo dpkg -i`, or use the Software Manager). Add the official *Python* extension. Open the integrated terminal (Ctrl+`) — you'll live here.
5. *(30 min)* Terminal micro-course: make sure `cd`, `ls`, `mkdir`, `cat`, `nano/edit`, `cp`, `mv`, and Ctrl+C are reflexes. If any aren't, do a 20-minute Linux command-line tutorial now — it pays for itself within the week.
6. *(45 min)* Create the project:
   ```bash
   mkdir -p ~/projects && cd ~/projects
   uv init news-investigator --python 3.12   # or your version
   cd news-investigator
   uv add requests python-dotenv
   uv run python -c "import requests; print('environment OK')"
   ```
   Poke around: open `pyproject.toml` and read it. That file *is* your project definition — dependencies, Python version, metadata. Understand that `uv run` executes inside the project's own virtual environment, isolated from the system.

**Checkpoint:** `uv run python -c "import requests; print('OK')"` prints OK from inside the project folder.

**Self-test:** What problem does a virtual environment solve? What's the difference between `pyproject.toml` and `uv.lock`? *(Short answers: dependency isolation between projects; declared intent vs. exact pinned reality.)*

---

### Phase 2 — Git & GitHub from zero (~4 h)

**Goal:** your project lives on GitHub, and committing is a reflex.

**Why:** version control is the baseline literacy of the entire software industry — it's how you'll undo mistakes, how employers verify you actually built this over months, and how the "green squares" on your profile tell the story before your CV does. Doing it *first* means every hour of the project is on the record.

**Steps:**

1. *(20 min)* Create a GitHub account. Choose the username like it's going on a CV — it is. Enable two-factor auth.
2. *(15 min)* Introduce yourself to git locally:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "same-email-as-github@example.com"
   git config --global init.defaultBranch main
   ```
3. *(30 min)* Set up SSH so pushing never asks for a password: `ssh-keygen -t ed25519 -C "your-email"`, press Enter through the prompts, copy the contents of `~/.ssh/id_ed25519.pub` into GitHub → Settings → SSH keys. Test with `ssh -T git@github.com`. Understand the idea: the *private* key stays on your machine forever; only the *public* key is shared.
4. *(45 min)* Read/watch a short "git core concepts" explainer until you can define: repository, commit, staging area, branch, remote, push/pull. (GitHub's own "Hello World" guide is enough.) Skip everything about rebasing/reflogs — not yet.
5. *(45 min)* Put your project under version control:
   ```bash
   cd ~/projects/news-investigator
   git init
   ```
   Create a `.gitignore` **before the first commit** — this is the moment that prevents the classic beginner disaster of publishing API keys. Start from GitHub's standard Python `.gitignore` template and make sure it contains at least: `.venv/`, `__pycache__/`, and **`.env`**.
6. *(30 min)* Create the skeleton: a `README.md` with the project name and a two-line description, a `docs/` folder, and save **this plan** as `docs/PLAN.md`. Then:
   ```bash
   git add .
   git commit -m "Initial project skeleton with build plan"
   ```
7. *(30 min)* Create an empty repository on GitHub named `news-investigator` (public, no auto-README since you have one), then connect and push:
   ```bash
   git remote add origin git@github.com:YOURNAME/news-investigator.git
   git push -u origin main
   ```
   Refresh the GitHub page and enjoy the moment — you're live.
8. *(15 min)* Practice the loop once more: edit README, `git status`, `git diff`, `git add`, `git commit`, `git push`. This five-command loop is 95% of daily git.

**Checkpoint:** your repo is visible on github.com with the plan inside, and `.env` is in `.gitignore` *before any `.env` file exists*.

**Self-test:** What's the difference between `git add` and `git commit`? Between commit and push? Why must `.env` never be committed, and what would you do if you accidentally pushed an API key? *(Answer to the last one: rotate/revoke the key immediately on the provider's site — deleting the file in a later commit does not remove it from history.)*

---

### Phase 3 — First LLM API calls (~6 h)

**Goal:** call Gemini, Groq, *and a local Ollama model* from Python, first raw, then through LangChain, and get *structured* (JSON/Pydantic) output back. Build the three-tier `get_llm()` helper that the rest of the project uses.

**Why:** an agent is nothing but LLM API calls arranged in a loop with tools. If you understand one call deeply — what goes in, what comes back, what a token is, why temperature matters — the framework will never feel like magic. And structured output is *the* core production skill: real systems don't want prose from a model, they want validated objects. The three-provider setup adds one more real skill: **graceful degradation**, which is how production AI systems stay alive when a vendor has an outage or you've spent your daily quota.

**Steps:**

1. *(20 min)* Get a **Gemini API key**: Google AI Studio → "Get API key" (no card needed). Create `.env` in your project:
   ```
   GOOGLE_API_KEY=...
   GROQ_API_KEY=...
   OLLAMA_MODEL=phi4-mini
   ```
   Confirm `git status` does **not** list `.env`. Also create a `.env.example` file with the variable names but no values — that one *does* get committed (it documents what a user of your repo needs).
2. *(60 min)* **The raw call.** Before any framework: open the Gemini API "Quickstart / REST" page and, using only Python's `requests`, POST the example JSON body to the endpoint with your key, then `print(response.json())`. Stare at the response structure — find where the actual text lives, find the token counts (`usageMetadata`). Change the prompt. Break it on purpose (wrong key, wrong model name) and read the error bodies. This hour is the foundation of everything.
3. *(30 min)* Read a short explainer on **tokens** and **temperature**, then verify empirically: same prompt at temperature 0 three times (near-identical answers) vs temperature 1 (variety). Note token counts for a long vs short prompt — you're paying quota in tokens.
4. *(45 min)* **Now the framework.** `uv add langchain langchain-google-genai`, then in a script:
   ```python
   from langchain.chat_models import init_chat_model
   llm = init_chat_model("google_genai:gemini-2.5-flash-lite")
   print(llm.invoke("Explain what an AI agent is in one sentence.").content)
   ```
   Notice what LangChain bought you: the exact same code will run on any provider by changing that one string. Try a system prompt + user message as a list of `("system", ...), ("human", ...)` tuples.
5. *(30 min)* **Cloud fallback: Groq.** Create a free Groq account (console.groq.com, no card), add `GROQ_API_KEY` to `.env`, `uv add langchain-groq`, and run the same script with `init_chat_model("groq:llama-3.3-70b-versatile")`. One string changed — same result. That's provider-agnostic design.
6. *(45 min)* **Local fallback: Ollama.** Install Ollama: go to ollama.com, follow the Linux install (one `curl` command). Then:
   ```bash
   ollama pull phi4-mini   # ~2.3 GB download — start it, stretch your legs
   ollama run phi4-mini "What is an AI agent?"   # interactive test
   ```
   Then `uv add langchain-ollama` and run the same script with `init_chat_model("ollama:phi4-mini")`. Watch it generate. It's slower, but it runs — and now you have three independent providers. Time this response vs. Gemini's: this concrete comparison is what makes the "local = fallback, not primary" architectural decision *yours*, not just received wisdom.
7. *(75 min)* **Structured output.** `uv add pydantic` (likely already present). Define:
   ```python
   from pydantic import BaseModel, Field

   class ArticleAnalysis(BaseModel):
       topic: str
       main_claim: str = Field(description="The single most important factual claim")
       claims: list[str]
       sensationalism_score: float = Field(ge=0, le=1)
   ```
   Use `llm.with_structured_output(ArticleAnalysis)` and invoke it on a pasted paragraph of news text. Try all three providers — Gemini Flash, Groq, and Ollama — on the same text. Compare quality and speed. You've just discovered that *schemas are prompts* and that model capability matters for structured extraction.
8. *(25 min)* Write `src/investigator/llm.py` (create the package folders) with a three-tier helper:
   ```python
   def get_llm(tier: str = "cheap"):
       if tier == "smart":
           return init_chat_model("google_genai:gemini-2.5-flash")
       elif tier == "cheap":
           return init_chat_model("google_genai:gemini-2.5-flash-lite")
       elif tier == "fallback":
           return init_chat_model("groq:llama-3.3-70b-versatile")
       elif tier == "local":
           return init_chat_model("ollama:phi4-mini")
   ```
   All later code calls `get_llm(tier=...)`. When Gemini gives a 429, the caller catches it and retries with `get_llm("fallback")`, then `get_llm("local")`. Routing logic lives in one file — that's the architecture.

**Checkpoint:** one script takes raw text, prints a validated `ArticleAnalysis` object from all three providers, and you can narrate why each tier exists.

**Self-test:** What is a token, roughly? Why does temperature 0 matter for extraction tasks? What does `with_structured_output` actually do under the hood? Why use local as the *last* fallback rather than the first? *(Answers: ~¾ of a word; determinism; binds schema as a tool the model must fill then validates with Pydantic; speed — a slow answer is better than no answer, but a fast cloud answer is better than a slow local one.)*

**Commit:** `Add three-tier LLM helper (Gemini / Groq / Ollama) with structured output`

---

### Phase 4 — MongoDB Atlas + PyMongo (~5 h)

**Goal:** a free Atlas cluster you can read *and write* from Python, with a first designed schema.

**Why:** you can read MongoDB; this phase makes you someone who *designs for it*. Persistence is the entire answer to "why isn't this just ChatGPT" — every later phase (caching, memory, claims, vector search) stands on this one. Schema design decisions (embed vs. reference) are also classic interview material.

**Steps:**

1. *(45 min)* Create the cluster: sign up at cloud.mongodb.com → Build a Database → **Free** tier → pick a region geographically close to you → create. Then: create a database user (username + strong password), and in Network Access add your current IP. *Gotcha to know now:* home IPs change; when connections mysteriously fail in three weeks, this allowlist is why. For a learning project you may allow access from anywhere (0.0.0.0/0) — acceptable here because the DB will hold public news data and is protected by the password, but know that you'd never do this with sensitive production data.
2. *(30 min)* Copy the connection string into `.env` as `MONGODB_URI` (URL-encode special characters in the password if needed). Then `uv add pymongo` and prove the connection:
   ```python
   from pymongo import MongoClient
   import os; from dotenv import load_dotenv; load_dotenv()
   client = MongoClient(os.environ["MONGODB_URI"])
   client.admin.command("ping"); print("connected")
   ```
3. *(90 min)* CRUD workout in a scratch script — do each from memory before checking docs: `insert_one`, `insert_many`, `find` with a filter, `find_one`, `update_one` with `$set`, `delete_one`, `count_documents`. Then aggregation's first taste: group fake articles by `source` and count. Browse what you created in the Atlas web UI ("Browse Collections") — seeing your documents appear in the cloud is a good moment.
4. *(60 min)* **Design session** (paper first, then code): the `articles` collection. Draft the document shape: `url` (unique), `title`, `text`, `site`, `published_at`, `fetched_at`. Create a unique index on `url` (`create_index`) and *understand* why: it makes re-fetching idempotent — inserting the same article twice fails instead of duplicating. Write down (in `docs/SCHEMA.md`) the embed-vs-reference question you'll face later: should claims live *inside* an investigation document or in their own collection? (Answer comes in Phase 11: their own, because claims get cross-referenced across investigations. Predict why before you read that.)
5. *(45 min)* Write `src/investigator/db.py`: one function `get_db()` returning the database handle, plus `save_article(article: dict)` doing an upsert on `url`. Every later phase imports from here.
6. *(15 min)* **VoyageAI access check** (do this now, not in Phase 10, so you don't hit a surprise on the day). In your Atlas UI, look for "AI Models" or "Voyage AI" in the left sidebar. Try generating a model API key. If Atlas lets you create one without requiring a billing card, add `VOYAGE_API_KEY=...` to `.env` and `.env.example` and note in `LEARNING_LOG.md` that you're on the VoyageAI path. If it prompts for a card you don't want to provide, note "sentence-transformers fallback" in the log and continue — Phase 10 fully documents both options. Either way, you're not blocked.

**Checkpoint:** a script saves an article dict to Atlas, running it twice creates one document, and you can see it in the Atlas UI. VoyageAI access confirmed (or fallback noted).

**Self-test:** When would you embed a sub-document vs. reference another collection? What does the unique index on `url` protect you from? What is an upsert?

**Commit:** `Add MongoDB layer with article schema and idempotent saves`

**🏁 Stage A milestone reached:** text in → LLM analysis → stored in a cloud database, all reproducible from a public repo. You've built the spine.

---

## Stage B — Tools & the V1 agent (Weeks 5–10, ~26 h)

*From here on, level up your git: start each phase on a branch (`git checkout -b phase-5-article-tool`), and when it's done, open a Pull Request on GitHub and merge it yourself. Self-PRs feel silly alone but they build the exact muscle memory of team development, and they make your repo history look professional.*

### Phase 5 — Tool #1: article ingestion (~5 h)

**Goal:** a robust Python function: URL in → clean article text + metadata out → saved to Mongo.

**Why:** here's the first mental unlock of agent building — **a "tool" is just a Python function with a good docstring**. The LLM never sees your code; it sees the function's name, docstring, and argument types, and decides when to call it. So tool-writing is two skills at once: handling messy real-world input (paywalls, cookie walls, JS-only pages) and writing docstrings *for a machine reader*.

**Steps:**

1. *(15 min)* `uv add trafilatura`. Skim its docs homepage: `fetch_url` then `extract`, with `output_format="json"` giving you title/date/text in one shot.
2. *(90 min)* Write `src/investigator/tools/articles.py` → `fetch_article(url: str) -> dict`. Return `{url, title, text, site, published_at, status}`. Test on five real article URLs from different major outlets *and* one URL you know will fail (a PDF, a paywalled site). Decide the failure contract: return `{"status": "error", "reason": ...}` rather than raising — agents handle a polite error string far better than a crash.
3. *(45 min)* Wire in persistence: on success, `save_article()` from Phase 4 (upsert). Add a cache check: if the URL is already in Mongo and fresh (< 7 days), return the stored version without fetching. You just built your first cache — remember the free-tier table; this pattern repeats.
4. *(60 min)* Now make it a **tool**. Write the docstring as if explaining to a new intern *when* to use it: "Fetches and extracts the readable text of a news article given its URL. Use this whenever the user provides a URL or you discover a source URL worth reading. Returns title, text, publication date." Test it standalone; keep functions pure (no prints, return data).
5. *(30 min)* Truncation guard: articles can be huge and Groq's per-minute token cap is small. Add a `max_chars` cut (e.g., 12,000 chars ≈ ~3,000 tokens) with a note in the returned dict when truncated.

**Checkpoint:** `fetch_article` handles your five good URLs and one bad URL gracefully, caches in Mongo, second call is instant.

**Self-test:** Why must tools return errors instead of raising them? Why does the *docstring* matter more than the code, from the agent's perspective?

**Commit / PR:** `Add article ingestion tool with caching and graceful failure`

---

### Phase 6 — Tool #2: web search (~3 h)

**Goal:** a search tool with topic filtering and Mongo-backed caching, spending Tavily credits like they're rare — because they are.

**Why:** retrieval quality is the ceiling on agent quality; garbage search results produce a confident agent saying garbage. And the 1,000 credits/month cap forces cost-aware engineering — the habit that separates demo-builders from production engineers.

**Steps:**

1. *(20 min)* Create a free Tavily account, add `TAVILY_API_KEY` to `.env` (and the name to `.env.example`). Install the client the Tavily quickstart currently recommends for LangChain use.
2. *(45 min)* Play in a scratch script: run a basic search, print the results structure. Try `topic="news"` and a recency window vs. general search; note that each response already contains clean content snippets — no scraping needed.
3. *(60 min)* Write `src/investigator/tools/search.py` → `search_news(query: str, max_results: int = 5) -> list[dict]`, returning simplified `{title, url, snippet, published}` items. Add the cache: before calling Tavily, check a `searches` collection for the same normalized query within 3 days; after calling, store the result. Log a counter in a `usage` collection — you'll enjoy watching what your agent actually spends.
4. *(45 min)* A second, narrower tool: `find_original_source(claim_or_topic: str)` — same API underneath, but a different docstring steering the agent toward press releases, official statements, and primary sources. Lesson inside: **tools are shaped by intent, not just by API** — two docstrings, two behaviors, one backend.

**Checkpoint:** both tools return clean results; repeating a query hits the Mongo cache (verify by the absence of a new `usage` entry).

**Self-test:** Why cache searches but *not* cache LLM final reports? Why do two tools share one API? What would happen to agent behavior if your search tool returned raw HTML?

**Commit / PR:** `Add cached news search and original-source tools`

---

### Phase 7 — Agent fundamentals: LangChain `create_agent` & the loop (~8 h)

**Goal:** understand the agent loop deeply, then have a working agent that autonomously uses your two tools.

**Why:** this is the conceptual heart of the entire project. An "agent" = an LLM in a loop: model sees the goal → decides to call a tool → your code runs it → result goes back into the conversation → model decides again → … until it answers. LangChain's `create_agent` gives you that loop pre-built on LangGraph's runtime; your job this phase is to make sure it's *understood*, not just imported.

**Steps:**

1. *(90 min)* Course time: do the first modules of **LangChain Academy's free "Introduction to LangGraph"** course (found via the LangChain docs site — the 1.0 docs live at docs.langchain.com). Goal: hear the official vocabulary — messages, tools, state, nodes, edges — before writing code.
2. *(60 min, the demystifier — don't skip)* **Build the loop by hand once.** In a scratch file, no agent imports: bind your two tools to the model with `llm.bind_tools([...])`, send a question, inspect the response's `tool_calls`, execute the requested function yourself, append a tool message with the result, call the model again. Ten to twenty lines. When you then see `create_agent`, you'll know exactly what it automates — the difference between using a framework and being used by one.
3. *(60 min)* The real thing:
   ```python
   from langchain.agents import create_agent
   agent = create_agent(
       model=get_llm("cheap"),
       tools=[fetch_article, search_news, find_original_source],
       system_prompt=INVESTIGATOR_PROMPT,
   )
   result = agent.invoke({"messages": [("user", "Is this article's main claim independently confirmed? " + url)]})
   ```
   Write `INVESTIGATOR_PROMPT` yourself (persona: skeptical investigative journalist; method: original source first, then independent coverage, then compare; always cite URLs; admit uncertainty). Prompt quality will visibly change behavior — iterate.
4. *(45 min)* **Watch it think.** Switch `invoke` → `stream` and print each step as it happens: which tool, which arguments, what came back. Seeing the decision sequence is the "wow" moment — screenshot it for your future LinkedIn post.
5. *(45 min)* Set up **LangSmith** (free developer account, a couple of env vars per its quickstart). Re-run the agent and open the trace in the browser: every prompt, every token count, the full tree. From now on, when the agent behaves oddly, you look here first.
6. *(60 min)* Stress the agent: a URL that fails to fetch (does it recover and search instead?), a question needing no tools (does it skip them?), a French-language article (fine — the models are multilingual). Add a safety net: pass a recursion/iteration limit so a confused agent can't loop your daily quota away. Note behaviors in `LEARNING_LOG.md`.

**Checkpoint:** given a URL and a question, the agent autonomously fetches, searches, and answers with cited sources — and you can narrate every step of its loop from the LangSmith trace.

**Self-test:** Draw the ReAct loop from memory. What exactly does `bind_tools` send to the API? Where does the tool *result* go, and why does the model need it in the message history? What stops an infinite loop?

**Commit / PR:** `Add investigator agent v0 with tool use and tracing`

---

### Phase 8 — Investigator V1: the full pipeline (~6 h)

**Goal:** one command runs a complete investigation of a URL and stores a structured investigation document in Mongo.

**Why:** this converts "an agent that answers questions" into "a system that produces artifacts." The investigation document — inputs, every tool call, sources, the report — is your unit of value, the thing memory and the UI are built on. Designing it teaches the observability mindset: if it isn't recorded, it didn't happen.

**Steps:**

1. *(45 min)* Design `investigations` schema in `docs/SCHEMA.md`: `_id`, `url`, `article` (title/site/date), `question`, `steps` (list of `{tool, args, summary}`), `sources` (list of `{url, title, stance}`), `report_md`, `model_usage`, `status`, `created_at`. Review your embed-vs-reference prediction from Phase 4.
2. *(90 min)* Write `src/investigator/investigation.py` → `run_investigation(url) -> investigation_id`: create the doc with `status="running"`, stream the agent, record each tool step into the doc as it happens (`update_one` + `$push`), save the final report, flip status. Crash-resilience for free: a failed run leaves a half-filled doc that tells you where it died.
3. *(60 min)* Structure the *output* too: instead of free-prose, have the final step produce a Pydantic `Report` (`verdict`, `confidence: float`, `summary`, `corroborating_sources`, `flags`) using your Phase 3 skill, and render it to markdown for humans. Machine-readable first, pretty second — you'll thank yourself in Phases 10–12.
4. *(45 min)* CLI entry point: `uv run python -m investigator.cli "https://..."` printing live progress lines and the final report. (A `__main__`-style module + `argparse`; keep it simple.)
5. *(60 min)* Run 4–5 real investigations on current news from different domains (tech announcement, health study, political claim, sports transfer rumor). Read the reports critically: where is the agent naive? Note improvements in `docs/IDEAS.md` — some become Stage D material.

**Checkpoint:** one command → live progress → complete investigation document visible in Atlas → readable report. Re-runs create new investigations while article fetches hit cache.

**Self-test:** Why record steps *during* the run instead of at the end? Why produce the report as a Pydantic object instead of prose? What's in a `status` field's state machine here?

**Commit / PR:** `Add end-to-end investigation pipeline with persisted runs`

---

### Phase 9 — Streamlit UI v1 (~4 h)

**Goal:** a local web app: paste URL → watch the investigation live → browse past investigations.

**Why:** demo-ability. A CLI convinces engineers; a live progress UI convinces *everyone* — and "the user watches the investigation unfold" is your project's signature. Streaming agent events into a UI is also a real skill (it's the same mechanism as every AI product's "thinking…" display).

**Steps:**

1. *(30 min)* `uv add streamlit`. Do the 15-minute official "main concepts" tour: the script-rerun model, `st.text_input`, `st.button`, `st.status`, `st.markdown`, `st.sidebar`.
2. *(90 min)* Page 1 — **New investigation**: URL input → on click, call `run_investigation` and surface progress live (`st.status` blocks per step: "🔎 Searching independent coverage…", "✓ 4 sources found"). Reuse the streaming callback from Phase 8 rather than duplicating logic — UI reads events, engine emits them.
3. *(60 min)* Page 2 — **History**: list past investigations from Mongo (newest first, title + verdict + confidence badge), click to view the full report and its step log. You're now *reading* your own database product.
4. *(30 min)* Ten minutes of polish, no more: a title, an emoji, a caption explaining the project in one sentence. Resist theming rabbit holes.
5. *(30 min)* Update the README: what it does, a screenshot, how to run (`uv sync`, fill `.env` from `.env.example`, `uv run streamlit run app.py`).

**Checkpoint:** `uv run streamlit run app.py` → paste a URL in your browser → watch steps appear → report renders → investigation appears in History.

**Self-test:** Why does Streamlit re-run the whole script on interaction, and what does that imply about where expensive work must live? How do UI progress events get from the agent to the page?

**Commit / PR:** `Add Streamlit UI with live investigation progress and history`

---

**🎉 MILESTONE — ship it (week ~10).** You now have a legitimate agentic AI project. Spend 1 h on your **first LinkedIn post**: a 30–60 s screen recording of a live investigation (SimpleScreenRecorder or Kooha on Mint), three sentences on what it does, one honest sentence on what you learned ("I finally understand what an 'agent' actually is: an LLM in a loop with tools"), the GitHub link. Post it before Stage C — public momentum is fuel, and early feedback sometimes redirects effort better than any plan.

---

## Stage C — Memory & structured knowledge: V2 + V3 (Weeks 11–15, ~22 h)

### Phase 10 — Embeddings + Atlas Vector Search (~8 h)

**Goal:** every investigation gets an embedding; the agent gains a `find_similar_investigations` tool; "have I seen this story before?" works.

**Why:** semantic search / RAG is the single most asked-about applied-AI skill right now. This phase also shows off two things in combination that most learners never see together: using the native embedding model of your database vendor (VoyageAI, owned by MongoDB) to eliminate a whole pipeline step. It's also where MongoDB stops being storage and becomes a retrieval engine — and that shift is the answer to "why not just use PostgreSQL?"

This phase documents **two paths** side by side. Check which one you're on based on your Phase 4 VoyageAI access test, then follow that path. Both produce the same outcome; only the code differs slightly.

**Step 1 — Concepts first *(45 min)*:** read/watch a good "embeddings explained" piece until you can say why *similar meaning → nearby vectors*, and what cosine similarity measures. The key intuition: a model maps words and sentences to points in a very high-dimensional space, and the *direction* of those points encodes meaning. Two sentences about Apple chips land near each other; a cake recipe lands far away. Everything below is plumbing on top of that idea.

**Step 2 — Touch the vectors *(60 min)*:**

*Path A (VoyageAI):* `uv add voyageai`, then:
```python
import voyageai
client = voyageai.Client()  # reads VOYAGE_API_KEY from env
result = client.embed(
    ["Apple unveils new AI chip", "Apple annonce une puce IA", "Recipe for lemon cake"],
    model="voyage-4-lite"
)
```
Each vector has **1024 dimensions**. Print shapes, compute cosine similarities with a two-line numpy function. The two Apple sentences — different languages! — should be close; the cake far.

*Path B (sentence-transformers):* `uv add sentence-transformers` (heads-up: pulls PyTorch CPU — a big download; start it, stretch your legs), then:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
v = model.encode(["Apple unveils new AI chip", "Apple annonce une puce IA", "Recipe for lemon cake"])
```
Each vector has **384 dimensions**. Same cosine similarity exercise. Runs entirely on your CPU, no API key needed.

In either case, stare at the numbers. *This* is the whole foundation.

**Step 3 — Embedding pipeline *(45 min)*:**

*Path A:* Write `src/investigator/embeddings.py` → `embed_text(text: str) -> list[float]` calling the Voyage API with `model="voyage-4-lite"`. Add error handling and a log entry to your `usage` collection (you're spending free tokens — it's educational to watch them). After each investigation completes, call `embed_text(title + " " + summary + " " + " ".join(main_claims))` and store the result in an `embedding` field on the investigation document. Backfill existing docs with a small script.

*Path B:* Same structure in `embeddings.py`, but the function loads the sentence-transformers model once at module level (it takes a second on first load) and calls `model.encode([text])[0].tolist()`. Local, instant, unlimited.

**Step 4 — Atlas Vector Search index *(90 min)*:**

In the Atlas UI → Search tab → Create Search Index → **Atlas Vector Search**. The JSON index definition differs only in `numDimensions`:

```json
{
  "fields": [{
    "type": "vector",
    "path": "embedding",
    "numDimensions": 1024,
    "similarity": "cosine"
  }]
}
```
*(Path B: use `384` instead of `1024`.)*

Wait for the index to finish building (usually under 2 minutes on an empty collection). Then query it from Python with a `$vectorSearch` aggregation stage — follow the current Atlas Vector Search quickstart for the exact pipeline syntax; it changes between minor versions. Get top-3 similar investigations for a fresh text and sanity-check by eye: are they actually similar?

**Step 4A — autoEmbed (Path A only, optional but impressive) *(30 min)*:** Atlas's `autoEmbed` index type (public preview, May 2026) generates Voyage embeddings automatically whenever a document is inserted or updated — no explicit embedding call needed in your Python code. If this feature is stable on your Atlas cluster, try replacing your manual embedding pipeline with an autoEmbed index on the `investigations.text_for_embedding` field. If it's still rough or unavailable on the free tier, keep the manual pipeline from Step 3 — it's more educational anyway, because you see every step.

**Step 5 — Package as a tool *(60 min)*:** `find_similar_investigations(topic_or_claim: str) -> list` returning `{title, url, verdict, date, similarity_score}`. The docstring tells the agent: *"Search your institutional memory for previously investigated articles on this topic or involving this claim. Call this before searching the open web."* Add it to the agent's tool list.

**Step 6 — Verify the magic *(60 min)*:** investigate an article, then investigate a *different* article on the same story a few minutes later. The LangSmith trace should show the memory tool firing and the report referencing the earlier investigation by title. Screenshot the moment — that's LinkedIn post #2 material: "the system remembered."

**Checkpoint:** the agent, given a fresh article about a previously-investigated topic, cites its own past investigation unprompted. Vector index built and querying successfully on whichever path you took.

**Self-test:** Why 1024 (or 384) numbers and not keywords? What does `numCandidates` trade off against `limit`? Why embed the *summary* rather than the full article text? What is the practical difference between the two embedding paths for this project, at this scale? *(Answer to the last: retrieval quality — Voyage 4-lite outperforms MiniLM significantly on benchmark evals, and the 200M free tokens make the API cost negligible. The main trade-off is API latency vs. local compute.)*

**Commit / PR:** `Add semantic memory via VoyageAI embeddings and Atlas Vector Search` (or `…via local embeddings…` if on Path B)

---

### Phase 11 — Claim extraction & entity tracking (~9 h)

**Goal:** investigations produce structured `Claim` and `Entity` records in their own collections; claims have a verification lifecycle.

**Why:** this is the leap from "app that uses a database" to "system that builds a knowledge base." Information extraction (unstructured text → validated records) is a marquee skill, and the schema-design decisions here — separate collections, cross-references, status lifecycles — are the MongoDB depth this project exists to demonstrate.

**Steps:**

1. *(60 min)* Design on paper, then in `docs/SCHEMA.md`:
   - `claims`: `text` (normalized single assertion), `subject`, `claim_type` (performance / date / quantity / event / quote), `first_seen`, `source_urls[]`, `investigation_ids[]`, `status` (`unverified → corroborated | disputed | contradicted`), `evidence[]` (`{url, stance: supports|contradicts|mentions, note}`), `confidence: float`.
   - `entities`: `name`, `type` (company / person / product / organization), `aliases[]`, `claim_ids[]`, `investigation_ids[]`.
   Justify each decision in writing — why separate collections (claims are shared *across* investigations; embedding would trap them), why `aliases` (dedup), why `evidence` is embedded (it belongs to exactly one claim).
2. *(90 min)* Extraction step: Pydantic models `ExtractedClaim` / `ExtractedEntity`, a dedicated extraction prompt ("atomic, verifiable, self-contained assertions — no opinions"), run with the *smart* model at temperature 0 via `with_structured_output`. Iterate on 3 articles until the claims read like a fact-checker wrote them. This prompt will take several rounds — that's the skill forming, not a delay.
3. *(60 min)* Persistence with dedup: upsert entities on a normalized name (lowercase, stripped) checking `aliases`; claims are near-duplicates problems — start simple (exact normalized text), and note "semantic claim dedup via embeddings" in `IDEAS.md` as a stretch (you already own the tool for it).
4. *(90 min)* The **lifecycle**: when an investigation gathers sources, have a verification step judge each existing relevant claim against each source (structured verdict: supports / contradicts / unrelated + one-line rationale), push into `evidence`, and recompute `status` with a simple rule (e.g., 2+ independent supporting domains → corroborated; any credible contradiction → disputed). Rules in plain code, judgment calls in the LLM — remember that division of labor.
5. *(60 min)* Surface it: a **Claims** page in Streamlit — filterable table (status, subject), click a claim → its evidence trail and linked investigations. A claim moving from *unverified* to *corroborated* across two separate investigations is your project's proudest artifact; engineer one such moment deliberately and screenshot it.
6. *(45 min)* Wire extraction into `run_investigation` and re-run on 3–4 fresh articles; watch collections populate in Atlas.

**Checkpoint:** investigating two related articles produces shared entities, at least one claim with multi-source evidence, and a status that changed because of evidence.

**Self-test:** Defend embedding `evidence` inside claims but *not* claims inside investigations. Why temperature 0 and the smart model for extraction? Who decides a claim's status — the LLM or your code — and why does that split matter?

**Commit / PR:** `Add structured claim and entity extraction with verification lifecycle`

---

### Phase 12 — Memory wired into the agent (~5 h)

**Goal:** every new investigation automatically consults the knowledge base — similar investigations, known entities, existing claim statuses — and the report shows it.

**Why:** V2 and V3 exist so the agent can be *contextual*. This phase is small in code but it's where the demo narrative crystallizes: "the system knows what it learned last month." It also teaches context engineering — deciding what past knowledge enters the prompt, and what stays out.

**Steps:**

1. *(90 min)* A pre-investigation "memory briefing" step: vector-search similar investigations + look up extracted entities' existing claims, condense into a short briefing block ("You previously investigated X on DATE, verdict Y. Known claims about ENTITY: …") injected into the agent's context. Keep it under a few hundred tokens — context is quota.
2. *(60 min)* Report upgrade: a *Previously investigated* section (linked) and per-claim annotations (new / consistent with record / **conflicts with record** — the last one flagged loudly; it's a contradiction across time, your headline feature ahead of Stage D).
3. *(60 min)* The showcase test: pick a developing story, investigate an early article, then a follow-up days later. Verify the second report references the first and updates claim statuses. Save both reports — LinkedIn post #2: "my agent remembers" with the before/after.
4. *(45 min)* Post it. Same format as post #1; emphasize memory + the claims table. Update README (features list + new screenshots).

**Checkpoint:** second-article-same-story demonstrably uses and cites first-article knowledge without being asked.

**Self-test:** Why condense memory into a briefing instead of dumping full past reports into context? What breaks if you skip entity dedup before this phase?

**Commit / PR:** `Wire knowledge-base memory into investigations`

---

## Stage D — Multi-agent & showcase: V4 (Weeks 16–20, ~22 h)

### Phase 13 — The multi-agent graph in LangGraph (~10 h)

**Goal:** replace the single agent with an explicit LangGraph `StateGraph` of specialists — Hunter, Analyst, Skeptic, Historian, Writer — with visible per-node progress.

**Why:** this is your graduation from `create_agent` (the pre-built loop) to LangGraph proper (you design the loop). Explicit graphs are how production agent systems are actually built — controllable, debuggable, resumable — and "I orchestrated a multi-agent pipeline with LangGraph, here's the graph diagram" is the strongest single line this project puts in your mouth. Budget-wise, a *structured* pipeline also spends fewer LLM calls than a free-roaming agent: control is economy.

**Steps:**

1. *(2 h)* Learn the core LangGraph API from the docs/Academy module: define a `TypedDict` state, `StateGraph(State)`, `add_node`, `add_edge`, `add_conditional_edges`, compile, stream. Build a toy 3-node graph first (fetch → summarize → format) to feel the mechanics without project stakes. Render it: LangGraph can draw the compiled graph as a Mermaid diagram — generate it and keep it (it goes in the README).
2. *(60 min)* Design `InvestigationState` on paper: `url`, `article`, `search_results[]`, `claims[]`, `memory_briefing`, `contradictions[]`, `report`, `errors[]`. Every node reads from and writes into this one shared object — that's the whole coordination model, and designing it well is the actual work.
3. *(3 h)* Implement the nodes, mostly by *relocating* Stage B/C code into functions of `state`:
   - **Hunter** — fetch the article, find original source + independent coverage (your tools, called directly in code: not everything needs an LLM decision).
   - **Analyst** — claim/entity extraction (Phase 11 step).
   - **Historian** — memory briefing (Phase 12 step).
   - **Skeptic** — the star: pair up claims across sources and across history; for each pair on the same subject+metric, a structured LLM verdict (`consistent | contradictory | unclear` + rationale); write findings to `state["contradictions"]`.
   - **Writer** — final structured report from the full state, smart model.
   Wire mostly sequential edges plus one conditional edge (e.g., Hunter found < 2 sources → route to a broader-search retry once, then continue regardless). Cap any loops.
4. *(90 min)* Streaming + resilience: stream per-node progress into the persisted investigation doc and the UI ("🕵️ Skeptic: comparing 9 claims across 5 sources…"); wrap nodes so one failure writes to `state["errors"]` and the graph continues degraded instead of dying.
5. *(90 min)* Compare: run the same URL through old V1 agent and new graph. Note report quality, LLM-call count (LangSmith), and failure behavior in `LEARNING_LOG.md` — this comparison is interview gold ("why explicit orchestration beats a free agent for fixed workflows — and when it doesn't").

**Checkpoint:** the graph runs end-to-end with live per-node progress, survives a source failure, and produces a report with a real contradictions section; you have its Mermaid diagram.

**Self-test:** What is state in LangGraph and who owns it? When do you let an LLM decide the route vs. hard-coding the edge? Why did the Skeptic need *structured* verdicts?

**Commit / PR:** `Replace single agent with multi-specialist LangGraph pipeline`

---

### Phase 14 — Timelines & the knowledge graph view (~6 h)

**Goal:** two showcase visualizations from data you already have: an entity timeline and an interactive entity–claim graph.

**Why:** this converts invisible database richness into the thing people *remember* about your project. It's also honest proof of your schema design — you can only draw a knowledge graph if you actually built one.

**Steps:**

1. *(2 h)* **Timeline**: for a chosen entity, pull its claims/events with dates (`published_at` / `first_seen`), sort, and render in Streamlit — a clean vertical markdown timeline is fine; a Plotly scatter-on-time-axis if you want polish. Add an entity picker.
2. *(2.5 h)* **Knowledge graph**: `uv add pyvis`. Build a small network — entity nodes, claim nodes, edges entity↔claim and claim↔investigation, colored by claim status — export pyvis HTML and embed via `st.components.v1.html`. Cap at the top ~50 nodes (most-connected) so your 2017 CPU's browser stays smooth; add a "focus on entity" filter.
3. *(90 min)* UI coherence pass: sidebar navigation (Investigate / History / Claims / Graph / Timeline), one-line explainer per page, loading states. Then stop — polish has diminishing returns and Phase 15 is worth more.

**Checkpoint:** after ~10 total investigations, the graph page shows a genuine connected web and the timeline reads like a story.

**Self-test:** Which Mongo queries feed the graph, and what index would you add if entities numbered 100k? Why cap rendered nodes?

**Commit / PR:** `Add knowledge graph and entity timeline visualizations`

---

### Phase 15 — Portfolio packaging: README, demo, deploy, LinkedIn (~6 h)

**Goal:** a stranger understands the project in 60 seconds; a recruiter can try it or watch it in 90.

**Why:** unpackaged projects don't exist. The last 5% of work produces 50% of the career value — this phase *is* the LinkedIn/GitHub goal you started with.

**Steps:**

1. *(2 h)* **The README** (order matters):
   - One-line pitch + a hero demo GIF/MP4 right at the top.
   - "Why this isn't a ChatGPT wrapper" — persistent investigations, claim lifecycle, memory across time, multi-agent orchestration (four bullets, link each to code).
   - Architecture: your Mermaid graph from Phase 13 + a data-model sketch of the collections.
   - Stack list, honest **Limitations** section (free-tier quotas, extraction imperfection — self-awareness reads as seniority), Quickstart (`git clone`, `uv sync`, `.env` from `.env.example`, run), Roadmap (from `IDEAS.md`), "What I learned."
2. *(60 min)* **The demo video**: 60–90 s screen recording — paste URL, agents work with visible progress, contradiction flagged, 5 s each on claims table and knowledge graph. Record with SimpleScreenRecorder/Kooha; convert a short version to GIF with `ffmpeg` for the README top, upload the full MP4 to the GitHub release/README.
3. *(90 min)* **Deploy (optional but high-value)**: Streamlit Community Cloud → connect the repo → put keys in its *Secrets* manager (never in git; also verify Atlas network access allows the cloud host). Since a public app spends *your* free quotas, add a tiny access code gate read from secrets, or a demo mode that only browses existing investigations. If deployment fights you for more than the budgeted time, the video demo is a perfectly respectable fallback — say so in the README.
4. *(30 min)* **GitHub profile day**: pin the repo, add topics (`ai-agents`, `langgraph`, `mongodb`, `rag`, `python`), a clean About line + link, and a short profile README introducing yourself.
5. *(60 min)* **LinkedIn post #3** (the big one): the demo video, the origin story (three posts back!), 3 concrete things you learned (name real concepts: tool calling, vector search, state graphs), the repo link, and what you'd build next. Then update your LinkedIn Projects/Featured section with it.

**Checkpoint:** you send the repo link to one technical friend and one non-technical friend; both can tell you what it does. 

**Commit:** `Add documentation, demo, and deployment` — then take the evening off. You earned it.

---

## Appendix A — The 429 survival kit (free-tier engineering)

You *will* hit rate limits (HTTP 429). Treat it as a design input, not an accident:

1. **Route by difficulty.** Flash-Lite by default; the smart model only for extraction, verification verdicts, and the final report. Your `get_llm(tier=...)` helper from Phase 3 makes this one line per call site.
2. **Retry with exponential backoff.** LangChain chat models accept `max_retries`; for anything custom, wrap calls in a small retry helper (sleep 2 s, 4 s, 8 s). Respect any retry-after hint in the error.
3. **Fail over across three providers.** Catch a persistent 429 from Gemini → retry on Groq (mind its small tokens-per-minute cap — send it summaries, not full articles) → if Groq also fails or you're offline, fall back to `get_llm("local")` (Ollama). Three independent quotas: you almost never run out of all three simultaneously. The cascade in `get_llm()` is the architecture.
4. **Cache everything cacheable.** Articles (done, Phase 5), searches (done, Phase 6), embeddings where practical. For VoyageAI embeddings specifically: store the resulting vector in the MongoDB document on first computation — never re-embed the same text twice. Your 200M free tokens last indefinitely at this project's scale, but the habit of not re-paying for the same bytes is the professional one.
5. **Keep prompts lean.** Truncate articles, summarize before re-use, cap memory briefings. Tokens-per-minute limits bite before request limits when you're careless with context.
6. **Cap the loops.** Recursion/iteration limits on every agent and graph. One runaway loop can eat a day's quota in minutes.
7. **Watch the meters.** Your `usage` collection + LangSmith traces tell you exactly where quota goes. Check weekly; optimize the top spender only.

## Appendix B — Pitfalls that end projects (and their antidotes)

- **Committing secrets.** Antidote: `.gitignore` before first commit (done in Phase 2); if a key ever leaks, *rotate it at the provider immediately* — git history is forever.
- **Tutorial hell.** Consuming courses feels like progress and isn't. Antidote: the 1:2 rule — for every hour of course/docs, two hours building on your own repo.
- **Scope creep.** Antidote: `IDEAS.md` is where shiny things go to wait.
- **The 3-hour bug spiral.** Antidote: the 45-minute rule from Part 1.
- **Atlas connection suddenly failing after weeks.** Almost always the IP allowlist (home IP changed). Check Network Access first, always.
- **Scraping despair.** Some sites will never yield to trafilatura (paywalls, aggressive JS). Antidote: graceful failure + Tavily's content snippets as fallback. An investigator that says "couldn't access X, relied on Y and Z" is *more* credible, not less.
- **Non-determinism confusion.** The same input can produce different agent paths — that's temperature and the nature of LLMs, not necessarily your bug. Antidote: temperature 0 for extraction/verdicts; judge conversational steps by *distribution* of behavior, not single runs; read traces before touching code.
- **Motivation dip around week 7–9.** Predictable and survivable. Antidote: the Phase 9 milestone is placed there on purpose — ship the post, absorb the dopamine, continue.

## Appendix C — Glossary (say these fluently by the end)

- **Agent** — an LLM in a loop that chooses actions (tool calls) toward a goal, observes results, and iterates.
- **Tool / tool calling** — a Python function exposed to the model via name + docstring + schema; the model outputs a request to call it, your runtime executes it.
- **ReAct loop** — the reason–act–observe cycle that `create_agent` implements for you.
- **System prompt** — standing instructions defining persona, method, and constraints; separate from the user's message.
- **Structured output** — forcing model responses into a validated schema (Pydantic) instead of prose.
- **Token** — the sub-word unit models read and emit; the currency of context windows and rate limits.
- **Temperature** — output randomness; 0 for extraction and verdicts, higher for prose.
- **Embedding** — a vector (here, 1024 floats for VoyageAI or 384 for sentence-transformers) whose geometry encodes meaning; nearby vectors ≈ similar meaning.
- **Vector search** — retrieval by embedding proximity (cosine similarity), via Atlas `$vectorSearch` here.
- **RAG** — retrieval-augmented generation: fetch relevant stored knowledge, put it in context, then generate.
- **VoyageAI** — MongoDB-owned embedding model family; `voyage-4-lite` (1024 dims) is your free choice here. Outperforms most general-purpose embeddings on retrieval benchmarks.
- **autoEmbed** — Atlas feature (public preview May 2026) that auto-generates Voyage embeddings on document insert, removing the need for an explicit embedding pipeline step.
- **Ollama** — a tool for running quantized LLMs locally. Manages model downloads and serves an OpenAI-compatible HTTP API on localhost; LangChain connects to it transparently.
- **Quantization** — compressing a model's weights from 16-bit floats to 4-bit integers (Q4_K_M). Shrinks a 7B model from ~14 GB to ~4.5 GB at the cost of minor quality loss. Makes local LLMs fit in ordinary RAM.
- **State (LangGraph)** — the shared, typed object every node reads and writes; the coordination backbone of the graph.
- **Node / edge / conditional edge** — a work step; a fixed transition; a routed transition decided at runtime.
- **Checkpointer / trace** — LangGraph's persistence of state; LangSmith's record of every call — how you debug what "thought" happened.
- **Upsert / idempotency** — update-or-insert; the property that running the same operation twice changes nothing extra. Cache-and-retry logic depends on both.

## Appendix D — Target repository layout

```
news-investigator/
├── app.py                      # Streamlit entry point
├── src/investigator/
│   ├── llm.py                  # get_llm(tier): Gemini → Groq → Ollama cascade
│   ├── db.py                   # Mongo client, saves, indexes
│   ├── embeddings.py           # embed_text(): VoyageAI (primary) or sentence-transformers (fallback)
│   ├── tools/
│   │   ├── articles.py         # fetch_article (trafilatura + cache)
│   │   └── search.py           # search_news, find_original_source (Tavily + cache)
│   ├── extraction.py           # claim/entity Pydantic models + prompts
│   ├── graph.py                # LangGraph StateGraph (Stage D)
│   ├── investigation.py        # run_investigation orchestration
│   └── cli.py
├── docs/
│   ├── PLAN.md                 # this file — tick as you go
│   ├── SCHEMA.md               # collections & design decisions
│   └── IDEAS.md                # scope-creep parking lot
├── LEARNING_LOG.md
├── .env.example                # GOOGLE_API_KEY, GROQ_API_KEY, VOYAGE_API_KEY, TAVILY_API_KEY, MONGODB_URI, OLLAMA_MODEL
├── .gitignore                  # includes .env
├── pyproject.toml / uv.lock
└── README.md
```

## Appendix E — Stretch ideas (post-V4, only if hungry)

Semantic claim deduplication with your embeddings · a scheduled watcher that re-checks *unverified* claims weekly (cron + a "claim resolved" diff — the strongest possible demo of knowledge-over-time) · source-reliability scoring learned from your own evidence records · FastAPI backend split (turns the project into a "real" API service — a strong V2 of the portfolio story) · exporting an investigation as a shareable PDF · evaluation harness: a small labeled set of articles and a script that scores extraction quality across prompt versions (this one teaches more than it demos).

---

*Last note: this plan is a map, not a contract. When reality diverges — a library changed, a free tier moved, a phase bores you — adjust and write down why in the log. Judgment under changing conditions is the actual skill being trained.*
