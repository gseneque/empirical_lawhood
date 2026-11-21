# SPDX-License-Identifier: MPL-2.0
"""Explicit platform selection and unsafe-grid refusal, without native evidence."""

from dataclasses import fields
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.gpu_openmm_limits import validate_cuda_pme_grid, validate_reference_pme_grid
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_selection as owner
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from tests.test_rubisco_accelerated_compute import fixture as fixture, gpu_engine


def test_reference_mm_has_distinct_canonical_selection_and_preserves_original_bytes(fixture):
    cuda = gpu_engine(fixture.selection.engine)
    original = cuda.canonical_bytes()
    selected = owner.GpuReferencePeriodicNumericEngine(**{f.name:getattr(cuda, f.name) for f in fields(cuda)})
    assert selected.identity != cuda.identity
    assert selected.files == cuda.files
    assert decode_canonical_bytes(selected.canonical_bytes(), owner.GpuReferencePeriodicNumericEngine,
        maximum_bytes=2**20) == selected
    assert owner.periodic_operator_options(selected) == dict(accelerated_compute=True,
        device_memory_bytes=cuda.device_memory_bytes, molecular_platform='Reference',
        host_memory_bytes=cuda.host_memory_bytes)
    assert owner.periodic_operator_options(cuda) == dict(accelerated_compute=True,
        device_memory_bytes=cuda.device_memory_bytes)
    assert cuda.canonical_bytes() == original
    assert decode_canonical_bytes(original, owner.AcceleratedPeriodicNumericEngine, maximum_bytes=2**20) == cuda


def test_large_pme_grid_refuses_the_actual_signed_byte_overflow():
    # Actual full-enzyme dimensions: two double values per allocated point.
    with pytest.raises(ValueError, match='16595712000 bytes'):
        validate_cuda_pme_grid((1029, 1050, 960))
    assert validate_cuda_pme_grid((511, 512, 512)) == 2143289344
    with pytest.raises(ValueError, match='signed buffer-clear'):
        validate_cuda_pme_grid((512, 512, 512))


def test_reference_pme_refuses_the_finer_full_model_index_overflow():
    assert validate_reference_pme_grid((1026, 1038, 948)) == 1009608624
    with pytest.raises(ValueError, match='4944545060 grid points'):
        validate_reference_pme_grid((1742, 1763, 1610))
    assert validate_reference_pme_grid((1290, 1290, 1290)) == 2146689000
    with pytest.raises(ValueError, match='signed grid-index'):
        validate_reference_pme_grid((1291, 1291, 1291))


def test_wide_reference_pme_still_requires_the_selected_host_allocation():
    mesh = (1742, 1763, 1610)
    with pytest.raises(ValueError, match='explicit host-memory'):
        validate_reference_pme_grid(mesh, index_bits=64)
    with pytest.raises(ValueError, match='79112720960 grid bytes'):
        validate_reference_pme_grid(mesh, index_bits=64, host_memory_bytes=64*2**30)
    assert validate_reference_pme_grid(mesh, index_bits=64, host_memory_bytes=128*2**30) == 4944545060
    with pytest.raises(ValueError, match='signed grid-index'):
        validate_reference_pme_grid(mesh, index_bits=32, host_memory_bytes=128*2**30)
    with pytest.raises(ValueError, match='addressable byte'):
        validate_reference_pme_grid((2**30, 2**30, 2**30), index_bits=64, host_memory_bytes=128*2**30)


def test_reference_mm_control_custody_reads_selected_platform_without_replay(fixture, monkeypatch):
    import json
    import numpy as np
    from empirical_lawhood.adapters.rubisco.rubisco_response import gpu_periodic_backend as backend
    from tests.test_rubisco_accelerated_compute import gpu_config
    from tests.test_rubisco_accelerated_traces import apparatus, cost
    from tests import test_rubisco_periodic_control_operation as control
    from tests.test_rubisco_periodic_controls import selected
    monkeypatch.setattr(backend, 'preflight_gpu_backend', lambda **kwargs:None)
    fixture.config = gpu_config(fixture, molecular_platform='Reference')
    fixture.selection = fixture.config.selection
    protocol, points, raw = selected(fixture)
    config = control.owner.AcceleratedPeriodicControlConfig('config.exposed.reference-mm', fixture.config, protocol, points[0])
    custody = control.custody(fixture, config)
    def original(**kwargs):
        control.disclose_point(kwargs)
        rows = apparatus(fixture.selection.engine.device_memory_bytes)
        rows[0].update(backend=backend.REFERENCE_MM_BACKEND.accelerated_backend,
            openmm_nonbonded_parameter_storage='BINARY64')
        rows[1].update(platform='Reference', properties={})
        rows += [dict(event='entry', evaluation=1), cost(1), dict(event='return', evaluation=1)]
        (kwargs['directory']/'native-observations.jsonl').write_text('\n'.join(json.dumps(row) for row in rows))
        return dict(energy_hartree=-3.25, gradient_hartree_per_bohr=np.zeros((83, 3)))
    result = control.execute(custody, monkeypatch, original)
    monkeypatch.setattr(control.native, 'execute_periodic_control', lambda **kwargs:pytest.fail('retained read repeated native work'))
    report = control.retained.read_periodic_control_point(config=config, representation=fixture.model,
        coordinate_bytes=raw, original_result=result, native_subwork=custody.store,
        assessor_source=fixture.model.material.sources[0], readout_id='read.exposed.reference-mm')
    assert report.original_result == result
    assert report.numerical_integrity.disposition.value == 'SATISFIED'
    with pytest.raises(ValueError, match='original accelerated baseline'):
        control.retained.read_periodic_molecular_precision(config=config, representation=fixture.model,
            coordinate_bytes=raw, original_result=result, native_subwork=custody.store,
            assessor_source=fixture.model.material.sources[0], readout_id='read.exposed.no-cuda-control')
