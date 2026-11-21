"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from math import isfinite
import re
from typing import ClassVar
from empirical_lawhood.science.records.serialization import CanonicalRecord


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


def frontier_orbital_diagnostics(*, spin, occupations, coefficients, energies,
                                overlap, ao_atom_indices, spin_square=None):
    """Reduce supplied converged orbital arrays without contacting an electronic solver."""
    import numpy as np
    result = {}
    if spin == 0:
        occupied = np.flatnonzero(occupations > 0)
        homo = int(occupied[-1])
        coefficient = coefficients[:, homo]
        result["homo_index_zero_based"] = homo
        result["homo_coefficient"] = coefficient.tolist()
        result["one_electron_homo_density_matrix"] = np.outer(coefficient, coefficient).tolist()
        result["homo_energy_hartree"] = float(energies[homo])
        result["adjacent_occupied_gap_hartree"] = float(energies[homo] - energies[homo - 1])
        result["populations"] = homo_populations(overlap, coefficient, ao_atom_indices, 14)
        result["s_squared"] = 0.0
        result["spin_diagnostic_role"] = "RESTRICTED_CLOSED_SHELL_ASSUMPTION"
    else:
        result["s_squared"], result["spin_multiplicity"] = map(float, spin_square)
        result["s_squared_minus_doublet_reference"] = result["s_squared"] - 0.75
    return result
