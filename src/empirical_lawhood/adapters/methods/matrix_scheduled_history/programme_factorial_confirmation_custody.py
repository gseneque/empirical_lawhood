# SPDX-License-Identifier: MPL-2.0
"""Pure original freeze/acquisition joins; actual custody is authenticated by API.

No publication locator, role label or successful preparation receipt supplies
scientific qualification. In particular, identical criteria bytes produced
after acquisition cannot replace the original producing receipt in the issued
acquisition design. Runtime-only views bind one exact current invocation; they
are supplied only by the installed parent preparation path.
"""

from dataclasses import dataclass

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.planning.study_authoring import DesignInputRole, StudyDraft
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import BarrierKind, ExecutionPlan, ScientificStage


def validate_criteria_binding(binding):
    from empirical_lawhood.kernel.serialization import validate_stable_id
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
    from .programme_factorial_confirmation import (
        ScheduledFactorialCriteriaBinding, ScheduledFactorialFrozenCriteria, freeze_node_id, operation_declarations,
    )
    from .programme_parent import _published
    if (type(binding) is not ScheduledFactorialCriteriaBinding or type(binding.record) is not ScheduledFactorialFrozenCriteria
            or type(binding.receipt) is not CanonicalTaskReceipt or type(binding.execution_plan) is not ExecutionPlan
            or type(binding.prior_execution) is not RecursivePriorExecutionBinding):
        raise ValueError("criteria freeze binding requires its exact original ordinary issued product/receipt/plan locators")
    validate_stable_id(binding.binding_id)
    binding.record.__post_init__()
    config = binding.record.configuration
    for record, publication in ((binding.record, binding.publication), (binding.receipt, binding.receipt_publication),
            (binding.execution_plan, binding.execution_plan_publication), (config, binding.configuration_publication)):
        _published(record, publication)
    node = freeze_node_id(config.specification)
    tasks = tuple(value for value in binding.execution_plan.tasks if value.task_id == node)
    declaration = operation_declarations()[0]
    manifest = declaration.manifest()
    if (len(tasks) != 1 or binding.receipt.task_id != node or binding.receipt.operational_status is not OperationalStatus.SUCCEEDED
            or binding.receipt.implementation_commit != binding.execution_plan.implementation_commit
            or binding.receipt.output_logical_artifacts != (binding.publication.logical,)
            or binding.receipt.output_materializations != (binding.publication.materialization,)
            or binding.configuration_publication.materialization.materialization_id not in binding.receipt.input_materialization_ids
            or not any(value.check_id == "original-full64-factorial-criteria-freeze" and value.passed for value in binding.receipt.checks)):
        raise ValueError("criteria freeze binding substitutes original successful ordinary producer or actual output custody")
    task = tasks[0]
    if (task.stage is not ScientificStage.FREEZE or task.barrier is not BarrierKind.FREEZE
            or task.capability.capability_key != manifest.capability_key or task.capability.capability_version != manifest.capability_version
            or task.capability_implementation_sha256 != manifest.implementation_sha256
            or task.capability.config.config_id != config.config_id or task.capability.config.config_schema != config.SCHEMA
            or task.capability.config.config_schema_sha256 != manifest.config_schema_sha256
            or task.capability.config.content_sha256 != config.fingerprint()
            or task.capability.config.artifact_id != binding.configuration_publication.logical.logical_artifact_id
            or len(task.outputs) != 1):
        raise ValueError("criteria freeze binding substitutes the exact original registered method/configuration")
    external = tuple(value for value in task.external_inputs
        if value.logical_artifact_id == binding.configuration_publication.logical.logical_artifact_id)
    if (len(external) != 1 or external[0].expected_payload_schema != config.SCHEMA
            or external[0].expected_content_sha256 != config.fingerprint()
            or any(expected is not None and actual != expected for actual, expected in (
                (binding.configuration_publication.materialization.size_bytes, external[0].expected_size_bytes),
                ("application/json", external[0].expected_media_type),
                (OutcomeAccess.OUTCOME_BLIND, external[0].expected_outcome_access),
                (VisibilityCeiling.PROSPECTIVE, external[0].expected_visibility_ceiling)))):
        raise ValueError("criteria freeze binding changes its exact actual blind configuration input")
    output, logical, physical = task.outputs[0], binding.publication.logical, binding.publication.materialization
    if (output.output_id != node+".product" or output.logical_artifact_id != logical.logical_artifact_id
            or output.relative_path != physical.relative_path or output.payload_schema != logical.payload_schema
            or output.profile is not logical.profile or output.media_type != logical.media_type
            or output.outcome_access is not logical.outcome_access or output.visibility_ceiling is not logical.visibility_ceiling):
        raise ValueError("criteria freeze binding changes its original ordinary output contract")
    prior = binding.prior_execution
    prior.__post_init__()
    if (prior.execution_plan != ObjectIdentity.from_record(binding.execution_plan.execution_plan_id, binding.execution_plan)
            or prior.run_id != binding.receipt.run_id or prior.task_id != node
            or prior.receipt != ObjectIdentity.from_record(binding.receipt.receipt_id, binding.receipt)
            or prior.logical_artifact_id != binding.publication.logical.logical_artifact_id or prior.record != binding.record.identity
            or prior.record_id_field != "record_id" or prior.additional_output_schema_ids or prior.scope_output_schema_ids or prior.native_subwork):
        raise ValueError("criteria freeze binding substitutes its exact genuine issued execution locator")


