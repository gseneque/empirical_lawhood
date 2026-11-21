"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from empirical_lawhood.domains.fusion.prepared_base import complete_radiation_receiver
import copy
from decimal import Decimal
import math
import time
from typing import Any, Mapping
import numpy as np
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import NamedDecimal

from empirical_lawhood.domains.fusion.prepared_base import (
    ActionLedger as _science_ActionLedger,
    DenseField as _science_DenseField,
    EpisodeDisposition as _science_EpisodeDisposition,
    NativeAction as _science_NativeAction,
    PreparedBaseAcquisitionBatch as _science_PreparedBaseAcquisitionBatch,
    PreparedBaseCell as _science_PreparedBaseCell,
    PreparedBaseCellSubstitution as _science_PreparedBaseCellSubstitution,
    PreparedBaseConfig as _science_PreparedBaseConfig,
    PreparedBaseEpisode as _science_PreparedBaseEpisode,
    PreparedBaseStage as _science_PreparedBaseStage,
    PreparedBaseTransition as _science_PreparedBaseTransition,
    PreparedBaseView as _science_PreparedBaseView,
    _TECHNICAL_RESERVE_DISPOSITIONS,
)

_SCALAR_SOURCES = {
    "receiver.beta-n": ("beta_N", "1"),
    "receiver.fgw-line-average": ("fgw_n_e_line_avg", "1"),
    "receiver.fgw-volume-average": ("fgw_n_e_volume_avg", "1"),
    "receiver.h98": ("H98", "1"),
    "receiver.lcfs-current": ("Ip", "A"),
    "receiver.volume-average-density": ("n_e_volume_avg", "m-3"),
    "receiver.p-fusion": ("P_fusion", "W"),
    "receiver.p-heat-total": ("P_heat_total", "W"),
    "receiver.p-radiation-electron": ("P_radiation_e", "W"),
    "receiver.q-fusion": ("Q_fusion", "1"),
    "receiver.q-min": ("q_min", "1"),
    "receiver.q95": ("q95", "1"),
}

_PROFILE_SOURCES = {
    "profile.density-electron": ("n_e", "m-3"),
    "profile.poloidal-flux": ("psi", "Wb"),
    "profile.q": ("q", "1"),
}

_DIAGNOSTIC_CLOCKS = frozenset((*range(1, 31), *range(105, 115), 150))

def _decimal(value: Any) -> Decimal:
    number = float(np.asarray(value, dtype=np.float64).reshape(-1)[0])
    if not math.isfinite(number):
        raise ValueError("Gym--TORAX produced a non-finite scalar")
    return Decimal(f"{number:.17g}")

def _native_action(values: Mapping[str, Any]) -> _science_NativeAction:
    if set(values) != {"Ip", "NBI", "ECRH"}:
        raise ValueError("Gym--TORAX action mapping changed")
    ip = np.asarray(values["Ip"], dtype=np.float64).reshape(-1)
    nbi = np.asarray(values["NBI"], dtype=np.float64).reshape(-1)
    ecrh = np.asarray(values["ECRH"], dtype=np.float64).reshape(-1)
    if ip.shape != (1,) or nbi.shape != (3,) or ecrh.shape != (3,):
        raise ValueError("Gym--TORAX action vector shape changed")

    def fixed(value: Any, expected: Decimal) -> Decimal:
        observed = _decimal(value)
        return expected if abs(observed - expected) <= Decimal("0.000000000000001") else observed

    return _science_NativeAction(
        ip_a=_decimal(ip[0]),
        nbi_power_w=_decimal(nbi[0]),
        nbi_location=fixed(nbi[1], Decimal("0.25")),
        nbi_width=fixed(nbi[2], Decimal("0.25")),
        ecrh_power_w=_decimal(ecrh[0]),
        ecrh_location=fixed(ecrh[1], Decimal("0.35")),
        ecrh_width=fixed(ecrh[2], Decimal("0.05")),
    )

def _action_mapping(action: _science_NativeAction) -> dict[str, np.ndarray[Any, np.dtype[np.float64]]]:
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

def _scale_profile(profile: Any, scale: float) -> Any:
    result = copy.deepcopy(profile)
    for radial_values in result.values():
        for radius in tuple(radial_values):
            if float(radius) < 1.0:
                radial_values[radius] = float(radial_values[radius]) * scale
    return result

