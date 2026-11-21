# SPDX-License-Identifier: MPL-2.0
"""Analytic relaxation controls; no enzyme physics or kinetic evidence."""

from decimal import Decimal as D
from io import BytesIO
import json

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_native import minimize_reference_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import ActiveRelaxationSettings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import GRADIENT_UNIT
from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import COULOMB_KJ_NM_PER_MOL_E2
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_assessment import assess_endpoint_trace, read_endpoint_arrays


class HarmonicOperator:
    def __init__(self, target, failure=None):
        self.target = np.asarray(target, dtype=float)
        self.calls = 0
        self.failure = failure
        self.coordinates = []

    def evaluate(self, coordinates):
        self.calls += 1
        self.coordinates.append(np.asarray(coordinates).copy())
        if self.failure == 'native-error':
            raise RuntimeError('exposed-electronic-refusal')
        # Independent analytic potential: E = 50 * sum((r_nm-r0_nm)^2),
        # in kJ/mol. Convert its derivatives to the declared native return.
        displacement_nm = (np.asarray(coordinates)-self.target)/10
        energy = 50*float(np.sum(displacement_nm**2))
        gradient_nm = 100*displacement_nm
        bohr = .52917721092
        hartree = COULOMB_KJ_NM_PER_MOL_E2/(bohr/10)
        gradient = gradient_nm*bohr/(10*hartree)
        if self.failure == 'incomplete':
            gradient = gradient[:-1]
        return dict(energy_hartree=energy/hartree, gradient_hartree_per_bohr=gradient,
            bohr_angstrom=bohr, hartree_kj_mol=hartree,
            gradient_unit='INCORRECT_UNIT' if self.failure == 'unit' else GRADIENT_UNIT)


def test_full_gradient_minimization_reaches_known_minimum_without_iteration_ceiling():
    target = np.asarray(((0., 1., 2.), (4., 3., -2.)))
    operator = HarmonicOperator(target)
    initial = target+np.asarray(((.9, -.4, .6), (-.2, .7, -.5)))
    observed = []
    settings = ActiveRelaxationSettings('settings.exposed.harmonic', maximum_gradient_kj_mol_nm=D('1e-7'))
    xyz, returned, summary = minimize_reference_geometry(operator=operator, initial_angstrom=initial,
        settings=settings, observe=observed.append)
    assert np.max(np.abs(xyz-target)) < 1e-7
    assert returned['energy_hartree'] < 1e-18
    assert summary['maximum_final_gradient_kj_mol_nm'] <= 1e-7
    assert summary['complete_reference_evaluations'] == operator.calls == summary['optimizer_evaluations']+1
    assert summary['optimizer_settings']['maximum_iterations'] is None
    assert summary['optimizer_settings']['maximum_evaluations'] is None
    assert summary['added_restraints'] is False and summary['molecular_time_seconds'] is None
    assert summary['equilibrium_population'] == summary['rate_admission'] == 'UNEVALUABLE'
    assert np.array_equal(operator.coordinates[-1], xyz)
    entries = [r for r in observed if r['event'] == 'relaxation-entry']
    returns = [r for r in observed if r['event'] == 'relaxation-return']
    assert [r['evaluation'] for r in entries] == list(range(1, operator.calls+1))
    assert [r['evaluation'] for r in returns] == list(range(1, operator.calls+1))
    assert returns[-1]['phase'] == 'final-endpoint-force'


@pytest.mark.parametrize('failure', ('native-error', 'incomplete', 'unit'))
def test_bad_reference_return_is_retained_as_error_and_never_retried(failure):
    operator = HarmonicOperator(np.zeros((2, 3)), failure=failure)
    events = []
    with pytest.raises((ValueError, RuntimeError)):
        minimize_reference_geometry(operator=operator, initial_angstrom=np.ones((2, 3)),
            settings=ActiveRelaxationSettings('settings.exposed.failure'), observe=events.append)
    assert operator.calls == 1
    assert [r['event'] for r in events] == ['relaxation-entry', 'relaxation-error']


def test_already_stationary_input_gets_a_fresh_endpoint_force():
    operator = HarmonicOperator(np.zeros((2, 3)))
    _, _, summary = minimize_reference_geometry(operator=operator, initial_angstrom=np.zeros((2, 3)),
        settings=ActiveRelaxationSettings('settings.exposed.stationary'), observe=lambda row: None)
    assert operator.calls == 2 and summary['iterations'] == 0
    assert summary['final_evaluation'] == 2


