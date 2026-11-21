# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.adapters.simulators.reactor_prepared_feed_qualification.provider import FeedNativeProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256
from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.domains.reactor.reactor_causal_response.campaign_records import EmpiricalStudySource
from empirical_lawhood.domains.reactor.reactor_prepared_feed_qualification.records import FeedRootEvidence
from empirical_lawhood.domains.reactor.reactor_prepared_feed_qualification.scoring import FeedCalibration
from empirical_lawhood.domains.reactor.reactor_prepared_feed_qualification.native_config import FeedNativeConfig

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="terminal-bench-science-feed.native-acquisition",
    kind=CapabilityKind.SIMULATOR,
    maximum_outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
    permissions=tuple(
        sorted((*FINITE_ACTION_MANIFEST.permissions, CapabilityPermission.READ_FROZEN_MODELS))
    ),
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    config_schema=FeedNativeConfig.SCHEMA,
    config_schema_sha256=sha256(FeedNativeConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted((FeedNativeConfig.SCHEMA, EmpiricalStudySource.SCHEMA, FeedCalibration.SCHEMA))
    ),
    output_schema_ids=(FeedRootEvidence.SCHEMA,),
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 1800, 256 * 1024**2, 128 * 1024**2),
    implementation_sha256=sha256(
        b"reactor-feed-native:causal-anchor-full-tape-nine-word-matched-views"
    ).hexdigest(),
    runtime_id="cpython-reactor-feed",
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "native-acquisition",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (FeedNativeConfig,),
    None,
    namespace="reactor-prepared-feed-qualification",
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast
from empirical_lawhood.domains.reactor.reactor_causal_response.resource_contract import EmpiricalResourceGuard
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.providers import ExternalInputPayload
from empirical_lawhood.domains.reactor.reactor_prepared_feed_qualification.native_config import FeedNativeConfig


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (FeedNativeConfig,)),
    required_platform_port_keys=(
        "reactor-feed-native-dependency-reader",
        "reactor-feed-native-resource-guard",
        "reactor-feed-native-source-input",
    ),
)


@dataclass(frozen=True, slots=True)
class FeedNativeFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> FeedNativeProvider:
        from empirical_lawhood.domains.reactor.reactor_causal_response.provider import DependencyCustodyReader
        from empirical_lawhood.adapters.simulators.reactor_prepared_feed_qualification.provider import FeedNativeProvider
        if len(records) != 1 or not isinstance(records[0], FeedNativeConfig):
            raise ValueError("local factory requires its exact configuration")
        ports = {p.port_key: p.port for p in platform_ports}
        if tuple(sorted(ports)) != self.binding.required_platform_port_keys or len(ports) != len(
            platform_ports
        ):
            raise ValueError("local factory port roster differs")
        if not callable(
            getattr(ports["reactor-feed-native-dependency-reader"], "read_dependency", None)
        ):
            raise TypeError(
                "local factory port contract differs: reactor-feed-native-dependency-reader"
            )
        if not callable(getattr(ports["reactor-feed-native-resource-guard"], "task", None)):
            raise TypeError(
                "local factory port contract differs: reactor-feed-native-resource-guard"
            )
        if not isinstance(ports["reactor-feed-native-source-input"], ExternalInputPayload):
            raise TypeError("local factory port contract differs: reactor-feed-native-source-input")
        return FeedNativeProvider(
            registry,
            records[0],
            ports["reactor-feed-native-source-input"],
            cast(DependencyCustodyReader, ports["reactor-feed-native-dependency-reader"]),
            cast(EmpiricalResourceGuard, ports["reactor-feed-native-resource-guard"]),
        )


_EXECUTABLE_ID = "executable-contribution.terminal-bench-science-feed.simulators"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (FeedNativeFactory(),)
_ISSUED_RECORD_TYPES = (FeedNativeConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
