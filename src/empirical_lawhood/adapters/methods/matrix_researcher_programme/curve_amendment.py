# SPDX-License-Identifier: MPL-2.0
"""Prospective curve/mechanism amendment after exposed E1/E2, before TRAIN.

The allocation exposure census remains an immutable original input. This
separate census identifies later E1/E2 exposure and the exact unentered stages.
Neither a design choice nor exposed explanatory analysis supplies authority.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs,
)
from .curve_amendment_design import CURVE_MECHANISM_AMENDMENT, MatrixCurveMechanismAmendmentRule, amend_curve_design
from .known_inputs import MatrixProgrammeProducedInput, MatrixProgrammePublishedInput, PHASE_INPUT_ROLES
from .selection import MatrixCurveAmendedProgrammeSpecification, MatrixResearchProgrammePlan
from .source_continuation import RETAINED_PHASES, MatrixProgrammeSourceContinuation, rebound_responses

PROTOCOL_ID = 'matrix.programme.curve-mechanism-amendment'
AMENDMENT_FILENAME = 'curve-mechanism-amendment.json'
ANALYSES = ('e2-mechanism', 'e2-mechanism-followup')
EVIDENCE_MEMBERS = ('completion', 'manifest', 'report', 'specification')
MAXIMUM_EVIDENCE_BYTES = 4 * 1024**2


def _pin(value):
    if type(value) is not ObjectIdentity:
        raise TypeError('amendment requires an exact original record identity')
    value.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixAmendmentEvidenceFile(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/amendment-evidence-file'
    path: str
    sha256: str
    size_bytes: int

    def __post_init__(self):
        if (type(self.path) is not str or not PurePosixPath(self.path).is_absolute()
                or '..' in PurePosixPath(self.path).parts or type(self.size_bytes) is not int
                or not 0 < self.size_bytes <= MAXIMUM_EVIDENCE_BYTES):
            raise ValueError('amendment evidence requires an explicit bounded absolute source file')
        validate_sha256(self.sha256)


@dataclass(frozen=True, slots=True)
class MatrixAmendmentAnalysisSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/amendment-analysis-selection'
    analysis: str
    files: tuple[tuple[str, MatrixAmendmentEvidenceFile], ...]

    def __post_init__(self):
        if (self.analysis not in ANALYSES or type(self.files) is not tuple
                or tuple(name for name, _ in self.files) != EVIDENCE_MEMBERS
                or any(type(value) is not MatrixAmendmentEvidenceFile for _, value in self.files)
                or len({value.path for _, value in self.files}) != len(self.files)):
            raise ValueError('amendment analysis drops its exact specification, manifest, completion or report')
        for _, value in self.files:
            value.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixAmendmentEvidenceSnapshot(CanonicalRecord):
    """Exact selected UTF-8 bytes, retained as exposed development evidence."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/amendment-evidence-snapshot'
    record_id: str
    analysis: str
    member: str
    original: MatrixAmendmentEvidenceFile
    utf8_text: str
    standing: str = 'POST_OUTCOME_EXPOSED_DEVELOPMENT_NO_CONFIRMATION_OR_QUALIFICATION'

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.analysis not in ANALYSES or self.member not in EVIDENCE_MEMBERS
                or type(self.original) is not MatrixAmendmentEvidenceFile or type(self.utf8_text) is not str
                or self.standing != 'POST_OUTCOME_EXPOSED_DEVELOPMENT_NO_CONFIRMATION_OR_QUALIFICATION'):
            raise ValueError('amendment snapshot changes its source or exposed explanatory standing')
        self.original.__post_init__()
        raw = self.utf8_text.encode('utf-8')
        if len(raw) != self.original.size_bytes or sha256(raw).hexdigest() != self.original.sha256:
            raise ValueError('amendment snapshot changes exact historical evidence bytes')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeCurveAmendmentSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/curve-amendment-specification'
    specification_id: str
    predecessor: MatrixProgrammePublishedInput
    directory: str
    rule: MatrixCurveMechanismAmendmentRule
    analyses: tuple[MatrixAmendmentAnalysisSelection, ...]
    withdrawn_derivations: tuple[MatrixProgrammePublishedInput, ...]

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        validate_relative_locator(self.directory)
        if type(self.predecessor) is not MatrixProgrammePublishedInput or self.rule != CURVE_MECHANISM_AMENDMENT:
            raise ValueError('curve amendment requires its exact original programme and fixed selected rule')
        self.predecessor.__post_init__()
        self.predecessor.require_kind(MatrixResearchProgrammePlan)
        self.rule.__post_init__()
        if (type(self.analyses) is not tuple or any(type(value) is not MatrixAmendmentAnalysisSelection for value in self.analyses)
                or tuple(value.analysis for value in self.analyses) != ANALYSES
                or type(self.withdrawn_derivations) is not tuple
                or any(type(value) is not MatrixProgrammePublishedInput for value in self.withdrawn_derivations)
                or tuple(value.record.object_id for value in self.withdrawn_derivations)
                    != tuple(sorted({value.record.object_id for value in self.withdrawn_derivations}))):
            raise ValueError('curve amendment changes the declared exposed analyses or withdrawn derivation census')
        for value in self.analyses:
            value.__post_init__()
        for value in self.withdrawn_derivations:
            value.__post_init__()
            value.require_kind(MatrixProgrammeSourceContinuation)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeAmendmentExposure(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/amendment-exposure-census'
    original_design: ObjectIdentity
    original_allocation_census: ObjectIdentity
    original_producing_provenance: ObjectIdentity
    phase_specifications: tuple[tuple[str, ObjectIdentity], ...]
    exposed_roots: tuple[tuple[str, tuple[str, ...]], ...]
    exposed_groups: tuple[tuple[str, tuple[str, ...]], ...]
    e2_protocols: tuple[tuple[str, ObjectIdentity], ...]
    dependent_reservations: tuple[tuple[str, ObjectIdentity], ...]

    def __post_init__(self):
        for value in (self.original_design, self.original_allocation_census, self.original_producing_provenance):
            _pin(value)
        for values, names in ((self.phase_specifications, RETAINED_PHASES),
                (self.dependent_reservations, PHASE_INPUT_ROLES[2:])):
            if type(values) is not tuple or tuple(name for name, _ in values) != names:
                raise ValueError('amendment exposure changes its complete original/future stage census')
            for _, pin in values:
                _pin(pin)
        for values in (self.exposed_roots, self.exposed_groups):
            if type(values) is not tuple or tuple(phase for phase, _ in values) != RETAINED_PHASES:
                raise ValueError('amendment exposure requires both complete original E1/E2 rosters')
            for _, rows in values:
                if type(rows) is not tuple or not rows or rows != tuple(sorted(set(rows))):
                    raise ValueError('amendment exposure drops or duplicates an original independent unit')
                for row in rows:
                    validate_stable_id(row)
        if tuple(root for root, _ in self.e2_protocols) != dict(self.exposed_roots)['e2']:
            raise ValueError('amendment exposure drops an original E2 protocol')
        for _, pin in self.e2_protocols:
            _pin(pin)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeCurveAmendment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/curve-mechanism-amendment'
    record_id: str
    specification: MatrixProgrammeCurveAmendmentSpecification
    target_plan: MatrixResearchProgrammePlan
    exposure: MatrixProgrammeAmendmentExposure
    predecessor_bindings: tuple[tuple[str, ObjectIdentity], ...]
    predecessor_terminals: tuple[tuple[str, ObjectIdentity], ...]
    unentered_training_packet: ObjectIdentity
    evidence: tuple[MatrixProgrammeProducedInput, ...]
    withdrawn_training_packets: tuple[tuple[ObjectIdentity, ObjectIdentity | None], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.specification) is not MatrixProgrammeCurveAmendmentSpecification
                or type(self.target_plan) is not MatrixResearchProgrammePlan
                or type(self.exposure) is not MatrixProgrammeAmendmentExposure):
            raise TypeError('curve amendment requires its actual complete selection, target and exposure census')
        for value in (self.specification, self.target_plan, self.exposure):
            value.__post_init__()
        target = self.target_plan.specification
        if (type(target) is not MatrixCurveAmendedProgrammeSpecification
                or target.predecessor != self.specification.predecessor or target.amendment_request != self.specification.identity
                or target.directory != self.specification.directory):
            raise ValueError('curve amendment loses its required target lineage')
        from .selection import MatrixProgrammePhaseBinding
        from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent
        from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
        for values, kinds in ((self.predecessor_bindings, (MatrixProgrammePhaseBinding,) * 2),
                (self.predecessor_terminals, (RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent))):
            if type(values) is not tuple or tuple(phase for phase, _ in values) != RETAINED_PHASES:
                raise ValueError('curve amendment drops the original E1/E2 binding or terminal')
            for (_, pin), kind in zip(values, kinds, strict=True):
                _pin(pin)
                if (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION):
                    raise ValueError('curve amendment changes the original custody record type')
        _pin(self.unentered_training_packet)
        if (self.unentered_training_packet.object_schema, self.unentered_training_packet.object_version) != (
                AuthoredRecursiveWave.SCHEMA, AuthoredRecursiveWave.VERSION):
            raise ValueError('curve amendment changes its unentered original TRAIN packet')
        if (type(self.evidence) is not tuple or len(self.evidence) != len(ANALYSES) * len(EVIDENCE_MEMBERS)
                or any(type(value) is not MatrixProgrammeProducedInput for value in self.evidence)
                or len({value.record for value in self.evidence}) != len(self.evidence)):
            raise ValueError('curve amendment drops its exact exposed evidence publications')
        for value in self.evidence:
            value.__post_init__()
            value.require_kind(MatrixAmendmentEvidenceSnapshot)
        if (type(self.withdrawn_training_packets) is not tuple
                or tuple(pin for pin, _ in self.withdrawn_training_packets)
                    != tuple(value.record for value in self.specification.withdrawn_derivations)):
            raise ValueError('curve amendment changes its complete withdrawn source-derivation census')
        for _, packet in self.withdrawn_training_packets:
            if packet is not None:
                _pin(packet)
                if (packet.object_schema, packet.object_version) != (AuthoredRecursiveWave.SCHEMA, AuthoredRecursiveWave.VERSION):
                    raise ValueError('curve amendment invents an unentered authored packet')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def amendment_exposure(original, bindings):
    phases = tuple(original.phase(role) for role in RETAINED_PHASES)
    roots = tuple((phase.role, tuple(sorted(root.root.root_id for root in phase.reservation.allocation.roots))) for phase in phases)
    groups = tuple((phase.role, tuple(sorted({root.root.independent_group_id for root in phase.reservation.allocation.roots}))) for phase in phases)
    return MatrixProgrammeAmendmentExposure(original.scientific_design.identity, original.commitments.exposure_census.record,
        original.producing_provenance.identity, tuple((role, bindings[role].specification.identity) for role in RETAINED_PHASES),
        roots, groups, tuple((protocol.public_source.root.root_id, ObjectIdentity.from_record(protocol.protocol_id, protocol))
            for protocol in original.phase('e2').responses.protocols),
        tuple((phase.role, original.commitments.phase(phase.role).reservation.record) for phase in original.phases[2:]))


