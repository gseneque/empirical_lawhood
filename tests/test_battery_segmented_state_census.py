# SPDX-License-Identifier: MPL-2.0
"""Exposed complete-census projection controls; no scientific acquisition."""

from dataclasses import replace
from decimal import Decimal as D

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_state_census as census
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_contracts as sc, segmented_fidelity as local
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_qualification as sq, segmented_roster as sr
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_science as ss
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_battery_segmented_fidelity_stream import _stream, _compare, prepared as prepared_fixture
from tests.test_battery_segmented_qualification import stocks as stocks_fixture, roster as roster_fixture
from tests.test_battery_segmented_qualification import negative_product, _receipt, uncertain, selected54  # noqa: F401

prepared = prepared_fixture
stocks = stocks_fixture
roster = roster_fixture


def test_compact_projection_keeps_exact_gap_and_complete_counts(prepared, tmp_path):
    original = _compare(_stream(prepared, tmp_path / "left"), _stream(prepared, tmp_path / "right", horizon=30, segments=2))
    result = census.compact_stream_assessment(original)
    assert result.original_assessment == ss.identity(original, "assessment_id")
    assert result.coverage_issues == original.coverage_issues and result.disposition is A.UNEVALUABLE
    assert result.declared_segment_counts == (1, 2) and result.retained_native_knots == (2, 4)
    assert result.comparison_counts == (original.interval_queries_including_repeated_boundaries,
        original.compared_rhs_components, original.compared_algebraic_components, original.compared_derivative_components)
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    with pytest.raises(ValueError, match="clears an unresolved"):
        replace(result, disposition=A.SATISFIED, reason_codes=())


def test_compact_projection_retains_actual_full_state_negative(prepared, tmp_path):
    original = _compare(_stream(prepared, tmp_path / "left"),
        _stream(prepared, tmp_path / "right", horizon=30, changed_state=(0, .01)))
    result = census.compact_stream_assessment(original)
    assert result.disposition is A.FALSIFIED
    assert dict(result.original_interval_dispositions)[A.FALSIFIED.value] > 0
    assert not result.whole_time_certified and not result.physical_qualification
    with pytest.raises(ValueError, match="scope"):
        replace(result, physical_qualification=True)


@pytest.fixture
def complete_negative(roster, stocks, prepared, tmp_path):
    rosters = (roster, *(sr.freeze_segmented_roster(roster.original_selection, uncertain(),
        sc.SegmentedMethodProtocol("method.exposed.segmented." + str(n) + "s", n), stocks) for n in (D(30), D(15))))
    pairs = tuple(negative_product(row, prepared[1], _receipt(tmp_path / str(i), ())) for i, row in enumerate(rosters))
    products = tuple(row[0] for row in pairs)
    comparisons = tuple(sq.compare_traces(at[left.configuration.config_id], bt[right.configuration.config_id], left, right,
        comparison_kind="SEGMENT_FIDELITY") for (a, at), (b, bt) in zip(pairs, pairs[1:])
        for left, right in zip(a.summaries, b.summaries, strict=True))
    receiver = sq.qualify_fidelity(products, comparisons)
    control = ss.identity(local.FullStateControlProtocol("control.exposed.complete"), "control_id")
    conclusions = {}
    for left_product, right_product in zip(products, products[1:]):
        for left, right in zip(left_product.summaries, right_product.summaries, strict=True):
            actual = tuple(row.configuration if row.condition_reuse is None else row.condition_reuse.observed_configuration for row in (left, right))
            key = tuple(ss.identity(row, "config_id") for row in actual)
            if key in conclusions:
                continue
            ordinal = len(conclusions)
            # Identified unavailable original controls are exposed operands here;
            # no test signer or synthetic record establishes real qualification.
            conclusions[key] = census.FullStateConclusion("conclusion.exposed." + str(ordinal),
                ObjectIdentity("assessment.exposed." + str(ordinal), "empirical-lawhood/battery-segmented/full-state-stream-assessment", "1.0.0", "a" * 64),
                control, key, (left.trace, right.trace), tuple(ObjectIdentity("evidence.exposed." + str(i) + "." + str(ordinal),
                    "empirical-lawhood/battery-segmented/native-evidence", "1.0.0", "b" * 64) for i in range(2)),
                (0, 0), (0, 0), (None, None), (0, 0), 0, tuple((name, 0) for name in sorted(row.value for row in A)),
                (0, 0, 0, 0), (), A.UNEVALUABLE, ("actual-full-state-clock-domain-unavailable",))
    return receiver, tuple(conclusions.values())


def test_complete_census_keeps108_96_12_and_refuses_supplier_promotion(complete_negative):
    receiver, conclusions = complete_negative
    result = census.join_complete_full_state(receiver, reversed(conclusions))
    assert len(result.conclusions) == 96 and len(result.selected_uses) == 108
    assert sum(bool(row.equal_condition_derivations) for row in result.selected_uses) == 12
    assert result.disposition is A.UNEVALUABLE and result.selected_model is None and result.fresh_physical_units == 0
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    with pytest.raises(ValueError, match="omits outcomes"):
        replace(result, selected_model="dfn-primary")
    with pytest.raises(ValueError, match="complete independently recomputed"):
        sq.require_fidelity_supplier(result)
    with pytest.raises(ValueError, match="hides an original"):
        replace(result, reason_codes=("unrelated-negative",))
    with pytest.raises(ValueError, match="hides an original"):
        replace(result, disposition=A.FALSIFIED)


@pytest.mark.parametrize("damage", ("omit", "duplicate", "trace", "control"))
def test_complete_census_refuses_unselected_missing_or_substituted_controls(complete_negative, damage):
    receiver, conclusions = complete_negative
    if damage == "omit":
        changed = conclusions[:-1]
    elif damage == "duplicate":
        changed = (*conclusions[:-1], conclusions[0])
    elif damage == "trace":
        changed = (replace(conclusions[0], traces=tuple(reversed(conclusions[0].traces))), *conclusions[1:])
    else:
        changed = (replace(conclusions[0], control=ss.identity(local.FullStateControlProtocol("control.exposed.other"), "control_id")), *conclusions[1:])
    with pytest.raises(ValueError):
        census.join_complete_full_state(receiver, changed)
