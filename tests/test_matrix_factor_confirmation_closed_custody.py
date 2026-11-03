# SPDX-License-Identifier: MPL-2.0
"""Exposed E1 closed-custody controls; no scientific authority or native entry.

The mathematical cases use disclosed categorical products. Public-reader cases
replace the issue/authority lookup only; original recovery publications, complete
task censuses, source selections and the missing-root reducer remain actual.
"""
from dataclasses import fields, replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import (
    compact_bindings as owner, compact_preparation as domain, compact_records as r,
    compact_science as science,
)
from empirical_lawhood.api import matrix_factor_confirmation_compact_read as reader
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.compiler import compile_run_plan, lower_run_plan
from empirical_lawhood.runtime.execution import OperationalFailureClass
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.plans import ExecutionPlan
from empirical_lawhood.runtime.prospective_experiment import SPECIFICATION_FILENAME, source_filename
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.recovery import (
    OperationalFailureDiagnostic, RecoveryTerminalAttempt, RecoveryTerminalDisposition,
    RunRecoveryIndex, RunRecoveryTerminalEvent, TaskRecoveryDisposition, TaskRecoveryEvent,
)
from tests.test_matrix_factor_confirmation_compact_core import compact_products
from tests.test_matrix_factor_confirmation_compact_declarative import _case
from tests.test_matrix_factor_confirmation_eligibility import provenance, stock  # noqa: F401
from tests.test_matrix_factor_confirmation_history import e1  # noqa: F401


def pin(value, field):
    return ObjectIdentity.from_record(getattr(value, field), value)


def fixture_pin(name, schema):
    return ObjectIdentity(name, schema, '1.0.0', 'a'*64)


@pytest.fixture
def case(e1):  # noqa: F811
    spec, selected, _ = _case(e1)
    policy = selected.root.system.authority_policy
    selected = replace(selected, root=replace(selected.root, campaign=replace(selected.root.campaign,
        authority_policy=pin(policy, 'policy_id'))))
    spec = replace(spec, selection=selected.identity)
    draft, _, _ = domain._derive(spec, selected)
    sources = r.sources_for_manifest(selected.manifest)
    declarations = owner.operation_declarations()
    registry = CapabilityRegistry('registry.disclosed.e1-closed', tuple(sorted(
        (row.manifest() for row in declarations), key=lambda row: row.registry_id)))
    compiled = compile_recursive_wave(draft=draft,
        registrations=tuple(row.registration() for row in declarations), registry=registry,
        implementation_commit=sources[0].implementation_commit, qualifications=selected.qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs,
        output_codecs={key: value for row in declarations for key, value in row.record_codecs.items()})
    candidate = compiled.candidate_report.candidate
    assert candidate is not None, compiled.candidate_report.diagnostics
    run = compile_run_plan(run_plan_id='run.disclosed.e1-closed', campaign=candidate.campaign,
        system=candidate.system, experiment=candidate.experiment, template=candidate.protocol,
        scientific_graph=candidate.scientific_graph, candidate=pin(candidate, 'candidate_id'), registry=registry,
        implementation_commit=sources[0].implementation_commit, frozen_proposal=None, authorization=None,
        approval_service=None, preissue_candidate=candidate)
    base = lower_run_plan(run, registry)
    # These resource references are disclosed unissued test operands. No
    # resource admission, authorization or worker dispatch is performed.
    extension = fixture_pin('extensions.disclosed.e1-closed', 'empirical-lawhood/runtime/issued-extension-set')
    plan = ExecutionPlan(**{field.name: getattr(base, field.name) for field in fields(base)},
        issued_extension_set=extension,
        execution_resource_envelope_spec=fixture_pin('resources.disclosed.e1-closed',
            'empirical-lawhood/runtime/execution-resource-envelope-spec'),
        predevelopment_jit_signature_census=None, jit_graph_signature_manifest=None)
    authority = SimpleNamespace(authorization_id='approval.disclosed.e1-closed')
    execution = SimpleNamespace(authority_id='execution.disclosed.e1-closed')
    reveal = SimpleNamespace(authority_id='reveal.disclosed.e1-closed')
    identities = tuple(fixture_pin(name, 'empirical-lawhood/testing/not-an-authority') for name in
        (authority.authorization_id, execution.authority_id, reveal.authority_id))
    index = RunRecoveryIndex.from_execution_plan(plan, run_id=run.run_plan_id,
        wave_id='wave.package.disclosed.e1-closed', authority_identities=identities)
    products, assessments = compact_products(e1[1], sources)
    return SimpleNamespace(plane=e1[0], spec=spec, selected=selected, draft=draft, sources=sources,
        registry=registry, candidate=candidate, plan=plan, index=index, products=products, assessments=assessments,
        authority=authority, execution=execution, reveal=reveal, identities=identities)


