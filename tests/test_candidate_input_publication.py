# SPDX-License-Identifier: MPL-2.0
"""Atomic input custody and bounded durability windows, without scientific authority."""

import errno
from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path
import signal
import stat

import pytest

from empirical_lawhood.infrastructure import candidate_sources as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from tests.test_unrestricted_source_resolution import _root


def _address(directory, raw):
    return owner.ExternalContentAddressedInputResolver.install_path(directory, sha256(raw).hexdigest())


def _same_bucket(count):
    values = []
    for index in range(100_000):
        raw = f"exposed candidate input {index}".encode()
        if sha256(raw).hexdigest().startswith('00'):
            values.append(raw)
            if len(values) == count:
                return values
    raise AssertionError('literal population did not supply a common content-address bucket')


def _sync_spy(monkeypatch):
    original = owner.os.fsync
    events = []

    def observe(descriptor):
        kind = 'directory' if stat.S_ISDIR(os.fstat(descriptor).st_mode) else 'file'
        events.append((kind, Path(os.readlink(f'/proc/self/fd/{descriptor}'))))
        original(descriptor)

    monkeypatch.setattr(owner.os, 'fsync', observe)
    return events


def _no_hardlinks(*_args, **_kwargs):
    raise PermissionError(errno.EPERM, 'exposed filesystem control has no hard links')


def test_removable_fallback_installs_one_fully_synced_write_atomically(tmp_path, monkeypatch):
    raw = b'exact exposed candidate control' * 4096
    events = _sync_spy(monkeypatch)
    written = []
    original_write = owner.os.write
    original_rename = owner.rename_noreplace

    def write(descriptor, value):
        count = original_write(descriptor, value)
        written.append(count)
        return count

    def install(source, target):
        assert not target.exists()
        assert source.read_bytes() == raw
        assert [kind for kind, _ in events] == ['file']
        assert sum(written) == len(raw)
        original_rename(source, target)

    monkeypatch.setattr(owner.os, 'link', _no_hardlinks)
    monkeypatch.setattr(owner.os, 'write', write)
    monkeypatch.setattr(owner, 'rename_noreplace', install)
    publisher = owner.ExternalCandidateInputPublisher(_root(tmp_path))
    result = publisher.publish(raw)
    target = _address(tmp_path, raw)
    assert result.publication_mode == 'ATOMIC_RENAME_NO_REPLACE' and not result.replayed
    assert target.read_bytes() == raw and sum(written) == len(raw)
    assert sum(kind == 'file' for kind, _ in events) == 1
    directories = [path for kind, path in events if kind == 'directory']
    assert directories == [target.parent, target.parent.parent, target.parent.parent.parent, tmp_path]
    assert not tuple(tmp_path.rglob('*.stage'))
    before = target.stat()
    replay = publisher.publish(raw)
    assert replay.replayed and replay.publication_mode == 'EXACT_REPLAY'
    assert target.stat().st_mtime_ns == before.st_mtime_ns and sum(written) == len(raw)
    assert sum(kind == 'file' for kind, _ in events) == 1


def test_bulk_keeps_each_file_synced_but_shares_bounded_directory_windows(tmp_path, monkeypatch):
    payloads = _same_bucket(5)
    events = _sync_spy(monkeypatch)
    monkeypatch.setattr(owner.os, 'link', _no_hardlinks)
    publisher = owner.ExternalCandidateInputPublisher(_root(tmp_path))

    def selected_inputs():
        for index, raw in enumerate(payloads):
            # The fourth member's directory window is durable before asking
            # the caller to produce another payload.
            if index == 4:
                assert sum(kind == 'file' for kind, _ in events) == 4
                assert sum(kind == 'directory' for kind, _ in events) == 4
            yield raw

    published = publisher.publish_many(selected_inputs(), batch_size=4)
    assert tuple(row.content_sha256 for row in published) == tuple(sha256(raw).hexdigest() for raw in payloads)
    assert all(_address(tmp_path, raw).read_bytes() == raw for raw in payloads)
    assert sum(kind == 'file' for kind, _ in events) == 5
    assert sum(kind == 'directory' for kind, _ in events) == 8
    assert all(not row.replayed for row in published)
    before = {raw: _address(tmp_path, raw).stat().st_mtime_ns for raw in payloads}
    replayed = publisher.publish_many((payloads[2], payloads[0], payloads[2]), batch_size=2)
    assert all(row.replayed for row in replayed)
    assert sum(kind == 'file' for kind, _ in events) == 5
    assert all(_address(tmp_path, raw).stat().st_mtime_ns == before[raw] for raw in payloads)


