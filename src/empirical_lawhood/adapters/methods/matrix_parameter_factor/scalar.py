"""Actual-member scalar sampling; the historical 0.30 contrast is geometric."""

from decimal import Decimal

import numpy as np

from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_derivatives import parameters

from .records import MatrixParameterScalarSample, VIEWS


def measure(parameter, supply, rule, arrays):
    return measure_values(parameter.coordinate, supply.state, rule, arrays)


def measure_values(coordinate, source_state, rule, arrays):
    """Use actual potential member and exact native schedule/clock at each tick.

    This avoids the old API's fixed member and the geometry observer's fixed
    16-tick cadence. It preserves the same residual/normalization operation
    order and never calls a passive generator or makes physical admission.
    """
    result = []
    for view in VIEWS:
        multiplier = 1 if view=='PRIMARY' else 2
        for sector in rule.sectors:
            for tick in rule.lattice:
                ratio, reason = None, 'SOURCE_'+source_state
                if arrays is not None:
                    i = multiplier*tick
                    base = view.lower()
                    x,y = arrays[base+'_alpha_tilde'][i]
                    state = SixMatrixState(2,arrays[base+'_positions'][i],arrays[base+'_momenta'][i],i,float(x),float(y))
                    selected = parameters(state,coordinate.member)
                    fields = state.positions[('X','Y').index(sector)]
                    alpha = (x,y)[('X','Y').index(sector)]
                    # Bind actual member/beta above; the named geometric
                    # comparison itself contains no M/cross coefficient.
                    # Do not evaluate unrelated action/kinetic receivers.
                    with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
                        coefficient = 2*((selected.alpha_x,selected.alpha_y)[('X','Y').index(sector)])/3
                        residual = max(float(np.linalg.norm(fields[b]@fields[c]-fields[c]@fields[b]
                            -1j*coefficient*fields[a])) for a,(b,c) in enumerate(((1,2),(2,0),(0,1))))
                        radius = float(np.trace(np.sum(fields@fields,axis=0)).real/selected.n)
                        scale = abs(alpha/3)*np.sqrt(4*max(radius,0)/3)
                        value = residual/max(float(scale),np.finfo(float).tiny)
                    ratio = Decimal(str(float(value))) if np.isfinite(value) else None
                    reason = None if ratio is not None else 'SCALAR_NUMERICALLY_UNRESOLVED'
                result.append(MatrixParameterScalarSample(view,sector,tick,ratio,reason))
    return tuple(result)