def closed(case, *, complete=(), kind='failed', publish=False):
    complete = set(complete)
    index = case.index
    summaries, events = [], []
    failure = OperationalFailureDiagnostic.create(OperationalFailureClass.RESOURCE_REFUSAL,
        sanitized_exception_type='DisclosedFailure', sanitized_message='Exposed control; no native execution')
    for task in case.plan.tasks:
        succeeded = task.task_id == owner.COMMIT_KEY or any(
            task.task_id == r.NAMESPACE+'.'+source.root_id+'.'+phase
            for source in case.sources if source.root_id in complete for phase in r.PHASES)
        if publish:
            succeeded = False
        binding = index.task(task.task_id)
        candidate, = binding.attempts
        if succeeded:
            summaries.append(RecoveryTerminalAttempt(candidate.attempt_id, task.task_id, 1,
                RecoveryTerminalDisposition.SUCCEEDED, None, 'receipt.'+candidate.attempt_id, 'b'*64))
            continue
        entered = ((not publish and (task.task_id.endswith('.history') or task.task_id == owner.KEY and len(complete) == len(case.sources)))
            or publish and kind == 'failed-terminal' and task.task_id == owner.COMMIT_KEY)
        unknown = entered and kind == 'unknown' and task.task_id.endswith('.history')
        reason = 'unknown-completion' if unknown else 'resource-computability-unavailable' if kind == 'blocked' else 'disclosed-worker-failure'
        disposition = RecoveryTerminalDisposition.BLOCKED if unknown or kind == 'blocked' else RecoveryTerminalDisposition.FAILED
        if entered:
            summary = RecoveryTerminalAttempt(candidate.attempt_id, task.task_id, 1, disposition, reason, None, None)
            event = TaskRecoveryEvent('recovery-event.'+candidate.attempt_id+'.failed', pin(index, 'recovery_index_id'),
                index.run_id, task.task_id, candidate.attempt_id, 1, TaskRecoveryDisposition(disposition.value),
                None, None, None, None, (), (reason,), failure)
        else:
            reason = 'campaign-elapsed-budget-exhausted' if task.task_id == owner.COMMIT_KEY else 'dependency-failed'
            summary = RecoveryTerminalAttempt(index.run_id+'.'+task.task_id+'.block-001', task.task_id, 1,
                RecoveryTerminalDisposition.BLOCKED, reason, None, None)
            event = TaskRecoveryEvent('recovery-event.'+index.run_id+'.'+task.task_id+'.not-attempted',
                pin(index, 'recovery_index_id'), index.run_id, task.task_id, None, None,
                TaskRecoveryDisposition.NOT_ATTEMPTED, None, None, None, None, (), (reason,))
        summaries.append(summary)
        events.append(event)
    terminal = RunRecoveryTerminalEvent('terminal.disclosed.e1-closed', pin(index, 'recovery_index_id'),
        index.run_id, 'FAILED' if any(row.disposition is RecoveryTerminalDisposition.FAILED for row in summaries) else 'BLOCKED',
        tuple(summaries), *(tuple(row.task_id for row in summaries if row.disposition is disposition)
            for disposition in (RecoveryTerminalDisposition.SUCCEEDED, RecoveryTerminalDisposition.FAILED, RecoveryTerminalDisposition.BLOCKED)))
    missing = []
    for source in case.sources:
        gaps = tuple(row for row in summaries if row.task_id.startswith(r.NAMESPACE+'.'+source.root_id+'.')
            and row.disposition is not RecoveryTerminalDisposition.SUCCEEDED)
        if not gaps:
            continue
        selected_events = tuple(row for row in events if row.task_id in {gap.task_id for gap in gaps})
        unknown = next((row for row in gaps if row.reason_code == 'unknown-completion'), None)
        contact = None if unknown is None else NativeEffectContact(index.run_id, unknown.task_id, unknown.attempt_id,
            index.execution_plan, pin(next(task for task in case.plan.tasks if task.task_id == unknown.task_id), 'task_id'),
            case.plan.implementation_commit, (), ())
        missing.append(r.E1CompactClosedRoot(source.identity, case.plan.implementation_commit, gaps, selected_events, contact))
    if publish:
        store = ExternalRunRecoveryStore(case.plane)
        store.freeze(index)
        for event in events:
            store.append_event(index, event)
        # Publication uses the same immutable terminal contract as the runtime;
        # the original store owns serialization, paths and member manifests.
        from empirical_lawhood.runtime.execution import OperationalAttempt, TaskAttemptDisposition
        from empirical_lawhood.kernel.status import OperationalStatus
        attempts = tuple(OperationalAttempt(row.attempt_id, index.run_id, row.task_id, row.ordinal,
            TaskAttemptDisposition(row.disposition.value), row.reason_code, None, None) for row in summaries)
        store.record_terminal(index, status=OperationalStatus(terminal.operational_status), attempts=attempts, receipts=())
        terminal = store.read_terminal(index)
    return terminal, tuple(missing)


