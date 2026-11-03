# SPDX-License-Identifier: MPL-2.0
"""Full-denominator and overlap controls, with zero scientific native contact."""

from dataclasses import replace
from decimal import Decimal as D

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, science
from empirical_lawhood.adapters.methods.battery_refined_inquiry import durable_roster as durable
from empirical_lawhood.adapters.methods.battery_refined_inquiry import prepared_qualification as prepared
from empirical_lawhood.adapters.methods.battery_refined_inquiry.preparation_science import assess_initial_preparation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_battery_dfn_precision_diagnostic import config_rows
from tests.test_battery_refined_inquiry import selected as historical_selection, table


@pytest.fixture
def selected54():
    source, policy = historical_selection.__wrapped__()
    probe = c.NumericalView("dfn-tolerance", "oregan-dfn", 180, 240, D("1e-6"), D("1e-10"), D("1e-11"))
    selection = replace(policy.selection, tolerance_probe=True, views=tuple(sorted((*policy.views, probe), key=lambda view: view.view_id)))
    policy = replace(policy, views=selection.views, tolerance_probe=True, protocol_sha256=selection.fingerprint())
    source = replace(source, policy=c.identity(policy), protocol_sha256=selection.fingerprint())
    return source, policy


def uncertain():
    return durable.UnknownDiagnosticWork("history.unknown-diagnostic", ObjectIdentity("contact.original", "empirical-lawhood/runtime/native-effect-contact", "1.0.0", "1" * 64),
        ObjectIdentity("numerical.producing-provenance", "empirical-lawhood/kernel/numerical-producing-provenance", "1.0.0", "2" * 64), config_rows())


def test_full54_roster_keeps_all36_comparison_operands_and_one_original_unit(selected54):
    roster = durable.freeze_forecast_roster(*selected54)
    assert len(roster.configurations) == 54 and len(roster.comparison_config_pairs) == 36
    assert roster.scientific_unit_id == c.UNIT and roster.fresh_physical_units == 0
    with pytest.raises(ValueError, match="fifty-four"):
        replace(roster, configurations=roster.configurations[:-1])
    with pytest.raises(ValueError, match="fifty-four"):
        replace(roster, configurations=tuple(reversed(roster.configurations)))
    with pytest.raises(ValueError, match="54/36"):
        replace(roster, comparison_config_pairs=roster.comparison_config_pairs[:-1])
    with pytest.raises(ValueError, match="physical"):
        replace(roster, fresh_physical_units=1)


def test_native_operand_overlap_includes_equal_temperature_recipe_labels(selected54):
    roster = durable.freeze_forecast_roster(*selected54)
    dispositions = durable.entry_dispositions(roster, uncertain())
    assert len(dispositions) == 54
    assert sum(bool(row.matching_uncertain_forecast_ids) for row in dispositions) == 12
    # ORegan SPMe uses the same source SOH request too: three additional matches.
    assert sum(bool(row.matching_uncertain_initializer_ids) for row in dispositions) == 20
    assert all(row.scientific_authority == "NONE" for row in dispositions)
    held = next(row for row in dispositions if row.matching_uncertain_forecast_ids)
    with pytest.raises(ValueError, match="automatic replay"):
        durable.require_no_uncertain_primitive(held)
    with pytest.raises(ValueError, match="cannot clear"):
        replace(held, state="NO_EXACT_OVERLAP_FOUND;NOT_ENTRY_AUTHORITY")
    assert all(row.state.endswith("NOT_ENTRY_AUTHORITY") for row in dispositions if not row.matching_uncertain_initializer_ids and not row.matching_uncertain_forecast_ids)


def test_changed_tolerance_does_not_clear_the_same_initializer(selected54):
    roster = durable.freeze_forecast_roster(*selected54)
    dispositions = durable.entry_dispositions(roster, uncertain())
    tolerance = tuple(row for row in dispositions if row.configuration.object_id.endswith("dfn-tolerance") and row.matching_uncertain_initializer_ids)
    assert len(tolerance) == 4 and all(not row.matching_uncertain_forecast_ids for row in tolerance)
    assert all(row.state == "HOLD_UNCERTAIN_PRIOR_PRIMITIVE" for row in tolerance)


@pytest.mark.parametrize("field", ["forecast_count", "initializer_count", "charging_segment_count"])
def test_unknown_original_counts_cannot_be_filled_with_zero(field):
    with pytest.raises(ValueError, match="cannot invent"):
        replace(uncertain(), **{field: 0})


def test_unknown_original_denominator_cannot_be_thinned_or_renamed():
    old = uncertain()
    assert len(old.configurations) == 12
    with pytest.raises(ValueError, match="original twelve"):
        replace(old, configurations=old.configurations[:-1])
    assert all(getattr(old, field) is None for field in ("forecast_count", "initializer_count", "charging_segment_count"))


def test_namespace_phase_and_decimal_spelling_do_not_clear_same_native_operands(selected54):
    roster = durable.freeze_forecast_roster(*selected54)
    old = uncertain().configurations[0]
    new = next(native for native in roster.configurations if durable.forecast_primitive(native) == durable.forecast_primitive(old))
    assert old.config_id != new.config_id and old.phase != new.phase
    assert durable.initializer_primitive(new) == durable.initializer_primitive(old)


def test_current_compact_qualification_refuses_legacy_receiver_only_success(selected54):
    source, policy = selected54
    traces = table(selected54)
    legacy = science.qualify(source, policy, traces)
    assert legacy.disposition is A.SATISFIED
    summaries = tuple(prepared.summarize_trace(trace, assess_initial_preparation(trace)) for trace in traces)
    qualification = prepared.qualify_summaries(source, policy, summaries, legacy.comparisons)
    assert len(qualification.summaries) == 54 and len(qualification.comparisons) == 36
    assert qualification.disposition is A.UNEVALUABLE and qualification.selected_model is None
    assert qualification.admitted_models == ()
    assert all(summary.preparation.disposition is A.UNEVALUABLE for summary in qualification.summaries)
    assert "complete-independent-initial-preparation-unresolved" in qualification.reason_codes
    assert sum(summary.native_provider_attempts for summary in qualification.summaries) == 54
    with pytest.raises(ValueError, match="no admitted model"):
        prepared.require_current_qualification(qualification)
    with pytest.raises(ValueError, match="all compact"):
        prepared.qualify_summaries(source, policy, summaries[:-1], legacy.comparisons)
    with pytest.raises(ValueError, match="complete independent"):
        prepared.qualify_summaries(source, policy, summaries, legacy.comparisons[:-1])
    with pytest.raises(ValueError, match="full forecast census"):
        replace(qualification, summaries=tuple(reversed(qualification.summaries)))
    assert all(not hasattr(summary, "times_s") for summary in qualification.summaries)
