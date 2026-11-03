# SPDX-License-Identifier: MPL-2.0
"""Compact, independently assessed observations with an explicit claim ceiling."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_observation_contracts as oc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_science as ss
from empirical_lawhood.adapters.methods.battery_refined_inquiry.segmented_fidelity_stream import FullStateStreamAssessment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.runtime.artifacts import ExternalRootContract
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion


def identity(record, name):
    return ObjectIdentity.from_record(getattr(record, name), record)


def combined_disposition(states, *, incomplete=False):
    """Only a complete all-SATISFIED denominator supports satisfaction."""
    if any(type(state) is not A for state in states):
        raise ValueError("observation reduction requires typed scientific dispositions")
    return A.FALSIFIED if A.FALSIFIED in states else A.UNEVALUABLE if (
        incomplete or not states or any(state is not A.SATISFIED for state in states)) else A.SATISFIED


@dataclass(frozen=True, slots=True)
class ObservedWindow(CanonicalRecord):
    """The actual completed native record and its authenticated measured costs."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-observation-inquiry/observed-window"
    window_id: str
    result: oc.PreparationObservationResult
    completion: NativeSubworkCompletion
    storage: ExternalRootContract

    def __post_init__(self):
        validate_stable_id(self.window_id)
        if (type(self.result) is not oc.PreparationObservationResult or type(self.completion) is not NativeSubworkCompletion
                or type(self.storage) is not ExternalRootContract):
            raise ValueError("observed window requires original typed result/completion/storage")
        self.result.__post_init__()
        self.completion.__post_init__()
        self.storage.__post_init__()
        ss.authenticate_payloads(self.result.evidence.native_receipt, (self.completion,))
        if (self.completion.definition != self.result.native_definition.identity
                or self.completion.operational_status is not self.result.evidence.native_receipt.operational_status
                or self.completion.peak_rss_bytes != self.result.evidence.trace.process_peak_rss_bytes
                or identity(self.storage, "storage_root_id") != self.result.entry_declaration.resources.declared_storage_root):
            raise ValueError("observed window changes original producing definition, costs or declared operational root")


@dataclass(frozen=True, slots=True)
class ObservationMethodAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-observation-inquiry/method-assessment"
    assessment_id: str
    observation: ObjectIdentity
    configured_method_index: int
    window: ObservedWindow
    preparation: oc.ObservationPreparationAssessment
    segments: tuple[ss.SegmentAssessment, ...]
    disposition: A
    reason_codes: tuple[str, ...]
    scope: str = "ACTUAL_PREPARATION_AND_COMPLETE_OBSERVED_WINDOW_CUSTODY;NUMERICAL_AND_FULL_FORECAST_QUALIFICATION_SEPARATE"
    full_forecast_completed: bool = False
    physical_qualification: bool = False

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if type(self.window) is not ObservedWindow or type(self.preparation) is not oc.ObservationPreparationAssessment:
            raise ValueError("method assessment substitutes original observed products")
        self.window.__post_init__()
        self.preparation.__post_init__()
        for row in self.segments:
            if type(row) is not ss.SegmentAssessment:
                raise ValueError("method assessment substitutes an actual call assessment")
            row.__post_init__()
        result = self.window.result
        if (self.observation != identity(result.observation, "observation_id")
                or type(self.configured_method_index) is not int or self.configured_method_index != result.configured_method_index
                or self.preparation.observation_result != identity(result, "result_id")
                or len(self.segments) != result.observed_native_calls
                or any(type(row) is not ss.SegmentAssessment or row.summary != identity(summary, "summary_id")
                       or row.native_receipt != summary.native_receipt
                       for row, summary in zip(self.segments, result.evidence.trace.segments, strict=True))):
            raise ValueError("method assessment omits/substitutes the actual complete call/preparation denominator")
        states = (self.preparation.disposition, *(row.disposition for row in self.segments))
        expected = combined_disposition(states, incomplete=result.disposition != "OBSERVATION_WINDOW_COMPLETED")
        reasons = {code for row in (self.preparation, *self.segments) for code in row.reason_codes}
        if result.disposition != "OBSERVATION_WINDOW_COMPLETED":
            reasons.add("declared-complete-observation-window-not-returned")
        if (self.disposition is not expected or self.reason_codes != tuple(sorted(reasons))
                or self.scope != "ACTUAL_PREPARATION_AND_COMPLETE_OBSERVED_WINDOW_CUSTODY;NUMERICAL_AND_FULL_FORECAST_QUALIFICATION_SEPARATE"
                or any(type(getattr(self, name)) is not bool or getattr(self, name)
                       for name in ("full_forecast_completed", "physical_qualification"))):
            raise ValueError("method assessment promotes an adverse or incomplete window to numerical/full success")