@pytest.mark.parametrize('kind', ('failed', 'blocked', 'unknown'))
def test_closed_population_keeps_every_root_and_unknown_interval(case, kind):
    first = case.sources[0].root_id
    terminal, missing = closed(case, complete=(first,), kind=kind)
    result = science.reduce_closed_population(case.selected.manifest, case.sources,
        case.products[:1], case.assessments[:1], unavailable=missing,
        plan=case.plan, index=case.index, terminal=terminal)
    assert type(result) is r.E1CompactClosedPopulationResult
    assert len(result.root_ids) == 4 and len(result.unavailable) == 3 and len(result.events) == 16
    assert sum(row.primary for row in result.findings) == 8
    assert all(event.occurrence is None and event.first_admission_tick is None
        for event in result.events if event.root_id != first)
    assert all(row.interval.lower is None for row in result.findings
        if row.family_id != case.sources[0].coordinate.family_id and row.endpoint == 'BOTH')
    assert {row.availability for row in result.unavailable} == {'UNKNOWN_CONTACT' if kind == 'unknown' else 'UNAVAILABLE'}
    assert decode_canonical_bytes(result.canonical_bytes(),type(result),maximum_bytes=None)==result


def test_closed_adjudication_failure_preserves_exact_complete_population_math_and_old_bytes(case):
    complete = science.reduce_population(case.selected.manifest, case.sources, case.products, case.assessments)
    original = complete.canonical_bytes()
    terminal, missing = closed(case, complete=tuple(source.root_id for source in case.sources))
    reconstructed = science.reduce_closed_population(case.selected.manifest, case.sources,
        case.products, case.assessments, unavailable=missing, plan=case.plan, index=case.index, terminal=terminal)
    assert (reconstructed.events,reconstructed.findings,reconstructed.risk_rows)==(complete.events,complete.findings,complete.risk_rows)
    assert reconstructed.unavailable == () and complete.canonical_bytes() == original
    assert complete.VERSION == '2.0.0' and reconstructed.SCHEMA != complete.SCHEMA


