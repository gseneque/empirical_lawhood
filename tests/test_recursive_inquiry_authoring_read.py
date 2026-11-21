# SPDX-License-Identifier: MPL-2.0
"""Incremental source reads over real PURE custody; no acquisition or authority."""

from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from dataclasses import replace
from decimal import localcontext
import gc
import os
from pathlib import Path
import shutil
import weakref

import pytest

from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.api import recursive_inquiry_read as owner
from empirical_lawhood.storage import recursive_custody
from tests.test_recursive_projection_lifetime import _stock_plane
from tests.test_recursive_report_projection import wave as wave  # noqa: F401


def _visits(monkeypatch):
    visits = []
    original = author._load_authored_wave
    def load(**kwargs):
        visits.append(Path(kwargs['directory']))
        return original(**kwargs)
    monkeypatch.setattr(author, '_load_authored_wave', load)
    return visits


def _read(plane, directory, *, products=False, unentered=False):
    with owner.inquiry_projection_read(plane) as reading:
        return reading.wave(directory=directory, include_products=products, require_unentered=unentered)


def test_authoring_reuses_each_original_metadata_root_and_releases_it(wave, monkeypatch):
    plane, visits = _stock_plane(wave.plane), _visits(monkeypatch)
    with owner.inquiry_authoring_read(plane) as reader:
        first = _read(reader, wave.directory)
        second = _read(plane, wave.directory)
        assert first is second and visits == [wave.directory]
        reference = weakref.ref(first.draft)
        held = owner._AUTHORING_READ.get()
        assert held.entries and held.bytes > 0
    assert not held.active and not held.entries and held.bytes == 0
    del first, second
    gc.collect()
    assert reference() is None
    _read(plane, wave.directory)
    assert visits == [wave.directory, wave.directory]


def test_current_products_are_read_for_each_projection(wave, monkeypatch):
    plane, calls = _stock_plane(wave.plane), []
    original = recursive_custody.read_recursive_products
    def products(**kwargs):
        calls.append('fresh execution, receipts, contacts and scientific products')
        return original(**kwargs)
    monkeypatch.setattr(recursive_custody, 'read_recursive_products', products)
    with owner.inquiry_authoring_read(plane) as reader:
        first = _read(reader, wave.directory, products=True)
        second = _read(plane, wave.directory, products=True)
        assert first.products == second.products and first is not second
        assert len(calls) == 2


def test_moved_equal_packet_cannot_reuse_original_path_validation(wave, monkeypatch):
    plane, visits = _stock_plane(wave.plane), _visits(monkeypatch)
    copied = wave.directory.with_name('authoring-read-copy')
    shutil.copytree(wave.directory, copied)
    with owner.inquiry_authoring_read(plane) as reader:
        _read(reader, wave.directory)
        # A pathname change is not a portable import; original sidecars still
        # bind the original path and must be refused by the ordinary reader.
        with pytest.raises(RuntimeError, match='actual member path'):
            _read(reader, copied)
    assert visits == [wave.directory, copied]


@pytest.mark.parametrize('member', ('draft.json', 'implementation.json'))
@pytest.mark.parametrize('consumer_failure', (False, True))
def test_source_mutation_is_refused_on_final_guard_even_during_failure(wave, member, consumer_failure):
    plane = _stock_plane(wave.plane)
    path = wave.directory / member
    raw, stat = path.read_bytes(), path.stat()
    try:
        with pytest.raises((ValueError, RuntimeError, OSError)) as caught:
            with owner.inquiry_authoring_read(plane) as reader:
                _read(reader, wave.directory)
                _read(reader, wave.directory)
                path.write_bytes(b'x' + raw[1:])
                os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
                if consumer_failure:
                    raise LookupError('consumer failed after source mutation')
        assert not isinstance(caught.value, LookupError)
    finally:
        path.write_bytes(raw)


def test_access_is_current_at_reuse_and_after_last_projection(wave, monkeypatch):
    plane = _stock_plane(wave.plane)
    original = recursive_custody.AuthenticatedRecursivePayloads.require_current
    revoked = False
    def access(payloads):
        if revoked:
            raise PermissionError('original access revoked')
        return original(payloads)
    monkeypatch.setattr(recursive_custody.AuthenticatedRecursivePayloads, 'require_current', access)
    with pytest.raises(PermissionError, match='original access revoked'):
        with owner.inquiry_authoring_read(plane) as reader:
            _read(reader, wave.directory)
            revoked = True
            _read(reader, wave.directory)
    revoked = False
    with pytest.raises(PermissionError, match='original access revoked'):
        with owner.inquiry_authoring_read(plane) as reader:
            _read(reader, wave.directory)
            revoked = True


