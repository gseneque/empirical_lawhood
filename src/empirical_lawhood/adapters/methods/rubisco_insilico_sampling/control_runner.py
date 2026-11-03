# SPDX-License-Identifier: MPL-2.0
"""Small fresh-only isolated composition for selected chemical/force controls."""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import (
    CHUNK_BYTES, file_chunks, publish_directory, publish_record)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import raw_output
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityManifest
from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster, NativeSubworkState

from . import control_contracts as c, control_roster


@dataclass(frozen=True, slots=True)
class ChemicalForceRunner:
    plan: c.ChemicalForcePlan
    invocation_path: str
    selected_definitions: tuple
    environment: tuple[tuple[str,str], ...]
    output_ids: tuple[tuple[str,str], ...]
    census_output_id: str
    manifest: CapabilityManifest | None = None
    stream_output_id: str | None = None

    def execute(self, context):
        raise ValueError("chemical/force controls require actual native progress and ordinary streaming")

    def validate_context(self, context, native_subwork):
        self.plan.__post_init__()
        selected = self.selected_definitions
        attempted = tuple(sorted("control.chemical-force."+name for name,_ in self.plan.selected_assets))
        contract = getattr(context, "prepared_invocation", None)
        implementation = None if contract is None else contract.implementation
        source_root = None if contract is None else json.loads(Path(self.invocation_path).read_bytes())["source_root"]
        if (not selected or native_subwork.parent_contact.task_id != context.task_id
                or selected != control_roster.definitions(self.plan,native_subwork.parent_contact,
                    sources=selected[0].sources,input_materialization_ids=selected[0].input_materialization_ids,
                    implementation=implementation,source_root=source_root)
                or selected[0].input_materialization_ids != tuple(sorted(port.materialization_id for port in context.input_ports))
                or tuple(name for name,_ in self.output_ids) != attempted
                or len(set(port for _,port in self.output_ids)) != len(attempted)
                or self.census_output_id in {port for _,port in self.output_ids}):
            raise ValueError("chemical/force runner changes actual parent/input/selected output joins")
        expected_inputs = {self.plan.identity,*selected[0].sources}
        science_ports = context.input_ports
        if self.manifest is not None:
            from .operation_bindings import SamplingOperationConfig
            science_ports = tuple(port for port in context.input_ports if port.payload_schema != SamplingOperationConfig.SCHEMA)
        if (context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or tuple(sorted(port.artifact_id for port in science_ports))
                    != tuple(sorted(row.object_id for row in expected_inputs))):
            raise ValueError("chemical/force runner substitutes the actual complete operand input census")
        for identity in expected_inputs:
            port = next(port for port in context.input_ports if port.artifact_id == identity.object_id)
            if (port.payload_schema != identity.object_schema or port.media_type != "application/json"
                    or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                    or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
                raise ValueError("chemical/force runner changes its authenticated input schema/access")
            if contract is None:
                raw = port.read()
            else:
                cursor = port.cursor()
                try:
                    raw = cursor.read()
                finally:
                    cursor.close()
            if len(raw) != port.size_bytes or sha256(raw).hexdigest() != identity.object_fingerprint:
                raise ValueError("chemical/force runner substitutes original full canonical materialized input bytes")
        actual = {port.output_id:port for port in context.output_ports}
        expected_outputs = {self.census_output_id, *(port for _,port in self.output_ids)} if self.stream_output_id is None else {
            self.census_output_id, self.stream_output_id}
        if set(actual) != expected_outputs:
            raise ValueError("chemical/force runner changes the actual compiled output census")
        census = actual[self.census_output_id]
        if (census.payload_schema,census.profile,census.media_type) != (
                c.ChemicalForceCensus.SCHEMA,ArtifactProfile.CANONICAL_JSON,"application/json"):
            raise ValueError("chemical/force runner substitutes actual compiled census output")
        expected_raw = raw_output("files.raw")
        for _,port_id in self.output_ids if self.stream_output_id is None else ():
            port = actual[port_id]
            if (port.payload_schema,port.profile,port.media_type) != (
                    expected_raw.payload_schema,expected_raw.profile,expected_raw.media_type):
                raise ValueError("chemical/force runner substitutes actual compiled full raw output")
        if self.stream_output_id is not None:
            from .unit_stream import SamplingUnitStreamChunk, MEDIA
            stream = actual[self.stream_output_id]
            if (stream.payload_schema,stream.profile,stream.media_type) != (
                    SamplingUnitStreamChunk.SCHEMA,ArtifactProfile.JSONL_CHUNKS,MEDIA):
                raise ValueError("chemical/force runner changes its exact portable unit stream contract")
        environment = dict(self.environment)
        if (len(environment) != len(self.environment) or environment.get("PYTHONDONTWRITEBYTECODE") != "1"
                or not environment.get("OPENMM_PLUGIN_DIR") or not Path(environment["OPENMM_PLUGIN_DIR"]).is_absolute()
                or not all(environment.get(name) == "1" for name in ("OPENMM_CPU_THREADS","OPENBLAS_NUM_THREADS",
                    "OMP_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"))):
            raise ValueError("chemical/force runner changes selected child bytecode/thread environment")
        return attempted

    def _entry_target(self):
        module = "empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_native_entry"
        return module,"selected_child",Path(__file__).with_name("control_native_entry.py"),"src/"+module.replace(".","/")+".py"

    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        from empirical_lawhood.infrastructure.isolated_native_subwork import run_isolated_native_entry
        from empirical_lawhood.infrastructure.numerical_provenance import numerical_observer_environment
        contract = context.prepared_invocation
        if contract is None or contract.native_work is None or contract.native_work.isolated_selection is None:
            raise ValueError("SOFTWARE: chemical/force controls require the complete actual specialist preparation before contact")
        contract.validate_context(context)
        self.validate_context(context,native_subwork)
        plan,selected = self.plan,self.selected_definitions
        # Exact complete typed invocation is built and checked by the real local
        # caller before parent contact. Recheck its plan/roster at this live join.
        data = json.loads(Path(self.invocation_path).read_bytes())
        if (data["plan"] != plan.canonical_bytes().decode()
                or tuple(data["definitions"]) != tuple(row.canonical_bytes().decode() for row in selected)):
            raise ValueError("chemical/force runner substitutes its sealed precontact invocation")
        module,function,source,relative = self._entry_target()
        source_sha256 = sha256(source.read_bytes()).hexdigest()
        from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_runner import validate_current_source_descriptor
        validate_current_source_descriptor(plan,contract.implementation,data["source_root"])
        frozen = contract.native_work
        selection = frozen.isolated_selection
        if (frozen.definitions != selected or native_subwork.parent_contact != contract.expected_parent_contact
                or (selection.entry_module,selection.entry_function,selection.entry_source_path,selection.entry_source_sha256,
                    selection.invocation_path,selection.invocation_sha256)
                    != (module,function,str(source),source_sha256,self.invocation_path,sha256(Path(self.invocation_path).read_bytes()).hexdigest())):
            raise ValueError("chemical/force runner substitutes its exact frozen parent/roster/entry/invocation")
        root = Path(plan.workdir)
        if root.exists():
            raise ValueError("chemical/force runner refuses existing work; uncertain native work is never replayed")
        control_roster.freeze(native_subwork,plan,selected,implementation=contract.implementation,source_root=data["source_root"])
        root.mkdir(parents=True,exist_ok=False)
        metadata_directory = root/"metadata"
        metadata_directory.mkdir()
        invocation = metadata_directory/"invocation.json"
        digest = sha256()
        with invocation.open("xb") as output:
            for chunk in file_chunks(Path(self.invocation_path)):
                output.write(chunk)
                digest.update(chunk)
        environment = numerical_observer_environment(dict(self.environment))
        if digest.hexdigest() != selection.invocation_sha256:
            raise ValueError("chemical/force retained invocation differs from its exact frozen input bytes")
        metadata = next(row for row in selected if row.subwork_id == control_roster.METADATA)
        metadata_entry = native_subwork.begin(metadata)
        native_subwork.contact(metadata_entry)
        manifest = publish_record(native_subwork,metadata_entry,"process.selection",selection)
        _,invocation_manifests = publish_directory(native_subwork,metadata_entry,metadata_directory,root)
        from .unit_stream import launcher_definition
        lifecycle = launcher_definition(metadata, selection, (("process.selection", manifest),
            ("files.raw", invocation_manifests[0]), ("files.census", invocation_manifests[1])))
        native_subwork.freeze_roster(NativeSubworkRoster(lifecycle.roster_id,native_subwork.parent_contact,
            (lifecycle.identity,),parent_subwork=metadata.identity),parent_entry=metadata_entry,definitions=(lifecycle,))
        launcher = native_subwork.begin(lifecycle)
        logs = root/"launcher"
        logs.mkdir()
        returned,error = None,None
        try:
            with (logs/"stdout.log").open("xb") as stdout,(logs/"stderr.log").open("xb") as stderr:
                returned = run_isolated_native_entry(selection,native_subwork,lifecycle_entry=launcher,
                    start_output_id="process.start",return_output_id="process.return",environment=environment,
                    cwd=root,stdout=stdout,stderr=stderr,prepared_contract=contract,entry_preflight="preflight_selected_child")
            publish_directory(native_subwork,launcher,logs,root)
            native_subwork.complete(launcher,operational_status=OperationalStatus.SUCCEEDED if returned.returncode == 0 else OperationalStatus.FAILED,
                cost=InquiryCost(returned.inclusive_cpu_seconds,returned.wall_seconds,None),
                cost_scope="Actual isolated child+relay inclusive window; nested native calls contained, RSS unknown",
                reason_codes=() if returned.returncode == 0 else ("known-chemical-force-child-adverse-return",))
        except Exception as caught:
            error = caught
        retained = control_roster.census(native_subwork,plan,selected,implementation=contract.implementation,source_root=data["source_root"])
        if error is None:
            publish_record(native_subwork,metadata_entry,"control.census",retained)
            native_subwork.complete(metadata_entry,operational_status=OperationalStatus.SUCCEEDED,
                cost=InquiryCost(None,None,None),cost_scope="Full 24/96 denominator metadata; cost unmeasured")
        raw = retained.canonical_bytes()
        for offset in range(0,len(raw),CHUNK_BYTES):
            emitter.write(self.census_output_id,raw[offset:offset+CHUNK_BYTES])
        if self.stream_output_id is not None:
            from .unit_stream import emit_units
            emit_units(emitter,self.stream_output_id,native_subwork,retained,selected,launcher=lifecycle)
        for unit_id,output_id in self.output_ids if self.stream_output_id is None else ():
            definition = next(row for row in selected if row.subwork_id == unit_id)
            if native_subwork.inspect(definition).state is NativeSubworkState.COMPLETED:
                for chunk in native_subwork.iter_completed_output(definition,"files.raw",maximum_chunk_bytes=CHUNK_BYTES):
                    emitter.write(output_id,chunk)
        if error is not None:
            raise error
        if not returned.handshake_completed or returned.returncode != 0:
            raise RuntimeError("chemical/force child adverse return; original custody and whole census retained")
        return (ReceiptCheck("rubisco-selected-chemical-force-original-custody",True,()),)
