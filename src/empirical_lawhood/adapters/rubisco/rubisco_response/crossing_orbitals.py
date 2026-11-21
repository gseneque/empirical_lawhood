# SPDX-License-Identifier: MPL-2.0
"""Evaluate AO overlaps on actual saved oxygen-path geometries without an SCF calculation."""

from io import BytesIO
import os

import numpy as np

from empirical_lawhood.methods.electronic_structure.occupied_space import (
    compare_occupied_spaces,
    occupied_density_factors,
)
from empirical_lawhood.methods.electronic_structure.populations import (
    spin_density_populations,
)


def require_orbital_runtime(threads):
    from importlib.metadata import version
    from pyscf import lib
    from threadpoolctl import threadpool_info

    if (
        type(threads) is not int
        or threads < 1
        or (hasattr(os, "sched_getaffinity") and len(os.sched_getaffinity(0)) < threads)
    ):
        raise ValueError(
            "the original orbital calculation requires its declared CPU capacity"
        )
    pools = threadpool_info()
    adjustable_blas = [
        p
        for p in pools
        if p["user_api"] == "blas" and p.get("threading_layer") != "disabled"
    ]
    if lib.num_threads() != threads or any(
        p["num_threads"] != threads for p in adjustable_blas
    ):
        raise ValueError(
            "configure PySCF and BLAS to use the original orbital calculation's thread count"
        )
    return dict(
        pyscf=version("pyscf"),
        numpy=version("numpy"),
        scipy=version("scipy"),
        threads=threads,
        blas=[
            (
                p["internal_api"],
                p["version"],
                p.get("threading_layer"),
                p["num_threads"],
            )
            for p in pools
            if p["user_api"] == "blas"
        ],
    )


def compare_crossing_path(card, points, bracket):
    """Consume the caller's authenticated point returns in path order, retaining missing spin comparisons."""
    from pyscf import gto

    previous = None
    inputs, same, adjacent, populations = [], [], [], []
    for report, payload in points:
        with np.load(BytesIO(payload), allow_pickle=False) as stored:
            xyz = stored["xyz_A"]
            if (
                xyz.shape != (len(card["elements"]), 3)
                or xyz.dtype.kind not in "if"
                or not np.isfinite(xyz).all()
            ):
                raise ValueError(
                    "native crossing coordinates must retain their complete original atom order"
                )
            molecule = gto.M(
                atom=list(zip(card["elements"], xyz, strict=True)),
                charge=card["charge"],
                spin=2,
                basis="def2-svp",
                unit="Angstrom",
                verbose=0,
            )
            metric = molecule.intor_symmetric("int1e_ovlp")
            slices = molecule.aoslice_by_atom()
            atoms = np.repeat(np.arange(molecule.natm), slices[:, 3] - slices[:, 2])
            states = {}
            properties = {
                label: None for label in ("triplet", "frontier", "opposite_local_spins")
            }
            statuses = dict.fromkeys(properties, "not entered")
            for label, state in report["states"].items():
                if (
                    label not in ("triplet", "frontier", "opposite_local_spins")
                    or type(state["converged"]) is not bool
                ):
                    raise ValueError(
                        "unknown electronic state or convergence status in original crossing"
                    )
                if state["converged"]:
                    statuses[label] = "converged"
                    spin = 2 if label == "triplet" else 0
                    counts = (
                        (molecule.nelectron + spin) // 2,
                        (molecule.nelectron - spin) // 2,
                    )
                    density = stored[label + "_density"]
                    alpha, beta = occupied_density_factors(density, metric, counts)
                    states[label] = alpha, beta
                    projection = spin_density_populations(
                        density,
                        metric,
                        atoms,
                        molecule.atom_charges(),
                        card["gas_indices"],
                    )
                    sz = spin / 2
                    properties[label] = dict(
                        gas_charge_e=projection["selected_charge_e"],
                        gas_spin_e=projection["selected_spin_e"],
                        S2=float(
                            sz * (sz + 1)
                            + counts[1]
                            - np.square(np.abs(alpha.T.conj() @ metric @ beta)).sum()
                        ),
                    )
                else:
                    statuses[label] = "unconverged"
        low, fraction = report["selected_Ms0_guess"], report["fraction"]
        if low is not None and (
            low not in ("frontier", "opposite_local_spins") or low not in states
        ):
            raise ValueError("selected original low-spin state is unavailable")
        states["lower_Ms0"] = states.get(low)
        inputs.append(
            dict(
                fraction=fraction,
                native_sha256=report["native_sha256"],
                selected_Ms0=low,
            )
        )
        populations.append(
            dict(fraction=fraction, states=properties, statuses=statuses)
        )
        same.append(
            dict(
                fraction=fraction,
                **compare_occupied_spaces(
                    states.get("frontier"),
                    states.get("opposite_local_spins"),
                    metric,
                    allow_spin_swap=True,
                ),
            )
        )
        if previous is not None:
            previous_fraction, previous_molecule, previous_states = previous
            cross = gto.intor_cross("int1e_ovlp", previous_molecule, molecule)
            comparisons = {
                key: compare_occupied_spaces(
                    previous_states.get(key),
                    states.get(key),
                    cross,
                    allow_spin_swap=key != "triplet",
                )
                for key in ("triplet", "lower_Ms0", "frontier", "opposite_local_spins")
            }
            adjacent.append(
                dict(fractions=[previous_fraction, fraction], comparisons=comparisons)
            )
        previous = fraction, molecule, states
    return dict(
        original_completed=True,
        points=inputs,
        original_bracket=bracket,
        two_starts_same_geometry=same,
        adjacent_occupied_spaces=adjacent,
        gas_populations=populations,
    )
