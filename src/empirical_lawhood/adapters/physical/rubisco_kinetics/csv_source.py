"""Bounded lossless native CSV profiles for reported Rubisco kinetics.

The Flamholz source table and de Pins kinetics crosswalk are distinct sources.
They are not pooled, temperature-normalized, deduplicated, construct-verified,
or promoted to independent evidence by this decoder. Missing labels remain
missing; ambiguous native conditions remain explicit uninterpreted text.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
from io import StringIO
import re
from typing import ClassVar

from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_sha256,
)

MAX_INPUT_BYTES = 8 * 1024**2
MAX_ROWS = 10000
MAX_CELL_BYTES = 16384
# These dispositions bind one exact retained artifact. They do not silently
# rewrite a future revision with the same native identifiers.
CROSSWALK_CONFLICT_SOURCE_SHA256 = "df2a55d8f527c6837eacf7cdb2085284eae0d5d8ecd1d53a40617999e79e791e"
CROSSWALK_SPECIFICITY_CONFLICT_IDS = frozenset({
    "ferrooxidans_davidi_2020_corrected", "marinus_davidi_2020_corrected",
    "rubrum_davidi_2020_corrected", "caldicuralii_davidi_2020_corrected",
    "elongatus_davidi_2020_corrected", "unknown_gwa2_54_124_davidi_2020_corrected",
    "unknown_cg1_02_49_23_davidi_2020_corrected", "unknown_davidi_2020_corrected",
    "unknown_cg_mariprof_03_davidi_2020_corrected",
})
CROSSWALK_ROW_JOIN_CONFLICT_IDS = frozenset({
    "elongatus_davidi_2020_corrected", "unknown_davidi_2020_corrected",
})
FLAMHOLZ_HEADERS = (
    "", "species", "identifier", "primary", "mutant", "heterologous_expression",
    "KC", "KC_SD", "vC", "vC_SD", "S", "S_SD", "KO", "KO_SD", "vO", "vO_SD",
    "KRuBP", "KRuBP_SD", "temp_C", "pH", "isoform", "variant", "taxonomy", "note",
    "short_ref", "pmid_or_doi", "citation", "year",
)
CROSSWALK_HEADERS = (
    "identifier", "genus", "species", "subspecies", "mutant", "mutant_details",
    "primary", "heterologous_expression", "kcat_val", "kcat_T", "kcat_pH", "Kc_val",
    "Kc_T", "Kc_pH", "Ko_val", "Ko_T", "Ko_pH", "S_val", "S_T", "S_pH", "temp",
    "pH", "pKa_used", "form", "PGS", "taxonomy", "group", "note", "short_ref", "year",
)


class SourceCSVProfile(StrEnum):
    FLAMHOLZ_SOURCE = "FLAMHOLZ_SOURCE"
    DE_PINS_CROSSWALK = "DE_PINS_CROSSWALK"


class ReportedQuantityKind(StrEnum):
    KCAT_C = "KCAT_C"
    SPECIFICITY_CO = "SPECIFICITY_CO"
    K_C = "K_C"
    K_O = "K_O"
    KCAT_O = "KCAT_O"
    K_RUBP = "K_RUBP"


class SourceQuantityAdmission(StrEnum):
    REPORTED_ENDPOINT_ONLY = "REPORTED_ENDPOINT_ONLY"
    REJECTED_QUANTITY_ROLE_CONFLICT = "REJECTED_QUANTITY_ROLE_CONFLICT"
    REJECTED_ROW_IDENTITY_JOIN_CONFLICT = "REJECTED_ROW_IDENTITY_JOIN_CONFLICT"


_UNITS = {
    ReportedQuantityKind.KCAT_C: "s^-1", ReportedQuantityKind.KCAT_O: "s^-1",
    ReportedQuantityKind.SPECIFICITY_CO: "dimensionless",
    ReportedQuantityKind.K_C: "micromolar", ReportedQuantityKind.K_O: "micromolar",
    ReportedQuantityKind.K_RUBP: "micromolar",
}


def _point(token: str, *, positive: bool) -> Decimal | None:
    if not token:
        return None
    if len(token) > 64 or re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", token) is None:
        raise ValueError("reported numerical cell is not a bounded decimal token")
    try:
        value = Decimal(token)
    except InvalidOperation as error:
        raise ValueError("reported numerical cell has an unsupported decimal exponent") from error
    validate_decimal(value, field_name="reported_value")
    if value and not -32 <= value.adjusted() <= 32:
        raise ValueError("reported numerical cell exceeds its bounded magnitude")
    if (positive and value <= 0) or (not positive and value < 0):
        raise ValueError("reported kinetic point/error has invalid sign")
    return value


def _condition(token: str) -> Decimal | None:
    """Unresolved conditions are retained, not silently interpreted or corrected."""
    if not token or len(token) > 64:
        return None
    try:
        value = Decimal(token)
    except InvalidOperation:
        return None
    return value if value.is_finite() and (not value or -32 <= value.adjusted() <= 32) else None


@dataclass(frozen=True, slots=True)
class ReportedKineticQuantityV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/reported-kinetic-quantity"
    kind: ReportedQuantityKind
    unit: str
    native_value: str
    value: Decimal | None
    native_error: str
    error: Decimal | None
    error_header: str
    native_temperature_c: str
    temperature_c: Decimal | None
    native_ph: str
    ph: Decimal | None
    scientific_admission: SourceQuantityAdmission = SourceQuantityAdmission.REPORTED_ENDPOINT_ONLY
    admission_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ReportedQuantityKind) or self.unit != _UNITS[self.kind]:
            raise ValueError("quantity kind/unit differs from the reviewed source profile")
        if self.value != _point(self.native_value, positive=True):
            raise ValueError("kinetic value differs from exact native point token")
        if self.error != _point(self.native_error, positive=False):
            raise ValueError("reported error differs from native token")
        if self.value is None and self.error is not None:
            raise ValueError("an error token cannot manufacture a missing point label")
        if self.temperature_c != _condition(self.native_temperature_c) or self.ph != _condition(self.native_ph):
            raise ValueError("condition value differs from its native token")
        if not isinstance(self.scientific_admission, SourceQuantityAdmission):
            raise ValueError("source quantity requires an explicit scientific disposition")
        require_sorted_unique_strings(self.admission_reasons, field_name="admission_reasons")
        ordinary = self.scientific_admission is SourceQuantityAdmission.REPORTED_ENDPOINT_ONLY
        if (ordinary and self.admission_reasons) or (not ordinary and not self.admission_reasons):
            raise ValueError("rejected quantities require reasons; ordinary reported labels have no rejection")

    @property
    def admitted_value(self) -> Decimal | None:
        """Source-reported endpoint only; never biological qualification or coverage.

        ``value`` preserves the numerical token even when a native header is
        scientifically wrong. Consumers must use this disposition-aware value.
        """
        return self.value if self.scientific_admission is SourceQuantityAdmission.REPORTED_ENDPOINT_ONLY else None


@dataclass(frozen=True, slots=True)
class NativeKineticCSVRowV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-kinetic-csv-row"
    table_row: int
    native_cells: tuple[str, ...]
    native_identifier: str
    primary_source_flag: bool
    quantities: tuple[ReportedKineticQuantityV1, ...]

    def __post_init__(self) -> None:
        if type(self.table_row) is not int or not 1 <= self.table_row <= MAX_ROWS:
            raise ValueError("source row exceeds its exact ordinal bound")
        if type(self.primary_source_flag) is not bool:
            raise ValueError("primary source flag must be explicit")
        if not self.native_identifier or not self.native_cells or any(
            len(c.encode("utf-8")) > MAX_CELL_BYTES for c in self.native_cells
        ):
            raise ValueError("source row identifier/text is missing or exceeds its bound")
        kinds = tuple(q.kind for q in self.quantities)
        if kinds != tuple(sorted(set(kinds))):
            raise ValueError("source quantities must have one sorted unique order")

    def quantity(self, kind: ReportedQuantityKind) -> ReportedKineticQuantityV1 | None:
        return next((q for q in self.quantities if q.kind is kind), None)


@dataclass(frozen=True, slots=True)
class NativeKineticCSVTableV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-kinetic-csv-table"
    profile: SourceCSVProfile
    source_sha256: str
    native_headers: tuple[str, ...]
    rows: tuple[NativeKineticCSVRowV1, ...]
    exposure: str = "EXPOSED_DEVELOPMENT_SOURCE"
    construct_verification: str = "NATIVE_METADATA_ONLY_NO_COMPLETE_CONSTRUCT_VERIFICATION"
    physical_independent_units_known: bool = False
    biological_joint_uncertainty_available: bool = False

    def __post_init__(self) -> None:
        validate_sha256(self.source_sha256, field_name="source_sha256")
        if not isinstance(self.profile, SourceCSVProfile):
            raise ValueError("unsupported native source profile")
        expected = FLAMHOLZ_HEADERS if self.profile is SourceCSVProfile.FLAMHOLZ_SOURCE else CROSSWALK_HEADERS
        if (self.native_headers != expected or not 1 <= len(self.rows) <= MAX_ROWS
                or tuple(r.table_row for r in self.rows) != tuple(range(1, len(self.rows) + 1))
                or any(len(r.native_cells) != len(expected) for r in self.rows)
                or self.exposure != "EXPOSED_DEVELOPMENT_SOURCE"
                or self.construct_verification != "NATIVE_METADATA_ONLY_NO_COMPLETE_CONSTRUCT_VERIFICATION"
                or self.physical_independent_units_known or self.biological_joint_uncertainty_available):
            raise ValueError("table changes native source shape or scientific admission ceiling")
        if any(_native_row(r.table_row, r.native_cells, self.profile, self.source_sha256) != r for r in self.rows):
            raise ValueError("native table projections differ from their exact source cells")


def _source_disposition(
    profile: SourceCSVProfile, source_sha256: str, identifier: str, kind: ReportedQuantityKind,
) -> tuple[SourceQuantityAdmission, tuple[str, ...]]:
    if profile is not SourceCSVProfile.DE_PINS_CROSSWALK or source_sha256 != CROSSWALK_CONFLICT_SOURCE_SHA256:
        return SourceQuantityAdmission.REPORTED_ENDPOINT_ONLY, ()
    reasons = []
    if identifier in CROSSWALK_SPECIFICITY_CONFLICT_IDS and kind is ReportedQuantityKind.SPECIFICITY_CO:
        reasons.append("NATIVE_S_VAL_IS_CARBOXYLATION_EFFICIENCY_NOT_SPECIFICITY")
    if identifier in CROSSWALK_ROW_JOIN_CONFLICT_IDS:
        reasons.append("NATIVE_ROW_MIXES_CORRECTED_ENZYME_IDENTITIES_RECONCILIATION_REQUIRED")
        return SourceQuantityAdmission.REJECTED_ROW_IDENTITY_JOIN_CONFLICT, tuple(sorted(reasons))
    if reasons:
        return SourceQuantityAdmission.REJECTED_QUANTITY_ROLE_CONFLICT, tuple(sorted(reasons))
    return SourceQuantityAdmission.REPORTED_ENDPOINT_ONLY, ()


def _native_row(
    index: int, cells: tuple[str, ...], profile: SourceCSVProfile, source_sha256: str,
) -> NativeKineticCSVRowV1:
    headers = FLAMHOLZ_HEADERS if profile is SourceCSVProfile.FLAMHOLZ_SOURCE else CROSSWALK_HEADERS
    row = dict(zip(headers, cells, strict=True))
    flag = row["primary"]
    allowed_flags = ("1", "0") if profile is SourceCSVProfile.FLAMHOLZ_SOURCE else ("TRUE", "FALSE")
    if flag not in allowed_flags:
        raise ValueError("source primary flag differs from the native profile")
    if profile is SourceCSVProfile.FLAMHOLZ_SOURCE:
        columns = ((ReportedQuantityKind.KCAT_C, "vC"), (ReportedQuantityKind.SPECIFICITY_CO, "S"),
                   (ReportedQuantityKind.K_C, "KC"), (ReportedQuantityKind.K_O, "KO"),
                   (ReportedQuantityKind.KCAT_O, "vO"), (ReportedQuantityKind.K_RUBP, "KRuBP"))
        selections = tuple((kind, column, column + "_SD", "temp_C", "pH") for kind, column in columns)
    else:
        selections = ((ReportedQuantityKind.KCAT_C, "kcat_val", "", "kcat_T", "kcat_pH"),
                      (ReportedQuantityKind.SPECIFICITY_CO, "S_val", "", "S_T", "S_pH"),
                      (ReportedQuantityKind.K_C, "Kc_val", "", "Kc_T", "Kc_pH"),
                      (ReportedQuantityKind.K_O, "Ko_val", "", "Ko_T", "Ko_pH"))
    quantities = []
    for kind, value_col, error_col, temp_col, ph_col in selections:
        native_value = row[value_col]
        native_error = row[error_col] if error_col else ""
        # The crosswalk declares endpoint-specific conditions plus shared conditions.
        # Retain all original cells even when the specific condition takes precedence.
        temp = row[temp_col] or (row["temp"] if profile is SourceCSVProfile.DE_PINS_CROSSWALK else "")
        ph = row[ph_col] or row["pH"]
        admission, reasons = _source_disposition(profile, source_sha256, row["identifier"], kind)
        quantities.append(ReportedKineticQuantityV1(
            kind, _UNITS[kind], native_value, _point(native_value, positive=True),
            native_error, _point(native_error, positive=False), error_col,
            temp, _condition(temp), ph, _condition(ph), admission, reasons,
        ))
    return NativeKineticCSVRowV1(index, cells, row["identifier"], flag == allowed_flags[0],
                               tuple(sorted(quantities, key=lambda q: q.kind)))


def decode_source_csv(
    payload: bytes, *, expected_sha256: str, profile: SourceCSVProfile,
) -> NativeKineticCSVTableV1:
    """Decode exact selected CSV bytes without acquisition, formulas or pooling."""
    validate_sha256(expected_sha256, field_name="expected_sha256")
    if len(payload) > MAX_INPUT_BYTES or sha256(payload).hexdigest() != expected_sha256:
        raise ValueError("source CSV exceeds its bound or differs from exact custody")
    if not isinstance(profile, SourceCSVProfile):
        raise ValueError("unsupported native source CSV profile")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("source CSV must be UTF-8") from error
    if "\x00" in text:
        raise ValueError("source CSV contains a NUL byte")
    expected = FLAMHOLZ_HEADERS if profile is SourceCSVProfile.FLAMHOLZ_SOURCE else CROSSWALK_HEADERS
    reader = csv.reader(StringIO(text, newline=""), strict=True)
    try:
        headers = tuple(next(reader))
        if headers != expected:
            raise ValueError("native CSV headers/order/units differ from the selected profile")
        rows = []
        for index, raw in enumerate(reader, 1):
            cells = tuple(raw)
            if index > MAX_ROWS or len(cells) != len(headers) or any(
                len(c.encode("utf-8")) > MAX_CELL_BYTES for c in cells
            ):
                raise ValueError("native CSV row dimensions/text exceed their bound")
            rows.append(_native_row(index, cells, profile, expected_sha256))
    except (csv.Error, StopIteration) as error:
        raise ValueError("source CSV is not a bounded rectangular table") from error
    return NativeKineticCSVTableV1(profile, expected_sha256, headers, tuple(rows))
