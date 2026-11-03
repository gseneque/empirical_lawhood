# SPDX-License-Identifier: MPL-2.0
"""Two exact public lifecycle leaves over shared original full-history science."""
from collections import Counter
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.experimental_design import IndependentUnit,UnitAllocation,UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord,validate_stable_id
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import (DependencyKind,ExecutionSelection,ExperimentCensus,ExperimentDependency,
    ExperimentPreparation,PreparedExperimentInputs,PreparedExperimentFile,ExperimentProtocolDeclaration,ExperimentInputConfigurationDeclaration)
from . import full_factor_records as r,full_factor_bindings as methods
from .full_factor_followup_records import ScheduledFullFactorScope,ScheduledFullFactorResources,ScheduledFullFactorScopeReference,scope_reference
from .selected_e3_e4_records import SelectedE3E4DevelopmentProgramme,SelectedE3E4DevelopmentBank,SelectedE3E4Evidence
from .selected_e4_programme import SelectedE4PhaseProgramme,SelectedE4PhaseBank
from .selected_e4_native_records import SelectedE4NativeProgrammeDeclaration,SelectedE4WaveLocator
from .selected_e4_method_bindings import SelectedE4DevelopmentAcquisition
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryReadoutSelection

DEV_PROTOCOL_ID='matrix.e4.selected-full-factor-followup.development'
PROTECTED_PROTOCOL_ID='matrix.e4.selected-full-factor-followup.protected'


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorMeasurement(CanonicalRecord):
    """Full original mathematics and declared source census, independent of outcomes."""
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-measurement'
    programme:ObjectIdentity
    rules:tuple[tuple[ObjectIdentity,r.FactorEventSpec,r.MatrixParameterFactorNumericalDesign],...]
    views:tuple[str,...]=('PRIMARY','FINE')
    measurement:str='COMPLETE_ORIGINAL_LATTICE_ASSOCIATIVE_LIE_FACTOR_TRANSPORT_ORIGIN_FIXED_SCALAR_CONTRAST'
    independence:str='ORIGINAL_MATCHED_GROUPS_COORDINATES_VIEWS_SECTORS_AND_TICKS_ARE_NESTED'

    def __post_init__(self):
        r._pin(self.programme,(SelectedE3E4DevelopmentProgramme,SelectedE4PhaseProgramme))
        if (type(self.rules) is not tuple or not self.rules
                or tuple(row[0].object_id for row in self.rules)!=tuple(sorted({row[0].object_id for row in self.rules}))
                or self.views!=('PRIMARY','FINE')
                or self.measurement!='COMPLETE_ORIGINAL_LATTICE_ASSOCIATIVE_LIE_FACTOR_TRANSPORT_ORIGIN_FIXED_SCALAR_CONTRAST'
                or self.independence!='ORIGINAL_MATCHED_GROUPS_COORDINATES_VIEWS_SECTORS_AND_TICKS_ARE_NESTED'):
            raise ValueError('full factor measurement changes original complete numerical definition')
        for coordinate,rule,numerical in self.rules:
            r._pin(coordinate,(r.MatrixParameterCoordinate,));r._exact(rule,r.FactorEventSpec)
            r._exact(numerical,r.MatrixParameterFactorNumericalDesign)


