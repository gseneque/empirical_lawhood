# SPDX-License-Identifier: MPL-2.0
"""Original custody, complete input boundaries and recovery with exposed forces."""
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes

from dataclasses import fields, replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import zlib

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import gas_relaxation_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import gas_relaxation_native as native
from empirical_lawhood.domains.rubisco.rubisco_response import gas_relaxation_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response import gas_relaxation_translation as graph
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.execution.capabilities import CapabilityConfigRef
from empirical_lawhood.execution.execution import TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.execution.native_subwork import NativeSubworkState, NativeSubworkObservationPublicationError
from empirical_lawhood.execution.recursive_handoff import RecursiveImplementationBinding
from empirical_lawhood.execution.local.native_subwork_inputs import validate_native_subwork_inputs
from empirical_lawhood.execution.local.execution import prepare_worker_invocation

from tests.runtime_platform.test_native_subwork import _plane, _store
from tests.runtime_platform.test_worker_preflight import _original_task
from tests.test_rubisco_gas_relaxation import exposed_operator, gas_input  # noqa: F401
from tests.test_rubisco_periodic_probe_operation import THREADS


@pytest.fixture
def fixture(gas_input, tmp_path, monkeypatch):  # noqa: F811
    for name in THREADS:
        monkeypatch.setenv(name, '1')
    package = (('src/exposed_gas_relaxation.py', '4'*64),)
    digest = sha256(canonical_json_bytes(package)).hexdigest()
    implementation = RecursiveImplementationBinding(package, digest, '5'*64, '3'*40, False)
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        '5'*64, package, digest, '3'*40, False)
    sources = owner.prepare_raw_sources(gas_input.selection.prototype, gas_input.raw_top, gas_input.raw_xyz)
    config = owner.GasRelaxationConfig('config.exposed.gas-relaxation', gas_input.selection, sources.identity,
        gas_input.model.canonical_size_bytes(), sources.canonical_size_bytes(), implementation, str(tmp_path/'working'), provenance)
    result = SimpleNamespace(item=gas_input, config=config, sources=sources, tmp_path=tmp_path, contexts=[])
    yield result
    for context in result.contexts:
        for port in context.input_ports:
            port.close()


