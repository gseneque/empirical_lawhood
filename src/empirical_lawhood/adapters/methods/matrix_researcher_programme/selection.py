# SPDX-License-Identifier: MPL-2.0
"""The sole current whole Matrix programme, rooted in immutable known inputs C."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs,
)

from .e4_operations import MatrixProgrammeE4Access
from .known_inputs import MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput, MatrixProgrammeProducedInput
from .operations import MatrixProgrammeE3Operations, MatrixProgrammeOperations
from .prepared_operations import MatrixProgrammePreparedAccess

PROTOCOL_ID = 'matrix.researcher-programme.v2'
CONTINUED_PROTOCOL_ID = 'matrix.researcher-programme.continued.v1'
AMENDED_PROTOCOL_ID = 'matrix.researcher-programme.curve-amended.v1'
PREPARATION_CONTEXT = 'matrix.programme.preparation-context'


@dataclass(frozen=True, slots=True)
class MatrixResearchProgrammeSpecification(CanonicalRecord):
    """Original science is selected once through C, never through a mutable slot."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/specification'
    VERSION: ClassVar[str] = '4.0.0'
    specification_id: str
    directory: str
    input_commitments: MatrixProgrammePublishedInput
    operations: MatrixProgrammeOperations

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        validate_relative_locator(self.directory)
        if type(self.input_commitments) is not MatrixProgrammePublishedInput or type(self.operations) is not MatrixProgrammeOperations:
            raise TypeError('Matrix programme requires its actual C publication and typed current operations')
        self.input_commitments.__post_init__()
        self.input_commitments.require_kind(MatrixProgrammeInputCommitments)
        self.operations.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class MatrixContinuedProgrammeSpecification(MatrixResearchProgrammeSpecification):
    """The continuation link is required science lineage, never an optional file."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/continued-specification'
    VERSION: ClassVar[str] = '1.0.0'
    predecessor: MatrixProgrammePublishedInput
    continuation_request: ObjectIdentity

    def __post_init__(self):
        MatrixResearchProgrammeSpecification.__post_init__(self)
        from .source_continuation import MatrixProgrammeSourceContinuationSpecification, MatrixProgrammeOutputContinuationSpecification
        from .retained_training_continuation import MatrixProgrammeRetainedTrainingContinuationSpecification
        from .retained_e3_continuation import MatrixProgrammeRetainedE3ContinuationSpecification
        from .e3_closeout import MatrixProgrammeE3CloseoutSpecification
        if type(self.predecessor) is not MatrixProgrammePublishedInput or type(self.continuation_request) is not ObjectIdentity:
            raise TypeError('continued programme requires its exact predecessor publication and original continuation request')
        self.predecessor.__post_init__()
        self.predecessor.require_kind(MatrixResearchProgrammePlan)
        self.continuation_request.__post_init__()
        if (self.continuation_request.object_schema, self.continuation_request.object_version) not in tuple(
                (kind.SCHEMA, kind.VERSION) for kind in (MatrixProgrammeSourceContinuationSpecification,
                    MatrixProgrammeOutputContinuationSpecification,
                    MatrixProgrammeRetainedTrainingContinuationSpecification, MatrixProgrammeRetainedE3ContinuationSpecification,
                    MatrixProgrammeE3CloseoutSpecification)):
            raise ValueError('continued programme changes its exact source-continuation request type')


@dataclass(frozen=True, slots=True)
class MatrixCurveAmendedProgrammeSpecification(MatrixResearchProgrammeSpecification):
    """Required prospective science lineage, separate from a source-only change."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/curve-amended-specification'
    VERSION: ClassVar[str] = '1.0.0'
    predecessor: MatrixProgrammePublishedInput
    amendment_request: ObjectIdentity

    def __post_init__(self):
        MatrixResearchProgrammeSpecification.__post_init__(self)
        from .curve_amendment import MatrixProgrammeCurveAmendmentSpecification
        if type(self.predecessor) is not MatrixProgrammePublishedInput or type(self.amendment_request) is not ObjectIdentity:
            raise TypeError('amended programme requires its exact original plan and selected prospective amendment')
        self.predecessor.__post_init__()
        self.predecessor.require_kind(MatrixResearchProgrammePlan)
        self.amendment_request.__post_init__()
        if (self.amendment_request.object_schema, self.amendment_request.object_version) != (
                MatrixProgrammeCurveAmendmentSpecification.SCHEMA, MatrixProgrammeCurveAmendmentSpecification.VERSION):
            raise ValueError('amended programme changes its exact prospective amendment type')


