# SPDX-License-Identifier: MPL-2.0
"""Original MIT parameter-source controls; no physical qualification evidence."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import gas_amber_stock as gas
from empirical_lawhood.science.records.decoding import decode_canonical_bytes


FIXTURES = Path(__file__).parent/'fixtures/rubisco/amber-templates'


def _stock(name):
    return gas.prepare_gas_amber_stock(gas=name,
        original_prepi_bytes=(FIXTURES/(name.lower()+'.prepi')).read_bytes(),
        original_frcmod_bytes=(FIXTURES/(name.lower()+'.frcmod')).read_bytes(),
        existing_atom_types=('C','K0','c','c3','o','oh','os'))


@pytest.mark.parametrize('name,count,charge', (('CO2',3,'-0.000001'),('O2',2,'0.000000')))
def test_original_charge_tokens_and_full_parameters_survive_roundtrip(name,count,charge):
    stock = _stock(name)
    assert decode_canonical_bytes(stock.canonical_bytes(),gas.GasAmberStock,maximum_bytes=16384) == stock
    read = gas.assess_gas_amber_stock(stock,existing_atom_types=('c','o'))
    assert len(read['atom_charge_tokens']) == count and read['partial_charge_sum_e'] == charge
    assert read['parameter_section_counts']['BOND'] == 1
    assert read['parameter_section_counts']['NONBON'] == (2 if name == 'CO2' else 1)
    assert not read['physical_or_chemical_admission']
    if name == 'O2':
        assert read['original_bond_parameter_rows'] == ('o -o   141.40   1.430',)


@pytest.mark.parametrize('name',('CO2','O2'))
def test_aliases_refuse_existing_host_types_and_source_substitution(name):
    stock = _stock(name)
    with pytest.raises(ValueError,match='collides'):
        gas.prepare_gas_amber_stock(gas=name,original_prepi_bytes=stock.original_prepi.raw_utf8.encode(),
            original_frcmod_bytes=stock.original_frcmod.raw_utf8.encode(),
            existing_atom_types=(stock.aliases[0][1],))
    with pytest.raises(ValueError,match='original source bytes'):
        gas.prepare_gas_amber_stock(gas=name,original_prepi_bytes=stock.original_prepi.raw_utf8.encode()+b'\n',
            original_frcmod_bytes=stock.original_frcmod.raw_utf8.encode(),existing_atom_types=())
    with pytest.raises(ValueError,match='numerical or non-type'):
        replace(stock,scoped_frcmod_utf8=stock.scoped_frcmod_utf8.replace('0.1463','0.1464'))


def test_independent_parameter_assessor_does_not_call_the_aliasing_producer(monkeypatch):
    stock = _stock('O2')
    def forbidden(*args,**kwargs):
        raise AssertionError('aliasing producer entered')
    monkeypatch.setattr(gas,'_scope_text',forbidden)
    assert gas.assess_gas_amber_stock(stock,existing_atom_types=('o',))['new_native_calls'] == 0
    # Bypass the constructor to challenge the independent consumer itself.
    object.__setattr__(stock,'scoped_frcmod_utf8',stock.scoped_frcmod_utf8.replace('1.430','1.431'))
    with pytest.raises(ValueError,match='parameter token'):
        gas.assess_gas_amber_stock(stock,existing_atom_types=('o',))
