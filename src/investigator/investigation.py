"""Run the graph for one URL and persist the investigation (live progress included)."""
from datetime import datetime, timezone
from typing import Callable

from investigator.db import get_db
from investigator.graph import build_graph


def run_investigation(url: str, on_step: Callable[[str, dict], None] | None = None) -> dict:
    """Stream the graph node by node, saving each step so a crash still leaves a partial record."""
    coll = get_db().investigations
    doc_id = coll.insert_one(
        {"url": url, "status": "running", "steps": [], "created_at": datetime.now(timezone.utc)}
    ).inserted_id

    state: dict = {"url": url, "errors": []}
    try:
        for update in build_graph().stream(state, stream_mode="updates"):
            for node, delta in update.items():
                state.update({k: v for k, v in delta.items() if k != "errors"})
                state["errors"] = state.get("errors", []) + delta.get("errors", [])
                coll.update_one(
                    {"_id": doc_id},
                    {"$push": {"steps": {"node": node, "at": datetime.now(timezone.utc), "errors": delta.get("errors", [])}}},
                )
                if on_step:
                    on_step(node, delta)
    except Exception as e:
        coll.update_one({"_id": doc_id}, {"$set": {"status": "failed", "error": f"{type(e).__name__}: {e}"}})
        raise

    coll.update_one(
        {"_id": doc_id},
        {"$set": {
            "status": "done", "report": state.get("report"), "claims": state.get("claims", []),
            "verdicts": state.get("verdicts", []), "sources": state.get("sources", []),
            "errors": state["errors"], "finished_at": datetime.now(timezone.utc),
        }},
    )
    return {"id": str(doc_id), **state}
