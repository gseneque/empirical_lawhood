# SPDX-License-Identifier: MPL-2.0
"""Closed truthful DEV32x9 graph; existing compiler/runtime own execution."""

from empirical_lawhood.kernel.decoding import validate_record_fields
from collections.abc import Mapping
from dataclasses import dataclass, replace
from functools import partial
from types import MappingProxyType
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, RecursiveScientificRootContext, RecursiveScientificRootPreparationContext
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveExecutionProperties, RecursiveScientificHooks

from . import selected_e3_e4_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import (
    MatrixE4SecondaryTarget, MatrixE4SecondaryReadoutSelection,
)
from .forecast import ScheduledPublicSource
from .operation_bindings import BUDGET
from .records import ScheduledCheckpoint
from .selected_native_source import source_transport, selected_native_operation, selected_native_source_operands, selected_stream_operands
from .response_records import ScheduledResponsePanel, ScheduledResponseProtocol, ScheduledResponseScore, ScheduledE4DenseMechanicalForecast, ScheduledE4DenseResponseScore
from .selected_e4_programme import _decimal_context_cache

NAMESPACE = r.NAMESPACE
PHASES = ("entry", "prefix", "numerical", "measure", "check", "project", "mechanical", "account",
    "continue", "full-numerical", "responses", "response-score", "collect", "reduce")
NATIVE = ("prefix", "continue", "responses")
ARRAY_OUTPUTS = ("prefix", "measure", "project", "mechanical", "continue", "responses")
WORLD = "world.matrix-selected-e3-e4.development"
QUESTION = "Retain every original scheduled DEV32x9 response and the three frozen selected E3 point accounts."
OUTPUTS = {"entry": r.SelectedE3E4EntrySeal, "prefix": r.SelectedE3E4PrefixHistory,
    "numerical": r.SelectedE3E4NumericalAssessment, "measure": r.SelectedE3E4Witness, "check": r.SelectedE3E4Frames,
    "project": r.SelectedE3E4CausalPrefix, "account": r.SelectedE3E4AccountSeal, "mechanical": r.SelectedE3E4MechanicalForecast,
    "continue": r.SelectedE3E4FullHistory, "full-numerical": r.SelectedE3E4NumericalAssessment,
    "responses": r.SelectedE3E4Responses, "response-score": ScheduledResponseScore, "collect": r.SelectedE3E4CaseResult,
    "reduce": r.SelectedE3E4DevelopmentReduction}
RECORDS = {"entry": r.SelectedE3E4EntrySeal, "source": r.SelectedE3E4NativeSourceReference, "evidence": r.SelectedE3E4Evidence,
    "design": r.SelectedE3E4ForecastDesign, "prefix": r.SelectedE3E4PrefixHistory, "checkpoint": ScheduledCheckpoint,
    "numerical": r.SelectedE3E4NumericalAssessment, "witness": r.SelectedE3E4Witness, "frames": r.SelectedE3E4Frames,
    "causal": r.SelectedE3E4CausalPrefix, "account": r.SelectedE3E4AccountSeal, "mechanical": r.SelectedE3E4MechanicalForecast,
    "full": r.SelectedE3E4FullHistory, "full-numerical": r.SelectedE3E4NumericalAssessment,
    "responses": r.SelectedE3E4Responses, "score": ScheduledResponseScore, "cases": r.SelectedE3E4CaseResult,
    "streams": MatrixHistorySeed}
INPUTS = {"entry": ("evidence",), "prefix": ("entry", "source", "streams"),
    "numerical": ("entry", "source", "prefix", "prefix-arrays"),
    "measure": ("entry", "source", "prefix", "prefix-arrays", "numerical"),
    "check": ("entry", "source", "prefix", "prefix-arrays", "numerical", "witness", "diagnostic-arrays"),
    "project": ("entry", "source", "prefix", "prefix-arrays", "numerical", "witness", "diagnostic-arrays", "frames"),
    "account": ("entry", "design", "causal", "causal-arrays", "witness", "diagnostic-arrays", "mechanical", "mechanical-arrays"),
    "mechanical": ("entry", "causal", "causal-arrays", "templates"),
    "continue": ("entry", "source", "streams", "prefix", "prefix-arrays", "checkpoint", "causal", "account", "mechanical"),
    "full-numerical": ("entry", "source", "full", "full-arrays"),
    "responses": ("entry", "source", "streams", "prefix", "prefix-arrays", "checkpoint", "causal", "account", "mechanical", "mechanical-arrays"),
    "response-score": ("entry", "source", "prefix", "prefix-arrays", "causal", "causal-arrays", "account", "mechanical",
        "mechanical-arrays", "responses", "response-arrays", "templates"),
    "collect": ("entry", "source", "prefix", "causal", "account", "mechanical", "full", "full-numerical", "responses", "score"),
    "reduce": ("entry", "cases")}


