# SPDX-License-Identifier: MPL-2.0
"""Exposed GPU lifecycle controls; no hardware or molecular findings are supplied."""

import builtins
from dataclasses import fields, replace
import json
import zlib

import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response import gpu_periodic_backend as backend
from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_backend_evidence import GpuTraceAssessment, assess_gpu_log
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from tests import test_rubisco_periodic_equilibrium_acquisition as equilibrium
from tests import test_rubisco_periodic_trajectory as trajectory
from tests import test_rubisco_active_relaxation_operation as relaxation
from tests import test_rubisco_conditional_active_relaxation as conditional
from tests.test_rubisco_accelerated_compute import gpu_config, gpu_engine


fixture = trajectory.fixture
matched = relaxation.matched
relaxation_fixture = relaxation.fixture


def apparatus(memory):
    return [dict(event='compute-backend', accelerated_compute=True, backend=backend.BACKEND.accelerated_backend,
        gpu4pyscf=backend.GPU4PYSCF_VERSION, device_index=0, device_uuid='GPU-EXPOSED-SOFTWARE-CONTROL',
        precision='float64', density_fitting=False, grid_response=True,
        openmm_nonbonded_parameter_storage='UPSTREAM_FLOAT32', device_allocation_bytes=memory,
        periodic_source_sha256=backend.PERIODIC_SOURCE_SHA256, mm_source_sha256=backend.MM_SOURCE_SHA256),
        dict(event='openmm-platform', platform='CUDA', properties={
            'Precision':'double', 'DeviceIndex':'0', 'DeterministicForces':'true'})]


def cost(number, failed=False):
    return dict(event='gpu-evaluation-cost', evaluation=number, failed=failed,
        synchronized_device_interval_ms=10., cupy_pool_reserved_bytes=1, cupy_pool_used_bytes=1,
        observed_peak_pool_bytes=1, device_free_bytes=2**30, observed_minimum_device_free_bytes=2**30,
        explicit_host_to_device_bytes=8, explicit_device_to_host_bytes=16)


def instrument_exposed_operator(monkeypatch, *, missing_cost=False):
    original = periodic_qmmm.PeriodicCoupledOperator
    calls = []
    class Instrumented(original):
        def __init__(self, **kwargs):
            assert kwargs['accelerated_compute'] is True
            memory = kwargs['device_memory_bytes']
            assert memory == 4*2**30
            target = kwargs['observe']
            for row in apparatus(memory):
                target(row)
            def observe(row):
                if row['event'] == 'return' and not missing_cost:
                    target(cost(row['evaluation']))
                target(row)
            kwargs['observe'] = observe
            super().__init__(**kwargs)
            calls.append(kwargs)
    monkeypatch.setattr(periodic_qmmm, 'PeriodicCoupledOperator', Instrumented)
    monkeypatch.setattr(backend, 'preflight_gpu_backend', lambda **k:None)
    return calls


@pytest.mark.parametrize('control', (trajectory, equilibrium))
def test_gpu_trace_compiles_without_device_contact_and_preserves_cpu_config(fixture, monkeypatch, control):
    cpu, _ = control.trajectory(fixture)
    original_bytes = cpu.canonical_bytes()
    fixture.config = gpu_config(fixture)
    fixture.selection = fixture.config.selection
    original_import = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.split('.')[0] in ('cupy', 'gpu4pyscf', 'openmm', 'pyscf'):
            pytest.fail('static GPU trace preparation contacted '+name)
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)
    config, _ = control.trajectory(fixture)
    assert decode_canonical_bytes(config.canonical_bytes(), type(config), maximum_bytes=control.owner.MAX_CONFIG) == config
    declaration = control.owner.operation_declaration(accelerated=True)
    draft = (control.graph.reference_trajectory_draft(config) if control is trajectory
        else control.graph.reference_equilibrium_draft(config))
    compiled = compile_recursive_wave(draft=draft, registrations=(declaration.registration(),),
        registry=CapabilityRegistry('registry.exposed.gpu-trace', (declaration.manifest(),)),
        implementation_commit=config.original.implementation.observed_git_head, output_codecs=declaration.record_codecs)
    task, = compiled.execution_plan.tasks
    assert task.capability.requested_resources.gpu_devices == 1
    assert task.capability.requested_resources.memory_bytes == 16*2**30
    assert task.capability.requested_resources.wall_time_seconds is None
    assert task.maximum_attempts == 1
    assert cpu.canonical_bytes() == original_bytes
    assert decode_canonical_bytes(original_bytes, type(cpu), maximum_bytes=control.owner.MAX_CONFIG) == cpu
    with pytest.raises(TypeError):
        replace(cpu, original=fixture.config)


