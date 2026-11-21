# SPDX-License-Identifier: MPL-2.0
"""Prospective reference-only ASH/Amber coupling; no native import on discovery.

The frozen caller owns source admission, allocation and execution authority.
These ordinary private helpers do not create any such authority. Native
construction is explicitly effectful and is deferred to the selected launcher.
No optimizer, reactive force-field parameter or Lennard-Jones engine is added.
"""

from __future__ import annotations

from copy import copy
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import math
import os
from pathlib import Path
import re
from types import MethodType
from typing import Any, Callable, Mapping


SOURCE_BYTES = 22365456
SOURCE_SHA256 = "87b5ed6e40ea77afde056312f923fca44f8b6ee164d8dd973e6deb3b79b2b902"
DRY_ATOMS = 13828
FULL_ATOMS = 116767
SOURCE_LJ_TYPES = 25
ASH_BOHR_ANGSTROM = 0.5291772109303
LINK_DISTANCE_ANGSTROM = 1.09
LINK_WITNESS_TOLERANCE_ANGSTROM = 1e-10
BACKBONE_NAMES = frozenset(("N", "H", "CA", "HA", "C", "O"))
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_SOURCE_PINS = (
    (
        "ash/modules/module_QMMM.py",
        "511d8d7aa23e7e750250a7bb9ef049a333d8157dddf14a7facf0682a4129c42e",
    ),
    (
        "ash/interfaces/interface_OpenMM.py",
        "55756fbc89974837e2eda7d6702e1606ff3017e8a8ca0156c55d0345a5044a04",
    ),
    (
        "ash/interfaces/interface_geometric_new.py",
        "f112beadd6461235e510f42856300c451cd2e8e73c229ba5cac6afcffded8381",
    ),
)


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label}: bool is not a numeric operand")
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{label}: invalid scalar") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label}: nonfinite scalar")
    return result


def _index(value: Any, count: int, label: str) -> int:
    if type(value) is not int or not 0 <= value < count:
        raise ValueError(f"{label}: index outside complete physical roster")
    return value


def _digest(value: Any, label: str) -> str:
    if type(value) is not str or _SHA.fullmatch(value) is None:
        raise ValueError(f"{label}: digest missing or invalid")
    return value


def _fraction(value: Any, label: str) -> Fraction:
    if (
        type(value) not in (tuple, list)
        or len(value) != 2
        or any(type(v) is not int for v in value)
        or value[1] <= 0
    ):
        raise ValueError(f"{label}: exact rational pair required")
    result = Fraction(value[0], value[1])
    if abs(result) > 10:
        raise ValueError(f"{label}: charge/scaling operand outside selected bound")
    return result


def _quantity(value: Any, unit: Any = None) -> float:
    if unit is not None and hasattr(value, "value_in_unit"):
        value = value.value_in_unit(unit)
    return _finite(value, "native force parameter")


@dataclass(frozen=True)
class NativeLibraries:
    """Injected live libraries, never a canonical scientific/source record."""

    ash: Any
    openmm: Any
    app: Any
    unit: Any
    parmed: Any
    numpy: Any


@dataclass
class CouplingSession:
    """Selected native objects plus an ordinary inspectable construction audit."""

    theory: Any
    fragment: Any
    active_atom_indices: tuple[int, ...]
    fixed_physical_atom_indices: tuple[int, ...]
    audit: dict[str, Any]
    scratch_directory: Path

    @property
    def fixed_atom_indices(self) -> tuple[int, ...]:
        return self.fixed_physical_atom_indices

    @property
    def masking_audit(self) -> dict[str, Any]:
        return self.audit


@dataclass
class NativeReferencePreparation:
    """Ordinary native preparation result; no Context or scientific authority."""

    source: Any
    dry: Any
    reloaded: Any
    prmtop_path: Path
    scratch_directory: Path
    selected: dict[str, Any]
    audit: dict[str, Any]


def load_bound_native_libraries(
    *, protocol_sha256: str, site_packages: str | Path
) -> NativeLibraries:
    """Explicit native-import boundary, called only by the frozen launcher.

    A syntactically valid digest is a binding operand, not authorization.
    The caller must authenticate the protocol/profile and all software sources.
    """
    _digest(protocol_sha256, "selected frozen protocol")
    if not Path(site_packages).is_absolute():
        raise ValueError("absolute selected native site-packages required")
    root = Path(site_packages).resolve(strict=True)
    for relative, expected in _SOURCE_PINS:
        member = root / relative
        if member.is_symlink() or sha256(member.read_bytes()).hexdigest() != expected:
            raise ValueError("pinned ASH coupling source differs")
    if (Path.home() / "ash_user_settings.ini").exists():
        raise ValueError("unselected ASH user configuration is present")
    plugin_dir = os.environ.get("OPENMM_PLUGIN_DIR")
    if (
        plugin_dir is None
        or not Path(plugin_dir).is_absolute()
        or not Path(plugin_dir).is_dir()
        or any(Path(plugin_dir).iterdir())
    ):
        raise ValueError("explicit selected empty OPENMM_PLUGIN_DIR required")
    # These imports are deliberately confined to the explicit native boundary.
    import ash
    import numpy
    import openmm
    from openmm import app, unit
    import parmed

    if Path(ash.__file__).resolve().parent != root / "ash":
        raise ValueError("realized ASH package differs from selected profile")
    if ash.constants.bohr2ang != ASH_BOHR_ANGSTROM:
        raise ValueError("pinned ASH Cartesian derivative units differ")
    return NativeLibraries(ash, openmm, app, unit, parmed, numpy)


# This additive reference-specific migration retains the authenticated scientific
# operators from the historical helper. It creates neither execution authority
# nor a Gp mutation-to-kinetics bridge. Exact old bytes remain at their locator.
MIGRATION_SOURCE_SHA256 = "0cbef06a873c745279d6525f6a697ae91b8adaa73bb8d8b5e7e0f256465e3765"


def _selected_libraries(native_libraries, site_packages, protocol_sha256):
    _digest(protocol_sha256, "selected frozen protocol")
    if native_libraries is not None:
        if site_packages is not None:
            raise ValueError("select injected libraries or a native profile, not both")
        return native_libraries
    if site_packages is None:
        raise ValueError("explicit selected native site-packages required")
    return load_bound_native_libraries(
        protocol_sha256=protocol_sha256, site_packages=site_packages
    )


def _selected_scratch(path: str | Path, protocol_sha256: str) -> Path:
    _digest(protocol_sha256, "selected frozen protocol")
    result = Path(path)
    if not result.is_absolute() or result.exists() or result.is_symlink():
        raise ValueError("new absolute selected scratch directory required")
    result.parent.resolve(strict=True)
    result.mkdir(mode=0o700)
    return result


