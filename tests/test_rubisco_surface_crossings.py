# SPDX-License-Identifier: MPL-2.0
"""Software controls for one bounded spin-crossing decision and its kinetic impulse."""

from decimal import Decimal, localcontext
import math

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.electronic_coupling_science import (
    oxygen_crossing_decision,
    oxygen_singlet_triplet_gap,
)
from empirical_lawhood.methods.electronic_structure.surface_crossing import (
    landau_zener_probability,
    locate_bracketed_energy_gap,
    rescale_crossing_velocity,
)


POINT = dict(
    incoming="T",
    coupling_squared_hartree2=0.007,
    coupling_squared_error_bound_hartree2=0.001,
    gap_speed_hartree_fs=0.05,
    minimum_resolved_gap_speed_hartree_fs=1e-12,
    hbar_hartree_fs=0.024188843265857,
    draw=0.9,
)


@pytest.mark.numerical(oracle="an affine two-state crossing at three eighths in either orientation")
@pytest.mark.parametrize("orientation", (1, -1))
def test_bracketed_oxygen_gap_retains_the_accepted_electronic_probe(orientation):
    seen = []

    def probe(fraction):
        state = {"fraction": fraction, "root": object()}
        seen.append(state)
        gap = oxygen_singlet_triplet_gap(singlet_hartree=orientation * (fraction - 0.375),
            triplet_hartree=0.0, alternate_ms0_hartree=1.0, lower_root_tolerance_hartree=1e-4,
            competition_window_hartree=0.01)
        return gap, state

    result = locate_bracketed_energy_gap(left_gap_hartree=orientation * -0.375,
        right_gap_hartree=orientation * 0.625, gap_tolerance_hartree=1e-5, maximum_probes=9, probe=probe)
    assert [state["fraction"] for state in seen] == [0.5, 0.25, 0.375]
    assert result.state is seen[-1]
    assert (result.fraction, result.gap_hartree, result.probes) == (0.375, 0, 3)


def test_gap_resolution_requires_an_observed_small_residual():
    seen = []

    def step(fraction):
        seen.append(fraction)
        return (-1 if fraction < 0.8 else 1), fraction

    kwargs = dict(left_gap_hartree=-1.0, right_gap_hartree=0.0,
        gap_tolerance_hartree=1e-5, maximum_probes=9, probe=step)
    for change in ({"left_gap_hartree": 1}, {"right_gap_hartree": math.nan},
                   {"gap_tolerance_hartree": 0}, {"maximum_probes": True}):
        with pytest.raises(ValueError):
            locate_bracketed_energy_gap(**(kwargs | change))
    assert seen == []
    with pytest.raises(ValueError, match="not located"):
        locate_bracketed_energy_gap(**kwargs)
    assert len(seen) == 9 and all(0 < x < 1 for x in seen)
    with pytest.raises(ValueError, match="finite"):
        locate_bracketed_energy_gap(**(kwargs | {"probe": lambda _: (math.nan, None)}))
    boundary = locate_bracketed_energy_gap(**(kwargs | {"probe": lambda _: (1e-5, "sample")}))
    assert boundary.probes == 1 and boundary.state == "sample"


def test_competing_ms0_state_refuses_the_same_probe():
    kwargs = dict(singlet_hartree=0.0, triplet_hartree=0.5, alternate_ms0_hartree=-1e-4,
        lower_root_tolerance_hartree=1e-4, competition_window_hartree=0.01)
    assert oxygen_singlet_triplet_gap(**kwargs) == -0.5
    with pytest.raises(ValueError, match="competes"):
        oxygen_singlet_triplet_gap(**(kwargs | {"alternate_ms0_hartree": -0.001}))
    assert oxygen_singlet_triplet_gap(**(kwargs | {"alternate_ms0_hartree": -0.001,
        "triplet_hartree": -0.5})) == 0.5
    for change in ({"alternate_ms0_hartree": math.nan}, {"competition_window_hartree": -1}):
        with pytest.raises(ValueError):
            oxygen_singlet_triplet_gap(**(kwargs | change))

    def failed_probe(_fraction):
        return oxygen_singlet_triplet_gap(**(kwargs | {"alternate_ms0_hartree": -0.1})), None

    with pytest.raises(ValueError, match="competes"):
        locate_bracketed_energy_gap(left_gap_hartree=-1, right_gap_hartree=1,
            gap_tolerance_hartree=1e-5, maximum_probes=9, probe=failed_probe)


@pytest.mark.numerical(
    oracle="high-precision exponential for one bright channel in a singlet and three equally populated triplet components"
)
@pytest.mark.parametrize("incoming,components", (("T", 3), ("S", 1)))
def test_brightness_and_original_draw_have_independent_bounds(incoming, components):
    args = {
        **POINT,
        "incoming": incoming,
        "coupling_squared_hartree2": 0.00007,
        "coupling_squared_error_bound_hartree2": 0.00001,
    }
    result = oxygen_crossing_decision(**args)
    with localcontext() as context:
        context.prec = 60
        pi = Decimal("3.14159265358979323846264338327950288419716939937510582097494")
        scale = Decimal("0.05") * Decimal("0.024188843265857")
        expected = [
            float((1 - (-2 * pi * x * components / scale).exp()) / components)
            for x in (Decimal("0.00006"), Decimal("0.00008"))
        ]
    assert result[:2] == pytest.approx(expected, rel=2e-15)
    lower, upper, _ = result
    for draw, fate in (
        (0.0, "ATTEMPT_HOP"),
        (lower, "UNRESOLVED"),
        ((lower + upper) / 2, "UNRESOLVED"),
        (upper, "STAY"),
    ):
        assert oxygen_crossing_decision(**{**args, "draw": draw}).decision == fate
    assert (
        landau_zener_probability(math.inf, donor_components=components)
        == 1 / components
    )


