# SPDX-License-Identifier: MPL-2.0
"""Current frontier and bounded orchestration controls; no science execution."""
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import (
    PHASES, MatrixProgrammeObservation, programme_frontier,
)
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import (
    MatrixProgrammeAuthoritySelection, MatrixProgrammeOperationSelection,
    MatrixResearchProgrammePlan, MatrixResearchProgrammeSpecification,
)
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_recursive_public_service import _plane
from tests.test_matrix_finite_dt_source_assembly import c_backed_source_case  # noqa: F401

from empirical_lawhood.api.matrix_researcher_programme import (
    MatrixResearchProgrammeService, _disposition_denominators, _disposition_facts,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes


ROOT = Path(__file__).parents[1]


def _execution(plane):
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    return ExecutionSelection(4, 'environment.disclosed-matrix-programme',
        ObjectIdentity.from_record('recursive-member.implementation', implementation_binding(ROOT)),
        plane.root.contract.canonical_path)


def observation(phase, *, complete=True, trigger=None, **report):
    return MatrixProgrammeObservation(phase, {'status': 'SUCCEEDED', **report}, complete, trigger)


def test_initial_frontier_has_only_independent_e1_e2_and_train():
    frontier = programme_frontier({}, downstream_account='ORIGINAL_E3')
    assert frontier.eligible == ('e1', 'e2', 'train')
    assert not frontier.complete and not frontier.unentered
    assert 'e3' in dict(frontier.waiting)
    assert not any('structure' in phase for phase in PHASES)


def test_adverse_completed_train_advances_but_uncertain_custody_does_not():
    complete = observation('train', scientific_status='PRIMARY_NONSUCCESS')
    assert 'e3' in programme_frontier({'train': complete}, downstream_account='ORIGINAL_E3').eligible
    uncertain = observation('train', complete=False, status='BLOCKED', uncertainty_status='UNKNOWN')
    assert 'e3' not in programme_frontier({'train': uncertain}, downstream_account='ORIGINAL_E3').eligible


def test_old_manual_selection_edition_has_no_decoder_bridge():
    raw = canonical_json_document_bytes({'schema': MatrixResearchProgrammeSpecification.SCHEMA,
        'version': '2.0.0', 'value': {'specification_id': 'literal.old', 'active_slot': 'e1', 'components': []}})
    with pytest.raises(ValueError, match='version'):
        decode_canonical_bytes(raw, MatrixResearchProgrammeSpecification, maximum_bytes=len(raw))


def test_operation_selects_actual_packages_without_manual_phase_or_run_mapping():
    pin = ObjectIdentity('plan.literal.unwritten', MatrixResearchProgrammePlan.SCHEMA,
        MatrixResearchProgrammePlan.VERSION, 'a' * 64)
    authority = MatrixProgrammeAuthoritySelection('issued/actual-package.json', 'authority.actual-reveal')
    selected = MatrixProgrammeOperationSelection('operation.literal', pin, (authority,))
    assert decode_canonical_bytes(selected.canonical_bytes(), type(selected), maximum_bytes=4096) == selected
    assert not hasattr(selected, 'slot') and not hasattr(authority, 'run_id')
    with pytest.raises(ValueError, match='unique sorted'):
        MatrixProgrammeOperationSelection('operation.duplicate', pin, (authority, authority))


def test_dispositions_preserve_whole_denominators_adverse_and_unknown_counts():
    report = {'scientific_result': {'scientific_status': 'PRIMARY_NONSUCCESS',
        'denominators': {'nearby': {'assigned_units': 64, 'successes': 3},
            'shifted': {'assigned_units': 64, 'successes': 0}}}}
    rows = _disposition_denominators(report)
    assert tuple(row['assigned'] for row in rows) == (64, 64)
    assert tuple(row['unsuccessful'] for row in rows) == (61, 64)
    assert all(row['usable'] is None for row in rows)
    assert _disposition_facts(report)[0]['values']['scientific_status'] == 'PRIMARY_NONSUCCESS'


@pytest.mark.parametrize('envelope', ('', 'scientific_result', 'scientific_result.structure'))
def test_nested_group_and_case_denominators_keep_their_exact_scope_and_source(envelope):
    values = {'assigned_groups': 16, 'assigned_cases': 144}
    report = values
    for key in reversed(envelope.split('.')) if envelope else ():
        report = {key: report}
    rows = _disposition_denominators(report)
    assert [(row['scope'], row['assigned']) for row in rows] == [('independent-groups', 16), ('cases', 144)]
    prefix = envelope + '.' if envelope else ''
    assert [row['source'] for row in rows] == [prefix + 'assigned_groups', prefix + 'assigned_cases']
    assert all(row['unevaluable'] is None and row['usable'] is None for row in rows)


def test_read_only_public_composite_seam_never_derives_authors_or_runs(monkeypatch):
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=object()))
    plan = object()
    context = SimpleNamespace(observations={}, bindings={})
    monkeypatch.setattr(service, '_plan', lambda directory: plan)
    monkeypatch.setattr(service, '_request', lambda actual, path: None)
    @contextmanager
    def scope(actual, **kwargs):
        assert actual is plan
        yield context
    monkeypatch.setattr(service, '_read_context', scope)
    monkeypatch.setattr(service, '_observe', lambda actual, **kwargs: None)
    monkeypatch.setattr(service, '_report', lambda actual, **kwargs: {'state': 'INSPECTED'})
    def forbidden(*args, **kwargs):
        pytest.fail('inspect-only read reached a mutation or execution owner')
    for name in ('_project', '_retain_binding', '_author_phase', '_operate_phase', '_advance'):
        monkeypatch.setattr(service, name, forbidden)
    assert service.read(directory='/literal', allow_partial=False) == {'state': 'INSPECTED'}


