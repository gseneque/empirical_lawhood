# SPDX-License-Identifier: MPL-2.0
"""Independent literal Amber→native parameter controls; no native engine."""
from copy import deepcopy
from decimal import Decimal as D
from fractions import Fraction
import math

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.amber_mm_assignment import assess_amber_force_assignment
from tests.test_rubisco_preparation_integrity import amber_text, topology


def selected(*, zero_lj=False):
    raw = topology()
    raw['CHARGE'] = list(map(D, ('9.11115', '-9.11115', '18.2223', '-18.2223')))
    raw['BOND_FORCE_CONSTANT'] = [D(100)]
    raw['BOND_EQUIL_VALUE'] = [D('1.1')]
    raw['ANGLE_EQUIL_VALUE'] = [D('1.5')]
    # Source sign explicitly selects a proper active 1–4 pair, atoms 0 and 3.
    raw['DIHEDRALS_WITHOUT_HYDROGEN'] = [0, 3, 6, 9, 1]
    raw['HBOND_ACOEF'] = raw['HBOND_BCOEF'] = raw['HBCUT'] = []
    sigma = math.sqrt(2)/10
    sigma2, epsilon2 = sigma, 4.184
    exception_sigma, exception_epsilon = sigma, 1.046
    if zero_lj:
        raw['LENNARD_JONES_ACOEF'] = list(map(D, (64, 0, 0)))
        raw['LENNARD_JONES_BCOEF'] = list(map(D, (8, 0, 0)))
        sigma2, epsilon2 = .1*2**(-1/6), 0.
        exception_sigma, exception_epsilon = 2**(-1/6), 0.
    snapshot = {
        'force_roster': ['NonbondedForce', 'HarmonicBondForce', 'HarmonicAngleForce', 'PeriodicTorsionForce'],
        'particles': [( .5, sigma, 1.046), (-.5, sigma2, epsilon2),
                      (1., sigma, 1.046), (-1., sigma2, epsilon2)],
        'exceptions': [(0, 1, 0., .1, 0.), (1, 2, 0., .1, 0.), (2, 3, 0., .1, 0.),
                       (0, 3, float(Fraction(-5, 12)), exception_sigma, exception_epsilon)],
        # These expected numbers are independently prescribed unit conversions:
        # Amber100 kcal/mol/A² = 1/2 *83680 kJ/mol/nm²; 66*2*4.184=552.288.
        'bonds': [(0, 1, .11, 83680.), (2, 3, .11, 83680.)],
        'angles': [(0, 1, 2, 1.5, 552.288)],
        'torsions': [(0, 1, 2, 3, 2, 0., -7.1128)],
    }
    return raw, snapshot, [12., 14., 12., 1.]


@pytest.mark.numerical(oracle='Four-atom literal source: +/-0.5 and +/-1e charges; 83680 bond coefficient,552.288 angle,-7.1128 torsion; four complete exceptions including exact -5/12e² and1.046kJ/mol scaled1–4.')
@pytest.mark.parametrize('zero_lj', (False, True))
def test_complete_assignment_matches_independent_unit_and_exception_oracle(zero_lj):
    raw, snapshot, masses = selected(zero_lj=zero_lj)
    result = assess_amber_force_assignment(amber_text(raw).encode(), snapshot, masses)
    assert result['status'] == 'CORRESPONDENCE_SATISFIED'
    assert (result['physical_atoms'], result['lj_ordered_type_pairs'], result['exceptions']) == (4, 4, 4)
    assert (result['ordinary_pairs'], result['excluded_non14_pairs'], result['active14_pairs']) == (2, 3, 1)
    assert result['physical_accuracy_admission'] == 'UNEVALUABLE'


@pytest.mark.parametrize('defect', ('mass', 'charge', 'bond-factor-two', 'angle-units', 'torsion-sign',
    'exception-scaling', 'missing-exclusion', 'missing-term', 'unsupported-force', 'offdiagonal-lj', 'zero-lj-substitution'))
def test_finite_assignment_and_population_defects_fail_closed(defect):
    raw, snapshot, masses = selected()
    snapshot = deepcopy(snapshot)
    if defect == 'mass': masses[0] = 13.
    elif defect == 'charge': snapshot['particles'][0] = (.6, *snapshot['particles'][0][1:])
    elif defect == 'bond-factor-two': snapshot['bonds'][0] = (0, 1, .11, 41840.)
    elif defect == 'angle-units': snapshot['angles'][0] = (0, 1, 2, 1.5, 66.)
    elif defect == 'torsion-sign': snapshot['torsions'][0] = (0, 1, 2, 3, 2, 0., 7.1128)
    elif defect == 'exception-scaling': snapshot['exceptions'][-1] = (0, 3, -.5, math.sqrt(2)/10, 1.046)
    elif defect == 'missing-exclusion': snapshot['exceptions'].pop(0)
    elif defect == 'missing-term': snapshot['bonds'].pop()
    elif defect == 'unsupported-force': snapshot['force_roster'].append('CustomBondForce')
    elif defect == 'offdiagonal-lj': raw['LENNARD_JONES_ACOEF'][1] = D(129)
    elif defect == 'zero-lj-substitution': snapshot['particles'][0] = (.5, math.sqrt(2)/10, 0.)
    with pytest.raises(ValueError):
        assess_amber_force_assignment(amber_text(raw).encode(), snapshot, masses)
