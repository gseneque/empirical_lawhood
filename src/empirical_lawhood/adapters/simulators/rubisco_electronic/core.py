# SPDX-License-Identifier: MPL-2.0
"""Reduced-enolate decoding and explicitly selected frontier-orbital diagnostics.

The four authentic source geometries and frozen eight-job roster are admitted
by the caller. These computations supply neither native Hirshfeld-I Fukui
values nor an enzyme-edit response. Optional numerical/native dependencies
are imported only during the explicitly selected calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from math import isfinite
import re
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord

_COORDINATE = re.compile(r"[-+]?\d{1,5}\.\d{1,16}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
CASE_IDS = ("B2", "B3", "W2", "W3")
SITE_INDICES = {"C2": 1, "O2": 4, "C3": 2, "O3": 5}


@dataclass(frozen=True, slots=True)
class ElectronicAtomV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/electronic/atom"
    element: str
    coordinate_tokens: tuple[str, str, str]

    def __post_init__(self) -> None:
        if self.element not in ("C", "H", "O"):
            raise ValueError("reduced enolate supports only C/H/O elements")
        if type(self.coordinate_tokens) is not tuple or len(self.coordinate_tokens) != 3:
            raise ValueError("coordinates require three native decimal tokens")
        for token in self.coordinate_tokens:
            if (type(token) is not str or _COORDINATE.fullmatch(token) is None
                    or Decimal(token).copy_abs() > 10000):
                raise ValueError("coordinates require bounded finite fixed-point tokens")


@dataclass(frozen=True, slots=True)
class ReducedGeometryV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/electronic/reduced-geometry"
    atoms: tuple[ElectronicAtomV1, ...]
    source_sha256: str
    source_bytes: int
    native_title: str

    def __post_init__(self) -> None:
        if (type(self.atoms) is not tuple or len(self.atoms) != 14
                or any(type(a) is not ElectronicAtomV1 for a in self.atoms)):
            raise ValueError("reduced geometry requires fourteen typed atoms")
        if tuple(a.element for a in self.atoms) != ("C",) * 4 + ("O",) * 3 + ("H",) * 7:
            raise ValueError("reduced geometry requires native C4/O3/H7 order")
        if type(self.source_sha256) is not str or _DIGEST.fullmatch(self.source_sha256) is None:
            raise ValueError("source requires an exact SHA256")
        if type(self.source_bytes) is not int or not 1 <= self.source_bytes <= 8192:
            raise ValueError("source exceeds reduced XYZ byte contract")
        if (type(self.native_title) is not str or len(self.native_title) > 200
                or any(ord(c) < 32 or ord(c) > 126 for c in self.native_title)):
            raise ValueError("XYZ title requires a bounded printable native line")
        for atom in self.atoms:
            atom.__post_init__()


def decode_reduced_xyz(raw: bytes) -> ReducedGeometryV1:
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
        atoms.append(ElectronicAtomV1(fields[0], tuple(fields[1:])))
    return ReducedGeometryV1(tuple(atoms), sha256(raw).hexdigest(), len(raw), lines[1])


def homo_populations(overlap, coefficient, ao_atom_indices, natoms: int) -> dict:
    """One-electron symmetric Lowdin and Mulliken HOMO populations.

    Every AO belongs to exactly one supplied atom, and every atom must have an
    AO. A near-singular or nonpositive overlap is refused, without clipping.
    Negative Mulliken contributions are valid retained diagnostic values.
    """
    import numpy as np

    s, c = np.asarray(overlap, dtype=float), np.asarray(coefficient, dtype=float)
    if (type(natoms) is not int or not 1 <= natoms <= 256 or s.ndim != 2
            or s.shape[0] != s.shape[1] or not 1 <= s.shape[0] <= 2048
            or c.shape != (s.shape[0],) or not np.isfinite(s).all()
            or not np.isfinite(c).all()):
        raise ValueError("HOMO requires finite bounded square overlap and matching vector")
    if not np.allclose(s, s.T, rtol=0, atol=1e-12):
        raise ValueError("overlap must be symmetric")
    census = tuple(ao_atom_indices)
    if (len(census) != len(c) or any(type(i) is not int or not 0 <= i < natoms for i in census)
            or set(census) != set(range(natoms))):
        raise ValueError("AO census must cover every atom exactly once per AO")
    eigenvalues, eigenvectors = np.linalg.eigh(s)
    if eigenvalues[0] <= max(1e-12, eigenvalues[-1] * 1e-12):
        raise ValueError("nonpositive or numerically singular overlap")
    norm = float(c @ s @ c)
    if not isfinite(norm) or abs(norm - 1) > 1e-8:
        raise ValueError("HOMO must have normalized one-electron metric norm")
    root_c = eigenvectors @ (np.sqrt(eigenvalues) * (eigenvectors.T @ c))
    lowdin_ao = root_c**2
    mulliken_ao = c * (s @ c)
    lowdin = np.bincount(census, weights=lowdin_ao, minlength=natoms)
    mulliken = np.bincount(census, weights=mulliken_ao, minlength=natoms)
    if (not np.isfinite(lowdin).all() or not np.isfinite(mulliken).all()
            or abs(float(lowdin.sum()) - 1) > 1e-8
            or abs(float(mulliken.sum()) - 1) > 1e-8):
        raise ArithmeticError("HOMO populations do not preserve one-electron density")
    return {"overlap_eigenvalues": eigenvalues.tolist(), "one_electron_metric_norm": norm,
            "lowdin_by_atom": lowdin.tolist(), "mulliken_by_atom": mulliken.tolist()}


def assess_carbon_ordering(results: dict) -> dict:
    """Evaluate the frozen four-anion denominator, including failed cases."""
    if type(results) is not dict or set(results) != set(CASE_IDS):
        raise ValueError("assessment requires exactly the four assigned anion cases")
    orders, changes = {}, {}
    for partition in ("lowdin", "mulliken"):
        vectors, observed = {}, {}
        for case in CASE_IDS:
            result = results[case]
            if result.get("status") != "converged":
                observed[case] = {"evaluable": False, "criterion_pass": False}
                continue
            values = result["populations"][partition + "_by_atom"]
            if (len(values) != 14 or any(type(v) not in (int, float) or not isfinite(v) for v in values)
                    or abs(sum(values) - 1) > 1e-8
                    or (partition == "lowdin" and any(v < 0 for v in values))):
                raise ValueError("assessment requires complete finite normalized atom populations")
            vectors[case] = values
            c2, c3 = values[1], values[2]
            passed = c3 > c2 if case.endswith("2") else c2 > c3
            observed[case] = {"evaluable": True, "C2": c2, "C3": c3,
                              "C2_minus_C3": c2 - c3, "criterion_pass": passed}
        orders[partition] = observed
        changes[partition] = {}
        for family in ("B", "W"):
            rows = {}
            for site, index in SITE_INDICES.items():
                if family + "2" not in vectors or family + "3" not in vectors:
                    rows[site] = {"evaluable": False, "direction_pass": False}
                else:
                    delta = vectors[family + "3"][index] - vectors[family + "2"][index]
                    rows[site] = {"evaluable": True, "enolate3_minus2": delta,
                                  "direction_pass": delta > 0 if site in ("C2", "O3") else delta < 0}
            changes[partition][family] = rows
    primary = orders["lowdin"]
    return {"assigned_anion_cases": list(CASE_IDS), "assigned_anion_denominator": 4,
            "evaluable_anion_count": sum(v["evaluable"] for v in primary.values()),
            "primary_entry_pass": all(v["criterion_pass"] for v in primary.values()),
            "primary_family_pass": {f: all(primary[f + n]["criterion_pass"] for n in ("2", "3"))
                                    for f in ("B", "W")},
            "carbon_ordering": orders, "site_changes": changes,
            "scientific_role": "EXPOSED_REDUCED_SUBSTRATE_DIAGNOSTIC_NOT_MUTANT_KINETICS"}


def functional_description(parsed) -> dict:
    """Retain libxc's resolved coefficients with builtin JSON scalar types."""
    hybrid, components = parsed
    return {"hybrid_tuple": [float(value) for value in hybrid],
            "components": [{"id": int(identifier), "coefficient": float(coefficient)}
                           for identifier, coefficient in components]}


