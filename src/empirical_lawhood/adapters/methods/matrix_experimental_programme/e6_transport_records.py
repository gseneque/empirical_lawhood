# SPDX-License-Identifier: MPL-2.0
"""Frozen empirical E6 transport challenges, without a transported warrant.

These seedless records retain declared policy, original calibration ancestry,
causal decisions and complete assigned-root outcomes. Publication, current
authority and scientific qualification remain caller-owned obligations.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id

from .records import MatrixFunctionalCriterion

METHODS = ("ALL_ORIGIN_RIDGE", "RAW_TRAIN_MEDIAN", "SPECTRAL_RIDGE")
TRANSFER_ROLES = ("TRANSFER_NEARBY", "TRANSFER_SHIFTED")
CALIBRATION_METHOD = "SPLIT_UPPER_MAX_POSITIVE_LOG1P_RESIDUAL_MAX_PAIRED_VIEWS_THEN_MAX15_PER_WHOLE_ROOT"
POINT_TRANSFORM = "ZERO_CLIP_THEN_CUMULATIVE_MAX_THEN_EXPM1"
STANDING = "EMPIRICAL_ORIGINAL_E3_TRANSPORT_CHALLENGE_NO_TRANSPORTED_CALIBRATION_OR_SERVICE_WARRANT"
MATCHED_CALIBRATION_METHOD = "UNCHANGED_E4_WHOLE_GROUP_MAX_POSITIVE_PAIRED58_NINE_COORDINATE_LOG_RESIDUAL"
MATCHED_ADMISSION_RULE = "FINITE_ORIGINAL_MODEL_Q_USABLE_CAUSAL_MECHANICS_AND_BOTH_VIEWS_THROUGH_EACH_SAMPLED_QUERY"
MATCHED_METHODS = ("B0", "BR", "S0", "SR")
MATCHED_STANDING = "EMPIRICAL_FROZEN_E4_TRANSPORT_NO_CALIBRATION_GUARANTEE"


def identity(record):
    return ObjectIdentity.from_record(getattr(record, "record_id", getattr(record, "result_id", None)), record)


def _pin(value):
    if type(value) is not ObjectIdentity:
        raise TypeError("E6 transport requires exact original typed identities")
    value.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixE6EmpiricalTransportPolicy(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/e6-empirical-transport-policy"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    candidate_specification: ObjectIdentity
    future_reservation: ObjectIdentity
    future_response_selections: tuple[tuple[str, ObjectIdentity], ...]
    availability: ObjectIdentity
    criterion: MatrixFunctionalCriterion
    endpoint_order: tuple[tuple[str, int], ...]
    calibration_alpha: Decimal
    regime_roster: tuple[tuple[str, str, str, str, ObjectIdentity], ...]
    calibration_method: str = CALIBRATION_METHOD
    point_transform: str = POINT_TRANSFORM
    admission_rule: str = "FINITE_ORIGINAL_Q_USABLE_CAUSAL_FEATURE_AND_PRIMARY_UPPER_AT_MOST_FROZEN_TOLERANCE"
    missing_policy: str = "ALL_ASSIGNED_NONSUCCESS_AND_ADMITTED_UNRESOLVED_FALSE_ADMISSION_WORST_CASE"
    comparator_methods: tuple[str, ...] = METHODS[:2]
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value in (self.candidate_specification, self.future_reservation, self.availability):
            _pin(value)
        if type(self.criterion) is not MatrixFunctionalCriterion:
            raise TypeError("E6 transport retains its genuine selected functional criterion")
        self.criterion.__post_init__()
        matched = self.criterion.is_matched
        if (type(self.future_response_selections) is not tuple or type(self.endpoint_order) is not tuple
                or type(self.regime_roster) is not tuple
                or tuple(role for role, _ in self.future_response_selections) !=
                ("CALIBRATION", "EVALUATION", *TRANSFER_ROLES)
                or len({pin for _, pin in self.future_response_selections}) != 4
                or not self.endpoint_order or len(set(self.endpoint_order)) != len(self.endpoint_order)
                or any(type(description) is not str or type(horizon) is not int or horizon < 1
                    for description, horizon in self.endpoint_order)
                or (self.criterion.predictor, self.criterion.horizon_tick) not in self.endpoint_order
                or self.regime_roster != tuple(sorted(self.regime_roster, key=lambda row: (row[0], row[2])))
                or {row[0] for row in self.regime_roster} != set(TRANSFER_ROLES)
                or any(len({row[index] for row in self.regime_roster}) != len(self.regime_roster) for index in (2, 3, 4))
                or any(len({row[1] for row in self.regime_roster if row[0] == role}) != 1 for role in TRANSFER_ROLES)
                or len({row[1] for row in self.regime_roster}) != 2
                or self.calibration_method != (MATCHED_CALIBRATION_METHOD if matched else CALIBRATION_METHOD) or self.point_transform != POINT_TRANSFORM
                or self.admission_rule != (MATCHED_ADMISSION_RULE if matched else "FINITE_ORIGINAL_Q_USABLE_CAUSAL_FEATURE_AND_PRIMARY_UPPER_AT_MOST_FROZEN_TOLERANCE")
                or self.missing_policy != "ALL_ASSIGNED_NONSUCCESS_AND_ADMITTED_UNRESOLVED_FALSE_ADMISSION_WORST_CASE"
                or self.comparator_methods != (MATCHED_METHODS if matched else METHODS[:2])
                or self.standing != (MATCHED_STANDING if matched else STANDING)):
            raise ValueError("E6 policy changes complete original roles, roots, endpoint menu or frozen empirical rule")
        validate_decimal(self.calibration_alpha, field_name="original calibration alpha", minimum=Decimal(0))
        if not 0 < self.calibration_alpha < 1:
            raise ValueError("E6 policy needs the original strict calibration alpha")
        if matched:
            from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
            if (self.endpoint_order != tuple(('FACTOR', tick) for tick in DENSE_RESPONSE_HORIZONS)
                    or self.calibration_alpha != Decimal('.05')
                    or any(sum(row[0] == role for row in self.regime_roster) != 64 for role in TRANSFER_ROLES)):
                raise ValueError("matched E6 policy changes its complete dense FACTOR menu or two64-root regimes")
        for _, value in self.future_response_selections:
            _pin(value)
        for _, regime, root, group, source in self.regime_roster:
            for value in (regime, root, group):
                validate_stable_id(value)
            _pin(source)

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MatrixE6FrozenCalibrationProjection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/e6-frozen-calibration-projection"
    record_id: str
    policy: ObjectIdentity
    package: ObjectIdentity
    specification: ObjectIdentity
    allocation: ObjectIdentity
    models: ObjectIdentity
    model_freeze: ObjectIdentity
    calibration: ObjectIdentity
    calibrated_freeze: ObjectIdentity
    calibration_unit_ids: tuple[str, ...]
    calibration_alpha: Decimal
    rank: int
    radius_kind: str
    radius: Decimal | None
    endpoint_order: tuple[tuple[str, int], ...]
    calibration_method: str = CALIBRATION_METHOD
    point_transform: str = POINT_TRANSFORM
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value in (self.policy, self.package, self.specification, self.allocation, self.models,
                self.model_freeze, self.calibration, self.calibrated_freeze):
            _pin(value)
        if (self.policy.object_schema != MatrixE6EmpiricalTransportPolicy.SCHEMA
                or type(self.calibration_unit_ids) is not tuple or type(self.endpoint_order) is not tuple
                or not self.calibration_unit_ids or self.calibration_unit_ids != tuple(sorted(set(self.calibration_unit_ids)))
                or type(self.rank) is not int or not 1 <= self.rank <= len(self.calibration_unit_ids) + 1
                or self.radius_kind not in ("FINITE", "INFINITE")
                or (self.radius is None) != (self.radius_kind == "INFINITE")
                or not self.endpoint_order or len(set(self.endpoint_order)) != len(self.endpoint_order)
                or self.calibration_method != CALIBRATION_METHOD or self.point_transform != POINT_TRANSFORM
                or self.standing != STANDING):
            raise ValueError("E6 projection changes original CAL ancestry, census, radius or endpoint rule")
        validate_decimal(self.calibration_alpha, field_name="original calibration alpha", minimum=Decimal(0))
        if not 0 < self.calibration_alpha < 1:
            raise ValueError("E6 projection needs original strict calibration alpha")
        if self.radius is not None:
            validate_decimal(self.radius, field_name="frozen original radius", minimum=Decimal(0))
        from empirical_lawhood.runtime.experimental_statistics import calibration_rank
        if self.rank != calibration_rank(len(self.calibration_unit_ids), self.calibration_alpha):
            raise ValueError("E6 projection changes the original declared CAL rank")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MatrixE6TransportDecision(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/e6-transport-decision"
    record_id: str
    policy: ObjectIdentity
    calibration_projection: ObjectIdentity
    source: ObjectIdentity
    original_source: ObjectIdentity
    root_id: str
    independent_group_id: str
    regime_id: str
    point: ObjectIdentity
    prefix: ObjectIdentity
    cutoff: Decimal
    original_support: bool
    feature_disposition: str
    radius_kind: str
    log_uppers: tuple[Decimal | None, ...]
    error_uppers: tuple[Decimal | None, ...]
    admission: str
    reasons: tuple[str, ...]
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value in (self.policy, self.calibration_projection, self.source, self.original_source, self.point, self.prefix):
            _pin(value)
        for value in (self.root_id, self.independent_group_id, self.regime_id):
            validate_stable_id(value)
        if (self.policy.object_schema != MatrixE6EmpiricalTransportPolicy.SCHEMA
                or self.calibration_projection.object_schema != MatrixE6FrozenCalibrationProjection.SCHEMA
                or type(self.original_support) is not bool
                or self.feature_disposition not in ("AVAILABLE", "NO_CAUSAL_ORIGIN", "UNAVAILABLE", "REFUSED")
                or self.radius_kind not in ("FINITE", "INFINITE")
                or len(self.log_uppers) != len(self.error_uppers) or not self.log_uppers
                or self.admission not in ("ADMIT", "ABSTAIN")
                or self.admission == "ADMIT" and (self.feature_disposition != "AVAILABLE" or self.radius_kind != "FINITE")
                or self.reasons != tuple(sorted(set(self.reasons))) or not self.reasons or self.standing != STANDING):
            raise ValueError("E6 decision changes causal availability, original scope or empirical admission")
        validate_decimal(self.cutoff, field_name="causal physical cutoff", minimum=Decimal(0))
        for values in (self.log_uppers, self.error_uppers):
            for value in values:
                if value is not None:
                    validate_decimal(value, field_name="frozen empirical upper", minimum=Decimal(0))
        if self.radius_kind == "INFINITE" and any(value is not None for value in (*self.log_uppers, *self.error_uppers)):
            raise ValueError("infinite original radius cannot invent finite E6 bounds")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MatrixE6TransportEndpointOutcome(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/e6-transport-endpoint-outcome"
    description: str
    horizon: int
    primary_error: Decimal | None
    fine_error: Decimal | None
    paired_error: Decimal | None
    error_upper: Decimal | None
    coverage: str
    # method, PRIMARY original/log absolute error, FINE original/log absolute error
    comparisons: tuple[tuple[str, Decimal | None, Decimal | None, Decimal | None, Decimal | None], ...]
    # method, PRIMARY and FINE categorical point-failure predictions
    failure_detection: tuple[tuple[str, str, str], ...]

    def __post_init__(self):
        if (type(self.horizon) is not int or self.horizon < 1
                or self.coverage not in ("COVERED", "UNCOVERED", "UNAVAILABLE", "VACUOUS")
                or tuple(row[0] for row in self.comparisons) != METHODS
                or tuple(row[0] for row in self.failure_detection) != METHODS):
            raise ValueError("E6 endpoint drops fixed method comparisons or finite/infinite coverage status")
        for value in (self.primary_error, self.fine_error, self.paired_error, self.error_upper,
                *(value for row in self.comparisons for value in row[1:])):
            if value is not None:
                validate_decimal(value, field_name="E6 endpoint error", minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class MatrixE6TransportLifetime(CanonicalRecord):
    """Descriptive retained-horizon lattice bounds, never continuous lifetimes."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/e6-transport-lifetime"
    description: str
    view: str
    last_definite_pass: int | None
    first_possible_failure: int | None
    first_definite_failure: int | None
    first_nonuse: int | None
    censoring_status: str
    source_dispositions: tuple[str, ...]
    point_failure_horizons: tuple[tuple[str, int | None], ...]

    def __post_init__(self):
        if (self.view not in ("PRIMARY", "FINE") or tuple(row[0] for row in self.point_failure_horizons) != METHODS
                or any(value is not None and (type(value) is not int or value < 1) for value in (
                    self.last_definite_pass, self.first_possible_failure, self.first_definite_failure, self.first_nonuse,
                    *(row[1] for row in self.point_failure_horizons)))):
            raise ValueError("E6 lifetime changes its fixed retained horizon or point-method census")


