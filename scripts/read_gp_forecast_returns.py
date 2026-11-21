# SPDX-License-Identifier: MPL-2.0
"""Independently join the four selected startup and geometry returns, including failed trials."""

import argparse
from pathlib import Path

from empirical_lawhood.api.domain_composition.rubisco_response.forecast_returns import (
    read_forecast_returns,
)
from empirical_lawhood.adapters.rubisco.rubisco_response.forecast_core import write_json


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    for flag in ("native-root", "evidence", "output"):
        cli.add_argument("--" + flag, required=True, type=Path)
    args = cli.parse_args()
    write_json(args.output, read_forecast_returns(args.native_root, args.evidence))


if __name__ == "__main__":
    main()