def test_zero_coupling_error_and_positive_uncertainty_across_zero():
    zero = {
        **POINT,
        "coupling_squared_hartree2": 0.0,
        "coupling_squared_error_bound_hartree2": 0.0,
        "draw": 0.0,
    }
    assert oxygen_crossing_decision(**zero) == (0.0, 0.0, "STAY")
    result = oxygen_crossing_decision(
        **{**zero, "coupling_squared_error_bound_hartree2": 1e-5}
    )
    assert result.lower_probability == 0 < result.upper_probability
    assert result.decision == "UNRESOLVED"


@pytest.mark.parametrize(
    "field,value",
    (
        ("incoming", "BS"),
        ("gap_speed_hartree_fs", 1e-12),
        ("minimum_resolved_gap_speed_hartree_fs", -1.0),
        ("coupling_squared_hartree2", -1e-6),
        ("coupling_squared_error_bound_hartree2", math.nan),
        ("hbar_hartree_fs", 0.0),
        ("draw", 1.0),
        ("draw", np.bool_(True)),
    ),
)
def test_unresolved_slope_and_invalid_state_inputs(field, value):
    with pytest.raises(ValueError, match="identified spin"):
        oxygen_crossing_decision(**{**POINT, field: value})


@pytest.mark.numerical(
    oracle="independent two-mass kinetic energy and conservation of the momentum orthogonal to the gap gradient"
)
@pytest.mark.parametrize("potential_change", (1.5, -1.5, 0.0))
def test_surface_impulse_conserves_energy_and_orthogonal_momentum(potential_change):
    velocity = np.array([[2.0, 0.2, -0.1], [-0.3, 1.1, 0.7]])
    masses = np.array([2.0, 7.0])
    gradient = np.array([[1.0, -0.1, 0.2], [-1.0, 0.1, -0.2]])
    result, allowed = rescale_crossing_velocity(
        velocity_nm_ps=velocity,
        masses_dalton=masses,
        gap_gradient=gradient,
        energy_change_kj_mol=potential_change,
    )
    assert allowed and not np.shares_memory(result, velocity)
    weights = masses[:, None]
    assert 0.5 * np.sum(weights * (velocity**2 - result**2)) == pytest.approx(
        potential_change, abs=2e-15
    )
    momentum_change = weights * (result - velocity)
    np.testing.assert_allclose(momentum_change.sum(axis=0), 0.0, atol=1e-15, rtol=0.0)
    np.testing.assert_allclose(
        np.cross(momentum_change, gradient), 0.0, atol=1e-15, rtol=0.0
    )
    changed_units, accepted = rescale_crossing_velocity(
        velocity_nm_ps=velocity,
        masses_dalton=masses,
        gap_gradient=-gradient * 1e-200,
        energy_change_kj_mol=potential_change,
    )
    assert accepted
    np.testing.assert_allclose(changed_units, result, atol=1e-15, rtol=0.0)


@pytest.mark.parametrize(
    "change,allowed,speed",
    ((1.5, True, math.sqrt(2.5)), (4.0, True, 0.0), (5.0, False, 2.0)),
)
def test_original_single_mass_control_and_threshold(change, allowed, speed):
    velocity = np.array([[2.0, 0.0, 0.0]])
    adjusted, outcome = rescale_crossing_velocity(
        velocity_nm_ps=velocity,
        masses_dalton=[2.0],
        gap_gradient=[[1.0, 0.0, 0.0]],
        energy_change_kj_mol=change,
    )
    assert outcome is allowed
    np.testing.assert_allclose(adjusted, [[speed, 0.0, 0.0]], atol=2e-15, rtol=0.0)
    assert not np.shares_memory(adjusted, velocity)


def test_flat_gradient_refuses_an_impulse_and_invalid_masses_or_arrays_fail():
    args = dict(
        velocity_nm_ps=[[1.0, 0.0, 0.0]],
        masses_dalton=[2.0],
        gap_gradient=[[0.0, 0.0, 0.0]],
        energy_change_kj_mol=-1.0,
    )
    adjusted, allowed = rescale_crossing_velocity(**args)
    assert not allowed
    np.testing.assert_array_equal(adjusted, args["velocity_nm_ps"])
    for field, value in (
        ("masses_dalton", [0.0]),
        ("velocity_nm_ps", [[np.nan, 0.0, 1.0]]),
        ("gap_gradient", [[1.0, 0.0]]),
        ("energy_change_kj_mol", math.inf),
    ):
        with pytest.raises(ValueError):
            rescale_crossing_velocity(**{**args, field: value})
