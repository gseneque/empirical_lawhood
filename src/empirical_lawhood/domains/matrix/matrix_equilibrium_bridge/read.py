# SPDX-License-Identifier: MPL-2.0
"""Independent covariance equations for the frozen equilibrium estimator."""
from decimal import Decimal
import numpy as np


def check_fit(config, parents, arrays, product, actual):
    selected = sorted((p for p in parents.values() if p.config.phase == 'assess'), key=lambda p:p.config.root.ordinal)
    if len(selected) != 16 or product.fit is None: raise PermissionError('SCI02-D read loses its complete training fit')
    covariance = np.zeros((5,5)); degrees = 0
    for source in selected:
        for preparation in arrays[source.config.node_id]['series'][0]:
            n = len(preparation)//config.design.block_samples
            means = np.array([preparation[i*config.design.block_samples:(i+1)*config.design.block_samples].mean(axis=0) for i in range(n)])
            covariance += np.cov(means.T, ddof=1)*(n-1)
            degrees += n-1
    covariance /= degrees
    ridge = float(config.design.ridge_fraction)*max(np.diag(covariance)[1:].max(), np.finfo(float).tiny)
    coefficient = np.zeros((3,4))
    if covariance[1,1] > 0: coefficient[1,0] = covariance[0,1]/covariance[1,1]
    coefficient[2] = np.linalg.solve(covariance[1:,1:]+ridge*np.eye(4),covariance[1:,0])
    weights = np.concatenate((np.ones((3,1)),-coefficient),axis=1)
    ratios = np.array([w@covariance@w for w in weights])/covariance[0,0] if covariance[0,0] > 0 else np.ones(3)
    fraction = tuple(next((Decimal(str(f)) for f in (.25,.5,1.) if f >= r),Decimal(1)) for r in ratios)
    np.testing.assert_allclose(actual['covariance'],covariance,atol=1e-12,rtol=1e-10)
    np.testing.assert_allclose(np.array(product.fit.coefficients,dtype=float),coefficient,atol=1e-12,rtol=1e-10)
    if product.fit.training != tuple(p.identity for p in selected) or product.fit.sampling_fractions != fraction:
        raise PermissionError('SCI02-D frozen estimator changes exact original training or bounded allocation')