def endpoint_files(operator=None):
    initial=np.asarray(((.1324567891234,1.,2.),(4.,3.,-2.)),dtype='<f8')
    operator=HarmonicOperator(initial) if operator is None else operator
    settings=ActiveRelaxationSettings('settings.exposed.endpoint')
    events=[]
    final,returned,summary=minimize_reference_geometry(operator=operator,initial_angstrom=initial,settings=settings,observe=events.append)
    files={'relaxation-summary.json':json.dumps(summary).encode(),
        'relaxation-evaluations.jsonl':b'\n'.join(json.dumps(row).encode() for row in events)+b'\n'}
    for name,arr in (('initial-coordinates-angstrom.npy',initial),('final-coordinates-angstrom.npy',final),
            ('final-gradient-hartree-per-bohr.npy',returned['gradient_hartree_per_bohr']),
            ('final-energy-hartree.npy',np.asarray(returned['energy_hartree']))):
        stream=BytesIO();np.save(stream,arr,allow_pickle=False);files[name]=stream.getvalue()
    return settings,files


def test_independent_endpoint_reader_uses_complete_arrays_and_fresh_force():
    settings,files=endpoint_files()
    initial,final,gradient,energy=read_endpoint_arrays(files,atom_count=2)
    count,maximum,first_energy,findings=assess_endpoint_trace(files,initial=initial,final=final,
        gradient=gradient,energy=energy,settings=settings)
    assert count==2 and maximum<1e-10 and first_energy==0 and findings==set()


@pytest.mark.parametrize('changed',('gradient','call-census','fresh-force','unit','trailing-array','incomplete-array'))
def test_independent_reader_refuses_changed_original_operands_and_calls(changed):
    settings,files=endpoint_files()
    if changed in ('trailing-array','incomplete-array'):
        if changed=='trailing-array':files['final-coordinates-angstrom.npy']+=b'FORGED_TRAILER'
        else:
            stream=BytesIO();np.save(stream,np.zeros((1,3)),allow_pickle=False)
            files['final-coordinates-angstrom.npy']=stream.getvalue()
        with pytest.raises(ValueError,match='complete finite'):read_endpoint_arrays(files,atom_count=2)
        return
    initial,final,gradient,energy=read_endpoint_arrays(files,atom_count=2)
    if changed=='gradient':gradient[0,0]+=1e-4
    elif changed=='unit':
        summary=json.loads(files['relaxation-summary.json']);summary['bohr_angstrom']=.052917721092
        files['relaxation-summary.json']=json.dumps(summary).encode()
    else:
        rows=[json.loads(line) for line in files['relaxation-evaluations.jsonl'].splitlines()]
        if changed=='call-census':rows.pop(0)
        else:
            for row in rows:
                if row.get('phase')=='final-endpoint-force':row['phase']='minimizer'
        files['relaxation-evaluations.jsonl']=b'\n'.join(json.dumps(row).encode() for row in rows)
    with pytest.raises(ValueError,match='trace|summary'):
        assess_endpoint_trace(files,initial=initial,final=final,gradient=gradient,energy=energy,settings=settings)


def test_optimizer_success_cannot_replace_independent_final_force_criterion():
    class ChangedFinalForce(HarmonicOperator):
        def evaluate(self,coordinates):
            value=super().evaluate(coordinates)
            if self.calls==2:value['gradient_hartree_per_bohr'][0,0]=.01
            return value
    operator=ChangedFinalForce(np.asarray(((.1324567891234,1.,2.),(4.,3.,-2.))))
    settings,files=endpoint_files(operator)
    initial,final,gradient,energy=read_endpoint_arrays(files,atom_count=2)
    _,maximum,_,findings=assess_endpoint_trace(files,initial=initial,final=final,
        gradient=gradient,energy=energy,settings=settings)
    assert json.loads(files['relaxation-summary.json'])['optimizer_reported_success'] is True
    assert maximum>1 and 'final-force-not-converged' in findings


def _prefix_source_pins():
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    return {name: ObjectIdentity('exposed.' + name, 'empirical-lawhood/exposed/' + name,
                                '1.0.0', str(index) * 64)
            for index, name in enumerate(('configuration', 'seed', 'prototype'), 1)}


