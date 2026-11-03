# SPDX-License-Identifier: MPL-2.0
"""Closed inert decoders/projectors for three already-held primary stocks.

No path, acquisition, fitting or native-science capability belongs here. Exact
original source digests precede parsing. All selected tables, headers, cells and
article paragraphs survive; scalar interpretation retains its native token.
"""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
from html.parser import HTMLParser
import re
import xml.etree.ElementTree as ET

from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import (
    NativeArticleParagraphV1, NativeHTMLCellV1,
)

from .historical_curation import (
    SOURCES, TABLE_ROWS, HistoricalContext, HistoricalCuration, HistoricalGroup,
    HistoricalNativeArticle, HistoricalNativeRow, HistoricalNativeTable,
    HistoricalQuantity, HistoricalRecipe, HistoricalVariantRole, MISSING_JOINS,
    reported_decimal_tokens,
)

_VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())


class _PrimaryHTML(HTMLParser):
    def __init__(self, source_id):
        super().__init__(convert_charrefs=True)
        self.selected = {table_id for table_id, _, _ in TABLE_ROWS[source_id]}
        self.stack = []
        self.nodes = 0
        self.dois = []
        self.tables = {}
        self.table = self.row = self.cell = self.paragraph = None
        self.paragraphs = []

    def handle_decl(self, decl):
        if decl.lower() != "doctype html":
            raise ValueError("historical HTML permits only the inert HTML5 doctype")

    def unknown_decl(self, decl):
        raise ValueError("historical HTML refuses declarations")

    def handle_starttag(self, tag, attrs):
        self.nodes += 1
        if self.nodes > 20000 or len(self.stack) >= 64 or len(attrs) > 64:
            raise ValueError("historical HTML exceeds its bounded structure")
        values = dict(attrs)
        if len(values) != len(attrs) or any(len(k.encode()) > 256 or (v is not None and len(v.encode()) > 8192) for k, v in attrs):
            raise ValueError("historical HTML attributes are duplicated or oversized")
        if tag == "meta" and values.get("name") == "citation_doi":
            self.dois.append(values.get("content"))
        if tag in _VOID:
            if tag == "br":
                if self.cell is not None:
                    self.cell[3].append("\n")
                if self.paragraph is not None:
                    self.paragraph[2].append("\n")
            return
        self.stack.append((tag, values.get("id")))
        scope = tuple(value for _, value in self.stack if value is not None)
        depth = len(self.stack)
        if tag == "table" and set(scope) & self.selected:
            matches = set(scope) & self.selected
            if len(matches) != 1 or self.table is not None or next(iter(matches)) in self.tables:
                raise ValueError("historical selected tables are nested or duplicated")
            self.table = (next(iter(matches)), depth, [])
        if tag == "tr" and self.table is not None:
            if self.row is not None:
                raise ValueError("historical rows are nested")
            self.row = (depth, [])
        if tag in {"th", "td"} and self.table is not None:
            if self.row is None or self.cell is not None:
                raise ValueError("historical cell has no unique native row")
            self.cell = (depth, tag, tuple(sorted((k, v or "") for k, v in attrs)), [])
        if tag == "p":
            if self.paragraph is not None:
                raise ValueError("historical paragraphs are nested")
            self.paragraph = (depth, scope or ("document",), [])

    def handle_endtag(self, tag):
        if tag in _VOID:
            return
        if not self.stack or self.stack[-1][0] != tag:
            raise ValueError("historical HTML is not explicitly balanced")
        depth = len(self.stack)
        if self.cell is not None and self.cell[0] == depth:
            _, native_tag, attrs, fragments = self.cell
            values = dict(attrs)
            if any(re.fullmatch(r"[1-9][0-9]?", values.get(k, "1")) is None for k in ("rowspan", "colspan")):
                raise ValueError("historical cell span is not an exact integer")
            self.row[1].append(NativeHTMLCellV1(native_tag, "".join(fragments), int(values.get("rowspan", "1")),
                                              int(values.get("colspan", "1")), attrs))
            self.cell = None
        if self.row is not None and self.row[0] == depth:
            self.table[2].append(HistoricalNativeRow(len(self.table[2]), tuple(self.row[1])))
            self.row = None
        if self.table is not None and self.table[1] == depth:
            self.tables[self.table[0]] = tuple(self.table[2])
            self.table = None
        if self.paragraph is not None and self.paragraph[0] == depth:
            self.paragraphs.append(NativeArticleParagraphV1(len(self.paragraphs), self.paragraph[1],
                                                          "".join(self.paragraph[2])))
            self.paragraph = None
        self.stack.pop()

    def handle_data(self, data):
        if self.cell is not None:
            self.cell[3].append(data)
        if self.paragraph is not None:
            self.paragraph[2].append(data)