def measurement(scope):
    rules={ObjectIdentity.from_record(source.coordinate.coordinate_id,source.coordinate):(source.rule,source.numerical_design)
        for source in scope.sources}
    if any(rules[ObjectIdentity.from_record(source.coordinate.coordinate_id,source.coordinate)]!=(source.rule,source.numerical_design) for source in scope.sources):
        raise ValueError('full factor measurement assigns incompatible definitions to one physical coordinate')
    return ScheduledFullFactorMeasurement(scope.programme.identity,tuple((coordinate,*value) for coordinate,value in sorted(rules.items(),key=lambda row:row[0].object_id)))


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorDevelopmentRequestV3(CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-development-request'
    VERSION:ClassVar[str]='3.0.0'
    record_id:str
    programme:ObjectIdentity
    bank:ObjectIdentity
    resources:ObjectIdentity
    campaign:ObjectIdentity
    original:SelectedE4DevelopmentAcquisition
    secondary_readout:MatrixE4SecondaryReadoutSelection

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value,kind in ((self.programme,SelectedE3E4DevelopmentProgramme),(self.bank,SelectedE3E4DevelopmentBank),
                (self.resources,ScheduledFullFactorResources),(self.campaign,CampaignSpec)):r._pin(value,(kind,))
        r._exact(self.original,SelectedE4DevelopmentAcquisition)
        if self.original.allow_partial:raise ValueError('full factor development follow-up needs complete original terminal census')
        r._exact(self.secondary_readout,MatrixE4SecondaryReadoutSelection)

    @property
    def identity(self):return r.identity(self)


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorProtectedRequestV4(CanonicalRecord):
    """Already revealed original evidence; ordinary nonpromoting PURE analysis.

    Actual original issue/execution/reveal locators remain mandatory. A new
    sealed scientific root or source qualification would misstate this work.
    """
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-protected-request'
    VERSION:ClassVar[str]='4.0.0'
    record_id:str
    programme:ObjectIdentity
    bank:ObjectIdentity
    resources:ObjectIdentity
    declaration:ObjectIdentity
    waves:tuple[SelectedE4WaveLocator,...]
    campaign:ObjectIdentity
    secondary_readout:MatrixE4SecondaryReadoutSelection

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value,kind in ((self.programme,SelectedE4PhaseProgramme),(self.bank,SelectedE4PhaseBank),
                (self.resources,ScheduledFullFactorResources),(self.declaration,SelectedE4NativeProgrammeDeclaration),
                (self.campaign,CampaignSpec)):r._pin(value,(kind,))
        if (type(self.waves) is not tuple or not self.waves or any(type(row) is not SelectedE4WaveLocator for row in self.waves)
                or tuple(row.wave_id for row in self.waves)!=tuple(sorted({row.wave_id for row in self.waves}))):
            raise ValueError('full factor revealed request needs every unique actual original wave')
        for row in self.waves:row.__post_init__()
        r._exact(self.secondary_readout,MatrixE4SecondaryReadoutSelection)

    @property
    def identity(self):return r.identity(self)


def request_types(protected):
    return (ScheduledFullFactorProtectedRequestV4,) if protected else (ScheduledFullFactorDevelopmentRequestV3,)


@dataclass(frozen=True,slots=True)
class _Specification(CanonicalRecord):
    specification_id:str
    request:ObjectIdentity
    scope:ObjectIdentity|None
    measurement:ScheduledFullFactorMeasurement|None
    preparation:None

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        protected=type(self) is ScheduledFullFactorProtectedSpecification
        r._pin(self.request,request_types(protected))
        if (self.scope is None)!=(self.measurement is None):raise ValueError('full factor specification must pin both actual scope and complete measurement')
        if self.scope is not None:r._pin(self.scope,(ScheduledFullFactorScope,));r._exact(self.measurement,ScheduledFullFactorMeasurement)
        if self.preparation is not None:raise ValueError('full factor current specification cannot invent prospective preparation')

    @property
    def identity(self):return ObjectIdentity.from_record(self.specification_id,self)


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorDevelopmentSpecification(_Specification):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-development-specification'


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorProtectedSpecification(_Specification):
    SCHEMA:ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-protected-specification'


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorFollowupInputs:
    request:ScheduledFullFactorDevelopmentRequestV3|ScheduledFullFactorProtectedRequestV4|None=None
    programme:SelectedE3E4DevelopmentProgramme|SelectedE4PhaseProgramme|None=None
    bank:SelectedE3E4DevelopmentBank|SelectedE4PhaseBank|None=None
    resources:ScheduledFullFactorResources|None=None
    campaign:CampaignSpec|None=None
    reference:ScheduledFullFactorScopeReference|None=None
    scope:ScheduledFullFactorScope|None=None
    files:tuple[tuple[str,PreparedExperimentFile],...]=()
    original_evidence:SelectedE3E4Evidence|None=None

    @property
    def files_by_role(self):return dict(self.files)

    def __post_init__(self):
        for name,kinds in (('request',(*request_types(False),*request_types(True))),
                ('programme',(SelectedE3E4DevelopmentProgramme,SelectedE4PhaseProgramme)),('bank',(SelectedE3E4DevelopmentBank,SelectedE4PhaseBank)),
                ('resources',(ScheduledFullFactorResources,)),('campaign',(CampaignSpec,)),
                ('reference',(ScheduledFullFactorScopeReference,)),('scope',(ScheduledFullFactorScope,)),('original_evidence',(SelectedE3E4Evidence,))):
            value=getattr(self,name)
            if value is not None:
                if type(value) not in kinds:raise TypeError('full factor public input changes exact typed role '+name)
                value.__post_init__()
        if (type(self.files) is not tuple or tuple(key for key,_ in self.files)!=tuple(sorted({key for key,_ in self.files}))
                or any(type(row) is not PreparedExperimentFile for _,row in self.files)):
            raise ValueError('full factor follow-up requires exact separately bound original array files')


def programme_allocation(programme,bank):
    index=bank.source_index()
    return UnitAllocation('allocation.full-factor.'+programme.programme_id,tuple(sorted((programme.identity,bank.identity,ObjectIdentity.from_record(bank.reservation.allocation.allocation_id,bank.reservation.allocation)),key=lambda row:row.object_id)),
        tuple(IndependentUnit(group,bank.reservation.allocation.allocation_id,next(case.family_id for case in programme.cases if case.independent_group_id==group),
            tuple(sorted({view.view_id for case in programme.cases if case.independent_group_id==group for view in (
                bank.source(case.root_id,index=index).coordinate.primary_view,bank.source(case.root_id,index=index).coordinate.fine_view)})),True)
            for group in programme.group_ids),tuple(UnitRoleAssignment(group,'analysis') for group in programme.group_ids))


def input_record_types():
    return (*request_types(False),*request_types(True),ScheduledFullFactorScopeReference,ScheduledFullFactorResources,
        SelectedE3E4DevelopmentProgramme,SelectedE3E4DevelopmentBank,SelectedE3E4Evidence,SelectedE4PhaseProgramme,SelectedE4PhaseBank,CampaignSpec)


def bind_inputs(specification,records,*,files=None):
    if type(specification) not in (ScheduledFullFactorDevelopmentSpecification,ScheduledFullFactorProtectedSpecification) or not isinstance(records,Mapping):
        raise TypeError('full factor public selection requires its exact static lifecycle specification')
    roles=('request','programme','bank','resources','campaign','reference','original-evidence')
    if set(records)-set(roles):raise ValueError('full factor selection adds unsupported scientific roles')
    scope=None
    if specification.scope is not None:
        file=(files or {}).get('external.full-factor.scope.'+specification.scope.object_fingerprint)
        if file is not None:
            from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
            from empirical_lawhood.kernel.decoding import decode_canonical_bytes
            raw=read_bounded_bytes(file.path,maximum_bytes=file.maximum_bytes)
            scope=decode_canonical_bytes(raw,ScheduledFullFactorScope,maximum_bytes=file.maximum_bytes)
            if (scope.canonical_bytes()!=raw or scope.identity!=specification.scope or file.record_version!=scope.VERSION
                    or file.identity!=scope_reference(scope).scope_artifact or records.get('reference')!=scope_reference(scope)):
                raise ValueError('full factor scope FILE changes exact selected canonical observations or blind reference')
    inputs=ScheduledFullFactorFollowupInputs(**{name.replace('-','_'):records.get(name) for name in roles},scope=scope,files=tuple(sorted((files or {}).items())))
    return PreparedExperimentInputs({} if inputs.programme is None or inputs.bank is None else {'programme':programme_allocation(inputs.programme,inputs.bank)},inputs)


def _draft(specification,inputs):
    return methods.lower(inputs.reference,inputs.resources,draft_id='draft.full-factor.'+specification.fingerprint(),
        campaign=inputs.campaign,protected_root=None)


def prepare(specification,*,scientific_inputs,execution,method_inputs=None,protocol_bytes=None):
    if type(specification) not in (ScheduledFullFactorDevelopmentSpecification,ScheduledFullFactorProtectedSpecification) or type(execution) is not ExecutionSelection:
        raise TypeError('full factor preparation requires its exact static lifecycle and explicit execution')
    specification.__post_init__();execution.__post_init__()
    inputs=ScheduledFullFactorFollowupInputs() if method_inputs is None else method_inputs
    if type(inputs) is not ScheduledFullFactorFollowupInputs:raise TypeError('full factor preparation requires exact bound records')
    inputs.__post_init__();dependencies=[]
    def missing(code,kind,detail):dependencies.append(ExperimentDependency('matrix.full-factor.'+code,kind,detail))
    protected=type(specification) is ScheduledFullFactorProtectedSpecification
    if not protected and inputs.reference is not None and inputs.original_evidence is None:
        missing('original-evidence',DependencyKind.EXTERNAL_INPUT,'Retain the exact original DEV packet locator evidence through the public derivation owner.')
    if inputs.original_evidence is not None and (protected or (inputs.programme is not None
            and inputs.original_evidence.programme!=inputs.programme.identity)):
        raise ValueError('full factor locator evidence changes its original DEV programme or lifecycle')
    for role in ('request','programme','bank','resources'):
        if getattr(inputs,role) is None:missing(role+'.missing',DependencyKind.EXTERNAL_INPUT,'Supply the actual typed '+role+' record.')
    if inputs.request is not None:
        expected=request_types(protected)
        if type(inputs.request) not in expected or inputs.request.identity!=specification.request:raise ValueError('full factor specification changes exact request/lifecycle')
        for role,field in (('programme','programme_id'),('bank','bank_id'),('resources','record_id')):
            value=getattr(inputs,role)
            if value is not None and ObjectIdentity.from_record(getattr(value,field),value)!=getattr(inputs.request,role):raise ValueError('full factor input differs from request pin '+role)
    selected_allocation=None if inputs.programme is None or inputs.bank is None else programme_allocation(inputs.programme,inputs.bank)
    if scientific_inputs!=({} if selected_allocation is None else {'programme':selected_allocation}):raise ValueError('full factor preparation changes whole original independent units')
    if inputs.scope is None or inputs.reference is None or specification.scope is None:
        missing('original-custody',DependencyKind.SOFTWARE,'Derive the exact full original receipt/wave/reveal scope through the public input derivation owner.')
    else:
        if inputs.scope.identity!=specification.scope or inputs.reference!=scope_reference(inputs.scope) or measurement(inputs.scope)!=specification.measurement:raise ValueError('full factor specification changes original full scope or measurement')
        if inputs.scope.programme!=inputs.programme or inputs.scope.protected!=protected:raise ValueError('full factor scope changes selected original programme/lifecycle')
    if inputs.reference is not None:validate_reference(specification,inputs)
    if inputs.campaign is None:missing('campaign',DependencyKind.EXTERNAL_INPUT,'Supply the explicit actual development campaign.')
    elif inputs.request is not None and ObjectIdentity.from_record(inputs.campaign.campaign_id,inputs.campaign)!=inputs.request.campaign:
        raise ValueError('full factor exposed analysis campaign differs from request pin')
    for field,kind in (('workers',DependencyKind.ENVIRONMENT),('environment_id',DependencyKind.ENVIRONMENT),('source_snapshot',DependencyKind.ENVIRONMENT),('output_root',DependencyKind.STORAGE)):
        if getattr(execution,field) is None:missing(field,kind,'Select actual '+field+' before authoring.')
    if protocol_bytes is not None:raise ValueError('full factor original lattice/rule/source definitions cannot be overridden')
    draft=None
    if not dependencies:
        draft=_draft(specification,inputs)
        expected={row.input_id:row for row in draft.external_inputs};files=dict(inputs.files)
        if set(files)!=set(expected):raise ValueError('full factor selection drops/adds complete original array roles')
        for name,external in expected.items():
            file=files[name]
            if (file.identity.artifact_id,file.identity.sha256,file.identity.size_bytes,file.maximum_bytes)!=(external.logical_artifact_id,external.expected_content_sha256,external.maximum_size_bytes,external.maximum_size_bytes):
                raise ValueError('full factor array FILE binding changes exact original aliased bytes')
    counts=() if draft is None else tuple(sorted(Counter(row.selection.capability_key for row in draft.operations).items()))
    census=ExperimentCensus(() if inputs.programme is None else (('groups',len(inputs.programme.group_ids)),('sources',len(inputs.programme.cases))),
        () if inputs.scope is None else (('groups',len(inputs.scope.programme.group_ids)),('sources',len(inputs.scope.sources))),counts,
        () if draft is None else (('pure-operations',len(draft.operations)),),0)
    design=tuple(sorted((role,getattr(inputs,role.replace('-','_'))) for role in ('request','programme','bank','resources','campaign','reference','original-evidence') if getattr(inputs,role.replace('-','_')) is not None))
    return ExperimentPreparation(specification.identity,census,tuple(sorted(dependencies,key=lambda row:row.code)),allocation=selected_allocation,draft=draft,
        input_records=(),input_files=() if draft is None else inputs.files,execution=execution,specification_record=specification,design_records=design,
        assessment_limitations=(ExperimentDependency('matrix.full-factor.no-qualification',DependencyKind.SCIENTIFIC_EVIDENCE,
            'Original full-history measurements and independent checks do not establish source qualification, sampling, causal useful lifetime, transport or scientific admission.'),))



def validate_instance(*,specification,allocation,draft,source_records):
    records=dict(source_records)
    bound=bind_inputs(specification,records).method_inputs
    if (bound.request is None or bound.request.identity!=specification.request
            or bound.reference is None or bound.reference.scope!=specification.scope or specification.measurement.programme!=bound.programme.identity):
        raise ValueError('full factor instance changes exact original source scope or complete measurement')
    if bound.reference.programme!=bound.programme:raise ValueError('full factor instance substitutes original programme')
    if (bound.campaign is None or ObjectIdentity.from_record(bound.campaign.campaign_id,bound.campaign)!=bound.request.campaign
            or specification.preparation is not None):
        raise ValueError('full factor instance substitutes selected development campaign')
    for role,field in (('programme','programme_id'),('bank','bank_id'),('resources','record_id')):
        value=getattr(bound,role)
        if value is None or ObjectIdentity.from_record(getattr(value,field),value)!=getattr(bound.request,role):
            raise ValueError('full factor instance substitutes exact immutable requested '+role)
    validate_reference(specification,bound)
    expected=_draft(specification,bound)
    if allocation!=programme_allocation(bound.programme,bound.bank) or draft!=expected:
        raise ValueError('full factor instance changes exact ordinary graph, full roster or root/source closure')


def protocol_declarations():
    return tuple(ExperimentProtocolDeclaration(protocol,kind,prepare,consumer,
        input_record_types=input_record_types(),bind_inputs=bind_inputs,validate_instance=validate_instance,
        input_storage_codecs=MATRIX_STORAGE_CODECS,input_file_record_types=tuple(sorted((ScheduledFullFactorScope,r.ScheduledFullFactorSource),key=lambda kind:(kind.SCHEMA,kind.VERSION))),requires_prospective_runtime_binding=False,
        requires_development_runtime_binding=True,
        configuration_inputs=(ExperimentInputConfigurationDeclaration(consumer+'.resources',ScheduledFullFactorResources,128*1024**2),
            ExperimentInputConfigurationDeclaration(consumer+'.request',request_types(protected)[0],128*1024**2)))
        for protocol,kind,consumer,protected in (
            (DEV_PROTOCOL_ID,ScheduledFullFactorDevelopmentSpecification,'experiment.matrix-e4-full-factor-development',False),
            (PROTECTED_PROTOCOL_ID,ScheduledFullFactorProtectedSpecification,'experiment.matrix-e4-full-factor-protected',True)))


def validate_reference(specification,inputs):
    """Exact blind selected ancestry, independently of observation availability."""
    request=inputs.request;reference=inputs.reference
    if request is None or reference is None or inputs.programme is None or inputs.bank is None or inputs.resources is None:
        raise ValueError('full factor reference requires all exact immutable original request roles')
    if (request.identity!=specification.request or reference.scope!=specification.scope or reference.programme!=inputs.programme
            or request.programme!=inputs.programme.identity or request.bank!=inputs.bank.identity or request.resources!=inputs.resources.identity):
        raise ValueError('full factor reference changes requested programme, bank, resource or original scope')
    if reference.protected:
        from .selected_e4_programme import validate_selected_phase_bank
        validate_selected_phase_bank(inputs.programme,inputs.bank)
        if (type(request) not in request_types(True) or reference.declaration!=request.declaration
                or reference.waves!=request.waves or reference.development is not None):
            raise ValueError('full factor reference changes actual requested protected source locators')
    else:
        from .selected_e3_e4_records import validate_development_bank
        validate_development_bank(inputs.programme,inputs.bank)
        if type(request) not in request_types(False) or reference.development!=request.original:
            raise ValueError('full factor reference changes actual requested DEV source locator')
        if (inputs.original_evidence is None or inputs.original_evidence.programme!=inputs.programme.identity
                or inputs.original_evidence.produced_input_parents!=reference.produced_input_parents):
            raise ValueError('full factor reference changes its exact original DEV locator evidence or parent census')
    from .selected_e3_e4_records import selected_original_factor_rule
    rule=selected_original_factor_rule(inputs.bank.forecast_design.criterion_record)
    index=inputs.bank.source_index()
    sources=tuple(inputs.bank.source(case.root_id,index=index) for case in inputs.programme.cases)
    rules={ObjectIdentity.from_record(source.coordinate.coordinate_id,source.coordinate):
        (rule,source.policy.factor_numerical_design) for source in sources}
    expected=ScheduledFullFactorMeasurement(inputs.programme.identity,tuple((coordinate,*value) for coordinate,value in sorted(rules.items(),key=lambda row:row[0].object_id)))
    if specification.measurement!=expected:raise ValueError('full factor specification changes exact original full mathematical definition')
