# SPDX-License-Identifier: MPL-2.0
"""Independent nonlinear references and pre-outcome single/composed trajectory forecasts."""

import numpy as np
from empirical_lawhood.domains.matrix.matrix_factor_response.science import (
    native_position_coordinates,
)
from empirical_lawhood.domains.matrix.path_thermodynamics.continuation import (
    HORIZONS,
    RECIPES,
    driven_prefix,
    futures,
    pulse_scales,
)
from empirical_lawhood.methods.path_likelihood.forecast import role
from empirical_lawhood.methods.statistics.conditional_response import (
    fair_energy,
    paired_mean_loss,
    root_interval,
)
from .forecasts import NAMES, all_means, fit_models, signed
from .linear import analytic_controls, phase

STOCHASTIC_FORECAST = True


def prefix(root, options):
    private, work = driven_prefix(root, options, retain_orbit=False)
    if role(root, options) == 4:
        oracle, n = futures(
            root,
            private,
            options,
            recipes=RECIPES,
            tapes=options["oracle_tapes"],
            purpose=41,
            clocks=(1,),
        )
        private["oracle"] = oracle[0, 0]
        work += n
    return private, work


def observe(private, options):
    return {"history": private["history"], "velocity": private["velocity"]}


def reference(root, private, options, development):
    if development:
        trace, n = futures(
            root,
            private,
            options,
            recipes=RECIPES[:3],
            tapes=options["tapes"],
            purpose=35,
            clocks=(1,),
            trace=True,
        )
        fine, m = futures(
            root,
            private,
            options,
            recipes=RECIPES[:3],
            tapes=options["tapes"],
            purpose=35,
            clocks=(2,),
        )
        trajectories = trace[0, 0]
        return {
            "trace": trajectories,
            "levels": np.stack((trajectories[:, :, HORIZONS, :2], fine[0, 0])),
        }, n + m
    ref, n = futures(
        root, private, options, recipes=RECIPES, tapes=options["tapes"], purpose=35
    )
    return {"levels": ref[:, 0]}, n


def training(private, observed, truth, options):
    q, p = private["positions"][0], private["momenta"][0]
    return {
        **observed,
        **truth,
        "native_q": native_position_coordinates(q),
        "phase_state": phase(q, p),
    }


def fit(data, options):
    model, measured = fit_models(data, options)
    benchmark = analytic_controls()
    controls = measured["controls"]
    if (
        max(
            controls[k]
            for k in (
                "full_finite_error",
                "switched_error",
                "visible_basis_error",
                "affine_noise_force_error",
            )
        )
        > 1e-8
        or controls["hessian_gradient_fd_error"] > 1e-6
        or benchmark["memory_error"] > 1e-12
    ):
        raise ArithmeticError("native linear elimination or harmonic control failed")
    return dict(
        measured,
        model=model,
        harmonic_control=benchmark,
        training=int((data["split"] == 1).sum()),
        selection=int((data["split"] == 2).sum()),
    )


def predict(observed, model, options, random):
    centers = all_means(
        observed["history"][:1], observed["velocity"][:1], model, options
    )[0]
    z = random.normal(size=(options["predictive_draws"], 6))
    chol = np.array(model["cholesky"])
    draws = np.einsum("dk,mjk->mdj", z, chol).reshape(len(NAMES), len(z), 3, 2)
    sigma = np.sqrt((chol**2).sum(axis=-1)).reshape(len(NAMES), 3, 2)
    return {
        "mean": centers,
        "draws": centers[:, :, None] + draws[:, None],
        "band_halfwidth": sigma * np.array(model["band"])[:, None, None],
    }


def measured(private, prediction, truth, options):
    return {**truth, **prediction, "oracle": private["oracle"]}


