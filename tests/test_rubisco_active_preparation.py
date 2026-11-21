# SPDX-License-Identifier: MPL-2.0
"""Exposed preparation controls with actual receipt, file and recovery custody."""
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes

from dataclasses import fields, replace
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import active_preparation_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import active_preparation_read as reader
from empirical_lawhood.domains.rubisco.rubisco_response import active_relaxation_native as native
from empirical_lawhood.domains.rubisco.rubisco_response import active_relaxation_operation as original
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import BOHR_ANGSTROM, HARTREE_KJ_MOL
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_selection import prepare_active_preparation_prefix
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import prepare_conditional_relaxation_selection
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import expand_state_coordinates
from empirical_lawhood.execution.local.execution import prepare_worker_invocation

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.execution.capabilities import CapabilityConfigRef
from empirical_lawhood.execution.execution import TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from tests.runtime_platform.test_native_subwork import _plane, _store
from tests.runtime_platform.test_worker_preflight import _original_task
from tests import test_rubisco_active_relaxation_operation as controls

fixture = controls.fixture
matched = controls.matched


@pytest.fixture
def prefix(fixture):
    selected = prepare_conditional_relaxation_selection(plan=fixture.plan,
        state_census=(next(row for row in fixture.plan.members[0].state_census
            if row[1:] == ('keto-hie', 'AS_CONSTRUCTED')),),
        assumptions=('Exposed software control, with no molecular qualification or measured mutation response.',))
    values = {field.name: getattr(fixture.config, field.name) for field in fields(original.ActiveRelaxationConfig)}
    conditional = original.ConditionalActiveRelaxationConfig(**values, selection=selected)
    selection = prepare_active_preparation_prefix(plan=fixture.plan, conditional_selection=selected)
    fixture.config = owner.ActivePreparationPrefixConfig('config.exposed.active-prefix', conditional, selection)
    return fixture


