# SPDX-License-Identifier: MPL-2.0
"""Disclosed parser controls without original paper coordinate fixtures."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from urllib.parse import quote

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import carbon_source_geometry as carbon
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import SourceMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity


def _synthetic_text():
    rows = ['C -0.0000 1.0000 2.0000']*79+['H 0.0000 1.0000 2.0000']*7
    rows[50] = 'M1 0.0000 1.0000 2.0000'
    return '86\nDisclosed synthetic source-parser control\n'+'\n'.join(rows)+'\n'


def test_native_xyz_tokens_and_full_cap_census_are_preserved():
    atoms = carbon._xyz_atoms(_synthetic_text())
    assert len(atoms) == 86 and atoms[0][1] == '-0.0000' and atoms[50][0] == 'M1'
    for text in (_synthetic_text().replace('86\n','85\n'),
            _synthetic_text()+'H 0.0 1.0 2.0\n',_synthetic_text().replace('1.0000','NaN',1)):
        with pytest.raises(ValueError):
            carbon._xyz_atoms(text)


def test_source_requires_original_archive_and_complete_original_pdb():
    with pytest.raises(ValueError,match='exact original'):
        carbon.prepare_carbon_source_projection(original_archive_bytes=b'not an archive')
    with pytest.raises(ValueError,match='original PDB census'):
        carbon._join_pdb(carbon._xyz_atoms(_synthetic_text()),'')


def test_magnesium_is_an_explicit_successor_correction_not_rewritten_source(monkeypatch):
    raw = _synthetic_text();digest = sha256(raw.encode()).hexdigest()
    # Synthetic pins only exercise the record's semantic boundary, never a
    # scientific source admission or an original paper geometry.
    monkeypatch.setattr(carbon,'PINS',(('P','synthetic','synthetic.pdb',digest,'0'*64),))
    source = SourceMember('source.carbon-state.p',
        carbon.ARCHIVE_URL+'#'+quote(carbon._BASE+'synthetic/P-QM_Zone.xyz'),digest,raw)
    pdb = ObjectIdentity('source.carbon-pdb.p','empirical-lawhood/rubisco-response/carbon-native-pdb-bytes','1.0.0','0'*64)
    state = carbon.CarbonSourceState('P',source,pdb,tuple(range(1,80)),(Decimal(0),)*3,((51,'M1','Mg',7231),))
    assert 'M1' in state.xyz_source.raw_utf8 and state.successor_atoms[50].element == 'Mg'
    assert state.gas_addition_role == 'SEPARATED_CO2_SOURCE'
    with pytest.raises(ValueError,match='element correction'):
        replace(state,element_corrections=())