@pytest.mark.parametrize('control', (trajectory, equilibrium))
@pytest.mark.parametrize('missing_cost', (False, True))
def test_gpu_trace_original_custody_assessment_and_recovery(fixture, monkeypatch, control, missing_cost):
    fixture.config = gpu_config(fixture)
    fixture.selection = fixture.config.selection
    config, raw = control.trajectory(fixture)
    control.stub_native(fixture, monkeypatch)
    calls = instrument_exposed_operator(monkeypatch, missing_cost=missing_cost)
    selected = control.custody(fixture, config, raw)
    runner = control.owner.operation_declaration(accelerated=True).runner_factory()
    runner.preflight(selected.fresh_context())
    returned = runner.execute_with_native_subwork(selected.context, selected.store)
    result_kind = control.owner.ReferenceTrajectoryResult if control is trajectory else control.owner.ReferenceEquilibriumResult
    original = decode_canonical_bytes(returned.outputs[0].payload, result_kind, maximum_bytes=control.owner.MAX_RETURN)
    assert len(calls) == 1 and original.returned.error is None
    monkeypatch.setattr(backend, 'preflight_gpu_backend', lambda **k:pytest.fail('recovery contacted GPU'))
    repeated = runner.execute_with_native_subwork(selected.fresh_context(), selected.store)
    assert repeated.outputs[0].payload == returned.outputs[0].payload
    reader = control.retained.read_reference_trajectory if control is trajectory else control.retained.read_reference_equilibrium
    report = reader(config=config, representation=fixture.model, phase_bytes=raw, original_result=original,
        native_subwork=selected.store, assessor_source=fixture.model.material.sources[0])
    assert report['new_operator_evaluations'] == 0
    assert report['authenticated_file_count'] == len(original.returned.files.files)
    if missing_cost:
        assert report['gpu_assessment'] is None
        assert 'cost' in report['gpu_assessment_error']
    else:
        assert report['gpu_assessment_error'] is None
        assert report['gpu_assessment']['complete_returns'] == 4
        assert report['gpu_assessment']['recorded_costs'] == 4
        assert report['gpu_assessment']['summed_synchronized_device_interval_ms'] == 40
    assert len(calls) == 1


@pytest.mark.parametrize('control', (trajectory, equilibrium))
def test_gpu_trace_flag_and_allocation_mismatch_refuse_before_device(fixture, monkeypatch, control):
    fixture.config = gpu_config(fixture)
    fixture.selection = fixture.config.selection
    config, phase = control.trajectory(fixture)
    selected = control.custody(fixture, config, phase)
    runner = control.owner.operation_declaration(accelerated=True).runner_factory()
    monkeypatch.setattr(control.owner, 'authenticate_periodic_engine', lambda *a, **k:pytest.fail('bad selection reached engine'))
    with pytest.raises(ValueError, match='accelerated_compute'):
        runner.preflight(replace(selected.context, accelerated_compute=False))
    with pytest.raises(ValueError, match='allocation'):
        runner.preflight(replace(selected.fresh_context(), prepared_invocation=None, resource_budget=control.owner.BUDGET))


@pytest.mark.parametrize('control', (trajectory, equilibrium))
def test_unknown_gpu_trace_contact_refuses_without_probing_or_reentry(fixture, monkeypatch, control):
    fixture.config = gpu_config(fixture)
    fixture.selection = fixture.config.selection
    config, phase = control.trajectory(fixture)
    selected = control.custody(fixture, config, phase)
    selected.store.freeze_roster(selected.work.rosters[0], definitions=selected.work.definitions)
    entry = selected.store.begin(selected.work.definitions[0])
    selected.store.contact(entry)
    monkeypatch.setattr(backend, 'preflight_gpu_backend', lambda **k:pytest.fail('unknown attempt reached GPU'))
    runner = control.owner.operation_declaration(accelerated=True).runner_factory()
    with pytest.raises(ValueError, match='no automatic retry'):
        runner.execute_with_native_subwork(selected.context, selected.store)
    assert selected.store.inspect(selected.work.definitions[0]).state is control.NativeSubworkState.UNKNOWN_COMPLETION


