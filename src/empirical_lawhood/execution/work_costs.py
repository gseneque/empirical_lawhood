# SPDX-License-Identifier: MPL-2.0
"""Actual work and measurement coverage, separate from estimates and authority.

Every work scope has its own exclusive part, including an enclosing invocation's
otherwise unmeasured overhead. Inclusive observations cover that part and all
descendants. Original observations survive selection; recovery is separate work
that references, rather than duplicates, its earlier physical work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_nonempty, validate_sha256, validate_stable_id
from empirical_lawhood.science.models.time import validate_utc_timestamp


MAX_COST_ROWS = 4096
MAX_COST_EVIDENCE_FILES = 240
MAX_COST_SOURCE_BYTES = 16 * 1024**2
MAX_COST_EVIDENCE_BYTES = 64 * 1024**2


def _rows(values, kind, attribute, name, *, nonempty=False):
    if (type(values) is not tuple or len(values) > MAX_COST_ROWS
            or (nonempty and not values) or any(type(row) is not kind for row in values)):
        raise ValueError(name + " requires a bounded immutable typed census")
    require_sorted_unique_ids(values, attribute=attribute, field_name=name)


def _ids(values, name, *, nonempty=False):
    if type(values) is not tuple or len(values) > MAX_COST_ROWS:
        raise ValueError(name + " requires a bounded immutable census")
    require_sorted_unique_strings(values, field_name=name, allow_empty=not nonempty)
    for value in values:
        validate_stable_id(value, field_name=name)


def _text(value, name):
    validate_nonempty(value, field_name=name)
    if len(value.encode('utf-8')) > 4096:
        raise ValueError(name + " exceeds its descriptive byte bound")


def _number(value):
    if value is None:
        return
    validate_decimal(value, field_name="measured cost", minimum=Decimal(0))
    parts = value.as_tuple()
    if len(parts.digits) > 96 or abs(parts.exponent) > 96:
        raise ValueError("measured cost exceeds its exact decimal bound")


def _sum(values):
    """Add bounded decimal observations without the ambient arithmetic context."""
    values = tuple(values)
    if not values:
        return Decimal(0)
    exponent = min(value.as_tuple().exponent for value in values)
    coefficient = sum(int(''.join(map(str, value.as_tuple().digits)))
                      * 10 ** (value.as_tuple().exponent - exponent) for value in values)
    return Decimal((0, tuple(map(int, str(coefficient))), exponent))


def _pointer(value, measured):
    if value is None:
        if measured is not None:
            raise ValueError("known cost requires its original JSON value pointer")
        return
    if (type(value) is not tuple or not value or len(value) > 32
            or any(type(part) is not str or not part or len(part) > 256 for part in value)):
        raise ValueError("cost source requires a bounded JSON field/index pointer")


@dataclass(frozen=True, slots=True)
class CostEvidence(CanonicalRecord):
    """Exact original source bytes; a binding does not certify their accuracy."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/work-cost-evidence"
    evidence_id: str
    sha256: str
    size_bytes: int
    description: str
    record_identity: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.evidence_id)
        validate_sha256(self.sha256)
        if type(self.size_bytes) is not int or not 0 < self.size_bytes <= MAX_COST_SOURCE_BYTES:
            raise ValueError("cost evidence requires an explicit bounded original byte count")
        _text(self.description, "cost evidence description")
        if self.record_identity is not None and (
                type(self.record_identity) is not ObjectIdentity
                or self.record_identity.object_fingerprint != self.sha256):
            raise ValueError("canonical cost evidence differs from its original record bytes")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.evidence_id, self)


