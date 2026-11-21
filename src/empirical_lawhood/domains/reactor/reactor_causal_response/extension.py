# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256
from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, EvidenceCeiling
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.domains.reactor.reactor_causal_response.config import EmpiricalRecipe
from empirical_lawhood.domains.reactor.reactor_causal_response.payload import DevelopmentBoundReactorResponsePayload
from empirical_lawhood.domains.reactor.reactor_causal_response.transport import CausalReactorRootEnvelope
from empirical_lawhood.domains.reactor.reactor_causal_response.terminal import EmpiricalQualificationResult
from empirical_lawhood.domains.reactor.reactor_causal_response.experiment_records import EmpiricalAcquisitionEnvelope, EmpiricalDiscoveryEnvelope, EmpiricalCalibrationEnvelope, EmpiricalQualificationTerminal

from empirical_lawhood.domains.reactor.reactor_causal_response.campaign_records import EmpiricalStudySource, TimedReactorConfirmationEnvelope, EmpiricalRootAnalysis, EmpiricalContributionResult, EmpiricalNativeBenchmarkResult

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="reactor-causal-response.numerical-method",
    kind=CapabilityKind.EVALUATOR,
    maximum_evidence_ceiling=EvidenceCeiling.CONTROLLER_USE,
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
    config_schema=EmpiricalRecipe.SCHEMA,
    config_schema_sha256=sha256(EmpiricalRecipe.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            (
                EmpiricalRecipe.SCHEMA,
                EmpiricalStudySource.SCHEMA,
                TimedReactorConfirmationEnvelope.SCHEMA,
                EmpiricalRootAnalysis.SCHEMA,
                EmpiricalContributionResult.SCHEMA,
                EmpiricalNativeBenchmarkResult.SCHEMA,
                DevelopmentBoundReactorResponsePayload.SCHEMA,
                CausalReactorRootEnvelope.SCHEMA,
                EmpiricalQualificationResult.SCHEMA,
                EmpiricalAcquisitionEnvelope.SCHEMA,
                EmpiricalDiscoveryEnvelope.SCHEMA,
                EmpiricalCalibrationEnvelope.SCHEMA,
                EmpiricalQualificationTerminal.SCHEMA,
            )
        )
    ),
    output_schema_ids=tuple(
        sorted(
            (
                EmpiricalDiscoveryEnvelope.SCHEMA,
                EmpiricalCalibrationEnvelope.SCHEMA,
                EmpiricalQualificationTerminal.SCHEMA,
                EmpiricalQualificationResult.SCHEMA,
                EmpiricalRootAnalysis.SCHEMA,
                EmpiricalContributionResult.SCHEMA,
                EmpiricalNativeBenchmarkResult.SCHEMA,
                ScientificAdjudicationRecord.SCHEMA,
            )
        )
    ),
    implementation_sha256=sha256(
        b"reactor-empirical-eight-root:causal-nine-ridge-rank32-descriptive-five-native"
    ).hexdigest(),
    runtime_id="cpython-reactor-causal-response",
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 12 * 3600, 256 * 1024**3, 256 * 1024**3),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "numerical-method",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (EmpiricalRecipe,),
    None,
    namespace="reactor-causal-response",
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.reactor.reactor_causal_response.resource_contract import EmpiricalResourceGuard

from empirical_lawhood.methods.law_assessment import CandidatePayloadPublisher, CandidatePayloadReader
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.domains.reactor.reactor_causal_response.config import EmpiricalRecipe

from empirical_lawhood.execution.task_records import DependencyCustodyReader
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.reactor.reactor_causal_response.provider import EmpiricalProvider
from empirical_lawhood.domains.reactor.reactor_causal_response.native_benchmark import NativeVerifierPort
from empirical_lawhood.execution.providers import ExternalInputPayload
from empirical_lawhood.adapters.simulators.reactor_causal_response.campaign import ControlCustodyPort


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (EmpiricalRecipe,)),
    required_platform_port_keys=(
        "candidate-payload-publisher",
        "candidate-payload-reader",
        "dependency-custody-reader",
        "reactor-causal-response-source-input",
        "reactor-empirical-control-custody",
        "reactor-empirical-native-verifier",
        "reactor-empirical-resource-guard",
    ),
)


@dataclass(frozen=True, slots=True)
class EmpiricalFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> EmpiricalProvider:
        from empirical_lawhood.domains.reactor.reactor_causal_response.provider import EmpiricalProvider
        if len(records) != 1 or not isinstance(records[0], EmpiricalRecipe):
            raise ValueError("finite chain factory requires its exact pre-acquisition design")
        ports = {p.port_key: p.port for p in platform_ports}
        if (
            len(platform_ports) != 7
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
        if not callable(
            getattr(ports["reactor-empirical-resource-guard"], "task", None)
        ) or not callable(
            getattr(ports["reactor-empirical-control-custody"], "open_control_store", None)
        ):
            raise TypeError("empirical resource/control ports differ")
        if not isinstance(ports["reactor-causal-response-source-input"], ExternalInputPayload) or (
            not callable(getattr(ports["reactor-empirical-native-verifier"], "verify", None))
            or not isinstance(
                getattr(ports["reactor-empirical-native-verifier"], "environment", None),
                ObjectIdentity,
            )
        ):
            raise TypeError("empirical source/verifier ports differ")
        return EmpiricalProvider(
            registry,
            records[0],
            cast(CandidatePayloadPublisher, ports["candidate-payload-publisher"]),
            cast(CandidatePayloadReader, ports["candidate-payload-reader"]),
            cast(DependencyCustodyReader, ports["dependency-custody-reader"]),
            cast(ControlCustodyPort, ports["reactor-empirical-control-custody"]),
            cast(NativeVerifierPort, ports["reactor-empirical-native-verifier"]),
            ports["reactor-causal-response-source-input"],
            limits=cast(EmpiricalResourceGuard, ports["reactor-empirical-resource-guard"]),
        )


_EXECUTABLE_ID = "executable-contribution.reactor-causal-response.numerical-method"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (EmpiricalFactory(),)
_ISSUED_RECORD_TYPES = (EmpiricalRecipe,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
