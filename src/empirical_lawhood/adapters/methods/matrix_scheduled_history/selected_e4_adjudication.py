# SPDX-License-Identifier: MPL-2.0
"""Issued E4 adjudication projects retained products without inventing warrant."""
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationContext, ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind
from empirical_lawhood.runtime.execution import TaskContext
from empirical_lawhood.runtime.plans import BarrierKind, ScientificStage, ExecutionTask
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract


def require_adjudication_context(context, manifest):
    """Require genuine current numerical reveal before any protected input read."""
    if type(context) is not TaskContext:
        raise TypeError("selected E4 adjudication needs the actual current task context")
    context.__post_init__()
    prepared, authority = context.prepared_invocation, context.scientific_adjudication_context
    if (type(prepared) is not PreparedInvocationContract or type(prepared.execution_task_record) is not ExecutionTask
            or prepared.manifest != manifest or prepared.native_effect
            or manifest.kind is not CapabilityKind.EVALUATOR or context.permissions != manifest.permissions
            or not manifest.resource_ceiling.contains(context.resource_budget)
            or context.outcome_access is not OutcomeAccess.EVALUATOR_REVEAL
            or prepared.execution_task_record.stage is not ScientificStage.EVALUATE
            or prepared.execution_task_record.barrier is not BarrierKind.REVEAL
            or type(authority) is not ScientificAdjudicationContext
            or authority.execution_plan != prepared.execution_plan
            or authority.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
            or authority.plumbing_only or authority.fixture_scope_id is not None
            or authority.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
            or authority.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE):
        raise ValueError("selected E4 adjudication lacks its exact issued numerical reveal context")
    prepared.require_complete();prepared.validate_context(context);authority.__post_init__()
    outputs = prepared.execution_task_record.outputs
    if (len(outputs) != 1 or len(context.output_ports) != 1
            or context.output_ports[0].output_id != context.task_id + ".adjudication"
            or context.output_ports[0].logical_artifact_id is None
            or (context.output_ports[0].payload_schema, context.output_ports[0].profile, context.output_ports[0].media_type) !=
                (ScientificAdjudicationRecord.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")
            or outputs[0].outcome_access is not authority.outcome_access
            or outputs[0].visibility_ceiling is not authority.visibility_ceiling):
        raise ValueError("selected E4 adjudication changes its exact compiled revealed output")
    return authority


def adjudication_record(context, manifest, reasons):
    authority = require_adjudication_context(context, manifest)
    return ScientificAdjudicationRecord("adjudication." + context.run_id + "." + context.task_id,
        context.run_id, context.task_id, authority.execution_plan, context.input_materialization_ids,
        tuple(sorted(port.logical_artifact_id for port in context.output_ports)), context.dependency_receipt_ids,
        authority.evidence_world_id, authority.evidence_world_kind, authority.relation, authority.independent_unit_id,
        authority.information_cutoffs, authority.visibility_ceiling, authority.outcome_access,
        AdjudicationEvaluability.UNEVALUABLE, ScientificStatus.UNEVALUABLE, AdmissionStatus.UNEVALUABLE,
        tuple(sorted(reasons)))
