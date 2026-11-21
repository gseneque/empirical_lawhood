"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from empirical_lawhood.domains.fusion.gym_torax_native.projection import project_gym_torax_episode
from dataclasses import fields
from typing import cast
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.identification_evidence import ObservationDisposition
from empirical_lawhood.design.linked_campaign import LinkedCampaignStageRole
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityManifest, CapabilityRegistry
from empirical_lawhood.execution.execution import RunnerResult, TaskContext, TaskOutputPayload, TaskRunner
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignDisposition, LinkedCampaignStageEnvelope
from empirical_lawhood.execution.plans import ProtocolExecutionPlan
from empirical_lawhood.execution.providers import CampaignRuntimeProvider, CapabilityOutputSemanticContract, ExternalInputPayload
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataNativeEpisode
from empirical_lawhood.domains.fusion.gym_torax_native.source_contracts import GYM_TORAX_CANONICAL_MEDIA_TYPE

from empirical_lawhood.domains.fusion.gym_torax_native.projection import (
    GymToraxNativeProjection as _science_GymToraxNativeProjection,
    GymToraxParameterisedProjectionConfig as _science_GymToraxParameterisedProjectionConfig,
)

GYM_TORAX_PARAMETERISED_PROJECTION_KEY = 'gym-torax-native.parameterised-view-projection'

GYM_TORAX_PARAMETERISED_PROJECTION_VERSION = "1.0.0"

_MAXIMUM_CANONICAL_INPUT_BYTES = 512 * 1024**2

class _GymToraxProjectionRunner:
    def __init__(
        self,
        *,
        manifest: CapabilityManifest,
        config: _science_GymToraxParameterisedProjectionConfig,
    ) -> None:
        self.manifest = manifest
        self._config = config

    def execute(self, context: TaskContext) -> RunnerResult:
        records = _decode_inputs(
            context,
            (
                _science_GymToraxParameterisedProjectionConfig,
                GymToraxFieldMetadataNativeEpisode,
                LinkedCampaignStageEnvelope,
            ),
        )
        config = cast(
            _science_GymToraxParameterisedProjectionConfig,
            records[_science_GymToraxParameterisedProjectionConfig.SCHEMA],
        )
        episode = cast(GymToraxFieldMetadataNativeEpisode, records[GymToraxFieldMetadataNativeEpisode.SCHEMA])
        upstream = cast(
            LinkedCampaignStageEnvelope,
            records[LinkedCampaignStageEnvelope.SCHEMA],
        )
        if config != self._config:
            raise ValueError("Gym projection task received a substituted config")
        prefix = f"{config.projection_task_prefix}."
        if not context.task_id.startswith(prefix):
            raise ValueError("Gym projection task identity differs")
        view = config.view(context.task_id[len(prefix) :])
        episode_identity = ObjectIdentity.from_record(episode.episode_id, episode)
        if (
            upstream.role is not LinkedCampaignStageRole.SOURCE_MATERIALIZATION
            or upstream.disposition is not LinkedCampaignDisposition.SUPPORTED
            or upstream.scientific_product != episode_identity
        ):
            raise ValueError("Gym projection input changes acquisition/view lineage")
        projection = project_gym_torax_episode(view, episode)
        envelope = LinkedCampaignStageEnvelope(
            envelope_id=f"stage-envelope.{context.task_id}",
            role=LinkedCampaignStageRole.EVIDENCE_PROJECTION,
            disposition=(
                LinkedCampaignDisposition.SUPPORTED
                if projection.projection_disposition is ObservationDisposition.COMPLETE
                else LinkedCampaignDisposition.UNEVALUABLE
            ),
            scientific_product=ObjectIdentity.from_record(projection.projection_id, projection),
            reason_codes=projection.reason_codes,
        )
        outputs = {value.SCHEMA: value for value in (projection, envelope)}
        if set(outputs) != {value.payload_schema for value in context.output_ports}:
            raise ValueError("Gym projection output contract differs")
        return RunnerResult(
            outputs=tuple(
                TaskOutputPayload(port.output_id, outputs[port.payload_schema].canonical_bytes())
                for port in context.output_ports
            ),
            checks=(
                ReceiptCheck("one-view-no-reexecution", True, ()),
                ReceiptCheck("native-status-axes-preserved", True, ()),
                ReceiptCheck("no-adapter-scientific-verdict", True, ()),
            ),
        )