@pytest.mark.parametrize('setting', ('decimal', 'environment', 'library'))
def test_changed_numerical_settings_reconstruct_original_metadata(wave, monkeypatch, setting):
    plane, visits = _stock_plane(wave.plane), _visits(monkeypatch)
    from contextlib import nullcontext
    from threadpoolctl import threadpool_limits
    import numpy  # noqa: F401 -- load the actual numerical backend before selecting its threads
    with owner.inquiry_authoring_read(plane) as reader:
        _read(reader, wave.directory)
        scope = localcontext() if setting == 'decimal' else threadpool_limits(limits=2) if setting == 'library' else nullcontext()
        with scope as context:
            if setting == 'decimal':
                context.prec += 1
            elif setting == 'environment':
                monkeypatch.setenv('OPENBLAS_NUM_THREADS', '2')
            _read(reader, wave.directory)
        assert visits == [wave.directory, wave.directory]


def test_changed_configuration_validator_cannot_inherit_old_validation(wave, monkeypatch):
    from empirical_lawhood.domains.materials.analytic_material_inquiry.operation_bindings import InquiryOperationConfig
    from empirical_lawhood.domains.materials.analytic_material_inquiry.policy_binding import scientific_work
    plane, visits = _stock_plane(wave.plane), _visits(monkeypatch)
    with owner.inquiry_authoring_read(plane) as reader:
        _read(reader, wave.directory)
        def refuse(self):
            raise ValueError('current config validator refuses')
        monkeypatch.setattr(InquiryOperationConfig, '__post_init__', refuse)
        refreshed = _read(reader, wave.directory)
        assert visits == [wave.directory, wave.directory]
        # Metadata loading supplies no scientific configuration verdict. The
        # actual registered consumer must use the current configuration owner.
        with pytest.raises(ValueError, match='current config validator refuses'):
            scientific_work(refreshed.draft, refreshed.draft.selected_operation_ids[0])


def test_changed_metadata_validator_refuses_during_fresh_source_read(wave, monkeypatch):
    from empirical_lawhood.design.recursive_authoring import RecursiveStudyDraft
    plane, visits = _stock_plane(wave.plane), _visits(monkeypatch)
    with owner.inquiry_authoring_read(plane) as reader:
        _read(reader, wave.directory)
        def refuse(self):
            raise ValueError('current draft validator refuses')
        monkeypatch.setattr(RecursiveStudyDraft, '__post_init__', refuse)
        with pytest.raises(ValueError, match='current draft validator refuses'):
            _read(reader, wave.directory)
        assert visits == [wave.directory, wave.directory]


def test_changed_current_read_policy_refuses_shared_history(wave):
    plane = _stock_plane(wave.plane)
    with pytest.raises(ValueError, match='read policy'):
        with owner.inquiry_authoring_read(plane) as reader:
            _read(reader, wave.directory)
            reader.semantic_validations = replace(reader.semantic_validations,
                registry_id='registry.new-current-validation')
            _read(reader, wave.directory)


@pytest.mark.parametrize('custom', ('manifest', 'traversal', 'capacity'))
def test_custom_policy_traversal_limits_and_eviction_keep_fresh_reads(wave, monkeypatch, custom):
    from contextlib import nullcontext
    from empirical_lawhood.storage.portable_closure import recursive_closure_limits
    from empirical_lawhood.execution.recursive_handoff import RecursiveClosureLimits
    from empirical_lawhood.science.records import decoded_record_store
    plane, visits = _stock_plane(wave.plane), _visits(monkeypatch)
    if custom == 'manifest':
        original = plane.verify_manifest
        monkeypatch.setattr(plane, 'verify_manifest', lambda manifest, **kw: original(manifest, **kw))
    elif custom == 'capacity':
        monkeypatch.setattr(decoded_record_store, 'MAX_SHARED_RECORD_BYTES', 1)
    scope = recursive_closure_limits(RecursiveClosureLimits()) if custom == 'traversal' else nullcontext()
    with scope, owner.inquiry_authoring_read(plane) as reader:
        _read(reader, wave.directory)
        _read(reader, wave.directory)
    assert visits == [wave.directory, wave.directory]


