# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.adapters.simulators.reactor_local_domain_qualification.provider import LocalNativeProvider


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
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.records import LocalRootEvidence
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.scoring import LocalCalibration
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.native_config import LocalNativeConfig

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="terminal-bench-science-local.native-acquisition",
    kind=CapabilityKind.SIMULATOR,
    maximum_outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
    permissions=tuple(
        sorted((*FINITE_ACTION_MANIFEST.permissions, CapabilityPermission.READ_FROZEN_MODELS))
    ),
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    config_schema=LocalNativeConfig.SCHEMA,
    config_schema_sha256=sha256(LocalNativeConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            (LocalNativeConfig.SCHEMA, EmpiricalStudySource.SCHEMA, LocalCalibration.SCHEMA)
        )
    ),
    output_schema_ids=(LocalRootEvidence.SCHEMA,),
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 1800, 256 * 1024**2, 128 * 1024**2),
    implementation_sha256=sha256(
        b"reactor-local-native:causal-anchor-full-tape-nine-word-matched-views"
    ).hexdigest(),
    runtime_id="cpython-reactor-local",
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "native-acquisition",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (LocalNativeConfig,),
    None,
    namespace="reactor-local-domain-qualification",
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
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.native_config import LocalNativeConfig


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (LocalNativeConfig,)),
    required_platform_port_keys=(
        "reactor-local-native-dependency-reader",
        "reactor-local-native-resource-guard",
        "reactor-local-native-source-input",
    ),
)


@dataclass(frozen=True, slots=True)
class LocalNativeFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> LocalNativeProvider:
        from empirical_lawhood.domains.reactor.reactor_causal_response.provider import DependencyCustodyReader
        from empirical_lawhood.adapters.simulators.reactor_local_domain_qualification.provider import LocalNativeProvider
        if len(records) != 1 or not isinstance(records[0], LocalNativeConfig):
            raise ValueError("local factory requires its exact configuration")
        ports = {p.port_key: p.port for p in platform_ports}
        if tuple(sorted(ports)) != self.binding.required_platform_port_keys or len(ports) != len(
            platform_ports
        ):
            raise ValueError("local factory port roster differs")
        if not callable(
            getattr(ports["reactor-local-native-dependency-reader"], "read_dependency", None)
        ):
            raise TypeError(
                "local factory port contract differs: reactor-local-native-dependency-reader"
            )
        if not callable(getattr(ports["reactor-local-native-resource-guard"], "task", None)):
            raise TypeError(
                "local factory port contract differs: reactor-local-native-resource-guard"
            )
        if not isinstance(ports["reactor-local-native-source-input"], ExternalInputPayload):
            raise TypeError(
                "local factory port contract differs: reactor-local-native-source-input"
            )
        return LocalNativeProvider(
            registry,
            records[0],
            ports["reactor-local-native-source-input"],
            cast(DependencyCustodyReader, ports["reactor-local-native-dependency-reader"]),
            cast(EmpiricalResourceGuard, ports["reactor-local-native-resource-guard"]),
        )


_EXECUTABLE_ID = "executable-contribution.terminal-bench-science-local.simulators"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (LocalNativeFactory(),)
_ISSUED_RECORD_TYPES = (LocalNativeConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
