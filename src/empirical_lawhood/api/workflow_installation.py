# SPDX-License-Identifier: MPL-2.0
"""Selected workflow software diagnosis, separate from source access and execution."""

from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
from importlib.resources import files
import json
from pathlib import Path
import sys

from empirical_lawhood.storage.bounded_io import bounded_file_sha256, read_bounded_bytes
from empirical_lawhood.execution.local.bounded_process import BoundedProcessError, run_bounded_command
from empirical_lawhood.execution.resources.environment_probe import inspect_interpreter_metadata
from empirical_lawhood.execution.discovery_descriptors import _source_path
from empirical_lawhood.api.results import ApiError, ApiResult, ErrorCategory, OperationStatus


_RESOURCE = "package_data/workflow_installations"


def _plain(value):
    return json.loads(json.dumps(value))


def _resource(name, *, maximum_bytes):
    _source_path(name)
    path = Path(str(files("empirical_lawhood").joinpath(_RESOURCE, name)))
    return read_bounded_bytes(path, maximum_bytes=maximum_bytes)


def workflow_installation(workflow_id: str, *, profile: str = "standard") -> dict:
    """Read one closed installed manifest, without checking any prerequisites."""
    from empirical_lawhood.adapters.composition.generated_public_facets import ENVIRONMENT_DECLARATIONS, WORKFLOW_INSTALLATIONS
    from empirical_lawhood.adapters.composition.generated_workflows import WORKFLOW_DECLARATIONS
    from empirical_lawhood.adapters.composition.generated_installation_manifest import MANIFEST_SHA256

    choices = [row for row in WORKFLOW_INSTALLATIONS if row.workflow_id == workflow_id and row.profile_id == profile]
    if len(choices) != 1:
        raise ValueError("unknown workflow installation profile; select its exact declared workflow and profile")
    declaration = choices[0]
    raw = _resource("manifest.json", maximum_bytes=16 * 1024**2)
    if sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("installed workflow manifest differs from its generated source binding")
    document = json.loads(raw)
    if (type(document) is not dict or document.get("schema") != "empirical-lawhood/software/workflow-installations"
            or document.get("version") != "1.0.0" or type(document.get("profiles")) is not list
            or type(document.get("environments")) is not dict):
        raise ValueError("installed workflow manifest has an unsupported contract")
    profiles = [row for row in document["profiles"] if row.get("declaration", {}).get("workflow_id") == workflow_id
                and row.get("declaration", {}).get("profile_id") == profile]
    if len(profiles) != 1 or profiles[0]["declaration"] != _plain(asdict(declaration)):
        raise ValueError("installed workflow manifest differs from its code-owned declaration")
    selected = profiles[0]
    workflow = next(row for row in WORKFLOW_DECLARATIONS if row.workflow.workflow_id == workflow_id)
    if (selected["guide"] != workflow.workflow.guide or selected["operations_available"] is not workflow.operations_available
            or selected["source_inputs"] != _plain([asdict(row) for row in workflow.workflow.inputs])
            or selected["scientific_ceiling"] != workflow.workflow.scientific_ceiling):
        raise ValueError("installed workflow manifest changes its original task or input boundary")
    required = {declaration.controller_environment, *(row.environment_id for row in declaration.workers)}
    environments = {}
    for identifier in sorted(required):
        expected = next(row for row in ENVIRONMENT_DECLARATIONS if row.route_id == identifier)
        environment = document["environments"].get(identifier)
        if not environment or environment["declaration"] != _plain(asdict(expected)):
            raise ValueError("installed workflow environment differs from its code-owned declaration")
        export = environment["requirements_export"]
        requirements = _resource(export["resource"], maximum_bytes=4 * 1024**2)
        if len(requirements) != export["size_bytes"] or sha256(requirements).hexdigest() != export["sha256"]:
            raise ValueError("installed workflow requirements export differs from its exact manifest")
        environments[identifier] = environment
    return {"schema": document["schema"], "version": document["version"],
            "manifest_sha256": sha256(raw).hexdigest(), "profile": selected, "environments": environments,
            "evidence_limit": document["evidence_limit"]}


