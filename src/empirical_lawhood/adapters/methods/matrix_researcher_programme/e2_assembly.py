# SPDX-License-Identifier: MPL-2.0
"""Current E2 metadata-assembly intent from the whole programme inputs C.

Static preparation authenticates no external publication and starts no native
work. The ordinary derivation owner authenticates C before constructing the
existing native-utility specification and request.
"""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import NativeTrainingResources
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs,
)
from .known_inputs import MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput

PROTOCOL_ID = 'matrix.programme.e2-input-assembly'


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE2AssemblyRequest(CanonicalRecord):
    VERSION: ClassVar[str] = '2.0.0'
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e2-assembly-request'
    record_id: str
    resources: NativeTrainingResources
    campaign: CampaignSpec

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.resources, NativeTrainingResources), (self.campaign, CampaignSpec)):
            if type(value) is not kind:
                raise TypeError('programme E2 assembly requires explicit resources and campaign')
            value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE2AssemblySpecification(CanonicalRecord):
    VERSION: ClassVar[str] = '2.0.0'
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e2-assembly-specification'
    specification_id: str
    request: ObjectIdentity
    input_commitments: MatrixProgrammePublishedInput

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (type(self.request) is not ObjectIdentity or (self.request.object_schema, self.request.object_version)
                != (MatrixProgrammeE2AssemblyRequest.SCHEMA, MatrixProgrammeE2AssemblyRequest.VERSION)):
            raise ValueError('programme E2 assembly substitutes its exact current request edition')
        self.request.__post_init__()
        if type(self.input_commitments) is not MatrixProgrammePublishedInput:
            raise TypeError('programme assembly requires its actual programme commitment')
        self.input_commitments.__post_init__()
        self.input_commitments.require_kind(MatrixProgrammeInputCommitments)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


def validate_request(specification, request):
    if type(specification) is not MatrixProgrammeE2AssemblySpecification or type(request) is not MatrixProgrammeE2AssemblyRequest:
        raise TypeError('programme E2 assembly requires its exact current specification and operational request')
    specification.__post_init__()
    request.__post_init__()
    if specification.request != request.identity:
        raise ValueError('programme E2 assembly changes its frozen request')


def bind_inputs(specification, records, *, files=None):
    if type(specification) is not MatrixProgrammeE2AssemblySpecification:
        raise TypeError('programme E2 assembly requires its exact current specification')
    specification.__post_init__()
    if files or set(records) - {'request'}:
        raise ValueError('programme E2 assembly accepts only its current operational request')
    request = records.get('request')
    if request is not None:
        validate_request(specification, request)
    return PreparedExperimentInputs({}, request)


def prepare(specification, *, execution, method_inputs=None, **_kwargs):
    if type(specification) is not MatrixProgrammeE2AssemblySpecification:
        raise TypeError('programme E2 assembly requires its exact current specification')
    specification.__post_init__()
    dependencies = []
    for name, kind in (('workers', DependencyKind.ENVIRONMENT), ('environment_id', DependencyKind.ENVIRONMENT),
            ('source_snapshot', DependencyKind.ENVIRONMENT), ('output_root', DependencyKind.STORAGE)):
        if getattr(execution, name) is None:
            dependencies.append(ExperimentDependency('programme-e2.execution.' + name.replace('_', '-'), kind,
                'Select explicit ' + name + '.'))
    if method_inputs is None:
        dependencies.append(ExperimentDependency('programme-e2.request', DependencyKind.EXTERNAL_INPUT,
            'Supply explicit native resources and the current campaign.', 'request'))
    else:
        validate_request(specification, method_inputs)
        if execution.workers != method_inputs.resources.maximum_parallel_tasks:
            dependencies.append(ExperimentDependency('programme-e2.worker-selection', DependencyKind.ENVIRONMENT,
                'Assembly and E2 must retain the same explicit native worker count.'))
        dependencies.append(ExperimentDependency('programme-e2.derive', DependencyKind.EXTERNAL_INPUT,
            'Use experiment-derive-inputs to authenticate C and construct ordinary native E2 inputs.'))
    return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0),
        tuple(sorted(dependencies, key=lambda value: value.code)), execution=execution, specification_record=specification)
