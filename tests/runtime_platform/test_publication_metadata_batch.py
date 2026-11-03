"""Staged-module metadata custody controls; no source capture, arrays or science.

Only literal ObjectIdentity JSON is published through the actual immutable plane.
The installed publication owner supplies both original singular and closed-batch
APIs. Literal fixtures carry no scientific or source authority.
"""
from dataclasses import replace
from hashlib import sha256
import cProfile
import json
import sys
from time import perf_counter

import pytest

from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.infrastructure import publication_metadata as original
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalRootUnavailable
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits, ArtifactProfile, ArtifactWriteRequest, ExternalRootContract



@pytest.fixture(scope='module')
def candidate():
    return original


def publication_case(directory, count=4, shape='singletons'):
    directory.mkdir(parents=True)
    mount = next(parent for parent in directory.parents if parent.is_mount())
    plane = artifacts.ExternalArtifactPlane(artifacts.GuardedExternalRoot(ExternalRootContract(
        'exposed.linear-metadata', 'Literal metadata software custody only', str(directory), str(mount),
        'empirical-lawhood/testing/linear-bookkeeping', 1)))
    records = tuple(ObjectIdentity('exposed.literal.'+str(index), ObjectIdentity.SCHEMA, '1.0.0',
        sha256(('literal-'+str(index)).encode()).hexdigest()) for index in range(count))
    requests = tuple(ArtifactWriteRequest(record.object_id, 'metadata/member-'+str(index)+'.json',
        record.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json',
        'exposed.shared' if shape != 'singletons' else 'exposed.single.'+str(index), 'metadata',
        record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)
        for index, record in enumerate(records))
    if shape == 'singletons':
        publications = tuple(plane.write(value) for value in requests)
    else:
        publications = plane.write_batch(requests, compact_manifests=shape == 'shared')
    manifests = tuple(plane.read_manifest(value.materialization.relative_path) for value in publications)
    return plane, publications, records, manifests


def consume_records(plane, records, publications, members):
    observed = []
    for record, publication in zip(records, publications, strict=True):
        path = publication.materialization.relative_path
        manifest = members[path]
        assert manifest.logical == publication.logical
        assert manifest.materialization == publication.materialization
        raw = plane.root.resolve(path, for_write=False).read_bytes()
        observed.append(decode_canonical_bytes(raw, ObjectIdentity,
            maximum_bytes=publication.materialization.size_bytes))
    assert tuple(observed) == records
    return tuple(observed)


def measured_operation(candidate, case, *, batch):
    plane, publications, records, _ = case
    codes = {'snapshot_guards': artifacts.ExternalArtifactPlane._require_verification_snapshot_paths.__code__,
        'guarded_resolves': artifacts.GuardedExternalRoot.resolve.__code__,
        'physical_member_validations': artifacts.ExternalArtifactPlane._verify_manifest_snapshot.__code__}
    profile = cProfile.Profile()
    started = perf_counter()
    profile.enable()
    try:
        with plane.verification_scope() as scoped:
            if batch:
                answer = candidate.consume_published_materializations(scoped, publications,
                    consume=lambda members: consume_records(scoped, records, publications, members))
            else:
                manifests = tuple(original.authenticate_published_materialization(scoped, value)
                    for value in publications)
                # Preserve original singular accesses; consume only after all.
                members = {value.materialization.relative_path: value for value in manifests}
                answer = consume_records(scoped, records, publications, members)
    finally:
        profile.disable()
    stats = profile.getstats()
    counts = {name: sum(entry.callcount for entry in stats if entry.code is code)
        for name, code in codes.items()}
    return answer, {**counts, 'profiled_wall_seconds': perf_counter()-started,
        'declared_payload_bytes': sum(value.materialization.size_bytes for value in publications),
        'claim': 'Actual code-entry counts; declared payload bytes are not total I/O. Profiled software timing is not whole-derive speedup.'}


