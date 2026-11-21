# SPDX-License-Identifier: MPL-2.0
"""Original-custody multisegment controls; no physical ensemble evidence."""

from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import weighted_path_continuation as continuation
from empirical_lawhood.domains.rubisco.rubisco_response import weighted_path_population as population
from empirical_lawhood.domains.rubisco.rubisco_response import weighted_path_resampling as resampling
from empirical_lawhood.domains.rubisco.rubisco_response import physical_path_history as history
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import PassageRegion, WeightedResamplingSelection
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from tests import test_rubisco_physical_first_passage as passage
from tests import test_rubisco_periodic_trajectory as trajectory
from tests import test_rubisco_periodic_equilibrium_acquisition as equilibrium


fixture = passage.fixture


def rule_for(selected, source, *, seed=91333, count=2):
    bins = continuation.WeightedBinMap(selected.ensembles[0].ensemble_id,
        (PassageRegion('region.progress', (D(0),), (D(10),)),), 'bin.outside')
    sampler = WeightedResamplingSelection('resampling.continuation.'+str(seed), ('bin.outside', 'region.progress'), (count,count), seed, 1024)
    rule = continuation.WeightedContinuationRule('rule.continuation.'+str(seed), selected, sampler.identity,
        (bins,), passage.ReferenceDynamicsSettings('settings.continuation', D('5e-16'), 4), 17442, 12, D('1e-9'), D('1e-9'))
    return rule, sampler


def root(fixture, monkeypatch, *, stochastic=False, event=False):
    if not stochastic:
        return passage.run_original(fixture, monkeypatch, event=event)
    config, raw, selected = passage.stochastic_selection(fixture, event=event)
    observed = equilibrium.stub_native(fixture, monkeypatch)
    custody = equilibrium.custody(fixture, config, raw)
    returned = equilibrium.owner.operation_declaration().runner_factory().execute_with_native_subwork(custody.context, custody.store)
    result = decode_canonical_bytes(returned.outputs[0].payload, equilibrium.owner.ReferenceEquilibriumResult,
        maximum_bytes=equilibrium.owner.MAX_RETURN)
    return selected, passage.retained.RetainedFirstPassagePath('path.0', config, fixture.model, raw, result, custody.store), custody, observed


def prepare(fixture, selected, source, *, count=2):
    rule, sampler = rule_for(selected, source, count=count)
    campaign = population.WeightedPathCampaign('campaign.exposed', rule, ())
    readout = population.read_weighted_path_campaign(selection=campaign, sources=(source,), assessor_source=fixture.model.material.sources[0])
    sampled = resampling.resample_weighted_paths(selection=sampler, paths=readout['paths'])
    histories = tuple(h for h, state in zip(readout['histories'], readout['paths'], strict=True) if state.disposition == 'ACTIVE')
    prepared = continuation.prepare_weighted_continuation(rule=rule, resampling=sampled,
        histories=histories, assessor_source=fixture.model.material.sources[0])
    return campaign, readout, prepared


def execute_child(fixture, source, prepared, child):
    module = equilibrium if type(child.selection) is continuation.ReferenceEquilibriumSelection else trajectory
    cf = SimpleNamespace(**vars(fixture))
    cf.tmp_path = fixture.tmp_path/child.path_id
    cf.tmp_path.mkdir()
    cf.workdir = cf.tmp_path/'native-work'
    original = replace(source.config.original, work_directory=str(cf.workdir))
    cf.config = original
    config = replace(source.config, config_id='config.'+child.path_id, original=original, selection=child.selection)
    raw = prepared['phase_bytes'][child.path_id]
    custody = module.custody(cf, config, raw)
    returned = module.owner.operation_declaration().runner_factory().execute_with_native_subwork(custody.context, custody.store)
    kind = module.owner.ReferenceEquilibriumResult if module is equilibrium else module.owner.ReferenceTrajectoryResult
    result = decode_canonical_bytes(returned.outputs[0].payload, kind, maximum_bytes=module.owner.MAX_RETURN)
    return passage.retained.RetainedFirstPassagePath(child.path_id, config, fixture.model, raw, result, custody.store)