def test_frontier_rejects_mislabelled_observation_and_unknown_phase():
    with pytest.raises(TypeError, match='typed current'):
        programme_frontier({'e3': observation('train')}, downstream_account='ORIGINAL_E3')
    with pytest.raises(TypeError, match='actual phase'):
        observation('e4.development.structure')


def test_current_c_backed_native_specification_reports_guarded_original_authentication(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_assembly as native
    from tests.test_matrix_native_training_assembly import assembly_case
    _, specification, request, _, _, execution = assembly_case(tmp_path)
    monkeypatch.setattr('empirical_lawhood.infrastructure.matrix_programme_inputs.authenticate_programme_inputs',
        lambda **_kw: pytest.fail("static preparation inspected C's guarded original publications"))
    bound = native.bind_inputs(specification, {"request": request}).method_inputs
    assert bound.request is request
    result = native.prepare(specification, method_inputs=bound, execution=execution)
    assert not result.executable and {value.code for value in result.dependencies} == {"native-assembly.derive"}
    assert result.census.native_effect_count == 0 and result.census.role_counts == ()
    pending = native.bind_inputs(specification, {}).method_inputs
    result = native.prepare(specification, method_inputs=pending, execution=execution)
    assert {value.code for value in result.dependencies} == {"native-assembly.request"}


def test_current_c_backed_source_binding_keeps_original_science_and_missing_key_hold(c_backed_source_case):  # noqa: F811
    from empirical_lawhood.adapters.methods import matrix_finite_dt_source_assembly as source
    from tests.test_matrix_finite_dt_source_assembly import selected_request
    request = selected_request(c_backed_source_case)
    specification = source.MatrixFiniteDtSourceAssemblySpecification("assembly.disclosed-current-source", request.identity)
    complete = source.bind_inputs(specification, {"request": request}).method_inputs
    assert complete is request and complete.input_commitments == c_backed_source_case.commitment
    assert complete.original_products == c_backed_source_case.original_products
    assert complete.canonical_bytes() == request.canonical_bytes()
    assert not complete.allow_metadata_key_creation
    result = source.prepare(specification, method_inputs=complete, execution=ExecutionSelection(4))
    assert not result.executable and result.census.native_effect_count == 0
    assert "finite-dt-assembly.derive" in {value.code for value in result.dependencies}
    with pytest.raises(ValueError, match="complete current C-backed"):
        source.bind_inputs(specification, {"request": request, "recipe-inputs": object()})
    old = request.to_document()
    old["version"] = "1.0.0"
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    with pytest.raises(ValueError):
        decode_canonical_bytes(canonical_json_document_bytes(old), type(request), maximum_bytes=None)


def test_noncomposite_derivation_preserves_existing_callback_arguments(tmp_path, monkeypatch):
    from empirical_lawhood.api import experiment_preparation as owner
    source = ROOT / "programmes/foundations/emergent-structure/workflows/matrix-response-experiment/native-training-assembly.example.json"
    plane = _plane(tmp_path / "ordinary-selection")
    service = ExperimentProgrammeService(ROOT, plane, SimpleNamespace(maximum_parallel_tasks=4))
    expected = object()
    calls = []
    monkeypatch.setattr(owner, "derive_experiment_inputs", lambda **kwargs: calls.append(kwargs) or expected)
    execution = _execution(plane)
    options = dict(specification_path=source, source_selection_path=tmp_path / "ordinary-sources.json",
        metadata_directory=tmp_path / "ordinary-metadata", output_selection_path=tmp_path / "ordinary-output.json", execution=execution)
    assert service.derive_inputs(**options) is expected
    assert calls == [{**options, "project_root": ROOT, "artifact_writer": plane}]


@pytest.mark.parametrize("prefix,expected", (("native-training", {"native-assembly.derive"}),
    ("finite-dt-source", {"finite-dt-assembly.derive"})))
def test_registered_compact_copied_examples_retain_exact_missing_originals(prefix, expected):
    from empirical_lawhood.api.experiment_preparation import load_experiment_specification
    directory = ROOT / "programmes/foundations/emergent-structure/workflows/matrix-response-experiment"
    specification = load_experiment_specification(directory / (prefix + "-assembly.example.json"))
    inputs = load_experiment_inputs(specification, directory / (prefix + "-sources.example.json"))
    stopped = prepare_experiment(specification, method_inputs=inputs.method_inputs, execution=ExecutionSelection(4))
    assert not stopped.executable
    assert expected <= {value.code for value in stopped.dependencies}
    assert stopped.census.native_effect_count == 0


def test_actual_e4_zero_locator_full_read_cannot_satisfy_programme_transition(monkeypatch):
    from empirical_lawhood.api.selected_e4_programme_service import SelectedE4ProgrammeService
    # The actual full reader requires the complete original wave/current reveal
    # census before structural or terminal assessment; no authority is invented.
    owner = SelectedE4ProgrammeService(service=SimpleNamespace(artifact_writer=object(),
        read=lambda **kwargs: pytest.fail('missing wave/reveal census reached an assessment read')))
    pin = SimpleNamespace(to_document=lambda: {"disclosed": "metadata-only"})
    wave = SimpleNamespace(wave_id="wave.disclosed", group_ids=("group.disclosed",), root_ids=("case.disclosed",))
    programme = SimpleNamespace(identity=pin, group_ids=wave.group_ids, cases=(), waves=(wave,))
    plan = SimpleNamespace(declaration=SimpleNamespace(identity=pin, programme=programme, planned_task_budgets=()),
        component_ids=())
    monkeypatch.setattr(owner, "_state", lambda _directory: (plan, None))
    monkeypatch.setattr(owner, "_request", lambda _path, _plan, **_kw: None)
    monkeypatch.setattr(owner, "_unentered", lambda _plan: None)
    with pytest.raises(PermissionError, match='every actual original wave and current reveal'):
        owner.read(directory=Path("/disclosed-original"))


def test_ordinary_retained_history_owner_preserves_256_unentered_and_zero_recalculation(tmp_path, monkeypatch):
    """Keep the independent retained-reader assertion after retiring manual slots.

    This descriptive public owner is separate from the programme's actual
    native E2 response frontier. No native source or fresh evidence is claimed.
    """
    from empirical_lawhood.adapters.methods.matrix_history_analysis import experiment_preparation as owner
    from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistoryAllocation, MatrixHistoryAnalysisConfig
    from empirical_lawhood.api import matrix_history_analysis as history
    plane = _plane(tmp_path / 'retained-history-owner')
    root = Path(plane.root.contract.canonical_path)
    allocation = decode_canonical_bytes((ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json').read_bytes(),
        MatrixHistoryAllocation, maximum_bytes=None)
    source = history.prepare_matrix_history_source_configuration(config_id='source.disclosed-history-owner',
        allocation=allocation, repo_root=ROOT)
    analysis = MatrixHistoryAnalysisConfig('analysis.disclosed-history-owner', 'ALGEBRA', source)
    specification = owner.MatrixHistoryProgrammeSpecification('experiment.disclosed-history-owner', allocation.identity,
        analysis.identity, (), 'retained-history-owner/result')
    inputs = owner.bind_inputs(specification, {'allocation': allocation, 'analysis': analysis})
    service = ExperimentProgrammeService(ROOT, plane, SimpleNamespace(maximum_parallel_tasks=4))
    prepared = service.prepare(specification, scientific_inputs=inputs.scientific_inputs,
        method_inputs=inputs.method_inputs, execution=_execution(plane))
    directory = root / 'retained-history-owner/child'
    service.author(preparation=prepared, output_dir=directory)
    actual = service.run(directory=directory, maximum_parallel_tasks=4)
    assert actual['result']['requested_histories'] == actual['result']['unentered_histories'] == 256
    assert actual['result']['completed_histories'] == actual['result']['unevaluable_histories'] == 0
    monkeypatch.setattr(history, 'analyze_matrix_histories', lambda **_: pytest.fail('completed recovery recalculated retained histories'))
    monkeypatch.setattr(history, 'produce_matrix_histories', lambda **_: pytest.fail('retained reader entered native acquisition'))
    assert service.recover(directory=directory, maximum_parallel_tasks=4) == actual
    monkeypatch.setattr(ExperimentProgrammeService, 'prepare', lambda *_a, **_kw: pytest.fail('retained read prepared current science'))
    assert service.read(directory=directory) == actual
    row, = _disposition_denominators(actual)
    assert row['assigned'] == row['unentered'] == 256 and row['completed'] == row['unevaluable'] == 0
    assert row['usable'] is row['successful'] is row['adverse'] is None


def test_native_e2_completion_keeps_adverse_results_and_refuses_passive_or_deferred_substitution():
    from empirical_lawhood.api.matrix_researcher_programme import _phase_complete
    complete = {'status': 'SUCCEEDED', 'scientific_result': {'scientific_completion': 'COMPLETE_NATIVE_UTILITY_ASSESSMENT',
        'scientific_status': 'UNEVALUABLE', 'qualification': 'NOT_ESTABLISHED', 'conditional_criterion_met': False}}
    assert _phase_complete('e2', complete)
    for report in ({'state': 'DESCRIPTIVE_RESULT_RETAINED'}, {'status': 'SUCCEEDED', 'scientific_result': None},
            {'status': 'SUCCEEDED', 'scientific_result': {'state': 'NATIVE_UTILITY_ASSESSMENT_DEFERRED'}}):
        assert not _phase_complete('e2', report)


@pytest.mark.parametrize('changed', ('reveal-only', 'different-run', 'different-package'))
def test_replacement_reveal_keeps_immutable_original_run_without_publication(monkeypatch, changed):
    from dataclasses import replace
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixProgrammeRunBinding
    from empirical_lawhood.api import matrix_researcher_programme_lineage as lineage
    programme = ObjectIdentity('programme.literal-original', MatrixResearchProgrammePlan.SCHEMA,
        MatrixResearchProgrammePlan.VERSION, 'a' * 64)
    specification = ObjectIdentity('specification.literal-original', 'empirical-lawhood/testing/specification', '1.0.0', 'b' * 64)
    package_pin = ObjectIdentity('package.literal-original', 'empirical-lawhood/api/experiment-package', '1.0.0', 'c' * 64)
    original_authority = MatrixProgrammeAuthoritySelection('issued/original.json', 'reveal.original')
    original = MatrixProgrammeRunBinding('binding.literal-original', programme, 'e3', 'main', specification,
        package_pin, 'run.literal-original', original_authority)
    raw = original.canonical_bytes()
    monkeypatch.setattr(lineage, 'retained_run_binding', lambda *_: original)
    writer = SimpleNamespace(write=lambda *_: pytest.fail('replacement reveal rewrote an immutable run binding'))
    runner = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=writer))
    context = SimpleNamespace(plan=SimpleNamespace(identity=programme))
    package = SimpleNamespace(package_id=package_pin.object_id, SCHEMA=package_pin.object_schema,
        VERSION=package_pin.object_version, fingerprint=lambda: 'f' * 64 if changed == 'different-package' else package_pin.object_fingerprint)
    run = SimpleNamespace(run_plan_id=original.run_id + '.foreign' if changed == 'different-run' else original.run_id)
    selected = SimpleNamespace(instance=SimpleNamespace(specification=specification))
    replacement = replace(original_authority, reveal_authority_id='reveal.actual-replacement')
    if changed == 'reveal-only':
        assert runner._retain_run(context, 'e3', selected, replacement, package, run) is original
    else:
        with pytest.raises(PermissionError, match='immutable original run locator'):
            runner._retain_run(context, 'e3', selected, replacement, package, run)
    assert original.canonical_bytes() == raw
