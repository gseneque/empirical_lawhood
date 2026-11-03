"""Exposed W1 equations and adverse controls; no biological qualification."""

from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from empirical_lawhood.adapters.methods.rubisco_prediction import kinetic_assay_bridge as bridge
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_supply import (
    ApparentKineticConstants, JointKineticSupply, KineticSupplyContext,
    KineticSupplyMember, KineticSupportInterval, KineticTargetComparison,
)
from empirical_lawhood.adapters.simulators.rubisco_assay.core import Products
from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as D


def identity(name):
    return ObjectIdentity(name, "empirical-lawhood/disclosed-synthetic-test-input", "1.0.0", "a" * 64)


def member(name="case.a", *, constants=None, outcome="AVAILABLE"):
    constants = constants or ApparentKineticConstants(*(Decimal(x) for x in ("6", "75", "1", "3000")))
    return KineticSupplyMember(name, outcome,
        KineticSupportInterval(constants.kcat_c_s_inv, constants.kcat_c_s_inv),
        KineticSupportInterval(constants.specificity, constants.specificity),
        constants if outcome == "AVAILABLE" else None, (), (identity("source.synthetic"),))


def supply(members=None):
    context = KineticSupplyContext("context.synthetic", identity("material.synthetic"),
        identity("assay.synthetic"), Decimal("298.15"))
    members = (member(),) if members is None else members
    return JointKineticSupply("supply.synthetic", context, tuple(row.member_id for row in members),
        members, "DISCLOSED_SYNTHETIC", None, ("unknown-biological-calibration",),
        ("supplied-apparent-kinetics-only",), 0)


def comparison(source, *, compatibility="DECLARED_CONDITIONAL_MATCH"):
    return KineticTargetComparison("comparison.synthetic",
        ObjectIdentity.from_record(source.context.context_id, source.context),
        KineticSupportInterval(Decimal("5.46"), Decimal("5.46")),
        KineticSupportInterval(Decimal("238"), Decimal("238")),
        (identity("reference.synthetic"),), compatibility, Decimal(0))


def run(source, query=None, tolerance=Decimal("1e-10")):
    return bridge.execute_kinetic_assay_bridge(source,
        query or AssayQuery(Decimal("10"), Decimal("250"), Decimal("2.5")),
        result_id="result.synthetic", relative_tolerance=tolerance)


@pytest.mark.parametrize("co2,o2", [(0, 0), (10, 0), (0, 250), (10, 250), (7500, 250)])
def test_joint_supply_reuses_product_solver_and_independent_competition_equations(co2, o2):
    source = supply()
    result = run(source, AssayQuery(Decimal(co2), Decimal(o2), Decimal("2.5")))
    row = result.member_results[0]
    # An independently rearranged exact rational equation, with neither the
    # producer's occupancy solver nor its reference/reduction helpers.
    vc = Fraction(6 * co2) / (Fraction(75) * (1 + Fraction(o2, 3000)) + co2)
    vo = Fraction(o2) / (Fraction(3000) * (1 + Fraction(co2, 75)) + o2)
    assert tuple(float(x) for x in row.reduced_rates) == pytest.approx((float(vc), float(vo)), abs=1e-12)
    assert tuple(float(x) for x in row.products_pga_pgly) == pytest.approx(
        (float((2 * vc + vo) * Fraction(5, 2)), float(vo * Fraction(5, 2))), abs=1e-12)
    assert row.disposition is D.SATISFIED
    assert result.assay_solver_calls == 1
    assert result.molecular_native_contacts == 0
    assert result.biological_predictive_calibration == "NOT_ESTABLISHED"


def test_supply_bridge_assessment_roundtrip_keeps_unknown_covariance_and_conditional_ceiling():
    source = supply()
    numerical = run(source)
    assessed = bridge.assess_joint_kinetic_target(source, comparison(source),
        assessment_id="assessment.synthetic", assay_bridge=numerical)
    assert assessed.robust_conditional_target_disposition is D.SATISFIED
    assert assessed.unresolved_covariance is True
    assert assessed.probability_of_joint_success is None
    assert assessed.nomination_readiness == "NOT_ESTABLISHED"
    assert assessed.biological_challenge_success == "NOT_DEMONSTRATED"
    for value in (source, numerical, assessed):
        assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value
    with pytest.raises(ValueError):
        replace(assessed, probability_of_joint_success=Decimal("0.99"))
    with pytest.raises(ValueError):
        replace(assessed, nomination_readiness="READY")