@dataclass(frozen=True, slots=True)
class MatrixResearchProgrammePlan(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/plan'
    VERSION: ClassVar[str] = '3.0.0'
    record_id: str
    specification: MatrixResearchProgrammeSpecification | MatrixContinuedProgrammeSpecification | MatrixCurveAmendedProgrammeSpecification
    workers: int
    environment_id: str
    source_snapshot: ObjectIdentity
    output_root: str

    def __post_init__(self):
        from pathlib import PurePosixPath
        validate_stable_id(self.record_id)
        validate_stable_id(self.environment_id)
        if (type(self.specification) not in (MatrixResearchProgrammeSpecification, MatrixContinuedProgrammeSpecification,
                MatrixCurveAmendedProgrammeSpecification)
                or type(self.source_snapshot) is not ObjectIdentity
                or type(self.workers) is not int or self.workers < 1
                or type(self.output_root) is not str or not PurePosixPath(self.output_root).is_absolute()
                or '..' in PurePosixPath(self.output_root).parts):
            raise TypeError('Matrix programme requires its exact original and selected execution settings')
        self.specification.__post_init__()
        self.source_snapshot.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammePhaseBinding(CanonicalRecord):
    """Actual immutable derivation output; this record claims no task completion."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/phase-binding'
    record_id: str
    programme: ObjectIdentity
    phase: str
    protocol_id: str
    specification: ExperimentInputBinding
    sources: ExperimentInputBinding
    requirements_publication: ArtifactWriteResult
    publications: tuple[ArtifactWriteResult, ...]

    def __post_init__(self):
        from .frontier import PHASES
        validate_stable_id(self.record_id)
        validate_stable_id(self.protocol_id)
        _programme_pin(self.programme)
        if self.phase not in PHASES:
            raise ValueError('Matrix binding selects an unsupported current phase')
        for value in (self.specification, self.sources):
            if type(value) is not ExperimentInputBinding:
                raise TypeError('Matrix phase binding requires actual bounded derivation outputs')
            value.__post_init__()
        if (type(self.requirements_publication) is not ArtifactWriteResult
                or type(self.publications) is not tuple or not self.publications
                or any(type(row) is not ArtifactWriteResult for row in self.publications)
                or self.requirements_publication not in self.publications):
            raise TypeError('Matrix phase binding must retain its actual complete derivation publications')
        paths = {}
        for value in self.publications:
            value.__post_init__()
            if paths.setdefault(value.materialization.relative_path, value) != value:
                raise ValueError('Matrix binding aliases different actual publications')
        if self.requirements_publication.logical.payload_schema != 'empirical-lawhood/operational/experiment-input-requirements':
            raise ValueError('Matrix binding changes its actual requirements publication schema')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeAuthoritySelection(CanonicalRecord):
    """Actual selected controls; the child owner replays their genuine authority."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/authority-selection'
    package_path: str
    reveal_authority_id: str
    parent_record_path: str | None = None
    parent_input_binding_paths: tuple[str, ...] = ()

    def __post_init__(self):
        validate_relative_locator(self.package_path)
        validate_stable_id(self.reveal_authority_id)
        if self.parent_record_path is not None:
            validate_relative_locator(self.parent_record_path)
        if (type(self.parent_input_binding_paths) is not tuple
                or self.parent_input_binding_paths != tuple(sorted(set(self.parent_input_binding_paths)))):
            raise ValueError('Matrix authority selection requires exact distinct sorted parent inputs')
        for path in self.parent_input_binding_paths:
            validate_relative_locator(path)


def _programme_pin(pin):
    if (type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version) !=
            (MatrixResearchProgrammePlan.SCHEMA, MatrixResearchProgrammePlan.VERSION)):
        raise ValueError('Matrix operation changes its actual current retained programme')
    pin.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixProgrammeOperationSelection(CanonicalRecord):
    """Later real access/issue selectors, separate from original D/C science."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/operation-selection'
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    programme: ObjectIdentity
    authorities: tuple[MatrixProgrammeAuthoritySelection, ...] = ()
    access: tuple[MatrixProgrammeE4Access | MatrixProgrammePreparedAccess, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _programme_pin(self.programme)
        if (type(self.authorities) is not tuple
                or any(type(row) is not MatrixProgrammeAuthoritySelection for row in self.authorities)
                or tuple(row.package_path for row in self.authorities) != tuple(sorted({row.package_path for row in self.authorities}))):
            raise ValueError('Matrix operation requires unique sorted actual issued package selections')
        if (type(self.access) is not tuple
                or any(type(row) not in (MatrixProgrammeE4Access, MatrixProgrammePreparedAccess) for row in self.access)
                or tuple(row.phase for row in self.access) != tuple(sorted({row.phase for row in self.access}))):
            raise ValueError('Matrix operation requires unique sorted current phase access selections')
        for value in (*self.authorities, *self.access):
            value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def access_for(self, phase):
        return next((row for row in self.access if row.phase == phase), None)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeRunBinding(CanonicalRecord):
    """Exact original run locator, not a claim that the run completed."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/run-binding'
    record_id: str
    programme: ObjectIdentity
    phase: str
    component_id: str
    specification: ObjectIdentity
    package: ObjectIdentity
    run_id: str
    authority: MatrixProgrammeAuthoritySelection

    def __post_init__(self):
        from .frontier import PHASES
        validate_stable_id(self.record_id)
        validate_stable_id(self.run_id)
        validate_stable_id(self.component_id)
        _programme_pin(self.programme)
        if self.phase not in PHASES or type(self.authority) is not MatrixProgrammeAuthoritySelection:
            raise ValueError('Matrix run binding requires an actual phase and original authority selector')
        for value in (self.specification, self.package):
            if type(value) is not ObjectIdentity:
                raise TypeError('Matrix run binding requires exact original specification/package identities')
            value.__post_init__()
        self.authority.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def input_record_types():
    return (MatrixProgrammeOperations, MatrixProgrammeE3Operations, MatrixProgrammeOperationSelection,
        MatrixProgrammePhaseBinding, MatrixProgrammeRunBinding, MatrixProgrammeProducedInput)


