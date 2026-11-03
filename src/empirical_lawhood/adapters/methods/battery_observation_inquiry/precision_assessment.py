# SPDX-License-Identifier: MPL-2.0
"""PURE reassessment of explicitly controlled, completed original observations.

The selected native tolerances and unchanged comparison budgets are different
operands. Original producing records and original adverse ordinary assessments
remain immutable. This owner changes only the expected native request tolerance
join; all other original request, array, custody and comparison guards remain.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
import json
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_science as science
from . import contracts as ct
from . import precision_control as policy

D = Decimal
SCOPE = "COMPLETED_ORIGINALS_PURE_REASSESSMENT;EXPLICIT_NATIVE_PRECISION_JOIN;UNCHANGED_COMPARISON_GATES;NO_REPLAY_OR_FRESH_QUALIFICATION"


class _ExpectedNativeTolerance:
    """Transient expected request view; never a substituted scientific record."""
    def __init__(self, original, control):
        self.original, self.rtol, self.atol = original, control.selected_rtol, control.selected_atol

    def __getattr__(self, name):
        return getattr(self.original, name)


def _policy_request_reasons(original_guard, control, assignment, config, layout, summary, request, full_state, previous_terminal):
    """Authenticate exact selected options before the unchanged original guard."""
    if type(control) is not policy.PrecisionControl or type(assignment) is not policy.ActualPrecisionAssignment:
        raise ValueError("precision reassessment omits its exact typed selected policy/assignment")
    control.__post_init__()
    assignment.__post_init__()
    configuration = ct.identity(config, "config_id")
    if (assignment.control != control or assignment.native_configuration != configuration
            or request.configuration != configuration
            or json.loads(request.primitive_json).get("solver") != json.loads(assignment.actual_solver_json)):
        raise ValueError("precision reassessment substitutes policy, configuration or actual complete solver options")
    # Only this guard reads the actual expected request tolerances. Comparison
    # consumers continue to receive the original config and its original weights.
    return original_guard(_ExpectedNativeTolerance(config, control), layout, summary, request, full_state, previous_terminal)


def _require_original(original):
    if type(original) is not policy.PrecisionReadout:
        raise ValueError("precision reassessment requires the complete original ordinary readout")
    original.__post_init__()
    methods = original.original_readout.methods
    if (len(methods) != 3 or tuple(method.configured_method_index for method in methods) != (0, 1, 2)
            or len({assignment.native_configuration for assignment in original.actual_assignments}) != 3):
        raise ValueError("precision reassessment changes the original complete configuration denominator")
    for method, assignment, operator in zip(methods, original.actual_assignments, original.actual_operators, strict=True):
        config = method.window.result.evidence.trace.config
        if (config.numerical_view.rtol, config.numerical_view.atol) != (D("1e-7"), D("1e-8")):
            raise ValueError("precision reassessment changes original comparison weights")
        policy.require_assignment(original.control, assignment, method.window)
        policy.require_operator(operator, assignment, method.window)
    return {row.native_configuration: row for row in original.actual_assignments}


@contextmanager
def precision_consumer_scope(original):
    """Use exact completed policy/assignment/operator evidence; never enter native."""
    stock = _require_original(original)
    original_guard = science._request_reasons

    def guard(config, layout, summary, request, full_state, previous_terminal):
        assignment = stock.get(ct.identity(config, "config_id"))
        if assignment is None:
            raise ValueError("precision reassessment lacks the actual selected configuration assignment")
        return _policy_request_reasons(original_guard, original.control, assignment, config, layout, summary,
            request, full_state, previous_terminal)

    with policy.request_control_scope(original.actual_assignments):
        science._request_reasons = guard
        try:
            yield
        finally:
            science._request_reasons = original_guard


@dataclass(frozen=True, slots=True)
class PrecisionReassessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-observation-inquiry/completed-precision-reassessment"
    assessment_id: str
    original_ordinary_readout: ObjectIdentity
    consumer_source_sha256: str
    reassessed_readout: policy.PrecisionReadout
    unchanged_comparison_rtol: Decimal = D("1e-7")
    unchanged_comparison_atol: Decimal = D("1e-8")
    scope: str = SCOPE
    native_entries: int = 0
    producer_reexecutions: int = 0
    fresh_physical_units: int = 0
    physical_qualification: bool = False
    whole_time_certified: bool = False

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        validate_sha256(self.consumer_source_sha256)
        if (type(self.original_ordinary_readout) is not ObjectIdentity
                or self.original_ordinary_readout.object_schema != policy.PrecisionReadout.SCHEMA
                or type(self.reassessed_readout) is not policy.PrecisionReadout
                or (self.unchanged_comparison_rtol, self.unchanged_comparison_atol) != (D("1e-7"), D("1e-8"))
                or self.scope != SCOPE
                or any(type(getattr(self, name)) is not int or getattr(self, name) != 0
                    for name in ("native_entries", "producer_reexecutions", "fresh_physical_units"))
                or any(type(getattr(self, name)) is not bool or getattr(self, name)
                    for name in ("physical_qualification", "whole_time_certified"))):
            raise ValueError("precision reassessment loses original identity, unchanged gates or retained-evidence scope")
        _require_original(self.reassessed_readout)


def complete_reassessment(original, reassessed, consumer_source_sha256):
    """Bind the original adverse ordinary product to this distinct PURE result."""
    _require_original(original)
    if type(reassessed) is not ct.ObservationReadout:
        raise ValueError("precision reassessment requires complete typed scientific outcomes")
    reassessed.__post_init__()
    if (reassessed.observation != original.original_readout.observation
            or tuple(method.window for method in reassessed.methods) != tuple(method.window for method in original.original_readout.methods)
            or tuple(pair.control for pair in reassessed.pairs) != tuple(pair.control for pair in original.original_readout.pairs)):
        raise ValueError("precision reassessment substitutes original windows or comparison protocol")
    controlled = policy.PrecisionReadout("reassessment." + original.control.control_id, original.control,
        reassessed, original.actual_assignments, original.actual_operators)
    return PrecisionReassessment("assessment." + controlled.readout_id,
        ct.identity(original, "readout_id"), consumer_source_sha256, controlled)
