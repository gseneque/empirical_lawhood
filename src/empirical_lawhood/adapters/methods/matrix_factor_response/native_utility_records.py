# SPDX-License-Identifier: MPL-2.0
"""Distinct E2 acquisition and complete utility contracts over current native science.

No E3 candidate, learned error predictor, TRAIN bank or future E3 reservation is
an operand. Published source records retain their original identities. Fresh
native contact remains the ordinary receipt/native-subwork owner's decision.
"""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support as current_exposure_support
from bisect import bisect_left
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition, MatrixParameterFactorControl
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import METHODS, MatrixParameterHistoryControl, coordinate_identity
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import (
    ROLES, ScheduledCheckpoint, ScheduledNativeEvidence, ScheduledPrefixPolicy, ScheduledPrefixTrace,
    ScheduledReservation, ScheduledSpecification, _publication, _validate_prefix_native_evidence,
    identity as scheduled_identity,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays, ScheduledResponseLossCell, ScheduledResponsePanel, ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_stable_id
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.runtime.experimental_statistics import AssignedBinomialInference, assigned_binomial_inference
from .origin_mechanics import MatrixOriginResponseModel, model_predictors
from .response_scoring import MatrixDenseResponseCell, MatrixDenseResponseDiagnostics
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import validate_response_score
from .records import PREDICTORS
from .response_frontier import MatrixResponseFrontierProtocol, MatrixResponseActionScale

PHASES = ("prefix", "numerical", "measure", "check", "project", "physical-forecast", "responses", "response-score")
ALL_PHASES = tuple(sorted((*PHASES,"entry","terminal")))
NAMESPACE = "matrix-native-utility-v1"


def identity(record):
    for name in ("record_id","specification_id","protocol_id","panel_id","operand_id","history_id","assessment_id","product_id","prefix_id","forecast_id","response_id","score_id"):
        if hasattr(record,name):return ObjectIdentity.from_record(getattr(record,name),record)
    return scheduled_identity(record)


class _Identity:
    __slots__=()
    @property
    def identity(self):return identity(self)


def exact_reference(value,kind):
    if type(value) is not ObjectIdentity or (value.object_schema,value.object_version)!=(kind.SCHEMA,kind.VERSION):
        raise ValueError("native E2 substitutes an exact original record edition")
    value.__post_init__()


def native_source_pins(source):
    return (source.reference.identity,coordinate_identity(source.coordinate),source.provenance.identity)


@dataclass(frozen=True,slots=True)
class NativeUtilityCriterion(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-factor-response/native-utility-criterion"
    record_id:str
    primary_horizon:int
    comparators:tuple[str,...]
    improvement_margin:Decimal
    maximum_view_discrepancy:Decimal
    null_success_numerator:int
    null_success_denominator:int
    alpha_numerator:int
    alpha_denominator:int
    minimum_usable_units:int
    candidate:str="FACTOR"
    estimand:str="FINITE_DT_ODD_RESPONSE_HALF_PLUS_MINUS"
    information:str="SAME_CAUSAL_CUTOFF_STATE_PHYSICS_PRIMARY_FRAME_AND_ORIGIN_HESSIAN"
    predictor_class:str="ZERO_FIT_ORIGIN_LINEARIZED_BAOAB_BOTH_FORCE_KICKS"
    phase_dimensions:tuple[tuple[str,int],...]=(("FACTOR",48),("FULL_COUPLED",192),("GENERIC_SLOW",48),("NORM_RADIUS",24),("SPECTRA",48))
    fitting_budget:int=0
    aggregation:str="MAX_ALL_RECEIVERS_PANELS_ACTIONS_AND_PRECEDING_HORIZONS_PER_WHOLE_ROOT"

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.primary_horizon) is not int or self.primary_horizon<1 or type(self.comparators) is not tuple
                or self.comparators!=tuple(sorted(set(self.comparators))) or "FULL_COUPLED" not in self.comparators
                or any(value not in PREDICTORS or value==self.candidate for value in self.comparators)
                or self.candidate!="FACTOR" or self.estimand!="FINITE_DT_ODD_RESPONSE_HALF_PLUS_MINUS"
                or self.information!="SAME_CAUSAL_CUTOFF_STATE_PHYSICS_PRIMARY_FRAME_AND_ORIGIN_HESSIAN"
                or self.predictor_class!="ZERO_FIT_ORIGIN_LINEARIZED_BAOAB_BOTH_FORCE_KICKS"
                or self.phase_dimensions!=(("FACTOR",48),("FULL_COUPLED",192),("GENERIC_SLOW",48),("NORM_RADIUS",24),("SPECTRA",48))
                or type(self.fitting_budget) is not int or self.fitting_budget!=0
                or self.aggregation!="MAX_ALL_RECEIVERS_PANELS_ACTIONS_AND_PRECEDING_HORIZONS_PER_WHOLE_ROOT"
                or type(self.minimum_usable_units) is not int or self.minimum_usable_units<1):
            raise ValueError("native E2 criterion changes implemented information, capacity, comparison or whole-root estimand")
        for value in (self.improvement_margin,self.maximum_view_discrepancy):validate_decimal(value,field_name="selected finite-dt utility precision",minimum=Decimal(0))
        for n,d in ((self.null_success_numerator,self.null_success_denominator),(self.alpha_numerator,self.alpha_denominator)):
            if type(n) is not int or type(d) is not int or not 0<n<d:raise ValueError("native E2 needs explicit exact null probability and alpha")


