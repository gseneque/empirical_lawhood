# SPDX-License-Identifier: MPL-2.0
"""Declarative complete E4 programme and ordinary issued component preparation."""

from collections.abc import Mapping
from dataclasses import dataclass,replace
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixE4StructuralChoices
from empirical_lawhood.kernel.experimental_design import IndependentUnit,UnitAllocation,UnitRoleAssignment
from empirical_lawhood.kernel.evidence import EvidenceCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord,validate_stable_id,require_sorted_unique_ids,canonical_json_bytes
from empirical_lawhood.planning.experiment_entry import ExperimentEntryPackage,validate_experiment_entry
from empirical_lawhood.planning.formal_analysis import FormalMethodCatalog,FormalMethodRole,FormalGapSourceCapabilityInventory,derive_formal_gap_applicability
from empirical_lawhood.planning.formal_gaps import FormalGapCoverageDisposition
from empirical_lawhood.kernel.status import ReadinessStatus
from empirical_lawhood.planning.study_authoring import MaterializationQualificationReceipt
from empirical_lawhood.runtime.experiment_preparation import (ExperimentPreparation,ExperimentCensus,ExperimentDependency,
    DependencyKind,ExecutionSelection,PreparedExperimentInputs,PreparedExperimentFile,ExperimentProtocolDeclaration)
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs,RecursiveProspectiveOperand
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig

from . import selected_e4_native_records as r,selected_e4_native_bindings as native,selected_e4_programme as p
from . import selected_e4_method_bindings as methods
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import (
    MatrixE4SecondaryReadoutSelection,
)

from .full_factor_followup_records import ScheduledFullFactorResources
from .selected_e4_operational_resources import SelectedE4OperationalResources,derive_selected_e4_resources
from .protected_factorial_preparation import _source_projection

PROGRAMME_PROTOCOL_ID="matrix.e4.selected-protected-programme"
COMPONENT_PROTOCOL_ID="matrix.e4.selected-protected-component"
ASSESSMENT_COMPONENT_ID="assessment"


