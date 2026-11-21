"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from empirical_lawhood.domains.fusion.numerical_denominator import evaluate_common_density_gauge
import math
import time
from decimal import Decimal
from typing import Any, Mapping, cast
import numpy as np
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.fusion.prepared_base import ActionLedger, DenseField, EpisodeDisposition, PreparedBaseCellSubstitution
from empirical_lawhood.adapters.simulators.prepared_base import _action_mapping, _environment, _native_action, _realized_action, _receiver_values, verify_cpu_runtime

from empirical_lawhood.domains.fusion.numerical_denominator import (
    NumericalDenominatorBatch as _science_NumericalDenominatorBatch,
    NumericalDenominatorConfig as _science_NumericalDenominatorConfig,
    NumericalDenominatorEpisode as _science_NumericalDenominatorEpisode,
    NumericalDenominatorGaugeObservation as _science_NumericalDenominatorGaugeObservation,
    NumericalDenominatorTransition as _science_NumericalDenominatorTransition,
    _DIAGNOSTIC_CLOCKS,
    _TECHNICAL_RESERVE_DISPOSITIONS,
    _decimal,
)

def _common_gauge(
    environment: Any,
    state: Mapping[str, Any],
    receiver_clock_s: int,
    common_grid_cells: int,
) -> _science_NumericalDenominatorGaugeObservation:
    sim_state = environment.torax_app.current_sim_state
    if sim_state is None:
        raise ValueError("numerical denominator TORAX state is absent")
    rho = np.asarray(sim_state.geometry.rho_norm, dtype=np.float64)
    density = np.asarray(sim_state.core_profiles.n_e.value, dtype=np.float64)
    vpr = np.asarray(sim_state.geometry.vpr, dtype=np.float64)
    return evaluate_common_density_gauge(
        receiver_clock_s=receiver_clock_s,
        common_grid_cells=common_grid_cells,
        rho=rho,
        density=density,
        vpr=vpr,
        current=float(np.asarray(sim_state.core_profiles.Ip_profile_face[-1])),
        minor_radius=float(np.asarray(sim_state.geometry.a_minor)),
        source_volume_density=_decimal(state["scalars"]["n_e_volume_avg"]),
        source_line_density=_decimal(state["scalars"]["n_e_line_avg"]),
        source_volume_fgw=_decimal(state["scalars"]["fgw_n_e_volume_avg"]),
        source_line_fgw=_decimal(state["scalars"]["fgw_n_e_line_avg"]),
    )

def _array_field(field_id: str, unit: str, raw: Any) -> DenseField:
    if raw is None:
        return DenseField(
            field_id=field_id,
            unit=unit,
            values=(),
            source_available=False,
        )
    values = tuple(_decimal(value) for value in np.asarray(raw).reshape(-1))
    return DenseField(
        field_id=field_id,
        unit=unit,
        values=values,
        source_available=bool(values),
    )

def _diagnostic_fields(environment: Any, receiver_clock_s: int) -> tuple[DenseField, ...]:
    if receiver_clock_s not in _DIAGNOSTIC_CLOCKS:
        return ()
    sim_state = environment.torax_app.current_sim_state
    if sim_state is None:
        return ()
    fields = [
        _array_field(
            "profile.electron-density",
            "m-3",
            sim_state.core_profiles.n_e.value,
        ),
        _array_field("profile.q", "1", sim_state.core_profiles.q_face),
        _array_field("profile.psi", "Wb", sim_state.core_profiles.psi.value),
        _array_field(
            "profile.current",
            "A",
            sim_state.core_profiles.Ip_profile_face,
        ),
        _array_field("grid.rho-cell", "1", sim_state.geometry.rho_norm),
        _array_field("grid.rho-face", "1", sim_state.geometry.rho_face_norm),
        _array_field("geometry.vpr", "m3", sim_state.geometry.vpr),
        _array_field(
            "boundary.electron-density-right",
            "m-3",
            sim_state.core_profiles.n_e.right_face_constraint,
        ),
        _array_field(
            "transport.d-electron",
            "m2.s-1",
            sim_state.core_transport.d_face_el,
        ),
        _array_field(
            "transport.v-electron",
            "m.s-1",
            sim_state.core_transport.v_face_el,
        ),
        _array_field(
            "transport.d-electron-pereverzev",
            "m2.s-1",
            sim_state.core_transport.d_face_el_pereverzev,
        ),
        _array_field(
            "transport.v-electron-pereverzev",
            "m.s-1",
            sim_state.core_transport.v_face_el_pereverzev,
        ),
    ]
    for source_id, raw in sorted(sim_state.core_sources.n_e.items()):
        stable = str(source_id).lower().replace("_", "-")
        fields.append(_array_field(f"source.density.{stable}", "m-3.s-1", raw))
    fields.extend(
        (
            _array_field("profile.density-source", "m-3.s-1", None),
            _array_field("profile.density-flux", "m-2.s-1", None),
            _array_field("profile.particle-balance", "m-3.s-1", None),
        )
    )
    return tuple(sorted(fields, key=lambda value: value.field_id))

