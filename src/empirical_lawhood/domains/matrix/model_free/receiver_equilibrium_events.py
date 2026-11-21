# SPDX-License-Identifier: MPL-2.0
"""Signed restrained free-energy estimates and commitment after a physical entry."""

from dataclasses import replace
from decimal import Decimal
import math

import numpy as np

from empirical_lawhood.methods.model_free.events import (
    assess_first_passage,
    assess_paired_first_passage,
)
from empirical_lawhood.methods.model_free_response import (
    equilibrium_grid_estimate,
    equilibrium_importance_endpoint,
    equilibrium_variance_transport,
)
from . import native
from .receiver_campaign import WORK, decimal_value

DEFAULTS = {
    "M6": {
        "coordinates": ["nominal", "high-coupling", "high-temperature"],
        "primary_pair": ["nominal", "high-coupling"],
        "initial_shift": "0.4",
        "energy_budget_kbt": "0.048790164169432003",
        "overlap_ess_fraction": "0.10",
    },
    "M7": {
        "coordinates": ["nominal", "high-temperature"],
        "primary_coordinate": "high-temperature",
        "primary_histories": ["baseline", "joint-increasing"],
        "interior_radius": "0.025",
        "entry_window_ticks": 1024,
        "dwell_ticks": 16,
        "incidence_budget": "0.10",
        "rmst_budget": "0.256",
    },
}
NUMERIC_FAILURES = (FloatingPointError, np.linalg.LinAlgError, OverflowError)


def _names(values, length=None):
    return (
        type(values) is list
        and bool(values)
        and (length is None or len(values) == length)
        and all(type(v) is str and bool(v) for v in values)
        and len(set(values)) == len(values)
    )


def validate(module, opts, base):
    if not _names(opts["coordinates"]):
        raise ValueError(f"{module} requires a unique coordinate census")
    if module == "M6":
        if not _names(opts["primary_pair"], 2) or not set(opts["primary_pair"]) <= set(
            opts["coordinates"]
        ):
            raise ValueError(
                "M6 requires two distinct primary coordinates in its assigned census"
            )
        decimal_value(opts["initial_shift"], "M6 separated start")
        decimal_value(opts["energy_budget_kbt"], "M6 free energy budget")
        decimal_value(
            opts["overlap_ess_fraction"], "M6 ESS fraction", maximum=Decimal(1)
        )
    else:
        if opts["primary_coordinate"] not in opts["coordinates"] or not _names(
            opts["primary_histories"], 2
        ):
            raise ValueError(
                "M7 needs one primary coordinate and two ordered histories"
            )
        radius = decimal_value(opts["interior_radius"], "M7 allowed interior radius")
        if radius >= min(
            Decimal(str(base["events"]["upper_target"])),
            -Decimal(str(base["events"]["lower_target"])),
        ):
            raise ValueError(
                "M7 allowed entry region must lie strictly between both boundaries"
            )
        for key in ("dwell_ticks", "entry_window_ticks"):
            if type(opts[key]) is not int or opts[key] <= 0:
                raise ValueError(f"M7 needs a positive {key}")
        decimal_value(opts["incidence_budget"], "M7 risk budget", maximum=Decimal(1))
        decimal_value(opts["rmst_budget"], "M7 restricted mean physical time budget")


def _coordinates(settings, module):
    rows = {row["id"]: row for row in settings["native"]["coordinates"]}
    names = settings["receiver_study"][module]["coordinates"]
    if set(names) - rows.keys():
        raise ValueError(f"{module} selected a missing physical coordinate")
    return [rows[name] for name in names]


def case_ids(settings, module):
    from .science import _recipes

    rows = _coordinates(settings, module)
    opts = settings["receiver_study"][module]
    if module == "M6":
        a, b = (
            next(r for r in rows if r["id"] == name) for name in opts["primary_pair"]
        )
        if Decimal(a["temperature"]) != Decimal(b["temperature"]) or Decimal(
            a["cross_coupling"]
        ) == Decimal(b["cross_coupling"]):
            raise ValueError(
                "M6 primary contrast requires different couplings at the same temperature"
            )
        if Decimal(a["friction"]) != Decimal(b["friction"]):
            raise ValueError("M6 primary contrast must use the same friction")
        return [row["id"] for row in rows]
    if (
        not settings["receiver_study"]["M1"]["structural_service"]
        or not set(opts["coordinates"])
        <= set(settings["receiver_study"]["M1"]["coordinates"])
        or not set(opts["primary_histories"]) <= set(_recipes(settings))
        or opts["dwell_ticks"] >= settings["events"]["horizon_ticks"]
    ):
        raise ValueError(
            "M7 requires the original structural handoffs and a complete physical dwell"
        )
    return [r["id"] + "." + recipe for r in rows for recipe in _recipes(settings)]


def _work():
    return {**dict.fromkeys(WORK, 0), "counts_are_lower_bounds": False}


def _charge(total, raw):
    for key in WORK:
        total[key] += raw.get(key, 0)
    total["counts_are_lower_bounds"] |= raw.get("counts_are_lower_bounds", False)


