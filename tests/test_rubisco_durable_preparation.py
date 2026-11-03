# SPDX-License-Identifier: MPL-2.0
"""Exposed real custody controls; never a molecular model or native qualification."""

from dataclasses import replace
from hashlib import sha256
import json
import gzip
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import durable_contracts as d
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import definitions, freeze, census, recover_unit, completed_call_custody
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import (
    DurableCallLedger, DurablePreparationRunner, complete_unit, copy_completed_geometry, directory_census, raw_archive_chunks,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_instrumentation import instrument_completion, selected_value
from empirical_lawhood.infrastructure.native_subwork_ipc import NativeSubworkPipeService, NativeSubworkRequest, PipeNativeSubworkProgress
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, TaskProcessError
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkState, NativeSubworkUncertainContact
from empirical_lawhood.runtime.execution import WorkerOutputPort
from tests.runtime_platform.test_native_subwork import ExposedInput, _plane, _store, _process_context


@pytest.fixture
def selected(tmp_path, request):
    plane = _plane(tmp_path / "custody")
    records = tuple(ExposedInput(name + ".selected", "exposed complete operand " + name)
                    for name in ("source", "nomination", "inventory", "coordinates"))
    exposed_entry = Path(__file__).with_name("rubisco_durable_entry.py")
    code = (("src/exposed_fixture.py", "4" * 64),
            ("tests/rubisco_durable_entry.py", sha256(exposed_entry.read_bytes()).hexdigest()))
    if getattr(request, "param", None) == "entry-mismatch":
        code = tuple((path, "7" * 64 if path == "tests/rubisco_durable_entry.py" else digest)
                     for path, digest in code)
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        "5" * 64, code, sha256(canonical_json_bytes(code)).hexdigest(), "3" * 40, False)
    identities = tuple(ObjectIdentity.from_record(row.selected_id, row) for row in records)
    executable_hash = sha256(Path(sys.executable).read_bytes()).hexdigest()
    plan = d.DurablePreparationPlan("config.selected", *identities, str(tmp_path / "working"),
        sys.executable, executable_hash, sys.executable, executable_hash, "6" * 64, code, "5" * 64)
    if getattr(request, "param", None) in ("pilot", "entry-mismatch"):
        first_geometry = d.geometry_id(*plan.geometry_census[0])
        model_ids = tuple(sorted(d.model_id(*key) for key in plan.model_census if d.geometry_id(*key[:2]) == first_geometry))
        plan = replace(plan, attempted_geometry_ids=(first_geometry,), attempted_model_ids=model_ids)
    manifests = []
    for name, record in (*((row.selected_id, row) for row in records),
            (provenance.identity.object_id, provenance), (plan.plan_id, plan)):
        result = plane.write(ArtifactWriteRequest(name, "inputs/" + name + ".json", record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", "selected.inputs", "inputs", record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifests.append(decode_artifact_manifest(plane.root.resolve(
            result.materialization.relative_path + ".manifest.json", for_write=False).read_bytes()))
    parent = NativeEffectContact("synthetic.run", "native.parent", "synthetic.run.native.parent.attempt-001",
        ObjectIdentity("plan.selected", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "1" * 64),
        ObjectIdentity("native.parent", "empirical-lawhood/runtime/execution-task", "1.0.0", "2" * 64),
        "3" * 40, tuple(sorted(row.materialization.materialization_id for row in manifests)), ())
    store = _store(plane, parent, tuple(manifests))
    store.parent_contacts.begin(parent)
    selected = definitions(plan, parent, sources=(*identities, provenance.identity),
        input_materialization_ids=parent.input_materialization_ids)
    context = _process_context(store, selected[0], tuple(manifests))
    service = NativeSubworkPipeService(store, context, tmp_path)
    class Connection:
        def send(self, message):
            if type(message) is NativeSubworkRequest:
                service.handle(message, self)
            else:
                self.reply = message
        def recv(self):
            return self.reply
    progress = PipeNativeSubworkProgress(Connection())
    freeze(progress, selected)
    Path(plan.workdir).mkdir()
    yield SimpleNamespace(plan=plan, selected=selected, store=store, progress=progress,
                          root=Path(plan.workdir), context=context)
    for port in context.input_ports:
        port.close()


def unit(selected, prefix="geometry."):
    definition = next(row for row in selected.selected if row.subwork_id.startswith(prefix))
    entry = selected.progress.begin(definition)
    selected.progress.contact(entry)
    directory = selected.root / definition.subwork_id
    directory.mkdir()
    return definition, entry, directory, DurableCallLedger(selected.progress, selected.plan, selected.root, entry, directory)


