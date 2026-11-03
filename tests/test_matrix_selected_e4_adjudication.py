# SPDX-License-Identifier: MPL-2.0
"""Disclosed prepared E4 evaluator controls; no authority, fitting or native work.

All original coefficients, receipts and reveal contexts below are literals.
These tests establish transport/refusal behavior, never scientific qualification.
"""
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as native
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as records
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as public
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_selection as selection
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as e3bridge
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationContext, ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactProfile, LogicalArtifactIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.experimental_statistics import StandardizedRidgeParameters, calibration_rank
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeInputContract, PreparedWorkerEnvironment
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.test_matrix_selected_protected_worker import MemoryReader
from tests.test_matrix_selected_e4_fixtures import selected_e4_populations, selected_bridge, transfer  # noqa: F401


def _pin(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, sha256(name.encode()).hexdigest())


@pytest.fixture(scope="module")
def adjudication_literals(selected_e4_populations):  # noqa: F811
    f=selected_e4_populations
    programme, bank=f.calibration, f.calibration_bank
    wave=programme.waves[0]
    cases=tuple(value for value in programme.cases if value.root_id in wave.root_ids)
    decision=_pin("decision.disclosed-adjudication", public.SelectedE4PublicRevisionDecision)
    def entry(groups, selected_cases, *, wave_id, wave_evidence):
        return records.SelectedE4ProtectedEntrySeal("entry.disclosed-adjudication."+(wave_id or "complete"),
            programme.identity, bank.identity, programme.forecast_design,
            _pin("evidence.disclosed-adjudication", records.SelectedE4ProtectedEvidence), groups,
            tuple(value.source for value in selected_cases), "CALIBRATION", wave_id, wave_evidence, decision, None, None, secondary_readout=f.secondary_readout.identity)
    rows=[]
    index=bank.source_index()
    for case in cases:
        absent=e3bridge.SelectedE3E4CaseResult.unentered(case)
        rows.append(records.SelectedE4NativeCaseResult(case.root_id, case.source, case.independent_group_id,
            absent.disposition, absent.numerical_disposition, absent.score_disposition,
            absent.paired_log_targets, absent.original_log_points, None, None, None, (), absent.native,
            absent.reason_codes, None, None, None,bank.source(case.root_id,index=index).coordinate))
    reduction=records.SelectedE4NativeReduction("reduction.disclosed-adjudication", programme.identity,
        bank.identity, tuple(rows), wave.group_ids, wave.wave_id)
    config=native.SelectedE4ProtectedReduceConfig("config."+native.global_node(programme,"adjudicate",wave.wave_id),
        programme, bank.identity, wave.wave_id, phase="adjudicate")
    wave_values={"entry":entry(wave.group_ids,cases,wave_id=wave.wave_id,wave_evidence=None), "reduction":reduction}
    wave_producers={"entry":native.global_node(programme,"entry",wave.wave_id),
        "reduction":native.global_node(programme,"reduce",wave.wave_id)}
    wave_declaration=next(value for value in native.operation_declarations() if value.capability_key.endswith(".adjudicate"))
    tuning=selection.ScheduledRevisionTuning("tuning.disclosed-adjudication",selection.FAMILY,
        tuple(sorted(selection.PHYSICAL)),D(1),False,4)
    parameters=StandardizedRidgeParameters((D(0),)*3,(D(1),)*3,(False,)*3,(D(0),)*4,9,9)
    models=tuple(selection.ScheduledRevisionFittedModel("model.disclosed-adjudication."+name,
        "candidate.disclosed-adjudication."+name,tuning,("group.disclosed-training",),(parameters,)*30)
        for name in ("revision","baseline"))
    specification=public.SelectedE4CalibrationSpecification("calibration.disclosed-adjudication",
        f.development.identity, programme.identity, _pin("nomination.disclosed-adjudication",science.SelectedE4RevisionNomination),
        _pin("frozen.disclosed-adjudication",science.SelectedE4FrozenRevision),D(".05"),public.SCORE_RULE)
    scores=tuple((group,D(0)) for group in programme.group_ids)
    calibration=science.SelectedE4Calibration("calibration-result.disclosed-adjudication",specification,
        _pin("target.disclosed-adjudication",selection.ScheduledRevisionTarget),*models,programme.group_ids,scores,scores,
        calibration_rank(len(scores),specification.alpha),D(0),D(0),
        _pin("observations.disclosed-adjudication",public.SelectedE4ObservedData),
        tuple(_pin("forecast.disclosed-adjudication."+case.root_id,public.SelectedE4ForecastSeal) for case in programme.cases))
    entry_node=native.global_node(programme,"phase-entry")
    calibration_node=methods.method_node(programme.identity,"revision-calibrate")
    node=methods.method_node(programme.identity,"revision-adjudicate")
    links=tuple(RecursiveInputLink("edge.disclosed-adjudication."+name,node,name,
        producer_node_id=producer,producer_output_id="product" if producer else None,
        external_input_id="external.programme" if producer is None else None,scientific_role="HISTORY" if producer else "SOURCE")
        for name,producer in (("calibration",calibration_node),("entry",entry_node),("programme",None)))
    budget=ResourceBudget(1,1024**2,0,None,1024**2,1024**2)
    cal_config=methods.SelectedE4MethodConfig("config."+node,"revision-adjudicate",programme.identity,
        programme.group_ids,(("programme",programme.identity),),links,budget,entry_node)
    cal_values={"programme":programme,"calibration":calibration,
        "entry":entry(programme.group_ids,programme.cases,wave_id=None,
            wave_evidence=_pin("wave-evidence.disclosed-adjudication",records.SelectedE4PhaseCollectionEvidence))}
    cal_producers={"entry":entry_node,"calibration":calibration_node}
    cal_declaration=next(value for value in methods.operation_declarations() if value.capability_key.endswith(".revision-adjudicate"))
    return {"wave":(wave_declaration,config,wave_values,wave_producers),
        "calibration":(cal_declaration,cal_config,cal_values,cal_producers)}