RECORDS.update({"secondary-target": MatrixE4SecondaryTarget,
    "secondary-readout": MatrixE4SecondaryReadoutSelection,
    "dense-mechanical": ScheduledE4DenseMechanicalForecast})
INPUTS["entry"] = (*INPUTS["entry"], "secondary-target")
INPUTS["mechanical"] = (*INPUTS["mechanical"], "secondary-target")
INPUTS["response-score"] = (*INPUTS["response-score"], "secondary-target", "secondary-readout",
    "dense-mechanical", "dense-mechanical-arrays")


RECORDS["provenance"] = NumericalProducingProvenance
INPUTS = {phase: tuple(names) + (("provenance",) if "source" in names else ())
    for phase, names in INPUTS.items()}


def global_node(programme, phase):
    return NAMESPACE + "." + phase + "." + programme.fingerprint()


def local_node(root_id, phase):
    return NAMESPACE + "." + root_id + "." + phase


@dataclass(frozen=True, slots=True)
class SelectedE3E4EntryConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/entry-config"
    VERSION: ClassVar[str] = "3.0.0"
    config_id: str
    programme: r.SelectedE3E4DevelopmentProgramme
    bank: r.SelectedE3E4DevelopmentBank
    evidence: ObjectIdentity
    evidence_size_bytes: int
    produced_input_parents: tuple[ArtifactLineageParent, ...]
    secondary_readout: MatrixE4SecondaryReadoutSelection
    phase: str = "entry"

    def __post_init__(self):
        if type(self.secondary_readout) is not MatrixE4SecondaryReadoutSelection:
            raise TypeError("E4 entry requires its actual pre-future target publication selection")
        validate_record_fields(self.secondary_readout)
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import validate_produced_input_parents
        from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
        validate_produced_input_parents(self.produced_input_parents)
        r.validate_development_bank(self.programme, self.bank)
        if self.secondary_readout.mathematical_protocol != self.bank.forecast_design.criterion_record.identity:
            raise ValueError("E4 entry changes its original response mathematics")
        package=self.bank.forecast_design.package
        originals={r.identity(package.models),r.identity(package.model_freeze),package.calibration,r.identity(package.calibrated_freeze)}
        receipts={value.identity for value in self.produced_input_parents
            if (value.identity.object_schema,value.identity.object_version)==(CanonicalTaskReceipt.SCHEMA,CanonicalTaskReceipt.VERSION)}
        if len(originals)!=4 or len(receipts)!=4 or {value.identity for value in self.produced_input_parents}!=originals|receipts:
            raise ValueError("selected E4 DEV entry changes its four actual original product/receipt parent census")
        r.exact_pin(self.evidence, r.SelectedE3E4Evidence)
        if (self.phase != "entry" or self.config_id != "config." + global_node(self.programme, self.phase)
                or type(self.evidence_size_bytes) is not int or self.evidence_size_bytes < 1):
            raise ValueError("selected E4 entry changes exact programme, original evidence or current phase")


@dataclass(frozen=True, slots=True)
class SelectedE3E4ReduceConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/reduce-config"
    config_id: str
    programme: r.SelectedE3E4DevelopmentProgramme
    phase: str = "reduce"

    def __post_init__(self):
        validate_record_fields(self.programme)
        if self.phase != "reduce" or self.config_id != "config." + global_node(self.programme, self.phase):
            raise ValueError("selected E4 reduction changes the complete original programme")


