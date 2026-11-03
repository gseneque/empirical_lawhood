# SPDX-License-Identifier: MPL-2.0
"""Bounded original native inspection; historical bytes are exposed software fixtures."""

from collections import Counter
from contextlib import contextmanager
import json
from pathlib import Path
import sys

import pytest

from empirical_lawhood.api import recursive_qualified_parents as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from tests.runtime_platform.test_recursive_prior_native_replay import _blocked_progress, _stored
from tests.test_artifact_read_context import _work


def _replay(fixture, writer):
    return owner._prior_native_subwork(writer, fixture.binding, fixture.plan, fixture.by_task)


def _completed_reader(fixture, plane):
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=fixture.parent.execution_plan,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.EVALUATION_SEALED)
    return ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts,
        parent_contact=fixture.parent, completed_only=True)


@contextmanager
def _scope_work(plane):
    """Count the shared census separately from necessary single-record guards."""
    shared, counts = [None], Counter()
    snapshot = ExternalArtifactPlane._require_verification_snapshot_paths.__code__
    digest = bounded_file_sha256.__code__
    with _work() as all_work:
        previous = sys.getprofile()
        def observe(frame, event, arg):
            previous(frame, event, arg)
            if event == 'call':
                if frame.f_code is snapshot and frame.f_locals['snapshots'] is shared[0]:
                    counts['snapshot_calls'] += 1
                    counts['snapshot_paths'] += len(shared[0])
                elif (frame.f_code is digest and frame.f_back.f_code is snapshot
                        and frame.f_back.f_locals['snapshots'] is shared[0]):
                    counts['snapshot_content_bytes'] += frame.f_locals['maximum_bytes']
                    counts['snapshot_content_checks'] += 1
        sys.setprofile(observe)
        try:
            with plane.read_context() as reading:
                shared[0] = reading._read_verification.snapshots
                yield reading, counts, all_work
        finally:
            sys.setprofile(previous)