def _prefix_run(operator, *, allowance=5, checkpoints=None, evaluations=None,
                resume_state=None, original_evaluations=()):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_native import minimize_reference_prefix
    checkpoints = [] if checkpoints is None else checkpoints
    evaluations = [] if evaluations is None else evaluations
    return minimize_reference_prefix(operator=operator, initial_angstrom=np.full((2, 3), 10.),
        settings=ActiveRelaxationSettings('settings.exposed.prefix', maximum_gradient_kj_mol_nm=D('1e-12')),
        complete_return_allowance=allowance, observe=lambda row: None,
        retain_evaluation=lambda number, xyz, value: evaluations.append((number, xyz.copy(), value)),
        retain_checkpoint=lambda *row: checkpoints.append(row), resume_state=resume_state,
        original_evaluations=original_evaluations)


def test_preparation_purchase_retains_actual_accepted_force_without_an_extra_endpoint_call():
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import prepare_checkpoint, read_checkpoint_arrays
    operator = HarmonicOperator(np.zeros((2, 3)))
    evaluations, checkpoints = [], []
    result = _prefix_run(operator, evaluations=evaluations, checkpoints=checkpoints)
    assert operator.calls == result['summary']['new_complete_reference_evaluations'] == 5
    assert not result['summary']['optimizer_reported_success']
    assert result['summary']['rate_admission'] == result['summary']['equilibrium_population'] == 'UNEVALUABLE'
    assert result['summary']['molecular_time_seconds'] is None
    assert len(checkpoints) == 5
    state, number, xyz, original = checkpoints[-1]
    assert np.array_equal(xyz, evaluations[number - 1][1])
    assert np.array_equal(original['gradient_hartree_per_bohr'], evaluations[number - 1][2]['gradient_hartree_per_bohr'])
    pins = _prefix_source_pins()
    record, arrays = prepare_checkpoint(state=state, native_coordinates=xyz, native_result=original,
        native_evaluation=number, **pins)
    read = read_checkpoint_arrays(record, arrays, **pins)
    assert read.evaluations == operator.calls
    assert np.array_equal(read.coordinates, state.coordinates)
    # Independent harmonic derivative in the retained physical units.
    assert np.max(np.abs(read.gradient - 10 * xyz.reshape(-1))) < 1e-12
    assert not read.coordinates.flags.writeable and not read.gradient.flags.writeable


def test_published_optimizer_continuation_matches_uninterrupted_calls_without_repeating_initial_force(tmp_path):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import ActivePreparationCheckpoint, prepare_checkpoint, publish_checkpoint_files, read_checkpoint_files
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    uninterrupted = HarmonicOperator(np.zeros((2, 3)))
    baseline = _prefix_run(uninterrupted, allowance=10)
    first_operator = HarmonicOperator(np.zeros((2, 3)))
    evaluations, checkpoints = [], []
    first = _prefix_run(first_operator, evaluations=evaluations, checkpoints=checkpoints)
    state, number, xyz, original = checkpoints[-1]
    pins = _prefix_source_pins()
    record, arrays = prepare_checkpoint(state=state, native_coordinates=xyz, native_result=original,
        native_evaluation=number, **pins)
    seal = publish_checkpoint_files(tmp_path, record, arrays)
    decoded = decode_canonical_bytes((tmp_path / seal).read_bytes(), ActivePreparationCheckpoint, maximum_bytes=2**20)
    files = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    restored, _ = read_checkpoint_files(decoded, files, **pins)
    second_operator = HarmonicOperator(np.zeros((2, 3)))
    continued = _prefix_run(second_operator, resume_state=restored, original_evaluations=tuple(evaluations))
    assert first_operator.calls == second_operator.calls == 5
    assert continued['summary']['previous_complete_evaluations'] == 5
    assert continued['summary']['complete_reference_evaluations'] == 10
    assert len(first['state'].history) > 0
    assert np.array_equal(continued['coordinates'], baseline['coordinates'])
    assert all(np.array_equal(a, b) for a, b in zip(
        uninterrupted.coordinates, first_operator.coordinates + second_operator.coordinates, strict=True))
    assert np.array_equal(continued['state'].gradient, baseline['state'].gradient)


