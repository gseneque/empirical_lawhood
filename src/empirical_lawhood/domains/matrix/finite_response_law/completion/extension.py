# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.matrix.finite_response_law.completion.provider import FiniteResponseLawRetainedCompletionProvider


# Scientific registration and configuration.

from dataclasses import replace
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.declaration_helpers import manifest, bundle
from empirical_lawhood.domains.matrix.finite_response_law.native_records import FiniteResponseLawCalibrationViewObservation, FiniteResponseLawCalibrationNativeEvaluation
from empirical_lawhood.domains.matrix.finite_response_law.assigned_native_records import FiniteResponseLawAssignedEvaluationViewObservation, FiniteResponseLawAssignedEvaluationNativeCompletion
from empirical_lawhood.domains.matrix.finite_response_law.completion.contracts import FiniteResponseLawAssignedRetainedCompletionConfig, FiniteResponseLawRetainedCompletionConfig, PROSPECTIVE_EVALUATION_COMPLETION_PREFIX, PREFIX
from empirical_lawhood.domains.matrix.finite_response_law.fresh_contracts import FiniteResponseLawCalibrationConfig
from empirical_lawhood.domains.matrix.finite_response_law.assigned_contracts import FiniteResponseLawAssignedEvaluationConfig

CAPABILITY = manifest(
    "completion",
    FiniteResponseLawRetainedCompletionConfig,
    CapabilityKind.EVALUATOR,
    (
        FiniteResponseLawRetainedCompletionConfig.SCHEMA,
        FiniteResponseLawCalibrationConfig.SCHEMA,
        ObjectIdentity.SCHEMA,
        FiniteResponseLawCalibrationViewObservation.SCHEMA,
        CanonicalTaskReceipt.SCHEMA,
        FiniteResponseLawCalibrationNativeEvaluation.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (
        ObjectIdentity.SCHEMA,
        FiniteResponseLawCalibrationNativeEvaluation.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
        ScientificAdjudicationRecord.SCHEMA,
    ),
    EvidenceCeiling.MEASUREMENT,
    OutcomeAccess.EVALUATOR_REVEAL,
    180,
    namespace=PREFIX,
    resources=ResourceBudget(1, 1024**3, 0, 180, 96 * 1024**2, 16 * 1024**2),
    read_permission=CapabilityPermission.READ_SEALED_OUTCOMES,
    implementation_id="retained-64-projection-custody-separate-adjudication",
    conformance_ids=(
        "exact-retained-projection-receipts",
        "no-native-recomputation",
        "separate-publication-evidence-classes",
    ),
)
CAPABILITY = replace(
    CAPABILITY,
    permissions=tuple(sorted((*CAPABILITY.permissions, CapabilityPermission.REVEAL_OUTCOMES))),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "completion",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (FiniteResponseLawRetainedCompletionConfig,),
    None,
    namespace=PREFIX,
)
ASSIGNED_CAPABILITY = manifest(
    "completion",
    FiniteResponseLawAssignedRetainedCompletionConfig,
    CapabilityKind.EVALUATOR,
    (
        FiniteResponseLawAssignedRetainedCompletionConfig.SCHEMA,
        FiniteResponseLawAssignedEvaluationConfig.SCHEMA,
        ObjectIdentity.SCHEMA,
        FiniteResponseLawAssignedEvaluationViewObservation.SCHEMA,
        CanonicalTaskReceipt.SCHEMA,
        FiniteResponseLawAssignedEvaluationNativeCompletion.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (
        ObjectIdentity.SCHEMA,
        FiniteResponseLawAssignedEvaluationNativeCompletion.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
        ScientificAdjudicationRecord.SCHEMA,
    ),
    EvidenceCeiling.MEASUREMENT,
    OutcomeAccess.EVALUATOR_REVEAL,
    180,
    namespace=PROSPECTIVE_EVALUATION_COMPLETION_PREFIX,
    resources=ResourceBudget(1, 1024**3, 0, 180, 96 * 1024**2, 16 * 1024**2),
    read_permission=CapabilityPermission.READ_SEALED_OUTCOMES,
    implementation_id="assigned-retained-128-projection-custody-separate-adjudication",
    conformance_ids=(
        "exact-retained-projection-receipts",
        "no-native-recomputation",
        "separate-publication-evidence-classes",
    ),
)
ASSIGNED_CAPABILITY = replace(
    ASSIGNED_CAPABILITY,
    permissions=tuple(sorted((*ASSIGNED_CAPABILITY.permissions, CapabilityPermission.REVEAL_OUTCOMES))),
)
_assigned, ASSIGNED_COMPONENTS = bundle(
    "completion",
    ExtensionContributionKind.METHOD,
    ASSIGNED_CAPABILITY,
    (FiniteResponseLawAssignedRetainedCompletionConfig,),
    None,
    namespace=PROSPECTIVE_EVALUATION_COMPLETION_PREFIX,
)
_parts = (_DISCOVERY_CONTRIBUTION, _assigned)
_DISCOVERY_CONTRIBUTION = replace(
    _DISCOVERY_CONTRIBUTION,
    capability_manifests=tuple(
        sorted((v for part in _parts for v in part.capability_manifests), key=lambda v: v.registry_id)
    ),
    candidate_capability_registrations=tuple(
        sorted(
            (v for part in _parts for v in part.candidate_capability_registrations),
            key=lambda v: v.registration_id,
        )
    ),
    profile_registrations=tuple(
        sorted((v for part in _parts for v in part.profile_registrations), key=lambda v: v.registration_id)
    ),
    config_decoders=tuple(
        sorted((v for part in _parts for v in part.config_decoders), key=lambda v: v.object_id)
    ),
    runtime_providers=tuple(
        sorted((v for part in _parts for v in part.runtime_providers), key=lambda v: v.object_id)
    ),
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.source_resolution import ContentAddressedInputResolver
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.domains.matrix.finite_response_law.completion.contracts import FiniteResponseLawAssignedRetainedCompletionConfig, FiniteResponseLawRetainedCompletionConfig, PREFIX

from empirical_lawhood.domains.matrix.finite_response_law.method_provider import INPUT_RESOLVER_PORT

BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (FiniteResponseLawRetainedCompletionConfig,)),
    required_platform_port_keys=(INPUT_RESOLVER_PORT,),
)
ASSIGNED_BINDING = replace(
    executable(
        ASSIGNED_CAPABILITY,
        ASSIGNED_COMPONENTS,
        (FiniteResponseLawAssignedRetainedCompletionConfig,),
    ),
    required_platform_port_keys=(INPUT_RESOLVER_PORT,),
)


@dataclass(frozen=True, slots=True)
class FiniteResponseLawRetainedCompletionFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> FiniteResponseLawRetainedCompletionProvider:
        from empirical_lawhood.domains.matrix.finite_response_law.completion.provider import FiniteResponseLawRetainedCompletionProvider
        manifest = CAPABILITY if self.binding == BINDING else ASSIGNED_CAPABILITY
        config_type = (
            FiniteResponseLawRetainedCompletionConfig
            if self.binding == BINDING
            else FiniteResponseLawAssignedRetainedCompletionConfig
        )
        if (
            self.binding not in (BINDING, ASSIGNED_BINDING)
            or len(records) != 1
            or type(records[0]) is not config_type
            or tuple(p.port_key for p in platform_ports) != (INPUT_RESOLVER_PORT,)
        ):
            raise ValueError("Retained completion requires its exact config and resolver")
        return FiniteResponseLawRetainedCompletionProvider(
            registry,
            manifest,
            records[0],
            cast(ContentAddressedInputResolver, platform_ports[0].port),
        )


_EXECUTABLE_ID = f"executable-contribution.{PREFIX}"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (
    FiniteResponseLawRetainedCompletionFactory(),
    FiniteResponseLawRetainedCompletionFactory(ASSIGNED_BINDING),
)
_ISSUED_RECORD_TYPES = (
    FiniteResponseLawRetainedCompletionConfig,
    FiniteResponseLawAssignedRetainedCompletionConfig,
)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['ASSIGNED_BINDING', 'ASSIGNED_CAPABILITY', 'BINDING', 'CAPABILITY', 'EXTENSION']
