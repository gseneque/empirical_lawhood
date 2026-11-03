# SPDX-License-Identifier: MPL-2.0
"""The original full-model method through the existing specialist lifecycle."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import subprocess

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntryReturn, IsolatedNativeProcessStart
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkRoster
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

from . import contracts as c
from .durable_contracts import DurableRawFileCensus
from .durable_preparation import CHUNK_BYTES
from .durable_roster import json_output, raw_output

LAUNCH = c.NAMESPACE + ".prepare.launch"


def source_root():
    return Path(__file__).resolve().parents[5]


def check_preparation_only_root(root):
    """Metadata presence establishes no completion or right to retry work."""
    root = Path(root)
    if root.is_symlink() or root.resolve() != root:
        raise ValueError("preparation changes its exact explicitly selected operational root")
    if root.exists():
        names = tuple(sorted(str(path.relative_to(root)) for path in root.rglob("*")))
        if (names != (".preparation", ".preparation/invocation.json")
                or any(path.is_symlink() for path in root.rglob("*"))
                or not (root / ".preparation/invocation.json").is_file()):
            raise ValueError("preparation refuses existing uncertain native work; use receipt-only recovery")


def launch_definition(config, parent, implementation):
    from .operation_bindings import operation_outputs
    outputs = (*tuple(json_output(name, record) for name, record in operation_outputs("prepare")),
        json_output("files.census", DurableRawFileCensus), raw_output("files.raw"),
        json_output("process.return", IsolatedNativeEntryReturn), json_output("process.start", IsolatedNativeProcessStart))
    return NativeSubworkDefinition(LAUNCH, LAUNCH, parent, ObjectIdentity.from_record(config.config_id, config),
        config.operands, implementation.code_sources_sha256, implementation.dependency_lock_sha256,
        parent.input_materialization_ids, (), tuple(sorted(outputs, key=lambda row: row.output_id)))


def invocation_bytes(config, values, definition):
    return canonical_json_bytes({"config": config.canonical_bytes().decode(),
        **{name: values[name].canonical_bytes().decode() for name in ("source", "nomination", "inventory", "coordinates")},
        "definition": definition.canonical_bytes().decode()})


def prepare_native_work(*, runner, context, expected_parent):
    from empirical_lawhood.infrastructure.numerical_provenance import capture_numerical_provenance, numerical_observer_environment
    from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
    from empirical_lawhood.infrastructure.isolated_native_subwork import (
        materialize_isolated_invocation, prepare_isolated_native_work, selected_environment_sha256)
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
    from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntrySelection
    from .operation_bindings import native_effect_slot_ids

    if runner.operation != "prepare":
        raise ValueError("original model method changes its registered native operation")
    config, values = runner.validated_inputs(context)
    check_preparation_only_root(config.source.native_workdir)
    if context.prepared_invocation is None:
        observed = capture_numerical_provenance(project_root=source_root())
        implementation = RecursiveImplementationBinding(observed.package_sources, observed.code_sources_sha256,
            observed.dependency_lock_sha256, observed.observed_git_head, observed.observed_checkout_clean)
    else:
        implementation = context.prepared_invocation.implementation
    if implementation.observed_git_head != expected_parent.implementation_commit:
        raise ValueError("original model preparation substitutes its actual implementation commit")
    definition = launch_definition(config, expected_parent, implementation)
    work = PreparedNativeWork(expected_parent, (c.UNIT,), native_effect_slot_ids(config), (definition,),
        (NativeSubworkRoster("selected.native-subwork", expected_parent, (definition.identity,)),))
    if context.prepared_invocation is None:
        return work
    previous = context.prepared_invocation.native_work
    if previous is not None and previous.isolated_selection is not None:
        work = replace(work, isolated_selection=previous.isolated_selection, isolated_environment=previous.isolated_environment,
            isolated_diagnostics=previous.isolated_diagnostics)
    payload = invocation_bytes(config, values, definition)
    root = Path(config.source.native_workdir)
    invocation = root / ".preparation/invocation.json"
    materialize_isolated_invocation(str(invocation),
        (payload[start:start + CHUNK_BYTES] for start in range(0, len(payload), CHUNK_BYTES)),
        expected_size_bytes=len(payload), expected_sha256=sha256(payload).hexdigest())
    interpreter = Path(c.ENGINE_ROOT) / ".venv/bin/python"
    try:
        _, interpreter_sha = bounded_file_sha256(interpreter.resolve(), maximum_bytes=None)
    except OSError as error:
        raise ValueError("ENVIRONMENT: original selected ENGINE_ROOT interpreter is unavailable") from error
    # These are the original explicitly selected parent environment bindings;
    # the scientific caller's existing child overrides remain exact.
    environment = dict(context.prepared_invocation.environment.selected_environment)
    environment.update(TMPDIR=str(root / "temporary"), TMP=str(root / "temporary"), TEMP=str(root / "temporary"),
        PYTHONPATH=str(source_root() / "src"), PYTHONDONTWRITEBYTECODE="1")
    environment.update({name: "1" for name in ("OPENMM_CPU_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS",
        "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")})
    environment = numerical_observer_environment(environment)
    module = "empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.ordinary_native_entry"
    entry = Path(__file__).with_name("ordinary_native_entry.py")
    selection = IsolatedNativeEntrySelection("rubisco.original-full-model-preparation.entry", str(interpreter), interpreter_sha,
        module, "selected_child", str(entry), sha256(entry.read_bytes()).hexdigest(), str(invocation),
        sha256(payload).hexdigest(), selected_environment_sha256(environment))
    diagnostic_contract = replace(context.prepared_invocation, native_work=work, native_preparation_error=None)
    selected, _ = prepare_isolated_native_work(selection, prepared_contract=diagnostic_contract,
        entry_preflight="preflight_selected_child", environment=environment, cwd=str(root),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return selected
