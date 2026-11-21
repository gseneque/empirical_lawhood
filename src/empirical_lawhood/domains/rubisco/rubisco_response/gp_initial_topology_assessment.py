# SPDX-License-Identifier: MPL-2.0
"""Independent raw Amber checks for the initial four-material construction.

The raw fixed-column reader validates complete force tables. This assessor
then checks original heavy atoms, all eight ligand/KCX graphs and source
charges. It imports no Amber, OpenMM or ParmEd construction implementation.
"""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal as D, ROUND_FLOOR
from hashlib import sha256
from itertools import product
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import assigned_census_supported_inactive14, read_prmtop
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.amber_template import ELEMENTS, RUBP_NAMES, read_amber_template
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import GpAmberModelInput, GpInitialAmberInput
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.amber_construction_admission import INITIAL_ASSESSMENT_FILES, assess_retained_endpoint, library_heavy_correspondence


@dataclass(frozen=True, slots=True)
class GpInitialTopologyAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-initial-topology-assessment"
    VERSION: ClassVar[str] = "2.0.0"
    assessment_id: str
    model: ObjectIdentity
    file_sha256s: tuple[tuple[str, str], ...]
    dry_atom_count: int
    solvated_atom_count: int
    original_heavy_atoms: int
    solvent_waters: int
    sodium_ions: int
    chloride_ions: int
    maximum_heavy_coordinate_error_angstrom: D
    dry_charge_e: D
    solvated_charge_e: D
    dry_term_census: tuple[tuple[str, int], ...]
    solvated_term_census: tuple[tuple[str, int], ...]
    findings: tuple[str, ...]
    construction_disposition: A
    active_ensemble_admission: A = A.UNEVALUABLE
    force_accuracy_admission: A = A.UNEVALUABLE
    rate_admission: A = A.UNEVALUABLE

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.model, ObjectIdentity)
        require_sorted_unique_strings(self.findings, field_name="findings")
        for value in (self.dry_atom_count, self.solvated_atom_count, self.original_heavy_atoms,
                      self.solvent_waters, self.sodium_ions, self.chloride_ions):
            if type(value) is not int or value < 0:
                raise ValueError("initial topology assessment needs complete integer denominators")
        for value in (self.maximum_heavy_coordinate_error_angstrom, self.dry_charge_e, self.solvated_charge_e):
            if type(value) is not D or not value.is_finite():
                raise ValueError("initial topology assessment needs finite exact decimal diagnostics")
        if (self.maximum_heavy_coordinate_error_angstrom < 0
                or self.construction_disposition is not (A.FALSIFIED if self.findings else A.SATISFIED)
                or any(v is not A.UNEVALUABLE for v in (self.active_ensemble_admission,
                    self.force_accuracy_admission, self.rate_admission))):
            raise ValueError("initial topology construction cannot promote physical or rate admission")
        if tuple(k for k, _ in self.file_sha256s) != INITIAL_ASSESSMENT_FILES:
            raise ValueError("initial topology assessment loses its original raw file census")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


def read_initial_coordinates(text, atom_count, *, periodic):
    """Read Amber ASCII coordinates; reject velocities and undeclared rows."""
    lines = text.splitlines()
    if len(lines) < 3 or len(lines[1].split()) != 1 or int(lines[1]) != atom_count:
        raise ValueError("initial Amber coordinates change their exact atom denominator")
    values = []
    for line in lines[2:]:
        if len(line) > 72:
            raise ValueError("initial Amber coordinates change fixed twelve-column format")
        for offset in range(0, len(line), 12):
            token = line[offset:offset+12].strip()
            if token:
                value = D(token)
                if not value.is_finite():
                    raise ValueError("initial Amber coordinates contain nonfinite components")
                values.append(value)
    if len(values) != 3*atom_count + (6 if periodic else 0):
        raise ValueError("initial Amber coordinates contain missing/extra coordinates or velocities")
    box = tuple(values[-6:]) if periodic else ()
    if box and (any(v <= 0 for v in box[:3]) or box[3:] != (D(90),)*3):
        raise ValueError("initial Amber topology requires its declared orthorhombic periodic cell")
    return tuple(tuple(values[i:i+3]) for i in range(0, 3*atom_count, 3)), box