class WorkCostOutcome(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    RECOVERY = "RECOVERY"
    OBSERVED_INVOCATION = "OBSERVED_INVOCATION"


@dataclass(frozen=True, slots=True)
class CostWorkScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/cost-work-scope"
    scope_id: str
    subject: ObjectIdentity
    evidence_id: str
    witness_evidence_ids: tuple[str, ...]
    outcome: WorkCostOutcome
    description: str
    parent_scope_id: str | None = None
    reuses_scope_ids: tuple[str, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.scope_id)
        validate_stable_id(self.evidence_id)
        if type(self.subject) is not ObjectIdentity or type(self.outcome) is not WorkCostOutcome:
            raise ValueError("cost work requires its actual typed subject and outcome")
        _ids(self.witness_evidence_ids, "work witnesses", nonempty=True)
        _ids(self.reuses_scope_ids, "reused work")
        _text(self.description, "work description")
        if self.parent_scope_id is not None:
            validate_stable_id(self.parent_scope_id)
        if self.scope_id == self.parent_scope_id or self.scope_id in self.reuses_scope_ids:
            raise ValueError("cost work cannot contain or reuse itself")
        if self.reuses_scope_ids and self.outcome is not WorkCostOutcome.RECOVERY:
            raise ValueError("completed-work references require a distinct recovery observation")


class CostQuantity(StrEnum):
    CPU_SECONDS = "CPU_SECONDS"
    GPU_DEVICE_SECONDS = "GPU_DEVICE_SECONDS"
    ELAPSED_SECONDS = "ELAPSED_SECONDS"
    RETAINED_BYTES = "RETAINED_BYTES"
    PEAK_RSS_BYTES = "PEAK_RSS_BYTES"


class CostCoverage(StrEnum):
    EXCLUSIVE = "EXCLUSIVE"
    INCLUDING_DESCENDANTS = "INCLUDING_DESCENDANTS"


@dataclass(frozen=True, slots=True)
class WorkCostMeasurement(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/work-cost-measurement"
    measurement_id: str
    scope_id: str
    coverage: CostCoverage
    quantity: CostQuantity
    value: Decimal | None
    evidence_id: str
    value_pointer: tuple[str, ...] | None
    scope_description: str

    def __post_init__(self):
        for name in ("measurement_id", "scope_id", "evidence_id"):
            validate_stable_id(getattr(self, name))
        if type(self.coverage) is not CostCoverage or type(self.quantity) is not CostQuantity:
            raise ValueError("measurement requires an explicit quantity and inclusion rule")
        _number(self.value)
        _pointer(self.value_pointer, self.value)
        _text(self.scope_description, "measurement scope")
        if self.quantity in (CostQuantity.RETAINED_BYTES, CostQuantity.PEAK_RSS_BYTES) and (
                self.value is not None and self.value != self.value.to_integral_value()):
            raise ValueError("measured bytes require a whole number of bytes")


@dataclass(frozen=True, slots=True)
class BilledResourceWindow(CanonicalRecord):
    """One actual billed resource interval, with its complete benefiting work.

    A financial upper bound, rate estimate or counterfactual is not a bill.
    Sharing this record does not split its charge among invented attempts.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/billed-resource-window"
    window_id: str
    resource_id: str
    started_at_utc: str
    ended_at_utc: str
    work_scope_ids: tuple[str, ...]
    billed_usd: Decimal | None
    evidence_id: str
    value_pointer: tuple[str, ...] | None
    billing_basis: str
    resource_pointer: tuple[str, ...]
    started_pointer: tuple[str, ...]
    ended_pointer: tuple[str, ...]

    def __post_init__(self):
        for name in ("window_id", "resource_id", "evidence_id"):
            validate_stable_id(getattr(self, name))
        for name in ("started_at_utc", "ended_at_utc"):
            validate_utc_timestamp(getattr(self, name), field_name=name)
        if datetime.fromisoformat(self.ended_at_utc) <= datetime.fromisoformat(self.started_at_utc):
            raise ValueError("billing window requires a positive actual UTC interval")
        _ids(self.work_scope_ids, "billed work", nonempty=True)
        _number(self.billed_usd)
        _pointer(self.value_pointer, self.billed_usd)
        for pointer in (self.resource_pointer, self.started_pointer, self.ended_pointer):
            _pointer(pointer, Decimal(0))
        _text(self.billing_basis, "original billing basis")


@dataclass(frozen=True, slots=True)
class WorkCostAccount(CanonicalRecord):
    """A bounded actual-work census and original observations, never estimates."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/work-cost-account"
    account_id: str
    comparison_scope: str
    evidence: tuple[CostEvidence, ...]
    work: tuple[CostWorkScope, ...]
    measurements: tuple[WorkCostMeasurement, ...]
    billing_windows: tuple[BilledResourceWindow, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.account_id)
        _text(self.comparison_scope, "actual comparison scope")
        _rows(self.evidence, CostEvidence, "evidence_id", "cost evidence", nonempty=True)
        if len(self.evidence) > MAX_COST_EVIDENCE_FILES:
            raise ValueError("cost evidence exceeds its closed publication member allowance")
        _rows(self.work, CostWorkScope, "scope_id", "actual work", nonempty=True)
        _rows(self.measurements, WorkCostMeasurement, "measurement_id", "measurements")
        _rows(self.billing_windows, BilledResourceWindow, "window_id", "billing windows")
        if sum(row.size_bytes for row in self.evidence) > MAX_COST_EVIDENCE_BYTES:
            raise ValueError("complete cost evidence exceeds its explicit aggregate byte bound")
        sources = {row.evidence_id: row for row in self.evidence}
        scopes = {row.scope_id: row for row in self.work}
        subjects = set()
        for row in self.work:
            source = sources.get(row.evidence_id)
            if source is None or row.subject != (source.record_identity or source.identity):
                raise ValueError("work subject differs from its exact original evidence binding")
            key = ((row.subject.object_schema, row.subject.object_version, row.subject.object_fingerprint)
                   if source.record_identity is not None else ("ORIGINAL_BYTES", source.sha256))
            if key in subjects:
                raise ValueError("one physical work subject cannot be renamed into another cost scope")
            subjects.add(key)
            if not set(row.witness_evidence_ids) <= sources.keys():
                raise ValueError("work omits its original completion, contact or invocation witnesses")
            if row.parent_scope_id is not None and row.parent_scope_id not in scopes:
                raise ValueError("cost work omits its enclosing scope")
            if not set(row.reuses_scope_ids) <= scopes.keys():
                raise ValueError("recovery omits its referenced original work")
        for row in self.work:
            visited, current = set(), row
            while current.parent_scope_id is not None:
                if current.scope_id in visited:
                    raise ValueError("cost work contains a parent cycle")
                visited.add(current.scope_id); current = scopes[current.parent_scope_id]
            for reused in row.reuses_scope_ids:
                if reused in descendants(self, row.scope_id):
                    raise ValueError("recovery cannot count reused work as new contained work")
        for row in (*self.measurements, *self.billing_windows):
            if row.evidence_id not in sources:
                raise ValueError("cost observation omits its original source")
        if any(row.scope_id not in scopes for row in self.measurements):
            raise ValueError("measurement changes the actual work census")
        if any(not set(row.work_scope_ids) <= scopes.keys() for row in self.billing_windows):
            raise ValueError("a shared bill requires its whole work scope; partial allocation is not implicit")
        coordinates = {}
        masks = _coverage_masks(self)
        for row in self.measurements:
            if row.value_pointer is None:
                continue
            key = (sources[row.evidence_id].sha256, row.value_pointer)
            meaning = (row.quantity, _coverage(masks, row))
            if key in coordinates and coordinates[key] != meaning:
                raise ValueError("one original measurement cannot acquire another quantity or work scope")
            coordinates[key] = meaning
        for row in self.billing_windows:
            if row.value_pointer is None:
                continue
            key = (sources[row.evidence_id].sha256, row.value_pointer)
            meaning = ("BILLED_USD", row.resource_id, row.started_at_utc, row.ended_at_utc, row.work_scope_ids)
            if key in coordinates and coordinates[key] != meaning:
                raise ValueError("one original billed amount cannot be assigned another resource or interval")
            coordinates[key] = meaning
        _selected_bills(self.billing_windows)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.account_id, self)


def descendants(account: WorkCostAccount, scope_id: str) -> frozenset[str]:
    """Include the scope's exclusive part, even when its cost is unknown."""
    result = {scope_id}
    children = {}
    for row in account.work:
        children.setdefault(row.parent_scope_id, []).append(row.scope_id)
    pending = [scope_id]
    while pending:
        for child in children.get(pending.pop(), ()):
            if child in result:
                raise ValueError("cost work contains a parent cycle")
            result.add(child); pending.append(child)
    return frozenset(result)


def _coverage_masks(account):
    # A bit per exclusive part keeps a deep 4,096-node hierarchy bounded without
    # retaining a Python set of every descendant at every ancestor.
    exclusive = {row.scope_id:1 << index for index,row in enumerate(account.work)}
    inclusive = dict(exclusive)
    children = {}
    for row in account.work:
        children.setdefault(row.parent_scope_id,[]).append(row.scope_id)
    order, pending = [], list(children.get(None,()))
    while pending:
        scope = pending.pop(); order.append(scope); pending.extend(children.get(scope,()))
    if len(order) != len(account.work):
        raise ValueError("cost work has an unresolved parent or cycle")
    parents = {row.scope_id:row.parent_scope_id for row in account.work}
    for scope in reversed(order):
        parent = parents[scope]
        if parent is not None:
            inclusive[parent] |= inclusive[scope]
    return exclusive,inclusive


def _coverage(masks, measurement):
    exclusive,inclusive = masks
    return (inclusive if measurement.coverage is CostCoverage.INCLUDING_DESCENDANTS else exclusive)[measurement.scope_id]


def _disjoint_observations(observations):
    selected, covered = [], 0
    for scope,row in sorted(observations.items(),key=lambda pair:(-pair[0].bit_count(),pair[1].measurement_id)):
        if scope & covered == scope:
            continue
        if scope & covered:
            raise ValueError("cost observations overlap without an exact inclusion relationship")
        selected.append(row); covered |= scope
    return selected,covered


def _selected_bills(bills):
    windows, aliases = {}, []
    for bill in bills:
        start, end = map(datetime.fromisoformat, (bill.started_at_utc, bill.ended_at_utc))
        key = (bill.resource_id, start, end)
        if key in windows:
            previous = windows[key]
            if (bill.billed_usd, bill.work_scope_ids, bill.evidence_id, bill.value_pointer, bill.billing_basis,
                    bill.resource_pointer, bill.started_pointer, bill.ended_pointer) != (
                    previous.billed_usd, previous.work_scope_ids, previous.evidence_id, previous.value_pointer, previous.billing_basis,
                    previous.resource_pointer, previous.started_pointer, previous.ended_pointer):
                raise ValueError("one shared billing window has conflicting observations")
            aliases.append(bill.window_id)
            continue
        if any(resource == bill.resource_id and max(start, other_start) < min(end, other_end)
               for resource, other_start, other_end in windows):
            raise ValueError("overlapping resource bills need original disjoint intervals, not an inferred split")
        windows[key] = bill
    return tuple(windows.values()), tuple(aliases)


def summarize_work_cost(account: WorkCostAccount) -> dict:
    """Choose a nonoverlapping cover; missing observations never become zero.

    CPU and retained storage are additive over declared disjoint exclusive
    work. Device time, elapsed time and peak RSS require one observation of
    the whole account. Concurrent GPU activity, clocks and peaks are not added.
    """
    if type(account) is not WorkCostAccount:
        raise TypeError("cost aggregation requires its exact actual-work account")
    account.__post_init__()
    masks = _coverage_masks(account)
    universe = (1 << len(account.work))-1
    quantities = {}
    for quantity in CostQuantity:
        observations = tuple(row for row in account.measurements if row.quantity is quantity)
        by_coverage = {}
        for row in observations:
            covered = _coverage(masks, row)
            known = by_coverage.get(covered)
            if known is not None and row.value is not None and known.value != row.value:
                raise ValueError("the same cost quantity and exact work coverage have conflicting measured values")
            if row.value is not None and known is None:
                by_coverage[covered] = row
        selected,covered = _disjoint_observations(by_coverage)
        missing = [row.scope_id for index,row in enumerate(account.work) if not covered & (1 << index)]
        additive = quantity in (CostQuantity.CPU_SECONDS, CostQuantity.RETAINED_BYTES)
        if additive:
            for outer,parent in by_coverage.items():
                components,component_mask = _disjoint_observations({scope:row for scope,row in by_coverage.items()
                    if scope != outer and scope & outer == scope})
                lower = _sum(row.value for row in components)
                if lower > parent.value or (component_mask == outer and lower != parent.value):
                    raise ValueError("nested cost measurements contradict their declared additive inclusion scopes")
        whole = next((row for scope, row in by_coverage.items() if scope == universe), None)
        subtotal = _sum(row.value for row in selected)
        total = (subtotal if not missing else None) if additive else (None if whole is None else whole.value)
        quantities[quantity.value] = {
            "value": total, "status": "MEASURED" if total is not None else "UNKNOWN",
            "aggregation": "DISJOINT_WORK_SUM" if additive else "WHOLE_ACCOUNT_OBSERVATION_REQUIRED",
            "known_disjoint_subtotal": subtotal if additive else None,
            "selected_measurement_ids": tuple(row.measurement_id for row in selected),
            "included_observations_not_added": tuple(row.measurement_id for row in observations
                if row.value is not None and row not in selected),
            "unknown_measurement_ids": tuple(row.measurement_id for row in observations if row.value is None),
            "unmeasured_exclusive_work_ids": tuple(missing),
            "component_observations": tuple({"measurement_id":row.measurement_id,"value":row.value,
                "scope_id":row.scope_id,"coverage":row.coverage.value,"scope_description":row.scope_description}
                for row in observations),
        }
    bills, aliases = _selected_bills(account.billing_windows)
    known_billing = _sum(bill.billed_usd for bill in bills if bill.billed_usd is not None)
    billed = known_billing if bills and all(row.billed_usd is not None for row in bills) else None
    return {"schema":"empirical-lawhood/operational/work-cost-summary","version":"1.0.0",
        "account":account.identity.to_document(),"comparison_scope":account.comparison_scope,
        "quantities":quantities,"billed_usd":billed,"known_billed_subtotal_usd":known_billing,
        "selected_billing_window_ids":tuple(row.window_id for row in bills),
        "shared_billing_aliases_not_added":aliases,
        "unknown_billing_window_ids":tuple(row.window_id for row in bills if row.billed_usd is None),
        "billing_status":"OBSERVED_SELECTED_BILLS" if billed is not None else "UNKNOWN",
        "billing_completeness":"DECLARED_WINDOWS_ONLY",
        "work_outcomes":tuple({"scope_id":row.scope_id,"outcome":row.outcome.value,
            "subject":row.subject.to_document(),"reuses_scope_ids":row.reuses_scope_ids} for row in account.work),
        "estimates_included":False,"scientific_authority":"NONE","new_execution":False}


def record_cost_evidence(record: CanonicalRecord, *, evidence_id: str, object_id: str,
                         description: str) -> CostEvidence:
    """Bind an already read original record; this performs no custody read."""
    if not isinstance(record,CanonicalRecord):
        raise TypeError("cost record evidence requires an original canonical record")
    return CostEvidence(evidence_id, record.fingerprint(), record.canonical_size_bytes(), description,
                        ObjectIdentity.from_record(object_id, record))


__all__ = ["BilledResourceWindow", "CostCoverage", "CostEvidence", "CostQuantity", "CostWorkScope",
           "WorkCostAccount", "WorkCostMeasurement", "WorkCostOutcome", "descendants",
           "record_cost_evidence", "summarize_work_cost"]
