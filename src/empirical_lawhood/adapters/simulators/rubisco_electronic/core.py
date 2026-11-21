"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from hashlib import sha256
from math import isfinite

from empirical_lawhood.domains.rubisco.electronic.frontier_diagnostics import (
    ElectronicAtomV1 as _science_ElectronicAtomV1,
    ReducedGeometryV1 as _science_ReducedGeometryV1,
)

def decode_reduced_xyz(raw: bytes) -> _science_ReducedGeometryV1:
    """Retain original digest/title/coordinate strings; refuse extra atom rows."""
    if type(raw) is not bytes or not 1 <= len(raw) <= 8192:
        raise ValueError("XYZ requires bounded original bytes")
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("XYZ requires ASCII native tokens") from exc
    if len(lines) != 16 or lines[0].strip() != "14":
        raise ValueError("XYZ requires the complete fourteen-atom denominator")
    atoms = []
    for line in lines[2:]:
        fields = line.split()
        if len(fields) != 4:
            raise ValueError("XYZ row requires element and three coordinate tokens")
        atoms.append(_science_ElectronicAtomV1(fields[0], tuple(fields[1:])))
    return _science_ReducedGeometryV1(tuple(atoms), sha256(raw).hexdigest(), len(raw), lines[1])


def functional_description(parsed) -> dict:
    """Retain libxc's resolved coefficients with builtin JSON scalar types."""
    hybrid, components = parsed
    return {"hybrid_tuple": [float(value) for value in hybrid],
            "components": [{"id": int(identifier), "coefficient": float(coefficient)}
                           for identifier, coefficient in components]}


def run_native_job(geometry: _science_ReducedGeometryV1, functional: str, basis: str,
                   charge: int, spin: int, output_stream) -> dict:
    """One selected fixed-geometry SCF; no retry, optimization or I/O custody.

    The caller owns pre-import threads, wall/CPU/RSS/output ceilings, sources,
    logs and complete roster. All numerical operands are returned to that
    caller. Checkpoint content is disabled; PySCF may create an empty temporary
    checkpoint during construction, in the caller's selected scratch directory.
    """
    if type(geometry) is not _science_ReducedGeometryV1:
        raise ValueError("native job requires a typed reduced geometry")
    geometry.__post_init__()
    if ((functional, basis) not in (("B3LYPG", "6-31g*"), ("WB97X", "def2-svp"))
            or type(charge) is not int or type(spin) is not int
            or (charge, spin) not in ((-1, 0), (0, 1))):
        raise ValueError("native job changes the frozen electronic realization")
    import numpy as np
    from pyscf import dft, gto, lib
    from pyscf.dft import libxc

    lib.num_threads(2)
    mol = gto.Mole()
    mol.atom = [(a.element, tuple(float(x) for x in a.coordinate_tokens)) for a in geometry.atoms]
    mol.unit, mol.basis, mol.charge, mol.spin = "Angstrom", basis, charge, spin
    mol.cart, mol.verbose, mol.max_memory, mol.stdout = False, 4, 1024, output_stream
    mol.build()
    if mol.nelectron != 55 - charge or mol.nelec != ((28, 28) if charge == -1 else (28, 27)):
        raise ArithmeticError("realized electronic census differs from declared hypotheses")
    expected_ao = 112 if functional == "B3LYPG" else 133
    if mol.nao_nr() != expected_ao:
        raise ArithmeticError("realized basis census differs from frozen protocol")
    mf = dft.RKS(mol) if spin == 0 else dft.UKS(mol)
    mf.xc, mf.grids.level, mf.conv_tol, mf.max_cycle = functional, 4, 1e-10, 120
    mf.init_guess, mf.chkfile = "minao", None
    energy = float(mf.kernel())
    result = {"status": "converged" if mf.converged else "scf_nonconverged",
              "source_sha256": geometry.source_sha256, "geometry_identity": geometry.fingerprint(),
              "charge": charge, "spin": spin, "electron_count": mol.nelectron,
              "alpha_beta_electrons": list(mol.nelec), "nao": mol.nao_nr(),
              "functional": functional, "libxc_parsed_functional": functional_description(libxc.parse_xc(functional)),
              "basis": basis, "spherical_basis": True, "grid_level": mf.grids.level,
              "grid_point_count": len(mf.grids.coords), "convergence_tolerance_hartree": mf.conv_tol,
              "maximum_cycles": mf.max_cycle, "cycles": mf.cycles, "initial_guess": mf.init_guess,
              "direct_scf": mf.direct_scf, "density_fitting": False,
              "last_energy_hartree": energy if isfinite(energy) else None,
              "scf_summary": mf.scf_summary, "native_threads": lib.num_threads(),
              "checkpoint_written": False,
              "numerical_defaults": {"conv_tol_grad": mf.conv_tol_grad, "damping": mf.damp,
                                     "level_shift": mf.level_shift, "diis_start_cycle": mf.diis_start_cycle,
                                     "grid_prune": str(mf.grids.prune), "grid_radi_method": str(mf.grids.radi_method)}}
    if not mf.converged:
        return result
    if not isfinite(energy):
        raise ArithmeticError("converged energy is nonfinite")
    result["energy_hartree"] = energy
    overlap = mol.intor_symmetric("int1e_ovlp")
    labels = mol.ao_labels(fmt=False)
    result["ao_atom_indices"] = [int(label[0]) for label in labels]
    result["ao_labels"] = [list(label) for label in labels]
    result["overlap"] = overlap.tolist()
    result["mo_energy_hartree"] = np.asarray(mf.mo_energy).tolist()
    result["mo_occupation"] = np.asarray(mf.mo_occ).tolist()
    result["mo_coefficient"] = np.asarray(mf.mo_coeff).tolist()
    result["density_matrix"] = np.asarray(mf.make_rdm1()).tolist()
    from empirical_lawhood.domains.rubisco.electronic.frontier_diagnostics import frontier_orbital_diagnostics
    result.update(frontier_orbital_diagnostics(spin=spin, occupations=mf.mo_occ,
        coefficients=mf.mo_coeff, energies=mf.mo_energy, overlap=overlap,
        ao_atom_indices=result["ao_atom_indices"], spin_square=None if spin == 0 else mf.spin_square()))
    return result
