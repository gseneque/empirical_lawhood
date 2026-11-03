# SPDX-License-Identifier: MPL-2.0
"""Current E3 statistical ports over the existing five mathematical owners.

Composition requires the owning API's original-publication and scientific-root
validators. Prepared bytes and the recomputed prefit join do not replace those
acts. These declarations are uninstalled; no qualification or reveal is granted.
"""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from functools import partial
from hashlib import sha256
import inspect
import sys
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledAllocation, ScheduledReservation, ScheduledSelection
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.kernel.time import AvailabilitySpec, InformationCutoff
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, derived_outcome_access
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner, TaskContext, WorkerInputKind, WorkerInputPort
from empirical_lawhood.runtime.plans import BarrierKind, ExecutionTask, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, RegisteredPublicationRequirement
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from . import experiment_methods as exposed
from . import protected_experiment_methods as science
from .experiment_specification import MatrixResponseErrorSpecification
from .protected_experiment_inputs import (
    E3RequiredPublication, ProtectedE3PreFitJoin, ProtectedE3SourceInputs,
    e3_prepared_publication_transports, project_protected_e3_allocation, require_e3_reserved_fit_inputs,
)
from .protected_feature_bindings import feature_task_id
from .protected_original_publications import ProtectedE3OriginalPublications
from .protected_prefix_workers import _read
from .protected_source_records import NAMESPACE, ProtectedE3NativeSourceManifest, _reference, identity
from .protected_input_custody import matches_protected_e3_producer

BUDGET = ResourceBudget(1, None, 0, None, None, None)
MEDIA = "application/json"
KINDS = ("fit", "freeze", "forecast", "calibrate", "assess")
PHASES = ("fit", "model-freeze", "forecast", "calibrate", "calibration-freeze", "assess")
PUBLICATION_KEYS = ("allocation", "native-selection", "reservation", "roles")


def statistical_task_id(specification, allocation, operation, *, mode="", root=None):
    _reference(specification, MatrixResponseErrorSpecification)
    _reference(allocation, UnitAllocation)
    if (operation not in KINDS or operation == "freeze" and mode not in ("model", "calibration")
            or operation == "forecast" and mode not in ("calibration", "evaluation")
            or operation not in ("freeze", "forecast") and mode
            or (root is not None) != (operation == "forecast")):
        raise ValueError("protected E3 statistical task changes its exact operation/mode/root")
    if root is not None:
        if type(root) is not MatrixProgrammeRoot:
            raise TypeError("protected E3 forecast task requires its exact seedless root")
        root.__post_init__()
        expected = MatrixProgrammeRole.CALIBRATION if mode == "calibration" else MatrixProgrammeRole.CONFIRMATION
        if root.role is not expected:
            raise ValueError("protected E3 statistical forecast changes its allocated root role")
    digest = sha256(canonical_json_bytes((specification, allocation, operation, mode, root))).hexdigest()
    return NAMESPACE + ".statistical." + operation + "." + digest


def _census(values):
    if (type(values) is not tuple or tuple(role for role, _ in values) != ("calibration", "evaluation")
            or any(type(count) is not int or count < 1 for _, count in values)):
        raise ValueError("protected E3 statistical config changes its complete CAL/CONF census")


@dataclass(frozen=True, slots=True)
class ProtectedE3StatisticalConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-statistical-config"
    record_id: str
    operation: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    query_census: tuple[tuple[str, int], ...]
    mode: str = ""
    root: MatrixProgrammeRoot | None = None

    def __post_init__(self):
        _census(self.query_census)
        if self.operation == "fit" or self.record_id != "config." + statistical_task_id(
                self.specification, self.allocation, self.operation, mode=self.mode, root=self.root):
            raise ValueError("protected E3 statistical config changes its derived task or fit metadata")