@pytest.mark.parametrize('shape', ('singletons', 'shared', 'shared-legacy'))
def test_actual_batch_matches_singular_and_verifies_complete_roster(candidate, tmp_path, shape):
    case = publication_case(tmp_path/'actual', shape=shape)
    expected, old = measured_operation(candidate, case, batch=False)
    actual, new = measured_operation(candidate, case, batch=True)
    assert actual == expected == case[2]
    assert old['physical_member_validations'] == new['physical_member_validations'] == len(case[1])
    assert new['snapshot_guards'] <= 5


@pytest.mark.parametrize('shape', ('singletons', 'shared'))
def test_two_sizes_have_constant_union_guards_and_linear_resolves(candidate, tmp_path, shape):
    observations = []
    for count in (4, 16):
        case = publication_case(tmp_path/('size-'+str(count)), count, shape)
        _, serial = measured_operation(candidate, case, batch=False)
        _, batch = measured_operation(candidate, case, batch=True)
        assert serial['snapshot_guards'] == 2*count+1
        assert batch['snapshot_guards'] == 5
        assert serial['physical_member_validations'] == batch['physical_member_validations'] == count
        observations.append({'count':count, 'serial':serial, 'batch':batch})
    small, large = observations
    assert large['batch']['guarded_resolves'] <= 5*small['batch']['guarded_resolves']
    assert large['serial']['guarded_resolves'] > large['batch']['guarded_resolves']
    (tmp_path/'actual-counts.json').write_text(json.dumps(observations, sort_keys=True, indent=2)+'\n')


def test_equal_duplicate_handle_deduplicates_but_complete_siblings_remain(candidate, tmp_path):
    plane, publications, records, _ = publication_case(tmp_path/'actual', shape='shared')
    with plane.verification_scope() as scoped:
        seen = candidate.consume_published_materializations(scoped, (publications[0], publications[0]),
            consume=lambda members: tuple(sorted(members)))
    assert seen == tuple(sorted(value.materialization.relative_path for value in publications))
    assert len(seen) == len(records)


def test_conflicting_same_path_and_invalid_roster_refuse_before_callback(candidate, tmp_path):
    plane, publications, _, _ = publication_case(tmp_path/'actual')
    bad = replace(publications[0], manifest_materialization=replace(
        publications[0].manifest_materialization, physical_sha256='f'*64))
    called = []
    with pytest.raises(ValueError, match='aliases'):
        candidate.consume_published_materializations(plane, (publications[0], bad), consume=lambda value:called.append(value))
    with pytest.raises(ValueError, match='nonempty closed tuple'):
        candidate.consume_published_materializations(plane, [], consume=lambda value:called.append(value))
    with pytest.raises(TypeError, match='exact original write results'):
        candidate.consume_published_materializations(plane, ({},), consume=lambda value:called.append(value))
    assert called == []


def test_exact_sidecar_handle_and_roster_bound_remain_required(candidate, tmp_path):
    plane, publications, _, _ = publication_case(tmp_path/'actual')
    bad = replace(publications[0], manifest_materialization=replace(
        publications[0].manifest_materialization, physical_sha256='f'*64))
    called = []
    with pytest.raises(ValueError, match='exact original manifest materialization'):
        candidate.consume_published_materializations(plane, (bad,), consume=lambda value:called.append(value))
    limited = artifacts.ExternalArtifactPlane(plane.root, plane.validators, plane.semantic_validations,
        custody_limits=replace(ArtifactCustodyLimits(), publication_members=1))
    with pytest.raises(ValueError, match='roster exceeds'):
        candidate.consume_published_materializations(limited, publications, consume=lambda value:called.append(value))
    assert called == []


