# SPDX-License-Identifier: MPL-2.0
"""Actual file ownership, publication and failure controls; no scientific entry."""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
import errno
import hashlib
import os
from pathlib import Path
import pickle
import threading

import pytest

from empirical_lawhood.storage import owned_output
from empirical_lawhood.storage.artifact_validation import ArtifactProfileValidatorRegistry
from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.storage.contracts.artifacts import ArtifactCustodyLimits, ArtifactProfile
from empirical_lawhood.storage.owned_output import OwnedOutputFile
from tests.test_artifact_publication_admission import _census, _plane, _requests


@contextmanager
def _source(path, payload):
    source = OwnedOutputFile(path)
    try:
        source.write(payload)
        source.seal()
        yield source
    finally:
        source.close()


def _request(request, source, *, adopt=True):
    selected = request.as_stream()
    bound = min(64, selected.maximum_bytes)
    stream = source.chunks(bound)
    return replace(selected, chunks=stream if adopt else iter(stream), maximum_chunk_bytes=bound)


def test_adoption_keeps_exact_publication_and_never_deletes_the_final_file(tmp_path):
    request, = _requests(1)
    baseline = _plane(tmp_path / 'baseline')
    current = _plane(tmp_path / 'current')
    with _source(tmp_path / 'original', request.payload) as source:
        original = baseline.write_stream(_request(request, source, adopt=False))
    with _source(tmp_path / 'adopted', request.payload) as source:
        inode = (tmp_path / 'adopted').stat().st_ino
        result = current.write_stream(_request(request, source))
        assert not (tmp_path / 'adopted').exists()
        final = current.root.resolve(result.materialization.relative_path, for_write=False)
        assert final.stat().st_ino == inode
    assert result == original
    assert final.read_bytes() == request.payload
    assert _census(tmp_path / 'baseline') == _census(tmp_path / 'current')
    assert not tuple(tmp_path.rglob('*.partial'))


@pytest.mark.parametrize('adopt', (False, True))
def test_measured_payload_writes_flushes_and_verification_passes(tmp_path, monkeypatch, record_property, adopt):
    request, = _requests(1)
    plane = _plane(tmp_path / 'artifacts')
    scratch = tmp_path / 'scratch'
    final = plane.root.resolve(request.relative_path, for_write=False)
    payload_paths = {scratch, final}
    calls = Counter()
    fdopen, fsync = os.fdopen, os.fsync
    stage = ExternalArtifactPlane._write_staged_stream
    identity = ExternalArtifactPlane._stream_identity
    validate = ArtifactProfileValidatorRegistry.validate_file
    chunks = OwnedOutputFile._chunks

    class MeteredFile:
        def __init__(self, handle, selected):
            self.handle, self.selected = handle, selected
        def __getattr__(self, name):
            return getattr(self.handle, name)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return self.handle.__exit__(*args)
        def write(self, raw):
            count = self.handle.write(raw)
            if self.selected:
                calls['payload_written_bytes'] += count
            return count

    def opened(fd, *args, **kwargs):
        path = Path(os.readlink(f'/proc/self/fd/{fd}'))
        return MeteredFile(fdopen(fd, *args, **kwargs), path in payload_paths)
    def flushed(fd):
        if Path(os.readlink(f'/proc/self/fd/{fd}')) in payload_paths:
            calls['payload_fsyncs'] += 1
        return fsync(fd)
    def staged(path, selected):
        payload_paths.add(path)
        return stage(path, selected)
    def hashed(path, **kwargs):
        if path in payload_paths:
            calls['publication_payload_hash_passes'] += 1
        return identity(path, **kwargs)
    def validated(self, path, selected, **kwargs):
        if path in payload_paths:
            calls['payload_validations'] += 1
        return validate(self, path, selected, **kwargs)
    def consumed(self, maximum_chunk_bytes):
        calls['source_read_passes'] += 1
        yield from chunks(self, maximum_chunk_bytes)

    monkeypatch.setattr(os, 'fdopen', opened)
    monkeypatch.setattr(os, 'fsync', flushed)
    monkeypatch.setattr(ExternalArtifactPlane, '_write_staged_stream', staticmethod(staged))
    monkeypatch.setattr(ExternalArtifactPlane, '_stream_identity', staticmethod(hashed))
    monkeypatch.setattr(ArtifactProfileValidatorRegistry, 'validate_file', validated)
    monkeypatch.setattr(OwnedOutputFile, '_chunks', consumed)
    with _source(scratch, request.payload) as source:
        plane.write_stream(_request(request, source, adopt=adopt))
    assert calls == {
        'payload_written_bytes': len(request.payload) * (1 if adopt else 2),
        'payload_fsyncs': 1 if adopt else 2,
        'source_read_passes': 1,
        'publication_payload_hash_passes': 2,
        'payload_validations': 1,
    }
    record_property('publication_work', dict(calls))


