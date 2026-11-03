# SPDX-License-Identifier: MPL-2.0
"""Current installed sampling delegates the original isolated runners and custody."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import subprocess

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import CHUNK_BYTES
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_runner import validate_current_source_descriptor
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.execution import WorkerInputKind
from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

from . import operation_bindings as ob


def load_inputs(context, manifest):
    ports = tuple(port for port in context.input_ports if port.payload_schema == ob.SamplingOperationConfig.SCHEMA)
    if len(ports) != 1:
        raise ValueError("sampling requires one complete immutable current configuration")
    config_port = ports[0]
    config = decode_canonical_bytes(config_port.read(), ob.SamplingOperationConfig, maximum_bytes=None)
    if (context.task_id != config.node_id or config_port.kind is not WorkerInputKind.EXTERNAL
            or config_port.artifact_id != context.config.artifact_id or config.config_id != context.config.config_id
            or config.fingerprint() != context.config.content_sha256 or context.permissions != manifest.permissions
            or context.resource_budget != ob.BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.dependency_receipts):
        raise ValueError("sampling changes its original config/task/access/resource/dependency contract")
    codecs = {(record.SCHEMA, record.VERSION): record for record in ob.INPUT_RECORD_TYPES}
    records = {}
    for identity in config.operands:
        matching = tuple(port for port in context.input_ports if port.artifact_id == identity.object_id)
        if len(matching) != 1:
            raise ValueError("sampling omits/substitutes an exact original scientific operand")
        port = matching[0]
        if (port.kind is not WorkerInputKind.EXTERNAL or port.payload_schema != identity.object_schema
                or port.media_type != ob.MEDIA or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
            raise ValueError("sampling substitutes its exact original input schema/access")
        raw = port.read()
        if len(raw) != port.size_bytes or sha256(raw).hexdigest() != identity.object_fingerprint:
            raise ValueError("sampling changes original full canonical materialized input bytes")
        record_type = codecs.get((identity.object_schema, identity.object_version))
        if record_type is None:
            raise ValueError("sampling lacks a declared exact original input schema/revision")
        records[identity] = decode_canonical_bytes(raw, record_type, maximum_bytes=None)
    if len(context.input_ports) != len(records) + 1 or records[config.plan.identity] != config.plan:
        raise ValueError("sampling receives undeclared inputs or replaces original complete plan bytes")
    return config, records


def _original_arguments(config, records):
    plan = config.plan
    if config.operation == "chemical-force":
        from .closed_raw_model_admission import ordinary_instance_records
        from .control_preparation_admission import validate_operands
        source, inputs = records[plan.source], records[plan.instance_inputs]
        assets = tuple(records[identity] for _, identity in plan.selected_assets)
        validate_operands(plan, source, inputs, None, None, assets, ())
        original = dict(ordinary_instance_records(inputs)) | {plan.identity: plan, plan.source: source,
            **{identity: asset for (_, identity), asset in zip(plan.selected_assets, assets, strict=True)}}
        if original != records or source != config.source:
            raise ValueError("sampling changes any original per-instance history/custody/assessment/source record")
        return plan, source, inputs, None, None, assets, ()
    from .nve_science import validate_operands
    plan.__post_init__()
    source = records[plan.chemical_controls.source]
    supplies = tuple(records[row[1]] for row in plan.admitted_parents)
    custody = tuple(records[supply.identity].original_custody for supply in plan.chemical_custody_supplies)
    if (source != config.source or records[plan.chemical_controls.identity] != plan.chemical_controls
            or any(records[supply.identity] != supply for supply in plan.chemical_custody_supplies)):
        raise ValueError("NVE changes its original selected chemical plan or exact named custody suppliers")
    validate_operands(plan, source, supplies, custody)
    return plan, source, supplies, custody


def _implementation(config, context, expected_parent):
    from empirical_lawhood.infrastructure.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
    if context.prepared_invocation is None:
        observed = capture_numerical_provenance(project_root=config.source_root)
        implementation = RecursiveImplementationBinding(observed.package_sources, observed.code_sources_sha256,
            observed.dependency_lock_sha256, observed.observed_git_head, observed.observed_checkout_clean)
    else:
        implementation = context.prepared_invocation.implementation
    if implementation.observed_git_head != expected_parent.implementation_commit:
        raise ValueError("sampling substitutes the exact actual anticipated implementation commit")
    validate_current_source_descriptor(config.plan, implementation, config.source_root)
    return implementation


def _inner_runner(config, definitions, manifest):
    if config.operation == "chemical-force":
        from .control_runner import ChemicalForceRunner
        runner_type = ChemicalForceRunner
        units = tuple(sorted("control.chemical-force." + name for name, _ in config.plan.selected_assets))
    else:
        from .nve_runner import NVEControlRunner
        from .nve_contracts import unit_id
        runner_type = NVEControlRunner
        units = tuple(sorted(unit_id(row) for row in config.plan.selected_cases))
    return runner_type(config.plan, config.invocation_path, definitions, config.environment,
        tuple((unit, "raw." + unit) for unit in units), config.node_id + ".census", manifest, config.node_id + ".units")


def _invocation(config, arguments, definitions, implementation):
    if config.operation == "chemical-force":
        from .control_invocation import build_invocation
        return build_invocation(*arguments, definitions, source_root=config.source_root, implementation=implementation)
    plan, source, supplies, custody = arguments
    return canonical_json_bytes({"plan": plan.canonical_bytes().decode(), "source": source.canonical_bytes().decode(),
        "supplies": tuple(row.canonical_bytes().decode() for row in supplies),
        "custody": tuple((name, definition.canonical_bytes().decode(), ci.canonical_bytes().decode(),
            completion.canonical_bytes().decode(), returned.canonical_bytes().decode(), assessment.canonical_bytes().decode())
            for name, definition, ci, completion, returned, assessment in custody),
        "definitions": tuple(row.canonical_bytes().decode() for row in definitions), "source_root": config.source_root})


def prepare_native_work(*, runner, context, expected_parent):
    """Exact original science projection, then explicit no-effect child preparation."""
    from empirical_lawhood.infrastructure.isolated_native_subwork import (
        materialize_isolated_invocation, prepare_isolated_native_work, selected_environment_sha256)
    from empirical_lawhood.infrastructure.numerical_provenance import numerical_observer_environment
    from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntrySelection
    from . import control_roster, nve_roster
    config, records = load_inputs(context, runner.manifest)
    if config.operation != runner.operation:
        raise ValueError("sampling config differs from its selected installed declaration")
    if Path(config.plan.workdir).exists():
        raise ValueError("sampling refuses existing uncertain work; use receipt-only recovery")
    arguments = _original_arguments(config, records)
    implementation = _implementation(config, context, expected_parent)
    roster = control_roster if config.operation == "chemical-force" else nve_roster
    selected = roster.definitions(config.plan, expected_parent, sources=tuple(row for row in config.operands if row != config.plan.identity),
        input_materialization_ids=context.input_materialization_ids, implementation=implementation, source_root=config.source_root)
    work = PreparedNativeWork(expected_parent, (ob.p.UNIT,), ob.native_effect_slot_ids(config), selected,
        (NativeSubworkRoster("selected.native-subwork", expected_parent, tuple(row.identity for row in selected)),))
    if context.prepared_invocation is None:
        return work
    previous = context.prepared_invocation.native_work
    if previous is not None and previous.isolated_selection is not None:
        work = replace(work, isolated_selection=previous.isolated_selection, isolated_environment=previous.isolated_environment,
            isolated_diagnostics=previous.isolated_diagnostics)
    payload = _invocation(config, arguments, selected, implementation)
    materialize_isolated_invocation(config.invocation_path,
        (payload[offset:offset + CHUNK_BYTES] for offset in range(0, len(payload), CHUNK_BYTES)),
        expected_size_bytes=len(payload), expected_sha256=sha256(payload).hexdigest())
    inner = _inner_runner(config, selected, runner.manifest)
    module, function, source, _ = inner._entry_target()
    controls = config.plan if config.operation == "chemical-force" else config.plan.chemical_controls
    environment = numerical_observer_environment(dict(config.environment))
    entry_id = "rubisco.chemical-force.entry" if config.operation == "chemical-force" else "rubisco.nve-control.entry"
    selection = IsolatedNativeEntrySelection(entry_id, controls.interpreter_path, controls.interpreter_sha256,
        module, function, str(source), sha256(source.read_bytes()).hexdigest(), config.invocation_path,
        sha256(payload).hexdigest(), selected_environment_sha256(environment))
    diagnostic_contract = replace(context.prepared_invocation, native_work=work, native_preparation_error=None)
    selected, _ = prepare_isolated_native_work(selection, prepared_contract=diagnostic_contract,
        entry_preflight="preflight_selected_child", environment=environment, cwd=str(Path(config.invocation_path).parent),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return selected


class SamplingOperationWorker:
    def __init__(self, operation, manifest=None):
        if manifest is None:
            manifest = next(row for row in ob.operation_manifests() if row.capability_key == ob.NAMESPACE + "." + operation)
        if operation not in ob.OPERATIONS or manifest.capability_key != ob.NAMESPACE + "." + operation:
            raise ValueError("sampling runner changes its installed declaration")
        self.operation, self.manifest = operation, manifest

    def execute(self, context):
        raise ValueError("sampling requires actual prepared native progress and original portable streaming")

    def preflight(self, context):
        contract = context.prepared_invocation
        if contract is None:
            raise ValueError("SOFTWARE: sampling needs its complete original prepared invocation")
        selected = prepare_native_work(runner=self, context=context, expected_parent=contract.expected_parent_contact)
        if selected != contract.native_work or selected.isolated_selection is None:
            raise ValueError("sampling substitutes its frozen complete actual specialist selection")

    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        contract = context.prepared_invocation
        if contract is None or contract.native_work is None or contract.native_work.isolated_selection is None:
            raise ValueError("SOFTWARE: sampling requires its actual prepared specialist before contact")
        contract.validate_context(context)
        config, records = load_inputs(context, self.manifest)
        if config.operation != self.operation:
            raise ValueError("sampling config differs from its exact installed operation")
        _original_arguments(config, records)
        inner = _inner_runner(config, contract.native_work.definitions, self.manifest)
        return inner.execute_streaming_with_native_subwork(context, native_subwork, emitter, progress)
