# SPDX-License-Identifier: MPL-2.0
"""Original E3 access separation and pre-body ordering, software controls only.

Literal product locators below are unpublished metadata. Only the existing
issued-control fixture supplies actual stored test grants; these tests make no
claim of four scientific E3 products, qualification or new native execution.
"""
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from collections import Counter
from contextlib import contextmanager
from contextvars import copy_context
import os
import sys
from typing import ClassVar

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Evidence, SelectedE3E4DevelopmentProgramme
from empirical_lawhood.api import recursive_qualified_parents as authority
from empirical_lawhood.api import selected_e3_access as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane, _ScopedArtifactPlane
from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads, read_recursive_bootstrap_record
from empirical_lawhood.infrastructure import recursive_custody as custody
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt, lineage_parent_sort_key
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
from tests.runtime_platform.test_recursive_compiler import Config
from tests.test_current_result_custody import actual_issued_current_task_controls  # noqa: F401
from tests.test_current_result_historical_access import later_reveal
from tests.test_rubisco_gas_contrast import _real_plane
from tests.test_recursive_report_projection import wave as wave  # noqa: F401


def pin(name, schema, version='1.0.0'):
    return ObjectIdentity(name, schema, version, 'a' * 64)


def literal_originals(f=None, reveal=None):
    package = None if f is None else f.control.package
    issue = pin('issued.disclosed', 'empirical-lawhood/runtime/issued-executable-study-manifest') if f is None else ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study)
    execution = pin('execution.disclosed', 'empirical-lawhood/planning/study-operation-authority') if f is None else ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority)
    package_pin = pin('package.disclosed', 'empirical-lawhood/api/experiment-package') if f is None else ObjectIdentity.from_record(package.package_id, package)
    plan = pin('plan.disclosed', 'empirical-lawhood/runtime/execution-plan') if f is None else ObjectIdentity.from_record(f.plan.execution_plan_id, f.plan)
    selected = pin('reveal.disclosed', 'empirical-lawhood/planning/study-operation-authority') if reveal is None else ObjectIdentity.from_record(reveal.authority_id, reveal)
    return tuple(MatrixSelectedOriginalProduct(RecursivePriorExecutionBinding(
        'binding.disclosed.' + str(index), issue, execution, package_pin, plan,
        'run.disclosed' if f is None else package.run_plan_id, 'task.disclosed.' + str(index),
        pin('receipt.disclosed.' + str(index), CanonicalTaskReceipt.SCHEMA), 'artifact.disclosed.' + str(index),
        pin('product.disclosed.' + str(index), Config.SCHEMA), record_id_field='config_id'), selected)
        for index in range(4))


def evidence(originals):
    parents = tuple(sorted((ArtifactLineageParent(identity, VisibilityCeiling.PROSPECTIVE,
        OutcomeAccess.EVALUATION_SEALED) for value in originals
        for identity in (value.record, value.prior_execution.receipt)), key=lineage_parent_sort_key))
    return SelectedE3E4Evidence('evidence.disclosed', pin('programme.disclosed',
        SelectedE3E4DevelopmentProgramme.SCHEMA, SelectedE3E4DevelopmentProgramme.VERSION), originals, parents)


def test_replacement_selection_preserves_all_original_scientific_bytes():
    originals = literal_originals()
    before = tuple(value.canonical_bytes() for value in originals)
    selected = tuple(replace(value, reveal_authority=replace(value.reveal_authority,
        object_id='reveal.disclosed.replacement')) for value in originals)
    current = owner.SelectedE3CurrentAccess(selected)
    assert current.effective_originals(originals) == selected
    assert tuple(value.canonical_bytes() for value in originals) == before
    assert not hasattr(current, 'identity') and not hasattr(current, 'canonical_bytes')


