# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.reactor.reactor_matched_replay_forecast.provider import ForecastChainProvider


# Scientific registration and configuration.

from empirical_lawhood.domains.reactor.reactor_matched_replay_forecast.transport import ReactorTraceEnvelope
from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.domains.reactor.reactor_matched_replay_forecast.science import ReactorForecastDesign
from empirical_lawhood.domains.reactor.reactor_matched_replay_forecast.records import ReactorForecastResult


INPUT_TYPES = (
    ReactorForecastDesign,
    ReactorTraceEnvelope,
    ReactorForecastResult,
)
OUTPUT_TYPES = (
    ReactorForecastResult,
    ScientificAdjudicationRecord,
)
CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="reactor-matched-replay-forecast.forecast-qualification",
    kind=CapabilityKind.EVALUATOR,
    maximum_outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
    permissions=tuple(
        sorted(
            (
                CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
                CapabilityPermission.READ_SEALED_OUTCOMES,
                CapabilityPermission.REVEAL_OUTCOMES,
            ),
            key=lambda p: p.value,
        )
    ),
    config_schema=ReactorForecastDesign.SCHEMA,
    config_schema_sha256=sha256(ReactorForecastDesign.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(sorted(t.SCHEMA for t in INPUT_TYPES)),
    output_schema_ids=tuple(sorted(t.SCHEMA for t in OUTPUT_TYPES)),
    implementation_sha256=sha256(
        b"reactor-matched-replay-forecast:matched-input-absolute-profile-and-separate-recovery-operands"
    ).hexdigest(),
    runtime_id="cpython-3.11-reactor-matched-replay-forecast",
    resource_ceiling=ResourceBudget(1, 4 * 1024**3, 0, 1800, 8 * 1024**3, 16 * 1024**2),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "forecast-qualification",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (ReactorForecastDesign,),
    None,
    namespace="reactor-matched-replay-forecast",
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast

from empirical_lawhood.methods.law_assessment import CandidatePayloadPublisher, CandidatePayloadReader
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.domains.reactor.reactor_matched_replay_forecast.science import ReactorForecastDesign



BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (ReactorForecastDesign,)),
    required_platform_port_keys=(
        "candidate-payload-publisher",
        "candidate-payload-reader",
        "dependency-custody-reader",
    ),
)


@dataclass(frozen=True, slots=True)
class ForecastChainFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> ForecastChainProvider:
        from empirical_lawhood.domains.reactor.reactor_matched_replay_forecast.provider import ForecastChainProvider, DependencyCustodyReader
        if len(records) != 1 or not isinstance(records[0], ReactorForecastDesign):
            raise ValueError("finite chain factory requires its exact pre-acquisition design")
        ports = {p.port_key: p.port for p in platform_ports}
        if (
            len(platform_ports) != 3
            or tuple(sorted(ports)) != self.binding.required_platform_port_keys
        ):
            raise ValueError("finite chain factory requires exact payload and custody ports")
        if (
            not callable(
                getattr(ports["candidate-payload-publisher"], "publish_candidate_payload", None)
            )
            or not callable(
                getattr(ports["candidate-payload-reader"], "read_candidate_payload", None)
            )
            or not callable(getattr(ports["dependency-custody-reader"], "read_dependency", None))
        ):
            raise TypeError("finite chain payload ports do not satisfy their protocols")
        return ForecastChainProvider(
            registry,
            records[0],
            cast(CandidatePayloadPublisher, ports["candidate-payload-publisher"]),
            cast(CandidatePayloadReader, ports["candidate-payload-reader"]),
            cast(DependencyCustodyReader, ports["dependency-custody-reader"]),
        )


_EXECUTABLE_ID = "executable-contribution.reactor-matched-replay-forecast.forecast-qualification"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (ForecastChainFactory(),)
_ISSUED_RECORD_TYPES = (ReactorForecastDesign,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION', 'OUTPUT_TYPES']
