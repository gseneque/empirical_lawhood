# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.adapters.simulators.reactor_staged_pulse_response.provider import ClassicalNativeProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.discovery import ClassicalNomination
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.law_terminal import ClassicalLaws
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.frozen_records import ClassicalFrozenRoot
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.prospective_plan import ReactorStagedPulseResponseProspectivePlan
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.phase_records import ClassicalFirstScreen, ClassicalInducedBundle
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.prediction import ClassicalPredictionSeal
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.records import ClassicalPreparation, ClassicalPrivate, ClassicalAssay
from empirical_lawhood.domains.reactor.reactor_causal_response.campaign_records import EmpiricalStudySource
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.records import FrontierPreparation, FrontierPrivate, FrontierAssay
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.native_config import ClassicalNativeConfig
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.native_acquisition_records import ClassicalNativeRoot

OUTPUT_RECORDS = (
    ClassicalPreparation,
    ClassicalPrivate,
    ClassicalAssay,
    ClassicalInducedBundle,
    ClassicalNativeRoot,
)
CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="reactor-staged-pulse-response.native",
    kind=CapabilityKind.SIMULATOR,
    config_schema=ClassicalNativeConfig.SCHEMA,
    config_schema_sha256=sha256(ClassicalNativeConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            {
                r.SCHEMA
                for r in (
                    *OUTPUT_RECORDS,
                    ClassicalNativeConfig,
                    EmpiricalStudySource,
                    FrontierPreparation,
                    FrontierPrivate,
                    FrontierAssay,
                    ClassicalNomination,
                    ClassicalFirstScreen,
                    ClassicalPredictionSeal,
                    ClassicalFrozenRoot,
                    ReactorStagedPulseResponseProspectivePlan,
                    ClassicalLaws,
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
        b"reactor-staged-pulse-response:pinned-native-finite-words-nominal-refined-actual-two-cutoff-prefix"
    ).hexdigest(),
    runtime_id="cpython-reactor-staged-pulse-response",
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "native",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (ClassicalNativeConfig,),
    None,
    namespace="reactor-staged-pulse-response",
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import Any, cast
from empirical_lawhood.execution.closed_provider_ports import closed_ports, input_payloads
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.config import ClassicalStage
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.native_config import ClassicalNativeConfig
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (ClassicalNativeConfig,)),
    required_platform_port_keys=tuple(
        sorted(
            (
                "classical-native-reader",
                "classical-native-control",
                "classical-native-custody",
                "classical-native-inputs",
                "classical-native-limits",
                "classical-stage",
            )
        )
    ),
)


@dataclass(frozen=True, slots=True)
class ClassicalNativeFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> ClassicalNativeProvider:
        from empirical_lawhood.adapters.simulators.reactor_staged_pulse_response.provider import ClassicalNativeRunner, ClassicalNativeProvider
        config, ports = closed_ports(self.binding, records, ClassicalNativeConfig, platform_ports)
        other = ports["classical-stage"]
        if not isinstance(other, ClassicalStage) or other.design != config.design:
            raise ValueError("provider changes its exact stage/native design")
        runner = ClassicalNativeRunner(
            config,
            other,
            cast(Any, ports["classical-native-custody"]),
            cast(Any, ports["classical-native-limits"]),
            cast(Any, ports["classical-native-control"]),
            cast(Any, ports["classical-native-reader"]),
        )
        return ClassicalNativeProvider(
            registry, runner, input_payloads(ports["classical-native-inputs"])
        )


_EXECUTABLE_ID = "executable-contribution.reactor-staged-pulse-response.native"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (ClassicalNativeFactory(),)
_ISSUED_RECORD_TYPES = (ClassicalNativeConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION', 'OUTPUT_RECORDS']
