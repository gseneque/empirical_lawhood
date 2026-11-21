"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
import math
import re
from typing import cast
import numpy as np
import numpy.typing as npt
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.domains.fusion.gym_torax_native.diagnostic_contracts import GYM_TORAX_HORIZON_REQUESTS, GymToraxActionDelivery, GymToraxDeliveryDisposition, GymToraxNativeAction, GymToraxNumericalDisposition, GymToraxObservationDisposition, GymToraxOperatorSourceSummary, GymToraxSourceDisposition
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataEpisodeRequest, GymToraxFieldMetadataFloat64Block, GymToraxFieldMetadataNativeEpisode, encode_gym_torax_float64_block
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata import GymToraxFieldMetadataManifest
from empirical_lawhood.domains.fusion.gym_torax_native.extraction_manifest import GymToraxBoundedExtractionManifest

_EXPECTED_VERSIONS = {
    "python": "3.11.14",
    "numpy": "2.4.6",
    "scipy": "1.17.1",
    "xarray": "2026.7.0",
    "gymtorax": "1.1.1",
    "torax": "1.4.2",
    "jax": "0.10.2",
    "jaxlib": "0.10.2",
}

_REQUIRED_PROFILES = frozenset(("T_e", "T_i", "n_e", "psi", "q"))

_REQUIRED_SCALARS = frozenset(
    (
        "H98",
        "P_heat_total",
        "P_radiation_e",
        "Q_fusion",
        "beta_N",
        "fgw_n_e_volume_avg",
        "q95",
        "q_min",
    )
)

_REQUIRED_NUMERICS = frozenset(("solver_error_state",))

_MINIMUM_EPISODE_ENVELOPE_BYTES = 16 * 1024

_BLOCK_METADATA_RESERVE_BYTES = 2 * 1024

_ACTION_COMPONENT_IDS = (
    "ip-a",
    "nbi-power-w",
    "nbi-location",
    "nbi-width",
    "ecrh-power-w",
    "ecrh-location",
    "ecrh-width",
)

@dataclass(frozen=True, slots=True)
class GymToraxRuntimeProbe:
    python_version: str
    numpy_version: str
    scipy_version: str
    xarray_version: str
    gymtorax_version: str
    torax_version: str
    jax_version: str
    jaxlib_version: str
    backend: str
    x64_enabled: bool

@dataclass(frozen=True, slots=True)
class GymToraxCapturedState:
    profiles: Mapping[str, npt.NDArray[np.float64]]
    scalars: Mapping[str, npt.NDArray[np.float64]]
    numerics: Mapping[str, npt.NDArray[np.float64]]
    dimensions: Mapping[tuple[str, str], tuple[str, ...]]
    coordinates: Mapping[str, npt.NDArray[np.float64]]
    reason_codes: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class GymToraxOperatorSnapshot:
    """One authentic source-provided controlled-IO operand triple."""

    request_clock: int
    source_method_id: str
    state_coordinate_ids: tuple[str, ...]
    input_coordinate_ids: tuple[str, ...]
    receiver_coordinate_ids: tuple[str, ...]
    transition_a: npt.NDArray[np.float64]
    input_b: npt.NDArray[np.float64]
    receiver_c: npt.NDArray[np.float64]

class GymToraxRuntimePreflightError(RuntimeError):
    """Fail-closed runtime-denominator mismatch before environment creation."""

    def __init__(self, reason_codes: Sequence[str]) -> None:
        self.reason_codes = tuple(sorted(set(reason_codes)))
        super().__init__(",".join(self.reason_codes))

class GymToraxOutputBoundError(RuntimeError):
    """The requested bound cannot contain even a typed minimal episode."""

