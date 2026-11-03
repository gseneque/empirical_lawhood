# SPDX-License-Identifier: MPL-2.0
"""Current native TRAIN assembly from the complete original known inputs C."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import NativeTrainingResources
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import (
    MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs,
)

PROTOCOL_ID = 'matrix.response-error.native-training-input-assembly'


@dataclass(frozen=True, slots=True)
class NativeTrainingAssemblySpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/scientific-native-training-assembly-specification'
    VERSION: ClassVar[str] = '3.0.0'
    specification_id: str
    namespace: str
    candidate: ObjectIdentity
    request: ObjectIdentity
    input_commitments: MatrixProgrammePublishedInput

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        validate_stable_id(self.namespace)
        for reference, kind in ((self.candidate, ConfiguredProtectedE3Specification),
                (self.request, NativeTrainingAssemblyRequest)):
            if (type(reference) is not ObjectIdentity
                    or (reference.object_schema, reference.object_version) != (kind.SCHEMA, kind.VERSION)):
                raise ValueError('native assembly substitutes its exact current candidate/request edition')
            reference.__post_init__()
        if type(self.input_commitments) is not MatrixProgrammePublishedInput:
            raise TypeError('native assembly requires its actual programme commitment')
        self.input_commitments.__post_init__()
        self.input_commitments.require_kind(MatrixProgrammeInputCommitments)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class NativeTrainingAssemblyRequest(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/scientific-native-training-assembly-request'
    VERSION: ClassVar[str] = '3.0.0'
    record_id: str
    resources: NativeTrainingResources
    campaign: CampaignSpec

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.resources, NativeTrainingResources), (self.campaign, CampaignSpec)):
            if type(value) is not kind:
                raise TypeError('native assembly requires its explicit resources and campaign')
            value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def input_record_types():
    from .native_training_protocol import NativeTrainingScientificProtocol
    from .exposure import MatrixFactorExposureCensus
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseAssay
    # These independent scientific records retain their ordinary authoring
    # consumers. Assembly binds only the complete operational request below.
    return (NativeTrainingAssemblyRequest, NativeTrainingScientificProtocol, MatrixFactorExposureCensus, ScheduledResponseAssay)


def validate_request(specification, request):
    if type(specification) is not NativeTrainingAssemblySpecification or type(request) is not NativeTrainingAssemblyRequest:
        raise TypeError('native assembly requires its exact current specification and operational request')
    specification.__post_init__()
    request.__post_init__()
    if specification.request != request.identity:
        raise ValueError('native assembly changes its frozen request pin')
    # The candidate body is in C. Its exact pin is joined only after guarded
    # ordinary C authentication; static discovery does not inspect storage.


@dataclass(frozen=True, slots=True)
class NativeTrainingAssemblyInputs:
    request: NativeTrainingAssemblyRequest | None = None
    request_path: object | None = None


def bind_inputs(specification, records, *, record_paths=None, files=None):
    if files or set(records) - {'request'}:
        raise ValueError('native assembly accepts only its exact current operational request')
    request = records.get('request')
    if request is not None:
        validate_request(specification, request)
    return PreparedExperimentInputs({}, NativeTrainingAssemblyInputs(request, (record_paths or {}).get('request')))


def prepare(specification, *, execution, method_inputs=None, **_kwargs):
    specification.__post_init__()
    inputs = method_inputs if type(method_inputs) is NativeTrainingAssemblyInputs else NativeTrainingAssemblyInputs()
    dependencies = []
    for name, kind in (('workers', DependencyKind.ENVIRONMENT), ('environment_id', DependencyKind.ENVIRONMENT),
            ('source_snapshot', DependencyKind.ENVIRONMENT), ('output_root', DependencyKind.STORAGE)):
        if getattr(execution, name) is None:
            dependencies.append(ExperimentDependency('native-assembly.execution.' + name.replace('_', '-'), kind,
                'Select explicit ' + name + '.'))
    if inputs.request is None:
        dependencies.append(ExperimentDependency('native-assembly.request', DependencyKind.EXTERNAL_INPUT,
            'Supply the exact native resources and campaign request.', 'request'))
    else:
        validate_request(specification, inputs.request)
        if execution.workers != inputs.request.resources.maximum_parallel_tasks:
            dependencies.append(ExperimentDependency('native-assembly.worker-selection', DependencyKind.ENVIRONMENT,
                'Assembly and native resources must retain the same explicit worker count.'))
        dependencies.append(ExperimentDependency('native-assembly.derive', DependencyKind.EXTERNAL_INPUT,
            'Use experiment-derive-inputs to authenticate the complete original C and derive TRAIN inputs; no native task is started.'))
    return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0),
        tuple(sorted(dependencies, key=lambda value: value.code)), execution=execution, specification_record=specification)