def decode_primary(source_id: str, payload: bytes) -> HistoricalNativeArticle:
    if source_id not in SOURCES or type(payload) is not bytes or not 1 <= len(payload) <= 2 * 1024**2:
        raise ValueError("historical decoder needs one bounded selected original")
    doi, digest = SOURCES[source_id]
    if sha256(payload).hexdigest() != digest:
        raise ValueError("historical source differs from its exact held original digest")
    text = payload.decode("utf-8")
    if "\x00" in text or "<!ENTITY" in text.upper():
        raise ValueError("historical original contains unsupported NUL/entities")
    if source_id != "zhou2014":
        parser = _PrimaryHTML(source_id)
        parser.feed(text)
        parser.close()
        if parser.stack or parser.dois != [doi] or set(parser.tables) != parser.selected:
            raise ValueError("historical source DOI or complete selected table census differs")
        tables = tuple(HistoricalNativeTable(name, parser.tables[name], headers) for name, _, headers in TABLE_ROWS[source_id])
        paragraphs = tuple(parser.paragraphs)
    else:
        if "<!DOCTYPE" in text.upper():
            raise ValueError("historical XML refuses external document types")
        root = ET.fromstring(text)
        nodes = tuple(root.iter())
        if len(nodes) > 20000 or [x.text for x in root.findall("./front/article-meta/article-id") if x.get("pub-id-type") == "doi"] != [doi]:
            raise ValueError("historical XML node/DOI census differs")
        wraps = root.findall(".//table-wrap")
        if len(wraps) != 1 or wraps[0].get("id") != "Tab1":
            raise ValueError("historical XML changes its complete table census")
        rows = []
        for ordinal, row in enumerate(wraps[0].findall(".//tr")):
            cells = []
            for cell in row:
                if cell.tag not in {"th", "td"}:
                    raise ValueError("historical XML row has an unsupported native child")
                attrs = tuple(sorted(cell.attrib.items()))
                cells.append(NativeHTMLCellV1(cell.tag, "".join(cell.itertext()), int(cell.get("rowspan", "1")),
                                             int(cell.get("colspan", "1")), attrs))
            rows.append(HistoricalNativeRow(ordinal, tuple(cells)))
        tables = (HistoricalNativeTable("Tab1", tuple(rows), 1),)
        collected = []

        def visit(node, scope=(), depth=0):
            if depth > 64:
                raise ValueError("historical XML exceeds its depth bound")
            scope = (*scope, node.get("id")) if node.get("id") else scope
            if node.tag == "p":
                collected.append(NativeArticleParagraphV1(len(collected), scope or ("document",), "".join(node.itertext())))
            for child in node:
                visit(child, scope, depth + 1)

        visit(root)
        paragraphs = tuple(collected)
    return HistoricalNativeArticle(source_id, doi, digest, tables, paragraphs)


def _prose(article, ordinals):
    return tuple(article.paragraphs[i] for i in ordinals)


_PENTA = ("V221C", "V235I", "C256F", "K258R", "I265V")
_TRIPLE = _PENTA[2:]
_S_LSU = {"V235I": ("V235I",), "V221C/V235I": _PENTA[:2], "Triple": _TRIPLE,
          "Penta": _PENTA, "Penta/ABSO": _PENTA}


