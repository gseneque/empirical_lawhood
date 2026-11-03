# SPDX-License-Identifier: MPL-2.0
"""Ordinary source-authenticated composition of the isolated preparation child."""

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.execution import WorkerInputKind

from . import durable_operation_bindings as ob
from . import durable_roster as roster
from . import durable_stream as stream


def validate_current_source_descriptor(plan, implementation, source_root):
    """Prove one complete source representation for a new prepared attempt.

    Historical plan labels and hashes remain immutable. A legacy checkout
    prefix is accepted only as a full bijection to every current package file.
    """
    from empirical_lawhood.infrastructure.numerical_provenance import numerical_package_sources, selected_dependency_lock_sha256
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding

    if type(implementation) is not RecursiveImplementationBinding:
        raise ValueError("current preparation requires its exact selected implementation")
    implementation.__post_init__()
    plan.__post_init__()
    if not isinstance(source_root, (str, Path)):
        raise ValueError("current preparation requires its explicit selected source root")
    root = Path(source_root)
    if not root.is_absolute() or root.is_symlink() or root.resolve() != root:
        raise ValueError("current preparation changes its exact selected source root")
    prefix = "src/empirical_lawhood/"
    names = tuple(name for name, _ in plan.code_sources)
    if plan.code_sources == implementation.package_sources:
        normalized = plan.code_sources
    elif all(name.startswith(prefix) for name in names):
        normalized = tuple((name[len(prefix):], digest) for name, digest in plan.code_sources)
    else:
        raise ValueError("current preparation mixes or aliases scientific source labels")
    if (not normalized or len({name for name, _ in normalized}) != len(normalized)
            or normalized != implementation.package_sources):
        raise ValueError("current preparation lacks the exact full scientific-to-implementation source bijection")
    package = root / "src/empirical_lawhood"
    if package.is_symlink() or package.resolve() != package:
        raise ValueError("current preparation substitutes a package root or ancestor link")
    actual = numerical_package_sources(package)
    if actual != normalized:
        raise ValueError("current preparation source files differ from the complete selected inventory")
    if (plan.dependency_lock_sha256, selected_dependency_lock_sha256(root)) != (
            implementation.dependency_lock_sha256, implementation.dependency_lock_sha256):
        raise ValueError("current preparation substitutes its selected immutable dependency lock")
    return implementation.code_sources_sha256


