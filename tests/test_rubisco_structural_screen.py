# SPDX-License-Identifier: MPL-2.0
"""Independent synthetic arithmetic and exposed-screen boundary checks."""

from dataclasses import replace
from decimal import Decimal, localcontext
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.rubisco_prediction import records as r
from empirical_lawhood.adapters.methods.rubisco_prediction import structural_screen as s
from empirical_lawhood.adapters.physical.rubisco_kinetics import plant_structural_scores as native
from empirical_lawhood.adapters.physical.rubisco_kinetics.mcdonald2026 import (
    PlantContextV1, PlantProteinRecipeV1, PlantQuantityV1,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.workbook import NativeWorkbookCellV1


def query(name, site, *features):
    return s.RidgeQueryV1(name, site, tuple(Decimal(str(v)) for v in features))


def training(name, site, response, *features):
    return s.RidgeTrainingPointV1(query(name, site, *features), Decimal(str(response)))


def synthetic_queries():
    return tuple(query(s.case_id(edit), int(edit[1:-1]), index + 1, int(edit[1:-1]) / 100)
                 for index, edit in enumerate(s.EDITS))


def test_module_import_is_cold_in_a_fresh_process():
    script = """
import importlib.abc, sys
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy', 'scipy', 'rapidfuzz', 'torch', 'transformers', 'esm'}:
            raise AssertionError('numerical import during cold discovery: ' + fullname)
sys.meta_path.insert(0, Refuse())
import empirical_lawhood.adapters.methods.rubisco_prediction.structural_screen
"""
    result = subprocess.run([sys.executable, "-B", "-c", script], cwd=Path(__file__).parent.parent,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


@pytest.mark.native("numpy")
def test_hand_computable_weighted_three_parameter_ridge():
    # Four rows at site1, two at site2. Site weighting gives orthogonal
    # standardized features, each variance1, and intercept2. At alpha1 the
    # exact slopes3/4 shrink to1.5/2. Pooled row weighting would not do this.
    rows = (training("a", 1, -5, -1, -1), training("b", 1, 9, 1, 1),
            training("c", 1, -5, -1, -1), training("d", 1, 9, 1, 1),
            training("e", 2, 3, -1, 1), training("f", 2, 1, 1, -1))
    held = (query("g", 3, 1, 0), query("h", 4, 0, 1))
    fit = s.fit_ridge(rows, held, Decimal(1))
    assert fit.row_weights == (Decimal("0.125"),) * 4 + (Decimal("0.25"),) * 2
    assert fit.feature_means == (Decimal(0), Decimal(0))
    assert fit.feature_scales == (Decimal(1), Decimal(1))
    assert fit.intercept == Decimal(2)
    assert fit.coefficients == (Decimal("1.5"), Decimal(2))
    assert fit.predictions == (Decimal("3.5"), Decimal(4))


@pytest.mark.native("numpy")
def test_query_extremes_do_not_change_training_scalers_or_coefficients():
    rows = (training("a", 1, -1, 10), training("b", 2, 1, 30))
    ordinary = s.fit_ridge(rows, (query("c", 3, 20),), Decimal(1))
    extreme = s.fit_ridge(rows, (query("c", 3, 1000000),), Decimal(1))
    assert ordinary.feature_means == extreme.feature_means == (Decimal(20),)
    assert ordinary.feature_scales == extreme.feature_scales == (Decimal(10),)
    assert ordinary.coefficients == extreme.coefficients == (Decimal("0.5"),)
    assert ordinary.intercept == extreme.intercept == 0
    assert ordinary.predictions == (Decimal(0),)
    assert extreme.predictions == (Decimal(49999),)


@pytest.mark.native("numpy")
def test_held_site_labels_cannot_change_that_outer_fit_or_inner_selection():
    queries = synthetic_queries()
    responses = tuple(Decimal(index % 3) for index in range(9))
    first = s._crossfit_family(queries, responses, "if-conservation", "KCAT_C")
    altered = tuple(Decimal(99999) if q.site == 391 else y
                    for q, y in zip(queries, responses, strict=True))
    second = s._crossfit_family(queries, altered, "if-conservation", "KCAT_C")
    fold = next(f for f in first if f.held_site == 391)
    assert fold == next(f for f in second if f.held_site == 391)
    assert tuple(q.case_id for q in fold.outer_fit.query_rows) == tuple(s.case_id(e) for e in s.EDITS[1:4])
    inner = next(f for f in fold.inner_fits if f.alpha == Decimal(1) and f.query_rows[0].site == 468)
    # With 391 and 468 absent, four singleton sites remain, cases1/5/6/9.
    assert inner.feature_means[0] == Decimal("5.25")
    assert len(inner.training_queries) == 4
    for candidate in fold.inner_fits:
        assert len({q.site for q in candidate.training_queries}) == 4
        assert not {q.site for q in candidate.training_queries} & {q.site for q in candidate.query_rows}
        assert 391 not in {q.site for q in (*candidate.training_queries, *candidate.query_rows)}


@pytest.mark.native("numpy")
def test_constant_response_is_intercept_only_and_larger_alpha_wins_ties():
    folds = s._crossfit_family(synthetic_queries(), (Decimal(1),) * 9, "if-conservation", "KCAT_C")
    assert all(f.selected_alpha == Decimal(10) and f.alpha_scores == (Decimal(0),) * 3 for f in folds)
    for fold in folds:
        assert fold.outer_fit.intercept == 1
        assert fold.outer_fit.coefficients == (Decimal(0), Decimal(0))
        assert fold.outer_fit.predictions == (Decimal(1),) * len(fold.outer_fit.query_rows)


@pytest.mark.native("numpy")
@pytest.mark.parametrize("invalid", ["nan", "inf"])
def test_nonfinite_solver_result_refuses_before_constant_response_normalization(monkeypatch, invalid):
    import numpy as np

    rows = (training("a", 1, 1, -1), training("b", 2, 1, 1))
    monkeypatch.setattr(np.linalg, "solve", lambda matrix, rhs: np.full(rhs.shape, float(invalid)))
    with pytest.raises(ValueError, match="nonfinite solve"):
        s.fit_ridge(rows, (query("c", 3, 0),), Decimal(1))


@pytest.mark.native("numpy")
def test_constant_training_feature_cannot_create_a_held_feature_response():
    rows = (training("a", 1, -2, 7), training("b", 2, 2, 7))
    fit = s.fit_ridge(rows, (query("c", 3, 7000),), Decimal("0.1"))
    assert fit.constant_columns == (True,)
    assert fit.feature_means == (Decimal(7),)
    assert fit.coefficients == (Decimal(0),)
    assert fit.predictions == (Decimal(0),)


def test_query_role_overlap_nonfinite_and_alpha_spoofs_refuse_before_numpy(monkeypatch):
    rows = (training("a", 1, -1, -1), training("b", 2, 1, 1))
    with pytest.raises(ValueError, match="held-site"):
        s.fit_ridge(rows, (query("c", 1, 0),), Decimal(1))
    with pytest.raises(ValueError, match="immutable typed census"):
        s.fit_ridge(rows, (rows[0],), Decimal(1))
    for alpha in (1, 1.0, True, Decimal("NaN")):
        with pytest.raises(ValueError, match="finite Decimal"):
            s.fit_ridge(rows, (query("c", 3, 0),), alpha)
    with pytest.raises(ValueError, match="finite Decimal"):
        query("c", 3, "Infinity")


def cell(address, token):
    return NativeWorkbookCellV1(address, "n", token, token, None, (("r", address),), ())


def quantity(kind, value, group):
    unit = {"KCAT_C": "s^-1", "SPECIFICITY_CO": "dimensionless", "KC_AIR": "micromolar",
            "CARBOXYLATION_EFFICIENCY_AIR": "mM^-1 s^-1"}[kind]
    role = "SOURCE_REPORTED_DERIVED_RATIO" if kind == "CARBOXYLATION_EFFICIENCY_AIR" else "SOURCE_REPORTED_MEASURED"
    return PlantQuantityV1(kind, unit, role, group, cell("U3", str(value)), cell("V3", "1"), cell("W3", "1"),
                           cell("T3", "1"), None, None, Decimal(value), Decimal(1), 1, (), None, None,
                           ("REPORTED_N_DIFFERS_FROM_LISTED_RAW_COUNT",))


def software_sources(monkeypatch, *, changed=True):
    # Source-shaped, truth-known SOFTWARE inputs with explicitly substituted
    # native pins. No original kinetic labels are fitted in these tests.
    protein = list("M" + "A" * 476)
    for site, residue in ((251, "I"), (391, "T"), (465, "I"), (468, "N")):
        protein[site - 1] = residue
    parent_lsu, ssu = "".join(protein), "M" + "A" * 122
    monkeypatch.setattr(r, "PARENT_LSU_SHA256", sha256(parent_lsu.encode()).hexdigest())
    monkeypatch.setattr(r, "PARENT_SSU_SHA256", sha256(ssu.encode()).hexdigest())
    monkeypatch.setattr(r, "PLANT_PANEL_FINGERPRINT", "e" * 64)
    contexts = {}
    for index, edit in enumerate((None, *r.EDITS)):
        mutant = parent_lsu if edit is None else parent_lsu[:int(edit[1:-1]) - 1] + edit[-1] + parent_lsu[int(edit[1:-1]):]
        recipe = PlantProteinRecipeV1("NtRbcL" + (f" {edit}" if edit else ""), parent_lsu, ssu, edit, mutant)
        factor = Decimal(1000) if edit == "A369V" else Decimal(2) if changed and edit is not None else Decimal(1)
        values = (Decimal(50) * factor, Decimal(2) * factor, Decimal(20), Decimal(100))
        kinds = ("SPECIFICITY_CO", "KCAT_C", "KC_AIR", "CARBOXYLATION_EFFICIENCY_AIR")
        contexts[edit] = PlantContextV1(cell("P3", str(index + 1)), cell("A3", recipe.native_name),
            tuple(quantity(kind, value, str(index + 1)) for kind, value in zip(kinds, values, strict=True)),
            recipe, None, "BACTERIAL_RECOMBINANT_SOURCE_REPORTED")
    monkeypatch.setattr(r, "PLANT_CONTEXT_FINGERPRINTS", {edit: c.fingerprint() for edit, c in contexts.items()})
    for owner in (native, s):
        monkeypatch.setattr(owner, "S1_SHA256", "a" * 64)
    monkeypatch.setattr(native, "STRUCTURAL_SHA256", "b" * 64)
    monkeypatch.setattr(native, "CONSERVATION_SHA256", "c" * 64)
    witnesses, rows = {}, []
    for index, edit in enumerate(s.EDITS):
        site = int(edit[1:-1])
        features = (Decimal(index + 1), Decimal(10 * (s.SITES.index(site) + 1)))
        cells = (cell("A1", edit), cell("B1", str(features[0])), cell("A2", str(site)),
                 cell("B2", edit[0]), cell("C2", str(features[1])))
        witnesses[edit] = sha256(b"".join(c.canonical_bytes() for c in cells)).hexdigest()
        rows.append((edit, site, *features, cells))
    monkeypatch.setattr(native, "WITNESSES", witnesses)
    scores = tuple(native.PlantStructuralScoreRowV1(*args, source_sha256="a" * 64,
                   structural_member_sha256="b" * 64, conservation_member_sha256="c" * 64) for args in rows)
    payload = (Path(__file__).parent.parent / "programmes/biology/photosynthesis/records/plant-structural-screen-protocol-v1.md").read_bytes()
    assert sha256(payload).hexdigest() == s.PROTOCOL_SHA256
    return scores, contexts[None], tuple(contexts[edit] for edit in r.EDITS), payload


@pytest.mark.native("numpy")
@pytest.mark.parametrize("changed", [False, True])
def test_complete_screen_no_change_and_intercept_only_controls(monkeypatch, changed):
    scores, parent, labels, payload = software_sources(monkeypatch, changed=changed)
    forecasts = s.crossfit_structural_scores(scores, parent, labels, protocol_payload=payload)
    assert len(forecasts.points) == 90 and len(forecasts.folds) == 36
    assert sum(len(f.inner_fits) + 1 for f in forecasts.folds) == 576
    assert len(forecasts.canonical_bytes()) < 128 * 1024**2
    assert forecasts.diagnostic_status == s.DIAGNOSTIC_STATUS
    assert all(f.selected_alpha == Decimal(10) for f in forecasts.folds)
    assert all(f.outer_fit.coefficients == (Decimal(0),) * len(f.outer_fit.coefficients) for f in forecasts.folds)
    # Once forecasts exist, evaluation cannot invoke any fitter.
    def refuse(*args, **kwargs):
        raise AssertionError("evaluation/refusal invoked a fitter")
    monkeypatch.setattr(s, "fit_ridge", refuse)
    # Keep all native source identities/witnesses and fitted numeric values.
    # Spoof only a retained query or omit one allele while keeping its site's
    # other alleles, so site-set checks alone would incorrectly admit it.
    first = forecasts.folds[0]
    outer = first.outer_fit
    altered_query = replace(outer.training_queries[0], features=(Decimal(999), *outer.training_queries[0].features[1:]))
    altered_outer = replace(outer, training_queries=(altered_query, *outer.training_queries[1:]))
    with pytest.raises(ValueError, match="outer queries.*native feature/case roster"):
        replace(forecasts, folds=(replace(first, outer_fit=altered_outer), *forecasts.folds[1:]))
    omitted_outer = replace(outer, training_queries=outer.training_queries[1:], row_weights=outer.row_weights[1:])
    with pytest.raises(ValueError, match="outer queries.*native feature/case roster"):
        replace(forecasts, folds=(replace(first, outer_fit=omitted_outer), *forecasts.folds[1:]))
    inner = first.inner_fits[0]
    altered_inner_query = replace(inner.query_rows[0], features=(Decimal(999), *inner.query_rows[0].features[1:]))
    altered_inner = replace(inner, query_rows=(altered_inner_query, *inner.query_rows[1:]))
    altered_fold = replace(first, inner_fits=(altered_inner, *first.inner_fits[1:]))
    with pytest.raises(ValueError, match="inner queries.*native feature/case roster"):
        replace(forecasts, folds=(altered_fold, *forecasts.folds[1:]))
    evaluated = s.evaluate_structural_screen(forecasts, parent, labels)
    assert len(evaluated.points) == 90 and len(evaluated.pair_orders) == 40
    assert evaluated.primary_endpoint_passes == (False, False)
    assert evaluated.primary_has_same_site_discrimination == (False, False)
    assert all(p.predicted_order == p.observed_order == 0 for p in evaluated.pair_orders)
    assert all("369" not in e.forecast.edit for e in evaluated.points)
    baseline = tuple(v for v in evaluated.summaries if v.method == "training-mean")
    # The 50-digit Decimal mean may round a repeated ln(2) at its last place.
    assert all(v.mean_absolute_log_error < Decimal("1e-48") for v in baseline)
    if not changed:
        assert all(e.absolute_error == e.absolute_log_error == 0 for e in evaluated.points)
    else:
        assert all(e.absolute_log_error > 0 for e in evaluated.points if e.forecast.method == "parent")
    for update in ({"points": evaluated.points[:-1]}, {"pair_orders": evaluated.pair_orders[:-1]},
                   {"primary_endpoint_passes": (True, True)}, {"primary_has_same_site_discrimination": (True, True)}):
        with pytest.raises(ValueError):
            replace(evaluated, **update)
    fake_summary = replace(evaluated.summaries[0], mean_absolute_log_error=Decimal(99))
    with pytest.raises(ValueError, match="summary arithmetic"):
        replace(evaluated, summaries=(fake_summary, *evaluated.summaries[1:]))
    fake_order = replace(evaluated.pair_orders[0], predicted_order=1)
    with pytest.raises(ValueError, match="pair arithmetic"):
        replace(evaluated, pair_orders=(fake_order, *evaluated.pair_orders[1:]))
    with pytest.raises(ValueError, match="frozen protocol"):
        s.crossfit_structural_scores(scores, parent, labels, protocol_payload=b"changed")
    with pytest.raises(ValueError, match="score source/roster"):
        s.crossfit_structural_scores(tuple(reversed(scores)), parent, labels, protocol_payload=payload)
    with pytest.raises(ValueError, match="focal/diagnostic census"):
        s.crossfit_structural_scores(scores, parent, tuple(reversed(labels)), protocol_payload=payload)


@pytest.mark.native("numpy")
def test_feature_sensitive_truth_known_same_site_ordering():
    queries = synthetic_queries()
    responses = tuple(Decimal(2) * q.features[0] for q in queries)
    folds = s._crossfit_family(queries, responses, "if-conservation", "KCAT_C")
    held = next(f for f in folds if f.held_site == 391)
    assert held.outer_fit.predictions[0] < held.outer_fit.predictions[1] < held.outer_fit.predictions[2]
    with localcontext(r.NUMERICAL_CONTEXT):
        other_site_means = tuple(r.mean(tuple(y for q, y in zip(queries, responses, strict=True) if q.site == site))
                                  for site in s.SITES if site != 391)
        mean = r.mean(other_site_means)
    assert len(set(held.outer_fit.predictions)) == 3
    assert all(value != mean for value in held.outer_fit.predictions)
