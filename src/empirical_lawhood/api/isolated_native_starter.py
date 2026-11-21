# SPDX-License-Identifier: MPL-2.0
"""Explicit starter inputs and original findings through ordinary custody."""

import json
import os
from pathlib import Path
import sys

from empirical_lawhood.adapters.isolated_native_starter import design, experiment
from empirical_lawhood.adapters.isolated_native_starter.records import MAX_CONTROL_BYTES, MAX_SOURCE_BYTES, NAMESPACE, PROTOCOL_ID, SquareInput, SquareResult, SquareSpecification, WorkerSelection
from empirical_lawhood.storage.bounded_io import bounded_file_sha256
from empirical_lawhood.execution.local.bounded_process import run_bounded_command
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.design.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection


def create_inputs(*, last_integer, worker_python, project_root, operator_profile, output_directory, scratch_directory, fault="none"):
    """Derive inputs, source and worker identities; no hand-authored native roster."""
    from empirical_lawhood.api.application_context import application_storage
    from empirical_lawhood.api.application_contracts import ApplicationContext
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.workflow_installation import inspect_workflow_environment
    from empirical_lawhood.storage.artifacts import GuardedExternalRoot
    from empirical_lawhood.execution.resources.environment_probe import inspect_interpreter_metadata
    from empirical_lawhood.storage.numerical_provenance import WORKER_ENVIRONMENT_DEFAULTS, capture_numerical_provenance, numerical_observer_environment
    from empirical_lawhood.execution.operator_profile import resolve_scientific_scratch_contract

    root = Path(project_root).resolve(strict=True)
    _, profile, plane = application_storage(ApplicationContext(
        context_id="isolated-native-starter.inputs", label="Isolated native starter inputs",
        python_executable=Path(sys.executable), project_root=root,
        operator_profile=Path(operator_profile)), for_write=True)
    destination, scratch = Path(output_directory), Path(scratch_directory)
    if not destination.is_absolute() or not scratch.is_absolute():
        raise ValueError("isolated starter requires new explicit absolute input and scratch destinations")
    destination = plane.root.resolve(destination.relative_to(plane.root.contract.canonical_path).as_posix(), for_write=True)
    guarded_scratch = GuardedExternalRoot(resolve_scientific_scratch_contract(profile, repo_root=root, home_root=Path.home()))
    scratch = guarded_scratch.resolve(scratch.relative_to(guarded_scratch.contract.canonical_path).as_posix(), for_write=True)
    if destination.exists() or scratch.exists():
        raise FileExistsError("isolated starter inputs require new input and scratch selections")
    selected_python = Path(worker_python).absolute()
    observed = inspect_interpreter_metadata(selected_python, ("numpy",))
    if ((observed["system"], observed["architecture"], observed["python_version"], observed["python_implementation"])
            != ("Linux", "x86_64", "3.11.14", "CPython") or len(observed["distributions"]["numpy"]) != 1):
        raise ValueError("isolated starter requires its selected CPython 3.11.14 Linux x86_64 worker")
    numpy_version = observed["distributions"]["numpy"][0]
    diagnosis = inspect_workflow_environment(NAMESPACE, project_root=root,
        profile="separate-numpy" if numpy_version == "2.3.5" else "standard",
        worker_pythons=("calculation=" + str(selected_python),))
    if not diagnosis["software_prerequisites_satisfied"]:
        raise ValueError("isolated starter software prerequisites are unsatisfied: " + ", ".join(diagnosis["reason_codes"]))
    # Resolve only the selected package's inert __init__. Scientific/native
    # preparation still occurs at the ordinary actual-worker preflight.
    package_probe = run_bounded_command((str(selected_python), "-I", "-B", "-c",
        "import empirical_lawhood, pathlib; print(pathlib.Path(empirical_lawhood.__file__).resolve().parent)"),
        timeout_seconds=30, maximum_stdout_bytes=4096, maximum_stderr_bytes=4096)
    if package_probe.returncode:
        raise ValueError("install the exact selected source or wheel in the worker before preparing starter inputs")
    package_root = Path(package_probe.stdout.decode().strip())
    if not package_root.is_absolute() or package_root.resolve(strict=True) != package_root:
        raise ValueError("isolated starter worker package locator is not its exact original directory")
    provenance = capture_numerical_provenance(project_root=root)
    relative_entry = "adapters/isolated_native_starter/native_entry.py"
    if bounded_file_sha256(package_root / relative_entry, maximum_bytes=MAX_CONTROL_BYTES)[1] != dict(provenance.package_sources)[relative_entry]:
        raise ValueError("isolated starter worker entry differs from the selected producing source")
    # The full worker environment is explicit and contains no copied secrets.
    # PATH supplies only the selected interpreter directory and system tools.
    environment = numerical_observer_environment({**WORKER_ENVIRONMENT_DEFAULTS,
        "PATH": str(selected_python.parent) + os.pathsep + os.defpath,
        "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(scratch)})
    worker = WorkerSelection(str(selected_python), observed["interpreter_file"]["sha256"],
        numpy_version, str(root), str(package_root), str(scratch), guarded_scratch.contract, tuple(sorted(environment.items())), fault)
    operand = SquareInput("operand." + NAMESPACE + ".n" + str(last_integer), last_integer)
    spec = SquareSpecification("specification." + NAMESPACE + "." + operand.fingerprint() + "." + worker.fingerprint(),
        operand.identity, provenance.identity, worker)
    experiment.bind_inputs(spec, {"operand": operand, "provenance": provenance})
    implementation = implementation_binding(root)
    if (implementation.package_sources, implementation.code_sources_sha256, implementation.dependency_lock_sha256,
            implementation.observed_git_head) != (provenance.package_sources, provenance.code_sources_sha256,
            provenance.dependency_lock_sha256, provenance.observed_git_head):
        raise ValueError("isolated starter source changed during input preparation")
    bindings = tuple(ExperimentInputBinding(name, value.identity, name + ".json", len(value.canonical_bytes()))
        for name, value in (("operand", operand), ("provenance", provenance)))
    selection = ExperimentInputSelection("inputs." + NAMESPACE + "." + spec.fingerprint(), PROTOCOL_ID, bindings)
    payloads = {"specification.json": spec.canonical_bytes(), "operand.json": operand.canonical_bytes(),
        "provenance.json": provenance.canonical_bytes(), "sources.json": selection.canonical_bytes(),
        "source-snapshot.json": implementation.canonical_bytes(),
        "installation-diagnosis.json": (json.dumps(diagnosis, indent=2, sort_keys=True) + "\n").encode(),
        "worker-observation.json": (json.dumps(observed, indent=2, sort_keys=True) + "\n").encode()}
    if any(len(raw) > MAX_SOURCE_BYTES for raw in payloads.values()):
        raise ValueError("isolated starter input exceeds its complete source bound")
    plane.root.verify(for_write=True)
    guarded_scratch.verify(for_write=True)
    destination.mkdir(parents=True, exist_ok=False)
    for name, raw in sorted(payloads.items()):
        with (destination / name).open("xb") as stream:
            stream.write(raw)
    return {"specification": str(destination / "specification.json"), "sources": str(destination / "sources.json"),
        "source_snapshot": str(destination / "source-snapshot.json"), "scratch_directory": str(scratch),
        "worker_numpy": worker.numpy_version, "fault": fault, "native_contact_count": 0,
        "qualification": "NOT_ESTABLISHED"}


def read_result(*, directory, artifact_writer, specification, instance, payloads, report, products, draft, plan, allow_partial=False):
    """Present the original authenticated comparison without NumPy or formula work."""
    if type(specification) is not SquareSpecification or instance.specification != specification.identity:
        raise PermissionError("isolated starter read substitutes its original specification")
    config = design.config_for(specification)
    base = {"namespace": NAMESPACE, "assigned_units": 1, "qualification": "NOT_ESTABLISHED",
        "evidence_scope": "EXPOSED_DEVELOPMENT", "native_acquisition_performed": False,
        "scientific_reconstruction_performed": False, "selected_fault": specification.worker.fault}
    if allow_partial or report.get("typed_product_validation") == "DEFERRED":
        return {**base, "scientific_completion": "DEFERRED"}
    if ({task.task_id for task in plan.tasks} != {config.node_id}
            or report.get("run_id") != plan.source_plan.object_id):
        raise PermissionError("isolated starter read changes its original complete task census")
    receipt = products["receipts"].get(config.node_id)
    if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED:
        return {**base, "scientific_completion": "INCOMPLETE"}
    value = products["records"].get(config.node_id, {}).get(config.node_id + ".product")
    if (type(value) is not SquareResult or value.config != config
            or (receipt.run_id, receipt.task_id) != (plan.source_plan.object_id, config.node_id)):
        raise PermissionError("isolated starter read substitutes its exact original result")
    value.__post_init__()
    return {**base, "scientific_completion": "COMPLETED", "claim_disposition": value.disposition,
        "last_integer": value.native.last_integer, "sum_of_squares": value.native.sum_of_squares,
        "independent_sum": value.independent_sum, "worker_numpy_version": value.native.numpy_version,
        "native_result": value.native.identity.to_document(), "result": value.identity.to_document(),
        "original_attempt_id": receipt.attempt_id}
