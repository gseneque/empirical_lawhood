# SPDX-License-Identifier: MPL-2.0
"""Five explicitly exposed software cases, with no original scientific population."""

from decimal import Decimal

from empirical_lawhood.science.identity.references import NamedDecimal
from empirical_lawhood.science.models.time import AvailabilitySpec, CausalPhase

from empirical_lawhood.methods.assigned_opportunity_assessment.records import ACCESS, OpportunityAuthorInput, OpportunityOutcome, OpportunityOutcomes, OpportunitySource


CASES = ("positive", "adverse", "insufficient", "interrupted", "unevaluable")


def example_inputs(case="positive", *, count=4):
    if case not in CASES or type(count) is not int or not 1 <= count <= 16:
        raise ValueError("select one disclosed case and one through sixteen assigned opportunities")
    source = OpportunitySource("source.assigned-opportunity.exposed", "unit.original-dependent-sequence",
        "clock.exposed-event-index", tuple("opportunity.%02d" % i for i in range(count)), ("view.a", "view.b"))
    actor = OpportunityAuthorInput("input.assigned-opportunity.actor", source, Decimal("0.5"),
        AvailabilitySpec(source.clock_id, CausalPhase.PRE_ACTION, ACCESS, Decimal(0)))
    rows = []
    for i, name in enumerate(source.opportunity_ids):
        status, values = "OBSERVED", (Decimal(1), Decimal(1))
        if case == "adverse":
            values = (Decimal(0), Decimal(0))
        elif case in ("insufficient", "interrupted") and i > 0:
            status, values = ("MISSING" if case == "insufficient" else "INTERRUPTED"), ()
        elif case == "unevaluable" and i == count - 1:
            values = (Decimal(0), Decimal(1))
        rows.append(OpportunityOutcome(name, source.identity, source.independent_unit_id,
            AvailabilitySpec(source.clock_id, CausalPhase.POST_OUTCOME, ACCESS, Decimal(i + 2)), status,
            tuple(NamedDecimal(view, value, "1") for view, value in zip(source.numerical_view_ids, values))))
    outcomes = OpportunityOutcomes("input.assigned-opportunity." + case, source, tuple(rows),
        AvailabilitySpec(source.clock_id, CausalPhase.POST_OUTCOME, ACCESS, Decimal(count + 1)))
    return actor, outcomes