def test_iterator_failure_syncs_published_prefix_and_replay_completes_same_addresses(tmp_path, monkeypatch):
    first, second, third = _same_bucket(3)
    events = _sync_spy(monkeypatch)
    failure = RuntimeError('literal caller stopped producing inputs')
    publisher = owner.ExternalCandidateInputPublisher(_root(tmp_path))

    def interrupted_inputs():
        yield first
        yield second
        raise failure

    with pytest.raises(RuntimeError) as caught:
        publisher.publish_many(interrupted_inputs(), batch_size=64)
    assert caught.value is failure
    assert sum(kind == 'file' for kind, _ in events) == 2
    assert sum(kind == 'directory' for kind, _ in events) == 4
    before = {raw: _address(tmp_path, raw).stat().st_mtime_ns for raw in (first, second)}
    complete = publisher.publish_many((first, second, third))
    assert [row.replayed for row in complete] == [True, True, False]
    assert all(_address(tmp_path, raw).read_bytes() == raw for raw in (first, second, third))
    assert all(_address(tmp_path, raw).stat().st_mtime_ns == before[raw] for raw in before)
    assert not tuple(tmp_path.rglob('*.stage'))


@pytest.mark.parametrize('invalid,error', ((b'', ValueError), ('foreign nonbytes', TypeError), (b'too-long', ValueError)))
def test_invalid_later_member_retains_and_syncs_only_completed_prefix(tmp_path, monkeypatch, invalid, error):
    events = _sync_spy(monkeypatch)
    publisher = owner.ExternalCandidateInputPublisher(_root(tmp_path))
    with pytest.raises(error):
        publisher.publish_many((b'ok', invalid), maximum_bytes=3)
    assert _address(tmp_path, b'ok').read_bytes() == b'ok'
    assert sum(kind == 'file' for kind, _ in events) == 1
    assert sum(kind == 'directory' for kind, _ in events) == 4
    assert not tuple(tmp_path.rglob('*.stage'))


def test_bulk_collision_preserves_foreign_bytes_and_syncs_previous_member(tmp_path, monkeypatch):
    first, collided = _same_bucket(2)
    target = _address(tmp_path, collided)
    target.parent.mkdir(parents=True)
    target.write_bytes(b'foreign bytes at selected address')
    before = target.stat().st_mtime_ns
    events = _sync_spy(monkeypatch)
    publisher = owner.ExternalCandidateInputPublisher(_root(tmp_path))
    with pytest.raises(ArtifactIdentityConflict):
        publisher.publish_many((first, collided))
    assert _address(tmp_path, first).read_bytes() == first
    assert target.read_bytes() == b'foreign bytes at selected address'
    assert target.stat().st_mtime_ns == before
    assert sum(kind == 'file' for kind, _ in events) == 1
    assert sum(kind == 'directory' for kind, _ in events) == 4


def test_stage_name_collision_never_removes_another_creators_file(tmp_path, monkeypatch):
    raw = b'literal occupied temporary name'
    digest = sha256(raw).hexdigest()
    target = _address(tmp_path, raw)
    target.parent.mkdir(parents=True)
    stamp = 123456789
    token = sha256(f'{os.getpid()}\0{stamp}\0{digest}'.encode()).hexdigest()[:24]
    foreign_stage = target.parent / f'.{digest}.{token}.stage'
    foreign_stage.write_bytes(b'other creator owns this staged payload')
    before = foreign_stage.stat().st_mtime_ns
    monkeypatch.setattr(owner.time, 'time_ns', lambda: stamp)
    publisher = owner.ExternalCandidateInputPublisher(_root(tmp_path))
    with pytest.raises(FileExistsError):
        publisher.publish(raw)
    assert not target.exists()
    assert foreign_stage.read_bytes() == b'other creator owns this staged payload'
    assert foreign_stage.stat().st_mtime_ns == before
    monkeypatch.setattr(owner.time, 'time_ns', lambda: stamp + 1)
    assert not publisher.publish(raw).replayed
    assert target.read_bytes() == raw and foreign_stage.exists()


