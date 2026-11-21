# SPDX-License-Identifier: MPL-2.0
"""Freeze one source-specific inherited-coordinate candidate for independent evaluation."""

import argparse
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.gp_crystal_sites import (
    SELECTIONS,
    select_gp_crystal_sites,
)
from empirical_lawhood.storage.bounded_io import read_bounded_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deposition", required=True, type=Path)
    parser.add_argument("--refinement", required=True, type=Path)
    parser.add_argument("--selection", required=True, choices=SELECTIONS)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = select_gp_crystal_sites(
        read_bounded_bytes(args.deposition, maximum_bytes=8 * 2**20),
        read_bounded_bytes(args.refinement, maximum_bytes=8 * 2**20),
        args.selection,
    )
    with args.output.open("xb") as out:
        out.write(result)
    print(sha256(result).hexdigest(), args.output)


if __name__ == "__main__":
    main()
