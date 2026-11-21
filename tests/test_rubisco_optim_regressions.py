# SPDX-License-Identifier: MPL-2.0
"""OPTIM regressions: real storage boundaries and independent scalar references.

No molecular engine, remote host or scientific experiment is executed.
"""

from fractions import Fraction
from hashlib import sha256
import random
import os
import tempfile

import numpy as np
import pytest

from empirical_lawhood.methods.binary64_reduction import dot, norm, REDUCTION_CONTRACT
from empirical_lawhood.domains.rubisco.rubisco_response.geometry_domain_minimizer import minimize_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import _check_transition
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics import durable_preparation as durable


@pytest.mark.numerical(oracle="exact rational sum of separately rounded binary64 products, including catastrophic cancellation")
def test_checkpoint_scalar_reductions_match_independent_rational_oracle():
    left = (1e16, 1., -1e16, .125, -.5)
    right = (1., 1., 1., 8., .5)
    expected = float(sum((Fraction.from_float(float(a*b)) for a,b in zip(left,right,strict=True)),Fraction()))
    assert dot(left,right) == expected == 1.75
    assert norm((3.,4.)) == 5.
    with pytest.raises(ValueError):
        dot((1.,2.),(1.,))
    with pytest.raises(ValueError):
        dot((float('nan'),),(1.,))


@pytest.mark.numerical(oracle="positive diagonal quadratic has exact stationary point zero; accepted checkpoint scalars independently rejoined")
def test_producer_and_reader_do_not_depend_on_numpy_dot(monkeypatch):
    def forbidden(*args,**kwargs):
        raise AssertionError('threaded/vendor dot must not own retained checkpoint scalars')
    monkeypatch.setattr(np,'dot',forbidden)
    diagonal=np.array([1.,2.,4.]); states=[]
    def objective(x):
        return float(sum(float(a*b*b) for a,b in zip(diagonal,x,strict=True))/2),diagonal*x
    def checkpoint(state):
        states.append(state);return False
    result=minimize_geometry(objective,np.array([.03,.04,.02]),violation_type=ValueError,
        maximum_gradient=1e-8,maximum_iterations=200,checkpoint_callback=checkpoint)
    assert result.success
    assert np.max(np.abs(result.x)) < 1e-8
    assert result.settings['scalar_reduction'] == REDUCTION_CONTRACT
    for previous,current in zip(states,states[1:]):
        _check_transition(previous,current)


def test_archive_publication_compresses_once_and_preserves_all_original_bytes(tmp_path,monkeypatch):
    native=tmp_path/'native';native.mkdir();(native/'result.bin').write_bytes(b'original native bytes'*1000)
    calls=[];original=durable.compressed_archive_chunks
    def observed(*args,**kwargs):
        calls.append(1);yield from original(*args,**kwargs)
    monkeypatch.setattr(durable,'compressed_archive_chunks',observed)
    outputs={}
    class Progress:
        def publish_output(self,entry,name,chunks,**limits):
            payload=b''.join(chunks)
            assert len(payload) <= limits['maximum_bytes']
            if name == 'files.census':
                assert len(payload)==limits['expected_size_bytes']
                assert sha256(payload).hexdigest()==limits['expected_physical_sha256']
            else:
                assert 'expected_size_bytes' not in limits
                assert 'expected_physical_sha256' not in limits
            outputs[name]=payload;return name
    selected,returned=durable.publish_directory(Progress(),None,native,tmp_path, selected_census=durable.directory_census(native, tmp_path))
    assert calls==[1] and returned==('files.raw','files.census')
    uncompressed=b''.join(durable.uncompressed_archive_chunks((outputs['files.raw'],)))
    assert uncompressed==b''.join(durable.raw_archive_chunks(tmp_path,selected))


def test_raw_census_hashes_each_stream_once_and_expected_streams_still_refuse_changes(tmp_path, monkeypatch):
    native = tmp_path/'native'
    native.mkdir()
    path = native/'original'
    path.write_bytes(b'exact selected original')
    constructed = []
    def counted(*args, **kwargs):
        constructed.append(1)
        return sha256(*args, **kwargs)
    monkeypatch.setattr(durable, 'sha256', counted)
    selected = durable.directory_census(native, tmp_path)
    assert constructed == [1]
    assert b''.join(durable.file_chunks(path, expected=selected.files[0])) == path.read_bytes()
    assert constructed == [1, 1]
    path.write_bytes(b'changed original bytes!')
    with pytest.raises(ValueError, match='selected byte census'):
        b''.join(durable.file_chunks(path, expected=selected.files[0]))


@pytest.mark.parametrize('damage', ['changed', 'added', 'removed'])
def test_archive_source_mutation_is_still_refused_before_commit(tmp_path, damage):
    native=tmp_path/'native';native.mkdir();path=native/'result.bin';path.write_bytes(b'original')
    committed = []
    class Progress:
        def publish_output(self,entry,name,chunks,**limits):
            iterator=iter(chunks);next(iterator)
            if damage == 'changed':
                before = path.stat()
                path.write_bytes(b'changed!')
                os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
            elif damage == 'added':
                (native/'unexpected').write_bytes(b'unselected')
            else:
                path.unlink()
            tuple(iterator)
            committed.append(name)
    with pytest.raises((ValueError, OSError),match='changed before publication|selected byte census|No such file'):
        durable.publish_directory(Progress(),None,native,tmp_path, selected_census=durable.directory_census(native, tmp_path))
    assert committed == []


