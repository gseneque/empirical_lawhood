# SPDX-License-Identifier: MPL-2.0
"""Check the pinned upstream parser and REST v2 route without provider contact."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import socket
from unittest.mock import patch


def check(task_path):
    from empirical_lawhood.execution.remote.accelerated_controller import SKYPILOT_COMMIT, RUNPOD_ACCELERATOR_MEMORY_GB
    from empirical_lawhood.adapters.cloud.skypilot_installation import verify_controller_installation
    identity = verify_controller_installation()
    # A failed unexpected network dependency is a refusal, not a cloud check.
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('offline control attempted network contact')):
        import sky
        from sky.adaptors import runpod
        from sky.provision.runpod import utils
        assert sky._get_git_commit() == SKYPILOT_COMMIT
        task = sky.Task.from_yaml(str(task_path))
        assert task.num_nodes == 1
        resource, = task.resources
        assert not resource.use_spot and len(resource.accelerators) == 1
        accelerator, count = next(iter(resource.accelerators.items()))
        assert accelerator in RUNPOD_ACCELERATOR_MEMORY_GB and count == 1
        gpu_id = utils.GPU_NAME_MAP[accelerator]
        assert resource.image_id
        calls = []

        def request(method, path, **kwargs):
            calls.append((method, path, kwargs))
            if (method, path) == ('GET', '/catalog/gpus/'+runpod.path_segment(gpu_id)):
                return {'memory': RUNPOD_ACCELERATOR_MEMORY_GB[accelerator]}
            assert (method, path) == ('POST', '/pods')
            return {'id': 'EXPOSED-NONEXISTENT-POD'}

        with patch.object(runpod, 'rest_request', side_effect=request), patch.object(
                utils.runpod_commands, 'create_spot_pod', side_effect=AssertionError('unexpected legacy spot route')):
            returned = utils.launch(cluster_name='el-exposed-control', node_type='head',
                instance_type='1x_'+accelerator+'_SECURE', region='CA', zone='CA-MTL-1', disk_size=40,
                image_name='example.invalid/control@sha256:'+'1'*64, ports=[],
                public_key='ssh-ed25519 EXPOSED-NONKEY', preemptible=False, bid_per_gpu=0,
                docker_login_config=None, network_volume_id='EXPOSED-NONEXISTENT-VOLUME',
                volume_mount_path='/el-persistent')
        assert returned == 'EXPOSED-NONEXISTENT-POD' and len(calls) == 2
        body = calls[-1][2]['json']
        assert body['gpu']['count'] == 1 and body['cloud'] == 'SECURE'
        assert body['gpu']['id'] == gpu_id
        assert body['mounts'] == {'network': [{'volumeId': 'EXPOSED-NONEXISTENT-VOLUME', 'path': '/el-persistent'}]}
        assert body['dataCenterIds'] == ['CA-MTL-1']
        with patch.object(runpod, '_get_api_key', return_value='EXPOSED-NONKEY'), patch.object(
                runpod.requests, 'request', side_effect=OSError('EXPOSED LOST RESPONSE')) as send:
            try:
                runpod.rest_request('POST', '/pods', json={})
            except runpod.RunPodRestError:
                pass
            else:
                raise AssertionError('lost POST response must refuse')
            assert send.call_count == 1
            assert send.call_args.args[:2] == ('POST', 'https://api.runpod.io/v2/pods')
        with patch.object(runpod, 'rest_request', side_effect=[
                {'pods': [{'id': 'exposed-1'}], 'pagination': {'hasNextPage': True, 'nextCursor': 'cursor-2'}},
                {'pods': [{'id': 'exposed-2'}], 'pagination': {'hasNextPage': False}},
        ]) as pages:
            assert runpod.rest_list('/pods', 'pods') == [{'id': 'exposed-1'}, {'id': 'exposed-2'}]
            assert pages.call_args.kwargs == {'params': {'cursor': 'cursor-2'}}
        compact = {'id': 'exposed-running', 'name': 'el-exposed-control-head',
            'status': 'RUNNING', 'runtime': None, 'ssh': {'direct': None}, 'gpu': {'vcpuCount': 8}}
        detail = {**compact, 'ssh': {'direct': {'host': '192.0.2.1', 'port': 22000}}}
        with patch.object(utils, '_list_pods', return_value=[compact]), patch.object(
                runpod, 'rest_request', return_value=detail) as lookup:
            observed = utils.list_instances()['exposed-running']
            assert observed.get('ssh_port') == 22000, 'RUNNING list rows require same-pod SSH detail lookup'
            assert observed['external_ip'] == '192.0.2.1'
            lookup.assert_called_once_with('GET', '/pods/exposed-running')
        with patch.object(utils, '_list_pods', return_value=[detail]), patch.object(
                runpod, 'rest_request', side_effect=AssertionError('ready row needs no extra lookup')):
            assert utils.list_instances()['exposed-running']['ssh_port'] == 22000
        with patch.object(utils, '_list_pods', return_value=[{**compact, 'status': 'PROVISIONING'}]), patch.object(
                runpod, 'rest_request', side_effect=AssertionError('pending row needs no lookup')):
            assert utils.list_instances()['exposed-running']['status'] == 'PROVISIONING'
        with patch.object(utils, '_list_pods', return_value=[compact]), patch.object(
                runpod, 'rest_request', return_value={**detail, 'id': 'different-pod'}):
            try:
                utils.list_instances()
            except ValueError:
                pass
            else:
                raise AssertionError('a detail response must preserve the requested pod identity')
    return {'status': 'PASS', 'controller': identity, 'task_sha256': sha256(task_path.read_bytes()).hexdigest(),
        'accelerator': accelerator, 'provider_gpu_id': gpu_id,
        'checks': ['actual-upstream-task-parser', 'on-demand-rest-v2-pod', 'persistent-network-volume',
            'no-repeat-after-unknown-post', 'complete-cursor-pagination', 'same-pod-running-ssh-details',
            'already-ready-and-pending-no-extra-lookup', 'changed-pod-detail-refusal'],
        'actual_provider_contact': False, 'real_access_or_allocation_tested': False,
        'scientific_qualification': 'NOT_ESTABLISHED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--output-file', type=Path, required=True)
    args = parser.parse_args()
    result = check(args.task)
    with args.output_file.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