def _harmonic_controls(centers, stiffness, ess_limit):
    """Compare an independently integrated normalized density against its analytic free energy."""
    from scipy.integrate import quad

    centers = np.asarray(centers)
    k0, beta = 2.0, 1.0
    rows = []

    def calculate(mu):
        def energy(x, s):
            return 0.5 * (k0 * (x - mu) ** 2 + stiffness * (x - s) ** 2)

        endpoint_partition = [
            quad(lambda x: math.exp(-beta * energy(x, s)), -np.inf, np.inf)[0]
            for s in (centers[0], centers[-1])
        ]
        measured = -math.log(endpoint_partition[1] / endpoint_partition[0]) / beta
        analytic = (
            k0
            * stiffness
            / (2 * (k0 + stiffness))
            * ((centers[-1] - mu) ** 2 - (centers[0] - mu) ** 2)
        )
        # For a restrained harmonic law the mean force is linear in the center.
        grid = float(
            np.trapezoid(k0 * stiffness / (k0 + stiffness) * (centers - mu), centers)
        )
        return np.array([measured, analytic, grid])

    baseline = calculate(0.0)
    for name, mu in [("identical", 0.0), ("shifted", 0.5)]:
        integrated, analytic, grid = calculate(mu) - baseline
        rows.append(
            {
                "control": name,
                "signed_log_partition_difference": float(integrated),
                "analytic_signed_difference": float(analytic),
                "finite_grid_signed_difference": float(grid),
                "maximum_absolute_error": float(
                    max(abs(integrated - analytic), abs(grid - analytic))
                ),
            }
        )
    # For two equal-variance normal laws and samples from the proposal, E[w]=1
    # and E[w^2]=exp(delta^2/sigma^2). This population ratio is known exactly.
    return {
        "signed_controls": rows,
        "gaussian_overlap": [
            {
                "shift_in_sigma": delta,
                "population_ess_fraction": math.exp(-(delta**2)),
                "admissible": math.exp(-(delta**2)) >= ess_limit,
            }
            for delta in (0.0, 5.0)
        ],
    }


def _noise_blocks(stream, steps):
    """Draw the six Hermitian innovations in the native (4 diagonal, 6 real, 6 imaginary) order."""
    n = 4
    diagonal = np.diag_indices(n)
    upper = np.triu_indices(n, 1)
    for start in range(0, steps, 128):
        count = min(128, steps - start)
        normal = stream.normal(size=(count, 2, 3, n * n))
        matrices = np.empty((count, 2, 3, n, n), dtype="<c16")
        matrices[..., diagonal[0], diagonal[1]] = normal[..., :n]
        off_diagonal = (normal[..., 4:10] + 1j * normal[..., 10:]) / np.sqrt(2)
        matrices[..., upper[0], upper[1]] = off_diagonal
        matrices[..., upper[1], upper[0]] = off_diagonal.conj()
        yield from matrices


class _RestrainedPath:
    """Use the existing immutable native force cache on one fixed-parameter path."""

    def __init__(self, initial, coord, direction, center, stiffness, view):
        self.direction = direction
        self.lifted = native.native_position_lift(direction)
        self.center = center
        self.stiffness = stiffness
        self.parameters = native.parameters(initial, coord.member)
        self.cache = native.BAOABGradientCache()
        self.dt = float(view.timestep)
        self.decay = math.exp(-float(view.friction_gamma) * self.dt)
        self.noise_scale = math.sqrt(
            float(view.bath_temperature) * (1 - self.decay * self.decay)
        )

    def gradient(self, position):
        q = native.native_position_coordinates(position)
        return (
            self.cache.evaluate(position, self.parameters)
            + self.stiffness * (float(self.direction @ q) - self.center) * self.lifted
        )

    def advance(self, state, noise):
        momentum = native.hermitian_part(
            state.momenta - 0.5 * self.dt * self.gradient(state.positions)
        )
        position = native.hermitian_part(state.positions + 0.5 * self.dt * momentum)
        momentum = native.hermitian_part(
            self.decay * momentum + self.noise_scale * noise
        )
        position = native.hermitian_part(position + 0.5 * self.dt * momentum)
        momentum = native.hermitian_part(
            momentum - 0.5 * self.dt * self.gradient(position)
        )
        return replace(
            state, positions=position, momenta=momentum, step_index=state.step_index + 1
        )


def _independent_reference(c, row, seed, opts, eq):
    coord, initial = native.target_state(c, row)
    force, _ = native.physical_chart(c, eq["receiver_seed"])
    direction = force[:, 0]
    sign = (-1, 1)[int(native.rng(seed, 680).integers(2))]
    shift = sign * float(opts["initial_shift"])
    direction_matrix = native.native_position_lift(direction)
    initial = replace(initial, positions=initial.positions + shift * direction_matrix)
    fine = replace(coord.primary_view, timestep=coord.primary_view.timestep / 2)
    stiffness = float(eq["stiffness"])
    counters = {"native_force_evaluations": 0, "native_force_evaluations_attempted": 0}
    results = []
    for index, center in enumerate(eq["centers"]):
        stream = native.rng(seed, 681, index)
        state = initial
        values = []
        result = {
            "center": float(center),
            "samples": values,
            "completed_steps": 0,
            "status": "COMPLETED",
        }
        results.append(result)
        path = None
        try:
            native.guard(state, c)
            burn, limit = (
                2 * eq["burnin_ticks"],
                2 * (eq["burnin_ticks"] + eq["reference_ticks"]),
            )
            path = _RestrainedPath(
                initial, coord, direction, float(center), stiffness, fine
            )
            innovations = _noise_blocks(stream, limit)
            for tick in range(limit + 1):
                if tick >= burn and (tick - burn) % (2 * eq["stride"]) == 0:
                    value = float(
                        direction @ native.native_position_coordinates(state.positions)
                    )
                    if not math.isfinite(value):
                        raise FloatingPointError(
                            "Nonfinite independent restrained sample"
                        )
                    values.append(value)
                if tick < limit:
                    state = path.advance(state, next(innovations))
                    result["completed_steps"] = tick + 1
                    native.guard(state, c)
            result["mean"] = float(np.mean(values))
        except NUMERIC_FAILURES as error:
            result.update(status="UNAVAILABLE", reason=str(error))
        if path is not None:
            counters["native_force_evaluations"] += path.cache.completed_evaluations
            counters["native_force_evaluations_attempted"] += (
                path.cache.evaluation_attempts
            )
    return {
        "refinement": 2,
        "physical_start_shift": shift,
        "reference_ticks": eq["reference_ticks"],
        "centers": results,
        **counters,
        "counts_are_lower_bounds": any(r["status"] != "COMPLETED" for r in results),
        "stream": "INDEPENDENT_OF_SHORT_AND_SHARED_LONG_RECORDS_PAIRED_BETWEEN_ARMS",
    }


