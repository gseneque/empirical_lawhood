# SPDX-License-Identifier: MPL-2.0
"""Bounded archive custody for a sealed population of ordinary transfer files.

Hash the complete carrier while independently reading its members. A closing
source-tree check alone cannot prove which bytes the archive actually contains.
This owner starts no transport and interprets no scientific result.
"""

from hashlib import sha256
from empirical_lawhood.execution.progress import report_progress
import os
from pathlib import Path
import tarfile

from empirical_lawhood.storage.artifact_replication import ReplicaFile
from empirical_lawhood.storage.bounded_io import BoundedFileIOError, _open_regular, _stable_descriptor


class _BoundedArchiveWriter:
    """Enforce the carrier allowance while writing, before disk consumption."""

    def __init__(self, stream, maximum_bytes):
        self.stream = stream
        self.maximum_bytes = maximum_bytes

    def tell(self):
        return self.stream.tell()

    def write(self, data):
        if self.tell() + len(data) > self.maximum_bytes:
            raise BoundedFileIOError('transfer archive exceeds its carrier byte limit')
        return self.stream.write(data)


class _BoundedHashReader:
    """Hash exactly the bytes consumed from one stable, bounded descriptor."""

    def __init__(self, descriptor, maximum_bytes):
        self.descriptor = descriptor
        self.maximum_bytes = maximum_bytes
        self.size = 0
        self.digest = sha256()
        self.last_nonzero_offset = -1

    def read(self, size):
        data = os.read(self.descriptor, min(size, self.maximum_bytes - self.size + 1))
        self.size += len(data)
        if self.size > self.maximum_bytes:
            raise ValueError('transfer archive exceeds its carrier byte allowance')
        self.digest.update(data)
        nonzero_length = len(data.rstrip(b'\x00'))
        if nonzero_length:
            self.last_nonzero_offset = self.size - len(data) + nonzero_length - 1
        return data


def archive_transfer_files(root, destination, members, *, maximum_archive_bytes):
    """Write and verify a complete sealed census; retain refused partial output.

The carrier digest and independent member comparison share one streaming read.
Memory remains bounded by the tar block and one 1-MiB content block. The caller
retains ownership of the source-tree closing check before publication.
"""
    root, destination = Path(root), Path(destination)
    if (type(members) is not tuple or not members
            or any(type(row) is not ReplicaFile for row in members)
            or len({row.relative_path for row in members}) != len(members)):
        raise ValueError('transfer archive requires a complete unique typed census')
    if type(maximum_archive_bytes) is not int or maximum_archive_bytes < 1:
        raise ValueError('transfer archive requires a positive carrier byte allowance')
    total_bytes = sum(row.size_bytes for row in members)
    completed_bytes = 0
    report_progress(phase='transfer.archive.write', done=0, total=total_bytes, unit='bytes')
    with destination.open('xb') as stream, tarfile.open(
            fileobj=_BoundedArchiveWriter(stream, maximum_archive_bytes), mode='w', dereference=True) as packed:
        for row in members:
            packed.add(root / row.relative_path, arcname=row.relative_path, recursive=False)
            completed_bytes += row.size_bytes
            report_progress(phase='transfer.archive.write', done=completed_bytes, total=total_bytes, unit='bytes')
    expected = {row.relative_path: row for row in members}
    descriptor, before = _open_regular(destination, maximum_bytes=maximum_archive_bytes)
    with _stable_descriptor(descriptor, before, operation='archive verification'):
        stream = _BoundedHashReader(descriptor, maximum_archive_bytes)
        report_progress(phase='transfer.archive.verify', done=0, total=before.st_size, unit='bytes')
        seen = set()
        payload_end = 0
        with tarfile.open(fileobj=stream, mode='r|', bufsize=2**20) as packed:
            for member in packed:
                if member.name not in expected or member.name in seen:
                    raise ValueError('transfer archive changes its complete member census')
                row = expected[member.name]
                if not member.isfile() or member.size != row.size_bytes:
                    raise ValueError('transfer archive changes a regular member or its size')
                seen.add(member.name)
                payload_end = member.offset_data + ((member.size + 511) // 512) * 512
                digest, size = sha256(), 0
                with packed.extractfile(member) as content:
                    for chunk in iter(lambda: content.read(2**20), b''):
                        size += len(chunk)
                        if size > row.size_bytes:
                            raise ValueError('transfer archive member exceeds its selected size')
                        digest.update(chunk)
                        report_progress(phase='transfer.archive.verify', done=stream.size, total=before.st_size, unit='bytes')
                if size != row.size_bytes or digest.hexdigest() != row.sha256:
                    raise ValueError('transfer archive changes original member bytes')
        if seen != set(expected):
            raise ValueError('transfer archive omits a sealed member')
        # tar ends before its carrier padding. Authenticate every retained byte,
        # including that padding, without reopening or rereading the archive.
        while stream.read(2**20):
            pass
        if stream.size != before.st_size:
            raise ValueError('transfer archive changed during its complete read')
        if stream.last_nonzero_offset >= payload_end:
            raise ValueError('transfer archive contains unselected bytes after its sealed members')
        report_progress(phase='transfer.archive.verify', done=stream.size, total=before.st_size, unit='bytes')
        result = stream.size, stream.digest.hexdigest()
    return result
