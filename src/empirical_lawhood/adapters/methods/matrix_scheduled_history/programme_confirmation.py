# SPDX-License-Identifier: MPL-2.0
"""Distinct confirmation preparation after a genuine complete global parent.

The new actual config, output and provider never alias the calibration freeze.
The old compact commitment remains exact inner scientific data. A code-injected
runtime view carries authenticated identities only, without parent outcomes.
"""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties,
)

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, CandidateExecutionPlan, ExecutionPlan, OutputTemplate, ScientificStage

from .commitment import ScheduledCommitment
from .commitment import authenticate_publication, require_publication_copy
from .compact_records import ScheduledCompactBank
from .operation_bindings import BUDGET
from .programme_composition import expected_global_commitment
from .programme_global import GLOBAL_TASK_ID, MAXIMUM_CONFIG_BYTES, source_publications, validate_programme_root
from .programme_parent import _published
from .programme_qualified_parent import ScheduledProgrammeQualifiedParentDeclaration, validate_qualified_parent_declaration
from .programme_records import MAXIMUM_PROGRAMME_BYTES, NAMESPACE, ScheduledProgramme, validate_programme_bank

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

CONFIG_ID = 'config.'+NAMESPACE+'.confirmation-global-commit'
CAPABILITY_KEY = NAMESPACE+'.confirmation-global-commit'
BLIND, PROSPECTIVE = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeConfirmationGlobalConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/confirmation-global-config'
    config_id: str
    programme: ScheduledProgramme
    bank: ObjectIdentity
    qualified_parent: ScheduledProgrammeQualifiedParentDeclaration

    def __post_init__(self):
        if (self.config_id != CONFIG_ID or type(self.programme) is not ScheduledProgramme
                or self.programme.mode != 'E4_CONFIRMATION' or self.bank != self.programme.bank
                or type(self.qualified_parent) is not ScheduledProgrammeQualifiedParentDeclaration
                or len(self.canonical_bytes()) > MAXIMUM_CONFIG_BYTES):
            raise ValueError('confirmation freeze requires its distinct bounded config and genuine parent declaration')


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeAuthenticatedParent:
    """Runtime-only result of stock original issue/execute/reveal custody replay.

    This view is supplied by installed parent-side API code. It is never a
    configuration operand, a canonical authority record or a boolean claim.
    """
    declaration: ObjectIdentity
    bank: ObjectIdentity
    package: ObjectIdentity
    execution_plan: ObjectIdentity
    producing_receipt: ObjectIdentity
    qualification_receipt: ObjectIdentity
    adjudication: ObjectIdentity
    evidence: ObjectIdentity


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeConfirmationGlobalCommit(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/confirmation-global-commit'
    commitment_id: str
    configuration: ObjectIdentity
    programme: ObjectIdentity
    bank: ObjectIdentity
    qualified_parent: ObjectIdentity
    semantic_commitment: ScheduledCommitment

    def __post_init__(self):
        validate_stable_id(self.commitment_id)
        if (self.configuration.object_schema != ScheduledProgrammeConfirmationGlobalConfig.SCHEMA
                or self.configuration.object_id != CONFIG_ID
                or self.programme.object_schema != ScheduledProgramme.SCHEMA
                or self.bank.object_schema != ScheduledCompactBank.SCHEMA
                or self.qualified_parent.object_schema != ScheduledProgrammeQualifiedParentDeclaration.SCHEMA
                or type(self.semantic_commitment) is not ScheduledCommitment
                or self.semantic_commitment.shared_context != self.bank
                or self.commitment_id != self.programme.object_id+'.confirmation-global-commit'):
            raise ValueError('confirmation product aliases actual preparation and original semantic identities')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.commitment_id, self)


