# SPDX-License-Identifier: MPL-2.0
"""Exposed accounting controls; no solver or scientific qualification evidence."""

from dataclasses import replace
from decimal import Decimal, localcontext
from hashlib import sha256
import json

import pytest

from empirical_lawhood.api.work_costs import project_attempt_cost_work, project_native_cost_work, read_work_cost_account, retain_work_cost_account, validate_work_cost_evidence
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.execution.work_costs import BilledResourceWindow, CostCoverage, CostEvidence, CostQuantity, CostWorkScope, WorkCostAccount, WorkCostMeasurement, WorkCostOutcome, summarize_work_cost
from tests.runtime_platform.test_native_subwork import _complete, _plane, _publish, _selected

D = Decimal


def raw_source(identifier, value):
    raw = (json.dumps(value,sort_keys=True) + '\n').encode()
    source = CostEvidence(identifier,sha256(raw).hexdigest(),len(raw),'Exposed software measurement fixture.')
    return source,raw


def receipt(task, *, failed=False):
    return CanonicalTaskReceipt('receipt.'+task,'exposed.run',task,'attempt.'+task,'a'*40,
        (),(),(),(),OperationalStatus.FAILED if failed else OperationalStatus.SUCCEEDED,
        ('EXPOSED_FAILURE',) if failed else ())


def account_fixture(*, unknown_recovery=False, include_whole=True):
    original = {
        'invocation_id':'exposed.invocation',
        'cpu_seconds':'10.000000000000000000000000000001',
        'elapsed_seconds':'5', 'retained_bytes':600, 'aggregate_peak_rss_bytes':1000,
        'exclusive_cpu_seconds':'2.000000000000000000000000000001',
        'a_cpu_seconds':'4','b_cpu_seconds':'3',
        'a_gpu_seconds':'3','b_gpu_seconds':'3','exclusive_gpu_seconds':'0',
        'bill':{'resource_id':'exposed.gpu','started_at_utc':'2026-11-09T00:00:00Z',
                'ended_at_utc':'2026-11-09T00:01:00Z','billed_usd':'0.125'},
    }
    source, raw = raw_source('exposed.invocation',original)
    root = CostWorkScope('invocation',source.identity,source.evidence_id,(source.evidence_id,),
        WorkCostOutcome.OBSERVED_INVOCATION,'Complete exposed invocation, including both attempts and recovery.')
    a = project_attempt_cost_work(receipt('a'),parent_scope_id=root.scope_id)
    b = project_attempt_cost_work(receipt('b',failed=True),parent_scope_id=root.scope_id)
    recovery_source,recovery_raw = raw_source('exposed.recovery',{'cpu_seconds':None if unknown_recovery else '1',
        'elapsed_seconds':'0.5','peak_rss_bytes':300,'gpu_seconds':'0'})
    recovery = CostWorkScope('recovery',recovery_source.identity,recovery_source.evidence_id,
        (recovery_source.evidence_id,),WorkCostOutcome.RECOVERY,'Separate completed-result read.',
        root.scope_id,(a['work'].scope_id,))
    evidence = (source,recovery_source,*a['evidence'],*b['evidence'])
    sources = {source.evidence_id:raw,recovery_source.evidence_id:recovery_raw,
               **a['evidence_bytes'],**b['evidence_bytes']}
    measurements = []
    def measured(identifier,scope,coverage,quantity,value,evidence,pointer):
        measurements.append(WorkCostMeasurement(identifier,scope,coverage,quantity,value,evidence,pointer,
            'Exposed original meter scope; software control only.'))
    exclusive = CostCoverage.EXCLUSIVE; inclusive = CostCoverage.INCLUDING_DESCENDANTS
    if include_whole:
        for name,quantity in (('cpu_seconds',CostQuantity.CPU_SECONDS),('elapsed_seconds',CostQuantity.ELAPSED_SECONDS),
                               ('retained_bytes',CostQuantity.RETAINED_BYTES),('aggregate_peak_rss_bytes',CostQuantity.PEAK_RSS_BYTES)):
            measured('whole.'+name,root.scope_id,inclusive,quantity,D(original[name]),source.evidence_id,(name,))
    measured('overhead.cpu',root.scope_id,exclusive,CostQuantity.CPU_SECONDS,D(original['exclusive_cpu_seconds']),
             source.evidence_id,('exclusive_cpu_seconds',))
    for name,projection in (('a',a),('b',b)):
        measured(name+'.cpu',projection['work'].scope_id,exclusive,CostQuantity.CPU_SECONDS,D(original[name+'_cpu_seconds']),
                 source.evidence_id,(name+'_cpu_seconds',))
    measured('recovery.cpu',recovery.scope_id,exclusive,CostQuantity.CPU_SECONDS,
        None if unknown_recovery else D(1),recovery_source.evidence_id,('cpu_seconds',))
    measured('recovery.wall',recovery.scope_id,exclusive,CostQuantity.ELAPSED_SECONDS,
        D('0.5'),recovery_source.evidence_id,('elapsed_seconds',))
    measured('recovery.peak',recovery.scope_id,exclusive,CostQuantity.PEAK_RSS_BYTES,
        D(300),recovery_source.evidence_id,('peak_rss_bytes',))
    bill = BilledResourceWindow('shared.bill','exposed.gpu',original['bill']['started_at_utc'],original['bill']['ended_at_utc'],
        tuple(sorted((a['work'].scope_id,b['work'].scope_id))),D('0.125'),source.evidence_id,('bill','billed_usd'),
        'Original shared resource invoice. Fixture amount, not a real purchase.',
        ('bill','resource_id'),('bill','started_at_utc'),('bill','ended_at_utc'))
    account = WorkCostAccount('exposed.account','Exposed full invocation, both attempts and separate recovery.',
        tuple(sorted(evidence,key=lambda row:row.evidence_id)),
        tuple(sorted((root,a['work'],b['work'],recovery),key=lambda row:row.scope_id)),
        tuple(sorted(measurements,key=lambda row:row.measurement_id)),(bill,))
    return account,sources