def custody(fixture):
    config = fixture.config
    capability = owner.capability_for(config)
    plane = _plane(fixture.tmp_path/'custody')
    records = (('config', config.identity, config), *owner.native_input_records(config, fixture.item.model, fixture.sources))
    manifests = []
    for name, pin, record in records:
        written = plane.write(ArtifactWriteRequest(pin.object_id, 'inputs/'+name+'.json', record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'inputs.exposed.gas-relaxation', 'inputs', record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifests.append(resolve_artifact_sidecar_bytes(plane, plane.root.resolve(written.materialization.relative_path + '.manifest.json', for_write=False).read_bytes()))
    manifests = tuple(sorted(manifests, key=lambda m: m.materialization.materialization_id))
    verified = tuple(sorted((VerifiedArtifactInput(m.logical, m.materialization) for m in manifests), key=lambda r: r.artifact_id))
    bindings = tuple(WorkerInputBinding.from_verified(row, kind=WorkerInputKind.EXTERNAL) for row in verified)
    by_id = {m.logical.logical_artifact_id: m for m in manifests}

    def ports():
        return tuple(plane.open(by_id[b.artifact_id], binding=b, maximum_bytes=b.size_bytes) for b in bindings)

    manifest = owner.operation_declaration(accelerated=config.ACCELERATED).manifest()
    context = TaskContext('exposed.gas', capability, 'exposed.gas.'+capability+'.attempt-001',
        CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config.identity.object_id),
        bindings, ports(), (WorkerOutputPort(capability+'.product', owner.GasRelaxationResult.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'logical.exposed.gas-relaxation-product'),),
        manifest.permissions, OutcomeAccess.DEVELOPMENT_VISIBLE, owner.resource_budget(config), WorkerIsolationProfile.TRUSTED_LOCAL,
        accelerated_compute=config.ACCELERATED)
    runner = owner.GasRelaxationRunner(accelerated=config.ACCELERATED)
    task = _original_task(runner, context, SimpleNamespace(verified_inputs=verified))
    plan = ObjectIdentity('plan.exposed.gas', 'empirical-lawhood/runtime/development-execution-plan', '1.0.0', '1'*64)
    contract = prepare_worker_invocation(runner, context, verified, implementation=config.implementation,
        execution_plan=plan, execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task,
        native_effect=True, native_work_preparer=owner.prepare_native_work)
    assert contract.native_preparation_error is None
    context = replace(context, prepared_invocation=contract); fixture.contexts.append(context)
    store = _store(plane, contract.expected_parent_contact, manifests, prepared_invocation=contract)
    store.parent_contacts.begin(contract.expected_parent_contact)

    def fresh():
        value = replace(context, input_ports=ports()); fixture.contexts.append(value)
        return value

    return SimpleNamespace(plane=plane, context=context, work=contract.native_work, store=store, manifests=manifests, fresh=fresh)


def test_all_original_inputs_and_one_native_attempt_are_frozen_without_preflight(fixture, monkeypatch):
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k: pytest.fail('native prerequisite inspected by authoring'))
    c = custody(fixture)
    assert owner._decode(c.context) == (fixture.config, fixture.item.model, fixture.sources)
    assert len(c.work.definitions) == len(c.work.rosters) == 1
    validate_native_subwork_inputs(c.plane, c.work.definitions[0], c.manifests,
        visibility=VisibilityCeiling.DEVELOPMENT_ONLY, access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    draft = graph.gas_relaxation_draft(fixture.config)
    assert draft.development_study.assigned_unit_ids == (owner.UNIT,)
    assert len(draft.external_inputs) == 5 and len(draft.operations) == 1
    assert owner.resource_budget(fixture.config).wall_time_seconds is None
    assert c.store.inspect(c.work.definitions[0]).state is NativeSubworkState.NOT_ENTERED


@pytest.mark.parametrize('platform', ('CUDA', 'Reference'))
def test_gpu_selection_retains_actual_allocation_and_rejects_implicit_cpu_fallback(fixture, platform, monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import prepare_periodic_probe_selection
    from tests.test_rubisco_accelerated_compute import gpu_engine

    original = fixture.config.selection.prototype
    engine = gpu_engine(original.engine, molecular_platform=platform)
    prototype = prepare_periodic_probe_selection(representation=fixture.item.model, path=original.path, cell=original.cell,
        electronic=original.electronic, molecular=original.molecular, engine=engine)
    selection = replace(fixture.config.selection, prototype=prototype)
    fixture.config = owner.AcceleratedGasRelaxationConfig(**{field.name: selection if field.name == 'selection'
        else getattr(fixture.config, field.name) for field in fields(owner.GasRelaxationConfig)})
    assert owner.resource_budget(fixture.config).gpu_devices == 1
    assert owner.resource_budget(fixture.config).memory_bytes == engine.host_memory_bytes
    assert graph.gas_relaxation_draft(fixture.config).operations[0].node_id == owner.GPU_CAPABILITY
    c = custody(fixture)
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k: pytest.fail('CPU fallback reached engine inspection'))
    with pytest.raises(ValueError, match='accelerated_compute'):
        owner.GasRelaxationRunner(accelerated=True).preflight(replace(c.context, accelerated_compute=False))
    assert c.store.inspect(c.work.definitions[0]).state is NativeSubworkState.NOT_ENTERED


@pytest.mark.parametrize('changed', ('size', 'source', 'missing-port', 'accelerated'))
def test_changed_native_operands_refuse_before_contact(fixture, changed):
    if changed == 'size':
        with pytest.raises(ValueError, match='complete original'):
            owner.native_input_records(replace(fixture.config, representation_size_bytes=1), fixture.item.model, fixture.sources)
    elif changed == 'source':
        with pytest.raises(ValueError, match='complete original'):
            owner.native_input_records(fixture.config, fixture.item.model,
                replace(fixture.sources, coordinates_utf8=fixture.sources.coordinates_utf8+'\n'))
    else:
        c = custody(fixture)
        with pytest.raises(ValueError):
            if changed == 'missing-port':
                owner._decode(replace(c.context, input_ports=c.context.input_ports[:-1]))
            else:
                owner.GasRelaxationRunner().preflight(replace(c.context, accelerated_compute=True))
        assert c.store.inspect(c.work.definitions[0]).state is NativeSubworkState.NOT_ENTERED


@pytest.mark.parametrize('failure', (None, 'native-error'))
def test_original_success_and_failure_are_recovered_and_read_without_replay(fixture, monkeypatch, failure):
    c = custody(fixture)
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k: None)
    operators = exposed_operator(monkeypatch, fixture.item.coordinates, failure=failure)
    runner = owner.GasRelaxationRunner()
    first = runner.execute_with_native_subwork(c.context, c.store)
    result = decode_canonical_bytes(first.outputs[0].payload, owner.GasRelaxationResult, maximum_bytes=16*2**20)
    assert len(operators) == 1 and operators[0].calls == (2 if failure is None else 1)
    expected_status = OperationalStatus.SUCCEEDED if failure is None else OperationalStatus.FAILED
    assert result.completion.operational_status is expected_status
    completion = c.store.recover(result.definition)
    assert completion.call_entry is not None and completion.call_return is not None
    assert result.completion.cost.retained_bytes == sum(m.materialization.size_bytes for m in completion.outputs)
    monkeypatch.setattr(native, 'execute_gas_relaxation', lambda **kw: pytest.fail('completed native attempt replayed'))
    second = runner.execute_with_native_subwork(c.fresh(), c.store)
    assert second.outputs[0].payload == first.outputs[0].payload
    readout = retained.read_relaxation(config=fixture.config, representation=fixture.item.model, original_result=result,
        native_subwork=c.store, assessor_source=fixture.item.model.material.sources[0], readout_id='readout.exposed.gas')
    assert readout.assessment_error is None
    assert (readout.assessment is None) == (failure is not None)
    if readout.assessment is not None:
        assert readout.assessment.complete_reference_evaluations == 2
        assert readout.assessment.rate_admission == 'UNEVALUABLE'
    assert decode_canonical_bytes(readout.canonical_bytes(), type(readout), maximum_bytes=16*2**20) == readout
    original = c.store.iter_completed_output

    def corrupt(definition, key, **kwargs):
        return iter((b'CHANGED ORIGINAL ARCHIVE',)) if key == 'files.raw' else original(definition, key, **kwargs)

    monkeypatch.setattr(c.store, 'iter_completed_output', corrupt)
    with pytest.raises((ValueError, zlib.error)):
        retained.read_relaxation(config=fixture.config, representation=fixture.item.model, original_result=result,
            native_subwork=c.store, assessor_source=fixture.item.model.material.sources[0], readout_id='readout.exposed.corrupt-gas')