@dataclass(frozen=True, slots=True)
class NativeAmendedUtilityCriterion(_Identity, CanonicalRecord):
    """Two fixed E2 questions with FULL_COUPLED retained as a benchmark."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/amended-native-utility-criterion'
    record_id: str
    primary_horizon: int = 128
    comparators: tuple[str, ...] = ('GENERIC_SLOW', 'IO48', 'SPECTRA')
    improvement_margin: Decimal = Decimal('0.001')
    maximum_view_discrepancy: Decimal = Decimal('0.0001')
    null_success_numerator: int = 1
    null_success_denominator: int = 2
    alpha_numerator: int = 1
    alpha_denominator: int = 160
    minimum_usable_units: int = 0
    candidate: str = 'FACTOR'
    adequacy_horizon: int = 32
    adequacy_tolerance: Decimal = Decimal('0.01')
    adequacy_null_numerator: int = 4
    adequacy_null_denominator: int = 5
    phase_dimensions: tuple[tuple[str, int], ...] = (('FACTOR', 48), ('FULL_COUPLED', 192),
        ('GENERIC_SLOW', 48), ('IO48', 48), ('NORM_RADIUS', 24), ('SPECTRA', 48), ('ZERO_RESPONSE', 0))
    fitting_budget: int = 0
    estimand: str = 'FINITE_DT_ODD_RESPONSE_HALF_PLUS_MINUS'
    io48_dimension_rule: str = 'AT_MOST48_WITH_EXPLICIT_REACHABLE_OBSERVABLE_BALANCED_AND_EFFECTIVE_RANKS'

    def __post_init__(self):
        validate_stable_id(self.record_id)
        integers = ('primary_horizon', 'null_success_numerator', 'null_success_denominator',
            'alpha_numerator', 'alpha_denominator', 'minimum_usable_units', 'adequacy_horizon',
            'adequacy_null_numerator', 'adequacy_null_denominator', 'fitting_budget')
        if (any(type(getattr(self, name)) is not int for name in integers)
                or tuple(getattr(self, name) for name in integers) != (128, 1, 2, 1, 160, 0, 32, 4, 5, 0)
                or self.comparators != ('GENERIC_SLOW', 'IO48', 'SPECTRA') or self.candidate != 'FACTOR'
                or type(self.phase_dimensions) is not tuple or any(type(row) is not tuple or len(row) != 2
                    or type(row[0]) is not str or type(row[1]) is not int for row in self.phase_dimensions)
                or self.phase_dimensions != (('FACTOR', 48), ('FULL_COUPLED', 192), ('GENERIC_SLOW', 48),
                    ('IO48', 48), ('NORM_RADIUS', 24), ('SPECTRA', 48), ('ZERO_RESPONSE', 0))
                or self.estimand != 'FINITE_DT_ODD_RESPONSE_HALF_PLUS_MINUS'
                or self.io48_dimension_rule != 'AT_MOST48_WITH_EXPLICIT_REACHABLE_OBSERVABLE_BALANCED_AND_EFFECTIVE_RANKS'):
            raise ValueError('amended E2 changes its two frozen questions, three-challenger conjunction or dimension policy')
        for name, expected in (('improvement_margin', Decimal('0.001')),
                ('maximum_view_discrepancy', Decimal('0.0001')), ('adequacy_tolerance', Decimal('0.01'))):
            if type(getattr(self, name)) is not Decimal or getattr(self, name) != expected:
                raise ValueError('amended E2 changes its exact frozen tolerance or strict improvement margin')


@dataclass(frozen=True,slots=True)
class NativeUtilitySpecification(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-factor-response/native-utility-specification"
    specification_id:str
    root_ids:tuple[str,...]
    mathematical_protocol:ObjectIdentity
    criterion:NativeUtilityCriterion|NativeAmendedUtilityCriterion|None

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        require_sorted_unique_strings(self.root_ids,field_name="all assigned native E2 roots",allow_empty=False)
        exact_reference(self.mathematical_protocol,MatrixResponseFrontierProtocol)
        if self.criterion is not None:
            if type(self.criterion) not in (NativeUtilityCriterion, NativeAmendedUtilityCriterion):raise TypeError("native E2 needs its explicit scientific criterion")
            self.criterion.__post_init__()
            if self.criterion.minimum_usable_units>len(self.root_ids):raise ValueError("native E2 usable criterion exceeds complete denominator")


@dataclass(frozen=True,slots=True)
class NativeUtilitySourceManifest(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-factor-response/native-utility-source-manifest"
    record_id:str
    reservation:ScheduledReservation
    native_specification:ScheduledSpecification
    provenances:tuple[NumericalProducingProvenance,...]
    audit:ScheduledExposureAudit
    audit_publication:ArtifactWriteResult
    reservation_publication:ArtifactWriteResult
    scalar_definition:MatrixParameterScalarDefinition
    scalar_definition_publication:ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value,kind in ((self.reservation,ScheduledReservation),(self.native_specification,ScheduledSpecification),(self.audit,ScheduledExposureAudit),(self.scalar_definition,MatrixParameterScalarDefinition)):
            if type(value) is not kind:raise TypeError("native E2 retains exact generic scheduled source operands")
            value.__post_init__()
        if (type(self.provenances) is not tuple or not self.provenances or any(type(value) is not NumericalProducingProvenance for value in self.provenances)
                or tuple(value.fingerprint() for value in self.provenances)!=tuple(sorted({value.fingerprint() for value in self.provenances}))
                or self.native_specification.selection.reservation!=scheduled_identity(self.reservation)):
            raise ValueError("native E2 source manifest changes provenance or original reservation")
        for value in self.provenances:value.__post_init__()
        for publication,record in ((self.audit_publication,self.audit),(self.reservation_publication,self.reservation),(self.scalar_definition_publication,self.scalar_definition)):
            _publication(publication,record)
        exposure=self.reservation.allocation.exposure
        if (self.audit.census!=exposure.census or self.audit.prior_scheduled_coordinates!=exposure.prior_scheduled_coordinates
                or (exposure.scheduled_audit.payload_schema,exposure.scheduled_audit.media_type,exposure.scheduled_audit.sha256,exposure.scheduled_audit.size_bytes)!=(self.audit.SCHEMA,"application/json",self.audit.fingerprint(),len(self.audit.canonical_bytes()))
                or self.audit_publication.logical.logical_artifact_id!=exposure.scheduled_audit.artifact_id):
            raise ValueError("native E2 changes complete original exposure audit")
        publication=self.scalar_definition_publication
        for policy in self.native_specification.selection.prefix_policies:
            owner=policy.factor_rule.scalar_closure.normalization_owner
            if (owner.artifact_id,owner.payload_schema,owner.sha256,owner.media_type,owner.size_bytes)!=(publication.logical.logical_artifact_id,self.scalar_definition.SCHEMA,self.scalar_definition.fingerprint(),"application/json",len(self.scalar_definition.canonical_bytes())):
                raise ValueError("native E2 changes actual declared scalar normalization source")


@dataclass(frozen=True,slots=True)
class NativeUtilityResources(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-factor-response/native-utility-resources"
    record_id:str
    budgets:tuple[tuple[str,ResourceBudget],...]
    maximum_parallel_tasks:int

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.budgets) is not tuple or tuple(name for name,_ in self.budgets)!=ALL_PHASES
                or type(self.maximum_parallel_tasks) is not int or self.maximum_parallel_tasks<1):raise ValueError("native E2 requires exact phase budgets and explicit worker capacity")
        for _,budget in self.budgets:
            if type(budget) is not ResourceBudget:raise TypeError("native E2 uses ordinary resource budgets")
            budget.__post_init__()
            if budget.cpu_cores!=1 or budget.gpu_devices!=0:raise ValueError("native E2 uses one numerical core per task")

    def for_operation(self,operation):return dict(self.budgets)[operation]


@dataclass(frozen=True,slots=True)
class NativeUtilityRequest(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-factor-response/native-utility-request"
    VERSION: ClassVar[str] = '2.0.0'
    record_id:str
    source_manifest:NativeUtilitySourceManifest
    sources:tuple[ScheduledSource,...]
    protocols:tuple[ScheduledResponseProtocol,...]
    panels:tuple[ScheduledResponsePanel,...]
    mathematical_protocol:MatrixResponseFrontierProtocol
    template_publications:tuple[ArtifactWriteResult,...]
    exposure_support:tuple[tuple[ArtifactIdentity,ArtifactWriteResult|ExperimentFileInputBinding],...]
    campaign:CampaignSpec
    resources:NativeUtilityResources

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value,kind in ((self.source_manifest,NativeUtilitySourceManifest),(self.mathematical_protocol,MatrixResponseFrontierProtocol),(self.campaign,CampaignSpec),(self.resources,NativeUtilityResources)):
            if type(value) is not kind:raise TypeError("native E2 requires its own exact source/scientific/resource selection")
            value.__post_init__()
        for rows,kind,attribute in ((self.sources,ScheduledSource,"root_id"),(self.protocols,ScheduledResponseProtocol,"protocol_id"),(self.panels,ScheduledResponsePanel,"panel_id")):
            require_sorted_unique_ids(rows,attribute=attribute,field_name="complete E2 source/response roster")
            if not rows or any(type(value) is not kind for value in rows):raise TypeError("native E2 changes exact source/protocol/panel types")
            for value in rows:value.__post_init__()


def source_for(request,root_id,*,index):
    position = bisect_left(request.sources, root_id, key=lambda value: value.root_id)
    if position == len(request.sources) or request.sources[position].root_id != root_id:
        raise ValueError("native E2 selects an unassigned root")
    return index.resolve(request.sources[position])


def panels_for(request,source):
    return tuple(value for value in request.panels if value.independent_group_id==source.root.root.independent_group_id)


def validate_request(specification,request):
    if type(specification) is not NativeUtilitySpecification or type(request) is not NativeUtilityRequest:raise TypeError("native E2 needs its own exact specification/request")
    specification.__post_init__();request.__post_init__()
    allocation=request.source_manifest.reservation.allocation
    if (specification.mathematical_protocol!=request.mathematical_protocol.identity
            or tuple(value.root_id for value in request.sources)!=specification.root_ids
            or tuple(sorted(value.public_source.root.root_id for value in request.protocols))!=specification.root_ids
            or tuple(value.root.root_id for value in allocation.roots)!=specification.root_ids
            or any(value.root.role is not MatrixProgrammeRole.DEVELOPMENT for value in allocation.roots)):
        raise ValueError("native E2 changes complete declared root/source/purpose scope")
    groups=tuple(value.root.independent_group_id for value in allocation.roots)
    source_seeds={value.effective_seed for root in allocation.roots for value in root.streams}
    census=allocation.exposure.census
    if len(groups)!=len(set(groups)) or set(groups)&set(census.exposed_independent_groups) or source_seeds&set(census.effective_seed_exclusions):raise ValueError("native E2 overlaps exposed whole groups or actual effective streams")
    if specification.criterion is not None and specification.criterion.primary_horizon not in request.mathematical_protocol.horizon_steps:raise ValueError("native E2 primary horizon is outside its frozen measurement")
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
    ScheduledResponseSelection("response-selection."+request.record_id,ObjectIdentity.from_record(allocation.allocation_id, allocation),tuple(sorted(request.protocols,key=lambda value:value.public_source.root.root_id)),tuple(sorted((group,tuple(value for value in request.panels if value.independent_group_id==group)) for group in groups)),request.template_publications,None).validate_allocation(allocation)
    expected_support={artifact for artifact, _ in current_exposure_support(request.source_manifest.audit)}
    if (type(request.exposure_support) is not tuple or tuple(value.artifact_id for value,_ in request.exposure_support)!=tuple(sorted({value.artifact_id for value,_ in request.exposure_support})) or {value for value,_ in request.exposure_support}!=expected_support):raise ValueError("native E2 omits original current exposure census support")
    for artifact,custody in request.exposure_support:
        if type(artifact) is not ArtifactIdentity or type(custody) not in (ArtifactWriteResult,ExperimentFileInputBinding):raise TypeError("native E2 exposure support needs actual ordinary custody")
        artifact.__post_init__();custody.__post_init__()
        if type(custody) is ExperimentFileInputBinding:
            if custody.identity!=artifact:raise ValueError("native E2 exposure FILE changes exact bytes")
        elif (custody.logical.logical_artifact_id,custody.logical.payload_schema,custody.logical.media_type,custody.logical.content_sha256,custody.materialization.physical_sha256,custody.materialization.size_bytes)!=(artifact.artifact_id,artifact.payload_schema,artifact.media_type,artifact.sha256,artifact.sha256,artifact.size_bytes):raise ValueError("native E2 exposure publication changes exact original bytes")
    template_rows={value.logical.logical_artifact_id:value for value in request.template_publications}
    used_templates=set();used_panels=set();future_seeds=[]
    protocols={value.public_source.root.root_id:value for value in request.protocols}
    index = ScheduledSourceIndex.from_shared(reservation=request.source_manifest.reservation,
        specification=request.source_manifest.native_specification, provenances=request.source_manifest.provenances)
    index.require_roster(request.sources, expected_root_ids=index.root_ids)
    for descriptor in request.sources:
        source=source_for(request,descriptor.root_id,index=index);protocol=protocols[source.root_id]
        protocol.public_source.validate_source(source)
        if specification.criterion is not None and ((type(specification.criterion) is NativeAmendedUtilityCriterion)
                != (type(protocol.mechanical_model) is MatrixOriginResponseModel)):
            raise ValueError('native E2 substitutes the assay bound to its exact old or amended questions')
        # This native route retains the already reviewed original factor/scalar
        # mathematics. Its explicit source policy may restrict the full rule
        # to a causal prefix; that restriction never changes the factor test.
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import validate_selected_prefix_projection
        validate_selected_prefix_projection(request.mathematical_protocol,source.policy,source.policy.cutoff_tick)
        selected=panels_for(request,source);used_panels.update(value.panel_id for value in selected)
        for panel in selected:
            if panel.role=="COMMON_NOISE_PANEL" and panel.streams!=source.root.streams:raise ValueError("native E2 common panel substitutes original source innovations")
            if panel.role=="INDEPENDENT_FUTURE":future_seeds.extend(value.effective_seed for value in panel.streams)
        scales=tuple(sorted((MatrixResponseActionScale(value.role,value.amplitude,value.force_norm,value.pulse_steps) for value in protocol.actions),key=lambda value:value.role))
        if (protocol.criterion!=request.mathematical_protocol.identity or protocol.horizon_steps!=request.mathematical_protocol.horizon_steps
                or source.coordinate.primary_view.timestep!=request.mathematical_protocol.primary_timestep or protocol.receiver_count!=48
                or scales!=request.mathematical_protocol.action_scales or protocol.receiver_gram_tolerance!=request.mathematical_protocol.receiver_gram_tolerance):raise ValueError("native E2 changes fixed paired native estimand/menu/clock/metric")
        artifact=protocol.templates.array_artifact;publication=template_rows.get(artifact.artifact_id)
        if publication is None or (publication.logical.payload_schema,publication.logical.media_type,publication.logical.content_sha256,publication.materialization.physical_sha256,publication.materialization.size_bytes)!=(artifact.payload_schema,artifact.media_type,artifact.sha256,artifact.sha256,artifact.size_bytes):raise ValueError("native E2 changes original template publication")
        used_templates.add(artifact.artifact_id)
    if used_panels!={value.panel_id for value in request.panels} or used_templates!=set(template_rows):raise ValueError("native E2 adds or drops actual panels/templates")
    if len(future_seeds)!=len(set(future_seeds)) or set(future_seeds)&(source_seeds|set(census.effective_seed_exclusions)):raise ValueError("native E2 independent future panels reuse actual effective streams")


def utility_allocation(specification,request):
    validate_request(specification,request)
    units=tuple(sorted((IndependentUnit(value.public_source.root.independent_group_id,request.record_id,value.public_source.coordinate.family_id,("fine","primary"),False) for value in request.protocols),key=lambda value:value.unit_id))
    return UnitAllocation("allocation."+specification.specification_id,(request.identity,),units,tuple(UnitRoleAssignment(value.unit_id,"native-utility") for value in units))


@dataclass(frozen=True,slots=True)
class NativeUtilityAcquisitionSeal(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-factor-response/native-utility-acquisition-seal"
    record_id:str
    specification:ObjectIdentity
    request:ObjectIdentity
    source_reservation:ObjectIdentity
    allocation:ObjectIdentity
    source_roster:tuple[tuple[str,str,ObjectIdentity],...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value,kind in ((self.specification,NativeUtilitySpecification),(self.request,NativeUtilityRequest),(self.source_reservation,ScheduledReservation),(self.allocation,UnitAllocation)):exact_reference(value,kind)
        if (type(self.source_roster) is not tuple or not self.source_roster
                or tuple(root for root,_,_ in self.source_roster)!=tuple(sorted({root for root,_,_ in self.source_roster}))
                or len({unit for _,unit,_ in self.source_roster})!=len(self.source_roster)):
            raise ValueError("native E2 seal drops or duplicates its frozen whole-root/source roster")
        for root,unit,source in self.source_roster:
            validate_stable_id(root);validate_stable_id(unit);exact_reference(source,ScheduledSource)


def acquisition_seal(specification,request):
    if specification.criterion is None:raise ValueError("native E2 cannot enter before its scientific utility criterion is selected")
    return NativeUtilityAcquisitionSeal("seal."+specification.specification_id,specification.identity,request.identity,scheduled_identity(request.source_manifest.reservation),utility_allocation(specification,request).identity,
        tuple(sorted((value.public_source.root.root_id,value.public_source.root.independent_group_id,value.public_source.source) for value in request.protocols)))


@dataclass(frozen=True, slots=True)
class NativeUtilityArrays(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/native-utility-arrays'
    operand_id: str
    source: ObjectIdentity
    role: str
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    producers: tuple[ObjectIdentity, ...]
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        require_sorted_unique_ids(self.members, attribute='name', field_name='members')
        require_sorted_unique_ids(self.producers, attribute='object_id', field_name='producers')
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.role not in ('PREFIX', 'FULL_HISTORY', 'PREFIX_DIAGNOSTICS', 'CAUSAL_STATE')
                or not self.members or not self.producers or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != 'application/x-npz' or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or self.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or self.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
            raise ValueError('scheduled arrays change bounded original causal/protected scope')


@dataclass(frozen=True, slots=True)
class NativeUtilityPrefixHistory(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/native-utility-prefix-history'
    history_id: str
    source: ObjectIdentity
    arrays: NativeUtilityArrays
    checkpoint: ScheduledCheckpoint
    native: ScheduledNativeEvidence
    configuration: ObjectIdentity
    acquisition: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.history_id)
        if (type(self.arrays) is not NativeUtilityArrays or self.arrays.role != 'PREFIX' or self.source != self.arrays.source
                or type(self.checkpoint) is not ScheduledCheckpoint or self.checkpoint.source != self.source
                or type(self.native) is not ScheduledNativeEvidence):
            raise ValueError('scheduled prefix cannot accept sealed full history or exposed source')

    def validate_source(self, source):
        self.__post_init__()
        self.checkpoint.validate_source(source, self.arrays)
        exact_reference(self.acquisition, NativeUtilityAcquisitionSeal)
        _validate_prefix_native_evidence(self, source, configuration=self.configuration,
            parent_task=NAMESPACE + "." + source.root_id + ".prefix", operation=NAMESPACE + ".paired-prefix.v1",
            native_sources={*native_source_pins(source), self.acquisition},
            output_access=OutcomeAccess.DEVELOPMENT_VISIBLE, output_visibility=VisibilityCeiling.DEVELOPMENT_ONLY)


@dataclass(frozen=True, slots=True)
class NativeUtilityNumericalAssessment(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/native-utility-numerical-assessment'
    assessment_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.history.object_schema != NativeUtilityPrefixHistory.SCHEMA
                or tuple(c.control_id for c in self.controls) != METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition == 'SATISFIED' for c in self.controls)):
            raise ValueError('scheduled prefix assessment loses exact independent numerical controls')


@dataclass(frozen=True, slots=True)
class NativeUtilityPrefixWitness(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/native-utility-prefix-witness'
    product_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical: ObjectIdentity
    policy: ObjectIdentity
    traces: tuple[ScheduledPrefixTrace, ...]
    arrays: NativeUtilityArrays

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.history.object_schema != NativeUtilityPrefixHistory.SCHEMA
                or self.numerical.object_schema != NativeUtilityNumericalAssessment.SCHEMA
                or self.policy.object_schema != ScheduledPrefixPolicy.SCHEMA
                or type(self.arrays) is not NativeUtilityArrays or self.arrays.role != 'PREFIX_DIAGNOSTICS'
                or self.arrays.source != self.source or not self.traces):
            raise ValueError('scheduled prefix witness cannot accept full-history E1 diagnostics')


@dataclass(frozen=True, slots=True)
class NativeUtilityFrameAssessment(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/native-utility-frame-assessment'
    assessment_id: str
    source: ObjectIdentity
    witness: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterFactorControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import METHODS as FACTOR_METHODS
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.witness.object_schema != NativeUtilityPrefixWitness.SCHEMA
                or tuple(c.method for c in self.controls) != FACTOR_METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(c.disposition in ('SATISFIED', 'NOT_APPLICABLE') for c in self.controls)):
            raise ValueError('scheduled frame assessment loses complete independent eigenpair controls')


@dataclass(frozen=True, slots=True)
class NativeUtilityCausalPrefix(_Identity, CanonicalRecord):
    """Predictor delivery: causal phase/frame only, never checkpoint/RNG state."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/native-utility-causal-prefix'
    prefix_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical: ObjectIdentity
    witness: ObjectIdentity
    frame_assessment: ObjectIdentity
    policy: ObjectIdentity
    root: MatrixProgrammeRoot
    cutoff_tick: int
    frame_sha256: str | None
    disposition: str
    reason: str | None
    arrays: NativeUtilityArrays

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_sha256
        validate_stable_id(self.prefix_id)
        if self.frame_sha256 is not None:
            validate_sha256(self.frame_sha256)
        if (self.source.object_schema != ScheduledSource.SCHEMA or self.history.object_schema != NativeUtilityPrefixHistory.SCHEMA
                or self.numerical.object_schema != NativeUtilityNumericalAssessment.SCHEMA
                or self.witness.object_schema != NativeUtilityPrefixWitness.SCHEMA
                or self.frame_assessment.object_schema != NativeUtilityFrameAssessment.SCHEMA
                or self.policy.object_schema != ScheduledPrefixPolicy.SCHEMA
                or type(self.root) is not MatrixProgrammeRoot or self.root.role not in ROLES
                or type(self.cutoff_tick) is not int or self.cutoff_tick < 1
                or self.disposition not in ('AVAILABLE', 'NO_ORIGIN', 'UNEVALUABLE')
                or (self.disposition == 'AVAILABLE') != (self.frame_sha256 is not None and self.reason is None)
                or self.disposition != 'AVAILABLE' and self.reason is None
                or type(self.arrays) is not NativeUtilityArrays or self.arrays.role != 'CAUSAL_STATE' or self.arrays.source != self.source):
            raise ValueError('causal delivery changes exact cutoff/role or manufactures available frame')


