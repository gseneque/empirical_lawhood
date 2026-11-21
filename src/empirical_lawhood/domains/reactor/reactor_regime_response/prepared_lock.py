"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.nested_controller_evaluation import PreparedFutureRole
from empirical_lawhood.execution.controller_evaluation_nested import PreparedDesignBindingReceipt, PreparedForecastParentCommitment, PreparedInstanceBindingReceipt, PreparedParentReturn, PreparedProbeCommitment

@dataclass(frozen=True, slots=True)
class RegimeDPreparedRequestLock(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/reactor-regime-response/regime-d-prepared-request-lock'

    request_index: int
    prefix_id: str
    design: PreparedDesignBindingReceipt
    parent: PreparedForecastParentCommitment
    returned: PreparedParentReturn
    instance: PreparedInstanceBindingReceipt
    probes: tuple[PreparedProbeCommitment, PreparedProbeCommitment]

    def __post_init__(self) -> None:
        if (
            self.request_index not in range(4)
            or self.prefix_id != (
                f"{self.design.root_id}.request-{self.request_index}.prepared"
            )
            or self.design.policy_id != f"reactor-regime-request-{self.request_index}"
            or self.design.parent_commitment
            != ObjectIdentity.from_record(self.parent.commitment_id, self.parent)
            or self.returned.parent_commitment != self.design.parent_commitment
            or self.instance.design_binding
            != ObjectIdentity.from_record(self.design.binding_id, self.design)
            or tuple(probe.slot.ordinal for probe in self.probes) != (0, 1)
            or any(probe.slot.role is not PreparedFutureRole.AUDIT_PROBE for probe in self.probes)
        ):
            raise ValueError("D controller use lock changed its frozen request and two audit words")
