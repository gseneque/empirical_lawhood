# SPDX-License-Identifier: MPL-2.0
"""Exposed raw-scale falsifiers; no prepared model or native backend."""
from copy import deepcopy
from decimal import Decimal as D
import os
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.amber_parameters import (
    Inactive14ScaleSupport,
    assigned_census,
    assigned_census_supported_inactive14,
    read_prmtop,
)
from tests.test_rubisco_preparation_integrity import amber_text, topology


def inactive():
    sections = read_prmtop(amber_text(topology()))
    sections['SCEE_SCALE_FACTOR'] = (D('0E-8'),)
    sections['SCNB_SCALE_FACTOR'] = (D('0E-8'),)
    return sections


def test_inactive_improper_zero_keeps_legacy_refusal_and_all_original_bytes_values():
    sections = inactive()
    before = deepcopy(sections)
    with pytest.raises(ValueError, match='invalid 1-4 scaling'):
        assigned_census(sections)
    result = assigned_census_supported_inactive14(sections)
    assert sections == before
    assert sections['SCEE_SCALE_FACTOR'][0].as_tuple() == D('0E-8').as_tuple()
    assert result['term_census'] == dict(atoms=4, bonds=2, angles=1, dihedrals=1)
    assert result['exclusions'] == (2, 3, 4, 0)
    assert result['inactive14_support'] == Inactive14ScaleSupport('raw-inactive14-support/1.0.0', 1, 1, 0, 1, (1,), ((1, 1),))


def test_supported_positive_original_census_and_force_values_are_unchanged():
    sections = read_prmtop(amber_text(topology()))
    legacy = assigned_census(sections)
    supported = assigned_census_supported_inactive14(sections)
    support = supported.pop('inactive14_support')
    assert supported == legacy
    assert support.zero_parameter_indices == () and support.dihedral_count == 1
    assert supported['indexed_bonded_terms']['DIHEDRALS_WITHOUT_HYDROGEN'] == ((0, 3, -6, -9, 1),)


@pytest.mark.parametrize('term', [(0, 3, 6, 9, 1), (0, 3, -6, 9, 1), (0, 3, 6, -9, 1)])
def test_zero_is_supported_only_when_both_selected_consumers_skip(term):
    sections = inactive()
    sections['DIHEDRALS_WITHOUT_HYDROGEN'] = term
    if term[2] > 0 and term[3] > 0:
        with pytest.raises(ValueError, match='active nonpositive'):
            assigned_census_supported_inactive14(sections)
    else:
        assert assigned_census_supported_inactive14(sections)['inactive14_support'].inactive14_term_count == 1


@pytest.mark.parametrize('scale', ['SCEE_SCALE_FACTOR', 'SCNB_SCALE_FACTOR'])
@pytest.mark.parametrize('value', [D('-1'), D('NaN'), D('Infinity')])
def test_negative_and_nonfinite_slots_refuse_even_when_unused_or_inactive(scale, value):
    sections = inactive()
    sections[scale] = (value,)
    with pytest.raises(ValueError, match='negative|nonfinite'):
        assigned_census_supported_inactive14(sections)


def test_unused_zero_slot_keeps_its_complete_parameter_denominator():
    sections = inactive()
    p = list(sections['POINTERS']); p[17] = 2; sections['POINTERS'] = tuple(p)
    for key in ('DIHEDRAL_FORCE_CONSTANT', 'DIHEDRAL_PERIODICITY', 'DIHEDRAL_PHASE', 'SCEE_SCALE_FACTOR', 'SCNB_SCALE_FACTOR'):
        sections[key] = sections[key] + sections[key]
    support = assigned_census_supported_inactive14(sections)['inactive14_support']
    assert support.parameter_count == 2
    assert support.zero_parameter_use_counts == ((1, 1), (2, 0))


@pytest.mark.parametrize('term', [(3, 6, 0, 9, 1), (3, 6, 9, 0, 1)])
def test_zero_offset_activation_disagreement_refuses_even_with_positive_factors(term):
    sections = read_prmtop(amber_text(topology()))
    sections['DIHEDRALS_WITHOUT_HYDROGEN'] = term
    with pytest.raises(ValueError, match='activation contracts differ'):
        assigned_census_supported_inactive14(sections)


@pytest.mark.parametrize('mutation', ['bond-index', 'exclusion-count', 'unknown-force', 'bad-sign', 'parameter-index', 'scale-count', 'missing-force'])
def test_all_later_complete_force_and_sign_falsifiers_execute_after_zero_support(mutation):
    sections = inactive()
    if mutation == 'bond-index': sections['BONDS_INC_HYDROGEN'] = (6, 99, 1)
    if mutation == 'exclusion-count': sections['NUMBER_EXCLUDED_ATOMS'] = (1, 1, 1, 0)
    if mutation == 'unknown-force': sections['EXTRA_FORCE_CONSTANT'] = (D(1),)
    if mutation == 'bad-sign': sections['DIHEDRALS_WITHOUT_HYDROGEN'] = (-3, 3, -6, -9, 1)
    if mutation == 'parameter-index': sections['DIHEDRALS_WITHOUT_HYDROGEN'] = (0, 3, -6, -9, 2)
    if mutation == 'scale-count': sections['SCEE_SCALE_FACTOR'] = ()
    if mutation == 'missing-force': del sections['DIHEDRAL_PHASE']
    with pytest.raises(ValueError):
        assigned_census_supported_inactive14(sections)


def test_supported_method_imports_cold_without_numpy_native_or_producer():
    module = 'empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.amber_parameters'
    code = f'''
import importlib.abc
import sys
class Forbidden(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('numpy','parmed','openmm','pdbfixer') or fullname.endswith(('.native','.parameter_audit','.science','.coordinate_plan')):
            raise AssertionError('forbidden import '+fullname)
sys.meta_path.insert(0,Forbidden())
from {module} import assigned_census_supported_inactive14, Inactive14ScaleSupport
assert callable(assigned_census_supported_inactive14)
assert not any(name.split('.')[0] in ('numpy','parmed','openmm','pdbfixer') for name in sys.modules)
'''
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).parents[1] / 'src'), PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
