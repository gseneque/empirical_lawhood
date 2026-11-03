"""Independent weighted OU bridge transformation."""

import numpy as np


def weighted_ou_bridge(coarse, bridge, *, friction, coarse_timestep):
    """Orthogonal normal transform; two fine OU steps equal one coarse OU step.

    With a=exp(-gamma*coarse_dt/2), a*z1+z2=sqrt(1+a*a)*zc.
    This couples OU innovations only; the full nonlinear paths may differ.
    """
    coarse,bridge = np.asarray(coarse),np.asarray(bridge)
    if (coarse.shape != bridge.shape or coarse.ndim != 5 or coarse.shape[1:] != (2,3,4,4)
            or coarse.dtype != np.dtype('<c16') or bridge.dtype != np.dtype('<c16')
            or not np.isfinite(coarse).all() or not np.isfinite(bridge).all()
            or not np.allclose(coarse,coarse.swapaxes(-1,-2).conj(),atol=1e-12,rtol=0)
            or not np.allclose(bridge,bridge.swapaxes(-1,-2).conj(),atol=1e-12,rtol=0)
            or not np.isfinite(float(friction)) or float(friction) <= 0
            or not np.isfinite(float(coarse_timestep)) or float(coarse_timestep) <= 0):
        raise ValueError('paired OU bridge requires full finite Hermitian original and independent draws')
    a = np.exp(-float(friction)*float(coarse_timestep)/2)
    divisor = np.sqrt(1+a*a)
    fine = np.empty((2*len(coarse),2,3,4,4),dtype='<c16')
    fine[0::2] = (a*coarse+bridge)/divisor
    fine[1::2] = (coarse-a*bridge)/divisor
    return fine