class GuardedReader(MemoryReader):
    def cursor(self):
        raise AssertionError("protected payload read before adjudication guard")


def _prepared(literals, *, authority=True, output=True, forbid_reads=False):
    declaration, config, values, producers=literals
    manifest=declaration.manifest()
    task_id=config.config_id.removeprefix("config.")
    budget=getattr(config,"operational_budget",native.BUDGET)
    ports, contracts, external, edges, receipt_materials=[],[],[],[],{}
    for name,value in sorted({"automatic":config,**values}.items()):
        raw=value.canonical_bytes(); digest=sha256(raw).hexdigest()
        lane=Access.EVALUATION_SEALED if name in ("reduction","calibration") else Access.OUTCOME_BLIND
        artifact_id = config.config_id if name == 'automatic' else 'artifact.' + name
        logical=LogicalArtifactIdentity(artifact_id,digest,value.SCHEMA,ArtifactProfile.CANONICAL_JSON,
            "application/json",Visibility.PROSPECTIVE,(),lane,
            ArtifactGenericValidation("validator.disclosed-adjudication","1.0.0","1"*64,value.SCHEMA,ArtifactProfile.CANONICAL_JSON))
        producer=producers.get(name)
        binding=WorkerInputBinding(logical.logical_artifact_id,"material."+name,value.SCHEMA,"application/json",len(raw),
            Visibility.PROSPECTIVE,lane,WorkerInputKind.DEPENDENCY if producer else WorkerInputKind.EXTERNAL)
        ports.append(WorkerInputPort(binding,(GuardedReader if forbid_reads else MemoryReader)(raw)))
        contracts.append(PreparedNativeInputContract(logical,binding,digest))
        if producer:receipt_materials.setdefault(producer,[]).append(binding.materialization_id)
        else:external.append(ExternalInputSpec('config' if name == 'automatic' else "external."+name,logical.logical_artifact_id,digest,value.SCHEMA,
            "application/json",len(raw),Visibility.PROSPECTIVE,lane,None))
        if name!="automatic":
            edges.append(ScientificInputSpec("edge."+name,name,ScientificInputRole.HISTORY if producer else ScientificInputRole.SOURCE,
                producer,producer+".product" if producer else None,None if producer else "external."+name,
                "scientific."+name,logical.logical_artifact_id,value.SCHEMA,"application/json",len(raw),lane,Visibility.PROSPECTIVE,
                BarrierKind.NONE))
        else:
            from empirical_lawhood.runtime.recursive_compiler import configuration_edge_id, configuration_input_id
            edges.append(ScientificInputSpec(configuration_edge_id(task_id), 'config', ScientificInputRole.CONFIGURATION,
                None, None, configuration_input_id(config.config_id), config.config_id, config.config_id,
                config.SCHEMA, 'application/json', len(raw), lane, Visibility.PROSPECTIVE, BarrierKind.NONE))
    ports.sort(key=lambda port: port.artifact_id)
    contracts.sort(key=lambda contract: contract.artifact_id)
    dependencies=tuple(DependencyReceiptBinding("receipt."+task,task,tuple(sorted(materials)))
        for task,materials in sorted(receipt_materials.items()))
    config_ref=CapabilityConfigRef(config.config_id,config.SCHEMA,manifest.config_schema_sha256,config.fingerprint(),config.config_id)
    outputs=tuple(WorkerOutputPort(task_id+"."+(row.output_id if output else "foreign-output"),
        row.payload_schema,row.profile,row.media_type,"output.disclosed-adjudication."+row.output_id)
        for row in declaration.outputs)
    requirement=CapabilityRequirement(manifest.capability_key,manifest.capability_version,manifest.kind,config_ref,
        manifest.input_schema_ids,manifest.output_schema_ids,manifest.permissions,declaration.evidence_ceiling,
        Access.EVALUATOR_REVEAL,budget)
    task=ExecutionTask(task_id,declaration.stage,requirement,manifest.implementation_sha256,tuple(sorted(receipt_materials)),
        tuple(external),tuple(ArtifactOutputSpec(row.output_id,row.logical_artifact_id,"unpublished/"+row.output_id+".json",
            row.payload_schema,row.profile,row.media_type,Visibility.OUTCOME_VISIBLE,(Visibility.PROSPECTIVE,),Access.EVALUATION_REVEALED)
            for row in outputs),(),declaration.execution_properties.barrier,1,("obligation.disclosed-adjudication",),scientific_inputs=tuple(edges))
    plan=ObjectIdentity("plan.disclosed-adjudication","empirical-lawhood/runtime/execution-plan","1.0.0","a"*64)
    scope=ScientificAdjudicationContext(plan,"world.disclosed-adjudication",WorldKind.NUMERICAL_SIMULATOR,
        ObjectIdentity("relation.disclosed-adjudication","empirical-lawhood/testing/relation","1.0.0","b"*64),
        "unit.disclosed-whole-group",(ObjectIdentity("cutoff.disclosed-adjudication","empirical-lawhood/testing/cutoff","1.0.0","c"*64),),
        Visibility.OUTCOME_VISIBLE,Access.EVALUATION_REVEALED) if authority else None
    context=TaskContext("run.disclosed-adjudication",task_id,"attempt.disclosed-adjudication",config_ref,
        tuple(port.binding for port in ports),tuple(ports),outputs,manifest.permissions,Access.EVALUATOR_REVEAL,budget,
        WorkerIsolationProfile.TRUSTED_LOCAL,dependencies,scientific_adjudication_context=scope)
    packages=(("synthetic/control.py","1"*64),)
    implementation=RecursiveImplementationBinding(packages,sha256(canonical_json_bytes(packages)).hexdigest(),"2"*64,"3"*40,False)
    prepared=PreparedInvocationContract("prepared.disclosed-adjudication",manifest,implementation,
        PreparedWorkerEnvironment("/synthetic/python","4"*64,"/synthetic",()),context.run_id,task_id,context.attempt_id,
        config_ref,tuple(contracts),outputs,manifest.permissions,Access.EVALUATOR_REVEAL,budget,WorkerIsolationProfile.TRUSTED_LOCAL,
        dependencies,execution_plan=plan,execution_task=ObjectIdentity.from_record(task_id,task),execution_task_record=task,
        required_input_artifact_ids=tuple(port.artifact_id for port in ports),scientific_adjudication_context=scope)
    context=replace(context,prepared_invocation=prepared)
    runner=declaration.runner_factory().with_prepared_scope((context.run_id,task_id,context.input_materialization_ids,plan))
    return runner,context


