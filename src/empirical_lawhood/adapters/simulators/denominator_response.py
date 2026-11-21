# SPDX-License-Identifier: MPL-2.0
"""Native Gym--TORAX denominator acquisition and external representation conversion.

Scientific qualification contracts, frozen cohorts and adjudication have their
canonical owner in domains.fusion.denominator_response. This adapter performs
actual simulator contact and converts native observations without a scheduler.
"""

from __future__ import annotations

import base64

import copy

import hashlib

import time

from decimal import Decimal

from typing import Any, Mapping, Sequence

import numpy as np

import numpy.typing as npt

from empirical_lawhood.science.identity.provenance import ObjectIdentity

from empirical_lawhood.domains.fusion.prepared_base import EpisodeDisposition

from empirical_lawhood.domains.fusion.denominator_response import DENOMINATOR_RESPONSE_HORIZON_S, DENOMINATOR_RESPONSE_COMMON_GRID_POINTS, DenominatorResponseCell, DenominatorResponseNumericalView, DenominatorResponseNativeAction, DenominatorResponseQualificationConfig, DenominatorResponseFloat64Block, DenominatorResponseCapturedEpisode, receiver_groups, plan_time_source_inventory

def _float64_block(
    *,
    category: str,
    native_field_id: str,
    native_unit: str,
    dimension_ids: tuple[str, ...],
    values: npt.ArrayLike,
    clock_s: tuple[int, ...] = (),
) -> DenominatorResponseFloat64Block:
    array = np.ascontiguousarray(values, dtype="<f8")
    if array.ndim == 0:
        array = array.reshape(1)
    payload = array.tobytes(order="C")
    token = hashlib.sha256(f"{category}\0{native_field_id}".encode("utf-8")).hexdigest()[:24]
    finite_count = int(np.isfinite(array).sum())
    return DenominatorResponseFloat64Block(
        block_id=f"block.denominator-response.{token}",
        category=category,
        native_field_id=native_field_id,
        native_unit=native_unit or "source-unit-unspecified",
        dimension_ids=dimension_ids,
        shape=tuple(int(value) for value in array.shape),
        clock_s=clock_s,
        data_base64=base64.b64encode(payload).decode("ascii"),
        data_sha256=hashlib.sha256(payload).hexdigest(),
        finite_value_count=finite_count,
        nonfinite_value_count=array.size - finite_count,
    )

def _scale_profile(profile: Any, scale: float) -> Any:
    result = copy.deepcopy(profile)
    for radial_values in result.values():
        for radius in tuple(radial_values):
            if float(radius) < 1.0:
                radial_values[radius] = float(radial_values[radius]) * scale
    return result

def _environment(cell: DenominatorResponseCell, view: DenominatorResponseNumericalView) -> Any:
    from gymtorax.envs.iter_hybrid_env import (  # type: ignore[import-untyped]
        CONFIG,
        IterHybridEnv,
    )

    source_config = copy.deepcopy(CONFIG)
    source_config["numerics"]["t_final"] = DENOMINATOR_RESPONSE_HORIZON_S
    source_config["numerics"]["fixed_dt"] = float(view.internal_timestep_s)
    source_config["geometry"]["n_rho"] = view.radial_cells
    source_config["solver"]["n_corrector_steps"] = view.corrector_steps
    source_config["profile_conditions"]["T_i"] = _scale_profile(
        source_config["profile_conditions"]["T_i"],
        float(cell.initial_temperature_scale),
    )
    source_config["profile_conditions"]["T_e"] = _scale_profile(
        source_config["profile_conditions"]["T_e"],
        float(cell.initial_temperature_scale),
    )
    source_config["profile_conditions"]["nbar"] = float(cell.initial_density_nbar)
    source_config["neoclassical"]["bootstrap_current"]["bootstrap_multiplier"] = float(
        cell.bootstrap_multiplier
    )
    for key in ("D_e_inner", "chi_i_inner", "chi_e_inner"):
        source_config["transport"][key] = float(source_config["transport"][key]) * float(
            cell.inner_transport_scale
        )

    class DenominatorResponseEnvironment(IterHybridEnv):  # type: ignore[misc]
        def _get_torax_config(self) -> dict[str, Any]:
            return {
                "config": source_config,
                "discretization": "fixed",
                "ratio_a_sim": int(round(1.0 / float(view.internal_timestep_s))),
            }

        def _compute_reward(self, state: Any, next_state: Any, action: Any) -> float:
            del state, next_state, action
            return 0.0

    return DenominatorResponseEnvironment(render_mode=None, store_history=False, log_level="warning")

