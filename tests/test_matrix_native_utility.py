# SPDX-License-Identifier: MPL-2.0
"""Disclosed E2 software controls: no freshness/qualification from test records.

Actual native control reuses already exposed test streams and ordinary source,
array, process, native-contact and receipt owners. Its synthetic exposure corpus
is not scientific authority. E2 has its own specification, seal and products.
"""
from dataclasses import fields,replace
from decimal import Decimal as D, localcontext
from pathlib import Path
from types import SimpleNamespace
import shutil

import pytest
from threadpoolctl import threadpool_limits
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_science as science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseLossCell
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support
from empirical_lawhood.api.experiment_preparation import author_prepared_experiment,load_experiment_inputs,load_experiment_specification,prepare_experiment
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.api.recursive_execution import read_recursive_wave,run_recursive_wave
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding,ExperimentFileInputSelection,ExperimentInputBinding
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case

ROOT=Path(__file__).parents[1]


def utility_case(tmp_path,*,original=None,root_count=1,amended=False):
    # Reuse only the disclosed generic source/reservation/template fixtures.
    # The old E3 candidate/TRAIN/future controls are not E2 request operands.
    old=fresh_training_metadata_case(tmp_path,training_count=root_count) if original is None else original
    prior=old.request.train_manifest
    manifest=r.NativeUtilitySourceManifest(**{value.name:getattr(prior,value.name) for value in fields(r.NativeUtilitySourceManifest)} )
    manifest=replace(manifest,record_id="manifest.disclosed-native-e2")
    criterion=r.NativeUtilityCriterion("criterion.disclosed-native-e2",old.request.mathematical_protocol.horizon_steps[-1],
        ("FULL_COUPLED","GENERIC_SLOW","NORM_RADIUS","SPECTRA"),D("0.0002"),D("0.0001"),1,2,1,20,1)
    specification=r.NativeUtilitySpecification("experiment.disclosed-native-e2",old.specification.root_ids,
        old.request.mathematical_protocol.identity,criterion)
    resources=r.NativeUtilityResources("resources.disclosed-native-e2",tuple((phase,old.request.resources.for_operation(phase)) for phase in r.ALL_PHASES),4)
    record_id="request.disclosed-native-e2"
    campaign=replace(old.request.campaign,objective=owner.QUESTION,system_ids=(record_id,),world_ids=(owner.WORLD,),
        target_claim_ids=("claim.study."+specification.specification_id,),budget=ResourceBudget.aggregate(tuple(resources.for_operation(phase)
            for phase in (*r.PHASES*len(specification.root_ids),"entry","terminal"))))
    # E2 consumes the exact current census, without TRAIN's future/C supports.
    # Retain actual FILE handles selected by independent physical-custody tests.
    supplied_support = dict(old.request.exposure_support)
    support = tuple((artifact, supplied_support[artifact]) for artifact, _ in exposure_support(manifest.audit))
    request=r.NativeUtilityRequest(record_id,manifest,old.request.sources,old.request.protocols,old.request.panels,
        old.request.mathematical_protocol,old.request.template_publications,support,campaign,resources)
    if amended:
        from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixIO48Construction, MatrixOriginResponseModel
        from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
        mathematical = replace(request.mathematical_protocol, protocol_id='mathematical.disclosed-amended-e2',
            horizon_steps=DENSE_RESPONSE_HORIZONS)
        protocols = tuple(replace(protocol, criterion=mathematical.identity, horizon_steps=DENSE_RESPONSE_HORIZONS,
            mechanical_model=MatrixOriginResponseModel('model.disclosed-amended-e2', protocol.mechanical_model.implementation,
                MatrixIO48Construction('io48.disclosed-amended-e2'))) for protocol in request.protocols)
        specification = replace(specification, mathematical_protocol=mathematical.identity,
            criterion=r.NativeAmendedUtilityCriterion('criterion.disclosed-amended-e2'))
        request = replace(request, mathematical_protocol=mathematical, protocols=protocols)
    r.validate_request(specification,request)
    return SimpleNamespace(plane=old.plane,source=old.source,sources=old.sources,specification=specification,request=request,
        template_files=old.template_files,acquisition=r.acquisition_seal(specification,request))