def _environment(cell: _science_PreparedBaseCell, view: _science_PreparedBaseView) -> Any:
    from gymtorax.envs.iter_hybrid_env import CONFIG, IterHybridEnv  # type: ignore[import-untyped]

    config = copy.deepcopy(CONFIG)
    config["numerics"]["fixed_dt"] = float(view.internal_timestep_s)
    config["geometry"]["n_rho"] = view.radial_cells
    config["solver"]["n_corrector_steps"] = view.corrector_steps
    config["profile_conditions"]["T_i"] = _scale_profile(
        config["profile_conditions"]["T_i"], float(cell.initial_temperature_scale)
    )
    config["profile_conditions"]["T_e"] = _scale_profile(
        config["profile_conditions"]["T_e"], float(cell.initial_temperature_scale)
    )
    config["profile_conditions"]["nbar"] = float(cell.initial_density_nbar)
    config["neoclassical"]["bootstrap_current"]["bootstrap_multiplier"] = float(
        cell.bootstrap_multiplier
    )
    for key in ("D_e_inner", "chi_i_inner", "chi_e_inner"):
        config["transport"][key] = float(config["transport"][key]) * float(
            cell.inner_transport_scale
        )

    class PreparedBaseEnvironment(IterHybridEnv):  # type: ignore[misc]
        def _get_torax_config(self) -> dict[str, Any]:
            return {
                "config": config,
                "discretization": "fixed",
                "ratio_a_sim": int(round(1.0 / float(view.internal_timestep_s))),
            }

        def _compute_reward(self, state: Any, next_state: Any, action: Any) -> float:
            del state, next_state, action
            return 0.0

    return PreparedBaseEnvironment(render_mode=None, store_history=False, log_level="warning")

def verify_cpu_runtime() -> tuple[str, ...]:
    import importlib.metadata
    import jax

    reasons = []
    try:
        jax.config.update("jax_platforms", "cpu")  # type: ignore[no-untyped-call]
        jax.config.update("jax_enable_x64", True)  # type: ignore[no-untyped-call]
    except (RuntimeError, ValueError):
        reasons.append("CPU_FLOAT64_CONFIGURATION_FAILED")
    if importlib.metadata.version("gymtorax") != "1.1.1":
        reasons.append("GYM_TORAX_VERSION_MISMATCH")
    if importlib.metadata.version("torax") != "1.4.2":
        reasons.append("TORAX_VERSION_MISMATCH")
    if importlib.metadata.version("jax") != "0.10.2":
        reasons.append("JAX_VERSION_MISMATCH")
    if importlib.metadata.version("jaxlib") != "0.10.2":
        reasons.append("JAXLIB_VERSION_MISMATCH")
    if jax.default_backend() != "cpu":
        reasons.append("CPU_BACKEND_REQUIRED_NO_FALLBACK")
    if not bool(getattr(jax.config, "x64_enabled", False)):
        reasons.append("JAX_FLOAT64_REQUIRED")
    return tuple(sorted(reasons))

def _state_scalar(state: Mapping[str, Any], source_id: str) -> Decimal | None:
    value = state.get("scalars", {}).get(source_id)
    return None if value is None else _decimal(value)

def _receiver_values(state: Mapping[str, Any]) -> tuple[tuple[NamedDecimal, ...], tuple[str, ...]]:
    values: dict[str, NamedDecimal] = {}
    missing = []
    for value_id, (source_id, unit) in _SCALAR_SOURCES.items():
        value = _state_scalar(state, source_id)
        if value is None:
            if value_id in {
                "receiver.beta-n",
                "receiver.fgw-volume-average",
                "receiver.h98",
                "receiver.p-heat-total",
                "receiver.p-radiation-electron",
                "receiver.q-min",
                "receiver.q95",
            }:
                missing.append(value_id)
            continue
        values[value_id] = NamedDecimal(value_id=value_id, value=value, unit=unit)
    return complete_radiation_receiver(values, missing)


def _diagnostic_fields(state: Mapping[str, Any], clock_s: int) -> tuple[_science_DenseField, ...]:
    if clock_s not in _DIAGNOSTIC_CLOCKS:
        return ()
    profiles = state.get("profiles", {})
    fields = []
    for field_id, (source_id, unit) in _PROFILE_SOURCES.items():
        raw = profiles.get(source_id)
        values = (
            () if raw is None else tuple(_decimal(value) for value in np.asarray(raw).reshape(-1))
        )
        fields.append(
            _science_DenseField(
                field_id=field_id,
                unit=unit,
                values=values,
                source_available=bool(values),
            )
        )
    for field_id, unit in (
        ("profile.current-boundary", "A"),
        ("profile.density-boundary", "m-3"),
        ("profile.density-flux", "m-2.s-1"),
        ("profile.density-source", "m-3.s-1"),
        ("profile.particle-balance", "m-3.s-1"),
    ):
        fields.append(
            _science_DenseField(
                field_id=field_id,
                unit=unit,
                values=(),
                source_available=False,
            )
        )
    return tuple(sorted(fields, key=lambda value: value.field_id))