@pytest.mark.parametrize('damage', ('body', 'sidecar', 'marker', 'ancestor'))
def test_metadata_to_plural_gap_refuses_actual_target_mutation(candidate, tmp_path, damage):
    plane, publications, _, manifests = publication_case(tmp_path/'actual')
    called, triggered = [], []
    actual_code = artifacts._ScopedArtifactPlane.verify_manifests_members.__code__
    def mutation(frame, event, _arg):
        if event != 'call' or frame.f_code is not actual_code or triggered:
            return
        triggered.append(True)
        material = publications[0].materialization
        if damage == 'ancestor':
            folder = plane.root.resolve(material.relative_path, for_write=False).parent
            moved = folder.with_name(folder.name+'-original')
            folder.rename(moved)
            folder.symlink_to(moved, target_is_directory=True)
        else:
            relative = (material.relative_path if damage == 'body' else material.relative_path+'.manifest.json'
                if damage == 'sidecar' else manifests[0].publication.commit_marker_relative_path)
            target = plane.root.resolve(relative, for_write=False)
            target.write_bytes(target.read_bytes()+b' ')
    assert sys.getprofile() is None
    sys.setprofile(mutation)
    try:
        with pytest.raises(ExternalRootUnavailable if damage == 'ancestor' else ArtifactIdentityConflict):
            candidate.consume_published_materializations(plane, publications, consume=lambda members:called.append(members))
    finally:
        sys.setprofile(None)
    assert triggered == [True] and called == []


@pytest.mark.parametrize('when', ('checkpoint', 'before-consume', 'during-consume'))
def test_prior_observed_input_mutation_never_escapes(candidate, tmp_path, when):
    plane, publications, _, _ = publication_case(tmp_path/'actual')
    prior_request = ArtifactWriteRequest('exposed.prior-train-metadata', 'prior/train-control.json', ObjectIdentity.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'exposed.prior-train-metadata', 'prior',
        ObjectIdentity('exposed.prior', ObjectIdentity.SCHEMA, '1.0.0', 'b'*64).canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)
    prior = plane.write(prior_request)
    prior_manifest = plane.read_manifest(prior.materialization.relative_path)
    called, returned = [], []
    def change():
        path = plane.root.resolve(prior.materialization.relative_path, for_write=False)
        path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ArtifactIdentityConflict):
        with plane.verification_scope() as scoped:
            scoped.verify_manifest(prior_manifest)
            if when != 'during-consume':
                change()
            if when == 'checkpoint':
                candidate.checkpoint_publication_access(scoped)
            def consume(members):
                called.append(True)
                change()
                return tuple(members)
            returned.append(candidate.consume_published_materializations(scoped, publications, consume=consume))
    assert returned == []
    assert called == ([True] if when == 'during-consume' else [])


def test_callback_exception_identity_and_final_mutation_guard(candidate, tmp_path):
    plane, publications, _, _ = publication_case(tmp_path/'actual')
    sentinel = RuntimeError('literal callback refusal')
    def fail(_members):
        raise sentinel
    with pytest.raises(RuntimeError) as caught:
        candidate.consume_published_materializations(plane, publications, consume=fail)
    assert caught.value is sentinel
    def changed_then_fail(_members):
        path = plane.root.resolve(publications[0].materialization.relative_path, for_write=False)
        path.write_bytes(path.read_bytes()+b' ')
        raise sentinel
    with pytest.raises(ArtifactIdentityConflict):
        candidate.consume_published_materializations(plane, publications, consume=changed_then_fail)


@pytest.mark.parametrize('owner', (artifacts.ExternalArtifactPlane, artifacts._ScopedArtifactPlane))
@pytest.mark.parametrize('hook', ('read_manifest', 'verify_manifest'))
def test_custom_singular_hooks_are_called_and_refuse_before_callback(candidate, tmp_path, monkeypatch, owner, hook):
    plane, publications, _, _ = publication_case(tmp_path/'actual')
    original_hook = getattr(owner, hook)
    sentinel, calls, callback = RuntimeError('custom singular refusal'), [], []
    def custom(self, *args, **kwargs):
        calls.append(True)
        if len(calls) == 2:
            raise sentinel
        return original_hook(self, *args, **kwargs)
    with plane.verification_scope() as scoped:
        monkeypatch.setattr(owner, hook, custom)
        assert not candidate.supports_closed_publication_access(scoped)
        with pytest.raises(RuntimeError) as caught:
            candidate.consume_published_materializations(scoped, publications, consume=lambda members:callback.append(members))
        assert caught.value is sentinel and len(calls) == 2 and callback == []


