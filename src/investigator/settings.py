"""Environment access with friendly errors (a missing key is the #1 first-run problem)."""
import os

from dotenv import load_dotenv

load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Copy .env.example to .env and fill it in (see the README Quickstart).")
    return value
