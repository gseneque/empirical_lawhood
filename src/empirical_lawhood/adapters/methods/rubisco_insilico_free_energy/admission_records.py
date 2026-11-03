# SPDX-License-Identifier: MPL-2.0
"""Additive current-use reports; frozen v1 producer records remain unchanged."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id


# This is an explicit scalar reporting convention, not scientific precedence.
REPORTED_PRECEDENCE = (A.UNEVALUABLE, A.REFUSED, A.FALSIFIED, A.UNSUPPORTED, A.NOT_ATTEMPTED, A.SATISFIED)
METHOD_DESCRIPTION = (
    "Exact immutable selection/window/trace census; typed finite production ordinals; "
    "SAT requires every selected nonempty observation and reported completed calls; "
    "scalar UNEVALUABLE,REFUSED,FALSIFIED,UNSUPPORTED,NOT_ATTEMPTED,SATISFIED; "
    "producer reports never authenticate raw custody, unique actual calls, independent sampling or biology."
)
METHOD_CONTRACT = ObjectIdentity(
    "method.rubisco-free-energy.current-window-admission",
    "empirical-lawhood/rubisco-insilico-free-energy/current-window-admission-method",
    "1.0.0", sha256(METHOD_DESCRIPTION.encode()).hexdigest(),
)


def identity(value, label):
    if type(value) is not ObjectIdentity:
        raise ValueError(label + " must be an exact ObjectIdentity")
    value.__post_init__()


def count(value, label):
    if type(value) is not int or value < 0:
        raise ValueError(label + " must be a nonnegative integer")


def expense(value):
    if value is not None and (type(value) is not Decimal or not value.is_finite() or value < 0):
        raise ValueError("reported expense must be finite nonnegative Decimal or unknown")


@dataclass(frozen=True, slots=True)
class WindowAdmission(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-free-energy/window-admission"
    VERSION: ClassVar[str] = "1.0.0"
    admission_id: str
    selection: ObjectIdentity
    window: ObjectIdentity
    legacy_trace: ObjectIdentity
    reported_disposition: A
    selected_sample_count: int
    retained_sample_count: int
    missing_selected_sample_count: int
    reported_attempted_energy_calls: int
    reported_completed_energy_calls: int
    reported_cpu_seconds: Decimal | None
    reported_wall_seconds: Decimal | None
    raw_files: tuple[ObjectIdentity, ...]
    reason_codes: tuple[str, ...]
    record_consistency_disposition: A = A.SATISFIED
    raw_custody_assessment_disposition: A = A.NOT_ATTEMPTED
    native_call_coverage_assessment_disposition: A = A.NOT_ATTEMPTED
    actual_attempted_energy_calls: int | None = None
    actual_completed_energy_calls: int | None = None

    def __post_init__(self):
        validate_stable_id(self.admission_id)
        for name in ("selection", "window", "legacy_trace"):
            identity(getattr(self, name), name)
        if type(self.reported_disposition) is not A:
            raise ValueError("reported disposition must be typed")
        for name in ("selected_sample_count", "retained_sample_count", "missing_selected_sample_count",
                     "reported_attempted_energy_calls", "reported_completed_energy_calls"):
            count(getattr(self, name), name)
        if (self.retained_sample_count + self.missing_selected_sample_count != self.selected_sample_count
                or self.reported_completed_energy_calls > self.reported_attempted_energy_calls):
            raise ValueError("admission changes selected sample or reported call denominator")
        if type(self.raw_files) is not tuple:
            raise ValueError("raw reference census must be an exact unique tuple")
        for raw in self.raw_files:
            identity(raw, "raw reference")
        if len(set(self.raw_files)) != len(self.raw_files):
            raise ValueError("raw reference census must be an exact unique tuple")
        if type(self.reason_codes) is not tuple:
            raise ValueError("admission reason codes must be sorted and unique")
        for reason in self.reason_codes:
            if type(reason) is not str or not reason.strip():
                raise ValueError("admission reason codes must be nonempty strings")
        if self.reason_codes != tuple(sorted(set(self.reason_codes))):
            raise ValueError("admission reason codes must be sorted and unique")
        for value in (self.reported_cpu_seconds, self.reported_wall_seconds):
            expense(value)
        if self.reported_disposition is A.SATISFIED and (
                self.selected_sample_count == 0 or self.missing_selected_sample_count != 0
                or self.reported_attempted_energy_calls == 0
                or self.reported_completed_energy_calls != self.reported_attempted_energy_calls
                or not self.raw_files):
            raise ValueError("positive admission omits selected observations/reported calls/raw references")
        if self.reported_disposition is A.NOT_ATTEMPTED and (
                self.reported_attempted_energy_calls or self.reported_completed_energy_calls
                or self.retained_sample_count or self.raw_files):
            raise ValueError("NOT_ATTEMPTED admission contains reported actual work")
        if (self.record_consistency_disposition is not A.SATISFIED
                or self.raw_custody_assessment_disposition is not A.NOT_ATTEMPTED
                or self.native_call_coverage_assessment_disposition is not A.NOT_ATTEMPTED
                or self.actual_attempted_energy_calls is not None or self.actual_completed_energy_calls is not None):
            raise ValueError("pure record consistency cannot authenticate raw custody or actual native-call coverage")


@dataclass(frozen=True, slots=True)
class WindowCensusAdmission(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-free-energy/window-census-admission"
    VERSION: ClassVar[str] = "1.0.0"
    report_id: str
    selection: ObjectIdentity
    selected_windows: tuple[ObjectIdentity, ...]
    windows: tuple[WindowAdmission, ...]
    assessor_source: ObjectIdentity
    method_contract: ObjectIdentity
    disposition_counts: tuple[tuple[A, int], ...]
    reported_preliminary_disposition: A
    independent_sampling_contact: ObjectIdentity | None = None
    independent_sampling_disposition: A = A.NOT_ATTEMPTED
    independent_sampling_assessment: ObjectIdentity | None = None
    reason_codes: tuple[str, ...] = ("INDEPENDENT_SAMPLING_ASSESSMENT_NOT_ENTERED",)
    evidence_role: str = "EXPOSED_DEVELOPMENT_NONPROMOTABLE"
    fresh_physical_units: int = 0
    qualification: str = "NOT_PERFORMED"
    biological_target_disposition: A = A.UNEVALUABLE

    def __post_init__(self):
        validate_stable_id(self.report_id)
        for name in ("selection", "assessor_source", "method_contract"):
            identity(getattr(self, name), name)
        if self.method_contract != METHOD_CONTRACT:
            raise ValueError("admission changes current method contract")
        if (type(self.selected_windows) is not tuple or not self.selected_windows
                or type(self.windows) is not tuple or len(self.windows) != len(self.selected_windows)):
            raise ValueError("admission omits complete selected window denominator")
        for window in self.selected_windows:
            identity(window, "selected window")
        if tuple(row.object_id for row in self.selected_windows) != tuple(sorted({row.object_id for row in self.selected_windows})):
            raise ValueError("selected windows must be complete ordered unique identities")
        for row in self.windows:
            if type(row) is not WindowAdmission:
                raise ValueError("admission windows must be exact typed rows")
            row.__post_init__()
        if (tuple(row.window for row in self.windows) != self.selected_windows
                or any(row.selection != self.selection for row in self.windows)
                or len({row.legacy_trace.object_id for row in self.windows}) != len(self.windows)):
            raise ValueError("admission changes exact selected window/trace/selection joins")
        expected = tuple((state, sum(row.reported_disposition is state for row in self.windows)) for state in A)
        if (type(self.disposition_counts) is not tuple
                or any(type(state) is not A or type(total) is not int or total < 0 for state, total in self.disposition_counts)
                or self.disposition_counts != expected):
            raise ValueError("admission drops or changes six-state denominator counts")
        reduced = next(state for state in REPORTED_PRECEDENCE if any(row.reported_disposition is state for row in self.windows))
        if self.reported_preliminary_disposition is not reduced:
            raise ValueError("admission changes reported scalar disposition")
        if self.independent_sampling_contact is None:
            expected_independent = A.NOT_ATTEMPTED
            expected_reasons = ("INDEPENDENT_SAMPLING_ASSESSMENT_NOT_ENTERED",)
        else:
            identity(self.independent_sampling_contact, "reported independent sampling contact")
            expected_independent = A.UNEVALUABLE
            expected_reasons = ("INDEPENDENT_SAMPLING_CONTACT_WITHOUT_AUTHENTICATED_ASSESSMENT",)
        if (self.independent_sampling_disposition is not expected_independent
                or self.independent_sampling_assessment is not None or self.reason_codes != expected_reasons):
            raise ValueError("unbound independent assessment cannot confer sampling admission")
        if (self.evidence_role != "EXPOSED_DEVELOPMENT_NONPROMOTABLE"
                or type(self.fresh_physical_units) is not int or self.fresh_physical_units != 0
                or self.qualification != "NOT_PERFORMED" or self.biological_target_disposition is not A.UNEVALUABLE):
            raise ValueError("record admission cannot confer fresh physical units, PMF or biological qualification")
