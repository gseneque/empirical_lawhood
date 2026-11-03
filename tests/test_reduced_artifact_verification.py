# SPDX-License-Identifier: MPL-2.0
"""Measured read work and forced byte boundaries; software evidence only."""

from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
import sys

import pytest

from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
from empirical_lawhood.infrastructure.artifact_verification import artifact_verification_operation
from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
from empirical_lawhood.infrastructure.publication_metadata import checkpoint_publication_access
from empirical_lawhood.runtime.operational_configuration import ArtifactVerificationMode
from empirical_lawhood.runtime.execution import VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind
from tests.runtime_platform.test_artifact_verification_scope import _publication


def _case(tmp_path, mode='reduced', count=4, workers=1):
    original, manifests = _publication(tmp_path, count)
    plane = artifacts.ExternalArtifactPlane(original.root, original.validators, original.semantic_validations,
        artifact_verification=mode, maximum_parallel_verifications=workers)
    return plane, manifests


@contextmanager
def _work():
    counts = Counter()
    physical = artifacts.ExternalArtifactPlane._verify_manifest_snapshot.__code__
    checkpoint = artifacts.ExternalArtifactPlane._require_verification_snapshot_paths.__code__
    validator = ArtifactProfileValidatorRegistry.validate_file.__code__
    digest = bounded_file_sha256.__code__
    def observe(frame, event, _arg):
        if event == 'call' and frame.f_code is validator:
            counts['deep_validations'] += 1
        elif event == 'call' and frame.f_code is digest and frame.f_back.f_code is checkpoint:
            counts['checkpoint_hashes'] += 1
            counts['checkpoint_hash_bytes'] += frame.f_locals['maximum_bytes']
        elif event == 'return' and frame.f_code is physical:
            counts['member_hash_bytes'] += frame.f_locals.get('observed_bytes', 0)
    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        yield counts
    finally:
        sys.setprofile(previous)


@pytest.mark.parametrize('count', (4, 32))
def test_default_reduced_checkpoints_remove_hash_work_but_keep_final_census(tmp_path, count, record_property):
    plane, manifests = _case(tmp_path, count=count)
    assert plane.artifact_verification is ArtifactVerificationMode.REDUCED
    values, measurements = {}, {}
    for mode in ArtifactVerificationMode:
        plane.artifact_verification = mode
        accesses = []
        with _work() as work:
            with plane.read_context(before_member=lambda value: accesses.append(value.materialization.relative_path)) as reading:
                values[mode] = reading.verify_manifests_members(manifests,
                    validate_members=lambda rows: tuple(sorted(value.fingerprint() for value in rows.values())))
                expected = len(reading._read_verification.snapshots)
                accesses.clear()
                for _ in range(3):
                    reading.require_verification_snapshot()
                assert set(accesses) == {value.materialization.relative_path for value in manifests}
                assert work['checkpoint_hashes'] == (0 if mode is ArtifactVerificationMode.REDUCED else 3 * expected)
            assert work['checkpoint_hashes'] == expected * (1 if mode is ArtifactVerificationMode.REDUCED else 4)
        measurements[mode.value] = dict(work)
        assert work['deep_validations'] == count
    assert values[ArtifactVerificationMode.REDUCED] == values[ArtifactVerificationMode.STRICT]
    record_property('verification_work', measurements)


