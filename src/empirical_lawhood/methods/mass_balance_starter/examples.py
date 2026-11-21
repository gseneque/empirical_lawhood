# SPDX-License-Identifier: MPL-2.0
"""Explicitly exposed arithmetic examples, never qualification evidence."""

from decimal import Decimal
from empirical_lawhood.methods.mass_balance_starter.records import NAMESPACE, MassEvidence, MassObservation, MassScope


def example_evidence(case):
    if case not in ("positive", "adverse", "unevaluable"):
        raise ValueError("select positive, adverse or unevaluable exposed example")
    outcomes = {"positive": "3.000000000000000000000000000001", "adverse": "3.2", "unevaluable": None}
    final = outcomes[case]
    scope = MassScope("population.exposed-mass-cases", "source.exposed-arithmetic-fixture",
                      "receiver.supplied-final-mass", "clock.after-addition")
    rows = (
        MassObservation("example.case.1", Decimal("1.000000000000000000000000000001"), Decimal("2"),
                        None if final is None else Decimal(final)),
        MassObservation("example.case.2", Decimal("2.5"), Decimal("0.5"), Decimal("3")),
        MassObservation("example.case.3", Decimal("0"), Decimal("0.01"), Decimal("0.01")),
    )
    return MassEvidence("example." + NAMESPACE + "." + case, scope, tuple(r.unit_id for r in rows), rows)
