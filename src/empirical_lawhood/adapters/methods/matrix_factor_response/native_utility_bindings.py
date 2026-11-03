# SPDX-License-Identifier: MPL-2.0
"""Installed E2 acquisition over current source and actual native owners."""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from dataclasses import dataclass
from decimal import getcontext
from functools import lru_cache, partial
from hashlib import sha256
from typing import ClassVar
import numpy as np

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as sr, science as scheduled_science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.parameter_native import execute_parameter_native_work
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_bindings import execute_paired_response_native_work
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_array_preparation import NativeResponseArrayPreparation
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_forecast import array_product
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import (
    ScheduledResponsePanel, ScheduledResponseProtocol, branch_census, validate_response_native_evidence)
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner, RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork, PreparedInvocationContract
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, RegisteredPublicationRequirement
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties
from . import native_utility_records as r, native_utility_science as science
from .native_utility_records import NativeUtilitySourceManifest

from .native_acquisition_contracts import native_work_definition

BUDGET = ResourceBudget(1, None, 0, None, None, None)
DEV, EXPOSED = OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY


@dataclass(frozen=True, slots=True)
class NativeUtilityEntryConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/native-utility-entry-config"
    record_id: str
    specification: r.NativeUtilitySpecification
    request: r.NativeUtilityRequest

    def __post_init__(self):
        from .native_utility_acquisition import entry_task_id
        r.validate_request(self.specification, self.request)
        if self.specification.criterion is None:
            raise ValueError("native E2 entry requires the scientific utility criterion before native contact")
        if self.record_id != "config." + entry_task_id(self.specification):
            raise ValueError("native E2 entry changes complete declared acquisition identity")


@dataclass(frozen=True, slots=True)
class NativeUtilityOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/native-utility-operation-config"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    operation: str
    specification: ObjectIdentity
    request: ObjectIdentity
    source: ScheduledSource | None
    public_source: ScheduledPublicSource | None
    protocol: ObjectIdentity | None
    panels: tuple[ScheduledResponsePanel, ...]
    resource_budget: ResourceBudget
    producer_configurations: tuple[tuple[str, ObjectIdentity], ...] = ()
    assigned_unit_ids: tuple[str, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.record_id)
        r.exact_reference(self.specification, r.NativeUtilitySpecification)
        r.exact_reference(self.request, r.NativeUtilityRequest)
        if self.operation not in (*r.PHASES, "terminal") or type(self.resource_budget) is not ResourceBudget:
            raise ValueError("native E2 operation changes closed phase or explicit resource selection")
        if not BUDGET.contains(self.resource_budget):
            raise ValueError("native E2 task exceeds its installed numerical placement")
        public = self.operation in ("physical-forecast",)
        if self.operation == "terminal":
            if any(value is not None for value in (self.source, self.public_source, self.protocol)) or self.panels:
                raise ValueError("native E2 terminal cannot acquire or predict a private source")
        elif public:
            if type(self.public_source) is not ScheduledPublicSource or self.source is not None or self.panels:
                raise ValueError("native E2 causal consumers require seedless public operands only")
        elif type(self.source) is not ScheduledSource or self.public_source is not None:
            raise ValueError("native E2 source phases need one actual compact source")
        expected_producers = () if self.source is None or self.operation == "prefix" else (("prefix", "responses") if self.operation == "response-score" else ("prefix",))
        if tuple(name for name, _ in self.producer_configurations) != expected_producers:
            raise ValueError("native E2 loses actual planned native producer configurations")
        for _, value in self.producer_configurations:
            r.exact_reference(value, NativeUtilityOperationConfig)
        if self.operation == "terminal":
            if not self.assigned_unit_ids or self.assigned_unit_ids != tuple(sorted(set(self.assigned_unit_ids))):
                raise ValueError("native E2 terminal requires complete actual assigned unit census")
        elif self.assigned_unit_ids:
            raise ValueError("native E2 local operation cannot substitute a global unit census")
        needs_protocol = self.operation in ("physical-forecast", "responses", "response-score")
        if needs_protocol != (type(self.protocol) is ObjectIdentity):
            raise ValueError("native E2 operation changes its exact paired physical protocol")
        if self.protocol is not None:
            r.exact_reference(self.protocol, ScheduledResponseProtocol)
        if self.operation in ("responses", "response-score"):
            if tuple(sorted(value.role for value in self.panels)) != ("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE"):
                raise ValueError("native E2 future loses either declared panel")
        elif self.panels:
            raise ValueError("native E2 pre-future operation receives future-panel streams")


