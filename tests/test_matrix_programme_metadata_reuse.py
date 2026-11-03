# SPDX-License-Identifier: MPL-2.0
"""Guard lifetime controls over retained PURE custody, not Matrix qualification."""
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import experiment_execution_read as execution_read
from empirical_lawhood.api import matrix_programme_source_continuation as owner
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_recursive_report_projection import ROOT, wave  # noqa: F401
from tests.test_matrix_programme_source_continuation import metadata_case, _plans  # noqa: F401


@pytest.fixture
def borrowed(wave, monkeypatch):  # noqa: F811
    """Exercise the custody guard with actual PURE receipts under two role labels.

    The role labels and absent TRAIN locator are an explicit seam. They do not
    assert an E1/E2 scientific design, source continuation or issued authority.
    """
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import _retained_plans
    packet, draft, _, payloads = load_authored_wave(directory=wave.directory,
        artifact_writer=wave.plane, lazy_payloads=True)
    _, _, index = _retained_plans(payloads, draft)
    service = ExperimentProgrammeService(ROOT, wave.plane)
    directory = wave.directory.parent / 'original-programme-seam'
    context = MatrixProgrammeProjectionContext(service, None, None, directory,
        {phase: object() for phase in ('e1', 'e2', 'train')}, {})
    reads = []

    class Reader:
        def __init__(self, *, service, descriptor=None):
            self.service, self.descriptor = service, descriptor

        def _read_phase(self, context, phase, *, execution_only, observe_controls):
            assert execution_only
            reads.append(phase)
            return execution_read.read_development_execution(directory=wave.directory,
                artifact_writer=context.writer, observe_controls=observe_controls)

    monkeypatch.setattr(owner, '_unentered_future_packet', lambda context:
        (ObjectIdentity.from_record(packet.packet_id, packet), 'run.disclosed-unentered-training'))
    monkeypatch.setattr(owner, '_pin_original_selection', lambda owner, context: lambda: None)
    return SimpleNamespace(context=context, reader=Reader(service=service), reads=reads,
        wave=wave, index=index)


def test_borrowed_complete_census_is_read_once_and_expires(borrowed):
    with owner._original_custody(borrowed.reader, borrowed.context) as retained:
        assert borrowed.reads == ['e1', 'e2']
        retained.require_current()
        retained.require_current()
        assert all(row['scientific_completion'] == 'DEFERRED_TO_FULL_READ'
            for row in retained.reports.values())
    assert borrowed.reads == ['e1', 'e2']
    with pytest.raises(PermissionError, match='escaped'):
        retained.require_current()


@pytest.mark.parametrize('changed', ('receipt', 'commit', 'late-attempt', 'future-binding', 'train-entry'))
def test_borrowed_census_rejects_changes_before_return(borrowed, changed):
    index, plane = borrowed.index, borrowed.wave.plane
    candidate = index.tasks[0].attempts[0]
    relative = candidate.receipt_relative_path
    if changed == 'commit':
        relative = plane.read_manifest(relative).publication.commit_marker_relative_path
    elif changed == 'late-attempt':
        # Freeze an absent event path already selected by the real index.
        relative = index.tasks[0].nonattempt_event_relative_path
    elif changed == 'future-binding':
        relative = (borrowed.context.directory / 'bindings/e3.json').relative_to(
            plane.root.contract.canonical_path).as_posix()
    elif changed == 'train-entry':
        relative = 'runs/run.disclosed-unentered-training'
    path = plane.root.resolve(relative, for_write=True)
    original = path.read_bytes() if path.is_file() else None
    try:
        with pytest.raises((PermissionError, ArtifactIdentityConflict)):
            with owner._original_custody(borrowed.reader, borrowed.context):
                path.parent.mkdir(parents=True, exist_ok=True)
                if changed == 'train-entry':
                    path.mkdir()
                else:
                    path.write_bytes(b'new uncommitted control' if original is None
                        else bytes([original[0] ^ 1]) + original[1:])
    finally:
        if original is not None:
            path.write_bytes(original)
        elif path.is_dir():
            path.rmdir()
        elif path.exists():
            path.unlink()


def test_borrowed_census_rechecks_current_member_access(borrowed):
    permission = [True]

    def require_access(_manifest):
        if not permission[0]:
            raise PermissionError('disclosed current access revoked')

    try:
        with pytest.raises(PermissionError, match='access revoked'):
            with borrowed.wave.plane.read_context(before_member=require_access) as plane:
                context = replace(borrowed.context,
                    service=replace(borrowed.context.service, artifact_writer=plane))
                with owner._original_custody(borrowed.reader, context):
                    permission[0] = False
    finally:
        permission[0] = True


