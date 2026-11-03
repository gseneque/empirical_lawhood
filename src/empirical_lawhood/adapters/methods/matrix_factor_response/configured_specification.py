# SPDX-License-Identifier: MPL-2.0
"""Explicit revision-two E3 parameters for exposed source-bank methods only."""
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from math import isfinite
from typing import ClassVar
from types import MappingProxyType
from empirical_lawhood.runtime.experiment_preparation import ExperimentConfigurationCapability
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_nonempty, validate_stable_id, validate_decimal
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from .experiment_specification import POPULATION_ROLES, PopulationSelection, DESCRIPTIONS, HORIZONS
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import FAMILY_IDS
from empirical_lawhood.adapters.methods.matrix_primary_family import AMENDED_PRIMARY_FAMILY, validate_declared_primary_family
from .origin_mechanics import ORIGIN_RESPONSE_PREDICTORS
from .response_scoring import DENSE_RESPONSE_HORIZONS
from .matched_response_prediction import MATCHED_FEATURE_BLOCKS, MATCHED_METHODS
from .curve_contract import CURVE_IMPROVEMENT_RULE, CURVE_SELECTION_RULE


_PAIRED15_FIXED_FIELDS = (
    ('action_amplitude', Decimal('0.01')),
    ('actions', ('COMPLEMENT', 'FACTOR', 'GENERIC', 'TRACE')),
    ('aggregation', 'MAX_ALL_PANELS_ACTIONS_AND_PRECEDING_HORIZONS_PER_WHOLE_ROOT'),
    ('descriptions', DESCRIPTIONS),
    ('estimand', 'FINITE_DT_ODD_RESPONSE_HALF_PLUS_MINUS'),
    ('feature_cadence_ticks', 16),
    ('feature_window_ticks', 32),
    ('fine_timestep', Decimal('0.0005')),
    ('horizons', HORIZONS),
    ('matrix_dimension', 4),
    ('metric', 'MAX_POSITION_MOMENTUM_HS24_ERROR_OVER_NOMINAL_ACTUATOR_SCALE'),
    ('numerical_views', ('FINE', 'PRIMARY')),
    ('origin_tick', 256),
    ('panel_roles', ('COMMON_NOISE_PANEL', 'INDEPENDENT_FUTURE')),
    ('primary_timestep', Decimal('0.001')),
    ('pulse_ticks', 16),
    ('q', 2),
    ('receiver_count', 48),
    ('target_contract', 'PAIRED15'),
)
_PAIRED15_FIXED = MappingProxyType(dict(_PAIRED15_FIXED_FIELDS))


