"""LLM routing: pick a model by difficulty tier, fall back across providers.

Tiers:
  "cheap"  - default workhorse (high free quota)
  "smart"  - extraction, verification, final report

Each tier is a chain: Gemini -> Groq -> Ollama (local). If a provider fails
(rate limit 429, outage, bad key), LangChain's `with_fallbacks` tries the next.
"""
import os
from typing import Literal

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

load_dotenv()

Tier = Literal["cheap", "smart"]

GEMINI_MODELS = {"cheap": "gemini-3.5-flash-lite", "smart": "gemini-3.8-flash"}
GROQ_MODELS = {"cheap": "openai/gpt-oss-20b", "smart": "openai/gpt-oss-120b"}


def get_llm(tier: Tier = "cheap", temperature: float = 0) -> BaseChatModel:
    """Return a chat model for the tier, with provider fallbacks attached."""
    ollama_model = os.getenv("OLLAMA_MODEL", "ministral-3:3b")
    chain = [
        ChatGoogleGenerativeAI(
            model=GEMINI_MODELS[tier], temperature=temperature, max_retries=1
        ),
        ChatGroq(model=GROQ_MODELS[tier], temperature=temperature, max_retries=1),
        ChatOllama(model=ollama_model, temperature=temperature),
    ]
    return chain[0].with_fallbacks(chain[1:])


def get_provider(tier: Tier, provider: Literal["gemini", "groq", "ollama"]) -> BaseChatModel:
    """One specific provider, no fallback (used to test each link of the chain)."""
    if provider == "gemini":
        return ChatGoogleGenerativeAI(model=GEMINI_MODELS[tier], temperature=0)
    if provider == "groq":
        return ChatGroq(model=GROQ_MODELS[tier], temperature=0)
    return ChatOllama(model=os.getenv("OLLAMA_MODEL", "ministral-3:3b"), temperature=0)