def _equilibrium(settings, seed, work):
    c, opts, eq = (
        settings["native"],
        settings["receiver_study"]["M6"],
        settings["equilibrium"],
    )
    outcomes = []
    for row in _coordinates(settings, "M6"):
        try:
            record = native.equilibrium_record(c, row, seed, eq)
        except native.NativeResponseFailure as error:
            record = {
                **error.partial_record,
                **error.partial_accounting,
                "status": "UNAVAILABLE",
                "reason": str(error),
                "coordinate": row,
            }
        _charge(work, record)
        independent = _independent_reference(c, row, seed, opts, eq)
        _charge(work, independent)
        outcomes.append(
            {
                "case_id": row["id"],
                "coordinate": row,
                "status": "COMPLETED"
                if record["status"] == "COMPLETED"
                and all(x["status"] == "COMPLETED" for x in independent["centers"])
                else "UNAVAILABLE",
                "primary": record,
                "independent": independent,
            }
        )
    return outcomes


def _analyse_equilibrium(case):
    primary, fine = case["primary"], case["independent"]
    rows = []
    for record in primary.get("center_records", []):
        values = np.asarray(record["samples"], dtype=float)
        n = record["sample_count"]
        halves = np.array_split(values[:, 0], 2)
        rows.append(
            {
                "center": record["center"],
                "short": record["mean"],
                "control": record["controlled_mean"],
                "shared_long": record["reference_mean"],
                "second_moment": float(np.mean(values[:n, 0] ** 2)),
                "lag_one_sample_covariance_q": float(
                    np.cov(values[:-1, 0], values[1:, 0], ddof=1)[0, 1]
                ),
                "shared_long_late_minus_early": float(
                    halves[1].mean() - halves[0].mean()
                ),
                "n_short": n,
                "n_long": len(values),
            }
        )
    return {
        "case_id": case["case_id"],
        "status": case["status"],
        "coordinate": case["coordinate"],
        "short_status": primary["status"],
        "short_reason": primary.get("reason"),
        "centers": rows,
        "importance": primary.get("importance", []),
        "independent_shift": fine["physical_start_shift"],
        "independent_centers": [
            {k: v for k, v in row.items() if k != "samples"}
            | {"sample_count": len(row["samples"])}
            for row in fine["centers"]
        ],
    }