@dataclass(frozen=True, slots=True)
class ProtectedE3FitConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-fit-config"
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    query_census: tuple[tuple[str, int], ...]
    source_manifest: ObjectIdentity
    training_allocation: ObjectIdentity
    fit_cutoff: InformationCutoff
    publications: tuple[tuple[str, ArtifactWriteResult, AvailabilitySpec], ...]
    original_publications: ProtectedE3OriginalPublications | None = None

    def __post_init__(self):
        _census(self.query_census)
        _reference(self.source_manifest, ProtectedE3NativeSourceManifest)
        _reference(self.training_allocation, UnitAllocation)
        if (self.record_id != "config." + statistical_task_id(self.specification, self.allocation, "fit")
                or type(self.fit_cutoff) is not InformationCutoff or type(self.publications) is not tuple
                or tuple(row[0] for row in self.publications) != PUBLICATION_KEYS):
            raise ValueError("protected E3 fit config loses its exact four publication bindings/cutoff")
        self.fit_cutoff.__post_init__()
        if self.original_publications is not None:
            if type(self.original_publications) is not ProtectedE3OriginalPublications:
                raise TypeError("protected E3 fit requires its exact original-publication custody carrier")
            self.original_publications.__post_init__()
            if (self.original_publications.specification != self.specification
                    or self.original_publications.source_manifest != self.source_manifest
                    or self.original_publications.training_allocation != self.training_allocation):
                raise ValueError("protected E3 fit changes its original source custody identities")
        for _, publication, availability in self.publications:
            if type(publication) is not ArtifactWriteResult or type(availability) is not AvailabilitySpec:
                raise TypeError("protected E3 fit requires exact publication/availability records")
            publication.__post_init__()
            availability.__post_init__()

    @property
    def operation(self):
        return "fit"

    @property
    def mode(self):
        return ""

    @property
    def root(self):
        return None


def _phase(config):
    if type(config) not in (ProtectedE3FitConfig, ProtectedE3StatisticalConfig):
        raise TypeError("protected E3 statistics requires its exact selected config")
    config.__post_init__()
    return config.mode + "-freeze" if config.operation == "freeze" else config.operation


def _units(config):
    _phase(config)
    return () if config.root is None else (config.root.independent_group_id,)


def _operands(config):
    _phase(config)
    return tuple(sorted((config.specification.object_fingerprint, config.allocation.object_fingerprint)))


def _ports(phase, *, confirmation=True):
    common = {"specification": MatrixResponseErrorSpecification, "allocation": UnitAllocation}
    if phase == "fit":
        return {**common, "manifest": ProtectedE3NativeSourceManifest, "training-allocation": UnitAllocation,
            "original-allocation": ScheduledAllocation, "native-selection": ScheduledSelection, "reservation": ScheduledReservation,
            "features": exposed.MatrixE3FeatureBank, "outcomes": exposed.MatrixE3OutcomeBank}
    if phase == "model-freeze":
        return {**common, "models": science.ProtectedE3ModelSet, "prefit-join": ProtectedE3PreFitJoin}
    if phase == "calibration-freeze":
        return {**common, "models": science.ProtectedE3ModelSet, "model-freeze": science.ProtectedE3FrozenProducts,
            "calibration": science.ProtectedE3Calibration}
    if phase == "forecast":
        selected = {**common, "models": science.ProtectedE3ModelSet, "frozen": science.ProtectedE3FrozenProducts,
            "feature": science.ProtectedE3CausalFeature}
        return {**selected, **({"calibration": science.ProtectedE3Calibration,
            "model-freeze": science.ProtectedE3FrozenProducts} if confirmation else {})}
    selected = {**common, "frozen": science.ProtectedE3FrozenProducts, "forecasts": science.ProtectedE3Forecast,
        "outcomes": science.ProtectedE3PairedOutcome}
    return {**selected, **({"models": science.ProtectedE3ModelSet} if phase == "calibrate" else {})}


def _product(phase):
    return {"fit": science.ProtectedE3ModelSet, "model-freeze": science.ProtectedE3FrozenProducts,
        "calibration-freeze": science.ProtectedE3FrozenProducts, "forecast": science.ProtectedE3Forecast,
        "calibrate": science.ProtectedE3Calibration, "assess": science.ProtectedE3Assessment}[phase]


def _stage(phase):
    return (ScientificStage.DEVELOP if phase == "fit" else ScientificStage.TRANSFORM if phase == "calibrate"
        else ScientificStage.FALSIFY if phase == "assess" else ScientificStage.FREEZE)


def _access(phase):
    return OutcomeAccess.DEVELOPMENT_VISIBLE if phase in ("fit", "model-freeze") else OutcomeAccess.EVALUATION_SEALED


def _global_hook(value):
    if type(value) is partial:
        _global_hook(value.func)
        canonical_json_bytes((value.args, value.keywords))
        return
    if (not inspect.isfunction(value) or value.__qualname__ != value.__name__
            or getattr(sys.modules.get(value.__module__), value.__name__, None) is not value):
        raise TypeError("protected E3 installation requires actual module-global code-owned hooks")


