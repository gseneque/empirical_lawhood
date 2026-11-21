"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from pathlib import Path
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.response_experiment import ResponseExperimentExtensionSet
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityManifest
from empirical_lawhood.execution.execution import StreamingOutputEmitter, TaskContext
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignDisposition, LinkedCampaignStageEnvelope
from empirical_lawhood.execution.response_experiment_binding import materialise_native_execution_request
from empirical_lawhood.design.linked_campaign import LinkedCampaignStageRole
from empirical_lawhood.execution.response_experiment_ports import ResponseSubstrateBinding, SourceReadinessCheck, SourceReadinessDisposition
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataNativeEpisode
from empirical_lawhood.adapters.simulators.gym_torax_native.extraction_manifest import verify_gym_torax_extraction_manifest
from empirical_lawhood.adapters.simulators.gym_torax_native.field_metadata import verify_installed_gym_torax_metadata_sources
from empirical_lawhood.domains.fusion.gym_torax_native.native_episode import GymToraxRuntimePreflightError
from empirical_lawhood.adapters.simulators.gym_torax_native.runtime import acquire_gym_torax_episode, inspect_gym_torax_runtime

from empirical_lawhood.domains.fusion.gym_torax_native.source_contracts import (
    GYM_TORAX_ACQUISITION_TASK_PREFIX as _science_GYM_TORAX_ACQUISITION_TASK_PREFIX,
    GYM_TORAX_CANONICAL_MEDIA_TYPE as _science_GYM_TORAX_CANONICAL_MEDIA_TYPE,
    GYM_TORAX_MAXIMUM_SOURCE_CONFIG_BYTES as _science_GYM_TORAX_MAXIMUM_SOURCE_CONFIG_BYTES,
    GymToraxFieldMetadataEpisodeAcquirer as _science_GymToraxFieldMetadataEpisodeAcquirer,
    GymToraxParameterisedAcquisitionManifest as _science_GymToraxParameterisedAcquisitionManifest,
    GymToraxParameterisedSourceConfig as _science_GymToraxParameterisedSourceConfig,
    materialise_gym_torax_parameterised_request as _science_materialise_gym_torax_parameterised_request,
    validate_gym_torax_parameterised_acquisition_manifest as _science_validate_gym_torax_parameterised_acquisition_manifest,
    validate_gym_torax_parameterised_source_config as _science_validate_gym_torax_parameterised_source_config,
)

def verify_gym_torax_static_readiness(
    *,
    source_pipeline_profile: ObjectIdentity,
    substrate_binding: ResponseSubstrateBinding,
    config: _science_GymToraxParameterisedSourceConfig,
    repository_root: Path,
) -> SourceReadinessCheck:
    """Inspect installed bytes/versions only; never construct or reset an environment."""

    reasons: set[str] = set()
    disposition = SourceReadinessDisposition.READY
    observed_version: str | None = substrate_binding.provider_version
    observed_implementation: str | None = substrate_binding.provider_implementation_sha256
    try:
        inspect_gym_torax_runtime()
        verify_gym_torax_extraction_manifest(
            config.extraction_manifest,
            expected_identity=ObjectIdentity.from_record(
                config.extraction_manifest.manifest_id,
                config.extraction_manifest,
            ),
            repository_root=repository_root,
        )
        verify_installed_gym_torax_metadata_sources(config.field_metadata_manifest)
    except GymToraxRuntimePreflightError as error:
        reasons.update(error.reason_codes)
        disposition = SourceReadinessDisposition.VERSION_MISMATCH
    except (ImportError, ModuleNotFoundError):
        reasons.add("GYM_TORAX_DEPENDENCY_NOT_INSTALLED")
        disposition = SourceReadinessDisposition.NOT_INSTALLED
        observed_version = None
        observed_implementation = None
    except (OSError, ValueError):
        reasons.add("GYM_TORAX_IMPLEMENTATION_SOURCE_DIVERGENCE")
        disposition = SourceReadinessDisposition.IMPLEMENTATION_MISMATCH
    return SourceReadinessCheck(
        check_id=f"source-readiness.{config.config_id}",
        source_pipeline_profile=source_pipeline_profile,
        provider_key=substrate_binding.provider_key,
        expected_provider_version=substrate_binding.provider_version,
        expected_implementation_sha256=substrate_binding.provider_implementation_sha256,
        disposition=disposition,
        observed_provider_version=observed_version,
        observed_implementation_sha256=observed_implementation,
        reason_codes=tuple(sorted(reasons)),
        grants_authority=False,
    )

