# SPDX-License-Identifier: MPL-2.0
"""Operating characteristics of the M1 structural handoff decision on independent roots."""

import math

import numpy as np
from scipy.stats import binom


def paired_delivery_halfwidth(assigned: int, module_alpha: float) -> float:
    """Simultaneous one-sided allowance used by the two M1 policy comparisons."""
    if type(assigned) is not int or assigned <= 0 or not 0 < module_alpha < 1:
        raise ValueError("Structural service needs independent roots and a module error allowance")
    return math.sqrt(2 * math.log(16 / module_alpha) / assigned)


def structural_service_design(
    *, assigned, module_alpha, delivery_floor, wrong_ceiling, allowed_loss,
    delivery_probability, wrong_probability, gain_probability, harm_probability,
    cheaper_probability,
):
    """Exact marginal passage probabilities under a stated complete-root scenario.

    Gains and harms refer to the same pair of policies. Delivery and wrong offers
    are disjoint assigned-root events. No independence between gates is assumed.
    The magnitude of paid force-call savings is an additional measured endpoint.
    """
    halfwidth = paired_delivery_halfwidth(assigned, module_alpha)
    probabilities = (delivery_probability, wrong_probability, gain_probability,
                     harm_probability, cheaper_probability)
    if (any(not 0 <= p <= 1 for p in probabilities)
            or not 0 < delivery_floor < 1 or not 0 < wrong_ceiling < 1
            or not 0 <= allowed_loss <= 1
            or delivery_probability + wrong_probability > 1
            or gain_probability > delivery_probability
            or harm_probability > 1 - delivery_probability + 1e-15):
        raise ValueError("Incompatible probabilities or margins for the paired service scenario")
    tail = module_alpha / 8
    counts = np.arange(assigned + 1)
    delivery = binom.sf(counts - 1, assigned, delivery_floor) <= tail
    wrong = binom.cdf(counts, assigned, wrong_ceiling) <= tail
    cheaper = binom.sf(counts - 1, assigned, 0.5) < tail
    net_needed = math.ceil(assigned * (halfwidth - allowed_loss))
    discordance = gain_probability + harm_probability
    pair_power = float(net_needed <= 0)
    if discordance:
        # Given m discordances, net gains equal twice the wins minus m.
        wins_needed = np.ceil((counts + net_needed) / 2).astype(int)
        pair_power = float(binom.pmf(counts, assigned, discordance)
                           @ binom.sf(wins_needed - 1, counts, gain_probability / discordance))
    passage = {
        "delivery_floor": float(binom.pmf(counts, assigned, delivery_probability)[delivery].sum()),
        "wrong_offer_ceiling": float(binom.pmf(counts, assigned, wrong_probability)[wrong].sum()),
        "paired_coverage_loss": pair_power,
        "probability_cheaper": float(binom.pmf(counts, assigned, cheaper_probability)[cheaper].sum()),
    }
    return {
        "assigned_roots": assigned, "module_alpha": module_alpha, "individual_tail": tail,
        "simultaneous_paired_halfwidth": halfwidth,
        "minimum_deliveries": int(counts[delivery][0]) if delivery.any() else None,
        "maximum_wrong_assignments": int(counts[wrong][-1]) if wrong.any() else None,
        "minimum_net_deliveries": net_needed,
        "minimum_cheaper_roots": int(counts[cheaper][0]) if cheaper.any() else None,
        "marginal_pass_probabilities": passage,
        "joint_pass_probability_upper_bound": min(passage.values()),
        "scope": "COMPLETE_PAIRED_ROOTS_POSITIVE_MEAN_COST_SAVING_STILL_REQUIRED",
    }
