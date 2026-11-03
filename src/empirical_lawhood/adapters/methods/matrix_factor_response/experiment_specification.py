# SPDX-License-Identifier: MPL-2.0
"""Editable selections for one parameterized origin-only response experiment.

These records select science, not storage or execution authority. Historical
prediction specifications and their fixed populations retain their exact codecs.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, validate_nonempty,
    validate_sha256, validate_stable_id,
)


POPULATION_ROLES = ("CALIBRATION", "EVALUATION", "TRAIN", "TRANSFER_NEARBY", "TRANSFER_SHIFTED")
FAMILIES = (
    "matrix-history.joint-decreasing-coupling",
    "matrix-history.joint-increasing-coupling",
    "matrix-history.x-first-increasing-coupling",
    "matrix-history.y-first-increasing-coupling",
)
DESCRIPTIONS = ("FACTOR", "FULL_COUPLED", "GENERIC_SLOW", "NORM_RADIUS", "SPECTRA")
HORIZONS = (16, 64, 128)


@dataclass(frozen=True, slots=True)
class PopulationSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/population-selection"
    selection_id: str
    source_key: str
    role: str
    expected_units: int
    family_id: str | None = None
    unit_ids: tuple[str, ...] | None = None

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        validate_stable_id(self.source_key, field_name="source_key")
        if self.role not in POPULATION_ROLES or type(self.expected_units) is not int or self.expected_units < 1:
            raise ValueError("population needs a declared whole-unit role and positive expected census")
        if self.family_id is not None and self.family_id not in FAMILIES:
            raise ValueError("population selects an unsupported Matrix preparation family")
        if self.unit_ids is not None:
            if type(self.unit_ids) is not tuple or not self.unit_ids or self.unit_ids != tuple(sorted(set(self.unit_ids))):
                raise ValueError("population unit selection requires explicit sorted unique original IDs")
            for unit_id in self.unit_ids:
                validate_stable_id(unit_id)


@dataclass(frozen=True, slots=True)
class MatrixResponseMeasurementSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/measurement-selection"
    q: int = 2
    matrix_dimension: int = 4
    descriptions: tuple[str, ...] = DESCRIPTIONS
    horizons: tuple[int, ...] = HORIZONS
    primary_description: str = "FACTOR"
    primary_horizon: int = 128
    origin_tick: int = 256
    feature_window_ticks: int = 32
    feature_cadence_ticks: int = 16
    primary_timestep: Decimal = Decimal("0.001")
    fine_timestep: Decimal = Decimal("0.0005")
    actions: tuple[str, ...] = ("COMPLEMENT", "FACTOR", "GENERIC", "TRACE")
    action_amplitude: Decimal = Decimal("0.01")
    pulse_ticks: int = 16
    panel_roles: tuple[str, ...] = ("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")
    receiver_count: int = 48
    numerical_views: tuple[str, ...] = ("FINE", "PRIMARY")
    target_discrepancy_tolerance: Decimal = Decimal("0.0001")
    estimand: str = "FINITE_DT_ODD_RESPONSE_HALF_PLUS_MINUS"
    metric: str = "MAX_POSITION_MOMENTUM_HS24_ERROR_OVER_NOMINAL_ACTUATOR_SCALE"
    aggregation: str = "MAX_ALL_PANELS_ACTIONS_AND_PRECEDING_HORIZONS_PER_WHOLE_ROOT"

    def __post_init__(self):
        # This domain protocol has a fixed measurement contract. Population and
        # role counts are authoring parameters; changing native science requires
        # another declared and independently validated measurement protocol.
        for name, definition in type(self).__dataclass_fields__.items():
            if name == "SCHEMA":
                continue
            if getattr(self, name) != definition.default or type(getattr(self, name)) is not type(definition.default):
                raise ValueError(f"measurement changes selected origin-only response contract: {name}")

    @property
    def endpoint_count(self):
        return len(self.descriptions) * len(self.horizons)


@dataclass(frozen=True, slots=True)
class MatrixResponseEstimatorSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/estimator-selection"
    method_key: str
    feature_blocks: tuple[str, ...]
    ridge_lambda: Decimal | None
    penalize_intercept: bool = False
    label_transform: str = "LOG1P"
    prediction_transform: str = "ZERO_CLIP_THEN_CUMULATIVE_MAX_THEN_EXPM1"
    fit_scale: str = "LOG1P"
    estimation_rule: str = "STANDARDIZED_RIDGE"

    def __post_init__(self):
        choices = {
            "ALL_ORIGIN_RIDGE": (("CONTEXT", "FACTOR", "NORM_RADIUS", "SPECTRAL"), Decimal(1)),
            "RAW_TRAIN_MEDIAN": ((), None),
            "SPECTRAL_RIDGE": (("CONTEXT", "SPECTRAL"), Decimal(1)),
        }
        if (self.method_key not in choices
                or (self.feature_blocks, self.ridge_lambda) != choices[self.method_key]
                or self.ridge_lambda is not None and type(self.ridge_lambda) is not Decimal
                or self.penalize_intercept is not False or self.label_transform != "LOG1P"
                or self.prediction_transform != "ZERO_CLIP_THEN_CUMULATIVE_MAX_THEN_EXPM1"
                or (self.fit_scale, self.estimation_rule) != (
                    ("RAW_NORMALIZED", "MEDIAN_EVEN_ARITHMETIC_MIDPOINT") if self.method_key == "RAW_TRAIN_MEDIAN"
                    else ("LOG1P", "STANDARDIZED_RIDGE"))):
            raise ValueError("estimator changes frozen feature mask, raw-median/ridge algorithm or forecast transform")

    @property
    def feature_count(self):
        sizes = {"CONTEXT": 10, "NORM_RADIUS": 4, "SPECTRAL": 3, "FACTOR": 4}
        return sum(sizes[block] for block in self.feature_blocks)


def selected_estimators():
    return (
        MatrixResponseEstimatorSelection("ALL_ORIGIN_RIDGE", ("CONTEXT", "FACTOR", "NORM_RADIUS", "SPECTRAL"), Decimal(1)),
        MatrixResponseEstimatorSelection("RAW_TRAIN_MEDIAN", (), None,
            fit_scale="RAW_NORMALIZED", estimation_rule="MEDIAN_EVEN_ARITHMETIC_MIDPOINT"),
        MatrixResponseEstimatorSelection("SPECTRAL_RIDGE", ("CONTEXT", "SPECTRAL"), Decimal(1)),
    )


@dataclass(frozen=True, slots=True)
class MatrixResponseErrorAssessmentSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/assessment-selection"
    improvement_margin: Decimal = Decimal("0.0002")
    null_success_numerator: int = 1
    null_success_denominator: int = 2
    alpha_numerator: int = 1
    alpha_denominator: int = 240
    minimum_usable_units: int = 58
    comparison_slots: int = 12
    improvement_rule: str = "STRICTLY_GREATER_EACH_BASELINE_BOTH_VIEWS"
    missing_rule: str = "NONSUCCESS_RETAIN_ALL_ASSIGNED_UNITS_AND_TAGS"
    usability_scope: str = "FIXED_ROSTER_REQUIREMENT_NO_POPULATION_CONFIDENCE_CLAIM"

    def __post_init__(self):
        for name, definition in type(self).__dataclass_fields__.items():
            if name in {"SCHEMA", "minimum_usable_units"}:
                continue
            if getattr(self, name) != definition.default or type(getattr(self, name)) is not type(definition.default):
                raise ValueError(f"assessment changes selected exact paired criterion: {name}")
        if type(self.minimum_usable_units) is not int or self.minimum_usable_units < 1:
            raise ValueError("assessment requires a positive explicit usable-unit census")

    @property
    def alpha(self):
        return Fraction(self.alpha_numerator, self.alpha_denominator)

    @property
    def null_probability(self):
        return Fraction(self.null_success_numerator, self.null_success_denominator)


@dataclass(frozen=True, slots=True)
class MatrixResponseErrorSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/specification"
    specification_id: str
    question: str
    protocol_sha256: str
    populations: tuple[PopulationSelection, ...]
    measurement: MatrixResponseMeasurementSelection = field(default_factory=MatrixResponseMeasurementSelection)
    methods: tuple[MatrixResponseEstimatorSelection, ...] = field(default_factory=selected_estimators)
    assessment: MatrixResponseErrorAssessmentSelection = field(default_factory=MatrixResponseErrorAssessmentSelection)
    calibration_alpha: Decimal = Decimal("0.05")
    calibration_scope: str = "MAX_POSITIVE_LOG1P_RESIDUAL_ALL15_OUTPUTS_PER_WHOLE_UNIT"
    calibration_missing_rule: str = "INFINITY_RETAIN_ALL_ASSIGNED_UNITS_AND_TAGS"
    reserve_before_training_load: bool = True
    permitted_revisions: tuple[str, ...] = ()
    evidence_scope: str = "PROSPECTIVE_REQUIRED"
    calibration_target_view: str | None = "MAX_PAIRED_VIEWS"

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        validate_nonempty(self.question, field_name="question")
        validate_sha256(self.protocol_sha256, field_name="protocol_sha256")
        if any(type(population) is not PopulationSelection for population in self.populations):
            raise ValueError("specification needs typed whole-unit population selections")
        require_sorted_unique_ids(self.populations, attribute="selection_id", field_name="populations")
        if tuple(sorted(population.role for population in self.populations)) != POPULATION_ROLES:
            raise ValueError("specification requires TRAIN, CALIBRATION, EVALUATION and both transfer populations exactly once")
        if (type(self.measurement) is not MatrixResponseMeasurementSelection
                or type(self.assessment) is not MatrixResponseErrorAssessmentSelection
                or self.methods != selected_estimators() or any(type(method) is not MatrixResponseEstimatorSelection for method in self.methods)
                or type(self.calibration_alpha) is not Decimal or self.calibration_alpha != Decimal("0.05")
                or self.calibration_scope != "MAX_POSITIVE_LOG1P_RESIDUAL_ALL15_OUTPUTS_PER_WHOLE_UNIT"
                or self.calibration_missing_rule != "INFINITY_RETAIN_ALL_ASSIGNED_UNITS_AND_TAGS"
                or self.reserve_before_training_load is not True or self.permitted_revisions
                or self.evidence_scope not in ("PROSPECTIVE_REQUIRED", "EXPOSED_CONFORMANCE")
                or self.calibration_target_view not in (None, "PRIMARY", "MAX_PAIRED_VIEWS")):
            raise ValueError("specification changes selected measurement, methods, calibration or E3 no-search ordering")
        if self.assessment.minimum_usable_units > self.population("EVALUATION").expected_units:
            raise ValueError("usable-unit requirement exceeds the complete evaluation census")

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


def selected_deanneal_specification(*, protocol_sha256, specification_id="matrix.e3.deanneal.response-error"):
    """Select the recorded candidate census without allocating fresh units."""
    populations = tuple(PopulationSelection("population." + role.lower(), source, role, 64, FAMILIES[0])
        for role, source in (("CALIBRATION", "nominal-calibration"), ("EVALUATION", "nominal-confirmation"),
            ("TRAIN", "retained-e2-population"), ("TRANSFER_NEARBY", "deanneal-nearby-reservation"),
            ("TRANSFER_SHIFTED", "deanneal-shifted-reservation")))
    return MatrixResponseErrorSpecification(specification_id,
        "Origin-only prediction opportunity for finite-dt nominal de-anneal FACTOR response error at horizon128",
        protocol_sha256, populations)
