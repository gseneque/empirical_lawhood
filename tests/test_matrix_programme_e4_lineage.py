# SPDX-License-Identifier: MPL-2.0
"""Exact current original-byte handles; exposed fixtures grant no authority."""
from dataclasses import replace
from contextlib import contextmanager
from pathlib import Path
from types import MethodType, SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
from empirical_lawhood.api.matrix_researcher_programme_e4_lineage import programme_e3_originals
from empirical_lawhood.api.matrix_researcher_programme_lineage import read_published_record
from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
from tests.test_matrix_finite_dt_source_assembly import c_backed_source_case, selected_request  # noqa: F401
from tests.test_configured_e3_product_export import export_case, products, original_case  # noqa: F401


@pytest.fixture(autouse=True)
def full_original_read():
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
    with scientific_reconstruction_operation('full'):
        yield


def _with_programme_products(context):
    context.programme_e3_products = MethodType(MatrixProgrammeProjectionContext.programme_e3_products, context)
    return context


def test_produced_e3_handle_keeps_original_body_access_and_canonical_custody(c_backed_source_case):  # noqa: F811
    case = c_backed_source_case
    handle = case.original_e3
    original = handle.publication
    read = read_published_record(case.plane, original.materialization.relative_path,
        type(case.public), len(case.public.canonical_bytes()))
    handle.require_record(read, read.identity)
    assert read == case.public
    assert handle.publication.logical.outcome_access == original.logical.outcome_access
    assert handle.publication.logical.visibility_ceiling == original.logical.visibility_ceiling
    with pytest.raises(ValueError, match='blind canonical publication'):
        MatrixProgrammePublishedInput(handle.record, original)
    changed = replace(read, record_id=read.record_id + '.foreign')
    with pytest.raises(ValueError, match='original identity or byte bound'):
        handle.require_record(changed, changed.identity)
    with pytest.raises(ValueError, match='canonical custody'):
        replace(handle, record=replace(handle.record, object_fingerprint='0' * 64))


def test_current_original_body_corruption_cannot_be_hidden_by_a_report(c_backed_source_case):  # noqa: F811
    case = c_backed_source_case
    relative = case.original_e3.publication.materialization.relative_path
    path = case.plane.root.resolve(relative, for_write=False)
    raw = path.read_bytes()
    try:
        path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
        with pytest.raises((ValueError, RuntimeError, OSError)):
            read_published_record(case.plane, relative, type(case.public), len(raw))
    finally:
        path.write_bytes(raw)
    assert read_published_record(case.plane, relative, type(case.public), len(raw)) == case.public


def test_past_success_report_cannot_replace_actual_original_authority_or_publish(monkeypatch):
    observed = []
    def authority(phase):
        assert phase == 'e3'
        observed.append(phase)
        raise PermissionError('actual current original reveal refused')
    context = _with_programme_products(SimpleNamespace(authority=authority, directory=Path('/disclosed/programme'),
        report=lambda phase: {'scientific_result': {'scientific_completion': 'RETAINED_ADJUDICATION',
            'typed_product_validation': 'COMPLETE'}},
        writer=SimpleNamespace(root=SimpleNamespace(contract=SimpleNamespace(canonical_path='/disclosed')),
            write_batch=lambda *_: pytest.fail('refused original permission published a copy'))))
    with pytest.raises(PermissionError, match='actual current original reveal'):
        with programme_e3_originals(context, publish=True):
            pytest.fail('refused current original access returned protected bytes')
    assert observed == ['e3']


def test_interruption_after_original_export_keeps_embedded_request_bytes_on_fresh_retry(
        c_backed_source_case, export_case):  # noqa: F811
    """Disclosed reader/context seams; actual typed products and custody writes.

    This transport control does not assert the two exposed fixture populations
    form a genuine whole C programme. Downstream scientific joins remain owned
    by their independent actual readers, outside this deliberately closed seam.
    """
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_assembly import MatrixFiniteDtSourceAssemblyRequest
    case, exported = c_backed_source_case, export_case
    exported.read.preparation = case.preparation
    plane = exported.products.plane
    directory = Path(plane.root.contract.canonical_path) / 'programme-embedded-retry'
    receipt_bytes = tuple(value.canonical_bytes() for _, value in sorted(exported.products.receipts.items()))
    def context():
        def authority(phase):
            assert phase == 'e3'
            return (object(), None, SimpleNamespace(reveal_authority_id=exported.products.reveal.object_id),
                exported.products.package, SimpleNamespace(run_plan_id=exported.products.package.run_plan_id),
                exported.products.plan)
        from empirical_lawhood.api.domain_composition.matrix_configured_protected_response.scientific_read import read_protected_e3_original_products
        def original_e3_products(*, selected, package, run_id, reveal_authority_id):
            return read_protected_e3_original_products(selected=selected, artifact_writer=plane,
                run_id=run_id, expected_package=package, reveal_authority_id=reveal_authority_id)
        return _with_programme_products(SimpleNamespace(writer=plane, directory=directory, namespace='disclosed.embedded-retry',
            original_e3_products=original_e3_products,
            authority=authority, design=SimpleNamespace(e3=exported.read.specification),
            method_inputs=lambda phase: pytest.fail('original preparation reopened the entire E3 input graph'),
            inputs=SimpleNamespace(phase=lambda phase: SimpleNamespace(reservation=case.preparation.manifest.reservation))))
    def request(original):
        source = selected_request(case)
        assert type(source) is MatrixFiniteDtSourceAssemblyRequest
        return replace(source, original_e3=original.original_e3,
            original_preparation=original.original_preparation, original_assay=original.original_assay,
            original_products=original.products).canonical_bytes()
    first = []
    with pytest.raises(RuntimeError, match='before phase binding'):
        with programme_e3_originals(context(), publish=True) as original:
            first.append(request(original))
            assert all(handle.publication.created is False for handle in
                (original.original_e3, original.original_preparation, original.original_assay))
            raise RuntimeError('interrupted before phase binding')
    inventory = {path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob('*') if path.is_file()}
    for publish in (True, False):
        with programme_e3_originals(context(), publish=publish) as original:
            assert request(original) == first[0]
            assert all(handle.publication.created is False for handle in
                (original.original_e3, original.original_preparation, original.original_assay))
    assert {path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob('*') if path.is_file()} == inventory
    assert tuple(value.canonical_bytes() for _, value in sorted(exported.products.receipts.items())) == receipt_bytes
    assert exported.calls.count('full-read') == 3


