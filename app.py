"""Streamlit UI. Run with: uv run streamlit run app.py"""
from html import escape

import streamlit as st
from pyvis.network import Network

from investigator.db import get_db
from investigator.extraction import normalize
from investigator.investigation import run_investigation

st.set_page_config(page_title="News Investigator", page_icon="🕵️", layout="wide")

VERDICT_BADGE = {
    "reliable": "🟢", "mostly_reliable": "🟢", "mixed": "🟡", "unreliable": "🔴", "unverifiable": "⚪",
}
STATUS_COLOR = {"corroborated": "#2e9e5b", "disputed": "#e0a030", "contradicted": "#d64545", "unverified": "#9aa0a6"}
NODE_LABELS = {
    "hunter": "Fetching the article", "analyst": "Extracting claims", "searcher": "Searching for independent coverage",
    "broaden": "Coverage was thin: searching again", "historian": "Checking memory of past investigations",
    "skeptic": "Checking each claim against the evidence", "writer": "Writing the report",
}
NODE_ORDER = ["hunter", "analyst", "searcher", "historian", "skeptic", "writer"]


# ---------- shared rendering ----------
def show_report(inv: dict) -> None:
    report = inv.get("report")
    if not report:
        st.info(f"No report (status: {inv.get('status')}).")
        return
    st.subheader(f"{VERDICT_BADGE.get(report['verdict'], '')} {report['verdict'].replace('_', ' ').title()}  ·  confidence {report['confidence']}")
    st.write(report["summary"])
    for flag in report.get("flags", []):
        st.warning(flag, icon="⚠️")

    claims, verdicts = inv.get("claims", []), {v["claim_index"]: v for v in inv.get("verdicts", [])}
    if claims:
        st.markdown("**Claims checked**")
        icons = {"supports": "✅", "contradicts": "❌", "unclear": "❔"}
        for i, c in enumerate(claims):
            v = verdicts.get(i)
            st.markdown(f"{icons.get(v['verdict'], '▫️') if v else '▫️'} {c['text']}")
            if v:
                st.caption(v["note"])
    if report.get("sources"):
        st.markdown("**Sources that backed a claim**")
        for s in report["sources"]:
            st.markdown(f"- [{s['title'] or s['source']}]({s['url']}) · {s['source']}")
    if report.get("previously_seen"):
        with st.expander(f"📚 Memory: {len(report['previously_seen'])} similar claims seen before"):
            for m in report["previously_seen"]:
                st.markdown(f"- `{m['status']}` (similarity {m['similarity']}) {m['claim']}")


# ---------- pages ----------
def page_investigate() -> None:
    st.title("🕵️ Investigate an article")
    st.caption("Paste a news article URL. Specialist agents fetch it, extract claims, look for independent coverage, "
               "compare with past investigations and write a sourced reliability report.")
    url = st.text_input("Article URL", placeholder="https://www.example.com/news/...")
    if st.button("Investigate", type="primary", disabled=not url.strip()):
        done: list[str] = []
        with st.status("Investigation running…", expanded=True) as status:
            def on_step(node: str, delta: dict) -> None:
                done.append(node)
                msg = f"✓ {NODE_LABELS.get(node, node)}"
                if delta.get("errors"):
                    msg += f"  ⚠ {'; '.join(delta['errors'])}"
                st.write(msg)

            st.write("Starting…")
            try:
                result = run_investigation(url.strip(), on_step=on_step)
            except Exception as e:
                status.update(label="Investigation failed", state="error")
                st.error(f"{type(e).__name__}: {e}")
                return
            status.update(label="Investigation complete", state="complete", expanded=False)
        show_report(result)


