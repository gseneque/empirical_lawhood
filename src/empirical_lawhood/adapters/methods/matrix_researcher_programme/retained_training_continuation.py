# SPDX-License-Identifier: MPL-2.0
"""Explicit source-only continuation after complete original TRAIN custody.

Original scientific records and producer identities remain immutable. This
selection authorizes no acquisition, issue, reveal, or scientific conclusion.
"""
from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs,
)
from empirical_lawhood.runtime.native_training_export import NativeTrainingExportAdoptionSelection
from .known_inputs import MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput
from .selection import MatrixContinuedProgrammeSpecification, MatrixResearchProgrammePlan, MatrixProgrammePhaseBinding
from .source_continuation import validate_continued_inputs

PROTOCOL_ID = 'matrix.programme.retained-training-continuation'
CONTINUATION_FILENAME = 'retained-training-continuation.json'
RETAINED_PHASES = ('e1', 'e2', 'train')


@dataclass(frozen=True, slots=True)
class MatrixProgrammeRetainedTrainingContinuationSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/retained-training-continuation-specification'
    specification_id: str
    predecessor: MatrixProgrammePublishedInput
    directory: str

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        validate_relative_locator(self.directory)
        if type(self.predecessor) is not MatrixProgrammePublishedInput:
            raise TypeError('retained TRAIN continuation requires its exact predecessor publication')
        self.predecessor.__post_init__()
        self.predecessor.require_kind(MatrixResearchProgrammePlan)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class MatrixRetainedTrainingSource(CanonicalRecord):
    """Blind source lineage; the untrusted bank locator is reauthenticated on use."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/retained-training-source'
    REQUEST_TYPE: ClassVar[type] = MatrixProgrammeRetainedTrainingContinuationSpecification
    record_id: str
    predecessor: MatrixProgrammePublishedInput
    input_commitments: MatrixProgrammePublishedInput
    training_locator: MatrixFiniteDtTrainingLocator
    export_adoption: NativeTrainingExportAdoptionSelection
    target_provenance: ObjectIdentity
    continuation_request: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.predecessor, MatrixResearchProgrammePlan),
                (self.input_commitments, MatrixProgrammeInputCommitments)):
            if type(value) is not MatrixProgrammePublishedInput:
                raise TypeError('retained TRAIN source requires exact original published operands')
            value.__post_init__()
            value.require_kind(kind)
        if (type(self.training_locator) is not MatrixFiniteDtTrainingLocator
                or type(self.export_adoption) is not NativeTrainingExportAdoptionSelection):
            raise TypeError('retained TRAIN source requires its exact original locator and adoption selection')
        self.training_locator.__post_init__()
        self.export_adoption.__post_init__()
        for value, kind in ((self.target_provenance, NumericalProducingProvenance),
                (self.continuation_request, self.REQUEST_TYPE)):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise TypeError('retained TRAIN source changes its source or continuation type')
            value.__post_init__()
        locator, adoption = self.training_locator, self.export_adoption
        if (locator.authored_directory, locator.run_id, locator.packet, locator.execution_plan) != (
                adoption.authored_directory, adoption.run_id, adoption.packet, adoption.execution_plan):
            raise ValueError('retained TRAIN source substitutes its exact original producing run')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def artifact(self):
        return ArtifactIdentity(self.record_id, 'retained-training-source', self.SCHEMA,
            self.fingerprint(), 'application/json', len(self.canonical_bytes()))


@dataclass(frozen=True, slots=True)
class MatrixProgrammeRetainedTrainingContinuation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/retained-training-continuation'
    record_id: str
    specification: MatrixProgrammeRetainedTrainingContinuationSpecification
    target_plan: MatrixResearchProgrammePlan
    predecessor_bindings: tuple[tuple[str, ObjectIdentity], ...]
    predecessor_terminals: tuple[tuple[str, ObjectIdentity], ...]
    retained_training: MatrixRetainedTrainingSource

    def __post_init__(self):
        from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent
        validate_stable_id(self.record_id)
        if (type(self.specification) is not MatrixProgrammeRetainedTrainingContinuationSpecification
                or type(self.target_plan) is not MatrixResearchProgrammePlan
                or type(self.retained_training) is not MatrixRetainedTrainingSource):
            raise TypeError('retained TRAIN continuation requires exact selected lineage records')
        for value in (self.specification, self.target_plan, self.retained_training):
            value.__post_init__()
        target = self.target_plan.specification
        if (type(target) is not MatrixContinuedProgrammeSpecification
                or target.directory != self.specification.directory
                or target.predecessor != self.specification.predecessor
                or target.continuation_request != self.specification.identity
                or self.retained_training.predecessor != self.specification.predecessor
                or self.retained_training.continuation_request != self.specification.identity):
            raise ValueError('retained TRAIN continuation changes its exact target or predecessor')
        for rows, kinds in ((self.predecessor_bindings, (MatrixProgrammePhaseBinding,) * 3),
                (self.predecessor_terminals, (RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent,
                    DevelopmentRunRecoveryTerminalEvent))):
            if type(rows) is not tuple or tuple(phase for phase, _ in rows) != RETAINED_PHASES:
                raise ValueError('retained TRAIN continuation requires all original E1/E2/TRAIN records')
            for (_, pin), kind in zip(rows, kinds, strict=True):
                if type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION):
                    raise ValueError('retained TRAIN continuation changes its original record types')
                pin.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def retained_source_files(commitments):
    schemas = {kind.SCHEMA for kind in retained_source_types()}
    return tuple(row for row in commitments.support_files if row[0].payload_schema in schemas)


def retained_source_types():
    from .retained_e3_continuation import MatrixE3RetainedTrainingSource
    from .e3_closeout import MatrixE3ClosedTrainingSource
    return MatrixRetainedTrainingSource, MatrixE3RetainedTrainingSource, MatrixE3ClosedTrainingSource


def validate_retained_inputs(original, continued, retained):
    """Prove that only source provenance and its explicit lineage have changed."""
    if type(retained) not in retained_source_types():
        raise TypeError('retained TRAIN continuation requires its actual typed source lineage')
    retained.__post_init__()
    retained.input_commitments.require_record(original.commitments,
        ObjectIdentity.from_record(original.commitments.record_id, original.commitments))
    rows = retained_source_files(continued.commitments)
    if (retained_source_files(original.commitments) or len(rows) != 1 or rows[0][0] != retained.artifact
            or continued.producing_provenance.identity != retained.target_provenance
            or original.producing_provenance == continued.producing_provenance):
        raise PermissionError('retained TRAIN continuation changes original lineage or lacks an actual source transition')
    reduced = replace(continued, commitments=replace(continued.commitments,
        support_files=tuple(row for row in continued.commitments.support_files if row != rows[0])))
    validate_continued_inputs(original, reduced)


def bind_inputs(specification, records, **kwargs):
    if type(specification) is not MatrixProgrammeRetainedTrainingContinuationSpecification:
        raise TypeError('retained TRAIN continuation requires its exact copied specification')
    specification.__post_init__()
    if records or kwargs.get('files'):
        raise ValueError('retained TRAIN continuation derives all science and bank locators from original custody')
    return PreparedExperimentInputs({}, None)


def prepare(specification, *, execution, **_kwargs):
    bind_inputs(specification, {})
    execution.__post_init__()
    missing = [ExperimentDependency('matrix.retained-training.original-custody', DependencyKind.EXTERNAL_INPUT,
        'Use experiment-derive-inputs to authenticate complete original E1/E2/TRAIN and unentered later children.')]
    for name, kind in (('workers', DependencyKind.ENVIRONMENT), ('environment_id', DependencyKind.ENVIRONMENT),
            ('source_snapshot', DependencyKind.ENVIRONMENT), ('output_root', DependencyKind.STORAGE)):
        if getattr(execution, name) is None:
            missing.append(ExperimentDependency('matrix.retained-training.execution.' + name.replace('_', '-'), kind,
                'Select explicit ' + name + ' for the new source-bound programme.'))
    return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0),
        tuple(sorted(missing, key=lambda row: row.code)), execution=execution, specification_record=specification)