def _source_binding(manifest, *, project_root):
    """Join ordinary installed build metadata or the actual executing checkout."""
    import empirical_lawhood
    from empirical_lawhood.storage.source_origin import observe_selected_implementation, require_executing_target_source
    from empirical_lawhood.storage.selected_candidate import installed_candidate

    package = Path(empirical_lawhood.__file__).resolve().parent
    inferred = package.parent.parent if package.parent.name == "src" else None
    candidate, root = None, None
    if project_root is not None:
        root = Path(project_root).resolve(strict=True)
        _, candidate = observe_selected_implementation(root)
    elif inferred is not None and (inferred / ".git").exists():
        root = inferred
        require_executing_target_source(root)
    else:
        candidate = installed_candidate()
    pins = [manifest["profile"]["owner"]]
    for environment in manifest["environments"].values():
        pins.extend((environment["project"], environment["lock"]))
    unique = {row["path"]: row for row in pins}
    for name in unique:
        _source_path(name)
    if candidate is not None:
        tracked = {row.relative_path: row for row in candidate.tracked_files}
        for name, pin in unique.items():
            row = tracked.get(name)
            if row is None or (row.size_bytes, row.sha256) != (pin["size_bytes"], pin["sha256"]):
                raise ValueError("workflow manifest differs from its installed build-source input: " + name)
        candidate.require_current()
        return {"kind": "INSTALLED_BUILD_SOURCE", "implementation_commit": candidate.implementation_commit,
                "implementation_sha256": candidate.implementation_sha256,
                "source_tree_sha256": candidate.source_tree_sha256, "worktree_matches_commit": None,
                "selected_source_distribution": None if root is None else str(root), "inputs": list(unique.values()),
                "status": "MATCHED"}
    for name, pin in unique.items():
        if bounded_file_sha256(root / name, maximum_bytes=pin["size_bytes"]) != (pin["size_bytes"], pin["sha256"]):
            raise ValueError("workflow manifest differs from its selected source input: " + name)
    commit = run_bounded_command(("git", "rev-parse", "HEAD"), cwd=root, timeout_seconds=5,
                                 maximum_stdout_bytes=128, maximum_stderr_bytes=4096)
    dirty = run_bounded_command(("git", "diff", "--quiet", "HEAD", "--", "src/empirical_lawhood", "pyproject.toml", "uv.lock"),
                                cwd=root, timeout_seconds=5, maximum_stdout_bytes=4096, maximum_stderr_bytes=4096)
    if commit.returncode or dirty.returncode not in (0, 1):
        raise ValueError("workflow installation cannot observe its executing source")
    return {"kind": "EXECUTING_CHECKOUT", "implementation_commit": commit.stdout.decode().strip(),
            "implementation_sha256": None, "source_tree_sha256": None, "worktree_matches_commit": dirty.returncode == 0,
            "selected_source_distribution": str(root), "inputs": list(unique.values()), "status": "MATCHED"}


def _selections(values, *, label):
    if type(values) is not tuple or len(values) > 32:
        raise ValueError(f"{label} requires a bounded tuple of ID=/absolute/path selections")
    result = {}
    for value in values:
        if type(value) is not str or len(value) > 8192 or any(ord(c) < 32 for c in value):
            raise ValueError(f"{label} requires ID=/absolute/path selections")
        key, separator, location = value.partition("=")
        path = Path(location)
        if not separator or not key or key in result or not path.is_absolute() or ".." in path.parts:
            raise ValueError(f"{label} requires unique IDs and absolute paths")
        result[key] = path
    return result


def _environment_report(environment, *, role, python, observations):
    base = {"role_id": role, "environment_id": environment["declaration"]["route_id"],
            "requirements_export": environment["requirements_export"], "required_interpreter": {
                "implementation": environment["declaration"]["python_implementation"],
                "version": environment["declaration"]["python_version"]}}
    if python is None:
        return {**base, "status": "SELECTION_REQUIRED", "reason_codes": ["WORKER_PYTHON_REQUIRED"],
                "observation": None, "dependencies": [], "software_prerequisites_satisfied": False}
    names = tuple(sorted({row["name"] for target in environment["targets"] for row in target["requirements"]}))
    key = (str(python), names)
    try:
        if key not in observations:
            observations[key] = inspect_interpreter_metadata(python, names)
        observed = observations[key]
    except (OSError, ValueError, BoundedProcessError) as error:
        return {**base, "status": "UNAVAILABLE", "reason_codes": ["INTERPRETER_METADATA_UNAVAILABLE"],
                "error": str(error)[:4096], "observation": None, "dependencies": [], "software_prerequisites_satisfied": False}
    targets = [row for row in environment["targets"]
               if row["system"] == observed["system"] and row["architecture"] == observed["architecture"]]
    reasons = []
    if len(targets) != 1:
        reasons.append("UNSUPPORTED_SOFTWARE_PLATFORM")
    if observed["python_implementation"] != base["required_interpreter"]["implementation"]:
        reasons.append("PYTHON_IMPLEMENTATION_MISMATCH")
    if observed["python_version"] != base["required_interpreter"]["version"]:
        reasons.append("PYTHON_VERSION_MISMATCH")
    dependencies = []
    for row in (() if not targets else targets[0]["requirements"]):
        versions = observed["distributions"][row["name"]]
        codes = ["DISTRIBUTION_ABSENT"] if not versions else ["AMBIGUOUS_DISTRIBUTION_METADATA"] if len(versions) != 1 else (
            ["DISTRIBUTION_VERSION_MISMATCH"] if versions[0] != row["version"] else [])
        dependencies.append({"distribution": row["name"], "required_version": row["version"],
            "observed_versions": versions, "reason_codes": codes, "version_matches": not codes})
        reasons.extend(codes)
    return {**base, "status": "SATISFIED" if not reasons else "UNSATISFIED", "reason_codes": sorted(set(reasons)),
            "observation": observed, "dependencies": dependencies, "software_prerequisites_satisfied": not reasons}


