# SPDX-License-Identifier: MPL-2.0
"""Public locators and exact original revision-CAL producer associations.

These records contain no calibration scores and grant no access. The API must
authenticate original issue/reveal, configuration, receipts and native inputs.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_sampling_bindings import MatrixSamplingOriginalProduct
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import BarrierKind, ExecutionPlan, ScientificStage

from .programme_calibration import _publication_pin
from .revision_calibration import ScheduledRevisionCalibration
from .revision_calibration_bindings import CHECK, ScheduledRevisionCalibrationConfig, calibration_task_id, operation_declarations, pin
from .revision_public import ScheduledRevisionPublicCalibration


@dataclass(frozen=True, slots=True)
class ScheduledRevisionCalibrationCustody(CanonicalRecord):
    """Public projection plus actual original sealed producer custody only."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-calibration-custody"
    record_id: str
    calibration: ScheduledRevisionPublicCalibration
    original: MatrixSamplingOriginalProduct
    configuration: ScheduledRevisionCalibrationConfig
    publication: ArtifactWriteResult
    receipt: CanonicalTaskReceipt
    receipt_publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.calibration) is not ScheduledRevisionPublicCalibration or type(self.original) is not MatrixSamplingOriginalProduct
                or type(self.configuration) is not ScheduledRevisionCalibrationConfig or type(self.receipt) is not CanonicalTaskReceipt):
            raise TypeError("revision calibration custody requires its exact public projection and original producer")
        for record in (self.calibration, self.original, self.configuration, self.receipt):
            record.__post_init__()
        original, config, receipt = self.original.prior_execution, self.configuration, self.receipt
        if (original.record != self.calibration.original or original.record_id_field != "record_id"
                or original.record.object_id != config.calibration_id or original.task_id != calibration_task_id(config.scope)
                or original.receipt != pin(receipt, "receipt_id") or original.run_id != receipt.run_id
                or original.task_id != receipt.task_id or original.logical_artifact_id != self.publication.logical.logical_artifact_id
                or original.additional_output_schema_ids or original.scope_output_schema_ids or original.native_subwork
                or receipt.operational_status is not OperationalStatus.SUCCEEDED
                or receipt.output_logical_artifacts != (self.publication.logical,)
                or receipt.output_materializations != (self.publication.materialization,)
                or not any(value.check_id == CHECK and value.passed for value in receipt.checks)
                or self.calibration.group_ids != config.unit_ids):
            raise ValueError("revision calibration custody substitutes its exact original successful producer or complete groups")
        _publication_pin(self.calibration.original, self.publication)
        _publication_pin(pin(receipt, "receipt_id"), self.receipt_publication, size=len(receipt.canonical_bytes()))
        if (self.publication.logical.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                or self.publication.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
            raise ValueError("revision calibration custody cannot relabel original sealed scores as blind metadata")

    @property
    def identity(self):
        return pin(self)


def validate_calibration_producer(*, config, binding, package, execution_plan, receipt, logical):
    """Pure original producer check after genuine grant/receipt authentication."""
    if type(config) is not ScheduledRevisionCalibrationConfig or type(execution_plan) is not ExecutionPlan:
        raise PermissionError("revision calibration requires its actual original issued producer configuration and plan")
    config.__post_init__()
    declaration, = operation_declarations()
    manifest = declaration.manifest()
    root = package.issued_study.candidate.authoring_package.base.draft
    task_id = calibration_task_id(config.scope)
    if (type(root) is not StudyDraft or root.development_unit_ids or root.evaluation_unit_ids != config.unit_ids
            or root.system is None or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or any(getattr(value, "fixture_scope_id", None) is not None or getattr(value, "plumbing_only", False)
                for value in (package, execution_plan, root))
            or tuple(task.task_id for task in execution_plan.tasks) != (task_id,)):
        raise PermissionError("revision calibration substitutes an original scientific scope or source-free/software fixture")
    task, = execution_plan.tasks
    if (task.task_id != binding.task_id or binding.record.object_id != config.calibration_id
            or binding.record.object_schema != ScheduledRevisionCalibration.SCHEMA or binding.record_id_field != "record_id"
            or task.stage is not ScientificStage.TRANSFORM or task.barrier is not BarrierKind.NONE
            or task.capability.capability_key != manifest.capability_key or task.capability.capability_version != manifest.capability_version
            or task.capability_implementation_sha256 != manifest.implementation_sha256
            or task.capability.config.config_id != config.config_id or task.capability.config.config_schema != config.SCHEMA
            or task.capability.config.content_sha256 != config.fingerprint()
            or task.capability.config.config_schema_sha256 != manifest.config_schema_sha256
            or task.capability.requested_outcome_access is not OutcomeAccess.EVALUATION_SEALED
            or task.capability.required_permissions != manifest.permissions or task.dependency_task_ids
            or len(task.external_inputs) != 4 or len(task.scientific_inputs) != 3 or len(task.outputs) != 1
            or receipt.task_id != task_id or receipt.implementation_commit != execution_plan.implementation_commit
            or not any(value.check_id == CHECK and value.passed for value in receipt.checks)):
        raise PermissionError("revision calibration substitutes the original installed method, configuration, input census or producing source")
    expected = {(config.SCHEMA, config.fingerprint()), *((value.object_schema, value.object_fingerprint)
        for value in (config.scope, config.sources, config.bank))}
    actual = {(value.expected_payload_schema, value.expected_content_sha256) for value in task.external_inputs}
    if len(actual) != 4 or actual != expected:
        raise PermissionError("revision calibration producer substitutes its complete exact original operand bytes")
    output, = task.outputs
    if (receipt.output_logical_artifacts != (logical,) or output.output_id != task_id + ".product"
            or output.logical_artifact_id != logical.logical_artifact_id or output.payload_schema != logical.payload_schema
            or output.profile is not logical.profile or output.media_type != logical.media_type
            or output.outcome_access is not OutcomeAccess.EVALUATION_SEALED
            or logical.outcome_access is not output.outcome_access or logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or output.visibility_ceiling is not logical.visibility_ceiling
            or logical.content_sha256 != binding.record.object_fingerprint):
        raise PermissionError("revision calibration producer substitutes its actual original sealed output")
