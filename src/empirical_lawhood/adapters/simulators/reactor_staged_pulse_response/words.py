"""Native acquisition, external-format translation and custody integration."""

from dataclasses import dataclass, field
from empirical_lawhood.adapters.simulators.reactor_causal_response.delivery import BatchDeliverySession
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import ReactorDelivery
from empirical_lawhood.adapters.simulators.reactor_prefix_response.finite_delivery import deliver_feed_word
from empirical_lawhood.science.response.action_contracts import OccurrenceActionWord
from empirical_lawhood.science.response.control import ScientificCommitmentKind
from empirical_lawhood.design.controller_study import ImplementationBinding, ImplementationRole
from empirical_lawhood.execution.controller_runtime import DeliveryPortResult

from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.native_words import (
    PulseProjection as _science_PulseProjection,
)




@dataclass
class ClassicalPulseDeliveryPort:
    implementation_binding: ImplementationBinding
    session: BatchDeliverySession
    mapping: _science_PulseProjection
    last_deliveries: list[ReactorDelivery] = field(default_factory=list)
    consumed: bool = False

    def deliver(
        self, *, action_word: OccurrenceActionWord, commitment_kind: ScientificCommitmentKind
    ) -> DeliveryPortResult:
        if (
            self.consumed
            or self.implementation_binding.role is not ImplementationRole.DELIVERY
            or commitment_kind is not ScientificCommitmentKind.ACTION
            or action_word != self.mapping.word
            or self.mapping.pulse.rate_kg_s <= 0
        ):
            raise ValueError("finite delivery requires one exact unconsumed ACTION commitment")
        self.consumed = True
        return deliver_feed_word(
            self.session, action_word, self.mapping.mappings, self.last_deliveries
        )
