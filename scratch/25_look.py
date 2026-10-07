"""Take quick screenshots of every page, for visual review (not for the README)."""
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT = Path("/tmp/claude-1000/look"); OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1400, "height": 900})
    pg.goto("http://localhost:8501/?page=investigate"); pg.get_by_label("Article URL").wait_for(timeout=60000); pg.wait_for_timeout(2000)
    pg.get_by_text("Use an example article").click(); pg.wait_for_timeout(1500)
    pg.screenshot(path=OUT / "investigate.png")
    for name in ("history", "claims", "graph"):
        pg.goto(f"http://localhost:8501/?page={name}"); pg.wait_for_timeout(6000)
        pg.screenshot(path=OUT / f"{name}.png")
    b.close()
print("ok")