def _action_array(action: DenominatorResponseNativeAction) -> npt.NDArray[np.float64]:
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

def _action_mapping(
    action: DenominatorResponseNativeAction,
) -> dict[str, npt.NDArray[np.float64]]:
    return {
        "Ip": np.asarray((float(action.ip_a),), dtype=np.float64),
        "NBI": np.asarray(
            (
                float(action.nbi_power_w),
                float(action.nbi_location),
                float(action.nbi_width),
            ),
            dtype=np.float64,
        ),
        "ECRH": np.asarray(
            (
                float(action.ecrh_power_w),
                float(action.ecrh_location),
                float(action.ecrh_width),
            ),
            dtype=np.float64,
        ),
    }

def _native_action(values: Mapping[str, Any]) -> DenominatorResponseNativeAction:
    ip = np.asarray(values["Ip"], dtype=np.float64).reshape(-1)
    nbi = np.asarray(values["NBI"], dtype=np.float64).reshape(-1)
    ecrh = np.asarray(values["ECRH"], dtype=np.float64).reshape(-1)
    return DenominatorResponseNativeAction(
        ip_a=Decimal(str(float(ip[0]))),
        nbi_power_w=Decimal(str(float(nbi[0]))),
        nbi_location=Decimal(str(float(nbi[1]))),
        nbi_width=Decimal(str(float(nbi[2]))),
        ecrh_power_w=Decimal(str(float(ecrh[0]))),
        ecrh_location=Decimal(str(float(ecrh[1]))),
        ecrh_width=Decimal(str(float(ecrh[2]))),
    )

def _state_scalar(state: Mapping[str, Any], field_id: str) -> Decimal | None:
    raw = state.get("scalars", {}).get(field_id)
    if raw is None:
        return None
    values = np.asarray(raw, dtype=np.float64).reshape(-1)
    if values.size != 1:
        return None
    return Decimal(str(float(values[0])))

def _realized_action(environment: Any, applied: DenominatorResponseNativeAction) -> DenominatorResponseNativeAction:
    state = environment.state or {}
    ip = _state_scalar(state, "Ip")
    nbi = _state_scalar(state, "P_aux_generic_total")
    ecrh = _state_scalar(state, "P_ecrh_e")
    return DenominatorResponseNativeAction(
        ip_a=applied.ip_a if ip is None else ip,
        nbi_power_w=applied.nbi_power_w if nbi is None else nbi,
        nbi_location=applied.nbi_location,
        nbi_width=applied.nbi_width,
        ecrh_power_w=applied.ecrh_power_w if ecrh is None else ecrh,
        ecrh_location=applied.ecrh_location,
        ecrh_width=applied.ecrh_width,
    )

def _source_metadata(
    environment: Any,
) -> tuple[
    dict[tuple[str, str], tuple[str, tuple[str, ...]]],
    dict[str, npt.NDArray[np.float64]],
]:
    """Read the source schema once; receiver values continue through ``state``."""

    tree = environment.torax_app.get_state_data()
    metadata: dict[tuple[str, str], tuple[str, tuple[str, ...]]] = {}
    for category in ("profiles", "scalars"):
        dataset = tree[f"/{category}/"].ds
        variables = dataset.variables
        coordinate_names = set(dataset.coords)
        for field_id, variable in variables.items():
            if field_id in coordinate_names:
                continue
            unit = str(
                variable.attrs.get(
                    "units",
                    variable.attrs.get("unit", "source-unit-unspecified"),
                )
            )
            dimensions = tuple(str(value) for value in variable.dims)
            if dimensions and dimensions[0] != "time":
                species_dimension = dimensions[0]
                labels = (
                    variables[species_dimension].values
                    if species_dimension in variables
                    else np.arange(variable.shape[0])
                )
                for index in range(variable.shape[0]):
                    split_id = f"{field_id}_{str(labels[index])}"
                    metadata[(category, split_id)] = (
                        unit,
                        dimensions[2:] if dimensions[1:2] == ("time",) else dimensions[1:],
                    )
            else:
                metadata[(category, field_id)] = (
                    unit,
                    dimensions[1:] if dimensions[:1] == ("time",) else dimensions,
                )
    coordinates = {
        str(name): np.asarray(value.values, dtype=np.float64).reshape(-1)
        for name, value in tree.coords.items()
        if str(name) in {"rho_norm", "rho_face_norm", "rho_cell_norm"}
    }
    return metadata, coordinates

