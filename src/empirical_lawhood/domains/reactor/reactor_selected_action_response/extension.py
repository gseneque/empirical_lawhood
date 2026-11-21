# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.reactor.reactor_selected_action_response.provider import ClassicalMethodProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.domains.reactor.reactor_selected_action_response.prospective_records import ClassicalNativeRoot
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.domains.reactor.reactor_selected_action_response.config import ClassicalDesign
from empirical_lawhood.domains.reactor.reactor_selected_action_response.records import ClassicalCausal, ClassicalPrivate, ClassicalAssay, ClassicalDecision, ClassicalQualification
from empirical_lawhood.domains.reactor.reactor_selected_action_response.law_terminal import ClassicalLaw
from empirical_lawhood.domains.reactor.reactor_selected_action_response.control_prospective_plan import ReactorSelectedActionResponseProspectivePlan
from empirical_lawhood.domains.reactor.reactor_selected_action_response.control_prospective_closeout import ClassicalSealResult
from empirical_lawhood.domains.reactor.reactor_selected_action_response.control_prospective_reveal import ClassicalRevealResult
from empirical_lawhood.domains.reactor.reactor_selected_action_response.control_prospective_cohort import ReactorSelectedActionResponseProspectiveCohort

OUTPUT_RECORDS = (
    ClassicalDecision,
    ClassicalQualification,
    ClassicalLaw,
    ReactorSelectedActionResponseProspectivePlan,
    ClassicalSealResult,
    ClassicalRevealResult,
    ReactorSelectedActionResponseProspectiveCohort,
    ScientificAdjudicationRecord,
)
CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="reactor-selected-action-response.method",
    kind=CapabilityKind.EVALUATOR,
    config_schema=ClassicalDesign.SCHEMA,
    config_schema_sha256=sha256(ClassicalDesign.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            {
                r.SCHEMA
                for r in (
                    *OUTPUT_RECORDS,
                    ClassicalDesign,
                    ClassicalCausal,
                    ClassicalPrivate,
                    ClassicalAssay,
                    ClassicalNativeRoot,
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
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 1800, 8 * 1024**3, 256 * 1024**2),
    implementation_sha256=sha256(
        b"reactor-selected-action-response:selected-bound-sole-local-law-finite-admission-prepared-controller-use"
    ).hexdigest(),
    runtime_id="cpython-reactor-selected-action-response",
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "method",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (ClassicalDesign,),
    None,
    namespace="reactor-selected-action-response",
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.methods.law_assessment import CandidatePayloadPublisher, CandidatePayloadReader
from empirical_lawhood.domains.reactor.reactor_causal_response.resource_contract import EmpiricalResourceGuard
from empirical_lawhood.domains.reactor.reactor_selected_action_response.native_config import ClassicalNativeConfig
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.domains.reactor.reactor_selected_action_response.config import ClassicalDesign


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (ClassicalDesign,)),
    required_platform_port_keys=tuple(
        sorted(
            (
                "classical-custody",
                "classical-limits",
                "classical-control",
                "candidate-payload-reader",
                "candidate-payload-publisher",
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
        from empirical_lawhood.domains.reactor.reactor_causal_response.provider import DependencyCustodyReader
        from empirical_lawhood.domains.reactor.reactor_selected_action_response.provider import ClassicalControlCustody
        from empirical_lawhood.domains.reactor.reactor_selected_action_response.provider import ClassicalMethodRunner, ClassicalMethodProvider
        if len(records) != 1 or not isinstance(records[0], ClassicalDesign):
            raise ValueError("classical method factory requires its exact issued configuration")
        ports = {p.port_key: p.port for p in platform_ports}
        if tuple(sorted(ports)) != self.binding.required_platform_port_keys or len(ports) != len(
            platform_ports
        ):
            raise ValueError("classical method factory port roster changed")
        for key, method in (
            ("classical-custody", "read_dependency"),
            ("classical-limits", "task"),
            ("classical-control", "open_prepared_store"),
            ("candidate-payload-reader", "read_candidate_payload"),
        ):
            if not callable(getattr(ports[key], method, None)):
                raise TypeError(
                    "classical factory lacks its installed custody, limits or control port"
                )
        native = ports["classical-native-config"]
        if not isinstance(native, ClassicalNativeConfig) or native.design != records[0]:
            raise ValueError("classical method factory changed its bound native preparation domain")
        if not callable(
            getattr(ports["candidate-payload-publisher"], "publish_candidate_payload", None)
        ):
            raise TypeError("classical method factory lacks publication")
        runner = ClassicalMethodRunner(
            records[0],
            native,
            cast(DependencyCustodyReader, ports["classical-custody"]),
            cast(EmpiricalResourceGuard, ports["classical-limits"]),
            cast(CandidatePayloadPublisher, ports["candidate-payload-publisher"]),
            cast(CandidatePayloadReader, ports["candidate-payload-reader"]),
            cast(ClassicalControlCustody, ports["classical-control"]),
        )
        return ClassicalMethodProvider(registry, runner)


_EXECUTABLE_ID = "executable-contribution.reactor-selected-action-response.method"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (ClassicalMethodFactory(),)
_ISSUED_RECORD_TYPES = (ClassicalDesign,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION', 'OUTPUT_RECORDS']
