# SPDX-License-Identifier: MPL-2.0
"""Explicit fixed-budget full-state consumers for the prospective native policy.

The existing numerical algorithms and every native custody guard are reused.
Legacy protocol strings and historical products stay unchanged. Internal legacy
record projections validate counts/custody only and are never published; the
new scientific products state their actual independent comparison budget.
Event/regime/suffix uncertainty remains an outcome, not a favourable subset.
"""

from contextlib import contextmanager
from dataclasses import dataclass, fields
from hashlib import sha256
from pathlib import Path
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from . import forecast_step_control as step
from . import segmented_fidelity as local, segmented_fidelity_stream as paired


@dataclass(frozen=True, slots=True)
class ForecastStateControl(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/forecast-state-control"
    control_id: str
    native_policy: step.ForecastStepPolicy
    interval_algorithm_source_sha256: str
    stream_algorithm_source_sha256: str
    comparison_weights: str = "SEPARATELY_DECLARED_FIXED_COMPARISON_ATOL_PLUS_RTOL_TIMES_MAXIMUM_ABSOLUTE_SCALED_COMPONENT"
    derivative_weights: str = "FIXED_COMPARISON_ATOL_OVER_ONE_SECOND_PLUS_RTOL_TIMES_MAXIMUM_ABSOLUTE_RETURNED_DERIVATIVE"
    scope: str = "COMPLETE_ORIGINAL_STREAM_NUMERICAL_CONTROL;EVENT_SUFFIX_RECEIVER_AND_ADMISSION_SEPARATE"

    def __post_init__(self):
        validate_stable_id(self.control_id)
        validate_sha256(self.interval_algorithm_source_sha256)
        validate_sha256(self.stream_algorithm_source_sha256)
        if (type(self.native_policy) is not step.ForecastStepPolicy
                or self.comparison_weights != "SEPARATELY_DECLARED_FIXED_COMPARISON_ATOL_PLUS_RTOL_TIMES_MAXIMUM_ABSOLUTE_SCALED_COMPONENT"
                or self.derivative_weights != "FIXED_COMPARISON_ATOL_OVER_ONE_SECOND_PLUS_RTOL_TIMES_MAXIMUM_ABSOLUTE_RETURNED_DERIVATIVE"
                or self.scope != "COMPLETE_ORIGINAL_STREAM_NUMERICAL_CONTROL;EVENT_SUFFIX_RECEIVER_AND_ADMISSION_SEPARATE"):
            raise ValueError("forecast state control loses actual native policy or explicit fixed scientific comparison weights")
        self.native_policy.__post_init__()

    @property
    def identity(self):
        return step.identity(self, "control_id")

    @property
    def algorithm_control(self):
        # Private parameter carrier for the unchanged arithmetic/cursor code.
        # Its legacy native-weight wording is not a scientific output claim.
        return local.FullStateControlProtocol("algorithm.internal." + self.control_id)


def require_algorithm_sources(control):
    if type(control) is not ForecastStateControl:
        raise ValueError("forecast state comparison needs its actual typed fixed-budget control")
    control.__post_init__()
    for module, expected in ((local, control.interval_algorithm_source_sha256), (paired, control.stream_algorithm_source_sha256)):
        if sha256(Path(module.__file__).read_bytes()).hexdigest() != expected:
            raise ValueError("forecast state comparison changed its authenticated scientific algorithm source")


def _interval_projection(record, algorithm_control):
    """Unpublished count/custody validation through the original exact contract."""
    values = {field.name: getattr(record, field.name) for field in fields(local.FullStateIntervalAssessment)}
    values["control"] = step.identity(algorithm_control, "control_id")
    return local.FullStateIntervalAssessment(**values)


@dataclass(frozen=True, slots=True, kw_only=True)
class ForecastStateInterval(local.FullStateIntervalAssessment):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/fixed-budget-state-interval"
    scientific_control: ForecastStateControl

    def __post_init__(self):
        self.scientific_control.__post_init__()
        if type(self.scientific_control) is not ForecastStateControl or self.control != self.scientific_control.identity:
            raise ValueError("fixed-budget interval substitutes its explicitly committed scientific control")
        _interval_projection(self, self.scientific_control.algorithm_control)


def _stream_projection(record):
    control = record.scientific_control.algorithm_control
    values = {field.name: getattr(record, field.name) for field in fields(paired.FullStateStreamAssessment)}
    values["control"] = step.identity(control, "control_id")
    values["intervals"] = tuple(_interval_projection(row, control) for row in record.intervals)
    return paired.FullStateStreamAssessment(**values)


@dataclass(frozen=True, slots=True, kw_only=True)
class ForecastStateStream(paired.FullStateStreamAssessment):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/fixed-budget-state-stream"
    intervals: tuple[ForecastStateInterval, ...]
    scientific_control: ForecastStateControl
    actual_assignment_evidence: tuple[ObjectIdentity, ObjectIdentity]

    def __post_init__(self):
        self.scientific_control.__post_init__()
        if (type(self.scientific_control) is not ForecastStateControl or self.control != self.scientific_control.identity
                or type(self.actual_assignment_evidence) is not tuple or len(self.actual_assignment_evidence) != 2
                or any(type(row) is not ObjectIdentity or row.object_schema != step.ForecastStepEvidence.SCHEMA
                       for row in self.actual_assignment_evidence)
                or any(type(row) is not ForecastStateInterval or row.scientific_control != self.scientific_control for row in self.intervals)):
            raise ValueError("fixed-budget stream omits actual assignments or complete scientific interval controls")
        _stream_projection(self)


@contextmanager
def _fixed_arithmetic(control, native_config):
    """Replace only the independently declared weights for this arithmetic call."""
    original = local._residual
    budget = control.native_policy.comparison_budget

    def residual(left, right, atol, rtol):
        if atol != native_config.atol or rtol != native_config.rtol:
            raise ValueError("forecast interval requested undeclared native weights or derivative time scale")
        return original(left, right, budget.atol, budget.rtol)

    local._residual = residual
    try:
        yield
    finally:
        local._residual = original


def assess_interval(control, left, right, *, start_s=None, end_s=None):
    """Complete native/query-grid algorithm with the explicit fixed budget."""
    require_algorithm_sources(control)
    for operand in (left, right):
        if operand.configuration.native.policy != control.native_policy.selected_numerical_policy:
            raise ValueError("forecast interval changes selected native policy")
    with _fixed_arithmetic(control, left.configuration):
        original = local.assess_interval(control.algorithm_control, left, right, start_s=start_s, end_s=end_s)
    values = {field.name: getattr(original, field.name) for field in fields(local.FullStateIntervalAssessment)}
    values["control"] = control.identity
    values["assessment_id"] = "assessment.fixed-budget." + original.assessment_id
    return ForecastStateInterval(**values, scientific_control=control)


def require_forecast_assignment(control, selected, metadata, evidence):
    if type(metadata) is not step.ForecastStepEvidence:
        raise ValueError("forecast state consumer omits actual completed assignment evidence")
    metadata.__post_init__()
    if (metadata.control != control.native_policy or metadata.original_native_receipt != evidence.native_receipt
            or metadata.original_native_definition.configuration != step.identity(evidence.trace.config, "config_id")):
        raise ValueError("forecast state assignment differs from its actual native evidence/receipt")
    if metadata.assignment is None:
        if evidence.trace.disposition != "TECHNICAL_FAILURE" or evidence.trace.segments or evidence.trace.backend_solve_calls:
            raise ValueError("absent forecast assignment cannot support completed native calls or successful trace")
        step.require_config(control.native_policy, selected, evidence.trace.config)
        return
    step.require_assignment(control.native_policy, selected, metadata.assignment, evidence.trace.config,
        metadata.original_native_definition, metadata.original_native_receipt)


def assess_streams(control, selected, left, right, assignment_evidence):
    """Consume every original call and keep all adverse/uncertain event/suffix data."""
    require_algorithm_sources(control)
    if type(assignment_evidence) is not tuple or len(assignment_evidence) != 2:
        raise ValueError("forecast stream requires both complete actual assignment operands")
    for metadata, operand in zip(assignment_evidence, (left, right), strict=True):
        require_forecast_assignment(control, selected, metadata, operand.evidence)
    original_interval = local.assess_interval
    algorithm = control.algorithm_control

    def interval(legacy_control, a, b, **kwargs):
        if legacy_control != algorithm:
            raise ValueError("forecast stream substitutes its scientific arithmetic control")
        with _fixed_arithmetic(control, a.configuration):
            return original_interval(legacy_control, a, b, **kwargs)

    local.assess_interval = interval
    try:
        present = tuple(row.assignment for row in assignment_evidence if row.assignment is not None)
        if present:
            with step.request_step_scope(present):
                original = paired.assess_streams(algorithm, left, right)
        else:
            # Both exact failed traces have zero native calls. The unchanged
            # complete cursor returns UE; no assignment or request is invented.
            original = paired.assess_streams(algorithm, left, right)
    finally:
        local.assess_interval = original_interval
    intervals = []
    for row in original.intervals:
        values = {field.name: getattr(row, field.name) for field in fields(local.FullStateIntervalAssessment)}
        values.update(control=control.identity, assessment_id="assessment.fixed-budget." + row.assessment_id)
        intervals.append(ForecastStateInterval(**values, scientific_control=control))
    values = {field.name: getattr(original, field.name) for field in fields(paired.FullStateStreamAssessment)}
    values.update(control=control.identity, assessment_id="assessment.fixed-budget." + original.assessment_id, intervals=tuple(intervals))
    return ForecastStateStream(**values, scientific_control=control,
        actual_assignment_evidence=tuple(step.identity(row, "evidence_id") for row in assignment_evidence))
