# SPDX-License-Identifier: MPL-2.0
"""Exposed operators through actual root, inquiry, custody, assessment and views.

The native callback executor below is a software-control seam. It makes no
claim about process isolation, molecular validity or provider deployment.
Pure root and assessment operations use the original process executor.
"""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests import test_rubisco_active_preparation as prefix_control
from tests import test_rubisco_preparation_response as response_control
from tests.test_rubisco_initial_root_public import ROOT

fixture = prefix_control.fixture
matched = prefix_control.matched
prefix = prefix_control.prefix


def _response_request():
    return dict(output_directory='/selected/new-output', root_directory='/selected/root',
        supplier_directory='/selected/prefix', previous_decision_directories=['/selected/root-decision'],
        completed_supplier_directories=['/selected/prefix'], contribution_directories=['/selected/prefix-contribution'],
        cutoff_id='cutoff.original', actor_id='owner.local-researcher', human_choice='acquire',
        human_reason='Select the frozen diagnostic.', prefix_directory='/selected/prefix',
        prefix_contribution='/selected/prefix-contribution', stage='diagnostic', native_work_directory='/selected/native')


def _prefix_request():
    request = _response_request()
    for field in ('prefix_directory', 'prefix_contribution', 'stage'):
        del request[field]
    request.update(supplier_directory=request['root_directory'], completed_supplier_directories=[],
        contribution_directories=['/selected/root-contribution'], design_file='/selected/design.json',
        plan_file='/selected/plan.json', model_files={name: {role: f'/selected/{name}/{role}'
            for role in ('preparation', 'prototype', 'representation', 'topology', 'coordinates')}
            for name in ('m1-i95m', 'm1-wt')})
    return request


@pytest.mark.parametrize('changed', (
    {'design_file': 'relative.json'}, {'model_files': {}},
    {'model_files': {'m1-i95m': {}, 'm1-wt': {}}},
    {'supplier_directory': '/selected/another-root'},
    {'contribution_directories': ['/selected/one', '/selected/two']},
    {'model_files': {name: {**files, 'topology': '../outside'} for name, files in _prefix_request()['model_files'].items()}},
))
def test_prefix_selection_refuses_before_original_custody(changed, monkeypatch):
    from scripts import operate_preparation_response as recipe
    from empirical_lawhood.api.application_contracts import ApplicationError
    monkeypatch.setattr(recipe, 'prepare_response_prefix_from_files', lambda **kwargs: pytest.fail('invalid selection reached custody'))
    with pytest.raises(ApplicationError):
        recipe.operate('prepare-prefix', _prefix_request() | changed, None, None)


@pytest.mark.parametrize('changed', (
    {'prefix_directory': '../outside'},
    {'prefix_contribution': '/selected/unrelated-contribution'},
    {'supplier_directory': '/selected/another-supplier'},
    {'completed_supplier_directories': []},
    {'contribution_directories': ['/selected/prefix-contribution']},
    {'native_work_directory': 'relative-work'},
    {'unknown_setting': 'must refuse'},
))
def test_continuation_selection_refuses_before_original_custody(changed, monkeypatch):
    from scripts import operate_preparation_response as recipe
    from empirical_lawhood.api.application_contracts import ApplicationError
    request = _response_request()
    del request['stage']
    request['contribution_directories'] = ['/selected/root-contribution', '/selected/prefix-contribution']
    monkeypatch.setattr(recipe, 'prepare_prefix_continuation',
        lambda **kwargs: pytest.fail('invalid continuation selection reached custody'))
    with pytest.raises(ApplicationError):
        recipe.operate('continue-prefix', request | changed, None, None)



@pytest.mark.parametrize('changed', (
    {'region': 'SEARCH_ALL_ATOMS'}, {'residue_keys': [['lsu.01', 1], ['lsu.01', 1]]},
    {'coordinate_tolerance_angstrom': 0.000001}, {'coordinate_tolerance_angstrom': '0.01'},
))
def test_environment_design_selection_refuses_before_original_custody(changed, monkeypatch):
    from scripts import operate_preparation_response as recipe
    from empirical_lawhood.api.application_contracts import ApplicationError
    request = dict(output_directory='/selected/new-environment', design_file='/selected/design.json',
        model_files=_prefix_request()['model_files'], region='SELECTED_COMMON_PROTEIN_RESIDUES',
        residue_keys=[['lsu.01', 1]])
    monkeypatch.setattr(recipe, 'prepare_environmental_response_design_from_files',
        lambda **kwargs: pytest.fail('invalid selection reached original inputs'))
    with pytest.raises(ApplicationError):
        recipe.operate('prepare-environment-design', request | changed, None, None)


def _prefix_files(directory, prefix, design):
    directory.mkdir()
    (directory / 'design.json').write_bytes(design.canonical_bytes())
    (directory / 'plan.json').write_bytes(prefix.plan.canonical_bytes())
    files = {}
    for name, row in zip(('m1-i95m', 'm1-wt'), prefix.models[:2], strict=True):
        model, prototype, preparation, top, xyz, _ = row
        member = directory / name
        member.mkdir()
        files[name] = {}
        for role, value in (('preparation', preparation.canonical_bytes()), ('prototype', prototype.canonical_bytes()),
                ('representation', model.canonical_bytes()), ('topology', top), ('coordinates', xyz)):
            path = member / role
            path.write_bytes(value)
            files[name][role] = str(path)
    return dict(design_file=directory / 'design.json', plan_file=directory / 'plan.json', model_files=files)