def test_nested_measurements_shared_bill_failure_and_recovery_match_independent_ledger():
    account,sources = account_fixture()
    account = replace(account,billing_windows=(replace(account.billing_windows[0],window_id='alias.bill'),*account.billing_windows))
    with localcontext() as context:
        context.prec = 2
        report = validate_work_cost_evidence(account=account,evidence_bytes=sources)
        # Independently fixed ledger: 2.000...001 invocation overhead, 4+3 for
        # distinct successful/failed attempts, 1 for the separate recovery.
        assert report['quantities']['CPU_SECONDS']['value'] == D('10.000000000000000000000000000001')
        exclusive = replace(account,measurements=tuple(row for row in account.measurements if row.measurement_id != 'whole.cpu_seconds'))
        assert summarize_work_cost(exclusive)['quantities']['CPU_SECONDS']['value'] == D('10.000000000000000000000000000001')
    assert report['billed_usd'] == D('0.125') and len(report['selected_billing_window_ids']) == 1
    assert len(report['shared_billing_aliases_not_added']) == 1
    assert report['quantities']['CPU_SECONDS']['selected_measurement_ids'] == ('whole.cpu_seconds',)
    assert len(report['quantities']['CPU_SECONDS']['included_observations_not_added']) == 4
    assert {row['outcome'] for row in report['work_outcomes']} >= {'SUCCEEDED','FAILED','RECOVERY'}
    assert report['quantities']['ELAPSED_SECONDS']['value'] == D(5)
    assert report['quantities']['PEAK_RSS_BYTES']['value'] == D(1000)
    assert report['quantities']['GPU_DEVICE_SECONDS']['value'] is None
    assert report['estimates_included'] is False and report['scientific_authority'] == 'NONE'
    assert decode_canonical_bytes(account.canonical_bytes(),WorkCostAccount,maximum_bytes=None) == account


def test_unknown_component_survives_known_outer_measurement_and_is_not_zero_when_outer_is_absent():
    account,sources = account_fixture(unknown_recovery=True)
    report = validate_work_cost_evidence(account=account,evidence_bytes=sources)
    assert report['quantities']['CPU_SECONDS']['value'] == D('10.000000000000000000000000000001')
    assert report['quantities']['CPU_SECONDS']['unknown_measurement_ids'] == ('recovery.cpu',)
    without_outer = replace(account,measurements=tuple(row for row in account.measurements if row.measurement_id != 'whole.cpu_seconds'))
    value = summarize_work_cost(without_outer)['quantities']['CPU_SECONDS']
    assert value['value'] is None and value['known_disjoint_subtotal'] == D('9.000000000000000000000000000001')
    assert value['unmeasured_exclusive_work_ids'] == ('recovery',)


def test_elapsed_and_peak_components_are_never_summed_into_a_whole_account_measurement():
    account,sources = account_fixture(include_whole=False)
    report = validate_work_cost_evidence(account=account,evidence_bytes=sources)
    for name in ('ELAPSED_SECONDS','PEAK_RSS_BYTES','RETAINED_BYTES','GPU_DEVICE_SECONDS'):
        assert report['quantities'][name]['value'] is None
    assert report['quantities']['CPU_SECONDS']['value'] == D('10.000000000000000000000000000001')
    assert summarize_work_cost(replace(account,billing_windows=()))['billed_usd'] is None