def test_complete_adverse_and_partial_denominator_does_not_fill_missing_constants(monkeypatch):
    partial = replace(member("case.b"), constants=None, unresolved_terms=("kcat_o", "ko"))
    rows = (member(), partial, *(member("case." + name.lower(), outcome=name)
        for name in ("FALSIFIED", "NOT_ENTERED", "UNEVALUABLE", "UNKNOWN")))
    source = supply(rows)
    calls = []
    original = bridge.execute_assay

    def spy(*args):
        calls.append(args)
        return original(*args)

    monkeypatch.setattr(bridge, "execute_assay", spy)
    result = run(source)
    assert len(calls) == result.assay_solver_calls == 1
    assert len(result.member_results) == len(rows) == 6
    assert all(row.disposition is D.UNEVALUABLE and row.execution == "NOT_ENTERED"
               for row in result.member_results[1:])
    assessed = bridge.assess_joint_kinetic_target(source, comparison(source),
        assessment_id="assessment.partial", assay_bridge=result)
    assert assessed.robust_conditional_target_disposition is D.UNEVALUABLE
    for mutate in (lambda: replace(source, members=source.members[:-1]),
                   lambda: replace(result, member_results=result.member_results[:-1]),
                   lambda: replace(assessed, member_dispositions=assessed.member_dispositions[:-1])):
        with pytest.raises(ValueError, match="denominator|census"):
            mutate()


@pytest.mark.parametrize("compatibility", ["UNRESOLVED", "INCOMPATIBLE"])
def test_incompatible_or_unresolved_reference_join_is_not_a_target_success(compatibility):
    source = supply()
    result = bridge.assess_joint_kinetic_target(source, comparison(source, compatibility=compatibility),
        assessment_id="assessment.unjoined")
    assert result.robust_conditional_target_disposition is D.UNEVALUABLE


def test_official_at_least_comparator_preserves_exact_equality_and_noncompensation():
    source = supply()
    target = replace(comparison(source), maize_turnover_s_inv=source.members[0].turnover_s_inv,
        gp_specificity=source.members[0].specificity)
    assess = lambda value: bridge.assess_joint_kinetic_target(source, value, assessment_id="assessment.compare")
    assert assess(target).robust_conditional_target_disposition is D.SATISFIED
    assert assess(replace(target, practical_relative_margin=Decimal("1e-80"))).robust_conditional_target_disposition is D.FALSIFIED
    assert assess(replace(target, gp_specificity=KineticSupportInterval(Decimal(241), Decimal(241)))).robust_conditional_target_disposition is D.FALSIFIED
    with localcontext() as ctx:
        ctx.prec = 3
        assert assess(target).robust_conditional_target_disposition is D.SATISFIED
        assert assess(replace(target, practical_relative_margin=Decimal("1e-80"))).robust_conditional_target_disposition is D.FALSIFIED
    with pytest.raises(ValueError):
        replace(target, comparator="GREATER_THAN")
    with pytest.raises(ValueError, match="positive"):
        replace(target, maize_turnover_s_inv=KineticSupportInterval(Decimal(0), Decimal(0)))


def test_overlapping_support_is_uncertain_and_one_supported_adverse_member_refutes_robust_claim():
    unknown = replace(member("case.b"), constants=None, unresolved_terms=("unknown-constants",),
        turnover_s_inv=KineticSupportInterval(Decimal(5), Decimal(7)))
    source = supply((member(), unknown))
    assessment = bridge.assess_joint_kinetic_target(source, comparison(source), assessment_id="assessment.overlap")
    assert assessment.robust_conditional_target_disposition is D.UNEVALUABLE
    adverse = replace(unknown, turnover_s_inv=KineticSupportInterval(Decimal(4), Decimal(5)))
    source = supply((member(), adverse))
    assessment = bridge.assess_joint_kinetic_target(source, comparison(source), assessment_id="assessment.adverse")
    assert assessment.robust_conditional_target_disposition is D.FALSIFIED
    assert assessment.nomination_readiness == "NOT_ESTABLISHED"


def test_wrong_product_or_balance_is_retained_and_cannot_pass_joined_target(monkeypatch):
    source = supply()
    monkeypatch.setattr(bridge, "execute_assay", lambda *args: Products(2, 1, 2.5, 0))
    result = run(source)
    assert result.member_results[0].disposition is D.FALSIFIED
    assessed = bridge.assess_joint_kinetic_target(source, comparison(source),
        assessment_id="assessment.bad-products", assay_bridge=result)
    assert assessed.robust_conditional_target_disposition is D.FALSIFIED
    original = result.member_results[0]
    with pytest.raises(ValueError, match="discrepancy"):
        replace(result, member_results=(replace(original, maximum_relative_rate_error=Decimal(0)),))
    with pytest.raises(ValueError, match="independently"):
        replace(result, member_results=(replace(original, independent_rates=(Decimal(1), Decimal(1))),))
    monkeypatch.setattr(bridge, "execute_assay", lambda *args: Products(2, 1, 2.5, 1))
    assert run(source).member_results[0].disposition is D.FALSIFIED


