# SPDX-License-Identifier: MPL-2.0
"""Finite shared reads over actual PURE software custody, never qualification."""

from dataclasses import replace
from contextvars import copy_context
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import gc
import os
import shutil
import weakref

import pytest

from empirical_lawhood.api import recursive_contributions as contributions
from empirical_lawhood.api.recursive_inquiry_read import inquiry_projection_read
from empirical_lawhood.science.inquiry.recursive_inquiry import identity
from tests.test_recursive_read_context import counts
from tests.test_recursive_report_projection import wave as wave  # noqa: F401
from tests.test_recursive_report_projection import admitted_wave as admitted_wave  # noqa: F401
from tests.test_recursive_inquiry import episode as episode  # noqa: F401
from tests.test_recursive_contribution_custody import portable_a as portable_a  # noqa: F401


def _stock_plane(plane):
    from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    root = Path(plane.root.contract.canonical_path)
    mount = next(path for path in (root, *root.parents) if path.is_mount())
    contract = replace(plane.root.contract, required_mount_path=str(mount))
    return ExternalArtifactPlane(GuardedExternalRoot(contract), validators=plane.validators,
        semantic_validations=plane.semantic_validations, custody_limits=plane.custody_limits)


def test_projection_shares_one_guarded_read_then_releases_its_roots(wave, monkeypatch):
    plane = _stock_plane(wave.plane)
    observed = counts(monkeypatch)
    with inquiry_projection_read(plane) as reading:
        first = reading.wave(directory=wave.directory, include_products=True)
        second = reading.wave(directory=wave.directory, include_products=True,
            expected=identity(first.packet, first.packet.packet_id))
        assert first is second and first.products['records']
        assert observed == {'loads': 1, 'plans': 1, 'products': 1}
        draft_ref = weakref.ref(first.draft)
    del first, second
    gc.collect()
    assert draft_ref() is None
    with pytest.raises(ValueError, match='escaped'):
        reading.wave(directory=wave.directory, include_products=True)
    with inquiry_projection_read(plane) as fresh:
        fresh.wave(directory=wave.directory, include_products=True)
    assert observed == {'loads': 2, 'plans': 2, 'products': 2}


def test_projection_wrong_packet_refuses_before_products(wave, monkeypatch):
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    packet, _, _, _ = load_authored_wave(directory=wave.directory, artifact_writer=wave.plane)
    changed = replace(identity(packet, packet.packet_id), object_fingerprint='0' * 64)
    observed = counts(monkeypatch)
    with pytest.raises(ValueError, match='exact authored packet'):
        with inquiry_projection_read(_stock_plane(wave.plane)) as reading:
            reading.wave(directory=wave.directory, include_products=True, expected=changed)
    assert observed == {'loads': 1, 'plans': 1, 'products': 0}


@pytest.mark.parametrize('changed', ('semantic_registry', 'read_method'))
def test_projection_cannot_reuse_roots_after_current_policy_changes(wave, monkeypatch, changed):
    with pytest.raises(ValueError, match='read policy'):
        with inquiry_projection_read(_stock_plane(wave.plane)) as reading:
            reading.wave(directory=wave.directory, include_products=True)
            if changed == 'semantic_registry':
                reading.writer.semantic_validations = replace(reading.writer.semantic_validations,
                    registry_id='registry.different-current-validation')
            else:
                monkeypatch.setattr(reading.writer, 'verify_manifest', lambda manifest: None)
            reading.wave(directory=wave.directory, include_products=True)


def test_projection_selected_closure_limits_keep_independent_traversals(wave, monkeypatch):
    from empirical_lawhood.storage.portable_closure import recursive_closure_limits
    from empirical_lawhood.execution.recursive_handoff import RecursiveClosureLimits
    observed = counts(monkeypatch)
    with recursive_closure_limits(RecursiveClosureLimits()):
        with inquiry_projection_read(_stock_plane(wave.plane)) as reading:
            reading.wave(directory=wave.directory, include_products=True)
            reading.wave(directory=wave.directory, include_products=True)
    assert observed == {'loads': 2, 'plans': 2, 'products': 2}


def test_domain_preflight_refuses_before_product_read(wave, monkeypatch):
    observed = counts(monkeypatch)
    def refuse(**roots):
        assert roots['packet'].draft == identity(roots['draft'], roots['draft'].draft_id)
        assert observed == {'loads': 1, 'plans': 1, 'products': 0}
        raise ValueError('original scientific selection refused')
    with pytest.raises(ValueError, match='scientific selection refused'):
        with inquiry_projection_read(_stock_plane(wave.plane)) as reading:
            reading.wave(directory=wave.directory, include_products=True, validate_authored=refuse)
    assert observed == {'loads': 1, 'plans': 1, 'products': 0}