@pytest.mark.parametrize('mode,expected', (('reduced', 4), ('strict', 12)))
def test_invocation_reuses_exact_format_proofs_across_separate_scopes(tmp_path, mode, expected):
    plane, manifests = _case(tmp_path, mode=mode)
    live, accessed = True, []
    def access(manifest):
        if not live:
            raise PermissionError('current grant revoked')
        accessed.append(manifest.materialization.relative_path)
    with _work() as work, artifact_verification_operation() as ledger:
        for _ in range(3):
            with plane.read_context(before_member=access) as reading:
                reading.verify_manifests(manifests)
            with pytest.raises(artifacts.ArtifactIdentityConflict, match='ended'):
                reading.require_verification_snapshot()
        assert work['deep_validations'] == expected
        assert work['checkpoint_hashes'] == 3 * (2 * len(manifests) + 1)
        assert accessed
        live = False
        with pytest.raises(PermissionError, match='revoked'):
            with plane.read_context(before_member=access) as reading:
                reading.verify_manifests(manifests)
    assert not ledger.active and not ledger.proofs and ledger.bytes == 0
    live = True
    with _work() as fresh, plane.read_context() as reading:
        reading.verify_manifests(manifests)
    assert fresh['deep_validations'] == len(manifests)


@pytest.mark.parametrize('count', (4, 32))
def test_format_proofs_do_not_rehash_the_shared_publication_per_manifest(tmp_path, monkeypatch, count):
    from empirical_lawhood.runtime.artifacts import ArtifactManifest
    plane, manifests = _case(tmp_path, count=count)
    monkeypatch.setattr(ArtifactManifest, 'fingerprint',
        lambda _self: pytest.fail('format proof rehashed an entire sibling publication roster'))
    with artifact_verification_operation(), _work() as work:
        for _ in range(2):
            with plane.read_context() as reading:
                reading.verify_manifests(manifests)
    assert work['deep_validations'] == count
    assert work['checkpoint_hashes'] == 2 * (2 * count + 1)


def _mask_changed_stat(monkeypatch, path):
    original = artifacts.os.stat
    observed = original(path, follow_symlinks=False)
    def masked(value, *args, **kwargs):
        if not isinstance(value, int) and Path(value) == path:
            return observed
        return original(value, *args, **kwargs)
    monkeypatch.setattr(artifacts.os, 'stat', masked)


@pytest.mark.parametrize('boundary', ('final-success', 'final-refusal', 'publication', 'worker'))
@pytest.mark.parametrize('member', ('body', 'sidecar', 'marker'))
def test_forced_boundaries_detect_bytes_even_when_all_stat_fields_are_preserved(tmp_path, monkeypatch, boundary, member):
    plane, manifests = _case(tmp_path, count=2)
    entered = False
    with pytest.raises(artifacts.ArtifactIdentityConflict):
        with plane.read_context() as reading:
            reading.verify_manifests(manifests)
            first = manifests[0]
            relative = (first.materialization.relative_path if member == 'body'
                else first.materialization.relative_path + '.manifest.json' if member == 'sidecar'
                else first.publication.commit_marker_relative_path)
            path = plane.root.resolve(relative, for_write=False)
            raw = path.read_bytes()
            _mask_changed_stat(monkeypatch, path)
            path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
            # The explicitly accepted limitation applies only in the middle.
            reading.require_verification_snapshot()
            if boundary == 'publication':
                checkpoint_publication_access(reading)
            elif boundary == 'worker':
                value = VerifiedArtifactInput(first.logical, first.materialization)
                binding = WorkerInputBinding.from_verified(value, kind=WorkerInputKind.EXTERNAL)
                reading.open_many((value,), bindings=(binding,), maximum_bytes=value.materialization.size_bytes)
            elif boundary == 'final-refusal':
                raise ValueError('consumer refused')
            entered = True
    assert entered is (boundary == 'final-success')


def test_parallel_final_guard_hashes_every_byte_despite_reduced_parent(tmp_path, monkeypatch):
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest
    plane, _ = _case(tmp_path, count=1, workers=2)
    manifest = plane.read_manifest('outputs/member-0.json')
    logical = manifest.logical
    payload = canonical_json_bytes({'schema': logical.payload_schema, 'value': 'a' * (1024**2), 'version': '1.0.0'})
    request = ArtifactWriteRequest('exposed.large', 'large/body.json', logical.payload_schema,
        logical.profile, logical.media_type, 'exposed.large-batch', 'large', payload,
        logical.visibility_ceiling, logical.parent_visibility_ceilings, logical.outcome_access)
    publication = plane.write(request)
    with pytest.raises(artifacts.ArtifactIdentityConflict):
        with plane.read_context() as reading:
            value = reading.read_manifest(publication.materialization.relative_path)
            reading.verify_manifest(value)
            path = plane.root.resolve(value.materialization.relative_path, for_write=False)
            _mask_changed_stat(monkeypatch, path)
            path.write_bytes(payload.replace(b'aaaa', b'baaa', 1))
            reading.require_verification_snapshot()


