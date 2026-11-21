# SPDX-License-Identifier: MPL-2.0
"""Offline monetary/lifecycle controls; test records grant no real cloud authority."""

from dataclasses import replace
from decimal import localcontext
from hashlib import sha256
import errno
import io
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest

from empirical_lawhood.adapters.cloud.skypilot_controller_action import require_cluster_identity
from empirical_lawhood.execution.remote import deployment_supervision as supervision
from empirical_lawhood.execution.local.bounded_process import BoundedProcessResult
from empirical_lawhood.execution.remote.deployment_supervision import SupervisionSelection
from empirical_lawhood.api.accelerated_deployment import supervise_deployment
from empirical_lawhood.adapters.cloud.runpod_budget import RunpodBudgetObserver
from empirical_lawhood.adapters.cloud import runpod_budget as cloud_observation, skypilot_budget as cloud_actions
from empirical_lawhood.execution.deployment_budget import DeploymentAllocation, DeploymentBudget, account_deployment


def allocation():
    return DeploymentAllocation('exposed-control', 'exposed-cluster', 'generation-1', 'pod-1',
        'exposed-cluster-head', 'volume-1', '/persistent', 'TEST-1',
        '2026-01-01T00:00:00+00:00', '2026-01-01T00:30:00+00:00',
        DeploymentBudget('80', '10', '1', '0.5', '3.99', '0.01', '0.03'))


def selection(tmp_path):
    a = allocation()
    authority = {'status': 'OWNER_AUTHORIZED', 'deployment_id': a.deployment_id,
        'budget_total_usd': '80', 'return_reserve_usd': '10', 'retirement_margin_usd': '1',
        'maximum_compute_hourly_usd': '3.99', 'keep_volume_id': a.volume_id, 'zone': a.zone,
        'financial_actions': ['CANCEL_SELECTED_JOBS', 'RETIRE_SELECTED_COMPUTE_KEEP_VOLUME'],
        'evidence_role': 'EXPOSED_SOFTWARE_CONTROL_ONLY'}
    auth = tmp_path/'exposed-authority.json'
    auth.write_text(json.dumps(authority))
    doc = {'version': '1.0.0', 'allocation': a.to_document(), 'authorization_path': str(auth),
        'authorization_sha256': sha256(auth.read_bytes()).hexdigest(),
        'controller_python': '/nonexecuting/python', 'controller_source_paths': ['/nonexecuting/source'],
        'controller_config': '/nonexecuting/config'}
    path = tmp_path/'selection.json'
    path.write_text(json.dumps(doc))
    return path, SupervisionSelection.read(path)


def test_per_resource_maximum_hour_buckets_prior_attempts_and_ambient_precision():
    with localcontext() as context:
        context.prec = 2
        result = account_deployment(allocation(), observed_utc='2026-01-01T01:00:00.000001+00:00',
            pod_billed_usd='5', volume_billed_usd='0')
    # Pod provider billing exceeds elapsed; volume billing lags across two buckets.
    assert result['accounted_usd'] == '5.560000000000'
    assert result['volume_billing_hours_upper'] == 2
    assert result['native_deadline'] is None
    result = account_deployment(allocation(), observed_utc='2026-01-01T01:00:01+00:00',
        pod_billed_usd='0', volume_billed_usd='0', previous_accounted_usd='69.9999999999999')
    assert result['accounted_usd'] == '70.000000000000'
    assert result['status'] == 'CONTINUE'  # Exact unrounded comparison owns the decision.


@pytest.mark.parametrize('billing,expected', [('69.47', 'STOP_SCIENCE_RETURN_ONLY'),
    ('78.47', 'RETIRE_COMPUTE'), ('80', 'RETIRE_COMPUTE')])
def test_exact_financial_boundaries_leave_shutdown_margin(billing, expected):
    result = account_deployment(allocation(), observed_utc='2026-01-01T01:00:00+00:00',
        pod_billed_usd=billing, volume_billed_usd='0')
    assert result['status'] == expected
    assert result['science_stop_usd'] == '70.000000000000'
    assert result['retirement_threshold_usd'] == '79.000000000000'


