# SPDX-License-Identifier: MPL-2.0
"""Compose a retained mass investigation with an explicit representation derivative."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from empirical_lawhood.api.investigations import (
    create_investigation_service,
    create_local_workspace,
    experiment_preparation_report,
    prepare_investigation,
)
from empirical_lawhood.api.mass_balance_starter import create_inputs as prepare_mass_inputs
from empirical_lawhood.api.mass_forecast_revision import create_inputs as prepare_derivative_inputs
from empirical_lawhood.methods.mass_balance_starter import example_evidence


def write_report(path: Path, value) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def run_investigation(service, workspace, name: str, selected):
    preparation = prepare_investigation(
        service,
        specification_path=Path(selected["specification"]),
        source_selection_path=Path(selected["sources"]),
        environment_id="environment.mass-balance.base",
    )
    explain = experiment_preparation_report(preparation)
    write_report(workspace.scratch_root / f"{name}-preparation.json", explain)
    if not preparation.executable:
        raise ValueError(f"Resolve the prerequisites in {name}-preparation.json")
    directory = workspace.artifact_root / name
    write_report(workspace.scratch_root / f"{name}-authoring.json",
        service.author(preparation=preparation, output_dir=directory))
    write_report(workspace.scratch_root / f"{name}-run.json", service.run(directory=directory))
    result = service.read(directory=directory)
    write_report(workspace.scratch_root / f"{name}-result.json", result)
    write_report(workspace.scratch_root / f"{name}-recovery.json", service.recover(directory=directory))
    return directory, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--case", choices=("positive", "adverse", "unevaluable"), default="adverse")
    parser.add_argument("--tolerance-kg", default="0.01")
    args = parser.parse_args()
    project = args.project_root.absolute()
    workspace = create_local_workspace(args.workspace, project_root=project)
    evidence_path = workspace.scratch_root / "evidence.json"
    with evidence_path.open("xb") as stream:
        stream.write(example_evidence(args.case).canonical_bytes())
    service = create_investigation_service(project_root=project, operator_profile=workspace.profile_path)
    original_inputs = prepare_mass_inputs(evidence_path=evidence_path, tolerance_kg=args.tolerance_kg,
        project_root=project, output_directory=workspace.scratch_root / "original-inputs")
    original_directory, original = run_investigation(service, workspace, "original", original_inputs)
    # This public binder authenticates the retained forecast, assessment, complete
    # producing receipts and original implementation before declaring a new wave.
    derivative_inputs = prepare_derivative_inputs(authoring_directory=original_directory,
        project_root=project, operator_profile=workspace.profile_path,
        output_directory=workspace.artifact_root / "derivative-inputs")
    derivative_directory, derivative = run_investigation(service, workspace, "derivative", derivative_inputs)
    print(json.dumps({
        "workspace": str(args.workspace.absolute()),
        "operator_profile": str(workspace.profile_path),
        "original_directory": str(original_directory),
        "derivative_directory": str(derivative_directory),
        "original": original["scientific_result"],
        "derivative": derivative["scientific_result"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