@pytest.mark.parametrize('damage', ('omitted-root','foreign-event','foreign-source','success-terminal','lost-contact'))
def test_closed_population_refuses_changed_custody_and_thinned_denominators(case, damage):
    terminal, missing = closed(case, kind='unknown')
    with pytest.raises((ValueError,TypeError)):
        if damage=='omitted-root': missing=missing[:-1]
        elif damage=='foreign-event':
            row=missing[0]
            event=replace(row.recovery_events[0],recovery_index=replace(row.recovery_events[0].recovery_index,object_fingerprint='c'*64))
            missing=(replace(row,recovery_events=(event,*row.recovery_events[1:])),*missing[1:])
        elif damage=='foreign-source': missing=(replace(missing[0],implementation_commit='c'*40),*missing[1:])
        elif damage=='success-terminal': terminal=replace(terminal,operational_status='SUCCEEDED')
        else: missing=(replace(missing[0],contact=None),*missing[1:])
        science.reduce_closed_population(case.selected.manifest,case.sources,(),(),unavailable=missing,
            plan=case.plan,index=case.index,terminal=terminal)


@pytest.mark.parametrize('damage', (None, 'foreign-input', 'missing-dependency', 'revoked'))
def test_unreceipted_contact_rechecks_actual_frozen_input_members_before_dispatch(case,monkeypatch,damage):
    """Actual guarded members; the dependency receipt and dispatch are test metadata."""
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.artifacts import (
        ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt,
    )
    task=next(row for row in case.plan.tasks if row.task_id==r.NAMESPACE+'.'+case.sources[0].root_id+'.history')
    _,_,records=domain._derive(case.spec,case.selected)
    operands={record.fingerprint():record for _,record in records}
    raw_by_digest={key:record.canonical_bytes() for key,record in operands.items()}
    from hashlib import sha256
    for operation in case.draft.operations:
        raw=operation.config_payload.encode()
        raw_by_digest[sha256(raw).hexdigest()]=raw
    materials=[]
    for spec in task.external_inputs:
        relative,scope,directory=provider_input_location(case.plane,case.index.run_id,spec.logical_artifact_id)
        raw=raw_by_digest[spec.expected_content_sha256]
        parent=ArtifactLineageParent(ObjectIdentity(spec.logical_artifact_id,spec.expected_payload_schema,
            '1.0.0',spec.identity_scope_sha256 or spec.expected_content_sha256),
            spec.expected_visibility_ceiling,spec.expected_outcome_access)
        publication=case.plane.write(ArtifactWriteRequest(spec.logical_artifact_id,relative,
            spec.expected_payload_schema,ArtifactProfile.CANONICAL_JSON,spec.expected_media_type,
            scope,directory,raw,spec.expected_visibility_ceiling,(spec.expected_visibility_ceiling,),
            spec.expected_outcome_access,lineage_parents=(parent,)))
        materials.append(publication.materialization.materialization_id)
    dependency,=task.dependency_task_ids
    commit_task=next(row for row in case.plan.tasks if row.task_id==dependency)
    output,=commit_task.outputs
    commitment=r.commitment_for(case.selected.manifest,case.sources)
    publication=case.plane.write(ArtifactWriteRequest(output.logical_artifact_id,output.relative_path,
        output.payload_schema,output.profile,output.media_type,'disclosed.commit-output','runs',
        commitment.canonical_bytes(),VisibilityCeiling.PROSPECTIVE,(),
        OutcomeAccess.OUTCOME_BLIND))
    materials.append(publication.materialization.materialization_id)
    attempt,=case.index.task(dependency).attempts
    receipt=CanonicalTaskReceipt('receipt.'+attempt.attempt_id,case.index.run_id,dependency,
        attempt.attempt_id,case.plan.implementation_commit,(),(publication.materialization,),
        (publication.logical,),(),OperationalStatus.SUCCEEDED,())
    native_attempt,=case.index.task(task.task_id).attempts
    contact=NativeEffectContact(case.index.run_id,task.task_id,native_attempt.attempt_id,
        case.index.execution_plan,pin(task,'task_id'),case.plan.implementation_commit,
        tuple(sorted(materials)),(receipt.receipt_id,))
    closure=SimpleNamespace(by_task={dependency:receipt})
    dispatches=[]
    monkeypatch.setattr(reader,'authenticate_task_dispatch_authority',lambda **kwargs:dispatches.append(kwargs))
    checks=[]
    def current(_member=None):
        if damage=='revoked':raise PermissionError('disclosed revoked reveal')
        checks.append(True)
    if damage=='foreign-input':contact=replace(contact,input_materialization_ids=('material.foreign',))
    elif damage=='missing-dependency':closure=SimpleNamespace(by_task={})
    args=dict(task=task,plan=case.plan,package=SimpleNamespace(),closure=closure,
        writer=case.plane,require_current=current)
    if damage is None:
        reader._require_original_contact(contact,**args)
        assert len(checks)>2 and len(dispatches)==1
        assert dispatches[0]['attempt_id']==native_attempt.attempt_id
    else:
        with pytest.raises(PermissionError):reader._require_original_contact(contact,**args)
        assert dispatches==[]


