# SPDX-License-Identifier: MPL-2.0
"""Finite-distribution and original-custody controls, not physical evidence."""

from dataclasses import replace
from decimal import Decimal as D
import math

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import equilibrium_reweighting_records as records
from empirical_lawhood.domains.rubisco.rubisco_response import equilibrium_reweighting_science as science
from empirical_lawhood.domains.rubisco.rubisco_response import equilibrium_reweighting_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias import ReferenceBiasConvention
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import ReferenceBiasGeometryCriteria
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection
from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.contracts import UmbrellaWindow
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
from tests import test_rubisco_periodic_equilibrium_acquisition as acquisition


def pin(name, schema='empirical-lawhood/source/exposed-control'):
    return ObjectIdentity(name, schema, '1.0.0', 'a'*64)


def criteria(**changes):
    return replace(records.EquilibriumReweightingCriteria('criteria.exposed.reweighting', D('1e-12'), 10000,
        D(1), D(1), D('.0001'), 2, D(1), D(100), 32, 412783, D('.9'), 2**30), **changes)


def ensemble(name='ensemble.exposed', *, window=None, convention=None, prototype=None, basins=None):
    if window is None:
        window = UmbrellaWindow('window.exposed.coordinates', 'model.exposed', 'REACTANT',
            (('atom.a','atom.b'),), ('DISTANCE',), (D(1),), (D(2),), 0, 1, 1, 1, D('.1'))
    if convention is None:
        convention = ReferenceBiasConvention('convention.exposed.coordinates',
            ObjectIdentity.from_record(window.window_id, window), ('ANGSTROM',), ('KJ_PER_MOL_PER_ANGSTROM_SQUARED',),
            'DISTANCE_12_MINUS_DISTANCE_23', 'SIGNED_ORDERED_TORSION_SHORTEST_ANGULAR_RESTRAINT',
            'ORTHORHOMBIC_MINIMUM_IMAGE_EACH_CONSECUTIVE_BOND')
    return records.ReweightingEnsemble(name, prototype or pin('prototype.exposed', PeriodicProbeSelection.SCHEMA),
        D('298.15'), window, convention, basins or (
            records.EquilibriumBasin('basin.left', (D(-3),), (D(0),)),
            records.EquilibriumBasin('basin.right', (D(0),), (D(3),))))


def contrast(name, *ensembles):
    terms = []
    for item, sign in ensembles:
        terms.extend((records.BasinContrastTerm(item.ensemble_id, 'basin.left', D(-sign)),
            records.BasinContrastTerm(item.ensemble_id, 'basin.right', D(sign))))
    return records.BasinFreeEnergyContrast(name, tuple(sorted(terms, key=lambda t:(t.ensemble_id,t.basin_id))))


@pytest.mark.numerical(oracle='Exact four-state probabilities and analytic free-energy ratio log(7/3)')
def test_finite_partition_oracle_with_complete_cross_window_energies():
    selected = ensemble()
    # The two original windows have exact empirical probabilities:
    # A=(1/4,1/4,1/4,1/4), B=(1/10,2/10,3/10,4/10).
    # The target distribution is B; exp(-bias_A/kT)=(1,1/2,1/3,1/4).
    states = np.concatenate((np.repeat(np.arange(4), 25), np.repeat(np.arange(4), (10,20,30,40))))
    q = np.asarray((-2.,-1.,1.,2.))[states, None]
    thermal = science.thermal_energy(selected.temperature_kelvin)
    potentials = np.stack((thermal*np.log(np.arange(1.,5.))[states], np.zeros(len(states))))
    result, arrays = science.fit_ensemble(ensemble=selected, biases_kj_mol=potentials,
        coordinates=q, counts=(100,100), criteria=criteria())
    assert result['available'] and result['converged']
    assert result['probabilities'] == pytest.approx({'basin.left':.3,'basin.right':.7}, abs=1e-12)
    assert (result['basin_free_energies_kj_mol']['basin.right']
        -result['basin_free_energies_kj_mol']['basin.left']) == pytest.approx(-thermal*math.log(7/3), abs=1e-11)
    assert result['outside_selected_basins_probability'] == 0
    assert arrays['reduced_bias_potentials'].shape == (2,200)
    assert result['physical_rate_admission'] == 'UNEVALUABLE'
    # Adding the same arbitrary reference potential to every row leaves MBAR
    # weights unchanged; the actual implementation retains this gauge apart.
    from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.science import reweighting
    shifted = reweighting(potentials/thermal+np.linspace(-100,100,200), (100,100),
        tolerance=D('1e-12'), maximum_iterations=10000)
    assert np.asarray(shifted.normalized_weights) == pytest.approx(arrays['window_weights'], abs=1e-12)


