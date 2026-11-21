# SPDX-License-Identifier: MPL-2.0
"""Check or regenerate extension projections through their existing ordered owners."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

from empirical_lawhood.execution.local.bounded_process import BoundedProcessError, run_bounded_command
from empirical_lawhood.storage.source_origin import require_executing_target_source


ROOT = Path(__file__).resolve().parents[1]
STAGES = (
    "generate_extension_bundle_aggregate",
    "generate_executable_binding_aggregate",
    "generate_cli_reference",
    "generate_workflow_index",
    "generate_config_schemas",
    "generate_workflow_installations",
)


def run_projections(*, check: bool) -> dict:
    """Checks report every stage; mutations stop at a failed dependency."""
    if type(check) is not bool:
        raise TypeError("projection selection requires an explicit check mode")
    require_executing_target_source(ROOT)
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    rows = []
    failed = False
    for name in STAGES:
        command = (sys.executable, str(ROOT / "scripts" / (name + ".py")), *(('--check',) if check else ()))
        if failed and not check:
            rows.append({"stage": name, "status": "SKIPPED_DEPENDENCY", "returncode": None,
                         "elapsed_seconds": 0, "command": command})
            continue
        start = time.monotonic()
        try:
            result = run_bounded_command(command, cwd=ROOT, environment=environment,
                timeout_seconds=180, maximum_stdout_bytes=256 * 1024, maximum_stderr_bytes=64 * 1024)
            row = {"stage": name, "command": command, "returncode": result.returncode,
                   "status": ("CURRENT" if check else "REGENERATED") if result.returncode == 0 else "FAILED",
                   "stdout": result.stdout.decode("utf-8", errors="replace"),
                   "stderr": result.stderr.decode("utf-8", errors="replace")}
        except (BoundedProcessError, OSError, ValueError) as error:
            row = {"stage": name, "command": command, "returncode": None, "status": "FAILED",
                   "error_type": type(error).__name__, "error": str(error)[:4096]}
        row["elapsed_seconds"] = time.monotonic() - start
        rows.append(row)
        failed = failed or row["status"] == "FAILED"
    return {"schema": "empirical-lawhood/development/extension-projection-check", "version": "1.0.0",
            "mode": "CHECK" if check else "REGENERATE", "source_root": str(ROOT),
            "status": "FAILED" if failed else "PASS", "stages": rows,
            "scientific_authority": "NONE", "complete_test_suite": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Inspect every projection without changing source files.")
    parser.add_argument("--json", action="store_true", help="Return all stage diagnostics in one bounded JSON report.")
    args = parser.parse_args(argv)
    report = run_projections(check=args.check)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for row in report["stages"]:
            print(f"{row['stage']}: {row['status']}")
            if row["status"] == "FAILED":
                print(row.get("stdout", "") + row.get("stderr", "") + row.get("error", ""))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
