# SPDX-License-Identifier: MPL-2.0
"""Real byte/access lifetime controls around a disclosed DEV replay seam."""
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import selected_e4_method_runtime as original
from empirical_lawhood.api.selected_e4_native_runtime import _development_replay
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.test_recursive_public_service import _plane


def _scope(tmp_path, monkeypatch):
    plane = _plane(tmp_path / 'custody')
    body = canonical_json_bytes({'schema': 'empirical-lawhood/testing/disclosed-replay',
        'version': '1.0.0', 'value': {'disclosed': True}})
    publication = plane.write(ArtifactWriteRequest('disclosed.replay', 'disclosed/original.json',
        'empirical-lawhood/testing/disclosed-replay', ArtifactProfile.CANONICAL_JSON,
        'application/json', 'disclosed.replay', 'disclosed', body,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    calls, checks = [], []
    allowed = [True]
    value = object(), object()
    def current(**kwargs):
        checks.append(True)
        if not allowed[0]:
            raise PermissionError('original current reveal revoked')
    def read(*, writer, _observe_original_access=None, **options):
        calls.append(options)
        writer.verify_manifest(writer.read_manifest(publication.materialization.relative_path))
        current()
        if _observe_original_access is not None:
            _observe_original_access(SimpleNamespace(require_current=current))
        return value
    monkeypatch.setattr(original, 'original_development_products', read)
    return plane, publication, calls, checks, allowed, value


def test_one_complete_replay_keeps_current_access_and_expires(tmp_path, monkeypatch):
    plane, _, calls, checks, _, value = _scope(tmp_path, monkeypatch)
    with plane.read_context() as view, _development_replay(view) as read:
        options = dict(writer=view, locator=SimpleNamespace(allow_partial=False), data_id='original')
        assert read(**options) is value and read(**options) is value
        assert len(calls) == 1 and len(checks) >= 3
    with pytest.raises(PermissionError, match='escaped'):
        read(**options)


@pytest.mark.parametrize('damage', ('bytes', 'access', 'operands', 'reader'))
def test_reused_replay_rejects_changed_bytes_access_and_operands(tmp_path, monkeypatch, damage):
    plane, publication, calls, _, allowed, _ = _scope(tmp_path, monkeypatch)
    path = plane.root.resolve(publication.materialization.relative_path, for_write=False)
    raw = path.read_bytes()
    try:
        with pytest.raises((PermissionError, ArtifactIdentityConflict)):
            with plane.read_context() as view, _development_replay(view) as read:
                options = dict(writer=view, locator=SimpleNamespace(allow_partial=False), data_id='original')
                read(**options)
                if damage == 'bytes':
                    path.write_bytes(raw.replace(b'true', b'null'))
                elif damage == 'access':
                    allowed[0] = False
                elif damage == 'operands':
                    options['data_id'] = 'substituted'
                else:
                    options['writer'] = plane
                read(**options)
                pytest.fail('changed original custody escaped the replay guard')
        assert len(calls) == 1
    finally:
        allowed[0] = True
        if damage == 'bytes':
            path.write_bytes(raw)


def test_partial_acquisition_keeps_separate_reads(tmp_path, monkeypatch):
    plane, _, calls, _, _, _ = _scope(tmp_path, monkeypatch)
    with plane.read_context() as view, _development_replay(view) as read:
        for _ in range(2):
            read(writer=view, locator=SimpleNamespace(allow_partial=True), data_id='original')
    assert len(calls) == 2
