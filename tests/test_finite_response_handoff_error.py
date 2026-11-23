"""Post-reveal arithmetic and masks on exposed software fixtures."""

from dataclasses import replace
from decimal import Decimal, localcontext

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.finite_response_law.handoff_error import (
    _error_rows, _signed_differences, revealed_handoff_errors,
)
from empirical_lawhood.domains.matrix.finite_response_law.evaluation_panel import evaluation_panel
from empirical_lawhood.domains.matrix.finite_response_law.law_payloads import FiniteResponseLawResponseChart
from empirical_lawhood.domains.matrix.finite_response_law.paired_assay import positive_pair_readouts
from tests.finite_response_custody_fixtures import synthetic_native
from tests.test_finite_response_assigned_method_records import _source


def test_prospective_panel_binds_issued_units_and_assigned_parents():
    source = _source("prospective-evaluation")
    panel = evaluation_panel(synthetic_native(source))
    assert panel.assigned_source == source
    assert panel.root_ids == tuple(root.stage_unit for root in source.roots)
    assert np.all(panel.response_valid) and np.all(panel.use_valid)
    assert np.all(panel.y[:, 0, 0] == .08)
    assert np.all(panel.y[:, 0, 1] == 0)
    with pytest.raises(ValueError, match="assigned census"):
        replace(panel, root_ids=panel.root_ids[::-1])
    with pytest.raises(ValueError, match="assigned preparation"):
        replace(panel, parent_indices=(panel.parent_indices + 1) % 5)
    with pytest.raises(ValueError, match="assigned census"):
        replace(panel, assigned_source=None)


def test_each_native_quantity_uses_its_own_delivery_and_missingness_mask():
    primary, refined = synthetic_native().views[:2]
    primary = replace(primary, words=tuple(
        replace(w, complete=False) if w.invocation.word.sign == 0 and w.invocation.purpose == "future-1" else w
        for w in primary.words
    ))
    refined = replace(refined, words=tuple(
        replace(w, maximum_force_error=Decimal("0.01"))
        if (w.invocation.purpose, w.invocation.word.magnitude, w.invocation.word.direction_index, w.invocation.word.sign)
        == ("future-2", 16, 1, -1) else w
        for w in refined.words
    ))
    chart = FiniteResponseLawResponseChart()
    observed = tuple(Decimal(i) for i in range(32))
    forecast = tuple(v - Decimal("0.25") for v in observed)
    rows = _error_rows(positive_pair_readouts((primary, refined), parent=primary.root.assigned_parent),
                       chart, forecast, observed)
    assert len(rows) == 128
    keys = [(r["magnitude"], r["direction_index"], r["purpose"], r["refinement"], r["quantity"]) for r in rows]
    assert len(set(keys)) == 128
    for row in rows:
        coordinate = chart.output_ids.index(row["quantity"])
        pair = 2 * (row["magnitude"] == 16) + row["direction_index"]
        assert row["observed_handoff_prediction"] == observed[8 * pair + coordinate]
        assert row["unit"] == chart.output_units[coordinate]
        hold_failed = row["refinement"] == 1 and row["purpose"] == "future-1"
        signed_failed = (row["refinement"], row["purpose"], pair) == (2, "future-2", 3)
        expected_valid = not signed_failed and (coordinate < 2 or not hold_failed)
        assert row["native_measurement"] is not None
        assert row["use_valid"] == (not hold_failed and not signed_failed)
        assert row["native_scoreable"] == expected_valid
        assert row["handoff_error"] == Decimal("-0.25")
        if expected_valid:
            assert row["downstream_error"] == row["observed_handoff_prediction"] - row["native_measurement"]
            assert row["total_error"] == row["handoff_error"] + row["downstream_error"]
        else:
            assert (row["downstream_error"], row["total_error"]) == (None, None)


def test_differences_preserve_small_signed_terms_and_each_available_contrast():
    low, high, native = Decimal("1e-54"), Decimal("1e24"), Decimal("5.3e-38")
    with localcontext() as ambient:
        ambient.prec = 5
        calculated = _signed_differences(low, high, native)
    with localcontext() as reference:
        reference.prec = 90
        assert calculated == (low - high, high - native, low - native)
        assert calculated[0] + calculated[1] == calculated[2]
        assert _signed_differences(None, high, native) == (None, high - native, None)
        assert _signed_differences(low, None, native) == (None, None, low - native)
        assert _signed_differences(low, high, None) == (low - high, None, None)
    with pytest.raises(TypeError, match="sealed and revealed"):
        revealed_handoff_errors(sealed=None, revealed=None, views=(), qualification=None, lower=None)
