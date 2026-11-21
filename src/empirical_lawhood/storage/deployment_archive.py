# SPDX-License-Identifier: MPL-2.0
"""Closed original-tree transport, retaining links without following or extracting them.

This is a transport carrier for the existing receipts, not a replacement store
or a domain completion reader. The caller establishes that native writers closed.
"""

from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile
from decimal import Decimal
from fractions import Fraction

from empirical_lawhood.storage.transfer_files import census_transfer_files as _census, encode_document as _encode, ordinary_root as _ordinary_root, read_transfer_manifest as _read_transfer_manifest
from empirical_lawhood.storage.artifact_replication import _durable_bytes
from empirical_lawhood.storage.bounded_io import _open_regular, _stable_descriptor, read_bounded_bytes
from empirical_lawhood.storage.file_census import FileHashCensus
from empirical_lawhood.storage.transfer_archive import _BoundedArchiveWriter, _BoundedHashReader


def _name(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or str(path) != name or '..' in path.parts
            or name == '.' or '\x00' in name or len(name.encode()) > 4096):
        raise ValueError('original archive requires bounded relative member names')
    return name


def _tree_census(root, *, maximum_bytes, maximum_entries):
    root = _ordinary_root(root)
    if any(type(v) is not int or v <= 0 for v in (maximum_bytes, maximum_entries)):
        raise ValueError('original archive requires explicit positive bounds')
    rows, identities, total = [], {}, 0
    with FileHashCensus() as bodies:
        for path in sorted(root.rglob('*')):
            if len(rows) >= maximum_entries:
                raise ValueError('original tree exceeds the selected entry allowance')
            before = path.lstat()
            name = _name(path.relative_to(root).as_posix())
            row = {'path': name, 'mode': stat.S_IMODE(before.st_mode), 'mtime_ns': before.st_mtime_ns,
                'uid': before.st_uid, 'gid': before.st_gid}
            if stat.S_ISDIR(before.st_mode):
                row['kind'] = 'directory'
            elif stat.S_ISLNK(before.st_mode):
                target = os.readlink(path)
                if len(target.encode()) > 4096:
                    raise ValueError('original symlink target exceeds its bound')
                row.update(kind='symlink', target=target)
            elif stat.S_ISREG(before.st_mode):
                size, digest = bodies.sha256(path, maximum_bytes=maximum_bytes-total)
                total += size
                row.update(kind='regular', bytes=size, sha256=digest)
                if before.st_ino != 0 and before.st_nlink > 1:
                    key = (before.st_dev, before.st_ino)
                    if key in identities:
                        row['hardlink_to'] = identities[key]
                    else:
                        identities[key] = name
            else:
                raise ValueError('original tree contains an unsupported special file')
            after = path.lstat()
            fields = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
            if any(getattr(before, field) != getattr(after, field) for field in fields):
                raise ValueError('original member changed during its census')
            rows.append(row)
    if not rows:
        raise ValueError('original tree is empty')
    return rows


