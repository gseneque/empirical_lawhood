# SPDX-License-Identifier: MPL-2.0
"""Closed truthful DEV32x9 graph; existing compiler/runtime own execution."""

from dataclasses import dataclass, fields, replace
from decimal import Decimal
from functools import lru_cache, partial
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorAction, MatrixFactorResponseModel
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixOriginResponseModel
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, RecursiveScientificRootContext
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveExecutionProperties, RecursiveScientificHooks

from . import selected_e4_native_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import (
    MatrixE4SecondaryTarget, MatrixE4SecondaryReadoutSelection,
)
from .forecast import ScheduledPublicSource
from . import selected_e4_programme as p
from .selected_e3_e4_records import SelectedE3E4ForecastDesign
from .operation_bindings import BUDGET
from .records import ScheduledCheckpoint
from .selected_native_source import source_transport, selected_native_operation, selected_native_source_operands, selected_stream_operands
from .response_records import ScheduledResponseArrays, ScheduledResponsePanel, ScheduledResponseProtocol, ScheduledResponseScore, ScheduledE4DenseMechanicalForecast, ScheduledE4DenseResponseScore

NAMESPACE = r.NAMESPACE
PHASES = ("entry", "prefix", "numerical", "measure", "check", "project", "mechanical", "account",
    "continue", "full-numerical", "responses", "response-score", "collect", "reduce")
NATIVE = ("prefix", "continue", "responses")
EXTRAS=("phase-entry","phase-collect","adjudicate")
ARRAY_OUTPUTS = ("prefix", "measure", "project", "mechanical", "continue", "responses")
WORLD = "world.matrix-selected-e4.protected"
QUESTION = "Retain every original scheduled DEV32x9 response and the three frozen selected E3 point accounts."
OUTPUTS = {"entry": r.SelectedE4ProtectedEntrySeal, "prefix": r.SelectedE4ProtectedPrefixHistory,
    "numerical": r.SelectedE4ProtectedNumericalAssessment, "measure": r.SelectedE4ProtectedWitness, "check": r.SelectedE4ProtectedFrames,
    "project": r.SelectedE4ProtectedCausalPrefix, "account": r.SelectedE4ProtectedAccountSeal, "mechanical": r.SelectedE4ProtectedMechanicalForecast,
    "continue": r.SelectedE4ProtectedFullHistory, "full-numerical": r.SelectedE4ProtectedNumericalAssessment,
    "responses": r.SelectedE4ProtectedResponses, "response-score": ScheduledResponseScore, "collect": r.SelectedE4NativeCaseResult,
    "reduce": r.SelectedE4NativeReduction}
RECORDS = {"entry": r.SelectedE4ProtectedEntrySeal, "source": r.SelectedE4ProtectedNativeSourceReference, "evidence": r.SelectedE4ProtectedEvidence,
    "design": SelectedE3E4ForecastDesign, "prefix": r.SelectedE4ProtectedPrefixHistory, "checkpoint": ScheduledCheckpoint,
    "numerical": r.SelectedE4ProtectedNumericalAssessment, "witness": r.SelectedE4ProtectedWitness, "frames": r.SelectedE4ProtectedFrames,
    "causal": r.SelectedE4ProtectedCausalPrefix, "account": r.SelectedE4ProtectedAccountSeal, "mechanical": r.SelectedE4ProtectedMechanicalForecast,
    "full": r.SelectedE4ProtectedFullHistory, "full-numerical": r.SelectedE4ProtectedNumericalAssessment,
    "responses": r.SelectedE4ProtectedResponses, "score": ScheduledResponseScore, "cases": r.SelectedE4NativeCaseResult,
    "streams": MatrixHistorySeed, "score-projection": p.SelectedE4ScoreProjection,"bank":p.SelectedE4PhaseBank,"revision-forecasts":p.SelectedE4ForecastBank}
INPUTS = {"entry": ("evidence","bank"), "prefix": ("entry", "source", "streams"),
    "numerical": ("entry", "source", "prefix", "prefix-arrays"),
    "measure": ("entry", "source", "prefix", "prefix-arrays", "numerical"),
    "check": ("entry", "source", "prefix", "prefix-arrays", "numerical", "witness", "diagnostic-arrays"),
    "project": ("entry", "source", "prefix", "prefix-arrays", "numerical", "witness", "diagnostic-arrays", "frames"),
    "account": ("entry", "revision-forecasts", "design", "causal", "causal-arrays", "witness", "diagnostic-arrays", "mechanical", "mechanical-arrays"),
    "mechanical": ("entry", "causal", "causal-arrays", "templates"),
    "continue": ("entry", "source", "streams", "prefix", "prefix-arrays", "checkpoint", "causal", "account", "mechanical"),
    "full-numerical": ("entry", "source", "full", "full-arrays"),
    "responses": ("entry", "source", "streams", "prefix", "prefix-arrays", "checkpoint", "causal", "account", "mechanical", "mechanical-arrays"),
    "response-score": ("entry", "source", "prefix", "prefix-arrays", "causal", "causal-arrays", "account", "mechanical",
        "mechanical-arrays", "responses", "response-arrays", "templates"),
    "collect": ("entry", "source", "prefix", "causal", "account", "mechanical", "full", "full-numerical", "responses", "score", "score-projection"),
    "reduce": ("entry", "cases")}


OUTPUTS.update({"phase-entry":r.SelectedE4ProtectedEntrySeal,"phase-collect":r.SelectedE4NativeReduction,"adjudicate":ScientificAdjudicationRecord})
RECORDS.update({"wave-evidence":r.SelectedE4PhaseCollectionEvidence,"waves":r.SelectedE4WaveObservation,"reduction":r.SelectedE4NativeReduction})
INPUTS.update({"phase-entry":("evidence","bank","wave-evidence","secondary-target"),"phase-collect":("entry","waves"),"adjudicate":("entry","reduction")})


RECORDS.update({"secondary-target": MatrixE4SecondaryTarget,
    "secondary-readout": MatrixE4SecondaryReadoutSelection,
    "dense-mechanical": ScheduledE4DenseMechanicalForecast})
INPUTS["entry"] = (*INPUTS["entry"], "secondary-target")
INPUTS["mechanical"] = (*INPUTS["mechanical"], "secondary-target")
INPUTS["response-score"] = (*INPUTS["response-score"], "secondary-target", "secondary-readout",
    "dense-mechanical", "dense-mechanical-arrays")

RECORDS["models"] = p.SelectedE4PublicModels
RECORDS["provenance"] = NumericalProducingProvenance
INPUTS = {phase: tuple(names) + (("provenance",) if "source" in names else ())
    for phase, names in INPUTS.items()}


def global_node(programme, phase, wave_id=None):
    return NAMESPACE+"."+phase+"."+programme.fingerprint()+("" if wave_id is None else ".wave."+wave_id)


def local_node(root_id, phase):
    return NAMESPACE + "." + root_id + "." + phase


