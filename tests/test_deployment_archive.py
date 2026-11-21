# SPDX-License-Identifier: MPL-2.0
"""Original-tree transport controls with no scientific completion claims."""

import json
import os
import tarfile
import io
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from empirical_lawhood.storage.transfer_files import seal_transfer
from empirical_lawhood.storage.deployment_archive import archive_original_tree, verify_original_archive
from empirical_lawhood.storage import deployment_archive, file_census


def original_tree(tmp_path):
    root = tmp_path/'original'
    root.mkdir()
    (root/'empty').mkdir()
    (root/'receipt.json').write_bytes(b'EXPOSED ORIGINAL; NO SCIENTIFIC AUTHORITY\n')
    (root/'same-bytes.json').hardlink_to(root/'receipt.json')
    (root/'link-to-outside').symlink_to('/not-present/do-not-read')
    os.utime(root/'receipt.json', ns=(1790000000123456789, 1790000000123456789))
    return root


def test_link_relationships_all_original_bytes_and_empty_directories_survive_without_extraction(tmp_path):
    root = original_tree(tmp_path)
    package = tmp_path/'archive'
    made = archive_original_tree(root, output_directory=package, maximum_bytes=1000, maximum_entries=20)
    manifest = tmp_path/'manifest.json'
    sealed = seal_transfer(package, manifest, maximum_bytes=100000, maximum_files=2)
    result = verify_original_archive(package, manifest, expected_sha256=sealed['sha256'])
    assert result['status'] == 'COMPLETE_ORIGINAL_ARCHIVE_MEMBER_RETURN_VERIFIED'
    assert result['entries'] == made['entries'] == 4 and result['files_extracted'] == 0
    assert result['native_completion'] == 'USE_ORIGINAL_DOMAIN_READER'
    census = json.loads((package/'original-tree-census.json').read_bytes())
    assert any(row.get('hardlink_to') == 'receipt.json' for row in census['entries'])
    assert any(row.get('target') == '/not-present/do-not-read' for row in census['entries'])
    assert (root/'receipt.json').stat().st_ino == (root/'same-bytes.json').stat().st_ino
    assert not (package/'empty').exists()


@pytest.mark.parametrize('damage', ['byte-bound', 'entry-bound', 'special', 'nested', 'root-link'])
def test_archive_refuses_unbounded_or_redirected_originals(tmp_path, damage):
    root = original_tree(tmp_path)
    out = tmp_path/'archive'
    maximum_bytes, maximum_entries = 1000, 20
    if damage == 'byte-bound': maximum_bytes = 1
    if damage == 'entry-bound': maximum_entries = 1
    if damage == 'special': os.mkfifo(root/'fifo')
    if damage == 'nested': out = root/'archive'
    if damage == 'root-link':
        alias = tmp_path/'alias'
        alias.symlink_to(root, target_is_directory=True)
        root = alias
    with pytest.raises((ValueError, RuntimeError, OSError)):
        archive_original_tree(root, output_directory=out, maximum_bytes=maximum_bytes, maximum_entries=maximum_entries)
    assert not out.exists()


@pytest.mark.parametrize('damage', ['tar', 'census', 'extra', 'manifest'])
def test_return_refuses_tampering_before_member_read(tmp_path, damage):
    root = original_tree(tmp_path)
    package = tmp_path/'archive'
    archive_original_tree(root, output_directory=package, maximum_bytes=1000, maximum_entries=20)
    manifest = tmp_path/'manifest.json'
    sealed = seal_transfer(package, manifest, maximum_bytes=100000, maximum_files=2)
    if damage == 'tar':
        with (package/'original-output.tar').open('r+b') as stream:
            stream.write(b'changed')
    if damage == 'census': (package/'original-tree-census.json').write_text('{}')
    if damage == 'extra': (package/'extra').write_bytes(b'extra')
    if damage == 'manifest': manifest.write_bytes(manifest.read_bytes()+b' ')
    with pytest.raises(ValueError):
        verify_original_archive(package, manifest, expected_sha256=sealed['sha256'])