def _live_lineage_context(case, exported, writer):
    """Literal scientific products with actual byte guards and live callbacks."""
    from empirical_lawhood.api.domain_composition.matrix_configured_protected_response.scientific_read import ConfiguredE3OriginalProducts

    state = {'current': 0, 'access': 0, 'allowed': True, 'active': True}
    for receipt in exported.products.receipts.values():
        for materialization in receipt.output_materializations:
            writer.verify_manifest(writer.read_manifest(materialization.relative_path))

    def access():
        state['access'] += 1
        if not state['active'] or not state['allowed']:
            raise PermissionError('exposed original access refused')

    def current():
        state['current'] += 1
        access()
        writer.require_verification_snapshot()

    original = exported.read
    read = ConfiguredE3OriginalProducts(original.package, original.execution_plan,
        original.specification, case.preparation, original.allocation, original.receipts,
        original.models, original.model_freeze, original.calibration, original.calibrated_freeze,
        original.prefit, original.report, original.reveal_authority, current, _access_read=access)

    @contextmanager
    def live_products(**_):
        # Scientific-read seam only. Published products, export joins and the
        # final byte census below are the actual owners under test.
        yield read

    context = SimpleNamespace(writer=writer,
        directory=Path(writer.root.contract.canonical_path) / exported.selection.record_id,
        namespace=exported.selection.record_id, original_e3_products=live_products,
        authority=lambda phase: (object(), None, SimpleNamespace(reveal_authority_id=read.reveal_authority.object_id),
            read.package, SimpleNamespace(run_plan_id=read.package.run_plan_id), read.execution_plan),
        design=SimpleNamespace(e3=read.specification),
        inputs=SimpleNamespace(phase=lambda phase: SimpleNamespace(reservation=case.preparation.manifest.reservation)))
    return _with_programme_products(context), state


@pytest.mark.parametrize('publish', (False, True))
def test_original_export_inspection_keeps_two_full_boundaries_and_live_access(
        c_backed_source_case, export_case, publish, record_property):  # noqa: F811
    plane = export_case.products.plane
    with plane.read_context() as writer:
        context, state = _live_lineage_context(c_backed_source_case, export_case, writer)
        context.writer = plane  # Publication keeps its separate effect lane.
        with programme_e3_originals(context, publish=True) as original:
            expected = tuple(row.canonical_bytes() for row in
                (original.original_e3, original.original_preparation, original.original_assay, *original.products))
        state.update(current=0, access=0)
        context.writer = plane if publish else writer
        with programme_e3_originals(context, publish=publish) as original:
            actual = tuple(row.canonical_bytes() for row in
                (original.original_e3, original.original_preparation, original.original_assay, *original.products))
            assert actual == expected
            assert state['current'] >= 1  # The complete guard precedes the consumer.
            before = state.copy()
            original.require_access()
            assert state['current'] == before['current']
            assert state['access'] == before['access'] + 1
        record_property('publication_selected', publish)
        record_property('full_original_checkpoints', state['current'])
        record_property('live_access_refreshes', state['access'])
        assert state['current'] == (5 if publish else 2)
        assert state['access'] >= 5


@pytest.mark.parametrize('damage', ('original-body', 'revoked-access'))
def test_original_export_inspection_rejects_changes_before_return(
        c_backed_source_case, export_case, damage):  # noqa: F811
    plane = export_case.products.plane
    path = plane.root.resolve(next(iter(export_case.products.receipts.values()))
        .output_materializations[0].relative_path, for_write=False)
    raw = path.read_bytes()
    entered = returned = False
    try:
        with pytest.raises((PermissionError, ValueError, RuntimeError)):
            with plane.read_context() as writer:
                context, state = _live_lineage_context(c_backed_source_case, export_case, writer)
                context.writer = plane
                with programme_e3_originals(context, publish=True):
                    pass
                context.writer = writer
                with programme_e3_originals(context, publish=False):
                    entered = True
                    if damage == 'original-body':
                        path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
                    else:
                        state['allowed'] = False
                returned = True
    finally:
        path.write_bytes(raw)
    assert entered and not returned
