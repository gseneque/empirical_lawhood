# SPDX-License-Identifier: MPL-2.0
"""Independent exact material/source joins and complete historical target ledger."""

from decimal import localcontext
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry import (
    science as portfolio,
)
from empirical_lawhood.adapters.methods.rubisco_cycle_constraints import (
    assessment as cycle,
)
from empirical_lawhood.adapters.methods.rubisco_cycle_constraints.contracts import (
    identity as cycle_identity,
)
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from .contracts import (
    ALTERNATIVES,
    CANDIDATE_ID,
    NominationDossier,
    NominationTargetFinding,
    identity,
    scope,
)


def validate_inputs(preparation, macro, outcome):
    preparation.__post_init__()
    macro.__post_init__()
    outcome.__post_init__()
    cycle.validate_supplier(outcome.model)
    if outcome.disposition is not AssessmentDisposition.SATISFIED:
        raise ValueError(
            "nomination conditional model method failed its independent scientific assessment"
        )
    cycle.validate_instance(macro, outcome.instance)
    if (
        identity(macro) != preparation.macro_source
        or cycle_identity(outcome) != preparation.cycle_outcome
    ):
        raise ValueError(
            "nomination swaps exact original macro source or actual prior outcome"
        )
    if outcome.instance.candidate_ids != (
        "gp.wt",
        "wilson2017-row17",
    ) or outcome.instance.reference_ids != ("coupled", "radiometric"):
        raise ValueError(
            "nomination requires the exact actual Gp/Te conditional outcome, not a different prior query"
        )
    expected = cycle.assess_use(outcome.model, macro, outcome.instance)
    # Original supplier is a design operand, unlike later reuse of an instance.
    if expected != outcome:
        raise ValueError(
            "nomination prior outcome differs from independently rederived complete source-bound model assessment"
        )
    candidates = {r.candidate_id: r for r in portfolio.complete_candidate_roster(macro)}
    selected = candidates[CANDIDATE_ID]
    if (
        preparation.lsu_sequence != selected.lsu_sequence
        or (preparation.source_ssu_view, preparation.reported_ssu_sequence)
        not in selected.ssu_sequence_views
        or preparation.proposed_m1_ssu_sequence
        != "M" + preparation.reported_ssu_sequence[1:]
    ):
        raise ValueError(
            "nomination exact LSU/SSU material mismatches authentic proposed I95M source hypothesis"
        )
    if (
        selected.turnover_s_inv is not None
        or selected.specificity_dimensionless is not None
    ):
        raise ValueError(
            "nomination cannot reinterpret unmeasured I95M as measured biology"
        )
    return candidates


def prepare(preparation, macro, outcome):
    candidates = validate_inputs(preparation, macro, outcome)
    from .assessment import assess_rationale
    from .construction import assess_construction

    assess_construction(preparation, macro, candidates)
    rationale = assess_rationale(preparation, macro, candidates)
    findings = []
    with localcontext() as ctx:
        ctx.prec = 60
        for cid in sorted((CANDIDATE_ID, *ALTERNATIVES)):
            c = candidates[cid]
            for name, k, s in sorted(portfolio.REFERENCES):
                kr = None if c.turnover_s_inv is None else c.turnover_s_inv / k
                sr = (
                    None
                    if c.specificity_dimensionless is None
                    else c.specificity_dimensionless / s
                )
                findings.append(
                    NominationTargetFinding(
                        cid,
                        name,
                        c.turnover_s_inv,
                        c.specificity_dimensionless,
                        kr,
                        sr,
                        None if kr is None or sr is None else kr >= 1 and sr >= 1,
                        c.pairing_and_processing,
                    )
                )
    return NominationDossier(
        "product." + preparation.proposed_material_id,
        preparation,
        cycle_identity(outcome),
        tuple(findings),
        outcome.reason_codes,
        outcome.scope,
        rationale,
        sum(
            len(a.scenarios) * len(outcome.instance.release_multipliers)
            for a in outcome.anchors
        ),
        scope(preparation),
        AssessmentDisposition.SATISFIED,
    )


def validate_dossier(record, macro, outcome):
    if record != prepare(record.preparation, macro, outcome):
        raise ValueError(
            "nomination dossier drops adverse/unknown target findings or changes source/model constraints"
        )


def preparation_from_source(
    macro,
    outcome,
    *,
    proposed_material_id,
    source_ssu_view,
    source_members,
    assay,
    conditional_rationale,
    adverse_rationale,
    decision_provenance,
    input_id="input.rubisco-nomination.gp-i95m-proposed-m1",
):
    """Pure construction of the exact proposed M1 view from authenticated stock."""
    from .contracts import NominationPreparationSource

    candidate = next(
        r
        for r in portfolio.complete_candidate_roster(macro)
        if r.candidate_id == CANDIDATE_ID
    )
    selected = tuple(
        s for name, s in candidate.ssu_sequence_views if name == source_ssu_view
    )
    if len(selected) != 1:
        raise ValueError("nomination must select one exact reported SSU view")
    record = NominationPreparationSource(
        input_id,
        identity(macro),
        cycle_identity(outcome),
        proposed_material_id,
        CANDIDATE_ID,
        candidate.lsu_sequence,
        source_ssu_view,
        selected[0],
        "M" + selected[0][1:],
        tuple(sorted(source_members, key=lambda r: (r.role, r.filename))),
        assay,
        conditional_rationale,
        adverse_rationale,
        decision_provenance,
    )
    validate_inputs(record, macro, outcome)
    return record
