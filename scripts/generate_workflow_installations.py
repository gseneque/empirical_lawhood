# SPDX-License-Identifier: MPL-2.0
"""Project exact workflow software requirements from adapter facts and frozen locks."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import re
import tomllib

from empirical_lawhood.execution.local.bounded_process import run_bounded_command
from empirical_lawhood.storage.bounded_io import read_bounded_bytes

try:
    from ._descriptor_discovery import require_safe_path
except ImportError:
    from _descriptor_discovery import require_safe_path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src/empirical_lawhood/package_data/workflow_installations"
INDEX_OUTPUT = ROOT / "src/empirical_lawhood/adapters/composition/generated_installation_manifest.py"
MAX_EXPORT_BYTES = 4 * 1024**2


def _bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _input(path):
    require_safe_path(path, root=ROOT, description="installation source input")
    data = read_bounded_bytes(path, maximum_bytes=16 * 1024**2)
    if not data:
        raise ValueError("installation source input exceeds its bounded source contract")
    return {"path": path.relative_to(ROOT).as_posix(), "size_bytes": len(data), "sha256": sha256(data).hexdigest()}


def parse_requirements(raw, *, python_version, python_implementation, system, architecture):
    """Resolve exported PEP 508 conditions for one exact supported target only."""
    from packaging.requirements import Requirement

    if (system, architecture) != ("Linux", "x86_64"):
        raise ValueError("installation projection has no accepted marker target for this platform")
    environment = {"os_name": "posix", "sys_platform": "linux", "platform_machine": architecture,
        "platform_python_implementation": python_implementation, "platform_system": system,
        "python_version": ".".join(python_version.split(".")[:2]), "python_full_version": python_version,
        "implementation_name": python_implementation.lower(), "implementation_version": python_version,
        "extra": ""}
    requirements = {}
    text = raw.decode("utf-8").replace("\\\n", " ")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = re.split(r"\s+--hash=", line)
        declaration = Requirement(fields[0])
        if declaration.marker is not None:
            marker = str(declaration.marker)
            if "platform_release" in marker or "platform_version" in marker:
                raise ValueError("kernel-dependent installation markers need an explicit accepted target")
            if not declaration.marker.evaluate(environment):
                continue
        specifiers = tuple(declaration.specifier)
        if (declaration.url is not None or len(specifiers) != 1 or specifiers[0].operator != "=="
                or "*" in specifiers[0].version or len(fields) == 1
                or any(re.fullmatch(r"sha256:[0-9a-f]{64}", value.strip()) is None for value in fields[1:])):
            raise ValueError("selected workflow requirements must be exact versions with SHA-256 artifact hashes")
        name = re.sub(r"[-_.]+", "-", declaration.name).lower()
        version = specifiers[0].version
        hashes = sorted({value.strip().removeprefix("sha256:") for value in fields[1:]})
        previous = requirements.get(name)
        if previous is not None and previous["version"] != version:
            raise ValueError("selected workflow requirements contain incompatible versions")
        requirements[name] = {"name": name, "version": version,
                              "artifact_sha256": sorted(set(hashes + ([] if previous is None else previous["artifact_sha256"])))}
    if not requirements:
        raise ValueError("selected workflow export contains no hash-pinned requirements")
    return [requirements[name] for name in sorted(requirements)]


def generated_resources():
    from empirical_lawhood.adapters.composition.generated_public_facets import ENVIRONMENT_DECLARATIONS, PUBLIC_FACET_OWNERS, WORKFLOW_INSTALLATIONS
    from empirical_lawhood.adapters.composition.generated_workflows import WORKFLOW_DECLARATIONS

    workflows = {row.workflow.workflow_id: row for row in WORKFLOW_DECLARATIONS}
    owner_names = {(key[0], key[1]): owner for symbol, key, owner in PUBLIC_FACET_OWNERS
                   if symbol == "WORKFLOW_INSTALLATIONS"}
    environments, resources = {}, {}
    for declaration in ENVIRONMENT_DECLARATIONS:
        lock = ROOT / declaration.lock_path
        project = lock.with_name("pyproject.toml")
        project_pin, lock_pin = _input(project), _input(lock)
        project_data = tomllib.loads(read_bounded_bytes(project, maximum_bytes=project_pin["size_bytes"]).decode())
        if not set(declaration.dependency_groups) <= set(project_data.get("dependency-groups", {})):
            raise ValueError("installation environment selects a group absent from its owning project")
        command = ["uv", "export", "--project", str(project.parent), "--frozen", "--offline",
                   "--no-default-groups", "--no-emit-project", "--no-header", "--no-annotate",
                   "--no-python-downloads", "--python", declaration.python_version, "--format", "requirements.txt"]
        for group in declaration.dependency_groups:
            command.extend(("--group", group))
        result = run_bounded_command(command, cwd=ROOT, timeout_seconds=60,
                                     maximum_stdout_bytes=MAX_EXPORT_BYTES, maximum_stderr_bytes=64 * 1024)
        if result.returncode:
            raise ValueError(f"frozen installation export failed for {declaration.route_id}: " + result.stderr.decode(errors="replace"))
        filename = declaration.route_id + ".requirements.txt"
        resources[filename] = result.stdout
        targets = []
        for system, architecture in declaration.supported_platforms:
            rows = parse_requirements(result.stdout, python_version=declaration.python_version,
                python_implementation=declaration.python_implementation, system=system, architecture=architecture)
            selected = {row["name"]: row["version"] for row in rows}
            if any(selected.get(re.sub(r"[-_.]+", "-", name).lower()) != version
                   for name, version in declaration.distribution_versions):
                raise ValueError(f"frozen lock differs from the exact declared pins for {declaration.route_id}")
            targets.append({"system": system, "architecture": architecture, "requirements": rows})
        environments[declaration.route_id] = {
            "declaration": asdict(declaration), "project": project_pin, "lock": lock_pin,
            "project_name": project_data["project"]["name"], "project_version": project_data["project"]["version"],
            "requires_python": project_data["project"]["requires-python"],
            "requirements_export": {"resource": filename, "size_bytes": len(result.stdout), "sha256": sha256(result.stdout).hexdigest()},
            "targets": targets,
        }
    profiles = []
    for declaration in WORKFLOW_INSTALLATIONS:
        workflow = workflows[declaration.workflow_id]
        owner = ROOT / "src" / Path(*owner_names[(declaration.workflow_id, declaration.profile_id)].split(".")).with_suffix(".py")
        profiles.append({"declaration": asdict(declaration), "owner": _input(owner),
            "guide": workflow.workflow.guide, "operations_available": workflow.operations_available,
            "source_inputs": [asdict(row) for row in workflow.workflow.inputs],
            "scientific_ceiling": workflow.workflow.scientific_ceiling})
    resources["manifest.json"] = _bytes({"schema": "empirical-lawhood/software/workflow-installations",
        "version": "1.0.0", "environments": environments, "profiles": profiles,
        "evidence_limit": "Software requirements only. Input access, source/session connection, resource admission, execution and reveal remain separate."})
    return resources


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    from empirical_lawhood.storage.source_origin import require_executing_target_source
    require_executing_target_source(ROOT)
    resources = generated_resources()
    index = ('"""Generated by scripts/generate_workflow_installations.py; do not edit."""\n\n'
             'MANIFEST_SHA256 = ' + repr(sha256(resources["manifest.json"]).hexdigest()) + '\n').encode()
    actual = {path.name for path in OUTPUT.iterdir()} if OUTPUT.exists() else set()
    if OUTPUT.is_symlink() or any((OUTPUT / name).is_symlink() for name in actual):
        raise ValueError("installation projections refuse symbolic outputs")
    if actual - resources.keys():
        raise ValueError("installation projection inventory contains unexpected files: " + repr(sorted(actual - resources.keys())))
    stale = [name for name, raw in resources.items() if name not in actual or (OUTPUT / name).read_bytes() != raw]
    if INDEX_OUTPUT.is_symlink() or (INDEX_OUTPUT.exists() and not INDEX_OUTPUT.is_file()):
        raise ValueError("installation index refuses a symbolic or nonregular output")
    if not INDEX_OUTPUT.exists() or INDEX_OUTPUT.read_bytes() != index:
        stale.append(INDEX_OUTPUT.relative_to(ROOT).as_posix())
    if args.check and stale:
        raise SystemExit("workflow installation projections are missing or stale: " + ", ".join(stale))
    if not args.check:
        require_safe_path(OUTPUT.parent, root=ROOT / "src/empirical_lawhood", description="installation projection parent")
        OUTPUT.mkdir(parents=True, exist_ok=True)
        for name, raw in resources.items():
            (OUTPUT / name).write_bytes(raw)
        INDEX_OUTPUT.write_bytes(index)
    print(f"workflow installation projections: {len(resources) - 1} exact environment exports; manifest current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
