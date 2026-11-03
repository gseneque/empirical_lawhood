"""Source-native direct endpoint panels; exposed observations, not qualification.

McDonald summaries retain their actual formula/cache joins and listed raw values.
Davidi's original rates, admitted correction annotations and later remeasurement
remain separate source worlds. Neither paired columns nor listed N establish
biological independence, prospective eligibility or calibrated joint precision.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
import re
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings, validate_decimal,
    validate_sha256, validate_stable_id,
)

from .workbook import NativeWorkbookCellV1, NativeWorkbookV1, NativeWorksheetV1
from .wilson2017 import MAX_HTML_BYTES, NativeHTMLTableRowV1, _TableParser

MCDONALD_SHEETS = ("Figure 3 Raw Data + Stats", "Kinetic table")
DAVIDI_SHEETS = ("spectroscopic assay", "radiometric assay")
MCDONALD_SOURCE_SHA256 = "1fbb073dbcc50e96d40677e0d38a817944a3cc1d859fdd38d9dc8c6c8f5e3f98"
DAVIDI_SOURCE_SHA256 = "37cb57accc4d10ef72098199038f6ab15310aefdd86461be54a8f7ffa5f7fa96"
TSAI_2025_SOURCE_SHA256 = "b68c813ff073972d42ed7b1ca9540244c45e6bfdb2c7bd8fe50070825b9068bc"
DIAGNOSTIC_ABSOLUTE_TOLERANCE = Decimal("0.00002")


def _number(token: str | None, *, nonnegative: bool = False) -> Decimal | None:
    if token in (None, "", "nm"):
        return None
    if len(token) > 128 or re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", token) is None:
        raise ValueError("kinetic source cache is not a bounded decimal or explicit missing token")
    try:
        value = Decimal(token)
    except InvalidOperation as error:
        raise ValueError("kinetic source decimal has an unsupported exponent") from error
    validate_decimal(value, field_name="native_kinetic_cache")
    if (value and not -32 <= value.adjusted() <= 32) or value < 0 or (not nonnegative and value == 0):
        raise ValueError("kinetic source point exceeds its sign/magnitude bounds")
    return value


def _mean_error(token: str) -> tuple[Decimal, Decimal]:
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*±\s*([0-9]+(?:\.[0-9]+)?)", token)
    if match is None:
        raise ValueError("reported native endpoint must retain its explicit mean ± token")
    mean = _number(match[1])
    error = _number(match[2], nonnegative=True)
    if mean is None or error is None:
        raise ValueError("explicit mean/error token cannot contain a missing value")
    return mean, error


def _cell(sheet: NativeWorksheetV1, address: str) -> NativeWorkbookCellV1:
    cell = sheet.cell(address)
    if cell is None:
        raise ValueError(f"required native source cell {address} is absent")
    return cell


def _text(cell: NativeWorkbookCellV1) -> str:
    if cell.token is None:
        raise ValueError("required native source text has no cached value")
    return cell.token


@dataclass(frozen=True, slots=True)
class NativeRawEndpointValueV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-raw-endpoint-value"
    worksheet: str
    group_cell: NativeWorkbookCellV1
    value_cell: NativeWorkbookCellV1
    value: Decimal

    def __post_init__(self) -> None:
        if self.value != _number(self.value_cell.token) or self.group_cell.token is None:
            raise ValueError("raw endpoint value differs from its native cached source")


def _diagnostics(
    reported_mean: Decimal | None, reported_sd: Decimal | None, reported_sem: Decimal | None,
    reported_n: int | None, raw_values: tuple[NativeRawEndpointValueV1, ...],
) -> tuple[Decimal | None, Decimal | None, tuple[str, ...]]:
    flags = []
    if reported_n is not None and reported_n != len(raw_values):
        flags.append("REPORTED_N_DIFFERS_FROM_LISTED_RAW_COUNT")
    with localcontext() as context:
        context.prec = 36
        mean = sum((v.value for v in raw_values), Decimal(0)) / len(raw_values) if raw_values else None
        sd = (sum((v.value - mean) ** 2 for v in raw_values) / (len(raw_values) - 1)).sqrt() if len(raw_values) > 1 else None
        if mean is not None and reported_mean is not None and abs(mean - reported_mean) > DIAGNOSTIC_ABSOLUTE_TOLERANCE:
            flags.append("REPORTED_MEAN_DIFFERS_FROM_LISTED_RAW_MEAN")
        if sd is not None and reported_sd is not None and abs(sd - reported_sd) > DIAGNOSTIC_ABSOLUTE_TOLERANCE:
            flags.append("REPORTED_SD_DIFFERS_FROM_LISTED_SAMPLE_SD")
        if reported_sem is not None and reported_sd is not None and reported_n:
            expected_sem = reported_sd / Decimal(reported_n).sqrt()
            if abs(expected_sem - reported_sem) > DIAGNOSTIC_ABSOLUTE_TOLERANCE:
                flags.append("REPORTED_SEM_DIFFERS_FROM_SD_OVER_SQRT_REPORTED_N")
    return mean, sd, tuple(sorted(flags))


@dataclass(frozen=True, slots=True)
class DirectEndpointObservationV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/direct-endpoint-observation"
    kind: str
    unit: str
    worksheet: str
    summary_cell: NativeWorkbookCellV1
    reported_mean: Decimal | None
    reported_error_token: str | None
    reported_error: Decimal | None
    error_semantics: str
    source_mean_cell: NativeWorkbookCellV1 | None
    source_sd_cell: NativeWorkbookCellV1 | None
    source_sem_cell: NativeWorkbookCellV1 | None
    source_n_cell: NativeWorkbookCellV1 | None
    reported_n: int | None
    raw_values: tuple[NativeRawEndpointValueV1, ...]
    recomputed_raw_mean: Decimal | None
    recomputed_raw_sample_sd: Decimal | None
    diagnostic_flags: tuple[str, ...]
    independent_unit_role: str = "BIOLOGICAL_VERSUS_TECHNICAL_AND_ENDPOINT_PAIRING_UNRESOLVED"

    def __post_init__(self) -> None:
        if (self.kind, self.unit) not in {("KCAT_C", "s^-1"), ("SPECIFICITY_CO", "dimensionless")}:
            raise ValueError("direct endpoint kind/unit is unsupported")
        if self.error_semantics == "NATIVE_PLUS_MINUS_UNRESOLVED":
            mean, error = _mean_error(_text(self.summary_cell))
            if self.reported_mean != mean or self.reported_error != error or self.reported_error_token != self.summary_cell.token:
                raise ValueError("direct reported mean/error differs from its complete native token")
        elif self.error_semantics == "PUBLISHED_SD_WITH_RAW_AUDIT_NOT_CALIBRATED":
            if self.reported_mean != _number(self.summary_cell.token) or self.reported_error != _number(
                self.reported_error_token, nonnegative=True
            ):
                raise ValueError("direct reported mean/error differs from its native cache")
            if any(c is None for c in (self.source_mean_cell, self.source_sd_cell, self.source_sem_cell, self.source_n_cell)):
                raise ValueError("published summary requires its complete native count/error/mean joins")
            if self.worksheet != MCDONALD_SHEETS[1] or self.summary_cell.formula != (
                f"'{MCDONALD_SHEETS[0]}'!{self.source_mean_cell.address}"
            ):
                raise ValueError("published summary formula differs from its declared native source cell")
        else:
            raise ValueError("direct endpoint error semantics must be explicit")
        if self.source_mean_cell is not None and self.source_mean_cell.token != self.summary_cell.token:
            raise ValueError("summary mean differs from its joined native source cell")
        if self.source_sd_cell is not None and self.source_sd_cell.token != self.reported_error_token:
            raise ValueError("summary error differs from its joined native source cell")
        if self.source_n_cell is not None:
            native_n = _text(self.source_n_cell)
            if re.fullmatch(r"0|[1-9][0-9]{0,3}", native_n) is None or self.reported_n != int(native_n):
                raise ValueError("reported N differs from its exact native count cell")
        elif self.reported_n is not None:
            raise ValueError("reported N cannot be invented without a source cell")
        sem = _number(self.source_sem_cell.token, nonnegative=True) if self.source_sem_cell else None
        mean, sd, flags = _diagnostics(self.reported_mean, self.reported_error, sem, self.reported_n, self.raw_values)
        if (self.recomputed_raw_mean, self.recomputed_raw_sample_sd, self.diagnostic_flags) != (mean, sd, flags):
            raise ValueError("raw diagnostic differs from its exact retained operands")
        require_sorted_unique_strings(self.diagnostic_flags, field_name="diagnostic_flags")
        if self.independent_unit_role != "BIOLOGICAL_VERSUS_TECHNICAL_AND_ENDPOINT_PAIRING_UNRESOLVED":
            raise ValueError("native listed counts do not resolve physical independence")


@dataclass(frozen=True, slots=True)
class NativeSequenceJoinV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/native-sequence-join"
    worksheet: str
    native_row: int
    identifier_cell: NativeWorkbookCellV1
    protein_cell: NativeWorkbookCellV1
    dna_cell: NativeWorkbookCellV1
    construct_scope: str = "NATIVE_LARGE_SUBUNIT_SEQUENCE_NOT_COMPLETE_ASSAY_PREPARATION"

    def __post_init__(self) -> None:
        if type(self.native_row) is not int or self.native_row < 1:
            raise ValueError("sequence join requires an explicit native row")
        if not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWYX*]{1,2000}", _text(self.protein_cell)) or not re.fullmatch(
            r"[ACGT]{1,10000}", _text(self.dna_cell)
        ):
            raise ValueError("source sequence tokens exceed the native alphabet/size profile")
        if self.construct_scope != "NATIVE_LARGE_SUBUNIT_SEQUENCE_NOT_COMPLETE_ASSAY_PREPARATION":
            raise ValueError("sequence lookup cannot invent a complete verified assay construct")


@dataclass(frozen=True, slots=True)
class DavidiCorrectionRowV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/davidi-correction-row"
    original_identifier: str
    native_table_row: int
    native_cells: tuple[str, ...]
    corrected_historical_turnover_token: str
    remeasured_2025_turnover_token: str

    def __post_init__(self) -> None:
        if not self.original_identifier or type(self.native_table_row) is not int or not 1 <= self.native_table_row <= 100:
            raise ValueError("correction row requires an explicit original identity/native row")
        if len(self.original_identifier.encode()) > 2048:
            raise ValueError("correction enzyme identity exceeds its native text bound")
        if not 3 <= len(self.native_cells) <= 32 or any(len(c.encode()) > 2048 for c in self.native_cells):
            raise ValueError("correction row exceeds its native text/dimension bounds")
        if self.native_cells[1:3] != (self.corrected_historical_turnover_token, self.remeasured_2025_turnover_token):
            raise ValueError("correction annotations differ from their retained native table cells")
        _mean_error(self.corrected_historical_turnover_token)
        _mean_error(self.remeasured_2025_turnover_token)


@dataclass(frozen=True, slots=True)
class DavidiCorrectionTableV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/davidi-correction-table"
    source_sha256: str
    source_doi: str
    native_table_locator: str
    native_headers: tuple[str, ...]
    rows: tuple[DavidiCorrectionRowV1, ...]
    interpretation: str = "SEPARATE_CORRECTED_HISTORICAL_AND_REMEASURED_2025_TURNOVER_NO_NEW_SPECIFICITY"
    native_header_rows: tuple[NativeHTMLTableRowV1, ...] = ()
    native_body_rows: tuple[NativeHTMLTableRowV1, ...] = ()
    source_name_aliases: tuple[tuple[str, str, str], ...] = ()
    original_panel: ObjectIdentity | None = None
    original_source_sha256: str | None = None

    def __post_init__(self) -> None:
        validate_sha256(self.source_sha256)
        if self.source_doi != "10.1038/s44318-025-00419-y" or not self.native_table_locator or len(self.native_table_locator) > 256:
            raise ValueError("correction table needs its explicit reviewed source/table identity")
        if not 1 <= len(self.rows) <= 9 or len({r.original_identifier for r in self.rows}) != len(self.rows):
            raise ValueError("correction table must have a bounded unique original-enzyme roster")
        if (not 3 <= len(self.native_headers) <= 32 or len({r.native_table_row for r in self.rows}) != len(self.rows)
                or any(len(r.native_cells) != len(self.native_headers) for r in self.rows)):
            raise ValueError("correction table dimensions/native row identities are inconsistent")
        if self.interpretation != "SEPARATE_CORRECTED_HISTORICAL_AND_REMEASURED_2025_TURNOVER_NO_NEW_SPECIFICITY":
            raise ValueError("turnover correction cannot invent a new paired specificity measurement")
        if self.native_body_rows or self.native_header_rows or self.source_name_aliases:
            if (len(self.native_header_rows) != 2 or len(self.native_body_rows) != 9 or len(self.rows) != 9
                    or len(self.source_name_aliases) != 9 or self.original_panel is None
                    or self.original_panel.object_schema != DirectEndpointPanelV1.SCHEMA
                    or self.original_source_sha256 != DAVIDI_SOURCE_SHA256 or self.source_sha256 != TSAI_2025_SOURCE_SHA256):
                raise ValueError("native correction requires complete source-version-bound headers/body/aliases")
            _validate_tsai_headers(*self.native_header_rows)
            if (self.native_headers != self.native_header_rows[1].texts
                    or tuple(r.ordinal_0based for r in (*self.native_header_rows, *self.native_body_rows)) != tuple(range(11))
                    or len({a[0] for a in self.source_name_aliases}) != 9
                    or len({a[1] for a in self.source_name_aliases}) != 9):
                raise ValueError("native correction changes its complete header/body/name denominator")
            for native, row, alias in zip(self.native_body_rows, self.rows, self.source_name_aliases, strict=True):
                if (native.texts != row.native_cells or native.ordinal_0based + 1 != row.native_table_row
                        or alias[0] != native.texts[0] or alias[2] != row.original_identifier):
                    raise ValueError("native correction identity/value join differs from its exact source cells")
                if _TSAI_SOURCE_NAME_ALIASES.get(alias[0]) != alias[1]:
                    raise ValueError("correction source-name alias differs from the reviewed source versions")
                for token in row.native_cells[1:5]:
                    _mean_error(token)
                if any(_number(token) is None for token in row.native_cells[5:]):
                    raise ValueError("native correction efficiency has no reported point")
        elif self.original_panel is not None or self.original_source_sha256 is not None:
            raise ValueError("original source binding requires complete native correction evidence")


@dataclass(frozen=True, slots=True)
class DirectEndpointRowV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/direct-endpoint-row"
    sample_id: str
    native_row: int
    native_name: str
    native_edits: str | None
    native_form: str | None
    native_oligomer: str | None
    native_identifier: str | None
    turnover: DirectEndpointObservationV1
    specificity: DirectEndpointObservationV1
    sequence_matches: tuple[NativeSequenceJoinV1, ...]
    correction: DavidiCorrectionRowV1 | None
    turnover_source_status: str
    joint_complete: bool

    def __post_init__(self) -> None:
        validate_stable_id(self.sample_id)
        if type(self.native_row) is not int or self.native_row < 1 or not self.native_name:
            raise ValueError("endpoint row requires its exact source ordinal/name")
        if self.turnover.kind != "KCAT_C" or self.specificity.kind != "SPECIFICITY_CO":
            raise ValueError("endpoint row changes its two scientific quantities")
        if self.joint_complete is not (self.turnover.reported_mean is not None and self.specificity.reported_mean is not None):
            raise ValueError("joint completeness differs from retained endpoint availability")
        if self.correction is not None and self.correction.original_identifier != self.native_identifier:
            raise ValueError("correction changes the exact native enzyme identity")
        expected_status = "SUPERSEDED_BY_SEPARATELY_ADMITTED_2025_CORRECTION" if self.correction else (
            "REPORTED_2025_NATIVE_SUMMARY" if self.native_identifier is None else "ORIGINAL_2020_REPORTED_NOT_CURRENT_VALIDATED"
        )
        if self.turnover_source_status != expected_status:
            raise ValueError("turnover source status differs from its native/correction evidence")
        for sequence in self.sequence_matches:
            if sequence.identifier_cell.token != self.native_identifier:
                raise ValueError("sequence join differs from the exact native enzyme identity")


@dataclass(frozen=True, slots=True)
class DirectEndpointPanelV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/direct-endpoint-panel"
    panel_id: str
    source_profile: str
    workbook: ObjectIdentity
    source_sha256: str
    rows: tuple[DirectEndpointRowV1, ...]
    correction_table: DavidiCorrectionTableV1 | None
    limitations: tuple[str, ...]
    exposure: str = "EXPOSED_RETROSPECTIVE_SOURCE_PANEL"
    independent_biological_units: int | None = None
    biological_joint_uncertainty_available: bool = False

    def __post_init__(self) -> None:
        validate_stable_id(self.panel_id)
        validate_sha256(self.source_sha256)
        if self.workbook.object_schema != NativeWorkbookV1.SCHEMA:
            raise ValueError("panel needs an exact native workbook identity")
        expected = tuple(range(3, 11)) if self.source_profile == "MCDONALD_2025_S3" else tuple(range(2, 11)) if self.source_profile == "DAVIDI_2020_EV1" else ()
        if not expected or tuple(r.native_row for r in self.rows) != expected:
            raise ValueError("direct panel changes its complete native enzyme-row denominator")
        if self.correction_table is not None:
            if self.source_profile != "DAVIDI_2020_EV1":
                raise ValueError("Davidi correction cannot relabel a different study")
            corrections = {r.original_identifier: r for r in self.correction_table.rows}
            if not set(corrections).issubset(r.native_identifier for r in self.rows) or any(
                r.correction != corrections.get(r.native_identifier) for r in self.rows
            ):
                raise ValueError("panel correction annotations differ from their exact admitted table")
            if self.correction_table.original_panel is not None:
                original = replace(self, correction_table=None, rows=tuple(replace(
                    r, correction=None, turnover_source_status="ORIGINAL_2020_REPORTED_NOT_CURRENT_VALIDATED",
                ) for r in self.rows))
                if (self.source_sha256 != self.correction_table.original_source_sha256
                        or self.correction_table.original_panel != ObjectIdentity.from_record(
                            "rubisco-davidi2020-direct-panel", original)):
                    raise ValueError("native correction does not bind this exact original source panel")
        elif any(r.correction is not None for r in self.rows):
            raise ValueError("correction annotation requires its separate source-bound table")
        require_sorted_unique_strings(self.limitations, field_name="limitations", allow_empty=False)
        if self.exposure != "EXPOSED_RETROSPECTIVE_SOURCE_PANEL" or self.independent_biological_units is not None or self.biological_joint_uncertainty_available:
            raise ValueError("source panel cannot invent fresh evidence, biological units or joint coverage")


def _mcdonald_endpoint(
    raw: NativeWorksheetV1, kinetic: NativeWorksheetV1, row: int, *, kind: str,
) -> DirectEndpointObservationV1:
    if kind == "KCAT_C":
        summary_column, error_column, group_column, value_column, source_group, n_column, mean_column, sd_column, sem_column = (
            "J", "K", "AL", "AM", "AN", "AP", "AQ", "AR", "AS")
        unit = "s^-1"
    else:
        summary_column, error_column, group_column, value_column, source_group, n_column, mean_column, sd_column, sem_column = (
            "F", "G", "V", "W", "X", "Z", "AA", "AB", "AC")
        unit = "dimensionless"
    summary = _cell(kinetic, f"{summary_column}{row}")
    error_cell = _cell(kinetic, f"{error_column}{row}")
    mean_cell = _cell(raw, f"{mean_column}{row}")
    sd_cell = _cell(raw, f"{sd_column}{row}")
    sem_cell = _cell(raw, f"{sem_column}{row}")
    n_cell = _cell(raw, f"{n_column}{row}")
    for dest, source in ((summary, mean_cell), (error_cell, sd_cell)):
        if dest.formula != f"'{raw.catalog_entry.name}'!{source.address}" or dest.token != source.token:
            raise ValueError("kinetic summary formula/cache does not join its declared raw source cell")
    group = _text(_cell(raw, f"A{row}"))
    if _text(_cell(raw, f"{source_group}{row}")) != group:
        raise ValueError("endpoint summary group differs from the native enzyme group")
    values = []
    for native_row in raw.row_ids:
        group_cell = raw.cell(f"{group_column}{native_row}")
        value_cell = raw.cell(f"{value_column}{native_row}")
        if group_cell is not None and group_cell.token == group and value_cell is not None and value_cell.token not in (None, "", "nm"):
            values.append(NativeRawEndpointValueV1(raw.catalog_entry.name, group_cell, value_cell, _number(value_cell.token)))
    mean = _number(summary.token)
    sd = _number(error_cell.token, nonnegative=True)
    n_token = _text(n_cell)
    if re.fullmatch(r"0|[1-9][0-9]{0,3}", n_token) is None:
        raise ValueError("native endpoint N is not an exact bounded count")
    n = int(n_token)
    sem = _number(sem_cell.token, nonnegative=True)
    raw_values = tuple(values)
    raw_mean, raw_sd, flags = _diagnostics(mean, sd, sem, n, raw_values)
    return DirectEndpointObservationV1(kind, unit, kinetic.catalog_entry.name, summary, mean,
        error_cell.token, sd, "PUBLISHED_SD_WITH_RAW_AUDIT_NOT_CALIBRATED", mean_cell, sd_cell,
        sem_cell, n_cell, n, raw_values, raw_mean, raw_sd, flags)


def build_mcdonald2025_panel(workbook: NativeWorkbookV1) -> DirectEndpointPanelV1:
    raw = workbook.worksheet(MCDONALD_SHEETS[0])
    kinetic = workbook.worksheet(MCDONALD_SHEETS[1])
    for address, token in (("F2", "(mol/mol)"), ("G2", "SD"), ("J2", "(s−1)"), ("K2", "SD")):
        if _text(_cell(kinetic, address)) != token:
            raise ValueError("McDonald kinetic table units/error headers differ from the reviewed profile")
    for address, token in (("Z2", "N ="), ("AA2", "Mean"), ("AB2", "Standard Deviation"),
                           ("AC2", "SE of Mean"), ("AP2", "N ="), ("AQ2", "Mean"),
                           ("AR2", "Standard Deviation"), ("AS2", "SE of Mean")):
        if _text(_cell(raw, address)) != token:
            raise ValueError("McDonald raw count/summary headers differ from the reviewed profile")
    names = tuple(_text(_cell(kinetic, f"A{r}")) for r in range(3, 11))
    if len(set(names)) != 8 or names[0] != "GWS1B":
        raise ValueError("McDonald complete panel needs its distinct WT and seven native mutants")
    rows = []
    for row in range(3, 11):
        name = _text(_cell(kinetic, f"A{row}"))
        if name != _text(_cell(raw, f"B{row}")):
            raise ValueError("kinetic-table enzyme name differs from its raw source group")
        turnover = _mcdonald_endpoint(raw, kinetic, row, kind="KCAT_C")
        specificity = _mcdonald_endpoint(raw, kinetic, row, kind="SPECIFICITY_CO")
        rows.append(DirectEndpointRowV1(f"mcdonald2025-row{row}", row, name, _text(_cell(raw, f"D{row}")),
            None, None, None, turnover, specificity, (), None, "REPORTED_2025_NATIVE_SUMMARY",
            turnover.reported_mean is not None and specificity.reported_mean is not None))
    limitations = (
        "COMPLETE_CONSTRUCT_AND_ASSEMBLY_NOT_VERIFIED_BY_THIS_WORKBOOK",
        "DERIVED_KCAT_O_AND_GAS_RESPONSE_CURVES_ARE_NOT_INDEPENDENT_MEASUREMENTS",
        "ENDPOINT_PAIRING_AND_BIOLOGICAL_INDEPENDENCE_UNRESOLVED",
        "EXPOSED_RETROSPECTIVE_MUTANT_PANEL_NO_PROSPECTIVE_EL_CLAIM",
        "PUBLISHED_UNCERTAINTY_RETAINED_NOT_JOINTLY_CALIBRATED",
    )
    if _text(_cell(kinetic, "S2")) == "SD" and _text(_cell(raw, "CM2")) == "SE of Mean":
        limitations += ("KO_UNCERTAINTY_HEADER_SD_VERSUS_SOURCE_SEM_CONFLICT",)
    return DirectEndpointPanelV1("rubisco-mcdonald2025-direct-panel", "MCDONALD_2025_S3",
        ObjectIdentity.from_record("rubisco-workbook." + workbook.source_sha256[:24], workbook),
        workbook.source_sha256, tuple(rows), None, tuple(sorted(limitations)))


def _davidi_endpoint(sheet: NativeWorksheetV1, row: int, *, kind: str) -> DirectEndpointObservationV1:
    cell = _cell(sheet, f"{'D' if kind == 'KCAT_C' else 'G'}{row}")
    mean, error = _mean_error(_text(cell))
    return DirectEndpointObservationV1(kind, "s^-1" if kind == "KCAT_C" else "dimensionless",
        sheet.catalog_entry.name, cell, mean, cell.token, error, "NATIVE_PLUS_MINUS_UNRESOLVED",
        None, None, None, None, None, (), None, None, ())


def build_davidi2020_panel(
    workbook: NativeWorkbookV1, *, correction_table: DavidiCorrectionTableV1 | None = None,
) -> DirectEndpointPanelV1:
    spectro = workbook.worksheet(DAVIDI_SHEETS[0])
    radio = workbook.worksheet(DAVIDI_SHEETS[1])
    for address, token in (("A1", "Organism"), ("B1", "Form"), ("C1", "Oligomeric state"),
                           ("D1", "kcat [s-1]"), ("G1", "Sc/o"), ("I1", "Identifier")):
        if _text(_cell(radio, address)) != token:
            raise ValueError("Davidi radiometric headers/units differ from the reviewed profile")
    for address, token in (("A1", "Identifier"), ("F1", "Protein seq"), ("G1", "DNA seq")):
        if _text(_cell(spectro, address)) != token:
            raise ValueError("Davidi sequence identity headers differ from the reviewed profile")
    corrections = {r.original_identifier: r for r in correction_table.rows} if correction_table else {}
    rows = []
    for row in range(2, 11):
        identifier = _text(_cell(radio, f"I{row}"))
        sequences = []
        for native_row in spectro.row_ids:
            id_cell = spectro.cell(f"A{native_row}")
            if id_cell is not None and id_cell.token == identifier:
                sequences.append(NativeSequenceJoinV1(spectro.catalog_entry.name, native_row, id_cell,
                    _cell(spectro, f"F{native_row}"), _cell(spectro, f"G{native_row}")))
        correction = corrections.get(identifier)
        rows.append(DirectEndpointRowV1(f"davidi2020-row{row}", row, _text(_cell(radio, f"A{row}")), None,
            _text(_cell(radio, f"B{row}")), _text(_cell(radio, f"C{row}")), identifier,
            _davidi_endpoint(radio, row, kind="KCAT_C"), _davidi_endpoint(radio, row, kind="SPECIFICITY_CO"),
            tuple(sequences), correction,
            "SUPERSEDED_BY_SEPARATELY_ADMITTED_2025_CORRECTION" if correction else "ORIGINAL_2020_REPORTED_NOT_CURRENT_VALIDATED",
            True))
    return DirectEndpointPanelV1("rubisco-davidi2020-direct-panel", "DAVIDI_2020_EV1",
        ObjectIdentity.from_record("rubisco-workbook." + workbook.source_sha256[:24], workbook),
        workbook.source_sha256, tuple(rows), correction_table, tuple(sorted((
            "BIOLOGICAL_INDEPENDENCE_AND_CROSS_ASSAY_PAIRING_UNKNOWN",
            "CORRECTED_HISTORICAL_AND_2025_REMEASURED_TURNOVER_REMAIN_DISTINCT",
            "FORM_I_SMALL_SUBUNITS_AND_COMPLETE_ASSAY_PREPARATIONS_NOT_VERIFIED",
            "ORIGINAL_2020_TURNOVER_NOT_A_CURRENT_UNCORRECTED_KINETIC_LABEL",
            "SPECTROSCOPIC_AND_RADIOMETRIC_SOURCES_REMAIN_DISTINCT",
            "TURNOVER_CORRECTION_DOES_NOT_REMEASURE_HISTORICAL_SPECIFICITY",
        ))))


_TSAI_SOURCE_NAME_ALIASES = {
    "Gallionella": "Gallionella sp.",
    "Zetaproteobacterium": "Zetaproteobacterium",
    "H. marinus": "H. marinus",
    "Sulfurivirga": "S. caldicuralii",
    "Unknown organism (Actinosporangium)": "Unknown organism",
    "Zetaproteobacteria_53_45": "Zetaproteobacteria_53_45",
    "A. ferrooxidans": "A. ferrooxidans",
    "R. rubrum": "R. rubrum",
    "S. elongatus": "S. elongatus",
}


def _validate_tsai_headers(headers: NativeHTMLTableRowV1, subheaders: NativeHTMLTableRowV1) -> None:
    expected_headers = ("", "Rate, kcat [s−1]", "Affinity, Km (CO2) [µM]",
                        "Carboxylation efficiency, kcat/Km [s−1 mM−1]")
    if (headers.texts != expected_headers or tuple(c.colspan for c in headers.cells) != (1, 2, 2, 2)
            or any(c.rowspan != 1 for c in (*headers.cells, *subheaders.cells))
            or tuple(c.colspan for c in subheaders.cells) != (1,) * 7
            or subheaders.texts != ("", "Davidi et al corrected", "This study", "Davidi et al corrected",
                                   "This study", "Davidi et al corrected", "This study")):
        raise ValueError("native correction endpoint units or historical/remeasured column hierarchy differs")


def decode_tsai2025_correction(
    payload: bytes, original_panel: DirectEndpointPanelV1, *, expected_sha256: str = TSAI_2025_SOURCE_SHA256,
) -> DavidiCorrectionTableV1:
    """Decode exact primary Table 1, joining reviewed source names, never row order.

    The alias interpretation is bound to the two exact inspected source
    revisions. A future article or original-panel revision needs a reviewed
    successor profile rather than reusing these aliases by accident.
    """
    validate_sha256(expected_sha256)
    if (expected_sha256 != TSAI_2025_SOURCE_SHA256 or not 1 <= len(payload) <= MAX_HTML_BYTES
            or sha256(payload).hexdigest() != expected_sha256):
        raise ValueError("correction source differs from the exact reviewed primary custody")
    if (original_panel.source_profile != "DAVIDI_2020_EV1" or original_panel.source_sha256 != DAVIDI_SOURCE_SHA256
            or original_panel.correction_table is not None):
        raise ValueError("correction aliases require the exact inspected original source version")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("primary correction HTML must be UTF-8") from error
    if "\x00" in text or "<!ENTITY" in text.upper():
        raise ValueError("primary correction HTML declarations/NUL bytes are forbidden")
    parser = _TableParser(target_section_id="Tab1")
    parser.feed(text)
    parser.close()
    if (parser.stack or parser.target_sections != 1 or parser.target_tables != 1
            or parser.dois != ["10.1038/s44318-025-00419-y"] or len(parser.rows) != 11):
        raise ValueError("native correction DOI, table selector or complete denominator differs")
    headers, subheaders = parser.rows[:2]
    _validate_tsai_headers(headers, subheaders)
    by_name = {r.native_name: r for r in original_panel.rows}
    if len(by_name) != 9 or set(by_name) != set(_TSAI_SOURCE_NAME_ALIASES.values()):
        raise ValueError("original source roster does not match the exact reviewed name-alias denominator")
    rows = []
    aliases = []
    seen = set()
    for native in parser.rows[2:]:
        cells = native.texts
        if len(cells) != 7 or cells[0] not in _TSAI_SOURCE_NAME_ALIASES or cells[0] in seen:
            raise ValueError("native correction has missing, duplicate or unreviewed enzyme identities")
        seen.add(cells[0])
        original = by_name[_TSAI_SOURCE_NAME_ALIASES[cells[0]]]
        if original.native_identifier is None:
            raise ValueError("original correction target lacks an exact source enzyme identifier")
        # Check all four mean/error cells. Efficiency columns are positive point
        # tokens; they never become specificity labels.
        for token in cells[1:5]:
            _mean_error(token)
        for token in cells[5:]:
            if _number(token) is None:
                raise ValueError("correction efficiency column has no reported point")
        rows.append(DavidiCorrectionRowV1(original.native_identifier, native.ordinal_0based + 1,
                                         cells, cells[1], cells[2]))
        aliases.append((cells[0], original.native_name, original.native_identifier))
    return DavidiCorrectionTableV1(expected_sha256, "10.1038/s44318-025-00419-y", "section#Tab1/table",
        subheaders.texts, tuple(rows), native_header_rows=tuple(parser.rows[:2]),
        native_body_rows=tuple(parser.rows[2:]), source_name_aliases=tuple(aliases),
        original_panel=ObjectIdentity.from_record("rubisco-davidi2020-direct-panel", original_panel),
        original_source_sha256=original_panel.source_sha256)
