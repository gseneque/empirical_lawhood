"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from dataclasses import dataclass
from collections.abc import Iterator
from typing import ClassVar, Any
from empirical_lawhood.methods.control.prepared_forecast import PreparedForecastLock
from empirical_lawhood.methods.receiver_conditioned_io.finite_action_mpc import FiniteMPCProposal
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.words import PulseProjection
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.finite_response_geometry import FiniteResponseSet, FiniteTaskFunctionalSpec
from empirical_lawhood.storage.contracts.canonical_record_archive import CanonicalRecordArchive
from empirical_lawhood.execution.controller_compiler import CompiledDeliveryControllerStudy
from empirical_lawhood.execution.controller_runtime import DeliveryControllerDecisionCommitment
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.selection import FrontierUseRequest

class UndeliverableSession:
    def advance(self, command: Any) -> Any:
        raise AssertionError("causal controller preparation attempted native delivery")

@dataclass(frozen=True, slots=True)
class FrontierFrozenUse(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/reactor-finite-control-frontier/frontier-frozen-use'
    request: FrontierUseRequest
    projection: PulseProjection | None
    compiled: CompiledDeliveryControllerStudy | None
    commitment: DeliveryControllerDecisionCommitment | None
    task: FiniteTaskFunctionalSpec | None
    forecasts: tuple[FiniteResponseSet, ...]
    proposal: FiniteMPCProposal | None
    lock: PreparedForecastLock | None
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.projection is None:
            if (
                any(v is not None for v in (self.compiled, self.commitment, self.task, self.lock))
                or self.forecasts
                or not self.reasons
            ):
                raise ValueError("nonattempt invented an owner commitment")
        elif (
            any(
                v is None
                for v in (self.compiled, self.commitment, self.task, self.proposal, self.lock)
            )
            or len(self.forecasts) != 1
            or self.reasons
            or self.commitment is None
            or self.commitment.action_binding is None
            or self.commitment.action_binding.action_word != self.projection.word
        ):
            raise ValueError("frozen use lost its exact chosen word or prepared-owner lock")

@dataclass(frozen=True, slots=True)
class FrontierFrozenRoot(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/reactor-finite-control-frontier/frontier-frozen-root'
    root: str
    preparation: ObjectIdentity
    prediction_seal: ObjectIdentity
    plan: ObjectIdentity
    use_archives: tuple[CanonicalRecordArchive, ...]

    def __post_init__(self) -> None:
        if len(self.use_archives) > 24 or any(
            a.subject.object_schema != FrontierFrozenUse.SCHEMA
            or not a.subject.object_id.startswith(f"{self.root}.")
            for a in self.use_archives
        ):
            raise ValueError("frozen request archive changed its root or owner schema")

    @property
    def uses(self) -> Iterator[FrontierFrozenUse]:
        """Authenticate and decode one unchanged owner record at a time."""
        for archive in self.use_archives:
            use = decode_canonical_bytes(
                archive.unpack(), FrontierFrozenUse, maximum_bytes=archive.decoded_bytes
            )
            if archive.subject.object_id != f"{self.root}.{use.request.request_id}.frozen-use":
                raise ValueError("frozen request archive substituted its exact request")
            yield use

    @property
    def record_id(self) -> str:
        return f"{self.root}.frontier-frozen-root"
