# SPDX-License-Identifier: MPL-2.0
"""CLI composition only; real protected science is tested by its lifecycle owner."""
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api import experiment_preparation as inputs
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.selected_e3_access import SelectedE3CurrentAccess
from empirical_lawhood.cli import experiment_preparation as owner, integrations, platform
from empirical_lawhood.cli.app import app
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_experiment_read_access import install_locator_codecs, locator_files
from tests.test_recursive_public_service import _plane


ROOT = Path(__file__).resolve().parents[2]


def _forbidden(*_args, **_kwargs):
    raise AssertionError('CLI composition opened unsupported inputs or entered scientific work')


@pytest.mark.parametrize('command,issued', (*((command, False) for command in
    ('explain', 'prepare', 'derive-inputs', 'export-products', 'author', 'run', 'read', 'recover')),
    ('run', True), ('read', True), ('recover', True)))
def test_all_public_commands_forward_one_typed_current_selection_and_preserve_inputs(
        tmp_path, monkeypatch, command, issued):
    install_locator_codecs(monkeypatch)
    originals, paths = locator_files(tmp_path / 'current-locators')
    original_bytes = tuple(path.read_bytes() for path in paths)
    plane = _plane(tmp_path / 'guarded')
    directory = Path(plane.root.contract.canonical_path) / 'authored'
    directory.mkdir()
    selected = {}
    for name in ('input', 'sources', 'snapshot', 'selection'):
        selected[name] = tmp_path / (name + '.json')
        selected[name].write_text('{}\n')
    storage_calls, calls, formatter_calls, protocol_calls = [], [], [], []
    service_result = {'scope': 'CLI_COMPOSITION_ONLY', 'native_contact': 'none', 'qualification': 'NOT_ESTABLISHED'}

    def storage(*, read_only=False):
        storage_calls.append(read_only)
        return ROOT, None, plane

    def service_call(service, **kwargs):
        assert service.artifact_writer is plane
        calls.append(kwargs)
        return service_result

    def derivation_report(result):
        # This dispatch control supplies no actual typed scientific derivation.
        assert result is service_result
        formatter_calls.append(result)
        return result

    def prepare(*args, **kwargs):
        calls.append(kwargs)
        return {'scope': 'CLI_COMPOSITION_ONLY', 'native_contact': 'none'}

    preparation = object()

    def prepare_record(*args, **kwargs):
        assert kwargs['programme_service'].artifact_writer is plane
        calls.append(kwargs)
        return preparation

    def protocol(*, specification_path=None, directory=None, artifact_writer=None):
        protocol_calls.append((specification_path, directory, artifact_writer))
        if command in ('explain', 'prepare', 'derive-inputs', 'author'):
            assert specification_path == selected['input'] and directory is None
            assert artifact_writer is (None if command in ('explain', 'prepare') else plane)
        else:
            assert specification_path is None and directory == expected_directory and artifact_writer is plane
        return 'protocol.disclosed.access.0'

    from empirical_lawhood.api import experiment_read_access
    expected_directory = directory
    monkeypatch.setattr(experiment_read_access, 'experiment_read_access_protocol', protocol)
    monkeypatch.setattr(integrations, '_storage', storage)
    monkeypatch.setattr(platform, 'CLI_OPERATOR_PROFILE', None)
    monkeypatch.setattr(owner, '_prepare', prepare)
    monkeypatch.setattr(owner, '_prepare_record', prepare_record)
    monkeypatch.setattr(inputs, 'experiment_input_derivation_report', derivation_report)
    monkeypatch.setattr(LocalProcessExecutor, 'execute', _forbidden)
    for name in ('author', 'run', 'read', 'recover', 'derive_inputs', 'export_products'):
        monkeypatch.setattr(ExperimentProgrammeService, name, service_call)
    args = ['campaign', 'experiment-' + command]
    if command in ('explain', 'prepare', 'derive-inputs', 'author'):
        args += ['--input', str(selected['input']), '--sources', str(selected['sources'])]
    if command == 'prepare':
        args += ['--output', str(tmp_path / 'preparation-report.json')]
    elif command == 'derive-inputs':
        args += ['--metadata-directory', str(tmp_path / 'derived'),
            '--output-selection', str(tmp_path / 'derived-selection.json')]
    elif command == 'author':
        args += ['--source-snapshot', str(selected['snapshot']), '--environment-id', 'environment.disclosed',
            '--output-dir', str(tmp_path / 'new-authoring')]
    elif command in ('run', 'read', 'recover', 'export-products'):
        args += ['--authoring-dir', str(directory)]
        if command == 'export-products':
            args += ['--selection', str(selected['selection'])]
    if issued:
        if command == 'run':
            args += ['--plan', str(selected['selection']), '--yes',
                '--reveal-authority-id', 'reveal.own-issued']
        elif command == 'read':
            args += ['--run', 'run.own-issued', '--attempt-history',
                '--reveal-authority-id', 'reveal.own-issued']
        else:
            args += ['--run', 'run.own-issued', '--yes', '--reconcile-only',
                '--reveal-authority-id', 'reveal.own-issued']
    for path in paths:
        args += ['--read-access', str(path)]
    returned = CliRunner().invoke(app, args)
    assert returned.exit_code == 0, returned.stdout + returned.stderr + repr(returned.exception)
    assert calls and len(protocol_calls) == 1
    if issued:
        request = calls[-1]['request']
        if command == 'run':
            assert request.path == selected['selection'] and request.confirmed is True
            assert request.reveal_authority_id == 'reveal.own-issued'
        else:
            assert request.run_id == 'run.own-issued'
            if command == 'read':
                assert request.include_attempt_history is True
                assert calls[-1]['reveal_authority_id'] == 'reveal.own-issued'
            else:
                assert request.confirmed is True and request.reconcile_only is True
                assert request.reveal_authority_id == 'reveal.own-issued'
    contexts = tuple(call['read_access'] for call in calls)
    assert all(type(context) is SelectedE3CurrentAccess for context in contexts)
    assert all(context is contexts[0] for context in contexts)
    assert contexts[0].effective_originals(originals) == originals
    assert storage_calls == ([] if command in ('explain', 'prepare') else [command == 'read'])
    assert formatter_calls == ([service_result] if command == 'derive-inputs' else [])
    assert tuple(path.read_bytes() for path in paths) == original_bytes
    assert not tuple(directory.iterdir())


