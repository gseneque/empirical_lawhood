# SPDX-License-Identifier: MPL-2.0
"""Disclosed software controls for the root's ordinary recursive lifecycle."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import initial_root_experiment as experiment
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model import required_initial_sources
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import InitialJointSupportReview
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root import prepare_initial_root
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_operation import operation_declarations
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_policy import initial_root_inquiry_specification
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootAnalysisInputs, InitialRootReviewInputs
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import initial_root_requirement_graph
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_translation import initial_root_draft, initial_root_origins
from empirical_lawhood.api.domain_composition.rubisco_response.initial_root_inquiry import project_initial_root_inquiry
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.experiment_preparation import ExecutionSelection
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from tests.test_rubisco_initial_model import support

ROOT = Path(__file__).resolve().parents[1]


def disclosed_analysis(values=(2, 3, 1, 1)):
    model, inputs, records, reviews = support(values)
    frozen = InitialRootReviewInputs(model.identity, inputs.identity, required_initial_sources(model, inputs),
        tuple(sorted(reviews, key=lambda row: row.review_id)),
        tuple(row for row in records if type(row) is InitialJointSupportReview))
    return InitialRootAnalysisInputs(prepare_initial_root(model=model), model, inputs, frozen)


def test_root_acquisition_keeps_conditional_omissions_separate_from_unproved_native_savings():
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root import calculate_initial_root, assess_initial_root
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_acquisition import InitialRootForceScenario, assess_initial_root_acquisition
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import analysis_arguments
    from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
    from empirical_lawhood.execution.work_costs import CostWorkScope, WorkCostAccount, WorkCostOutcome, record_cost_evidence

    analysis = disclosed_analysis((1, 1, None, None))
    arguments = analysis_arguments(analysis)
    result = calculate_initial_root(**arguments)
    assessment = assess_initial_root(result=result, **arguments)
    evidence = record_cost_evidence(result, evidence_id='cost.control', object_id=result.result_id,
        description='Disclosed software control with no native observation or measured cost.')
    work = CostWorkScope('work.control', evidence.record_identity, evidence.evidence_id, (evidence.evidence_id,),
        WorkCostOutcome.OBSERVED_INVOCATION, 'Only the exposed calculation; expense unmeasured.')
    account = WorkCostAccount('account.control', 'Disclosed control, not an actual molecular campaign.', (evidence,), (work,), ())
    scenario = InitialRootForceScenario('scenario.control', 'Illustrative four-call workload with unmeasured preparation.', 4,
        (Exact.of(500), Exact.of(600)), Exact.of('3.99'), (evidence.identity,),
        ('Historical performance is assumed unchanged solely for this disclosed arithmetic control.',), ())
    report = assess_initial_root_acquisition(analysis=analysis, result=result, assessment=assessment,
        measured_account=account, scenarios=(scenario,))
    assert report['joint_outcome'] == 'CONTRADICTED'
    assert report['decision_specific_omissions']
    assert report['demonstrated_avoided_native_calls'] == 0 and report['demonstrated_net_saving'] is None
    forecast, = report['scenarios']
    assert forecast['full_delivery_cost'] is None and not forecast['execution_authorized']
    assert forecast['historical_rate_usd'] == ({'numerator': 133, 'denominator': 60}, {'numerator': 133, 'denominator': 50})
    unknown = replace(scenario, complete_force_calls=None)
    assert assess_initial_root_acquisition(analysis=analysis, result=result, assessment=assessment,
        measured_account=account, scenarios=(unknown,))['scenarios'][0]['historical_rate_usd'] is None
    with pytest.raises(ValueError, match='prerequisite scope'):
        assess_initial_root_acquisition(analysis=analysis, result=result, assessment=assessment,
            measured_account=account, scenarios=(replace(scenario, unpriced_requirement_ids=('invented.prerequisite',)),))
    with pytest.raises(ValueError, match='original cost sources'):
        assess_initial_root_acquisition(analysis=analysis, result=result, assessment=assessment,
            measured_account=account, scenarios=(replace(scenario, observation_sources=(analysis.identity,)),))


@pytest.mark.parametrize('values,expected_missing', [((2, 3, 1, 1), False), ((None, None, None, None), True)])
def test_root_prerequisites_are_receiver_driven_and_optional_suppliers_do_not_expand_target(values, expected_missing):
    analysis = disclosed_analysis(values)
    graph = initial_root_requirement_graph(analysis)
    draft = initial_root_draft(analysis)
    spec = initial_root_inquiry_specification(draft)
    assert len(graph.suppliers) == 5 and all(not row.selected for row in graph.suppliers)
    root = next(row for row in graph.requirements if row.requirement_id == graph.root_requirement_id)
    assert len(root.further_requirement_ids) > 1 if expected_missing else len(root.further_requirement_ids) == 1
    assert spec.target.required_requirement_ids == root.further_requirement_ids
    assert not any('matrix' in row.requirement_id or 'benefit' in row.requirement_id for row in spec.requirements)
    assert set(spec.required_requirement_closure) == {row.requirement_id for row in spec.requirements}
    declarations = operation_declarations()
    compiled = compile_recursive_wave(draft=draft, registrations=tuple(row.registration() for row in declarations),
        registry=CapabilityRegistry('test.root.registry', tuple(sorted((row.manifest() for row in declarations), key=lambda row: row.registry_id))),
        implementation_commit='a' * 40, output_codecs=declarations[0].record_codecs)
    assert len(compiled.execution_plan.tasks) == 2
    assert all(not row.execution_properties.native_effect for row in declarations)


def test_preparation_preserves_source_census_and_exposed_groups_before_any_worker(tmp_path):
    analysis = disclosed_analysis()
    spec = experiment.initial_root_experiment_specification(analysis)
    bound = experiment.bind_inputs(spec, {'analysis': analysis})
    missing = experiment.prepare(spec, scientific_inputs=bound.scientific_inputs, method_inputs=bound.method_inputs,
        execution=ExecutionSelection())
    assert not missing.executable and len(missing.dependencies) == 4
    prepared = experiment.prepare(spec, scientific_inputs=bound.scientific_inputs, method_inputs=bound.method_inputs,
        execution=ExecutionSelection(workers=4, environment_id='rubisco-prediction', output_root=str(tmp_path),
            source_snapshot=ObjectIdentity('test.source', 'empirical-lawhood/testing/source', '1.0.0', 'a' * 64)))
    assert prepared.executable and prepared.census.native_effect_count == 0
    assert all(row.exposed for row in prepared.allocation.units)
    experiment.validate_instance(specification=spec, allocation=prepared.allocation, draft=prepared.draft,
        source_records=prepared.design_records)
    for changed in (replace(spec, analysis=replace(spec.analysis, object_fingerprint='b' * 64)),
            replace(spec, expected_case_ids=('substituted',)), replace(spec, expected_exposure_groups=('fresh',))):
        with pytest.raises(ValueError, match='source, consumer, exposure'):
            experiment.bind_inputs(changed, {'analysis': analysis})
    with pytest.raises(ValueError, match='post-outcome'):
        project_initial_root_inquiry(directory=tmp_path, artifact_writer=None,
            information_cutoff=InformationCutoff('test.cutoff', 'clock.rubisco.declared-rate-closure', CausalPhase.PRE_ACTION, None))


@pytest.mark.parametrize('values,outcome,decision', [
    ((2, 3, 1, 1), 'SUPPORTED', 'independent-check'),
    ((1, 1, None, None), 'CONTRADICTED', 'close-branch'),
    ((None, None, None, None), 'UNRESOLVED', 'hold'),
])
def test_public_root_run_read_contribution_and_inquiry_preserve_scientific_outcome(tmp_path, monkeypatch, values, outcome, decision):
    from empirical_lawhood.api import recursive_authoring as author, recursive_execution as execute, recursive_inquiry as inquiry
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.recursive_contributions import export_recursive_contribution, authenticate_recursive_contribution
    from empirical_lawhood.execution.local.execution import LocalProcessExecutor
    from tests.test_rubisco_gas_contrast import _real_plane

    # Actual guarded local custody and workers; the input values above are
    # disclosed algebra controls and never molecular observations.
    root = tmp_path / 'actual-custody'
    plane = _real_plane(root)
    source = author.implementation_binding(ROOT)
    analysis = disclosed_analysis(values)
    spec = experiment.initial_root_experiment_specification(analysis)
    bound = experiment.bind_inputs(spec, {'analysis': analysis})
    service = ExperimentProgrammeService(ROOT, plane)
    preparation = service.prepare(spec, scientific_inputs=bound.scientific_inputs, method_inputs=bound.method_inputs,
        execution=ExecutionSelection(workers=1, environment_id='rubisco-prediction', output_root=str(root),
            source_snapshot=ObjectIdentity.from_record('recursive-member.implementation', source)))
    wave = root / 'root-wave'
    assert service.author(preparation=preparation, output_dir=wave)['status'] == 'AUTHORED'
    report = service.run(directory=wave, maximum_parallel_tasks=1)
    assert report['status'] == 'SUCCEEDED' and report['new_native_contact_count'] == 0
    _, products, draft, _ = execute.read_recursive_wave(directory=wave, artifact_writer=plane, include_products=True)
    assert len(products['connection_assessments']) == 4
    result = next(record.result for rows in products['records'].values() for record in rows.values() if hasattr(record, 'result'))
    assert result.joint_outcome == outcome
    read = service.read(directory=wave)
    assert read['terminal_products'] == report['terminal_products']
    exported = export_recursive_contribution(directory=wave, output_dir=root / 'contribution', project_root=ROOT, artifact_writer=plane)
    assert exported['status'] == 'EXPORTED'
    parent = authenticate_recursive_contribution(directory=root / 'contribution', artifact_writer=plane)[2]
    assert len(parent.products) == 2
    projected = project_initial_root_inquiry(directory=wave, artifact_writer=plane,
        information_cutoff=InformationCutoff('test.root.post-outcome', 'clock.rubisco.declared-rate-closure', CausalPhase.POST_OUTCOME, None))
    assert len(projected.state.operational_census) == 2
    assert all(not row.independent_unit_ids for row in projected.state.stock)
    kwargs = dict(specification=projected.specification, state=projected.state, sources=projected.sources,
        menu=projected.menu, policy=projected.policy, campaign=draft.campaign,
        right=draft.campaign.decision_rights[0], actor_id='owner.local-researcher', project_root=ROOT, artifact_writer=plane)
    _, records = inquiry.commit_inquiry_decision(**kwargs, output_dir=root / 'decision')
    assert records['decision.json'].selected_alternative_id == decision
    assert bool(records['decision.json'].unresolved_target_claim_ids) == (outcome != 'SUPPORTED')
    assert inquiry.read_inquiry_decision(directory=root / 'decision', artifact_writer=plane)[1] == records
    if outcome == 'SUPPORTED':
        _accept_successor(root, plane, wave, analysis, projected)
    else:
        assert projected.successor is None
        with pytest.raises(ValueError, match='successor builder'):
            inquiry.preview_inquiry_successor(supplier_directory=wave, artifact_writer=plane)
    def no_worker(*args, **kwargs):
        raise AssertionError('retained read/recovery entered a worker')
    monkeypatch.setattr(LocalProcessExecutor, 'execute', no_worker)
    assert service.recover(directory=wave, maximum_parallel_tasks=1) == report
    assert service.read(directory=wave)['terminal_products'] == report['terminal_products']


def _accept_successor(root, plane, wave, analysis, projected):
    from empirical_lawhood.api import recursive_inquiry as inquiry
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import read_recursive_wave
    from tests.test_robust_inquiry_acceptance import publish_sources

    successor = inquiry.preview_inquiry_successor(supplier_directory=wave, artifact_writer=plane)
    assert successor == projected.successor
    origins = initial_root_origins(successor)
    # Ordinary authoring materialization retains the original SOURCE input;
    # contribution custody supplies the two original result products.
    original = load_authored_wave(directory=wave, artifact_writer=plane)
    bindings = publish_sources(plane, successor, (analysis,))
    inquiry.author_inquiry_successor(decision_directory=root / 'decision', supplier_directory=wave,
        origins=origins, input_bindings=bindings, contribution_dir=root / 'contribution',
        project_root=ROOT, artifact_writer=plane, output_dir=root / 'reuse')
    assert inquiry.read_inquiry_successor(directory=root / 'reuse', artifact_writer=plane)
    report = inquiry.run_inquiry_successor(directory=root / 'reuse', project_root=ROOT, artifact_writer=plane)
    assert report['status'] == 'SUCCEEDED' and report['new_native_contact_count'] == 0
    _, products, used, _ = read_recursive_wave(directory=root / 'reuse', artifact_writer=plane, include_products=True)
    assert len(products['records']) == 1 and len(products['connection_assessments']) == 4
    assert used.contribution_parents == successor.contribution_parents
    final = project_initial_root_inquiry(directory=root / 'reuse', artifact_writer=plane,
        information_cutoff=InformationCutoff('test.root.reuse-post-outcome', 'clock.rubisco.declared-rate-closure', CausalPhase.POST_OUTCOME, None))
    _, closed = inquiry.commit_inquiry_decision(specification=final.specification, state=final.state,
        sources=final.sources, menu=final.menu, policy=final.policy, campaign=used.campaign,
        right=used.campaign.decision_rights[0], actor_id='owner.local-researcher', project_root=ROOT,
        artifact_writer=plane, output_dir=root / 'reuse-final-decision')
    assert closed['decision.json'].selected_alternative_id == 'stop-target'
    assert not closed['decision.json'].unresolved_target_claim_ids
    assert load_authored_wave(directory=wave, artifact_writer=plane)[0] == original[0]
    parent = successor.contribution_parents[0]
    changed = disclosed_analysis((1, 1, 1, 1))
    with pytest.raises(ValueError, match='original contribution'):
        initial_root_draft(changed, parent=parent)
    changed_consumer = replace(analysis, request=prepare_initial_root(model=analysis.model,
        alternative_policy='ROBUST_FOR_EVERY_SELECTED_ALTERNATIVE'))
    with pytest.raises(ValueError, match='original contribution'):
        initial_root_draft(changed_consumer, parent=parent)