@pytest.mark.parametrize('bad', ['NaN', 'Infinity', '-1', 3.99, '1e10000'])
def test_invalid_money_refuses(bad):
    with pytest.raises(ValueError):
        replace(allocation().budget, total_usd=bad)


def test_latency_reserve_and_future_start_refuse():
    with pytest.raises(ValueError, match='latency'):
        replace(allocation().budget, retirement_margin_usd='0.001')
    with pytest.raises(ValueError, match='precedes'):
        account_deployment(allocation(), observed_utc='2025-01-01T00:00:00+00:00',
            pod_billed_usd='0', volume_billed_usd='0')


def test_budget_amendment_keeps_accounting_floor_without_double_counting():
    selected = replace(allocation(), budget=replace(allocation().budget, accounting_floor_usd='38.1234567890123'))
    result = account_deployment(selected, observed_utc='2026-01-01T01:00:00+00:00',
        pod_billed_usd='30', volume_billed_usd='0')
    assert result['accounted_usd'] == '38.123456789013'


class Observer:
    def __init__(self, values):
        self.values = iter(values)
    def observe(self, output):
        value = next(self.values)
        if isinstance(value, Exception):
            raise value
        return value


class Actions:
    def __init__(self, *, fail=False):
        self.calls, self.fail = [], fail
    def act(self, action, output):
        self.calls.append(action)
        output.write_text('EXPOSED NO-CLOUD ACTION\n')
        if self.fail:
            raise RuntimeError('exposed upstream failure')


def observed(billing):
    return {'status': 'OBSERVED', 'observed_utc': '2026-01-01T01:00:00+00:00',
        'pod_billed_usd': billing, 'volume_billed_usd': '0'}


def test_cancel_once_continue_return_then_verify_compute_absent_and_volume_retained(tmp_path):
    path, _ = selection(tmp_path)
    observer = Observer([observed('69.47'), observed('1'), observed('78.47'),
        {'status': 'COMPUTE_ABSENT_VOLUME_RETAINED'}])
    actions = Actions()
    result = supervise_deployment(path, output_directory=tmp_path/'watch', observer=observer,
        actions=actions, sleep=lambda _: None, emit=lambda _: None)
    assert actions.calls == ['cancel', 'retire']
    assert result['status'] == 'COMPUTE_ABSENT_VOLUME_RETAINED'
    events = [json.loads(line) for line in (tmp_path/'watch/events.jsonl').read_text().splitlines()]
    assert all(row['native_work_dispatched'] is False and row['automatic_replay'] is False for row in events)
    assert sum(row['status'] == 'FINANCIAL_CANCELLATION_RETURNED' for row in events) == 1
    assert (tmp_path/'watch/original-authorization.json').is_file()


@pytest.mark.parametrize('failure', ['observe', 'cancel', 'retire', 'still-present'])
def test_failure_never_reports_retirement_from_command_success_alone(tmp_path, failure):
    path, _ = selection(tmp_path)
    actions = Actions(fail=failure in ('cancel', 'retire'))
    inputs = ([ValueError('missing billing')] if failure == 'observe' else
        [observed('69.47' if failure == 'cancel' else '78.47')])
    inputs.append({'status': 'COMPUTE_ABSENT_VOLUME_RETAINED'} if failure == 'observe' else observed('78.47'))
    kwargs = dict(output_directory=tmp_path/'watch', observer=Observer(inputs), actions=actions,
        sleep=lambda _: None, emit=lambda _: None)
    if failure == 'observe':
        assert supervise_deployment(path, **kwargs)['status'] == 'COMPUTE_ABSENT_VOLUME_RETAINED'
    else:
        with pytest.raises(RuntimeError, match='unresolved'):
            supervise_deployment(path, **kwargs)
        assert json.loads((tmp_path/'watch/latest.json').read_text())['status'] == 'RETIREMENT_UNRESOLVED'
    assert actions.calls[-1] == 'retire'


def test_authorization_change_refuses_before_any_action(tmp_path):
    path, selected = selection(tmp_path)
    Path(selected.authorization_path).write_text('{}')
    actions = Actions()
    with pytest.raises(ValueError, match='authorization changed'):
        supervise_deployment(path, output_directory=tmp_path/'watch', actions=actions)
    assert not actions.calls and not (tmp_path/'watch').exists()


