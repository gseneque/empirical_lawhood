# SPDX-License-Identifier: MPL-2.0
"""Supplier semantic gaps, full paired analysis and original work expense."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction as F

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import PARAMETER_ORDER
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_decision, disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.paired_prediction import predict_paired_rates
from empirical_lawhood.domains.rubisco.rubisco_response.rate_suppliers import RateSupplierCensus, RateSupplierSemantics, assess_rate_suppliers
from empirical_lawhood.domains.rubisco.rubisco_response.reference_supply import ReferenceCostCensus, ReferenceKineticAssessment, assess_reference_supply, profile_reference_costs
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryAttemptStatus, InquiryCost
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.models.time import CausalPhase, ClockLabelSemantics, ClockSpec, ClockTransportKind, HoldSemantics, SamplingSemantics
from tests.kernel.test_time_validation import _transport
from tests.test_recursive_inquiry_policy import obj, work_bound_case


def semantics(supply, *, ledger=None):
    ledger = supply.scenarios[0].ledger if ledger is None else ledger
    source = supply.case.sources[0]
    clock = ClockSpec("clock.disclosed.supplier", "Disclosed physical seconds", "s", "molecular.physical",
        SamplingSemantics.CONTINUOUS, HoldSemantics.NONE, ClockLabelSemantics.INSTANT)
    sources = tuple(sorted((source, ledger.identity, supply.context.identity, ObjectIdentity.from_record(clock.clock_id, clock)),
                           key=lambda row: row.object_id))
    return tuple(RateSupplierSemantics("supplier.disclosed." + binding.parameter, ledger.identity, binding.parameter,
        source, supply.context.identity, supply.context.temperature_k, source, clock, None,
        D(1) if binding.parameter in {"c", "o"} else None,
        source if binding.parameter in {"c", "o"} else None,
        "BULK_ALREADY_INCLUDED" if binding.parameter in {"c", "o"} else "UNIMOLECULAR",
        source if binding.parameter in {"c", "o"} else None, source, source, source,
        "SOURCE_SUPPORTED_REVERSE" if binding.parameter in {"b", "d_c", "d_o"} else "NOT_REVERSE",
        source if binding.parameter in {"b", "d_c", "d_o"} else None, source, sources, ()) for binding in ledger.bindings)


def assess_semantics(supply, selected=(), *, ledger=None):
    return assess_rate_suppliers(supply.scenarios[0].ledger if ledger is None else ledger,
        supply.context, selected, census_id="supplier-census.disclosed")


def test_complete_metadata_preserves_every_physical_applicability_and_assumed_rate_gap():
    supply = disclosed_supply()
    result = assess_semantics(supply, semantics(supply))
    assert result.metadata_complete and len(result.semantics) == 8
    assert result.scientific_admission is A.UNEVALUABLE
    assert sum(key.endswith(".supplier-physical-applicability") for key in result.unresolved_requirement_ids) == 8
    assert sum(key.endswith(".independent-rate-support") for key in result.unresolved_requirement_ids) == 8
    assert sum(key.endswith(".mutation-dependence-support") for key in result.unresolved_requirement_ids) == 7
    assert decode_canonical_bytes(result.canonical_bytes(), RateSupplierCensus, maximum_bytes=200_000) == result
    with pytest.raises(ValueError, match="physical rate applicability"):
        replace(result, scientific_admission=A.SATISFIED)
    missing = assess_semantics(supply)
    assert missing.semantics == (None,) * 8
    assert all(len(rows) == 1 and rows[0].endswith(".supplier-semantics") for _, rows in missing.metadata_requirements)


def test_barrier_without_prefactor_and_transmission_never_establishes_a_rate():
    supply = disclosed_supply()
    ledger = replace(supply.scenarios[0].ledger,
        bindings=tuple(replace(row, supplier_route="FREE_ENERGY_AND_DYNAMICS") if row.parameter == "a" else row
            for row in supply.scenarios[0].ledger.bindings))
    selected = semantics(supply, ledger=ledger)
    selected = (replace(selected[0], paired_prefactor_model=None, paired_transmission_model=None), *selected[1:])
    result = assess_semantics(supply, selected, ledger=ledger)
    gaps = dict(result.metadata_requirements)["a"]
    assert any(key.endswith(".paired-prefactor") for key in gaps)
    assert any(key.endswith(".paired-transmission") for key in gaps)
    assert result.ledger.bindings[0].wild_type_bounds == ledger.bindings[0].wild_type_bounds


def test_native_steps_need_the_shared_physical_clock_transport_and_its_domain():
    supply = disclosed_supply()
    original = semantics(supply)[0]
    clock = replace(original.source_clock, time_unit="step")
    sources = tuple(sorted((*original.sources, ObjectIdentity.from_record("clock.additional.step", clock)), key=lambda row: row.object_id))
    # Exact source identity must use the clock's own identity, not an arbitrary alias.
    sources = tuple(row for row in sources if row.object_id not in {clock.clock_id, "clock.additional.step"})
    sources = tuple(sorted((*sources, ObjectIdentity.from_record(clock.clock_id, clock)), key=lambda row: row.object_id))
    selected = replace(original, source_clock=clock, sources=sources)
    result = assess_semantics(supply, (selected,))
    assert any(key.endswith(".native-to-physical-clock") for key in dict(result.metadata_requirements)["a"])
    transport = replace(_transport(), source_clock_id=clock.clock_id, source_time_unit=clock.time_unit,
        source_coordinate_frame=clock.coordinate_frame, target_clock_id="clock.rubisco.physical-seconds", target_time_unit="s",
        kind=ClockTransportKind.AFFINE_EXACT, scale=D("1e-12"), offset=D(0), tolerance=D(0))
    selected = replace(selected, clock_transport=transport,
        sources=tuple(sorted((*sources, ObjectIdentity.from_record(transport.transport_id, transport)), key=lambda row: row.object_id)))
    result = assess_semantics(supply, (selected,))
    assert not any(key.endswith(".native-to-physical-clock") for key in dict(result.metadata_requirements)["a"])
    assert any(key.endswith(".clock-domain-and-error-assessment") for key in dict(result.metadata_requirements)["a"])


def test_standard_state_bulk_access_and_reverse_commitment_cannot_be_silently_changed():
    supply = disclosed_supply()
    rows = semantics(supply)
    capture = next(row for row in rows if row.parameter == "c")
    with pytest.raises(ValueError, match="standard state requires"):
        replace(capture, standard_state_evidence=None)
    unresolved = replace(capture, gas_access="LOCAL_REQUIRES_ONE_BULK_CONVERSION", bulk_access_assessment=None)
    assert any(key.endswith(".bulk-access-once") for key in dict(assess_semantics(supply, (unresolved,)).metadata_requirements)["c"])
    reverse = next(row for row in rows if row.parameter == "d_c")
    with pytest.raises(ValueError, match="fixed-zero"):
        assess_semantics(supply, (replace(reverse, reverse_commitment="FIXED_ZERO_ASSUMPTION"),))
    with pytest.raises(ValueError, match="temperature"):
        assess_semantics(supply, (replace(rows[0], temperature_k=D(298)),))
    with pytest.raises(ValueError, match="repeats"):
        assess_semantics(supply, (rows[0], rows[0]))


def test_unidentified_reverse_support_remains_unknown_not_exact_zero():
    supply = disclosed_supply()
    old = supply.scenarios[0].ledger
    bindings = tuple(replace(row, evidence_kind="UNIDENTIFIED", supplier_route="UNSELECTED", wild_type_bounds=None,
        mutant_bounds=None, mutation_dependence="UNIDENTIFIED", unresolved_requirement_ids=("requirement.reverse.unknown",))
        if row.parameter == "d_o" else row for row in old.bindings)
    ledger = replace(old, bindings=bindings)
    result = assess_semantics(supply, ledger=ledger)
    assert result.ledger.bindings[4].wild_type_bounds is None
    assert "requirement.reverse.unknown" in result.unresolved_requirement_ids


def test_reference_profile_retains_joint_support_mechanism_scope_and_all_failed_alternatives(monkeypatch):
    supply = disclosed_supply(scenario_states=("AVAILABLE", "UNKNOWN", "FAILED"))
    prediction = predict_paired_rates(supply, prediction_id="reference.disclosed")
    from empirical_lawhood.domains.rubisco.rubisco_prediction import kinetic_model
    for name in ("solve_four_state", "intrinsic_constants", "endpoint_sensitivities"):
        monkeypatch.setattr(kinetic_model, name, lambda *a, **k: pytest.fail("original producer entered"))
    result = assess_reference_supply(supply, prediction, disclosed_decision(supply), assessment_id="reference.analysis")
    assert len(result.supplier_censuses) == 3 and len(result.point_findings) == 2
    assert result.independent_prediction_assessment.conditional_action == "HOLD"
    assert result.mechanism_findings == (("scenario.01", "GATING_ONLY_SPECIFICITY_INVARIANT_BY_CONSTRUCTION"),
        ("scenario.02", "UNRESOLVED_REFERENCE"), ("scenario.03", "UNRESOLVED_REFERENCE"))
    assert all(row.identifiability.local_unconstrained_nullity == 6 for row in result.point_findings)
    gating = next(row for row in result.sensitivities if row.parameter == "a")
    assert gating.maximum_absolute_elasticities[1].fraction == 0
    assert gating.maximum_absolute_elasticities[0].fraction > 0
    assert result.new_native_calls == 0 and result.biological_reference_validity is A.UNEVALUABLE
    assert any(key.endswith(".actual-molecular-supplier-costs") for key in result.unresolved_requirement_ids)
    assert any(key.endswith(".justified-reduction-target") for key in result.unresolved_requirement_ids)
    assert decode_canonical_bytes(result.canonical_bytes(), ReferenceKineticAssessment, maximum_bytes=500_000) == result
    with pytest.raises(ValueError, match="mechanism scope"):
        replace(result, unresolved_requirement_ids=())
    changed = replace(gating, maximum_absolute_derivatives=(Exact.of(0), Exact.of(0)))
    with pytest.raises(ValueError, match="independent rank matrices"):
        replace(result, sensitivities=(changed, *result.sensitivities[1:]))


def test_failed_reference_arithmetic_cannot_create_a_sensitivity_ranking():
    supply = disclosed_supply()
    prediction = predict_paired_rates(supply, prediction_id="reference.failed")
    point = prediction.points[0]
    wrong = replace(point.wild_type, carboxylation_events_per_site_s=Exact.of(100))
    prediction = replace(prediction, points=(replace(point, wild_type=wrong),))
    result = assess_reference_supply(supply, prediction, disclosed_decision(supply), assessment_id="reference.failed.analysis")
    assert result.independent_prediction_assessment.disposition is A.FALSIFIED
    assert result.point_findings[0].identifiability is None
    assert all(row.maximum_absolute_derivatives is None for row in result.sensitivities)
    assert tuple(row.parameter for row in result.sensitivities) == PARAMETER_ORDER


@pytest.mark.parametrize("known", (False, True))
def test_uncertain_work_and_unmeasured_costs_remain_unknown(known):
    state = work_bound_case(known=known).state
    result = profile_reference_costs(state, census_id="costs.retained")
    assert len(result.expected_attempt_ids) == 1
    assert result.groups[0].attempts[0].status is InquiryAttemptStatus.UNCERTAIN_CONTACT
    assert (result.groups[0].method is not None) == known
    assert result.total == InquiryCost(None, None, None)
    assert decode_canonical_bytes(result.canonical_bytes(), ReferenceCostCensus, maximum_bytes=100_000) == result
    with pytest.raises(ValueError, match="unknown or complete"):
        replace(result, total=InquiryCost(D(0), D(0), D(0)))
    with pytest.raises(ValueError, match="drops or duplicates"):
        replace(result, groups=())
    with pytest.raises(ValueError, match="post-outcome"):
        profile_reference_costs(replace(state, information_cutoff=replace(state.information_cutoff, phase=CausalPhase.PRE_ACTION)),
            census_id="costs.invalid-cutoff")


def test_complete_cost_census_keeps_failed_work_and_exact_decimals():
    state = work_bound_case().state
    first = state.operational_census[0]
    second = replace(first, attempt_id="attempt.second", receipt=obj("receipt.second"), status=InquiryAttemptStatus.FAILED)
    second_binding = replace(state.attempt_work_bindings[0], attempt_id=second.attempt_id, witness=second.receipt, work=None)
    values = (D("1000000000000000000000000000000.00001"), D("0.00000000000000000001"))
    events = (replace(state.cost_events[0], cost=InquiryCost(values[0], D(1), None)),
        replace(state.cost_events[0], event_id="event.second", attempt_id=second.attempt_id, receipt=second.receipt,
            cost=InquiryCost(values[1], D(2), None)))
    state = replace(state, operational_census=(first, second), cost_events=events,
        attempt_work_bindings=(state.attempt_work_bindings[0], second_binding))
    with localcontext() as context:
        context.prec = 2
        result = profile_reference_costs(state, census_id="costs.exact")
    assert len(result.groups) == 2 and len(result.expected_attempt_ids) == 2
    assert F(result.total.cpu_seconds) == F(values[0]) + F(values[1])
    assert result.total.wall_seconds == 3 and result.total.retained_bytes is None
    assert any(row.status is InquiryAttemptStatus.FAILED for group in result.groups for row in group.attempts)


def test_public_retained_reference_rejects_future_cutoff_before_opening_inputs():
    from empirical_lawhood.api.domain_composition.rubisco_response.reference import read_reference_analysis
    from empirical_lawhood.science.models.time import InformationCutoff
    cutoff = InformationCutoff("cutoff.invalid", "clock.rubisco.physical-seconds", CausalPhase.PRE_ACTION, D(0))
    with pytest.raises(ValueError, match="post-outcome"):
        read_reference_analysis(directory="does-not-exist", information_cutoff=cutoff, artifact_writer=None)


def assert_actual_retained_reference(directory, plane, *, expected_attempts, expected_action):
    from empirical_lawhood.api.domain_composition.rubisco_response.reference import read_reference_analysis
    from empirical_lawhood.science.models.time import InformationCutoff
    result = read_reference_analysis(directory=directory, artifact_writer=plane,
        information_cutoff=InformationCutoff("cutoff.reference.retained", "clock.rubisco.physical-seconds", CausalPhase.POST_OUTCOME, None))
    assert len(result.references) == len(result.study.cases.cases) == 2
    assert len(result.producing_receipts) == len(result.costs.expected_attempt_ids) == expected_attempts
    assert result.costs.total == InquiryCost(None, None, None)
    assert all(row.new_native_calls == 0 and row.biological_reference_validity is A.UNEVALUABLE for row in result.references)
    assert all(len(row.supplier_censuses) == len(row.supply.scenarios) for row in result.references)
    assert all(row.independent_prediction_assessment.disposition is A.SATISFIED for row in result.references)
    assert next(row for row in result.references if row.supply.case.case_role == "CANDIDATE").independent_prediction_assessment.conditional_action == expected_action
    return result
