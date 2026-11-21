# SPDX-License-Identifier: MPL-2.0
"""Original input, native definition and isolated selection joins."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.execution import WorkerInputKind
from empirical_lawhood.execution.isolated_native_subwork import IsolatedNativeEntryReturn, IsolatedNativeEntrySelection, IsolatedNativeProcessStart
from empirical_lawhood.execution.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster
from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork

from empirical_lawhood.adapters.isolated_native_starter import design
from empirical_lawhood.adapters.isolated_native_starter.records import MAX_CONTROL_BYTES, MAX_SOURCE_BYTES, NAMESPACE, UNIT, ProcessLog, SquareConfig, SquareInput, SquareNativeResult

CALCULATION = NAMESPACE + ".calculation"
METADATA = NAMESPACE + ".metadata"
LAUNCHER = NAMESPACE + ".process"
ENTRY_MODULE = "empirical_lawhood.adapters.isolated_native_starter.native_entry"


def guarded_scratch(worker):
    from empirical_lawhood.storage.artifacts import GuardedExternalRoot
    selected = GuardedExternalRoot(worker.scratch_contract)
    relative = Path(worker.scratch_directory).relative_to(worker.scratch_contract.canonical_path).as_posix()
    return selected.resolve(relative, for_write=True)


def output(name, kind):
    return NativeSubworkOutput(name, kind.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")


def effect_slots(config):
    return ("native." + config.node_id,)


def definitions_for(config, parent, *, materialization_ids, code_sha256, lock_sha256):
    sources = tuple(sorted((config.specification.operand, config.specification.provenance), key=lambda r: r.object_id))
    base = NativeSubworkDefinition(CALCULATION, NAMESPACE + ".sum-integer-squares", parent, config.identity,
        sources, code_sha256, lock_sha256, materialization_ids, (), (output("native.result", SquareNativeResult),))
    metadata = replace(base, subwork_id=METADATA, operation_id=NAMESPACE + ".select-process",
        outputs=(output("process.selection", IsolatedNativeEntrySelection),))
    return tuple(sorted((base, metadata), key=lambda r: r.subwork_id))


def launcher_definition(metadata, selection, manifest):
    if (manifest.logical.payload_schema != selection.SCHEMA
            or manifest.logical.content_sha256 != selection.fingerprint()):
        raise ValueError("isolated starter launcher changes its authenticated selection")
    logs = tuple(output(name, ProcessLog) for name in ("process.stderr", "process.stdout"))
    return replace(metadata, subwork_id=LAUNCHER, operation_id=NAMESPACE + ".launch",
        configuration=selection.identity, roster_id="conditional." + LAUNCHER,
        input_materialization_ids=tuple(sorted((*metadata.input_materialization_ids,
            manifest.materialization.materialization_id))),
        outputs=tuple(sorted((output("process.start", IsolatedNativeProcessStart),
            output("process.return", IsolatedNativeEntryReturn), *logs), key=lambda r: r.output_id)))


def load_inputs(context, manifest):
    kinds = {kind.SCHEMA: kind for kind in (SquareConfig, SquareInput, NumericalProducingProvenance)}
    received = {}
    for port in context.input_ports:
        kind = kinds.get(port.payload_schema)
        if (kind is None or kind in received or port.kind is not WorkerInputKind.EXTERNAL
                or port.media_type != "application/json" or port.visibility_ceiling is not design.VISIBILITY
                or port.outcome_access is not design.ACCESS):
            raise ValueError("isolated starter changes its exact input role or complete census")
        received[kind] = decode_canonical_bytes(port.read(), kind, maximum_bytes=MAX_SOURCE_BYTES)
    if set(received) != set(kinds.values()):
        raise ValueError("isolated starter omits a required original input")
    config, operand, provenance = (received[k] for k in (SquareConfig, SquareInput, NumericalProducingProvenance))
    if (operand.identity != config.specification.operand or provenance.identity != config.specification.provenance
            or (context.task_id, context.config.config_id, context.config.content_sha256)
                != (config.node_id, config.config_id, config.fingerprint())
            or context.resource_budget != design.BUDGET or context.permissions != manifest.permissions
            or context.outcome_access is not design.ACCESS or context.dependency_receipts
            or tuple(p.output_id for p in context.output_ports) != (config.node_id + ".product",)):
        raise ValueError("isolated starter substitutes its original inputs, task, resources or output")
    return config, operand, provenance


def invocation_bytes(config, operand, definitions):
    raw = canonical_json_bytes({"config": config.canonical_bytes().decode(), "operand": operand.canonical_bytes().decode(),
        "definitions": tuple(row.canonical_bytes().decode() for row in definitions)})
    if len(raw) > MAX_CONTROL_BYTES:
        raise ValueError("isolated starter control invocation exceeds its complete 64 KiB bound")
    return raw


def decode_invocation(invocation, expected_parent, contract):
    if invocation.size_bytes > MAX_CONTROL_BYTES:
        raise ValueError("isolated starter control invocation exceeds its complete 64 KiB bound")
    data = json.loads(invocation.read())
    if type(data) is not dict or set(data) != {"config", "operand", "definitions"}:
        raise ValueError("isolated starter invocation changes its complete field census")
    config = decode_canonical_bytes(data["config"].encode(), SquareConfig, maximum_bytes=MAX_CONTROL_BYTES)
    operand = decode_canonical_bytes(data["operand"].encode(), SquareInput, maximum_bytes=MAX_CONTROL_BYTES)
    definitions = tuple(decode_canonical_bytes(raw.encode(), NativeSubworkDefinition,
        maximum_bytes=MAX_CONTROL_BYTES) for raw in data["definitions"])
    work = contract.native_work
    expected = definitions_for(config, expected_parent, materialization_ids=expected_parent.input_materialization_ids,
        code_sha256=contract.implementation.code_sources_sha256, lock_sha256=contract.implementation.dependency_lock_sha256)
    if (work is None or expected_parent != contract.expected_parent_contact or definitions != expected
            or definitions != work.definitions or work.scientific_unit_ids != (UNIT,)
            or work.native_effect_slot_ids != effect_slots(config) or operand.identity != config.specification.operand):
        raise ValueError("isolated starter changes its original prepared parent or work census")
    for value in (config, operand):
        matches = tuple(row for row in contract.inputs if (row.logical.payload_schema, row.logical.content_sha256)
            == (value.SCHEMA, value.fingerprint()))
        if len(matches) != 1:
            raise ValueError("isolated starter embedded operand lacks its original authenticated input")
    return config, operand, definitions


def prepare_native_work(*, runner, context, expected_parent):
    from empirical_lawhood.execution.local.isolated_native_subwork import materialize_isolated_invocation, prepare_isolated_native_work, selected_environment_sha256
    config, operand, provenance = load_inputs(context, runner.manifest)
    selected = definitions_for(config, expected_parent, materialization_ids=context.input_materialization_ids,
        code_sha256=provenance.code_sources_sha256, lock_sha256=provenance.dependency_lock_sha256)
    if provenance.observed_git_head != expected_parent.implementation_commit:
        raise ValueError("isolated starter provenance changes its original implementation commit")
    work = PreparedNativeWork(expected_parent, (UNIT,), effect_slots(config), selected,
        (NativeSubworkRoster("selected.native-subwork", expected_parent, tuple(row.identity for row in selected)),))
    contract = context.prepared_invocation
    if contract is None:
        return work
    if (provenance.package_sources, provenance.code_sources_sha256, provenance.dependency_lock_sha256) != (
            contract.implementation.package_sources, contract.implementation.code_sources_sha256,
            contract.implementation.dependency_lock_sha256):
        raise ValueError("isolated starter changes the complete original source or lock")
    previous = contract.native_work
    if previous is not None and previous.isolated_selection is not None:
        work = replace(work, isolated_selection=previous.isolated_selection, isolated_environment=previous.isolated_environment,
            isolated_diagnostics=previous.isolated_diagnostics)
    worker = config.specification.worker
    path = guarded_scratch(worker) / "invocation.json"
    raw = invocation_bytes(config, operand, selected)
    materialize_isolated_invocation(str(path), (raw,), expected_size_bytes=len(raw), expected_sha256=sha256(raw).hexdigest())
    source = Path(worker.package_root) / "adapters/isolated_native_starter/native_entry.py"
    entry_sha256 = sha256(read_bounded_bytes(source, maximum_bytes=MAX_CONTROL_BYTES)).hexdigest()
    if dict(provenance.package_sources).get("adapters/isolated_native_starter/native_entry.py") != entry_sha256:
        raise ValueError("isolated starter selected entry differs from its original producing source")
    selection = IsolatedNativeEntrySelection(NAMESPACE + ".entry", worker.interpreter_path,
        worker.interpreter_sha256, ENTRY_MODULE, "selected_child", str(source),
        entry_sha256, str(path),
        sha256(raw).hexdigest(), selected_environment_sha256(dict(worker.environment)))
    diagnostic = replace(contract, native_work=work, native_preparation_error=None)
    observed, _ = prepare_isolated_native_work(selection, prepared_contract=diagnostic,
        entry_preflight="preflight_selected_child", environment=dict(worker.environment),
        cwd=path.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return observed