def raw(selected, definition, output):
    result = b"".join(selected.progress.iter_completed_output(definition, output))
    return gzip.decompress(result) if output == "files.raw" else result


def test_full_roster_retains_every_unentered_geometry_and_model(selected):
    result = census(selected.progress, selected.plan, selected.selected)
    assert len(selected.selected) == 37 and len(result.states) == 36
    assert sum(name.startswith("geometry.") for name, _ in result.states) == 12
    assert sum(name.startswith("model.") for name, _ in result.states) == 24
    assert all(state is NativeSubworkState.NOT_ENTERED for _, state in result.states)
    assert result.physical_independent_units == 0


@pytest.mark.parametrize("changed", ["geometry_census", "model_census", "physical_independent_units"])
def test_plan_refuses_thinned_duplicated_or_relabelled_denominator(selected, changed):
    value = 1 if changed == "physical_independent_units" else getattr(selected.plan, changed)[:-1]
    with pytest.raises(ValueError, match="12/24"):
        replace(selected.plan, **{changed: value})


def test_actual_conditional_operands_and_full_binary_returns_survive_before_guard(selected):
    definition, entry, directory, ledger = unit(selected)
    before = bytes(range(256)) * 9000
    after = before[::-1]
    (directory / "positions.bin").write_bytes(before)
    (directory / "empty.log").write_bytes(b"")
    def actual():
        assert selected.store.inspect(ledger.call_definitions[-1]).state is NativeSubworkState.UNKNOWN_COMPLETION
        (directory / "positions.bin").write_bytes(after)
        return {"returncode": -7, "zero": "-0.0"}
    returned = ledger.call("exposed.native-return", {"full_state": "positions.bin", "internal_iterations": None},
        actual, realization=lambda value: value)
    assert returned["returncode"] == -7
    call = ledger.call_definitions[-1]
    actual_receipt = selected.progress.recover(call)
    assert actual_receipt.completion.operational_status is OperationalStatus.SUCCEEDED
    assert actual_receipt.completion.peak_rss_bytes is None
    assert after in raw(selected, call, "files.raw")
    carrier, = selected.store.iter_roster_definitions(call.parent_contact, call.subwork_id + ".operand-roster")
    assert before in raw(selected, carrier, "files.raw")
    bound = json.loads(raw(selected, carrier, "call.operand"))
    assert bound["value"]["requested_json"] == '{"full_state":"positions.bin","internal_iterations":null}'
    assert call.configuration.object_fingerprint == sha256(raw(selected, carrier, "call.operand")).hexdigest()
    complete_unit(selected.progress, selected.plan, entry, selected.root, directory, ledger,
                  succeeded=False, error="adverse return interpreted only after raw receipt")
    assert selected.progress.recover(definition).completion.operational_status is OperationalStatus.FAILED
    assert len(census(selected.progress, selected.plan, selected.selected).states) == 36


@pytest.mark.parametrize("returncode,write_parameters", [(17, False), (0, False), (0, True)])
def test_tleap_known_return_capture_is_separate_from_model_guard(selected, returncode, write_parameters):
    definition, entry, directory, ledger = unit(selected, "model.")
    def actual():
        (directory / "tleap.stdout.log").write_bytes(b"full known native stdout\x00\xff")
        (directory / "tleap.stderr.log").write_bytes(b"")
        if write_parameters:
            (directory / "model.prmtop").write_bytes(b"exposed complete parameter bytes")
            (directory / "model.inpcrd").write_bytes(b"exposed complete positions")
        return subprocess.CompletedProcess(["exposed.tleap", "-f", "tleap.in"], returncode)
    result = ledger.call("ambertools.tleap", {"command": ["exposed.tleap", "-f", "tleap.in"]},
        actual, realization=lambda row: {"returncode": row.returncode})
    call = ledger.call_definitions[-1]
    assert selected.progress.recover(call).completion.operational_status is OperationalStatus.SUCCEEDED
    assert b"full known native stdout\x00\xff" in raw(selected, call, "files.raw")
    succeeded = result.returncode == 0 and all((directory / name).is_file() for name in ("model.prmtop", "model.inpcrd"))
    complete_unit(selected.progress, selected.plan, entry, selected.root, directory, ledger,
        succeeded=succeeded, error=None if succeeded else "known return or missing output")
    assert selected.progress.recover(definition).completion.operational_status is (
        OperationalStatus.SUCCEEDED if succeeded else OperationalStatus.FAILED)


