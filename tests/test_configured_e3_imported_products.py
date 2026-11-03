# SPDX-License-Identifier: MPL-2.0
"""Cross-run product joins using disclosed custody seams and real product bytes.

These tests do not establish authority or a real unfinished continuation.
Original plan, receipt and current-access readers have separate controls.
"""
from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import configured_e3_imported_products as owner
from empirical_lawhood.api import configured_e3_retained_read, matrix_sampling_runtime, protected_e3_read_custody, recursive_qualified_parents
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_unfinished_execution import ConfiguredE3CompletedOutput, ConfiguredE3UnfinishedExecution
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
from tests.test_configured_e3_product_export import products, original_case, _literal  # noqa: F401


def pin(value, field):
    return ObjectIdentity.from_record(getattr(value, field), value)


def _imported_case(products, monkeypatch, damage=None, *, closed=False):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_closeout_execution import ConfiguredE3ClosedExecution

    names = ('models', 'model-freeze', 'calibration', 'calibrated-freeze')
    old = products.package
    current = _literal('package.disclosed-next', old.SCHEMA, package_id='package.disclosed-next',
        run_plan_id='run.disclosed-next', issued_study=old.issued_study, execution_authority=old.execution_authority)
    phases = dict(zip(names, ('retained-fit', 'retained-model-freeze', 'calibrate', 'calibration-freeze'), strict=True))
    all_tasks = {}
    for name, task in zip(names, products.plan.tasks, strict=True):
        all_tasks[name] = SimpleNamespace(task_id=task.task_id, outputs=task.outputs,
            capability=SimpleNamespace(capability_key='matrix-e3-configured-protected.' + phases[name]),
            external_inputs=(() if name in names[:2] else (SimpleNamespace(expected_payload_schema=(
                ConfiguredE3ClosedExecution if closed else ConfiguredE3UnfinishedExecution).SCHEMA),)))
    plans = {package.run_plan_id: _literal('plan.' + package.run_plan_id, products.plan.SCHEMA,
        execution_plan_id='plan.' + package.run_plan_id, source_plan=SimpleNamespace(object_id=package.run_plan_id),
        tasks=tuple(all_tasks[name] for name in selected)) for package, selected in ((old, names[:2]), (current, names[2:]))}
    receipts = {old.run_plan_id: {}, current.run_plan_id: {}}
    metadata, originals, imports = {}, [], []
    for name in names:
        package = old if name in names[:2] else current
        task = all_tasks[name]
        receipt = replace(products.receipts[task.task_id], run_id=package.run_plan_id)
        receipts[package.run_plan_id][task.task_id] = receipt
        logical, = receipt.output_logical_artifacts
        record = getattr(products.full, name.replace('-', '_'))
        binding = RecursivePriorExecutionBinding('disclosed.' + name, pin(package.issued_study, 'issue_id'),
            pin(package.execution_authority, 'authority_id'), pin(package, 'package_id'), pin(plans[package.run_plan_id], 'execution_plan_id'),
            package.run_plan_id, task.task_id, pin(receipt, 'receipt_id'), logical.logical_artifact_id,
            ObjectIdentity.from_record(record.record_id, record))
        original = MatrixSelectedOriginalProduct(binding, products.reveal)
        originals.append((original, binding.record))
        metadata[binding.task_id] = (package, package.issued_study, SimpleNamespace(authority_id=products.reveal.object_id),
            receipt, logical, ())
        if package is old:
            imports.append(ConfiguredE3CompletedOutput(task.task_id, task.outputs[0].output_id,
                binding.receipt, logical, receipt.output_materializations[0]))
    if damage == 'imported-receipt':
        imports[0] = replace(imports[0], receipt=replace(imports[0].receipt, object_fingerprint='0' * 64))
    if damage == 'current-receipt':
        receipts[current.run_plan_id][all_tasks['calibration'].task_id] = None
    if damage == 'unrelated-run':
        original, expected = originals[0]
        originals[0] = (replace(original, prior_execution=replace(original.prior_execution, run_id='run.unrelated')), expected)
    reads = []; state = {'revoked': damage == 'revoked'}
    def require_access():
        reads.append('access')
        if state['revoked']:
            raise PermissionError('actual original access revoked')
    predecessor = SimpleNamespace(package=old, plan=plans[old.run_plan_id], receipts=receipts[old.run_plan_id],
        writer=products.plane, require_access=require_access, require_current=require_access)
    completed = SimpleNamespace(writer=products.plane, receipts=receipts[current.run_plan_id],
        require_current=require_access, require_access=require_access)
    retained = SimpleNamespace(predecessor=predecessor, unfinished=SimpleNamespace(imported_outputs=tuple(imports)))
    active = {'continuation': False}
    @contextmanager
    def receipt_read(*args, **kwargs):
        if damage == 'incomplete-current':
            raise PermissionError('disclosed continuation terminal is incomplete')
        yield completed
    @contextmanager
    def continuation_read(**kwargs):
        active['continuation'] = True
        try:
            yield retained
        finally:
            active['continuation'] = False
    monkeypatch.setattr(protected_e3_read_custody, 'configured_receipt_read', receipt_read)
    monkeypatch.setattr(configured_e3_retained_read, 'continued_plan_read', continuation_read)
    monkeypatch.setattr(matrix_sampling_runtime, '_original_product_metadata',
        lambda writer, original, expected, **kwargs: metadata[original.prior_execution.task_id])
    monkeypatch.setattr(recursive_qualified_parents, '_ParentReadScope', lambda writer: SimpleNamespace(
        plan_reader=SimpleNamespace(authenticate=lambda **kwargs: plans[kwargs['package'].run_plan_id])))
    monkeypatch.setattr(recursive_qualified_parents, '_semantic_writer', lambda package, plan, writer, codecs: writer)
    monkeypatch.setattr(recursive_qualified_parents, '_require_parent_authorities_current', lambda *args: require_access())
    return SimpleNamespace(originals=tuple(originals), plans=plans, receipts=receipts, metadata=metadata,
        old=old, current=current, names=names, tasks=all_tasks, reads=reads, active=active, state=state)


