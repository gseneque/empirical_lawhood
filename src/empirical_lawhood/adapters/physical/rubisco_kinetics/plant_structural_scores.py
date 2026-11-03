# SPDX-License-Identifier: MPL-2.0
"""Exact deposited structural proxies; no model or native science is executed.

The complete reviewed workbook is byte-pinned. Its larger 4RUB sheet has a
separate 3 MiB source-specific inspection boundary, leaving the generic native
workbook's 1 MiB selected-sheet contract unchanged. Only nine declared focal
rows are projected, with exact cell witnesses and missing diagnostic explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
from typing import ClassVar
import xml.etree.ElementTree as ET
import zipfile

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal

from .workbook import (
    NS, NativeWorkbookCellV1, NativeWorkbookV1, decode_native_workbook,
)

S1_SHA256 = "01c58e35fa43a8cc1a363d58ca4e4c5e3ff2c262c5c4f3b10002ceb3c869ff26"
STRUCTURAL_MEMBER = "xl/worksheets/sheet3.xml"
STRUCTURAL_SHA256 = "c6f3a8f65162abe355da64c5e04c1a9bc0a43cded89f73efab21a7ac526ebc38"
CONSERVATION_SHA256 = "2cb9ab1a07e09e4ee2c2a1076a2f1f984fce726e76745d5711040ac0f5850a89"
CONSERVATION_WORKBOOK_FP = "37495bc0bda294ff1a2e046db9839f04270f0f8ea35bbad9f39cd1a844fc83a6"
EDITS = ("I251L", "T391C", "T391I", "T391V", "A438R", "I465V", "N468D", "N468Q", "A470R")
# Digests of five concatenated canonical native cells per edit: structural
# mutation/score, then conservation site/WT residue/land-plant percentage.
# These were calculated directly from the byte-pinned original before fitting.
WITNESSES = {
    "I251L": "b80ebb8aaec7ad3880451f83ffb8a39d7fdda193a599eb1ffd197bc6c625333d",
    "T391C": "9532f35556abcc3bf7f55170ac6106bcf0807a0c55be903ac82fc24a7959814e",
    "T391I": "6dc21e59aba6268708679bfd0af82957c8ec60160b0b610b86d8465c711da737",
    "T391V": "35e055ae06a31726357dfcfb001465a4999c81cf532f789cc8fd949b042503d2",
    "A438R": "3b470423e384a87edc8d643e296a89e4cf8112b328c19c81013bee32f3ccec58",
    "I465V": "882eb380c7e8e1e7b1a46def9499e764541a7faca9711b93030cf4609a9ca5c5",
    "N468D": "2451f01d4b65128441646a952643b515b193dfacfbe6eb5257d39b424ad71481",
    "N468Q": "4d9d65d0f6fc81c6d89142a9a7fba3d158df5e08e5139f8f2ee6b9fdeb7a8947",
    "A470R": "692da5919614eb2c04fa58c0c868b985b04d1aa204decdc22c2360fabb7cf810",
}


@dataclass(frozen=True, slots=True)
class PlantStructuralScoreRowV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/plant-structural-score-row"
    edit: str
    site: int
    inverse_folding_log_likelihood: Decimal
    land_plant_conservation_percent: Decimal
    native_cells: tuple[NativeWorkbookCellV1, ...]
    source_sha256: str = S1_SHA256
    structural_member_sha256: str = STRUCTURAL_SHA256
    conservation_member_sha256: str = CONSERVATION_SHA256
    context_role: str = "TRANSFERRED_NATIVE_V369_CABP_STRUCTURE_PROXY_FOR_A369_ASSAY"

    def __post_init__(self) -> None:
        if self.edit not in EDITS or type(self.site) is not int or self.site != int(self.edit[1:-1]):
            raise ValueError("structural row changes the exact focal edit/site")
        if (self.source_sha256, self.structural_member_sha256, self.conservation_member_sha256,
                self.context_role) != (S1_SHA256, STRUCTURAL_SHA256, CONSERVATION_SHA256,
                "TRANSFERRED_NATIVE_V369_CABP_STRUCTURE_PROXY_FOR_A369_ASSAY"):
            raise ValueError("structural row changes its source or transferred context")
        if (type(self.native_cells) is not tuple or len(self.native_cells) != 5
                or any(type(c) is not NativeWorkbookCellV1 for c in self.native_cells)
                or sha256(b"".join(c.canonical_bytes() for c in self.native_cells)).hexdigest() != WITNESSES[self.edit]):
            raise ValueError("structural row changes its exact native cell witnesses")
        validate_decimal(self.inverse_folding_log_likelihood, field_name="inverse_folding_log_likelihood")
        validate_decimal(self.land_plant_conservation_percent, field_name="land_plant_conservation_percent")
        if (self.inverse_folding_log_likelihood != Decimal(self.native_cells[1].token)
                or self.land_plant_conservation_percent != Decimal(self.native_cells[4].token)):
            raise ValueError("structural values differ from native source tokens")


@dataclass(frozen=True, slots=True)
class PlantStructuralScorePanelV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/plant-structural-score-panel"
    rows: tuple[PlantStructuralScoreRowV1, ...]
    conservation_workbook: NativeWorkbookV1
    source_sha256: str = S1_SHA256
    diagnostic_edit: str = "A369V"
    diagnostic_status: str = "UNEVALUABLE_NO_EXACT_DEPOSITED_STRUCTURAL_SCORE"
    exposure: str = "EXPOSED_DEVELOPMENT_SOURCE"

    def __post_init__(self) -> None:
        if (type(self.rows) is not tuple or any(type(r) is not PlantStructuralScoreRowV1 for r in self.rows)
                or tuple(r.edit for r in self.rows) != EDITS):
            raise ValueError("structural score panel omits or changes the complete nine-row roster")
        for row in self.rows:
            row.__post_init__()
        if (type(self.conservation_workbook) is not NativeWorkbookV1
                or self.conservation_workbook.fingerprint() != CONSERVATION_WORKBOOK_FP
                or self.source_sha256 != S1_SHA256
                or (self.diagnostic_edit, self.diagnostic_status, self.exposure) != (
                    "A369V", "UNEVALUABLE_NO_EXACT_DEPOSITED_STRUCTURAL_SCORE", "EXPOSED_DEVELOPMENT_SOURCE")):
            raise ValueError("structural score panel changes its native workbook or diagnostic role")


def _native_cell(node: ET.Element, strings: tuple[str, ...]) -> NativeWorkbookCellV1:
    values, formulas = node.findall(NS + "v"), node.findall(NS + "f")
    if len(values) != 1 or formulas:
        raise ValueError("selected structural cell requires one literal cached value without a formula")
    native = values[0].text
    kind = node.get("t", "n")
    token = strings[int(native)] if kind == "s" else native
    return NativeWorkbookCellV1(node.get("r"), kind, native, token, None,
                                tuple(sorted(node.attrib.items())), ())


def decode_plant_structural_scores(payload: bytes) -> PlantStructuralScorePanelV1:
    """Admit exact original bytes and preserve all selected native cell lineage."""
    if type(payload) is not bytes or not 1 <= len(payload) <= 16 * 1024**2 or sha256(payload).hexdigest() != S1_SHA256:
        raise ValueError("structural score intake requires the exact reviewed original S1")
    workbook = decode_native_workbook(payload, expected_sha256=S1_SHA256,
                                      selected_sheets=("Conservation scores",))
    entry = next(c for c in workbook.sheet_catalog if c.member == STRUCTURAL_MEMBER)
    if entry.name != "4RUB DMS":
        raise ValueError("structural source member changes its native sheet identity")
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        info = archive.getinfo(STRUCTURAL_MEMBER)
        if info.file_size > 3 * 1024**2:
            raise ValueError("reviewed structural member exceeds its separate 3 MiB bound")
        with archive.open(info) as stream:
            raw = stream.read(3 * 1024**2 + 1)
    if len(raw) != info.file_size or sha256(raw).hexdigest() != STRUCTURAL_SHA256:
        raise ValueError("structural member changes its exact admitted bytes")
    if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
        raise ValueError("structural source refuses XML entities")
    root = ET.fromstring(raw)
    native_rows = root.find(NS + "sheetData").findall(NS + "row")
    if len(native_rows) > 20000:
        raise ValueError("structural source exceeds its separate native row bound")
    conservation = workbook.worksheet("Conservation scores")
    selected = {}
    for node in native_rows:
        cells = node.findall(NS + "c")
        if not cells or cells[0].find(NS + "v") is None or cells[0].find(NS + "f") is not None:
            continue
        mutation = _native_cell(cells[0], workbook.shared_strings)
        if mutation.token not in EDITS:
            continue
        if mutation.token in selected:
            raise ValueError("structural source duplicates an exact focal allele")
        site = int(mutation.token[1:-1])
        score = _native_cell(cells[1], workbook.shared_strings)
        witness = (mutation, score, *(conservation.cell(f"{c}{site + 1}") for c in "ABC"))
        selected[mutation.token] = PlantStructuralScoreRowV1(
            mutation.token, site, Decimal(score.token), Decimal(witness[4].token), witness,
        )
    if set(selected) != set(EDITS):
        raise ValueError("structural source omits focal score rows")
    return PlantStructuralScorePanelV1(tuple(selected[edit] for edit in EDITS), workbook)