def _decode_inputs(
    context: TaskContext,
    record_types: tuple[type[CanonicalRecord], ...],
) -> dict[str, CanonicalRecord]:
    by_schema = {value.SCHEMA: value for value in record_types}
    decoded: dict[str, CanonicalRecord] = {}
    for port in context.input_ports:
        record_type = by_schema.get(port.payload_schema)
        try:
            if record_type is None:
                continue
            payload = port.read(port.size_bytes + 1)
            if len(payload) != port.size_bytes or port.read(1):
                raise ValueError("Gym projection input size differs")
            value = decode_canonical_bytes(
                payload,
                record_type,
                maximum_bytes=_MAXIMUM_CANONICAL_INPUT_BYTES,
            )
            if value.SCHEMA in decoded:
                raise ValueError("Gym projection received duplicate typed input")
            decoded[value.SCHEMA] = value
        finally:
            port.close()
    if set(decoded) != set(by_schema):
        raise ValueError("Gym projection input roster differs")
    return decoded

class GymToraxParameterisedProjectionProvider(CampaignRuntimeProvider):
    def __init__(
        self,
        *,
        registry: CapabilityRegistry,
        manifest: CapabilityManifest,
        config: _science_GymToraxParameterisedProjectionConfig,
    ) -> None:
        if registry.resolve(manifest.capability_key, manifest.capability_version) != manifest:
            raise ValueError("Gym projection manifest differs from installed registry")
        self.registry = registry
        self.registry_sha256 = registry.fingerprint()
        self.manifest = manifest
        self.config = config
        self.capability_count = 1

    def runners(
        self,
        registry: CapabilityRegistry,
        source_records: tuple[CanonicalRecord, ...] = (),
    ) -> tuple[TaskRunner, ...]:
        if registry != self.registry or source_records:
            raise ValueError("Gym projection runner inputs differ")
        return (
            cast(
                TaskRunner,
                _GymToraxProjectionRunner(manifest=self.manifest, config=self.config),
            ),
        )

    def external_inputs(
        self,
        plan: ProtocolExecutionPlan,
        source_records: tuple[CanonicalRecord, ...] = (),
    ) -> tuple[ExternalInputPayload, ...]:
        if plan.registry_sha256 != self.registry_sha256 or source_records:
            raise ValueError("Gym projection plan/source inputs differ")
        tasks = tuple(
            value
            for value in plan.tasks
            if value.capability.capability_key == self.manifest.capability_key
        )
        expected_task_ids = {
            f"{self.config.projection_task_prefix}.{value.view_id}" for value in self.config.views
        }
        if {value.task_id for value in tasks} != expected_task_ids:
            raise ValueError("Gym projection task roster differs from config")
        specs = {
            value.logical_artifact_id: value
            for task in tasks
            for value in task.external_inputs
            if value.expected_payload_schema == self.config.SCHEMA
        }
        if (
            len(specs) != 1
            or next(iter(specs.values())).expected_content_sha256 != self.config.fingerprint()
        ):
            raise ValueError("Gym projection tasks lack the exact shared config")
        parent = ArtifactLineageParent(
            ObjectIdentity.from_record(self.config.config_id, self.config),
            VisibilityCeiling.PROSPECTIVE,
            OutcomeAccess.OUTCOME_BLIND,
        )
        return (
            ExternalInputPayload.from_bytes(
                logical_artifact_id=next(iter(specs)),
                payload_schema=self.config.SCHEMA,
                profile=ArtifactProfile.CANONICAL_JSON,
                media_type=GYM_TORAX_CANONICAL_MEDIA_TYPE,
                payload=self.config.canonical_bytes(),
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                outcome_access=OutcomeAccess.OUTCOME_BLIND,
                parent_visibility_ceilings=(parent.visibility_ceiling,),
                lineage_parents=(parent,),
                logical_content_sha256=self.config.fingerprint(),
            ),
        )

    def output_semantic_contracts(
        self,
        registry: CapabilityRegistry,
        execution_plan: ProtocolExecutionPlan | None = None,
    ) -> tuple[CapabilityOutputSemanticContract, ...]:
        if registry != self.registry:
            raise ValueError("Gym projection semantic registry differs")
        del execution_plan
        types = {
            _science_GymToraxNativeProjection.SCHEMA: _science_GymToraxNativeProjection,
            LinkedCampaignStageEnvelope.SCHEMA: LinkedCampaignStageEnvelope,
        }
        return tuple(
            CapabilityOutputSemanticContract.from_manifest(
                self.manifest,
                payload_schema=schema,
                profile=ArtifactProfile.CANONICAL_JSON,
                top_level_keys=("schema", "value", "version"),
                value_keys=tuple(sorted(value.name for value in fields(types[schema]))),
            )
            for schema in self.manifest.output_schema_ids
        )

    def scientific_adjudication_contract(
        self,
        registry: CapabilityRegistry,
        execution_plan: ProtocolExecutionPlan | None = None,
    ) -> None:
        if registry != self.registry:
            raise ValueError("Gym projection adjudication registry differs")
        del execution_plan
        return None
