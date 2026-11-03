# SPDX-License-Identifier: MPL-2.0
"""Explicit continuation after entered CAL missingness and before CONF entry."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_closeout_execution import ConfiguredE3ClosedExecution
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs
from .retained_e3_continuation import MatrixE3RetainedTrainingSource, MatrixProgrammeRetainedE3Continuation, MatrixProgrammeRetainedE3ContinuationSpecification

PROTOCOL_ID = 'matrix.programme.e3-cal-closeout'


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE3CloseoutSpecification(MatrixProgrammeRetainedE3ContinuationSpecification):
    """Select original entered CAL custody; this request grants no repeat call."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e3-cal-closeout-specification'


@dataclass(frozen=True, slots=True)
class MatrixE3ClosedTrainingSource(MatrixE3RetainedTrainingSource):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e3-closed-training-source'
    REQUEST_TYPE: ClassVar[type] = MatrixProgrammeE3CloseoutSpecification


@dataclass(frozen=True, slots=True)
class MatrixProgrammeClosedE3Continuation(MatrixProgrammeRetainedE3Continuation):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/closed-e3-continuation'
    REQUEST_TYPE: ClassVar[type] = MatrixProgrammeE3CloseoutSpecification
    PREDECESSOR_TRAINING_TYPE: ClassVar[type] = MatrixE3RetainedTrainingSource
    TRAINING_TYPE: ClassVar[type] = MatrixE3ClosedTrainingSource
    specification: MatrixProgrammeE3CloseoutSpecification
    predecessor_training: MatrixE3RetainedTrainingSource
    retained_training: MatrixE3ClosedTrainingSource
    closeout: ConfiguredE3ClosedExecution

    def __post_init__(self):
        if type(self.closeout) is not ConfiguredE3ClosedExecution or self.closeout.retention != self.retained_e3:
            raise ValueError('CAL closeout programme changes its authenticated original execution')
        self.closeout.__post_init__()
        super(MatrixProgrammeClosedE3Continuation, self).__post_init__()

    @property
    def predecessor_reveal_authority(self):
        return self.closeout.predecessor_reveal_authority


def bind_inputs(specification, records, **kwargs):
    if type(specification) is not MatrixProgrammeE3CloseoutSpecification:
        raise TypeError('CAL closeout requires its explicit distinct specification')
    specification.__post_init__()
    if records or kwargs.get('files'):
        raise ValueError('CAL closeout derives every original contact, missing outcome and retained receipt from custody')
    return PreparedExperimentInputs({}, None)


def prepare(specification, *, execution, **_kwargs):
    bind_inputs(specification, {})
    execution.__post_init__()
    missing = [ExperimentDependency('matrix.e3-closeout.original-custody', DependencyKind.EXTERNAL_INPUT,
        'Use experiment-derive-inputs to authenticate entered CAL, its complete missingness census and untouched CONF.')]
    for name, kind in (('workers', DependencyKind.ENVIRONMENT), ('environment_id', DependencyKind.ENVIRONMENT),
            ('source_snapshot', DependencyKind.ENVIRONMENT), ('output_root', DependencyKind.STORAGE)):
        if getattr(execution, name) is None:
            missing.append(ExperimentDependency('matrix.e3-closeout.execution.' + name.replace('_', '-'), kind,
                'Select explicit ' + name + ' for the closed-CAL continuation.'))
    return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0),
        tuple(sorted(missing, key=lambda row: row.code)), execution=execution, specification_record=specification)
