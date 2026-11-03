# SPDX-License-Identifier: MPL-2.0
"""Exposed complete-census/adverse contracts; zero scientific native entry."""

from dataclasses import fields, replace
from decimal import Decimal as D

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, durable_roster as dr
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_contracts as sc, segmented_evidence as se
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_qualification as sq, segmented_roster as sr, segmented_science as ss
from empirical_lawhood.adapters.methods.battery_refined_inquiry import source_derived_preparation as derived
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_battery_durable_roster import selected54, uncertain  # noqa: F401
from tests.test_battery_refined_inquiry import exposed
from tests.test_battery_segmented_science import _receipt, prepared as exposed_prepared


@pytest.fixture
def prepared():
    return exposed_prepared.__wrapped__()


def failed_trace(config):
    old = exposed(config.native, technical=True)
    values = {field.name: getattr(old, field.name) for field in fields(sc.SegmentedTrace) if hasattr(old, field.name)}
    values.update(trace_id="trace." + config.config_id, config=config, segments=(), transitions=(),
        native_provider_attempts=1, backend_solve_calls=0, temperature_regimes=(),
        native_initializer_contacts=0, initializer_status="NOT_ENTERED;INDEPENDENTLY_ASSESSED_DERIVED_SOURCE_ASSIGNMENT",
        native_output_retention="COMPLETE_NATIVE_ARRAYS_IN_AUTHENTICATED_SEGMENT_PAYLOADS;NO_THINNING")
    for name in ("times_s", "current_a", "voltage_v", "capacity_ah", "mean_temperature_k", "ambient_temperature_k", "control_modes"):
        values[name] = ()
    return sc.SegmentedTrace(**values)


@pytest.fixture(scope="module")
def stocks():
    source, _ = selected54.__wrapped__()
    return {stock: (root, derived.assess_source_roots(root)) for stock in ("Chen2020", "ORegan2022")
        for root in (derived.supply_source_roots(c.identity(source), stock),)}


@pytest.fixture
def roster(selected54, stocks):
    return sr.freeze_segmented_roster(dr.freeze_forecast_roster(*selected54), uncertain(),
        sc.SegmentedMethodProtocol("method.exposed.segmented.60s", D(60)), stocks)


def unavailable(config, protocol, receipt):
    return ss.UnavailableDerivedPreparationAssessment("assessment.unavailable." + config.config_id,
        ss.identity(config, "config_id"), ss.identity(protocol, "protocol_id"), ss.identity(config.preparation, "preparation_id"),
        ss.identity(config.preparation_assessment, "assessment_id"), ss.identity(receipt, "receipt_id"),
        ("actual-initial", "layout", "requested-initial", "source-assignment"), ("actual-complete-preparation-operands-unavailable",))


def test_missing_actual_preparation_has_exact_unevaluable_carrier(prepared, tmp_path):
    config, protocol = prepared[:2]
    trace = failed_trace(config)
    receipt = _receipt(tmp_path, (trace, protocol))
    evidence = se.SegmentedNativeEvidence("evidence.exposed", trace, protocol, None, None, None, None, None, None, None, receipt)
    assessment = se.assess_preparation_evidence(config, evidence)
    assert type(assessment) is ss.UnavailableDerivedPreparationAssessment
    assert assessment.disposition is A.UNEVALUABLE and len(assessment.missing_output_ids) == 4
    summary = sq.summarize_trace(trace, assessment, ())
    assert summary.disposition is A.UNEVALUABLE and summary.charging_segment_calls == 0
    assert "native-technical-failure" in summary.receiver_check.reason_codes
    assert decode_canonical_bytes(evidence.canonical_bytes(), type(evidence), maximum_bytes=None) == evidence
    assert decode_canonical_bytes(summary.canonical_bytes(), type(summary), maximum_bytes=None) == summary
    with pytest.raises(ValueError, match="cannot invent"):
        replace(assessment, disposition=A.SATISFIED)


def test_carrier_cannot_hide_an_actual_materialized_preparation(prepared, tmp_path):
    config, protocol, assignment, layout, requested, actual = prepared
    trace = failed_trace(config)
    receipt = _receipt(tmp_path, (trace, protocol, assignment, layout, requested, actual))
    with pytest.raises(ValueError, match="omits a materialized"):
        se.SegmentedNativeEvidence("evidence.exposed", trace, protocol, None, layout, requested, actual, None, None, None, receipt)
    evidence = se.SegmentedNativeEvidence("evidence.exposed", trace, protocol, assignment, layout, requested, actual, None, None, None, receipt)
    assert se.assess_preparation_evidence(config, evidence).disposition is A.SATISFIED


def test_substantive_method_retains_all54_slots36_comparisons48_native_effects(roster):
    assert len(roster.configurations) == 54 and len(roster.comparison_config_pairs) == 36
    groups = sr.distinct_forecast_groups(roster)
    assert len(groups) == 48 and sum(len(group) - 1 for group in groups) == 6
    assert all(config.native == old for config, old in zip(roster.configurations, roster.original_selection.configurations, strict=True))
    assert decode_canonical_bytes(roster.canonical_bytes(), type(roster), maximum_bytes=None) == roster
    with pytest.raises(ValueError, match="fifty-four"):
        replace(roster, configurations=roster.configurations[:-1])
    with pytest.raises(ValueError, match="thirty-six"):
        replace(roster, comparison_config_pairs=roster.comparison_config_pairs[:-1])


