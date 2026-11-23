# SPDX-License-Identifier: MPL-2.0
"""Secondary checks on the original training operator, calibration and issued forecasts."""

from hashlib import sha256
import numpy as np
from scipy.linalg import expm
from scipy.integrate import quad
from empirical_lawhood.domains.matrix.path_thermodynamics.continuation import (
    HORIZONS,
    RECIPES,
    pulse_scales,
)
from empirical_lawhood.methods.linear_memory.elimination import impulse_hankel
from empirical_lawhood.methods.path_likelihood.scores import mean_interval
from empirical_lawhood.methods.retained_gaussian_response import HarmonicBath
from .forecasts import AR_MODELS, NAMES, recursive_mean
from .linear import maps, phase_basis


def harmonic_force_check():
    """Compare the reduced velocity convolution and hidden initial force to full acceleration."""
    initial = np.array([0.3, -0.4, 0.6, 0.8])
    errors = []
    for frequency in (1.0, 2.0):
        stiffness = np.array([[3.0, frequency], [frequency, frequency**2]])
        source = HarmonicBath(stiffness[:1, :1], stiffness[:1, 1:], stiffness[1:, 1:])
        evolution = np.block(
            [[np.zeros((2, 2)), np.eye(2)], [-stiffness, np.zeros((2, 2))]]
        )
        for t in (0.0, 0.125, 1.0):
            x = expm(t * evolution) @ initial
            history = quad(
                lambda s: (
                    source.memory(t - s)[0, 0] * (expm(s * evolution) @ initial)[2]
                ),
                0.0,
                t,
            )[0]
            force = source.initial_force(t, initial[:1], initial[1:2], initial[3:])[0]
            reduced = -source.effective_stiffness[0, 0] * x[0] - history + force
            errors.append(float(abs(reduced + stiffness[0] @ x[:2])))
    return max(errors)


def memory_diagnostics(options, model, development, evaluation):
    m, b, _, _, _ = maps(
        np.asarray(model["training_reference_q"]), float(options["timestep"]), options
    )
    visibility = np.eye(len(m))[:2]
    hidden = m[2:, 2:]
    tail = m[:2, 2:].copy()
    norms = []
    for lag in range(128):
        norms.append(float(np.linalg.norm(tail @ m[2:, :2])))
        tail = tail @ hidden
    operator = {
        "hankel": impulse_hankel(m, b[:, :1], visibility, (4, 8, 16, 32, 64)),
        "basis_sha256": sha256(
            np.asarray(phase_basis(), dtype="<f8").tobytes()
        ).hexdigest(),
        "hidden_spectral_radius": float(max(abs(np.linalg.eigvals(hidden)))),
        "hidden_resolvent_condition": float(
            np.linalg.cond(np.eye(len(hidden)) - hidden)
        ),
        "feedback_norm_by_lag": norms,
    }
    dev_history, dev_velocity, dev_levels = [], [], []
    for values in development:
        if len(values["evaluable_root"]):
            mask = values["split"] == 0
            dev_history.extend(values["history"][mask, 0])
            dev_velocity.extend(values["velocity"][mask, 0])
            dev_levels.extend(values["levels"][mask, 0].mean(axis=1))
    history, velocity, truth = map(np.asarray, (dev_history, dev_velocity, dev_levels))
    # All roots have the same phase and imposed drive. Keep the observed present and
    # substitute another root's 16 preceding displacements about its own endpoint.
    shuffled = history.copy()
    order = np.random.default_rng(20261123).permutation(len(history))
    shuffled[:, :-1] = history[:, -1:] + history[order, :-1] - history[order, -1:]
    shuffle = {}
    scales = np.asarray(model["scale"])
    for name, fit in zip(AR_MODELS, model["ar"], strict=True):
        if not name.startswith("history"):
            continue
        losses = []
        for h in (history, shuffled):
            forecast = recursive_mean(h, velocity, options, name, fit, RECIPES[:3])
            losses.append(np.mean(((forecast - truth) / scales) ** 2, axis=(1, 2, 3)))
        shuffle[name] = mean_interval(losses[1] - losses[0])
    coverage, observed_cov, native_sign, evaluated = {}, {}, {}, 0
    units = pulse_scales(options)
    for name, arm, mirror in (("single", 0, 2), ("blind_composition", 3, 4)):
        coverage[name], observed_cov[name], native_sign[name] = [], [], []
    for row in evaluation:
        if not len(row["evaluable_root"]):
            continue
        observed = row["levels"][:, 0]
        evaluated += len(observed)
        for name, arm, mirror in (("single", 0, 2), ("blind_composition", 3, 4)):
            truth = observed[:, :, arm]
            point = row["mean"][:, :, arm]
            hits = (
                np.abs(truth[:, None] - point[:, :, None])
                <= row["band_halfwidth"][:, :, None]
            )
            coverage[name].extend(hits.all(axis=-1).mean(axis=2))
            native_sign[name].extend(
                (observed[:, :, arm] - observed[:, :, mirror]).mean(axis=1) / 2
            )
            observed_cov[name].extend(
                np.array([np.cov(y[:, 0, 0], y[:, 2, 0])[0, 1] for y in truth])
            )
    results = {}
    for recipe in coverage:
        h = np.asarray(coverage[recipe])
        contrast = np.asarray(native_sign[recipe])
        results[recipe] = {
            "horizonwise_two_port_coverage": {
                name: h[:, i].mean(axis=0).tolist() for i, name in enumerate(NAMES)
            },
            "within_root_native_even_covariance_32_128": mean_interval(
                observed_cov[recipe]
            ),
            "reference_signed_native_mean": contrast.mean(axis=0).tolist(),
            "reference_signed_scaled_mean": (
                contrast.mean(axis=0) / units[:, None]
            ).tolist(),
        }
    return {
        "operator": operator,
        "harmonic_full_acceleration_max_error": harmonic_force_check(),
        "shuffled_development_excess_standardized_level_error": shuffle,
        "native_evaluation": results,
        "horizons": list(HORIZONS),
        "evaluable": evaluated,
        "unit": "independent preparation",
        "diagnostic_scope": "ADDITIONAL_READ_OF_ORIGINALS",
    }
