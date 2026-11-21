# SPDX-License-Identifier: MPL-2.0
"""Whole-system geometry and force diagnostics without native engine contact.

The explicit policy is a conservative construction/continuation screen, not a
MolProbity score, chemical-model validation or an equilibrium assertion. Local
harmonic strain uses the actual selected force constants: z=|q-q0|sqrt(k/RT)
for OpenMM's E=k(q-q0)^2/2 convention. This is an authored screening allocation,
not a claim that all correlated protein coordinates are independent Gaussians.
"""

from dataclasses import dataclass
from decimal import Decimal
import math
from typing import ClassVar

from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal


AMBER_PLANARITY_BASIS = 'AUTHORED_GROSS_GEOMETRY_LIMITS_AND_LOCAL_HARMONIC_STRAIN_V2_AMBER_NOMINAL_PI'


@dataclass(frozen=True, slots=True)
class MolecularGeometryPolicy(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/molecular-geometry-policy'
    minimum_unbonded_distance_angstrom: Decimal = Decimal('1.00')
    minimum_unbonded_heavy_atom_distance_angstrom: Decimal = Decimal('1.00')
    minimum_nuclear_distance_angstrom: Decimal = Decimal('0.60')
    maximum_bond_deviation_angstrom: Decimal = Decimal('0.20')
    maximum_angle_deviation_degrees: Decimal = Decimal('30')
    maximum_planar_improper_distance_angstrom: Decimal = Decimal('0.10')
    maximum_harmonic_standard_deviations: Decimal = Decimal('6')
    reference_temperature_kelvin: Decimal = Decimal('298.15')
    maximum_contact_candidates: int = 1000000
    reactive_hydrogen_bond_pairs: tuple[tuple[int, int], ...] = ()
    basis: str = 'AUTHORED_GROSS_GEOMETRY_LIMITS_AND_LOCAL_HARMONIC_STRAIN_V1_NOT_MOLPROBITY'

    def __post_init__(self):
        for name in ('minimum_unbonded_distance_angstrom', 'minimum_unbonded_heavy_atom_distance_angstrom',
                     'minimum_nuclear_distance_angstrom', 'maximum_bond_deviation_angstrom',
                     'maximum_angle_deviation_degrees', 'maximum_planar_improper_distance_angstrom',
                     'maximum_harmonic_standard_deviations',
                     'reference_temperature_kelvin'):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if not value:
                raise ValueError('whole-molecule quality requires positive authored limits')
        if (self.maximum_angle_deviation_degrees >= 180
                or type(self.maximum_contact_candidates) is not int or self.maximum_contact_candidates <= 0
                or type(self.basis) is not str or not self.basis.strip()):
            raise ValueError('whole-molecule quality has no finite geometry interpretation')
        pairs = self.reactive_hydrogen_bond_pairs
        if (type(pairs) is not tuple or any(type(pair) is not tuple or len(pair) != 2
                or any(type(i) is not int or i < 0 for i in pair) or pair[0] >= pair[1] for pair in pairs)
                or pairs != tuple(sorted(set(pairs)))):
            raise ValueError('reactive hydrogen bonds require prospectively selected distinct canonical atom pairs')


@dataclass(frozen=True, slots=True)
class GeometryTerms:
    """Native-order elements and OpenMM-convention coefficient tuples.

    Bonds: i,j,r0_A,k_kJ/mol/nm^2; angles: i,j,k,theta0_rad,k_kJ/mol/rad^2;
    torsions: i,j,k,l,n,phase_rad,k_kJ/mol. Every term is retained, including
    zero-strength terms; selected wholly-QM terms may be separately exempted.
    """
    atomic_numbers: tuple[int, ...]
    bonds: tuple[tuple, ...]
    angles: tuple[tuple, ...]
    torsions: tuple[tuple, ...]
    improper_torsion_indices: tuple[int, ...] = ()

    def __post_init__(self):
        count = len(self.atomic_numbers)
        if (not count or type(self.atomic_numbers) is not tuple
                or any(type(z) is not int or not 1 <= z <= 118 for z in self.atomic_numbers)):
            raise ValueError('geometry requires complete physical atomic numbers')
        for rows, arity in ((self.bonds, 2), (self.angles, 3), (self.torsions, 4)):
            if type(rows) is not tuple:
                raise ValueError('geometry terms must be immutable complete tuples')
            for row in rows:
                if (type(row) is not tuple or len(row) != arity + (3 if arity == 4 else 2)
                        or any(type(i) is not int or not 0 <= i < count for i in row[:arity])
                        or len(set(row[:arity])) != arity
                        or any(type(x) not in (int, float) or not math.isfinite(x) for x in row[arity:])):
                    raise ValueError('geometry has incomplete, nonfinite or invalid bonded operands')
                if arity != 4 and row[-1] < 0 or arity == 2 and row[-2] <= 0:
                    raise ValueError('geometry has invalid equilibrium or force coefficients')
                if arity == 3 and not 0 <= row[-2] <= math.pi:
                    raise ValueError('geometry angle equilibrium is outside radians domain')
                if arity == 4 and (type(row[4]) is not int or row[4] <= 0):
                    raise ValueError('geometry torsion requires a positive integer periodicity')
        if (type(self.improper_torsion_indices) is not tuple
                or len(set(self.improper_torsion_indices)) != len(self.improper_torsion_indices)
                or any(type(i) is not int or not 0 <= i < len(self.torsions) for i in self.improper_torsion_indices)):
            raise ValueError('geometry improper indices change the original torsion census')


def geometry_terms_from_amber(raw_topology):
    """Read every source term independently, with explicit Amber unit conversion."""
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import (
        assigned_census_supported_inactive14, read_prmtop,
    )
    if type(raw_topology) is not bytes:
        raise TypeError('whole-molecule geometry requires original raw Amber bytes')
    sections = read_prmtop(raw_topology.decode('ascii'))
    census = assigned_census_supported_inactive14(sections)
    bonds, angles, torsions, improper_indices = [], [], [], []
    for name, rows in census['indexed_bonded_terms'].items():
        for row in rows:
            indices, parameter = tuple(abs(i)//3 for i in row[:-1]), row[-1]-1
            if name.startswith('BONDS'):
                bonds.append((*indices, float(sections['BOND_EQUIL_VALUE'][parameter]),
                              2*418.4*float(sections['BOND_FORCE_CONSTANT'][parameter])))
            elif name.startswith('ANGLES'):
                angles.append((*indices, float(sections['ANGLE_EQUIL_VALUE'][parameter]),
                               2*4.184*float(sections['ANGLE_FORCE_CONSTANT'][parameter])))
            else:
                periodicity = float(sections['DIHEDRAL_PERIODICITY'][parameter])
                if not periodicity.is_integer():
                    raise ValueError('raw geometry torsion periodicity is not integral')
                if row[3] < 0:
                    improper_indices.append(len(torsions))
                torsions.append((*indices, int(periodicity), float(sections['DIHEDRAL_PHASE'][parameter]),
                                 4.184*float(sections['DIHEDRAL_FORCE_CONSTANT'][parameter])))
    return GeometryTerms(tuple(census['atomic_numbers']), tuple(bonds), tuple(angles), tuple(torsions), tuple(improper_indices))


def geometry_terms_from_snapshot(atomic_numbers, snapshot):
    """Convert an exposed OpenMM force snapshot; native/source checking is external."""
    return GeometryTerms(tuple(atomic_numbers),
        tuple((*row[:2], float(row[2])*10, float(row[3])) for row in snapshot['bonds']),
        tuple((*row[:3], float(row[3]), float(row[4])) for row in snapshot['angles']),
        tuple((*row[:4], row[4], float(row[5]), float(row[6])) for row in snapshot['torsions']))


def bound_geometry_terms(representation, raw_topology):
    """Bind geometry operands to the original complete source, elements and bonds."""
    from hashlib import sha256
    if sha256(raw_topology).hexdigest() != representation.raw_topology.object_fingerprint:
        raise ValueError('whole-molecule quality substitutes the original topology')
    terms = geometry_terms_from_amber(raw_topology)
    if (terms.atomic_numbers != tuple(a.atomic_number for a in representation.atoms)
            or {tuple(sorted(row[:2])) for row in terms.bonds}
            != {(b.first, b.second) for b in representation.bonds}):
        raise ValueError('whole-molecule quality substitutes the full source atom/bond census')
    return terms


def _planar_improper(periodicity, phase, force, basis):
    if periodicity != 2 or force == 0:
        return False
    # AmberTools also writes 180 degrees as 3.141594 radians. Only the
    # classification uses this representation. Energy uses the original phase.
    representations = (math.pi, 3.141594) if basis == AMBER_PLANARITY_BASIS else (math.pi,)
    return any(abs(math.remainder(phase - (pi if force > 0 else 0.), 2*pi)) < 1e-7
               for pi in representations)


def fixed_bond_feasibility(coordinates_angstrom, terms, mobile_indices, policy):
    """Enumerate violations that a fixed-coordinate dry-parent repair cannot change."""
    import numpy as np
    xyz = np.asarray(coordinates_angstrom, dtype=float)
    if (type(terms) is not GeometryTerms or type(policy) is not MolecularGeometryPolicy
            or xyz.shape != (len(terms.atomic_numbers), 3) or not np.isfinite(xyz).all()):
        raise ValueError('fixed-bond feasibility requires a complete finite selected dry topology and coordinates')
    mobile = frozenset(mobile_indices)
    if len(mobile) != len(mobile_indices) or any(type(i) is not int or not 0 <= i < len(xyz) for i in mobile):
        raise ValueError('fixed-bond feasibility changes the selected atom census')
    rt = .00831446261815324 * float(policy.reference_temperature_kelvin)
    count, failures = 0, []
    for i, j, r0, k in terms.bonds:
        if i in mobile or j in mobile:
            continue
        count += 1
        distance = float(np.linalg.norm(xyz[i] - xyz[j]))
        deviation = abs(distance - r0)
        z = deviation / 10 * math.sqrt(k / rt)
        absolute_failure = deviation > float(policy.maximum_bond_deviation_angstrom)
        strain_failure = z > float(policy.maximum_harmonic_standard_deviations)
        if absolute_failure or strain_failure:
            failures.append(dict(atoms=[i, j], distance_angstrom=distance, equilibrium_angstrom=r0,
                deviation_angstrom=deviation, harmonic_z=z,
                absolute_failure=absolute_failure, strain_failure=strain_failure))
    return dict(fixed_bonds=count, violations=failures,
                disposition='INFEASIBLE_UNDER_SELECTED_FIXED_COORDINATES' if failures else 'FIXED_BOND_SCREEN_PASSED')


def assess_molecular_geometry(coordinates_angstrom, terms, *, policy, cell_angstrom=None, exempt_bonded_atoms=()):
    """Inspect every atom and bonded term, with bounded diagnostic detail.

    Fully-QM bonded terms are counted as exempt because a reactive QM graph
    need not retain its original MM equilibrium. Mixed QM/MM and all-MM terms
    remain tested. The all-atom gross contact screen has no QM exemption.
    Prospectively selected reactive H-heavy pairs are treated as covalent for
    contacts only, with the same absolute nuclear floor as source bonds. They
    require exactly one H and two actual QM atoms; no bond is inferred by length.
    """
    import numpy as np
    from scipy.spatial import cKDTree
    if type(terms) is not GeometryTerms or type(policy) is not MolecularGeometryPolicy:
        raise TypeError('geometry requires explicit typed topology and authored policy')
    xyz = np.asarray(coordinates_angstrom, dtype=float)
    if xyz.shape != (len(terms.atomic_numbers), 3) or not np.isfinite(xyz).all():
        raise ValueError('whole-molecule geometry omits finite coordinates or physical atoms')
    exempt = frozenset(exempt_bonded_atoms)
    if (len(exempt) != len(exempt_bonded_atoms)
            or any(type(i) is not int or not 0 <= i < len(xyz) for i in exempt)):
        raise ValueError('geometry exemption changes its explicit selected atom census')
    reactive_bonds = frozenset(policy.reactive_hydrogen_bond_pairs)
    for first, second in reactive_bonds:
        if (second >= len(xyz) or not {first, second} <= exempt
                or sum(terms.atomic_numbers[i] == 1 for i in (first, second)) != 1):
            raise ValueError('reactive hydrogen contact treatment requires exactly one hydrogen and both actual selected QM atoms')
    box = None if cell_angstrom is None else np.asarray(cell_angstrom, dtype=float)
    if box is not None and (box.shape != (3,) or not np.isfinite(box).all() or np.any(box <= 0)):
        raise ValueError('geometry requires a finite positive orthorhombic cell')
    def delta(a, b):
        d = a-b
        return d if box is None else d-box*np.floor(d/box+.5)
    rt = .00831446261815324*float(policy.reference_temperature_kelvin)
    findings, detail = set(), []
    counts = dict(atoms=len(xyz), hydrogens=terms.atomic_numbers.count(1), bonds=len(terms.bonds),
                  angles=len(terms.angles), torsions=len(terms.torsions), impropers=len(terms.improper_torsion_indices),
                  reactive_hydrogen_bonds=len(reactive_bonds),
                  planar_impropers_checked=0, other_impropers=0,
                  exempt_bonds=0, exempt_angles=0, exempt_torsions=0)
    amber_planarity = policy.basis == AMBER_PLANARITY_BASIS
    if amber_planarity:
        counts.update(positive_amplitude_impropers=0, negative_amplitude_impropers=0,
                      zero_amplitude_impropers=0, applicable_planar_impropers=0,
                      exempt_planar_impropers=0, undefined_planar_impropers=0,
                      violating_planar_impropers=0)
    metrics = dict(maximum_bond_deviation_angstrom=0.0, maximum_angle_deviation_degrees=0.0,
                   maximum_bond_harmonic_z=0.0, maximum_angle_harmonic_z=0.0,
                   torsion_energy_kj_mol=0.0, undefined_torsions=0,
                   maximum_planar_improper_distance_angstrom=0.0)
    def note(kind, indices, value):
        findings.add(kind)
        if len(detail) < 64:
            detail.append(dict(finding=kind, atoms=list(indices), value=float(value)))
    bonded = {tuple(sorted(row[:2])) for row in terms.bonds}
    for i, j, r0, k in terms.bonds:
        if {i, j} <= exempt:
            counts['exempt_bonds'] += 1
            continue
        distance = float(np.linalg.norm(delta(xyz[i], xyz[j])))
        deviation = abs(distance-r0)
        z = deviation/10*math.sqrt(k/rt)
        metrics['maximum_bond_deviation_angstrom'] = max(metrics['maximum_bond_deviation_angstrom'], deviation)
        metrics['maximum_bond_harmonic_z'] = max(metrics['maximum_bond_harmonic_z'], z)
        if deviation > float(policy.maximum_bond_deviation_angstrom):
            note('whole-molecule-bond-deviation', (i, j), deviation)
        if z > float(policy.maximum_harmonic_standard_deviations):
            note('whole-molecule-bond-strain', (i, j), z)
    for i, j, k, theta0, force in terms.angles:
        if {i, j, k} <= exempt:
            counts['exempt_angles'] += 1
            continue
        a, b = delta(xyz[i], xyz[j]), delta(xyz[k], xyz[j])
        norm = float(np.linalg.norm(a)*np.linalg.norm(b))
        if norm == 0:
            note('whole-molecule-undefined-angle', (i, j, k), 0)
            continue
        theta = math.acos(float(np.clip(np.dot(a, b)/norm, -1, 1)))
        deviation = abs(theta-theta0)
        z = deviation*math.sqrt(force/rt)
        metrics['maximum_angle_deviation_degrees'] = max(metrics['maximum_angle_deviation_degrees'], math.degrees(deviation))
        metrics['maximum_angle_harmonic_z'] = max(metrics['maximum_angle_harmonic_z'], z)
        if math.degrees(deviation) > float(policy.maximum_angle_deviation_degrees):
            note('whole-molecule-angle-deviation', (i, j, k), math.degrees(deviation))
        if z > float(policy.maximum_harmonic_standard_deviations):
            note('whole-molecule-angle-strain', (i, j, k), z)
    improper_indices = frozenset(terms.improper_torsion_indices)
    for term_index, (i, j, k, l, periodicity, phase, force) in enumerate(terms.torsions):
        improper = term_index in improper_indices
        planar = improper and _planar_improper(periodicity, phase, force, policy.basis)
        if amber_planarity and improper:
            sign = "positive" if force > 0 else "negative" if force < 0 else "zero"
            counts[sign + "_amplitude_impropers"] += 1
            counts['applicable_planar_impropers'] += int(planar)
        if {i, j, k, l} <= exempt:
            counts['exempt_torsions'] += 1
            if amber_planarity and planar:
                counts['exempt_planar_impropers'] += 1
            continue
        a, b, c = delta(xyz[j], xyz[i]), delta(xyz[k], xyz[j]), delta(xyz[l], xyz[k])
        n1, n2 = np.cross(a, b), np.cross(b, c)
        if float(np.linalg.norm(n1)*np.linalg.norm(n2)*np.linalg.norm(b)) <= 1e-20:
            metrics['undefined_torsions'] += 1
            if amber_planarity and planar:
                counts['undefined_planar_impropers'] += 1
            note('whole-molecule-undefined-torsion', (i, j, k, l), 0)
            continue
        phi = math.atan2(float(np.dot(np.cross(n1, n2), b/np.linalg.norm(b))), float(np.dot(n1, n2)))
        metrics['torsion_energy_kj_mol'] += force*(1+math.cos(periodicity*phi-phase))
        if improper:
            # Only an explicitly improper n=2 term with planar minima qualifies:
            # positive amplitude/phase=pi or negative amplitude/phase=0.
            # Proper torsions and intentionally nonplanar impropers cannot use
            # this criterion. Four-point orthogonal-plane residual is symmetric
            # in atom order; its 0.10-A default is an authored gross bound.
            if planar:
                points4 = np.asarray((np.zeros(3), a, a+b, a+b+c))
                centered = points4-points4.mean(axis=0)
                normal = np.linalg.svd(centered, full_matrices=False)[2][-1]
                residual = float(np.max(np.abs(centered@normal)))
                counts['planar_impropers_checked'] += 1
                metrics['maximum_planar_improper_distance_angstrom'] = max(
                    metrics['maximum_planar_improper_distance_angstrom'], residual)
                if residual > float(policy.maximum_planar_improper_distance_angstrom):
                    if amber_planarity:
                        counts['violating_planar_impropers'] += 1
                    note('whole-molecule-planar-improper-deviation', (i, j, k, l), residual)
            else:
                counts['other_impropers'] += 1
    if amber_planarity and counts['planar_impropers_checked'] == 0:
        findings.add('whole-molecule-planar-improper-coverage-empty')
    points = xyz if box is None else xyz % box
    tree = cKDTree(points, boxsize=box)
    examined, bad_pairs, complete = 0, 0, True
    minimum = float(policy.minimum_unbonded_distance_angstrom)
    heavy_minimum = float(policy.minimum_unbonded_heavy_atom_distance_angstrom)
    nuclear_minimum = float(policy.minimum_nuclear_distance_angstrom)
    # Per-atom streaming avoids constructing an unbounded NxN pair array for a
    # corrupt coincident structure. Capacity exhaustion refuses admission.
    for i, point in enumerate(points):
        neighbours = tree.query_ball_point(point, max(minimum, heavy_minimum, nuclear_minimum))
        for j in neighbours:
            if j <= i:
                continue
            examined += 1
            if examined > policy.maximum_contact_candidates:
                complete = False
                break
            distance = float(np.linalg.norm(delta(xyz[i], xyz[j])))
            threshold = nuclear_minimum
            if (i, j) not in bonded and (i, j) not in reactive_bonds:
                threshold = max(threshold, heavy_minimum if terms.atomic_numbers[i] > 1 and terms.atomic_numbers[j] > 1 else minimum)
            if distance < threshold:
                bad_pairs += 1
                note('whole-molecule-gross-all-atom-contact', (i, j), distance)
        if not complete:
            findings.add('whole-molecule-contact-census-capacity-exceeded')
            break
    if any(not math.isfinite(value) for value in metrics.values()):
        raise ValueError('whole-molecule geometry calculation produced nonfinite diagnostics')
    return dict(schema='el.rubisco.whole-molecule-geometry.v1', disposition='REJECTED' if findings else 'SCREEN_PASSED',
        findings=sorted(findings), counts=counts, metrics=metrics, diagnostics=detail,
        gross_contact_pairs=bad_pairs, contact_candidates=examined, contact_census_complete=complete,
        policy=policy.to_document(), wholly_qm_bonded_atoms=sorted(exempt),
        interpretation='GROSS_GEOMETRY_AND_LOCAL_STRAIN_SCREEN_NOT_MOLPROBITY_CHEMICAL_OR_ENSEMBLE_ADMISSION')


def gradient_statistics(gradient, *, unit, bohr_angstrom=None, hartree_kj_mol=None):
    """Report distinct component and per-atom norms; never infer convergence."""
    import numpy as np
    values = np.asarray(gradient, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3 or not len(values) or not np.isfinite(values).all():
        raise ValueError('force statistics require a complete finite atom-by-Cartesian array')
    if unit == 'kJ/mol/nm':
        if bohr_angstrom is not None or hartree_kj_mol is not None:
            raise ValueError('already converted force cannot carry another unit conversion')
        converted = values
    elif unit == 'Eh/PySCF-Bohr-0.52917721092-A':
        if (bohr_angstrom != .52917721092 or type(hartree_kj_mol) not in (float, int)
                or not math.isfinite(hartree_kj_mol) or hartree_kj_mol <= 0):
            raise ValueError('force conversion requires the selected exact Bohr and positive Hartree convention')
        converted = values*(hartree_kj_mol*10/bohr_angstrom)
    else:
        raise ValueError('force statistics refuse an unspecified or incompatible physical unit')
    if not np.isfinite(converted).all():
        raise ValueError('force conversion overflowed')
    scale = float(np.max(np.abs(converted)))
    scaled = converted if scale == 0 else converted/scale
    component_sq = math.fsum(float(x)*float(x) for x in scaled.flat)
    atoms = np.linalg.norm(scaled, axis=1)*scale
    component_rms, atom_rms = scale*math.sqrt(component_sq/values.size), scale*math.sqrt(component_sq/len(values))
    if not np.isfinite(atoms).all() or not math.isfinite(atom_rms):
        raise ValueError('force statistics exceed the finite selected numeric range')
    return dict(unit='kJ/mol/nm', atom_count=len(values), component_count=int(values.size),
        maximum_cartesian_component=float(np.max(np.abs(converted))),
        rms_cartesian_component=component_rms,
        maximum_atom_vector_norm=float(np.max(atoms)), rms_atom_vector_norm=atom_rms,
        interpretation='DISTINCT_NORMS_NOT_A_CONVERGENCE_OR_PHYSICAL_ACCURACY_CLAIM')