def _residues(census):
    starts = tuple(i-1 for i in census["residue_starts"])
    rows = []
    for name, lo, hi in zip(census["residue_names"], starts, (*starts[1:], census["term_census"]["atoms"]), strict=True):
        names = census["atom_names"][lo:hi]
        if len(set(names)) != len(names):
            raise ValueError("initial topology duplicates a named atom within one residue")
        rows.append((name,dict(zip(names,range(lo,hi),strict=True))))
    return tuple(rows)


def solvent_last_residues(original):
    """Declare Amber's stable solute/solvent partition, retaining source keys.

    saveAmberParm places water residues after all solutes. The named atom,
    element and coordinate checks must still verify every resulting join;
    residue position alone never establishes correspondence.
    """
    return {key:value for water in (False,True) for key,value in original.items()
        if (key[2] in {"HOH","WAT"}) is water}


def stereocentre_volume(positions, names):
    """Signed four-substituent volume in decreasing keto-graph CIP order."""
    first,second,third,last = (positions[name] for name in names)
    a,b,c = (tuple(v-o for v,o in zip(point,last,strict=True)) for point in (first,second,third))
    return a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])


def keto_stereocentre_preserved(before, after, names, minimum_volume):
    """Retain the selected R keto centre, rejecting inversion and near-planarity.

    The determinant uses all four named substituents in the source's CIP
    order; it is six times oriented tetrahedral volume, in Angstrom cubed.
    """
    if type(minimum_volume) is not D or not minimum_volume.is_finite() or minimum_volume <= 0:
        raise ValueError("initial stereochemistry requires its explicit positive degeneracy floor")
    first = stereocentre_volume(before, names)
    final = stereocentre_volume(after, names)
    return first < 0 and final < 0 and min(abs(first), abs(final)) >= minimum_volume


@dataclass(frozen=True, slots=True)
class SolvationAtomCorrespondence:
    """Exact original named atoms joined across Amber's solvent reordering."""
    original_to_solvated_atoms: tuple[int, ...]
    original_to_solvated_residues: tuple[int, ...]
    translation_angstrom: tuple[D, D, D]
    maximum_coordinate_residual_angstrom: D


