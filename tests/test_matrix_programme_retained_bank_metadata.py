# SPDX-License-Identifier: MPL-2.0
"""Real immutable publication and namespace controls over exposed metadata.

Original E3 science and bank composition are disclosed seams, not authentic
scientific evidence. Their independent readers retain their own controls.
"""
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_programme_completed_continuation as continuation
from empirical_lawhood.api import matrix_programme_e4_inputs, matrix_programme_e4_phases
from empirical_lawhood.api.matrix_programme_retained_bank_metadata import retained_e4_bank_metadata
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.test_recursive_public_service import _plane


@pytest.fixture
def metadata(tmp_path, monkeypatch):
    plane = _plane(tmp_path / 'artifacts')
    root = Path(plane.root.contract.canonical_path)
    directory = root / 'programme'
    prefix = 'programme/derived/e4.development/original-banks'
    requests = tuple(ArtifactWriteRequest('metadata.' + phase + '.' + kind,
        prefix + '/' + phase + '.' + kind + '.json', 'empirical-lawhood/testing/bank-metadata',
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'metadata.disclosed', prefix,
        b'{"schema":"empirical-lawhood/testing/bank-metadata","value":{"test_only":true},"version":"1.0.0"}\n',
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)
        for phase in ('development', 'calibration', 'confirmation') for kind in ('bank', 'programme'))
    plane.write_batch(requests)
    state = {'allowed': True}; events = []
    def current():
        events.append('current-access')
        if not state['allowed']:
            raise PermissionError('disclosed original grant revoked')
    @contextmanager
    def originals(*, publish):
        assert publish is False
        current()
        yield SimpleNamespace(require_current=current)
        current()
    @contextmanager
    def banks(**kwargs):
        current()
        events.append('authenticated-banks')
        yield object()
        current()
    request = SimpleNamespace(input_commitments=None, original_e3=None, original_preparation=None,
        original_assay=None, original_products=None, native_training_locator=None,
        source_budget=SimpleNamespace(source_scan_bytes=1024**2))
    monkeypatch.setattr(matrix_programme_e4_phases, '_source_request', lambda *args: request)
    monkeypatch.setattr(matrix_programme_e4_inputs, 'authenticated_programme_e4_banks', banks)
    expected = {'requests': requests}
    monkeypatch.setattr(matrix_programme_e4_inputs, 'programme_e4_bank_requests', lambda *args, **kwargs: expected['requests'])
    context = SimpleNamespace(directory=directory, writer=plane,
        bindings=dict.fromkeys(continuation.domain.COMPLETED_PHASES), pending_bindings={},
        child_directory=lambda phase: directory / 'children' / phase,
        metadata_directory=lambda phase: directory / 'derived' / phase, e3_originals=originals)
    return SimpleNamespace(context=context, plane=plane, root=root, requests=requests,
        state=state, events=events, expected=expected)


def test_complete_retained_metadata_is_read_only_and_does_not_allow_successor_entry(metadata, monkeypatch):
    before = {path: path.read_bytes() for path in metadata.context.directory.rglob('*') if path.is_file()}
    monkeypatch.setattr(metadata.plane, 'write_batch', lambda *args: pytest.fail('retained metadata was republished'))
    with metadata.plane.read_context() as writer:
        metadata.context.writer = writer
        with retained_e4_bank_metadata(metadata.context) as guard:
            assert callable(guard)
            continuation.require_unentered_successors(metadata.context, retained_metadata=guard)
            child = metadata.context.child_directory('e4.development')
            child.mkdir(parents=True)
            with pytest.raises(PermissionError, match='entered or authored'):
                continuation.require_unentered_successors(metadata.context, retained_metadata=guard)
    assert all(path.read_bytes() == raw for path, raw in before.items())
    assert metadata.events.count('authenticated-banks') == 1


@pytest.mark.parametrize('damage', ('missing', 'foreign', 'symlink', 'uncommitted', 'body', 'selection', 'lineage',
    'new-child', 'new-run', 'new-binding', 'other-phase', 'revoked'))
def test_incomplete_changed_or_entered_metadata_cannot_enable_source_handoff(metadata, damage):
    context = metadata.context
    bank = context.metadata_directory('e4.development') / 'original-banks'
    if damage == 'missing':
        (bank / 'development.bank.json').unlink()
    elif damage == 'foreign':
        (bank / 'foreign.json').write_bytes(b'{}')
    elif damage == 'symlink':
        (bank / 'foreign-link').symlink_to(metadata.root / 'missing')
    elif damage == 'uncommitted':
        commit, = bank.glob('.publication-batches/*/*.commit.json')
        commit.with_name(commit.name.replace('.commit.json', '.intent.json')).write_bytes(b'{}')
    elif damage == 'body':
        (bank / 'development.bank.json').write_bytes(b'{}\n')
    elif damage in ('selection', 'lineage'):
        field = ({'payload': b'{"schema":"empirical-lawhood/testing/bank-metadata","value":{"test_only":false},"version":"1.0.0"}\n'}
            if damage == 'selection' else {'visibility_ceiling': VisibilityCeiling.PROSPECTIVE})
        metadata.expected['requests'] = (replace(metadata.requests[0], **field), *metadata.requests[1:])
    elif damage in ('new-child', 'new-run', 'new-binding', 'other-phase'):
        path = (context.child_directory('e4.development') if damage == 'new-child' else
            context.directory / 'runs/e4.development.main.json' if damage == 'new-run' else
            context.directory / 'bindings/e4.development.json' if damage == 'new-binding' else
            context.metadata_directory('e4.calibration'))
        path.mkdir(parents=True)
    elif damage == 'revoked':
        metadata.state['allowed'] = False
    with pytest.raises((PermissionError, ValueError, RuntimeError)):
        with metadata.plane.read_context() as writer:
            context.writer = writer
            with retained_e4_bank_metadata(context):
                pytest.fail('unaccepted metadata enabled continuation')


@pytest.mark.parametrize('damage', ('new-file', 'body', 'revoked'))
def test_original_custody_and_namespace_remain_live_until_handoff_closes(metadata, damage):
    with pytest.raises((PermissionError, ValueError, RuntimeError)):
        with metadata.plane.read_context() as writer:
            metadata.context.writer = writer
            with retained_e4_bank_metadata(metadata.context) as guard:
                if damage == 'new-file':
                    (metadata.context.metadata_directory('e4.development') / 'entry.json').write_bytes(b'{}')
                elif damage == 'body':
                    (metadata.root / metadata.requests[0].relative_path).write_bytes(b'{}\n')
                else:
                    metadata.state['allowed'] = False
                guard()
