# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.adapters.simulators.causal_response.provider import CausalResponseSourceProvider


# Scientific registration and configuration.
from empirical_lawhood.execution.capabilities import CapabilityPermission


from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.design.source_qualification import FreshSourceQualificationExperiment
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.source_qualification import FreshSourceQualificationSubstrateBinding
from empirical_lawhood.execution.declaration_helpers import manifest, bundle
from empirical_lawhood.adapters.simulators.prepared_response.native_pair import NATIVE_PAIR_SCHEMA
from empirical_lawhood.adapters.simulators.prepared_response.source_outputs import PreparedNativeTaskResult
from empirical_lawhood.domains.matrix.causal_response.records import CausalResponseCommittedPrediction
from empirical_lawhood.domains.matrix.causal_response.contracts import CausalResponseNativeConfig

NAMESPACE = "causal-response-prediction"
SOURCE_RECORDS = (
    CausalResponseNativeConfig,
    FreshSourceQualificationExperiment,
    FreshSourceQualificationSubstrateBinding,
)
SOURCE_CAPABILITY = manifest(
    "source",
    CausalResponseNativeConfig,
    CapabilityKind.SIMULATOR,
    (
        CausalResponseNativeConfig.SCHEMA,
        PreparedNativeTaskResult.SCHEMA,
        CausalResponseCommittedPrediction.SCHEMA,
        NATIVE_PAIR_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (
        PreparedNativeTaskResult.SCHEMA,
        CausalResponseCommittedPrediction.SCHEMA,
        NATIVE_PAIR_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    EvidenceCeiling.MEASUREMENT,
    OutcomeAccess.EVALUATION_SEALED,
    1800,
    namespace=NAMESPACE,
    resources=ResourceBudget(1, 768 * 1024**2, 0, 1800, 32 * 1024**2, 20 * 1024**2),
    implementation_id="prepared-mechanics-with-committed-causal-handoff-predictions",
    conformance_ids=(
        "exact-causal-response-prediction-native-census",
        "forecast-before-future-receipt",
        "paired-independent-future-innovations",
    ),
    read_permission=(CapabilityPermission.READ_OUTCOME_VISIBLE if 'source' == "evaluation" else CapabilityPermission.READ_SEALED_OUTCOMES),
)
_DISCOVERY_CONTRIBUTION, SOURCE_COMPONENTS = bundle(
    "source",
    ExtensionContributionKind.SOURCE,
    SOURCE_CAPABILITY,
    (CausalResponseNativeConfig,),
    NATIVE_PAIR_SCHEMA,
    namespace=NAMESPACE,
)


# Executable roles.

from dataclasses import dataclass, replace
from math import ceil
from typing import cast
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.source_qualification import FreshSourceQualificationExperiment
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort, ExecutableRecordTypeBinding
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.plans import BarrierKind, ProtocolStepTemplate, ProtocolTemplate, ScientificStage
from empirical_lawhood.execution.source_qualification import FreshSourceQualificationSubstrateBinding, derive_source_qualification_topology
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.adapters.simulators.response_geometry_prospective.extension import ASSAY_SOURCE_BINDING as SHARED_QUALIFICATION_CODEC_OWNER
from empirical_lawhood.execution.protocol_helpers import capability_config_ref as _config_ref, protocol_outputs as _outputs
from empirical_lawhood.domains.matrix.causal_response.extension import PROJECTION_CAPABILITY, EVALUATION_CAPABILITY
from empirical_lawhood.domains.matrix.causal_response.records import CausalResponseProjectionConfig, CausalResponseEvaluationConfig, CausalResponseViewObservation, CausalResponseEvaluation, CausalResponseCommittedPrediction
from empirical_lawhood.adapters.simulators.prepared_response.source_outputs import PreparedNativeTaskResult
from empirical_lawhood.adapters.simulators.prepared_response.native_pair import NATIVE_PAIR_SCHEMA
from empirical_lawhood.domains.matrix.causal_response.contracts import CausalResponseNativeConfig, native_invocations

from empirical_lawhood.domains.matrix.causal_response.roster import REFERENCE_CLOCK, NATIVE_RECEIVERS, native_declarations, substrate_binding

_BASE = executable(SOURCE_CAPABILITY, SOURCE_COMPONENTS, (CausalResponseNativeConfig,))
_BASE = replace(
    _BASE,
    issued_decoder_registrations=tuple(
        replace(d, maximum_payload_bytes=16 * 1024**2)
        for d in _BASE.issued_decoder_registrations
    ),
)
_SHARED_SCHEMAS = (
    FreshSourceQualificationExperiment.SCHEMA,
    FreshSourceQualificationSubstrateBinding.SCHEMA,
)
_SHARED_COMPONENTS = tuple(
    component
    for component in SHARED_QUALIFICATION_CODEC_OWNER.discovery_components
    if component.input_schema_ids in tuple((schema,) for schema in _SHARED_SCHEMAS)
    and component.output_schema_ids == component.input_schema_ids
)
SOURCE_BINDING = replace(
    _BASE,
    discovery_components=tuple(
        sorted(
            (*_BASE.discovery_components, *_SHARED_COMPONENTS),
            key=lambda value: value.registration_id,
        )
    ),
    accepted_config_types=tuple(
        sorted(
            (
                ExecutableRecordTypeBinding(value.SCHEMA, value.VERSION)
                for value in SOURCE_RECORDS
            ),
            key=lambda value: value.type_id,
        )
    ),
    required_issued_payload_schemas=tuple(
        sorted(value.SCHEMA for value in SOURCE_RECORDS)
    ),
    codec_registration_identities=tuple(
        sorted(
            (
                *_BASE.codec_registration_identities,
                *(
                    ObjectIdentity.from_record(value.registration_id, value)
                    for value in _SHARED_COMPONENTS
                ),
            ),
            key=lambda value: value.object_id,
        )
    ),
    issued_decoder_registrations=tuple(
        sorted(
            (
                *_BASE.issued_decoder_registrations,
                *(
                    value
                    for value in SHARED_QUALIFICATION_CODEC_OWNER.issued_decoder_registrations
                    if value.payload_schema in _SHARED_SCHEMAS
                ),
            ),
            key=lambda value: value.registration_id,
        )
    ),
)


def validate_source_records(
    spec: CausalResponseNativeConfig,
    carrier: FreshSourceQualificationExperiment,
    association: FreshSourceQualificationSubstrateBinding,
) -> None:
    binding = ObjectIdentity.from_record(SOURCE_BINDING.binding_id, SOURCE_BINDING)
    source_owner = ObjectIdentity.from_record(
        SOURCE_CAPABILITY.capability_key, SOURCE_CAPABILITY
    )
    declarations = native_declarations(spec)
    if (
        spec.recipe.native_implementation != source_owner
        or carrier.source_capability != source_owner
        or carrier.source_config != ObjectIdentity.from_record(spec.spec_id, spec)
        or (carrier.physical_units, carrier.segments, carrier.views)
        != (declarations.units, declarations.segments, declarations.views)
        or carrier.receiver_ids != NATIVE_RECEIVERS
        or carrier.clock_ids != (REFERENCE_CLOCK,)
        or not carrier.extension_set_id.endswith(".source-qualification")
        or carrier.evaluator_task_id
        != f"{carrier.extension_set_id.removesuffix('.source-qualification')}.evaluate"
        or association != substrate_binding(spec, carrier, binding)
    ):
        raise ValueError(
            "causal response prediction source records change native units/actions/views/clock/provider lineage"
        )


@dataclass(frozen=True, slots=True)
class CausalResponseSourceFactory:
    binding: ExecutableCapabilityBinding = SOURCE_BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CausalResponseSourceProvider:
        from empirical_lawhood.adapters.simulators.causal_response.provider import CausalResponseSourceProvider
        by_type = {type(value): value for value in records}
        if (
            self.binding != SOURCE_BINDING
            or platform_ports
            or len(records) != 3
            or set(by_type) != set(SOURCE_RECORDS)
        ):
            raise ValueError(
                "causal response prediction source factory requires its three exact issued records"
            )
        spec = cast(CausalResponseNativeConfig, by_type[CausalResponseNativeConfig])
        carrier = cast(
            FreshSourceQualificationExperiment, by_type[FreshSourceQualificationExperiment]
        )
        association = cast(
            FreshSourceQualificationSubstrateBinding,
            by_type[FreshSourceQualificationSubstrateBinding],
        )
        validate_source_records(spec, carrier, association)
        return CausalResponseSourceProvider(registry, SOURCE_CAPABILITY, spec)

    def expand_parameterised_protocol(
        self, *, records: tuple[CanonicalRecord, ...], template: ProtocolTemplate
    ) -> ProtocolTemplate:
        by_type = {type(value): value for value in records}
        if (
            self.binding != SOURCE_BINDING
            or len(records) != 5
            or set(by_type)
            != {*SOURCE_RECORDS, CausalResponseProjectionConfig, CausalResponseEvaluationConfig}
        ):
            raise ValueError(
                "causal response prediction expansion requires its exact source/carrier/method records"
            )
        spec = cast(CausalResponseNativeConfig, by_type[CausalResponseNativeConfig])
        carrier = cast(
            FreshSourceQualificationExperiment, by_type[FreshSourceQualificationExperiment]
        )
        association = cast(
            FreshSourceQualificationSubstrateBinding,
            by_type[FreshSourceQualificationSubstrateBinding],
        )
        projection = cast(CausalResponseProjectionConfig, by_type[CausalResponseProjectionConfig])
        evaluation = cast(CausalResponseEvaluationConfig, by_type[CausalResponseEvaluationConfig])
        validate_source_records(spec, carrier, association)
        if (
            projection.native_spec != spec
            or evaluation.projection != projection
            or carrier.projection_config
            != ObjectIdentity.from_record(projection.config_id, projection)
            or carrier.evaluator_config
            != ObjectIdentity.from_record(evaluation.config_id, evaluation)
            or carrier.projection_capability
            != ObjectIdentity.from_record(
                PROJECTION_CAPABILITY.capability_key, PROJECTION_CAPABILITY
            )
            or carrier.evaluator_capability
            != ObjectIdentity.from_record(
                EVALUATION_CAPABILITY.capability_key, EVALUATION_CAPABILITY
            )
        ):
            raise ValueError(
                "causal response prediction expansion changes its exact projection/evaluation owners"
            )
        source_id = ObjectIdentity.from_record(spec.spec_id, spec)
        owners = {
            ObjectIdentity.from_record(manifest.capability_key, manifest): (
                manifest,
                config,
                identity,
            )
            for manifest, config, identity in (
                (SOURCE_CAPABILITY, spec, source_id),
                (PROJECTION_CAPABILITY, projection, carrier.projection_config),
                (EVALUATION_CAPABILITY, evaluation, carrier.evaluator_config),
            )
        }
        outputs = {
            ScientificStage.PREPARE: _outputs(
                (
                    ("native-result", PreparedNativeTaskResult.SCHEMA),
                    ("committed-prediction", CausalResponseCommittedPrediction.SCHEMA),
                    ("stage-envelope", LinkedCampaignStageEnvelope.SCHEMA),
                ),
                ("native-observations", NATIVE_PAIR_SCHEMA),
            ),
            ScientificStage.TRANSFORM: _outputs(
                (
                    ("view-report", CausalResponseViewObservation.SCHEMA),
                    ("stage-envelope", LinkedCampaignStageEnvelope.SCHEMA),
                )
            ),
            ScientificStage.EVALUATE: _outputs(
                (
                    ("evaluation", CausalResponseEvaluation.SCHEMA),
                    ("stage-envelope", LinkedCampaignStageEnvelope.SCHEMA),
                    ("scientific-adjudication", ScientificAdjudicationRecord.SCHEMA),
                )
            ),
        }
        native = {task.task_id: task for task in native_invocations(spec)}
        stages = derive_source_qualification_topology(carrier).stages
        by_id = {stage.task_id: stage for stage in stages}
        steps = []
        for stage in stages:
            manifest, config, identity = owners[stage.owner]
            if stage.config != identity:
                raise ValueError("causal response prediction topology changes its frozen stage config")
            scan = len(config.canonical_bytes()) * (
                2
                if stage.stage is ScientificStage.PREPARE
                and not stage.dependency_task_ids
                else 1
            )
            scan += sum(
                owners[by_id[key].owner][0].resource_ceiling.output_bytes
                for key in stage.dependency_task_ids
            )
            if scan > manifest.resource_ceiling.source_scan_bytes:
                raise ValueError(
                    "causal response prediction complete predecessor roster exceeds its installed scan ceiling"
                )
            # Conservative inherited numerical cost; complete route/resource admission is separate.
            wall = (
                ceil(2 + native[stage.task_id].maximum_native_updates * 0.004)
                if stage.stage is ScientificStage.PREPARE
                else manifest.resource_ceiling.wall_time_seconds
            )
            steps.append(
                ProtocolStepTemplate(
                    stage.task_id,
                    stage.stage,
                    manifest.capability_key,
                    manifest.capability_version,
                    _config_ref(config, identity, manifest),
                    stage.dependency_task_ids,
                    outputs[stage.stage],
                    manifest.permissions,
                    OutcomeAccess.EVALUATION_REVEALED
                    if stage.stage is ScientificStage.EVALUATE
                    else OutcomeAccess.EVALUATION_SEALED,
                    VisibilityCeiling.OUTCOME_VISIBLE
                    if stage.stage is ScientificStage.EVALUATE
                    else VisibilityCeiling.DEVELOPMENT_ONLY,
                    replace(
                        manifest.resource_ceiling,
                        source_scan_bytes=scan,
                        wall_time_seconds=wall,
                    ),
                    (),
                    BarrierKind.REVEAL
                    if stage.stage is ScientificStage.EVALUATE
                    else BarrierKind.FREEZE
                    if stage.stage is ScientificStage.TRANSFORM
                    else BarrierKind.NONE,
                    1,
                    (
                        f"{carrier.evaluator_task_id.removesuffix('.evaluate')}.single-terminal",
                    )
                    if stage.stage is ScientificStage.EVALUATE
                    else (f"custody.{stage.task_id}",),
                )
            )
        if len(steps) != 3073:
            raise ValueError(
                "causal response prediction expansion changes its complete production task census"
            )
        return replace(
            template,
            template_id=f"{template.template_id}.{carrier.fingerprint()[:16]}",
            steps=tuple(sorted(steps, key=lambda value: value.step_id)),
            requires_model_set=False,
            requests_controller=False,
            nonactuating=True,
        )


_EXECUTABLE_ID = "executable-contribution.causal-response-prediction.source"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (CausalResponseSourceFactory(),)
_ISSUED_RECORD_TYPES = (CausalResponseNativeConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION', 'NAMESPACE', 'SOURCE_BINDING', 'SOURCE_CAPABILITY']