@dataclass(frozen=True, slots=True)
class ConfiguredE3Measurement(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/measurement-selection"
    VERSION: ClassVar[str] = "3.0.0"
    q: int = _PAIRED15_FIXED["q"]
    matrix_dimension: int = _PAIRED15_FIXED["matrix_dimension"]
    descriptions: tuple[str, ...] = _PAIRED15_FIXED["descriptions"]
    horizons: tuple[int, ...] = _PAIRED15_FIXED["horizons"]
    primary_description: str = field(kw_only=True)
    primary_horizon: int = field(kw_only=True)
    origin_tick: int = _PAIRED15_FIXED["origin_tick"]
    feature_window_ticks: int = _PAIRED15_FIXED["feature_window_ticks"]
    feature_cadence_ticks: int = _PAIRED15_FIXED["feature_cadence_ticks"]
    primary_timestep: Decimal = _PAIRED15_FIXED["primary_timestep"]
    fine_timestep: Decimal = _PAIRED15_FIXED["fine_timestep"]
    actions: tuple[str, ...] = _PAIRED15_FIXED["actions"]
    action_amplitude: Decimal = _PAIRED15_FIXED["action_amplitude"]
    pulse_ticks: int = _PAIRED15_FIXED["pulse_ticks"]
    panel_roles: tuple[str, ...] = _PAIRED15_FIXED["panel_roles"]
    receiver_count: int = _PAIRED15_FIXED["receiver_count"]
    numerical_views: tuple[str, ...] = _PAIRED15_FIXED["numerical_views"]
    target_discrepancy_tolerance: Decimal = field(kw_only=True)
    estimand: str = _PAIRED15_FIXED["estimand"]
    metric: str = _PAIRED15_FIXED["metric"]
    aggregation: str = _PAIRED15_FIXED["aggregation"]
    target_contract: str = 'PAIRED15'

    def __post_init__(self):
        if self.target_contract not in ('PAIRED15', 'MATCHED_FACTOR58'):
            raise ValueError('configured measurement requires its explicit supported target contract')
        (MATCHED58_MEASUREMENT_CAPABILITY if self.is_matched else PAIRED15_MEASUREMENT_CAPABILITY).validate(self)
        if (type(self.primary_description) is not str or type(self.primary_horizon) is not int
                or (self.primary_description, self.primary_horizon) not in tuple(
                    (description, horizon) for description in self.descriptions for horizon in self.horizons)):
            raise ValueError("primary endpoint is outside the implemented response census")
        validate_decimal(self.target_discrepancy_tolerance, field_name="selected target discrepancy tolerance", minimum=Decimal(0))
        if self.target_discrepancy_tolerance <= 0:
            raise ValueError("selected target discrepancy tolerance must be positive")

    @property
    def forecast_endpoints(self):
        descriptions = ('FACTOR',) if self.is_matched else self.descriptions
        return tuple((description, horizon) for description in descriptions for horizon in self.horizons)

    @property
    def endpoint_count(self):
        return len(self.forecast_endpoints)

    @property
    def point_endpoint_count(self):
        return 2 * self.endpoint_count if self.is_matched else self.endpoint_count

    @property
    def is_matched(self):
        return self.target_contract == 'MATCHED_FACTOR58'


PAIRED15_MEASUREMENT_CAPABILITY = ExperimentConfigurationCapability(
    'matrix.response-error.paired15-measurement.v1', ConfiguredE3Measurement, _PAIRED15_FIXED_FIELDS,
    ('primary_description', 'primary_horizon', 'target_discrepancy_tolerance'))

MATCHED58_MEASUREMENT_CAPABILITY = ExperimentConfigurationCapability(
    'matrix.response-error.matched-factor58-measurement.v1', ConfiguredE3Measurement,
    tuple(sorted({**dict(_PAIRED15_FIXED_FIELDS), 'target_contract': 'MATCHED_FACTOR58',
        'descriptions': ORIGIN_RESPONSE_PREDICTORS, 'horizons': DENSE_RESPONSE_HORIZONS,
        'primary_description': 'FACTOR', 'primary_horizon': 128,
        'target_discrepancy_tolerance': Decimal('0.0001')}.items())), ())

# One schema projection per record type. Each selected mode still validates
# against its complete immutable capability above at construction time.
SOURCEBOUND_MEASUREMENT_CAPABILITY = ExperimentConfigurationCapability(
    'matrix.response-error.selected-paired-target.v3', ConfiguredE3Measurement,
    tuple((key, value) for key, value in _PAIRED15_FIXED_FIELDS
        if key not in ('descriptions', 'horizons', 'target_contract')),
    ('descriptions', 'horizons', 'primary_description', 'primary_horizon',
        'target_contract', 'target_discrepancy_tolerance'))


def matched_e3_measurement():
    return ConfiguredE3Measurement(descriptions=ORIGIN_RESPONSE_PREDICTORS, horizons=DENSE_RESPONSE_HORIZONS,
        primary_description='FACTOR', primary_horizon=128, target_discrepancy_tolerance=Decimal('0.0001'),
        target_contract='MATCHED_FACTOR58')


def matched_e3_estimators(*, curve_primary=False):
    base = ('CONTEXT', 'NORM_RADIUS', 'SPECTRAL', 'LINEAR_DEFECT')
    if type(curve_primary) is not bool:
        raise TypeError('matched estimators require their explicit prospective selection')
    if curve_primary:
        base += ('PAST_HESSIAN',)
    rule = CURVE_SELECTION_RULE if curve_primary else 'TWO_FOLD_COMMON_COMPLETE_PAIRED58_RIDGE_PENALTIES_1_10_K_LOSS'
    return tuple(ConfiguredE3Estimator(name, (), None, False, fit_scale='RAW_NORMALIZED',
        estimation_rule='MEDIAN_EVEN_ARITHMETIC_MIDPOINT') if name == 'RAW_TRAIN_MEDIAN' else
        ConfiguredE3Estimator(name, base + (('FACTOR',) if name == 'S0' else ('NORM_DRIFT',) if name == 'B0' else ()),
            None, False, estimation_rule=rule) for name in MATCHED_METHODS)


@dataclass(frozen=True, slots=True)
class ConfiguredE3Protocol(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protocol"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    measurement: ConfiguredE3Measurement
    contract_id: str = "ORIGIN_ONLY_WHOLE_ROOT_PAIRED15"

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.measurement) is not ConfiguredE3Measurement or self.contract_id !=
                ('ORIGIN_ONLY_WHOLE_ROOT_MATCHED58' if self.measurement.is_matched else 'ORIGIN_ONLY_WHOLE_ROOT_PAIRED15')):
            raise ValueError("configured E3 changes its explicit paired response target contract")
        self.measurement.__post_init__()


