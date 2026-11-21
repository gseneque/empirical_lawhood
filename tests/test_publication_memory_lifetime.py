# SPDX-License-Identifier: MPL-2.0
"""Complete publication and live guards without retaining released reader indexes."""

import gc
import inspect
from types import SimpleNamespace
from weakref import ref

import pytest

from empirical_lawhood.storage.artifact_sidecars import decode_artifact_sidecar
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.storage.contracts.artifact_sidecar import ArtifactManifestReference
from empirical_lawhood.storage.recursive_custody import AuthenticatedRecursivePayloads
from tests.test_recursive_custody_batched_members import _case
from tests.test_recursive_member_guard_identity import CurrentAccess


def test_default_publication_stores_one_roster_and_linear_member_sidecars(tmp_path):
    observations = []
    for count in (8, 32):
        directory = tmp_path / str(count)
        directory.mkdir()
        plane, manifests, _, _ = _case(directory, count=count, together=True)
        sidecars = tuple(plane.root.resolve(row.materialization.relative_path + '.manifest.json',
            for_write=False).read_bytes() for row in manifests)
        assert all(type(decode_artifact_sidecar(raw)) is ArtifactManifestReference for raw in sidecars)
        with plane.read_context() as reading:
            selected = tuple(reading.read_manifest(row.materialization.relative_path) for row in manifests)
            assert len({id(row.publication) for row in selected}) == 1
            assert len(selected[0].publication.members) == count
            reading.verify_manifests(selected)
        observations.append(sum(map(len, sidecars)))
    # Four times as many members needs about four times the sidecar bytes;
    # identifier digit counts may grow. Repeated rosters would grow sixteenfold.
    assert 3.9 < observations[1] / observations[0] < 4.2
    assert 'compact_manifests' not in inspect.signature(ExternalArtifactPlane.write_batch).parameters
    assert not hasattr(ExternalArtifactPlane, 'write_compact_batch')


@pytest.mark.parametrize('damage', ('access', 'payload', 'sidecar', 'commit'))
def test_active_final_guards_release_stock_reader_metadata_before_owner_exit(tmp_path, damage):
    plane, manifests, members, directory = _case(tmp_path, count=8, together=True)
    access = CurrentAccess()
    failure = PermissionError if damage == 'access' else ArtifactIdentityConflict
    with pytest.raises(failure):
        with plane.read_context() as reading:
            payloads = AuthenticatedRecursivePayloads(plane=reading, directory=directory,
                members=members, original_input_access=access)
            observed = ref(payloads)
            del payloads
            gc.collect()
            assert observed() is None
            assert reading._read_verification.member_preflights
            if damage == 'access':
                access.allowed = False
            else:
                path = (directory / members[0].filename if damage == 'payload' else
                    directory / (members[0].filename + '.manifest.json') if damage == 'sidecar' else
                    plane.root.resolve(manifests[0].publication.commit_marker_relative_path, for_write=False))
                path.write_bytes(b'X' + path.read_bytes()[1:])
    assert observed() is None


def test_detached_access_guard_keeps_authority_but_not_its_reader(tmp_path):
    plane, _, members, directory = _case(tmp_path, count=4, together=True)
    access = CurrentAccess()
    payloads = AuthenticatedRecursivePayloads(plane=plane, directory=directory,
        members=members, original_input_access=access)
    guard, observed = payloads.retained_access_guard(), ref(payloads)
    del payloads
    gc.collect()
    assert observed() is None
    guard()
    access.allowed = False
    with pytest.raises(PermissionError, match='access revoked'):
        guard()


def test_stock_unprotected_reader_requires_no_retained_access_callback(tmp_path):
    plane, _, members, directory = _case(tmp_path, count=4, together=True)
    payloads = AuthenticatedRecursivePayloads(plane=plane, directory=directory, members=members)
    assert payloads.retained_access_guard() is None