def assess(data, model, options):
    level = data["levels"]
    means = np.concatenate((data["mean"], data["oracle"].mean(axis=1)[:, None]), axis=1)
    names = NAMES + ("native_shooting",)
    scale = np.asarray(model["scale"])
    unit = pulse_scales(options)
    signed_limit = float(options["margin"]) ** 2
    level_limit = float(options["level_margin"]) ** 2
    joint_limit = float(options["joint_margin"])
    winner = int(model["winner"])
    results = {}
    for composed, key in ((False, "single"), (True, "blind_composition")):
        recipe = 3 if composed else 0
        target = signed(level, options, composed)
        a, b = (x.mean(axis=2) for x in np.split(target, 2, axis=2))
        p = signed(means, options, composed)[:, :, 1, 0]
        mse = paired_mean_loss(p, a[:, 0, 1, 0, None], b[:, 0, 1, 0, None])
        fine = paired_mean_loss(p, a[:, 1, 1, 0, None], b[:, 1, 1, 0, None])
        v1, v2 = (x.mean(axis=2) for x in np.split(level, 2, axis=2))
        truth = level[:, 0, :, recipe]
        point = means[:, :, recipe]
        err = (
            paired_mean_loss(point, v1[:, 0, None, recipe], v2[:, 0, None, recipe])
            / unit[None, None, :, None] ** 2
        )
        scores = []
        for r, observed in enumerate(truth):
            y = (observed / scale).reshape(len(observed), -1)
            row = [
                fair_energy((d / scale).reshape(len(d), -1), y)
                for d in data["draws"][r, :, recipe]
            ]
            native = data["oracle"][r, :, recipe]
            row.append(fair_energy((native / scale).reshape(len(native), -1), y))
            scores.append(row)
        scores = np.array(scores)
        rows = {}
        for j, name in enumerate(names):
            # Simultaneous comparisons across fitted candidates; all nested tapes stay with their root.
            alpha = 0.05 / len(names)
            interval = lambda x: root_interval(x, alpha=alpha)
            s = interval(mse[:, j])
            bias = interval(fine[:, j] - mse[:, j])
            allowance = max(abs(bias["lower"]), abs(bias["upper"]))
            signed_ok = s["upper"] + allowance < signed_limit
            l = [interval(err[:, j, h, c]) for h in range(3) for c in range(2)]
            joint = interval(scores[:, j] - scores[:, -1])
            rows[name] = {
                "signed_squared": s,
                "fine_minus_coarse_squared": bias,
                "signed_within_margin": signed_ok,
                "level_squared_by_time_port": l,
                "level_within_margin": all(v["upper"] < level_limit for v in l),
                "energy": float(scores[:, j].mean()),
                "excess_energy_vs_native": joint,
                "joint_noninferior": joint["upper"] < joint_limit,
                "signed_gain_over_present": interval(mse[:, 1] - mse[:, j]),
                "mean_signed": float(p[:, j].mean()),
                "signed_direction_agreement": float(
                    np.mean(
                        np.sign(p[:, j]) == np.sign((a[:, 0, 1, 0] + b[:, 0, 1, 0]) / 2)
                    )
                ),
            }
            if j < len(NAMES):
                half = data["band_halfwidth"][:, j]
                hit = (abs(truth - point[:, j, None]) <= half[:, None]).all(
                    axis=(-1, -2)
                )
                cov = interval(hit.mean(axis=1))
                rows[name].update(
                    simultaneous_coverage=cov,
                    mean_band_width=(2 * half.mean(axis=0)).tolist(),
                    coverage_pass=cov["lower"] >= float(options["coverage_floor"]),
                )
                draws = data["draws"][:, j, recipe]
                rows[name]["cross_time_covariance_32_128_even"] = float(
                    np.mean([np.cov(d[:, 0, 0], d[:, 2, 0])[0, 1] for d in draws])
                )
                rows[name]["adequate"] = bool(
                    signed_ok
                    and rows[name]["level_within_margin"]
                    and rows[name]["joint_noninferior"]
                    and rows[name]["coverage_pass"]
                )
        results[key] = rows
    return {
        "selected": names[winner],
        "decisions": results,
        "selected_blind_adequate": results["blind_composition"][names[winner]][
            "adequate"
        ],
        "adequate_on_both": [
            n for n in NAMES if all(results[k][n]["adequate"] for k in results)
        ],
        "primary_clock": 1,
        "horizons": list(HORIZONS),
        "recipes": list(RECIPES),
        "tolerances": {
            "signed_rmse": options["margin"],
            "level_rmse": options["level_margin"],
            "joint_excess": options["joint_margin"],
            "coverage": options["coverage_floor"],
        },
        "interval_unit": "independent preparation",
        "actual_assignment_count": len(means),
        "training_native_recipes": list(RECIPES[:3]),
        "future_observation_updates": 0,
    }