def run_native_job(geometry: ReducedGeometryV1, functional: str, basis: str,
                   charge: int, spin: int, output_stream) -> dict:
    """One selected fixed-geometry SCF; no retry, optimization or I/O custody.

    The caller owns pre-import threads, wall/CPU/RSS/output ceilings, sources,
    logs and complete roster. All numerical operands are returned to that
    caller. Checkpoint content is disabled; PySCF may create an empty temporary
    checkpoint during construction, in the caller's selected scratch directory.
    """
    if type(geometry) is not ReducedGeometryV1:
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
    if spin == 0:
        occupied = np.flatnonzero(mf.mo_occ > 0)
        homo = int(occupied[-1])
        coefficient = mf.mo_coeff[:, homo]
        result["homo_index_zero_based"] = homo
        result["homo_coefficient"] = coefficient.tolist()
        result["one_electron_homo_density_matrix"] = np.outer(coefficient, coefficient).tolist()
        result["homo_energy_hartree"] = float(mf.mo_energy[homo])
        result["adjacent_occupied_gap_hartree"] = float(mf.mo_energy[homo] - mf.mo_energy[homo - 1])
        result["populations"] = homo_populations(overlap, coefficient, result["ao_atom_indices"], 14)
        result["s_squared"] = 0.0
        result["spin_diagnostic_role"] = "RESTRICTED_CLOSED_SHELL_ASSUMPTION"
    else:
        result["s_squared"], result["spin_multiplicity"] = map(float, mf.spin_square())
        result["s_squared_minus_doublet_reference"] = result["s_squared"] - 0.75
    return result
