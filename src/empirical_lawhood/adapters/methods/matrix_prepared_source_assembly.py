# SPDX-License-Identifier: MPL-2.0
"""Copied inputs for prepared-source metadata; actual DEV custody stays required."""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support as current_exposure_support
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedProtectedProgramme,MatrixSelectedPublicProgramme
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import MatrixRevisionPreparedProgramme
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_development_product import MatrixSelectedDevelopmentProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_development_product import MatrixRevisionDevelopmentProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import ConfiguredProtectedE3PreparationSelection
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeInputCommitments,MatrixProgrammePublishedInput,MatrixProgrammeProducedInput
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_operational_resources import SelectedE4OperationalResources
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.obligations import ComputabilityEvidence
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord,validate_relative_locator,validate_stable_id
from empirical_lawhood.kernel.time import InformationCutoff
from empirical_lawhood.planning.dataset_authority import DatasetWorkEnvelope,_validate_reason_codes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.runtime.experiment_preparation import DependencyKind,ExperimentCensus,ExperimentDependency,ExperimentPreparation,PreparedExperimentInputs

PROTOCOL_ID='matrix.source.prepared-finite-dt-input-assembly'
PROGRAMME_TYPES=(MatrixSelectedProtectedProgramme,MatrixSelectedPublicProgramme,MatrixRevisionPreparedProgramme)
DEVELOPMENT_TYPES=(MatrixSelectedDevelopmentProduct,MatrixRevisionDevelopmentProduct)


def _pin(value,kinds):
    if (type(value) is not ObjectIdentity or (value.object_schema,value.object_version)
            not in {(kind.SCHEMA,kind.VERSION) for kind in kinds}):
        raise TypeError('prepared source assembly requires its exact scientific input edition')
    value.__post_init__()