def test_prefix_configuration_preserves_exact_design_and_refuses_changed_plan(prefix, tmp_path, monkeypatch):
    import json
    from empirical_lawhood.api import configuration, recursive_inquiry_read
    from empirical_lawhood.api.domain_composition.rubisco_response.active_preparation import prepare_response_prefix_from_files
    from empirical_lawhood.domains.rubisco.rubisco_response.formation_coordinate import prepare_formation_coordinate
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import prepare_response_design
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootScopedAssessment
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    coordinates = tuple((name, prepare_formation_coordinate(representation=row[0], prepared=row[2],
        site_id=prefix.config.prefix.conditional.state_census[0][0]))
        for name, row in zip(('m1-i95m', 'm1-wt'), prefix.models[:2], strict=True))
    design = prepare_response_design(prefix=prefix.config.prefix,
        root_assessment=ObjectIdentity('assessment.exposed.original-root', InitialRootScopedAssessment.SCHEMA,
            InitialRootScopedAssessment.VERSION, '8' * 64), formation_coordinates=coordinates)
    files = _prefix_files(tmp_path / 'selection', prefix, design)
    copied = tmp_path / 'copied-design.json'
    copied.write_text(json.dumps(json.loads(design.canonical_bytes()), indent=2))
    consumer = 'rubisco-preparation-response-design'
    monkeypatch.setattr(recursive_inquiry_read, 'inquiry_projection_read', lambda *args: pytest.fail('configuration read scientific custody'))
    report = configuration.validate_configuration(copied, consumer=consumer)
    assert report['preparation_required'] and not report['authority_granted'] and not report['external_prerequisites_checked']
    with pytest.raises(configuration.ConfigurationError, match='prepare a new canonical'):
        configuration.load_configuration_record(copied, consumer=consumer)
    canonical = tmp_path / 'prepared-design.json'
    configuration.prepare_configuration(copied, canonical, consumer=consumer)
    assert canonical.read_bytes() == design.canonical_bytes()
    assert configuration.load_configuration_record(canonical, consumer=consumer) == design
    # The full frozen plan must join before any original root or model is read.
    files['plan_file'].write_bytes(replace(prefix.plan, plan_id='plan.exposed.other').canonical_bytes())
    with pytest.raises(ValueError, match='original matched plan'):
        prepare_response_prefix_from_files(**files, native_work_directory=tmp_path / 'native',
            root_directory=tmp_path / 'root', root_contribution=tmp_path / 'contribution',
            project_root=ROOT, artifact_writer=None)


@pytest.mark.parametrize('changed', (
    {'stage': 'invented-stage'},
    {'stage': 'challenge'},
    {'unknown_setting': 'must refuse'},
    {'prefix_directory': '../outside'},
    {'completed_supplier_directories': '/selected/prefix'},
    {'previous_decision_directories': []},
    {'contribution_directories': ['/selected/prefix-contribution', '/selected/prefix-contribution']},
    {'contribution_directories': ['/selected/different-contribution']},
    {'prefix_contribution': '/selected/different-prefix'},
    {'human_reason': ''},
))
def test_operator_request_refuses_before_original_custody(changed, monkeypatch):
    from scripts import operate_preparation_response as recipe
    from empirical_lawhood.api.application_contracts import ApplicationError
    monkeypatch.setattr(recipe, 'prefix_case', lambda *args: pytest.fail('invalid request reached scientific read'))
    with pytest.raises(ApplicationError):
        recipe.operate('prepare-response', _response_request() | changed, None, None)


def test_operator_later_stage_requires_both_original_diagnostic_locators():
    from scripts.operate_preparation_response import validate_request
    from empirical_lawhood.api.application_contracts import ApplicationError
    request = _response_request()
    assert validate_request('prepare-response', request) == request
    request.update(stage='challenge', diagnostic_directory='/selected/analysis',
        diagnostic_contribution='/selected/analysis-contribution',
        contribution_directories=['/selected/prefix-contribution', '/selected/analysis-contribution'])
    assert validate_request('prepare-response', request) == request
    request['diagnostic_contribution'] = None
    with pytest.raises(ApplicationError, match='both original diagnostic'):
        validate_request('prepare-response', request)


@pytest.mark.parametrize('stage', ('diagnostic', 'initial-primary', 'environment-diagnostic', 'challenge', 'additional-refinement'))
def test_operator_response_preparation_reads_each_selected_parent_once(monkeypatch, stage):
    """The thin caller reuses one parent's record, not an access decision."""
    from scripts import operate_preparation_response as recipe
    request, reads = _response_request(), []
    request['stage'] = stage
    if stage not in ('diagnostic', 'initial-primary'):
        request.update(diagnostic_directory='/selected/analysis', diagnostic_contribution='/selected/analysis-contribution')
        request['contribution_directories'].append('/selected/analysis-contribution')
    parents = {Path(path): object() for path in request['contribution_directories']}
    def parent(path, plane):
        reads.append(Path(path))
        return parents[Path(path)]
    models = ('m1-i95m', 'm1-wt')
    original = dict(checkpoints={'centers': (), 'frames': ()},
        configs=tuple(SimpleNamespace(original=SimpleNamespace(model_name=name, prototype=None)) for name in models),
        representations=dict.fromkeys(models),
        model_sources={name: SimpleNamespace(topology_utf8='', coordinates_utf8='') for name in models})
    def prepare(**kwargs):
        assert kwargs['preparation_parent'] is parents[Path(request['prefix_contribution'])]
        assert kwargs['diagnostic_parent'] is (None if stage in ('diagnostic', 'initial-primary')
            else parents[Path(request['diagnostic_contribution'])])
        return {}
    monkeypatch.setattr(recipe, 'original_parent', parent)
    monkeypatch.setattr(recipe, 'prefix_case', lambda *args: original)
    monkeypatch.setattr(recipe, 'read_response_analysis', lambda **kwargs: {'assessment': None})
    monkeypatch.setattr(recipe, 'freeze_response_predictions', lambda **kwargs: ())
    monkeypatch.setattr(recipe, 'prepare_preparation_response_stage', prepare)
    monkeypatch.setattr(recipe, 'retain_response_inputs', lambda **kwargs: ())
    monkeypatch.setattr(recipe, 'author_prepared_supplier', lambda *args: ('prepared', None, None))
    plane = SimpleNamespace(root=SimpleNamespace(contract=SimpleNamespace(canonical_path='/selected'),
        resolve=lambda relative, **kwargs: Path('/selected') / relative))
    assert recipe.operate('prepare-response', request, SimpleNamespace(project_root=ROOT), plane) == 'prepared'
    assert reads == list(parents)


def test_operator_return_checks_current_root_before_writing(tmp_path):
    from scripts.operate_preparation_response import retain
    destination = tmp_path / 'selected' / 'operation-return.json'
    calls = []
    def resolve(relative, **kwargs):
        calls.append(relative)
        if len(calls) == 2:
            raise PermissionError('selected mount is no longer available')
        return tmp_path / relative
    plane = SimpleNamespace(root=SimpleNamespace(contract=SimpleNamespace(canonical_path=str(tmp_path)), resolve=resolve))
    with pytest.raises(PermissionError, match='mount'):
        retain(destination, {'status': 'software-control'}, plane=plane)
    assert not destination.exists() and len(calls) == 2


