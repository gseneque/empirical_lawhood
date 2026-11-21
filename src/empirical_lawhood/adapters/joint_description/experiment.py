# SPDX-License-Identifier: MPL-2.0
"""Pure preparation and revalidation through the ordinary experiment protocol."""
from empirical_lawhood.design.joint_description import JointSpecification,SelectedInputs
from empirical_lawhood.adapters.joint_description.lowering import lower
from empirical_lawhood.science.experiments.experimental_design import IndependentUnit,UnitAllocation,UnitRoleAssignment
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.execution.experiment_preparation import DependencyKind,ExperimentCensus,ExperimentDependency,ExperimentPreparation,PreparedExperimentInputs


def allocation_for(specification,selected):
    calibration=set(specification.calibration_unit_ids)
    return UnitAllocation("allocation.joint-description."+specification.fingerprint(),(selected.identity,),
        tuple(IndependentUnit(u,selected.record_id,"family."+specification.family_id.lower(),(),True) for u in specification.all_unit_ids),
        tuple(UnitRoleAssignment(u,"calibration" if u in calibration else "evaluation") for u in specification.all_unit_ids))


def bind_inputs(specification,records,*,files=None):
    if type(specification) is not JointSpecification:
        raise TypeError("new joint-description experiments require their authored specification")
    specification.__post_init__()
    from empirical_lawhood.domains.joint_description_catalogue import family_module
    validator = getattr(family_module(specification.family_id), "validate_specification", None)
    if validator is not None:
        validator(specification)
    if set(records)-{"selected","provenance"} or files:
        raise ValueError("joint-description binding supplied undeclared scientific operands")
    selected=records.get("selected");provenance=records.get("provenance")
    if selected is not None:
        if type(selected) is not SelectedInputs or selected.specification!=specification.identity:
            raise ValueError("selected inputs belong to another authored experiment")
        selected.__post_init__()
        if selected.device=="gpu" and specification.family_id not in ("R17","R22"):
            raise ValueError("only R17/R22 have native GPU implementations; all other families select CPU")
    if provenance is not None:
        if type(provenance) is not NumericalProducingProvenance:
            raise TypeError("native work requires exact producing-source provenance")
        provenance.__post_init__()
    return PreparedExperimentInputs({} if selected is None else {"selected":allocation_for(specification,selected)},records)


def prepare(specification,*,scientific_inputs,execution,method_inputs=None,protocol_bytes=None):
    records={} if method_inputs is None else method_inputs
    bound=bind_inputs(specification,records)
    if scientific_inputs!=bound.scientific_inputs or protocol_bytes is not None:
        raise ValueError("joint-description preparation changed declared scientific inputs")
    dependencies=[]
    for key in ("selected","provenance"):
        if key not in records:
            dependencies.append(ExperimentDependency("joint-description.input."+key,DependencyKind.EXTERNAL_INPUT,
                "Supply the copied typed "+key+" record through the public input author.",key))
    for key in ("environment_id","source_snapshot","output_root","workers"):
        if getattr(execution,key) is None:
            dependencies.append(ExperimentDependency("joint-description.execution."+key,DependencyKind.ENVIRONMENT,
                "Select explicit "+key+" before authoring."))
    selected=records.get("selected")
    if selected is not None and specification.family_id in ("R13","R14","R15","R16","R22"):
        if selected.archive_json is None:
            dependencies.append(ExperimentDependency("joint-description.input.raw-cohort",DependencyKind.EXTERNAL_INPUT,
                "Supply newly selected raw observations matching the strict family cohort schema; no result archive or synthetic substitute.","selected"))
        else:
            from empirical_lawhood.adapters.physical.joint_description import validate_selected_cohort
            validate_selected_cohort(selected.archive_json.encode("utf-8"), specification)
    allocation=draft=None;inputs=()
    if not dependencies:
        allocation=allocation_for(specification,selected)
        draft,inputs=lower(specification,selected,records["provenance"])
    counts=(("calibration-roots",len(specification.calibration_unit_ids)),("evaluation-roots",len(specification.evaluation_unit_ids)))
    resolved=tuple((name,count if allocation is not None else 0) for name,count in counts)
    return ExperimentPreparation(specification.identity,ExperimentCensus(counts,resolved,(("operations",6),),
        (("canonical-products",6),),len(specification.calibration_unit_ids)+2*len(specification.evaluation_unit_ids)),
        tuple(sorted(dependencies,key=lambda r:r.code)),allocation=allocation,draft=draft,input_records=inputs,
        execution=execution,specification_record=specification,
        design_records=tuple(sorted((r.identity.object_id,r) for r in records.values())))


def validate_instance(*,specification,allocation,draft,source_records):
    records={"selected" if type(value) is SelectedInputs else "provenance":value for _,value in source_records}
    if len(source_records)!=2 or set(records)!={"selected","provenance"}:
        raise ValueError("new experiment requires its exact two selected source records")
    bind_inputs(specification,records)
    if allocation!=allocation_for(specification,records["selected"]) or draft!=lower(specification,records["selected"],records["provenance"])[0]:
        raise ValueError("authored experiment changed its scientific allocation or recursive graph")