def _capture_state(
    state: Mapping[str, Any],
    *,
    metadata: Mapping[tuple[str, str], tuple[str, tuple[str, ...]]],
    field_values: dict[tuple[str, str], list[npt.NDArray[np.float64]]],
    expected_shapes: dict[tuple[str, str], tuple[int, ...]],
    reason_codes: set[str],
) -> None:
    for category in ("profiles", "scalars"):
        observed = state.get(category, {})
        for field_id, raw in observed.items():
            key = (category, str(field_id))
            array = np.asarray(raw, dtype=np.float64)
            if array.ndim == 0:
                array = array.reshape(1)
            shape = tuple(int(value) for value in array.shape)
            if key not in expected_shapes:
                expected_shapes[key] = shape
                field_values[key] = []
            if shape != expected_shapes[key]:
                reason_codes.add("SOURCE_FIELD_SHAPE_DRIFT")
                array = np.full(expected_shapes[key], np.nan, dtype=np.float64)
            field_values[key].append(np.ascontiguousarray(array, dtype=np.float64))
        missing = set(expected_shapes).difference(
            (category, str(field_id)) for field_id in observed
        )
        for key in missing:
            if key[0] != category:
                continue
            reason_codes.add("SOURCE_FIELD_MISSING_AFTER_INITIALIZATION")
            field_values[key].append(np.full(expected_shapes[key], np.nan, dtype=np.float64))
    unknown_metadata = set(field_values).difference(metadata)
    if unknown_metadata:
        reason_codes.add("SOURCE_FIELD_METADATA_UNAVAILABLE")

def _numerics_values(environment: Any) -> dict[str, npt.NDArray[np.float64]]:
    current = environment.torax_app.current_sim_state
    if current is None:
        return {}
    outputs = current.solver_numeric_outputs
    result = {}
    for field_id in (
        "inner_solver_iterations",
        "outer_solver_iterations",
        "sawtooth_crash",
    ):
        raw = getattr(outputs, field_id, None)
        if raw is not None:
            result[field_id] = np.asarray(raw, dtype=np.float64).reshape(-1)
    return result

