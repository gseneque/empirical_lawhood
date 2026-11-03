# SPDX-License-Identifier: MPL-2.0
"""Independent complete assigned-term census; no native imports or construction."""

from collections import Counter
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext
from io import StringIO
from itertools import product
from math import isfinite
import re


def _number(value, name):
    if value is None or not isfinite(float(value)):
        raise ValueError(f"unassigned/nonfinite molecular parameter: {name}")
    return repr(float(value))


def assigned_parameter_inventory(structure):
    """Enumerate every term of an actually generated ParmEd Amber topology.

    Original native parameter values, zeros and signs are retained. Missing
    coefficients refuse. This checks actual assignment, not chemical accuracy.
    The complete rows belong in retained custody, not a silently truncated log.
    """
    atom_rows = []
    atom_map = {}
    for index, atom in enumerate(structure.atoms):
        if atom.idx != index or atom in atom_map:
            raise ValueError("molecular topology duplicates or reorders atom identity")
        atom_map[atom] = index
        atom_rows.append(
            dict(
                index=index,
                name=atom.name,
                residue_index=atom.residue.idx,
                residue_name=atom.residue.name,
                residue_number=atom.residue.number,
                chain=atom.residue.chain,
                atomic_number=atom.atomic_number,
                atom_type=atom.type,
                charge_electron=_number(atom.charge, "charge"),
                mass_dalton=_number(atom.mass, "mass"),
                rmin_half_angstrom=_number(atom.rmin, "LJ radius"),
                epsilon_kcal_mol=_number(atom.epsilon, "LJ epsilon"),
            )
        )
        if not atom.type or not atom.atomic_number or atom.mass <= 0:
            raise ValueError("molecular topology contains an untyped/unknown atom")
    if not atom_rows:
        raise ValueError("empty molecular parameter assignment")
    rows = {"atoms": atom_rows}
    specifications = (
        ("bonds", ("atom1", "atom2"), ("k", "req")),
        ("angles", ("atom1", "atom2", "atom3"), ("k", "theteq")),
        (
            "dihedrals",
            ("atom1", "atom2", "atom3", "atom4"),
            ("phi_k", "phase", "per", "scee", "scnb"),
        ),
    )
    for category, atoms, coefficients in specifications:
        assigned = []
        for term in getattr(structure, category):
            if term.type is None:
                raise ValueError(f"unassigned molecular {category} term")
            try:
                indices = tuple(atom_map[getattr(term, name)] for name in atoms)
            except KeyError as error:
                raise ValueError("bonded term refers to an absent atom") from error
            entry = dict(
                atoms=indices,
                coefficients={
                    name: _number(getattr(term.type, name, None), name)
                    for name in coefficients
                },
            )
            if category == "dihedrals":
                entry.update(
                    improper=bool(term.improper), ignore_end=bool(term.ignore_end)
                )
            assigned.append(entry)
        rows[category] = assigned
    # Amber's complete interaction matrix is retained independently of per-atom
    # radii: mixing and exclusions must not disappear in a coverage summary.
    required = (
        "NONBONDED_PARM_INDEX",
        "LENNARD_JONES_ACOEF",
        "LENNARD_JONES_BCOEF",
        "NUMBER_EXCLUDED_ATOMS",
        "EXCLUDED_ATOMS_LIST",
    )
    if any(name not in structure.parm_data for name in required):
        raise ValueError("generated Amber topology omits nonbonded/exclusion tables")
    rows["native_nonbonded_tables"] = {
        name: tuple(_number(value, name) for value in structure.parm_data[name])
        for name in required
    }
    if any(
        getattr(structure, name, ())
        for name in ("urey_bradleys", "cmaps", "rb_torsions", "impropers", "adjusts")
    ):
        raise ValueError("selected Amber assignment contains unenumerated term classes")
    rows["term_census"] = {
        name: len(rows[name]) for name in ("atoms", "bonds", "angles", "dihedrals")
    }
    rows["residue_atom_census"] = tuple(
        sorted(
            Counter((atom.residue.name, atom.type) for atom in structure.atoms).items()
        )
    )
    rows["claim_scope"] = (
        "COMPLETE_ASSIGNED_PARAMETER_CENSUS_NOT_FORCE_FIELD_OR_KINETIC_VALIDATION"
    )
    return rows