def test_complete_return_without_checkpoint_replays_exact_original_first_force():
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_native import minimize_reference_prefix
    first = HarmonicOperator(np.zeros((2, 3)))
    evaluations = []
    def sealed_then_interrupted(number, xyz, returned):
        evaluations.append((number, xyz.copy(), returned))
        raise OSError('exposed-complete-return-before-checkpoint')
    with pytest.raises(OSError, match='before-checkpoint'):
        minimize_reference_prefix(operator=first, initial_angstrom=np.full((2, 3), 10.),
            settings=ActiveRelaxationSettings('settings.exposed.prefix', maximum_gradient_kj_mol_nm=D('1e-12')),
            complete_return_allowance=5, observe=lambda row: None,
            retain_evaluation=sealed_then_interrupted, retain_checkpoint=lambda *row: pytest.fail('unsealed checkpoint'))
    continued = HarmonicOperator(np.zeros((2, 3)))
    actual = _prefix_run(continued, allowance=4, original_evaluations=tuple(evaluations))
    baseline = HarmonicOperator(np.zeros((2, 3)))
    expected = _prefix_run(baseline)
    assert first.calls == 1 and continued.calls == 4 and baseline.calls == 5
    assert actual['summary']['replayed_evaluations'] == [1]
    assert actual['summary']['native_electronic_continuation'] == 'RESTARTED_INITIALIZATION'
    assert np.array_equal(actual['state'].coordinates, expected['state'].coordinates)
    assert all(np.array_equal(a, b) for a, b in zip(
        first.coordinates + continued.coordinates, baseline.coordinates, strict=True))


def test_exhausted_original_allowance_restores_checkpoint_without_new_calls():
    first = HarmonicOperator(np.zeros((2, 3)))
    evaluations = []
    original = _prefix_run(first, evaluations=evaluations)
    continued = HarmonicOperator(np.zeros((2, 3)))
    restored = _prefix_run(continued, allowance=0, resume_state=original['state'],
        original_evaluations=tuple(evaluations))
    assert first.calls == 5 and continued.calls == 0
    assert restored['summary']['complete_reference_evaluations'] == 5
    assert restored['summary']['new_complete_reference_evaluations'] == 0
    assert np.array_equal(restored['state'].coordinates, original['state'].coordinates)
    assert np.array_equal(restored['state'].gradient, original['state'].gradient)


@pytest.mark.parametrize('changed', ('source', 'gradient', 'curvature', 'trailer'))
def test_preparation_checkpoint_reader_refuses_source_force_history_and_array_substitution(tmp_path, changed):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import prepare_checkpoint, publish_checkpoint_files, read_checkpoint_arrays, read_checkpoint_files
    result = _prefix_run(HarmonicOperator(np.zeros((2, 3))))
    pins = _prefix_source_pins()
    record, arrays = prepare_checkpoint(state=result['state'], native_coordinates=result['coordinates'],
        native_result=result['native_result'], native_evaluation=result['accepted_evaluation'], **pins)
    if changed == 'source':
        pins['prototype'] = pins['seed']
    elif changed == 'gradient':
        arrays['gradient-hartree-per-bohr'] = arrays['gradient-hartree-per-bohr'].copy()
        arrays['gradient-hartree-per-bohr'][0, 0] += .1
    elif changed == 'curvature':
        arrays['curvature-rho-mol-per-kj'] = arrays['curvature-rho-mol-per-kj'].copy()
        arrays['curvature-rho-mol-per-kj'][0] *= 2
    else:
        publish_checkpoint_files(tmp_path, record, arrays)
        files = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
        name = next(name for name in files if name.endswith('.coordinates-angstrom.npy'))
        files[name] += b'UNBOUND'
        with pytest.raises(ValueError, match='trailer'):
            read_checkpoint_files(record, files, **pins)
        return
    with pytest.raises(ValueError, match='source|array'):
        read_checkpoint_arrays(record, arrays, **pins)


def test_preparation_return_publication_failure_cannot_become_an_accepted_state():
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_native import minimize_reference_prefix
    operator = HarmonicOperator(np.zeros((2, 3)))
    checkpoints = []
    def refuse(*args):
        raise OSError('disclosed-publication-interruption')
    with pytest.raises(OSError, match='publication-interruption'):
        minimize_reference_prefix(operator=operator, initial_angstrom=np.ones((2, 3)),
            settings=ActiveRelaxationSettings('settings.exposed.interrupted'), complete_return_allowance=5,
            observe=lambda row: None, retain_evaluation=refuse, retain_checkpoint=lambda *row: checkpoints.append(row))
    assert operator.calls == 1 and checkpoints == []
