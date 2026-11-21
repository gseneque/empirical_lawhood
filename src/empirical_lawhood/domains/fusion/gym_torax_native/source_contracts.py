"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_sha256, validate_stable_id
from empirical_lawhood.design.response_experiment import ResponseExperimentExtensionSet
from empirical_lawhood.execution.response_experiment_ports import NativeExecutionRequest, ResponseSubstrateBinding
from empirical_lawhood.domains.fusion.gym_torax_native.action_word import build_gym_torax_native_schedule
from empirical_lawhood.domains.fusion.gym_torax_native.diagnostic_contracts import GymToraxNumericalMember, GymToraxPreparation
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataEpisodeRequest, GymToraxFieldMetadataNativeEpisode, GymToraxRequestRole
from empirical_lawhood.domains.fusion.gym_torax_native.extraction_manifest import GymToraxBoundedExtractionManifest
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata import GymToraxFieldMetadataManifest
from empirical_lawhood.domains.fusion.gym_torax_native.source_qualification import GymToraxNativeSourceQualificationDisposition, GymToraxNativeSourceQualificationReceipt

GYM_TORAX_PARAMETERISED_PROVIDER_KEY = 'gym-torax-native.parameterised-source-acquisition'

GYM_TORAX_PARAMETERISED_PROVIDER_VERSION = "1.0.0"

GYM_TORAX_CANONICAL_MEDIA_TYPE = "application/json"

GYM_TORAX_MAXIMUM_REQUEST_BYTES = 8 * 1024 * 1024

GYM_TORAX_MAXIMUM_SOURCE_CONFIG_BYTES = 32 * 1024 * 1024

GYM_TORAX_ACQUISITION_TASK_PREFIX = "task.gym-torax-acquire"

@dataclass(frozen=True, slots=True)
class GymToraxParameterisedAcquisitionBinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/gym-torax-native/gym-torax-parameterised-acquisition-binding'

    binding_id: str
    acquisition_group_id: str
    preparation_instance_id: str
    physical_independent_unit_id: str
    preparation_coordinate_id: str
    view_ids: tuple[str, ...]
    preparation_sha256: str
    environment_seed_id: str
    environment_seed: int
    numerical_member_id: str
    preparation: GymToraxPreparation
    numerical_member: GymToraxNumericalMember

    def __post_init__(self) -> None:
        for name in (
            "binding_id",
            "acquisition_group_id",
            "preparation_instance_id",
            "physical_independent_unit_id",
            "preparation_coordinate_id",
            "environment_seed_id",
            "numerical_member_id",
        ):
            validate_stable_id(getattr(self, name), field_name=name)
        if tuple(sorted(set(self.view_ids))) != self.view_ids or not self.view_ids:
            raise ValueError("Gym--TORAX acquisition views must be sorted and nonempty")
        validate_sha256(self.preparation_sha256, field_name="preparation_sha256")
        if (
            self.environment_seed < 0
            or self.environment_seed != self.preparation.environment_seed
            or self.physical_independent_unit_id != self.preparation.physical_independent_unit_id
            or self.preparation_sha256 != self.preparation.fingerprint()
            or self.numerical_member_id != self.numerical_member.member_id
        ):
            raise ValueError("Gym--TORAX adapter realization differs from its native records")

