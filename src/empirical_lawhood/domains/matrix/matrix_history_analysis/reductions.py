# SPDX-License-Identifier: MPL-2.0
"""Complete-family scientific reductions for the fixed 256-history population."""

from empirical_lawhood.domains.matrix.matrix_history_analysis.records import HISTORY_FAMILIES


def decimal_metrics(metrics):
    from decimal import Decimal
    import math
    return tuple(sorted((name, Decimal(str(float(value))) if value is not None and math.isfinite(value) else None) for name, value in metrics.items()))



def family_medians(roots):
    """Only a fully evaluated 64-root family has a numerical family median."""
    if tuple(root.root_index for root in roots) != tuple(range(256)):
        raise ValueError("History family reduction requires the complete ordered 256-root census")
    medians = []
    from statistics import median
    for index, family in enumerate(HISTORY_FAMILIES):
        group = roots[index * 64:(index + 1) * 64]
        names = sorted({name for r in group for name, _ in r.metrics})
        values = []
        for name in names:
            sample = [dict(r.metrics).get(name) for r in group]
            values.append((name, median(sample) if all(r.disposition == "COMPLETE" for r in group) and all(v is not None for v in sample) else None))
        medians.append((family, tuple(values)))
    return tuple(medians)
