# SPDX-License-Identifier: MPL-2.0
"""Typed finite-dt source metadata preprocessing; scientific authority stays explicit."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import ConfiguredProtectedE3PreparationSelection
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput, MatrixProgrammeProducedInput
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_operational_resources import SelectedE4OperationalResources
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.obligations import ComputabilityEvidence
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord,validate_relative_locator,validate_stable_id
from empirical_lawhood.kernel.time import InformationCutoff
from empirical_lawhood.planning.dataset_authority import DatasetWorkEnvelope, _validate_reason_codes
from empirical_lawhood.runtime.experiment_preparation import (DependencyKind,ExperimentCensus,ExperimentDependency,
    ExperimentPreparation,PreparedExperimentInputs)

PROTOCOL_ID='matrix.source.finite-dt-input-assembly'


@dataclass(frozen=True,slots=True)
class MatrixFiniteDtSourceAssemblyRequest(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-source/finite-dt-input-assembly-request'
    VERSION: ClassVar[str]='2.0.0'
    PREPARATION_TYPE: ClassVar[type] = ConfiguredProtectedE3PreparationSelection
    ADDITIONAL_PREPARATION_TYPES: ClassVar[tuple[type, ...]] = ()
    record_id:str
    namespace:str
    input_commitments:MatrixProgrammePublishedInput
    original_e3:MatrixProgrammeProducedInput
    original_preparation:MatrixProgrammePublishedInput
    original_assay:MatrixProgrammePublishedInput
    original_products:tuple[MatrixSelectedOriginalProduct,...]
    phase:str
    native_training_locator:MatrixFiniteDtTrainingLocator
    physical_cutoff:InformationCutoff
    source_computability_evidence:ComputabilityEvidence
    source_budget:ResourceBudget
    dataset_work_envelope:DatasetWorkEnvelope
    operational_resources:SelectedE4OperationalResources
    metadata_issuer_id:str
    metadata_approver_id:str
    metadata_requester_id:str
    metadata_private_key_relative_path:str
    metadata_validity_seconds:int
    metadata_reason_codes:tuple[str,...]
    licence_id:str
    scratch_namespace:str
    allow_metadata_key_creation:bool=False
    metadata_valid_from_utc:str|None=None

    def __post_init__(self):
        _validate_request_values(self)

    @property
    def identity(self):return ObjectIdentity.from_record(self.record_id,self)

    @property
    def preparation_type(self):
        return next((kind for kind in (self.PREPARATION_TYPE, *self.ADDITIONAL_PREPARATION_TYPES)
            if (kind.SCHEMA, kind.VERSION) == (self.original_preparation.record.object_schema,
                self.original_preparation.record.object_version)), self.PREPARATION_TYPE)


def _validate_request_values(self):
    for value in (self.record_id,self.namespace,self.metadata_issuer_id,self.metadata_approver_id,self.metadata_requester_id):validate_stable_id(value)
    for selected,kind,handle in ((self.input_commitments,MatrixProgrammeInputCommitments,MatrixProgrammePublishedInput),
            (self.original_e3,ConfiguredMatrixSelectedPublicPackage,MatrixProgrammeProducedInput),
            (self.original_preparation,self.preparation_type,MatrixProgrammePublishedInput),
            (self.original_assay,ScheduledResponseProtocol,MatrixProgrammePublishedInput)):
        if type(selected) is not handle:
            raise TypeError('source assembly requires its actual original typed publication handles')
        selected.__post_init__();selected.require_kind(kind)
    if (type(self.original_products) is not tuple or len(self.original_products)!=4
            or any(type(value) is not MatrixSelectedOriginalProduct for value in self.original_products)
            or tuple(value.record.object_id for value in self.original_products)!=tuple(sorted(
                {value.record.object_id for value in self.original_products}))):
        raise ValueError('source assembly requires exactly four distinct original E3 producer locators')
    for value in self.original_products:value.__post_init__()
    for value,kind in ((self.native_training_locator,MatrixFiniteDtTrainingLocator),
            (self.physical_cutoff,InformationCutoff),(self.source_computability_evidence,ComputabilityEvidence),
            (self.source_budget,ResourceBudget),(self.dataset_work_envelope,DatasetWorkEnvelope),(self.operational_resources,SelectedE4OperationalResources)):
        if type(value) is not kind:raise TypeError('source assembly requires its exact actual scientific/operational input owner')
        value.__post_init__()
    validate_relative_locator(self.metadata_private_key_relative_path)
    for field in ('memory_bytes','source_scan_bytes','output_bytes'):
        if type(getattr(self.source_budget,field)) is not int or getattr(self.source_budget,field)<1:
            raise ValueError('source assembly requires a finite positive '+field)
    if (self.phase not in ('CALIBRATION','CONFIRMATION') or type(self.metadata_validity_seconds) is not int or self.metadata_validity_seconds<1
            or type(self.allow_metadata_key_creation) is not bool or type(self.metadata_reason_codes) is not tuple
            or self.metadata_reason_codes!=tuple(sorted(set(self.metadata_reason_codes))) or not self.metadata_reason_codes):
        raise ValueError('source assembly requires explicit phase, machine-key policy, positive validity and sorted reasons')
    _validate_reason_codes(self.metadata_reason_codes,field_name='metadata_reason_codes',
        envelope_limit=self.dataset_work_envelope.control.max_reason_codes)
    if self.metadata_requester_id==self.metadata_approver_id:raise PermissionError('metadata request cannot self-approve')
    if not isinstance(self.licence_id,str) or not self.licence_id.strip():raise ValueError('source assembly needs its real licence')
    from empirical_lawhood.planning.source_pipelines import _validate_static_locator
    _validate_static_locator(self.scratch_namespace,field_name='scratch_namespace')
    if self.metadata_valid_from_utc is not None:
        from datetime import datetime
        if not isinstance(self.metadata_valid_from_utc,str) or not self.metadata_valid_from_utc.endswith('Z'):
            raise ValueError('metadata validity start must be an explicit UTC timestamp')
        datetime.fromisoformat(self.metadata_valid_from_utc.replace('Z','+00:00'))


def input_record_types():
    return (MatrixFiniteDtSourceAssemblyRequest,)


@dataclass(frozen=True,slots=True)
class MatrixFiniteDtSourceAssemblySpecification(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-source/finite-dt-input-assembly-specification'
    VERSION: ClassVar[str]='2.0.0'
    REQUEST_TYPE: ClassVar[type] = MatrixFiniteDtSourceAssemblyRequest
    specification_id:str
    request:ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        kind=self.REQUEST_TYPE
        if type(self.request) is not ObjectIdentity or (self.request.object_schema,self.request.object_version)!=(kind.SCHEMA,kind.VERSION):
            raise ValueError('source assembly requires its exact immutable request edition')
        self.request.__post_init__()

    @property
    def identity(self):return ObjectIdentity.from_record(self.specification_id,self)


def bind_inputs(specification,records,**kwargs):
    request=records.get('request')
    if set(records)-{'request'}:
        raise ValueError('source assembly accepts only its complete current C-backed request')
    if request is not None:
        if type(request) is not specification.REQUEST_TYPE:
            raise TypeError('source assembly changes its exact request edition')
        request.__post_init__()
        if specification.request!=request.identity:raise ValueError('source assembly changes its selected request pin')
    return PreparedExperimentInputs({},request)


def prepare(specification,*,execution,method_inputs=None,**kwargs):
    specification.__post_init__();request=method_inputs;dependencies=[]
    for name,kind in (('workers',DependencyKind.ENVIRONMENT),('environment_id',DependencyKind.ENVIRONMENT),
            ('source_snapshot',DependencyKind.ENVIRONMENT),('output_root',DependencyKind.STORAGE)):
        if getattr(execution,name) is None:dependencies.append(ExperimentDependency('finite-dt-assembly.execution.'+name.replace('_','-'),kind,'Select explicit '+name+'.'))
    if request is None:
        dependencies.append(ExperimentDependency('finite-dt-assembly.request',DependencyKind.EXTERNAL_INPUT,
            'Supply actual C and original E3/preparation/assay publications, four E3 producers, native TRAIN locator and explicit operational selections.','request'))
    else:
        bind_inputs(specification,{'request':request})
        if execution.workers!=request.operational_resources.controls.maximum_parallel_tasks:
            dependencies.append(ExperimentDependency('finite-dt-assembly.worker-selection',DependencyKind.ENVIRONMENT,'Source controls and selected workers must match.'))
        dependencies.append(ExperimentDependency('finite-dt-assembly.derive',DependencyKind.EXTERNAL_INPUT,
            'Use experiment-derive-inputs to construct actual pending-source metadata, metadata-only dataset authorization and public source candidate; no scientific issue/reveal or native acquisition.'))
    # Static preparation does not open C or infer its assigned group census.
    return ExperimentPreparation(specification.identity,ExperimentCensus((),(),(),(),0),
        tuple(sorted(dependencies,key=lambda value:value.code)),execution=execution,specification_record=specification)


from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection, ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection

CONTINUED_PROTOCOL_ID = 'matrix.source.finite-dt-retained-e3-input-assembly'


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtRetainedE3AssemblyRequest(MatrixFiniteDtSourceAssemblyRequest):
    """Distinct source recipe for the explicitly retained E3 preparation."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-source/finite-dt-retained-e3-assembly-request'
    VERSION: ClassVar[str] = '1.0.0'
    PREPARATION_TYPE: ClassVar[type] = ConfiguredE3ContinuedPreparationSelection
    ADDITIONAL_PREPARATION_TYPES: ClassVar[tuple[type, ...]] = (ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection)


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtRetainedE3AssemblySpecification(MatrixFiniteDtSourceAssemblySpecification):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-source/finite-dt-retained-e3-assembly-specification'
    VERSION: ClassVar[str] = '1.0.0'
    REQUEST_TYPE: ClassVar[type] = MatrixFiniteDtRetainedE3AssemblyRequest


def source_assembly_request_types():
    return (MatrixFiniteDtSourceAssemblyRequest, MatrixFiniteDtRetainedE3AssemblyRequest)
