# SPDX-License-Identifier: MPL-2.0
"""Export, locally validate and independently review matched relaxed Gp constructions."""

import argparse
import json
from pathlib import Path

from empirical_lawhood.api.domain_composition.rubisco_response.molprobity_validation import (
    MolProbitySelection,
    validate_structure,
    original_export as original_export,
    original_material_pins as original_material_pins,
    review_batch as review_batch,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("export", "export-parent", "run", "assess"):
        p = sub.add_parser(command)
        p.add_argument("--context", required=True, type=Path)
        p.add_argument("--operator-profile", required=True, type=Path)
        p.add_argument("--output-directory", required=True, type=Path)
        if command in ("export", "export-parent"):
            p.add_argument("--authoring-directory", required=True, type=Path)
            if command == "export":
                p.add_argument("--scaffold-directory", required=True, type=Path)
        else:
            p.add_argument("--export-directory", required=True, type=Path)
            p.add_argument("--export-sha256", required=True)
            p.add_argument("--runtime-receipt-sha256", required=True)
        if command == "run":
            p.add_argument("--runtime-prefix", required=True, type=Path)
            p.add_argument("--timeout-seconds", required=True, type=int)
            p.add_argument(
                "--restraint",
                action="append",
                nargs=2,
                default=[],
                metavar=("ABSOLUTE_CIF", "SHA256"),
            )
        if command == "assess":
            p.add_argument("--run-directory", required=True, type=Path)
            p.add_argument("--run-sha256", required=True)
    args = parser.parse_args()
    args.restraint = tuple(tuple(pair) for pair in getattr(args, "restraint", ()))
    result = validate_structure(MolProbitySelection(**vars(args)))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