class GymToraxParameterisedEpisodeTask:
    """One issued-config/group to one episode; it never loops or retries."""

    def __init__(
        self,
        *,
        manifest: CapabilityManifest,
        extension_set: ResponseExperimentExtensionSet,
        substrate_binding: ResponseSubstrateBinding,
        source_config: _science_GymToraxParameterisedSourceConfig,
        acquisition_manifest: _science_GymToraxParameterisedAcquisitionManifest,
        acquirer: _science_GymToraxFieldMetadataEpisodeAcquirer,
    ) -> None:
        if (
            manifest.kind is not CapabilityKind.SIMULATOR
            or manifest.input_schema_ids != (_science_GymToraxParameterisedAcquisitionManifest.SCHEMA,)
            or set(manifest.output_schema_ids)
            != {GymToraxFieldMetadataNativeEpisode.SCHEMA, LinkedCampaignStageEnvelope.SCHEMA}
        ):
            raise ValueError("Gym parameterised task manifest has another contract")
        _science_validate_gym_torax_parameterised_source_config(
            config=source_config,
            extension_set=extension_set,
            substrate_binding=substrate_binding,
        )
        _science_validate_gym_torax_parameterised_acquisition_manifest(
            manifest=acquisition_manifest,
            extension_set=extension_set,
            source_config=source_config,
        )
        self.manifest = manifest
        self._extension_set = extension_set
        self._substrate_binding = substrate_binding
        self._source_config = source_config
        self._acquisition_manifest = acquisition_manifest
        self._acquirer = acquirer

    def execute_streaming(
        self,
        context: TaskContext,
        emitter: StreamingOutputEmitter,
    ) -> tuple[ReceiptCheck, ...]:
        if len(context.input_ports) != 2 or len(context.output_ports) != 2:
            raise ValueError("Gym parameterised task requires config/manifest and two outputs")
        record_types: dict[str, type[CanonicalRecord]] = {
            _science_GymToraxParameterisedSourceConfig.SCHEMA: (_science_GymToraxParameterisedSourceConfig),
            _science_GymToraxParameterisedAcquisitionManifest.SCHEMA: (
                _science_GymToraxParameterisedAcquisitionManifest
            ),
        }
        decoded: dict[str, CanonicalRecord] = {}
        for input_port in context.input_ports:
            record_type = record_types.get(input_port.payload_schema)
            if (
                record_type is None
                or input_port.media_type != _science_GYM_TORAX_CANONICAL_MEDIA_TYPE
                or input_port.size_bytes > _science_GYM_TORAX_MAXIMUM_SOURCE_CONFIG_BYTES
            ):
                input_port.close()
                raise ValueError("Gym parameterised config/manifest port differs")
            try:
                payload = input_port.read(input_port.size_bytes + 1)
                if len(payload) != input_port.size_bytes or input_port.read(1):
                    raise ValueError("Gym parameterised config/manifest size differs")
            finally:
                input_port.close()
            value = decode_canonical_bytes(
                payload,
                record_type,
                maximum_bytes=_science_GYM_TORAX_MAXIMUM_SOURCE_CONFIG_BYTES,
            )
            if value.SCHEMA in decoded:
                raise ValueError("Gym parameterised task received a duplicate typed input")
            decoded[value.SCHEMA] = value
        if set(decoded) != set(record_types):
            raise ValueError("Gym parameterised config/manifest roster differs")
        config = decoded[_science_GymToraxParameterisedSourceConfig.SCHEMA]
        acquisition_manifest = decoded[_science_GymToraxParameterisedAcquisitionManifest.SCHEMA]
        if config != self._source_config or acquisition_manifest != self._acquisition_manifest:
            raise ValueError("Gym parameterised task received a substituted issued record")
        assert isinstance(config, _science_GymToraxParameterisedSourceConfig)
        prefix = f"{_science_GYM_TORAX_ACQUISITION_TASK_PREFIX}."
        if not context.task_id.startswith(prefix):
            raise ValueError("Gym parameterised task identity differs")
        group_id = context.task_id[len(prefix) :]
        if group_id not in self._acquisition_manifest.acquisition_group_ids:
            raise ValueError("Gym task acquisition group lies outside its manifest")
        try:
            group = next(
                value
                for value in self._extension_set.identification_config.acquisition_groups
                if value.acquisition_group_id == group_id
            )
        except StopIteration as error:
            raise ValueError("Gym task acquisition group lies outside the extension") from error
        unit = next(
            value
            for value in self._extension_set.identification_config.physical_units
            if value.physical_independent_unit_id == group.physical_independent_unit_id
        )
        view = next(
            value
            for value in self._extension_set.identification_config.nested_views
            if value.view_id == group.view_ids[0]
        )
        if any(
            value.action_word_id != view.action_word_id
            or value.numerical_member_id != view.numerical_member_id
            for value in self._extension_set.identification_config.nested_views
            if value.view_id in group.view_ids
        ):
            raise ValueError("one Gym acquisition group requests heterogeneous episodes")
        intent = materialise_native_execution_request(
            request_id=f"request.gym-torax.{group_id}",
            extension_set=self._extension_set,
            binding=self._substrate_binding,
            installed_executable_binding=(self._substrate_binding.installed_executable_binding),
            stage_id='stage.measurement-source-materialization',
            causal_cutoff_id=(
                self._extension_set.identification_config.action_chart.common_horizon_id
                if self._extension_set.identification_config.action_chart is not None
                else "cutoff.gym-torax.unspecified"
            ),
            physical_unit=unit,
            acquisition_group=group,
            nested_view=view,
        )
        request = _science_materialise_gym_torax_parameterised_request(
            intent=intent,
            extension_set=self._extension_set,
            substrate_binding=self._substrate_binding,
            config=config,
        )
        episode = self._acquirer(request)
        if (
            episode.request != ObjectIdentity.from_record(request.request_id, request)
            or episode.preparation
            != ObjectIdentity.from_record(request.preparation.preparation_id, request.preparation)
            or episode.numerical_member
            != ObjectIdentity.from_record(
                request.numerical_member.member_id, request.numerical_member
            )
            or episode.action_word
            != ObjectIdentity.from_record(
                request.schedule.action_word.word_id, request.schedule.action_word
            )
            or episode.outcome_access is not request.outcome_access
            or episode.evidence_ceiling is not request.evidence_ceiling
        ):
            raise ValueError("Gym acquired episode changed its issued identities")
        episode_output = next(
            value
            for value in context.output_ports
            if value.payload_schema == GymToraxFieldMetadataNativeEpisode.SCHEMA
        )
        envelope_output = next(
            value
            for value in context.output_ports
            if value.payload_schema == LinkedCampaignStageEnvelope.SCHEMA
        )
        envelope = LinkedCampaignStageEnvelope(
            envelope_id=f"stage-envelope.{context.task_id}",
            role=LinkedCampaignStageRole.SOURCE_MATERIALIZATION,
            disposition=LinkedCampaignDisposition.SUPPORTED,
            scientific_product=ObjectIdentity.from_record(episode.episode_id, episode),
            reason_codes=(),
        )
        for output, value in ((episode_output, episode), (envelope_output, envelope)):
            if (
                output.profile is not ArtifactProfile.CANONICAL_JSON
                or output.media_type != _science_GYM_TORAX_CANONICAL_MEDIA_TYPE
            ):
                raise ValueError("Gym parameterised output port differs")
            emitter.write(output.output_id, value.canonical_bytes())
        return (
            ReceiptCheck("bounded-canonical-stream-emitted", True, ()),
            ReceiptCheck("exact-issued-identities-preserved", True, ()),
            ReceiptCheck("one-native-record-resident", True, ()),
        )

def default_gym_torax_acquirer(
    *,
    config: _science_GymToraxParameterisedSourceConfig,
    repository_root: Path,
) -> _science_GymToraxFieldMetadataEpisodeAcquirer:
    return lambda request: acquire_gym_torax_episode(
        request,
        extraction_manifest=config.extraction_manifest,
        field_metadata_manifest=config.field_metadata_manifest,
        repository_root=repository_root,
    )
