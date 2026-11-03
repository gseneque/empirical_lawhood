# SPDX-License-Identifier: MPL-2.0
"""Complete prospective operands and actual option joins; exposed software only."""
from dataclasses import replace
from decimal import Decimal as D
import json
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, durable_roster as dr
from empirical_lawhood.adapters.methods.battery_refined_inquiry import forecast_step_control as step
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_contracts as sc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import source_derived_preparation as roots
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from tests.test_battery_durable_roster import selected54 as original_selection
from tests.test_battery_internal_step_control import Backend, constructor


@pytest.fixture
def selected():
    original = dr.freeze_forecast_roster(*original_selection.__wrapped__())
    changed = step.prospective_selection(original, policy_id='policy.exposed-full-step',
        source_id='source.exposed-full-step', roster_id='roster.exposed-full-step')
    original_options = {'type': 'IDAKLUSolver', **constructor(),
        'options': {'calc_ic': True, 'jacobian': 'sparse'} | constructor()['options']}
    control = step.ForecastStepPolicy('step.exposed', step.identity(original, 'roster_id'), step.identity(changed, 'roster_id'),
        c.identity(changed.policy), step.ForecastComparisonBudget('budget.exposed', step.identity(changed, 'roster_id')),
        ObjectIdentity('assessment.exposed-precision', 'empirical-lawhood/battery-observation-inquiry/completed-precision-reassessment', '1.0.0', '2' * 64),
        tuple(ObjectIdentity('assessment.exposed-clock-' + str(n), 'empirical-lawhood/battery-segmented/representable-clock-assessment', '1.0.0', str(n) * 64) for n in (3, 4)),
        ObjectIdentity('request.exposed-original', step.native.SegmentRequest.SCHEMA, '1.0.0', '5' * 64),
        step._primitive(original_options))
    return original, changed, control


@pytest.fixture
def config(selected):
    selected_roster = selected[1]
    native = selected_roster.configurations[0]
    stock = 'Chen2020' if native.model_view == 'chen-spme' else 'ORegan2022'
    supplied = roots.supply_source_roots(c.identity(selected_roster.source), stock)
    return sc.SegmentedNativeConfig('config.exposed-full-step', native, supplied, roots.assess_source_roots(supplied),
        sc.SegmentedMethodProtocol('method.exposed-full-step', D(60)))


def witness(control, config):
    backend = Backend()
    view = step._BackendView(backend, control, config.native)
    original_kwargs = constructor() | {'rtol': float(config.rtol), 'atol': float(config.atol)}
    solver = view.IDAKLUSolver(**original_kwargs)
    assignment = step.ActualForecastStepAssignment('assignment.exposed-full-step', control,
        step.identity(config, 'config_id'), config.native.numerical_view, *view.assignment)
    return view, backend, assignment, solver


def test_complete_ladder_keeps_original54_36_scientific_operands(selected):
    original, changed, control = selected
    old_bytes = original.canonical_bytes()
    step.require_policy(control, original, changed)
    assert original.canonical_bytes() == old_bytes
    assert len(changed.configurations) == 54 and len(changed.comparison_config_pairs) == 36
    assert changed.policy.development_preparations == original.policy.development_preparations
    assert changed.policy.later_preparations == original.policy.later_preparations
    assert changed.source.original == original.source.original
    assert changed.source.source_members == original.source.source_members
    assert changed.source.diagnostic == original.source.diagnostic
    for old, new in zip(original.policy.views, changed.policy.views, strict=True):
        assert replace(new, rtol=old.rtol, atol=old.atol) == old
        assert (new.rtol, new.atol) == ((D('1e-11'), D('1e-12')) if new.view_id == 'dfn-tolerance' else (D('1e-9'), D('1e-10')))
    assert control.comparison_budget.rtol == D('1e-7') and control.comparison_budget.atol == D('1e-8')
    assert decode_canonical_bytes(control.canonical_bytes(), step.ForecastStepPolicy, maximum_bytes=None) == control


