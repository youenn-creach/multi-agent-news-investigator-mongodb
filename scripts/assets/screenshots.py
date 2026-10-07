"""Capture README screenshots. Needs the app running on :8501 and Playwright's Chromium.

Run: uv run --with playwright python scripts/assets/screenshots.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[2] / "docs" / "img"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://localhost:8501"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 1000})

    # 1. A finished report (History page opens on the latest investigation)
    page.goto(f"{BASE}/?page=history")
    page.get_by_text("Claims checked").wait_for(timeout=60_000)
    page.wait_for_timeout(1500)
    page.screenshot(path=OUT / "report.png")

    # 2. The knowledge graph (give the physics a few seconds to settle)
    page.goto(f"{BASE}/?page=graph")
    page.locator("iframe").wait_for(timeout=60_000)
    page.wait_for_timeout(6000)
    page.screenshot(path=OUT / "graph.png")

    # 3. The claims table with one claim opened to show its evidence trail
    page.goto(f"{BASE}/?page=claims")
    page.get_by_text("claims", exact=False).first.wait_for(timeout=60_000)
    page.wait_for_timeout(1500)
    page.locator("summary", has_text="CORROBORATED").first.click()
    page.wait_for_timeout(800)
    page.screenshot(path=OUT / "claims.png")

    # 4. The topic timeline: semantic search + $lookup + $sort in one pipeline
    page.goto(f"{BASE}/?page=timeline")
    page.get_by_text("By topic").click()
    page.get_by_placeholder("e.g. central bank raises borrowing costs").fill("central bank raises borrowing costs")
    page.keyboard.press("Enter")
    page.get_by_text("match 0.").first.wait_for(timeout=60_000)
    page.wait_for_timeout(1500)
    page.screenshot(path=OUT / "timeline.png")

    browser.close()
print("saved:", *sorted(f.name for f in OUT.glob("*.png")))
