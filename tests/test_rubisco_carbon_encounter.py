# SPDX-License-Identifier: MPL-2.0
"""Exposed three-atom correspondence controls; no paper coordinate fixture."""

from dataclasses import replace
from decimal import Decimal

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.carbon_encounter import ANCHORS, SOURCE_ANCHORS, SOURCE_GAS, CarbonEncounterGeometry
from empirical_lawhood.domains.rubisco.rubisco_response.oxygen_encounter import fit_gas_encounter, assess_gas_encounter
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity


def _control():
    anchors=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[1.,1.,0.],[.2,.3,1.]])
    gas=np.array([[2.,3.,4.],[1.,3.,4.],[3.,3.,4.]])
    environment=np.vstack((anchors,gas[2]+[10.1,0.,0.]))
    operands=dict(source_anchors=anchors,target_anchors=anchors,source_gas=gas,
        environment=environment,atomic_numbers=(6,6,8,8,12,8),box=(10,10,10))
    r,t,rmsd,residuals,positions,contacts=fit_gas_encounter(**operands)
    identity=ObjectIdentity('exposed.source','empirical-lawhood/testing/exposed-source','1.0.0','0'*64)
    def decimals(values): return tuple(Decimal(str(float(v))) for v in values)
    record=CarbonEncounterGeometry(*(identity,)*6,'0'*64,'1'*64,len(environment),
        tuple(zip(ANCHORS,SOURCE_ANCHORS,range(5),strict=True)),SOURCE_GAS,
        decimals(r.ravel()),decimals(t),decimals(residuals),Decimal(str(rmsd)),
        tuple(decimals(row) for row in positions),contacts,3*len(environment))
    return record,operands


def test_original_direction_and_three_gas_atoms_survive_canonical_read_and_independent_geometry():
    record,operands=_control()
    original=decode_canonical_bytes(record.canonical_bytes(),CarbonEncounterGeometry,maximum_bytes=2**16)
    assert original==record and original.native_source_label=='P'
    result=assess_gas_encounter(observation=(np.asarray(original.rotation,dtype=float).reshape(3,3),
        original.translation_angstrom,original.fit_rmsd_angstrom,original.anchor_residuals_angstrom,
        original.gas_coordinates_angstrom,original.nearest_original_contacts),**operands)
    assert result['inspected_gas_environment_pairs']==18
    assert original.nearest_original_contacts[2][0]==5
    assert original.nearest_original_contacts[2][1]==pytest.approx(Decimal('.1'),abs=Decimal('1e-13'))


@pytest.mark.parametrize('changes',(
    {'native_source_label':'R'}, {'source_gas_indices_1based':(57,64,63)},
    {'inspected_gas_environment_pairs':12}, {'retained_physical_atom_count':5},
))
def test_source_direction_gas_order_and_complete_environment_cannot_be_relabelled(changes):
    record,_=_control()
    with pytest.raises(ValueError):
        replace(record,**changes)
