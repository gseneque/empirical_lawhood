# SPDX-License-Identifier: MPL-2.0
"""Run the authored classical matrix series through the public recursive lifecycle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

from empirical_lawhood.api.investigations import (
    create_local_workspace, create_investigation_service, prepare_investigation, experiment_preparation_report,
)
from empirical_lawhood.api.classical_matrix_series import create_inputs, create_reanalysis_inputs
from empirical_lawhood.storage.progress import OperationalProgressReporter


def write_report(path, value):
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=("prepare", "run", "reanalyse", "read", "recover", "execute"), default="run")
    parser.add_argument("--prepare-only", action="store_true", help="Prepare the complete run without executing native work.")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True,
        help="Explicit fresh root for prepare/run/reanalyse; original root for read/recover/execute.")
    parser.add_argument("--definition", type=Path,
        help="Editable scientific JSON; required for prepare/run/reanalyse.")
    parser.add_argument("--parent-workspace", type=Path, help="Original complete native run for retained reanalysis.")
    parser.add_argument("--maximum-parallel-tasks", type=int,
        help="Optional operational cap; otherwise use automatic usable host capacity.")
    parser.add_argument("--no-progress", action="store_true")
    parser.add_argument("--partial", action="store_true", help="Read available operational custody without a new scientific assessment.")
    args = parser.parse_args(argv)
    if args.prepare_only:
        if args.operation not in ("run", "prepare"):
            parser.error("--prepare-only is a new-study authoring selection")
        args.operation = "prepare"
    project, root = args.project_root.absolute(), args.workspace.absolute()
    new = args.operation in ("prepare", "run", "reanalyse")
    if new and args.definition is None:
        parser.error("select --definition for a new authored study")
    if (args.operation == "reanalyse") != (args.parent_workspace is not None):
        parser.error("--parent-workspace belongs to reanalyse and is required there")
    if args.partial and args.operation != "read":
        parser.error("--partial is an operational read selection only")
    if new:
        workspace = create_local_workspace(root, project_root=project,
            maximum_parallel_tasks=args.maximum_parallel_tasks)
        profile, artifact_root, scratch = workspace.profile_path, workspace.artifact_root, workspace.scratch_root
    else:
        profile, artifact_root, scratch = root / "operator-storage.json", root / "artifacts", root / "scratch"
    service = create_investigation_service(project_root=project, operator_profile=profile)
    directory = artifact_root / "classical-series"
    # Each invocation owns its progress file; later reads/recovery must not
    # overwrite a previous or still-running invocation's snapshot.
    progress_path = scratch / ("progress.json" if new else "progress." + args.operation + "." + uuid4().hex + ".json")
    with OperationalProgressReporter(progress_path, "classical matrix series",
            stream=None if args.no_progress else sys.stderr):
        if new:
            if args.operation == "reanalyse":
                parent = args.parent_workspace.absolute()
                parent_service = create_investigation_service(project_root=project, operator_profile=parent / "operator-storage.json")
                inputs = create_reanalysis_inputs(definition_path=args.definition, project_root=project,
                    output_directory=scratch / "inputs", parent_directory=parent / "artifacts" / "classical-series",
                    parent_service=parent_service)
            else:
                inputs = create_inputs(definition_path=args.definition, project_root=project, output_directory=scratch / "inputs")
            write_report(scratch / "inputs.json", inputs)
            prepared = prepare_investigation(service, specification_path=Path(inputs["specification"]),
                source_selection_path=Path(inputs["sources"]), environment_id="environment.matrix-classical-series.base")
            report = experiment_preparation_report(prepared)
            write_report(scratch / "preparation.json", report)
            if not prepared.executable:
                print(json.dumps({"status":"BLOCKED","preparation_report":str(scratch / "preparation.json"),
                    "dependencies":report.get("dependencies")}, indent=2))
                return 2
            authored = service.author(preparation=prepared, output_dir=directory)
            write_report(scratch / "authoring.json", authored)
            # Execution owns a fresh authenticated read of the authored inputs.
            # Retained reanalysis preparation can contain the full native roster.
            del prepared
        if args.operation in ("run", "reanalyse", "execute"):
            result = service.run(directory=directory, maximum_parallel_tasks=args.maximum_parallel_tasks)
            write_report(scratch / "execution.json", result)
        elif args.operation == "recover":
            result = service.recover(directory=directory, maximum_parallel_tasks=args.maximum_parallel_tasks)
            write_report(scratch / "recovery.json", result)
        elif args.operation == "read":
            result = service.read(directory=directory, allow_partial=args.partial)
        if args.operation != "prepare":
            # Run/recover already return the complete authenticated readout.
            # A separate cold read is an explicit --operation read invocation.
            write_report(scratch / "result.json", result)
            science = result.get("scientific_result") or {}
            print(json.dumps({"status":result.get("status"),"scientific_completion":science.get("scientific_completion"),
                "qualification":science.get("qualification"),"assigned_roots":science.get("assigned_roots"),
                "assigned_confirmation_roots":science.get("assigned_confirmation_roots"),
                "completed_operations":science.get("completed_operations"),"assigned_operations":science.get("assigned_operations"),
                "mode":science.get("mode"),"result_report":str(scratch / "result.json"),
                "operator_profile":str(profile),"authoring_directory":str(directory),
                "progress_report":str(progress_path)}, indent=2))
            return 0 if args.partial or science.get("scientific_completion") == "COMPLETED" else 3
        print(json.dumps({"status":"PREPARED_NOT_EXECUTED","operator_profile":str(profile),
            "authoring_directory":str(directory),"preparation_report":str(scratch / "preparation.json"),
            "progress_report":str(progress_path)}, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
