# SPDX-License-Identifier: MPL-2.0
"""Scientific controls on the concrete instrument and the shared observations."""

import json
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

import numpy as np
import pytest
from empirical_lawhood.domains.circuits.thermal_rc.assessment import (
    evaluate as assess_rc,
)
from empirical_lawhood.methods.path_likelihood.records import numerical_json
from empirical_lawhood.domains.circuits.thermal_rc import physics as rc
from empirical_lawhood.domains.circuits.thermal_rc.assessment import memory_score
from empirical_lawhood.domains.matrix.path_thermodynamics import instrument as matrix
from empirical_lawhood.domains.matrix.path_thermodynamics.observations import (
    window_labels,
)
from empirical_lawhood.domains.matrix.six_matrix_response.parameter_derivatives import (
    scheduled_force_step,
)
from empirical_lawhood.methods.path_likelihood import arrays
from empirical_lawhood.methods.path_likelihood.scores import bounded_path_kl


def test_voltage_seeds_are_shard_invariant_and_reverse_is_independent():
    a = rc.normals(323, 5, 8, 1)
    np.testing.assert_array_equal(
        a, np.concatenate([rc.normals(323, 2, 8, 1), rc.normals(325, 3, 8, 1)])
    )
    assert not np.array_equal(a, rc.normals(323, 5, 8, 2))
    for reverse in (True, False):
        for phase in rc.PHASES:
            for clock in (0.0, 0.25, 1.0):
                assert (
                    abs(
                        rc.means(phase, clock, reverse=reverse, driven=True)
                        - rc.independent_mean(
                            phase, clock, reverse=reverse, driven=True
                        )
                    )
                    < 1e-14
                )
    path = rc.stationary_path(a, [1.0, 1.0, 4.0], 0.25)
    assert memory_score(path, 4.0)["analytic"] == pytest.approx(
        (np.exp(-0.25) - np.exp(-1)) ** 2 / 2
    )
    assert memory_score(path, 1.0)["analytic"] == pytest.approx(0.0, abs=1e-14)


def test_original_array_bytes_and_critic_domain():
    data = {"root": np.arange(4, dtype="<i8"), "voltage": np.ones(4)}
    raw, metadata = arrays.encode(data)
    np.testing.assert_array_equal(arrays.decode(raw, metadata)["root"], data["root"])
    metadata["voltage"][2] = "0" * 64
    with pytest.raises(ValueError):
        arrays.decode(raw, metadata)
    with pytest.raises(ValueError):
        bounded_path_kl(np.array([0.1, 2.0]), np.zeros(2), bound=0.7, alpha=0.05)


def test_thermal_scientific_decisions_round_trip_through_the_native_product():
    settings = {"hidden_rate": "4"}
    result = assess_rc(settings, [rc.acquire(settings, 101, 64, None)], None)
    assert json.loads(numerical_json(result))["assigned"] == 64


def test_precision_panels_reuse_the_primary_assessments():
    from empirical_lawhood.domains.matrix.path_thermodynamics import assessment, physics
    from empirical_lawhood.domains.circuits.thermal_rc.assessment import (
        correlation_panel,
    )

    settings = {"hidden_rate": "4", "panel": "correlation"}
    block = rc.acquire(settings, 23, 64, None)
    assert set(block[1]) == {"root", "lag_voltages"}
    full = assess_rc(settings, [block], None)
    assert full["phases"]["positive"] == correlation_panel(
        block[1]["lag_voltages"], 0.0, True
    )
    recipe = (
        Path(__file__).resolve().parents[1]
        / "programmes/foundations/emergent-structure/workflows/matrix-path-thermodynamics/preparation-precision.json"
    )
    options = json.loads(recipe.read_bytes())["parameters"]
    b = physics.acquire(dict(options, retained_root=1), 1, 2, None)
    assert set(b[1]) == {"root", "evaluable_root", "transient"}
    dev = assessment.evaluate(options, [b], None)
    assert dev["transient"] == assessment.slopes(b[1]["transient"])
    assert assessment.evaluate(options, [b], dev)["decision"] == dev["decision"]


