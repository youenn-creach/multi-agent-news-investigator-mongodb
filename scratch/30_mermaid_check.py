"""Check that the README's Mermaid diagram parses (same library GitHub uses). Needs internet for the CDN."""
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

diagram = re.search(r"```mermaid\n(.*?)```", Path("README.md").read_text(), re.S).group(1)
html = """<html><body><div id="out"></div><script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
window.check = async (src) => { try { await mermaid.parse(src); const r = await mermaid.render('g', src); return 'OK ' + r.svg.length; } catch (e) { return 'ERROR ' + e.message; } };
window.ready = true;
</script></body></html>"""
with sync_playwright() as p:
    b = p.chromium.launch(); page = b.new_page(); page.set_content(html)
    page.wait_for_function("window.ready === true", timeout=30000)
    print(page.evaluate("src => window.check(src)", diagram)[:300]); b.close()
