# SPDX-License-Identifier: MPL-2.0
"""Exact balances and source-conditional exclusions, never inferred microrates."""

from decimal import Decimal, localcontext
from fractions import Fraction as F
import json
import re
import xml.etree.ElementTree as ET

from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import (
    NominationDossier,
)
from empirical_lawhood.adapters.methods.rubisco_nomination_preparation import (
    assessment as prior_assessment,
)
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry import (
    science as portfolio,
)
from . import contracts as c
from .source_manifest import SOURCE_MANIFEST


# These are one declared algebraic normalization, not a physical fit or grid.
PREPARATION_NORMALIZATION = (F(2), F(1), F(3), F(1), F(4), F(2))


def solve(matrix):
    """Independent exact elimination with explicit singularity refusal."""
    rows = [list(map(F, row)) for row in matrix]
    n = len(rows)
    for column in range(n):
        pivot = next((row for row in range(column, n) if rows[row][column]), None)
        if pivot is None:
            raise ValueError("normalized reaction-state balance is singular")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        scale = rows[column][column]
        rows[column] = [value / scale for value in rows[column]]
        for row in range(n):
            if row != column:
                scale = rows[row][column]
                rows[row] = [
                    a - scale * b for a, b in zip(rows[row], rows[column], strict=True)
                ]
    return tuple(row[-1] for row in rows)


def stationary(edges, n):
    generator = [[F(0) for _ in range(n)] for _ in range(n)]
    for start, end, rate in edges:
        rate = F(rate)
        if rate < 0 or start == end:
            raise ValueError("elementary model edge is invalid")
        generator[end][start] += rate
        generator[start][start] -= rate
    rows = [row + [F(0)] for row in generator[:-1]] + [[F(1)] * n + [F(1)]]
    p = solve(rows)
    if (
        min(p) < 0
        or sum(p) != 1
        or any(sum(a * b for a, b in zip(row, p, strict=True)) for row in generator)
    ):
        raise ValueError(
            "reaction model violates exact normalized enzyme/state balance"
        )
    return p


def coarse_balance(carbon, oxygen=None, *, gas_c=F(1), gas_o=F(10)):
    """Three or five states; independent of the response formula being checked."""
    k, off, a, b, r = map(F, carbon)
    edges = [(0, 1, k * gas_c), (1, 0, off), (1, 2, a), (2, 1, b), (2, 0, r)]
    if oxygen is None:
        p = stationary(edges, 3)
        return r * p[2], F(0)
    ko, oo, ao, bo, ro = map(F, oxygen)
    edges.extend(((0, 3, ko * gas_o), (3, 0, oo), (3, 4, ao), (4, 3, bo), (4, 0, ro)))
    p = stationary(edges, 5)
    return r * p[2], ro * p[4]


def expanded_balance(
    carbon, oxygen, *, preparation=PREPARATION_NORMALIZATION, gas_c=F(1), gas_o=F(10)
):
    """Eight states: inactive, active, RuBP, enediolate, C/Pc, O/Po.

    Product release returns to active free enzyme, consuming the RuBP cycle.
    Shared activation/RuBP/enolization is explicit. All normalization rates are
    hypothetical; this theorem supplies no enzyme-specific binding/activation fit.
    """
    activation, deactivation, association_rubp, off_rubp, enol, deenol = preparation
    k, off, a, b, r = map(F, carbon)
    ko, oo, ao, bo, ro = map(F, oxygen)
    edges = [
        (0, 1, activation),
        (1, 0, deactivation),
        (1, 2, association_rubp),
        (2, 1, off_rubp),
        (2, 3, enol),
        (3, 2, deenol),
        (3, 4, k * gas_c),
        (4, 3, off),
        (4, 5, a),
        (5, 4, b),
        (5, 1, r),
        (3, 6, ko * gas_o),
        (6, 3, oo),
        (6, 7, ao),
        (7, 6, bo),
        (7, 1, ro),
    ]
    p = stationary(edges, 8)
    return r * p[5], ro * p[7]


def capture_probability(rates):
    """Exact first-passage product probability starting at gas-bound intermediate."""
    _, off, a, b, r = map(F, rates)
    bound, _ = solve(((off + a, -a, F(0)), (-b, b + r, r)))
    if bound != a * r / (off * (b + r) + a * r):
        raise ValueError("independent first-passage oracle disagrees")
    return bound


