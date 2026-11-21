# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.adapters.simulators.reactor_matched_replay_forecast.provider import ReactorBatchProvider


# Scientific registration and configuration.

from empirical_lawhood.domains.reactor.reactor_matched_replay_forecast.transport import ReactorTraceEnvelope

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.domains.reactor.reactor_matched_replay_forecast.design import ReactorBatchConfig, ReactorBatchSource
from empirical_lawhood.domains.reactor.reactor_matched_replay_forecast.trace import MAXIMUM_BATCH_BYTES


CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="reactor-matched-replay-forecast.reactor-batch",
    kind=CapabilityKind.SIMULATOR,
    maximum_outcome_access=OutcomeAccess.EVALUATION_SEALED,
    config_schema=ReactorBatchConfig.SCHEMA,
    config_schema_sha256=sha256(ReactorBatchConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(sorted((ReactorBatchConfig.SCHEMA, ReactorBatchSource.SCHEMA))),
    output_schema_ids=(ReactorTraceEnvelope.SCHEMA,),
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    resource_ceiling=ResourceBudget(1, 4 * 1024**3, 0, 1200, 1024**2, MAXIMUM_BATCH_BYTES),
    implementation_sha256=sha256(
        b"reactor-matched-replay-forecast-programme:matched-input-policy-robustness-and-prescribed-recovery"
    ).hexdigest(),
    runtime_id="cpython-3.11.14-numpy-2.4.6-reactor-matched-replay-forecast-programme",
    conformance_check_ids=(
        "14400-decisions-five-nested-episodes",
        "exact-source-pin",
        "no-inferred-delivery",
        "whole-unit-view-roster",
    ),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "reactor-batch",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (ReactorBatchConfig,),
    None,
    namespace="reactor-matched-replay-forecast",
)


# Executable roles.

from dataclasses import dataclass, replace

from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.providers import ExternalInputPayload

from empirical_lawhood.domains.reactor.reactor_matched_replay_forecast.design import ReactorBatchConfig


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (ReactorBatchConfig,)),
    required_platform_port_keys=("reactor-matched-replay-source-input",),
)


@dataclass(frozen=True, slots=True)
class ReactorBatchFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> ReactorBatchProvider:
        from empirical_lawhood.adapters.simulators.reactor_matched_replay_forecast.provider import ReactorBatchProvider
        if len(records) != 1 or not isinstance(records[0], ReactorBatchConfig):
            raise ValueError("reactor factory requires its exact full-batch configuration")
        if tuple(
            p.port_key for p in platform_ports
        ) != self.binding.required_platform_port_keys or not isinstance(
            platform_ports[0].port, ExternalInputPayload
        ):
            raise ValueError("reactor factory requires its authenticated source input port")
        return ReactorBatchProvider(registry, records[0], platform_ports[0].port)


_EXECUTABLE_ID = "executable-contribution.reactor-matched-replay-forecast.reactor-batch"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (ReactorBatchFactory(),)
_ISSUED_RECORD_TYPES = (ReactorBatchConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