@pytest.mark.parametrize('stochastic', (False, True))
def test_exact_descendants_keep_full_phases_clocks_run_nesting_and_original_costs(fixture, monkeypatch, stochastic):
    selected, source, _, observed = root(fixture, monkeypatch, stochastic=stochastic)
    campaign, initial, prepared = prepare(fixture, selected, source)
    assert initial['paths'][0].disposition == 'ACTIVE'
    assert len(prepared['prepared'].children) == 2
    before = len(observed)
    children = prepared['prepared'].children
    assert all(prepared['phase_bytes'][c.path_id] == prepared['parent_readouts']['path.0']['phase_bytes'] for c in children)
    assert len(observed) == before
    if stochastic:
        seeds = {c.selection.settings.random_seed for c in children}
        assert len(seeds) == 2 and source.config.selection.settings.random_seed not in seeds
    else:
        assert children[0].selection == children[1].selection  # Deterministic clones create no new randomness.
    originals = (source, *(execute_child(fixture, source, prepared, c) for c in children))
    campaign = replace(campaign, continuations=(prepared['prepared'],))
    before = len(observed)
    result = population.read_weighted_path_campaign(selection=campaign, sources=tuple(sorted(originals, key=lambda s:s.path_id)),
        assessor_source=fixture.model.material.sources[0])
    assert len(observed) == before
    assert len(result['report']['original_cost_census']) == 3
    assert all(s.physical_step == 8 and s.run_id == 'run.one' and s.weight == passage.records.PathWeight(1,2) for s in result['paths'])
    assert all(len(s.history) == 2 for s in result['paths'])
    assert all(result['arrays'][s.path_id+'.physical_steps'].tolist() == list(range(9)) for s in result['paths'])
    assert all(result['report']['path_census'][s.path_id]['boundaries'][0]['disposition'] == 'SATISFIED' for s in result['paths'])
    assert result['report']['independent_units_added'] == 0
    assert decode_canonical_bytes(campaign.canonical_bytes(), population.WeightedPathCampaign, maximum_bytes=2**24) == campaign


@pytest.mark.parametrize('change', ('phase', 'bin', 'step', 'horizon', 'allocation'))
def test_continuation_refuses_changed_phase_bin_clock_and_allocation_before_child_entry(fixture, monkeypatch, change):
    selected, source, _, observed = root(fixture, monkeypatch)
    campaign, initial, prepared = prepare(fixture, selected, source)
    rule = campaign.initial_rule
    sampled = prepared['prepared'].resampling
    if change in {'phase', 'bin', 'step'}:
        state = initial['paths'][0]
        state = replace(state, **({'phase': replace(state.phase, object_fingerprint='0'*64)} if change == 'phase'
            else {'bin_id':'bin.outside'} if change == 'bin' else {'physical_step':5}))
        sampled = resampling.resample_weighted_paths(selection=sampled.selection, paths=(state,))
    elif change == 'horizon':
        rule = replace(rule, target_physical_steps=6)
    else:
        rule = replace(rule, initial_passages=replace(selected, maximum_projection_bytes=1))
    before = len(observed)
    with pytest.raises(ValueError, match='history|endpoint|clock|bin|allocation'):
        continuation.prepare_weighted_continuation(rule=rule, resampling=sampled, histories=initial['histories'],
            assessor_source=fixture.model.material.sources[0])
    assert len(observed) == before


def test_absorbed_original_has_no_descendant_and_keeps_its_exact_weight(fixture, monkeypatch):
    selected, source, _, observed = root(fixture, monkeypatch, event=True)
    _, initial, prepared = prepare(fixture, selected, source)
    assert initial['paths'][0].disposition == 'ABSORBED'
    assert prepared['prepared'].children == () and prepared['phase_bytes'] == {}
    assert prepared['prepared'].resampling.retained_terminal_paths == initial['paths']


def test_boundary_force_discontinuity_is_independently_falsified(fixture, monkeypatch):
    selected, source, _, _ = root(fixture, monkeypatch)
    campaign, _, prepared = prepare(fixture, selected, source, count=1)
    child = execute_child(fixture, source, prepared, prepared['prepared'].children[0])
    read = history.read_physical_path
    def changed(**kwargs):
        consume = kwargs['frame_consumer']
        if kwargs['config'] == child.config:
            def altered(frame):
                consume(dict(frame, energy_hartree=frame['energy_hartree']+1))
            kwargs['frame_consumer'] = altered
        return read(**kwargs)
    monkeypatch.setattr(history, 'read_physical_path', changed)
    result = population.read_weighted_path_campaign(selection=replace(campaign, continuations=(prepared['prepared'],)),
        sources=tuple(sorted((source, child), key=lambda s:s.path_id)), assessor_source=fixture.model.material.sources[0])
    state = result['paths'][0]
    assert state.disposition == 'FAILED'
    row = result['report']['path_census'][state.path_id]
    assert row['boundaries'][0]['disposition'] == 'FALSIFIED'
    assert row['whole_history_mechanics']['disposition'] == 'FALSIFIED'


