# SPDX-License-Identifier: MPL-2.0
"""Independent complete raw-Amber/OpenMM force-parameter correspondence.

No engine is imported or invoked. This reader checks an exposed complete force
snapshot before QM masking. It establishes assignment, not physical accuracy.
"""

from collections import defaultdict
from hashlib import sha256
from math import isclose, isfinite, sqrt

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import assigned_census_supported_inactive14, read_prmtop
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.physical_preparation_geometry import interaction_partition


def _number(actual, expected, label):
    if (type(actual) not in (int, float) or not isfinite(actual)
            or not isfinite(expected) or not isclose(actual, expected, rel_tol=1e-12, abs_tol=0.0)):
        raise ValueError("raw Amber/native force parameter differs: "+label)


def _bonded_population(actual, expected, arity, label, count):
    def grouped(rows):
        result = defaultdict(list)
        for row in rows:
            if (type(row) not in (tuple, list) or len(row) != arity+(3 if arity == 4 else 2)
                    or any(type(i) is not int or not 0 <= i < count for i in row[:arity])):
                raise ValueError("raw Amber/native bonded row has an invalid atom denominator: "+label)
            atoms = tuple(row[:arity])
            key = min(atoms, atoms[::-1])
            coefficients = tuple(row[arity:])
            if any(type(v) not in (int, float) or not isfinite(v) for v in coefficients):
                raise ValueError("raw Amber/native bonded row has a nonfinite coefficient: "+label)
            if arity == 4 and type(coefficients[0]) is not int:
                raise ValueError("raw Amber/native torsion periodicity must be an integer")
            result[key].append(coefficients)
        return result
    left, right = grouped(actual), grouped(expected)
    if set(left) != set(right) or any(len(left[key]) != len(right[key]) for key in right):
        raise ValueError("raw Amber/native complete bonded population differs: "+label)
    for key in right:
        for row, selected in zip(sorted(left[key]), sorted(right[key]), strict=True):
            for actual_value, expected_value in zip(row, selected, strict=True):
                _number(actual_value, expected_value, label)


