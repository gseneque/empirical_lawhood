# SPDX-License-Identifier: MPL-2.0
"""Explicit programme continuation after E3 fit and before future responses."""
from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import ConfiguredE3RetainedExecution
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_unfinished_execution import ConfiguredE3UnfinishedExecution
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs
from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent
from .known_inputs import MatrixProgrammePublishedInput
from .retained_training_continuation import MatrixRetainedTrainingSource, RETAINED_PHASES, retained_source_files
from .selection import MatrixContinuedProgrammeSpecification, MatrixProgrammePhaseBinding, MatrixProgrammeRunBinding, MatrixResearchProgrammePlan
from .source_continuation import validate_continued_inputs

PROTOCOL_ID = 'matrix.programme.retained-e3-continuation'
CONTINUATION_FILENAME = 'retained-e3-continuation.json'


@dataclass(frozen=True, slots=True)
class MatrixProgrammeRetainedE3ContinuationSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/retained-e3-continuation-specification'
    specification_id: str
    predecessor: MatrixProgrammePublishedInput
    directory: str
    continued_e3_run_id: str
    original_reveal_authority_id: str

    def __post_init__(self):
        for value in (self.specification_id, self.continued_e3_run_id, self.original_reveal_authority_id):
            validate_stable_id(value)
        validate_relative_locator(self.directory)
        if type(self.predecessor) is not MatrixProgrammePublishedInput:
            raise TypeError('retained E3 continuation requires its actual predecessor publication')
        self.predecessor.__post_init__()
        self.predecessor.require_kind(MatrixResearchProgrammePlan)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class MatrixE3RetainedTrainingSource(MatrixRetainedTrainingSource):
    """Keep the original TRAIN producer directly; do not recursively adopt it."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e3-retained-training-source'
    REQUEST_TYPE: ClassVar[type] = MatrixProgrammeRetainedE3ContinuationSpecification


def _reference(pin, kind):
    if type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError('retained E3 continuation changes an exact original record type')
    pin.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixProgrammeRetainedE3Continuation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/retained-e3-continuation'
    PREDECESSOR_TRAINING_TYPE: ClassVar[type] = MatrixRetainedTrainingSource
    REQUEST_TYPE: ClassVar[type] = MatrixProgrammeRetainedE3ContinuationSpecification
    TRAINING_TYPE: ClassVar[type] = MatrixE3RetainedTrainingSource
    record_id: str
    specification: MatrixProgrammeRetainedE3ContinuationSpecification
    target_plan: MatrixResearchProgrammePlan
    predecessor_bindings: tuple[tuple[str, ObjectIdentity], ...]
    predecessor_terminals: tuple[tuple[str, ObjectIdentity], ...]
    predecessor_e3_binding: ObjectIdentity
    predecessor_e3_run: ObjectIdentity
    predecessor_training: MatrixRetainedTrainingSource
    retained_training: MatrixE3RetainedTrainingSource
    retained_e3: ConfiguredE3RetainedExecution

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for record, kind in ((self.specification, self.REQUEST_TYPE),
                (self.target_plan, MatrixResearchProgrammePlan), (self.predecessor_training, self.PREDECESSOR_TRAINING_TYPE),
                (self.retained_training, self.TRAINING_TYPE), (self.retained_e3, ConfiguredE3RetainedExecution)):
            if type(record) is not kind:
                raise TypeError('retained E3 continuation requires its exact selected lineage records')
            record.__post_init__()
        target, request = self.target_plan.specification, self.specification
        if (type(target) is not MatrixContinuedProgrammeSpecification or target.directory != request.directory
                or target.predecessor != request.predecessor or target.continuation_request != request.identity
                or self.retained_e3.continued_run_id != request.continued_e3_run_id
                or self.predecessor_reveal_authority.object_id != request.original_reveal_authority_id
                or self.retained_training.continuation_request != request.identity
                or self.retained_training.target_provenance != self.retained_e3.response_provenance.identity):
            raise ValueError('retained E3 continuation changes its actual target, original reveal or source')
        old, new = self.predecessor_training, self.retained_training
        if (old.predecessor, old.input_commitments, old.training_locator, old.export_adoption) != (
                new.predecessor, new.input_commitments, new.training_locator, new.export_adoption):
            raise ValueError('retained E3 continuation substitutes its original acquired TRAIN')
        _reference(self.predecessor_e3_binding, MatrixProgrammePhaseBinding)
        _reference(self.predecessor_e3_run, MatrixProgrammeRunBinding)
        for rows, kinds in ((self.predecessor_bindings, (MatrixProgrammePhaseBinding,) * 3),
                (self.predecessor_terminals, (RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent,
                    DevelopmentRunRecoveryTerminalEvent))):
            if type(rows) is not tuple or tuple(role for role, _ in rows) != RETAINED_PHASES:
                raise ValueError('retained E3 continuation omits original E1/E2/TRAIN custody')
            for (_, pin), kind in zip(rows, kinds, strict=True):
                _reference(pin, kind)

    @property
    def predecessor_reveal_authority(self):
        return self.retained_e3.original_reveal_authority

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeUnfinishedE3Continuation(MatrixProgrammeRetainedE3Continuation):
    """Retain the original continued run and issue only its unfinished work."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/unfinished-e3-continuation'
    PREDECESSOR_TRAINING_TYPE: ClassVar[type] = MatrixE3RetainedTrainingSource
    predecessor_training: MatrixE3RetainedTrainingSource
    unfinished: ConfiguredE3UnfinishedExecution

    def __post_init__(self):
        if type(self.unfinished) is not ConfiguredE3UnfinishedExecution or self.unfinished.retention != self.retained_e3:
            raise ValueError('unfinished E3 programme changes its authenticated predecessor boundary')
        self.unfinished.__post_init__()
        super(MatrixProgrammeUnfinishedE3Continuation, self).__post_init__()

    @property
    def predecessor_reveal_authority(self):
        return self.unfinished.predecessor_reveal_authority