def test_declined_metadata_admission_retains_one_authority_without_reader_graphs(tmp_path):
    from empirical_lawhood.api.recursive_inquiry_read import _AuthoredInquiryReads

    plane, _, members, directory = _case(tmp_path, count=4, together=True)
    access, references = CurrentAccess(), []

    class UnsupportedMetadata:
        # An explicitly unsupported optional cache entry, not scientific data.
        def _is_cacheable(self):
            return False

    metadata = UnsupportedMetadata()
    with plane.read_context() as reading:
        owner = _AuthoredInquiryReads(plane, reading)
        try:
            for number in range(8):
                payloads = AuthenticatedRecursivePayloads(plane=reading, directory=directory,
                    members=members, original_input_access=access)
                references.append(ref(payloads))
                value = SimpleNamespace(payloads=payloads, packet=metadata, draft=metadata,
                    implementation=metadata, run=metadata, plan=metadata)
                owner.retain(str(number), value)
                del payloads, value
            gc.collect()
            assert not owner.entries and owner.bytes == 0
            assert len(owner.payload_guards) == 1
            assert {len(guards) for guards in reading._read_verification.member_preflights.values()} == {1}
            assert len(reading._read_verification.retained_access_guards) == 1
            assert all(reference() is None for reference in references)
            access.allowed = False
            with pytest.raises(PermissionError, match='access revoked'):
                owner.require_current()
        finally:
            access.allowed = True
            owner.close()
    assert not owner.payload_guards


def test_guard_snapshot_reuse_keeps_distinct_selected_sets_and_access_owners(tmp_path):
    plane, _, members, directory = _case(tmp_path, count=4, together=True)
    access = CurrentAccess()
    with plane.read_context() as reading:
        for selected, authority in ((members, access), (members[:2], access), (members, CurrentAccess())):
            payloads = AuthenticatedRecursivePayloads(plane=reading, directory=directory,
                members=selected, original_input_access=authority)
            del payloads
        assert len(reading._read_verification.retained_access_guards) == 3
        assert {len(guards) for guards in reading._read_verification.member_preflights.values()} == {3}
    assert not reading._read_verification.retained_access_guards


@pytest.mark.parametrize('admission', ('byte-budget', 'entry-eviction'))
def test_projection_reader_bounds_its_own_optional_metadata(tmp_path, monkeypatch, admission):
    from contextlib import ExitStack
    from empirical_lawhood.api.recursive_inquiry_read import _InquiryRead
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.science.records import decoded_record_store

    plane, _, members, directory = _case(tmp_path, count=2, together=True)
    if admission == 'byte-budget':
        monkeypatch.setattr(decoded_record_store, 'MAX_SHARED_RECORD_BYTES', 1)
    else:
        monkeypatch.setattr(decoded_record_store, 'MAX_SHARED_RECORDS', 1)
    with ExitStack() as lifetime, plane.read_context() as reading:
        projection = _InquiryRead(reading, lifetime, True)
        references = []
        for number in range(2):
            payloads = AuthenticatedRecursivePayloads(plane=reading, directory=directory, members=members)
            references.append(ref(payloads))
            record = ObjectIdentity('software.' + str(number), ObjectIdentity.SCHEMA, '1.0.0', 'a' * 64)
            value = SimpleNamespace(source=record, packet=record, draft=record, implementation=record,
                report=None, products=None, run=record, plan=record, payloads=payloads)
            projection._retain_wave((str(number), False), value)
            del payloads, value
        gc.collect()
        if admission == 'byte-budget':
            assert not projection.waves and projection.wave_bytes == 0
            assert all(reference() is None for reference in references)
        else:
            assert tuple(projection.waves) == (('1', False),)
            assert 0 < projection.wave_bytes <= decoded_record_store.MAX_SHARED_RECORD_BYTES
            assert references[0]() is None and references[1]() is not None
        # These are actual independent file guards, not optional cache state.
        assert reading._read_verification.snapshots


def test_custom_current_callback_keeps_its_live_state_until_final_guard(tmp_path, monkeypatch):
    plane, _, members, directory = _case(tmp_path, count=4, together=True)
    original = AuthenticatedRecursivePayloads.require_current
    allowed = True

    def custom(payloads):
        if not allowed:
            raise PermissionError('custom current reader policy revoked')
        return original(payloads)

    monkeypatch.setattr(AuthenticatedRecursivePayloads, 'require_current', custom)
    with pytest.raises(PermissionError, match='custom current reader policy revoked'):
        with plane.read_context() as reading:
            payloads = AuthenticatedRecursivePayloads(plane=reading, directory=directory,
                members=members, original_input_access=CurrentAccess())
            observed = ref(payloads)
            del payloads
            gc.collect()
            assert observed() is not None
            allowed = False
    gc.collect()
    assert observed() is None