def solvation_atom_correspondence(dry, solvated, dry_coordinates, solvated_coordinates):
    """Retain every original atom, including every complete crystal water.

    Amber places added ions before solvent and can remove waters while adding
    them. Native indices therefore do not establish original-atom identity.
    Solutes retain their complete named residue order. Every original water
    must have one unique match of all three named coordinates under the same
    global translation. Missing, moved or ambiguous waters refuse.
    """
    original, final = _residues(dry), _residues(solvated)
    if (len(dry_coordinates) != dry['term_census']['atoms']
            or len(solvated_coordinates) != solvated['term_census']['atoms']):
        raise ValueError('solvation correspondence changes the full coordinate denominator')
    original_solutes = [(r, name, atoms) for r, (name, atoms) in enumerate(original) if name != 'WAT']
    final_solutes = [(r, name, atoms) for r, (name, atoms) in enumerate(final)
                     if name not in {'WAT', 'Na+', 'Cl-'}]
    if not original_solutes or len(original_solutes) != len(final_solutes):
        raise ValueError('solvation correspondence loses an original solute residue')
    first_name = next(iter(original_solutes[0][2]))
    if first_name not in final_solutes[0][2]:
        raise ValueError('solvation correspondence loses its original named translation anchor')
    shift = tuple(a-b for a, b in zip(solvated_coordinates[final_solutes[0][2][first_name]],
        dry_coordinates[original_solutes[0][2][first_name]], strict=True))
    tolerance, width = D('0.000002'), D('0.00001')
    atom_map, residue_map, used_residues = {}, {}, set()
    maximum = D(0)

    def residue_error(before, after):
        return max(abs(a-b-s) for name in before
            for a, b, s in zip(solvated_coordinates[after[name]], dry_coordinates[before[name]], shift, strict=True))

    def add(original_index, final_index, before, after):
        nonlocal maximum
        if final_index in used_residues:
            raise ValueError('solvation correspondence aliases two original residues')
        if set(before) != set(after):
            raise ValueError('solvation correspondence changes an original named atom population')
        error = residue_error(before, after)
        if error > tolerance:
            raise ValueError('solvation correspondence moves an original atom beyond the global translation')
        maximum = max(maximum, error)
        used_residues.add(final_index)
        residue_map[original_index] = final_index
        atom_map.update((i, after[name]) for name, i in before.items())

    for (before_index, before_name, before), (after_index, after_name, after) in zip(
            original_solutes, final_solutes, strict=True):
        if before_name != after_name:
            raise ValueError('solvation correspondence changes the complete original solute sequence')
        add(before_index, after_index, before, after)

    def key(point):
        return tuple(int((v/width).to_integral_value(rounding=ROUND_FLOOR)) for v in point)

    def require_water(census, atoms):
        if (set(atoms) != {'O', 'H1', 'H2'}
                or tuple(census['atomic_numbers'][atoms[n]] for n in ('O', 'H1', 'H2')) != (8, 1, 1)):
            raise ValueError('solvation correspondence requires each complete original three-site water')

    water_index = {}
    for r, (name, atoms) in enumerate(final):
        if name == 'WAT':
            require_water(solvated, atoms)
            position = tuple(v-s for v, s in zip(solvated_coordinates[atoms['O']], shift, strict=True))
            water_index.setdefault(key(position), []).append((r, atoms))
    offsets = tuple(product((-1, 0, 1), repeat=3))
    for r, (name, atoms) in enumerate(original):
        if name != 'WAT':
            continue
        require_water(dry, atoms)
        center = key(dry_coordinates[atoms['O']])
        candidates = [(index, final_atoms) for offset in offsets
            for index, final_atoms in water_index.get(tuple(a+b for a, b in zip(center, offset, strict=True)), ())
            if residue_error(atoms, final_atoms) <= tolerance]
        if len(candidates) != 1:
            raise ValueError('solvation correspondence loses or ambiguously identifies an original complete water')
        add(r, candidates[0][0], atoms, candidates[0][1])
    if (set(atom_map) != set(range(dry['term_census']['atoms']))
            or len(set(atom_map.values())) != len(atom_map) or set(residue_map) != set(range(len(original)))):
        raise ValueError('solvation correspondence loses its complete one-to-one original atom population')
    return SolvationAtomCorrespondence(tuple(atom_map[i] for i in range(len(atom_map))),
        tuple(residue_map[i] for i in range(len(residue_map))), shift, maximum)


