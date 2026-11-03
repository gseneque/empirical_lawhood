# SPDX-License-Identifier: MPL-2.0
"""Independent software arithmetic; no original biochemical endpoints are fitted."""

from dataclasses import replace
from decimal import Decimal, localcontext
from math import exp
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.rubisco_prediction import paired_response as p
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


def query(name, group, *features):
    return p.PairedFeatureQueryV1(name, group, tuple(Decimal(str(v)) for v in features))


def point(name, group, response, *features):
    return p.PairedTrainingPointV1(query(name, group, *features), Decimal(str(response)))


def software_descriptors():
    # Deliberately synthetic table values and source identity. These tests
    # neither admit an AAindex source nor attach results to biological units.
    return p.CompositionDescriptorsV1("a" * 64,
        tuple(Decimal(index) for index in range(20)),
        tuple(Decimal(-index) for index in range(20)))


def test_descriptor_arithmetic_is_position_blind_with_explicit_h_zero_charge():
    table = software_descriptors()
    assert p.composition_delta("A", "R", table) == (Decimal(1), Decimal(-1), Decimal(1))
    assert p.composition_delta("HH", "HK", table)[2] == 1
    assert p.composition_delta("KRDEH", "HHHHH", table)[2] == 0
    assert p.composition_delta("AR", "RA", table) == (Decimal(0),) * 3
    assert p.composition_delta("AA", "AR", table) == p.composition_delta("AA", "RA", table)
    # Unequal-length encoded recipes use total composition, not an alignment
    # or a silent length normalization.
    assert p.composition_delta("A", "RR", table) == (Decimal(2), Decimal(-2), Decimal(2))
    with pytest.raises(ValueError, match="standard-amino-acid"):
        p.composition_delta("AX", "AR", table)


def test_descriptor_and_group_arithmetic_is_independent_of_caller_precision():
    volumes = list(software_descriptors().volume_index)
    volumes[:2] = (Decimal("12.345"), Decimal("23.456"))
    table = replace(software_descriptors(), volume_index=tuple(volumes))
    rows = tuple(query(f"row{i}", "large", 1, 0, 0, 0, 0, 0) for i in range(3)) + (
        query("single", "small", 1, 0, 0, 0, 0, 0),)
    with localcontext() as context:
        context.prec = 50
        expected_delta = p.composition_delta("AA", "RR", table)
        expected_weights = p.group_weights(rows)
    with localcontext() as context:
        context.prec = 3
        assert p.composition_delta("AA", "RR", table) == expected_delta
        assert p.group_weights(rows) == expected_weights
    assert expected_delta[0] == Decimal("22.222")


def test_query_roles_refuse_labels_overlap_and_non_decimal_operands_before_fitting():
    row = point("train", "source", 2, 1, 0, 0, 0, 0, 0)
    with pytest.raises(ValueError, match="typed rows"):
        p.fit_response((row,), (row,), "split-ridge", Decimal(1))
    with pytest.raises(ValueError, match="held-group overlap"):
        p.fit_response((row,), (query("other", "source", 1, 0, 0, 0, 0, 0),),
                       "split-ridge", Decimal(1))
    with pytest.raises(ValueError, match="duplicate cases"):
        p.fit_response((row,), (query("train", "external", 1, 0, 0, 0, 0, 0),),
                       "split-ridge", Decimal(1))
    with pytest.raises(TypeError):
        replace(row.query, response=Decimal(1000))
    with pytest.raises(ValueError, match="finite Decimal"):
        query("bad", "external", "NaN", 0, 0, 0, 0, 0)
    with pytest.raises(ValueError, match="finite Decimal"):
        p.PairedFeatureQueryV1("bad", "external", (1,) * 6)