@dataclass(frozen=True, slots=True)
class _RunnerFactory:
    phase: str
    publication_requirement: RegisteredPublicationRequirement
    scientific_root_validator: object
    outcome_task_id: object

    def __call__(self):
        declaration = _declaration(self.phase, self.publication_requirement,
            self.scientific_root_validator, self.outcome_task_id)
        return ProtectedE3StatisticalRunner(self.phase, declaration.manifest(), self.outcome_task_id)


def prepare_for_invocation(supplier, runner):
    """Keep actual issued-fit custody in the parent before TRAIN delivery."""
    if type(runner) is not ProtectedE3StatisticalRunner or runner.phase != "fit":
        raise TypeError("protected E3 parent preparation requires its exact current fit runner")
    callback = getattr(supplier, "prepare_protected_e3_fit", None)
    if not callable(callback):
        raise PermissionError("protected E3 fit requires its installed parent custody preparation")
    return ParentPreparedTaskRunner(runner.manifest, partial(callback, runner=runner))


def _declaration(phase, publication_requirement, scientific_root_validator, outcome_task_id):
    kinds = _ports(phase)
    config_type = ProtectedE3FitConfig if phase == "fit" else ProtectedE3StatisticalConfig
    output = _product(phase)
    codecs = {kind.SCHEMA: kind for kind in (config_type, output, ProtectedE3PreFitJoin, *kinds.values())}
    inputs = tuple(RecursivePortContract(name, kind.SCHEMA, MEDIA, None,
        minimum_count=0 if phase == "forecast" and name in ("model-freeze", "calibration") else 1,
        maximum_count=None if phase in ("calibrate", "assess") and name in ("forecasts", "outcomes") else 1)
        for name, kind in sorted(kinds.items()))
    outputs = (OutputTemplate("product", output.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, ".json"),)
    if phase == "fit":
        outputs = (OutputTemplate("prefit-join", ProtectedE3PreFitJoin.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, ".json"), *outputs)
    permissions = [CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
        CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_FROZEN_MODELS]
    if phase not in ("fit", "model-freeze"):
        permissions.append(CapabilityPermission.READ_SEALED_OUTCOMES)
    return RecursiveOperationDeclaration(NAMESPACE + "." + phase, "1.0.0",
        NAMESPACE + "." + phase + ".original-statistical-owner.v1",
        CapabilityKind.FALSIFIER if phase == "assess" else CapabilityKind.TRANSFORM if phase == "calibrate" else
            CapabilityKind.ANALYSIS if phase == "fit" else CapabilityKind.EXPERIMENT_DESIGNER,
        config_type, _stage(phase), inputs, outputs, tuple(sorted(permissions)), EvidenceCeiling.RESPONSE,
        _access(phase), VisibilityCeiling.DEVELOPMENT_ONLY if phase in ("fit", "model-freeze") else VisibilityCeiling.PROSPECTIVE,
        BUDGET, tuple(sorted(("exact-current-fit-freeze-forecast-outcome-receipts", "reserved-originals-before-train-decode",
            "complete-paired-root-statistics-and-retained-nonuse"))),
        _RunnerFactory(phase, publication_requirement, scientific_root_validator, outcome_task_id), codecs,
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=_units, scientific_operand_sha256s=_operands,
            scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(
            barrier=BarrierKind.FREEZE if _stage(phase) is ScientificStage.FREEZE else BarrierKind.NONE,
            runner_preparation_factory=prepare_for_invocation if phase == "fit" else None),
        publication_requirements=(publication_requirement,) if phase == "fit" else (),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))


def statistical_declarations(*, publication_requirement, scientific_root_validator, outcome_task_id):
    """Compose only with the real API publication/root/outcome owners supplied.

    The owning public resolver must authenticate actual originals before TRAIN
    is materialized/decoded. This factory neither runs nor substitutes that act.
    """
    if type(publication_requirement) is not RegisteredPublicationRequirement:
        raise TypeError("protected E3 composition requires its exact registered original-publication requirement")
    publication_requirement.__post_init__()
    for hook in (publication_requirement.validate, scientific_root_validator, outcome_task_id):
        _global_hook(hook)
    return tuple(_declaration(phase, publication_requirement, scientific_root_validator, outcome_task_id) for phase in PHASES)


def _current_dependency(context, edge, port, task, output):
    receipts = tuple(row for row in context.dependency_receipts if port.materialization_id in row.output_materialization_ids)
    if (port.kind is not WorkerInputKind.DEPENDENCY or len(receipts) != 1 or receipts[0].task_id != task
            or not matches_protected_e3_producer(edge, task, output)):
        raise ValueError("protected E3 statistic substitutes its actual current producer task/output/receipt")


