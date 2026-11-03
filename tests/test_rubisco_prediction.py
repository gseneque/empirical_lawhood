# SPDX-License-Identifier: MPL-2.0
"""Truth-known software source fixtures, exact KNN ties and label isolation."""

from dataclasses import replace
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.rubisco_prediction import knn as k
from empirical_lawhood.adapters.methods.rubisco_prediction import records as r
from empirical_lawhood.adapters.physical.rubisco_kinetics import iqbal2023 as source
from empirical_lawhood.adapters.physical.rubisco_kinetics.mcdonald2026 import (
    PlantContextV1, PlantProteinRecipeV1, PlantQuantityV1,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.workbook import (
    NativeArchiveMemberV1, NativeSheetCatalogEntryV1, NativeWorkbookCellV1, NativeWorkbookV1,
    NativeWorksheetV1, SelectedWorkbookMemberV1,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


def cell(address, token):
    # This is a native-profile-shaped software cell, not copied assay evidence.
    return NativeWorkbookCellV1(address, "n", token, token, None, (("r", address),), ())


def software_parent():
    protein = list("M" + "A" * 476)
    for site, residue in ((251, "I"), (391, "T"), (465, "I"), (468, "N")):
        protein[site - 1] = residue
    return "".join(protein), "M" + "A" * 122


def software_natural(monkeypatch, *, nonconstant=False):
    cells = []
    for index in range(183):
        row = index + 2
        # Exactly 132 sequence identities and 86 source genera. All means are
        # constant, so independent arithmetic establishes zero CV error for all
        # k and the required smaller-k selection. Missingness differs by target.
        tail = "".join("C" if (index % 132) & (1 << bit) else "A" for bit in range(8))
        sequence = "M" + "A" * 413 + tail
        turnover = "2"
        if nonconstant:
            letters = list(software_parent()[0])
            for bit in range(7):
                letters[10 + bit] = tail[bit]
            letters[250] = "L" if tail[7] == "C" else "I"
            sequence = "".join(letters)
            turnover = "4" if letters[250] == "L" else "2"
        tokens = (f"Genus{index % 86} species{index}", "software", "software", "software",
                  None if index < 18 else turnover, "1", None if 15 <= index < 28 else "100", "1",
                  None if 15 <= index < 28 else "20", "1", str(len(sequence)), "software", "2000", sequence)
        cells.extend(cell(f"{column}{row}", token) for column, token in zip("ABCDEFGHIJKLMN", tokens, strict=True))
    entry = NativeSheetCatalogEntryV1("Sheet1", "1", "rId1", "xl/worksheets/sheet1.xml")
    sheet = NativeWorksheetV1(entry, "a" * 64, tuple(range(2, 185)), tuple(cells), ())
    book = NativeWorkbookV1("b" * 64, 100, (NativeArchiveMemberV1(0, entry.member, 1, 1, "00000000", 0, 0, 0),),
                           (SelectedWorkbookMemberV1(entry.member, sheet.member_sha256, 1),), (entry,), (), (sheet,))
    monkeypatch.setattr(source, "ARTICLE_SHA256", "c" * 64)
    monkeypatch.setattr(source, "WORKBOOK_SHA256", book.source_sha256)
    monkeypatch.setattr(source, "WORKBOOK_FINGERPRINT", book.fingerprint())
    # Genuine native constructors run, with explicitly substituted software
    # source pins. No decoder, source constructor or authority is bypassed.
    table = source.IqbalTrainingTableV1(source.ARTICLE_SHA256, book, source._rows(book))
    monkeypatch.setattr(r, "IQBAL_TABLE_FINGERPRINT", table.fingerprint())
    return k.prepare_training(table)


def quantity(kind, value, group):
    unit = {"KCAT_C": "s^-1", "SPECIFICITY_CO": "dimensionless", "KC_AIR": "micromolar",
            "CARBOXYLATION_EFFICIENCY_AIR": "mM^-1 s^-1"}[kind]
    role = "SOURCE_REPORTED_DERIVED_RATIO" if kind == "CARBOXYLATION_EFFICIENCY_AIR" else "SOURCE_REPORTED_MEASURED"
    return PlantQuantityV1(kind, unit, role, group, cell("U3", str(value)), cell("V3", "1"), cell("W3", "1"),
                           cell("T3", "1"), None, None, Decimal(value), Decimal(1), 1, (), None, None,
                           ("REPORTED_N_DIFFERS_FROM_LISTED_RAW_COUNT",))


def software_plant(monkeypatch):
    parent, ssu = software_parent()
    monkeypatch.setattr(r, "PARENT_LSU_SHA256", sha256(parent.encode()).hexdigest())
    monkeypatch.setattr(r, "PARENT_SSU_SHA256", sha256(ssu.encode()).hexdigest())
    contexts = {}
    for index, edit in enumerate((None, *r.EDITS)):
        mutant = parent if edit is None else parent[:int(edit[1:-1]) - 1] + edit[-1] + parent[int(edit[1:-1]):]
        recipe = PlantProteinRecipeV1("NtRbcL" + (f" {edit}" if edit else ""), parent, ssu, edit, mutant)
        # Truth-known point labels: focal errors are 1..9, while reversion has
        # very large error and must never enter either focal summary.
        turnover = "3" if edit is None else "1000" if edit == "A369V" else str(3 + index)
        specificity = "80" if edit is None else str(80 + index)
        values = (specificity, turnover, "20", "100")
        kinds = ("SPECIFICITY_CO", "KCAT_C", "KC_AIR", "CARBOXYLATION_EFFICIENCY_AIR")
        contexts[edit] = PlantContextV1(cell("P3", str(index + 1)), cell("A3", recipe.native_name),
            tuple(quantity(kind, value, str(index + 1)) for kind, value in zip(kinds, values, strict=True)),
            recipe, None, "BACTERIAL_RECOMBINANT_SOURCE_REPORTED")
    monkeypatch.setattr(r, "PLANT_CONTEXT_FINGERPRINTS", {edit: context.fingerprint() for edit, context in contexts.items()})
    queries = r.PlantQueriesV1(r.PREFIX + ".queries", r.plant_identity(), r.PROTOCOL_SHA256,
                              tuple(r.PlantQueryV1(r.context_identity(edit), contexts[edit].protein_recipe) for edit in r.EDITS))
    anchors = r.PlantParentAnchorsV1(r.PREFIX + ".anchors", r.plant_identity(), r.PROTOCOL_SHA256, contexts[None])
    labels = r.PlantLabelsV1(r.PREFIX + ".labels", r.plant_identity(), r.PROTOCOL_SHA256,
                           tuple(r.PlantLabelV1(contexts[edit]) for edit in r.EDITS))
    return queries, anchors, labels


@pytest.fixture
def roles(monkeypatch):
    return software_natural(monkeypatch), software_plant(monkeypatch)


@pytest.fixture
def result(roles):
    training, (queries, anchors, labels) = roles
    model = k.fit(training)
    forecasts = k.predict(model, queries, anchors)
    commitment = k.commit(forecasts)
    return model, commitment, labels


def test_decimal_anchoring_is_independent_of_caller_context_and_refuses_invalid_means():
    expected = r.forecast_values(Decimal("3.5"), Decimal("9"), Decimal("6"))
    assert expected[0] == Decimal("5.25")
    assert float(expected[1]) == pytest.approx(math.log(1.5))
    with localcontext() as context:
        context.prec, context.rounding = 3, ROUND_DOWN
        assert r.forecast_values(Decimal("3.5"), Decimal("9"), Decimal("6")) == expected
        assert r.mean((Decimal("1.11"), Decimal("2.22"), Decimal("3.33"))) == Decimal("2.22")
    for invalid in (Decimal(0), Decimal(-1), Decimal("NaN"), Decimal("Infinity")):
        with pytest.raises(ValueError):
            r.forecast_values(Decimal(3), Decimal(2), invalid)


def test_cold_public_import_never_imports_optional_distance_library():
    script = """
import importlib.abc, sys
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'rapidfuzz' or fullname.startswith('rapidfuzz.'):
            raise AssertionError('optional numerical import during discovery')
sys.meta_path.insert(0, Refuse())
import empirical_lawhood.adapters.methods.rubisco_prediction
import empirical_lawhood.adapters.methods.rubisco_prediction.records
assert 'rapidfuzz' not in sys.modules
"""
    completed = subprocess.run([sys.executable, "-c", script], cwd=Path(__file__).parent.parent,
                               capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr


def test_source_training_census_projection_and_label_injection_refuse(roles):
    training, (queries, anchors, labels) = roles
    assert len(training.rows) == 183
    for invalid in (labels, queries, anchors):
        with pytest.raises(ValueError, match="only typed natural training"):
            k.fit(invalid)
    with pytest.raises(ValueError, match="bounded immutable typed roster"):
        replace(training, rows=training.rows[:-1])
    with pytest.raises(ValueError, match="complete 183-row census"):
        replace(training, rows=tuple(reversed(training.rows)))
    row = training.rows[30].native
    native_cells = tuple(replace(c, token="20", xml_v_token="20") if c.address == f"E{row.native_row}" else c for c in row.cells)
    coherent = replace(row, cells=native_cells, turnover_s_inv=Decimal(20))
    projection = r.NaturalTrainingRowV1(coherent)
    with pytest.raises(ValueError, match="sealed native source-row projection"):
        replace(training, rows=tuple(projection if x.native.native_row == row.native_row else x for x in training.rows))
    document = json.loads(queries.canonical_bytes())
    document["value"]["labels"] = labels.to_document()
    with pytest.raises(ValueError):
        decode_canonical_bytes(json.dumps(document).encode(), r.PlantQueriesV1, maximum_bytes=1024**2)


def test_full_boundary_tie_has_row_weights_and_is_source_order_independent(roles):
    training, _ = roles
    originals = training.rows[30:35]
    modified = []
    for row, point in zip(originals, ("1", "3", "5", "7", "100"), strict=True):
        native = row.native
        cells = tuple(replace(c, token=point, xml_v_token=point) if c.address == f"E{native.native_row}" else c for c in native.cells)
        modified.append(r.NaturalTrainingRowV1(replace(native, cells=cells, turnover_s_inv=Decimal(point))))
    rows = {row.row_id: row for row in modified}
    distances = tuple(r.SequenceDistanceV1(row.row_id, distance) for row, distance in zip(modified, (0, 1, 1, 1, 2), strict=True))
    point = k._neighbour_mean(distances, rows, "KCAT_C", 3)
    assert len(point.neighbours) == 4 and point.boundary_distance == 1
    assert point.mean == Decimal(4)  # (1 + 3 + 5 + 7)/4, not a three-row truncation
    with pytest.raises(ValueError, match="complete distance tie"):
        r.check_neighbour_mean(replace(point, neighbours=point.neighbours[:3], mean=Decimal(3)), distances, rows, "KCAT_C")
    assert k._neighbour_mean(distances, dict(reversed(tuple(rows.items()))), "KCAT_C", 3) == point
    hamming = lambda a, b: sum(x != y for x, y in zip(a, b, strict=True))
    assert k._distances(modified[0].sequence, tuple(modified), hamming) == k._distances(
        modified[0].sequence, tuple(reversed(modified)), hamming)
    # Duplicate sequence associations are retained as separate source rows.
    assert len(rows) == 5


def test_genus_score_is_equal_genus_weight_not_pooled_row_weight():
    a = r.GenusErrorV1("Alpha", ("row-a",), Decimal(6))
    b = r.GenusErrorV1("Beta", ("row-b", "row-c", "row-d"), Decimal(2))
    assert r.KSelectionV1(1, (a, b), Decimal(4)).mean_genus_absolute_error == Decimal(4)
    with pytest.raises(ValueError, match="equal-genus weighting"):
        r.KSelectionV1(1, (a, b), Decimal(3))  # pooled (6 + 2 + 2 + 2)/4


@pytest.mark.native("rapidfuzz")
def test_maintained_distance_matches_independent_dynamic_programming():
    def reference(a, b):
        previous = list(range(len(b) + 1))
        for index, letter in enumerate(a, 1):
            current = [index]
            for column, other in enumerate(b, 1):
                current.append(min(current[-1] + 1, previous[column] + 1, previous[column - 1] + (letter != other)))
            previous = current
        return previous[-1]
    for a, b in (("", "M"), ("ACD", "AD"), ("ACD", "AEC"), ("ACDEFG", "CDEFGH"), ("M" * 422, "M" * 485)):
        assert k._levenshtein(a, b) == reference(a, b)


@pytest.mark.native("rapidfuzz")
def test_source_only_six_k_tuning_preserves_genera_missingness_and_exact_ties(result):
    model, _, _ = result
    assert tuple(f.endpoint for f in model.endpoint_fits) == r.ENDPOINTS
    for fit, count in zip(model.endpoint_fits, (165, 170), strict=True):
        assert len(fit.eligible_row_ids) == len(fit.cross_validation) == count
        assert tuple(candidate.k for candidate in fit.tuning) == (1, 3, 5, 9, 15, 31)
        assert fit.chosen_k == 1 and all(candidate.mean_genus_absolute_error == 0 for candidate in fit.tuning)
        rows = {row.row_id: row for row in model.training.rows}
        for query in fit.cross_validation:
            assert query.row_id not in {distance.row_id for distance in query.distances}
            assert all(rows[item.row_id].genus != query.held_genus for item in query.distances)
            assert len(query.predictions) == 6 and query.absolute_errors == (Decimal(0),) * 6
            for point in query.predictions:
                assert point.neighbours == tuple(d for d in query.distances if d.distance <= point.boundary_distance)


@pytest.mark.native("rapidfuzz")
def test_all_forecasts_degeneracy_independent_metrics_and_diagnostic_exclusion(result):
    model, commitment, labels = result
    forecasts = commitment.forecasts
    assert len(forecasts.forecasts) == 60 and len(forecasts.model_points) == 22
    assert len({p.case_id for p in forecasts.forecasts}) == 10
    for point in forecasts.forecasts:
        assert point.anchored_value == (Decimal(3) if point.endpoint == "KCAT_C" else Decimal(80))
        assert point.predicted_log_contrast == 0
        if point.method != "parent":
            assert point.same_model_value and point.same_sequence is False
    report = k.evaluate(commitment, labels)
    assert len(report.errors) == 60 and len(report.summaries) == 12
    for summary in report.summaries:
        assert summary.mean_absolute_error == (Decimal(5) if summary.weighting == "NINE_ROWS" else Decimal("5.25"))
        if summary.endpoint == "KCAT_C" and summary.weighting == "NINE_ROWS":
            assert float(summary.mean_absolute_log_error) == pytest.approx(sum(math.log(x / 3) for x in range(4, 13)) / 9)
    diagnostic = next(error for error in report.errors if error.case_id == r.case_id("A369V")
                      and error.method == "parent" and error.endpoint == "KCAT_C")
    assert diagnostic.absolute_error == 997
    assert report.independent_biological_units is report.calibrated_joint_coverage is None
    assert not report.candidate_nomination_established and not report.el_advantage_established
    with pytest.raises(ValueError, match="cannot promote"):
        replace(report, candidate_nomination_established=True)
    changed_summary = replace(report.summaries[0], mean_absolute_error=Decimal(0))
    with pytest.raises(ValueError, match="row/site arithmetic"):
        replace(report, summaries=(changed_summary, *report.summaries[1:]))
    assert model.training.native_source.rows == tuple(row.native for row in model.training.rows)


@pytest.mark.native("rapidfuzz")
def test_nonconstant_truth_known_natural_relation_changes_anchored_mutant_forecast(monkeypatch):
    training = software_natural(monkeypatch, nonconstant=True)
    queries, anchors, labels = software_plant(monkeypatch)
    model = k.fit(training)
    forecasts = k.predict(model, queries, anchors)
    parent = next(p for p in forecasts.model_points if p.case_id == r.PREFIX + ".parent" and p.endpoint == "KCAT_C")
    mutant = next(p for p in forecasts.model_points if p.case_id == r.case_id("I251L") and p.endpoint == "KCAT_C")
    assert parent.fixed_1nn.mean == 2 and mutant.fixed_1nn.mean == 4
    point = next(p for p in forecasts.forecasts if p.case_id == r.case_id("I251L") and p.method == "1nn" and p.endpoint == "KCAT_C")
    assert point.anchored_value == 6  # source parent3 × learned mutant4 / learned parent2
    assert float(point.predicted_log_contrast) == pytest.approx(math.log(2))
    assert not point.same_model_value and not point.same_neighbourhood
    assert not point.same_sequence and not point.same_distances
    report = k.evaluate(k.commit(forecasts), labels)
    error = next(e for e in report.errors if e.case_id == r.case_id("I251L") and e.method == "1nn" and e.endpoint == "KCAT_C")
    assert error.absolute_error == 2  # frozen observed software point4; no refit to its label


@pytest.mark.native("rapidfuzz")
def test_complete_global_barrier_and_truthful_distance_check_precede_any_label_inspection(result):
    _, commitment, labels = result
    class ForbiddenLabels:
        def __getattribute__(self, name):
            raise AssertionError("label access preceded complete commitment proof")
    with pytest.raises(ValueError, match="complete global"):
        k.evaluate(None, ForbiddenLabels())
    with pytest.raises(ValueError, match="bounded immutable typed roster"):
        replace(commitment.forecasts, forecasts=commitment.forecasts.forecasts[:-1])
    point = commitment.forecasts.model_points[0]
    shifted = tuple(replace(distance, distance=distance.distance + 1) for distance in point.distances)
    changed = replace(point, distances=shifted,
                      fixed_1nn=replace(point.fixed_1nn, boundary_distance=point.fixed_1nn.boundary_distance + 1,
                                        neighbours=tuple(replace(n, distance=n.distance + 1) for n in point.fixed_1nn.neighbours)),
                      selected_knn=replace(point.selected_knn, boundary_distance=point.selected_knn.boundary_distance + 1,
                                           neighbours=tuple(replace(n, distance=n.distance + 1) for n in point.selected_knn.neighbours)))
    # Arithmetic/membership remain valid, but the claimed distances are false.
    # Rebuild through normal frozen constructors, then the explicit numerical
    # validator must refuse before even inspecting the forbidden label operand.
    points = (changed, *commitment.forecasts.model_points[1:])
    by_case = {(point.case_id, point.endpoint): point for point in points}
    coherent_forecasts = tuple(replace(forecast, same_distances=(
        by_case[forecast.case_id, forecast.endpoint].distances == by_case[r.PREFIX + ".parent", forecast.endpoint].distances))
        if forecast.method != "parent" else forecast for forecast in commitment.forecasts.forecasts)
    forged = replace(commitment.forecasts, model_points=points, forecasts=coherent_forecasts)
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    altered = replace(commitment, forecasts=forged,
                      forecast_identity=ObjectIdentity.from_record(forged.forecast_id, forged))
    with pytest.raises(ValueError, match="source-sequence distances"):
        k.evaluate(altered, ForbiddenLabels())
    assert k.evaluate(commitment, labels).errors


@pytest.mark.native("rapidfuzz")
def test_predict_rejects_target_labels_and_foreign_protocol_source_and_parent(result):
    model, commitment, labels = result
    forecasts = commitment.forecasts
    with pytest.raises(ValueError, match="label-free queries"):
        k.predict(model, labels, forecasts.anchors)
    with pytest.raises(ValueError, match="frozen protocol"):
        replace(forecasts.queries, protocol_sha256="a" * 64)
    with pytest.raises(ValueError, match="source panel"):
        replace(forecasts.anchors, source_panel=replace(forecasts.anchors.source_panel, object_fingerprint="a" * 64))
    with pytest.raises(ValueError, match="exact A369"):
        replace(forecasts.queries.queries[0], recipe=replace(forecasts.queries.queries[0].recipe,
            translated_ssu="M" + "C" * 122))
    label = labels.labels[0]
    original = label.native.quantity("KCAT_C")
    coherent = replace(original, mean=Decimal(999), mean_cell=replace(original.mean_cell, token="999", xml_v_token="999"))
    native = replace(label.native, quantities=tuple(coherent if q.kind == "KCAT_C" else q for q in label.native.quantities))
    with pytest.raises(ValueError, match="native endpoint/source projection"):
        replace(label, native=native)


@pytest.mark.native("rapidfuzz")
def test_forecast_and_evaluation_closed_roundtrip_and_caller_context(result):
    _, commitment, labels = result
    expected = k.evaluate(commitment, labels)
    encoded = commitment.canonical_bytes()
    decoded = decode_canonical_bytes(encoded, r.PlantCommitmentV1, maximum_bytes=128 * 1024**2)
    assert decoded == commitment
    with localcontext() as context:
        context.prec, context.rounding = 3, ROUND_DOWN
        assert k.evaluate(decoded, labels) == expected
    assert decode_canonical_bytes(expected.canonical_bytes(), r.PlantEvaluationV1, maximum_bytes=1024**2) == expected