def test_domain_preflight_is_fresh_for_each_consumer(wave, monkeypatch):
    observed, visits = counts(monkeypatch), []
    def validate(**roots):
        visits.append(roots['draft'])
    with inquiry_projection_read(_stock_plane(wave.plane)) as reading:
        first = reading.wave(directory=wave.directory, include_products=True, validate_authored=validate)
        second = reading.wave(directory=wave.directory, include_products=True, validate_authored=validate)
        assert first is second and visits == [first.draft, first.draft]
        def refuse(**roots):
            raise ValueError('current consumer refused')
        with pytest.raises(ValueError, match='current consumer refused'):
            reading.wave(directory=wave.directory, include_products=True, validate_authored=refuse)
    assert observed == {'loads': 1, 'plans': 1, 'products': 1}


def test_projection_final_bytes_refuse_even_with_preserved_stat(wave):
    path = wave.directory / 'draft.json'
    raw, stat = path.read_bytes(), path.stat()
    try:
        with pytest.raises((ValueError, RuntimeError, OSError)):
            with inquiry_projection_read(_stock_plane(wave.plane)) as reading:
                reading.wave(directory=wave.directory, include_products=True)
                path.write_bytes(b'x' + raw[1:])
                os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    finally:
        path.write_bytes(raw)


def test_successor_admission_composes_one_lazy_read_and_starts_fresh(admitted_wave, monkeypatch):
    from empirical_lawhood.api import recursive_authoring as author, recursive_inquiry as inquiry
    from empirical_lawhood.storage.recursive_custody import AuthenticatedRecursivePayloads

    case, reads, external_bodies = admitted_wave, [], []
    wave = case.wave
    original_load = author._load_authored_wave
    original_item = AuthenticatedRecursivePayloads.__getitem__
    def load(**kwargs):
        reads.append((kwargs['directory'], kwargs['lazy_payloads']))
        return original_load(**kwargs)
    def item(payloads, name):
        if name.startswith('external-'):
            external_bodies.append(name)
        return original_item(payloads, name)
    def decision(**kwargs):
        # A decision and its admission need the same already selected authored
        # metadata. Each independent admission must perform a new guarded read.
        original = kwargs['reading'].wave(directory=wave.directory, include_products=False)
        assert original.packet == case.packet
        return case.packet, case.records
    monkeypatch.setattr(author, '_load_authored_wave', load)
    monkeypatch.setattr(AuthenticatedRecursivePayloads, '__getitem__', item)
    monkeypatch.setattr(inquiry, '_read_inquiry_decision', decision)
    plane = _stock_plane(wave.plane)
    first = inquiry.read_inquiry_successor(directory=wave.directory, artifact_writer=plane)
    second = inquiry.read_inquiry_successor(directory=wave.directory, artifact_writer=plane)
    assert first == second and first[0] == case.admission
    assert reads == [(wave.directory, True)] * 2
    assert external_bodies == []


@pytest.mark.parametrize('member', ('draft.json', 'origins.json'))
def test_successor_admission_keeps_final_bytes_guard(admitted_wave, monkeypatch, member):
    from empirical_lawhood.api import recursive_inquiry as inquiry

    case = admitted_wave
    path = case.wave.directory / member
    raw, stat = path.read_bytes(), path.stat()
    original_allowances = inquiry._validate_successor_allowances
    def change(records, draft):
        original_allowances(records, draft)
        path.write_bytes(b'x' + raw[1:])
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    monkeypatch.setattr(inquiry, '_validate_successor_allowances', change)
    try:
        with pytest.raises((ValueError, RuntimeError, OSError)):
            inquiry.read_inquiry_successor(directory=case.wave.directory,
                artifact_writer=_stock_plane(case.wave.plane))
    finally:
        path.write_bytes(raw)