def public_context(case, monkeypatch, *, kind='blocked-terminal'):
    terminal, _ = closed(case, publish=True,kind=kind)
    candidate = pin(case.candidate,'candidate_id')
    package = SimpleNamespace(package_id='package.disclosed.e1-closed', run_plan_id=case.index.run_id,
        registry=case.registry, scientific_approval=case.authority, execution_authority=case.execution,
        issued_study=SimpleNamespace(candidate=case.candidate,source_closure='disclosed.original.source'))
    original_pin=reader._pin
    def disclosed_pin(value, field):
        if value is package.issued_study:return fixture_pin('issue.disclosed.e1-closed','empirical-lawhood/testing/not-issued')
        if value in (case.authority,case.execution,case.reveal):
            return next(row for row in case.identities if row.object_id==getattr(value,field))
        return original_pin(value,field)
    monkeypatch.setattr(reader,'_pin',disclosed_pin)
    monkeypatch.setattr(reader,'_actual_package',lambda *args,**kwargs:package)
    monkeypatch.setattr(reader,'CurrentResultPlanReader',lambda *args:SimpleNamespace(
        authenticate_execution_plan=lambda **kwargs:case.plan,original_recovery_index=lambda **kwargs:case.index))
    monkeypatch.setattr(reader,'ExternalStudyOperationAuthorityStore',lambda *args:SimpleNamespace(load=lambda *_:case.reveal))
    monkeypatch.setattr(reader,'_replay_parent_authority',lambda *args:(package.issued_study,case.reveal))
    current=[]
    monkeypatch.setattr(reader,'require_current_result_reveal_authority',lambda **kwargs:current.append(kwargs['expected_identity']))
    # The shared recovery reader uses these two explicit unissued authority pins
    # while its on-disk index/events/terminal and source graph remain actual.
    from empirical_lawhood.api import recursive_qualified_parents as parents
    original_object_pin=parents.ObjectIdentity.from_record
    def parent_pin(identifier,value):
        if value in (case.authority,case.execution,case.reveal):
            return next(row for row in case.identities if row.object_id==identifier)
        return original_object_pin(identifier,value)
    monkeypatch.setattr(parents.ObjectIdentity,'from_record',parent_pin)
    selected=SimpleNamespace(payloads={SPECIFICATION_FILENAME:case.spec.canonical_bytes(),
        source_filename(case.selected.identity):case.selected.canonical_bytes()},
        instance=SimpleNamespace(specification=case.spec.identity,sources=(case.selected.identity,),
            allocation=domain.population_allocation(case.spec,case.sources).identity),
        association=SimpleNamespace(candidate=candidate),implementation='disclosed.original.source',
        projection=case.plan,draft=case.draft)
    return selected, terminal, current