@dataclass(frozen=True, slots=True)
class _BoundConfiguration:
    wire: NativeUtilityOperationConfig
    protocol: ScheduledResponseProtocol

    def __post_init__(self):
        if ObjectIdentity.from_record(self.protocol.protocol_id, self.protocol) != self.wire.protocol:
            raise ValueError("native E2 shared protocol changes its actual compact configuration pin")

    def __getattr__(self, name):
        return getattr(self.wire, name)


INPUTS = {
    "entry": (),
    "prefix": ("specification", "source", "coordinate", "manifest", "acquisition", "provenance", "streams"),
    "numerical": ("specification", "manifest", "acquisition", "history", "history-arrays"),
    "measure": ("specification", "manifest", "acquisition", "history", "history-arrays", "numerical"),
    "check": ("specification", "manifest", "acquisition", "history", "history-arrays", "numerical", "witness", "diagnostic-arrays"),
    "project": ("specification", "manifest", "acquisition", "history", "history-arrays", "numerical", "witness", "diagnostic-arrays", "frames"),
    "physical-forecast": ("specification", "protocol", "acquisition", "causal", "causal-arrays", "templates"),
    "responses": ("specification", "source", "coordinate", "protocol", "manifest", "acquisition", "history", "history-arrays", "checkpoint", "causal", "physical", "physical-arrays", "provenance", "streams"),
    "response-score": ("specification", "protocol", "manifest", "acquisition", "history", "history-arrays", "causal", "physical", "physical-arrays", "responses", "response-arrays"),
    "terminal": ("specification", "acquisition", "outcomes",),
}
RECORDS = {"source": ScheduledSource, "coordinate": MatrixParameterCoordinate,
    "specification": r.NativeUtilitySpecification, "protocol": ScheduledResponseProtocol, "manifest": NativeUtilitySourceManifest,
    "acquisition": r.NativeUtilityAcquisitionSeal, "provenance": NumericalProducingProvenance,
    "history": r.NativeUtilityPrefixHistory, "checkpoint": sr.ScheduledCheckpoint,
    "numerical": r.NativeUtilityNumericalAssessment, "witness": r.NativeUtilityPrefixWitness,
    "frames": r.NativeUtilityFrameAssessment, "causal": r.NativeUtilityCausalPrefix,
    "physical": r.NativeUtilityPhysicalForecast, "responses": r.NativeUtilityResponse,
    "outcomes": r.NativeUtilityOutcome,
    "streams": MatrixHistorySeed}
PRODUCTS = {"entry": r.NativeUtilityAcquisitionSeal, "prefix": r.NativeUtilityPrefixHistory,
    "numerical": r.NativeUtilityNumericalAssessment, "measure": r.NativeUtilityPrefixWitness,
    "check": r.NativeUtilityFrameAssessment, "project": r.NativeUtilityCausalPrefix,
    "physical-forecast": r.NativeUtilityPhysicalForecast,
    "responses": r.NativeUtilityResponse, "response-score": r.NativeUtilityOutcome, "terminal": r.NativeUtilitySummary}
ARRAY_PHASES = ("prefix", "measure", "project", "physical-forecast", "responses")
NATIVE = ("prefix", "responses")
OWNERS = {"history": ("prefix", "product"), "history-arrays": ("prefix", "arrays"), "checkpoint": ("prefix", "checkpoint"),
    "numerical": ("numerical", "product"), "witness": ("measure", "product"), "diagnostic-arrays": ("measure", "arrays"),
    "frames": ("check", "product"), "causal": ("project", "product"), "causal-arrays": ("project", "arrays"),
    "physical": ("physical-forecast", "product"), "physical-arrays": ("physical-forecast", "arrays"),
    "responses": ("responses", "product"), "response-arrays": ("responses", "arrays")}


