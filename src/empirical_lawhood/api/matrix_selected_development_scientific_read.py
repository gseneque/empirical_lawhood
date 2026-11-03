# SPDX-License-Identifier: MPL-2.0
"""Ordinary complete E5DEV scientific projection from current read context.

The common development reader has already authenticated the actual authored
instance, graph, plan and receipt closure. Original protected parents still
use their existing current issue/reveal owners once. No nomination/headroom
predicate authorizes this read; adverse and no-opportunity outcomes are kept.
"""
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_prepared_choices as scientific_choices
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity as opportunity
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_bindings as original
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_bindings as revision
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as declarative
from empirical_lawhood.adapters.methods.matrix_experimental_programme.functional_case_reduction import native_functional_case
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_secondary_readout import prepared_secondary_projection
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import MatrixSelectedOpportunityRootConfigV2,MatrixSelectedOpportunityEvidenceV2
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_results import assess_revision_programme
from .matrix_selected_opportunity_runtime import _authenticate_original_products
from .matrix_selected_scientific_read import (
    _pin,_decode,_configuration,_consumed,_product,_original_source_operands,revision_entry_seal,_science_edges,
    _replay_matched_revision_case,
)
from .matrix_selected_runtime import _published_input
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.runtime.prospective_experiment import source_filename


def _selected_programme(specification,instance,payloads,entry,is_revision):
    programme=entry.programme
    if type(specification) is not scientific_choices.SelectedPreparedDevelopmentSpecification:
        raise PermissionError('E5DEV read requires the current declarative scientific specification')
    kind=declarative.SelectedPreparedDerivedSelectionV4
    matches=tuple(ref for ref in instance.sources if
        (ref.object_schema,ref.object_version)==(kind.SCHEMA,kind.VERSION))
    if len(matches)!=1:raise PermissionError('E5DEV read lacks exact declarative derived selection')
    ref,=matches;selection=_decode(payloads[source_filename(ref)],kind)
    if (selection.identity!=ref or declarative.validate_selection(specification,selection)!=programme
            or _pin(selection.evidence)!=(entry.entry_evidence if is_revision else entry.evidence)
            or is_revision!=(specification.account=='REVISION')):
        raise PermissionError('E5DEV read substitutes actual declarative programme, account or evidence')
    allocation=declarative.allocation(programme)
    if (programme.phase!='E5_OPPORTUNITY' or instance.specification!=specification.identity or instance.allocation!=allocation.identity):
        raise PermissionError('E5DEV read changes actual development phase or complete assigned allocation')
    return programme


def _evidence(writer,run_id,task,entry,is_revision,*,custody=None):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import MatrixRevisionEntryEvidenceV2
    pin=entry.entry_evidence if is_revision else entry.evidence
    kinds=(MatrixRevisionEntryEvidenceV2,) if is_revision else (MatrixSelectedOpportunityEvidenceV2,)
    kinds=tuple(kind for kind in kinds if (kind.SCHEMA,kind.VERSION)==(pin.object_schema,pin.object_version))
    specs=tuple(row for row in task.external_inputs if row.logical_artifact_id!=task.capability.config.artifact_id)
    bound=entry.entry_evidence_size_bytes if is_revision else entry.evidence_size_bytes
    if len(kinds)!=1 or len(specs)!=1 or specs[0].expected_size_bytes!=bound:
        raise PermissionError('E5DEV read changes its actual complete original evidence input')
    evidence=_published_input(writer,run_id,specs[0],kinds[0],custody=custody)
    if evidence.identity!=pin:raise PermissionError('E5DEV read substitutes actual original evidence bytes')
    return evidence



