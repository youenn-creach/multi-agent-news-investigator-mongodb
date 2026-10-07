"""Record a real investigation in the app and turn it into an animated GIF for the README.

Needs the app running on :8501. Run:
    uv run --with playwright --with pillow python scripts/assets/demo_gif.py
"""
import io
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

URL = "https://www.cnbc.com/2026/09/10/ecb-interest-rate-hike-lagarde-iran.html"
OUT = Path(__file__).resolve().parents[2] / "docs" / "img" / "demo.gif"
WIDTH = 960  # output width in pixels

frames: list[tuple[Image.Image, int]] = []  # (image, duration in ms)


def snap(page, ms: int) -> None:
    img = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
    img = img.resize((WIDTH, int(img.height * WIDTH / img.width)), Image.LANCZOS)
    frames.append((img, ms))


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 1150})
    page.goto("http://localhost:8501/?page=investigate")
    page.get_by_label("Article URL").wait_for(timeout=60_000)
    page.wait_for_timeout(1000)
    snap(page, 1200)

    page.get_by_label("Article URL").fill(URL)
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)
    snap(page, 900)

    page.get_by_role("button", name="Investigate").click()
    # live progress: one frame every ~1.5 s until the app says it is done
    for _ in range(120):
        page.wait_for_timeout(1500)
        snap(page, 700)
        if page.get_by_text("Investigation complete").count():
            break
    page.wait_for_timeout(800)
    snap(page, 2500)

    page.mouse.wheel(0, 700)  # scroll the report
    page.wait_for_timeout(500)
    snap(page, 2500)

    for label, hold in [("Timeline", 3200), ("Graph", 3200)]:
        page.get_by_text(label, exact=False).first.click()
        page.wait_for_timeout(5000 if label == "Graph" else 2500)
        snap(page, hold)
    browser.close()

images = [f[0].quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in frames]
images[0].save(OUT, save_all=True, append_images=images[1:], duration=[f[1] for f in frames], loop=0, optimize=True)
print(f"saved {OUT} ({len(frames)} frames, {OUT.stat().st_size / 1e6:.1f} MB)")
