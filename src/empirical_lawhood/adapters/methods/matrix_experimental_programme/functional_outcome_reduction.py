# SPDX-License-Identifier: MPL-2.0
"""Private complete-result arithmetic shared by separately guarded consumers.

This owner receives no scientific source, score, fitted data, access grant or
sampling authority. Its caller authenticates actual subjects and outcomes.
"""

from dataclasses import replace
from decimal import Decimal

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import assigned_binomial_inference, binomial_upper_tail

from .records import MatrixFunctionalCriterion


def _matched_nomination_values(groups, arms, baseline, cases):
    """One frozen DEV16 ranking, replayed by the canonical result validator."""
    from .paired_adequacy import PRACTICAL_GAIN, paired_adequacy
    from .science import MatrixFunctionalCaseResult, _effort_sum

    if (type(groups) is not tuple or len(groups) != 16 or groups != tuple(sorted(set(groups)))
            or type(cases) is not tuple or any(type(row) is not MatrixFunctionalCaseResult for row in cases)):
        raise ValueError("matched nomination requires the complete assigned DEV16 outcome census")
    by_unit = {(row.unit_id, row.arm_id): row for row in cases}
    if (len(by_unit) != len(cases) or set(by_unit) != {(unit, arm) for unit in groups for arm in arms}
            or any(row.response_adequacy_meaning != "SAMPLED_FACTOR_RESPONSE_ADEQUACY_THROUGH64_NOT_EXTERNAL_TASK" for row in cases)):
        raise ValueError("matched nomination drops or substitutes an assigned sampled-adequacy result")
    candidates, tables, rescues = [], [], set()
    for arm in arms:
        if arm == baseline:
            continue
        rows = tuple(by_unit[(unit, arm)] for unit in groups)
        paired = paired_adequacy(groups, tuple(row.response_adequacy for row in rows),
            tuple(by_unit[(unit, baseline)].response_adequacy for unit in groups))
        effort = None if any(row.preparation_effort is None for row in rows) else _effort_sum(tuple(row.preparation_effort for row in rows))
        candidates.append((arm, sum(row.response_adequacy is True for row in rows), len(paired.observed_gain_ids), effort))
        tables.append((arm, paired))
        rescues.update(paired.observed_gain_ids)
    eligible = tuple(arm for arm, paired in tables if len(paired.observed_gain_ids) >= 2
        and paired.conservative.net_gain >= PRACTICAL_GAIN)
    selected = None
    uncertain = any(table.unknown_group_ids for _, table in tables)
    if eligible:
        values = dict(tables)
        maximum = max(values[arm].conservative.net_gain for arm in eligible)
        tied = tuple(row for row in candidates if row[0] in eligible and values[row[0]].conservative.net_gain == maximum)
        if len(tied) == 1:
            selected = tied[0][0]
        elif any(row[3] is None for row in tied):
            uncertain = True
        else:
            selected = min(tied, key=lambda row: (row[3], row[0]))[0]
    disposition = "NOMINATED" if selected is not None else "UNEVALUABLE_OPPORTUNITY" if uncertain else "NONDISCRIMINATING_OPPORTUNITY"
    return tuple(candidates), tuple(sorted(rescues)), selected, disposition, tuple(tables)


