# SPDX-License-Identifier: MPL-2.0
"""Recorded prepared-access joins with disclosed control-reader seams.

Real product and receipt bytes exercise membership. The issuing history and
continuation readers are disclosed metadata seams, not scientific evidence.
"""
from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import (
    matrix_sampling_runtime, recorded_e3_products, recursive_qualified_parents,
    retained_e3_evidence, selected_prepared_access,
)
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
from tests.test_configured_e3_imported_products import _imported_case
from tests.test_configured_e3_product_export import products, original_case  # noqa: F401
from tests.test_matrix_e3_protected_prefix_science import forbid_native as forbid_native  # noqa: F401


@pytest.fixture
def recorded_case(products, monkeypatch):  # noqa: F811
    case = _imported_case(products, monkeypatch, closed=True)
    originals = tuple(sorted((value for value, _ in case.originals), key=lambda value: value.record.object_id))
    state = {'active': None, 'refuse': None, 'contexts': 0, 'closed': 0}
    collected, metadata_readers, facts, envelopes = [], [], set(), {}
    for receipts in case.receipts.values():
        for receipt in receipts.values():
            publication = products.plane.write(ArtifactWriteRequest('recorded.' + receipt.receipt_id,
                'recorded-receipts/' + receipt.fingerprint() + '.json', receipt.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, 'application/json', 'recorded-receipts',
                'recorded-receipts', receipt.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY,
                (), OutcomeAccess.OUTCOME_BLIND))
            member = products.plane.read_manifest(publication.materialization.relative_path)
            envelopes[(receipt.run_id, receipt.task_id, receipt.attempt_id)] = receipt, member
            facts.add((member.logical, member.materialization))
            facts.update(zip(receipt.output_logical_artifacts, receipt.output_materializations, strict=True))

    def require_access(*args):
        case.reads.append('recorded-current-access')
        if case.state['revoked']:
            raise PermissionError('disclosed current original grant revoked')

    def metadata(original, expected):
        require_access()
        before = case.metadata[original.prior_execution.task_id]
        assert original.record == expected
        if original.prior_execution.run_id != before[0].run_plan_id:
            raise PermissionError('disclosed control reader refused unrelated original run')
        return before

    reader = SimpleNamespace(
        authenticate=lambda **kwargs: case.plans[kwargs['package'].run_plan_id],
        execution_task=lambda execution_plan, task_id: next(
            task for task in execution_plan.tasks if task.task_id == task_id))
    owners = {run_id: SimpleNamespace(package=package, plan=case.plans[run_id], writer=products.plane,
        report={'operational_census': [dict(task_id=task_id, operational_status='SUCCEEDED',
            receipt_id=receipt.receipt_id, receipt_sha256=receipt.fingerprint())
            for task_id, receipt in case.receipts[run_id].items()]})
        for run_id, package in ((case.old.run_plan_id, case.old), (case.current.run_plan_id, case.current))}

    def imported(boundary, task_id):
        require_access()
        receipt = case.receipts[case.old.run_plan_id][task_id]
        if state['refuse'] == 'imported-receipt':
            receipt = replace(receipt, receipt_id='receipt.disclosed-substitution')
        return owners[case.old.run_plan_id], receipt

    @contextmanager
    def context(writer):
        require_access()
        if state['active'] is not None:
            yield state['active']
            require_access()
            return
        with products.plane.read_context() as scoped:
            state['contexts'] += 1
            active = SimpleNamespace(writer=scoped, reader=reader, product_metadata=metadata,
                producer=lambda run_id, reveal_id: owners[run_id], imported=imported,
                require_access=require_access)
            state['active'] = active
            try:
                yield active
                require_access()
            finally:
                state['active'] = None
                state['closed'] += 1

    def original_metadata(writer, original, expected, *, _control_reader=None):
        assert state['active'] is not None
        assert writer is state['active'].writer
        assert _control_reader is reader
        metadata_readers.append(_control_reader)
        return metadata(original, expected)

    def boundary(read, owner):
        require_access()
        if owner.package is case.old:
            return None
        return SimpleNamespace(retention=SimpleNamespace(continued_run_id=case.current.run_plan_id))

    def collect(package, plan, writer, reveal, prefixes, *, control_reader=None, allow_partial=False):
        assert state['active'] is not None and control_reader is reader
        assert allow_partial is (package is case.old)
        collected.append((package.run_plan_id, allow_partial))
        rows = dict(case.receipts[package.run_plan_id])
        if state['refuse'] == 'receipt-census':
            rows.pop(next(iter(rows)))
        manifests = tuple(writer.read_manifest(row.relative_path)
            for receipt in rows.values() for row in receipt.output_materializations)
        if state['refuse'] == 'revoked':
            case.state['revoked'] = True
        return SimpleNamespace(by_task=rows, manifests=manifests)

    def envelope(self, run, task, attempt):
        value = envelopes[(run, task, attempt)]
        if state['refuse'] == 'missing-envelope':
            return None
        if state['refuse'] == 'changed-envelope':
            return value[0], replace(value[1], publication=None,
                logical=replace(value[1].logical, content_sha256='0' * 64))
        return value

    monkeypatch.setattr(retained_e3_evidence, 'retained_e3_evidence_context', context)
    monkeypatch.setattr(recorded_e3_products, 'retained_e3_evidence_context', context)
    monkeypatch.setattr(recorded_e3_products, '_boundary', boundary)
    monkeypatch.setattr(matrix_sampling_runtime, '_original_product_metadata', original_metadata)
    monkeypatch.setattr(recursive_qualified_parents, '_ParentReadScope',
        lambda writer, *, plan_reader: SimpleNamespace(plan_reader=plan_reader))
    monkeypatch.setattr(recursive_qualified_parents, '_collect_receipt_closure', collect)
    monkeypatch.setattr(ExternalTaskReceiptStore, '_read_envelope', envelope)
    from empirical_lawhood.api import configured_e3_imported_products
    monkeypatch.setattr(configured_e3_imported_products, 'imported_e3_product_custody',
        lambda *a, **k: pytest.fail('default prepared access entered retrospective E3 reconstruction'))
    return SimpleNamespace(products=products, case=case, originals=originals, state=state,
        facts=facts, collected=collected, metadata_readers=metadata_readers, reader=reader)


