# SPDX-License-Identifier: MPL-2.0
"""Exposed PyBaMM lifecycle/DAE fixtures, never battery qualification."""

import gc
import importlib
import weakref

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.battery_thermal_inquiry.native import (
    detached_terminal_solution,
)

pytestmark = pytest.mark.native("pybamm")


@pytest.fixture(scope="module")
def pybamm():
    return importlib.import_module("pybamm")


def dae_model(pybamm):
    model = pybamm.BaseModel(name="exposed detached continuation DAE")
    x, z = pybamm.Variable("x"), pybamm.Variable("z")
    u = pybamm.InputParameter("u")
    model.rhs = {x: u - x}
    model.algebraic = {z: z - 2 * x}
    model.initial_conditions = {x: 0, z: 0}
    model.variables = {"x": x, "z": z}
    return pybamm.Discretisation().process_model(model)


def test_actual_solution_detaches_complete_state_derivative_sensitivity_and_events(pybamm):
    model = dae_model(pybamm)
    t = np.linspace(4, 9, 101)
    y = np.vstack((np.linspace(0, 1, 101), np.linspace(0, 2, 101)))
    yp = np.ones_like(y)
    sensitivity = np.arange(202.0).reshape(202, 1)
    inputs = np.array([3.0])
    y_event = y[:, -1:]
    solution = pybamm.Solution(
        t,
        y,
        model,
        {"u": inputs},
        t_event=t[-1:],
        y_event=y_event,
        termination="event: exposed [experiment]",
        all_yps=yp,
        all_sensitivities={"all": sensitivity},
        options={"compile": False},
    )
    solution.closest_event_idx = 3
    solution.solve_time, solution.integration_time, solution.set_up_time = 2, 3, 4
    # Deliberately materialize caches and processed receivers before detaching.
    solution["x"](t)
    expected = solution.last_state
    solution_ref, trajectory_ref = weakref.ref(solution), weakref.ref(y)
    terminal = detached_terminal_solution(solution)
    assert terminal.all_models[0] is model
    np.testing.assert_array_equal(terminal.all_ys[0], expected.all_ys[0])
    np.testing.assert_array_equal(terminal.all_yps[0], expected.all_yps[0])
    np.testing.assert_array_equal(
        terminal._all_sensitivities["all"][0], expected._all_sensitivities["all"][0]
    )
    assert terminal.t.tolist() == [9]
    assert (
        terminal.termination == solution.termination and terminal.closest_event_idx == 3
    )
    assert terminal.user_options == solution.user_options
    assert (terminal.solve_time, terminal.integration_time, terminal.set_up_time) == (
        2,
        3,
        4,
    )
    for copied, original in (
        (terminal.all_ys[0], y),
        (terminal.all_yps[0], yp),
        (terminal.all_inputs[0]["u"], inputs),
        (terminal._all_sensitivities["all"][0], sensitivity),
        (terminal.y_event, y_event),
        (terminal.t_event, t),
    ):
        assert not np.shares_memory(copied, original)
    assert terminal._sub_solutions == [] and terminal._variables == {}
    assert (
        "last_state" not in terminal.__dict__ and "first_state" not in terminal.__dict__
    )
    del expected, solution, y, y_event, t, original
    gc.collect()
    assert solution_ref() is None and trajectory_ref() is None
    assert terminal.all_ys[0].shape == (2, 1)  # RHS plus algebraic, never RHS-only.


def continuation(pybamm, detach):
    model = dae_model(pybamm)
    solver = pybamm.IDAKLUSolver(rtol=1e-9, atol=1e-9)
    before = solver.step(None, model, 1.0, inputs={"u": 1.0}, save=False)
    native_knots = before.t.copy()
    receiver = before["z"](native_knots).copy()
    terminal = detached_terminal_solution(before) if detach else before
    after = solver.step(terminal, model, 1.0, inputs={"u": 2.0}, save=False)
    return before, after, native_knots, receiver


def test_actual_exposed_dae_continuation_is_equivalent_after_detachment(pybamm):
    full_before, full_after, full_knots, full_receiver = continuation(pybamm, False)
    detached_before, detached_after, detached_knots, detached_receiver = continuation(
        pybamm, True
    )
    np.testing.assert_array_equal(detached_knots, full_knots)
    np.testing.assert_array_equal(detached_receiver, full_receiver)
    np.testing.assert_array_equal(detached_before.all_ys[0], full_before.all_ys[0])
    np.testing.assert_array_equal(detached_after.t, full_after.t)
    np.testing.assert_array_equal(detached_after.all_ys[0], full_after.all_ys[0])
    assert detached_after.t[-1] == full_after.t[-1] == 2.0
    np.testing.assert_allclose(
        detached_after.all_ys[0][1], 2 * detached_after.all_ys[0][0], atol=1e-9
    )
    assert detached_after.termination == full_after.termination


def test_output_only_or_truncated_state_cannot_be_detached(pybamm):
    model = dae_model(pybamm)
    output_only = pybamm.Solution(
        np.array([0.0, 1.0]), np.zeros((2, 2)), model, {}, variables_returned=True
    )
    with pytest.raises(ValueError, match="full native Solution"):
        detached_terminal_solution(output_only)
    missing_alg = pybamm.Solution(np.array([0.0, 1.0]), np.zeros((1, 2)), model, {})
    with pytest.raises(ValueError, match="RHS/algebraic"):
        detached_terminal_solution(missing_alg)