@dataclass(frozen=True, slots=True)
class ConfiguredE3Estimator(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/estimator-selection"
    VERSION: ClassVar[str] = "3.0.0"
    method_key: str
    feature_blocks: tuple[str, ...]
    ridge_lambda: Decimal | None
    penalize_intercept: bool
    label_transform: str = "LOG1P"
    prediction_transform: str = "ZERO_CLIP_THEN_CUMULATIVE_MAX_THEN_EXPM1"
    fit_scale: str = "LOG1P"
    estimation_rule: str = "STANDARDIZED_RIDGE"

    def __post_init__(self):
        if self.method_key in ('S0', 'B0', 'SHARED_BASE'):
            blocks = ('CONTEXT', 'NORM_RADIUS', 'SPECTRAL', 'LINEAR_DEFECT')
            if self.estimation_rule == CURVE_SELECTION_RULE:
                blocks += ('PAST_HESSIAN',)
            blocks += ('FACTOR',) if self.method_key == 'S0' else ('NORM_DRIFT',) if self.method_key == 'B0' else ()
            if (self.feature_blocks != blocks or self.ridge_lambda is not None or self.penalize_intercept is not False
                    or self.label_transform != 'LOG1P' or self.fit_scale != 'LOG1P'
                    or self.prediction_transform != 'ZERO_CLIP_THEN_CUMULATIVE_MAX_THEN_EXPM1'
                    or self.estimation_rule not in (CURVE_SELECTION_RULE, 'TWO_FOLD_COMMON_COMPLETE_PAIRED58_RIDGE_PENALTIES_1_10_K_LOSS')):
                raise ValueError('matched estimator changes its shared base, equal feature budget or fixed tuning rule')
            return
        choices = {
            "ALL_ORIGIN_RIDGE": (("CONTEXT", "FACTOR", "NORM_RADIUS", "SPECTRAL"), None),
            "RAW_TRAIN_MEDIAN": ((), None),
            "SPECTRAL_RIDGE": (("CONTEXT", "SPECTRAL"), None),
        }
        if (self.method_key not in choices
                or self.feature_blocks != choices[self.method_key][0]
                or (self.ridge_lambda is not None if self.method_key == "RAW_TRAIN_MEDIAN" else
                    type(self.ridge_lambda) is not Decimal or not self.ridge_lambda.is_finite()
                    or self.ridge_lambda <= 0 or not isfinite(float(self.ridge_lambda)) or float(self.ridge_lambda) <= 0)
                or self.ridge_lambda is not None and type(self.ridge_lambda) is not Decimal
                or type(self.penalize_intercept) is not bool
                or self.method_key == "RAW_TRAIN_MEDIAN" and self.penalize_intercept
                or self.label_transform != "LOG1P"
                or self.prediction_transform != "ZERO_CLIP_THEN_CUMULATIVE_MAX_THEN_EXPM1"
                or (self.fit_scale, self.estimation_rule) != (
                    ("RAW_NORMALIZED", "MEDIAN_EVEN_ARITHMETIC_MIDPOINT") if self.method_key == "RAW_TRAIN_MEDIAN"
                    else ("LOG1P", "STANDARDIZED_RIDGE"))):
            raise ValueError("estimator changes frozen feature mask, raw-median/ridge algorithm or forecast transform")

    @property
    def feature_count(self):
        return sum(len(MATCHED_FEATURE_BLOCKS[block]) for block in self.feature_blocks)

@dataclass(frozen=True, slots=True)
class ConfiguredE3Assessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/assessment-selection"
    VERSION: ClassVar[str] = "3.0.0"
    improvement_margin: Decimal | None = field(kw_only=True)
    null_success_numerator: int
    null_success_denominator: int
    alpha_numerator: int
    alpha_denominator: int
    minimum_usable_units: int = field(kw_only=True)
    comparison_ids: tuple[str, ...]
    improvement_rule: str = "STRICTLY_GREATER_EACH_BASELINE_BOTH_VIEWS"
    missing_rule: str = "NONSUCCESS_RETAIN_ALL_ASSIGNED_UNITS_AND_TAGS"
    usability_scope: str = "FIXED_ROSTER_REQUIREMENT_NO_POPULATION_CONFIDENCE_CLAIM"
    duration_margin_numerator: int | None = None
    duration_margin_denominator: int | None = None

    def __post_init__(self):
        matched = self.improvement_rule in (CURVE_IMPROVEMENT_RULE, 'MATCHED_MEAN_K_LOSS_REDUCTION_AT_LEAST_ONE_OF_29')
        if matched:
            if ((self.improvement_margin != Decimal('.1') or type(self.improvement_margin) is not Decimal
                    if self.is_curve_primary else self.improvement_margin is not None)
                    or type(self.duration_margin_numerator) is not int or type(self.duration_margin_denominator) is not int
                    or (self.duration_margin_numerator, self.duration_margin_denominator) != (1, 29)
                    or (self.null_success_numerator, self.null_success_denominator, self.alpha_numerator,
                        self.alpha_denominator, self.minimum_usable_units) != (1, 2, 1, 160, 0)
                    or self.comparison_ids != AMENDED_PRIMARY_FAMILY):
                raise ValueError('matched assessment changes its exact duration margin, complete roster or primary family')
        else:
            validate_decimal(self.improvement_margin, field_name="selected paired margin", minimum=Decimal(0))
            if self.duration_margin_numerator is not None or self.duration_margin_denominator is not None:
                raise ValueError('closed paired15 assessment cannot substitute a duration margin')
        if (any(type(getattr(self, name)) is not int for name in (
                "null_success_numerator", "null_success_denominator", "alpha_numerator", "alpha_denominator"))
                or self.null_success_denominator <= 0 or self.alpha_denominator <= 0
                or not 0 <= self.null_success_numerator <= self.null_success_denominator
                or not 0 < self.alpha_numerator < self.alpha_denominator):
            raise ValueError("assessment requires exact integer probability operands")
        validate_declared_primary_family(self.comparison_ids, required=AMENDED_PRIMARY_FAMILY if matched else FAMILY_IDS)
        if self.alpha * self.comparison_slots > 1:
            raise ValueError("equal per-comparison alpha exceeds the declared family probability budget")
        if (self.improvement_rule not in (CURVE_IMPROVEMENT_RULE, 'MATCHED_MEAN_K_LOSS_REDUCTION_AT_LEAST_ONE_OF_29', "STRICTLY_GREATER_EACH_BASELINE_BOTH_VIEWS")
                or self.missing_rule != "NONSUCCESS_RETAIN_ALL_ASSIGNED_UNITS_AND_TAGS"
                or self.usability_scope != "FIXED_ROSTER_REQUIREMENT_NO_POPULATION_CONFIDENCE_CLAIM"):
            raise ValueError("assessment changes the implemented complete-root decision or missing-data rule")
        if type(self.minimum_usable_units) is not int or self.minimum_usable_units < (0 if matched else 1):
            raise ValueError("assessment requires a positive explicit usable-unit census")

    @property
    def comparison_slots(self):
        return len(self.comparison_ids)

    @property
    def is_curve_primary(self):
        return self.improvement_rule == CURVE_IMPROVEMENT_RULE

    @property
    def alpha(self):
        return Fraction(self.alpha_numerator, self.alpha_denominator)

    @property
    def null_probability(self):
        return Fraction(self.null_success_numerator, self.null_success_denominator)

@dataclass(frozen=True, slots=True)
class ConfiguredMatrixResponseErrorSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/specification"
    VERSION: ClassVar[str] = "3.0.0"
    specification_id: str
    question: str
    protocol: ConfiguredE3Protocol
    populations: tuple[PopulationSelection, ...]
    methods: tuple[ConfiguredE3Estimator, ...]
    assessment: ConfiguredE3Assessment
    calibration_alpha: Decimal
    role_coordinates: tuple[tuple[str, ObjectIdentity], ...]
    calibration_scope: str = "MAX_POSITIVE_LOG1P_RESIDUAL_ALL15_OUTPUTS_PER_WHOLE_UNIT"
    calibration_missing_rule: str = "INFINITY_RETAIN_ALL_ASSIGNED_UNITS_AND_TAGS"
    reserve_before_training_load: bool = True
    permitted_revisions: tuple[str, ...] = ()
    evidence_scope: str = "EXPOSED_CONFORMANCE"
    calibration_target_view: str = field(kw_only=True)

    def __post_init__(self):
        self._validate_selected_contract('EXPOSED_CONFORMANCE')

    def _validate_selected_contract(self, evidence_scope):
        validate_stable_id(self.specification_id)
        validate_nonempty(self.question, field_name="question")
        if type(self.protocol) is not ConfiguredE3Protocol:
            raise TypeError("configured E3 needs its exact typed protocol")
        self.protocol.__post_init__()
        if any(type(population) is not PopulationSelection for population in self.populations):
            raise ValueError("specification needs typed whole-unit population selections")
        require_sorted_unique_ids(self.populations, attribute="selection_id", field_name="populations")
        if tuple(sorted(population.role for population in self.populations)) != POPULATION_ROLES:
            raise ValueError("specification requires TRAIN, CALIBRATION, EVALUATION and both transfer populations exactly once")
        matched = self.measurement.is_matched
        if matched and evidence_scope != 'PROSPECTIVE_REQUIRED':
            raise ValueError('matched paired58 requires the native TRAIN and protected causal workflow')
        expected_methods = MATCHED_METHODS if matched else ('ALL_ORIGIN_RIDGE', 'RAW_TRAIN_MEDIAN', 'SPECTRAL_RIDGE')
        calibration_scope = ('MAX_POSITIVE_LOG1P_RESIDUAL_PAIRED58_FACTOR_OUTPUTS_PER_WHOLE_UNIT' if matched else
            'MAX_POSITIVE_LOG1P_RESIDUAL_ALL15_OUTPUTS_PER_WHOLE_UNIT')
        if (type(self.measurement) is not ConfiguredE3Measurement
                or type(self.assessment) is not ConfiguredE3Assessment
                or type(self.methods) is not tuple or tuple(method.method_key for method in self.methods) != expected_methods
                or any(type(method) is not ConfiguredE3Estimator for method in self.methods)
                or type(self.calibration_alpha) is not Decimal or not self.calibration_alpha.is_finite() or not 0 < self.calibration_alpha < 1
                or self.calibration_scope != calibration_scope
                or self.calibration_missing_rule != "INFINITY_RETAIN_ALL_ASSIGNED_UNITS_AND_TAGS"
                or self.reserve_before_training_load is not True or self.permitted_revisions
                or self.evidence_scope != evidence_scope
                or self.calibration_target_view not in ("PRIMARY", "MAX_PAIRED_VIEWS")):
            raise ValueError("specification changes selected measurement, methods, calibration or E3 no-search ordering")
        self.assessment.__post_init__()
        if matched != (self.assessment.improvement_rule in (CURVE_IMPROVEMENT_RULE, 'MATCHED_MEAN_K_LOSS_REDUCTION_AT_LEAST_ONE_OF_29')):
            raise ValueError('configured E3 mixes a matched target with another primary comparison')
        if matched and self.methods != matched_e3_estimators(curve_primary=self.is_curve_primary):
            raise ValueError('configured E3 mixes the selected primary loss with another feature or fitting rule')
        if matched and (self.calibration_alpha != Decimal('.05') or self.calibration_target_view != 'MAX_PAIRED_VIEWS'
                or self.population('TRAIN').expected_units < 48):
            raise ValueError('matched E3 requires the fixed paired calibration and at least48 assigned TRAIN roots')
        for method in self.methods:
            method.__post_init__()
        if (type(self.role_coordinates) is not tuple or tuple(role for role, _ in self.role_coordinates) != POPULATION_ROLES
                or any(type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version) !=
                    (MatrixParameterCoordinate.SCHEMA, MatrixParameterCoordinate.VERSION) for _, pin in self.role_coordinates)):
            raise ValueError("configured E3 requires explicit exact role-to-coordinate identities")
        for _, pin in self.role_coordinates:
            pin.__post_init__()
        if self.assessment.minimum_usable_units > self.population("EVALUATION").expected_units:
            raise ValueError("usable-unit requirement exceeds the complete evaluation census")

    @property
    def measurement(self):
        return self.protocol.measurement

    @property
    def is_curve_primary(self):
        return self.assessment.is_curve_primary

    @property
    def protocol_sha256(self):
        return self.protocol.fingerprint()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)

    def population(self, role):
        return next(population for population in self.populations if population.role == role)

    @property
    def calibration_rank(self):
        from empirical_lawhood.runtime.experimental_statistics import calibration_rank
        return calibration_rank(self.population("CALIBRATION").expected_units, self.calibration_alpha)

    @property
    def minimum_successes(self):
        from empirical_lawhood.runtime.experimental_statistics import binomial_minimum_successes
        return binomial_minimum_successes(self.population("EVALUATION").expected_units,
            self.assessment.null_probability, self.assessment.alpha)