@dataclass(frozen=True, slots=True)
class SelectedE4ProtectedEntryConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/protected-entry-config"
    VERSION: ClassVar[str] = "2.0.0"
    config_id:str
    programme:p.SelectedE4PhaseProgramme
    bank:ObjectIdentity
    evidence:ObjectIdentity
    evidence_size_bytes:int
    forecast_design_size_bytes:int
    decision:p.SelectedE4PublicRevisionDecision
    models:p.SelectedE4PublicModels|None
    calibration:p.SelectedE4PublicCalibration|None
    declaration:r.SelectedE4NativeProgrammeDeclaration
    declaration_publication:ArtifactWriteResult
    wave_id:str|None
    secondary_readout: MatrixE4SecondaryReadoutSelection
    phase:str="entry"
    wave_evidence:ObjectIdentity|None=None
    wave_evidence_size_bytes:int|None=None

    def __post_init__(self):
        if type(self.secondary_readout) is not MatrixE4SecondaryReadoutSelection:
            raise TypeError("E4 entry requires its actual pre-future target publication selection")
        self.secondary_readout.__post_init__()
        self.programme.__post_init__()
        r.exact_pin(self.bank,p.SelectedE4PhaseBank)
        if self.programme.bank!=self.bank:raise ValueError("selected E4 config changes original complete source bank")
        r.exact_pin(self.evidence,r.SelectedE4ProtectedEvidence)
        if (self.programme.mode=="E4_REVISION_CALIBRATION" and self.models is None):
            raise ValueError("untriggered or unevaluable revision retains CAL unentered")
        if (self.phase not in ("entry","phase-entry") or self.config_id!="config."+global_node(self.programme,self.phase,self.wave_id)
                or type(self.evidence_size_bytes) is not int or not 0<self.evidence_size_bytes<=64*1024**2
                or type(self.decision) is not p.SelectedE4PublicRevisionDecision
                or type(self.forecast_design_size_bytes) is not int or self.forecast_design_size_bytes<1
                or self.models is not None and type(self.models) is not p.SelectedE4PublicModels
                or self.calibration is not None and type(self.calibration) is not p.SelectedE4PublicCalibration):
            raise ValueError("protected E4 entry changes exact whole programme and public frozen operands")
        if (type(self.declaration) is not r.SelectedE4NativeProgrammeDeclaration
                or (self.programme,self.bank,self.evidence,self.decision,self.models,self.calibration)!=(
                    self.declaration.programme,self.declaration.bank,self.declaration.evidence,
                    self.declaration.decision,self.declaration.models,self.declaration.calibration)):
            raise ValueError("protected E4 entry substitutes original full programme declaration")
        from .selected_e4_native_preparation import validate_produced_publication
        validate_produced_publication(self.declaration_publication,self.declaration,
            self.declaration.produced_input_parents)
        if (self.phase=="entry")!=(self.wave_id is not None) or (self.phase=="phase-entry")!=(self.wave_evidence is not None):
            raise ValueError("selected E4 wave and full-phase source entries cannot be interchanged")
        if self.wave_id is not None:self.declaration.wave(self.wave_id)
        if self.wave_evidence is not None:
            r.exact_pin(self.wave_evidence,r.SelectedE4PhaseCollectionEvidence)
            if type(self.wave_evidence_size_bytes) is not int or self.wave_evidence_size_bytes<1:raise ValueError("selected E4 collection evidence needs exact bounded size")
        elif self.wave_evidence_size_bytes is not None:raise ValueError("wave entry cannot invent collection evidence size")

    @property
    def programme_pin(self):return self.programme.identity
    @property
    def scope_group_ids(self):return self.programme.group_ids if self.wave_id is None else self.declaration.wave(self.wave_id).group_ids
    @property
    def scope_cases(self):return tuple(v for v in self.programme.cases if self.wave_id is None or v.root_id in self.declaration.wave(self.wave_id).root_ids)



@dataclass(frozen=True,slots=True)
class SelectedE4ProtectedReduceConfig(CanonicalRecord):
    SCHEMA: ClassVar[str]="empirical-lawhood/matrix-selected-e4/protected-reduce-config"
    config_id:str
    programme:p.SelectedE4PhaseProgramme
    bank:ObjectIdentity
    wave_id:str
    phase:str="reduce"

    def __post_init__(self):
        self.programme.__post_init__()
        r.exact_pin(self.bank,p.SelectedE4PhaseBank)
        if self.programme.bank!=self.bank:raise ValueError("selected E4 config changes original complete source bank")
        if self.phase not in ("reduce","adjudicate") or self.config_id!="config."+global_node(self.programme,self.phase,self.wave_id):
            raise ValueError("protected E4 reduction changes whole assigned original programme")


@dataclass(frozen=True,slots=True)
class SelectedE4ProtectedConfig(CanonicalRecord):
    SCHEMA: ClassVar[str]="empirical-lawhood/matrix-selected-e4/protected-native-config"
    config_id:str
    programme:ObjectIdentity
    source:r.SelectedE4ProtectedNativeSource
    protocol:ScheduledResponseProtocol
    panels:tuple[ScheduledResponsePanel,...]
    response_selection:ObjectIdentity
    phase:str
    population_phase:str
    decision:p.SelectedE4PublicRevisionDecision
    models:p.SelectedE4PublicModels|None
    calibration:p.SelectedE4PublicCalibration|None
    original_summary:p.SelectedE4OriginalCalibrationSummary

    def __post_init__(self):
        if (type(self.source) is not r.SelectedE4ProtectedNativeSource or self.programme!=self.source.programme
                or self.phase not in PHASES or self.phase in ("entry","reduce","account","mechanical")
                or self.config_id!="config."+local_node(self.source.root_id,self.phase)
                or self.protocol.public_source!=self.source.public or type(self.panels) is not tuple
                or tuple(sorted(v.role for v in self.panels))!=("COMMON_NOISE_PANEL","INDEPENDENT_FUTURE")
                or any(v.independent_group_id!=self.source.root.root.independent_group_id for v in self.panels)
                or self.population_phase not in r.POPULATIONS or self.population_phase!=self.source.root.root.role.value):
            raise ValueError("protected E4 local config substitutes phase/population/source/assay")
        _public_models(self)
        self.source.__post_init__()
        self.protocol.__post_init__()
        for v in self.panels:v.__post_init__()



@dataclass(frozen=True,slots=True)
class SelectedE4ProtectedCompactConfig(CanonicalRecord):
    SCHEMA: ClassVar[str]="empirical-lawhood/matrix-selected-e4/protected-compact-native-config"
    config_id:str
    programme:ObjectIdentity
    source:r.SelectedE4ProtectedNativeSourceReference
    protocol:ScheduledResponseProtocol
    panels:tuple[ScheduledResponsePanel,...]
    response_selection:ObjectIdentity
    phase:str
    population_phase:str
    decision:p.SelectedE4PublicRevisionDecision
    models:p.SelectedE4PublicModels|None
    calibration:p.SelectedE4PublicCalibration|None
    original_summary:p.SelectedE4OriginalCalibrationSummary

    def __post_init__(self):
        if (type(self.source) is not r.SelectedE4ProtectedNativeSourceReference or self.programme!=self.source.programme
                or self.phase not in PHASES or self.phase in ("entry","reduce","account","mechanical")
                or self.config_id!="config."+local_node(self.source.root_id,self.phase)
                or self.protocol.public_source!=self.source.public or type(self.panels) is not tuple
                or tuple(sorted(v.role for v in self.panels))!=("COMMON_NOISE_PANEL","INDEPENDENT_FUTURE")
                or any(v.independent_group_id!=self.source.root.root.independent_group_id for v in self.panels)
                or self.population_phase not in r.POPULATIONS or self.population_phase!=self.source.root.root.role.value):
            raise ValueError("protected E4 local config substitutes phase/population/source/assay")
        _public_models(self)
        self.source.__post_init__()
        self.protocol.__post_init__()
        for v in self.panels:v.__post_init__()