def archive_original_tree(root, *, output_directory, maximum_bytes, maximum_entries):
    """Retain all selected original types and bytes in a fresh bounded carrier."""
    root = _ordinary_root(root)
    output = Path(output_directory)
    if (not output.is_absolute() or output.resolve(strict=False) != output or output.exists()
            or not output.parent.is_dir() or output.is_relative_to(root) or root.is_relative_to(output)):
        raise ValueError('select a fresh ordinary archive destination separate from the originals')
    rows = _tree_census(root, maximum_bytes=maximum_bytes, maximum_entries=maximum_entries)
    # Reserve extended path/time headers as well as ordinary tar padding.
    archive_limit = maximum_bytes+maximum_entries*16384+10240
    output.mkdir()
    archive = output/'original-output.tar'
    with archive.open('xb') as stream, tarfile.open(
            fileobj=_BoundedArchiveWriter(stream, archive_limit), mode='w', dereference=False) as packed:
        for row in rows:
            def exact_time(info):
                whole, part = divmod(row['mtime_ns'], 10**9)
                info.pax_headers['mtime'] = f'{whole}.{part:09d}'
                return info
            packed.add(root/row['path'], arcname=row['path'], recursive=False, filter=exact_time)
    record = {'schema': 'empirical-lawhood/operational/original-tree-archive', 'version': '1.0.0',
        'original_root': str(root), 'maximum_bytes': maximum_bytes, 'maximum_entries': maximum_entries,
        'entries': rows,
        'linked_targets_followed': False, 'native_completion': 'NOT_INFERRED'}
    # Before accepting the producer, read the archive through its independent
    # member comparison and hash the same consumed carrier. The source-tree
    # closing check follows it; an intermediate full source census adds no
    # independent comparison to this complete publication boundary.
    size, digest = _verify_members(archive, record)
    record.update(archive_bytes=size, archive_sha256=digest)
    if _tree_census(root, maximum_bytes=maximum_bytes, maximum_entries=maximum_entries) != rows:
        raise ValueError('original tree changed before archive publication')
    raw = _encode(record)
    _durable_bytes(output/'original-tree-census.json', raw)
    return {'status': 'ORIGINAL_TREE_ARCHIVED', 'package': str(output), 'entries': len(rows),
        'archive_bytes': size, 'native_completion': 'NOT_INFERRED', 'linked_targets_followed': False}