def test_known_exception_retains_return_error_and_partial_files(selected):
    definition, entry, directory, ledger = unit(selected)
    def actual():
        (directory / "partial-return.bin").write_bytes(b"actual bytes before known error")
        raise ValueError("exposed known failure")
    with pytest.raises(RuntimeError, match="known native preparation call failed"):
        ledger.call("exposed.error", {}, actual)
    call = ledger.call_definitions[-1]
    assert selected.progress.recover(call).completion.operational_status is OperationalStatus.FAILED
    assert b"actual bytes before known error" in raw(selected, call, "files.raw")
    assert b"exposed known failure" in raw(selected, call, "call.return")
    complete_unit(selected.progress, selected.plan, entry, selected.root, directory, ledger,
                  succeeded=False, error="actual known error retained")
    assert selected.progress.recover(definition).completion.cost.cpu_seconds is None


def test_known_native_return_is_retained_when_extraction_fails(selected):
    _, _, directory, ledger = unit(selected)
    def actual():
        (directory / "returned.bin").write_bytes(b"known original returned raw bytes")
        return object()
    def broken_extractor(result):
        assert result is not None
        assert selected.store.inspect(ledger.call_definitions[-1]).state is NativeSubworkState.UNKNOWN_COMPLETION
        raise ValueError("exposed complete extraction unavailable")
    with pytest.raises(RuntimeError, match="known native preparation call failed"):
        ledger.call("exposed.extraction-error", {}, actual, realization=broken_extractor)
    call = ledger.call_definitions[-1]
    witness = json.loads(raw(selected, call, "call.witness"))["value"]
    assert witness["native_returned"] is True and witness["return_type"] == "object"
    assert witness["error_text"] is None
    returned = json.loads(raw(selected, call, "call.return"))["value"]
    assert "extraction_error_text" in json.loads(returned["realized_json"])
    assert "exposed complete extraction unavailable" in returned["error_text"]
    assert b"known original returned raw bytes" in raw(selected, call, "files.raw")


def test_interruption_keeps_uncertain_call_and_unit_and_refuses_replay(selected):
    definition, _, directory, ledger = unit(selected)
    def interrupted():
        (directory / "raw-prefix.bin").write_bytes(b"contacted but no authenticated complete return")
        raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        ledger.call("exposed.interrupted", {}, interrupted)
    call = ledger.call_definitions[-1]
    assert selected.store.inspect(call).state is NativeSubworkState.UNKNOWN_COMPLETION
    assert selected.store.inspect(definition).state is NativeSubworkState.UNKNOWN_COMPLETION
    for original in (call, definition):
        with pytest.raises(NativeSubworkUncertainContact):
            selected.progress.recover(original)
        with pytest.raises(NativeSubworkUncertainContact):
            selected.progress.begin(original)


def test_complete_unit_recovers_actual_conditional_operand_and_return_without_replay(selected):
    definition, entry, directory, ledger = unit(selected)
    (directory / "original-request.bin").write_bytes(b"full original selected request")
    calls = []
    def actual():
        calls.append(True)
        (directory / "actual-return.bin").write_bytes(b"full actual known return")
        return -7
    ledger.call("exposed.conditional-return", {"adverse": -7}, actual)
    complete_unit(selected.progress, selected.plan, entry, selected.root, directory, ledger,
                  succeeded=False, error="actual adverse value retained")
    original, = completed_call_custody(selected.progress, definition)
    assert original.call_state is NativeSubworkState.COMPLETED
    assert original.operand_state is NativeSubworkState.COMPLETED
    assert original.call_definition == ledger.call_definitions[0]
    assert b"full original selected request" in raw(selected, original.operand_definition, "files.raw")
    assert b"full actual known return" in raw(selected, original.call_definition, "files.raw")
    assert original.call_definition.configuration.object_fingerprint == sha256(
        raw(selected, original.operand_definition, "call.operand")).hexdigest()
    assert completed_call_custody(selected.progress, definition) == (original,)
    assert calls == [True]


def test_known_adverse_unit_retains_unknown_nested_call_without_recovery_or_replay(selected):
    definition, entry, directory, ledger = unit(selected)
    def lost():
        raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        ledger.call("exposed.contact-lost", {}, lost)
    # A known orchestration refusal can retain an unknown nested native contact.
    complete_unit(selected.progress, selected.plan, entry, selected.root, directory, ledger,
                  succeeded=False, error="orchestrator returned while nested completion is unknown")
    original, = completed_call_custody(selected.progress, definition)
    assert original.call == ledger.call_definitions[0].identity
    assert original.call_state is NativeSubworkState.UNKNOWN_COMPLETION
    assert original.call_definition is None and original.operand_definition is None
    with pytest.raises(NativeSubworkUncertainContact):
        selected.progress.begin(ledger.call_definitions[0])