@pytest.mark.parametrize('damage', ('same-size', 'replace', 'symlink', 'hardlink', 'truncate'))
def test_changed_sealed_source_refuses_and_closes_descriptors(tmp_path, damage):
    request, = _requests(1)
    plane = _plane(tmp_path / 'artifacts')
    path = tmp_path / 'scratch'
    with _source(path, request.payload) as source:
        descriptor = source._reader
        stream = _request(request, source)
        if damage == 'same-size':
            path.write_bytes(b'X' + request.payload[1:])
        elif damage == 'replace':
            path.rename(tmp_path / 'original-retained')
            path.write_bytes(request.payload)
        elif damage == 'symlink':
            path.rename(tmp_path / 'original-retained')
            path.symlink_to(tmp_path / 'original-retained')
        elif damage == 'hardlink':
            os.link(path, tmp_path / 'alias')
        else:
            path.write_bytes(request.payload[:-1])
        with pytest.raises(ArtifactIdentityConflict):
            plane.write_stream(stream)
        assert not plane.root.resolve(request.relative_path, for_write=False).exists()
    with pytest.raises(OSError):
        os.fstat(descriptor)
    if damage in ('replace', 'symlink'):
        assert path.read_bytes() == request.payload


@pytest.mark.parametrize('where', ('before-rename', 'after-rename', 'directory-fsync', 'validator', 'bind', 'intent', 'final-rename', 'commit'))
@pytest.mark.parametrize('exception', (OSError, KeyboardInterrupt))
def test_interrupted_adoption_has_no_false_commit_and_retries_exactly(tmp_path, monkeypatch, where, exception):
    request, = _requests(1)
    plane = _plane(tmp_path / 'artifacts')
    failed = False
    def interrupt():
        nonlocal failed
        if not failed:
            failed = True
            raise exception('injected publication interruption')
    with monkeypatch.context() as patch:
        if where in ('before-rename', 'after-rename'):
            original = owned_output.rename_noreplace
            def rename(*args, **kwargs):
                if where == 'before-rename':
                    interrupt()
                original(*args, **kwargs)
                interrupt()
            patch.setattr(owned_output, 'rename_noreplace', rename)
        elif where == 'directory-fsync':
            original = os.fsync
            def fsync(fd):
                import stat
                if stat.S_ISDIR(os.fstat(fd).st_mode):
                    interrupt()
                original(fd)
            patch.setattr(os, 'fsync', fsync)
        elif where == 'validator':
            def validate(*args, **kwargs):
                interrupt()
            patch.setattr(ArtifactProfileValidatorRegistry, 'validate_file', validate)
        elif where in ('bind', 'intent'):
            name = '_bind_staged_batch' if where == 'bind' else '_write_publication_intent'
            original = getattr(plane, name)
            def wrapped(*args, **kwargs):
                result = original(*args, **kwargs)
                interrupt()
                return result
            patch.setattr(plane, name, wrapped)
        else:
            original = ExternalArtifactPlane._rename_noreplace
            def final_rename(source, destination):
                original(source, destination)
                if ((where == 'commit' and destination.name.endswith('.commit.json'))
                        or (where == 'final-rename' and destination == plane.root.resolve(request.relative_path, for_write=False))):
                    interrupt()
            patch.setattr(ExternalArtifactPlane, '_rename_noreplace', staticmethod(final_rename))
        with _source(tmp_path / 'scratch', request.payload) as source:
            with pytest.raises(exception):
                plane.write_stream(_request(request, source))
    assert failed
    # Commit publication is the durable boundary, even if the caller was interrupted.
    commits = tuple((tmp_path / 'artifacts').rglob('*.commit.json'))
    assert bool(commits) == (where == 'commit')
    with _source(tmp_path / 'retry', request.payload) as source:
        result = plane.write_stream(_request(request, source))
    plane.verify_manifest(plane.read_manifest(result.materialization.relative_path))
    assert not tuple(tmp_path.rglob('*.batch.partial'))


