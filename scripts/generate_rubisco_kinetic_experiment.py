# SPDX-License-Identifier: MPL-2.0
"""Project a high-level W1 example from the unchanged disclosed source records."""

import argparse
from pathlib import Path

from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.disclosed_examples import DisclosedAssumption
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.experiment_specification import (
    PROTOCOL_ID, kinetic_experiment_specification,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_supply import JointKineticSupply, KineticTargetComparison
from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft


ROOT = Path(__file__).resolve().parents[1] / "programmes/biology/photosynthesis/workflows/rubisco-kinetic-join"


def projections():
    filenames = {"material": ("assumptions.json", DisclosedAssumption),
        "supply": ("supply.json", JointKineticSupply), "query": ("query.json", AssayQuery),
        "comparison": ("comparison.json", KineticTargetComparison)}
    records = {key: decode_canonical_bytes((ROOT / name).read_bytes(), kind, maximum_bytes=None)
        for key, (name, kind) in filenames.items()}
    records["campaign"] = decode_canonical_bytes((ROOT / "draft.json").read_bytes(),
        RecursiveStudyDraft, maximum_bytes=None).campaign
    specification = kinetic_experiment_specification(
        specification_id="specification.rubisco-kinetic-experiment.exposed",
        campaign=records["campaign"], material=records["material"], supply=records["supply"],
        source_query=records["query"], comparison=records["comparison"])
    filenames["campaign"] = ("campaign.json", type(records["campaign"]))
    selection = ExperimentInputSelection("selection.rubisco-kinetic-experiment.original-sources", PROTOCOL_ID,
        tuple(ExperimentInputBinding(key, specification.source_query if key == "query" else getattr(specification, key),
            filenames[key][0], len(record.canonical_bytes())) for key, record in sorted(records.items())))
    return {"campaign.json": records["campaign"].canonical_bytes(),
        "experiment.json": specification.canonical_bytes(), "experiment-sources.json": selection.canonical_bytes()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    payloads = projections()
    for name, payload in payloads.items():
        path = ROOT / name
        if arguments.check and (not path.is_file() or path.read_bytes() != payload):
            raise SystemExit("kinetic experiment projection drifted: " + name)
        if path.exists() and path.read_bytes() != payload:
            raise SystemExit("preserve existing experiment; select a successor identity/path: " + name)
    if not arguments.check:
        for name, payload in payloads.items():
            (ROOT / name).write_bytes(payload)


if __name__ == "__main__":
    main()