@pytest.mark.parametrize("entered", [True, False])
def test_numerical_failure_has_complete_denominator_and_actual_attempt_count(monkeypatch, entered):
    source = supply()
    if entered:
        def failed(*args):
            raise ArithmeticError("exposed numerical failure")
        monkeypatch.setattr(bridge, "execute_assay", failed)
    else:
        constants = replace(source.members[0].constants, kc_um=Decimal("1e-400"))
        source = supply((member(constants=constants),))
    result = run(source)
    assert result.assay_solver_calls == int(entered)
    assert result.member_results[0].execution == "NUMERICAL_FAILURE"
    assert result.member_results[0].disposition is D.UNEVALUABLE
    assert bridge.assess_joint_kinetic_target(source, comparison(source),
        assessment_id="assessment.failure", assay_bridge=result).robust_conditional_target_disposition is D.UNEVALUABLE


def test_invalid_protocol_or_tolerance_refuses_before_solver_entry(monkeypatch):
    def forbidden(*args):
        raise AssertionError("invalid supplied operands entered solver")
    monkeypatch.setattr(bridge, "execute_assay", forbidden)
    source = supply()
    for tolerance in (Decimal(0), Decimal(-1), Decimal("NaN")):
        with pytest.raises(ValueError):
            run(source, tolerance=tolerance)
    with pytest.raises(ValueError, match="298.15"):
        run(replace(source, context=replace(source.context, temperature_k=Decimal("300"))))


def test_exact_context_and_assay_source_cannot_be_substituted():
    source = supply()
    substitute = replace(source, context=replace(source.context, material=identity("material.other")))
    with pytest.raises(ValueError, match="context"):
        bridge.assess_joint_kinetic_target(substitute, comparison(source), assessment_id="assessment.substitute")
    with pytest.raises(ValueError, match="assay bridge"):
        bridge.assess_joint_kinetic_target(substitute, comparison(substitute),
            assessment_id="assessment.substitute", assay_bridge=run(source))
    assessment = bridge.assess_joint_kinetic_target(source, comparison(source), assessment_id="assessment.exact")
    with pytest.raises(ValueError, match="census"):
        replace(assessment, member_dispositions=(("case.a", D.UNEVALUABLE),))
    with pytest.raises(ValueError, match="census"):
        replace(assessment, unresolved_covariance=False)


@pytest.mark.parametrize("matrix", [
    (("-1", "0", "0", "0"), ("0", "1", "0", "0"), ("0", "0", "1", "0"), ("0", "0", "0", "1")),
    (("0", "1", "0", "0"), ("1", "1", "0", "0"), ("0", "0", "1", "0"), ("0", "0", "0", "1")),
    (("1", "2", "0", "0"), ("2", "1", "0", "0"), ("0", "0", "1", "0"), ("0", "0", "0", "1")),
    (("1", "1", "0", "0"), ("0", "1", "0", "0"), ("0", "0", "1", "0"), ("0", "0", "0", "1")),
])
def test_reported_covariance_rejects_exact_negative_or_nonsymmetric_variance(matrix):
    with pytest.raises(ValueError, match="semidefinite|symmetric"):
        replace(supply(), constant_covariance=tuple(tuple(Decimal(x) for x in row) for row in matrix))


def test_singular_reported_covariance_is_retained_without_creating_a_distribution():
    covariance = tuple(tuple(Decimal(1) for _ in range(4)) for _ in range(4))
    source = replace(supply(), constant_covariance=covariance)
    assessment = bridge.assess_joint_kinetic_target(source, comparison(source), assessment_id="assessment.covariance")
    assert assessment.unresolved_covariance is False
    assert assessment.probability_of_joint_success is None
    with pytest.raises(ValueError):
        replace(source, independent_biological_units=4)
    with pytest.raises(ValueError, match="unresolved"):
        replace(source.members[0], constants=None)
    with pytest.raises(ValueError, match="contradict"):
        replace(source.members[0], specificity=KineticSupportInterval(Decimal(1), Decimal(2)))
