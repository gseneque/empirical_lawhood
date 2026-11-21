"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from empirical_lawhood.domains.fusion.mastu_freegsnke_response.canary_assessment import voltage_vector, current_extrema, assemble_canary_episode
from empirical_lawhood.domains.fusion.mastu_freegsnke_response.canary_assessment import action_roster as _science_action_roster, select_canary as _science_select_canary, select_preparation_slice as _science_select_preparation_slice
import contextlib
import sys
import time
from typing import Any, Final
import numpy as np
from empirical_lawhood.adapters.physical.mast_freegsnke_static_transport.experiment import _build_tokamak, _set_currents
from empirical_lawhood.domains.fusion.mast_freegsnke_static_transport.assessment import primary_xpoint

from empirical_lawhood.domains.fusion.mastu_freegsnke_response.canary_assessment import _admission_limit

from empirical_lawhood.domains.fusion.mastu_freegsnke_response.canary_assessment import DT_S as _science_DT_S, HORIZONS_S as _science_HORIZONS_S, SCHEMA as _science_SCHEMA, VIEWS as _science_VIEWS


def _scientific_episode(
    preparation: dict[str, np.ndarray[Any, Any]],
    machine: dict[str, object],
    *,
    view: int,
    word: str,
    increment_v: float,
    source_slice_index: int,
    qualification_only: bool = False,
) -> dict[str, object]:
    try:
        return _episode(
            preparation,
            machine,
            view=view,
            word=word,
            increment_v=increment_v,
            source_slice_index=source_slice_index,
            qualification_only=qualification_only,
        )
    except (ArithmeticError, RuntimeError, np.linalg.LinAlgError) as error:
        if qualification_only:
            return {
                "eligible": False,
                "error_code": f"FREEGSNKE_{type(error).__name__.upper()}",
                "view": view,
            }
        return {
            "episode_id": f"canary.view-{view}.{word}",
            "view": view,
            "word": word,
            "requested_increment_v": increment_v,
            "valid": False,
            "error_code": f"FREEGSNKE_{type(error).__name__.upper()}",
            "pickup_1_t": {},
        }


def evaluate_canary(
    preparation: dict[str, np.ndarray[Any, Any]],
    static_target: dict[str, np.ndarray[Any, Any]],
    machine: dict[str, object],
    *,
    materiality_t: float = 0.0017,
) -> dict[str, object]:
    """Evaluate supplied MAST-U inputs without asserting release authority.

    Native FreeGSNKE dependencies are loaded only when this calculation runs.
    The result is a calculation; callers must separately establish source,
    input, execution, and claim authority before publishing a scientific claim.
    """

    selected_slice = _science_select_preparation_slice(
        np.asarray(static_target["slice_times_s"], dtype=float),
        np.asarray(static_target["symmetry_collapsed__baseline_65__valid"], dtype=bool),
        np.asarray(static_target["symmetry_collapsed__refined_129__valid"], dtype=bool),
    )
    if selected_slice >= len(preparation["slice_times_s"]):
        raise ValueError("selected static-target slice is absent from preparation")
    view_qualifications = [
        _scientific_episode(
            preparation,
            machine,
            view=view,
            word="qualification",
            increment_v=0,
            source_slice_index=selected_slice,
            qualification_only=True,
        )
        for view in _science_VIEWS
    ]
    qualified = all(bool(item.get("eligible")) for item in view_qualifications)
    qualification: dict[str, object] = {
        "eligible": qualified,
        "views": view_qualifications,
        "selection_rule": "EARLIEST_STATIC_VALID_IN_BOTH_FROZEN_VIEWS",
    }
    if not qualified:
        episodes: list[dict[str, object]] = []
    else:
        raw_limits = [item.get("full_p4_increment_v") for item in view_qualifications]
        if any(not isinstance(item, (float, int)) for item in raw_limits):
            raise TypeError("qualified admission voltage limits are not numeric")
        full = min(float(item) for item in raw_limits if isinstance(item, (float, int)))
        qualification["full_p4_increment_v"] = full
        episodes = [
            _scientific_episode(
                preparation,
                machine,
                view=view,
                word=word,
                increment_v=increment,
                source_slice_index=selected_slice,
            )
            for view in _science_VIEWS
            for word, increment in _science_action_roster(full)
        ]
    selection = (
        _science_select_canary(episodes, materiality_t=materiality_t)
        if len(episodes) == 14
        else {
            "disposition": "SHORT_HORIZON_SOURCE_UNEVALUABLE",
            "selected_fraction": None,
            "selected_horizon_s": None,
            "minimum_signed_contrast_t": None,
            "reason_codes": ["ZERO_ACTION_PROBE_INVALID"],
        }
    )
    result = {
        "schema": _science_SCHEMA,
        "experiment_id": "mastu-freegsnke-short-horizon-voltage-canary",
        "preparation_selection_rule": "EARLIEST_STATIC_VALID_IN_BOTH_FROZEN_VIEWS",
        "source_slice_index": selected_slice,
        "source_time_s": format(float(preparation["slice_times_s"][selected_slice]), ".2f"),
        "coordinate": "SYMMETRY_COLLAPSED",
        "timestep_s": _science_DT_S,
        "materiality_t": materiality_t,
        "qualification": qualification,
        "episodes": episodes,
        "selection": selection,
    }
    return result








ACTIVE_LABELS: Final = (
    "Solenoid",
    "px",
    "d1",
    "d2",
    "d3",
    "dp",
    "d5",
    "d6",
    "d7",
    "p4",
    "p5",
    "p6",
)