def amended_e6_policy(original, phases, design):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import build_e6_transport_policy
    selected = {phase.role: phase for phase in phases}
    roles = (('CALIBRATION', 'e3.calibration'), ('EVALUATION', 'e3.confirmation'),
        ('TRANSFER_NEARBY', 'e6.nearby'), ('TRANSFER_SHIFTED', 'e6.shifted'))
    return build_e6_transport_policy(record_id=original.e6_policy.record_id, candidate_specification=design.e3,
        future_reservation=original.phase('e3.calibration').reservation,
        future_response_selections=tuple((role, selected[phase].responses) for role, phase in roles),
        availability=(original.commitments.availability.record, original.availability), criterion=design.e6_policy.criterion)


def validate_amended_inputs(original, amended):
    """Only the fixed new claim and source-bound protocols may change."""
    before, after = original.commitments, amended.commitments
    expected = amend_curve_design(original.scientific_design, record_id=amended.scientific_design.record_id)
    if amended.scientific_design != expected:
        raise PermissionError('curve amendment changes science outside the exact authorized endpoint and feature construction')
    if replace(after, record_id=before.record_id, scientific_design=before.scientific_design,
            producing_provenance=before.producing_provenance, phases=before.phases, e6_policy=before.e6_policy) != before:
        raise PermissionError('curve amendment changes original allocations, folds, streams, exposure, availability or support custody')
    if (original.exposure_census, original.exposure_audit, original.scalar_definitions, original.availability) != (
            amended.exposure_census, amended.exposure_audit, amended.scalar_definitions, amended.availability):
        raise PermissionError('curve amendment changes an immutable original non-source input')
    for previous, current in zip(original.phases, amended.phases, strict=True):
        if (current.role, current.reservation, current.native_specification) != (
                previous.role, previous.reservation, previous.native_specification):
            raise PermissionError('curve amendment reallocates or changes original native selections')
        old_handle, new_handle = before.phase(previous.role), after.phase(previous.role)
        if replace(new_handle, responses=old_handle.responses) != old_handle:
            raise PermissionError('curve amendment changes original reservation or native-selection publications')
        assay = expected.e2.assay if previous.role == 'e2' else expected.training_assay
        response = None if previous.responses is None else rebound_responses(previous, amended.producing_provenance, assay)
        if current.responses != response:
            raise PermissionError('curve amendment changes the original response task or future panel roster')
        if current.responses is not None and any(protocol.public_source.policy.cutoff_tick < 32 for protocol in current.responses.protocols):
            raise ValueError('curve amendment lacks its fixed past observation window before issue')
    if amended.e6_policy != amended_e6_policy(original, amended.phases, expected):
        raise PermissionError('curve amendment changes the frozen pre-TRAIN E6 policy')


