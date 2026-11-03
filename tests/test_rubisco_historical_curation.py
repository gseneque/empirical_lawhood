"""Exposed three-stock source controls; no fit or biological qualification."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

from empirical_lawhood.adapters.methods.rubisco_prediction import historical_curation as r
from empirical_lawhood.adapters.methods.rubisco_prediction import historical_curation_sources as s
from empirical_lawhood.kernel.decoding import decode_canonical_bytes

FIXTURES = Path(__file__).parent / "fixtures/rubisco/historical-curation"


@pytest.fixture(scope="module")
def originals():
    census = json.loads((FIXTURES / "source-census.json").read_text())
    archive = FIXTURES / "primary-originals.tar.gz"
    assert len(archive.read_bytes()) == census["archive_bytes"]
    assert sha256(archive.read_bytes()).hexdigest() == census["archive_sha256"]
    assert census["stock_audit_sha256"] == "19cea59a6262f88c244086aa3ca1b9b43821f21623bef1cb763b66c5c0a46795"
    rows = {}
    with tarfile.open(archive, "r:gz") as packet:
        assert packet.getnames() == [m["member"] for m in census["members"]]
        for member in census["members"]:
            payload = packet.extractfile(member["member"]).read()
            assert len(payload) == member["bytes"]
            assert sha256(payload).hexdigest() == member["sha256"] == r.SOURCES[member["source_id"]][1]
            rows[member["source_id"]] = payload
    return rows


@pytest.fixture(scope="module")
def stocks(originals):
    return {name: s.curate_primary(s.decode_primary(name, payload)) for name, payload in originals.items()}


@pytest.mark.parametrize("name,table_counts,contexts,variants,paragraphs,cells,quantity_cells", [
    ("spreitzer2005", (4, 6, 4), 11, 8, 60, 140, 100),
    ("genkov2009", (13, 9), 17, 11, 55, 143, 99),
    ("zhou2014", (3,), 2, 2, 47, 18, 10),
])
def test_complete_selected_source_census_and_canonical_spelling(stocks, name, table_counts, contexts, variants, paragraphs, cells, quantity_cells):
    stock = stocks[name]
    assert tuple(len(t.rows) for t in stock.native.tables) == table_counts
    assert len(stock.contexts) == contexts
    assert len(stock.variant_roles) == variants
    assert len(stock.native.paragraphs) == paragraphs
    assert sum(len(row.cells) for table in stock.native.tables for row in table.rows) == cells
    assert sum(len(row.quantities) for row in stock.contexts) == quantity_cells
    restored = decode_canonical_bytes(stock.canonical_bytes(), r.HistoricalCuration, maximum_bytes=None)
    assert restored == stock
    assert restored.canonical_bytes() == stock.canonical_bytes()
    assert restored.independent_calibration_units is None
    assert restored.probability_of_joint_success is None
    assert restored.native_scientific_contacts == 0
    assert all(row.missing_roles[:len(r.MISSING_JOINS)] == r.MISSING_JOINS for row in restored.contexts)


def test_spreitzer_separate_series_derived_oxygenation_and_material_backgrounds(stocks):
    stock = stocks["spreitzer2005"]
    by_id = {row.context_id: row for row in stock.contexts}
    penta = by_id["spreitzer2005.tbl2.row3"]
    ko = penta.quantities[4]
    assert (ko.cell.raw_text, ko.mean_token, ko.error_token) == (" 1,400 ± 172 ", "1,400", "172")
    assert ko.reported_mean == Decimal("1400")
    assert penta.recipe.large_subunit_edits == ("V221C", "V235I", "C256F", "K258R", "I265V")
    assert penta.recipe.small_subunit_role == "RESIDENT_RBCS1_RBCS2_FAMILY"
    assert all(q.quantity_role == "SOURCE_CALCULATED" and q.reported_count_lower is None for q in penta.quantities[5:])
    assert penta.quantities[2].quantity_role == "REPORTED_TURNOVER_NORMALIZATION_UNVERIFIED"
    abso = by_id["spreitzer2005.tbl2.row4"]
    assert "SINGLE_RBCS1" in abso.recipe.small_subunit_role
    # The second series remains a separate observation of the same variant.
    same_variant = next(v for v in stock.variant_roles if v.variant == "Penta/ABSO")
    assert same_variant.native_context_ids == ("spreitzer2005.tbl2.row5", "spreitzer2005.tbl3.row3")
    assert by_id["spreitzer2005.tbl2.row5"].quantities[0].reported_mean == Decimal("67")
    assert by_id["spreitzer2005.tbl3.row3"].quantities[0].reported_mean == Decimal("70")
    assert "SINGLE_V221C_CORNER_UNREPORTED" in penta.missing_roles
    assert "TRIPLE_ABSO_CORNER_UNREPORTED" in penta.missing_roles


def test_genkov_complete_variant_denominator_failure_initial_only_and_mass_activity(stocks):
    stock = stocks["genkov2009"]
    roles = {v.variant: v for v in stock.variant_roles}
    assert roles["L18A"].role == "PURIFICATION_FAILURE_NO_KINETIC_ROW"
    assert roles["L18A"].native_context_ids == ()
    assert any("could not be isolated" in p.text for p in roles["L18A"].source_paragraphs)
    for name in ("S16A", "P19A", "E92A"):
        assert roles[name].role == "INITIAL_ASSAY_ONLY_NO_DEEP_KINETIC_ROW"
        assert len(roles[name].native_context_ids) == 1
        assert ".t1." in roles[name].native_context_ids[0]
    assert not any(q.kind == "KCAT_C" for row in stock.contexts for q in row.quantities)
    deep = next(row for row in stock.contexts if row.context_id == "genkov2009.t2.row2")
    assert deep.native_row.cells[0].text == "Wild-type"
    assert deep.recipe.small_subunit_edits == ()
    assert deep.quantities[0].quantity_role == "COPIED_FROM_SAME_PAPER_TABLE1"
    assert deep.quantities[1].kind == "VC_MASS"
    assert deep.quantities[1].reported_mean == Decimal("127")
    assert deep.quantities[3].unit == "source-printed-uM-CO2-unresolved"
    assert stock.native.tables[1].rows[1].cells[4].text == "μm CO2"
    assert "TABLE2_SPECIFICITY_REUSES_TABLE1_SUMMARY" in deep.missing_roles


def test_zhou_retains_turnover_sd_experiment_range_screen_and_missing_specificity(stocks):
    stock = stocks["zhou2014"]
    row = stock.contexts[1]
    assert row.native_row.cells[0].text == "M6-5"
    assert row.recipe.small_subunit_edits == ("E49V", "D82G")
    assert row.recipe.large_subunit_edits == ()
    kcat = row.quantities[1]
    assert kcat.cell.raw_text == "14.6\u00a0±\u00a01.1"
    assert (kcat.reported_count_lower, kcat.reported_count_upper) == (5, 6)
    assert kcat.count_role == "INDEPENDENT_EXPERIMENTS_SOURCE_REPORTED_NO_SAMPLE_IDS"
    assert "SPECIFICITY_AND_OXYGENATION_UNREPORTED" in row.missing_roles
    assert "SINGLE_MUTANT_CORNERS_E49V_D82G_UNREPORTED" in row.missing_roles
    assert not any(q.kind in {"SPECIFICITY_CO", "KCAT_O", "KO"} for q in row.quantities)
    assert "his6-tag" in row.recipe.material_paragraphs[-1].text
    assert "100% N2" in row.recipe.assay_paragraphs[-1].text
    assert row.quantities[3].quantity_role == "SOURCE_CALCULATED"


@pytest.mark.parametrize("name", tuple(r.SOURCES))
def test_original_digest_refuses_changed_cross_source_and_mutable_bytes(originals, name):
    blob = originals[name]
    with pytest.raises(ValueError, match="digest"):
        s.decode_primary(name, blob + b" ")
    with pytest.raises(ValueError):
        s.decode_primary(name, bytearray(blob))
    other = next(key for key in originals if key != name)
    with pytest.raises(ValueError, match="digest"):
        s.decode_primary(name, originals[other])


def test_exact_native_projection_refuses_cell_prose_header_and_row_omissions(stocks):
    native = stocks["spreitzer2005"].native
    table = native.tables[1]
    row = table.rows[1]
    cell = replace(row.cells[1], raw_text="99 ± 1")
    changed_row = replace(row, cells=(row.cells[0], cell, *row.cells[2:]))
    changed_table = replace(table, rows=(table.rows[0], changed_row, *table.rows[2:]))
    with pytest.raises(ValueError, match="projection"):
        replace(native, tables=(native.tables[0], changed_table, native.tables[2]))
    changed_p = replace(native.paragraphs[25], raw_text="missing assay recipe")
    with pytest.raises(ValueError, match="projection"):
        replace(native, paragraphs=(*native.paragraphs[:25], changed_p, *native.paragraphs[26:]))
    with pytest.raises(ValueError):
        replace(native, tables=native.tables[:2])
    with pytest.raises(ValueError):
        replace(native.paragraphs[0], ordinal_0based=True)
    with pytest.raises(ValueError):
        replace(table, rows=table.rows[1:])


@pytest.mark.parametrize("change", [
    {"candidate_domain_qualification": "QUALIFIED"},
    {"probability_of_joint_success": Decimal(".99")},
    {"independent_calibration_units": 17},
    {"native_scientific_contacts": True},
    {"exposure": "UNTOUCHED"},
    {"missing_roles": ()},
    {"programme_predictive_status": "PREDICTIVELY_QUALIFIED"},
])
def test_curation_cannot_promote_source_counts_or_exposure(stocks, change):
    with pytest.raises(ValueError):
        replace(stocks["genkov2009"], **change)


def test_source_interpretation_rejects_quantity_role_count_material_gas_and_group_changes(stocks):
    stock = stocks["spreitzer2005"]
    row = stock.contexts[3]
    for altered in (
        replace(row.quantities[0], quantity_role="SOURCE_CALCULATED"),
        replace(row.quantities[0], unit="s^-1"),
        replace(row.quantities[0], reported_count_upper=4),
    ):
        changed = replace(row, quantities=(altered, *row.quantities[1:]))
        with pytest.raises(ValueError, match="source roles"):
            replace(stock, contexts=(*stock.contexts[:3], changed, *stock.contexts[4:]))
    for altered_recipe in (
        replace(row.recipe, small_subunit_role="HOMOGENEOUS_SSU"),
        replace(row.recipe, gas_recipe_role="FULLY_AUTHENTICATED_ASSAY"),
        replace(row.recipe, large_subunit_edits=("V221C",)),
    ):
        changed = replace(row, recipe=altered_recipe)
        with pytest.raises(ValueError, match="source roles"):
            replace(stock, contexts=(*stock.contexts[:3], changed, *stock.contexts[4:]))
    changed = replace(row, groups=(replace(row.groups[0], group_id="fresh-paper"), *row.groups[1:]))
    with pytest.raises(ValueError, match="source roles"):
        replace(stock, contexts=(*stock.contexts[:3], changed, *stock.contexts[4:]))
    with pytest.raises(ValueError, match="source roles"):
        replace(stock, variant_roles=stock.variant_roles[:-1])


def test_nested_components_preserve_paper_parent_sites_without_counting_independent_units(stocks):
    complete = tuple(stocks.values())
    groups = r.connected_context_groups(complete)
    assert sorted(map(len, groups)) == [2, 11, 17]
    assert {row for group in groups for row in group} == {row.context_id for stock in complete for row in stock.contexts}
    assert sum(len(group) for group in groups) == 30
    assert all(stock.independent_calibration_units is None for stock in complete)
    with pytest.raises(ValueError, match="duplicate"):
        r.connected_context_groups((complete[0], complete[0]))


def test_import_is_cold_and_has_no_native_or_acquisition_dependency():
    code = """
import builtins
real = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'numpy','scipy','rapidfuzz','requests','urllib3','pyscf','pybamm'}:
        raise AssertionError('native/acquisition import: ' + name)
    return real(name, *args, **kwargs)
builtins.__import__ = guarded
from empirical_lawhood.adapters.methods.rubisco_prediction.historical_curation_sources import decode_primary
assert callable(decode_primary)
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