def realized_atom_origins(structure, plan, *, chemical_residue_map=None):
    """Join every actual Amber atom to the complete native preparation topology.

    Amber files need not retain chain IDs. Their actual ordered residue/atom
    census is independently joined to the selected sixteen full protein chains
    and every original chemical/water residue. Added solvent/ions/H atoms are
    declared additions; an omitted original heavy atom or genotype refuses.
    """
    from .coordinate_plan import THREE

    reverse = {name: letter for letter, name in THREE.items()}
    reverse.update(KCX="K", HID="H", HIE="H", HIP="H", CYX="C")
    residues = list(structure.residues)
    protein_count = sum(len(row["sequence"]) for row in plan["complete_chains"])
    if len(residues) < protein_count:
        raise ValueError("Amber omits complete selected protein residues")
    expected = {}
    for atom in plan["complete_heavy_atoms"]:
        key = (atom["chain"], atom["position"])
        expected.setdefault(key, []).append(atom)
    if chemical_residue_map is not None:
        native_seen = set()
        for index, atom in enumerate(structure.atoms):
            if type(atom.idx) is not int or atom.idx != index:
                raise ValueError("Amber chemical map changes native atom identity")
        for residue in residues:
            for atom in residue.atoms:
                if not 0 <= atom.idx < len(structure.atoms) or structure.atoms[atom.idx] is not atom or atom.residue is not residue or atom.idx in native_seen:
                    raise ValueError("Amber chemical map changes native residue atom identity")
                native_seen.add(atom.idx)
        if len(native_seen) != len(structure.atoms):
            raise ValueError("Amber chemical map omits native residue atom identities")
        for originals in expected.values():
            if len({row["atom"] for row in originals}) != len(originals) or len({row["component"] for row in originals}) != 1:
                raise ValueError("Amber chemical map has duplicate/incoherent source atoms")
    joins, protein_chains = [], []
    source_residues = []
    offset = 0
    for chain in plan["complete_chains"]:
        actual = residues[offset : offset + len(chain["sequence"])]
        sequence = "".join(reverse.get(row.name, "?") for row in actual)
        if sequence != chain["sequence"]:
            raise ValueError("Amber changes full L8S8 realized genotype")
        protein_chains.append(
            chain
            | dict(
                amber_residue_indices=tuple(row.idx for row in actual),
                actual_residue_names=tuple(row.name for row in actual),
            )
        )
        source_residues.extend(
            ((chain["chain"], index + 1), row) for index, row in enumerate(actual)
        )
        offset += len(actual)
    protein_ids = {row["chain"] for row in plan["complete_chains"]}
    chemical_keys = [key for key in expected if key[0] not in protein_ids]
    if len(residues) < offset + len(chemical_keys):
        raise ValueError("Amber omits inherited chemical/water residues")
    if chemical_residue_map is None:
        source_residues.extend(
            zip(chemical_keys, residues[offset : offset + len(chemical_keys)], strict=True)
        )
    else:
        # A supplied index map is an explicit join operand, not coordinate proof.
        # The named successor below computes it from the full raw population.
        if type(chemical_residue_map) is not dict or set(chemical_residue_map) != set(chemical_keys):
            raise ValueError("Amber chemical map omits/adds source residue keys")
        selected = tuple(chemical_residue_map[key] for key in chemical_keys)
        if any(type(index) is not int or not offset <= index < len(residues) for index in selected):
            raise ValueError("Amber chemical map has an invalid native residue index")
        if len(set(selected)) != len(selected) or any(type(row.idx) is not int or row.idx != index for index, row in enumerate(residues)):
            raise ValueError("Amber chemical map duplicates/reorders native residue identity")
        source_residues.extend((key, residues[index]) for key, index in zip(chemical_keys, selected, strict=True))
        if {key for key, _ in source_residues} != set(expected):
            raise ValueError("Amber chemical map changes complete source residue denominator")
    atom_indices = {}
    for key, residue in source_residues:
        names = {atom.name: atom for atom in residue.atoms}
        if len(names) != len(residue.atoms):
            raise ValueError("Amber duplicates one residue atom name")
        originals = {row["atom"]: row for row in expected[key]}
        if not set(originals).issubset(names):
            raise ValueError("Amber omits completed/inherited heavy atom")
        expected_name = next(iter(originals.values()))["component"]
        if residue.name != expected_name and not (
            expected_name == "HOH" and residue.name == "WAT"
        ):
            raise ValueError("Amber changes inherited residue chemical state")
        for name, atom in names.items():
            original = originals.get(name)
            if original is None and atom.atomic_number != 1:
                raise ValueError("Amber silently adds an unselected nonhydrogen atom")
            if original is not None and atom.atomic_number != (
                dict(H=1, C=6, N=7, O=8, P=15, S=16, MG=12, NA=11, CL=17).get(
                    original["element"].upper()
                )
            ):
                raise ValueError("Amber changes inherited atom element")
            atom_indices[(key[0], key[1], name)] = atom.idx
            joins.append(
                dict(
                    amber_atom_index=atom.idx,
                    amber_residue_index=residue.idx,
                    chain=key[0],
                    position=key[1],
                    atom=name,
                    residue_name=residue.name,
                    source_origin=original,
                    status="REALIZED_COMPLETE_PREPARATION_ATOM"
                    if original is not None
                    else "DECLARED_AMBER_ADDED_HYDROGEN",
                )
            )
    joined = {row["amber_atom_index"] for row in joins}
    for atom in structure.atoms:
        if atom.idx not in joined:
            joins.append(
                dict(
                    amber_atom_index=atom.idx,
                    amber_residue_index=atom.residue.idx,
                    chain=None,
                    position=None,
                    atom=atom.name,
                    residue_name=atom.residue.name,
                    source_origin=None,
                    status="DECLARED_ADDED_SOLVENT_OR_NEUTRALIZING_ION",
                )
            )
            if atom.residue.name not in ("WAT", "Na+", "Cl-", "NA", "CL"):
                raise ValueError("Amber adds an undeclared non-solvent chemical")
    expected_disulfides = {
        tuple(
            sorted(
                atom_indices[(chain, position, "SG")]
                for chain, position in row["partners"]
            )
        )
        for row in plan["authenticated_disulfides"]
    }
    actual_disulfides = {
        tuple(sorted((row.atom1.idx, row.atom2.idx)))
        for row in structure.bonds
        if row.atom1.name == row.atom2.name == "SG"
    }
    if actual_disulfides != expected_disulfides:
        raise ValueError("Amber changes authenticated source disulfide assignment")
    if len(joins) != len(structure.atoms) or len(
        {row["amber_atom_index"] for row in joins}
    ) != len(joins):
        raise ValueError("Amber atom origin census omits/duplicates native atoms")
    result = dict(
        complete_chains=protein_chains,
        atoms=sorted(joins, key=lambda row: row["amber_atom_index"]),
        authenticated_disulfide_atom_pairs=sorted(expected_disulfides),
        claim_scope="ACTUAL_PARAMETER_COMPLETE_MODEL_ORIGINS_NOT_DYNAMIC_OR_KINETIC_VALIDATION",
    )
    if chemical_residue_map is not None:
        result["chemical_residue_map"] = [
            dict(chain=key[0], position=key[1], amber_residue_index=chemical_residue_map[key])
            for key in chemical_keys
        ]
    return result