def _make_state_blocks(
    *,
    state_clock_s: tuple[int, ...],
    metadata: Mapping[tuple[str, str], tuple[str, tuple[str, ...]]],
    coordinates: Mapping[str, npt.NDArray[np.float64]],
    field_values: Mapping[tuple[str, str], list[npt.NDArray[np.float64]]],
    numerics_values: Mapping[str, list[npt.NDArray[np.float64]]],
    requested: Sequence[DenominatorResponseNativeAction],
    accepted: Sequence[DenominatorResponseNativeAction],
    applied: Sequence[DenominatorResponseNativeAction],
    realized: Sequence[DenominatorResponseNativeAction],
    reason_codes: set[str],
) -> tuple[DenominatorResponseFloat64Block, ...]:
    blocks: list[DenominatorResponseFloat64Block] = []
    for coordinate_id, coordinate_values in sorted(coordinates.items()):
        blocks.append(
            _float64_block(
                category="coordinate",
                native_field_id=coordinate_id,
                native_unit="1",
                dimension_ids=(coordinate_id,),
                values=coordinate_values,
            )
        )
    for (category, field_id), captured_values in sorted(field_values.items()):
        if len(captured_values) != len(state_clock_s):
            reason_codes.add("SOURCE_FIELD_CLOCK_COUNT_MISMATCH")
            continue
        unit, dimensions = metadata.get(
            (category, field_id),
            (
                "source-unit-unspecified",
                tuple(f"axis_{i}" for i in range(captured_values[0].ndim)),
            ),
        )
        if category == "scalars" and not dimensions and captured_values[0].ndim == 1:
            dimensions = ("value",)
        if len(dimensions) != captured_values[0].ndim:
            reason_codes.add("SOURCE_FIELD_DIMENSION_METADATA_MISMATCH")
            dimensions = tuple(f"source_axis_{index}" for index in range(captured_values[0].ndim))
        stacked = np.stack(captured_values)
        blocks.append(
            _float64_block(
                category=f"source-{category.removesuffix('s')}",
                native_field_id=field_id,
                native_unit=unit,
                dimension_ids=("clock_s", *dimensions),
                values=stacked,
                clock_s=state_clock_s,
            )
        )
    for field_id, captured_numerics in sorted(numerics_values.items()):
        if len(captured_numerics) != len(state_clock_s):
            reason_codes.add("NUMERICS_FIELD_CLOCK_COUNT_MISMATCH")
            continue
        blocks.append(
            _float64_block(
                category="source-numerics",
                native_field_id=field_id,
                native_unit="1",
                dimension_ids=("clock_s", "value"),
                values=np.stack(captured_numerics),
                clock_s=state_clock_s,
            )
        )
    action_clock_s = tuple(range(len(requested)))
    for category, action_values in (
        ("action-requested", requested),
        ("action-accepted", accepted),
        ("action-applied", applied),
        ("action-realized", realized),
    ):
        if not action_values:
            continue
        blocks.append(
            _float64_block(
                category=category,
                native_field_id="native-action",
                native_unit='mixed-native-see-denominator-response-action-component-contract',
                dimension_ids=("clock_s", "action_component"),
                values=np.stack([_action_array(value) for value in action_values]),
                clock_s=action_clock_s,
            )
        )

    common_grid = np.linspace(0.0, 1.0, DENOMINATOR_RESPONSE_COMMON_GRID_POINTS, dtype=np.float64)
    blocks.append(
        _float64_block(
            category="coordinate",
            native_field_id="common_rho_norm",
            native_unit="1",
            dimension_ids=("common_rho_norm",),
            values=common_grid,
        )
    )
    by_key = {(value.category, value.native_field_id): value for value in blocks}
    receiver_by_field = {value.source_field_id: value for value in receiver_groups()}
    for field_id, group in sorted(receiver_by_field.items()):
        source = by_key.get(("source-profile", field_id))
        if source is None:
            reason_codes.add(f"DECISIVE_SOURCE_FIELD_ABSENT_{field_id.upper()}")
            continue
        if len(source.dimension_ids) != 2:
            reason_codes.add(f"DECISIVE_SOURCE_FIELD_RANK_INVALID_{field_id.upper()}")
            continue
        coordinate_id = source.dimension_ids[1]
        coordinate = by_key.get(("coordinate", coordinate_id))
        if coordinate is None:
            reason_codes.add(f"DECISIVE_SOURCE_COORDINATE_ABSENT_{coordinate_id.upper()}")
            continue
        native_x = coordinate.array().reshape(-1)
        native_y = source.array()
        if native_y.shape[1] != native_x.size or native_x[0] > 0 or native_x[-1] < 1:
            reason_codes.add(f"DECISIVE_SOURCE_SUPPORT_INVALID_{field_id.upper()}")
            continue
        common = np.stack([np.interp(common_grid, native_x, row) for row in native_y])
        blocks.append(
            _float64_block(
                category="common-profile",
                native_field_id=field_id,
                native_unit=group.native_unit,
                dimension_ids=("clock_s", "common_rho_norm"),
                values=common,
                clock_s=state_clock_s,
            )
        )
    return tuple(sorted(blocks, key=lambda value: value.block_id))

