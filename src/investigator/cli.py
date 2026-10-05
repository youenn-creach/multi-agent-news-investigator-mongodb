"""Usage: uv run python -m investigator.cli <article-url>"""
import sys

from investigator.investigation import run_investigation

ICONS = {"hunter": "🔎", "searcher": "🌐", "broaden": "🔁", "analyst": "🧩", "historian": "📚", "skeptic": "🤨", "writer": "✍️"}


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    result = run_investigation(sys.argv[1], on_step=lambda node, d: print(f"{ICONS.get(node, '•')} {node} done"))
    r = result["report"]
    print(f"\nVerdict: {r['verdict']} (confidence: {r['confidence']})\n\n{r['summary']}")
    for flag in r["flags"]:
        print(f"  ⚑ {flag}")
    for s in r["sources"]:
        print(f"  ✓ {s['source']}: {s['url']}")
    if result["errors"]:
        print("\nProblems along the way:", *result["errors"], sep="\n  - ")


if __name__ == "__main__":
    main()