_ORIGIN_ELEMENTS = dict(H=1, C=6, N=7, O=8, P=15, S=16, MG=12, NA=11, CL=17)
_ORIGIN_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)\Z")
_RESTART_DECIMAL = re.compile(r"[+-]?[0-9]+\.[0-9]{7}\Z")
_ORIGIN_SCALE = 10_000_000
_ORIGIN_HALF_UNIT = Decimal("0.00000005")


def _origin_heavy_pdb(text, expected):
    """Producer lexical Decimal reader; no independent assessor dependency."""
    if type(text) is not str or not text.isascii():
        raise ValueError("coordinate origin join requires ASCII complete-heavy PDB")
    points, serials, previous_serial = {}, {}, 0
    for line in StringIO(text):
        if line[:6] not in ("ATOM  ", "HETATM"):
            continue
        try:
            if len(line.rstrip("\r\n")) < 78 or line[16:17].strip() or line[26:27].strip():
                raise ValueError("ambiguous fixed-column atom")
            serial_token, position_token = line[6:11].strip(), line[22:26].strip()
            if not serial_token.isdigit() or not position_token.isdigit() or int(position_token) <= 0:
                raise ValueError("ambiguous source integer identity")
            serial = int(serial_token)
            key = (line[21].strip(), int(position_token), line[12:16].strip())
            component, element = line[17:20].strip(), line[76:78].strip().upper()
            tokens = tuple(line[index:index + 8].strip() for index in (30, 38, 46))
            if any(not _ORIGIN_DECIMAL.fullmatch(token) for token in tokens):
                raise ValueError("malformed coordinate")
            xyz = tuple(Decimal(token) for token in tokens)
        except (ValueError, ArithmeticError) as error:
            raise ValueError("coordinate origin join has malformed complete-heavy PDB") from error
        if serial <= previous_serial or key in points or key not in expected:
            raise ValueError("coordinate origin join duplicates/adds/reorders source atom identity")
        source = expected[key]
        if element in ("H", "D") or element != source["element"].upper() or component != source["component"]:
            raise ValueError("coordinate origin join changes source PDB element/component")
        if any(not value.is_finite() for value in xyz):
            raise ValueError("coordinate origin join has nonfinite source coordinates")
        points[key], serials[key], previous_serial = xyz, serial, serial
    if set(points) != set(expected):
        raise ValueError("coordinate origin join omits source heavy PDB atoms")
    return points, serials