@pytest.mark.parametrize('owner', (artifacts.ExternalArtifactPlane, artifacts._ScopedArtifactPlane))
def test_custom_write_policy_cannot_select_new_ordering(candidate, tmp_path, monkeypatch, owner):
    plane, publications, _, _ = publication_case(tmp_path/'actual')
    old = getattr(owner, 'write')
    calls = []
    def custom(self, value):
        calls.append(value.logical_artifact_id)
        return old(self, value)
    with plane.verification_scope() as scoped:
        monkeypatch.setattr(owner, 'write', custom)
        assert not candidate.supports_closed_publication_access(scoped)
        with pytest.raises(TypeError, match='unchanged stock read/write'):
            candidate.checkpoint_publication_access(scoped)
        assert calls == []
        answer = candidate.consume_published_materializations(scoped, publications,
            consume=lambda members:tuple(sorted(members)))
        assert answer == tuple(sorted(value.materialization.relative_path for value in publications))


@pytest.mark.parametrize('hook', ('verify', '_manifest_materialization', '_stream_identity'))
def test_instance_access_hook_denial_survives_exact_serial_fallback(candidate, tmp_path, hook):
    plane, publications, _, _ = publication_case(tmp_path/'actual')
    sentinel, calls, callback = RuntimeError('instance access denial'), [], []
    def denied(*args, **kwargs):
        calls.append(True)
        raise sentinel
    setattr(plane, hook, denied)
    assert not candidate.supports_closed_publication_access(plane)
    with pytest.raises(RuntimeError) as caught:
        candidate.consume_published_materializations(plane, publications, consume=lambda members:callback.append(members))
    assert caught.value is sentinel and calls == [True] and callback == []


@pytest.mark.parametrize('owner', (artifacts.ExternalArtifactPlane, artifacts._ScopedArtifactPlane))
@pytest.mark.parametrize('hook', ('verify', '_manifest_materialization', '_stream_identity'))
def test_class_access_hook_denial_survives_serial_fallback(candidate, tmp_path, monkeypatch, owner, hook):
    plane, publications, _, _ = publication_case(tmp_path/'actual')
    sentinel, calls, callback = RuntimeError('class access denial'), [], []
    def denied(*args, **kwargs):
        calls.append(True)
        raise sentinel
    with plane.verification_scope() as scoped:
        monkeypatch.setattr(owner, hook, denied)
        assert not candidate.supports_closed_publication_access(scoped)
        with pytest.raises(RuntimeError) as caught:
            candidate.consume_published_materializations(scoped, publications, consume=lambda members:callback.append(members))
        assert caught.value is sentinel and calls == [True] and callback == []


def test_unknown_instance_policy_keeps_original_singular_route(candidate, tmp_path):
    plane, publications, records, _ = publication_case(tmp_path/'actual')
    plane.custom_policy = 'explicit unknown customization'
    assert not candidate.supports_closed_publication_access(plane)
    assert candidate.consume_published_materializations(plane, publications,
        consume=lambda members:consume_records(plane, records, publications, members)) == records



def test_custom_duplicate_handles_preserve_each_original_singular_call(candidate, tmp_path, monkeypatch):
    plane, publications, _, _ = publication_case(tmp_path/'actual')
    calls, original_hook = [], plane.verify_manifest
    def counted(manifest):
        calls.append(manifest.materialization.relative_path)
        return original_hook(manifest)
    plane.verify_manifest = counted
    assert not candidate.supports_closed_publication_access(plane)
    answer = candidate.consume_published_materializations(plane, (publications[0], publications[0]),
        consume=lambda members:tuple(sorted(members)))
    expected = publications[0].materialization.relative_path
    assert calls == [expected, expected]
    assert answer == (expected,)
