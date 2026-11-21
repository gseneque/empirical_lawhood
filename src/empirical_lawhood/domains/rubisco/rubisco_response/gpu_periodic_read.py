# SPDX-License-Identifier: MPL-2.0
"""Independent read of authenticated GPU apparatus and complete-return costs."""

import json
import math

from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import BACKEND, REFERENCE_MM_BACKEND, GPU4PYSCF_VERSION, MM_SOURCE_SHA256, PERIODIC_SOURCE_SHA256
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import accelerated_engine, periodic_molecular_platform


def verify_gpu_observations(raw, *, engine, successful, evaluation=1):
    """Check apparatus claims without importing or running any numerical engine."""
    if not accelerated_engine(engine):
        raise ValueError('GPU observations require an explicitly selected accelerated engine')
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    molecular_platform = periodic_molecular_platform(engine)
    backend = BACKEND if molecular_platform == 'CUDA' else REFERENCE_MM_BACKEND
    if any(type(row) is not dict for row in rows):
        raise ValueError('GPU observations require complete diagnostic objects')
    devices = [row for row in rows if row.get('event') == 'compute-backend']
    if len(devices) > 1 or successful and len(devices) != 1:
        raise ValueError('GPU return omits or repeats its actual backend observation')
    for row in devices:
        expected = dict(accelerated_compute=True, backend=backend.accelerated_backend,
            gpu4pyscf=GPU4PYSCF_VERSION, device_index=0, precision='float64',
            density_fitting=False, grid_response=True,
            openmm_nonbonded_parameter_storage='UPSTREAM_FLOAT32' if molecular_platform == 'CUDA' else 'BINARY64',
            device_allocation_bytes=engine.device_memory_bytes,
            periodic_source_sha256=PERIODIC_SOURCE_SHA256, mm_source_sha256=MM_SOURCE_SHA256)
        if any(type(row.get(key)) is not type(value) or row[key] != value for key, value in expected.items()):
            raise ValueError('GPU return changes its selected numerical backend or device allocation')
        if not isinstance(row.get('device_uuid'), str) or not row['device_uuid'].startswith('GPU-'):
            raise ValueError('GPU return omits its actual device identity')
    platforms = [row for row in rows if row.get('event') == 'openmm-platform']
    if len(platforms) > 1 or successful and len(platforms) != 1:
        raise ValueError('GPU return omits or repeats its actual MM platform observation')
    for row in platforms:
        properties = ({'Precision': 'double', 'DeviceIndex': '0', 'DeterministicForces': 'true'}
            if molecular_platform == 'CUDA' else {})
        if row.get('platform') != molecular_platform or row.get('properties') != properties:
            raise ValueError('GPU return substitutes its explicitly selected MM platform or precision')
    costs = [row for row in rows if row.get('event') == 'gpu-evaluation-cost']
    returns = [row for row in rows if row.get('event') == 'return']
    if successful and (len(costs) != 1 or len(returns) != 1 or costs[0].get('failed') is not False):
        raise ValueError('GPU return omits its complete synchronized evaluation cost')
    for row in costs:
        value = row.get('synchronized_device_interval_ms')
        if (type(value) not in (int, float) or not math.isfinite(value) or value < 0
                or type(row.get('failed')) is not bool or type(row.get('evaluation')) is not int
                or row['evaluation'] != evaluation):
            raise ValueError('GPU cost changes the actual complete evaluation denominator')
        for key in ('cupy_pool_reserved_bytes', 'cupy_pool_used_bytes', 'observed_peak_pool_bytes',
                'device_free_bytes', 'observed_minimum_device_free_bytes',
                'explicit_host_to_device_bytes', 'explicit_device_to_host_bytes'):
            if type(row.get(key)) is not int or row[key] < 0:
                raise ValueError('GPU cost omits a finite observed memory or transfer count')
    if any(type(row.get('evaluation')) is not int or row['evaluation'] != evaluation for row in returns):
        raise ValueError('GPU return substitutes its original evaluation number')
    return tuple(rows)