def test_provider_get_is_filtered_bounded_and_preserves_originals_without_token(tmp_path):
    _, selected = selection(tmp_path)
    requests = []
    pod = dict(id='pod-1', name='exposed-cluster-head', dataCenterId='TEST-1', cost='3.99',
        mounts={'network': [dict(path='/persistent', volumeId='volume-1')]})
    def opener(request, timeout):
        requests.append((request.get_method(), request.full_url, timeout))
        data = pod if '/pods/pod-1' in request.full_url else {'metadata': {'totals': {'totalAmount': '0.2'}}}
        return io.BytesIO(json.dumps(data).encode())
    result = RunpodBudgetObserver(selected, credential='EXPOSED-TEST-TOKEN', opener=opener).observe(tmp_path)
    assert result['pod_billed_usd'] == '0.2'
    assert all(method == 'GET' and timeout == 20 for method, _, timeout in requests)
    assert 'podId=pod-1' in requests[1][1] and 'networkVolumeId=volume-1' in requests[2][1]
    assert all(b'EXPOSED-TEST-TOKEN' not in path.read_bytes() for path in tmp_path.glob('*billing.json'))


@pytest.mark.parametrize('damage', ['pod-id', 'name', 'price', 'zone', 'volume'])
def test_provider_identity_changes_refuse_before_billing(tmp_path, damage):
    _, selected = selection(tmp_path)
    pod = dict(id='pod-1', name='exposed-cluster-head', dataCenterId='TEST-1', cost='3.99',
        mounts={'network': [dict(path='/persistent', volumeId='volume-1')]})
    key = {'pod-id': 'id', 'name': 'name', 'price': 'cost', 'zone': 'dataCenterId', 'volume': 'mounts'}[damage]
    pod[key] = '4.00' if damage == 'price' else {'network': []} if damage == 'volume' else 'other'
    with pytest.raises(ValueError, match='changed'):
        RunpodBudgetObserver(selected, credential='EXPOSED',
            opener=lambda *a, **k: io.BytesIO(json.dumps(pod).encode())).observe(tmp_path)
    assert not (tmp_path/'pod-billing.json').exists()


def test_absent_pod_does_not_imply_volume_survival(tmp_path):
    _, selected = selection(tmp_path)
    def opener(request, **kwargs):
        raise HTTPError(request.full_url, 404, 'exposed absence', {}, None)
    with pytest.raises(RuntimeError, match='HTTP 404'):
        RunpodBudgetObserver(selected, credential='EXPOSED', opener=opener).observe(tmp_path)


def test_retirement_postcondition_uses_actual_rest_v2_volume_resource_shape(tmp_path):
    _, selected = selection(tmp_path)
    def opener(request, **kwargs):
        if request.full_url == 'https://api.runpod.io/v2/pods/pod-1':
            raise HTTPError(request.full_url, 404, 'exposed absence', {}, None)
        assert request.full_url == 'https://api.runpod.io/v2/network-volumes/volume-1'
        return io.BytesIO(json.dumps({'id': 'volume-1', 'dataCenter': 'TEST-1', 'size': 256,
            'name': 'exposed-volume', 'tags': [], 'type': 'STANDARD'}).encode())
    result = RunpodBudgetObserver(selected, credential='EXPOSED', opener=opener).observe(tmp_path)
    assert result['status'] == 'COMPUTE_ABSENT_VOLUME_RETAINED'


@pytest.mark.parametrize('damage', ['generation', 'pod', 'cloud', 'name', 'node', 'extra-pod',
    'extra-node', 'head', 'missing-info', None])