def validate_retained_e3_inputs(original, continued, original_training, retained):
    """Keep the B-to-C source transition separate from the original A TRAIN."""
    old_rows, new_rows = retained_source_files(original.commitments), retained_source_files(continued.commitments)
    from .e3_closeout import MatrixE3ClosedTrainingSource
    if (type(original_training) not in (MatrixRetainedTrainingSource, MatrixE3RetainedTrainingSource)
            or type(retained) not in (MatrixE3RetainedTrainingSource, MatrixE3ClosedTrainingSource)
            or len(old_rows) != 1 or len(new_rows) != 1
            or old_rows[0][0] != original_training.artifact or new_rows[0][0] != retained.artifact
            or retained.target_provenance != continued.producing_provenance.identity
            or original_training.target_provenance != original.producing_provenance.identity
            or (retained.predecessor, retained.input_commitments, retained.training_locator, retained.export_adoption) !=
                (original_training.predecessor, original_training.input_commitments,
                    original_training.training_locator, original_training.export_adoption)):
        raise PermissionError('retained E3 input transition changes original TRAIN or its target source')
    comparison = replace(continued, commitments=replace(continued.commitments,
        support_files=tuple(sorted((*tuple(row for row in continued.commitments.support_files if row != new_rows[0]),
            old_rows[0]), key=lambda row: row[0].artifact_id))))
    validate_continued_inputs(original, comparison)


def bind_inputs(specification, records, **kwargs):
    if type(specification) is not MatrixProgrammeRetainedE3ContinuationSpecification:
        raise TypeError('retained E3 continuation requires its exact copied specification')
    specification.__post_init__()
    if records or kwargs.get('files'):
        raise ValueError('retained E3 continuation derives every retained task and original producer from custody')
    return PreparedExperimentInputs({}, None)


def prepare(specification, *, execution, **_kwargs):
    bind_inputs(specification, {})
    execution.__post_init__()
    missing = [ExperimentDependency('matrix.retained-e3.original-custody', DependencyKind.EXTERNAL_INPUT,
        'Use experiment-derive-inputs to authenticate the original E3 prefix/fit and unentered future responses.')]
    for name, kind in (('workers', DependencyKind.ENVIRONMENT), ('environment_id', DependencyKind.ENVIRONMENT),
            ('source_snapshot', DependencyKind.ENVIRONMENT), ('output_root', DependencyKind.STORAGE)):
        if getattr(execution, name) is None:
            missing.append(ExperimentDependency('matrix.retained-e3.execution.' + name.replace('_', '-'), kind,
                'Select explicit ' + name + ' for the continued programme.'))
    return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0),
        tuple(sorted(missing, key=lambda row: row.code)), execution=execution, specification_record=specification)