def _realized_action(environment: Any, applied: _science_NativeAction) -> _science_NativeAction:
    state = environment.state or {}
    ip = _state_scalar(state, "Ip")
    nbi = _state_scalar(state, "P_aux_generic_total")
    ecrh = _state_scalar(state, "P_ecrh_e")
    if ip is None or nbi is None or ecrh is None:
        return applied
    return _science_NativeAction(
        ip_a=ip,
        nbi_power_w=nbi,
        nbi_location=applied.nbi_location,
        nbi_width=applied.nbi_width,
        ecrh_power_w=ecrh,
        ecrh_location=applied.ecrh_location,
        ecrh_width=applied.ecrh_width,
    )

def acquire_episode(
    *,
    config: _science_PreparedBaseConfig,
    cell_id: str,
    word_id: str,
    view_id: str,
) -> _science_PreparedBaseEpisode:
    runtime_reasons = verify_cpu_runtime()
    if runtime_reasons:
        raise RuntimeError(",".join(runtime_reasons))
    cell = next(value for value in config.cells if value.cell_id == cell_id)
    word = next(value for value in config.words if value.word_id == word_id)
    view = next(value for value in config.views if value.view_id == view_id)
    environment = _environment(cell, view)
    transitions: list[_science_PreparedBaseTransition] = []
    reasons: set[str] = set()
    disposition = _science_EpisodeDisposition.COMPLETE
    started = time.monotonic()
    try:
        observation, _ = environment.reset(seed=cell.environment_seed)
        del observation
        for request_clock, row in enumerate(word.rows):
            if int(round(float(environment.current_time))) != request_clock:
                disposition = _science_EpisodeDisposition.TECHNICAL_OBSERVATION_FAILURE
                reasons.add("NATIVE_CLOCK_DIVERGENCE")
                break
            requested = row.action
            _, reward, terminated, truncated, info = environment.step(_action_mapping(requested))
            accepted = requested
            applied = _native_action(environment.torax_app.config.get_current_action_values())
            realized = _realized_action(environment, applied)
            receiver_clock = request_clock + 1
            state = environment.state or {}
            receivers, missing = _receiver_values(state)
            valid = (
                float(reward) != -1000.0
                and not missing
                and all(math.isfinite(float(value.value)) for value in receivers)
            )
            clipped = bool(info.get("action_clipped", False))
            transitions.append(
                _science_PreparedBaseTransition(
                    transition_id=(
                        f"transition.{cell.cell_id.removeprefix('cell.')}."
                        f"{word.word_id.removeprefix('word.')}."
                        f"{view.view_id.removeprefix('view.')}.{receiver_clock:03d}"
                    ),
                    receiver_clock_s=receiver_clock,
                    action=_science_ActionLedger(
                        request_clock_s=request_clock,
                        accepted_clock_s=request_clock,
                        applied_clock_s=receiver_clock,
                        realized_clock_s=receiver_clock,
                        requested=requested,
                        accepted=accepted,
                        applied=applied,
                        realized=realized,
                        clipped=clipped,
                        realization_basis_id=(
                            "realization.gym-torax.state-scalars"
                            if realized != applied
                            else "realization.gym-torax.current-action-values"
                        ),
                    ),
                    receiver_values=receivers,
                    diagnostic_fields=_diagnostic_fields(state, receiver_clock),
                    valid=valid,
                    terminated=bool(terminated),
                    truncated=bool(truncated),
                    missing_primary_operand_ids=missing,
                )
            )
            if clipped:
                disposition = _science_EpisodeDisposition.DELIVERY_INVALID
                reasons.add("UNEXPECTED_NATIVE_CLIPPING")
            if missing:
                disposition = _science_EpisodeDisposition.UNEVALUABLE_OPERAND
                reasons.add("PRIMARY_RECEIVER_OPERAND_ABSENT")
            if not valid and not missing:
                disposition = _science_EpisodeDisposition.NUMERICAL_INVALID
                reasons.add("NONFINITE_OR_FAILED_SIMULATION")
            if terminated or truncated:
                if receiver_clock < 150:
                    if disposition is _science_EpisodeDisposition.COMPLETE:
                        disposition = _science_EpisodeDisposition.SIMULATOR_TERMINATED
                    reasons.add(
                        "SIMULATOR_TERMINATED_BEFORE_HORIZON"
                        if terminated
                        else "SIMULATOR_TRUNCATED_BEFORE_HORIZON"
                    )
                break
    except Exception as error:
        disposition = _science_EpisodeDisposition.TECHNICAL_OBSERVATION_FAILURE
        reasons.add(f"TECHNICAL_{type(error).__name__.upper()}")
    finally:
        environment.close()
    if len(transitions) < 150 and disposition is _science_EpisodeDisposition.COMPLETE:
        disposition = _science_EpisodeDisposition.PARTIAL_VALID_PREFIX
        reasons.add("REQUIRED_CLOCKS_ABSENT")
    last_valid = max(
        (value.receiver_clock_s for value in transitions if value.valid),
        default=None,
    )
    runtime = Decimal(f"{time.monotonic() - started:.9f}")
    return _science_PreparedBaseEpisode(
        episode_id=(
            f"episode.{config.stage.value.lower()}."
            f"{cell.cell_id.removeprefix('cell.')}."
            f"{word.word_id.removeprefix('word.')}."
            f"{view.view_id.removeprefix('view.')}"
        ),
        config=ObjectIdentity.from_record(config.config_id, config),
        cell=ObjectIdentity.from_record(cell.cell_id, cell),
        word=ObjectIdentity.from_record(word.word_id, word),
        view=ObjectIdentity.from_record(view.view_id, view),
        transitions=tuple(transitions),
        disposition=disposition,
        last_valid_clock_s=last_valid,
        missing_required_clocks_s=tuple(range(len(transitions) + 1, 151)),
        reason_codes=tuple(sorted(reasons)),
        runtime_seconds=runtime,
        backend="cpu",
        precision="float64",
        outcome_access=config.outcome_access,
    )

