"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from empirical_lawhood.domains.fusion.gym_torax_native.native_episode import encode_gym_torax_action_values, finalize_gym_torax_episode as _science_finalize_gym_torax_episode
from collections.abc import Callable, Mapping, Sequence
import copy
from decimal import Decimal
from importlib import metadata as importlib_metadata
from pathlib import Path
import resource
import sys
import time
from typing import Any, Protocol, cast
import numpy as np
import numpy.typing as npt
from empirical_lawhood.domains.fusion.gym_torax_native.diagnostic_contracts import GYM_TORAX_HORIZON_REQUESTS, GymToraxActionDelivery, GymToraxDeliveryDisposition, GymToraxNativeAction, GymToraxNumericalDisposition, GymToraxNumericalMember, GymToraxObservationDisposition, GymToraxPreparation
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata_contracts import GymToraxFieldMetadataEpisodeRequest, GymToraxFieldMetadataNativeEpisode
from empirical_lawhood.domains.fusion.gym_torax_native.field_metadata import GymToraxFieldMetadataManifest
from empirical_lawhood.adapters.simulators.gym_torax_native.field_metadata import verify_installed_gym_torax_metadata_sources
from empirical_lawhood.domains.fusion.gym_torax_native.extraction_manifest import GymToraxBoundedExtractionManifest
from empirical_lawhood.adapters.simulators.gym_torax_native.extraction_manifest import verify_gym_torax_extraction_manifest

from empirical_lawhood.domains.fusion.gym_torax_native.native_episode import (
    GymToraxCapturedState as _science_GymToraxCapturedState,
    GymToraxOperatorSnapshot as _science_GymToraxOperatorSnapshot,
    GymToraxOutputBoundError as _science_GymToraxOutputBoundError,
    GymToraxRuntimePreflightError as _science_GymToraxRuntimePreflightError,
    GymToraxRuntimeProbe as _science_GymToraxRuntimeProbe,
    _ACTION_COMPONENT_IDS,
    _MINIMUM_EPISODE_ENVELOPE_BYTES,
    _REQUIRED_PROFILES,
    _REQUIRED_SCALARS,
    _reason_token,
    _reserve_capture_before_append,
    _reserve_operator_before_append,
    _validate_exact_native_schedule,
    _validate_extraction_binding,
    _validate_field_metadata_binding,
    _validate_operator_snapshot,
    _validate_runtime_probe,
)

_NUMERICS_FIELDS = (
    "inner_solver_iterations",
    "outer_solver_iterations",
    "sawtooth_crash",
    "solver_error_state",
)

_OPERATOR_REQUEST_CLOCKS = frozenset(range(104, 110))

_MAX_CAPTURED_ARRAY_ELEMENTS = 2_000_000

class GymToraxEnvironment(Protocol):
    """Minimal injected environment surface used by acquisition."""

    @property
    def current_time(self) -> object: ...

    @property
    def state(self) -> object: ...

    def reset(self, *, seed: int) -> object: ...

    def step(self, action: Mapping[str, npt.NDArray[np.float64]]) -> object: ...

    def close(self) -> object: ...

GymToraxEnvironmentFactory = Callable[
    [GymToraxPreparation, GymToraxNumericalMember], GymToraxEnvironment
]

GymToraxRuntimeInspector = Callable[[], _science_GymToraxRuntimeProbe]

GymToraxProgressCallback = Callable[[Decimal], None]

GymToraxResetObserver = Callable[[], None]

class GymToraxProgressEmissionError(RuntimeError):
    """The executor's monotone progress port rejected a completed clock."""

def _emit_completed_clock_progress(
    callback: GymToraxProgressCallback | None,
    receiver_clock: int,
) -> None:
    if callback is None:
        return
    try:
        # Counter zero is reserved for "no completed work".  Reset clock zero
        # therefore advances to one, followed by receiver clocks 1--120 as
        # counters 2--121.
        callback(Decimal(receiver_clock + 1))
    except Exception as error:
        raise GymToraxProgressEmissionError(
            "native receiver-clock progress could not be emitted"
        ) from error

