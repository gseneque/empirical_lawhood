# SPDX-License-Identifier: MPL-2.0
"""Current authorized compact E1 replay; no provider, native work or eigensolve.

The ordinary retained companion owns the complete original draft/instance join;
CurrentResultPlanReader owns issued-plan, current grants and receipt closure.
This consumer joins exact original compact operands and independently replays the
native/factor witnesses and complete terminal reduction, once per actual root.
"""
from types import SimpleNamespace
from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_records as r,compact_science as science,compact_bindings as owner,compact_preparation as domain
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.compact_publications import authenticate_prior_publications
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.occurrence import cell_report
from empirical_lawhood.api.current_result_custody import (
    CurrentResultPlanReader, retained_output_artifact_plane, authenticate_task_dispatch_authority,
    require_current_result_reveal_authority,
)
from empirical_lawhood.api.recursive_qualified_parents import _actual_package,_replay_parent_authority,_collect_receipt_closure,_verify_receipt_closure,_output_payload
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from .matrix_retained_replay import map_reconstructions, replay_e1, replay_weight
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.recursive_custody import (
    _execution_operational_census, _require_no_orphaned_native_custody,
)
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.kernel.status import AdmissionStatus,OperationalStatus,ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability,ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, artifact_custody_limits
from empirical_lawhood.runtime.execution import VerifiedArtifactInput, dependency_artifact_inputs
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent
from empirical_lawhood.runtime.plans import BarrierKind,ScientificStage
from empirical_lawhood.runtime.prospective_experiment import SPECIFICATION_FILENAME,source_filename


def _pin(record,field):return ObjectIdentity.from_record(getattr(record,field),record)


def _decode(raw,kind):
    return decode_canonical_bytes(raw,kind,maximum_bytes=len(raw))


def deferred(specification):
    return {'scientific_completion':'NOT_ESTABLISHED','scientific_status':'UNEVALUABLE','admission_status':'UNEVALUABLE',
        'evaluability':'DEFERRED','reason_codes':('COMPACT_E1_PARTIAL_SCIENTIFIC_READ_DEFERRED',),
        'denominators':{'confirmation':{'assigned_units':len(specification.root_ids),'assessed_units':None}},'new_native_contact_count':0}


def original_selection(selected,specification):
    kinds={(kind.SCHEMA,kind.VERSION):kind for kind in domain.selection_types()}
    refs=tuple(ref for ref in selected.instance.sources if (ref.object_schema,ref.object_version) in kinds)
    if len(refs)!=1 or len(selected.instance.sources)!=1:raise PermissionError('compact E1 read requires one exact original scientific/entry selection')
    reference,=refs
    selection=_decode(selected.payloads[source_filename(reference)],kinds[(reference.object_schema,reference.object_version)])
    sources=r.sources_for_manifest(selection.manifest)
    if (ObjectIdentity.from_record(reference.object_id,selection)!=reference or selection.identity!=specification.selection
            or tuple(source.root_id for source in sources)!=specification.root_ids or selection.root.question!=specification.question
            or domain.population_allocation(specification,sources).identity!=selected.instance.allocation):
        raise PermissionError('compact E1 read changes original selection or complete independent allocation')
    return selection,sources