def confirmation_committed(config, bank, parent):
    if type(config) is not ScheduledProgrammeConfirmationGlobalConfig:
        raise ValueError('confirmation preparation requires its distinct actual configuration')
    validate_programme_bank(config.programme, bank)
    validate_qualified_parent_declaration(bank, config.qualified_parent)
    if (type(parent) is not ScheduledProgrammeAuthenticatedParent or parent.declaration != config.qualified_parent.identity
            or parent.bank != config.bank or parent.evidence != config.qualified_parent.evidence
            or parent.adjudication != config.qualified_parent.binding.adjudication
            or parent.producing_receipt.object_id != config.qualified_parent.binding.receipt_id
            or parent.qualification_receipt.object_id != config.qualified_parent.binding.qualification_receipt_id):
        raise PermissionError('confirmation preparation lacks independently replayed original qualified-parent custody')
    return ScheduledProgrammeConfirmationGlobalCommit(config.programme.programme_id+'.confirmation-global-commit',
        ObjectIdentity.from_record(config.config_id, config), config.programme.identity, config.bank,
        config.qualified_parent.identity, expected_global_commitment(bank))


def scientific_root_validator(config, context):
    if (type(config) is not ScheduledProgrammeConfirmationGlobalConfig or context.node_id != GLOBAL_TASK_ID
            or context.stage is not ScientificStage.FREEZE or context.outcome_access is not BLIND
            or context.visibility_ceiling is not PROSPECTIVE or context.unit_ids != config.programme.group_ids
            or context.selected_unit_ids != config.programme.group_ids
            or len(context.config_inputs) != 1 or context.config_inputs[0].record != config):
        raise ValueError('confirmation preparation changes its actual node, stage or global group scope')
    validate_programme_root(config.programme, context)
    if config.qualified_parent.identity not in {value.object_identity for value in context.root.design_inputs}:
        raise ValueError('confirmation preparation omits its exact original qualified-parent declaration pin')