def _synthesise_equilibrium(settings, roots, alpha):
    opts, eq = settings["receiver_study"]["M6"], settings["equilibrium"]
    centers = np.asarray(eq["centers"], dtype=float)
    stiffness = float(eq["stiffness"])
    ids = list(case_ids(settings, "M6"))
    base, primary_b = opts["primary_pair"]
    pairs = [[base, name] for name in ids if name != base]
    indexed = [{case["case_id"]: case for case in r["cases"]} for r in roots]
    pair_rows, marginal = [], []
    family = len(ids) * 6 + len(pairs) * 7
    cell_alpha = alpha / family
    controls = _harmonic_controls(
        centers, stiffness, float(opts["overlap_ess_fraction"])
    )

    def operands(selected):
        records = [[idx[key] for key in selected] for idx in indexed]
        temps = [float(r["coordinate"]["temperature"]) for r in records[0]]
        means = {
            column: np.asarray(
                [
                    [[p[column] for p in case["centers"]] for case in arms]
                    for arms in records
                ]
            )
            for column in ("short", "control", "shared_long", "second_moment")
        }
        means["independent_fine"] = np.asarray(
            [
                [[p["mean"] for p in case["independent_centers"]] for case in arms]
                for arms in records
            ]
        )
        logs = np.asarray(
            [
                [
                    [p["log_normalization_ratio"] for p in case["importance"]]
                    for case in arms
                ]
                for arms in records
            ]
        )
        ess = min(
            p["effective_sample_size"]
            for arms in records
            for case in arms
            for p in case["importance"]
        )
        weight = max(
            p["maximum_normalized_weight"]
            for arms in records
            for case in arms
            for p in case["importance"]
        )
        return temps, means, logs, ess, weight

    for names in [[name] for name in ids] + pairs:
        result = {"coordinates": names, "assigned_roots": len(roots)}
        destination = marginal if len(names) == 1 else pair_rows
        destination.append(result)
        absent = [
            {"seed": root["seed"], "coordinate": name}
            for root, idx in zip(roots, indexed)
            for name in names
            if idx[name]["status"] != "COMPLETED"
        ]
        if absent:
            result.update(
                status="UNRESOLVED",
                reason="INCOMPLETE_ASSIGNED_PAIRED_OR_MARGINAL_RECORD",
                missing=absent,
                decision="UNRESOLVED",
            )
            continue
        temperatures, means, logs, ess, max_weight = operands(names)
        paired = len(names) == 2
        beta = 1 / np.asarray(temperatures)

        def select(array):
            return array if paired else array[:, 0, :]

        sigma = {}
        for source in ("short", "shared_long", "control", "independent_fine"):
            sigma[source] = equilibrium_grid_estimate(
                select(stiffness * (centers - means[source])), centers, alpha=cell_alpha
            )
        sigma["coarse_grid"] = equilibrium_grid_estimate(
            select(stiffness * (centers[::2] - means["short"][..., ::2])),
            centers[::2],
            alpha=cell_alpha,
        )
        sigma["importance"] = equilibrium_importance_endpoint(
            select(logs), centers, beta if paired else beta[0], alpha=cell_alpha
        )
        targets = np.asarray([value["root_targets"] for value in sigma.values()])
        result.update(
            status="ESTIMATED",
            estimators=sigma,
            order=list(sigma),
            covariance_of_estimator_means=None
            if len(roots) < 2
            else (np.cov(targets, ddof=1) / len(roots)).tolist(),
            minimum_importance_ess_fraction=ess / eq["importance_samples"],
            maximum_normalized_weight=max_weight,
            importance_overlap_diagnostic="LOW"
            if ess / eq["importance_samples"] < float(opts["overlap_ess_fraction"])
            else "ABOVE_FLOOR",
            finite_estimator_scope="COMPLETE_ASSIGNED_ROOT_MEANS_FULL_TEMPORAL_CROSS_CENTER_AND_CROSS_ARM_DEPENDENCE",
        )
        if not paired:
            cases = [r[names[0]] for r in indexed]
            result["separated_initialisation_census"] = [
                {
                    "signed_shift": shift,
                    "roots": sum(c["independent_shift"] == shift for c in cases),
                }
                for shift in sorted({c["independent_shift"] for c in cases})
            ]
            result["temporal_diagnostics"] = [
                {
                    "center": center,
                    "mean_lag_one_sample_covariance_q": float(
                        np.mean(
                            [
                                case["centers"][i]["lag_one_sample_covariance_q"]
                                for case in cases
                            ]
                        )
                    ),
                    "mean_shared_long_late_minus_early": float(
                        np.mean(
                            [
                                case["centers"][i]["shared_long_late_minus_early"]
                                for case in cases
                            ]
                        )
                    ),
                    "short_observations_per_root": cases[0]["centers"][i]["n_short"],
                    "long_observations_per_root": cases[0]["centers"][i]["n_long"],
                }
                for i, center in enumerate(centers.tolist())
            ]
        if paired:
            result["independent_root_moment_transport"] = (
                equilibrium_variance_transport(
                    means["short"],
                    means["second_moment"],
                    centers,
                    beta,
                    stiffness=stiffness,
                    alpha=cell_alpha,
                )
            )
        same_temperature = len(set(temperatures)) == 1
        budget = (
            temperatures[0] * float(opts["energy_budget_kbt"])
            if same_temperature
            else None
        )
        half = sigma["short"]["normal_approximation_halfwidth"]
        precision_decision = (
            "OUTSIDE_FIXED_TEMPERATURE_TASK"
            if budget is None
            else "UNRESOLVED"
            if half is None
            else "WITHIN_APPROXIMATE_STATISTICAL_BUDGET"
            if half <= budget
            else "APPROXIMATE_STATISTICAL_BUDGET_EXCEEDED"
        )
        result.update(
            energy_budget=budget,
            finite_grid_statistical_decision=precision_decision,
            canonical_energy_decision="UNRESOLVED",
            approximately_precise_for_finite_grid=(
                None if budget is None or half is None else half <= budget
            ),
            fine_minus_primary=float(
                sigma["independent_fine"]["mean"] - sigma["short"]["mean"]
            ),
            shared_long_minus_primary=float(
                sigma["shared_long"]["mean"] - sigma["short"]["mean"]
            ),
            finite_step_and_preparation_bias_bound=None,
            continuous_quadrature_bound=None,
            canonical_total_error_bound=None,
            decision="UNRESOLVED",
            reason="CANONICAL_PREPARATION_FINITE_STEP_AND_QUADRATURE_BIASES_UNBOUNDED"
            if same_temperature
            else "TEMPERATURE_STRESS_COMPARISON_OUTSIDE_FIXED_TEMPERATURE_ENERGY_BUDGET",
        )
    return {
        "decision": "UNRESOLVED",
        "primary_pair": [base, primary_b],
        "budget_kbt": opts["energy_budget_kbt"],
        "budget_use": "MATRIX_FREE_ENERGY_SHARE_OF_LOG_RATE_BUDGET_AT_FIXED_PREFACTOR",
        "known_law_controls": controls,
        "marginals": marginal,
        "paired_equilibrium": pair_rows,
        "alpha_per_estimator": cell_alpha,
        "pair_convention": "SECOND_MINUS_FIRST_ENDPOINT_FREE_ENERGY_CHANGE",
        "measure": "exp(-beta*(native_potential+k/2*(a.q-s)^2)) dq dp",
        "basins_dividing_surface_kinetic_prefactor_and_transmission": "UNASSIGNED",
    }


