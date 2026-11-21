# SPDX-License-Identifier: MPL-2.0
"""Native array limits and complete populations; no enzyme qualification."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import periodic_memory as owner


@pytest.mark.parametrize('resident,virtual,host,group,expected', (
    (950, 10, 2000, 2000, 50),
    (10, 975, 2000, 2000, 25),
    (10, 10, 30, 2000, 30),
    (10, 10, 2000, 40, 40),
))
def test_all_actual_memory_limits_constrain_the_block(monkeypatch, resident, virtual, host, group, expected):
    monkeypatch.setattr(owner, '_kilobyte_fields', lambda path:
        dict(VmRSS=resident, VmSize=virtual) if path.name == 'status' else dict(MemAvailable=host))
    monkeypatch.setattr(owner.resource, 'getrlimit', lambda _: (1000, 1000))
    monkeypatch.setattr(owner, '_cgroup_headrooms', lambda:
        [dict(path='exposed-parent', used_bytes=1000-group, limit_bytes=1000)])
    assert owner.memory_observation(.001)['available_bytes'] == expected


def test_changing_headroom_keeps_the_complete_population_and_refuses_before_omission(monkeypatch):
    observed = iter((120, 40, 80, 0))
    monkeypatch.setattr(owner, 'memory_observation', lambda _: dict(available_bytes=next(observed)))
    blocks = owner.memory_blocks(9, bytes_per_item=20, maximum_memory_mb=1)
    assert next(blocks) == (0, 3)
    assert next(blocks) == (3, 4)
    assert next(blocks) == (4, 6)
    with pytest.raises(MemoryError, match='one complete native array item'):
        next(blocks)


@pytest.mark.parametrize('version', (1, 2))
def test_cgroup_controller_reads_leaf_and_parent_limits(tmp_path, monkeypatch, version):
    mount = tmp_path / 'mounted'; leaf = mount / 'job'
    leaf.mkdir(parents=True)
    limit, used = ('memory.max', 'memory.current') if version == 2 else ('memory.limit_in_bytes', 'memory.usage_in_bytes')
    (mount / limit).write_text('1000'); (mount / used).write_text('750')
    (leaf / limit).write_text('800'); (leaf / used).write_text('100')
    stat_key = 'inactive_file' if version == 2 else 'total_inactive_file'
    (mount / 'memory.stat').write_text(stat_key + ' 50\n')
    actual = Path.read_text
    def read(path, *args, **kwargs):
        if str(path) == '/proc/self/cgroup':
            return '0::/job\n' if version == 2 else '7:memory:/job\n'
        if str(path) == '/proc/self/mountinfo':
            return (f'1 0 0:1 / {mount} rw - cgroup2 cgroup rw\n' if version == 2 else
                f'1 0 0:1 / {mount} rw - cgroup cgroup rw,memory\n')
        return actual(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', read)
    rows = owner._cgroup_headrooms()
    assert [(row['limit_bytes'], row['used_bytes']) for row in rows] == [(800, 100), (1000, 750)]
    assert [row['reclaimable_file_bytes'] for row in rows] == [0, 50]


def test_original_failed_tensor_shape_is_blocked_under_actual_rlimit_as(record_property):
    # The original full-enzyme failure requested this 1.77 GiB scalar tensor.
    # Keep the exact dimensions, with exposed deterministic values. The child
    # limit makes the original request fail and bounds every successful block.
    script = r'''
import importlib.util,json,resource,sys
import numpy as np
spec=importlib.util.spec_from_file_location('memory_pressure_owner',sys.argv[1])
owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
before=owner.memory_observation(6000)
limit=before['virtual_bytes']+192*1024**2
resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
count,nao=54,2095
try:
    original=np.empty((count,nao,nao),dtype=np.float64)
except MemoryError:
    refused=True
else:
    raise AssertionError('original oversized allocation unexpectedly fit')
total=0.;blocks=[]
for start,end in owner.memory_blocks(count,bytes_per_item=16*nao**2,
        maximum_memory_mb=6000,fixed_bytes=8*nao**2,max_items=200):
    block=np.empty((end-start,nao,nao),dtype=np.float64)
    block[:]=(np.arange(start,end,dtype=np.float64)+1)[:,None,None]
    total+=float(block.sum())
    blocks.append([start,end,int(block.nbytes)])
    del block
assert total==nao**2*count*(count+1)/2
assert [i for start,end,_ in blocks for i in range(start,end)]==list(range(count))
print(json.dumps(dict(original_allocation_refused=refused,original_bytes=count*nao**2*8,
    complete_items=count,blocks=blocks,total=total,limit_bytes=limit,
    maximum_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))
'''
    result = subprocess.run([sys.executable, '-c', script, str(Path(owner.__file__))],
        check=True, capture_output=True, text=True)
    evidence = json.loads(result.stdout)
    assert evidence['original_allocation_refused'] and evidence['complete_items'] == 54
    assert len(evidence['blocks']) > 1
    record_property('actual_allocation_pressure', evidence)


def test_combined_ram_and_swap_can_be_the_limiting_controller(tmp_path, monkeypatch):
    mount = tmp_path/'memory'; mount.mkdir()
    for name, value in {'memory.limit_in_bytes': 1000, 'memory.usage_in_bytes': 500,
            'memory.memsw.limit_in_bytes': 1100, 'memory.memsw.usage_in_bytes': 1050}.items():
        (mount/name).write_text(str(value))
    (mount/'memory.stat').write_text('total_inactive_file 10\n')
    actual = Path.read_text
    def read(path, *args, **kwargs):
        if str(path) == '/proc/self/cgroup':
            return '7:memory:/\n'
        if str(path) == '/proc/self/mountinfo':
            return f'1 0 0:1 / {mount} rw - cgroup cgroup rw,memory\n'
        return actual(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', read)
    monkeypatch.setattr(owner, '_kilobyte_fields', lambda path:
        dict(VmRSS=1, VmSize=1) if path.name == 'status' else dict(MemAvailable=1000))
    monkeypatch.setattr(owner.resource, 'getrlimit', lambda _: (1000, 1000))
    observed = owner.memory_observation(.001)
    assert observed['available_bytes'] == 60
    assert {row['controller'] for row in observed['cgroups']} == {
        'memory.limit_in_bytes', 'memory.memsw.limit_in_bytes'}


def test_grid_block_preserves_alignment_and_all_points_with_atomic_response(monkeypatch):
    monkeypatch.setattr(owner, 'memory_observation', lambda _: dict(available_bytes=400*2**20))
    rows = []
    block = owner.grid_block_size(19616, nao=2095, derivative=2, maximum_memory_mb=6000,
        alignment=56, response_atoms=152, observe=rows.append)
    assert 56 <= block < 19616 and block % 56 == 0
    assert rows[0]['simultaneous_bytes_per_point'] >= 3*152**2*8
    assert rows[0]['simultaneous_bytes_per_point'] >= 10*2095*8
    assert 2*block*rows[0]['simultaneous_bytes_per_point']+rows[0]['fixed_workspace_bytes'] <= 400*2**20
    assert owner.grid_block_size(111, nao=10, derivative=0, maximum_memory_mb=6000,
        alignment=56, requested_size=56) == 56
    assert owner.grid_block_size(29, nao=10, derivative=0, maximum_memory_mb=6000,
        alignment=56) == 56
    with pytest.raises(MemoryError, match='complete aligned DFT grid block'):
        owner.grid_block_size(1000, nao=2095, derivative=2, maximum_memory_mb=6000,
            alignment=56, working_memory_mb=1)
    with pytest.raises(ValueError, match='aligned requested blocks'):
        owner.grid_block_size(1000, nao=2095, derivative=2, maximum_memory_mb=6000,
            alignment=56, requested_size=57)


def test_complete_dft_grid_arrays_under_actual_address_space_pressure(record_property):
    script = r'''
import importlib.util,json,resource,sys
import numpy as np
spec=importlib.util.spec_from_file_location('grid_pressure_owner',sys.argv[1])
owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
before=owner.memory_observation(6000)
limit=before['virtual_bytes']+384*1024**2
resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
try:
    original=np.empty((10,19616,2095),dtype=np.float64)
except MemoryError:
    refused=True
else:
    raise AssertionError('original complete atomic AO allocation unexpectedly fit')
count=253;offset=0;blocks=[];ao_total=partition_total=0.
while offset<count:
    block=owner.grid_block_size(count-offset,nao=2095,derivative=2,
        maximum_memory_mb=6000,alignment=56,response_atoms=152)
    end=min(count,offset+block)
    partition=np.ones((152,152,3,end-offset),dtype=np.float64)
    partition_total+=float(partition.sum());del partition
    ao=np.ones((10,end-offset,2095),dtype=np.float64)
    ao_total+=float(ao.sum());del ao
    blocks.append([offset,end]);offset=end
assert partition_total==152**2*3*count
assert ao_total==10*2095*count
print(json.dumps(dict(original_allocation_refused=refused,limit_bytes=limit,
    original_ao_bytes=10*19616*2095*8,blocks=blocks,complete_points=count,
    ao_total=ao_total,partition_total=partition_total,
    maximum_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))
'''
    result = subprocess.run([sys.executable, '-c', script, str(Path(owner.__file__))],
        check=True, capture_output=True, text=True)
    evidence = json.loads(result.stdout)
    assert evidence['original_allocation_refused'] and evidence['complete_points'] == 253
    assert len(evidence['blocks']) > 1
    record_property('actual_dft_allocation_pressure', evidence)