class ScheduledProgrammeConfirmationGlobalCommitter:
    def __init__(self, manifest, authenticated_parent=None):
        self.manifest = manifest
        self.authenticated_parent = authenticated_parent

    def execute(self, context):
        try:
            if (type(context) is not TaskContext or context.task_id != GLOBAL_TASK_ID
                    or context.permissions != self.manifest.permissions or context.outcome_access is not BLIND
                    or type(self.authenticated_parent) is not ScheduledProgrammeAuthenticatedParent
                    or not BUDGET.contains(context.resource_budget)
                    or any(p.kind is not WorkerInputKind.EXTERNAL or p.outcome_access is not BLIND
                        or p.visibility_ceiling is not PROSPECTIVE for p in context.input_ports)):
                raise PermissionError('confirmation freeze requires actual prepared runtime authority before input reads')
            configs = tuple(p for p in context.input_ports if p.payload_schema == ScheduledProgrammeConfirmationGlobalConfig.SCHEMA)
            banks = tuple(p for p in context.input_ports if p.payload_schema == ScheduledCompactBank.SCHEMA)
            if len(configs) != 1 or len(banks) != 1:
                raise ValueError('confirmation freeze omits its exact actual config and bank')
            config_raw, bank_raw = configs[0].read(), banks[0].read()
            config = decode_canonical_bytes(config_raw, ScheduledProgrammeConfirmationGlobalConfig, maximum_bytes=MAXIMUM_CONFIG_BYTES)
            bank = decode_canonical_bytes(bank_raw, ScheduledCompactBank, maximum_bytes=MAXIMUM_PROGRAMME_BYTES)
            if (config.canonical_bytes() != config_raw or bank.canonical_bytes() != bank_raw
                    or context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
                    or context.config.content_sha256 != sha256(config_raw).hexdigest()
                    or context.config.artifact_id != configs[0].artifact_id
                    or banks[0].artifact_id != bank.bank_id or sha256(bank_raw).hexdigest() != config.bank.object_fingerprint):
                raise ValueError('confirmation freeze changes exact current config/shared bank bytes')
            value = confirmation_committed(config, bank, self.authenticated_parent)
            expected = {configs[0].artifact_id, bank.bank_id}
            for record, publication in source_publications(bank):
                ports = tuple(p for p in context.input_ports if p.artifact_id == publication.logical.logical_artifact_id)
                if len(ports) != 1:
                    raise ValueError('confirmation freeze drops an original blind operand')
                raw = ports[0].read()
                if raw != record.canonical_bytes() or sha256(raw).hexdigest() != publication.materialization.physical_sha256:
                    raise ValueError('confirmation freeze substitutes original blind source bytes')
                require_publication_copy(record, ports[0], publication)
                expected.add(ports[0].artifact_id)
            for publication in bank.response_selection.template_publications:
                ports = tuple(p for p in context.input_ports if p.artifact_id == publication.logical.logical_artifact_id)
                if len(ports) != 1:
                    raise ValueError('confirmation freeze omits a complete fixed instrument')
                raw = ports[0].read()
                if (ports[0].payload_schema != MATRIX_ARRAY_SCHEMA or len(raw) != publication.materialization.size_bytes
                        or sha256(raw).hexdigest() != publication.logical.content_sha256
                        or sha256(raw).hexdigest() != publication.materialization.physical_sha256
                        or ports[0].media_type != publication.logical.media_type
                        or ports[0].size_bytes != publication.materialization.size_bytes):
                    raise ValueError('confirmation freeze changes original fixed instrument bytes')
                expected.add(ports[0].artifact_id)
            if len(context.input_ports) != len(expected) or {p.artifact_id for p in context.input_ports} != expected:
                raise ValueError('confirmation freeze receives an undeclared or repeated input')
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != GLOBAL_TASK_ID+'.product'
                    or context.output_ports[0].payload_schema != value.SCHEMA
                    or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON):
                raise ValueError('confirmation freeze changes its actual distinct output contract')
            return RunnerResult((TaskOutputPayload(GLOBAL_TASK_ID+'.product', value.canonical_bytes()),),
                (ReceiptCheck('programme-confirmation-authenticated-global-parent-freeze', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_factories():
    return tuple(row.provider_factory() for row in operation_declarations())


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeConfirmationParentBinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/confirmation-parent-binding'
    binding_id: str
    parent: ScheduledProgrammeConfirmationGlobalCommit
    publication: ArtifactWriteResult
    receipt: CanonicalTaskReceipt
    receipt_publication: ArtifactWriteResult
    execution_plan: ExecutionPlan | CandidateExecutionPlan
    execution_plan_publication: ArtifactWriteResult
    configuration: ScheduledProgrammeConfirmationGlobalConfig
    configuration_publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.binding_id)
        if (type(self.parent) is not ScheduledProgrammeConfirmationGlobalCommit
                or type(self.configuration) is not ScheduledProgrammeConfirmationGlobalConfig
                or type(self.receipt) is not CanonicalTaskReceipt
                or type(self.execution_plan) not in (CandidateExecutionPlan, ExecutionPlan)
                or self.parent.configuration != ObjectIdentity.from_record(self.configuration.config_id, self.configuration)
                or self.parent.programme != self.configuration.programme.identity or self.parent.bank != self.configuration.bank
                or self.parent.qualified_parent != self.configuration.qualified_parent.identity
                or self.receipt.task_id != GLOBAL_TASK_ID or self.receipt.operational_status is not OperationalStatus.SUCCEEDED
                or self.receipt.implementation_commit != self.execution_plan.implementation_commit):
            raise ValueError('confirmation parent changes actual product/config/successful receipt/plan')
        for record, publication in ((self.parent, self.publication), (self.receipt, self.receipt_publication),
                (self.execution_plan, self.execution_plan_publication), (self.configuration, self.configuration_publication)):
            _published(record, publication)
        tasks = tuple(task for task in self.execution_plan.tasks if task.task_id == GLOBAL_TASK_ID)
        factory, = operation_factories()
        if len(tasks) != 1:
            raise ValueError('confirmation parent omits its actual global producer')
        task = tasks[0]
        if (task.stage is not ScientificStage.FREEZE or task.barrier is not BarrierKind.FREEZE
                or task.capability.capability_key != factory.manifest.capability_key
                or task.capability.capability_version != factory.manifest.capability_version
                or task.capability_implementation_sha256 != factory.manifest.implementation_sha256
                or task.capability.config.config_id != CONFIG_ID or task.capability.config.config_schema != self.configuration.SCHEMA
                or task.capability.config.config_schema_sha256 != factory.manifest.config_schema_sha256
                or task.capability.config.content_sha256 != self.configuration.fingerprint()
                or task.capability.config.artifact_id != self.configuration_publication.logical.logical_artifact_id
                or self.configuration_publication.materialization.materialization_id not in self.receipt.input_materialization_ids
                or self.receipt.output_logical_artifacts != (self.publication.logical,)
                or self.receipt.output_materializations != (self.publication.materialization,)
                or not any(c.check_id == 'programme-confirmation-authenticated-global-parent-freeze' and c.passed
                    for c in self.receipt.checks)):
            raise ValueError('confirmation parent aliases a different actual producer/config/output receipt')
        inputs = tuple(p for p in task.external_inputs if p.logical_artifact_id == self.configuration_publication.logical.logical_artifact_id)
        if (len(inputs) != 1 or inputs[0].expected_payload_schema != self.configuration.SCHEMA
                or inputs[0].expected_content_sha256 != self.configuration.fingerprint()
                or inputs[0].expected_size_bytes != self.configuration_publication.materialization.size_bytes
                or inputs[0].expected_media_type != 'application/json' or inputs[0].expected_outcome_access is not BLIND
                or inputs[0].expected_visibility_ceiling is not PROSPECTIVE or len(task.outputs) != 1):
            raise ValueError('confirmation parent changes exact actual configuration input or sole output')
        output, logical, physical = task.outputs[0], self.publication.logical, self.publication.materialization
        if (output.output_id != GLOBAL_TASK_ID+'.product' or output.logical_artifact_id != logical.logical_artifact_id
                or output.relative_path != physical.relative_path or output.payload_schema != logical.payload_schema
                or output.profile is not logical.profile or output.media_type != logical.media_type
                or output.outcome_access is not logical.outcome_access or output.visibility_ceiling is not logical.visibility_ceiling):
            raise ValueError('confirmation parent changes the actual output publication contract')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.binding_id, self)


def authenticate_confirmation_parent(plane, binding):
    if type(binding) is not ScheduledProgrammeConfirmationParentBinding:
        raise ValueError('confirmation parent requires its closed distinct binding')
    binding.__post_init__()
    for record, publication in ((binding.parent, binding.publication), (binding.receipt, binding.receipt_publication),
            (binding.execution_plan, binding.execution_plan_publication), (binding.configuration, binding.configuration_publication)):
        authenticate_publication(plane, publication, record)
    return binding.parent


def operation_declarations():
    from .programme_global import operation_declarations as global_declarations
    original, = global_declarations()
    def prepare(supplier, runner):
        from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner
        return ParentPreparedTaskRunner(runner.manifest, lambda context: supplier.prepare_programme_task(context, runner))
    selected = RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + 'confirmation-global-commit',
        capability_version="1.0.0",
        implementation_id='genuine-qualified-parent-confirmation-freeze.v1',
        kind=CapabilityKind.EXPERIMENT_DESIGNER,
        config_record_type=ScheduledProgrammeConfirmationGlobalConfig,
        stage=ScientificStage.FREEZE,
        input_ports=original.input_ports,
        outputs=(OutputTemplate('product', ScheduledProgrammeConfirmationGlobalCommit.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_FROZEN_MODELS))),
        evidence_ceiling=EvidenceCeiling.RESPONSE,
        outcome_access=BLIND,
        visibility_ceiling=PROSPECTIVE,
        resources=BUDGET,
        conformance_check_ids=tuple(sorted(('distinct-confirmation-preparation-identities', 'exact-original-qualified-parent-replay', 'original-published-operands'))),
        runner_factory=lambda: ScheduledProgrammeConfirmationGlobalCommitter(selected.manifest()),
        record_codecs={**original.record_codecs, ScheduledProgrammeConfirmationGlobalCommit.SCHEMA: ScheduledProgrammeConfirmationGlobalCommit},
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c: tuple(sorted({c.programme.fingerprint(), c.bank.object_fingerprint, c.qualified_parent.fingerprint()})), scientific_unit_ids=lambda c: c.programme.group_ids, scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE, runner_preparation_factory=prepare),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        storage_codecs=MATRIX_STORAGE_CODECS,
    )
    return (selected,)
