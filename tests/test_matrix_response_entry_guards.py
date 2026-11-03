# SPDX-License-Identifier: MPL-2.0
"""Exposed publication faults and races; no scientific contact is entered."""

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
import stat
from threading import Barrier

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.entry_guards import publish_entry_guards
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.runtime_platform.test_native_subwork import _plane


def arguments(plane, destination='cases/first'):
    return dict(plane=plane, entry_ledger_relative_root='campaign/entry-ledger',
        selected_destination=destination, root_id='history.exposed.root',
        allocation_sha256='a'*64, prepared_packet_sha256='b'*64,
        prepared_review_sha256='c'*64)


def global_path(plane):
    return plane.root.resolve('campaign/entry-ledger/history.exposed.root.'+'a'*64+'.entry.begin.json', for_write=False)


def test_exact_historical_bytes_and_two_durable_barriers_precede_contact(tmp_path, monkeypatch):
    plane = _plane(tmp_path/'guarded')
    events = []
    write = ExternalArtifactPlane._write_staged_bytes
    rename = ExternalArtifactPlane._rename_noreplace
    sync = ExternalArtifactPlane._fsync_directory
    def observed_write(path, raw, **kwargs):
        write(path, raw, **kwargs)
        events.append(('file-synced', path.name))
    def observed_rename(src, dst):
        rename(src, dst)
        events.append(('published', dst.name))
    def observed_sync(path):
        sync(path)
        events.append(('directory-synced', str(path)))
    monkeypatch.setattr(ExternalArtifactPlane, '_write_staged_bytes', staticmethod(observed_write))
    monkeypatch.setattr(ExternalArtifactPlane, '_rename_noreplace', staticmethod(observed_rename))
    monkeypatch.setattr(ExternalArtifactPlane, '_fsync_directory', staticmethod(observed_sync))
    proof = publish_entry_guards(**arguments(plane))
    events.append(('contact', None))
    assert [e[0] for e in events if e[0] in ('file-synced','published','contact')] == [
        'file-synced','published','file-synced','published','contact']
    for index, e in enumerate(events):
        if e[0] == 'published':
            assert events[index+1][0] == 'directory-synced'
    expected = canonical_json_bytes(dict(root_id='history.exposed.root',allocation_sha256='a'*64,
        prepared_packet_sha256='b'*64,selected_destination='cases/first',
        scope='ONE_ROOT_PER_SEALED_ALLOCATION;COMPLETED_OR_UNKNOWN_REQUIRES_RETAINED_INSPECTION'))
    assert global_path(plane).read_bytes() == expected
    for row in proof:
        raw = plane.root.resolve(row['relative_path'],for_write=False).read_bytes()
        assert sha256(raw).hexdigest()==row['sha256'] and len(raw)==row['size_bytes']
    with pytest.raises(FileExistsError):
        publish_entry_guards(**arguments(plane,'cases/competing'))


@pytest.mark.parametrize('point', ('staged-file','after-global-rename','global-directory','local-file','local-directory'))
def test_interruption_never_reaches_contact_and_retains_partial_or_global_barrier(tmp_path, monkeypatch, point):
    plane = _plane(tmp_path/'guarded')
    write, rename, sync = (ExternalArtifactPlane._write_staged_bytes,
        ExternalArtifactPlane._rename_noreplace, ExternalArtifactPlane._fsync_directory)
    def fault_write(path, raw, **kwargs):
        write(path, raw, **kwargs)
        if point=='staged-file' or point=='local-file' and path.parent.name=='first':
            raise OSError('injected interruption after file fsync')
    def fault_rename(src,dst):
        rename(src,dst)
        if point=='after-global-rename' and dst.parent.name=='entry-ledger':
            raise OSError('injected interruption after exclusive publication')
    def fault_sync(path):
        if point=='global-directory' and global_path(plane).exists() and path.name=='entry-ledger':
            raise OSError('injected failure before directory sync')
        if point=='local-directory' and path.name=='first' and (path/'entry.begin.json').exists():
            raise OSError('injected failure before local directory sync')
        sync(path)
    monkeypatch.setattr(ExternalArtifactPlane,'_write_staged_bytes',staticmethod(fault_write))
    monkeypatch.setattr(ExternalArtifactPlane,'_rename_noreplace',staticmethod(fault_rename))
    monkeypatch.setattr(ExternalArtifactPlane,'_fsync_directory',staticmethod(fault_sync))
    contacts = []
    with pytest.raises(OSError):
        publish_entry_guards(**arguments(plane))
        contacts.append('forbidden')
    assert not contacts
    path=global_path(plane)
    assert path.exists() or path.with_name('.'+path.name+'.pending').exists()
    with pytest.raises(FileExistsError):
        publish_entry_guards(**arguments(plane,'cases/replacement'))


@pytest.mark.parametrize('after_sync', (False, True))
def test_file_sync_failure_prevents_contact_without_claiming_a_crash_test(tmp_path, monkeypatch, after_sync):
    plane=_plane(tmp_path/'guarded')
    fsync=os.fsync
    def interrupted(descriptor):
        if stat.S_ISREG(os.fstat(descriptor).st_mode):
            if after_sync:
                fsync(descriptor)
            raise OSError('injected file sync interruption')
        fsync(descriptor)
    monkeypatch.setattr(os,'fsync',interrupted)
    contacts=[]
    with pytest.raises(OSError):
        publish_entry_guards(**arguments(plane))
        contacts.append('forbidden')
    assert not contacts and not global_path(plane).exists()
    pending = global_path(plane).with_name('.'+global_path(plane).name+'.pending')
    assert pending.exists()
    with pytest.raises(FileExistsError):
        publish_entry_guards(**arguments(plane, 'cases/replacement'))


def test_two_competing_destinations_have_one_winner_and_one_contact(tmp_path):
    plane=_plane(tmp_path/'guarded');barrier=Barrier(2)
    def enter(destination):
        barrier.wait()
        try:
            publish_entry_guards(**arguments(plane,destination))
            return ('contact',destination)
        except FileExistsError:
            return ('refused',destination)
    with ThreadPoolExecutor(max_workers=2) as pool:
        a=pool.submit(enter,'cases/one');b=pool.submit(enter,'cases/two')
        result=(a.result(),b.result())
    assert sorted(r[0] for r in result)==['contact','refused']
    winner=next(r[1] for r in result if r[0]=='contact')
    assert json.loads(global_path(plane).read_bytes())['selected_destination']==winner
    assert sum(plane.root.resolve(d+'/entry.begin.json',for_write=False).exists()
               for d in ('cases/one','cases/two'))==1


def test_unsafe_or_changed_guard_operands_refuse_before_publication(tmp_path):
    plane=_plane(tmp_path/'guarded')
    for field,value in (('selected_destination','../escape'),('root_id','BAD ROOT'),
                        ('allocation_sha256','short'),('prepared_review_sha256','x'*64)):
        with pytest.raises(ValueError):
            publish_entry_guards(**(arguments(plane)|{field:value}))
    assert not global_path(plane).exists()
