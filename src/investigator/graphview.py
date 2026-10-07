"""The knowledge-graph page (pyvis), built from claims and entities.

Claim and article text comes from the web and from LLMs, so it is untrusted. The graph is embedded in a
page that runs scripts, and the library writes node data into a <script> block: text containing
"</script>" could close that block early and inject markup. Without "<" and ">" no tag can form, so
`no_markup` swaps them for look-alike characters. (Labels are drawn on a canvas as plain text, so
HTML-escaping them would only show up as ugly "&#x27;" on screen.)
"""
from urllib.parse import urlparse

from pyvis.network import Network

from investigator.extraction import normalize

STATUS_COLOR = {"corroborated": "#2e9e5b", "disputed": "#e0a030", "contradicted": "#d64545", "unverified": "#9aa0a6"}
MAX_NODES = 50


def no_markup(text: str) -> str:
    return str(text).replace("<", "‹").replace(">", "›")


def build_graph_html(claims: list[dict], entities: list[dict]) -> str:
    net = Network(height="620px", width="100%", bgcolor="#0e1117", font_color="#fafafa", cdn_resources="in_line")
    present: set[str] = set()

    def add(node_id: str, **kw) -> None:
        net.add_node(node_id, **kw)
        present.add(node_id)

    for c in claims:
        cid = f"c{c['_id']}"
        add(cid, label=no_markup(c["text"][:40]) + "…", title=no_markup(c["text"]),
            color=STATUS_COLOR.get(c.get("status"), "#9aa0a6"), shape="dot", size=14)
        for u in c.get("article_urls", []):
            if u not in present:
                add(u, label=no_markup(urlparse(u).netloc or u[:30]), title=no_markup(u), color="#c77dff", shape="square", size=10)
            net.add_edge(cid, u)
        for e in entities:
            eid = f"e{e['_id']}"
            if len(e["name"]) > 3 and normalize(e["name"]) in normalize(c["text"]):
                if eid not in present and len(present) < MAX_NODES:
                    add(eid, label=no_markup(e["name"]), title=no_markup(e.get("type", "")), color="#4c9be8", size=18)
                if eid in present:
                    net.add_edge(eid, cid)
    return net.generate_html()
