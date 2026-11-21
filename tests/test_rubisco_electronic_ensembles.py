# SPDX-License-Identifier: MPL-2.0
"""Independent spin-space and finite-distribution controls, not enzyme evidence."""

from dataclasses import fields, replace
from decimal import Decimal as D
from itertools import combinations
import math
import json
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.electronic_coupling_science import occupied_spinors, singlet_triplet_spin_orbit, spin_orbit_spinor
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_ensemble_records import ElectronicPairObservable, ElectronicEnsembleRule
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_ensemble_science import hbar_native_hartree_seconds, reduce_electronic_pair, joint_electronic_analysis
from tests.test_rubisco_electronic_couplings import criteria
from tests import test_rubisco_equilibrium_reweighting as equilibrium
from tests import test_rubisco_periodic_equilibrium_acquisition as acquisition
from tests import test_rubisco_accelerated_traces as gpu_controls


fixture = acquisition.fixture


def pair(name='pair.exposed', ensemble='ensemble.a'):
    return ElectronicPairObservable(name,ensemble,'state.a','state.b','SPIN_FREE',
        (D('.00005'),D('.0001')),D('.0001'),2,D(2),D('.2'),D('.1'),D('.01'))


def fock_one_body(operator, electrons=2):
    """Explicit occupation-basis creation/annihilation oracle, no cofactors."""
    states = tuple(combinations(range(len(operator)),electrons))
    index = {row:i for i,row in enumerate(states)}
    result = np.zeros((len(states),len(states)),dtype=complex)
    for j,occupied in enumerate(states):
        for q in occupied:
            remaining = tuple(i for i in occupied if i != q)
            for p in range(len(operator)):
                if p in remaining:
                    continue
                sign = (-1)**(occupied.index(q)+sum(i < p for i in remaining))
                row = tuple(sorted((*remaining,p)))
                result[index[row],j] += sign*operator[p,q]
    return states,result


def spin_operands():
    rng = np.random.default_rng(9913)
    rotation,_ = np.linalg.qr(rng.normal(size=(3,3)))
    c = np.stack((rotation,rotation))
    d = np.stack((np.eye(3),np.eye(3)))
    singlet = np.array([[1,0,0],[1,0,0]])
    triplet = np.array([[1,1,0],[0,0,0]])
    raw = rng.normal(size=(3,3,3))*1e-4
    imaginary = raw-raw.transpose(0,2,1)
    return dict(overlap=np.eye(3),singlet_coefficients=c,singlet_occupations=singlet,
        triplet_coefficients=d,triplet_occupations=triplet,soc_imaginary=imaginary,
        singlet_spin_square_excess=0.,triplet_spin_square_excess=0.,donor_is_triplet=True)


def test_complete_spin_components_match_explicit_many_electron_lowering():
    args = spin_operands()
    states,h = fock_one_body(spin_orbit_spinor(args['soc_imaginary']))
    a = occupied_spinors(args['singlet_coefficients'],args['singlet_occupations'])
    b = occupied_spinors(args['triplet_coefficients'],args['triplet_occupations'])
    singlet = np.array([np.linalg.det(a[list(row)]) for row in states])
    highest = np.array([np.linalg.det(b[list(row)]) for row in states])
    lowering = np.zeros((6,6)); lowering[3:,:3] = np.eye(3)
    _,lower = fock_one_body(lowering)
    components = (highest,lower@highest/math.sqrt(2),lower@lower@highest/2)
    np.testing.assert_allclose([v.conj()@v for v in components],1,atol=1e-15)
    oracle = np.array([singlet.conj()@h@v for v in components])
    result = singlet_triplet_spin_orbit(**args)
    np.testing.assert_allclose(result['singlet_bra_amplitudes_hartree'],oracle,atol=1e-18)
    assert result['coupling_squared_hartree2'] == pytest.approx(np.vdot(oracle,oracle).real/3)
    assert result['amplitude_error_bounds_hartree'] == (0.,0.,0.)
    reverse = singlet_triplet_spin_orbit(**{**args,'donor_is_triplet':False})
    assert reverse['coupling_squared_hartree2'] == pytest.approx(3*result['coupling_squared_hartree2'])


