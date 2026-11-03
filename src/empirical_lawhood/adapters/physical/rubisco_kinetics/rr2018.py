"""Lossless exposed RR2018 Table 1 curation, adapted from the retained E1 owner.

Historical implementation: icf-yolo aa9346547560abcb6500f2e97b53b96f456d9be3,
adapters/physical/rubisco_kinetics_v1/rr2018.py. New EL records have distinct
identities; this adapter never rewrites the historical records or receipts.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import re
from typing import ClassVar
import xml.etree.ElementTree as ET

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256

from .records import (
    HistoricalFeatureSliceV1,
    HistoricalLabelSliceV1,
    HistoricalTrainingSliceV1,
    ReportedEndpointsV1,
    ReportedSubstitutionV1,
)

DOI = "10.1038/s41598-018-23869-3"
SOURCE_SHA256 = "5dc1ccfa4239bc530842cd6d904a4b1b775ac3098c4fba139a263fa9844bffa0"
SUPPLEMENT_SHA256 = "6d801635db500e664783b88bbcaa0ac830ffd5c251993b5df6c48b4b9fb1946d"
PREFIX = "rubisco-rr2018-curation-v1"
MAX_INPUT_BYTES = 2 * 1024**2
MAX_SUPPLEMENT_BYTES = 16 * 1024**2
HEADERS = (
    "Rubisco", "In vitro Evolution strategy", "Tm (°C)", "[Rubisco] (% tsp1)",
    "SC/O (mol.mol−1)", "KC (μM)", "kcatC (s-1)", "kcatC/KC (mM.s-1)", "KmRuBP (μM)",
)
LABELS = (
    "RubRr", "Clone 9", "Clone 11", "Clone 25", "Clone 27", "MRPro", "Clone B2",
    "Clone B3", "Clone B9",
)
SUBSTITUTIONS = (
    "WT", "A99T/H181Y", "M100T", "K300R/M376L", "D206E", "WT", "F189L", "V67I", "E415V",
)
LIMITATIONS = tuple(sorted((
    "BIOLOGICAL_REPLICATION_AND_ENDPOINT_PAIRING_UNKNOWN",
    "C_TERMINAL_HIS6_TAG_JUNCTION_NOT_SEQUENCE_VERIFIED",
    "DEVELOPMENT_EXPOSED_HISTORICAL_TABLE",
    "NATIVE_PLUS_MINUS_SEMANTICS_UNRESOLVED",
    "TURNOVER_LYSATE_PH8_VERSUS_SPECIFICITY_PURIFIED_PH8P1",
    "TWO_SINGLE_MUTANT_CONTRASTS_NO_CALIBRATION_UNITS",
)))


def _disposition(index: int) -> str:
    if index in (0, 2, 4):
        return "INCLUDED"
    if index in (1, 3):
        return "EXCLUDED_MULTIPLE_SUBSTITUTIONS"
    return "EXCLUDED_ANCESTRAL_PARENT"


@dataclass(frozen=True, slots=True)
class Rr2018NativeRowV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/rr2018-native-row"
    table_row: int
    native_cells: tuple[str, ...]
    reported_substitutions: str
    disposition: str

    def __post_init__(self) -> None:
        if type(self.table_row) is not int or not 1 <= self.table_row <= 9 or len(self.native_cells) != 9:
            raise ValueError("native row changes the exact table dimensions")
        if any(not isinstance(c, str) or len(c) > 256 or len(c.encode("utf-8")) > 1024 for c in self.native_cells):
            raise ValueError("native cell exceeds its bounded text contract")
        i = self.table_row - 1
        if (self.native_cells[0] != LABELS[i] or self.reported_substitutions != SUBSTITUTIONS[i]
                or self.disposition != _disposition(i)):
            raise ValueError("native row changes the predeclared label/mutation census")
        for column in (4, 6):
            reported_mean(self.native_cells[column])


@dataclass(frozen=True, slots=True)
class Rr2018NativeAuditV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/rr2018-native-audit"
    audit_id: str
    source_sha256: str
    supplement_sha256: str
    native_headers: tuple[str, ...]
    rows: tuple[Rr2018NativeRowV1, ...]
    supplement_bytes_verified: bool = False
    limitations: tuple[str, ...] = LIMITATIONS
    physical_independent_units_known: bool = False
    biological_joint_uncertainty_available: bool = False

    def __post_init__(self) -> None:
        validate_sha256(self.source_sha256, field_name="source_sha256")
        if (self.audit_id != f"{PREFIX}.native-audit" or self.supplement_sha256 != SUPPLEMENT_SHA256
                or self.native_headers != HEADERS
                or tuple(r.table_row for r in self.rows) != tuple(range(1, 10))
                or self.limitations != LIMITATIONS or self.physical_independent_units_known
                or self.biological_joint_uncertainty_available
                or type(self.supplement_bytes_verified) is not bool):
            raise ValueError("native audit changes source, denominator or evidence ceiling")


def reported_mean(token: str) -> Decimal:
    """Extract the exact mean without interpreting the retained native error token."""
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*±\s*([0-9]+(?:\.[0-9]+)?)", token)
    if match is None or Decimal(match[1]) <= 0:
        raise ValueError("endpoint requires a positive mean and explicit native ± token")
    return Decimal(match[1])


def decode_rr2018(
    payload: bytes, *, expected_sha256: str, supplement_payload: bytes | None = None,
) -> Rr2018NativeAuditV1:
    """Pure hash-first XML decode; no network, fitting, DTDs or source correction.

    Supplement identity is the retained curator's declared source. It becomes a
    verified current byte observation only when the caller supplies those bytes.
    Synthetic inputs remain exposed software fixtures regardless of their hash.
    """
    validate_sha256(expected_sha256, field_name="expected_sha256")
    if len(payload) > MAX_INPUT_BYTES or sha256(payload).hexdigest() != expected_sha256:
        raise ValueError("article exceeds its bound or differs from exact custody")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("article must be UTF-8 XML") from error
    if "\x00" in text or "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError("article DTD/entity declarations are forbidden")
    if supplement_payload is not None and (
        len(supplement_payload) > MAX_SUPPLEMENT_BYTES
        or sha256(supplement_payload).hexdigest() != SUPPLEMENT_SHA256
    ):
        raise ValueError("supplement differs from retained exact custody")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        raise ValueError("article is not well-formed XML") from error
    pending = [(root, 0)]
    count = 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if depth > 64 or count > 20000:
            raise ValueError("article XML exceeds its structural bound")
        pending.extend((child, depth + 1) for child in node)
    if root.tag != "article" or [
        x.text for x in root.findall("./front/article-meta/article-id[@pub-id-type='doi']")
    ] != [DOI]:
        raise ValueError("article DOI differs from the frozen source")
    tables = root.findall(".//table-wrap[@id='Tab1']")
    if len(tables) != 1:
        raise ValueError("article must have exactly one native Tab1")
    cells = tuple(tuple("".join(c.itertext()) for c in row) for row in tables[0].findall(".//tr"))
    if len(cells) != 10 or cells[0] != HEADERS:
        raise ValueError("native table dimensions, header or units differ")
    rows = tuple(Rr2018NativeRowV1(i + 1, row, SUBSTITUTIONS[i], _disposition(i))
                 for i, row in enumerate(cells[1:]))
    return Rr2018NativeAuditV1(
        f"{PREFIX}.native-audit", expected_sha256, SUPPLEMENT_SHA256, cells[0], rows,
        supplement_bytes_verified=supplement_payload is not None,
    )


def selected_endpoints(audit: Rr2018NativeAuditV1) -> tuple[ReportedEndpointsV1, ...]:
    by_label = {r.native_cells[0]: r for r in audit.rows}
    return tuple(ReportedEndpointsV1(sample, reported_mean(by_label[label].native_cells[6]),
                                     reported_mean(by_label[label].native_cells[4]))
                 for sample, label in (("d206e", "Clone 27"), ("m100t", "Clone 11"), ("wt", "RubRr")))


def selected_features(audit: Rr2018NativeAuditV1) -> tuple[ReportedSubstitutionV1, ...]:
    by_label = {r.native_cells[0]: r for r in audit.rows}
    return tuple(ReportedSubstitutionV1(sample, by_label[label].reported_substitutions)
                 for sample, label in (("d206e", "Clone 27"), ("m100t", "Clone 11"), ("wt", "RubRr")))


Rr2018Slice = HistoricalTrainingSliceV1 | HistoricalFeatureSliceV1 | HistoricalLabelSliceV1


def role_slices(audit: Rr2018NativeAuditV1) -> tuple[Rr2018Slice, ...]:
    source = ObjectIdentity.from_record(audit.audit_id, audit)
    features = {f.sample_id: f for f in selected_features(audit)}
    endpoints = {e.sample_id: e for e in selected_endpoints(audit)}
    records: list[Rr2018Slice] = []
    for fold, training, target in (("site100", ("d206e", "wt"), "m100t"),
                                   ("site206", ("m100t", "wt"), "d206e")):
        prefix = f"{PREFIX}.{fold}"
        records.extend((
            HistoricalTrainingSliceV1(f"{prefix}.training", fold, source,
                                      tuple(features[s] for s in training),
                                      tuple(endpoints[s] for s in training)),
            HistoricalFeatureSliceV1(f"{prefix}.features", fold, source, (features[target],)),
            HistoricalLabelSliceV1(f"{prefix}.labels", fold, source, (endpoints[target],)),
        ))
    return tuple(sorted(records, key=lambda r: r.slice_id))
