# SPDX-License-Identifier: MPL-2.0
"""Generate the exposed paired-response example through its scientific owners."""

import argparse
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_study
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_specification import PROTOCOL_ID, response_experiment_specification
from empirical_lawhood.design.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection

ROOT = Path(__file__).resolve().parents[1] / "programmes/biology/photosynthesis/workflows/rubisco-response"


def projections():
    study = disclosed_study()
    specification = response_experiment_specification(study)
    selection = ExperimentInputSelection("selection.rubisco-response.original-source", PROTOCOL_ID,
        (ExperimentInputBinding("study", study.identity, "study.json", len(study.canonical_bytes())),))
    return {"experiment.json": specification.canonical_bytes(), "experiment-sources.json": selection.canonical_bytes(),
            "study.json": study.canonical_bytes()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    payloads = projections()
    for name, raw in payloads.items():
        path = ROOT / name
        if arguments.check and (not path.is_file() or path.read_bytes() != raw):
            raise SystemExit("response experiment projection drifted: " + name)
        if path.exists() and path.read_bytes() != raw:
            raise SystemExit("preserve existing experiment; select a successor identity/path: " + name)
    if not arguments.check:
        for name, raw in payloads.items():
            (ROOT / name).write_bytes(raw)



if __name__ == "__main__":
    main()
