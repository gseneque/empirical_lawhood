# SPDX-License-Identifier: MPL-2.0
"""Declarative fresh native E2 lowering through ordinary recursive operations."""
from dataclasses import dataclass
from functools import lru_cache
from decimal import getcontext
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs
from . import native_utility_records as r

PROTOCOL_ID="matrix.factor-response.native-utility"
QUESTION="Do the frozen factor variables improve the declared finite-dt native response description against the explicit origin-mechanical comparators?"
WORLD="world.matrix-native-utility.current-paired-scheduled"


def entry_task_id(specification):
    return r.NAMESPACE+"."+(specification.specification_id if type(specification) is r.NativeUtilitySpecification else specification.object_id)+".entry"


def terminal_task_id(specification):return entry_task_id(specification).removesuffix("entry")+"terminal"


def task_id(root_id,operation):return r.NAMESPACE+"."+root_id+"."+operation


def development_root(specification,request,study_id):
    groups=tuple(sorted(value.root.independent_group_id for value in request.source_manifest.reservation.allocation.roots))
    views=tuple(sorted({view.view_id for coordinate in request.source_manifest.reservation.allocation.coordinates for view in (coordinate.primary_view,coordinate.fine_view)}))
    claim=ClaimSpec("claim."+study_id,WORLD,request.record_id,QUESTION,
        "Every assigned whole E2 root, full coupled native odd response, all selected zero-fit descriptions and both views; all adverse/nonuse outcomes remain.",
        "unit.original-whole-group",None,EvidenceCeiling.NON_PROMOTABLE,OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,
        "Fresh native E2 acquisition with pre-contact criterion; conditional finite-dt arithmetic only, sampling and scientific qualification not established.",
        ("assumption.native-utility.actual-declared-source",),numerical_view_ids=views)
    operands=tuple(sorted((specification.identity,request.identity,r.scheduled_identity(request.source_manifest.reservation)),key=lambda value:value.object_id))
    if len({value.object_id for value in operands})!=len(operands):raise ValueError("native E2 aliases distinct frozen scientific operands")
    return DevelopmentStudySpec(study_id,QUESTION,request.identity,WORLD,WorldKind.NUMERICAL_SIMULATOR,groups,views,(claim,),operands)


def contracts(specification,request):
    context=getcontext()
    signature=(context.prec,context.rounding,context.Emin,context.Emax,context.clamp,context.capitals,tuple(sorted((signal.__name__,enabled) for signal,enabled in context.traps.items())))
    return _contracts(signature,specification,request)


