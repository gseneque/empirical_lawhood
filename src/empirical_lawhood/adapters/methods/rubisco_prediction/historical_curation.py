# SPDX-License-Identifier: MPL-2.0
"""Selected historical source cells and nested calibration roles.

This additive stock is exposed source curation. Published errors, preparation
counts and paired table columns do not create paired sample identities,
covariance, a candidate-domain model or independent calibration units.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import ClassVar

from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import (
    NativeArticleParagraphV1, NativeHTMLCellV1,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

SOURCES = {
    "spreitzer2005": ("10.1073/pnas.0508042102", "6341e81481cf81db96a44533be83971b407f1fc5fcaed559a827d0a2ff09e86c"),
    "genkov2009": ("10.1074/jbc.M109.044081", "865aacfbf37c0b7ef5b467649c0fa4bb5da60390a126e0a71e5f99ce584598e5"),
    "zhou2014": ("10.1007/s13238-014-0072-x", "9ef682ed154bcae7e390965eacd5f412c69ea6dfeccdfb84259b4505b3fbf025"),
}
TABLE_ROWS = {
    "spreitzer2005": (("tbl1", (5,) * 4, 1), ("tbl2", (12,) * 6, 1), ("tbl3", (12,) * 4, 1)),
    "genkov2009": (("T1", (4, 3, 4, *(6,) * 10), 3), ("T2", (8,) * 9, 2)),
    "zhou2014": (("Tab1", (6,) * 3, 1),),
}
# Exact canonical native projections are pinned after reading the held originals.
ARTICLE_FINGERPRINTS = {
    "spreitzer2005": "54ef1f2d2ffa2f67311525f869c3ae17e4fcb3fda95234ebb554405ae94db5a5",
    "genkov2009": "461644826b882725e39914298de2987b165896b5f0566e44dbf2b41779af7230",
    "zhou2014": "e30e8f9c57eae7421a1cf7becf0e0e52e6aaea6f97de15c6305913bf21829081",
}
MISSING_JOINS = (
    "ACTIVE_SITE_METROLOGY_NOT_INDEPENDENTLY_JOINED",
    "CANDIDATE_GALDIERIA_SSU_DOMAIN_APPLICABILITY_UNASSESSED",
    "ENDPOINT_SAMPLE_IDENTITIES_AND_PAIRING_UNAVAILABLE",
    "FULL_ASSAY_MATERIAL_SEQUENCE_AND_PREPARATION_JOIN_UNVERIFIED",
    "JOINT_ENDPOINT_COVARIANCE_UNAVAILABLE",
    "NO_INDEPENDENT_CANDIDATE_CALIBRATION_UNITS_ESTABLISHED",
    "REPORTED_PREPARATION_COUNTS_DO_NOT_IDENTIFY_INDEPENDENT_MODEL_UNITS",
    "CROSS_PAPER_EXACT_PARENT_AND_HOMOLOGOUS_SITE_JOINS_UNVERIFIED",
)
CEILING = "EXPOSED_HISTORICAL_CURATION_NO_CANDIDATE_QUALIFICATION"


def _tuple(value, kind, *, minimum=0, maximum=10000):
    if type(value) is not tuple or not minimum <= len(value) <= maximum or any(type(x) is not kind for x in value):
        raise ValueError("historical curation needs bounded immutable typed operands")


@dataclass(frozen=True, slots=True)
class HistoricalNativeRow(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical-curation/native-row"
    ordinal_0based: int
    cells: tuple[NativeHTMLCellV1, ...]

    def __post_init__(self):
        if type(self.ordinal_0based) is not int or not 0 <= self.ordinal_0based < 128:
            raise ValueError("historical native row needs an exact ordinal")
        _tuple(self.cells, NativeHTMLCellV1, minimum=1, maximum=16)
        for cell in self.cells:
            cell.__post_init__()


@dataclass(frozen=True, slots=True)
class HistoricalNativeTable(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical-curation/native-table"
    table_id: str
    rows: tuple[HistoricalNativeRow, ...]
    header_rows: int

    def __post_init__(self):
        if self.table_id not in {entry[0] for roster in TABLE_ROWS.values() for entry in roster}:
            raise ValueError("historical table needs its exact native source identifier")
        _tuple(self.rows, HistoricalNativeRow, minimum=1, maximum=128)
        if type(self.header_rows) is not int or not 1 <= self.header_rows < len(self.rows):
            raise ValueError("historical table needs explicit native headers")
        if tuple(r.ordinal_0based for r in self.rows) != tuple(range(len(self.rows))):
            raise ValueError("historical table changes its full native row census")
        for row in self.rows:
            row.__post_init__()


@dataclass(frozen=True, slots=True)
class HistoricalNativeArticle(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical-curation/native-article"
    source_id: str
    doi: str
    source_sha256: str
    tables: tuple[HistoricalNativeTable, ...]
    paragraphs: tuple[NativeArticleParagraphV1, ...]
    exposure: str = CEILING

    def __post_init__(self):
        if self.source_id not in SOURCES or (self.doi, self.source_sha256) != SOURCES[self.source_id]:
            raise ValueError("historical article changes its selected original source")
        _tuple(self.tables, HistoricalNativeTable, minimum=1, maximum=3)
        expected = TABLE_ROWS[self.source_id]
        actual = tuple((t.table_id, tuple(len(r.cells) for r in t.rows), t.header_rows) for t in self.tables)
        if actual != expected or self.exposure != CEILING:
            raise ValueError("historical article changes its complete source-specific table census or ceiling")
        _tuple(self.paragraphs, NativeArticleParagraphV1, minimum=1, maximum=20000)
        if tuple(p.ordinal_0based for p in self.paragraphs) != tuple(range(len(self.paragraphs))):
            raise ValueError("historical article drops or reorders native prose")
        for item in (*self.tables, *self.paragraphs):
            item.__post_init__()
        if self.fingerprint() != ARTICLE_FINGERPRINTS[self.source_id]:
            raise ValueError("historical native article changes its exact complete cell/prose projection")

    @property
    def identity(self):
        return ObjectIdentity.from_record("historical-native." + self.source_id, self)


def reported_decimal_tokens(cell: NativeHTMLCellV1):
    """Interpret complete native text while separately retaining every spelling."""
    token = cell.text
    match = re.fullmatch(r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)(?:\s*±\s*([0-9]+(?:\.[0-9]+)?))?", token)
    if match is None:
        raise ValueError("historical quantity is not a supported complete native numeric token")
    mean_token, error_token = match.groups()
    return mean_token, error_token, Decimal(mean_token.replace(",", "")), Decimal(error_token) if error_token else None


@dataclass(frozen=True, slots=True)
class HistoricalQuantity(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical-curation/quantity"
    native_column_0based: int
    kind: str
    unit: str
    cell: NativeHTMLCellV1
    mean_token: str
    error_token: str | None
    reported_mean: Decimal
    reported_error: Decimal | None
    quantity_role: str
    error_role: str
    reported_count_lower: int | None
    reported_count_upper: int | None
    count_role: str

    def __post_init__(self):
        if type(self.native_column_0based) is not int or not 1 <= self.native_column_0based <= 15:
            raise ValueError("historical quantity must retain its native column")
        if type(self.cell) is not NativeHTMLCellV1:
            raise ValueError("historical quantity needs its original typed cell")
        self.cell.__post_init__()
        if type(self.reported_mean) is not Decimal or self.reported_error is not None and type(self.reported_error) is not Decimal:
            raise ValueError("historical quantities need exact Decimal interpretations")
        if (self.mean_token, self.error_token, self.reported_mean, self.reported_error) != reported_decimal_tokens(self.cell):
            raise ValueError("historical quantity changes a native Decimal spelling/value/error")
        if self.quantity_role not in {"REPORTED_MEASURED_SUMMARY", "REPORTED_TURNOVER_NORMALIZATION_UNVERIFIED",
                                      "SOURCE_CALCULATED", "COPIED_FROM_SAME_PAPER_TABLE1"}:
            raise ValueError("historical quantity needs an explicit measured, reported or derived role")
        if self.error_role not in {"PUBLISHED_SD_NOT_JOINT_UNCERTAINTY", "NOT_REPORTED_FOR_CALCULATED_VALUE"}:
            raise ValueError("historical error role is unsupported")
        if self.error_role == "NOT_REPORTED_FOR_CALCULATED_VALUE":
            if self.reported_error is not None or (self.reported_count_lower, self.reported_count_upper) != (None, None):
                raise ValueError("calculated historical values cannot invent errors or sample counts")
        elif self.reported_error is None or any(type(x) is not int or x < 1 for x in (self.reported_count_lower, self.reported_count_upper)):
            raise ValueError("published SD needs its source-reported bounded count")
        if self.reported_count_lower is not None and self.reported_count_lower > self.reported_count_upper:
            raise ValueError("historical preparation count bounds are reversed")


@dataclass(frozen=True, slots=True)
class HistoricalRecipe(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical-curation/recipe"
    material_background: str
    small_subunit_role: str
    large_subunit_edits: tuple[str, ...]
    small_subunit_edits: tuple[str, ...]
    material_paragraphs: tuple[NativeArticleParagraphV1, ...]
    assay_paragraphs: tuple[NativeArticleParagraphV1, ...]
    reported_assay_temperature_c: Decimal
    gas_recipe_role: str
    normalization_role: str = "SOURCE_REPORTED_NO_INDEPENDENT_ACTIVE_SITE_METROLOGY_JOIN"
    full_sequence_join: ObjectIdentity | None = None

    def __post_init__(self):
        for edits in (self.large_subunit_edits, self.small_subunit_edits):
            _tuple(edits, str, maximum=5)
            if len(set(edits)) != len(edits) or any(re.fullmatch(r"[A-Z][1-9][0-9]{0,3}[A-Z]", e) is None for e in edits):
                raise ValueError("historical substitution recipes need explicit source-reported sites")
        for prose in (self.material_paragraphs, self.assay_paragraphs):
            _tuple(prose, NativeArticleParagraphV1, minimum=1, maximum=32)
            for paragraph in prose:
                paragraph.__post_init__()
        if type(self.reported_assay_temperature_c) is not Decimal or self.reported_assay_temperature_c != Decimal("25") or self.full_sequence_join is not None:
            raise ValueError("selected historical recipes cannot invent temperature or verified sequence joins")
        if self.normalization_role != "SOURCE_REPORTED_NO_INDEPENDENT_ACTIVE_SITE_METROLOGY_JOIN":
            raise ValueError("historical recipes cannot invent active-site metrology")


@dataclass(frozen=True, slots=True)
class HistoricalGroup(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical-curation/group"
    role: str
    group_id: str

    def __post_init__(self):
        if self.role not in {"paper", "shared-parent", "assay-series", "site-background"}:
            raise ValueError("historical nested grouping role is unsupported")
        validate_stable_id(self.group_id)


@dataclass(frozen=True, slots=True)
class HistoricalContext(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical-curation/context"
    context_id: str
    native_table_id: str
    native_row: HistoricalNativeRow
    quantities: tuple[HistoricalQuantity, ...]
    recipe: HistoricalRecipe
    groups: tuple[HistoricalGroup, ...]
    missing_roles: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.context_id)
        if type(self.native_row) is not HistoricalNativeRow or type(self.recipe) is not HistoricalRecipe:
            raise ValueError("historical context needs its full native row and source recipe")
        _tuple(self.quantities, HistoricalQuantity, minimum=1, maximum=15)
        if tuple(q.native_column_0based for q in self.quantities) != tuple(range(1, len(self.native_row.cells))):
            raise ValueError("historical context omits or duplicates a supplied quantity cell")
        if tuple(q.cell for q in self.quantities) != self.native_row.cells[1:]:
            raise ValueError("historical quantities differ from the full native row")
        _tuple(self.groups, HistoricalGroup, minimum=3, maximum=16)
        if len(set((g.role, g.group_id) for g in self.groups)) != len(self.groups):
            raise ValueError("historical context repeats a nested group")
        if self.missing_roles[:len(MISSING_JOINS)] != MISSING_JOINS:
            raise ValueError("historical context omits unresolved joint-calibration roles")
        for item in (*self.quantities, self.recipe, *self.groups):
            item.__post_init__()


@dataclass(frozen=True, slots=True)
class HistoricalVariantRole(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical-curation/variant-role"
    variant: str
    role: str
    source_paragraphs: tuple[NativeArticleParagraphV1, ...]
    native_context_ids: tuple[str, ...]

    def __post_init__(self):
        if not self.variant or self.role not in {"LISTED_ASSAY_CONTEXTS", "PURIFICATION_FAILURE_NO_KINETIC_ROW",
                                              "INITIAL_ASSAY_ONLY_NO_DEEP_KINETIC_ROW"}:
            raise ValueError("historical variant requires an explicit retained outcome role")
        _tuple(self.source_paragraphs, NativeArticleParagraphV1, minimum=1, maximum=16)
        _tuple(self.native_context_ids, str, maximum=8)
        if self.role == "PURIFICATION_FAILURE_NO_KINETIC_ROW" and self.native_context_ids:
            raise ValueError("failed purification cannot invent kinetic observations")


@dataclass(frozen=True, slots=True)
class HistoricalCuration(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical-curation/stock"
    curation_id: str
    native: HistoricalNativeArticle
    contexts: tuple[HistoricalContext, ...]
    variant_roles: tuple[HistoricalVariantRole, ...]
    missing_roles: tuple[str, ...] = MISSING_JOINS
    exposure: str = CEILING
    candidate_domain_qualification: str = "UNASSESSED"
    probability_of_joint_success: Decimal | None = None
    independent_calibration_units: int | None = None
    native_scientific_contacts: int = 0
    programme_predictive_status: str = "PRIOR_EXPOSED_PREDICTIVE_FAILURES_RETAINED_NOT_REASSESSED"

    def __post_init__(self):
        if type(self.native) is not HistoricalNativeArticle:
            raise ValueError("historical curation needs a pinned native article")
        self.native.__post_init__()
        validate_stable_id(self.curation_id)
        if self.curation_id != "historical-curation." + self.native.source_id:
            raise ValueError("historical curation changes its source-specific identity")
        if self.native.fingerprint() != ARTICLE_FINGERPRINTS.get(self.native.source_id):
            raise ValueError("historical curation differs from the exact complete original cell/prose projection")
        _tuple(self.contexts, HistoricalContext, minimum=1, maximum=64)
        _tuple(self.variant_roles, HistoricalVariantRole, minimum=1, maximum=16)
        # Domain-owned source interpretation is independently recomputed from
        # the immutable native cells/prose, never accepted as caller assertions.
        from .historical_curation_sources import project_contexts, project_variant_roles
        if self.contexts != project_contexts(self.native) or self.variant_roles != project_variant_roles(self.native, self.contexts):
            raise ValueError("historical curation changes complete source roles, material/assay joins or nested groups")
        if (self.missing_roles != MISSING_JOINS or self.exposure != CEILING
                or self.candidate_domain_qualification != "UNASSESSED"
                or self.probability_of_joint_success is not None or self.independent_calibration_units is not None
                or type(self.native_scientific_contacts) is not int or self.native_scientific_contacts != 0
                or self.programme_predictive_status != "PRIOR_EXPOSED_PREDICTIVE_FAILURES_RETAINED_NOT_REASSESSED"):
            raise ValueError("historical curation cannot create calibration, probability or native authority")
        for item in (*self.contexts, *self.variant_roles):
            item.__post_init__()


def connected_context_groups(stocks: tuple[HistoricalCuration, ...]) -> tuple[tuple[str, ...], ...]:
    """Conservative connected groups for later declared grouped validation."""
    _tuple(stocks, HistoricalCuration, minimum=1, maximum=3)
    rows = tuple(row for stock in stocks for row in stock.contexts)
    if len({row.context_id for row in rows}) != len(rows):
        raise ValueError("historical grouping refuses duplicate source contexts")
    remaining = set(range(len(rows)))
    components = []
    keys = [{(g.role, g.group_id) for g in row.groups if g.role != "assay-series"} for row in rows]
    while remaining:
        selected = {min(remaining)}
        joined = set(keys[min(remaining)])
        while True:
            found = {i for i in remaining - selected if keys[i] & joined}
            if not found:
                break
            selected.update(found)
            for i in found:
                joined.update(keys[i])
        remaining.difference_update(selected)
        components.append(tuple(sorted(rows[i].context_id for i in selected)))
    return tuple(sorted(components))