def _input_name(phase, input_id):
    if phase in ("calibrate", "assess"):
        for name in ("forecasts", "outcomes"):
            if input_id.startswith(name + ".") and len(input_id) > len(name) + 1:
                return name
    return input_id


def _decode(context, phase, manifest):
    if type(context) is not TaskContext:
        raise TypeError("protected E3 statistics requires its actual prepared TaskContext")
    context.__post_init__()
    prepared = context.prepared_invocation
    if (type(prepared) is not PreparedInvocationContract or type(prepared.execution_task_record) is not ExecutionTask
            or prepared.manifest != manifest or prepared.native_effect or context.permissions != manifest.permissions
            or manifest.capability_key != NAMESPACE + "." + phase
            or not manifest.resource_ceiling.contains(context.resource_budget)
            or context.outcome_access is not _access(phase) or prepared.execution_task_record.stage is not _stage(phase)):
        raise ValueError("protected E3 statistic changes its prepared declaration/stage/access/resources")
    ports = {port.artifact_id: port for port in context.input_ports}
    contracts = {row.artifact_id: row for row in prepared.inputs}
    config_port = ports.get(context.config.artifact_id)
    config_kind = ProtectedE3FitConfig if phase == "fit" else ProtectedE3StatisticalConfig
    if (config_port is None or type(config_port) is not WorkerInputPort or config_port.kind is not WorkerInputKind.EXTERNAL
            or (config_port.payload_schema, config_port.media_type) != (config_kind.SCHEMA, MEDIA)
            or (context.config.config_schema, context.config.config_schema_sha256) != (manifest.config_schema, manifest.config_schema_sha256)):
        raise ValueError("protected E3 statistic loses its exact automatic configuration port")
    config = _read(config_port, contracts[config_port.artifact_id], config_kind)
    if (_phase(config) != phase or context.config.config_id != config.record_id
            or context.config.content_sha256 != config.fingerprint()
            or context.task_id != statistical_task_id(config.specification, config.allocation,
                config.operation, mode=config.mode, root=config.root)):
        raise ValueError("protected E3 statistic substitutes its frozen operation/root/configuration")
    allowed_access = (OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.DEVELOPMENT_VISIBLE, OutcomeAccess.EVALUATION_SEALED)
    if any(type(port) is not WorkerInputPort or port.outcome_access not in allowed_access
            or port.visibility_ceiling not in (VisibilityCeiling.PROSPECTIVE, VisibilityCeiling.DEVELOPMENT_ONLY) for port in context.input_ports):
        raise ValueError("protected E3 statistic receives revealed/privileged or unbound inputs")
    expected_access = derived_outcome_access(_access(phase), *(port.outcome_access for port in context.input_ports))
    ceiling = inherited_visibility(tuple(port.visibility_ceiling for port in context.input_ports), expected_access)
    expected_outputs = {"product": _product(phase)}
    if phase == "fit":
        expected_outputs["prefit-join"] = ProtectedE3PreFitJoin
    actual_outputs = {port.output_id.rsplit(".", 1)[-1]: port for port in context.output_ports}
    if (set(actual_outputs) != set(expected_outputs) or len(actual_outputs) != len(context.output_ports)
            or any(port.logical_artifact_id is None or (port.payload_schema, port.profile, port.media_type) !=
                (expected_outputs[name].SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA) for name, port in actual_outputs.items())
            or len({port.logical_artifact_id for port in context.output_ports}) != len(context.output_ports)
            or any(output.outcome_access is not expected_access or output.visibility_ceiling is not ceiling
                for output in prepared.execution_task_record.outputs)):
        raise ValueError("protected E3 statistic changes its actual compiled output lane or canonical contract")
    kinds = _ports(phase, confirmation=config.mode == "evaluation")
    edges = validated_scientific_input_edges(context, config_port=config_port)
    counts = Counter(_input_name(phase, edge.consumer_input_id) for edge in edges)
    if (set(counts) != set(kinds) or any(count != (dict(config.query_census)["calibration" if phase == "calibrate" else "evaluation"]
                if phase in ("calibrate", "assess") and name in ("forecasts", "outcomes") else 1) for name, count in counts.items())
            or len({edge.operational_logical_artifact_id for edge in edges}) != len(edges)
            or {edge.operational_logical_artifact_id for edge in edges} != set(ports) - {config_port.artifact_id}):
        raise ValueError("protected E3 statistic changes its complete scientific input/whole-unit edge census")
    records = {}
    for edge in edges:
        name, port = _input_name(phase, edge.consumer_input_id), ports[edge.operational_logical_artifact_id]
        if (port.payload_schema, port.media_type) != (kinds[name].SCHEMA, MEDIA):
            raise ValueError("protected E3 statistic changes an exact input type or encoding")
        external = name in ("specification", "allocation") or phase == "fit"
        if external and (port.kind is not WorkerInputKind.EXTERNAL or edge.producer_task_id is not None):
            raise ValueError("protected E3 statistic substitutes original external source metadata")
        # TRAIN bodies are deliberately unread until all reservation joins pass.
        value = None if phase == "fit" and name in ("features", "outcomes") else _read(port, contracts[port.artifact_id], kinds[name])
        if phase in ("calibrate", "assess") and name in ("forecasts", "outcomes"):
            if edge.consumer_input_id != name + "." + value.feature.public_source.root.root_id:
                raise ValueError("protected E3 statistic substitutes its exact per-root paired input edge")
        records.setdefault(name, []).append((value, port, edge))
    one = lambda name: records[name][0][0]
    specification, allocation = one("specification"), one("allocation")
    science._selected(specification, allocation)
    if (specification.identity != config.specification or allocation.identity != config.allocation
            or config.query_census != tuple((role, len(allocation.unit_ids(role))) for role in ("calibration", "evaluation"))):
        raise ValueError("protected E3 statistic substitutes its exact selected specification/allocation/census")
    return config, specification, allocation, records, contracts


