# SPDX-License-Identifier: MPL-2.0
"""Checkout entry point for the R23–R27 exposed scientific reproduction."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from empirical_lawhood.api.preparation_reuse_operands import (
    STUDIES,
    WORKFLOW,
    export_recursive_inputs,
    rebuild_released_archive,
)
from empirical_lawhood.api.preparation_reuse_reproduction import reproduce_preparation_reuse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", choices=(*STUDIES, "all"), default="all")
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument(
        "--operand-directory", type=Path, default=Path(__file__).resolve().parents[1] / WORKFLOW / "operands"
    )
    parser.add_argument(
        "--rebuild-archives",
        action="store_true",
        help="Repackage the disclosed source members using the release manifests.",
    )
    parser.add_argument(
        "--series-directory", type=Path, help="Source copy of the released R-series evidence."
    )
    parser.add_argument(
        "--tier2-directory", type=Path, help="Source copy of the original disclosed Tier 2 lineage."
    )
    parser.add_argument(
        "--export-recursive-inputs",
        action="store_true",
        help="Write the original R25 or R26 input selection for the supported recursive workflow.",
    )
    parser.add_argument(
        "--native-cohort",
        choices=("Q", "E", "calibration", "retained", "disjoint"),
        help="Reacquire a published R23 or R24 cohort from its frozen native inputs.",
    )
    parser.add_argument("--root-index", type=int, help="Select a single native root for a spot check.")
    parser.add_argument(
        "--from-seals",
        action="store_true",
        help="Recompute every R24 root from its original sealed control and reveal.",
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="Independent workers for native replication or the R24 sealed-control read."
    )
    args = parser.parse_args()
    if args.from_seals and (args.rebuild_archives or args.study not in ("r24", "all")):
        parser.error("--from-seals selects R24 or all studies")
    if args.native_cohort and (
        args.study not in ("r23", "r24")
        or args.from_seals
        or args.rebuild_archives
        or args.export_recursive_inputs
    ):
        parser.error("Select one R23 or R24 cohort for a native replication")
    if args.root_index is not None and not args.native_cohort:
        parser.error("--root-index selects a native spot check")
    if args.workers < 1 or (args.workers != 1 and not (args.from_seals or args.native_cohort)):
        parser.error("Select a positive worker count for sealed reconstruction or native replication")
    if args.export_recursive_inputs:
        if (
            args.study not in ("r25", "r26")
            or args.rebuild_archives
            or args.from_seals
            or args.series_directory
            or args.tier2_directory
        ):
            parser.error("Select just R25 or R26 to export its closed recursive inputs")
        export_recursive_inputs(
            directory=args.operand_directory, study=args.study, destination=args.output_directory
        )
        return
    args.output_directory.mkdir(parents=True, exist_ok=True)
    sources = {
        k: v for k, v in (("series", args.series_directory), ("tier2", args.tier2_directory)) if v is not None
    }
    for study in STUDIES if args.study == "all" else (args.study,):
        if args.rebuild_archives:
            needed = {"series", "tier2"} if study == "r27" else {"series"}
            if not needed <= sources.keys():
                parser.error("Select the source directories identified in the operand manifest")
            output = args.output_directory / f"{study}.zip"
            rebuild_released_archive(
                directory=args.operand_directory, study=study, sources=sources, destination=output
            )
        else:
            if sources:
                parser.error("Source directories are used with --rebuild-archives")
            if args.native_cohort:
                from empirical_lawhood.api.preparation_reuse_native import reproduce_native_roots

                report = reproduce_native_roots(
                    study=study,
                    cohort=args.native_cohort,
                    directory=args.operand_directory,
                    root_index=args.root_index,
                    workers=args.workers,
                )
                selection = "all" if args.root_index is None else f"r{args.root_index:03d}"
                output = args.output_directory / f"{study}-{args.native_cohort}-{selection}.json"
            else:
                report = reproduce_preparation_reuse(
                    study=study,
                    operand_directory=args.operand_directory,
                    from_seals=args.from_seals and study == "r24",
                    workers=args.workers,
                )
                output = args.output_directory / f"{study}.json"
            raw = (json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
            with TemporaryDirectory(dir=args.output_directory) as temporary:
                staged = Path(temporary) / "report"
                staged.write_bytes(raw)
                try:
                    output.hardlink_to(staged)
                except FileExistsError:
                    if output.read_bytes() != raw:
                        raise ValueError(f"Different result already exists at {output}") from None
        print(study.upper(), sha256(output.read_bytes()).hexdigest(), output, flush=True)


if __name__ == "__main__":
    main()