@pytest.fixture
def original(tmp_path, monkeypatch):
    _blocked_progress(monkeypatch)
    fixture = _stored(tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail('completed custody read requested recovery or publication')
    monkeypatch.setattr(ExternalNativeSubworkStore, 'recover', forbidden)
    monkeypatch.setattr(ExternalTaskReceiptStore, 'commit', forbidden)
    return fixture


@pytest.mark.parametrize('count', (8, 16))
def test_full_native_census_keeps_whole_scope_digest_work_bounded(tmp_path, monkeypatch, count):
    _blocked_progress(monkeypatch)
    fixture = _stored(tmp_path, subwork_count=count)
    root = Path(fixture.plane.root.contract.canonical_path)
    total_stored_bytes = sum(path.stat().st_size for path in root.rglob('*') if path.is_file())
    with _scope_work(fixture.plane) as (reading, work, all_work):
        actual = _replay(fixture, reading)
    assert tuple(row.inspection for row in actual) == fixture.inspections
    assert tuple(row.binding for row in actual) == fixture.binding.native_subwork
    (tmp_path / 'native-census-read-work.json').write_text(json.dumps({
        'native_entries': count, 'total_stored_bytes': total_stored_bytes,
        'whole_scope_work': dict(work), 'all_work': dict(all_work),
        'new_native_contact_count': 0, 'scope': 'EXPOSED_SOFTWARE_CUSTODY_ONLY',
    }, sort_keys=True) + '\n')
    assert work['snapshot_calls'] <= 2
    assert work['snapshot_content_bytes'] <= 2 * total_stored_bytes
    assert work['snapshot_content_checks'] == work['snapshot_paths']


@pytest.mark.parametrize('damage', ('output', 'completion', 'receipt', 'parent-contact', 'sidecar', 'marker'))
def test_completed_native_read_retains_exact_final_mutation_guard(original, damage):
    definition = original.definitions[0]
    output = original.inspections[0].outputs[0]
    if damage == 'receipt':
        run, task, attempt = original.store._receipt_locator(definition)
        relative = f'runs/{run}/receipts/{task}/{attempt}.json'
    elif damage == 'parent-contact':
        relative = original.store.parent_contacts._path(original.parent.run_id, original.parent.task_id)
    elif damage == 'completion':
        relative = original.store._root(definition) + '/completion.json'
    elif damage == 'marker':
        relative = output.publication.commit_marker_relative_path
    else:
        relative = output.materialization.relative_path + ('.manifest.json' if damage == 'sidecar' else '')
    with pytest.raises(ArtifactIdentityConflict):
        with original.plane.read_context() as reading:
            assert tuple(row.inspection for row in _replay(original, reading)) == original.inspections
            path = reading.root.resolve(relative, for_write=False)
            raw = path.read_bytes()
            changed = b'X' + raw[1:]
            assert changed != raw and len(changed) == len(raw)
            path.write_bytes(changed)


def test_completed_native_read_rechecks_current_member_access(original):
    allowed, calls = True, []
    def access(manifest):
        calls.append(manifest.materialization.relative_path)
        if not allowed:
            raise PermissionError('current native evidence access revoked')
    with pytest.raises(PermissionError, match='access revoked'):
        with original.plane.read_context(before_member=access) as reading:
            assert tuple(row.inspection for row in _replay(original, reading)) == original.inspections
            first_calls = len(calls)
            allowed = False
            with pytest.raises(PermissionError, match='access revoked'):
                _replay(original, reading)
            assert len(calls) > first_calls


def test_completed_native_read_requires_its_live_context(original):
    with original.plane.read_context() as reading:
        reader = _completed_reader(original, reading)
        assert reader.inspect(original.definitions[0]) == original.inspections[0]
    with pytest.raises(ArtifactIdentityConflict, match='scope has ended'):
        reader.inspect(original.definitions[0])


def test_ordinary_completed_inspection_keeps_its_eager_snapshot(original):
    with pytest.raises(ArtifactIdentityConflict):
        with original.plane.verification_scope() as reading:
            reader = _completed_reader(original, reading)
            assert reader.inspect(original.definitions[0]) == original.inspections[0]
            path = reading.root.resolve(original.inspections[0].outputs[0].materialization.relative_path,
                for_write=False)
            raw = path.read_bytes()
            path.write_bytes(b'X' + raw[1:])
            with pytest.raises(ArtifactIdentityConflict):
                reader.inspect(original.definitions[1])


@pytest.mark.parametrize('count', (8, 16))
def test_public_parent_inspection_checks_its_whole_census_a_constant_number_of_times(tmp_path, monkeypatch, count):
    from empirical_lawhood.infrastructure.native_parent_finalization import (
        _native_parent_definitions, inspect_native_parent_return,
    )
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

    _blocked_progress(monkeypatch)
    fixture = _stored(tmp_path, subwork_count=count)
    work = PreparedNativeWork(fixture.parent, ('exposed.unit',), ('exposed.slot',),
        fixture.definitions, (fixture.store.read_roster(fixture.parent),))
    def forbidden(*args, **kwargs):
        pytest.fail('read-only parent inspection requested recovery or receipt publication')
    monkeypatch.setattr(ExternalNativeSubworkStore, 'recover', forbidden)
    monkeypatch.setattr(ExternalTaskReceiptStore, 'commit', forbidden)
    whole_census, checks = [None], []
    guard = ExternalArtifactPlane._require_verification_snapshot_paths.__code__
    previous = sys.getprofile()
    def observe(frame, event, _argument):
        if event == 'call':
            if frame.f_code is _native_parent_definitions.__code__:
                whole_census[0] = frame.f_locals['store'].plane._read_verification.snapshots
            elif frame.f_code is guard and frame.f_locals['snapshots'] is whole_census[0]:
                checks.append(len(whole_census[0]))
    sys.setprofile(observe)
    try:
        observed = inspect_native_parent_return(store=fixture.store, work=work)
    finally:
        sys.setprofile(previous)
    assert observed.inspections == fixture.inspections
    assert 1 <= len(checks) <= 4
    assert checks[-1] > count  # Complete closing custody includes every child.
