# SPDX-License-Identifier: MPL-2.0
"""Signed joint error accounts with exact telescoping and visible missing stages."""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import ANCHORED_LOG_AXES, RAW_LOG_AXES, JointLogCovariance, PairedJointValue
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.policy_indicator import OUTPUTS
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import exact_log_bounds

STAGES = ("REFERENCE", "PROJECTION", "OMITTED_RETURN", "FROZEN_DYNAMICS", "FINITE_MUTATION", "APPROXIMATION")
PARITY_FIELDS = ("chemical_model", "molecular_preparation", "coordinates_masses_constraints",
                 "dynamics_and_integrator", "clock_and_standard_states", "kinetic_consumer")


@dataclass(frozen=True, slots=True)
class SupplierComparisonParity(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/supplier-comparison-parity"
    parity_id: str
    case: ObjectIdentity
    context: ObjectIdentity
    chemical_model: ObjectIdentity
    molecular_preparation: ObjectIdentity
    coordinates_masses_constraints: ObjectIdentity
    dynamics_and_integrator: ObjectIdentity
    clock_and_standard_states: ObjectIdentity
    kinetic_consumer: ObjectIdentity
    reference_method: ObjectIdentity
    conventional_method: ObjectIdentity
    approximation_method: ObjectIdentity
    sources: tuple[ObjectIdentity, ...]
    interpretation: str = "SELECTED_SHARED_OPERANDS_REQUIRING_INDEPENDENT_NATIVE_PARITY_ASSESSMENT"

    def __post_init__(self):
        validate_stable_id(self.parity_id)
        required = tuple(getattr(self, name) for name in (*PARITY_FIELDS, "case", "context",
            "reference_method", "conventional_method", "approximation_method"))
        for value in required:
            exact(value, ObjectIdentity)
        identities(self.sources)
        if not set(required) <= set(self.sources) or len({self.reference_method, self.conventional_method, self.approximation_method}) != 3:
            raise ValueError("comparison needs its complete shared operands and three distinct selected methods")
        if self.interpretation != "SELECTED_SHARED_OPERANDS_REQUIRING_INDEPENDENT_NATIVE_PARITY_ASSESSMENT":
            raise ValueError("a common selected model cannot assert independently assessed physical parity")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.parity_id, self)


