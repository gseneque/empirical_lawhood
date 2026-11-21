# SPDX-License-Identifier: MPL-2.0
"""Original conditional-root findings through the bounded presentation extension."""

from empirical_lawhood.api.application_presentations import ApplicationPresentation, PresentationData


def _exploration(science, graph, result, report):
    from empirical_lawhood.api.application_exploration_contracts import EXPLORATION_SCHEMA, EXPLORATION_VERSION
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.api.domain_composition.rubisco_response.application_methods import method_for_requirement, method_descriptions

    requirements = {row.requirement_id: row for row in graph.requirements}
    root = requirements[graph.root_requirement_id]
    supplier_ids = {row.requirement_id for row in graph.suppliers}
    cases = {case.case_id: set(case.decision_requirement_ids) for case in result.cases}
    nodes, edges = [], []
    for requirement in graph.requirements:
        key = requirement.requirement_id
        source = ObjectIdentity.from_record(key, requirement).to_document()
        method, label = method_for_requirement(requirement, graph)
        role = ("root" if key == graph.root_requirement_id else "numerical" if key == graph.numerical_requirement_id
            else "supplier" if key in supplier_ids else "requirement")
        state = ({"physical": result.joint_outcome, "biological": science["biological_predictive_validity"]} if role == "root"
            else {"numerical": science["numerical_disposition"]} if role == "numerical"
            else {"selection": "UNSELECTED"} if role == "supplier" else {"evidence": "UNRESOLVED"})
        membership = [case for case, required in cases.items() if key in required]
        group = membership[0] if len(membership) == 1 else "shared" if membership else "supplier" if role == "supplier" else "root"
        nodes.append({"id": key, "label": label, "role": role, "state": state, "source": source,
            "record": requirement.to_document(), "children": list(requirement.further_requirement_ids),
            "method_ids": [method], "group": group})
        for child in requirement.further_requirement_ids:
            from hashlib import sha256
            edge_id = "requires." + sha256((key + "\0" + child).encode()).hexdigest()
            edges.append({"id": edge_id, "from": key, "to": child, "kind": "REQUIRES", "label": "requires",
                "scope": requirement.scope.coordinate_meaning, "source": source})
    summary = {"execution_status": report["status"], "assigned_tasks": report["task_count"],
        "scientific_completion": science["scientific_completion"], "numerical_disposition": science["numerical_disposition"],
        "joint_outcome": result.joint_outcome, "biological_predictive_validity": science["biological_predictive_validity"],
        "independent_biological_units": science["independent_biological_units"], "new_native_calls": science["new_native_calls"],
        "root_prerequisites": len(root.further_requirement_ids), "unresolved_physical_requirements": len(result.decision_requirement_ids),
        "requirement_count": len(graph.requirements), "supplier_count": len(graph.suppliers),
        "selected_suppliers": sum(item.selected for item in graph.suppliers),
        "numerical_requirement_id": graph.numerical_requirement_id, "qualification": "NOT_ESTABLISHED",
        "recorded_decision": "READ_EXPLICIT_COMPANION", "incurred_monetary_total": None,
        "conventional_baseline": "UNAVAILABLE", "demonstrated_net_saving": None,
        "current_activity": "NO_CURRENT_OBSERVATION"}
    physical = next((node["id"] for node in nodes if node["method_ids"] == ["rubisco.preparation"]
        and node["id"] in root.further_requirement_ids), None)
    retained = next((node["id"] for node in nodes if node["method_ids"] == ["rubisco.retained"] and node["role"] == "supplier"), None)
    case_layout = []
    for case in result.cases:
        selected = [node for node in nodes if node["group"] == case.case_id]
        def matching(*methods):
            return [node["id"] for method in methods for node in selected if method in node["method_ids"]]
        case_layout.append({"id": case.case_id, "label": case.processing_view,
            "requirement_ids": list(case.decision_requirement_ids),
            "groups": [
                {"label": "Turnover > 1", "formula": "1 / (w/qₐ + (1−w)/qᵣ)",
                    "requirement_ids": matching("rubisco.formation", "rubisco.processing")},
                {"label": "Specificity ≥ 1", "formula": "qᴅ × qχ",
                    "requirement_ids": matching("rubisco.oxygen", "rubisco.commitment")}],
            "joint_support_ids": matching("rubisco.support")})
    return {"schema": EXPLORATION_SCHEMA, "version": EXPLORATION_VERSION, "question": science["question"],
        "root_id": graph.root_requirement_id, "nodes": nodes, "edges": edges, "summary": summary,
        "findings": [case.to_document() for case in result.cases], "question_readouts": [],
        "work_coverage": {"assigned_tasks": report["task_count"], "new_native_calls": science["new_native_calls"],
            "independent_biological_units": science["independent_biological_units"],
            "case_count": len(result.cases), "nested_views": [case.processing_view for case in result.cases]},
        "methods": method_descriptions(),
        "layout": {"kind": "rubisco-joint-root", "retained": retained, "physical": physical,
            "numerical": graph.numerical_requirement_id,
            "cases": case_layout,
            "suppliers": [proposal.to_document() for proposal in graph.suppliers],
            "overview_scope": "Editorial requirement journey; positions do not imply execution order or assessed supply."},
        "coverage": {"total_nodes": len(nodes), "total_edges": len(edges), "complete_requirements": True,
            "requirement_count": len(graph.requirements), "connection_count": len(graph.connections)},
        "pending_bindings": [{"owner": "M50-03", "status": "NOT_SUPPLIED_BY_THIS_ORIGINAL", "reader": "safe-checkpoint-independent-read"},
            {"owner": "M50-04", "status": "NOT_SUPPLIED_BY_THIS_ORIGINAL", "reader": "six-question-response-assessment"}]}


