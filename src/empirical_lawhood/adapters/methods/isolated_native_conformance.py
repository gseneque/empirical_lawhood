# SPDX-License-Identifier: MPL-2.0
"""Exposed selected-interpreter transport controls; no scientific native engine."""

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

from empirical_lawhood.infrastructure.isolated_native_subwork import run_isolated_native_entry, selected_environment_sha256
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntryReturn, IsolatedNativeEntrySelection, IsolatedNativeProcessStart
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster


def exposed_metadata_definition(first):
    """A selected fixture carrier retains the derived immutable launch operand."""
    return replace(first, subwork_id="engine.metadata", operation_id="exposed.isolated.metadata", streams=(),
        outputs=(NativeSubworkOutput("process.selection", IsolatedNativeEntrySelection.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json"),))


def _freeze_initial(progress, definitions):
    metadata = exposed_metadata_definition(definitions[0])
    selected = tuple(sorted((*definitions, metadata), key=lambda row: row.subwork_id))
    progress.freeze_roster(NativeSubworkRoster("selected.native-subwork", progress.parent_contact,
        tuple(row.identity for row in selected)), definitions=selected)
    return metadata


def exposed_child(progress, invocation):
    """Authenticate selected fixture operands; retain exact states on deliberate loss."""
    data = json.loads(invocation.read())
    definitions = tuple(decode_canonical_bytes(text.encode(), NativeSubworkDefinition,
        maximum_bytes=len(text.encode())) for text in data["definitions"])
    _freeze_initial(progress, definitions)
    first = next(row for row in definitions if row.subwork_id == "forecast.one")
    if data["phase"] == "before-begin":
        os._exit(91)
    entry = progress.begin(first)
    if data["phase"] == "before-contact":
        os._exit(92)
    progress.contact(entry)
    if data["phase"] == "after-contact":
        os._exit(93)
    payload = data["payload"].encode()
    progress.publish_output(entry, first.outputs[0].output_id, iter((payload,)),
        maximum_bytes=len(payload), maximum_chunk_bytes=len(payload),
        expected_size_bytes=len(payload), expected_physical_sha256=sha256(payload).hexdigest())
    if data["phase"] == "after-publication":
        os._exit(94)
    progress.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
        cost=InquiryCost(None, None, None), cost_scope="exposed transport control; native costs not measured",
        consumed_streams=first.streams)
    if data["phase"] == "after-completion":
        os._exit(95)


@dataclass(frozen=True, slots=True)
class ExposedIsolatedNativeRunner:
    """Only fixture paths are selected; the real executor provides actual progress."""
    invocation_path: str
    selected_directory: str
    wrong: str | None = None
    selected_entry_source: str | None = None
    replace_invocation_after_handshake: bool = False
    selected_import_root: str | None = None
    selected_interpreter_path: str | None = None
    selected_interpreter_sha256: str | None = None

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        if (self.selected_interpreter_path is None) != (self.selected_interpreter_sha256 is None):
            raise ValueError("Selected isolated interpreter path and digest must be supplied together")
        root = Path(self.selected_directory)
        source_path = Path(self.selected_entry_source).resolve() if self.selected_entry_source else Path(__file__).resolve()
        module_name = source_path.stem if self.selected_entry_source else __name__
        import_roots = [str(Path(self.selected_import_root).resolve(strict=True))
            if self.selected_import_root else str(Path(__file__).resolve().parents[3])]
        if self.selected_entry_source:
            import_roots.append(str(source_path.parent))
        environment = dict(os.environ, PYTHONPATH=os.pathsep.join(import_roots), PYTHONDONTWRITEBYTECODE="1")
        invocation = Path(self.invocation_path)
        data = json.loads(invocation.read_bytes())
        definitions = tuple(decode_canonical_bytes(text.encode(), NativeSubworkDefinition,
            maximum_bytes=len(text.encode())) for text in data["definitions"])
        parent = native_subwork.parent_contact
        metadata = _freeze_initial(native_subwork, definitions)
        metadata_entry = native_subwork.begin(metadata)
        native_subwork.contact(metadata_entry)
        interpreter = self.selected_interpreter_path or sys.executable
        interpreter_sha256 = self.selected_interpreter_sha256 or sha256(Path(sys.executable).read_bytes()).hexdigest()
        selection = IsolatedNativeEntrySelection("exposed.isolated.entry", interpreter,
            interpreter_sha256, module_name, "exposed_child",
            str(source_path), sha256(source_path.read_bytes()).hexdigest(), str(invocation),
            sha256(invocation.read_bytes()).hexdigest(), selected_environment_sha256(environment))
        if self.wrong is not None and self.wrong != "lifecycle_selection":
            selection = replace(selection, **{self.wrong: "f" * 64})
        raw_selection = selection.canonical_bytes()
        selected_manifest = native_subwork.publish_output(metadata_entry, "process.selection", iter((raw_selection,)),
            maximum_bytes=len(raw_selection), expected_size_bytes=len(raw_selection),
            expected_physical_sha256=sha256(raw_selection).hexdigest())
        lifecycle_definition = replace(metadata, subwork_id="engine.launch", operation_id="exposed.isolated.launch",
            configuration=metadata.configuration if self.wrong == "lifecycle_selection" else selection.identity,
            input_materialization_ids=tuple(sorted((*metadata.input_materialization_ids,
                selected_manifest.materialization.materialization_id))),
            roster_id="conditional.isolated.engine", outputs=tuple(NativeSubworkOutput(output_id,
                record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json") for output_id, record in (
                    ("process.return", IsolatedNativeEntryReturn), ("process.start", IsolatedNativeProcessStart))))
        native_subwork.freeze_roster(NativeSubworkRoster(lifecycle_definition.roster_id, parent,
            (lifecycle_definition.identity,), parent_subwork=metadata.identity), parent_entry=metadata_entry,
            definitions=(lifecycle_definition,))
        lifecycle_entry = native_subwork.begin(lifecycle_definition)
        if self.replace_invocation_after_handshake:
            # Test-only interception at the child's parent round trip, after it
            # has authenticated/sealed the input and received its entry ACK.
            port_type = type(native_subwork)
            original = port_type._call
            parent_inspections = 0
            def changed_call(port, operation, *arguments):
                nonlocal parent_inspections
                if port is native_subwork and operation == "parent-contact":
                    parent_inspections += 1
                    if parent_inspections == 2:
                        invocation.write_text('{"substituted":true}')
                return original(port, operation, *arguments)
            port_type._call = changed_call
        with (root / "child.stdout").open("xb") as stdout, (root / "child.stderr").open("xb") as stderr:
            try:
                returned = run_isolated_native_entry(selection, native_subwork, environment=environment,
                    lifecycle_entry=lifecycle_entry, start_output_id="process.start",
                    return_output_id="process.return", cwd=root, stdout=stdout, stderr=stderr)
            finally:
                if self.replace_invocation_after_handshake:
                    port_type._call = original
        (root / "child-return.json").write_bytes(returned.canonical_bytes())
        native_subwork.complete(lifecycle_entry,
            operational_status=OperationalStatus.SUCCEEDED if returned.returncode == 0 else OperationalStatus.FAILED,
            cost=InquiryCost(returned.inclusive_cpu_seconds, returned.wall_seconds, None),
            cost_scope="Selected interpreter and relay inclusive window; contains nested fixture costs, never sum twice",
            reason_codes=() if returned.returncode == 0 else ("exposed-child-adverse-return",))
        native_subwork.complete(metadata_entry, operational_status=OperationalStatus.SUCCEEDED,
            cost=InquiryCost(None, None, None), cost_scope="Derived fixture launch selection; nested launch window measured separately")
        if not returned.handshake_completed or returned.returncode != 0:
            raise RuntimeError("exposed isolated child returned an adverse operational result")
        from empirical_lawhood.runtime.execution import RunnerResult
        return RunnerResult((), (ReceiptCheck("exposed-selected-interpreter", True,
            ()),))