@dataclass(frozen=True, slots=True)
class ObservationReadout(CanonicalRecord):
    """Complete three-method/two-pair outcome and measured-cost denominator."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-observation-inquiry/readout"
    readout_id: str
    observation: oc.PreparationObservationProtocol
    methods: tuple[ObservationMethodAssessment, ...]
    pairs: tuple[FullStateStreamAssessment, ...]
    disposition: A
    reason_codes: tuple[str, ...]
    cost_scope: str = "THREE_ORIGINAL_NATIVE_COMPLETIONS_INCLUDE_NESTED_CALLS;DO_NOT_SUM_NESTED_COSTS;PURE_AND_ALL_TOTAL_COSTS_SEPARATE"
    resource_scope: str = "ACTUAL_SCOPED_PEAK_AND_RETAINED_BYTES_ONLY;NO_FULL_FORECAST_MEMORY_OR_STORAGE_BOUND"
    selected_model: str | None = None
    full_forecast_completed: bool = False
    physical_qualification: bool = False
    fresh_physical_units: int = 0
    scientific_authority: str = "NONE"

    def __post_init__(self):
        validate_stable_id(self.readout_id)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if type(self.observation) is not oc.PreparationObservationProtocol:
            raise ValueError("observation readout loses its prospective declaration")
        self.observation.__post_init__()
        if (len(self.methods) != 3 or any(type(row) is not ObservationMethodAssessment for row in self.methods)
                or tuple(row.configured_method_index for row in self.methods) != (0, 1, 2)
                or any(row.observation != identity(self.observation, "observation_id") for row in self.methods)
                or len(self.pairs) != 2 or any(type(row) is not FullStateStreamAssessment for row in self.pairs)):
            raise ValueError("observation readout thins its complete60/30/15 and60-30/30-15 denominators")
        for row in (*self.methods, *self.pairs):
            row.__post_init__()
        for pair, left, right in zip(self.pairs, self.methods[:-1], self.methods[1:], strict=True):
            if (pair.left_evidence != identity(left.window.result.evidence, "evidence_id")
                    or pair.right_evidence != identity(right.window.result.evidence, "evidence_id")):
                raise ValueError("observation readout substitutes actual compared operands")
        states = tuple(row.disposition for row in (*self.methods, *self.pairs))
        expected = combined_disposition(states)
        reasons = tuple(sorted({code for row in (*self.methods, *self.pairs) for code in row.reason_codes}))
        if (self.disposition is not expected or self.reason_codes != reasons
                or self.selected_model is not None or self.scientific_authority != "NONE"
                or self.cost_scope != "THREE_ORIGINAL_NATIVE_COMPLETIONS_INCLUDE_NESTED_CALLS;DO_NOT_SUM_NESTED_COSTS;PURE_AND_ALL_TOTAL_COSTS_SEPARATE"
                or self.resource_scope != "ACTUAL_SCOPED_PEAK_AND_RETAINED_BYTES_ONLY;NO_FULL_FORECAST_MEMORY_OR_STORAGE_BOUND"
                or any(type(getattr(self, name)) is not bool or getattr(self, name)
                       for name in ("full_forecast_completed", "physical_qualification"))
                or type(self.fresh_physical_units) is not int or self.fresh_physical_units != 0):
            raise ValueError("observation readout invents a selected supplier, favourable outcome or qualification")


def summarize(observation, methods, pairs):
    states = tuple(row.disposition for row in (*methods, *pairs))
    disposition = combined_disposition(states)
    reasons = tuple(sorted({code for row in (*methods, *pairs) for code in row.reason_codes}))
    return ObservationReadout("readout." + observation.observation_id, observation, methods, pairs, disposition, reasons)