def assess_amber_force_assignment(raw_topology, snapshot, masses):
    """Compare every mass, charge, bonded term, LJ type pair and exception.

    Raw decimal table rounding permits a relative 1e-6 discrepancy when the
    complete printed LJ pair table is represented by Lorentz--Berthelot mixing,
    matching the selected OpenMM parser's source convention. All native scalar
    assignments use 1e-12 relative arithmetic tolerance and exact zero checks.
    No nonzero coefficient can be replaced by zero through an absolute floor.
    """
    if type(raw_topology) is not bytes or type(snapshot) is not dict:
        raise ValueError("MM assignment requires complete original raw bytes and a force snapshot")
    sections = read_prmtop(raw_topology.decode("ascii"))
    census = assigned_census_supported_inactive14(sections)
    count, ntype = census["term_census"]["atoms"], sections["POINTERS"][1]
    required = {"particles", "exceptions", "bonds", "angles", "torsions", "force_roster"}
    if set(snapshot) != required:
        raise ValueError("MM assignment changes the complete selected force snapshot")
    roster = tuple(snapshot["force_roster"])
    force_types = {"NonbondedForce", "HarmonicBondForce", "HarmonicAngleForce", "PeriodicTorsionForce"}
    if (set(roster)-force_types-{"CMMotionRemover"} or not force_types.issubset(roster)
            or len(roster) != len(set(roster))):
        raise ValueError("MM assignment changes the complete standard Amber force roster")
    if len(masses) != count or len(snapshot["particles"]) != count:
        raise ValueError("MM assignment omits complete physical masses or nonbonded particles")
    for actual, expected in zip(masses, census["masses"], strict=True):
        _number(actual, float(expected), "natural mass")
    types = tuple(i-1 for i in sections["ATOM_TYPE_INDEX"])
    def source_pair(first, second):
        slot = census["nonbonded_matrix"][first*ntype+second]-1
        return float(census["lj_a"][slot]), float(census["lj_b"][slot])
    parameters = []
    for index in range(ntype):
        a, b = source_pair(index, index)
        if not a or not b:
            if a or b:
                raise ValueError("MM assignment cannot discard a nonzero one-sided LJ coefficient")
            # Selected parser's zero-interaction radius is 0.5 Angstrom.
            sigma, epsilon = .1*2**(-1/6), 0.0
        else:
            sigma, epsilon = (2*a/b)**(1/6)*.1*2**(-1/6), b*b/(4*a)*4.184
        parameters.append((sigma, epsilon))
    charges = tuple(float(q)/18.2223 for q in census["charges_scaled"])
    for i, row in enumerate(snapshot["particles"]):
        if type(row) not in (tuple, list) or len(row) != 3:
            raise ValueError("MM assignment omits a particle charge, sigma or epsilon")
        for actual, expected, label in zip(row, (charges[i], *parameters[types[i]]),
                ("particle charge", "particle sigma", "particle epsilon"), strict=True):
            _number(actual, expected, label)
    maximum_mixing_error = 0.0
    for first in range(ntype):
        for second in range(ntype):
            sigma = (parameters[first][0]+parameters[second][0])/2*10
            epsilon = sqrt(parameters[first][1]*parameters[second][1])/4.184
            a, b = source_pair(first, second)
            for original, mixed in ((a, 4*epsilon*sigma**12), (b, 4*epsilon*sigma**6)):
                if not original:
                    if mixed:
                        raise ValueError("MM assignment creates a nonzero original zero LJ pair")
                else:
                    error = abs(original-mixed)/abs(original)
                    maximum_mixing_error = max(maximum_mixing_error, error)
                    if not isfinite(error) or error > 1e-6:
                        raise ValueError("MM assignment omits an original off-diagonal LJ pair coefficient")
    bonds, angles, torsions = [], [], []
    for key, terms in census["indexed_bonded_terms"].items():
        for row in terms:
            atoms, index = tuple(abs(i)//3 for i in row[:-1]), row[-1]-1
            if key.startswith("BONDS"):
                bonds.append((*atoms, float(sections["BOND_EQUIL_VALUE"][index])*.1,
                    2*float(sections["BOND_FORCE_CONSTANT"][index])*418.4))
            elif key.startswith("ANGLES"):
                angles.append((*atoms, float(sections["ANGLE_EQUIL_VALUE"][index]),
                    2*float(sections["ANGLE_FORCE_CONSTANT"][index])*4.184))
            else:
                periodicity = sections["DIHEDRAL_PERIODICITY"][index]
                if periodicity <= 0 or periodicity != int(periodicity):
                    raise ValueError("MM assignment refuses noninteger or nonpositive raw torsion periodicity")
                torsions.append((*atoms, int(periodicity), float(sections["DIHEDRAL_PHASE"][index]),
                    float(sections["DIHEDRAL_FORCE_CONSTANT"][index])*4.184))
    for label, expected, arity in (("bonds", bonds, 2), ("angles", angles, 3), ("torsions", torsions, 4)):
        _bonded_population(snapshot[label], expected, arity, label, count)
    excluded, active, pair_counts, signed_counts = interaction_partition(sections, census)
    exceptions = {}
    for row in snapshot["exceptions"]:
        if (type(row) not in (tuple, list) or len(row) != 5
                or any(type(i) is not int or not 0 <= i < count for i in row[:2])):
            raise ValueError("MM assignment changes a complete exception row")
        pair = tuple(sorted(row[:2]))
        if pair[0] == pair[1] or pair in exceptions:
            raise ValueError("MM assignment duplicates an exception pair")
        exceptions[pair] = tuple(row[2:])
    if set(exceptions) != excluded|active.keys():
        raise ValueError("MM assignment omits or adds an original exclusion or active 1-4 pair")
    for (first, second), actual in exceptions.items():
        if (first, second) in active:
            scee, scnb = (float(v) for v in active[first, second])
            if scee <= 0 or scnb <= 0:
                raise ValueError("MM assignment has nonpositive active 1-4 scaling")
            a, b = source_pair(types[first], types[second])
            if not a or not b:
                if a or b:
                    raise ValueError("MM assignment cannot discard a one-sided 1-4 LJ coefficient")
                # The selected parser's 1-4 zero branch uses 1 nm for rMin.
                sigma, epsilon = 2**(-1/6), 0.0
            else:
                sigma, epsilon = (2*a/b)**(1/6)*.1*2**(-1/6), b*b/(4*a)*4.184/scnb
            expected = (charges[first]*charges[second]/scee, sigma, epsilon)
        else:
            expected = (0.0, .1, 0.0)
        for value, selected, label in zip(actual, expected, ("exception charge", "exception sigma", "exception epsilon"), strict=True):
            _number(value, selected, label)
    return dict(status="CORRESPONDENCE_SATISFIED", raw_topology_sha256=sha256(raw_topology).hexdigest(),
        physical_atoms=count, natural_masses=count, particles=count,
        bonds=len(bonds), angles=len(angles), torsions=len(torsions),
        lj_types=ntype, lj_ordered_type_pairs=ntype*ntype, exceptions=len(exceptions),
        ordinary_pairs=pair_counts[0], excluded_non14_pairs=pair_counts[1], active14_pairs=pair_counts[2],
        original_signed_row_census=signed_counts, maximum_lj_mixing_relative_error=maximum_mixing_error,
        native_assignment_relative_tolerance=1e-12, printed_lj_mixing_relative_tolerance=1e-6,
        force_roster=roster, engine_invocations=0, physical_accuracy_admission="UNEVALUABLE")