def custody(f, *, continuation_raw=None, suffix=''):
    from empirical_lawhood.api.recursive_operations import operation_storage_codecs
    continued = hasattr(f.config, 'continuation')
    plane = _plane(f.tmp_path / ('custody' + suffix), binary_codecs=operation_storage_codecs())
    records = (('config', f.config.identity, f.config), *owner.native_input_records(f.config, f.model, f.prepared, f.sources))
    if continued:
        records += (('native-continuation-archive', f.config.continuation.archive_identity, continuation_raw),)
    manifests = []
    for name, pin, record in records:
        binary = type(record) is bytes
        written = plane.write(ArtifactWriteRequest(pin.object_id, 'inputs/' + name + ('.gz' if binary else '.json'), pin.object_schema,
            ArtifactProfile.RAW_SOURCE_BYTES if binary else ArtifactProfile.CANONICAL_JSON,
            'application/gzip' if binary else 'application/json', 'inputs.exposed.prefix', 'inputs', record if binary else record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifests.append(resolve_artifact_sidecar_bytes(plane, plane.root.resolve(written.materialization.relative_path + '.manifest.json', for_write=False).read_bytes()))
    manifests = tuple(sorted(manifests, key=lambda m: m.materialization.materialization_id))
    verified = tuple(sorted((VerifiedArtifactInput(m.logical, m.materialization) for m in manifests), key=lambda r: r.artifact_id))
    bindings = tuple(WorkerInputBinding.from_verified(row, kind=WorkerInputKind.EXTERNAL) for row in verified)
    by_id = {m.logical.logical_artifact_id: m for m in manifests}
    def ports():
        return tuple(plane.open(by_id[b.artifact_id], binding=b, maximum_bytes=b.size_bytes) for b in bindings)
    manifest = owner.operation_declaration(continuation=continued).manifest()
    node = owner.node_id(f.config)
    context = TaskContext('exposed.prefix', node, 'exposed.prefix.' + node + '.attempt-001',
        CapabilityConfigRef(f.config.config_id, f.config.SCHEMA, manifest.config_schema_sha256,
            f.config.fingerprint(), f.config.identity.object_id), bindings, ports(),
        (WorkerOutputPort(node + '.assessment', reader.ActivePreparationPrefixReadout.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'logical.exposed.prefix-assessment'),
         WorkerOutputPort(node + '.product', owner.ActivePreparationPrefixResult.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'logical.exposed.prefix-product')),
        manifest.permissions, OutcomeAccess.DEVELOPMENT_VISIBLE, owner.resource_budget(f.config), WorkerIsolationProfile.TRUSTED_LOCAL)
    runner = owner.ActivePreparationPrefixRunner(continuation=continued)
    task = _original_task(runner, context, SimpleNamespace(verified_inputs=verified))
    plan = ObjectIdentity('plan.exposed.prefix', 'empirical-lawhood/runtime/development-execution-plan', '1.0.0', '1' * 64)
    contract = prepare_worker_invocation(runner, context, verified, implementation=f.config.original.implementation,
        execution_plan=plan, execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task,
        native_effect=True, native_work_preparer=owner.prepare_native_work)
    assert contract.native_preparation_error is None
    context = replace(context, prepared_invocation=contract)
    f.contexts.append(context)
    store = _store(plane, contract.expected_parent_contact, manifests, prepared_invocation=contract)
    store.parent_contacts.begin(contract.expected_parent_contact)
    def fresh():
        value = replace(context, input_ports=ports())
        f.contexts.append(value)
        return value
    return SimpleNamespace(plane=plane, context=context, work=contract.native_work, store=store, fresh=fresh)


def assert_sealed_input_reuse(context, decode, monkeypatch):
    """Count actual strict decodes and retain complete-read and identity refusals."""
    from empirical_lawhood.science.records import decoding
    calls = []
    original = decoding.decode_canonical_bytes
    def counted(raw, kind, **kwargs):
        calls.append((kind.SCHEMA, len(raw)))
        return original(raw, kind, **kwargs)
    with monkeypatch.context() as scoped:
        scoped.setattr(decoding, 'decode_canonical_bytes', counted)
        outputs = []
        for _ in range(2):
            ports = tuple(p.cursor() for p in context.input_ports)
            try:
                outputs.append(decode(replace(context, input_ports=ports), accelerated=False))
                assert all(p.bytes_read == p.size_bytes for p in ports)
            finally:
                for port in ports:
                    port.close()
            assert len(calls) == sum(p.media_type == 'application/json' for p in ports)
        assert outputs[0] == outputs[1]
        assert all(a is b for a, b in zip(outputs[0], outputs[1], strict=True) if type(a) is not bytes)
        ports = tuple(p.cursor() for p in context.input_ports)
        try:
            selected = next(i for i, p in enumerate(ports) if p.payload_schema == MolecularRepresentation.SCHEMA)
            changed = list(ports)
            changed[selected] = replace(ports[selected], binding=replace(ports[selected].binding,
                artifact_id='substituted.original-artifact'))
            changed = tuple(sorted(changed, key=lambda p: p.artifact_id))
            # Exercise the domain's pre-admission check; a prepared invocation
            # independently refuses this substitution at TaskContext creation.
            with pytest.raises(ValueError, match='exact original'):
                decode(replace(context, input_ports=changed, input_bindings=tuple(p.binding for p in changed),
                    prepared_invocation=None),
                    accelerated=False)
            assert all(p.bytes_read == p.size_bytes for p in ports)
            assert len(calls) == sum(p.media_type == 'application/json' for p in ports)
        finally:
            for port in ports:
                port.close()


def test_prefix_sealed_input_reuse_preserves_complete_bytes_and_original_identities(prefix, monkeypatch):
    selected = custody(prefix)
    assert_sealed_input_reuse(selected.fresh(), owner._decode, monkeypatch)


def install_exposed_operator(f, monkeypatch, *, fail_at=None, anisotropic=False):
    from tests.rubisco_exposed_geometry_fixture import install_exposed_geometry
    install_exposed_geometry(monkeypatch)
    import empirical_lawhood.domains.rubisco.rubisco_response as package
    import empirical_lawhood.adapters.rubisco.rubisco_response as native_package
    from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm as qmmm
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k: None)
    monkeypatch.setattr(original, 'authenticate_periodic_engine', lambda *a, **k: None)
    for short in ('periodic_mm_remainder', 'periodic_images', 'pyscf_periodic_electronic'):
        owner_package = native_package if short == 'pyscf_periodic_electronic' else package
        stub = ModuleType(owner_package.__name__ + '.' + short)
        monkeypatch.setitem(sys.modules, stub.__name__, stub)
        monkeypatch.setattr(owner_package, short, stub, raising=False)
    seed, = original.selected_seeds(f.config.original, f.prepared)
    initial = expand_state_coordinates(seed, f.coordinates)
    target_nm = initial / 10
    target_nm[:, 0] += .015
    stiffness = 100 * (1 + np.arange(len(initial)) % 5)[:, None] if anisotropic else 100
    calls = []
    def build(**kwargs):
        return object(), {}, dict(scope='EXPOSED_SOFTWARE_CONTROL')
    class TranslatedHarmonicOperator:
        def __init__(self, **kwargs):
            self.observe = kwargs['observe']
            self.evaluations = 0
            self.remainder_audit = self.embedding_audit = dict(scope='EXPOSED_SOFTWARE_CONTROL')
        def evaluate(self, coordinates):
            self.evaluations += 1
            calls.append(coordinates.copy())
            self.observe(dict(event='entry', evaluation=self.evaluations, physical_atoms=len(coordinates)))
            if self.evaluations == fail_at:
                self.observe(dict(event='error', evaluation=self.evaluations, error='EXPOSED_FAILED_NATIVE_EFFECT'))
                raise RuntimeError('EXPOSED_FAILED_NATIVE_EFFECT')
            displacement = coordinates / 10 - target_nm
            energy = .5 * float(np.sum(stiffness * displacement**2)) / HARTREE_KJ_MOL
            gradient = stiffness * displacement * BOHR_ANGSTROM / (10 * HARTREE_KJ_MOL)
            for event in ('electronic-return', 'return'):
                self.observe(dict(event=event, evaluation=self.evaluations, physical_atoms=len(coordinates),
                    converged=True, orbital_gradient_norm=0., energy_hartree=energy))
            return dict(energy_hartree=energy, gradient_hartree_per_bohr=gradient,
                gradient_unit=native.GRADIENT_UNIT, bohr_angstrom=BOHR_ANGSTROM, hartree_kj_mol=HARTREE_KJ_MOL)
    monkeypatch.setattr(qmmm, 'build_periodic_amber_system', build)
    monkeypatch.setattr(qmmm, 'PeriodicCoupledOperator', TranslatedHarmonicOperator)
    return calls


@pytest.mark.parametrize('fail_at', (None, 2))
def test_original_prefix_readback_failure_and_completed_recovery_without_replay(prefix, monkeypatch, fail_at):
    f = prefix
    c = custody(f)
    calls = install_exposed_operator(f, monkeypatch, fail_at=fail_at)
    runner = owner.ActivePreparationPrefixRunner()
    first = runner.execute_with_native_subwork(c.context, c.store)
    result = decode_canonical_bytes(first.outputs[1].payload, owner.ActivePreparationPrefixResult, maximum_bytes=16 * 2**20)
    report, arrays, evaluations = reader.read_preparation_prefix(config=f.config, representation=f.model,
        prepared=f.prepared, coordinate_bytes=f.coordinates, original_result=result, native_subwork=c.store,
        assessor_source=f.model.material.sources[0], readout_id='readout.exposed.prefix', include_operands=True)
    assert report.assessment_error is None, report.assessment_error
    retained_assessment = decode_canonical_bytes(first.outputs[0].payload, reader.ActivePreparationPrefixReadout, maximum_bytes=16 * 2**20)
    assert retained_assessment.assessment.positions == report.assessment.positions
    assert report.assessment is not None
    assert len(calls) == 2
    assert len(evaluations) == (2 if fail_at is None else 1)
    assert [r.disposition for r in report.assessment.positions] == ['AVAILABLE', 'AVAILABLE' if fail_at is None else 'UNAVAILABLE']
    assert len(arrays) == len(evaluations)
    assert report.independent_biological_replicates == 0 and report.original_starting_hypotheses == 384
    assert report.assessment.complete_native_return_ledger == (fail_at is None)
    assert (result.unit.returned.error is None) == (fail_at is None)
    assert decode_canonical_bytes(report.canonical_bytes(), reader.ActivePreparationPrefixReadout, maximum_bytes=16 * 2**20) == report
    def refuse(**kwargs):
        pytest.fail('completed original native effect was replayed')
    monkeypatch.setattr(native, 'execute_active_relaxation', refuse)
    second = runner.execute_with_native_subwork(c.fresh(), c.store)
    assert tuple(o.payload for o in second.outputs) == tuple(o.payload for o in first.outputs)
    assert len(calls) == 2
    changed = replace(f.config, config_id=f.config.config_id + '.changed')
    with pytest.raises(ValueError, match='original selected configuration'):
        reader.read_preparation_prefix(config=changed, representation=f.model, prepared=f.prepared,
            coordinate_bytes=f.coordinates, original_result=result, native_subwork=c.store,
            assessor_source=f.model.material.sources[0], readout_id='readout.exposed.changed')
    assert Path(f.config.original.work_directory).is_dir()


def _continuation_selection(f, c, returned, *, suffix='continued'):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import prepare_continuation
    report = decode_canonical_bytes(returned.outputs[0].payload, reader.ActivePreparationPrefixReadout, maximum_bytes=16 * 2**20)
    assert report.assessment_error is None, report.assessment_error
    definition = report.original_result.unit.definition
    completion = c.store.recover(definition)
    archive, = (m for m in completion.outputs if m.logical.logical_artifact_id.endswith('.output.files.raw'))
    selected = prepare_continuation(previous=f.config, readout=report, archive=archive)
    raw = b''.join(c.store.iter_completed_output(definition, 'files.raw'))
    config = owner.config_type(continuation=True)('config.exposed.' + suffix,
        replace(f.config.original, work_directory=str(f.tmp_path / suffix)), f.config.prefix,
        continuation=selected)
    return config, raw, report


@pytest.mark.parametrize('boundary', ('after-evaluation-seal', 'before-checkpoint-seal', 'after-checkpoint-seal'))
def test_registered_continuation_replays_only_sealed_returns_and_preserves_trajectory(prefix, monkeypatch, boundary):
    from empirical_lawhood.domains.rubisco.rubisco_response import active_preparation_checkpoint as checkpoint
    from empirical_lawhood.domains.rubisco.rubisco_response import active_preparation_evaluation as evaluation
    f = prefix
    initial_config = f.config
    c = custody(f)
    calls = install_exposed_operator(f, monkeypatch, anisotropic=True)
    with monkeypatch.context() as failure:
        if boundary == 'after-evaluation-seal':
            publish = evaluation.publish_evaluation_files
            def fail_after_return(*args, **kwargs):
                publish(*args, **kwargs)
                raise OSError('EXPOSED_INTERRUPTION_AFTER_COMPLETE_EVALUATION_SEAL')
            failure.setattr(evaluation, 'publish_evaluation_files', fail_after_return)
        elif boundary == 'before-checkpoint-seal':
            open_file = Path.open
            def refuse_seal(path, *args, **kwargs):
                if path.name == 'accepted-00000000.json' and args == ('xb',):
                    raise OSError('EXPOSED_INTERRUPTION_BEFORE_CHECKPOINT_SEAL')
                return open_file(path, *args, **kwargs)
            failure.setattr(Path, 'open', refuse_seal)
        else:
            publish = checkpoint.publish_checkpoint_files
            def fail_after_checkpoint(directory, record, arrays):
                published = publish(directory, record, arrays)
                if record.iterations == 1:
                    raise OSError('EXPOSED_INTERRUPTION_AFTER_ACCEPTED_OPTIMIZER_STATE')
                return published
            failure.setattr(checkpoint, 'publish_checkpoint_files', fail_after_checkpoint)
        first = owner.ActivePreparationPrefixRunner().execute_with_native_subwork(c.context, c.store)
    first_count = len(calls)
    config, raw, report = _continuation_selection(f, c, first)
    assert report.original_result.unit.returned.error is not None
    assert report.assessment.complete_native_return_ledger
    assert config.continuation.remaining_allowance == 5 - first_count
    assert decode_canonical_bytes(config.canonical_bytes(), type(config), maximum_bytes=64 * 2**20) == config
    f.config = config
    continued = custody(f, continuation_raw=raw, suffix='-continued')
    runner = owner.ActivePreparationPrefixRunner(continuation=True)
    actual = runner.execute_with_native_subwork(continued.context, continued.store)
    readout = decode_canonical_bytes(actual.outputs[0].payload, reader.ActivePreparationPrefixReadout, maximum_bytes=16 * 2**20)
    assert readout.assessment_error is None, readout.assessment_error
    assert readout.original_result.unit.returned.error is None, readout.original_result.unit.returned.error
    # This exposed anisotropic objective converges in three complete calls.
    assert len(calls) == 3
    assert readout.assessment.evaluations[:first_count] == report.assessment.evaluations
    assert readout.assessment.checkpoints[:len(report.assessment.checkpoints)] == report.assessment.checkpoints
    assert readout.assessment.configuration == initial_config.identity
    assert runner.execute_with_native_subwork(continued.fresh(), continued.store).outputs == actual.outputs
    assert len(calls) == 3
    # An uninterrupted operation supplies the independent complete-call trajectory.
    f.config = replace(initial_config, original=replace(initial_config.original,
        work_directory=str(f.tmp_path / 'uninterrupted')))
    baseline_calls = install_exposed_operator(f, monkeypatch, anisotropic=True)
    baseline_custody = custody(f, suffix='-baseline')
    baseline = owner.ActivePreparationPrefixRunner().execute_with_native_subwork(baseline_custody.context, baseline_custody.store)
    expected = decode_canonical_bytes(baseline.outputs[0].payload, reader.ActivePreparationPrefixReadout, maximum_bytes=16 * 2**20)
    assert expected.assessment_error is None
    assert len(baseline_calls) == len(calls)
    assert all(np.array_equal(a, b) for a, b in zip(calls, baseline_calls, strict=True))
    actual_state = readout.assessment.checkpoints[-1].checkpoint
    expected_state = expected.assessment.checkpoints[-1].checkpoint
    for field in ('native_evaluation', 'energy_hartree', 'optimizer_energy_kj_mol', 'iterations',
                  'evaluations', 'invalid_trials', 'curvature_skips', 'descent_iterations'):
        assert getattr(actual_state, field) == getattr(expected_state, field)
    assert actual_state.arrays.members == expected_state.arrays.members


@pytest.mark.parametrize('boundary', ('before-evaluation-seal', 'after-native-entry'))
def test_registered_continuation_refuses_unsealed_or_failed_contact(prefix, monkeypatch, boundary):
    from empirical_lawhood.domains.rubisco.rubisco_response import active_preparation_evaluation as evaluation
    f = prefix
    c = custody(f)
    calls = install_exposed_operator(f, monkeypatch, fail_at=2 if boundary == 'after-native-entry' else None)
    if boundary == 'before-evaluation-seal':
        def fail_before_seal(*args, **kwargs):
            raise OSError('EXPOSED_RETURN_WITHOUT_COMPLETE_OPERAND_PUBLICATION')
        monkeypatch.setattr(evaluation, 'publish_evaluation_files', fail_before_seal)
    returned = owner.ActivePreparationPrefixRunner().execute_with_native_subwork(c.context, c.store)
    count = len(calls)
    with pytest.raises(ValueError, match='complete return ledger'):
        _continuation_selection(f, c, returned)
    assert len(calls) == count


def test_registered_continuation_refuses_changed_source_threads_allowance_and_archive(prefix, monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import read_continuation_files
    from empirical_lawhood.domains.rubisco.rubisco_response import active_preparation_checkpoint as checkpoint
    f = prefix
    c = custody(f)
    calls = install_exposed_operator(f, monkeypatch)
    publish = checkpoint.publish_checkpoint_files
    with monkeypatch.context() as failure:
        def stop(directory, record, arrays):
            publish(directory, record, arrays)
            raise OSError('EXPOSED_ACCEPTED_STATE_INTERRUPTION')
        failure.setattr(checkpoint, 'publish_checkpoint_files', stop)
        first = owner.ActivePreparationPrefixRunner().execute_with_native_subwork(c.context, c.store)
    config, raw, _ = _continuation_selection(f, c, first)
    with pytest.raises(ValueError, match='source, threads'):
        replace(config, original=replace(config.original,
            implementation=replace(config.original.implementation, observed_git_head='4' * 40),
            provenance=replace(config.original.provenance, observed_git_head='4' * 40)))
    with pytest.raises(ValueError, match='source closure'):
        replace(config, original=replace(config.original, prototype=replace(config.original.prototype,
            engine=replace(config.original.prototype.engine, numerical_threads=2))))
    with pytest.raises(ValueError, match='remaining original allowance'):
        replace(config.continuation, remaining_allowance=config.continuation.remaining_allowance + 1)
    with pytest.raises(ValueError, match='archive bytes'):
        read_continuation_files(config.continuation, raw[:-1] + bytes([raw[-1] ^ 1]),
            representation=f.model, prepared=f.prepared, coordinate_bytes=f.coordinates)
    assert len(calls) == 1


def test_interruption_before_native_entry_reuses_only_unentered_original_work(prefix, monkeypatch):
    f = prefix
    c = custody(f)
    calls = install_exposed_operator(f, monkeypatch)
    with monkeypatch.context() as failure:
        def refuse(*args, **kwargs):
            raise ValueError('EXPOSED_PREFLIGHT_INTERRUPTION')
        failure.setattr(owner, 'authenticate_periodic_engine', refuse)
        with pytest.raises(ValueError, match='PREFLIGHT'):
            owner.ActivePreparationPrefixRunner().execute_with_native_subwork(c.context, c.store)
    assert calls == []
    owner.ActivePreparationPrefixRunner().execute_with_native_subwork(c.fresh(), c.store)
    assert len(calls) == 2


def test_unpublished_completion_never_authorizes_repurchase(prefix, monkeypatch):
    from empirical_lawhood.execution.native_subwork import NativeSubworkReceiptPublicationPending
    f = prefix
    c = custody(f)
    calls = install_exposed_operator(f, monkeypatch)
    with monkeypatch.context() as failure:
        def refuse(*args, **kwargs):
            raise OSError('EXPOSED_INTERRUPTION_BEFORE_DURABLE_COMPLETION')
        failure.setattr(c.store, 'complete', refuse)
        with pytest.raises(OSError, match='DURABLE_COMPLETION'):
            owner.ActivePreparationPrefixRunner().execute_with_native_subwork(c.context, c.store)
    assert len(calls) == 2
    with pytest.raises(NativeSubworkReceiptPublicationPending):
        owner.ActivePreparationPrefixRunner().execute_with_native_subwork(c.fresh(), c.store)
    assert len(calls) == 2


def test_prefix_refuses_portfolio_expansion_and_missing_direct_source(prefix):
    f = prefix
    with pytest.raises(ValueError, match='ten-return'):
        replace(f.config.prefix, model_allowances=(('m1-i95m', 6), ('m1-wt', 5)))
    c = custody(f)
    assert len(c.context.input_ports) == 107 and len(c.work.definitions) == 1
    with pytest.raises(ValueError, match='input ports|complete direct input'):
        owner._decode(replace(c.context, input_ports=c.context.input_ports[:-1]), accelerated=False)
    assert not Path(f.config.original.work_directory).exists()


@pytest.mark.parametrize(('matched', 'reader_threads'), ((1, 8), (8, 1)), indirect=('matched',))
def test_original_prefix_readback_preserves_producing_threads(prefix, monkeypatch, reader_threads):
    from threadpoolctl import threadpool_info, threadpool_limits
    f = prefix
    c = custody(f)
    calls = install_exposed_operator(f, monkeypatch)
    with threadpool_limits(limits=f.prototype.engine.numerical_threads):
        produced = owner.ActivePreparationPrefixRunner().execute_with_native_subwork(c.context, c.store)
    report = decode_canonical_bytes(produced.outputs[0].payload, reader.ActivePreparationPrefixReadout,
        maximum_bytes=16 * 2**20)
    assert report.assessment_error is None
    with threadpool_limits(limits=reader_threads):
        before = threadpool_info()
        observed = reader.read_preparation_prefix(config=f.config, representation=f.model,
            prepared=f.prepared, coordinate_bytes=f.coordinates, original_result=report.original_result,
            native_subwork=c.store, assessor_source=report.assessment.assessor_source,
            readout_id=report.readout_id)
        assert threadpool_info() == before
    assert observed.canonical_bytes() == report.canonical_bytes()
    assert len(calls) == 2
