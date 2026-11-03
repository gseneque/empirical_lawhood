# SPDX-License-Identifier: MPL-2.0
"""An issued producer of the original, sealed whole-group E4 calibration.

Only original acquisition/forecast locators are editable inputs. The API replays
their actual owners and reconstructs paired outcomes; the worker applies the
existing calibration equation. No caller-provided label bank is admitted here.
"""

from dataclasses import dataclass
from functools import partial
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_sampling_bindings import MatrixSamplingOriginalProduct
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner, RunnerResult, TaskContext, WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from .compact_records import ScheduledCompactBank, compact_identity
from .operation_bindings import _outputs
from .programme_records import validate_programme_bank
from .programme_reduction import ScheduledProgrammeReduction
from .programme_selection import ScheduledRevisionDataBank
from .revision_calibration import ScheduledRevisionCalibration, ScheduledRevisionCalibrationSpecification, calibrate_revision
from .revision_future_bindings import ScheduledRevisionFutureScope, ScheduledRevisionSealCustody, _read_record

KEY = "matrix-scheduled-revision.calibrate"
MAXIMUM_RECORD_BYTES = 16 * 1024**2
CHECK = "original64-group-revision-calibration"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
BLIND, SEALED, PROSPECTIVE = OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE


def pin(record, field="record_id"):
    return ObjectIdentity.from_record(getattr(record, field), record)


@dataclass(frozen=True, slots=True)
class ScheduledRevisionCalibrationScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-calibration-scope"
    record_id: str
    specification: ScheduledRevisionCalibrationSpecification
    future: ScheduledRevisionFutureScope

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.specification) is not ScheduledRevisionCalibrationSpecification or type(self.future) is not ScheduledRevisionFutureScope:
            raise TypeError("revision calibration needs its exact frozen scientific scope")
        self.specification.__post_init__()
        self.future.__post_init__()
        value, future = self.specification, self.future
        if (future.programme.mode != "E4_REVISION_CALIBRATION"
                or (value.development_programme, value.calibration_programme, value.nomination, value.frozen_models)
                    != (future.development.identity, future.programme.identity, future.nomination.identity, future.frozen.identity)):
            raise ValueError("revision calibration changes its original separate64-group programme or frozen models")

    @property
    def identity(self):
        return pin(self)


