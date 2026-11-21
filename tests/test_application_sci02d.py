# SPDX-License-Identifier: MPL-2.0
"""Disclosed read-dispatch controls; no trajectories or full-study fixture."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.api import matrix_sci02d as owner
from empirical_lawhood.api.application_contracts import ApplicationError
from empirical_lawhood.api.sci02d_workbench import sci02d_projection
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.status import OperationalStatus
from tests.test_application_workbench import context, request
from tests.test_matrix_sci02d_workflow import setup, campaign_fixture


def recorded_fixture(tmp_path, monkeypatch):
    from empirical_lawhood.api import matrix_native_read_custody, matrix_sci02
    from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import bindings, experiment, science, assessment, read
    design, selection, provenance, _ = setup(tmp_path)
    campaign = campaign_fixture()[0].campaign
    specification = experiment.BridgeSpecification('test.recorded.spec', design.identity, selection.identity,
        provenance.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign), 'TRAINING')
    roots = experiment.roots_for(selection, 'TRAINING')
    configs = bindings.configs(design, selection.identity, roots, provenance.identity, None)
    records, receipts = {}, {}
    for i, config in enumerate(configs):
        pin = ObjectIdentity('test.recorded.'+str(i), 'empirical-lawhood/testing/recorded', '1.0.0', 'a'*64)
        records[config.node_id] = SimpleNamespace(config=config, identity=pin, measurements=(), native=(),
            disposition='PARTIAL', reasons=('LITERAL_ADVERSE_CONTROL',), predecessors=(), fit=None)
        receipts[config.node_id] = SimpleNamespace(operational_status=OperationalStatus.SUCCEEDED,
            to_document=lambda: {'literal': 'disclosed-parent-receipt'})
    for record in records.values():
        record.predecessors = tuple(sorted((records[c.node_id].identity for c in bindings.parents_for(record.config).values()), key=lambda p:p.object_id))
    calls = []
    def source(_payloads, identity, _kind):
        return {design.identity:design, selection.identity:selection, provenance.identity:provenance}[identity]
    def arrays(writer, products, tasks, product):
        calls.append(product.config.phase)
        if product.config.phase == 'sample':
            pytest.fail('recorded inspection opened native positions/gradients for reconstruction')
        return {key:np.array([1.,2.]) for key in ('estimates','prefix_estimates','prefix_half_widths',
            'doubled_block_half_widths','five_node_estimates','kinetic_means','reconstruction_residuals')}
    def native(*args):
        return SimpleNamespace(definition=SimpleNamespace(identity=next(iter(records.values())).identity),
            completion=SimpleNamespace(to_document=lambda:{'literal':'completed-native'}),
            receipt=SimpleNamespace(to_document=lambda:{'literal':'native-receipt'}))
    def forbidden(*args, **kwargs):
        raise RuntimeError('independent reconstruction selected')
    monkeypatch.setattr(matrix_sci02, '_source_record', source)
    monkeypatch.setattr(matrix_native_read_custody, '_record', lambda products,tasks,run,node,kind:records[node])
    monkeypatch.setattr(owner, 'values', arrays)
    monkeypatch.setattr(owner, '_native_custody', native)
    for module, name in ((science,'controls'),(science,'fit'),(science,'confirm'),(assessment,'assess'),(read,'check_fit')):
        monkeypatch.setattr(module, name, forbidden)
    kwargs = dict(directory=tmp_path, artifact_writer=object(), specification=specification,
        instance=SimpleNamespace(specification=specification.identity), payloads={}, report={'run_id':'test.run'},
        products={'receipts':receipts}, draft=SimpleNamespace(selected_operation_ids=tuple(c.node_id for c in configs)),
        plan=SimpleNamespace(source_plan=SimpleNamespace(object_id='test.run'), tasks=tuple(SimpleNamespace(task_id=c.node_id) for c in configs)))
    return kwargs, records, calls


def test_recorded_view_keeps_adverse_units_and_native_custody_without_reconstruction(tmp_path, monkeypatch):
    kwargs, _, calls = recorded_fixture(tmp_path, monkeypatch)
    result = owner.read_recorded_result(**kwargs)
    assert result['scientific_completion'] == 'NOT_RECONSTRUCTED_BY_RECORDED_VIEW'
    assert result['assigned_roots'] == len(result['root_findings']) == 16
    assert all(r['state']=='RECORDED' and r['disposition']=='PARTIAL' for r in result['root_findings'])
    assert result['root_findings'][0]['native_custody']['completion'] == {'literal':'completed-native'}
    assert result['pooled_reasons'] == ['LITERAL_ADVERSE_CONTROL']
    assert result['qualification'] == 'NOT_ESTABLISHED'
    assert result['molecular_requirement']['status'] == 'OPEN'
    assert 'sample' not in calls
    with pytest.raises(RuntimeError, match='independent reconstruction selected'):
        owner.read_result(**kwargs)


def test_recorded_view_keeps_missing_roots_and_rejects_changed_predecessor(tmp_path, monkeypatch):
    kwargs, records, _ = recorded_fixture(tmp_path, monkeypatch)
    chosen = next(record for record in records.values() if record.config.phase=='assess')
    original = chosen.predecessors
    chosen.predecessors = ()
    with pytest.raises(PermissionError, match='predecessor custody'):
        owner.read_recorded_result(**kwargs)
    chosen.predecessors = original
    # A missing root remains in the denominator. Its dependent pooled receipt
    # cannot remain successful after removal of the original predecessor.
    kwargs['products']['receipts'].pop(chosen.config.node_id)
    pooled = next(record for record in records.values() if record.config.phase=='fit')
    kwargs['products']['receipts'].pop(pooled.config.node_id)
    result = owner.read_recorded_result(**kwargs)
    assert result['assigned_roots'] == len(result['root_findings']) == 16
    assert sum(row['state']=='UNKNOWN' for row in result['root_findings']) == 1
    assert result['state'] == 'RECORDED_PRODUCTS_INCOMPLETE'


def test_recorded_projection_keeps_complete_banks_exact_values_and_scope():
    from decimal import Decimal
    from empirical_lawhood.api.application_contracts import application_result, load_application_json, response_bytes
    report = dict(run_id='original', status='SUCCEEDED', task_count=145, new_native_contact_count=0,
        **{key:'a'*64 for key in ('packet_sha256','draft_sha256','execution_plan_sha256','producing_code_sha256',
            'dependency_lock_sha256','observed_producing_git_head','producing_provenance_sha256')})
    rows = [{'root':'r1','bank':'CONFIRMATION','disposition':'PARTIAL','estimate':Decimal('0.1234567890123456789')},
        {'root':'r2','bank':'REFERENCE','disposition':'UNKNOWN'}]
    report['scientific_result'] = dict(read_scope='AUTHENTICATED_HISTORICAL_SCI02D_FINDINGS',root_findings=rows,
        assigned_roots=2,tranche='CONFIRMATION',scientific_completion='NOT_RECONSTRUCTED_BY_RECORDED_VIEW',
        qualification='NOT_ESTABLISHED',equilibrium_state_coverage='NOT_ESTABLISHED',molecular_requirement={'status':'OPEN'},
        original_completed_native_contacts=2,design={'literal':'design'},selection={'literal':'selection'},cost_components={},
        cost_scope='Do not sum overlapping windows.',read_cpu_seconds=1.,read_wall_seconds=2.)
    result = sci02d_projection(report,request=request('sci02d.findings'),parameters={'filter':'PARTIAL','limit':1})
    assert result['page']['total'] == 2 and result['page']['matching_total'] == 1
    assert result['summary']['bank_census'] == {'CONFIRMATION':1,'REFERENCE':1}
    assert result['summary']['recorded_dispositions'] == {'PARTIAL':1,'UNKNOWN':1}
    assert result['page']['rows'][0]['estimate'] == rows[0]['estimate']
    assert result['summary']['claim_assessment'] == 'NOT_SUPPLIED_BY_THIS_WAVE_READ'
    encoded = load_application_json(response_bytes(application_result('sci02d.findings', result)))
    assert encoded['payload']['costs']['this_read_cpu_seconds'] == {'decimal':'1'}
    report['scientific_result']['read_scope'] = 'FULL_READ'
    with pytest.raises(ValueError):
        sci02d_projection(report,request=request('sci02d.findings'),parameters={})


def test_binary64_transport_preserves_exact_finite_values_and_nonfinite_bits():
    from decimal import Decimal
    import struct
    from empirical_lawhood.api.sci02d_workbench import _exact_values
    values = [0.1, -0.0, float('inf'), struct.unpack('!d', bytes.fromhex('7ff8000000000001'))[0]]
    result = _exact_values({'arrays':values, 'threshold':Decimal('0.100000000000000000000001')})
    assert result['arrays'][0] == Decimal.from_float(0.1)
    assert result['arrays'][1].is_signed()
    assert result['arrays'][2] == {'binary64_bits':'7ff0000000000000'}
    assert result['arrays'][3] == {'binary64_bits':'7ff8000000000001'}
    assert result['threshold'] == Decimal('0.100000000000000000000001')


def test_sci02d_dispatch_requires_exact_family_and_keeps_full_read_explicit(monkeypatch):
    from empirical_lawhood.api import application, experiment_scientific_read, sci02d_workbench
    from empirical_lawhood.api.application_operations import application_operation
    from pathlib import Path
    monkeypatch.setattr(experiment_scientific_read,'_development_runtime_context',lambda **kwargs:(None,object(),None))
    with pytest.raises(ApplicationError,match='original SCI02-D'):
        sci02d_workbench._selected_context({}, object())
    selected=[]
    monkeypatch.setattr(application,'application_storage',lambda c:(None,None,'plane'))
    def read(**kwargs):
        selected.append(kwargs)
        return {'original':'complete-full-report'}
    monkeypatch.setattr(sci02d_workbench,'read_sci02d',read)
    full = application.execute_application(context(),request('sci02d.assess',directory='/original'))
    assert full.succeeded and full.payload == {'original':'complete-full-report'}
    assert selected[0]['reconstruct'] is True
    denied = application.execute_application(replace(context(),read_access_paths=(Path('/unrelated/access'),)),
        request('sci02d.assess',directory='/original'))
    assert not denied.succeeded and len(selected)==1
    assert all(application_operation(key).lifecycle=='DURABLE_READ' for key in ('sci02d.findings','sci02d.assess'))
