# SPDX-License-Identifier: MPL-2.0
"""Actual selected-child controls using exposed software operands, no native science."""

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import pytest

from empirical_lawhood.infrastructure import isolated_native_subwork as bridge
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, WorkerPreflightError
from empirical_lawhood.infrastructure.native_subwork_ipc import NativeSubworkPipeService, NativeSubworkReply, NativeSubworkRequest, PipeNativeSubworkProgress
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import ReceiptCheck, RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntryReturn, IsolatedNativeEntrySelection, IsolatedNativeInvocation, IsolatedNativeProcessStart
from empirical_lawhood.runtime.native_subwork import NativeSubworkOutput, NativeSubworkReceiptPublicationPending, NativeSubworkRoster, NativeSubworkState
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeWork, PreparedWorkerEnvironment, WorkerPreflightMismatch, WorkerPreflightResult
from tests.runtime_platform.test_native_subwork import ExposedInput, _store
from tests.runtime_platform.test_worker_preflight import ExposedReadRunner, _case, _literal_readiness


ENTRY_SOURCE = '''"""Exposed exact-byte joins and PID markers; no solver or scientific verdict."""
import json
import os
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntryReturn, IsolatedNativeProcessStart
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkOutput
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeWork

def _record(raw, kind):
    return decode_canonical_bytes(raw.encode(), kind, maximum_bytes=len(raw.encode()))

def prepare(*, invocation, expected_parent, prepared_contract):
    global prepared_pid, selected_work
    data = json.loads(invocation.read())
    original = _record(data["contract"], PreparedInvocationContract)
    scientific_work = replace(prepared_contract.native_work, isolated_selection=None, isolated_environment=None,
        isolated_diagnostics=())
    scientific_contract = replace(prepared_contract, native_work=scientific_work)
    if original != scientific_contract:
        raise ValueError("exposed original invocation contract differs")
    if _record(data["parent"], NativeEffectContact) != expected_parent:
        raise ValueError("exposed full anticipated parent differs")
    observed = data["inputs"]
    if tuple(row["artifact_id"] for row in observed) != tuple(row.artifact_id for row in original.inputs):
        raise ValueError("exposed complete embedded input census differs")
    for row, selected in zip(observed, original.inputs, strict=True):
        raw = row["raw"].encode()
        if len(raw) != selected.binding.size_bytes or sha256(raw).hexdigest() != selected.physical_sha256:
            raise ValueError("exposed embedded input bytes differ: " + selected.artifact_id)
    selected = _record(data["work"], PreparedNativeWork)
    if selected != original.native_work:
        raise ValueError("exposed complete native work differs")
    selected = replace(selected, isolated_selection=prepared_contract.native_work.isolated_selection,
        isolated_environment=prepared_contract.native_work.isolated_environment,
        isolated_diagnostics=prepared_contract.native_work.isolated_diagnostics)
    prepared_pid = os.getpid()
    selected_work = selected
    return selected

def refuse(**arguments):
    raise ValueError("exposed scientific-operand join refused")

def boolean_result(**arguments):
    return True

def missing_result(**arguments):
    return None

def changed_work(**arguments):
    from dataclasses import replace
    return replace(prepare(**arguments), scientific_unit_ids=("substituted.unit",))

def enter(progress, invocation):
    data = json.loads(invocation.read())
    expected = _record(data["parent"], NativeEffectContact)
    if progress.parent_contact != expected:
        raise ValueError("exposed actual parent differs")
    metadata = next(row for row in selected_work.definitions if row.subwork_id == "entry.metadata")
    manifest, = progress.inspect(metadata).outputs
    lifecycle = replace(metadata, subwork_id="entry.lifecycle", operation_id="exposed.selected-entry.lifecycle",
        configuration=invocation.selection, roster_id="conditional.exposed.isolated",
        input_materialization_ids=tuple(sorted((*metadata.input_materialization_ids, manifest.materialization.materialization_id))),
        outputs=(NativeSubworkOutput("process.return", IsolatedNativeEntryReturn.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),
            NativeSubworkOutput("process.start", IsolatedNativeProcessStart.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")))
    state = progress.inspect(lifecycle).state.value
    if state != "UNKNOWN_COMPLETION":
        raise ValueError("exposed lifecycle was not contacted before Proceed")
    with Path("entry-marker.json").open("x") as stream:
        json.dump(dict(prepared_pid=prepared_pid, entry_pid=os.getpid(),
            invocation_sha256=sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            lifecycle_state=state), stream, sort_keys=True)
'''