def test_module_import_is_cold_in_a_fresh_process():
    script = """
import importlib.abc, sys
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy', 'scipy', 'rapidfuzz', 'torch', 'transformers', 'esm'}:
            raise AssertionError('numerical import during cold discovery: ' + fullname)
sys.meta_path.insert(0, Refuse())
import empirical_lawhood.adapters.methods.rubisco_prediction.paired_response
"""
    result = subprocess.run([sys.executable, "-B", "-c", script],
                            cwd=Path(__file__).parent.parent, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


@pytest.mark.native("numpy")
def test_hand_computable_group_weighted_through_origin_ridge():
    # Equal group weights produce an identity feature Gram matrix. For the
    # synthetic response3*x+4*y, alpha1 halves the two exact slopes.
    rows = (point("a", "many", 7, 1, 1, 0, 0, 0, 0),
            point("b", "many", -7, -1, -1, 0, 0, 0, 0),
            point("c", "many", 7, 1, 1, 0, 0, 0, 0),
            point("d", "many", -7, -1, -1, 0, 0, 0, 0),
            point("e", "few", -1, 1, -1, 0, 0, 0, 0),
            point("f", "few", 1, -1, 1, 0, 0, 0, 0))
    held = (query("x", "external", 1, 0, 0, 0, 0, 0),
            query("y", "external", 0, 1, 0, 0, 0, 0))
    fit = p.fit_response(rows, held, "split-ridge", Decimal(1))
    assert fit.row_weights == (Decimal("0.125"),) * 4 + (Decimal("0.25"),) * 2
    assert fit.feature_scales == (Decimal(1),) * 6
    assert fit.coefficients == (Decimal("1.5"), Decimal(2), *(Decimal(0),) * 4)
    assert fit.predictions == (Decimal("1.5"), Decimal(2))


@pytest.mark.native("numpy")
def test_rms_retains_constant_nonzero_channel_and_ignores_unlearned_zero_channel():
    rows = (point("train", "source", 4, 2, 0, 0, 0, 0, 0),)
    held = (query("changed", "external", 4, 0, 0, 0, 0, 0),
            query("parent", "external", 0, 0, 0, 0, 0, 0),
            query("uninformed", "external", 0, 0, 0, 10000, 0, 0))
    fit = p.fit_response(rows, held, "split-ridge", Decimal(1))
    # Mean centering would delete the only active channel and fail this check.
    assert fit.feature_scales == (Decimal(2), *(Decimal(1),) * 5)
    assert fit.inactive_columns == (False, True, True, True, True, True)
    assert fit.coefficients == (Decimal(2), *(Decimal(0),) * 5)
    assert fit.predictions == (Decimal(4), Decimal(0), Decimal(0))


@pytest.mark.native("numpy")
def test_pooled_channels_and_separate_subunits_are_distinct_models():
    rows = (point("train", "source", 6, 2, 0, 0, 1, 0, 0),)
    held = (query("ssu", "external", 0, 0, 0, 1, 0, 0),)
    split = p.fit_response(rows, held, "split-ridge", Decimal(1))
    pooled = p.fit_response(rows, held, "pooled-ridge", Decimal(1))
    # Split normalized training features are(1,1), so both slopes are2.
    # Pooled training feature is3: normalized slope3, query feature1/3.
    assert float(split.predictions[0]) == pytest.approx(2, abs=1e-13)
    assert float(pooled.predictions[0]) == pytest.approx(1, abs=1e-13)


@pytest.mark.native("numpy")
@pytest.mark.parametrize("method,invalid", [("split-ridge", "nan"), ("anchored-rbf", "inf")])
def test_nonfinite_solve_refuses_before_zero_parent_roundoff_normalization(monkeypatch, method, invalid):
    import numpy as np

    rows = (point("train", "source", 1, 2, 0, 0, 0, 0, 0),)
    held = (query("parent", "external", 0, 0, 0, 0, 0, 0),)
    monkeypatch.setattr(np.linalg, "solve", lambda matrix, rhs: np.full(rhs.shape, float(invalid)))
    with pytest.raises(ValueError):
        p.fit_response(rows, held, method, Decimal(1), Decimal(1) if method == "anchored-rbf" else None)


@pytest.mark.native("numpy")
def test_anchored_rbf_one_point_matches_independent_exponential_hand_calculation():
    rows = (point("train", "source", 1, 2, 0, 0, 0, 0, 0),)
    held = (query("twice", "external", 4, 0, 0, 0, 0, 0),
            query("parent", "external", 0, 0, 0, 0, 0, 0))
    fit = p.fit_response(rows, held, "anchored-rbf", Decimal(1), Decimal(1))
    # Standardized train/query1/2. Anchored K(1,1)=2-2e^-1;
    # K(2,1)=1-e^-4. No NumPy-derived expected result is used.
    coefficient = 1 / (3 - 2 * exp(-1))
    expected = (1 - exp(-4)) * coefficient
    assert float(fit.coefficients[0]) == pytest.approx(coefficient, abs=1e-13)
    assert float(fit.predictions[0]) == pytest.approx(expected, abs=1e-13)
    assert fit.predictions[1] == Decimal(0)


@pytest.mark.native("numpy")
def test_anchored_rbf_weighted_symmetry_and_source_order_invariance():
    rows = (point("positive", "left", 1, 2, 0, 0, 0, 0, 0),
            point("negative", "right", -1, -2, 0, 0, 0, 0, 0))
    held = (query("plus", "external", 2, 0, 0, 0, 0, 0),
            query("minus", "external", -2, 0, 0, 0, 0, 0))
    forward = p.fit_response(rows, held, "anchored-rbf", Decimal(1), Decimal(1))
    reverse = p.fit_response(tuple(reversed(rows)), held, "anchored-rbf", Decimal(1), Decimal(1))
    # Antisymmetric two-point solution with weight1/2 per group:
    # Kdiag-Koff=1-e^-4; effective ridge penalty is2.
    expected = (1 - exp(-4)) / (3 - exp(-4))
    assert float(forward.predictions[0]) == pytest.approx(expected, abs=1e-13)
    assert float(forward.predictions[1]) == pytest.approx(-expected, abs=1e-13)
    assert tuple(map(float, reverse.predictions)) == pytest.approx(tuple(map(float, forward.predictions)), abs=1e-13)


@pytest.mark.native("numpy")
def test_external_feature_extremes_do_not_change_group_tuning_or_training_scales():
    rows = (point("a", "large", 2, 1, 0, 0, 0, 0, 0),
            point("b", "large", 3, 2, 0, 0, 0, 0, 0),
            point("c", "small", -2, -1, 0, 0, 0, 0, 0))
    first = p.tune_response(rows, (query("external", "held", 3, 0, 0, 0, 0, 0),), "anchored-rbf")
    second = p.tune_response(rows, (query("external", "held", 1000000, 0, 0, 0, 0, 0),), "anchored-rbf")
    assert first.groups == second.groups == ("large", "small")
    assert first.inner_fits == second.inner_fits
    assert first.scores == second.scores
    assert (first.selected_alpha, first.selected_gamma) == (second.selected_alpha, second.selected_gamma)
    assert first.final_fit.feature_scales == second.final_fit.feature_scales
    assert first.final_fit.coefficients == second.final_fit.coefficients
    for fit in first.inner_fits:
        assert not {q.group_id for q in fit.training_queries} & {q.group_id for q in fit.query_rows}
        assert {q.case_id for q in (*fit.training_queries, *fit.query_rows)} == {"a", "b", "c"}
        assert "external" not in {q.case_id for q in (*fit.training_queries, *fit.query_rows)}
    omitted = replace(first.inner_fits[0], query_rows=(first.inner_fits[0].query_rows[0],),
                      predictions=(first.inner_fits[0].predictions[0],))
    with pytest.raises(ValueError, match="whole-group separation"):
        replace(first, inner_fits=(omitted, *first.inner_fits[1:]))


@pytest.mark.native("numpy")
def test_exact_tuning_ties_choose_larger_penalty_and_smaller_gamma():
    rows = (point("a", "left", 0, 1, 0, 0, 0, 0, 0),
            point("b", "right", 0, -1, 0, 0, 0, 0, 0))
    selection = p.tune_response(rows, (query("external", "held", 2, 0, 0, 0, 0, 0),), "anchored-rbf")
    assert selection.scores == (Decimal(0),) * 9
    assert selection.selected_alpha == Decimal(10)
    assert selection.selected_gamma == Decimal("0.1")


@pytest.mark.native("numpy")
def test_fixed_alpha_diagnostic_retains_two_blocks_without_selecting_from_errors():
    rows = (point("a", "large", 4, 2, 0, 0, 0, 0, 0),
            point("b", "large", 4, 2, 0, 0, 0, 0, 0),
            point("c", "small", 4, 2, 0, 0, 0, 0, 0))
    result = p.diagnose_fixed(rows, (query("external", "held", 4, 0, 0, 0, 0, 0),), "split-ridge")
    assert result.groups == ("large", "small")
    assert result.held_mean_absolute_errors == (Decimal(2), Decimal(2))
    assert result.final_fit.row_weights == (Decimal("0.25"), Decimal("0.25"), Decimal("0.5"))
    assert result.final_fit.alpha == 1
    assert result.final_fit.predictions == (Decimal(4),)
    assert all(fit.alpha == 1 for fit in result.inner_fits)
    with pytest.raises(ValueError, match="whole-group source split"):
        replace(result, inner_fits=tuple(reversed(result.inner_fits)))


@pytest.mark.native("numpy")
def test_canonical_closed_roundtrip_preserves_all_fits_and_selected_census():
    rows = (point("a", "left", 1, 1, 0, 0, 0, 0, 0),
            point("b", "right", -1, -1, 0, 0, 0, 0, 0))
    held = (query("external", "held", 3, 0, 0, 0, 0, 0),)
    selection = p.tune_response(rows, held, "anchored-rbf")
    diagnostic = p.diagnose_fixed(rows, held, "split-ridge")
    for record in (software_descriptors(), rows[0], held[0], selection.final_fit, selection, diagnostic):
        encoded = record.canonical_bytes()
        decoded = decode_canonical_bytes(encoded, type(record), maximum_bytes=2 * 1024**2)
        assert decoded == record
        assert decoded.canonical_bytes() == encoded