def test_twelve_original_geometry_receipts_feed_twenty_four_models_without_replay(selected):
    count = 0
    for definition in selected.selected:
        if not definition.subwork_id.startswith("geometry."):
            continue
        entry = selected.progress.begin(definition)
        selected.progress.contact(entry)
        directory = selected.root / definition.subwork_id
        directory.mkdir()
        (directory / "complete-heavy.pdb").write_bytes(definition.subwork_id.encode())
        ledger = DurableCallLedger(selected.progress, selected.plan, selected.root, entry, directory)
        complete_unit(selected.progress, selected.plan, entry, selected.root, directory, ledger, succeeded=True)
        count += 1
    for construct, view, parameters in selected.plan.model_census:
        geometry = next(row for row in selected.selected if row.subwork_id == d.geometry_id(construct, view))
        definition = next(row for row in selected.selected if row.subwork_id == d.model_id(construct, view, parameters))
        entry = selected.progress.begin(definition)
        selected.progress.contact(entry)
        directory = selected.root / definition.subwork_id
        directory.mkdir()
        receipt = copy_completed_geometry(selected.progress, geometry, directory)
        assert (directory / "complete-heavy.pdb").read_bytes() == geometry.subwork_id.encode()
        assert receipt == ObjectIdentity.from_record(selected.progress.recover(geometry).receipt.receipt_id,
                                                    selected.progress.recover(geometry).receipt)
        ledger = DurableCallLedger(selected.progress, selected.plan, selected.root, entry, directory)
        complete_unit(selected.progress, selected.plan, entry, selected.root, directory, ledger,
                      succeeded=True, geometry=geometry.identity, geometry_receipt=receipt)
    assert count == 12
    assert all(state is NativeSubworkState.COMPLETED for _, state in census(selected.progress, selected.plan, selected.selected).states)
    definition = next(row for row in selected.selected if row.subwork_id.startswith("geometry."))
    original = selected.progress.recover(definition)
    assert b"complete-heavy.pdb" in gzip.decompress(b"".join(recover_unit(selected.progress, definition.identity, "files.raw", maximum_chunk_bytes=31)))
    assert selected.progress.recover(definition) == original


@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory"])
def test_unrepresented_file_types_refuse_before_actual_native_callback(selected, kind):
    _, _, directory, ledger = unit(selected)
    path = directory / "unrepresented"
    if kind == "symlink":
        path.symlink_to(sys.executable)
    elif kind == "fifo":
        os.mkfifo(path)
    else:
        path.mkdir()
    with pytest.raises((ValueError, OSError, RuntimeError)):
        ledger.call("exposed.not-entered", {}, lambda: pytest.fail("native callback entered"))
    assert not ledger.call_definitions


def test_native_file_mutation_cannot_satisfy_old_raw_census(selected):
    _, _, directory, _ = unit(selected)
    path = directory / "full.bin"
    path.write_bytes(b"original")
    selected_census = directory_census(directory, selected.root)
    path.write_bytes(b"changed!")
    with pytest.raises(ValueError, match="byte census"):
        b"".join(raw_archive_chunks(directory, selected.root, selected_census, maximum_chunk_bytes=3))


def test_complete_native_quantity_keeps_units_binary_values_and_array_shape():
    class Quantity:
        unit = "nanometer"
        def value_in_unit(self, unit):
            assert unit == self.unit
            return ((-0.0, 1.2345678901234567, 2.0),)
    result = selected_value(Quantity())
    assert result["unit"] == "nanometer"
    assert result["value"][0][0]["binary64_hex"] == "-0x0.0p+0"
    assert result["value"][0][0]["ieee754_binary64_be"] == "8000000000000000"
    assert result["value"][0][1]["binary64_hex"] == float(1.2345678901234567).hex()
    with pytest.raises(ValueError, match="unrepresented"):
        selected_value(object())


