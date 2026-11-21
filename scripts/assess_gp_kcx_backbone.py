# SPDX-License-Identifier: MPL-2.0
"""Score the Gp 209–211 KCX neighbourhood against the original native observations."""

import argparse
import json
from pathlib import Path

from empirical_lawhood.api.domain_composition.rubisco_response.kcx_backbone_read import (
    BackboneSelection,
    assess_files,
    assess_supplement as assess_supplement,
    compare as compare,
    native_ramalyze as native_ramalyze,
)
from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_projection import (
    file_sha,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in (
        "export-directory",
        "component-directory",
        "runtime-prefix",
        "output-directory",
    ):
        parser.add_argument("--" + option, required=True, type=Path)
    for option in (
        "material",
        "export-sha256",
        "components-sha256",
        "runtime-receipt-sha256",
    ):
        parser.add_argument("--" + option, required=True)
    parser.add_argument("--timeout-seconds", type=int, required=True)
    args = parser.parse_args()
    try:
        selection = BackboneSelection(**vars(args))
    except ValueError as error:
        parser.error(str(error))
    path = assess_files(selection)
    print(json.dumps(dict(record=str(path), sha256=file_sha(path))))


if __name__ == "__main__":
    main()