def acquire_denominator_qualification_episode(
    *,
    config: DenominatorResponseQualificationConfig,
    cell_id: str,
    view_id: str,
) -> DenominatorResponseCapturedEpisode:
    """Execute one exact Act A path and retain the complete source surface."""

    from empirical_lawhood.adapters.simulators.prepared_base import verify_cpu_runtime

    runtime_reasons = verify_cpu_runtime()
    if runtime_reasons:
        raise RuntimeError(",".join(runtime_reasons))
    cell = next(value for value in config.cells if value.cell_id == cell_id)
    view = next(value for value in config.views if value.view_id == view_id)
    word = config.baseline_word
    started = time.monotonic()
    reason_codes: set[str] = set()
    disposition = EpisodeDisposition.COMPLETE
    state_clock_s: list[int] = []
    field_values: dict[tuple[str, str], list[npt.NDArray[np.float64]]] = {}
    numerics_values: dict[str, list[npt.NDArray[np.float64]]] = {}
    expected_shapes: dict[tuple[str, str], tuple[int, ...]] = {}
    requested_values: list[DenominatorResponseNativeAction] = []
    accepted_values: list[DenominatorResponseNativeAction] = []
    applied_values: list[DenominatorResponseNativeAction] = []
    realized_values: list[DenominatorResponseNativeAction] = []
    clipped_clock_s: list[int] = []
    metadata: dict[tuple[str, str], tuple[str, tuple[str, ...]]] = {}
    coordinates: dict[str, npt.NDArray[np.float64]] = {}
    environment: Any | None = None
    try:
        environment = _environment(cell, view)
        environment.reset(seed=cell.environment_seed)
        metadata, coordinates = _source_metadata(environment)
        state_clock_s.append(0)
        _capture_state(
            environment.state or {},
            metadata=metadata,
            field_values=field_values,
            expected_shapes=expected_shapes,
            reason_codes=reason_codes,
        )
        for field_id, values in _numerics_values(environment).items():
            numerics_values.setdefault(field_id, []).append(values)

        for row in word.rows:
            request_clock = row.request_clock_s
            if int(round(float(environment.current_time))) != request_clock:
                disposition = EpisodeDisposition.TECHNICAL_OBSERVATION_FAILURE
                reason_codes.add("NATIVE_CLOCK_DIVERGENCE")
                break
            requested = row.action
            _, reward, terminated, truncated, info = environment.step(_action_mapping(requested))
            accepted = requested
            applied = _native_action(environment.torax_app.config.get_current_action_values())
            realized = _realized_action(environment, applied)
            requested_values.append(requested)
            accepted_values.append(accepted)
            applied_values.append(applied)
            realized_values.append(realized)
            receiver_clock = request_clock + 1
            state_clock_s.append(receiver_clock)
            _capture_state(
                environment.state or {},
                metadata=metadata,
                field_values=field_values,
                expected_shapes=expected_shapes,
                reason_codes=reason_codes,
            )
            observed_numerics = _numerics_values(environment)
            prior_clock_count = len(state_clock_s) - 1
            for field_id in set(numerics_values) | set(observed_numerics):
                if field_id in observed_numerics:
                    if field_id not in numerics_values:
                        numerics_values[field_id] = [
                            np.full_like(observed_numerics[field_id], np.nan)
                            for _ in range(prior_clock_count)
                        ]
                        reason_codes.add("NUMERICS_FIELD_APPEARED_AFTER_INITIALIZATION")
                    numerics_values[field_id].append(observed_numerics[field_id])
                else:
                    reason_codes.add("NUMERICS_FIELD_MISSING_AFTER_INITIALIZATION")
                    previous = numerics_values[field_id][-1]
                    numerics_values[field_id].append(np.full_like(previous, np.nan))
            if bool(info.get("action_clipped", False)):
                clipped_clock_s.append(request_clock)
                disposition = EpisodeDisposition.DELIVERY_INVALID
                reason_codes.add("UNEXPECTED_NATIVE_CLIPPING")
            decisive_field_ids = {value.source_field_id for value in config.receiver_groups}
            state_finite = all(
                np.isfinite(np.asarray(raw, dtype=np.float64)).all()
                for field_id, raw in (environment.state or {}).get("profiles", {}).items()
                if field_id in decisive_field_ids
            )
            if float(reward) == -1000.0 or not state_finite:
                disposition = EpisodeDisposition.NUMERICAL_INVALID
                reason_codes.add("NONFINITE_OR_FAILED_SIMULATION")
            if terminated or truncated:
                if receiver_clock < DENOMINATOR_RESPONSE_HORIZON_S:
                    if disposition is EpisodeDisposition.COMPLETE:
                        disposition = EpisodeDisposition.SIMULATOR_TERMINATED
                    reason_codes.add(
                        "SIMULATOR_TERMINATED_BEFORE_HORIZON"
                        if terminated
                        else "SIMULATOR_TRUNCATED_BEFORE_HORIZON"
                    )
                break
    except Exception as error:
        if state_clock_s:
            disposition = EpisodeDisposition.NUMERICAL_INVALID
            reason_codes.add(f"SIMULATOR_{type(error).__name__.upper()}")
        else:
            disposition = EpisodeDisposition.TECHNICAL_OBSERVATION_FAILURE
            reason_codes.add(f"TECHNICAL_INITIALIZATION_{type(error).__name__.upper()}")
    finally:
        if environment is not None:
            environment.close()

    state_clocks = tuple(state_clock_s)
    blocks = _make_state_blocks(
        state_clock_s=state_clocks,
        metadata=metadata,
        coordinates=coordinates,
        field_values=field_values,
        numerics_values=numerics_values,
        requested=requested_values,
        accepted=accepted_values,
        applied=applied_values,
        realized=realized_values,
        reason_codes=reason_codes,
    )
    missing_clocks = tuple(value for value in range(DENOMINATOR_RESPONSE_HORIZON_S + 1) if value not in state_clocks)
    if missing_clocks and disposition is EpisodeDisposition.COMPLETE:
        disposition = EpisodeDisposition.PARTIAL_VALID_PREFIX
        reason_codes.add("REQUIRED_CLOCKS_ABSENT")
    decisive_fields = {value.source_field_id for value in config.receiver_groups}
    available_profiles = {
        value.native_field_id for value in blocks if value.category == "source-profile"
    }
    if decisive_fields - available_profiles:
        disposition = EpisodeDisposition.UNEVALUABLE_OPERAND
    invalid_nonfinite_categories = {
        "action-accepted",
        "action-applied",
        "action-realized",
        "action-requested",
        "common-profile",
        "coordinate",
    }
    decisive_nonfinite = any(
        value.nonfinite_value_count
        and (
            value.category in invalid_nonfinite_categories
            or (value.category == "source-profile" and value.native_field_id in decisive_fields)
        )
        for value in blocks
    )
    if decisive_nonfinite:
        if disposition is EpisodeDisposition.COMPLETE:
            disposition = EpisodeDisposition.NUMERICAL_INVALID
        reason_codes.add("NONFINITE_DECISIVE_VALUE")
    if disposition is EpisodeDisposition.COMPLETE and reason_codes:
        disposition = EpisodeDisposition.UNEVALUABLE_OPERAND

    return DenominatorResponseCapturedEpisode(
        episode_id=(
            f"episode.denominator-qualification.{config.stage.value.lower().replace('_', '-')}."
            f"{cell.cell_id.removeprefix('cell.denominator-response-')}."
            f"{view.view_id.removeprefix('view.denominator-response.')}"
        ),
        config=ObjectIdentity.from_record(config.config_id, config),
        cell=ObjectIdentity.from_record(cell.cell_id, cell),
        view=ObjectIdentity.from_record(view.view_id, view),
        word=ObjectIdentity.from_record(word.word_id, word),
        state_clock_s=state_clocks,
        action_request_clock_s=tuple(range(len(requested_values))),
        blocks=blocks,
        source_profile_field_ids=tuple(
            sorted(value.native_field_id for value in blocks if value.category == "source-profile")
        ),
        source_scalar_field_ids=tuple(
            sorted(value.native_field_id for value in blocks if value.category == "source-scalar")
        ),
        source_numerics_field_ids=tuple(
            sorted(value.native_field_id for value in blocks if value.category == "source-numerics")
        ),
        source_unavailable_operand_ids=plan_time_source_inventory().known_source_unavailable_operand_ids,
        action_clipped_clock_s=tuple(clipped_clock_s),
        disposition=disposition,
        last_valid_clock_s=max(state_clocks) if state_clocks else None,
        missing_required_state_clock_s=missing_clocks,
        reason_codes=tuple(sorted(reason_codes)),
        runtime_seconds=Decimal(f"{time.monotonic() - started:.9f}"),
        backend="cpu",
        precision="float64",
        outcome_access=config.outcome_access,
    )

__all__ = ["acquire_denominator_qualification_episode"]
