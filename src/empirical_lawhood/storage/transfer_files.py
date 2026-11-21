# SPDX-License-Identifier: MPL-2.0
"""Generic exact-file preparation and verification for inputs, logs and evidence.

Placement and transport are independent. This owner starts no network activity,
infers no completion and grants no scientific qualification. Optional resource
ceilings are operator selections; otherwise the complete observed census sets
finite exact read extents, and all stream buffers remain bounded.
"""
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from empirical_lawhood.execution.progress import progress_step
from empirical_lawhood.science.records.serialization import validate_relative_locator, validate_sha256
from empirical_lawhood.storage.artifact_replication import ReplicaFile, _durable_bytes
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.file_census import FileHashCensus
from empirical_lawhood.storage.transfer_archive import archive_transfer_files

def encode_document(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'

def portable_relative_path(value):
    validate_relative_locator(value)
    # The shared locator contract excludes backslashes/newlines, so GNU
    # sha256sum accepts the complete UTF-8 name (including spaces) literally.
    return value

def normalized_absolute_path(value):
    if (type(value) is not str or not value.startswith('/') or value == '/'
            or str(PurePosixPath(value)) != value or '..' in PurePosixPath(value).parts):
        raise ValueError('deployment paths require explicit normalized absolute locations')
    return value

def ordinary_root(root):
    root = Path(root)
    if (not root.is_absolute() or root.resolve(strict=True) != root or root.is_symlink() or not root.is_dir()):
        raise ValueError('transfer requires an existing ordinary absolute root')
    return root

def census_transfer_files(root, *, maximum_bytes=None, maximum_files=None):
    root = ordinary_root(root)
    if any(v is not None and (type(v) is not int or v <= 0) for v in (maximum_bytes, maximum_files)):
        raise ValueError('transfer requires explicit positive file and byte allowances')
    files, total = [], 0
    paths = sorted(root.rglob('*'))
    with FileHashCensus() as bodies, progress_step('transfer.census', total=len(paths), unit='paths') as progress:
        for path in paths:
            if path.is_symlink() or path.resolve(strict=True) != path:
                raise ValueError('transfer refuses linked or redirected members')
            if path.is_dir():
                progress.advance(1)
                continue
            if not path.is_file():
                raise ValueError('transfer refuses nonregular members')
            if maximum_files is not None and len(files) >= maximum_files:
                raise ValueError('transfer exceeds its selected file allowance')
            name = portable_relative_path(path.relative_to(root).as_posix())
            size, digest = bodies.sha256(path, maximum_bytes=None if maximum_bytes is None else maximum_bytes-total)
            total += size
            files.append(ReplicaFile(name, size, digest))
            progress.advance(1)
    if not files:
        raise ValueError('transfer requires a nonempty explicitly selected payload')
    return tuple(files)

def seal_transfer(root, manifest_path, *, maximum_bytes=None, maximum_files=None):
    """Hash a selected closed export; primary receipts and scientific status stay unchanged."""
    root = ordinary_root(root)
    manifest_path = Path(manifest_path)
    if (not manifest_path.is_absolute() or manifest_path.resolve(strict=False) != manifest_path
            or manifest_path.is_relative_to(root) or not manifest_path.parent.is_dir()):
        raise ValueError('transfer manifest must have a fresh explicit path outside its payload')
    members = census_transfer_files(root, maximum_bytes=maximum_bytes, maximum_files=maximum_files)
    document = {'schema': 'empirical-lawhood/operational/transfer-files', 'version': '1.0.0',
        'maximum_bytes': max(1, sum(row.size_bytes for row in members)) if maximum_bytes is None else maximum_bytes,
        'maximum_files': len(members) if maximum_files is None else maximum_files,
        'files': [row.to_mapping() for row in members], 'scientific_qualification': 'NOT_ESTABLISHED',
        'native_completion': 'NOT_INFERRED', 'primary_receipts': 'UNCHANGED'}
    if census_transfer_files(root, maximum_bytes=maximum_bytes, maximum_files=maximum_files) != members:
        raise ValueError('complete transfer payload changed during its census')
    raw = encode_document(document)
    _durable_bytes(manifest_path, raw)
    return {'manifest': str(manifest_path), 'sha256': sha256(raw).hexdigest(),
        'files': len(members), 'bytes': sum(row.size_bytes for row in members)}

def read_transfer_manifest(manifest_path, *, expected_sha256):
    validate_sha256(expected_sha256, field_name='authenticated transfer manifest digest')
    raw = read_bounded_bytes(Path(manifest_path), maximum_bytes=None)
    if sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('transfer manifest differs from its independently authenticated digest')
    document = json.loads(raw)
    if (type(document) is not dict or set(document) != {'schema', 'version', 'maximum_bytes',
            'maximum_files', 'files', 'scientific_qualification', 'native_completion', 'primary_receipts'}
            or document['schema'] != 'empirical-lawhood/operational/transfer-files'
            or document['version'] != '1.0.0' or encode_document(document) != raw
            or document['scientific_qualification'] != 'NOT_ESTABLISHED'
            or document['native_completion'] != 'NOT_INFERRED' or document['primary_receipts'] != 'UNCHANGED'):
        raise ValueError('transfer manifest changes its operational evidence contract')
    expected = tuple(ReplicaFile(**row) for row in document['files'])
    if not expected or len({row.relative_path for row in expected}) != len(expected):
        raise ValueError('transfer manifest requires a complete unique nonempty file census')
    if (any(type(document[name]) is not int or document[name] <= 0 for name in ('maximum_bytes', 'maximum_files'))
            or len(expected) > document['maximum_files']
            or sum(row.size_bytes for row in expected) > document['maximum_bytes']):
        raise ValueError('transfer manifest exceeds its declared bounds')
    return document, expected

def verify_transfer(root, manifest_path, *, expected_sha256):
    """Verify the complete transfer against an independently retained digest."""
    document, expected = read_transfer_manifest(manifest_path, expected_sha256=expected_sha256)
    for _ in range(2):
        if census_transfer_files(root, maximum_bytes=document['maximum_bytes'], maximum_files=document['maximum_files']) != expected:
            raise ValueError('transfer changes the complete original file census or bytes')
    return {'status': 'BYTE_VERIFIED', 'manifest_sha256': expected_sha256, 'files': len(expected),
        'bytes': sum(row.size_bytes for row in expected), 'native_completion': 'NOT_INFERRED'}

def prepare_transfer(root, output_directory, *, maximum_bytes=None, maximum_files=None):
    """Prepare one immutable exact-file transfer package with two source passes.

    The independently parsed carrier verifies every byte against the opening
    census. A complete closing census catches additions, removals and changes.
    Manifest publication follows these checks. The same package serves remote
    inputs and the return of evidence/logs for any scientific substrate.
    """
    root = ordinary_root(root)
    output = Path(output_directory)
    if (not output.is_absolute() or output.resolve(strict=False) != output
            or output.is_relative_to(root) or root.is_relative_to(output)
            or not output.parent.is_dir() or output.exists() and any(output.iterdir())):
        raise ValueError('transfer preparation requires a fresh separate absolute output directory')
    output.mkdir(exist_ok=True)
    members = census_transfer_files(root, maximum_bytes=maximum_bytes, maximum_files=maximum_files)
    observed_bytes = sum(row.size_bytes for row in members)
    # Tar record alignment, extended names/metadata and final record padding;
    # this is a format-derived allocation, not a workload-size ceiling.
    archive_bound = 10240 + sum(((row.size_bytes + 511)//512)*512 +
        ((len(row.relative_path.encode('utf-8')) + 511)//512 + 6)*512 for row in members)
    archive = output / 'payload.tar'
    archive_bytes, archive_sha256 = archive_transfer_files(root, archive, members,
        maximum_archive_bytes=archive_bound)
    if census_transfer_files(root, maximum_bytes=maximum_bytes, maximum_files=maximum_files) != members:
        raise ValueError('complete transfer payload changed during archive preparation')
    document = {'schema': 'empirical-lawhood/operational/transfer-files', 'version': '1.0.0',
        'maximum_bytes': max(1, observed_bytes) if maximum_bytes is None else maximum_bytes,
        'maximum_files': len(members) if maximum_files is None else maximum_files,
        'files': [row.to_mapping() for row in members], 'scientific_qualification': 'NOT_ESTABLISHED',
        'native_completion': 'NOT_INFERRED', 'primary_receipts': 'UNCHANGED'}
    raw = encode_document(document)
    manifest_path = output / 'payload-manifest.json'
    _durable_bytes(manifest_path, raw)
    _durable_bytes(output / 'SHA256SUMS', ''.join(f'{row.sha256}  ./{row.relative_path}\n' for row in members).encode())
    return {'manifest': str(manifest_path), 'sha256': sha256(raw).hexdigest(),
        'files': len(members), 'bytes': observed_bytes, 'archive': str(archive),
        'archive_bytes': archive_bytes, 'archive_sha256': archive_sha256}