def test_concurrent_gpu_components_do_not_establish_disjoint_device_time():
    account,sources = account_fixture(include_whole=False)
    rows = []
    for scope in account.work:
        if scope.scope_id == 'invocation':
            evidence,pointer,value = 'exposed.invocation',('exclusive_gpu_seconds',),D(0)
        elif scope.scope_id == 'recovery':
            evidence,pointer,value = 'exposed.recovery',('gpu_seconds',),D(0)
        else:
            task = 'a' if scope.outcome is WorkCostOutcome.SUCCEEDED else 'b'
            evidence,pointer,value = 'exposed.invocation',(task+'_gpu_seconds',),D(3)
        rows.append(WorkCostMeasurement('gpu.'+scope.scope_id,scope.scope_id,CostCoverage.EXCLUSIVE,
            CostQuantity.GPU_DEVICE_SECONDS,value,evidence,pointer,'Overlapping kernel observations on one shared device.'))
    account = replace(account,measurements=tuple(sorted((*account.measurements,*rows),key=lambda row:row.measurement_id)))
    report = validate_work_cost_evidence(account=account,evidence_bytes=sources)['quantities']['GPU_DEVICE_SECONDS']
    assert report['unmeasured_exclusive_work_ids'] == ()
    assert report['value'] is None and report['known_disjoint_subtotal'] is None


def test_missing_enclosing_overhead_remains_an_unknown_part_of_the_complete_denominator():
    account,_ = account_fixture(include_whole=False)
    account = replace(account,measurements=tuple(row for row in account.measurements if row.measurement_id != 'overhead.cpu'))
    result = summarize_work_cost(account)['quantities']['CPU_SECONDS']
    assert result['value'] is None and result['known_disjoint_subtotal'] == D(8)
    assert result['unmeasured_exclusive_work_ids'] == ('invocation',)


@pytest.mark.parametrize('fault',('value','bytes','omitted-source','billing-resource','billing-interval'))
def test_original_measurement_and_billing_substitution_refuses_before_custody_write(tmp_path,fault):
    account,sources = account_fixture(); plane = _plane(tmp_path / 'guarded')
    if fault == 'value':
        account = replace(account,measurements=tuple(replace(row,value=D(400)) if row.measurement_id == 'a.cpu' else row for row in account.measurements))
    elif fault == 'bytes':
        sources['exposed.invocation'] += b' '
    elif fault == 'omitted-source':
        del sources['exposed.invocation']
    else:
        bill = account.billing_windows[0]
        bill = replace(bill,**({'resource_id':'another.gpu'} if fault == 'billing-resource' else {'ended_at_utc':'2026-11-09T00:02:00Z'}))
        account = replace(account,billing_windows=(bill,))
    destination = tmp_path / 'guarded/refused'
    with pytest.raises(ValueError):
        retain_work_cost_account(account=account,evidence_bytes=sources,artifact_writer=plane,output_directory=destination)
    assert not destination.exists()


@pytest.mark.parametrize('fault',('renamed-work','different-quantity','different-coverage','cycle','reused-child'))
def test_scope_aliases_conversion_and_cycles_refuse(fault):
    account,_ = account_fixture()
    with pytest.raises(ValueError):
        if fault == 'renamed-work':
            replace(account,work=tuple(sorted((*account.work,replace(account.work[0],scope_id='alias')),key=lambda row:row.scope_id)))
        elif fault in ('different-quantity','different-coverage'):
            row = next(row for row in account.measurements if row.measurement_id == 'a.cpu')
            replacement = (replace(row,measurement_id='alias',quantity=CostQuantity.GPU_DEVICE_SECONDS)
                           if fault == 'different-quantity' else replace(row,measurement_id='alias',scope_id='recovery'))
            replace(account,measurements=tuple(sorted((*account.measurements,replacement),key=lambda row:row.measurement_id)))
        elif fault == 'cycle':
            replace(account,work=tuple(replace(row,parent_scope_id='recovery') if row.scope_id == 'invocation' else row for row in account.work))
        else:
            recovery = next(row for row in account.work if row.scope_id == 'recovery')
            replace(account,work=tuple(replace(row,parent_scope_id='recovery') if row.scope_id == recovery.reuses_scope_ids[0] else row for row in account.work))


def test_changed_receipt_for_same_attempt_cannot_become_another_physical_work():
    account,sources = account_fixture()
    changed = project_attempt_cost_work(replace(receipt('a'),receipt_id='changed.receipt'))
    account = replace(account,work=tuple(sorted((*account.work,changed['work']),key=lambda row:row.scope_id)),
        evidence=tuple(sorted((*account.evidence,*changed['evidence']),key=lambda row:row.evidence_id)))
    with pytest.raises(ValueError,match='original work|Original work'):
        validate_work_cost_evidence(account=account,evidence_bytes={**sources,**changed['evidence_bytes']})