@dataclass(frozen=True,slots=True)
class SelectedE4ProtectedPublicConfig(CanonicalRecord):
    SCHEMA: ClassVar[str]="empirical-lawhood/matrix-selected-e4/protected-public-config"
    VERSION: ClassVar[str] = "2.0.0"
    config_id:str
    programme:ObjectIdentity
    public_source:ScheduledPublicSource
    protocol:ScheduledResponseProtocol
    phase:str
    population_phase:str
    decision:p.SelectedE4PublicRevisionDecision
    models:p.SelectedE4PublicModels|None
    calibration:p.SelectedE4PublicCalibration|None
    original_summary:p.SelectedE4OriginalCalibrationSummary

    secondary_readout: MatrixE4SecondaryReadoutSelection

    def __post_init__(self):
        if type(self.secondary_readout) is not MatrixE4SecondaryReadoutSelection:
            raise TypeError("E4 predictor requires its exact pre-future target publication selection")
        self.secondary_readout.__post_init__()
        if type(self.protocol) is not ScheduledResponseProtocol:
            raise TypeError("E4 predictor requires its exact original response protocol")
        if self.secondary_readout.mathematical_protocol != self.protocol.criterion:
            raise ValueError("E4 predictor changes the target's original response mathematics")
        if (type(self.public_source) is not ScheduledPublicSource or self.phase not in ("account","mechanical")
                or self.protocol.public_source!=self.public_source or self.population_phase not in r.POPULATIONS
                or self.public_source.root.role.value!=self.population_phase
                or self.config_id!="config."+local_node(self.public_source.root.root_id,self.phase)):
            raise ValueError("protected E4 predictor config changes exact seedless source/population")
        _public_models(self)



@dataclass(frozen=True,slots=True)
class SelectedE4ProtectedReferencedConfig(SelectedE4ProtectedCompactConfig):
    SCHEMA: ClassVar[str]="empirical-lawhood/matrix-selected-e4/protected-model-reference-native-config"
    models:ObjectIdentity|None


@dataclass(frozen=True,slots=True)
class SelectedE4ProtectedReferencedPublicConfig(SelectedE4ProtectedPublicConfig):
    SCHEMA: ClassVar[str]="empirical-lawhood/matrix-selected-e4/protected-model-reference-public-config"
    models:ObjectIdentity|None


@dataclass(frozen=True,slots=True)
class SelectedE4ProtocolBody(CanonicalRecord):
    """Exact original assay body; its public source already belongs to the leaf."""
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/source-free-protocol-body"
    original:ObjectIdentity
    protocol_id:str
    criterion:ObjectIdentity
    mechanical_model:MatrixFactorResponseModel | MatrixOriginResponseModel
    actions:tuple[MatrixFactorAction,...]
    horizon_steps:tuple[int,...]
    receiver_count:int
    templates:ScheduledResponseArrays
    hessian_difference_step:Decimal
    generic_gap_minimum:Decimal
    spectral_gap_minimum:Decimal
    radial_norm_minimum:Decimal
    complement_gram_minimum:Decimal
    native_reference_tolerance:Decimal
    hessian_reference_tolerance:Decimal
    weak_response_minimum:Decimal
    receiver_gram_tolerance:Decimal
    origin_rule:str

    def __post_init__(self):
        r.exact_pin(self.original,ScheduledResponseProtocol)
        if self.original.object_id!=self.protocol_id:
            raise ValueError("selected E4 protocol body changes original assay identity")

    @classmethod
    def from_protocol(cls,protocol):
        if type(protocol) is not ScheduledResponseProtocol:
            raise TypeError("selected E4 requires the exact original response protocol")
        protocol.__post_init__()
        return cls(original=ObjectIdentity.from_record(protocol.protocol_id,protocol),**{
            field.name:getattr(protocol,field.name) for field in fields(ScheduledResponseProtocol)
            if field.name!="public_source"})

    @p._decimal_context_cache
    def bind(self,public_source):
        self.__post_init__()
        protocol=ScheduledResponseProtocol(public_source=public_source,**{
            field.name:getattr(self,field.name) for field in fields(ScheduledResponseProtocol)
            if field.name!="public_source"})
        if ObjectIdentity.from_record(protocol.protocol_id,protocol)!=self.original:
            raise ValueError("selected E4 protocol body substitutes original source or assay bytes")
        return protocol


@dataclass(frozen=True,slots=True)
class SelectedE4ProtectedProtocolConfig(SelectedE4ProtectedReferencedConfig):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/source-free-protocol-native-config"
    protocol:SelectedE4ProtocolBody

    def __post_init__(self):
        if type(self.protocol) is not SelectedE4ProtocolBody:
            raise TypeError("selected E4 requires the exact source-free protocol body")
        SelectedE4ProtectedReferencedConfig(**{
            field.name:self.protocol.bind(self.source.public) if field.name=="protocol" else getattr(self,field.name)
            for field in fields(SelectedE4ProtectedReferencedConfig)})


@dataclass(frozen=True,slots=True)
class SelectedE4ProtectedProtocolPublicConfig(SelectedE4ProtectedReferencedPublicConfig):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/source-free-protocol-public-config"
    protocol:SelectedE4ProtocolBody

    def __post_init__(self):
        if type(self.protocol) is not SelectedE4ProtocolBody:
            raise TypeError("selected E4 requires the exact source-free protocol body")
        SelectedE4ProtectedReferencedPublicConfig(**{
            field.name:self.protocol.bind(self.public_source) if field.name=="protocol" else getattr(self,field.name)
            for field in fields(SelectedE4ProtectedReferencedPublicConfig)})


def referenced_config(config):
    return type(config) in (SelectedE4ProtectedReferencedConfig,SelectedE4ProtectedReferencedPublicConfig,
        SelectedE4ProtectedProtocolConfig,SelectedE4ProtectedProtocolPublicConfig)


@dataclass(frozen=True,slots=True)
class BoundSelectedE4Models:
    """Noncanonical local values; identities always remain the original wire."""
    transport:object
    models:p.SelectedE4PublicModels

    def __post_init__(self):
        if not referenced_config(self.transport) or type(self.models) is not p.SelectedE4PublicModels:
            raise TypeError("selected E4 needs its exact referenced configuration and public models")
        self.transport.__post_init__()
        self.models.__post_init__()
        if self.transport.models!=self.models.identity:
            raise ValueError("selected E4 substitutes the exact shared frozen public models")
        _public_models(self)

    def __getattr__(self,name):
        return protocol_for_config(self.transport) if name=="protocol" else getattr(self.transport,name)


def bind_selected_e4_models(config,models):return BoundSelectedE4Models(config,models)


def wire_config(config):return config.transport if type(config) is BoundSelectedE4Models else config


def protocol_body_config(config):
    return type(wire_config(config)) in (SelectedE4ProtectedProtocolConfig,SelectedE4ProtectedProtocolPublicConfig)


def protocol_for_config(config):
    wire=wire_config(config)
    if not protocol_body_config(wire):return wire.protocol
    source=wire.source.public if type(wire) is SelectedE4ProtectedProtocolConfig else wire.public_source
    return wire.protocol.bind(source)


def native_config(config):
    return type(wire_config(config)) in (SelectedE4ProtectedCompactConfig,SelectedE4ProtectedReferencedConfig,
        SelectedE4ProtectedProtocolConfig)