def test_foreign_staging_destination_survives_failed_adoption(tmp_path, monkeypatch):
    request, = _requests(1)
    plane = _plane(tmp_path / 'artifacts')
    occupied = []
    original = owned_output.rename_noreplace
    def collide(source, destination, **kwargs):
        parent = Path(os.readlink(f'/proc/self/fd/{kwargs["destination_dir_fd"]}'))
        path = parent / destination
        path.write_bytes(b'foreign bytes')
        occupied.append(path)
        original(source, destination, **kwargs)
    monkeypatch.setattr(owned_output, 'rename_noreplace', collide)
    with _source(tmp_path / 'scratch', request.payload) as source:
        with pytest.raises(FileExistsError):
            plane.write_stream(_request(request, source))
    assert occupied[0].read_bytes() == b'foreign bytes'


def test_cross_device_rename_uses_existing_stream_copy(tmp_path, monkeypatch):
    request, = _requests(1)
    plane = _plane(tmp_path / 'artifacts')
    def cross_device(*args, **kwargs):
        raise OSError(errno.EXDEV, 'injected cross-device rename')
    monkeypatch.setattr(owned_output, 'rename_noreplace', cross_device)
    with _source(tmp_path / 'scratch', request.payload) as source:
        inode = (tmp_path / 'scratch').stat().st_ino
        result = plane.write_stream(_request(request, source))
        assert (tmp_path / 'scratch').exists()
        final = plane.root.resolve(result.materialization.relative_path, for_write=False)
        assert final.stat().st_ino != inode
    assert final.read_bytes() == request.payload


def test_replay_checks_actual_source_bytes_without_consuming_the_committed_file(tmp_path, monkeypatch):
    request, = _requests(1)
    plane = _plane(tmp_path / 'artifacts')
    plane.write(request)
    before = _census(tmp_path / 'artifacts')
    monkeypatch.setattr(owned_output, 'rename_noreplace', lambda *args, **kwargs: pytest.fail('replay moved a file'))
    with _source(tmp_path / 'exact', request.payload) as source:
        assert not plane.write_stream(_request(request, source)).created
    with _source(tmp_path / 'wrong', b'X' + request.payload[1:]) as source:
        with pytest.raises(ArtifactIdentityConflict):
            plane.write_stream(_request(request, source))
    assert _census(tmp_path / 'artifacts') == before


def test_file_is_single_use_and_cannot_cross_thread_process_or_copy(tmp_path):
    with _source(tmp_path / 'scratch', b'abc') as source:
        with pytest.raises(TypeError):
            pickle.dumps(source)
        with ThreadPoolExecutor(1) as pool:
            with pytest.raises(ArtifactIdentityConflict, match='lifetime'):
                pool.submit(source.chunks, 1).result()
        pid = os.fork()
        if pid == 0:
            try:
                source.chunks(1)
            except ArtifactIdentityConflict:
                os._exit(0)
            os._exit(1)
        assert os.waitpid(pid, 0)[1] == 0
        chunks = source.chunks(1)
        assert b''.join(chunks) == b'abc'
        with pytest.raises(ArtifactIdentityConflict):
            b''.join(chunks)
        with pytest.raises(ArtifactIdentityConflict):
            source.chunks(1)
        with pytest.raises(ArtifactIdentityConflict):
            source.write(b'd')
    with pytest.raises(ArtifactIdentityConflict):
        source.chunks(1)