def test_worker_delivery_always_rehashes_and_revalidates_after_read_cache_hit(tmp_path):
    plane, manifests = _case(tmp_path, count=2)
    with plane.read_context() as reading:
        reading.verify_manifests(manifests)
        value = VerifiedArtifactInput(manifests[0].logical, manifests[0].materialization)
        binding = WorkerInputBinding.from_verified(value, kind=WorkerInputKind.EXTERNAL)
        with _work() as work:
            port, = reading.open_many((value,), bindings=(binding,), maximum_bytes=value.materialization.size_bytes)
        try:
            assert work['deep_validations'] == len(manifests)
            assert work['member_hash_bytes'] == sum(row.materialization.size_bytes for row in manifests)
            assert work['checkpoint_hashes'] == 2 * len(manifests) + 1
        finally:
            port.close()


def test_new_validator_registry_and_changed_manifest_cannot_reuse_proofs(tmp_path):
    plane, manifests = _case(tmp_path, count=2)
    with artifact_verification_operation(), _work() as work:
        with plane.read_context() as reading:
            reading.verify_manifests(manifests)
        other = artifacts.ExternalArtifactPlane(plane.root, ArtifactProfileValidatorRegistry(), plane.semantic_validations)
        with other.read_context() as reading:
            reading.verify_manifests(manifests)
        assert work['deep_validations'] == 2 * len(manifests)
        with plane.read_context() as reading:
            foreign = replace(manifests[0], logical=replace(manifests[0].logical, content_sha256='f' * 64), publication=None)
            with pytest.raises(artifacts.ArtifactIdentityConflict):
                reading.verify_manifest(foreign)


def test_cache_limits_fall_back_without_retaining_payload_or_access(tmp_path, monkeypatch):
    from empirical_lawhood.infrastructure import artifact_verification as cache
    monkeypatch.setattr(cache, 'MAX_VERIFICATION_PROOFS', 1)
    plane, manifests = _case(tmp_path, count=4)
    with artifact_verification_operation() as ledger:
        for _ in range(2):
            with plane.read_context() as reading:
                reading.verify_manifests(manifests)
            assert len(ledger.proofs) <= 1
            assert ledger.bytes <= cache.MAX_VERIFICATION_PROOF_BYTES
        assert not any(callable(value) for value in vars(ledger).values())


def test_nested_public_invocations_have_separate_proofs_and_restore_the_parent(tmp_path):
    plane, manifests = _case(tmp_path, count=2)
    with artifact_verification_operation(new=True) as outer, _work() as work:
        with plane.read_context() as reading:
            reading.verify_manifests(manifests)
        with artifact_verification_operation(new=True) as inner:
            assert inner is not outer
            with plane.read_context() as reading:
                reading.verify_manifests(manifests)
        assert not inner.active and outer.active
        with plane.read_context() as reading:
            reading.verify_manifests(manifests)
        assert work['deep_validations'] == 2 * len(manifests)


def test_custom_inspector_keeps_full_intermediate_checks(tmp_path):
    plane, manifests = _case(tmp_path)
    class Custom(artifacts.LocalFilesystemInspector):
        pass
    plane.root.inspector = Custom()
    with plane.read_context() as reading:
        reading.verify_manifests(manifests)
        with _work() as work:
            reading.require_verification_snapshot()
        assert work['checkpoint_hashes'] == 2 * len(manifests) + 1
