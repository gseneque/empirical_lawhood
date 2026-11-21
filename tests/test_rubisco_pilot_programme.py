# SPDX-License-Identifier: MPL-2.0
"""Finite pilot stages and original non-force costs; exposed software evidence."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction as F

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import pilot_programme as stages
from empirical_lawhood.domains.rubisco.rubisco_response import pilot_allocation as costs
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import fraction
from empirical_lawhood.api.domain_composition.rubisco_response import pilot_costs as public
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
from empirical_lawhood.storage.transfer_files import seal_transfer, verify_transfer
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from tests import test_rubisco_pilot_allocation as calibration
from tests import test_rubisco_paired_forecast as forecast
from tests.test_recursive_public_service import _plane


fixture = calibration.fixture
pin = calibration.pin


def source_capture(fixture, monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda *a, **k:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **k:fixture.config.provenance)


def analysis_rule(observation):
    selected = calibration.selected()
    profile = costs.PilotCostClass('class.analysis', 'COMPLETE_ANALYSIS_EXPORT', 1, D(1), observation.scope.identity,
        'Exposed complete analysis invocation at its exact selected size, implementation and environment.')
    case = costs.PilotCalibrationCase('calibration.analysis', observation.scope.scientific_selection, profile.class_id)
    work = replace(selected.candidates[0].work[0], scientific_selection=case.configuration, cost_class=profile.class_id,
        host_memory_bytes=2**40, units=2)
    candidate = replace(selected.candidates[0], work=(work,), overhead_charge=D(0))
    return replace(selected, calibrations=(case,), cost_classes=(profile,), candidates=(candidate,),
        priority=(candidate.candidate_id,), maximum_additional_projected_charge=D(1000), available_host_memory_bytes=2**41)


def measured_analysis(fixture, monkeypatch, *, fail=False):
    source_capture(fixture, monkeypatch)
    writer = _plane(fixture.tmp_path/'non-force-cost')
    selection = forecast.prepared_empty()
    if fail:
        def failed(**kwargs):
            raise ValueError('EXPOSED analysis failure; no native contact')
        monkeypatch.setattr(forecast.public, 'read_paired_forecast', failed)
    observed = public.measure_pilot_analysis_export(analysis_kind='PAIRED_FORECAST', selection=selection, sources=(),
        project_root=fixture.tmp_path, artifact_writer=writer, output_relative_path='analysis',
        observation_relative_path='measurements/original.json')['observation']
    source = public.RetainedPilotAnalysisCalibration('calibration.analysis', 'measurements/original.json', observed.identity, ())
    return writer, observed, source


def test_complete_non_force_measurement_binds_original_export_and_exact_cost(fixture, monkeypatch):
    writer, observation, source = measured_analysis(fixture, monkeypatch)
    assert observation.disposition == 'COMPLETE' and observation.cost.wall_seconds > 0
    assert observation.cost.cpu_seconds >= 0 and observation.process_peak_rss_bytes > 0
    assert len(observation.members) == 5 and observation.cost.retained_bytes == sum(m.byte_count for m in observation.members)
    rule = analysis_rule(observation)
    report = public.read_complete_pilot_allocation(selection=rule, native_sources=(), analysis_sources=(source,),
        artifact_writer=writer, assessor_source=fixture.config.provenance.identity)
    assert report['selected_candidate'] == 'candidate.a' and report['new_native_calls'] == 0
    assert fraction(report['candidates']['candidate.a']['serial_seconds']) == 2*F(observation.cost.wall_seconds)
    assert report['original_calibrations'][0]['value']['cost'] == observation.cost.to_document()
    with localcontext() as context:
        context.prec = 2
        assert public.read_complete_pilot_allocation(selection=rule, native_sources=(), analysis_sources=(source,),
            artifact_writer=writer, assessor_source=fixture.config.provenance.identity) == report
    target = writer.root.resolve('analysis/report.txt', for_write=False)
    target.write_bytes(target.read_bytes()+b'changed')
    with pytest.raises((ValueError, ArtifactIdentityConflict), match='changed|bytes|digest|size'):
        public.read_complete_pilot_allocation(selection=rule, native_sources=(), analysis_sources=(source,),
            artifact_writer=writer, assessor_source=fixture.config.provenance.identity)


def test_actual_source_analysis_measurement_retains_complete_provenance_and_rereads(tmp_path):
    from tests.test_recursive_public_service import ROOT
    writer = _plane(tmp_path/'actual-source-cost')
    measured = public.measure_pilot_analysis_export(analysis_kind='PAIRED_FORECAST', selection=forecast.prepared_empty(),
        sources=(), project_root=ROOT, artifact_writer=writer, output_relative_path='analysis',
        observation_relative_path='measurements/original.json')
    observation = measured['observation']
    assert observation.disposition == 'COMPLETE', observation.failure
    assert len(observation.producing_provenance.package_sources) > 100
    assert observation.producing_provenance.identity == observation.scope.producing_provenance
    source = public.RetainedPilotAnalysisCalibration('calibration.analysis', 'measurements/original.json', observation.identity, ())
    result = public.read_complete_pilot_allocation(selection=analysis_rule(observation), native_sources=(),
        analysis_sources=(source,), artifact_writer=writer, assessor_source=observation.producing_provenance.identity)
    assert result['selected_candidate'] == 'candidate.a' and result['new_native_calls'] == 0


def test_failed_and_missing_non_force_invocations_keep_cost_and_block_selection(fixture, monkeypatch):
    writer, observation, source = measured_analysis(fixture, monkeypatch, fail=True)
    rule = analysis_rule(observation)
    assert observation.disposition == 'FAILED' and observation.failure.startswith('ValueError:')
    report = public.read_complete_pilot_allocation(selection=rule, native_sources=(), analysis_sources=(source,),
        artifact_writer=writer, assessor_source=fixture.config.provenance.identity)
    assert report['selected_candidate'] is None
    assert fraction(report['total_original_calibration_cost']['wall_seconds']) == F(observation.cost.wall_seconds)
    missing = replace(source, observation_relative_path=None, observation=None)
    report = public.read_complete_pilot_allocation(selection=rule, native_sources=(), analysis_sources=(missing,),
        artifact_writer=writer, assessor_source=fixture.config.provenance.identity)
    assert report['selected_candidate'] is None and report['total_original_calibration_cost']['wall_seconds'] is None
    assert report['original_calibrations'][0]['value']['completed_units'] == 0


def test_force_and_non_force_costs_join_once_and_changed_scope_refuses(fixture, monkeypatch):
    _, original, _, calls = calibration.passage.run_original(fixture, monkeypatch)
    native_source = calibration.pilot_source(original)
    native_rule = calibration.native_rule(native_source)
    writer, observation, source = measured_analysis(fixture, monkeypatch)
    overhead = analysis_rule(observation)
    native_work = replace(native_rule.candidates[0].work[0], coverage=tuple(c for c in costs.COMPLETE_COVERAGE if c[1]!='assessment-export'))
    other_work = replace(overhead.candidates[0].work[0], work_id='work.export',
        coverage=tuple(c for c in costs.COMPLETE_COVERAGE if c[1]=='assessment-export'))
    candidate = replace(native_rule.candidates[0], work=tuple(sorted((native_work, other_work), key=lambda w:w.work_id)))
    rule = replace(native_rule, calibrations=tuple(sorted((*native_rule.calibrations, *overhead.calibrations), key=lambda c:c.calibration_id)),
        cost_classes=tuple(sorted((*native_rule.cost_classes, *overhead.cost_classes), key=lambda c:c.class_id)), candidates=(candidate,))
    before = len(calls)
    report = public.read_complete_pilot_allocation(selection=rule, native_sources=(native_source,), analysis_sources=(source,),
        artifact_writer=writer, assessor_source=fixture.config.provenance.identity)
    assert len(calls) == before and len(report['original_calibrations']) == 2
    assert report['selected_candidate'] == candidate.candidate_id
    assert fraction(report['total_original_calibration_cost']['wall_seconds']) == (
        F(original.original_result.completion.cost.wall_seconds)+F(observation.cost.wall_seconds))
    bad = replace(rule, cost_classes=tuple(replace(c, scope=pin('scope.wrong')) if c.class_id=='class.analysis' else c for c in rule.cost_classes))
    with pytest.raises(ValueError, match='implementation or observation'):
        public.read_complete_pilot_allocation(selection=bad, native_sources=(native_source,), analysis_sources=(source,),
            artifact_writer=writer, assessor_source=fixture.config.provenance.identity)
    with pytest.raises(ValueError, match='omits or repeats'):
        public.read_complete_pilot_allocation(selection=rule, native_sources=(native_source,), analysis_sources=(),
            artifact_writer=writer, assessor_source=fixture.config.provenance.identity)


def identity(name, schema):
    return ObjectIdentity(name, schema, '1.0.0', pin(name).object_fingerprint)


def programme():
    rule = calibration.selected(maximum_additional_projected_charge=D(1000))
    work = rule.candidates[0].work[0]
    first = replace(work, work_id='work.first', coverage=tuple(c for c in work.coverage if c[0].startswith('m1')))
    second = replace(work, work_id='work.second', scientific_selection=pin('selection.second'),
        coverage=tuple(c for c in work.coverage if c[0].startswith('v1')))
    candidate = replace(rule.candidates[0], work=(first, second))
    rule = replace(rule, candidates=(candidate,), priority=(candidate.candidate_id,))
    recipes = tuple(stages.PilotRecipeBinding(w.work_id, w.scientific_selection,
        identity('packet.'+w.work_id, 'empirical-lawhood/runtime/authored-recursive-wave'),
        identity('plan.'+w.work_id, 'empirical-lawhood/runtime/development-execution-plan'),
        (identity('task.'+w.work_id, 'empirical-lawhood/runtime/execution-task'),),
        (identity('task.'+w.work_id, 'empirical-lawhood/runtime/execution-task'),)) for w in candidate.work)
    gates = tuple(stages.PilotScientificGate('gate.'+w.work_id, 'PAIRED_FORECAST', pin('analysis.'+w.work_id), (w.work_id,)) for w in candidate.work)
    stage = (stages.PilotStage('stage.first', (first.work_id,), (), (gates[0].gate_id,)),
        stages.PilotStage('stage.second', (second.work_id,), (gates[0].gate_id,), (gates[1].gate_id,)))
    selected = stages.PilotProgrammeRule('programme.exposed', rule, candidate.candidate_id, stage, recipes, gates)
    allocation = costs.allocate_pilot(rule, (calibration.measured(rule),))
    observed = {r.work_id:{t.object_id:'COMPLETE' for t in r.tasks} for r in recipes}
    findings = {g.gate_id:'SATISFIED' for g in gates}
    return selected, allocation, observed, findings


@pytest.mark.parametrize('state,action', (
    ('UNKNOWN', 'HOLD_UNCERTAIN_CONTACT'), ('RETURNED_PENDING_PUBLICATION', 'RECOVER_RETURNED_PUBLICATION_ONLY'),
    ('FAILED', 'STOP_RETAINED_OPERATIONAL_FAILURE'), ('UNASSESSED', 'USE_EXISTING_EXECUTION_PREFLIGHT'),
))
def test_finite_stage_actions_preserve_failure_unknown_and_no_repeat_recovery(state, action):
    selected, allocation, observed, gates = programme()
    observed['work.first']['task.work.first'] = state
    report = stages.assess_pilot_progress(selected, allocation=allocation, recipes=observed, gates=gates)
    assert report['stages'][0]['action'] == action and report['stages'][1]['action'] == 'WAIT_FOR_PREDECESSOR'
    assert report['new_native_calls'] == 0 and report['native_entry_authority'] == 'NONE'


def test_scientific_stops_are_distinct_from_cost_selection_and_native_completion():
    selected, allocation, observed, gates = programme()
    complete = stages.assess_pilot_progress(selected, allocation=allocation, recipes=observed, gates=gates)
    assert complete['disposition'] == 'COMPLETE_SELECTED_STAGE_CHECKS'
    assert decode_canonical_bytes(selected.canonical_bytes(), stages.PilotProgrammeRule, maximum_bytes=2**20) == selected
    gates['gate.work.first'] = 'FALSIFIED'
    assert stages.assess_pilot_progress(selected, allocation=allocation, recipes=observed, gates=gates)['stages'][0]['action'] == 'STOP_SCIENTIFIC_FALSIFICATION'
    gates['gate.work.first'] = 'UNEVALUABLE'
    assert stages.assess_pilot_progress(selected, allocation=allocation, recipes=observed, gates=gates)['stages'][0]['action'] == 'WAIT_FOR_INDEPENDENT_ASSESSMENT'
    gates['gate.work.first'] = 'SATISFIED'
    # Exhausted/unselected future cost never asks to repeat completed work.
    allocation = dict(allocation, selected_candidate=None)
    assert stages.assess_pilot_progress(selected, allocation=allocation, recipes=observed, gates=gates)['disposition'] == 'COMPLETE_SELECTED_STAGE_CHECKS'
    observed['work.first']['task.work.first'] = 'UNASSESSED'
    assert stages.assess_pilot_progress(selected, allocation=allocation, recipes=observed, gates=gates)['stages'][0]['action'] == 'HOLD_COST_SELECTION'


def test_missing_recipes_and_circular_or_incomplete_stage_rosters_cannot_complete():
    selected, allocation, observed, gates = programme()
    selected = replace(selected, recipes=(selected.recipes[1],))
    report = stages.assess_pilot_progress(selected, allocation=allocation, recipes={'work.second':observed['work.second']}, gates=gates)
    assert report['stages'][0]['action'] == 'PREPARE_MISSING_RECIPES'
    with pytest.raises(ValueError, match='every native'):
        replace(selected, stages=(selected.stages[0],))
    with pytest.raises(ValueError, match='circular'):
        replace(selected, stages=(replace(selected.stages[0], entry_gate_ids=('gate.work.second',)), selected.stages[1]))


def test_actual_recipe_binding_retained_return_and_missing_science_use_existing_readers(fixture, monkeypatch):
    from pathlib import Path
    import shutil
    from empirical_lawhood.api import recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import periodic_trajectory, pilot_programme
    from tests import test_rubisco_periodic_trajectory as trajectory
    from tests.runtime_platform.test_native_subwork import _plane as native_plane
    source_capture(fixture, monkeypatch)
    config, phase = trajectory.trajectory(fixture)
    project = fixture.tmp_path/'project'
    project.mkdir()
    writer = native_plane(fixture.tmp_path/'authored-custody', binary_codecs=(trajectory.owner.PHASE_CODEC,))
    directory = Path(writer.root.contract.canonical_path)/'authored'
    authored = periodic_trajectory.author_reference_trajectory(selection=config.selection, prototype=fixture.selection,
        representation=fixture.model, raw_topology=fixture.raw_top, raw_coordinates=fixture.raw_xyz, phase_bytes=phase,
        project_root=project, work_directory=fixture.tmp_path/'future-native', artifact_writer=writer, output_dir=directory)
    # Missing calibration is explicit; authoring does not manufacture cost or
    # imply that a selected native task is safe to enter.
    source = calibration.retained.RetainedPilotCalibration('calibration.one', config, fixture.model, phase, None, None)
    rule = calibration.native_rule(source)
    work = replace(rule.candidates[0].work[0], scientific_selection=config.selection.identity)
    rule = replace(rule, candidates=(replace(rule.candidates[0], work=(work,)),))
    binding = pilot_programme.bind_pilot_recipe(work=work, authoring_directory=Path(authored['authoring_dir']), artifact_writer=writer)
    assert len(binding.tasks) == authored['task_count'] == 1
    gate = stages.PilotScientificGate('gate.complete', 'PAIRED_FORECAST', forecast.prepared_empty().identity, (work.work_id,))
    selected = stages.PilotProgrammeRule('programme.actual-authoring', rule, rule.candidates[0].candidate_id,
        (stages.PilotStage('stage.one', (work.work_id,), (), (gate.gate_id,)),), (binding,), (gate,))
    with pytest.raises(ValueError, match='scientific operand'):
        pilot_programme.bind_pilot_recipe(work=replace(work, scientific_selection=pin('selection.wrong')),
            authoring_directory=directory, artifact_writer=writer)
    args = dict(selection=selected, native_cost_sources=(source,), analysis_cost_sources=(),
        gate_sources=(pilot_programme.RetainedPilotGate(gate.gate_id, None, ()),), assessor_source=fixture.config.provenance.identity)
    original = pilot_programme.read_pilot_programme(**args,
        recipe_sources=(pilot_programme.RetainedPilotRecipe(work.work_id, directory),), artifact_writer=writer)
    assert original['stages'][0]['action'] == 'HOLD_COST_SELECTION' and original['new_native_calls'] == 0
    assert original['task_census'][work.work_id] == {binding.tasks[0].object_id:'UNASSESSED'}
    root = Path(writer.root.contract.canonical_path)
    manifest = fixture.tmp_path/'return-manifest.json'
    sealed = seal_transfer(root, manifest, maximum_bytes=2**26, maximum_files=10000)
    returned = native_plane(fixture.tmp_path/'returned-custody', binary_codecs=(trajectory.owner.PHASE_CODEC,))
    returned_root = Path(returned.root.contract.canonical_path)
    shutil.copytree(root, returned_root, dirs_exist_ok=True)
    assert verify_transfer(returned_root, manifest, expected_sha256=sealed['sha256'])['status'] == 'BYTE_VERIFIED'
    replayed = pilot_programme.read_pilot_programme(**args,
        recipe_sources=(pilot_programme.RetainedPilotRecipe(work.work_id, returned_root/'authored'),), artifact_writer=returned)
    assert replayed == original and replayed['physical_admission'] == 'UNEVALUABLE'
    assert verify_transfer(returned_root, manifest, expected_sha256=sealed['sha256'])['status'] == 'BYTE_VERIFIED'
    packet, _, _, _ = recursive_authoring.load_authored_wave(directory=returned_root/'authored', artifact_writer=returned)
    assert binding.authored_wave == ObjectIdentity.from_record(packet.packet_id, packet)


def test_shared_contact_observations_override_summary_and_never_imply_safe_retry():
    from empirical_lawhood.api.domain_composition.rubisco_response.pilot_programme import _task_states
    from empirical_lawhood.execution.execution import TaskBlockReason
    selected, _, _, _ = programme()
    binding = selected.recipes[0]
    task = binding.tasks[0].object_id
    report = dict(task_census=[dict(task_id=task, operational_status='BLOCKED', reason_code=TaskBlockReason.UNKNOWN_COMPLETION.value)],
        operational_census=[dict(task_id=task, attempt_id='attempt.original')])
    assert _task_states(report, binding) == {task:'UNKNOWN'}
    fact = dict(task_id=task, uncertain_contact_definition_ids=(), pending_publication_definition_ids=('original',), failed_return_definition_ids=())
    report['current_native_facts'] = (fact,)
    assert _task_states(report, binding) == {task:'RETURNED_PENDING_PUBLICATION'}
    report['native_observation_unavailable'] = (dict(attempt_id='attempt.original', reason='original unavailable'),)
    assert _task_states(report, binding) == {task:'UNKNOWN'}


def test_stage_reader_follows_real_shared_execution_recovery_and_complete_remote_return(fixture, monkeypatch):
    from pathlib import Path
    import shutil
    from empirical_lawhood.api import recursive_authoring, recursive_execution
    from empirical_lawhood.api.domain_composition.rubisco_response import pilot_programme
    from empirical_lawhood.execution.local.execution import LocalProcessExecutor
    from tests.test_recursive_public_service import _draft, ROOT
    # Reuse the established exposed RC lifecycle. It exercises real subprocess
    # execution and shared custody, not molecular or physical qualification.
    writer = _plane(fixture.tmp_path/'shared-lifecycle')
    directory = Path(writer.root.contract.canonical_path)/'authored'
    draft = _draft()
    authored = recursive_authoring.author_recursive_wave(draft=draft, project_root=ROOT,
        artifact_writer=writer, output_dir=directory)
    executed = recursive_execution.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=writer)
    assert executed['status'] == 'SUCCEEDED' and executed['new_native_contact_count'] == 2
    assert authored['task_count'] == 9
    terminal = next(iter(next(iter(executed['terminal_products'].values())).values()))['value']
    dispositions = {r['value']['variant_id']:r['value']['measurement_state'] for r in terminal['cases']}
    assert dispositions['biased'] == 'FAILED' and dispositions['missing'] == 'UNEVALUABLE'
    def forbidden(*args, **kwargs):
        pytest.fail('completed stage attempted another worker entry')
    monkeypatch.setattr(LocalProcessExecutor, 'execute', forbidden)
    recovered = recursive_execution.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=writer)
    assert recovered['new_native_contact_count'] == 0
    config, phase, _ = calibration.passage.native_selection(fixture)
    source = calibration.retained.RetainedPilotCalibration('calibration.one', config, fixture.model, phase, None, None)
    rule = calibration.native_rule(source)
    work = replace(rule.candidates[0].work[0], scientific_selection=draft.development_study.system)
    rule = replace(rule, candidates=(replace(rule.candidates[0], work=(work,)),))
    binding = pilot_programme.bind_pilot_recipe(work=work, authoring_directory=directory, artifact_writer=writer)
    assert len(binding.tasks) == 9 and len(binding.native_tasks) == 2
    gate = stages.PilotScientificGate('gate.molecular-science', 'PAIRED_FORECAST', forecast.prepared_empty().identity, (work.work_id,))
    selected = stages.PilotProgrammeRule('programme.shared-lifecycle', rule, rule.candidates[0].candidate_id,
        (stages.PilotStage('stage.original', (work.work_id,), (), (gate.gate_id,)),), (binding,), (gate,))
    args = dict(selection=selected, native_cost_sources=(source,), analysis_cost_sources=(),
        gate_sources=(pilot_programme.RetainedPilotGate(gate.gate_id, None, ()),), assessor_source=fixture.config.provenance.identity)
    original = pilot_programme.read_pilot_programme(**args,
        recipe_sources=(pilot_programme.RetainedPilotRecipe(work.work_id, directory),), artifact_writer=writer)
    # The legacy RC native effects have receipts but no prepared subwork
    # census. Keep that current-read uncertainty beside operational completion.
    task_states = original['task_census'][work.work_id]
    assert set(task_states.values()) == {'COMPLETE', 'UNKNOWN'}
    assert {task for task, value in task_states.items() if value == 'UNKNOWN'} == {t.object_id for t in binding.native_tasks}
    assert original['stages'][0]['action'] == 'HOLD_UNCERTAIN_CONTACT'
    root = Path(writer.root.contract.canonical_path)
    manifest = fixture.tmp_path/'lifecycle-return-manifest.json'
    sealed = seal_transfer(root, manifest, maximum_bytes=2**27, maximum_files=20000)
    returned = _plane(fixture.tmp_path/'returned-lifecycle')
    returned_root = Path(returned.root.contract.canonical_path)
    shutil.copytree(root, returned_root, dirs_exist_ok=True)
    assert verify_transfer(returned_root, manifest, expected_sha256=sealed['sha256'])['status'] == 'BYTE_VERIFIED'
    replayed = pilot_programme.read_pilot_programme(**args,
        recipe_sources=(pilot_programme.RetainedPilotRecipe(work.work_id, returned_root/'authored'),), artifact_writer=returned)
    assert replayed == original and replayed['new_native_calls'] == 0
    # A completed software lifecycle cannot stand in for the missing molecular
    # supplier. Its exported readout remains explicitly unevaluable.
    source_capture(fixture, monkeypatch)
    exported = forecast.public.export_paired_forecast(selection=forecast.prepared_empty(), sources=(), project_root=ROOT,
        artifact_writer=returned, output_relative_path='forecast')
    reread = forecast.public.read_paired_forecast_export(directory_relative_path='forecast', sources=(), artifact_writer=returned)
    assert reread['report'] == exported['report']
    assert all(r['conditional_forecast_status'] == 'UNEVALUABLE' for r in reread['report']['cases'].values())