def exact_graph(selection,sources,draft,plan):
    tasks={task.task_id:task for task in plan.tasks};expected={}
    for source in sources:
        for phase in r.PHASES:
            node=r.NAMESPACE+'.'+source.root_id+'.'+phase
            expected[node]=r.E1CompactOperationConfig('config.'+node,phase,source)
    expected[owner.COMMIT_KEY]=owner.E1CompactCommitmentConfig('config.'+owner.COMMIT_KEY,selection.manifest)
    expected[owner.KEY]=owner.E1CompactAdjudicationConfig('config.'+owner.KEY,sources[0].manifest,selection.manifest.specification.selection.criterion,sources)
    if (len(tasks)!=len(plan.tasks) or set(tasks)!=set(expected) or draft.selected_operation_ids!=tuple(sorted(expected))
            or tuple(row.node_id for row in draft.operations)!=tuple(sorted(expected)) or draft.prospective_draft!=selection.root
            or draft.campaign!=selection.root.campaign):raise PermissionError('compact E1 read changes complete original graph/root census')
    budgets=dict(domain.selection_task_budgets(selection,sources))
    proof_by_node={}
    for obligation,node in domain.selection_proof_owners(selection,sources):proof_by_node.setdefault(node,[]).append(obligation)
    for operation in draft.operations:
        task=tasks[operation.node_id];config=expected[operation.node_id]
        phase='commit' if operation.node_id==owner.COMMIT_KEY else 'adjudicate' if operation.node_id==owner.KEY else config.operation
        stage=ScientificStage.FREEZE if phase=='commit' else ScientificStage.REVEAL if phase=='adjudicate' else next(row[3] for row in owner.PHASES if row[0]==phase)
        access=OutcomeAccess.OUTCOME_BLIND if phase=='commit' else OutcomeAccess.EVALUATOR_REVEAL if phase=='adjudicate' else OutcomeAccess.EVALUATION_SEALED
        output_kind=r.E1CompactCommitment if phase=='commit' else r.E1CompactPopulationResult if phase=='adjudicate' else next(row[2] for row in owner.PHASES if row[0]==phase)
        outputs={('product',output_kind.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json')}
        if phase in ('history','measure'):outputs.add(('arrays',r.MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz'))
        if phase=='adjudicate':outputs.add(('adjudication',ScientificAdjudicationRecord.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json'))
        obligations=tuple(proof_by_node.get(operation.node_id,()))
        if (operation.config_payload.encode()!=config.canonical_bytes() or operation.config_id!=config.config_id
                or operation.selection.capability_key!=r.NAMESPACE+'.'+phase or operation.selection.capability_version!='1.0.0'
                or task.capability.capability_key!=operation.selection.capability_key or task.capability.capability_version!=operation.selection.capability_version
                or task.capability_implementation_sha256!=operation.selection.implementation_sha256 or task.stage is not stage
                or task.capability.requested_outcome_access is not access or task.capability.config.content_sha256!=config.fingerprint()
                or task.capability.config.config_id!=config.config_id or task.capability.config.config_schema!=config.SCHEMA
                or operation.resource_budget!=budgets[operation.node_id] or task.capability.requested_resources!=budgets[operation.node_id]
                or operation.maximum_attempts!=1 or task.maximum_attempts!=1 or operation.resource_lock_ids or task.resource_lock_ids
                or operation.obligation_ids!=obligations or task.obligation_ids!=obligations
                or {(row.output_id.removeprefix(task.task_id+'.'),row.payload_schema,row.profile,row.media_type) for row in task.outputs}!=outputs or len(task.outputs)!=len(outputs)
                or task.barrier is not (BarrierKind.FREEZE if phase=='commit' else BarrierKind.REVEAL if phase=='adjudicate' else BarrierKind.NONE)):
            raise PermissionError('compact E1 read changes exact retained phase/configuration/resource/output contract')
    return tasks,expected


def payload(writer,receipts,tasks,node,output, *, before_member=None):
    task=tasks[node];receipt=receipts.get(node);rows=tuple(row for row in task.outputs if row.output_id==node+'.'+output)
    if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED or len(rows)!=1:raise PermissionError('compact E1 read lacks exact successful producing receipt')
    planned,=rows
    logicals=tuple(row for row in receipt.output_logical_artifacts if row.logical_artifact_id==planned.logical_artifact_id)
    physicals=tuple(row for row in receipt.output_materializations if row.logical_artifact_id==planned.logical_artifact_id)
    if len(logicals)!=1 or len(physicals)!=1:raise PermissionError('compact E1 read changes exact output publication')
    return _output_payload(writer,receipt,logicals[0],physicals[0].size_bytes, before_member=before_member)


def _closed_root(*, source, tasks, closure, terminal, plan, package, writer, require_current):
    """Join actual original gaps; no failed receipt, contact or event is invented."""
    index = closure.recovery_index
    recovery = ExternalRunRecoveryStore(writer)
    summaries, events = [], []
    contact = None
    for phase in r.PHASES:
        node = r.NAMESPACE+'.'+source.root_id+'.'+phase
        if node in closure.by_task:
            continue
        require_current()
        task, summary = tasks[node], closure.operational_summaries[node]
        binding = index.task(node)
        candidate = next((row for row in binding.attempts if row.attempt_id == summary.attempt_id), None)
        event_path = binding.nonattempt_event_relative_path if candidate is None else candidate.event_relative_path
        event = recovery.read_event(index, event_path)
        if event is not None:
            events.append(event)
        summaries.append(summary)
        contacts = ExternalNativeEffectContactStore(plane=writer, execution_plan=index.execution_plan,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.EVALUATION_SEALED)
        actual = contacts.read(index.run_id, node)
        if actual is None:
            _require_no_orphaned_native_custody(plane=writer, run_id=index.run_id, task_id=node)
            continue
        if phase != 'history' or candidate is None:
            raise PermissionError('closed E1 pure or unentered task has unexpected native contact')
        _require_original_contact(actual, task=task, plan=plan, package=package,
            closure=closure, writer=writer, require_current=require_current)
        contact = actual
    result = r.E1CompactClosedRoot(r.identity(source), plan.implementation_commit,
        tuple(sorted(summaries, key=lambda row: row.task_id)),
        tuple(sorted(events, key=lambda row: row.task_id)), contact)
    if any(row not in terminal.attempts for row in result.terminal_attempts):
        raise PermissionError('closed E1 gap substitutes its exact operational terminal')
    return result


def _require_original_contact(contact, *, task, plan, package, closure, writer, require_current):
    """Authenticate an actual dispatch and its frozen operands without a receipt."""
    require_current()
    dependencies = {}
    for node in task.dependency_task_ids:
        receipt = closure.by_task.get(node)
        if receipt is None:
            raise PermissionError('closed E1 native contact lacks an actual successful dependency')
        logicals = {row.logical_artifact_id: row for row in receipt.output_logical_artifacts}
        dependencies[node] = tuple(VerifiedArtifactInput(logicals[row.logical_artifact_id], row)
            for row in receipt.output_materializations)
    material_ids = {row.materialization.materialization_id
        for row in dependency_artifact_inputs(task, dependencies)}
    for spec in task.external_inputs:
        path, _, _ = provider_input_location(writer, plan.source_plan.object_id, spec.logical_artifact_id)
        manifest = writer.read_manifest(path, maximum_bytes=artifact_custody_limits(writer).manifest_bytes)
        logical, physical = manifest.logical, manifest.materialization
        if (logical.logical_artifact_id != spec.logical_artifact_id or physical.relative_path != path
                or physical.storage_root_id != writer.root.contract.storage_root_id or manifest.publication is None
                or physical.compression != 'none' or physical.partition_selector is not None
                or any(expected is not None and actual != expected for actual, expected in (
                    (logical.content_sha256, spec.expected_content_sha256),
                    (logical.payload_schema, spec.expected_payload_schema),
                    (logical.media_type, spec.expected_media_type), (physical.size_bytes, spec.expected_size_bytes),
                    (logical.visibility_ceiling, spec.expected_visibility_ceiling),
                    (logical.outcome_access, spec.expected_outcome_access)))
                or spec.identity_scope_sha256 is not None and not any(
                    row.identity.object_fingerprint == spec.identity_scope_sha256 for row in logical.lineage_parents)):
            raise PermissionError('closed E1 native contact changes its exact original external input')
        writer.verify_manifest(manifest, before_member=require_current)
        material_ids.add(physical.materialization_id)
    expected = NativeEffectContact(plan.source_plan.object_id, task.task_id, contact.attempt_id,
        _pin(plan, 'execution_plan_id'), ObjectIdentity.from_record(task.task_id, task), plan.implementation_commit,
        tuple(sorted(material_ids)), tuple(sorted(closure.by_task[node].receipt_id for node in task.dependency_task_ids)))
    if contact != expected:
        raise PermissionError('closed E1 native contact changes its original source, inputs or task')
    authenticate_task_dispatch_authority(package=package, execution_plan=plan,
        run_id=contact.run_id, task_id=contact.task_id, attempt_id=contact.attempt_id, writer=writer)
    require_current()


def _require_closed_contacts_unchanged(writer, index, unavailable, require_current):
    """Recheck negative observations before returning a closed scientific read."""
    contacts = ExternalNativeEffectContactStore(plane=writer, execution_plan=index.execution_plan,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.EVALUATION_SEALED)
    for root in unavailable:
        for gap in root.terminal_attempts:
            require_current()
            expected = root.contact if root.contact is not None and root.contact.task_id == gap.task_id else None
            if contacts.read(index.run_id, gap.task_id) != expected:
                raise PermissionError('closed E1 native contact changed during its scientific read')
            if expected is None:
                _require_no_orphaned_native_custody(plane=writer,run_id=index.run_id,task_id=gap.task_id)


def validate_adjudication(adjudication,result,criterion,config,plan,receipts):
    receipt=receipts[owner.KEY];task=next(row for row in plan.tasks if row.task_id==owner.KEY)
    expected=(plan.source_plan.object_id,owner.KEY,_pin(plan,'execution_plan_id'),receipt.input_materialization_ids,
        tuple(sorted(row.logical_artifact_id for row in receipt.output_logical_artifacts)),tuple(sorted(receipts[node].receipt_id for node in task.dependency_task_ids)),
        criterion.world_id,criterion.relation,criterion.independent_unit_id,tuple(ObjectIdentity.from_record(value.cutoff_id,value) for value in owner.cutoffs(config)))
    actual=(adjudication.run_id,adjudication.adjudication_task_id,adjudication.execution_plan,adjudication.input_materialization_ids,
        adjudication.output_logical_artifact_ids,adjudication.required_receipt_ids,adjudication.evidence_world_id,adjudication.relation,adjudication.independent_unit_id,adjudication.information_cutoffs)
    evaluable=result.scientific_status is not ScientificStatus.UNEVALUABLE
    if (actual!=expected or adjudication.scientific_status is not result.scientific_status or adjudication.reason_codes!=result.reason_codes
            or adjudication.evaluability is not (AdjudicationEvaluability.EVALUABLE if evaluable else AdjudicationEvaluability.UNEVALUABLE)
            or adjudication.admission_status is not (AdmissionStatus.NOT_EVALUATED if evaluable else AdmissionStatus.UNEVALUABLE)
            or adjudication.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
            or adjudication.outcome_access is not OutcomeAccess.EVALUATION_REVEALED or adjudication.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or adjudication.plumbing_only or adjudication.fixture_scope_id is not None):raise PermissionError('compact E1 read changes actual issued/revealed scientific adjudication')


def read_result(*,selected,artifact_writer,run_id,reveal_authority_id=None,allow_partial=False):
    validate_stable_id(run_id)
    if type(allow_partial) is not bool:raise TypeError('compact E1 partial read must be explicit')
    specification=_decode(selected.payloads[SPECIFICATION_FILENAME],domain.E1CompactExperimentSpecification)
    if specification.identity!=selected.instance.specification:raise PermissionError('compact E1 read substitutes original specification edition')
    # This effect-free control census owns one complete final byte check.
    # Per-task lookups retain current access without hashing every earlier
    # control again for each member of the original receipt roster.
    with artifact_writer.read_context() as controls:
        reader=CurrentResultPlanReader(controls);package=_actual_package(controls,run_id,control_reader=reader)
        if (_pin(package.issued_study.candidate,'candidate_id')!=selected.association.candidate or package.issued_study.source_closure!=selected.implementation or package.run_plan_id!=run_id):raise PermissionError('compact E1 read changes original candidate/source/run')
        plan=reader.authenticate_execution_plan(package=package,issued=package.issued_study,run_id=run_id)
        if {task.task_id for task in plan.tasks}!={task.task_id for task in selected.projection.tasks}:raise PermissionError('compact E1 read changes complete retained task projection')
        if allow_partial:return deferred(specification)
        if reveal_authority_id is None:raise PermissionError('compact E1 scientific read requires genuine current reveal authority')
        reveal=ExternalStudyOperationAuthorityStore(artifact_writer).load(reveal_authority_id)
        _,reveal=_replay_parent_authority(SimpleNamespace(issued_study=_pin(package.issued_study,'issue_id'),execution_authority=_pin(package.execution_authority,'authority_id'),reveal_authority=_pin(reveal,'authority_id')),package,artifact_writer)
        reveal_identity = _pin(reveal, 'authority_id')
        def require_current(_member=None):
            require_current_result_reveal_authority(writer=artifact_writer, package=package,
                reveal_authority_id=reveal_authority_id, expected_identity=reveal_identity)
        selection,sources=original_selection(selected,specification)
        tasks,configs=exact_graph(selection,sources,selected.draft,plan)
        authenticate_prior_publications(artifact_writer,(SimpleNamespace(record=configs[owner.COMMIT_KEY]),))
        codecs={kind.SCHEMA:kind for kind in (r.E1CompactCommitment,r.E1CompactNativeHistory,r.E1CompactNumericalAssessment,r.E1CompactFactorProduct,r.E1CompactFactorAssessment,r.E1CompactPopulationResult,ScientificAdjudicationRecord)}
        semantic=retained_output_artifact_plane(package,plan,artifact_writer,codecs)
        closure=_collect_receipt_closure(package,plan,semantic,reveal,(r.NAMESPACE+'.',),
            control_reader=reader,allow_partial=True)
        terminal=ExternalRunRecoveryStore(controls).read_terminal(closure.recovery_index)
        if (type(terminal) is not RunRecoveryTerminalEvent
                or terminal.operational_status not in ('SUCCEEDED','FAILED','BLOCKED')):
            raise PermissionError('compact E1 scientific read requires actual closed operational custody')
        closed=terminal.operational_status!='SUCCEEDED'
        if not closed and (terminal.completed_task_ids!=tuple(task.task_id for task in plan.tasks)
                or terminal.failed_task_ids or terminal.blocked_task_ids):
            raise PermissionError('compact E1 successful terminal changes the complete task census')
    with semantic.read_context() as writer:
        require_current()
        receipts=_verify_receipt_closure(writer,closure,before_member=require_current)
        def original_payload(node, output):
            return payload(writer,receipts,tasks,node,output,before_member=require_current)
        if owner.COMMIT_KEY in receipts:
            commitment=_decode(original_payload(owner.COMMIT_KEY,'product'),r.E1CompactCommitment)
            if commitment!=r.commitment_for(selection.manifest,sources):raise PermissionError('compact E1 read changes actual pre-contact source commitment')
        elif not closed:
            raise PermissionError('compact E1 completed read lacks its pre-contact commitment')
        recovery=ExternalRunRecoveryStore(writer)
        if (recovery.read_index(closure.recovery_index.index_relative_path,
                expected_schema=closure.recovery_index.SCHEMA)!=closure.recovery_index
                or recovery.read_terminal(closure.recovery_index)!=terminal):
            raise PermissionError('compact E1 operational custody changed during its scientific read')
        products=[];assessments=[];unavailable=[]
        def reconstruction_inputs():
            for source in sources:
                nodes={phase:r.NAMESPACE+'.'+source.root_id+'.'+phase for phase in r.PHASES}
                if not set(nodes.values()).issubset(receipts):
                    if not closed:
                        raise PermissionError('compact E1 completed read omits a successful root phase')
                    unavailable.append(_closed_root(source=source,tasks=tasks,closure=closure,terminal=terminal,
                        plan=plan,package=package,writer=writer,require_current=require_current))
                    continue
                history=_decode(original_payload(nodes['history'],'product'),r.E1CompactNativeHistory)
                numerical=_decode(original_payload(nodes['numerical'],'product'),r.E1CompactNumericalAssessment)
                product=_decode(original_payload(nodes['measure'],'product'),r.E1CompactFactorProduct)
                assessment=_decode(original_payload(nodes['check'],'product'),r.E1CompactFactorAssessment)
                for record,phase in ((history,'history'),(product,'measure')):
                    planned=next(output for output in tasks[nodes[phase]].outputs if output.output_id==nodes[phase]+'.arrays')
                    if record.arrays.array_artifact.artifact_id!=planned.logical_artifact_id:raise PermissionError('compact E1 read changes actual ordinary native/diagnostic array publication')
                native=original_payload(nodes['history'],'arrays');diagnostics=original_payload(nodes['measure'],'arrays')
                require_current()
                root_receipts=tuple(receipts[node] for node in nodes.values())
                yield replay_weight(records=(source,history,numerical,product,assessment,*root_receipts),
                    archives=((native,history.arrays),(diagnostics,product.arrays))), (
                    source,history,numerical,product,assessment,native,diagnostics,root_receipts)
                products.append(product);assessments.append(assessment)
        replayed=map_reconstructions(writer,replay_e1,reconstruction_inputs())
        if replayed!=tuple(product.traces[0].root.root_id for product in products):
            raise PermissionError('compact E1 reconstruction changes the complete ordered root census')
        require_current()
        if closed:
            if owner.KEY in receipts:
                raise PermissionError('closed E1 task census contradicts a successful adjudication')
            result=science.reduce_closed_population(selection.manifest,sources,tuple(products),tuple(assessments),
                unavailable=tuple(unavailable),plan=plan,index=closure.recovery_index,terminal=terminal)
            adjudication=None
        else:
            result=_decode(original_payload(owner.KEY,'product'),r.E1CompactPopulationResult)
            if result!=science.reduce_population(selection.manifest,sources,tuple(products),tuple(assessments)):raise PermissionError('compact E1 read changes complete occurrence/survival/risk/alpha reduction')
            adjudication=_decode(original_payload(owner.KEY,'adjudication'),ScientificAdjudicationRecord)
            validate_adjudication(adjudication,result,selection.manifest.specification.selection.criterion,configs[owner.KEY],plan,receipts)
        # The same common owner checks the original task census at entry and
        # return. A newly appearing receipt/event cannot be hidden as a gap.
        _execution_operational_census(recovery=recovery,store=ExternalTaskReceiptStore(writer),
            plan=plan,index=closure.recovery_index,terminal=terminal)
        if closed:
            _require_closed_contacts_unchanged(writer,closure.recovery_index,unavailable,require_current)
        writer.require_verification_snapshot()
        require_current()
    require_current()
    report={'scientific_completion':'CLOSED_CUSTODY_REDUCTION' if closed else 'RETAINED_ADJUDICATION',
        'scientific_status':result.scientific_status.value,
        'admission_status':'UNEVALUABLE' if closed else adjudication.admission_status.value,
        'evaluability':'RECONSTRUCTED_WITHOUT_ADJUDICATION' if closed else adjudication.evaluability.value,
        'denominators':{'confirmation':{'assigned_units':len(sources),'assessed_units':len(products),
            'numerically_usable_units':sum(product.history_numerical_pass and assessment.numerical_pass for product,assessment in zip(products,assessments,strict=True))}},
        'primary_alpha':{'numerator':result.primary_alpha_numerator,'denominator':result.primary_alpha_denominator},
        'cell_alpha':{'numerator':result.cell_alpha_numerator,'denominator':result.cell_alpha_denominator},
        'occurrence_end_tick':selection.manifest.specification.selection.criterion.occurrence_end_tick,
        'survival_origin_end_tick':selection.manifest.specification.selection.criterion.survival_origin_end_tick,
        'occurrence_map':tuple(cell_report(cell) for cell in result.findings),
        'result':result.to_document(),'adjudication':None if closed else adjudication.to_document(),
        'execution_plan':_pin(plan,'execution_plan_id').to_document(),
        'typed_product_validation':('COMPLETE_ASSESSED_ROOTS_AND_AUTHENTICATED_INCOMPLETE_CUSTODY'
            if closed else 'COMPLETE'),'new_native_contact_count':0}
    if closed:
        report.update(operational_status=terminal.operational_status,
            operational_terminal=_pin(terminal,'terminal_event_id').to_document(),
            qualification='NOT_ESTABLISHED',sampling_warrant='NOT_ESTABLISHED',
            missing_roots=tuple(row.to_document() for row in unavailable),
            task_census=tuple(row.to_document() for row in terminal.attempts))
        report['denominators']['confirmation'].update(unavailable_units=len(unavailable),
            unknown_contact_units=sum(row.availability=='UNKNOWN_CONTACT' for row in unavailable))
    return report
