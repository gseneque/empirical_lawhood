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
from empirical_lawhood.domains.matrix.finite_response_law.assigned_native_records import FiniteResponseLawAssignedCalibrationViewObservation, FiniteResponseLawAssignedCalibrationNativeEvaluation, FiniteResponseLawAssignedEvaluationViewObservation, FiniteResponseLawAssignedEvaluationNativeCompletion
from empirical_lawhood.domains.matrix.finite_response_law.completion.contracts import FiniteResponseLawAssignedCalibrationRetainedConfig, FiniteResponseLawAssignedRetainedCompletionConfig, FiniteResponseLawRetainedCompletionConfig, PROSPECTIVE_EVALUATION_COMPLETION_PREFIX, PREFIX
from empirical_lawhood.domains.matrix.finite_response_law.fresh_contracts import FiniteResponseLawCalibrationConfig
from empirical_lawhood.domains.matrix.finite_response_law.assigned_contracts import FiniteResponseLawAssignedCalibrationConfig, FiniteResponseLawAssignedEvaluationConfig

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


def _assigned_completion(config, source, view, result, namespace, implementation_id):
    capability = manifest(
        "completion",
        config,
        CapabilityKind.EVALUATOR,
        (
            config.SCHEMA,
            source.SCHEMA,
            ObjectIdentity.SCHEMA,
            view.SCHEMA,
            CanonicalTaskReceipt.SCHEMA,
            result.SCHEMA,
            LinkedCampaignStageEnvelope.SCHEMA,
        ),
        (
            ObjectIdentity.SCHEMA,
            result.SCHEMA,
            LinkedCampaignStageEnvelope.SCHEMA,
            ScientificAdjudicationRecord.SCHEMA,
        ),
        EvidenceCeiling.MEASUREMENT,
        OutcomeAccess.EVALUATOR_REVEAL,
        180,
        namespace=namespace,
        resources=ResourceBudget(1, 1024**3, 0, 180, 96 * 1024**2, 16 * 1024**2),
        read_permission=CapabilityPermission.READ_SEALED_OUTCOMES,
        implementation_id=implementation_id,
        conformance_ids=(
            "exact-retained-projection-receipts",
            "no-native-recomputation",
            "separate-publication-evidence-classes",
        ),
    )
    capability = replace(capability,
        permissions=tuple(sorted((*capability.permissions, CapabilityPermission.REVEAL_OUTCOMES))))
    contribution, components = bundle("completion", ExtensionContributionKind.METHOD, capability,
        (config,), None, namespace=namespace)
    return capability, contribution, components


ASSIGNED_CAPABILITY, _assigned, ASSIGNED_COMPONENTS = _assigned_completion(
    FiniteResponseLawAssignedRetainedCompletionConfig, FiniteResponseLawAssignedEvaluationConfig,
    FiniteResponseLawAssignedEvaluationViewObservation, FiniteResponseLawAssignedEvaluationNativeCompletion,
    PROSPECTIVE_EVALUATION_COMPLETION_PREFIX, "assigned-retained-128-projection-custody-separate-adjudication")
CALIBRATION_CAPABILITY, _calibration, CALIBRATION_COMPONENTS = _assigned_completion(
    FiniteResponseLawAssignedCalibrationRetainedConfig, FiniteResponseLawAssignedCalibrationConfig,
    FiniteResponseLawAssignedCalibrationViewObservation, FiniteResponseLawAssignedCalibrationNativeEvaluation,
    FiniteResponseLawAssignedCalibrationRetainedConfig.PREFIX_ID, "assigned-calibration-64-retained-projection-custody")
_parts = (_DISCOVERY_CONTRIBUTION, _assigned, _calibration)
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
from empirical_lawhood.domains.matrix.finite_response_law.completion.contracts import FiniteResponseLawAssignedCalibrationRetainedConfig, FiniteResponseLawAssignedRetainedCompletionConfig, FiniteResponseLawRetainedCompletionConfig, PREFIX

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

CALIBRATION_BINDING = replace(
    executable(CALIBRATION_CAPABILITY, CALIBRATION_COMPONENTS, (FiniteResponseLawAssignedCalibrationRetainedConfig,)),
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
        choices = {
            BINDING: (CAPABILITY, FiniteResponseLawRetainedCompletionConfig),
            ASSIGNED_BINDING: (ASSIGNED_CAPABILITY, FiniteResponseLawAssignedRetainedCompletionConfig),
            CALIBRATION_BINDING: (CALIBRATION_CAPABILITY, FiniteResponseLawAssignedCalibrationRetainedConfig),
        }
        if self.binding not in choices:
            raise ValueError("Unregistered retained completion binding")
        manifest, config_type = choices[self.binding]
        if (len(records) != 1
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
    FiniteResponseLawRetainedCompletionFactory(CALIBRATION_BINDING),
)
_ISSUED_RECORD_TYPES = (
    FiniteResponseLawAssignedCalibrationRetainedConfig,
    FiniteResponseLawRetainedCompletionConfig,
    FiniteResponseLawAssignedRetainedCompletionConfig,
)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['ASSIGNED_BINDING', 'ASSIGNED_CAPABILITY', 'BINDING', 'CAPABILITY', 'CALIBRATION_BINDING', 'CALIBRATION_CAPABILITY', 'EXTENSION']