def test_prospective_changed_operands_preserve_all_original_holds_and_unknowns(roster):
    history = uncertain()
    rows = sr.method_dispositions(roster, history)
    assert len(rows) == 54
    assert sum(bool(row.original_entry.matching_uncertain_forecast_ids) for row in rows) == 12
    assert sum(bool(row.original_entry.matching_uncertain_initializer_ids) for row in rows) == 20
    assert all(row.scientific_authority == "NONE" and row.prior_uncertainty.endswith("NO_REPLAY_OR_COMPLETION_CLEARANCE") for row in rows)
    assert all(getattr(history, field) is None for field in ("forecast_count", "initializer_count", "charging_segment_count"))
    with pytest.raises(ValueError, match="cannot clear"):
        replace(rows[0], scientific_authority="AUTHORIZED")


def test_half_quarter_methods_change_real_operands_without_new_units(roster, stocks):
    for duration in (D(30), D(15)):
        changed = sr.freeze_segmented_roster(roster.original_selection, uncertain(),
            sc.SegmentedMethodProtocol("method.exposed.segmented." + str(duration) + "s", duration), stocks)
        assert changed.fingerprint() != roster.fingerprint() and changed.fresh_physical_units == 0
        assert changed.original_selection == roster.original_selection and len(sr.distinct_forecast_groups(changed)) == 48
        assert all(a.native == b.native and a.preparation == b.preparation and a.fingerprint() != b.fingerprint()
            for a, b in zip(changed.configurations, roster.configurations, strict=True))


def negative_product(roster, protocol, receipt):
    traces, summaries = {}, {}
    for group in sr.distinct_forecast_groups(roster):
        config = roster.configurations[group[0]]
        trace = failed_trace(config)
        prepared_protocol = replace(protocol, configuration=ss.identity(config, "config_id"), source=config.preparation.source,
            parameter_source=config.preparation.parameter_source, model_family="DFN" if "dfn" in config.model_view else "SPMe",
            electrode_points=config.numerical_view.electrode_points, particle_points=config.numerical_view.particle_points,
            initial_temperature_k=config.initial_temperature_k)
        summary = sq.summarize_trace(trace, unavailable(config, prepared_protocol, receipt), ())
        for index in group:
            selected = roster.configurations[index]
            traces[selected.config_id] = trace
            summaries[selected.config_id] = summary if index == group[0] else sq.reuse_summary(selected, summary)
    comparisons = tuple(sq.compare_traces(traces[a], traces[b], summaries[a], summaries[b]) for a, b in roster.comparison_config_pairs)
    return sq.qualify_summaries(roster, tuple(summaries.values()), comparisons), traces


def test_complete_negative_qualification_preserves_denominators_aliases_and_cost_once(roster, prepared, tmp_path):
    product, _ = negative_product(roster, prepared[1], _receipt(tmp_path, ()))
    assert product.disposition is A.UNEVALUABLE and product.selected_model is None
    assert len(product.summaries) == 54 and len(product.comparisons) == 36
    assert sum(row.native_contacts for row in product.summaries) == 48
    assert sum(row.condition_reuse is not None for row in product.summaries) == 6
    assert sum(row.cpu_seconds for row in product.summaries) == D(48)
    assert all(row.disposition is A.UNEVALUABLE for row in product.comparisons)
    assert decode_canonical_bytes(product.canonical_bytes(), type(product), maximum_bytes=None) == product
    with pytest.raises(ValueError, match="forecast denominator"):
        sq.qualify_summaries(roster, product.summaries[:-1], product.comparisons)
    with pytest.raises(ValueError, match="comparison denominator"):
        sq.qualify_summaries(roster, product.summaries, product.comparisons[:-1])
    with pytest.raises(ValueError, match="bypass segment fidelity"):
        replace(product, selected_model="dfn-primary", disposition=A.SATISFIED)


def test_complete_fidelity_negative_keeps_later_use_unentered(roster, stocks, prepared, tmp_path):
    rosters = (roster, *(sr.freeze_segmented_roster(roster.original_selection, uncertain(),
        sc.SegmentedMethodProtocol("method.exposed.segmented." + str(duration) + "s", duration), stocks) for duration in (D(30), D(15))))
    products_and_traces = tuple(negative_product(row, prepared[1], _receipt(tmp_path / str(index), ())) for index, row in enumerate(rosters))
    products = tuple(row[0] for row in products_and_traces)
    comparisons = tuple(sq.compare_traces(a_traces[left.configuration.config_id], b_traces[right.configuration.config_id], left, right,
        comparison_kind="SEGMENT_FIDELITY") for (a, a_traces), (b, b_traces) in zip(products_and_traces, products_and_traces[1:])
        for left, right in zip(a.summaries, b.summaries, strict=True))
    result = sq.qualify_fidelity(products, comparisons)
    assert result.disposition is A.UNEVALUABLE and result.selected_model is None
    assert result.selected_forecast_slots == 162 and result.distinct_forecast_effects == 144
    assert result.selected_fidelity_comparisons == result.selected_reference_comparisons == 108
    assert not result.whole_time_certified and not result.physical_qualification
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    with pytest.raises(ValueError, match="remains unentered"):
        sq.require_fidelity_supplier(result)
    with pytest.raises(ValueError, match="one-hundred-eight"):
        sq.qualify_fidelity(products, comparisons[:-1])
    with pytest.raises(ValueError, match="independently recomputed"):
        sq.qualify_fidelity((replace(products[0], admitted_models=("chen-spme",)), *products[1:]), comparisons)
