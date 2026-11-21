# SPDX-License-Identifier: MPL-2.0
"""Independent occupied-space controls and complete native return custody."""

from hashlib import sha256
import json
import numpy as np
import pytest

from empirical_lawhood.api.domain_composition.rubisco_response.crossing_orbitals import (
    CrossingOrbitalSources,
    read_crossing_orbitals,
)
from empirical_lawhood.methods.electronic_structure.occupied_space import (
    occupied_density_factors,
    compare_occupied_spaces,
    opposite_spin_frontier_densities,
)
from empirical_lawhood.methods.electronic_structure.populations import (
    spin_density_populations,
)
from empirical_lawhood.storage.checksum_manifest import checksum_manifest


@pytest.mark.numerical(oracle="two analytic opposite real orbital combinations in a nonorthogonal atomic basis")
def test_frontier_seed_keeps_the_core_and_both_spin_populations():
    metric = np.diag([4.0, 9.0, 16.0])
    orbitals = np.diag([0.5, 1 / 3, 0.25])
    a, b = opposite_spin_frontier_densities(orbitals, metric, 2)
    expected_total = np.diag([0.5, 1 / 9, 1 / 16])
    expected_spin = np.zeros((3, 3))
    expected_spin[1, 2] = expected_spin[2, 1] = 1 / 12
    np.testing.assert_allclose(a + b, expected_total, atol=1e-15)
    np.testing.assert_allclose(a - b, expected_spin, atol=1e-15)
    for matrix in (a, b):
        assert np.trace(matrix @ metric) == pytest.approx(2)
        np.testing.assert_allclose(matrix @ metric @ matrix, matrix, atol=1e-15)
    for bad, count in ((2 * orbitals, 2), (orbitals, 3), (orbitals, True),
                       (orbitals.astype(complex), 2)):
        with pytest.raises(ValueError):
            opposite_spin_frontier_densities(bad, metric, count)


@pytest.mark.numerical(
    oracle="orthogonal projections of two unit spin orbitals rotated by a known angle in a nonorthogonal AO metric"
)
def test_density_projection_preserves_occupied_metric_and_gauge():
    metric = np.diag([4.0, 9.0])
    bases = np.diag([0.5, 1 / 3])
    a, b = bases.T
    theta = np.pi / 6
    d = np.cos(theta) * a + np.sin(theta) * b
    left = occupied_density_factors(
        np.array([np.outer(a, a), np.outer(a, a)]), metric, (1, 1)
    )
    right = occupied_density_factors(
        np.array([np.outer(d, d), np.outer(d, d)]), metric, (1, 1)
    )
    result = compare_occupied_spaces(
        left, tuple(1j * block for block in right), metric, allow_spin_swap=False
    )
    assert result["smallest_squared_overlap"] == pytest.approx(np.cos(theta) ** 2)
    assert result["projection_loss_e"] == pytest.approx(2 * np.sin(theta) ** 2)
    np.testing.assert_allclose(result["squared_singular_values"], [[0.75], [0.75]])
    swapped = compare_occupied_spaces(
        (a[:, None], b[:, None]), (b[:, None], a[:, None]), metric, allow_spin_swap=True
    )
    assert swapped["spin_swap"] and swapped[
        "losses_in_direct_then_swapped_order_e"
    ] == pytest.approx([2, 0])


def test_rank_spin_selection_and_missing_sectors():
    zero = np.zeros((2, 2))
    metric = np.eye(2)
    blocks = occupied_density_factors([np.diag([1.0, 0.0]), zero], metric, (1, 0))
    result = compare_occupied_spaces(blocks, blocks, metric, allow_spin_swap=False)
    assert result["squared_singular_values"] == [[1.0], []]
    assert compare_occupied_spaces(None, blocks, metric, allow_spin_swap=True) == {
        "disposition": "missing converged determinant"
    }
    with pytest.raises(ValueError, match="counts"):
        compare_occupied_spaces(blocks, blocks, metric, allow_spin_swap=True)
    with pytest.raises(ValueError, match="exceeds unity"):
        compare_occupied_spaces(blocks, blocks, 2 * metric, allow_spin_swap=False)
    for density, count in (
        ([zero, zero], (1, 0)),
        ([np.diag([1.0, 0.5]), zero], (1, 0)),
        ([np.array([[1.0, 1.0], [0.0, 0.0]]), zero], (1, 0)),
        ([np.eye(2), zero], (True, 0)),
    ):
        with pytest.raises(ValueError):
            occupied_density_factors(density, metric, count)


