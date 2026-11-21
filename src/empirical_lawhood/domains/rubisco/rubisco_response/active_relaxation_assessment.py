# SPDX-License-Identifier: MPL-2.0
"""Independent endpoint checks over retained arrays; no force or reconstruction."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import json
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import periodic_geometry_policy
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import verified_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import ActiveRelaxationSettings
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import GRADIENT_UNIT


@dataclass(frozen=True, slots=True)
class ActiveRelaxationAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-relaxation-assessment'
    seed: ObjectIdentity
    settings: ObjectIdentity
    assessor_source: ObjectIdentity
    disposition: str
    findings: tuple[str, ...]
    complete_reference_evaluations: int
    physical_atoms: int
    maximum_gradient_kj_mol_nm: Decimal
    initial_energy_hartree: Decimal
    final_energy_hartree: Decimal
    nearest_water_magnesium_angstrom: Decimal
    stereocentres_checked: int
    state_retained: bool
    equilibrium_population: str = 'UNEVALUABLE'
    force_accuracy: str = 'UNEVALUABLE'
    chemical_state_admission: str = 'UNEVALUABLE'
    rate_admission: str = 'UNEVALUABLE'

    def __post_init__(self):
        for value in (self.seed, self.settings, self.assessor_source):
            exact(value, ObjectIdentity)
        if (type(self.findings) is not tuple or self.findings != tuple(sorted(set(self.findings)))
                or self.disposition != ('FALSIFIED' if self.findings else 'SATISFIED')
                or type(self.state_retained) is not bool
                or self.state_retained != (not any(f in self.findings for f in (
                    'proton-allocation-escaped', 'magnesium-water-state-escaped', 'catalytic-heavy-bond-broken')))
                or any(type(n) is not int or n < 0 for n in (self.complete_reference_evaluations,
                    self.physical_atoms, self.stereocentres_checked))
                or self.complete_reference_evaluations < 2 or self.physical_atoms == 0
                or any(getattr(self, n) != 'UNEVALUABLE' for n in ('equilibrium_population', 'force_accuracy', 'chemical_state_admission', 'rate_admission'))):
            raise ValueError('relaxation assessment changes its complete endpoint findings or scientific scope')
        for finding in self.findings:
            validate_stable_id(finding)
        for name in ('maximum_gradient_kj_mol_nm', 'nearest_water_magnesium_angstrom'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        for name in ('initial_energy_hartree', 'final_energy_hartree'):
            validate_decimal(getattr(self, name), field_name=name)


def read_endpoint_arrays(files, *, atom_count):
    """Require original complete numeric arrays, including the sole energy scalar."""
    import numpy as np
    result = []
    for name, shape in (('initial-coordinates-angstrom.npy', (atom_count, 3)),
            ('final-coordinates-angstrom.npy', (atom_count, 3)),
            ('final-gradient-hartree-per-bohr.npy', (atom_count, 3)), ('final-energy-hartree.npy', ())):
        raw = files[name]
        stream = BytesIO(raw)
        value = np.load(stream, allow_pickle=False)
        if (value.shape != shape or value.dtype != np.dtype('<f8') or not np.isfinite(value).all()
                or stream.tell() != len(raw)):
            raise ValueError('relaxation endpoint loses complete finite original array: '+name)
        result.append(value)
    return tuple(result)


def assess_endpoint_trace(files, *, initial, final, gradient, energy, settings, electronic_energy_tolerance_hartree=0):
    """Join every original evaluation, fresh final force, exact units and operands."""
    import numpy as np
    exact(settings, ActiveRelaxationSettings)
    tolerance = float(electronic_energy_tolerance_hartree)
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError('endpoint energy comparison needs its selected finite electronic tolerance')
    summary = json.loads(files['relaxation-summary.json'])
    rows = [json.loads(line) for line in files['relaxation-evaluations.jsonl'].splitlines()]
    entries = [r for r in rows if r['event'] == 'relaxation-entry']
    returns = [r for r in rows if r['event'] == 'relaxation-return']
    count = len(entries)
    if (count < 2 or any(r['event'] == 'relaxation-error' for r in rows)
            or [r['evaluation'] for r in entries] != list(range(1, count+1))
            or [r['evaluation'] for r in returns] != list(range(1, count+1))
            or [(r['event'], r['evaluation']) for r in rows if r['event'] in ('relaxation-entry', 'relaxation-return')]
                != [(kind, i) for i in range(1, count+1) for kind in ('relaxation-entry', 'relaxation-return')]
            or any((a['coordinate_sha256'], a['phase']) != (b['coordinate_sha256'], b['phase'])
                for a, b in zip(entries, returns, strict=True))
            or any(r['phase'] != 'minimizer' for r in entries[:-1])
            or entries[-1]['phase'] != 'final-endpoint-force'
            or entries[0]['coordinate_sha256'] != sha256(initial.tobytes()).hexdigest()
            or entries[-1]['coordinate_sha256'] != sha256(final.tobytes()).hexdigest()
            or any(r['physical_atoms'] != len(initial) for r in entries)
            or any(r['gradient_unit'] != GRADIENT_UNIT for r in returns)
            or returns[-1]['gradient_sha256'] != sha256(gradient.tobytes()).hexdigest()
            or returns[-1]['energy_hartree'] != float(energy)):
        raise ValueError('relaxation trace changes its complete calls or independently retained final force')
    bohr = .52917721092
    from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import COULOMB_KJ_NM_PER_MOL_E2
    hartree = COULOMB_KJ_NM_PER_MOL_E2/(bohr/10)
    maximum = float(np.max(np.abs(gradient)))*hartree*10/bohr
    if (summary['bohr_angstrom'] != bohr or summary['hartree_kj_mol'] != hartree
            or summary['gradient_unit'] != GRADIENT_UNIT or summary['physical_atom_count'] != len(initial)
            or summary['complete_reference_evaluations'] != count or summary['final_evaluation'] != count
            or summary['optimizer_evaluations'] != count-1
            or summary['maximum_gradient_selection_kj_mol_nm'] != str(settings.maximum_gradient_kj_mol_nm)
            or summary['final_energy_hartree'] != float(energy)
            or summary['maximum_final_gradient_kj_mol_nm'] != maximum
            or summary['initial_energy_kj_mol'] != returns[0]['energy_hartree']*hartree
            or summary['added_restraints'] is not False or summary['molecular_time_seconds'] is not None
            or summary['equilibrium_population'] != 'UNEVALUABLE' or summary['rate_admission'] != 'UNEVALUABLE'):
        raise ValueError('relaxation summary substitutes its original arrays, units or selected limits')
    findings = set()
    if maximum > float(settings.maximum_gradient_kj_mol_nm):
        findings.add('final-force-not-converged')
    if not summary['optimizer_reported_success']:
        findings.add('minimizer-stopped-before-convergence')
    if float(energy)-returns[0]['energy_hartree'] > 2*tolerance:
        findings.add('endpoint-energy-increased')
    return count, maximum, returns[0]['energy_hartree'], findings


def endpoint_geometry(*, representation, site, protocol, seed, original, final, cell, settings):
    """Inspect catalytic preservation and source stereocentres independently.

    Whole-system force-topology geometry is separately required by the reader.
    These legacy preservation predicates alone are not a structure-quality pass.
    """
    import numpy as np
    from scipy.spatial import cKDTree
    box = np.asarray(tuple(map(float, cell.lengths_angstrom)))
    def delta(a, b):
        value = a-b
        return value-box*np.floor(value/box+.5)
    graph = next(g for g in protocol.graphs if g.identity == seed.graph)
    mapping = site.core_atom_indices
    findings, bonds = set(), set()
    for bond in representation.bonds:
        bonds.add((bond.first, bond.second))
    proton_hosts = {}
    for bond in graph.bonds:
        a, b = graph.atoms[bond.first], graph.atoms[bond.second]
        if a.cap or b.cap:
            continue
        first, second = mapping[bond.first], mapping[bond.second]
        distance = np.linalg.norm(delta(final[first], final[second]))
        if a.atomic_number == 1 or b.atomic_number == 1:
            hydrogen, host = (first, second) if a.atomic_number == 1 else (second, first)
            proton_hosts[hydrogen] = host
            if distance > float(settings.maximum_hydrogen_bond_angstrom):
                findings.add('proton-allocation-escaped')
        elif a.atomic_number != 12 and b.atomic_number != 12 and distance > 2.2:
            # A permissive diagnostic for gross loss of a selected core bond;
            # it does not infer bond order or chemical accuracy from distance.
            findings.add('catalytic-heavy-bond-broken')
    heavy = np.asarray([i for i, atom in enumerate(representation.atoms) if atom.atomic_number != 1])
    heavy_points = final[heavy] % box
    tree = cKDTree(heavy_points, boxsize=box)
    for hydrogen, host in proton_hosts.items():
        nearest = int(heavy[tree.query(final[hydrogen] % box)[1]])
        if nearest != host:
            findings.add('proton-allocation-escaped')
    for a, b in tree.query_pairs(float(settings.minimum_heavy_contact_angstrom)):
        if tuple(sorted((int(heavy[a]), int(heavy[b])))) not in bonds:
            findings.add('gross-heavy-atom-contact')
            break
    residues = {r.residue_id:r for r in representation.residues}
    grouped = {}
    for i, atom in enumerate(representation.atoms):
        grouped.setdefault(atom.residue_id, {})[atom.name] = i
    mg = next(mapping[i] for i, atom in enumerate(graph.atoms) if atom.atomic_number == 12)
    water_oxygens = [i for i, atom in enumerate(representation.atoms)
        if residues[atom.residue_id].role == 'WATER' and atom.atomic_number == 8]
    nearest_water = float(np.min(np.linalg.norm(delta(final[water_oxygens], final[mg]), axis=1)))
    selected_water = site.water_atom_indices[site.water_residue_ids.index(site.coordination_water_residue_id)][0]
    selected_water_distance = float(np.linalg.norm(delta(final[selected_water], final[mg])))
    if (seed.water_occupancy == 'OCCUPIED' and selected_water_distance > float(settings.occupied_water_maximum_angstrom)
            or seed.water_occupancy == 'UNOCCUPIED' and nearest_water < float(settings.unoccupied_water_minimum_angstrom)):
        findings.add('magnesium-water-state-escaped')
    centres = []
    for residue in representation.residues:
        names = grouped[residue.residue_id]
        definitions = []
        if residue.role == 'PROTEIN':
            if residue.component != 'GLY':
                definitions.append(('CA', 'N', 'C', 'CB'))
            if residue.component == 'ILE':
                definitions.append(('CB', 'CA', 'CG1', 'CG2'))
            elif residue.component == 'THR':
                definitions.append(('CB', 'CA', 'OG1', 'CG2'))
        elif residue.role == 'LIGAND':
            definitions.append(('C4', 'C3', 'C5', 'O4'))
            focal = residue.residue_id == representation.atoms[next(mapping[i] for i, a in enumerate(graph.atoms)
                if a.label == 'ligand.C3')].residue_id
            if not focal or seed.state_label.startswith('keto-'):
                definitions.append(('C3', 'C2', 'C4', 'O3'))
        for names4 in definitions:
            if any(name not in names for name in names4):
                raise ValueError('relaxation reader finds an incomplete source stereocentre')
            centres.append(tuple(names[n] for n in names4))
    for centre, a, b, c in centres:
        before = np.linalg.det(delta(original[[a, b, c]], original[centre]))
        after = np.linalg.det(delta(final[[a, b, c]], final[centre]))
        if abs(before) < float(settings.minimum_stereocentre_volume_angstrom3):
            findings.add('source-stereocentre-degenerate')
        if abs(after) < float(settings.minimum_stereocentre_volume_angstrom3) or before*after <= 0:
            findings.add('stereocentre-inverted-or-planar')
    return findings, nearest_water, len(centres)


def assess_coupled_relaxation_trace(*, prototype, files, physical_atoms, evaluations):
    """Join nested complete electronic calls to an authenticated minimizer trace."""
    import numpy as np
    native = [json.loads(line) for line in files['native-observations.jsonl'].splitlines()]
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import accelerated_engine
    if accelerated_engine(prototype.engine):
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_backend_evidence import assess_gpu_log
        assess_gpu_log(files['native-observations.jsonl'], engine=prototype.engine,
            expected_evaluations=evaluations, successful=True, state=getattr(prototype.electronic, 'state', None))
    for event in ('entry', 'electronic-return', 'return'):
        if [r['evaluation'] for r in native if r['event'] == event] != list(range(1, evaluations+1)):
            raise ValueError('relaxation endpoint omits an original nested electronic call')
    minimizer = [json.loads(line) for line in files['relaxation-evaluations.jsonl'].splitlines()]
    coupled_returns = [r for r in native if r['event'] == 'return']
    retained_returns = [r for r in minimizer if r['event'] == 'relaxation-return']
    if (any(r['physical_atoms'] != physical_atoms for r in native if r['event'] == 'entry')
            or any(a['energy_hartree'] != b['energy_hartree'] for a, b in zip(coupled_returns, retained_returns, strict=True))):
        raise ValueError('relaxation endpoint changes its nested complete operator return')
    findings = set()
    if (any(r['event'] == 'error' for r in native)
            or any(r['converged'] is not True or not np.isfinite(r['orbital_gradient_norm'])
                or r['orbital_gradient_norm'] >= float(prototype.electronic.orbital_gradient_tolerance)
                for r in native if r['event'] == 'electronic-return')):
        findings.add('electronic-solution-not-converged')
    return findings


def assess_active_endpoint(*, representation, prototype, prepared, site, seed, settings,
                           coordinate_bytes, files, assessor_source):
    """Read one authenticated original endpoint without coordinate construction."""
    original = verified_coordinates(representation, coordinate_bytes)
    initial, final, gradient, energy = read_endpoint_arrays(files, atom_count=len(original))
    if sha256(initial.tobytes()).hexdigest() != seed.expanded_coordinate_sha256:
        raise ValueError('relaxation endpoint substitutes its prepared complete initial array')
    expected_records = (('seed.json', seed), ('site.json', site), ('protocol.json', prepared.protocol), ('settings.json', settings))
    if any(files[name] != record.canonical_bytes() for name, record in expected_records):
        raise ValueError('relaxation endpoint substitutes its original selected state or assessment thresholds')
    bindings = json.loads(files['source-bindings.json'])
    if (bindings['representation'] != representation.identity.to_document()
            or bindings['prototype'] != prototype.identity.to_document()
            or bindings['topology_sha256'] != representation.raw_topology.object_fingerprint
            or bindings['original_coordinate_sha256'] != seed.original_coordinate_sha256
            or bindings['initial_coordinate_sha256'] != seed.expanded_coordinate_sha256
            or bindings['physical_atoms'] != len(original) or bindings['cell'] != prototype.cell.to_document()
            or bindings['state_graph'] != seed.graph.to_document()):
        raise ValueError('relaxation endpoint loses its complete source bindings')
    count, maximum, first_energy, findings = assess_endpoint_trace(files, initial=initial, final=final,
        gradient=gradient, energy=energy, settings=settings,
        electronic_energy_tolerance_hartree=prototype.electronic.energy_tolerance_hartree)
    findings |= assess_coupled_relaxation_trace(prototype=prototype, files=files,
        physical_atoms=len(original), evaluations=count)
    geometry, nearest, stereo_count = endpoint_geometry(representation=representation, site=site,
        protocol=prepared.protocol, seed=seed, original=original, final=final, cell=prototype.cell, settings=settings)
    findings |= geometry
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import bound_geometry_terms, assess_molecular_geometry
    terms = bound_geometry_terms(representation, files['original.prmtop'])
    for coordinates in (initial, final):
        quality = assess_molecular_geometry(coordinates, terms, policy=periodic_geometry_policy(prototype.molecular),
            cell_angstrom=tuple(map(float, prototype.cell.lengths_angstrom)), exempt_bonded_atoms=site.path.qm_atom_indices)
        findings.update(quality['findings'])
    return ActiveRelaxationAssessment(seed.identity, settings.identity, assessor_source,
        'FALSIFIED' if findings else 'SATISFIED', tuple(sorted(findings)), count, len(original),
        Decimal(str(maximum)), Decimal(str(first_energy)), Decimal(str(float(energy))), Decimal(str(nearest)),
        stereo_count, not bool(findings & {'proton-allocation-escaped', 'magnesium-water-state-escaped', 'catalytic-heavy-bond-broken'}))