def test_independent_estimating_equations_reject_corrupt_solver_return(monkeypatch):
    original = science.reweighting
    def altered(*args, **kwargs):
        value = original(*args, **kwargs)
        return replace(value, free_energies_reduced=(0., 1.))
    monkeypatch.setattr(science, 'reweighting', altered)
    result, _ = science.fit_ensemble(ensemble=ensemble(), biases_kj_mol=np.zeros((2,20)),
        coordinates=np.tile([[-1.],[1.]], (10,1)), counts=(10,10), criteria=criteria())
    assert not result['available']
    assert result['reason'] == 'MBAR_ESTIMATING_EQUATIONS_NOT_RESOLVED'


def test_independent_weights_reject_an_incorrect_reported_overlap(monkeypatch):
    original = science.reweighting
    def altered(*args, **kwargs):
        value = original(*args, **kwargs)
        return replace(value, overlap=((1.,0.),(0.,1.)))
    monkeypatch.setattr(science, 'reweighting', altered)
    result, _ = science.fit_ensemble(ensemble=ensemble(), biases_kj_mol=np.zeros((2,4)),
        coordinates=np.array([[-1.],[1.],[-1.],[1.]]), counts=(2,2), criteria=criteria())
    assert not result['available'] and result['maximum_overlap_disagreement'] == .5


@pytest.mark.numerical(oracle='Stationary AR(1) integrated autocorrelation (1+rho)/(1-rho) with fixed seed and declared finite-sample tolerance')
def test_correlation_estimate_retains_constant_and_correlated_series():
    rng = np.random.Generator(np.random.PCG64DXSM(9137))
    noise = rng.normal(size=20000)
    series = np.empty_like(noise)
    series[0] = noise[0]
    for i in range(1,len(series)):
        series[i] = .85*series[i-1]+noise[i]
    measured = science.statistical_inefficiency(series)
    assert measured['resolved']
    assert measured['inefficiency'] == pytest.approx((1+.85)/(1-.85), rel=.25)
    assert science.statistical_inefficiency(np.ones(100))['inefficiency'] is None
    assert science.statistical_inefficiency(np.arange(3.))['reason'] == 'TOO_FEW_SAMPLES'


def joint_selection(*, coupled=True):
    first, second = ensemble('ensemble.a'), ensemble('ensemble.b')
    traces = tuple(records.ReweightingTrace('trace.'+str(i), item.ensemble_id,
        pin('config.'+str(i), acquisition.owner.ReferenceEquilibriumConfig.SCHEMA),
        'group.paired' if coupled else 'group.'+str(i), 8, None) for i,item in enumerate((first,second)))
    contrasts = (contrast('contrast.a', (first,1)), contrast('contrast.b', (second,1)),
        contrast('contrast.difference', (first,-1),(second,1)))
    return records.EquilibriumReweightingSelection('selection.exposed.reweighting', (first,second), traces,
        contrasts, criteria(), pin('dependence.exposed'), ('Exposed coupled numerical controls only.',))


def test_joint_block_draws_preserve_paired_covariance_and_signed_difference():
    selected = joint_selection()
    rng = np.random.Generator(np.random.PCG64DXSM(89))
    coordinates = rng.choice((-2.,-1.,1.,2.), size=(256,1))
    tables = {t.trace_id:dict(coordinates=coordinates.copy(), reference_energy_kj_mol=coordinates[:,0]**2)
        for t in selected.traces}
    result, _ = science.joint_block_analysis(selection=selected, tables=tables, windows={t.trace_id:None for t in selected.traces})
    draws = np.asarray(result['bootstrap']['joint_contrasts_kj_mol'])
    assert np.array_equal(draws[:,0], draws[:,1]) and np.all(draws[:,2] == 0)
    assert result['bootstrap']['failed_replicates'] == []
    covariance = np.asarray(result['bootstrap']['covariance_kj_mol_squared'])
    assert covariance[0,0] > 0 and covariance[0,0] == covariance[0,1]
    assert result['bootstrap']['retained_replicates'] == 32
    assert len(result['bootstrap']['block_starts']['group.paired']) == 32
    assert result['physical_rate_admission'] == 'UNEVALUABLE'
    independent, _ = science.joint_block_analysis(selection=joint_selection(coupled=False), tables=tables,
        windows={t.trace_id:None for t in selected.traces})
    assert independent['bootstrap']['covariance_kj_mol_squared'][2][2] > 0