def _hidden_commitment_controls(horizon, risk_budget):
    """Competing exponential clocks from a matched visible origin; history identifies the regime."""
    rows = []
    for label, arms in [
        ("equal", ((0.5, 0.5), (0.5, 0.5))),
        ("different", ((0.1, 0.9), (0.9, 0.1))),
        ("different-holding-time", ((0.5, 0.5), (0.25, 0.25))),
    ]:
        incidence, restricted = [], []
        for target, competing in arms:
            total = target + competing
            restricted.append(-math.expm1(-total * horizon) / total)
            incidence.append(target * restricted[-1])
        visible = sum(incidence) / 2
        visible_error = max(abs(v - visible) for v in incidence)
        rows.append(
            {
                "control": label,
                "hazards_target_competing": [list(v) for v in arms],
                "matched_visible_entry": 0,
                "target_incidence": incidence,
                "restricted_mean": restricted,
                "signed_incidence": incidence[1] - incidence[0],
                "signed_restricted_mean": restricted[1] - restricted[0],
                "visible_forecast": visible,
                "history_forecasts": incidence,
                "worst_visible_error": visible_error,
                "worst_history_error": 0.0,
                "visible_meets_budget": visible_error <= risk_budget,
                "history_meets_budget": True,
            }
        )
    return rows


def _side(x, low, high):
    return 1 if x >= high else (-1 if x <= low else 0)


class _ExitObservation:
    """Commitment time is the time the required physical dwell has been observed."""

    def __init__(self, dwell_steps):
        self.dwell_steps = dwell_steps
        self.first_step = None
        self.current_side = 0
        self.event = None
        self.event_step = None

    def observe(self, tick, side):
        if self.event is not None:
            return
        if side != self.current_side:
            self.current_side = side
            self.first_step = tick if side else None
        if side and tick - self.first_step >= self.dwell_steps:
            self.event, self.event_step = ("target" if side == 1 else "competing"), tick


def _committed_paths(
    settings, row, seed, replica, history, initial, direction, reference, work
):
    c, options, opts = (
        settings["native"],
        settings["events"],
        settings["receiver_study"]["M7"],
    )
    coord = native.coordinate(c, row)
    h = float(coord.primary_view.timestep)
    streams = (native.rng(seed, 692, replica), native.rng(seed, 693, replica))
    states = {r: replace(initial, step_index=initial.step_index * r) for r in (1, 2)}
    caches = {r: native.BAOABGradientCache() for r in states}
    views = {
        r: replace(coord.primary_view, timestep=coord.primary_view.timestep / r)
        for r in states
    }
    rules = {
        r: {
            "dwell": _ExitObservation(opts["dwell_ticks"] * r),
            "first": _ExitObservation(0),
        }
        for r in states
    }
    observed, failures = dict.fromkeys(states, 0), dict.fromkeys(states)
    low, high = float(options["lower_target"]), float(options["upper_target"])
    for step in range(options["horizon_ticks"]):
        active = [
            r
            for r in states
            if failures[r] is None
            and any(rule.event is None for rule in rules[r].values())
        ]
        if not active:
            break
        noise = native.hermitian_noise(rng=streams[0], q=2)
        bridge = native.hermitian_noise(rng=streams[1], q=2)
        innovations = {
            1: (noise,),
            2: native.split_parameter_innovations(coord, noise, bridge),
        }
        for refinement in active:
            try:
                for delta, value in enumerate(innovations[refinement], start=1):
                    state = native.step(
                        states[refinement],
                        coord,
                        value,
                        numerical=views[refinement],
                        cache=caches[refinement],
                    )
                    native.guard(state, c)
                    projection = (
                        float(
                            direction
                            @ native.native_position_coordinates(state.positions)
                        )
                        - reference
                    )
                    if not math.isfinite(projection):
                        raise FloatingPointError("Nonfinite event receiver")
                    tick = refinement * step + delta
                    occupancy = _side(projection, low, high)
                    for rule in rules[refinement].values():
                        rule.observe(tick, occupancy)
                    observed[refinement] = tick
                    states[refinement] = state
            except NUMERIC_FAILURES as error:
                failures[refinement] = str(error)
    output = {}
    for refinement, labels in rules.items():
        for label, rule in labels.items():
            if rule.event is not None:
                status = "event"
            elif failures[refinement] is not None:
                status = "failed"
            else:
                status = "administrative_censor"
            output[f"h{refinement}_{label}"] = {
                "root_id": str(seed),
                "replica": replica,
                "entry_history": history,
                "weight": 1 / options["replicas"],
                "event": rule.event,
                "status": status,
                "event_time": None
                if rule.event_step is None
                else rule.event_step / refinement * h,
                "observed_until": observed[refinement] / refinement * h,
                "failure": failures[refinement],
            }
        work["native_force_evaluations"] += caches[refinement].completed_evaluations
        work["counts_are_lower_bounds"] |= failures[refinement] is not None
    return output


