# SPDX-License-Identifier: MPL-2.0
"""Observe native array headroom without changing the selected process limits.

The supported native route is Linux. RSS, virtual address space and cgroup
memory are different limits. Inactive file cache can be reclaimed by Linux.
A block must fit all observed limits after that cache allowance. These
observations are estimates, not an allocation guarantee or scientific cutoff.
"""
from __future__ import annotations

import math
import re
import resource
from pathlib import Path


def _kilobyte_fields(path: Path) -> dict[str, int]:
    result = {}
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[2] == 'kB':
            result[fields[0].rstrip(':')] = int(fields[1]) * 1024
    return result


def _mount_path(value: str) -> Path:
    return Path(re.sub(r'\\([0-7]{3})', lambda match: chr(int(match[1], 8)), value))


def _cgroup_headrooms() -> list[dict[str, int | str]]:
    """Read the applicable v1/v2 memory controllers, including parent limits."""
    groups = []
    for line in Path('/proc/self/cgroup').read_text().splitlines():
        _, controllers, path = line.split(':', 2)
        if not controllers or 'memory' in controllers.split(','):
            groups.append((not controllers, Path(path)))
    result = []
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left, right = line.split(' - ', 1)
        fields, filesystem = left.split(), right.split()
        v2 = filesystem[0] == 'cgroup2'
        if not v2 and not (filesystem[0] == 'cgroup' and 'memory' in filesystem[2].split(',')):
            continue
        root, mount = _mount_path(fields[3]), _mount_path(fields[4])
        for selected_v2, group in groups:
            if selected_v2 != v2 or not group.is_relative_to(root):
                continue
            relative = group.relative_to(root)
            if '..' in relative.parts:
                continue
            directory = mount / relative
            while directory.is_relative_to(mount):
                controls = (('memory.max', 'memory.current'),) if v2 else (
                    ('memory.limit_in_bytes', 'memory.usage_in_bytes'),
                    ('memory.memsw.limit_in_bytes', 'memory.memsw.usage_in_bytes'))
                for limit_name, usage_name in controls:
                    limit_path, usage_path = directory / limit_name, directory / usage_name
                    if limit_path.is_file() and usage_path.is_file():
                        limit = limit_path.read_text().strip()
                        if limit != 'max':
                            statistics = directory / 'memory.stat'
                            counters = (dict(line.split() for line in statistics.read_text().splitlines())
                                if statistics.is_file() else {})
                            inactive = int(counters.get('inactive_file' if v2 else 'total_inactive_file',
                                counters.get('inactive_file', '0')))
                            used = int(usage_path.read_text())
                            result.append(dict(path=str(directory), controller=limit_name,
                                limit_bytes=int(limit), used_bytes=used,
                                reclaimable_file_bytes=min(used, max(0, inactive))))
                if directory == mount:
                    break
                directory = directory.parent
    return result


def memory_observation(maximum_memory_mb: float) -> dict:
    """Return the actual current process, address-space and memory headroom."""
    if (isinstance(maximum_memory_mb, bool) or not math.isfinite(maximum_memory_mb)
            or maximum_memory_mb <= 0):
        raise ValueError('native array budget requires positive finite memory in MB')
    process = _kilobyte_fields(Path('/proc/self/status'))
    resident, virtual = process['VmRSS'], process['VmSize']
    selected = int(maximum_memory_mb * 1_000_000)
    address_limit = resource.getrlimit(resource.RLIMIT_AS)[0]
    address_limit = None if address_limit == resource.RLIM_INFINITY else address_limit
    groups = _cgroup_headrooms()
    host_available = _kilobyte_fields(Path('/proc/meminfo')).get('MemAvailable')
    headrooms = {'selected_resident': selected - resident}
    if address_limit is not None:
        headrooms['address_space'] = address_limit - virtual
    if host_available is not None:
        headrooms['host_available'] = host_available
    for index, row in enumerate(groups):
        headrooms['cgroup_' + str(index)] = (row['limit_bytes'] - row['used_bytes']
            + row.get('reclaimable_file_bytes', 0))
    return dict(resident_bytes=resident, virtual_bytes=virtual,
        selected_resident_limit_bytes=selected, address_space_limit_bytes=address_limit,
        cgroups=groups, headrooms_bytes=headrooms,
        available_bytes=max(0, min(headrooms.values())))


