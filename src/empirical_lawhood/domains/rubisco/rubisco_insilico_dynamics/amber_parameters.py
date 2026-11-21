# SPDX-License-Identifier: MPL-2.0
"""Independent fixed-column Amber parameter reader; never imports ParmEd.

This checks complete raw assignment/interaction/exclusion rows, not chemical
accuracy, a minimized structure, a valid ensemble or biological kinetics.
Unsupported force extensions are refused rather than omitted from a count.
"""

from dataclasses import dataclass
from decimal import Decimal as D
from math import isfinite, pi
import re
from types import FunctionType

FORMAT = re.compile(r"%FORMAT\(\s*(\d+)([aAiIeEfFdD])(\d+)(?:\.(\d+))?\s*\)[ \t]*")
SELECTED_FLAGS = frozenset("TITLE POINTERS ATOM_NAME CHARGE ATOMIC_NUMBER MASS ATOM_TYPE_INDEX NUMBER_EXCLUDED_ATOMS NONBONDED_PARM_INDEX RESIDUE_LABEL RESIDUE_POINTER BOND_FORCE_CONSTANT BOND_EQUIL_VALUE ANGLE_FORCE_CONSTANT ANGLE_EQUIL_VALUE DIHEDRAL_FORCE_CONSTANT DIHEDRAL_PERIODICITY DIHEDRAL_PHASE SCEE_SCALE_FACTOR SCNB_SCALE_FACTOR SOLTY LENNARD_JONES_ACOEF LENNARD_JONES_BCOEF BONDS_INC_HYDROGEN BONDS_WITHOUT_HYDROGEN ANGLES_INC_HYDROGEN ANGLES_WITHOUT_HYDROGEN DIHEDRALS_INC_HYDROGEN DIHEDRALS_WITHOUT_HYDROGEN EXCLUDED_ATOMS_LIST HBOND_ACOEF HBOND_BCOEF HBCUT AMBER_ATOM_TYPE TREE_CHAIN_CLASSIFICATION JOIN_ARRAY IROTAT RADIUS_SET RADII SCREEN IPOL SOLVENT_POINTERS ATOMS_PER_MOLECULE BOX_DIMENSIONS RESIDUE_CHAINID RESIDUE_ICODE RESIDUE_NUMBER FORCE_FIELD_TYPE".split())


def read_prmtop(text):
    if type(text) is not str or not text.startswith("%VERSION"):
        raise ValueError("independent Amber topology has no version header")
    return read_prmtop_lines(iter(text.splitlines()))


def read_prmtop_lines(lines, *, selected_flags=None):
    """Read fixed-column rows once, retaining complete selected populations.

    A selected flag set supports independent atom/residue diagnosis without
    materializing unrelated force tables. Every section control, format and row
    width is checked, and unknown sections are refused in this mode. It does
    not validate or assess the numerical values of unselected force tables.
    The default retains all sections for the existing full assignment assessor.
    """
    wanted = None if selected_flags is None else frozenset(selected_flags)
    if wanted is not None and (not wanted or wanted - SELECTED_FLAGS):
        raise ValueError("independent Amber selected flags are empty/unknown")
    rows = iter(lines)
    first = next(rows, None)
    if type(first) is not str or not first.startswith("%VERSION"):
        raise ValueError("independent Amber topology has no version header")
    sections, seen = {}, set()
    name, values, format_ready = None, [], False
    repeat, kind, width = 0, None, 0
    for original in rows:
        if type(original) is not str:
            raise ValueError("independent Amber rows must retain lexical text")
        line = original.rstrip("\r\n")
        if not line.strip():
            if name is not None and not format_ready:
                raise ValueError("independent Amber unsupported fixed-column format")
            continue
        if line.startswith("%COMMENT"):
            continue
        if line.startswith("%FLAG "):
            if name is not None:
                if not format_ready:
                    raise ValueError("independent Amber unsupported fixed-column format")
                if wanted is None or name in wanted:
                    sections[name] = tuple(values)
            name = line.removeprefix("%FLAG ").strip()
            if not name or name in seen:
                raise ValueError("independent Amber duplicate/empty section")
            if wanted is not None and name not in SELECTED_FLAGS:
                raise ValueError("independent Amber unselected/unknown section")
            seen.add(name)
            values, format_ready = [], False
            continue
        if name is None:
            raise ValueError("independent Amber unexpected section control")
        if not format_ready:
            match = FORMAT.fullmatch(line)
            if match is None:
                raise ValueError("independent Amber unsupported fixed-column format")
            repeat, kind, width = int(match[1]), match[2].upper(), int(match[3])
            if repeat <= 0 or width <= 0:
                raise ValueError("independent Amber empty fixed-column format")
            format_ready = True
            continue
        if line.startswith("%") or len(line) > repeat*width:
            raise ValueError("independent Amber malformed fixed-column row")
        if wanted is None or name in wanted:
            for offset in range(0, len(line), width):
                token = line[offset:offset+width].strip()
                if not token:
                    continue
                try:
                    value = token if kind == "A" else int(token) if kind == "I" else D(token.replace("D", "E").replace("d", "e"))
                except (ValueError, ArithmeticError) as error:
                    raise ValueError("independent Amber malformed numeric field") from error
                if isinstance(value, D) and not value.is_finite():
                    raise ValueError("independent Amber nonfinite parameter")
                values.append(value)
    if name is not None:
        if not format_ready:
            raise ValueError("independent Amber unsupported fixed-column format")
        if wanted is None or name in wanted:
            sections[name] = tuple(values)
    if wanted is not None and seen & wanted != wanted:
        raise ValueError("independent Amber selected raw section missing")
    return sections