def _read(case):
    with scientific_reconstruction_operation('off'):
        return selected_prepared_access.original_input_access(artifact_writer=case.products.plane,
            locators=tuple(('original.' + str(index), value) for index, value in enumerate(case.originals)))


def test_default_prepared_access_reuses_control_reader_and_keeps_complete_original_members(recorded_case):
    case = recorded_case
    result = _read(case)
    assert result.original_members == case.facts
    assert result.originals == result.selected_originals == case.originals
    assert len(result.parents) == 8
    assert set(case.collected) == {(case.case.old.run_plan_id, True), (case.case.current.run_plan_id, False)}
    assert len(case.collected) == 2
    assert case.metadata_readers == [case.reader] * 4
    assert case.state['contexts'] == case.state['closed'] == 1
    assert case.state['active'] is None
    result.require_current()
    case.case.state['revoked'] = True
    with pytest.raises(PermissionError, match='revoked'):
        result.require_current()


@pytest.mark.parametrize('damage', ('imported-receipt', 'receipt-census', 'missing-envelope', 'changed-envelope', 'revoked'))
def test_default_prepared_access_refuses_changed_original_custody(recorded_case, damage):
    case = recorded_case
    case.state['refuse'] = damage
    with pytest.raises(PermissionError):
        _read(case)
    assert case.state['active'] is None
    assert case.state['contexts'] == case.state['closed'] == 1


def test_product_consumer_uses_same_recorded_metadata_join_and_real_frozen_bytes(recorded_case):
    case = recorded_case
    observations = []

    def consume(**arguments):
        assert case.state['active'] is not None
        observations.append(arguments['receipt'].task_id)

    originals = tuple((value, value.record) for value in case.originals)
    payloads = recorded_e3_products.read_recorded_original_products(case.products.plane,
        originals, {}, scope_validator=consume)
    expected = {value.record.object_id: getattr(case.products.full, name.replace('-', '_')).canonical_bytes()
        for (value, _), name in zip(case.case.originals, case.case.names, strict=True)}
    assert payloads == tuple(expected[value.record.object_id] for value in case.originals)
    assert observations == [value.prior_execution.task_id for value in case.originals]
    assert case.collected == []
    assert case.state['contexts'] == case.state['closed'] == 1


def _parents(case):
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import selected_produced_input_parents
    with scientific_reconstruction_operation('off'):
        return selected_produced_input_parents(case.products.plane, originals=case.originals)


def test_lineage_projection_matches_complete_access_without_constructing_member_authority(recorded_case, monkeypatch):
    case = recorded_case
    expected = _read(case).parents
    case.collected.clear()
    monkeypatch.setattr(recursive_qualified_parents, '_collect_receipt_closure',
        lambda *a, **k: pytest.fail('lineage identities constructed future member access'))
    monkeypatch.setattr(selected_prepared_access, 'original_input_access',
        lambda **k: pytest.fail('lineage identities constructed an access object'))
    result = _parents(case)
    assert type(result) is tuple and result == expected and len(result) == 8
    assert case.collected == []
    assert case.state['active'] is None
    assert case.state['contexts'] == case.state['closed'] == 2


@pytest.mark.parametrize('damage', ('imported-receipt', 'plan', 'revoked-during-read'))
def test_lineage_projection_keeps_actual_producer_and_current_access_guards(recorded_case, damage, monkeypatch):
    case = recorded_case
    if damage == 'imported-receipt':
        case.state['refuse'] = damage
    elif damage == 'plan':
        original = case.originals[0]
        prior = original.prior_execution
        changed = replace(original, prior_execution=replace(prior,
            execution_plan=replace(prior.execution_plan, object_fingerprint='0' * 64)))
        case.originals = (changed, *case.originals[1:])
    else:
        authenticate = case.reader.authenticate
        def revoked(**options):
            result = authenticate(**options)
            case.case.state['revoked'] = True
            return result
        monkeypatch.setattr(case.reader, 'authenticate', revoked)
    with pytest.raises(PermissionError):
        _parents(case)
    assert case.state['active'] is None
    assert case.collected == []


def test_full_lineage_selection_keeps_its_original_complete_reader(recorded_case, monkeypatch):
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import selected_produced_input_parents
    case, calls, parents = recorded_case, [], object()
    def complete(**options):
        calls.append(options)
        return SimpleNamespace(parents=parents)
    monkeypatch.setattr(selected_prepared_access, 'original_input_access', complete)
    with scientific_reconstruction_operation('full'):
        assert selected_produced_input_parents(case.products.plane, originals=case.originals) is parents
    assert len(calls) == 1
    assert tuple(value for _, value in calls[0]['locators']) == case.originals
    assert case.state['contexts'] == 0
