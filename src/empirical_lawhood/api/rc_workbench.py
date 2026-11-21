# SPDX-License-Identifier: MPL-2.0
"""Selected bounded RC presentation through the original authenticated readers."""

from empirical_lawhood.api.application_projections import finding_projection, projection


MAX_RC_INSPECTION_OPERATIONS = 16
MAX_RC_INSPECTION_DRAFT_BYTES = 4 * 1024**2


def is_bounded_rc_draft(draft):
    from empirical_lawhood.design.recursive_authoring import RecursiveStudyDraft
    from empirical_lawhood.domains.circuits.rc_prerequisite_chain.operation_bindings import NAMESPACE, PHASES
    keys = {f"{NAMESPACE}.{row[0]}" for row in PHASES}
    return (type(draft) is RecursiveStudyDraft and 0 < len(draft.operations) <= MAX_RC_INSPECTION_OPERATIONS
        and draft.development_study is not None and draft.prospective_draft is None
        and all(row.selection.capability_key in keys and row.selection.capability_version == "1.0.0"
                for row in draft.operations))


def load_bounded_rc(*, directory, plane):
    from empirical_lawhood.api.application_development import load_bounded_development
    return load_bounded_development(directory=directory, plane=plane,
        maximum_draft_bytes=MAX_RC_INSPECTION_DRAFT_BYTES, accept_draft=is_bounded_rc_draft,
        refusal_code="UNSUPPORTED_BOUNDED_RC_SELECTION")


def inspect_rc(*, directory, plane, request, parameters, findings=False):
    from empirical_lawhood.api.recursive_authoring import explain_recursive_draft
    from empirical_lawhood.api.recursive_execution import read_recursive_wave
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    with plane.read_context() as reader:
        packet, draft, source, _payloads = load_bounded_rc(directory=directory, plane=reader)
        identity = ObjectIdentity.from_record(packet.packet_id, packet).to_document()
        if findings:
            report = read_recursive_wave(directory=directory, artifact_writer=reader, terminal_product_format="documents")
            result = finding_projection(report, request=request, parameters=parameters, identity=identity)
        else:
            from empirical_lawhood.api.recursive_execution import _retained_plans
            _run, plan, _index = _retained_plans(_payloads, draft)
            explanation = explain_recursive_draft(draft)
            result = projection(request=request, kind="design", title=explanation["question"], identity=identity,
                scope="AUTHENTICATED_RC_DESIGN", parameters=parameters, records=explanation["requirements"],
                summary={key: explanation[key] for key in ("draft_id", "draft_sha256", "authored_operation_count",
                    "selected_operation_count", "requirement_count", "connection_count", "scientific_root", "qualification")},
                design={key: explanation[key] for key in ("selected_operations", "connections", "suppliers",
                    "unresolved_selected_premises", "unresolved_decisions", "declared_claims")},
                execution_graph={"identity": ObjectIdentity.from_record(plan.execution_plan_id, plan).to_document(),
                    "nodes": tuple({"task_id": task.task_id, "stage": task.stage.value,
                        "capability_key": task.capability.capability_key,
                        "dependency_task_ids": task.dependency_task_ids,
                        "scientific_inputs": tuple(edge.to_document() for edge in task.scientific_inputs)}
                        for task in plan.tasks),
                    "scope": "ORIGINAL_AUTHENTICATED_EXECUTION_PLAN"},
                provenance={"packet": identity, "implementation": packet.implementation.to_document(),
                    "observed_producing_git_head": source.observed_git_head, "dependency_lock_sha256": source.dependency_lock_sha256})
        reader.require_verification_snapshot()
    return result