def test_partially_overlapping_resource_bills_and_conflicting_same_coverage_refuse():
    account,_ = account_fixture(); bill = account.billing_windows[0]
    # A separate original meter field does not permit overlapping resource time.
    later = replace(bill,window_id='later.bill',started_at_utc='2026-11-09T00:00:30Z',
                    ended_at_utc='2026-11-09T00:01:30Z',value_pointer=('another-bill','billed_usd'))
    with pytest.raises(ValueError,match='overlapping resource bills'):
        replace(account,billing_windows=(later,bill))
    row = next(row for row in account.measurements if row.measurement_id == 'whole.cpu_seconds')
    conflict = replace(row,measurement_id='conflict',value=D(20),value_pointer=('another-meter',))
    with pytest.raises(ValueError,match='conflicting measured values'):
        summarize_work_cost(replace(account,measurements=tuple(sorted((*account.measurements,conflict),key=lambda row:row.measurement_id))))


def test_impossible_inclusive_measurement_and_unknown_bill_remain_explicit():
    account,_ = account_fixture()
    with pytest.raises(ValueError,match='contradict.*additive inclusion'):
        summarize_work_cost(replace(account,measurements=tuple(replace(row,value=D(6))
            if row.measurement_id == 'whole.cpu_seconds' else row for row in account.measurements)))
    unknown = replace(account.billing_windows[0],billed_usd=None,value_pointer=None)
    report = summarize_work_cost(replace(account,billing_windows=(unknown,)))
    assert report['billed_usd'] is None and report['billing_status'] == 'UNKNOWN'
    assert report['unknown_billing_window_ids'] == (unknown.window_id,)


def test_guarded_publication_and_read_preserve_original_bytes_without_execution(tmp_path,monkeypatch):
    account,sources = account_fixture(); plane = _plane(tmp_path / 'guarded'); destination = tmp_path / 'guarded/costs'
    result = retain_work_cost_account(account=account,evidence_bytes=sources,artifact_writer=plane,output_directory=destination)
    original = {path.relative_to(destination):path.read_bytes() for path in destination.rglob('*') if path.is_file()}
    from empirical_lawhood.execution.local.execution import LocalProcessExecutor
    monkeypatch.setattr(LocalProcessExecutor,'execute',lambda *a,**k: pytest.fail('account read executed work'))
    retained = read_work_cost_account(directory=destination,artifact_writer=plane)
    assert retained['account'] == account and retained['summary'] == result['summary']
    assert retained['new_execution'] is False and retained['read_cpu_seconds'] is None
    assert original == {path.relative_to(destination):path.read_bytes() for path in destination.rglob('*') if path.is_file()}
    with pytest.raises(FileExistsError):
        retain_work_cost_account(account=account,evidence_bytes=sources,artifact_writer=plane,output_directory=destination)
    (destination / 'evidence.0000.json').write_bytes(b'{}\n')
    with pytest.raises((ValueError,RuntimeError,OSError)):
        read_work_cost_account(directory=destination,artifact_writer=plane)


def test_native_projection_uses_original_custody_and_preserves_unknown_costs(tmp_path):
    store,definition,inputs = _selected(tmp_path)
    entry = store.begin(definition,inputs); store.contact(entry)
    _publish(store,entry,b'EXPOSED')
    completed = _complete(store,entry)
    parent = project_attempt_cost_work(definition.parent_contact)
    projection = project_native_cost_work(completed,roster=store.read_roster(definition.parent_contact),
        parent_scope_id=parent['work'].scope_id,coverage=CostCoverage.EXCLUSIVE)
    evidence = {row.evidence_id:row for row in (*parent['evidence'],*projection['evidence'])}
    account = WorkCostAccount('exposed.native-costs','Original exposed nested software fixture.',
        tuple(sorted(evidence.values(),key=lambda row:row.evidence_id)),
        tuple(sorted((parent['work'],projection['work']),key=lambda row:row.scope_id)),projection['measurements'])
    sources = {**parent['evidence_bytes'],**projection['evidence_bytes']}
    report = validate_work_cost_evidence(account=account,evidence_bytes=sources)
    assert report['quantities']['CPU_SECONDS']['value'] is None
    assert report['quantities']['ELAPSED_SECONDS']['value'] is None
    assert report['quantities']['ELAPSED_SECONDS']['component_observations'][0]['value'] == D('2.500')
    assert store.recover(definition) == completed
    # Removing original roster custody cannot turn the declaration into entered work.
    roster_id = next(row.evidence_id for row in projection['evidence'] if row.record_identity.object_schema.endswith('/native-subwork-roster'))
    changed = replace(projection['work'],witness_evidence_ids=tuple(value for value in projection['work'].witness_evidence_ids if value != roster_id))
    with pytest.raises(ValueError,match='original entered roster'):
        validate_work_cost_evidence(account=replace(account,work=tuple(changed if row.scope_id == changed.scope_id else row for row in account.work)),evidence_bytes=sources)
    assert canonical_json_bytes(report)