def inspect_gym_torax_runtime() -> _science_GymToraxRuntimeProbe:
    """Late-import JAX and bind the exact CPU/float64 source denominator."""

    import jax

    jax_config = cast(Any, jax.config)
    jax_config.update("jax_platforms", "cpu")
    jax_config.update("jax_enable_x64", True)
    return _science_GymToraxRuntimeProbe(
        python_version=(
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        ),
        numpy_version=importlib_metadata.version("numpy"),
        scipy_version=importlib_metadata.version("scipy"),
        xarray_version=importlib_metadata.version("xarray"),
        gymtorax_version=importlib_metadata.version("gymtorax"),
        torax_version=importlib_metadata.version("torax"),
        jax_version=importlib_metadata.version("jax"),
        jaxlib_version=importlib_metadata.version("jaxlib"),
        backend=str(jax.default_backend()),
        x64_enabled=bool(jax_config.read("jax_enable_x64")),
    )

def _scale_profile(profile: object, scale: float) -> object:
    result = copy.deepcopy(profile)
    if not isinstance(result, Mapping):
        raise TypeError("Gym--TORAX source profile is not a radial mapping")
    for radial_values in result.values():
        if not isinstance(radial_values, Mapping):
            raise TypeError("Gym--TORAX radial profile is not a mapping")
        mutable = cast(dict[object, object], radial_values)
        for radius in tuple(mutable):
            if float(cast(Any, radius)) < 1.0:
                mutable[radius] = float(cast(Any, mutable[radius])) * scale
    return result

def _build_gym_torax_environment_after_preflight(
    preparation: GymToraxPreparation,
    numerical_member: GymToraxNumericalMember,
) -> GymToraxEnvironment:
    from gymtorax.envs.iter_hybrid_env import (  # type: ignore[import-untyped]
        CONFIG,
        IterHybridEnv,
    )

    source_config = copy.deepcopy(CONFIG)
    source_config["numerics"]["t_final"] = GYM_TORAX_HORIZON_REQUESTS
    source_config["numerics"]["fixed_dt"] = float(numerical_member.internal_timestep_s)
    source_config["geometry"]["n_rho"] = numerical_member.radial_cells
    source_config["solver"]["n_corrector_steps"] = numerical_member.corrector_steps
    for field_id in ("T_i", "T_e"):
        source_config["profile_conditions"][field_id] = _scale_profile(
            source_config["profile_conditions"][field_id],
            float(preparation.initial_temperature_scale),
        )
    source_config["profile_conditions"]["nbar"] = float(preparation.initial_density_nbar)
    source_config["neoclassical"]["bootstrap_current"]["bootstrap_multiplier"] = float(
        preparation.bootstrap_multiplier
    )
    for field_id in ("D_e_inner", "chi_i_inner", "chi_e_inner"):
        source_config["transport"][field_id] = float(source_config["transport"][field_id]) * float(
            preparation.inner_transport_scale
        )

    class GymToraxEnvironment(IterHybridEnv):  # type: ignore[misc]
        def _get_torax_config(self) -> dict[str, Any]:
            return {
                "config": source_config,
                "discretization": "fixed",
                "ratio_a_sim": int(round(1.0 / float(numerical_member.internal_timestep_s))),
            }

        def _compute_reward(self, state: object, next_state: object, action: object) -> float:
            del state, next_state, action
            return 0.0

    return cast(
        GymToraxEnvironment,
        GymToraxEnvironment(render_mode=None, store_history=False, log_level="warning"),
    )

def build_gym_torax_environment(
    preparation: GymToraxPreparation,
    numerical_member: GymToraxNumericalMember,
    *,
    runtime_inspector: GymToraxRuntimeInspector = inspect_gym_torax_runtime,
) -> GymToraxEnvironment:
    """Construct the exact source environment only after denominator preflight."""

    _validate_runtime_probe(runtime_inspector())
    return _build_gym_torax_environment_after_preflight(preparation, numerical_member)