def _nominate_functional_cases(*, result_id, specification_identity, package_identity, roster_identity, evidence_identity,
        group_ids: tuple[str, ...], arm_ids: tuple[str, ...], hold_arm_id, criterion: MatrixFunctionalCriterion,
        minimum_recoverable_groups: int, tie_policy, recipes: tuple[tuple[str, ObjectIdentity], ...], cases):
    from .science import MatrixFunctionalCaseResult, MatrixPreparationNomination, _effort_sum

    if (type(group_ids) is not tuple or not group_ids or group_ids != tuple(sorted(set(group_ids)))
            or type(arm_ids) is not tuple or arm_ids != tuple(sorted(set(arm_ids))) or len(arm_ids) != 3 or hold_arm_id not in arm_ids
            or type(criterion) is not MatrixFunctionalCriterion or type(minimum_recoverable_groups) is not int or minimum_recoverable_groups < 1
            or tie_policy not in ("LEXICAL_ARM_ID", "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL")
            or type(recipes) is not tuple or tuple(arm for arm, _ in recipes) != arm_ids
            or any(type(value) is not ObjectIdentity for _, value in recipes)
            or any(type(value) is not ObjectIdentity for value in (specification_identity, package_identity, roster_identity, evidence_identity))
            or type(cases) is not tuple or any(type(row) is not MatrixFunctionalCaseResult for row in cases)):
        raise TypeError("functional nomination arithmetic requires exact complete immutable result operands")
    validate_stable_id(result_id)
    criterion.__post_init__()
    for value in (*group_ids, *arm_ids):
        validate_stable_id(value)
    by_unit = {(row.unit_id, row.arm_id): row for row in cases}
    if len(by_unit) != len(cases) or set(by_unit) != {(unit, arm) for unit in group_ids for arm in arm_ids}:
        raise ValueError("functional nomination arithmetic drops or duplicates an assigned whole-group/arm result")
    for row in cases:
        row.__post_init__()
    if criterion.is_matched:
        if minimum_recoverable_groups != 2 or tie_policy != "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL":
            raise ValueError("matched nomination changes its two actual rescues or effort/lexical tie rule")
        candidates, recoverable, selected, disposition, paired = _matched_nomination_values(group_ids, arm_ids, hold_arm_id, cases)
        return MatrixPreparationNomination(result_id, specification_identity, package_identity, roster_identity, evidence_identity,
            group_ids, candidates, recoverable, selected, None if selected is None else dict(recipes)[selected],
            dict(recipes)[hold_arm_id], criterion, tie_policy, disposition, cases, paired_adequacy=paired)
    candidates, recoverable = [], set()
    complete = all(row.disposition == "FINITE" for row in cases)
    for arm in arm_ids:
        if arm == hold_arm_id:
            continue
        rows = tuple(by_unit[(unit, arm)] for unit in group_ids)
        recovered = tuple(unit for unit in group_ids
            if by_unit[(unit, arm)].functional_reliable and not by_unit[(unit, hold_arm_id)].functional_reliable
            and by_unit[(unit, hold_arm_id)].disposition == "FINITE")
        recoverable.update(recovered)
        effort = None if any(row.preparation_effort is None for row in rows) else _effort_sum(tuple(row.preparation_effort for row in rows))
        candidates.append((arm, sum(row.functional_reliable for row in rows), len(recovered), effort))
    nominated = complete and len(recoverable) >= minimum_recoverable_groups
    selected = None
    if nominated:
        if tie_policy == "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL" and any(row[3] is None for row in candidates):
            complete, nominated = False, False
        else:
            selected = min(candidates, key=lambda row: (-row[1], row[3] if tie_policy == "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL" else Decimal(0), row[0]))[0]
            if next(row[2] for row in candidates if row[0] == selected) < minimum_recoverable_groups:
                selected, nominated = None, False
    recipe = None if selected is None else dict(recipes)[selected]
    hold = dict(recipes)[hold_arm_id]
    return MatrixPreparationNomination(result_id, specification_identity, package_identity, roster_identity, evidence_identity,
        group_ids, tuple(candidates), tuple(sorted(recoverable)), selected, recipe,
        hold, criterion, tie_policy,
        "NOMINATED" if nominated else "NONDISCRIMINATING_OPPORTUNITY" if complete else "UNEVALUABLE_OPPORTUNITY", cases)


def _functional_comparison(criterion, comparison_id, groups, successes, rows):
    """Original complete-assigned-group calculation; no sampling warrant."""
    from .science import MatrixFunctionalComparison, _effort_sum

    probability = binomial_upper_tail(len(groups), successes, criterion.null_probability)
    usable = sum(row.disposition == "FINITE" for row in rows)
    admitted = sum(row.conditional_admission for row in rows)
    false = sum(row.false_admission for row in rows)
    missing = tuple(group for group, row in zip(groups, rows, strict=True) if row.disposition != "FINITE")
    met = (probability <= criterion.alpha and usable >= criterion.minimum_usable_groups
        and admitted >= criterion.minimum_admitted_groups and false <= criterion.maximum_false_admissions)
    effort = None if any(row.preparation_effort is None for row in rows) else _effort_sum(tuple(row.preparation_effort for row in rows))
    return MatrixFunctionalComparison(comparison_id, groups, successes, usable, admitted, false,
        sum(row.covered is True for row in rows), sum(row.error_upper is not None for row in rows), missing,
        probability.numerator, probability.denominator, met, effort)