@dataclass(slots=True)
class _GymToraxEncodedOutputBudget:
    maximum_bytes: int
    reserved_bytes: int = _MINIMUM_EPISODE_ENVELOPE_BYTES

    def reserve_array(self, values: npt.NDArray[np.float64]) -> None:
        self.reserve_shape(tuple(int(value) for value in values.shape))

    def reserve_shape(self, shape: tuple[int, ...]) -> None:
        element_count = math.prod(shape)
        raw_bytes = element_count * 8
        encoded_bytes = 4 * ((raw_bytes + 2) // 3)
        proposed = self.reserved_bytes + encoded_bytes + _BLOCK_METADATA_RESERVE_BYTES
        if proposed > self.maximum_bytes:
            raise GymToraxOutputBoundError("GYM_TORAX_OUTPUT_BOUND_EXCEEDED")
        self.reserved_bytes = proposed

    def reserve_record(self, value: CanonicalRecord) -> None:
        proposed = self.reserved_bytes + len(value.canonical_bytes())
        if proposed > self.maximum_bytes:
            raise GymToraxOutputBoundError("GYM_TORAX_OUTPUT_BOUND_EXCEEDED")
        self.reserved_bytes = proposed

def _array_output_reservation(values: npt.NDArray[np.float64]) -> int:
    raw_bytes = int(values.size) * 8
    return 4 * ((raw_bytes + 2) // 3) + _BLOCK_METADATA_RESERVE_BYTES

def _reserve_capture_before_append(
    capture: GymToraxCapturedState,
    *,
    reserved_bytes: int,
    maximum_bytes: int,
    include_coordinates: bool,
) -> int:
    arrays = (
        *capture.profiles.values(),
        *capture.scalars.values(),
        *capture.numerics.values(),
        *(capture.coordinates.values() if include_coordinates else ()),
    )
    proposed = reserved_bytes + sum(_array_output_reservation(value) for value in arrays)
    if proposed > maximum_bytes:
        raise GymToraxOutputBoundError("GYM_TORAX_OUTPUT_BOUND_EXCEEDED")
    return proposed

def _reserve_operator_before_append(
    snapshot: GymToraxOperatorSnapshot,
    *,
    reserved_bytes: int,
    maximum_bytes: int,
) -> int:
    proposed = reserved_bytes + sum(
        _array_output_reservation(value)
        for value in (snapshot.transition_a, snapshot.input_b, snapshot.receiver_c)
    )
    if proposed > maximum_bytes:
        raise GymToraxOutputBoundError("GYM_TORAX_OUTPUT_BOUND_EXCEEDED")
    return proposed

def _validate_runtime_probe(probe: GymToraxRuntimeProbe) -> None:
    reasons = {
        f"RUNTIME_VERSION_MISMATCH_{name.upper()}"
        for name, expected in _EXPECTED_VERSIONS.items()
        if getattr(probe, f"{name}_version") != expected
    }
    if probe.backend != "cpu":
        reasons.add("RUNTIME_BACKEND_NOT_CPU")
    if not probe.x64_enabled:
        reasons.add("RUNTIME_FLOAT64_DISABLED")
    if reasons:
        raise GymToraxRuntimePreflightError(tuple(reasons))

def _validate_exact_native_schedule(request: GymToraxFieldMetadataEpisodeRequest) -> None:
    from empirical_lawhood.domains.fusion.gym_torax_native.action_word import build_gym_torax_native_schedule

    try:
        expected = build_gym_torax_native_schedule(request.schedule.action_word)
    except ValueError as error:
        raise GymToraxRuntimePreflightError(("NATIVE_ACTION_WORD_IDENTITY_DRIFT",)) from error
    if request.schedule != expected:
        raise GymToraxRuntimePreflightError(("NATIVE_SCHEDULE_IDENTITY_DRIFT",))

def _validate_field_metadata_binding(
    request: GymToraxFieldMetadataEpisodeRequest,
    manifest: GymToraxFieldMetadataManifest,
) -> None:
    expected = ObjectIdentity.from_record(manifest.manifest_id, manifest)
    if request.field_metadata_manifest != expected:
        raise GymToraxRuntimePreflightError(("FIELD_METADATA_MANIFEST_DIVERGENCE",))

def _validate_extraction_binding(
    request: GymToraxFieldMetadataEpisodeRequest,
    manifest: GymToraxBoundedExtractionManifest,
) -> None:
    expected = ObjectIdentity.from_record(manifest.manifest_id, manifest)
    if request.extraction_manifest != expected:
        raise GymToraxRuntimePreflightError(("SURGICAL_EXTRACTION_MANIFEST_DIVERGENCE",))

def _reason_token(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_") or "UNKNOWN"

def _stable_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown"

def _validate_operator_snapshot(
    snapshot: GymToraxOperatorSnapshot, *, expected_clock: int
) -> None:
    if snapshot.request_clock != expected_clock:
        raise ValueError("operator snapshot changed its request clock")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", snapshot.source_method_id):
        raise ValueError("operator source method identity is invalid")
    for values in (
        snapshot.state_coordinate_ids,
        snapshot.input_coordinate_ids,
        snapshot.receiver_coordinate_ids,
    ):
        if (
            not values
            or len(set(values)) != len(values)
            or any(not isinstance(value, str) or not value for value in values)
        ):
            raise ValueError("operator coordinate basis is empty or ambiguous")
    n_state = len(snapshot.state_coordinate_ids)
    n_input = len(snapshot.input_coordinate_ids)
    n_receiver = len(snapshot.receiver_coordinate_ids)
    if (
        snapshot.transition_a.shape != (n_state, n_state)
        or snapshot.input_b.shape != (n_state, n_input)
        or snapshot.receiver_c.shape != (n_receiver, n_state)
        or not np.isfinite(snapshot.transition_a).all()
        or not np.isfinite(snapshot.input_b).all()
        or not np.isfinite(snapshot.receiver_c).all()
    ):
        raise ValueError("operator operand shape or finiteness differs from its basis")

def _operator_blocks(
    snapshots: Sequence[GymToraxOperatorSnapshot],
    *,
    api_exposed: bool,
    output_budget: _GymToraxEncodedOutputBudget,
    reasons: set[str],
) -> tuple[tuple[GymToraxFieldMetadataFloat64Block, ...], GymToraxOperatorSourceSummary]:
    if not api_exposed:
        reasons.add("OPERATOR_API_UNAVAILABLE")
        return (), GymToraxOperatorSourceSummary(
            summary_id='operator-source.tokamak-control.unavailable',
            disposition=GymToraxSourceDisposition.OPERATOR_API_UNAVAILABLE,
            source_method_id="operator-source.gym-torax.unavailable",
            state_coordinate_ids=(),
            input_coordinate_ids=(),
            receiver_coordinate_ids=(),
            operator_block_ids=(),
            reason_codes=("OPERATOR_API_UNAVAILABLE",),
        )
    expected_clocks = tuple(range(104, 110))
    rosters = {
        (
            value.source_method_id,
            value.state_coordinate_ids,
            value.input_coordinate_ids,
            value.receiver_coordinate_ids,
        )
        for value in snapshots
    }
    if tuple(value.request_clock for value in snapshots) != expected_clocks or len(rosters) != 1:
        reasons.add("OPERATOR_SOURCE_INCOMPLETE")
        return (), GymToraxOperatorSourceSummary(
            summary_id='operator-source.tokamak-control.incomplete',
            disposition=GymToraxSourceDisposition.SOURCE_UNAVAILABLE,
            source_method_id="operator-source.gym-torax.incomplete",
            state_coordinate_ids=(),
            input_coordinate_ids=(),
            receiver_coordinate_ids=(),
            operator_block_ids=(),
            reason_codes=("OPERATOR_SOURCE_INCOMPLETE",),
        )
    source_method_id, state_ids, input_ids, receiver_ids = next(iter(rosters))
    clocks = tuple(value.request_clock for value in snapshots)
    blocks_list: list[GymToraxFieldMetadataFloat64Block] = []
    for name, attribute, dimensions in (
        ("A", "transition_a", ("state-row", "state-column")),
        ("B", "input_b", ("state-row", "input-column")),
        ("C", "receiver_c", ("receiver-row", "state-column")),
    ):
        arrays = [getattr(value, attribute) for value in snapshots]
        shape = (len(arrays), *arrays[0].shape)
        output_budget.reserve_shape(shape)
        blocks_list.append(
            encode_gym_torax_float64_block(
                block_id=f"block.operator-{name.lower()}",
                category="operator",
                native_field_id=name,
                native_unit="source-native",
                native_frame_id='frame.tokamak-control.controlled-io-operator',
                field_metadata_id=None,
                dimension_ids=("request-clock", *dimensions),
                values=np.stack(arrays),
                clock_values=clocks,
            )
        )
    blocks = tuple(sorted(blocks_list, key=lambda value: value.block_id))
    return blocks, GymToraxOperatorSourceSummary(
        summary_id='operator-source.tokamak-control.available',
        disposition=GymToraxSourceDisposition.AVAILABLE,
        source_method_id=source_method_id,
        state_coordinate_ids=state_ids,
        input_coordinate_ids=input_ids,
        receiver_coordinate_ids=receiver_ids,
        operator_block_ids=tuple(value.block_id for value in blocks),
        reason_codes=(),
    )

def _captured_state_blocks(
    captures: Sequence[GymToraxCapturedState],
    clocks: tuple[int, ...],
    *,
    field_metadata_manifest: GymToraxFieldMetadataManifest,
    output_budget: _GymToraxEncodedOutputBudget,
    reasons: set[str],
) -> tuple[GymToraxFieldMetadataFloat64Block, ...]:
    blocks: list[GymToraxFieldMetadataFloat64Block] = []
    coordinates: dict[str, npt.NDArray[np.float64]] = {}
    dimensions_by_capture: list[Mapping[tuple[str, str], tuple[str, ...]]] = []
    for capture in captures:
        coordinates.update(capture.coordinates)
        dimensions_by_capture.append(capture.dimensions)
        reasons.update(capture.reason_codes)
    retained_coordinate_ids = {
        dimension_id
        for field in field_metadata_manifest.fields
        for dimension_id in field.native_dimension_ids
        if dimension_id != "value"
    }
    for coordinate_id in sorted(retained_coordinate_ids):
        if coordinate_id not in coordinates:
            reasons.add(f"SOURCE_COORDINATE_MISSING_{_reason_token(coordinate_id)}")
            continue
        values = coordinates[coordinate_id]
        output_budget.reserve_array(values)
        blocks.append(
            encode_gym_torax_float64_block(
                block_id=f"block.coordinate.{_stable_token(coordinate_id)}",
                category="coordinate",
                native_field_id=coordinate_id,
                native_unit="1",
                native_frame_id=f'frame.tokamak-control.{_stable_token(coordinate_id)}',
                field_metadata_id=None,
                dimension_ids=(coordinate_id,),
                values=values,
            )
        )
    for field_metadata in field_metadata_manifest.fields:
        category = field_metadata.source_category
        field_id = field_metadata.native_field_id
        category_id = {
            "profiles": "profile",
            "scalars": "scalar",
            "numerics": "numerics",
        }[category]
        observed = [getattr(capture, category).get(field_id) for capture in captures]
        exemplar = next((value for value in observed if value is not None), None)
        if exemplar is None:
            reasons.add(f"SOURCE_FIELD_MISSING_{_reason_token(field_id)}")
            continue
        normalized: list[npt.NDArray[np.float64]] = []
        for value in observed:
            if value is None or value.shape != exemplar.shape:
                reasons.add("SOURCE_FIELD_MISSING_OR_SHAPE_DRIFT")
                normalized.append(np.full(exemplar.shape, np.nan, dtype=np.float64))
            else:
                normalized.append(value)
        key = (category, field_id)
        if any(
            dimensions.get(key) != field_metadata.native_dimension_ids
            for dimensions in dimensions_by_capture
        ):
            reasons.add("SOURCE_FIELD_DIMENSION_METADATA_MISMATCH")
        if len(field_metadata.native_dimension_ids) != exemplar.ndim:
            reasons.add("SOURCE_FIELD_DIMENSION_METADATA_MISMATCH")
        stacked_shape = (len(normalized), *exemplar.shape)
        output_budget.reserve_shape(stacked_shape)
        blocks.append(
            encode_gym_torax_float64_block(
                block_id=f"block.source-{category_id}.{_stable_token(field_id)}",
                category=f"source-{category_id}",
                native_field_id=field_id,
                native_unit=field_metadata.native_unit,
                native_frame_id=field_metadata.native_frame_id,
                field_metadata_id=field_metadata.field_metadata_id,
                dimension_ids=("state-clock", *field_metadata.native_dimension_ids),
                values=np.stack(normalized),
                clock_values=clocks,
            )
        )
    return tuple(sorted(blocks, key=lambda value: value.block_id))

def _action_blocks(
    deliveries: Sequence[GymToraxActionDelivery],
    *,
    output_budget: _GymToraxEncodedOutputBudget,
) -> tuple[GymToraxFieldMetadataFloat64Block, ...]:
    clocks = tuple(value.request_clock for value in deliveries)
    blocks: list[GymToraxFieldMetadataFloat64Block] = []
    for stage in ("requested", "accepted", "applied", "realized"):
        values = []
        for delivery in deliveries:
            action = cast(GymToraxNativeAction | None, getattr(delivery, stage))
            values.append(
                encode_gym_torax_action_values(action)
                if action is not None
                else np.full(len(_ACTION_COMPONENT_IDS), np.nan, dtype=np.float64)
            )
        if values:
            output_budget.reserve_shape((len(values), len(_ACTION_COMPONENT_IDS)))
            blocks.append(
                encode_gym_torax_float64_block(
                    block_id=f"block.action-{stage}",
                    category=f"action-{stage}",
                    native_field_id="native-action",
                    native_unit="mixed-native-see-action-component-contract",
                    native_frame_id='frame.tokamak-control.native-action-chart',
                    field_metadata_id=None,
                    dimension_ids=("request-clock", "action-component"),
                    values=np.stack(values),
                    clock_values=clocks,
                )
            )
    return tuple(sorted(blocks, key=lambda value: value.block_id))

def _episode_id(request: GymToraxFieldMetadataEpisodeRequest) -> str:
    return f"episode.{request.request_id.removeprefix('request.')}"

def _empty_operator_summary(
    disposition: GymToraxSourceDisposition, reason: str
) -> GymToraxOperatorSourceSummary:
    return GymToraxOperatorSourceSummary(
        summary_id=f'operator-source.tokamak-control.{_stable_token(disposition.value)}',
        disposition=disposition,
        source_method_id=f"operator-source.gym-torax.{_stable_token(disposition.value)}",
        state_coordinate_ids=(),
        input_coordinate_ids=(),
        receiver_coordinate_ids=(),
        operator_block_ids=(),
        reason_codes=(reason,),
    )

def finalize_gym_torax_episode(
    *,
    request: GymToraxFieldMetadataEpisodeRequest,
    extraction_manifest: GymToraxBoundedExtractionManifest,
    field_metadata_manifest: GymToraxFieldMetadataManifest,
    runtime_probe: GymToraxRuntimeProbe,
    source_reset_attempted: bool,
    state_clocks: Sequence[int],
    captures: Sequence[GymToraxCapturedState],
    deliveries: Sequence[GymToraxActionDelivery],
    operator_snapshots: Sequence[GymToraxOperatorSnapshot],
    operator_api_exposed: bool,
    reason_codes: Sequence[str],
    termination: bool,
    truncation: bool,
    runtime_seconds: Decimal,
    peak_rss_bytes: int,
    initial_numerical_disposition: GymToraxNumericalDisposition | None = None,
    initial_observation_disposition: GymToraxObservationDisposition = GymToraxObservationDisposition.COMPLETE,
) -> GymToraxFieldMetadataNativeEpisode:
    """Finalize captures from either ordinary or live controlled acquisition.

    This has no environment or action-selection authority.  It only applies
    the same bounded episode encoding and orthogonal disposition derivation as
    the ordinary source path to an already completed capture ledger.
    """

    _validate_exact_native_schedule(request)
    _validate_extraction_binding(request, extraction_manifest)
    _validate_field_metadata_binding(request, field_metadata_manifest)
    _validate_runtime_probe(runtime_probe)
    reasons = set(reason_codes)
    clocks = tuple(state_clocks)
    if clocks != tuple(sorted(set(clocks))):
        raise ValueError("episode finalization state clocks are not exact")
    if len(captures) != len(clocks):
        raise ValueError("episode finalization captures differ from state clocks")
    missing = tuple(value for value in range(GYM_TORAX_HORIZON_REQUESTS + 1) if value not in clocks)
    observation = initial_observation_disposition
    numerical = initial_numerical_disposition if initial_numerical_disposition is not None else (
        GymToraxNumericalDisposition.SOLVER_FAILURE
        if "SOLVER_FAILURE" in reasons
        else GymToraxNumericalDisposition.VALID
    )
    if missing:
        reasons.add("REQUIRED_STATE_CLOCKS_ABSENT")
        observation = (
            GymToraxObservationDisposition.PARTIAL
            if clocks
            else GymToraxObservationDisposition.UNEVALUABLE
        )
    available_profiles = set().union(*(capture.profiles.keys() for capture in captures))
    available_scalars = set().union(*(capture.scalars.keys() for capture in captures))
    available_numerics = set().union(*(capture.numerics.keys() for capture in captures))
    if _REQUIRED_PROFILES - available_profiles:
        reasons.add("REQUIRED_PROFILE_OPERAND_ABSENT")
        observation = GymToraxObservationDisposition.PARTIAL if clocks else observation
    if _REQUIRED_SCALARS - available_scalars:
        reasons.add("REQUIRED_SCALAR_OPERAND_ABSENT")
        observation = GymToraxObservationDisposition.PARTIAL if clocks else observation
    if _REQUIRED_NUMERICS - available_numerics:
        reasons.add("SOLVER_ERROR_STATE_ABSENT")
        observation = GymToraxObservationDisposition.PARTIAL if clocks else observation
    if captures and any(
        _REQUIRED_PROFILES - capture.profiles.keys()
        or _REQUIRED_SCALARS - capture.scalars.keys()
        or _REQUIRED_NUMERICS - capture.numerics.keys()
        for capture in captures
    ):
        reasons.add("REQUIRED_FIELD_CLOCK_COVERAGE_INCOMPLETE")
        observation = GymToraxObservationDisposition.PARTIAL
    if any(
        not np.isfinite(value).all()
        for capture in captures
        for field_id, value in (*capture.profiles.items(), *capture.scalars.items())
        if field_id in _REQUIRED_PROFILES or field_id in _REQUIRED_SCALARS
    ):
        reasons.add("NONFINITE_REQUIRED_STATE")
        numerical = GymToraxNumericalDisposition.INVALID

    output_budget = _GymToraxEncodedOutputBudget(request.maximum_output_bytes)
    for delivery in deliveries:
        output_budget.reserve_record(delivery)
    state_blocks = (
        _captured_state_blocks(
            captures,
            clocks,
            field_metadata_manifest=field_metadata_manifest,
            output_budget=output_budget,
            reasons=reasons,
        )
        if captures
        else ()
    )
    if any(
        reason.startswith(("SOURCE_FIELD_", "SOURCE_COORDINATE_", "REQUIRED_FIELD_"))
        for reason in reasons
    ):
        observation = (
            GymToraxObservationDisposition.PARTIAL
            if clocks
            else GymToraxObservationDisposition.UNEVALUABLE
        )
    action_blocks = _action_blocks(deliveries, output_budget=output_budget)
    if not clocks:
        operator_blocks: tuple[GymToraxFieldMetadataFloat64Block, ...] = ()
        operator_summary = _empty_operator_summary(
            GymToraxSourceDisposition.SOURCE_UNAVAILABLE,
            "SOURCE_EPISODE_UNAVAILABLE",
        )
        reasons.add("SOURCE_EPISODE_UNAVAILABLE")
    else:
        operator_blocks, operator_summary = _operator_blocks(
            operator_snapshots,
            api_exposed=operator_api_exposed,
            output_budget=output_budget,
            reasons=reasons,
        )
    blocks = tuple(
        sorted((*state_blocks, *action_blocks, *operator_blocks), key=lambda value: value.block_id)
    )
    delivery_disposition = GymToraxDeliveryDisposition.COMPLETE
    observed_delivery_dispositions = {value.disposition for value in deliveries}
    for candidate in (
        GymToraxDeliveryDisposition.REJECTED,
        GymToraxDeliveryDisposition.PARTIAL,
        GymToraxDeliveryDisposition.CLIPPED,
    ):
        if candidate in observed_delivery_dispositions:
            delivery_disposition = candidate
            break
    if len(deliveries) != GYM_TORAX_HORIZON_REQUESTS:
        delivery_disposition = GymToraxDeliveryDisposition.PARTIAL
        reasons.add("DELIVERY_HORIZON_INCOMPLETE")

    episode = GymToraxFieldMetadataNativeEpisode(
        episode_id=_episode_id(request),
        request=ObjectIdentity.from_record(request.request_id, request),
        preparation=ObjectIdentity.from_record(
            request.preparation.preparation_id,
            request.preparation,
        ),
        numerical_member=ObjectIdentity.from_record(
            request.numerical_member.member_id,
            request.numerical_member,
        ),
        action_word=ObjectIdentity.from_record(
            request.schedule.action_word.word_id,
            request.schedule.action_word,
        ),
        extraction_manifest=request.extraction_manifest,
        field_metadata_manifest=request.field_metadata_manifest,
        source_reset_attempted=source_reset_attempted,
        state_clocks=clocks,
        missing_required_state_clocks=missing,
        last_valid_state_clock=max(clocks) if clocks else None,
        deliveries=tuple(sorted(deliveries, key=lambda value: value.delivery_id)),
        blocks=blocks,
        operator_source=operator_summary,
        source_disposition=(
            GymToraxSourceDisposition.AVAILABLE
            if any(value.category.startswith("source-") for value in blocks)
            else GymToraxSourceDisposition.SOURCE_UNAVAILABLE
        ),
        delivery_disposition=delivery_disposition,
        numerical_disposition=numerical,
        observation_disposition=observation,
        termination=termination,
        truncation=truncation,
        backend=runtime_probe.backend,
        precision="float64",
        python_version=runtime_probe.python_version,
        numpy_version=runtime_probe.numpy_version,
        scipy_version=runtime_probe.scipy_version,
        xarray_version=runtime_probe.xarray_version,
        gymtorax_version=runtime_probe.gymtorax_version,
        torax_version=runtime_probe.torax_version,
        jax_version=runtime_probe.jax_version,
        jaxlib_version=runtime_probe.jaxlib_version,
        runtime_seconds=runtime_seconds,
        peak_rss_bytes=peak_rss_bytes,
        reason_codes=tuple(sorted(reasons)),
        outcome_access=request.outcome_access,
        evidence_ceiling=request.evidence_ceiling,
    )
    serialized_size = len(episode.canonical_bytes())
    if serialized_size > request.maximum_output_bytes:
        raise GymToraxOutputBoundError("GYM_TORAX_OUTPUT_BOUND_EXCEEDED")
    return episode


def encode_gym_torax_action_values(action: GymToraxNativeAction) -> npt.NDArray[np.float64]:
    return np.asarray(
        (
            float(action.ip_a),
            float(action.nbi_power_w),
            float(action.nbi_location),
            float(action.nbi_width),
            float(action.ecrh_power_w),
            float(action.ecrh_location),
            float(action.ecrh_width),
        ),
        dtype=np.float64,
    )