def test_complete_multiplet_is_rotation_invariant_and_contamination_is_bounded():
    args = spin_operands()
    original = singlet_triplet_spin_orbit(**args)
    rotation,_ = np.linalg.qr(np.random.default_rng(231).normal(size=(3,3)))
    rotated = np.einsum('ij,jab->iab',rotation,args['soc_imaginary'])
    current = singlet_triplet_spin_orbit(**{**args,'soc_imaginary':rotated})
    assert current['coupling_squared_hartree2'] == pytest.approx(original['coupling_squared_hartree2'])
    uncertain = singlet_triplet_spin_orbit(**{**args,'singlet_spin_square_excess':.02,
        'triplet_spin_square_excess':.04})
    assert uncertain['higher_spin_weight_upper_bounds'] == (.01,.01)
    assert all(v > 0 for v in uncertain['amplitude_error_bounds_hartree'])
    assert uncertain['relative_coupling_squared_error_bound'] > .01
    with pytest.raises(ValueError,match='highest-weight'):
        singlet_triplet_spin_orbit(**{**args,'triplet_occupations':args['singlet_occupations']})


def gap_data():
    gaps = np.tile(np.array([-.75,-.25,.25,.75])*1e-4,128)
    gaps = np.random.default_rng(3091).permutation(gaps)
    return dict(pair=pair(),weights=np.full(len(gaps),1/len(gaps)),gaps=gaps,
        coupling_squared=np.full(len(gaps),1e-20),gap_speeds=np.full(len(gaps),1e12),
        point_supported=np.ones(len(gaps),dtype=bool),trace_counts=(len(gaps),),
        sample_intervals_seconds=(1e-15,),hartree_kj_mol=2625.4996394799,
        unbiased_gap_dynamics=True)


def test_finite_gap_density_rate_matches_independent_units_and_bandwidth_oracle():
    args = gap_data()
    result = reduce_electronic_pair(**args)
    hbar = 1.0545718176461565e-34/(2625.4996394799*1000/6.02214076e23)
    assert hbar_native_hartree_seconds(args['hartree_kj_mol']) == pytest.approx(hbar,rel=1e-15)
    oracle = 2*math.pi/hbar*1e-20/(2e-4)
    assert all(r['finite_slab_rate_per_second'] == pytest.approx(oracle) for r in result['bandwidths'])
    assert result['absolute_bandwidth_log_rate_range'] == 0
    assert result['selected_golden_rule_criteria'] == 'SATISFIED'
    assert result['physical_rate_admission'] == 'UNEVALUABLE'


def test_missing_points_never_become_success_subset_or_zero_rate():
    args = gap_data()
    args['point_supported'][0] = False
    result = reduce_electronic_pair(**args)
    assert result['assigned_configurations'] == 512 and result['supported_configurations'] == 511
    assert result['primary_rate_per_second'] is None and not result['complete_population']
    assert 'COMPLETE_SUPPORTED_ELECTRONIC_POINT_POPULATION_UNAVAILABLE' in result['missing']


def test_strong_transition_and_biased_sampling_cannot_supply_a_physical_markov_rate():
    args = gap_data()
    args['gap_speeds'][:] = 0
    result = reduce_electronic_pair(**args)
    assert result['selected_golden_rule_criteria'] == 'FALSIFIED'
    assert all(r['maximum_landau_zener_probability'] == 1 for r in result['bandwidths'])
    biased = reduce_electronic_pair(**{**gap_data(),'unbiased_gap_dynamics':False})
    assert 'BIASED_SAMPLING_TIME_CANNOT_SUPPLY_PHYSICAL_GAP_MEMORY' in biased['missing']
    assert all(r['rate_memory_product'] is None for r in biased['bandwidths'])
    assert biased['primary_rate_per_second'] is not None