def test_adoption_keeps_current_policy_and_actual_registered_array_codec(tmp_path, monkeypatch):
    from empirical_lawhood.api.recursive_operation_index import operation_storage_codecs
    from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_FRAMED_CODEC
    from tests.test_classical_series_workflow import sample_transport

    _, encoded, raw = sample_transport()
    base, = _requests(1)
    request = replace(base, payload=raw, payload_schema=MATRIX_FRAMED_CODEC.payload_schema,
                      profile=MATRIX_FRAMED_CODEC.profile, media_type=MATRIX_FRAMED_CODEC.media_type)
    plane = _plane(tmp_path / 'artifacts')
    plane.validators = ArtifactProfileValidatorRegistry(binary_codecs=operation_storage_codecs())
    with _source(tmp_path / 'arrays', raw) as source:
        result = plane.write_stream(_request(request, source))
    assert result.materialization.physical_sha256 == encoded.array_artifact.sha256
    plane.verify_manifest(plane.read_manifest(request.relative_path))

    original = ExternalArtifactPlane._write_staged_stream
    def tighten(path, selected):
        result = original(path, selected)
        plane.custody_limits = ArtifactCustodyLimits(raw_source_bytes=1)
        return result
    monkeypatch.setattr(ExternalArtifactPlane, '_write_staged_stream', staticmethod(tighten))
    other = replace(request, relative_path='software/publication/other.bin', logical_artifact_id='software.other')
    with _source(tmp_path / 'limited', raw) as source:
        with pytest.raises(ArtifactIdentityConflict):
            plane.write_stream(_request(other, source))
    assert not plane.root.resolve(other.relative_path, for_write=False).exists()


def test_four_concurrent_publishers_preserve_exact_shared_commit(tmp_path):
    request, = _requests(1)
    plane = _plane(tmp_path / 'artifacts')
    barrier = threading.Barrier(4)
    def publish(number):
        with _source(tmp_path / f'scratch-{number}', request.payload) as source:
            stream = _request(request, source)
            barrier.wait(timeout=10)
            return plane.write_stream(stream)
    with ThreadPoolExecutor(4) as pool:
        results = tuple(pool.map(publish, range(4)))
    assert sum(row.created for row in results) == 1
    assert len({row.materialization for row in results}) == 1
    plane.verify_manifest(plane.read_manifest(request.relative_path))
    assert not tuple(tmp_path.rglob('*.partial'))


def test_empty_owned_output_preserves_size_digest_and_replay(tmp_path):
    base, = _requests(1)
    request = replace(base, payload=b'', profile=ArtifactProfile.NATIVE_SUBWORK_PREFIX,
                      payload_schema='empirical-lawhood/runtime/native-subwork-received-prefix', media_type='application/octet-stream')
    plane = _plane(tmp_path / 'artifacts')
    for number in range(2):
        with _source(tmp_path / f'empty-{number}', b'') as source:
            result = plane.write_stream(_request(request, source))
        assert result.materialization.size_bytes == 0
        assert result.materialization.physical_sha256 == hashlib.sha256(b'').hexdigest()
        assert result.created == (number == 0)


@pytest.mark.parametrize('adopt', (False, True))
def test_model_free_event_census_publishes_the_exact_empty_companion(tmp_path, adopt):
    from io import BytesIO
    from empirical_lawhood.api.model_free_matrix import load_definition, specification_for
    from empirical_lawhood.api.recursive_operation_index import operation_storage_codecs
    from empirical_lawhood.domains.matrix.classical_series.arrays import (
        decode_acquisition, encode_acquisition, iter_encoded_bytes,
    )
    from empirical_lawhood.domains.matrix.model_free import design
    from empirical_lawhood.domains.matrix.model_free.bindings import calculate

    definition = Path(__file__).parents[1] / 'programmes/foundations/emergent-structure/workflows/model-free/smoke.json'
    _, label, assignments, settings = load_definition(definition)
    specification = specification_for(label, assignments, settings)
    configs = {config.module: config for config in design.configs_for(specification)
        if config.phase == 'acquire' and config.assignments[0].seed == 1790003}
    preparation = calculate(configs['M1'])
    events = calculate(configs['M7'], (preparation,))
    assert len(events.payload['cases']) == events.payload['assigned_case_count'] > 0
    encoded, leaves = encode_acquisition(events, artifact_id='artifact.small-events', allow_empty=True)
    raw = b''.join(iter_encoded_bytes(encoded, leaves))
    assert raw == b'' and not encoded.array_manifest.members

    base, = _requests(1)
    request = replace(base, payload=raw, payload_schema=encoded.array_artifact.payload_schema,
        profile=ArtifactProfile.RAW_SOURCE_BYTES, media_type=encoded.array_artifact.media_type,
        logical_artifact_id=encoded.array_artifact.artifact_id)
    plane = _plane(tmp_path / 'artifacts')
    plane.validators = ArtifactProfileValidatorRegistry(binary_codecs=operation_storage_codecs())
    for number in range(2):
        with _source(tmp_path / f'empty-events-{number}', raw) as source:
            result = plane.write_stream(_request(request, source, adopt=adopt))
        plane.verify_manifest(plane.read_manifest(request.relative_path))
        assert result.materialization.size_bytes == 0
        assert result.materialization.physical_sha256 == encoded.array_artifact.sha256
        assert result.created == (number == 0)
    final = plane.root.resolve(request.relative_path, for_write=False)
    assert decode_acquisition(encoded, BytesIO(final.read_bytes())) == events.payload
    plane.validators = ArtifactProfileValidatorRegistry(binary_codecs=tuple(
        replace(codec, allow_empty=False) if codec.payload_schema == request.payload_schema else codec
        for codec in operation_storage_codecs()))
    with pytest.raises(ArtifactIdentityConflict):
        plane.verify_manifest(plane.read_manifest(request.relative_path))


