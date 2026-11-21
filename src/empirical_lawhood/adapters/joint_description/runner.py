# SPDX-License-Identifier: MPL-2.0
"""Shared worker/custody integration; all scientific calculations are delegated.

Native work is one recorded subwork per independent root. Recovery reads the
original completed bytes; it never silently repeats an uncertain native effect.
"""
from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import json
import resource
import time

from empirical_lawhood.adapters.joint_description import lowering as workflow
from empirical_lawhood.design.joint_description import JointSpecification,SelectedInputs
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.joint_description import MAX_BYTES,MAX_COHORT_BYTES,Assessment,Calibration,Forecast,Model,Outcomes,Predictors,TrialRequest,split_batch
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.artifact_stream_primitives import STREAM_CHUNK_BYTES
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile,ReceiptCheck
from empirical_lawhood.execution.execution import RunnerResult,TaskOutputPayload
from empirical_lawhood.execution.native_subwork import NativeSubworkDefinition,NativeSubworkOutput,NativeSubworkRoster
from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork
from .records import NATIVE_PHASES,OperationConfig,acquisition_units,effect_slots,phase_config,units

KINDS=(JointSpecification,SelectedInputs,NumericalProducingProvenance,OperationConfig,
    Calibration,Predictors,Outcomes,Model,Forecast,Assessment)
INPUTS={"calibrate":(("selected",SelectedInputs),("provenance",NumericalProducingProvenance)),
    "fit":(("calibration",Calibration),),
    "prepare":(("selected",SelectedInputs),("provenance",NumericalProducingProvenance),("model",Model)),
    "forecast":(("model",Model),("predictors",Predictors)),
    "evaluate":(("selected",SelectedInputs),("provenance",NumericalProducingProvenance),("forecast",Forecast),("predictors",Predictors)),
    "assess":(("model",Model),("forecast",Forecast),("outcomes",Outcomes))}
OUTPUTS={"calibrate":("calibration",Calibration),"fit":("model",Model),"prepare":("predictors",Predictors),
    "forecast":("forecast",Forecast),"evaluate":("outcomes",Outcomes),"assess":("assessment",Assessment)}


def load_inputs(context,manifest):
    codecs={kind.SCHEMA:kind for kind in KINDS}
    received={}
    for port in context.input_ports:
        kind=codecs.get(port.payload_schema)
        if kind is None or kind in received or port.media_type!="application/json":
            raise ValueError("joint-description worker changed an exact input schema or role")
        bound = MAX_COHORT_BYTES if kind in (Calibration, Predictors, Outcomes) else MAX_BYTES
        received[kind]=port.decode_canonical_record(kind, maximum_bytes=bound)
    config=received.pop(OperationConfig)
    expected_capability = "joint-description." + config.phase + "." + (
        config.device if config.phase in NATIVE_PHASES else "cpu")
    if manifest.capability_key != expected_capability:
        raise ValueError("worker manifest differs from the exact authored phase/device capability")
    expected=INPUTS[config.phase]
    if set(received)!={kind for _,kind in expected}:
        raise ValueError("joint-description worker changed its complete input census")
    if (context.task_id,context.config.config_id,context.config.content_sha256)!=(config.node_id,config.config_id,config.fingerprint()):
        raise ValueError("worker configuration differs from the compiler's immutable task")
    if context.resource_budget!=workflow.budget(config.phase,config.device) or context.permissions!=manifest.permissions or context.outcome_access is not workflow.ACCESS:
        raise ValueError("worker changed resources, permissions or evidence scope")
    output_name,_=OUTPUTS[config.phase]
    if tuple(p.output_id for p in context.output_ports)!=(config.node_id+"."+output_name,):
        raise ValueError("worker changed its complete typed output census")
    values={name:received[kind] for name,kind in expected}
    parents = {name: phase_config(config, phase).node_id + "." + name for name, phase in (
        ("calibration", "calibrate"), ("model", "fit"), ("predictors", "prepare"),
        ("forecast", "forecast"), ("outcomes", "evaluate"))}
    for value in values.values():
        if hasattr(value,"specification") and value.specification!=config.specification.identity:
            raise ValueError("worker input belongs to another scientific specification")
    for name, value in values.items():
        if name in parents and value.record_id != parents[name]:
            raise ValueError("worker predecessor identity differs from the code-derived scientific phase")
    model = values.get("model")
    if model is not None and model.calibration.object_id != parents["calibration"]:
        raise ValueError("model substituted its code-derived calibration predecessor")
    forecast = values.get("forecast")
    if forecast is not None and (forecast.model.object_id != parents["model"]
                                or forecast.predictors.object_id != parents["predictors"]):
        raise ValueError("forecast substituted its code-derived model or predictor predecessor")
    calibration = values.get("calibration")
    if calibration is not None:
        prefix = phase_config(config, "calibrate").node_id
        if (calibration.predictors.record_id, calibration.outcomes.record_id) != (prefix + ".predictors", prefix + ".outcomes"):
            raise ValueError("calibration substituted its code-derived predictor/outcome tables")
    if config.phase in NATIVE_PHASES:
        if values["selected"].identity!=config.selected_inputs or values["provenance"].identity!=config.provenance or values["selected"].device!=config.device:
            raise ValueError("native acquisition changed selected source, provenance or device")
    return config,values


