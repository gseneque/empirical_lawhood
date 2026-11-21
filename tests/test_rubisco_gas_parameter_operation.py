# SPDX-License-Identifier: MPL-2.0
"""Real native custody over exposed literal topologies; no physical evidence."""
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import gas_parameter_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response.gas_parameter_records import GasParameterEngine, GasParameterSource, authenticate_gas_parameter_engine, prepare_gas_parameter_source
from empirical_lawhood.domains.rubisco.rubisco_response.gas_parameter_translation import gas_parameter_draft
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.api.domain_composition.rubisco_response.gas_parameters import read_gas_parameter_pair
from empirical_lawhood.execution.local.execution import prepare_worker_invocation

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.execution.capabilities import CapabilityConfigRef
from empirical_lawhood.execution.execution import TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.execution.native_subwork import NativeSubworkObservationPublicationError, NativeSubworkState
from empirical_lawhood.execution.recursive_handoff import RecursiveImplementationBinding
from tests.runtime_platform.test_native_subwork import _plane, _store
from tests.runtime_platform.test_worker_preflight import _original_task
from tests.test_rubisco_geometry_repair import numeric_engine
from tests.test_rubisco_gas_stock import _stock
from tests.test_rubisco_gas_topology import FIXTURES


@pytest.fixture
def case(tmp_path):
    numeric = numeric_engine(tmp_path/'stock')
    path = Path(numeric.site_packages)/'parmed/exposed.txt'
    path.parent.mkdir()
    path.write_bytes(b'EXPOSED NONEXECUTABLE STOCK CONTROL\n')
    engine = GasParameterEngine(numeric, (FileEvidence('parmed/exposed.txt', path.stat().st_size,
        sha256(path.read_bytes()).hexdigest()),))
    raw = (FIXTURES/'host.prmtop').read_bytes()
    pin = ObjectIdentity('source.exposed-topology', 'empirical-lawhood/testing/exposed-topology', '1.0.0', sha256(raw).hexdigest())
    source = prepare_gas_parameter_source(topology=pin, original_topology_bytes=raw,
        stocks=(_stock('CO2'), _stock('O2')), engine=engine)
    package = (('src/exposed_gas_parameter_control.py', '4'*64),)
    digest = sha256(canonical_json_bytes(package)).hexdigest()
    implementation = RecursiveImplementationBinding(package, digest, '5'*64, '3'*40, False)
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        '5'*64, package, digest, '3'*40, False)
    config = owner.GasParameterConfig('config.exposed-gas-parameters', source.identity, source.canonical_size_bytes(),
        implementation, provenance, str(tmp_path/'working'))
    value = SimpleNamespace(source=source, config=config, tmp_path=tmp_path, contexts=[])
    yield value
    for context in value.contexts:
        for port in context.input_ports:
            port.close()