@pytest.mark.parametrize('damage', (
    {'maximum_internal_step_s': D('.5')}, {'scientific_horizon_s': D(60)},
    {'selected_forecast_slots': 48}, {'selected_reference_pairs': 35},
    {'fresh_physical_units': 1}, {'qualification': 'SATISFIED'},
    {'historical_completion': 'COMPLETED'}, {'scope': 'PHYSICALLY_QUALIFIED'},
))
def test_no_scope_denominator_horizon_or_unknown_clearance(selected, damage):
    with pytest.raises(ValueError):
        replace(selected[2], **damage)


@pytest.mark.parametrize('damage', ({'rtol': D('1e-9')}, {'atol': D('1e-10')}, {'derivative_time_scale_s': D(2)}))
def test_comparison_budget_stays_separate_and_unchanged(selected, damage):
    with pytest.raises(ValueError):
        replace(selected[2].comparison_budget, **damage)


def test_forged_control_and_changed_mesh_refuse_before_native_hooks(selected):
    original, changed, control = selected
    original_hooks = step.native.build_forecast_definition, step.native.build_runtime
    forged = replace(control, selected_numerical_policy=c.identity(original.policy))
    with pytest.raises(ValueError, match='prospective numerical policy'):
        with step.native_step_scope(forged, original, changed):
            pytest.fail('forged policy entered native wrapper')
    assert original_hooks == (step.native.build_forecast_definition, step.native.build_runtime)
    rows = tuple(replace(row, electrode_points=31) if row.view_id == 'chen-spme' else row for row in changed.policy.views)
    selection = replace(changed.policy.selection, views=rows)
    policy = replace(changed.policy, views=rows, protocol_sha256=selection.fingerprint())
    source = replace(changed.source, policy=c.identity(policy), protocol_sha256=selection.fingerprint())
    changed_mesh = replace(dr.freeze_forecast_roster(source, policy), roster_id=changed.roster_id)
    forged_mesh = replace(control, selected_roster=step.identity(changed_mesh, 'roster_id'), selected_numerical_policy=c.identity(policy),
        comparison_budget=replace(control.comparison_budget, selected_roster=step.identity(changed_mesh, 'roster_id')))
    with pytest.raises(ValueError, match='mesh'):
        step.require_policy(forged_mesh, original, changed_mesh)


def test_actual_assignment_keeps_selected_precision_and_every_option(selected, config):
    _, changed, control = selected
    step.require_config(control, changed, config)
    view, backend, assignment, solver = witness(control, config)
    assert assignment.numerical_view.rtol == D('1e-9')
    assert solver.to_config()['options']['dt_max'] == 1.0
    assert backend.calls[0]['rtol'] == 1e-9 and backend.calls[0]['atol'] == 1e-10
    assert decode_canonical_bytes(assignment.canonical_bytes(), type(assignment), maximum_bytes=None) == assignment
    with pytest.raises(ValueError, match='single'):
        view.IDAKLUSolver(**constructor())
    assert len(backend.calls) == 1


@pytest.mark.parametrize('changed', ('rtol', 'atol', 'dt_max', 'calc_ic', 'on_failure'))
def test_wrong_actual_options_and_hidden_native_precision_refuse(selected, config, changed):
    assignment = witness(selected[2], config)[2]
    document = json.loads(assignment.actual_solver_json)
    if changed in ('rtol', 'atol'):
        document[changed] = {'binary64': float(1e-7).hex()}
    elif changed == 'on_failure':
        document[changed] = 'ignore'
    else:
        document['options'][changed] = False if changed == 'calc_ic' else {'binary64': 2.0.hex()}
    with pytest.raises(ValueError, match='undeclared options'):
        replace(assignment, actual_solver_json=json.dumps(document))


