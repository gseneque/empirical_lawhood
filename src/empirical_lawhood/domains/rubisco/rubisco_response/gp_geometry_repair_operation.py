# SPDX-License-Identifier: MPL-2.0
"""Constructed-atom repair through the existing registered native lifecycle."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import resource
import time
import traceback
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import RAW_MAGIC, _ChunkReader, publish_directory, publish_record, uncompressed_archive_chunks, directory_census
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_roster import json_output, raw_output
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.execution.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition, NativeSubworkRoster, NativeSubworkState, invoke_native_subwork, require_native_completion_receipt
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork
from empirical_lawhood.execution.recursive_handoff import RecursiveImplementationBinding
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair import GEOMETRY_ID, REPAIR_INPUT_TYPES, GpAmberFragmentRepairInput, GpCarboxylateRepairInput, GpGeometryRepairInput
from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import _absolute
from empirical_lawhood.adapters.rubisco.rubisco_response.construction_engine import authenticate_numeric_engine
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_assessment import GpAmberFragmentRepairAssessment, GpCarboxylateRepairAssessment, GpGeometryRepairAssessment, assess_geometry_repair, repair_assessment_files, read_initial_terminal_geometry, read_amber_fragment_initialization
from empirical_lawhood.domains.rubisco.rubisco_response.gp_terminal_geometry import INITIAL_REJECTION, TERMINAL_GEOMETRY_FILE, require_initial_terminal_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import authenticate_engine
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


CAPABILITY="rubisco-response.repair-gp-constructed-geometry"
CARBOXYLATE_CAPABILITY="rubisco-response.refine-gp-glu213-geometry"
AMBER_FRAGMENT_CAPABILITY="rubisco-response.refine-gp-terminal-fragment-geometry"
UNIT="unit.gp-original-1bwv-assembly"
MAX_INPUT=64*2**20
BUDGET=ResourceBudget(8,8*2**30,0,None,512*2**20,2*2**30)


def repair_capability(source):
    if type(source) is GpAmberFragmentRepairInput:
        return AMBER_FRAGMENT_CAPABILITY
    return CARBOXYLATE_CAPABILITY if type(source) is GpCarboxylateRepairInput else CAPABILITY


REPAIR_REVISIONS = {
    GpGeometryRepairInput.VERSION: (CAPABILITY, GpGeometryRepairAssessment),
    GpCarboxylateRepairInput.VERSION: (CARBOXYLATE_CAPABILITY, GpCarboxylateRepairAssessment),
    GpAmberFragmentRepairInput.VERSION: (AMBER_FRAGMENT_CAPABILITY, GpAmberFragmentRepairAssessment),
}


@dataclass(frozen=True, slots=True)
class GpGeometryRepairConfig(CanonicalRecord):
    SCHEMA: ClassVar[str]="empirical-lawhood/rubisco-response/gp-geometry-repair-config"
    VERSION: ClassVar[str] = "2.0.0"
    config_id: str
    source: GpGeometryRepairInput | GpCarboxylateRepairInput | GpAmberFragmentRepairInput
    implementation: RecursiveImplementationBinding
    work_directory: str
    provenance: NumericalProducingProvenance

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if type(self.source) not in REPAIR_INPUT_TYPES:
            raise ValueError("geometry repair changes its original selected input revision")
        for row,kind in ((self.implementation,RecursiveImplementationBinding),
                         (self.provenance,NumericalProducingProvenance)):exact(row,kind)
        _absolute(self.work_directory)
        if any(getattr(self.provenance,name)!=getattr(self.implementation,name) for name in (
                "package_sources","code_sources_sha256","dependency_lock_sha256","observed_git_head","observed_checkout_clean")):
            raise ValueError("geometry repair changes its actual selected producing source")

    @property
    def identity(self):return ObjectIdentity.from_record(self.config_id,self)


@dataclass(frozen=True, slots=True)
class GpGeometryRepairReturn(CanonicalRecord):
    SCHEMA: ClassVar[str]="empirical-lawhood/rubisco-response/gp-geometry-repair-return"
    source: ObjectIdentity
    files: DurableRawFileCensus
    error: str | None

    def __post_init__(self):
        exact(self.source,ObjectIdentity);exact(self.files,DurableRawFileCensus)
        if self.error is not None and (type(self.error) is not str or not self.error):
            raise ValueError("geometry repair loses its actual native error")


@dataclass(frozen=True, slots=True)
class GpGeometryRepairResult(CanonicalRecord):
    SCHEMA: ClassVar[str]="empirical-lawhood/rubisco-response/gp-geometry-repair-result"
    result_id: str
    returned: GpGeometryRepairReturn
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt
    assessment: GpGeometryRepairAssessment | GpCarboxylateRepairAssessment | GpAmberFragmentRepairAssessment | None
    assessment_error: str | None

    def __post_init__(self):
        validate_stable_id(self.result_id)
        for row,kind in ((self.returned,GpGeometryRepairReturn),(self.definition,NativeSubworkDefinition),
                (self.completion,NativeSubworkCompletion),(self.receipt,CanonicalTaskReceipt)):exact(row,kind)
        require_native_completion_receipt(self.completion,self.receipt,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
        revision = REPAIR_REVISIONS.get(self.returned.source.object_version, (CAPABILITY, GpGeometryRepairAssessment))
        if (self.returned.source.object_schema != GpGeometryRepairInput.SCHEMA
                or self.definition.operation_id!=revision[0] or self.definition.subwork_id!=GEOMETRY_ID
                or self.definition.configuration!=self.returned.source or self.completion.definition!=self.definition.identity
                or self.completion.operational_status is not (OperationalStatus.SUCCEEDED if self.returned.error is None else OperationalStatus.FAILED)):
            raise ValueError("geometry repair changes its actual native source/completion")
        logical_id=self.receipt.task_id+".output.repair.return"
        logical=tuple(r for r in self.receipt.output_logical_artifacts if r.logical_artifact_id==logical_id)
        physical=tuple(r for r in self.receipt.output_materializations if r.logical_artifact_id==logical_id)
        raw=self.returned.canonical_bytes()
        if (len(logical)!=1 or len(physical)!=1 or logical[0].payload_schema!=GpGeometryRepairReturn.SCHEMA
                or logical[0].content_sha256!=sha256(raw).hexdigest()
                or (physical[0].physical_sha256,physical[0].size_bytes)!=(sha256(raw).hexdigest(),len(raw))):
            raise ValueError("geometry repair substitutes its receipted original native return")
        if self.assessment is not None:
            exact(self.assessment, revision[1])
            expected={r.relative_path:r.sha256 for r in self.returned.files.files}
            if (self.returned.error is not None or self.assessment_error is not None or self.assessment.source!=self.returned.source
                    or any(expected.get(GEOMETRY_ID+"/"+name)!=digest for name,digest in self.assessment.file_sha256s)):
                raise ValueError("geometry repair assessment changes its actual successful raw operands")
        if self.assessment_error is not None and (type(self.assessment_error) is not str or not self.assessment_error):
            raise ValueError("geometry repair loses its actual assessment diagnostic")


def native_input_records(config):
    return (("native-provenance",config.provenance.identity,config.provenance),
            ("native-source",config.source.identity,config.source))


def operands(config):
    return tuple(sorted((config.identity,config.source.identity,config.source.parent.identity,
        config.provenance.identity),key=lambda r:r.object_id))


def slots(config):return ("native.constructed-gp-repair."+config.fingerprint(),)


def native_work(context,config,parent):
    outputs=(json_output("files.census",DurableRawFileCensus),raw_output("files.raw"),json_output("repair.return",GpGeometryRepairReturn))
    sources=tuple(sorted((config.identity,config.source.identity,config.provenance.identity),key=lambda r:r.object_id))
    definition=NativeSubworkDefinition(GEOMETRY_ID,repair_capability(config.source),parent,config.source.identity,sources,
        config.implementation.code_sources_sha256,config.implementation.dependency_lock_sha256,
        tuple(sorted(p.materialization_id for p in context.input_ports)),(),outputs)
    roster=NativeSubworkRoster("selected.native-subwork",parent,(definition.identity,))
    return PreparedNativeWork(parent,(UNIT,),slots(config),(definition,),(roster,))


def _decode(context):
    declaration=operation_declaration(carboxylates=context.task_id == CARBOXYLATE_CAPABILITY,
        amber_fragments=context.task_id == AMBER_FRAGMENT_CAPABILITY).manifest()
    if (context.task_id!=declaration.capability_key or context.permissions!=declaration.permissions or context.resource_budget!=BUDGET
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or len(context.input_ports)!=3):
        raise ValueError("geometry repair changes its complete task/input contract")
    received={}
    for port in context.input_ports:
        if (port.kind is not WorkerInputKind.EXTERNAL or port.media_type!="application/json" or port.size_bytes>MAX_INPUT
                or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("geometry repair changes a selected direct exposed input")
        raw=port.read(MAX_INPUT);key=(port.payload_schema,sha256(raw).hexdigest())
        if key in received:raise ValueError("geometry repair duplicates a direct native input")
        received[key]=(port,raw)
    selected=tuple(value for (schema,_),value in received.items() if schema==GpGeometryRepairConfig.SCHEMA)
    if len(selected)!=1:raise ValueError("geometry repair lacks its unique complete configuration")
    port,raw=selected[0]
    config=decode_canonical_bytes(raw,GpGeometryRepairConfig,maximum_bytes=MAX_INPUT)
    if context.task_id != repair_capability(config.source):
        raise ValueError("geometry repair changes its scientific protocol or original operation selection")
    if (config.config_id,config.fingerprint(),port.artifact_id)!=(context.config.config_id,context.config.content_sha256,context.config.artifact_id):
        raise ValueError("geometry repair substitutes its selected configuration")
    expected={(config.SCHEMA,config.fingerprint()):config}
    expected.update({(pin.object_schema,pin.object_fingerprint):record for _,pin,record in native_input_records(config)})
    if set(received)!=set(expected) or any(received[key][1]!=record.canonical_bytes() for key,record in expected.items()):
        raise ValueError("geometry repair substitutes its exact direct native input census")
    return config


def prepare_native_work(*,runner,context,expected_parent):
    if type(runner) is not GpGeometryRepairRunner or runner.manifest.capability_key != context.task_id:
        raise ValueError("geometry repair needs its installed native owner")
    return native_work(context,_decode(context),expected_parent)


def read_repair_files(native_subwork,definition,returned, *, required_files=None):
    """Authenticate the entire native archive, retaining the assessor operands."""
    assessment_files = repair_assessment_files(returned.source) if required_files is None else required_files
    if sum(r.byte_count for r in returned.files.files)>2*2**30:
        raise ValueError("geometry repair raw archive exceeds its selected output budget")
    chunks=native_subwork.iter_completed_output(definition,"files.raw")
    reader=_ChunkReader(uncompressed_archive_chunks(chunks))
    try:
        if reader.take(len(RAW_MAGIC))!=RAW_MAGIC:raise ValueError("geometry repair raw format changed")
        size=int.from_bytes(reader.take(8),"big")
        if not 0<size<=2**20:raise ValueError("geometry repair census exceeds its bounded record size")
        header=reader.take(size)
        census=decode_canonical_bytes(header,DurableRawFileCensus,maximum_bytes=2**20)
        if census!=returned.files or header!=b"".join(native_subwork.iter_completed_output(definition,"files.census")):
            raise ValueError("geometry repair substitutes its original complete raw census")
        files={}
        for row in census.files:
            path=PurePosixPath(row.relative_path)
            if path.parts!=(GEOMETRY_ID,path.name):raise ValueError("geometry repair changes its selected unit directory")
            if path.name == "terminal-fragments.json":
                from .terminal_fragment_placement import MAXIMUM_BUNDLE_BYTES
                if row.byte_count > MAXIMUM_BUNDLE_BYTES:
                    raise ValueError("terminal fragment receipt exceeds its authored ceiling")
            remaining=row.byte_count;digest=sha256();parts=[]
            while remaining:
                block=reader.take(min(remaining,2**20));remaining-=len(block);digest.update(block)
                if path.name in assessment_files:parts.append(block)
            if digest.hexdigest()!=row.sha256:raise ValueError("geometry repair original native file bytes changed")
            if path.name in assessment_files:files[path.name]=b"".join(parts)
        reader.finish()
        if set(files)!=set(assessment_files):raise ValueError("geometry repair lacks a complete native endpoint")
        return files
    finally:
        close=getattr(chunks,"close",None)
        if close is not None:close()


def _read_failed_fragment(source, files, names, native_error):
    from .amber_construction_admission import _document
    from .terminal_fragment_placement import METHOD, TerminalCandidateRejected, replay_terminal_fragments
    candidate_error = "TerminalCandidateRejected: " in native_error.rstrip().rpartition("\n")[2]
    if "terminal-fragments.json" not in files:
        if candidate_error or "initialized-heavy.pdb" in names:
            raise ValueError("failed fragment repair omits the source-bound records for work already entered")
        return
    bundle = _document(files["terminal-fragments.json"])
    if (bundle.get("method") != METHOD or bundle.get("source") != source.identity.to_document()
            or bundle.get("amber_engine") != source.amber_engine.identity.to_document()
            or bundle.get("numerical_engine") != source.numeric_engine.fingerprint()):
        raise ValueError("failed fragment repair changes the selected source or engines")
    refusal = bundle.get("refusal")
    if refusal is None:
        if candidate_error:
            raise ValueError("failed fragment repair omits its candidate refusal")
        if "initialization.json" in files:
            read_amber_fragment_initialization(source, files, _document(files["initialization.json"]))
        return
    if (type(refusal) is not dict or type(refusal.get("error_type")) is not str or type(refusal.get("message")) is not str
            or not native_error.rstrip().endswith(refusal["error_type"] + ": " + refusal["message"])
            or names - {"terminal-fragments.json", "terminal-fragments.pending", "native-error.txt"}):
        raise ValueError("failed fragment repair substitutes its original refusal or subsequent work")
    if not candidate_error:
        if "candidate_diagnostics" in refusal:
            raise ValueError("partial fragment work cannot report a completed candidate")
        return
    try:
        replay_terminal_fragments(source, files["terminal-fragments.json"])
    except TerminalCandidateRejected as error:
        if (refusal["error_type"] != type(error).__name__ or refusal["message"] != str(error)
                or json.dumps(refusal.get("candidate_diagnostics"), sort_keys=True) != json.dumps(error.diagnostics, sort_keys=True)):
            raise ValueError("failed fragment repair differs from the independently reconstructed candidate refusal") from error
    else:
        raise ValueError("failed fragment repair reports a refusal for an accepted initial candidate")


def _read_failed_repair(source, definition, returned, native_subwork):
    names = {PurePosixPath(row.relative_path).name for row in returned.files.files}
    required = {"native-error.txt"}
    if TERMINAL_GEOMETRY_FILE in names:
        required.update(("initialized-heavy.pdb", "atom-origin-provenance.json", TERMINAL_GEOMETRY_FILE))
    fragments = type(source) is GpAmberFragmentRepairInput
    if fragments:
        required.update(names.intersection(("terminal-fragments.json", "initialization.json", "initialized-heavy.pdb")))
    files = read_repair_files(native_subwork, definition, returned, required_files=required)
    if files["native-error.txt"] != returned.error.encode():
        raise ValueError("failed repair substitutes the original native error")
    if fragments:
        _read_failed_fragment(source, files, names, returned.error)
    if TERMINAL_GEOMETRY_FILE in files:
        if files["atom-origin-provenance.json"] != source.origin_json.encode():
            raise ValueError("failed repair substitutes the original source atom origins")
        terminal = read_initial_terminal_geometry(files, json.loads(source.origin_json))
        try:
            require_initial_terminal_geometry(terminal)
        except ValueError as error:
            if (not returned.error.rstrip().endswith("ValueError: " + str(error))
                    or names.intersection(("amber.stdout", "amber.stderr", "dry.prmtop", "dry.inpcrd",
                                           "atom-selection.json", "optimizer-return.json", "complete-heavy.pdb"))):
                raise ValueError("failed repair changes the initial geometry refusal or entered work") from error
            return
    if INITIAL_REJECTION in returned.error:
        raise ValueError("failed repair reports a geometry refusal without its independently rejected initial geometry")


def assess_return(source,definition,returned,completed,native_subwork,*,result_id):
    assessment,error=None,None
    try:
        if returned.error is None:
            files=read_repair_files(native_subwork,definition,returned)
            assessment=assess_geometry_repair(source,files,assessment_id="assessment.gp-repair."+source.fingerprint())
        elif isinstance(source, GpCarboxylateRepairInput):
            _read_failed_repair(source, definition, returned, native_subwork)
    except (OSError,ValueError,ArithmeticError):error=traceback.format_exc()
    return GpGeometryRepairResult(result_id,returned,definition,completed.completion,completed.receipt,assessment,error)


class GpGeometryRepairRunner:
    def __init__(self, *, carboxylates=False, amber_fragments=False):
        self.manifest=operation_declaration(carboxylates=carboxylates, amber_fragments=amber_fragments).manifest()

    def preflight(self,context):
        if self.manifest.capability_key != context.task_id:
            raise ValueError("geometry repair preflight changes its installed native owner")
        source=_decode(context).source
        authenticate_engine(source.amber_engine);authenticate_numeric_engine(source.numeric_engine)

    def execute(self,context):raise ValueError("geometry repair requires ordinary native lifecycle authority")

    def execute_with_native_subwork(self,context,native_subwork,progress=None):
        try:
            if self.manifest.capability_key != context.task_id:
                raise ValueError("geometry repair execution changes its installed native owner")
            config=_decode(context);prepared=context.prepared_invocation
            if prepared is None or prepared.implementation!=config.implementation:
                raise ValueError("geometry repair changes its frozen producing source")
            authenticate_engine(config.source.amber_engine);authenticate_numeric_engine(config.source.numeric_engine)
            work=native_work(context,config,native_subwork.parent_contact)
            if prepared.native_work!=work:raise ValueError("geometry repair changes its frozen native census")
            root=Path(config.work_directory);root.mkdir(parents=False,exist_ok=True)
            native_subwork.freeze_roster(work.rosters[0],definitions=work.definitions)
            definition=work.definitions[0];completed=native_subwork.recover(definition)
            if completed is not None:
                returned=decode_canonical_bytes(b"".join(native_subwork.iter_completed_output(definition,"repair.return")),
                    GpGeometryRepairReturn,maximum_bytes=MAX_INPUT)
            else:
                if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
                    raise ValueError("uncertain geometry repair contact cannot be repeated")
                directory=root/GEOMETRY_ID;directory.mkdir()
                entry=native_subwork.begin(definition);native_subwork.contact(entry)
                wall,cpu,self_cpu=time.monotonic(),resource.getrusage(resource.RUSAGE_CHILDREN),time.process_time()
                error=None
                try:
                    from empirical_lawhood.adapters.rubisco.rubisco_response.gp_geometry_repair_native import execute_repair
                    invoke_native_subwork(native_subwork,entry,execute_repair,config.source,directory)
                except Exception:
                    error=traceback.format_exc()
                    with (directory/"native-error.txt").open("x") as stream:stream.write(error)
                # Actual raw return and completion precede every scientific assessment.
                census,_=publish_directory(native_subwork,entry,directory,root, selected_census=directory_census(directory, root))
                returned=GpGeometryRepairReturn(config.source.identity,census,error)
                publish_record(native_subwork,entry,"repair.return",returned)
                after=resource.getrusage(resource.RUSAGE_CHILDREN)
                completed=native_subwork.complete(entry,operational_status=OperationalStatus.SUCCEEDED if error is None else OperationalStatus.FAILED,
                    cost=InquiryCost(Decimal(str(after.ru_utime+after.ru_stime-cpu.ru_utime-cpu.ru_stime+time.process_time()-self_cpu)),
                        Decimal(str(time.monotonic()-wall)),Decimal(sum(r.byte_count for r in census.files))),
                    cost_scope=("One stock-fragment Amber common-parent attempt including fragment preparation, "
                                "any entered full minimization and complete raw publication"
                                if type(config.source) is GpAmberFragmentRepairInput else
                                "One PDBFixer/Amber/OpenMM common-parent construction with all hydrogens mobile and complete raw publication; no dynamics or rates"),
                    reason_codes=() if error is None else ("constructed-geometry-native-failure",))
            result=assess_return(config.source,definition,returned,completed,native_subwork,result_id=context.task_id+".result")
            if len(context.output_ports)!=1 or context.output_ports[0].output_id!=context.task_id+".product" or context.output_ports[0].payload_schema!=result.SCHEMA:
                raise ValueError("geometry repair changes its complete aggregate output")
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id,result.canonical_bytes()),),
                (ReceiptCheck("complete-original-geometry-native-census",True,()),))
        finally:
            for port in context.input_ports:port.close()


def operation_declaration(*, carboxylates=False, amber_fragments=False):
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_translation import validate_root
    conformance = ("complete-direct-native-inputs","complete-original-amber-force-assignment",
        "independent-final-maximum-gradient","observed-heavy-atoms-exactly-fixed","original-custody-no-replay",
        "whole-system-geometry-and-hydrogen-census")
    if carboxylates and amber_fragments:
        raise ValueError("select one common-parent initializer")
    if carboxylates or amber_fragments:
        conformance = tuple(sorted((set(conformance) - {"observed-heavy-atoms-exactly-fixed"}) |
                            {"source-bound-inherited-atom-mobility", "fixed-bond-feasibility", "amber-nominal-phase-coverage"}))
    source_kind, implementation = GpGeometryRepairInput, "pdbfixer-numbered-amber-openmm-selected-cpu-v3"
    if carboxylates:
        source_kind, implementation = GpCarboxylateRepairInput, "pdbfixer-numbered-amber-openmm-scoped-repair-v4"
    elif amber_fragments:
        source_kind, implementation = GpAmberFragmentRepairInput, "amber-terminal-fragments-openmm-scoped-repair-v5"
        conformance = tuple(sorted((*conformance, "amber-terminal-fragment-source-and-reconstruction", "initial-protein-chirality-and-peptides")))
    return RecursiveOperationDeclaration(capability_key=REPAIR_REVISIONS[source_kind.VERSION][0],
        capability_version=source_kind.VERSION, implementation_id=implementation,
        kind=CapabilityKind.SIMULATOR,
        config_record_type=GpGeometryRepairConfig,stage=ScientificStage.ACQUIRE,
        input_ports=(RecursivePortContract("native-provenance",NumericalProducingProvenance.SCHEMA,"application/json",MAX_INPUT),
            RecursivePortContract("native-source",GpGeometryRepairInput.SCHEMA,"application/json",MAX_INPUT)),
        outputs=(OutputTemplate("product",GpGeometryRepairResult.SCHEMA,ArtifactProfile.CANONICAL_JSON,"application/json",".json"),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,resources=BUDGET,
        conformance_check_ids=conformance,
        runner_factory=lambda: GpGeometryRepairRunner(carboxylates=carboxylates, amber_fragments=amber_fragments),
        record_codecs={c.SCHEMA:c for c in (
            GpGeometryRepairConfig,GpGeometryRepairInput,GpGeometryRepairResult,NumericalProducingProvenance)},
        input_record_types=(source_kind,) if source_kind is not GpGeometryRepairInput else (),
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c:tuple(sorted({r.object_fingerprint for r in operands(c)})),
            scientific_unit_ids=lambda c:(UNIT,),native_effect_slot_ids=slots,scientific_root_validator=validate_root),
        execution_properties=RecursiveExecutionProperties(native_effect=True,complete_unit_census=True,native_work_preparer=prepare_native_work))
