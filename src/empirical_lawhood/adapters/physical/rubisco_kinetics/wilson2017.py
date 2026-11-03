"""Lossless primary Table 1 and verified Te amino-acid specifications.

The source denominator is nineteen enzymes: fifteen Te and four Se. Deposited
MG000148.1 supplies the Te parent LSU/SSU sequences; published substitutions
specify derived protein sequences. No mutant nucleotide bytes, new biological
measurements, calibrated joint uncertainty or cross-background transport are
created by this exposed source projection.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from html.parser import HTMLParser
import re
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id

from .genbank import NativeTeParentConstructV1
from .records import ReportedSubstitutionV1

DOI = "10.1074/jbc.M117.810861"
SOURCE_SHA256 = "102a96a551bf11104b7ca7563572010adf8dc540a937165c671f23c618a24316"
MAX_HTML_BYTES = 2 * 1024**2
MAX_HTML_NODES = 20000
MAX_HTML_DEPTH = 64
MAX_TABLE_ROWS = 128
MAX_CELL_BYTES = 4096
_VOID_TAGS = frozenset("area base br col embed hr img input link meta param source track wbr".split())


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True, slots=True)
class NativeHTMLCellV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-html-table-cell"
    native_tag: str
    raw_text: str
    rowspan: int
    colspan: int
    attributes: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if self.native_tag not in {"th", "td"} or len(self.raw_text.encode()) > MAX_CELL_BYTES:
            raise ValueError("native HTML cell tag/text exceeds its bounds")
        if type(self.rowspan) is not int or type(self.colspan) is not int or not 1 <= self.rowspan <= 4 or not 1 <= self.colspan <= 10:
            raise ValueError("native HTML cell span exceeds the reviewed table bounds")
        if self.attributes != tuple(sorted(self.attributes)) or len(dict(self.attributes)) != len(self.attributes) or len(self.attributes) > 16:
            raise ValueError("native HTML cell attributes must have a bounded unique order")
        attrs = dict(self.attributes)
        if attrs.get("rowspan", "1") != str(self.rowspan) or attrs.get("colspan", "1") != str(self.colspan):
            raise ValueError("native HTML spans differ from the retained source attributes")

    @property
    def text(self) -> str:
        return _normalized(self.raw_text)


@dataclass(frozen=True, slots=True)
class NativeHTMLTableRowV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-html-table-row"
    ordinal_0based: int
    cells: tuple[NativeHTMLCellV1, ...]

    def __post_init__(self) -> None:
        if type(self.ordinal_0based) is not int or not 0 <= self.ordinal_0based < MAX_TABLE_ROWS or not 1 <= len(self.cells) <= 10:
            raise ValueError("native table row dimensions exceed the reviewed source bounds")

    @property
    def texts(self) -> tuple[str, ...]:
        return tuple(c.text for c in self.cells)


@dataclass(frozen=True, slots=True)
class NativeArticleParagraphV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-article-paragraph"
    ordinal_0based: int
    native_scope_ids: tuple[str, ...]
    raw_text: str

    def __post_init__(self) -> None:
        if type(self.ordinal_0based) is not int or not 0 <= self.ordinal_0based < MAX_HTML_NODES or len(self.raw_text.encode()) > 32768:
            raise ValueError("native article paragraph exceeds its ordinal/text bound")
        if not self.native_scope_ids or len(self.native_scope_ids) > MAX_HTML_DEPTH or any(len(s.encode()) > 256 for s in self.native_scope_ids):
            raise ValueError("native article paragraph must retain bounded source scopes")

    @property
    def text(self) -> str:
        return _normalized(self.raw_text)


@dataclass(frozen=True, slots=True)
class NativeWilsonTableV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-wilson2017-table"
    source_sha256: str
    doi: str
    native_locator: str
    rows: tuple[NativeHTMLTableRowV1, ...]
    paragraphs: tuple[NativeArticleParagraphV1, ...]
    exposure: str = "EXPOSED_RETROSPECTIVE_PRIMARY_SOURCE"

    def __post_init__(self) -> None:
        validate_sha256(self.source_sha256)
        if self.doi != DOI or self.native_locator != "section#T1/table" or not 4 <= len(self.rows) <= MAX_TABLE_ROWS:
            raise ValueError("primary table DOI/locator/roster differs from the reviewed source")
        if tuple(r.ordinal_0based for r in self.rows) != tuple(range(len(self.rows))):
            raise ValueError("primary table must retain its complete ordered native row census")
        if self.exposure != "EXPOSED_RETROSPECTIVE_PRIMARY_SOURCE":
            raise ValueError("public source decoding cannot create prospective eligibility")


class _TableParser(HTMLParser):
    def __init__(self, *, target_section_id="T1"):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.nodes = 0
        self.dois = []
        self.target_sections = 0
        self.target_tables = 0
        self.table_depth = None
        self.row_depth = None
        self.cell_depth = None
        self.cell_tag = None
        self.cell_attrs = ()
        self.cell_fragments = []
        self.row_cells = []
        self.rows = []
        self.paragraph_ordinal = -1
        self.paragraph_depth = None
        self.paragraph_scope = ()
        self.paragraph_fragments = []
        self.paragraphs = []
        self.target_section_id = target_section_id

    def handle_decl(self, declaration):
        if declaration.lower() != "doctype html":
            raise ValueError("only the inert HTML5 doctype is supported; declarations/entities are forbidden")

    def unknown_decl(self, declaration):
        raise ValueError("unsupported HTML declaration")

    def handle_starttag(self, tag, attrs):
        self.nodes += 1
        if self.nodes > MAX_HTML_NODES or len(self.stack) >= MAX_HTML_DEPTH:
            raise ValueError("source HTML exceeds its bounded structure")
        if len(attrs) > 64 or len(dict(attrs)) != len(attrs) or any(len(k.encode()) > 256 or (v is not None and len(v.encode()) > 8192) for k, v in attrs):
            raise ValueError("source HTML attributes are duplicated or exceed their bounds")
        values = dict(attrs)
        if tag == "meta" and values.get("name") == "citation_doi":
            self.dois.append(values.get("content"))
        if tag in _VOID_TAGS:
            if tag == "br" and self.cell_depth is not None:
                self.cell_fragments.append("\n")
            return
        self.stack.append((tag, values.get("id")))
        scope = tuple(identity for _, identity in self.stack if identity is not None)
        if tag == "section" and values.get("id") == self.target_section_id:
            self.target_sections += 1
        if tag == "table" and self.target_section_id in scope:
            self.target_tables += 1
            if self.table_depth is not None:
                raise ValueError("nested target tables are forbidden")
            self.table_depth = len(self.stack)
        if tag == "tr" and self.table_depth is not None:
            if self.row_depth is not None:
                raise ValueError("nested native table rows are ambiguous")
            self.row_depth = len(self.stack)
            self.row_cells = []
        if tag in {"th", "td"} and self.table_depth is not None:
            if self.row_depth is None or self.cell_depth is not None:
                raise ValueError("native table cell is outside its unique source row")
            self.cell_depth = len(self.stack)
            self.cell_tag = tag
            self.cell_attrs = tuple(sorted((key, value or "") for key, value in attrs))
            self.cell_fragments = []
        if tag == "p":
            self.paragraph_ordinal += 1
            if set(scope) & {self.target_section_id, "sec14", "sec16", "F3"}:
                if self.paragraph_depth is not None:
                    raise ValueError("nested selected native paragraphs are ambiguous")
                self.paragraph_depth = len(self.stack)
                self.paragraph_scope = scope
                self.paragraph_fragments = []

    def handle_endtag(self, tag):
        if tag in _VOID_TAGS:
            return
        if not self.stack or self.stack[-1][0] != tag:
            raise ValueError("source HTML tags are not explicitly balanced within the selected profile")
        depth = len(self.stack)
        if depth == self.cell_depth:
            fields = dict(self.cell_attrs)
            for name in ("rowspan", "colspan"):
                if re.fullmatch(r"[1-9][0-9]?", fields.get(name, "1")) is None:
                    raise ValueError("native cell span is not an exact bounded integer")
            self.row_cells.append(NativeHTMLCellV1(self.cell_tag, "".join(self.cell_fragments),
                int(fields.get("rowspan", "1")), int(fields.get("colspan", "1")), self.cell_attrs))
            self.cell_depth = None
        if depth == self.row_depth:
            self.rows.append(NativeHTMLTableRowV1(len(self.rows), tuple(self.row_cells)))
            if len(self.rows) > MAX_TABLE_ROWS:
                raise ValueError("native target table exceeds its complete row bound")
            self.row_depth = None
        if depth == self.table_depth:
            self.table_depth = None
        if depth == self.paragraph_depth:
            self.paragraphs.append(NativeArticleParagraphV1(self.paragraph_ordinal, self.paragraph_scope,
                                                            "".join(self.paragraph_fragments)))
            self.paragraph_depth = None
        self.stack.pop()

    def handle_data(self, data):
        if self.cell_depth is not None:
            self.cell_fragments.append(data)
        if self.paragraph_depth is not None:
            self.paragraph_fragments.append(data)


def decode_wilson2017_html(payload: bytes, *, expected_sha256: str) -> NativeWilsonTableV1:
    validate_sha256(expected_sha256)
    if not 1 <= len(payload) <= MAX_HTML_BYTES or sha256(payload).hexdigest() != expected_sha256:
        raise ValueError("primary HTML exceeds its byte bound or differs from exact custody")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("primary HTML must be UTF-8") from error
    if "\x00" in text or "<!ENTITY" in text.upper():
        raise ValueError("primary HTML NUL bytes/entity declarations are forbidden")
    parser = _TableParser()
    parser.feed(text)
    parser.close()
    if parser.stack or parser.target_sections != 1 or parser.target_tables != 1 or parser.dois != [DOI]:
        raise ValueError("primary source DOI, balanced target section or unique table differs")
    return NativeWilsonTableV1(expected_sha256, DOI, "section#T1/table", tuple(parser.rows), tuple(parser.paragraphs))


@dataclass(frozen=True, slots=True)
class NativeReplicationDescriptorV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-replication-descriptor"
    native_token: str
    biological_minimum: int
    biological_maximum: int
    technical_replicates: int | None
    scope: str = "COLUMN_LEVEL_RANGE_NOT_PER_ENZYME_COUNTS_OR_JOINT_PAIRING"

    def __post_init__(self) -> None:
        if (self.biological_minimum, self.biological_maximum, self.technical_replicates) != _replication_counts(self.native_token):
            raise ValueError("replication bounds differ from their exact native token")
        if self.scope != "COLUMN_LEVEL_RANGE_NOT_PER_ENZYME_COUNTS_OR_JOINT_PAIRING":
            raise ValueError("column-level sample counts cannot invent per-enzyme joint units")


def _replication_counts(token: str) -> tuple[int, int, int | None]:
    match = re.fullmatch(r"([1-9][0-9]?)(?:–([1-9][0-9]?))?(?:,\s*([1-9][0-9]?))?", token)
    if match is None:
        raise ValueError("replication must retain the source biological/technical count token")
    minimum, maximum = int(match[1]), int(match[2] or match[1])
    if minimum > maximum:
        raise ValueError("native biological replication range is reversed")
    return minimum, maximum, int(match[3]) if match[3] else None


def _reported(token: str) -> tuple[Decimal | None, Decimal | None, str]:
    if token == "NM":
        return None, None, ""
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*±\s*([0-9]+(?:\.[0-9]+)?)(\*{0,2})", token)
    if match is None or len(token) > 128 or Decimal(match[1]) <= 0:
        raise ValueError("native endpoint must retain its positive mean, error and significance suffix")
    return Decimal(match[1]), Decimal(match[2]), match[3]


@dataclass(frozen=True, slots=True)
class WilsonReportedEndpointV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/wilson-reported-endpoint"
    kind: str
    unit: str
    native_token: str
    mean: Decimal | None
    standard_error: Decimal | None
    significance_suffix: str
    replication: NativeReplicationDescriptorV1

    def __post_init__(self) -> None:
        units = {"KCAT_C": "s^-1", "SPECIFICITY_CO": "dimensionless", "K_C_AIR": "micromolar",
                 "APPARENT_CARBOXYLATION_EFFICIENCY": "millimolar^-1 s^-1", "EXPRESSION_SOLUBLE_PROTEIN": "percent_w_w",
                 "THERMAL_MIDPOINT": "degree_C"}
        if units.get(self.kind) != self.unit or (self.mean, self.standard_error, self.significance_suffix) != _reported(self.native_token):
            raise ValueError("reported endpoint differs from its native quantity/token")
        if self.mean is None and self.kind != "THERMAL_MIDPOINT":
            raise ValueError("this source panel has no missing intrinsic kinetic endpoint")


def apply_reported_edits(
    parent_sequence: str, native_token: str, *, subunit: str,
) -> tuple[str, tuple[ReportedSubstitutionV1, ...]]:
    if subunit not in {"rbcl", "rbcs"}:
        raise ValueError("native edits need their exact LSU or SSU namespace")
    if native_token == "None":
        return parent_sequence, ()
    edits = []
    sequence = list(parent_sequence)
    positions = set()
    for token in native_token.split(", "):
        mutation = ReportedSubstitutionV1(f"{subunit}-{token.lower()}", token)
        if mutation.position is None or mutation.position > len(sequence) or mutation.position in positions:
            raise ValueError("reported edits duplicate or exceed their exact parent positions")
        positions.add(mutation.position)
        if parent_sequence[mutation.position - 1] != mutation.ancestral_residue:
            raise ValueError("reported ancestral residue disagrees with the deposited parent sequence")
        sequence[mutation.position - 1] = mutation.replacement_residue
        edits.append(mutation)
    return "".join(sequence), tuple(edits)


@dataclass(frozen=True, slots=True)
class TeProteinSpecificationV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/te-protein-specification"
    parent: NativeTeParentConstructV1
    native_rbcl_edits: str
    native_rbcs_edits: str
    large_subunit_edits: tuple[ReportedSubstitutionV1, ...]
    small_subunit_edits: tuple[ReportedSubstitutionV1, ...]
    large_subunit_sequence: str
    small_subunit_sequence: str
    nucleotide_scope: str = "DERIVED_AMINO_ACID_RECIPE_NO_MUTANT_DNA_ADMITTED"
    assembly_scope: str = "REPORTED_L8S8_NOT_REVALIDATED"

    def __post_init__(self) -> None:
        lsu, l_edits = apply_reported_edits(self.parent.coding_sequence("rbcL").protein_sequence, self.native_rbcl_edits, subunit="rbcl")
        ssu, s_edits = apply_reported_edits(self.parent.coding_sequence("rbcS").protein_sequence, self.native_rbcs_edits, subunit="rbcs")
        if (self.large_subunit_sequence, self.large_subunit_edits, self.small_subunit_sequence,
                self.small_subunit_edits) != (lsu, l_edits, ssu, s_edits):
            raise ValueError("specified mutant proteins differ from the verified parent/edit recipe")
        if self.nucleotide_scope != "DERIVED_AMINO_ACID_RECIPE_NO_MUTANT_DNA_ADMITTED" or self.assembly_scope != "REPORTED_L8S8_NOT_REVALIDATED":
            raise ValueError("an amino-acid recipe cannot create native mutant DNA or biological readiness")


@dataclass(frozen=True, slots=True)
class WilsonMutantRowV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/wilson-mutant-row"
    sample_id: str
    native_table_row: NativeHTMLTableRowV1
    name: str
    library: str
    native_rbcl_edits: str
    native_rbcs_edits: str
    endpoints: tuple[WilsonReportedEndpointV1, ...]
    te_protein_specification: TeProteinSpecificationV1 | None
    sequence_scope: str

    def __post_init__(self) -> None:
        validate_stable_id(self.sample_id)
        cells = self.native_table_row.texts
        if len(cells) != 10 or cells[:4] != (self.name, self.library, self.native_rbcl_edits, self.native_rbcs_edits):
            raise ValueError("mutant row identity/edits differ from exact native table cells")
        if tuple(e.native_token for e in self.endpoints) != cells[4:]:
            raise ValueError("mutant endpoints differ from complete native cells")
        if tuple(e.kind for e in self.endpoints) != (
            "EXPRESSION_SOLUBLE_PROTEIN", "KCAT_C", "K_C_AIR", "APPARENT_CARBOXYLATION_EFFICIENCY",
            "SPECIFICITY_CO", "THERMAL_MIDPOINT",
        ):
            raise ValueError("mutant endpoint roles differ from the exact primary column hierarchy")
        if self.name.startswith("Te-"):
            if self.te_protein_specification is None or self.sequence_scope != "TE_PARENT_AND_PROTEIN_EDITS_VERIFIED":
                raise ValueError("Te row requires its exact verified parent/edit projection")
            if (self.te_protein_specification.native_rbcl_edits, self.te_protein_specification.native_rbcs_edits) != (self.native_rbcl_edits, self.native_rbcs_edits):
                raise ValueError("Te construct edits differ from the native source row")
        elif not self.name.startswith("Se-") or self.te_protein_specification is not None or self.sequence_scope != "SE_PARENT_SEQUENCE_NOT_ADMITTED_NUMBERING_NOT_BORROWED_FROM_TE":
            raise ValueError("Se reference rows cannot borrow another species' parent construct")

    def endpoint(self, kind: str) -> WilsonReportedEndpointV1:
        matches = [e for e in self.endpoints if e.kind == kind]
        if len(matches) != 1:
            raise ValueError("required source endpoint is not declared exactly once")
        return matches[0]


@dataclass(frozen=True, slots=True)
class WilsonMutantPanelV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/wilson-mutant-panel"
    table: NativeWilsonTableV1
    parent: NativeTeParentConstructV1
    rows: tuple[WilsonMutantRowV1, ...]
    native_row_dispositions: tuple[str, ...]
    kinetic_temperature_c: Decimal = Decimal(25)
    joint_endpoint_pairing: str = "SOLUBLE_EXTRACT_TURNOVER_AND_PURIFIED_SPECIFICITY_PAIRING_UNRESOLVED"
    exposure: str = "EXPOSED_RETROSPECTIVE_PRIMARY_PANEL_NO_NEW_BIOLOGICAL_EVIDENCE"

    def __post_init__(self) -> None:
        if len(self.rows) != 19 or sum(r.name.startswith("Te-") for r in self.rows) != 15 or sum(r.name.startswith("Se-") for r in self.rows) != 4:
            raise ValueError("primary panel must retain all fifteen Te and four Se source rows")
        if len({r.name for r in self.rows}) != 19 or len(self.native_row_dispositions) != len(self.table.rows):
            raise ValueError("native panel denominator or complete disposition census is duplicated/missing")
        enzyme_rows = tuple(r for r, d in zip(self.table.rows, self.native_row_dispositions, strict=True) if d == "ENZYME_REPORTED")
        if tuple(r.native_table_row for r in self.rows) != enzyme_rows:
            raise ValueError("projected enzyme roster differs from complete native source dispositions")
        if any(r.te_protein_specification is not None and r.te_protein_specification.parent != self.parent for r in self.rows):
            raise ValueError("mutant protein recipes change the exact admitted deposited parent")
        source_replication = self.table.rows[3].texts[4:]
        if len(source_replication) != 6 or any(tuple(e.replication.native_token for e in r.endpoints) != source_replication for r in self.rows):
            raise ValueError("endpoint replication differs from native column-level source counts")
        if self.kinetic_temperature_c != Decimal(25) or self.joint_endpoint_pairing != "SOLUBLE_EXTRACT_TURNOVER_AND_PURIFIED_SPECIFICITY_PAIRING_UNRESOLVED" or self.exposure != "EXPOSED_RETROSPECTIVE_PRIMARY_PANEL_NO_NEW_BIOLOGICAL_EVIDENCE":
            raise ValueError("native panel cannot invent endpoint pairing, temperature or prospective evidence")


def build_wilson2017_panel(table: NativeWilsonTableV1, parent: NativeTeParentConstructV1) -> WilsonMutantPanelV1:
    header = ("Rubisco", "Mutant library", "Amino acid mutation(s)", "Expression (% (w/w) sol E. coli protein)",
              "kcatc", "Kc21% O2", "kcatc/Kc21%O2", "SC/O", "Tma")
    units = ("", "", "", "", "", "s−1", "μm", "mm−1 s−1", "mol mol−1", "°C")
    if table.rows[0].texts != header or table.rows[1].texts != ("RbcL", "RbcS") or table.rows[2].texts != units:
        raise ValueError("primary Wilson headers, subunit hierarchy or native units differ")
    n_row = table.rows[3].texts
    if len(n_row) != 10 or n_row[0] != "n = biological samples, technical replicates":
        raise ValueError("primary table biological/technical count hierarchy differs")
    caption = " ".join(p.text for p in table.paragraphs if "T1" in p.native_scope_ids)
    if not all(token in caption for token in ("means ± S.E.", "biological samples", "duplicate or triplicate", "25 °C")):
        raise ValueError("primary table does not state the reviewed error/sample/temperature scope")
    kinds = ("EXPRESSION_SOLUBLE_PROTEIN", "KCAT_C", "K_C_AIR", "APPARENT_CARBOXYLATION_EFFICIENCY", "SPECIFICITY_CO", "THERMAL_MIDPOINT")
    quantity_units = ("percent_w_w", "s^-1", "micromolar", "millimolar^-1 s^-1", "dimensionless", "degree_C")
    replication = tuple(NativeReplicationDescriptorV1(token, *_replication_counts(token)) for token in n_row[4:])
    rows = []
    dispositions = []
    for native in table.rows:
        cells = native.texts
        if len(cells) == 10 and cells[0].startswith(("Te-", "Se-")):
            endpoints = tuple(WilsonReportedEndpointV1(kind, unit, token, *_reported(token), count)
                for kind, unit, token, count in zip(kinds, quantity_units, cells[4:], replication, strict=True))
            specification = None
            scope = "SE_PARENT_SEQUENCE_NOT_ADMITTED_NUMBERING_NOT_BORROWED_FROM_TE"
            if cells[0].startswith("Te-"):
                lsu, l_edits = apply_reported_edits(parent.coding_sequence("rbcL").protein_sequence, cells[2], subunit="rbcl")
                ssu, s_edits = apply_reported_edits(parent.coding_sequence("rbcS").protein_sequence, cells[3], subunit="rbcs")
                specification = TeProteinSpecificationV1(parent, cells[2], cells[3], l_edits, s_edits, lsu, ssu)
                scope = "TE_PARENT_AND_PROTEIN_EDITS_VERIFIED"
            rows.append(WilsonMutantRowV1(f"wilson2017-row{native.ordinal_0based}", native, cells[0], cells[1], cells[2], cells[3], endpoints, specification, scope))
            dispositions.append("ENZYME_REPORTED")
        elif native.ordinal_0based < 4:
            dispositions.append("HEADER_UNITS_OR_COLUMN_REPLICATION")
        elif len(cells) == 1 and not cells[0]:
            dispositions.append("NATIVE_DIVIDER")
        elif len(cells) == 10 and cells[0].startswith(("First generation", "Second generation")) and not any(cells[1:]):
            dispositions.append("NATIVE_MUTANT_GENERATION_LABEL")
        else:
            raise ValueError("native source row is not covered by the complete scientific denominator")
    return WilsonMutantPanelV1(table, parent, tuple(rows), tuple(dispositions))


def panel_identity(panel: WilsonMutantPanelV1) -> ObjectIdentity:
    return ObjectIdentity.from_record("rubisco-wilson2017-mutant-panel", panel)
