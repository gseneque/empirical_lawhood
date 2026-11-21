# SPDX-License-Identifier: MPL-2.0
"""Prepare an explicit derivative from an authenticated retained version-1 run."""

import argparse
import json
from pathlib import Path


def main():
    from empirical_lawhood.api.mass_forecast_revision import create_inputs
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authoring-directory', type=Path, required=True)
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--operator-profile', type=Path, required=True)
    parser.add_argument('--source-operator-profile', type=Path)
    parser.add_argument('--output-directory', type=Path, required=True)
    print(json.dumps(create_inputs(**vars(parser.parse_args())), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
