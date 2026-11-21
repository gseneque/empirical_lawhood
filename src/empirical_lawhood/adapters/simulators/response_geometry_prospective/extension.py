# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.adapters.simulators.response_geometry_prospective.provider import ResponseGeometryAssaySourceProvider


# Scientific registration and configuration.

from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.source_qualification import FreshSourceQualificationExperiment
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.source_qualification import FreshSourceQualificationSubstrateBinding
from empirical_lawhood.domains.matrix.six_matrix_response.response_qualification import ResponseGeometryAssayNativeConfig, ResponseGeometryAssayNativeSegmentResult
from empirical_lawhood.domains.matrix.six_matrix_response.response_dynamics import ASSAY_HDF5_SCHEMA

from empirical_lawhood.adapters.simulators.response_geometry_prospective.discovery import bundle, manifest

SOURCE_RECORDS: tuple[type[CanonicalRecord], ...] = (
    ResponseGeometryAssayNativeConfig,
    FreshSourceQualificationExperiment,
    FreshSourceQualificationSubstrateBinding,
)
ASSAY_SOURCE_CAPABILITY = manifest(
    "source",
    ResponseGeometryAssayNativeConfig,
    CapabilityKind.SIMULATOR,
    (
        ResponseGeometryAssayNativeConfig.SCHEMA,
        ResponseGeometryAssayNativeSegmentResult.SCHEMA,
        ASSAY_HDF5_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (ResponseGeometryAssayNativeSegmentResult.SCHEMA, ASSAY_HDF5_SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    EvidenceCeiling.MEASUREMENT,
    OutcomeAccess.EVALUATION_SEALED,
    1800,
)
_DISCOVERY_CONTRIBUTION, ASSAY_SOURCE_COMPONENTS = bundle(
    "source", ExtensionContributionKind.SOURCE, ASSAY_SOURCE_CAPABILITY, SOURCE_RECORDS, ASSAY_HDF5_SCHEMA
)


# Executable roles.

from empirical_lawhood.execution.protocol_helpers import capability_config_ref as _config_ref, protocol_outputs as _outputs

from dataclasses import dataclass, replace
from math import ceil
from typing import cast

from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.design.source_qualification import FreshSourceQualificationExperiment
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.plans import BarrierKind, ProtocolStepTemplate, ProtocolTemplate, ScientificStage
from empirical_lawhood.execution.source_qualification import FreshSourceQualificationSubstrateBinding, derive_source_qualification_topology
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.domains.matrix.six_matrix_response.response_qualification import ResponseGeometryAssayNativeConfig, ResponseGeometryAssayNativeSegmentResult, assay_segments
from empirical_lawhood.domains.matrix.six_matrix_response.response_dynamics import ASSAY_HDF5_SCHEMA

from empirical_lawhood.adapters.simulators.response_geometry_prospective.discovery import executable



ASSAY_SOURCE_BINDING = executable(ASSAY_SOURCE_CAPABILITY, ASSAY_SOURCE_COMPONENTS, SOURCE_RECORDS)


@dataclass(frozen=True, slots=True)
class ResponseGeometryAssaySourceProviderFactory:
    binding: ExecutableCapabilityBinding = ASSAY_SOURCE_BINDING

    def expand_parameterised_protocol(
        self, *, records: tuple[CanonicalRecord, ...], template: ProtocolTemplate
    ) -> ProtocolTemplate:
        from empirical_lawhood.adapters.simulators.response_geometry_prospective.provider import validate_response_geometry_assay_native_roster
        from empirical_lawhood.domains.matrix.response_geometry_prospective.extension import ASSAY_PROJECTION_CAPABILITY, ASSAY_EVALUATION_CAPABILITY
        from empirical_lawhood.domains.matrix.response_geometry_prospective.projection import ASSAY_DIAGNOSTICS_SCHEMA
        from empirical_lawhood.domains.matrix.response_geometry_prospective.qualification import ResponseGeometryAssayProjectionConfig, ResponseGeometryAssayEvaluationConfig, ResponseGeometryAssayViewReport, ResponseGeometryAssayEvaluation

        by_type = {type(value): value for value in records}
        if (
            len(by_type) != 5
            or len(records) != 5
            or set(by_type) != {*SOURCE_RECORDS, ResponseGeometryAssayProjectionConfig, ResponseGeometryAssayEvaluationConfig}
        ):
            raise ValueError("assay expansion requires its five exact issued config/carrier records")
        carrier = cast(FreshSourceQualificationExperiment, by_type[FreshSourceQualificationExperiment])
        association = cast(
            FreshSourceQualificationSubstrateBinding, by_type[FreshSourceQualificationSubstrateBinding]
        )
        source = cast(ResponseGeometryAssayNativeConfig, by_type[ResponseGeometryAssayNativeConfig])
        projection = cast(ResponseGeometryAssayProjectionConfig, by_type[ResponseGeometryAssayProjectionConfig])
        evaluation = cast(ResponseGeometryAssayEvaluationConfig, by_type[ResponseGeometryAssayEvaluationConfig])
        source_identity = ObjectIdentity.from_record(source.config_id, source)
        projection_identity = ObjectIdentity.from_record(projection.config_id, projection)
        evaluation_identity = ObjectIdentity.from_record(evaluation.config_id, evaluation)
        if (
            carrier.source_config != source_identity
            or carrier.projection_config != projection_identity
            or carrier.evaluator_config != evaluation_identity
            or projection.source_config != source_identity
            or evaluation.projection_config != projection_identity
            or association.qualification_carrier
            != ObjectIdentity.from_record(carrier.extension_set_id, carrier)
            or association.source_config != source_identity
            or association.substrate.installed_executable_binding
            != ObjectIdentity.from_record(self.binding.binding_id, self.binding)
        ):
            raise ValueError("assay expansion changes native/config/owner lineage")
        native = {segment.task_id: segment for segment in assay_segments()}
        validate_response_geometry_assay_native_roster(source, carrier)
        owners = {
            ObjectIdentity.from_record(manifest.capability_key, manifest): (
                manifest,
                config,
                identity,
            )
            for manifest, config, identity in (
                (ASSAY_SOURCE_CAPABILITY, source, source_identity),
                (ASSAY_PROJECTION_CAPABILITY, projection, projection_identity),
                (ASSAY_EVALUATION_CAPABILITY, evaluation, evaluation_identity),
            )
        }
        outputs = {
            ScientificStage.PREPARE: _outputs(
                (
                    ("native-result", ResponseGeometryAssayNativeSegmentResult.SCHEMA),
                    ("stage-envelope", LinkedCampaignStageEnvelope.SCHEMA),
                ),
                ("native-observations", ASSAY_HDF5_SCHEMA),
            ),
            ScientificStage.TRANSFORM: _outputs(
                (
                    ("view-report", ResponseGeometryAssayViewReport.SCHEMA),
                    ("stage-envelope", LinkedCampaignStageEnvelope.SCHEMA),
                ),
                ("diagnostics", ASSAY_DIAGNOSTICS_SCHEMA),
            ),
            ScientificStage.EVALUATE: _outputs(
                (
                    ("evaluation", ResponseGeometryAssayEvaluation.SCHEMA),
                    ("stage-envelope", LinkedCampaignStageEnvelope.SCHEMA),
                    ("scientific-adjudication", ScientificAdjudicationRecord.SCHEMA),
                )
            ),
        }
        stages = derive_source_qualification_topology(carrier).stages
        stage_by_id = {stage.task_id: stage for stage in stages}
        config_sizes = {
            identity: len(config.canonical_bytes()) for _, config, identity in owners.values()
        }
        steps = []
        for stage in stages:
            if stage.owner not in owners:
                raise ValueError("assay expansion selects another scientific owner")
            manifest, config, identity = owners[stage.owner]
            if stage.config != identity:
                raise ValueError("assay expansion stage config differs")
            # An unmeasured duration forecast for authoring authoring metadata:
            # 30 ms/native update plus 2 s per source segment, 120 s/projection.
            # The compiler/runtime-owner execution envelope has no elapsed-time stop.
            seconds = (
                ceil(2 + native[stage.task_id].native_updates * 0.03)
                if stage.stage is ScientificStage.PREPARE
                else 120
            )
            # The compiler supplies the capability config. Preparation prefixes
            # also retain the graph's explicit MODEL config role. Charge both reads,
            # plus each predecessor's whole output allocation exactly once.
            input_bytes = (
                2 if stage.stage is ScientificStage.PREPARE and not stage.dependency_task_ids else 1
            ) * config_sizes[identity]
            input_bytes += sum(
                owners[stage_by_id[dependency].owner][0].resource_ceiling.output_bytes
                for dependency in stage.dependency_task_ids
            )
            if input_bytes > manifest.resource_ceiling.source_scan_bytes:
                raise ValueError("assay input roster exceeds its installed scan ceiling")
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
                    VisibilityCeiling.PROSPECTIVE,
                    replace(
                        manifest.resource_ceiling,
                        wall_time_seconds=seconds,
                        source_scan_bytes=input_bytes,
                    ),
                    (),
                    BarrierKind.REVEAL
                    if stage.stage is ScientificStage.EVALUATE
                    else BarrierKind.FREEZE
                    if stage.stage is ScientificStage.TRANSFORM
                    else BarrierKind.NONE,
                    1,
                    ("response-geometry-assay.single-terminal",)
                    if stage.stage is ScientificStage.EVALUATE
                    else (f"custody.{stage.task_id}",),
                )
            )
        if len(steps) != 865:
            raise ValueError("assay expansion changes the complete 865-task production topology")
        return replace(
            template,
            template_id=f"{template.template_id}.{carrier.fingerprint()[:16]}",
            steps=tuple(steps),
            requires_model_set=False,
            requests_controller=False,
            nonactuating=True,
        )

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> ResponseGeometryAssaySourceProvider:
        from empirical_lawhood.adapters.simulators.response_geometry_prospective.provider import ResponseGeometryAssaySourceProvider
        by_type = {type(value): value for value in records}
        if platform_ports or len(records) != 3 or set(by_type) != set(SOURCE_RECORDS):
            raise ValueError("assay native provider requires its three exact issued records")
        return ResponseGeometryAssaySourceProvider(
            registry,
            ASSAY_SOURCE_CAPABILITY,
            cast(ResponseGeometryAssayNativeConfig, by_type[ResponseGeometryAssayNativeConfig]),
            cast(FreshSourceQualificationExperiment, by_type[FreshSourceQualificationExperiment]),
            cast(
                FreshSourceQualificationSubstrateBinding,
                by_type[FreshSourceQualificationSubstrateBinding],
            ),
            ObjectIdentity.from_record(self.binding.binding_id, self.binding),
        )


_EXECUTABLE_ID = "executable-contribution.response-geometry-assay.source"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (ResponseGeometryAssaySourceProviderFactory(),)
_ISSUED_RECORD_TYPES = tuple(sorted(SOURCE_RECORDS, key=lambda value: value.SCHEMA))


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['ASSAY_SOURCE_BINDING', 'ASSAY_SOURCE_CAPABILITY', 'EXTENSION', '_config_ref', '_outputs']
