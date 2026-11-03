"""New parameter-source joins without widening historical factor records."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec, FactorTrace
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import (
    EXPOSED, MatrixParameterAllocation, MatrixParameterHistoryAssessment,
    MatrixParameterHistoryProduct, MatrixParameterHistorySource, coordinate_identity,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.contracts import BetaCouplingRule
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_decimal, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import NativeSubworkBegin, NativeSubworkCompletion, NativeSubworkContact, NativeSubworkDefinition, NativeSubworkOutput

VIEWS = ('PRIMARY', 'FINE')
STATES = ('ABSENT', 'NOT_ENTERED', 'BEGUN', 'UNKNOWN_COMPLETION', 'FAILED', 'COMPLETED')
DIAGNOSTICS = ('ticks', 'spectrum', 'projector', 'basis', 'factor', 'aligned_factor', 'available', 'identifiable')
METHODS = ('raw-operator', 'all-eigenpairs', 'eigenvector-orthogonality', 'slow-projector', 'pauli-factor', 'scalar-contrast')


def native_metadata_identity(definition, record, name):
    key = sha256((definition.parent_contact.task_id+':'+definition.subwork_id).encode()).hexdigest()
    return ObjectIdentity.from_record('native-subwork.'+key+'.'+name,record)


def identity(record):
    for name in ('source_id', 'evidence_id', 'design_id', 'definition_id', 'spec_id', 'operand_id', 'product_id', 'assessment_id', 'config_id'):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError('parameter factor record has no declared identity')


def prefix(view, sector):
    return view.lower()+'_'+sector.lower()+'_'


def expected_members(rule):
    n = len(rule.lattice)
    shape = {'ticks': ('<i8', (n,)), 'spectrum': ('<f8', (n,15)), 'projector': ('<f8', (n,15,15)),
        'basis': ('<f8', (n,15,3)), 'factor': ('<c16', (n,3,4,4)), 'aligned_factor': ('<c16', (n,3,4,4)),
        'available': ('|b1', (n,)), 'identifiable': ('|b1', (n,)),
        'operator': ('<f8', (n,15,15)), 'eigenvectors': ('<f8', (n,15,15))}
    return dict(sorted((prefix(v,s)+k,value) for v in VIEWS for s in rule.sectors for k,value in shape.items()))


@dataclass(frozen=True, slots=True)
class MatrixParameterScalarDefinition(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-factor/scalar-definition'
    definition_id: str
    threshold: Decimal = Decimal('0.30')
    convention: str = 'Q2_PUBLISHED_GEOMETRIC_RESIDUAL_2ALPHA_OVER3_RADIUS_HS_ORIGINAL_TINY_FALLBACK'
    scope: str = 'HISTORICAL_GEOMETRIC_CONTRAST_NO_PHYSICAL_OR_SOURCE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.definition_id)
        if (self.threshold != Decimal('0.30')
                or self.convention != 'Q2_PUBLISHED_GEOMETRIC_RESIDUAL_2ALPHA_OVER3_RADIUS_HS_ORIGINAL_TINY_FALLBACK'
                or self.scope != 'HISTORICAL_GEOMETRIC_CONTRAST_NO_PHYSICAL_OR_SOURCE_ADMISSION'):
            raise ValueError('parameter scalar changes its named historical contrast')


@dataclass(frozen=True, slots=True)
class MatrixParameterScalarContrastSpec(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-factor/scalar-contrast'
    spec_id: str
    coordinate: ObjectIdentity
    member: ObjectIdentity
    normalization: ArtifactIdentity
    beta_rule: BetaCouplingRule
    clock_id: str

    def __post_init__(self):
        validate_stable_id(self.spec_id)
        validate_stable_id(self.clock_id)
        if (self.normalization.payload_schema != MatrixParameterScalarDefinition.SCHEMA
                or self.normalization.media_type != 'application/json'
                or self.beta_rule is not BetaCouplingRule.PUBLISHED_DETERMINISTIC):
            raise ValueError('parameter scalar loses its original beta/normalization convention')


@dataclass(frozen=True, slots=True)
class MatrixParameterFactorNumericalDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-factor/numerical-design'
    design_id: str
    operator_tolerance: Decimal
    eigenpair_tolerance: Decimal
    orthogonality_tolerance: Decimal
    projector_tolerance: Decimal
    factor_tolerance: Decimal
    scalar_tolerance: Decimal
    standing: str = 'FINITE_RETAINED_EQUATION_CHECK_NO_CONTINUUM_OR_STATISTICAL_BOUND'

    def __post_init__(self):
        validate_stable_id(self.design_id)
        for name in ('operator_tolerance', 'eigenpair_tolerance', 'orthogonality_tolerance', 'projector_tolerance', 'factor_tolerance', 'scalar_tolerance'):
            validate_decimal(getattr(self,name), field_name=name, minimum=Decimal(0))
        if self.standing != 'FINITE_RETAINED_EQUATION_CHECK_NO_CONTINUUM_OR_STATISTICAL_BOUND':
            raise ValueError('parameter factor design changes its numerical standing')


@dataclass(frozen=True, slots=True)
class MatrixParameterFactorSupply(CanonicalRecord):
    """Exact original metadata; absent bytes do not become available histories.

    The custody caller authenticates these original records and the absence
    census. This report cannot recreate live native authority or prove freshness.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-factor/supply'
    evidence_id: str
    source: ObjectIdentity
    state: str
    product: MatrixParameterHistoryProduct | None = None
    assessment: MatrixParameterHistoryAssessment | None = None
    product_artifact: ArtifactIdentity | None = None
    definition: NativeSubworkDefinition | None = None
    begin: NativeSubworkBegin | None = None
    contact: NativeSubworkContact | None = None
    completion: NativeSubworkCompletion | None = None
    receipt: CanonicalTaskReceipt | None = None

    def __post_init__(self):
        validate_stable_id(self.evidence_id)
        if self.state not in STATES or self.source.object_schema != MatrixParameterHistorySource.SCHEMA:
            raise ValueError('parameter factor supply changes its original source/state')
        if (self.begin is not None and (self.definition is None or self.begin.definition != self.definition.identity)
                or self.contact is not None and (self.begin is None or self.contact.begin != native_metadata_identity(self.definition,self.begin,'begin'))
                or self.completion is not None and (self.definition is None or self.contact is None
                    or self.completion.definition != self.definition.identity
                    or self.completion.contact != native_metadata_identity(self.definition,self.contact,'contact'))):
            raise ValueError('parameter factor supply substitutes original native contact lineage')
        if self.state == 'COMPLETED':
            if (self.product is None or self.assessment is None or self.product_artifact is None or self.begin is None or self.contact is None
                    or self.definition != self.product.native.definition or self.completion != self.product.native.completion
                    or self.receipt != self.product.native.receipt):
                raise ValueError('completed parameter supply needs exact original product/assessment/contact/receipt')
        elif self.product is not None or self.assessment is not None or self.product_artifact is not None:
            raise ValueError('unavailable parameter supply cannot fabricate positive products')
        if self.state == 'ABSENT' and any(x is not None for x in (self.definition,self.begin,self.contact,self.completion,self.receipt)):
            raise ValueError('absent parameter source invents native metadata')
        if self.state == 'NOT_ENTERED' and any(x is not None for x in (self.begin,self.contact,self.completion,self.receipt)):
            raise ValueError('unentered parameter source invents entered native metadata')
        if self.state=='BEGUN' and (self.begin is None or self.contact is not None or self.completion is not None or self.receipt is not None):
            raise ValueError('uncertain parameter history invents a known completion')
        if self.state=='UNKNOWN_COMPLETION' and (self.begin is None or self.contact is None or self.receipt is not None):
            raise ValueError('uncertain parameter history changes original contact/receipt absence')
        if self.state == 'FAILED' and (self.completion is None or self.receipt is None
                or self.completion.operational_status is not OperationalStatus.FAILED
                or self.receipt.operational_status is not OperationalStatus.FAILED):
            raise ValueError('failed parameter source needs its real failed completion/receipt')
        if self.completion is not None and tuple(sorted((*self.completion.consumed_streams,*self.completion.unconsumed_streams,
                *self.completion.unknown_streams),key=lambda x:x.object_id))!=self.definition.streams:
            raise ValueError('parameter supply changes retained completion stream census')
        if self.completion is not None and set((*self.completion.output_ids,*self.completion.omitted_output_ids))!={o.output_id for o in self.definition.outputs}:
            raise ValueError('parameter supply changes retained completion output census')
        if self.receipt is not None:
            d,r,c = self.definition,self.receipt,self.completion
            key = sha256((d.parent_contact.task_id+':'+d.subwork_id).encode()).hexdigest()
            task = 'native-subwork.'+key
            attempt = d.parent_contact.run_id+'.'+task+'.attempt-001'
            returned = tuple(sorted(o.output_id for o in d.outputs if any(
                a.logical_artifact_id==task+'.output.'+o.output_id for a in r.output_logical_artifacts)))
            meta = tuple(a for a in r.output_logical_artifacts if a.logical_artifact_id==task+'.completion')
            if (r is None or (r.receipt_id,r.run_id,r.task_id,r.attempt_id)!=
                    ('receipt.'+attempt,d.parent_contact.run_id,task,attempt)
                    or r.implementation_commit!=d.parent_contact.implementation_commit
                    or not set(d.input_materialization_ids)<=set(r.input_materialization_ids)
                    or r.operational_status!=c.operational_status or r.reason_codes!=c.reason_codes
                    or tuple(sorted((*c.consumed_streams,*c.unconsumed_streams,*c.unknown_streams),key=lambda x:x.object_id))!=d.streams
                    or c.output_ids!=returned or set((*c.output_ids,*c.omitted_output_ids))!={o.output_id for o in d.outputs}
                    or len(meta)!=1 or meta[0].payload_schema!=c.SCHEMA or meta[0].content_sha256!=c.fingerprint()):
                raise ValueError('parameter supply substitutes exact original receipt/completion/output/stream custody')
            material = next(m for m in r.output_materializations if m.logical_artifact_id==meta[0].logical_artifact_id)
            if material.physical_sha256!=c.fingerprint() or material.size_bytes!=len(c.canonical_bytes()):
                raise ValueError('parameter supply substitutes physical completion receipt bytes')

    def validate_source(self, source):
        from empirical_lawhood.adapters.methods.matrix_parameter_history.operation_bindings import MatrixParameterOperationConfig
        if self.source != ObjectIdentity.from_record(source.source_id,source):
            raise ValueError('parameter supply substitutes its selected source')
        if self.definition is not None and (set(self.definition.sources) != {
                self.source,ObjectIdentity.from_record(source.allocation.allocation_id,source.allocation),
                coordinate_identity(source.coordinate),source.provenance.identity}
                or self.definition.streams != tuple(sorted((source.root.stream_identity(s) for s in source.root.streams),key=lambda x:x.object_id))
                or self.definition.code_sources_sha256 != source.provenance.code_sources_sha256
                or self.definition.dependency_lock_sha256 != source.provenance.dependency_lock_sha256):
            raise ValueError('parameter supply changes original native operands/stream/provenance')
        if self.definition is not None:
            expected_config = MatrixParameterOperationConfig('config.matrix-parameter-history-development.'+source.root_id+'.history','history',source)
            if (self.definition.subwork_id!='subwork.'+source.root_id+'.paired-history'
                    or self.definition.operation_id!='matrix-parameter-native.paired-history'
                    or self.definition.parent_contact.task_id!='matrix-parameter-history-development.'+source.root_id+'.history'
                    or self.definition.configuration!=ObjectIdentity.from_record(expected_config.config_id,expected_config)
                    or self.definition.roster_id!='selected.native-subwork'
                    or self.definition.outputs!=(NativeSubworkOutput('arrays',MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz'),)):
                raise ValueError('parameter supply substitutes the named original native configuration/operation/output')
        if self.product is not None:
            from empirical_lawhood.adapters.methods.matrix_parameter_history.science import validate_assessment
            self.product.validate_source(source)
            validate_assessment(source,self.product,self.assessment)
            if (self.product_artifact.payload_schema!=self.product.SCHEMA
                    or self.product_artifact.media_type!='application/json'
                    or self.product_artifact.sha256!=self.product.fingerprint()
                    or self.product_artifact.size_bytes!=len(self.product.canonical_bytes())):
                raise ValueError('parameter supply changes exact retained canonical product bytes')


@dataclass(frozen=True, slots=True)
class MatrixParameterFactorRootScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-factor/root-scope'
    root_id: str
    independent_group_id: str
    coordinate: ObjectIdentity
    clock_id: str
    numerical_view_ids: tuple[str, ...]

    def __post_init__(self):
        for value in (self.root_id,self.independent_group_id,self.clock_id):
            validate_stable_id(value)
        if len(self.numerical_view_ids)!=2 or tuple(sorted(set(self.numerical_view_ids)))!=self.numerical_view_ids:
            raise ValueError('parameter factor scope loses both actual nested view identities')


def allocation_scopes(allocation):
    coordinates = {coordinate_identity(c):c for c in allocation.coordinates}
    return tuple(MatrixParameterFactorRootScope(r.root.root_id,r.root.independent_group_id,r.coordinate,r.root.clock_id,
        tuple(sorted((coordinates[r.coordinate].primary_view.view_id,coordinates[r.coordinate].fine_view.view_id)))) for r in allocation.roots)


@dataclass(frozen=True, slots=True)
class MatrixParameterFactorSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-factor/source'
    source_id: str
    parameter_source: ObjectIdentity
    allocation: ObjectIdentity
    coordinate: ObjectIdentity
    supply: ObjectIdentity
    rule: ObjectIdentity
    scalar: ObjectIdentity
    scalar_definition: ObjectIdentity
    numerical_design: ObjectIdentity
    producing_provenance: ObjectIdentity
    root_id: str
    independent_group_id: str
    clock_id: str
    roster: tuple[MatrixParameterFactorRootScope, ...]
    source_state: str
    history_arrays: ArtifactIdentity | None
    history_product: ArtifactIdentity | None
    history_numerical_pass: bool | None
    exposure: str = EXPOSED

    def __post_init__(self):
        for name in ('source_id','root_id','independent_group_id','clock_id'):
            validate_stable_id(getattr(self,name))
        if (self.exposure != EXPOSED or self.source_state not in STATES
                or (self.source_state=='COMPLETED')!=(self.history_arrays is not None)
                or (self.source_state=='COMPLETED')!=(self.history_product is not None)
                or (self.source_state=='COMPLETED')!=(type(self.history_numerical_pass) is bool)
                or self.source_state!='COMPLETED' and self.history_numerical_pass is not None
                or self.parameter_source.object_schema != MatrixParameterHistorySource.SCHEMA
                or self.allocation.object_schema != MatrixParameterAllocation.SCHEMA
                or self.supply.object_schema != MatrixParameterFactorSupply.SCHEMA
                or self.rule.object_schema != FactorEventSpec.SCHEMA
                or self.scalar.object_schema != MatrixParameterScalarContrastSpec.SCHEMA
                or self.scalar_definition.object_schema != MatrixParameterScalarDefinition.SCHEMA
                or self.numerical_design.object_schema != MatrixParameterFactorNumericalDesign.SCHEMA
                or self.producing_provenance.object_schema != NumericalProducingProvenance.SCHEMA):
            raise ValueError('parameter factor source changes named identities/exposure')
        if (tuple(r.root_id for r in self.roster)!=tuple(sorted({r.root_id for r in self.roster}))
                or self.root_id not in {r.root_id for r in self.roster}):
            raise ValueError('parameter factor source loses complete compact allocation scope')

    def validate_operands(self, parameter, supply, rule, scalar, definition, design, provenance):
        supply.validate_source(parameter)
        if (self.source_state!=supply.state or self.history_arrays!=(None if supply.product is None else supply.product.arrays.array_artifact)
                or self.history_product!=supply.product_artifact
                or self.history_numerical_pass!=(None if supply.assessment is None else supply.assessment.numerical_pass)):
            raise ValueError('parameter factor changes actual original supply availability/array identity')
        actual = (ObjectIdentity.from_record(parameter.source_id,parameter),ObjectIdentity.from_record(parameter.allocation.allocation_id,parameter.allocation),
            coordinate_identity(parameter.coordinate),identity(supply),rule.identity,identity(scalar),identity(definition),identity(design),provenance.identity)
        if actual != (self.parameter_source,self.allocation,self.coordinate,self.supply,self.rule,self.scalar,self.scalar_definition,self.numerical_design,self.producing_provenance):
            raise ValueError('parameter factor changes original typed operands')
        c = parameter.coordinate
        if (self.roster!=allocation_scopes(parameter.allocation)
                or (self.root_id,self.independent_group_id,self.clock_id) != (parameter.root_id,parameter.root.root.independent_group_id,c.clock_id)
                or rule.primary_dt != c.primary_view.timestep or rule.lattice != c.observation_ticks
                or scalar.coordinate != self.coordinate or scalar.member != ObjectIdentity.from_record(c.member.member_id,c.member)
                or scalar.beta_rule != c.member.beta_rule or scalar.clock_id != c.clock_id
                or rule.scalar_closure is None or rule.scalar_closure.normalization_owner != scalar.normalization
                or rule.scalar_closure.threshold != definition.threshold
                or scalar.normalization.artifact_id != definition.definition_id
                or scalar.normalization.sha256 != definition.fingerprint()
                or scalar.normalization.size_bytes != len(definition.canonical_bytes())):
            raise ValueError('parameter factor substitutes member/beta/schedule/view/clock/scalar definition')


@dataclass(frozen=True, slots=True)
class MatrixParameterFactorArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-factor/arrays'
    operand_id: str
    source: ObjectIdentity
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    producers: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        require_sorted_unique_ids(self.members,attribute='name',field_name='members')
        require_sorted_unique_ids(self.producers,attribute='object_id',field_name='producers')
        if (self.source.object_schema != MatrixParameterFactorSource.SCHEMA
                or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA or self.array_artifact.media_type != 'application/x-npz'
                or not self.members or sum(m.size_bytes for m in self.members)>MAXIMUM_MATRIX_ARRAY_BYTES
                or not 0<self.array_artifact.size_bytes<=MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError('parameter factor diagnostics lose bounded array/source census')


@dataclass(frozen=True, slots=True)
class MatrixParameterScalarSample(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-factor/scalar-sample'
    view: str
    sector: str
    tick: int
    ratio: Decimal | None
    reason: str | None

    def __post_init__(self):
        if self.view not in VIEWS or self.sector not in ('X','Y') or type(self.tick) is not int or self.tick<0:
            raise ValueError('parameter scalar substitutes declared view/sector/tick')
        if (self.ratio is None) != (self.reason is not None):
            raise ValueError('parameter scalar unresolved observation loses reason')
        if self.ratio is not None:
            validate_decimal(self.ratio,field_name='scalar ratio',minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class MatrixParameterFactorProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-factor/product'
    product_id: str
    source: ObjectIdentity
    root_id: str
    independent_group_id: str
    coordinate: ObjectIdentity
    clock_id: str
    source_state: str
    history_numerical_pass: bool | None
    requested_traces: int
    requested_observations: int
    traces: tuple[FactorTrace, ...]
    scalars: tuple[MatrixParameterScalarSample, ...]
    arrays: MatrixParameterFactorArrays
    standing: str = 'EXPOSED_STRUCTURAL_SCORING_NO_PHYSICAL_ADMISSION_OR_QUALIFICATION'

    def __post_init__(self):
        for name in ('product_id','root_id','independent_group_id','clock_id'):
            validate_stable_id(getattr(self,name))
        if (self.source_state not in STATES or self.source != self.arrays.source
                or self.requested_traces not in (2,4) or type(self.requested_observations) is not int
                or self.requested_observations<1 or len(self.scalars)!=self.requested_traces*self.requested_observations
                or self.standing!='EXPOSED_STRUCTURAL_SCORING_NO_PHYSICAL_ADMISSION_OR_QUALIFICATION'
                or (self.source_state=='COMPLETED') != (len(self.traces)==self.requested_traces)
                or self.source_state!='COMPLETED' and (self.traces or self.history_numerical_pass is not None)):
            raise ValueError('parameter factor product manufactures available traces or loses requested denominator')


@dataclass(frozen=True, slots=True)
class MatrixParameterFactorControl(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-factor/control'
    method: str
    measured_errors: tuple[Decimal | None, ...]
    tolerance: Decimal
    denominator_real_coordinates: int
    disposition: str
    applicable: tuple[bool, ...]

    def __post_init__(self):
        validate_decimal(self.tolerance,field_name='control tolerance',minimum=Decimal(0))
        for error in self.measured_errors:
            if error is not None:
                validate_decimal(error,field_name='measured control error',minimum=Decimal(0))
        if (len(self.applicable)!=len(self.measured_errors) or any(type(x) is not bool for x in self.applicable)
                or any(not active and x is not None for active,x in zip(self.applicable,self.measured_errors,strict=True))):
            raise ValueError('parameter factor control substitutes applicability/missingness')
        active_errors = tuple(x for x,active in zip(self.measured_errors,self.applicable,strict=True) if active)
        expected = ('VIOLATED' if any(x is not None and x>self.tolerance for x in active_errors)
            else 'UNASSESSED' if any(x is None for x in active_errors) else 'SATISFIED' if active_errors else 'NOT_APPLICABLE')
        if self.method not in METHODS or not self.measured_errors or self.disposition!=expected:
            raise ValueError('parameter factor control replaces measured failure/missingness')


@dataclass(frozen=True, slots=True)
class MatrixParameterFactorAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-factor/assessment'
    assessment_id: str
    source: ObjectIdentity
    product: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterFactorControl, ...]
    numerical_pass: bool
    admission: str = 'UNASSESSED'

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (tuple(c.method for c in self.controls)!=METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass!=all(c.disposition in ('SATISFIED','NOT_APPLICABLE') for c in self.controls) or self.admission!='UNASSESSED'):
            raise ValueError('parameter factor assessment changes independent census or implies admission')