def model_identity(config):
    value=config.models
    return value if type(value) is ObjectIdentity else None if value is None else value.identity


def inputs_for_config(config, *, direct_operands=True):
    wire=wire_config(config)
    names=INPUTS[wire.phase]
    if not direct_operands and wire.phase=="responses":
        names=tuple(name for name in names if name!="checkpoint")
    return names+(("models",) if referenced_config(wire) else ())


def key_for_phase(phase,*,referenced=False,compact_protocol=False):
    if (phase not in (*PHASES,*EXTRAS) or referenced and phase in ("entry","reduce",*EXTRAS)
            or compact_protocol and not referenced):
        raise ValueError("selected E4 capability requires its exact installed owning phase")
    return NAMESPACE+(".shared-protocol." if compact_protocol else ".shared-models." if referenced else ".")+phase


def declaration_for_config(config):
    wire=wire_config(config)
    rows=tuple(value for value in operation_declarations() if value.capability_key==key_for_phase(wire.phase,
        referenced=referenced_config(wire),compact_protocol=protocol_body_config(wire))
        and value.config_record_type is type(wire))
    if len(rows)!=1:raise ValueError("selected E4 configuration lacks its exact installed capability revision")
    return rows[0]


def _public_models(config):
    if (type(config.decision) is not p.SelectedE4PublicRevisionDecision
            or (config.models is None)!=(not config.decision.fit_available)
            or config.models is not None and not referenced_config(config) and (type(config.models) is not p.SelectedE4PublicModels
                or (config.models.development,config.models.nomination,config.models.frozen,
                    config.models.revision_model.identity,config.models.baseline_model.identity)!=(
                    config.decision.development,config.decision.nomination,config.decision.frozen,
                    config.decision.revision_model,config.decision.baseline_model))
            or config.population_phase=="CALIBRATION" and config.models is None
            or (config.calibration is None)!=(config.population_phase!="CONFIRMATION" or config.models is None)):
        raise ValueError("protected E4 config changes actual revision/baseline entry or matched calibration")
    if referenced_config(config):
        r.exact_pin(config.models,p.SelectedE4PublicModels)
    if type(config.original_summary) is not p.SelectedE4OriginalCalibrationSummary:
        raise TypeError("selected E4 local config requires exact original calibration scope")
    for v in (config.original_summary,config.decision,config.models,config.calibration):
        if v is not None:v.__post_init__()