def custody(case):
    plane = _plane(case.tmp_path/'custody')
    records = (case.config, case.source, case.config.provenance)
    manifests = []
    for i, record in enumerate(records):
        pin = record.identity
        relative = 'inputs/input-'+str(i)+'.json'
        plane.write(ArtifactWriteRequest(pin.object_id, relative, pin.object_schema, ArtifactProfile.CANONICAL_JSON,
            'application/json', 'inputs.exposed-gas', 'inputs', record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifests.append(resolve_artifact_sidecar_bytes(plane, plane.root.resolve(relative + '.manifest.json', for_write=False).read_bytes()))
    manifests = tuple(sorted(manifests, key=lambda row: row.materialization.materialization_id))
    verified = tuple(sorted((VerifiedArtifactInput(row.logical, row.materialization) for row in manifests), key=lambda row: row.artifact_id))
    bindings = tuple(WorkerInputBinding.from_verified(row, kind=WorkerInputKind.EXTERNAL) for row in verified)
    by_id = {row.logical.logical_artifact_id: row for row in manifests}
    def ports():
        return tuple(plane.open(by_id[b.artifact_id], binding=b, maximum_bytes=b.size_bytes) for b in bindings)
    manifest = owner.operation_declaration().manifest()
    context = TaskContext('exposed.gas', owner.CAPABILITY, 'exposed.gas.'+owner.CAPABILITY+'.attempt-001',
        CapabilityConfigRef(case.config.config_id, case.config.SCHEMA, manifest.config_schema_sha256,
            case.config.fingerprint(), case.config.identity.object_id), bindings, ports(),
        (WorkerOutputPort(owner.CAPABILITY+'.product', owner.GasParameterPairResult.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            'application/json', 'logical.exposed.gas-product'),), manifest.permissions, OutcomeAccess.DEVELOPMENT_VISIBLE,
        owner.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL)
    runner = owner.GasParameterRunner()
    task = _original_task(runner, context, SimpleNamespace(verified_inputs=verified))
    plan = ObjectIdentity('plan.exposed', 'empirical-lawhood/runtime/development-execution-plan', '1.0.0', '1'*64)
    contract = prepare_worker_invocation(runner, context, verified, implementation=case.config.implementation,
        execution_plan=plan, execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task,
        native_effect=True, native_work_preparer=owner.prepare_native_work)
    assert contract.native_preparation_error is None
    context = replace(context, prepared_invocation=contract)
    case.contexts.append(context)
    store = _store(plane, contract.expected_parent_contact, manifests, prepared_invocation=contract)
    store.parent_contacts.begin(contract.expected_parent_contact)
    def fresh():
        result = replace(context, input_ports=ports())
        case.contexts.append(result)
        return result
    return SimpleNamespace(plane=plane, context=context, store=store, work=contract.native_work, fresh=fresh)


@pytest.mark.parametrize('change', ('extra', 'missing', 'bytes', 'link'))
def test_parmed_file_census_is_authenticated_without_native_imports(case, change):
    engine = case.source.engine
    authenticate_gas_parameter_engine(engine)
    path = Path(engine.numeric.site_packages)/'parmed/exposed.txt'
    if change == 'extra': (path.parent/'extra.txt').write_text('extra')
    elif change == 'missing': path.unlink()
    elif change == 'bytes': path.write_text('changed')
    else:
        path.unlink()
        path.symlink_to(Path(engine.numeric.site_packages)/'numpy/exposed.txt')
    with pytest.raises((ValueError, OSError)):
        authenticate_gas_parameter_engine(engine)


def test_source_requires_both_gases_and_exact_original_topology(case):
    for changes in ({'stocks': case.source.stocks[:1]}, {'stocks': case.source.stocks[::-1]},
            {'topology_ascii': case.source.topology_ascii+'\n'}):
        with pytest.raises(ValueError):
            replace(case.source, **changes)
    assert decode_canonical_bytes(case.source.canonical_bytes(), GasParameterSource, maximum_bytes=2**20) == case.source


def test_cold_registration_and_graph_need_no_engine_or_output_contact(case, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('cold metadata entered native work')
    monkeypatch.setattr(owner, 'authenticate_gas_parameter_engine', forbidden)
    monkeypatch.setattr(owner, '_construct', forbidden)
    declaration = owner.operation_declaration()
    draft = gas_parameter_draft(case.config)
    assert declaration.execution_properties.native_effect and declaration.resources.gpu_devices == 0
    assert declaration.resources.wall_time_seconds is None and len(draft.external_inputs) == 2
    assert draft.development_study.assigned_unit_ids == (owner.UNIT,)
    assert not Path(case.config.work_directory).exists()


@pytest.mark.parametrize('failed', (False, True))
def test_original_returns_survive_failures_and_independent_reads_never_reenter(case, monkeypatch, failed):
    c = custody(case)
    calls = []
    def construct(source, stock, directory):
        calls.append(stock.gas)
        (directory/'gas.prmtop').write_bytes((FIXTURES/(stock.gas.lower()+'.prmtop')).read_bytes())
        if failed and stock.gas == 'CO2':
            raise RuntimeError('exposed construction failure after raw return')
    monkeypatch.setattr(owner, '_construct', construct)
    result = owner.GasParameterRunner().execute_with_native_subwork(c.context, c.store)
    original = decode_canonical_bytes(result.outputs[0].payload, owner.GasParameterPairResult, maximum_bytes=2**20)
    assert calls == ['CO2', 'O2'] and tuple(row.returned.gas for row in original.units) == ('CO2', 'O2')
    for i, unit in enumerate(original.units):
        completed = c.store.recover(unit.definition)
        assert completed.call_entry is not None and completed.call_return is not None
        assert unit.completion.cost.cpu_seconds is not None and unit.completion.cost.wall_seconds is not None
        assert owner.read_gas_parameter_files(c.store, unit.definition, unit.returned)['gas.prmtop'] == (
            FIXTURES/(unit.returned.gas.lower()+'.prmtop')).read_bytes()
        assert unit.completion.operational_status is (OperationalStatus.FAILED if failed and i == 0 else OperationalStatus.SUCCEEDED)
        assert (unit.assessment_json is None) == (failed and i == 0)
    def forbidden(*args, **kwargs):
        pytest.fail('original native work was replayed')
    monkeypatch.setattr(owner, '_construct', forbidden)
    repeated = owner.GasParameterRunner().execute_with_native_subwork(c.fresh(), c.store)
    assert repeated.outputs == result.outputs
    assert read_gas_parameter_pair(source=case.source, original_result=original, native_subwork=c.store) == original


def test_raw_custody_precedes_negative_parameter_assessment(case, monkeypatch):
    c = custody(case)
    def construct(source, stock, directory):
        (directory/'gas.prmtop').write_bytes(b'EXPOSED MALFORMED RETURN RETAINED BEFORE PARSING\n')
    monkeypatch.setattr(owner, '_construct', construct)
    output = owner.GasParameterRunner().execute_with_native_subwork(c.context, c.store)
    original = decode_canonical_bytes(output.outputs[0].payload, owner.GasParameterPairResult, maximum_bytes=2**20)
    assert all(unit.completion.operational_status is OperationalStatus.SUCCEEDED for unit in original.units)
    assert all(unit.assessment_json is None and unit.assessment_error for unit in original.units)
    assert all(owner.read_gas_parameter_files(c.store, unit.definition, unit.returned)['gas.prmtop'].startswith(b'EXPOSED')
        for unit in original.units)


@pytest.mark.parametrize('boundary', ('contact', 'return-observation'))
def test_uncertain_native_completion_cannot_be_replayed_or_promoted(case, monkeypatch, boundary):
    c = custody(case)
    calls = []
    def construct(source, stock, directory):
        calls.append(stock.gas)
        (directory/'gas.prmtop').write_bytes(b'EXPOSED ORIGINAL')
    monkeypatch.setattr(owner, '_construct', construct)
    if boundary == 'contact':
        c.store.freeze_roster(c.work.rosters[0], definitions=c.work.definitions)
        entry = c.store.begin(c.work.definitions[0])
        c.store.contact(entry)
    else:
        def refuse(*args, **kwargs):
            raise OSError('exposed lost call-return observation')
        monkeypatch.setattr(c.store, 'call_return', refuse)
    with pytest.raises((ValueError, NativeSubworkObservationPublicationError)):
        owner.GasParameterRunner().execute_with_native_subwork(c.context, c.store)
    assert calls == ([] if boundary == 'contact' else ['CO2'])
    assert c.store.inspect(c.work.definitions[0]).state is NativeSubworkState.UNKNOWN_COMPLETION
    assert c.store.inspect(c.work.definitions[1]).state is NativeSubworkState.NOT_ENTERED


def test_parameter_library_return_survives_postcall_stock_refusal(case, monkeypatch):
    directory = case.tmp_path/'literal-return'
    directory.mkdir()
    monkeypatch.setattr(owner, 'append_gas_parameter_tables', lambda **kwargs: b'EXPOSED COMPLETE NATIVE RETURN')
    def refuse(*args, **kwargs):
        raise ValueError('exposed loaded-stock mismatch')
    monkeypatch.setattr(owner, 'authenticate_gas_parameter_engine', refuse)
    with pytest.raises(ValueError, match='loaded-stock'):
        owner._construct(case.source, case.source.stocks[0], directory)
    assert (directory/'gas.prmtop').read_bytes() == b'EXPOSED COMPLETE NATIVE RETURN'
