"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.design.identification_evidence import ObservationDisposition
from empirical_lawhood.design.response_experiment import ResponseExperimentExtensionSet
from empirical_lawhood.execution.response_experiment_ports import ResponseSubstrateBinding
from empirical_lawhood.domains.fusion.gym_torax_native.diagnostic_contracts import GymToraxDeliveryDisposition, GymToraxNumericalDisposition, GymToraxObservationDisposition, GymToraxSourceDisposition
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataNativeEpisode
from empirical_lawhood.domains.fusion.gym_torax_native.observation import derive_gym_torax_observation_disposition
from empirical_lawhood.domains.fusion.gym_torax_native.source_contracts import GymToraxParameterisedSourceConfig

@dataclass(frozen=True, slots=True)
class GymToraxProjectionView(CanonicalRecord):
    """Exact neutral view and native-episode identities for one pure projection."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/gym-torax-native/gym-torax-projection-view'

    view_id: str
    acquisition_group_id: str
    physical_independent_unit_id: str
    native_preparation_id: str
    action_word_id: str
    numerical_member_id: str
    receiver_ids: tuple[str, ...]
    clock_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "view_id",
            "acquisition_group_id",
            "physical_independent_unit_id",
            "native_preparation_id",
            "action_word_id",
            "numerical_member_id",
        ):
            validate_stable_id(getattr(self, name), field_name=name)
        require_sorted_unique_strings(
            self.receiver_ids,
            field_name="receiver_ids",
            allow_empty=False,
        )
        require_sorted_unique_strings(
            self.clock_ids,
            field_name="clock_ids",
            allow_empty=False,
        )

@dataclass(frozen=True, slots=True)
class GymToraxParameterisedProjectionConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/gym-torax-native/gym-torax-parameterised-projection-config'

    config_id: str
    parameterised_source_config: ObjectIdentity
    projection_task_prefix: str
    views: tuple[GymToraxProjectionView, ...]
    grants_authority: bool
    outcome_access: OutcomeAccess

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        validate_stable_id(self.projection_task_prefix, field_name="projection_task_prefix")
        if (
            self.parameterised_source_config.object_schema
            != GymToraxParameterisedSourceConfig.SCHEMA
        ):
            raise ValueError("Gym projection config binds another source config")
        require_sorted_unique_ids(self.views, attribute="view_id", field_name="views")
        if not self.views:
            raise ValueError("Gym projection config requires scientific views")
        if self.grants_authority or self.outcome_access is not OutcomeAccess.OUTCOME_BLIND:
            raise ValueError("Gym projection config cannot grant authority or reveal outcomes")

    def view(self, view_id: str) -> GymToraxProjectionView:
        try:
            return next(value for value in self.views if value.view_id == view_id)
        except StopIteration as error:
            raise KeyError(view_id) from error

@dataclass(frozen=True, slots=True)
class GymToraxNativeProjection(CanonicalRecord):
    """View-specific native projection that constructs no response-law verdict."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/gym-torax-native/gym-torax-native-projection'

    projection_id: str
    view: ObjectIdentity
    native_episode: ObjectIdentity
    receiver_ids: tuple[str, ...]
    clock_ids: tuple[str, ...]
    source_disposition: GymToraxSourceDisposition
    delivery_disposition: GymToraxDeliveryDisposition
    numerical_disposition: GymToraxNumericalDisposition
    observation_disposition: GymToraxObservationDisposition
    projection_disposition: ObservationDisposition
    native_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    requested_accepted_applied_realized_preserved: bool
    native_units_frames_directions_preserved: bool
    causal_cutoff_preserved: bool
    scientific_verdict_constructed: bool
    outcome_access: OutcomeAccess

    def __post_init__(self) -> None:
        validate_stable_id(self.projection_id, field_name="projection_id")
        if self.view.object_schema != GymToraxProjectionView.SCHEMA:
            raise ValueError("Gym native projection binds another scientific view")
        if self.native_episode.object_schema != GymToraxFieldMetadataNativeEpisode.SCHEMA:
            raise ValueError("Gym native projection binds another episode")
        require_sorted_unique_strings(
            self.receiver_ids,
            field_name="receiver_ids",
            allow_empty=False,
        )
        require_sorted_unique_strings(self.clock_ids, field_name="clock_ids", allow_empty=False)
        require_sorted_unique_strings(
            self.native_reason_codes,
            field_name="native_reason_codes",
        )
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if (self.projection_disposition is ObservationDisposition.COMPLETE) == bool(
            self.reason_codes
        ):
            raise ValueError("Gym projection disposition and reasons disagree")
        if (
            not self.requested_accepted_applied_realized_preserved
            or not self.native_units_frames_directions_preserved
            or not self.causal_cutoff_preserved
            or self.scientific_verdict_constructed
            or self.outcome_access is not OutcomeAccess.EVALUATION_SEALED
        ):
            raise ValueError("Gym projection loses native semantics or exceeds authority")

