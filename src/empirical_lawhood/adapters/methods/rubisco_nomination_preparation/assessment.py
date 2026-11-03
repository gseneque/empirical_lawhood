# SPDX-License-Identifier: MPL-2.0
"""Independent exact stationary equations for prospective rationale witnesses."""

from decimal import Decimal, localcontext
from fractions import Fraction as F
from hashlib import sha256
import json
from empirical_lawhood.kernel.decoding import decode_canonical_record
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.science import (
    REFERENCES,
)
from .contracts import (
    AssayPreparationProposal,
    NominationRationaleAssessment,
    NominationRationaleCase,
)

CASE_IDS = (
    "donor-nominal-compatibility",
    "gp-sufficient-unmeasured-headroom",
    "gp-donor-speed-headroom-insufficient",
    "gp-oxygen-recapture-larger-specificity-loss",
    "gp-mutation-no-release-effect",
)


def number(doc):
    if set(doc) != {"decimal", "fraction"}:
        raise ValueError("rationale number loses its exact rational/decimal view")
    q = F(doc["fraction"])
    with localcontext() as ctx:
        ctx.prec = 80
        d = Decimal(q.numerator) / Decimal(q.denominator)
        if not Decimal(doc["decimal"]).is_finite() or abs(
            d - Decimal(doc["decimal"])
        ) > Decimal("1e-50"):
            raise ValueError("rationale decimal view differs from exact fraction")
    return q


def dec(q):
    with localcontext() as ctx:
        ctx.prec = 60
        return Decimal(q.numerator) / Decimal(q.denominator)


def stationary(branches, gases):
    """Original state-generator conservation plus normalization, exact fractions."""
    count = 1 + 2 * len(branches)
    generator = [[F(0) for _ in range(count)] for _ in range(count)]
    for index, (rates, gas) in enumerate(zip(branches, gases, strict=True)):
        kon, off, a, b, r = rates
        c, p = 1 + index * 2, 2 + index * 2
        for start, end, rate in (
            (0, c, kon * gas),
            (c, 0, off),
            (c, p, a),
            (p, c, b),
            (p, 0, r),
        ):
            generator[end][start] += rate
            generator[start][start] -= rate
    rows = [line + [F(0)] for line in generator[:-1]] + [[F(1)] * (count + 1)]
    for column in range(count):
        pivot = next((i for i in range(column, count) if rows[i][column]), None)
        if pivot is None:
            raise ValueError("rationale stationary generator is singular")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        scale = rows[column][column]
        rows[column] = [q / scale for q in rows[column]]
        for i in range(count):
            if i != column:
                multiple = rows[i][column]
                rows[i] = [
                    q - multiple * b for q, b in zip(rows[i], rows[column], strict=True)
                ]
    occupancy = tuple(row[-1] for row in rows)
    if (
        sum(occupancy) != 1
        or any(q <= 0 for q in occupancy)
        or any(
            sum(q * p for q, p in zip(line, occupancy, strict=True))
            for line in generator
        )
    ):
        raise ValueError("rationale stationary solution violates exact state balance")
    return tuple(occupancy[2 + 2 * i] * rates[4] for i, rates in enumerate(branches))


def _named(preparation, filename, role):
    records = tuple(
        r
        for r in preparation.source_members
        if r.filename == filename and r.role == role
    )
    if len(records) != 1:
        raise ValueError(
            "nomination lacks its uniquely declared " + role + " source " + filename
        )
    return records[0]


