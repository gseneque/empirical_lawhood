# SPDX-License-Identifier: MPL-2.0
"""Public declarative recipe, input preparation and retained-result interface."""
from __future__ import annotations

from dataclasses import fields
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.design.joint_description import Description,Economics,JointSpecification,PROTOCOL_ID,ReceiverPolicy,SelectedInputs,json_text
from empirical_lawhood.science.joint_description import MAX_BYTES,Assessment
from empirical_lawhood.science.records.status import OperationalStatus


def new_recipe(family_id):
    """A researcher edits this ordinary JSON document, never generated task IDs."""
    from empirical_lawhood.domains.joint_description_catalogue import preset
    selected=preset(family_id)
    work_fields={"forecast_work_units","forecast_work_unit","forecast_work_basis"}
    if any(not work_fields <= set(row) for row in selected["descriptions"]):
        raise ValueError("scientific presets must explicitly author forecast construction work, unit and estimate basis")
    return {"family_id":family_id,"question":selected["question"],"seed":20261114,
        "calibration_unit_ids":[f"unit.{family_id.lower()}.calibration.{i:04d}" for i in range(selected["calibration_units"])],
        "evaluation_unit_ids":[f"unit.{family_id.lower()}.evaluation.{i:04d}" for i in range(selected["evaluation_units"])],
        "actions":list(selected["actions"]),"horizons":list(selected["horizons"]),
        "receiver_policies":selected["receiver_policies"],"descriptions":selected["descriptions"],
        "parameters":selected["parameters"],
        "economics":{f.name:(str(getattr(Economics(),f.name)) if isinstance(getattr(Economics(),f.name),Decimal)
            else getattr(Economics(),f.name)) for f in fields(Economics)}}


def specification_from_recipe(recipe):
    expected={"family_id","question","seed","calibration_unit_ids","evaluation_unit_ids","actions","horizons",
        "receiver_policies","descriptions","parameters","economics"}
    if not isinstance(recipe,dict) or set(recipe)!=expected:
        raise ValueError("recipe fields must exactly match the current declared scientific authoring contract")
    descriptors=[]
    for row in recipe["descriptions"]:
        if set(row)!={"id","features","model","state_dimension","interface_dimension","memory_dimension","memory_samples","rationale",
                     "forecast_work_units","forecast_work_unit","forecast_work_basis"}:
            raise ValueError("description adds or omits a scientific contract field")
        descriptors.append(Description(row["id"],tuple(row["features"]),row["model"],row["state_dimension"],
            row["interface_dimension"],row["memory_dimension"],row["memory_samples"],row["rationale"],
            Decimal(str(row["forecast_work_units"])),row["forecast_work_unit"],row["forecast_work_basis"]))
    policies=[]
    for receiver,row in recipe["receiver_policies"].items():
        if set(row)-{"units","target","scale","max_abs_error","weight","safety_lower","safety_upper"}:
            raise ValueError("receiver policy includes undeclared scientific coordinates")
        policies.append(ReceiverPolicy(receiver,row["units"],*(Decimal(str(row[key])) for key in ("target","scale","max_abs_error","weight")),
            *(None if row.get(key) is None else Decimal(str(row[key])) for key in ("safety_lower","safety_upper"))))
    economics=dict(recipe["economics"])
    if set(economics)!={f.name for f in fields(Economics)}:
        raise ValueError("all economic prices, thresholds and units must be explicit")
    for name in economics:
        if name not in ("accounting_unit","reuse_count"):
            economics[name]=Decimal(str(economics[name]))
    identifier="specification.joint-description."+recipe["family_id"].lower()+"."+sha256(json_text(recipe).encode()).hexdigest()[:24]
    return JointSpecification(identifier,recipe["family_id"],recipe["question"],recipe["seed"],
        tuple(sorted(recipe["calibration_unit_ids"])),tuple(sorted(recipe["evaluation_unit_ids"])),
        tuple(sorted(Decimal(str(v)) for v in recipe["actions"])),tuple(sorted(Decimal(str(v)) for v in recipe["horizons"])),
        tuple(sorted(policies,key=lambda r:r.receiver_id)),tuple(sorted(descriptors,key=lambda r:r.description_id)),
        json_text(recipe["parameters"]),Economics(**economics))


