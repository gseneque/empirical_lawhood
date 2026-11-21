# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.adapters.simulators.reactor_selected_action_response.provider import ClassicalNativeProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.domains.reactor.reactor_causal_response.campaign_records import EmpiricalStudySource
from empirical_lawhood.domains.reactor.reactor_selected_action_response.records import ClassicalCausal, ClassicalPrivate, ClassicalAssay, ClassicalDecision, ClassicalQualification
from empirical_lawhood.domains.reactor.reactor_selected_action_response.law_terminal import ClassicalLaw
from empirical_lawhood.domains.reactor.reactor_selected_action_response.control_prospective_plan import ReactorSelectedActionResponseProspectivePlan
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.domains.reactor.reactor_selected_action_response.native_config import ClassicalNativeConfig
from empirical_lawhood.domains.reactor.reactor_selected_action_response.prospective_records import ClassicalNativeRoot

OUTPUT_RECORDS = (ClassicalCausal, ClassicalPrivate, ClassicalAssay, ClassicalNativeRoot)
CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="reactor-selected-action-response.native",
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
                    ClassicalDecision,
                    ClassicalQualification,
                    ClassicalLaw,
                    ReactorSelectedActionResponseProspectivePlan,
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
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 1800, 8 * 1024**3, 256 * 1024**2),
    implementation_sha256=sha256(
        b"reactor-selected-action-response:native-pinned-medium-causal-preparation-sealed-delivery"
    ).hexdigest(),
    runtime_id="cpython-reactor-selected-action-response",
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "native",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (ClassicalNativeConfig,),
    None,
    namespace="reactor-selected-action-response",
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.methods.law_assessment import CandidatePayloadReader
from empirical_lawhood.domains.reactor.reactor_causal_response.resource_contract import EmpiricalResourceGuard
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.providers import ExternalInputPayload
from empirical_lawhood.domains.reactor.reactor_selected_action_response.native_config import ClassicalNativeConfig


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (ClassicalNativeConfig,)),
    required_platform_port_keys=tuple(
        sorted(
            (
                "classical-native-custody",
                "classical-native-limits",
                "classical-native-control",
                "classical-native-law-reader",
                "classical-source-input",
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
        from empirical_lawhood.domains.reactor.reactor_causal_response.provider import DependencyCustodyReader
        from empirical_lawhood.domains.reactor.reactor_selected_action_response.provider import ClassicalControlCustody
        from empirical_lawhood.adapters.simulators.reactor_selected_action_response.provider import ClassicalNativeRunner, ClassicalNativeProvider
        if len(records) != 1 or not isinstance(records[0], ClassicalNativeConfig):
            raise ValueError("classical native factory requires its exact issued configuration")
        ports = {p.port_key: p.port for p in platform_ports}
        if tuple(sorted(ports)) != self.binding.required_platform_port_keys or len(ports) != len(
            platform_ports
        ):
            raise ValueError("classical native factory port roster changed")
        for key, method in (
            ("classical-native-custody", "read_dependency"),
            ("classical-native-limits", "task"),
            ("classical-native-control", "open_prepared_store"),
            ("classical-native-law-reader", "read_candidate_payload"),
        ):
            if not callable(getattr(ports[key], method, None)):
                raise TypeError(
                    "classical factory lacks its installed custody, limits or control port"
                )
        runner = ClassicalNativeRunner(
            records[0],
            cast(DependencyCustodyReader, ports["classical-native-custody"]),
            cast(EmpiricalResourceGuard, ports["classical-native-limits"]),
            cast(ClassicalControlCustody, ports["classical-native-control"]),
            cast(CandidatePayloadReader, ports["classical-native-law-reader"]),
        )
        source = ports["classical-source-input"]
        if not isinstance(source, ExternalInputPayload):
            raise TypeError("classical native source has no declared input payload")
        return ClassicalNativeProvider(registry, runner, source)


_EXECUTABLE_ID = "executable-contribution.reactor-selected-action-response.native"
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