@pytest.mark.parametrize('where', ('after-transfer', 'after-intent', 'after-final-move', 'after-commit'))
def test_process_death_retains_exact_bytes_and_original_commit_recovery(tmp_path, monkeypatch, where):
    """Exit without unwinding, then use a new lifetime and the ordinary writer."""
    request, = _requests(1)
    plane = _plane(tmp_path / 'artifacts')
    destination = plane.root.resolve(request.relative_path, for_write=False)
    pid = os.fork()
    if pid == 0:
        with monkeypatch.context() as patch:
            if where == 'after-transfer':
                original = owned_output.rename_noreplace
                def transfer(*args, **kwargs):
                    original(*args, **kwargs)
                    os._exit(73)
                patch.setattr(owned_output, 'rename_noreplace', transfer)
            elif where == 'after-intent':
                original = plane._write_publication_intent
                def intent(*args, **kwargs):
                    original(*args, **kwargs)
                    os._exit(73)
                patch.setattr(plane, '_write_publication_intent', intent)
            else:
                original = ExternalArtifactPlane._rename_noreplace
                def rename(source, target):
                    original(source, target)
                    if ((where == 'after-final-move' and target == destination)
                            or (where == 'after-commit' and target.name.endswith('.commit.json'))):
                        os._exit(73)
                patch.setattr(ExternalArtifactPlane, '_rename_noreplace', staticmethod(rename))
            with _source(tmp_path / 'scratch', request.payload) as source:
                plane.write_stream(_request(request, source))
        os._exit(74)
    assert os.waitpid(pid, 0)[1] == 73 << 8
    assert not (tmp_path / 'scratch').exists()
    exact_payloads = tuple(path for path in (tmp_path / 'artifacts').rglob('*')
                           if path.is_file() and path.read_bytes() == request.payload)
    assert len(exact_payloads) == 1
    commits = tuple((tmp_path / 'artifacts').rglob('*.commit.json'))
    assert bool(commits) == (where == 'after-commit')
    if commits:
        plane.verify_manifest(plane.read_manifest(request.relative_path))
    else:
        with pytest.raises((FileNotFoundError, ArtifactIdentityConflict)):
            plane.verify_manifest(plane.read_manifest(request.relative_path))
    with _source(tmp_path / 'retry', request.payload) as source:
        result = plane.write_stream(_request(request, source))
    assert result.created == (where != 'after-commit')
    assert destination.read_bytes() == request.payload
    plane.verify_manifest(plane.read_manifest(request.relative_path))
    assert not tuple((tmp_path / 'artifacts').rglob('*.intent.json'))