def assigned_census(sections):
    """Validate every selected atom, bonded row, LJ index and exclusion slot."""
    def rows(name, count=None, kind=None):
        if name not in sections:
            raise ValueError("independent Amber missing raw section: " + name)
        values = sections[name]
        if count is not None and len(values) != count or kind is not None and any(type(value) is not kind for value in values):
            raise ValueError("independent Amber section count/type changed: " + name)
        return values

    pointers = rows("POINTERS", kind=int)
    if set(sections) - SELECTED_FLAGS:
        raise ValueError("independent Amber contains an unselected/unknown force or metadata section")
    if len(pointers) < 31 or any(value < 0 for value in pointers):
        raise ValueError("independent Amber incomplete pointer denominator")
    natom, ntype, nres = pointers[0], pointers[1], pointers[11]
    if min(natom, ntype, nres) <= 0 or pointers[19] or pointers[20] or pointers[29] or pointers[30]:
        raise ValueError("independent Amber unsupported hydrogen-bond/perturbation/extra-point force")
    if any(name.startswith(("CHARMM_", "AMOEBA_", "CMAP_", "UREY_BRADLEY_")) or name in ("CTITLE", "LENNARD_JONES_CCOEF") for name in sections) or any(sections.get("IPOL", (0,))):
        raise ValueError("independent Amber unsupported additional force class")
    names = rows("ATOM_NAME", natom, str)
    types = rows("AMBER_ATOM_TYPE", natom, str)
    if any(not name for name in names+types):
        raise ValueError("independent Amber untyped atom")
    numbers = rows("ATOMIC_NUMBER", natom, int)
    masses, charges = rows("MASS", natom, D), rows("CHARGE", natom, D)
    if any(number <= 0 for number in numbers) or any(mass <= 0 for mass in masses):
        raise ValueError("independent Amber unknown atomic number/mass")
    atom_types = rows("ATOM_TYPE_INDEX", natom, int)
    if any(not 1 <= value <= ntype for value in atom_types):
        raise ValueError("independent Amber atom type index absent")
    residues = rows("RESIDUE_LABEL", nres, str)
    starts = rows("RESIDUE_POINTER", nres, int)
    if starts[0] != 1 or tuple(sorted(set(starts))) != starts or starts[-1] > natom:
        raise ValueError("independent Amber complete residue partition changed")
    lj_count = ntype*(ntype+1)//2
    a, b = rows("LENNARD_JONES_ACOEF", lj_count, D), rows("LENNARD_JONES_BCOEF", lj_count, D)
    if any(value < 0 for value in a+b):
        raise ValueError("independent Amber negative raw Lennard-Jones coefficient")
    matrix = rows("NONBONDED_PARM_INDEX", ntype*ntype, int)
    if any(not 1 <= value <= lj_count for value in matrix) or any(matrix[i*ntype+j] != matrix[j*ntype+i] for i in range(ntype) for j in range(ntype)):
        raise ValueError("independent Amber nonbonded matrix is incomplete/asymmetric")
    counts = rows("NUMBER_EXCLUDED_ATOMS", natom, int)
    exclusions = rows("EXCLUDED_ATOMS_LIST", pointers[10], int)
    if sum(counts) != len(exclusions) or any(value < 0 for value in counts) or any(not 0 <= value <= natom for value in exclusions):
        raise ValueError("independent Amber full exclusion denominator changed")
    parameter_sets = {
        "bonds": (pointers[15], ("BOND_FORCE_CONSTANT", "BOND_EQUIL_VALUE")),
        "angles": (pointers[16], ("ANGLE_FORCE_CONSTANT", "ANGLE_EQUIL_VALUE")),
        "dihedrals": (pointers[17], ("DIHEDRAL_FORCE_CONSTANT", "DIHEDRAL_PERIODICITY", "DIHEDRAL_PHASE", "SCEE_SCALE_FACTOR", "SCNB_SCALE_FACTOR")),
    }
    for category, (count, keys) in parameter_sets.items():
        if count <= 0:
            raise ValueError("independent Amber bonded parameter class absent: " + category)
        for key in keys:
            rows(key, count, D)
    if any(value <= 0 for key in ("SCEE_SCALE_FACTOR", "SCNB_SCALE_FACTOR") for value in sections[key]):
        raise ValueError("independent Amber invalid 1-4 scaling")
    census = {"atoms":natom}
    indexed = {}
    for category, arity, name, expected in (
        ("bonds",2,"BONDS_INC_HYDROGEN",pointers[2]), ("bonds",2,"BONDS_WITHOUT_HYDROGEN",pointers[3]),
        ("angles",3,"ANGLES_INC_HYDROGEN",pointers[4]), ("angles",3,"ANGLES_WITHOUT_HYDROGEN",pointers[5]),
        ("dihedrals",4,"DIHEDRALS_INC_HYDROGEN",pointers[6]), ("dihedrals",4,"DIHEDRALS_WITHOUT_HYDROGEN",pointers[7]),
    ):
        values = rows(name, expected*(arity+1), int)
        terms = tuple(values[index:index+arity+1] for index in range(0,len(values),arity+1))
        for term in terms:
            if any(abs(value)%3 or not 0 <= abs(value)//3 < natom for value in term[:arity]) or not 1 <= term[-1] <= parameter_sets[category][0]:
                raise ValueError("independent Amber bonded atom/parameter index absent")
            if category != "dihedrals" and any(value < 0 for value in term[:arity]):
                raise ValueError("independent Amber unsupported signed bonded index")
            if category == "dihedrals" and any(value < 0 for value in term[:2]):
                raise ValueError("independent Amber unsupported first/second dihedral sign")
        census[category] = census.get(category,0) + len(terms)
        indexed[name] = terms
    if any(census[name] <= 0 for name in ("bonds","angles","dihedrals")):
        raise ValueError("independent Amber full bonded class denominator empty")
    return {"term_census":census, "atom_names":names, "atom_types":types, "atomic_numbers":numbers,
        "masses":masses, "charges_scaled":charges, "residue_names":residues, "residue_starts":starts,
        "nonbonded_matrix":matrix, "lj_a":a, "lj_b":b, "exclusion_counts":counts, "exclusions":exclusions,
        "indexed_bonded_terms":indexed}


@dataclass(frozen=True, slots=True)
class Inactive14ScaleSupport:
    """Method data for the complete raw signed-term scaling assessment."""

    method_revision: str
    parameter_count: int
    dihedral_count: int
    active14_term_count: int
    inactive14_term_count: int
    zero_parameter_indices: tuple[int, ...]
    zero_parameter_use_counts: tuple[tuple[int, int], ...]


def assigned_census_supported_inactive14(sections):
    """Full raw census supporting zero scales only at inactive parameter slots.

    The selected ParmEd decoder skips negative third offsets or impropers;
    the selected OpenMM reader emits endpoints only for positive third/fourth
    offsets. Both must agree for every original signed term. Negative factors
    always refuse. Active factors must be positive. Complete inactive/unused
    zero slots retain their original values and full use denominators.

    A private zero-only surrogate lets the unchanged legacy census validate
    every other original force table, pointer and signed term. The surrogate
    is never returned, serialized or written into the original sections.
    Original factors are then assessed against all validated signed terms.
    """
    surrogate = dict(sections)
    scales = {}
    for name in ("SCEE_SCALE_FACTOR", "SCNB_SCALE_FACTOR"):
        if name not in sections:
            raise ValueError("independent Amber missing raw section: " + name)
        values = sections[name]
        if any(type(value) is not D or not value.is_finite() for value in values):
            raise ValueError("independent Amber nonfinite/untyped 1-4 scaling")
        if any(value < 0 for value in values):
            raise ValueError("independent Amber negative 1-4 scaling")
        scales[name] = values
        surrogate[name] = tuple(D(1) if value == 0 else value for value in values)
    census = assigned_census(surrogate)
    parameter_count = len(scales["SCEE_SCALE_FACTOR"])
    zero_slots = {index for index in range(parameter_count)
                  if any(values[index] == 0 for values in scales.values())}
    zero_uses = {index: 0 for index in zero_slots}
    active = inactive = 0
    for name in ("DIHEDRALS_INC_HYDROGEN", "DIHEDRALS_WITHOUT_HYDROGEN"):
        for term in census["indexed_bonded_terms"][name]:
            parmed_active = term[2] >= 0 and term[3] >= 0
            openmm_active = term[2] > 0 and term[3] > 0
            if parmed_active != openmm_active:
                raise ValueError("independent Amber selected 1-4 activation contracts differ")
            index = term[-1] - 1
            if index in zero_slots:
                zero_uses[index] += 1
            if parmed_active:
                if any(values[index] <= 0 for values in scales.values()):
                    raise ValueError("independent Amber active nonpositive 1-4 scaling")
                active += 1
            else:
                inactive += 1
    census["inactive14_support"] = Inactive14ScaleSupport(
        "raw-inactive14-support/1.0.0", parameter_count, active + inactive,
        active, inactive, tuple(index + 1 for index in sorted(zero_slots)),
        tuple((index + 1, zero_uses[index]) for index in sorted(zero_slots)))
    return census


def _binary(value):
    result = float(value)
    if not isfinite(result):
        raise ValueError("independent Amber parameter exceeds finite binary64")
    return result


def _matches_number(actual, expected):
    if type(actual) is not str:
        raise ValueError("retained parameter must preserve its numerical text")
    try:
        value = D(actual)
    except ArithmeticError as error:
        raise ValueError("retained parameter has malformed numerical text") from error
    if not value.is_finite() or value != D(repr(_binary(expected))):
        raise ValueError("retained assignment differs from independently read raw Amber parameter")


def validate_assignment(raw_prmtop, audit):
    """Join every audit row to raw Amber, with pinned stock conversion semantics.

    Amber charge scale 18.2223, radians-to-degrees 180/pi, torsion periodicity
    int conversion and the native per-type LJ getter's 1e-10 zero branch come
    from the authenticated selected ParmEd source. All full mixing/exclusion
    tables are compared even where that getter reports zero. Comparisons use
    exact Decimal equality to the selected binary64 repr, not physical error
    tolerances. No producer, ParmEd, native object or solver is called.
    """
    sections = read_prmtop(raw_prmtop)
    census = assigned_census(sections)
    if type(audit) is not dict or audit.get("term_census") != census["term_census"]:
        raise ValueError("raw Amber and retained audit term denominators differ")
    atom_rows = audit.get("atoms")
    if type(atom_rows) is not list or len(atom_rows) != census["term_census"]["atoms"]:
        raise ValueError("retained audit omits complete raw Amber atoms")
    starts = census["residue_starts"]
    residue_index = 0
    ntype = sections["POINTERS"][1]
    residue_numbers = sections.get("RESIDUE_NUMBER", tuple(range(len(starts))))
    residue_chains = sections.get("RESIDUE_CHAINID", ("",)*len(starts))
    if len(residue_numbers) != len(starts) or len(residue_chains) != len(starts):
        raise ValueError("raw Amber optional residue identity denominator changed")
    for index, atom in enumerate(atom_rows):
        while residue_index+1 < len(starts) and index+1 >= starts[residue_index+1]:
            residue_index += 1
        expected = dict(index=index, name=census["atom_names"][index], residue_index=residue_index,
            residue_name=census["residue_names"][residue_index], residue_number=residue_numbers[residue_index],
            chain=residue_chains[residue_index], atomic_number=census["atomic_numbers"][index], atom_type=census["atom_types"][index])
        if type(atom) is not dict or any(type(atom.get(key)) is not type(value) or atom[key] != value for key,value in expected.items()):
            raise ValueError("retained atom identity differs from complete raw Amber rows")
        typ = sections["ATOM_TYPE_INDEX"][index]-1
        slot = census["nonbonded_matrix"][typ*ntype+typ]-1
        a, b = _binary(census["lj_a"][slot]), _binary(census["lj_b"][slot])
        if a < 1e-10 or b < 1e-10:
            radius = depth = 0.0
        else:
            factor = 2*a/b
            radius, depth = pow(factor, 1.0/6.0)*0.5, b/2/factor
        for name, value in dict(charge_electron=_binary(census["charges_scaled"][index])/18.2223,
                mass_dalton=census["masses"][index], rmin_half_angstrom=radius, epsilon_kcal_mol=depth).items():
            _matches_number(atom.get(name), value)
    specs = (
        ("bonds", "BONDS", ("k", "req"), ("BOND_FORCE_CONSTANT", "BOND_EQUIL_VALUE")),
        ("angles", "ANGLES", ("k", "theteq"), ("ANGLE_FORCE_CONSTANT", "ANGLE_EQUIL_VALUE")),
        ("dihedrals", "DIHEDRALS", ("phi_k", "per", "phase", "scee", "scnb"),
            ("DIHEDRAL_FORCE_CONSTANT", "DIHEDRAL_PERIODICITY", "DIHEDRAL_PHASE", "SCEE_SCALE_FACTOR", "SCNB_SCALE_FACTOR")),
    )
    for category, prefix, coefficients, flags in specs:
        raw_terms = census["indexed_bonded_terms"][prefix+"_WITHOUT_HYDROGEN"] + census["indexed_bonded_terms"][prefix+"_INC_HYDROGEN"]
        actual = audit.get(category)
        if type(actual) is not list or len(actual) != len(raw_terms):
            raise ValueError("retained bonded rows omit raw Amber denominator")
        for term, raw in zip(actual, raw_terms, strict=True):
            atoms = [abs(value)//3 for value in raw[:-1]]
            if type(term) is not dict or term.get("atoms") != atoms or any(type(value) is not int for value in term["atoms"]):
                raise ValueError("retained bonded atoms differ from raw Amber indices")
            actual_coefficients = term.get("coefficients")
            if type(actual_coefficients) is not dict or set(actual_coefficients) != set(coefficients):
                raise ValueError("retained bonded coefficient census changed")
            for key, flag in zip(coefficients, flags, strict=True):
                value = _binary(sections[flag][raw[-1]-1])
                if key in ("theteq", "phase"):
                    value *= 180.0/pi
                if key == "per":
                    value = int(value)
                _matches_number(actual_coefficients[key], value)
            if category == "dihedrals" and any(type(term.get(key)) is not bool or term[key] is not value
                    for key,value in dict(ignore_end=raw[2] < 0, improper=raw[3] < 0).items()):
                raise ValueError("retained dihedral sign/1-4 semantics changed")
    tables = audit.get("native_nonbonded_tables")
    expected_flags = ("NONBONDED_PARM_INDEX", "LENNARD_JONES_ACOEF", "LENNARD_JONES_BCOEF", "NUMBER_EXCLUDED_ATOMS", "EXCLUDED_ATOMS_LIST")
    if type(tables) is not dict or set(tables) != set(expected_flags):
        raise ValueError("retained full mixing/exclusion table census changed")
    for key in expected_flags:
        if type(tables[key]) is not list or len(tables[key]) != len(sections[key]):
            raise ValueError("retained full mixing/exclusion denominator changed")
        for actual, expected in zip(tables[key], sections[key], strict=True):
            _matches_number(actual, expected)
    return census


def validate_assignment_supported_inactive14(raw_prmtop, audit):
    """All legacy audit comparisons, with the additive raw-scale method.

    A private function namespace selects the additive complete census. Module
    globals, original raw text and audit rows are never changed. The legacy
    conversion/comparison code and actual zero audit values remain intact.
    """
    namespace = dict(validate_assignment.__globals__)
    namespace["assigned_census"] = assigned_census_supported_inactive14
    selected = FunctionType(validate_assignment.__code__, namespace,
                            "validate_assignment_supported_inactive14")
    return selected(raw_prmtop, audit)