def load_inputs(context, manifest):
    configs = tuple(port for port in context.input_ports if port.payload_schema == ob.DurablePreparationConfig.SCHEMA)
    if len(configs) != 1:
        raise ValueError("durable preparation requires one exact immutable configuration")
    config_port = configs[0]
    config = decode_canonical_bytes(config_port.read(), ob.DurablePreparationConfig, maximum_bytes=None)
    if (context.task_id != ob.NODE or config_port.kind is not WorkerInputKind.EXTERNAL
            or config_port.artifact_id != context.config.artifact_id
            or config.config_id != context.config.config_id or config.fingerprint() != context.config.content_sha256
            or context.permissions != manifest.permissions or context.resource_budget != ob.BUDGET
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.dependency_receipts):
        raise ValueError("durable preparation changes actual config/task/access/resources")
    from .durable_recursive_translation import input_identities
    identities = input_identities(config)
    records = {}
    for name, record_type in ob.INPUTS:
        identity = identities[name]
        matched = tuple(port for port in context.input_ports if port.artifact_id == identity.object_id)
        if len(matched) != 1:
            raise ValueError("durable preparation omits/substitutes exact original scientific input")
        port = matched[0]
        if (port.kind is not WorkerInputKind.EXTERNAL or port.payload_schema != record_type.SCHEMA
                or port.media_type != ob.MEDIA or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("durable preparation changes declared scientific input schema/access")
        raw = port.read()
        if len(raw) != port.size_bytes or sha256(raw).hexdigest() != identity.object_fingerprint:
            raise ValueError("durable preparation changes original full materialized input bytes")
        records[name] = decode_canonical_bytes(raw, record_type, maximum_bytes=None)
    if len(context.input_ports) != len(ob.INPUTS) + 1:
        raise ValueError("durable preparation receives undeclared input materializations")
    provenance = records["producing-provenance"]
    if (records["source"] != config.source or records["plan"] != config.plan
            or provenance.identity != config.producing_provenance
            or provenance.package_sources != config.plan.code_sources
            or provenance.dependency_lock_sha256 != config.plan.dependency_lock_sha256):
        raise ValueError("durable preparation changes exact source/plan/producing-byte binding")
    expected = tuple((ob.NODE + "." + name, record.SCHEMA,
        ArtifactProfile.JSONL_CHUNKS if name == "units" else ArtifactProfile.CANONICAL_JSON,
        ob.media_for(name)) for name, record in ob.OUTPUTS)
    if tuple((port.output_id, port.payload_schema, port.profile, port.media_type) for port in context.output_ports) != expected:
        raise ValueError("durable preparation changes its complete ordinary output contract")
    return config, records


def _current_projection(runner, context, expected_parent):
    from empirical_lawhood.infrastructure.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork
    from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster
    from .durable_recursive_translation import native_effect_slot_ids
    from . import contracts as historical

    config, records = load_inputs(context, runner.manifest)
    if Path(config.plan.workdir).exists():
        raise ValueError("durable preparation refuses existing uncertain work; use receipt-only recovery")
    if context.prepared_invocation is None:
        observed = capture_numerical_provenance(project_root=config.source_root)
        implementation = RecursiveImplementationBinding(observed.package_sources, observed.code_sources_sha256,
            observed.dependency_lock_sha256, observed.observed_git_head, observed.observed_checkout_clean)
    else:
        implementation = context.prepared_invocation.implementation
    if implementation.observed_git_head != expected_parent.implementation_commit:
        raise ValueError("durable preparation changes its actual anticipated implementation commit")
    selected = roster.definitions(config.plan, expected_parent, sources=config.operands,
        input_materialization_ids=context.input_materialization_ids,
        implementation=implementation, source_root=config.source_root)
    work = PreparedNativeWork(expected_parent, (historical.UNIT,), native_effect_slot_ids(config), selected,
        (NativeSubworkRoster("selected.native-subwork", expected_parent, tuple(row.identity for row in selected)),))
    return config, records, work


def _invocation_bytes(config, records, selected):
    return canonical_json_bytes({name: records[name].canonical_bytes().decode()
        for name in ("plan", "source", "nomination", "inventory", "coordinates")} | {
            "definitions": tuple(row.canonical_bytes().decode() for row in selected), "source_root": config.source_root})


def prepare_native_work(*, runner, context, expected_parent):
    """Read-only science projection, then explicit operational child preparation."""
    from dataclasses import replace
    import subprocess
    from empirical_lawhood.infrastructure.isolated_native_subwork import (
        materialize_isolated_invocation, prepare_isolated_native_work, selected_environment_sha256)
    from empirical_lawhood.infrastructure.numerical_provenance import numerical_observer_environment
    from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntrySelection
    from .durable_preparation import CHUNK_BYTES

    config, records, work = runner.project_native_scope(context, expected_parent)
    if context.prepared_invocation is None:
        return work
    previous = context.prepared_invocation.native_work
    if previous is not None and previous.isolated_selection is not None:
        work = replace(work, isolated_selection=previous.isolated_selection,
            isolated_environment=previous.isolated_environment, isolated_diagnostics=previous.isolated_diagnostics)
    payload = runner.invocation_bytes(config, records, work.definitions, context)
    materialize_isolated_invocation(config.invocation_path,
        (payload[offset:offset + CHUNK_BYTES] for offset in range(0, len(payload), CHUNK_BYTES)),
        expected_size_bytes=len(payload), expected_sha256=sha256(payload).hexdigest())
    target = runner.inner_runner(config, work.definitions, (), "preparation.census")
    module, function, source, _ = target._entry_target()
    environment = numerical_observer_environment(dict(config.environment))
    selection = IsolatedNativeEntrySelection("rubisco.durable-preparation.entry", config.plan.interpreter_path,
        config.plan.interpreter_sha256, module, function, str(source), sha256(source.read_bytes()).hexdigest(),
        config.invocation_path, sha256(payload).hexdigest(), selected_environment_sha256(environment))
    selected_contract = replace(context.prepared_invocation, native_work=work, native_preparation_error=None)
    selected, _ = prepare_isolated_native_work(selection, prepared_contract=selected_contract,
        entry_preflight="preflight_selected_child", environment=environment, cwd=str(Path(config.invocation_path).parent),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return selected


class _InnerOutputSink:
    """Inner raw replay is verified by primary custody; ordinary export follows.

The original inner runner also reads each completed raw archive. We retain
bounded buffers and account for that I/O in actual task cost; no partial raw
archive is treated as a completed portable product.
"""

    def __init__(self, allowed):
        self.allowed = frozenset(allowed)

    def write(self, output_id, raw):
        if output_id not in self.allowed or type(raw) is not bytes:
            raise ValueError("inner preparation changes exact declared virtual output")


class DurablePreparationWorker:
    def __init__(self, operation, manifest=None):
        if operation != "prepare":
            raise ValueError("unknown durable preparation operation")
        self.manifest = ob.operation_manifests()[0] if manifest is None else manifest

    def execute(self, context):
        raise ValueError("durable preparation requires actual ordinary streaming/native progress")

    def project_native_scope(self, context, expected_parent):
        return _current_projection(self, context, expected_parent)

    def invocation_bytes(self, config, records, definitions, context):
        return _invocation_bytes(config, records, definitions)

    def inner_runner(self, config, definitions, output_ids, census_output_id):
        from .durable_preparation import DurablePreparationRunner
        return DurablePreparationRunner(config.plan, config.invocation_path, definitions, config.environment,
            output_ids, census_output_id)

    def scientific_inputs(self, context):
        return load_inputs(context, self.manifest)

    @property
    def output_node(self):
        return ob.NODE

    def preflight(self, context):
        contract = context.prepared_invocation
        if contract is None:
            raise ValueError("SOFTWARE: durable preparation requires its complete original prepared invocation")
        selected = prepare_native_work(runner=self, context=context, expected_parent=contract.expected_parent_contact)
        if selected != contract.native_work or selected.isolated_selection is None:
            raise ValueError("durable preparation changes its frozen actual specialist selection")

    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        contract = context.prepared_invocation
        if contract is None or contract.native_work is None or contract.native_work.isolated_selection is None:
            raise ValueError("SOFTWARE: durable preparation requires its actual prepared specialist before contact")
        contract.validate_context(context)
        config, records = self.scientific_inputs(context)
        validate_current_source_descriptor(config.plan, contract.implementation, config.source_root)
        if Path(config.plan.workdir).exists():
            raise ValueError("durable preparation refuses existing uncertain working directory; use receipt-only recovery")
        selected = roster.definitions(config.plan, native_subwork.parent_contact, sources=config.operands,
            input_materialization_ids=context.input_materialization_ids,
            implementation=contract.implementation, source_root=config.source_root)
        if selected != contract.native_work.definitions or native_subwork.parent_contact != contract.expected_parent_contact:
            raise ValueError("durable preparation changes its complete prepared native parent/roster")
        path = Path(config.invocation_path)
        if sha256(path.read_bytes()).hexdigest() != contract.native_work.isolated_selection.invocation_sha256:
            raise ValueError("durable preparation changes its frozen complete invocation metadata")
        attempted = tuple(sorted((*config.plan.attempted_geometry_ids, *config.plan.attempted_model_ids)))
        virtual = tuple((unit, "raw." + unit) for unit in attempted)
        inner = self.inner_runner(config, selected, virtual, "virtual.census")
        sink = _InnerOutputSink(("virtual.census", *(name for _, name in virtual)))
        error = None
        try:
            inner.execute_streaming_with_native_subwork(context, native_subwork, sink, progress)
        except BaseException as caught:
            error = caught
        # Loss/adverse return remains primary. Export only original completed
        # products and the full UNKNOWN/unentered census; never restart a child.
        try:
            census = roster.census(native_subwork, config.plan, selected)
            emitter.write(self.output_node + ".census", census.canonical_bytes())
            stream.emit_units(emitter, self.output_node + ".units", native_subwork, census, selected)
        except Exception as export_error:
            if error is not None:
                raise RuntimeError("preparation adverse return retained; portable export also failed: " + str(export_error)) from error
            raise
        if error is not None:
            raise error
        return (ReceiptCheck("rubisco-durable-preparation-complete-original-custody", True, ()),)