def test_numpy_scalar_vec3_quantity_and_arrays_retain_actual_dtype_shape_bits():
    import numpy as np
    # Distinct NaN payload, both signed zeros and nonfinite returned operands are
    # retained as raw data; this control does not declare them admissible science.
    values = np.array([0x8000000000000000, 0x7ff8000000000123,
                       0x7ff0000000000000, 0xfff0000000000000], dtype="<u8").view("<f8")
    class Vec3(tuple):
        pass
    class Quantity:
        unit = "nanometer"
        def value_in_unit(self, unit): return [Vec3((values[0], values[1], np.float64(1.25)))]
    result = selected_value(Quantity())["value"][0]
    for original, retained in zip((values[0], values[1], np.float64(1.25)), result, strict=True):
        assert retained["dtype"] == original.dtype.str and retained["shape"] == []
        assert bytes.fromhex(retained["full_native_bytes_hex"]) == original.tobytes()
    array = values.reshape((2, 2))[:, ::-1]
    retained = selected_value(array)
    assert retained["shape"] == [2, 2] and retained["source_strides"] == list(array.strides)
    assert bytes.fromhex(retained["full_native_bytes_hex"]) == array.tobytes(order="C")
    with pytest.raises(ValueError, match="nonnumeric"):
        selected_value(np.array([object()], dtype=object))


def test_large_native_positions_are_streamed_as_complete_file_operands(tmp_path):
    import numpy as np
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_instrumentation import write_full_positions
    original = np.arange(3 * 100_000, dtype="<f8").reshape((-1, 3))
    path = tmp_path / "complete-positions.json"
    write_full_positions(path, original)
    retained = json.loads(path.read_text())
    assert retained["shape"] == [100_000, 3]
    assert retained["dtype"] == "<f8"
    assert bytes.fromhex(retained["full_native_bytes_hex"]) == original.tobytes(order="C")


def test_tleap_environment_is_minimal_and_does_not_capture_inherited_credentials(selected, monkeypatch):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import selected_tleap_environment
    monkeypatch.setenv("EXPOSED_CREDENTIAL_SENTINEL", "never-retain-this-value")
    environment = selected_tleap_environment(selected.plan, selected.root)
    assert "EXPOSED_CREDENTIAL_SENTINEL" not in environment
    assert "never-retain-this-value" not in json.dumps(environment)
    assert environment["AMBERHOME"] and environment["LD_LIBRARY_PATH"]
    assert environment["OPENMM_CPU_THREADS"] == "1"