class GymToraxNativeActionCodec:
    """Exact native Gym--TORAX action translation without semantic aliases."""

    component_ids = _ACTION_COMPONENT_IDS


    @staticmethod
    def mapping(
        action: GymToraxNativeAction,
    ) -> dict[str, npt.NDArray[np.float64]]:
        values = encode_gym_torax_action_values(action)
        return {
            "Ip": values[0:1].copy(),
            "NBI": values[1:4].copy(),
            "ECRH": values[4:7].copy(),
        }

    @staticmethod
    def decode(values: Mapping[str, object]) -> GymToraxNativeAction:
        ip = _finite_vector(values["Ip"], expected_size=1)
        nbi = _finite_vector(values["NBI"], expected_size=3)
        ecrh = _finite_vector(values["ECRH"], expected_size=3)
        return GymToraxNativeAction(
            ip_a=_decimal(ip[0]),
            nbi_power_w=_decimal(nbi[0]),
            nbi_location=_decimal(nbi[1]),
            nbi_width=_decimal(nbi[2]),
            ecrh_power_w=_decimal(ecrh[0]),
            ecrh_location=_decimal(ecrh[1]),
            ecrh_width=_decimal(ecrh[2]),
        )

def _decimal(value: np.float64) -> Decimal:
    return Decimal(str(float(value)))

def _finite_vector(value: object, *, expected_size: int) -> npt.NDArray[np.float64]:
    array = np.asarray(value, dtype=np.float64).reshape(-1)
    if array.size != expected_size or not np.isfinite(array).all():
        raise ValueError("native action stage has invalid shape or nonfinite values")
    return array

def _as_mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError("Gym--TORAX source value is not a mapping")
    if not all(isinstance(key, str) for key in value):
        raise TypeError("Gym--TORAX source mapping has a non-string key")
    return cast(Mapping[str, object], value)

def _bounded_array(value: object) -> npt.NDArray[np.float64]:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim == 0:
        array = array.reshape(1)
    if array.size > _MAX_CAPTURED_ARRAY_ELEMENTS:
        raise ValueError("source array exceeds the in-memory capture bound")
    return np.ascontiguousarray(array, dtype=np.float64)

def _native_numerics(environment: GymToraxEnvironment) -> Mapping[str, object]:
    app = getattr(environment, "torax_app", None)
    current = getattr(app, "current_sim_state", None)
    outputs = getattr(current, "solver_numeric_outputs", None)
    if outputs is None:
        return {}
    return {
        field_id: value
        for field_id in _NUMERICS_FIELDS
        if (value := getattr(outputs, field_id, None)) is not None
    }

def _source_dimensions(
    environment: GymToraxEnvironment,
) -> tuple[
    Mapping[tuple[str, str], tuple[str, ...]],
    Mapping[str, npt.NDArray[np.float64]],
]:
    provider = getattr(environment, 'source_dimensions', None)
    if callable(provider):
        raw_dimensions, raw_coordinates = provider()
        return cast(Mapping[tuple[str, str], tuple[str, ...]], raw_dimensions), {
            str(key): _bounded_array(value).reshape(-1)
            for key, value in _as_mapping(raw_coordinates).items()
        }
    app = getattr(environment, "torax_app", None)
    getter = getattr(app, "get_state_data", None)
    if not callable(getter):
        return {}, {}
    tree = getter()
    dimensions_by_field: dict[tuple[str, str], tuple[str, ...]] = {}
    for category in ("profiles", "scalars"):
        dataset = tree[f"/{category}/"].ds
        variables = dataset.variables
        coordinate_names = set(dataset.coords)
        for field_id, variable in variables.items():
            if field_id in coordinate_names:
                continue
            dimensions = tuple(str(value) for value in variable.dims)
            native_dimensions = dimensions[1:] if dimensions[:1] == ("time",) else dimensions
            dimensions_by_field[(category, str(field_id))] = (
                ("value",) if category == "scalars" and not native_dimensions else native_dimensions
            )
    coordinates = {
        str(name): _bounded_array(value.values).reshape(-1)
        for name, value in tree.coords.items()
        if str(name) in {"rho_norm", "rho_face_norm", "rho_cell_norm"}
    }
    return dimensions_by_field, coordinates