@dataclass(frozen=True, slots=True)
class ScheduledRevisionCalibrationWave(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-calibration-wave"
    wave_id: str
    original: MatrixSamplingOriginalProduct

    def __post_init__(self):
        validate_stable_id(self.wave_id)
        if type(self.original) is not MatrixSamplingOriginalProduct:
            raise TypeError("revision calibration needs its actual original issued collector and reveal locator")
        self.original.__post_init__()
        binding = self.original.prior_execution
        if (binding.task_id != self.wave_id + ".collect" or binding.record_id_field != "result_id"
                or binding.record.object_schema != "empirical-lawhood/matrix-scheduled-programme/wave-result"
                or binding.record.object_version != "1.0.0" or binding.additional_output_schema_ids or binding.scope_output_schema_ids):
            raise ValueError("revision calibration substitutes its exact original wave collector")


@dataclass(frozen=True, slots=True)
class ScheduledRevisionCalibrationSources(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-calibration-sources"
    record_id: str
    waves: tuple[ScheduledRevisionCalibrationWave, ...]
    forecasts: tuple[ScheduledRevisionSealCustody, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.waves) is not tuple or type(self.forecasts) is not tuple
                or len(self.waves) != 16 or len(self.forecasts) != 576
                or any(type(value) is not ScheduledRevisionCalibrationWave for value in self.waves)
                or any(type(value) is not ScheduledRevisionSealCustody for value in self.forecasts)
                or tuple(value.wave_id for value in self.waves) != tuple(sorted({value.wave_id for value in self.waves}))
                or tuple(value.forecast.case_id for value in self.forecasts)
                    != tuple(sorted({value.forecast.case_id for value in self.forecasts}))
                or len({value.original.prior_execution.run_id for value in self.waves}) != 16):
            raise ValueError("revision calibration requires exactly16 original waves and576 distinct earlier forecasts")
        for value in (*self.waves, *self.forecasts):
            value.__post_init__()

    @property
    def identity(self):
        return pin(self)

    def validate_scope(self, scope):
        scope.__post_init__()
        programme = scope.future.programme
        if (tuple(value.wave_id for value in self.waves) != tuple(value.wave_id for value in programme.waves)
                or tuple(value.forecast.case_id for value in self.forecasts) != tuple(case.root_id for case in programme.cases)
                or any(value.forecast != scope.future.forecast(value.forecast.case_id, record_id=value.forecast.record_id)
                    for value in self.forecasts)):
            raise ValueError("revision calibration substitutes an original wave, frozen prediction, source or complete case census")


@dataclass(frozen=True, slots=True)
class ScheduledRevisionCalibrationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-calibration-config"
    config_id: str
    scope: ObjectIdentity
    sources: ObjectIdentity
    bank: ObjectIdentity
    unit_ids: tuple[str, ...]
    reduction_id: str
    data_id: str
    calibration_id: str

    def __post_init__(self):
        for value in (self.config_id, self.reduction_id, self.data_id, self.calibration_id):
            validate_stable_id(value)
        for value, kind in ((self.scope, ScheduledRevisionCalibrationScope), (self.sources, ScheduledRevisionCalibrationSources),
                (self.bank, ScheduledCompactBank)):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError("revision calibration changes an exact scientific input type")
        if (self.config_id != "config." + calibration_task_id(self.scope)
                or type(self.unit_ids) is not tuple or len(self.unit_ids) != 64
                or self.unit_ids != tuple(sorted(set(self.unit_ids)))):
            raise ValueError("revision calibration changes its exact producer or complete64-group denominator")
        for value in self.unit_ids:
            validate_stable_id(value)

    @property
    def identity(self):
        return pin(self, "config_id")


def calibration_task_id(scope):
    return KEY + "." + scope.object_fingerprint


@dataclass(frozen=True, slots=True)
class RevisionCalibrationInputs:
    """Original products reconstructed by the parent, never an authority token."""
    reduction: ScheduledProgrammeReduction
    data: ScheduledRevisionDataBank
    forecasts: tuple

    def __post_init__(self):
        if (type(self.reduction) is not ScheduledProgrammeReduction or type(self.data) is not ScheduledRevisionDataBank
                or type(self.forecasts) is not tuple):
            raise TypeError("revision calibration retains exact immutable reconstructed scientific inputs")

    def assess(self, config, scope):
        if (self.reduction.reduction_id != config.reduction_id or self.data.bank_id != config.data_id
                or type(self.forecasts) is not tuple):
            raise ValueError("revision calibration changes its exact reconstructed input identities")
        future = scope.future
        return calibrate_revision(scope.specification, future.development, future.nomination, future.frozen,
            future.programme, self.reduction, self.data, self.forecasts, record_id=config.calibration_id)


@dataclass(frozen=True, slots=True)
class PreparedRevisionCalibration:
    run_id: str
    task_id: str
    execution_plan: ObjectIdentity
    input_materialization_ids: tuple[str, ...]
    configuration: ObjectIdentity
    scope: ObjectIdentity
    sources: ObjectIdentity
    inputs: RevisionCalibrationInputs


def scientific_root_validator(config, context):
    root = context.root
    if (type(config) is not ScheduledRevisionCalibrationConfig or type(root) is not StudyDraft
            or root.system is None or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or root.development_unit_ids or root.evaluation_unit_ids != config.unit_ids
            or not {config.scope, config.sources, config.bank} <= {value.object_identity for value in root.design_inputs}
            or context.node_id != calibration_task_id(config.scope)
            or context.stage is not ScientificStage.TRANSFORM or context.outcome_access is not SEALED
            or context.visibility_ceiling is not PROSPECTIVE or context.unit_ids != config.unit_ids
            or context.selected_unit_ids != config.unit_ids or len(context.config_inputs) != 1):
        raise ValueError("revision calibration changes its original complete issued scope, access or producer")
    incoming = tuple(value for value in context.links if value.consumer_node_id == context.node_id)
    if (len(incoming) != 3 or {value.consumer_input_id for value in incoming} != {"scope", "sources", "bank"}
            or any(value.producer_node_id is not None or value.external_input_id is None for value in incoming)):
        raise ValueError("revision calibration changes its exact original source prerequisite census")


class ScheduledRevisionCalibrationWorker:
    def __init__(self, manifest=None, prepared=None):
        self.manifest = manifest or operation_declarations()[0].manifest()
        self.prepared = prepared

    def execute(self, context):
        try:
            contract, prepared = context.prepared_invocation, self.prepared
            if (type(context) is not TaskContext or type(contract) is not PreparedInvocationContract
                    or type(prepared) is not PreparedRevisionCalibration or type(prepared.inputs) is not RevisionCalibrationInputs
                    or context.permissions != self.manifest.permissions or context.outcome_access is not SEALED
                    or context.dependency_receipts or len(context.input_ports) != 4):
                raise PermissionError("revision calibration requires actual issued current and original-source preparation")
            contract.require_complete()
            contract.validate_context(context)
            if (contract.manifest != self.manifest or contract.native_effect
                    or (prepared.run_id, prepared.task_id, prepared.execution_plan, prepared.input_materialization_ids)
                        != (context.run_id, context.task_id, contract.execution_plan, context.input_materialization_ids)):
                raise PermissionError("revision calibration substitutes its complete prepared task/plan/input census")
            values = {}
            for kind in (ScheduledRevisionCalibrationConfig, ScheduledRevisionCalibrationScope, ScheduledRevisionCalibrationSources, ScheduledCompactBank):
                ports = tuple(port for port in context.input_ports if port.payload_schema == kind.SCHEMA)
                if len(ports) != 1 or ports[0].kind is not WorkerInputKind.EXTERNAL:
                    raise ValueError("revision calibration aliases or omits an exact declared external input")
                values[kind] = _read_record(ports[0], kind), ports[0]
            config, config_port = values[ScheduledRevisionCalibrationConfig]
            scope, _ = values[ScheduledRevisionCalibrationScope]
            sources, _ = values[ScheduledRevisionCalibrationSources]
            bank, _ = values[ScheduledCompactBank]
            sources.validate_scope(scope)
            validate_programme_bank(scope.future.programme, bank)
            if ((config.scope, config.sources, config.bank, config.unit_ids) !=
                    (scope.identity, sources.identity, compact_identity(bank), scope.future.programme.group_ids)
                    or (prepared.configuration, prepared.scope, prepared.sources) != (config.identity, scope.identity, sources.identity)
                    or context.task_id != calibration_task_id(scope.identity) or context.config.artifact_id != config_port.artifact_id
                    or context.config.content_sha256 != config.fingerprint() or context.config.config_id != config.config_id
                    or context.config.config_schema != config.SCHEMA):
                raise ValueError("revision calibration substitutes exact original scope, configuration, bank or groups")
            result = _outputs(context, prepared.inputs.assess(config, scope))
            return RunnerResult(result.outputs, (ReceiptCheck(CHECK, True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def prepare_for_invocation(supplier, runner):
    callback = getattr(supplier, "prepare_revision_calibration", None)
    if not callable(callback):
        raise PermissionError("revision calibration requires actual current and original issued custody preparation")
    return ParentPreparedTaskRunner(runner.manifest, partial(callback, runner=runner))


def operation_declarations():
    kinds = (ScheduledRevisionCalibrationScope, ScheduledRevisionCalibrationSources, ScheduledCompactBank)
    permissions = tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_SEALED_OUTCOMES,
        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS)))
    return (RecursiveOperationDeclaration(KEY, "1.0.0", KEY + ".original-wave-paired-rank.v1", CapabilityKind.TRANSFORM,
        ScheduledRevisionCalibrationConfig, ScientificStage.TRANSFORM,
        tuple(sorted((RecursivePortContract(name, kind.SCHEMA, "application/json", MAXIMUM_RECORD_BYTES)
            for name, kind in zip(("scope", "sources", "bank"), kinds, strict=True)), key=lambda value: value.port_id)),
        (OutputTemplate("product", ScheduledRevisionCalibration.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        permissions, EvidenceCeiling.RESPONSE, SEALED, PROSPECTIVE, BUDGET, (CHECK,), ScheduledRevisionCalibrationWorker,
        {ScheduledRevisionCalibration.SCHEMA: ScheduledRevisionCalibration},
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=lambda config: config.unit_ids,
            scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(runner_preparation_factory=prepare_for_invocation),
        input_record_types=tuple(sorted(kinds, key=lambda kind: (kind.SCHEMA, kind.VERSION)))),)


def operation_factories():
    return tuple(value.provider_factory() for value in operation_declarations())


def revision_calibration_draft(*, root, config, scope, sources, bank, proof_owners, operational_budget, draft_id):
    """Lower one sealed producer from exact original source locators, without I/O."""
    if type(root) is not StudyDraft or type(config) is not ScheduledRevisionCalibrationConfig:
        raise TypeError("revision calibration requires its actual ordinary scientific root/configuration")
    sources.validate_scope(scope)
    validate_programme_bank(scope.future.programme, bank)
    if (config.scope, config.sources, config.bank, config.unit_ids) != (scope.identity, sources.identity, compact_identity(bank), scope.future.programme.group_ids):
        raise ValueError("revision calibration lowering substitutes its exact original scientific input census")
    declaration, = operation_declarations()
    node = calibration_task_id(scope.identity)
    operation = RecursiveOperationSpec.from_config(node_id=node, selection=declaration.registration().selection,
        config_id=config.config_id, config=config, obligation_ids=proof_owners, resource_budget=operational_budget)
    operands = (("scope", scope, scope.identity), ("sources", sources, sources.identity), ("bank", bank, compact_identity(bank)))
    external, links, records = [], [], {}
    for name, record, identity in operands:
        if len(record.canonical_bytes()) > MAXIMUM_RECORD_BYTES:
            raise ValueError("revision calibration source exceeds its closed16MiB operand bound")
        input_id = "external." + identity.object_id
        external.append(RecursiveExternalInput(input_id, identity.object_id, record.SCHEMA, "application/json",
            len(record.canonical_bytes()), BLIND, PROSPECTIVE, record.fingerprint(), "SOURCE"))
        links.append(RecursiveInputLink("edge." + node + "." + name, node, name, external_input_id=input_id, scientific_role="SOURCE"))
        records[identity.object_id] = record
    return RecursiveStudyDraft(draft_id, root.question, root.campaign, (), (), (), (operation,),
        tuple(sorted(external, key=lambda row: row.input_id)), tuple(sorted(links, key=lambda row: row.edge_id)),
        (node,), prospective_draft=root), records