def correct_coulomb_exceptions(
    system: Any,
    qm_indices: tuple[int, ...],
    charges: tuple[float, ...],
    scee_by_pair: Mapping[tuple[int, int], Fraction],
    *,
    unit: Any = None,
) -> dict[str, Any]:
    """Correct independently stored exception products; preserve all LJ fields.

    Proper 1-4 pairs must come from the parameterized source/donor topology,
    including its ignore-end/improper policy. Excluded pairs remain zero.
    No original nonzero exception may silently lose its scaling witness.
    """
    count = system.getNumParticles()
    if len(charges) != count or len(set(qm_indices)) != len(qm_indices):
        raise ValueError("charge or QM denominator differs")
    qset = {_index(i, count, "QM") for i in qm_indices}
    values = tuple(_finite(q, "selected charge") for q in charges)
    if any(values[i] != 0.0 for i in qset):
        raise ValueError("classical QM particle charges must be zero")
    scales = {}
    for pair, scale in scee_by_pair.items():
        if (
            type(pair) is not tuple
            or len(pair) != 2
            or pair != tuple(sorted(pair))
            or pair[0] == pair[1]
        ):
            raise ValueError("noncanonical 1-4 pair")
        _index(pair[0], count, "1-4")
        _index(pair[1], count, "1-4")
        if not isinstance(scale, Fraction) or not 0 < scale <= 10:
            raise ValueError("positive exact source SCEE required")
        scales[pair] = scale
    charge_unit = unit.elementary_charge**2 if unit is not None else None
    forces = [f for f in system.getForces() if type(f).__name__ == "NonbondedForce"]
    if len(forces) != 1:
        raise ValueError("exactly one classical NonbondedForce required")
    force = forces[0]
    seen = set()
    corrected = []
    excluded = 0
    qm_zeroed = 0
    for ordinal in range(force.getNumExceptions()):
        a, b, old_product, sigma, epsilon = force.getExceptionParameters(ordinal)
        pair = tuple(sorted((int(a), int(b))))
        if pair in seen:
            raise ValueError("duplicate native exception pair")
        seen.add(pair)
        old = _quantity(old_product, charge_unit)
        if pair[0] in qset or pair[1] in qset:
            new = 0.0
            qm_zeroed += 1
        elif pair in scales:
            new = values[pair[0]] * values[pair[1]] / float(scales[pair])
        else:
            if old != 0.0:
                raise ValueError("nonzero exception has no source SCEE witness")
            new = 0.0
            excluded += 1
        force.setExceptionParameters(ordinal, a, b, new, sigma, epsilon)
        after = force.getExceptionParameters(ordinal)
        if tuple(after[0:2]) != (a, b) or after[3] != sigma or after[4] != epsilon:
            raise ValueError("exception correction altered native LJ or indices")
        if _quantity(after[2], charge_unit) != new:
            raise ValueError("exception Coulomb product was not updated")
        if old != new:
            corrected.append((ordinal, pair, old, new))
    # A source active 1-4 pair must have a native exception even if q_i*q_j=0.
    if set(scales) - seen:
        raise ValueError("source active 1-4 pair missing from native exceptions")
    return {
        "exception_count": len(seen),
        "qm_containing_zeroed_count": qm_zeroed,
        "excluded_non14_mm_count": excluded,
        "changed_products": tuple(corrected),
        "all_exception_lj_preserved": True,
    }


def _term_atoms(term: Any, size: int) -> tuple[Any, ...]:
    return tuple(getattr(term, f"atom{i}") for i in range(1, size + 1))


def _type_witness(value: Any, kind: str) -> tuple[Any, ...]:
    names = {
        "bonds": ("k", "req"),
        "angles": ("k", "theteq"),
        "dihedrals": ("phi_k", "per", "phase", "scee", "scnb"),
    }[kind]
    if value is None or isinstance(value, (tuple, list)):
        raise ValueError("missing or unsplit source bonded parameter")
    return tuple(
        _finite(getattr(value, name), "source bonded parameter") for name in names
    )


def _term_key(term: Any, size: int) -> tuple[Any, ...]:
    indices = tuple(a.idx for a in _term_atoms(term, size))
    return indices + ((bool(term.improper), bool(term.ignore_end)) if size == 4 else ())


def splice_spectator_hid(
    source: Any, dry: Any, donor_to_target: Mapping[int, int], *, parmed: Any
) -> dict[str, Any]:
    """Transplant complete parameterized HID side-chain and boundary terms.

    Indices are native zero-based. The complete 17-row same-chain donor map is
    explicit. Peptide-neighbor joins are derived solely from source topology
    residue adjacency/name/type, retained in the audit and refused if ambiguous.
    This source-only native preparation never evaluates an energy or force.
    """
    if len(donor_to_target) != 17 or len(set(donor_to_target.values())) != 17:
        raise ValueError("complete bijective seventeen-atom HID donor map required")
    for a, b in donor_to_target.items():
        _index(a, len(source.atoms), "donor")
        _index(b, len(dry.atoms), "spectator")
    donor_residues = {source.atoms[i].residue.idx for i in donor_to_target}
    target_residues = {dry.atoms[i].residue.idx for i in donor_to_target.values()}
    if len(donor_residues) != 1 or len(target_residues) != 1:
        raise ValueError("HID donor/target is not one complete native residue")
    donor_res = source.residues[next(iter(donor_residues))]
    target_res = dry.residues[next(iter(target_residues))]
    if len(donor_res.atoms) != 17 or len(target_res.atoms) != 17:
        raise ValueError("native residue inventory differs from selected HID/HIE")
    expected = frozenset(
        "N H CA HA CB HB2 HB3 CG ND1 HD1 CE1 HE1 NE2 CD2 HD2 C O".split()
    )
    if {a.name for a in donor_res.atoms} != expected or donor_res.name != "HID":
        raise ValueError("source donor is not complete native HID")
    if {a.name for a in target_res.atoms} != (expected - {"HD1"}) | {"HE2"}:
        raise ValueError("source spectator is not complete native HIE")
    side_donor = {
        i for i in donor_to_target if source.atoms[i].name not in BACKBONE_NAMES
    }
    side_target = {donor_to_target[i] for i in side_donor}
    for attr in (
        "urey_bradleys",
        "impropers",
        "rb_torsions",
        "cmaps",
        "trigonal_angles",
        "pi_torsions",
        "out_of_plane_bends",
        "stretch_bends",
        "torsion_torsions",
    ):
        if getattr(source, attr, ()) or getattr(dry, attr, ()):
            raise ValueError(f"unsupported source force class: {attr}")
    joins = dict(donor_to_target)
    outside_joins = []

    def join_atom(atom: Any) -> Any:
        if atom.idx not in joins:
            delta = atom.residue.idx - donor_res.idx
            target_r = target_res.idx + delta
            if delta not in (-1, 1) or not 0 <= target_r < len(dry.residues):
                raise ValueError("donor term crosses an unsupported residue boundary")
            matches = [a for a in dry.residues[target_r].atoms if a.name == atom.name]
            if len(matches) != 1:
                raise ValueError("ambiguous donor peptide-neighbor name join")
            other = matches[0]
            if (
                atom.type != other.type
                or atom.atomic_number != other.atomic_number
                or atom.mass != other.mass
                or atom.name not in BACKBONE_NAMES
            ):
                raise ValueError("donor peptide-neighbor parameter types differ")
            joins[atom.idx] = other.idx
            outside_joins.append((atom.idx, other.idx, atom.name, delta, atom.type))
        return dry.atoms[joins[atom.idx]]

    before_source = {}
    transplanted = {}
    removed = {}
    for kind, size, clsname in (
        ("bonds", 2, "Bond"),
        ("angles", 3, "Angle"),
        ("dihedrals", 4, "Dihedral"),
    ):
        original_terms = getattr(source, kind)
        wanted = [
            t
            for t in original_terms
            if any(a.idx in side_donor for a in _term_atoms(t, size))
        ]
        before_source[kind] = tuple(
            (_term_key(t, size), _type_witness(t.type, kind)) for t in wanted
        )
        destination = getattr(dry, kind)
        old = [
            t
            for t in destination
            if any(a.idx in side_target for a in _term_atoms(t, size))
        ]
        removed[kind] = tuple(
            (_term_key(t, size), _type_witness(t.type, kind)) for t in old
        )
        for term in old:
            term.delete()
            destination.remove(term)
        copied = []
        for original in wanted:
            atoms = tuple(join_atom(a) for a in _term_atoms(original, size))
            parameter = copy(original.type)
            types = getattr(dry, kind[:-1] + "_types")
            types.append(parameter)
            if hasattr(types, "claim"):
                types.claim()
            extra = (
                {"improper": original.improper, "ignore_end": original.ignore_end}
                if size == 4
                else {}
            )
            if size == 2:
                extra = {
                    "order": original.order,
                    "qualitative_type": original.qualitative_type,
                }
            new = getattr(parmed, clsname)(*atoms, type=parameter, **extra)
            destination.append(new)
            if _type_witness(new.type, kind) != _type_witness(original.type, kind):
                raise ValueError("transplanted bonded parameter changed")
            copied.append((_term_key(new, size), _type_witness(new.type, kind)))
        transplanted[kind] = tuple(copied)
    assignments = []
    for donor_i, target_i in sorted(donor_to_target.items()):
        donor, target = source.atoms[donor_i], dry.atoms[target_i]
        expected_name = "HE2" if donor.name == "HD1" else donor.name
        if target.name != expected_name or donor.atomic_number != target.atomic_number:
            raise ValueError("spectator donor physical nucleus/name join differs")
        target.name = donor.name
        for attribute in ("type", "nb_idx", "mass", "atomic_number", "charge"):
            setattr(target, attribute, getattr(donor, attribute))
        target.atom_type = copy(donor.atom_type)
        assignments.append(
            (
                donor_i,
                target_i,
                donor.name,
                donor.type,
                donor.nb_idx,
                _finite(donor.mass, "donor mass"),
                _finite(donor.charge, "donor q"),
            )
        )
    target_res.name = "HID"
    if {a.name for a in target_res.atoms} != expected:
        raise ValueError("complete spectator HID assignment failed")
    # ParmEd owns regeneration of native pointers/exclusions; no new decoder.
    dry.update_dihedral_exclusions()
    dry.remake_parm()
    return {
        "donor_atom_assignments": tuple(assignments),
        "outside_neighbor_joins": tuple(outside_joins),
        "source_terms": before_source,
        "removed_target_terms": removed,
        "transplanted_terms": transplanted,
        "bonded_parameter_splice_complete": True,
        "claim": "source-derived native preparation; not evaluated/qualified chemistry",
    }