def validate_gym_torax_projection_config(
    *,
    config: GymToraxParameterisedProjectionConfig,
    extension_set: ResponseExperimentExtensionSet,
    substrate_binding: ResponseSubstrateBinding,
    source_config: GymToraxParameterisedSourceConfig,
) -> None:
    """Join every view to its issued acquisition and native receiver contracts."""

    if config.parameterised_source_config != ObjectIdentity.from_record(
        source_config.config_id,
        source_config,
    ):
        raise ValueError("Gym projection config binds another source realization")
    if source_config.experiment_extension_set != ObjectIdentity.from_record(
        extension_set.extension_set_id,
        extension_set,
    ) or source_config.substrate_binding != ObjectIdentity.from_record(
        substrate_binding.binding_id,
        substrate_binding,
    ):
        raise ValueError("Gym projection parents differ from source parents")
    authored_views = {value.view_id: value for value in extension_set.identification_config.nested_views}
    projection_views = {value.view_id: value for value in config.views}
    if set(authored_views) != set(projection_views):
        raise ValueError("Gym projection view roster differs from the extension")
    receiver_ids = tuple(sorted(value.receiver_id for value in substrate_binding.receivers))
    clock_ids = tuple(sorted(value.clock_id for value in substrate_binding.clocks))
    for view_id, authored in authored_views.items():
        projected = projection_views[view_id]
        acquisition = source_config.binding(authored.acquisition_group_id)
        if (
            projected.acquisition_group_id != authored.acquisition_group_id
            or projected.physical_independent_unit_id != authored.physical_independent_unit_id
            or projected.native_preparation_id != acquisition.preparation.preparation_id
            or projected.action_word_id != authored.action_word_id
            or projected.numerical_member_id != authored.numerical_member_id
            or projected.receiver_ids != receiver_ids
            or projected.clock_ids != clock_ids
        ):
            raise ValueError("Gym projection view changes native group/view lineage")

def _projection_reasons(episode: GymToraxFieldMetadataNativeEpisode) -> tuple[str, ...]:
    reasons = {
        value
        for value in episode.reason_codes
        if not value.startswith(("OPERATOR_API_", "OPERATOR_SOURCE_"))
    }
    if episode.source_disposition is not GymToraxSourceDisposition.AVAILABLE:
        reasons.add(f"SOURCE_{episode.source_disposition.value}")
    if episode.delivery_disposition is not GymToraxDeliveryDisposition.COMPLETE:
        reasons.add(f"DELIVERY_{episode.delivery_disposition.value}")
    if episode.numerical_disposition is not GymToraxNumericalDisposition.VALID:
        reasons.add(f"NUMERICAL_{episode.numerical_disposition.value}")
    if episode.observation_disposition is not GymToraxObservationDisposition.COMPLETE:
        reasons.add(f"OBSERVATION_{episode.observation_disposition.value}")
    if any(value.nonfinite_value_count for value in episode.blocks):
        reasons.add("NONFINITE_NATIVE_FIELD")
    return tuple(sorted(reasons))


def project_gym_torax_episode(
    view: GymToraxProjectionView, episode: GymToraxFieldMetadataNativeEpisode
) -> GymToraxNativeProjection:
    """Reduce an authenticated captured episode to the declared scientific view."""
    if (
        episode.preparation.object_id != view.native_preparation_id
        or episode.numerical_member.object_id != view.numerical_member_id
        or episode.action_word.object_id != view.action_word_id
    ):
        raise ValueError("Gym projection input changes acquisition/view lineage")
    reasons = _projection_reasons(episode)
    projection = GymToraxNativeProjection(
        projection_id=f"projection.gym-torax.{view.view_id}",
        view=ObjectIdentity.from_record(view.view_id, view),
        native_episode=ObjectIdentity.from_record(episode.episode_id, episode),
        receiver_ids=view.receiver_ids,
        clock_ids=view.clock_ids,
        source_disposition=episode.source_disposition,
        delivery_disposition=episode.delivery_disposition,
        numerical_disposition=episode.numerical_disposition,
        observation_disposition=episode.observation_disposition,
        projection_disposition=derive_gym_torax_observation_disposition(
            episode,
            reasons,
        ),
        native_reason_codes=episode.reason_codes,
        reason_codes=reasons,
        requested_accepted_applied_realized_preserved=True,
        native_units_frames_directions_preserved=True,
        causal_cutoff_preserved=True,
        scientific_verdict_constructed=False,
        outcome_access=OutcomeAccess.EVALUATION_SEALED,
    )
    return projection