@pytest.mark.parametrize('command,options', (
    ('run', ('--programme-request', '/unopened/composite.json')),
    ('read', ('--programme-request', '/unopened/composite.json')),
    ('recover', ('--custody-only',)),
    ('recover', ('--programme-request', '/unopened/composite.json')),
))
def test_unsupported_lifecycle_options_refuse_before_locator_or_storage_access(
        tmp_path, monkeypatch, command, options):
    monkeypatch.setattr(integrations, '_storage', _forbidden)
    monkeypatch.setattr(owner, '_read_access_options', _forbidden)
    result = CliRunner().invoke(app, ['campaign', 'experiment-' + command,
        '--authoring-dir', str(tmp_path), '--read-access', '/unopened/current.json', *options])
    assert result.exit_code == 2, result.stdout + result.stderr + repr(result.exception)
    assert '--read-access refuses' in result.stderr
    assert not tuple(tmp_path.iterdir())


@pytest.mark.parametrize('command,options,message', (
    ('run', ('--yes', '--reveal-authority-id', 'reveal.own-issued'), 'require --plan'),
    ('read', ('--reveal-authority-id', 'reveal.own-issued'), 'require --run'),
    ('recover', ('--yes', '--reveal-authority-id', 'reveal.own-issued'), 'require --run'),
))
def test_original_selection_does_not_replace_own_issued_authority_prerequisites(
        tmp_path, monkeypatch, command, options, message):
    plane = _plane(tmp_path / 'guarded')
    monkeypatch.setattr(integrations, '_storage', lambda **kwargs: (ROOT, None, plane))
    monkeypatch.setattr(owner, '_read_access_options', _forbidden)
    result = CliRunner().invoke(app, ['campaign', 'experiment-' + command,
        '--authoring-dir', str(tmp_path), '--read-access', '/unopened/original.json', *options])
    assert result.exit_code == 2, result.stdout + result.stderr + repr(result.exception)
    assert message in result.stderr
    assert not (tmp_path / 'original.json').exists()


@pytest.mark.parametrize('command', ('explain', 'prepare'))
def test_current_access_without_scientific_sources_refuses_before_any_input_read(tmp_path, monkeypatch, command):
    monkeypatch.setattr(owner, '_read_access_options', _forbidden)
    monkeypatch.setattr(owner, '_prepare', _forbidden)
    args = ['campaign', 'experiment-' + command, '--input', '/unopened/specification.json',
        '--read-access', '/unopened/current.json']
    if command == 'prepare':
        args += ['--output', str(tmp_path / 'report.json')]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 2, result.stdout + result.stderr + repr(result.exception)
    assert '--read-access requires the exact --sources' in result.stderr
    assert not tuple(tmp_path.iterdir())


@pytest.mark.parametrize('configured', (False, True))
def test_prepare_selects_actual_plane_before_loader_and_preserves_unconfigured_blind_route(
        tmp_path, monkeypatch, configured):
    events = []
    specification, scientific, methods, preparation = (object() for _ in range(4))
    plane = object()
    profile = SimpleNamespace(maximum_parallel_tasks=1)
    current = object() if configured else None
    service = SimpleNamespace(artifact_writer=plane, storage_profile=profile)

    def load_specification(path):
        events.append('specification')
        return specification

    def storage():
        events.append('storage')
        return ROOT, profile, plane

    def load_inputs(value, path, *, artifact_writer, read_access):
        events.append('protected-input-loader')
        assert value is specification and read_access is current
        assert artifact_writer is (plane if configured else None)
        return SimpleNamespace(scientific_inputs=scientific, method_inputs=methods)

    def prepare(value, **kwargs):
        events.append('prepare')
        assert value is specification
        assert kwargs['scientific_inputs'] is scientific and kwargs['method_inputs'] is methods
        return preparation

    service.prepare = prepare
    monkeypatch.setattr(inputs, 'load_experiment_specification', load_specification)
    monkeypatch.setattr(inputs, '_protocol', lambda value: SimpleNamespace(consumer_id='consumer.disclosed'))
    monkeypatch.setattr(inputs, 'load_experiment_inputs', load_inputs)
    monkeypatch.setattr(inputs, 'prepare_experiment', prepare)
    monkeypatch.setattr(integrations, '_storage', storage)
    monkeypatch.setattr('empirical_lawhood.api.experiment_programme.ExperimentProgrammeService',
        lambda *args, **kwargs: service)
    monkeypatch.setattr(platform, 'CLI_OPERATOR_PROFILE', tmp_path / 'profile.json' if configured else None)
    monkeypatch.setattr(owner, 'attempt_input', lambda path, **kwargs: path)
    monkeypatch.setattr(owner, '_execution_selection', lambda *args, **kwargs: ExecutionSelection(workers=1))
    actual = owner._prepare_record(tmp_path / 'specification.json', None, None, None, 1,
        tmp_path / 'sources.json', read_access=current)
    assert actual is preparation
    assert events == ['specification', 'specification', *(['storage'] if configured else []),
        'protected-input-loader', 'prepare']