def _confirmation_comparisons(criterion, groups, prepared, hold_arm_id, cases):
    """Declared recipe/original-ramp comparison, retaining every paired group."""
    by_unit = {(row.unit_id, row.arm_id): row for row in cases}
    if len(by_unit) != len(cases) or set(by_unit) != {(group, arm) for group in groups for arm in (hold_arm_id, prepared)}:
        raise ValueError("functional confirmation arithmetic drops or duplicates assigned paired cases")
    rows = tuple(by_unit[(unit, prepared)] for unit in groups)
    if criterion.is_matched:
        from .paired_adequacy import paired_adequacy
        from .science import MatrixFunctionalComparison, _effort_sum

        if (len(groups) != 80 or any(row.response_adequacy_meaning !=
                "SAMPLED_FACTOR_RESPONSE_ADEQUACY_THROUGH64_NOT_EXTERNAL_TASK" for row in cases)):
            raise ValueError("matched confirmation requires all80 assigned sampled-adequacy pairs")
        paired = paired_adequacy(groups, tuple(row.response_adequacy for row in rows),
            tuple(by_unit[(unit, hold_arm_id)].response_adequacy for unit in groups))
        tail = paired.conservative.tail_probability
        effort = None if any(row.preparation_effort is None for row in rows) else _effort_sum(tuple(row.preparation_effort for row in rows))
        return (MatrixFunctionalComparison("e5.preparation", groups, paired.conservative.gains, paired.observed.unit_count,
            sum(row.conditional_admission for row in rows), sum(row.false_admission for row in rows),
            sum(row.covered is True for row in rows), sum(row.error_upper is not None for row in rows),
            paired.unknown_group_ids, tail.numerator, tail.denominator, paired.criterion_met, effort, paired_adequacy=paired),)
    improvements = sum(row.disposition == "FINITE" and by_unit[(unit, hold_arm_id)].disposition == "FINITE"
        and row.functional_reliable and not by_unit[(unit, hold_arm_id)].functional_reliable
        for unit, row in zip(groups, rows, strict=True))
    paired_rows = tuple(row if by_unit[(unit, hold_arm_id)].disposition == "FINITE" else
        replace(row, disposition="UNEVALUABLE", actual_error=None, functional_reliable=False,
            conditional_admission=False, false_admission=False, covered=None,
            reasons=tuple(sorted(set((*row.reasons, "PAIRED_HOLD_UNAVAILABLE")))))
        for unit, row in zip(groups, rows, strict=True))
    return (_functional_comparison(criterion, "e5.preparation", groups, improvements, paired_rows),)


def _transfer_comparisons(criterion, regime_groups, domain_claims, hold_arm_id, cases, *, curve_decisions=None):
    """Both original separate regime events, with no fit or pooled denominator."""
    by_unit = {(row.unit_id, row.arm_id): row for row in cases}
    groups = tuple(unit for _, values in regime_groups for unit in values)
    if (len(regime_groups) != 2 or len(domain_claims) != 2 or len(set(groups)) != len(groups)
            or len(by_unit) != len(cases) or set(by_unit) != {(group, hold_arm_id) for group in groups}):
        raise ValueError("functional transfer arithmetic drops, overlaps or duplicates assigned regime cases")
    if criterion.is_curve_primary != (curve_decisions is not None):
        raise ValueError('functional transfer cannot exchange the original K and amended curve claims')
    if curve_decisions is not None:
        from empirical_lawhood.adapters.methods.matrix_factor_response.curve_prediction import MatchedCurveDecision
        if (not criterion.is_matched or type(curve_decisions) is not tuple
                or any(type(row) is not MatchedCurveDecision for row in curve_decisions)
                or len(curve_decisions) != len(groups) or {row.unit_id for row in curve_decisions} != set(groups)):
            raise ValueError('curve transfer requires the complete assigned independently bound root decisions')
        curve_by_unit = {row.unit_id: row for row in curve_decisions}
    comparisons = []
    for (regime, groups), domain_claim, comparison in zip(regime_groups, domain_claims,
            ("e6.nearby", "e6.shifted"), strict=True):
        rows = tuple(by_unit[(unit, hold_arm_id)] for unit in groups)
        if criterion.is_matched:
            from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import RELATION_METHODS
            from .science import MatrixFunctionalComparison, MatrixCurveFunctionalComparison, _effort_sum

            if (len(groups) != 64 or any(tuple(method for method, _ in row.duration_error_counts) != RELATION_METHODS
                    for row in rows)):
                raise ValueError("matched transfer requires all64 assigned frozen duration comparisons in each regime")
            if curve_decisions is None:
                counts = tuple(dict(row.duration_error_counts) for row in rows)
                events = tuple(None if value['SR'] is None or value['BR'] is None else value['BR'] - value['SR'] >= 2 for value in counts)
            else:
                selected = tuple(curve_by_unit[unit] for unit in groups)
                events = tuple(row.success if row.usable else None for row in selected)
            inference = assigned_binomial_inference(groups, events, null_probability=criterion.null_probability, alpha=criterion.alpha)
            effort = None if any(row.preparation_effort is None for row in rows) else _effort_sum(tuple(row.preparation_effort for row in rows))
            result_type = MatrixFunctionalComparison if curve_decisions is None else MatrixCurveFunctionalComparison
            extra = ({'duration_inference': inference} if curve_decisions is None else
                {'curve_inference': inference, 'curve_decisions': selected})
            comparisons.append(result_type(comparison, groups, inference.successes, len(groups) - inference.unknowns,
                sum(row.conditional_admission for row in rows), sum(row.false_admission for row in rows),
                sum(row.covered is True for row in rows), sum(row.error_upper is not None for row in rows),
                tuple(unit for unit, event in zip(groups, events, strict=True) if event is None),
                inference.tail_numerator, inference.tail_denominator, inference.criterion_met, effort,
                regime, domain_claim, **extra))
            continue
        successes = sum(row.functional_reliable and row.conditional_admission for row in rows)
        comparisons.append(replace(_functional_comparison(criterion, comparison, groups, successes, rows),
            transfer_regime_id=regime, transfer_domain_claim=domain_claim))
    return tuple(comparisons)