def test_rollback_cannot_delete_another_publishers_completed_commit(tmp_path, monkeypatch):
    request, = _requests(1)
    plane = _plane(tmp_path / 'artifacts')
    original_lock = plane._publication_batch_lock
    original_rename = ExternalArtifactPlane._rename_noreplace
    destination = plane.root.resolve(request.relative_path, for_write=False)
    interrupted = False
    competing = []

    @contextmanager
    def release_then_compete(path):
        try:
            with original_lock(path):
                yield
        finally:
            if interrupted and not competing:
                competing.append(None)
                with _source(tmp_path / 'competitor', request.payload) as source:
                    competing[0] = plane.write_stream(_request(request, source))

    def interrupt_first_move(source, target):
        nonlocal interrupted
        original_rename(source, target)
        if not interrupted and target == destination:
            interrupted = True
            raise KeyboardInterrupt('first publisher lost its caller after placement')

    monkeypatch.setattr(plane, '_publication_batch_lock', release_then_compete)
    monkeypatch.setattr(ExternalArtifactPlane, '_rename_noreplace', staticmethod(interrupt_first_move))
    with _source(tmp_path / 'original', request.payload) as source:
        with pytest.raises(KeyboardInterrupt):
            plane.write_stream(_request(request, source))
    assert competing[0].created
    assert destination.read_bytes() == request.payload
    plane.verify_manifest(plane.read_manifest(request.relative_path))


@pytest.mark.parametrize('where', ('reading', 'validation'))
@pytest.mark.parametrize('damage', ('mutate', 'replace'))
def test_mutation_inside_adopted_read_lifetime_refuses_and_preserves_replacements(tmp_path, monkeypatch, where, damage):
    request, = _requests(1)
    plane = _plane(tmp_path / 'artifacts')
    changed = []
    def damage_path(path):
        if changed:
            return
        changed.append(path)
        if damage == 'replace':
            path.rename(tmp_path / 'original-inode')
        path.write_bytes(b'X' + request.payload[1:])
    if where == 'reading':
        original = OwnedOutputFile._chunks
        def mutate(self, limit):
            for chunk in original(self, limit):
                yield chunk
                damage_path(self._path)
        monkeypatch.setattr(OwnedOutputFile, '_chunks', mutate)
    else:
        original = ArtifactProfileValidatorRegistry.validate_file
        def mutate(self, path, selected, **kwargs):
            original(self, path, selected, **kwargs)
            damage_path(path)
        monkeypatch.setattr(ArtifactProfileValidatorRegistry, 'validate_file', mutate)
    with _source(tmp_path / 'scratch', request.payload) as source:
        with pytest.raises(ArtifactIdentityConflict):
            plane.write_stream(_request(request, source))
    assert changed
    assert not tuple((tmp_path / 'artifacts').rglob('*.commit.json'))
    if damage == 'replace':
        assert changed[0].read_bytes() == b'X' + request.payload[1:]


def test_writer_construction_failure_releases_only_its_own_path_and_descriptor(tmp_path, monkeypatch):
    descriptors = []
    def fail(descriptor, *args, **kwargs):
        descriptors.append(descriptor)
        raise OSError('writer construction refused')
    monkeypatch.setattr(os, 'fdopen', fail)
    with pytest.raises(OSError, match='writer construction'):
        OwnedOutputFile(tmp_path / 'scratch')
    assert not (tmp_path / 'scratch').exists()
    with pytest.raises(OSError):
        os.fstat(descriptors[0])


def test_collector_failure_releases_every_output_even_when_close_raises(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from empirical_lawhood.execution.local.execution import _ScratchOutputCollector

    context = SimpleNamespace(resource_budget=SimpleNamespace(output_bytes=100),
        output_ports=(SimpleNamespace(output_id='a'), SimpleNamespace(output_id='b')))
    collector = _ScratchOutputCollector(context, tmp_path)
    outputs = tuple(collector._files.values())
    descriptors = tuple(output._writer.fileno() for output in outputs)
    close = OwnedOutputFile.close
    closed = []
    def interrupt(self):
        close(self)
        closed.append(self)
        if len(closed) == 1:
            raise KeyboardInterrupt('one output cleanup interrupted')
    monkeypatch.setattr(OwnedOutputFile, 'close', interrupt)
    with pytest.raises(KeyboardInterrupt):
        collector.abort()
    assert len(closed) == 2
    assert not tuple(tmp_path.iterdir())
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)
