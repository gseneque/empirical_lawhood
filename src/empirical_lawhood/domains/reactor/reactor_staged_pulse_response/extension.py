# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.provider import ClassicalMethodProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.domains.reactor.reactor_causal_response.campaign_records import EmpiricalStudySource
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.discovery import FrontierDevelopment
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.measurement import FrontierMeasuredRoot
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.records import FrontierPreparation, FrontierAssay
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.selection import FrontierPredictionSeal
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.native_acquisition_records import ClassicalNativeRoot
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.calibration import ClassicalCalibration
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.comparison import ClassicalComparison
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.config import ClassicalStage
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.discovery import ClassicalNomination
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.law_terminal import ClassicalLaws
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.measurement import ClassicalMeasuredRoot
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.prospective_cohort import ReactorStagedPulseResponseProspectiveCohort
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.frozen_records import ClassicalFrozenRoot
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.prospective_plan import ReactorStagedPulseResponseProspectivePlan
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.prospective_reveal import ClassicalRevealedRoot
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.prospective_seal import ClassicalSealedRoot
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.phase_records import ClassicalFirstScreen, ClassicalInducedBundle
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.prediction import ClassicalPredictionSeal
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.qualification import ClassicalQualification
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.records import ClassicalPreparation, ClassicalAssay

OUTPUT_RECORDS = (
    ClassicalCalibration,
    ClassicalNomination,
    ClassicalFirstScreen,
    ClassicalPredictionSeal,
    ClassicalMeasuredRoot,
    ClassicalQualification,
    ClassicalLaws,
    ReactorStagedPulseResponseProspectivePlan,
    ClassicalFrozenRoot,
    ClassicalSealedRoot,
    ClassicalRevealedRoot,
    ReactorStagedPulseResponseProspectiveCohort,
    ClassicalComparison,
    ScientificAdjudicationRecord,
)
CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="reactor-staged-pulse-response.method",
    kind=CapabilityKind.EVALUATOR,
    config_schema=ClassicalStage.SCHEMA,
    config_schema_sha256=sha256(ClassicalStage.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            {
                r.SCHEMA
                for r in (
                    *OUTPUT_RECORDS,
                    ClassicalStage,
                    ClassicalPreparation,
                    ClassicalAssay,
                    ClassicalInducedBundle,
                    ClassicalNativeRoot,
                    EmpiricalStudySource,
                    FrontierDevelopment,
                    FrontierMeasuredRoot,
                    FrontierPreparation,
                    FrontierAssay,
                    FrontierPredictionSeal,
                )
            }
        )
    ),
    output_schema_ids=tuple(sorted(r.SCHEMA for r in OUTPUT_RECORDS)),
    permissions=tuple(
        sorted(
            (
                CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
                CapabilityPermission.READ_SEALED_OUTCOMES,
                CapabilityPermission.REVEAL_OUTCOMES,
            )
        )
    ),
    maximum_evidence_ceiling=EvidenceCeiling.CONTROLLER_USE,
    maximum_outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 10800, 8 * 1024**3, 512 * 1024**2),
    implementation_sha256=sha256(
        b"reactor-staged-pulse-response:fixed-calibration-receiver-map-finite-law-owner-prepared-use-bounded-sequence-root-families"
    ).hexdigest(),
    runtime_id="cpython-reactor-staged-pulse-response",
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "method",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (ClassicalStage,),
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
    executable(CAPABILITY, COMPONENTS, (ClassicalStage,)),
    required_platform_port_keys=tuple(
        sorted(
            (
                "candidate-payload-publisher",
                "candidate-payload-reader",
                "classical-control",
                "classical-custody",
                "classical-method-inputs",
                "classical-limits",
                "classical-native-config",
            )
        )
    ),
)


@dataclass(frozen=True, slots=True)
class ClassicalMethodFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> ClassicalMethodProvider:
        from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.provider import ClassicalMethodRunner, ClassicalMethodProvider
        config, ports = closed_ports(self.binding, records, ClassicalStage, platform_ports)
        other = ports["classical-native-config"]
        if not isinstance(other, ClassicalNativeConfig) or other.design != config.design:
            raise ValueError("provider changes its exact stage/native design")
        runner = ClassicalMethodRunner(
            config,
            other,
            cast(Any, ports["classical-custody"]),
            cast(Any, ports["classical-limits"]),
            cast(Any, ports["candidate-payload-publisher"]),
            cast(Any, ports["candidate-payload-reader"]),
            cast(Any, ports["classical-control"]),
        )
        return ClassicalMethodProvider(
            registry, runner, input_payloads(ports["classical-method-inputs"])
        )


_EXECUTABLE_ID = "executable-contribution.reactor-staged-pulse-response.method"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (ClassicalMethodFactory(),)
_ISSUED_RECORD_TYPES = (ClassicalStage,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION', 'OUTPUT_RECORDS']