def acquire_stage(
    *,
    config: _science_PreparedBaseConfig,
) -> _science_PreparedBaseAcquisitionBatch:
    """Acquire primary bundles and consume reserves only for blinded technical failures."""

    if config.stage is _science_PreparedBaseStage.QUALIFICATION:
        raise ValueError("qualification uses the explicit excluded paired-route acquisition")
    episodes: list[_science_PreparedBaseEpisode] = []
    active_cell_ids: list[str] = []
    excluded_cell_ids: list[str] = []
    substitutions: list[_science_PreparedBaseCellSubstitution] = []
    reserve_ids = iter(config.reserve_cell_ids)

    for intended_cell_id in config.primary_cell_ids:
        current_cell_id = intended_cell_id
        while True:
            bundle: list[_science_PreparedBaseEpisode] = []
            technical_failure = False
            for word in config.words:
                for view in config.views:
                    episode = acquire_episode(
                        config=config,
                        cell_id=current_cell_id,
                        word_id=word.word_id,
                        view_id=view.view_id,
                    )
                    bundle.append(episode)
                    episodes.append(episode)
                    if episode.disposition in _TECHNICAL_RESERVE_DISPOSITIONS:
                        technical_failure = True
                        break
                if technical_failure:
                    break
            if not technical_failure:
                active_cell_ids.append(current_cell_id)
                break
            excluded_cell_ids.append(current_cell_id)
            try:
                replacement_cell_id = next(reserve_ids)
            except StopIteration:
                break
            reasons = tuple(
                sorted({reason for episode in bundle for reason in episode.reason_codes})
            )
            substitutions.append(
                _science_PreparedBaseCellSubstitution(
                    substitution_id=(
                        f"substitution.{config.config_id.removeprefix('config.')}."
                        f"{intended_cell_id.removeprefix('cell.')}."
                        f"{replacement_cell_id.removeprefix('cell.')}"
                    ),
                    intended_cell_id=intended_cell_id,
                    replacement_cell_id=replacement_cell_id,
                    excluded_episode_ids=tuple(sorted(value.episode_id for value in bundle)),
                    reason_codes=reasons or ("TECHNICAL_BUNDLE_FAILURE",),
                    receiver_outcome_released_to_evaluator=False,
                )
            )
            current_cell_id = replacement_cell_id

    return _science_PreparedBaseAcquisitionBatch(
        batch_id=f"batch.{config.config_id.removeprefix('config.')}",
        config=ObjectIdentity.from_record(config.config_id, config),
        stage=config.stage,
        episodes=tuple(sorted(episodes, key=lambda value: value.episode_id)),
        active_cell_ids=tuple(sorted(active_cell_ids)),
        excluded_cell_ids=tuple(sorted(excluded_cell_ids)),
        substitutions=tuple(sorted(substitutions, key=lambda value: value.substitution_id)),
        expected_active_cell_count=len(config.primary_cell_ids),
        complete_active_roster=len(active_cell_ids) == len(config.primary_cell_ids),
        outcome_access=config.outcome_access,
    )
