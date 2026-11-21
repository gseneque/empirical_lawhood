# SPDX-License-Identifier: MPL-2.0
"""Versioned, finite presentation data derived by an installed scientific reader."""

from empirical_lawhood.api.application_contracts import ApplicationError, exact_mapping, identifier


EXPLORATION_SCHEMA = "empirical-lawhood/application/exploration"
EXPLORATION_VERSION = "1.0.0"
MAX_VISIBLE_NODES = 16
MAX_VISIBLE_EDGES = 32
MAX_EXPANSION_DEPTH = 8
QUESTION_IDS = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6")
RELATIONSHIPS = frozenset(("REQUIRES", "CANDIDATE_SUPPLY", "ASSESSED_SUPPLY", "ADMITTED_SUPPLY",
    "LINEAGE", "SUCCESSOR", "INFORMING_REFERENCE", "CLASSIFICATION"))


def validate_exploration(value):
    """Validate a display contract, never calculate or admit its scientific values."""
    names = ("schema", "version", "question", "root_id", "nodes", "edges", "summary", "findings",
        "question_readouts", "work_coverage", "methods", "layout", "coverage", "pending_bindings")
    exact_mapping(value, names, required=names)
    if value["schema"] != EXPLORATION_SCHEMA or value["version"] != EXPLORATION_VERSION:
        raise ApplicationError("UNSUPPORTED_EXPLORATION_REVISION", "Use the generic original-record view for this presentation revision.")
    if type(value["question"]) is not str or not 1 <= len(value["question"]) <= 4096:
        raise ValueError("exploration requires its bounded original question")
    ids = set()
    nodes = value["nodes"]
    if type(nodes) not in (list, tuple) or not 1 <= len(nodes) <= 4096:
        raise ValueError("exploration requires its complete bounded node census")
    for node in nodes:
        fields = ("id", "label", "role", "state", "source", "record", "children", "method_ids", "group")
        exact_mapping(node, fields, required=fields)
        identifier(node["id"], "node.id")
        if node["id"] in ids:
            raise ValueError("exploration repeats an original node identity")
        ids.add(node["id"])
        if (type(node["label"]) is not str or not 1 <= len(node["label"]) <= 4096
                or type(node["state"]) is not dict or type(node["record"]) is not dict):
            raise ValueError("exploration node loses its text, scoped state or original record")
        from empirical_lawhood.science.records.decoding import decode_canonical_record
        from empirical_lawhood.science.identity.provenance import ObjectIdentity
        decode_canonical_record(node["source"], ObjectIdentity)
        for name in ("children", "method_ids"):
            if type(node[name]) not in (list, tuple) or len(node[name]) > 4096:
                raise ValueError("exploration node references exceed their finite bound")
            for selected in node[name]:
                identifier(selected, name)
    if value["root_id"] not in ids or any(not set(node["children"]) <= ids for node in nodes):
        raise ValueError("exploration loses its root or a child record")
    edges = value["edges"]
    if type(edges) not in (list, tuple) or len(edges) > 8192:
        raise ValueError("exploration exceeds its complete edge bound")
    edge_ids = set()
    for edge in edges:
        names = ("id", "from", "to", "kind", "label", "scope", "source")
        exact_mapping(edge, names, required=names)
        identifier(edge["id"], "edge.id")
        if edge["id"] in edge_ids or edge["from"] not in ids or edge["to"] not in ids or edge["kind"] not in RELATIONSHIPS:
            raise ValueError("exploration changes a relationship identity, endpoint or kind")
        edge_ids.add(edge["id"])
        decode_canonical_record(edge["source"], ObjectIdentity)
        if any(type(edge[name]) is not str or len(edge[name]) > 4096 for name in ("label", "scope")):
            raise ValueError("exploration relationship text is not bounded")
    questions = value["question_readouts"]
    if type(questions) not in (list, tuple) or len(questions) not in (0, 6):
        raise ValueError("a selected M50 presentation retains all six questions")
    if questions and tuple(row.get("question_id") for row in questions) != QUESTION_IDS:
        raise ValueError("the original six-question census or order changed")
    for row in questions:
        names = ("question_id", "label", "acquisition_state", "authentication_state", "assessment_state",
            "disposition", "quantity", "uncertainty", "denominator", "evidence", "consequence")
        exact_mapping(row, names, required=names)
        if type(row["denominator"]) is not dict or type(row["evidence"]) not in (list, tuple):
            raise ValueError("question readouts require original dependence and evidence")
    for name in ("summary", "work_coverage", "layout", "coverage"):
        if type(value[name]) is not dict:
            raise ValueError("exploration retains named scope and coverage fields")
    if value["coverage"].get("total_nodes") != len(nodes) or value["coverage"].get("total_edges") != len(edges):
        raise ValueError("exploration coverage must retain its complete known census")
    if type(value["findings"]) not in (list, tuple) or type(value["methods"]) not in (list, tuple):
        raise ValueError("exploration requires explicit findings and method references")
    return value