def _event_case(settings, row, seed, history, handoff, source, work):
    c, options, opts = (
        settings["native"],
        settings["events"],
        settings["receiver_study"]["M7"],
    )
    case = {
        "case_id": row["id"] + "." + history,
        "coordinate": row,
        "entry_history": history,
        "status": "COMPLETED",
        "fixed_occupancy": "unobserved",
        "wait_ticks": 0,
        "futures": [],
    }
    if handoff is None or handoff.get("state") is None:
        return {
            **case,
            "status": "UNAVAILABLE",
            "entry_status": "UNKNOWN",
            "reason": "FIXED_HANDOFF_UNAVAILABLE",
        }
    coord, ideal = native.target_state(c, row)
    force, _ = native.physical_chart(c, options["receiver_seed"])
    direction = force[:, 0]
    state = native.restore(handoff["state"])
    reference = float(direction @ native.native_position_coordinates(ideal.positions))

    def displacement(state):
        return (
            float(direction @ native.native_position_coordinates(state.positions))
            - reference
        )

    initial_q = displacement(state)
    low, high = float(options["lower_target"]), float(options["upper_target"])
    side = _side(initial_q, low, high)
    case.update(
        fixed_displacement=initial_q,
        common_absolute_reference=reference,
        fixed_tick=handoff["tick"],
        fixed_occupancy={-1: "competing", 0: "between_boundaries", 1: "target"}[side],
    )
    if options["require_admitted_entry"] and not handoff["present"]:
        observed = next(
            (o for o in source["observations"] if o["tick"] == handoff["tick"]), None
        )
        values = (
            []
            if observed is None
            else [
                observed["factors"][s]["raw_admitted"]
                for s in settings["formation"]["required_sectors"]
            ]
        )
        if False in values:
            return {**case, "entry_status": "NO_STRUCTURAL_ADMISSION"}
        return {
            **case,
            "status": "UNAVAILABLE",
            "entry_status": "UNKNOWN",
            "reason": "UNIDENTIFIABLE_STRUCTURAL_ENTRY",
        }
    # The terminal Hamiltonian applies at this common physical handoff on each branch.
    terminal = replace(
        state, alpha_tilde_x=float(coord.target_x), alpha_tilde_y=float(coord.target_y)
    )
    account = native.protocol_work_account()
    cache = native.BAOABGradientCache()
    previous = None
    stream = native.rng(seed, 691)
    try:
        if (state.alpha_tilde_x, state.alpha_tilde_y) != (
            terminal.alpha_tilde_x,
            terminal.alpha_tilde_y,
        ):
            account.record_jump(
                native._potential,
                state.positions,
                native.parameters(state, coord.member),
                native.parameters(terminal, coord.member),
            )
        state = terminal
        for tick in range(opts["entry_window_ticks"] + 1):
            q_now = displacement(state)
            if abs(q_now) <= float(opts["interior_radius"]):
                case.update(
                    entry_status="ENTERED",
                    entry_displacement=q_now,
                    history_increment=None if previous is None else q_now - previous,
                    entry_checkpoint_sha256=native.checkpoint(state)["sha256"],
                )
                break
            if tick < opts["entry_window_ticks"]:
                previous = q_now
                state = native.step(
                    state, coord, native.hermitian_noise(rng=stream, q=2), cache=cache
                )
                native.guard(state, c)
                case["wait_ticks"] = tick + 1
        else:
            case["entry_status"] = "NO_INTERIOR_BEFORE_DEADLINE"
        if case["entry_status"] == "ENTERED":
            for replica in range(options["replicas"]):
                case["futures"].append(
                    _committed_paths(
                        settings,
                        row,
                        seed,
                        replica,
                        history,
                        state,
                        direction,
                        reference,
                        work,
                    )
                )
            if any(
                path["status"] == "failed"
                for future in case["futures"]
                for path in future.values()
            ):
                case.update(
                    status="UNAVAILABLE", reason="FAILED_FUTURE_RETAINS_OBSERVED_PREFIX"
                )
    except NUMERIC_FAILURES as error:
        case.update(status="UNAVAILABLE", reason=str(error))
        case.setdefault("entry_status", "UNKNOWN")
        work["counts_are_lower_bounds"] = True
    case["handoff_work"] = account.summary(complete=case["entry_status"] != "UNKNOWN")
    work["native_force_evaluations"] += cache.completed_evaluations
    work["native_energy_evaluations"] += account.potential_evaluations_completed
    return case


def _attempted(rows, seed, history, replicas, view):
    by_replica = {future[view]["replica"]: future[view] for future in rows}
    return [
        by_replica.get(
            i,
            {
                "root_id": str(seed),
                "replica": i,
                "entry_history": history,
                "weight": 1 / replicas,
                "event": None,
                "status": "failed",
                "event_time": None,
                "observed_until": 0.0,
                "reason": "ASSIGNED_ENTERED_FUTURE_UNAVAILABLE",
            },
        )
        for i in range(replicas)
    ]


def _bounded_risk(assigned, alpha):
    """Equally weighted bounded root measurements, each with its own missing-data bounds."""
    data = np.asarray(assigned, dtype=float)
    bounds = data.mean(axis=0)
    band = math.sqrt(math.log(4 / alpha) / (2 * len(data)))
    return {
        "assigned_roots": len(data),
        "completion_bounds": bounds.tolist(),
        "confidence_bounds": [
            max(0.0, float(bounds[0] - band)),
            min(1.0, float(bounds[1] + band)),
        ],
    }


def _tolerance(bounds, budget):
    if bounds is None:
        return "UNRESOLVED"
    if max(abs(x) for x in bounds) <= budget:
        return "WITHIN_BUDGET"
    if bounds[0] > budget or bounds[1] < -budget:
        return "DIFFERENCE_EXCEEDS_BUDGET"
    return "UNRESOLVED"


