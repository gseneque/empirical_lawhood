# SPDX-License-Identifier: MPL-2.0
"""Exposed recovery controls with real receipts/events and a disclosed input seam.

The three-task arithmetic graph supplies no E4 result or native authority.
Only its companion/source lookup is substituted. The primary failure census,
control-byte guards, terminal reconciliation and source comparisons are real.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import development_structure_repair as owner
from empirical_lawhood.api.recursive_execution import _external_inputs
from empirical_lawhood.infrastructure.execution import DirectTaskExecutor, LocalScheduler, TaskProcessError
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec
from empirical_lawhood.runtime.artifacts import ReceiptCheck
from empirical_lawhood.runtime.development_structure_repair import DevelopmentStructureRepair
from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, RunnerRegistry, RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.plans import PlanLane
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
from tests.runtime_platform.test_execution_scheduler import StaticExternalInputResolver
from tests.runtime_platform.test_recursive_compiler import Config, UseConfig, fixture
from tests.test_development_output_repair import _sources
from tests.test_recursive_public_service import ROOT, _plane


def _source_changed(source, path, digest='f' * 64):
    rows = dict(source.package_sources)
    rows[path] = digest
    rows = tuple(sorted(rows.items()))
    return replace(source, package_sources=rows, code_sources_sha256=sha256(canonical_json_bytes(rows)).hexdigest())


def _graph():
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_bindings import key
    draft, registrations, registry = fixture()
    tail = replace(registrations[1], selection=replace(registrations[1].selection, capability_key='generic.tail'))
    operation = RecursiveOperationSpec.from_config(node_id='tail', selection=tail.selection,
        config_id='config.tail', config=UseConfig('config.tail', 3), obligation_ids=('obligation.tail',),
        resource_budget=tail.resource_ceiling)
    requirement = replace(draft.requirements[0], requirement_id='requirement.tail',
        consumer_operation_id='tail', assessment_operation_id='tail')
    connection = replace(draft.connections[0], connection_id='connection.tail', requirement_id=requirement.requirement_id,
        supplier_operation_id='use', assessment_operation_id='tail')
    link = replace(draft.links[0], edge_id='edge.tail', consumer_node_id='tail', producer_node_id='use',
        requirement_id=requirement.requirement_id, connection_id=connection.connection_id)
    rename = {'generic.source':key(False, 'measure'), 'generic.use':key(False, 'assess'), 'generic.tail':key(False, 'reduce')}
    registrations = tuple(replace(row, selection=replace(row.selection, capability_key=rename[row.selection.capability_key]))
        for row in (*registrations, tail))
    manifests = (*registry.capabilities, replace(registry.capabilities[1], capability_key='generic.tail'))
    registry = replace(registry, capabilities=tuple(sorted((replace(row, capability_key=rename[row.capability_key])
        for row in manifests), key=lambda row:row.registry_id)))
    operations = tuple(replace(row, selection=replace(row.selection, capability_key=rename[row.selection.capability_key]))
        for row in (*draft.operations, operation))
    draft = replace(draft, requirements=(*draft.requirements, requirement), connections=(*draft.connections, connection),
        links=(*draft.links, link), operations=tuple(sorted(operations, key=lambda row:row.node_id)),
        selected_operation_ids=('source', 'tail', 'use'))
    return draft, registrations, registry


class _LiteralRunner:
    def __init__(self, manifest, failure):
        self.manifest, self.failure = manifest, failure

    def execute(self, context):
        try:
            for port in context.input_ports:
                port.read()
            if context.task_id == ('use' if self.failure == 'partial-success' else 'source') and self.failure:
                error = TypeError if self.failure == 'other-error' else ValueError
                raise error('Disclosed structural software failure; no native evidence')
            value = Config('literal.' + context.task_id, 3)
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, value.canonical_bytes()),),
                (ReceiptCheck('disclosed-arithmetic-only', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


class _TransportFixtureExecutor(DirectTaskExecutor):
    """Exercise the real process-error envelope without a spawned native worker."""
    def execute(self, runner, context, *, timeout_seconds):
        try:
            return super().execute(runner, context, timeout_seconds=timeout_seconds)
        except (ValueError, TypeError) as error:
            raise TaskProcessError('disclosed child failure', child_exception_type=type(error).__name__,
                child_message=str(error)) from error


@pytest.fixture
def failed_structure(tmp_path, monkeypatch, request):
    from empirical_lawhood.api import experiment_execution_read
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_preparation import ScheduledFullFactorDevelopmentSpecification
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import SelectedE3E4ExperimentSpecification
    draft, registrations, registry = _graph()
    plane = _plane(tmp_path / 'disclosed-structural-repair')
    original, replacement = _sources()
    directory = Path(plane.root.contract.canonical_path) / 'development'
    access_state = {'revoked':False}
    def current():
        if access_state['revoked']:
            raise PermissionError('disclosed original permission revoked')
    access = SimpleNamespace(require_current=current)
    def produce(run_id, failure, specification_kind):
        compiled = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
            implementation_commit=original.observed_git_head, run_plan_id=run_id, output_codecs={Config.SCHEMA:Config})
        plan, run = compiled.execution_plan, compiled.run_plan
        inputs = _external_inputs(plane=plane, plan=plan, draft=draft,
            payloads={value.config_id:value.payload for value in compiled.config_inputs}, read_only=False)
        index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run_id, wave_id='wave.development')
        recovery, receipts = ExternalRunRecoveryStore(plane), ExternalTaskReceiptStore(plane)
        engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
        upgrade_catalog(engine)
        scheduler = LocalScheduler(operational_repository=SQLiteOperationalRepository(engine), artifact_writer=plane,
            receipt_store=receipts, recovery_index=index, recovery_store=recovery,
            runner_registry=RunnerRegistry(tuple(_LiteralRunner(manifest, failure) for manifest in registry.capabilities),
                registry_sha256=registry.fingerprint()), implementation_commit=original.observed_git_head,
            external_input_resolver=StaticExternalInputResolver(inputs), executor=_TransportFixtureExecutor(),
            input_port_factory=plane, lane=PlanLane.DEVELOPMENT, authorized_barriers=(),
            assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL)
        try:
            result = scheduler.execute(run_id, plan)
        finally:
            engine.dispose()
        draft_pin = ObjectIdentity.from_record(draft.draft_id, draft)
        source_pin = ObjectIdentity.from_record('recursive-member.implementation', original)
        # Explicit companion lookup seam: this fixture is not an E4 programme.
        spec_pin = ObjectIdentity('specification.disclosed', specification_kind.SCHEMA, specification_kind.VERSION, 'c' * 64)
        packet = AuthoredRecursiveWave('packet.' + run_id, draft_pin, source_pin, (
            RecursiveWaveMember('draft.json', draft_pin, len(draft.canonical_bytes())),
            RecursiveWaveMember('experiment-specification.json', spec_pin, 1),
            RecursiveWaveMember('implementation.json', source_pin, len(original.canonical_bytes()))))
        return (packet, run, plan, index, original, access), result
    acquisition, acquired = produce('run.disclosed.acquisition', None, SelectedE3E4ExperimentSpecification)
    mode = getattr(request, 'param', 'value-error')
    structural, failed = produce('run.disclosed.structure', mode, ScheduledFullFactorDevelopmentSpecification)
    assert acquired.status is OperationalStatus.SUCCEEDED and failed.status is OperationalStatus.FAILED
    def controls(*, directory:Path, **kwargs):
        return structural if Path(directory).name == 'analysis' else acquisition
    monkeypatch.setattr(experiment_execution_read, 'load_development_execution_controls', controls)
    monkeypatch.setattr('empirical_lawhood.api.recursive_operations.operation_catalog', lambda:(registrations, registry, {}))
    return SimpleNamespace(plane=plane, directory=directory, acquisition=acquisition, structural=structural,
        original=original, replacement=replacement, access_state=access_state)


def test_structural_repair_binds_complete_primary_census_and_roundtrips(failed_structure):
    case = failed_structure
    observed = owner._original_controls(writer=case.plane, directory=case.directory)
    proof = owner._selection(case.plane, case.directory, observed,
        instruction_sha256='d' * 64, replacement=case.replacement)
    assert decode_canonical_bytes(proof.canonical_bytes(), DevelopmentStructureRepair, maximum_bytes=None) == proof
    assert proof.acquisition_packet.object_fingerprint == case.acquisition[0].fingerprint()
    assert proof.structural_packet.object_fingerprint == case.structural[0].fingerprint()
    assert proof.child_relative_path.startswith('development/structure/repairs/repair.development-structure.')
    assert proof.child_relative_path.endswith('/analysis')
    assert replace(proof, owner_instruction_sha256='e' * 64).child_relative_path != proof.child_relative_path
    observed[-1]()


@pytest.mark.parametrize('failed_structure', ('other-error', 'partial-success'), indirect=True)
def test_structural_repair_refuses_other_failures_or_successful_work(failed_structure):
    with pytest.raises(PermissionError, match='measurement failure|discard successful'):
        owner._original_controls(writer=failed_structure.plane, directory=failed_structure.directory)


@pytest.mark.parametrize('damage', ('unreceipted-output', 'native-contact', 'missing-terminal', 'original-permission'))
def test_structural_repair_refuses_incomplete_or_uncertain_original_custody(failed_structure, monkeypatch, damage):
    case = failed_structure
    _, _, plan, index, _, _ = case.structural
    if damage == 'unreceipted-output':
        path = case.plane.root.resolve(plan.tasks[0].outputs[0].relative_path, for_write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'disclosed unreceipted output')
    elif damage == 'native-contact':
        from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
        monkeypatch.setattr(ExternalNativeEffectContactStore, 'read', lambda *args:object())
    elif damage == 'missing-terminal':
        case.plane.root.resolve(index.terminal_event_relative_path, for_write=True).unlink()
        case.plane.root.resolve(index.terminal_event_relative_path + '.manifest.json', for_write=True).unlink()
    else:
        case.access_state['revoked'] = True
    with pytest.raises((ValueError, PermissionError, RuntimeError), match='output|native contact|settled|revoked'):
        owner._original_controls(writer=case.plane, directory=case.directory)


@pytest.mark.parametrize('damage', ('control-bytes', 'original-permission'))
def test_structural_original_guard_stays_live_after_selection(failed_structure, damage):
    case = failed_structure
    observed = owner._original_controls(writer=case.plane, directory=case.directory)
    if damage == 'control-bytes':
        path = case.plane.root.resolve(case.structural[3].terminal_event_relative_path, for_write=True)
        path.write_bytes(path.read_bytes() + b'\n')
    else:
        case.access_state['revoked'] = True
    with pytest.raises(PermissionError, match='custody during use|revoked'):
        observed[-1]()


@pytest.mark.parametrize('path', (
    'adapters/simulators/exposed.py', 'adapters/methods/matrix_scheduled_history/full_factor_science.py',
    'adapters/methods/matrix_parameter_factor/science.py', 'kernel/exposed.py',
))
def test_structural_repair_refuses_numerical_or_kernel_changes(path):
    original, replacement = _sources()
    with pytest.raises((ValueError, PermissionError), match='numerical|kernel'):
        owner.require_structural_source(original, _source_changed(replacement, path))


def test_structural_repair_permits_only_selected_adapter_metadata_changes():
    original, replacement = _sources()
    changed = _source_changed(replacement, 'adapters/methods/matrix_scheduled_history/full_factor_records.py')
    owner.require_structural_source(original, changed)
    with pytest.raises(ValueError, match='distinct source|dependency lock'):
        owner.require_structural_source(original, replace(changed, dependency_lock_sha256='f' * 64))


@pytest.mark.parametrize('confirmed', (False, None, 1))
def test_public_structural_repair_requires_explicit_selection_before_input_io(confirmed):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    with pytest.raises(ValueError, match='explicit --yes'):
        ExperimentProgrammeService(ROOT, object()).repair_development_structure(directory=Path('/missing'),
            repair_instruction_path=Path('/missing'), confirmed=confirmed)


def test_public_structural_repair_binds_instruction_and_workers(tmp_path, monkeypatch):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    instruction = tmp_path / 'instruction.txt'
    instruction.write_bytes(b'Disclosed PURE repair request\n')
    calls = []
    monkeypatch.setattr(owner, 'repair_development_structure', lambda **kwargs:calls.append(kwargs) or {'status':'DISPATCHED_TEST_SEAM'})
    service = ExperimentProgrammeService(ROOT, object())
    assert service.repair_development_structure(directory=tmp_path, repair_instruction_path=instruction,
        confirmed=True, maximum_parallel_tasks=1) == {'status':'DISPATCHED_TEST_SEAM'}
    call, = calls
    assert call['owner_instruction_sha256'] == sha256(instruction.read_bytes()).hexdigest()
    assert call['maximum_parallel_tasks'] == 1 and call['service'] is service


def test_selected_structure_retains_original_custody_through_its_read(failed_structure):
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
    case = failed_structure
    observed = owner._original_controls(writer=case.plane, directory=case.directory)
    proof = owner._selection(case.plane, case.directory, observed,
        instruction_sha256='d' * 64, replacement=case.replacement)
    relative = owner._relative(case.plane, case.directory)
    case.plane.write(ArtifactWriteRequest(proof.repair_id, relative, proof.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', proof.repair_id,
        relative.rsplit('/', 1)[0], proof.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY,
        (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    child, retained, current = owner.selected_structure_directory(writer=case.plane, directory=case.directory)
    assert retained == proof
    assert child == Path(case.plane.root.contract.canonical_path) / proof.child_relative_path
    assert not child.exists()
    current()
    case.access_state['revoked'] = True
    with pytest.raises(PermissionError, match='revoked'):
        current()


@pytest.mark.parametrize('changed', ('none', 'source', 'scientific-member', 'run'))
def test_replacement_keeps_exact_scientific_members(failed_structure, monkeypatch, changed):
    case = failed_structure
    observed = owner._original_controls(writer=case.plane, directory=case.directory)
    proof = owner._selection(case.plane, case.directory, observed,
        instruction_sha256='d' * 64, replacement=case.replacement)
    child = Path(case.plane.root.contract.canonical_path) / proof.child_relative_path
    child.mkdir(parents=True)
    (child / 'authored-wave.json').write_bytes(b'Disclosed loader seam; not an authenticated scientific packet')
    original_packet, original_run, original_plan = case.structural[:3]
    members = original_packet.members
    if changed == 'scientific-member':
        members = tuple(replace(member, size_bytes=member.size_bytes + 1)
            if member.filename == 'experiment-specification.json' else member for member in members)
    packet = replace(original_packet, members=members)
    source = case.original if changed == 'source' else case.replacement
    run = original_run if changed == 'run' else replace(original_run, run_plan_id='run.disclosed.replacement')
    monkeypatch.setattr('empirical_lawhood.api.recursive_authoring.load_authored_wave',
        lambda **kwargs:(packet, object(), source, {}))
    monkeypatch.setattr('empirical_lawhood.api.recursive_execution._retained_plans',
        lambda *_args:(run, original_plan, object()))
    if changed == 'none':
        assert owner._require_replacement(case.plane, proof, observed) == child
    else:
        with pytest.raises(PermissionError, match='scientific inputs|selected source'):
            owner._require_replacement(case.plane, proof, observed)