def test_missing_window_and_failed_bootstrap_never_shrink_denominator():
    selected = joint_selection()
    tables = {'trace.0':dict(coordinates=np.tile([[-1.],[1.]],(16,1)),reference_energy_kj_mol=np.zeros(32)),
        'trace.1':dict(coordinates=np.empty((0,1)),reference_energy_kj_mol=np.empty(0))}
    result, _ = science.joint_block_analysis(selection=selected, tables=tables, windows={t.trace_id:None for t in selected.traces})
    assert len(result['ensembles']) == 2
    assert result['ensembles']['ensemble.b']['counts'] == (0,)
    assert result['contrasts_kj_mol'][1:] == (None,None)
    assert len(result['bootstrap']['failed_replicates']) == result['bootstrap']['requested_replicates'] == 32
    assert result['bootstrap']['simultaneous_intervals_kj_mol'] is None
    assert result['selected_numerical_sampling_criteria'] != 'SATISFIED'


def test_typed_selection_preserves_decimal_bytes_and_rejects_gauge_or_overlap():
    selected = joint_selection()
    assert decode_canonical_bytes(selected.canonical_bytes(), type(selected), maximum_bytes=2**20) == selected
    first = selected.ensembles[0]
    with pytest.raises(ValueError, match='overlap'):
        replace(first, basins=(first.basins[0], replace(first.basins[1], lower=(D(-1),))))
    with pytest.raises(ValueError, match='gauge'):
        replace(selected.contrasts[0], terms=tuple(replace(t, coefficient=D(1)) for t in selected.contrasts[0].terms))


def test_decimal_thresholds_do_not_round_to_pass_at_binary64_equality():
    selected = criteria(minimum_target_weight_ess=D('4.000000000000000000001'),
        minimum_window_weight_ess=D('4.000000000000000000001'), minimum_overlap=D('.500000000000000000001'))
    result, _ = science.fit_ensemble(ensemble=ensemble(), biases_kj_mol=np.zeros((2,4)),
        coordinates=np.array([[-1.],[1.],[-1.],[1.]]), counts=(2,2), criteria=selected)
    assert result['target_weight_effective_samples'] == 4
    assert set(result['selected_criteria_failures']) == {'WINDOW_WEIGHT_ESS_BELOW_SELECTION',
        'TARGET_WEIGHT_ESS_BELOW_SELECTION','OVERLAP_GRAPH_DISCONNECTED_AT_SELECTED_THRESHOLD'}


def test_joint_quantile_rank_uses_the_exact_decimal_coverage():
    selected = joint_selection()
    selected = replace(selected, criteria=replace(selected.criteria, bootstrap_replicates=9,
        simultaneous_coverage=D('.30000000000000000000001')))
    q = np.tile([[-1.],[1.]],(32,1))
    tables = {t.trace_id:dict(coordinates=q,reference_energy_kj_mol=np.ones(len(q))) for t in selected.traces}
    result, _ = science.joint_block_analysis(selection=selected, tables=tables, windows={t.trace_id:None for t in selected.traces})
    assert result['bootstrap']['simultaneous_quantile_rank'] == 4


fixture = acquisition.fixture


def original_selection(fixture, config):
    original = config.selection
    basins = (records.EquilibriumBasin('basin.left', (D(-100),)*3, (D(0),D(100),D(100))),
        records.EquilibriumBasin('basin.right', (D(0),D(-100),D(-100)), (D(100),)*3))
    item = ensemble(window=original.window, convention=original.convention,
        prototype=config.original.selection.identity, basins=basins)
    limits = ReferenceBiasGeometryCriteria('criteria.exposed.reweighting-geometry', original.convention.identity,
        D('1e-5'), (D('1e-10'),)*3, (D('1e-7'),)*3, (D('1e-7'),)*3, D('1e-9'), D('1e-6'), D('1e-6'))
    trace = records.ReweightingTrace('trace.original', item.ensemble_id, config.identity, 'group.original', 1, limits)
    return records.EquilibriumReweightingSelection('selection.exposed.original-reweighting', (item,), (trace,),
        (contrast('contrast.original', (item,1)),), criteria(), fixture.model.material.sources[0],
        ('Exposed complete original native transport; no enzyme equilibrium claim.',))