def test_upstream_lifecycle_refuses_changed_cluster_generation_or_foreign_pod(tmp_path, damage):
    _, selected = selection(tmp_path)
    info = SimpleNamespace(head_instance_id='pod-1',
        instances={'pod-1': [SimpleNamespace(instance_id='pod-1')]})
    handle = SimpleNamespace(instance_ids=['pod-1-0'], cached_cluster_info=info,
        launched_resources=SimpleNamespace(cloud='RunPod'))
    record = dict(name='exposed-cluster', cluster_hash='generation-1', handle=handle)
    if damage == 'generation': record['cluster_hash'] = 'replacement'
    if damage == 'name': record['name'] = 'foreign'
    if damage == 'pod': info.instances['pod-1'][0].instance_id = 'replacement'
    if damage == 'node': handle.instance_ids = ['pod-1']
    if damage == 'extra-pod': info.instances['replacement'] = [SimpleNamespace(instance_id='replacement')]
    if damage == 'extra-node': info.instances['pod-1'].append(SimpleNamespace(instance_id='pod-1'))
    if damage == 'head': info.head_instance_id = 'replacement'
    if damage == 'missing-info': handle.cached_cluster_info = None
    if damage == 'cloud': handle.launched_resources.cloud = 'aws'
    if damage:
        with pytest.raises(ValueError, match='cluster'):
            require_cluster_identity(selected, record)
    else:
        require_cluster_identity(selected, record)


