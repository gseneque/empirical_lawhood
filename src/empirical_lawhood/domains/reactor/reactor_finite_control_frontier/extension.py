# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.provider import FrontierMethodProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256
from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.domains.reactor.reactor_causal_response.campaign_records import EmpiricalStudySource
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.native_acquisition_records import FrontierNativeRoot
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.phase import FrontierPhase
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.records import FrontierPreparation, FrontierAssay
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.selection import FrontierPredictionSeal
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.measurement import FrontierMeasuredRoot
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.discovery import FrontierDevelopment
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.qualification import FrontierQualification
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.law_terminal import FrontierLaws
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.prospective_plan import ReactorFiniteControlFrontierProspectivePlan
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.frozen_records import FrontierFrozenRoot
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.prospective_seal import FrontierSealedRoot
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.prospective_reveal import FrontierRevealedRoot
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.prospective_cohort import ArchivedReactorFrontierCohort
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.comparison import FrontierComparison

OUTPUT_RECORDS = (
    FrontierPredictionSeal,
    FrontierMeasuredRoot,
    FrontierDevelopment,
    FrontierQualification,
    FrontierLaws,
    ReactorFiniteControlFrontierProspectivePlan,
    FrontierFrozenRoot,
    FrontierSealedRoot,
    FrontierRevealedRoot,
    ArchivedReactorFrontierCohort,
    FrontierComparison,
    ScientificAdjudicationRecord,
)
CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="reactor-finite-control-frontier.method",
    kind=CapabilityKind.EVALUATOR,
    config_schema=FrontierPhase.SCHEMA,
    config_schema_sha256=sha256(FrontierPhase.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            {
                r.SCHEMA
                for r in (
                    *OUTPUT_RECORDS,
                    FrontierPhase,
                    FrontierPreparation,
                    FrontierAssay,
                    FrontierNativeRoot,
                    EmpiricalStudySource,
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
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 7200, 8 * 1024**3, 512 * 1024**2),
    implementation_sha256=sha256(
        b"reactor-finite-control-frontier:72-independent-laws-singleton-admission-ranking-prepared-controller-use-root-joins"
    ).hexdigest(),
    runtime_id="cpython-reactor-finite-control-frontier",
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "method",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (FrontierPhase,),
    None,
    namespace="reactor-finite-control-frontier",
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast, Any
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.methods.law_assessment import CandidatePayloadPublisher, CandidatePayloadReader
from empirical_lawhood.domains.reactor.reactor_causal_response.resource_contract import EmpiricalResourceGuard
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.native_config import FrontierNativeConfig
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.providers import ExternalInputPayload
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.phase import FrontierPhase


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (FrontierPhase,)),
    required_platform_port_keys=tuple(
        sorted(
            (
                "frontier-custody",
                "frontier-limits",
                "frontier-control",
                "frontier-native-config",
                "frontier-method-inputs",
                "candidate-payload-reader",
                "candidate-payload-publisher",
            )
        )
    ),
)


@dataclass(frozen=True, slots=True)
class FrontierMethodFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> FrontierMethodProvider:
        from empirical_lawhood.domains.reactor.reactor_causal_response.provider import DependencyCustodyReader
        from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.provider import FrontierMethodRunner, FrontierMethodProvider
        if len(records) != 1 or not isinstance(records[0], FrontierPhase):
            raise ValueError("method factory requires its exact issued phase")
        ports = {p.port_key: p.port for p in platform_ports}
        if tuple(sorted(ports)) != self.binding.required_platform_port_keys or len(ports) != len(
            platform_ports
        ):
            raise ValueError("method factory changed its closed port roster")
        native = ports["frontier-native-config"]
        if not isinstance(native, FrontierNativeConfig) or native.design != records[0].design:
            raise ValueError("method factory lost its pinned native configuration")
        runner = FrontierMethodRunner(
            records[0],
            native,
            cast(DependencyCustodyReader, ports["frontier-custody"]),
            cast(EmpiricalResourceGuard, ports["frontier-limits"]),
            cast(CandidatePayloadPublisher, ports["candidate-payload-publisher"]),
            cast(CandidatePayloadReader, ports["candidate-payload-reader"]),
            cast(Any, ports["frontier-control"]),
        )
        inputs = ports["frontier-method-inputs"]
        if not isinstance(inputs, tuple) or any(
            not isinstance(p, ExternalInputPayload) for p in inputs
        ):
            raise TypeError("method factory requires exact upstream source payloads")
        return FrontierMethodProvider(registry, runner, inputs)


_EXECUTABLE_ID = "executable-contribution.reactor-finite-control-frontier.method"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (FrontierMethodFactory(),)
_ISSUED_RECORD_TYPES = (FrontierPhase,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION', 'OUTPUT_RECORDS']