@dataclass
class _SelectedCase:
    plane: object
    bundle: object
    context: object
    contract: object
    parent: object
    selection: IsolatedNativeEntrySelection
    environment: dict
    root: Path
    data: dict
    metadata: object

    def rebind_data(self):
        raw = json.dumps(self.data, sort_keys=True, separators=(",", ":")).encode()
        Path(self.selection.invocation_path).write_bytes(raw)
        self.selection = replace(self.selection, invocation_sha256=sha256(raw).hexdigest())

    def diagnostic(self, *, entry_preflight="prepare", contract=None, selection=None, prefix_selected=True):
        with (self.root / "diagnostic.stdout").open("xb") as stdout, (self.root / "diagnostic.stderr").open("xb") as stderr:
            return bridge.preflight_isolated_native_entry(selection or self.selection,
                prepared_contract=contract or self.contract, entry_preflight=entry_preflight,
                environment=self.environment, cwd=self.root, stdout=stdout, stderr=stderr,
                prefix_selected=prefix_selected)

    def close(self):
        self.bundle.close()


def _selected_case(tmp_path):
    plane, bundle, _, context, contract, parent = _case(tmp_path, actual=True, native=True)
    root = tmp_path / "selected-child"
    root.mkdir()
    source = root / "exposed_selected_entry.py"
    source.write_text(ENTRY_SOURCE)
    environment = dict(os.environ, PYTHONPATH=os.pathsep.join((str(Path(bridge.__file__).resolve().parents[2]),
        str(root))), PYTHONDONTWRITEBYTECODE="1")
    selected_environment = PreparedWorkerEnvironment(str(Path(sys.executable).absolute()),
        sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(), str(Path(sys.prefix).absolute()),
        tuple(sorted(environment.items())))
    first = contract.native_definitions[0]
    metadata = replace(first, subwork_id="entry.metadata", operation_id="exposed.selected-entry.metadata",
        streams=(), outputs=(NativeSubworkOutput("process.selection", IsolatedNativeEntrySelection.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json"),))
    definitions = tuple(sorted((*contract.native_definitions, metadata), key=lambda row: row.subwork_id))
    work = replace(contract.native_work, definitions=definitions,
        rosters=(NativeSubworkRoster("selected.native-subwork", parent, tuple(row.identity for row in definitions)),))
    contract = replace(contract, environment=selected_environment, native_work=work)
    inputs = []
    for port in context.input_ports:
        cursor = port.cursor()
        try:
            inputs.append(dict(artifact_id=port.artifact_id, raw=cursor.read().decode()))
        finally:
            cursor.close()
    data = dict(contract=contract.canonical_bytes().decode(), parent=parent.canonical_bytes().decode(),
        work=work.canonical_bytes().decode(), inputs=inputs)
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    invocation = root / "invocation.json"
    invocation.write_bytes(raw)
    selection = IsolatedNativeEntrySelection("exposed.selected-entry", selected_environment.interpreter_path,
        selected_environment.interpreter_sha256, source.stem, "enter", str(source), sha256(source.read_bytes()).hexdigest(),
        str(invocation), sha256(raw).hexdigest(), bridge.selected_environment_sha256(environment))
    return _SelectedCase(plane, bundle, context, contract, parent, selection, environment, root, data, metadata)


def _assert_diagnostic_has_no_entry_effect(case):
    assert not (case.root / "entry-marker.json").exists()
    assert not (case.root / "isolated-native-process-start.json").exists()
    assert not (case.root / "isolated-native-process-return.json").exists()
    assert _store(case.plane, case.parent).parent_contacts.read(case.context.run_id, case.context.task_id) is None
    assert all(port.bytes_read == 0 for port in case.context.input_ports)


class _LiteralMessages:
    """Disclosed malformed transport values; these are not producing observations."""

    def __init__(self, values):
        self.values = iter(values)

    def recv(self):
        return next(self.values)


def _literal_handshake(case):
    return bridge._Handshake(case.selection.identity, case.parent, case.selection.interpreter_sha256,
        case.selection.entry_source_sha256, case.selection.invocation_sha256, case.selection.environment_sha256)


def test_parent_positive_ready_requires_the_actual_selected_handshake(tmp_path):
    case = _selected_case(tmp_path)
    try:
        with pytest.raises(ValueError, match="actual selected handshake"):
            bridge._receive_prepared_ready(_LiteralMessages((_literal_readiness(case.contract),)),
                case.selection, case.contract)
        _assert_diagnostic_has_no_entry_effect(case)
    finally:
        case.close()


@pytest.mark.parametrize("field", ("actual_interpreter_sha256", "actual_entry_source_sha256", "actual_invocation_sha256",
    "actual_environment_sha256", "parent"))
def test_parent_requires_the_exact_full_selected_child_handshake(tmp_path, field):
    case = _selected_case(tmp_path)
    try:
        value = "8" * 64 if field != "parent" else replace(case.parent,
            execution_task=replace(case.parent.execution_task, object_fingerprint="8" * 64))
        handshake = replace(_literal_handshake(case), **{field: value})
        with pytest.raises(ValueError, match="actual selection or full anticipated parent"):
            bridge._receive_prepared_ready(_LiteralMessages((handshake, _literal_readiness(case.contract))),
                case.selection, case.contract)
        _assert_diagnostic_has_no_entry_effect(case)
    finally:
        case.close()


@pytest.mark.parametrize("field,value", (("dependency_lock_sha256", "8" * 64), ("observed_git_head", "8" * 40)))
def test_parent_refuses_changed_positive_source_report_before_entry(tmp_path, field, value):
    case = _selected_case(tmp_path)
    try:
        result = _literal_readiness(case.contract)
        result = replace(result, producing_provenance=replace(result.producing_provenance, **{field: value}))
        with pytest.raises(ValueError, match="complete prepared source"):
            bridge._receive_prepared_ready(_LiteralMessages((_literal_handshake(case), result)),
                case.selection, case.contract)
        _assert_diagnostic_has_no_entry_effect(case)
    finally:
        case.close()


def test_parent_retains_failed_selection_report_without_positive_handshake(tmp_path):
    case = _selected_case(tmp_path)
    try:
        failed = WorkerPreflightResult(case.contract.identity, None, None,
            (WorkerPreflightMismatch("specialist.selection", "disclosed actual selection refusal"),))
        assert bridge._receive_prepared_ready(_LiteralMessages((failed,)), case.selection, case.contract) == failed
        _assert_diagnostic_has_no_entry_effect(case)
    finally:
        case.close()


@pytest.mark.parametrize("changed", ("missing-selection", "missing-environment", "interpreter", "full-environment"))
def test_retained_isolated_pair_requires_both_exact_selections_and_complete_environment(tmp_path, changed):
    case = _selected_case(tmp_path)
    try:
        selection, environment = case.selection, case.contract.environment
        if changed == "missing-selection":
            selection = None
        elif changed == "missing-environment":
            environment = None
        elif changed == "interpreter":
            selection = replace(selection, interpreter_sha256="8" * 64)
        else:
            selection = replace(selection, environment_sha256="8" * 64)
        with pytest.raises(ValueError, match="isolated"):
            replace(case.contract.native_work, isolated_selection=selection, isolated_environment=environment)
    finally:
        case.close()


def test_retained_work_contract_and_readiness_have_explicit_new_record_revisions(tmp_path):
    case = _selected_case(tmp_path)
    try:
        work = replace(case.contract.native_work, isolated_selection=case.selection,
            isolated_environment=case.contract.environment)
        contract = replace(case.contract, native_work=work)
        ready = replace(_literal_readiness(contract), native_work=work)
        for record, kind in ((work, PreparedNativeWork), (contract, PreparedInvocationContract), (ready, WorkerPreflightResult)):
            assert record.VERSION == "1.1.0"
            raw = record.canonical_bytes()
            assert decode_canonical_bytes(raw, kind, maximum_bytes=len(raw)).fingerprint() == record.fingerprint()
            old_tag = json.loads(raw)
            old_tag["version"] = "1.0.0"
            substituted = (json.dumps(old_tag, sort_keys=True, separators=(",", ":")) + "\n").encode()
            with pytest.raises(ValueError):
                decode_canonical_bytes(substituted, kind, maximum_bytes=len(substituted))
    finally:
        case.close()


def _literal_diagnostics(case):
    # These values test closed record structure, not actual producing evidence.
    selected = replace(case.contract.native_work, isolated_selection=case.selection,
        isolated_environment=case.contract.environment)
    observed = replace(_literal_readiness(case.contract), mismatches=(WorkerPreflightMismatch("worker.prefix",
        "disclosed unselected-prefix observation"),))
    projection = replace(case.contract, native_work=selected)
    ready = _literal_readiness(projection)
    retained = replace(selected, isolated_diagnostics=(observed, ready))
    return retained, observed, ready


@pytest.mark.parametrize("changed", ("order", "recursive", "too-many", "wrong-unit"))
def test_retained_diagnostics_refuse_recursive_reordered_or_foreign_work_snapshots(tmp_path, changed):
    case = _selected_case(tmp_path)
    try:
        retained, observed, ready = _literal_diagnostics(case)
        if changed == "order":
            values = (ready, observed)
        elif changed == "recursive":
            values = (observed, replace(ready, native_work=retained))
        elif changed == "too-many":
            values = (observed, ready, ready)
        else:
            foreign = replace(ready.native_work, scientific_unit_ids=("foreign.unit",))
            values = (observed, replace(ready, native_work=foreign))
        with pytest.raises(ValueError, match="diagnostic|recursive|work"):
            replace(retained, isolated_diagnostics=values)
    finally:
        case.close()


@pytest.mark.parametrize("changed", ("source-lock", "positive-invocation"))
def test_retained_positive_diagnostics_require_exact_source_and_full_invocation_fingerprint(tmp_path, changed):
    case = _selected_case(tmp_path)
    try:
        retained, observed, ready = _literal_diagnostics(case)
        if changed == "source-lock":
            ready = replace(ready, producing_provenance=replace(ready.producing_provenance, dependency_lock_sha256="8" * 64))
        else:
            ready = replace(ready, invocation=replace(ready.invocation, object_fingerprint="8" * 64))
        work = replace(retained, isolated_diagnostics=(observed, ready))
        with pytest.raises(ValueError, match="implementation|invocation|original task/input/output selection"):
            replace(case.contract, native_work=work)
    finally:
        case.close()


def test_isolated_sealed_cursor_retains_original_binding_and_refuses_late_rebinding(tmp_path):
    case = _selected_case(tmp_path)
    port = bridge._seal_invocation(case.selection)
    bound = replace(port, prepared_invocation=case.contract)
    cursor = None
    try:
        cursor = bound.cursor()
        assert cursor.prepared_invocation is case.contract
        assert cursor.read(7) == Path(case.selection.invocation_path).read_bytes()[:7]
        assert bound.bytes_read == 0
        foreign = replace(case.contract, invocation_id="foreign.invocation")
        object.__setattr__(bound, "prepared_invocation", foreign)
        with pytest.raises(ValueError, match="original prepared binding"):
            bound.read(1)
        with pytest.raises(ValueError, match="original prepared binding"):
            bound.cursor()
        assert bound.bytes_read == 0
    finally:
        if cursor is not None:
            cursor.close()
        bound.close()
        case.close()


def test_isolated_port_refuses_a_foreign_selection_anchor_for_bound_work(tmp_path):
    case = _selected_case(tmp_path)
    port = bridge._seal_invocation(case.selection)
    try:
        selected = replace(case.contract.native_work, isolated_selection=case.selection,
            isolated_environment=case.contract.environment)
        contract = replace(case.contract, native_work=selected)
        with pytest.raises(ValueError, match="frozen selection/input binding"):
            IsolatedNativeInvocation(replace(case.selection.identity, object_fingerprint="8" * 64),
                port.size_bytes, port.content_sha256, port._reader, contract)
    finally:
        port.close()
        case.close()


def test_actual_selected_child_ready_then_stop_has_actual_source_environment_and_no_entry_effect(tmp_path):
    case = _selected_case(tmp_path)
    try:
        result = case.diagnostic()
        assert result.ready and result.invocation == case.contract.identity
        assert result.environment.fingerprint() == case.contract.environment.fingerprint()
        assert result.native_work.fingerprint() == case.contract.native_work.fingerprint()
        assert result.producing_provenance.package_sources == case.contract.implementation.package_sources
        assert result.producing_provenance.code_sources_sha256 == case.contract.implementation.code_sources_sha256
        assert result.producing_provenance.dependency_lock_sha256 == case.contract.implementation.dependency_lock_sha256
        _assert_diagnostic_has_no_entry_effect(case)
    finally:
        case.close()


def test_actual_selected_child_observed_prefix_does_not_select_it_or_create_readiness(tmp_path):
    case = _selected_case(tmp_path)
    try:
        result = case.diagnostic(prefix_selected=False)
        assert not result.ready
        assert "worker.prefix" in {row.operand_id for row in result.mismatches}
        assert result.environment.prefix == sys.prefix
        assert result.native_work.fingerprint() == case.contract.native_work.fingerprint()
        _assert_diagnostic_has_no_entry_effect(case)
    finally:
        case.close()


def test_actual_selected_child_binds_only_sole_prefix_observation_then_reuses_the_frozen_pair(tmp_path):
    case = _selected_case(tmp_path)
    try:
        with (case.root / "prepare.stdout").open("xb") as stdout, (case.root / "prepare.stderr").open("xb") as stderr:
            work, observations = bridge.prepare_isolated_native_work(case.selection,
                prepared_contract=case.contract, entry_preflight="prepare", environment=case.environment,
                cwd=case.root, stdout=stdout, stderr=stderr)
        first, confirmed = observations
        assert not first.ready and tuple(row.operand_id for row in first.mismatches) == ("worker.prefix",)
        assert confirmed.ready and work.isolated_selection == case.selection
        assert work.isolated_environment.fingerprint() == first.environment.fingerprint() == confirmed.environment.fingerprint()
        assert replace(work, isolated_selection=None, isolated_environment=None,
            isolated_diagnostics=()).fingerprint() == case.contract.native_work.fingerprint()
        assert tuple(row.fingerprint() for row in work.isolated_diagnostics) == tuple(row.fingerprint() for row in observations)
        assert all(not row.native_work.isolated_diagnostics for row in observations)
        selected_contract = replace(case.contract, native_work=work)
        with (case.root / "reuse.stdout").open("xb") as stdout, (case.root / "reuse.stderr").open("xb") as stderr:
            reused, following = bridge.prepare_isolated_native_work(case.selection,
                prepared_contract=selected_contract, entry_preflight="prepare", environment=case.environment,
                cwd=case.root, stdout=stdout, stderr=stderr)
        assert reused.fingerprint() == work.fingerprint() and len(following) == 1 and following[0].ready
        with (case.root / "drift.stdout").open("xb") as stdout, (case.root / "drift.stderr").open("xb") as stderr:
            with pytest.raises(ValueError, match="frozen selection/full environment"):
                bridge.prepare_isolated_native_work(replace(case.selection, invocation_sha256="8" * 64),
                    prepared_contract=selected_contract, entry_preflight="prepare", environment=case.environment,
                    cwd=case.root, stdout=stdout, stderr=stderr)
        _assert_diagnostic_has_no_entry_effect(case)
    finally:
        case.close()


def test_actual_selected_child_does_not_adopt_prefix_when_other_prerequisites_refuse(tmp_path):
    case = _selected_case(tmp_path)
    try:
        with (case.root / "prepare.stdout").open("xb") as stdout, (case.root / "prepare.stderr").open("xb") as stderr:
            with pytest.raises(WorkerPreflightError) as refused:
                bridge.prepare_isolated_native_work(case.selection,
                    prepared_contract=case.contract, entry_preflight="refuse", environment=case.environment,
                    cwd=case.root, stdout=stdout, stderr=stderr)
        operands = {row.operand_id for row in refused.value.result.mismatches}
        assert {"worker.prefix", "specialist.work"}.issubset(operands)
        assert case.contract.native_work.isolated_selection is None
        assert case.contract.native_work.isolated_environment is None
        _assert_diagnostic_has_no_entry_effect(case)
    finally:
        case.close()


@pytest.mark.parametrize("entry_preflight", (None, "missing_function", "refuse", "boolean_result", "missing_result", "changed_work"))
def test_actual_selected_child_refuses_missing_invalid_or_changed_pure_preparation_without_contact(tmp_path, entry_preflight):
    case = _selected_case(tmp_path)
    try:
        result = case.diagnostic(entry_preflight=entry_preflight)
        assert not result.ready
        assert {row.operand_id for row in result.mismatches} & {"specialist.preparer", "specialist.work"}
        _assert_diagnostic_has_no_entry_effect(case)
    finally:
        case.close()


@pytest.mark.parametrize("changed", ("embedded-bytes", "embedded-census", "anticipated-parent", "unit-census", "slot-census"))
def test_rehashed_actual_invocation_cannot_substitute_original_operands_or_native_scope(tmp_path, changed):
    case = _selected_case(tmp_path)
    try:
        if changed == "embedded-bytes":
            config = next(row for row in case.data["inputs"] if row["artifact_id"] == case.context.config.artifact_id)
            config["raw"] = ExposedInput("exposed.config", "modified exact bytes").canonical_bytes().decode()
        elif changed == "embedded-census":
            case.data["inputs"].pop()
        elif changed == "anticipated-parent":
            parent = replace(case.parent, execution_task=replace(case.parent.execution_task, object_fingerprint="8" * 64))
            case.data["parent"] = parent.canonical_bytes().decode()
        else:
            field = "scientific_unit_ids" if changed == "unit-census" else "native_effect_slot_ids"
            case.data["work"] = replace(case.contract.native_work, **{field: ("substituted.scope",)}).canonical_bytes().decode()
        case.rebind_data()
        result = case.diagnostic()
        assert not result.ready and "specialist.work" in {row.operand_id for row in result.mismatches}
        _assert_diagnostic_has_no_entry_effect(case)
    finally:
        case.close()


@pytest.mark.parametrize("changed", ("prefix", "environment", "source-lock", "task-fingerprint"))
def test_actual_selected_child_refuses_complete_contract_source_environment_or_task_substitution(tmp_path, changed):
    case = _selected_case(tmp_path)
    try:
        if changed == "prefix":
            contract = replace(case.contract, environment=replace(case.contract.environment, prefix="/exposed/wrong-prefix"))
            expected = "worker.environment"
        elif changed == "environment":
            bindings = dict(case.contract.environment.selected_environment, OMP_NUM_THREADS="2")
            contract = replace(case.contract, environment=replace(case.contract.environment,
                selected_environment=tuple(sorted(bindings.items()))))
            expected = "worker.environment"
        elif changed == "source-lock":
            contract = replace(case.contract, implementation=replace(case.contract.implementation, dependency_lock_sha256="8" * 64))
            expected = "worker.implementation"
        else:
            # Cold construction must refuse a consistently encoded attempt to
            # keep the original task while changing its selected fingerprint.
            with pytest.raises(ValueError, match="original execution task fingerprint"):
                replace(case.contract, execution_task=replace(case.contract.execution_task, object_fingerprint="8" * 64),
                    native_work=None)
            return
        case.data["contract"] = contract.canonical_bytes().decode()
        case.rebind_data()
        result = case.diagnostic(contract=contract)
        assert not result.ready and expected in {row.operand_id for row in result.mismatches}
        _assert_diagnostic_has_no_entry_effect(case)
    finally:
        case.close()


class _ServiceConnection:
    """Exercise the actual guarded service and reply types, without test signers."""

    def __init__(self, service):
        self.service = service
        self.reply = None
        self.operations = []

    def send(self, value):
        if type(value) is NativeSubworkRequest:
            self.operations.append(value.operation)
            self.service.handle(value, self)
        else:
            assert type(value) is NativeSubworkReply
            self.reply = value

    def recv(self):
        value, self.reply = self.reply, None
        return value


def _begun_lifecycle(case):
    store = _store(case.plane, case.parent, case.bundle.manifests, prepared_invocation=case.contract)
    store.parent_contacts.begin(case.parent)
    service = NativeSubworkPipeService(store, case.context, case.root)
    connection = _ServiceConnection(service)
    progress = PipeNativeSubworkProgress(connection)
    progress.freeze_roster(case.contract.native_rosters[0], definitions=case.contract.native_definitions)
    metadata_entry = progress.begin(case.metadata)
    progress.contact(metadata_entry)
    raw = case.selection.canonical_bytes()
    manifest = progress.publish_output(metadata_entry, "process.selection", iter((raw,)),
        maximum_bytes=len(raw), expected_size_bytes=len(raw), expected_physical_sha256=sha256(raw).hexdigest())
    lifecycle = replace(case.metadata, subwork_id="entry.lifecycle", operation_id="exposed.selected-entry.lifecycle",
        configuration=case.selection.identity, roster_id="conditional.exposed.isolated",
        input_materialization_ids=tuple(sorted((*case.metadata.input_materialization_ids, manifest.materialization.materialization_id))),
        outputs=(NativeSubworkOutput("process.return", IsolatedNativeEntryReturn.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),
            NativeSubworkOutput("process.start", IsolatedNativeProcessStart.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")))
    progress.freeze_roster(NativeSubworkRoster(lifecycle.roster_id, case.parent, (lifecycle.identity,),
        parent_subwork=case.metadata.identity), parent_entry=metadata_entry, definitions=(lifecycle,))
    entry = progress.begin(lifecycle)
    return store, service, connection, progress, lifecycle, entry


def test_actual_selected_child_ready_and_proceed_share_pid_and_contact_precedes_entry(tmp_path):
    case = _selected_case(tmp_path)
    store, service, _, progress, lifecycle, entry = _begun_lifecycle(case)
    try:
        with (case.root / "entry.stdout").open("xb") as stdout, (case.root / "entry.stderr").open("xb") as stderr:
            returned = bridge.run_isolated_native_entry(case.selection, progress, lifecycle_entry=entry,
                start_output_id="process.start", return_output_id="process.return", environment=case.environment,
                cwd=case.root, stdout=stdout, stderr=stderr, prepared_contract=case.contract, entry_preflight="prepare")
        assert returned.returncode == 0 and returned.handshake_completed
        assert store.read_prepared_invocation(case.parent) == case.contract
        observed = store.inspect(lifecycle)
        assert observed.call_entry.invocation == case.contract.identity
        assert observed.call_return.return_code == 0
        marker = json.loads((case.root / "entry-marker.json").read_bytes())
        assert marker["prepared_pid"] == marker["entry_pid"] != os.getpid()
        assert marker["lifecycle_state"] == NativeSubworkState.UNKNOWN_COMPLETION.value
        start = next(row for row in store.inspect(lifecycle).outputs
            if row.logical.payload_schema == IsolatedNativeProcessStart.SCHEMA)
        raw = case.plane.root.resolve(start.materialization.relative_path, for_write=False).read_bytes()
        started = decode_canonical_bytes(raw, IsolatedNativeProcessStart, maximum_bytes=len(raw))
        assert started.child_pid == marker["entry_pid"] and started.parent_contact == case.parent
        assert store.inspect(lifecycle).state is NativeSubworkState.UNKNOWN_COMPLETION
        with pytest.raises(NativeSubworkReceiptPublicationPending, match="known native return"):
            store.recover(lifecycle)
    finally:
        service.close()
        store.parent_contacts.retire_live_creator(case.parent)
        case.close()


def test_actual_selected_child_refusal_preserves_begun_lifecycle_without_contact_or_witness(tmp_path):
    case = _selected_case(tmp_path)
    store, service, connection, progress, lifecycle, entry = _begun_lifecycle(case)
    before = tuple(connection.operations)
    try:
        with (case.root / "entry.stdout").open("xb") as stdout, (case.root / "entry.stderr").open("xb") as stderr:
            with pytest.raises(WorkerPreflightError) as refused:
                bridge.run_isolated_native_entry(case.selection, progress, lifecycle_entry=entry,
                    start_output_id="process.start", return_output_id="process.return", environment=case.environment,
                    cwd=case.root, stdout=stdout, stderr=stderr, prepared_contract=case.contract, entry_preflight="refuse")
        assert not refused.value.result.ready
        assert connection.operations[len(before):] == ["parent-contact"]
        assert store.inspect(lifecycle).state is NativeSubworkState.BEGUN
        assert store.inspect(lifecycle).outputs == ()
        assert not (case.root / "entry-marker.json").exists()
        assert not (case.root / "isolated-native-process-start.json").exists()
        assert not (case.root / "isolated-native-process-return.json").exists()
    finally:
        service.close()
        store.parent_contacts.retire_live_creator(case.parent)
        case.close()


class _BoundPointerRunner(ExposedReadRunner):
    def execute(self, context):
        if context.prepared_invocation is None:
            raise ValueError("exposed worker lacks its complete bound invocation")
        record = ExposedInput("exposed.config", context.prepared_invocation.identity.object_fingerprint)
        return RunnerResult((TaskOutputPayload("echo", record.canonical_bytes()),), (ReceiptCheck("bound-invocation", True, ()),))


def test_actual_worker_binds_original_complete_invocation_before_execute(tmp_path):
    plane, bundle, _, context, contract, _ = _case(tmp_path, actual=True)
    try:
        result = LocalProcessExecutor(scratch_root=plane.root).execute(_BoundPointerRunner(), context,
            timeout_seconds=None, prepared_contract=contract)
        raw = result.outputs[0].payload
        assert decode_canonical_bytes(raw, ExposedInput, maximum_bytes=len(raw)).value == contract.identity.object_fingerprint
        assert context.prepared_invocation is None
    finally:
        bundle.close()


@pytest.mark.parametrize("pointer", ("foreign", "untyped"))
def test_actual_worker_refuses_late_foreign_context_pointer_before_rebinding_or_output(tmp_path, pointer):
    plane, bundle, _, context, contract, parent = _case(tmp_path, actual=True)
    try:
        selected = replace(contract, invocation_id="foreign.invocation") if pointer == "foreign" else object()
        object.__setattr__(context, "prepared_invocation", selected)
        with pytest.raises(WorkerPreflightError) as refused:
            LocalProcessExecutor(scratch_root=plane.root).execute(_BoundPointerRunner(), context,
                timeout_seconds=None, prepared_contract=contract)
        assert not refused.value.result.ready
        assert "worker.invocation" in {row.operand_id for row in refused.value.result.mismatches}
        assert _store(plane, parent).parent_contacts.read(context.run_id, context.task_id) is None
    finally:
        bundle.close()
