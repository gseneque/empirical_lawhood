"""Bounded source-native XLSX inspection without Excel or formula execution.

Only explicitly selected worksheets, workbook relationships and shared strings
are expanded. The complete archive inventory is retained, including unselected
members. Native cached tokens and formulas remain separate observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import re
import stat
from typing import ClassVar
import xml.etree.ElementTree as ET
import zipfile

from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, validate_relative_locator, validate_sha256,
)

MAX_ARCHIVE_BYTES = 16 * 1024**2
MAX_MEMBERS = 128
MAX_TOTAL_EXPANDED_BYTES = 32 * 1024**2
MAX_MEMBER_BYTES = 8 * 1024**2
MAX_SELECTED_XML_BYTES = 1024**2
MAX_SELECTED_TOTAL_BYTES = 4 * 1024**2
MAX_XML_ELEMENTS = 50000
MAX_XML_DEPTH = 64
MAX_SHARED_STRINGS = 20000
MAX_TEXT_BYTES = 32768
MAX_CELLS = 20000
MAX_NATIVE_ROW = 100000
MAX_NATIVE_COLUMN = 1024
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
OFFICE_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
WORKSHEET_REL = OFFICE_REL_NS[1:-1] + "/worksheet"
SHARED_STRINGS_REL = OFFICE_REL_NS[1:-1] + "/sharedStrings"


def _bounded_text(value: str, *, where: str) -> None:
    if not isinstance(value, str) or len(value.encode("utf-8")) > MAX_TEXT_BYTES:
        raise ValueError(f"{where} exceeds the native text bound")


def _coordinate(address: str) -> tuple[int, int]:
    match = re.fullmatch(r"([A-Z]{1,3})([1-9][0-9]{0,5})", address)
    if match is None:
        raise ValueError("worksheet cell address is not a bounded native coordinate")
    column = 0
    for c in match[1]:
        column = column * 26 + ord(c) - ord("A") + 1
    row = int(match[2])
    if row > MAX_NATIVE_ROW or column > MAX_NATIVE_COLUMN:
        raise ValueError("worksheet coordinate exceeds its selected bounds")
    return row, column


@dataclass(frozen=True, slots=True)
class NativeArchiveMemberV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-workbook-archive-member"
    ordinal: int
    member: str
    compressed_bytes: int
    expanded_bytes: int
    crc32: str
    compression_method: int
    header_offset: int
    flag_bits: int

    def __post_init__(self) -> None:
        validate_relative_locator(self.member[:-1] if self.member.endswith("/") else self.member)
        for name, value, maximum in (("ordinal", self.ordinal, MAX_MEMBERS - 1),
                                     ("compressed_bytes", self.compressed_bytes, MAX_ARCHIVE_BYTES),
                                     ("expanded_bytes", self.expanded_bytes, MAX_MEMBER_BYTES),
                                     ("header_offset", self.header_offset, MAX_ARCHIVE_BYTES),
                                     ("flag_bits", self.flag_bits, 65535)):
            if type(value) is not int or not 0 <= value <= maximum:
                raise ValueError(f"archive {name} exceeds its exact bounded integer contract")
        if self.compression_method not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED} or self.flag_bits & 1 or re.fullmatch(r"[0-9a-f]{8}", self.crc32) is None:
            raise ValueError("archive member changes its supported compression/CRC contract")


@dataclass(frozen=True, slots=True)
class SelectedWorkbookMemberV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/selected-workbook-member"
    member: str
    sha256: str
    expanded_bytes: int

    def __post_init__(self) -> None:
        validate_relative_locator(self.member)
        validate_sha256(self.sha256)
        if type(self.expanded_bytes) is not int or not 0 <= self.expanded_bytes <= MAX_SELECTED_XML_BYTES:
            raise ValueError("selected member exceeds the XML member bound")


@dataclass(frozen=True, slots=True)
class NativeSheetCatalogEntryV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-workbook-sheet-catalog-entry"
    name: str
    native_sheet_id: str
    relationship_id: str
    member: str

    def __post_init__(self) -> None:
        for value in (self.name, self.native_sheet_id, self.relationship_id):
            _bounded_text(value, where="sheet catalog text")
            if not value:
                raise ValueError("sheet catalog identity must be explicit")
        validate_relative_locator(self.member)


@dataclass(frozen=True, slots=True)
class NativeWorkbookCellV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-workbook-cell"
    address: str
    cell_type: str
    xml_v_token: str | None
    token: str | None
    formula: str | None
    cell_attributes: tuple[tuple[str, str], ...]
    formula_attributes: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _coordinate(self.address)
        if self.cell_type not in {"n", "s", "str", "inlineStr", "b", "e", "d"}:
            raise ValueError("unsupported native workbook cell type")
        for value in (self.xml_v_token, self.token, self.formula):
            if value is not None:
                _bounded_text(value, where="native cell text")
        for attributes in (self.cell_attributes, self.formula_attributes):
            if tuple(sorted(attributes)) != attributes or len(dict(attributes)) != len(attributes) or len(attributes) > 16:
                raise ValueError("native attributes must be bounded and uniquely ordered")
            for key, value in attributes:
                _bounded_text(key, where="attribute name")
                _bounded_text(value, where="attribute value")
        attrs = dict(self.cell_attributes)
        if attrs.get("r") != self.address or attrs.get("t", "n") != self.cell_type:
            raise ValueError("cell identity differs from its native attributes")
        if self.formula is None and self.formula_attributes:
            raise ValueError("formula attributes cannot invent a missing formula")


@dataclass(frozen=True, slots=True)
class NativeWorksheetV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-worksheet"
    catalog_entry: NativeSheetCatalogEntryV1
    member_sha256: str
    row_ids: tuple[int, ...]
    cells: tuple[NativeWorkbookCellV1, ...]
    merged_ranges: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_sha256(self.member_sha256)
        if self.row_ids != tuple(sorted(set(self.row_ids))) or any(
            type(r) is not int or not 1 <= r <= MAX_NATIVE_ROW for r in self.row_ids
        ):
            raise ValueError("worksheet row roster must be bounded, sorted and unique")
        addresses = tuple(c.address for c in self.cells)
        if len(self.cells) > MAX_CELLS or len(set(addresses)) != len(addresses) or addresses != tuple(
            sorted(addresses, key=_coordinate)
        ) or any(_coordinate(a)[0] not in self.row_ids for a in addresses):
            raise ValueError("worksheet cells change the exact native row roster")
        for merged in self.merged_ranges:
            endpoints = merged.split(":")
            if not 1 <= len(endpoints) <= 2:
                raise ValueError("merged range is not a bounded cell range")
            for endpoint in endpoints:
                _coordinate(endpoint)

    def cell(self, address: str) -> NativeWorkbookCellV1 | None:
        return next((c for c in self.cells if c.address == address), None)


@dataclass(frozen=True, slots=True)
class NativeWorkbookV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-workbook"
    source_sha256: str
    archive_bytes: int
    archive_inventory: tuple[NativeArchiveMemberV1, ...]
    selected_members: tuple[SelectedWorkbookMemberV1, ...]
    sheet_catalog: tuple[NativeSheetCatalogEntryV1, ...]
    shared_strings: tuple[str, ...]
    worksheets: tuple[NativeWorksheetV1, ...]
    exposure: str = "EXPOSED_DEVELOPMENT_SOURCE"
    formula_execution: str = "NEVER_EXECUTED_NATIVE_CACHES_ONLY"

    def __post_init__(self) -> None:
        validate_sha256(self.source_sha256)
        if type(self.archive_bytes) is not int or not 1 <= self.archive_bytes <= MAX_ARCHIVE_BYTES:
            raise ValueError("workbook exceeds its physical archive bound")
        if not 1 <= len(self.archive_inventory) <= MAX_MEMBERS or tuple(
            m.ordinal for m in self.archive_inventory
        ) != tuple(range(len(self.archive_inventory))):
            raise ValueError("workbook archive inventory must retain its complete ordered census")
        names = tuple(m.member for m in self.archive_inventory)
        if len(set(names)) != len(names) or sum(m.expanded_bytes for m in self.archive_inventory) > MAX_TOTAL_EXPANDED_BYTES:
            raise ValueError("workbook archive census is duplicated or exceeds its expansion bound")
        if any(m.header_offset >= self.archive_bytes for m in self.archive_inventory):
            raise ValueError("archive member header lies outside the exact selected bytes")
        selected = {m.member: m for m in self.selected_members}
        if len(selected) != len(self.selected_members) or sum(m.expanded_bytes for m in self.selected_members) > MAX_SELECTED_TOTAL_BYTES:
            raise ValueError("selected workbook members are duplicated or exceed their total bound")
        for m in self.archive_inventory:
            if m.member in selected and m.expanded_bytes != selected[m.member].expanded_bytes:
                raise ValueError("selected member size differs from the complete inventory")
        if not set(selected).issubset(names):
            raise ValueError("selected XML is absent from the complete archive inventory")
        if not 1 <= len(self.worksheets) <= 8 or len({w.catalog_entry.name for w in self.worksheets}) != len(self.worksheets):
            raise ValueError("selected worksheet names must be bounded and unique")
        for w in self.worksheets:
            if w.catalog_entry not in self.sheet_catalog or w.catalog_entry.member not in selected or selected[
                w.catalog_entry.member
            ].sha256 != w.member_sha256:
                raise ValueError("selected worksheet differs from its catalog/member identity")
        if len({s.name for s in self.sheet_catalog}) != len(self.sheet_catalog) or len({s.member for s in self.sheet_catalog}) != len(self.sheet_catalog):
            raise ValueError("native sheet catalog identities are duplicated")
        if len(self.shared_strings) > MAX_SHARED_STRINGS:
            raise ValueError("shared strings exceed their count bound")
        for s in self.shared_strings:
            _bounded_text(s, where="shared string")
        for w in self.worksheets:
            for c in w.cells:
                if c.cell_type == "s" and c.xml_v_token is not None:
                    if not re.fullmatch(r"0|[1-9][0-9]*", c.xml_v_token) or int(c.xml_v_token) >= len(self.shared_strings):
                        raise ValueError("cell shared-string reference is outside the admitted roster")
                    if c.token != self.shared_strings[int(c.xml_v_token)]:
                        raise ValueError("cell text differs from its exact shared-string reference")
                elif c.cell_type != "inlineStr" and c.token != c.xml_v_token:
                    raise ValueError("native cell token differs from its exact cached value")
        if self.exposure != "EXPOSED_DEVELOPMENT_SOURCE" or self.formula_execution != "NEVER_EXECUTED_NATIVE_CACHES_ONLY":
            raise ValueError("workbook inspection cannot create fresh evidence or formula evaluation")

    def worksheet(self, name: str) -> NativeWorksheetV1:
        matches = [w for w in self.worksheets if w.catalog_entry.name == name]
        if len(matches) != 1:
            raise ValueError("required worksheet was not selected exactly once")
        return matches[0]


def _xml(payload: bytes, *, root_name: str) -> ET.Element:
    if len(payload) > MAX_SELECTED_XML_BYTES:
        raise ValueError("selected XML exceeds its member bound")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("selected workbook XML must be UTF-8") from error
    if "\x00" in text or "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError("workbook XML DTD/entity declarations and NUL bytes are forbidden")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        raise ValueError("selected workbook XML is malformed") from error
    if root.tag != root_name:
        raise ValueError("selected workbook XML has an unexpected native root")
    pending = [(root, 0)]
    count = 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if depth > MAX_XML_DEPTH or count > MAX_XML_ELEMENTS:
            raise ValueError("selected workbook XML exceeds its structural bounds")
        pending.extend((child, depth + 1) for child in node)
    return root


def _rich_text(element: ET.Element) -> str:
    # Phonetic guides, formatting and unrelated XML text are not cell values.
    fragments = []
    for child in element:
        if child.tag == NS + "t":
            fragments.append(child.text or "")
        elif child.tag == NS + "r":
            fragments.extend(t.text or "" for t in child.findall(NS + "t"))
    value = "".join(fragments)
    _bounded_text(value, where="native rich text")
    return value


def _worksheet(
    payload: bytes, entry: NativeSheetCatalogEntryV1, strings: tuple[str, ...],
) -> NativeWorksheetV1:
    root = _xml(payload, root_name=NS + "worksheet")
    data = root.findall(NS + "sheetData")
    if len(data) != 1:
        raise ValueError("selected worksheet needs exactly one native sheetData")
    rows = []
    cells = []
    for row in data[0].findall(NS + "row"):
        native_row = row.get("r", "")
        if re.fullmatch(r"[1-9][0-9]{0,5}", native_row) is None:
            raise ValueError("worksheet row needs an explicit bounded ordinal")
        row_number = int(native_row)
        rows.append(row_number)
        for cell in row.findall(NS + "c"):
            address = cell.get("r", "")
            if _coordinate(address)[0] != row_number:
                raise ValueError("cell address differs from its native row")
            values = cell.findall(NS + "v")
            formulas = cell.findall(NS + "f")
            if len(values) > 1 or len(formulas) > 1:
                raise ValueError("native cell has ambiguous values or formulas")
            native = values[0].text or "" if values else None
            token = native
            kind = cell.get("t", "n")
            if kind == "s" and native is not None:
                if not re.fullmatch(r"0|[1-9][0-9]*", native) or len(native) > 8 or int(native) >= len(strings):
                    raise ValueError("shared-string index exceeds the native admitted roster")
                token = strings[int(native)]
            elif kind == "inlineStr":
                inline = cell.findall(NS + "is")
                if len(inline) != 1 or values:
                    raise ValueError("inline string has an ambiguous value representation")
                token = _rich_text(inline[0])
            cells.append(NativeWorkbookCellV1(
                address, kind, native, token, (formulas[0].text or "") if formulas else None,
                tuple(sorted(cell.attrib.items())), tuple(sorted(formulas[0].attrib.items())) if formulas else (),
            ))
            if len(cells) > MAX_CELLS:
                raise ValueError("selected worksheet exceeds its native cell count bound")
    if len(set(rows)) != len(rows):
        raise ValueError("native worksheet row ordinals are duplicated")
    merged = tuple(n.get("ref", "") for n in root.findall(NS + "mergeCells/" + NS + "mergeCell"))
    return NativeWorksheetV1(entry, sha256(payload).hexdigest(), tuple(sorted(rows)),
                             tuple(sorted(cells, key=lambda c: _coordinate(c.address))), merged)


def decode_native_workbook(
    payload: bytes, *, expected_sha256: str, selected_sheets: tuple[str, ...],
) -> NativeWorkbookV1:
    """Inspect exact caller-supplied bytes with no I/O or spreadsheet execution."""
    validate_sha256(expected_sha256)
    if not 1 <= len(payload) <= MAX_ARCHIVE_BYTES or sha256(payload).hexdigest() != expected_sha256:
        raise ValueError("workbook exceeds its archive bound or differs from exact custody")
    if not isinstance(selected_sheets, tuple) or not 1 <= len(selected_sheets) <= 8 or len(set(selected_sheets)) != len(selected_sheets):
        raise ValueError("selected sheet names must have a bounded unique roster")
    inventory = []
    selected_members = []
    try:
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            infos = archive.infolist()
            if not 1 <= len(infos) <= MAX_MEMBERS:
                raise ValueError("workbook member count exceeds its bound")
            names = set()
            offsets = set()
            total = 0
            for ordinal, info in enumerate(infos):
                name = info.filename
                locator = name[:-1] if info.is_dir() else name
                validate_relative_locator(locator)
                mode = info.external_attr >> 16
                if (name in names or info.header_offset in offsets or len(name.encode("utf-8")) > 512
                        or info.flag_bits & 1 or info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                        or stat.S_IFMT(mode) not in {0, stat.S_IFREG, stat.S_IFDIR}
                        or not 0 <= info.header_offset < len(payload)
                        or not 0 <= info.file_size <= MAX_MEMBER_BYTES
                        or info.file_size > max(1, info.compress_size) * 1000):
                    raise ValueError("workbook ZIP member violates the bounded safe-member contract")
                names.add(name)
                offsets.add(info.header_offset)
                total += info.file_size
                if total > MAX_TOTAL_EXPANDED_BYTES:
                    raise ValueError("workbook complete expansion inventory exceeds its bound")
                inventory.append(NativeArchiveMemberV1(ordinal, name, info.compress_size, info.file_size,
                    f"{info.CRC:08x}", info.compress_type, info.header_offset, info.flag_bits))

            def read_xml(member: str) -> bytes:
                if any(m.member == member for m in selected_members):
                    raise ValueError("selected source XML member was requested more than once")
                info = archive.getinfo(member)
                if info.file_size > MAX_SELECTED_XML_BYTES or sum(
                    m.expanded_bytes for m in selected_members
                ) + info.file_size > MAX_SELECTED_TOTAL_BYTES:
                    raise ValueError("selected XML expansion exceeds its explicit bounds")
                with archive.open(info) as stream:
                    raw = stream.read(MAX_SELECTED_XML_BYTES + 1)
                if len(raw) != info.file_size:
                    raise ValueError("selected XML expansion differs from its native size")
                selected_members.append(SelectedWorkbookMemberV1(member, sha256(raw).hexdigest(), len(raw)))
                return raw

            workbook = _xml(read_xml("xl/workbook.xml"), root_name=NS + "workbook")
            relationships = _xml(read_xml("xl/_rels/workbook.xml.rels"), root_name=REL_NS + "Relationships")
            links = {}
            string_members = []
            for rel in relationships.findall(REL_NS + "Relationship"):
                relationship_id = rel.get("Id", "")
                if not relationship_id or relationship_id in links:
                    raise ValueError("workbook relationships need unique explicit identities")
                target = rel.get("Target", "")
                if rel.get("TargetMode") == "External":
                    raise ValueError("external workbook relationships are forbidden")
                validate_relative_locator(target)
                member = "xl/" + target
                if rel.get("Type") in {WORKSHEET_REL, SHARED_STRINGS_REL} and member not in names:
                    raise ValueError("workbook relationship target is absent from the archive")
                links[relationship_id] = (rel.get("Type"), member)
                if rel.get("Type") == SHARED_STRINGS_REL:
                    string_members.append(member)
            if len(string_members) > 1:
                raise ValueError("workbook has ambiguous shared-string relationships")
            strings = ()
            if string_members:
                shared = _xml(read_xml(string_members[0]), root_name=NS + "sst")
                strings = tuple(_rich_text(si) for si in shared.findall(NS + "si"))
                if len(strings) > MAX_SHARED_STRINGS:
                    raise ValueError("workbook shared-string count exceeds its bound")
            catalogs = []
            for sheet in workbook.findall(NS + "sheets/" + NS + "sheet"):
                relationship_id = sheet.get(OFFICE_REL_NS + "id", "")
                if relationship_id not in links or links[relationship_id][0] != WORKSHEET_REL:
                    raise ValueError("native sheet does not resolve to a worksheet relationship")
                catalogs.append(NativeSheetCatalogEntryV1(sheet.get("name", ""), sheet.get("sheetId", ""),
                                                          relationship_id, links[relationship_id][1]))
            by_name = {s.name: s for s in catalogs}
            if len(by_name) != len(catalogs) or len({s.member for s in catalogs}) != len(catalogs):
                raise ValueError("workbook sheet names or member relationships are duplicated")
            if not set(selected_sheets).issubset(by_name):
                raise ValueError("requested native worksheet is absent from the workbook catalog")
            worksheets = tuple(_worksheet(read_xml(by_name[name].member), by_name[name], strings)
                               for name in selected_sheets)
    except (zipfile.BadZipFile, KeyError, RuntimeError, NotImplementedError) as error:
        raise ValueError("source is not a supported bounded XLSX archive") from error
    return NativeWorkbookV1(expected_sha256, len(payload), tuple(inventory), tuple(selected_members),
                             tuple(catalogs), strings, worksheets)