@dataclass(frozen=True, slots=True)
class GymToraxParameterisedSourceConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/gym-torax-native/gym-torax-parameterised-source-config'

    config_id: str
    experiment_extension_set: ObjectIdentity
    substrate_binding: ObjectIdentity
    source_pipeline_profile: ObjectIdentity
    source_qualification: GymToraxNativeSourceQualificationReceipt
    extraction_manifest: GymToraxBoundedExtractionManifest
    field_metadata_manifest: GymToraxFieldMetadataManifest
    acquisition_bindings: tuple[GymToraxParameterisedAcquisitionBinding, ...]
    maximum_episode_bytes: int
    maximum_episode_outcome_access: OutcomeAccess
    maximum_evidence_ceiling: EvidenceCeiling
    grants_authority: bool
    outcome_access: OutcomeAccess

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        if self.experiment_extension_set.object_schema != ResponseExperimentExtensionSet.SCHEMA:
            raise ValueError("Gym source config requires a measurement through controller use extension set")
        if self.substrate_binding.object_schema != ResponseSubstrateBinding.SCHEMA:
            raise ValueError("Gym source config requires the open substrate binding")
        require_sorted_unique_ids(
            self.acquisition_bindings,
            attribute="acquisition_group_id",
            field_name="acquisition_bindings",
        )
        if not self.acquisition_bindings:
            raise ValueError("Gym source config requires acquisition bindings")
        all_views = tuple(
            sorted(view for binding in self.acquisition_bindings for view in binding.view_ids)
        )
        if len(set(all_views)) != len(all_views):
            raise ValueError("Gym source config maps a view to multiple acquisitions")
        qualification = self.source_qualification
        if (
            qualification.disposition is not GymToraxNativeSourceQualificationDisposition.QUALIFIED
            or qualification.extraction_manifest
            != ObjectIdentity.from_record(
                self.extraction_manifest.manifest_id,
                self.extraction_manifest,
            )
            or qualification.field_metadata_manifest
            != ObjectIdentity.from_record(
                self.field_metadata_manifest.manifest_id,
                self.field_metadata_manifest,
            )
        ):
            raise ValueError("Gym source config lacks exact source qualification")
        if not 0 < self.maximum_episode_bytes <= 512 * 1024**2:
            raise ValueError("Gym source episode bound is outside 512 MiB")
        if (
            self.maximum_episode_outcome_access is not OutcomeAccess.EVALUATION_SEALED
            or self.maximum_evidence_ceiling is not EvidenceCeiling.MEASUREMENT
            or self.grants_authority
            or self.outcome_access is not OutcomeAccess.OUTCOME_BLIND
        ):
            raise ValueError("Gym source config exceeds its source-only authority")

    def binding(self, acquisition_group_id: str) -> GymToraxParameterisedAcquisitionBinding:
        for value in self.acquisition_bindings:
            if value.acquisition_group_id == acquisition_group_id:
                return value
        raise KeyError(acquisition_group_id)

