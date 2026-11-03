# SPDX-License-Identifier: MPL-2.0
"""Original exposed associations test exact intake, without biological warrant."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics import iqbal2023 as source
from empirical_lawhood.kernel.decoding import decode_canonical_bytes

FIXTURES = Path(__file__).parent / "fixtures" / "rubisco" / "iqbal2023"


@pytest.fixture(scope="module")
def originals():
    return tuple((FIXTURES / name).read_bytes() for name in ("primary.xml", "table_s2.xlsx"))


@pytest.fixture(scope="module")
def table(originals):
    return source.decode_iqbal2023(*originals)


def test_original_custody_complete_census_and_missing_endpoints(table, originals):
    metadata = json.loads((FIXTURES / "source-metadata.json").read_text())
    assert metadata["license"].startswith("CC BY 4.0")
    assert [(len(b), sha256(b).hexdigest()) for b in originals] == [
        (f["bytes"], f["sha256"]) for f in metadata["files"]
    ]
    assert len(table.rows) == 183
    assert tuple(r.native_row for r in table.rows) == tuple(range(2, 185))
    assert len({r.sequence for r in table.rows}) == 132
    assert len({r.genus for r in table.rows}) == 86
    assert sum(r.turnover_s_inv is not None for r in table.rows) == 165
    assert sum(r.specificity_dimensionless is not None for r in table.rows) == 170
    assert sum(r.turnover_s_inv is not None and r.specificity_dimensionless is not None
               for r in table.rows) == 155
    assert len({r.cells[11].token for r in table.rows}) == 17
    assert min(len(r.sequence) for r in table.rows) == 422
    assert max(len(r.sequence) for r in table.rows) == 485
    beta = next(r for r in table.rows if r.native_row == 21)
    assert beta.cells[4].token is None and beta.turnover_s_inv is None
    assert beta.specificity_dimensionless == Decimal("92.9")
    crithmum = next(r for r in table.rows if r.native_row == 40)
    assert crithmum.turnover_s_inv == Decimal("3.4")
    assert crithmum.cells[6].token is None and crithmum.specificity_dimensionless is None


def test_native_tobacco_background_uncertainties_and_roles(table):
    row = next(r for r in table.rows if r.native_row == 112)
    assert row.cells[0].token == "Nicotiana tabacum"
    assert row.genus == "Nicotiana" and len(row.sequence) == 477
    assert row.sequence[368] == "V" and row.sequence[390] == "T"
    assert row.turnover_s_inv == Decimal("3.1")
    assert row.cells[5].token == "0.3"
    assert row.specificity_dimensionless == Decimal("80")
    assert row.cells[7].token == "2.6"
    assert row.adjusted_kc_air_micromolar == Decimal("18.3")
    assert all(r.independent_biological_n is None and r.endpoint_pairing == "UNRESOLVED"
               for r in table.rows)
    assert "NO_INDEPENDENT_BIOLOGICAL_N_OR_ENDPOINT_PAIRING" in table.limitations
    assert "KC_AIR_ADJUSTED_SOURCE_ROLE_NOT_DIRECT_SPECIFICITY" in table.limitations


def test_closed_roundtrip(table):
    decoded = decode_canonical_bytes(table.canonical_bytes(), source.IqbalTrainingTableV1,
                                     maximum_bytes=2 * 1024**2)
    assert decoded == table and decoded.fingerprint() == table.fingerprint()


@pytest.mark.parametrize("index", (0, 1))
def test_original_bytes_are_mandatory(originals, index):
    altered = list(originals)
    altered[index] += b" "
    with pytest.raises(ValueError):
        source.decode_iqbal2023(*altered)


def test_genuine_original_hash_does_not_admit_coherently_altered_cells(table):
    sheet = table.workbook.worksheets[0]
    genuine = sheet.cell("E112")
    forged = replace(genuine, token="31", xml_v_token="31")
    altered_sheet = replace(sheet, cells=tuple(forged if c.address == "E112" else c for c in sheet.cells))
    altered_book = replace(table.workbook, worksheets=(altered_sheet,))
    assert altered_book.source_sha256 == source.WORKBOOK_SHA256
    assert altered_book.fingerprint() != source.WORKBOOK_FINGERPRINT
    with pytest.raises(ValueError, match="coherent native projection"):
        replace(table, workbook=altered_book)


def test_native_row_projection_and_complete_denominator_cannot_change(table):
    row = table.rows[110]
    with pytest.raises(ValueError, match="exact mean projections"):
        replace(row, turnover_s_inv=Decimal("31"))
    with pytest.raises(ValueError, match="species/genus/sequence/length"):
        replace(row, genus="Galdieria")
    with pytest.raises(ValueError, match="source cells"):
        replace(table, rows=table.rows[:-1])


def test_equal_python_integer_cannot_replace_exact_decimal_quantity(table):
    row = table.rows[110]
    assert row.specificity_dimensionless == 80
    with pytest.raises(ValueError, match="exact mean projections"):
        replace(row, specificity_dimensionless=80)


@pytest.mark.parametrize("changes", [
    {"independent_biological_n": 3}, {"endpoint_pairing": "PAIRED"},
    {"uncertainty_role": "CALIBRATED_PRECISION"}, {"native_row": True},
])
def test_no_invented_biological_units_pairing_or_precision(table, changes):
    with pytest.raises(ValueError):
        replace(table.rows[0], **changes)


@pytest.mark.parametrize("changes", [
    {"exposure": "FRESH_MUTATION_EVIDENCE"}, {"limitations": ()},
    {"units_and_conditions_role": "COMPLETE_PER_ROW_METROLOGY"},
])
def test_compilation_cannot_create_mutation_support_or_metrology(table, changes):
    with pytest.raises(ValueError):
        replace(table, **changes)