def stage(operation):
    return (ScientificStage.ACQUIRE if operation in NATIVE else ScientificStage.FALSIFY if operation in
        ("numerical", "check", "response-score") else ScientificStage.FREEZE if operation in ("entry", "physical-forecast")
        else ScientificStage.REPORT if operation == "terminal" else ScientificStage.TRANSFORM)


def config_phase(config):
    return "entry" if type(config) is NativeUtilityEntryConfig else config.operation


def units(config):
    if type(config) is NativeUtilityEntryConfig:
        return tuple(sorted(value.root.independent_group_id for value in config.request.source_manifest.reservation.allocation.roots))
    return config.assigned_unit_ids if config.operation == "terminal" else (config.public_source.root.independent_group_id
        if config.public_source is not None else config.source.root.root.independent_group_id,)


def operands(config):
    if type(config) is NativeUtilityEntryConfig:
        return tuple(sorted((config.specification.fingerprint(), config.request.fingerprint())))
    values = (config.specification, config.request)
    return tuple(sorted({value.object_fingerprint for value in values}))


def native_slots(config):
    return (config.operation + "." + config.source.root_id,)


_root_context_cache = None


def scientific_root_validator(config, context):
    """Check one immutable complete layout once; keep every local guard fresh."""
    from .native_utility_acquisition import contracts, development_root
    from empirical_lawhood.runtime.recursive_compiler import RecursiveScientificRootContext
    global _root_context_cache
    if type(context) is not RecursiveScientificRootContext:
        raise TypeError("native E2 requires its actual compiler scientific context")
    decimal = getcontext()
    signature = (decimal.prec, decimal.rounding, decimal.Emin, decimal.Emax, decimal.clamp, decimal.capitals,
        tuple(sorted((signal.__name__, enabled) for signal, enabled in decimal.traps.items())))
    key = context.config_inputs, context.external_inputs, context.links, context.root
    cached = _root_context_cache
    if cached is None or signature != cached[0] or any(left is not right for left, right in zip(key, cached[1], strict=True)):
        entries = tuple(row.record for row in context.config_inputs if type(row.record) is NativeUtilityEntryConfig)
        if len(entries) != 1:
            raise ValueError("native E2 needs one actual complete declared entry")
        entry, = entries
        configs, external, links, _, _ = contracts(entry.specification, entry.request)
        if (tuple((row.node_id, row.record) for row in context.config_inputs) != configs
                or tuple(context.external_inputs) != external or tuple(context.links) != links
                or context.root != development_root(entry.specification, entry.request, context.root.study_id)):
            raise ValueError("native E2 changes complete actual configuration/edge/source/root census")
        by_node, groups = dict(configs), units(entry)
        _root_context_cache = signature, key, by_node, groups
    else:
        by_node, groups = cached[2], cached[3]
    phase, node = config_phase(config), config.record_id.removeprefix("config.")
    if (by_node.get(node) != config or context.node_id != node or context.requirements or context.connections
            or context.stage is not stage(phase) or context.unit_ids != units(config)
            or context.selected_unit_ids != groups or context.complete_unit_census != (phase in NATIVE)
            or context.outcome_access is not DEV or context.visibility_ceiling is not EXPOSED):
        raise ValueError("native E2 changes current phase/roles/census or causal-before-future boundary")