def test_supported_authoring_binds_original_receipts_and_reconstructs_full_preparation(fixture, monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import weighted_paths as public
    from tests.runtime_platform.test_native_subwork import _plane
    selected, source, _, observed = root(fixture, monkeypatch)
    _, initial, prepared = prepare(fixture, selected, source, count=1)
    plane = _plane(fixture.tmp_path/'child-authoring', binary_codecs=(trajectory.owner.PHASE_CODEC,))
    project = fixture.tmp_path/'project'
    project.mkdir()
    destination = Path(plane.root.contract.canonical_path)/'selected'
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **k:fixture.config.provenance)
    authored = []
    def author(**kwargs):
        authored.append(kwargs)
        for key, path in kwargs['input_bindings']:
            manifest = plane.read_manifest(path.relative_to(Path(plane.root.contract.canonical_path)).as_posix())
            plane.verify_manifest(manifest)
            assert len(manifest.logical.lineage_parents) == 2
        return dict(scope='EXPOSED_SHARED_AUTHOR_CONTROL')
    monkeypatch.setattr(recursive_authoring, 'author_recursive_wave', author)
    before = len(observed)
    result = public.author_weighted_continuation(prepared=prepared['prepared'], histories=initial['histories'],
        raw_sources=(fixture.sources,), project_root=project, work_directory=fixture.tmp_path/'child-native',
        artifact_writer=plane, output_dir=destination)
    assert len(observed) == before and len(authored) == 1
    assert len(result['children']) == 1 and result['new_native_calls'] == 0
    reread = public.read_weighted_continuation_preparation(relative_path='selected/preparation.json', histories=initial['histories'],
        artifact_writer=plane, maximum_bytes=2**24)
    assert reread['prepared'] == prepared['prepared']


def test_second_resampling_retains_zero_offspring_costs_and_closed_export(fixture, monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import weighted_paths as public
    from tests.runtime_platform.test_native_subwork import _plane
    selected, source, _, observed = root(fixture, monkeypatch)
    campaign, _, first = prepare(fixture, selected, source)
    originals = [source, *(execute_child(fixture, source, first, c) for c in first['prepared'].children)]
    campaign = replace(campaign, continuations=(first['prepared'],))
    middle = population.read_weighted_path_campaign(selection=campaign, sources=tuple(sorted(originals, key=lambda s:s.path_id)),
        assessor_source=fixture.model.material.sources[0])
    next_rule, sampler = rule_for(selected, source, seed=93734, count=1)
    sampled = resampling.resample_weighted_paths(selection=sampler, paths=middle['paths'])
    assert len(sampled.offspring) == 1
    next_prepared = continuation.prepare_weighted_continuation(rule=next_rule, resampling=sampled,
        histories=middle['histories'], assessor_source=fixture.model.material.sources[0])
    next_child = next_prepared['prepared'].children[0]
    parent = next(s for s in originals if s.path_id == next_child.parent_path_id)
    originals.append(execute_child(fixture, parent, next_prepared, next_child))
    campaign = replace(campaign, continuations=(*campaign.continuations, next_prepared['prepared']))
    sources = tuple(sorted(originals, key=lambda s:s.path_id))
    before = len(observed)
    final = population.read_weighted_path_campaign(selection=campaign, sources=sources, assessor_source=fixture.model.material.sources[0])
    assert final['paths'][0].disposition == 'CENSORED' and final['paths'][0].physical_step == 12
    assert final['paths'][0].weight == passage.records.PathWeight(1,1)
    assert len(final['report']['original_cost_census']) == 4
    assert len(final['report']['path_census']) == 4 and len(final['report']['populations']) == 3
    plane = _plane(fixture.tmp_path/'weighted-export')
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **k:fixture.config.provenance)
    exported = public.export_weighted_path_campaign(selection=campaign, sources=sources, project_root=fixture.tmp_path,
        artifact_writer=plane, output_relative_path='selected/weighted')
    current = public.read_weighted_path_export(directory_relative_path='selected/weighted', sources=sources, artifact_writer=plane)
    assert current['report'] == exported['report'] and len(observed) == before
    manifest = plane.read_manifest('selected/weighted/evidence.json')
    assert len(manifest.logical.lineage_parents) == 4
    with pytest.raises(ValueError, match='resampling stream'):
        replace(campaign, continuations=(campaign.continuations[0], campaign.continuations[0]))