def programme_protocol(specification):
    if type(specification) is MatrixCurveAmendedProgrammeSpecification:
        return AMENDED_PROTOCOL_ID
    if type(specification) is MatrixContinuedProgrammeSpecification:
        return CONTINUED_PROTOCOL_ID
    if type(specification) is not MatrixResearchProgrammeSpecification:
        raise TypeError('Matrix programme requires its exact current C-pinned specification')
    return PROTOCOL_ID


def bind_inputs(specification, records, **kwargs):
    programme_protocol(specification)
    if records or kwargs.get('files'):
        raise ValueError('Matrix programme selects its original C and typed operations; no component/task map inputs')
    return PreparedExperimentInputs({}, None)


def prepare(specification, *, execution, **kwargs):
    programme_protocol(specification)
    specification.__post_init__()
    execution.__post_init__()
    missing = [ExperimentDependency(PREPARATION_CONTEXT, DependencyKind.ENVIRONMENT,
        'Use the selected programme service to authenticate the actual original C and operational selections.')]
    for name, kind in (('workers', DependencyKind.ENVIRONMENT), ('environment_id', DependencyKind.ENVIRONMENT),
            ('source_snapshot', DependencyKind.ENVIRONMENT), ('output_root', DependencyKind.STORAGE)):
        if getattr(execution, name) is None:
            missing.append(ExperimentDependency('matrix.programme.execution.' + name.replace('_', '-'), kind,
                'Select explicit ' + name + ' for the ordinary component owners.'))
    plan = None
    if all(getattr(execution, name) is not None for name in ('workers', 'environment_id', 'source_snapshot', 'output_root')):
        plan = MatrixResearchProgrammePlan('plan.' + specification.fingerprint(), specification,
            execution.workers, execution.environment_id, execution.source_snapshot, execution.output_root)
    return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0),
        tuple(sorted(missing, key=lambda row: row.code)), execution=execution,
        specification_record=specification, programme=plan)