@pytest.mark.parametrize("count",(1,3))
@pytest.mark.parametrize("amended", (False, True))
def test_actual_declarative_native_e2_lowering_preserves_two_populations_and_pre_future_boundary(tmp_path,monkeypatch,count,amended):
    case=utility_case(tmp_path,root_count=count,amended=amended)
    monkeypatch.setattr(bindings,"execute_parameter_native_work",lambda *a,**kw:pytest.fail("preparation entered native E2 prefix"))
    monkeypatch.setattr(bindings,"execute_paired_response_native_work",lambda *a,**kw:pytest.fail("preparation entered native E2 response"))
    bound=owner.bind_inputs(case.specification,{"request":case.request},files=case.template_files)
    prepared=owner.prepare(case.specification,method_inputs=bound.method_inputs,
        execution=ExecutionSelection(4,"environment.disclosed-native-e2",case.source.provenance.identity,str(tmp_path)))
    assert prepared.executable and prepared.census.native_effect_count==2*count
    assert dict(prepared.census.role_counts)=={"native-utility":count}
    assert dict(prepared.census.output_counts)["selected-tasks"]==8*count+2
    declarations=bindings.operation_declarations()
    registry=CapabilityRegistry("registry.disclosed-native-e2",tuple(sorted((value.manifest() for value in declarations),key=lambda value:value.registry_id)))
    compiled=compile_recursive_wave(draft=prepared.draft,registrations=tuple(value.registration() for value in declarations),registry=registry,
        implementation_commit=case.source.provenance.observed_git_head,output_codecs={key:value for declaration in declarations for key,value in declaration.record_codecs.items()})
    assert len(compiled.execution_plan.tasks)==8*count+2
    configs=dict(owner.contracts(case.specification,case.request)[0])
    for root in case.specification.root_ids:
        physical=configs[owner.task_id(root,"physical-forecast")]
        assert physical.source is None and physical.panels==() and physical.public_source is not None
        assert not any(edge.consumer_node_id==owner.task_id(root,"physical-forecast") and edge.consumer_input_id.startswith("streams") for edge in prepared.draft.links)
    assert not any("train" in value.name or "candidate" in value.name or "future_reservation" in value.name for value in fields(r.NativeUtilitySpecification))
    for value in (case.specification,case.request,case.acquisition):assert decode_canonical_bytes(value.canonical_bytes(),type(value),maximum_bytes=None)==value


def test_native_e2_holds_absent_scientific_choices_before_lowering_or_contact(tmp_path,monkeypatch):
    case=utility_case(tmp_path)
    specification=replace(case.specification,criterion=None)
    bound=owner.bind_inputs(specification,{"request":case.request},files=case.template_files)
    monkeypatch.setattr(owner,"lower",lambda *a,**kw:pytest.fail("missing E2 criterion compiled executable work"))
    result=owner.prepare(specification,method_inputs=bound.method_inputs,execution=ExecutionSelection(4))
    assert not result.executable and result.draft is None
    assert "native-utility.criterion" in {value.code for value in result.dependencies}
    with pytest.raises(ValueError,match="before.*criterion|criterion.*before|scientific utility criterion"):
        r.acquisition_seal(specification,case.request)
    with pytest.raises(ValueError,match="comparison|capacity|criterion"):
        replace(case.specification.criterion,comparators=("GENERIC_SLOW",))
    with pytest.raises(TypeError,match="own exact"):
        foreign = tmp_path / "foreign"
        foreign.mkdir()
        r.validate_request(case.specification,fresh_training_metadata_case(foreign).request)


