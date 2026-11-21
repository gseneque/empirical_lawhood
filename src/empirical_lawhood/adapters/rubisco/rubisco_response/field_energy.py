# SPDX-License-Identifier: MPL-2.0
"""Reconstruct the signed external-field change at a fixed observed Rubisco cluster."""

from io import BytesIO

import numpy as np

from empirical_lawhood.methods.electronic_structure.field_energy import (
    field_energy_bounds,
)


def observed_field_shift(card, field, density):
    from pyscf import gto, qmmm, scf

    xyz = np.asarray(card["xyz_A"])
    if xyz.shape != (len(card["elements"]), 3) or not np.isfinite(xyz).all():
        raise ValueError(
            "select the complete ordered molecular coordinates in angstrom"
        )
    with np.load(BytesIO(field), allow_pickle=False) as data:
        charges = data["delta_charge_e"]
        positions = data["delta_xyz_A"]
    if (
        charges.ndim != 1
        or not len(charges)
        or positions.shape != (len(charges), 3)
        or not np.isfinite(charges).all()
        or not np.isfinite(positions).all()
    ):
        raise ValueError(
            "select every signed embedding charge and its position in angstrom"
        )
    mol = gto.M(
        atom=list(zip(card["elements"], xyz, strict=True)),
        unit="Angstrom",
        basis="def2-svp",
        charge=card["charge"],
        spin=2 if card["state"].startswith("O-") else 0,
        verbose=0,
    )
    with_field = qmmm.mm_charge(scf.RHF(mol), positions, charges, unit="Angstrom")
    h = with_field.get_hcore() - scf.hf.get_hcore(mol)
    nuclear = float(with_field.energy_nuc() - mol.energy_nuc())
    dm = None
    if density is not None:
        with np.load(BytesIO(density), allow_pickle=False) as data:
            dm = data["density"]
    work = field_energy_bounds(
        h, mol.intor_symmetric("int1e_ovlp"), nuclear, mol.nelec, density=dm
    )
    return {
        "spin_electron_counts": mol.nelec,
        "nuclear_shift_Eh": nuclear,
        "min_AO_eigenvalue_Eh": work.lowest_orbital_shift,
        "max_AO_eigenvalue_Eh": work.highest_orbital_shift,
        "density_independent_interval_Eh": (work.lower, work.upper),
        "frozen_density_shift_Eh": work.frozen,
        "variational_interval_Eh": (
            work.lower,
            work.frozen if work.frozen is not None else work.upper,
        ),
    }