def test_operational_observation_reuses_only_inherited_execution_reports(monkeypatch):
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=None))
    report = {'read_scope': 'EXECUTION_RECORDS', 'execution_complete': True,
        'scientific_completion': 'DEFERRED_TO_FULL_READ'}
    context = SimpleNamespace(bindings={'e1': object()}, observations={},
        retained_execution_reports={'e1': report})
    reads = []
    monkeypatch.setattr(service, '_read_phase', lambda *_args, **_kwargs: reads.append(1) or report)
    service._observe(context, phases=('e1',), operational=True)
    assert not reads and context.observations['e1'].execution_complete
    assert not context.observations['e1'].complete
    service._observe(context, phases=('e1',), operational=False)
    assert reads == [1] and not context.observations['e1'].complete


def test_public_author_keeps_one_preparation_context_through_publication(metadata_case, monkeypatch):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import prepare
    _, _, plan = _plans(metadata_case)
    writer = metadata_case.case.writer
    service = ExperimentProgrammeService(ROOT, writer, SimpleNamespace(maximum_parallel_tasks=4))
    selected = MatrixResearchProgrammeService(service=service)
    prepared = prepare(plan.specification, execution=metadata_case.case.execution)
    assert not prepared.executable
    state = []

    @contextmanager
    def context(actual):
        assert actual == plan
        state.append('enter')
        try:
            yield SimpleNamespace(plan=plan, directory=selected._home(plan))
        finally:
            state.append('exit')

    def advance(context, *, mode, confirmed):
        assert context.plan == plan and mode == 'author' and not confirmed and state == ['enter']
        return {'state': 'software-author-boundary'}

    monkeypatch.setattr(selected, '_context', context)
    monkeypatch.setattr(selected, '_advance', advance)
    monkeypatch.setattr(ExperimentProgrammeService, '_composite_programme', lambda *_args, **_kwargs: selected)
    monkeypatch.setattr(ExperimentProgrammeService, '_refine_preparation',
        lambda *_args: pytest.fail('authoring reopened a separate prerequisite context'))
    report = service.author(preparation=prepared, output_dir=selected._home(plan))
    assert report['state'] == 'software-author-boundary' and state == ['enter', 'exit']


def test_cli_author_defers_current_refinement_to_the_owning_author(monkeypatch, tmp_path):
    from empirical_lawhood.api import experiment_preparation as preparation_owner
    from empirical_lawhood.cli import experiment_preparation as cli
    specification, execution, expected = object(), object(), object()
    monkeypatch.setattr(preparation_owner, 'load_experiment_specification', lambda path: specification)
    monkeypatch.setattr(preparation_owner, '_protocol', lambda actual: SimpleNamespace(consumer_id='software-consumer'))
    monkeypatch.setattr(cli, 'attempt_input', lambda path, **kwargs: path)
    monkeypatch.setattr(cli, '_execution_selection', lambda *args, **kwargs: execution)
    called = []
    monkeypatch.setattr(preparation_owner, 'prepare_experiment',
        lambda actual, **kwargs: called.append((actual, kwargs['execution'])) or expected)
    service = SimpleNamespace(storage_profile=None,
        prepare=lambda *args, **kwargs: pytest.fail('CLI authoring repeated current prerequisite refinement'))
    result = cli._prepare_record(tmp_path / 'selection.json', None, 'software-env', Path(tmp_path), 4,
        programme_service=service, authoring=True)
    assert result is expected and called == [(specification, execution)]


def test_author_without_selected_storage_keeps_its_prerequisite(metadata_case):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import prepare
    _, _, plan = _plans(metadata_case)
    service = ExperimentProgrammeService(ROOT, metadata_case.case.writer)
    prepared = prepare(plan.specification, execution=metadata_case.case.execution)
    with pytest.raises(ValueError, match='selected storage profile'):
        service.author(preparation=prepared, output_dir=Path(plan.output_root) / plan.specification.directory)


def test_nested_input_reads_reuse_pure_joins_but_expire_with_the_outer_scope(metadata_case, monkeypatch):  # noqa: F811
    from empirical_lawhood.infrastructure import matrix_programme_inputs as inputs
    original, calls = inputs.validate_programme_input_records, []

    def validate(resolved):
        calls.append(resolved)
        return original(resolved)

    monkeypatch.setattr(inputs, 'validate_programme_input_records', validate)
    options = dict(writer=metadata_case.case.writer, commitment=metadata_case.commitment,
        maximum_source_bytes=metadata_case.case.request.metadata_budget.source_scan_bytes)
    with inputs.authenticated_programme_inputs(**options) as first:
        with inputs.authenticated_programme_inputs(**options) as second:
            assert first == second and first.scientific_design is second.scientific_design
            assert len(calls) == 1
    with inputs.authenticated_programme_inputs(**options) as third:
        assert first == third and len(calls) == 2