@lru_cache(maxsize=2)
def _contracts(_decimal_context,specification,request):
    from . import native_utility_bindings as b
    r.validate_request(specification,request)
    if specification.criterion is None:raise ValueError("native E2 lowering lacks its pre-contact scientific utility criterion")
    configs,external,links,records,files={},{},[],{},{}
    specification_pin, request_pin = specification.identity, request.identity
    entry,terminal=entry_task_id(specification),terminal_task_id(specification)
    configs[entry]=b.NativeUtilityEntryConfig("config."+entry,specification,request)
    configs[terminal]=b.NativeUtilityOperationConfig("config."+terminal,"terminal",specification_pin,request_pin,
        None,None,None,(),request.resources.for_operation("terminal"),(),tuple(sorted(value.root.independent_group_id for value in request.source_manifest.reservation.allocation.roots)))
    def record(value,logical):
        key="external."+logical
        item=RecursiveExternalInput(key,logical,value.SCHEMA,"application/json",len(value.canonical_bytes()),b.DEV,b.EXPOSED,value.fingerprint(),"SOURCE")
        if external.setdefault(key,item)!=item or records.setdefault(key,value)!=value:raise ValueError("native E2 aliases original canonical operands")
        return key
    def file(artifact):
        key="external."+artifact.artifact_id
        item=RecursiveExternalInput(key,artifact.artifact_id,artifact.payload_schema,artifact.media_type,artifact.size_bytes,b.DEV,b.EXPOSED,artifact.sha256,"SOURCE")
        if external.setdefault(key,item)!=item or files.setdefault(key,artifact)!=artifact:raise ValueError("native E2 aliases original shared template bytes")
        return key
    def edge(node,name,*,external=None,producer=None,output="product"):
        links.append(RecursiveInputLink("edge."+node+"."+name,node,name,external_input_id=external,producer_node_id=producer,
            producer_output_id=output if producer is not None else None,scientific_role="SOURCE" if external is not None else "HISTORY"))
    specification_input=record(specification,specification.specification_id)
    manifest_input=record(request.source_manifest,request.source_manifest.record_id)
    protocols={value.public_source.root.root_id:value for value in request.protocols}
    index = ScheduledSourceIndex.from_shared(reservation=request.source_manifest.reservation,
        specification=request.source_manifest.native_specification, provenances=request.source_manifest.provenances)
    index.require_roster(request.sources, expected_root_ids=index.root_ids)
    for descriptor in request.sources:
        source=r.source_for(request,descriptor.root_id,index=index);protocol=protocols[source.root_id];panels=r.panels_for(request,source)
        provenance=record(source.provenance,source.provenance.identity.object_id)
        for operation in r.PHASES:
            node=task_id(source.root_id,operation);public=operation=="physical-forecast"
            selected_protocol=r.identity(protocol) if operation in ("physical-forecast","responses","response-score") else None
            configs[node]=b.NativeUtilityOperationConfig("config."+node,operation,specification_pin,request_pin,
                None if public else descriptor,protocol.public_source if public else None,selected_protocol,
                panels if operation in ("responses","response-score") else (),request.resources.for_operation(operation),
                () if public or operation=="prefix" else tuple((phase,r.identity(configs[task_id(source.root_id,phase)])) for phase in (("prefix","responses") if operation=="response-score" else ("prefix",))))
            for name in b.INPUTS[operation]:
                if name=="specification":edge(node,name,external=specification_input)
                elif name=="source":edge(node,name,external=record(descriptor,descriptor.source_id))
                elif name=="coordinate":edge(node,name,external=record(source.coordinate,source.coordinate.coordinate_id))
                elif name=="protocol":edge(node,name,external=record(protocol,protocol.protocol_id))
                elif name=="manifest":edge(node,name,external=manifest_input)
                elif name=="provenance":edge(node,name,external=provenance)
                elif name=="templates":edge(node,name,external=file(protocol.templates.array_artifact))
                elif name=="streams":
                    for stream in source.root.streams:edge(node,"streams.source."+stream.purpose,external=record(stream,source.root.stream_identity(stream).object_id))
                    if operation=="responses":
                        for panel in panels:
                            if panel.role=="INDEPENDENT_FUTURE":
                                for stream in panel.streams:edge(node,"streams.future."+panel.panel_id+"."+stream.purpose,external=record(stream,panel.stream_identity(stream).object_id))
                elif name=="acquisition":edge(node,name,producer=entry)
                else:
                    producer,output=b.OWNERS[name];edge(node,name,producer=task_id(source.root_id,producer),output=output)
        edge(terminal,"outcomes."+source.root_id,producer=task_id(source.root_id,"response-score"))
    edge(terminal,"specification",external=specification_input);edge(terminal,"acquisition",producer=entry)
    return tuple(sorted(configs.items())),tuple(sorted(external.values(),key=lambda value:value.input_id)),tuple(sorted(links,key=lambda value:value.edge_id)),tuple(sorted(records.items())),tuple(sorted(files.items()))


def lower(specification,request):
    from .native_utility_bindings import config_phase,operation_declarations
    configs,external,links,records,files=contracts(specification,request)
    declarations={value.capability_key.rsplit(".",1)[-1]:value for value in operation_declarations()}
    root=development_root(specification,request,"study."+specification.specification_id)
    if (request.campaign.objective!=root.question or request.campaign.system_ids!=(root.system.object_id,)
            or request.campaign.world_ids!=(root.world_id,) or request.campaign.target_claim_ids!=tuple(value.claim_id for value in root.claims)):
        raise ValueError("native E2 campaign substitutes its actual scientific question/claims")
    operations=tuple(RecursiveOperationSpec.from_config(node_id=node,selection=declarations[config_phase(config)].registration().selection,
        config_id=config.record_id,config=config,obligation_ids=("obligation."+node+".complete-selected-scope",),resource_budget=request.resources.for_operation(config_phase(config))) for node,config in configs)
    if not request.campaign.budget.contains(ResourceBudget.aggregate(tuple(value.resource_budget for value in operations))):raise ValueError("native E2 budget omits complete task-resource aggregate")
    return RecursiveStudyDraft("draft."+specification.specification_id,root.question,request.campaign,(),(),(),operations,external,links,tuple(node for node,_ in configs),development_study=root),records,files