def capture_gym_torax_state(
    environment: GymToraxEnvironment,
    field_metadata_manifest: GymToraxFieldMetadataManifest,
) -> _science_GymToraxCapturedState:
    """Capture only the frozen retained fields and their source dimensions."""

    reasons: set[str] = set()
    state = _as_mapping(environment.state or {})
    profiles_raw = _as_mapping(state.get("profiles", {}))
    scalars_raw = _as_mapping(state.get("scalars", {}))
    dimensions_raw, coordinates = _source_dimensions(environment)
    dimensions = dict(dimensions_raw)
    retained = field_metadata_manifest.by_key()

    def capture_category(
        category: str,
        values: Mapping[str, object],
    ) -> dict[str, npt.NDArray[np.float64]]:
        result: dict[str, npt.NDArray[np.float64]] = {}
        expected_ids = sorted(
            field_id for source_category, field_id in retained if source_category == category
        )
        for field_id in expected_ids:
            if field_id not in values:
                reasons.add(f"SOURCE_FIELD_MISSING_{_reason_token(field_id)}")
                continue
            try:
                result[field_id] = _bounded_array(values[field_id])
            except (TypeError, ValueError, OverflowError):
                reasons.add(f"SOURCE_FIELD_INVALID_{_reason_token(field_id)}")
        return result

    numerics_raw = state.get("numerics")
    numerics = capture_category(
        "numerics",
        _as_mapping(numerics_raw) if numerics_raw is not None else _native_numerics(environment),
    )
    for field_id in numerics:
        dimensions.setdefault(("numerics", field_id), ("value",))
    return _science_GymToraxCapturedState(
        profiles=capture_category("profiles", profiles_raw),
        scalars=capture_category("scalars", scalars_raw),
        numerics=numerics,
        dimensions=dimensions,
        coordinates=coordinates,
        reason_codes=tuple(sorted(reasons)),
    )

def _environment_clock(environment: GymToraxEnvironment) -> int:
    value = float(cast(Any, environment.current_time))
    rounded = int(round(value))
    if not np.isfinite(value) or abs(value - rounded) > 1e-9:
        raise ValueError("native environment clock is not an exact integer")
    return rounded

def _decode_action_or_none(value: object) -> GymToraxNativeAction | None:
    try:
        return GymToraxNativeActionCodec.decode(_as_mapping(value))
    except (KeyError, TypeError, ValueError, OverflowError):
        return None

def _applied_action(
    environment: GymToraxEnvironment, info: Mapping[str, object]
) -> GymToraxNativeAction | None:
    if "applied_action" in info:
        return _decode_action_or_none(info["applied_action"])
    app = getattr(environment, "torax_app", None)
    config = getattr(app, "config", None)
    getter = getattr(config, "get_current_action_values", None)
    return _decode_action_or_none(getter()) if callable(getter) else None

