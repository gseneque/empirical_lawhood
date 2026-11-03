# SPDX-License-Identifier: MPL-2.0
"""Additive full-history E4 measurements; no prefix or qualification relabelling."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import (
    FactorEventSpec, FactorLifetime, FactorObservation, FactorTrace,
)
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import (
    METHODS, STATES, VIEWS, MatrixParameterFactorControl, MatrixParameterFactorNumericalDesign,
    MatrixParameterScalarSample, expected_members,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access, validate_produced_input_parents
from .selected_e4_programme import SelectedE4PhaseProgramme
from .continuation import ScheduledFullArrays
from .records import ScheduledSource
from .selected_e3_e4_records import SelectedE3E4CaseResult, SelectedE3E4FullHistory, SelectedE3E4NumericalAssessment, SelectedE3E4DevelopmentProgramme, SelectedE3E4CausalPrefix
from .selected_e4_native_records import (
    SelectedE4DevelopmentProduct, SelectedE4NativeCaseResult, SelectedE4ProtectedFullHistory,
    SelectedE4ProtectedNumericalAssessment, SelectedE4WaveLocator, SelectedE4ProtectedCausalPrefix,
)


def identity(record):
    return ObjectIdentity.from_record(record.record_id, record)


def _exact(value, kind):
    if type(value) is not kind:
        raise TypeError('full factor measurement requires its exact typed operand')
    value.__post_init__()


def _pin(value, kinds):
    _exact(value,ObjectIdentity)
    if (value.object_schema,value.object_version) not in tuple((kind.SCHEMA,kind.VERSION) for kind in kinds):
        raise ValueError('full factor measurement changes its actual record edition')


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorProtectedProduct(CanonicalRecord):
    """An original wave output locator; authentication/reveal remain reader owned."""
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-protected-product'
    record:ObjectIdentity
    wave:SelectedE4WaveLocator
    task_id:str
    receipt:ObjectIdentity
    publication:ArtifactWriteResult

    def __post_init__(self):
        _exact(self.record,ObjectIdentity);_exact(self.wave,SelectedE4WaveLocator)
        _pin(self.receipt,(CanonicalTaskReceipt,));_exact(self.publication,ArtifactWriteResult)
        validate_stable_id(self.task_id)
        if (self.record.object_schema,self.record.object_fingerprint)!=(self.publication.logical.payload_schema,self.publication.logical.content_sha256):
            raise ValueError('full factor protected locator substitutes original canonical output bytes')


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorSource(CanonicalRecord):
    """Receipt locators authenticate upstream; this value supplies no access grant."""
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-source'
    VERSION: ClassVar[str]='2.0.0'
    record_id:str
    programme:ObjectIdentity
    original_case:ObjectIdentity
    source:ObjectIdentity
    root_id:str
    group_id:str
    coordinate:MatrixParameterCoordinate
    rule:FactorEventSpec
    numerical_design:MatrixParameterFactorNumericalDesign
    source_state:str
    causal_disposition:str
    causal_prefix:ObjectIdentity|None
    history:ObjectIdentity|None
    full_arrays:ScheduledFullArrays|None
    full_numerical:ObjectIdentity|None
    history_numerical_pass:bool|None
    original_products:tuple[SelectedE4DevelopmentProduct|ScheduledFullFactorProtectedProduct,...]
    produced_input_parents:tuple[ArtifactLineageParent,...]

    def __post_init__(self):
        validate_produced_input_parents(self.produced_input_parents)
        for name in ('record_id','root_id','group_id'):validate_stable_id(getattr(self,name))
        for value,kind in ((self.programme,ObjectIdentity),(self.coordinate,MatrixParameterCoordinate),
                (self.rule,FactorEventSpec),(self.numerical_design,MatrixParameterFactorNumericalDesign)):
            _exact(value,kind)
        _pin(self.source,(ScheduledSource,))
        _pin(self.original_case,(SelectedE3E4CaseResult,SelectedE4NativeCaseResult))
        if (self.source_state not in STATES
                or self.causal_disposition not in ('AVAILABLE','NO_ORIGIN','UNEVALUABLE','INSTRUMENT_UNRESOLVED','UNOBSERVED')
                or self.rule.primary_dt!=self.coordinate.primary_view.timestep
                or self.rule.lattice!=self.coordinate.observation_ticks
                or self.rule.scalar_closure is None):
            raise ValueError('full factor source changes its original complete lattice, clock, rule or disposition')
        if (self.causal_prefix is None)!=(self.causal_disposition=='UNOBSERVED'):
            raise ValueError('full factor source invents or discards actual causal-prefix disposition')
        if self.causal_prefix is not None:_pin(self.causal_prefix,(SelectedE3E4CausalPrefix,SelectedE4ProtectedCausalPrefix))
        complete=self.source_state=='COMPLETED'
        if (complete!=(self.history is not None) or complete!=(self.full_arrays is not None)
                or (self.full_numerical is not None)!=(type(self.history_numerical_pass) is bool)
                or complete and self.causal_prefix is None
                or not complete and (self.full_numerical is not None or self.history_numerical_pass is not None)):
            raise ValueError('full factor source invents or discards actual full-history/numerical availability')
        protected=self.original_case.object_schema==SelectedE4NativeCaseResult.SCHEMA
        product_kind=ScheduledFullFactorProtectedProduct if protected else SelectedE4DevelopmentProduct
        if type(self.original_products) is not tuple or any(type(row) is not product_kind for row in self.original_products):
            raise TypeError('full factor source needs its actual original development/protected receipt locators')
        pins=tuple(row.record for row in self.original_products)
        allowed={value for value in (self.original_case,self.causal_prefix,self.history,self.full_numerical) if value is not None}
        if (len(pins)!=len(set(pins)) or set(pins)-allowed or self.original_case.object_id!=self.root_id):
            raise ValueError('full factor source duplicates outputs or substitutes its observed original case')
        for row in self.original_products:row.__post_init__()
        producers={(row.wave.run_id,row.wave.execution_plan) if protected else (row.run_id,row.execution_plan)
            for row in self.original_products}
        if len(producers)>1:
            raise ValueError('full factor source combines original history/numerical outputs from different waves')
        if protected and len({row.wave for row in self.original_products})>1:
            raise ValueError('full factor source substitutes original issue/reveal/authority between outputs')
        expected_case_schema=SelectedE4PhaseProgramme if protected else SelectedE3E4DevelopmentProgramme
        _pin(self.programme,(expected_case_schema,))
        if self.causal_prefix is not None:
            _pin(self.causal_prefix,(SelectedE4ProtectedCausalPrefix,) if protected else (SelectedE3E4CausalPrefix,))
            if self.causal_prefix not in pins:raise ValueError('full factor source omits actual causal-prefix producer')
        if complete:
            _pin(self.history,(SelectedE4ProtectedFullHistory,) if protected else (SelectedE3E4FullHistory,))
            if self.full_numerical is not None:
                _pin(self.full_numerical,(SelectedE4ProtectedNumericalAssessment,) if protected else (SelectedE3E4NumericalAssessment,))
            _exact(self.full_arrays,ScheduledFullArrays)
            if (self.history not in pins or self.full_numerical is not None and self.full_numerical not in pins
                    or self.full_arrays.source!=self.source):
                raise ValueError('full factor source substitutes its actual full-history/assessment producers')
            # Retain the original scientific operand verbatim. Its publication's
            # inherited custody is authenticated independently by the API.
            expected=(OutcomeAccess.EVALUATION_SEALED,VisibilityCeiling.PROSPECTIVE) if protected else (OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY)
            if (self.full_arrays.outcome_access,self.full_arrays.visibility_ceiling)!=expected:
                raise ValueError('full factor source relabels original protected/development arrays')

    @property
    def identity(self):return identity(self)

    @property
    def producers(self):
        return tuple(sorted((self.identity,*(value for value in (self.history,self.full_numerical) if value is not None)),key=lambda row:row.object_id))

    @property
    def outcome_access(self):
        return self.access_pair[0]

    @property
    def visibility_ceiling(self):
        return self.access_pair[1]

    @property
    def access_pair(self):
        protected=self.original_case.object_schema==SelectedE4NativeCaseResult.SCHEMA
        return produced_access(declared_access=OutcomeAccess.EVALUATION_REVEALED if protected else OutcomeAccess.DEVELOPMENT_VISIBLE,
            declared_visibility=VisibilityCeiling.OUTCOME_VISIBLE if protected else VisibilityCeiling.DEVELOPMENT_ONLY,
            parents=self.produced_input_parents)


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorRoot(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-root'
    source:ObjectIdentity
    root_id:str
    group_id:str
    coordinate:ObjectIdentity
    history:ObjectIdentity
    native_arrays:ArtifactIdentity

    def __post_init__(self):
        _pin(self.source,(ScheduledFullFactorSource,))
        _pin(self.coordinate,(MatrixParameterCoordinate,))
        _pin(self.history,(SelectedE3E4FullHistory,SelectedE4ProtectedFullHistory))
        _exact(self.native_arrays,ArtifactIdentity)
        for value in (self.root_id,self.group_id):validate_stable_id(value)


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorTrace(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-trace'
    root:ScheduledFullFactorRoot
    rule:ObjectIdentity
    view:str
    sector:str
    observations:tuple[FactorObservation,...]
    moving_lifetime:FactorLifetime
    origin_fixed_lifetime:FactorLifetime
    diagnostics:ArtifactIdentity|None
    diagnostic_members:tuple[MatrixArrayMember,...]=()

    def __post_init__(self):
        _exact(self.root,ScheduledFullFactorRoot)
        FactorTrace.__post_init__(self)
        for value in self.observations:_exact(value,FactorObservation)
        for value in (self.moving_lifetime,self.origin_fixed_lifetime):_exact(value,FactorLifetime)


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorArrays(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-arrays'
    record_id:str
    source:ObjectIdentity
    array_artifact:ArtifactIdentity
    members:tuple[MatrixArrayMember,...]
    producers:tuple[ObjectIdentity,...]
    outcome_access:OutcomeAccess
    visibility_ceiling:VisibilityCeiling

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _pin(self.source,(ScheduledFullFactorSource,))
        _exact(self.array_artifact,ArtifactIdentity)
        require_sorted_unique_ids(self.members,attribute='name',field_name='full factor members')
        require_sorted_unique_ids(self.producers,attribute='object_id',field_name='full factor producers')
        if (self.array_artifact.payload_schema!=MATRIX_ARRAY_SCHEMA or self.array_artifact.media_type!='application/x-npz'
                or not self.members or not 0<self.array_artifact.size_bytes<=MAXIMUM_MATRIX_ARRAY_BYTES
                or sum(row.size_bytes for row in self.members)>MAXIMUM_MATRIX_ARRAY_BYTES
                or (self.outcome_access,self.visibility_ceiling) not in (
                    (OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY),
                    (OutcomeAccess.EVALUATION_SEALED,VisibilityCeiling.PROSPECTIVE),
                    (OutcomeAccess.EVALUATION_SEALED,VisibilityCeiling.DEVELOPMENT_ONLY),
                    (OutcomeAccess.EVALUATION_REVEALED,VisibilityCeiling.OUTCOME_VISIBLE))):
            raise ValueError('full factor diagnostics change bounded members or actual analysis access')


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorProduct(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-product'
    record_id:str
    source:ObjectIdentity
    requested_traces:int
    requested_observations:int
    traces:tuple[ScheduledFullFactorTrace,...]
    scalars:tuple[MatrixParameterScalarSample,...]
    arrays:ScheduledFullFactorArrays

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _pin(self.source,(ScheduledFullFactorSource,))
        _exact(self.arrays,ScheduledFullFactorArrays)
        if (type(self.requested_traces) is not int or self.requested_traces<1
                or type(self.requested_observations) is not int or self.requested_observations<2
                or type(self.traces) is not tuple or any(type(row) is not ScheduledFullFactorTrace for row in self.traces)
                or type(self.scalars) is not tuple or any(type(row) is not MatrixParameterScalarSample for row in self.scalars)
                or len(self.scalars)!=self.requested_traces*self.requested_observations or self.arrays.source!=self.source):
            raise ValueError('full factor product thins its requested view/sector/tick census')
        for row in (*self.traces,*self.scalars):row.__post_init__()

    @property
    def identity(self):return identity(self)


def validate_product(source,product):
    _exact(source,ScheduledFullFactorSource);_exact(product,ScheduledFullFactorProduct)
    expected=tuple((view,sector,tick) for view in VIEWS for sector in source.rule.sectors for tick in source.rule.lattice)
    if (product.source!=source.identity or (product.requested_traces,product.requested_observations)!=(2*len(source.rule.sectors),len(source.rule.lattice))
            or tuple((row.view,row.sector,row.tick) for row in product.scalars)!=expected
            or {row.name:(row.dtype,row.shape) for row in product.arrays.members}!=expected_members(source.rule)
            or (product.arrays.outcome_access,product.arrays.visibility_ceiling)!=(source.outcome_access,source.visibility_ceiling)
            or product.arrays.producers!=source.producers):
        raise ValueError('full factor product changes complete original source/physical/analysis scope')
    if source.source_state!='COMPLETED':
        if product.traces:raise ValueError('unavailable full history invents measured factor traces')
        return
    root=ScheduledFullFactorRoot(source.identity,source.root_id,source.group_id,
        ObjectIdentity.from_record(source.coordinate.coordinate_id,source.coordinate),source.history,source.full_arrays.array_artifact)
    if tuple((row.view,row.sector) for row in product.traces)!=tuple((view,sector) for view in VIEWS for sector in source.rule.sectors):
        raise ValueError('full factor product drops an actual view/sector trace')
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import validate_trace
    for row in product.traces:
        if row.root!=root or row.diagnostics!=product.arrays.array_artifact or row.diagnostic_members!=product.arrays.members:
            raise ValueError('full factor trace substitutes original history or diagnostics')
        validate_trace(row,source.rule)


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-assessment'
    record_id:str
    source:ObjectIdentity
    product:ObjectIdentity
    numerical_design:ObjectIdentity
    controls:tuple[MatrixParameterFactorControl,...]
    witness_pass:bool
    history_numerical_pass:bool|None
    history_available:bool
    disposition:str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _pin(self.source,(ScheduledFullFactorSource,));_pin(self.product,(ScheduledFullFactorProduct,))
        _pin(self.numerical_design,(MatrixParameterFactorNumericalDesign,))
        if (type(self.controls) is not tuple or tuple(row.method for row in self.controls)!=METHODS
                or any(type(row) is not MatrixParameterFactorControl for row in self.controls)
                or type(self.witness_pass) is not bool or self.witness_pass!=all(row.disposition in ('SATISFIED','NOT_APPLICABLE') for row in self.controls)
                or self.history_numerical_pass is not None and type(self.history_numerical_pass) is not bool
                or type(self.history_available) is not bool
                or not self.history_available and self.history_numerical_pass is not None):
            raise ValueError('full factor assessment changes independent controls or history status')
        expected=('HISTORY_UNAVAILABLE' if not self.history_available else 'HISTORY_NUMERICAL_UNASSESSED'
            if self.history_numerical_pass is None else 'HISTORY_NUMERICALLY_FAILED'
            if not self.history_numerical_pass else 'MEASUREMENT_CHECKS_SATISFIED' if self.witness_pass else 'WITNESS_NOT_ESTABLISHED')
        if self.disposition!=expected:raise ValueError('full factor assessment manufactures a scientific or numerical admission')
        for row in self.controls:row.__post_init__()

    @property
    def identity(self):return identity(self)


def validate_assessment(source,product,assessment):
    validate_product(source,product);_exact(assessment,ScheduledFullFactorAssessment)
    n=product.requested_traces*product.requested_observations
    if (assessment.source!=source.identity or assessment.product!=product.identity
            or assessment.numerical_design!=ObjectIdentity.from_record(source.numerical_design.design_id,source.numerical_design)
            or assessment.history_available!=(source.history is not None)
            or assessment.history_numerical_pass!=source.history_numerical_pass
            or tuple(len(row.measured_errors) for row in assessment.controls)!=(n,15*n,n,n,n,n)
            or tuple(row.denominator_real_coordinates for row in assessment.controls)!=(225,15,225,225,48,1)):
        raise ValueError('full factor assessment changes original availability or complete independent denominator')


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorCell(CanonicalRecord):
    """One nested view/sector, never an independent sampling unit."""
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-cell'
    root_id:str
    group_id:str
    coordinate:ObjectIdentity
    source:ObjectIdentity
    product:ObjectIdentity
    assessment:ObjectIdentity
    view:str
    sector:str
    source_state:str
    causal_disposition:str
    history_numerical_pass:bool|None
    witness_pass:bool
    requested_observations:int
    available_observations:int
    unidentifiable_observations:int
    unavailable_observations:int
    scalar_comparable_observations:int
    scalar_disagreement_observations:int
    moving_lifetime:FactorLifetime|None
    origin_fixed_lifetime:FactorLifetime|None

    def __post_init__(self):
        for value in (self.root_id,self.group_id):validate_stable_id(value)
        for value,kinds in ((self.coordinate,(MatrixParameterCoordinate,)),(self.source,(ScheduledFullFactorSource,)),
                (self.product,(ScheduledFullFactorProduct,)),(self.assessment,(ScheduledFullFactorAssessment,))):_pin(value,kinds)
        counts=(self.requested_observations,self.available_observations,self.unidentifiable_observations,
            self.unavailable_observations,self.scalar_comparable_observations,self.scalar_disagreement_observations)
        if (self.view not in VIEWS or self.sector not in ('X','Y') or self.source_state not in STATES
                or self.causal_disposition not in ('AVAILABLE','NO_ORIGIN','UNEVALUABLE','INSTRUMENT_UNRESOLVED','UNOBSERVED')
                or self.history_numerical_pass is not None and type(self.history_numerical_pass) is not bool
                or type(self.witness_pass) is not bool
                or any(type(value) is not int or value<0 for value in counts)
                or self.requested_observations<2
                or sum(counts[1:4])!=self.requested_observations
                or not self.scalar_disagreement_observations<=self.scalar_comparable_observations<=self.requested_observations
                or (self.source_state=='COMPLETED')!=(self.moving_lifetime is not None)
                or (self.source_state=='COMPLETED')!=(self.origin_fixed_lifetime is not None)):
            raise ValueError('full factor cell changes nested availability or full lattice denominator')
        for value in (self.moving_lifetime,self.origin_fixed_lifetime):
            if value is not None:_exact(value,FactorLifetime)


@dataclass(frozen=True,slots=True)
class ScheduledFullFactorCensus(CanonicalRecord):
    """Complete original matched groups; a measurement, never a qualification."""
    SCHEMA: ClassVar[str]='empirical-lawhood/matrix-selected-e4/full-factor-census'
    record_id:str
    programme:ObjectIdentity
    group_ids:tuple[str,...]
    root_ids:tuple[str,...]
    cells:tuple[ScheduledFullFactorCell,...]

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import require_sorted_unique_strings
        validate_stable_id(self.record_id)
        _pin(self.programme,(SelectedE3E4DevelopmentProgramme,SelectedE4PhaseProgramme))
        require_sorted_unique_strings(self.group_ids,field_name='full factor original independent groups',allow_empty=False)
        require_sorted_unique_strings(self.root_ids,field_name='full factor original cases',allow_empty=False)
        if (type(self.cells) is not tuple or any(type(row) is not ScheduledFullFactorCell for row in self.cells)
                or tuple((row.root_id,row.view,row.sector) for row in self.cells)!=tuple(sorted({(row.root_id,row.view,row.sector) for row in self.cells}))
                or tuple(sorted({row.root_id for row in self.cells}))!=self.root_ids
                or tuple(sorted({row.group_id for row in self.cells}))!=self.group_ids):
            raise ValueError('full factor census duplicates or drops original matched cases/groups')
        for row in self.cells:row.__post_init__()

    @property
    def identity(self):return identity(self)
