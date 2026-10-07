"""Generate the README architecture diagram (docs/img/architecture.svg and .png).

Run: uv run --with playwright python scripts/assets/architecture_diagram.py
The SVG is written by hand-placed coordinates below; Playwright's Chromium renders it to a 2x PNG
(the README uses the PNG, because SVG fonts can differ between viewers).
"""
from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[2] / "docs" / "img"
W, H = 1400, 930

GREEN, GREEN_DK = "#13aa52", "#0b5d2e"
AMBER = "#f2b84b"
INK, MUTED, FAINT = "#e8eef7", "#9fb0c6", "#6f8199"
CARD, CARD_LINE = "#14233a", "#2c4768"
FONT = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'DejaVu Sans Mono', Consolas, monospace"

parts: list[str] = []


def add(s: str) -> None:
    parts.append(s)


def text(x, y, s, size=13, fill=INK, weight=400, anchor="start", mono=False, spacing=0, opacity=1):
    fam = MONO if mono else FONT
    add(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}" letter-spacing="{spacing}" opacity="{opacity}">{escape(s)}</text>')


def rect(x, y, w, h, rx=12, fill=CARD, stroke=CARD_LINE, sw=1.2, dash=None, extra=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d} {extra}/>')


def pill(x, y, w, h, label, fill, stroke, color=INK, size=11.5, weight=600, mono=False):
    rect(x, y, w, h, rx=h / 2, fill=fill, stroke=stroke, sw=1)
    text(x + w / 2, y + h / 2 + size * 0.35, label, size=size, fill=color, weight=weight, anchor="middle", mono=mono)


