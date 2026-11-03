# SPDX-License-Identifier: MPL-2.0
"""Compact current E3 prefix products, without qualification or authority.

Native expectations come from the actual bound original source and current
configuration. These metadata joins neither authenticate stored publications
nor perform native work. Causal products contain no checkpoint or RNG state.
"""

from dataclasses import dataclass
from types import SimpleNamespace
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import validate_trace
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import (
    METHODS as FACTOR_METHODS, MatrixParameterFactorControl, MatrixParameterFactorNumericalDesign,
    expected_members as diagnostic_members,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import (
    METHODS, MatrixParameterHistoryControl, MatrixParameterNumericalDesign, coordinate_identity, expected_members,
)
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ResolvedScheduledSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import compact_identity
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition, NativeSubworkOutput

from .configured_protected_specification import ConfiguredProtectedE3Specification as MatrixResponseErrorSpecification
from .configured_protected_source_records import (
    ProtectedE3NativeSourceManifest, ConfiguredProtectedE3SourceConfig, ProtectedE3SourcePhase, _reference,
    bind_protected_e3_source, identity, prefix_native_operation_id, source_task_id,
)


def protected_prefix_native_contract(config: ConfiguredProtectedE3SourceConfig, manifest: ProtectedE3NativeSourceManifest,
        *, specification: MatrixResponseErrorSpecification):
    """Derived native metadata only, never an effect definition or a grant."""
    source = bind_protected_e3_source(config, manifest, specification=specification)
    if config.phase is not ProtectedE3SourcePhase.PREFIX:
        raise ValueError("protected E3 prefix requires its exact current prefix configuration")
    if source.policy.cutoff_tick != specification.measurement.origin_tick:
        raise ValueError("protected E3 prefix changes the selected original causal cutoff")
    sources = tuple(sorted((compact_identity(config.source), identity(manifest), specification.identity,
        coordinate_identity(source.coordinate), source.provenance.identity), key=lambda row: row.object_id))
    outputs = (NativeSubworkOutput("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),
        NativeSubworkOutput("checkpoint", scheduled.ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"))
    return (source, identity(config), source_task_id(source.root_id, ProtectedE3SourcePhase.PREFIX),
        prefix_native_operation_id(), sources, outputs)


def _exact(value, kind):
    if type(value) is not kind:
        raise TypeError("protected E3 prefix requires exact original or current record types")
    value.__post_init__()


def _source(source):
    _exact(source, ResolvedScheduledSource)
    if source.root.root.role not in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION):
        raise ValueError("protected E3 prefix cannot acquire reserved transfer or exposed roots")


def _arrays(arrays, source_reference, role):
    _exact(arrays, scheduled.ScheduledArrays)
    if arrays.source != source_reference or arrays.role != role:
        raise ValueError("protected E3 prefix substitutes array phase or original source")


def _members(arrays, expected, producers):
    if ({member.name: (member.dtype, member.shape) for member in arrays.members} != expected
            or arrays.producers != tuple(sorted(producers, key=lambda row: row.object_id))):
        raise ValueError("protected E3 prefix thins complete array members or changes exact producers")


def _native_members(source):
    return expected_members(SimpleNamespace(total_ticks=source.policy.cutoff_tick))


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3PrefixHistory(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-prefix-history"
    record_id: str
    source: ObjectIdentity
    configuration: ObjectIdentity
    arrays: scheduled.ScheduledArrays
    checkpoint: scheduled.ScheduledCheckpoint
    native: scheduled.ScheduledNativeEvidence

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _reference(self.source, scheduled.ScheduledSource)
        _reference(self.configuration, ConfiguredProtectedE3SourceConfig)
        _arrays(self.arrays, self.source, "PREFIX")
        _exact(self.checkpoint, scheduled.ScheduledCheckpoint)
        _exact(self.native, scheduled.ScheduledNativeEvidence)
        _exact(self.native.definition, NativeSubworkDefinition)
        _exact(self.native.completion, NativeSubworkCompletion)
        _exact(self.native.receipt, CanonicalTaskReceipt)
        if self.checkpoint.source != self.source or self.native.definition.configuration != self.configuration:
            raise ValueError("protected E3 prefix substitutes its original checkpoint or current configuration")

    def validate_source(self, config: ConfiguredProtectedE3SourceConfig, manifest: ProtectedE3NativeSourceManifest,
            *, specification: MatrixResponseErrorSpecification) -> ResolvedScheduledSource:
        self.__post_init__()
        source, configuration, parent_task, operation, sources, _ = protected_prefix_native_contract(
            config, manifest, specification=specification)
        if self.configuration != configuration:
            raise ValueError("protected E3 prefix substitutes its actual current configuration")
        self.checkpoint.validate_source(source, self.arrays)
        scheduled._validate_prefix_native_evidence(self, source, configuration=configuration,
            parent_task=parent_task, operation=operation, native_sources=set(sources))
        _members(self.arrays, _native_members(source), (scheduled.identity(source), coordinate_identity(source.coordinate)))
        return source


def _history(source, history):
    _source(source)
    _exact(history, ConfiguredProtectedE3PrefixHistory)
    if history.source != scheduled.identity(source):
        raise ValueError("protected E3 prefix product substitutes its complete original source")
    history.checkpoint.validate_source(source, history.arrays)
    _members(history.arrays, _native_members(source), (scheduled.identity(source), coordinate_identity(source.coordinate)))


def _witness_source(source, witness):
    _source(source)
    _exact(witness, ConfiguredProtectedE3PrefixWitness)
    rule = source.policy.factor_rule
    if (witness.source != scheduled.identity(source) or witness.policy != scheduled.identity(source.policy)
            or tuple((t.view, t.sector) for t in witness.traces) != tuple((v, s) for v in ("PRIMARY", "FINE") for s in rule.sectors)):
        raise ValueError("protected E3 witness changes original complete source, policy, view or sector census")
    for trace in witness.traces:
        validate_trace(trace, rule)
    _members(witness.arrays, diagnostic_members(rule), (witness.source, witness.history, witness.numerical))


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3NumericalAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-prefix-numerical-assessment"
    record_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _reference(self.source, scheduled.ScheduledSource)
        _reference(self.history, ConfiguredProtectedE3PrefixHistory)
        _reference(self.numerical_design, MatrixParameterNumericalDesign)
        if type(self.controls) is not tuple or len(self.controls) != len(METHODS):
            raise ValueError("protected E3 numerical assessment omits original four controls")
        for control in self.controls:
            _exact(control, MatrixParameterHistoryControl)
        n = self.controls[0].denominator_steps
        if (tuple(c.control_id for c in self.controls) != METHODS
                or tuple((c.denominator_steps, c.denominator_real_coordinates) for c in self.controls) !=
                   ((n, 192), (2*n, 192), (n, 192), (n, 96))
                or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition == "SATISFIED" for c in self.controls)):
            raise ValueError("protected E3 numerical assessment changes complete native denominators or verdicts")

    def validate_source(self, source, history):
        self.__post_init__()
        _history(source, history)
        n, design = source.policy.cutoff_tick, source.numerical_design
        if (self.source != scheduled.identity(source) or self.history != identity(history)
                or self.numerical_design != scheduled.identity(design)
                or tuple((c.denominator_steps, c.denominator_real_coordinates, c.tolerance) for c in self.controls) !=
                   ((n, 192, design.trajectory_tolerance), (2*n, 192, design.trajectory_tolerance),
                    (n, 192, design.bridge_tolerance), (n, 96, design.trajectory_tolerance))):
            raise ValueError("protected E3 numerical assessment substitutes original history, design or cutoff")


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3PrefixWitness(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-prefix-witness"
    record_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical: ObjectIdentity
    policy: ObjectIdentity
    traces: tuple[scheduled.ScheduledPrefixTrace, ...]
    arrays: scheduled.ScheduledArrays

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for reference, kind in ((self.source, scheduled.ScheduledSource), (self.history, ConfiguredProtectedE3PrefixHistory),
                (self.numerical, ConfiguredProtectedE3NumericalAssessment), (self.policy, scheduled.ScheduledPrefixPolicy)):
            _reference(reference, kind)
        _arrays(self.arrays, self.source, "PREFIX_DIAGNOSTICS")
        if type(self.traces) is not tuple or not self.traces:
            raise ValueError("protected E3 witness omits original causal traces")
        for trace in self.traces:
            _exact(trace, scheduled.ScheduledPrefixTrace)
        if tuple((trace.view, trace.sector) for trace in self.traces) != (
                ("PRIMARY", "X"), ("PRIMARY", "Y"), ("FINE", "X"), ("FINE", "Y")):
            raise ValueError("protected E3 witness omits complete paired views or both sectors")

    def validate_source(self, source, history, numerical):
        self.__post_init__()
        _exact(numerical, ConfiguredProtectedE3NumericalAssessment)
        numerical.validate_source(source, history)
        if (self.source != scheduled.identity(source) or self.history != identity(history)
                or self.numerical != identity(numerical) or self.policy != scheduled.identity(source.policy)):
            raise ValueError("protected E3 witness substitutes its original source, policy or numerical record")
        _witness_source(source, self)


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3FrameAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-prefix-frame-assessment"
    record_id: str
    source: ObjectIdentity
    witness: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterFactorControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _reference(self.source, scheduled.ScheduledSource)
        _reference(self.witness, ConfiguredProtectedE3PrefixWitness)
        _reference(self.numerical_design, MatrixParameterFactorNumericalDesign)
        if type(self.controls) is not tuple or len(self.controls) != len(FACTOR_METHODS):
            raise ValueError("protected E3 frame assessment omits original six controls")
        for control in self.controls:
            _exact(control, MatrixParameterFactorControl)
        n = len(self.controls[0].measured_errors)
        if (tuple(c.method for c in self.controls) != FACTOR_METHODS
                or tuple(len(c.measured_errors) for c in self.controls) != (n, 15*n, n, n, n, n)
                or tuple(c.denominator_real_coordinates for c in self.controls) != (225, 15, 225, 225, 48, 1)
                or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition in ("SATISFIED", "NOT_APPLICABLE") for c in self.controls)):
            raise ValueError("protected E3 frame assessment changes full eigenpair denominators or verdicts")

    def validate_source(self, source, witness):
        self.__post_init__()
        _witness_source(source, witness)
        design, rule = source.policy.factor_numerical_design, source.policy.factor_rule
        n = 2*len(rule.sectors)*len(rule.lattice)
        tolerances = (design.operator_tolerance, design.eigenpair_tolerance, design.orthogonality_tolerance,
            design.projector_tolerance, design.factor_tolerance, design.scalar_tolerance)
        if (self.source != scheduled.identity(source) or witness.source != self.source
                or self.witness != identity(witness) or witness.policy != scheduled.identity(source.policy)
                or self.numerical_design != scheduled.identity(design)
                or tuple(len(c.measured_errors) for c in self.controls) != (n, 15*n, n, n, n, n)
                or tuple(c.tolerance for c in self.controls) != tolerances):
            raise ValueError("protected E3 frame assessment substitutes original source, lattice or design")


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3CausalPrefix(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-causal-prefix"
    record_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical: ObjectIdentity
    witness: ObjectIdentity
    frame_assessment: ObjectIdentity
    policy: ObjectIdentity
    root: MatrixProgrammeRoot
    cutoff_tick: int
    frame_sha256: str | None
    disposition: str
    reason: str | None
    arrays: scheduled.ScheduledArrays

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for reference, kind in ((self.source, scheduled.ScheduledSource), (self.history, ConfiguredProtectedE3PrefixHistory),
                (self.numerical, ConfiguredProtectedE3NumericalAssessment), (self.witness, ConfiguredProtectedE3PrefixWitness),
                (self.frame_assessment, ConfiguredProtectedE3FrameAssessment), (self.policy, scheduled.ScheduledPrefixPolicy)):
            _reference(reference, kind)
        _exact(self.root, MatrixProgrammeRoot)
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        _arrays(self.arrays, self.source, "CAUSAL_STATE")
        if (self.root.role not in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION)
                or type(self.cutoff_tick) is not int or self.cutoff_tick < 1
                or self.disposition not in ("AVAILABLE", "NO_ORIGIN", "UNEVALUABLE")
                or (self.disposition == "AVAILABLE") != (self.frame_sha256 is not None and self.reason is None)
                or self.disposition != "AVAILABLE" and self.frame_sha256 is not None
                or self.disposition != "AVAILABLE" and self.reason is None):
            raise ValueError("protected E3 causal prefix changes cutoff, role or missingness")
        members = expected_members(SimpleNamespace(total_ticks=self.cutoff_tick))
        members = {name: value for name, value in members.items() if not name.endswith("innovations")}
        members["frame"] = ("<c16", (3, 4, 4))
        _members(self.arrays, members, (self.source, self.history, self.witness, self.frame_assessment))
        frame = next(member for member in self.arrays.members if member.name == "frame")
        if (frame.finite_required != (self.disposition == "AVAILABLE")
                or self.disposition == "AVAILABLE" and frame.sha256 != self.frame_sha256
                or any(not member.finite_required for member in self.arrays.members if member.name != "frame")):
            raise ValueError("protected E3 causal prefix changes finite frame or phase metadata")

    def validate_source(self, source, history, numerical, witness, assessment):
        self.__post_init__()
        _exact(witness, ConfiguredProtectedE3PrefixWitness)
        witness.validate_source(source, history, numerical)
        _exact(assessment, ConfiguredProtectedE3FrameAssessment)
        assessment.validate_source(source, witness)
        if (self.source != scheduled.identity(source) or self.history != identity(history)
                or self.numerical != identity(numerical) or self.witness != identity(witness)
                or self.frame_assessment != identity(assessment) or self.policy != scheduled.identity(source.policy)
                or self.root != source.root.root or self.cutoff_tick != source.policy.cutoff_tick):
            raise ValueError("protected E3 causal prefix substitutes original root, role, cutoff or immutable products")
        observation = next(trace for trace in witness.traces if trace.view == "PRIMARY" and trace.sector == source.policy.origin_sector).observations[-1]
        valid = {
            "PREFIX_NUMERICAL_CONTROLS_NOT_SATISFIED": not numerical.numerical_pass or not assessment.numerical_pass,
            "CAUSAL_CUTOFF_OBSERVATION_UNAVAILABLE": numerical.numerical_pass and assessment.numerical_pass and observation.raw_admitted is None,
            "DECLARED_CUTOFF_NOT_CAUSALLY_ADMITTED": numerical.numerical_pass and assessment.numerical_pass and observation.raw_admitted is not None
                and (observation.causal_admitted is not True or observation.alignment_ambiguous),
            None: numerical.numerical_pass and assessment.numerical_pass and observation.raw_admitted is not None
                and observation.causal_admitted is True and not observation.alignment_ambiguous,
        }
        expected_disposition = ("AVAILABLE" if self.reason is None else "NO_ORIGIN"
            if self.reason == "DECLARED_CUTOFF_NOT_CAUSALLY_ADMITTED" else "UNEVALUABLE")
        if not valid.get(self.reason, False) or self.disposition != expected_disposition:
            raise ValueError("protected E3 causal prefix changes original cutoff admission or nonuse semantics")