@dataclass(frozen=True,slots=True)
class SelectedE4PhaseCollectConfig(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/phase-collect-config"
    config_id:str
    programme:p.SelectedE4PhaseProgramme
    bank:ObjectIdentity
    declaration:r.SelectedE4NativeProgrammeDeclaration
    observations:tuple[tuple[str,ObjectIdentity,int],...]
    phase:str="phase-collect"

    def __post_init__(self):
        if (type(self.programme) is not p.SelectedE4PhaseProgramme or self.programme!=self.declaration.programme
                or self.bank!=self.programme.bank or self.phase!="phase-collect"
                or self.config_id!="config."+global_node(self.programme,self.phase)
                or type(self.observations) is not tuple or any(type(v) is not tuple or len(v)!=3 for v in self.observations)
                or tuple(v[0] for v in self.observations)!=tuple(v.wave_id for v in self.programme.waves)):
            raise ValueError("selected E4 collector changes original complete programme/wave census")
        for _,pin,size in self.observations:
            r.exact_pin(pin,r.SelectedE4WaveObservation)
            if type(size) is not int or not 0<size<=64*1024**2:raise ValueError("selected E4 collector changes bounded observed wave bytes")


def phase_of(config):
    config=wire_config(config)
    if type(config) not in (SelectedE4ProtectedEntryConfig, SelectedE4ProtectedReduceConfig, SelectedE4ProtectedCompactConfig, SelectedE4ProtectedPublicConfig,SelectedE4PhaseCollectConfig,SelectedE4ProtectedReferencedConfig,SelectedE4ProtectedReferencedPublicConfig,SelectedE4ProtectedProtocolConfig,SelectedE4ProtectedProtocolPublicConfig):
        raise TypeError("selected E4 requires an exact installed owning configuration")
    config.__post_init__()
    return config.phase


def task_id(config):
    phase_of(config)
    return config.config_id.removeprefix("config.")


def units(config):
    if type(config) in (SelectedE4ProtectedEntryConfig, SelectedE4ProtectedReduceConfig,SelectedE4PhaseCollectConfig):
        return config.scope_group_ids if type(config) is SelectedE4ProtectedEntryConfig else config.programme.group_ids if type(config) is SelectedE4PhaseCollectConfig else next(v.group_ids for v in config.programme.waves if v.wave_id==config.wave_id)
    return ((config.source.root.root.independent_group_id,) if native_config(config)
        else (config.public_source.root.independent_group_id,))


def stage(phase):
    if phase == "adjudicate":return ScientificStage.EVALUATE
    return (ScientificStage.ACQUIRE if phase in NATIVE else ScientificStage.FREEZE if phase in ("entry","phase-entry", "account", "mechanical")
        else ScientificStage.FALSIFY if phase in ("numerical", "check", "full-numerical", "response-score", "reduce","phase-collect")
        else ScientificStage.TRANSFORM)


def access(phase):
    if phase not in (*PHASES,*EXTRAS):raise ValueError("unknown protected E4 operation")
    if phase == "adjudicate":return OutcomeAccess.EVALUATOR_REVEAL
    return r.SEALED if phase in ("continue","full-numerical","responses","response-score","collect","reduce","phase-collect") else r.BLIND


def input_access(name):
    base=name.split(".",1)[0] if name.startswith(("cases.","streams.","waves.")) else name
    return r.SEALED if base in ("full","full-arrays","full-numerical","responses","response-arrays","score","score-projection","cases","waves","reduction") else r.BLIND


def native_contract(config, source, *, recorded_operation=None):
    if not native_config(config) or config.source != source_transport(source) or config.phase not in NATIVE:
        raise ValueError("selected E4 native work requires exact current local configuration")
    operation, _ = selected_native_operation(NAMESPACE, config.phase, recorded_operation=recorded_operation)
    sources = selected_native_source_operands(source)
    return ObjectIdentity.from_record(config.config_id, wire_config(config)), config.config_id.removeprefix("config."), operation, tuple(sorted(sources, key=lambda value: value.object_id))


def digests(config):
    if type(config) in (SelectedE4ProtectedEntryConfig, SelectedE4ProtectedReduceConfig,SelectedE4PhaseCollectConfig):
        return tuple(sorted((config.programme.fingerprint(), config.secondary_readout.fingerprint(),
            config.secondary_readout.target.object_fingerprint))) if type(config) is SelectedE4ProtectedEntryConfig else (config.programme.fingerprint(),)
    values = {config.programme.object_fingerprint, protocol_for_config(config).fingerprint()}
    if native_config(config):
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
    referenced: bool=False
    compact_protocol: bool=False

    def __call__(self):
        from .selected_e4_protected_workers import SelectedE4ProtectedWorker
        declaration = next(row for row in operation_declarations() if row.capability_key == key_for_phase(self.phase,referenced=self.referenced,compact_protocol=self.compact_protocol))
        return SelectedE4ProtectedWorker(self.phase, declaration.manifest())


def prepare_for_invocation(supplier, runner):
    callback = getattr(supplier, "prepare_selected_e4_protected", None)
    if not callable(callback):
        raise PermissionError("selected protected E4 requires actual issue/execution/source/original producer custody")
    return ParentPreparedTaskRunner(runner.manifest, partial(callback, runner=runner), native_effect=runner.phase in NATIVE)


def prepare_native_work(*, runner, context, expected_parent):
    return runner.prepare_native_work(context, expected_parent=expected_parent)


@lru_cache(maxsize=1)
def operation_declarations():
    kinds = (*RECORDS.values(), *OUTPUTS.values(), ScheduledE4DenseResponseScore, SelectedE4ProtectedEntryConfig, SelectedE4ProtectedReduceConfig, SelectedE4ProtectedCompactConfig, SelectedE4ProtectedPublicConfig,SelectedE4PhaseCollectConfig,r.SelectedE4PhaseCollectionEvidence,r.SelectedE4WaveObservation,p.SelectedE4ScoreProjection,p.SelectedE4ObservedData,p.SelectedE4ForecastBank)
    kinds = (*kinds, r.SelectedE4ProtectedNativeSource, SelectedE4ProtectedConfig,SelectedE4ProtectedReferencedConfig,SelectedE4ProtectedReferencedPublicConfig,
        SelectedE4ProtocolBody,SelectedE4ProtectedProtocolConfig,SelectedE4ProtectedProtocolPublicConfig,p.SelectedE4PublicModels)
    codecs = {kind.SCHEMA: kind for kind in kinds}
    rows = []
    for phase in (*PHASES,*EXTRAS):
        ports = tuple(sorted((RecursivePortContract(name, MATRIX_ARRAY_SCHEMA if (kind := RECORDS.get(name)) is None else kind.SCHEMA,
            "application/x-npz" if kind is None else "application/json", MAXIMUM_MATRIX_ARRAY_BYTES if kind is None else None,
            minimum_count=(8 if phase == "responses" else 4) if name == "streams" else 1, maximum_count=(8 if phase == "responses" else 4) if name == "streams" else None if name in ("cases","waves") else 1)
            for name in INPUTS[phase]), key=lambda value: value.port_id))
        outputs = [OutputTemplate("adjudication" if phase == "adjudicate" else "product", OUTPUTS[phase].SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json")]
        if phase == "mechanical":
            outputs.extend((OutputTemplate("dense-product", ScheduledE4DenseMechanicalForecast.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
                OutputTemplate("dense-arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz")))
        if phase == "response-score":
            outputs.append(OutputTemplate("dense-score", ScheduledE4DenseResponseScore.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, "application/json", ".json"))
        if phase in ARRAY_OUTPUTS:
            outputs.append(OutputTemplate("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", ".npz"))
        if phase == "entry":
            outputs.append(OutputTemplate("forecasts",p.SelectedE4ForecastBank.SCHEMA,ArtifactProfile.CANONICAL_JSON,"application/json",".json"))
        if phase == "response-score":
            outputs.append(OutputTemplate("projection",p.SelectedE4ScoreProjection.SCHEMA,ArtifactProfile.CANONICAL_JSON,"application/json",".json"))
        if phase in ("reduce","phase-collect"):
            outputs.extend((OutputTemplate("observed",p.SelectedE4ObservedData.SCHEMA,ArtifactProfile.CANONICAL_JSON,"application/json",".json"),
                OutputTemplate("forecasts",p.SelectedE4ForecastBank.SCHEMA,ArtifactProfile.CANONICAL_JSON,"application/json",".json")))
        if phase == "prefix":
            outputs.append(OutputTemplate("checkpoint", ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"))
        kind = (SelectedE4ProtectedEntryConfig if phase in ("entry","phase-entry") else SelectedE4PhaseCollectConfig if phase=="phase-collect" else SelectedE4ProtectedReduceConfig if phase in ("reduce","adjudicate")
            else SelectedE4ProtectedPublicConfig if phase in ("account", "mechanical") else SelectedE4ProtectedCompactConfig)
        rows.append(RecursiveOperationDeclaration(NAMESPACE + "." + phase, "3.0.0" if phase in NATIVE or phase in ("response-score", "account") else "2.0.0" if phase in ("entry", "phase-entry", "account", "mechanical") or "source" in INPUTS[phase] else "1.0.0",
            NAMESPACE + "." + phase + (".direct-operands.v3" if phase in NATIVE else ".matched-causal.v3" if phase == "account" else ".dense-e4.v3" if phase == "response-score" else ".dense-e4.v2" if phase in ("entry", "phase-entry", "account", "mechanical") else ".provenance-reference.v2" if "source" in INPUTS[phase] else ".original-science.v1"),
            CapabilityKind.EVALUATOR if phase == "adjudicate" else CapabilityKind.SIMULATOR if phase in NATIVE else CapabilityKind.FALSIFIER if stage(phase) is ScientificStage.FALSIFY else CapabilityKind.TRANSFORM,
            kind, stage(phase), ports, tuple(sorted(outputs, key=lambda value: value.output_id)),
            tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_FROZEN_MODELS,
                *((CapabilityPermission.READ_SEALED_OUTCOMES,) if access(phase) in
                    (OutcomeAccess.EVALUATION_SEALED,OutcomeAccess.EVALUATOR_REVEAL) else ()),
                *((CapabilityPermission.REVEAL_OUTCOMES,) if phase == "adjudicate" else ())))),
            EvidenceCeiling.NON_PROMOTABLE, access(phase), VisibilityCeiling.OUTCOME_VISIBLE if phase == "adjudicate" else r.PROSPECTIVE, BUDGET,
            ("actual-parent-original-product-custody", "declared-whole-group-protected-e4-phase", "selected-e3-primary-point-only"),
            _Factory(phase), codecs,
            scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=units,
                scientific_operand_sha256s=digests,
                native_effect_slot_ids=slots if phase in NATIVE else None,
                scientific_root_validator=scientific_root_validator,
                adjudication_output_id="adjudication" if phase == "adjudicate" else None),
            execution_properties=RecursiveExecutionProperties(native_effect=phase in NATIVE, complete_unit_census=phase in NATIVE,
                native_work_preparer=prepare_native_work if phase in NATIVE else None, runner_preparation_factory=prepare_for_invocation,
                barrier=BarrierKind.REVEAL if phase == "adjudicate" else BarrierKind.FREEZE if stage(phase) is ScientificStage.FREEZE else BarrierKind.NONE),
            provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS))
    for original in tuple(rows):
        phase=original.capability_key.rsplit(".",1)[-1]
        if original.config_record_type not in (SelectedE4ProtectedCompactConfig,SelectedE4ProtectedPublicConfig):continue
        kind=SelectedE4ProtectedReferencedConfig if original.config_record_type is SelectedE4ProtectedCompactConfig else SelectedE4ProtectedReferencedPublicConfig
        rows.append(replace(original,capability_key=key_for_phase(phase,referenced=True),capability_version="3.0.0" if phase in NATIVE or phase in ("response-score", "account") else "2.0.0" if phase in ("account","mechanical") else "1.0.0",
            implementation_id=NAMESPACE+"."+phase+(".shared-public-models.matched-causal.v3" if phase == "account" else ".shared-public-models.dense-e4.v3" if phase == "response-score" else ".shared-public-models.dense-e4.v2" if phase in ("account","mechanical") else ".shared-public-models.v1"),
            config_record_type=kind,input_ports=tuple(sorted((*original.input_ports,
                RecursivePortContract("models",p.SelectedE4PublicModels.SCHEMA,"application/json",None)),key=lambda value:value.port_id)),
            runner_factory=_Factory(phase,True)))
    for original in tuple(rows):
        phase=original.capability_key.rsplit(".",1)[-1]
        if original.config_record_type not in (SelectedE4ProtectedReferencedConfig,SelectedE4ProtectedReferencedPublicConfig):continue
        kind=SelectedE4ProtectedProtocolConfig if original.config_record_type is SelectedE4ProtectedReferencedConfig else SelectedE4ProtectedProtocolPublicConfig
        rows.append(replace(original,capability_key=key_for_phase(phase,referenced=True,compact_protocol=True),
            implementation_id=NAMESPACE+"."+phase+(".source-free-protocol.matched-causal.v3" if phase == "account" else ".source-free-protocol.dense-e4.v3" if phase == "response-score" else ".source-free-protocol.dense-e4.v2" if phase in ("account","mechanical") else ".source-free-protocol.v1"),config_record_type=kind,
            runner_factory=_Factory(phase,True,True)))
    return tuple(sorted(rows, key=lambda row: (row.capability_key,row.capability_version)))


@p._decimal_context_cache
def contracts(programme,bank,evidence_pin,evidence_size,decision,models,calibration,declaration,declaration_publication,wave_id,*,secondary_readout,secondary_target=None,referenced_models=True,compact_protocol=True,direct_operands=True):
    """Reuse only pure immutable wave projections; custody remains caller-owned."""
    p.validate_selected_phase_bank(programme,bank)
    if bank.identity!=declaration.bank:raise ValueError("selected E4 wave substitutes actual original bank")
    wave=declaration.wave(wave_id)
    entry=SelectedE4ProtectedEntryConfig("config."+global_node(programme,"entry",wave_id),programme,bank.identity,evidence_pin,
        evidence_size,len(bank.forecast_design.canonical_bytes()),decision,models,calibration,declaration,declaration_publication,wave_id,secondary_readout)
    prefixes=[]
    index=bank.source_index()
    for descriptor in bank.sources:
        if descriptor.root_id not in wave.root_ids:continue
        source=r.SelectedE4ProtectedNativeSourceReference.from_bank(programme,bank,descriptor,index=index)
        protocol=next(v for v in bank.response_selection.protocols if v.public_source.root.root_id==source.root_id)
        panels=dict(bank.response_selection.panels)[source.root.root.independent_group_id]
        kind=(SelectedE4ProtectedProtocolConfig if compact_protocol else SelectedE4ProtectedReferencedConfig) if referenced_models and models is not None else SelectedE4ProtectedCompactConfig
        selected_models=models.identity if kind in (SelectedE4ProtectedReferencedConfig,SelectedE4ProtectedProtocolConfig) else models
        if kind is SelectedE4ProtectedProtocolConfig:protocol=SelectedE4ProtocolBody.from_protocol(protocol)
        prefixes.append(kind("config."+local_node(source.root_id,"prefix"),programme.identity,source,
            protocol,panels,bank.response_selection.identity,"prefix",bank.phase,decision,selected_models,calibration,declaration.original_summary))
    return wave_contracts(entry,tuple(prefixes),bank_record=bank,design_record=bank.forecast_design,secondary_target=secondary_target,direct_operands=direct_operands)


@p._decimal_context_cache
def wave_contracts(entry,prefixes,*,bank_record=None,design_record=None,secondary_target=None,direct_operands=True):
    """Exact immutable graph projection; two working sets, no I/O or authority."""
    entry.__post_init__()
    if secondary_target is not None:
        entry.secondary_readout.validate_target(secondary_target)
        for original in prefixes:
            secondary_target.validate_protocol(protocol_for_config(original))
    programme=entry.programme
    wave=entry.declaration.wave(entry.wave_id)
    if (type(prefixes) is not tuple or tuple(v.source.root_id for v in prefixes)!=wave.root_ids):
        raise ValueError("selected E4 wave changes complete declared root ordering")
    configs={task_id(entry):entry}
    final=global_node(programme,"reduce",entry.wave_id)
    configs[final]=SelectedE4ProtectedReduceConfig("config."+final,programme,entry.bank,entry.wave_id)
    adjudicate=global_node(programme,"adjudicate",entry.wave_id)
    configs[adjudicate]=SelectedE4ProtectedReduceConfig("config."+adjudicate,programme,entry.bank,entry.wave_id,phase="adjudicate")
    external={};records={};arrays={};links=[]
    def pin_input(name,pin,size,access=r.BLIND,*,logical_id=None):
        external[name]=RecursiveExternalInput(name,pin.object_id if logical_id is None else logical_id,pin.object_schema,"application/json",size,
            access,r.PROSPECTIVE,pin.object_fingerprint,"SOURCE")
        return name
    def add(name,value,identifier):
        pin=r.pin(value,identifier)
        pin_input(name,pin,len(value.canonical_bytes()))
        if records.setdefault(name,value)!=value:raise ValueError("selected E4 aliases original external scientific bytes")
        return name
    def array(artifact):
        name="external.selected-e4-array."+artifact.fingerprint()
        row=RecursiveExternalInput(name,artifact.artifact_id,artifact.payload_schema,artifact.media_type,artifact.size_bytes,
            r.BLIND,r.PROSPECTIVE,artifact.sha256,"SOURCE")
        if external.setdefault(name,row)!=row or arrays.setdefault(name,artifact)!=artifact:
            raise ValueError("selected E4 aliases original template custody")
        return name
    def edge(node,port,external_id=None,producer=None,output="product"):
        links.append(RecursiveInputLink("edge."+node+"."+port,node,port,external_input_id=external_id,
            producer_node_id=producer,producer_output_id=output if producer is not None else None,
            scientific_role="SOURCE" if producer is None else "HISTORY"))
    evidence=pin_input("external.selected-e4-evidence."+entry.evidence.object_fingerprint,entry.evidence,entry.evidence_size_bytes)
    bank=pin_input("external.selected-e4-bank."+entry.bank.object_fingerprint,entry.bank,entry.declaration.bank_publication.materialization.size_bytes)
    edge(task_id(entry),"evidence",external_id=evidence);edge(task_id(entry),"bank",external_id=bank)
    target_pin=entry.secondary_readout.target
    target_id=pin_input("external.selected-e4-secondary-target."+target_pin.object_fingerprint,
        target_pin,entry.secondary_readout.publication.materialization.size_bytes)
    if secondary_target is not None:records[target_id]=secondary_target
    selection_id=add("external.selected-e4-secondary-readout."+entry.secondary_readout.fingerprint(),
        entry.secondary_readout,"record_id")
    edge(task_id(entry),"secondary-target",external_id=target_id)
    if bank_record is not None:
        if bank_record.identity!=entry.bank:raise ValueError("selected E4 original bank bytes differ")
        records[bank]=bank_record
    design=pin_input("external.selected-e4-design."+programme.forecast_design.object_fingerprint,
        programme.forecast_design,entry.forecast_design_size_bytes)
    if design_record is not None:
        if design_record.identity!=programme.forecast_design:raise ValueError("selected E4 original forecast design bytes differ")
        records[design]=design_record
    models_id=None
    if any(referenced_config(value) for value in prefixes):
        if entry.models is None:raise ValueError("selected E4 referenced leaves require actual frozen public models")
        models_id=add("external.selected-e4-models."+entry.models.fingerprint(),entry.models,"record_id")
    for original in prefixes:
        source=original.source
        protocol=protocol_for_config(original)
        case=next(v for v in entry.scope_cases if v.root_id==source.root_id)
        if (source.programme!=programme.identity or source.bank!=entry.bank or source.reference.identity!=case.source
                or ObjectIdentity.from_record(source.coordinate.coordinate_id,source.coordinate)!=case.coordinate
                or source.root.root.independent_group_id!=case.independent_group_id
                or original.response_selection!=programme.response_selection or protocol.public_source!=source.public
                or (original.population_phase,original.decision,model_identity(original),original.calibration,original.original_summary)!=(
                    entry.declaration.bank_phase,entry.decision,model_identity(entry),entry.calibration,entry.declaration.original_summary)):
            raise ValueError("selected E4 wave changes original exact scientific source/coordinate/model/assay")
        source_id=add("external.selected-e4-source."+source.fingerprint(),source,"record_id")
        provenance_id=pin_input("external.selected-e4-provenance."+source.provenance.object_fingerprint,
            source.provenance,source.provenance_size_bytes,logical_id="selected-e4.provenance."+source.provenance.object_fingerprint)
        if bank_record is not None:
            provenance=next(v for v in bank_record.provenances if v.identity==source.provenance)
            if len(provenance.canonical_bytes())!=source.provenance_size_bytes:
                raise ValueError("selected E4 changes original standalone provenance size")
            records[provenance_id]=provenance
        # Stream object IDs are code-owned original root stream identities.
        streams=[]
        for stream_pin, value in selected_stream_operands(source, original.panels, include_future=direct_operands):
            name=pin_input("external.selected-e4-stream."+stream_pin.object_id,stream_pin,len(value.canonical_bytes()))
            records[name]=value;streams.append(name)
        templates=array(protocol.templates.array_artifact)
        nodes={phase:local_node(source.root_id,phase) for phase in PHASES if phase not in ("entry","reduce")}
        produced={"entry":(task_id(entry),"product"),"revision-forecasts":(task_id(entry),"forecasts"),"prefix":(nodes["prefix"],"product"),"prefix-arrays":(nodes["prefix"],"arrays"),
            "checkpoint":(nodes["prefix"],"checkpoint"),"numerical":(nodes["numerical"],"product"),"witness":(nodes["measure"],"product"),
            "diagnostic-arrays":(nodes["measure"],"arrays"),"frames":(nodes["check"],"product"),"causal":(nodes["project"],"product"),
            "causal-arrays":(nodes["project"],"arrays"),"account":(nodes["account"],"product"),"mechanical":(nodes["mechanical"],"product"),
            "mechanical-arrays":(nodes["mechanical"],"arrays"),"dense-mechanical":(nodes["mechanical"],"dense-product"),
            "dense-mechanical-arrays":(nodes["mechanical"],"dense-arrays"),"full":(nodes["continue"],"product"),"full-arrays":(nodes["continue"],"arrays"),
            "full-numerical":(nodes["full-numerical"],"product"),"responses":(nodes["responses"],"product"),"response-arrays":(nodes["responses"],"arrays"),
            "score":(nodes["response-score"],"product"),"score-projection":(nodes["response-score"],"projection")}
        for phase,node in nodes.items():
            public_kind=(SelectedE4ProtectedProtocolPublicConfig if protocol_body_config(original) else SelectedE4ProtectedReferencedPublicConfig) if referenced_config(original) else SelectedE4ProtectedPublicConfig
            configs[node]=(public_kind("config."+node,programme.identity,source.public,original.protocol,phase,
                original.population_phase,entry.decision,original.models,entry.calibration,entry.declaration.original_summary,entry.secondary_readout) if phase in ("account","mechanical")
                else replace(original,config_id="config."+node,phase=phase))
            for name in inputs_for_config(configs[node],direct_operands=direct_operands):
                if name=="streams":
                    for index,stream in enumerate(streams if phase == "responses" else streams[:4]):edge(node,"streams."+str(index),external_id=stream)
                elif name in ("source","design","templates","provenance","models","secondary-target","secondary-readout"):
                    edge(node,name,external_id={"source":source_id,"design":design,"templates":templates,"provenance":provenance_id,"models":models_id,"secondary-target":target_id,"secondary-readout":selection_id}[name])
                else:
                    producer,output=produced[name];edge(node,name,producer=producer,output=output)
        edge(final,"cases."+source.root_id,producer=nodes["collect"])
    edge(final,"entry",producer=task_id(entry))
    edge(adjudicate,"entry",producer=task_id(entry));edge(adjudicate,"reduction",producer=final)
    return tuple(sorted(configs.items())),tuple(sorted(external.values(),key=lambda v:v.input_id)),tuple(sorted(links,key=lambda v:v.edge_id)),tuple(sorted(records.items())),tuple(sorted(arrays.items()))


def validate_selected_e4_root_scope(*,programme,group_ids,context):
    if type(context) is not RecursiveScientificRootContext or type(context.root) is not StudyDraft:
        raise TypeError("selected protected E4 requires an actual prospective scientific root")
    entries=tuple(v.record for v in context.config_inputs if type(v.record) is SelectedE4ProtectedEntryConfig)
    if len(entries)!=1:raise ValueError("protected E4 requires exact unique phase/wave entry")
    entry,=entries
    entry.__post_init__()
    views=tuple(sorted({v.view_id for row in context.config_inputs if native_config(row.record)
        for v in (row.record.source.coordinate.primary_view,row.record.source.coordinate.fine_view)}))
    expected=r.phase_root(entry.declaration) if entry.wave_id is None else r.wave_root(entry.declaration,entry.wave_id,views=views)
    root=context.root
    if (entry.programme.identity!=programme or entry.scope_group_ids!=group_ids or context.selected_unit_ids!=group_ids
            or root.system is None or root.experiment is None or root.campaign is None):
        raise ValueError("protected E4 changes exact complete phase/wave selection")
    normalized=replace(root,source_materializations=(),dag_template_key=expected.dag_template_key,
        capability_selections=expected.capability_selections,campaign=replace(root.campaign,budget=expected.campaign.budget,
            authority_policy=expected.campaign.authority_policy))
    if normalized!=replace(expected,source_materializations=()):
        raise ValueError("protected E4 component changes original scientific root, cutoffs, controls or frozen programme")
    if entry.declaration.identity not in {v.object_identity for v in root.design_inputs}:
        raise ValueError("protected E4 component omits original pre-entry full declaration publication pin")
    return entry


def scientific_root_validator(config,context):
    entries=tuple(v.record for v in context.config_inputs if type(v.record) is SelectedE4ProtectedEntryConfig)
    if len(entries)!=1:raise ValueError("protected E4 requires exact unique wave entry")
    entry,=entries
    validate_selected_e4_root_scope(programme=entry.programme.identity,group_ids=entry.scope_group_ids,context=context)
    if entry.wave_id is None:
        validate_phase_collect_scope(config,context,entry)
        return
    prefixes=tuple(v.record for v in context.config_inputs if native_config(v.record) and v.record.phase=="prefix")
    configs,external,links,_,_=wave_contracts(entry,prefixes)
    node=task_id(config);phase=phase_of(config)
    if (tuple((v.node_id,v.record) for v in context.config_inputs)!=configs or dict(configs).get(node)!=config or context.node_id!=node
            or tuple(context.links)!=links or tuple(context.external_inputs)!=external
            or context.stage is not stage(phase) or context.unit_ids!=units(config)
            or context.complete_unit_census!=(phase in NATIVE) or context.outcome_access is not access(phase)
            or context.visibility_ceiling is not (VisibilityCeiling.OUTCOME_VISIBLE if phase == "adjudicate" else r.PROSPECTIVE)):
        raise ValueError("protected E4 changes exact native wave graph/assay/freeze-before-future/census/lane")


@dataclass(frozen=True,slots=True)
class LoweredSelectedE4Protected:
    draft:RecursiveStudyDraft
    input_records:tuple
    input_artifacts:tuple


def operational_tasks(declaration,bank,*,evidence,declaration_publication,wave_id):
    r.validate_evidence(evidence,declaration.programme,bank,declaration.decision,declaration.models,declaration.calibration)
    p.validate_selected_phase_bank(declaration.programme,bank)
    if bank.identity!=declaration.bank:raise ValueError("selected E4 tasks substitute actual original bank")
    declaration.__post_init__()
    from .selected_e4_native_preparation import validate_produced_publication
    validate_produced_publication(declaration_publication,declaration,declaration.produced_input_parents)
    wave=declaration.wave(wave_id)
    rows=[(global_node(declaration.programme,phase,wave_id),phase) for phase in ("entry","reduce","adjudicate")]
    rows.extend((local_node(root,phase),phase) for root in wave.root_ids
        for phase in PHASES if phase not in ("entry","reduce"))
    return tuple(sorted(rows))


def lower_selected_e4_protected_wave(declaration,bank,*,evidence,declaration_publication,wave_id,campaign,draft_id,secondary_target,secondary_readout):
    r.validate_evidence(evidence,declaration.programme,bank,declaration.decision,declaration.models,declaration.calibration)
    secondary_readout.validate_target(secondary_target)
    configs,external,links,records,arrays=contracts(declaration.programme,bank,evidence.identity,len(evidence.canonical_bytes()),
        declaration.decision,declaration.models,declaration.calibration,declaration,declaration_publication,wave_id,
        secondary_readout=secondary_readout,secondary_target=secondary_target)
    selected=dict(declaration.planned_task_budgets)
    operations=tuple(RecursiveOperationSpec.from_config(node_id=n,selection=declaration_for_config(c).registration().selection,
        config_id=c.config_id,config=c,obligation_ids=("obligation."+n,),resource_budget=selected[n]) for n,c in configs)
    records=tuple(sorted((*records,("external.selected-e4-evidence."+evidence.fingerprint(),evidence))))
    index=bank.source_index()
    views=tuple(sorted({v.view_id for root in declaration.wave(wave_id).root_ids
        for v in (bank.source(root,index=index).coordinate.primary_view,bank.source(root,index=index).coordinate.fine_view)}))
    root=r.wave_root(declaration,wave_id,views=views)
    if campaign!=declaration.root.campaign:raise ValueError("selected E4 wave changes original declared full-phase campaign")
    return LoweredSelectedE4Protected(RecursiveStudyDraft(draft_id,root.question,root.campaign,(),(),(),operations,external,links,
        tuple(n for n,_ in configs),prospective_draft=root),records,arrays)


def phase_collect_contracts(entry,collection,*,bank_record=None,evidence_record=None,observations=None,secondary_target=None):
    if (entry.phase!="phase-entry" or entry.wave_id is not None or collection.identity!=entry.wave_evidence
            or collection.declaration!=entry.declaration.identity
            or tuple(v.locator.wave_id for v in collection.waves)!=tuple(v.wave_id for v in entry.programme.waves)):
        raise ValueError("selected E4 phase collector changes original full declaration/waves")
    node=global_node(entry.programme,"phase-collect")
    config=SelectedE4PhaseCollectConfig("config."+node,entry.programme,entry.bank,entry.declaration,
        tuple((v.locator.wave_id,v.observation,v.size_bytes) for v in collection.waves))
    return _phase_contract_rows(entry,config,collection=collection,bank_record=bank_record,
        evidence_record=evidence_record,observations=observations,secondary_target=secondary_target)


def _phase_contract_rows(entry,config,*,collection=None,bank_record=None,evidence_record=None,observations=None,secondary_target=None):
    entry.__post_init__()
    if secondary_target is not None:entry.secondary_readout.validate_target(secondary_target)
    external=[];records=[];links=[]
    def add(name,pin,size,consumer,port,access,record=None,*,scientific_role="SOURCE"):
        key="external.selected-e4-"+name+"."+pin.object_fingerprint
        external.append(RecursiveExternalInput(key,pin.object_id,pin.object_schema,"application/json",size,access,r.PROSPECTIVE,pin.object_fingerprint,scientific_role))
        links.append(RecursiveInputLink("edge."+consumer+"."+port,consumer,port,external_input_id=key,scientific_role=scientific_role))
        if record is not None:records.append((key,record))
    add("bank",entry.bank,entry.declaration.bank_publication.materialization.size_bytes,task_id(entry),"bank",r.BLIND,bank_record)
    add("evidence",entry.evidence,entry.evidence_size_bytes,task_id(entry),"evidence",r.BLIND,evidence_record)
    add("secondary-target",entry.secondary_readout.target,entry.secondary_readout.publication.materialization.size_bytes,
        task_id(entry),"secondary-target",r.BLIND,secondary_target)
    size=entry.wave_evidence_size_bytes
    add("wave-evidence",entry.wave_evidence,size,task_id(entry),"wave-evidence",r.BLIND,collection)
    observed={} if observations is None else {v.wave_id:v for v in observations}
    for wave,pin,size in config.observations:
        add("wave-observation",pin,size,task_id(config),"waves."+wave,r.SEALED,observed.get(wave),scientific_role="HISTORY")
    links.append(RecursiveInputLink("edge."+task_id(config)+".entry",task_id(config),"entry",
        producer_node_id=task_id(entry),producer_output_id="product",scientific_role="HISTORY"))
    return tuple(sorted(((task_id(entry),entry),(task_id(config),config)))),tuple(sorted(external,key=lambda v:v.input_id)),tuple(sorted(links,key=lambda v:v.edge_id)),tuple(sorted(records)),()


def validate_phase_collect_scope(config,context,entry):
    configs=tuple(v.record for v in context.config_inputs if type(v.record) is SelectedE4PhaseCollectConfig)
    if len(configs)!=1:raise ValueError("selected E4 full phase requires one actual all-wave collector")
    collector=configs[0]
    expected_configs,external,links,_,_=_phase_contract_rows(entry,collector)
    ids={v[0] for v in expected_configs}
    if (tuple((v.node_id,v.record) for v in context.config_inputs if v.node_id in ids)!=expected_configs
            or tuple(v for v in context.links if v.consumer_node_id in ids)!=links
            or tuple(v for v in context.external_inputs if v.input_id in {x.input_id for x in external})!=external
            or task_id(config)!=context.node_id or context.stage is not stage(config.phase)
            or context.unit_ids!=entry.programme.group_ids or context.complete_unit_census
            or context.outcome_access is not access(config.phase) or context.visibility_ceiling is not r.PROSPECTIVE):
        raise ValueError("selected E4 phase collector changes original all-wave custody links or access")
