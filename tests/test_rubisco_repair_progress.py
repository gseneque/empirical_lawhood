# SPDX-License-Identifier: MPL-2.0
"""The best finite repair observation survives interruption and failed writes."""

import numpy as np
import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response.repair_progress import retain_evaluation


def test_progress_retains_exact_complete_arrays_without_completion(tmp_path):
    coordinates = np.array([[.031, 1., 2.], [.064, 1., 2.]])
    forces = np.array([[-3e8, 0., 0.], [3e8, 0., 0.]])
    retain_evaluation(tmp_path, 25, "initial-clash-descent", coordinates, 4e5, forces)
    with np.load(tmp_path / "lowest-energy-evaluation.npz", allow_pickle=False) as retained:
        assert np.array_equal(retained["coordinates_nm"], coordinates)
        assert np.array_equal(retained["forces_kj_mol_nm"], forces)
        assert retained["energy_kj_mol"] == 4e5 and retained["evaluation"] == 25
        assert retained["progress_only"] and retained["phase"] == "initial-clash-descent"
    assert {p.name for p in tmp_path.iterdir()} == {"lowest-energy-evaluation.npz"}


def test_invalid_progress_cannot_replace_the_original_finite_state(tmp_path, monkeypatch):
    original = np.ones((2, 3))
    retain_evaluation(tmp_path, 1, "openmm-initial", original, 20., original, first=True)
    path = tmp_path / "lowest-energy-evaluation.npz"
    before = path.read_bytes()
    for coordinates, energy, forces in ((original[:1], 10., original), (original * np.nan, 10., original),
                                        (original, 10., original * np.inf), (original, np.nan, original)):
        with pytest.raises(ValueError, match="complete finite"):
            retain_evaluation(tmp_path, 2, "openmm-iteration", coordinates, energy, forces)
    with pytest.raises(FileExistsError):
        retain_evaluation(tmp_path, 1, "openmm-initial", original, 5., original, first=True)

    def interrupted(stream, **fields):
        stream.write(b"partial")
        raise OSError("interrupted write")

    monkeypatch.setattr(np, "savez", interrupted)
    with pytest.raises(OSError, match="interrupted write"):
        retain_evaluation(tmp_path, 2, "openmm-iteration", original, 10., original)
    assert list(tmp_path.iterdir()) == [path]
    assert path.read_bytes() == before


@pytest.mark.native("openmm")
@pytest.mark.numerical(oracle="Harmonic bond energy and its analytic force on each particle, plus a constant force on the fixed anchor.")
def test_interrupted_minimizer_retains_full_physical_forces(tmp_path, monkeypatch):
    import openmm as mm
    from empirical_lawhood.adapters.rubisco.rubisco_response.library_construction import complete_amber_minimization

    system = mm.System()
    system.addParticle(12.)
    system.addParticle(1.)
    bond = mm.HarmonicBondForce()
    bond.addBond(0, 1, .109, 1000.)
    system.addForce(bond)
    anchor = mm.CustomExternalForce("11*x")
    anchor.addParticle(0, [])
    system.addForce(anchor)
    initial = np.array([[0., 0., 0.], [.2, 0., 0.]])
    minimize = mm.LocalEnergyMinimizer.minimize

    def interrupt_after_iteration(context, *, tolerance, maxIterations, reporter):
        minimize(context, tolerance=tolerance, maxIterations=1, reporter=reporter)
        raise InterruptedError("interrupted after native iteration")

    monkeypatch.setattr(mm.LocalEnergyMinimizer, "minimize", interrupt_after_iteration)
    for platform in ("Reference", "CPU"):
        directory = tmp_path / platform
        directory.mkdir()
        with pytest.raises(InterruptedError, match="after native iteration"):
            complete_amber_minimization(system, initial, (1,), maximum_component=1e-6,
                                        platform_name=platform, threads=1, progress_directory=directory)
        with np.load(directory / "lowest-energy-evaluation.npz", allow_pickle=False) as retained:
            points = retained["coordinates_nm"]
            assert np.array_equal(points[0], initial[0])
            displacement = points[1] - points[0]
            distance = np.linalg.norm(displacement)
            force = 1000. * (distance - .109) * displacement / distance
            np.testing.assert_allclose(retained["forces_kj_mol_nm"], [force - [11., 0., 0.], -force], atol=1e-10)
            assert retained["energy_kj_mol"] == pytest.approx(500. * (distance - .109)**2)
            assert retained["energy_kj_mol"] < 500. * (.2 - .109)**2
            assert retained["progress_only"] and retained["phase"] == "openmm-iteration"
            assert retained["evaluation"] >= 2