def test_gpu_assessment_failure_cannot_hide_late_custody_corruption(fixture, monkeypatch):
    fixture.config = gpu_config(fixture)
    fixture.selection = fixture.config.selection
    config, phase = trajectory.trajectory(fixture)
    trajectory.stub_native(fixture, monkeypatch)
    instrument_exposed_operator(monkeypatch)
    original_native = trajectory.native.execute_reference_trajectory
    def changed(**kwargs):
        result = original_native(**kwargs)
        directory = kwargs['directory']
        path = directory/'gpu.apparatus.openmm-platform.json'
        row = json.loads(path.read_bytes())
        row['platform'] = 'Reference'
        path.write_text(json.dumps(row))
        (directory/'zz-tail.txt').write_bytes(b'original-tail')
        return result
    monkeypatch.setattr(trajectory.native, 'execute_reference_trajectory', changed)
    selected = trajectory.custody(fixture, config, phase)
    runner = trajectory.owner.operation_declaration(accelerated=True).runner_factory()
    output = runner.execute_with_native_subwork(selected.context, selected.store)
    original = decode_canonical_bytes(output.outputs[0].payload, trajectory.owner.ReferenceTrajectoryResult,
        maximum_bytes=trajectory.owner.MAX_RETURN)
    iterator = selected.store.iter_completed_output
    archive = b''.join(iterator(original.definition, 'files.raw'))
    expanded = zlib.decompress(archive, wbits=31)
    assert expanded.endswith(b'original-tail')
    compressor = zlib.compressobj(wbits=31)
    changed_archive = compressor.compress(expanded[:-1]+b'X')+compressor.flush()
    def corrupt(definition, output_id, **kwargs):
        if output_id == 'files.raw':
            yield changed_archive
        else:
            yield from iterator(definition, output_id, **kwargs)
    monkeypatch.setattr(selected.store, 'iter_completed_output', corrupt)
    with pytest.raises(trajectory.retained.TrajectoryCustodyError, match='original complete file'):
        trajectory.retained.read_reference_trajectory(config=config, representation=fixture.model, phase_bytes=phase,
            original_result=original, native_subwork=selected.store, assessor_source=fixture.model.material.sources[0])


@pytest.mark.parametrize('damage', ('missing-middle', 'repeated-return', 'wrong-number', 'cpu-platform', 'missing-cost', 'negative-cost', 'after-error'))
def test_multicall_cost_reader_refuses_hidden_or_relabelled_work(fixture, damage):
    engine = gpu_engine(fixture.selection.engine)
    rows = apparatus(engine.device_memory_bytes)
    for n in range(1, 4):
        rows.extend((dict(event='entry', evaluation=n), cost(n), dict(event='return', evaluation=n)))
    raw = lambda:b'\n'.join(json.dumps(r).encode() for r in rows)
    assert assess_gpu_log(raw(), engine=engine, expected_evaluations=3, successful=True)['recorded_costs'] == 3
    if damage == 'missing-middle': del rows[5:8]
    elif damage == 'repeated-return': rows.insert(5, dict(event='return', evaluation=1))
    elif damage == 'wrong-number': rows[3]['evaluation'] = True
    elif damage == 'cpu-platform': rows[1]['platform'] = 'Reference'
    elif damage == 'missing-cost': del rows[6]
    elif damage == 'negative-cost': rows[6]['synchronized_device_interval_ms'] = -1
    else: rows.insert(5, dict(event='error', evaluation=1))
    with pytest.raises(ValueError):
        assess_gpu_log(raw(), engine=engine, expected_evaluations=3, successful=True)


def test_failed_gpu_trace_retains_missing_cost_without_claiming_completion(fixture):
    engine = gpu_engine(fixture.selection.engine)
    rows = [*apparatus(engine.device_memory_bytes), dict(event='entry', evaluation=1), cost(1), dict(event='return', evaluation=1),
        dict(event='entry', evaluation=2), dict(event='gpu-cost-unavailable', evaluation=2), dict(event='error', evaluation=2)]
    raw = b'\n'.join(json.dumps(r).encode() for r in rows)
    result = assess_gpu_log(raw, engine=engine, expected_evaluations=5, successful=False)
    assert result['complete_returns'] == 1 and result['unavailable_costs'] == 1
    assert result['recorded_evaluations'] == 2
    assert result['recorded_entries'] == 2
    assert result['summed_synchronized_device_interval_ms'] is None
    assert result['measured_synchronized_device_interval_ms'] == 10
    with pytest.raises(ValueError):
        assess_gpu_log(raw, engine=engine, expected_evaluations=5, successful=True)
    assessment = GpuTraceAssessment(engine)
    with pytest.raises(ValueError, match='undeclared'):
        assessment.consume('gpu.undeclared.json', b'{}')