@dataclass(frozen=True, slots=True)
class NativeUtilityPhysicalForecast(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/native-utility-response-forecast'
    forecast_id: str
    source: ObjectIdentity
    causal_prefix: ObjectIdentity
    protocol: ObjectIdentity
    mechanical_model: ObjectIdentity
    frame_sha256: str | None
    arrays: ScheduledResponseArrays
    disposition: str
    dispositions: tuple[tuple[str, str, str, str | None], ...]

    def __post_init__(self):
        validate_stable_id(self.forecast_id)
        expected = tuple((v, p) for v in ('PRIMARY', 'FINE') for p in model_predictors(self.mechanical_model))
        if (self.causal_prefix.object_schema != NativeUtilityCausalPrefix.SCHEMA
                or self.protocol.object_schema != ScheduledResponseProtocol.SCHEMA or self.arrays.role != 'FORECAST'
                or self.arrays.source != self.source or tuple((v, p) for v, p, _, _ in self.dispositions) != expected
                or self.disposition not in ('AVAILABLE', 'NO_ORIGIN', 'UNEVALUABLE', 'INSTRUMENT_UNRESOLVED')
                or any(s not in ('AVAILABLE', 'UNRESOLVED') or (s == 'AVAILABLE') != (reason is None)
                    for _, _, s, reason in self.dispositions)):
            raise ValueError('scheduled forecast thins full paired predictor/menu or manufactures availability')


@dataclass(frozen=True, slots=True)
class NativeUtilityResponse(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/native-utility-native-responses'
    response_id: str
    source: ObjectIdentity
    causal_prefix: ObjectIdentity
    physical_forecast: ObjectIdentity
    acquisition_seal: ObjectIdentity
    protocol: ObjectIdentity
    arrays: ScheduledResponseArrays
    branch_ids: tuple[str, ...]
    native: tuple[ScheduledNativeEvidence, ...]
    disposition: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.response_id)
        if (self.arrays.source != self.source or self.arrays.role != 'RESPONSES'
                or self.branch_ids != tuple(sorted(set(self.branch_ids)))
                or self.disposition not in ('COMPLETED', 'NO_ORIGIN', 'UNEVALUABLE', 'INSTRUMENT_UNRESOLVED')
                or (self.disposition == 'COMPLETED') != bool(self.native)
                or self.native and len(self.native) != 1
                or any(type(n) is not ScheduledNativeEvidence for n in self.native)):
            raise ValueError('scheduled response changes actual branch/native/nonuse census')


    def validate_nonentry(self, causal, physical, protocol, panels):
        """Require exact unavailable-operand nonuse without opening array bytes."""
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import validate_native_response_nonentry
        return validate_native_response_nonentry(self, causal, physical, protocol, panels)

    @property
    def error_forecast(self):
        """Local received-array interface; canonical evidence names the real acquisition seal."""
        return self.acquisition_seal


@dataclass(frozen=True, slots=True)
class NativeUtilityScore(_Identity, CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/native-utility-response-score'
    VERSION: ClassVar[str] = '2.0.0'
    score_id: str
    source: ObjectIdentity
    causal_prefix: ObjectIdentity
    acquisition_seal: ObjectIdentity
    physical_forecast: ObjectIdentity
    responses: ObjectIdentity
    root_id: str
    independent_group_id: str
    role: str
    criterion: ObjectIdentity
    controls: tuple[ScheduledResponseTransitionControl, ...]
    numerical_pass: bool
    disposition: str
    cells: tuple[ScheduledResponseLossCell | MatrixDenseResponseCell, ...]
    cumulative_log_errors: tuple[Decimal | None, ...]
    reason_codes: tuple[str, ...]
    dense: MatrixDenseResponseDiagnostics | None = None

    def __post_init__(self):
        validate_response_score(self)

    @property
    def error_forecast(self):
        """Local received-array interface; canonical evidence names the real acquisition seal."""
        return self.acquisition_seal




@dataclass(frozen=True, slots=True)
class NativeUtilityAmendedEndpoints(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/amended-native-utility-endpoints'
    adequacy: bool | None
    structural_advantage: bool | None
    zero_adequacy: bool | None

    def __post_init__(self):
        if any(value is not None and type(value) is not bool for value in
                (self.adequacy, self.structural_advantage, self.zero_adequacy)):
            raise ValueError('amended E2 endpoint changes an explicit observed/unknown event')

    @property
    def joint_adequacy_advantage(self):
        if self.adequacy is False or self.structural_advantage is False:
            return False
        return None if self.adequacy is None or self.structural_advantage is None else True

    @property
    def factor_adequate_zero_inadequate(self):
        if self.adequacy is False or self.zero_adequacy is True:
            return False
        return None if self.adequacy is None or self.zero_adequacy is None else True


@dataclass(frozen=True,slots=True)
class NativeUtilityOutcome(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-factor-response/native-utility-outcome"
    VERSION: ClassVar[str] = '2.0.0'
    record_id:str
    specification:ObjectIdentity
    acquisition:ObjectIdentity
    root_id:str
    unit_id:str
    source:ObjectIdentity
    score:ObjectIdentity
    losses:tuple[tuple[str,str,int,Decimal|None],...]
    contrasts:tuple[tuple[str,str,Decimal|None],...]
    usable:bool
    success:bool
    numerical_disposition:str
    reason_codes:tuple[str,...]
    amended: NativeUtilityAmendedEndpoints | None = None

    def __post_init__(self):
        for value in (self.record_id,self.root_id,self.unit_id):validate_stable_id(value)
        for value,kind in ((self.specification,NativeUtilitySpecification),(self.acquisition,NativeUtilityAcquisitionSeal),(self.source,ScheduledSource),(self.score,NativeUtilityScore)):exact_reference(value,kind)
        if (type(self.usable) is not bool or type(self.success) is not bool or self.success and not self.usable
                or self.numerical_disposition not in ("SATISFIED","VIOLATED","UNEVALUABLE")
                or type(self.losses) is not tuple or tuple((v,p,h) for v,p,h,_ in self.losses)!=tuple(sorted({(v,p,h) for v,p,h,_ in self.losses}))
                or type(self.contrasts) is not tuple or tuple((v,p) for v,p,_ in self.contrasts)!=tuple(sorted({(v,p) for v,p,_ in self.contrasts}))):raise ValueError("native E2 outcome changes complete loss/contrast/nonuse scope")
        for _,_,_,value in self.losses:
            if value is not None:validate_decimal(value,field_name="native E2 finite loss",minimum=Decimal(0))
        for _,_,value in self.contrasts:
            if value is not None:validate_decimal(value,field_name="paired comparator loss minus factor loss")
        require_sorted_unique_strings(self.reason_codes,field_name="native E2 adverse/nonuse reasons")
        if self.amended is not None:
            if type(self.amended) is not NativeUtilityAmendedEndpoints:
                raise TypeError('amended E2 requires its exact paired endpoint records')
            self.amended.__post_init__()
            if self.success != (self.amended.structural_advantage is True) or self.usable != (self.amended.structural_advantage is not None):
                raise ValueError('amended E2 substitutes the common three-challenger event')



@dataclass(frozen=True, slots=True)
class NativeUtilityAmendedInference(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/amended-native-utility-inference'
    adequacy: AssignedBinomialInference
    structural_advantage: AssignedBinomialInference

    def __post_init__(self):
        for record, null in ((self.adequacy, (4, 5)), (self.structural_advantage, (1, 2))):
            if (type(record) is not AssignedBinomialInference
                    or (record.null_numerator, record.null_denominator) != null
                    or (record.alpha_numerator, record.alpha_denominator) != (1, 160)):
                raise ValueError('amended E2 changes its exact two primary nulls or family allocation')
            record.__post_init__()
        if self.adequacy.unit_ids != self.structural_advantage.unit_ids:
            raise ValueError('amended E2 primary questions substitute the common whole assigned roster')

    def validate_outcomes(self, outcomes, missing_unit_ids=()):
        by_unit = {value.unit_id: value for value in outcomes}
        units = tuple(sorted((*by_unit, *missing_unit_ids)))
        if (units != self.adequacy.unit_ids or len(by_unit) != len(outcomes)
                or any(value.amended is None for value in outcomes)):
            raise ValueError('amended E2 inference drops, repeats or substitutes an assigned observed/missing root')
        for name in ('adequacy', 'structural_advantage'):
            expected = tuple(None if unit not in by_unit else getattr(by_unit[unit].amended, name) for unit in units)
            if getattr(self, name).events != expected:
                raise ValueError('amended E2 inference changes an actual known or unresolved whole-root event')


def amended_utility_inference(outcomes, missing_unit_ids=()):
    from fractions import Fraction
    by_unit = {value.unit_id: value for value in outcomes}
    units = tuple(sorted((*by_unit, *missing_unit_ids)))
    if len(by_unit) != len(outcomes) or any(value.amended is None for value in outcomes):
        raise ValueError('amended E2 inference requires distinct actual amended outcomes')
    events = {name: tuple(None if unit not in by_unit else getattr(by_unit[unit].amended, name) for unit in units)
        for name in ('adequacy', 'structural_advantage')}
    result = NativeUtilityAmendedInference(
        assigned_binomial_inference(units, events['adequacy'], null_probability=Fraction(4, 5), alpha=Fraction(1, 160)),
        assigned_binomial_inference(units, events['structural_advantage'], null_probability=Fraction(1, 2), alpha=Fraction(1, 160)))
    result.validate_outcomes(outcomes, missing_unit_ids)
    return result


@dataclass(frozen=True,slots=True)
class NativeUtilitySummary(_Identity,CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-factor-response/native-utility-summary"
    VERSION: ClassVar[str] = '2.0.0'
    record_id:str
    specification:ObjectIdentity
    acquisition:ObjectIdentity
    outcomes:tuple[NativeUtilityOutcome,...]
    assigned_units:int
    usable_units:int
    successes:int
    tail_numerator:int
    tail_denominator:int
    conditional_criterion_met:bool
    scientific_status:str="UNEVALUABLE"
    qualification:str="NOT_ESTABLISHED"
    sampling_warrant:str="NOT_ESTABLISHED"
    numerical_scope:str="FINITE_DT_EMPIRICAL_CROSSCHECK_NOT_CONTINUUM_ERROR_ENCLOSURE"
    amended: NativeUtilityAmendedInference | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_reference(self.specification,NativeUtilitySpecification);exact_reference(self.acquisition,NativeUtilityAcquisitionSeal)
        require_sorted_unique_ids(self.outcomes,attribute="unit_id",field_name="complete E2 whole-unit outcomes")
        if (not self.outcomes or any(type(value) is not NativeUtilityOutcome for value in self.outcomes)
                or len({value.root_id for value in self.outcomes})!=len(self.outcomes)
                or any(value.specification!=self.specification or value.acquisition!=self.acquisition for value in self.outcomes)
                or type(self.assigned_units) is not int or self.assigned_units!=len(self.outcomes)
                or type(self.usable_units) is not int or self.usable_units!=sum(value.usable for value in self.outcomes)
                or type(self.successes) is not int or self.successes!=sum(value.success for value in self.outcomes)
                or type(self.tail_numerator) is not int or type(self.tail_denominator) is not int or not 0<=self.tail_numerator<=self.tail_denominator
                or self.tail_denominator<1 or type(self.conditional_criterion_met) is not bool
                or (self.scientific_status,self.qualification,self.sampling_warrant,self.numerical_scope)!=("UNEVALUABLE","NOT_ESTABLISHED","NOT_ESTABLISHED","FINITE_DT_EMPIRICAL_CROSSCHECK_NOT_CONTINUUM_ERROR_ENCLOSURE")):
            raise ValueError("native E2 summary thins denominator or promotes conditional utility arithmetic")
        for value in self.outcomes:value.__post_init__()
        if self.amended is not None:
            if type(self.amended) is not NativeUtilityAmendedInference:
                raise TypeError('amended E2 summary requires the complete two-question inference')
            self.amended.__post_init__()
            self.amended.validate_outcomes(self.outcomes)
            structural = self.amended.structural_advantage
            if ((self.successes, self.tail_numerator, self.tail_denominator, self.conditional_criterion_met) !=
                    (structural.successes, structural.tail_numerator, structural.tail_denominator, structural.criterion_met)):
                raise ValueError('amended E2 summary changes its declared structural event arithmetic')
        elif any(value.amended is not None for value in self.outcomes):
            raise ValueError('amended E2 summary drops one or both declared primary questions')