def response(v, uc, uo, lam):
    if not 0 <= uc < v or uo < 0 or lam < 1:
        raise ValueError("invalid declared coarse latent scenario")
    return lam * (1 + v) / (lam + v), ((1 + uc) * (lam + uo)) / ((lam + uc) * (1 + uo))


def rational(doc):
    if set(doc) != {"fraction", "decimal"}:
        raise ValueError(
            "rationale exact value changes its original fraction/decimal projection"
        )
    q = F(doc["fraction"])
    with localcontext() as ctx:
        ctx.prec = 60
        if abs(
            Decimal(q.numerator) / Decimal(q.denominator) - Decimal(doc["decimal"])
        ) > Decimal("1e-55"):
            raise ValueError("rationale fraction/decimal disagree")
    return q


def rationale(nomination):
    members = tuple(
        r
        for r in nomination.preparation.source_members
        if r.role == "RATIONALE" and r.filename == "exact-conditional-rationale.json"
    )
    if len(members) != 1:
        raise ValueError(
            "original nomination lacks its exact conditional rationale source"
        )
    return json.loads(members[0].raw_utf8)


def named_cases(nomination):
    doc = rationale(nomination)
    all_rows = (
        doc["donor_nominal_witness"],
        doc["gp_sufficient_unmeasured_witness"],
        *doc["adverse_witnesses"],
    )
    by_id = {row["case"]: row for row in all_rows}
    if len(by_id) != len(all_rows) or set(by_id) != set(c.CASE_IDS):
        raise ValueError(
            "original rationale prunes or substitutes favourable/adverse mathematical cases"
        )
    return tuple(by_id[key] for key in c.CASE_IDS)


def check_case(row, selection):
    latent = row["latent_assumptions"]
    v, uc, uo, lam = (rational(latent[key]) for key in ("vC", "uC", "uO", "lambda"))
    carbon, oxygen = (
        tuple(rational(value) for value in row["positive_micro_rate_witnesses"][key])
        for key in ("carbon", "oxygen")
    )
    if len(carbon) != 5 or len(oxygen) != 5 or min((*carbon, *oxygen)) <= 0:
        raise ValueError("rationale drops positive complete branch-rate witness")
    predicted_k, predicted_s = response(v, uc, uo, lam)
    if predicted_k != rational(row["turnover_multiplier"]) or predicted_s != rational(
        row["specificity_multiplier"]
    ):
        raise ValueError(
            "original rationale ratio projection differs from independently checked formulas"
        )
    expected_checks = iter(row["stationary_oracle_checks"])
    count = 0
    original_s = None
    for factor, state in ((F(1), "before"), (lam, "after")):
        cr, ox = (*carbon[:4], carbon[4] * factor), (*oxygen[:4], oxygen[4] * factor)
        for branch in (cr, ox):
            for gas in selection.gas_probes:
                actual = coarse_balance(branch, gas_c=gas.fraction)[0]
                expected = next(expected_checks)
                if (
                    expected["scope"] != "three-state-single-branch"
                    or expected["state"] != state
                    or gas.fraction != rational(expected["gas_uM"])
                    or actual != rational(expected["exact_flux"])
                ):
                    raise ValueError(
                        "rationale exact stationary three-state oracle differs"
                    )
                count += 1
        flux_c, flux_o = coarse_balance(cr, ox)
        actual_s = flux_c / flux_o * 10
        expected = next(expected_checks)
        if (
            expected["scope"] != "five-state-competing-gases"
            or expected["state"] != state
            or actual_s != rational(expected["exact_specificity"])
        ):
            raise ValueError("rationale exact competing-gas oracle differs")
        count += 1
        if original_s is None:
            original_s = actual_s
        elif actual_s / original_s != predicted_s:
            raise ValueError("competing-state specificity response differs")
    if next(expected_checks, None) is not None or count != 14:
        raise ValueError("original stationary check denominator differs")
    # A downstream irreversible processed state cannot return to the gas-bound
    # intermediate: this removes release sensitivity of substrate discrimination.
    irreversible = ((*carbon[:3], F(0), carbon[4]), (*oxygen[:3], F(0), oxygen[4]))
    invariant = []
    expanded = []
    for factor in (F(1), lam):
        cr, ox = (
            (*irreversible[0][:4], carbon[4] * factor),
            (*irreversible[1][:4], oxygen[4] * factor),
        )
        fc, fo = coarse_balance(cr, ox)
        invariant.append(fc / fo * 10)
        # Two exact normalization contexts establish shared pregas factors cancel
        # in specificity even when they constrain absolute turnover.
        for prep in (
            PREPARATION_NORMALIZATION,
            tuple(2 * q for q in PREPARATION_NORMALIZATION),
        ):
            ec, eo = expanded_balance(cr, ox, preparation=prep)
            expanded.append(ec / eo * 10)
    if (
        len(set(invariant)) != 1
        or len(set(expanded)) != 1
        or expanded[0] != invariant[0]
    ):
        raise ValueError(
            "independent irreversible/expanded state theorem was falsified"
        )
    k, off, a, b, release = carbon
    _, _, ao, bo, _ = oxygen
    # Nonzero minor proves rank2 of (kcat_C,S) for all positive branch rates:
    # d kcat_C/d a >0; dS/dkon_O=-S/kon_O !=0; dkcat_C/dkon_O=0.
    rank_minor = (
        release * (b + release) / (a + b + release) ** 2 * (-original_s / oxygen[0])
    )
    if rank_minor == 0:
        raise ValueError("endpoint structural-identifiability rank witness fails")
    capture = capture_probability(carbon)
    values = {
        "carbon_forward_capture_probability": capture,
        "carbon_formation_equilibrium_ratio": a / b,
        "oxygen_formation_equilibrium_ratio": ao / bo,
        "turnover_multiplier": predicted_k,
        "specificity_multiplier": predicted_s,
        "irreversible_specificity_multiplier": F(1),
        "endpoint_jacobian_rank_minor": rank_minor,
        "release_equilibrium_multiplier_if_reverse_binding_fixed": lam,
        "reverse_binding_multiplier_required_if_release_equilibrium_fixed": lam,
        "carbon_u_strict_ceiling_from_formation_equilibrium": v / (1 + a / b),
    }
    return c.CaseFinding(
        row["case"],
        tuple((name, c.Exact.of(value)) for name, value in sorted(values.items())),
        14,
        2,
        4,
        True,
        True,
        True,
        capture >= selection.primary_forward_partition.fraction,
        a / b > 1,
    )