def _unresolved_score(case):
    protocol=case.request.protocols[0];panels=r.panels_for(case.request,case.source)
    cells=tuple(sorted((ScheduledResponseLossCell(view,panel.panel_id,action.action_id,predictor,horizon,None,None,None,None,None)
        for view in ("PRIMARY","FINE") for panel in panels for action in protocol.actions for predictor in r.PREDICTORS
        for horizon in protocol.horizon_steps),key=lambda value:value.key))
    pin=lambda name:ObjectIdentity(name,"empirical-lawhood/matrix-factor-response/native-utility-"+name,"1.0.0","a"*64)
    return r.NativeUtilityScore("score.disclosed-e2",protocol.public_source.source,pin("causal-prefix"),case.acquisition.identity,
        pin("response-forecast"),pin("native-responses"),case.source.root_id,protocol.public_source.root.independent_group_id,
        "DEVELOPMENT",protocol.criterion,(),False,"NO_ORIGIN",cells,(None,)*15,("actual-no-origin",))


def test_native_e2_complete_nonuse_adverse_counts_and_foreign_seals_stay_explicit(tmp_path,monkeypatch):
    case=utility_case(tmp_path);protocol=case.request.protocols[0];panels=r.panels_for(case.request,case.source)
    score=_unresolved_score(case)
    monkeypatch.setattr(bindings,"execute_parameter_native_work",lambda *a,**kw:pytest.fail("pure assessment acquired prefix"))
    monkeypatch.setattr(bindings,"execute_paired_response_native_work",lambda *a,**kw:pytest.fail("pure assessment acquired futures"))
    outcome=science.assess_score(case.specification,protocol,panels,case.acquisition,score)
    assert not outcome.usable and not outcome.success and outcome.numerical_disposition=="UNEVALUABLE"
    assert len(outcome.losses)==30 and all(value is None for *_,value in outcome.losses)
    summary=science.summarize(case.specification,case.acquisition,(outcome,))
    assert (summary.assigned_units,summary.usable_units,summary.successes)==(1,0,0)
    assert (summary.scientific_status,summary.qualification,summary.sampling_warrant)==("UNEVALUABLE","NOT_ESTABLISHED","NOT_ESTABLISHED")
    assert not summary.conditional_criterion_met and summary.tail_numerator==summary.tail_denominator==1
    with pytest.raises(ValueError,match="denominator"):
        science.assess_score(case.specification,protocol,panels,case.acquisition,replace(score,cells=score.cells[:-1]))
    with pytest.raises(ValueError,match="root/group|freeze|frozen"):
        science.assess_score(case.specification,protocol,panels,replace(case.acquisition,request=replace(case.acquisition.request,object_fingerprint="b"*64)),score)
    with pytest.raises(ValueError,match="omits|duplicates"):
        science.summarize(case.specification,case.acquisition,())
    with pytest.raises(ValueError,match="omits|substitutes"):
        science.summarize(case.specification,case.acquisition,(replace(outcome,unit_id="unit.foreign"),))


def copied_preparation(case,directory):
    directory.mkdir();specification_path=directory/"specification.json";request_path=directory/"request.json"
    specification_path.write_bytes(case.specification.canonical_bytes());request_path.write_bytes(case.request.canonical_bytes())
    files=[]
    for index,(key,value) in enumerate(sorted(case.template_files.items())):
        target=directory/("template-"+str(index)+".npz");shutil.copyfile(value.path,target)
        files.append(ExperimentFileInputBinding(key,value.identity,value.record_version,target.name,value.maximum_bytes))
    selection=ExperimentFileInputSelection("sources.disclosed-native-e2",owner.PROTOCOL_ID,
        (ExperimentInputBinding("request",case.request.identity,request_path.name,request_path.stat().st_size),),tuple(files))
    selection_path=directory/"sources.json";selection_path.write_bytes(selection.canonical_bytes())
    specification=load_experiment_specification(specification_path);inputs=load_experiment_inputs(specification,selection_path)
    execution=ExecutionSelection(4,"environment.disclosed-native-e2",ObjectIdentity.from_record("recursive-member.implementation",implementation_binding(ROOT)),case.plane.root.contract.canonical_path)
    prepared=prepare_experiment(specification,scientific_inputs=inputs.scientific_inputs,method_inputs=inputs.method_inputs,execution=execution)
    assert prepared.executable,prepared.dependencies
    return prepared


