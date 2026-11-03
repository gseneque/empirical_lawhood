# SPDX-License-Identifier: MPL-2.0
"""Generate one disclosed conditional W1 example; acquire no scientific data."""

import argparse
from decimal import Decimal as D
from pathlib import Path

from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.disclosed_examples import DisclosedAssumption

from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.recursive_translation import kinetic_join_draft
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_supply import (
    ApparentKineticConstants, JointKineticSupply, KineticSupplyContext,
    KineticSupplyMember, KineticSupportInterval, KineticTargetComparison,
)
from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery
from empirical_lawhood.kernel.provenance import ObjectIdentity

ROOT = Path(__file__).resolve().parents[1]


def examples():
    assumed = DisclosedAssumption("example.rubisco.kinetic-assumptions.v1",
        "Invented material and matched 298.15 K apparent-rate assay. Supplied constants 6,75,1,3000; "
        "reference bounds 5.46 and 238 are displayed values only, not authenticated challenge controls. "
        "A partial family lacks oxygenation kinetics; a rejected member remains in the denominator.")
    parent = ObjectIdentity.from_record(assumed.assumption_id, assumed)
    context = KineticSupplyContext("example.rubisco.context.v1", parent, parent, D("298.15"))
    constants = ApparentKineticConstants(D("6"), D("75"), D("1"), D("3000"))
    unknown = KineticSupportInterval(None, None)
    members = (
        KineticSupplyMember("example.case.a-supplied", "AVAILABLE",
            KineticSupportInterval(D("6"), D("6")), KineticSupportInterval(D("240"), D("240")),
            constants, (), (parent,)),
        KineticSupplyMember("example.case.b-partial", "AVAILABLE", unknown, unknown, None,
            ("kcat_o", "ko"), (parent,)),
        KineticSupplyMember("example.case.c-rejected", "FALSIFIED", unknown, unknown, None,
            ("unsupported-member",), (parent,)),
    )
    supply = JointKineticSupply("example.rubisco.supply.v1", context,
        tuple(row.member_id for row in members), members, "DISCLOSED_SYNTHETIC", None,
        ("unknown-biological-calibration", "unknown-constant-covariance"),
        ("no-mutation-to-kinetics-model", "supplied-apparent-kinetics-only"), 0)
    query = AssayQuery(D("10"), D("250"), D("2.5"))
    comparison = KineticTargetComparison("example.rubisco.comparison.v1",
        ObjectIdentity.from_record(context.context_id, context),
        KineticSupportInterval(D("5.46"), D("5.46")), KineticSupportInterval(D("238"), D("238")),
        (parent,), "DECLARED_CONDITIONAL_MATCH", D("0"))
    draft = kinetic_join_draft(supply, query, comparison, relative_tolerance=D("1e-10"))
    return {name:record.canonical_bytes() for name, record in (
        ("assumptions.json", assumed), ("supply.json", supply), ("query.json", query),
        ("comparison.json", comparison), ("draft.json", draft))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = ROOT / "programmes/biology/photosynthesis/workflows/rubisco-kinetic-join"
    payloads = examples()
    for name, payload in payloads.items():
        path = root / name
        if args.check and (not path.is_file() or path.read_bytes() != payload):
            raise SystemExit("disclosed kinetic example drifted: " + name)
        if not args.check and path.exists() and path.read_bytes() != payload:
            raise SystemExit("preserve existing kinetic example; select a successor identity/path: " + name)
    if not args.check:
        root.mkdir(exist_ok=True)
        for name, payload in payloads.items():
            (root / name).write_bytes(payload)


if __name__ == "__main__":
    main()
