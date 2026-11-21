# SPDX-License-Identifier: MPL-2.0
"""GPU selection and complete-force contracts with disclosed software operands."""

import builtins
from dataclasses import fields, replace
import math
from types import SimpleNamespace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_selection as selection_owner
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_translation as graph
from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import bind_charged_background, bind_full_density_potential
from empirical_lawhood.methods.electrostatics import charged_background_energy
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from tests import test_rubisco_periodic_probe_operation as controls

fixture = controls.fixture


def test_retained_cpu_reference_binds_current_adapter_domain_and_method_sources():
    """Source-only preparation must work without installing a native solver."""
    from tests.rubisco_gpu_reference import source_bindings
    bindings = source_bindings()
    assert {'periodic_qmmm.py', 'periodic_images.py', 'periodic_mm_remainder.py',
        'periodic_memory.py', 'periodic_force_contracts.py', 'electrostatics.py',
        'numeric_fixture'} <= bindings.keys()
    assert all(len(value) == 64 for value in bindings.values())


def test_periodic_scientific_records_are_owned_by_domain_without_adapter_aliases():
    from empirical_lawhood.domains.rubisco.rubisco_response import periodic_force_contracts
    from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm
    for name in ('AmberPeriodicCell', 'PeriodicForceSettings', 'ConstrainedPeriodicForceSettings',
            'PeriodicMMSettings', 'read_amber_periodic_cell', 'validate_periodic_force_settings'):
        assert getattr(periodic_force_contracts, name).__module__ == periodic_force_contracts.__name__
        assert not hasattr(periodic_qmmm, name)


def gpu_engine(original, *, molecular_platform='CUDA'):
    added = tuple(FileEvidence(name+'/EXPOSED-NONEXECUTABLE-CONTROL', 0, '0'*64)
        for name in set(selection_owner.GPU_NUMERIC_PACKAGES)-set(selection_owner.NUMERIC_PACKAGES))
    engine_type = (selection_owner.AcceleratedPeriodicNumericEngine if molecular_platform == 'CUDA'
        else selection_owner.GpuReferencePeriodicNumericEngine)
    return engine_type(
        **{field.name:getattr(original, field.name) for field in fields(selection_owner.PeriodicNumericEngine)
           if field.name != 'files'},
        files=tuple(sorted((*original.files, *added), key=lambda row: row.relative_path)),
        host_memory_bytes=16*2**30, device_memory_bytes=4*2**30)


def gpu_config(fixture, *, molecular_platform='CUDA'):
    engine = gpu_engine(fixture.selection.engine, molecular_platform=molecular_platform)
    selected = selection_owner.prepare_periodic_probe_selection(representation=fixture.model,
        path=fixture.selection.path, cell=fixture.selection.cell, electronic=fixture.selection.electronic,
        molecular=fixture.selection.molecular, engine=engine)
    return owner.AcceleratedPeriodicProbeConfig(**{field.name:(selected if field.name == 'selection'
        else getattr(fixture.config, field.name)) for field in fields(owner.PeriodicProbeConfig)})


def test_charged_background_has_independent_closed_form_and_preserves_upstream():
    # q_QM=-2, q_MM=5, V=8000, eta=0.3 gives +pi/90 Eh.
    expected = math.pi/90
    assert charged_background_energy(qm_charge=-2, mm_charge=5, volume_bohr3=8000,
        eta_inverse_bohr=.3) == pytest.approx(expected, abs=1e-16)
    assert charged_background_energy(qm_charge=0, mm_charge=17, volume_bohr3=8000,
        eta_inverse_bohr=.3) == 0
    calls = []
    def original(**kwargs):
        calls.append(kwargs)
        return 7.5
    mean_field = SimpleNamespace(energy_ewald=original, mol=SimpleNamespace(charge=-2),
        mm_mol=SimpleNamespace(atom_charges=lambda: [2., 3.], vol=8000., get_ewald_params=lambda: (.3, 12.)))
    bind_charged_background(mean_field)
    assert mean_field.energy_ewald(dm='two-spin-density') == pytest.approx(7.5+expected)
    assert calls == [dict(dm='two-spin-density', mm_ewald_pot=None, qm_ewald_pot=None)]
    with pytest.raises(ValueError, match='already bound'):
        bind_charged_background(mean_field)


