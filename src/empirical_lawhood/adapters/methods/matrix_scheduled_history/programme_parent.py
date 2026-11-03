# SPDX-License-Identifier: MPL-2.0
"""Actual global preparation receipt/plan binding, distinct from qualification."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import CandidateExecutionPlan, ExecutionPlan, ScientificStage, BarrierKind

from .commitment import authenticate_publication
from .programme_global import GLOBAL_CONFIG_ID, GLOBAL_TASK_ID, ScheduledProgrammeGlobalCommit, ScheduledProgrammeGlobalCommitConfig, operation_factories


def _published(record, publication):
    if (type(publication) is not ArtifactWriteResult or publication.logical.payload_schema != record.SCHEMA
            or publication.logical.content_sha256 != record.fingerprint()
            or publication.materialization.physical_sha256 != record.fingerprint()
            or publication.materialization.size_bytes != len(record.canonical_bytes())
            or publication.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or publication.logical.media_type != 'application/json'
            or publication.logical.logical_artifact_id != publication.materialization.logical_artifact_id
            or publication.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or publication.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
        raise ValueError('programme global parent changes actual original blind publication bytes/metadata')


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeGlobalParentBinding(CanonicalRecord):
    """A successful actual preparation product; this is not a qualified parent.

    A candidate execution plan is an explicit software/preparation route. It
    grants no prospective issue/execution/reveal authority. Current issued
    plans remain their distinct exact ExecutionPlan type and retain all their
    existing envelope/issued-extension bindings.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/global-parent-binding'
    binding_id: str
    parent: ScheduledProgrammeGlobalCommit
    publication: ArtifactWriteResult
    receipt: CanonicalTaskReceipt
    receipt_publication: ArtifactWriteResult
    execution_plan: ExecutionPlan | CandidateExecutionPlan
    execution_plan_publication: ArtifactWriteResult
    configuration: ScheduledProgrammeGlobalCommitConfig
    configuration_publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.binding_id)
        if (type(self.parent) is not ScheduledProgrammeGlobalCommit or type(self.receipt) is not CanonicalTaskReceipt
                or type(self.configuration) is not ScheduledProgrammeGlobalCommitConfig
                or type(self.execution_plan) not in (CandidateExecutionPlan, ExecutionPlan)
                or self.parent.configuration != ObjectIdentity.from_record(self.configuration.config_id, self.configuration)
                or self.parent.programme != self.configuration.programme.identity
                or self.parent.bank != self.configuration.bank
                or self.receipt.task_id != GLOBAL_TASK_ID or self.receipt.operational_status is not OperationalStatus.SUCCEEDED
                or self.receipt.implementation_commit != self.execution_plan.implementation_commit):
            raise ValueError('programme global parent changes actual product/configuration/successful receipt/plan')
        for record, publication in ((self.parent, self.publication), (self.receipt, self.receipt_publication),
                (self.execution_plan, self.execution_plan_publication), (self.configuration, self.configuration_publication)):
            _published(record, publication)
        tasks = tuple(task for task in self.execution_plan.tasks if task.task_id == GLOBAL_TASK_ID)
        factory, = operation_factories()
        if len(tasks) != 1:
            raise ValueError('programme parent omits its exact actual global producer task')
        task = tasks[0]
        if (task.stage is not ScientificStage.FREEZE or task.barrier is not BarrierKind.FREEZE
                or task.capability.capability_key != factory.manifest.capability_key
                or task.capability.capability_version != factory.manifest.capability_version
                or task.capability_implementation_sha256 != factory.manifest.implementation_sha256
                or task.capability.config.config_id != GLOBAL_CONFIG_ID
                or task.capability.config.config_schema != self.configuration.SCHEMA
                or task.capability.config.config_schema_sha256 != factory.manifest.config_schema_sha256
                or task.capability.config.content_sha256 != self.configuration.fingerprint()
                or task.capability.config.artifact_id != self.configuration_publication.logical.logical_artifact_id
                or self.configuration_publication.materialization.materialization_id not in self.receipt.input_materialization_ids
                or len(self.receipt.output_logical_artifacts) != 1 or len(self.receipt.output_materializations) != 1
                or self.receipt.output_logical_artifacts[0] != self.publication.logical
                or self.receipt.output_materializations[0] != self.publication.materialization
                or not any(check.check_id == 'programme-global-original-published-whole-bank-freeze' and check.passed for check in self.receipt.checks)):
            raise ValueError('programme parent aliases a different actual selection/configuration or output receipt')
        config_inputs = tuple(value for value in task.external_inputs if
            value.logical_artifact_id == self.configuration_publication.logical.logical_artifact_id)
        if (len(config_inputs) != 1 or config_inputs[0].expected_content_sha256 != self.configuration.fingerprint()
                or config_inputs[0].expected_payload_schema != self.configuration.SCHEMA
                or config_inputs[0].expected_media_type != 'application/json'
                or config_inputs[0].expected_size_bytes != self.configuration_publication.materialization.size_bytes
                or config_inputs[0].expected_outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or config_inputs[0].expected_visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
            raise ValueError('programme parent producer plan changes its exact actual configuration input')
        if len(task.outputs) != 1:
            raise ValueError('programme parent producer plan changes its exact sole output')
        output = task.outputs[0]
        logical, physical = self.publication.logical, self.publication.materialization
        if (output.output_id != GLOBAL_TASK_ID+'.product' or output.logical_artifact_id != logical.logical_artifact_id
                or output.relative_path != physical.relative_path or output.payload_schema != logical.payload_schema
                or output.profile is not logical.profile or output.media_type != logical.media_type
                or output.outcome_access is not logical.outcome_access or output.visibility_ceiling is not logical.visibility_ceiling):
            raise ValueError('programme parent producer plan changes its actual output publication contract')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.binding_id, self)


def authenticate_global_parent(plane, binding):
    """Recheck every actual guarded publication; source metadata is insufficient."""
    if type(binding) is not ScheduledProgrammeGlobalParentBinding:
        raise ValueError('programme global parent authentication requires its closed actual binding')
    binding.__post_init__()
    for record, publication in ((binding.parent, binding.publication), (binding.receipt, binding.receipt_publication),
            (binding.execution_plan, binding.execution_plan_publication), (binding.configuration, binding.configuration_publication)):
        authenticate_publication(plane, publication, record)
    return binding.parent