def _origin_restart(text, atoms):
    """Read every raw coordinate; index every nonhydrogen, retaining native IDs."""
    if type(text) is not str or not text.isascii() or len(atoms) < 3:
        raise ValueError("coordinate origin join requires selected ASCII restart")
    lines = iter(StringIO(text))
    if next(lines, None) is None:
        raise ValueError("coordinate origin join omits restart title")
    header = next(lines, "").split()
    if not 1 <= len(header) <= 2 or not header[0].isdigit() or int(header[0]) != len(atoms):
        raise ValueError("coordinate origin join restart atom count differs")
    if len(header) == 2 and (not _ORIGIN_DECIMAL.fullmatch(header[1]) or not Decimal(header[1]).is_finite()):
        raise ValueError("coordinate origin join has invalid restart time")
    positions, index = [None] * len(atoms), {}
    pending = []
    for row in range((len(atoms) + 1) // 2):
        line = next(lines, "").rstrip("\r\n")
        count = min(6, 3 * len(atoms) - 6 * row)
        if len(line) < 12 * count or line[12 * count:].strip():
            raise ValueError("coordinate origin join restart coordinate row differs")
        for field in range(count):
            token = line[12 * field:12 * (field + 1)].strip()
            if not _RESTART_DECIMAL.fullmatch(token):
                raise ValueError("coordinate origin join requires seven-place restart coordinates")
            pending.append(int(Decimal(token) * _ORIGIN_SCALE))
            if len(pending) == 3:
                atom_index = 2 * row + (field // 3)
                atom = atoms[atom_index]
                if atom.idx != atom_index:
                    raise ValueError("coordinate origin join changes native atom order")
                if atom.atomic_number != 1:
                    point = tuple(pending)
                    positions[atom_index] = point
                    index.setdefault(point, []).append(atom_index)
                pending.clear()
    line = next(lines, "").rstrip("\r\n")
    if len(line) < 72 or line[72:].strip():
        raise ValueError("coordinate origin join requires a complete periodic box")
    tokens = tuple(line[start:start + 12].strip() for start in range(0, 72, 12))
    if any(not _RESTART_DECIMAL.fullmatch(token) for token in tokens):
        raise ValueError("coordinate origin join has malformed periodic box")
    box = tuple(Decimal(token) for token in tokens)
    if any(value <= 0 for value in box[:3]) or box[3:] != (90, 90, 90) or any(line.strip() for line in lines):
        raise ValueError("coordinate origin join requires coordinate-only orthorhombic restart")
    return positions, index


def _coordinate_chemical_residues(structure, plan, heavy_pdb, raw_inpcrd):
    expected = {}
    for source in plan["complete_heavy_atoms"]:
        key = (source["chain"], source["position"], source["atom"])
        if key in expected or _ORIGIN_ELEMENTS.get(source["element"].upper()) in (None, 1):
            raise ValueError("coordinate origin join has duplicate/unknown source heavy atoms")
        expected[key] = source
    points, serials = _origin_heavy_pdb(heavy_pdb, expected)
    atoms, residues = list(structure.atoms), list(structure.residues)
    if any(type(residue.idx) is not int or residue.idx != index for index, residue in enumerate(residues)):
        raise ValueError("coordinate origin join reorders native residues")
    seen = set()
    for residue in residues:
        for atom in residue.atoms:
            if type(atom.idx) is not int or not 0 <= atom.idx < len(atoms) or atoms[atom.idx] is not atom or atom.residue is not residue or atom.idx in seen:
                raise ValueError("coordinate origin join duplicates/changes native atom identity")
            seen.add(atom.idx)
    if len(seen) != len(atoms):
        raise ValueError("coordinate origin join omits native residue atoms")
    positions, index = _origin_restart(raw_inpcrd, atoms)
    protein_ids = {chain["chain"] for chain in plan["complete_chains"]}
    protein_residues, offset = {}, 0
    for chain in plan["complete_chains"]:
        for position in range(1, len(chain["sequence"]) + 1):
            if offset >= len(residues):
                raise ValueError("coordinate origin join omits whole protein residues")
            protein_residues[(chain["chain"], position)] = residues[offset]
            offset += 1
    intervals, mapped = None, {}

    def intersect(key, atom_index):
        nonlocal intervals
        delta = tuple(Decimal(value) / _ORIGIN_SCALE - source for value, source in zip(positions[atom_index], points[key], strict=True))
        candidate = tuple((value - _ORIGIN_HALF_UNIT, value + _ORIGIN_HALF_UNIT) for value in delta)
        intervals = candidate if intervals is None else tuple((max(old[0], new[0]), min(old[1], new[1])) for old, new in zip(intervals, candidate, strict=True))
        if any(low > high for low, high in intervals):
            raise ValueError("coordinate origin join lacks one common source translation")

    for key, source in expected.items():
        if key[0] not in protein_ids:
            continue
        residue = protein_residues.get(key[:2])
        candidates = [] if residue is None else [atom for atom in residue.atoms if atom.name == key[2] and atom.atomic_number == _ORIGIN_ELEMENTS[source["element"].upper()] and residue.name == source["component"]]
        if len(candidates) != 1:
            raise ValueError("coordinate origin join omits/changes full protein heavy anchor")
        mapped[key] = candidates[0].idx
        intersect(key, candidates[0].idx)
    protein_anchors = len(mapped)
    if not protein_anchors:
        raise ValueError("coordinate origin join has no complete protein heavy anchors")
    chemical_map, used_atoms, used_residues = {}, set(mapped.values()), set()
    # Freeze the full-protein frame during candidate selection. Refining it
    # atom by atom must not suppress an initially ambiguous competing origin.
    protein_intervals = intervals
    for key, source in expected.items():
        if key[0] in protein_ids:
            continue
        ranges = []
        for coordinate, (low, high) in zip(points[key], protein_intervals, strict=True):
            first = int(((coordinate + low - _ORIGIN_HALF_UNIT) * _ORIGIN_SCALE).to_integral_value(rounding=ROUND_CEILING))
            last = int(((coordinate + high + _ORIGIN_HALF_UNIT) * _ORIGIN_SCALE).to_integral_value(rounding=ROUND_FLOOR))
            ranges.append(range(first, last + 1))
        eligible = []
        for point in product(*ranges):
            for atom_index in index.get(point, ()):
                atom = atoms[atom_index]
                if atom.name == key[2] and atom.atomic_number == _ORIGIN_ELEMENTS[source["element"].upper()] and (atom.residue.name == source["component"] or source["component"] == "HOH" and atom.residue.name == "WAT"):
                    eligible.append(atom_index)
        if len(eligible) != 1:
            raise ValueError("coordinate origin join has absent/ambiguous chemical atom")
        atom_index, group = eligible[0], key[:2]
        residue_index = atoms[atom_index].residue.idx
        if atom_index in used_atoms or residue_index < offset:
            raise ValueError("coordinate origin join reuses a native source atom/protein residue")
        previous = chemical_map.get(group)
        if previous is not None and previous != residue_index:
            raise ValueError("coordinate origin join splits a chemical source group")
        if previous is None:
            if residue_index in used_residues:
                raise ValueError("coordinate origin join reuses a native chemical residue")
            chemical_map[group] = residue_index
            used_residues.add(residue_index)
        mapped[key] = atom_index
        used_atoms.add(atom_index)
        intersect(key, atom_index)
    grouped = {}
    for key, atom_index in mapped.items():
        grouped.setdefault(key[:2], set()).add(atom_index)
    for group, residue_index in chemical_map.items():
        native_heavy = {atom.idx for atom in residues[residue_index].atoms if atom.atomic_number != 1}
        if grouped[group] != native_heavy:
            raise ValueError("coordinate origin join adds an unselected chemical heavy atom")
    return chemical_map, serials, protein_anchors, intervals, len(index), sum(point is not None for point in positions)


def realized_atom_origins_from_coordinates(structure, plan, complete_heavy_pdb, raw_inpcrd):
    """Explicit producer successor for authentic Amber chemical permutations.

    All source protein heavy anchors determine a common translation; every
    chemical heavy atom then has exactly one name/element/component match in
    the full native nonhydrogen coordinate population. All source atoms refine
    the same translation at the restart's half-last-place serialization bound.
    This is origin postprocessing, not independent assessment or qualification.
    No native calculation, structure mutation or physical tolerance is added.
    """
    with localcontext() as context:
        context.prec = 50
        mapping, serials, anchors, intervals, cells, native_heavy = _coordinate_chemical_residues(structure, plan, complete_heavy_pdb, raw_inpcrd)
    result = realized_atom_origins(structure, plan, chemical_residue_map=mapping)
    for row in result["atoms"]:
        if row["source_origin"] is not None:
            row["source_heavy_pdb_serial"] = serials[(row["chain"], row["position"], row["atom"])]
    result["coordinate_origin_join"] = dict(
        complete_source_group_count=len({key[:2] for key in serials}),
        complete_heavy_count=len(serials),
        source_heavy_atoms=len(serials),
        full_protein_heavy_anchors=anchors,
        native_nonhydrogen_atoms=native_heavy,
        native_nonhydrogen_coordinate_cells=cells,
        common_translation_intervals_angstrom=tuple(tuple(str(value) for value in interval) for interval in intervals),
        restart_serialization_half_unit_angstrom=str(_ORIGIN_HALF_UNIT),
        claim_scope="PRODUCER_COORDINATE_ORIGIN_JOIN_NOT_INDEPENDENT_ASSESSMENT_OR_CHEMICAL_VALIDATION",
    )
    return result