@pytest.mark.numerical(
    oracle="explicit two-atom partition of the diagonal of the spin density times the AO metric"
)
def test_selected_charge_and_spin_preserve_full_atomic_partition():
    overlap = np.array([[1.0, 0.2], [0.2, 1.0]])
    alpha = np.array([[0.6, 0.25], [0.25, 0.3]])
    beta = np.array([[0.4, -0.25], [-0.25, 0.7]])
    observed = spin_density_populations([alpha, beta], overlap, [0, 1], [2, 1], [1])
    assert observed["atom_populations_e"] == pytest.approx([1.0, 1.0])
    assert observed["atom_spin_e"] == pytest.approx([0.3, -0.3])
    assert observed["total_charge_e"] == pytest.approx(1.0)
    assert observed["selected_charge_e"] == pytest.approx(0.0)
    assert observed["selected_spin_e"] == pytest.approx(-0.3)
    closed = spin_density_populations(alpha + beta, overlap, [0, 1], [2, 1], [0, 1])
    assert closed["selected_spin_e"] == 0 and closed[
        "selected_charge_e"
    ] == pytest.approx(1.0)
    for bad in ([1, 1], [-1], [True]):
        with pytest.raises(ValueError):
            spin_density_populations(alpha, overlap, [0, 1], [2, 1], bad)


def test_source_manifest_requires_original_and_unique_members():
    row = b"0" * 64 + b"  ./record\n"
    for content in (row + row, row.replace(b"./record", b"../record"), b""):
        with pytest.raises(ValueError):
            checksum_manifest(content, sha256(content).hexdigest())
    with pytest.raises(ValueError):
        checksum_manifest(row, "1" * 64)


def sample_return(root):
    content = {}

    def write(name, obj):
        raw = obj if type(obj) is bytes else json.dumps(obj, sort_keys=True).encode()
        dest = root / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        dig = sha256(raw).hexdigest()
        content[name] = dig
        return dig

    refs, cards = {}, []
    for case in ("V1-WT", "V1-I95M"):
        for wet in ("dry", "wet"):
            label = f"{case}-{wet}"
            cards.append(dict(name=label + "-O-I", case=case, hydration=wet))
            pre = "crossing-results-01/" + label
            dig = write(pre + "/point-0/native.npz", b"original density")
            write(pre + "/point-0/point.json", dict(fraction=0, native_sha256=dig))
            write(
                pre + "/completed.json",
                dict(
                    case=case, water=wet, evaluated_geometries=1, bracket_fraction=None
                ),
            )
            refs[label] = write(f"orbital-readback-01/{label}.json", {})
    source = write("prepared-02/states.json", dict(states=cards))
    write(
        "orbital-readback-01/finished.json",
        dict(threads=4, input_sha256=source, returned_sha256=refs),
    )
    write("crossing-results-01/finished.json", dict(completed=4, failed=0))
    manifest = b"".join(
        f"{value}  ./{key}\n".encode() for key, value in sorted(content.items())
    )
    (root / "SHA256SUMS").write_bytes(manifest)
    return CrossingOrbitalSources(root, sha256(manifest).hexdigest())


@pytest.mark.parametrize(
    "mutation,raise_during", [(False, False), (True, False), (True, True)]
)
def test_read_keeps_original_operands_guarded_through_comparison(
    tmp_path, monkeypatch, mutation, raise_during
):
    from empirical_lawhood.adapters.rubisco.rubisco_response import crossing_orbitals

    selection = sample_return(tmp_path)
    monkeypatch.setattr(
        crossing_orbitals,
        "require_orbital_runtime",
        lambda threads: {"threads": threads},
    )

    def consume(card, points, bracket):
        [(point, body)] = list(points)
        assert body == b"original density" and point["fraction"] == 0
        if mutation:
            name = card["name"].removesuffix("-O-I")
            (
                tmp_path / "crossing-results-01" / name / "point-0/native.npz"
            ).write_bytes(b"changed density!")
        if raise_during:
            raise RuntimeError("interrupted original receiver")
        return {"fraction": 0}

    monkeypatch.setattr(crossing_orbitals, "compare_crossing_path", consume)
    if mutation:
        with pytest.raises(ValueError, match="changed during consumption"):
            read_crossing_orbitals(selection)
    else:
        result = read_crossing_orbitals(selection)
        assert len(result["paths"]) == 4 and len(result["consumed_members"]) == 16
