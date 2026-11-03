"""Exposed byte-custody controls; no native science or qualification evidence."""

from hashlib import sha256
import os
from pathlib import Path
import shutil

import pytest

from empirical_lawhood.api import recursive_contributions as contributions
from empirical_lawhood.infrastructure import bounded_io
from empirical_lawhood.infrastructure.recursive_custody import iter_exact_custody_file_chunks
from tests.test_battery_recursive_construction import battery_wave_a_draft
from tests.test_recursive_contribution_custody import (
    ROOT,
    _freeze_test_producer,
    _publish_fixture_wave,
    _read_transport,
)
from tests.test_recursive_public_service import _plane


@pytest.mark.parametrize("maximum", (None, 257 * 1024 + 7))
def test_complete_binary_copy_retains_every_byte_and_hash(tmp_path, monkeypatch, maximum):
    raw = bytes(range(256)) * 1028 + b"\x00\xff\x00\n\x80\x01\xfe"
    source, destination = tmp_path / "source.bin", tmp_path / "copy.bin"
    source.write_bytes(raw)
    # Small work chunks exercise an arbitrary number of boundaries; this is
    # not a ceiling on the complete file or on any scientific output.
    monkeypatch.setattr(bounded_io, "CONTROL_PLANE_CHUNK_BYTES", 4096)
    actual = bounded_io.copy_bounded_file(source, destination, maximum_bytes=maximum)
    assert actual == (len(raw), sha256(raw).hexdigest())
    assert destination.read_bytes() == source.read_bytes() == raw


def test_copy_refuses_explicit_identity_bound_and_existing_destination(tmp_path, monkeypatch):
    source, destination = tmp_path / "source", tmp_path / "copy"
    source.write_bytes(b"complete original")
    with pytest.raises(bounded_io.BoundedFileIOError, match="byte limit"):
        bounded_io.copy_bounded_file(source, destination, maximum_bytes=3)
    assert not destination.exists()
    destination.write_bytes(b"keep this prior exact artifact")
    opened = []
    original_open = bounded_io._open_regular

    def capture(*args, **kwargs):
        result = original_open(*args, **kwargs)
        opened.append(result[0])
        return result

    monkeypatch.setattr(bounded_io, "_open_regular", capture)
    with pytest.raises(FileExistsError):
        bounded_io.copy_bounded_file(source, destination, maximum_bytes=None)
    assert destination.read_bytes() == b"keep this prior exact artifact"
    with pytest.raises(OSError):
        os.fstat(opened[0])  # Refusal also closes the source descriptor.


@pytest.mark.parametrize("mutation", ("grow", "truncate", "same-size"))
def test_mutating_source_refuses_and_retains_incomplete_copy(tmp_path, monkeypatch, mutation):
    source, destination = tmp_path / "source", tmp_path / "copy"
    source.write_bytes(b"original data" * 100)
    monkeypatch.setattr(bounded_io, "CONTROL_PLANE_CHUNK_BYTES", 32)
    original_read = bounded_io.os.read
    changed = False

    def change_after_read(descriptor, size):
        nonlocal changed
        raw = original_read(descriptor, size)
        if raw and not changed:
            changed = True
            if mutation == "grow":
                with source.open("ab") as stream:
                    stream.write(b"additional bytes")
            elif mutation == "truncate":
                source.write_bytes(b"short")
            else:
                with source.open("r+b") as stream:
                    stream.write(b"substitution!")
        return raw

    monkeypatch.setattr(bounded_io.os, "read", change_after_read)
    with pytest.raises(bounded_io.BoundedFileIOError):
        bounded_io.copy_bounded_file(source, destination, maximum_bytes=None)
    assert destination.exists()  # Adverse working evidence is preserved.