def _recipe(article, name):
    source = article.source_id
    if source == "spreitzer2005":
        background = "SPINACH_SOURCE_ENZYME" if name == "Spinach" else "CHLAMYDOMONAS_2137_OR_ISOGENIC_TRANSFORMANT_SOURCE_REPORTED"
        ssu = ("SPINACH_NATIVE_FAMILY_UNRESOLVED" if name == "Spinach" else
               "SINGLE_RBCS1_WITH_28AA_CHLAMYDOMONAS_LOOP_REPLACED_BY_22AA_SPINACH_LOOP" if "ABSO" in name else
               "RESIDENT_RBCS1_RBCS2_FAMILY")
        return HistoricalRecipe(background, ssu, _S_LSU.get(name, ()), (), _prose(article, (19, 20, 21, 30, 31)),
            _prose(article, (23, 25, 38, 39, 40, 41, 42, 43)), Decimal("25"),
            "SIMULTANEOUS_SPECIFICITY_COUNTS_WITH_REFERENCE_DEPENDENT_GAS_AND_RATE_DETAILS")
    if source == "genkov2009":
        return HistoricalRecipe("CHLAMYDOMONAS_RBCS_DELETION_RECONSTITUTED_WITH_PSS1_RBCS1", "SINGLE_RBCS1_SS1_CONTROL",
            (), () if name in {"Wild-type", "Wild-type SS1"} else (name,), _prose(article, (15, 16, 17, 18, 19)),
            _prose(article, (20, 29, 30, 32, 35, 36, 37)), Decimal("25"),
            "N2_O2_SOURCE_ASSAYS_AND_SIMULTANEOUS_SPECIFICITY_REFERENCE_DETAILS_UNRESOLVED")
    return HistoricalRecipe("SYNECHOCOCCUS_PCC7002_RBCL_RBCX_RBCS_PET30A_ECOLI", "SOURCE_RBCS_WT_OR_E49V_D82G",
        (), ("E49V", "D82G") if name == "M6-5" else (), _prose(article, (21, 28, 32, 35)),
        _prose(article, (24, 27, 35, 36)), Decimal("25"), "ANAEROBIC_100_PERCENT_N2_NO_OXYGENATION_ASSAY")


def _columns(source, table):
    # Native unit spellings remain in the full headers. The Genkov Ko unit
    # printed as CO2 is explicitly unresolved rather than silently corrected.
    if source == "spreitzer2005":
        base = (("SPECIFICITY_CO", "dimensionless"), ("VC_MASS", "umol/h/mg"), ("KC", "uM-CO2"), ("KO", "uM-O2"))
        if table == "tbl1":
            return base
        return (*base[:2], ("KCAT_C", "s^-1"), *base[2:], ("VO_MASS", "umol/h/mg"), ("KCAT_O", "s^-1"),
                ("VC_OVER_KC", "source-native-ratio"), ("VO_OVER_KO", "source-native-ratio"),
                ("KO_OVER_KC", "dimensionless"), ("VC_OVER_VO", "dimensionless"))
    if source == "genkov2009":
        if table == "T1":
            return (("SPECIFICITY_CO", "dimensionless"), ("VC_N2_12.4MM_BICARBONATE", "umol-CO2/h/mg-protein"),
                    ("VC_N2_0.98MM_BICARBONATE", "umol-CO2/h/mg-protein"), ("VC_O2_0.98MM_BICARBONATE", "umol-CO2/h/mg-protein"),
                    ("ACTIVITY_N2_OVER_O2", "dimensionless"))
        return (("SPECIFICITY_CO", "dimensionless"), ("VC_MASS", "umol/h/mg"), ("KC", "uM-CO2"),
                ("KO", "source-printed-uM-CO2-unresolved"), ("VC_OVER_KC", "source-native-ratio"),
                ("KO_OVER_KC", "dimensionless"), ("VC_OVER_VO", "dimensionless"))
    return (("SPECIFIC_CARBOXYLATION_ACTIVITY", "U/mg"), ("KCAT_C", "s^-1"), ("KM_C", "umol/L"),
            ("KCAT_C_OVER_KM_C", "s^-1/(mmol/L)"), ("KM_RUBP", "umol/L"))