@dataclass(frozen=True,slots=True)
class NativeUtilityInputs:
    request:r.NativeUtilityRequest|None=None
    files:tuple=()


def bind_inputs(specification,records,*,files=None):
    if set(records)-{"request"}:raise ValueError("native E2 accepts only its own complete declared request")
    request=records.get("request")
    if request is not None:r.validate_request(specification,request)
    allocation=None if request is None else r.utility_allocation(specification,request)
    return PreparedExperimentInputs({} if allocation is None else {"native-utility":allocation},NativeUtilityInputs(request,tuple(sorted((files or {}).items()))))


def prepare(specification,*,execution,method_inputs=None,**_kwargs):
    from .native_utility_bindings import NATIVE
    specification.__post_init__()
    if method_inputs is not None and type(method_inputs) is not NativeUtilityInputs:raise TypeError("native E2 requires its registered exact copied inputs")
    inputs=NativeUtilityInputs() if method_inputs is None else method_inputs
    dependencies=[];request=inputs.request;allocation=draft=None;records=files=design=()
    for name,kind in (("workers",DependencyKind.ENVIRONMENT),("environment_id",DependencyKind.ENVIRONMENT),("source_snapshot",DependencyKind.ENVIRONMENT),("output_root",DependencyKind.STORAGE)):
        if getattr(execution,name) is None:dependencies.append(ExperimentDependency("native-utility.execution."+name.replace("_","-"),kind,"Select explicit "+name+"."))
    if specification.criterion is None:dependencies.append(ExperimentDependency("native-utility.criterion",DependencyKind.SCIENTIFIC_EVIDENCE,"Freeze the actual E2 comparator/effect/numerical/statistical criterion before native prefix contact.","criterion"))
    if request is None:dependencies.append(ExperimentDependency("native-utility.request",DependencyKind.EXTERNAL_INPUT,"Supply the actual separately selected E2 source census, exposure support, pre-contact measurement and resource request.","request"))
    else:
        allocation=r.utility_allocation(specification,request)
        if execution.workers is not None and execution.workers!=request.resources.maximum_parallel_tasks:dependencies.append(ExperimentDependency("native-utility.worker-selection",DependencyKind.ENVIRONMENT,"Workers differ from selected native E2 placement."))
        if specification.criterion is not None:
            draft,records,identities=lower(specification,request);selected=[];available=dict(inputs.files)
            for key,artifact in identities:
                value=available.get(artifact.artifact_id)
                if value is None:dependencies.append(ExperimentDependency("native-utility.file."+artifact.artifact_id,DependencyKind.EXTERNAL_INPUT,"Supply original exact template bytes.",artifact.artifact_id))
                elif value.identity!=artifact:raise ValueError("native E2 template FILE changes original identity")
                else:selected.append((key,value))
            files=tuple(selected);design=((request.record_id,request),)
        if dependencies:draft=None;records=files=()
    count=len(specification.root_ids)
    census=ExperimentCensus((("native-utility",count),),(("native-utility",count if request is not None else 0),),
        tuple(sorted((operation,1 if operation in ("entry","terminal") else count) for operation in r.ALL_PHASES)),
        (("native-response-targets",30*count),("selected-tasks",len(r.PHASES)*count+2),("utility-rows",count)),len(NATIVE)*count)
    return ExperimentPreparation(specification.identity,census,tuple(sorted(dependencies,key=lambda value:value.code)),allocation=allocation,draft=draft,
        input_records=records,execution=execution,specification_record=specification,design_records=design,input_files=files)


def validate_instance(*,specification,allocation,draft,source_records):
    requests=tuple(value for _,value in source_records if type(value) is r.NativeUtilityRequest)
    if len(requests)!=1:raise ValueError("native E2 requires one actual original acquisition request")
    expected,_,_=lower(specification,requests[0])
    if draft!=expected or allocation!=r.utility_allocation(specification,requests[0]):raise ValueError("native E2 instance substitutes its frozen full graph/source census")