def _science(writer,run_id,programme,entry_task,entry,is_revision,products,plan,original_allocation,*,custody=None,original_input_access=None,reconstruct=True):
    from functools import partial
    configuration=partial(_configuration,custody=custody) if custody is not None else _configuration
    consumed=partial(_consumed,original_input_access=original_input_access) if original_input_access is not None else _consumed
    product=partial(_product,original_input_access=original_input_access) if original_input_access is not None else _product
    owner=revision if is_revision else original
    tasks={task.task_id:task for task in plan.tasks};receipts=products['receipts']
    if len(tasks)!=len(plan.tasks) or set(receipts)!=set(tasks):
        raise PermissionError('E5DEV read lacks complete actual successful receipt census')
    phase='assess-programme' if is_revision else 'nominate'
    task=tasks.get(owner.global_node(programme,phase))
    expected_key=revision.capability_key(phase,'DEVELOPMENT') if is_revision else original.NAMESPACE+'.'+phase
    if task is None or task.capability.capability_key!=expected_key:
        raise PermissionError('E5DEV read changes its exact actual terminal producer')
    final=configuration(writer,run_id,task,(revision.MatrixRevisionRootConfig,) if is_revision else (original.MatrixSelectedOpportunityRootConfig,))
    if final.phase!=phase or final.programme!=programme:
        raise PermissionError('E5DEV read substitutes actual terminal scientific programme')
    port='entry' if is_revision else 'design'
    seal=consumed(writer,receipts,tasks,task,port,owner.OUTPUTS[port],producer=entry_task.task_id)
    expected=revision_entry_seal(programme) if is_revision else opportunity.opportunity_seal(programme)
    if seal!=expected:raise PermissionError('E5DEV read changes actual successful entry/design seal')
    expected_inputs={port};observations={};mechanism={}
    if is_revision:
        actual=consumed(writer,receipts,tasks,task,'original-allocation',UnitAllocation,producer=entry_task.task_id,output='original-allocation')
        if actual!=original_allocation:raise PermissionError('E5DEV read substitutes actual original allocation')
        expected_inputs.add('original-allocation')
    sources=programme.source_arms() if is_revision else tuple((None,source) for source in programme.sources.sources)
    for _,source in sources:
        names=tuple(port+'.'+source.source_id for port in ('points','mechanicals','readouts'))
        observations['case.'+source.source_id]=tuple(consumed(writer,receipts,tasks,task,name,owner.FINAL_KINDS[port])
            for name,port in zip(names,('points','mechanicals','readouts'),strict=True))
        if reconstruct and is_revision and programme.criterion.is_matched:
            mechanism['case.'+source.source_id]=_replay_matched_revision_case(writer,run_id,programme,source,observations['case.'+source.source_id],tasks,receipts,
                original_input_access=original_input_access,control_custody=custody)
        expected_inputs.update(names)
    scientific=_science_edges(task)
    if len(scientific)!=len(expected_inputs) or {edge.consumer_input_id for edge in scientific}!=expected_inputs:
        raise PermissionError('E5DEV read changes complete actual consumed terminal input census')
    replay=(assess_revision_programme(programme,observations,result_id='result.'+task.task_id,original_allocation=original_allocation)
        if is_revision else opportunity.nominate_selected_opportunity(programme,observations,result_id='nomination.'+programme.original_programme.object_fingerprint))
    kinds=((revision.MatrixRevisionManifest,revision.MatrixRevisionProgrammeAssessment) if is_revision else
        (opportunity.MatrixSelectedOpportunityManifest,original.MatrixPreparationNomination))
    manifest,manifest_custody=product(writer,receipts,task,'manifest',kinds[0])
    result,result_custody=product(writer,receipts,task,'product',kinds[1])
    if (manifest,result)!=replay:raise PermissionError('E5DEV read changes exact complete scientific terminal reduction')
    functional=result.functional if is_revision else result
    retained={'scientific_completion':'COMPLETE_ASSIGNED_E5_DEVELOPMENT_CENSUS' if reconstruct else 'DEFERRED_TO_FULL_READ',
        'decision_consumption':'COMPLETE_RETAINED_E5_NOMINATION','scientific_reconstruction':'FULL' if reconstruct else 'OFF',
        'phase':programme.phase,'programme':programme.identity.to_document(),
        'manifest':manifest.to_document(),'assessment':result.to_document(),
        'nomination_disposition':functional.disposition,'assigned_groups':len(programme.panels),'assigned_cases':len(programme.roster.cases),
        'custody':{'manifest':manifest_custody,'assessment':result_custody},'new_native_contact_count':0,
        'scientific_qualification':'NOT_ESTABLISHED'}
    if not reconstruct:
        return retained
    source_by_case={'case.'+source.source_id:source for _,source in sources}
    native=tuple(native_functional_case(programme.criterion,case,source_by_case[case.case_id],observations[case.case_id][2],
        protocol=programme.protocol(source_by_case[case.case_id]),panels=dict(programme.panels)[case.unit_id]) for case in programme.roster.cases)
    groups=(('opportunity',tuple(group for group,_ in programme.panels)),)
    from .matrix_mechanism_read import prepared_mechanism_projection
    return {**retained,
        **(prepared_mechanism_projection(programme,mechanism) if is_revision else {}),
        'native_functional_diagnostic':{'scope':'NATIVE_ASSAY_ONLY_NO_POINT_OR_ADMISSION_CLAIM',
            'criterion':programme.criterion.to_document(),'cases':tuple(row.to_document() for row in native)},
        'secondary_all_horizon_readout':prepared_secondary_projection(programme,observations,groups),
        'downstream_uncertainty':(
            'EMPIRICALLY_ASSESSED_FROZEN_E4_TRANSPORT_NO_GUARANTEE' if programme.criterion.is_matched else 'NOT_ESTABLISHED'),
        'admission_status':'EMPIRICALLY_REPORTED_FROZEN_POLICIES' if programme.criterion.is_matched else 'UNEVALUABLE',
        'service':'ADMISSION_AND_OBSERVED_SAMPLED_RESPONSE_ADEQUACY' if programme.criterion.is_matched else 'UNESTABLISHED',
        'external_delivered_task':'NOT_SELECTED' if programme.criterion.is_matched else 'UNESTABLISHED'}