@pytest.mark.parametrize('field', ('package', 'execution_plan', 'issued_study', 'execution_authority', 'record', 'receipt', 'run_id'))
def test_replacement_selection_refuses_foreign_original_identity(field):
    originals = literal_originals()
    prior = originals[0].prior_execution
    value = getattr(prior, field)
    changed = value + '.foreign' if type(value) is str else replace(value, object_id=value.object_id + '.foreign')
    selected = (replace(originals[0], prior_execution=replace(prior, **{field: changed})), *originals[1:])
    with pytest.raises(PermissionError, match='original product'):
        owner.SelectedE3CurrentAccess(selected).effective_originals(originals)


def test_locator_only_evidence_does_not_launder_model_bearing_records():
    original = evidence(literal_originals())
    access = owner.SelectedE3OriginalInputAccess(None, original.upstream_products,
        original.upstream_products, original.produced_input_parents, ())

    @dataclass(frozen=True)
    class Derived(CanonicalRecord):
        SCHEMA: ClassVar[str] = 'empirical-lawhood/tests/original-parent-derived'
        record_id: str
        parent: ObjectIdentity

    assert access.record_parents(original) == ()
    assert access.record_parents(Config('pure.disclosed', 1)) == ()
    assert access.record_parents(Derived('derived.disclosed', original.upstream_products[0].record)) == original.produced_input_parents


class LaterClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2030, 1, 1, tzinfo=UTC)


def test_actual_stored_replacement_grant_is_fresh_and_survives_scientific_scope_exit(
        actual_issued_current_task_controls, monkeypatch):  # noqa: F811
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    original = literal_originals(f, f.control.reveal)
    replacement = later_reveal(f)
    selected = owner.SelectedE3CurrentAccess(literal_originals(f, replacement)).effective_originals(original)
    parents = evidence(original).produced_input_parents
    monkeypatch.setattr(authority, 'datetime', LaterClock)
    expired = owner.SelectedE3OriginalInputAccess(plane, original, original, parents, ((original[0], f.control.package),))
    with pytest.raises(PermissionError, match='expired'):
        expired.require_current()
    with plane.read_context() as scoped:
        access = owner.SelectedE3OriginalInputAccess(scoped, original, selected, parents, ((selected[0], f.control.package),))
        check = _ScopedArtifactPlane.require_verification_snapshot
        def no_recursive_scientific_snapshot(current):
            if current is scoped:
                pytest.fail('authority check reentered the scientific snapshot')
            return check(current)
        with monkeypatch.context() as patch:
            patch.setattr(_ScopedArtifactPlane, 'require_verification_snapshot', no_recursive_scientific_snapshot)
            access.require_current()
    access.require_current(artifact_writer=plane)
    foreign = replace(replacement, authority_id=replacement.authority_id + '.foreign-subject',
        subject=replace(replacement.subject, object_id='issued.disclosed.foreign'))
    ExternalStudyOperationAuthorityStore(plane).persist(foreign)
    foreign_selected = owner.SelectedE3CurrentAccess(literal_originals(f, foreign)).effective_originals(original)
    refused = owner.SelectedE3OriginalInputAccess(plane, original, foreign_selected, parents,
        ((foreign_selected[0], f.control.package),))
    with pytest.raises(PermissionError, match='subject'):
        refused.require_current()
    load = ExternalStudyOperationAuthorityStore.load
    def revoked(store, authority_id):
        if authority_id == replacement.authority_id:
            raise PermissionError('actual stored replacement revoked')
        return load(store, authority_id)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', revoked)
    with pytest.raises(PermissionError, match='revoked'):
        access.require_current(artifact_writer=plane)
    assert not f.control.executor.invocations


@contextmanager
def _authority_read_work():
    """Count real calls without replacing methods that select custody policy."""
    counts = Counter()
    owners = {
        ExternalArtifactPlane._verify_manifest_snapshot.__code__: 'payload_validations',
        ExternalArtifactPlane._read_current_manifest.__code__: 'sidecar_decodes',
        ExternalStudyOperationAuthorityStore.load.__code__: 'fresh_grant_loads',
        authority._validate_parent_authorities_now.__code__: 'fresh_utc_checks',
    }
    snapshot = ExternalArtifactPlane._require_verification_snapshot_paths.__code__
    def observe(frame, event, arg):
        if event == 'call':
            label = owners.get(frame.f_code)
            if label is not None:
                counts[label] += 1
            if frame.f_code is snapshot:
                counts['snapshot_calls'] += 1
                counts['snapshot_paths'] += len(frame.f_locals['snapshots'])
    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        yield counts
    finally:
        sys.setprofile(previous)