def test_source_change_during_archive_is_retained_as_failed_attempt(tmp_path, monkeypatch):
    root = original_tree(tmp_path)
    original = tarfile.TarFile.add
    def changed(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        (root/'receipt.json').write_bytes(b'CHANGED DURING PUBLICATION')
        return result
    monkeypatch.setattr(tarfile.TarFile, 'add', changed)
    package = tmp_path/'archive'
    with pytest.raises(ValueError):
        archive_original_tree(root, output_directory=package, maximum_bytes=1000, maximum_entries=20)
    assert (package/'original-output.tar').exists()
    assert not (package/'original-tree-census.json').exists()


def test_hardlinks_share_only_body_reads_and_each_census_reopens_every_path(tmp_path, monkeypatch):
    root = original_tree(tmp_path)
    opened, hashed = [], []
    original_open = file_census._open_regular
    original_hash = file_census._hash_regular_descriptor
    def observed_open(path, **bounds):
        opened.append(path.name)
        return original_open(path, **bounds)
    def observed_hash(descriptor, before, **bounds):
        hashed.append(before.st_size)
        return original_hash(descriptor, before, **bounds)
    monkeypatch.setattr(file_census, '_open_regular', observed_open)
    monkeypatch.setattr(file_census, '_hash_regular_descriptor', observed_hash)
    initial = deployment_archive._tree_census(root, maximum_bytes=1000, maximum_entries=20)
    closing = deployment_archive._tree_census(root, maximum_bytes=1000, maximum_entries=20)
    assert initial == closing
    assert opened == ['receipt.json', 'same-bytes.json'] * 2
    assert hashed == [(root/'receipt.json').stat().st_size] * 2
    # Two names still consume two logical-file allowances despite one body.
    with pytest.raises(RuntimeError, match='byte limit'):
        deployment_archive._tree_census(root, maximum_bytes=hashed[0], maximum_entries=20)


def test_body_reuse_preserves_alias_access_current_identity_and_owner(tmp_path, monkeypatch):
    path = tmp_path/'first'
    alias = tmp_path/'second'
    path.write_bytes(b'original')
    alias.hardlink_to(path)
    original_open = file_census._open_regular
    with file_census.FileHashCensus() as bodies:
        initial = bodies.sha256(path, maximum_bytes=20)
        def revoked(selected, **bounds):
            if selected == alias:
                raise PermissionError('current alias access was revoked')
            return original_open(selected, **bounds)
        monkeypatch.setattr(file_census, '_open_regular', revoked)
        with pytest.raises(PermissionError, match='revoked'):
            bodies.sha256(alias, maximum_bytes=20)
        monkeypatch.setattr(file_census, '_open_regular', original_open)
        alias.unlink()
        alias.write_bytes(b'changed!')
        assert bodies.sha256(alias, maximum_bytes=20) != initial
        with ThreadPoolExecutor(max_workers=1) as pool:
            with pytest.raises(RuntimeError, match='original owner'):
                pool.submit(bodies.sha256, path, maximum_bytes=20).result()
    with pytest.raises(RuntimeError, match='active original owner'):
        bodies.sha256(path, maximum_bytes=20)


def test_changed_hardlink_body_is_not_reused_by_closing_census(tmp_path):
    root = original_tree(tmp_path)
    selected = deployment_archive._tree_census(root, maximum_bytes=1000, maximum_entries=20)
    path = root/'receipt.json'
    before = path.stat()
    path.write_bytes(b'X' * before.st_size)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    returned = deployment_archive._tree_census(root, maximum_bytes=1000, maximum_entries=20)
    assert returned != selected
    assert {row['sha256'] for row in returned if row['kind'] == 'regular'} == {sha256(path.read_bytes()).hexdigest()}


def test_unavailable_inode_identity_never_merges_distinct_bodies_or_links(tmp_path, monkeypatch):
    root = tmp_path/'original'
    root.mkdir()
    (root/'a.body').write_bytes(b'first123')
    (root/'a.link').hardlink_to(root/'a.body')
    (root/'b.body').write_bytes(b'second45')
    (root/'b.link').hardlink_to(root/'b.body')
    original_fstat, original_lstat = os.fstat, type(root).lstat
    def unavailable_inode(observed):
        fields = {name: getattr(observed, name) for name in dir(observed) if name.startswith('st_')}
        fields.update(st_ino=0, st_mtime_ns=0, st_ctime_ns=0)
        return SimpleNamespace(**fields)
    monkeypatch.setattr(os, 'fstat', lambda descriptor: unavailable_inode(original_fstat(descriptor)))
    monkeypatch.setattr(type(root), 'lstat', lambda path: unavailable_inode(original_lstat(path)))
    rows = deployment_archive._tree_census(root, maximum_bytes=1000, maximum_entries=20)
    assert len(rows) == 4
    assert all('hardlink_to' not in row for row in rows)
    assert {row['path']: row['sha256'] for row in rows} == {
        path.name: sha256(path.read_bytes()).hexdigest() for path in root.iterdir()}


def test_independent_archive_reader_checks_target_once_and_never_extracts_a_link(tmp_path, monkeypatch):
    root = original_tree(tmp_path)
    original = tarfile.TarFile.extractfile
    observed = []
    def extracted(self, member):
        assert member.isfile() and not member.islnk()
        observed.append(member.name)
        return original(self, member)
    monkeypatch.setattr(tarfile.TarFile, 'extractfile', extracted)
    package = tmp_path/'archive'
    archive_original_tree(root, output_directory=package, maximum_bytes=1000, maximum_entries=20)
    assert observed == ['receipt.json']


def test_final_source_census_catches_mutation_during_independent_archive_read(tmp_path, monkeypatch):
    root = original_tree(tmp_path)
    original = deployment_archive._verify_members
    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        path = root/'receipt.json'
        before = path.stat()
        path.write_bytes(b'X' * before.st_size)
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        return result
    monkeypatch.setattr(deployment_archive, '_verify_members', changed)
    package = tmp_path/'archive'
    with pytest.raises(ValueError, match='before archive publication'):
        archive_original_tree(root, output_directory=package, maximum_bytes=1000, maximum_entries=20)
    assert not (package/'original-tree-census.json').exists()


def test_archive_member_check_refuses_changed_writer_bytes_with_unchanged_sources(tmp_path, monkeypatch):
    root = original_tree(tmp_path)
    original = tarfile.TarFile.addfile
    unchanged = (root/'receipt.json').read_bytes()
    def corrupt(self, member, fileobj=None):
        if member.name == 'receipt.json' and member.isfile():
            fileobj = io.BytesIO(b'X' * member.size)
        return original(self, member, fileobj)
    monkeypatch.setattr(tarfile.TarFile, 'addfile', corrupt)
    package = tmp_path/'archive'
    with pytest.raises(ValueError, match='original member bytes'):
        archive_original_tree(root, output_directory=package, maximum_bytes=1000, maximum_entries=20)
    assert (root/'receipt.json').read_bytes() == unchanged
    assert not (package/'original-tree-census.json').exists()


@pytest.mark.parametrize('damage', ['payload', 'target', 'self'])
def test_archive_hardlink_requires_exact_earlier_target_and_no_payload(tmp_path, monkeypatch, damage):
    root = original_tree(tmp_path)
    original = tarfile.TarFile.addfile
    def corrupt(self, member, fileobj=None):
        if member.islnk():
            if damage == 'payload':
                member.size = 1
                fileobj = io.BytesIO(b'X')
            else:
                member.linkname = member.name if damage == 'self' else 'empty'
        return original(self, member, fileobj)
    monkeypatch.setattr(tarfile.TarFile, 'addfile', corrupt)
    package = tmp_path/'archive'
    with pytest.raises(ValueError, match='hardlink relationship'):
        archive_original_tree(root, output_directory=package, maximum_bytes=1000, maximum_entries=20)
    assert not (package/'original-tree-census.json').exists()


def test_return_closing_census_catches_mutation_after_member_read(tmp_path, monkeypatch):
    root = original_tree(tmp_path)
    package = tmp_path/'archive'
    archive_original_tree(root, output_directory=package, maximum_bytes=1000, maximum_entries=20)
    manifest = tmp_path/'manifest.json'
    sealed = seal_transfer(package, manifest, maximum_bytes=100000, maximum_files=2)
    original = deployment_archive._verify_members
    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        path = package/'original-output.tar'
        before = path.stat()
        with path.open('r+b') as stream:
            stream.write(b'X')
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        return result
    monkeypatch.setattr(deployment_archive, '_verify_members', changed)
    with pytest.raises(ValueError, match='complete original file census or bytes'):
        verify_original_archive(package, manifest, expected_sha256=sealed['sha256'])


def test_original_archive_rejects_unselected_carrier_tail_even_if_resealed(tmp_path):
    root = original_tree(tmp_path)
    package = tmp_path/'archive'
    archive_original_tree(root, output_directory=package, maximum_bytes=1000, maximum_entries=20)
    path = package/'original-output.tar'
    with path.open('ab') as stream:
        stream.write(b'UNSELECTED NONZERO TAIL')
    census_path = package/'original-tree-census.json'
    census = json.loads(census_path.read_bytes())
    census.update(archive_bytes=path.stat().st_size, archive_sha256=sha256(path.read_bytes()).hexdigest())
    census_path.write_bytes(deployment_archive._encode(census))
    manifest = tmp_path/'manifest.json'
    sealed = seal_transfer(package, manifest, maximum_bytes=100000, maximum_files=2)
    with pytest.raises(ValueError, match='unselected bytes'):
        verify_original_archive(package, manifest, expected_sha256=sealed['sha256'])