def test_controller_helper_import_requires_no_scientific_or_provider_dependencies():
    from empirical_lawhood.adapters.cloud import skypilot_controller_action as deployment_controller_action
    source_root = Path(deployment_controller_action.__file__).resolve().parents[3]
    code = '''import builtins, sys
sys.path.insert(0, sys.argv[1])
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in ('pyarrow','numpy','scipy','cupy','openmm','sky','runpod'):
        raise RuntimeError('thin controller imported an unrelated dependency: '+name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from empirical_lawhood.adapters.cloud.skypilot_controller_action import require_cluster_identity
'''
    result = subprocess.run([sys.executable, '-I', '-c', code, str(source_root)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


class RetirementObserver:
    """Offline allocation with independently observed retirement postconditions."""

    def __init__(self, confirmation='COMPUTE_ABSENT_VOLUME_RETAINED'):
        self.confirmation = confirmation
        self.calls = []

    def observe(self, output):
        self.calls.append(output.name)
        if output.name.startswith('retirement-'):
            return {'status': self.confirmation}
        return observed('80')


def offline_controller(monkeypatch, *, returncode=0):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        # Exercise the production action's original-byte pin, without importing
        # a provider or granting these exposed records real cloud authority.
        source = Path(command[command.index('--selection') + 1])
        assert sha256(source.read_bytes()).hexdigest() == command[command.index('--expected-selection-sha256') + 1]
        return BoundedProcessResult(returncode, b'EXPOSED CONTROLLER RETURN\n', b'')

    monkeypatch.setattr(cloud_actions, 'run_bounded_command', run)
    return calls


@pytest.mark.parametrize('failure_errno', [errno.ENOSPC, errno.EROFS, errno.EIO])
@pytest.mark.parametrize('boundary', ['initial-directory', 'selection-copy', 'observation-directory',
                                     'event-journal', 'latest-record', 'action-log'])
def test_evidence_storage_failure_cannot_prevent_authorized_retirement(tmp_path, monkeypatch, failure_errno, boundary):
    path, selected = selection(tmp_path)
    calls = offline_controller(monkeypatch)
    actions = cloud_actions.SkyPilotBudgetActions(selected, path)
    output = tmp_path/'watch'
    mkdir, open_file, durable = Path.mkdir, Path.open, supervision._durable_bytes

    def fail():
        raise OSError(failure_errno, 'EXPOSED evidence storage failure')

    def guarded_mkdir(target, *args, **kwargs):
        if (boundary == 'initial-directory' and target == output
                or boundary == 'observation-directory' and target.name.startswith('observation-')):
            fail()
        return mkdir(target, *args, **kwargs)

    def guarded_open(target, *args, **kwargs):
        if boundary == 'event-journal' and target == output/'events.jsonl':
            fail()
        return open_file(target, *args, **kwargs)

    def guarded_durable(target, raw):
        if ((boundary == 'selection-copy' and target == output/'selection.json')
                or (boundary == 'latest-record' and target == output/'latest.pending.json')
                or (boundary == 'action-log' and target.name == 'retire.log')):
            fail()
        return durable(target, raw)

    monkeypatch.setattr(Path, 'mkdir', guarded_mkdir)
    monkeypatch.setattr(Path, 'open', guarded_open)
    monkeypatch.setattr(supervision, '_durable_bytes', guarded_durable)
    monkeypatch.setattr(cloud_actions, '_durable_bytes', guarded_durable)
    monkeypatch.setattr(cloud_observation, '_durable_bytes', guarded_durable)
    emitted = []
    kwargs = dict(output_directory=output, observer=RetirementObserver(), actions=actions,
        sleep=lambda _: pytest.fail('storage failure must retire immediately'), emit=emitted.append)
    if boundary in ('initial-directory', 'event-journal', 'latest-record'):
        with pytest.raises(RuntimeError, match='retirement is unresolved'):
            supervise_deployment(path, **kwargs)
        assert emitted[-1]['status'] == 'RETIREMENT_UNRESOLVED'
        assert not any(row['status'] == 'COMPUTE_ABSENT_VOLUME_RETAINED' for row in emitted)
    else:
        result = supervise_deployment(path, **kwargs)
        assert result['status'] == 'COMPUTE_ABSENT_VOLUME_RETAINED'
        if boundary == 'action-log':
            assert result['retirement_action']['action_log'] == 'UNAVAILABLE'
    assert len(calls) == 1
    command, options = calls[0]
    assert command[command.index('--action') + 1] == 'retire'
    assert command[command.index('--selection') + 1] == str(path)
    assert options['timeout_seconds'] == selected.allocation.budget.action_timeout_seconds
    assert options['maximum_stdout_bytes'] == options['maximum_stderr_bytes'] == 2**20
    assert all(row['keep_volume_id'] == selected.allocation.volume_id for row in emitted)


@pytest.mark.parametrize('failure', ['controller-return', 'confirmation', 'event-consumer'])
def test_emergency_failure_never_infers_financial_closure(tmp_path, monkeypatch, failure):
    path, selected = selection(tmp_path)
    calls = offline_controller(monkeypatch, returncode=1 if failure == 'controller-return' else 0)
    durable = supervision._durable_bytes

    def no_log(target, raw):
        if target.name == 'retire.log':
            raise OSError(errno.ENOSPC, 'EXPOSED unavailable action log')
        return durable(target, raw)

    monkeypatch.setattr(supervision, '_durable_bytes', no_log)
    monkeypatch.setattr(cloud_actions, '_durable_bytes', no_log)
    monkeypatch.setattr(cloud_observation, '_durable_bytes', no_log)
    monkeypatch.setattr(cloud_actions, '_durable_bytes', no_log)
    monkeypatch.setattr(cloud_observation, '_durable_bytes', no_log)
    emitted = []

    def emit(value):
        if failure == 'event-consumer':
            raise BrokenPipeError('EXPOSED closed consumer')
        emitted.append(value)

    observer = RetirementObserver('OBSERVED' if failure == 'confirmation' else 'COMPUTE_ABSENT_VOLUME_RETAINED')
    with pytest.raises(RuntimeError, match='retirement is unresolved'):
        supervise_deployment(path, output_directory=tmp_path/'watch', observer=observer,
            actions=cloud_actions.SkyPilotBudgetActions(selected, path), emit=emit, sleep=lambda _: None)
    assert len(calls) == 1
    if failure != 'event-consumer':
        assert emitted[-1]['status'] == 'RETIREMENT_UNRESOLVED'
        assert not any(row['status'] == 'COMPUTE_ABSENT_VOLUME_RETAINED' for row in emitted)


@pytest.mark.parametrize('changed', ['selection', 'authorization', 'missing-authorization'])
def test_emergency_retirement_preserves_live_selection_and_authority_checks(tmp_path, monkeypatch, changed):
    path, selected = selection(tmp_path)
    calls = offline_controller(monkeypatch)
    actions = cloud_actions.SkyPilotBudgetActions(selected, path)

    class ChangingObserver:
        def observe(self, output):
            if changed == 'selection':
                path.write_text(path.read_text() + '\n')
            elif changed == 'authorization':
                Path(selected.authorization_path).write_text('{}')
            else:
                Path(selected.authorization_path).unlink()
            raise OSError(errno.ENOSPC, 'EXPOSED observation failure')

    emitted = []
    with pytest.raises(RuntimeError, match='retirement is unresolved'):
        supervise_deployment(path, output_directory=tmp_path/'watch', observer=ChangingObserver(),
            actions=actions, emit=emitted.append, sleep=lambda _: None)
    assert calls == []
    assert emitted[-1]['status'] == 'RETIREMENT_UNRESOLVED'


def test_controller_refuses_selection_changed_after_parent_action_check(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.cloud import skypilot_controller_action as controller

    path, _ = selection(tmp_path)
    digest = sha256(path.read_bytes()).hexdigest()
    path.write_text(path.read_text() + '\n')
    monkeypatch.setattr(controller, 'verify_controller_installation',
        lambda: pytest.fail('changed selection must refuse before provider initialization'))
    with pytest.raises(ValueError, match='original supervision selection bytes'):
        controller.act(path, 'retire', expected_selection_sha256=digest)


def test_lost_cancellation_log_retires_without_repeating_cancellation(tmp_path, monkeypatch):
    path, selected = selection(tmp_path)
    calls = offline_controller(monkeypatch)
    durable = supervision._durable_bytes

    def no_log(target, raw):
        if target.name in ('cancel.log', 'retire.log'):
            raise OSError(errno.ENOSPC, 'EXPOSED full action-log storage')
        return durable(target, raw)

    monkeypatch.setattr(supervision, '_durable_bytes', no_log)
    monkeypatch.setattr(cloud_actions, '_durable_bytes', no_log)
    monkeypatch.setattr(cloud_observation, '_durable_bytes', no_log)
    monkeypatch.setattr(cloud_actions, '_durable_bytes', no_log)
    monkeypatch.setattr(cloud_observation, '_durable_bytes', no_log)
    result = supervise_deployment(path, output_directory=tmp_path/'watch',
        observer=Observer([observed('69.47'), {'status': 'COMPUTE_ABSENT_VOLUME_RETAINED'}]),
        actions=cloud_actions.SkyPilotBudgetActions(selected, path), emit=lambda _: None,
        sleep=lambda _: pytest.fail('lost action evidence must not continue paid work'))
    assert [command[command.index('--action')+1] for command, _ in calls] == ['cancel', 'retire']
    assert result['status'] == 'COMPUTE_ABSENT_VOLUME_RETAINED'
    assert result['retirement_action']['action_log'] == 'UNAVAILABLE'


def test_storage_loss_during_provider_confirmation_remains_unresolved(tmp_path, monkeypatch):
    path, selected = selection(tmp_path)
    calls = offline_controller(monkeypatch)
    durable = supervision._durable_bytes

    def missing_provider_storage(target, raw):
        if target.name == 'pod.json':
            raise OSError(errno.EROFS, 'EXPOSED provider evidence storage unavailable')
        return durable(target, raw)

    monkeypatch.setattr(supervision, '_durable_bytes', missing_provider_storage)
    monkeypatch.setattr(cloud_actions, '_durable_bytes', missing_provider_storage)
    monkeypatch.setattr(cloud_observation, '_durable_bytes', missing_provider_storage)

    def opener(request, **kwargs):
        if calls:
            raise HTTPError(request.full_url, 404, 'EXPOSED absent pod', {}, None)
        return io.BytesIO(json.dumps(dict(id='pod-1', name='exposed-cluster-head', dataCenterId='TEST-1', cost='3.99',
            mounts={'network': [dict(path='/persistent', volumeId='volume-1')]})).encode())

    observer = RunpodBudgetObserver(selected, credential='EXPOSED', opener=opener)
    emitted = []
    with pytest.raises(RuntimeError, match='retirement is unresolved'):
        supervise_deployment(path, output_directory=tmp_path/'watch', observer=observer,
            actions=cloud_actions.SkyPilotBudgetActions(selected, path), emit=emitted.append,
            sleep=lambda _: pytest.fail('provider evidence failure must retire immediately'))
    assert len(calls) == 1
    assert emitted[-1]['status'] == 'RETIREMENT_UNRESOLVED'
    assert not any(row['status'] == 'COMPUTE_ABSENT_VOLUME_RETAINED' for row in emitted)
