# SPDX-License-Identifier: MPL-2.0
"""Direct scientific E3 inputs after actual native TRAIN; no scientific issue."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.runtime.native_training_export import NativeTrainingExportAdoptionSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import ProtectedE3ResourceSelection
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
from empirical_lawhood.kernel.authority import AuthorityPolicy
from empirical_lawhood.kernel.obligations import ComputabilityEvidence
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.kernel.worlds import ComputabilityEnvelope
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.runtime.experiment_preparation import (DependencyKind, ExperimentCensus, ExperimentDependency,
    ExperimentPreparation, PreparedExperimentInputs)
from .configured_primary_amendment import MatrixE3PrimaryFamilyAmendment
from .native_training_protocol import NativeTrainingScientificProtocol

PROTOCOL_ID = 'matrix.response-error.configured-protected-input-assembly'


def _pin(value, kind):
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise TypeError('configured scientific assembly substitutes its exact scientific operand')
    value.__post_init__()


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3AssemblyRequest(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/scientific-configured-protected-assembly-request'
    record_id: str
    namespace: str
    scientific_protocol: ObjectIdentity
    pretrain_inputs_relative_directory: str
    native_training_locator: MatrixFiniteDtTrainingLocator
    resources: ProtectedE3ResourceSelection
    authority_policy: AuthorityPolicy
    computability_envelope: ComputabilityEnvelope
    computability_evidence: ComputabilityEvidence
    operator_id: str
    bank_export_record_id: str
    bank_export_relative_path: str
    normalization_file: ExperimentFileInputBinding
    primary_amendment: ObjectIdentity | None = None

    def __post_init__(self):
        for value in (self.record_id, self.namespace, self.operator_id, self.bank_export_record_id):
            validate_stable_id(value)
        for value in (self.pretrain_inputs_relative_directory, self.bank_export_relative_path):
            validate_relative_locator(value)
        _pin(self.scientific_protocol, NativeTrainingScientificProtocol)
        for value, kind in ((self.native_training_locator, MatrixFiniteDtTrainingLocator),
                (self.resources, ProtectedE3ResourceSelection), (self.authority_policy, AuthorityPolicy),
                (self.computability_envelope, ComputabilityEnvelope), (self.computability_evidence, ComputabilityEvidence),
                (self.normalization_file, ExperimentFileInputBinding)):
            if type(value) is not kind:
                raise TypeError('configured scientific assembly substitutes an exact scientific/operational owner')
            value.__post_init__()
        if self.computability_evidence.envelope_id != self.computability_envelope.envelope_id:
            raise ValueError('configured scientific assembly changes its explicit computability envelope')
        if self.primary_amendment is not None:
            _pin(self.primary_amendment, MatrixE3PrimaryFamilyAmendment)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3AssemblySpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/scientific-configured-protected-assembly-specification'
    specification_id: str
    request: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        _pin(self.request, ConfiguredProtectedE3AssemblyRequest)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3AssemblyInputs:
    request: ConfiguredProtectedE3AssemblyRequest | None = None
    request_path: object | None = None
    scientific_protocol: NativeTrainingScientificProtocol | None = None
    primary_amendment: MatrixE3PrimaryFamilyAmendment | None = None
    export_adoption: NativeTrainingExportAdoptionSelection | None = None
    retained_training_continuation: MatrixProgrammePublishedInput | None = None


def require_computability_scope(envelope, evidence, coordinate):
    """Check the declared E3 scope without granting readiness or access."""
    if (evidence.envelope_id != envelope.envelope_id
            or set(evidence.numerical_view_ids) != {coordinate.primary_view.view_id, coordinate.fine_view.view_id}):
        raise ValueError("Actual scoped computability evidence changes the selected envelope or paired native views")


def validate_scientific_protocol(request, scientific):
    if type(request) is not ConfiguredProtectedE3AssemblyRequest or type(scientific) is not NativeTrainingScientificProtocol:
        raise TypeError('configured scientific assembly requires its direct mathematical protocol')
    request.__post_init__()
    scientific.__post_init__()
    if request.scientific_protocol != scientific.identity:
        raise ValueError('configured scientific assembly changes its exact separately bound scientific protocol')
    if request.normalization_file.identity != scientific.full_factor_rule.scalar_closure.normalization_owner:
        raise ValueError('configured scientific assembly requires its exact original normalization source bytes')


def bind_inputs(specification, records, *, record_paths=None, files=None):
    if set(records) - {'request', 'scientific-protocol', 'primary-amendment', 'native-training-export-adoption',
            'retained-training-continuation'} or files:
        raise ValueError('configured scientific assembly accepts its direct request and separately pinned scientific protocol')
    specification.__post_init__()
    request = records.get('request')
    scientific = records.get('scientific-protocol')
    amendment = records.get('primary-amendment')
    if request is not None:
        if type(request) is not ConfiguredProtectedE3AssemblyRequest:
            raise TypeError('configured scientific assembly changes its current request type')
        request.__post_init__()
        if specification.request != request.identity:
            raise ValueError('configured scientific assembly changes its selected request')
    if scientific is not None:
        if type(scientific) is not NativeTrainingScientificProtocol:
            raise TypeError('configured scientific assembly requires its exact mathematical definitions')
        scientific.__post_init__()
        if request is not None:
            validate_scientific_protocol(request, scientific)
    if amendment is not None:
        if request is None or type(amendment) is not MatrixE3PrimaryFamilyAmendment:
            raise TypeError('primary assessment amendment requires its exact current assembler request')
        amendment.__post_init__()
        if request.primary_amendment != amendment.identity:
            raise ValueError('configured scientific assembly substitutes its frozen primary amendment')
    adoption = records.get('native-training-export-adoption')
    if adoption is not None:
        if type(adoption) is not NativeTrainingExportAdoptionSelection:
            raise TypeError('configured E3 export adoption requires its exact typed selection')
        adoption.__post_init__()
    continuation = records.get('retained-training-continuation')
    if continuation is not None:
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.retained_training_continuation import MatrixProgrammeRetainedTrainingContinuation
        if type(continuation) is not MatrixProgrammePublishedInput or adoption is None:
            raise TypeError('continued E3 requires its exact published retained TRAIN handoff and bank adoption selection')
        continuation.__post_init__()
        continuation.require_kind(MatrixProgrammeRetainedTrainingContinuation)
    return PreparedExperimentInputs({}, ConfiguredProtectedE3AssemblyInputs(request,
        (record_paths or {}).get('request'), scientific, amendment, adoption, continuation))


def prepare(specification, *, execution, method_inputs=None, **kwargs):
    specification.__post_init__()
    dependencies = []
    inputs = method_inputs if type(method_inputs) is ConfiguredProtectedE3AssemblyInputs else ConfiguredProtectedE3AssemblyInputs()
    for name, kind in (('workers', DependencyKind.ENVIRONMENT), ('environment_id', DependencyKind.ENVIRONMENT),
            ('source_snapshot', DependencyKind.ENVIRONMENT), ('output_root', DependencyKind.STORAGE)):
        if getattr(execution, name) is None:
            dependencies.append(ExperimentDependency('configured-assembly.execution.' + name.replace('_', '-'), kind,
                'Select explicit ' + name + '.'))
    if inputs.request is None:
        dependencies.append(ExperimentDependency('configured-assembly.request', DependencyKind.EXTERNAL_INPUT,
            'Supply actual preTRAIN commitments and completed native TRAIN locator, scientific protocol, policy, computability and resources.', 'request'))
    if inputs.scientific_protocol is None:
        dependencies.append(ExperimentDependency('configured-assembly.scientific-protocol', DependencyKind.EXTERNAL_INPUT,
            'Supply the direct mathematical protocol, coordinates, numerical design, scalar and prefix definitions.', 'scientific-protocol'))
    if inputs.request is not None:
        if inputs.request.primary_amendment is not None and inputs.primary_amendment is None:
            dependencies.append(ExperimentDependency('configured-assembly.primary-amendment', DependencyKind.EXTERNAL_INPUT,
                'Supply the exact primary alpha/family amendment over the unchanged original native TRAIN candidate.', 'primary-amendment'))
        records = {'request': inputs.request}
        if inputs.scientific_protocol is not None:
            records['scientific-protocol'] = inputs.scientific_protocol
        if inputs.primary_amendment is not None:
            records['primary-amendment'] = inputs.primary_amendment
        if inputs.export_adoption is not None:
            records['native-training-export-adoption'] = inputs.export_adoption
        if inputs.retained_training_continuation is not None:
            records['retained-training-continuation'] = inputs.retained_training_continuation
        bind_inputs(specification, records)
        if execution.workers != inputs.request.resources.resources.maximum_parallel_tasks:
            dependencies.append(ExperimentDependency('configured-assembly.workers', DependencyKind.ENVIRONMENT,
                'Configured E3 resources must match selected workers.'))
        dependencies.append(ExperimentDependency('configured-assembly.derive', DependencyKind.EXTERNAL_INPUT,
            'Use experiment-derive-inputs to authenticate actual native TRAIN, retain all four future selectors, export exact banks and build current E3 inputs; human issue/proposer/reveal acts remain separate.'))
    return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0),
        tuple(sorted(dependencies, key=lambda value: value.code)), execution=execution, specification_record=specification)
