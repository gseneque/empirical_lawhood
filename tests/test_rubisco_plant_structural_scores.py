# SPDX-License-Identifier: MPL-2.0
"""Exact structural source intake; these tests perform no kinetic model fits."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics import plant_structural_scores as source
from empirical_lawhood.adapters.physical.rubisco_kinetics.workbook import decode_native_workbook
from empirical_lawhood.kernel.decoding import decode_canonical_bytes

FIXTURES = Path(__file__).parent / "fixtures" / "rubisco" / "mcdonald2026_structural"


@pytest.fixture(scope="module")
def original():
    return (FIXTURES / "sciadv.aeh3246_table_s1.xlsx").read_bytes()


@pytest.fixture(scope="module")
def panel(original):
    return source.decode_plant_structural_scores(original)


def test_original_custody_and_complete_source_projection(original, panel):
    metadata = json.loads((FIXTURES / "source-metadata.json").read_text())
    assert metadata["license"].startswith("CC BY 4.0")
    assert len(original) == metadata["files"][0]["bytes"] == 698031
    assert sha256(original).hexdigest() == metadata["files"][0]["sha256"] == source.S1_SHA256
    assert tuple(r.edit for r in panel.rows) == source.EDITS
    assert tuple(r.site for r in panel.rows) == (251, 391, 391, 391, 438, 465, 468, 468, 470)
    assert panel.fingerprint() == "7481b9a8aa81cd61cfe03c9d9c47e04b0e6b390bf227b91d6e2c51270b04d8e0"
    assert panel.conservation_workbook.fingerprint() == source.CONSERVATION_WORKBOOK_FP
    assert len(panel.conservation_workbook.worksheet("Conservation scores").row_ids) == 478
    assert {m.member for m in panel.conservation_workbook.archive_inventory}.issuperset(
        {"xl/worksheets/sheet2.xml", "xl/worksheets/sheet3.xml", "xl/worksheets/sheet5.xml"})


def test_native_feature_meanings_and_missing_diagnostic(panel):
    rows = {r.edit: r for r in panel.rows}
    assert rows["T391I"].inverse_folding_log_likelihood == Decimal("-0.31658801007014398")
    assert rows["T391I"].native_cells[1].address == "B7202"
    assert rows["I251L"].land_plant_conservation_percent == Decimal("61.764705880000001")
    assert rows["N468D"].land_plant_conservation_percent == rows["N468Q"].land_plant_conservation_percent
    assert all(rows[m].land_plant_conservation_percent == Decimal("100") for m in ("T391C", "T391I", "T391V"))
    assert panel.diagnostic_edit == "A369V" and "NO_EXACT" in panel.diagnostic_status
    assert all("V369" in r.context_role and "A369" in r.context_role for r in panel.rows)
    # Native cached formula tokens stay source evidence, without execution.
    assert rows["I251L"].native_cells[2].formula == ""
    assert rows["I251L"].native_cells[2].token == "251"
    assert all(r.native_cells[1].formula is None for r in panel.rows)


def test_closed_canonical_roundtrip(panel):
    assert decode_canonical_bytes(panel.canonical_bytes(), source.PlantStructuralScorePanelV1,
                                   maximum_bytes=1024**2) == panel


def test_generic_member_bound_is_preserved(original):
    with pytest.raises(ValueError, match="XML expansion exceeds"):
        decode_native_workbook(original, expected_sha256=source.S1_SHA256, selected_sheets=("4RUB DMS",))


@pytest.mark.parametrize("payload", (b"", b"not a workbook"))
def test_unreviewed_bytes_refused(payload):
    with pytest.raises(ValueError, match="exact reviewed"):
        source.decode_plant_structural_scores(payload)


def test_changed_original_refused_before_xml_or_zip(original, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("unreviewed source was parsed")
    monkeypatch.setattr(source, "decode_native_workbook", forbidden)
    with pytest.raises(ValueError, match="exact reviewed"):
        source.decode_plant_structural_scores(original + b" ")


def test_forged_numbers_or_native_cells_with_genuine_source_id_refused(panel):
    row = panel.rows[0]
    with pytest.raises(ValueError, match="native source tokens"):
        replace(row, inverse_folding_log_likelihood=Decimal("-0.1"))
    cell = replace(row.native_cells[1], xml_v_token="-0.1", token="-0.1")
    with pytest.raises(ValueError, match="native cell witnesses"):
        replace(row, native_cells=(row.native_cells[0], cell, *row.native_cells[2:]),
                inverse_folding_log_likelihood=Decimal("-0.1"))


def test_roster_context_diagnostic_and_decimal_types_cannot_change(panel):
    with pytest.raises(ValueError, match="complete nine-row"):
        replace(panel, rows=panel.rows[:-1])
    with pytest.raises(ValueError, match="context"):
        replace(panel.rows[0], context_role="EXACT_A369_MUTANT_BACKBONE")
    with pytest.raises(ValueError, match="diagnostic"):
        replace(panel, diagnostic_status="SCORED")
    with pytest.raises(ValueError):
        replace(panel.rows[1], land_plant_conservation_percent=100)


def test_genuine_hash_with_changed_conservation_projection_refused(panel):
    workbook = panel.conservation_workbook
    sheet = workbook.worksheets[0]
    cell = replace(sheet.cell("C252"), xml_v_token="100", token="100")
    forged_sheet = replace(sheet, cells=tuple(cell if c.address == "C252" else c for c in sheet.cells))
    forged_workbook = replace(workbook, worksheets=(forged_sheet,))
    assert forged_workbook.source_sha256 == workbook.source_sha256
    with pytest.raises(ValueError, match="native workbook"):
        replace(panel, conservation_workbook=forged_workbook)
