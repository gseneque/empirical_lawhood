# SPDX-License-Identifier: MPL-2.0
"""Joint conditional error arithmetic and finite sequential error allocation.

The calculation establishes a support function on the declared finite convex
hull. It does not establish that a molecular error lies in that hull, that an
allowance covers a nonlinear remainder, or that calibration transfers.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import ScientificConditionScope
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_stable_id
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities

OUTPUTS = ("wt-log-kcat-c", "wt-log-specificity", "mutant-log-kcat-c", "mutant-log-specificity",
           "paired-log-kcat-c", "paired-log-specificity")
INTERPRETATIONS = ("RIGOROUS_BOUND", "CALIBRATED_PREDICTOR", "DEVELOPMENT_HEURISTIC")


def exact_vector(values, length, *, nonnegative=False, positive=False):
    if type(values) is not tuple or len(values) != length:
        raise ValueError("joint vector changes its complete dimension")
    for value in values:
        exact(value, Exact)
        if positive and value.fraction <= 0 or nonnegative and value.fraction < 0:
            raise ValueError("joint allowance, tolerance or risk has an invalid sign")


def pre_action_cutoff(value):
    exact(value, InformationCutoff)
    if value.coordinate is None or not value.phase.precedes_or_equals(CausalPhase.PRE_ACTION):
        raise ValueError("prospective policy needs an explicit pre-action coordinate")


def cutoff_precedes(left, right):
    """Use coordinate first, then causal phase; missing/foreign clocks never join."""
    exact(left, InformationCutoff)
    exact(right, InformationCutoff)
    if left.clock_id != right.clock_id or left.coordinate is None or right.coordinate is None:
        return False
    return left.coordinate < right.coordinate or (left.coordinate == right.coordinate
        and left.phase.precedes_or_equals(right.phase)
        and (not left.includes_coordinate or right.includes_coordinate))


@dataclass(frozen=True, slots=True)
class JointErrorVertex(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/joint-error-vertex"
    vertex_id: str
    parameter_errors: tuple[Exact, ...]

    def __post_init__(self):
        validate_stable_id(self.vertex_id)
        if not self.parameter_errors:
            raise ValueError("error vertex must retain every selected parameter")
        exact_vector(self.parameter_errors, len(self.parameter_errors))


@dataclass(frozen=True, slots=True)
class JointIndicatorInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/joint-indicator-input"
    input_id: str
    scope: ScientificConditionScope
    context: ObjectIdentity
    supplier: ObjectIdentity
    parameter_ids: tuple[str, ...]
    parameter_units: tuple[str, ...]
    jacobian: tuple[tuple[Exact, ...], ...]
    vertices: tuple[JointErrorVertex, ...]
    nonlinear_allowances: tuple[Exact, ...]
    log_tolerances: tuple[Exact, ...]
    interpretation: str
    information_cutoff: InformationCutoff
    valid_from: Decimal
    valid_until: Decimal
    sources: tuple[ObjectIdentity, ...]
    output_ids: tuple[str, ...] = OUTPUTS
    support_meaning: str = "CONVEX_HULL_OF_DECLARED_JOINT_VERTICES"

    def __post_init__(self):
        validate_stable_id(self.input_id)
        exact(self.scope, ScientificConditionScope)
        exact(self.context, ObjectIdentity)
        exact(self.supplier, ObjectIdentity)
        require_sorted_unique_strings(self.parameter_ids, field_name="parameter_ids", allow_empty=False)
        if (type(self.parameter_units) is not tuple or len(self.parameter_units) != len(self.parameter_ids)
                or any(type(unit) is not str or not unit.strip() for unit in self.parameter_units)):
            raise ValueError("indicator needs an explicit unit for every parameter perturbation")
        if type(self.jacobian) is not tuple or len(self.jacobian) != len(OUTPUTS):
            raise ValueError("indicator must stack both absolute arms and both paired outputs")
        for row in self.jacobian:
            exact_vector(row, len(self.parameter_ids))
        if type(self.vertices) is not tuple or not self.vertices:
            raise ValueError("empty error support cannot pass the indicator")
        require_sorted_unique_ids(self.vertices, attribute="vertex_id", field_name="vertices")
        for row in self.vertices:
            exact(row, JointErrorVertex)
            exact_vector(row.parameter_errors, len(self.parameter_ids))
        exact_vector(self.nonlinear_allowances, len(OUTPUTS), nonnegative=True)
        exact_vector(self.log_tolerances, len(OUTPUTS), positive=True)
        if self.interpretation not in INTERPRETATIONS or self.output_ids != OUTPUTS:
            raise ValueError("indicator changes its explicit interpretation or endpoint denominator")
        if self.support_meaning != "CONVEX_HULL_OF_DECLARED_JOINT_VERTICES":
            raise ValueError("finite support arithmetic cannot establish a different error distribution")
        pre_action_cutoff(self.information_cutoff)
        for name in ("valid_from", "valid_until"):
            validate_decimal(getattr(self, name), field_name=name)
        if (self.scope.clock_id != self.information_cutoff.clock_id
                or not self.valid_from <= self.information_cutoff.coordinate <= self.valid_until):
            raise ValueError("indicator leaves its declared physical clock or validity horizon")
        identities(self.sources)
        # Log mutant/WT derivatives are exact differences, including any shared
        # parameter columns. An independent paired row would lose dependence.
        for arm, paired in ((0, 4), (1, 5)):
            if any(self.jacobian[paired][j].fraction != self.jacobian[arm + 2][j].fraction - self.jacobian[arm][j].fraction
                   for j in range(len(self.parameter_ids))):
                raise ValueError("paired derivative must retain the exact mutant-minus-WT dependence")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.input_id, self)


def _indicator_values(selection):
    projections = tuple(tuple(sum((a.fraction * b.fraction for a, b in
        zip(row, vertex.parameter_errors, strict=True)), Fraction(0)) for row in selection.jacobian)
        for vertex in selection.vertices)
    support = tuple((min(row[i] for row in projections), max(row[i] for row in projections)) for i in range(len(OUTPUTS)))
    normalized = tuple((max(abs(lo), abs(hi)) + allowance.fraction) / tolerance.fraction
        for (lo, hi), allowance, tolerance in zip(support, selection.nonlinear_allowances, selection.log_tolerances, strict=True))
    return (tuple(tuple(Exact.of(value) for value in row) for row in projections),
            tuple(tuple(Exact.of(value) for value in row) for row in support),
            tuple(Exact.of(value) for value in normalized), Exact.of(max(normalized)))


@dataclass(frozen=True, slots=True)
class JointIndicatorAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/joint-indicator-assessment"
    assessment_id: str
    selection: JointIndicatorInput
    signed_vertex_projections: tuple[tuple[Exact, ...], ...]
    linear_support_bounds: tuple[tuple[Exact, Exact], ...]
    normalized_error_bounds: tuple[Exact, ...]
    eta: Exact
    claim_scope: str = "EXACT_DECLARED_LINEAR_SUPPORT_PLUS_SELECTED_ALLOWANCE_NOT_ERROR_COVERAGE"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.selection, JointIndicatorInput)
        if (self.signed_vertex_projections, self.linear_support_bounds, self.normalized_error_bounds, self.eta) != _indicator_values(self.selection):
            raise ValueError("indicator changes its exact joint projection, signed support or allocated allowance")
        if self.claim_scope != "EXACT_DECLARED_LINEAR_SUPPORT_PLUS_SELECTED_ALLOWANCE_NOT_ERROR_COVERAGE":
            raise ValueError("arithmetic indicator cannot assert calibration or physical error coverage")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


def assess_joint_indicator(selection, *, assessment_id):
    exact(selection, JointIndicatorInput)
    return JointIndicatorAssessment(assessment_id, selection, *_indicator_values(selection))


@dataclass(frozen=True, slots=True)
class CheckpointErrorAllocation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/checkpoint-error-allocation"
    checkpoint_id: str
    information_cutoff: InformationCutoff
    endpoint_error_probabilities: tuple[Exact, ...]

    def __post_init__(self):
        validate_stable_id(self.checkpoint_id)
        pre_action_cutoff(self.information_cutoff)
        exact_vector(self.endpoint_error_probabilities, len(OUTPUTS), nonnegative=True)
        if any(value.fraction > 1 for value in self.endpoint_error_probabilities):
            raise ValueError("allocated error probability exceeds one")


@dataclass(frozen=True, slots=True)
class FiniteSequentialProcedure(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/finite-sequential-procedure"
    procedure_id: str
    checkpoints: tuple[CheckpointErrorAllocation, ...]
    family_error_probability: Exact
    bound_validity_requirement_id: str
    interpretation: str = "FINITE_UNION_BOUND_REQUIRING_VALID_CONDITIONAL_ENDPOINT_BOUNDS"
    audit_design: str = "REFERENCE_ON_EVERY_ASSIGNED_CASE_INCLUDING_REFUSALS"

    def __post_init__(self):
        validate_stable_id(self.procedure_id)
        validate_stable_id(self.bound_validity_requirement_id)
        if type(self.checkpoints) is not tuple or not self.checkpoints:
            raise ValueError("sequential procedure needs its complete frozen finite checkpoint menu")
        if len({row.checkpoint_id for row in self.checkpoints}) != len(self.checkpoints):
            raise ValueError("checkpoint allocation cannot be spent twice")
        for row in self.checkpoints:
            exact(row, CheckpointErrorAllocation)
        for left, right in zip(self.checkpoints, self.checkpoints[1:]):
            if (not cutoff_precedes(left.information_cutoff, right.information_cutoff)
                    or left.information_cutoff.coordinate == right.information_cutoff.coordinate):
                raise ValueError("checkpoint order needs strictly increasing coordinates on the same clock")
        exact(self.family_error_probability, Exact)
        total = sum((value.fraction for row in self.checkpoints for value in row.endpoint_error_probabilities), Fraction(0))
        if not 0 <= total <= self.family_error_probability.fraction < 1:
            raise ValueError("complete joint/checkpoint risk allocation exceeds its frozen family error budget")
        if (self.interpretation != "FINITE_UNION_BOUND_REQUIRING_VALID_CONDITIONAL_ENDPOINT_BOUNDS"
                or self.audit_design != "REFERENCE_ON_EVERY_ASSIGNED_CASE_INCLUDING_REFUSALS"):
            raise ValueError("this finite procedure cannot claim an unimplemented audit or uncertainty design")

    @property
    def allocated_error_probability(self):
        return Exact.of(sum((value.fraction for row in self.checkpoints for value in row.endpoint_error_probabilities), Fraction(0)))

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.procedure_id, self)
