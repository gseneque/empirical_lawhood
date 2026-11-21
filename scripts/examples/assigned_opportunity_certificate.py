# SPDX-License-Identifier: MPL-2.0
"""Produce or verify a portable certificate for an actual retained finite case."""

import argparse
import json
from pathlib import Path
import sys

from empirical_lawhood.methods.assigned_opportunity_assessment.portability import replay_specification
from empirical_lawhood.api.application_context import application_storage
from empirical_lawhood.api.application_contracts import ApplicationContext
from empirical_lawhood.api.knowledge_certificates import produce_assessment_certificate, verify_assessment_certificate
from empirical_lawhood.api.recursive_execution import read_recursive_wave


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("produce", "verify"))
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--operator-profile", type=Path, required=True)
    parser.add_argument("--authoring-directory", type=Path)
    parser.add_argument("--output-directory", type=Path)
    parser.add_argument("--certificate-directory", type=Path)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    _, _, plane = application_storage(ApplicationContext(context_id="assigned-opportunity.certificate",
        label="Original finite-assessment certificate", python_executable=Path(sys.executable),
        project_root=root, operator_profile=args.operator_profile), for_write=args.action == "produce")
    if args.action == "produce":
        if (args.authoring_directory is None or args.output_directory is None
                or args.certificate_directory is not None or args.allow_incomplete):
            parser.error("produce requires the original --authoring-directory and a new --output-directory")
        _, _, draft, _ = read_recursive_wave(directory=args.authoring_directory, artifact_writer=plane, include_products=True)
        report = produce_assessment_certificate(directory=args.authoring_directory,
            output_directory=args.output_directory, specification=replay_specification(draft),
            project_root=root, artifact_writer=plane)
    else:
        if args.certificate_directory is None or args.authoring_directory is not None or args.output_directory is not None:
            parser.error("verify requires only the selected --certificate-directory")
        report = verify_assessment_certificate(directory=args.certificate_directory,
            artifact_writer=plane, allow_incomplete=args.allow_incomplete)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