def native_port(family_id):
    if family_id in ("R20","R21"):
        from empirical_lawhood.adapters.simulators.reactor_joint_description.native import ReactorJointDescriptionPort
        return ReactorJointDescriptionPort()
    if family_id in ("R17","R18","R19","R22"):
        from empirical_lawhood.adapters.simulators.joint_description_native import NativeJointDescriptionPort
        return NativeJointDescriptionPort()
    return None


def request_for(config,selected,unit):
    spec=config.specification
    parameters=json.loads(spec.parameters_json)
    parameters["receivers"]=tuple(r.receiver_id for r in spec.receivers)
    return TrialRequest(spec.family_id,spec.seed,(unit,),"calibration" if config.phase=="calibrate" else "evaluation",
        tuple(float(v) for v in spec.actions),tuple(float(v) for v in spec.horizons),parameters,
        device=config.device,input_json=selected.archive_json)


def definitions(config,values,context,parent):
    provenance=values["provenance"]
    if provenance.observed_git_head!=parent.implementation_commit or not provenance.observed_checkout_clean:
        raise ValueError("native producing source is not the exact clean entered implementation")
    contract=context.prepared_invocation
    if contract is not None and (provenance.package_sources,provenance.code_sources_sha256,provenance.dependency_lock_sha256)!=(
            contract.implementation.package_sources,contract.implementation.code_sources_sha256,contract.implementation.dependency_lock_sha256):
        raise ValueError("native source/lock census differs from the prepared implementation")
    sources=tuple(sorted((value.identity for value in values.values()),key=lambda r:r.object_id))
    return tuple(NativeSubworkDefinition("unit."+unit,"joint-description."+config.phase,parent,config.identity,
        sources,provenance.code_sources_sha256,provenance.dependency_lock_sha256,context.input_materialization_ids,(),
        (NativeSubworkOutput("trial",Calibration.SCHEMA,ArtifactProfile.CANONICAL_JSON,"application/json"),))
        for unit in acquisition_units(config))


def prepare_native_work(*,runner,context,expected_parent):
    config,values=load_inputs(context,runner.manifest)
    selected=definitions(config,values,context,expected_parent)
    return PreparedNativeWork(expected_parent,units(config),effect_slots(config),selected,
        (NativeSubworkRoster("selected.native-subwork",expected_parent,tuple(d.identity for d in selected)),))


class Runner:
    def __init__(self,*,manifest):
        self.manifest=manifest

    def execute(self,context):
        from empirical_lawhood.methods.joint_description import assess_descriptions,fit_response_laws,forecast_and_choose
        try:
            config,inputs=load_inputs(context,self.manifest)
            name,_=OUTPUTS[config.phase]
            identifier=config.node_id+"."+name
            if config.phase=="fit":
                result=fit_response_laws(config.specification,inputs["calibration"],record_id=identifier)
            elif config.phase=="forecast":
                result=forecast_and_choose(config.specification,inputs["model"],inputs["predictors"],record_id=identifier)
            elif config.phase=="assess":
                result=assess_descriptions(config.specification,inputs["model"],inputs["forecast"],inputs["outcomes"],record_id=identifier)
            else:
                raise ValueError("acquisition requires the actual shared native-progress port")
            return RunnerResult((TaskOutputPayload(identifier,result.canonical_bytes()),),
                (ReceiptCheck("joint-description-typed-causal-census",True,()),))
        finally:
            for port in context.input_ports:
                port.close()