def test_authoring_reuses_decision_supplier_read(admitted_wave, monkeypatch):
    from empirical_lawhood.api import recursive_authoring as author, recursive_inquiry as inquiry
    from empirical_lawhood.execution.recursive_inquiry import InquiryStateSources, InquiryWaveSource

    case, visits = admitted_wave, []
    wave = case.wave
    plane = _stock_plane(wave.plane)
    original = inquiry.read_inquiry_successor(directory=wave.directory, artifact_writer=plane)
    _, products, _, _ = contributions.read_recursive_wave(directory=wave.directory,
        artifact_writer=plane, include_products=True)
    parent = contributions._described(case.draft, products)
    draft = replace(case.draft, draft_id=case.draft.draft_id + '.fork', contribution_parents=(parent,))
    intent = replace(case.records['intent.json'], draft=identity(draft, draft.draft_id))
    records = {**case.records, 'intent.json': intent,
        'decision.json': replace(case.records['decision.json'], human_directed=True),
        'sources.json': InquiryStateSources((InquiryWaveSource(
            wave.directory.relative_to(plane.root.contract.canonical_path).as_posix(),
            identity(case.packet, case.packet.packet_id), True),))}
    original_load = author._load_authored_wave
    def load(**kwargs):
        visits.append(kwargs['directory'])
        return original_load(**kwargs)
    def decision(**kwargs):
        source = kwargs['reading'].wave(directory=wave.directory, include_products=True)
        assert source.packet == original[3]
        return case.packet, records
    # The original parent identity is real. Separate portable-parent custody
    # is an explicit owner double here; its refusals have independent controls.
    monkeypatch.setattr(contributions, 'authenticate_recursive_parents',
        lambda **kwargs: ((None, None, parent, None, None, None),)
        if kwargs['draft'].contribution_parents else ())
    monkeypatch.setattr(author, '_load_authored_wave', load)
    monkeypatch.setattr(inquiry, '_read_inquiry_decision', decision)
    projected = inquiry.preview_inquiry_authoring(decision_directory=wave.directory.parent / 'decision-fixture',
        origins=wave.origins, artifact_writer=plane, supplier_directory=wave.directory,
        human_fork_draft=draft, contribution_dirs=(wave.directory.parent / 'disclosed-parent-locator',))
    assert projected == (case.packet, records, draft)
    assert visits == [wave.directory]


def _reconstructions(monkeypatch):
    visits = []
    original = contributions._authenticate_selected
    def counted(selected, writer, **kwargs):
        visits.append(selected)
        return original(selected, writer, **kwargs)
    monkeypatch.setattr(contributions, '_authenticate_selected', counted)
    return visits


def test_closed_ancestry_context_starts_fresh_and_runs_final_checks():
    checks = []
    with contributions.recursive_contribution_read_context() as original:
        original.lifetime.callback(checks.append, 'original')
        with contributions.recursive_contribution_read_context() as nested:
            assert nested is original
        token = contributions._READ_STACK.set((Path('/original-ancestor'),))
        try:
            copied = copy_context()
        finally:
            contributions._READ_STACK.reset(token)
    assert checks == ['original']
    assert not original.active and original.lifetime is None and not original.entries
    with pytest.raises(ValueError, match='escaped'):
        original.get('original')
    def read_again():
        with contributions.recursive_contribution_read_context() as current:
            assert current is not original and contributions._READ_STACK.get() == ()
            current.lifetime.callback(checks.append, 'fresh')
    copied.run(read_again)
    assert checks == ['original', 'fresh']


def test_copied_ancestry_context_on_another_thread_owns_its_checks():
    checks = []
    with contributions.recursive_contribution_read_context() as original:
        original.lifetime.callback(checks.append, 'original')
        def read_again():
            with pytest.raises(ValueError, match='escaped'):
                original.get('original')
            with contributions.recursive_contribution_read_context() as current:
                assert current is not original
                current.lifetime.callback(checks.append, 'thread')
        with ThreadPoolExecutor(max_workers=1) as workers:
            workers.submit(copy_context().run, read_again).result()
        assert checks == ['thread'] and original.active
    assert checks == ['thread', 'original']


def test_ancestry_final_guard_runs_on_consumer_failure_and_releases_owner():
    checks = []
    with pytest.raises(ValueError, match='consumer failed'):
        with contributions.recursive_contribution_read_context() as current:
            def final_check():
                current.require_current()
                checks.append('final')
            current.lifetime.callback(final_check)
            raise ValueError('consumer failed')
    assert checks == ['final'] and not current.active and current.lifetime is None


def test_nested_ancestry_keeps_cycle_detection(monkeypatch):
    selected = Path('/selected/original-contribution')
    monkeypatch.setattr(contributions, '_selected_directory', lambda *args: selected)
    monkeypatch.setattr(contributions, '_read_policy_key', lambda writer: None)
    def parent(*args, **kwargs):
        return contributions.authenticate_recursive_contribution(directory=selected, artifact_writer=None)
    monkeypatch.setattr(contributions, '_authenticate_selected', parent)
    with pytest.raises(ValueError, match='closure cycles'):
        contributions.authenticate_recursive_contribution(directory=selected, artifact_writer=None)
    assert contributions._current_contribution_reads() is None