def _disclosed_matched_root(prefix):
    """Use the original matched preparer, including its physical prerequisites."""
    from decimal import Decimal
    from empirical_lawhood.domains.rubisco.rubisco_response.contexts import RubiscoAssayContext
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_model import required_initial_sources
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root import prepare_initial_root
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootAnalysisInputs, InitialRootReviewInputs
    from empirical_lawhood.api.domain_composition.rubisco_response import initial_model as model
    from tests.test_rubisco_initial_model import selection
    original, source = selection()
    context = RubiscoAssayContext('context.exposed.preparation-response', Decimal('298.15'), (Decimal(8), Decimal(8)),
        'Exposed matched software control; no physical admission.', prefix.models[0][0].chemistry,
        'INITIAL_RATE_SINKS', (source.identity,), 'NEW_SELECTION')
    selected = model.prepare_matched_initial_model(plan=prefix.plan, state_selection=prefix.config.prefix.conditional,
        contexts=(('m1', context), ('v1', context)), protocol=source.identity, closure_source=source.identity,
        closure_assumptions=('Disclosed limiting-closure software control.',),
        dependencies=original.cases[0].dependencies, expected_alternative_ids=('chemical.exposed',),
        source_evidence=tuple(sorted((source.identity, prefix.plan.identity, prefix.config.prefix.conditional.identity),
            key=lambda p: p.object_id)), maximum_analysis_bytes=8 * 2**20)
    evidence = model.empty_initial_evidence(selected, evidence_id='evidence.exposed.preparation-response.missing')
    reviews = InitialRootReviewInputs(selected.identity, evidence.identity, required_initial_sources(selected, evidence), (), ())
    return InitialRootAnalysisInputs(prepare_initial_root(model=selected), selected, evidence, reviews)


@pytest.mark.parametrize('accelerated', (False, True))
@pytest.mark.parametrize('continuation', (False, True))
def test_presentation_guard_accepts_registered_prefix_revisions(accelerated, continuation):
    from empirical_lawhood.api.domain_composition.rubisco_response.preparation_presentation import selected
    declaration = prefix_control.owner.operation_declaration(accelerated=accelerated, continuation=continuation)
    operation = SimpleNamespace(node_id='test.original-prefix', selection=SimpleNamespace(
        capability_key=declaration.capability_key, capability_version=declaration.capability_version))
    draft = SimpleNamespace(operations=(operation,), selected_operation_ids=(operation.node_id,))
    assert selected(draft)
    operation.selection.capability_version = 'unsupported'
    assert not selected(draft)
    operation.selection.capability_version = declaration.capability_version
    operation.selection.capability_key = 'unregistered.prefix'
    assert not selected(draft)


def _controlled_executor(monkeypatch, fixtures, retained):
    from empirical_lawhood.execution.local import execution
    real_executor = execution.LocalProcessExecutor

    class ExposedCallbackExecutor(execution.DirectTaskExecutor):
        def __init__(self, **kwargs):
            self.pure = real_executor(**kwargs)

        def close_run_workers(self, run_id=None):
            self.pure.close_run_workers(run_id)

        def execute(self, runner, context, *, timeout_seconds, native_subwork=None, prepared_contract=None,
                    provenance_requirements=(), native_entry=None, native_work_preparer=None, completed_native_work=None):
            if not prepared_contract.native_effect:
                return self.pure.execute(runner, context, timeout_seconds=timeout_seconds,
                    prepared_contract=prepared_contract, provenance_requirements=provenance_requirements)
            assert prepared_contract.native_preparation_error is None
            prepared_contract.require_complete()
            prepared_contract.validate_context(context)
            context = replace(context, prepared_invocation=prepared_contract)
            if native_entry is not None:
                parent, native_subwork = native_entry()
                assert parent == prepared_contract.expected_parent_contact
            assert native_subwork is not None
            if isinstance(runner, prefix_control.owner.ActivePreparationPrefixRunner):
                f = fixtures[context.task_id.rsplit('.', 1)[1]]
                assert f.config.fingerprint() == context.config.content_sha256
                # The real runner consumes its ports once. Temporary native
                # mocks end before the shared source guard observes completion.
                with monkeypatch.context() as native_patch:
                    retained['prefix_calls'].append(prefix_control.install_exposed_operator(f, native_patch))
                    if (retained.get('interrupt_prefix_once') and not runner.continuation
                            and f.config.original.model_name == 'm1-i95m'):
                        from empirical_lawhood.domains.rubisco.rubisco_response import active_preparation_checkpoint as checkpoint
                        publish = checkpoint.publish_checkpoint_files
                        def interrupt_after_seal(directory, record, arrays):
                            publish(directory, record, arrays)
                            retained['interrupt_prefix_once'] = False
                            retained.setdefault('publication_interruptions', []).append(record.identity)
                            raise OSError('EXPOSED_INTERRUPTION_AFTER_AUTHENTICATED_CHECKPOINT')
                        native_patch.setattr(checkpoint, 'publish_checkpoint_files', interrupt_after_seal)
                    try:
                        return runner.execute_with_native_subwork(context, native_subwork)
                    except Exception:
                        import traceback
                        traceback.print_exc()
                        raise
            return runner.execute_with_native_subwork(context, native_subwork)

        def execute_deadline_free(self, runner, context, *, progress_contract, progress_callback, **kwargs):
            return self.execute(runner, context, timeout_seconds=None, **kwargs)

    monkeypatch.setattr(execution, 'LocalProcessExecutor', ExposedCallbackExecutor)


def _export(root, plane, wave, name):
    from empirical_lawhood.api.recursive_contributions import export_recursive_contribution, authenticate_recursive_contribution
    path = root / (name + '-contribution')
    assert export_recursive_contribution(directory=wave, output_dir=path, project_root=ROOT, artifact_writer=plane)['status'] == 'EXPORTED'
    return path, authenticate_recursive_contribution(directory=path, artifact_writer=plane)[2]