def page_history() -> None:
    st.title("📜 History")
    invs = list(get_db().investigations.find({}, {"url": 1, "status": 1, "report.verdict": 1, "created_at": 1}).sort("created_at", -1).limit(100))
    if not invs:
        st.info("No investigations yet.")
        return
    labels = {
        str(i["_id"]): f"{i['created_at']:%d %b %H:%M} · {VERDICT_BADGE.get(i.get('report', {}).get('verdict', ''), '⚙️')} {i['url'][:80]}"
        for i in invs
    }
    chosen = st.selectbox("Investigation", list(labels), format_func=labels.get)
    inv = get_db().investigations.find_one({"_id": next(i["_id"] for i in invs if str(i["_id"]) == chosen)})
    st.markdown(f"[{inv['url']}]({inv['url']})")
    show_report(inv)
    with st.expander("Step log"):
        for s in inv.get("steps", []):
            st.markdown(f"- `{s['at']:%H:%M:%S}` **{s['node']}** {'⚠ ' + '; '.join(s['errors']) if s['errors'] else ''}")


def page_claims() -> None:
    st.title("🧩 Claims")
    st.caption("Every claim extracted so far, across all investigations, with its evidence trail.")
    statuses = st.multiselect("Status", list(STATUS_COLOR), default=list(STATUS_COLOR))
    query = st.text_input("Filter by text")
    claims = list(get_db().claims.find({"status": {"$in": statuses}}, {"embedding": 0}).sort("created_at", -1))
    if query:
        claims = [c for c in claims if query.lower() in c["text"].lower()]
    st.caption(f"{len(claims)} claims")
    for c in claims:
        with st.expander(f"{c['status'].upper()} · {c['text'][:110]}"):
            st.write(c["text"])
            st.caption(f"type: {c['type']} · subject: {c['subject']} · seen in {len(c['article_urls'])} article(s)")
            for e in c.get("evidence", []):
                st.markdown(f"- `{e['verdict']}` [{e['source'][:70]}]({e['source']}): {e['note']}")
            for u in c["article_urls"]:
                st.markdown(f"↳ [{u[:80]}]({u})")


def page_graph() -> None:
    st.title("🕸️ Knowledge graph")
    st.caption("Entities (blue), claims (colored by status) and the articles that mention them. Showing the most recent ~50 nodes.")
    db = get_db()
    claims = list(db.claims.find({}, {"embedding": 0}).sort("created_at", -1).limit(25))
    if not claims:
        st.info("Nothing to show yet: run an investigation first.")
        return
    entities = list(db.entities.find({}).limit(200))
    net = Network(height="620px", width="100%", bgcolor="#0e1117", font_color="#fafafa", cdn_resources="in_line")
    n_nodes = 0
    for c in claims:
        net.add_node(f"c{c['_id']}", label=escape(c["text"][:40]) + "…", title=escape(c["text"]), color=STATUS_COLOR[c["status"]], shape="dot", size=14)
        n_nodes += 1
        for u in c["article_urls"]:
            if u not in net.get_nodes():
                net.add_node(u, label=escape(u.split("/")[2]), title=escape(u), color="#c77dff", shape="square", size=10)
                n_nodes += 1
            net.add_edge(f"c{c['_id']}", u)
        for e in entities:
            if len(e["name"]) > 3 and normalize(e["name"]) in normalize(c["text"]):
                if f"e{e['_id']}" not in net.get_nodes() and n_nodes < 50:
                    net.add_node(f"e{e['_id']}", label=escape(e["name"]), title=escape(e["type"]), color="#4c9be8", size=18)
                    n_nodes += 1
                if f"e{e['_id']}" in net.get_nodes():
                    net.add_edge(f"e{e['_id']}", f"c{c['_id']}")
    st.iframe(net.generate_html(), height=640)


# ---------- navigation ----------
PAGES = {"🕵️ Investigate": page_investigate, "📜 History": page_history, "🧩 Claims": page_claims, "🕸️ Graph": page_graph}
# ?page=history (or investigate / claims / graph) opens a page directly, so pages can be linked
_wanted = next((i for i, name in enumerate(PAGES) if st.query_params.get("page", "") in name.lower()), 0) if st.query_params.get("page") else 0
choice = st.sidebar.radio("Navigate", list(PAGES), index=_wanted, label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption("Multi-agent news investigator · LangGraph + MongoDB Atlas + Voyage AI")
PAGES[choice]()