def uncertainty(endpoint, before, after, before_se, after_se):
    def published_se(token, mean):
        match = re.fullmatch(
            r"([0-9]+(?:\.[0-9]+)?) ± ([0-9]+(?:\.[0-9]+)?)(?:\*{1,2})?", token
        )
        if match is None or F(match[1]) != F(mean):
            raise ValueError(
                "published native mean/SE token differs from source endpoint"
            )
        return F(match[2])

    mean0, mean1 = map(F, (before, after))
    se0, se1 = published_se(before_se, before), published_se(after_se, after)
    if min(mean0, mean1) <= 0 or min(se0, se1) < 0 or mean0 <= se0:
        raise ValueError("published mean/SE box cannot supply a positive finite ratio")
    z0, z1 = se0 / mean0, se1 / mean1
    return c.DonorUncertainty(
        endpoint,
        *(c.Exact.of(v) for v in (mean0, mean1, se0, se1, mean1 / mean0)),
        tuple(
            c.Exact.of(v)
            for v in ((mean1 - se1) / (mean0 + se0), (mean1 + se1) / (mean0 - se0))
        ),
        tuple(c.Exact.of(v) for v in ((z1 - z0) ** 2, (z1 + z0) ** 2)),
        before_se,
        after_se,
    )


def source_text(source, name):
    return next(row.raw_utf8 for row in source.primary_sources if row.filename == name)