def assess_rationale(preparation, macro, candidates):
    material = json.loads(
        _named(preparation, "construct-options.json", "MATERIAL").raw_utf8
    )
    for name in (
        "source_candidate_id",
        "source_ssu_view",
        "lsu_sequence",
        "reported_ssu_sequence",
        "proposed_m1_ssu_sequence",
        "proposed_material_id",
        "processing_gate",
    ):
        if material.get(name) != getattr(preparation, name):
            raise ValueError(
                "nomination material document mismatches its exact typed preparation"
            )
    if (
        material.get("status") != "PROPOSED_NOT_ENTERED"
        or material.get("material_constructed") is not False
        or material.get("assembly_verified") is not False
        or material.get("candidate_actual_kcat") is not None
        or material.get("candidate_actual_specificity") is not None
        or material.get("stoichiometry") != {"LSU": 8, "SSU": 8}
    ):
        raise ValueError(
            "nomination material document fabricates actual construction or measurements"
        )
    actual_assay = decode_canonical_record(
        json.loads(_named(preparation, "paired-assay-proposal.json", "ASSAY").raw_utf8),
        AssayPreparationProposal,
    )
    if actual_assay != preparation.assay:
        raise ValueError(
            "nomination assay source differs from selected complete prospective proposal"
        )
    source = _named(preparation, "exact-conditional-rationale.json", "RATIONALE")
    doc = json.loads(source.raw_utf8)
    if (
        doc.get("schema") != "rubisco-nomination01/exact-conditional-rationale"
        or doc.get("version") != "1.0.0"
        or doc.get("nominee") != "gp.i95m"
        or doc.get("target_biology") != "UNEVALUABLE"
        or doc.get("decision_scope") != "EXPLORATORY_HIGH_RISK_TEST_NOMINEE"
        or doc.get("measured_mutant_kcat") is not None
        or doc.get("measured_mutant_specificity") is not None
        or doc.get("biological_qualification") is not False
        or doc.get("submitted") is not False
        or doc.get("native_contacts") != 0
        or doc.get("new_biological_units") != 0
        or not doc.get("identifiability")
    ):
        raise ValueError(
            "nomination rationale promotes conditional mathematics to measured or qualified biology"
        )
    script = _named(preparation, "conditional_witness.py", "RATIONALE")
    if doc.get("implementation_source_sha256") != script.source_sha256:
        raise ValueError(
            "nomination rationale loses original reproduction script identity"
        )
    donor = doc["donor_source"]
    contrast = _named(preparation, "donor-contrast-authentication.json", "RATIONALE")
    panel_raw = macro.named("wilson2017-panel.json")
    panel = json.loads(panel_raw)["value"]
    if (
        donor["panel_sha256"] != sha256(panel_raw).hexdigest()
        or donor["contrast_sha256"] != contrast.source_sha256
    ):
        raise ValueError("nomination donor source or original contrast substitution")
    contrast_doc = json.loads(contrast.raw_utf8)
    before, after = candidates["wilson2017-row12"], candidates["wilson2017-row17"]
    for label, candidate in (("before", before), ("after", after)):
        row = contrast_doc[label]
        if (
            row not in panel["rows"]
            or row["value"]["sample_id"] != candidate.candidate_id
        ):
            raise ValueError("nomination contrast loses exact original donor row")
    if (
        donor["before_sample_id"] != before.candidate_id
        or donor["after_sample_id"] != after.candidate_id
        or before.lsu_sequence != after.lsu_sequence
        or len(before.ssu_sequence_views) != 1
        or len(after.ssu_sequence_views) != 1
    ):
        raise ValueError(
            "nomination donor comparison changes fixed LSU or exact subunit views"
        )
    changes = tuple(
        (i + 1, a, b)
        for i, (a, b) in enumerate(
            zip(
                before.ssu_sequence_views[0][1],
                after.ssu_sequence_views[0][1],
                strict=True,
            )
        )
        if a != b
    )
    if changes != ((98, "V", "M"),):
        raise ValueError(
            "nomination donor contrast is not the sole source V98M substitution"
        )
    for key, expected in (
        ("turnover_before", before.turnover_s_inv),
        ("turnover_after", after.turnover_s_inv),
        ("specificity_before", before.specificity_dimensionless),
        ("specificity_after", after.specificity_dimensionless),
    ):
        if number(donor[key]) != F(expected):
            raise ValueError(
                "nomination donor endpoint differs from original source means"
            )
    cases = (
        doc["donor_nominal_witness"],
        doc["gp_sufficient_unmeasured_witness"],
        *doc["adverse_witnesses"],
    )
    if tuple(c["case"] for c in cases) != CASE_IDS:
        raise ValueError(
            "nomination omits or substitutes complete positive/adverse case denominator"
        )
    results = []
    gp = candidates["gp.wt"]
    reference = {name: (F(k), F(s)) for name, k, s in REFERENCES}
    for index, case in enumerate(cases):
        if case["status"] != "CONDITIONAL_MATHEMATICAL_WITNESS_NOT_MUTATION_PREDICTION":
            raise ValueError("nomination changes witness into a mutation prediction")
        assumed = case["latent_assumptions"]
        v, uc, uo, lam = (number(assumed[k]) for k in ("vC", "uC", "uO", "lambda"))
        if not (v > uc > 0 and 2 > uo > 0 and lam >= 1):
            raise ValueError(
                "nomination witness changes positive conditional topology domain"
            )
        k, s = (
            (F(before.turnover_s_inv), F(before.specificity_dimensionless))
            if index == 0
            else (F(gp.turnover_s_inv), F(gp.specificity_dimensionless))
        )
        if (
            number(case["parent_turnover"]) != k
            or number(case["parent_specificity"]) != s
        ):
            raise ValueError("nomination witness parent source anchor substitution")
        km = lam * (1 + v) / (lam + v)
        sm = (1 + uc) * (lam + uo) / ((lam + uc) * (1 + uo))
        for key, wanted in (
            ("turnover_multiplier", km),
            ("specificity_multiplier", sm),
            ("conditional_turnover", k * km),
            ("conditional_specificity", s * sm),
        ):
            if number(case[key]) != wanted:
                raise ValueError(
                    "nomination witness changes independently derived response"
                )
        branches = tuple(
            tuple(number(q) for q in case["positive_micro_rate_witnesses"][name])
            for name in ("carbon", "oxygen")
        )
        if any(len(b) != 5 or any(q <= 0 for q in b) for b in branches):
            raise ValueError(
                "nomination microscopic witnesses require all positive exact hypothetical rates"
            )
        for b, target_k, target_eff, target_v, target_u in (
            (branches[0], k, F(1), v, uc),
            (branches[1], F(1, 10), 1 / s, F(2), uo),
        ):
            kon, off, a, rev, r = b
            if (
                a * r / (a + rev + r) != target_k
                or kon * a * r / (off * (rev + r) + a * r) != target_eff
                or (a + rev) / r != target_v
                or off * rev / ((off + a) * r) != target_u
            ):
                raise ValueError(
                    "nomination rates fail source-anchor/latent-coordinate realization"
                )
        checks = []
        for state, pair in (
            ("before", branches),
            ("after", tuple((*b[:4], b[4] * lam) for b in branches)),
        ):
            for branch in pair:
                for gas in (F(1, 100), F(1), F(100)):
                    checks.append(
                        (
                            "three-state-single-branch",
                            state,
                            gas,
                            stationary((branch,), (gas,))[0],
                        )
                    )
            jc, jo = stationary(pair, (F(100), F(200)))
            specificity = jc / jo * 2
            if specificity != (s if state == "before" else s * sm):
                raise ValueError(
                    "nomination competing-gas stationary specificity falsifies response"
                )
            checks.append(("five-state-competing-gases", state, None, specificity))
        recorded = case["stationary_oracle_checks"]
        if len(recorded) != 14:
            raise ValueError("nomination drops independent state-balance checks")
        for actual, expected in zip(recorded, checks, strict=True):
            typ, state, gas, q = expected
            if (
                actual["scope"] != typ
                or actual["state"] != state
                or (gas is not None and number(actual["gas_uM"]) != gas)
                or number(
                    actual["exact_flux" if gas is not None else "exact_specificity"]
                )
                != q
            ):
                raise ValueError(
                    "nomination retained stationary checks differ from independent exact state balance"
                )
        results.append(
            NominationRationaleCase(
                case["case"],
                dec(km),
                dec(sm),
                dec(k * km),
                dec(s * sm),
                tuple(
                    (name, k * km >= tk and s * sm >= ts)
                    for name, (tk, ts) in sorted(reference.items())
                ),
                len(checks),
            )
        )
    if number(cases[0]["turnover_multiplier"]) != F(after.turnover_s_inv) / F(
        before.turnover_s_inv
    ) or number(cases[0]["specificity_multiplier"]) != F(
        after.specificity_dimensionless
    ) / F(before.specificity_dimensionless):
        raise ValueError(
            "nomination donor witness fails both actual donor macro ratios"
        )
    if set(doc["targets"]) != set(reference):
        raise ValueError("nomination omits one original reference target")
    for name, (k, s) in reference.items():
        target = doc["targets"][name]
        required = k / F(gp.turnover_s_inv)
        for key, expected in (
            ("turnover_target", k),
            ("specificity_target", s),
            ("required_turnover_multiplier", required),
            ("strict_vC_lower_bound", required - 1),
            ("minimum_lambda_given_vC10", required * 10 / (11 - required)),
            (
                "naive_donor_ratio_transport_turnover",
                F(gp.turnover_s_inv)
                * F(after.turnover_s_inv)
                / F(before.turnover_s_inv),
            ),
        ):
            if number(target[key]) != expected:
                raise ValueError(
                    "nomination target or necessary headroom threshold substitution"
                )
        if (
            target["gp_sufficient_witness_joint_pass"]
            is not dict(results[1].target_joint_pass)[name]
            or target["naive_transport_joint_pass"] is not False
        ):
            raise ValueError(
                "nomination promotes naive transport or changes sufficient conditional classification"
            )
    return NominationRationaleAssessment(
        "assessment." + preparation.proposed_material_id + ".conditional-rationale",
        source.source_sha256,
        tuple(results),
        70,
        "CONDITIONAL_MATHEMATICAL_WITNESS_NOT_MUTATION_PREDICTION",
        "UNEVALUABLE",
    )
