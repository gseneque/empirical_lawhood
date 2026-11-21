# SPDX-License-Identifier: MPL-2.0
"""Copy exposed starter evidence or prepare selected canonical experiment inputs."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    examples = commands.add_parser("examples")
    examples.add_argument("--output-directory", type=Path, required=True)
    inputs = commands.add_parser("inputs")
    inputs.add_argument("--evidence", type=Path, required=True)
    inputs.add_argument("--tolerance-kg", required=True)
    inputs.add_argument("--project-root", type=Path, required=True)
    inputs.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "examples":
        from empirical_lawhood.methods.mass_balance_starter.examples import example_evidence
        destination = args.output_directory.absolute()
        destination.mkdir(parents=True, exist_ok=False)
        result = {}
        for case in ("positive", "adverse", "unevaluable"):
            path = destination / (case + ".json")
            path.write_bytes(example_evidence(case).canonical_bytes())
            result[case] = str(path)
        incompatible = destination / "incompatible-units.json"
        original = example_evidence("positive").canonical_bytes()
        assert original.count(b'"units":"kg"') == 1
        incompatible.write_bytes(original.replace(b'"units":"kg"', b'"units":"g"'))
        result["incompatible_units"] = str(incompatible)
        result["evidence_scope"] = "EXPOSED_DEVELOPMENT"
    else:
        from empirical_lawhood.api.mass_balance_starter import create_inputs
        result = create_inputs(evidence_path=args.evidence, tolerance_kg=args.tolerance_kg,
                               project_root=args.project_root, output_directory=args.output_directory)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
