# SPDX-License-Identifier: MPL-2.0
"""Conditional W1 vertical slice using the existing supplied-kinetics assay.

The product solver and independent Decimal flux calculation are distinct.
No partial family is completed by assuming missing constants. Joint target
assessment concerns all supported members and never counts scenarios as
probability trials or biological units.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.adapters.simulators.rubisco_assay.core import (
    GasQuery, Kinetics, execute_assay, reduce_products,
)
from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, validate_decimal, validate_nonempty, validate_stable_id,
)

from .kinetic_supply import (
    CONSTANT_ORDER, CONTEXT, OUTCOMES, JointKineticSupply, KineticSupplyMember,
    KineticTargetComparison,
)


def _rate_error(actual, expected):
    with localcontext(CONTEXT):
        return max(abs(a - b) / abs(b) if b else abs(a - b)
                   for a, b in zip(actual, expected, strict=True))


def _independent_rates(member, query):
    k = member.constants
    with localcontext(CONTEXT):
        c, o = query.co2_um / k.kc_um, query.o2_um / k.ko_um
        denominator = Decimal(1) + c + o
        return (k.kcat_c_s_inv * c / denominator, k.kcat_o_s_inv * o / denominator)


def _product_rates(products, query):
    with localcontext(CONTEXT):
        return ((products[0] - products[1]) / (2 * query.duration_s),
                products[1] / query.duration_s)


def _numerical_error(result, member, query):
    reference = _independent_rates(member, query)
    if result.independent_rates != reference:
        raise ValueError("assay bridge substitutes its independently computed fluxes")
    return max(_rate_error(result.reduced_rates, reference),
               _rate_error(_product_rates(result.products_pga_pgly, query), reference))


def _tolerance(value):
    validate_decimal(value, field_name="rate_tolerance", minimum=Decimal(0))
    if value == 0:
        raise ValueError("binary64 assay comparison needs a declared positive numerical tolerance")


@dataclass(frozen=True, slots=True)
class KineticAssayMemberResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/assay-member-result"
    member_id: str
    source_member: ObjectIdentity
    outcome: str
    products_pga_pgly: tuple[Decimal, Decimal] | None
    reduced_rates: tuple[Decimal, Decimal] | None
    independent_rates: tuple[Decimal, Decimal] | None
    maximum_relative_rate_error: Decimal | None
    disposition: AssessmentDisposition
    reason: str
    execution: str
    assay_call_entered: bool
    balance_residual: Decimal | None

    def __post_init__(self):
        validate_stable_id(self.member_id)
        if (type(self.source_member) is not ObjectIdentity
                or self.source_member.object_schema != KineticSupplyMember.SCHEMA
                or self.outcome not in OUTCOMES):
            raise ValueError("assay result changes its exact supplied member")
        validate_nonempty(self.reason, field_name="assay_result_reason")
        if (self.execution not in ("RETURNED", "NOT_ENTERED", "NUMERICAL_FAILURE")
                or type(self.assay_call_entered) is not bool
                or type(self.disposition) is not AssessmentDisposition):
            raise ValueError("assay result loses its actual execution disposition")
        present = tuple(value is not None for value in (self.products_pga_pgly, self.reduced_rates,
            self.independent_rates, self.maximum_relative_rate_error, self.balance_residual))
        if any(present) and not all(present):
            raise ValueError("assay result drops paired products/rates/independent assessment")
        if all(present):
            if self.outcome != "AVAILABLE" or self.execution != "RETURNED" or not self.assay_call_entered:
                raise ValueError("adverse or unentered family cannot acquire an assay result")
            for values in (self.products_pga_pgly, self.reduced_rates, self.independent_rates):
                if type(values) is not tuple or len(values) != 2:
                    raise ValueError("assay result loses a gas/product branch")
                for value in values:
                    validate_decimal(value, field_name="assay_quantity", minimum=Decimal(0))
            validate_decimal(self.maximum_relative_rate_error, field_name="rate_error", minimum=Decimal(0))
            validate_decimal(self.balance_residual, field_name="balance_residual", minimum=Decimal(0))
            if self.products_pga_pgly[0] < self.products_pga_pgly[1]:
                raise ValueError("assay products violate paired product stoichiometry")
        elif self.disposition is not AssessmentDisposition.UNEVALUABLE:
            raise ValueError("unattempted/partial assay has no passing numerical assessment")
        elif (self.execution == "RETURNED"
                or (self.execution == "NOT_ENTERED" and self.assay_call_entered)):
            raise ValueError("missing assay products contradict its execution census")


@dataclass(frozen=True, slots=True)
class KineticAssayBridgeResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/assay-bridge-result"
    result_id: str
    supply: JointKineticSupply
    query: AssayQuery
    member_results: tuple[KineticAssayMemberResult, ...]
    numerical_relative_tolerance: Decimal
    assay_solver_calls: int
    molecular_native_contacts: int = 0
    biological_predictive_calibration: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.result_id)
        if type(self.supply) is not JointKineticSupply or type(self.query) is not AssayQuery:
            raise ValueError("assay bridge requires its exact typed supply/query")
        self.supply.__post_init__()
        self.query.__post_init__()
        if self.supply.context.temperature_k != Decimal("298.15"):
            raise ValueError("existing supplied-kinetics assay is conditional on 298.15 K")
        _tolerance(self.numerical_relative_tolerance)
        if (type(self.member_results) is not tuple
                or any(type(row) is not KineticAssayMemberResult for row in self.member_results)
                or tuple(row.member_id for row in self.member_results) != self.supply.expected_member_ids):
            raise ValueError("assay bridge loses its full positive/adverse/partial denominator")
        attempted = 0
        for member, result in zip(self.supply.members, self.member_results, strict=True):
            result.__post_init__()
            if result.source_member != ObjectIdentity.from_record(member.member_id, member) or result.outcome != member.outcome:
                raise ValueError("assay bridge substitutes an outcome or supplied member")
            eligible = member.outcome == "AVAILABLE" and member.constants is not None
            if ((eligible and result.execution == "NOT_ENTERED")
                    or (not eligible and result.execution != "NOT_ENTERED")):
                raise ValueError("assay bridge drops eligible execution or fills a partial kinetic family")
            attempted += result.assay_call_entered
            if result.execution == "RETURNED":
                if result.maximum_relative_rate_error != _numerical_error(result, member, self.query):
                    raise ValueError("assay discrepancy disagrees with independent flux/product assessment")
                expected = (AssessmentDisposition.SATISFIED if result.maximum_relative_rate_error <= self.numerical_relative_tolerance
                            and result.balance_residual <= self.numerical_relative_tolerance
                            else AssessmentDisposition.FALSIFIED)
                if result.disposition is not expected:
                    raise ValueError("assay numerical disposition contradicts its actual discrepancy")
        if (type(self.assay_solver_calls) is not int or self.assay_solver_calls != attempted
                or type(self.molecular_native_contacts) is not int or self.molecular_native_contacts != 0
                or self.biological_predictive_calibration != "NOT_ESTABLISHED"):
            raise ValueError("assay bridge changes actual compute accounting or evidence ceiling")


def execute_kinetic_assay_bridge(supply: JointKineticSupply, query: AssayQuery, *,
                                result_id: str, relative_tolerance: Decimal) -> KineticAssayBridgeResult:
    if type(supply) is not JointKineticSupply or type(query) is not AssayQuery:
        raise ValueError("assay bridge requires a typed kinetic supply and query")
    validate_stable_id(result_id)
    _tolerance(relative_tolerance)
    supply.__post_init__()
    query.__post_init__()
    if supply.context.temperature_k != Decimal("298.15"):
        raise ValueError("existing supplied-kinetics assay is conditional on 298.15 K")
    results = []
    for member in supply.members:
        source = ObjectIdentity.from_record(member.member_id, member)
        if member.outcome != "AVAILABLE" or member.constants is None:
            results.append(KineticAssayMemberResult(member.member_id, source, member.outcome,
                None, None, None, None, AssessmentDisposition.UNEVALUABLE,
                "retained-adverse-or-unidentified-kinetic-family", "NOT_ENTERED", False, None))
            continue
        from numpy.linalg import LinAlgError

        k = member.constants
        entered = False
        try:
            parameters = Kinetics(*(float(getattr(k, name)) for name in CONSTANT_ORDER))
            native_query = GasQuery(float(query.co2_um), float(query.o2_um), float(query.duration_s))
            entered = True
            native = execute_assay(parameters, native_query)
            actual = tuple(Decimal(str(value)) for value in reduce_products(native))
            reference = _independent_rates(member, query)
            products = (Decimal(str(native.pga_per_site)), Decimal(str(native.pgly_per_site)))
            error = max(_rate_error(actual, reference), _rate_error(_product_rates(products, query), reference))
            balance = Decimal(str(native.balance_residual))
        except (ArithmeticError, ValueError, LinAlgError) as exc:
            results.append(KineticAssayMemberResult(member.member_id, source, member.outcome,
                None, None, None, None, AssessmentDisposition.UNEVALUABLE,
                f"{type(exc).__name__}: {exc}", "NUMERICAL_FAILURE", entered, None))
            continue
        results.append(KineticAssayMemberResult(member.member_id, source, member.outcome,
            products, actual, reference, error,
            AssessmentDisposition.SATISFIED if error <= relative_tolerance and balance <= relative_tolerance
            else AssessmentDisposition.FALSIFIED,
            "independent-stationary-flux-and-product-stoichiometry", "RETURNED", True, balance))
    return KineticAssayBridgeResult(result_id, supply, query, tuple(results), relative_tolerance,
        sum(row.assay_call_entered for row in results))


@dataclass(frozen=True, slots=True)
class KineticJointTargetAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/joint-target-assessment"
    assessment_id: str
    supply: JointKineticSupply
    comparison: KineticTargetComparison
    assay_bridge: KineticAssayBridgeResult | None
    member_dispositions: tuple[tuple[str, AssessmentDisposition], ...]
    robust_conditional_target_disposition: AssessmentDisposition
    unresolved_covariance: bool
    uncertainty_sources: tuple[str, ...]
    domain_limitations: tuple[str, ...]
    nomination_readiness: str = "NOT_ESTABLISHED"
    biological_challenge_success: str = "NOT_DEMONSTRATED"
    probability_of_joint_success: Decimal | None = None

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (type(self.supply) is not JointKineticSupply
                or type(self.comparison) is not KineticTargetComparison
                or self.nomination_readiness != "NOT_ESTABLISHED"
                or self.biological_challenge_success != "NOT_DEMONSTRATED"
                or self.probability_of_joint_success is not None):
            raise ValueError("conditional target arithmetic cannot create calibration or prize success")
        self.supply.__post_init__()
        self.comparison.__post_init__()
        rows, aggregate = _target_dispositions(self.supply, self.comparison, self.assay_bridge)
        if (self.member_dispositions != rows or self.robust_conditional_target_disposition is not aggregate
                or type(self.unresolved_covariance) is not bool
                or self.unresolved_covariance != (self.supply.constant_covariance is None)
                or self.uncertainty_sources != self.supply.uncertainty_sources
                or self.domain_limitations != self.supply.domain_limitations):
            raise ValueError("joint target assessment changes its complete evidence/disposition census")


def _target_dispositions(supply, target, bridge):
    if target.candidate_context != ObjectIdentity.from_record(supply.context.context_id, supply.context):
        raise ValueError("target assessment substitutes the supplied material/assay context")
    if bridge is not None:
        if type(bridge) is not KineticAssayBridgeResult or bridge.supply != supply:
            raise ValueError("target assessment substitutes its supplied-kinetics assay bridge")
        bridge.__post_init__()
    rows = []
    for member in supply.members:
        disposition = AssessmentDisposition.UNEVALUABLE
        if member.outcome == "AVAILABLE" and target.assay_compatibility == "DECLARED_CONDITIONAL_MATCH":
            checks = []
            margin = Fraction(1) + Fraction(target.practical_relative_margin)
            for candidate, reference in ((member.turnover_s_inv, target.maize_turnover_s_inv),
                                         (member.specificity, target.gp_specificity)):
                if (candidate.lower is not None and reference.upper is not None
                        and Fraction(candidate.lower) >= Fraction(reference.upper) * margin):
                    checks.append(AssessmentDisposition.SATISFIED)
                elif (candidate.upper is not None and reference.lower is not None
                        and Fraction(candidate.upper) < Fraction(reference.lower) * margin):
                    checks.append(AssessmentDisposition.FALSIFIED)
                else:
                    checks.append(AssessmentDisposition.UNEVALUABLE)
            if AssessmentDisposition.FALSIFIED in checks:
                disposition = AssessmentDisposition.FALSIFIED
            elif all(row is AssessmentDisposition.SATISFIED for row in checks):
                disposition = AssessmentDisposition.SATISFIED
        if bridge is not None:
            numerical = bridge.member_results[len(rows)].disposition
            if numerical is AssessmentDisposition.FALSIFIED:
                disposition = AssessmentDisposition.FALSIFIED
            elif numerical is AssessmentDisposition.UNEVALUABLE and disposition is AssessmentDisposition.SATISFIED:
                disposition = AssessmentDisposition.UNEVALUABLE
        rows.append((member.member_id, disposition))
    all_dispositions = tuple(row[1] for row in rows)
    aggregate = (AssessmentDisposition.FALSIFIED if AssessmentDisposition.FALSIFIED in all_dispositions
                 else AssessmentDisposition.UNEVALUABLE if AssessmentDisposition.UNEVALUABLE in all_dispositions
                 else AssessmentDisposition.SATISFIED)
    return tuple(rows), aggregate


def assess_joint_kinetic_target(supply: JointKineticSupply, target: KineticTargetComparison, *,
                               assessment_id: str,
                               assay_bridge: KineticAssayBridgeResult | None = None) -> KineticJointTargetAssessment:
    if type(supply) is not JointKineticSupply or type(target) is not KineticTargetComparison:
        raise ValueError("target assessment requires typed source-conditioned supply/comparison")
    supply.__post_init__()
    target.__post_init__()
    rows, aggregate = _target_dispositions(supply, target, assay_bridge)
    return KineticJointTargetAssessment(assessment_id, supply, target, assay_bridge, rows, aggregate,
        supply.constant_covariance is None, supply.uncertainty_sources, supply.domain_limitations)