def test_network_refusal_precedes_resolution_and_keeps_only_redacted_event(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    path = tmp_path / "network-refusal.jsonl"
    script = """import socket, sys
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import refuse_external_network
refuse_external_network(sys.argv[1])
try:
    socket.getaddrinfo('exposed-never-contact.invalid', 443)
except PermissionError:
    pass
else:
    raise AssertionError('network guard failed')
"""
    result = subprocess.run([sys.executable, "-c", script, str(path)], cwd=repo,
        env={"PYTHONPATH": str(repo / "src"), "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr.decode()
    assert json.loads(path.read_text()) == {"event": "socket.getaddrinfo", "refused_before_effect": True}
    assert "exposed-never-contact" not in path.read_text()


def test_all_durable_owner_imports_are_cold_in_real_subprocess():
    repo = Path(__file__).resolve().parents[1]
    script = """import sys
class Refuse:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy','scipy','openmm','pdbfixer','parmed','pybamm','flint'}:
            raise AssertionError('unselected native/scientific import ' + fullname)
sys.meta_path.insert(0, Refuse())
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import durable_contracts, durable_roster, durable_preparation, durable_instrumentation, durable_native_entry
"""
    result = subprocess.run([sys.executable, "-c", script], cwd=repo,
        env={"PYTHONPATH": str(repo / "src"), "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr.decode()


def test_complete_selected_engine_file_link_and_actual_loaded_module_authentication(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import (
        authenticate_engine_stock, authenticate_loaded_engine_modules,
    )
    selected_file = tmp_path / "selected-engine-file.py"
    selected_file.write_bytes(b"exposed selected engine source, no engine or model\n")
    link = tmp_path / "selected-engine-link"
    link.symlink_to(selected_file.name)
    row = dict(path="exposed-engine.py", actual_path=str(selected_file), kind="file",
               size=selected_file.stat().st_size, sha256=sha256(selected_file.read_bytes()).hexdigest())
    inventory = dict(entries=[row, dict(path="exposed-engine-link", actual_path=str(link),
                                      kind="symlink", target=selected_file.name)])
    stock = {"source.engine-inventory": json.dumps(inventory)}
    assert authenticate_engine_stock(stock) == inventory
    link.unlink()
    link.symlink_to("unselected-target")
    with pytest.raises(ValueError, match="engine link changed"):
        authenticate_engine_stock(stock)
    link.unlink()
    link.symlink_to(selected_file.name)
    # Include every actually loaded selected array file; this fake additional
    # module is disclosed and never executes molecular science.
    monkeypatch.setitem(sys.modules, "numpy.exposed_native_module", SimpleNamespace(__file__=str(selected_file)))
    files = {}
    for name, module in tuple(sys.modules.items()):
        if name.split(".")[0] in {"numpy", "scipy", "openmm", "pdbfixer", "parmed"}:
            path = getattr(module, "__file__", None)
            if path is not None:
                actual = Path(path).resolve()
                files[str(actual)] = dict(actual_path=str(actual), kind="file", size=actual.stat().st_size,
                                         sha256=sha256(actual.read_bytes()).hexdigest())
    actual_inventory = dict(entries=list(files.values()))
    assert any(value["module"] == "numpy.exposed_native_module" for value in
               authenticate_loaded_engine_modules(actual_inventory))
    selected_file.write_bytes(b"exposed substituted engine source\n")
    with pytest.raises(ValueError, match="engine member changed"):
        authenticate_engine_stock(stock)
    with pytest.raises((ValueError, RuntimeError), match="changed selected bytes|exceeds its byte limit"):
        authenticate_loaded_engine_modules(actual_inventory)


def test_actual_fixer_mutation_and_missing_atom_returns_keep_full_positions_topology(selected):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_instrumentation import selected_fixer_factory
    definition, entry, directory, ledger = unit(selected)
    chain = SimpleNamespace(index=0, id="A")
    residue = SimpleNamespace(index=0, id="1", name="MET", chain=chain)
    atoms = [SimpleNamespace(index=index, name=name, residue=residue, element=SimpleNamespace(symbol="C"))
             for index, name in enumerate(("CA", "CB"))]
    class Fixer:
        def __init__(self):
            self.positions = [(0.0, -0.0, 1.0), (2.0, 3.0, 4.0)]
            self.topology = SimpleNamespace(atoms=lambda: iter(atoms), bonds=lambda: iter(((atoms[0], atoms[1]),)))
            self.missingResidues, self.missingAtoms, self.missingTerminals = {}, {}, {}
        def applyMutations(self, mutations, chain_id):
            assert mutations == ["ILE-95-MET"] and chain_id == "A"
            self.positions[1] = (9.0, 8.0, 7.0)
        def findMissingAtoms(self):
            self.missingResidues = {(0, 1): ["GLY"]}
    class PDBFile:
        @staticmethod
        def writeFile(topology, positions, output, keepIds):
            assert keepIds
            output.write(json.dumps({"atoms": [atom.name for atom in topology.atoms()], "positions": positions}))
    factory = selected_fixer_factory(Fixer, ledger, directory, SimpleNamespace(PDBFile=PDBFile))
    fixer = ledger.call("completion.pdbfixer", {}, factory)
    fixer.applyMutations(["ILE-95-MET"], "A")
    fixer.findMissingAtoms()
    complete_unit(selected.progress, selected.plan, entry, selected.root, directory, ledger, succeeded=True)
    custody = completed_call_custody(selected.progress, definition)
    assert len(custody) == 3
    returned = raw(selected, custody[-1].call_definition, "files.raw")
    assert b'"GLY"' in returned and b'"full_native_bytes_hex"' not in returned
    assert b'"bonds":[[0,1]]' in returned and b'"ieee754_binary64_be":"8000000000000000"' in returned
    assert b'9.0, 8.0, 7.0' in returned


@pytest.mark.parametrize("dtype,strided", [(">f8", False), (">f8", True), ("<f8", True)])
def test_full_position_file_preserves_non_native_byteorder_noncontiguous_shape_and_nan_payload(tmp_path, dtype, strided):
    import numpy as np
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_instrumentation import write_full_positions
    value = np.arange(36, dtype=dtype).reshape(6, 6)
    # Deliberately chosen binary64 payload, negative zero and infinity survive.
    value.view(dtype.replace("f8", "u8"))[0, :3] = (0x7ff8000000000123, 0x8000000000000000, 0x7ff0000000000000)
    if strided:
        value = value[:, ::2]
    path = tmp_path / "original-position-array.json"
    write_full_positions(path, value)
    payload = json.loads(path.read_text())
    assert payload["dtype"] == value.dtype.str
    assert payload["shape"] == list(value.shape) and payload["source_strides"] == list(value.strides)
    assert bytes.fromhex(payload["full_native_bytes_hex"]) == value.tobytes(order="C")


class ExposedDurableRunner(DurablePreparationRunner):
    """Actual inherited launcher/relay with a disclosed solver-free child."""
    def _entry_target(self):
        path = Path(__file__).with_name("rubisco_durable_entry.py")
        return "tests.rubisco_durable_entry", "exposed_child", path, "tests/rubisco_durable_entry.py"


@pytest.mark.parametrize("selected", ["pilot"], indirect=True)
@pytest.mark.parametrize("phase,state", [
    ("success", NativeSubworkState.COMPLETED),
    ("before-begin", NativeSubworkState.NOT_ENTERED),
    ("after-begin", NativeSubworkState.BEGUN),
    ("after-contact", NativeSubworkState.UNKNOWN_COMPLETION),
    ("after-call-completion", NativeSubworkState.UNKNOWN_COMPLETION),
    ("after-unit-completion", NativeSubworkState.COMPLETED),
])
def test_actual_isolated_child_and_streaming_keep_pilot_full_census_and_loss_states(selected, phase, state):
    invocation = selected.root.parent / "selected-invocation.json"
    invocation.write_text(json.dumps({"plan": selected.plan.canonical_bytes().decode(),
        "definitions": [row.canonical_bytes().decode() for row in selected.selected],
        "phase": phase, "returncode": 0}))
    original_invocation = invocation.read_bytes()
    selected.root.rmdir()
    repo = Path(__file__).resolve().parents[1]
    environment = (("LC_ALL", "C"), ("PATH", "/usr/bin:/bin"),
        ("PYTHONDONTWRITEBYTECODE", "1"), ("PYTHONPATH", str(repo / "src") + os.pathsep + str(repo)))
    attempted = tuple(sorted((*selected.plan.attempted_geometry_ids, *selected.plan.attempted_model_ids)))
    output_ids = tuple((unit_id, "ordinary." + unit_id) for unit_id in attempted)
    ports = tuple(sorted((WorkerOutputPort("preparation.census", d.DurablePreparationCensus.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json"), *(WorkerOutputPort(output_id,
        "empirical-lawhood/source/capture-assured-uninterpreted-public-bytes", ArtifactProfile.RAW_SOURCE_BYTES,
        "application/gzip") for _, output_id in output_ids)), key=lambda row: row.output_id))
    context = replace(selected.context, output_ports=ports)
    runner = ExposedDurableRunner(selected.plan, str(invocation), selected.selected, environment, output_ids)
    executor = LocalProcessExecutor(scratch_root=selected.store.plane.root)
    if phase == "success":
        result = executor.execute(runner, context, timeout_seconds=None, native_subwork=selected.store)
        assert result.checks[0].passed
        outputs = {row.output_id: row for row in result.outputs}
        assert set(outputs) == {row.output_id for row in ports}
        for unit_id, output_id in output_ids:
            definition = next(row for row in selected.selected if row.subwork_id == unit_id)
            output = outputs[output_id]
            try:
                streamed = b"".join(output.source.chunks(1024 * 1024))
            finally:
                output.source.close()
            assert streamed == b"".join(selected.progress.iter_completed_output(definition, "files.raw"))
    else:
        with pytest.raises(TaskProcessError):
            executor.execute(runner, context, timeout_seconds=None, native_subwork=selected.store)
    first = next(row for row in selected.selected if row.subwork_id == attempted[0])
    assert selected.store.inspect(first).state is state
    assert all(selected.store.inspect(row).state is NativeSubworkState.NOT_ENTERED for row in selected.selected
               if row.subwork_id not in attempted and row.subwork_id != "preparation.metadata")
    metadata = next(row for row in selected.selected if row.subwork_id == "preparation.metadata")
    retained = json.loads(raw(selected, metadata, "preparation.census"))["value"]
    assert len(retained["states"]) == 36 and retained["physical_independent_units"] == 0
    invocation.write_text('{"original-path-now-mutated":true}')
    assert original_invocation in raw(selected, metadata, "files.raw")
    assert (selected.root / "metadata/invocation.json").read_bytes() == original_invocation
    if state is NativeSubworkState.UNKNOWN_COMPLETION:
        with pytest.raises(NativeSubworkUncertainContact):
            selected.progress.recover(first)
    if phase == "after-call-completion":
        calls = tuple(selected.store.iter_roster_definitions(first.parent_contact, first.subwork_id + ".call.000001.roster"))
        assert len(calls) == 1 and selected.progress.recover(calls[0]).completion is not None


@pytest.mark.parametrize("selected", ["pilot"], indirect=True)
def test_existing_workdir_refuses_fresh_launcher_and_products_recover_separately(selected):
    attempted = tuple(sorted((*selected.plan.attempted_geometry_ids, *selected.plan.attempted_model_ids)))
    runner = ExposedDurableRunner(selected.plan, "/unused-invocation", selected.selected,
        (("PYTHONDONTWRITEBYTECODE", "1"),), tuple((unit_id, "ordinary." + unit_id) for unit_id in attempted))
    with pytest.raises(FileExistsError):
        runner.execute_streaming_with_native_subwork(selected.context, selected.progress,
                                                    SimpleNamespace(write=lambda *_: pytest.fail("unexpected output")))
    assert all(state is NativeSubworkState.NOT_ENTERED for _, state in census(
        selected.progress, selected.plan, selected.selected).states)


@pytest.mark.parametrize("selected", ["entry-mismatch"], indirect=True)
def test_changed_selected_entry_source_binding_refuses_before_any_process_or_contact(selected):
    selected.root.rmdir()
    attempted = tuple(sorted((*selected.plan.attempted_geometry_ids, *selected.plan.attempted_model_ids)))
    runner = ExposedDurableRunner(selected.plan, "/unused-invocation", selected.selected,
        (("PYTHONDONTWRITEBYTECODE", "1"),), tuple((key, "ordinary." + key) for key in attempted))
    with pytest.raises(ValueError, match="actual plan code-source binding"):
        runner.execute_streaming_with_native_subwork(selected.context, selected.progress,
                                                    SimpleNamespace(write=lambda *_: pytest.fail("unexpected output")))
    assert all(selected.store.inspect(row).state is NativeSubworkState.NOT_ENTERED for row in selected.selected)


def test_instrumented_minimizer_step_context_bind_full_current_system_integrator_state(selected):
    _, _, directory, ledger = unit(selected)
    class Integrator:
        def __init__(self, *args):
            self.seed, self.steps, self.arguments = 0, 0, args
        def step(self, count):
            self.steps += count
        def setRandomNumberSeed(self, seed):
            self.seed = seed
    class Platform:
        def getName(self): return "CPU"
        def getPropertyNames(self): return ("Threads",)
        def getPropertyValue(self, context, name): return "1"
    class Context:
        def __init__(self, system, integrator):
            self.positions, self.system, self.integrator = [[0.0, 1.0, 2.0]], system, integrator
            self.parameters = {"lambda": 0.0}
        def getPlatform(self): return Platform()
        def getState(self, **kwargs):
            return {"positions": self.positions, "parameters": self.parameters, "steps": self.integrator.steps}
        def setPositions(self, positions): self.positions = positions
        def setState(self, state): self.positions = state["positions"]
        def setParameter(self, name, value): self.parameters[name] = value
    class Minimizer:
        @staticmethod
        def minimize(context, **kwargs): context.positions = [[9.0, 8.0, 7.0]]
    class Serializer:
        @staticmethod
        def serialize(value):
            return json.dumps(value if type(value) is dict else {
                name: row for name, row in vars(value).items() if not callable(row)}, sort_keys=True)
    mm = SimpleNamespace(Context=Context, LangevinIntegrator=Integrator,
                         LocalEnergyMinimizer=Minimizer, XmlSerializer=Serializer)
    restore = instrument_completion(mm, ledger, directory)
    try:
        integrator = mm.LangevinIntegrator(0.002)
        integrator.setRandomNumberSeed(173)
        context = mm.Context({"particles": 1, "all_force_terms": [0, -7, 13]}, integrator)
        context.setPositions([[3.0, 4.0, 5.0]])
        mm.LocalEnergyMinimizer.minimize(context, tolerance=1.0, maxIterations=0)
        integrator.step(37)
    finally:
        restore()
    for role in ("completion.minimization", "completion.integration", "completion.set-positions"):
        row = next(row for row in ledger.calls if row.role == role)
        request = json.loads(row.requested_json)
        assert {"system", "integrator", "state", "context_call"}.issubset(request)
        assert request["system"]["sha256"] and request["state"]["sha256"]
    minimizer = next(row for row in ledger.calls if row.role == "completion.minimization")
    assert json.loads(minimizer.requested_json)["native_internal_iteration_count"] == "NOT_EXPOSED_BY_NATIVE_API"
    step = next(row for row in ledger.calls if row.role == "completion.integration")
    assert json.loads(step.requested_json)["steps"] == 37
    assert mm.Context is Context and mm.LangevinIntegrator is Integrator
    assert "step" not in vars(integrator) and "getState" not in vars(context)
