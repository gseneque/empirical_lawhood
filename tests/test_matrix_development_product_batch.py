# SPDX-License-Identifier: MPL-2.0
"""Real producer declarations and publications with disclosed read seams.

The core retained-run and acquisition readers are replaced explicitly. These
controls test batching and local refusal boundaries, never scientific custody.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_revision_preparation as preparation
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4DevelopmentProduct
from empirical_lawhood.api import recursive_authoring, recursive_execution, selected_e4_method_runtime
from empirical_lawhood.api import selected_e4_native_runtime as owner
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_matrix_selected_e4_methods import selected_revision, selected_e4_populations, selected_bridge, transfer, pin, campaign_fixture  # noqa: F401
from tests.test_recursive_public_service import _plane


@pytest.fixture
def batch(selected_revision, tmp_path, monkeypatch):  # noqa: F811
    f = selected_revision
    acquisition = methods.SelectedE4DevelopmentAcquisition('acquisition.disclosed-batch', 'original/disclosed-dev',
        'run.disclosed-dev', pin('plan.disclosed-dev', 'empirical-lawhood/runtime/development-execution-plan'),
        pin('receipt.disclosed-entry', CanonicalTaskReceipt.SCHEMA), False)
    resources = methods.SelectedE4MethodResources('resources.disclosed-batch', tuple(
        (name, ResourceBudget(1, 1024**3, 0, None, None, None)) for name in ('revision-fit', 'revision-freeze')))
    inputs = preparation.SelectedE4RevisionInputs(campaign_fixture()[0].campaign, f.programme, f.bank,
        acquisition, f.reduction, f.data, resources)
    draft, _ = preparation.lower_development(f.editable, inputs)
    declarations = methods.operation_declarations()
    codecs = {schema: kind for declaration in declarations for schema, kind in declaration.record_codecs.items()}
    compiled = compile_recursive_wave(draft=draft,
        registry=CapabilityRegistry('registry.disclosed-batch', tuple(row.manifest() for row in declarations)),
        registrations=tuple(row.registration() for row in declarations), implementation_commit='a' * 40, output_codecs=codecs)
    plan, run = compiled.execution_plan, SimpleNamespace(run_plan_id='run.disclosed-batch')
    packet = SimpleNamespace(packet_id='packet.disclosed-batch', fingerprint=lambda: 'b' * 64)
    plane = _plane(tmp_path / 'custody')
    receipts, outputs, index, locators = {}, {}, [], {}
    for operation, record in (('revision-fit', f.nomination), ('revision-freeze', f.frozen)):
        task, = (row for row in plan.tasks if row.capability.capability_key == methods.NAMESPACE + '.' + operation)
        output, = (row for row in task.outputs if row.output_id == task.task_id + '.product')
        publication = plane.write(ArtifactWriteRequest(output.logical_artifact_id, 'disclosed/' + operation + '.json', record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'disclosed.batch', 'disclosed', record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        receipt = CanonicalTaskReceipt('receipt.' + operation, run.run_plan_id, task.task_id, 'attempt.' + operation,
            'a' * 40, (), (publication.materialization,), (publication.logical,), (), OperationalStatus.SUCCEEDED, ())
        receipts[task.task_id] = receipt
        outputs[output.logical_artifact_id] = plane.read_manifest(publication.materialization.relative_path)
        index.append({'task_id': task.task_id, 'schema': record.SCHEMA, 'logical_artifact_id': output.logical_artifact_id})
        locators[operation] = SelectedE4DevelopmentProduct(record.identity, 'programme/revision-component', run.run_plan_id,
            ObjectIdentity.from_record(plan.execution_plan_id, plan), task.task_id,
            ObjectIdentity.from_record(receipt.receipt_id, receipt), publication)
    report = {'run_id': run.run_plan_id, 'execution_plan_sha256': plan.fingerprint(), 'packet_sha256': packet.fingerprint()}
    products = {'receipts': receipts, 'outputs': outputs, 'product_index': index}
    result, roots = (report, products, draft, plan), (packet, draft, None, run, plan, None)
    calls = {'roots': 0, 'acquisition': 0, 'operands': []}
    def read(**options):
        calls['roots'] += 1
        assert options['terminal_product_format'] == 'compact'
        validated = options['validate_authored'](packet=packet, draft=draft, source=None,
            payloads={}, run=run, plan=plan, index=None)
        return result, roots, validated
    def replay(**options):
        calls['acquisition'] += 1
        return f.reduction, f.data
    def operands(**options):
        calls['operands'].append(options['config'].operation)
        reduced, data = options['_original_development_reader'](writer=options['writer'], locator=acquisition,
            programme=f.programme, bank=f.bank, data_id=f.data.record_id, _secondary_readout=None)
        assert (reduced, data) == (f.reduction, f.data)
        return {'programme': f.programme, 'bank': f.bank}
    monkeypatch.setattr(recursive_execution, '_read_recursive_wave_with_roots', read)
    monkeypatch.setattr(recursive_authoring, 'load_authored_wave', lambda **_: pytest.fail('second authored packet load'))
    monkeypatch.setattr(owner, 'CurrentDevelopmentTaskCustody', lambda **_: SimpleNamespace(inputs={}))
    monkeypatch.setattr(selected_e4_method_runtime, 'original_development_products', replay)
    monkeypatch.setattr(selected_e4_method_runtime, 'authenticate_selected_e4_development_operands', operands)
    requests = tuple((locators[operation], operation) for operation in ('revision-fit', 'revision-freeze'))
    return SimpleNamespace(plane=plane, calls=calls, requests=requests, codecs=codecs, f=f,
        result=result, roots=roots, report=report)


def test_two_original_products_use_one_packet_and_one_acquisition_replay(batch):
    results = owner.development_products(batch.plane, batch.requests, batch.codecs, include_bank=True)
    assert results == ((batch.f.programme, batch.f.nomination, batch.f.bank),
        (batch.f.programme, batch.f.frozen, batch.f.bank))
    assert batch.calls == {'roots': 1, 'acquisition': 1, 'operands': ['revision-fit', 'revision-freeze']}


@pytest.mark.parametrize('damage', ('run', 'receipt', 'producer', 'record'))
def test_batched_read_keeps_each_original_producer_and_custody_refusal(batch, damage):
    first, (locator, operation) = batch.requests
    if damage == 'run':
        locator = replace(locator, run_id='run.foreign')
    elif damage == 'receipt':
        locator = replace(locator, receipt=replace(locator.receipt, object_id='receipt.foreign'))
    elif damage == 'producer':
        operation = 'revision-fit'
    else:
        locator = replace(locator, record=replace(locator.record, object_id='record.foreign'))
    with pytest.raises((PermissionError, ValueError)):
        owner.development_products(batch.plane, (first, (locator, operation)), batch.codecs)
    assert batch.calls['roots'] <= 1 and batch.calls['acquisition'] <= 1


def test_locator_batch_uses_one_complete_custody_read_without_scientific_replay(batch, monkeypatch):
    from empirical_lawhood.api import matrix_researcher_programme_prepared_lineage as lineage
    calls = []
    def custody(**options):
        calls.append(options)
        assert options['terminal_product_format'] == 'compact' and options['include_products']
        assert options['_scientific_consumer']() is None
        return batch.result, batch.roots
    monkeypatch.setattr(recursive_execution, '_read_recursive_wave_with_retained_roots', custody)
    context = SimpleNamespace(writer=batch.plane,
        child_directory=lambda _: batch.plane.root.resolve('programme', for_write=False),
        report=lambda _: batch.report, plan=SimpleNamespace(specification=SimpleNamespace(
            operations=SimpleNamespace(metadata_budget=SimpleNamespace(source_scan_bytes=64 * 1024**2)))))
    locators = lineage.retained_development_products(context, 'e4.revision',
        (type(batch.f.nomination), type(batch.f.frozen)), locator_type=SelectedE4DevelopmentProduct)
    assert tuple(locator.record for locator in locators) == (batch.f.nomination.identity, batch.f.frozen.identity)
    assert len(calls) == 1
    context.report = lambda _: {**batch.report, 'run_id': 'run.foreign'}
    with pytest.raises(PermissionError, match='original authored instance/run/plan'):
        lineage.retained_development_products(context, 'e4.revision',
            (type(batch.f.nomination), type(batch.f.frozen)), locator_type=SelectedE4DevelopmentProduct)