@dataclass(frozen=True, slots=True)
class JointErrorStage(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/joint-error-stage"
    role: str
    parity: ObjectIdentity
    method: ObjectIdentity
    original_state: str
    value: PairedJointValue | None
    sources: tuple[ObjectIdentity, ...]
    reason_codes: tuple[str, ...]
    covariance: JointLogCovariance | None = None

    def __post_init__(self):
        if self.role not in (*STAGES, "CONVENTIONAL") or self.original_state not in {"AVAILABLE", "FAILED", "UNKNOWN", "NOT_ENTERED"}:
            raise ValueError("error stage changes its complete role or original outcome state")
        exact(self.parity, ObjectIdentity)
        exact(self.method, ObjectIdentity)
        identities(self.sources, allow_empty=self.original_state == "NOT_ENTERED")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.value is not None:
            exact(self.value, PairedJointValue)
        if self.covariance is not None:
            exact(self.covariance, JointLogCovariance)
            if not set(self.covariance.sources) <= set(self.sources):
                raise ValueError("error stage drops original covariance sources")
            if self.value is not None and self.covariance.axes != (RAW_LOG_AXES if self.value.anchor_wild_type is None else ANCHORED_LOG_AXES):
                raise ValueError("error stage covariance changes original shared-reference dependence")
        if self.original_state == "AVAILABLE" and (self.value is None or self.reason_codes):
            raise ValueError("available stage needs its actual complete joint endpoints")
        if self.original_state != "AVAILABLE" and not self.reason_codes:
            raise ValueError("failed, unknown or unentered stages must retain their reasons")


def endpoint_coordinates(value, scale):
    exact(value, PairedJointValue)
    if scale == "RAW":
        arms = value.wild_type, value.mutant
    elif scale == "ANCHORED" and value.anchor_wild_type is not None:
        arms = value.anchor_wild_type, value.anchored_mutant
    else:
        raise ValueError("selected anchored comparison lacks an actual shared WT reference")
    return (*(item.fraction for arm in arms for item in (arm.kcat_c_s_inv, arm.specificity)),
            value.turnover_ratio, value.specificity_ratio)


def _difference(before, after, scale, tolerances):
    if before.original_state != "AVAILABLE" or after.original_state != "AVAILABLE":
        return None, None, None
    left, right = endpoint_coordinates(before.value, scale), endpoint_coordinates(after.value, scale)
    factors = tuple(Exact.of(a / b) for a, b in zip(left, right, strict=True))
    logs = tuple(exact_log_bounds(value.fraction) for value in factors)
    normalized = []
    for (lo, hi), tolerance in zip(logs, tolerances, strict=True):
        lo, hi, tolerance = Fraction(lo), Fraction(hi), Fraction(tolerance)
        low = Fraction(0) if lo <= 0 <= hi else min(abs(lo), abs(hi))
        normalized.append((Exact.of(low / tolerance), Exact.of(max(abs(lo), abs(hi)) / tolerance)))
    return factors, logs, tuple(normalized)


@dataclass(frozen=True, slots=True)
class SignedJointErrorTerm(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/signed-joint-error-term"
    before_role: str
    after_role: str
    ratio_factors: tuple[Exact, ...] | None
    signed_log_bounds: tuple[tuple[Decimal, Decimal], ...] | None
    normalized_absolute_error_bounds: tuple[tuple[Exact, Exact], ...] | None

    def __post_init__(self):
        if self.before_role not in STAGES or self.after_role not in (*STAGES, "CONVENTIONAL"):
            raise ValueError("error term changes its explicit before/after meanings")
        if len({self.ratio_factors is None, self.signed_log_bounds is None, self.normalized_absolute_error_bounds is None}) != 1:
            raise ValueError("unresolved error term cannot invent a partial exact projection")
        if self.ratio_factors is not None:
            if any(type(values) is not tuple or len(values) != len(OUTPUTS) for values in
                   (self.ratio_factors, self.signed_log_bounds, self.normalized_absolute_error_bounds)):
                raise ValueError("signed error term loses an absolute or paired output")
            for factor, bounds, normalized in zip(self.ratio_factors, self.signed_log_bounds,
                                                  self.normalized_absolute_error_bounds, strict=True):
                exact(factor, Exact)
                if factor.fraction <= 0:
                    raise ValueError("log error ratios must be positive")
                if type(bounds) is not tuple or len(bounds) != 2 or type(normalized) is not tuple or len(normalized) != 2:
                    raise ValueError("signed error needs complete ordered bound pairs")
                for value in bounds:
                    validate_decimal(value, field_name="signed_log_bound")
                for value in normalized:
                    exact(value, Exact)
                if bounds != exact_log_bounds(factor.fraction):
                    raise ValueError("signed log bounds must enclose the original exact ratio")
                if not 0 <= normalized[0].fraction <= normalized[1].fraction:
                    raise ValueError("normalized absolute error must be a nonnegative ordered interval")


def _terms(stages, conventional, scale, tolerances):
    terms = tuple(SignedJointErrorTerm(left.role, right.role, *_difference(left, right, scale, tolerances))
        for left, right in zip(stages, stages[1:]))
    total = SignedJointErrorTerm(stages[0].role, stages[-1].role, *_difference(stages[0], stages[-1], scale, tolerances))
    baseline = SignedJointErrorTerm(stages[0].role, conventional.role, *_difference(stages[0], conventional, scale, tolerances))
    complete = all(row.ratio_factors is not None for row in terms)
    telescoping = None
    if complete:
        product = [Fraction(1)] * len(OUTPUTS)
        for term in terms:
            product = [a * b.fraction for a, b in zip(product, term.ratio_factors, strict=True)]
        telescoping = tuple(Exact.of(value) for value in product)
        if telescoping != total.ratio_factors:
            raise ValueError("signed log account fails its exact multiplicative telescoping identity")
    return terms, total, baseline, telescoping


def _validate_scale_and_tolerances(scale, tolerances):
    if scale not in {"RAW", "ANCHORED"} or type(tolerances) is not tuple or len(tolerances) != len(OUTPUTS):
        raise ValueError("comparison must select its exact scale and all six log tolerances")
    for value in tolerances:
        validate_decimal(value, field_name="log_tolerance", minimum=Decimal(0))
        if value == 0:
            raise ValueError("comparison tolerance must be positive")


@dataclass(frozen=True, slots=True)
class JointErrorDecomposition(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/joint-error-decomposition"
    assessment_id: str
    parity: SupplierComparisonParity
    scenario_id: str
    point_id: str
    scale: str
    log_tolerances: tuple[Decimal, ...]
    stages: tuple[JointErrorStage, ...]
    conventional: JointErrorStage
    terms: tuple[SignedJointErrorTerm, ...]
    total: SignedJointErrorTerm
    conventional_error: SignedJointErrorTerm
    telescoping_product: tuple[Exact, ...] | None
    sign_convention: str = "LOG_REFERENCE_MINUS_LOG_APPROXIMATION"
    chemical_model_discrepancy: str = "OUTSIDE_THE_SHARED_MODEL_COMPARISON_NOT_ASSESSED"
    biological_validation: str = "NOT_ESTABLISHED"
    cross_stage_covariance: str = "NOT_IDENTIFIED_FROM_WITHIN_STAGE_COVARIANCES"

    def __post_init__(self):
        for value in (self.assessment_id, self.scenario_id, self.point_id):
            validate_stable_id(value)
        exact(self.parity, SupplierComparisonParity)
        _validate_scale_and_tolerances(self.scale, self.log_tolerances)
        if type(self.stages) is not tuple or tuple(row.role for row in self.stages) != STAGES or self.conventional.role != "CONVENTIONAL":
            raise ValueError("signed account must retain all declared intermediates and the conventional comparator")
        for row in (*self.stages, self.conventional):
            exact(row, JointErrorStage)
            if row.parity != self.parity.identity or row.value is not None and row.value.value_id != self.point_id:
                raise ValueError("error stage substitutes a point, native model, preparation, dynamics or kinetic consumer")
            if row.original_state == "AVAILABLE":
                endpoint_coordinates(row.value, self.scale)
        if (self.stages[0].method != self.parity.reference_method or self.stages[-1].method != self.parity.approximation_method
                or self.conventional.method != self.parity.conventional_method):
            raise ValueError("error account changes one of its exact selected comparison methods")
        if type(self.terms) is not tuple:
            raise ValueError("signed account needs immutable retained terms")
        for term in (*self.terms, self.total, self.conventional_error):
            exact(term, SignedJointErrorTerm)
        if self.telescoping_product is not None:
            if type(self.telescoping_product) is not tuple:
                raise ValueError("signed account needs immutable exact ratio factors")
            for value in self.telescoping_product:
                exact(value, Exact)
        expected = _terms(self.stages, self.conventional, self.scale, self.log_tolerances)
        if (self.terms, self.total, self.conventional_error, self.telescoping_product) != expected:
            raise ValueError("signed account drops a term, cancellation, missing operand or exact error enclosure")
        if (self.sign_convention != "LOG_REFERENCE_MINUS_LOG_APPROXIMATION"
                or self.chemical_model_discrepancy != "OUTSIDE_THE_SHARED_MODEL_COMPARISON_NOT_ASSESSED"
                or self.biological_validation != "NOT_ESTABLISHED"
                or self.cross_stage_covariance != "NOT_IDENTIFIED_FROM_WITHIN_STAGE_COVARIANCES"):
            raise ValueError("conditional same-model error cannot admit biological or chemical-model accuracy")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


def assess_joint_error_decomposition(parity, stages, conventional, *, scenario_id, point_id, scale,
                                     log_tolerances, assessment_id):
    exact(parity, SupplierComparisonParity)
    _validate_scale_and_tolerances(scale, log_tolerances)
    if type(stages) is not tuple or tuple(row.role for row in stages) != STAGES:
        raise ValueError("signed account must retain all declared intermediates")
    for row in (*stages, conventional):
        exact(row, JointErrorStage)
    return JointErrorDecomposition(assessment_id, parity, scenario_id, point_id, scale, log_tolerances,
        stages, conventional, *_terms(stages, conventional, scale, log_tolerances))
