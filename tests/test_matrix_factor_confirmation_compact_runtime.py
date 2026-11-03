# SPDX-License-Identifier: MPL-2.0
"""Hypothetical compact E1 custody/math controls; no real authority or contact."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import pytest
import numpy as np
from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_records as r,compact_science as science,compact_bindings as owner,compact_preparation as domain
from empirical_lawhood.adapters.methods.matrix_factor_confirmation import science as original_science
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNativeHistory,coordinate_identity
from tests.test_matrix_factor_confirmation_compact_core import compact_case
from tests.test_matrix_factor_confirmation_history import e1 as e1,complete_history
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance,stock as stock
from tests.test_matrix_factor_confirmation_refined import retained
from tests.test_matrix_factor_confirmation_adjudication import prospective


def _no_science(*args,**kwargs):raise AssertionError('metadata entered native science')


def selected_case(e1):
    manifest,sources=compact_case(e1)
    prior,_=prospective(e1)
    root=prior.prospective_draft
    proof=tuple(sorted((obligation,operation.node_id.replace('matrix-factor-confirmation.','matrix-factor-confirmation-compact.',1)) for operation in prior.operations for obligation in operation.obligation_ids))
    nodes=tuple(sorted((owner.COMMIT_KEY,owner.KEY,*(r.NAMESPACE+'.'+source.root_id+'.'+phase for source in sources for phase in r.PHASES))))
    budget=ResourceBudget(1,1024**3,0,None,64*1024**2,64*1024**2)
    selected=domain.E1CompactExperimentSelection('selection.disclosed.compact-e1',root,manifest,proof,tuple((node,budget) for node in nodes),(),(),(),None,None,(),None)
    spec=domain.E1CompactExperimentSpecification('experiment.disclosed.compact-e1',root.question,tuple(source.root_id for source in sources),selected.identity)
    return spec,selected,sources


def test_actual_compact_public_preparation_reports_real_qualification_entry_and_resource_holds(e1,monkeypatch):
    spec,selected,sources=selected_case(e1)
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
    monkeypatch.setattr(parameter_source,'acquire_parameter_history',_no_science)
    monkeypatch.setattr(science,'measure',_no_science)
    inputs=domain.bind_inputs(spec,{'selection':selected})
    prepared=domain.prepare(spec,method_inputs=inputs.method_inputs,execution=ExecutionSelection(4,'environment.disclosed-e1',sources[0].provenance,str(Path(e1[0].root.contract.canonical_path))))
    assert not prepared.executable and prepared.prospective_spec is None and prepared.draft is not None
    assert len(prepared.draft.operations)==4*len(sources)+2
    assert prepared.census.native_effect_count==len(sources)
    assert {'e1.entry','e1.formal-methods','e1.formal-sources','e1.qualifications','e1.source-configs','e1.resources'}<={row.code for row in prepared.dependencies}
    for operation in prepared.draft.operations:
        if operation.node_id not in (owner.COMMIT_KEY,owner.KEY):
            assert len(operation.config_payload.encode())<64*1024
            assert '"package_sources"' not in operation.config_payload and '"exposure"' not in operation.config_payload
    manifest_externals=tuple(row for row in prepared.draft.external_inputs if row.payload_schema==r.E1CompactManifest.SCHEMA)
    assert len(manifest_externals)==1


def _compact_history(e1,source):
    from tests.native_completion_fixtures import publish_completion
    plane,old_sources,_=e1
    original_source=next(value for value in old_sources if value.root_id==source.root_id)
    prior,numerical,arrays,raw=complete_history(plane,original_source)
    retained_raw,operand=science.array_product(source,arrays,artifact_id='native.compact.arrays.'+source.root_id)
    assert retained_raw==raw
    task=r.NAMESPACE+'.'+source.root_id+'.history'
    parent=replace(prior.native.definition.parent_contact,task_id=task,attempt_id='attempt.'+task,
        execution_task=replace(prior.native.definition.parent_contact.execution_task,object_id=task))
    config=r.E1CompactOperationConfig('config.'+parent.task_id,'history',source)
    definition=replace(prior.native.definition,operation_id='matrix-e1-compact.full-paired-history',parent_contact=parent,configuration=r.identity(config),
        sources=tuple(sorted((r.identity(source),source.manifest,coordinate_identity(source.coordinate),source.provenance),key=lambda value:value.object_id)))
    native_task='native-subwork.'+sha256((parent.task_id+':'+definition.subwork_id).encode()).hexdigest()
    published=retained(plane,native_task+'.output.arrays',operand.array_artifact.payload_schema,raw,OutcomeAccess.EVALUATION_SEALED)
    attempt=parent.run_id+'.'+native_task+'.attempt-001'
    receipt=CanonicalTaskReceipt('receipt.'+attempt,parent.run_id,native_task,attempt,parent.implementation_commit,parent.input_materialization_ids,
        (published.materialization,),(published.logical,),(),OperationalStatus.SUCCEEDED,())
    completion=replace(prior.native.completion,definition=definition.identity)
    receipt=publish_completion(plane,receipt,completion,visibility=published.logical.visibility_ceiling,
        access=OutcomeAccess.EVALUATION_SEALED)
    native=MatrixParameterNativeHistory(definition,completion,receipt)
    history=r.E1CompactNativeHistory('history.'+source.root_id,r.identity(source),coordinate_identity(source.coordinate),source.root_id,source.root.root.independent_group_id,source.coordinate.clock_id,operand,native,source.coordinate.total_ticks,2*source.coordinate.total_ticks)
    assessed=science.assess_history(source,history,arrays)
    assert assessed.controls==numerical.controls
    return history,assessed,arrays,raw,prior,numerical


def test_native_direct_operand_revision_preserves_exact_legacy_history_and_rejects_crossed_rosters(e1):
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from tests.native_completion_fixtures import publish_completion
    _,sources=compact_case(e1);source=sources[0]
    history,_,_,_,_,_=_compact_history(e1,source)
    original=history.canonical_bytes()
    history.validate_source(source)
    assert decode_canonical_bytes(original,type(history),maximum_bytes=None).canonical_bytes()==original
    definition=replace(history.native.definition,operation_id=r.NATIVE_HISTORY_OPERATION,
        sources=r.native_history_sources(source,r.NATIVE_HISTORY_OPERATION))
    completion=replace(history.native.completion,definition=definition.identity)
    receipt=publish_completion(e1[0],history.native.receipt,completion,
        visibility=VisibilityCeiling.PROSPECTIVE,access=OutcomeAccess.EVALUATION_SEALED)
    revised=replace(history,native=replace(history.native,definition=definition,completion=completion,receipt=receipt))
    revised.validate_source(source)
    assert source.manifest not in revised.native.definition.sources
    assert history.canonical_bytes()==original
    for operation,sources in ((r.NATIVE_HISTORY_OPERATION,history.native.definition.sources),
            (r.NATIVE_HISTORY_OPERATION_V1,definition.sources)):
        changed=replace(definition,operation_id=operation,sources=sources)
        completion=replace(history.native.completion,definition=changed.identity)
        receipt=publish_completion(e1[0],history.native.receipt,completion,
            visibility=VisibilityCeiling.PROSPECTIVE,access=OutcomeAccess.EVALUATION_SEALED)
        crossed=replace(history,native=replace(history.native,definition=changed,completion=completion,receipt=receipt))
        with pytest.raises(ValueError,match='native source/stream/provenance'):
            crossed.validate_source(source)


@pytest.mark.parametrize('family',range(4))
def test_actual_measurement_bytes_preserved_with_time_zero_risk_and_independent_cold_checks(e1,monkeypatch,family):
    manifest,sources=compact_case(e1,trailing=2);source=sources[family]
    history,numerical,arrays,raw,original,original_numerical=_compact_history(e1,source)
    original_raw,original_product=original_science.measure(e1[1][family],original,original_numerical,arrays,artifact_id='diagnostic.original.disclosed')
    diagnostic,product=science.measure(source,history,numerical,arrays,artifact_id='diagnostic.compact.disclosed')
    assert diagnostic==original_raw
    # Raw spectra/algebra and exact NPZ bytes are shared; the current population
    # includes preparation time and therefore has a different risk interval.
    for current, previous in zip(product.traces, original_product.traces, strict=True):
        assert tuple(replace(row, origin_angle_degrees=None, causal_admitted=row.raw_admitted) for row in current.observations)==tuple(
            replace(row, origin_angle_degrees=None, causal_admitted=row.raw_admitted) for row in previous.observations)
        if current.observations[0].raw_admitted is None:
            assert current.moving_lifetime.unavailable_ticks[0]==0
            assert previous.moving_lifetime.unavailable_ticks[0]>=4
        elif current.observations[0].raw_admitted is True:
            assert current.observations[0].causal_admitted is True
            assert current.moving_lifetime.origin_tick==0
    old_assessment=original_science.assess_factor(e1[1][family],original,original_numerical,original_product,raw,original_raw)
    monkeypatch.setattr(np.linalg,'eigh',_no_science);monkeypatch.setattr(np.linalg,'eigvalsh',_no_science)
    assessment=science.assess_factor(source,history,numerical,product,raw,diagnostic)
    assert assessment.controls==old_assessment.controls
    from empirical_lawhood.adapters.methods.matrix_parameter_factor import independent
    from tests.test_matrix_independent_gram import literal_operator
    with monkeypatch.context() as literal:
        literal.setattr(independent,'raw_operator',literal_operator)
        assert science.assess_factor(source,history,numerical,product,raw,diagnostic).canonical_bytes()==assessment.canonical_bytes()
    plane=e1[0];receipts=[]
    for phase,record,array_bytes in (('history',history,raw),('numerical',numerical,None),('measure',product,diagnostic),('check',assessment,None)):
        outputs=[retained(plane,'ordinary.compact.'+phase+'.'+source.root_id,record.SCHEMA,record.canonical_bytes(),OutcomeAccess.EVALUATION_SEALED)]
        if array_bytes is not None:outputs.append(retained(plane,record.arrays.array_artifact.artifact_id,record.arrays.array_artifact.payload_schema,array_bytes,OutcomeAccess.EVALUATION_SEALED))
        outputs.sort(key=lambda row:row.logical.logical_artifact_id)
        parent=history.native.definition.parent_contact;task=r.NAMESPACE+'.'+source.root_id+'.'+phase
        receipts.append(CanonicalTaskReceipt('receipt.compact.'+phase,parent.run_id,task,parent.attempt_id if phase=='history' else 'attempt.'+task,
            source.implementation_commit,parent.input_materialization_ids if phase=='history' else (),tuple(row.materialization for row in outputs),tuple(row.logical for row in outputs),(),OperationalStatus.SUCCEEDED,()))
    from empirical_lawhood.infrastructure import matrix_array_io
    decoded=[]
    decode=matrix_array_io._decode_matrix_arrays
    def counted(*args):
        decoded.append(args[1].array_artifact.artifact_id)
        return decode(*args)
    monkeypatch.setattr(matrix_array_io,'_decode_matrix_arrays',counted)
    with matrix_array_io.decoded_matrix_array_scope():
        assert science.read_retained(source,history,numerical,product,assessment,raw,diagnostic,receipts=tuple(receipts))==(product,assessment)
    assert decoded==[history.arrays.array_artifact.artifact_id,product.arrays.array_artifact.artifact_id]
    if family==0:
        from types import SimpleNamespace
        from empirical_lawhood.api.matrix_retained_replay import replay_e1, replay_weight, map_reconstructions
        from empirical_lawhood.infrastructure.parallel_verification import CanonicalValidationPool
        value=(source,history,numerical,product,assessment,raw,diagnostic,tuple(receipts))
        weight=replay_weight(records=(source,history,numerical,product,assessment,*receipts),
            archives=((raw,history.arrays),(diagnostic,product.arrays)))
        pool=CanonicalValidationPool(2)
        try:
            writer=SimpleNamespace(_read_verification=SimpleNamespace(canonical_pool=pool))
            assert map_reconstructions(writer,replay_e1,((weight,value),(weight,value)))==(source.root_id,)*2
            bad=(*value[:6],diagnostic+b'changed',value[7])
            with pytest.raises(ValueError):map_reconstructions(writer,replay_e1,((weight,bad),))
        finally:pool.close()
    with pytest.raises(ValueError,match='original operation|producing implementation'):
        science.read_retained(source,history,numerical,product,assessment,raw,diagnostic,receipts=(replace(receipts[0],task_id='foreign.task'),*receipts[1:]))


def test_public_partial_and_missing_reveal_cannot_open_original_selection_or_scientific_products(e1,monkeypatch):
    from contextlib import contextmanager
    from types import SimpleNamespace
    from empirical_lawhood.api import matrix_factor_confirmation_compact_read as read
    spec,selection,_=selected_case(e1)
    candidate=ObjectIdentity('candidate.disclosed.compact-e1','empirical-lawhood/testing/candidate','1.0.0','a'*64)
    class Payloads:
        def __getitem__(self,name):
            if name=='experiment-specification.json':return spec.canonical_bytes()
            raise AssertionError('partial/missing-authority read opened canonical scientific source')
    class Writer:
        @contextmanager
        def read_context(self):yield self
    plan=SimpleNamespace(tasks=(SimpleNamespace(task_id='task.disclosed.compact-e1'),))
    package=SimpleNamespace(issued_study=SimpleNamespace(candidate=object(),source_closure='original.source'),run_plan_id='run.disclosed.compact-e1')
    monkeypatch.setattr(read,'_pin',lambda record,field:candidate)
    monkeypatch.setattr(read,'_actual_package',lambda *args,**kwargs:package)
    monkeypatch.setattr(read,'CurrentResultPlanReader',lambda *args,**kwargs:SimpleNamespace(authenticate_execution_plan=lambda **kwargs:plan))
    monkeypatch.setattr(read,'original_selection',_no_science)
    selected=SimpleNamespace(payloads=Payloads(),instance=SimpleNamespace(specification=spec.identity),association=SimpleNamespace(candidate=candidate),implementation='original.source',projection=plan)
    result=read.read_result(selected=selected,artifact_writer=Writer(),run_id=package.run_plan_id,allow_partial=True)
    assert result['scientific_completion']=='NOT_ESTABLISHED' and result['denominators']['confirmation']['assessed_units'] is None
    with pytest.raises(PermissionError,match='current reveal authority'):
        read.read_result(selected=selected,artifact_writer=Writer(),run_id=package.run_plan_id)