def run_original(fixture, monkeypatch, *, failure=None):
    config, phase = acquisition.trajectory(fixture)
    observed = acquisition.stub_native(fixture, monkeypatch, failure=failure)
    custody = acquisition.custody(fixture, config, phase)
    runner = acquisition.owner.operation_declaration().runner_factory()
    returned = runner.execute_with_native_subwork(custody.context, custody.store)
    original = decode_canonical_bytes(returned.outputs[0].payload, acquisition.owner.ReferenceEquilibriumResult,
        maximum_bytes=acquisition.owner.MAX_RETURN)
    return config, phase, observed, custody, original


def test_original_custody_projection_makes_no_new_force_or_producing_bias_calls(fixture, monkeypatch):
    config, phase, observed, custody, original = run_original(fixture, monkeypatch)
    selected = original_selection(fixture, config)
    before = len(observed)
    from empirical_lawhood.domains.rubisco.rubisco_response import periodic_bias
    monkeypatch.setattr(periodic_bias, 'evaluate_reference_umbrella_bias', lambda **k:pytest.fail('producing bias was called'))
    source = retained.RetainedEquilibriumTrace('trace.original', config, fixture.model, phase, original, custody.store)
    report, arrays = retained.read_equilibrium_reweighting(selection=selected, sources=(source,),
        assessor_source=fixture.model.material.sources[0])
    trace = report['trace_census']['trace.original']
    assert trace['eligible_for_complete_window_fit']
    assert trace['retained_projected_samples'] == trace['expected_samples'] == 2
    assert arrays['trace.original.evaluations'].tolist() == [3,4]
    assert arrays['trace.original.reference_energy_hartree'].shape == (2,)
    assert arrays['ensemble.exposed.bias_potentials_kj_mol'].shape == (1,2)
    assert len(observed) == before and report['new_reference_evaluations'] == 0
    assert report['statistics']['physical_rate_admission'] == 'UNEVALUABLE'
    assert report['statistics']['selected_numerical_sampling_criteria'] != 'SATISFIED'


def test_absent_original_retains_selected_trace_without_claiming_nonentry(fixture):
    config, phase = acquisition.trajectory(fixture)
    selected = original_selection(fixture, config)
    source = retained.RetainedEquilibriumTrace('trace.original', config, fixture.model, phase, None, None)
    report, arrays = retained.read_equilibrium_reweighting(selection=selected, sources=(source,),
        assessor_source=fixture.model.material.sources[0])
    assert report['assigned_traces'] == 1 and report['supplied_results'] == 0
    assert report['trace_census']['trace.original']['disposition'] == 'NOT_SUPPLIED'
    assert arrays['trace.original.coordinates'].shape == (0,3)
    assert report['statistics']['bootstrap']['simultaneous_intervals_kj_mol'] is None


def test_workspace_and_reference_substitution_refuse_before_original_contact(fixture):
    config, phase = acquisition.trajectory(fixture)
    selected = original_selection(fixture, config)
    source = retained.RetainedEquilibriumTrace('trace.original', config, fixture.model, phase, None, None)
    with pytest.raises(ValueError, match='workspace'):
        retained.validate_reweighting_inputs(replace(selected, criteria=replace(selected.criteria, maximum_workspace_bytes=1)), (source,))
    with pytest.raises(ValueError, match='reference model'):
        retained.validate_reweighting_inputs(replace(selected, ensembles=(replace(selected.ensembles[0],
            prototype=pin('prototype.substituted', PeriodicProbeSelection.SCHEMA)),)), (source,))