def test_cost_preserves_nested_segment_scope_and_counts_extra_bytes_once(selected, monkeypatch):
    published, completed = [], []
    def publish(progress, entry, name, record):
        published.append(name)
        return N(materialization=N(size_bytes=len(record.canonical_bytes())))
    monkeypatch.setattr(step.passive, '_publish', publish)
    original = N(begin=lambda definition, inputs: N(definition=definition), contact=lambda entry: None,
        complete=lambda entry, **kwargs: completed.append(kwargs) or kwargs)
    progress = step._ControlledProgress(original, selected[2])
    main = progress.begin(N(operation_id='battery.segmented-native.forecast'))
    progress.contact(main)
    child = progress.begin(N(operation_id='battery.segmented-native.segment'))
    progress.contact(child)
    cost = InquiryCost(D(2), D(3), D(10))
    assert progress.complete(child, cost=cost)['cost'] == cost
    assert progress.complete(main, cost=cost)['cost'].retained_bytes == 10 + len(selected[2].canonical_bytes())
    assert published == ['forecast-step-policy'] and len(completed) == 2


def test_every_actual_request_options_and_full_policy_sources_are_checked(selected, config, monkeypatch):
    from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as stream
    assignment = witness(selected[2], config)[2]
    frame = object.__new__(stream.SegmentEvidenceFrame)
    object.__setattr__(frame, 'request', N(configuration=assignment.native_configuration,
        primitive_json=json.dumps({'solver': json.loads(assignment.actual_solver_json)})))
    object.__setattr__(frame, 'definition', N(sources=assignment.control.sources))
    original_reader = lambda port: iter((frame,))
    monkeypatch.setattr(stream, 'read_frames', original_reader)
    with step.request_step_scope((assignment,)):
        assert tuple(stream.read_frames(None)) == (frame,)
    object.__setattr__(frame, 'definition', N(sources=assignment.control.sources[:-1]))
    with pytest.raises(ValueError, match='complete solver options'):
        with step.request_step_scope((assignment,)):
            tuple(stream.read_frames(None))
    assert stream.read_frames is original_reader