def test_closed_copied_ancestry_keeps_actual_final_mutation_guard(portable_a):
    _, _, _, _, consumer, imported, _ = portable_a
    consumer = _stock_plane(consumer)
    with contributions.recursive_contribution_read_context():
        copied = copy_context()
    path = imported / 'contribution.json'
    raw, stat = path.read_bytes(), path.stat()
    def read_and_mutate():
        with contributions.recursive_contribution_read_context():
            contributions.authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
            path.write_bytes(b'x' + raw[1:])
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    try:
        with pytest.raises((ValueError, RuntimeError, OSError)):
            copied.run(read_and_mutate)
    finally:
        path.write_bytes(raw)


def test_ancestry_reconstruction_is_per_copy_and_per_invocation(portable_a, monkeypatch):
    _, _, _, _, consumer, imported, _ = portable_a
    consumer = _stock_plane(consumer)
    other = imported.with_name('another-complete-copy')
    shutil.copytree(imported, other)
    visits = _reconstructions(monkeypatch)
    with contributions.recursive_contribution_read_context():
        first = contributions.authenticate_recursive_contribution(directory=imported, artifact_writer=consumer,
            include_draft=True)
        for _ in range(4):
            again = contributions.authenticate_recursive_contribution(directory=imported, artifact_writer=consumer,
                include_draft=True)
            assert again == first
        copied = contributions.authenticate_recursive_contribution(directory=other, artifact_writer=consumer,
            include_draft=True)
        assert copied[2] == first[2] and copied[0] != first[0]
        assert visits == [imported, other]
        draft_ref = weakref.ref(first[-1])
    del first, again, copied
    gc.collect()
    assert draft_ref() is None
    contributions.authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
    assert visits == [imported, other, imported]


@pytest.mark.parametrize('changed', ('decimal', 'callback_policy'))
def test_changed_scientific_read_policy_reconstructs_ancestry_without_custody_refusal(portable_a, monkeypatch, changed):
    from contextlib import nullcontext
    from decimal import localcontext
    from empirical_lawhood.api import recursive_operations
    _, _, _, _, consumer, imported, _ = portable_a
    consumer = _stock_plane(consumer)
    visits = _reconstructions(monkeypatch)
    with contributions.recursive_contribution_read_context():
        first = contributions.authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
        numerical = localcontext() if changed == 'decimal' else nullcontext()
        with numerical as context:
            if changed == 'decimal':
                context.prec += 1
            else:
                # A different callback-provider policy can supply the same
                # registered science. It must get an ordinary fresh read.
                original = recursive_operations.operation_factories
                monkeypatch.setattr(recursive_operations, 'operation_factories', lambda: original())
            second = contributions.authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
            assert first[2] == second[2] and first[3] == second[3] and first[4] == second[4]
            assert visits == [imported, imported]


@pytest.mark.parametrize('name', ('transport.json', 'contribution.json'))
def test_ancestry_reuse_refreshes_original_control_bytes(portable_a, name):
    _, _, _, _, consumer, imported, _ = portable_a
    consumer = _stock_plane(consumer)
    with pytest.raises((ValueError, RuntimeError, OSError)):
        with contributions.recursive_contribution_read_context():
            contributions.authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
            path = imported / name
            raw, stat = path.read_bytes(), path.stat()
            path.write_bytes(b'x' + raw[1:])
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            contributions.authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)


def test_custom_contribution_policy_keeps_independent_checks(portable_a, monkeypatch):
    _, _, _, _, consumer, imported, _ = portable_a
    consumer = _stock_plane(consumer)
    original = consumer.verify_manifest
    monkeypatch.setattr(consumer, 'verify_manifest', lambda manifest: original(manifest))
    visits = _reconstructions(monkeypatch)
    with contributions.recursive_contribution_read_context():
        for _ in range(2):
            contributions.authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
    assert visits == [imported, imported]


def test_explicit_closure_budget_keeps_original_traversal_and_refusal(portable_a, monkeypatch):
    from empirical_lawhood.storage.portable_closure import recursive_closure_limits
    from empirical_lawhood.execution.recursive_handoff import RecursiveClosureLimits
    _, _, _, _, consumer, imported, _ = portable_a
    consumer = _stock_plane(consumer)
    visits = _reconstructions(monkeypatch)
    with contributions.recursive_contribution_read_context():
        with recursive_closure_limits(RecursiveClosureLimits(maximum_authentications=2)):
            for _ in range(2):
                contributions.authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
            assert visits == [imported, imported]
            with pytest.raises(ValueError, match='depth or authentication bound'):
                contributions.authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