@pytest.mark.native
def test_actual_public_native_e2_execution_and_receipt_recovery_never_become_train_or_passive_results(tmp_path,monkeypatch):
    from tests.test_matrix_native_training_public_lifecycle import _actual_case
    from tests.test_matrix_native_training_parent_preflight import observe_native_preflight_controls
    ready_phases=observe_native_preflight_controls(monkeypatch,bindings)
    with threadpool_limits(limits=1):
        case=utility_case(tmp_path,original=_actual_case(tmp_path,monkeypatch,training_count=2),amended=True)
        prepared=copied_preparation(case,tmp_path/"utility-copied")
        directory=Path(case.plane.root.contract.canonical_path)/"native-e2-authored"
        authored=author_prepared_experiment(preparation=prepared,project_root=ROOT,artifact_writer=case.plane,output_dir=directory)
        assert authored["task_count"]==18 and authored["native_contact"]=="none"
        report=run_recursive_wave(directory=directory,project_root=ROOT,artifact_writer=case.plane,maximum_parallel_tasks=4)
        assert report["status"]=="SUCCEEDED" and report["new_native_contact_count"]==4
        assert sorted(ready_phases)==['prefix','prefix','responses','responses']
        retained,products,actual_draft,actual_plan=read_recursive_wave(directory=directory,artifact_writer=case.plane,include_products=True)
        from tests.matrix_native_acquisition_replay_controls import assert_actual_replay_rejects_changed_records
        assert_actual_replay_rejects_changed_records(case=case, products=products, draft=actual_draft,
            plan=actual_plan, training=False, monkeypatch=monkeypatch)
        task=owner.terminal_task_id(case.specification)
        summary,=(value for value in products["records"][task].values() if type(value) is r.NativeUtilitySummary)
        assert summary.assigned_units==2 and summary.qualification=="NOT_ESTABLISHED"
        assert summary.amended is not None
        assert summary.amended.adequacy.unit_ids == summary.amended.structural_advantage.unit_ids
        assert all(value.amended is not None for value in summary.outcomes)
        response_count=sum(len(value.native) for records in products["records"].values()
            for value in records.values() if type(value) is r.NativeUtilityResponse)
        assert 0<=response_count<=2  # Potential ordinary entry does not create a response observation.
        assert summary.scientific_status=="UNEVALUABLE"
        monkeypatch.setattr(LocalProcessExecutor,"execute",lambda *a,**kw:pytest.fail("completed E2 recovery entered executor"))
        recovered=run_recursive_wave(directory=directory,project_root=ROOT,artifact_writer=case.plane,maximum_parallel_tasks=4)
        assert recovered["status"]=="SUCCEEDED" and recovered["new_native_contact_count"]==0
        assert retained["qualification"]=="NOT_ESTABLISHED"


