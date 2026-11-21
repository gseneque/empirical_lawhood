# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.matrix.causal_response.provider import CausalResponseMethodProvider


# Scientific registration and configuration.
from empirical_lawhood.execution.capabilities import CapabilityPermission


from dataclasses import replace

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.declaration_helpers import manifest, bundle
from empirical_lawhood.adapters.simulators.prepared_response.native_pair import NATIVE_PAIR_SCHEMA
from empirical_lawhood.adapters.simulators.prepared_response.source_outputs import PreparedNativeTaskResult
from empirical_lawhood.domains.matrix.causal_response.models import PROGRAMME
from empirical_lawhood.domains.matrix.causal_response.records import CausalResponseCommittedPrediction, CausalResponseProjectionConfig, CausalResponseEvaluationConfig, CausalResponseViewObservation, CausalResponseEvaluation

PROJECTION_CAPABILITY = manifest(
    "projection",
    CausalResponseProjectionConfig,
    CapabilityKind.TRANSFORM,
    (
        CausalResponseProjectionConfig.SCHEMA,
        PreparedNativeTaskResult.SCHEMA,
        CausalResponseCommittedPrediction.SCHEMA,
        NATIVE_PAIR_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (CausalResponseViewObservation.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    EvidenceCeiling.RESPONSE,
    OutcomeAccess.EVALUATION_SEALED,
    60,
    namespace=PROGRAMME,
    resources=ResourceBudget(1, 3 * 1024**3, 0, 60, 1024**3, 1024**2),
    implementation_id="causal-prediction-paired-native-contrast-projection",
    read_permission=(CapabilityPermission.READ_OUTCOME_VISIBLE if 'projection' == "evaluation" else CapabilityPermission.READ_SEALED_OUTCOMES),
    conformance_ids=("exact-frozen-source-qualification-roster", 'no-scientific-retry', 'separate-root-view-action-clocks'),
)
EVALUATION_CAPABILITY = manifest(
    "evaluation",
    CausalResponseEvaluationConfig,
    CapabilityKind.EVALUATOR,
    (
        CausalResponseEvaluationConfig.SCHEMA,
        CausalResponseViewObservation.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (
        CausalResponseEvaluation.SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
        ScientificAdjudicationRecord.SCHEMA,
    ),
    EvidenceCeiling.RESPONSE,
    OutcomeAccess.EVALUATION_REVEALED,
    60,
    namespace=PROGRAMME,
    resources=ResourceBudget(1, 3 * 1024**3, 0, 60, 256 * 1024**2, 1024**2),
    implementation_id="independent-context-exact-root-prediction-comparison",
    read_permission=(CapabilityPermission.READ_OUTCOME_VISIBLE if 'evaluation' == "evaluation" else CapabilityPermission.READ_SEALED_OUTCOMES),
    conformance_ids=("exact-frozen-source-qualification-roster", 'no-scientific-retry', 'separate-root-view-action-clocks'),
)
_projection, PROJECTION_COMPONENTS = bundle(
    "projection",
    ExtensionContributionKind.METHOD,
    PROJECTION_CAPABILITY,
    (CausalResponseProjectionConfig,),
    None,
    namespace=PROGRAMME,
)
_evaluation, EVALUATION_COMPONENTS = bundle(
    "evaluation",
    ExtensionContributionKind.METHOD,
    EVALUATION_CAPABILITY,
    (CausalResponseEvaluationConfig,),
    None,
    namespace=PROGRAMME,
)
_DISCOVERY_CONTRIBUTION = replace(
    _projection,
    contribution_id=f"extension-contribution.{PROGRAMME}.methods",
    capability_manifests=tuple(
        sorted(
            (*_projection.capability_manifests, *_evaluation.capability_manifests),
            key=lambda v: v.registry_id,
        )
    ),
    candidate_capability_registrations=tuple(
        sorted(
            (
                *_projection.candidate_capability_registrations,
                *_evaluation.candidate_capability_registrations,
            ),
            key=lambda v: v.manifest.registry_id,
        )
    ),
    profile_registrations=tuple(
        sorted(
            (*_projection.profile_registrations, *_evaluation.profile_registrations),
            key=lambda v: v.registration_id,
        )
    ),
    config_decoders=tuple(
        sorted(
            (*_projection.config_decoders, *_evaluation.config_decoders), key=lambda v: v.object_id
        )
    ),
    runtime_providers=tuple(
        sorted(
            (*_projection.runtime_providers, *_evaluation.runtime_providers),
            key=lambda v: v.object_id,
        )
    ),
)


# Executable roles.

from dataclasses import dataclass, replace

from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.declaration_helpers import executable

from empirical_lawhood.domains.matrix.causal_response.models import PROGRAMME
from empirical_lawhood.domains.matrix.causal_response.records import CausalResponseProjectionConfig, CausalResponseEvaluationConfig

PROJECTION_BINDING, EVALUATION_BINDING = tuple(
    replace(
        binding,
        issued_decoder_registrations=tuple(
            replace(d, maximum_payload_bytes=16 * 1024**2)
            for d in binding.issued_decoder_registrations
        ),
    )
    for binding in (
        executable(PROJECTION_CAPABILITY, PROJECTION_COMPONENTS, (CausalResponseProjectionConfig,)),
        executable(EVALUATION_CAPABILITY, EVALUATION_COMPONENTS, (CausalResponseEvaluationConfig,)),
    )
)


@dataclass(frozen=True, slots=True)
class CausalResponseMethodFactory:
    binding: ExecutableCapabilityBinding

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CausalResponseMethodProvider:
        from empirical_lawhood.domains.matrix.causal_response.provider import CausalResponseMethodProvider
        if platform_ports or len(records) != 1:
            raise ValueError("causal response prediction method factory requires one exact issued configuration")
        config = records[0]
        if self.binding == PROJECTION_BINDING and type(config) is CausalResponseProjectionConfig:
            return CausalResponseMethodProvider(registry, PROJECTION_CAPABILITY, config)
        if self.binding == EVALUATION_BINDING and type(config) is CausalResponseEvaluationConfig:
            return CausalResponseMethodProvider(registry, EVALUATION_CAPABILITY, config)
        raise ValueError("causal response prediction method factory changes its installed binding/configuration")


_EXECUTABLE_BINDINGS = tuple(sorted((PROJECTION_BINDING, EVALUATION_BINDING), key=lambda b: b.binding_id))
_EXECUTABLE_ID = f"executable-contribution.{PROGRAMME}.methods"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = tuple(
    CausalResponseMethodFactory(b) for b in _EXECUTABLE_BINDINGS
)
_RECORD_TYPES: tuple[type[CanonicalRecord], ...] = (CausalResponseProjectionConfig, CausalResponseEvaluationConfig)
_ISSUED_RECORD_TYPES = tuple(sorted(_RECORD_TYPES, key=lambda t: t.SCHEMA))


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EVALUATION_BINDING', 'EVALUATION_CAPABILITY', 'EXTENSION', 'PROJECTION_BINDING', 'PROJECTION_CAPABILITY']

_EXECUTION_CONTRIBUTION = EXTENSION.executable