def source_scee_by_pair(structure: Any) -> dict[tuple[int, int], Fraction]:
    result = {}
    for d in structure.dihedrals:
        if d.improper or d.ignore_end:
            continue
        scale = Fraction(str(_finite(d.type.scee, "active native SCEE")))
        if not 0 < scale <= 10:
            raise ValueError("active native 1-4 SCEE outside selected bound")
        pair = tuple(sorted((d.atom1.idx, d.atom4.idx)))
        if pair[0] == pair[1] or (pair in result and result[pair] != scale):
            raise ValueError("ambiguous native 1-4 scaling")
        result[pair] = scale
    return result


def source_lj_tables(structure: Any) -> dict[str, tuple[Any, ...]]:
    """Exact native source lookup/coefficient operands, not recombined LJ."""
    data = structure.parm_data
    names = ("NONBONDED_PARM_INDEX", "LENNARD_JONES_ACOEF", "LENNARD_JONES_BCOEF")
    tables = {name: tuple(data[name]) for name in names}
    if not tables[names[0]] or any(type(v) is not int for v in tables[names[0]]):
        raise ValueError("native LJ lookup is missing or noninteger")
    for name in names[1:]:
        if not tables[name] or any(
            _finite(v, "source LJ coefficient") < 0 for v in tables[name]
        ):
            raise ValueError("native LJ coefficients differ from supported source")
    if len(tables[names[1]]) != len(tables[names[2]]):
        raise ValueError("native A/B pair denominator differs")
    return tables


def verify_source_lj_tables(
    expected: Mapping[str, tuple[Any, ...]], structure: Any, *, stage: str
) -> dict[str, Any]:
    found = source_lj_tables(structure)
    if found != expected:
        raise ValueError(f"source native A/B/lookup changed during {stage}")
    return {
        "stage": stage,
        "source_native_lj_tables_exact": True,
        "table_counts": {name: len(values) for name, values in found.items()},
        "table_sha256": {
            name: sha256(repr(values).encode("ascii")).hexdigest()
            for name, values in found.items()
        },
    }


def _native_source_atom_roster(structure: Any, count: int) -> tuple[tuple[Any, ...], ...]:
    """Exact native atom identity/type witness; not source admission authority."""
    if len(structure.atoms) != count:
        raise ValueError("native source/dry atom denominator differs")
    rows = []
    for i, atom in enumerate(structure.atoms):
        if (
            type(atom.idx) is not int
            or atom.idx != i
            or type(atom.nb_idx) is not int
            or not 1 <= atom.nb_idx <= SOURCE_LJ_TYPES
        ):
            raise ValueError("native source/dry atom order or LJ index differs")
        rows.append(
            (
                atom.idx,
                atom.name,
                atom.type,
                atom.nb_idx,
                _finite(atom.mass, "native source mass"),
                _finite(atom.charge, "native source charge"),
                atom.atomic_number,
                atom.residue.idx,
                atom.residue.name,
            )
        )
    native_indices = tuple(structure.parm_data["ATOM_TYPE_INDEX"])
    if any(type(v) is not int for v in native_indices) or native_indices != tuple(
        row[3] for row in rows
    ):
        raise ValueError("native atom LJ indices differ from parameter array")
    return tuple(rows)


def _verify_bound_type_slots(structure: Any, count: int) -> None:
    """Retain all original slots, including types absent from the dry core."""
    pointers = structure.parm_data["POINTERS"]
    if (
        len(pointers) < 2
        or type(pointers[0]) is not int
        or pointers[0] != count
        or type(pointers[1]) is not int
        or pointers[1] != SOURCE_LJ_TYPES
        or type(structure.pointers.get("NATOM")) is not int
        or structure.pointers["NATOM"] != count
        or type(structure.pointers.get("NTYPES")) is not int
        or structure.pointers["NTYPES"] != SOURCE_LJ_TYPES
    ):
        raise ValueError("native source/dry NATOM or complete NTYPES slots differ")
    tables = source_lj_tables(structure)
    expected_pairs = SOURCE_LJ_TYPES * (SOURCE_LJ_TYPES + 1) // 2
    if (
        len(tables["NONBONDED_PARM_INDEX"]) != SOURCE_LJ_TYPES**2
        or any(not 1 <= v <= expected_pairs for v in tables["NONBONDED_PARM_INDEX"])
        or len(tables["LENNARD_JONES_ACOEF"]) != expected_pairs
        or len(tables["LENNARD_JONES_BCOEF"]) != expected_pairs
    ):
        raise ValueError("native source/dry complete LJ table denominator differs")