def read_development_result(*,directory,artifact_writer,specification,instance,payloads,report,products,draft,plan,allow_partial=False,read_access=None,
        decision_only=False):
    """Ordinary DEV callback; partial reads never enter original or future science."""
    if type(allow_partial) is not bool:raise TypeError('E5DEV read needs an explicit partial selection')
    if type(decision_only) is not bool:raise TypeError('E5DEV decision consumption needs an explicit selection')
    if allow_partial or report.get('status')!='SUCCEEDED' or not decision_only and report.get('typed_product_validation')=='DEFERRED':
        return {'scientific_completion':'NOT_ESTABLISHED','state':'E5_DEVELOPMENT_ASSESSMENT_DEFERRED','new_native_contact_count':0}
    if draft.development_study is None or draft.prospective_draft is not None or instance.draft!=_pin(draft,'draft_id'):
        raise PermissionError('E5DEV read changes actual authored development lifecycle')
    revision_keys=(revision.capability_key('entry','DEVELOPMENT','2.0.0'),)
    entries=tuple(task for task in plan.tasks if task.capability.capability_key in (*revision_keys,original.COMMITTED_DESIGN_KEY))
    if len(entries)!=1:raise PermissionError('E5DEV read needs one exact actual entry/design producer')
    task,=entries;is_revision=task.capability.capability_key in revision_keys
    run_id=report['run_id']
    access=getattr(payloads,'original_input_access',None)
    custody=None
    if access is not None:
        from .selected_prepared_access import validate_development_read_access
        from .current_task_custody import CurrentDevelopmentTaskCustody
        validate_development_read_access(payloads=payloads,read_access=read_access)
        custody=CurrentDevelopmentTaskCustody(writer=artifact_writer,directory=directory,plan=plan,
            payloads=payloads,original_input_access=access,read_access=read_access)
    elif read_access is not None:raise PermissionError('prepared read access lacks its exact original bootstrap')
    with artifact_writer.read_context() as writer:
        kinds=(revision.MatrixRevisionRootConfigV2,) if is_revision else (MatrixSelectedOpportunityRootConfigV2,)
        entry=(_configuration(writer,run_id,task,kinds) if custody is None else _configuration(writer,run_id,task,kinds,custody=custody))
        if entry.phase!=('entry' if is_revision else 'design'):raise PermissionError('E5DEV read changes actual entry phase')
        programme=_selected_programme(specification,instance,payloads,entry,is_revision)
        evidence=(_evidence(writer,run_id,task,entry,is_revision) if custody is None else _evidence(writer,run_id,task,entry,is_revision,custody=custody))
        from empirical_lawhood.api.recursive_operations import operation_catalog
        codecs=operation_catalog()[2]
        original_allocation=(_original_source_operands(writer,entry,evidence,True,codecs,source_scan_bytes=task.capability.requested_resources.source_scan_bytes,**({} if read_access is None else {"current_access":read_access})) if is_revision else None)
        if not is_revision:_authenticate_original_products(writer,programme,evidence,codecs,source_scan_bytes=task.capability.requested_resources.source_scan_bytes,**({} if read_access is None else {"current_access":read_access}))
        result=_science(writer,run_id,programme,task,entry,is_revision,products,plan,original_allocation,
            custody=custody,original_input_access=access,reconstruct=not decision_only)
        writer.require_verification_snapshot()
    if access is not None:access.require_current(artifact_writer=artifact_writer)
    return result
