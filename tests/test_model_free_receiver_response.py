# SPDX-License-Identifier: MPL-2.0
"""Controls for causal scalar delivery, coupled fallback and finite-frame decisions."""

import json

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.model_free import receiver_population as population
from empirical_lawhood.domains.matrix.model_free import receiver_preparation as preparation
from empirical_lawhood.domains.matrix.model_free import receiver_response as response


def test_original_packet_cannot_be_substituted_by_a_valid_looking_digest():
    selection = dict(preparation.ORIGINAL_IDENTITY, template_hex="", template_members={}, physical_design="{}")
    for key in preparation.ORIGINAL_IDENTITY:
        with pytest.raises(ValueError, match="substitutes another original"):
            preparation.instrument_operands({**selection, key: "0" * 64})


def test_cutoff_decision_uses_agreement_and_prefers_cheapest_eligible_prediction():
    settings = {"horizon_ticks": 64, "timestep": "0.001", "pulse_ticks": 16, "amplitude": "0.01"}
    instrument = {"force_roles": ["FACTOR"], "momentum_weights": [1.0]}
    options = response.DEFAULTS["M3"]
    scale = 0.01 * 0.016
    forecasts = []
    for refinement in (1, 2):
        for arm in preparation.ARMS:
            forecasts.append(
                {
                    "arm": arm,
                    "refinement": refinement,
                    "predictions": {
                        name: [[[scale * (0.003 if arm == "ORIGINAL" else 0.0)]]] for name in response.METHODS
                    },
                }
            )
    assert response._choose(forecasts, instrument, options, settings)["selected"] == "frozen"
    forecasts[2]["predictions"]["enriched-refresh"] = [[[scale * -0.002]]]
    assert response._choose(forecasts, instrument, options, settings)["selected"] == "native-fallback"


@pytest.mark.numerical(
    oracle="independent full propagation and lifted reduced map on a coupled two-coordinate oscillator"
)
def test_map_defect_reconstruction_survives_a_causal_change_of_basis():
    old = np.array([[2.0, 0.8], [0.8, 3.0]])
    new = np.array([[1.5, -1.1], [-1.1, 2.5]])
    full = np.eye(2)
    reduced = full[:, :1]
    source = reduced.copy()

    def maps(h, u):
        return u, response._maps(u.T @ h @ u, u, source, 0.001, 1.0, 0.01)

    material = {
        "frozen": maps(old, reduced),
        "fixed-refresh": maps(new, reduced),
        "enriched-refresh": maps(new, full),
        "full-frozen": maps(old, full),
        "full-refresh": maps(new, full),
    }
    costs = {"candidate_propagation_cpu_seconds": 0.0, "dense_propagation_cpu_seconds": 0.0}
    outputs, ranks, losses, defects = response._propagate(material, np.eye(4), 1, 16, costs)
    assert len(outputs["fixed-refresh"]) == 49
    assert ranks["enriched-refresh"] == [1, 2]
    assert losses["enriched-refresh"] == 0.0
    for term in defects.values():
        assert np.linalg.norm(term["inherited"]) > 1e-10
        assert term["raw_closure_error"] < 1e-17
    assert np.linalg.norm(defects["fixed-refresh"]["generated"]) > 1e-10
    assert np.max(np.abs(defects["enriched-refresh"]["generated"])) < 1e-17


def test_e4_and_sci02_schedules_remain_distinct():
    value = np.zeros((49, 4, 48))
    value[1, 0, 26] = 1.0
    clock = {"timestep": "0.001", "amplitude": "0.01", "pulse_ticks": 16, "horizon_ticks": 64}
    assert max(response._error_curve(value, clock, response.CHECKS)) == 0.0
    assert max(response._error_curve(value, clock, response.ALL_CHECKS)) > 0.0


def _population(wrong_view=False, undefined_unsampled=False):
    settings = {
        "receiver_study": population.DEFAULTS,
        "population": {"audit_size": 2, "frame_size": 4, "mode": "reveal_all"},
    }
    roots = []
    for seed in range(1, 5):
        value = float(seed) / 10
        case = {
            "sampling": {"audit_selected": seed in (1, 3), "frame_id": "frame"},
            "native_value": value,
            "auxiliary": value,
            "one_coefficient": value,
            "native_selected": True,
            "frame_member_defined": True,
            "native_cpu_seconds": 10.0,
            "supplier_dispositions": dict.fromkeys(("one_coefficient", "auxiliary"), "FROZEN_ORIGIN_HESSIAN"),
            "supplier_seconds": {"zero": 0.0, "one_coefficient": 0.1, "auxiliary": 1.0},
            "preparation_cpu_seconds": 1.0,
            "auxiliary_cpu_seconds": 1.1,
            "signed_arm_panel_values": {"2": [[value, value], [0.0, 0.0]]},
            "numerical_difference": 0.001 if seed == 2 and wrong_view else 0.0,
        }
        if undefined_unsampled and seed == 2:
            settings["population"]["mode"] = "sparse"
            case.update(frame_member_defined=False, native_value=None)
        assessed = population.analyse(settings, "M5", {"cases": [case]})
        roots.append({"seed": seed, **assessed})
    result = population.synthesise(settings, "M5", list(reversed(roots)), 0.05)
    return json.loads(json.dumps(result, allow_nan=False))


@pytest.mark.numerical(
    oracle="constant paired residual and exact enumeration of four-unit simple random samples"
)
def test_equal_precision_comparison_prices_the_cheapest_supplier_and_tracks_sample():
    result = _population()
    assert result["sampled_root_seeds"] == [1, 3]
    assert (
        result["finite_frame_comparisons"]["one_coefficient"]["full_frame_benchmark"][
            "chebyshev_halfwidth_at_risk"
        ]
        == 0.0
    )
    direct = result["costs"]["equal_precision_routes"]["zero"]
    assert direct["required_audit_roots"] == 4 and direct["expected_cpu_seconds"] == 44.0
    assert result["preferred_supplier"] == "one_coefficient"
    assert result["economically_supported_sparse_delivery"]
    result = _population(wrong_view=True)
    assert result["sampled_numerical_failures"] == 0
    assert result["all_observed_numerical_failures"] == 1
    assert not result["economically_supported_sparse_delivery"]
    result = _population(undefined_unsampled=True)
    assert result["undefined_frame_member_seeds"] == [2]
    assert result["finite_frame_mean"] is None
