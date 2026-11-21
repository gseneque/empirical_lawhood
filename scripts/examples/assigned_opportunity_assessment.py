# SPDX-License-Identifier: MPL-2.0
"""Author or read a disclosed dependent-opportunity fixture through public owners."""

import argparse
import json
from pathlib import Path
import sys

from empirical_lawhood.methods.assigned_opportunity_assessment.examples import CASES, example_inputs
from empirical_lawhood.api.application_context import application_storage
from empirical_lawhood.api.application_contracts import ApplicationContext
from empirical_lawhood.api.assigned_opportunity_assessment import author_assigned_opportunity_wave, read_assigned_opportunity_result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("author", "read"))
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--operator-profile", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path)
    parser.add_argument("--authoring-directory", type=Path)
    parser.add_argument("--case", choices=CASES, default="positive")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    _, _, plane = application_storage(ApplicationContext(context_id="assigned-opportunity.example",
        label="Exposed dependent-opportunity fixture", python_executable=Path(sys.executable),
        project_root=root, operator_profile=args.operator_profile), for_write=args.action == "author")
    if args.action == "author":
        if args.output_directory is None or args.authoring_directory is not None or args.allow_partial:
            parser.error("author requires a new --output-directory without read selections")
        if not args.output_directory.is_absolute():
            parser.error("select an absolute output directory beneath the operator artifact root")
        relative = args.output_directory.relative_to(plane.root.contract.canonical_path).as_posix()
        output = plane.root.resolve(relative, for_write=True)
        if output.exists():
            raise FileExistsError("fixture authoring requires a new explicit destination")
        actor, outcomes = example_inputs(args.case)
        output.mkdir(parents=True)
        for name, record in (("actor.json", actor), ("outcomes.json", outcomes)):
            with (output / name).open("xb") as stream:
                stream.write(record.canonical_bytes())
        report = author_assigned_opportunity_wave(actor_path=output / "actor.json", outcomes_path=output / "outcomes.json",
            project_root=root, artifact_writer=plane, output_directory=output / "wave")
        result = {"case": args.case, "authoring_directory": str(output / "wave"), "authoring": report,
            "assigned_opportunities": len(outcomes.rows), "original_independent_roots": 1,
            "nested_views_per_opportunity": 2, "evidence_scope": outcomes.source.evidence_scope,
            "native_acquisition_performed": False, "qualification": "NOT_ESTABLISHED"}
    else:
        if args.authoring_directory is None or args.output_directory is not None:
            parser.error("read requires --authoring-directory without an output selection")
        result = read_assigned_opportunity_result(directory=args.authoring_directory, artifact_writer=plane,
                                                  allow_partial=args.allow_partial)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