@pytest.mark.parametrize("kind",("wave","calibration"))
def test_actual_e4_evaluators_retain_unevaluable_status_and_exact_scope(adjudication_literals,kind):
    runner,context=_prepared(adjudication_literals[kind])
    result=runner.execute(context)
    output,=result.outputs
    record=decode_canonical_bytes(output.payload,ScientificAdjudicationRecord,maximum_bytes=None)
    assert output.output_id==context.task_id+".adjudication"
    assert record.matches_context(context.scientific_adjudication_context)
    assert record.input_materialization_ids==context.input_materialization_ids
    assert record.required_receipt_ids==context.dependency_receipt_ids
    assert record.evaluability is AdjudicationEvaluability.UNEVALUABLE
    assert record.scientific_status is ScientificStatus.UNEVALUABLE
    assert record.admission_status is AdmissionStatus.UNEVALUABLE
    if kind=="calibration":assert "CONDITIONAL_REVISION_RADIUS_FINITE" in record.reason_codes
    else:assert "SCIENTIFIC_ASSESSMENT_PENDING" in record.reason_codes
    assert all(port._reader.stream.closed for port in context.input_ports)


@pytest.mark.parametrize("kind",("wave","calibration"))
@pytest.mark.parametrize("damage",("missing-context","missing-output"))
def test_e4_adjudication_guard_refuses_before_any_input_read(adjudication_literals,kind,damage):
    runner,context=_prepared(adjudication_literals[kind],authority=damage!="missing-context",output=damage!="missing-output",forbid_reads=True)
    with pytest.raises(ValueError,match="reveal context|revealed output"):
        runner.execute(context)
    assert all(port._reader.stream.closed for port in context.input_ports)


@pytest.mark.parametrize("kind",("wave","calibration"))
@pytest.mark.parametrize("damage",("missing-entry","foreign-entry"))
def test_actual_e4_evaluators_refuse_missing_or_foreign_entry(adjudication_literals,kind,damage):
    declaration,config,values,producers=adjudication_literals[kind]
    values=dict(values)
    if damage=="missing-entry":values.pop("entry")
    else:values["entry"]=replace(values["entry"],programme=replace(values["entry"].programme,object_fingerprint="f"*64))
    runner,context=_prepared((declaration,config,values,producers))
    with pytest.raises(ValueError,match="operand|assigned exact|declared source|source-entry|successful source-entry"):
        runner.execute(context)
    assert all(port._reader.stream.closed for port in context.input_ports)