def validate_inputs(source, macro, nomination):
    source.__post_init__()
    if (
        type(macro) is not portfolio.SourceAudit
        or type(nomination) is not NominationDossier
    ):
        raise ValueError(
            "mechanism requires typed original macro SOURCE and actual nomination OUTCOME"
        )
    macro.__post_init__()
    nomination.__post_init__()
    if (
        source.nomination != c.identity(nomination)
        or source.macro_source != c.identity(macro)
        or nomination.preparation.macro_source != c.identity(macro)
    ):
        raise ValueError(
            "mechanism substitutes authentic original nomination or macro source"
        )
    candidates = {r.candidate_id: r for r in portfolio.complete_candidate_roster(macro)}
    if (
        prior_assessment.assess_rationale(nomination.preparation, macro, candidates)
        != nomination.rationale_assessment
    ):
        raise ValueError("original nomination rationale reduction differs")
    # Primary research observed0.93..1 in three other activated-Mg enzymes,
    # not a measured Gp or mutant bound. Keep the commentary95:5 separate.
    abstract = ET.fromstring(
        source_text(source, "pierce1986-primary-core.xml")
    ).findtext(".//abstractText")
    if (
        not abstract
        or "0.93 to 1" not in abstract
        or "three different sources" not in abstract
        or "Mg2+" not in abstract
    ):
        raise ValueError(
            "primary intermediate-partition constraint was not authenticated"
        )
    if not re.search(
        r"95[^\n]{0,80}5", source_text(source, "tcherkez2018-commentary.html")
    ):
        raise ValueError("selected commentary partition summary missing")
    return candidates


def assess(source, macro, nomination):
    candidates = validate_inputs(source, macro, nomination)
    cases = tuple(check_case(row, source.selection) for row in named_cases(nomination))
    before, after = candidates["wilson2017-row12"], candidates["wilson2017-row17"]
    if before.lsu_sequence != after.lsu_sequence:
        raise ValueError("donor changes original LSU background")
    uncertainty_rows = tuple(
        uncertainty(
            endpoint,
            getattr(before, mean),
            getattr(after, mean),
            getattr(before, error),
            getattr(after, error),
        )
        for endpoint, mean, error in (
            ("specificity", "specificity_dimensionless", "specificity_error_token"),
            ("turnover", "turnover_s_inv", "turnover_error_token"),
        )
    )
    gp = candidates["gp.wt"]
    if "±" in gp.turnover_error_token or "±" in gp.specificity_error_token:
        raise ValueError("historical Gp anchor uncertainty contract differs")
    required_s = F(238) / F(gp.specificity_dimensionless)
    v = rational(
        rationale(nomination)["gp_sufficient_unmeasured_witness"]["latent_assumptions"][
            "vC"
        ]
    )
    targets = []
    for view, target in (("coupled", F("3.70")), ("radiometric", F("5.46"))):
        gain = target / F(gp.turnover_s_inv)
        if gain >= 1 + v:
            raise ValueError("prior claimed finite release target is unreachable")
        targets.append(
            c.TargetCondition(
                view,
                c.Exact.of(gain),
                c.Exact.of(1 - 1 / gain),
                c.Exact.of(gain * v / (1 + v - gain)),
                c.Exact.of(required_s),
            )
        )
    donor_gain = F(after.turnover_s_inv) / F(before.turnover_s_inv)
    return c.MechanismAssessment(
        "product." + c.NAMESPACE + ".challenge",
        source,
        nomination.scope,
        cases,
        tuple(targets),
        uncertainty_rows,
        c.Exact.of(1 / source.selection.primary_forward_partition.fraction),
        c.Exact.of(1 / source.selection.commentary_forward_partition.fraction),
        c.Exact.of(1 - 1 / donor_gain),
    )


def validate_assessment(record, macro, nomination):
    if record != assess(record.source, macro, nomination):
        raise ValueError(
            "mechanism assessment differs from complete independent source/balance reduction"
        )


def source_from_bytes(
    raw_sources,
    *,
    macro,
    nomination,
    input_id="input.rubisco-insilico-mechanism",
    selection=None,
):
    if set(raw_sources) != {row[0] for row in SOURCE_MANIFEST}:
        raise ValueError("mechanism original primary-source byte census differs")
    selection = selection or c.MechanismSelection(
        "selection.rubisco-insilico-mechanism.check1"
    )
    source = c.MechanismSource(
        input_id,
        c.identity(nomination),
        c.identity(macro),
        selection,
        tuple(
            c.PrimarySource(name, doi, raw_sources[name].decode())
            for name, doi, _, _ in SOURCE_MANIFEST
        ),
    )
    validate_inputs(source, macro, nomination)
    return source