OPERATIONS = ("calibrate", "evaluate", "fit", "forecast", "freeze", "observe")


def validate_configured_resource_budget(value):
    if (type(value) is not ResourceBudget or any(
            operand is not None and type(operand) is not int for operand in (
                value.cpu_cores, value.memory_bytes, value.gpu_devices, value.wall_time_seconds,
                value.source_scan_bytes, value.output_bytes))
            or value.cpu_cores != 1 or value.gpu_devices != 0
            or value.memory_bytes is None or value.output_bytes is None or value.source_scan_bytes is None
            or value.output_bytes <= 0 or value.source_scan_bytes <= 0):
        raise ValueError("configured E3 needs exact integer finite memory/output/source reservations within its CPU/GPU capability")
    value.__post_init__()


@dataclass(frozen=True, slots=True)
class ConfiguredE3Resources(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-resources"
    record_id: str
    phase_budgets: tuple[tuple[str, ResourceBudget], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.phase_budgets) is not tuple or tuple(name for name, _ in self.phase_budgets) != OPERATIONS:
            raise ValueError("configured E3 resources require all six operation reservations")
        for _, value in self.phase_budgets:
            validate_configured_resource_budget(value)

    def budget(self, phase):
        self.__post_init__()
        return dict(self.phase_budgets)[phase]


@dataclass(frozen=True, slots=True)
class ConfiguredE3CoordinateCensus(CanonicalRecord):
    """Consistent declared exposed metadata, never native source qualification."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-coordinate-census"
    record_id: str
    assignments: tuple[tuple[str, ObjectIdentity, ObjectIdentity], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.assignments) is not tuple or not self.assignments
                or tuple(row[0] for row in self.assignments) != tuple(sorted({row[0] for row in self.assignments}))):
            raise ValueError("configured coordinate census must contain sorted unique original unit identities")
        for unit, source, coordinate in self.assignments:
            validate_stable_id(unit)
            if (type(source) is not ObjectIdentity or type(coordinate) is not ObjectIdentity
                    or (coordinate.object_schema, coordinate.object_version) != (MatrixParameterCoordinate.SCHEMA, MatrixParameterCoordinate.VERSION)):
                raise TypeError("configured coordinate metadata needs explicit source/coordinate identities")
            source.__post_init__()
            coordinate.__post_init__()

    def validate(self, specification, allocation, feature_banks):
        self.__post_init__()
        rows = {unit: (source, coordinate) for unit, source, coordinate in self.assignments}
        if set(rows) != {unit.unit_id for unit in allocation.units}:
            raise ValueError("configured coordinate census drops or adds assigned whole units")
        selected = dict(specification.role_coordinates)
        for role in POPULATION_ROLES:
            if any(rows[unit][1] != selected[role] for unit in allocation.unit_ids(role.lower())):
                raise ValueError("configured population substitutes its explicit coordinate selection")
        for bank in feature_banks:
            for feature in bank.rows:
                if rows[feature.unit_id][0] != feature.native_source:
                    raise ValueError("configured coordinate census substitutes an original bank source")