def _strip_bound_dry_core(
    source_path: Path,
    source: Any,
    *,
    parmed: Any,
    observe_native: Callable[[str, Any], None] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Reload an already authenticated path, then use native ParmEd stripping.

    The caller hash-checks the original path before native loading. Slicing an
    AmberParm rebuilds its lookup with fewer type slots, so do not slice or
    reconstruct LJ tables here. The full source remains pristine for donors.
    """
    _verify_bound_type_slots(source, FULL_ATOMS)
    original_atoms = _native_source_atom_roster(source, FULL_ATOMS)
    original_lj = source_lj_tables(source)
    dry = parmed.load_file(str(source_path))
    if observe_native is not None:
        observe_native("dry-reloaded", dry)
    if dry is source or {id(a) for a in source.atoms} & {id(a) for a in dry.atoms}:
        raise ValueError("dry source reload aliases pristine native source")
    _verify_bound_type_slots(dry, FULL_ATOMS)
    if _native_source_atom_roster(dry, FULL_ATOMS) != original_atoms:
        raise ValueError("dry source reload changed complete native atom roster")
    verify_source_lj_tables(original_lj, dry, stage="dry source reload")
    # remake_parm calls rediscover_molecules; clearing only this dry object's box
    # disables its solvent reordering path before the native strip/remake call.
    dry.box = None
    selection = f"@{DRY_ATOMS + 1}-{FULL_ATOMS}"
    try:
        dry.strip(selection)
    finally:
        if observe_native is not None:
            observe_native("dry-after-strip", dry)
            observe_native("original-after-strip", source)
    _verify_bound_type_slots(dry, DRY_ATOMS)
    if _native_source_atom_roster(dry, DRY_ATOMS) != original_atoms[:DRY_ATOMS]:
        raise ValueError("native dry strip changed retained atom identity/order/types")
    audit = verify_source_lj_tables(original_lj, dry, stage="native dry strip")
    _verify_bound_type_slots(source, FULL_ATOMS)
    if _native_source_atom_roster(source, FULL_ATOMS) != original_atoms:
        raise ValueError("native dry strip altered pristine donor source atoms")
    verify_source_lj_tables(original_lj, source, stage="pristine donor source")
    audit.update(
        {
            "library_operation": "AmberParm.strip",
            "selection": selection,
            "original_atom_count": FULL_ATOMS,
            "retained_atom_count": DRY_ATOMS,
            "complete_original_type_slots": SOURCE_LJ_TYPES,
            "unused_retained_type_slots": tuple(
                sorted(set(range(1, SOURCE_LJ_TYPES + 1)) - {a.nb_idx for a in dry.atoms})
            ),
            "separate_source_reload": True,
            "pristine_donor_source_unchanged": True,
            "table_rebuilding_or_restoration": False,
        }
    )
    return dry, audit


def _bonded_topology_witness(structure: Any) -> dict[str, tuple[Any, ...]]:
    """Complete term multiplicities and native parameters before ASH masking."""
    result = {}
    for kind, size in (("bonds", 2), ("angles", 3), ("dihedrals", 4)):
        rows = []
        for term in getattr(structure, kind):
            indices = tuple(a.idx for a in _term_atoms(term, size))
            canonical = min(indices, indices[::-1])
            flags = (bool(term.improper), bool(term.ignore_end)) if size == 4 else ()
            rows.append((canonical + flags, _type_witness(term.type, kind)))
        result[kind] = tuple(sorted(rows))
    return result


def verify_bonded_roundtrip(
    expected: Mapping[str, tuple[Any, ...]], structure: Any
) -> dict[str, Any]:
    """Admit existing ParmEd serialization precision, preserve every term."""
    found = _bonded_topology_witness(structure)
    errors = {}
    for kind in expected:
        left, right = expected[kind], found[kind]
        if len(left) != len(right) or Counter(r[0] for r in left) != Counter(
            r[0] for r in right
        ):
            raise ValueError(
                f"derived {kind} topology/multiplicity changed on save/reload"
            )
        largest = 0.0
        for (key_a, values_a), (key_b, values_b) in zip(left, right, strict=True):
            if key_a != key_b:
                raise ValueError("native bonded term ordering differs")
            for a, b in zip(values_a, values_b, strict=True):
                relative = abs(a - b) / max(1.0, abs(a), abs(b))
                largest = max(largest, relative)
                # Amber's existing 16.8E parameter writer is the precision
                # boundary. This is a software serialization check, not a
                # retuned scientific geometry/force threshold.
                if relative > 1e-7:
                    raise ValueError(
                        "native bonded parameter changed beyond writer precision"
                    )
        errors[kind] = largest
    return {
        "complete_term_multiplicity_preserved": True,
        "counts": {kind: len(rows) for kind, rows in found.items()},
        "maximum_scaled_parameter_roundtrip_error": errors,
        "software_serialization_tolerance": 1e-7,
    }


def inspect_force_snapshot(system: Any, *, unit: Any = None) -> dict[str, Any]:
    """Inspect live OpenMM force objects without constructing a Context."""
    units = {
        "q": unit.elementary_charge if unit is not None else None,
        "q2": unit.elementary_charge**2 if unit is not None else None,
        "r": unit.nanometer if unit is not None else None,
        "e": unit.kilojoule_per_mole if unit is not None else None,
        "bk": unit.kilojoule_per_mole / unit.nanometer**2 if unit is not None else None,
        "ak": unit.kilojoule_per_mole / unit.radian**2 if unit is not None else None,
        "a": unit.radian if unit is not None else None,
    }
    out: dict[str, Any] = {
        "particles": (),
        "exceptions": (),
        "bonds": (),
        "angles": (),
        "torsions": (),
        "force_roster": (),
    }
    roster = []
    for force in system.getForces():
        name = type(force).__name__
        roster.append(name)
        if name == "NonbondedForce":
            if out["particles"]:
                raise ValueError("multiple NonbondedForce objects")
            out["particles"] = tuple(
                tuple(
                    _quantity(v, units[k])
                    for v, k in zip(
                        force.getParticleParameters(i), ("q", "r", "e"), strict=True
                    )
                )
                for i in range(force.getNumParticles())
            )
            out["exceptions"] = tuple(
                (
                    int(r[0]),
                    int(r[1]),
                    _quantity(r[2], units["q2"]),
                    _quantity(r[3], units["r"]),
                    _quantity(r[4], units["e"]),
                )
                for r in (
                    force.getExceptionParameters(i)
                    for i in range(force.getNumExceptions())
                )
            )
        elif name == "HarmonicBondForce":
            if out["bonds"]:
                raise ValueError("multiple HarmonicBondForce objects")
            out["bonds"] = tuple(
                (
                    int(r[0]),
                    int(r[1]),
                    _quantity(r[2], units["r"]),
                    _quantity(r[3], units["bk"]),
                )
                for r in (
                    force.getBondParameters(i) for i in range(force.getNumBonds())
                )
            )
        elif name == "HarmonicAngleForce":
            if out["angles"]:
                raise ValueError("multiple HarmonicAngleForce objects")
            out["angles"] = tuple(
                (
                    int(r[0]),
                    int(r[1]),
                    int(r[2]),
                    _quantity(r[3], units["a"]),
                    _quantity(r[4], units["ak"]),
                )
                for r in (
                    force.getAngleParameters(i) for i in range(force.getNumAngles())
                )
            )
        elif name == "PeriodicTorsionForce":
            if out["torsions"]:
                raise ValueError("multiple PeriodicTorsionForce objects")
            out["torsions"] = tuple(
                (
                    *(int(v) for v in r[:5]),
                    _quantity(r[5], units["a"]),
                    _quantity(r[6], units["e"]),
                )
                for r in (
                    force.getTorsionParameters(i) for i in range(force.getNumTorsions())
                )
            )
        elif name != "CMMotionRemover":
            raise ValueError(f"unselected native force class: {name}")
    if roster.count("NonbondedForce") != 1 or any(roster.count(n) > 1 for n in roster):
        raise ValueError("unexpected native force roster")
    out["force_roster"] = tuple(roster)
    return out


def verify_ash_masks(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    qm_indices: tuple[int, ...],
    charges: tuple[float, ...],
) -> dict[str, Any]:
    """Verify the installed ASH masks, including its explicit boundary policy."""
    qset = set(qm_indices)
    if before["force_roster"] != after["force_roster"] or len(
        after["particles"]
    ) != len(charges):
        raise ValueError("native force/particle roster changed unexpectedly")
    for i, (old, new) in enumerate(
        zip(before["particles"], after["particles"], strict=True)
    ):
        if old[1:] != new[1:] or new[0] != charges[i] or (i in qset and new[0] != 0):
            raise ValueError("particle LJ or selected charge/mask differs")
    removed = {}
    for kind, size, threshold in (
        ("bonds", 2, 2),
        ("angles", 3, 2),
        ("torsions", 4, 3),
    ):
        if len(before[kind]) != len(after[kind]):
            raise ValueError("ASH changed bonded-term denominator")
        count = 0
        for old, new in zip(before[kind], after[kind], strict=True):
            zero = sum(i in qset for i in old[:size]) >= threshold
            expected = old[:-1] + (0.0 if zero else old[-1],)
            if new != expected:
                raise ValueError(f"ASH {kind} mask or retained boundary term differs")
            count += int(zero)
        removed[kind] = count
    exceptions = {tuple(sorted(r[:2])): r[2:] for r in after["exceptions"]}
    if len(exceptions) != len(after["exceptions"]):
        raise ValueError("duplicate masked exception")
    for a in qm_indices:
        for b in qm_indices:
            if a < b and exceptions.get((a, b)) != (0.0, 0.0, 0.0):
                raise ValueError("QM-QM classical nonbonded interaction survives")
    cross = 0
    for old in before["exceptions"]:
        pair = tuple(sorted(old[:2]))
        if (pair[0] in qset) != (pair[1] in qset):
            if pair not in exceptions or exceptions[pair][1:] != old[3:]:
                raise ValueError("source cross-boundary exception LJ changed")
            if exceptions[pair][0] != 0.0:
                raise ValueError("source cross-boundary exception Coulomb survives")
            cross += 1
    return {
        "masked_bonded_counts": removed,
        "physical_lj_particles_preserved": True,
        "cross_exception_lj_preserved_count": cross,
        "qm_qm_nonbonded_removed": True,
        "boundary_policy": "keep_cut_bond;remove_angles_with_ge2QM;remove_torsions_with_ge3QM",
    }


def _bind_fixed_links(
    theory: Any, coordinates: Any, links: tuple[tuple[Any, ...], ...]
) -> dict[str, Any]:
    """Check ASH's unmodified simple-link geometry and fixed endpoints.

    The exact original cap operands remain source witnesses. Initial ASH
    rounding deltas are retained explicitly. No generated coordinate is
    overwritten, so ASH's ordinary link force projection remains applicable.
    Both endpoints are fixed by the selected active-coordinate domain.
    """
    expected_pairs = tuple((int(row[2]), int(row[3])) for row in links)
    if expected_pairs != tuple(sorted(expected_pairs)):
        raise ValueError("generated-link/source order differs from ASH order")
    found = tuple(sorted((q, m) for q, ms in theory.boundaryatoms.items() for m in ms))
    if found != expected_pairs:
        raise ValueError("ASH inferred a boundary other than the five declared cuts")
    endpoints = {
        i: tuple(float(v) for v in coordinates[i]) for p in expected_pairs for i in p
    }
    held = tuple(
        tuple(_finite(v, "held cap coordinate") for v in row[4]) for row in links
    )
    original = theory.create_linkatoms
    initial = tuple(tuple(map(float, xyz)) for xyz in original(coordinates))
    if len(initial) != len(held):
        raise ValueError("ASH generated-link denominator differs")
    deltas = tuple(
        math.dist(xyz, retained) for xyz, retained in zip(initial, held, strict=True)
    )
    if any(delta > LINK_WITNESS_TOLERANCE_ANGSTROM for delta in deltas):
        raise ValueError("ASH initial link geometry differs from the held cap")

    def selected_links(self: Any, current_coords: Any) -> list[list[float]]:
        if any(
            tuple(float(v) for v in current_coords[i]) != xyz
            for i, xyz in endpoints.items()
        ):
            raise ValueError("fixed physical link endpoint moved")
        generated = original(current_coords)
        if tuple(tuple(map(float, xyz)) for xyz in generated) != initial:
            raise ValueError("ASH generated cap moved despite fixed endpoints")
        return generated

    theory.create_linkatoms = MethodType(selected_links, theory)
    theory.create_linkatoms(coordinates)
    return {
        "links": tuple(
            (row[0], row[1], row[2], row[3], held[i], initial[i], deltas[i])
            for i, row in enumerate(links)
        ),
        "fixed_endpoints_verified": True,
        "original_held_cap_bytes_unchanged": True,
        "native_link_generation_unmodified": True,
        "generated_cap_count": len(held),
    }


def _bind_point_field(
    theory: Any,
    coordinates: tuple[tuple[float, ...], ...],
    elements: tuple[str, ...],
    qm_indices: tuple[int, ...],
    expected_pc: tuple[float, ...],
    *,
    fixed_mm: bool,
    audit: dict[str, Any],
) -> None:
    """Check lazy ASH runprep and each callback without priming its cache.

    Reference MM sites are all fixed. The synthetic control permits moving
    sites for finite differences while checking exact current row ordering.
    No source rational is silently replaced: the selected IEEE float view is
    derived once by the caller/helper and retained beside source fractions.
    """
    qset = set(qm_indices)
    mm_indices = tuple(i for i in range(len(coordinates)) if i not in qset)
    mm_elements = tuple(elements[i] for i in mm_indices)
    link_count = sum(len(values) for values in theory.boundaryatoms.values())
    qm_elements = tuple(elements[i] for i in qm_indices) + ("H",) * link_count
    if tuple(map(int, theory.mmatoms)) != mm_indices or len(expected_pc) != len(
        mm_indices
    ):
        raise ValueError("selected point-charge row denominator/order differs")
    expected_pc = tuple(_finite(v, "selected PC float view") for v in expected_pc)
    current: dict[str, Any] = {"coords": None}
    original_run, original_prep, original_callback = (
        theory.run,
        theory.runprep,
        theory.qm_theory.run,
    )
    audit.update(
        point_field_materialized=False,
        expected_point_charge_rows=len(mm_indices),
        expected_nonzero_point_charge_atoms=sum(v != 0 for v in expected_pc),
        selected_mm_full_indices=mm_indices,
        point_charge_float_policy="Python float(Fraction(n,d));ASH source shift for synthetic fixture",
        verified_callback_entries=0,
    )

    def coord_rows(value: Any) -> tuple[tuple[float, ...], ...]:
        rows = tuple(
            tuple(_finite(v, "current Å coordinate") for v in row) for row in value
        )
        if len(rows) != len(coordinates) or any(len(row) != 3 for row in rows):
            raise ValueError("current complete physical coordinate shape differs")
        return rows

    def check_cache(self: Any) -> None:
        if (
            tuple(map(int, self.mmatoms)) != mm_indices
            or tuple(map(float, self.pointcharges)) != expected_pc
            or tuple(self.mm_elems_for_qmprogram) != mm_elements
            or tuple(self.current_qmelems) != qm_elements
        ):
            raise ValueError(
                "ASH lazy point-charge/element ordering differs from selected field"
            )

    def guarded_prep(self: Any, current_coords: Any) -> Any:
        if audit["point_field_materialized"]:
            raise ValueError("ASH point-field cache preparation entered twice")
        result = original_prep(current_coords)
        check_cache(self)
        audit["point_field_materialized"] = True
        audit["realized_nonzero_point_charge_atoms"] = sum(
            int(v != 0) for v in self.pointcharges
        )
        return result

    def guarded_run(self: Any, *args: Any, **kwargs: Any) -> Any:
        operand = kwargs.get("current_coords", args[0] if args else None)
        rows = coord_rows(operand)
        if fixed_mm and any(rows[i] != coordinates[i] for i in mm_indices):
            raise ValueError(
                "fixed reference MM physical coordinate moved before callback"
            )
        current["coords"] = rows
        if audit["point_field_materialized"]:
            check_cache(self)
        return original_run(*args, **kwargs)

    def guarded_callback(self: Any, *args: Any, **kwargs: Any) -> Any:
        if args or not audit["point_field_materialized"] or current["coords"] is None:
            raise ValueError(
                "QM callback lacks admitted current full-coordinate/field view"
            )
        check_cache(theory)
        rows = current["coords"]
        expected_mm_coords = tuple(rows[i] for i in mm_indices)
        links = theory.create_linkatoms(rows)
        expected_qm_coords = tuple(rows[i] for i in qm_indices) + tuple(
            tuple(map(float, row)) for row in links
        )
        if (
            tuple(tuple(map(float, row)) for row in kwargs.get("current_MM_coords", ()))
            != expected_mm_coords
            or tuple(tuple(map(float, row)) for row in kwargs.get("current_coords", ()))
            != expected_qm_coords
            or tuple(map(float, kwargs.get("MMcharges", ()))) != expected_pc
            or tuple(kwargs.get("qm_elems", ())) != qm_elements
            or tuple(kwargs.get("mm_elems", ())) != mm_elements
            or kwargs.get("PC") is not True
        ):
            raise ValueError(
                "QM callback physical/PC coordinate, charge or element row join differs"
            )
        audit["verified_callback_entries"] += 1
        return original_callback(**kwargs)

    theory.runprep = MethodType(guarded_prep, theory)
    theory.run = MethodType(guarded_run, theory)
    theory.qm_theory.run = MethodType(guarded_callback, theory.qm_theory)


def _construct_ash(
    parm_path: Path,
    elements: tuple[str, ...],
    coordinates: tuple[tuple[float, ...], ...],
    qm_indices: tuple[int, ...],
    charges: tuple[float, ...],
    qm_callback: Any,
    *,
    libs: NativeLibraries,
    qm_charge: int,
) -> tuple[Any, Any, Any, dict[str, Any]]:
    if (
        not hasattr(qm_callback, "run")
        or getattr(qm_callback, "__class__").__name__ != "StrictQmmmXtbTheoryV1"
    ):
        raise ValueError("selected strict QM callback is required")
    libs.ash.settings_ash.settings_dict.update(
        connectivity_code="py",
        nonbondedMM_code="py",
        print_input=False,
        print_exit_footer=False,
        print_full_timings=False,
    )
    fragment = libs.ash.Fragment(
        elems=list(elements),
        coords=libs.numpy.array(coordinates),
        charge=None,
        mult=None,
    )
    classical = libs.ash.OpenMMTheory(
        Amberfiles=True,
        amberprmtopfile=str(parm_path),
        periodic=False,
        platform="Reference",
        numcores=1,
        autoconstraints=None,
        hydrogenmass=None,
        rigidwater=False,
        printlevel=0,
        delete_QM1_MM1_bonded=False,
    )
    if (
        classical.system.getNumParticles() != len(elements)
        or classical.system.getNumConstraints() != 0
    ):
        raise ValueError("native dry physical denominator or constraints differ")
    # All selected particle charges are assigned before ASH masks; explicit
    # exception products are corrected separately after its constructor.
    classical.update_charges(tuple(range(len(elements))), charges)
    before = inspect_force_snapshot(classical.system, unit=libs.unit)
    theory = libs.ash.QMMMTheory(
        qm_theory=qm_callback,
        mm_theory=classical,
        fragment=fragment,
        qmatoms=list(qm_indices),
        charges=list(charges),
        qm_charge=qm_charge,
        qm_mult=1,
        embedding="elstat",
        TruncatedPC=False,
        numcores=1,
        printlevel=0,
        linkatom_method="simple",
        linkatom_simple_distance=1.09,
        linkatom_forceproj_method="adv",
        chargeboundary_method="shift",
        dipole_correction=False,
        openmm_externalforce=False,
    )
    if tuple(theory.qmatoms) != qm_indices:
        raise ValueError(
            "ASH real-QM ordering differs from explicit physical index map"
        )
    return theory, fragment, classical, before


def _check_original_source(path: str | Path) -> Path:
    result = Path(path)
    if (
        result.is_symlink()
        or not result.is_file()
        or result.stat().st_size != SOURCE_BYTES
    ):
        raise ValueError("original complete native prmtop file binding differs")
    h = sha256()
    with result.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    if h.hexdigest() != SOURCE_SHA256:
        raise ValueError("original native prmtop digest differs")
    return result


def _validate_reference_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if (
        manifest.get("manifest_kind") != "DEVELOPMENT_REFERENCE_INDEX_PLAN"
        or manifest.get("context_variant") != "unedited-reference"
        or manifest.get("proton_view") != "V2"
        or manifest.get("original_prmtop_binding")
        not in (
            ("WT-HID91/prepared.prmtop", SOURCE_BYTES, SOURCE_SHA256),
            ["WT-HID91/prepared.prmtop", SOURCE_BYTES, SOURCE_SHA256],
        )
        or manifest.get("bonded_parameter_splice_complete") is not False
        or manifest.get("executable_native_hamiltonian") is not False
        or type(manifest.get("native_effects")) is not int
        or manifest.get("native_effects") != 0
    ):
        raise ValueError("explicit cold reference-V2 source/index plan required")
    rows = tuple(manifest["physical_atoms"])
    if len(rows) != DRY_ATOMS or tuple(r[0] for r in rows) != tuple(
        f"amber:{i + 1}" for i in range(DRY_ATOMS)
    ):
        raise ValueError("complete original physical ID order differs")
    elements = tuple(r[1] for r in rows)
    coordinates = tuple(
        tuple(_finite(v, "physical Å coordinate") for v in r[2]) for r in rows
    )
    if any(len(v) != 3 for v in coordinates):
        raise ValueError("physical coordinate shape differs")
    q = tuple(manifest["real_qm_full_indices_0based"])
    active = tuple(manifest["active_full_indices_0based"])
    fixed = tuple(manifest["fixed_real_qm_full_indices_0based"])
    mm = tuple(manifest["fixed_mm_full_indices_0based"])
    for values in (q, active, fixed, mm):
        if values != tuple(sorted(set(values))) or any(
            type(i) is not int or not 0 <= i < DRY_ATOMS for i in values
        ):
            raise ValueError("physical index roster is not ordered, bounded, complete")
    if (len(q), len(active), len(fixed), len(mm)) != (76, 50, 26, 13752):
        raise ValueError("reference QM/mobile/fixed/environment denominator differs")
    if (
        set(active) & set(fixed)
        or set(active) | set(fixed) != set(q)
        or set(q) & set(mm)
        or set(q) | set(mm) != set(range(DRY_ATOMS))
    ):
        raise ValueError("source physical index partitions differ")
    links = tuple(tuple(r) for r in manifest["generated_links"])
    if len(links) != 5 or tuple(r[1] for r in links) != tuple(range(76, 81)):
        raise ValueError("reference generated-cap indices differ")
    for row in links:
        if row[2] not in fixed or row[3] not in mm:
            raise ValueError("generated link endpoints are not fixed physical CB/CA")
    fractions = tuple(
        _fraction(v, "classical physical q")
        for v in manifest["classical_charge_fractions"]
    )
    if len(fractions) != DRY_ATOMS or any(fractions[i] for i in q):
        raise ValueError("classical QM exclusion/charge denominator differs")
    mmset = set(mm)
    if sum(v == 0 for i, v in enumerate(fractions) if i in mmset) != 5:
        raise ValueError(
            "five zero-charge MM CA atoms must remain in the steric roster"
        )
    joins = tuple(manifest["spectator_atom_joins"])
    if any(type(r[0]) is not int or type(r[1]) is not int for r in joins):
        raise ValueError("native donor join requires exact integer indices")
    donor_map = {r[1] - 1: r[0] for r in joins}
    if len(joins) != 17 or len(donor_map) != 17:
        raise ValueError("complete spectator donor roster required")
    return {
        "elements": elements,
        "coordinates": coordinates,
        "qm_indices": q,
        "active_indices": active,
        "fixed_indices": fixed,
        "mm_indices": mm,
        "links": links,
        "charges": tuple(float(v) for v in fractions),
        "charge_fractions": fractions,
        "donor_map": donor_map,
    }


def verify_spectator_peptide(
    source: Any, dry: Any, donor_map: Mapping[int, int], manifest: Mapping[str, Any]
) -> dict[str, Any]:
    target = set(donor_map.values())

    def edges(structure: Any) -> tuple[tuple[int, int], ...]:
        return tuple(
            sorted(
                tuple(sorted((b.atom1.idx, b.atom2.idx)))
                for b in structure.bonds
                if bool({b.atom1.idx, b.atom2.idx} & target)
                and not {b.atom1.idx, b.atom2.idx} <= target
            )
        )

    original, realized = edges(source), edges(dry)
    witnessed = tuple(
        sorted(
            tuple(sorted((int(row[0]) - 1, int(row[1]) - 1)))
            for row in manifest["spectator_target_original_external_bond_witnesses"]
        )
    )
    prepared = tuple(
        sorted(
            tuple(sorted(int(atom_id.split(":")[1]) - 1 for atom_id in pair))
            for pair in manifest["spectator_target_prepared_external_bonds"]
        )
    )
    if original != witnessed or original != prepared or realized != original:
        raise ValueError("spectator native external peptide bond/multiplicity differs")
    return {
        "original_external_peptide_bonds_full0": original,
        "prepared_external_peptide_bonds_full0": realized,
        "external_peptide_bond_multiplicity_preserved": True,
    }


def prepare_reference_topology(
    original_prmtop_path: str | Path,
    reference_manifest: Mapping[str, Any],
    *,
    scratch_directory: str | Path,
    protocol_sha256: str,
    parmed: Any,
    native_numpy: Any,
    observe_native: Callable[[str, Any], None] | None = None,
) -> NativeReferencePreparation:
    """The shared real pre-ASH source preparation, with optional raw witnesses.

    Inject live libraries only after the selected caller's profile/effect gate.
    Observation precedes admission guards and preserves partial destructive
    operations on refusal; it never replaces those guards or creates authority.
    No ASH object, OpenMM Context, energy/force or QM callback is constructed.
    """
    selected = _validate_reference_manifest(reference_manifest)
    source_path = _check_original_source(original_prmtop_path)
    scratch = _selected_scratch(scratch_directory, protocol_sha256)
    source = parmed.load_file(str(source_path))
    if observe_native is not None:
        observe_native("original-loaded", source)
    if len(source.atoms) != FULL_ATOMS:
        raise ValueError("complete original native source atom census differs")
    source_lj = source_lj_tables(source)
    original_atoms = _native_source_atom_roster(source, FULL_ATOMS)
    original_bonded = _bonded_topology_witness(source)
    dry, dry_selection = _strip_bound_dry_core(
        source_path, source, parmed=parmed, observe_native=observe_native
    )
    lj_audits = [dry_selection]
    try:
        splice = splice_spectator_hid(
            source, dry, selected["donor_map"], parmed=parmed
        )
    finally:
        if observe_native is not None:
            observe_native("dry-after-donor-splice", dry)
    peptide = verify_spectator_peptide(
        source, dry, selected["donor_map"], reference_manifest
    )
    rows = reference_manifest["physical_atoms"]
    parameters = reference_manifest["physical_parameters"]
    if len(parameters) != DRY_ATOMS:
        raise ValueError("complete source parameter assignment roster differs")
    donor_by_target = {target: donor for donor, target in selected["donor_map"].items()}
    source_charge_max_error = 0.0
    for i, (atom, physical, parameter) in enumerate(
        zip(dry.atoms, rows, parameters, strict=True)
    ):
        expected_source_index = donor_by_target.get(i, i) + 1
        witness = source.atoms[expected_source_index - 1]
        source_charge = float(Fraction(parameter[6]) / Fraction("18.2223"))
        source_charge_error = abs(
            _finite(witness.charge, "native source charge") - source_charge
        )
        source_charge_max_error = max(source_charge_max_error, source_charge_error)
        if (
            parameter[0] != physical[0]
            or parameter[1] != i + 1
            or parameter[2] != expected_source_index
            or witness.type != parameter[3]
            or witness.nb_idx != parameter[4]
            or witness.mass != float(parameter[5])
            or source_charge_error > 1e-14
            or atom.type != parameter[3]
            or atom.nb_idx != parameter[4]
            or atom.mass != float(parameter[5])
        ):
            raise ValueError(
                "native source/donor index, type, LJ, mass or lexical-charge assignment differs"
            )
        # A's former HE2 nucleus is now called HD1 in QM, while its frozen
        # classical type/graph remains an explicit cross-LJ approximation.
        atom.name = physical[6]
        atom.charge = selected["charges"][i]
    classical_edges = {tuple(sorted((b.atom1.idx, b.atom2.idx))) for b in dry.bonds}
    physical_edges = {
        tuple(sorted(v))
        for v in reference_manifest["physical_bonds_full_indices_0based"]
    }
    qset = set(selected["qm_indices"])
    mismatches = classical_edges ^ physical_edges
    if any(not set(pair) <= qset for pair in mismatches):
        raise ValueError("unparameterized graph change crosses QM/MM or remains in MM")
    dry.coordinates = native_numpy.array(selected["coordinates"])
    try:
        dry.remake_parm()
    finally:
        if observe_native is not None:
            observe_native("dry-after-charge-remake", dry)
    _verify_bound_type_slots(dry, DRY_ATOMS)
    lj_audits.append(
        verify_source_lj_tables(source_lj, dry, stage="complete donor/charge remake")
    )
    bonded_before = _bonded_topology_witness(dry)
    prmtop = scratch / "reference-v2-derived.prmtop"
    try:
        dry.save(str(prmtop), overwrite=False)
    finally:
        if observe_native is not None:
            observe_native("dry-after-save", dry)
    reloaded = parmed.load_file(str(prmtop))
    if observe_native is not None:
        observe_native("derived-reloaded", reloaded)
    if len(reloaded.atoms) != DRY_ATOMS:
        raise ValueError("derived native topology save/reload atom denominator differs")
    _verify_bound_type_slots(reloaded, DRY_ATOMS)
    lj_audits.append(
        verify_source_lj_tables(source_lj, reloaded, stage="derived save/reload")
    )
    bonded_roundtrip = verify_bonded_roundtrip(bonded_before, reloaded)
    peptide_after = verify_spectator_peptide(
        source, reloaded, selected["donor_map"], reference_manifest
    )
    if peptide_after != peptide:
        raise ValueError("spectator peptide witness changed on native save/reload")
    if tuple((a.name, a.type, a.nb_idx, a.mass) for a in reloaded.atoms) != tuple(
        (a.name, a.type, a.nb_idx, a.mass) for a in dry.atoms
    ):
        raise ValueError(
            "derived native atom type/name/mass order changed on save/reload"
        )
    if observe_native is not None:
        observe_native("original-preparation-complete", source)
    _verify_bound_type_slots(source, FULL_ATOMS)
    verify_source_lj_tables(source_lj, source, stage="pristine source after preparation")
    if _native_source_atom_roster(source, FULL_ATOMS) != original_atoms:
        raise ValueError("native preparation altered pristine donor source atoms")
    verify_bonded_roundtrip(original_bonded, source)
    audit = {
        "role": "DEVELOPMENT_NATIVE_TOPOLOGY_PREPARATION_NOT_SCIENTIFIC_QUALIFICATION",
        "source_plan_id": reference_manifest["plan_id"],
        "original_prmtop_sha256": SOURCE_SHA256,
        "protocol_sha256": protocol_sha256,
        "spectator_splice": splice,
        "spectator_peptide": peptide,
        "source_lj_table_audits": tuple(lj_audits),
        "native_bonded_roundtrip": bonded_roundtrip,
        "source_lexical_charge_conversion": {
            "native_scale": "18.2223",
            "maximum_parmed_vs_exact_source_float_error_e": source_charge_max_error,
            "software_source_conversion_tolerance_e": 1e-14,
        },
        "wholly_qm_classical_graph_differences": tuple(sorted(mismatches)),
        "fixed_source_qm_cross_lj_type_policy": reference_manifest["qm_lj_type_policy"],
        "pristine_full_source_after_preparation": True,
        "derived_prmtop_sha256": sha256(prmtop.read_bytes()).hexdigest(),
        "native_contexts": 0,
        "native_force_evaluations": 0,
        "qm_callbacks": 0,
    }
    return NativeReferencePreparation(
        source, dry, reloaded, prmtop, scratch, selected, audit
    )


def build_reference_coupling(
    original_prmtop_path: str | Path,
    reference_manifest: Mapping[str, Any],
    qm_callback: Any,
    *,
    scratch_directory: str | Path,
    protocol_sha256: str,
    native_libraries: NativeLibraries | None = None,
    site_packages: str | Path | None = None,
) -> CouplingSession:
    """Explicit native preparation after the frozen caller authenticates inputs.

    Full original source is hash-checked before ParmEd. The dry topology is
    copied without coordinate regeneration. Active-A classical connectivity
    differences are admitted only wholly inside QM; its fixed source LJ types
    persist. The spectator is fully parameter-spliced. No Context, force or
    QM callback is invoked here.
    """
    _validate_reference_manifest(reference_manifest)
    _check_original_source(original_prmtop_path)
    libs = _selected_libraries(native_libraries, site_packages, protocol_sha256)
    prepared = prepare_reference_topology(
        original_prmtop_path,
        reference_manifest,
        scratch_directory=scratch_directory,
        protocol_sha256=protocol_sha256,
        parmed=libs.parmed,
        native_numpy=libs.numpy,
    )
    selected = prepared.selected
    dry = prepared.dry
    prmtop = prepared.prmtop_path
    scratch = prepared.scratch_directory
    rows = reference_manifest["physical_atoms"]
    scales = source_scee_by_pair(dry)
    theory, fragment, classical, before = _construct_ash(
        prmtop,
        selected["elements"],
        selected["coordinates"],
        selected["qm_indices"],
        selected["charges"],
        qm_callback,
        libs=libs,
        qm_charge=-6,
    )
    # Already-projected CA=0 and q_CA/3 field charges are supplied. ASH's shift
    # then adds zero, preventing a second redistribution. Verify its recipients.
    for row in selected["links"]:
        ca = row[3]
        expected = {
            i
            for i, atom in enumerate(rows)
            if atom[3:5] == rows[ca][3:5] and atom[6] in ("N", "C", "HA")
        }
        if (
            set(theory.MMboundarydict[ca]) != expected
            or len(expected) != 3
            or selected["charges"][ca] != 0
        ):
            raise ValueError("CA charge-shift neighbors differ from N/C/HA source rule")
    links = _bind_fixed_links(
        theory, libs.numpy.array(selected["coordinates"]), selected["links"]
    )
    correction = correct_coulomb_exceptions(
        classical.system,
        selected["qm_indices"],
        selected["charges"],
        scales,
        unit=libs.unit,
    )
    after = inspect_force_snapshot(classical.system, unit=libs.unit)
    masks = verify_ash_masks(before, after, selected["qm_indices"], selected["charges"])
    audit = {
        "role": "NEW_SOURCE_DERIVED_REFERENCE_V2_NATIVE_PREPARATION_NOT_SCIENTIFIC_QUALIFICATION",
        "original_prmtop_sha256": SOURCE_SHA256,
        "protocol_sha256": protocol_sha256,
        "source_plan_id": reference_manifest["plan_id"],
        "physical_atoms": DRY_ATOMS,
        "real_qm_atoms": 76,
        "generated_links": 5,
        "total_qm_atoms": 81,
        "active_physical_atoms": 50,
        "fixed_real_qm_atoms": 26,
        "fixed_total_qm_atoms": 31,
        "environment_steric_atoms": 13752,
        "nonzero_point_charge_atoms": 13747,
        "force_roster": after["force_roster"],
        "force_counts": {
            k: len(after[k])
            for k in ("particles", "exceptions", "bonds", "angles", "torsions")
        },
        **{k: v for k, v in prepared.audit.items() if k != "role"},
        "links": links,
        "exception_correction": correction,
        "masks": masks,
        "native_contexts": 0,
        "native_force_evaluations": 0,
        "qm_callbacks": 0,
        "derived_prmtop_sha256": sha256(prmtop.read_bytes()).hexdigest(),
    }
    _bind_point_field(
        theory,
        selected["coordinates"],
        selected["elements"],
        selected["qm_indices"],
        tuple(selected["charges"][i] for i in selected["mm_indices"]),
        fixed_mm=True,
        audit=audit,
    )
    return CouplingSession(
        theory,
        fragment,
        selected["active_indices"],
        tuple(sorted(set(selected["fixed_indices"]) | set(selected["mm_indices"]))),
        audit,
        scratch,
    )


def build_ethane_control(
    qm_callback: Any,
    *,
    scratch_directory: str | Path,
    protocol_sha256: str,
    native_libraries: NativeLibraries | None = None,
    site_packages: str | Path | None = None,
) -> CouplingSession:
    """Deferred synthetic native fixture, reusing the parent's Amber roundtrip.

    Calling this after freeze constructs a native System but evaluates no force
    or QM method. The caller owns the exact finite control call menu.
    """
    libs = _selected_libraries(native_libraries, site_packages, protocol_sha256)
    scratch = _selected_scratch(scratch_directory, protocol_sha256)
    app, mm, unit = libs.app, libs.openmm, libs.unit
    topology = app.Topology()
    residue = topology.addResidue("ETH", topology.addChain())
    elements = ("C", "C") + ("H",) * 6
    native_elements = (app.element.carbon,) * 2 + (app.element.hydrogen,) * 6
    atoms = [
        topology.addAtom(f"{e.symbol}{i}", e, residue)
        for i, e in enumerate(native_elements)
    ]
    pairs = ((0, 1), (0, 2), (0, 3), (0, 4), (1, 5), (1, 6), (1, 7))
    coords = (
        (-0.77, 0.0, 0.0),
        (0.77, 0.0, 0.0),
        (-1.13, 1.02, 0.0),
        (-1.13, -0.51, 0.88),
        (-1.13, -0.51, -0.88),
        (1.13, -1.02, 0.0),
        (1.13, 0.51, 0.88),
        (1.13, 0.51, -0.88),
    )
    system = mm.System()
    nonbonded = mm.NonbondedForce()
    harmonic = mm.HarmonicBondForce()
    source_charges = (0.12, 0.12, -0.04, -0.04, -0.04, -0.03, -0.04, -0.05)
    for i, element in enumerate(native_elements):
        system.addParticle(element.mass)
        nonbonded.addParticle(source_charges[i], 0.25, 0.1)
    for a, b in pairs:
        topology.addBond(atoms[a], atoms[b])
        harmonic.addBond(a, b, 0.154 if (a, b) == (0, 1) else 0.109, 100000.0)
    nonbonded.createExceptionsFromBonds(pairs, 1 / 1.2, 0.5)
    system.addForce(nonbonded)
    system.addForce(harmonic)
    structure = libs.parmed.openmm.load_topology(
        topology, system, xyz=libs.numpy.array(coords)
    )
    prmtop = scratch / "ethane-control.prmtop"
    structure.save(str(prmtop), overwrite=False)
    q = (0, 2, 3, 4)
    charges = tuple(0.0 if i in q else source_charges[i] for i in range(8))
    theory, fragment, classical, before = _construct_ash(
        prmtop, elements, coords, q, charges, qm_callback, libs=libs, qm_charge=0
    )
    if theory.boundaryatoms != {0: [1]}:
        raise ValueError("synthetic ASH cut differs from C0-C1")
    scales = {
        tuple(sorted((a, b))): Fraction(6, 5) for a in (2, 3, 4) for b in (5, 6, 7)
    }
    correction = correct_coulomb_exceptions(
        classical.system, q, charges, scales, unit=unit
    )
    after = inspect_force_snapshot(classical.system, unit=unit)
    masks = verify_ash_masks(before, after, q, charges)
    # The fixture deliberately has two nonzero *shifted* field sites. Unlike
    # the historical symmetric fixture, it exercises genuine PC derivatives.
    # Classical MM charges remain the selected unshifted values; ASH shifts
    # only its QM point-charge view. This is an explicit additive Hamiltonian.
    expected_pc = (
        0.0,
        charges[5] + charges[1] / 3,
        charges[6] + charges[1] / 3,
        charges[7] + charges[1] / 3,
    )
    if sum(v != 0 for v in expected_pc) != 2:
        raise ValueError(
            "synthetic shifted field is not the selected two-site PC control"
        )
    audit = {
        "role": "SYNTHETIC_NATIVE_CONTROL_NOT_RUBISCO_EVIDENCE",
        "physical_atoms": 8,
        "real_qm_atoms": 4,
        "generated_links": 1,
        "qm_charge": 0,
        "protocol_sha256": protocol_sha256,
        "exception_correction": correction,
        "masks": masks,
        "classical_charges": charges,
        "source_charges": source_charges,
        "expected_shifted_mm_pointcharges": expected_pc,
        "expected_nonzero_point_charge_atoms": 2,
        "point_field_materialized": False,
        "classical_charge_policy": "unshifted-source-MM;QM-particle-and-exception-zero",
        "quantum_field_policy": "ASH-CAcharge-shift-only;no-dipole-correction",
        "native_contexts": 0,
        "native_force_evaluations": 0,
        "qm_callbacks": 0,
        "derived_prmtop_sha256": sha256(prmtop.read_bytes()).hexdigest(),
    }
    _bind_point_field(
        theory, coords, elements, q, expected_pc, fixed_mm=False, audit=audit
    )
    return CouplingSession(
        theory, fragment, (3, 4), (0, 1, 2, 5, 6, 7), audit, scratch
    )