@pytest.mark.parametrize('entered', (False, True))
def test_unknown_or_unacknowledged_native_attempt_is_never_replayed(fixture, monkeypatch, entered):
    c = custody(fixture); calls = []
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k: None)

    def execute(**kwargs):
        calls.append('EXPOSED_NATIVE_CALLBACK')
        return {}

    monkeypatch.setattr(native, 'execute_gas_relaxation', execute)
    if entered:
        def refuse(*a, **k):
            raise OSError('exposed observation-publication failure')
        monkeypatch.setattr(c.store, 'call_return', refuse)
        expected = NativeSubworkObservationPublicationError
    else:
        c.store.freeze_roster(c.work.rosters[0], definitions=c.work.definitions)
        entry = c.store.begin(c.work.definitions[0]); c.store.contact(entry)
        expected = ValueError
    with pytest.raises(expected):
        owner.GasRelaxationRunner().execute_with_native_subwork(c.context, c.store)
    assert len(calls) == int(entered)
    assert c.store.inspect(c.work.definitions[0]).state is NativeSubworkState.UNKNOWN_COMPLETION


def test_public_author_publishes_exact_inputs_and_returns_existing_lifecycle_paths(fixture, monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import gas_relaxation as public

    plane = _plane(fixture.tmp_path/'public-custody')
    project = fixture.tmp_path/'project'; project.mkdir()
    output = Path(plane.root.contract.canonical_path)/'authored'
    calls = []
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda root: fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **kw: fixture.config.provenance)

    def author(**kwargs):
        calls.append(kwargs)
        assert len(kwargs['input_bindings']) == len(kwargs['draft'].external_inputs) == 5
        return {'authoring_dir': str(output)}

    monkeypatch.setattr(recursive_authoring, 'author_recursive_wave', author)
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k: pytest.fail('public author contacted native engine'))
    result = public.author_gas_relaxation(selection=fixture.item.selection, representation=fixture.item.model,
        raw_topology=fixture.item.raw_top, raw_coordinates=fixture.item.raw_xyz, project_root=project,
        work_directory=fixture.tmp_path/'future-native', artifact_writer=plane, output_dir=output)
    assert len(calls) == 1 and result['authoring_dir'] == str(output)
    assert len(result['native_input_paths']) == 5
    for external in calls[0]['draft'].external_inputs:
        path = Path(result['native_input_paths'][external.input_id])
        assert path.is_file()
