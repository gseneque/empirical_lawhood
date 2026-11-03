# SPDX-License-Identifier: MPL-2.0
"""New identities retain unknown completion; no old result schema is retyped."""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    validate_stable_id,
    validate_sha256,
    validate_relative_locator,
)
from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import (
    DiagnosticSource,
)
from empirical_lawhood.runtime.artifacts import ArtifactManifest

NAMESPACE = "battery-diagnostic-obstruction"
UNIT = "unit.battery-thermal-inquiry.lgm50-family"
QUESTION = "Does authentic adverse diagnostic custody establish an operational obstruction and explicitly unknown numerical completion, without supplying a diagnostic result?"
ROLES = ("contact", "event", "index", "plan", "terminal")


def identity(record):
    key = next(
        k for k in ("source_id", "config_id", "product_id") if hasattr(record, k)
    )
    return ObjectIdentity.from_record(getattr(record, key), record)


@dataclass(frozen=True, slots=True)
class CustodyMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-diagnostic-obstruction/custody-member"
    )
    relative_path: str
    size_bytes: int
    sha256: str

    def __post_init__(self):
        validate_relative_locator(self.relative_path)
        validate_sha256(self.sha256)
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise ValueError("custody member requires exact nonnegative byte census")


@dataclass(frozen=True, slots=True)
class OperationalRecord(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-diagnostic-obstruction/operational-record"
    )
    role: str
    relative_path: str
    raw_utf8: str
    manifest_raw_utf8: str

    def __post_init__(self):
        if self.role not in ROLES:
            raise ValueError(
                "obstruction changes its complete retained operational record roles"
            )
        validate_relative_locator(self.relative_path)
        if not self.raw_utf8 or not self.manifest_raw_utf8:
            raise ValueError("obstruction omits original record or manifest bytes")


@dataclass(frozen=True, slots=True)
class ObstructionSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-diagnostic-obstruction/source"
    source_id: str
    diagnostic_source: DiagnosticSource
    prior_supply: ObjectIdentity
    records: tuple[OperationalRecord, ...]
    complete_custody: tuple[CustodyMember, ...]
    input_manifests: tuple[ArtifactManifest, ...]
    invocation_report_sha256: str
    invocation_cost_raw_utf8: str
    kernel_excerpt_raw_utf8: str
    kernel_excerpt_sha256: str
    kernel_attribution_scope: str = (
        "HOST_JOURNAL_PID_EVIDENCE_NOT_A_SCIENTIFIC_COMPLETION_LEDGER"
    )

    @property
    def original(self):
        return self.diagnostic_source.original

    def __post_init__(self):
        validate_stable_id(self.source_id)
        self.diagnostic_source.__post_init__()
        if (
            self.prior_supply.object_schema
            != "empirical-lawhood/battery-thermal-inquiry/supply"
            or self.prior_supply.object_fingerprint
            != self.diagnostic_source.prior_supply_sha256
        ):
            raise ValueError(
                "obstruction changes actual original negative supply identity"
            )
        if tuple(r.role for r in self.records) != ROLES:
            raise ValueError(
                "obstruction omits or duplicates complete primary operational records"
            )
        paths = tuple(r.relative_path for r in self.complete_custody)
        if paths != tuple(sorted(set(paths))) or not paths:
            raise ValueError(
                "obstruction custody must retain exact sorted complete census"
            )
        for record in (*self.records, *self.complete_custody):
            record.__post_init__()
        validate_sha256(self.invocation_report_sha256)
        validate_sha256(self.kernel_excerpt_sha256)
        if (
            sha256(self.kernel_excerpt_raw_utf8.encode()).hexdigest()
            != self.kernel_excerpt_sha256
        ):
            raise ValueError("obstruction substitutes original kernel excerpt bytes")
        if (
            self.kernel_attribution_scope
            != "HOST_JOURNAL_PID_EVIDENCE_NOT_A_SCIENTIFIC_COMPLETION_LEDGER"
        ):
            raise ValueError(
                "kernel evidence cannot invent numerical completion or independently authenticate a native PID"
            )


@dataclass(frozen=True, slots=True)
class ObstructionAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-diagnostic-obstruction/assessment"
    )
    product_id: str
    source: ObstructionSource
    original_negative_supply: ObjectIdentity
    diagnostic_run_id: str
    execution_plan: ObjectIdentity
    native_contact: ObjectIdentity
    recovery_terminal: ObjectIdentity
    selected_forecast_roster_count: int = 12
    entered_registered_native_operations: int = 1
    returned_materialized_trace_rows: int = 0
    returned_diagnostic_results: int = 0
    actual_forecast_provider_entries: int | None = None
    actual_forecast_completions: int | None = None
    actual_charging_subcalls: int | None = None
    actual_initial_soc_soh_subcalls: int | None = None
    numerical_disposition: A = A.UNEVALUABLE
    method_disposition: A = A.SATISFIED
    new_native_contacts: int = 0
    new_physical_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        validate_stable_id(self.diagnostic_run_id)
        self.source.__post_init__()
        if self.original_negative_supply != self.source.prior_supply:
            raise ValueError("obstruction assessment substitutes prior supply")
        if (
            self.selected_forecast_roster_count,
            self.entered_registered_native_operations,
            self.returned_materialized_trace_rows,
            self.returned_diagnostic_results,
        ) != (12, 1, 0, 0):
            raise ValueError(
                "obstruction changes selected/entered/returned custody census"
            )
        if any(
            x is not None
            for x in (
                self.actual_forecast_provider_entries,
                self.actual_forecast_completions,
                self.actual_charging_subcalls,
                self.actual_initial_soc_soh_subcalls,
            )
        ):
            raise ValueError(
                "absent ledger cannot establish actual zero, completion or attempted forecast counts"
            )
        if (
            self.numerical_disposition is not A.UNEVALUABLE
            or self.method_disposition is not A.SATISFIED
            or self.new_native_contacts != 0
            or self.new_physical_units != 0
        ):
            raise ValueError(
                "obstruction cannot supply numerical adequacy, fresh native evidence or physical qualification"
            )

    @property
    def scope(self):
        from .science import scope

        return scope(self.source)


@dataclass(frozen=True, slots=True)
class ObstructionOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/battery-diagnostic-obstruction/operation-config"
    )
    config_id: str
    source: ObstructionSource

    def __post_init__(self):
        if self.config_id != "config." + NAMESPACE + ".assess":
            raise ValueError("obstruction changes registered pure operation")
        self.source.__post_init__()

    @property
    def operands(self):
        return tuple(
            sorted(
                (identity(self.source), self.source.prior_supply),
                key=lambda r: r.object_id,
            )
        )