def test_failed_original_preserves_prefix_and_cost_without_filling_missing_samples(fixture, monkeypatch):
    config, phase, observed, custody, original = run_original(fixture, monkeypatch, failure='native')
    selected = original_selection(fixture, config)
    before = len(observed)
    source = retained.RetainedEquilibriumTrace('trace.original', config, fixture.model, phase, original, custody.store)
    report, arrays = retained.read_equilibrium_reweighting(selection=selected, sources=(source,),
        assessor_source=fixture.model.material.sources[0])
    trace = report['trace_census']['trace.original']
    assert trace['disposition'] == 'ORIGINAL_FAILED'
    assert not trace['eligible_for_complete_window_fit']
    assert trace['original_completion'] == original.completion.to_document()
    assert trace['retained_projected_samples'] < trace['expected_samples']
    assert arrays['trace.original.all_window_bias_potentials_kj_mol'].shape[0] == 1
    assert report['statistics']['ensembles']['ensemble.exposed']['counts'] == (0,)
    assert report['statistics']['contrasts_kj_mol'] == (None,)
    assert len(observed) == before


def test_closed_public_export_retains_original_receipts_and_independent_reconstruction(fixture, monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import equilibrium_reweighting as public
    from tests.test_recursive_public_service import _plane
    config, phase, observed, custody, original = run_original(fixture, monkeypatch)
    selected = original_selection(fixture, config)
    source = retained.RetainedEquilibriumTrace('trace.original', config, fixture.model, phase, original, custody.store)
    plane = _plane(fixture.tmp_path/'analysis-custody')
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **k:fixture.config.provenance)
    before = len(observed)
    exported = public.export_equilibrium_reweighting(selection=selected, sources=(source,),
        project_root=fixture.tmp_path, artifact_writer=plane, output_relative_path='selected/reweighting')
    assert set(exported['paths']) == set(public.MEMBERS)
    reread = public.read_equilibrium_reweighting_export(directory_relative_path='selected/reweighting', sources=(source,), artifact_writer=plane)
    assert reread['evidence'] == exported['evidence']
    assert reread['report'] == exported['report']
    assert len(observed) == before
    with pytest.raises(ValueError, match='fresh'):
        public.export_equilibrium_reweighting(selection=selected, sources=(source,), project_root=fixture.tmp_path,
            artifact_writer=plane, output_relative_path='selected/reweighting')
    # A closed sibling cannot be changed while leaving its selection intact.
    target = plane.root.resolve('selected/reweighting/report.txt', for_write=False)
    target.write_bytes(target.read_bytes()+b'altered\n')
    with pytest.raises(ArtifactIdentityConflict):
        public.read_equilibrium_reweighting_export(directory_relative_path='selected/reweighting', sources=(source,), artifact_writer=plane)


def test_selected_shared_noise_cannot_be_relabelled_as_independent(fixture):
    config, phase = acquisition.trajectory(fixture)
    selected = original_selection(fixture, config)
    other = replace(config, config_id='config.exposed.second-equilibrium')
    traces = (selected.traces[0], replace(selected.traces[0], trace_id='trace.other', configuration=other.identity,
        resampling_group_id='group.other'))
    selected = replace(selected, traces=traces)
    sources = (retained.RetainedEquilibriumTrace('trace.original', config, fixture.model, phase, None, None),
        retained.RetainedEquilibriumTrace('trace.other', other, fixture.model, phase, None, None))
    with pytest.raises(ValueError, match='random streams'):
        retained.validate_reweighting_inputs(selected, sources)