@dataclass(frozen=True, slots=True)
class MatrixE6TransportRootOutcome(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/e6-transport-root-outcome"
    case_id: str
    unit_id: str
    arm_id: str
    regime_id: str
    source: ObjectIdentity
    decision: ObjectIdentity | None
    point: ObjectIdentity | None
    mechanical: ObjectIdentity | None
    readout: ObjectIdentity | None
    original_support: bool
    admission: str
    outcome_disposition: str
    functional_reliable: bool
    delivered_service: bool
    joint_service: bool
    false_admission_known: bool
    false_admission_unresolved: bool
    whole_menu_coverage: str
    endpoints: tuple[MatrixE6TransportEndpointOutcome, ...]
    preparation_effort: Decimal | None
    reasons: tuple[str, ...]
    lifetimes: tuple[MatrixE6TransportLifetime, ...] = ()
    primary_comparator_improvements: tuple[tuple[str, Decimal | None, Decimal | None], ...] = ()
    beats_both_comparators: bool | None = None

    def __post_init__(self):
        if (self.admission not in ("ADMIT", "ABSTAIN", "MISSING_DECISION")
                or self.outcome_disposition not in ("FINITE", "NO_ORIGIN", "OBSERVATION_FAILED", "NUMERIC_FAILED", "MISSING")
                or self.whole_menu_coverage not in ("COVERED", "UNCOVERED", "UNAVAILABLE", "VACUOUS")
                or any(type(value) is not bool for value in (self.original_support, self.functional_reliable,
                    self.delivered_service, self.joint_service, self.false_admission_known, self.false_admission_unresolved))
                or self.joint_service != (self.delivered_service and self.functional_reliable)
                or self.delivered_service != (self.admission == "ADMIT" and self.outcome_disposition == "FINITE")
                or self.false_admission_known and self.false_admission_unresolved
                or (self.false_admission_known or self.false_admission_unresolved) and self.admission != "ADMIT"
                or self.beats_both_comparators is not None and type(self.beats_both_comparators) is not bool
                or self.primary_comparator_improvements and tuple(row[0] for row in self.primary_comparator_improvements) != METHODS[:2]
                or self.reasons != tuple(sorted(set(self.reasons)))):
            raise ValueError("E6 root changes complete adverse outcomes or empirical service semantics")


@dataclass(frozen=True, slots=True)
class MatrixE6TransportComparison(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/e6-transport-comparison"
    comparison_id: str
    regime_id: str
    assigned_group_ids: tuple[str, ...]
    successes: int
    usable_groups: int
    admitted_groups: int
    false_admissions_known: int
    false_admissions_unresolved: int
    covered_groups: int
    uncovered_groups: int
    unavailable_coverage_groups: int
    vacuous_coverage_groups: int
    functional_successes: int
    delivered_services: int
    p_value_numerator: int
    p_value_denominator: int
    criterion_met_conditionally: bool
    strata: tuple[tuple[bool, str, str, int], ...]
    total_preparation_effort: Decimal | None

    def __post_init__(self):
        n = len(self.assigned_group_ids)
        counts = (self.successes, self.usable_groups, self.admitted_groups, self.false_admissions_known,
            self.false_admissions_unresolved, self.covered_groups, self.uncovered_groups,
            self.unavailable_coverage_groups, self.vacuous_coverage_groups, self.functional_successes, self.delivered_services)
        if (not n or self.assigned_group_ids != tuple(sorted(set(self.assigned_group_ids)))
                or any(type(value) is not int or not 0 <= value <= n for value in counts)
                or sum(counts[5:9]) != n or sum(row[3] for row in self.strata) != n
                or type(self.p_value_numerator) is not int or type(self.p_value_denominator) is not int
                or not 0 <= self.p_value_numerator <= self.p_value_denominator or self.p_value_denominator < 1):
            raise ValueError("E6 regime comparison drops assigned whole roots or exact probability")


@dataclass(frozen=True, slots=True)
class MatrixE6EmpiricalTransportAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/e6-empirical-transport-assessment"
    result_id: str
    programme: ObjectIdentity
    policy: ObjectIdentity
    calibration_projection: ObjectIdentity
    package: ObjectIdentity
    roster: ObjectIdentity
    manifest: ObjectIdentity
    criterion: MatrixFunctionalCriterion
    comparisons: tuple[MatrixE6TransportComparison, ...]
    cases: tuple[MatrixE6TransportRootOutcome, ...]
    unused_family_slots: tuple[str, ...]
    qualification: str = "NOT_ESTABLISHED"
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.result_id)
        if (self.qualification != "NOT_ESTABLISHED" or self.standing != STANDING
                or tuple(row.comparison_id for row in self.comparisons) != ("e6.nearby", "e6.shifted")
                or tuple(row.case_id for row in self.cases) != tuple(sorted({row.case_id for row in self.cases}))):
            raise ValueError("E6 empirical assessment changes original separate regimes or promotes qualification")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MatrixE6TransportManifest(CanonicalRecord):
    """Every assigned case and each independently retained causal/outcome pin."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/e6-transport-manifest"
    record_id: str
    programme: ObjectIdentity
    rows: tuple[tuple[str, ObjectIdentity | None, ObjectIdentity | None, ObjectIdentity | None, ObjectIdentity | None], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        _pin(self.programme)
        if not self.rows or tuple(row[0] for row in self.rows) != tuple(sorted({row[0] for row in self.rows})):
            raise ValueError("E6 manifest omits complete assigned cases")
        for case, *pins in self.rows:
            validate_stable_id(case)
            for pin in pins:
                if pin is not None:
                    _pin(pin)

    @property
    def identity(self):
        return identity(self)