def read(context, directory, artifact_writer):
    from empirical_lawhood.api.application_contracts import ApplicationError
    from empirical_lawhood.api.application_development import load_bounded_development
    from empirical_lawhood.api.recursive_execution import read_recursive_wave
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_experiment import InitialRootExperimentSpecification
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootResult, InitialRootScopedAssessment
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import ASSESS, CALCULATE, InitialRootRequirementGraph
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes, decode_canonical_record
    from empirical_lawhood.science.identity.provenance import ObjectIdentity

    if context.read_access_paths:
        raise ApplicationError("UNSUPPORTED_ACCESS_SELECTION", "The exposed conditional-root view does not accept protected access selections.")

    def selected(draft):
        return (len(draft.operations) == 2 and set(draft.selected_operation_ids) == {ASSESS, CALCULATE}
            and {(row.selection.capability_key, row.selection.capability_version) for row in draft.operations}
                == {(ASSESS, "1.0.0"), (CALCULATE, "1.0.0")})

    packet, _, source, payloads = load_bounded_development(directory=directory, plane=artifact_writer,
        maximum_draft_bytes=4 * 1024**2, accept_draft=selected)
    raw = payloads["experiment-specification.json"]
    specification = decode_canonical_bytes(raw, InitialRootExperimentSpecification, maximum_bytes=1024**2)
    report = read_recursive_wave(directory=directory, artifact_writer=artifact_writer,
        expected_specification_bytes=raw, terminal_product_format="documents")
    science = report["scientific_result"]
    if science.get("namespace") != "rubisco-initial-root" or science.get("scientific_completion") != "COMPLETED":
        raise ApplicationError("ROOT_READ_INCOMPLETE", "Use the execution view until the original complete root assessment is available.")
    graph = decode_canonical_record(science["requirement_graph"], InitialRootRequirementGraph)
    result = decode_canonical_record(science["result"], InitialRootResult)
    assessment = decode_canonical_record(science["assessment"], InitialRootScopedAssessment)
    if (graph.analysis != specification.analysis or graph.result != result.identity
            or assessment.analysis != specification.analysis or assessment.assessment.result != result.identity):
        raise PermissionError("conditional root presentation substitutes its original operands or assessment")
    identity = ObjectIdentity.from_record(packet.packet_id, packet).to_document()
    exploration = _exploration(science, graph, result, report)
    rows = tuple({"requirement_id": node["id"], "condition": node["label"], "role": node["role"],
        "scoped_state": node["state"], "record": node["record"]} for node in exploration["nodes"])
    return PresentationData(identity, science["evidence_scope"], exploration["summary"], rows, science,
        {"packet": identity, "implementation": packet.implementation.to_document(),
            "producing_git_head": source.observed_git_head, "dependency_lock_sha256": source.dependency_lock_sha256,
            "run_id": report["run_id"], "product_receipts": [row["producing_receipt"] for row in report["retained_product_index"]],
            "specification": specification.to_document(), "graph": graph.identity.to_document(),
            "result": result.identity.to_document(), "assessment": assessment.identity.to_document(),
            "scientific_connections": [item.to_document() for item in graph.connections]},
        "Numerical reconstruction, physical support and biological validity retain separate dispositions. Empty realizations supply no endpoint ratios.",
        exploration)


APPLICATION_PRESENTATION = ApplicationPresentation("rubisco.initial-root", "1.0.0", "Conditional paired Rubisco root",
    "rubisco-initial-root-experiment-v1", "programmes/biology/photosynthesis/workflows/rubisco-response/initial-root-v1.md",
    ("requirement_id", "condition", "role", "scoped_state"), 256, read)
