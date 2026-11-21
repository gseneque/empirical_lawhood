# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.adapters.simulators.reactor_finite_control_frontier.provider import FrontierNativeProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256
from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.domains.reactor.reactor_causal_response.campaign_records import EmpiricalStudySource
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.records import FrontierPreparation, FrontierPrivate, FrontierAssay, FrontierRetainedRoot
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.selection import FrontierPredictionSeal
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.prospective_plan import ReactorFiniteControlFrontierProspectivePlan
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.frozen_records import FrontierFrozenRoot
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.native_config import FrontierNativeConfig
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.native_acquisition_records import FrontierNativeRoot

OUTPUT_RECORDS = (FrontierPreparation, FrontierPrivate, FrontierAssay, FrontierNativeRoot)
CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="reactor-finite-control-frontier.native",
    kind=CapabilityKind.SIMULATOR,
    config_schema=FrontierNativeConfig.SCHEMA,
    config_schema_sha256=sha256(FrontierNativeConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            {
                r.SCHEMA
                for r in (
                    *OUTPUT_RECORDS,
                    FrontierNativeConfig,
                    EmpiricalStudySource,
                    FrontierRetainedRoot,
                    FrontierPredictionSeal,
                    FrontierFrozenRoot,
                    ReactorFiniteControlFrontierProspectivePlan,
                )
            }
        )
    ),
    output_schema_ids=tuple(sorted(r.SCHEMA for r in OUTPUT_RECORDS)),
    permissions=tuple(
        sorted(
            (
                *FINITE_ACTION_MANIFEST.permissions,
                CapabilityPermission.READ_FROZEN_MODELS,
                CapabilityPermission.READ_SEALED_OUTCOMES,
            )
        )
    ),
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    maximum_outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 1800, 8 * 1024**3, 512 * 1024**2),
    implementation_sha256=sha256(
        b"reactor-finite-control-frontier:pinned-native-unshifted-exploration-complete-twelve-command-pulse-paired-refinement"
    ).hexdigest(),
    runtime_id="cpython-reactor-finite-control-frontier",
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "native",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (FrontierNativeConfig,),
    None,
    namespace="reactor-finite-control-frontier",
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast, Any
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.domains.reactor.reactor_causal_response.resource_contract import EmpiricalResourceGuard
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.phase import FrontierPhase
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.providers import ExternalInputPayload
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.native_config import FrontierNativeConfig


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (FrontierNativeConfig,)),
    required_platform_port_keys=tuple(
        sorted(
            (
                "frontier-native-custody",
                "frontier-native-limits",
                "frontier-native-control",
                "frontier-native-inputs",
                "frontier-phase",
            )
        )
    ),
)


@dataclass(frozen=True, slots=True)
class FrontierNativeFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> FrontierNativeProvider:
        from empirical_lawhood.domains.reactor.reactor_causal_response.provider import DependencyCustodyReader
        from empirical_lawhood.adapters.simulators.reactor_finite_control_frontier.provider import FrontierNativeRunner, FrontierNativeProvider
        if len(records) != 1 or not isinstance(records[0], FrontierNativeConfig):
            raise ValueError("native factory requires its exact issued configuration")
        ports = {p.port_key: p.port for p in platform_ports}
        if tuple(sorted(ports)) != self.binding.required_platform_port_keys or len(ports) != len(
            platform_ports
        ):
            raise ValueError("native factory changed its closed port roster")
        phase = ports["frontier-phase"]
        if not isinstance(phase, FrontierPhase) or phase.design != records[0].design:
            raise ValueError("native factory lost its exact issued phase")
        inputs = ports["frontier-native-inputs"]
        if not isinstance(inputs, tuple) or any(
            not isinstance(p, ExternalInputPayload) for p in inputs
        ):
            raise TypeError("native factory requires its exact upstream payloads")
        runner = FrontierNativeRunner(
            records[0],
            phase,
            cast(DependencyCustodyReader, ports["frontier-native-custody"]),
            cast(EmpiricalResourceGuard, ports["frontier-native-limits"]),
            cast(Any, ports["frontier-native-control"]),
        )
        return FrontierNativeProvider(registry, runner, inputs)


_EXECUTABLE_ID = "executable-contribution.reactor-finite-control-frontier.native"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (FrontierNativeFactory(),)
_ISSUED_RECORD_TYPES = (FrontierNativeConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION', 'OUTPUT_RECORDS']