def test_bulk_and_individual_same_roster_keep_file_work_and_reduce_directory_syncs(tmp_path, monkeypatch):
    payloads = sorted(_same_bucket(8), key=lambda raw: sha256(raw).hexdigest())
    original_write, original_sync = owner.os.write, owner.os.fsync
    observed = {}
    active = None

    def write(descriptor, value):
        written = original_write(descriptor, value)
        active['write_calls'] += 1
        active['write_bytes'] += written
        return written

    def sync(descriptor):
        kind = 'directory_fsyncs' if stat.S_ISDIR(os.fstat(descriptor).st_mode) else 'file_fsyncs'
        active[kind] += 1
        original_sync(descriptor)

    monkeypatch.setattr(owner.os, 'write', write)
    monkeypatch.setattr(owner.os, 'fsync', sync)
    for name in ('individual', 'bulk'):
        directory = tmp_path / name
        directory.mkdir()
        active = {'write_calls': 0, 'write_bytes': 0, 'file_fsyncs': 0, 'directory_fsyncs': 0}
        publisher = owner.ExternalCandidateInputPublisher(_root(directory))
        if name == 'individual':
            publications = tuple(publisher.publish(raw) for raw in payloads)
        else:
            publications = publisher.publish_many(iter(payloads), batch_size=64)
        assert all(_address(directory, raw).read_bytes() == raw for raw in payloads)
        observed[name] = {**active, 'publication_modes': sorted({row.publication_mode for row in publications})}
    assert all(row['write_calls'] >= len(payloads) for row in observed.values())
    assert observed['individual']['write_bytes'] == observed['bulk']['write_bytes'] == sum(map(len, payloads))
    assert observed['individual']['file_fsyncs'] == observed['bulk']['file_fsyncs'] == len(payloads)
    assert observed['individual']['directory_fsyncs'] == 4 * len(payloads)
    assert observed['bulk']['directory_fsyncs'] == 4
    (tmp_path / 'durability-work-counts.json').write_text(json.dumps({
        'scope': 'Eight exposed same-bucket inputs; syscall work counts only, not a production benchmark',
        'content_sha256': [sha256(raw).hexdigest() for raw in payloads], 'counts': observed}, sort_keys=True, indent=2) + '\n')


@pytest.mark.parametrize('collision', ('exact', 'different', 'directory', 'symlink-read-refusal'))
def test_atomic_rename_race_rechecks_regular_exact_bytes(tmp_path, monkeypatch, collision):
    raw = b'literal race operand'
    original = owner.rename_noreplace
    original_compare = owner.file_matches_bytes
    monkeypatch.setattr(owner.os, 'link', _no_hardlinks)

    def install(source, target):
        if collision == 'directory':
            target.mkdir()
        else:
            target.write_bytes(b'foreign' if collision == 'different' else raw)
        original(source, target)

    def nofollow_compare(path, expected):
        if collision == 'symlink-read-refusal':
            # VFAT cannot create symlinks. Inject the no-follow reader's
            # ELOOP refusal at the race boundary, never follow a fake link.
            raise OSError(errno.ELOOP, 'exposed no-follow race refusal')
        return original_compare(path, expected)

    monkeypatch.setattr(owner, 'rename_noreplace', install)
    monkeypatch.setattr(owner, 'file_matches_bytes', nofollow_compare)
    publisher = owner.ExternalCandidateInputPublisher(_root(tmp_path))
    if collision == 'exact':
        result = publisher.publish(raw)
        assert result.replayed and result.publication_mode == 'EXACT_REPLAY'
        assert _address(tmp_path, raw).read_bytes() == raw
    else:
        with pytest.raises(ArtifactIdentityConflict):
            publisher.publish(raw)
        target = _address(tmp_path, raw)
        assert target.is_dir() if collision == 'directory' else target.read_bytes() == (b'foreign' if collision == 'different' else raw)
    assert not tuple(tmp_path.rglob('*.stage'))


def test_unsupported_exclusive_rename_fails_closed_without_visible_partial_file(tmp_path, monkeypatch):
    raw = b'no unsafe publication fallback'
    monkeypatch.setattr(owner.os, 'link', _no_hardlinks)

    def unsupported(*_args, **_kwargs):
        raise OSError(errno.ENOSYS, 'literal unsupported exclusive publication')

    monkeypatch.setattr(owner, 'rename_noreplace', unsupported)
    with pytest.raises(OSError) as caught:
        owner.ExternalCandidateInputPublisher(_root(tmp_path)).publish(raw)
    assert caught.value.errno == errno.ENOSYS
    assert not _address(tmp_path, raw).exists()
    assert not tuple(tmp_path.rglob('*.stage'))


def test_file_close_error_still_cleans_owned_stage_and_flushes_ancestry(tmp_path, monkeypatch):
    raw = b'literal close failure after file sync'
    original_close = owner.os.close
    events = _sync_spy(monkeypatch)
    interrupted = False

    def close(descriptor):
        nonlocal interrupted
        fail = not interrupted and stat.S_ISREG(os.fstat(descriptor).st_mode)
        original_close(descriptor)
        if fail:
            interrupted = True
            raise OSError(errno.EIO, 'literal file close error')

    monkeypatch.setattr(owner.os, 'close', close)
    with pytest.raises(OSError) as caught:
        owner.ExternalCandidateInputPublisher(_root(tmp_path)).publish(raw)
    assert caught.value.errno == errno.EIO and interrupted
    assert not _address(tmp_path, raw).exists()
    assert not tuple(tmp_path.rglob('*.stage'))
    assert sum(kind == 'directory' for kind, _ in events) == 4


