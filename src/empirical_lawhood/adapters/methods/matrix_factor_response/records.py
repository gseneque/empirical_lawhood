"""Shared Matrix response scientific definitions and bounded array contracts."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec
from empirical_lawhood.adapters.simulators.six_matrix_response.contracts import MatrixIntegratorKind, SixMatrixResponseModelFamilyMember, SixMatrixResponseNumericalView
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_decimal, validate_stable_id
from .eligibility import EligibleMatrixArrays


EXPOSED = 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'



PREDICTORS = ('FACTOR', 'FULL_COUPLED', 'GENERIC_SLOW', 'NORM_RADIUS', 'SPECTRA')



ACTION_ROLES = ('COMPLEMENT', 'FACTOR', 'GENERIC', 'TRACE')



SIGNS = ('HOLD', 'MINUS', 'PLUS')



def identity(record):
    for name in ('source_id', 'design_id', 'model_id', 'origin_id', 'forecast_id',
                 'response_id', 'assessment_id', 'operand_id', 'config_id','carrier_id'):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError('matrix response record lacks its declared identity')



@dataclass(frozen=True, slots=True)
class MatrixResponseArrays(CanonicalRecord):
    """Exposed B manifest using the unchanged bounded matrix-array transport."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/development-arrays'
    operand_id: str
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    producers: tuple[ObjectIdentity, ...]
    exposure: str = EXPOSED

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        require_sorted_unique_ids(self.members, attribute='name', field_name='members')
        require_sorted_unique_ids(self.producers, attribute='object_id', field_name='producers')
        if (self.exposure != EXPOSED or not self.members or not self.producers
                or sum(m.size_bytes for m in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES
                or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError('matrix response loses its complete exposed bounded array package')



ResponseArrays = MatrixResponseArrays | EligibleMatrixArrays



@dataclass(frozen=True, slots=True)
class MatrixFactorAction(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/action'
    action_id: str
    role: str
    amplitude: Decimal
    pulse_steps: int
    force_norm: Decimal

    def __post_init__(self):
        validate_stable_id(self.action_id)
        for name in ('amplitude', 'force_norm'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if (self.role not in ACTION_ROLES or self.amplitude == 0 or self.force_norm == 0
                or type(self.pulse_steps) is not int or self.pulse_steps < 1):
            raise ValueError('matrix response action requires its positive finite pulse and norm')



@dataclass(frozen=True, slots=True)
class MatrixFactorResponseDesign(CanonicalRecord):
    """Public conditions; no native innovation seeds or realised future operands."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/design'
    design_id: str
    rule: FactorEventSpec
    member: SixMatrixResponseModelFamilyMember
    view: SixMatrixResponseNumericalView
    alpha_x: Decimal
    alpha_y: Decimal
    origin_tick: int
    actions: tuple[MatrixFactorAction, ...]
    horizon_steps: tuple[int, ...]
    receiver_count: int
    hessian_difference_step: Decimal
    generic_gap_minimum: Decimal
    spectral_gap_minimum: Decimal
    native_reference_tolerance: Decimal
    weak_response_minimum: Decimal
    potential_difference_step: Decimal
    hessian_reference_tolerance: Decimal
    model: ObjectIdentity
    evaluator: ObjectIdentity
    instrument: ObjectIdentity
    receiver: ObjectIdentity
    initial_state_rule: ObjectIdentity
    preparation_schedule: ObjectIdentity
    factor_sector: str = 'Y'
    normalization: str = 'ODD_FINITE_RESPONSE_HALF_PLUS_MINUS'

    def __post_init__(self):
        validate_stable_id(self.design_id)
        require_sorted_unique_ids(self.actions, attribute='action_id', field_name='actions')
        if (tuple(sorted(a.role for a in self.actions)) != ACTION_ROLES
                or len({a.force_norm for a in self.actions}) != 1
                or self.origin_tick not in self.rule.lattice or self.origin_tick < self.rule.risk_start_tick
                or self.rule.primary_dt != self.view.timestep
                or self.factor_sector not in self.rule.sectors
                or self.view.integrator is not MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN
                or self.view.rng_algorithm != 'PCG64'
                or not self.horizon_steps or self.horizon_steps != tuple(sorted(set(self.horizon_steps)))
                or any(type(n) is not int or n < 1 for n in self.horizon_steps)
                or any(a.pulse_steps > self.horizon_steps[-1] for a in self.actions)
                or type(self.receiver_count) is not int or not 1 <= self.receiver_count <= 48
                or self.normalization != 'ODD_FINITE_RESPONSE_HALF_PLUS_MINUS'):
            raise ValueError('matrix response changes factor clock, menu, horizon or same-task normalization')
        for name in ('alpha_x', 'alpha_y', 'generic_gap_minimum', 'spectral_gap_minimum', 'weak_response_minimum'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        for name in ('hessian_difference_step', 'native_reference_tolerance', 'potential_difference_step', 'hessian_reference_tolerance'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
            if getattr(self, name) == 0:
                raise ValueError('matrix response numerical reference must be positive')

    @property
    def cutoff(self):
        return self.rule.primary_dt * self.origin_tick



@dataclass(frozen=True, slots=True)
class MatrixFactorResponseModel(CanonicalRecord):
    """Zero-fit mechanistic comparison; all models share the same native inputs."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/mechanistic-model'
    model_id: str
    implementation: ObjectIdentity
    predictors: tuple[str, ...] = PREDICTORS
    fitting_budget: int = 0
    factor_phase_dimension: int = 48
    radius_phase_dimension: int = 24
    spectra_phase_dimension: int = 48
    generic_phase_dimension: int = 48
    benchmark_phase_dimension: int = 192
    target: str = 'ODD_FINITE_RESPONSE_HALF_PLUS_MINUS'

    def __post_init__(self):
        validate_stable_id(self.model_id)
        if (self.predictors != PREDICTORS or type(self.fitting_budget) is not int or self.fitting_budget != 0
                or (self.factor_phase_dimension, self.radius_phase_dimension, self.spectra_phase_dimension,
                    self.generic_phase_dimension, self.benchmark_phase_dimension) != (48, 24, 48, 48, 192)
                or self.target != 'ODD_FINITE_RESPONSE_HALF_PLUS_MINUS'):
            raise ValueError('matrix mechanistic comparison changes complete methods, complexity, budget or task')



@dataclass(frozen=True, slots=True)
class MatrixFactorPreparationRecipe(CanonicalRecord):
    """Constant new prefix and authentic retained history have distinct meaning."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/preparation-recipe'
    recipe_id: str
    mode: str
    alpha_x: Decimal
    alpha_y: Decimal
    rng_revision: str
    original_source: ObjectIdentity | None = None
    original_result: ArtifactIdentity | None = None
    original_arrays: ArtifactIdentity | None = None
    copied_prefix: ArtifactIdentity | None = None
    copy_proof: ArtifactIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.recipe_id)
        lineage = (self.original_source,self.original_result,self.original_arrays,self.copied_prefix,self.copy_proof)
        if (self.mode == 'CONSTANT_ALPHA_NEW_PREFIX' and (any(v is not None for v in lineage) or self.rng_revision != 'PCG64:1.0.0')
                or self.mode == 'AUTHENTICATED_RETAINED_PREFIX' and (any(v is None for v in lineage) or self.rng_revision != 'ORIGINAL_PCG64DXSM_RETAINED_NOT_REGENERATED')
                or self.mode not in ('CONSTANT_ALPHA_NEW_PREFIX','AUTHENTICATED_RETAINED_PREFIX')):
            raise ValueError('matrix prefix recipe confuses historical ramp lineage with new constant-alpha science')



@dataclass(frozen=True, slots=True)
class MatrixFactorResponseScore(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/score'
    panel_id: str
    panel_role: str
    action_id: str
    horizon_step: int
    receiver_index: int
    predictor: str
    predicted_odd_response: Decimal | None
    actual_odd_response: Decimal
    absolute_error: Decimal | None
    signed_error: Decimal | None
    relative_error: Decimal | None
    weak_response: bool
    complementary_leakage: Decimal
    predictor_disposition: str = 'AVAILABLE'

    def __post_init__(self):
        for name in ('panel_id', 'action_id'):
            validate_stable_id(getattr(self, name))
        for name in ('predicted_odd_response', 'actual_odd_response', 'absolute_error', 'signed_error', 'complementary_leakage'):
            if getattr(self, name) is not None:
                validate_decimal(getattr(self, name), field_name=name)
        if (self.predictor not in PREDICTORS or self.panel_role not in ('COMMON_NOISE_PANEL', 'INDEPENDENT_FUTURE')
                or type(self.horizon_step) is not int or self.horizon_step < 1
                or type(self.receiver_index) is not int or self.receiver_index < 0
                or type(self.weak_response) is not bool or self.complementary_leakage < 0
                or self.predictor_disposition not in ('AVAILABLE', 'UNRESOLVED')
                or (self.predicted_odd_response is None) != (self.predictor_disposition == 'UNRESOLVED')
                or (self.absolute_error is None) != (self.predictor_disposition == 'UNRESOLVED')
                or (self.signed_error is None) != (self.predictor_disposition == 'UNRESOLVED')
                or self.absolute_error is not None and self.absolute_error < 0
                or (self.relative_error is None) != (self.weak_response or self.predictor_disposition == 'UNRESOLVED')):
            raise ValueError('matrix response score changes target, weak-response disposition or panel role')
