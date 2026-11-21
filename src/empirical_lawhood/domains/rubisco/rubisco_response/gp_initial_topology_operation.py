# SPDX-License-Identifier: MPL-2.0
"""Bounded initial Amber construction through the ordinary native lifecycle."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path, PurePosixPath
import resource
import subprocess
import time
import traceback
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import RAW_MAGIC, _ChunkReader, file_chunks, publish_directory, publish_record, uncompressed_archive_chunks, directory_census
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
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import GpAmberModelInput, GpInitialAmberInput, MODEL_NAMES, initial_heavy_pdb, initial_leap_script, initial_parameter_files
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import GpInitialTopologyAssessment, assess_initial_topology
from empirical_lawhood.domains.rubisco.rubisco_response.gp_heavy_geometry import require_initial_heavy_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


CAPABILITY = "rubisco-response.prepare-initial-gp-amber"
MAX_INPUT = 64 * 2**20
BUDGET = ResourceBudget(8, 8 * 2**30, 0, None, 512 * 2**20, 2 * 2**30)
UNIT = "unit.gp-original-1bwv-assembly"


@dataclass(frozen=True, slots=True)
class GpAmberOperationConfig(CanonicalRecord):
    """Current complete native input contract; no historical configuration shim."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-amber-operation-config"
    VERSION: ClassVar[str] = "4.0.0"
    config_id: str
    source: GpInitialAmberInput
    implementation: RecursiveImplementationBinding
    work_directory: str
    provenance: NumericalProducingProvenance

    def __post_init__(self):
        validate_stable_id(self.config_id)
        exact(self.source, GpInitialAmberInput)
        exact(self.implementation, RecursiveImplementationBinding)
        path = PurePosixPath(self.work_directory)
        if not path.is_absolute() or ".." in path.parts or str(path) != self.work_directory:
            raise ValueError("initial Amber construction requires its exact selected fresh work directory")
        exact(self.provenance, NumericalProducingProvenance)
        if any(getattr(self.provenance, name) != getattr(self.implementation, name)
               for name in ("package_sources", "code_sources_sha256", "dependency_lock_sha256",
                            "observed_git_head", "observed_checkout_clean")):
            raise ValueError("initial Amber provenance substitutes its actual selected producing implementation")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class GpAmberBuildReturn(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-amber-build-return"
    model: ObjectIdentity
    return_code: int | None
    timed_out: bool
    files: DurableRawFileCensus
    error: str | None

    def __post_init__(self):
        exact(self.model, ObjectIdentity)
        exact(self.files, DurableRawFileCensus)
        if self.return_code is not None and type(self.return_code) is not int or type(self.timed_out) is not bool:
            raise ValueError("initial Amber return changes its original process result")
        if self.error is not None and (type(self.error) is not str or not self.error):
            raise ValueError("initial Amber error must preserve an actual nonempty diagnostic")


@dataclass(frozen=True, slots=True)
class GpAmberUnitProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-amber-unit-product"
    returned: GpAmberBuildReturn
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt
    assessment: GpInitialTopologyAssessment | None
    assessment_error: str | None

    def __post_init__(self):
        for record, kind in ((self.returned,GpAmberBuildReturn),(self.definition,NativeSubworkDefinition),
                            (self.completion,NativeSubworkCompletion),(self.receipt,CanonicalTaskReceipt)):
            exact(record,kind)
        require_native_completion_receipt(self.completion,self.receipt,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
        if (self.completion.definition != self.definition.identity or self.definition.operation_id != CAPABILITY
                or self.definition.configuration != self.returned.model):
            raise ValueError("initial Amber result changes its original model or native owner")
        logical_id = self.receipt.task_id+".output.build.return"
        logical = tuple(row for row in self.receipt.output_logical_artifacts if row.logical_artifact_id == logical_id)
        physical = tuple(row for row in self.receipt.output_materializations if row.logical_artifact_id == logical_id)
        raw = self.returned.canonical_bytes()
        if (len(logical) != 1 or len(physical) != 1 or logical[0].payload_schema != GpAmberBuildReturn.SCHEMA
                or logical[0].content_sha256 != sha256(raw).hexdigest()
                or (physical[0].physical_sha256,physical[0].size_bytes) != (sha256(raw).hexdigest(),len(raw))):
            raise ValueError("initial Amber result substitutes its original receipted raw return")
        if self.assessment is not None:
            exact(self.assessment,GpInitialTopologyAssessment)
            expected = {row.relative_path:row.sha256 for row in self.returned.files.files}
            if (self.assessment.model != self.returned.model or self.returned.return_code != 0
                    or self.returned.timed_out or self.returned.error is not None or self.assessment_error is not None
                    or any(expected.get(self.definition.subwork_id+"/"+name) != digest
                        for name,digest in self.assessment.file_sha256s)):
                raise ValueError("initial Amber assessment substitutes its completed original native bytes")
        if self.assessment_error is not None and (type(self.assessment_error) is not str or not self.assessment_error):
            raise ValueError("initial Amber assessment error must retain its actual diagnostic")


@dataclass(frozen=True, slots=True)
class GpAmberPreparationResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-amber-preparation-result"
    result_id: str
    source: ObjectIdentity
    units: tuple[GpAmberUnitProduct, ...]
    interpretation: str = "INITIAL_CONSTRUCTION_ONLY_NO_REACTIVE_ENSEMBLE_OR_RATE_ADMISSION"

    def __post_init__(self):
        validate_stable_id(self.result_id)
        exact(self.source,ObjectIdentity)
        if (type(self.units) is not tuple or len(self.units) != 4
                or tuple(row.definition.subwork_id for row in self.units) != tuple("initial-gp."+n for n in sorted(MODEL_NAMES))
                or self.interpretation != "INITIAL_CONSTRUCTION_ONLY_NO_REACTIVE_ENSEMBLE_OR_RATE_ADMISSION"):
            raise ValueError("initial Amber result drops a selected arm or promotes its interpretation")
        for row in self.units:
            exact(row,GpAmberUnitProduct)


def operands(config):
    return tuple(sorted((config.identity,config.source.identity,config.source.engine.identity,
        *(m.scaffold for m in config.source.models),config.provenance.identity),key=lambda row:row.object_id))


def native_input_records(config):
    """Exact direct model/source/provenance carriers for native input guards."""
    exact(config, GpAmberOperationConfig)
    values = [("native-source", config.source.identity, config.source),
              ("native-provenance", config.provenance.identity, config.provenance)]
    values.extend(("native-model." + model.name, model.identity, model) for model in config.source.models)
    return tuple(sorted(values, key=lambda row: row[0]))


def slots(config):
    return ("native.initial-gp-amber."+config.fingerprint(),)


def native_work(context, config, parent):
    outputs = (json_output("build.return",GpAmberBuildReturn),json_output("files.census",DurableRawFileCensus),raw_output("files.raw"))
    sources = tuple(sorted((config.identity, config.source.identity, config.provenance.identity), key=lambda row: row.object_id))
    definitions = tuple(NativeSubworkDefinition("initial-gp."+model.name,CAPABILITY,parent,model.identity,sources,
        config.implementation.code_sources_sha256,config.implementation.dependency_lock_sha256,
        tuple(sorted(port.materialization_id for port in context.input_ports)),(),outputs)
        for model in sorted(config.source.models,key=lambda m:m.name))
    roster = NativeSubworkRoster("selected.native-subwork",parent,tuple(row.identity for row in definitions))
    return PreparedNativeWork(parent,(UNIT,),slots(config),definitions,(roster,))


def _decode(context):
    manifest = operation_declaration().manifest()
    if (context.task_id != CAPABILITY or context.permissions != manifest.permissions
            or context.resource_budget != BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or len(context.input_ports) != 7):
        raise ValueError("initial Amber worker changes its finite task contract")
    received = {}
    for port in context.input_ports:
        if (port.kind is not WorkerInputKind.EXTERNAL or port.media_type != "application/json" or port.size_bytes > MAX_INPUT
                or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("initial Amber worker substitutes its complete exposed input")
        raw = port.read(MAX_INPUT)
        key = (port.payload_schema, sha256(raw).hexdigest())
        if key in received:
            raise ValueError("initial Amber worker repeats a direct scientific input")
        received[key] = (port, raw)
    selected = tuple(value for (schema, _), value in received.items() if schema == GpAmberOperationConfig.SCHEMA)
    if len(selected) != 1:
        raise ValueError("initial Amber worker lacks its unique complete configuration")
    port, raw = selected[0]
    config = decode_canonical_bytes(raw,GpAmberOperationConfig,maximum_bytes=MAX_INPUT)
    if (config.config_id,config.fingerprint(),port.artifact_id) != (
            context.config.config_id,context.config.content_sha256,context.config.artifact_id):
        raise ValueError("initial Amber worker substitutes its selected configuration")
    expected = {(config.SCHEMA, config.fingerprint()): config}
    expected.update({(pin.object_schema, pin.object_fingerprint): record for _, pin, record in native_input_records(config)})
    if set(received) != set(expected) or any(received[key][1] != record.canonical_bytes() for key, record in expected.items()):
        raise ValueError("initial Amber worker substitutes its exact direct model/source/provenance census")
    require_initial_heavy_geometry(config.source)
    return config


def prepare_native_work(*,runner,context,expected_parent):
    if type(runner) is not GpAmberRunner:
        raise ValueError("initial Amber preparer requires its installed runner")
    return native_work(context,_decode(context),expected_parent)


def authenticate_engine(engine):
    root = Path(engine.root)
    if root.is_symlink() or root.resolve() != root:
        raise ValueError("selected Amber engine requires its original canonical root")
    actual = []
    for path in root.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("selected Amber engine contains an undeclared link or special member")
        if path.is_file():
            actual.append(path.relative_to(root).as_posix())
    if tuple(sorted(actual)) != tuple(row.relative_path for row in engine.files):
        raise ValueError("selected Amber engine changes its complete regular-file closure")
    for row in engine.files:
        for _ in file_chunks(root/row.relative_path,expected=row):
            pass
    amber_command(engine)


def amber_command(engine):
    """Use the selected loader with its own copied C runtime and library set."""
    loader = engine.library_directory + "/ld-linux-x86-64.so.2"
    if not {loader, engine.library_directory + "/libc.so.6"}.issubset(
            row.relative_path for row in engine.files):
        raise ValueError("initial Amber engine lacks its selected runtime loader and C library")
    root = Path(engine.root)
    return [str(root/loader), "--library-path", str(root/engine.library_directory),
            str(root/engine.executable)]


def read_initial_amber_files(native_subwork,definition,returned,*,maximum_bytes):
    """Authenticate the whole original archive without reconstructing a model."""
    if sum(row.byte_count for row in returned.files.files) > maximum_bytes:
        raise ValueError("initial Amber raw return exceeds its selected model-output ceiling")
    from empirical_lawhood.domains.rubisco.rubisco_response.amber_construction_admission import INITIAL_ASSESSMENT_FILES
    wanted = set(INITIAL_ASSESSMENT_FILES)
    chunks = native_subwork.iter_completed_output(definition,"files.raw")
    reader = _ChunkReader(uncompressed_archive_chunks(chunks))
    try:
        if reader.take(len(RAW_MAGIC)) != RAW_MAGIC:
            raise ValueError("initial Amber return changes its original archive format")
        size = int.from_bytes(reader.take(8),"big")
        if not 0 < size <= 2**20:
            raise ValueError("initial Amber return changes its bounded raw census")
        header = reader.take(size)
        census = decode_canonical_bytes(header,DurableRawFileCensus,maximum_bytes=2**20)
        if census != returned.files or header != b"".join(native_subwork.iter_completed_output(definition,"files.census")):
            raise ValueError("initial Amber return substitutes its complete raw census")
        files = {}
        for row in census.files:
            path = PurePosixPath(row.relative_path)
            if path.parts != (definition.subwork_id,path.name):
                raise ValueError("initial Amber return changes its original model directory")
            digest,parts,remaining = sha256(),[],row.byte_count
            while remaining:
                block = reader.take(min(remaining,2**20));remaining -= len(block);digest.update(block)
                if path.name in wanted:parts.append(block)
            if digest.hexdigest() != row.sha256:
                raise ValueError("initial Amber raw file differs from its original full-byte digest")
            if path.name in wanted:files[path.name] = b"".join(parts)
        reader.finish()
        if set(files) != wanted:
            raise ValueError("initial Amber return has missing dry or solvated native output")
        return files
    finally:
        close = getattr(chunks,"close",None)
        if close is not None:close()


def reassess_initial_amber_result(source,result,native_subwork,*,result_id):
    """Current pure assessment retains all original calls and known failures."""
    exact(source,GpInitialAmberInput)
    exact(result,GpAmberPreparationResult)
    if result.source != source.identity:
        raise ValueError("initial Amber retained read substitutes the original four-material source")
    models = {"initial-gp."+model.name:model for model in source.models}
    units = []
    for original in result.units:
        definition = original.definition
        model = models[definition.subwork_id]
        observed = native_subwork.recover(definition)
        if (observed is None or observed.completion != original.completion or observed.receipt != original.receipt
                or definition.configuration != model.identity or source.identity not in definition.sources):
            raise ValueError("initial Amber retained read loses original model/receipt custody")
        returned = decode_canonical_bytes(b"".join(native_subwork.iter_completed_output(definition,"build.return")),
            GpAmberBuildReturn,maximum_bytes=MAX_INPUT)
        if returned != original.returned:
            raise ValueError("initial Amber retained read substitutes its original raw return")
        assessment,error = None,None
        if returned.return_code == 0 and not returned.timed_out and returned.error is None:
            try:
                files = read_initial_amber_files(native_subwork,definition,returned,maximum_bytes=source.maximum_model_output_bytes)
                assessment = assess_initial_topology(source,model,files,assessment_id="assessment.initial-gp."+model.name)
            except (OSError,ValueError,ArithmeticError):
                error = traceback.format_exc()
        units.append(GpAmberUnitProduct(returned,definition,observed.completion,observed.receipt,assessment,error))
    return GpAmberPreparationResult(result_id,source.identity,tuple(units))


class GpAmberRunner:
    def __init__(self):
        self.manifest = operation_declaration().manifest()

    def preflight(self,context):
        authenticate_engine(_decode(context).source.engine)

    def execute(self,context):
        raise ValueError("initial Amber construction requires ordinary native lifecycle authority")

    def execute_with_native_subwork(self,context,native_subwork,progress=None):
        try:
            config = _decode(context)
            prepared = context.prepared_invocation
            if prepared is None or prepared.implementation != config.implementation:
                raise ValueError("initial Amber construction changes its frozen producing source")
            authenticate_engine(config.source.engine)
            work = native_work(context,config,native_subwork.parent_contact)
            if prepared.native_work != work:
                raise ValueError("initial Amber construction changes its prepared complete native census")
            root = Path(config.work_directory)
            root.mkdir(parents=False,exist_ok=True)
            parameter_files = initial_parameter_files(config.source.parameter_sources,config.source.ligand)
            native_subwork.freeze_roster(work.rosters[0],definitions=work.definitions)
            units = []
            for definition in work.definitions:
                model = next(m for m in config.source.models if "initial-gp."+m.name == definition.subwork_id)
                recovered = native_subwork.recover(definition)
                if recovered is not None:
                    raw = b"".join(native_subwork.iter_completed_output(definition,"build.return"))
                    returned = decode_canonical_bytes(raw,GpAmberBuildReturn,maximum_bytes=MAX_INPUT)
                    completed = recovered
                else:
                    if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
                        raise ValueError("uncertain initial Amber contact cannot be repeated")
                    directory = root/definition.subwork_id
                    directory.mkdir()
                    for name,text in {**parameter_files,"complete-heavy.pdb":initial_heavy_pdb(model),"build.leap":initial_leap_script()}.items():
                        with (directory/name).open("x",encoding="ascii") as stream:
                            stream.write(text)
                    entry = native_subwork.begin(definition)
                    native_subwork.contact(entry)
                    wall,cpu,self_cpu = time.monotonic(),resource.getrusage(resource.RUSAGE_CHILDREN),time.process_time()
                    return_code,timed_out,error = None,False,None
                    try:
                        from empirical_lawhood.adapters.rubisco.rubisco_response.initial_amber_native import execute_initial_amber
                        return_code,timed_out = invoke_native_subwork(native_subwork,entry,execute_initial_amber,config.source,directory)
                    except subprocess.TimeoutExpired:
                        timed_out,error = True,"Amber process timed out"
                    except subprocess.CalledProcessError as failure:
                        return_code,error = failure.returncode,"Amber process returned "+str(failure.returncode)
                    except (OSError, ValueError, ArithmeticError, RuntimeError, ImportError):
                        error = traceback.format_exc()
                    if error is not None:
                        with (directory/"process-error.txt").open("x") as stream:
                            stream.write(error)
                    # Seal original native bytes and completion before any scientific
                    # parser, parameter/geometry guard or assessment can fail.
                    selected,_ = publish_directory(native_subwork,entry,directory,root, selected_census=directory_census(directory, root))
                    returned = GpAmberBuildReturn(model.identity,return_code,timed_out,selected,error)
                    publish_record(native_subwork,entry,"build.return",returned)
                    after = resource.getrusage(resource.RUSAGE_CHILDREN)
                    completed = native_subwork.complete(entry,
                        operational_status=OperationalStatus.SUCCEEDED if return_code == 0 and not timed_out else OperationalStatus.FAILED,
                        cost=InquiryCost(Decimal(str(after.ru_utime+after.ru_stime-cpu.ru_utime-cpu.ru_stime+time.process_time()-self_cpu)),
                            Decimal(str(time.monotonic()-wall)),Decimal(sum(row.byte_count for row in selected.files))),
                        cost_scope="One full PDBFixer mutation, Amber assignment and complete OpenMM molecular minimization plus original raw publication; no ensemble or kinetic admission",
                        reason_codes=() if error is None else ("initial-amber-build-failure",))
                assessment,assessment_error = None,None
                if returned.return_code == 0 and not returned.timed_out and returned.error is None:
                    try:
                        files = read_initial_amber_files(native_subwork,definition,returned,
                            maximum_bytes=config.source.maximum_model_output_bytes)
                        assessment = assess_initial_topology(config.source,model,files,assessment_id="assessment.initial-gp."+model.name)
                    except (OSError,ValueError,ArithmeticError):
                        assessment_error = traceback.format_exc()
                units.append(GpAmberUnitProduct(returned,definition,completed.completion,completed.receipt,assessment,assessment_error))
            authenticate_engine(config.source.engine)
            product = GpAmberPreparationResult(CAPABILITY+".result",config.source.identity,tuple(units))
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != CAPABILITY+".product"
                    or context.output_ports[0].payload_schema != product.SCHEMA):
                raise ValueError("initial Amber construction changes its complete aggregate output")
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id,product.canonical_bytes()),),
                (ReceiptCheck("complete-four-material-native-census",True,()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declaration():
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_translation import validate_root
    return RecursiveOperationDeclaration(capability_key=CAPABILITY,capability_version="3.0.0",
        implementation_id="initial-full-gp-amber-selected-cpu-whole-geometry-v3",
        kind=CapabilityKind.SIMULATOR,config_record_type=GpAmberOperationConfig,stage=ScientificStage.ACQUIRE,
        input_ports=(RecursivePortContract("native-model",GpAmberModelInput.SCHEMA,"application/json",MAX_INPUT,minimum_count=4,maximum_count=4),
            RecursivePortContract("native-provenance",NumericalProducingProvenance.SCHEMA,"application/json",MAX_INPUT),
            RecursivePortContract("native-source",GpInitialAmberInput.SCHEMA,"application/json",MAX_INPUT)),
        outputs=(OutputTemplate("product",GpAmberPreparationResult.SCHEMA,ArtifactProfile.CANONICAL_JSON,"application/json",".json"),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,resources=BUDGET,
        conformance_check_ids=("all-four-materials-and-eight-sites","complete-direct-native-inputs","complete-raw-parameter-census","original-custody-no-replay"),
        runner_factory=GpAmberRunner,record_codecs={kind.SCHEMA:kind for kind in (GpAmberOperationConfig,
            GpAmberPreparationResult,GpAmberModelInput,GpInitialAmberInput,NumericalProducingProvenance)},
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c:tuple(sorted({r.object_fingerprint for r in operands(c)})),
            scientific_unit_ids=lambda c:(UNIT,),native_effect_slot_ids=slots,scientific_root_validator=validate_root),
        execution_properties=RecursiveExecutionProperties(native_effect=True,complete_unit_census=True,native_work_preparer=prepare_native_work))