@dataclass(frozen=True, slots=True)
class GymToraxParameterisedAcquisitionManifest(CanonicalRecord):
    """Shared scientific source declaration, distinct from executable config."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/gym-torax-native/gym-torax-parameterised-acquisition-manifest'

    manifest_id: str
    source_config: ObjectIdentity
    acquisition_group_ids: tuple[str, ...]
    view_ids: tuple[str, ...]
    grants_authority: bool
    outcome_access: OutcomeAccess

    def __post_init__(self) -> None:
        validate_stable_id(self.manifest_id, field_name="manifest_id")
        if self.source_config.object_schema != GymToraxParameterisedSourceConfig.SCHEMA:
            raise ValueError("Gym acquisition manifest binds another source config")
        require_sorted_unique_strings(
            self.acquisition_group_ids,
            field_name="acquisition_group_ids",
            allow_empty=False,
        )
        require_sorted_unique_strings(self.view_ids, field_name="view_ids", allow_empty=False)
        if self.grants_authority or self.outcome_access is not OutcomeAccess.OUTCOME_BLIND:
            raise ValueError("Gym acquisition manifest cannot grant authority or reveal outcomes")

def validate_gym_torax_parameterised_acquisition_manifest(
    *,
    manifest: GymToraxParameterisedAcquisitionManifest,
    extension_set: ResponseExperimentExtensionSet,
    source_config: GymToraxParameterisedSourceConfig,
) -> None:
    if manifest.source_config != ObjectIdentity.from_record(
        source_config.config_id,
        source_config,
    ):
        raise ValueError("Gym acquisition manifest binds another source realization")
    if manifest.acquisition_group_ids != tuple(
        sorted(
            value.acquisition_group_id for value in extension_set.identification_config.acquisition_groups
        )
    ) or manifest.view_ids != tuple(
        sorted(value.view_id for value in extension_set.identification_config.nested_views)
    ):
        raise ValueError("Gym acquisition manifest changes the group/view roster")

def validate_gym_torax_parameterised_source_config(
    *,
    config: GymToraxParameterisedSourceConfig,
    extension_set: ResponseExperimentExtensionSet,
    substrate_binding: ResponseSubstrateBinding,
) -> None:
    """Join adapter realization to the neutral unit/group/view model exactly."""

    if config.experiment_extension_set != ObjectIdentity.from_record(
        extension_set.extension_set_id, extension_set
    ) or config.substrate_binding != ObjectIdentity.from_record(
        substrate_binding.binding_id, substrate_binding
    ):
        raise ValueError("Gym source config changed its generic parents")
    identification_config = extension_set.identification_config
    if (
        config.source_pipeline_profile != identification_config.source_pipeline_profile
        or substrate_binding.provider_key != GYM_TORAX_PARAMETERISED_PROVIDER_KEY
        or substrate_binding.provider_version != GYM_TORAX_PARAMETERISED_PROVIDER_VERSION
        or substrate_binding.native_episode_schema != GymToraxFieldMetadataNativeEpisode.SCHEMA
    ):
        raise ValueError("Gym source config changes source/provider native semantics")
    groups = {value.acquisition_group_id: value for value in identification_config.acquisition_groups}
    units = {value.physical_independent_unit_id: value for value in identification_config.physical_units}
    views = {value.view_id: value for value in identification_config.nested_views}
    if set(groups) != {value.acquisition_group_id for value in config.acquisition_bindings}:
        raise ValueError("Gym acquisition binding roster differs from extension groups")
    for binding in config.acquisition_bindings:
        group = groups[binding.acquisition_group_id]
        unit = units[group.physical_independent_unit_id]
        if (
            binding.preparation_instance_id != group.preparation_instance_id
            or binding.physical_independent_unit_id != group.physical_independent_unit_id
            or binding.preparation_coordinate_id != unit.preparation_coordinate_id
            or binding.view_ids != group.view_ids
            or binding.preparation_sha256 != unit.preparation_sha256
            or binding.environment_seed_id != unit.adapter_realization_id
            or any(
                views[view_id].acquisition_group_id != group.acquisition_group_id
                or views[view_id].numerical_member_id != binding.numerical_member_id
                for view_id in group.view_ids
            )
        ):
            raise ValueError("Gym acquisition binding changes unit/group/view lineage")

def materialise_gym_torax_parameterised_request(
    *,
    intent: NativeExecutionRequest,
    extension_set: ResponseExperimentExtensionSet,
    substrate_binding: ResponseSubstrateBinding,
    config: GymToraxParameterisedSourceConfig,
) -> GymToraxFieldMetadataEpisodeRequest:
    "Lower one neutral interactive intent to the authoritative request."

    validate_gym_torax_parameterised_source_config(
        config=config,
        extension_set=extension_set,
        substrate_binding=substrate_binding,
    )
    if (
        intent.experiment_extension_set != config.experiment_extension_set
        or intent.substrate_binding != config.substrate_binding
        or intent.native_config != substrate_binding.native_config
        or intent.native_request_schema != substrate_binding.native_request_schema
    ):
        raise ValueError("Gym native intent differs from its frozen config/binding")
    binding = config.binding(intent.acquisition_group_id)
    if (
        intent.preparation_instance_id != binding.preparation_instance_id
        or intent.physical_independent_unit_id != binding.physical_independent_unit_id
        or intent.preparation_coordinate_id != binding.preparation_coordinate_id
        or intent.preparation_sha256 != binding.preparation_sha256
        or intent.adapter_realization_id != binding.environment_seed_id
        or intent.nested_view_id not in binding.view_ids
    ):
        raise ValueError("Gym native intent changes adapter realization lineage")
    chart = extension_set.identification_config.action_chart
    if chart is None:
        raise ValueError("interactive Gym acquisition requires a declared action chart")
    try:
        action_word = next(
            value for value in chart.action_words if value.word_id == intent.action_word_id
        )
    except StopIteration as error:
        raise ValueError("Gym intent action word is absent from the issued chart") from error
    return GymToraxFieldMetadataEpisodeRequest(
        request_id=intent.request_id,
        request_role=GymToraxRequestRole.SCIENTIFIC_EPISODE,
        source_qualification=ObjectIdentity.from_record(
            config.source_qualification.receipt_id,
            config.source_qualification,
        ),
        extraction_manifest=ObjectIdentity.from_record(
            config.extraction_manifest.manifest_id,
            config.extraction_manifest,
        ),
        field_metadata_manifest=ObjectIdentity.from_record(
            config.field_metadata_manifest.manifest_id,
            config.field_metadata_manifest,
        ),
        preparation=binding.preparation,
        numerical_member=binding.numerical_member,
        schedule=build_gym_torax_native_schedule(action_word),
        maximum_output_bytes=config.maximum_episode_bytes,
        outcome_access=config.maximum_episode_outcome_access,
        evidence_ceiling=config.maximum_evidence_ceiling,
    )

GymToraxFieldMetadataEpisodeAcquirer = Callable[[GymToraxFieldMetadataEpisodeRequest], GymToraxFieldMetadataNativeEpisode]
