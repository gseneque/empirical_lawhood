# SPDX-License-Identifier: MPL-2.0
"""Measure transfer of paired Rubisco kinetics on whole held-out LSU backgrounds."""

import argparse
import json
from pathlib import Path
from time import monotonic, process_time


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("operation", choices=("geometry", "predict", "score", "recursive"))
    cli.add_argument("--evidence", required=True, type=Path)
    cli.add_argument("--archive", type=Path)
    cli.add_argument("--reference", type=Path)
    cli.add_argument("--project-root", type=Path)
    cli.add_argument("--workspace", type=Path)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    if args.operation in ("predict", "score") and args.archive is None:
        cli.error("predict and score require the native source --archive")
    if args.operation == "geometry" and args.reference is None:
        cli.error("geometry requires the dry structural --reference")
    start, cpu = monotonic(), process_time()
    if args.operation == "recursive" and (
        args.project_root is None or args.workspace is None
    ):
        cli.error("recursive requires --project-root and --workspace")
    from empirical_lawhood.api.domain_composition.rubisco_response.interface_forecast import (
        measure_interface_transfer,
    )

    value = measure_interface_transfer(
        args.operation,
        evidence=args.evidence,
        archive=args.archive,
        reference=args.reference,
        project_root=args.project_root,
        workspace=args.workspace,
    )
    value = {
        "result": value,
        "wall_s": monotonic() - start,
        "cpu_s": process_time() - cpu,
    }
    with args.output.open("x") as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")


if __name__ == "__main__":
    main()
