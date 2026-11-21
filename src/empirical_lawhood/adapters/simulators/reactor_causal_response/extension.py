# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.adapters.simulators.reactor_causal_response.provider import EmpiricalNativeProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256
from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.domains.reactor.reactor_causal_response.campaign_records import EmpiricalStudySource, TimedReactorConfirmationEnvelope
from empirical_lawhood.domains.reactor.reactor_causal_response.experiment_records import EmpiricalAcquisitionEnvelope, EmpiricalDiscoveryEnvelope, EmpiricalCalibrationEnvelope, EmpiricalQualificationTerminal
from empirical_lawhood.domains.reactor.reactor_causal_response.transport import CausalReactorRootEnvelope
from empirical_lawhood.domains.reactor.reactor_causal_response.native_config import EmpiricalNativeConfig, SOURCE_IMPLEMENTATION

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="reactor-causal-response.native-acquisition",
    kind=CapabilityKind.SIMULATOR,
    maximum_outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
    permissions=tuple(
        sorted((*FINITE_ACTION_MANIFEST.permissions, CapabilityPermission.READ_FROZEN_MODELS))
    ),
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    config_schema=EmpiricalNativeConfig.SCHEMA,
    config_schema_sha256=sha256(EmpiricalNativeConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            (
                EmpiricalNativeConfig.SCHEMA,
                EmpiricalStudySource.SCHEMA,
                EmpiricalQualificationTerminal.SCHEMA,
                EmpiricalDiscoveryEnvelope.SCHEMA,
                EmpiricalCalibrationEnvelope.SCHEMA,
            )
        )
    ),
    output_schema_ids=tuple(
        sorted(
            (
                EmpiricalAcquisitionEnvelope.SCHEMA,
                CausalReactorRootEnvelope.SCHEMA,
                TimedReactorConfirmationEnvelope.SCHEMA,
            )
        )
    ),
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 14400, 256 * 1024**2, 4 * 1024**3),
    implementation_sha256=SOURCE_IMPLEMENTATION,
    runtime_id="cpython-3.11.14-numpy-2.4.6-reactor-causal-response",
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "native-acquisition",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (EmpiricalNativeConfig,),
    None,
    namespace="reactor-causal-response",
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
from empirical_lawhood.methods.law_assessment import CandidatePayloadReader
from empirical_lawhood.adapters.simulators.reactor_causal_response.campaign import ControlCustodyPort
from empirical_lawhood.execution.task_records import DependencyCustodyReader
from empirical_lawhood.domains.reactor.reactor_causal_response.native_config import EmpiricalNativeConfig


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (EmpiricalNativeConfig,)),
    required_platform_port_keys=(
        "reactor-empirical-native-control-custody",
        "reactor-empirical-native-dependency-reader",
        "reactor-empirical-native-payload-reader",
        "reactor-empirical-native-resource-guard",
        "reactor-empirical-native-source-input",
    ),
)


@dataclass(frozen=True, slots=True)
class EmpiricalNativeFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> EmpiricalNativeProvider:
        from empirical_lawhood.adapters.simulators.reactor_causal_response.provider import EmpiricalNativeProvider
        if len(records) != 1 or not isinstance(records[0], EmpiricalNativeConfig):
            raise ValueError("native empirical factory requires its exact configuration")
        ports = {p.port_key: p.port for p in platform_ports}
        if tuple(sorted(ports)) != self.binding.required_platform_port_keys or len(ports) != len(
            platform_ports
        ):
            raise ValueError("native empirical factory port roster differs")
        source = ports["reactor-empirical-native-source-input"]
        if (
            not callable(
                getattr(
                    ports["reactor-empirical-native-payload-reader"], "read_candidate_payload", None
                )
            )
            or not isinstance(source, ExternalInputPayload)
            or not callable(
                getattr(
                    ports["reactor-empirical-native-dependency-reader"], "read_dependency", None
                )
            )
        ):
            raise TypeError("native empirical factory port contract differs")
        if not callable(
            getattr(ports["reactor-empirical-native-resource-guard"], "task", None)
        ) or not callable(
            getattr(ports["reactor-empirical-native-control-custody"], "open_control_store", None)
        ):
            raise TypeError("empirical resource/control ports differ")
        return EmpiricalNativeProvider(
            registry,
            records[0],
            source,
            cast(DependencyCustodyReader, ports["reactor-empirical-native-dependency-reader"]),
            cast(ControlCustodyPort, ports["reactor-empirical-native-control-custody"]),
            cast(CandidatePayloadReader, ports["reactor-empirical-native-payload-reader"]),
            limits=cast(EmpiricalResourceGuard, ports["reactor-empirical-native-resource-guard"]),
        )


_EXECUTABLE_ID = "executable-contribution.reactor-causal-response.native-acquisition"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (EmpiricalNativeFactory(),)
_ISSUED_RECORD_TYPES = (EmpiricalNativeConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