@lru_cache(maxsize=1)
def operation_declarations():
    from .native_utility_publications import authenticate_utility_publications
    declarations = []
    codecs = {kind.SCHEMA: kind for kind in (NativeUtilityEntryConfig, NativeUtilityOperationConfig,
        *RECORDS.values(), *PRODUCTS.values(), r.NativeUtilityScore, sr.ScheduledCheckpoint)}
    for operation in r.ALL_PHASES:
        inputs = tuple(sorted((RecursivePortContract(name, RECORDS[name].SCHEMA if name in RECORDS else MATRIX_ARRAY_SCHEMA,
            "application/json" if name in RECORDS else "application/x-npz", None if name in RECORDS else MAXIMUM_MATRIX_ARRAY_BYTES,
            maximum_count=None if name in ("streams", "outcomes",) else 1) for name in INPUTS[operation]), key=lambda row: row.port_id))
        outputs = [OutputTemplate("product", PRODUCTS[operation].SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json")]
        if operation in ARRAY_PHASES:
            outputs.append(OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz"))
        if operation == "prefix":
            outputs.append(OutputTemplate("checkpoint", sr.ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"))
        if operation == "response-score":
            outputs.append(OutputTemplate("score", r.NativeUtilityScore.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"))
        selected_stage = stage(operation)
        kind = (CapabilityKind.SIMULATOR if operation in NATIVE else CapabilityKind.FALSIFIER if selected_stage is ScientificStage.FALSIFY
            else CapabilityKind.REPORTER if operation == "terminal" else CapabilityKind.TRANSFORM)
        declarations.append(RecursiveOperationDeclaration(r.NAMESPACE + "." + operation, "1.0.0",
            r.NAMESPACE + "." + operation + ".current-paired-native.v1", kind,
            NativeUtilityEntryConfig if operation == "entry" else NativeUtilityOperationConfig, selected_stage, inputs,
            tuple(sorted(outputs, key=lambda row: row.output_id)), tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_FROZEN_MODELS))),
            EvidenceCeiling.NON_PROMOTABLE, DEV, EXPOSED, BUDGET,
            ("actual-prior-e2-source-custody", "complete-paired-utility-nonuse-denominator", "frozen-e2-criterion-before-native-contact"),
            lambda operation=operation: native_runner(operation) if operation in NATIVE else NativeUtilityRunner(operation),
            codecs, scientific_hooks=RecursiveScientificHooks(scientific_root_validator=scientific_root_validator,
                scientific_unit_ids=units, scientific_operand_sha256s=operands,
                native_effect_slot_ids=native_slots if operation in NATIVE else None),
            execution_properties=RecursiveExecutionProperties(native_effect=operation in NATIVE, complete_unit_census=operation in NATIVE,
                native_work_preparer=prepare_native_work if operation in NATIVE else None,
                barrier=BarrierKind.FREEZE if operation in ("entry", "physical-forecast") else BarrierKind.NONE),
            publication_requirements=(RegisteredPublicationRequirement(r.NAMESPACE + ".prior-publications.v1",
                authenticate_utility_publications),) if operation == "entry" else (),
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS))
    return tuple(declarations)


@lru_cache(maxsize=1)
def _decode_shared_manifest(raw):
    """Reuse one exact immutable manifest, retaining every current input check.

    Parent projections and the worker read their authenticated ports afresh.
    Only canonical decoding is reused; changed bytes replace this bounded entry.
    """
    return decode_canonical_bytes(raw, NativeUtilitySourceManifest, maximum_bytes=len(raw))


def _decode(context, operation, manifest):
    from .native_utility_acquisition import entry_task_id, task_id, terminal_task_id
    if type(context) is not TaskContext or context.outcome_access is not DEV:
        raise ValueError("native E2 refuses foreign outcome access before reading inputs")
    prepared = context.prepared_invocation
    if (type(prepared) is not PreparedInvocationContract or prepared.manifest != manifest
            or context.permissions != manifest.permissions or prepared.execution_task_record.stage is not stage(operation)
            or prepared.native_effect != (operation in NATIVE)
            or context.config.config_schema_sha256 != manifest.config_schema_sha256):
        raise ValueError("native E2 requires its actual prepared invocation/permissions")
    prepared.validate_context(context)
    ports = {port.artifact_id: port for port in context.input_ports}
    config_port = ports.get(context.config.artifact_id)
    kind = NativeUtilityEntryConfig if operation == "entry" else NativeUtilityOperationConfig
    if config_port is None or config_port.kind is not WorkerInputKind.EXTERNAL or config_port.payload_schema != kind.SCHEMA:
        raise ValueError("native E2 omits actual immutable configuration")
    config = decode_canonical_bytes(config_port.read(), kind, maximum_bytes=config_port.size_bytes)
    if (context.config.content_sha256 != config.fingerprint() or context.config.config_id != config.record_id
            or context.config.config_schema != config.SCHEMA or config_phase(config) != operation
            or not BUDGET.contains(context.resource_budget)):
        raise ValueError("native E2 substitutes exact current configuration/resources")
    budget = config.request.resources.for_operation(operation) if operation == "entry" else config.resource_budget
    if context.resource_budget != budget:
        raise ValueError("native E2 changes explicit selected task budget")
    edges = validated_scientific_input_edges(context, config_port=config_port)
    if operation == "entry":
        if context.task_id != entry_task_id(config.specification) or len(ports) != 1 or edges:
            raise ValueError("native E2 entry changes its actual complete request task")
        return config, config.specification, None, {}, {}
    expected = set(INPUTS[operation]) - {"streams", "outcomes",}
    actual = {edge.consumer_input_id for edge in edges}
    if (actual - expected != {name for name in actual if name.startswith(("streams.", "outcomes."))}
            or not expected.issubset(actual) or len(actual) != len(edges)
            or {edge.operational_logical_artifact_id for edge in edges} != set(ports) - {config_port.artifact_id}):
        raise ValueError("native E2 loses exact scientific operand census")
    records, selected_ports = {}, {}
    for edge in edges:
        name = edge.consumer_input_id
        category = name.split(".", 1)[0]
        if category not in INPUTS[operation]:
            raise ValueError("native E2 receives undeclared information")
        port = ports[edge.operational_logical_artifact_id]
        selected_ports[name] = port
        if port.outcome_access not in (DEV, OutcomeAccess.OUTCOME_BLIND):
            raise ValueError("native E2 receives sealed or revealed foreign input")
        if category in ("specification", "source", "coordinate", "protocol", "manifest", "provenance", "streams", "templates"):
            if port.kind is not WorkerInputKind.EXTERNAL:
                raise ValueError("native E2 substitutes an external declared scientific operand")
        else:
            if port.kind is not WorkerInputKind.DEPENDENCY:
                raise ValueError("native E2 substitutes a current dependency with an asserted payload")
            if category == "acquisition":
                owner = entry_task_id(config.specification)
            elif category in ("outcomes",):
                owner = task_id(name.split(".", 1)[1], "response-score")
            else:
                owner = task_id(config.public_source.root.root_id if config.public_source is not None else config.source.root_id,
                    OWNERS[category][0])
            receipts = tuple(row for row in context.dependency_receipts if port.materialization_id in row.output_materialization_ids)
            if len(receipts) != 1 or receipts[0].task_id != owner:
                raise ValueError("native E2 loses exact actual producer receipt")
        if category in RECORDS:
            raw = port.read()
            record = (_decode_shared_manifest(raw) if category == "manifest" else
                decode_canonical_bytes(raw, RECORDS[category], maximum_bytes=port.size_bytes))
            records[name] = record
    specification = records["specification"]
    acquisition = records["acquisition"]
    if (specification.identity != config.specification or acquisition.specification != config.specification
            or acquisition.request != config.request):
        raise ValueError("native E2 substitutes current frozen E2 acquisition seal")
    expected_task = terminal_task_id(specification) if operation == "terminal" else task_id(
        config.public_source.root.root_id if config.public_source is not None else config.source.root_id, operation)
    if context.task_id != expected_task:
        raise ValueError("native E2 task changes actual root identity")
    source = None
    if config.source is not None:
        source_manifest = records["manifest"]
        index = ScheduledSourceIndex.from_shared(reservation=source_manifest.reservation,
            specification=source_manifest.native_specification, provenances=source_manifest.provenances)
        source = index.resolve(config.source)
        if (source.root.root.role.value != "DEVELOPMENT" or source.root_id not in specification.root_ids
                or acquisition.source_reservation != sr.identity(source.reservation)):
            raise ValueError("native E2 substitutes original reserved DEVELOPMENT source")
        if operation in ("prefix", "responses"):
            if records["source"] != config.source or records["coordinate"] != source.coordinate:
                raise ValueError("native E2 substitutes its direct compact source or coordinate")
            supplied = tuple(sorted((value for name, value in records.items() if name.startswith("streams.")),
                key=lambda value: (value.purpose, value.digest_sha256)))
            needed = (*source.root.streams, *(stream for panel in config.panels if panel.role == "INDEPENDENT_FUTURE" for stream in panel.streams))
            if supplied != tuple(sorted(needed, key=lambda value: (value.purpose, value.digest_sha256))) or records["provenance"] != source.provenance:
                raise ValueError("native E2 changes actual direct streams or producing provenance")
        if "history" in records:
            history = records["history"]
            history.validate_source(source)
            if (history.acquisition != acquisition.identity or history.native.definition.parent_contact.run_id != context.run_id
                    or history.configuration != dict(config.producer_configurations)["prefix"]):
                raise ValueError("native E2 replaces current-run prefix/native custody")
        if config.protocol is not None:
            records["protocol"].public_source.validate_source(source)
    if config.protocol is not None:
        config = _BoundConfiguration(config, records["protocol"])
        if config.public_source is not None and config.public_source != config.protocol.public_source:
            raise ValueError("native E2 public configuration changes actual shared protocol source")
    return config, specification, source, records, selected_ports


def _values(ports, name, owner):
    return decode_matrix_arrays(ports[name].read(), owner)


def _outputs(context, product, *, raw=None, checkpoint=None, score=None):
    ports = {port.output_id.rsplit(".", 1)[-1]: port for port in context.output_ports}
    values = {"product": product.canonical_bytes()}
    if raw is not None:
        if (ports["arrays"].logical_artifact_id != product.arrays.array_artifact.artifact_id
                or sha256(raw).hexdigest() != product.arrays.array_artifact.sha256):
            raise ValueError("native E2 changes its actual output array bytes")
        values["arrays"] = raw
    if checkpoint is not None:
        values["checkpoint"] = checkpoint.canonical_bytes()
    if score is not None:
        values["score"] = score.canonical_bytes()
    if set(values) != set(ports) or ports["product"].payload_schema != product.SCHEMA:
        raise ValueError("native E2 changes complete declared output census")
    return RunnerResult(tuple(sorted((TaskOutputPayload(ports[name].output_id, raw) for name, raw in values.items()),
        key=lambda value: value.output_id)), (ReceiptCheck("native-utility-current-custody-and-complete-census", True, ()),))


def _native_work(context, config, source, records, ports, expected_parent):
    if ((expected_parent.run_id, expected_parent.task_id, expected_parent.attempt_id, expected_parent.input_materialization_ids,
            expected_parent.dependency_receipt_ids, expected_parent.implementation_commit) !=
            (context.run_id, context.task_id, context.attempt_id, context.input_materialization_ids,
                context.dependency_receipt_ids, source.provenance.observed_git_head)):
        raise ValueError("native E2 changes its actual ordinary native parent")
    if expected_parent != context.prepared_invocation.expected_parent_contact:
        raise ValueError("native E2 changes its complete prepared parent plan or task")
    implementation = context.prepared_invocation.implementation
    if (source.provenance.package_sources, source.provenance.code_sources_sha256, source.provenance.dependency_lock_sha256,
            source.provenance.observed_git_head) != (implementation.package_sources, implementation.code_sources_sha256,
                implementation.dependency_lock_sha256, implementation.observed_git_head):
        raise ValueError("native E2 changes selected current producing source/dependency closure")
    definition = native_work_definition(config, source, records, expected_parent, context.input_materialization_ids)
    roster = NativeSubworkRoster("selected.native-subwork", expected_parent, (definition.identity,))
    return PreparedNativeWork(expected_parent, (source.root.root.independent_group_id,), native_slots(config), (definition,), (roster,)), None, None


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not NativeUtilityNativeRunner or runner.operation not in NATIVE:
        raise ValueError("native E2 preparation requires its exact installed native owner")
    config, _, source, records, ports = _decode(context, runner.operation, runner.manifest)
    return _native_work(context, config, source, records, ports, expected_parent)[0]


class NativeUtilityRunner:
    def __init__(self, operation):
        self.operation = operation
        self.manifest = next(value.manifest() for value in operation_declarations() if value.capability_key.endswith("." + operation))

    def execute(self, context):
        try:
            config, specification, source, records, ports = _decode(context, self.operation, self.manifest)
            if self.operation == "entry":
                return _outputs(context, r.acquisition_seal(specification, config.request))
            if self.operation == "terminal":
                outcomes = tuple(value for name, value in records.items() if name.startswith("outcomes."))
                if any(value.specification != specification.identity or value.acquisition != records["acquisition"].identity for value in outcomes):
                    raise ValueError("native E2 terminal changes frozen utility ancestry")
                return _outputs(context, science.summarize(specification, records["acquisition"], outcomes))
            arrays_port = next((port for port in context.output_ports if port.profile is ArtifactProfile.MATRIX_ARRAY_NPZ), None)
            artifact_id = None if arrays_port is None else arrays_port.logical_artifact_id
            if self.operation in NATIVE:
                raise ValueError("native E2 acquisition requires genuine existing native-subwork owner")
            if self.operation in ("physical-forecast",):
                causal = records["causal"]
                arrays = _values(ports, "causal-arrays", causal.arrays)
                templates = _values(ports, "templates", config.protocol.templates)
                raw, product = science.physical(config.protocol, causal, arrays, templates, artifact_id=artifact_id)
                return _outputs(context, product, raw=raw)
            history = records["history"]
            native = _values(ports, "history-arrays", history.arrays)
            if self.operation == "numerical":
                return _outputs(context, science.numerical(source, history, native))
            if self.operation == "measure":
                raw, product = science.measure(source, history, records["numerical"], native, artifact_id=artifact_id)
                return _outputs(context, product, raw=raw)
            if self.operation in ("check", "project"):
                witness = records["witness"]
                diagnostic = _values(ports, "diagnostic-arrays", witness.arrays)
                if self.operation == "check":
                    return _outputs(context, science.frames(source, history, records["numerical"], witness, native, diagnostic))
                raw, product = science.project(source, history, records["numerical"], witness, records["frames"], native,
                    diagnostic, artifact_id=artifact_id)
                return _outputs(context, product, raw=raw)
            responses, physical = records["responses"], records["physical"]
            validate_response_native_evidence(responses, source, config.specification, history, records["causal"], physical,
                records["acquisition"], configuration=dict(config.producer_configurations)["responses"],
                parent_task=context.task_id.removesuffix("response-score") + "responses", operation=r.NAMESPACE + ".paired-responses.v1",
                shared_sources=r.native_source_pins(source), panels=config.panels, protocol=config.protocol) if responses.native else responses.validate_nonentry(
                    records["causal"], physical, config.protocol, config.panels)
            score, outcome = science.score(specification, source, config.protocol, config.panels, records["acquisition"], history,
                records["causal"], physical, responses, native, _values(ports, "physical-arrays", physical.arrays),
                _values(ports, "response-arrays", responses.arrays))
            return _outputs(context, outcome, score=score)
        finally:
            for port in context.input_ports:
                port.close()


def _prepare_native_runner(context, *, operation):
    """Bind only the installed owner after the engine built its complete contract.

    This callback creates no issue, qualification or native entry. The ordinary
    engine then invokes the PURE work hook twice and child preflight rechecks it.
    """
    runner = NativeUtilityNativeRunner(operation)
    prepared = context.prepared_invocation
    if (type(prepared) is not PreparedInvocationContract or not prepared.native_effect
            or prepared.manifest != runner.manifest):
        raise ValueError("native E2 parent preparation requires its complete actual native invocation")
    prepared.validate_context(context)
    return runner


def native_runner(operation):
    """Use the existing staged parent route, retaining strict bound decoding."""
    if operation not in NATIVE:
        raise ValueError("native E2 parent selection requires an actual native phase")
    runner = NativeUtilityNativeRunner(operation)
    return ParentPreparedTaskRunner(runner.manifest, partial(_prepare_native_runner, operation=operation), native_effect=True)


class NativeUtilityNativeRunner(NativeUtilityRunner):
    def __init__(self, operation):
        super().__init__(operation)
        self._response_array_preparation = NativeResponseArrayPreparation()

    def preflight(self, context):
        if self.operation == "responses":
            config, _, source, records, ports = _decode(context, self.operation, self.manifest)
            self._response_array_preparation.prepare(context, source=source, history=records["history"].arrays,
                physical=records["physical"].arrays, ports=ports, protocol=config.protocol,
                physical_disposition=records["physical"].disposition)

    def _response_arrays(self, context):
        return self._response_array_preparation.arrays(context)

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, _, source, records, ports = _decode(context, self.operation, self.manifest)
            work, prefix, frozen = _native_work(context, config, source, records, ports, native_subwork.parent_contact)
            artifact_id = next(port.logical_artifact_id for port in context.output_ports if port.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            if self.operation == "prefix":
                raw, values, checkpoint, definition, completed = execute_parameter_native_work(source, work, native_subwork,
                    prefix_only=True, start=0, stop=source.policy.cutoff_tick, progress=progress)
                # Reuse the original exact native archive/member projection;
                # its actual emitted E2 operand has the explicit DEV lane.
                native_raw, operand = scheduled_science._array_product(source, values, role="PREFIX", artifact_id=artifact_id,
                    producers=(sr.identity(source), coordinate_identity(source.coordinate)), raw=raw)
                product = r.NativeUtilityPrefixHistory("history." + source.root_id, sr.identity(source), science.dev_arrays(operand),
                    checkpoint, sr.ScheduledNativeEvidence(definition, completed.completion, completed.receipt),
                    r.identity(config), records["acquisition"].identity)
                product.validate_source(source)
                return _outputs(context, product, raw=native_raw, checkpoint=checkpoint)
            history, causal, physical = (records[name] for name in ("history", "causal", "physical"))
            prefix, frozen = self._response_arrays(context)
            native = ()
            if physical.disposition != "AVAILABLE" or causal.disposition != "AVAILABLE":
                arrays = {"unentered_branches": np.arange(len(branch_census(config.protocol, config.panels)), dtype="<i8")}
                disposition = "NO_ORIGIN" if causal.disposition == "NO_ORIGIN" else "INSTRUMENT_UNRESOLVED" if physical.disposition == "INSTRUMENT_UNRESOLVED" else "UNEVALUABLE"
                raw = None
            else:
                raw, arrays, definition, completed = execute_paired_response_native_work(source, work, native_subwork,
                    protocol=config.protocol, panels=config.panels, history=history,
                    prefix=prefix, frozen=frozen,
                    selection=config.specification, progress=progress)
                native = (sr.ScheduledNativeEvidence(definition, completed.completion, completed.receipt),)
                disposition = "COMPLETED"
            raw, operand = array_product(config.protocol, arrays, role="RESPONSES", artifact_id=artifact_id,
                producers=(sr.identity(source), config.request, r.identity(physical), records["acquisition"].identity),
                access=DEV, visibility=EXPOSED, **({"raw": raw} if native else {}))
            product = r.NativeUtilityResponse("responses." + source.root_id, sr.identity(source), r.identity(causal),
                r.identity(physical), records["acquisition"].identity, ObjectIdentity.from_record(config.protocol.protocol_id, config.protocol),
                operand, tuple(value[0] for value in branch_census(config.protocol, config.panels)), native, disposition,
                () if native else ("complete-paired-branch-slots-not-entered-" + disposition.lower(),))
            if native:
                validate_response_native_evidence(product, source, config.specification, history, causal, physical, records["acquisition"],
                    configuration=r.identity(config), parent_task=context.task_id, operation=r.NAMESPACE + ".paired-responses.v1",
                    shared_sources=r.native_source_pins(source), panels=config.panels, protocol=config.protocol)
            else:
                product.validate_nonentry(causal, physical, config.protocol, config.panels)
            return _outputs(context, product, raw=raw)
        finally:
            self._response_array_preparation.clear()
            for port in context.input_ports:
                port.close()
