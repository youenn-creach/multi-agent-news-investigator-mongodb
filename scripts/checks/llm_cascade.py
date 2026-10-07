"""Check every provider individually, then check the fallback chain."""
import time

from investigator.llm import get_llm, get_provider

PROMPT = "In one sentence, what is a news fact-checker?"

for provider in ("gemini", "groq", "ollama"):
    for tier in ("cheap", "smart"):
        start = time.time()
        try:
            reply = get_provider(tier, provider).invoke(PROMPT)
            print(f"OK   {provider:7} {tier:6} {time.time() - start:5.1f}s  {reply.text[:70]!r}")
        except Exception as e:
            print(f"FAIL {provider:7} {tier:6} {type(e).__name__}: {str(e)[:90]}")

print("\nFallback chain (smart):")
print(get_llm("smart").invoke(PROMPT).text)

print("\nForced failure: Gemini gets a bad key, Groq should answer instead:")
from langchain_google_genai import ChatGoogleGenerativeAI
from investigator.llm import get_provider
broken = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", api_key="bad-key", max_retries=0)
chain = broken.with_fallbacks([get_provider("cheap", "groq")])
print(chain.invoke(PROMPT).text)
