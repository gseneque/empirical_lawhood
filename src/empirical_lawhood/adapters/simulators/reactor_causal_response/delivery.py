"""Native acquisition, external-format translation and custody integration."""

from dataclasses import dataclass
from decimal import Decimal as D
from typing import Protocol
from empirical_lawhood.science.response.action_contracts import OccurrenceActionWord, ObservedActionOccurrence
from empirical_lawhood.science.response.control import ScientificCommitmentKind, OperationalDeliveryState
from empirical_lawhood.design.controller_study import ImplementationBinding, ImplementationRole
from empirical_lawhood.execution.controller_runtime import DeliveryPortResult
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import ReactorCommand, ReactorDelivery, ReactorFinalDelivery

from empirical_lawhood.domains.reactor.reactor_causal_response.delivery_words import (
    ReactorExposureWordMap as _science_ReactorExposureWordMap,
    exposure_word as _science_exposure_word,
)



class BatchDeliverySession(Protocol):
    def advance(self, command: ReactorCommand) -> ReactorDelivery | ReactorFinalDelivery: ...

@dataclass
class ReactorProfileDeliveryPort:
    implementation_binding: ImplementationBinding
    session: BatchDeliverySession
    mapping: _science_ReactorExposureWordMap
    last_delivery: ReactorDelivery | ReactorFinalDelivery | None = None

    def deliver(
        self, *, action_word: OccurrenceActionWord, commitment_kind: ScientificCommitmentKind
    ) -> DeliveryPortResult:
        if (
            self.implementation_binding.role is not ImplementationRole.DELIVERY
            or commitment_kind is not ScientificCommitmentKind.ACTION
            or action_word != self.mapping.word
        ):
            raise ValueError("native delivery requires the exact committed profile and ACTION")
        try:
            raw = self.session.advance(self.mapping.command)
        except RuntimeError as error:
            if str(error) not in {
                "reactor delivery timed out; no completion evidence",
                "native reactor failed; no completion evidence",
            }:
                raise
            return DeliveryPortResult(
                f"delivery.{self.mapping.command.decision_id}",
                (),
                OperationalDeliveryState.TERMINATED,
            )
        self.last_delivery = raw
        if raw.command != self.mapping.command:
            raise ValueError("native session substituted command")
        if isinstance(raw, ReactorFinalDelivery) != (raw.command.time_s == D(28790)):
            raise ValueError("last native interval requires terminal delivery without a callback")
        actual = _science_exposure_word(
            raw.command,
            (raw.accepted_feed_kg_s, raw.accepted_jacket_k),
            (raw.applied_feed_kg_s, raw.applied_jacket_k),
            tuple((e.time_s, e.duration_s, e.feed_kg_s, e.jacket_k) for e in raw.exposures),
            history_id=action_word.retained_history_id,
            horizon_id=action_word.horizon_id,
        )
        observed = tuple(
            ObservedActionOccurrence(
                f"observed.{o.occurrence_id}",
                o.occurrence_id,
                o.requested,
                o.accepted,
                o.applied,
                o.realized,
                (),
            )
            for o in actual.occurrences
        )
        return DeliveryPortResult(
            f"delivery.{raw.command.decision_id}",
            observed,
            None if actual == action_word else OperationalDeliveryState.TERMINATED,
        )
