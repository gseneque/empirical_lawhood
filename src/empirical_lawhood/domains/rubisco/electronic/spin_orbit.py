# SPDX-License-Identifier: MPL-2.0
"""Reusable BP-SOMF operator combination for supplied Cartesian AO integrals.

Native integral acquisition remains with the PySCF adapter. These calculations
preserve the original imaginary-spatial Hartree coefficient convention.
"""
import numpy as np

SOC_ARRAYS = ('soc-one-electron-imaginary', 'soc-two-electron-imaginary')

def combine_breit_pauli_integrals(one, j, k1, k2, *, light_speed_atomic_units):
    """Combine supplied one-electron and direct/exchange Cartesian tensors."""
    two = -(j-1.5*k1-1.5*k2)
    factor = 0.5/light_speed_atomic_units**2
    terms = {name: np.asarray(value*factor, dtype='<f8', order='C')
        for name, value in zip(SOC_ARRAYS, (one, two), strict=True)}
    if any(not np.isfinite(a).all() or not np.allclose(a, -a.transpose(0, 2, 1), rtol=1e-9, atol=1e-12)
            for a in terms.values()):
        raise ValueError('original BP-SOMF integrals violate finite antisymmetric Cartesian conventions')
    return terms