def project_contexts(article: HistoricalNativeArticle) -> tuple[HistoricalContext, ...]:
    article.__post_init__()
    source = article.source_id
    contexts = []
    for table in article.tables:
        for row in table.rows[table.header_rows:]:
            name = row.cells[0].text
            recipe = _recipe(article, name)
            quantities = []
            for col, ((kind, unit), cell) in enumerate(zip(_columns(source, table.table_id), row.cells[1:], strict=True), 1):
                mean_token, error_token, mean, error = reported_decimal_tokens(cell)
                derived = (source == "spreitzer2005" and table.table_id != "tbl1" and col >= 6
                           or source == "genkov2009" and col >= 5
                           or source == "zhou2014" and col == 4)
                role = "SOURCE_CALCULATED" if derived else "REPORTED_MEASURED_SUMMARY"
                if source == "genkov2009" and table.table_id == "T2" and col == 1:
                    role = "COPIED_FROM_SAME_PAPER_TABLE1"
                if not derived and kind == "KCAT_C":
                    role = "REPORTED_TURNOVER_NORMALIZATION_UNVERIFIED"
                lower = None if derived else 5 if source == "zhou2014" else 3
                upper = None if derived else 6 if source == "zhou2014" else 3
                quantities.append(HistoricalQuantity(col, kind, unit, cell, mean_token, error_token, mean, error, role,
                    "NOT_REPORTED_FOR_CALCULATED_VALUE" if derived else "PUBLISHED_SD_NOT_JOINT_UNCERTAINTY", lower, upper,
                    "NOT_REPORTED" if derived else "INDEPENDENT_EXPERIMENTS_SOURCE_REPORTED_NO_SAMPLE_IDS" if source == "zhou2014"
                    else "THREE_SEPARATE_ENZYME_PREPARATIONS_SOURCE_REPORTED_NO_SAMPLE_IDS"))
            groups = [HistoricalGroup("paper", source), HistoricalGroup("shared-parent", source + "." +
                ("spinach" if name == "Spinach" else "same-parent-background")),
                HistoricalGroup("assay-series", source + "." + table.table_id.lower())]
            for subunit, edits in (("lsu", recipe.large_subunit_edits), ("ssu", recipe.small_subunit_edits)):
                for edit in edits:
                    groups.append(HistoricalGroup("site-background", source + "." + subunit + ".site" + edit[1:-1]))
            if "ABSO" in name:
                groups.append(HistoricalGroup("site-background", source + ".ssu.native-loop-replacement"))
            missing = MISSING_JOINS
            if source == "genkov2009":
                missing += ("NO_ACTIVE_SITE_TURNOVER_COLUMN", "KO_NATIVE_HEADER_PRINTS_CO2_UNRESOLVED")
                if table.table_id == "T2":
                    missing += ("TABLE2_SPECIFICITY_REUSES_TABLE1_SUMMARY",)
            elif source == "zhou2014":
                missing += ("SPECIFICITY_AND_OXYGENATION_UNREPORTED", "SINGLE_MUTANT_CORNERS_E49V_D82G_UNREPORTED",
                            "ACTIVITY_SCREEN_SELECTED_MUTANT_HISTORICALLY_EXPOSED")
            elif table.table_id == "tbl1":
                missing += ("NO_REPORTED_TURNOVER_CELL_IN_THIS_SERIES",)
            if source == "spreitzer2005":
                missing += ("SINGLE_V221C_CORNER_UNREPORTED", "TRIPLE_ABSO_CORNER_UNREPORTED")
            contexts.append(HistoricalContext(f"{source}.{table.table_id.lower()}.row{row.ordinal_0based}", table.table_id,
                row, tuple(quantities), recipe, tuple(groups), missing))
    return tuple(contexts)


def _variant(source, native_name):
    if source == "spreitzer2005" and native_name in {"Wild type", "Chlamydomonas"}:
        return "Chlamydomonas wild type"
    if source == "genkov2009" and native_name in {"Wild-type", "Wild-type SS1"}:
        return "Wild-type SS1"
    return native_name


def project_variant_roles(article, contexts):
    source = article.source_id
    by_name = {}
    for row in contexts:
        name = _variant(source, row.native_row.cells[0].text)
        by_name.setdefault(name, []).append(row.context_id)
    if source == "genkov2009":
        names = ("Wild-type SS1", "S16A", "L18A", "P19A", "Y32A", "E43A", "W73A", "L78A", "P79A", "F81A", "E92A")
    else:
        names = tuple(by_name)
    roles = []
    for name in names:
        role = ("PURIFICATION_FAILURE_NO_KINETIC_ROW" if source == "genkov2009" and name == "L18A" else
                "INITIAL_ASSAY_ONLY_NO_DEEP_KINETIC_ROW" if source == "genkov2009" and name in {"S16A", "P19A", "E92A"}
                else "LISTED_ASSAY_CONTEXTS")
        ordinals = ((15, 16, 17, 18, 21, 27, 30) if source == "genkov2009" else
                    (19, 20, 27, 30, 31, 37, 41) if source == "spreitzer2005" else (21, 24, 27, 28))
        roles.append(HistoricalVariantRole(name, role, _prose(article, ordinals), tuple(by_name.get(name, ()))))
    return tuple(roles)


def curate_primary(article: HistoricalNativeArticle) -> HistoricalCuration:
    contexts = project_contexts(article)
    return HistoricalCuration("historical-curation." + article.source_id, article, contexts, project_variant_roles(article, contexts))