@pytest.mark.parametrize('spin_components', (1, 2))
def test_full_density_potential_is_independent_of_accumulated_history(spin_components):
    import numpy as np
    matrix = np.array([[2., .3], [.3, 1.]])
    current = np.array([[.4, .1], [.1, .8]])
    previous = np.array([[.3, .15], [.15, .6]])
    if spin_components == 2:
        current = np.stack((current, current*.7))
        previous = np.stack((previous, previous*.7))
    def potential(dm):
        return matrix@dm + dm@matrix
    periodic = np.full_like(current, .05)
    observations = []
    def get_veff(mol=None, dm=None, dm_last=None, vhf_last=None, hermi=1, **kwargs):
        assert hermi == 1 and kwargs['qm_ewald_pot'] is periodic
        if vhf_last is not None:
            return potential(dm-dm_last) + vhf_last + periodic
        return potential(dm) + periodic
    mean_field = SimpleNamespace(get_veff=get_veff)
    bind_full_density_potential(mean_field, observe=observations.append)
    for error in (1e-3, -2e-3):
        accumulated = potential(previous) + error
        actual = mean_field.get_veff(dm=current, dm_last=previous,
            vhf_last=accumulated, qm_ewald_pot=periodic)
        np.testing.assert_array_equal(actual, potential(current)+periodic)
    assert observations == [dict(event='gpu-scf-potential-policy',
        density='COMPLETE_CURRENT_DENSITY', incremental_jk=False,
        numerical_tolerances_changed=False)]
    with pytest.raises(ValueError, match='already bound'):
        bind_full_density_potential(mean_field, observe=observations.append)


@pytest.mark.parametrize('molecular_platform', ('CUDA', 'Reference'))
def test_gpu_config_and_compiler_bind_exact_allocations_without_device_contact(fixture, monkeypatch, molecular_platform):
    original_import = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.split('.')[0] in ('cupy', 'gpu4pyscf', 'openmm', 'pyscf'):
            pytest.fail('static configuration contacted a numerical backend: '+name)
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)
    original_bytes = fixture.config.canonical_bytes()
    config = gpu_config(fixture, molecular_platform=molecular_platform)
    assert decode_canonical_bytes(config.canonical_bytes(), owner.AcceleratedPeriodicProbeConfig,
        maximum_bytes=owner.MAX_CONFIG) == config
    declaration = owner.operation_declaration(accelerated=True)
    compiled = compile_recursive_wave(draft=graph.periodic_probe_draft(config),
        registrations=(declaration.registration(),),
        registry=CapabilityRegistry('registry.exposed-cuda', (declaration.manifest(),)),
        implementation_commit=config.implementation.observed_git_head, output_codecs=declaration.record_codecs)
    task, = compiled.execution_plan.tasks
    assert task.capability.capability_key == owner.GPU_CAPABILITY
    assert task.capability.requested_resources.gpu_devices == 1
    assert task.capability.requested_resources.memory_bytes == 16*2**30
    assert task.capability.requested_resources.wall_time_seconds is None
    assert task.maximum_attempts == 1
    assert selection_owner.periodic_molecular_platform(config.selection.engine) == molecular_platform
    assert fixture.config.canonical_bytes() == original_bytes
    assert decode_canonical_bytes(original_bytes, owner.PeriodicProbeConfig, maximum_bytes=owner.MAX_CONFIG) == fixture.config


@pytest.mark.parametrize('damage', ('host-memory', 'device-memory', 'package-census', 'cpu-config', 'cpu-engine'))
def test_gpu_engine_refuses_incomplete_allocation_or_implicit_cpu_fallback(fixture, damage):
    config = gpu_config(fixture)
    with pytest.raises((ValueError, TypeError)):
        if damage == 'host-memory':
            engine = replace(config.selection.engine, host_memory_bytes=1)
            selection = selection_owner.prepare_periodic_probe_selection(representation=fixture.model,
                path=config.selection.path, cell=config.selection.cell, electronic=config.selection.electronic,
                molecular=config.selection.molecular, engine=engine)
            replace(config, selection=selection)
        elif damage == 'device-memory':
            replace(config.selection.engine, device_memory_bytes=0)
        elif damage == 'package-census':
            replace(config.selection.engine, files=config.selection.engine.files[:-1])
        elif damage == 'cpu-config':
            replace(fixture.config, selection=config.selection)
        else:
            replace(config, selection=fixture.selection)