def _verify_members(archive_path, census):
    if any(type(census[name]) is not int or census[name] <= 0
            for name in ('maximum_entries', 'maximum_bytes')):
        raise ValueError('original archive requires explicit positive bounds')
    rows = census['entries']
    if type(rows) is not list or not 0 < len(rows) <= census['maximum_entries']:
        raise ValueError('original archive changes its bounded entry census')
    expected = {_name(row['path']): row for row in rows}
    if len(expected) != len(rows):
        raise ValueError('original archive repeats a member')
    if sum(row.get('bytes', 0) for row in rows) > census['maximum_bytes']:
        raise ValueError('original archive exceeds its logical byte allowance')
    archive_limit = census['maximum_bytes'] + census['maximum_entries'] * 16384 + 10240
    descriptor, before = _open_regular(Path(archive_path), maximum_bytes=archive_limit)
    with _stable_descriptor(descriptor, before, operation='original archive verification'):
        carrier = _BoundedHashReader(descriptor, archive_limit)
        seen, payload_end = set(), 0
        with tarfile.open(fileobj=carrier, mode='r|', bufsize=2**20) as archive:
            for member in archive:
                if member.name not in expected or member.name in seen:
                    raise ValueError('original archive changes the complete member census')
                row = expected[member.name]
                if (member.mode, member.uid, member.gid) != (row['mode'], row['uid'], row['gid']):
                    raise ValueError('original archive changes member metadata')
                # PAX owns exact subsecond time serialization in this carrier.
                if Fraction(Decimal(str(member.pax_headers.get('mtime', member.mtime))))*10**9 != row['mtime_ns']:
                    raise ValueError('original archive changes member timestamp')
                if row['kind'] == 'directory':
                    if not member.isdir() or member.size != 0:
                        raise ValueError('original archive changes a directory')
                elif row['kind'] == 'symlink':
                    if not member.issym() or member.size != 0 or member.linkname != row['target']:
                        raise ValueError('original archive changes a symlink without following it')
                elif row['kind'] == 'regular':
                    if 'hardlink_to' in row:
                        # A hardlink has no payload. Its earlier ordinary target
                        # was already independently hashed in this same stream.
                        if (not member.islnk() or member.size != 0
                                or member.linkname != row['hardlink_to'] or member.linkname not in seen
                                or expected[member.linkname]['kind'] != 'regular'
                                or expected[member.linkname].get('hardlink_to') is not None
                                or (expected[member.linkname]['bytes'], expected[member.linkname]['sha256'])
                                != (row['bytes'], row['sha256'])):
                            raise ValueError('original archive changes a hardlink relationship')
                    else:
                        if not member.isfile() or member.size != row['bytes']:
                            raise ValueError('original archive changes a regular member')
                        digest, count = sha256(), 0
                        with archive.extractfile(member) as content:
                            for chunk in iter(lambda: content.read(2**20), b''):
                                count += len(chunk)
                                if count > row['bytes']:
                                    raise ValueError('original archive member exceeds its declared bytes')
                                digest.update(chunk)
                        if count != row['bytes'] or digest.hexdigest() != row['sha256']:
                            raise ValueError('original archive changes original member bytes')
                else:
                    raise ValueError('original archive declares an unsupported member type')
                seen.add(member.name)
                payload_end = member.offset_data + ((member.size + 511) // 512) * 512
        if seen != set(expected):
            raise ValueError('original archive omits a member')
        while carrier.read(2**20):
            pass
        if carrier.size != before.st_size:
            raise ValueError('original archive changed during its complete read')
        if carrier.last_nonzero_offset >= payload_end:
            raise ValueError('original archive contains unselected bytes after its members')
        return carrier.size, carrier.digest.hexdigest()


def verify_original_archive(package, manifest_path, *, expected_sha256):
    """Authenticate transport and compare every original member without extraction."""
    package = _ordinary_root(package)
    document, expected = _read_transfer_manifest(manifest_path, expected_sha256=expected_sha256)
    # This composition owns one opening and one closing complete census. Do
    # not nest the standalone two-pass verifier on both sides of member reads.
    if _census(package, maximum_bytes=document['maximum_bytes'], maximum_files=document['maximum_files']) != expected:
        raise ValueError('transfer changes the complete original file census or bytes')
    selected = {row.relative_path: row for row in expected}
    if not {'original-tree-census.json', 'original-output.tar'} <= set(selected):
        raise ValueError('original archive omits its retained carrier or census')
    raw = read_bounded_bytes(package/'original-tree-census.json', maximum_bytes=selected['original-tree-census.json'].size_bytes)
    if (len(raw), sha256(raw).hexdigest()) != (
            selected['original-tree-census.json'].size_bytes, selected['original-tree-census.json'].sha256):
        raise ValueError('original archive census differs from its authenticated transfer')
    census = json.loads(raw)
    if (set(census) != {'schema', 'version', 'original_root', 'maximum_bytes', 'maximum_entries',
            'archive_bytes', 'archive_sha256', 'entries', 'linked_targets_followed', 'native_completion'}
            or census['schema'] != 'empirical-lawhood/operational/original-tree-archive'
            or census['version'] != '1.0.0' or census['linked_targets_followed'] is not False
            or census['native_completion'] != 'NOT_INFERRED'):
        raise ValueError('original archive changes its transport-only evidence contract')
    actual = _verify_members(package/'original-output.tar', census)
    if (actual != (census['archive_bytes'], census['archive_sha256'])
            or actual != (selected['original-output.tar'].size_bytes, selected['original-output.tar'].sha256)):
        raise ValueError('original archive differs from its retained census')
    if _census(package, maximum_bytes=document['maximum_bytes'], maximum_files=document['maximum_files']) != expected:
        raise ValueError('transfer changes the complete original file census or bytes')
    _read_transfer_manifest(manifest_path, expected_sha256=expected_sha256)
    verification = {'status': 'BYTE_VERIFIED', 'manifest_sha256': expected_sha256, 'files': len(expected),
        'bytes': sum(row.size_bytes for row in expected), 'native_completion': 'NOT_INFERRED'}
    return {'status': 'COMPLETE_ORIGINAL_ARCHIVE_MEMBER_RETURN_VERIFIED', 'entries': len(census['entries']),
        'transfer': verification, 'files_extracted': 0, 'native_completion': 'USE_ORIGINAL_DOMAIN_READER'}
