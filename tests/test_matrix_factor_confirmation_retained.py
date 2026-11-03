# SPDX-License-Identifier: MPL-2.0
"""Protected cold I/O conformance on hypothetical software-only custody.

No issue or native producer runs. Setup retains deterministic supplied-noise
values under software progress records. Real qualification remains absent.
"""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import records as r, retained, science
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.commitment import COMMIT_KEY, E1CommitmentConfig, E1Commitment, committed
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.operation_bindings import BUDGET, NAMESPACE, PHASES, E1OperationConfig, operation_factories
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNativeHistory, coordinate_identity
from empirical_lawhood.api.execution import CampaignExecutionService
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, CandidateExecutionPlan, ExecutionTask, PlanLane, BarrierKind, ScientificStage, ScientificInputSpec, ScientificInputRole
from empirical_lawhood.runtime.providers import ExternalInputPayload
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance
from tests.test_matrix_factor_confirmation_eligibility import stock as stock
from tests.test_matrix_factor_confirmation_history import deterministic_arrays, ordinary_receipt
from tests.test_matrix_factor_confirmation_history import e1 as e1


def cold_case(e1, *, defect=None):
    plane, sources, _ = e1
    source, run = sources[1], 'run.software.e1'
    def stage_inputs(writes):
        values = tuple(ExternalInputPayload.from_bytes(logical_artifact_id=w.logical.logical_artifact_id,
            payload_schema=w.logical.payload_schema, profile=w.logical.profile, media_type=w.logical.media_type,
            payload=plane.root.resolve(w.materialization.relative_path, for_write=False).read_bytes(),
            visibility_ceiling=w.logical.visibility_ceiling, outcome_access=w.logical.outcome_access,
            parent_visibility_ceilings=w.logical.parent_visibility_ceilings, lineage_parents=w.logical.lineage_parents) for w in writes)
        staged = CampaignExecutionService._persist_provider_inputs(SimpleNamespace(artifact_plane=plane), run, values, minimum_free_bytes=0)
        return tuple(retained._manifest(plane, s.materialization.relative_path) for s in staged)
    config = E1CommitmentConfig('config.'+COMMIT_KEY, sources)
    commitment_writes = [publish(plane, config, config.config_id), *(publish(plane, s, s.source_id) for s in sources),
        source.reservation.publication, source.specification.publication]
    commitment_inputs = stage_inputs(commitment_writes)
    assert next(m for m in commitment_inputs if m.logical == source.reservation.publication.logical).materialization != source.reservation.publication.materialization
    commitment = committed(config)
    if defect == 'changed-commitment':
        commitment = replace(commitment, sources=tuple(replace(s, object_fingerprint='f'*64) for s in commitment.sources))
    written = publish(plane, commitment, 'ordinary.commit')
    commit_manifest = retained._manifest(plane, written.materialization.relative_path)
    m = next(f.manifest for f in operation_factories() if f.manifest.capability_key == COMMIT_KEY)
    requirement = CapabilityRequirement(m.capability_key, m.capability_version, m.kind,
        CapabilityConfigRef(config.config_id, config.SCHEMA, m.config_schema_sha256, config.fingerprint(), config.config_id),
        m.input_schema_ids, m.output_schema_ids, m.permissions, m.maximum_evidence_ceiling, Access.OUTCOME_BLIND, BUDGET)
    commit_task = ExecutionTask(COMMIT_KEY, ScientificStage.FREEZE, requirement, m.implementation_sha256, (), (),
        (ArtifactOutputSpec(COMMIT_KEY+'.product', written.logical.logical_artifact_id, written.materialization.relative_path,
            E1Commitment.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND),),
        (), BarrierKind.FREEZE, 1, ('obligation.software.commit',), scientific_inputs=())
    commit_receipt = CanonicalTaskReceipt('receipt.ordinary.commit', run, COMMIT_KEY, 'attempt.'+COMMIT_KEY,
        source.provenance.observed_git_head, tuple(sorted(m.materialization.materialization_id for m in commitment_inputs)),
        (written.materialization,), (written.logical,), (), OperationalStatus.SUCCEEDED, ())
    tasks = []
    for (role, _, output, stage), factory in zip(PHASES, operation_factories()[:4], strict=True):
        task_id = NAMESPACE+'.'+source.root_id+'.'+role
        config = E1OperationConfig('config.'+task_id, role, source)
        m = factory.manifest
        requirement = CapabilityRequirement(m.capability_key, m.capability_version, m.kind,
            CapabilityConfigRef(config.config_id, config.SCHEMA, m.config_schema_sha256, config.fingerprint(), config.config_id),
            m.input_schema_ids, m.output_schema_ids, m.permissions, m.maximum_evidence_ceiling, Access.EVALUATION_SEALED, BUDGET)
        logical = 'ordinary.'+role+'.'+source.root_id
        outputs = [ArtifactOutputSpec(task_id+'.product', logical, 'refined-inputs/'+logical, output.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', Visibility.PROSPECTIVE, (), Access.EVALUATION_SEALED)]
        if role in ('history', 'measure'):
            logical = ('native.arrays.' if role == 'history' else 'factor.arrays.')+source.root_id
            from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
            outputs.append(ArtifactOutputSpec(task_id+'.arrays', logical, 'refined-inputs/'+logical, MATRIX_ARRAY_SCHEMA,
                ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', Visibility.PROSPECTIVE, (), Access.EVALUATION_SEALED))
        if defect == 'wrong-capability' and role == 'check':
            requirement = replace(requirement, capability_key='other.check')
        if defect == 'wrong-output-path' and role == 'check':
            outputs[0] = replace(outputs[0], relative_path='elsewhere/'+outputs[0].logical_artifact_id)
        if defect == 'wrong-media' and role == 'check':
            outputs[0] = replace(outputs[0], media_type='text/plain')
        dependencies = (COMMIT_KEY,) if role == 'history' and defect != 'missing-commitment-dependency' else ()
        edges = (ScientificInputSpec('edge.'+task_id+'.commitment', 'commitment', ScientificInputRole.SOURCE,
            COMMIT_KEY, COMMIT_KEY+'.product', None, written.logical.logical_artifact_id, written.logical.logical_artifact_id,
            E1Commitment.SCHEMA, 'application/json', None, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, BarrierKind.FREEZE),) if dependencies else ()
        tasks.append(ExecutionTask(task_id, stage, requirement, m.implementation_sha256, dependencies, (),
            tuple(sorted(outputs, key=lambda o: o.output_id)), (), BarrierKind.NONE, 1,
            ('obligation.software.'+role,), scientific_inputs=edges))
    tasks.append(commit_task)
    source_plan = ObjectIdentity(run if defect != 'foreign-run-plan' else 'foreign.run', 'empirical-lawhood/runtime/candidate-run-plan', '1.0.0', '1'*64)
    plan = CandidateExecutionPlan('plan.software.e1', PlanLane.PROSPECTIVE if defect != 'wrong-lane' else PlanLane.DEVELOPMENT,
        source_plan, '2'*64, source.provenance.observed_git_head, tuple(sorted(tasks, key=lambda t: t.task_id)), True,
        candidate=ObjectIdentity('candidate.software.e1', 'empirical-lawhood/planning/draft-study-candidate', '1.0.0', '3'*64))
    pin = ObjectIdentity.from_record(plan.execution_plan_id, plan)
    plane.write(ArtifactWriteRequest(plan.execution_plan_id, 'runs/'+run+'/plans/execution-plan.json', plan.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.software.plan', 'runs/'+run+'/plans', plan.canonical_bytes(),
        Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
    task = next(t for t in tasks if t.task_id.endswith('.history'))
    config = E1OperationConfig('config.'+task.task_id, 'history', source)
    values = [(config.config_id, config), (source.source_id, source),
        (source.coordinate.coordinate_id, source.coordinate), (source.provenance.identity.object_id, source.provenance)]
    values += [(source.root.stream_identity(s).object_id, s) for s in source.root.streams]
    writes = [publish(plane, record, name) for name, record in values]
    writes += [source.reservation.publication, source.specification.publication]
    inputs = (*stage_inputs(writes), commit_manifest)
    parent = NativeEffectContact(run, task.task_id, 'attempt.'+task.task_id, pin,
        ObjectIdentity.from_record(task.task_id, task), source.provenance.observed_git_head,
        tuple(sorted(m.materialization.materialization_id for m in inputs)), ())
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=pin,
        visibility_ceiling=Visibility.PROSPECTIVE, outcome_access=Access.EVALUATION_SEALED)
    contacts.begin(parent)
    native = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent, parent_inputs=inputs)
    definition = NativeSubworkDefinition('paired-history.'+source.root_id, 'matrix-e1.full-paired-history', parent,
        r.identity(config), tuple(sorted((r.identity(source), r.identity(source.allocation), coordinate_identity(source.coordinate), source.provenance.identity), key=lambda x: x.object_id)),
        source.provenance.code_sources_sha256, source.provenance.dependency_lock_sha256, parent.input_materialization_ids,
        tuple(sorted((source.root.stream_identity(s) for s in source.root.streams), key=lambda x: x.object_id)),
        (NativeSubworkOutput('arrays', 'empirical-lawhood/data/matrix-array-npz', ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'),))
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
    definition = replace(definition, outputs=(replace(definition.outputs[0], payload_schema=MATRIX_ARRAY_SCHEMA),))
    native.freeze_roster(NativeSubworkRoster('selected.native-subwork', parent, (definition.identity,)), definitions=(definition,))
    entry = native.begin(definition)
    native.contact(entry)
    arrays = deterministic_arrays(source)
    raw, operand = science.array_product(source, arrays, artifact_id='native.arrays.'+source.root_id)
    native.publish_output(entry, 'arrays', (raw,), maximum_bytes=len(raw), maximum_chunk_bytes=len(raw),
        expected_size_bytes=len(raw), expected_physical_sha256=sha256(raw).hexdigest())
    complete = native.complete(entry, operational_status=OperationalStatus.SUCCEEDED, consumed_streams=definition.streams,
        cost=InquiryCost(None, None, None), cost_scope='hypothetical software custody, deterministic supplied values only')
    history = r.E1NativeHistory('history.'+source.root_id, r.identity(source), coordinate_identity(source.coordinate), source.root_id,
        source.root.root.independent_group_id, source.coordinate.clock_id, operand, MatrixParameterNativeHistory(definition, complete.completion, complete.receipt), 8, 16)
    numerical = science.assess_history(source, history, arrays)
    diagnostic, product = science.measure(source, history, numerical, arrays, artifact_id='factor.arrays.'+source.root_id)
    assessment = science.assess_factor(source, history, numerical, product, raw, diagnostic)
    receipts = (ordinary_receipt(plane, source, 'history', history, raw), ordinary_receipt(plane, source, 'numerical', numerical),
        ordinary_receipt(plane, source, 'measure', product, diagnostic), ordinary_receipt(plane, source, 'check', assessment))
    store = ExternalTaskReceiptStore(plane)
    store.commit(commit_receipt, visibility_ceiling=Visibility.PROSPECTIVE, outcome_access=Access.OUTCOME_BLIND)
    for receipt in receipts:
        store.commit(receipt, visibility_ceiling=Visibility.PROSPECTIVE, outcome_access=Access.EVALUATION_SEALED)
    return dict(plane=plane, run_id=run, execution_plan=pin, source=source, original_inputs=inputs,
        receipt_locators=tuple((role, receipt.attempt_id) for (role, _, _, _), receipt in zip(PHASES, receipts, strict=True)),
        commitment_attempt_id=commit_receipt.attempt_id if defect != 'missing-commitment-receipt' else 'missing.attempt',
        commitment_inputs=commitment_inputs), (history, numerical, product, assessment)


@pytest.mark.parametrize('defect', (None, 'wrong-lane', 'foreign-run-plan', 'wrong-capability', 'wrong-output-path', 'wrong-media', 'missing-receipt',
    'missing-commitment-dependency', 'missing-commitment-receipt', 'changed-commitment', 'missing-native-receipt'))
def test_actual_protected_plan_receipts_and_native_completion_cold_read(e1, monkeypatch, defect):
    selected, expected = cold_case(e1, defect=defect)
    if defect == 'missing-receipt':
        selected['receipt_locators'] = (*selected['receipt_locators'][:-1], ('check', 'missing.attempt'))
    root = selected['plane'].root.contract.canonical_path
    from pathlib import Path
    if defect == 'missing-native-receipt':
        receipt = expected[0].native.receipt
        relative = f'runs/{receipt.run_id}/receipts/{receipt.task_id}/{receipt.attempt_id}.json'
        for suffix in ('', '.manifest.json'):
            Path(root, relative + suffix).unlink()
    before = {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest() for p in Path(root).rglob('*') if p.is_file()}
    def blocked(*args, **kwargs):
        raise AssertionError('cold adapter entered a mutation, producer, RNG or eigensolver')
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', blocked)
    monkeypatch.setattr(ExternalNativeEffectContactStore, 'begin', blocked)
    for name in ('begin', 'contact', 'freeze_roster', 'publish_output', 'complete', 'recover'):
        monkeypatch.setattr(ExternalNativeSubworkStore, name, blocked)
    monkeypatch.setattr(ExternalTaskReceiptStore, 'commit', blocked)
    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.random, 'PCG64DXSM', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    monkeypatch.setattr(np.linalg, 'eigvalsh', blocked)
    if defect is None:
        assert retained.read_root(**selected) == expected
    else:
        with pytest.raises(ValueError):
            retained.read_root(**selected)
    assert before == {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest() for p in Path(root).rglob('*') if p.is_file()}


def test_complete_root_read_rechecks_native_receipt_bytes_before_return(e1, monkeypatch):
    """The whole read's final guard includes already consumed native custody."""
    from pathlib import Path

    selected, expected = cold_case(e1)
    receipt = expected[0].native.receipt
    path = Path(selected['plane'].root.contract.canonical_path,
        f'runs/{receipt.run_id}/receipts/{receipt.task_id}/{receipt.attempt_id}.json')
    before = path.read_bytes()
    original = science.read_retained

    def change_after_scientific_replay(*args, **kwargs):
        result = original(*args, **kwargs)
        assert path.read_bytes() == before
        path.write_bytes(before[:-1] + b' ')
        return result

    monkeypatch.setattr(science, 'read_retained', change_after_scientific_replay)
    with pytest.raises(ArtifactIdentityConflict, match='verification'):
        retained.read_root(**selected)
    assert path.read_bytes() == before[:-1] + b' '