def test_nested_input_reuse_still_authenticates_current_bytes(metadata_case):  # noqa: F811
    from empirical_lawhood.infrastructure import matrix_programme_inputs as inputs
    writer = metadata_case.case.writer
    options = dict(writer=writer, commitment=metadata_case.commitment,
        maximum_source_bytes=metadata_case.case.request.metadata_budget.source_scan_bytes)
    path = writer.root.resolve(metadata_case.commitment.publication.materialization.relative_path, for_write=False)
    before = path.read_bytes()
    try:
        with pytest.raises((PermissionError, ValueError, ArtifactIdentityConflict)):
            with inputs.authenticated_programme_inputs(**options):
                path.write_bytes(bytes([before[0] ^ 1]) + before[1:])
                with inputs.authenticated_programme_inputs(**options):
                    pytest.fail('nested input reuse accepted changed original bytes')
    finally:
        path.write_bytes(before)


@pytest.fixture(scope='module')
def just_authored(wave):  # noqa: F811
    from empirical_lawhood.adapters.methods.analytic_material_inquiry.recursive_translation import supply_draft
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave
    draft = supply_draft(wave.source, draft_id='draft.metadata-authoring.pure')
    directory = wave.directory.parent / 'unentered-authoring-records'
    report = author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=wave.plane,
        output_dir=directory, input_bindings=((draft.external_inputs[0].input_id,
            wave.directory.parent / 'selected-source.json'),))
    return SimpleNamespace(report=report, directory=directory, plane=wave.plane)


def test_new_authoring_uses_its_actual_packet_without_graph_or_execution_replay(just_authored, monkeypatch):
    from empirical_lawhood.api import recursive_execution
    monkeypatch.setattr(recursive_execution, '_retained_plans',
        lambda *_args, **_kwargs: pytest.fail('new authoring replays the graph it just compiled'))
    monkeypatch.setattr(execution_read, 'read_execution_records',
        lambda **_kwargs: pytest.fail('new authoring claims an execution census'))
    with execution_read.observed_development_authoring(directory=just_authored.directory,
            artifact_writer=just_authored.plane, authoring_report=just_authored.report) as report:
        assert report['read_scope'] == 'AUTHORING_RECORDS' and report['status'] == 'UNENTERED'
        assert report['task_count'] == just_authored.report['task_count']
        assert not report['execution_complete'] and report['scientific_qualification'] == 'NOT_ESTABLISHED'


@pytest.mark.parametrize('changed', ('packet-pin', 'member', 'run-namespace'))
def test_new_authoring_observation_rejects_foreign_or_changed_custody(just_authored, changed):
    report = dict(just_authored.report)
    path, before = None, None
    if changed == 'packet-pin':
        report['packet_sha256'] = '0' * 64
    elif changed == 'member':
        path = just_authored.directory / 'run-plan.json'
        before = path.read_bytes()
    else:
        path = just_authored.plane.root.resolve('runs/' + report['run_id'], for_write=True)
    try:
        with pytest.raises((PermissionError, ValueError, ArtifactIdentityConflict)):
            with execution_read.observed_development_authoring(directory=just_authored.directory,
                    artifact_writer=just_authored.plane, authoring_report=report):
                if changed == 'member':
                    path.write_bytes(bytes([before[0] ^ 1]) + before[1:])
                elif changed == 'run-namespace':
                    path.mkdir(parents=True)
                else:
                    pytest.fail('new authoring accepted a foreign author result')
    finally:
        if before is not None:
            path.write_bytes(before)
        elif path is not None and path.exists():
            path.rmdir()


def test_retained_selection_reuses_typed_operands_but_compares_every_original_byte(wave, monkeypatch):  # noqa: F811
    from empirical_lawhood.api import recursive_execution
    from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection
    _, draft, _, payloads = recursive_execution.load_authored_wave(directory=wave.directory,
        artifact_writer=wave.plane, lazy_payloads=True)
    decode = recursive_execution.decode_canonical_bytes

    def decode_once(raw, kind, **kwargs):
        assert kind is not RecursiveScientificSelection
        return decode(raw, kind, **kwargs)

    monkeypatch.setattr(recursive_execution, 'decode_canonical_bytes', decode_once)
    original = recursive_execution._retained_plans(payloads, draft)
    assert original[0].run_plan_id == wave.report['run_id']
    names = ('run-plan.json', 'execution-plan.json', 'template.json', 'scientific-projection.json',
        'registry.json', 'graph-preservation.json')
    changed = {name: payloads[name] for name in names}
    changed['scientific-projection.json'] += b' '
    with pytest.raises(ValueError, match='scientific projection differs'):
        recursive_execution._retained_plans(changed, draft)