@pytest.mark.parametrize('damage', (None, 'imported-receipt', 'current-receipt', 'unrelated-run', 'revoked'))
def test_four_products_keep_actual_origins_and_refuse_changed_custody(products, monkeypatch, damage):  # noqa: F811
    case = _imported_case(products, monkeypatch, damage)
    produced = []
    def scope(**kwargs):
        produced.append((kwargs['package'].run_plan_id, kwargs['receipt'].task_id))
    if damage:
        with pytest.raises(PermissionError):
            owner.read_imported_e3_products(products.plane, case.originals, {}, scope_validator=scope)
    else:
        result = owner.read_imported_e3_products(products.plane, case.originals, {}, scope_validator=scope)
        assert result == tuple(getattr(products.full, name.replace('-', '_')).canonical_bytes() for name in case.names)
        assert produced == [(case.old.run_plan_id if name in case.names[:2] else case.current.run_plan_id,
            case.tasks[name].task_id) for name in case.names]
        assert case.reads


@pytest.mark.parametrize('closed', (False, True))
@pytest.mark.parametrize('damage', (None, 'imported-receipt', 'current-receipt', 'unrelated-run', 'revoked',
    'incomplete-current', 'missing-envelope', 'changed-envelope', 'closure-receipt'))
def test_prepared_access_keeps_actual_partial_producers_inside_completed_continuation(products, monkeypatch, closed, damage):  # noqa: F811
    from empirical_lawhood.api import current_result_custody, selected_prepared_access
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling

    case = _imported_case(products, monkeypatch, damage, closed=closed)
    monkeypatch.setattr(current_result_custody.CurrentResultPlanReader, 'authenticate',
        lambda self, **kwargs: case.plans[kwargs['package'].run_plan_id])
    envelopes, facts, calls = {}, set(), []
    for receipts in case.receipts.values():
        for receipt in receipts.values():
            if receipt is None:
                continue
            publication = products.plane.write(ArtifactWriteRequest('envelope.' + receipt.receipt_id,
                'imported-receipts/' + receipt.fingerprint() + '.json', receipt.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                'application/json', 'imported-receipts', 'imported-receipts', receipt.canonical_bytes(),
                VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.OUTCOME_BLIND))
            envelopes[(receipt.run_id, receipt.task_id, receipt.attempt_id)] = (receipt, publication)
            facts.add((publication.logical, publication.materialization))
            facts.update(zip(receipt.output_logical_artifacts, receipt.output_materializations, strict=True))

    def collect(package, plan, writer, reveal, prefixes, *, control_reader=None, allow_partial=False):
        old = package is case.old
        calls.append((package.run_plan_id, allow_partial))
        if old and not allow_partial:
            raise PermissionError('qualified parent lacks a complete successful retained parent execution')
        assert not allow_partial or case.active['continuation'], 'partial closure escaped its authenticated continuation'
        rows = dict(case.receipts[package.run_plan_id])
        if damage == 'closure-receipt' and old:
            rows.pop(next(iter(rows)))
        manifests = tuple(writer.read_manifest(row.relative_path)
            for receipt in rows.values() for row in receipt.output_materializations)
        return SimpleNamespace(by_task=rows, manifests=manifests)

    def envelope(self, run, task, attempt):
        value = envelopes[(run, task, attempt)]
        if damage == 'missing-envelope':
            return None
        if damage == 'changed-envelope':
            publication = value[1]
            return value[0], replace(publication,
                logical=replace(publication.logical, content_sha256='0' * 64))
        return value

    monkeypatch.setattr(recursive_qualified_parents, '_collect_receipt_closure', collect)
    monkeypatch.setattr(ExternalTaskReceiptStore, '_read_envelope', envelope)
    originals = tuple(sorted((original for original, _ in case.originals), key=lambda value: value.record.object_id))

    def read():
        from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
        with scientific_reconstruction_operation('full'):
            return selected_prepared_access.original_input_access(artifact_writer=products.plane,
                locators=tuple(('original.' + str(index), original) for index, original in enumerate(originals)))

    if damage:
        with pytest.raises(PermissionError):
            read()
    else:
        result = read()
        assert result.original_members == facts
        assert result.originals == result.selected_originals == originals
        assert len(result.parents) == 8
        assert set(calls) == {(case.old.run_plan_id, True), (case.current.run_plan_id, False)}
        assert len(calls) == 2
        result.require_current()
        assert not case.active['continuation']
        case.state['revoked'] = True
        with pytest.raises(PermissionError, match='revoked'):
            result.require_current()