def test_residence_confirmation_crosses_a_segment_boundary_without_reset(fixture, monkeypatch):
    selected, source, _, _ = root(fixture, monkeypatch)
    ensemble = selected.ensembles[0]
    event = replace(ensemble.events[0], region=replace(ensemble.events[0].region, lower=(D('2.4'),)), residence_steps=3)
    ensemble = replace(ensemble, entry_region=replace(ensemble.entry_region, upper=(D('2.4'),)), events=(event,))
    selected = replace(selected, ensembles=(ensemble,))
    campaign, initial, prepared = prepare(fixture, selected, source, count=1)
    assert initial['paths'][0].disposition == 'ACTIVE'
    child = execute_child(fixture, source, prepared, prepared['prepared'].children[0])
    result = population.read_weighted_path_campaign(selection=replace(campaign, continuations=(prepared['prepared'],)),
        sources=tuple(sorted((source, child), key=lambda s:s.path_id)), assessor_source=fixture.model.material.sources[0])
    path = result['paths'][0]
    assert path.disposition == 'ABSORBED'
    event = result['report']['path_census'][path.path_id]['first_event']
    assert event['entrance_step'] == 3 and event['confirmation_step'] == 6


def test_missing_descendant_retains_weight_and_cannot_become_administrative_censoring(fixture, monkeypatch):
    selected, source, _, _ = root(fixture, monkeypatch)
    campaign, _, prepared = prepare(fixture, selected, source, count=1)
    child = prepared['prepared'].children[0]
    config = replace(source.config, config_id='config.absent-descendant', selection=child.selection)
    missing = passage.retained.RetainedFirstPassagePath(child.path_id, config, source.representation,
        prepared['phase_bytes'][child.path_id], None, None)
    result = population.read_weighted_path_campaign(selection=replace(campaign, continuations=(prepared['prepared'],)),
        sources=tuple(sorted((source, missing), key=lambda s:s.path_id)), assessor_source=fixture.model.material.sources[0])
    state = result['paths'][0]
    assert state.disposition == 'MISSING' and state.physical_step == 4
    assert state.weight == passage.records.PathWeight(1,1)
    row = result['report']['statistics']['ensembles'][selected.ensembles[0].ensemble_id]['runs']['run.one']
    assert tuple(map(passage.science.fraction, row['event_probability_by_horizon_bounds']['event.product'])) == (0,1)
    assert passage.science.fraction(row['restricted_mean_first_passage_bounds_seconds'][0]) == passage.F('2e-15')
    with pytest.raises(ValueError, match='omits'):
        population.read_weighted_path_campaign(selection=replace(campaign, continuations=(prepared['prepared'],)),
            sources=(source,), assessor_source=fixture.model.material.sources[0])


def test_failed_native_finalization_cannot_start_a_new_segment(fixture, monkeypatch):
    config, raw, selected = passage.native_selection(fixture, event=False)
    observed = trajectory.stub_native(fixture, monkeypatch)
    execute = trajectory.native.execute_reference_trajectory
    def failed_finalization(**kwargs):
        execute(**kwargs)
        raise ValueError('exposed final native check failed after complete frame capture')
    monkeypatch.setattr(trajectory.native, 'execute_reference_trajectory', failed_finalization)
    custody = trajectory.custody(fixture, config, raw)
    returned = trajectory.owner.operation_declaration().runner_factory().execute_with_native_subwork(custody.context, custody.store)
    original = decode_canonical_bytes(returned.outputs[0].payload, trajectory.owner.ReferenceTrajectoryResult,
        maximum_bytes=trajectory.owner.MAX_RETURN)
    source = passage.retained.RetainedFirstPassagePath('path.0', config, fixture.model, raw, original, custody.store)
    before = len(observed)
    _, readout, prepared = prepare(fixture, selected, source)
    assert readout['paths'][0].disposition == 'FAILED'
    assert readout['paths'][0].physical_step == 4
    assert prepared['prepared'].children == () and len(observed) == before