def test_gpu_failure_before_cost_or_error_callback_keeps_its_entered_call(fixture):
    engine = gpu_engine(fixture.selection.engine)
    rows = [*apparatus(engine.device_memory_bytes), dict(event='entry', evaluation=1)]
    result = assess_gpu_log(b'\n'.join(json.dumps(r).encode() for r in rows), engine=engine,
        expected_evaluations=5, successful=False)
    assert result['recorded_evaluations'] == result['recorded_entries'] == result['unavailable_costs'] == 1
    assert result['recorded_costs'] == result['complete_returns'] == 0
    assert result['summed_synchronized_device_interval_ms'] is None


def accelerated_relaxation(fixture, *, subset):
    from tests.rubisco_active_fixture import prepared_control
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import prepare_matched_relaxation_plan
    owner = relaxation.owner
    stock = gpu_engine(fixture.prototype.engine)
    models = tuple(prepared_control(name, stock) for name in relaxation.MODEL_NAMES)
    plan = prepare_matched_relaxation_plan(models=tuple((m.material,p,s) for m,s,p,*_ in models),
        settings=fixture.plan.settings)
    model, prototype, prepared, top, xyz, coordinates = models[0]
    sources = owner.prepare_raw_sources(prototype, top, xyz)
    values = {f.name:getattr(fixture.config, f.name) for f in fields(owner.ActiveRelaxationConfig)}
    values.update(plan=plan, prototype=prototype, preparation=prepared.identity,
        preparation_size_bytes=prepared.canonical_size_bytes(), seeds=prepared.seeds,
        representation_size_bytes=model.canonical_size_bytes(), raw_sources=sources.identity,
        raw_source_size_bytes=sources.canonical_size_bytes())
    if subset:
        values['selection'] = conditional.public.prepare_conditional_active_relaxation(plan=plan,
            state_census=plan.members[0].state_census[:2], assumptions=('Exposed GPU software control, no physical population.',))
    fixture.config = owner.configuration_type(conditional=subset, accelerated=True)(**values)
    for key,value in dict(models=models, plan=plan, model=model, prototype=prototype, prepared=prepared,
            raw_top=top, raw_xyz=xyz, coordinates=coordinates, sources=sources).items():
        setattr(fixture, key, value)
    return fixture


@pytest.mark.parametrize('subset', (False, True))
def test_gpu_relaxation_compiles_complete_and_conditional_denominators(relaxation_fixture, subset):
    f = accelerated_relaxation(relaxation_fixture, subset=subset)
    owner = relaxation.owner
    declaration = owner.operation_declaration(conditional=subset, accelerated=True)
    assert decode_canonical_bytes(f.config.canonical_bytes(), type(f.config), maximum_bytes=owner.MAX_CONFIG) == f.config
    compiled = compile_recursive_wave(draft=relaxation.graph.active_relaxation_draft(f.config),
        registrations=(declaration.registration(),),
        registry=CapabilityRegistry('registry.exposed.gpu-relaxation', (declaration.manifest(),)),
        implementation_commit=f.config.implementation.observed_git_head, output_codecs=declaration.record_codecs)
    task, = compiled.execution_plan.tasks
    assert task.capability.requested_resources.gpu_devices == 1
    assert task.capability.requested_resources.memory_bytes == 16*2**30
    assert len(f.config.seeds) == 96
    assert len(owner.state_census_for(f.config)) == (2 if subset else 96)


def test_gpu_conditional_relaxation_returns_and_recovers_original_endpoint_evidence(relaxation_fixture, monkeypatch):
    f = accelerated_relaxation(relaxation_fixture, subset=True)
    conditional.install_exposed_operator(monkeypatch)
    calls = instrument_exposed_operator(monkeypatch)
    selected = relaxation.custody(f)
    runner = relaxation.owner.ActiveRelaxationRunner(conditional=True, accelerated=True)
    runner.preflight(selected.fresh())
    returned = runner.execute_with_native_subwork(selected.context, selected.store)
    original = decode_canonical_bytes(returned.outputs[0].payload,
        relaxation.owner.ConditionalActiveRelaxationResult, maximum_bytes=64*2**20)
    assert all(unit.returned.error is None for unit in original.units)
    report = relaxation.retained.read_relaxation(config=f.config, representation=f.model, prepared=f.prepared,
        coordinate_bytes=f.coordinates, original_result=original, native_subwork=selected.store,
        assessor_source=f.model.material.sources[0], readout_id='readout.exposed.gpu-relaxation')
    assert len(report.endpoints) == 2 and len(report.state_census) == 96
    assert all(row.assessment is not None for row in report.endpoints)
    monkeypatch.setattr(backend, 'preflight_gpu_backend', lambda **k:pytest.fail('recovery contacted GPU'))
    assert runner.execute_with_native_subwork(selected.fresh(), selected.store).outputs == returned.outputs
    assert len(calls) == 2
