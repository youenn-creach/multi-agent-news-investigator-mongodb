"""Render the GitHub social preview image (1280x640) from an inline HTML card.

Run: uv run --with playwright python scripts/assets/social_preview.py
Then upload docs/img/social-preview.png in the repo: Settings -> Social preview.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[2] / "docs" / "img" / "social-preview.png"

HTML = """
<html><body style="margin:0;width:1280px;height:640px;font-family:'Inter','Segoe UI',Helvetica,Arial,sans-serif;
  background:radial-gradient(circle at 15% 20%,#16324a 0%,#0b1220 55%);color:#f4f7fb;display:flex;flex-direction:column;
  justify-content:center;padding:0 90px;box-sizing:border-box;position:relative;overflow:hidden">
  <div style="position:absolute;right:-120px;top:-120px;width:520px;height:520px;border-radius:50%;
    background:radial-gradient(circle,#13aa5266 0%,transparent 70%)"></div>
  <div style="font-size:26px;letter-spacing:3px;color:#5fd38d;font-weight:600">AGENTIC AI  ·  FACT-CHECKING</div>
  <div style="font-size:84px;font-weight:800;line-height:1.05;margin:22px 0 26px">Multi-Agent<br>News Investigator</div>
  <div style="font-size:32px;color:#b9c6d8;max-width:980px;line-height:1.35">
    Specialist agents extract claims, find independent sources and <b style="color:#fff">remember</b> past investigations.</div>
  <div style="display:flex;gap:16px;margin-top:44px;font-size:26px;font-weight:600">
    <span style="padding:10px 22px;border-radius:999px;background:#13aa52;color:#04210f">MongoDB Atlas Vector Search</span>
    <span style="padding:10px 22px;border-radius:999px;background:#1f2f45;border:1px solid #38506f">Voyage AI</span>
    <span style="padding:10px 22px;border-radius:999px;background:#1f2f45;border:1px solid #38506f">LangGraph</span>
  </div>
  <div style="position:absolute;bottom:34px;left:90px;font-size:22px;color:#7f93ad;font-family:monospace">
    hunter → analyst → searcher → historian → skeptic → writer</div>
</body></html>
"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 640})
    page.set_content(HTML)
    page.wait_for_timeout(300)
    page.screenshot(path=OUT)
    browser.close()
print("saved", OUT)