def _realized_action(
    environment: GymToraxEnvironment,
    info: Mapping[str, object],
    applied: GymToraxNativeAction | None,
) -> GymToraxNativeAction | None:
    if "realized_action" in info:
        return _decode_action_or_none(info["realized_action"])
    if applied is None:
        return None
    try:
        state = _as_mapping(environment.state or {})
        scalars = _as_mapping(state.get("scalars", {}))
        ip = _finite_vector(scalars["Ip"], expected_size=1)[0]
        nbi = _finite_vector(scalars["P_aux_generic_total"], expected_size=1)[0]
        ecrh = _finite_vector(scalars["P_ecrh_e"], expected_size=1)[0]
        return GymToraxNativeAction(
            ip_a=_decimal(ip),
            nbi_power_w=_decimal(nbi),
            nbi_location=applied.nbi_location,
            nbi_width=applied.nbi_width,
            ecrh_power_w=_decimal(ecrh),
            ecrh_location=applied.ecrh_location,
            ecrh_width=applied.ecrh_width,
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return None

def _operator_snapshot(
    environment: GymToraxEnvironment,
    *,
    request_clock: int,
    action_mapping: Mapping[str, npt.NDArray[np.float64]],
) -> _science_GymToraxOperatorSnapshot | None:
    provider = _operator_provider(environment)
    if not callable(provider):
        return None
    raw = provider(request_clock, action_mapping)
    if isinstance(raw, _science_GymToraxOperatorSnapshot):
        snapshot = raw
    else:
        values = _as_mapping(raw)
        snapshot = _science_GymToraxOperatorSnapshot(
            request_clock=request_clock,
            source_method_id=str(values["source_method_id"]),
            state_coordinate_ids=tuple(cast(Sequence[str], values["state_coordinate_ids"])),
            input_coordinate_ids=tuple(cast(Sequence[str], values["input_coordinate_ids"])),
            receiver_coordinate_ids=tuple(cast(Sequence[str], values["receiver_coordinate_ids"])),
            transition_a=_bounded_array(values["A"]),
            input_b=_bounded_array(values["B"]),
            receiver_c=_bounded_array(values["C"]),
        )
    _validate_operator_snapshot(snapshot, expected_clock=request_clock)
    return snapshot

def _operator_provider(environment: GymToraxEnvironment) -> object:
    provider = getattr(environment, "capture_controlled_input_output_operators", None)
    if callable(provider):
        return provider
    app = getattr(environment, "torax_app", None)
    return getattr(app, "capture_controlled_input_output_operators", None)

def _peak_rss_bytes() -> int:
    observed = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return observed if sys.platform == "darwin" else observed * 1024

def acquire_gym_torax_episode(
    request: GymToraxFieldMetadataEpisodeRequest,
    *,
    extraction_manifest: GymToraxBoundedExtractionManifest,
    field_metadata_manifest: GymToraxFieldMetadataManifest,
    repository_root: Path,
    environment_factory: GymToraxEnvironmentFactory | None = None,
    runtime_inspector: GymToraxRuntimeInspector = inspect_gym_torax_runtime,
    progress_callback: GymToraxProgressCallback | None = None,
    source_reset_observer: GymToraxResetObserver | None = None,
) -> GymToraxFieldMetadataNativeEpisode:
    """Acquire one exact reset plus 120-request native episode.

    Runtime qualification always precedes environment construction.  All
    scientific outcomes remain source observations; this function neither
    retries nor adjudicates them.
    """

    _validate_exact_native_schedule(request)
    _validate_extraction_binding(request, extraction_manifest)
    _validate_field_metadata_binding(request, field_metadata_manifest)
    try:
        verify_gym_torax_extraction_manifest(
            extraction_manifest,
            expected_identity=request.extraction_manifest,
            repository_root=repository_root,
        )
    except (OSError, ValueError) as error:
        raise _science_GymToraxRuntimePreflightError(("SURGICAL_EXTRACTION_SOURCE_DIVERGENCE",)) from error
    verify_installed_gym_torax_metadata_sources(field_metadata_manifest)
    probe = runtime_inspector()
    _validate_runtime_probe(probe)
    if request.maximum_output_bytes <= _MINIMUM_EPISODE_ENVELOPE_BYTES:
        raise _science_GymToraxOutputBoundError("GYM_TORAX_OUTPUT_BOUND_EXCEEDED")
    factory = environment_factory or _build_gym_torax_environment_after_preflight
    started = time.monotonic()
    reasons: set[str] = set()
    state_clocks: list[int] = []
    captures: list[_science_GymToraxCapturedState] = []
    deliveries: list[GymToraxActionDelivery] = []
    operator_snapshots: list[_science_GymToraxOperatorSnapshot] = []
    operator_api_exposed = False
    environment: GymToraxEnvironment | None = None
    source_reset_attempted = False
    numerical = GymToraxNumericalDisposition.VALID
    observation = GymToraxObservationDisposition.COMPLETE
    termination = False
    truncation = False
    capture_reserved_bytes = _MINIMUM_EPISODE_ENVELOPE_BYTES
    output_bound_error: _science_GymToraxOutputBoundError | None = None
    try:
        environment = factory(request.preparation, request.numerical_member)
        operator_api_exposed = callable(_operator_provider(environment))
        if source_reset_observer is not None:
            source_reset_observer()
        source_reset_attempted = True
        environment.reset(seed=request.preparation.environment_seed)
        if _environment_clock(environment) != 0:
            reasons.add("NATIVE_RESET_CLOCK_DIVERGENCE")
            observation = GymToraxObservationDisposition.UNEVALUABLE
        else:
            initial_capture = capture_gym_torax_state(
                environment,
                field_metadata_manifest,
            )
            capture_reserved_bytes = _reserve_capture_before_append(
                initial_capture,
                reserved_bytes=capture_reserved_bytes,
                maximum_bytes=request.maximum_output_bytes,
                include_coordinates=True,
            )
            captures.append(initial_capture)
            state_clocks.append(0)
            _emit_completed_clock_progress(progress_callback, 0)
        for row in request.schedule.rows:
            if observation is GymToraxObservationDisposition.UNEVALUABLE:
                break
            if _environment_clock(environment) != row.request_clock:
                reasons.add("NATIVE_CLOCK_DIVERGENCE")
                observation = GymToraxObservationDisposition.PARTIAL
                break
            action_mapping = GymToraxNativeActionCodec.mapping(row.action)
            if row.request_clock in _OPERATOR_REQUEST_CLOCKS:
                try:
                    snapshot = _operator_snapshot(
                        environment,
                        request_clock=row.request_clock,
                        action_mapping=action_mapping,
                    )
                    if snapshot is not None:
                        capture_reserved_bytes = _reserve_operator_before_append(
                            snapshot,
                            reserved_bytes=capture_reserved_bytes,
                            maximum_bytes=request.maximum_output_bytes,
                        )
                        operator_snapshots.append(snapshot)
                except (KeyError, TypeError, ValueError, OverflowError):
                    reasons.add("OPERATOR_SOURCE_INVALID")
            raw_step = environment.step(action_mapping)
            if not isinstance(raw_step, tuple) or len(raw_step) != 5:
                raise TypeError("Gym--TORAX step result is not the five-field Gym surface")
            _, reward_raw, terminated_raw, truncated_raw, info_raw = raw_step
            info = _as_mapping(info_raw)
            rejected = bool(info.get("action_rejected", False))
            accepted = (
                None
                if rejected
                else _decode_action_or_none(info["accepted_action"])
                if "accepted_action" in info
                else row.action
            )
            applied = _applied_action(environment, info)
            realized = _realized_action(environment, info, applied)
            clipped = bool(info.get("action_clipped", False))
            delivery_reasons: set[str] = set()
            if rejected:
                disposition = GymToraxDeliveryDisposition.REJECTED
                delivery_reasons.add("ACTION_REJECTED")
            elif accepted is None or applied is None or realized is None:
                disposition = GymToraxDeliveryDisposition.PARTIAL
                delivery_reasons.add("ACTION_STAGE_UNAVAILABLE")
            elif clipped:
                disposition = GymToraxDeliveryDisposition.CLIPPED
                delivery_reasons.add("ACTION_CLIPPED")
            else:
                disposition = GymToraxDeliveryDisposition.COMPLETE
            deliveries.append(
                GymToraxActionDelivery(
                    delivery_id=f"delivery.{request.request_id.removeprefix('request.')}.{row.request_clock:04d}",
                    request_clock=row.request_clock,
                    receiver_clock=row.request_clock + 1,
                    occurrence_id=row.controlled_occurrence_id,
                    requested=row.action,
                    accepted=accepted,
                    applied=applied,
                    realized=realized,
                    disposition=disposition,
                    reason_codes=tuple(sorted(delivery_reasons)),
                )
            )
            reasons.update(delivery_reasons)
            receiver_clock = row.request_clock + 1
            if _environment_clock(environment) != receiver_clock:
                reasons.add("NATIVE_RECEIVER_CLOCK_DIVERGENCE")
                observation = GymToraxObservationDisposition.PARTIAL
                break
            capture = capture_gym_torax_state(
                environment,
                field_metadata_manifest,
            )
            capture_reserved_bytes = _reserve_capture_before_append(
                capture,
                reserved_bytes=capture_reserved_bytes,
                maximum_bytes=request.maximum_output_bytes,
                include_coordinates=False,
            )
            captures.append(capture)
            state_clocks.append(receiver_clock)
            _emit_completed_clock_progress(progress_callback, receiver_clock)
            decisive_scalars = {
                field_id: value
                for field_id, value in capture.scalars.items()
                if field_id in _REQUIRED_SCALARS
            }
            decisive_profiles = {
                field_id: value
                for field_id, value in capture.profiles.items()
                if field_id in _REQUIRED_PROFILES
            }
            if any(
                not np.isfinite(value).all()
                for value in (*decisive_scalars.values(), *decisive_profiles.values())
            ):
                numerical = GymToraxNumericalDisposition.INVALID
                reasons.add("NONFINITE_REQUIRED_STATE")
            solver_error = capture.numerics.get("solver_error_state")
            if float(cast(Any, reward_raw)) == -1000.0 or (
                solver_error is not None and np.any(solver_error != 0.0)
            ):
                numerical = GymToraxNumericalDisposition.SOLVER_FAILURE
                reasons.add("SOLVER_FAILURE")
            terminated_now = bool(terminated_raw)
            truncated_now = bool(truncated_raw)
            if terminated_now or truncated_now:
                if receiver_clock < GYM_TORAX_HORIZON_REQUESTS:
                    termination = terminated_now
                    truncation = truncated_now
                    reasons.add(
                        "SIMULATOR_TERMINATED_BEFORE_HORIZON"
                        if terminated_now
                        else "SIMULATOR_TRUNCATED_BEFORE_HORIZON"
                    )
                    observation = GymToraxObservationDisposition.PARTIAL
                break
    except GymToraxProgressEmissionError:
        raise
    except _science_GymToraxOutputBoundError as error:
        output_bound_error = error
    except Exception as error:
        reasons.add(
            f"SIMULATOR_{type(error).__name__.upper()}"
            if state_clocks
            else f"TECHNICAL_INITIALIZATION_{type(error).__name__.upper()}"
        )
        if state_clocks:
            numerical = GymToraxNumericalDisposition.SOLVER_FAILURE
            observation = GymToraxObservationDisposition.PARTIAL
        else:
            numerical = GymToraxNumericalDisposition.UNEVALUABLE
            observation = GymToraxObservationDisposition.UNEVALUABLE
    finally:
        if environment is not None:
            try:
                environment.close()
            except Exception as error:
                reasons.add(f"CLEANUP_{type(error).__name__.upper()}")
    if output_bound_error is not None:
        raise output_bound_error

    return _science_finalize_gym_torax_episode(
        request=request,
        extraction_manifest=extraction_manifest,
        field_metadata_manifest=field_metadata_manifest,
        runtime_probe=probe,
        source_reset_attempted=source_reset_attempted,
        state_clocks=state_clocks,
        captures=captures,
        deliveries=deliveries,
        operator_snapshots=operator_snapshots,
        operator_api_exposed=operator_api_exposed,
        reason_codes=tuple(reasons),
        termination=termination,
        truncation=truncation,
        runtime_seconds=Decimal(f"{time.monotonic() - started:.9f}"),
        peak_rss_bytes=_peak_rss_bytes(),
        initial_numerical_disposition=numerical,
        initial_observation_disposition=observation,
    )
