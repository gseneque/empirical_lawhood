# SPDX-License-Identifier: MPL-2.0
"""Independent one-electron bounds, signed state contrasts and original-return lifetimes."""

from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.electronic.field_contrast import (
    HARTREE_KCAL_MOL,
    four_state_field_contrast,
)
from empirical_lawhood.methods.electronic_structure.field_energy import (
    field_energy_bounds,
)
from empirical_lawhood.storage.checksum_manifest import selected_checksum_members


@pytest.mark.numerical(
    oracle="In an orthonormal eigenbasis with levels −2, 1 and 4, two alpha and zero beta electrons give [−1,5]. A common nonsingular change of basis preserves both extrema and the frozen trace."
)
def test_spectral_bounds_and_density_work_are_basis_invariant():
    levels = np.diag([-2.0, 1.0, 4.0])
    density = np.stack((np.diag([0.25, 0.75, 1.0]), np.zeros((3, 3))))
    transform = np.array([[1, 0.3j, 0.4], [0, 2.0, 0.1], [0, 0, 0.5]])
    inv = np.linalg.inv(transform)
    for h, s, dm in (
        (levels, np.eye(3), density),
        (
            transform.conj().T @ levels @ transform,
            transform.conj().T @ transform,
            inv @ density @ inv.conj().T,
        ),
    ):
        observed = field_energy_bounds(h, s, 0.5, (2, 0), density=dm)
        assert [observed.lower, observed.upper, observed.frozen] == pytest.approx(
            [-0.5, 5.5, 4.75]
        )
        assert [
            observed.lowest_orbital_shift,
            observed.highest_orbital_shift,
        ] == pytest.approx([-2, 4])
    empty = field_energy_bounds(levels, np.eye(3), 0.5, (0, 0))
    assert empty.lower == empty.upper == 0.5 and empty.frozen is None


@pytest.mark.parametrize(
    "bad",
    [
        np.diag([1.0, 1.0, 1.0]),
        np.diag([3.0, -1.0, 0.0]),
        np.array([[0.0, 1.0], [0.0, 0.0]]),
    ],
)
def test_inadmissible_frozen_density_refused(bad):
    with pytest.raises(ValueError):
        field_energy_bounds(np.eye(3), np.eye(3), 0.0, (1, 1), density=bad)


@pytest.mark.numerical(
    oracle="Four signed intervals [1,2],[3,4],[5,6],[7,8] in C-TS,C-P,O-II,O-I order give endpoints −2,2, including reversed limits on both subtractions."
)
def test_four_state_accumulation_keeps_missing_density_and_orientation():
    states = {
        name: {"variational_interval_Eh": bounds, "frozen_density_shift_Eh": bounds[0]}
        for name, bounds in zip(
            ("C-TS", "C-P", "O-II", "O-I"),
            ((1, 2), (3, 4), (5, 6), (7, 8)),
            strict=True,
        )
    }
    value = four_state_field_contrast(states)
    assert value["four_state_interval_kcal_mol"] == pytest.approx(
        [-2 * HARTREE_KCAL_MOL, 2 * HARTREE_KCAL_MOL]
    )
    assert value["frozen_four_state_shift_kcal_mol"] == 0
    states["O-II"]["frozen_density_shift_Eh"] = None
    assert four_state_field_contrast(states)["frozen_four_state_shift_kcal_mol"] is None
    del states["O-II"]
    with pytest.raises(ValueError, match="complete four-state"):
        four_state_field_contrast(states)


def test_original_member_access_requires_its_active_context_and_thread(tmp_path):
    path = tmp_path / "field.bin"
    path.write_bytes(b"signed field")
    body = sha256(path.read_bytes()).hexdigest()
    root = tmp_path / "SHA256SUMS"
    root.write_bytes(f"{body}  ./field.bin\n".encode())
    with selected_checksum_members(tmp_path, sha256(root.read_bytes()).hexdigest()) as (
        _,
        read,
        _,
    ):
        assert read("field.bin", claimed=body) == b"signed field"
        with pytest.raises(RuntimeError, match="owning context"):
            copy_context().run(read, "field.bin")
        with (
            ThreadPoolExecutor(max_workers=1) as pool,
            pytest.raises(RuntimeError, match="active owner"),
        ):
            pool.submit(read, "field.bin").result()
        assert read("field.bin") == b"signed field"
    with pytest.raises(RuntimeError, match="active owner"):
        read("field.bin")
