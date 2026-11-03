# SPDX-License-Identifier: MPL-2.0
"""Run the supported portable suite once on an unchanged staged candidate."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

# These scripts are also importable by focused tests from the repository root.
if __package__:
    from .release_check import (portable_test_environment_policy, release_source_disclosure,
                               retained_test_options, seal_log_snapshot)
    from .release_portable_evidence import SCHEMA, candidate_inventory, inventory_digest, release_input_paths
else:
    from release_check import (portable_test_environment_policy, release_source_disclosure,
                               retained_test_options, seal_log_snapshot)
    from release_portable_evidence import SCHEMA, candidate_inventory, inventory_digest, release_input_paths

ROOT = Path(__file__).resolve().parents[1]
THREAD_ENVIRONMENT = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                      "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    packet = args.output_dir.absolute()
    if (".." in packet.parts or packet.exists() or packet.is_relative_to(ROOT)
            or any(part.is_symlink() for part in (packet, *packet.parents))):
        raise SystemExit("Select one new ordinary evidence directory outside the checkout")
    selected_paths = release_input_paths(ROOT)
    inventory = candidate_inventory(ROOT, selected_paths=selected_paths, verify_selected=True)
    disclosure = release_source_disclosure(ROOT, selected_paths)
    tree = subprocess.check_output(["git", "write-tree"], cwd=ROOT, text=True).strip()
    packet.mkdir(parents=True)
    (packet / "logs").mkdir()
    temporary_files = packet / "temporary-files"
    temporary_files.mkdir()
    inventory_path = packet / "candidate-inventory.json"
    inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n")
    record = {"schema": SCHEMA, "version": "1.0.0", "status": "RUNNING", "candidate_tree": tree,
              "attribution": "Precommit staged candidate; this is not a clean-commit test execution.",
              "parent_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "inventory_before_sha256": inventory_digest(inventory), "inventory_after_sha256": None,
              "selected_paths": list(selected_paths), "source_disclosure": disclosure,
              "final_source_disclosure": None,
              "uv_lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
              "full_suite_invocations": 0, "checks": [], "candidate_inventory": {
                  "path": inventory_path.name, "size_bytes": inventory_path.stat().st_size,
                  "sha256": hashlib.sha256(inventory_path.read_bytes()).hexdigest()},
              "coverage": None, "scientific_qualification": "NOT_PERFORMED",
              "test_environment_policy": portable_test_environment_policy(packet, ROOT)}
    environment = dict(os.environ, COVERAGE_FILE=str(packet / ".coverage"),
                       COVERAGE_RCFILE=str(ROOT / ".coveragerc"), PYTHONDONTWRITEBYTECODE="1",
                       TMPDIR=str(temporary_files), TMP=str(temporary_files), TEMP=str(temporary_files),
                       UV_CACHE_DIR=str(packet / "uv-cache"), XDG_CACHE_HOME=str(packet / "cache"),
                       RUFF_CACHE_DIR=str(packet / "ruff-cache"))
    environment.pop("PYTEST_ADDOPTS", None)
    # Plugins can import numerical libraries before pytest_sessionstart runs.
    # Set the supported profile before launching any selected interpreter.
    environment.update({name: "1" for name in THREAD_ENVIRONMENT})
    python = ["uv", "run", "--no-sync", "python"]

    def persist():
        temporary = packet / "precommit-portable-evidence.pending.json"
        with temporary.open("w") as stream:
            stream.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(packet / "precommit-portable-evidence.json")

    persist()

    def require_stability():
        if release_input_paths(ROOT) != selected_paths:
            raise RuntimeError("Selected release input census changed during its suite")
        after = inventory_digest(candidate_inventory(ROOT, selected_paths=selected_paths, verify_selected=True))
        record["final_source_disclosure"] = release_source_disclosure(ROOT, selected_paths)
        if after != record["inventory_before_sha256"] or subprocess.check_output(["git", "write-tree"], cwd=ROOT, text=True).strip() != tree:
            raise RuntimeError("Staged or loaded source changed during its suite")
        return after

    def run(name, command):
        print(f"candidate check: {name}", flush=True)
        began = time.monotonic()
        live = packet / "logs" / (name + ".live.log")
        sealed = packet / "logs" / (name + ".log")
        check = {"name": name, "command": command, "exit_code": None, "disposition": "RUNNING"}
        record["checks"].append(check)
        persist()
        try:
            with live.open("xb") as stream:
                result = subprocess.run(command, cwd=ROOT, env=environment, stdout=stream, stderr=subprocess.STDOUT)
            check.update(exit_code=result.returncode, disposition="PASSED" if result.returncode == 0 else "FAILED")
        except BaseException:
            check["disposition"] = "INTERRUPTED"
            raise
        finally:
            if live.is_file():
                size, checksum = seal_log_snapshot(live, sealed)
                check.update(log=sealed.relative_to(packet).as_posix(), size_bytes=size, sha256=checksum,
                             seconds=round(time.monotonic() - began, 3))
            persist()
        if check["exit_code"] != 0:
            raise RuntimeError(f"{name} failed; preserve this packet and use focused repair checks")

    try:
        run("environment", [*python, "-c", "import importlib.metadata as m,json,os,platform,sys; "
            "from pathlib import Path; import empirical_lawhood; "
            "from empirical_lawhood.infrastructure.source_origin import require_executing_target_source; "
            "require_executing_target_source(Path.cwd()); "
            "assert empirical_lawhood.__version__ == m.version('empirical-lawhood'); "
            "assert platform.python_version() == '3.11.14'; "
            "print(json.dumps({'python':platform.python_version(),'executable':sys.executable,"
            "'package_origin':empirical_lawhood.__file__,'thread_environment':{k:os.environ[k] for k in "
            f"{THREAD_ENVIRONMENT!r}"
            "},'packages':sorted((d.metadata['Name'],d.version) for d in m.distributions())},indent=2))"])
        # The precommit route needs the same inexpensive owner checks as the
        # artifact route before its once-only expensive portable invocation.
        # A passing test selection cannot excuse stale shipped examples.
        run("static-errors", ["uv", "run", "--no-sync", "ruff", "check", "src", "tests", "scripts"])
        for generator in ("extension_bundle_aggregate", "executable_binding_aggregate", "cli_reference",
                          "test_fixture", "operator_examples", "workflow_index", "config_schemas",
                          "integration_examples", "recursive_examples", "matrix_experiment_examples"):
            run(f"generated-{generator}", [*python, f"scripts/generate_{generator}.py", "--check"])
        run("documentation-links", [*python, "scripts/check_documentation.py"])
        run("frozen-rc-numerical-inputs", [*python, "scripts/check_frozen_rc_inputs.py"])
        run("coverage-configuration", [*python, "scripts/check_coverage_inventory.py", "--checkout", str(ROOT)])
        require_stability()
        record["full_suite_invocations"] = 1
        # Portable software controls can acquire disclosed native fixtures.
        # Keep successful bodies as well as failures for the exposure census.
        run("tests", [*python, "-m", "coverage", "run", "-m", "pytest", "-q", "-ra", "--fail-on-skip",
            *retained_test_options(packet), "tests", "-m", "not native and not held"])
        run("critical-coverage", [*python, "-m", "coverage", "report"])
        run("critical-coverage-json", [*python, "-m", "coverage", "json", "-o", str(packet / "coverage.json")])
        run("critical-coverage-inventory", [*python, "scripts/check_coverage_inventory.py", "--checkout", str(ROOT),
            "--coverage-json", str(packet / "coverage.json")])
        coverage = packet / "coverage.json"
        record["coverage"] = {"path": coverage.name, "size_bytes": coverage.stat().st_size,
                              "sha256": hashlib.sha256(coverage.read_bytes()).hexdigest()}
        after = require_stability()
        record["inventory_after_sha256"] = after
        record["status"] = "PASSED"
    except BaseException as error:
        record.update(status="INTERRUPTED" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "FAILED",
                      failure_type=type(error).__name__, failure=str(error))
        raise
    finally:
        record["finished_utc"] = datetime.now(timezone.utc).isoformat()
        persist()
    print(f"candidate suite passed; preserve exact tree before committing: {tree}", flush=True)


if __name__ == "__main__":
    main()
