# SPDX-License-Identifier: MPL-2.0
"""Exposed successor audit/geometry controls, never native model evidence."""
from copy import deepcopy
from decimal import Decimal as D

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import amber_parameters as a
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import physical_preparation_geometry as g
from tests.test_rubisco_physical_preparation_geometry import heavy_pdb, inpcrd, origins, stock
from tests.test_rubisco_preparation_integrity import amber_text, expected_audit, topology


def zero_stock(rows):
    rows['SCEE_SCALE_FACTOR'] = [D('0E-8')]
    rows['SCNB_SCALE_FACTOR'] = [D('0E-8')]
    return rows


def test_supported_full_audit_keeps_actual_zero_values_and_legacy_namespace_refusal():
    sections=zero_stock(topology())
    raw=amber_text(sections)
    audit=expected_audit()
    audit['dihedrals'][0]['coefficients'].update(scee='0.0',scnb='0.0')
    before=deepcopy(audit)
    original=a.assigned_census
    with pytest.raises(ValueError,match='invalid 1-4 scaling'):a.validate_assignment(raw,audit)
    result=a.validate_assignment_supported_inactive14(raw,audit)
    assert result['inactive14_support'].zero_parameter_use_counts==((1,1),)
    assert audit==before and a.assigned_census is original
    with pytest.raises(ValueError,match='invalid 1-4 scaling'):a.validate_assignment(raw,audit)
    audit['dihedrals'][0]['coefficients']['scee']='1.2'
    with pytest.raises(ValueError,match='differs'):a.validate_assignment_supported_inactive14(raw,audit)


def test_successor_geometry_reuses_complete_math_and_declares_new_method():
    raw=amber_text(zero_stock(stock()))
    original=g.assigned_census
    with pytest.raises(ValueError,match='invalid 1-4 scaling'):g.diagnose_geometry(raw,inpcrd(),heavy_pdb(),origins())
    result=g.diagnose_geometry_supported_inactive14(raw,inpcrd(),heavy_pdb(),origins())
    assert result.method==g.SUPPORTED_INACTIVE14_METHOD and result.method!=g.METHOD
    assert result.method.object_version=='1.1.0'
    result.diagnostic.__post_init__()
    assert result.diagnostic.atom_count==4
    assert dict(result.diagnostic.pair_counts)['active14']==0
    assert g.assigned_census is original
    with pytest.raises(ValueError,match='invalid 1-4 scaling'):g.diagnose_geometry(raw,inpcrd(),heavy_pdb(),origins())


def test_active_zero_stays_refused_by_both_successor_consumers():
    rows=zero_stock(stock());rows['DIHEDRALS_WITHOUT_HYDROGEN']=[0,3,6,9,1]
    raw=amber_text(rows)
    audit=expected_audit()
    with pytest.raises(ValueError,match='active nonpositive'):a.validate_assignment_supported_inactive14(raw,audit)
    with pytest.raises(ValueError,match='active nonpositive'):g.diagnose_geometry_supported_inactive14(raw,inpcrd(),heavy_pdb(),origins())


def test_geometry_successor_does_not_weaken_original_origin_or_custody_predicates():
    raw=amber_text(zero_stock(stock()))
    false=origins();false['amber_realization']['atoms'][0]['atom']='WRONG'
    with pytest.raises(ValueError,match='order/residue identity'):g.diagnose_geometry_supported_inactive14(raw,inpcrd(),heavy_pdb(),false)
    rows=zero_stock(stock());rows['EXCLUDED_ATOMS_LIST'].pop()
    with pytest.raises(ValueError,match='count/type'):g.diagnose_geometry_supported_inactive14(amber_text(rows),inpcrd(),heavy_pdb(),origins())
