# SPDX-License-Identifier: MPL-2.0
"""Bounded collection relationships; editorial classifications never assert supply."""

from empirical_lawhood.storage.operational_observation import read_selected_pin
from empirical_lawhood.api.application_projections import projection


def collection_neighbourhood(document, *, request, values):
    rows = [{name: entry["value"][name] for name in ("selection_id", "investigation_id", "context_id", "label",
        "question", "identity", "classification", "links")} for entry in document["entries"]]
    result = projection(request=request, kind="collection-neighbourhood", title="Selected knowledge relationships",
        identity=None, scope="EXPLICIT_COLLECTION_WITH_SOURCE_PINNED_EDITORIAL_RELATIONSHIPS", records=rows, parameters=values,
        summary={"collection_count": len(rows), "scientific_reads": 0, "native_calls": 0,
            "consumer_admission": "REQUIRES_CURRENT_ORIGINAL_DESTINATION_ASSESSMENT",
            "knowledge_import_coverage": "NOT_SELECTED; USE_EXPLICIT_KNOWLEDGE_QUERY",
            "unseen_updates": "UNKNOWN"})
    sources = {}
    def source_status(pin):
        key = pin["path"], pin["sha256"]
        if key not in sources:
            if len(sources) >= 16:
                return "SOURCE_WINDOW_LIMIT"
            try:
                read_selected_pin(pin, maximum_bytes=128 * 1024)
            except (ValueError, OSError, RuntimeError):
                sources[key] = "SOURCE_UNAVAILABLE_OR_CHANGED"
            else:
                sources[key] = "PIN_VERIFIED"
        return sources[key]
    selected_ids = {row["selection_id"] for row in rows}
    edges = []
    for row in result["page"]["rows"]:
        row["classification_status"] = source_status(row["classification"]["source"])
        for link in row["links"]:
            target = document["aliases"].get(link["target"], link["target"])
            edges.append({"from": row["selection_id"], "to": target, "kind": link["kind"], "label": link["label"],
                "source": link["source"], "source_status": source_status(link["source"]),
                "target_coverage": "REGISTERED" if target in selected_ids else "OUTSIDE_SELECTED_COLLECTION",
                "scope": "EDITORIAL_CONTEXT; NO_ASSESSED_SCIENTIFIC_SUPPLY"})
    result["relationships"] = edges
    result["relationship_coverage"] = "OUTGOING_EDITORIAL_LINKS_OF_THIS_EXPLICIT_PAGE"
    result["scientific_relationships"] = {"status": "EXPLICIT_ORIGINAL_READ_REQUIRED", "edges": [],
        "procedure": "Open an original investigation or contribution. Use knowledge.query and knowledge.resolve for selected imports."}
    result["layout_bounds"] = {"visible_nodes": 16, "visible_edges": 32, "expansion_depth": 8}
    # Source pins remain current through the selected finite read, including a
    # repeated file used by several classifications. Nothing scans result stores.
    for (path, digest), status in sources.items():
        if status == "PIN_VERIFIED":
            read_selected_pin({"path": path, "sha256": digest}, maximum_bytes=128 * 1024)
    return result