@dataclass(frozen=True, slots=True)
class SelectedE3E4Config(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/native-config"
    config_id: str
    programme: ObjectIdentity
    source: r.SelectedE3E4NativeSource
    protocol: ScheduledResponseProtocol
    panels: tuple[ScheduledResponsePanel, ...]
    response_selection: ObjectIdentity
    phase: str

    def __post_init__(self):
        if (type(self.source) is not r.SelectedE3E4NativeSource or self.programme != self.source.programme
                or self.phase not in PHASES or self.phase in ("entry", "reduce", "account", "mechanical")
                or self.config_id != "config." + local_node(self.source.root_id, self.phase)
                or self.protocol.public_source != self.source.public
                or tuple(sorted(value.role for value in self.panels)) != ("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")
                or any(value.independent_group_id != self.source.root.root.independent_group_id for value in self.panels)):
            raise ValueError("selected E4 local configuration changes exact original source/assay/current phase")
        validate_record_fields(self.source)
        validate_record_fields(self.protocol)
        for panel in self.panels:
            validate_record_fields(panel)



@dataclass(frozen=True, slots=True)
class SelectedE3E4CompactConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/compact-native-config"
    config_id: str
    programme: ObjectIdentity
    source: r.SelectedE3E4NativeSourceReference
    protocol: ScheduledResponseProtocol
    panels: tuple[ScheduledResponsePanel, ...]
    response_selection: ObjectIdentity
    phase: str

    def __post_init__(self):
        if (type(self.source) is not r.SelectedE3E4NativeSourceReference or self.programme != self.source.programme
                or self.phase not in PHASES or self.phase in ("entry", "reduce", "account", "mechanical")
                or self.config_id != "config." + local_node(self.source.root_id, self.phase)
                or self.protocol.public_source != self.source.public
                or tuple(sorted(value.role for value in self.panels)) != ("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")
                or any(value.independent_group_id != self.source.root.root.independent_group_id for value in self.panels)):
            raise ValueError("selected E4 local configuration changes exact original source/assay/current phase")
        validate_record_fields(self.source)
        validate_record_fields(self.protocol)
        for panel in self.panels:
            validate_record_fields(panel)


@dataclass(frozen=True, slots=True)
class SelectedE3E4PublicConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e3-e4/public-config"
    VERSION: ClassVar[str] = "2.0.0"
    config_id: str
    programme: ObjectIdentity
    public_source: ScheduledPublicSource
    protocol: ScheduledResponseProtocol
    phase: str

    secondary_readout: MatrixE4SecondaryReadoutSelection

    def __post_init__(self):
        if type(self.secondary_readout) is not MatrixE4SecondaryReadoutSelection:
            raise TypeError("E4 predictor requires its exact pre-future target publication selection")
        validate_record_fields(self.secondary_readout)
        if type(self.protocol) is not ScheduledResponseProtocol:
            raise TypeError("E4 predictor requires its exact original response protocol")
        if self.secondary_readout.mathematical_protocol != self.protocol.criterion:
            raise ValueError("E4 predictor changes the target's original response mathematics")
        if (type(self.public_source) is not ScheduledPublicSource or self.phase not in ("account", "mechanical")
                or self.protocol.public_source != self.public_source
                or self.public_source.root.role.value != "DEVELOPMENT"
                or self.config_id != "config." + local_node(self.public_source.root.root_id, self.phase)):
            raise ValueError("selected E4 predictor configuration substitutes its exact seedless original source")


def phase_of(config):
    if type(config) not in (SelectedE3E4EntryConfig, SelectedE3E4ReduceConfig, SelectedE3E4CompactConfig, SelectedE3E4PublicConfig):
        raise TypeError("selected E4 requires an exact installed owning configuration")
    validate_record_fields(config)
    return config.phase


def task_id(config):
    phase_of(config)
    return config.config_id.removeprefix("config.")


def units(config):
    if type(config) in (SelectedE3E4EntryConfig, SelectedE3E4ReduceConfig):
        return config.programme.group_ids
    return ((config.source.root.root.independent_group_id,) if type(config) is SelectedE3E4CompactConfig
        else (config.public_source.root.independent_group_id,))


def stage(phase):
    return (ScientificStage.ACQUIRE if phase in NATIVE else ScientificStage.FREEZE if phase in ("entry", "account", "mechanical")
        else ScientificStage.FALSIFY if phase in ("numerical", "check", "full-numerical", "response-score", "reduce")
        else ScientificStage.TRANSFORM)


def native_contract(config, source, *, recorded_operation=None):
    if type(config) is not SelectedE3E4CompactConfig or config.source != source_transport(source) or config.phase not in NATIVE:
        raise ValueError("selected E4 native work requires exact current local configuration")
    operation, _ = selected_native_operation(NAMESPACE, config.phase, recorded_operation=recorded_operation)
    sources = selected_native_source_operands(source)
    return ObjectIdentity.from_record(config.config_id, config), config.config_id.removeprefix("config."), operation, tuple(sorted(sources, key=lambda value: value.object_id))


def digests(config):
    if type(config) in (SelectedE3E4EntryConfig, SelectedE3E4ReduceConfig):
        return tuple(sorted((config.programme.fingerprint(), config.secondary_readout.fingerprint(), config.secondary_readout.target.object_fingerprint))) if type(config) is SelectedE3E4EntryConfig else (config.programme.fingerprint(),)
    values = {config.programme.object_fingerprint, config.protocol.fingerprint()}
    if type(config) is SelectedE3E4CompactConfig:
        values.update((config.source.fingerprint(), config.source.reference.identity.object_fingerprint,
            config.source.provenance.object_fingerprint, config.response_selection.object_fingerprint))
        values.update(panel.fingerprint() for panel in config.panels)
    else:
        values.update((config.public_source.fingerprint(), config.secondary_readout.fingerprint(),
            config.secondary_readout.target.object_fingerprint))
    return tuple(sorted(values))


def slots(config):
    return (config.phase + "." + config.source.root_id,)


@dataclass(frozen=True, slots=True)
class _Factory:
    phase: str

    def __call__(self):
        from .selected_e3_e4_workers import SelectedE3E4Worker
        declaration = next(row for row in operation_declarations() if row.capability_key == NAMESPACE + "." + self.phase)
        return SelectedE3E4Worker(self.phase, declaration.manifest())


def prepare_for_invocation(supplier, runner):
    callback = getattr(supplier, "prepare_selected_e3_e4_development", None)
    if not callable(callback):
        raise PermissionError("selected E4 development requires actual authored custody and original E3 producer admission")
    return ParentPreparedTaskRunner(runner.manifest, partial(callback, runner=runner), native_effect=runner.phase in NATIVE)


def prepare_native_work(*, runner, context, expected_parent):
    return runner.prepare_native_work(context, expected_parent=expected_parent)


def config_input_parents(config, all_config_records):
    """Project intrinsic configuration custody from the complete frozen census."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_record_parents

    from bisect import bisect_left

    if type(all_config_records) is not tuple:
        raise TypeError('selected E4 configuration custody requires its complete typed node census')
    if type(config) not in (SelectedE3E4EntryConfig, SelectedE3E4ReduceConfig,
            SelectedE3E4CompactConfig, SelectedE3E4PublicConfig):
        raise TypeError('selected E4 configuration custody changes its exact configuration owner')
    programme = config.programme
    digest = programme.object_fingerprint if type(programme) is ObjectIdentity else programme.fingerprint()
    entry_node = NAMESPACE + '.entry.' + digest
    position = bisect_left(all_config_records, entry_node, key=lambda row: row[0])
    if (position == len(all_config_records) or all_config_records[position][0] != entry_node
            or type(all_config_records[position][1]) is not SelectedE3E4EntryConfig):
        raise ValueError('selected E4 configuration custody lacks its one actual whole-programme entry')
    entry = all_config_records[position][1]
    return produced_record_parents(config, entry.produced_input_parents)


def operation_declarations():
    kinds = (*RECORDS.values(), *OUTPUTS.values(), ScheduledE4DenseResponseScore, SelectedE3E4EntryConfig, SelectedE3E4ReduceConfig, SelectedE3E4CompactConfig, SelectedE3E4PublicConfig)
    kinds = (*kinds, r.SelectedE3E4NativeSource, SelectedE3E4Config)
    codecs = {kind.SCHEMA: kind for kind in kinds}
    rows = []
    for phase in PHASES:
        ports = tuple(sorted((RecursivePortContract(name, MATRIX_ARRAY_SCHEMA if (kind := RECORDS.get(name)) is None else kind.SCHEMA,
            "application/x-npz" if kind is None else "application/json", MAXIMUM_MATRIX_ARRAY_BYTES if kind is None else None,
            minimum_count=(8 if phase == "responses" else 4) if name == "streams" else 1, maximum_count=(8 if phase == "responses" else 4) if name == "streams" else None if name == "cases" else 1)
            for name in INPUTS[phase]), key=lambda value: value.port_id))
        outputs = [OutputTemplate("product", OUTPUTS[phase].SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json")]
        if phase == "mechanical":
            outputs.extend((OutputTemplate("dense-product", ScheduledE4DenseMechanicalForecast.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
                OutputTemplate("dense-arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz")))
        if phase == "response-score":
            outputs.append(OutputTemplate("dense-score", ScheduledE4DenseResponseScore.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, "application/json", ".json"))
        if phase in ARRAY_OUTPUTS:
            outputs.append(OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz"))
        if phase == "prefix":
            outputs.append(OutputTemplate("checkpoint", ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"))
        kind = (SelectedE3E4EntryConfig if phase == "entry" else SelectedE3E4ReduceConfig if phase == "reduce"
            else SelectedE3E4PublicConfig if phase in ("account", "mechanical") else SelectedE3E4CompactConfig)
        rows.append(RecursiveOperationDeclaration(NAMESPACE + "." + phase, "3.0.0" if phase in NATIVE or phase in ("response-score", "account") else "2.0.0" if phase in ("entry", "phase-entry", "account", "mechanical") or "source" in INPUTS[phase] else "1.0.0",
            NAMESPACE + "." + phase + (".direct-operands.v3" if phase in NATIVE else ".matched-causal.v3" if phase == "account" else ".dense-e4.v3" if phase == "response-score" else ".dense-e4.v2" if phase in ("entry", "phase-entry", "account", "mechanical") else ".provenance-reference.v2" if "source" in INPUTS[phase] else ".original-science.v1"),
            CapabilityKind.SIMULATOR if phase in NATIVE else CapabilityKind.FALSIFIER if stage(phase) is ScientificStage.FALSIFY else CapabilityKind.TRANSFORM,
            kind, stage(phase), ports, tuple(sorted(outputs, key=lambda value: value.output_id)),
            tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_FROZEN_MODELS))),
            EvidenceCeiling.NON_PROMOTABLE, r.DEV, r.EXPOSED, BUDGET,
            ("actual-parent-original-product-custody", "selected-e3-primary-point-only", "whole32x9-original-scheduled-dev"),
            _Factory(phase), codecs,
            scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=units,
                scientific_operand_sha256s=digests,
                native_effect_slot_ids=slots if phase in NATIVE else None,
                scientific_root_validator=scientific_root_validator,
                scientific_root_preparer=scientific_root_preparer),
            execution_properties=RecursiveExecutionProperties(native_effect=phase in NATIVE, complete_unit_census=phase in NATIVE,
                native_work_preparer=prepare_native_work if phase in NATIVE else None, runner_preparation_factory=prepare_for_invocation,
                barrier=BarrierKind.FREEZE if stage(phase) is ScientificStage.FREEZE else BarrierKind.NONE),
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS,
            config_input_parents=config_input_parents))
    return tuple(sorted(rows, key=lambda row: row.capability_key))


@_decimal_context_cache
def contracts(programme, bank, evidence_pin, evidence_size, *, produced_input_parents, secondary_readout, secondary_target=None, direct_operands=True):
    r.validate_development_bank(programme, bank)
    if type(secondary_readout) is not MatrixE4SecondaryReadoutSelection:
        raise TypeError("E4 lowering requires its actual frozen target publication selection")
    validate_record_fields(secondary_readout)
    if secondary_readout.mathematical_protocol != bank.forecast_design.criterion_record.identity:
        raise ValueError("E4 lowering substitutes original response mathematics")
    if secondary_target is not None:
        secondary_readout.validate_target(secondary_target)
        for protocol in bank.response_selection.protocols:
            secondary_target.validate_protocol(protocol)
    configs, external, records, arrays, links = {}, {}, {}, {}, []
    def add(name, value, object_id):
        row = RecursiveExternalInput(name, object_id, value.SCHEMA, "application/json", len(value.canonical_bytes()),
            r.DEV, r.EXPOSED, value.fingerprint(), "SOURCE")
        if external.setdefault(name, row) != row or records.setdefault(name, value) != value:
            raise ValueError("selected E4 aliases distinct original scientific bytes")
        return name
    def array(artifact):
        name = "external.selected-e4-array." + artifact.fingerprint()
        row = RecursiveExternalInput(name, artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.size_bytes,
            r.DEV, r.EXPOSED, artifact.sha256, "SOURCE")
        if external.setdefault(name, row) != row or arrays.setdefault(name, artifact) != artifact:
            raise ValueError("selected E4 aliases distinct original array custody")
        return name
    def edge(node, port, *, external_id=None, producer=None, output="product"):
        links.append(RecursiveInputLink("edge." + node + "." + port, node, port, external_input_id=external_id,
            producer_node_id=producer, producer_output_id=output if producer is not None else None,
            scientific_role="SOURCE" if producer is None else "HISTORY"))
    entry, final = (global_node(programme, phase) for phase in ("entry", "reduce"))
    configs[entry] = SelectedE3E4EntryConfig("config." + entry, programme, bank, evidence_pin, evidence_size, produced_input_parents, secondary_readout)
    configs[final] = SelectedE3E4ReduceConfig("config." + final, programme)
    evidence_id = "external.selected-e4-evidence." + evidence_pin.object_fingerprint
    external[evidence_id] = RecursiveExternalInput(evidence_id, evidence_pin.object_id, evidence_pin.object_schema, "application/json",
        evidence_size, r.DEV, r.EXPOSED, evidence_pin.object_fingerprint, "SOURCE")
    edge(entry, "evidence", external_id=evidence_id)
    target_pin = secondary_readout.target
    target_id = "external.selected-e4-secondary-target." + target_pin.object_fingerprint
    external[target_id] = RecursiveExternalInput(target_id, target_pin.object_id, target_pin.object_schema,
        "application/json", secondary_readout.publication.materialization.size_bytes,
        r.DEV, r.EXPOSED, target_pin.object_fingerprint, "SOURCE")
    if secondary_target is not None:
        records[target_id] = secondary_target
    selection_id = add("external.selected-e4-secondary-readout." + secondary_readout.fingerprint(),
        secondary_readout, secondary_readout.record_id)
    edge(entry, "secondary-target", external_id=target_id)
    design = add("external.selected-e4-design." + bank.forecast_design.fingerprint(), bank.forecast_design, bank.forecast_design.record_id)
    source_index=bank.source_index()
    for descriptor in bank.sources:
        source = r.SelectedE3E4NativeSourceReference.from_bank(programme,bank,descriptor,index=source_index)
        protocol = next(value for value in bank.response_selection.protocols if value.public_source.root.root_id == source.root_id)
        panels = dict(bank.response_selection.panels)[source.root.root.independent_group_id]
        source_id = add("external.selected-e4-source." + source.fingerprint(), source, source.record_id)
        provenance = next(value for value in bank.provenances if value.identity == source.provenance)
        provenance_id = add("external.selected-e4-provenance." + provenance.fingerprint(), provenance, "selected-e4.provenance." + provenance.fingerprint())
        streams = tuple(add("external.selected-e4-stream." + pin.object_id, value, pin.object_id)
            for pin, value in selected_stream_operands(source, panels, include_future=direct_operands))
        templates = array(protocol.templates.array_artifact)
        nodes = {phase: local_node(source.root_id, phase) for phase in PHASES if phase not in ("entry", "reduce")}
        produced = {"entry": (entry, "product"), "prefix": (nodes["prefix"], "product"), "prefix-arrays": (nodes["prefix"], "arrays"),
            "checkpoint": (nodes["prefix"], "checkpoint"), "numerical": (nodes["numerical"], "product"),
            "witness": (nodes["measure"], "product"), "diagnostic-arrays": (nodes["measure"], "arrays"), "frames": (nodes["check"], "product"),
            "causal": (nodes["project"], "product"), "causal-arrays": (nodes["project"], "arrays"),
            "account": (nodes["account"], "product"), "mechanical": (nodes["mechanical"], "product"),
            "mechanical-arrays": (nodes["mechanical"], "arrays"), "dense-mechanical": (nodes["mechanical"], "dense-product"),
            "dense-mechanical-arrays": (nodes["mechanical"], "dense-arrays"), "full": (nodes["continue"], "product"), "full-arrays": (nodes["continue"], "arrays"),
            "full-numerical": (nodes["full-numerical"], "product"), "responses": (nodes["responses"], "product"),
            "response-arrays": (nodes["responses"], "arrays"), "score": (nodes["response-score"], "product")}
        for phase, node in nodes.items():
            configs[node] = (SelectedE3E4PublicConfig("config." + node, programme.identity, source.public, protocol, phase, secondary_readout)
                if phase in ("account", "mechanical") else SelectedE3E4CompactConfig("config." + node, programme.identity, source,
                    protocol, panels, bank.response_selection.identity, phase))
            names=INPUTS[phase]
            if not direct_operands and phase=="responses":
                names=tuple(name for name in names if name!="checkpoint")
            for name in names:
                if name == "streams":
                    for index, stream in enumerate(streams if phase == "responses" else streams[:4]):
                        edge(node, "streams." + str(index), external_id=stream)
                elif name in ("source", "design", "templates", "provenance", "secondary-target", "secondary-readout"):
                    edge(node, name, external_id={"source": source_id, "design": design, "templates": templates, "provenance": provenance_id, "secondary-target": target_id, "secondary-readout": selection_id}[name])
                else:
                    producer, output = produced[name]
                    edge(node, name, producer=producer, output=output)
        edge(final, "cases." + source.root_id, producer=nodes["collect"])
    edge(final, "entry", producer=entry)
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import inherit_external_inputs
    inherited = inherit_external_inputs(tuple(external.values()), tuple(records.items()), produced_input_parents)
    return (tuple(sorted(configs.items())), tuple(sorted(inherited, key=lambda value: value.input_id)),
        tuple(sorted(links, key=lambda value: value.edge_id)), tuple(sorted(records.items())), tuple(sorted(arrays.items())))


@_decimal_context_cache
def development_root(programme, bank, study_id, *, produced_input_parents, secondary_readout):
    # The root names both original scientific subjects and their exact bounded
    # transports. A transport projection never substitutes for its subject.
    operands = {programme.identity, programme.bank, programme.forecast_design,
        programme.reservation, programme.allocation, programme.specification,
        programme.response_selection, programme.criterion, *programme.source_census}
    if type(secondary_readout) is not MatrixE4SecondaryReadoutSelection:
        raise TypeError("E4 development root requires its exact frozen target selection")
    validate_record_fields(secondary_readout)
    operands.update((secondary_readout.identity, secondary_readout.target))
    operands.update(value.identity for value in produced_input_parents)
    index=bank.source_index()
    for descriptor in bank.sources:
        source = r.SelectedE3E4NativeSourceReference.from_bank(programme,bank,descriptor,index=index)
        operands.update((source.identity, source.reference.identity, source.provenance,
            ObjectIdentity.from_record("public." + source.root_id, source.public)))
    operands.update(ObjectIdentity.from_record(protocol.protocol_id, protocol)
        for protocol in bank.response_selection.protocols)
    operands.update(ObjectIdentity.from_record(panel.panel_id, panel)
        for _, panels in bank.response_selection.panels for panel in panels)
    ordered = tuple(sorted(operands, key=lambda value: value.object_id))
    if len({value.object_id for value in ordered}) != len(ordered):
        raise ValueError("selected E4 scientific operands alias distinct original identities")
    views = tuple(sorted({view.view_id for coordinate in bank.reservation.allocation.coordinates
        for view in (coordinate.primary_view, coordinate.fine_view)}))
    claim = ClaimSpec("claim." + study_id, WORLD, "population.selected-e4-development", QUESTION,
        f"All{len(programme.group_ids)} declared original independent groups, every declared factorial coordinate and all paired30 assay endpoints.",
        "unit.original-whole-group", None, EvidenceCeiling.NON_PROMOTABLE, r.DEV, r.EXPOSED,
        "Exposed development and original selected point error only; no protected admission, calibration or transfer qualification.",
        ("assumption.selected-e4.original-scheduled-physics",), numerical_view_ids=views)
    return DevelopmentStudySpec(study_id, QUESTION, programme.identity, WORLD, WorldKind.NUMERICAL_SIMULATOR,
        programme.group_ids, views, (claim,), ordered)


@dataclass(frozen=True, slots=True, eq=False)
class SelectedE3E4ScientificPreparation:
    """One invocation's validated scientific graph, never access authority."""

    batch: RecursiveScientificRootPreparationContext
    node_configs: Mapping[str, CanonicalRecord]
    entry: SelectedE3E4EntryConfig
    group_ids: tuple[str, ...]
    selected_units_by_phase: Mapping[str, tuple[str, ...]]


def scientific_root_preparer(batch):
    if type(batch) is not RecursiveScientificRootPreparationContext or type(batch.root) is not DevelopmentStudySpec:
        raise TypeError("selected E4 acquisition requires its actual truthful development root")
    entries = tuple(value.record for value in batch.config_inputs if type(value.record) is SelectedE3E4EntryConfig)
    if len(entries) != 1:
        raise ValueError("selected E4 requires one complete whole-programme entry")
    entry, = entries
    configs, external, links, _, _ = contracts(entry.programme, entry.bank, entry.evidence, entry.evidence_size_bytes,
        produced_input_parents=entry.produced_input_parents, secondary_readout=entry.secondary_readout)
    if (tuple((value.node_id, value.record) for value in batch.config_inputs) != configs
            or batch.external_inputs != external or batch.links != links
            or batch.root != development_root(entry.programme, entry.bank, batch.root.study_id,
                produced_input_parents=entry.produced_input_parents, secondary_readout=entry.secondary_readout)):
        raise ValueError("selected E4 acquisition changes complete original graph/census/point-before-future or truthful DEV lane")
    group_ids = entry.programme.group_ids
    selection_ids = {value.capability_key.removeprefix(NAMESPACE + "."): value.registration().selection.selection_id
        for value in operation_declarations()}
    if (set(selection_ids) != set(PHASES)
            or set(batch.selected_unit_ids_by_selection) != set(selection_ids.values())):
        raise ValueError("selected E4 acquisition changes its complete declared phase-selection census")
    selected_units_by_phase = {phase: batch.selected_unit_ids_by_selection[selection_id]
        for phase, selection_id in selection_ids.items()}
    if any(value != group_ids for value in selected_units_by_phase.values()):
        raise ValueError("selected E4 acquisition changes its complete selected whole-group census")
    return SelectedE3E4ScientificPreparation(batch,
        MappingProxyType({value.node_id: value.record for value in batch.config_inputs}), entry, group_ids,
        MappingProxyType(selected_units_by_phase))


def scientific_root_validator(config, context):
    if type(context) is not RecursiveScientificRootContext:
        raise TypeError("selected E4 acquisition requires its actual truthful development root")
    prepared = context.scientific_preparation
    if type(prepared) is not SelectedE3E4ScientificPreparation:
        raise TypeError("selected E4 acquisition requires its exact invocation's scientific preparation")
    batch = prepared.batch
    if (context.root is not batch.root or context.config_inputs is not batch.config_inputs
            or context.links is not batch.links or context.external_inputs is not batch.external_inputs
            or context.requirements is not batch.requirements or context.connections is not batch.connections
            or context.qualifications is not batch.qualifications or context.known_design_inputs is not batch.known_design_inputs
            or prepared.node_configs.get(context.node_id) is not config):
        raise ValueError("selected E4 acquisition changes its prepared invocation or exact selected configuration")
    # The whole contract comparison already validated every owning config. Do
    # not rerun an entry's complete bank/programme validation at each node.
    phase, node = config.phase, config.config_id.removeprefix("config.")
    expected_units = prepared.group_ids if type(config) in (SelectedE3E4EntryConfig, SelectedE3E4ReduceConfig) else units(config)
    if (context.node_id != node or context.stage is not stage(phase) or context.unit_ids != expected_units
            or context.selected_unit_ids is not prepared.selected_units_by_phase.get(phase)
            or context.complete_unit_census != (phase in NATIVE) or context.outcome_access is not r.DEV or context.visibility_ceiling is not r.EXPOSED):
        raise ValueError("selected E4 acquisition changes complete original graph/census/point-before-future or truthful DEV lane")


@dataclass(frozen=True, slots=True)
class LoweredSelectedE3E4:
    draft: RecursiveStudyDraft
    input_records: tuple
    input_artifacts: tuple


def operational_tasks(programme, bank, *, evidence):
    """Derive the complete selected task/phase projection before budget choice.

    This is an operational selection surface, never a scientific resource
    ceiling or a claim about the memory required by actual native work.
    """
    r.validate_evidence(evidence, programme, bank)
    rows = [(global_node(programme, phase), phase) for phase in ("entry", "reduce")]
    rows.extend((local_node(case.root_id, phase), phase) for case in programme.cases
        for phase in PHASES if phase not in ("entry", "reduce"))
    return tuple(sorted(rows))


def _selected_operational_budgets(tasks, operational_budgets):
    if not isinstance(operational_budgets, Mapping):
        raise TypeError("selected E4 requires an explicit operational budget mapping")
    selected = dict(operational_budgets)
    if set(selected) != {node for node, _ in tasks}:
        raise ValueError("selected E4 operational budgets change the complete task census")
    if any(type(value) is not ResourceBudget or not BUDGET.contains(value) for value in selected.values()):
        raise ValueError("selected E4 operational budget exceeds its registered capability ceiling")
    for value in selected.values():
        validate_record_fields(value)
    return selected


def lower_selected_e3_e4_development(programme, bank, *, evidence, campaign, draft_id, operational_budgets, secondary_target, secondary_readout):
    r.validate_evidence(evidence, programme, bank)
    secondary_readout.validate_target(secondary_target)
    configs, external, links, records, arrays = contracts(programme, bank, evidence.identity, len(evidence.canonical_bytes()),
        produced_input_parents=evidence.produced_input_parents, secondary_readout=secondary_readout, secondary_target=secondary_target)
    records = tuple(sorted((*records, ("external.selected-e4-evidence." + evidence.fingerprint(), evidence))))
    tasks = tuple((node, phase_of(config)) for node, config in configs)
    selected = _selected_operational_budgets(tasks, operational_budgets)
    selections = {value.capability_key.rsplit(".", 1)[-1]: value.registration().selection for value in operation_declarations()}
    operations = tuple(RecursiveOperationSpec.from_config(node_id=node, selection=selections[phase],
        config_id=config.config_id, config=config, obligation_ids=("obligation." + node,), resource_budget=selected[node])
        for (node, config), (_, phase) in zip(configs, tasks, strict=True))
    study = development_root(programme, bank, "study." + draft_id, produced_input_parents=evidence.produced_input_parents, secondary_readout=secondary_readout)
    campaign = replace(campaign, objective=QUESTION, system_ids=(programme.programme_id,), world_ids=(WORLD,),
        target_claim_ids=tuple(value.claim_id for value in study.claims))
    draft = RecursiveStudyDraft(draft_id, QUESTION, campaign, (), (), (), operations, external, links,
        tuple(node for node, _ in configs), development_study=study)
    return LoweredSelectedE3E4(draft, records, arrays)