def arrow(x1, y1, x2, y2, color=MUTED, dash=None, marker="arr"):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.8"{d} marker-end="url(#{marker})"/>')


# ---------- defs and background ----------
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
add(f'''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0d1a2c"/><stop offset="1" stop-color="#08101c"/></linearGradient>
<radialGradient id="glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{GREEN}" stop-opacity="0.32"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></radialGradient>
<marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker>
<marker id="arrG" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{GREEN}"/></marker>
<marker id="arrA" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{AMBER}"/></marker>
</defs>''')
rect(0, 0, W, H, rx=0, fill="url(#bg)", stroke="none", sw=0)
add(f'<circle cx="1180" cy="560" r="330" fill="url(#glow)"/>')

# ---------- header ----------
text(30, 40, "ONE INVESTIGATION, END TO END", 13, GREEN, 700, spacing=3)
text(30, 66, "A LangGraph state graph: every step reads the shared state and returns only what it changes.", 15, MUTED)

# ---------- row A: the pipeline ----------
Y, NH, NW, X0, STEP = 128, 142, 160, 170, 188
AY = Y + 71  # y of the arrows between steps
steps = [
    ("1", "hunter", ["Fetch the article"], "trafilatura", "articles", False, False),
    ("2", "analyst", ["Extract claims", "and entities"], "Pydantic schema", "claims · entities", True, False),
    ("3", "searcher", ["Find independent", "coverage"], "Tavily news search", "searches · usage", False, False),
    ("4", "historian", ["Recall similar", "past claims"], "Voyage AI embeddings", "claims (vector search)", False, True),
    ("5", "skeptic", ["Judge each claim", "against the evidence"], "strict verdicts", "claims.evidence", True, False),
    ("6", "writer", ["Write the sourced", "report"], "verdict + confidence", "investigations", True, False),
]
# input and output chips
rect(20, AY - 31, 112, 62, rx=14, fill="#10304a", stroke="#2f6a9a")
text(76, AY - 4, "Article URL", 14, INK, 700, "middle")
text(76, AY + 15, "app or CLI", 11.5, MUTED, 400, "middle")
arrow(134, AY, X0 - 4, AY)
rect(1290, AY - 31, 96, 62, rx=14, fill="#10304a", stroke="#2f6a9a")
text(1338, AY - 4, "Report", 14, INK, 700, "middle")
text(1338, AY + 15, "verdict · sources", 11, MUTED, 400, "middle")
arrow(X0 + 5 * STEP + NW + 2, AY, 1286, AY)

for i, (num, name, role, tool, store, llm, vec) in enumerate(steps):
    x = X0 + STEP * i
    edge = GREEN if vec else CARD_LINE
    rect(x, Y, NW, NH, rx=14, fill=CARD, stroke=edge, sw=2 if vec else 1.2)
    add(f'<path d="M{x},{Y + 14} a14,14 0 0 1 14,-14 h{NW - 28} a14,14 0 0 1 14,14 v22 h-{NW} z" fill="{GREEN_DK if vec else "#1c3556"}"/>')
    add(f'<circle cx="{x + 22}" cy="{Y + 21}" r="11" fill="{GREEN if vec else "#3b6aa0"}"/>')
    text(x + 22, Y + 26, num, 13, "#04210f" if vec else "#fff", 800, "middle")
    text(x + 41, Y + 27, name, 16.5, INK, 700)
    for j, line in enumerate(role):
        text(x + 14, Y + 62 + 17 * j, line, 13, INK, 500)
    pill(x + 12, Y + 92, NW - 24, 22, tool, "#0f1b2d", "#35557c" if not vec else GREEN, MUTED if not vec else "#9ae6b4", 11, 600)
    text(x + 14, Y + 132, "→ " + store, 11.5, "#6fdc9a" if store != "investigations" else "#6fdc9a", 600, mono=False)
    if llm:
        pill(x + NW - 46, Y + 8, 38, 18, "LLM", "#3a2c0c", AMBER, AMBER, 10, 800)
    if i < 5:
        arrow(x + NW + 2, AY, x + STEP - 4, AY)
    # dotted link down to the shared-state strip
    add(f'<line x1="{x + NW / 2}" y1="{Y + NH}" x2="{x + NW / 2}" y2="{Y + NH + 22}" stroke="{FAINT}" stroke-width="1.5" stroke-dasharray="2 4"/>')

# the "not enough sources" loop above the searcher
sx = X0 + STEP * 2
add(f'<path d="M{sx + 40},{Y} C{sx + 40},{Y - 34} {sx + 120},{Y - 34} {sx + 120},{Y - 2}" fill="none" stroke="{AMBER}" stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#arrA)"/>')
text(sx + 80, Y - 40, "fewer than 2 sources: search once more", 11, AMBER, 600, "middle")

# ---------- shared state strip ----------
SY = Y + NH + 22
rect(X0 - 10, SY, 5 * STEP + NW + 20, 46, rx=23, fill="#0e1a2c", stroke=FAINT, sw=1.2, dash="6 5")
text(X0 + 8, SY + 28, "SHARED STATE", 11.5, MUTED, 800, spacing=1.5)
labels = ["url", "article", "sources", "claims", "memory", "verdicts", "report", "errors"]
cx = X0 + 150
for lab in labels:
    w = 22 + 8.2 * len(lab)
    pill(cx, SY + 11, w, 24, lab, "#16273f", "#3a5a85", "#c9d8ec", 12, 500, mono=True)
    cx += w + 12
text(X0 + 5 * STEP + NW - 6, SY + 28, "a failing step adds to errors; the graph carries on", 11, FAINT, 400, "end")

# ---------- row C left: LLM cascade and services ----------
PY, PH = 378, 515
rect(20, PY, 520, PH, rx=18, fill="#0f1b2e", stroke="#33507a", sw=1.4)
text(42, PY + 34, "LLM routing", 17, INK, 700)
pill(150, PY + 18, 54, 20, "LLM", "#3a2c0c", AMBER, AMBER, 10, 800)
text(214, PY + 33, "= step uses it", 11.5, MUTED)
text(42, PY + 58, "Every call has a hard deadline: a stuck provider is abandoned, the next one answers.", 12, MUTED)

def tier(y, name, chips):
    text(42, y + 27, name, 13, AMBER, 800, spacing=1)
    xs = [104, 254, 404]
    for k, (label, sub) in enumerate(chips):
        rect(xs[k], y, 126, 50, rx=11, fill="#16253d" if k < 2 else "#0f2a1c", stroke="#3a5a85" if k < 2 else GREEN, sw=1.2)
        text(xs[k] + 63, y + 22, label, 12.5, INK, 700, "middle")
        text(xs[k] + 63, y + 39, sub, 10.5, MUTED, 400, "middle")
        if k < 2:
            arrow(xs[k] + 128, y + 25, xs[k + 1] - 3, y + 25, AMBER, marker="arrA")

tier(PY + 86, "SMART", [("Gemini", "3.5 Flash"), ("Groq", "gpt-oss-120b"), ("Mistral", "local · Ollama")])
tier(PY + 154, "CHEAP", [("Gemini", "3.5 Flash-Lite"), ("Groq", "gpt-oss-20b"), ("Mistral", "local · Ollama")])
text(104, PY + 232, "on rate limit (429), timeout or outage →", 11.5, AMBER, 500)
text(42, PY + 262, "Local Mistral is free and unlimited: it keeps the project working offline.", 12, MUTED)

add(f'<line x1="42" y1="{PY + 286}" x2="518" y2="{PY + 286}" stroke="#274064" stroke-width="1"/>')
text(42, PY + 314, "External services (all on free tiers)", 14, INK, 700)
services = [
    ("Tavily", "news search · results cached 7 days · credit counter", "#5aa9ff"),
    ("trafilatura", "clean article text from any web page", "#5aa9ff"),
    ("Voyage AI", "voyage-4-lite · 1024-dim embeddings via Atlas", GREEN),
]
for k, (n, d, col) in enumerate(services):
    yy = PY + 340 + 42 * k
    add(f'<circle cx="52" cy="{yy + 8}" r="6" fill="{col}"/>')
    text(68, yy + 13, n, 13.5, INK, 700)
    text(68, yy + 31, d, 11.5, MUTED)
text(42, PY + 488, "Every provider needs only a free key; nothing here costs money.", 11.5, FAINT)

# ---------- row C right: MongoDB Atlas ----------
AX = 560
rect(AX, PY, 820, PH, rx=18, fill="#0e2418", stroke=GREEN, sw=2)
add(f'<circle cx="{AX + 30}" cy="{PY + 30}" r="11" fill="{GREEN}"/>')
add(f'<path d="M{AX + 30},{PY + 21} q6,8 0,18 q-6,-10 0,-18z" fill="#04210f"/>')
text(AX + 52, PY + 36, "MongoDB Atlas", 18, INK, 700)
text(AX + 800, PY + 36, "free M0 cluster · database news_investigator", 12, "#8fd9ad", 400, "end")

def coll(x, y, w, h, name, lines, hot=False):
    rect(x, y, w, h, rx=12, fill="#12301f" if hot else "#10261a", stroke=GREEN if hot else "#2a6b44", sw=2.2 if hot else 1.2)
    text(x + 14, y + 26, name, 15.5, INK, 700, mono=True)
    for j, l in enumerate(lines):
        text(x + 14, y + 49 + 17 * j, l, 11.8, "#b9ddc8", 400)

C1, C2, C3 = AX + 20, AX + 285, AX + 550
CW = 250
R1, R2 = PY + 66, PY + 246
coll(C1, R1, CW, 150, "articles", ["fetched text and metadata", "unique index on url:", "re-fetching never duplicates"])
coll(C2, R1, CW, 150, "claims", ["text · status · evidence · embedding", "unverified → corroborated /", "disputed / contradicted"], hot=True)
pill(C2 + 14, R1 + 108, CW - 28, 26, "Atlas Vector Search · cosine · 1024-d", GREEN, GREEN, "#04210f", 11.5, 800)
coll(C3, R1, CW, 150, "entities", ["people, organisations, places", "unique key: normalised name", "links claims to the graph"])
coll(C1, R2, CW, 120, "searches", ["cached Tavily results", "TTL index: MongoDB deletes", "them after 7 days"])
coll(C2, R2, CW, 120, "investigations", ["one document per run:", "steps are saved as they happen,", "so a crash leaves a partial record"])
coll(C3, R2, CW, 120, "usage", ["monthly search-credit counter", "the tool refuses to search", "past the free budget"])

# memory loop: historian -> claims ($vectorSearch)
hx = X0 + STEP * 3 + NW / 2
add(f'<path d="M{hx},{SY + 46} C{hx},{SY + 118} {C2 + 70},{SY + 80} {C2 + 70},{R1 - 3}" fill="none" stroke="{GREEN}" stroke-width="3" marker-end="url(#arrG)"/>')
pill(C2 + 86, R1 - 30, 178, 22, "recall: $vectorSearch", "#0b3b20", GREEN, "#9ae6b4", 11.5, 700, mono=False)

# bottom ribbons inside the Atlas panel
RY = R2 + 140
rect(AX + 20, RY, 780, 44, rx=11, fill="#0b2d1b", stroke="#2a6b44", sw=1)
text(AX + 36, RY + 19, "Timeline page", 12.5, "#9ae6b4", 800)
text(AX + 36, RY + 35, "one aggregation pipeline:", 11.5, "#b9ddc8")
text(AX + 224, RY + 28, "$vectorSearch  →  $unwind  →  $lookup(articles)  →  $sort", 13, INK, 600, mono=True)
rect(AX + 20, RY + 54, 780, 44, rx=11, fill="#0b2d1b", stroke="#2a6b44", sw=1)
text(AX + 36, RY + 73, "Claim dedup", 12.5, "#9ae6b4", 800)
text(AX + 36, RY + 89, "same fact, new wording:", 11.5, "#b9ddc8")
text(AX + 224, RY + 82, "cosine ≥ 0.985 and same numbers → merge   ·   0.93–0.985 → LLM judge   ·   below → keep", 12.5, INK, 600, mono=False)

# ---------- footer legend ----------
text(30, H - 18, "Streamlit UI reads it all: Investigate · History · Claims · Timeline · Graph", 12.5, MUTED)
text(W - 30, H - 18, "green = MongoDB Atlas   ·   amber = LLM cascade   ·   dashed = shared state", 12.5, FAINT, 400, "end")
add("</svg>")

svg = "\n".join(parts)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "architecture.svg").write_text(svg, encoding="utf-8")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
    page.set_content(f'<html><body style="margin:0;background:#08101c">{svg}</body></html>')
    page.wait_for_timeout(300)
    page.screenshot(path=OUT / "architecture.png")
    browser.close()
print("saved architecture.svg and architecture.png")