def _synthesise_events(settings, roots, alpha):
    opts, config = settings["receiver_study"]["M7"], settings["events"]
    replica_count = config["replicas"]
    h = float(settings["native"]["timestep"])
    horizon = h * config["horizon_ticks"]
    indexed = [{case["case_id"]: case for case in root["cases"]} for root in roots]
    ids = case_ids(settings, "M7")
    views = ("h1_dwell", "h2_dwell", "h1_first", "h2_first")
    grid = [h * t for t in config["time_grid_ticks"]]
    # Each generic passage bound further splits its own declared time menu.
    allowance = alpha / (len(ids) * (len(views) * 4 + 4) + 3)
    rows, service_bounds = [], {}
    for name in ids:
        cases = [idx[name] for idx in indexed]
        records = {view: [] for view in views}
        known_entry = sum(c["entry_status"] == "ENTERED" for c in cases)
        unknown_entry = sum(c["entry_status"] == "UNKNOWN" for c in cases)
        result = {
            "case_id": name,
            "coordinate": cases[0]["coordinate"]["id"],
            "entry_history": cases[0]["entry_history"],
            "assigned_roots": len(roots),
            "entered_roots": known_entry,
            "unknown_entry_roots": unknown_entry,
            "assigned_replica_slots": len(roots) * replica_count,
            "eligible_future_slots": known_entry * replica_count,
            "initial_occupancy": {
                key: sum(c["fixed_occupancy"] == key for c in cases)
                for key in ("target", "competing", "between_boundaries", "unobserved")
            },
            "entry_census": {
                key: sum(c["entry_status"] == key for c in cases)
                for key in (
                    "ENTERED",
                    "NO_STRUCTURAL_ADMISSION",
                    "NO_INTERIOR_BEFORE_DEADLINE",
                    "UNKNOWN",
                )
            },
            "entry_probability": _bounded_risk(
                [
                    [
                        int(c["entry_status"] == "ENTERED"),
                        int(c["entry_status"] in ("ENTERED", "UNKNOWN")),
                    ]
                    for c in cases
                ],
                allowance,
            ),
            "mean_paid_entry_wait_physical_time_per_assignment": float(
                np.mean([c["wait_ticks"] * h for c in cases])
            ),
            "entry_wait_scope": "AFTER_PAID_M1_FIXED_HANDOFF_INCLUDES_ALL_COMPLETED_WAIT_PREFIXES",
        }
        risk_bounds, forecast = (
            [],
            {label: [] for label in ("visible_sign", "last_entry_increment")},
        )
        for root, case in zip(roots, cases):
            status = case["entry_status"]
            if status != "ENTERED":
                risk_bounds.append([0.0, float(status == "UNKNOWN")])
                continue
            for view in views:
                records[view].extend(
                    _attempted(
                        case["futures"],
                        root["seed"],
                        case["entry_history"],
                        replica_count,
                        view,
                    )
                )
            paths = records["h1_dwell"][-replica_count:]
            observed_target = sum(p["event"] == "target" for p in paths)
            unknown = sum(p["status"] in ("failed", "truncated") for p in paths)
            risk_bounds.append(
                [
                    observed_target / replica_count,
                    (observed_target + unknown) / replica_count,
                ]
            )
            for method, cue in [
                ("visible_sign", case["entry_displacement"]),
                ("last_entry_increment", case["history_increment"]),
            ]:
                if cue is None:
                    forecast[method].append([0.0, 1.0])
                else:
                    errors = sum(
                        (p["event"] == "target") != (cue >= 0.0)
                        for p in paths
                        if p["status"] not in ("failed", "truncated")
                    )
                    forecast[method].append(
                        [errors / replica_count, (errors + unknown) / replica_count]
                    )
        service_bounds[name] = np.asarray(risk_bounds)
        result["target_service_per_original_assignment"] = _bounded_risk(
            risk_bounds, allowance
        )
        result["previous_motion_and_visible_forecast_risk_among_entered"] = {
            key: None if not values else _bounded_risk(values, allowance)
            for key, values in forecast.items()
        }
        result["history_forecast_availability"] = {
            "entered_roots": known_entry,
            "observed_previous_physical_increment": sum(
                c["entry_status"] == "ENTERED"
                and c.get("history_increment") is not None
                for c in cases
            ),
            "unavailable_history_risk_bounds": [0.0, 1.0],
        }
        result["entered_views"] = []
        for view in views:
            paths = records[view]
            for target in ("target", "competing"):
                if not paths:
                    result["entered_views"].append(
                        {
                            "view": view,
                            "event": target,
                            "status": "UNRESOLVED",
                            "reason": "NO_OBSERVED_INTERIOR_ENTRY",
                        }
                    )
                    continue
                assessed = assess_first_passage(
                    paths,
                    horizon=horizon,
                    target_event=target,
                    time_grid=grid,
                    alpha=allowance,
                )
                censored = sum(p["status"] == "administrative_censor" for p in paths)
                unknown = sum(p["status"] in ("failed", "truncated") for p in paths)
                target_count = sum(p["event"] == target for p in paths)
                result["entered_views"].append(
                    {
                        "view": view,
                        "event": target,
                        "assessment": assessed,
                        "observed_normalized_eventual_incidence_bounds": [
                            target_count / len(paths),
                            (target_count + censored + unknown) / len(paths),
                        ],
                        "eventual_scope": "ABSORBING_COMMITMENTS_AFTER_KNOWN_ENTRY_ADMINISTRATIVE_AND_UNKNOWN_MASS_RETAINED",
                    }
                )
        differences = []
        for case in cases:
            for future in case["futures"]:
                first, second = future["h1_dwell"], future["h2_dwell"]
                if first["status"] == "failed" or second["status"] == "failed":
                    differences.append(None)
                else:
                    differences.append(
                        (
                            first["event"] != second["event"],
                            abs(
                                (
                                    horizon
                                    if first["event_time"] is None
                                    else first["event_time"]
                                )
                                - (
                                    horizon
                                    if second["event_time"] is None
                                    else second["event_time"]
                                )
                            ),
                        )
                    )
        evaluated = [d for d in differences if d is not None]
        result["coupled_temporal_grid_sensitivity"] = {
            "evaluated_nested_futures": len(evaluated),
            "assigned_interior_futures": known_entry * replica_count,
            "different_commitment_labels": sum(d[0] for d in evaluated),
            "maximum_restricted_time_difference": max(
                (d[1] for d in evaluated), default=None
            ),
        }
        rows.append(result)
    histories = opts["primary_histories"]
    names = [opts["primary_coordinate"] + "." + history for history in histories]
    a, b = (service_bounds[name] for name in names)
    differences = np.column_stack((b[:, 0] - a[:, 1], b[:, 1] - a[:, 0]))
    average = differences.mean(axis=0)
    width = math.sqrt(2 * math.log(4 / allowance) / len(roots))
    ci = [max(-1.0, float(average[0] - width)), min(1.0, float(average[1] + width))]
    incidence_decision = _tolerance(ci, float(opts["incidence_budget"]))
    paired_assignments, paired_paths = [], []
    for root, by_id in zip(roots, indexed):
        both = [by_id[name] for name in names]
        if all(case["entry_status"] == "ENTERED" for case in both):
            paired_assignments.extend(
                {
                    "root_id": str(root["seed"]),
                    "replica": i,
                    "weight": 1 / replica_count,
                }
                for i in range(replica_count)
            )
            for case in both:
                paired_paths.extend(
                    _attempted(
                        case["futures"],
                        root["seed"],
                        case["entry_history"],
                        replica_count,
                        "h1_dwell",
                    )
                )
    paired = (
        assess_paired_first_passage(
            paired_paths,
            histories=histories,
            assignments=paired_assignments,
            horizon=horizon,
            time_grid=grid,
            alpha=allowance,
        )
        if paired_assignments
        else None
    )
    if paired is not None:
        paired["estimand"] = (
            "PAIRED_HISTORY_CONTRAST_CONDITIONAL_ON_BOTH_PHYSICAL_INTERIOR_ENTRIES"
        )
    rmst_ci = None if paired is None else paired["restricted_mean"]["confidence_bounds"]
    return {
        "decision": incidence_decision,
        "primary": {
            "coordinate": opts["primary_coordinate"],
            "histories": histories,
            "assigned_roots": len(roots),
            "sign": "SECOND_MINUS_FIRST_TARGET_SERVICE_PER_ORIGINAL_ASSIGNMENT",
            "completion_bounds": average.tolist(),
            "confidence_bounds": ci,
            "incidence_budget": opts["incidence_budget"],
            "decision": incidence_decision,
        },
        "both_arms_entered_estimand": paired,
        "restricted_mean_decision_among_both_entered": _tolerance(
            rmst_ci, float(opts["rmst_budget"])
        ),
        "rmst_budget_physical_time": opts["rmst_budget"],
        "horizon_physical_time": horizon,
        "known_law_controls": _hidden_commitment_controls(
            horizon, float(opts["incidence_budget"])
        ),
        "entry_and_passage": rows,
        "alpha_per_comparison": allowance,
        "grid_sensitivity_scope": "PAIRED_POST_ENTRY_VIEWS_START_FROM_THE_SAME_COARSE_OBSERVED_INTERIOR_STATE",
        "kinetic_scope": "FINITE_HORIZON_TWO_ABSORBING_COMMITMENTS_FROM_OBSERVED_INTERIOR_ENTRIES",
    }