@dataclass(frozen=True,slots=True)
class MatrixPreparedSourceAssemblyRequest(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-source/prepared-finite-dt-input-assembly-request'
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
    prepared_programme:ObjectIdentity
    development_product:ObjectIdentity
    native_training_locator:MatrixFiniteDtTrainingLocator
    exposure_support:tuple[tuple[ArtifactIdentity,ArtifactWriteResult|ExperimentFileInputBinding],...]
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
        for value in (self.record_id,self.namespace,self.metadata_issuer_id,self.metadata_approver_id,self.metadata_requester_id):
            validate_stable_id(value)
        for value,kinds in ((self.prepared_programme,PROGRAMME_TYPES),(self.development_product,DEVELOPMENT_TYPES)):
            _pin(value,kinds)
        for value,kind in ((self.native_training_locator,MatrixFiniteDtTrainingLocator),
                (self.physical_cutoff,InformationCutoff),(self.source_computability_evidence,ComputabilityEvidence),
                (self.source_budget,ResourceBudget),(self.dataset_work_envelope,DatasetWorkEnvelope),
                (self.operational_resources,SelectedE4OperationalResources)):
            if type(value) is not kind:raise TypeError('prepared source assembly requires its exact actual scientific/operational owner')
            value.__post_init__()
        for selected,kind,handle in ((self.input_commitments,MatrixProgrammeInputCommitments,MatrixProgrammePublishedInput),
                (self.original_e3,ConfiguredMatrixSelectedPublicPackage,MatrixProgrammeProducedInput),
                (self.original_preparation,self.preparation_type,MatrixProgrammePublishedInput),
                (self.original_assay,ScheduledResponseProtocol,MatrixProgrammePublishedInput)):
            if type(selected) is not handle:
                raise TypeError('prepared source assembly requires actual original C/E3/preparation/assay publication handles')
            selected.__post_init__();selected.require_kind(kind)
        if (type(self.original_products) is not tuple or len(self.original_products)!=4
                or any(type(value) is not MatrixSelectedOriginalProduct for value in self.original_products)
                or tuple(value.record.object_id for value in self.original_products)!=tuple(sorted(
                    {value.record.object_id for value in self.original_products}))):
            raise ValueError('prepared source assembly requires the four exact distinct original E3 producer locators')
        for value in self.original_products:value.__post_init__()
        if (type(self.exposure_support) is not tuple or len(self.exposure_support)!=1
                or any(type(row) is not tuple or len(row)!=2 for row in self.exposure_support)
                or any(type(artifact) is not ArtifactIdentity or type(custody) not in (ArtifactWriteResult,ExperimentFileInputBinding)
                    for artifact,custody in self.exposure_support)
                or tuple(artifact.artifact_id for artifact,_ in self.exposure_support)
                    !=tuple(sorted({artifact.artifact_id for artifact,_ in self.exposure_support}))):
            raise ValueError('prepared source assembly needs the exact current census publication support')
        for artifact,custody in self.exposure_support:
            artifact.__post_init__();custody.__post_init__()
            if type(custody) is ExperimentFileInputBinding:
                matches=custody.identity==artifact
            else:
                matches=(artifact.artifact_id,artifact.payload_schema,artifact.sha256,artifact.media_type,artifact.size_bytes)==(
                    custody.logical.logical_artifact_id,custody.logical.payload_schema,custody.logical.content_sha256,
                    custody.logical.media_type,custody.materialization.size_bytes)
            if not matches:raise ValueError('prepared source exposure support changes exact original byte custody')
        validate_relative_locator(self.metadata_private_key_relative_path)
        for field in ('memory_bytes','source_scan_bytes','output_bytes'):
            if type(getattr(self.source_budget,field)) is not int or getattr(self.source_budget,field)<1:
                raise ValueError('prepared source requires its explicit finite positive '+field)
        if (type(self.metadata_validity_seconds) is not int or self.metadata_validity_seconds<1
                or type(self.allow_metadata_key_creation) is not bool):
            raise ValueError('prepared source needs explicit machine-key creation policy and positive metadata validity')
        _validate_reason_codes(self.metadata_reason_codes,field_name='metadata_reason_codes',
            envelope_limit=self.dataset_work_envelope.control.max_reason_codes)
        if self.metadata_requester_id==self.metadata_approver_id:raise PermissionError('metadata request cannot self-approve')
        if not isinstance(self.licence_id,str) or not self.licence_id.strip():raise ValueError('prepared source needs its actual source licence')
        from empirical_lawhood.planning.source_pipelines import _validate_static_locator
        _validate_static_locator(self.scratch_namespace,field_name='scratch_namespace')
        if self.metadata_valid_from_utc is not None:
            if not isinstance(self.metadata_valid_from_utc,str) or not self.metadata_valid_from_utc.endswith('Z'):
                raise ValueError('metadata validity start must be an explicit UTC timestamp')
            datetime.fromisoformat(self.metadata_valid_from_utc.replace('Z','+00:00'))

    @property
    def identity(self):return ObjectIdentity.from_record(self.record_id,self)

    @property
    def preparation_type(self):
        return next((kind for kind in (self.PREPARATION_TYPE, *self.ADDITIONAL_PREPARATION_TYPES)
            if (kind.SCHEMA, kind.VERSION) == (self.original_preparation.record.object_schema,
                self.original_preparation.record.object_version)), self.PREPARATION_TYPE)


@dataclass(frozen=True,slots=True)
class MatrixPreparedSourceAssemblySpecification(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-source/prepared-finite-dt-input-assembly-specification'
    VERSION: ClassVar[str]='2.0.0'
    REQUEST_TYPE: ClassVar[type] = MatrixPreparedSourceAssemblyRequest
    specification_id:str
    request:ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        _pin(self.request,(self.REQUEST_TYPE,))

    @property
    def identity(self):return ObjectIdentity.from_record(self.specification_id,self)


@dataclass(frozen=True,slots=True)
class MatrixPreparedSourceAssemblyInputs:
    request:MatrixPreparedSourceAssemblyRequest|None=None
    prepared_programme:MatrixSelectedProtectedProgramme|MatrixSelectedPublicProgramme|MatrixRevisionPreparedProgramme|None=None
    development_product:MatrixSelectedDevelopmentProduct|MatrixRevisionDevelopmentProduct|None=None


def input_record_types():
    return (MatrixPreparedSourceAssemblyRequest,*PROGRAMME_TYPES,*DEVELOPMENT_TYPES)


def validate_inputs(specification,inputs,*,complete=False):
    specification.__post_init__()
    if type(inputs) is not MatrixPreparedSourceAssemblyInputs:raise TypeError('prepared source assembly requires exact bound inputs')
    request=inputs.request
    if request is not None:
        if type(request) is not specification.REQUEST_TYPE:raise TypeError('prepared source assembly changes request edition')
        request.__post_init__()
        if specification.request!=request.identity:raise ValueError('prepared source assembly changes its exact request pin')
    for name,kinds in (('prepared_programme',PROGRAMME_TYPES),
            ('development_product',DEVELOPMENT_TYPES)):
        value=getattr(inputs,name)
        if value is not None:
            if type(value) not in kinds:raise TypeError('prepared source assembly changes '+name+' scientific owner')
            value.__post_init__()
            if request is not None and getattr(request,name)!=value.identity:
                raise ValueError('prepared source assembly changes its exact '+name+' pin')
    if complete and any(getattr(inputs,name) is None for name in ('request','prepared_programme','development_product')):
        raise ValueError('prepared source assembly omits actual current request/programme/development bindings')
    programme=inputs.prepared_programme
    if programme is not None:
        if programme.phase not in ('E5_CONFIRMATION','E6_TRANSFER'):
            raise ValueError('prepared source assembly needs exact protected CONF or original reserved E6 sources')
        if request is not None and {value for value,_ in request.exposure_support}!={
                artifact for artifact,_ in current_exposure_support(programme.sources.closure.audit)}:
            raise ValueError('prepared source assembly omits the selected original current census support')
        if inputs.development_product is not None and (type(programme) is MatrixRevisionPreparedProgramme)!=(
                type(inputs.development_product) is MatrixRevisionDevelopmentProduct):
            raise TypeError('prepared source assembly mixes original and revised DEV/programme families')


def bind_inputs(specification,records,*,files=None,**kwargs):
    roles={'request':'request','prepared-programme':'prepared_programme',
        'development-product':'development_product'}
    if set(records)-set(roles) or files:raise ValueError('prepared source assembly accepts only its three canonical input roles')
    inputs=MatrixPreparedSourceAssemblyInputs(**{roles[key]:value for key,value in records.items()})
    validate_inputs(specification,inputs)
    return PreparedExperimentInputs({},inputs)


def prepare(specification,*,execution,method_inputs=None,**kwargs):
    inputs=method_inputs if type(method_inputs) is MatrixPreparedSourceAssemblyInputs else MatrixPreparedSourceAssemblyInputs()
    validate_inputs(specification,inputs)
    dependencies=[]
    for name,kind in (('workers',DependencyKind.ENVIRONMENT),('environment_id',DependencyKind.ENVIRONMENT),
            ('source_snapshot',DependencyKind.ENVIRONMENT),('output_root',DependencyKind.STORAGE)):
        if getattr(execution,name) is None:dependencies.append(ExperimentDependency('prepared-source-assembly.execution.'+name.replace('_','-'),kind,'Select explicit '+name+'.'))
    for name,key in (('request','request'),('prepared_programme','prepared-programme'),
            ('development_product','development-product')):
        if getattr(inputs,name) is None:dependencies.append(ExperimentDependency('prepared-source-assembly.input.'+key,
            DependencyKind.EXTERNAL_INPUT,'Supply the exact original canonical '+key+' record.',key))
    if inputs.request is not None and execution.workers!=inputs.request.operational_resources.controls.maximum_parallel_tasks:
        dependencies.append(ExperimentDependency('prepared-source-assembly.worker-selection',DependencyKind.ENVIRONMENT,
            'Source metadata controls and selected workers must match.'))
    if all(getattr(inputs,name) is not None for name in ('request','prepared_programme','development_product')):
        dependencies.append(ExperimentDependency('prepared-source-assembly.derive',DependencyKind.EXTERNAL_INPUT,
            'Use experiment-derive-inputs to authenticate actual complete E5 DEV controls, original TRAIN/E3/E4 custody, current CONF exclusions or exact original E6 reserve, then publish the source candidate.'))
    groups=0 if inputs.prepared_programme is None else len({source.root.root.independent_group_id
        for _,source in inputs.prepared_programme.sources.source_arms()})
    return ExperimentPreparation(specification.identity,ExperimentCensus((('source',groups),),(('source',0),),(),(),0),
        tuple(sorted(dependencies,key=lambda value:value.code)),execution=execution,specification_record=specification)


from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection, ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection

CONTINUED_PROTOCOL_ID = 'matrix.source.prepared-retained-e3-input-assembly'


@dataclass(frozen=True, slots=True)
class MatrixPreparedRetainedE3AssemblyRequest(MatrixPreparedSourceAssemblyRequest):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-source/prepared-retained-e3-assembly-request'
    VERSION: ClassVar[str] = '1.0.0'
    PREPARATION_TYPE: ClassVar[type] = ConfiguredE3ContinuedPreparationSelection
    ADDITIONAL_PREPARATION_TYPES: ClassVar[tuple[type, ...]] = (ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection)


@dataclass(frozen=True, slots=True)
class MatrixPreparedRetainedE3AssemblySpecification(MatrixPreparedSourceAssemblySpecification):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-source/prepared-retained-e3-assembly-specification'
    VERSION: ClassVar[str] = '1.0.0'
    REQUEST_TYPE: ClassVar[type] = MatrixPreparedRetainedE3AssemblyRequest


def prepared_assembly_request_types():
    return (MatrixPreparedSourceAssemblyRequest, MatrixPreparedRetainedE3AssemblyRequest)


def prepared_assembly_request_kind(identity):
    kinds = tuple(kind for kind in prepared_assembly_request_types()
        if (identity.object_schema, identity.object_version) == (kind.SCHEMA, kind.VERSION))
    if len(kinds) != 1:
        raise ValueError('prepared source request requires its exact supported canonical edition')
    return kinds[0]
