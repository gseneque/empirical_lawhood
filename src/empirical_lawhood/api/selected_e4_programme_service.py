# SPDX-License-Identifier: MPL-2.0
"""One declarative phase over ordinary issued wave and assessment lifecycles.

The immutable full plan fixes all groups before entry. Authored component packets,
original issue/publication custody and execution/recovery records are the state.
This owner creates neither authorities nor a scheduler.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from types import SimpleNamespace
from typing import ClassVar

from empirical_lawhood.api import composite_experiment_programme as programme_source

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as d
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as r
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling,inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord,validate_stable_id,validate_relative_locator
from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest,ArtifactWriteResult,ArtifactProfile,derived_outcome_access
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection,PreparedExperimentFile
from empirical_lawhood.runtime.experiment_programme import ExperimentProgrammeDescriptor
from empirical_lawhood.api.results import RunCampaignRequest,ResumeCampaignRequest,CampaignStatusRequest

MAX_PLAN_BYTES=64*1024**2
PLAN_FILENAME="selected-e4-programme-plan.json"
STATE_FILENAME="selected-e4-programme-authoring.json"


@dataclass(frozen=True,slots=True)
class SelectedE4ComponentRequest(CanonicalRecord):
    """Operational selection of existing controls; fields confer no authority."""
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/component-request"
    component_id:str
    run_id:str
    package_path:str|None
    reveal_authority_id:str
    parent_record_path:str|None
    parent_input_binding_paths:tuple[str,...]

    def __post_init__(self):
        for v in (self.component_id,self.run_id,self.reveal_authority_id):validate_stable_id(v)
        if type(self.parent_input_binding_paths) is not tuple or len(set(self.parent_input_binding_paths))!=len(self.parent_input_binding_paths):
            raise TypeError("selected E4 request needs immutable distinct existing parent input paths")
        for v in (self.package_path,self.parent_record_path,*self.parent_input_binding_paths):
            if v is not None:validate_relative_locator(v)


@dataclass(frozen=True,slots=True)
class SelectedE4ProgrammeRequest(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/programme-request"
    record_id:str
    programme:ObjectIdentity
    components:tuple[SelectedE4ComponentRequest,...]
    collection:d.SelectedE4PhaseCollectionSelection|None

    def __post_init__(self):
        validate_stable_id(self.record_id);r.exact_pin(self.programme,d.SelectedE4ProtectedProgrammePlan)
        if (type(self.components) is not tuple or any(type(v) is not SelectedE4ComponentRequest for v in self.components)
                or tuple(v.component_id for v in self.components)!=tuple(sorted({v.component_id for v in self.components}))):
            raise ValueError("selected E4 programme duplicates or reorders original component selections")
        for v in self.components:v.__post_init__()
        if self.collection is not None:
            if type(self.collection) is not d.SelectedE4PhaseCollectionSelection:raise TypeError("selected E4 needs exact produced-input admissions")
            self.collection.__post_init__()


@dataclass(frozen=True,slots=True)
class SelectedE4ProgrammeAuthoring(CanonicalRecord):
    SCHEMA:ClassVar[str]="empirical-lawhood/matrix-selected-e4/programme-authoring"
    VERSION:ClassVar[str]="3.0.0"
    record_id:str
    programme:ObjectIdentity
    plan_publication:ArtifactWriteResult
    upstream_products:tuple[MatrixSelectedOriginalProduct,...]
    calibration_product:MatrixSelectedOriginalProduct|None
    source_snapshot:ObjectIdentity
    environment_id:str|None
    output_root_id:str
    component_slots:tuple[str,...]
    declaration_publication:ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.record_id);r.exact_pin(self.programme,d.SelectedE4ProtectedProgrammePlan)
        d.validate_component_original_products(self.upstream_products,self.calibration_product)
        if (type(self.plan_publication) is not ArtifactWriteResult
                or self.plan_publication.logical.logical_artifact_id!=self.programme.object_id
                or self.plan_publication.logical.payload_schema!=self.programme.object_schema
                or self.plan_publication.logical.content_sha256!=self.programme.object_fingerprint
                or self.plan_publication.materialization.physical_sha256!=self.programme.object_fingerprint):
            raise ValueError("selected E4 state needs its actual published complete programme plan")
        self.plan_publication.__post_init__()
        from empirical_lawhood.planning.study_issue import ImplementationSourceClosure
        from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
        if (type(self.source_snapshot) is not ObjectIdentity or
                (self.source_snapshot.object_schema,self.source_snapshot.object_version) not in
                {(kind.SCHEMA,kind.VERSION) for kind in (ImplementationSourceClosure,RecursiveImplementationBinding)}):
            raise TypeError("selected E4 authoring needs its exact retained implementation source selection")
        self.source_snapshot.__post_init__()
        validate_stable_id(self.output_root_id)
        if self.environment_id is not None:validate_stable_id(self.environment_id)
        if type(self.component_slots) is not tuple or not self.component_slots or len(set(self.component_slots))!=len(self.component_slots):
            raise ValueError("selected E4 authoring needs exact frozen component slots")
        for v in self.component_slots:validate_stable_id(v)
        if type(self.declaration_publication) is not ArtifactWriteResult:raise TypeError("selected E4 state needs actual original declaration publication")
        self.declaration_publication.__post_init__()

    @property
    def identity(self):return r.pin(self)


def _codecs():
    from empirical_lawhood.api.recursive_operations import operation_catalog
    return operation_catalog()[2]


def _path(writer,directory,name,*,write=False):
    directory=Path(directory)
    if not directory.is_absolute() or any(v.is_symlink() for v in (directory,*directory.parents)):
        raise ValueError("selected E4 requires absolute unlinked operational directory")
    root=Path(writer.root.contract.canonical_path)
    return writer.root.resolve((directory/name).relative_to(root).as_posix(),for_write=write)


def _publish(writer,directory,name,record,*,sealed=False,lineage_parents=()):
    path=_path(writer,directory,name,write=True)
    relative=path.relative_to(Path(writer.root.contract.canonical_path)).as_posix()
    access=derived_outcome_access(OutcomeAccess.EVALUATION_SEALED if sealed else OutcomeAccess.OUTCOME_BLIND,
        *(value.outcome_access for value in lineage_parents))
    ceilings=tuple(value.visibility_ceiling for value in lineage_parents)
    return writer.write(ArtifactWriteRequest(record.identity.object_id,relative,record.SCHEMA,ArtifactProfile.CANONICAL_JSON,
        "application/json",record.identity.object_id,str(Path(relative).parent),record.canonical_bytes(),
        inherited_visibility(ceilings,access),ceilings,access,lineage_parents=lineage_parents))


def _load(writer,directory,name,kind,maximum=MAX_PLAN_BYTES,*,publication=None):
    path=_path(writer,directory,name)
    relative=path.relative_to(Path(writer.root.contract.canonical_path)).as_posix()
    manifest=writer.read_manifest(relative)
    if (manifest.logical.payload_schema!=kind.SCHEMA or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or manifest.logical.media_type!="application/json" or manifest.materialization.size_bytes>maximum
            or manifest.materialization.compression!="none"
            or publication is None and (manifest.logical.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or manifest.logical.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE)
            or publication is not None and (manifest.logical,manifest.materialization)!=(publication.logical,publication.materialization)):
        raise PermissionError("selected E4 operational state changes exact public canonical custody")
    writer.verify_manifest(manifest)
    raw=read_bounded_bytes(path,maximum_bytes=maximum)
    value=decode_canonical_bytes(raw,kind,maximum_bytes=maximum)
    if raw!=value.canonical_bytes() or sha256(raw).hexdigest()!=manifest.logical.content_sha256 or len(raw)!=manifest.materialization.size_bytes:
        raise PermissionError("selected E4 operational state changes exact published bytes")
    return value


def _files(writer,inputs,specification):
    _,_,arrays,_,_=d.component_design(specification,inputs)
    wanted={v.artifact_id:v for _,v in arrays};publications={}
    for publication in inputs.plan.bank.response_selection.template_publications:
        publications[publication.logical.logical_artifact_id]=publication
    if inputs.collection is not None:
        wanted.update((v.artifact_id,v) for v in inputs.collection.observations)
        for artifact in inputs.collection.observations:
            relative="observations/"+artifact.sha256+".json"
            manifest=writer.read_manifest(relative)
            publications[artifact.artifact_id]=SimpleNamespace(logical=manifest.logical,materialization=manifest.materialization)
    result=[]
    for key,artifact in sorted(wanted.items()):
        publication=publications.get(key)
        if publication is None:raise ValueError("selected E4 lacks actual template or generated observation publication: "+key)
        logical,physical=publication.logical,publication.materialization
        if (logical.payload_schema,logical.content_sha256,logical.media_type,physical.size_bytes)!=(artifact.payload_schema,artifact.sha256,artifact.media_type,artifact.size_bytes):
            raise PermissionError("selected E4 source handle substitutes exact actual publication bytes")
        manifest=writer.read_manifest(physical.relative_path);writer.verify_manifest(manifest)
        versions=tuple(v.record_version for v in MATRIX_STORAGE_CODECS if (v.payload_schema,v.media_type)==(artifact.payload_schema,artifact.media_type))
        version=r.SelectedE4WaveObservation.VERSION if artifact.payload_schema==r.SelectedE4WaveObservation.SCHEMA else (versions[0] if len(versions)==1 else None)
        if version is None:raise ValueError("selected E4 file lacks actual installed record version")
        result.append((key,PreparedExperimentFile(artifact,version,writer.root.resolve(physical.relative_path,for_write=False),artifact.size_bytes)))
    return tuple(result)


def _locator(writer,selection,declaration):
    from empirical_lawhood.api.recursive_qualified_parents import _actual_package,_replay_parent_authority
    from empirical_lawhood.api.current_result_custody import authenticate_current_execution_plan
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    package=_actual_package(writer,selection.run_id)
    reveal=ExternalStudyOperationAuthorityStore(writer).load(selection.reveal_authority_id)
    locator=SimpleNamespace(package=r.pin(package,"package_id"),issued_study=r.pin(package.issued_study,"issue_id"),
        execution_authority=r.pin(package.execution_authority,"authority_id"),reveal_authority=r.pin(reveal,"authority_id"))
    # The selected logical ID never supplies authority: replay original live
    # store and actual package before reading any protected product.
    issued,_=_replay_parent_authority(locator,package,writer)
    execution=authenticate_current_execution_plan(package=package,issued=issued,run_id=selection.run_id,writer=writer)
    return r.SelectedE4WaveLocator(selection.component_id,selection.run_id,locator.package,locator.issued_study,
        locator.execution_authority,locator.reveal_authority,r.pin(execution,"execution_plan_id"))


def preflight_selected_e4_component(*,api,selected,request,recover,expected_run_id):
    """Reuse actual no-effect execution validators, never confirmation preview.

    All checks repeat at the real per-component execution boundary. This early
    pass prevents a knowably refused later wave from permitting wave one entry.
    """
    execution=api._execution_service
    if execution is None:raise ValueError("selected E4 requires actual public execution composition")
    if recover:
        package=execution.load_persisted_package(request.run_id)
        run,plan=api._compile_package(package)
    else:
        package,run,plan=api._compile_path(request.path)
    if (package.run_plan_id!=expected_run_id or run.run_plan_id!=expected_run_id
            or r.pin(package.issued_study.candidate,"candidate_id")!=selected.association.candidate):
        raise PermissionError("selected E4 component changes its actual run/candidate")
    at_utc=api._study_issue_clock.now_utc()
    execution._check_identity(package)
    execution._validate_campaign_authorization(package)
    execution._validate_issued_execution_authority(package,at_utc=at_utc)
    execution._validate_issued_reveal_authority(package,reveal_authority_id=request.reveal_authority_id,at_utc=at_utc)
    execution.preexecution_contract_closure(package=package,run_plan=run,execution_plan=plan).require_pass()
    admission=execution.resource_admission(plan,package=package)
    if not admission.admitted:raise ValueError("selected E4 current resource admission refused: "+",".join(admission.reason_codes))
    execution.artifact_plane.root.verify(for_write=True,operation_minimum_free_bytes=plan.minimum_free_bytes)
    # Conditional original-parent operands are authenticated by the same owner.
    api._conditional_execution_records(package=package,parent_record_path=request.parent_record_path,
        parent_input_binding_paths=request.parent_input_binding_paths)


def _new_native_contacts(reports):
    """Sum actual execution deltas; missing counts cannot imply no contact."""
    counts=tuple(report.get("new_native_contact_count") for _,report in reports)
    return sum(counts) if all(type(value) is int and value>=0 for value in counts) else None


class SelectedE4ProgrammeService:
    def __init__(self,*,service,descriptor=None):
        self.service,self.descriptor=service,descriptor
        self.writer=service.artifact_writer

    def _state(self,directory):
        state=_load(self.writer,directory,STATE_FILENAME,SelectedE4ProgrammeAuthoring)
        from .selected_e4_native_preparation import require_selected_e4_original_access,require_selected_e4_plan_access
        require_selected_e4_original_access(self.writer,state.upstream_products,state.calibration_product,
            produced_input_parents=state.plan_publication.logical.lineage_parents)
        plan=_load(self.writer,directory,PLAN_FILENAME,d.SelectedE4ProtectedProgrammePlan,publication=state.plan_publication)
        expected=ExperimentProgrammeDescriptor("programme."+plan.fingerprint(),d.PROGRAMME_PROTOCOL_ID,plan.specification.identity,plan.identity)
        if (self.descriptor!=expected or state.programme!=plan.identity or state.component_slots!=plan.component_ids
                or state.output_root_id!=self.writer.root.contract.storage_root_id
                or state.upstream_products!=plan.evidence.upstream_products
                or state.calibration_product!=plan.evidence.calibration_product
                or state.plan_publication.materialization.relative_path!=_path(self.writer,directory,PLAN_FILENAME).relative_to(
                    self.writer.root.contract.canonical_path).as_posix()):
            raise PermissionError("selected E4 descriptor/plan/source state changes frozen complete programme")
        require_selected_e4_plan_access(self.writer,plan)
        d.validate_produced_publication(state.plan_publication,plan,plan.evidence.produced_input_parents)
        d.validate_produced_publication(state.declaration_publication,plan.declaration,plan.evidence.produced_input_parents)
        from empirical_lawhood.api.selected_e4_native_runtime import authenticate_publication
        authenticate_publication(self.writer,state.plan_publication,plan)
        authenticate_publication(self.writer,state.declaration_publication,plan.declaration)
        require_selected_e4_plan_access(self.writer,plan)
        return plan,state

    def _request(self,path,plan,*,request=None):
        if path is not None and request is not None:
            raise ValueError('select one exact E4 operational request record or path')
        if path is None and request is None:return None
        if path is not None:
            raw=read_bounded_bytes(Path(path),maximum_bytes=MAX_PLAN_BYTES)
            request=decode_canonical_bytes(raw,SelectedE4ProgrammeRequest,maximum_bytes=MAX_PLAN_BYTES)
            if raw!=request.canonical_bytes():
                raise ValueError('selected E4 request changes its exact canonical bytes')
        if type(request) is not SelectedE4ProgrammeRequest:
            raise TypeError('selected E4 operation requires its exact typed current request')
        request.__post_init__()
        if request.programme!=plan.identity or set(v.component_id for v in request.components)-set(plan.component_ids):
            raise ValueError("selected E4 operational selection changes full programme or component census")
        return request

    def _author_component(self,*,directory,plan,state,declaration_publication,component,collection=None,
            _admitted_source=None):
        specification=d.component_specification(plan,component)
        source_snapshot=programme_source.component_source_snapshot(self.service.project_root,state.source_snapshot,d.component_prospective_spec_id(specification),
            _admitted_source=_admitted_source)
        selected=d.SelectedE4NativeComponentInputs("component-inputs."+plan.plan_id+"."+component,
            plan.identity,state.plan_publication,state.upstream_products,state.calibration_product,component,declaration_publication,collection)
        resolved=d.resolve_component_inputs(selected,plan)
        wrapper=d.SelectedE4PreparedComponentInputs(selected,resolved,_files(self.writer,resolved,specification))
        groups=plan.declaration.programme.group_ids if specification.wave_id is None else plan.declaration.wave(specification.wave_id).group_ids
        preparation=d.prepare_component(specification,scientific_inputs={plan.declaration.bank_phase.lower():d.programme_allocation(plan,group_ids=groups)},
            execution=ExecutionSelection(workers=plan.declaration.maximum_parallel_tasks,environment_id=state.environment_id,
                source_snapshot=source_snapshot,output_root=self.writer.root.contract.canonical_path),method_inputs=wrapper)
        return self.service.author(preparation=preparation,output_dir=Path(directory)/"components"/component)

    def retain_unentered(self,*,preparation,output_dir):
        """Retain the actual adverse DEV decision without issuing/entering CAL."""
        from empirical_lawhood.runtime.experiment_preparation import DependencyKind
        if (tuple((value.code,value.kind) for value in preparation.dependencies)
                != (("matrix.selected-e4.revision-eligibility",DependencyKind.SCIENTIFIC_EVIDENCE),)
                or type(preparation.programme) is not d.SelectedE4ProtectedProgrammePlan
                or preparation.execution is None
                or any(getattr(preparation.execution,name) is None for name in
                    ("workers","environment_id","source_snapshot","output_root"))
                or preparation.execution.output_root!=self.writer.root.contract.canonical_path):
            raise ValueError("Selected E4 unentered retention permits only its actual revision-eligibility decision")
        plan=preparation.programme
        from .selected_e4_native_preparation import require_selected_e4_plan_access
        require_selected_e4_plan_access(self.writer,plan)
        plan.__post_init__()
        # Reopen the ordinary DEV products before any operational metadata write.
        if self._unentered(plan) is None:
            raise PermissionError("Selected E4 unentered retention requires the actual nontriggered/unevaluable DEV decision")
        return self.author(preparation=preparation,output_dir=output_dir)

    def author(self,*,preparation,output_dir):
        from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
        from empirical_lawhood.api.composite_experiment_programme import write_experiment_programme_descriptor
        if type(preparation.programme) is not d.SelectedE4ProtectedProgrammePlan or preparation.execution is None:
            raise TypeError("selected E4 author requires full typed programme and actual source selection")
        plan=preparation.programme
        from .selected_e4_native_preparation import require_selected_e4_plan_access
        require_selected_e4_plan_access(self.writer,plan)
        plan.__post_init__()
        if preparation.execution.workers!=plan.declaration.maximum_parallel_tasks:raise ValueError("selected E4 author changes declared concurrency")
        admitted_source=programme_source.preflight_programme_source(self.service.project_root,preparation.execution.source_snapshot)
        directory=preflight_authoring_output_directory(directory=Path(output_dir),repo_root=self.service.project_root,artifact_writer=self.writer)
        parents=plan.evidence.produced_input_parents
        require_selected_e4_plan_access(self.writer,plan)
        plan_publication=_publish(self.writer,directory,PLAN_FILENAME,plan,lineage_parents=parents)
        require_selected_e4_plan_access(self.writer,plan)
        publication=_publish(self.writer,directory,"native-declaration.json",plan.declaration,lineage_parents=parents)
        state=SelectedE4ProgrammeAuthoring("authoring."+plan.fingerprint(),plan.identity,plan_publication,
            plan.evidence.upstream_products,plan.evidence.calibration_product,preparation.execution.source_snapshot,
            preparation.execution.environment_id,self.writer.root.contract.storage_root_id,plan.component_ids,publication)
        _publish(self.writer,directory,STATE_FILENAME,state)
        descriptor=ExperimentProgrammeDescriptor("programme."+plan.fingerprint(),d.PROGRAMME_PROTOCOL_ID,plan.specification.identity,plan.identity)
        write_experiment_programme_descriptor(service=self.service,directory=directory,descriptor=descriptor)
        unentered=self._unentered(plan)
        if unentered is not None:return {**unentered,"authoring_dir":str(directory),"programme_descriptor":descriptor.to_document()}
        components=tuple(self._author_component(directory=directory,plan=plan,state=state,declaration_publication=publication,
            component=wave.wave_id,_admitted_source=admitted_source) for wave in plan.declaration.programme.waves)
        return {"programme":descriptor.to_document(),"authoring_dir":str(directory),"components":components,
            "assigned_groups":len(plan.declaration.programme.group_ids),"assigned_cases":len(plan.declaration.programme.cases),
            "assessment":{"state":"AWAITING_ACTUAL_WAVE_PRODUCTS_AND_PRODUCED_INPUT_ADMISSIONS"}}

    def _unentered(self,plan):
        if plan.declaration.models is not None or (plan.declaration.bank_phase != 'CALIBRATION'
                and plan.declaration.decision.relation_fit is None):
            return None
        from empirical_lawhood.api.selected_e4_native_runtime import development_products
        (development,nomination),(original,frozen)=development_products(self.writer,
            ((plan.evidence.development_nomination,'revision-fit'),(plan.evidence.development_freeze,'revision-freeze')),_codecs())
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PublicRevisionDecision,validate_phase_separation
        decision=SelectedE4PublicRevisionDecision.from_products(development,nomination,frozen,record_id=plan.declaration.decision.record_id)
        validate_phase_separation(development,plan.declaration.programme)
        if original!=development or decision!=plan.declaration.decision or decision.fit_available:
            raise PermissionError("selected E4 unentered CAL changes actual original DEV branch")
        return {"programme":plan.identity.to_document(),"state":"UNENTERED_REVISION_"+decision.trigger_disposition,
            "assigned_groups":plan.declaration.programme.group_ids,"assigned_cases":tuple(v.root_id for v in plan.declaration.programme.cases),
            "scientific_completion":"NOT_ESTABLISHED","scientific_qualification":"NOT_ESTABLISHED","new_native_contact_count":0,
            "structure":{"state":"NOT_ENTERED","scientific_completion":"NOT_ESTABLISHED","new_native_contact_count":0}}

    def _structure(self,*,directory,plan,state,request,produce,maximum_parallel_tasks=None):
        from empirical_lawhood.api.selected_e4_structure import produce_selected_e4_structure,read_selected_e4_structure,structure_projection
        from empirical_lawhood.kernel.decoding import decode_canonical_record
        rows=() if request is None else tuple(value for value in request.components if value.component_id!=d.ASSESSMENT_COMPONENT_ID)
        locators=tuple(_locator(self.writer,value,plan.declaration) for value in rows)
        if tuple(value.wave_id for value in locators)!=tuple(value.wave_id for value in plan.declaration.programme.waves):
            raise PermissionError("ordinary E4 structure requires every actual original wave and current reveal")
        kwargs=dict(directory=directory,artifact_writer=self.writer,programme=plan.declaration.programme,
            bank=plan.bank,choices=plan.structure,secondary_readout=plan.secondary_readout,resources=plan.structural_resources,
            declaration=plan.declaration,waves=locators,campaign=plan.declaration.root.campaign)
        if produce:
            result=produce_selected_e4_structure(**kwargs,project_root=self.service.project_root,
                maximum_parallel_tasks=maximum_parallel_tasks,
                environment_id=state.environment_id)
        else:
            result=read_selected_e4_structure(**kwargs)
        observations=tuple(decode_canonical_record(value,r.SelectedE4WaveObservation)
            for value in result["original_wave_observations"])
        if tuple(value.wave_id for value in observations)!=tuple(value.wave_id for value in locators):
            raise PermissionError("ordinary E4 structure changes its authenticated original observation census")
        return observations,{**result["original_response"],"structure":structure_projection(result)}

    def _publish_observations(self,plan,observations,collection):
        if tuple(v.observation for v in collection.evidence.waves)!=tuple(v.identity for v in observations):
            raise PermissionError("selected E4 produced-input admissions change actual all-wave observations")
        for value,artifact in zip(observations,collection.observations,strict=True):
            if (value.identity.object_id,value.SCHEMA,value.fingerprint(),len(value.canonical_bytes()))!=(artifact.artifact_id,artifact.payload_schema,artifact.sha256,artifact.size_bytes):
                raise PermissionError("selected E4 produced source changes actual authenticated observation bytes")
            _publish(self.writer,Path(self.writer.root.contract.canonical_path),"observations/"+value.fingerprint()+".json",value,sealed=True,
                lineage_parents=plan.evidence.produced_input_parents)

    def _preflight_component(self,*,directory,selected,maximum_parallel_tasks,confirmed,recover):
        path=Path(directory)/"components"/selected.component_id
        selected_context,api=self.service._prospective_context(path,maximum_parallel_tasks=maximum_parallel_tasks,
            reveal_authority_id=selected.reveal_authority_id,lifecycle="recover" if recover else "run",
            recovery_run_id=selected.run_id if recover else None)
        kwargs=self._request_kwargs(selected)
        value=(ResumeCampaignRequest(selected.run_id,confirmed=confirmed,**kwargs) if recover else
            RunCampaignRequest(self.writer.root.resolve(selected.package_path,for_write=False),confirmed=confirmed,
                reveal_authority_id=selected.reveal_authority_id,parent_record_path=kwargs["parent_record_path"],
                parent_input_binding_paths=kwargs["parent_input_binding_paths"]))
        preflight_selected_e4_component(api=api,selected=selected_context,request=value,recover=recover,
            expected_run_id=selected.run_id)
        return path,value

    def _operation(self,*,directory,maximum_parallel_tasks,programme_request_path,confirmed,recover,request=None,result_read_scope='FULL'):
        if result_read_scope not in ('FULL', 'EXECUTION_RECORDS'):
            raise ValueError('selected E4 operation requires a full or execution-record result scope')
        plan,state=self._state(directory);request=self._request(programme_request_path,plan,request=request)
        if type(confirmed) is not bool or maximum_parallel_tasks!=plan.declaration.maximum_parallel_tasks:
            raise ValueError("selected E4 operation requires exact declared concurrency and explicit confirmation")
        unentered=self._unentered(plan)
        if unentered is not None:return unentered
        rows={} if request is None else {v.component_id:v for v in request.components}
        missing=tuple(component for component in plan.component_ids if component not in rows)
        # All native wave authority requests must be selected before any contact;
        # the causally later assessment remains a declared pending slot.
        wave_ids=tuple(v.wave_id for v in plan.declaration.programme.waves)
        if any(v not in rows for v in wave_ids):
            return {"programme":plan.identity.to_document(),"state":"DEPENDENCIES_REQUIRED","missing_components":missing,
                "new_native_contact_count":0}
        if not recover:
            for component,selected in rows.items():
                if selected.package_path is None:
                    raise ValueError("selected E4 run lacks actual issued package path: "+component)
        from empirical_lawhood.api.current_result_custody import current_result_package_present
        def retained(selected):
            return recover or current_result_package_present(writer=self.writer,run_id=selected.run_id)
        prepared=[]
        for component in wave_ids:
            continuing=retained(rows[component])
            path,value=self._preflight_component(directory=directory,selected=rows[component],
                maximum_parallel_tasks=maximum_parallel_tasks,confirmed=confirmed,recover=continuing)
            prepared.append((component,path,value,continuing))
        assessment=None
        if d.ASSESSMENT_COMPONENT_ID in rows:
            path=Path(directory)/"components"/d.ASSESSMENT_COMPONENT_ID
            if not path.exists():
                raise FileNotFoundError("selected E4 assessment must be authored before selecting its issued authority: "+str(path))
            continuing=retained(rows[d.ASSESSMENT_COMPONENT_ID])
            path,value=self._preflight_component(directory=directory,selected=rows[d.ASSESSMENT_COMPONENT_ID],
                maximum_parallel_tasks=maximum_parallel_tasks,confirmed=confirmed,recover=continuing)
            assessment=(path,value,continuing)
        if not confirmed:return {"programme":plan.identity.to_document(),"state":"CONFIRMATION_REQUIRED","components":wave_ids,"missing_components":missing}
        reports=[]
        for component,path,value,continuing in prepared:
            operation=self.service.recover if continuing else self.service.run
            report=operation(directory=path,maximum_parallel_tasks=maximum_parallel_tasks,request=value)
            reports.append((component,report))
            if report.get("status")!="SUCCEEDED":
                from empirical_lawhood.api.selected_e4_native_read import read_selected_e4_wave
                try:
                    # A complete adverse terminal is retained evidence, never
                    # permission to retry native work or discard assigned units.
                    read_selected_e4_wave(writer=self.writer,declaration=plan.declaration,
                        locator=_locator(self.writer,rows[component],plan.declaration),codecs=_codecs())
                except (ValueError,PermissionError,OSError,KeyError):
                    return {"programme":plan.identity.to_document(),"state":"COMPONENT_REFUSED_OR_INCOMPLETE",
                        "components":tuple(reports),"missing_components":missing,"new_native_contact_count":_new_native_contacts(reports)}
        observations,wave_state=self._structure(directory=directory,plan=plan,state=state,request=request,
            produce=True,maximum_parallel_tasks=maximum_parallel_tasks)
        wave_state={**wave_state,"new_native_contact_count":_new_native_contacts(reports)}
        if request.collection is None:
            return {**wave_state,"state":"AWAITING_PRODUCED_INPUT_ADMISSIONS_AND_ASSESSMENT_AUTHORITY","components":tuple(reports),"missing_components":missing}
        collection=request.collection
        if (collection.evidence.declaration!=plan.declaration.identity
                or tuple(v.locator for v in collection.evidence.waves)!=tuple(_locator(self.writer,rows[v],plan.declaration) for v in wave_ids)):
            raise PermissionError("selected E4 collection changes actual original all-wave authority/custody")
        component=d.ASSESSMENT_COMPONENT_ID;path=Path(directory)/"components"/component
        admitted_source=None
        if assessment is None and not path.exists():
            admitted_source=programme_source.preflight_programme_source(self.service.project_root,state.source_snapshot)
        self._publish_observations(plan,observations,collection)
        if assessment is None:
            if not path.exists():
                self._author_component(directory=directory,plan=plan,state=state,declaration_publication=state.declaration_publication,
                    component=component,collection=collection,_admitted_source=admitted_source)
            return {**wave_state,"state":"ASSESSMENT_AUTHORITY_REQUIRED","components":tuple(reports),"assessment_directory":str(path)}
        path,value,continuing=assessment
        report=(self.service.recover if continuing else self.service.run)(directory=path,maximum_parallel_tasks=maximum_parallel_tasks,request=value)
        assessment_state="ASSESSMENT_RETAINED" if report.get("status")=="SUCCEEDED" else "ASSESSMENT_REFUSED_OR_INCOMPLETE"
        # Structure already returned the complete original wave read. Read only
        # the new assessment here, so the parent need not replay every wave.
        scientific_report = (self.service.read(directory=path, request=CampaignStatusRequest(rows[d.ASSESSMENT_COMPONENT_ID].run_id),
            reveal_authority_id=rows[d.ASSESSMENT_COMPONENT_ID].reveal_authority_id)
            if report.get("status")=="SUCCEEDED" and result_read_scope == 'FULL' else report)
        return {**wave_state,"state":assessment_state,"components":tuple(reports),"assessment":scientific_report,
            "new_native_contact_count":_new_native_contacts((*reports,(component,report))),
            **({'read_scope':'EXECUTION_RECORDS','execution_complete':report.get('status')=='SUCCEEDED',
                'operational_terminal':'AUTHENTICATED' if report.get('status')=='SUCCEEDED' else 'INCOMPLETE'}
                if result_read_scope == 'EXECUTION_RECORDS' else {}),
            "scientific_completion":"ASSESSMENT_RETAINED" if scientific_report.get("status")=="SUCCEEDED"
                and scientific_report.get("scientific_result") is not None else "NOT_ESTABLISHED",
            "scientific_qualification":"NOT_ESTABLISHED"}

    def _request_kwargs(self,value):
        path=lambda v:None if v is None else self.writer.root.resolve(v,for_write=False)
        return {"reveal_authority_id":value.reveal_authority_id,"parent_record_path":path(value.parent_record_path),
            "parent_input_binding_paths":tuple(path(v) for v in value.parent_input_binding_paths)}

    def run(self,*,directory,maximum_parallel_tasks,programme_request_path=None,confirmed=False,request=None,result_read_scope='FULL'):
        return self._operation(directory=directory,maximum_parallel_tasks=maximum_parallel_tasks,
            programme_request_path=programme_request_path,confirmed=confirmed,recover=False,request=request,result_read_scope=result_read_scope)

    def recover(self,*,directory,maximum_parallel_tasks,programme_request_path=None,confirmed=False,request=None,result_read_scope='FULL'):
        return self._operation(directory=directory,maximum_parallel_tasks=maximum_parallel_tasks,
            programme_request_path=programme_request_path,confirmed=confirmed,recover=True,request=request,result_read_scope=result_read_scope)

    def read_execution(self, *, directory, programme_request_path=None, request=None):
        """Inspect every retained component without reconstructing wave outcomes."""
        from .selected_e4_structure import read_structural_execution
        from .selected_e4_access import SelectedE4CurrentAccess
        plan, _ = self._state(directory)
        request = self._request(programme_request_path, plan, request=request)
        unentered = self._unentered(plan)
        if unentered is not None:
            return {**unentered, 'read_scope':'EXECUTION_RECORDS','execution_complete':False}
        rows = {} if request is None else {row.component_id:row for row in request.components}
        reports = []
        for component in plan.component_ids:
            selected = rows.get(component)
            if selected is None:
                reports.append((component, {'state':'RUN_SELECTION_REQUIRED','execution_complete':False}))
            else:
                report = self.service.read_execution(directory=Path(directory)/'components'/component,
                    request=CampaignStatusRequest(selected.run_id), reveal_authority_id=selected.reveal_authority_id)
                reports.append((component, report))
        structure = {'state':'NOT_ENTERED','execution_complete':False}
        child = Path(directory)/'structure'/'analysis'
        wave_ids = tuple(wave.wave_id for wave in plan.declaration.programme.waves)
        if (child.exists() or child.is_symlink()) and all(value in rows for value in wave_ids):
            locators = tuple(_locator(self.writer, rows[value], plan.declaration) for value in wave_ids)
            structure = read_structural_execution(directory=directory, artifact_writer=self.writer,
                programme=plan.declaration.programme, bank=plan.bank, choices=plan.structure,
                secondary_readout=plan.secondary_readout, resources=plan.structural_resources,
                campaign=plan.declaration.root.campaign, declaration=plan.declaration,
                current_access=SelectedE4CurrentAccess(locators))
        complete = structure.get('execution_complete') is True and all(
            report.get('execution_complete') is True for _, report in reports)
        return {'programme':plan.identity.to_document(),'read_scope':'EXECUTION_RECORDS',
            'execution_complete':complete,'operational_terminal':'AUTHENTICATED' if complete else 'INCOMPLETE',
            'state':'ASSESSMENT_RETAINED' if complete else 'INCOMPLETE', 'components':tuple(reports),
            'structure':structure,'scientific_completion':'DEFERRED_TO_FULL_READ',
            'scientific_qualification':'NOT_ESTABLISHED','new_native_contact_count':0}

    def read(self,*,directory,allow_partial=False,programme_request_path=None,request=None):
        if type(allow_partial) is not bool:raise TypeError("selected E4 read requires explicit partial selection")
        plan,state=self._state(directory);request=self._request(programme_request_path,plan,request=request)
        if allow_partial:
            return {"programme":plan.identity.to_document(),"state":"UNASSESSED","assigned_groups":plan.declaration.programme.group_ids,
                "assigned_cases":tuple(v.root_id for v in plan.declaration.programme.cases),"new_native_contact_count":0}
        unentered=self._unentered(plan)
        if unentered is not None:return unentered
        observations,report=self._structure(directory=directory,plan=plan,state=state,request=request,produce=False)
        rows={} if request is None else {v.component_id:v for v in request.components}
        assessment=rows.get(d.ASSESSMENT_COMPONENT_ID)
        if assessment is None:return {**report,"scientific_completion":"NOT_ESTABLISHED","assessment":None}
        result=self.service.read(directory=Path(directory)/"components"/d.ASSESSMENT_COMPONENT_ID,
            request=CampaignStatusRequest(assessment.run_id),reveal_authority_id=assessment.reveal_authority_id)
        return {**report,"assessment":result,"scientific_completion":"ASSESSMENT_RETAINED" if result.get("status")=="SUCCEEDED" else "NOT_ESTABLISHED"}


def selected_e4_programme_service(*,service,descriptor=None):
    return SelectedE4ProgrammeService(service=service,descriptor=descriptor)
