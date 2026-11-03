# SPDX-License-Identifier: MPL-2.0
"""Actual DEV metadata receipt/read controls with disclosed literal Matrix cells.

The parent-product I/O seam supplies no scientific qualification or authority.
No native task executes. Current original-parent refusal and partial ordering
are separately exercised before any received scientific value is projected.
"""
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_selected_development_scientific_read as reader
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as declarative
from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile,ArtifactWriteRequest,CanonicalTaskReceipt
from empirical_lawhood.runtime.prospective_experiment import source_filename
from tests.test_matrix_selected_protected import transfer  # noqa: F401
from tests.test_matrix_selected_opportunity import opportunity,literal_observations  # noqa: F401
from tests.test_matrix_selected_declarative_preparation import science, request as selected_request, selection
from tests.test_recursive_public_service import _plane
from tests.selected_reader_configuration_support import freeze_reader_terminal


@pytest.fixture(params=(True,False))
def actual_context(opportunity,tmp_path,monkeypatch,request):  # noqa: F811
    specification=science(opportunity)
    selected=selection(specification,selected_request(opportunity),opportunity)
    programme,evidence=selected.programme,selected.evidence
    values=literal_observations(programme,hold_error=D('.9') if request.param else D('.01'),fixed_error=D('.01') if request.param else D('.9'))
    draft=declarative.lower(specification,selected).draft
    budgets=dict(selected.request.phase_resources.phase_budgets)
    plane=_plane(tmp_path/'custody');receipts={};tasks={};publications={};configs={}
    run='run.disclosed.secondary-development'

    def publish(task_id,outputs,*,phase):
        specs=[]
        writes=[]
        for name,value in sorted(outputs):
            publication=plane.write(ArtifactWriteRequest('artifact.'+task_id+'.'+name,
                'selected-development/'+sha256((task_id+'.'+name).encode()).hexdigest()+'.json',value.SCHEMA,
                ArtifactProfile.CANONICAL_JSON,'application/json','publication.'+task_id+'.'+name,'selected-development',value.canonical_bytes(),
                VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
            publications[task_id,name]=publication
            writes.append(publication)
            specs.append(SimpleNamespace(output_id=task_id+'.'+name,logical_artifact_id=publication.logical.logical_artifact_id,payload_schema=value.SCHEMA))
        receipts[task_id]=CanonicalTaskReceipt('receipt.'+task_id,run,task_id,'attempt.'+task_id,'c'*40,(),
            tuple(row.materialization for row in writes),tuple(sorted((row.logical for row in writes),key=lambda row:row.logical_artifact_id)),(),OperationalStatus.SUCCEEDED,())
        task=SimpleNamespace(task_id=task_id,outputs=tuple(specs),
            capability=SimpleNamespace(capability_key=reader.original.COMMITTED_DESIGN_KEY if phase=='design' else reader.original.NAMESPACE+'.'+phase,
                requested_resources=budgets[phase]))
        tasks[task_id]=task
        return task

    entry_id=reader.original.global_node(programme,'design')
    entry=reader.original.MatrixSelectedOpportunityRootConfigV2('config.'+entry_id,programme,'design',evidence.identity,
        len(evidence.canonical_bytes()),selected.request.produced_input_parents)
    entry_task=publish(entry_id,(('product',reader.opportunity.opportunity_seal(programme)),),phase='design')
    configs[entry_id]=entry
    edges=[]
    def consume(name,task,output='product'):
        spec,=tuple(row for row in task.outputs if row.output_id==task.task_id+'.'+output)
        edges.append(SimpleNamespace(consumer_input_id=name,producer_task_id=task.task_id,producer_output_id=spec.output_id,operational_logical_artifact_id=spec.logical_artifact_id))
    consume('design',entry_task)
    for case_id,row in values.items():
        source_id=case_id.removeprefix('case.')
        for port,value in zip(('points','mechanicals','readouts'),row,strict=True):
            task=publish('task.disclosed.'+port+'.'+source_id,(('product',value),),
                phase={'points':'point','mechanicals':'mechanical','readouts':'response-score'}[port])
            consume(port+'.'+source_id,task)
    final_id=reader.original.global_node(programme,'nominate')
    replay=reader.opportunity.nominate_selected_opportunity(programme,values,result_id='nomination.'+programme.original_programme.object_fingerprint)
    final=publish(final_id,(('manifest',replay[0]),('product',replay[1])),phase='nominate')
    final.scientific_inputs=tuple(edges)
    configs[final_id]=reader.original.MatrixSelectedOpportunityRootConfig('config.'+final_id,programme,'nominate')
    declaration,=(value for value in reader.original.operation_declarations()
        if value.capability_key==reader.original.capability_key('nominate'))
    final=freeze_reader_terminal(plane=plane,task=final,config=configs[final_id],
        declaration=declaration,receipts=receipts,resources=budgets['nominate'])
    tasks[final_id]=final
    plan=SimpleNamespace(tasks=tuple(tasks.values()))
    instance=SimpleNamespace(specification=specification.identity,allocation=declarative.allocation(programme).identity,
        draft=ObjectIdentity.from_record(draft.draft_id,draft),sources=(selected.identity,))
    monkeypatch.setattr(reader,'_configuration',lambda writer,run,task,kinds:configs[task.task_id])
    monkeypatch.setattr(reader,'_evidence',lambda *args:evidence)
    calls=[]
    def authenticate_originals(writer,actual_programme,actual_evidence,codecs,*,source_scan_bytes):
        assert actual_programme==programme and actual_evidence==evidence
        assert type(source_scan_bytes) is int and source_scan_bytes==budgets['design'].source_scan_bytes
        assert actual_evidence.original_commitments == selected.request.original_commitments
        calls.append({'source_scan_bytes':source_scan_bytes})
    monkeypatch.setattr(reader,'_authenticate_original_products',authenticate_originals)
    kwargs=dict(directory=None,artifact_writer=plane,specification=specification,instance=instance,
        payloads={source_filename(selected.identity):selected.canonical_bytes()},
        report={'status':'SUCCEEDED','run_id':run},products={'receipts':receipts},draft=draft,plan=plan)
    return SimpleNamespace(kwargs=kwargs,programme=programme,values=values,replay=replay,final=final,plane=plane,
        receipts=receipts,publications=publications,calls=calls,useful=request.param,
        source_scan_bytes=budgets['design'].source_scan_bytes)


def test_current_dev_read_exposes_all_three_arms_and_adverse_nomination(actual_context):
    f=actual_context
    result=reader.read_development_result(**f.kwargs)
    assert result['manifest']==f.replay[0].to_document() and result['assessment']==f.replay[1].to_document()
    assert (result['nomination_disposition']=='NOMINATED') is f.useful
    assert result['assigned_cases']==3*result['assigned_groups']
    secondary=result['secondary_all_horizon_readout']
    assert len(secondary['adequacy'])==result['assigned_cases']*30
    assert len(secondary['counts'])==3
    assert sum(row['assigned_cases'] for row in secondary['counts'])==result['assigned_cases']
    assert len(result['native_functional_diagnostic']['cases'])==result['assigned_cases']
    assert result['scientific_qualification']=='NOT_ESTABLISHED' and result['new_native_contact_count']==0
    assert f.calls==[{'source_scan_bytes':f.source_scan_bytes}]


@pytest.mark.parametrize('mode', ('off', 'full'))
def test_programme_decision_consumption_preserves_nomination_without_optional_reports(actual_context, monkeypatch, mode):
    from empirical_lawhood.api import matrix_programme_decisions as decisions, recursive_execution, experiment_scientific_read
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
    f = actual_context
    calls = []
    def retained(**options):
        calls.append(options['terminal_product_format'])
        result = options['_scientific_consumer'](**{
            key: value for key, value in f.kwargs.items() if key not in ('specification', 'instance')})
        return ({'scientific_result':result}, None, f.kwargs['draft'], f.kwargs['plan']), None
    monkeypatch.setattr(recursive_execution, '_read_recursive_wave_with_retained_roots', retained)
    monkeypatch.setattr(experiment_scientific_read, '_development_runtime_context',
        lambda **_: (None, f.kwargs['specification'], f.kwargs['instance']))
    context = SimpleNamespace(writer=f.plane, child_directory=lambda phase: None,
        report=lambda phase: {'read_scope':'EXECUTION_RECORDS'},
        binding=lambda phase: SimpleNamespace(specification=SimpleNamespace(identity=f.kwargs['specification'].identity)))
    if mode == 'off':
        def forbidden(*args, **kwargs):
            pytest.fail('required nomination entered an optional numerical or exhaustive report')
        for name in ('native_functional_case', 'prepared_secondary_projection', '_replay_matched_revision_case'):
            monkeypatch.setattr(reader, name, forbidden)
        f.kwargs['report']['typed_product_validation'] = 'DEFERRED'
    with scientific_reconstruction_operation(mode):
        result = decisions.development_assessment(context)
    assert result['assessment'] == f.replay[1].to_document()
    assert result['assigned_cases'] == len(f.programme.roster.cases)
    assert result['assigned_groups'] == len(f.programme.panels)
    assert (result['nomination_disposition'] == 'NOMINATED') is f.useful
    assert result['decision_consumption'] == 'COMPLETE_RETAINED_E5_NOMINATION'
    assert ('secondary_all_horizon_readout' in result) == (mode == 'full')
    assert calls == ['compact' if mode == 'off' else 'documents']


@pytest.mark.parametrize('compact',(False,True))
def test_partial_dev_read_defers_before_original_and_scientific_payload(actual_context,monkeypatch,compact):
    def forbidden(*args,**kwargs):pytest.fail('partial DEV reader entered original or future scientific bytes')
    monkeypatch.setattr(reader,'_configuration',forbidden)
    monkeypatch.setattr(reader,'_authenticate_original_products',forbidden)
    if compact:actual_context.kwargs['report']['typed_product_validation']='DEFERRED'
    result=reader.read_development_result(**actual_context.kwargs,allow_partial=not compact)
    assert result['scientific_completion']=='NOT_ESTABLISHED' and actual_context.calls==[]


def test_original_parent_refusal_precedes_any_terminal_science(actual_context,monkeypatch):
    def refused(*args,**kwargs):raise PermissionError('DISCLOSED_CURRENT_ORIGINAL_REVEAL_REVOKED')
    monkeypatch.setattr(reader,'_authenticate_original_products',refused)
    monkeypatch.setattr(reader,'_science',lambda *args:pytest.fail('invalid parent reached terminal scientific bytes'))
    with pytest.raises(PermissionError,match='REVEAL_REVOKED'):
        reader.read_development_result(**actual_context.kwargs)


@pytest.mark.parametrize('damage',('missing-receipt','consumed-producer','consumed-logical','changed-output'))
def test_terminal_read_requires_actual_complete_consumed_custody(actual_context,damage):
    f=actual_context
    if damage=='missing-receipt':f.receipts.pop(next(iter(f.receipts)))
    elif damage in ('consumed-producer','consumed-logical'):
        edge=next(row for row in f.final.scientific_inputs if row.consumer_input_id.startswith('points.'))
        changed=(replace(edge,producer_task_id='task.foreign') if damage=='consumed-producer'
            else replace(edge,operational_logical_artifact_id='artifact.foreign'))
        edges=tuple(changed if row is edge else row for row in f.final.scientific_inputs)
        f.final=replace(f.final,scientific_inputs=edges,
            dependency_task_ids=tuple(sorted({row.producer_task_id for row in edges if row.producer_task_id is not None})))
        f.kwargs['plan'].tasks=tuple(f.final if row.task_id==f.final.task_id else row for row in f.kwargs['plan'].tasks)
    else:
        publication=f.publications[f.final.task_id,'product']
        f.plane.root.resolve(publication.materialization.relative_path,for_write=False).write_bytes(b'changed')
    with pytest.raises((ValueError,PermissionError,RuntimeError)):
        reader.read_development_result(**f.kwargs)


def test_current_public_dev_route_registers_its_lazy_scientific_reader():
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative_development.experiment_binding import EXPERIMENT_RUNTIME_BINDING as binding
    binding.__post_init__()
    assert binding.specification_schema is not None and callable(binding.read_development_result)


def test_development_science_bounds_whole_census_guards(actual_context,record_property):
    """Many retained products must not rescan the growing census per member."""
    import sys
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
    f=actual_context
    guards=[]
    code=ExternalArtifactPlane._require_verification_snapshot_paths.__code__
    previous=sys.getprofile()
    def observe(frame,event,_argument):
        if event=='call' and frame.f_code is code:guards.append(len(frame.f_locals['snapshots']))
    sys.setprofile(observe)
    try:result=reader.read_development_result(**f.kwargs)
    finally:sys.setprofile(previous)
    assert result['assessment']==f.replay[1].to_document()
    record_property('published_products',len(f.publications))
    record_property('whole_census_guards',len(guards))
    assert len(f.publications)>10 and max(guards)>20
    assert len(guards)<=8,guards


def test_development_science_rechecks_final_bytes_and_expires_its_scope(actual_context,monkeypatch):
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
    f=actual_context
    publication=f.publications[f.final.task_id,'product']
    path=f.plane.root.resolve(publication.materialization.relative_path,for_write=False)
    raw=path.read_bytes()
    science=reader._science
    observed=[]
    def changed(writer,*args,**kwargs):
        result=science(writer,*args,**kwargs)
        observed.append(writer)
        path.write_bytes(b'X'+raw[1:])
        return result
    monkeypatch.setattr(reader,'_science',changed)
    try:
        with pytest.raises(ArtifactIdentityConflict):reader.read_development_result(**f.kwargs)
    finally:path.write_bytes(raw)
    assert len(observed)==1
    with pytest.raises(ArtifactIdentityConflict,match='scope has ended'):
        observed[0].require_verification_context()