def _fit(config, specification, allocation, records, contracts, result_id, *, context):
    one = lambda name: records[name][0][0]
    manifest, training = one("manifest"), one("training-allocation")
    if identity(manifest) != config.source_manifest or training.identity != config.training_allocation:
        raise ValueError("protected E3 fit changes its actual original manifest/training allocation")
    coordinates = manifest.reservation.allocation.coordinates
    by_temperature = {row.primary_view.bath_temperature: row for row in coordinates}
    inputs = ProtectedE3SourceInputs(specification, training, manifest.reservation, manifest.native_specification,
        by_temperature[Decimal(1)], by_temperature[Decimal("1.25")], by_temperature[Decimal(3)])
    if project_protected_e3_allocation(inputs) != allocation:
        raise ValueError("protected E3 fit substitutes original selected role projection")
    original_publications = {"allocation": manifest.reservation.publication,
        "native-selection": manifest.native_specification.publication, "reservation": manifest.reservation_publication}
    if any(publication != original_publications[key] for key, publication, _ in config.publications if key in original_publications):
        raise ValueError("protected E3 fit substitutes its actual original manifest publications")
    publications = tuple(E3RequiredPublication(key,
        one({"allocation": "original-allocation", "roles": "allocation"}.get(key, key)), publication, availability)
        for key, publication, availability in config.publications)
    original_ports = {key: records[{"allocation": "original-allocation", "roles": "allocation"}.get(key, key)][0][1]
        for key in PUBLICATION_KEYS}
    transports = e3_prepared_publication_transports(publications, context)
    joined = require_e3_reserved_fit_inputs(inputs, publications=publications, ports=original_ports,
        fit_cutoff=config.fit_cutoff, record_id=result_id + ".prefit-join", publication_transports=transports)
    banks = []
    for name, kind in (("features", exposed.MatrixE3FeatureBank), ("outcomes", exposed.MatrixE3OutcomeBank)):
        _, port, _ = records[name][0]
        if (port.outcome_access, port.visibility_ceiling) != (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("protected E3 fit relabels original exposed TRAIN payloads")
        banks.append(_read(port, contracts[port.artifact_id], kind))
    models = science.fit_protected_e3_models(inputs, joined, *banks, record_id=result_id)
    return models, joined


class ProtectedE3StatisticalRunner:
    def __init__(self, phase, manifest, outcome_task_id):
        if phase not in PHASES:
            raise ValueError("protected E3 statistic requires its declared operation")
        _global_hook(outcome_task_id)
        self.phase, self.manifest, self.outcome_task_id = phase, manifest, outcome_task_id

    def execute(self, context):
        from .protected_statistical_execution import StatisticalExecutionContract, execute_statistical
        return execute_statistical(self, context, StatisticalExecutionContract(
            _decode, _fit, science.freeze_protected_e3, science.forecast_protected_e3,
            science.calibrate_protected_e3, science.assess_protected_e3, science.identity,
            statistical_task_id, feature_task_id, _current_dependency))