def acquire(settings, seed, module, prerequisites, sampling, assigned_modules):
    from .science import _recipes

    case_ids(settings, module)
    work = _work()
    if module == "M6":
        cases = _equilibrium(settings, seed, work)
    else:
        by_case = {case["case_id"]: case for case in prerequisites["M1"]["cases"]}
        cases = []
        for row in _coordinates(settings, "M7"):
            for recipe in _recipes(settings):
                source = by_case[row["id"] + "." + recipe]
                cases.append(
                    _event_case(
                        settings,
                        row,
                        seed,
                        recipe,
                        source.get("checkpoints", {}).get("fixed"),
                        source,
                        work,
                    )
                )
    return {"cases": cases, "work_accounting": work}


def analyse(settings, module, payload):
    if module == "M7":
        replicas = settings["events"]["replicas"]
        names = {"h1_dwell", "h2_dwell", "h1_first", "h2_first"}
        for case in payload["cases"]:
            seen = set()
            for future in case["futures"]:
                if set(future) != names or case["entry_status"] != "ENTERED":
                    raise ValueError(
                        "M7 future changes its physical entry or assigned sensitivity views"
                    )
                identities = {
                    (
                        row["root_id"],
                        row["replica"],
                        row["entry_history"],
                        row["weight"],
                    )
                    for row in future.values()
                }
                if len(identities) != 1:
                    raise ValueError(
                        "M7 matched future views substitute another root, history or replica"
                    )
                root, replica, history, weight = identities.pop()
                if (
                    root != str(payload["seed"])
                    or type(replica) is not int
                    or not 0 <= replica < replicas
                    or replica in seen
                    or history != case["entry_history"]
                    or weight != 1 / replicas
                ):
                    raise ValueError(
                        "M7 future changes an assigned root, history, replica or weight"
                    )
                seen.add(replica)
            if (
                case["entry_status"] == "ENTERED"
                and case["status"] == "COMPLETED"
                and len(seen) != replicas
            ):
                raise ValueError("Complete native M7 entry omits an assigned future")
    return {
        "cases": [_analyse_equilibrium(c) for c in payload["cases"]]
        if module == "M6"
        else payload["cases"]
    }


def synthesise(settings, module, roots, alpha):
    return (
        _synthesise_equilibrium(settings, roots, alpha)
        if module == "M6"
        else _synthesise_events(settings, roots, alpha)
    )
