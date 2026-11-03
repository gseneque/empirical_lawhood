"""Independent historical scalar closure check using raw native matrices.

This retains the q=2 residual and normalization of the historical 0.30
criterion. It uses no passive generator, band ratio, spectrum or producer.
"""

from decimal import Decimal

import numpy as np


def independent_scalar_closure_ratio(triplet, alpha_tilde):
    fields = np.asarray(triplet)
    if (fields.shape != (3, 4, 4) or fields.dtype.str != "<c16"
            or not np.isfinite(fields).all()
            or not np.allclose(fields, fields.conj().swapaxes(-1, -2), atol=1e-10, rtol=0)
            or not np.isfinite(alpha_tilde) or alpha_tilde < 0):
        raise ValueError("scalar closure assessment needs complete q2 Hermitian fields and original coupling")
    # The native parameter alpha is alpha_tilde/q, with q=2. Retain the
    # original operation order instead of simplifying or replacing it.
    physical_alpha = float(alpha_tilde)/2.0
    coefficient = 2.0*physical_alpha/3.0
    residual = max(float(np.linalg.norm(fields[b]@fields[c]-fields[c]@fields[b]
        -1.0j*coefficient*fields[a])) for a,(b,c) in enumerate(((1,2),(2,0),(0,1))))
    radius = float(np.trace(np.sum(fields@fields, axis=0)).real/4)
    denominator = abs(float(alpha_tilde)/3)*np.sqrt(4*max(radius,0)/3)
    ratio = residual/max(float(denominator),np.finfo(float).tiny)
    if not np.isfinite(ratio):
        raise ValueError("independent scalar closure ratio is numerically unresolved")
    return Decimal(str(float(ratio)))


def assess_scalar_trace(trace, spec, positions, couplings):
    if spec.scalar_closure is None:
        if any(o.scalar_closure_ratio is not None for o in trace.observations):
            raise ValueError("unselected scalar comparison contains undeclared operands")
        return {"requested_observations":len(trace.observations),"assessed_observations":0,"disposition":"NOT_SELECTED"}
    multiplier = 1 if trace.view == "PRIMARY" else 2
    sector = ("X","Y").index(trace.sector)
    assessed = 0
    for observation in trace.observations:
        native_step = multiplier*observation.tick
        ratio = independent_scalar_closure_ratio(positions[native_step,sector],couplings[native_step,sector])
        if ratio != observation.scalar_closure_ratio or observation.scalar_closure_pass != (ratio <= spec.scalar_closure.threshold):
            raise ValueError("retained scalar comparison differs from actual native fields/couplings or original threshold")
        assessed += 1
    return {"requested_observations":len(trace.observations),"assessed_observations":assessed,"disposition":"INDEPENDENTLY_ASSESSED"}
