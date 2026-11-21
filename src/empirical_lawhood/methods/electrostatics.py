# SPDX-License-Identifier: MPL-2.0
"""Solver-independent electrostatic terms with explicit atomic-unit operands."""

import math


def charged_background_energy(*, qm_charge, mm_charge, volume_bohr3, eta_inverse_bohr):
    """Uniform Ewald-background QM self and QM/MM cross energy, in hartree.

Charges are in elementary-charge units; volume is in bohr cubed and the
positive Ewald screening parameter in inverse bohr. The fixed-charge, fixed-
cell term has zero Cartesian derivative. The MM-only background contribution
belongs to the selected molecular potential and is deliberately excluded.
This term does not determine boundary conventions for another physical model.
"""
    values = tuple(float(v) for v in (qm_charge, mm_charge, volume_bohr3, eta_inverse_bohr))
    if not all(math.isfinite(v) for v in values) or min(values[2:]) <= 0:
        raise ValueError('charged periodic background requires finite charges, positive volume and eta')
    q, m, volume, eta = values
    numerator, denominator = -math.pi*(q*q + 2*q*m), 2*volume*eta*eta
    if not math.isfinite(numerator) or not math.isfinite(denominator) or denominator <= 0:
        raise ValueError('charged periodic background exceeds finite binary64 arithmetic')
    result = numerator/denominator
    if not math.isfinite(result):
        raise ValueError('charged periodic background exceeds finite binary64 arithmetic')
    return result