def create_inputs(*,recipe_path,project_root,output_directory,device="cpu",raw_cohort_path=None):
    """Freeze selected new inputs and source; do not run an experiment."""
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.storage.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.storage.bounded_io import read_bounded_bytes
    from empirical_lawhood.design.experiment_inputs import ExperimentInputBinding,ExperimentInputSelection
    from empirical_lawhood.adapters.joint_description.experiment import bind_inputs
    destination=Path(output_directory).absolute()
    if destination.exists():
        raise FileExistsError("new experiment inputs require a new explicit destination")
    raw=read_bounded_bytes(Path(recipe_path),maximum_bytes=1024**2)
    spec=specification_from_recipe(json.loads(raw))
    archive=None if raw_cohort_path is None else read_bounded_bytes(Path(raw_cohort_path),maximum_bytes=MAX_BYTES//2).decode("utf-8")
    selected=SelectedInputs("inputs.joint-description."+spec.fingerprint(),spec.identity,device,archive,
        None if archive is None else sha256(archive.encode()).hexdigest())
    provenance=capture_numerical_provenance(project_root=project_root)
    implementation=implementation_binding(project_root)
    if (provenance.observed_git_head,provenance.code_sources_sha256,provenance.dependency_lock_sha256)!=(
            implementation.observed_git_head,implementation.code_sources_sha256,implementation.dependency_lock_sha256):
        raise ValueError("source changed while selecting the new experiment")
    bind_inputs(spec,{"selected":selected,"provenance":provenance})
    sources=ExperimentInputSelection("sources.joint-description."+spec.fingerprint(),PROTOCOL_ID,
        tuple(ExperimentInputBinding(name,value.identity,name+".json",len(value.canonical_bytes())) for name,value in
            (("provenance",provenance),("selected",selected))))
    payloads={"specification.json":spec.canonical_bytes(),"selected.json":selected.canonical_bytes(),
        "provenance.json":provenance.canonical_bytes(),"sources.json":sources.canonical_bytes(),
        "source-snapshot.json":implementation.canonical_bytes(),"recipe.json":raw}
    destination.mkdir(parents=True,exist_ok=False)
    for name,payload in sorted(payloads.items()):
        with (destination/name).open("xb") as stream:
            stream.write(payload)
    return {"specification":str(destination/"specification.json"),"sources":str(destination/"sources.json"),
        "source_snapshot":str(destination/"source-snapshot.json"),"family_id":spec.family_id,"device":device,
        "native_contact_count":0,"scientific_execution_performed":False}


def read_result(*,directory,artifact_writer,specification,instance,payloads,report,products,draft,plan,allow_partial=False):
    """Present original completed assessment bytes; never refit or reacquire."""
    if type(specification) is not JointSpecification or instance.specification!=specification.identity:
        raise PermissionError("retained result belongs to another scientific definition")
    base={"namespace":"joint-description","family_id":specification.family_id,
        "evidence_scope":"EXPOSED_DEVELOPMENT","qualification":"NOT_ESTABLISHED",
        "scientific_reconstruction_performed":False,"native_acquisition_performed":False}
    if allow_partial or report.get("typed_product_validation")=="DEFERRED":
        return {**base,"scientific_completion":"DEFERRED"}
    found=[]
    for task,records in products["records"].items():
        for value in records.values():
            if type(value) is Assessment:
                receipt=products["receipts"].get(task)
                if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED or value.specification!=specification.identity:
                    raise PermissionError("assessment lacks its successful original typed receipt")
                found.append(value)
    if not found:
        return {**base,"scientific_completion":"INCOMPLETE"}
    if len(found)!=1:
        raise PermissionError("experiment has more than one terminal scientific assessment")
    assessment=found[0]
    return {**base,"scientific_completion":"COMPLETED","assessment":assessment.identity.to_document(),
        "findings":json.loads(assessment.result_json)}
