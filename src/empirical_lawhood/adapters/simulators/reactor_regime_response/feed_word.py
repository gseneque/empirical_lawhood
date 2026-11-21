"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal as D
from empirical_lawhood.adapters.simulators.reactor_causal_response.delivery import BatchDeliverySession
from empirical_lawhood.domains.reactor.reactor_causal_response.delivery_words import ReactorExposureWordMap, exposure_word
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import ReactorDelivery, ReactorFinalDelivery
from empirical_lawhood.science.response.action_contracts import OccurrenceActionWord, ObservedActionOccurrence
from empirical_lawhood.science.response.control import OperationalDeliveryState, ScientificCommitmentKind
from empirical_lawhood.domains.reactor.reactor_regime_response.science import HORIZON
from empirical_lawhood.design.controller_study import ImplementationBinding, ImplementationRole
from empirical_lawhood.execution.controller_runtime import DeliveryPortResult

from empirical_lawhood.domains.reactor.reactor_regime_response.feed_word import (
    ReactorFeedOnlyWordMap as _science_ReactorFeedOnlyWordMap,
    scalar_feed_word as _science_scalar_feed_word,
)

@dataclass
class ReactorScalarFeedDeliveryPort:
    """Installed owner's delivery port for one committed scalar feed word."""

    implementation_binding: ImplementationBinding
    session: BatchDeliverySession
    mapping: _science_ReactorFeedOnlyWordMap
    last_delivery: ReactorDelivery | ReactorFinalDelivery | None = None

    def deliver(
        self, *, action_word: OccurrenceActionWord, commitment_kind: ScientificCommitmentKind
    ) -> DeliveryPortResult:
        if (
            self.implementation_binding.role is not ImplementationRole.DELIVERY
            or action_word != self.mapping.scalar_word
            or commitment_kind not in (
                ScientificCommitmentKind.ACTION,
                ScientificCommitmentKind.MEASURED_HOLD,
            )
            or (
                commitment_kind is ScientificCommitmentKind.ACTION
                and self.mapping.full_native.command.feed_kg_s == 0
            )
            or (
                commitment_kind is ScientificCommitmentKind.MEASURED_HOLD
                and self.mapping.full_native.command.feed_kg_s != 0
            )
        ):
            raise ValueError("scalar owner delivery changed its committed native feed word")
        command = self.mapping.full_native.command
        try:
            raw = self.session.advance(command)
        except RuntimeError as error:
            if str(error) not in {
                "reactor delivery timed out; no completion evidence",
                "native reactor failed; no completion evidence",
            }:
                raise
            return DeliveryPortResult(
                f"delivery.{command.decision_id}", (), OperationalDeliveryState.TERMINATED
            )
        self.last_delivery = raw
        if raw.command != command:
            raise ValueError("native source substituted the committed full command")
        if isinstance(raw, ReactorFinalDelivery) != (command.time_s == D(28790)):
            raise ValueError("terminal native interval changed its delivery shape")
        actual_exposure = tuple(
            (e.time_s, e.duration_s, e.feed_kg_s, e.jacket_k) for e in raw.exposures
        )
        actual_full = ReactorExposureWordMap(
            raw.command,
            (raw.accepted_feed_kg_s, raw.accepted_jacket_k),
            (raw.applied_feed_kg_s, raw.applied_jacket_k),
            actual_exposure,
            exposure_word(
                raw.command,
                (raw.accepted_feed_kg_s, raw.accepted_jacket_k),
                (raw.applied_feed_kg_s, raw.applied_jacket_k),
                actual_exposure,
                history_id=action_word.retained_history_id,
                horizon_id=HORIZON,
            ),
        )
        observed_word = _science_scalar_feed_word(actual_full)
        if (
            raw.accepted_jacket_k != self.mapping.fixed_jacket_K
            or raw.applied_jacket_k != self.mapping.fixed_jacket_K
            or any(e.jacket_k != self.mapping.fixed_jacket_K for e in raw.exposures)
        ):
            raise ValueError("actual native jacket changed its fixed denominator")
        observed = tuple(
            ObservedActionOccurrence(
                f"observed.{occurrence.occurrence_id}",
                occurrence.occurrence_id,
                occurrence.requested,
                occurrence.accepted,
                occurrence.applied,
                occurrence.realized,
                (),
            )
            for occurrence in observed_word.occurrences
        )
        return DeliveryPortResult(
            f"delivery.{command.decision_id}",
            observed,
            None if observed_word == action_word else OperationalDeliveryState.TERMINATED,
        )
