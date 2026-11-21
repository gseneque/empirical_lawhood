# SPDX-License-Identifier: MPL-2.0
"""Exposed neutral-gas input and retained numerical endpoint controls."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import json
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import gas_relaxation_native as native
from empirical_lawhood.domains.rubisco.rubisco_response import gas_relaxation_assessment as reader
from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import ActiveRelaxationSettings
from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import expand_state_coordinates, materialize_catalytic_states
from empirical_lawhood.domains.rubisco.rubisco_response.gas_reactive_model import prepare_gas_reactive_candidate
from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_selection import prepare_gas_relaxation_selection
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import prepare_periodic_probe_selection
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from tests.rubisco_active_fixture import molecular_control
from tests.rubisco_response_molecular_fixture import raw_identity
from tests.test_rubisco_active_relaxation import HarmonicOperator
from tests.test_rubisco_gas_reactive_model import _prepared_host, operands


@pytest.fixture(scope='module', params=('CO2', 'O2'))
def gas_input(tmp_path_factory, request):
    host = _prepared_host(tmp_path_factory, 'm1-wt')
    model, site, cell, coordinates, original = host
    protocol = molecular_control('m1-wt')[-1]
    seeds = materialize_catalytic_states(representation=model, site=site, protocol=protocol,
        coordinate_bytes=coordinates, cell=cell)
    seed = next(s for s in seeds if (s.state_label, s.water_occupancy) == ('reactive-enolate-kcxh-hie', 'UNOCCUPIED'))
    values = operands(host, request.param)
    expanded = expand_state_coordinates(seed, coordinates).tobytes()
    raw_array = expanded+values['augmented_coordinate_bytes'][len(coordinates):]
    values['augmentation'] = replace(values['augmentation'], selected_seed=seed.identity,
        expanded_seed_coordinate_sha256=sha256(expanded).hexdigest(),
        augmented_coordinates=raw_identity('source.exposed.gas-relaxation-array', raw_array))
    values['augmented_coordinate_bytes'] = raw_array
    candidate = prepare_gas_reactive_candidate(**values)
    prototype = prepare_periodic_probe_selection(representation=candidate['representation'], path=candidate['path'],
        cell=candidate['cell'], electronic=candidate['electronic_settings'], molecular=original.molecular, engine=original.engine)
    selection = prepare_gas_relaxation_selection(representation=candidate['representation'], prototype=prototype,
        augmentation=values['augmentation'], encoding=candidate['encoding'], convention=candidate['convention'],
        electronic_state=candidate['electronic_selection'], site=site, seed=seed, protocol=protocol,
        settings=ActiveRelaxationSettings('settings.exposed.gas-relaxation'))
    return SimpleNamespace(selection=selection, model=candidate['representation'],
        raw_top=values['augmented_topology_bytes'], raw_xyz=candidate['raw_coordinate_bytes'],
        coordinates=np.frombuffer(candidate['coordinate_bytes'], dtype='<f8').reshape(-1, 3),
        original_model=model, original_seed=seed)


def test_original_gas_selection_keeps_complete_host_and_explicit_triplet(gas_input):
    item = gas_input
    selection = item.selection
    assert decode_canonical_bytes(selection.canonical_bytes(), type(selection), maximum_bytes=8*2**20) == selection
    assert selection.augmentation.original_representation == item.original_model.identity
    assert selection.seed == item.original_seed
    assert selection.prototype.path.qm_atom_indices[-len(selection.prototype.path.gas_atom_indices):] == selection.prototype.path.gas_atom_indices
    assert selection.prototype.path.spin_multiplicity == (3 if selection.prototype.path.gas == 'O2' else 1)
    assert np.array_equal(native.gas_relaxation_coordinates(selection=selection, representation=item.model,
        raw_topology=item.raw_top, raw_coordinates=item.raw_xyz), item.coordinates)


@pytest.mark.parametrize('changed', ('seed', 'protocol', 'encoding', 'gas-indices', 'host-partition', 'source', 'coordinates'))
def test_changed_gas_or_host_operands_refuse_before_native_libraries(gas_input, changed, monkeypatch):
    item, selection = gas_input, gas_input.selection
    monkeypatch.setattr(periodic_qmmm, 'build_periodic_amber_system', lambda **kw: pytest.fail('native construction entered'))
    with pytest.raises(ValueError):
        if changed == 'seed':
            replace(selection, seed=replace(selection.seed, seed_id='seed.exposed.substitution'))
        elif changed == 'protocol':
            replace(selection, protocol=replace(selection.protocol, protocol_id='protocol.exposed.changed'))
        elif changed == 'encoding':
            replace(selection, encoding=replace(selection.encoding, original_coordinates=item.model.raw_coordinates))
        elif changed == 'gas-indices':
            path = selection.prototype.path
            replace(selection, prototype=replace(selection.prototype, path=replace(path, gas_atom_indices=path.gas_atom_indices[:-1])))
        elif changed == 'host-partition':
            path = selection.prototype.path
            move = path.mm_atom_indices[-1]
            replace(selection, prototype=replace(selection.prototype, path=replace(path,
                qm_atom_indices=tuple(sorted((*path.qm_atom_indices, move))), mm_atom_indices=path.mm_atom_indices[:-1])))
        else:
            native.gas_relaxation_coordinates(selection=selection, representation=item.model,
                raw_topology=item.raw_top+(b'\n' if changed == 'source' else b''),
                raw_coordinates=item.raw_xyz+(b'\n' if changed == 'coordinates' else b''))


def exposed_operator(monkeypatch, target, *, failure=None):
    import empirical_lawhood.domains.rubisco.rubisco_response as package
    import empirical_lawhood.adapters.rubisco.rubisco_response as native_package
    operators = []
    for short in ('periodic_mm_remainder', 'periodic_images', 'pyscf_periodic_electronic'):
        owner_package = native_package if short == 'pyscf_periodic_electronic' else package
        stub = ModuleType(owner_package.__name__+'.'+short)
        monkeypatch.setitem(sys.modules, stub.__name__, stub)
        monkeypatch.setattr(owner_package, short, stub, raising=False)

    class Operator(HarmonicOperator):
        def __init__(self, **kwargs):
            super().__init__(target, failure=failure)
            self.observe = kwargs['observe']
            self.remainder_audit, self.embedding_audit = {'exposed': True}, {'exposed': True}
            self.reuse_converged_density = kwargs['reuse_converged_density']
            operators.append(self)

        @property
        def evaluations(self):
            return self.calls

        def evaluate(self, coordinates):
            number = self.calls+1
            self.observe(dict(event='entry', evaluation=number, physical_atoms=len(coordinates)))
            result = super().evaluate(coordinates)
            self.observe(dict(event='electronic-return', evaluation=number, converged=True, orbital_gradient_norm=0.0))
            self.observe(dict(event='return', evaluation=number, energy_hartree=result['energy_hartree']))
            return result

    monkeypatch.setattr(periodic_qmmm, 'build_periodic_amber_system', lambda **kw: (object(), (), {'exposed': True}))
    monkeypatch.setattr(periodic_qmmm, 'PeriodicCoupledOperator', Operator)
    return operators


def original_files(item, tmp_path, monkeypatch):
    operators = exposed_operator(monkeypatch, item.coordinates)
    directory = tmp_path/'native'
    directory.mkdir()
    summary = native.execute_gas_relaxation(selection=item.selection, representation=item.model,
        raw_topology=item.raw_top, raw_coordinates=item.raw_xyz, directory=directory)
    files = {p.name: p.read_bytes() for p in directory.iterdir()}
    return summary, files, operators


def test_selected_native_wrapper_and_independent_reader_retain_exact_original_arrays(gas_input, tmp_path, monkeypatch):
    summary, files, operators = original_files(gas_input, tmp_path, monkeypatch)
    assert len(operators) == 1 and operators[0].calls == 2
    assert operators[0].reuse_converged_density == (gas_input.selection.prototype.path.gas == 'CO2')
    assert summary['optimizer_settings']['maximum_iterations'] is None
    assert summary['optimizer_settings']['maximum_evaluations'] is None
    assert files['original.prmtop'] == gas_input.raw_top and files['original.inpcrd'] == gas_input.raw_xyz
    monkeypatch.setattr(native, 'execute_gas_relaxation', lambda **kw: pytest.fail('native replay during assessment'))
    assessment = reader.assess_gas_relaxation_endpoint(selection=gas_input.selection, representation=gas_input.model,
        files=files, assessor_source=gas_input.model.material.sources[0])
    assert assessment.complete_reference_evaluations == 2 and assessment.maximum_gradient_kj_mol_nm < D('1e-10')
    assert assessment.initial_energy_hartree == 0 and abs(assessment.final_energy_hartree) < D('1e-24')
    n = len(gas_input.selection.prototype.path.gas_atom_indices)
    assert len(assessment.gas_host_contacts_angstrom) == n
    assert len(assessment.gas_internal_distances_angstrom) == n*(n-1)//2
    assert len(assessment.gas_c2_distances_angstrom) == n
    assert assessment.gas_basin_admission == assessment.electronic_character_admission == assessment.rate_admission == 'UNEVALUABLE'
    assert decode_canonical_bytes(assessment.canonical_bytes(), type(assessment), maximum_bytes=2**20) == assessment


@pytest.mark.parametrize('changed', ('initial-array', 'selection', 'source-binding', 'native-census', 'native-energy', 'final-force'))
def test_endpoint_reader_rejects_changed_source_and_missing_complete_native_returns(gas_input, tmp_path, monkeypatch, changed):
    _, files, _ = original_files(gas_input, tmp_path, monkeypatch)
    if changed == 'initial-array':
        from io import BytesIO
        stream = BytesIO()
        points = gas_input.coordinates.copy(); points[-1, 0] += .01
        np.save(stream, points, allow_pickle=False)
        files['initial-coordinates-angstrom.npy'] = stream.getvalue()
    elif changed == 'selection':
        files['gas-selection.json'] += b'\n'
    elif changed == 'source-binding':
        row = json.loads(files['source-bindings.json']); row['physical_atoms'] -= 1
        files['source-bindings.json'] = json.dumps(row).encode()
    elif changed == 'final-force':
        files['relaxation-evaluations.jsonl'] = files['relaxation-evaluations.jsonl'].replace(b'final-endpoint-force', b'minimizer')
    else:
        rows = [json.loads(line) for line in files['native-observations.jsonl'].splitlines()]
        if changed == 'native-census':
            rows.pop(0)
        else:
            rows[-1]['energy_hartree'] += 1
        files['native-observations.jsonl'] = b'\n'.join(json.dumps(r).encode() for r in rows)
    with pytest.raises(ValueError):
        reader.assess_gas_relaxation_endpoint(selection=gas_input.selection, representation=gas_input.model,
            files=files, assessor_source=gas_input.model.material.sources[0])


def test_native_failure_retains_attempt_without_replay_or_endpoint_invention(gas_input, tmp_path, monkeypatch):
    operators = exposed_operator(monkeypatch, gas_input.coordinates, failure='native-error')
    directory = tmp_path/'failed-native'; directory.mkdir()
    with pytest.raises(RuntimeError, match='exposed-electronic-refusal'):
        native.execute_gas_relaxation(selection=gas_input.selection, representation=gas_input.model,
            raw_topology=gas_input.raw_top, raw_coordinates=gas_input.raw_xyz, directory=directory)
    assert len(operators) == 1 and operators[0].calls == 1
    assert not (directory/'final-coordinates-angstrom.npy').exists()
    assert not (directory/'relaxation-summary.json').exists()
    assert [json.loads(line)['event'] for line in (directory/'relaxation-evaluations.jsonl').read_bytes().splitlines()] == ['relaxation-entry', 'relaxation-error']


def test_periodic_gas_contacts_use_all_host_atoms_and_do_not_invent_basin_criteria(gas_input):
    points = gas_input.coordinates.copy()
    selection = gas_input.selection
    n = selection.augmentation.original_atom_count
    first = selection.prototype.path.gas_atom_indices[0]
    heavy = next(i for i in reversed(range(n)) if gas_input.model.atoms[i].atomic_number != 1)
    box = float(selection.prototype.cell.lengths_angstrom[0])
    points[first] = points[heavy]+np.asarray((box+.125, 0, 0))
    _, contacts, _ = reader.observe_gas_endpoint_geometry(selection=selection, representation=gas_input.model, final=points)
    assert contacts[0][3] == heavy
    assert abs(contacts[0][4]-D('.125')) < D('1e-10')