def _actual_original_access(f, writer=None):
    plane = f.control.service.artifact_plane if writer is None else writer
    originals = literal_originals(f, f.control.reveal)
    return owner.SelectedE3OriginalInputAccess(plane, originals, originals,
        evidence(originals).produced_input_parents, ((originals[0], f.control.package),))


def test_original_projection_shares_only_grant_custody_across_independent_access_objects(
        actual_issued_current_task_controls, tmp_path):  # noqa: F811
    """Actual stored grants; this is no claim of completed scientific products."""
    import json
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    measured = []
    for boundaries in (4, 8):
        with _authority_read_work() as work:
            with owner.original_e3_authority_read_context(plane):
                with plane.read_context() as scientific:
                    first = _actual_original_access(f, scientific)
                    # A separate bootstrap may construct a new access object
                    # and a new scientific verification scope in this operation.
                    with scientific.verification_scope() as nested:
                        second = _actual_original_access(f, nested)
                        assert owner._current_authority_reader(scientific) is owner._current_authority_reader(nested)
                        assert owner._current_authority_reader(scientific) is not scientific
                        for index in range(boundaries):
                            assert (first if index % 2 else second).require_current() is None
                assert owner._current_authority_reader(plane) is not None
        assert owner._current_authority_reader(plane) is None
        # Two independently bootstrapped access objects each decode the two
        # actual grants once. Every subsequent access rechecks stored bytes
        # and samples fresh UTC; no authorization verdict is retained.
        assert work['fresh_grant_loads'] == 4
        assert work['fresh_utc_checks'] == boundaries
        assert work['payload_validations'] == 2
        assert work['sidecar_decodes'] <= 4
        measured.append(dict(work))
    assert measured[1]['snapshot_paths'] <= 2 * measured[0]['snapshot_paths']
    (tmp_path / 'original-authority-read-work.json').write_text(json.dumps({
        'boundaries': [4, 8], 'work': measured,
        'claim': 'Actual stored grant custody only; no whole-DEV scaling or scientific acceptance',
    }, sort_keys=True) + '\n')
    assert not f.control.executor.invocations


def test_original_authority_context_never_reenters_scientific_snapshot_and_ended_context_is_fresh(
        actual_issued_current_task_controls):  # noqa: F811
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    with owner.original_e3_authority_read_context(plane):
        with plane.read_context() as scientific:
            access = _actual_original_access(f, scientific)
            snapshot = _ScopedArtifactPlane.require_verification_snapshot.__code__
            def no_scientific_reentry(frame, event, arg):
                if event == 'call' and frame.f_code is snapshot:
                    assert frame.f_locals['self'] is not scientific
            previous = sys.getprofile()
            sys.setprofile(no_scientific_reentry)
            try:
                access.require_current()
                copied = copy_context()
            finally:
                sys.setprofile(previous)
    # Even a copied context cannot reuse an ended grant verification lifetime.
    with _authority_read_work() as fresh:
        copied.run(access.require_current, artifact_writer=plane)
    assert fresh['payload_validations'] == 2
    assert fresh['fresh_grant_loads'] == 2 and fresh['fresh_utc_checks'] == 1