def _pickup_1(eq: Any) -> tuple[float, bool]:
    pickups = sorted(
        eq.tokamak.probes.pickups,
        key=lambda value: (float(value["position"][2]), str(value["name"])),
    )
    if len(pickups) < 2:
        raise ValueError("public machine lacks the declared pickup pair")
    eq.tokamak.probes.initialise_setup(eq)
    values = dict(
        zip(
            eq.tokamak.probes.pickup_order,
            eq.tokamak.probes.calculate_pickup_value(eq),
            strict=True,
        )
    )
    _point, _mismatch, topology = primary_xpoint(np.asarray(eq.xpt, dtype=np.float64), float(eq.psi_axis), float(eq.psi_bndry))
    valid = (
        topology != "UNQUALIFIED" and not bool(eq.intersectsWall()) and not bool(eq.flag_limiter)
    )
    return float(values[str(pickups[0]["name"])]), valid

def _episode(
    preparation: dict[str, np.ndarray[Any, Any]],
    machine: dict[str, object],
    *,
    view: int,
    word: str,
    increment_v: float,
    source_slice_index: int,
    qualification_only: bool = False,
) -> dict[str, object]:
    from freegsnke import (  # type: ignore[import-untyped]
        GSstaticsolver,
        equilibrium_update,
        jtor_update,
        nonlinear_solve,
    )

    started = time.monotonic()
    grid = np.asarray(preparation["grid"], dtype=float)
    tokamak = _build_tokamak(machine, "SYMMETRY_COLLAPSED")
    labels = np.asarray(preparation["coil_labels"]).astype(str).tolist()
    _set_currents(
        tokamak,
        machine,
        "SYMMETRY_COLLAPSED",
        labels,
        np.asarray(preparation["currents_output_a"], dtype=float)[source_slice_index],
    )
    eq = equilibrium_update.Equilibrium(
        tokamak=tokamak,
        Rmin=float(grid[0]),
        Rmax=float(grid[1]),
        Zmin=float(grid[2]),
        Zmax=float(grid[3]),
        nx=view,
        ny=view,
    )
    profiles = jtor_update.Lao85(
        eq=eq,
        Ip=float(preparation["plasma_current_a"][source_slice_index]),
        fvac=float(preparation["fvac_t_m"][source_slice_index]),
        alpha=np.asarray(preparation["alpha"], dtype=float)[source_slice_index],
        beta=np.asarray(preparation["beta"], dtype=float)[source_slice_index],
        alpha_logic=bool(preparation["alpha_logic"][source_slice_index]),
        beta_logic=bool(preparation["beta_logic"][source_slice_index]),
    )
    solver = GSstaticsolver.NKGSsolver(eq)
    with contextlib.redirect_stdout(sys.stderr):
        solver.solve(
            eq=eq,
            profiles=profiles,
            constrain=None,
            target_relative_tolerance=1e-6,
            max_solving_iterations=100,
            verbose=False,
        )
        initial_pickup, initial_valid = _pickup_1(eq)
        stepping = nonlinear_solve.nl_solver(
            eq=eq,
            profiles=profiles,
            GSStaticSolver=solver,
            full_timestep=_science_DT_S,
            max_internal_timestep=_science_DT_S,
            plasma_resistivity=1e-6,
            max_mode_frequency=10**2.5,
        )
        stepping.initialize_from_ICs(eq, profiles)
        resistance = np.asarray(stepping.evol_metal_curr.coil_resist, dtype=float)[:12]
        baseline = np.asarray(stepping.vessel_currents_vec, dtype=float)
        active_labels = tuple(tokamak.coils_list[:12])
        if active_labels != ACTIVE_LABELS:
            raise ValueError("public symmetric circuit order differs")
        full_increment = _admission_limit(
            np.asarray(stepping.evol_metal_curr.coil_self_ind, dtype=float)[:12, :12],
            resistance, active_labels, baseline[:12],
        )
        if qualification_only:
            return {
                "eligible": bool(initial_valid),
                "full_p4_increment_v": full_increment,
                "initial_pickup_1_t": initial_pickup,
                "view": view,
                "runtime_s": time.monotonic() - started,
            }
        voltage, vector_sha = voltage_vector(baseline[:12], resistance, active_labels, increment_v)
        snapshots = {"0.000": initial_pickup}
        validity = bool(initial_valid)
        max_relative_change = 0.0
        domain_departed = False
        completed_steps = 0
        extrema_min = baseline[:12].copy()
        extrema_max = baseline[:12].copy()
        for step in range(1, round(_science_HORIZONS_S[-1] / _science_DT_S) + 1):
            if bool(stepping.handleMyy.check_Myy(stepping.hatIy)):
                domain_departed = True
                break
            stepping.nlstepper(
                active_voltage_vec=voltage,
                linear_only=False,
                verbose=0,
                max_solving_iterations=50,
            )
            completed_steps = step
            physical = np.asarray(stepping.vessel_currents_vec, dtype=float)
            extrema_min, extrema_max = current_extrema(extrema_min, extrema_max, physical[:12])
            relative = float(getattr(stepping.NK, "relative_change", 0.0))
            max_relative_change = max(max_relative_change, relative)
            clock = step * _science_DT_S
            if any(abs(clock - target) < 1e-12 for target in _science_HORIZONS_S):
                pickup, observed = _pickup_1(stepping.eq1)
                snapshots[format(clock, ".3f")] = pickup
                validity &= observed
    return assemble_canary_episode(
        active_labels=active_labels, extrema_min=extrema_min, extrema_max=extrema_max,
        validity=validity, domain_departed=domain_departed, snapshots=snapshots,
        completed_steps=completed_steps, view=view, word=word, increment_v=increment_v,
        vector_sha=vector_sha, max_relative_change=max_relative_change,
        runtime_s=time.monotonic() - started,
    )