def test_joint_rates_reuse_original_paired_blocks_and_keep_failed_draws():
    selected = equilibrium.joint_selection()
    rules = tuple(pair('pair.'+str(i),e.ensemble_id) for i,e in enumerate(selected.ensembles))
    rule = ElectronicEnsembleRule('rule.exposed',selected,criteria(),rules,2**31,('Exposed numerical control.',))
    rng = np.random.default_rng(89)
    q = rng.choice((-2.,-1.,1.,2.),size=(256,1))
    tables = {t.trace_id:dict(coordinates=q.copy(),reference_energy_kj_mol=q[:,0]**2) for t in selected.traces}
    report,_ = equilibrium.science.joint_block_analysis(selection=selected,tables=tables,
        windows={t.trace_id:None for t in selected.traces})
    projected = {t.trace_id+'.coordinates':q for t in selected.traces}
    projected.update({t.trace_id+'.all_window_bias_potentials_kj_mol':np.zeros((1,len(q))) for t in selected.traces})
    data = np.zeros((len(q),12)); data[:,2] = q[:,0]*1e-5; data[:,6] = (3+q[:,0])*1e-20
    points = {p.pair_id:(data.copy(),np.ones(len(q),dtype=bool)) for p in rules}
    values = {p.pair_id:dict(primary_rate_per_second=1.) for p in rules}
    params = dict(rule=rule,equilibrium={'statistics':report},projected=projected,points=points,
        point_estimates=values,energy_conversions={e.ensemble_id:2625.4996394799 for e in selected.ensembles})
    result,arrays = joint_electronic_analysis(**params)
    assert result['retained_replicates'] == 32 and result['failed_replicates'] == ()
    draws = np.asarray(result['joint_values'])
    np.testing.assert_array_equal(draws[:,-1],draws[:,-2])
    covariance = np.asarray(result['covariance'])
    assert covariance[-1,-1] > 0 and covariance[-1,-1] == covariance[-1,-2]
    points['pair.0'][1][0] = False
    failed,masked = joint_electronic_analysis(**params)
    assert len(failed['failed_replicates']) == failed['requested_replicates'] == 32
    assert failed['covariance'] is None
    assert not masked['electronic.joint_available'][:,-2].any()
    assert arrays['electronic.joint_available'].all()


def test_spin_population_is_an_explicit_scientific_selection():
    with pytest.raises(ValueError,match='population'):
        replace(pair(),coupling='SPIN_ORBIT_SINGLET_TRIPLET_MULTIPLET')
    selected = replace(pair(),coupling='SPIN_ORBIT_SINGLET_TRIPLET_MULTIPLET',
        spin_population_model='ISOTROPIC_UNPOLARIZED_ZERO_FIELD')
    assert selected.spin_population_model == 'ISOTROPIC_UNPOLARIZED_ZERO_FIELD'


def observed_configuration(fixture):
    from empirical_lawhood.domains.rubisco.rubisco_response.electronic_states import ElectronicPopulationConstraint, ConstrainedElectronicState
    from empirical_lawhood.domains.rubisco.rubisco_response.electronic_observations import ElectronicObservationSet
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import ConstrainedPeriodicForceSettings
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import prepare_periodic_probe_selection
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import prepare_raw_sources
    from empirical_lawhood.api.domain_composition.rubisco_response import electronic_ensembles as public
    fixture.config = gpu_controls.gpu_config(fixture)
    baseline = fixture.config.selection
    prototypes = []
    for name in ('a','b'):
        state = ConstrainedElectronicState('state.'+name,fixture.model.identity,baseline.path.qm_atom_indices,
            baseline.path.qm_formal_charge,1,(ElectronicPopulationConstraint('constraint.exposed',
                'ELECTRON_POPULATION',(baseline.path.qm_atom_indices[0],),D(2)),),D('1e-8'),D('1e-10'),100,(D(0),),
            fixture.model.material.sources[0])
        options = {f.name:getattr(baseline.electronic,f.name) for f in fields(baseline.electronic)}
        options.update(settings_id='settings.electronic.'+name,ks_flavour='UKS',state=state)
        electronic = ConstrainedPeriodicForceSettings(**options)
        prototypes.append(prepare_periodic_probe_selection(representation=fixture.model,path=baseline.path,
            cell=baseline.cell,electronic=electronic,molecular=baseline.molecular,engine=baseline.engine))
    observations = ElectronicObservationSet('observations.exposed',tuple(prototypes))
    fixture.selection = prototypes[0]
    fixture.sources = prepare_raw_sources(fixture.selection,fixture.raw_top,fixture.raw_xyz)
    fixture.config = replace(fixture.config,selection=fixture.selection,raw_sources=fixture.sources.identity,
        raw_source_size_bytes=fixture.sources.canonical_size_bytes())
    ordinary,raw = acquisition.trajectory(fixture)
    xyz,velocity,_ = acquisition.selected.read_equilibrium_phase_space(ordinary.selection,fixture.model,raw)
    selection,phase = public.prepare_electronic_equilibrium(observations=observations,prototype=fixture.selection,
        representation=fixture.model,phase_source=fixture.model.raw_coordinates,
        initial_angstrom=xyz,initial_velocity_nm_per_ps=velocity,settings=ordinary.selection.settings,
        window=ordinary.selection.window,convention=ordinary.selection.convention,criteria=ordinary.selection.criteria)
    config = acquisition.owner.ObservedElectronicEquilibriumConfig('config.exposed.electronic',fixture.config,selection)
    chosen = equilibrium.original_selection(fixture,config)
    rule = ElectronicEnsembleRule('rule.original.electronic',chosen,replace(criteria(),maximum_workspace_bytes=2**20),
        (pair(ensemble='ensemble.exposed'),),2**30,('Exposed complete native custody with synthetic electronic arrays.',))
    return config,phase,rule


