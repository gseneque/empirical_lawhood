# SPDX-License-Identifier: MPL-2.0
"""Prepare explicit copied inputs for the ordinary isolated starter lifecycle."""

import argparse
import json
from pathlib import Path


def main():
    from empirical_lawhood.adapters.isolated_native_starter.records import FAULTS
    from empirical_lawhood.api.isolated_native_starter import create_inputs

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--last-integer", type=int, default=64)
    parser.add_argument("--worker-python", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--operator-profile", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--scratch-directory", type=Path, required=True)
    parser.add_argument("--fault", choices=FAULTS, default="none")
    result = create_inputs(**vars(parser.parse_args()))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
