# SPDX-License-Identifier: MPL-2.0
"""One-factor constructor, custody, dispatch and source-preservation controls."""
from dataclasses import replace
from decimal import Decimal as D
import json
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.adapters.methods.battery_observation_inquiry import internal_step_control as sc
from empirical_lawhood.adapters.methods.battery_observation_inquiry import contracts as ct
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_observation_contracts as oc
from empirical_lawhood.infrastructure.execution import LocalScheduler, ResourceAdmissionError
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost


@pytest.fixture
def control():
    return sc.InternalStepControl('control.exposed-internal-step',
        ObjectIdentity('observation.exposed', oc.PreparationObservationProtocol.SCHEMA, '1.0.0', '1' * 64),
        ObjectIdentity('readout.exposed-negative', ct.ObservationReadout.SCHEMA, '1.0.0', '2' * 64), D(1),
        ObjectIdentity('request.exposed-baseline', 'empirical-lawhood/battery-segmented/native-request', '1.0.0', '4' * 64),
        sc._primitive({'type': 'IDAKLUSolver', **constructor(), 'options': {'calc_ic': True, 'jacobian': 'sparse'} | constructor()['options']}))


@pytest.mark.parametrize('damage', (
    {'maximum_internal_step_s': D(0)}, {'maximum_internal_step_s': D('2')},
    {'maximum_internal_step_s': 1}, {'baseline_internal_step_s': D(1)},
    {'unchanged_rtol': D('1e-8')}, {'unchanged_atol': D('1e-9')},
    {'unchanged_electrode_points': 60}, {'unchanged_particle_points': 80},
    {'physical_units': 1}, {'scope': 'QUALIFIED'},
))
def test_control_refuses_multiple_factors_or_promoted_scope(control, damage):
    with pytest.raises(ValueError):
        replace(control, **damage)


def test_exact_control_typed_roundtrip(control):
    assert decode_canonical_bytes(control.canonical_bytes(), sc.InternalStepControl, maximum_bytes=None) == control


class Backend:
    def __init__(self):
        self.calls = []

    def IDAKLUSolver(self, **kwargs):
        self.calls.append(kwargs)
        options = {'calc_ic': True, 'jacobian': 'sparse'} | kwargs['options']
        solver = N(to_config=lambda: {'type': 'IDAKLUSolver', **kwargs, 'options': options})
        return solver


def constructor():
    return {'rtol': 1e-7, 'atol': 1e-8, 'on_failure': 'warn',
        'options': {'max_num_steps': -1, 'dt_max': 0.0, 'num_steps_no_progress': 0, 'num_threads': 1, 'num_solvers': 1}}


def witness(control):
    backend = Backend()
    view = sc._BackendView(backend, control)
    original = constructor()
    solver = view.IDAKLUSolver(**original)
    assert original == constructor()
    assert backend.calls == [dict(original, options=dict(original['options'], dt_max=1.0))]
    record = sc.ActualInternalStepAssignment('assignment.exposed-step', control,
        ObjectIdentity('config.exposed', 'empirical-lawhood/battery-segmented/native-config', '1.0.0', '3' * 64),
        *view.assignment)
    assert solver.to_config()['options']['calc_ic'] is True
    return record, backend, view


def test_actual_assignment_preserves_all_original_options_and_binary_bits(control):
    record, backend, view = witness(control)
    assert decode_canonical_bytes(record.canonical_bytes(), sc.ActualInternalStepAssignment, maximum_bytes=None) == record
    with pytest.raises(ValueError):
        view.IDAKLUSolver(**constructor())
    assert len(backend.calls) == 1


@pytest.mark.parametrize('changed', ('dt_max', 'rtol', 'calc_ic'))
def test_actual_solver_mismatch_refuses(control, changed):
    record, _, _ = witness(control)
    values = json.loads(record.actual_solver_json)
    if changed == 'rtol':
        values[changed] = {'binary64': float(1e-8).hex()}
    else:
        values['options'][changed] = False if changed == 'calc_ic' else {'binary64': float(2).hex()}
    with pytest.raises(ValueError):
        replace(record, actual_solver_json=json.dumps(values))


def test_dispatch_keeps_pure_consumers_out_of_native_parent(control):
    scheduler = object.__new__(LocalScheduler)
    for operation in ('assess', 'pair', 'summarize'):
        runner = sc.ControlledObservationRunner(operation, control, None, None)
        assert scheduler._native_subwork_progress(runner, None, ()) is None
    with pytest.raises(ResourceAdmissionError, match='no selected native-effect parent'):
        scheduler._native_subwork_progress(sc.ControlledObservationRunner('observe', control, None, None), None, ())


def test_missing_original_negative_refuses_before_native_hook_mutation(control):
    original = sc.native.build_observation_definition, sc.native.build_runtime
    with pytest.raises(ValueError):
        with sc.native_control_scope(control, None, None):
            pytest.fail('invalid reference entered controlled scope')
    assert original == (sc.native.build_observation_definition, sc.native.build_runtime)