def test_nonregular_or_link_source_cannot_create_copy(tmp_path):
    source, destination = tmp_path / "fifo", tmp_path / "copy"
    os.mkfifo(source)
    with pytest.raises(bounded_io.BoundedFileIOError, match="regular file"):
        bounded_io.copy_bounded_file(source, destination, maximum_bytes=None)
    source.unlink()
    source.symlink_to(tmp_path / "actual")
    (tmp_path / "actual").write_bytes(b"original")
    with pytest.raises(OSError):
        bounded_io.copy_bounded_file(source, destination, maximum_bytes=None)
    assert not destination.exists()


def test_raw_binary_member_streams_through_real_export_and_relocation(tmp_path, monkeypatch):
    _freeze_test_producer(monkeypatch)
    producer = _plane(tmp_path / "producer")
    wave = Path(producer.root.contract.canonical_path) / "authored"
    _publish_fixture_wave(monkeypatch, producer, wave, battery_wave_a_draft())
    raw_path = wave / "native-working/full-precision-frames.bin"
    raw_path.parent.mkdir()
    raw = bytes(range(256)) * 2049 + b"complete final frame\x00\xff"
    raw_path.write_bytes(raw)
    exported = wave.parent / "exported"
    original_read = contributions.read_bounded_bytes

    def refuse_whole_raw_read(path, **kwargs):
        if path.name == raw_path.name:
            pytest.fail("portable raw custody attempted a whole-file byte allocation")
        return original_read(path, **kwargs)

    monkeypatch.setattr(contributions, "read_bounded_bytes", refuse_whole_raw_read)
    contributions.export_recursive_contribution(directory=wave, output_dir=exported,
        project_root=ROOT, artifact_writer=producer)
    transport = _read_transport(exported)
    relative = raw_path.relative_to(wave.parent).as_posix()
    member = next(row for row in transport.members if row.relative_path == relative)
    assert (member.size_bytes, member.sha256) == (len(raw), sha256(raw).hexdigest())
    consumer = _plane(tmp_path / "consumer")
    imported = Path(consumer.root.contract.canonical_path) / "imported"
    shutil.copytree(exported, imported)
    shutil.rmtree(wave.parent)
    assert contributions.inspect_recursive_contribution(directory=imported,
        artifact_writer=consumer)["status"] == "AUTHENTICATED"
    assert (imported / "custody" / relative).read_bytes() == raw
    # Every raw byte matters independently of the scientific JSON products.
    (imported / "custody" / relative).write_bytes(raw[:-1] + b"\x01")
    with pytest.raises(ValueError):
        contributions.inspect_recursive_contribution(directory=imported, artifact_writer=consumer)


@pytest.mark.parametrize("raw", (b"", b"x", b"exact tiny input", bytes(range(256)) * 1024),
                         ids=("empty", "one-byte", "tiny", "many-chunks"))
def test_exact_source_stream_has_complete_tiny_empty_and_many_chunk_censuses(tmp_path, raw):
    source = tmp_path / "selected-source"
    source.write_bytes(raw)
    observed = tuple(iter_exact_custody_file_chunks(source, size_bytes=len(raw),
        expected_sha256=sha256(raw).hexdigest(), maximum_chunk_bytes=7))
    assert b"".join(observed) == raw
    assert all(len(chunk) <= 7 for chunk in observed)


def test_exact_source_stream_refuses_edit_to_consumed_chunk_with_coarse_timestamps(tmp_path, monkeypatch):
    source = tmp_path / "selected-source"
    raw = b"0123456789" * 100
    source.write_bytes(raw)
    original_identity = bounded_io._identity
    monkeypatch.setattr(bounded_io, "_identity", lambda value: (*original_identity(value)[:3], value.st_nlink))
    iterator = iter_exact_custody_file_chunks(source, size_bytes=len(raw),
        expected_sha256=sha256(raw).hexdigest(), maximum_chunk_bytes=10)
    assert next(iterator) == raw[:10]
    with source.open("r+b") as stream:
        stream.write(b"9876543210")
    with pytest.raises(ValueError, match="changed during its streamed read"):
        tuple(iterator)