def retained_bonded_signature(sections,census,atom_limit,*,atom_indices=None):
    """Compare assigned forces by coefficients, not mutable parameter indices."""
    selected = tuple(range(atom_limit)) if atom_indices is None else atom_indices
    if len(selected) != atom_limit or len(set(selected)) != atom_limit:
        raise ValueError('bonded comparison changes its complete original atom mapping')
    inverse = {native: original for original, native in enumerate(selected)}
    coefficients = {
        "BONDS":("BOND_FORCE_CONSTANT","BOND_EQUIL_VALUE"),
        "ANGLES":("ANGLE_FORCE_CONSTANT","ANGLE_EQUIL_VALUE"),
        "DIHEDRALS":("DIHEDRAL_FORCE_CONSTANT","DIHEDRAL_PERIODICITY","DIHEDRAL_PHASE","SCEE_SCALE_FACTOR","SCNB_SCALE_FACTOR"),
    }
    result = Counter()
    for name,terms in census["indexed_bonded_terms"].items():
        category = name.split("_")[0]
        for term in terms:
            original = tuple(abs(i)//3 in inverse for i in term[:-1])
            if any(original) and not all(original):
                raise ValueError("solvation adds a covalent term across the original-atom boundary")
            if all(original):
                joined = tuple((-1 if i < 0 else 1)*3*inverse[abs(i)//3] for i in term[:-1])
                result[(name,joined,tuple(sections[key][term[-1]-1] for key in coefficients[category]))] += 1
    return result


def exclusion_signature(census,atom_limit,*,atom_indices=None):
    selected = tuple(range(atom_limit)) if atom_indices is None else atom_indices
    if len(selected) != atom_limit or len(set(selected)) != atom_limit:
        raise ValueError('exclusion comparison changes its complete original atom mapping')
    inverse = {native: original for original, native in enumerate(selected)}
    result,offset = [set() for _ in range(atom_limit)],0
    total = len(census['exclusion_counts'])
    for atom,count in enumerate(census["exclusion_counts"]):
        values = census["exclusions"][offset:offset+count]
        offset += count
        nonzero = tuple(v for v in values if v)
        if (len(set(nonzero)) != len(nonzero) or any(not atom+1 < v <= total for v in nonzero)
                or not nonzero and values != (0,) or nonzero and 0 in values):
            raise ValueError("initial Amber exclusions duplicate or change their upper-triangular atom scope")
        for value in nonzero:
            other = value-1
            if (atom in inverse) != (other in inverse):
                raise ValueError('initial Amber exclusions cross the complete original atom boundary')
            if atom in inverse:
                lo, hi = sorted((inverse[atom], inverse[other]))
                result[lo].add(hi+1)
    return tuple(tuple(sorted(row)) for row in result)


def hydrogen_findings(census, neighbours, coordinates, bond_equilibria):
    """Check each hydrogen's chemical parent, preserving Amber water triangles.

    The H1-H2 term in a complete three-site water is a geometric topology
    edge. It does not add a chemical heavy-atom parent. No other H-H edge,
    missing O-H edge or external water bond receives this exception.
    Distances must match each original assigned bond equilibrium within
    0.15 Angstrom. A universal 1.3 Angstrom ceiling incorrectly excludes
    ordinary cysteine S-H bonds (assigned equilibrium 1.336 Angstrom).
    """
    if not bond_equilibria or any(type(v) is not D or not v.is_finite() or v <= 0
            for v in bond_equilibria):
        raise ValueError("hydrogen geometry requires finite positive original bond equilibria")
    equilibrium_by_pair = {}
    for key in ("BONDS_INC_HYDROGEN", "BONDS_WITHOUT_HYDROGEN"):
        for a, b, index in census["indexed_bonded_terms"][key]:
            if type(index) is not int or not 1 <= index <= len(bond_equilibria):
                raise ValueError("hydrogen geometry loses an assigned bond parameter")
            pair = tuple(sorted((a//3, b//3)))
            value = bond_equilibria[index-1]
            if pair in equilibrium_by_pair and equilibrium_by_pair[pair] != value:
                raise ValueError("hydrogen geometry has conflicting bond equilibria")
            equilibrium_by_pair[pair] = value
    findings = set()
    waters = {}
    for label, atoms in _residues(census):
        if (label == "WAT" and set(atoms) == {"O", "H1", "H2"}
                and tuple(census["atomic_numbers"][atoms[k]] for k in ("O", "H1", "H2")) == (8, 1, 1)):
            members = set(atoms.values())
            if all(neighbours[i] == members-{i} for i in members):
                waters.update((i, atoms["O"]) for i in (atoms["H1"], atoms["H2"]))
    for i, number in enumerate(census["atomic_numbers"]):
        if number != 1:
            continue
        parents = tuple(j for j in neighbours[i] if census["atomic_numbers"][j] != 1)
        if len(parents) != 1 or (len(neighbours[i]) != 1 and waters.get(i) != parents[0]):
            findings.add("hydrogen-covalent-valence")
            continue
        pair = tuple(sorted((i, parents[0])))
        if pair not in equilibrium_by_pair:
            raise ValueError("hydrogen geometry lacks its original assigned parent bond")
        equilibrium = equilibrium_by_pair[pair]
        squared = sum((a-b)**2 for a, b in zip(coordinates[i], coordinates[parents[0]], strict=True))
        if not max(D(0), equilibrium-D("0.15"))**2 <= squared <= (equilibrium+D("0.15"))**2:
            findings.add("hydrogen-bond-length")
    return tuple(sorted(findings))


def assess_initial_topology(source, model, files, *, assessment_id):
    exact(source, GpInitialAmberInput)
    exact(model, GpAmberModelInput)
    if model not in source.models or set(files) != set(INITIAL_ASSESSMENT_FILES):
        raise ValueError("initial topology assessor requires its complete selected model/raw file census")
    if any(type(v) is not bytes or len(v) > source.maximum_model_output_bytes for v in files.values()):
        raise ValueError("initial topology assessor requires bounded original raw bytes")
    sections = {key: read_prmtop(files[key+".prmtop"].decode("ascii")) for key in ("dry", "model")}
    census = {key: assigned_census_supported_inactive14(value) for key, value in sections.items()}
    coordinates, boxes = {}, {}
    for key in census:
        coordinates[key], boxes[key] = read_initial_coordinates(files[key+".inpcrd"].decode("ascii"),
            census[key]["term_census"]["atoms"], periodic=key == "model")
    final_points, endpoint_findings, endpoint = assess_retained_endpoint(source, model, files,
        census["model"]["term_census"]["atoms"], boxes["model"])
    findings, maximum_error = set(endpoint_findings), D(0)
    residues = {key: _residues(value) for key, value in census.items()}
    original = {}
    for chain, position, component, name, element, xyz in library_heavy_correspondence(model, files,
            construction_seed=source.construction_seed, construction_platform=source.construction_platform,
            construction_threads=source.construction_threads):
        original.setdefault((chain, position, component), {})[name] = (element, xyz)
    original = solvent_last_residues(original)
    if len(residues["dry"]) != len(original):
        findings.add("complete-original-residue-denominator")
    elements = {"C":6, "N":7, "O":8, "P":15, "S":16, "MG":12}
    heavy_count = 0
    for index, ((_, _, component), atoms) in enumerate(original.items()):
        if index >= len(residues["dry"]):
            break
        expected_name = {"HIS":"HIE", "HID":"HIE", "HOH":"WAT", "MG":"MG"}.get(component, component)
        name, actual = residues["dry"][index]
        # Amber may use the element's mixed case in its ion residue label.
        if name.upper() != expected_name.upper():
            findings.add("complete-original-residue-sequence")
        heavy = {n:i for n,i in actual.items() if census["dry"]["atomic_numbers"][i] != 1}
        if set(heavy) != set(atoms):
            findings.add("complete-original-heavy-atom-denominator")
        for atom, (element, xyz) in atoms.items():
            if atom not in heavy:
                continue
            i = heavy[atom]
            heavy_count += 1
            if census["dry"]["atomic_numbers"][i] != elements[element.upper()]:
                findings.add("original-heavy-elements")
            maximum_error = max(maximum_error, *(abs(a-b) for a,b in zip(xyz,coordinates["dry"][i],strict=True)))
    if heavy_count != model.assessment.atom_count or maximum_error > D("0.000001"):
        findings.add("original-heavy-coordinate-correspondence")
    # Solvation can translate the whole original molecule; relative geometry,
    # all original hydrogens, residues and force assignments must be preserved.
    dry_count = census["dry"]["term_census"]["atoms"]
    correspondence = None
    try:
        correspondence = solvation_atom_correspondence(census['dry'], census['model'], coordinates['dry'], coordinates['model'])
    except ValueError:
        findings.add('solvation-original-atom-correspondence')
    else:
        selected = correspondence.original_to_solvated_atoms
        from empirical_lawhood.domains.rubisco.rubisco_response.gp_heavy_geometry import heavy_stereochemistry
        final_heavy = tuple((chain, position, component, atom, element,
            final_points[selected[residues["dry"][r][1][atom]]])
            for r, ((chain, position, component), atoms) in enumerate(original.items()) for atom, (element, _) in atoms.items()
            if r < len(residues["dry"]) and atom in residues["dry"][r][1])
        _, stereo_anomalies = heavy_stereochemistry(final_heavy, minimum_volume=source.minimum_stereocentre_volume_angstrom3)
        if stereo_anomalies:
            findings.add("whole-system-protein-stereochemistry")
        for key in ("atom_names", "atom_types", "atomic_numbers", "masses", "charges_scaled"):
            if tuple(census['model'][key][i] for i in selected) != census['dry'][key]:
                findings.add('solvation-original-atom-parameters')
        maximum_error = max(maximum_error, correspondence.maximum_coordinate_residual_angstrom)
        if retained_bonded_signature(sections["dry"],census["dry"],dry_count) != retained_bonded_signature(
                sections["model"],census["model"],dry_count,atom_indices=selected):
            findings.add("solvation-original-bonded-coefficients")
        if exclusion_signature(census["dry"],dry_count) != exclusion_signature(census["model"],dry_count,atom_indices=selected):
            findings.add("solvation-original-exclusions")
        first_types = {}
        for i,name in enumerate(census["dry"]["atom_types"]):
            first_types.setdefault(name,i)
        for first in first_types.values():
            for second in first_types.values():
                pairs = []
                for key in ("dry","model"):
                    indices = (first, second) if key == 'dry' else (selected[first], selected[second])
                    a,b = (sections[key]["ATOM_TYPE_INDEX"][i]-1 for i in indices)
                    index = census[key]["nonbonded_matrix"][a*sections[key]["POINTERS"][1]+b]-1
                    pairs.append((census[key]["lj_a"][index],census[key]["lj_b"][index]))
                if pairs[0] != pairs[1]:
                    findings.add("solvation-original-nonbonded-coefficients")
    dry_edges = set()
    for key in ("BONDS_INC_HYDROGEN", "BONDS_WITHOUT_HYDROGEN"):
        for a,b,_ in census["dry"]["indexed_bonded_terms"][key]:
            edge = tuple(sorted((a//3,b//3)))
            if edge in dry_edges:
                findings.add("duplicate-bond")
            dry_edges.add(edge)
    neighbours = {i:set() for i in range(dry_count)}
    for a,b in dry_edges:
        neighbours[a].add(b); neighbours[b].add(a)
    atom_residues = {atom:r for r,(_,names) in enumerate(residues["dry"]) for atom in names.values()}
    cross_residue = {edge for edge in dry_edges if atom_residues[edge[0]] != atom_residues[edge[1]]}
    expected_peptides = set()
    ordered_original = tuple(original)
    for index,((chain,position,_),(following,next_position,_)) in enumerate(zip(ordered_original,ordered_original[1:])):
        if chain != "Z" and chain == following and next_position == position+1 and index+1 < len(residues["dry"]):
            left,right = residues["dry"][index][1],residues["dry"][index+1][1]
            if "C" not in left or "N" not in right:
                findings.add("protein-peptide-boundary")
            else:
                expected_peptides.add(tuple(sorted((left["C"],right["N"]))))
    if cross_residue != expected_peptides:
        findings.add("complete-protein-peptide-boundaries")
    stock = {s.member_id.removeprefix("source.gp-initial-amber."):s for s in source.parameter_sources}
    templates = {name:read_amber_template(stock[filename],template_id="template.assess-initial."+name.lower())
        for name,filename in (("RUB","rubp.prepi"),("KCX","kcx.prepin"))}
    for name, template in templates.items():
        selected = [atoms for label,atoms in residues["dry"] if label == name]
        if len(selected) != 8:
            findings.add("all-eight-"+name.lower()+"-sites")
        for atoms in selected:
            if set(atoms) != {a.name for a in template.atoms}:
                findings.add("complete-"+name.lower()+"-graph")
                continue
            reverse = {i:n for n,i in atoms.items()}
            edges = {tuple(sorted((reverse[a],reverse[b]))) for a,b in dry_edges if a in reverse and b in reverse}
            if edges != set(template.bonds):
                findings.add("complete-"+name.lower()+"-graph")
            if name == "RUB":
                before_positions = {atom:coordinates["dry"][index] for atom,index in atoms.items()}
                positions = {atom:final_points[correspondence.original_to_solvated_atoms[index]]
                    if correspondence is not None else coordinates["dry"][index] for atom,index in atoms.items()}
                aliases = dict(RUBP_NAMES)
                for _,_,ordered in source.ligand.stereocentres:
                    if not keto_stereocentre_preserved(before_positions, positions, tuple(aliases.get(n,n) for n in ordered),
                            source.minimum_stereocentre_volume_angstrom3):
                        findings.add("rubp-keto-stereochemistry")
            for atom in template.atoms:
                i = atoms[atom.name]
                if (census["dry"]["atomic_numbers"][i] != ELEMENTS[atom.atom_type]
                        or abs(census["dry"]["charges_scaled"][i]/D("18.2223")-atom.partial_charge_e) > D("0.0000001")):
                    findings.add("source-"+name.lower()+"-elements-and-charges")
                external = neighbours[i]-set(reverse)
                if len(external) != (1 if name == "KCX" and atom.name in ("N","C") else 0):
                    findings.add("source-"+name.lower()+"-boundary-bonds")
    if correspondence is not None:
        final_original = tuple(final_points[index] for index in correspondence.original_to_solvated_atoms)
        findings.update(hydrogen_findings(census["dry"], neighbours, final_original, sections["dry"]["BOND_EQUIL_VALUE"]))
    counts = Counter(census["model"]["residue_names"])
    if set(counts) - set(census["dry"]["residue_names"]) - {"Na+","Cl-"}:
        findings.add("undeclared-solvent-residue")
    charges = {key:sum(row["charges_scaled"],D(0))/D("18.2223") for key,row in census.items()}
    if abs(charges["model"]) > D("0.0005"):
        findings.add("neutralized-cell-charge")
    from empirical_lawhood.domains.rubisco.rubisco_response.amber_construction_log import assess_leap_diagnostics
    log_assessment = assess_leap_diagnostics(files["stdout.txt"], files["stderr.txt"],
        complete_endpoint_satisfied=not endpoint_findings, final_charge_balanced=abs(charges["model"]) <= D("0.0005"))
    findings.update(log_assessment["findings"])
    topology_box = tuple(sections["model"].get("BOX_DIMENSIONS",()))
    if len(topology_box) != 4 or any(abs(a-b) > D("0.00001") for a,b in zip(topology_box,(D(90),*boxes["model"][:3]),strict=True)):
        findings.add("topology-coordinate-periodic-box")
    return GpInitialTopologyAssessment(assessment_id,model.identity,
        tuple((name,sha256(raw).hexdigest()) for name,raw in sorted(files.items())),dry_count,
        census["model"]["term_census"]["atoms"],heavy_count,counts["WAT"],counts["Na+"],counts["Cl-"],
        maximum_error,charges["dry"],charges["model"],tuple(sorted(census["dry"]["term_census"].items())),
        tuple(sorted(census["model"]["term_census"].items())),tuple(sorted(findings)),A.FALSIFIED if findings else A.SATISFIED)