def instrument_electronic_operator(fixture,monkeypatch,*,failed_point=False):
    from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm
    from empirical_lawhood.domains.rubisco.rubisco_response import electronic_observation_native
    from empirical_lawhood.domains.rubisco.rubisco_response.constrained_observations import UPSTREAM_FILES
    from empirical_lawhood.domains.rubisco.rubisco_response.electronic_ensemble_read import _qm_geometry
    observed = acquisition.stub_native(fixture,monkeypatch)
    base = periodic_qmmm.PeriodicCoupledOperator
    calls = []
    prototypes = {}

    def capture(directory,*,mf,gpu,state,evaluation,diagnostics,name_prefix=''):
        prototype = prototypes[state.state_id]
        atomic = [fixture.model.atoms[i].atomic_number for i in state.qm_atom_indices]+[1]*len(prototype.path.boundaries)
        electrons = sum(atomic)-state.qm_formal_charge
        n = electrons//2+2
        c = np.eye(n)
        if state.state_id == 'state.b':
            theta = .6; i,j = n-3,n-1
            c[i,i] = c[j,j] = math.cos(theta); c[i,j] = -math.sin(theta); c[j,i] = math.sin(theta)
        c = np.stack((c,c)); occ = np.zeros((2,n)); occ[:,:electrons//2] = 1
        projector = np.zeros((1,n,n)); projector[0,0,0] = 1
        arrays = {'ao-overlap':np.eye(n),'mo-coefficients':c,'mo-occupations':occ,
            'mo-energies':np.zeros((2,n)),'density':(c*occ[:,None,:])@c.transpose(0,2,1),
            'constraint-projectors':projector,'constraint-multipliers':np.zeros(1),
            'constraint-potential':np.zeros((2,n,n))}
        prefix = name_prefix+f'electronic.{evaluation:016d}.'
        metadata = {}
        for name,value in arrays.items():
            value = np.asarray(value,dtype='<f8')
            with (directory/(prefix+name+'.npy')).open('xb') as stream:
                np.save(stream,value,allow_pickle=False)
            metadata[name] = dict(shape=list(value.shape),dtype='<f8',sha256=sha256(value.tobytes()).hexdigest())
        (directory/(prefix+'state.json')).write_text(json.dumps(dict(evaluation=evaluation,state=state.to_document(),
            diagnostics=diagnostics,arrays=metadata,spin_orbit=None,ao_labels=[f'{i} EXPOSED AO' for i in range(n)],
            atom_charges=atomic,atom_coordinates_bohr=_qm_geometry(prototype,mf).tolist(),
            electrons=electrons,alpha_beta_electrons=[electrons//2]*2)))

    class Operator(base):
        def __init__(self,**kwargs):
            state = kwargs['settings'].state
            prototype = next(p for p in fixture.electronic_config.selection.observations.prototypes if p.electronic.state == state)
            prototypes[state.state_id] = prototype
            target = kwargs['observe']
            for row in gpu_controls.apparatus(kwargs['device_memory_bytes']):
                target(row)
            self.state,self.capture = state,kwargs['capture_electronic_state']
            electrons = sum(fixture.model.atoms[i].atomic_number for i in state.qm_atom_indices)-state.qm_formal_charge
            self.diagnostics = dict(state=state.identity.to_document(),constraint_ids=['constraint.exposed'],
                observed_electrons=[2.],target_electrons=[2.],residual_electrons=[0.],lagrange_multipliers_hartree=[0.],
                alpha_beta_electron_counts=[electrons/2]*2,spin_square=0.,effective_multiplicity=1.,
                spin_purity_admission='UNEVALUABLE',projection=state.projection,upstream_files=UPSTREAM_FILES)
            def observe(row):
                if row['event'] == 'entry':
                    target(dict(event='constrained-state-entry',evaluation=row['evaluation'],state=state.identity.to_document(),
                        upstream='GPU4PYSCF_1.8.1_CDFT_UKS_MINAO_LAGRANGE'))
                elif row['event'] == 'return':
                    target(dict(event='constrained-state-return',evaluation=row['evaluation'],**self.diagnostics))
                    target(gpu_controls.cost(row['evaluation']))
                target(row)
            kwargs['observe'] = observe
            super().__init__(**kwargs)
            calls.append(state.state_id)

        def evaluate(self,coordinates):
            if failed_point and self.state.state_id == 'state.b':
                raise RuntimeError('exposed original vertical failure')
            returned = super().evaluate(coordinates)
            self.capture(coordinates,None,self.evaluations,self.diagnostics)
            returned.update(scf_converged=True,orbital_gradient_norm=0.)
            if self.state.state_id == 'state.b':
                returned['energy_hartree'] += 1e-5
            return returned

    monkeypatch.setattr(periodic_qmmm,'PeriodicCoupledOperator',Operator)
    monkeypatch.setattr(electronic_observation_native,'record_constrained_state',capture)
    monkeypatch.setattr(gpu_controls.backend,'preflight_gpu_backend',lambda **k:None)
    return calls,observed


@pytest.mark.parametrize('failed_point',(False,True))
def test_original_electronic_custody_keeps_complete_frames_failures_and_no_repeat(fixture,monkeypatch,failed_point):
    from empirical_lawhood.api.domain_composition.rubisco_response import electronic_ensembles as public
    config,phase,rule = observed_configuration(fixture)
    fixture.electronic_config = config
    calls,_ = instrument_electronic_operator(fixture,monkeypatch,failed_point=failed_point)
    custody = acquisition.custody(fixture,config,phase)
    runner = acquisition.owner.operation_declaration(accelerated=True,observed=True).runner_factory()
    returned = runner.execute_with_native_subwork(custody.context,custody.store)
    original = acquisition.decode_canonical_bytes(returned.outputs[0].payload,
        acquisition.owner.ReferenceEquilibriumResult,maximum_bytes=acquisition.owner.MAX_RETURN)
    assert original.returned.error is None,original.returned.error
    assert calls == ['state.a','state.b','state.b']
    source = public.RetainedEquilibriumTrace('trace.original',config,fixture.model,phase,original,custody.store)
    result,arrays = public.read_electronic_ensembles(selection=rule,sources=(source,),assessor_source=fixture.model.material.sources[0])
    assert result['assigned_points'] == 4
    assert result['complete_pair_configurations'] == (0 if failed_point else 2)
    census = result['original_trace_census']['trace.original']['observed_frames']
    assert tuple(census) == ('1','2')
    assert all(not row['states']['state.b']['complete'] for row in census.values()) if failed_point else all(
        row['states']['state.b']['complete'] for row in census.values())
    assert all(np.isfinite(v).all() for v in arrays.values())
    monkeypatch.setattr(gpu_controls.backend,'preflight_gpu_backend',lambda **k:pytest.fail('recovery touched device'))
    repeated = runner.execute_with_native_subwork(custody.fresh_context(),custody.store)
    assert repeated.outputs[0].payload == returned.outputs[0].payload
    assert calls == ['state.a','state.b','state.b']


def test_unentered_electronic_population_keeps_every_assigned_point_and_draw(fixture):
    from empirical_lawhood.api.domain_composition.rubisco_response import electronic_ensembles as public
    config,phase,rule = observed_configuration(fixture)
    source = public.RetainedEquilibriumTrace('trace.original',config,fixture.model,phase,None,None)
    result,arrays = public.read_electronic_ensembles(selection=rule,sources=(source,),
        assessor_source=fixture.model.material.sources[0])
    assert result['assigned_points'] == 4 and result['complete_pair_configurations'] == 0
    assert result['pairs']['pair.exposed']['primary_rate_per_second'] is None
    assert len(result['joint']['failed_replicates']) == result['joint']['requested_replicates']
    assert not arrays['pair.exposed.original_point_available'].any()
    assert result['new_native_calls'] == 0


@pytest.mark.parametrize('failed_point',(False,True))
def test_electronic_closed_export_reconstructs_originals_and_preserves_failed_points(fixture,monkeypatch,failed_point):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import electronic_ensembles as public
    from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
    from tests.test_recursive_public_service import _plane
    config,phase,rule = observed_configuration(fixture)
    fixture.electronic_config = config
    calls,_ = instrument_electronic_operator(fixture,monkeypatch,failed_point=failed_point)
    custody = acquisition.custody(fixture,config,phase)
    runner = acquisition.owner.operation_declaration(accelerated=True,observed=True).runner_factory()
    returned = runner.execute_with_native_subwork(custody.context,custody.store)
    original = acquisition.decode_canonical_bytes(returned.outputs[0].payload,
        acquisition.owner.ReferenceEquilibriumResult,maximum_bytes=acquisition.owner.MAX_RETURN)
    sources = (public.RetainedEquilibriumTrace('trace.original',config,fixture.model,phase,original,custody.store),)
    plane = _plane(fixture.tmp_path/'electronic-export')
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **k:fixture.config.provenance)
    before = tuple(calls)
    exported = public.export_electronic_ensembles(selection=rule,sources=sources,project_root=fixture.tmp_path,
        artifact_writer=plane,output_relative_path='selected/electronic')
    assert set(exported['paths']) == set(public.MEMBERS)
    reread = public.read_electronic_ensembles_export(directory_relative_path='selected/electronic',
        sources=sources,artifact_writer=plane)
    assert reread['report'] == exported['report'] and reread['evidence'] == exported['evidence']
    assert tuple(calls) == before
    assert reread['report']['complete_pair_configurations'] == (0 if failed_point else 2)
    target = plane.root.resolve('selected/electronic/report.txt',for_write=False)
    target.write_bytes(target.read_bytes()+b'changed\n')
    with pytest.raises(ArtifactIdentityConflict):
        public.read_electronic_ensembles_export(directory_relative_path='selected/electronic',
            sources=sources,artifact_writer=plane)


def test_electronic_original_mutation_during_analysis_refuses_final_return(fixture,monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import electronic_ensemble_read as owner
    from empirical_lawhood.api.domain_composition.rubisco_response import electronic_ensembles as public
    config,phase,rule = observed_configuration(fixture)
    fixture.electronic_config = config
    instrument_electronic_operator(fixture,monkeypatch)
    custody = acquisition.custody(fixture,config,phase)
    runner = acquisition.owner.operation_declaration(accelerated=True,observed=True).runner_factory()
    returned = runner.execute_with_native_subwork(custody.context,custody.store)
    original = acquisition.decode_canonical_bytes(returned.outputs[0].payload,
        acquisition.owner.ReferenceEquilibriumResult,maximum_bytes=acquisition.owner.MAX_RETURN)
    source = public.RetainedEquilibriumTrace('trace.original',config,fixture.model,phase,original,custody.store)
    analyze = owner.joint_electronic_analysis
    stream = source.native_subwork.iter_completed_output
    def changed(definition,output_id,**kwargs):
        first = True
        for block in stream(definition,output_id,**kwargs):
            if output_id == 'files.raw' and first and block:
                block = bytes((block[0]^1,))+block[1:]
                first = False
            yield block
    def during(**kwargs):
        result = analyze(**kwargs)
        monkeypatch.setattr(source.native_subwork,'iter_completed_output',changed)
        return result
    monkeypatch.setattr(owner,'joint_electronic_analysis',during)
    with pytest.raises(ValueError,match='original output changed before return'):
        public.read_electronic_ensembles(selection=rule,sources=(source,),assessor_source=fixture.model.material.sources[0])
