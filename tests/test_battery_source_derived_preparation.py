# SPDX-License-Identifier: MPL-2.0
"""Independent mathematical controls; no native preparation observation."""

from dataclasses import replace
from decimal import Decimal as D
import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, preparation_science as ps, source_derived_preparation as derived
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_battery_refined_inquiry import selected as historical_selection


@pytest.fixture(params=("Chen2020", "ORegan2022"))
def supplier(request):
    source, _ = historical_selection.__wrapped__()
    return derived.supply_source_roots(c.identity(source), request.param)


def test_complete_source_roots_and_assigned_scalars_are_derived_only(supplier, monkeypatch):
    # The independent assessment checks complete-domain brackets directly; it
    # must not reproduce the producer bisection to declare itself independent.
    monkeypatch.setattr(ps, "source_root_enclosures", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("producer re-execution")))
    assessment = derived.assess_source_roots(supplier)
    assert assessment.disposition is A.SATISFIED and assessment.complete_endpoint_denominator == 2
    assert derived.require_assessed_source_roots(supplier, assessment) == supplier
    assert supplier.native_initializer_contacts == 0 and not supplier.observed_native_state
    assert supplier.historical_completion == "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"
    assert assessment.native_preparation == "UNOBSERVED"
    assert decode_canonical_bytes(supplier.canonical_bytes(), derived.SourceRootPreparation, maximum_bytes=None) == supplier


@pytest.mark.parametrize("field", ("usable_capacity_ah", "assigned_negative_concentration", "assigned_positive_concentration", "particle_lithium_capacity_ah", "faraday_constant", "pre_soc_negative_concentration"))
def test_independent_physics_refuses_compensating_or_changed_derived_operands(supplier, field):
    values = {field: getattr(supplier, field) + D(".01")}
    values["binary64_operands"] = tuple((name, float(values.get(name, getattr(supplier, name))).hex()) for name in derived.SCALARS)
    changed = replace(supplier, **values)
    assessment = derived.assess_source_roots(changed)
    assert assessment.disposition is A.FALSIFIED
    with pytest.raises(ValueError, match="independently assessed"):
        derived.require_assessed_source_roots(changed, assessment)


def test_root_denominator_and_native_observation_cannot_be_relabelled(supplier):
    for values in ({"roots": supplier.roots[:1]}, {"observed_native_state": True}, {"native_initializer_contacts": 1},
            {"observation_kind": "OBSERVED"}, {"historical_completion": "COMPLETED"}, {"source_members": supplier.source_members[:-1]}):
        with pytest.raises(ValueError):
            replace(supplier, **values)


def test_independent_endpoint_bracket_refuses_a_narrow_but_wrong_claim(supplier):
    root = supplier.roots[0]
    shift = root.lower_denominator // 100
    altered = replace(root, lower_numerator=root.lower_numerator + shift,
        upper_numerator=root.upper_numerator + shift * root.upper_denominator // root.lower_denominator)
    changed = replace(supplier, roots=(altered, supplier.roots[1]))
    assessment = derived.assess_source_roots(changed)
    assert assessment.disposition is A.FALSIFIED
    assert "independent-source-endpoint-bracket-does-not-cross" in assessment.reason_codes


def test_claimed_positive_assessment_is_recomputed_before_native_assignment(supplier):
    assessment = derived.assess_source_roots(supplier)
    wrong = replace(assessment, assessment_id="assessment.forged-renamed")
    with pytest.raises(ValueError, match="independently assessed"):
        derived.require_assessed_source_roots(supplier, wrong)