def test_pre_volta_refuses_before_optional_library_import(monkeypatch):
    from empirical_lawhood.execution.resources import accelerated_compute
    from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import preflight_gpu_backend
    monkeypatch.setattr(accelerated_compute, 'observe_cuda_devices',
        lambda: (SimpleNamespace(compute_capability='6.1'),))
    original_import = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.split('.')[0] in ('cupy', 'gpu4pyscf', 'openmm'):
            pytest.fail('unsupported device reached optional numerical construction')
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)
    with pytest.raises(RuntimeError, match='pre-Volta'):
        preflight_gpu_backend(device_memory_bytes=1024)


@pytest.mark.parametrize('initial,needed,expected_release', ((80,70,False),(40,70,True)))
def test_successive_cold_operator_reclaims_only_idle_pool_blocks(initial,needed,expected_release):
    from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import available_device_memory
    state = dict(free=initial, live=10, calls=[])
    def release():
        state['calls'].append('unused-pool-blocks')
        state['free'] = 80
    runtime = SimpleNamespace(memGetInfo=lambda:(state['free'],100),
        deviceSynchronize=lambda:state['calls'].append('synchronize'))
    cp = SimpleNamespace(cuda=SimpleNamespace(runtime=runtime),
        get_default_memory_pool=lambda:SimpleNamespace(free_all_blocks=release))
    free,total,before = available_device_memory(cp,required_bytes=needed)
    assert (free,total,before) == (80,100,initial)
    assert state['live'] == 10
    assert state['calls'] == (['synchronize','unused-pool-blocks'] if expected_release else [])


@pytest.mark.parametrize('molecular_platform', ('CUDA', 'Reference'))
def test_gpu_reader_requires_actual_platform_and_complete_cost_without_native_contact(fixture, molecular_platform):
    import json
    from empirical_lawhood.adapters.rubisco.rubisco_response import gpu_periodic_backend as backend
    from empirical_lawhood.domains.rubisco.rubisco_response.gpu_periodic_read import verify_gpu_observations
    engine = replace(gpu_engine(fixture.selection.engine, molecular_platform=molecular_platform), device_memory_bytes=2**30)
    selected = backend.BACKEND if molecular_platform == 'CUDA' else backend.REFERENCE_MM_BACKEND
    rows = [dict(event='compute-backend', accelerated_compute=True, backend=selected.accelerated_backend,
        gpu4pyscf=backend.GPU4PYSCF_VERSION, device_index=0, device_uuid='GPU-EXPOSED', precision='float64',
        density_fitting=False, grid_response=True,
        openmm_nonbonded_parameter_storage='UPSTREAM_FLOAT32' if molecular_platform == 'CUDA' else 'BINARY64',
        device_allocation_bytes=engine.device_memory_bytes, periodic_source_sha256=backend.PERIODIC_SOURCE_SHA256,
        mm_source_sha256=backend.MM_SOURCE_SHA256),
        dict(event='openmm-platform', platform=molecular_platform, properties=({
            'Precision': 'double', 'DeviceIndex': '0', 'DeterministicForces': 'true'} if molecular_platform == 'CUDA' else {})),
        dict(event='gpu-evaluation-cost', evaluation=1, failed=False, synchronized_device_interval_ms=10.,
            cupy_pool_reserved_bytes=1, cupy_pool_used_bytes=1, observed_peak_pool_bytes=1,
            device_free_bytes=2**30, observed_minimum_device_free_bytes=2**30,
            explicit_host_to_device_bytes=1, explicit_device_to_host_bytes=1), dict(event='return', evaluation=1)]
    def encode(values):
        return b'\n'.join(json.dumps(value).encode() for value in values)
    assert verify_gpu_observations(encode(rows), engine=engine, successful=True) == tuple(rows)
    assert verify_gpu_observations(b'', engine=engine, successful=False) == ()
    other_platform = 'Reference' if molecular_platform == 'CUDA' else 'CUDA'
    for changed in (rows[:-1], rows[1:], [rows[0], {**rows[1], 'platform': other_platform}, *rows[2:]],
            [rows[0], rows[1], {**rows[2], 'failed': True}, rows[3]],
            [{**rows[0], 'device_allocation_bytes': 1}, *rows[1:]]):
        with pytest.raises(ValueError):
            verify_gpu_observations(encode(changed), engine=engine, successful=True)