@dataclass(frozen=True,slots=True)
class SelectedE4ProtectedProgrammeSpecification(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/protected-programme-specification"
    specification_id:str
    declaration:ObjectIdentity
    population_phase:str
    independent_group_count:int
    cases_per_group:int
    question:str

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        r.exact_pin(self.declaration,r.SelectedE4NativeProgrammeDeclaration)
        if (self.population_phase not in r.POPULATIONS or type(self.independent_group_count) is not int or self.independent_group_count<1
                or self.cases_per_group!=9 or type(self.cases_per_group) is not int or not self.question.strip()):
            raise ValueError("selected E4 full programme specification changes its declared whole-group grid")

    @property
    def identity(self):return r.pin(self,"specification_id")


@dataclass(frozen=True,slots=True)
class SelectedE4NativeComponentSpecification(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/native-component-specification"
    specification_id:str
    declaration:ObjectIdentity
    component_id:str
    wave_id:str|None
    stage:str

    def __post_init__(self):
        validate_stable_id(self.specification_id);validate_stable_id(self.component_id)
        r.exact_pin(self.declaration,r.SelectedE4NativeProgrammeDeclaration)
        if ((self.stage=="ACQUIRE_WAVE")!=(self.wave_id is not None)
                or self.stage not in ("ACQUIRE_WAVE","ASSESS_PHASE")
                or self.component_id!=(self.wave_id if self.wave_id is not None else ASSESSMENT_COMPONENT_ID)):
            raise ValueError("selected E4 component cannot substitute a subset for its declared full phase")

    @property
    def identity(self):return r.pin(self,"specification_id")


@dataclass(frozen=True,slots=True)
class SelectedE4ProtectedTailSelection(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/protected-tail-selection"
    record_id:str
    revision:p.SelectedE4RevisionExport
    resources:methods.SelectedE4MethodResources
    calibration: p.SelectedE4CalibrationSpecification|None
    confirmation:methods.SelectedE4ConfirmationScope|None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.revision) is not p.SelectedE4RevisionExport or type(self.resources) is not methods.SelectedE4MethodResources
                or (self.calibration is None)==(self.confirmation is None)
                or self.calibration is not None and type(self.calibration) is not p.SelectedE4CalibrationSpecification
                or self.confirmation is not None and type(self.confirmation) is not methods.SelectedE4ConfirmationScope):
            raise TypeError("selected E4 tail requires exact declared CAL or CONF scientific choices")
        for v in (self.revision,self.resources,self.calibration,self.confirmation):
            if v is not None:v.__post_init__()

    @property
    def identity(self):return r.pin(self)


@dataclass(frozen=True,slots=True)
class SelectedE4ProgrammePreparationSelectionV2(CanonicalRecord):
    """Component-aware formal preparation for the complete protected phase."""
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/programme-preparation-selection"
    VERSION:ClassVar[str]="2.0.0"
    record_id:str
    entry:ExperimentEntryPackage
    formal_methods:FormalMethodCatalog
    formal_source_inventories:tuple[FormalGapSourceCapabilityInventory,...]
    qualifications:tuple[MaterializationQualificationReceipt,...]
    source_configs:tuple[SourceMaterializationConfig,...]
    resources:SelectedE4OperationalResources

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for v,k in ((self.entry,ExperimentEntryPackage),(self.formal_methods,FormalMethodCatalog)):
            if type(v) is not k:raise TypeError("selected E4 requires actual existing entry and formal methods")
            v.__post_init__()
        for values,kind,key in ((self.formal_source_inventories,FormalGapSourceCapabilityInventory,"denominator_id"),
                (self.qualifications,MaterializationQualificationReceipt,"receipt_id"),(self.source_configs,SourceMaterializationConfig,"source_id")):
            if type(values) is not tuple or any(type(v) is not kind for v in values):raise TypeError("selected E4 needs exact immutable source/formal qualification rosters")
            require_sorted_unique_ids(values,attribute=key,field_name=key)
            for v in values:v.__post_init__()
        if type(self.resources) is not SelectedE4OperationalResources:
            raise TypeError("selected E4 resources require one explicit operational phase profile")
        self.resources.__post_init__()

    @property
    def identity(self):return r.pin(self)


@dataclass(frozen=True,slots=True)
class SelectedE4ProtectedProgrammePlan(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/protected-programme-plan"
    VERSION:ClassVar[str]="3.0.0"
    plan_id:str
    specification:SelectedE4ProtectedProgrammeSpecification
    declaration:r.SelectedE4NativeProgrammeDeclaration
    bank:p.SelectedE4PhaseBank
    evidence:r.SelectedE4ProtectedEvidence
    preparation:SelectedE4ProgrammePreparationSelectionV2
    tail:SelectedE4ProtectedTailSelection
    structure:MatrixE4StructuralChoices
    secondary_readout:MatrixE4SecondaryReadoutSelection
    structural_resources:ScheduledFullFactorResources

    def __post_init__(self):
        validate_stable_id(self.plan_id)
        for v,k in ((self.specification,SelectedE4ProtectedProgrammeSpecification),(self.declaration,r.SelectedE4NativeProgrammeDeclaration),
                (self.bank,p.SelectedE4PhaseBank),(self.evidence,r.SelectedE4ProtectedEvidence),
                (self.tail,SelectedE4ProtectedTailSelection),(self.structure,MatrixE4StructuralChoices),
                (self.structural_resources,ScheduledFullFactorResources)):
            if type(v) is not k:raise TypeError("selected E4 programme requires its complete exact immutable full plan")
            v.__post_init__()
        if type(self.preparation) is not SelectedE4ProgrammePreparationSelectionV2:
            raise TypeError("selected E4 programme requires its exact component-aware formal preparation")
        self.preparation.__post_init__()
        if type(self.secondary_readout) is not MatrixE4SecondaryReadoutSelection:
            raise TypeError("E4 programme requires its actual pre-future target publication selection")
        self.secondary_readout.validate_target(self.structure.secondary_target)
        for protocol in self.bank.response_selection.protocols:
            self.structure.secondary_target.validate_protocol(protocol)
        from .selected_e4_structure import structural_measurement
        structural_measurement(programme=self.declaration.programme,bank=self.bank,choices=self.structure)
        d=self.declaration
        validate_component_formal_selection(d.root,self.preparation.entry,self.preparation.formal_methods,d.bank_phase)
        r.validate_evidence(self.evidence,d.programme,self.bank,d.decision,d.models,d.calibration)
        if self.evidence.produced_input_parents != d.produced_input_parents:
            raise ValueError("selected E4 plan changes its exact actual produced-parent census")
        original=self.bank.forecast_design.package
        if (d.original_summary.original_package,d.original_summary.calibration,d.original_summary.models,
                d.original_summary.model_freeze,d.original_summary.calibrated_freeze)!=(original.original_package,original.calibration,
                r.identity(original.models),r.identity(original.model_freeze),r.identity(original.calibrated_freeze)):
            raise ValueError("selected E4 full plan changes original E3 calibration/model lineage")
        if (self.bank.identity!=d.bank or self.evidence.identity!=d.evidence or self.specification.declaration!=d.identity
                or (self.specification.population_phase,self.specification.independent_group_count,self.specification.cases_per_group)!=(
                    d.bank_phase,len(d.programme.group_ids),d.programme.design.cases_per_group)
                or tuple(k for k,_ in self.component_resources)!=tuple(sorted((*[v.wave_id for v in d.programme.waves],ASSESSMENT_COMPONENT_ID)))
                or any(v.maximum_parallel_tasks!=d.maximum_parallel_tasks for _,v in self.component_resources)
                or (self.tail.revision.decision,self.tail.revision.models)!=(d.decision,d.models)
                or (d.bank_phase=="CALIBRATION")!=(self.tail.calibration is not None)
                or len(self.canonical_bytes())>64*1024**2):
            raise ValueError("selected E4 plan changes full frozen phase, declared resources/models or bounded metadata")
        for wave in d.programme.waves:
            resources=dict(self.component_resources)[wave.wave_id]
            expected={native.global_node(d.programme,phase,wave.wave_id):dict(d.budgets.phase_budgets)[phase] for phase in ("entry","reduce")}
            expected[native.global_node(d.programme,"adjudicate",wave.wave_id)]=d.budgets.collector_budget
            expected.update({native.local_node(root,phase):dict(d.budgets.phase_budgets)[phase]
                for root in wave.root_ids for phase in native.PHASES if phase not in ("entry","reduce")})
            validate_component_resources(resources,expected)

    @property
    def identity(self):return r.pin(self,"plan_id")

    @property
    def component_ids(self):return tuple(v.wave_id for v in self.declaration.programme.waves)+(ASSESSMENT_COMPONENT_ID,)

    @property
    def component_resources(self):return derive_selected_e4_resources(self.declaration,self.tail,self.preparation.resources)



@dataclass(frozen=True,slots=True)
class SelectedE4PhaseCollectionSelection(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/phase-collection-selection"
    record_id:str
    evidence:r.SelectedE4PhaseCollectionEvidence
    observations:tuple[ArtifactIdentity,...]
    qualifications:tuple[MaterializationQualificationReceipt,...]
    source_configs:tuple[SourceMaterializationConfig,...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.evidence) is not r.SelectedE4PhaseCollectionEvidence:raise TypeError("selected E4 assessment needs actual complete wave locators")
        self.evidence.__post_init__()
        if (type(self.observations) is not tuple or any(type(v) is not ArtifactIdentity for v in self.observations)
                or tuple((v.artifact_id,v.payload_schema,v.sha256,v.size_bytes) for v in self.observations)!=tuple(
                    (v.observation.object_id,v.observation.object_schema,v.observation.object_fingerprint,v.size_bytes) for v in self.evidence.waves)):
            raise ValueError("selected E4 assessment substitutes actual complete wave observation artifacts")
        for rows,kind,key in ((self.qualifications,MaterializationQualificationReceipt,"receipt_id"),(self.source_configs,SourceMaterializationConfig,"source_id")):
            if type(rows) is not tuple or any(type(v) is not kind for v in rows):raise TypeError("selected E4 assessment needs exact produced-input source admissions")
            require_sorted_unique_ids(rows,attribute=key,field_name=key)

    @property
    def identity(self):return r.pin(self)


@dataclass(frozen=True,slots=True)
class SelectedE4NativeComponentInputs(CanonicalRecord):
    """One component's exact reference to the actual published full plan."""
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/native-component-inputs"
    VERSION:ClassVar[str]="3.0.0"
    record_id:str
    plan:ObjectIdentity
    plan_publication:ArtifactWriteResult
    upstream_products:tuple[MatrixSelectedOriginalProduct,...]
    calibration_product:MatrixSelectedOriginalProduct|None
    component_id:str
    declaration_publication:ArtifactWriteResult
    collection:SelectedE4PhaseCollectionSelection|None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        r.exact_pin(self.plan,SelectedE4ProtectedProgrammePlan)
        validate_stable_id(self.component_id)
        validate_component_original_products(self.upstream_products,self.calibration_product)
        publication=self.plan_publication
        from empirical_lawhood.runtime.artifacts import ArtifactProfile
        if (type(publication) is not ArtifactWriteResult
                or publication.logical.logical_artifact_id!=self.plan.object_id
                or publication.logical.payload_schema!=self.plan.object_schema
                or publication.logical.content_sha256!=self.plan.object_fingerprint
                or publication.logical.profile is not ArtifactProfile.CANONICAL_JSON
                or publication.logical.media_type!="application/json"
                or publication.materialization.logical_artifact_id!=self.plan.object_id
                or publication.materialization.physical_sha256!=self.plan.object_fingerprint
                or publication.materialization.compression!="none"
                or not 0<publication.materialization.size_bytes<=64*1024**2):
            raise ValueError("selected component requires its exact actual published programme plan")
        publication.__post_init__()
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import validate_produced_input_parents, produced_access
        validate_produced_input_parents(publication.logical.lineage_parents)
        if (publication.logical.outcome_access,publication.logical.visibility_ceiling)!=produced_access(
                declared_access=r.BLIND,declared_visibility=r.PROSPECTIVE,parents=publication.logical.lineage_parents):
            raise ValueError("selected E4 shared plan drops its actual inherited access")
        if type(self.declaration_publication) is not ArtifactWriteResult:
            raise TypeError("selected component requires its actual declaration publication")
        self.declaration_publication.__post_init__()
        if self.collection is not None:
            if type(self.collection) is not SelectedE4PhaseCollectionSelection:raise TypeError("selected phase needs exact original wave inputs")
            self.collection.__post_init__()
            if self.component_id!=ASSESSMENT_COMPONENT_ID:
                raise ValueError("native wave cannot consume later collection outcomes")

    @property
    def identity(self):return r.pin(self)


@dataclass(frozen=True,slots=True)
class ResolvedSelectedE4ComponentInputs:
    """Ephemeral pure lowering view; never a canonical retained source body."""
    plan:SelectedE4ProtectedProgrammePlan
    component_id:str
    declaration_publication:ArtifactWriteResult
    collection:SelectedE4PhaseCollectionSelection|None

    def __post_init__(self):
        if type(self.plan) is not SelectedE4ProtectedProgrammePlan:
            raise TypeError("selected component needs its resolved full programme plan")
        self.plan.__post_init__()
        if self.component_id not in self.plan.component_ids:
            raise ValueError("selected component is outside its complete original programme")
        validate_produced_publication(self.declaration_publication,self.plan.declaration,self.plan.evidence.produced_input_parents)
        if self.collection is not None:
            if type(self.collection) is not SelectedE4PhaseCollectionSelection:
                raise TypeError("selected assessment needs its exact collection binding")
            self.collection.__post_init__()
            if (self.component_id!=ASSESSMENT_COMPONENT_ID
                    or self.collection.evidence.declaration!=self.plan.declaration.identity):
                raise ValueError("selected component changes original phase collection")


def validate_component_original_products(upstream_products,calibration_product):
    if (type(upstream_products) is not tuple or len(upstream_products)!=4
            or any(type(value) is not MatrixSelectedOriginalProduct for value in upstream_products)
            or tuple(value.record.object_id for value in upstream_products)!=tuple(sorted({value.record.object_id for value in upstream_products}))
            or calibration_product is not None and type(calibration_product) is not MatrixSelectedOriginalProduct):
        raise TypeError("selected E4 component requires its exact four original E3 and optional CAL locators")
    for value in (*upstream_products,*((calibration_product,) if calibration_product is not None else ())):
        value.__post_init__()


def validate_produced_publication(publication,record,parents):
    """Exact immutable body/labels only; the API separately checks permission."""
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeProducedInput
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access,validate_produced_input_parents
    validate_produced_input_parents(parents)
    MatrixProgrammeProducedInput(record.identity,publication).require_record(record,record.identity)
    if (publication.logical.logical_artifact_id!=record.identity.object_id
            or publication.logical.lineage_parents!=parents
            or (publication.logical.outcome_access,publication.logical.visibility_ceiling)!=produced_access(
                declared_access=r.BLIND,declared_visibility=r.PROSPECTIVE,parents=parents)):
        raise ValueError("selected E4 produced publication changes actual lineage or inherited access")


def resolve_component_inputs(selection,plan):
    """Join exact typed bodies only; the API authenticates physical publication."""
    if type(selection) is not SelectedE4NativeComponentInputs:
        raise TypeError("selected component requires its current published-plan reference")
    selection.__post_init__()
    if type(plan) is not SelectedE4ProtectedProgrammePlan or plan.identity!=selection.plan:
        raise ValueError("selected component substitutes its published programme plan")
    if (selection.upstream_products!=plan.evidence.upstream_products
            or selection.calibration_product!=plan.evidence.calibration_product
            or selection.plan_publication.logical.lineage_parents!=plan.evidence.produced_input_parents):
        raise ValueError("selected E4 component changes exact plan bytes, original access locators or produced parents")
    validate_produced_publication(selection.plan_publication,plan,plan.evidence.produced_input_parents)
    return ResolvedSelectedE4ComponentInputs(plan,selection.component_id,
        selection.declaration_publication,selection.collection)


def validate_component_resources(resources,expected):
    if {v.task_id for v in resources.task_cells}!=set(expected) or len(resources.task_cells)!=len(expected):
        raise ValueError("selected E4 resource cells change actual complete declared task census")
    for cell in resources.task_cells:
        budget=expected[cell.task_id]
        actual=cell.resource_budget
        if (budget.wall_time_seconds is not None or (actual.cpu_cores,actual.memory_bytes,actual.source_byte_limit,actual.output_bytes)!=(budget.cpu_cores,budget.memory_bytes,
                budget.source_scan_bytes,budget.output_bytes) or budget.gpu_devices!=0):
            raise ValueError("selected E4 resource cells substitute exact frozen phase reservations")


def component_specification(plan,component_id):
    if component_id not in plan.component_ids:raise ValueError("selected E4 component is outside the frozen full phase")
    return SelectedE4NativeComponentSpecification("specification."+plan.plan_id+"."+component_id,plan.declaration.identity,
        component_id,None if component_id==ASSESSMENT_COMPONENT_ID else component_id,
        "ASSESS_PHASE" if component_id==ASSESSMENT_COMPONENT_ID else "ACQUIRE_WAVE")


def programme_allocation(plan,*,group_ids=None):
    d=plan.declaration;programme=d.programme
    groups=programme.group_ids if group_ids is None else group_ids
    if not set(groups)<=set(programme.group_ids):raise ValueError("selected E4 allocation adds undeclared original units")
    units=[]
    index=plan.bank.source_index()
    for group in groups:
        cases=tuple(v for v in programme.cases if v.independent_group_id==group)
        views=tuple(sorted({v.view_id for c in cases for v in (plan.bank.source(c.root_id,index=index).coordinate.primary_view,
            plan.bank.source(c.root_id,index=index).coordinate.fine_view)}))
        units.append(IndependentUnit(group,plan.bank.reservation.allocation.allocation_id,cases[0].family_id,views,False))
    return UnitAllocation("allocation."+plan.plan_id+"."+("complete" if group_ids is None else sha256(canonical_json_bytes(groups)).hexdigest()),
        tuple(sorted((d.identity,programme.identity,d.bank,
            ObjectIdentity.from_record(plan.bank.reservation.allocation.allocation_id,plan.bank.reservation.allocation)),key=lambda v:v.object_id)),tuple(units),
        tuple(UnitRoleAssignment(group,d.bank_phase.lower()) for group in groups))


def bind_programme_inputs(specification,records,**kwargs):
    if not isinstance(records,Mapping) or set(records)!={"plan"} or type(records["plan"]) is not SelectedE4ProtectedProgrammePlan:
        raise ValueError("selected full programme requires exactly its declared complete plan")
    plan=records["plan"]
    if plan.specification!=specification:raise ValueError("selected E4 plan substitutes its exact scientific specification")
    return PreparedExperimentInputs({plan.declaration.bank_phase.lower():programme_allocation(plan)},plan)


def prepare_programme(specification,*,scientific_inputs,execution,protocol_bytes=None,method_inputs=None):
    if type(specification) is not SelectedE4ProtectedProgrammeSpecification or type(execution) is not ExecutionSelection:
        raise TypeError("selected full E4 preparation requires its exact specification and explicit execution selection")
    if type(method_inputs) is not SelectedE4ProtectedProgrammePlan:
        raise ValueError("selected full E4 preparation needs its actual full source/phase/resource plan")
    plan=method_inputs;plan.__post_init__()
    if plan.specification!=specification or execution.workers!=plan.declaration.maximum_parallel_tasks:
        raise ValueError("selected E4 changes full plan or explicitly selected worker count")
    allocation=programme_allocation(plan)
    if scientific_inputs!={plan.declaration.bank_phase.lower():allocation}:
        raise ValueError("selected E4 preparation substitutes complete frozen independent units")
    tasks=len(plan.declaration.planned_task_budgets)
    tails=1 if plan.declaration.bank_phase=="CALIBRATION" else 3
    from .selected_e4_structure import structural_stage_census
    future_operations,future_outputs=structural_stage_census(plan.declaration.programme)
    census=ExperimentCensus(tuple(sorted((("groups",len(allocation.units)),("cases",len(plan.declaration.programme.cases)),("waves",len(plan.declaration.programme.waves))))),
        tuple(sorted((("groups",len(allocation.units)),("cases",len(plan.declaration.programme.cases)),("waves",len(plan.declaration.programme.waves))))),
        tuple(sorted((("native-and-collector",tasks),("scientific-tail",tails),*future_operations))),
        tuple(sorted((("complete-phase-products",3),*future_outputs))),3*len(plan.declaration.programme.cases))
    dependencies=() if not (plan.declaration.bank_phase=="CALIBRATION" and plan.declaration.models is None) else (
        ExperimentDependency("matrix.selected-e4.revision-eligibility",DependencyKind.SCIENTIFIC_EVIDENCE,
            "Frozen DEV revision is "+plan.declaration.decision.trigger_disposition+"; CAL remains assigned and UNENTERED."),)
    return ExperimentPreparation(specification.identity,census,dependencies,allocation=allocation,execution=execution,
        specification_record=specification,programme=plan,assessment_limitations=(ExperimentDependency(
            "matrix.selected-e4.sampling-warrant",DependencyKind.SCIENTIFIC_EVIDENCE,
            "Conditional whole-group results retain SAMPLING_ASSUMPTION_NOT_AUTHENTICATED until actual scoped evidence is admitted."),))


@dataclass(frozen=True,slots=True)
class SelectedE4PreparedComponentInputs:
    selection:SelectedE4NativeComponentInputs
    resolved:ResolvedSelectedE4ComponentInputs
    files:tuple[tuple[str,PreparedExperimentFile],...]

    def __post_init__(self):
        if type(self.selection) is not SelectedE4NativeComponentInputs or type(self.files) is not tuple:
            raise TypeError("selected E4 component needs exact immutable selection and source handles")
        self.selection.__post_init__()
        if (type(self.resolved) is not ResolvedSelectedE4ComponentInputs
                or resolve_component_inputs(self.selection,self.resolved.plan)!=self.resolved):
            raise ValueError("selected E4 resolved inputs change the exact published-plan reference")
        if (tuple(k for k,_ in self.files)!=tuple(sorted({k for k,_ in self.files}))
                or any(type(v) is not PreparedExperimentFile for _,v in self.files)):
            raise ValueError("selected E4 source handles duplicate a selected artifact")
        for _,v in self.files:v.__post_init__()


def bind_component_inputs(specification,records,*,files=None,**kwargs):
    if not isinstance(records,Mapping) or set(records)!={"inputs","plan"}:
        raise ValueError("selected E4 component requires its reference and separately bound shared plan")
    inputs=records["inputs"];resolved=resolve_component_inputs(inputs,records["plan"]);plan=resolved.plan
    if inputs.component_id!=specification.component_id:
        raise ValueError("selected E4 component changes its exact selected component")
    if component_specification(plan,specification.component_id)!=specification:
        raise ValueError("selected E4 component substitutes original frozen declaration")
    groups=plan.declaration.programme.group_ids if specification.wave_id is None else plan.declaration.wave(specification.wave_id).group_ids
    handles={} if files is None else files
    if not isinstance(handles,Mapping):raise TypeError("selected E4 source files require an explicit role mapping")
    return PreparedExperimentInputs({plan.declaration.bank_phase.lower():programme_allocation(plan,group_ids=groups)},
        SelectedE4PreparedComponentInputs(inputs,resolved,tuple(sorted(handles.items()))))


def component_source_operands(specification,inputs):
    """Derive exact declared operands before source admission; grant no entry.

    This pure projection freezes native and scientific-tail owner contracts.
    component_design still requires and validates every source qualification
    before a prospective candidate can be prepared or issued.
    """
    if type(inputs) is not ResolvedSelectedE4ComponentInputs:
        raise TypeError("selected E4 lowering requires its explicit resolved programme view")
    inputs.__post_init__()
    if inputs.component_id!=specification.component_id:
        raise ValueError("selected E4 lowering changes its exact component binding")
    plan=inputs.plan;d=plan.declaration
    if component_specification(plan,specification.component_id)!=specification:raise ValueError("selected E4 component changes exact full declaration")
    if specification.wave_id is not None:
        if inputs.collection is not None:raise ValueError("native wave cannot consume later collection outcomes")
        lowered=native.lower_selected_e4_protected_wave(d,plan.bank,evidence=plan.evidence,
            declaration_publication=inputs.declaration_publication,wave_id=specification.wave_id,
            campaign=d.root.campaign,draft_id="draft."+specification.specification_id,
            secondary_target=plan.structure.secondary_target,secondary_readout=plan.secondary_readout)
        draft,records,arrays=lowered.draft,lowered.input_records,lowered.input_artifacts
    else:
        collection=inputs.collection
        if collection is None:raise ValueError("selected phase assessment requires actual all-wave closure and source admissions")
        entry=native.SelectedE4ProtectedEntryConfig("config."+native.global_node(d.programme,"phase-entry"),d.programme,d.bank,
            plan.evidence.identity,len(plan.evidence.canonical_bytes()),len(plan.bank.forecast_design.canonical_bytes()),
            d.decision,d.models,d.calibration,d,inputs.declaration_publication,None,
            secondary_readout=plan.secondary_readout,phase="phase-entry",wave_evidence=collection.evidence.identity,wave_evidence_size_bytes=len(collection.evidence.canonical_bytes()))
        configs,external,links,records,arrays=native.phase_collect_contracts(entry,collection.evidence,bank_record=plan.bank,evidence_record=plan.evidence,secondary_target=plan.structure.secondary_target)
        from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft,RecursiveOperationSpec
        declarations={v.capability_key:v for v in native.operation_declarations()}
        budgets=dict(d.planned_task_budgets)
        operations=tuple(RecursiveOperationSpec.from_config(node_id=n,selection=declarations[native.NAMESPACE+"."+c.phase].registration().selection,
            config_id=c.config_id,config=c,obligation_ids=("obligation."+n,),resource_budget=budgets[n]) for n,c in configs)
        root=r.phase_root(d)
        draft=RecursiveStudyDraft("draft."+specification.specification_id,root.question,root.campaign,(),(),(),operations,external,links,
            tuple(n for n,_ in configs),prospective_draft=root)
        operands=({"bank":plan.bank,"specification":plan.tail.calibration,"revision":plan.tail.revision} if d.bank_phase=="CALIBRATION"
            else {"bank":plan.bank,"specification":plan.tail.confirmation.factorial,"scope":plan.tail.confirmation})
        node=native.global_node(d.programme,"phase-collect")
        draft,tail_records=methods.lower_selected_e4_methods(draft,programme=d.programme,operands=operands,
            connections={"reduction":(node,"product"),"data":(node,"observed"),"forecasts":(node,"forecasts")},
            resources=plan.tail.resources,entry_node_id=native.task_id(entry))
        records=tuple(sorted((*records,*tail_records)))
    draft=_bind_component_obligations(draft,plan.declaration,specification.wave_id)
    return draft,records,arrays


def _bind_component_obligations(draft,declaration,wave_id):
    """Assign actual finite acquisition/assessment/reveal verdict owners.

    Coverage names the responsible retained output. It never changes an
    obligation's status or promotes an adverse/unevaluable scientific result.
    Original E3 records and the declared component graph remain unchanged.
    """
    from empirical_lawhood.runtime.candidate_compiler import _required_obligation_ids
    experiment=draft.prospective_draft.experiment
    programme=declaration.programme
    if wave_id is not None:
        wave=declaration.wave(wave_id)
        assessment=native.global_node(programme,"reduce",wave_id)
        terminal=native.global_node(programme,"adjudicate",wave_id)
        cutoffs={case.information_cutoff.cutoff_id:native.local_node(case.root_id,"project")
            for case in programme.cases if case.root_id in wave.root_ids}
    else:
        operation="revision-calibrate" if declaration.bank_phase=="CALIBRATION" else "confirmation-assess"
        assessment=methods.method_node(programme.identity,operation)
        terminal=methods.method_node(programme.identity,
            "revision-adjudicate" if declaration.bank_phase=="CALIBRATION" else "downstream-adjudicate")
        cutoffs={value.cutoff_id:native.global_node(programme,"phase-entry")
            for value in experiment.information_cutoffs}
    required=set(_required_obligation_ids(experiment))
    if set(cutoffs)!={value.cutoff_id for value in experiment.information_cutoffs}:
        raise ValueError("selected E4 obligation owners change the complete actual component cutoff census")
    owners={value:assessment for value in required}
    owners.update(cutoffs)
    for value in (experiment.reveal_barrier.barrier_id,*(experiment.experiment_id+"."+suffix
            for suffix in ("admission","authority","required-outputs","seal-reveal-separation"))):
        owners[value]=terminal
    nodes={value.node_id for value in draft.operations}
    if set(owners.values())-nodes:
        raise ValueError("selected E4 canonical obligation lacks its actual scientific/terminal producer")
    operations=tuple(replace(value,obligation_ids=tuple(sorted(set(value.obligation_ids)|
        {key for key,node in owners.items() if node==value.node_id}))) for value in draft.operations)
    if any(sum(key in value.obligation_ids for value in operations)!=1 for key in required):
        raise ValueError("selected E4 canonical obligation requires exactly one actual verdict owner")
    return replace(draft,operations=operations)


def validate_component_formal_selection(root,entry,catalog,bank_phase):
    """Require the authored E4 families to select their actual scientific method.

    This validates the caller's semantics; it never relabels an E3 algorithm as
    an E4 algorithm. Graph addresses are the only generated formal selections.
    Native acquisition has its separate finite-contract obligation owners.
    """
    operation="revision-calibrate" if bank_phase=="CALIBRATION" else "confirmation-assess"
    evaluator=next(value for value in methods.operation_declarations()
        if value.capability_key==methods.NAMESPACE+"."+operation)
    manifest=evaluator.manifest()
    from empirical_lawhood.runtime.candidate_compiler import _required_obligation_ids
    scientific=set(_required_obligation_ids(root.experiment))
    terminal={root.experiment.reveal_barrier.barrier_id,*(root.experiment.experiment_id+"."+suffix
        for suffix in ("admission","authority","required-outputs","seal-reveal-separation"))}
    scientific.difference_update(terminal)
    scientific.difference_update(value.cutoff_id for value in root.experiment.information_cutoffs)
    facts={value.gap_id:value for value in entry.coverage.applicability}
    for assignment in entry.coverage.assignments:
        if assignment.disposition is not FormalGapCoverageDisposition.TEST_IN_THIS_ACT:
            continue
        if not set(assignment.obligation_ids)<=scientific:
            raise ValueError("E4 V2 formal obligations must name actual whole-phase scientific contracts")
        if not set(assignment.selected_control_ids)<={value.control_id for value in root.experiment.controls}:
            raise ValueError("E4 V2 formal controls must name actual whole-phase scientific controls")
        for role,family in ((FormalMethodRole.ESTIMATOR,assignment.selected_estimator_family_id),
                (FormalMethodRole.MULTIPLICITY,assignment.selected_multiplicity_family_id)):
            binding=catalog.resolve(role,family)
            if (binding is None or assignment.gap_id not in binding.supported_gap_ids
                    or (binding.capability_key,binding.capability_version,binding.implementation_sha256)!=(
                        manifest.capability_key,manifest.capability_version,manifest.implementation_sha256)
                    or binding.input_schema_id!=evaluator.config_record_type.SCHEMA
                    or binding.output_schema_id!=methods.output_types(operation)["product"].SCHEMA
                    or EvidenceCeiling.lowest(binding.maximum_claim_ceiling,manifest.maximum_evidence_ceiling)
                        is not binding.maximum_claim_ceiling
                    or EvidenceCeiling.lowest(facts[assignment.gap_id].requested_claim_ceiling,binding.maximum_claim_ceiling)
                        is not facts[assignment.gap_id].requested_claim_ceiling):
                raise ValueError("E4 V2 formal family requires its exact declared current CAL/CONF scientific method")


def _component_formal_entry(*,draft,selection,inventory,wave_id,bank_phase):
    root=draft.prospective_draft
    selected={(value.selection.capability_key,value.selection.capability_version,
        value.selection.implementation_sha256) for value in draft.operations}
    actual_controls={value.control_id for value in root.experiment.controls}
    def present(role,family):
        binding=selection.formal_methods.resolve(role,family)
        return binding is not None and (binding.capability_key,binding.capability_version,
            binding.implementation_sha256) in selected
    inventory=replace(inventory,
        available_control_ids=tuple(value for value in inventory.available_control_ids if value in actual_controls),
        available_estimator_family_ids=tuple(value for value in inventory.available_estimator_family_ids
            if present(FormalMethodRole.ESTIMATOR,value)),
        multiplicity_family_ids=tuple(value for value in inventory.multiplicity_family_ids
            if present(FormalMethodRole.MULTIPLICITY,value)))
    if wave_id is None:
        validate_component_formal_selection(root,selection.entry,selection.formal_methods,bank_phase)
    assignments=[]
    for assignment in selection.entry.coverage.assignments:
        if assignment.disposition is not FormalGapCoverageDisposition.TEST_IN_THIS_ACT:
            assignments.append(assignment)
            continue
        if wave_id is not None:
            # The parent primary question is assessed only after all waves.
            # Do not replace its minimum, family, or complete parent roster
            # with a wave-sized population assertion.
            assignments.append(replace(assignment,
                disposition=FormalGapCoverageDisposition.DEFER_WITH_TYPED_PREREQUISITE,
                readiness_reason=ReadinessStatus.PREREQUISITE_NOT_MET,
                reason_codes=("E4_WHOLE_PHASE_ASSESSMENT_REQUIRES_ALL_WAVES",),
                selected_estimator_family_id=None,selected_control_ids=(),
                selected_multiplicity_family_id=None,obligation_ids=(),output_ids=(),adjudication_owner_ids=()))
            continue
        operation="revision-calibrate" if bank_phase=="CALIBRATION" else "confirmation-assess"
        owners=tuple(value for value in draft.operations
            if value.selection.capability_key==methods.NAMESPACE+"."+operation)
        if len(owners)!=1 or not set(assignment.obligation_ids)<=set(owners[0].obligation_ids):
            raise ValueError("E4 formal assignment lacks its exact owned scientific obligation producer")
        assignments.append(replace(assignment,output_ids=("product",),adjudication_owner_ids=(owners[0].node_id,)))
    coverage=replace(selection.entry.coverage,candidate_act_id=root.draft_id,denominator_id=root.system.system_id,
        applicability=derive_formal_gap_applicability(selection.entry.register,inventory),assignments=tuple(assignments))
    entry=replace(selection.entry,coverage=coverage,checklist=replace(selection.entry.checklist,
        draft=r.pin(root,"draft_id"),formal_gap_coverage=r.pin(coverage,"coverage_id")))
    validate_experiment_entry(root,entry,for_issue=False)
    return entry,inventory


def select_component_qualifications(draft, available, versions, observation_operator):
    """Select one exact access receipt for each local source/semantic scope.

    The full plan retains independently produced access records for all waves.
    A wave cannot borrow another wave's validity/uncertainty contracts.
    """
    root = draft.prospective_draft
    if root is None or root.system is None or root.experiment is None:
        raise ValueError("selected E4 source access requires its actual local scientific root")
    semantic_scope = (root.system.world.world_id, observation_operator,
        tuple(v.view_id for v in root.system.numerical_views),
        tuple(sorted({v.native_unit for v in root.system.quantities})),
        tuple(sorted({v.coordinate_frame for v in root.system.quantities})),
        tuple(v.clock_id for v in root.system.clocks), root.system.relation.relation_id,
        root.experiment.obligations.validity.validity_id, root.experiment.obligations.uncertainty.uncertainty_id)
    by_source = {}
    for value in available:
        if type(value) is not MaterializationQualificationReceipt:
            raise TypeError("selected E4 source access requires exact immutable qualification receipts")
        by_source.setdefault(value.source_id, []).append(value)
    selected = []
    for external in draft.external_inputs:
        materialization = ObjectIdentity(external.logical_artifact_id, external.payload_schema,
            versions[external.logical_artifact_id], external.expected_content_sha256)
        matches = tuple(value for value in by_source.get(external.input_id, ()) if (
            value.source_id == external.input_id and value.materialization == materialization
            and value.content_sha256 == external.expected_content_sha256
            and (value.evidence_world_id, value.observation_operator, value.numerical_view_ids,
                value.native_unit_ids, value.frame_ids, value.clock_ids, value.receiver_semantics_id,
                value.validity_contract_id, value.uncertainty_contract_id) == semantic_scope
            and value.outcome_access is external.outcome_access
            and value.visibility_ceiling is external.visibility_ceiling))
        if len(matches) != 1:
            raise ValueError("selected E4 needs exactly one current local-scope source qualification for " + external.input_id)
        selected.append(matches[0])
    return tuple(sorted(selected, key=lambda value: value.receipt_id))


def _component_source_configs(available,additional,wanted):
    """Keep exact repeated admissions once in the public SHA-keyed roster."""
    configs={}
    for value in (*available,*additional):
        if value.source_id not in wanted:
            continue
        if configs.setdefault(value.source_id,value)!=value:
            raise ValueError("selected E4 component has conflicting source configs for "+value.source_id)
    return tuple(sorted(configs.values(),key=lambda value:value.fingerprint()))


def component_prospective_spec_id(specification):
    if type(specification) is not SelectedE4NativeComponentSpecification:
        raise TypeError("selected E4 prospective design requires its exact component specification")
    specification.__post_init__()
    return "prospective." + specification.specification_id


def component_design(specification,inputs):
    draft,records,arrays=component_source_operands(specification,inputs)
    plan=inputs.plan
    selection=plan.preparation
    additional=() if inputs.collection is None else inputs.collection.qualifications
    extra_configs=() if inputs.collection is None else inputs.collection.source_configs
    source_configs=_component_source_configs(selection.source_configs,extra_configs,
        {v.input_id for v in draft.external_inputs})
    from types import SimpleNamespace
    codecs={schema:kind for declaration in (*native.operation_declarations(),*methods.operation_declarations())
        for schema,kind in declaration.record_codecs.items()}
    versions={}
    for row in draft.external_inputs:
        kind=codecs.get(row.payload_schema)
        if kind is not None:versions[row.logical_artifact_id]=kind.VERSION
        else:
            matches=tuple(v for v in MATRIX_STORAGE_CODECS if (v.payload_schema,v.media_type)==(row.payload_schema,row.media_type))
            if len(matches)!=1:raise ValueError("selected E4 external source lacks one exact declared record or storage version")
            versions[row.logical_artifact_id]=matches[0].record_version
    qualifications=select_component_qualifications(draft,(*selection.qualifications,*additional),versions,
        plan.evidence.source.pipeline.pipeline_config.profile.observation_operator)
    draft=_source_projection(draft,SimpleNamespace(qualifications=qualifications,source_configs=source_configs),versions)
    root=draft.prospective_draft
    inventories=tuple(value for value in selection.formal_source_inventories
        if value.denominator_id==root.system.system_id)
    if len(inventories)!=1:
        raise ValueError("selected E4 component requires one actual parent formal source denominator")
    parent_inventory=inventories[0]
    local_units=set((*root.development_unit_ids,*root.evaluation_unit_ids))
    local_views={value.view_id for value in root.system.numerical_views}
    inventory=replace(parent_inventory,
        source_materializations=tuple(sorted((value.materialization for value in root.source_materializations),key=lambda value:value.object_id)),
        independent_unit_ids=tuple(value for value in parent_inventory.independent_unit_ids if value in local_units),
        numerical_view_ids=tuple(value for value in parent_inventory.numerical_view_ids if value in local_views))
    entry,inventory=_component_formal_entry(draft=draft,selection=selection,inventory=inventory,
        wave_id=specification.wave_id,bank_phase=plan.declaration.bank_phase)
    operands=tuple(sorted((RecursiveProspectiveOperand(v.logical_artifact_id,v.expected_content_sha256,v.maximum_size_bytes,
        v.payload_schema,v.media_type,v.outcome_access,v.visibility_ceiling) for v in draft.external_inputs),key=lambda v:v.logical_artifact_id))
    design=RecursiveProspectiveDesignInputs(component_prospective_spec_id(specification),draft,entry,selection.formal_methods,
        (inventory,),qualifications,root.design_inputs,operands,())
    return draft,records,arrays,design,source_configs


def prepare_component(specification,*,scientific_inputs,execution,protocol_bytes=None,method_inputs=None):
    if type(specification) is not SelectedE4NativeComponentSpecification or type(execution) is not ExecutionSelection:
        raise TypeError("selected E4 component preparation requires exact declaration and explicit execution")
    if type(method_inputs) is not SelectedE4PreparedComponentInputs:
        raise ValueError("selected E4 component requires its resolved published plan and actual source files")
    method_inputs.__post_init__()
    inputs=method_inputs.resolved;inputs.__post_init__()
    d=inputs.plan.declaration
    if execution.workers!=d.maximum_parallel_tasks:raise ValueError("selected E4 component changes declared worker count")
    draft,records,arrays,design,configs=component_design(specification,inputs)
    wanted={v.artifact_id:v for _,v in arrays}
    if inputs.collection is not None:wanted.update((v.artifact_id,v) for v in inputs.collection.observations)
    files={v.identity.artifact_id:v for _,v in method_inputs.files}
    if len(files)!=len(method_inputs.files) or set(files)!=set(wanted) or any(files[k].identity!=v for k,v in wanted.items()):
        raise ValueError("selected E4 component loses or substitutes actual complete raw/source file bindings")
    resources=dict(inputs.plan.component_resources)[specification.component_id]
    expected={v.node_id:v.resource_budget for v in draft.operations}
    validate_component_resources(resources,expected)
    groups=d.programme.group_ids if specification.wave_id is None else d.wave(specification.wave_id).group_ids
    allocation=programme_allocation(inputs.plan,group_ids=groups)
    if scientific_inputs!={d.bank_phase.lower():allocation}:
        raise ValueError("selected E4 component changes exact whole independent units")
    from collections import Counter
    counts=tuple(sorted(Counter(v.selection.capability_key for v in draft.operations).items()))
    census=ExperimentCensus((("groups",len(groups)),),(("groups",len(groups)),),counts,
        (("native-components",len(draft.operations)),),sum(v.selection.capability_key in {native.key_for_phase(p,referenced=kind,compact_protocol=compact)
            for p in native.NATIVE for kind,compact in ((False,False),(True,False),(True,True))}
            for v in draft.operations))
    # Prepared file selections use immutable artifact IDs. The prospective
    # transport binds them to their exact declared external-input roles.
    file_roles=tuple(sorted((value.input_id,files[value.logical_artifact_id]) for value in draft.external_inputs
        if value.logical_artifact_id in files))
    if ({key for key,_ in records}|{key for key,_ in file_roles})!={value.input_id for value in draft.external_inputs}:
        raise ValueError("selected E4 component loses an exact external-input file role")
    return ExperimentPreparation(specification.identity,census,(),allocation=allocation,draft=draft,input_records=records,
        execution=execution,specification_record=specification,
        design_records=((method_inputs.selection.record_id,method_inputs.selection),),input_files=file_roles,
        assessment_limitations=(ExperimentDependency("matrix.selected-e4.sampling-warrant",DependencyKind.SCIENTIFIC_EVIDENCE,
            "Source/receipt custody does not authenticate IID or exchangeability premises."),))


def validate_component_instance(*,specification,allocation,draft,source_records,resolved_inputs=None):
    rows=tuple(v for _,v in source_records if type(v) is SelectedE4NativeComponentInputs)
    if len(rows)!=1 or len(source_records)!=1:
        raise ValueError("selected E4 instance requires one exact published-plan component reference")
    if source_records[0][0]!=rows[0].record_id:
        raise ValueError("selected E4 component reference changes its original source key")
    if (type(resolved_inputs) is not ResolvedSelectedE4ComponentInputs
            or resolve_component_inputs(rows[0],resolved_inputs.plan)!=resolved_inputs):
        raise ValueError("selected E4 full scientific validation requires its resolved published plan")
    inputs=resolved_inputs
    if inputs.component_id!=specification.component_id:
        raise ValueError("selected E4 retained component changes its exact component binding")
    expected,_,_,_,_=component_design(specification,inputs)
    groups=inputs.plan.declaration.programme.group_ids if specification.wave_id is None else inputs.plan.declaration.wave(specification.wave_id).group_ids
    if draft!=expected or allocation!=programme_allocation(inputs.plan,group_ids=groups):
        raise ValueError("selected E4 retained component changes original scientific graph or full group allocation")


def protocol_declarations():
    return (
        ExperimentProtocolDeclaration(PROGRAMME_PROTOCOL_ID,SelectedE4ProtectedProgrammeSpecification,prepare_programme,
            "matrix-selected-e4-programme",maximum_config_bytes=64*1024**2,input_record_types=(SelectedE4ProtectedProgrammePlan,),
            bind_inputs=bind_programme_inputs,programme_record_type=SelectedE4ProtectedProgrammePlan),
        ExperimentProtocolDeclaration(COMPONENT_PROTOCOL_ID,SelectedE4NativeComponentSpecification,prepare_component,
            "matrix-selected-e4-component",maximum_config_bytes=64*1024**2,
            input_record_types=(SelectedE4NativeComponentInputs,SelectedE4ProtectedProgrammePlan),
            bind_inputs=bind_component_inputs,validate_instance=validate_component_instance,
            input_storage_codecs=MATRIX_STORAGE_CODECS,input_file_record_types=(r.SelectedE4WaveObservation,),requires_prospective_runtime_binding=True))