def memory_blocks(count: int, *, bytes_per_item: int, maximum_memory_mb: float,
        max_items: int | None = None, fixed_bytes: int = 0):
    """Cover every item once, recalculating safe array size before each block.

    Callers account for simultaneously live arrays and release a block before
    requesting another. Half the observed residual headroom stays available
    for native workspaces, allocator overhead and concurrent cgroup changes.
    A single item that cannot fit fails explicitly; no term is omitted.
    """
    if (type(count) is not int or count < 0 or type(bytes_per_item) is not int or bytes_per_item < 1
            or type(fixed_bytes) is not int or fixed_bytes < 0
            or (max_items is not None and (type(max_items) is not int or max_items < 1))):
        raise ValueError('native array blocks require integral nonnegative sizes and positive item bytes')
    offset = 0
    while offset < count:
        observed = memory_observation(maximum_memory_mb)
        capacity = (observed['available_bytes'] - fixed_bytes) // (2 * bytes_per_item)
        if capacity < 1:
            raise MemoryError('Not enough memory for one complete native array item: '
                f'item_bytes={bytes_per_item}, fixed_bytes={fixed_bytes}, observed={observed}')
        end = min(count, offset + capacity, offset + (max_items or count))
        yield offset, end
        offset = end


def grid_block_size(count: int, *, nao: int, derivative: int, maximum_memory_mb: float,
        alignment: int, working_memory_mb: float | None = None,
        requested_size: int | None = None, response_atoms: int = 0, observe=None) -> int:
    """Bound AO and complete Becke-response workspaces before their allocation.

    The response partition tensor has three components for every atom pair.
    It is released before AO evaluation. Both phases must fit the same block.
    Four AO matrices are reserved in addition to the observed live arrays.
    Half the remaining workspace stays available for native temporaries.
    """
    if (type(count) is not int or count < 0 or type(nao) is not int or nao < 1
            or type(derivative) is not int or derivative < 0
            or type(alignment) is not int or alignment < 1
            or type(response_atoms) is not int or response_atoms < 0
            or (requested_size is not None and (type(requested_size) is not int
                or requested_size < alignment or requested_size % alignment))):
        raise ValueError('grid arrays require positive integral dimensions and aligned requested blocks')
    if count == 0:
        return 0
    observed = memory_observation(maximum_memory_mb)
    available = observed['available_bytes']
    if working_memory_mb is not None:
        if isinstance(working_memory_mb, bool) or not math.isfinite(working_memory_mb):
            raise ValueError('grid working memory must be finite')
        available = min(available, int(working_memory_mb * 1_000_000))
    comp = (derivative+1)*(derivative+2)*(derivative+3)//6
    ao_bytes_per_point = 8*((3*comp+8)*nao+64)
    partition_bytes_per_point = 8*(3*response_atoms**2+12*response_atoms+64)
    item_bytes = max(ao_bytes_per_point, partition_bytes_per_point)
    fixed_bytes = 4*nao**2*8
    capacity = (available-fixed_bytes)//(2*item_bytes*alignment)*alignment
    if capacity < alignment:
        raise MemoryError('Not enough memory for one complete aligned DFT grid block: '
            f'point_bytes={item_bytes}, fixed_bytes={fixed_bytes}, alignment={alignment}, '
            f'working_memory_mb={working_memory_mb}, observed={observed}')
    selected = min(capacity, (count+alignment-1)//alignment*alignment,
        requested_size or 1200*alignment)
    if observe is not None:
        observe(dict(event='dft-grid-block-selection', grid_points=count, basis_functions=nao,
            ao_derivative=derivative, response_atoms=response_atoms, block_points=selected,
            simultaneous_bytes_per_point=item_bytes, fixed_workspace_bytes=fixed_bytes, memory=observed))
    return selected