def _read_once(reader, *, directory, artifact_writer, monkeypatch):
    """Every independent scientific read uses one original root load."""
    from empirical_lawhood.api import recursive_authoring as author
    visits = []
    original = author._load_authored_wave
    def load(**kwargs):
        if Path(kwargs['directory']) == directory:
            visits.append(kwargs['lazy_payloads'])
        return original(**kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(author, '_load_authored_wave', load)
        result = reader(directory=directory, artifact_writer=artifact_writer)
    assert visits == [True]
    return result


def _fork(root, plane, original_root, previous, design, prepared, bindings, parents, supplier, name, completed=(),
          human_choice='acquire', minimum_supplied=0):
    from scripts.operate_preparation_response import author_prepared_supplier
    from empirical_lawhood.api.recursive_operations import inquiry_selection_scope
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_policy import supply_owners
    with inquiry_selection_scope(prepared['draft']):
        selected = supply_owners(prepared['draft'])[0]
        repeated = supply_owners(prepared['draft'])[0]
        assert len(selected) == len(repeated)
        assert all(left is right for left, right in zip(selected, repeated, strict=True))
    request = dict(output_directory=str(root / name), root_directory=str(original_root),
        previous_decision_directories=tuple(map(str, previous)),
        completed_supplier_directories=tuple(map(str, completed)),
        supplier_directory=str(supplier), cutoff_id='test.preparation.' + name,
        actor_id='owner.local-researcher', human_choice=human_choice,
        human_reason='Explicitly selected exposed software-control supplier; preserve the unresolved original root and full denominator.')
    result, projected, records = author_prepared_supplier(request, SimpleNamespace(project_root=ROOT),
        plane, dict(prepared, design=design), bindings, parents)
    supplied = [row for row in projected.menu.frontier.requirement_findings
        if row.requirement.object_id.startswith('requirement.preparation-supply.') and row.supplied]
    assert len(supplied) >= minimum_supplied
    assert all(not row.supplied for row in projected.menu.frontier.requirement_findings
        if row.requirement.object_id.endswith('actual-paired-physical-preparation'))
    assert records['decision.json'].human_directed
    assert records['decision.json'].unresolved_target_claim_ids
    decision = Path(result['decision_directory'])
    if human_choice == 'hold':
        acquire, = (row for row in projected.menu.alternatives if row.alternative_id == 'acquire')
        assert not acquire.supplier.selected and acquire.supplier.unavailable_reason_codes
        assert 'Decline the optional refinement' in acquire.expected_next_evidence
        assert result['selected_directory'] is None
        return None, decision
    assert result['authoring']['status'] == 'AUTHORED'
    return Path(result['selected_directory']), decision


def _observe(plane, directory, *, monkeypatch=None, output=None):
    from empirical_lawhood.api.domain_composition.rubisco_response.preparation_observation import observe
    from empirical_lawhood.api.experiment_execution_read import load_development_execution_controls
    packet, _, _, index, source, _ = load_development_execution_controls(directory=directory, artifact_writer=plane)
    selection = {'binding': {'run_id': index.run_id, 'packet_sha256': packet.fingerprint(),
        'worker_source_sha256': source.code_sources_sha256}}
    context = SimpleNamespace(read_access_paths=())
    # Match the shared collector's owning verification lifetime. A domain
    # callback receives this scope; it cannot reuse an unscoped native store.
    with plane.read_context() as reader:
        observed = observe(context=context, directory=directory, artifact_writer=reader, selection=selection)
        with pytest.raises(PermissionError, match='packet, run, source'):
            observe(context=context, directory=directory, artifact_writer=reader,
                selection={'binding': selection['binding'] | {'worker_source_sha256': '0' * 64}})
    if output is not None:
        _collect_original(plane, directory, observed, selection['binding'], output, monkeypatch)
    return observed


def _collect_original(plane, directory, observed, binding, output, monkeypatch):
    """Original task/native metadata and domain callback through sealed collection.

    Only storage composition is selected here; the allocation is an explicitly
    disclosed nonexecuting test record, with no supervisor or financial claim.
    """
    from empirical_lawhood.api import application_context, operational_observation as api
    from empirical_lawhood.api.application_contracts import ApplicationContext
    from empirical_lawhood.storage.operational_observation import read_export, import_snapshot, read_retained_observation
    from empirical_lawhood.storage.workbench_state import WorkbenchStateStore
    from empirical_lawhood.execution.operational_observation import SELECTION_SCHEMA, document_bytes
    from tests.test_deployment_supervision import allocation
    output.mkdir()
    def write(name, value):
        path = output / name
        raw = document_bytes(value)
        path.write_bytes(raw)
        return {'path': str(path), 'sha256': sha256(raw).hexdigest()}
    money = allocation()
    allocation_pin = write('exposed-allocation.json', money.to_document())
    job = write('exposed-job.json', {'evidence_role': 'EXPOSED_SOFTWARE_CONTROL', 'observation': {
        'cadence_seconds': 30, 'stale_after_seconds': 120,
        'controller_source_sha256': binding['worker_source_sha256'],
        'worker_source_sha256': binding['worker_source_sha256'], 'selected_gpu': 'NO_PROVIDER_ALLOCATION'}})
    complete_binding = dict(binding, deployment_id=money.deployment_id, investigation_id='exposed.m50',
        selection_id='exposed.m50.' + directory.name, allocation_sha256=allocation_pin['sha256'],
        job_card_sha256=job['sha256'], controller_source_sha256=binding['worker_source_sha256'])
    selected = dict(schema=SELECTION_SCHEMA, version='1.0.0', binding=complete_binding, directory=str(directory),
        allocation=allocation_pin, job_card=job, supervisors=[], cadence_seconds=30, stale_after_seconds=120,
        task_offset=0, native_offset=0, row_limit=200, domain_panel={'panel_id': 'rubisco.preparation-response',
            'panel_version': '1.0.0', 'observation_version': '1.0.0'})
    selected_pin = write('selection.json', selected)
    context = ApplicationContext('exposed.m50', 'Exposed M50 collector control', Path('/nonexecuting/python'),
        input_root=output, observation_root=output)
    with monkeypatch.context() as scoped:
        scoped.setattr(application_context, 'application_storage', lambda *_: (ROOT, None, plane))
        scoped.setattr(api, 'operational_state_store', lambda _context, path=None:
            WorkbenchStateStore(plane.root, path, writable=True))
        export = api.collect_observation(context, selected_pin, collector_id='collector.exposed.m50', sequence=1,
            output_directory=output / 'export')
        _, snapshot = read_export(export['directory'], expected_manifest_sha256=export['manifest_sha256'])
        assert snapshot['domain'] == observed
        assert snapshot['financial']['status'] == 'UNAVAILABLE'
        assert all(snapshot[key] == 0 for key in ('provider_calls', 'native_calls', 'lifecycle_actions'))
        retained = WorkbenchStateStore(plane.root, output / 'imported.json', writable=True)
        imported = import_snapshot(export['directory'], expected_manifest_sha256=export['manifest_sha256'],
            expected_binding=complete_binding, expected_allocation=money.to_document(),
            store=retained)
        digest, reopened = read_retained_observation(retained)
        assert imported['state_sha256'] == digest and reopened['snapshot'] == snapshot
        changed = dict(selected, domain_panel=dict(selected['domain_panel'], panel_version='unsupported'))
        _, _, unavailable = api._observe_execution(context, changed)
        assert unavailable['status'] == 'UNAVAILABLE' and unavailable['complete_return_count'] is None


def test_native_result_read_scope_closes_and_refuses_mutation(prefix, monkeypatch):
    from empirical_lawhood.api.domain_composition.rubisco_response.preparation_response_analysis import native_result_reader
    from empirical_lawhood.storage.artifact_validation import ArtifactIdentityConflict
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes

    custody = prefix_control.custody(prefix)
    calls = prefix_control.install_exposed_operator(prefix, monkeypatch)
    returned = prefix_control.owner.ActivePreparationPrefixRunner().execute_with_native_subwork(custody.context, custody.store)
    result = decode_canonical_bytes(returned.outputs[1].payload, prefix_control.owner.ActivePreparationPrefixResult,
        maximum_bytes=16 * 2**20)
    definition = result.unit.definition
    with native_result_reader(custody.plane, result) as reader:
        recovered = reader.recover(definition)
        assert recovered.completion == result.unit.completion
        assert recovered.receipt == result.unit.receipt
        assert b''.join(reader.iter_completed_output(definition, 'relaxation.return')) == result.unit.returned.canonical_bytes()
    with pytest.raises(ArtifactIdentityConflict):
        reader.recover(definition)
    with pytest.raises(ArtifactIdentityConflict, match='changed|mismatch'):
        with native_result_reader(custody.plane, result) as reader:
            recovered = reader.recover(definition)
            manifest = recovered.outputs[0]
            path = custody.plane.root.resolve(manifest.materialization.relative_path, for_write=False)
            raw = path.read_bytes()
            path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
    assert len(calls) == 2


@pytest.mark.parametrize('environmental', (False, True), ids=('local', 'environment'))
def test_public_rooted_preparation_diagnostic_and_frozen_challenge(prefix, tmp_path, monkeypatch, environmental):
    # These padded, deliberately nonphysical inputs require the same disclosed
    # geometry seam during execution AND independent readback. The ordinary
    # reader still verifies original bytes, identities and assessment equality.
    # Separate whole-molecule controls exercise genuine geometry refusal.
    from tests.rubisco_exposed_geometry_fixture import install_exposed_geometry
    install_exposed_geometry(monkeypatch)
    from empirical_lawhood.api import recursive_execution as execute, recursive_inquiry as inquiry
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.domain_composition.rubisco_response.initial_root_inquiry import project_initial_root_inquiry
    from empirical_lawhood.api.domain_composition.rubisco_response.active_preparation import prepare_response_prefix_from_files, prepare_prefix_continuation, retain_preparation_prefix_inputs
    from empirical_lawhood.api.domain_composition.rubisco_response.preparation_response import prepare_preparation_response_stage, retain_response_inputs, freeze_response_predictions
    from empirical_lawhood.api.domain_composition.rubisco_response.preparation_response_analysis import read_preparation_stage, read_response_stage, prepare_response_analysis, retain_response_analysis_inputs, read_response_analysis, native_result_reader
    from empirical_lawhood.api.domain_composition.rubisco_response.preparation_presentation import read as presentation_read
    from empirical_lawhood.api.domain_composition.rubisco_response.preparation_supply import prepare_preparation_supply, read_preparation_supply
    from empirical_lawhood.domains.rubisco.rubisco_response import initial_root_experiment as experiment
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_inquiry import actual_assessment
    from empirical_lawhood.domains.rubisco.rubisco_response.formation_coordinate import prepare_formation_coordinate
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import prepare_response_design
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
    from empirical_lawhood.execution.experiment_preparation import ExecutionSelection
    from tests.test_rubisco_gas_contrast import _real_plane
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
    from empirical_lawhood.storage.artifacts import ExternalArtifactPlane

    root = tmp_path / 'actual-custody'
    plane = ExternalArtifactPlane(_real_plane(root).root,
        validators=integration_artifact_profile_validators())
    analysis = _disclosed_matched_root(prefix)
    specification = experiment.initial_root_experiment_specification(analysis)
    bound = experiment.bind_inputs(specification, {'analysis': analysis})
    service = ExperimentProgrammeService(ROOT, plane)
    root_prepared = service.prepare(specification, scientific_inputs=bound.scientific_inputs, method_inputs=bound.method_inputs,
        execution=ExecutionSelection(workers=1, environment_id='rubisco-prediction', output_root=str(root),
            source_snapshot=ObjectIdentity.from_record('recursive-member.implementation', implementation_binding(ROOT))))
    root_wave = root / 'original-root'
    service.author(preparation=root_prepared, output_dir=root_wave)
    assert service.run(directory=root_wave, maximum_parallel_tasks=1)['status'] == 'SUCCEEDED'
    _, root_products, root_draft, _ = execute.read_recursive_wave(directory=root_wave, artifact_writer=plane, include_products=True)
    root_assessment = actual_assessment(root_draft, root_products)[3][0]
    assert root_assessment.joint_outcome == 'UNRESOLVED'
    root_contribution, root_parent = _export(root, plane, root_wave, 'root')
    projected = project_initial_root_inquiry(directory=root_wave, artifact_writer=plane,
        information_cutoff=InformationCutoff('test.root.original', 'clock.rubisco.declared-rate-closure', CausalPhase.POST_OUTCOME, None))
    root_decision = root / 'original-root-decision'
    inquiry.commit_inquiry_decision(specification=projected.specification, state=projected.state, sources=projected.sources,
        menu=projected.menu, policy=projected.policy, campaign=root_draft.campaign,
        right=root_draft.campaign.decision_rights[0], actor_id='owner.local-researcher', project_root=ROOT,
        artifact_writer=plane, output_dir=root_decision)
    fixtures, coordinates = {}, []
    for name, row in zip(('m1-i95m', 'm1-wt'), prefix.models[:2], strict=True):
        model, prototype, preparation, raw_top, raw_xyz, raw = row
        fixtures[name] = SimpleNamespace(model=model, prototype=prototype, prepared=preparation,
            coordinates=raw, config=None)
        coordinates.append((name, prepare_formation_coordinate(representation=model, prepared=preparation,
            site_id=prefix.config.prefix.conditional.state_census[0][0])))
    design = prepare_response_design(prefix=prefix.config.prefix, root_assessment=root_assessment.identity,
        formation_coordinates=tuple(coordinates))
    files = _prefix_files(root / 'prefix-selection', prefix, design)
    if environmental:
        from empirical_lawhood.api.domain_composition.rubisco_response.preparation_response import prepare_environmental_response_design_from_files
        design = prepare_environmental_response_design_from_files(design_file=files['design_file'],
            model_files=files['model_files'], region='SELECTED_COMMON_PROTEIN_RESIDUES', residue_keys=(('lsu.01', 1),))
        files['design_file'].write_bytes(design.canonical_bytes())
    (root / 'native-prefix').mkdir()
    prepared = prepare_response_prefix_from_files(**files, native_work_directory=root / 'native-prefix',
        root_directory=root_wave, root_contribution=root_contribution, project_root=ROOT, artifact_writer=plane)
    bindings = retain_preparation_prefix_inputs(prepared=prepared, artifact_writer=plane, output_dir=root / 'prefix-inputs')
    wave, decision = _fork(root, plane, root_wave, (root_decision,), design, prepared, bindings,
        (root_contribution,), root_wave, 'prefix')
    before = _observe(plane, wave, monkeypatch=monkeypatch, output=root / 'prefix-before-observation')
    assert len(before['positions']) == 4 and before['complete_return_count'] == 0
    pending = presentation_read(context=SimpleNamespace(read_access_paths=()), directory=wave, artifact_writer=plane)
    assert [q['question_id'] for q in pending.exploration['question_readouts']] == ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6']
    assert all(q['assessment_state'] == 'NOT_YET_ASSESSED' for q in pending.exploration['question_readouts'])
    retained = {'prefix_calls': [], 'interrupt_prefix_once': True}
    for config in prepared['configs']:
        fixtures[config.original.model_name].config = config
    _controlled_executor(monkeypatch, fixtures, retained)
    # The exposed callback represents the declared molecular worker. Pure tasks
    # still run on the actual host and the ordinary admission policy stays active.
    from empirical_lawhood.execution.local.execution import LocalExecutionResourceAdmitter
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import BUDGET
    from functools import partial
    observed = LocalExecutionResourceAdmitter.detect_capacity()
    capacity = replace(observed, cpu_cores=max(observed.cpu_cores, BUDGET.cpu_cores),
                       memory_bytes=max(observed.memory_bytes, BUDGET.memory_bytes))
    run_successor = partial(inquiry.run_inquiry_successor, parallel_resource_capacity=capacity)
    assert run_successor(directory=wave, project_root=ROOT, artifact_writer=plane)['status'] == 'SUCCEEDED'
    partial_wave, partial_decision = wave, decision
    partial = _read_once(read_preparation_stage, directory=wave, artifact_writer=plane, monkeypatch=monkeypatch)
    assert partial['checkpoints']['checkpoint_status'] == 'UNAVAILABLE_PAIRED_HANDOFF'
    assert sum(map(len, retained['prefix_calls'])) == 3 and len(retained['publication_interruptions']) == 1
    partial_contribution, _ = _export(root, plane, wave, 'partial-prefix')
    (root / 'native-continued-prefix').mkdir()
    prepared = prepare_prefix_continuation(prefix_directory=wave, prefix_contribution=partial_contribution,
        native_work_directory=root / 'native-continued-prefix', project_root=ROOT, artifact_writer=plane)
    assert tuple(c.continuation.remaining_allowance for c in prepared['configs']) == (4, 0)
    bindings = retain_preparation_prefix_inputs(prepared=prepared, artifact_writer=plane, output_dir=root / 'continued-prefix-inputs')
    wave, decision = _fork(root, plane, root_wave, (root_decision, partial_decision), design, prepared, bindings,
        (root_contribution, partial_contribution), partial_wave, 'continued-prefix', completed=(partial_wave,))
    inherited = _observe(plane, wave, monkeypatch=monkeypatch, output=root / 'continued-prefix-before-observation')
    assert inherited['complete_return_count'] == 3
    assert all(p['independent_reading'] == 'ORIGINAL_CONTINUATION_INPUT_ASSESSED' for p in inherited['positions'])
    for config in prepared['configs']:
        fixtures[config.original.model_name].config = config
    assert run_successor(directory=wave, project_root=ROOT, artifact_writer=plane)['status'] == 'SUCCEEDED'
    assert [len(c) for c in retained['prefix_calls']] == [1, 2, 1, 0]
    prefix_wave = wave
    original_prefix = _read_once(read_preparation_stage, directory=wave, artifact_writer=plane, monkeypatch=monkeypatch)
    assert original_prefix['checkpoints']['checkpoint_status'] == 'AVAILABLE'
    after = _observe(plane, wave, monkeypatch=monkeypatch, output=root / 'prefix-after-observation')
    assert len(after['positions']) == 4 and after['complete_return_count'] == sum(map(len, retained['prefix_calls'])) == 4
    assert all(p['safe_state'] == 'PUBLISHED_ASSESSED_AVAILABLE' for p in after['positions'])
    displayed = presentation_read(context=SimpleNamespace(read_access_paths=()), directory=wave, artifact_writer=plane)
    assert len(displayed.records) == 4 and displayed.summary['independent_biological_units'] == 0
    prefix_contribution, prefix_parent = _export(root, plane, wave, 'prefix')
    checkpoints = original_prefix['checkpoints']
    paired = SimpleNamespace(design=design, centers=checkpoints['centers'], frames=checkpoints['frames'],
        raw=checkpoints['center_bytes'], fixtures=fixtures)
    if environmental:
        from tests.test_rubisco_preparation_environment_workflow import install_quadratic_environment
        calls = install_quadratic_environment(paired, monkeypatch)
    else:
        calls = response_control.install_response_operator(paired, monkeypatch)
    completed, decisions, stages, contributions = [partial_wave, wave], [root_decision, partial_decision, decision], [], []
    prefix_readouts = tuple(checkpoints['original_readouts'][name] for name in ('m1-i95m', 'm1-wt'))
    admission_prepared = prepare_preparation_supply(design=design, original_prefixes=prefix_readouts, parents=(prefix_parent,))
    admitted, admission_decision = _fork(root, plane, root_wave, tuple(decisions), design, admission_prepared, (),
        (prefix_contribution,), wave, 'prefix-admission', completed=tuple(completed))
    assert run_successor(directory=admitted, project_root=ROOT, artifact_writer=plane)['status'] == 'SUCCEEDED'
    handoff = _read_once(read_preparation_supply, directory=admitted, artifact_writer=plane, monkeypatch=monkeypatch)
    assert len(handoff['connection_assessments']) == 8
    assert all(row.disposition.value == 'SATISFIED' for row in handoff['connection_assessments'])
    assert handoff['assessment'].response_disposition is None and not calls
    completed.append(admitted)
    decisions.append(admission_decision)
    diagnostic_assessment, diagnostic_parent, predictions = None, None, ()
    analysis_contribution = None
    # Admission satisfies the prerequisite; the original prefix remains the
    # receipt-backed supplier of the diagnostic's scientific operands.
    supplier = wave
    stages_selected = ('initial-primary', 'environment-diagnostic', 'challenge') if environmental else ('diagnostic', 'challenge')
    frozen_nomination = None
    for stage in stages_selected:
        model_rows = tuple((name, prototype, model, top, xyz, root / ('native-' + stage + '-' + name))
            for name, row in zip(('m1-i95m', 'm1-wt'), prefix.models[:2], strict=True)
            for model, prototype, _, top, xyz, _ in (row,))
        prepared = prepare_preparation_response_stage(checkpoints=checkpoints, stage=stage, models=model_rows,
            project_root=ROOT, preparation_parent=prefix_parent, predictions=predictions,
            diagnostic=diagnostic_assessment, diagnostic_parent=diagnostic_parent)
        bindings = retain_response_inputs(prepared=prepared, artifact_writer=plane, output_dir=root / (stage + '-inputs'))
        parents = (prefix_contribution,) if stage in ('diagnostic', 'initial-primary') else (prefix_contribution, analysis_contribution)
        wave, decision = _fork(root, plane, root_wave, tuple(decisions), design, prepared, bindings,
            parents, supplier, stage, completed=tuple(completed), minimum_supplied=2)
        assert _observe(plane, wave)['complete_return_count'] == 0
        assert run_successor(directory=wave, project_root=ROOT, artifact_writer=plane)['status'] == 'SUCCEEDED'
        observed = _observe(plane, wave)
        assert len(observed['effects']) == len(prepared['configs']) == observed['complete_return_count']
        returned = _read_once(read_response_stage, directory=wave, artifact_writer=plane, monkeypatch=monkeypatch)
        stages.append((returned['configs'], returned['readouts']))
        contribution, parent = _export(root, plane, wave, stage)
        contributions.append((contribution, parent))
        completed.append(wave)
        decisions.append(decision)
        assessment_prepared = prepare_response_analysis(checkpoints=checkpoints, stages=tuple(stages),
            representations=original_prefix['representations'], parents=(prefix_parent, *(p for _, p in contributions)),
            project_root=ROOT, native_subwork_for_result=lambda result: native_result_reader(plane, result))
        binding = retain_response_analysis_inputs(prepared=assessment_prepared, artifact_writer=plane,
            output_dir=root / (stage + '-analysis-inputs'))
        analysis_wave, analysis_decision = _fork(root, plane, root_wave, tuple(decisions), design,
            assessment_prepared, binding, (prefix_contribution, *(p for p, _ in contributions)), wave,
            stage + '-analysis', completed=tuple(completed))
        assert run_successor(directory=analysis_wave, project_root=ROOT, artifact_writer=plane)['status'] == 'SUCCEEDED'
        assessment = _read_once(read_response_analysis, directory=analysis_wave, artifact_writer=plane,
            monkeypatch=monkeypatch)['assessment']
        assert assessment == assessment_prepared['preliminary_assessment']
        analysis_contribution, assessed_parent = _export(root, plane, analysis_wave, stage + '-analysis')
        displayed = presentation_read(context=SimpleNamespace(read_access_paths=()), directory=analysis_wave, artifact_writer=plane)
        assert [q['question_id'] for q in displayed.exploration['question_readouts']] == ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6']
        assert displayed.exploration['question_readouts'][0]['denominator']['original_starting_hypotheses'] == 384
        completed.append(analysis_wave)
        decisions.append(analysis_decision)
        admission_prepared = prepare_preparation_supply(design=design, original_prefixes=prefix_readouts,
            original_response=assessment, parents=(prefix_parent, assessed_parent))
        admitted, admission_decision = _fork(root, plane, root_wave, tuple(decisions), design, admission_prepared, (),
            (prefix_contribution, analysis_contribution), analysis_wave, stage + '-admission', completed=tuple(completed), minimum_supplied=2)
        assert run_successor(directory=admitted, project_root=ROOT, artifact_writer=plane)['status'] == 'SUCCEEDED'
        supply = _read_once(read_preparation_supply, directory=admitted, artifact_writer=plane, monkeypatch=monkeypatch)
        assert len(supply['connection_assessments']) == 12
        assert supply['assessment'].next_supplier_decision == assessment.next_supplier_decision
        assert supply['assessment'].response_disposition.value == ('SATISFIED' if stage == 'challenge' else 'UNEVALUABLE')
        completed.append(admitted)
        decisions.append(admission_decision)
        supplier = analysis_wave
        if environmental:
            assert assessment.nomination.disposition == 'AVAILABLE'
            frozen_nomination = frozen_nomination or assessment.nomination
            assert assessment.nomination == frozen_nomination
        if stage != 'challenge':
            assert all(q.disposition == 'UNAVAILABLE' for q in assessment.questions[3:])
            if stage == 'initial-primary':
                with pytest.raises(ValueError):
                    freeze_response_predictions(assessment=assessment, centers=checkpoints['centers'], frames=checkpoints['frames'])
            else:
                predictions = freeze_response_predictions(assessment=assessment, centers=checkpoints['centers'], frames=checkpoints['frames'])
            diagnostic_assessment, diagnostic_parent = assessment, assessed_parent
        else:
            assert assessment.questions[3].disposition == ('WITHIN_SELECTED_ERROR_ALL_POSITIONS' if environmental
                else 'WITHIN_SELECTED_ERROR_AFTER_PREPARATION')
            assert assessment.next_supplier_decision == ('RETAIN_SUFFICIENT_INITIAL_RESPONSE_AND_ASSESS_OMITTING_ADDITIONAL_PREPARATION'
                if environmental else 'RETAIN_SIGNAL_LIMIT_AND_ASSESS_A_CONSEQUENTIAL_FORMATION_RECEIVER')
    assert len(calls) == 24
    optional = prepare_preparation_response_stage(checkpoints=checkpoints, stage='additional-refinement', models=model_rows,
        project_root=ROOT, preparation_parent=prefix_parent, diagnostic=assessment, diagnostic_parent=assessed_parent)
    bindings = retain_response_inputs(prepared=optional, artifact_writer=plane, output_dir=root / 'optional-inputs')
    unentered, _ = _fork(root, plane, root_wave, tuple(decisions), design, optional, bindings,
        (prefix_contribution, analysis_contribution), supplier, 'optional-decline', completed=tuple(completed),
        human_choice='hold', minimum_supplied=3)
    assert unentered is None and len(calls) == 24
    for completed_native in (prefix_wave, wave):
        recovered = run_successor(directory=completed_native, project_root=ROOT,
            artifact_writer=plane, terminal_product_format='compact')
        assert recovered['status'] == 'SUCCEEDED' and recovered['new_native_contact_count'] == 0
    assert sum(map(len, retained['prefix_calls'])) == 4 and len(calls) == 24
    assert run_successor(directory=analysis_wave, project_root=ROOT, artifact_writer=plane)['status'] == 'SUCCEEDED'
    assert len(calls) == 24


def test_prefix_inquiry_preserves_original_root_and_continuation_history(monkeypatch):
    """Declared products exercise meaning only; lifecycle tests authenticate custody."""
    from empirical_lawhood.domains.rubisco.rubisco_response import active_preparation_inquiry as owner
    from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.science.inquiry.recursive_requirements import ContributionRole, ScientificConditionScope
    from empirical_lawhood.science.identity.references import ArtifactIdentity
    from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
    from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput
    scope = ScientificConditionScope('system.exposed.prefix', 'world.exposed.prefix', 'source.exposed.prefix',
        ('accepted-state',), ('angstrom',), 'receiver.exposed.prefix', 'clock.exposed.prefix',
        'Disclosed projection-only control with no scientific or custody authority.')
    root_scope = replace(scope, source_id='source.exposed.root', receiver_id='receiver.exposed.root')
    payloads, externals, products = {}, [], []
    for name in ('original-root-assessment', 'original-prefix-assessment.m1-i95m',
                 'original-prefix-assessment.m1-wt', 'native-prefix-selection'):
        raw = ('{"exposed":"' + name + '"}').encode()
        digest = sha256(raw).hexdigest()
        schema = 'empirical-lawhood/test/exposed-prefix-input'
        pin = ObjectIdentity('record.exposed.' + name, schema, '1.0.0', digest)
        external = RecursiveExternalInput('external.active-prefix.' + name, 'artifact.exposed.' + name,
            schema, 'application/json', len(raw), OutcomeAccess.DEVELOPMENT_VISIBLE,
            VisibilityCeiling.DEVELOPMENT_ONLY, digest, 'SOURCE' if name == 'native-prefix-selection' else 'HISTORY')
        externals.append(external)
        payloads['external-' + sha256(external.input_id.encode()).hexdigest()[:24] + '.json'] = raw
        if external.scientific_role == 'HISTORY':
            products.append(ContributionProduct('product.exposed.' + name, pin,
                ArtifactIdentity(external.logical_artifact_id, 'exposed-original-input', schema,
                    digest, 'application/json', len(raw)),
                ObjectIdentity('receipt.exposed.' + name, 'empirical-lawhood/runtime/task-receipt', '1.0.0', 'a' * 64),
                ContributionRole.RETAINED_ANALYSIS_INPUT, EvidenceCeiling.NON_PROMOTABLE,
                OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))
    def parent(label, original_scope, rows):
        return ContributionManifest('contribution.exposed.' + label, 'Preserve original source meanings.',
            'Declared software control only.', original_scope, tuple(sorted(rows, key=lambda p: p.product_id)),
            tuple(sorted((p.record for p in rows), key=lambda p: p.object_id)), ())
    root_parent = parent('root', root_scope, products[:1])
    prefix_parent = parent('prefix', scope, products[1:])
    config = SimpleNamespace(scientific_context=SimpleNamespace(parent=root_parent,
        original_root=SimpleNamespace(scope=root_scope)), continuation=SimpleNamespace(parent=prefix_parent))
    views = ('view.exposed.initial', 'view.exposed.later')
    draft = SimpleNamespace(external_inputs=tuple(externals),
        development_study=SimpleNamespace(numerical_view_ids=views))
    monkeypatch.setattr(owner, 'selected_configs', lambda selected: (config,))
    monkeypatch.setattr(owner, 'prefix_scope', lambda configs: scope)
    bindings = {row.binding_id: row for row in owner.evidence_projector(draft, payloads)}
    for external, product in zip(externals[:3], products, strict=True):
        row = bindings[external.input_id]
        assert row.scope == (root_scope if external is externals[0] else scope)
        assert row.role is product.role and row.nested_view_ids == ()
        assert row.independent_unit_ids == () and row.content_sha256 == product.artifact.sha256
    source = bindings[externals[-1].input_id]
    assert source.scope == scope and source.role is ContributionRole.DESIGN_OPERAND
    assert source.nested_view_ids == views
    changed_product = replace(products[1], record=replace(products[1].record, object_fingerprint='b' * 64),
        artifact=replace(products[1].artifact, sha256='b' * 64))
    for changed in (None, parent('prefix', scope, products),
                    parent('prefix', scope, (changed_product, products[2]))):
        config.continuation.parent = changed
        with pytest.raises(ValueError, match='one exact original contribution product'):
            owner.evidence_projector(draft, payloads)