def acquire_episode(
    *,
    config: _science_NumericalDenominatorConfig,
    cell_id: str,
    view_id: str,
) -> _science_NumericalDenominatorEpisode:
    runtime_reasons = verify_cpu_runtime()
    if runtime_reasons:
        raise RuntimeError(",".join(runtime_reasons))
    cell = next(value for value in config.cells if value.cell_id == cell_id)
    view = next(value for value in config.views if value.view_id == view_id)
    word = config.word
    environment = _environment(cast(Any, cell), cast(Any, view))
    transitions: list[_science_NumericalDenominatorTransition] = []
    reasons: set[str] = set()
    disposition = EpisodeDisposition.COMPLETE
    started = time.monotonic()
    try:
        observation, _ = environment.reset(seed=cell.environment_seed)
        del observation
        for request_clock, row in enumerate(word.rows):
            if int(round(float(environment.current_time))) != request_clock:
                disposition = EpisodeDisposition.TECHNICAL_OBSERVATION_FAILURE
                reasons.add("NATIVE_CLOCK_DIVERGENCE")
                break
            requested = row.action
            _, reward, terminated, truncated, info = environment.step(
                _action_mapping(requested)
            )
            accepted = requested
            applied = _native_action(environment.torax_app.config.get_current_action_values())
            realized = _realized_action(environment, applied)
            receiver_clock = request_clock + 1
            state = environment.state or {}
            receivers, missing = _receiver_values(state)
            gauge: _science_NumericalDenominatorGaugeObservation | None
            try:
                gauge = _common_gauge(
                    environment,
                    state,
                    receiver_clock,
                    config.common_grid_cells,
                )
            except (KeyError, TypeError, ValueError, FloatingPointError):
                gauge = None
                missing = tuple(
                    sorted(
                        {
                            *missing,
                            "receiver.common-gauge-density-fgw",
                        }
                    )
                )
            valid = (
                float(reward) != -1000.0
                and not missing
                and all(math.isfinite(float(value.value)) for value in receivers)
                and gauge is not None
            )
            clipped = bool(info.get("action_clipped", False))
            transitions.append(
                _science_NumericalDenominatorTransition(
                    transition_id=(
                        f"transition.{cell.cell_id.removeprefix('cell.')}."
                        f"{view.view_id.removeprefix('view.')}.{receiver_clock:03d}"
                    ),
                    receiver_clock_s=receiver_clock,
                    action=ActionLedger(
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
                    gauge=gauge,
                    diagnostic_fields=_diagnostic_fields(environment, receiver_clock),
                    valid=valid,
                    terminated=bool(terminated),
                    truncated=bool(truncated),
                    missing_primary_operand_ids=missing,
                )
            )
            if clipped:
                disposition = EpisodeDisposition.DELIVERY_INVALID
                reasons.add("UNEXPECTED_NATIVE_CLIPPING")
            if missing:
                disposition = EpisodeDisposition.UNEVALUABLE_OPERAND
                reasons.add("PRIMARY_OR_COMMON_GAUGE_OPERAND_ABSENT")
            if not valid and not missing:
                disposition = EpisodeDisposition.NUMERICAL_INVALID
                reasons.add("NONFINITE_OR_FAILED_SIMULATION")
            if terminated or truncated:
                if receiver_clock < 150:
                    if disposition is EpisodeDisposition.COMPLETE:
                        disposition = EpisodeDisposition.SIMULATOR_TERMINATED
                    reasons.add(
                        "SIMULATOR_TERMINATED_BEFORE_HORIZON"
                        if terminated
                        else "SIMULATOR_TRUNCATED_BEFORE_HORIZON"
                    )
                break
    except Exception as error:
        # Once a simulator trajectory exists, an untyped source exception is
        # conservatively scientific/numerical evidence.  It cannot consume a
        # reserve as though it were an outcome-blind infrastructure failure.
        if transitions:
            disposition = EpisodeDisposition.NUMERICAL_INVALID
            reasons.add(f"SIMULATOR_{type(error).__name__.upper()}")
        else:
            disposition = EpisodeDisposition.TECHNICAL_OBSERVATION_FAILURE
            reasons.add(f"TECHNICAL_INITIALIZATION_{type(error).__name__.upper()}")
    finally:
        environment.close()
    if len(transitions) < 150 and disposition is EpisodeDisposition.COMPLETE:
        disposition = EpisodeDisposition.PARTIAL_VALID_PREFIX
        reasons.add("REQUIRED_CLOCKS_ABSENT")
    last_valid = max(
        (value.receiver_clock_s for value in transitions if value.valid),
        default=None,
    )
    return _science_NumericalDenominatorEpisode(
        episode_id=(
            f"episode.{config.stage.value.lower()}."
            f"{cell.cell_id.removeprefix('cell.')}."
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
        runtime_seconds=Decimal(f"{time.monotonic() - started:.9f}"),
        backend="cpu",
        precision="float64",
        outcome_access=config.outcome_access,
    )

def acquire_stage(config: _science_NumericalDenominatorConfig) -> _science_NumericalDenominatorBatch:
    """Acquire whole view bundles with outcome-blind technical replacement."""

    episodes: list[_science_NumericalDenominatorEpisode] = []
    active: list[str] = []
    excluded: list[str] = []
    substitutions: list[PreparedBaseCellSubstitution] = []
    reserve_ids = iter(config.reserve_cell_ids)
    for intended_cell_id in config.primary_cell_ids:
        current_cell_id = intended_cell_id
        while True:
            bundle: list[_science_NumericalDenominatorEpisode] = []
            technical_failure = False
            for view in config.views:
                episode = acquire_episode(
                    config=config,
                    cell_id=current_cell_id,
                    view_id=view.view_id,
                )
                bundle.append(episode)
                episodes.append(episode)
                if episode.disposition in _TECHNICAL_RESERVE_DISPOSITIONS:
                    technical_failure = True
                    break
            if not technical_failure:
                active.append(current_cell_id)
                break
            excluded.append(current_cell_id)
            try:
                replacement = next(reserve_ids)
            except StopIteration:
                break
            substitutions.append(
                PreparedBaseCellSubstitution(
                    substitution_id=(
                        f"substitution.{config.config_id.removeprefix('config.')}."
                        f"{intended_cell_id.removeprefix('cell.')}."
                        f"{replacement.removeprefix('cell.')}"
                    ),
                    intended_cell_id=intended_cell_id,
                    replacement_cell_id=replacement,
                    excluded_episode_ids=tuple(
                        sorted(value.episode_id for value in bundle)
                    ),
                    reason_codes=tuple(
                        sorted(
                            {
                                reason
                                for episode in bundle
                                for reason in episode.reason_codes
                            }
                        )
                    )
                    or ("TECHNICAL_BUNDLE_FAILURE",),
                    receiver_outcome_released_to_evaluator=False,
                )
            )
            current_cell_id = replacement
    return _science_NumericalDenominatorBatch(
        batch_id=f"batch.{config.config_id.removeprefix('config.')}",
        config=ObjectIdentity.from_record(config.config_id, config),
        stage=config.stage,
        episodes=tuple(sorted(episodes, key=lambda value: value.episode_id)),
        active_cell_ids=tuple(sorted(active)),
        excluded_cell_ids=tuple(sorted(excluded)),
        substitutions=tuple(
            sorted(substitutions, key=lambda value: value.substitution_id)
        ),
        expected_active_cell_count=len(config.primary_cell_ids),
        complete_active_roster=len(active) == len(config.primary_cell_ids),
        outcome_access=config.outcome_access,
    )
