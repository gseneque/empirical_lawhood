# SPDX-License-Identifier: MPL-2.0
"""Compact actual-return carrier, including unavailable scientific operands.

Native full arrays travel on a separate authenticated segment stream. This
packet contains only the receiver trace, boundary operands and actual receipt;
known recovery loads original bytes rather than making another native call.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from . import preparation_contracts as pc
from . import segmented_contracts as sc
from . import segmented_science as ss


@dataclass(frozen=True, slots=True)
class SegmentedNativeEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/native-evidence"
    evidence_id: str
    trace: sc.SegmentedTrace
    protocol: pc.PreparationProtocol
    source_assignment: sc.ActualSourceAssignment | None
    layout: pc.ProcessedInitialStateLayout | None
    requested_initial: pc.StateObservation | None
    actual_initial: pc.StateObservation | None
    initial_derivative: pc.StateObservation | None
    actual_terminal: pc.StateObservation | None
    terminal_derivative: pc.StateObservation | None
    native_receipt: CanonicalTaskReceipt

    def __post_init__(self):
        validate_stable_id(self.evidence_id)
        expected = ((self.trace, sc.SegmentedTrace), (self.protocol, pc.PreparationProtocol),
            (self.native_receipt, CanonicalTaskReceipt))
        optional = ((self.source_assignment, sc.ActualSourceAssignment), (self.layout, pc.ProcessedInitialStateLayout),
            *((getattr(self, name), pc.StateObservation) for name in (
                "requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative")))
        if any(type(row) is not kind for row, kind in expected) or any(row is not None and type(row) is not kind for row, kind in optional):
            raise ValueError("native evidence substitutes its actual typed returned operands")
        records = (self.trace, self.protocol, *(row for row, _ in optional if row is not None))
        ss.authenticate_payloads(self.native_receipt, records)
        schemas = {kind.SCHEMA for _, kind in (*expected[:2], *optional)}
        actual = {(row.payload_schema, row.content_sha256) for row in self.native_receipt.output_logical_artifacts if row.payload_schema in schemas}
        if actual != {(record.SCHEMA, record.fingerprint()) for record in records}:
            raise ValueError("native evidence omits a materialized scientific output from its complete receipt census")
        config_id, protocol_id = ss.identity(self.trace.config, "config_id"), ss.identity(self.protocol, "protocol_id")
        if self.protocol.configuration != config_id:
            raise ValueError("native evidence changes the actual configuration/protocol join")
        if self.source_assignment is not None and (self.source_assignment.configuration != config_id or self.source_assignment.protocol != protocol_id):
            raise ValueError("native evidence changes its actual source assignment join")
        if self.layout is not None and self.layout.protocol != protocol_id:
            raise ValueError("native evidence changes its actual processed layout join")
        for name in ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"):
            state = getattr(self, name)
            if state is not None and (state.protocol != protocol_id or state.role != name.replace("_", "-")
                    or self.layout is not None and state.layout != ss.identity(self.layout, "layout_id")):
                raise ValueError("native evidence changes an actual boundary role/layout/protocol")


def evidence_from_result(config, result):
    """Accept only an actual result or independently reloaded original result."""
    if result.trace is None or result.trace.config != config:
        raise ValueError("known recovery requires original authenticated scientific outputs; no replay")
    receipt = result.inspection.receipt
    if receipt is None:
        raise ValueError("native evidence requires an actual completed receipt")
    return SegmentedNativeEvidence("evidence." + config.config_id, result.trace, result.protocol,
        result.source_assignment, result.layout, result.requested_initial, result.actual_initial,
        result.initial_derivative, result.actual_terminal, result.terminal_derivative, receipt)


def assess_preparation_evidence(config, evidence):
    """Recompute independent preparation or retain its exact missing census."""
    if type(evidence) is not SegmentedNativeEvidence or evidence.trace.config != config:
        raise ValueError("preparation assessment substitutes the exact actual evidence carrier")
    evidence.__post_init__()
    operands = (("source-assignment", evidence.source_assignment), ("layout", evidence.layout),
        ("requested-initial", evidence.requested_initial), ("actual-initial", evidence.actual_initial))
    missing = tuple(sorted(name for name, record in operands if record is None))
    if missing:
        return ss.UnavailableDerivedPreparationAssessment("assessment.unavailable." + config.config_id,
            ss.identity(config, "config_id"), ss.identity(evidence.protocol, "protocol_id"),
            ss.identity(config.preparation, "preparation_id"), ss.identity(config.preparation_assessment, "assessment_id"),
            ss.identity(evidence.native_receipt, "receipt_id"), missing,
            ("actual-complete-preparation-operands-unavailable",))
    return ss.assess_derived_preparation(config, evidence.protocol, evidence.source_assignment,
        evidence.layout, evidence.requested_initial, evidence.actual_initial)