def inspect_workflow_environment(workflow_id, *, profile="standard", project_root=None,
                                 worker_pythons=(), external_software=()) -> dict:
    manifest = workflow_installation(workflow_id, profile=profile)
    declaration = manifest["profile"]["declaration"]
    workers = _selections(worker_pythons, label="worker interpreters")
    external = _selections(external_software, label="external software")
    if not workers.keys() <= {row["role_id"] for row in declaration["workers"]}:
        raise ValueError("worker selection names a role absent from the selected workflow profile")
    if not external.keys() <= {row["software_id"] for row in declaration["external_software"]}:
        raise ValueError("external software selection names an undeclared prerequisite")
    reasons, observations = [], {}
    try:
        source = _source_binding(manifest, project_root=project_root)
    except (OSError, PermissionError, ValueError, BoundedProcessError) as error:
        source = {"status": "UNAVAILABLE_OR_MISMATCHED", "error": str(error)[:4096]}
        reasons.append("INSTALLATION_SOURCE_BINDING_UNAVAILABLE")
    environments = [_environment_report(manifest["environments"][declaration["controller_environment"]],
        role="controller", python=Path(sys.executable), observations=observations)]
    for worker in declaration["workers"]:
        python = workers.get(worker["role_id"])
        if python is None and worker["selection"] == "controller":
            python = Path(sys.executable)
        environments.append(_environment_report(manifest["environments"][worker["environment_id"]],
            role=worker["role_id"], python=python, observations=observations))
    software = []
    for requirement in declaration["external_software"]:
        path = external.get(requirement["software_id"])
        observed, codes = None, []
        if path is None:
            codes.append("EXTERNAL_SOFTWARE_SELECTION_REQUIRED")
        else:
            try:
                size, checksum = bounded_file_sha256(path, maximum_bytes=requirement["maximum_bytes"])
                observed = {"path": str(path), "size_bytes": size, "sha256": checksum}
                if checksum != requirement["sha256"]:
                    codes.append("EXTERNAL_SOFTWARE_IDENTITY_MISMATCH")
                if requirement["kind"] == "executable" and not path.stat().st_mode & 0o111:
                    codes.append("EXTERNAL_SOFTWARE_NOT_EXECUTABLE")
            except (OSError, ValueError) as error:
                codes.append("EXTERNAL_SOFTWARE_UNAVAILABLE")
                observed = {"path": str(path), "error": str(error)[:4096]}
        software.append({"requirement": requirement, "observation": observed, "reason_codes": codes,
                         "software_prerequisites_satisfied": not codes})
        reasons.extend(codes)
    for row in environments:
        reasons.extend(row["reason_codes"])
    if not manifest["profile"]["operations_available"]:
        reasons.append("WORKFLOW_OPERATIONS_UNAVAILABLE")
    return {"schema": "empirical-lawhood/software/workflow-diagnosis", "version": "1.0.0",
        "workflow_id": workflow_id, "profile_id": profile, "manifest": manifest, "source_binding": source,
        "environments": environments, "external_software": software, "reason_codes": sorted(set(reasons)),
        "software_prerequisites_satisfied": not reasons, "source_inputs_state": "NOT_INSPECTED",
        "continuing_source_state": "NOT_CONNECTED", "resource_admission": "NOT_ASSESSED",
        "execution_authority": "NOT_ASSESSED", "reveal_authority": "NOT_ASSESSED",
        "scientific_qualification": "NOT_ESTABLISHED", "native_contacts": 0}


def workflow_environment_result(workflow_id, *, assert_prerequisites=False, operation="doctor.workflow", **selection):
    try:
        if type(assert_prerequisites) is not bool:
            raise TypeError("prerequisite assertion requires an explicit boolean")
        report = inspect_workflow_environment(workflow_id, **selection)
    except (TypeError, ValueError) as error:
        return ApiResult(operation, OperationStatus.INVALID, errors=(
            ApiError(ErrorCategory.VALIDATION, "INVALID_WORKFLOW_INSTALLATION", str(error)),),
            reason_codes=("INVALID_WORKFLOW_INSTALLATION",))
    report["assertion_requested"] = assert_prerequisites
    failed = assert_prerequisites and not report["software_prerequisites_satisfied"]
    from empirical_lawhood.api.application_contracts import application_result

    return replace(application_result(operation, report), status=OperationStatus.BLOCKED if failed else OperationStatus.SUCCEEDED,
        reason_codes=tuple(report["reason_codes"]) if failed else ())