def bind_inputs(specification, records, **kwargs):
    if type(specification) is not MatrixProgrammeCurveAmendmentSpecification:
        raise TypeError('curve amendment requires its exact copied specification')
    specification.__post_init__()
    if records or kwargs.get('files'):
        raise ValueError('curve amendment derives the fixed change from original custody, without replacement scientific operands')
    return PreparedExperimentInputs({}, None)


def prepare(specification, *, execution, **_kwargs):
    bind_inputs(specification, {})
    execution.__post_init__()
    dependencies = [ExperimentDependency('matrix.amendment.original-custody', DependencyKind.EXTERNAL_INPUT,
        'Use experiment-derive-inputs to bind exposed E1/E2 and analyses and authenticate every unentered dependent stage.')]
    for name, kind in (('workers', DependencyKind.ENVIRONMENT), ('environment_id', DependencyKind.ENVIRONMENT),
            ('source_snapshot', DependencyKind.ENVIRONMENT), ('output_root', DependencyKind.STORAGE)):
        if getattr(execution, name) is None:
            dependencies.append(ExperimentDependency('matrix.amendment.execution.' + name.replace('_', '-'), kind,
                'Select explicit ' + name + ' for the prospective amended programme.'))
    return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0),
        tuple(sorted(dependencies, key=lambda row: row.code)), execution=execution, specification_record=specification)