class _InterruptedPublication(BaseException):
    pass


@pytest.mark.parametrize('phase', ('partial-write', 'after-rename'))
def test_interrupted_member_cleans_owned_stage_and_syncs_every_complete_address(tmp_path, monkeypatch, phase):
    first, second = _same_bucket(2)
    events = _sync_spy(monkeypatch)
    original_write, original_rename = owner.os.write, owner.rename_noreplace
    monkeypatch.setattr(owner.os, 'link', _no_hardlinks)
    writes = 0

    def write(descriptor, value):
        nonlocal writes
        writes += 1
        if phase == 'partial-write' and writes > 1:
            if writes == 2:
                return original_write(descriptor, value[:2])
            raise _InterruptedPublication('literal partial write interruption')
        return original_write(descriptor, value)

    def install(source, target):
        original_rename(source, target)
        if phase == 'after-rename' and target == _address(tmp_path, second):
            raise _InterruptedPublication('literal interruption after atomic visibility')

    monkeypatch.setattr(owner.os, 'write', write)
    monkeypatch.setattr(owner, 'rename_noreplace', install)
    with pytest.raises(_InterruptedPublication):
        owner.ExternalCandidateInputPublisher(_root(tmp_path)).publish_many((first, second))
    assert _address(tmp_path, first).read_bytes() == first
    assert _address(tmp_path, second).exists() is (phase == 'after-rename')
    if phase == 'after-rename':
        assert _address(tmp_path, second).read_bytes() == second
    assert sum(kind == 'directory' for kind, _ in events) == 4
    assert not tuple(tmp_path.rglob('*.stage'))


def test_directory_sync_failure_attempts_all_ancestors_and_returns_no_success(tmp_path, monkeypatch):
    raw = b'exposed directory sync failure'
    original = owner.os.fsync
    directories = []

    def failed_sync(descriptor):
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            directories.append(Path(os.readlink(f'/proc/self/fd/{descriptor}')))
            if len(directories) == 1:
                raise OSError(errno.EIO, 'literal first directory sync failure')
        original(descriptor)

    monkeypatch.setattr(owner.os, 'fsync', failed_sync)
    publisher = owner.ExternalCandidateInputPublisher(_root(tmp_path))
    with pytest.raises(OSError) as caught:
        publisher.publish(raw)
    assert caught.value.errno == errno.EIO
    target = _address(tmp_path, raw)
    assert directories == [target.parent, target.parent.parent, target.parent.parent.parent, tmp_path]
    assert target.read_bytes() == raw
    assert publisher.publish(raw).replayed
    assert not tuple(tmp_path.rglob('*.stage'))


@pytest.mark.parametrize('before_install', (True, False))
def test_process_death_exposes_absent_or_complete_address_and_recovers_exactly(tmp_path, before_install):
    context = multiprocessing.get_context('fork')
    receiving, sending = context.Pipe(duplex=False)
    raw = b'exposed crash-safe candidate input' * 2048

    def child():
        owner.os.link = _no_hardlinks
        original = owner.rename_noreplace

        def install(source, target):
            if not before_install:
                original(source, target)
            sending.send('staged-before-install' if before_install else 'installed-complete')
            signal.pause()

        owner.rename_noreplace = install
        owner.ExternalCandidateInputPublisher(_root(tmp_path)).publish(raw)

    process = context.Process(target=child)
    process.start()
    try:
        assert receiving.poll(20), 'publication child never reached its exact interruption point'
        assert receiving.recv() == ('staged-before-install' if before_install else 'installed-complete')
    finally:
        if process.is_alive():
            process.kill()
        process.join(5)
        receiving.close()
        sending.close()
    assert process.exitcode == -signal.SIGKILL
    target = _address(tmp_path, raw)
    assert target.exists() is not before_install
    if not before_install:
        assert target.read_bytes() == raw
    replay = owner.ExternalCandidateInputPublisher(_root(tmp_path)).publish(raw)
    assert replay.replayed is not before_install
    assert target.read_bytes() == raw


@pytest.mark.parametrize('batch_size', (True, 0, -1, 1.5))
def test_invalid_window_refuses_before_consuming_inputs(tmp_path, batch_size):
    def unselected_inputs():
        raise AssertionError('invalid window must refuse before caller input consumption')
        yield b'unselected'

    with pytest.raises(ValueError, match='batch_size'):
        owner.ExternalCandidateInputPublisher(_root(tmp_path)).publish_many(unselected_inputs(), batch_size=batch_size)
    assert not tuple(tmp_path.iterdir())
