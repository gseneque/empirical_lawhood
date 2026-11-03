# SPDX-License-Identifier: MPL-2.0
"""In-memory selected E4 software controls; no native, custody or authority acts.

The disclosed 32/64/64 populations are release fixtures. Shape and arithmetic
controls here do not establish original producer, source or scientific warrant.
"""
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_science as method
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as p
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import selected_target_shape
from empirical_lawhood.api import selected_e4_programme_service as public
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
from tests.test_matrix_selected_package import package
from tests.test_matrix_selected_e4_fixtures import selected_e4_populations,selected_bridge,transfer  # noqa: F401
from tests.test_matrix_selected_e4_methods import selected_revision,fixture_observations  # noqa: F401
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401
from tests.test_matrix_source_evidence import source_case  # noqa: F401


def _ordinary_structure_case(monkeypatch):
    """Disclosed adverse metadata tests orchestration, never actual custody."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_protocol import NativeTrainingScientificProtocol
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_reduction import NATIVE_PHASES, ScheduledProgrammeNativeDisposition
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
    from empirical_lawhood.runtime.plans import ExecutionPlan

    def pin(name, kind):
        return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, "a"*64)

    original = Path(__file__).parents[1]/"programmes/foundations/emergent-structure/workflows/matrix-response-experiment/native-training-scientific-protocol.example.json"
    coordinate = decode_canonical_bytes(original.read_bytes(), NativeTrainingScientificProtocol, maximum_bytes=None).coordinates[0]
    observations = []
    locators = []
    rows = []
    for wave_id in ("wave.a", "wave.b"):
        group = "group."+wave_id
        native = tuple(ScheduledProgrammeNativeDisposition(phase,"UNENTERED",None,None,None,
            ("disclosed-orchestration-control",)) for phase in NATIVE_PHASES)
        cases = tuple(r.SelectedE4NativeCaseResult("root."+wave_id+"."+str(index),
            pin("source."+wave_id+"."+str(index),ScheduledSource), group,
            "UNENTERED","UNENTERED","UNENTERED",(None,)*30,
            tuple((method,(None,)*15) for method in selected_target_shape("PAIRED15")[0]),None,None,None,(),native,
            ("disclosed-orchestration-control",),None,None,None,coordinate) for index in range(9))
        observations.append(r.SelectedE4WaveObservation("observation."+wave_id,
            pin("declaration.disclosed",r.SelectedE4NativeProgrammeDeclaration),wave_id,
            pin("plan."+wave_id,ExecutionPlan),
            ObjectIdentity("terminal."+wave_id,"empirical-lawhood/runtime/run-recovery-terminal-event","1.0.0","b"*64),
            cases,()))
        locators.append(SimpleNamespace(wave_id=wave_id,run_id="run."+wave_id))
        rows.append(public.SelectedE4ComponentRequest(wave_id,"run."+wave_id,"package."+wave_id+".json",
            "reveal."+wave_id,None,()))
    programme = SimpleNamespace(waves=tuple(SimpleNamespace(wave_id=row.wave_id) for row in locators),
        group_ids=tuple(row.cases[0].group_id for row in observations),
        cases=tuple(case for observation in observations for case in observation.cases))
    plan = SimpleNamespace(identity=pin("programme.disclosed",public.d.SelectedE4ProtectedProgrammePlan),
        declaration=SimpleNamespace(programme=programme,maximum_parallel_tasks=4,
        root=SimpleNamespace(campaign=object())),bank=object(),structure=object(),secondary_readout=object(),structural_resources=object())
    def forbidden(**_kwargs):
        raise AssertionError("structural orchestration must not enter, recover, author or publish original work")
    service = SimpleNamespace(artifact_writer=object(),project_root=Path("/disclosed-selected-source"),
        run=forbidden,recover=forbidden,author=forbidden,read=forbidden)
    wrapper = public.SelectedE4ProgrammeService(service=service)
    seen = []
    def locator(writer, selection, declaration):
        assert writer is wrapper.writer and declaration is plan.declaration
        seen.append(selection)
        return next(value for value in locators if value.wave_id==selection.component_id)
    monkeypatch.setattr(public,"_locator",locator)
    response = {"assigned_groups":2,"assigned_cases":18,"new_native_contact_count":0,
        "scientific_completion":"ADVERSE_TERMINAL_RETAINED"}
    result = {"scientific_completion":"COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS",
        "original_response":response,"original_wave_observations":tuple(row.to_document() for row in observations),
        "assigned_groups":2,"assigned_cases":18,"new_native_contact_count":0}
    return SimpleNamespace(wrapper=wrapper,plan=plan,state=SimpleNamespace(environment_id="environment.disclosed"),
        request=SimpleNamespace(components=tuple(rows),collection=None),locators=tuple(locators),
        observations=tuple(observations),result=result,seen=seen,forbidden=forbidden)


@pytest.mark.parametrize("produce",(False,True))
def test_ordinary_structure_retains_every_adverse_case_and_uses_only_selected_pure_route(monkeypatch,produce):
    from empirical_lawhood.api import selected_e4_structure as structure
    case = _ordinary_structure_case(monkeypatch)
    calls = []
    def selected(**kwargs):
        calls.append(kwargs)
        return case.result
    monkeypatch.setattr(structure,"produce_selected_e4_structure",selected if produce else case.forbidden)
    monkeypatch.setattr(structure,"read_selected_e4_structure",case.forbidden if produce else selected)
    # A later assessment is outside the complete original wave source roster.
    assessment = public.SelectedE4ComponentRequest(public.d.ASSESSMENT_COMPONENT_ID,"run.assessment",
        "package.assessment.json","reveal.assessment",None,())
    request = SimpleNamespace(components=(*case.request.components,assessment))
    observations,report = case.wrapper._structure(directory=Path("/disclosed-programme"),plan=case.plan,
        state=case.state,request=request,produce=produce,maximum_parallel_tasks=4)
    assert observations==case.observations
    assert sum(len(value.cases) for value in observations)==18
    assert all(value.disposition=="UNENTERED" and value.paired_log_targets==(None,)*30
        and not value.ordinary_receipts for observation in observations for value in observation.cases)
    assert report["structure"]=={key:value for key,value in case.result.items()
        if key not in ("original_response","original_wave_observations")}
    assert not {"original_response","original_wave_observations"}.intersection(report["structure"])
    assert report["assigned_groups"]==2 and report["assigned_cases"]==18
    assert report["new_native_contact_count"]==0
    assert case.seen==list(case.request.components)
    call, = calls
    assert call["programme"] is case.plan.declaration.programme and call["bank"] is case.plan.bank
    assert call["choices"] is case.plan.structure and call["resources"] is case.plan.structural_resources
    assert call["secondary_readout"] is case.plan.secondary_readout
    assert call["declaration"] is case.plan.declaration and call["waves"]==case.locators
    assert call["campaign"] is case.plan.declaration.root.campaign
    if produce:
        assert call["maximum_parallel_tasks"]==4 and call["environment_id"]==case.state.environment_id
        assert call["project_root"]==case.wrapper.service.project_root
    else:
        assert not {"maximum_parallel_tasks","environment_id","project_root"}.intersection(call)


@pytest.mark.parametrize("damage",("missing","duplicate","reordered","absent"))
@pytest.mark.parametrize("produce",(False,True))
def test_ordinary_structure_refuses_incomplete_original_wave_selection_before_any_stage(monkeypatch,damage,produce):
    from empirical_lawhood.api import selected_e4_structure as structure
    case = _ordinary_structure_case(monkeypatch)
    monkeypatch.setattr(structure,"produce_selected_e4_structure",case.forbidden)
    monkeypatch.setattr(structure,"read_selected_e4_structure",case.forbidden)
    rows = case.request.components
    request = None if damage=="absent" else SimpleNamespace(components=rows[:-1] if damage=="missing" else
        (rows[0],rows[0]) if damage=="duplicate" else rows[::-1])
    with pytest.raises(PermissionError,match="every actual original wave"):
        case.wrapper._structure(directory=Path("/disclosed-programme"),plan=case.plan,state=case.state,
            request=request,produce=produce,maximum_parallel_tasks=4)


@pytest.mark.parametrize("damage",("missing","reordered","extra"))
def test_ordinary_structure_refuses_a_changed_retained_observation_census(monkeypatch,damage):
    from empirical_lawhood.api import selected_e4_structure as structure
    case = _ordinary_structure_case(monkeypatch)
    values = case.result["original_wave_observations"]
    case.result["original_wave_observations"] = values[:-1] if damage=="missing" else values[::-1] if damage=="reordered" else (*values,values[-1])
    monkeypatch.setattr(structure,"produce_selected_e4_structure",case.forbidden)
    monkeypatch.setattr(structure,"read_selected_e4_structure",lambda **kwargs:case.result)
    with pytest.raises(PermissionError,match="observation census"):
        case.wrapper._structure(directory=Path("/disclosed-programme"),plan=case.plan,state=case.state,
            request=case.request,produce=False)


def test_ordinary_structure_current_access_refusal_precedes_any_stage(monkeypatch):
    from empirical_lawhood.api import selected_e4_structure as structure
    case = _ordinary_structure_case(monkeypatch)
    actual = public._locator
    def refuse_second(writer,selection,declaration):
        if selection.component_id=="wave.b":
            raise PermissionError("disclosed actual current reveal refusal")
        return actual(writer,selection,declaration)
    monkeypatch.setattr(public,"_locator",refuse_second)
    monkeypatch.setattr(structure,"produce_selected_e4_structure",case.forbidden)
    monkeypatch.setattr(structure,"read_selected_e4_structure",case.forbidden)
    with pytest.raises(PermissionError,match="current reveal refusal"):
        case.wrapper._structure(directory=Path("/disclosed-programme"),plan=case.plan,state=case.state,
            request=case.request,produce=True,maximum_parallel_tasks=4)
    assert case.seen==[case.request.components[0]]


@pytest.mark.parametrize("operation",("read","run","recover"))
def test_ordinary_unentered_revision_never_enters_structural_or_native_work(monkeypatch,operation):
    case = _ordinary_structure_case(monkeypatch)
    retained = {"state":"UNENTERED_REVISION_NOT_TRIGGERED","scientific_completion":"NOT_ESTABLISHED",
        "new_native_contact_count":0,"structure":{"state":"NOT_ENTERED","scientific_completion":"NOT_ESTABLISHED",
            "new_native_contact_count":0}}
    monkeypatch.setattr(case.wrapper,"_state",lambda directory:(case.plan,case.state))
    monkeypatch.setattr(case.wrapper,"_request",lambda path,plan,*,request=None:case.request)
    monkeypatch.setattr(case.wrapper,"_unentered",lambda plan:retained)
    monkeypatch.setattr(case.wrapper,"_structure",case.forbidden)
    kwargs={"directory":Path("/disclosed-programme")}
    if operation!="read":
        kwargs.update(maximum_parallel_tasks=4,confirmed=True)
    assert getattr(case.wrapper,operation)(**kwargs) is retained
    assert case.seen==[]


def test_ordinary_partial_read_preserves_assigned_census_without_structure_or_access(monkeypatch):
    case = _ordinary_structure_case(monkeypatch)
    monkeypatch.setattr(case.wrapper,"_state",lambda directory:(case.plan,case.state))
    monkeypatch.setattr(case.wrapper,"_request",lambda path,plan,*,request=None:case.request)
    monkeypatch.setattr(case.wrapper,"_unentered",case.forbidden)
    monkeypatch.setattr(case.wrapper,"_structure",case.forbidden)
    report = case.wrapper.read(directory=Path("/disclosed-programme"),allow_partial=True)
    assert report["state"]=="UNASSESSED" and report["new_native_contact_count"]==0
    assert report["assigned_groups"]==case.plan.declaration.programme.group_ids
    assert report["assigned_cases"]==tuple(row.root_id for row in case.plan.declaration.programme.cases)
    assert len(report["assigned_cases"])==18 and case.seen==[]


def test_all_actual_new_factories_build_manifest_bound_parent_prepared_runners():
    class Supplier:
        def resolve_input(self,spec):raise AssertionError("discovery must not read inputs")
        def prepare_selected_e4_protected(self,context,runner):raise AssertionError("discovery must not prepare or grant a task")
    declarations=owner.operation_declarations()
    keys=tuple(value.capability_key for value in declarations)
    assert keys==tuple(sorted(keys))
    expected={owner.NAMESPACE+"."+phase for phase in (*owner.PHASES,*owner.EXTRAS)}
    expected.update(owner.key_for_phase(phase,referenced=True,compact_protocol=compact)
        for phase in owner.PHASES if phase not in ("entry","reduce") for compact in (False,True))
    assert set(keys)==expected
    assert len({(value.capability_key,value.capability_version) for value in declarations})==len(declarations)
    registry=CapabilityRegistry("registry.disclosed-protected-e4",tuple(v.manifest() for v in declarations))
    for declaration in declarations:
        factory=declaration.provider_factory()
        ports=(ExecutablePlatformPort(factory.binding.required_platform_port_keys[0],RecursiveOperationInputPort(Supplier())),)
        provider=factory.build_provider(registry=registry,records=(),platform_ports=ports)
        runner,=provider.runners(registry)
        assert runner.manifest==declaration.manifest()
        assert runner.native_effect==(declaration.capability_key.rsplit(".",1)[1] in owner.NATIVE)


def test_selected_operation_families_use_compiler_allowed_stage_kinds():
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_bindings, selected_protected_bindings, selected_revision_bindings
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings, selected_e4_method_bindings
    from empirical_lawhood.runtime.candidate_compiler import _ALLOWED_STAGE_KINDS
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
    from empirical_lawhood.runtime.compiler import _validate_stage_capability
    from empirical_lawhood.runtime.plans import ProtocolStepTemplate

    families = (selected_e3_e4_bindings, owner, selected_e4_method_bindings,
        selected_opportunity_bindings, selected_protected_bindings, selected_revision_bindings)
    for family in families:
        for declaration in family.operation_declarations():
            assert declaration.kind in _ALLOWED_STAGE_KINDS[declaration.stage], (
                family.__name__, declaration.capability_key, declaration.stage, declaration.kind)
            manifest=declaration.manifest()
            config=CapabilityConfigRef("config.stage-guard",manifest.config_schema,
                manifest.config_schema_sha256,"a"*64,"artifact.stage-guard")
            step=ProtocolStepTemplate("step.stage-guard",declaration.stage,manifest.capability_key,
                manifest.capability_version,config,(),declaration.outputs,manifest.permissions,
                declaration.outcome_access,declaration.visibility_ceiling,declaration.resources,(),
                declaration.execution_properties.barrier,1,("obligation.stage-guard",))
            _validate_stage_capability(step,declaration.kind)


def test_actual_phase_sources_keep_original_subject_and_cold_canonical_local_configs(selected_revision):  # noqa: F811
    f=selected_revision
    decision=p.SelectedE4PublicRevisionDecision.from_products(f.programme,f.nomination,f.frozen,record_id="decision.disclosed-e4")
    models=p.SelectedE4PublicModels.from_products(f.programme,f.nomination,f.frozen,record_id="models.disclosed-e4")
    summary=p.SelectedE4OriginalCalibrationSummary.from_package(f.populations.selected.package,record_id="summary.disclosed-e4")
    programme,bank=f.populations.calibration,f.populations.calibration_bank
    descriptor=bank.sources[0]
    source=r.SelectedE4ProtectedNativeSourceReference.from_bank(programme,bank,descriptor,index=bank.source_index())
    assert r.identity(source)==source.identity
    assert source.reference.identity==descriptor.identity
    assert source.identity!=source.reference.identity
    protocol,panels=bank.response_selection.validate_source(bank.source(descriptor.root_id,index=bank.source_index()))
    config=owner.SelectedE4ProtectedCompactConfig("config."+owner.local_node(source.root_id,"prefix"),programme.identity,source,
        protocol,panels,bank.response_selection.identity,"prefix","CALIBRATION",decision,models,None,summary)
    assert decode_canonical_bytes(config.canonical_bytes(),type(config),maximum_bytes=None)==config
    assert decode_canonical_bytes(source.canonical_bytes(),type(source),maximum_bytes=None)==source
    assert len(config.canonical_bytes())<4*1024**2 and len(source.canonical_bytes())<=256*1024
    with pytest.raises(ValueError):
        replace(source,public=replace(source.public,root=replace(source.public.root,role=source.public.root.role.DEVELOPMENT)))
    with pytest.raises(ValueError):
        replace(config,population_phase="DEVELOPMENT")


def test_original_infinite_calibration_summary_is_exactly_retained_and_never_e4_warrant():
    original=package(missing=20)
    assert original.calibration.radius is None
    summary=p.SelectedE4OriginalCalibrationSummary.from_package(original,record_id="summary.disclosed-infinite")
    assert summary.radius is None and summary.rank==original.calibration.rank
    assert summary.group_ids==original.allocation.unit_ids("calibration")
    assert summary.applicability=="ORIGINAL_E3_SCOPE_ONLY_E4_APPLICABILITY_UNEVALUABLE"
    assert decode_canonical_bytes(summary.canonical_bytes(),type(summary),maximum_bytes=None)==summary
    with pytest.raises(ValueError):replace(summary,applicability="E4_APPLICABLE")
    with pytest.raises(ValueError):replace(summary,rank=summary.rank-1)


def test_full64_by9_reducer_preserves_whole_missing_group_all30_and_all_three_original_accounts(selected_revision):  # noqa: F811
    f=selected_revision
    programme,bank=f.populations.confirmation,f.populations.confirmation_bank
    reduction,_=fixture_observations(programme,bank)
    group=programme.group_ids[0]
    cases=tuple(replace(v,disposition="UNKNOWN",numerical_disposition="UNKNOWN",score_disposition="UNEVALUABLE",
        paired_log_targets=(None,)*30,score=None,score_projection=None,reason_codes=("disclosed-whole-group-missing",))
        if v.group_id==group else v for v in reduction.cases)
    result,observed,forecasts=method.reduce_cases(programme,bank.identity,cases,record_id="reduction.disclosed-full64")
    assert len(result.group_ids)==64 and len(result.cases)==576
    assert sum(v.group_id==group for v in observed.cases)==9
    assert all(len(v.paired_log_targets)==30 and len(v.original_log_points)==3 for v in result.cases)
    assert len(forecasts.forecasts)==0
    assert decode_canonical_bytes(result.canonical_bytes(),type(result),maximum_bytes=None)==result
    with pytest.raises(ValueError,match="census"):
        method.reduce_cases(programme,bank.identity,cases[9:],record_id="reduction.disclosed-thinned")


def test_native_and_collector_budgets_both_require_explicit_finite_non_time_limits():
    budget=ResourceBudget(1,64*1024**2,0,None,1024,1024)
    selected=r.SelectedE4NativeBudgets("budgets.disclosed-e4",tuple((phase,budget) for phase in sorted(owner.PHASES)),budget)
    assert decode_canonical_bytes(selected.canonical_bytes(),type(selected),maximum_bytes=None)==selected
    with pytest.raises(ValueError):
        replace(selected,collector_budget=replace(budget,source_scan_bytes=None))
    with pytest.raises(ValueError):
        replace(selected,collector_budget=replace(budget,wall_time_seconds=D(1)))


def test_unprepared_new_worker_refuses_before_reading_any_protected_port():
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_protected_workers import SelectedE4ProtectedWorker
    declaration=next(v for v in owner.operation_declarations() if v.capability_key.endswith(".response-score"))
    runner=SelectedE4ProtectedWorker("response-score",declaration.manifest())
    with pytest.raises(TypeError,match="TaskContext"):runner.execute(object())


@pytest.mark.parametrize("recover",(False,True))
@pytest.mark.parametrize("refusal",("source","resources"))
def test_actual_all_wave_preflight_refuses_wave_two_before_any_wave_one_execution(monkeypatch,recover,refusal):
    """Control sequencing only; real validators own independent custody tests."""
    entered=[];checked=[]
    class Candidate:
        candidate_id="candidate.disclosed-e4"
        SCHEMA="empirical-lawhood/testing/candidate"
        VERSION="1.0.0"
        def fingerprint(self):return "1"*64
    candidate=Candidate()
    package_value=SimpleNamespace(run_plan_id="run.disclosed-e4",issued_study=SimpleNamespace(candidate=candidate))
    plan_value=SimpleNamespace(minimum_free_bytes=0)
    run_value=SimpleNamespace(run_plan_id="run.disclosed-e4")
    context=SimpleNamespace(association=SimpleNamespace(candidate=r.pin(candidate,"candidate_id")))
    class Execution:
        artifact_plane=SimpleNamespace(root=SimpleNamespace(verify=lambda **kwargs:None))
        def __init__(self,index):self.index=index
        def load_persisted_package(self,run):return package_value
        def _check_identity(self,*args,**kwargs):
            checked.append(("source",self.index))
            if self.index==2 and refusal=="source":raise PermissionError("disclosed current source refusal")
        def _validate_campaign_authorization(self,*args,**kwargs):pass
        def _validate_issued_execution_authority(self,*args,**kwargs):pass
        def _validate_issued_reveal_authority(self,*args,**kwargs):pass
        def preexecution_contract_closure(self,**kwargs):return SimpleNamespace(require_pass=lambda:None)
        def resource_admission(self,*args,**kwargs):
            checked.append(("resources",self.index))
            return SimpleNamespace(admitted=not(self.index==2 and refusal=="resources"),reason_codes=("DISCLOSED_RESOURCE_REFUSAL",))
    def api(index):
        return SimpleNamespace(_execution_service=Execution(index),_compile_path=lambda path:(package_value,run_value,plan_value),
            _compile_package=lambda package:(run_value,plan_value),_study_issue_clock=SimpleNamespace(now_utc=lambda:"2026-10-17T00:00:00Z"),
            _conditional_execution_records=lambda **kwargs:())
    contexts=iter(((context,api(1)),(context,api(2))))
    service=SimpleNamespace(artifact_writer=SimpleNamespace(root=SimpleNamespace(resolve=lambda v,**kwargs:Path("/explicit-el")/v)),
        _prospective_context=lambda *args,**kwargs:next(contexts),
        run=lambda **kwargs:entered.append(kwargs),recover=lambda **kwargs:entered.append(kwargs))
    wrapper=public.SelectedE4ProgrammeService(service=service)
    waves=(SimpleNamespace(wave_id="wave.a"),SimpleNamespace(wave_id="wave.b"))
    plan=SimpleNamespace(component_ids=("wave.a","wave.b","assessment"),
        declaration=SimpleNamespace(maximum_parallel_tasks=4,programme=SimpleNamespace(waves=waves)))
    rows=tuple(public.SelectedE4ComponentRequest(w.wave_id,"run.disclosed-e4","controls/package.json",
        "authority.disclosed-reveal",None,()) for w in waves)
    monkeypatch.setattr(wrapper,"_unentered",lambda plan:None)
    monkeypatch.setattr(wrapper,"_state",lambda directory:(plan,None))
    monkeypatch.setattr(wrapper,"_request",lambda path,plan,*,request=None:SimpleNamespace(components=rows,collection=None))
    with pytest.raises((ValueError,PermissionError),match="source refusal|resource admission"):
        wrapper._operation(directory=Path("/explicit-el/programme"),maximum_parallel_tasks=4,
            programme_request_path=Path("/explicit-el/request.json"),confirmed=True,recover=recover)
    assert entered==[]
    assert ("source",1) in checked and ("source",2) in checked




def test_explicit_resource_profile_derives_exact_native_cells_without_task_id_configuration():
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_operational_resources import SelectedE4OperationalResources
    path=Path(__file__).parents[1]/"programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/resources-calibration.example.json"
    choice=decode_canonical_bytes(path.read_bytes(),SelectedE4OperationalResources,maximum_bytes=None)
    budget=ResourceBudget(1,256*1024**2,0,None,1024,1024)
    result=choice.for_component(component_id="wave.disclosed",budgets={"task.disclosed":budget},
        phases={"task.disclosed":"prefix"},native_groups={"task.disclosed":"group.disclosed"})
    cell,=result.task_cells
    assert result.maximum_parallel_tasks==4
    assert cell.task_id=="task.disclosed" and cell.physical_independent_unit_id=="group.disclosed"
    assert cell.native_simulator_launch and cell.resource_budget.source_byte_limit==1024
    with pytest.raises(ValueError,match="omits"):
        choice.for_component(component_id="wave.disclosed",budgets={"task.disclosed":budget},
            phases={"task.disclosed":"undeclared"},native_groups={})


def test_parent_native_scope_requires_exact_whole_wave_budgets_and_selected_concurrency(selected_e4_populations):  # noqa: F811
    from empirical_lawhood.api.selected_e4_native_runtime import require_selected_e4_native_plan_budget
    programme=selected_e4_populations.calibration;wave=programme.waves[0]
    cases=tuple(v for v in programme.cases if v.root_id in wave.root_ids)
    budget=ResourceBudget(1,64*1024**2,0,None,1024,1024)
    phases={owner.global_node(programme,p,wave.wave_id):p for p in ("entry","reduce","adjudicate")}
    phases.update((owner.local_node(c.root_id,p),p) for c in cases for p in owner.PHASES if p not in ("entry","reduce"))
    tasks=tuple(SimpleNamespace(task_id=n,capability=SimpleNamespace(capability_key=owner.NAMESPACE+"."+p,requested_resources=budget))
        for n,p in sorted(phases.items()))
    declaration=SimpleNamespace(maximum_parallel_tasks=4,planned_task_budgets=tuple((v.task_id,budget) for v in tasks))
    entry=SimpleNamespace(declaration=declaration,wave_id=wave.wave_id,programme=programme,scope_cases=cases)
    package_value=SimpleNamespace(execution_resource_envelope_spec=SimpleNamespace(maximum_parallel_tasks=4))
    require_selected_e4_native_plan_budget(package=package_value,plan=SimpleNamespace(tasks=tasks),entry=entry)
    with pytest.raises(PermissionError,match="concurrency"):
        require_selected_e4_native_plan_budget(package=SimpleNamespace(execution_resource_envelope_spec=SimpleNamespace(maximum_parallel_tasks=1)),
            plan=SimpleNamespace(tasks=tasks),entry=entry)
    wrong=SimpleNamespace(task_id=tasks[0].task_id,capability=SimpleNamespace(capability_key=tasks[0].capability.capability_key,
        requested_resources=replace(budget,memory_bytes=32*1024**2)))
    with pytest.raises(PermissionError,match="budget"):
        require_selected_e4_native_plan_budget(package=package_value,plan=SimpleNamespace(tasks=(wrong,*tasks[1:])),entry=entry)


@pytest.mark.held
@pytest.mark.parametrize("phase", ("CAL", "CONF"))
@pytest.mark.parametrize("component", ("wave", "assessment"))
def test_selected_size_component_structural_preparation_refuses_unsigned_authoring(
        literal_recipe_source_inputs, source_case, tmp_path, monkeypatch, phase, component):  # noqa: F811
    """Declared-size structure and honest unsigned refusal, no issued proof."""
    import json
    import os
    from empirical_lawhood.adapters.methods import matrix_source_evidence as shared
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_bank_recipe as recipe
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as science
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as preparation_owner
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial as factorial
    from empirical_lawhood.api.experiment_preparation import author_prepared_experiment,load_experiment_inputs
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection,ExperimentInputBinding,ExperimentFileInputBinding
    from empirical_lawhood.infrastructure.source_closure import capture_target_closure
    from empirical_lawhood.api.facade import EmpiricalLawhoodApi
    from empirical_lawhood.api.models import ExperimentPackage
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, PreparedExperimentFile
    from empirical_lawhood.runtime.experimental_factorial import PairInteractionScale
    from empirical_lawhood.runtime.experimental_statistics import PairedMeanTAlternative
    from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile, resolve_external_root_contract
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, ExecutionPlan
    from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent
    from empirical_lawhood.runtime.study_issue import IssuedExecutableStudyManifest
    from empirical_lawhood.planning.study_issue import StudyOperationAuthority
    from empirical_lawhood.kernel.evidence import EvidenceCeiling
    from tests import matrix_selected_source_predecessor as gates, matrix_selected_e4_public_fixture as held
    from tests.test_matrix_selected_e4_methods import declaration
    from tests.test_matrix_selected_e4_public_programme import _wave_observation_records
    from tests.test_matrix_selected_protected import unpublished
    from tests.test_matrix_sampling_follow_on import prior_product

    old=held.old
    literal=literal_recipe_source_inputs
    # Reuse its small DEV fit while testing the actual full protected group
    # and wave sizes. These generated outcomes remain disclosed test inputs.
    protected_groups=20
    selected_recipe=replace(literal.inputs.recipe,population_designs=tuple((role,
        replace(design,group_count=protected_groups,wave_group_count=8) if role!="DEVELOPMENT" else design)
        for role,design in literal.inputs.recipe.population_designs))
    f=SimpleNamespace(**{**vars(literal),"inputs":replace(literal.inputs,recipe=selected_recipe)})
    selected_root=Path(f.case.plane.root.contract.canonical_path)
    assert selected_root.is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    profile_path=Path(os.environ.get("EL_TEST_OPERATOR_PROFILE",
        "/media/chevre/EL/empirical-lawhood/operator-profiles/el-four-core-default.json"))
    if not profile_path.is_file():pytest.skip("select existing EL profile for held component compile/proof")
    raw=profile_path.read_bytes()
    profile=decode_canonical_bytes(raw,OperatorStorageProfile,maximum_bytes=len(raw))
    profile=replace(profile,profile_id="operator.disclosed-components",external_root_locator=str(selected_root.parent),artifact_namespace=selected_root.name)
    contract=resolve_external_root_contract(profile,repo_root=held.ROOT,home_root=Path.home())
    contract=replace(contract,storage_root_id=f.case.plane.root.contract.storage_root_id,logical_name=f.case.plane.root.contract.logical_name)
    contract=resolve_external_root_contract(profile,selected_contract=contract,repo_root=held.ROOT,home_root=Path.home())
    writer=ExternalArtifactPlane(GuardedExternalRoot(contract),validators=f.case.plane.validators,
        semantic_validations=f.case.plane.semantic_validations,custody_limits=f.case.plane.custody_limits)
    writer.root.verify(for_write=True)
    stem="disclosed-component."+phase.lower()+"."+component
    allocation=recipe.recipe_allocation(f.inputs)
    reservation=old.ScheduledReservation("reservation."+stem,allocation,f.publish(writer,allocation,stem+".allocation"))
    selection=recipe.recipe_selection(f.inputs,reservation)
    specification=old.ScheduledSpecification("specification."+stem,selection,f.publish(writer,selection,stem+".selection"))
    banks={};programmes={}
    for label,role in (("DEV","DEVELOPMENT"),("CAL","CALIBRATION"),("CONF","CONFIRMATION")):
        _,responses=recipe.recipe_responses(f.inputs,reservation,specification,f.case.provenance,role)
        bank=recipe.recipe_bank(f.inputs,reservation=reservation,specification=specification,provenance=f.case.provenance,
            criterion_publication=f.publish(writer,f.inputs.original_preparation.mathematical_protocol,stem+".criterion"),
            response_publication=f.publish(writer,responses,stem+".responses."+label.lower()),phase=role)
        banks[label]=bank;programmes[label]=recipe.recipe_programme(bank,role)
    development=programmes["DEV"]
    reduction,data=fixture_observations(development,banks["DEV"])
    choice=science.derive_revision_specification(declaration(development),development)
    nomination=science.select_revision(choice,development,banks["DEV"],reduction,data,nomination_id="nomination."+stem)
    frozen=science.freeze_revision(development,nomination,freeze_id="frozen."+stem)
    assert nomination.trigger_disposition=="TRIGGERED"
    export=p.SelectedE4RevisionExport.from_products(development,nomination,frozen,record_id="export."+stem)
    def pin(name,kind):return ObjectIdentity(name,kind.SCHEMA,kind.VERSION,"a"*64)
    def locator(value,operation):
        return r.SelectedE4DevelopmentProduct(value.identity,"unissued-dev","run.unissued-dev",
            pin("plan.unissued-dev",DevelopmentExecutionPlan),"method."+operation,pin("receipt."+operation,CanonicalTaskReceipt),unpublished(value,"product."+operation))
    products=SimpleNamespace(nomination=nomination,frozen=frozen,
        nomination_locator=locator(nomination,"revision-fit"),frozen_locator=locator(frozen,"revision-freeze"))
    bank,programme=banks[phase],programmes[phase]
    selected_wave=programme.waves[-1]
    pipeline,_=source_case
    cutoff=InformationCutoff("cutoff."+stem,programme.cases[0].information_cutoff.clock_id,CausalPhase.PREPARATION,D(0))
    scope=gates.ReleaseGateScope("scope."+stem,programme.identity,bank.identity,old.identity(bank.reservation),bank.response_selection.identity,
        old.identity(bank.source(bank.sources[0].root_id,index=bank.source_index()).numerical_design),cutoff,programme.group_ids,pipeline.pipeline_config.profile,
        pipeline.receipt,pipeline.evidence_profile,pipeline.receipt.publication,pipeline.receipt.recovery,pipeline.receipt.validator_receipts[0])
    configs=gates.gate_configs(scope)
    declarations=tuple(gates.gate_declaration(kind) for kind in gates.GATES)
    qualifier=shared.MatrixSourceQualificationConfig("qualification."+stem,gates.gate_specification(scope),pipeline.receipt,
        CapabilityRegistry("registry."+stem,tuple(sorted((value.manifest() for value in declarations),key=lambda value:value.registry_id))),
        tuple(sorted((gates.gate_product(value) for value in configs),key=lambda value:value.evidence_id)))
    # Typed structural metadata, with no issued original producer locators. An
    # execution attempt must still refuse these disclosed prerequisites.
    source=r.SelectedE4SourceQualification("source."+stem,qualifier.specification,qualifier.assess(),
        replace(pipeline,qualification_config=qualifier),(),())
    rule=science.SelectedE4NominationRule("rule."+stem,("REVISION","ORIGINAL_E3"),D(0),4,0,D(100),(),
        science.workflow.ENDPOINT,len(programmes["CONF"].group_ids),PairedMeanTAlternative.LESS)
    factor=science.SelectedE4FactorialSpecification("factorial."+stem,programmes["CONF"].identity,choice.target,
        factorial.ENDPOINT,PairInteractionScale.SIGNED_MEAN_DIFFERENCE,
        tuple(factorial.ScheduledFactorialComparison(name,PairedMeanTAlternative.TWO_SIDED_POINT_NULL,D(0),None) for name in factorial.E4_COMPARISONS),
        D(".05"),factorial.PROCEDURE,factorial.mean_t_requirement("requirement."+stem),(),"REQUIRE_COMPLETE_ASSIGNED_WHOLE_GROUPS",factorial.FAMILY_IDS)
    settings=selected_root/(stem+".confirmation.json")
    settings.write_text(json.dumps({"calibration_alpha":".05","nomination_rule":rule.to_document(),"factorial":factor.to_document()}))
    selected=SimpleNamespace(namespace=stem,workers=4,numerical_threads=1,memory_bytes_per_task=1024**3,
        source_bytes_per_task=128*1024**2,output_bytes_per_task=64*1024**2,confirmation_selection_path=settings)
    originals=SimpleNamespace(writer=writer,package=f.package,bindings=f.inputs.original_products,profile=profile)
    monkeypatch.setattr(held,"original_preparation",lambda value:f.inputs.original_preparation if value is originals else pytest.fail("foreign original"))
    public_calibration=calibration_product=None
    if phase=="CONF":
        cr,cd=fixture_observations(programmes["CAL"],banks["CAL"],revision=export)
        forecasts=p.SelectedE4ForecastBank("forecasts."+stem,programmes["CAL"].identity,tuple(value.revision_seal for value in cr.cases))
        cs=p.SelectedE4CalibrationSpecification("calibration-spec."+stem,development.identity,programmes["CAL"].identity,
            nomination.identity,frozen.identity,D(".05"),p.SCORE_RULE)
        calibration=science.calibrate_revision_public(cs,export,programmes["CAL"],banks["CAL"],cr,cd,forecasts,record_id="calibration."+stem)
        public_calibration=p.SelectedE4PublicCalibration.from_calibration(calibration,record_id="public-calibration."+stem)
        prior=prior_product(calibration.identity)
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
        calibration_product=MatrixSelectedOriginalProduct(prior.prior_execution,prior.reveal_authority)
    destination=selected_root/stem
    original_root_bytes=f.inputs.original_preparation.root.canonical_bytes()
    from tests.test_matrix_selected_e3_e4_bridge import disclosed_produced_parents
    disclosed_parents=disclosed_produced_parents((*originals.bindings,
        *((calibration_product,) if calibration_product is not None else ())),
        development=(products.nomination_locator,products.frozen_locator))
    from tests.matrix_e4_structure_support import publish_secondary
    target,secondary=publish_secondary(writer,banks["DEV"],selected_root/(stem+".early-secondary"))
    plan,publication=held.protected_plan(originals,SimpleNamespace(programmes=programmes,banks=banks,
        secondary_target=target,secondary_readout=secondary),selected,
        label=phase,products=products,predecessor=SimpleNamespace(source=source),directory=destination,
        public_calibration=public_calibration,calibration_product=calibration_product,
        disclosed_parent_metadata=(disclosed_produced_parents(originals.bindings),disclosed_parents))
    plan=_active_e4_formal_plan(plan)
    from empirical_lawhood.api.selected_e4_declarative import expected_declaration_publication
    publication=expected_declaration_publication(writer,destination,plan.declaration)
    assert decode_canonical_bytes(plan.canonical_bytes(),type(plan),maximum_bytes=None)==plan
    phase_root=plan.declaration.root
    support=phase_root.experiment.obligations.support
    assert support.physical_unit_count==len(programme.group_ids)==protected_groups
    assert support.denominator_cell_ids==tuple(sorted(value.root_id for value in programme.cases))
    assert support.information_cutoff_id in {value.cutoff_id for value in phase_root.experiment.information_cutoffs}
    assert not support.evidence_link_ids
    assert phase_root.experiment.obligations.uncertainty.confidence_level==programme.design.confidence
    assert all(value.requested_rung is None and value.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
        and not value.derivation_parent_ids and not value.parent_visibility_ceilings for value in phase_root.experiment.claims)
    assert f.inputs.original_preparation.root.canonical_bytes()==original_root_bytes
    collection=None;observations=()
    if component=="assessment":
        observed,_=fixture_observations(programme,bank,revision=export)
        observations=tuple(r.SelectedE4WaveObservation("observation."+wave.wave_id,plan.declaration.identity,wave.wave_id,
            pin("plan."+wave.wave_id,ExecutionPlan),pin("terminal."+wave.wave_id,RunRecoveryTerminalEvent),
            tuple(value for value in observed.cases if value.root_id in wave.root_ids),()) for wave in programme.waves)
        rows=[]
        for wave,observation in zip(programme.waves,observations,strict=True):
            location=r.SelectedE4WaveLocator(wave.wave_id,"run."+wave.wave_id,pin("package."+wave.wave_id,ExperimentPackage),
                pin("issued."+wave.wave_id,IssuedExecutableStudyManifest),pin("execution."+wave.wave_id,StudyOperationAuthority),pin("reveal."+wave.wave_id,StudyOperationAuthority),observation.execution_plan)
            rows.append(r.SelectedE4WaveInput(location,observation.identity,len(observation.canonical_bytes())))
        evidence=r.SelectedE4PhaseCollectionEvidence("collection-evidence."+stem,plan.declaration.identity,tuple(rows))
        artifacts=tuple(ArtifactIdentity(value.record_id,"disclosed-unissued-observation",value.SCHEMA,value.fingerprint(),"application/json",len(value.canonical_bytes())) for value in observations)
        collection=preparation_owner.SelectedE4PhaseCollectionSelection("collection."+stem,evidence,artifacts,(),())
    component_id=preparation_owner.ASSESSMENT_COMPONENT_ID if collection is not None else selected_wave.wave_id
    component_spec=preparation_owner.component_specification(plan,component_id)
    component_allocation=preparation_owner.programme_allocation(plan,
        group_ids=programme.group_ids if collection is not None else selected_wave.group_ids)
    assert old.identity(bank.reservation.allocation) in component_allocation.sources
    assert {unit.source_id for unit in component_allocation.units}=={bank.reservation.allocation.allocation_id}
    inputs=preparation_owner.ResolvedSelectedE4ComponentInputs(plan,component_id,publication,collection)
    draft,records,arrays=preparation_owner.component_source_operands(component_spec,inputs)
    # The declaration contains fitted producer operands. Its exact inherited
    # custody is mandatory even in this disclosed, unissued structural proof.
    entry_operation=next(value for value in draft.operations
        if value.config_identity.object_schema==owner.SelectedE4ProtectedEntryConfig.SCHEMA)
    entry=decode_canonical_bytes(entry_operation.config_payload.encode(),owner.SelectedE4ProtectedEntryConfig,
        maximum_bytes=None)
    assert entry.declaration_publication.logical.lineage_parents==plan.evidence.produced_input_parents
    assert entry.declaration_publication.logical.outcome_access is not r.BLIND
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import _publication
    with pytest.raises(ValueError,match="blind prospective"):
        _publication(entry.declaration_publication,entry.declaration)
    for damage in ("blind","missing-parent","different-body"):
        damaged_publication=entry.declaration_publication
        with pytest.raises(ValueError):
            if damage=="blind":
                damaged_publication=replace(damaged_publication,logical=replace(damaged_publication.logical,
                    outcome_access=r.BLIND,visibility_ceiling=r.PROSPECTIVE))
            elif damage=="missing-parent":
                parents=damaged_publication.logical.lineage_parents[:-1]
                damaged_publication=replace(damaged_publication,logical=replace(damaged_publication.logical,lineage_parents=parents,
                    parent_visibility_ceilings=tuple(value.visibility_ceiling for value in parents)))
            else:
                damaged_publication=replace(damaged_publication,materialization=replace(damaged_publication.materialization,
                    physical_sha256="f"*64))
            replace(entry,declaration_publication=damaged_publication)
    wave_inputs=tuple(value for value in draft.external_inputs
        if value.payload_schema==r.SelectedE4WaveObservation.SCHEMA)
    if component=="assessment":
        assert wave_inputs and all(value.scientific_role=="HISTORY" and value.outcome_access is r.SEALED
            for value in wave_inputs)
        wave_ids={value.input_id for value in wave_inputs}
        assert all(value.scientific_role=="HISTORY" for value in draft.links
            if value.external_input_id in wave_ids)
    else:
        assert not wave_inputs
    if component=="wave":
        from dataclasses import fields
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_execution import phase_config
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import bind_selected_native_source

        # Inspect the actual public lowering over the already constructed small
        # fixture. No extra fit, source read, native task or authority is added.
        kinds={kind.SCHEMA:kind for kind in (
            owner.SelectedE4ProtectedProtocolConfig,owner.SelectedE4ProtectedProtocolPublicConfig)}
        leaves=tuple((operation,decode_canonical_bytes(operation.config_payload.encode(),
            kinds[operation.config_identity.object_schema],maximum_bytes=None)) for operation in draft.operations
            if operation.config_identity.object_schema in kinds)
        assert leaves and all(config.models==export.models.identity for _,config in leaves)
        model_inputs=tuple(value for value in draft.external_inputs if value.payload_schema==p.SelectedE4PublicModels.SCHEMA)
        shared,=model_inputs
        assert shared.expected_content_sha256==export.models.fingerprint()
        assert shared.maximum_size_bytes==len(export.models.canonical_bytes())
        assert shared.outcome_access is r.BLIND and shared.visibility_ceiling is r.PROSPECTIVE
        assert dict(records)[shared.input_id]==export.models
        model_links=tuple(value for value in draft.links if value.external_input_id==shared.input_id)
        assert {value.consumer_node_id for value in model_links}=={operation.node_id for operation,_ in leaves}
        assert all(value.consumer_input_id=="models" for value in model_links)
        compact=tuple(config for _,config in leaves if type(config) is owner.SelectedE4ProtectedProtocolConfig)
        wave=selected_wave
        assert {config.source.root_id for config in compact}==set(wave.root_ids)
        assert {config.source.root.root.independent_group_id for config in compact}==set(wave.group_ids)
        assert plan.declaration.programme.group_ids==programme.group_ids
        for _,config in leaves:
            assert decode_canonical_bytes(config.canonical_bytes(),type(config),maximum_bytes=None)==config
        wire=next(config for config in compact if config.phase=="prefix")
        bound=owner.bind_selected_e4_models(wire,export.models)
        assert owner.wire_config(bound) is wire and bound.models is export.models
        original_protocol=next(value for value in bank.response_selection.protocols
            if value.public_source.root.root_id==wire.source.root_id)
        assert type(wire.protocol) is owner.SelectedE4ProtocolBody
        assert bound.protocol==owner.protocol_for_config(wire)==original_protocol
        assert bound.protocol.canonical_bytes()==original_protocol.canonical_bytes()
        assert wire.protocol.original==ObjectIdentity.from_record(original_protocol.protocol_id,original_protocol)
        assert len(wire.protocol.canonical_bytes())<len(original_protocol.canonical_bytes())
        assert "public_source" not in {field.name for field in fields(type(wire.protocol))}
        assert original_protocol.fingerprint() in owner.digests(wire)
        altered_pin=replace(wire.protocol.original,object_fingerprint="0"*64)
        with pytest.raises(ValueError,match="original source or assay bytes"):
            replace(wire,protocol=replace(wire.protocol,original=altered_pin))
        with pytest.raises((TypeError,ValueError)):
            replace(wire,protocol=replace(wire.protocol,receiver_count=0))
        native_source=bind_selected_native_source(wire.source,next(value for value in bank.provenances
            if value.identity==wire.source.provenance))
        assert owner.native_contract(bound,native_source)[0]==ObjectIdentity.from_record(wire.config_id,wire)
        continued=phase_config(bound,"continue")
        continued_wire=owner.wire_config(continued)
        assert continued.models is export.models and continued_wire.models==export.models.identity
        assert type(continued_wire) is owner.SelectedE4ProtectedProtocolConfig
        assert continued.protocol==original_protocol
        assert (continued_wire.phase,continued_wire.config_id)==("continue","config."+owner.local_node(native_source.root_id,"continue"))
        assert owner.native_contract(continued,native_source)[0]==ObjectIdentity.from_record(continued_wire.config_id,continued_wire)
        parameters=export.models.revision_model.parameters[0]
        altered_parameters=replace(parameters,coefficients=(parameters.coefficients[0]+D(1),*parameters.coefficients[1:]))
        altered=replace(export.models,revision_model=replace(export.models.revision_model,
            parameters=(altered_parameters,*export.models.revision_model.parameters[1:])))
        with pytest.raises((TypeError,ValueError)):
            owner.bind_selected_e4_models(wire,altered)
        legacy=owner.SelectedE4ProtectedCompactConfig(**{
            field.name:export.models if field.name=="models" else getattr(bound,field.name)
            for field in fields(owner.SelectedE4ProtectedCompactConfig)})
        legacy_raw=legacy.canonical_bytes()
        assert owner.wire_config(legacy) is legacy
        assert owner.native_contract(legacy,native_source)[0]==ObjectIdentity.from_record(legacy.config_id,legacy)
        assert decode_canonical_bytes(legacy_raw,type(legacy),maximum_bytes=None)==legacy
        assert legacy.canonical_bytes()==legacy_raw
        referenced=owner.SelectedE4ProtectedReferencedConfig(**{
            field.name:wire.models if field.name=="models" else getattr(legacy,field.name)
            for field in fields(owner.SelectedE4ProtectedReferencedConfig)})
        referenced_raw=referenced.canonical_bytes()
        assert decode_canonical_bytes(referenced_raw,type(referenced),maximum_bytes=None)==referenced
        assert owner.bind_selected_e4_models(referenced,export.models).protocol==original_protocol
        assert owner.declaration_for_config(referenced).capability_key==owner.key_for_phase("prefix",referenced=True)
        assert owner.declaration_for_config(wire).capability_key==owner.key_for_phase("prefix",referenced=True,compact_protocol=True)
        if phase=="CONF":
            public_wire=next(config for _,config in leaves if type(config) is owner.SelectedE4ProtectedProtocolPublicConfig)
            unentered=replace(export.decision,trigger_disposition="NOT_TRIGGERED",frozen_disposition="UNENTERED",
                revision_model=None,baseline_model=None)
            ordinary=owner.SelectedE4ProtectedPublicConfig(**{
                field.name:None if field.name in ("models","calibration") else unentered if field.name=="decision"
                else owner.protocol_for_config(public_wire) if field.name=="protocol"
                else getattr(public_wire,field.name) for field in fields(owner.SelectedE4ProtectedPublicConfig)})
            raw=ordinary.canonical_bytes()
            assert owner.wire_config(ordinary) is ordinary and ordinary.models is None
            assert decode_canonical_bytes(raw,type(ordinary),maximum_bytes=None)==ordinary
            assert ordinary.canonical_bytes()==raw

        # A warm pure-data projection must retain the active Decimal contract.
        # Reuse this existing small typed bank; no extra population or fit.
        from decimal import Inexact, Rounded, localcontext
        contract_args=(programme,bank,plan.evidence.identity,len(plan.evidence.canonical_bytes()),
            plan.declaration.decision,plan.declaration.models,plan.declaration.calibration,
            plan.declaration,publication,component_id)
        for function,arguments,keywords in ((p.validate_selected_phase_bank,(programme,bank),{}),
                (owner.contracts,contract_args,{'secondary_readout':plan.secondary_readout})):
            function(*arguments,**keywords)
            with localcontext() as decimal_context:
                decimal_context.prec=1
                decimal_context.traps[Inexact]=False
                decimal_context.traps[Rounded]=True
                with pytest.raises(Rounded):
                    function.__wrapped__(*arguments,**keywords)
                misses=function.cache_info().misses
                with pytest.raises(Rounded):
                    function(*arguments,**keywords)
                assert function.cache_info().misses==misses+1
        views=tuple(sorted({view.view_id for config in compact
            for view in (config.source.coordinate.primary_view,config.source.coordinate.fine_view)}))
        scoped=r.wave_root(plan.declaration,component_id,views=views)
        assert r.wave_root(plan.declaration,component_id,views=views) is scoped
        assert r.wave_root.__wrapped__(plan.declaration,component_id,views=views).canonical_bytes()==scoped.canonical_bytes()
        with localcontext() as decimal_context:
            decimal_context.prec+=1
            misses=r.wave_root.cache_info().misses
            assert r.wave_root(plan.declaration,component_id,views=views).canonical_bytes()==scoped.canonical_bytes()
            assert r.wave_root.cache_info().misses==misses+1
    if collection is not None:
        records=_wave_observation_records(draft,records,observations)
        configs,qualifications=held._source_admissions(draft,records,arrays,root=draft.prospective_draft,prefix=stem,
            observation_operator=source.pipeline.pipeline_config.profile.observation_operator)
        from empirical_lawhood.planning.study_authoring import SourceMaterializationRole
        assert all(value.role is SourceMaterializationRole.RETAINED_HISTORY for value in configs
            if value.source_id in wave_ids)
        collection=replace(collection,source_configs=configs,qualifications=qualifications)
        inputs=replace(inputs,collection=collection)
        parent_configs={value.source_id:value for value in plan.preparation.source_configs}
        wanted={value.input_id for value in draft.external_inputs}
        overlap=next(value for value in collection.source_configs
            if value.source_id in wanted and parent_configs.get(value.source_id)==value)
        conflicting=replace(collection,source_configs=tuple(
            replace(value,config_id=value.config_id+".conflict") if value.source_id==overlap.source_id else value
            for value in collection.source_configs))
        with pytest.raises(ValueError,match="conflict"):
            preparation_owner.component_design(component_spec,replace(inputs,collection=conflicting))
    handles=[]
    records=dict(records)
    all_files=dict(arrays)
    if collection is not None:
        all_files.update((external.input_id,next(artifact for artifact in collection.observations if artifact.artifact_id==external.logical_artifact_id))
            for external in draft.external_inputs if external.payload_schema==r.SelectedE4WaveObservation.SCHEMA)
    for key,artifact in all_files.items():
        if artifact.payload_schema==r.SelectedE4WaveObservation.SCHEMA:
            value=records[key];path=selected_root/(artifact.sha256+".observation.json");path.write_bytes(value.canonical_bytes())
        else:path=writer.root.resolve(f.inputs.template_publication.materialization.relative_path,for_write=False)
        handles.append((key,PreparedExperimentFile(artifact,"1.0.0",path,artifact.size_bytes)))
    implementation=capture_target_closure(held.ROOT,"prospective."+component_spec.specification_id+".source-closure").closure
    execution=ExecutionSelection(workers=4,environment_id="main-locked",source_snapshot=ObjectIdentity.from_record("recursive-member.implementation",implementation),output_root=str(selected_root))
    parent_entry_bytes=plan.preparation.entry.canonical_bytes()
    parent_inventories_bytes=tuple(value.canonical_bytes() for value in plan.preparation.formal_source_inventories)
    plan_publication=public._publish(writer,destination,public.PLAN_FILENAME,plan,lineage_parents=plan.evidence.produced_input_parents)
    declaration_publication=public._publish(writer,destination,"native-declaration.json",plan.declaration,lineage_parents=plan.evidence.produced_input_parents)
    assert (declaration_publication.logical,declaration_publication.materialization,
        declaration_publication.manifest_materialization)==(publication.logical,publication.materialization,
        publication.manifest_materialization)
    selection=preparation_owner.SelectedE4NativeComponentInputs("inputs."+stem,plan.identity,
        plan_publication,plan.evidence.upstream_products,plan.evidence.calibration_product,component_id,declaration_publication,collection)
    resolved=preparation_owner.resolve_component_inputs(selection,plan)
    assert resolved==inputs
    assert decode_canonical_bytes(selection.canonical_bytes(),type(selection),maximum_bytes=None)==selection
    assert selection.to_document()["value"]["plan"]==plan.identity.to_document()
    assert selection.upstream_products==plan.evidence.upstream_products
    assert selection.calibration_product==plan.evidence.calibration_product
    assert selection.plan_publication.logical.lineage_parents==plan.evidence.produced_input_parents
    with pytest.raises(TypeError,match='original E3'):
        replace(selection,upstream_products=selection.upstream_products[:-1])
    assert "preparation" not in selection.to_document()["value"]
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    obsolete=selection.to_document()
    obsolete["version"]="1.0.0"
    obsolete["value"]["plan"]=plan.to_document()
    obsolete["value"].pop("plan_publication")
    obsolete["value"].pop("component_id")
    with pytest.raises(ValueError):
        decode_canonical_bytes(canonical_json_document_bytes(obsolete),type(selection),maximum_bytes=None)
    for wave in programme.waves:
        reference=replace(selection,component_id=wave.wave_id,collection=None)
        assert reference.plan_publication==plan_publication and reference.plan==plan.identity
        assert len(reference.canonical_bytes())<len(plan.canonical_bytes())
    source_path=destination/"component-inputs.json"
    source_path.write_bytes(selection.canonical_bytes())
    selector=ExperimentFileInputSelection("selection."+stem,preparation_owner.COMPONENT_PROTOCOL_ID,
        (ExperimentInputBinding("inputs",selection.identity,source_path.relative_to(selected_root).as_posix(),len(selection.canonical_bytes())),
         ExperimentInputBinding("plan",plan.identity,plan_publication.materialization.relative_path,len(plan.canonical_bytes()))),
        tuple(ExperimentFileInputBinding(key,handle.identity,handle.record_version,
            handle.path.relative_to(selected_root).as_posix(),handle.maximum_bytes) for key,handle in sorted(handles)))
    selector_path=selected_root/(stem+".component-sources.json")
    selector_path.write_bytes(selector.canonical_bytes())
    bound=load_experiment_inputs(component_spec,selector_path)
    assert bound.method_inputs.selection==selection and bound.method_inputs.resolved==resolved
    assert bound.scientific_inputs=={bank.phase.lower():component_allocation}
    prepared=preparation_owner.prepare_component(component_spec,
        scientific_inputs=bound.scientific_inputs,method_inputs=bound.method_inputs,execution=execution)
    assert prepared.executable
    assert prepared.design_records==((selection.record_id,selection),)
    with pytest.raises(ValueError,match="resolved published plan"):
        preparation_owner.validate_component_instance(specification=component_spec,allocation=prepared.allocation,
            draft=prepared.draft,source_records=prepared.design_records)
    from empirical_lawhood.api.selected_e4_native_preparation import authenticate_selected_e4_component_instance
    with pytest.raises(ValueError,match="source key"):
        authenticate_selected_e4_component_instance(specification=component_spec,allocation=prepared.allocation,
            draft=prepared.draft,source_records=(("foreign.source-key",selection),),artifact_writer=writer)
    # These declared producer locators are unsigned. Actual custody must refuse
    # before any authoring, issue or worker contact; typed structure is no grant.
    missing_package=writer.root.resolve("runs/run.exposed/plans/campaign-package.json.manifest.json",for_write=False)
    assert not missing_package.exists()
    with pytest.raises(FileNotFoundError) as refused:
        authenticate_selected_e4_component_instance(specification=component_spec,allocation=prepared.allocation,
            draft=prepared.draft,source_records=prepared.design_records,artifact_writer=writer)
    assert Path(refused.value.filename)==missing_package
    assert {key for key,_ in prepared.input_records}|{key for key,_ in prepared.input_files}=={
        value.input_id for value in prepared.draft.external_inputs}
    def forbidden(*args,**kwargs):pytest.fail("unsigned structural control entered issue or worker execution")
    monkeypatch.setattr(EmpiricalLawhoodApi,"issue_study",forbidden)
    monkeypatch.setattr(EmpiricalLawhoodApi,"issue_extensions",forbidden)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_protected_workers import SelectedE4ProtectedWorker
    monkeypatch.setattr(SelectedE4ProtectedWorker,"execute",forbidden)
    monkeypatch.setattr(methods.SelectedE4MethodWorker,"execute",forbidden)
    directory=destination/"authored-component"
    with pytest.raises(FileNotFoundError) as refused:
        author_prepared_experiment(preparation=prepared,project_root=held.ROOT,artifact_writer=writer,output_dir=directory)
    assert Path(refused.value.filename)==missing_package
    assert not directory.exists()
    # Formal structure can be checked from the pure component projection. It
    # does not require claiming a prospective handoff from unsigned originals.
    _,_,_,design,_=preparation_owner.component_design(component_spec,inputs)
    from empirical_lawhood.planning.formal_analysis import derive_formal_gap_applicability
    from empirical_lawhood.planning.experiment_entry import validate_experiment_entry
    local_root=design.draft.prospective_draft
    local_entry=design.entry_package
    local_inventory,=design.formal_source_inventories
    parent_inventory,=plan.preparation.formal_source_inventories
    validate_experiment_entry(local_root,local_entry,for_issue=False)
    assert local_entry.coverage.candidate_act_id==local_root.draft_id
    assert local_entry.checklist.draft==r.pin(local_root,"draft_id")
    assert local_entry.checklist.formal_gap_coverage==r.pin(local_entry.coverage,"coverage_id")
    assert local_inventory.source_materializations==tuple(sorted(
        (value.materialization for value in local_root.source_materializations),key=lambda value:value.object_id))
    assert local_inventory.independent_unit_ids==tuple(value for value in parent_inventory.independent_unit_ids
        if value in {*local_root.development_unit_ids,*local_root.evaluation_unit_ids})
    assert local_inventory.numerical_view_ids==tuple(value for value in parent_inventory.numerical_view_ids
        if value in {view.view_id for view in local_root.system.numerical_views})
    assert local_entry.coverage.applicability==derive_formal_gap_applicability(local_entry.register,local_inventory)
    from empirical_lawhood.planning.formal_gaps import FormalGapCoverageDisposition
    assert local_entry.register.canonical_bytes()==plan.preparation.entry.register.canonical_bytes()
    assert all(value.minimum_independent_units==len(programme.group_ids) for value in local_entry.register.gaps)
    if component=="wave":
        assert len(local_inventory.independent_unit_ids)==4<len(parent_inventory.independent_unit_ids)==20
        assert tuple(len(value.group_ids) for value in programme.waves)==(8,8,4)
        assert all(value.disposition is FormalGapCoverageDisposition.DEFER_WITH_TYPED_PREREQUISITE
            and value.reason_codes==("E4_WHOLE_PHASE_ASSESSMENT_REQUIRES_ALL_WAVES",)
            for value in local_entry.coverage.assignments)
        assert not local_inventory.available_estimator_family_ids and not local_inventory.multiplicity_family_ids
    else:
        actual=methods.method_node(programme.identity,"revision-calibrate" if phase=="CAL" else "confirmation-assess")
        assert local_inventory.independent_unit_ids==programme.group_ids
        assert all(value.disposition is FormalGapCoverageDisposition.TEST_IN_THIS_ACT
            and value.adjudication_owner_ids==(actual,) and value.output_ids==("product",)
            for value in local_entry.coverage.assignments)
        assert tuple((value.selected_estimator_family_id,value.selected_multiplicity_family_id,value.obligation_ids)
            for value in local_entry.coverage.assignments)==tuple((value.selected_estimator_family_id,
                value.selected_multiplicity_family_id,value.obligation_ids) for value in plan.preparation.entry.coverage.assignments)
    assert local_entry.checklist.bindings==plan.preparation.entry.checklist.bindings
    assert plan.preparation.entry.canonical_bytes()==parent_entry_bytes
    assert tuple(value.canonical_bytes() for value in plan.preparation.formal_source_inventories)==parent_inventories_bytes


def _active_e4_formal_plan(plan):
    """Explicit actual E4 method families; disclosed conformance inputs only."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as preparation
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
    from empirical_lawhood.kernel.evidence import EvidenceCeiling,OutcomeAccess
    from empirical_lawhood.kernel.worlds import EvidenceUnitScope
    from empirical_lawhood.planning.formal_analysis import (
        FormalGapSourceCapabilityInventory,FormalMethodBinding,FormalMethodCatalog,FormalMethodRole,derive_formal_gap_applicability,
    )
    from empirical_lawhood.planning.formal_gaps import (
        FormalDomain,FormalGapCoverage,FormalGapCoverageAssignment,FormalGapCoverageDisposition,
        FormalGapRegister,FormalGapSpec,
    )
    root=plan.declaration.root
    phase=plan.declaration.bank_phase
    prefix="e4-formal.disclosed."+phase.lower()
    operation="revision-calibrate" if phase=="CALIBRATION" else "confirmation-assess"
    declaration=next(value for value in methods.operation_declarations()
        if value.capability_key==methods.NAMESPACE+"."+operation)
    manifest=declaration.manifest()
    estimator=prefix+".whole-group-"+operation
    uncertainty=prefix+".frozen-family-"+operation
    controls=tuple(value.control_id for value in root.experiment.controls)
    gaps=tuple(FormalGapSpec(prefix+".gap."+domain.value.lower(),domain,
        "Declared finite E4 "+operation+" "+domain.value.lower()+" over the complete frozen physical-group roster",
        (plan.bank.identity.object_id,),(plan.preparation.entry.checklist.portfolio_world,),len(plan.declaration.programme.group_ids),
        len(root.system.numerical_views),(estimator,),controls,(prefix+".falsifier",),(prefix+".fixed-roster",),uncertainty,
        EvidenceCeiling.RESPONSE,(plan.bank.identity.object_id,)) for domain in FormalDomain)
    register=FormalGapRegister(prefix+".register","1.0.0",(plan.bank.identity,),
        tuple(sorted(gaps,key=lambda value:value.gap_id)))
    inventory=FormalGapSourceCapabilityInventory(prefix+".inventory",root.system.system_id,
        plan.preparation.entry.checklist.portfolio_world,plan.preparation.formal_source_inventories[0].source_materializations,
        (plan.bank.identity.object_id,),(prefix+".fixed-roster",),plan.declaration.programme.group_ids,
        EvidenceUnitScope.PHYSICAL_INDEPENDENT_UNIT,tuple(value.view_id for value in root.system.numerical_views),
        (estimator,),controls,(uncertainty,),(),(),EvidenceCeiling.RESPONSE,OutcomeAccess.OUTCOME_BLIND)
    catalog=FormalMethodCatalog(prefix+".catalog",tuple(sorted((FormalMethodBinding(family,role,
        manifest.capability_key,manifest.capability_version,manifest.implementation_sha256,
        tuple(value.gap_id for value in register.gaps),declaration.config_record_type.SCHEMA,
        methods.output_types(operation)["product"].SCHEMA,EvidenceCeiling.RESPONSE,OutcomeAccess.EVALUATOR_REVEAL)
        for family,role in ((estimator,FormalMethodRole.ESTIMATOR),(uncertainty,FormalMethodRole.MULTIPLICITY))),
        key=lambda value:value.binding_id)))
    assignments=tuple(FormalGapCoverageAssignment(value.gap_id,FormalGapCoverageDisposition.TEST_IN_THIS_ACT,None,(),
        estimator,controls,uncertainty,(root.experiment.obligations.uncertainty.uncertainty_id,),
        ("old-component.product",),("old-component.node",)) for value in register.gaps)
    coverage=FormalGapCoverage(prefix+".coverage",r.pin(register,"register_id"),root.system.system_id,root.draft_id,
        derive_formal_gap_applicability(register,inventory),assignments,OutcomeAccess.OUTCOME_BLIND)
    entry=replace(plan.preparation.entry,register=register,coverage=coverage,
        checklist=replace(plan.preparation.entry.checklist,formal_gap_register=r.pin(register,"register_id"),
            formal_gap_coverage=r.pin(coverage,"coverage_id")))
    preparation.validate_component_formal_selection(root,entry,catalog,phase)
    # Exact declared implementation/schema/obligation ownership is required
    # before any issue/native execution. Rebinding a node cannot fix these.
    for change in ("digest","capability","input-schema","output-schema"):
        first=catalog.bindings[0]
        if change=="digest":first=replace(first,implementation_sha256="0"*64)
        elif change=="capability":first=replace(first,capability_key="matrix-e3-configured-protected.assess")
        elif change=="input-schema":first=replace(first,input_schema_id="empirical-lawhood/wrong-input")
        else:first=replace(first,output_schema_id="empirical-lawhood/wrong-output")
        hostile=replace(catalog,bindings=(first,*catalog.bindings[1:]))
        with pytest.raises(ValueError,match="exact declared current"):
            preparation.validate_component_formal_selection(root,entry,hostile,phase)
    wrong=replace(coverage,assignments=tuple(replace(value,obligation_ids=("e3.single-terminal",))
        for value in coverage.assignments))
    hostile=replace(entry,coverage=wrong,checklist=replace(entry.checklist,formal_gap_coverage=r.pin(wrong,"coverage_id")))
    with pytest.raises(ValueError,match="actual whole-phase scientific contracts"):
        preparation.validate_component_formal_selection(root,hostile,catalog,phase)
    current=preparation.SelectedE4ProgrammePreparationSelectionV2(
        plan.preparation.record_id,entry,catalog,(inventory,),plan.preparation.qualifications,
        plan.preparation.source_configs,plan.preparation.resources)
    return replace(plan,preparation=current)