def require_original_criteria_design(root, binding):
    """Require both criteria and producing receipt in the original issued design.

    This function is a pure association check. Its API caller authenticates the
    original issued source closure and qualifications before invoking it.
    """
    from .programme_factorial_confirmation import ScheduledFactorialCriteriaBinding
    if type(root) is not StudyDraft or type(binding) is not ScheduledFactorialCriteriaBinding:
        raise PermissionError("factorial chronology requires the actual original issued scientific root and freeze binding")
    binding.__post_init__()
    required = (binding.record.identity, ObjectIdentity.from_record(binding.receipt.receipt_id, binding.receipt), binding.identity)
    for identity in required:
        rows = tuple(value for value in root.design_inputs if value.object_identity == identity)
        if (len(rows) != 1 or rows[0].materialization_sha256 != identity.object_fingerprint
                or rows[0].role is not DesignInputRole.READINESS_METADATA
                or rows[0].outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or rows[0].visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                or rows[0].physical_unit_ids or rows[0].seed_ids):
            raise PermissionError("factorial criteria/ordinary producing receipt were not frozen in the original issued acquisition design")


@dataclass(frozen=True, slots=True)
class VerifiedFactorialInvocation:
    """Identity-bound parent replay result, never a canonical authority record."""
    configuration: ObjectIdentity
    programme: ObjectIdentity
    bank: ObjectIdentity
    package: ObjectIdentity
    execution_plan: ObjectIdentity
    execution_task: ObjectIdentity
    execution_authority: ObjectIdentity
    reveal_authority: ObjectIdentity | None
    input_materialization_ids: tuple[str, ...]
    dependency_receipt_ids: tuple[str, ...]
    qualified_parent: ObjectIdentity
    criteria_binding: ObjectIdentity | None
    cases: tuple
    waves: tuple
    reduction: ObjectIdentity | None
    data: ObjectIdentity | None
    input_seal: ObjectIdentity | None = None

    def validate_invocation(self, context):
        from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
        contract = context.prepared_invocation
        if (type(contract) is not PreparedInvocationContract or contract.execution_task != self.execution_task
                or contract.execution_plan != self.execution_plan):
            raise PermissionError("factorial prepared invocation lacks its original complete worker task/plan contract")
        contract.validate_context(context)
        if (self.configuration.object_id != context.config.config_id or self.configuration.object_schema != context.config.config_schema
                or self.configuration.object_fingerprint != context.config.content_sha256 or self.execution_task.object_id != context.task_id
                or self.input_materialization_ids != context.input_materialization_ids
                or self.dependency_receipt_ids != context.dependency_receipt_ids
                or self.execution_authority.object_schema != "empirical-lawhood/planning/study-operation-authority"):
            raise PermissionError("factorial prepared invocation substitutes actual current task/configuration/input custody")

    def validate_context(self, config, context):
        from .programme_factorial_confirmation import (
            ScheduledFactorialConfirmationConfig, ScheduledFactorialConfirmationSealConfig, confirmation_input_seal,
        )
        self.validate_invocation(context)
        if self.configuration != config.identity or self.programme != config.programme.identity or self.bank != config.bank:
            raise PermissionError("factorial prepared invocation substitutes original programme or scientific configuration")
        if type(config) is ScheduledFactorialConfirmationSealConfig and (self.criteria_binding != config.criteria.identity
                or self.reveal_authority is not None or self.cases or self.waves or self.reduction is not None or self.data is not None
                or self.input_seal is not None):
            raise PermissionError("factorial input seal preparation changes its original criteria or blind metadata boundary")
        if type(config) is ScheduledFactorialConfirmationConfig and (self.reveal_authority is None
                or self.criteria_binding != config.criteria.identity or self.reduction != config.reduction or self.data != config.data
                or self.input_seal != confirmation_input_seal(config).identity
                or tuple(value.root_id for value in self.cases) != tuple(value.root_id for value in config.programme.cases)
                or tuple(value.wave_id for value in self.waves) != tuple(value.wave_id for value in config.programme.waves)):
            raise PermissionError("factorial prepared invocation lacks current reveal, original criteria or full576-case custody")
