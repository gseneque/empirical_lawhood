# SPDX-License-Identifier: MPL-2.0
"""Prepare or read a Gp construction with the selected application context."""

import argparse
import json
from pathlib import Path

from empirical_lawhood.api.domain_composition.rubisco_response.construction_operations import (
    FIELDS as FIELDS,
    run_construction_operation,
    validate_request as validate_request,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=tuple(FIELDS))
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--operator-profile", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    args = parser.parse_args()
    record = run_construction_operation(
        args.operation,
        context_path=args.context,
        operator_profile=args.operator_profile,
        request_path=args.request,
    )
    print(json.dumps(record, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