@pytest.mark.parametrize("amplitude", [0.0, 0.2])
def test_original_matrix_step_bytes_force_reversal_and_density(amplitude):
    root = Path(__file__).resolve().parents[1]
    recipe = (
        root
        / "programmes/foundations/emergent-structure/workflows/matrix-path-thermodynamics/smoke.json"
    )
    options = json.loads(recipe.read_bytes())["parameters"]
    state, _ = matrix.initial(1001, 1, options, jitter=0.03)
    tape = matrix.noise(matrix.rng(1001, 2), 1)[0]
    h = 0.001
    args = dict(
        direction=tape,
        amplitude=amplitude,
        member=matrix.MEMBER,
        numerical_view=matrix.view(h),
        next_alpha_tilde_x=state.alpha_tilde_x + 0.125,
        next_alpha_tilde_y=state.alpha_tilde_y,
        standardized_noise=tape,
    )
    direct = scheduled_force_step(state, **args)
    events = []
    recorded = scheduled_force_step(state, recorder=events.append, **args)
    for name in ("positions", "momenta"):
        assert getattr(direct, name).tobytes() == getattr(recorded, name).tobytes()
    (frame,) = events
    with pytest.raises(ValueError):
        frame.q_mid.setflags(write=True)
    for reverse in (False, True):
        ledger = matrix.Ledger(h, reverse=reverse)
        ledger.observe(frame)
        assert ledger.inverse_error < 1e-10
        assert ledger.ou_error < 1e-10
        assert ledger.jump_error < 1e-10
    decay = np.exp(-h)
    inverse = (-frame.p_minus + decay * frame.p_plus) / np.sqrt(1 - decay**2)
    back = scheduled_force_step(
        matrix.reversed_state(recorded),
        **dict(
            args, next_alpha_tilde_x=state.alpha_tilde_x, standardized_noise=inverse
        ),
    )
    np.testing.assert_allclose(back.positions, state.positions, atol=1e-13)
    np.testing.assert_allclose(back.momenta, -state.momenta, atol=1e-13)


def test_physical_reversal_precedes_causal_voltage_label():
    path = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]])
    for trailing in (True, False):
        true = window_labels(path[:, ::-1], 0.4, trailing=trailing)
        wrong = window_labels(path, 0.4, trailing=trailing)[:, ::-1]
        assert bool((true != wrong).any()) is trailing


@pytest.mark.parametrize(
    "family",
    [
        "thermal-rc",
        "matrix-path-thermodynamics",
        "matrix-orientation-response",
        "matrix-projected-memory",
        "marked-event-response",
    ],
)
def test_public_interruption_preserves_acquired_roots_and_decision(family):
    external = os.environ.get("EL_PATH_ENSEMBLE_TEST_STORAGE")
    if not external:
        pytest.skip(
            "select external conformance scratch with EL_PATH_ENSEMBLE_TEST_STORAGE"
        )
    root = Path(
        os.environ.get(
            "EL_PATH_ENSEMBLE_TEST_SOURCE", Path(__file__).resolve().parents[1]
        )
    )
    area = (
        "measurement-and-response"
        if family in ("thermal-rc", "marked-event-response")
        else "emergent-structure"
    )
    definition = (
        root / "programmes" / "foundations" / area / "workflows" / family / "smoke.json"
    )
    with tempfile.TemporaryDirectory(dir=external) as tmp:
        workspace = Path(tmp) / "experiment"

        def command(choice, *options):
            return [
                sys.executable,
                "-m",
                "empirical_lawhood.api.path_ensembles",
                choice,
                "--project-root",
                str(root),
                "--workspace",
                str(workspace),
                "--workers",
                "1",
                *options,
            ]

        subprocess.run(
            command("prepare", "--definition", str(definition)),
            check=True,
            capture_output=True,
        )
        run = subprocess.Popen(
            command("run"), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        receipts = workspace / "artifacts" / "runs"
        try:
            deadline = time.monotonic() + (900 if "matrix-" in family else 300)

            def evaluation_settled():
                # Recovery publishes this event after the original receipt and
                # its manifest settle. Staging files can appear earlier.
                for event in receipts.glob(
                    "*/recovery/*/events/*.evaluate.*/attempt-001.json"
                ):
                    value = json.loads(event.read_bytes())["value"]
                    if value["disposition"] == "SUCCEEDED":
                        path = workspace / "artifacts" / value["receipt_relative_path"]
                        if (
                            path.is_file()
                            and hashlib.sha256(path.read_bytes()).hexdigest()
                            == value["receipt_sha256"]
                        ):
                            return True
                return False

            while not evaluation_settled():
                if time.monotonic() >= deadline or run.poll() is not None:
                    raise AssertionError(
                        "control exited before a settled evaluation root"
                    )
                time.sleep(0.05)
            run.send_signal(signal.SIGINT)
            run.communicate(timeout=180)
            assert run.returncode != 0
        finally:
            if run.poll() is None:
                run.terminate()
                run.wait(timeout=30)

        def retained():
            return {
                p: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in receipts.glob("*/receipts/*/*attempt-???.json")
            }

        settled = retained()
        assert any(".freeze." in k.parent.name for k in settled)
        assert any(".evaluate." in k.parent.name for k in settled)
        assert not any(".assess." in k.parent.name for k in settled)
        subprocess.run(command("recover"), check=True, capture_output=True)
        report = json.loads(subprocess.check_output(command("read")))
        assert report["scientific_result"]["scientific_completion"] == "COMPLETED"
        assert report["new_native_contact_count"] == 0
        from empirical_lawhood.api.path_ensembles import portable_readout

        portable = portable_readout(report)
        assert len(portable["receipt_sha256"]) == report["task_count"]
        companion = next(
            v
            for v in report["retained_product_index"]
            if v["output_id"].endswith(".arrays")
        )
        companion["sha256"] = "0" * 64
        with pytest.raises(PermissionError, match="binary"):
            portable_readout(report)
        final = retained()
        assert all(final[path] == digest for path, digest in settled.items())
        assert all(p.name.endswith("attempt-001.json") for p in final)