def test_no_cache_admission_keeps_access_guard_until_owner_closes(wave, monkeypatch):
    from empirical_lawhood.science.records import decoded_record_store
    plane = _stock_plane(wave.plane)
    original = recursive_custody.AuthenticatedRecursivePayloads.require_current
    revoked = False
    def require_current(payloads):
        if revoked:
            raise PermissionError('original access revoked without metadata retention')
        return original(payloads)
    monkeypatch.setattr(decoded_record_store, 'MAX_SHARED_RECORD_BYTES', 1)
    monkeypatch.setattr(recursive_custody.AuthenticatedRecursivePayloads, 'require_current', require_current)
    with pytest.raises(PermissionError, match='without metadata retention'):
        with owner.inquiry_authoring_read(plane) as reader:
            _read(reader, wave.directory)
            current = owner._AUTHORING_READ.get()
            assert not current.entries and current.payload_guards
            revoked = True
    assert not current.payload_guards and not current.active


def test_copied_context_after_close_starts_an_independent_lifetime(wave, monkeypatch):
    plane, visits = _stock_plane(wave.plane), _visits(monkeypatch)
    with owner.inquiry_authoring_read(plane) as reader:
        _read(reader, wave.directory)
        copied = copy_context()
        original = owner._AUTHORING_READ.get()
    def fresh():
        with owner.inquiry_authoring_read(plane) as reader:
            assert owner._AUTHORING_READ.get() is not original
            _read(reader, wave.directory)
    copied.run(fresh)
    assert visits == [wave.directory, wave.directory]


def test_copied_context_on_another_thread_has_fresh_source_and_projection_owners(wave, monkeypatch):
    plane, visits = _stock_plane(wave.plane), _visits(monkeypatch)
    with owner.inquiry_authoring_read(plane) as reader:
        original = owner._AUTHORING_READ.get()
        with owner.inquiry_projection_read(reader) as reading:
            reading.wave(directory=wave.directory, include_products=False)
            def fresh():
                with pytest.raises(ValueError, match='escaped'):
                    original.require_current()
                with pytest.raises(ValueError, match='escaped'):
                    reading.wave(directory=wave.directory, include_products=False)
                with owner.inquiry_authoring_read(plane) as new_reader:
                    assert owner._AUTHORING_READ.get() is not original
                    _read(new_reader, wave.directory)
            with ThreadPoolExecutor(max_workers=1) as threads:
                threads.submit(copy_context().run, fresh).result()
    assert visits == [wave.directory, wave.directory]


@pytest.mark.parametrize('changed_policy', (False, True))
def test_execution_requires_the_authoring_source_scope_to_close(wave, monkeypatch, changed_policy):
    from contextlib import nullcontext
    from empirical_lawhood.api import recursive_inquiry
    plane = _stock_plane(wave.plane)
    final = pytest.raises(ValueError, match='read policy') if changed_policy else nullcontext()
    with final, owner.inquiry_authoring_read(plane) as reader:
        if changed_policy:
            original = plane.verify_manifest
            monkeypatch.setattr(plane, 'verify_manifest', lambda value, **kw: original(value, **kw))
        for writer in (plane, reader):
            for run in (execution.run_recursive_wave, recursive_inquiry.run_inquiry_successor):
                with pytest.raises(ValueError, match='before execution'):
                    run(directory=wave.directory, project_root=Path(__file__).resolve().parents[1],
                        artifact_writer=writer)


def test_prospective_no_entry_guard_outlives_its_projection(wave):
    plane = _stock_plane(wave.plane)
    # A second genuine authored wave is not executed. No invented run identity.
    _, draft, _, _ = author.load_authored_wave(directory=wave.directory,
        artifact_writer=plane, lazy_payloads=True)
    target = wave.directory.with_name('unentered-authoring-read')
    draft = replace(draft, draft_id=draft.draft_id + '.unentered')
    source = Path(plane.root.contract.canonical_path) / 'selected-source.json'
    result = author.author_recursive_wave(draft=draft, project_root=Path(__file__).resolve().parents[1],
        artifact_writer=plane, output_dir=target,
        input_bindings=((draft.external_inputs[0].input_id, source),), origins=wave.origins)
    run_path = plane.root.resolve('runs/' + result['run_id'], for_write=True)
    try:
        with pytest.raises(ValueError, match='execution custody'):
            with owner.inquiry_authoring_read(plane) as reader:
                _read(reader, target, unentered=True)
                run_path.mkdir()
    finally:
        run_path.rmdir()