def _finite_score(case,*,factor_loss):
    """Disclosed 48-receiver arithmetic, never an acquired scientific result."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
    protocol=case.request.protocols[0];panels=r.panels_for(case.request,case.source);cells=[]
    for view in ("PRIMARY","FINE"):
        for panel in panels:
            for action in protocol.actions:
                for predictor in r.PREDICTORS:
                    for horizon in protocol.horizon_steps:
                        loss=D(factor_loss) if predictor=="FACTOR" else D(2)
                        impulse=action.amplitude*action.force_norm*protocol.public_source.coordinate.primary_view.timestep*min(action.pulse_steps,horizon)
                        errors=tuple(loss*impulse if index==24 else D(0) for index in range(48))
                        cells.append(ScheduledResponseLossCell(view,panel.panel_id,action.action_id,predictor,horizon,
                            (D(0),)*48,errors,errors,(None,)*48,loss))
    controls=[]
    for branch,view,*_ in branch_census(protocol,panels):
        count=(1 if view=="PRIMARY" else 2)*protocol.horizon_steps[-1]
        controls.append(ScheduledResponseTransitionControl("control.scheduled."+case.source.root_id+"."+branch,
            "SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS",D(0),protocol.native_reference_tolerance,
            "SATISFIED",count,192,(D(0),)*count,()))
    with localcontext() as context:
        context.prec=50
        cumulative=tuple((1+(D(factor_loss) if predictor=="FACTOR" else D(2))).ln() for predictor in r.PREDICTORS for _ in protocol.horizon_steps)
    return replace(_unresolved_score(case),controls=tuple(controls),numerical_pass=True,disposition="FINITE",
        cells=tuple(sorted(cells,key=lambda value:value.key)),cumulative_log_errors=cumulative,reason_codes=())


@pytest.mark.parametrize("factor_loss,expected_success",(("1",True),("3",False)))
def test_explicit_full_coupled_comparator_preserves_positive_and_adverse_paired_utility(tmp_path,factor_loss,expected_success):
    case=utility_case(tmp_path);protocol=case.request.protocols[0];panels=r.panels_for(case.request,case.source)
    score=_finite_score(case,factor_loss=factor_loss)
    outcome=science.assess_score(case.specification,protocol,panels,case.acquisition,score)
    assert outcome.usable and outcome.success is expected_success
    assert all(value==D(2)-D(factor_loss) for _,_,value in outcome.contrasts)
    summary=science.summarize(case.specification,case.acquisition,(outcome,))
    assert summary.successes==int(expected_success) and summary.usable_units==summary.assigned_units==1
    assert summary.scientific_status=="UNEVALUABLE" and summary.sampling_warrant=="NOT_ESTABLISHED"
    assert not summary.conditional_criterion_met  # One disclosed root cannot meet alpha1/20.


@pytest.mark.parametrize("defect",("normalized-units","cross-predictor-truth","missing-branch-control","foreign-role"))
def test_e2_utility_reducer_refuses_favorable_arithmetic_or_independent_control_substitution(tmp_path,defect):
    case=utility_case(tmp_path);protocol=case.request.protocols[0];panels=r.panels_for(case.request,case.source)
    score=_finite_score(case,factor_loss="1")
    if defect=="normalized-units":score=replace(score,cells=(replace(score.cells[0],normalized_error=D(0)),*score.cells[1:]))
    elif defect=="cross-predictor-truth":score=replace(score,cells=(replace(score.cells[0],actual_odd_responses=(D(1),)*48),*score.cells[1:]))
    elif defect=="foreign-role":score=replace(score,role="CONFIRMATION")
    else:score=replace(score,controls=score.controls[:-1])
    with pytest.raises(ValueError,match="native E2"):
        science.assess_score(case.specification,protocol,panels,case.acquisition,score)


@pytest.mark.parametrize("count", (1, 3))
def test_native_e2_contracts_reuse_exact_request_identity_without_changing_operands(tmp_path, monkeypatch, count):
    case = utility_case(tmp_path, root_count=count)
    context = __import__("decimal").getcontext()
    # Obtain the complete unchanged contract independently of the bounded cache.
    signature = (context.prec, context.rounding, context.Emin, context.Emax, context.clamp,
        context.capitals, tuple(sorted((signal.__name__, enabled) for signal, enabled in context.traps.items())))
    expected = owner._contracts.__wrapped__(signature, case.specification, case.request)
    identity = r._Identity.identity.fget
    calls = {r.NativeUtilitySpecification: 0, r.NativeUtilityRequest: 0}
    def observed(record):
        if type(record) in calls:
            calls[type(record)] += 1
        return identity(record)
    monkeypatch.setattr(r._Identity, "identity", property(observed))
    actual = owner._contracts.__wrapped__(signature, case.specification, case.request)
    assert actual == expected
    assert calls == {r.NativeUtilitySpecification: 1, r.NativeUtilityRequest: 1}
