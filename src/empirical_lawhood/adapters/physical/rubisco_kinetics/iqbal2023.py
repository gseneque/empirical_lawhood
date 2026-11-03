# SPDX-License-Identifier: MPL-2.0
"""Exact natural-plant source associations; no mutation or uncertainty warrant.

The publication's separate endpoint means and raw LSU sequences are retained
with all missing cells and citations. Source-converted SDs do not establish
biological n, exact holoenzyme composition, pairing or calibrated precision.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import re
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord

from .direct_panels import _number
from .workbook import NativeWorkbookCellV1, NativeWorkbookV1, decode_native_workbook

ARTICLE_SHA256 = "77c7bb857c26132820123d70ad356deb36124b162300f124784df6eddadbdd0f"
WORKBOOK_SHA256 = "bbd449d86c96297acf6351cf184464ceb23cbc1f42535beff4fce8b0dcd7bbc0"
WORKBOOK_FINGERPRINT = "7e778dc69a2d1c8d958a7cf1ac18b8895201a951bf56bb45fb5a0862b61fabee"
LIMITATIONS = (
    "ACTUAL_ASSAY_HOLOENZYME_SMALL_SUBUNITS_AND_PROCESSING_UNRESOLVED",
    "COMPILED_NATURAL_SOURCE_ASSOCIATIONS_NOT_INDEPENDENT_MUTATION_EVIDENCE",
    "DUPLICATE_SEQUENCES_AND_CITATION_DEPENDENCE_RETAINED",
    "EXPOSED_SOURCE_REPORTED_DATA_NOT_QUALIFICATION",
    "GENUS_DERIVED_FROM_NATIVE_SPECIES_FIRST_TOKEN",
    "KC_AIR_ADJUSTED_SOURCE_ROLE_NOT_DIRECT_SPECIFICITY",
    "NO_INDEPENDENT_BIOLOGICAL_N_OR_ENDPOINT_PAIRING",
    "SOURCE_SD_CONVERSIONS_AND_ASSUMED_SAMPLE_COUNTS_NOT_CALIBRATION",
    "TEMPERATURE_25C_AND_PH_NEAR8_FROM_PRIMARY_METHOD_NOT_PER_ROW_METROLOGY",
)


@dataclass(frozen=True, slots=True)
class IqbalNaturalRowV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/iqbal2023-natural-row"
    native_row: int
    cells: tuple[NativeWorkbookCellV1, ...]
    genus: str
    sequence: str
    turnover_s_inv: Decimal | None
    specificity_dimensionless: Decimal | None
    adjusted_kc_air_micromolar: Decimal | None
    independent_biological_n: int | None = None
    endpoint_pairing: str = "UNRESOLVED"
    uncertainty_role: str = "SOURCE_CONVERTED_SD_NOT_CALIBRATED_BIOLOGICAL_PRECISION"

    def __post_init__(self) -> None:
        if (type(self.native_row) is not int or not 2 <= self.native_row <= 184
                or not isinstance(self.cells, tuple)
                or not all(isinstance(c, NativeWorkbookCellV1) for c in self.cells)
                or tuple(c.address for c in self.cells) != tuple(f"{c}{self.native_row}" for c in "ABCDEFGHIJKLMN")):
            raise ValueError("Iqbal row must retain all fourteen native cells and exact source ordinal")
        if (self.cells[0].token is None or self.genus != self.cells[0].token.split()[0]
                or self.sequence != self.cells[13].token or not isinstance(self.sequence, str)
                or re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]{422,485}", self.sequence) is None
                or self.cells[10].token != str(len(self.sequence))):
            raise ValueError("Iqbal native species/genus/sequence/length projection differs")
        expected = tuple(_number(self.cells[i].token) for i in (4, 6, 8))
        observed = (self.turnover_s_inv, self.specificity_dimensionless, self.adjusted_kc_air_micromolar)
        if (any(v is not None and type(v) is not Decimal for v in observed)
                or observed != expected):
            raise ValueError("Iqbal native endpoint roles or exact mean projections differ")
        if (self.independent_biological_n is not None or self.endpoint_pairing != "UNRESOLVED"
                or self.uncertainty_role != "SOURCE_CONVERTED_SD_NOT_CALIBRATED_BIOLOGICAL_PRECISION"):
            raise ValueError("source associations cannot invent biological n, pairing or precision")


def _rows(workbook: NativeWorkbookV1) -> tuple[IqbalNaturalRowV1, ...]:
    sheet = workbook.worksheets[0]
    result = []
    for row in range(2, 185):
        cells = tuple(sheet.cell(f"{column}{row}") for column in "ABCDEFGHIJKLMN")
        if any(cell is None for cell in cells):
            raise ValueError("Iqbal complete native row or missing-value cell is absent")
        species, sequence = cells[0].token, cells[13].token
        result.append(IqbalNaturalRowV1(row, cells, species.split()[0], sequence,
                                      *(_number(cells[i].token) for i in (4, 6, 8))))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class IqbalTrainingTableV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/iqbal2023-training-table"
    original_article_sha256: str
    workbook: NativeWorkbookV1
    rows: tuple[IqbalNaturalRowV1, ...]
    units_and_conditions_role: str = "PRIMARY_METHOD_UNITS_AND_CONTEXT_NO_NATIVE_WORKBOOK_UNIT_ROW"
    limitations: tuple[str, ...] = LIMITATIONS
    exposure: str = "EXPOSED_COMPILED_NATURAL_TRAINING_ASSOCIATIONS"

    def __post_init__(self) -> None:
        if (self.original_article_sha256 != ARTICLE_SHA256
                or not isinstance(self.workbook, NativeWorkbookV1)
                or self.workbook.source_sha256 != WORKBOOK_SHA256
                or self.workbook.fingerprint() != WORKBOOK_FINGERPRINT
                or tuple(s.catalog_entry.name for s in self.workbook.worksheets) != ("Sheet1",)):
            raise ValueError("Iqbal exact original source or coherent native projection differs")
        if self.rows != _rows(self.workbook):
            raise ValueError("Iqbal training projections differ from sealed native source cells")
        if (len(self.rows) != 183 or len({r.sequence for r in self.rows}) != 132
                or len({r.genus for r in self.rows}) != 86
                or sum(r.turnover_s_inv is not None for r in self.rows) != 165
                or sum(r.specificity_dimensionless is not None for r in self.rows) != 170
                or sum(r.adjusted_kc_air_micromolar is not None for r in self.rows) != 170):
            raise ValueError("Iqbal native species/sequence/genus/endpoint census differs")
        if (self.units_and_conditions_role != "PRIMARY_METHOD_UNITS_AND_CONTEXT_NO_NATIVE_WORKBOOK_UNIT_ROW"
                or self.limitations != LIMITATIONS or self.exposure != "EXPOSED_COMPILED_NATURAL_TRAINING_ASSOCIATIONS"):
            raise ValueError("Iqbal source cannot promote mutation support, metrology or uncertainty warrant")


def decode_iqbal2023(article_xml: bytes, training_xlsx: bytes) -> IqbalTrainingTableV1:
    """Admit exact reviewed source bytes; callers own bounded I/O and custody.

    The article is a pinned original used for method/context attribution, not a
    general XML input: no JATS DTD, entity, network or executable content runs.
    The existing bounded workbook decoder owns native XLSX interpretation.
    """
    if not isinstance(article_xml, bytes) or sha256(article_xml).hexdigest() != ARTICLE_SHA256:
        raise ValueError("Iqbal reviewed original article bytes differ from custody")
    workbook = decode_native_workbook(training_xlsx, expected_sha256=WORKBOOK_SHA256, selected_sheets=("Sheet1",))
    return IqbalTrainingTableV1(ARTICLE_SHA256, workbook, _rows(workbook))