@pytest.mark.parametrize('kind',('blocked-terminal','failed-terminal'))
def test_public_closed_nonentry_uses_actual_terminal_events_and_full_denominator(case,monkeypatch,kind):
    selected,terminal,current=public_context(case,monkeypatch,kind=kind)
    result=reader.read_result(selected=selected,artifact_writer=case.plane,run_id=case.index.run_id,
        reveal_authority_id=case.reveal.authority_id)
    assert result['scientific_completion']=='CLOSED_CUSTODY_REDUCTION'
    assert result['adjudication'] is None and result['new_native_contact_count']==0
    assert result['denominators']['confirmation']==dict(assigned_units=4,assessed_units=0,
        numerically_usable_units=0,unavailable_units=4,unknown_contact_units=0)
    assert len(result['missing_roots'])==4 and len(result['task_census'])==18
    assert result['operational_terminal']==pin(terminal,'terminal_event_id').to_document()
    assert len(current)>4


def test_public_missing_reveal_stays_before_scientific_sources(case,monkeypatch):
    selected,_,_=public_context(case,monkeypatch)
    monkeypatch.setattr(reader,'original_selection',lambda *_:pytest.fail('scientific sources opened before reveal'))
    with pytest.raises(PermissionError,match='current reveal authority'):
        reader.read_result(selected=selected,artifact_writer=case.plane,run_id=case.index.run_id)


def test_public_revoked_reveal_refuses_before_population_reduction(case,monkeypatch):
    selected,_,_=public_context(case,monkeypatch)
    def revoked(**kwargs):raise PermissionError('disclosed revoked reveal')
    monkeypatch.setattr(reader,'require_current_result_reveal_authority',revoked)
    monkeypatch.setattr(science,'reduce_closed_population',lambda *args,**kwargs:pytest.fail('revoked read reduced observations'))
    with pytest.raises(PermissionError,match='revoked reveal'):
        reader.read_result(selected=selected,artifact_writer=case.plane,run_id=case.index.run_id,
            reveal_authority_id=case.reveal.authority_id)


@pytest.mark.parametrize('damage',('missing-terminal','corrupt-event','late-orphan-contact'))
def test_public_closed_read_refuses_missing_changed_and_late_custody(case,monkeypatch,damage):
    selected,_,_=public_context(case,monkeypatch)
    if damage=='missing-terminal':
        # This is disposable exposed test custody, never a retained run.
        for suffix in ('','.manifest.json'):
            case.plane.root.resolve(case.index.terminal_event_relative_path+suffix,for_write=False).unlink()
    elif damage=='corrupt-event':
        relative=case.index.task(r.NAMESPACE+'.'+case.sources[0].root_id+'.history').nonattempt_event_relative_path
        case.plane.root.resolve(relative,for_write=False).write_bytes(b'corrupt exposed event\n')
    else:
        original=science.reduce_closed_population
        def changed(*args,**kwargs):
            value=original(*args,**kwargs)
            from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
            relative=ExternalNativeEffectContactStore._path(case.index.run_id,r.NAMESPACE+'.'+case.sources[0].root_id+'.history')
            path=case.plane.root.resolve(relative,for_write=False)
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(b'orphaned exposed contact\n')
            return value
        monkeypatch.setattr(science,'reduce_closed_population',changed)
    with pytest.raises((PermissionError,ValueError,RuntimeError)):
        reader.read_result(selected=selected,artifact_writer=case.plane,run_id=case.index.run_id,
            reveal_authority_id=case.reveal.authority_id)