def test_two_actual_window_returns_supply_the_complete_cross_potential_matrix(fixture, monkeypatch):
    from types import SimpleNamespace
    config, phase, _, custody, original = run_original(fixture, monkeypatch)
    second = SimpleNamespace(**vars(fixture))
    second.tmp_path = fixture.tmp_path/'second'
    second.tmp_path.mkdir()
    second.workdir = second.tmp_path/'native'
    second.config = replace(fixture.config, config_id='config.exposed.other-probe', work_directory=str(second.workdir))
    other, other_phase = acquisition.trajectory(second)
    window = replace(other.selection.window, window_id='window.exposed.other', centers=(D('.9'),)*3)
    convention = replace(other.selection.convention, convention_id='convention.exposed.other',
        window=ObjectIdentity.from_record(window.window_id, window))
    settings = replace(other.selection.settings, settings_id='settings.exposed.other',
        bias_window=convention.window, bias_convention=convention.identity)
    xyz, velocity, _ = acquisition.selected.read_equilibrium_phase_space(other.selection, second.model, other_phase)
    selection, other_phase = acquisition.selected.prepare_reference_equilibrium(prototype=second.selection,
        representation=second.model, phase_source=other.selection.phase_source, initial_angstrom=xyz,
        initial_velocity_nm_per_ps=velocity, settings=settings, criteria=other.selection.criteria,
        density_guess_policy='COLD', window=window, convention=convention)
    other = replace(other, config_id='config.exposed.other-equilibrium', selection=selection)
    acquisition.stub_native(second, monkeypatch)
    other_custody = acquisition.custody(second, other, other_phase)
    returned = acquisition.owner.operation_declaration().runner_factory().execute_with_native_subwork(
        other_custody.context, other_custody.store)
    other_result = decode_canonical_bytes(returned.outputs[0].payload, acquisition.owner.ReferenceEquilibriumResult,
        maximum_bytes=acquisition.owner.MAX_RETURN)
    selected = original_selection(fixture, config)
    trace = selected.traces[0]
    other_trace = replace(trace, trace_id='trace.other', configuration=other.identity,
        bias_geometry_criteria=replace(trace.bias_geometry_criteria, criteria_id='criteria.exposed.other-geometry',
            convention=convention.identity))
    selected = replace(selected, traces=(trace,other_trace))
    sources = (retained.RetainedEquilibriumTrace('trace.original', config, fixture.model, phase, original, custody.store),
        retained.RetainedEquilibriumTrace('trace.other', other, second.model, other_phase, other_result, other_custody.store))
    report, arrays = retained.read_equilibrium_reweighting(selection=selected, sources=sources,
        assessor_source=fixture.model.material.sources[0])
    assert report['complete_window_traces'] == report['assigned_traces'] == 2
    assert report['statistics']['ensembles']['ensemble.exposed']['counts'] == (2,2)
    assert arrays['ensemble.exposed.bias_potentials_kj_mol'].shape == (2,4)
    for trace in selected.traces:
        cross = arrays[trace.trace_id+'.all_window_bias_potentials_kj_mol']
        assert cross.shape == (2,2) and np.all(cross[0] != cross[1])
        assert report['trace_census'][trace.trace_id]['cross_window_trace_order'] == ('trace.original','trace.other')


def test_original_mutation_during_fitting_refuses_the_final_return(fixture, monkeypatch):
    config, phase, _, custody, original = run_original(fixture, monkeypatch)
    selected = original_selection(fixture, config)
    source = retained.RetainedEquilibriumTrace('trace.original', config, fixture.model, phase, original, custody.store)
    analyze = retained.joint_block_analysis
    original_iter = custody.store.iter_completed_output
    def altered(definition, output_id, **kwargs):
        first = True
        for block in original_iter(definition, output_id, **kwargs):
            if output_id == 'files.raw' and first and block:
                block = bytes((block[0] ^ 1,))+block[1:]
                first = False
            yield block
    def during_fit(**kwargs):
        result = analyze(**kwargs)
        monkeypatch.setattr(custody.store, 'iter_completed_output', altered)
        return result
    monkeypatch.setattr(retained, 'joint_block_analysis', during_fit)
    with pytest.raises(ValueError, match='original output changed before return'):
        retained.read_equilibrium_reweighting(selection=selected, sources=(source,),
            assessor_source=fixture.model.material.sources[0])


def test_cross_window_diagonal_must_match_the_original_bias_return(fixture, monkeypatch):
    config, phase, _, custody, original = run_original(fixture, monkeypatch)
    selected = original_selection(fixture, config)
    source = retained.RetainedEquilibriumTrace('trace.original', config, fixture.model, phase, original, custody.store)
    project = retained.cross_window_biases
    monkeypatch.setattr(retained, 'cross_window_biases', lambda *args:project(*args)+1.)
    report, arrays = retained.read_equilibrium_reweighting(selection=selected, sources=(source,),
        assessor_source=fixture.model.material.sources[0])
    trace = report['trace_census']['trace.original']
    assert not trace['eligible_for_complete_window_fit']
    assert 'CROSS_WINDOW_ORIGINAL_BIAS_DIAGONAL_FALSIFIED' in trace['reasons']
    assert report['statistics']['selected_numerical_sampling_criteria'] == 'FALSIFIED'
    assert arrays['trace.original.original_bias_energy_kj_mol'].shape == (2,)
