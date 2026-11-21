# SPDX-License-Identifier: MPL-2.0
"""Fixed selected-installation entry point; one finite invocation per process."""

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import sys

import empirical_lawhood
from empirical_lawhood.api.application_contracts import APPLICATION_VERSION, PROJECTION_VERSION, MAX_REQUEST_BYTES, ApplicationContext, ApplicationError, ApplicationRequest, application_result, error_result, exact_mapping, load_application_json, response_bytes
from empirical_lawhood.api.application_operations import application_operation, application_operations
from empirical_lawhood.api.results import ErrorCategory


ENGINE_SCHEMA = "empirical-lawhood/application/selected-engine"
ENGINE_VERSION = "1.0.0"


def describe_engine():
    from empirical_lawhood.api.generated_application_presentations import APPLICATION_PRESENTATION_MODULES
    package = Path(empirical_lawhood.__file__).parent
    # This observation identifies this entry point and its application contract.
    # Scientific producing-source identity remains with the original receipts.
    members = ("workbench/engine.py", "api/application.py", "api/application_contracts.py",
        "api/diagnostics.py", "api/retained_diagnostics.py", "api/investigation_trace.py",
        "api/results.py", "execution/resources/capacity.py",
        "api/application_context.py", "api/application_operations.py", "api/application_projections.py", "api/rc_workbench.py",
        "api/application_state.py", "api/application_collection.py", "api/application_neighbourhood.py", "storage/workbench_state.py",
        "api/application_exploration.py", "api/application_exploration_contracts.py",
        "api/application_companions.py", "api/domain_composition/rubisco_response/application_companions.py",
        "api/operational_observation.py", "api/observation_return.py", "execution/operational_observation.py",
        "storage/operational_observation.py", "storage/native_subwork.py",
        "api/domain_composition/rubisco_response/application_methods.py",
        "api/application_inquiry.py", "api/recursive_inquiry.py",
        "api/application_programme.py", "api/composite_experiment_programme.py", "api/experiment_programme.py",
        "api/application_knowledge.py", "api/knowledge_store.py", "api/knowledge_certificate_types.py",
        "api/application_continuing.py", "api/continuing_source.py",
        "api/sci02d_workbench.py", "api/application_presentations.py", "api/application_development.py",
        "api/generated_application_presentations.py",
        "api/application_invocation.py", "api/application_rc.py", "api/invocation_retention.py", "api/configuration.py",
        "storage/application_invocations.py", "execution/local/application_progress.py", "workbench/worker.py")
    members += tuple(module.removeprefix("empirical_lawhood.").replace(".", "/") + ".py"
        for module in APPLICATION_PRESENTATION_MODULES)
    description = {"schema": ENGINE_SCHEMA, "version": ENGINE_VERSION,
        "application_version": APPLICATION_VERSION, "projection_version": PROJECTION_VERSION,
        "package_version": empirical_lawhood.__version__, "python_executable": str(Path(sys.executable).absolute()),
        "environment_prefix": sys.prefix, "package_directory": str(package),
        "identity_scope": "ENTRY_POINT_AND_SELECTED_APPLICATION_CONTRACT",
        "entry_members": {name: sha256((package/name).read_bytes()).hexdigest() for name in members},
        "operations": [asdict(row) for row in application_operations()]}
    return description | {"identity_sha256": sha256(json.dumps(description, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def invoke(document):
    names = ("schema", "version", "context", "request", "expected_engine", "client")
    exact_mapping(document, names, required=names)
    if document["schema"] != ENGINE_SCHEMA or document["version"] != ENGINE_VERSION:
        raise ApplicationError("UNSUPPORTED_ENGINE_VERSION", "The selected engine transport is incompatible.")
    observed = describe_engine()
    if document["expected_engine"] != observed["identity_sha256"]:
        raise ApplicationError("ENGINE_CHANGED", "The selected engine changed. Negotiate a new application session.", category=ErrorCategory.IDENTITY)
    context = ApplicationContext.from_document(document["context"])
    request = ApplicationRequest.from_document(document["request"])
    if document["client"] not in ("browser", "cli"):
        raise ApplicationError("UNSUPPORTED_CLIENT", "Select a registered application client.")
    if context.python_executable.absolute() != Path(sys.executable).absolute():
        raise ApplicationError("INTERPRETER_MISMATCH", "This invocation did not enter the selected interpreter.", category=ErrorCategory.IDENTITY)
    descriptor = application_operation(request.operation)
    if descriptor.lifecycle in ("DURABLE_READ", "EFFECT"):
        raise ApplicationError("DURABLE_INVOCATION_REQUIRED", "Use the selected durable invocation entry for this operation.")
    if document["client"] == "browser" and not descriptor.browser_available:
        raise ApplicationError(descriptor.unavailable_reason or "UNAVAILABLE_BROWSER_OPERATION",
            "The selected engine does not expose this operation to the browser.", category=ErrorCategory.CAPABILITY)
    if context.project_root is not None:
        from empirical_lawhood.storage.source_origin import require_selected_implementation
        require_selected_implementation(context.project_root)
    from empirical_lawhood.api.application import execute_application
    return execute_application(context, request)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    operation = "application.engine"
    try:
        if args == ["--describe"]:
            result = application_result(operation, describe_engine())
        elif args == ["--invoke"]:
            raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
            result = invoke(load_application_json(raw))
        else:
            raise ApplicationError("INVALID_ENGINE_ARGUMENTS", "Select description or one typed invocation.")
        body = response_bytes(result)
    except Exception as error:
        body = response_bytes(error_result(operation, error))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
