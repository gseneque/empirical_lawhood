"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.methods.control.prepared_forecast import PreparedForecastLock
from empirical_lawhood.methods.receiver_conditioned_io.finite_action_mpc import FiniteMPCProposal
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.native_words import PulseProjection
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.finite_response_geometry import FiniteResponseSet, FiniteTaskFunctionalSpec
from empirical_lawhood.storage.contracts.canonical_record_archive import CanonicalRecordArchive
from empirical_lawhood.execution.controller_compiler import CompiledDeliveryControllerStudy
from empirical_lawhood.execution.controller_evaluation_trajectory import TrajectoryCallbackLink
from empirical_lawhood.execution.controller_runtime import CommitmentDisposition, DeliveryControllerDecisionCommitment
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.config import Request
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.prediction import ClassicalPredictedBound
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.records import ClassicalContext

@dataclass(frozen=True, slots=True)
class ClassicalFrozenStage(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/reactor-staged-pulse-response/classical-frozen-stage'
    policy: str
    request: Request
    stage_kind: str
    causal: ClassicalContext
    predicted: ClassicalPredictedBound | None
    projection: PulseProjection | None
    compiled: CompiledDeliveryControllerStudy | None
    commitment: DeliveryControllerDecisionCommitment | None
    task: FiniteTaskFunctionalSpec | None
    forecasts: tuple[FiniteResponseSet, ...]
    proposal: FiniteMPCProposal | None
    lock: PreparedForecastLock | None
    link: TrajectoryCallbackLink | None
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        complete = (
            self.predicted,
            self.projection,
            self.compiled,
            self.commitment,
            self.task,
            self.proposal,
            self.lock,
            self.link,
        )
        if self.compiled is None:
            if any(v is not None for v in complete) or self.forecasts or not self.reasons:
                raise ValueError("nonentry stage invents an owner or native commitment")
        elif any(v is None for v in complete) or len(self.forecasts) != 1:
            raise ValueError("frozen stage omits its exact selected law or prepared owner")
        if self.admitted and (
            self.reasons
            or self.commitment is None
            or self.commitment.action_binding is None
            or self.projection is None
            or self.commitment.action_binding.action_word != self.projection.word
        ):
            raise ValueError("admitted frozen stage changes the owner-selected native word")

    @property
    def record_id(self) -> str:
        return f"{self.causal.root}.{self.policy.lower()}.{self.request.request_id.lower()}.{self.stage_kind}.frozen"

    @property
    def admitted(self) -> bool:
        return (
            self.commitment is not None
            and self.commitment.disposition is not CommitmentDisposition.NONATTEMPT
        )

@dataclass(frozen=True, slots=True)
class ClassicalFrozenRoot(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/reactor-staged-pulse-response/classical-frozen-root'
    root: str
    preparation: ObjectIdentity
    seal: ObjectIdentity
    plan: ObjectIdentity
    stages: tuple[CanonicalRecordArchive, ...]

    @property
    def record_id(self) -> str:
        return f"{self.root}.frozen-controller-inputs"

    def unpack(self) -> tuple[ClassicalFrozenStage, ...]:
        result = tuple(
            decode_canonical_bytes(
                a.unpack(), ClassicalFrozenStage, maximum_bytes=a.decoded_bytes
            )
            for a in self.stages
        )
        if any(
            a.subject != ObjectIdentity.from_record(s.record_id, s)
            or s.causal.root != self.root
            or s.stage_kind == "joint"
            for a, s in zip(self.stages, result, strict=True)
        ):
            raise ValueError(
                "pre-t0 archive substitutes its initial request or invents a second decision"
            )
        return result
