"""Streamlit UI. Run with: uv run streamlit run app.py"""
from html import escape
from urllib.parse import urlparse

import streamlit as st
from pyvis.network import Network

from investigator import timeline
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
STATUS_BADGE = {"corroborated": "green", "disputed": "orange", "contradicted": "red", "unverified": "gray"}


def md_link(label: str, url: str) -> str:
    """A markdown link that cannot be broken by brackets or parentheses in web-supplied titles and URLs."""
    label = label.replace("[", "(").replace("]", ")")
    return f"[{label}]({url.replace(')', '%29').replace(' ', '%20')})"


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
            st.markdown(f"- {md_link(s['title'] or s['source'], s['url'])} · {s['source']}")
    if report.get("previously_seen"):
        with st.expander(f"📚 Memory: {len(report['previously_seen'])} similar claims seen before"):
            for m in report["previously_seen"]:
                st.markdown(f"- `{m['status']}` (similarity {m['similarity']}) {m['claim']}")


# ---------- pages ----------
def page_investigate() -> None:
    st.title("🕵️ Investigate an article")
    st.caption("Paste a news article URL. Specialist agents fetch it, extract claims, look for independent coverage, "
               "compare with past investigations and write a sourced reliability report.")
    EXAMPLE = "https://www.cnbc.com/2026/09/10/ecb-interest-rate-hike-lagarde-iran.html"
    st.text_input("Article URL", key="url_input", placeholder="https://www.example.com/news/...")
    st.button("Use an example article", on_click=lambda: st.session_state.update(url_input=EXAMPLE), type="tertiary")
    url = st.session_state.get("url_input", "")
    st.caption("🔎 fetch → 🧩 extract claims → 🌐 find independent coverage → 📚 recall similar past claims → 🤨 judge each claim → ✍️ write the report")
    db = get_db()
    c1, c2, c3 = st.columns(3)
    c1.metric("Investigations", db.investigations.count_documents({"status": "done"}))
    c2.metric("Claims in memory", db.claims.count_documents({}))
    c3.metric("Articles read", db.articles.count_documents({}))
    st.caption("Memory lives in MongoDB Atlas; similar claims are found with Atlas Vector Search over Voyage AI embeddings.")
    if st.button("Investigate", type="primary"):
        if not url.strip():
            st.warning("Paste an article URL first.")
            return
        with st.status("Investigation running…", expanded=True) as status:
            def on_step(node: str, delta: dict) -> None:
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
    st.markdown(md_link(inv["url"], inv["url"]))
    show_report(inv)
    with st.expander("Step log"):
        for s in inv.get("steps", []):
            st.markdown(f"- `{s['at']:%H:%M:%S}` **{s['node']}** {'⚠ ' + '; '.join(s['errors']) if s['errors'] else ''}")


def page_claims() -> None:
    st.title("🧩 Claims")
    st.caption("Every claim extracted so far, across all investigations, with its evidence trail.")
    statuses = st.multiselect("Status", list(STATUS_COLOR), default=list(STATUS_COLOR))
    query = st.text_input("Filter by text")
    shown_max = 300  # one expander per claim: keep the page responsive
    claims = list(get_db().claims.find({"status": {"$in": statuses}}, {"embedding": 0}).sort("created_at", -1))
    if query:
        claims = [c for c in claims if query.lower() in c["text"].lower()]
    st.caption(f"{len(claims)} claims" + (f" (showing the newest {shown_max})" if len(claims) > shown_max else ""))
    for c in claims[:shown_max]:
        with st.expander(f"{c.get('status', 'unverified').upper()} · {c['text'][:110]}"):
            st.write(c["text"])
            urls = c.get("article_urls", [])
            st.caption(f"type: {c.get('type', '?')} · subject: {c.get('subject', '?')} · seen in {len(urls)} article(s)")
            for e in c.get("evidence", []):
                st.markdown(f"- `{e['verdict']}` {md_link(e['source'][:70], e['source'])}: {e['note']}")
            if c.get("variants"):
                st.caption("Also worded as: " + " | ".join(c["variants"]))
            for u in urls:
                st.markdown(f"↳ {md_link(u[:80], u)}")


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
        net.add_node(f"c{c['_id']}", label=escape(c["text"][:40]) + "…", title=escape(c["text"]), color=STATUS_COLOR.get(c.get("status"), "#9aa0a6"), shape="dot", size=14)
        n_nodes += 1
        for u in c.get("article_urls", []):
            if u not in net.get_nodes():
                net.add_node(u, label=escape(urlparse(u).netloc or u[:30]), title=escape(u), color="#c77dff", shape="square", size=10)
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


# ---------- timeline ----------

def page_timeline() -> None:
    st.title("⏳ Timeline")
    st.caption("Claims in chronological order, each linked to the article that made it. Every timeline is a single MongoDB aggregation pipeline.")
    mode = st.radio("Build the timeline", ["By entity", "By topic (semantic search)"], horizontal=True)
    if mode == "By entity":
        entities = timeline.entities_with_claims()
        if not entities:
            st.info("No entities yet: run an investigation first.")
            return
        chosen = st.selectbox("Entity", entities, format_func=lambda e: f"{e['name']}  ({e['type']}, {e['mentions']} claim(s))")
        pipeline = timeline.entity_pipeline(chosen)
    else:
        topic = st.text_input("Topic", placeholder="e.g. central bank raises borrowing costs")
        if not topic.strip():
            st.info("Describe a topic in your own words. Claims are matched by meaning, not by keywords.")
            return
        try:
            pipeline = timeline.topic_pipeline(topic.strip())
        except Exception as e:
            st.error(f"Semantic search is unavailable right now ({type(e).__name__}). Try again in a minute.")
            return
    try:
        events = timeline.run(pipeline)
    except Exception as e:
        st.error(f"The MongoDB query failed ({type(e).__name__}). Is the Atlas Vector Search index ready? Run: uv run python -m investigator.setup")
        return
    if not events:
        st.warning("No claims found for this selection.")
    by_date: dict[str, list[dict]] = {}
    for ev in events:
        by_date.setdefault(ev["date"], []).append(ev)
    for date, group in by_date.items():
        with st.container(border=True):
            estimate = "  ·  *no publication date found: fetch date shown*" if group[0]["date_is_estimate"] else ""
            st.markdown(f"#### 📅 {date}{estimate}")
            for ev in group:
                a = ev["article"]
                score = f" · match {ev['score']:.2f}" if "score" in ev else ""
                st.markdown(f"{ev['text']}")
                badge = STATUS_BADGE.get(ev["status"], "gray")
                st.caption(f":{badge}-badge[{ev['status']}]{score} · {md_link(a['title'] or a['source'] or a['url'], a['url'])} · {a['source']}")
    with st.expander("Show the MongoDB pipeline behind this page"):
        st.code(timeline.describe(pipeline), language="json")


# ---------- navigation ----------
PAGES = {"🕵️ Investigate": page_investigate, "📜 History": page_history, "🧩 Claims": page_claims,
         "⏳ Timeline": page_timeline, "🕸️ Graph": page_graph}
# ?page=history (or investigate / claims / graph) opens a page directly, so pages can be linked
_wanted = next((i for i, name in enumerate(PAGES) if st.query_params.get("page", "") in name.lower()), 0) if st.query_params.get("page") else 0
choice = st.sidebar.radio("Navigate", list(PAGES), index=_wanted, label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption("Multi-agent news investigator · LangGraph + MongoDB Atlas + Voyage AI")
PAGES[choice]()