def test_archive_consumer_failure_cannot_publish_census_or_claim_completion(tmp_path):
    native = tmp_path/'native'
    native.mkdir()
    (native/'original').write_bytes(b'original')
    calls = []
    class Progress:
        def publish_output(self, entry, name, chunks, **limits):
            calls.append(name)
            iterator = iter(chunks)
            next(iterator)
            raise OSError('consumer refused before stream completion')
    with pytest.raises(OSError, match='consumer refused'):
        durable.publish_directory(Progress(), None, native, tmp_path, selected_census=durable.directory_census(native, tmp_path))
    assert calls == ['files.raw']


def test_selected_archive_census_refuses_foreign_directory_before_any_body_read(tmp_path, monkeypatch):
    native, foreign = tmp_path/'native', tmp_path/'foreign'
    native.mkdir()
    foreign.mkdir()
    (native/'result').write_bytes(b'selected unit')
    (foreign/'result').write_bytes(b'foreign unit')
    selected = durable.directory_census(foreign, tmp_path)
    monkeypatch.setattr(durable, 'file_chunks', lambda *a, **kw: pytest.fail('foreign body read'))
    monkeypatch.setattr(tempfile, 'TemporaryFile', lambda *a, **kw: pytest.fail('spool opened'))
    class Progress:
        def publish_output(self, *args, **kwargs):
            pytest.fail('publication entered')
    with pytest.raises(ValueError, match='outside its selected directory'):
        durable.publish_directory(Progress(), None, native, tmp_path, selected_census=selected)


def test_archive_streams_without_private_spool_or_global_tmpdir(tmp_path, monkeypatch):
    selected = tmp_path / 'selected'; selected.mkdir()
    foreign = tmp_path / 'cached'; foreign.mkdir()
    native = selected / 'native'; native.mkdir()
    (native / 'original').write_bytes(b'original')
    monkeypatch.setattr(tempfile, 'tempdir', str(foreign))
    monkeypatch.setattr(tempfile, 'TemporaryFile', lambda *a, **kw: pytest.fail('redundant private spool'))
    class Progress:
        def publish_output(self, entry, name, chunks, **limits):
            payload = b''.join(chunks)
            assert len(payload) <= limits['maximum_bytes']
            return name
    durable.publish_directory(Progress(), None, native, selected, selected_census=durable.directory_census(native, selected))
    assert not tuple(foreign.iterdir())
    assert {path.name for path in selected.iterdir()} == {'native'}


def test_archive_unconsumed_stream_cannot_publish_typed_census(tmp_path):
    native = tmp_path / 'native'; native.mkdir()
    (native / 'original').write_bytes(b'original')
    calls = []
    class IncompletePublisher:
        def publish_output(self, entry, name, chunks, **limits):
            calls.append(name)
            next(iter(chunks))
            return name
    with pytest.raises(ValueError, match='did not consume'):
        durable.publish_directory(IncompletePublisher(), None, native, tmp_path,
                                  selected_census=durable.directory_census(native, tmp_path))
    assert calls == ['files.raw']


def test_global_registry_publishes_gzip_above_previous_arbitrary_operand_limit(tmp_path):
    """Exercise actual global codec selection with a complete >64MiB archive."""
    from empirical_lawhood.api.recursive_operation_index import operation_storage_codecs
    from empirical_lawhood.storage.contracts.artifacts import ArtifactStreamWriteRequest,ArtifactProfile
    from empirical_lawhood.science.evidence.evidence import VisibilityCeiling,OutcomeAccess
    from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import RAW_SCHEMA
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_operation import operation_declaration as analysis
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import operation_declaration as prefix
    from tests.runtime_platform.test_native_subwork import _plane
    native=tmp_path/'native';native.mkdir()
    rng=random.Random(135);block_size=2**20
    with (native/'complete-return.bin').open('wb') as stream:
        for _ in range(65):stream.write(rng.randbytes(block_size))
    selected=durable.directory_census(native,tmp_path)
    payload=tmp_path/'archive.gz';expected=sha256();size=0
    with payload.open('wb') as stream:
        for block in durable.compressed_archive_chunks(tmp_path,selected):
            stream.write(block);expected.update(block);size+=len(block)
    assert size>64*2**20
    plane=_plane(tmp_path/'custody',binary_codecs=operation_storage_codecs())
    result=plane.write_stream(ArtifactStreamWriteRequest('complete.original.archive','outputs/archive.gz',
        RAW_SCHEMA,ArtifactProfile.RAW_SOURCE_BYTES,'application/gzip','archive.scope','outputs',
        durable.file_chunks(payload),maximum_bytes=size,expected_size_bytes=size,
        expected_physical_sha256=expected.hexdigest(),visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
    assert result.materialization.size_bytes==size
    assert result.materialization.physical_sha256==expected.hexdigest()
    assert next(p for p in analysis().input_ports if p.port_id=='native-array').maximum_size_bytes is None
    assert next(p for p in prefix(continuation=True).input_ports if p.port_id=='native-continuation-archive').maximum_size_bytes is None