class NativeRunner(Runner):
    def preflight(self,context):
        config,values=load_inputs(context,self.manifest)
        if context.accelerated_compute != (config.device == "gpu"):
            raise ValueError("actual invocation acceleration differs from the frozen CPU/GPU selection")
        contract=context.prepared_invocation
        if contract is None or contract.native_work is None:
            raise ValueError("native work requires a prepared complete source/effect contract")
        contract.validate_context(context)
        if contract.native_work.definitions!=definitions(config,values,context,contract.expected_parent_contact):
            raise ValueError("native worker changed its prepared subwork census")

    def execute_streaming_with_native_subwork(self,context,native_subwork,emitter,progress=None):
        from empirical_lawhood.domains.joint_description_catalogue import family_module
        try:
            config,values=load_inputs(context,self.manifest)
            contract=context.prepared_invocation
            if contract is None or contract.native_work is None:
                raise ValueError("native work requires actual prepared progress custody")
            contract.validate_context(context)
            selected=definitions(config,values,context,contract.expected_parent_contact)
            if native_subwork.parent_contact!=contract.expected_parent_contact or selected!=contract.native_work.definitions:
                raise ValueError("native progress substituted original parent or definitions")
            owner=family_module(config.specification.family_id)
            port=None
            retained=[]
            native_subwork.freeze_roster(contract.native_work.rosters[0],definitions=selected)
            for ordinal,(unit,definition) in enumerate(zip(acquisition_units(config),selected,strict=True)):
                completed=native_subwork.recover(definition)
                if completed is None:
                    entry=native_subwork.begin(definition)
                    native_subwork.contact(entry)
                    cpu_start,wall_start=time.process_time(),time.monotonic()
                    try:
                        if port is None:
                            port=native_port(config.specification.family_id)
                        request=request_for(config,values["selected"],unit)
                        batch=(owner.prepare_predictors(request,native_port=port) if config.phase=="prepare"
                            else owner.produce(request,native_port=port))
                        batch.validate_census(request,tuple(r.receiver_id for r in config.specification.receivers))
                        predictors,outcomes=split_batch(batch,config.specification.identity,config.node_id+".unit."+unit)
                        if config.phase=="evaluate":
                            issued=tuple(r for r in values["predictors"].rows if r.unit_id==unit)
                            if predictors.rows!=issued:
                                raise ValueError("evaluation changed the already issued causal predictor bytes")
                        result=Calibration(config.node_id+".unit."+unit+".trial",config.specification.identity,predictors,outcomes)
                        raw=result.canonical_bytes()
                        native_subwork.publish_output(entry,"trial",(raw,),maximum_bytes=MAX_BYTES,
                            maximum_chunk_bytes=MAX_BYTES,expected_size_bytes=len(raw),expected_physical_sha256=sha256(raw).hexdigest())
                    except Exception:
                        native_subwork.complete(entry,operational_status=OperationalStatus.FAILED,
                            cost=InquiryCost(Decimal(str(time.process_time()-cpu_start)),Decimal(str(time.monotonic()-wall_start)),None),
                            cost_scope="attempted root acquisition; uncertain native work is not retried",
                            unknown_streams=definition.streams,reason_codes=("joint-description-native-acquisition-failed",))
                        raise
                    native_subwork.complete(entry,operational_status=OperationalStatus.SUCCEEDED,
                        cost=InquiryCost(Decimal(str(time.process_time()-cpu_start)),Decimal(str(time.monotonic()-wall_start)),Decimal(len(raw))),
                        cost_scope="actual per-root worker CPU/wall and retained bytes including repeated causal-prefix preparation",
                        consumed_streams=definition.streams,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
                raw=b"".join(native_subwork.iter_completed_output(definition,"trial"))
                retained.append(decode_canonical_bytes(raw,Calibration,maximum_bytes=MAX_BYTES))
                if progress is not None:
                    progress.advance(Decimal(ordinal+1))
            name,_=OUTPUTS[config.phase]
            prefix=config.node_id
            predictors=Predictors(prefix+".predictors",config.specification.identity,
                tuple(sorted((r for item in retained for r in item.predictors.rows),key=lambda r:r.key)),
                retained[0].predictors.source_kind,tuple(sorted({p for item in retained for p in item.predictors.provenance})))
            outcomes=Outcomes(prefix+".outcomes",config.specification.identity,
                tuple(sorted((r for item in retained for r in item.outcomes.rows),key=lambda r:r.key)),
                retained[0].outcomes.source_kind,tuple(sorted({p for item in retained for p in item.outcomes.provenance})))
            result=(Calibration(prefix+".calibration",config.specification.identity,predictors,outcomes)
                if config.phase=="calibrate" else predictors if config.phase=="prepare" else outcomes)
            if result.canonical_size_bytes() > MAX_COHORT_BYTES:
                raise ValueError("complete cohort product exceeds its declared custody bound")
            raw=result.canonical_bytes()
            output_id = prefix + "." + name
            for start in range(0, len(raw), STREAM_CHUNK_BYTES):
                emitter.write(output_id, raw[start : start + STREAM_CHUNK_BYTES])
            return (ReceiptCheck("joint-description-original-per-root-custody",True,()),)
        finally:
            for port in context.input_ports:
                port.close()
