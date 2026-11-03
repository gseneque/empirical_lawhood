# SPDX-License-Identifier: MPL-2.0
"""Real sealed read operands; exposed custody fixtures confer no authority."""

from dataclasses import replace

import pytest

from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.infrastructure.retained_input_read import RetainedInputRead
from empirical_lawhood.runtime.execution import VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.test_artifact_read_context import _work


def inputs(manifests):
    values = tuple(VerifiedArtifactInput(row.logical, row.materialization) for row in manifests)
    bindings = tuple(WorkerInputBinding.from_verified(row, kind=WorkerInputKind.EXTERNAL) for row in values)
    return values, bindings, sum(row.size_bytes for row in bindings)


def count_copies(monkeypatch):
    copies, original = [], artifacts._anonymous_input_descriptor
    def create():
        copies.append(1)
        return original()
    monkeypatch.setattr(artifacts, '_anonymous_input_descriptor', create)
    return copies


def test_common_inputs_are_sealed_once_with_independent_cursors_and_live_access(tmp_path, monkeypatch):
    from empirical_lawhood.api import current_result_custody
    from empirical_lawhood.kernel import decoding
    from empirical_lawhood.kernel.provenance import ObjectIdentity

    plane, manifests = _publication(tmp_path, 2)
    values, bindings, size = inputs(manifests)
    copies, access = count_copies(monkeypatch), []
    decodes, decode = [], decoding.decode_canonical_bytes_with_identity
    def observed(raw, kind, **kwargs):
        decodes.append(kind)
        return decode(raw, kind, **kwargs)
    monkeypatch.setattr(decoding, 'decode_canonical_bytes_with_identity', observed)
    raw = tuple(plane.root.resolve(row.materialization.relative_path, for_write=False).read_bytes() for row in manifests)
    with plane.read_context(before_member=lambda row: access.append(row.logical.logical_artifact_id)) as reading:
        controls = current_result_custody.CurrentResultPlanReader(reading)
        with RetainedInputRead(reading, shared_artifact_ids=(row.artifact_id for row in values)) as retained:
            with retained.open_many(values, bindings=bindings, maximum_bytes=size) as first:
                control = controls.read_control(retained.retained_manifest(first[0]), ObjectIdentity, first[0].size_bytes)
                assert first[0].read(1) == raw[0][:1]
                before = len(access)
                with retained.open_many(values, bindings=bindings, maximum_bytes=size) as second:
                    assert tuple(row.read() for row in second) == raw
                    assert first[0].tell() == 1
                    assert first[0].read() == raw[0][1:]
                    assert all(retained.retained_manifest(row) is not None for row in second)
                    assert controls.read_control(retained.retained_manifest(second[0]), ObjectIdentity, second[0].size_bytes) is control
                assert set(access[before:]) == {row.artifact_id for row in values}
            assert len(copies) == 2
            assert decodes == [ObjectIdentity]
            assert retained._bytes == size
        assert retained._bytes == 0 and not retained._retained
        with pytest.raises(RuntimeError, match='lifetime has ended'):
            with retained.open_many(values, bindings=bindings, maximum_bytes=size):
                pass
        with pytest.raises(ValueError, match='closed'):
            first[0].read(1)
        # Worker delivery still seals afresh on every ordinary open.
        for _ in range(2):
            for port in reading.open_many(values, bindings=bindings, maximum_bytes=size):
                port.close()
        assert len(copies) == 6


@pytest.mark.parametrize('limit', ('bytes', 'members'))
def test_cache_bounds_fall_back_to_fresh_inputs_without_relaxing_total_scan_budget(tmp_path, monkeypatch, limit):
    plane, manifests = _publication(tmp_path, 2)
    values, bindings, size = inputs(manifests)
    copies = count_copies(monkeypatch)
    bounds = {'maximum_bytes': bindings[0].size_bytes} if limit == 'bytes' else {'maximum_members': 1}
    with plane.read_context() as reading:
        with RetainedInputRead(reading, shared_artifact_ids=(row.artifact_id for row in values), **bounds) as retained:
            for _ in range(3):
                with retained.open_many(values, bindings=bindings, maximum_bytes=size) as ports:
                    assert len(ports) == 2
            assert len(copies) == 4  # Shared first member once, other member each time.
            assert len(retained._retained) == 1
            assert retained._bytes == bindings[0].size_bytes
            with pytest.raises(artifacts.ArtifactInputLimitExceeded, match='scan budget'):
                with retained.open_many(values, bindings=bindings, maximum_bytes=size - 1):
                    pass
            assert len(copies) == 4


@pytest.mark.parametrize('damage', ('bytes', 'access', 'binding'))
def test_retained_bytes_never_hide_mutation_revocation_or_changed_binding(tmp_path, damage):
    plane, manifests = _publication(tmp_path, 1)
    values, bindings, size = inputs(manifests)
    live = True
    def access(row):
        if not live:
            raise PermissionError('current access revoked')
    with pytest.raises((artifacts.ArtifactIdentityConflict, PermissionError), match='changed|differ|revoked|binding'):
        with plane.read_context(before_member=access) as reading:
            with RetainedInputRead(reading, shared_artifact_ids=(values[0].artifact_id,)) as retained:
                with retained.open_many(values, bindings=bindings, maximum_bytes=size):
                    pass
                if damage == 'access':
                    live = False
                elif damage == 'binding':
                    bindings = (replace(bindings[0], size_bytes=size + 1),)
                else:
                    path = plane.root.resolve(manifests[0].materialization.relative_path, for_write=False)
                    raw = path.read_bytes()
                    path.write_bytes(b'X' + raw[1:])
                with retained.open_many(values, bindings=bindings, maximum_bytes=size) as ports:
                    assert damage == 'bytes'  # Exact final scope guard must still refuse.
                    assert ports[0].read()


def test_custom_open_keeps_fresh_delivery_and_expired_owner_cannot_be_borrowed(tmp_path, monkeypatch):
    plane, manifests = _publication(tmp_path, 1)
    values, bindings, size = inputs(manifests)
    copies = count_copies(monkeypatch)
    with plane.read_context() as reading:
        original = reading.open_many
        monkeypatch.setattr(reading, 'open_many', lambda *args, **kwargs: original(*args, **kwargs))
        with RetainedInputRead(reading, shared_artifact_ids=(values[0].artifact_id,)) as retained:
            for _ in range(2):
                with retained.open_many(values, bindings=bindings, maximum_bytes=size) as ports:
                    assert retained.retained_manifest(ports[0]) is None
            assert len(copies) == 2 and retained._bytes == 0
    with pytest.raises((artifacts.ArtifactIdentityConflict, RuntimeError), match='ended'):
        RetainedInputRead(reading, shared_artifact_ids=())


@pytest.mark.parametrize('count', (8, 16))
def test_unique_read_inputs_do_not_revisit_the_whole_sibling_publication(tmp_path, count):
    plane, manifests = _publication(tmp_path, count)
    values, bindings, _ = inputs(manifests)
    with _work() as work:
        with plane.read_context() as reading:
            with RetainedInputRead(reading, shared_artifact_ids=()) as retained:
                for value, binding in zip(values, bindings, strict=True):
                    with retained.open_many((value,), bindings=(binding,), maximum_bytes=binding.size_bytes) as ports:
                        assert len(ports[0].read()) == binding.size_bytes
                assert retained._bytes == 0  # The fresh-input route, without shared-body retention.
                assert work['payloads'] == 2 * count  # One full closure plus one exact seal per selected member.
                assert work['snapshot_content_checks'] == 0
    assert work['snapshot_content_checks'] == 2 * count + 1  # One final complete byte census.