def test_additional_native_payload_cost_is_scoped_once_to_main(control, monkeypatch):
    published, completed = [], []
    def publish(progress, entry, name, record):
        size = len(record.canonical_bytes())
        published.append((entry, name, size))
        return N(materialization=N(size_bytes=size))
    monkeypatch.setattr(sc.passive, '_publish', publish)
    original = N(begin=lambda definition, inputs: N(definition=definition), contact=lambda entry: None,
        complete=lambda entry, **kwargs: completed.append((entry, kwargs)) or kwargs)
    wrapped = sc._ControlledProgress(original, control)
    main = wrapped.begin(N(operation_id='battery.segmented-observation.initial-window'))
    wrapped.contact(main)
    child = wrapped.begin(N(operation_id='battery.segmented-native.segment'))
    wrapped.contact(child)
    cost = InquiryCost(D(3), D(4), D(100))
    assert wrapped.complete(child, cost=cost)['cost'] == cost
    returned = wrapped.complete(main, cost=cost)['cost']
    assert returned.cpu_seconds == 3 and returned.wall_seconds == 4
    assert returned.retained_bytes == 100 + len(control.canonical_bytes())
    assert len(published) == 1 and len(completed) == 2


def test_request_scope_rejects_changed_solver_default_and_restores_reader(control, monkeypatch):
    from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as stream
    record, _, _ = witness(control)
    # The exposed iterator isolates the new request guard; ordinary frame/custody
    # validity is still owned and exercised by the existing full-state tests.
    frame = object.__new__(stream.SegmentEvidenceFrame)
    solver = json.loads(record.actual_solver_json)
    solver['options']['calc_ic'] = False
    object.__setattr__(frame, 'request', N(configuration=record.native_configuration,
        primitive_json=json.dumps({'solver': solver})))
    object.__setattr__(frame, 'definition', N(sources=(control.identity,)))
    original = lambda port: iter((frame,))
    monkeypatch.setattr(stream, 'read_frames', original)
    with pytest.raises(ValueError, match='full solver options'):
        with sc.request_control_scope((record,)):
            tuple(stream.read_frames(None))
    assert stream.read_frames is original
    solver['options']['calc_ic'] = True
    object.__setattr__(frame, 'request', N(configuration=record.native_configuration,
        primitive_json=json.dumps({'solver': solver})))
    with sc.request_control_scope((record,)):
        assert tuple(stream.read_frames(None)) == (frame,)
    assert stream.read_frames is original


def test_authenticated_config_replay_preserves_binding_and_exact_bytes():
    import io
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind, WorkerInputPort
    payload = b'{"original":"exact canonical byte spelling"}'
    binding = WorkerInputBinding('config.exposed-original', 'materialization.exposed-original',
        'empirical-lawhood/exposed/original-record', 'application/json', len(payload),
        VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE, WorkerInputKind.EXTERNAL)
    original = WorkerInputPort(binding, io.BytesIO(payload))
    replay = sc._ReplayPort(original, original.read())
    assert replay.binding is binding and replay.read() == payload
    replay.reader.seek(0)
    assert replay.read() == payload and replay.materialization_id == binding.materialization_id
    replay.close()


def test_missing_changed_recipe_inputs_refuse_before_original_loader(control):
    with pytest.raises(ValueError, match='control/reference input'):
        sc.controlled_context(N(input_ports=()), control, N(readout_id='readout.exposed', fingerprint=lambda: '5' * 64,
            SCHEMA=ct.ObservationReadout.SCHEMA, VERSION='1.0.0'), N(identity=control.baseline_native_request))


def test_runtime_wrapper_emits_policy_and_actual_assignment_through_original_custody(control, monkeypatch):
    backend, publications = Backend(), []
    config = N(config_id='config.exposed', SCHEMA='empirical-lawhood/battery-segmented/native-config', VERSION='1.0.0', fingerprint=lambda: '3' * 64)
    observation = N(configurations=(config,))
    # This exposed runtime double constructs no molecular/electrical model. It
    # exercises the exact wrapper-to-original-custody publication seam.
    def runtime(original_config, protocol, selected_backend):
        assert original_config is config
        return N(), selected_backend.IDAKLUSolver(**constructor())
    monkeypatch.setattr(sc.native, 'build_runtime', runtime)
    monkeypatch.setattr(sc, 'require_control', lambda *_: None)
    monkeypatch.setattr(sc.passive, '_publish', lambda progress, entry, name, record:
        publications.append((name, record)) or N(materialization=N(size_bytes=len(record.canonical_bytes()))))
    original = N(begin=lambda definition, inputs: N(definition=definition), contact=lambda entry: None)
    before = sc.native.build_observation_definition, sc.native.build_runtime
    with sc.native_control_scope(control, None, observation, original) as selected:
        main = selected.begin(N(operation_id='battery.segmented-observation.initial-window'))
        selected.contact(main)
        _, solver = sc.native.build_runtime(config, None, backend)
        assert solver.to_config()['options']['dt_max'] == 1.0
    assert before == (sc.native.build_observation_definition, sc.native.build_runtime)
    assert tuple(name for name, _ in publications) == ('internal-step-control', 'internal-step-assignment')
    assert publications[1][1].control is control
    assert selected.added_bytes == sum(len(record.canonical_bytes()) for _, record in publications)