@pytest.mark.parametrize('horizon', (D(60), D(30), D(15)))
def test_actual_definition_typed_roundtrip_full_outputs_sources_and_all_inputs(selected, config, horizon):
    from hashlib import sha256
    from empirical_lawhood.adapters.methods.battery_refined_inquiry.preparation_contracts import PreparationProtocol
    from empirical_lawhood.adapters.methods.battery_refined_inquiry.preparation_science import PREPARATION_SOURCE_MEMBERS
    from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
    original, changed, control = selected
    config = replace(config, method=sc.SegmentedMethodProtocol('method.exposed.' + str(horizon), horizon))
    sources = (('src/exposed-forecast-control.py', '6' * 64),)
    provenance = NumericalProducingProvenance('{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        '7' * 64, sources, sha256(canonical_json_bytes(sources)).hexdigest(), '8' * 40, False)
    protocol = PreparationProtocol('protocol.exposed-full-step', step.identity(config, 'config_id'), c.identity(changed.source),
        provenance.identity, 'Chen2020', 'SPMe', config.native.numerical_view.electrode_points,
        config.native.numerical_view.particle_points, config.initial_temperature_k, PREPARATION_SOURCE_MEMBERS)
    all_inputs = tuple('materialization.exposed-' + str(n) for n in range(20))
    parent = NativeEffectContact('run.exposed-full-step', 'task.exposed-full-step', 'attempt.exposed-full-step',
        ObjectIdentity('plan.exposed', 'empirical-lawhood/runtime/development-execution-plan', '1.0.0', '9' * 64),
        ObjectIdentity('task.exposed-full-step', 'empirical-lawhood/runtime/execution-task', '1.0.0', 'a' * 64),
        provenance.observed_git_head, tuple(sorted(all_inputs)), ())
    original_hooks = step.native.build_forecast_definition, step.native.build_runtime
    with step.native_step_scope(control, original, changed):
        definition = step.native.build_forecast_definition(config, protocol, provenance, N(parent_contact=parent), all_inputs)
        assert decode_canonical_bytes(definition.canonical_bytes(), NativeSubworkDefinition, maximum_bytes=None) == definition
        assert set(control.sources).issubset(definition.sources)
        assert definition.input_materialization_ids == tuple(sorted(all_inputs))
        assert {row.output_id for row in definition.outputs} == {row.output_id for row in step.native.forecast_outputs()} | {'forecast-step-policy', 'forecast-step-assignment'}
        assert definition.configuration == step.identity(config, 'config_id')
    assert original_hooks == (step.native.build_forecast_definition, step.native.build_runtime)


def test_retained_local_evidence_cannot_be_omitted_or_replaced_by_schema_id(selected):
    original, changed, control = selected
    with pytest.raises(ValueError, match='complete retained'):
        step.require_retained_evidence(control, original, changed, None, control.retained_clock_assessments, None, None)


def test_existing_roster_convention_keeps_distinct_content_and_original_exact_identity(selected):
    original, previous, previous_control = selected
    changed = step.prospective_selection(original, policy_id=previous.policy.policy_id,
        source_id=previous.source.source_id, roster_id=original.roster_id)
    control = replace(previous_control, selected_roster=step.identity(changed, 'roster_id'),
        comparison_budget=replace(previous_control.comparison_budget, selected_roster=step.identity(changed, 'roster_id')))
    step.require_policy(control, original, changed)
    assert control.original_roster.object_id == control.selected_roster.object_id
    assert control.original_roster != control.selected_roster and control.original_roster.object_fingerprint == original.fingerprint()
    assert len({row.object_id for row in control.sources}) == len(control.sources) == 8
    assert control.selected_roster in control.sources and control.original_roster not in control.sources
    with pytest.raises(ValueError, match='committed source and policy'):
        step.prospective_selection(original, policy_id=original.policy.policy_id, source_id=previous.source.source_id, roster_id=original.roster_id)


def test_actual_scheduler_identifies_controlled_forecast_native_interface(selected):
    from empirical_lawhood.infrastructure.execution import LocalScheduler, ResourceAdmissionError
    runner = step.ControlledSegmentedRunner(*selected[2:], selected[0], selected[1], None, None, None, None)
    with pytest.raises(ResourceAdmissionError, match='no selected native-effect parent'):
        object.__new__(LocalScheduler)._native_subwork_progress(runner, None, ())


def failed_assignment_evidence(selected, config, tmp_path):
    from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition, NativeSubworkOutput
    from tests.test_battery_segmented_fidelity import _receipt

    control = selected[2]
    inputs = ('materialization.exposed-input',)
    parent = NativeEffectContact('run.exposed-full-step', 'task.exposed-full-step', 'attempt.exposed-full-step',
        ObjectIdentity('plan.exposed', 'empirical-lawhood/runtime/development-execution-plan', '1.0.0', '9' * 64),
        ObjectIdentity('task.exposed-full-step', 'empirical-lawhood/runtime/execution-task', '1.0.0', 'a' * 64),
        '0' * 40, inputs, ())
    definition = NativeSubworkDefinition('native.exposed-step-failure', 'battery.exposed-step-failure', parent,
        step.identity(config, 'config_id'), tuple(sorted(control.sources, key=lambda row: row.object_id)),
        'b' * 64, 'c' * 64, inputs, (), tuple(sorted((
            NativeSubworkOutput('forecast-step-policy', step.ForecastStepPolicy.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json'),
            NativeSubworkOutput('forecast-step-assignment', step.ActualForecastStepAssignment.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json')),
            key=lambda row: row.output_id)))
    completion = NativeSubworkCompletion(definition.identity,
        ObjectIdentity('contact.exposed-step-failure', 'empirical-lawhood/runtime/native-subwork-contact', '1.0.0', 'd' * 64),
        OperationalStatus.FAILED, ('forecast-step-policy',), ('forecast-step-assignment',), (), (), (),
        InquiryCost(D(0), D(0), D(0)), 'EXPOSED_SOFTWARE_ONLY', None, ('known-pre-constructor-failure',))
    receipt = replace(_receipt(tmp_path / 'assignment-failure', (control, completion), inputs=inputs, definition=definition),
        operational_status=OperationalStatus.FAILED, reason_codes=('known-pre-constructor-failure',))
    return step.ForecastStepEvidence('evidence.exposed-step-failure', control, None, definition, completion, receipt)


def test_actual_known_failed_assignment_absence_is_retained_not_a_positive(selected, config, tmp_path):
    evidence = failed_assignment_evidence(selected, config, tmp_path)
    assert evidence.assignment is None
    assert decode_canonical_bytes(evidence.canonical_bytes(), type(evidence), maximum_bytes=None) == evidence
    assert evidence.original_native_completion.omitted_output_ids == ('forecast-step-assignment',)


@pytest.mark.parametrize('kind', ['successful-receipt', 'missing-omission', 'successful-completion', 'wrong-completion', 'unreceipted-policy'])
def test_assignment_absence_refuses_false_or_unauthed_failure(selected, config, tmp_path, kind):
    from empirical_lawhood.kernel.status import OperationalStatus
    evidence = failed_assignment_evidence(selected, config, tmp_path)
    with pytest.raises(ValueError):
        if kind == 'successful-receipt':
            replace(evidence, original_native_receipt=replace(evidence.original_native_receipt, operational_status=OperationalStatus.SUCCEEDED))
        elif kind == 'missing-omission':
            replace(evidence, original_native_completion=replace(evidence.original_native_completion, omitted_output_ids=()))
        elif kind == 'successful-completion':
            complete = replace(evidence.original_native_completion, operational_status=OperationalStatus.SUCCEEDED,
                omitted_output_ids=(), reason_codes=())
            replace(evidence, original_native_completion=complete)
        elif kind == 'wrong-completion':
            replace(evidence, original_native_completion=replace(evidence.original_native_completion,
                definition=ObjectIdentity('other.definition', evidence.original_native_definition.SCHEMA, '1.0.0', 'e' * 64)))
        else:
            replace(evidence, control=replace(evidence.control, policy_id='other.control'))


def context_fixture(selected, monkeypatch):
    """Isolate actual port integrity; retained scientific joins have separate controls."""
    from dataclasses import dataclass
    import io
    from empirical_lawhood.kernel.serialization import CanonicalRecord
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerOutputPort

    @dataclass(frozen=True)
    class ExposedPrecision(CanonicalRecord):
        SCHEMA = 'empirical-lawhood/battery-observation-inquiry/completed-precision-reassessment'
        assessment_id: str

    @dataclass(frozen=True)
    class ExposedClock(CanonicalRecord):
        SCHEMA = 'empirical-lawhood/battery-segmented/representable-clock-assessment'
        assessment_id: str

    @dataclass(frozen=True)
    class ExposedNegative(CanonicalRecord):
        SCHEMA = 'empirical-lawhood/battery-observation-inquiry/readout'
        readout_id: str

    @dataclass(frozen=True)
    class ExposedRequest(CanonicalRecord):
        SCHEMA = step.native.SegmentRequest.SCHEMA
        request_id: str

        @property
        def identity(self):
            return step.identity(self, 'request_id')

    original, changed, control = selected
    precision = ExposedPrecision('assessment.exposed-port-precision')
    clocks = tuple(ExposedClock('assessment.exposed-port-clock-' + str(n)) for n in (0, 1))
    negative, baseline = ExposedNegative('readout.exposed-port-negative'), ExposedRequest('request.exposed-port-baseline')
    operands = control, original, changed, precision, clocks, negative, baseline
    records = ((control, control.identity), (original, step.identity(original, 'roster_id')),
        (precision, step.identity(precision, 'assessment_id')), *((row, step.identity(row, 'assessment_id')) for row in clocks),
        (negative, step.identity(negative, 'readout_id')), (baseline, baseline.identity))
    ports = tuple(WorkerInputPort(WorkerInputBinding(identity.object_id, 'materialization.exposed-port-' + str(n),
        record.SCHEMA, 'application/json', len(record.canonical_bytes()), VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.DEVELOPMENT_VISIBLE, WorkerInputKind.EXTERNAL), io.BytesIO(record.canonical_bytes()))
        for n, (record, identity) in enumerate(records))
    outputs = (WorkerOutputPort('task.exposed-port.evidence', 'empirical-lawhood/battery-segmented/native-evidence', ArtifactProfile.CANONICAL_JSON, 'application/json'),
        WorkerOutputPort('task.exposed-port.segments', 'empirical-lawhood/battery-segmented-inquiry/segment-stream-chunk', ArtifactProfile.JSONL_CHUNKS, 'application/jsonl'),
        WorkerOutputPort('task.exposed-port.forecast-step-evidence', step.ForecastStepEvidence.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json'))
    monkeypatch.setattr(step, 'require_retained_evidence', lambda *args: None)
    return N(task_id='task.exposed-port', input_ports=ports, output_ports=outputs), operands


@pytest.mark.parametrize('compiled_order', (False, True))
def test_actual_extra_inputs_use_real_typed_ports_without_losing_materializations(selected, monkeypatch, compiled_order):
    context, operands = context_fixture(selected, monkeypatch)
    if compiled_order:
        context.output_ports = tuple(sorted(context.output_ports, key=lambda row: row.output_id))
    original_bindings = tuple(port.binding for port in context.input_ports)
    view, output, additional = step.controlled_context(context, *operands)
    assert view.input_ports == () and tuple(row.output_id for row in view.output_ports) == ('task.exposed-port.evidence', 'task.exposed-port.segments')
    assert output.payload_schema == step.ForecastStepEvidence.SCHEMA
    assert additional == tuple(port.materialization_id for port in context.input_ports)
    assert tuple(port.binding for port in context.input_ports) == original_bindings


@pytest.mark.parametrize('damage', ('missing-input', 'wrong-access', 'wrong-kind', 'wrong-size', 'wrong-bytes', 'unprefixed-output', 'wrong-profile', 'missing-output'))
def test_actual_additional_port_counterexamples_refuse_before_original_loader(selected, monkeypatch, damage):
    import io
    from empirical_lawhood.kernel.evidence import OutcomeAccess
    from empirical_lawhood.runtime.execution import WorkerInputKind
    context, operands = context_fixture(selected, monkeypatch)
    port = context.input_ports[0]
    if damage == 'missing-input':
        context.input_ports = context.input_ports[1:]
    elif damage == 'wrong-access':
        context.input_ports = (replace(port, binding=replace(port.binding, outcome_access=OutcomeAccess.OUTCOME_BLIND)), *context.input_ports[1:])
    elif damage == 'wrong-kind':
        context.input_ports = (replace(port, binding=replace(port.binding, kind=WorkerInputKind.DEPENDENCY)), *context.input_ports[1:])
    elif damage == 'wrong-size':
        context.input_ports = (replace(port, binding=replace(port.binding, size_bytes=port.size_bytes + 1)), *context.input_ports[1:])
    elif damage == 'wrong-bytes':
        context.input_ports = (replace(port, _reader=io.BytesIO(b'{}')), *context.input_ports[1:])
    elif damage == 'missing-output':
        context.output_ports = context.output_ports[:-1]
    else:
        output = context.output_ports[-1]
        changed = replace(output, output_id='forecast-step-evidence') if damage == 'unprefixed-output' else replace(output, profile=ArtifactProfile.JSONL_CHUNKS)
        context.output_ports = (*context.output_ports[:-1], changed)
    with pytest.raises(ValueError):
        step.controlled_context(context, *operands)
