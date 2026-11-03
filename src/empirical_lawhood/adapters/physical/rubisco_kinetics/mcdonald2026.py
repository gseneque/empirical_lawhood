# SPDX-License-Identifier: MPL-2.0
"""Exact exposed McDonald plant release; source reports, not qualified kinetics.

The original XML and S4/S5/S8 archives are mandatory, hash-first inputs. Native
workbook projections are sealed too: keeping an authentic archive digest while
editing its cells cannot create an admitted panel. No formula, model, experiment
or source acquisition runs here. Source means and measurement counts retain
their unresolved preparation and literal RuBP-unit reconstruction limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import re
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord

from .direct_panels import NativeRawEndpointValueV1, _diagnostics, _number
from .genbank import _translate_complete_cds
from .workbook import (
    MAX_SELECTED_XML_BYTES, NativeWorkbookCellV1, NativeWorkbookV1, NativeWorksheetV1, _xml, decode_native_workbook,
)

ARTICLE_SHA256 = "6c37fa27a8a0e1a98442544ecc7fd5113edaa5adebbe7fc96fbe893cfbe2b621"
S4_SHA256 = "dde3da450f7747952dc67f2c8562d28fa27ba183f39bb608f5acfaaa2d237451"
S5_SHA256 = "bebe5d372c3dbc479cfc1f6a3b4ea36158cd690b4ea27225b27937565e782f31"
S8_SHA256 = "d328da05d4d330f0ca95722d1a7b84cf1a38a284e50cbebf53d2bf370ebbb0f5"
S4_FINGERPRINT = "371a56c91d0c8556bdff67506318774460f20363f18468fb2248f3e764152ae2"
S5_FINGERPRINT = "2a527e2b0777ea350a020708db1c5e67bda0b91fb8c89ca46d7fb497763f073e"
S8_FINGERPRINT = "c1678bb031210b13263a17426ef5aa96496aa0655a534846a987e734f983cc8f"
ARTICLE_FINGERPRINT = "3a35c1bf227f84257d609c381274dc68f45d863d3bf59a74e89710fb2b916724"
S4_SHEETS = ("Kinetics Raw Data + Stats", "Summary table")
S5_SHEETS = ("Enrichment frequencies",)
S8_SHEETS = ("Sheet1",)
CONTEXT_NAMES = (
    "NtRbcL", "NtRbcL I251L", "NtRbcL T391C", "NtRbcL T391I", "NtRbcL T391V",
    "NtRbcL A438R", "NtRbcL I465V", "NtRbcL N468D", "NtRbcL N468Q", "NtRbcL A470R",
    "NtRbcL A369V", "N. tabacum leaf",
)
LIMITS = (
    "A369_BACKGROUND_DIFFERS_FROM_NATIVE_V369_REFERENCE",
    "COUNTS_ARE_ENDPOINT_MEASUREMENTS_NOT_INDEPENDENT_BIOLOGICAL_N",
    "EXPOSED_SOURCE_REPORTED_EVIDENCE_NOT_QUALIFICATION",
    "K201_CONTROL_HAS_EIGHTEEN_VARIANTS_K201M_ABSENT",
    "LEAF_SPECIFICITY_NOT_MEASURED",
    "LITERAL_1_3_MICROMOLAR_RUBP_CONDITIONAL_RECONSTRUCTION_CONFLICT_UNRESOLVED",
    "NO_MEASURED_MUTANT_KO_OR_OXYGENATION_KCAT",
    "NO_TOBACCO_TO_RED_PARENT_EFFECT_TRANSPORT",
    "PLANT_V369_HIS6_FUSION_AND_ENDOGENOUS_SSUS_ARE_A_SEPARATE_VIEW",
    "S4_A470R_EXPRESSION_AND_FIGURE3_EXPRESSION_JOIN_UNRESOLVED",
    "S5_TWENTY_RESCREEN_FLAGS_AND_FIGURE3_NINETEEN_RESCREEN_VARIANTS_RETAINED",
    "SOURCE_DERIVED_AMINO_ACID_RECIPES_NOT_DEPOSITED_MUTANT_DNA",
    "SPECIFICITY_AND_TURNOVER_PREPARATION_PAIRING_AND_COVARIANCE_UNRESOLVED",
    "TERMINAL_PROCESSING_AND_UBIQUITIN_CLEAVAGE_NOT_INDEPENDENTLY_VERIFIED",
)


def _cell(sheet: NativeWorksheetV1, address: str) -> NativeWorkbookCellV1:
    result = sheet.cell(address)
    if result is None:
        raise ValueError(f"required McDonald2026 native cell {address} is absent")
    return result


def _token(cell: NativeWorkbookCellV1) -> str:
    if cell.token is None:
        raise ValueError("required McDonald2026 native token is absent")
    return cell.token


def _sealed_workbook(workbook: NativeWorkbookV1, source: str, fingerprint: str, sheets: tuple[str, ...]) -> None:
    if (workbook.source_sha256 != source or workbook.fingerprint() != fingerprint
            or tuple(w.catalog_entry.name for w in workbook.worksheets) != sheets):
        raise ValueError("McDonald2026 source workbook or coherent native-cell projection differs")


@dataclass(frozen=True, slots=True)
class NativePlantArticleV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/mcdonald2026-native-article"
    source_sha256: str
    doi: str
    pmcid: str
    title: str
    table1_cells: tuple[tuple[str, ...], ...]
    table1_caption: str
    method_sections: tuple[tuple[str, tuple[str, ...]], ...]

    def __post_init__(self) -> None:
        if (self.source_sha256, self.doi, self.pmcid) != (
            ARTICLE_SHA256, "10.1126/sciadv.aeh3246", "PMC13644767"
        ) or len(self.table1_cells) != 11 or any(len(row) != 6 for row in self.table1_cells):
            raise ValueError("McDonald2026 article identity or complete Table1 census differs")
        if self.fingerprint() != ARTICLE_FINGERPRINT:
            raise ValueError("McDonald2026 native article projection differs from the exact source")


def _article(payload: bytes) -> NativePlantArticleV1:
    if not 1 <= len(payload) <= MAX_SELECTED_XML_BYTES or sha256(payload).hexdigest() != ARTICLE_SHA256:
        raise ValueError("McDonald2026 original article bytes differ from source custody")
    root = _xml(payload, root_name="article")
    ids = {x.get("pub-id-type"): x.text for x in root.findall(".//article-id")}
    title = root.find(".//article-title")
    table = root.find(".//table-wrap[@id='T1']")
    if title is None or table is None or table.find("caption") is None:
        raise ValueError("McDonald2026 original article requires native title and Table1")
    sections = []
    for identity in ("sec14", "sec15", "sec16"):
        section = root.find(f".//sec[@id='{identity}']")
        if section is None or section.find("title") is None:
            raise ValueError("McDonald2026 requires complete native purification and assay sections")
        sections.append(("".join(section.find("title").itertext()),
                         tuple("".join(p.itertext()) for p in section.findall("p"))))
    return NativePlantArticleV1(
        ARTICLE_SHA256, ids.get("doi", ""), ids.get("pmcid", ""), "".join(title.itertext()),
        tuple(tuple("".join(c.itertext()) for c in row) for row in table.findall(".//tr")),
        "".join(table.find("caption").itertext()), tuple(sections),
    )


@dataclass(frozen=True, slots=True)
class PlantQuantityV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/mcdonald2026-quantity"
    kind: str
    unit: str
    role: str
    source_group: str
    mean_cell: NativeWorkbookCellV1 | None
    sd_cell: NativeWorkbookCellV1 | None
    sem_cell: NativeWorkbookCellV1 | None
    count_cell: NativeWorkbookCellV1
    summary_mean_cell: NativeWorkbookCellV1 | None
    summary_sd_cell: NativeWorkbookCellV1 | None
    mean: Decimal | None
    sd: Decimal | None
    measurement_count: int | None
    raw_values: tuple[NativeRawEndpointValueV1, ...]
    recomputed_raw_mean: Decimal | None
    recomputed_raw_sample_sd: Decimal | None
    diagnostic_flags: tuple[str, ...]
    uncertainty_role: str = "SOURCE_REPORTED_SD_NOT_CALIBRATED_JOINT_PRECISION"
    independent_biological_n: int | None = None
    paired_sample_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        units = {"KCAT_C": "s^-1", "SPECIFICITY_CO": "dimensionless", "KC_AIR": "micromolar",
                 "CARBOXYLATION_EFFICIENCY_AIR": "mM^-1 s^-1"}
        if self.kind not in units or self.unit != units[self.kind]:
            raise ValueError("McDonald2026 quantity role/unit is unsupported; no inferred oxygenation labels")
        if (self.independent_biological_n is not None or self.paired_sample_ids
                or self.uncertainty_role != "SOURCE_REPORTED_SD_NOT_CALIBRATED_JOINT_PRECISION"):
            raise ValueError("endpoint counts cannot invent biological n, pairing or joint precision")
        missing = self.count_cell.token == "n.m."
        expected_role = ("MISSING_NOT_MEASURED" if missing else "SOURCE_REPORTED_DERIVED_RATIO"
                         if self.kind == "CARBOXYLATION_EFFICIENCY_AIR" else "SOURCE_REPORTED_MEASURED")
        if self.role != expected_role:
            raise ValueError("McDonald2026 quantity has an incompatible measured/derived/missing role")
        if missing:
            if any(x is not None for x in (self.mean_cell, self.sd_cell, self.sem_cell,
                                          self.mean, self.sd, self.measurement_count)) or self.raw_values:
                raise ValueError("missing specificity cannot acquire inferred observations")
        else:
            if any(x is None for x in (self.mean_cell, self.sd_cell, self.sem_cell)):
                raise ValueError("measured quantity needs exact native mean/error cells")
            if (self.mean is None or self.sd is None or self.mean != _number(self.mean_cell.token)
                    or self.sd != _number(self.sd_cell.token, nonnegative=True)
                    or not re.fullmatch(r"[1-9][0-9]{0,3}", _token(self.count_cell))
                    or type(self.measurement_count) is not int
                    or self.measurement_count != int(self.count_cell.token)):
                raise ValueError("McDonald2026 quantity differs from native source caches/count")
        for value in self.raw_values:
            if value.group_cell.token != self.source_group or value.worksheet != S4_SHEETS[0]:
                raise ValueError("raw endpoint group differs from the exact native construct join")
        for summary, original in ((self.summary_mean_cell, self.mean_cell), (self.summary_sd_cell, self.sd_cell)):
            if summary is not None and (original is None or summary.token != original.token
                    or summary.formula not in (None, f"'{S4_SHEETS[0]}'!{original.address}")):
                raise ValueError("McDonald2026 summary differs from its native formula/cache lineage")
        sem = _number(self.sem_cell.token, nonnegative=True) if self.sem_cell else None
        diagnostics = _diagnostics(self.mean, self.sd, sem, self.measurement_count, self.raw_values)
        if (self.recomputed_raw_mean, self.recomputed_raw_sample_sd, self.diagnostic_flags) != diagnostics:
            raise ValueError("McDonald2026 raw/cache diagnostics differ from retained operands")


@dataclass(frozen=True, slots=True)
class NativePlasmidCDSV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/mcdonald2026-plasmid-cds"
    plasmid_name_cell: NativeWorkbookCellV1
    plasmid_dna_cell: NativeWorkbookCellV1
    start_1based: int
    end_1based_including_stop: int
    translated_protein: str
    strand: str = "+"

    def __post_init__(self) -> None:
        if (self.strand != "+" or type(self.start_1based) is not int
                or type(self.end_1based_including_stop) is not int
                or not 1 <= self.start_1based < self.end_1based_including_stop <= len(_token(self.plasmid_dna_cell))
                or not re.fullmatch(r"[ACGTacgt]{1,20000}", _token(self.plasmid_dna_cell))):
            raise ValueError("native plasmid CDS has unsupported source boundaries/alphabet")
        dna = self.plasmid_dna_cell.token[self.start_1based - 1:self.end_1based_including_stop].upper()
        if _translate_complete_cds(dna) != self.translated_protein:
            raise ValueError("native CDS translation differs from its exact source DNA cell")


@dataclass(frozen=True, slots=True)
class PlantProteinRecipeV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/mcdonald2026-protein-recipe"
    native_name: str
    immediate_parent_lsu: str
    translated_ssu: str
    edit: str | None
    translated_lsu: str
    evidence_role: str = "SOURCE_DERIVED_AMINO_ACID_RECIPE_NOT_DEPOSITED_MUTANT_DNA"
    mutant_dna: str | None = None
    observed_terminal_processing_verified: bool = False
    assembly_view: str = "BACTERIAL_RECOMBINANT_TRANSLATED_RECIPE"

    def __post_init__(self) -> None:
        if (len(self.immediate_parent_lsu) != 477 or self.immediate_parent_lsu[368] != "A"
                or len(self.translated_ssu) != 123
                or not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]+", self.immediate_parent_lsu + self.translated_ssu)):
            raise ValueError("biochemical recipe requires the exact A369 LSU/123-aa SSU background")
        expected = self.immediate_parent_lsu
        if self.edit is not None:
            match = re.fullmatch(r"([ACDEFGHIKLMNPQRSTVWY])([1-9][0-9]{0,2})([ACDEFGHIKLMNPQRSTVWY])", self.edit)
            if match is None or not 1 <= int(match[2]) <= 477:
                raise ValueError("source-derived substitution has an unsupported amino-acid recipe")
            position = int(match[2]) - 1
            if expected[position] != match[1] or match[1] == match[3]:
                raise ValueError("source-derived edit differs from the immediate parent or makes no change")
            expected = expected[:position] + match[3] + expected[position + 1:]
        if (self.translated_lsu != expected or self.native_name != "NtRbcL" + (f" {self.edit}" if self.edit else "")
                or self.evidence_role != "SOURCE_DERIVED_AMINO_ACID_RECIPE_NOT_DEPOSITED_MUTANT_DNA"
                or self.mutant_dna is not None or self.observed_terminal_processing_verified is not False
                or self.assembly_view != "BACTERIAL_RECOMBINANT_TRANSLATED_RECIPE"):
            raise ValueError("protein recipe cannot invent clone DNA, processing or plant assay equivalence")


@dataclass(frozen=True, slots=True)
class PlantContextV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/mcdonald2026-context"
    group_cell: NativeWorkbookCellV1
    name_cell: NativeWorkbookCellV1
    quantities: tuple[PlantQuantityV1, ...]
    protein_recipe: PlantProteinRecipeV1 | None
    table1_row: tuple[str, ...] | None
    context_role: str

    def __post_init__(self) -> None:
        if tuple(q.kind for q in self.quantities) != ("SPECIFICITY_CO", "KCAT_C", "KC_AIR", "CARBOXYLATION_EFFICIENCY_AIR"):
            raise ValueError("McDonald2026 context must preserve exactly four separate quantity roles")
        if any(q.source_group != self.group_cell.token for q in self.quantities):
            raise ValueError("context endpoints differ from native group identity")
        leaf = self.name_cell.token == "N. tabacum leaf"
        if (leaf and (self.protein_recipe is not None or self.table1_row is not None
                      or self.context_role != "LEAF_CONTROL_WITH_UNRESOLVED_COMPLEX_RECIPE")
                or not leaf and (self.protein_recipe is None or self.protein_recipe.native_name != self.name_cell.token
                                 or self.context_role != "BACTERIAL_RECOMBINANT_SOURCE_REPORTED")):
            raise ValueError("native context conflates leaf/plant and biochemical assembly views")

    @property
    def joint_complete(self) -> bool:
        return self.quantities[0].mean is not None and self.quantities[1].mean is not None

    def quantity(self, kind: str) -> PlantQuantityV1:
        matches = [q for q in self.quantities if q.kind == kind]
        if len(matches) != 1:
            raise ValueError("quantity is not an admitted measured or derived source role")
        return matches[0]


@dataclass(frozen=True, slots=True)
class NativeScreeningVariantV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/mcdonald2026-screening-variant"
    native_row: int
    mutation_cell: NativeWorkbookCellV1
    disposition_cell: NativeWorkbookCellV1 | None
    role: str = "SELECTION_OR_ENRICHMENT_NOT_INTRINSIC_KINETIC_LABELS"

    def __post_init__(self) -> None:
        if (type(self.native_row) is not int or self.mutation_cell.address != f"A{self.native_row}"
                or not re.fullmatch(r"[A-Z][0-9]+[A-Z]", _token(self.mutation_cell))
                or self.disposition_cell is not None and self.disposition_cell.address != f"M{self.native_row}"
                or self.role != "SELECTION_OR_ENRICHMENT_NOT_INTRINSIC_KINETIC_LABELS"):
            raise ValueError("screened variant must preserve native mutation/disposition, not invented kinetics")


def _cds(s8: NativeWorkbookV1, row: int, start: int, length: int) -> NativePlasmidCDSV1:
    sheet = s8.worksheets[0]
    name, dna = _cell(sheet, f"A{row}"), _cell(sheet, f"B{row}")
    end = start + 3 * (length + 1) - 1
    return NativePlasmidCDSV1(name, dna, start, end, _translate_complete_cds(_token(dna)[start - 1:end].upper()))


def _quantity(raw: NativeWorksheetV1, summary: NativeWorksheetV1, row: int, kind: str) -> PlantQuantityV1:
    group, value, count, mean_col, sd_col, sem_col, summary_col, error_col, unit = {
        "SPECIFICITY_CO": ("P", "Q", "T", "U", "V", "W", "F", "G", "dimensionless"),
        "KCAT_C": ("AB", "AC", "AF", "AG", "AH", "AI", "J", "K", "s^-1"),
        "KC_AIR": ("AN", "AO", "AR", "AS", "AT", "AU", "N", "O", "micromolar"),
        "CARBOXYLATION_EFFICIENCY_AIR": ("AZ", "BA", "BD", "BE", "BF", "BG", "R", "S", "mM^-1 s^-1"),
    }[kind]
    source_group = _token(_cell(raw, f"A{row}"))
    count_cell = _cell(raw, f"{count}{row}")
    missing = count_cell.token == "n.m."
    cells = {c.address: c for c in raw.cells}
    values = []
    for cell in raw.cells:
        match = re.fullmatch(value + r"([0-9]+)", cell.address)
        if match is not None and cell.token is not None:
            group_cell = cells.get(group + match[1])
            if group_cell is not None and group_cell.token == source_group:
                values.append(NativeRawEndpointValueV1(S4_SHEETS[0], group_cell, cell, _number(cell.token)))
    mean_cell = None if missing else _cell(raw, f"{mean_col}{row}")
    sd_cell = None if missing else _cell(raw, f"{sd_col}{row}")
    sem_cell = None if missing else _cell(raw, f"{sem_col}{row}")
    mean = _number(mean_cell.token) if mean_cell else None
    sd = _number(sd_cell.token, nonnegative=True) if sd_cell else None
    n = None if missing else int(_token(count_cell))
    computed_mean, computed_sd, flags = _diagnostics(
        mean, sd, _number(sem_cell.token, nonnegative=True) if sem_cell else None, n, tuple(values),
    )
    return PlantQuantityV1(
        kind, unit, "MISSING_NOT_MEASURED" if missing else "SOURCE_REPORTED_DERIVED_RATIO"
        if kind == "CARBOXYLATION_EFFICIENCY_AIR" else "SOURCE_REPORTED_MEASURED",
        source_group, mean_cell, sd_cell, sem_cell, count_cell,
        _cell(summary, f"{summary_col}{row}") if row <= 12 else None,
        _cell(summary, f"{error_col}{row}") if row <= 12 else None,
        mean, sd, n, tuple(values), computed_mean, computed_sd, flags,
    )


def _contexts(article: NativePlantArticleV1, s4: NativeWorkbookV1, lsu: str, ssu: str) -> tuple[PlantContextV1, ...]:
    raw, summary = s4.worksheets
    rows = []
    for row, name in enumerate(CONTEXT_NAMES, 3):
        if _token(_cell(raw, f"B{row}")) != name or _token(_cell(raw, f"A{row}")) != str(row - 2):
            raise ValueError("McDonald2026 complete source roster or construct identity differs")
        recipe = None
        if row < 14:
            edit = name.split(" ")[1] if " " in name else None
            sequence = lsu
            if edit is not None:
                match = re.fullmatch(r"([A-Z])([0-9]+)([A-Z])", edit)
                position = int(match[2]) - 1
                if sequence[position] != match[1]:
                    raise ValueError("published substitution differs from its immediate parent")
                sequence = sequence[:position] + match[3] + sequence[position + 1:]
            recipe = PlantProteinRecipeV1(name, lsu, ssu, edit, sequence)
        rows.append(PlantContextV1(
            _cell(raw, f"A{row}"), _cell(raw, f"B{row}"),
            tuple(_quantity(raw, summary, row, kind) for kind in (
                "SPECIFICITY_CO", "KCAT_C", "KC_AIR", "CARBOXYLATION_EFFICIENCY_AIR")),
            recipe, article.table1_cells[row - 2] if row <= 12 else None,
            "LEAF_CONTROL_WITH_UNRESOLVED_COMPLEX_RECIPE" if row == 14 else "BACTERIAL_RECOMBINANT_SOURCE_REPORTED",
        ))
    return tuple(rows)


def _screening(s5: NativeWorkbookV1) -> tuple[NativeScreeningVariantV1, ...]:
    sheet = s5.worksheets[0]
    cells = {c.address: c for c in sheet.cells}
    return tuple(NativeScreeningVariantV1(row, cells[f"A{row}"], cells.get(f"M{row}"))
                 for row in sheet.row_ids if f"A{row}" in cells and re.fullmatch(
                     r"[A-Z][0-9]+[A-Z]", cells[f"A{row}"].token or ""))


@dataclass(frozen=True, slots=True)
class Mcdonald2026PanelV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/mcdonald2026-panel"
    article: NativePlantArticleV1
    s4: NativeWorkbookV1
    s5: NativeWorkbookV1
    s8: NativeWorkbookV1
    parent_lsu: NativePlasmidCDSV1
    parent_ssu: NativePlasmidCDSV1
    tagged_ssu: NativePlasmidCDSV1
    plant_fusion: NativePlasmidCDSV1
    declared_ssu_cleavage_product: str
    contexts: tuple[PlantContextV1, ...]
    screened_variants: tuple[NativeScreeningVariantV1, ...]
    limitations: tuple[str, ...] = LIMITS
    exposure: str = "EXPOSED_SOURCE_REPORTED_PANEL"
    biological_independent_n: int | None = None
    endpoint_preparation_pairing: str = "UNRESOLVED"
    plant_endogenous_ssu_census: tuple[str, ...] | None = None
    processing_role: str = "DECLARED_CLEAVAGE_SEQUENCE_CONSEQUENCE_NOT_MEASURED_TERMINUS"
    metrology_role: str = "LITERAL_SOURCE_METHOD_RECONSTRUCTION_UNRESOLVED"

    def __post_init__(self) -> None:
        _sealed_workbook(self.s4, S4_SHA256, S4_FINGERPRINT, S4_SHEETS)
        _sealed_workbook(self.s5, S5_SHA256, S5_FINGERPRINT, S5_SHEETS)
        _sealed_workbook(self.s8, S8_SHA256, S8_FINGERPRINT, S8_SHEETS)
        if self.article.fingerprint() != ARTICLE_FINGERPRINT:
            raise ValueError("native article projection is not admitted")
        expected_cds = (_cds(self.s8, 2, 4021, 477), _cds(self.s8, 2, 5699, 123),
                        _cds(self.s8, 5, 236, 219), _cds(self.s8, 6, 5354, 540))
        if (self.parent_lsu, self.parent_ssu, self.tagged_ssu, self.plant_fusion) != expected_cds:
            raise ValueError("parent/background/taggedSSU/plantfusion projection differs from native S8")
        if (self.declared_ssu_cleavage_product != self.tagged_ssu.translated_protein[96:]
                or self.declared_ssu_cleavage_product != self.parent_ssu.translated_protein
                or self.parent_lsu.translated_protein[368] != "A"
                or self.plant_fusion.translated_protein[57 + 368] != "V"
                or not self.plant_fusion.translated_protein.endswith("HHHHHH")):
            raise ValueError("native biochemical background or declared cleavage/plant view differs")
        if self.contexts != _contexts(self.article, self.s4, self.parent_lsu.translated_protein, self.parent_ssu.translated_protein):
            raise ValueError("source context or coherent endpoint/recipe projection differs from native cells")
        if self.screened_variants != _screening(self.s5):
            raise ValueError("complete screening denominator/dispositions differ from native S5")
        if (len(self.contexts) != 12 or sum(c.joint_complete for c in self.contexts) != 11
                or len(self.screened_variants) != 949 or sum(
                    v.disposition_cell is not None and v.disposition_cell.token == "Selected for rescreening"
                    for v in self.screened_variants) != 20):
            raise ValueError("native measured/missing or screened source census differs")
        if (self.limitations != LIMITS or self.exposure != "EXPOSED_SOURCE_REPORTED_PANEL"
                or self.biological_independent_n is not None or self.endpoint_preparation_pairing != "UNRESOLVED"
                or self.plant_endogenous_ssu_census is not None
                or self.processing_role != "DECLARED_CLEAVAGE_SEQUENCE_CONSEQUENCE_NOT_MEASURED_TERMINUS"
                or self.metrology_role != "LITERAL_SOURCE_METHOD_RECONSTRUCTION_UNRESOLVED"):
            raise ValueError("source panel cannot promote freshness, biological n, processing, transport or metrology")

    def context(self, name: str) -> PlantContextV1:
        matches = [c for c in self.contexts if c.name_cell.token == name]
        if len(matches) != 1:
            raise ValueError("context is not admitted exactly once in the complete native roster")
        return matches[0]


def decode_mcdonald2026(article_xml: bytes, s4_xlsx: bytes, s5_xlsx: bytes, s8_xlsx: bytes) -> Mcdonald2026PanelV1:
    """Pure exact-byte source admission; callers own bounded I/O and custody."""
    article = _article(article_xml)
    s4 = decode_native_workbook(s4_xlsx, expected_sha256=S4_SHA256, selected_sheets=S4_SHEETS)
    s5 = decode_native_workbook(s5_xlsx, expected_sha256=S5_SHA256, selected_sheets=S5_SHEETS)
    s8 = decode_native_workbook(s8_xlsx, expected_sha256=S8_SHA256, selected_sheets=S8_SHEETS)
    lsu, ssu, tagged, plant = (_cds(s8, 2, 4021, 477), _cds(s8, 2, 5699, 123),
                               _cds(s8, 5, 236, 219), _cds(s8, 6, 5354, 540))
    return Mcdonald2026PanelV1(article, s4, s5, s8, lsu, ssu, tagged, plant, tagged.translated_protein[96:],
                             _contexts(article, s4, lsu.translated_protein, ssu.translated_protein), _screening(s5))
