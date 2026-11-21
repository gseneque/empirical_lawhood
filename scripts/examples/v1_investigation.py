# SPDX-License-Identifier: MPL-2.0
"""Prepare, author, run, inspect and recover one exposed recursive investigation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from empirical_lawhood.storage.progress import OperationalProgressReporter
from empirical_lawhood.execution.progress import progress_step, report_workflow_progress


def write_report(path: Path, value) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    evidence_selection = parser.add_mutually_exclusive_group()
    evidence_selection.add_argument("--case", choices=("positive", "adverse", "unevaluable"),
        help="Supplied exposed fixture; defaults to positive when --evidence is absent.")
    evidence_selection.add_argument("--evidence", type=Path,
        help="Original canonical MassEvidence file; exact bytes are copied by the public input owner.")
    parser.add_argument("--tolerance-kg", default="0.01")
    parser.add_argument("--no-progress", action="store_true", help="Suppress stderr progress; the selected workspace retains its operational snapshot.")
    args = parser.parse_args()
    project = args.project_root.absolute()
    with OperationalProgressReporter(None, "investigation startup", stream=None if args.no_progress else sys.stderr):
        with progress_step("investigation.initialize", total=1, unit="workspaces") as step:
            from empirical_lawhood.api.investigations import create_local_workspace
            workspace = create_local_workspace(args.workspace, project_root=project)
            step.advance()
    with OperationalProgressReporter(workspace.scratch_root / "progress.json", "investigation lifecycle",
            stream=None if args.no_progress else sys.stderr) as progress:
        result = run_investigation(args, workspace, project)
        if result:
            progress.finish("FAILED")
        return result


def run_investigation(args, workspace, project) -> int:
    from empirical_lawhood.api.investigations import (
        create_investigation_service, prepare_investigation,
        experiment_preparation_report,
    )
    from empirical_lawhood.api.mass_balance_starter import create_inputs
    from empirical_lawhood.methods.mass_balance_starter import example_evidence
    report_workflow_progress(done=0, total=5, unit="lifecycle-steps")
    case = args.case or "positive"
    if args.evidence is None:
        evidence_path = workspace.scratch_root / "evidence.json"
        with evidence_path.open("xb") as stream:
            stream.write(example_evidence(case).canonical_bytes())
    else:
        evidence_path = args.evidence.absolute()
        case = "supplied"
    with progress_step("investigation.inputs", total=1, unit="input-selections") as step:
        selected = create_inputs(evidence_path=evidence_path, tolerance_kg=args.tolerance_kg,
            project_root=project, output_directory=workspace.scratch_root / "inputs")
        step.advance()
    service = create_investigation_service(project_root=project, operator_profile=workspace.profile_path)
    preparation = prepare_investigation(service,
        specification_path=Path(selected["specification"]), source_selection_path=Path(selected["sources"]),
        environment_id="environment.mass-balance.base")
    report_workflow_progress(done=1, total=5, unit="lifecycle-steps")
    explain = experiment_preparation_report(preparation)
    write_report(workspace.scratch_root / "preparation.json", explain)
    if not preparation.executable:
        print(json.dumps(explain, indent=2))
        return 2
    directory = workspace.artifact_root / "investigation"
    authored = service.author(preparation=preparation, output_dir=directory)
    write_report(workspace.scratch_root / "authoring.json", authored)
    report_workflow_progress(done=2, total=5, unit="lifecycle-steps")
    run = service.run(directory=directory)
    write_report(workspace.scratch_root / "run.json", run)
    report_workflow_progress(done=3, total=5, unit="lifecycle-steps")
    retained = service.read(directory=directory)
    write_report(workspace.scratch_root / "result.json", retained)
    report_workflow_progress(done=4, total=5, unit="lifecycle-steps")
    recovered = service.recover(directory=directory)
    write_report(workspace.scratch_root / "recovery.json", recovered)
    report_workflow_progress(done=5, total=5, unit="lifecycle-steps")
    print(json.dumps({"progress_report": str(workspace.scratch_root / "progress.json"), "workspace": str(args.workspace.absolute()),
        "operator_profile": str(workspace.profile_path), "authoring_directory": str(directory),
        "preparation_report": str(workspace.scratch_root / "preparation.json"),
        "result_report": str(workspace.scratch_root / "result.json"),
        "recovery_report": str(workspace.scratch_root / "recovery.json"),
        "scientific_result": retained.get("scientific_result"),
        "case": case, "selected_workers": preparation.execution.workers}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