def test_generic_parent_authority_refresh_keeps_a_warm_scientific_snapshot_separate(
        actual_issued_current_task_controls):  # noqa: F811
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    record = Config('config.authority-isolation', 1)
    publication = plane.write_batch((ArtifactWriteRequest(record.config_id,
        'authority-isolation/science.json', record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        'application/json', 'publication.authority-isolation', 'authority-isolation',
        record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (),
        OutcomeAccess.DEVELOPMENT_VISIBLE),))[0]
    scientific_path = plane.root.resolve(publication.materialization.relative_path, for_write=False)
    with plane.read_context() as scientific:
        scientific.verify_manifest(plane.read_manifest(publication.materialization.relative_path))
        snapshot = ExternalArtifactPlane._require_verification_snapshot_paths.__code__
        observed = []
        def isolated(frame, event, arg):
            if event == 'call' and frame.f_code is snapshot:
                paths = tuple(frame.f_locals['snapshots'])
                observed.append(paths)
                assert scientific_path not in paths
        previous = sys.getprofile()
        sys.setprofile(isolated)
        try:
            authority._require_parent_authorities_current(_actual_original_access(f).entries, scientific)
        finally:
            sys.setprofile(previous)
        assert observed and max(map(len, observed)) <= 6


@pytest.mark.parametrize('operand', ('payload', 'sidecar', 'marker'))
@pytest.mark.parametrize('guard', ('access', 'final'))
def test_shared_original_authority_context_refuses_immediate_same_size_mutation(
        actual_issued_current_task_controls, tmp_path, operand, guard):  # noqa: F811
    import json
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    access = _actual_original_access(f)
    relative = ExternalStudyOperationAuthorityStore._relative_path(f.control.reveal.authority_id)
    manifest = plane.read_manifest(relative)
    selected = (relative if operand == 'payload' else relative + '.manifest.json'
        if operand == 'sidecar' else manifest.publication.commit_marker_relative_path)
    path = plane.root.resolve(selected, for_write=False)
    raw = path.read_bytes()
    # Corrupt real bytes without changing size or manipulating filesystem time.
    changed = bytes([raw[0] ^ 1]) + raw[1:]
    observed = {}
    with pytest.raises((ArtifactIdentityConflict, ValueError, PermissionError)):
        with owner.original_e3_authority_read_context(plane):
            access.require_current()
            before = path.stat()
            path.write_bytes(changed)
            after = path.stat()
            observed = {'same_size': after.st_size == before.st_size,
                'stat_identity_equal': all(getattr(before, name) == getattr(after, name)
                    for name in ('st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))}
            assert observed['same_size']
            if guard == 'access':
                access.require_current()
    (tmp_path / 'original-authority-mutation.json').write_text(json.dumps({
        'operand': operand, 'guard': guard, 'observed': observed,
        'refused': True, 'clock_or_fsync_manipulation': False,
    }, sort_keys=True) + '\n')


def test_shared_original_authority_context_reloads_revocation_and_expiry(
        actual_issued_current_task_controls, monkeypatch):  # noqa: F811
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    access = _actual_original_access(f)
    with owner.original_e3_authority_read_context(plane):
        access.require_current()
        with monkeypatch.context() as patch:
            patch.setattr(authority, 'datetime', LaterClock)
            with pytest.raises(PermissionError, match='expired'):
                access.require_current()
    load = ExternalStudyOperationAuthorityStore.load
    def revoked(store, authority_id):
        if authority_id == f.control.reveal.authority_id:
            raise PermissionError('stored original grant revoked')
        return load(store, authority_id)
    with owner.original_e3_authority_read_context(plane):
        access.require_current()
        monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', revoked)
        with pytest.raises(PermissionError, match='revoked'):
            access.require_current()


def test_original_authority_context_keeps_foreign_policy_and_custom_reads_eager(
        actual_issued_current_task_controls, monkeypatch):  # noqa: F811
    from empirical_lawhood.runtime.artifacts import ArtifactSemanticValidationRegistry
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    with owner.original_e3_authority_read_context(plane):
        foreign = plane.with_semantic_validation_registry(ArtifactSemanticValidationRegistry('foreign.original-read', ()))
        assert owner._current_authority_reader(foreign) is None
        access = _actual_original_access(f, foreign)
        with _authority_read_work() as eager:
            access.require_current()
            access.require_current()
        assert eager['payload_validations'] == 4
        verify = ExternalArtifactPlane.verify_manifest
        calls = []
        def custom_manifest(current, *args, **kwargs):
            calls.append(args[0])
            return verify(current, *args, **kwargs)
        # A class policy remains in the scope's ordinary eager implementation.
        # This control makes no instance-hook preservation claim.
        monkeypatch.setattr(ExternalArtifactPlane, 'verify_manifest', custom_manifest)
        assert owner._current_authority_reader(plane) is None
        _actual_original_access(f).require_current()
        assert len(calls) == 2


def test_shared_grant_record_reuse_still_hashes_bytes_when_stat_identity_is_masked(
        actual_issued_current_task_controls, monkeypatch):  # noqa: F811
    from tests.test_reduced_artifact_verification import _mask_changed_stat
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    access = _actual_original_access(f)
    path = plane.root.resolve(ExternalStudyOperationAuthorityStore._relative_path(
        f.control.reveal.authority_id), for_write=False)
    with pytest.raises(ArtifactIdentityConflict):
        with owner.original_e3_authority_read_context(plane):
            access.require_current()
            original = path.read_bytes()
            _mask_changed_stat(monkeypatch, path)
            path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
            access.require_current()


def test_copied_thread_context_owns_a_separate_original_grant_reader(actual_issued_current_task_controls):  # noqa: F811
    from concurrent.futures import ThreadPoolExecutor
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    access = _actual_original_access(f)
    with owner.original_e3_authority_read_context(plane):
        access.require_current()
        parent = owner._current_authority_reader(plane)
        copied = copy_context()
        def child():
            assert owner._current_authority_reader(plane) is None
            with owner.original_e3_authority_read_context(plane):
                assert owner._current_authority_reader(plane) is not parent
                with _authority_read_work() as work:
                    access.require_current()
                assert work['fresh_grant_loads'] == 2
            assert owner._current_authority_reader(plane) is None
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(copied.run, child).result()
        assert owner._current_authority_reader(plane) is parent
        access.require_current()


def published_packet(tmp_path):
    root = tmp_path / 'closed-bootstrap'
    plane = _real_plane(root)
    records = {name: Config('config.' + name.removesuffix('.json'), index)
        for index, name in enumerate(('draft.json', 'implementation.json', 'private.json'))}
    members = tuple(RecursiveWaveMember(name, ObjectIdentity.from_record('member.' + name.removesuffix('.json'), record),
        len(record.canonical_bytes())) for name, record in sorted(records.items()))
    packet = AuthoredRecursiveWave('packet.disclosed', members[0].identity, members[1].identity, members)
    records['authored-wave.json'] = packet
    publications = plane.write_batch(tuple(ArtifactWriteRequest('artifact.' + name.removesuffix('.json'),
        'authored/' + name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json',
        'publication.closed-bootstrap', 'authored', record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY,
        (), OutcomeAccess.DEVELOPMENT_VISIBLE) for name, record in sorted(records.items())))
    return plane, packet, publications


def test_bootstrap_reads_only_closed_metadata_even_with_unloaded_publication_siblings(tmp_path, monkeypatch):
    plane, packet, _ = published_packet(tmp_path)
    original_open = os.open
    def no_private_body(path, *args, **kwargs):
        if not isinstance(path, int) and Path(path).name == 'private.json':
            pytest.fail('bootstrap opened an unrelated body before original access')
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(os, 'open', no_private_body)
    assert read_recursive_bootstrap_record(plane, 'authored/authored-wave.json', AuthoredRecursiveWave) == packet


@pytest.mark.parametrize('bound', ('in_memory_payload_bytes', 'control_record_bytes'))
def test_bootstrap_selected_byte_bound_refuses_before_body_open(tmp_path, monkeypatch, bound):
    plane, _, _ = published_packet(tmp_path)
    plane.custody_limits = replace(plane.custody_limits, **{bound: 1})
    original_open = os.open
    def no_packet_body(path, *args, **kwargs):
        if not isinstance(path, int) and Path(path).name == 'authored-wave.json':
            pytest.fail('bootstrap body opened before its selected byte admission')
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(os, 'open', no_packet_body)
    with pytest.raises(ValueError, match='selected in-memory or control byte bound'):
        read_recursive_bootstrap_record(plane, 'authored/authored-wave.json', AuthoredRecursiveWave)


def test_payload_guard_refuses_before_any_member_hash_or_decode(tmp_path, monkeypatch):
    plane, packet, _ = published_packet(tmp_path)
    def no_body(*args, **kwargs):
        pytest.fail('publication body verification preceded the original-access guard')
    monkeypatch.setattr(plane, 'verify_manifests_members', no_body)
    class Refused:
        def require_current(self):
            raise PermissionError('original reveal expired before body access')
        def require_member(self, manifest):
            self.require_current()
    with pytest.raises(PermissionError, match='expired before body'):
        AuthenticatedRecursivePayloads(plane=plane, directory=Path(plane.root.contract.canonical_path) / 'authored',
            members=packet.members, original_input_access=Refused())


def test_payload_guard_refreshes_after_heavy_canonical_verification(tmp_path, monkeypatch):
    plane, packet, _ = published_packet(tmp_path)
    events = []
    class Access:
        expired = False
        def require_current(self):
            if self.expired:
                raise PermissionError('original reveal expired during canonical verification')
        def require_member(self, manifest):
            self.require_current()
    access = Access()
    inspect = AuthenticatedRecursivePayloads._inspect_member
    def verified(current, name, member, manifest):
        result = inspect(current, name, member, manifest)
        events.append(name)
        if name == 'private.json':
            access.expired = True
        return result
    monkeypatch.setattr(AuthenticatedRecursivePayloads, '_inspect_member', verified)
    with pytest.raises(PermissionError, match='expired during canonical'):
        AuthenticatedRecursivePayloads(plane=plane, directory=Path(plane.root.contract.canonical_path) / 'authored',
            members=packet.members, original_input_access=access)
    assert events == ['draft.json', 'implementation.json', 'private.json']


@pytest.mark.parametrize('operation', ('exposed', 'getitem', 'chunks'))
def test_verify_return_expiry_refuses_before_direct_body_reopen(tmp_path, monkeypatch, operation):
    plane, packet, _ = published_packet(tmp_path)
    directory = Path(plane.root.contract.canonical_path) / 'authored'
    class Access:
        expired = False
        def require_current(self):
            if self.expired:
                raise PermissionError('original reveal expired at publication verification return')
        def require_member(self, manifest):
            self.require_current()
    access = Access()
    payloads = AuthenticatedRecursivePayloads(plane=plane, directory=directory, members=packet.members,
        original_input_access=access)
    verify = plane.verify_manifest
    def expire(manifest, **kwargs):
        result = verify(manifest, **kwargs)
        access.expired = True
        return result
    monkeypatch.setattr(plane, 'verify_manifest', expire)
    opened = []
    original_open = os.open
    def only_authorized_open(path, *args, **kwargs):
        if not isinstance(path, int) and Path(path).name == 'draft.json':
            opened.append(access.expired)
            assert not access.expired, 'direct body reopened after grant expiry'
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(os, 'open', only_authorized_open)
    with pytest.raises(PermissionError, match='verification return'):
        if operation == 'exposed':
            custody.read_exposed_recursive_payload(plane, payloads.manifest('draft.json'),
                maximum_bytes=packet.members[0].size_bytes, original_input_access=access)
        elif operation == 'getitem':
            payloads['draft.json']
        else:
            tuple(payloads.chunks('draft.json'))
    assert opened and not any(opened)


def test_stream_refreshes_before_second_exact_byte_scan(tmp_path):
    raw = b'original bounded scientific input'
    path = tmp_path / 'streamed-input.bin'
    path.write_bytes(raw)
    calls = []
    def current():
        calls.append(len(calls))
        if len(calls) == 2:
            raise PermissionError('original reveal expired before second scan')
    from hashlib import sha256
    stream = custody.iter_exact_custody_file_chunks(path, size_bytes=len(raw), expected_sha256=sha256(raw).hexdigest(),
        maximum_chunk_bytes=len(raw), read_guard=current)
    assert next(stream) == raw
    with pytest.raises(PermissionError, match='second scan'):
        next(stream)
    assert calls == [0, 1]


def test_product_verification_expiry_refuses_before_independent_body_rehash(wave, monkeypatch):
    """Actual PURE receipts/plan; clock spy supplies no scientific authority."""
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import _external_inputs, _retained_plans
    _, draft, _, payloads = load_authored_wave(directory=wave.directory, artifact_writer=wave.plane, lazy_payloads=True)
    _, plan, index = _retained_plans(payloads, draft)
    inputs = _external_inputs(plane=wave.plane, plan=plan, draft=draft, payloads=payloads, read_only=True)
    from empirical_lawhood.api.recursive_operations import operation_catalog
    codecs = operation_catalog()[2]
    target = plan.tasks[0].outputs[0].logical_artifact_id
    class Access:
        expired = False
        def require_current(self):
            if self.expired:
                raise PermissionError('original reveal expired after product verification')
        def require_member(self, manifest):
            self.require_current()
    access = Access()
    verify = wave.plane.verify_manifest_members
    def expire(manifest, **kwargs):
        result = verify(manifest, **kwargs)
        if manifest.logical.logical_artifact_id == target:
            access.expired = True
        return result
    monkeypatch.setattr(wave.plane, 'verify_manifest_members', expire)
    opened = []
    read = custody._verified_product_path
    def no_late_rehash(**kwargs):
        opened.append(kwargs['logical'].logical_artifact_id)
        assert not access.expired, 'independent product body rehashed after grant expiry'
        return read(**kwargs)
    monkeypatch.setattr(custody, '_verified_product_path', no_late_rehash)
    with pytest.raises(PermissionError, match='after product verification'):
        custody.read_recursive_products(plane=wave.plane, plan=plan, index=index, external_inputs=inputs,
            output_codecs=codecs, original_input_access=access)
    assert target not in opened



@pytest.mark.parametrize('custom_policy', (False, True))
def test_four_original_publication_replays_reuse_only_stock_base_and_reload_grants(
        actual_issued_current_task_controls, monkeypatch, custom_policy):  # noqa: F811
    """Actual issue custody only; literal locators are not four completed E3 products."""
    from empirical_lawhood.infrastructure import study_issue
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    originals = literal_originals(f, f.control.reveal)
    base_reads = []
    read = study_issue.ExternalIssuedStudyPublisher._read_immutable_manifest
    def counted_read(publisher, payload, kind, **options):
        if kind is type(f.control.package.issued_study.base):
            base_reads.append(kind)
        return read(publisher, payload, kind, **options)
    # The stock reader compares the retained exact record with all stored
    # bytes instead of decoding it again. Count that actual validation owner.
    monkeypatch.setattr(study_issue.ExternalIssuedStudyPublisher, '_read_immutable_manifest', counted_read)
    if custom_policy:
        verify = ExternalArtifactPlane.verify_manifest
        def custom_verify(current, *args, **options):
            return verify(current, *args, **options)
        monkeypatch.setattr(ExternalArtifactPlane, 'verify_manifest', custom_verify)
    with _authority_read_work() as work:
        with plane.read_context() as writer:
            publisher = study_issue.ExternalIssuedStudyPublisher(artifact_plane=writer,
                authority_store=ExternalStudyOperationAuthorityStore(writer),
                grantee_id=study_issue.PROGRAMME_ISSUE_GRANTEE_ID)
            with publisher.read_context() as issued:
                for original in originals:
                    manifest, reveal = authority._replay_parent_authority(
                        original, f.control.package, writer, _issued_reader=issued)
                    assert manifest == f.control.package.issued_study
                    assert reveal == f.control.reveal
                assert len(base_reads) == (4 if custom_policy else 1)
    assert work['fresh_grant_loads'] == 16
    assert work['fresh_utc_checks'] == 8
    assert not f.control.executor.invocations
    with pytest.raises(ArtifactIdentityConflict, match='ended'):
        authority._replay_parent_authority(originals[0], f.control.package, writer, _issued_reader=issued)


@pytest.mark.parametrize('damage', ('type', 'writer', 'grantee'))
def test_original_publication_reader_refuses_foreign_owner_or_writer(
        actual_issued_current_task_controls, damage):  # noqa: F811
    from empirical_lawhood.infrastructure import study_issue
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    original = literal_originals(f, f.control.reveal)[0]
    with plane.read_context() as writer:
        other = (ExternalArtifactPlane(plane.root, plane.validators, plane.semantic_validations,
            custody_limits=plane.custody_limits) if damage == 'writer' else writer)
        publisher = (object() if damage == 'type' else study_issue.ExternalIssuedStudyPublisher(
            artifact_plane=other, authority_store=ExternalStudyOperationAuthorityStore(other),
            grantee_id='operator.foreign' if damage == 'grantee' else study_issue.PROGRAMME_ISSUE_GRANTEE_ID))
        with pytest.raises(PermissionError, match='actual issued-publication reader'):
            authority._replay_parent_authority(original, f.control.package, writer, _issued_reader=publisher)
    assert not f.control.executor.invocations


@pytest.mark.parametrize('damage', ('revoked', 'expired', 'source'))
def test_warm_original_publication_keeps_current_grant_and_source_refusals(
        actual_issued_current_task_controls, monkeypatch, damage):  # noqa: F811
    from empirical_lawhood.infrastructure import study_issue
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    original = literal_originals(f, f.control.reveal)[0]
    with plane.read_context() as writer:
        publisher = study_issue.ExternalIssuedStudyPublisher(artifact_plane=writer,
            authority_store=ExternalStudyOperationAuthorityStore(writer),
            grantee_id=study_issue.PROGRAMME_ISSUE_GRANTEE_ID)
        with publisher.read_context() as issued:
            authority._replay_parent_authority(original, f.control.package, writer, _issued_reader=issued)
            if damage == 'revoked':
                load = ExternalStudyOperationAuthorityStore.load
                def revoked(store, authority_id):
                    if authority_id == f.control.reveal.authority_id:
                        raise PermissionError('actual stored reveal revoked')
                    return load(store, authority_id)
                monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', revoked)
            elif damage == 'expired':
                monkeypatch.setattr(authority, 'datetime', LaterClock)
            else:
                original = replace(original, prior_execution=replace(original.prior_execution,
                    issued_study=replace(original.issued_study, object_id='issued.foreign')))
            with pytest.raises(PermissionError):
                authority._replay_parent_authority(original, f.control.package, writer, _issued_reader=issued)
    assert not f.control.executor.invocations


def test_warm_original_publication_final_guard_refuses_same_stat_base_corruption(
        actual_issued_current_task_controls):  # noqa: F811
    from empirical_lawhood.infrastructure import study_issue
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    original = literal_originals(f, f.control.reveal)[0]
    path = plane.root.resolve('issued-programmes/' + f.control.package.issued_study.base.issue_id
        + '/manifest.json', for_write=False)
    with pytest.raises(ArtifactIdentityConflict):
        with plane.read_context() as writer:
            publisher = study_issue.ExternalIssuedStudyPublisher(artifact_plane=writer,
                authority_store=ExternalStudyOperationAuthorityStore(writer),
                grantee_id=study_issue.PROGRAMME_ISSUE_GRANTEE_ID)
            with publisher.read_context() as issued:
                authority._replay_parent_authority(original, f.control.package, writer, _issued_reader=issued)
                raw, before = path.read_bytes(), path.stat()
                path.write_bytes(b'[' + raw[1:])
                os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
                authority._replay_parent_authority(original, f.control.package, writer, _issued_reader=issued)
    assert not f.control.executor.invocations
