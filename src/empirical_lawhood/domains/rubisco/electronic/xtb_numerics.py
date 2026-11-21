"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from math import isfinite, sqrt


ANGSTROM_PER_BOHR = Decimal('0.52917726')


def angstrom_to_bohr(value):
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError('finite Decimal Angstrom coordinate required')
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        return value / ANGSTROM_PER_BOHR


def bohr_to_angstrom(value):
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError('finite Decimal Bohr coordinate required')
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        return value * ANGSTROM_PER_BOHR


def gradient_hartree_per_angstrom(value):
    """Chain rule: an Eh/Bohr derivative is divided by Angstrom/Bohr."""
    return angstrom_to_bohr(value)


def gfn2_damped_coulomb_kernel(distance_bohr, qm_shell_hardness, external_hardness=99.0):
    """Tagged GFN2 kernel only: arithmetic hardness mean, not singular 1/r."""
    values = (distance_bohr, qm_shell_hardness, external_hardness)
    if any(type(v) not in (int, float) or not isfinite(v) for v in values):
        raise ValueError('finite native-kernel operands required')
    if distance_bohr < 0 or qm_shell_hardness <= 0 or external_hardness != 99:
        raise ValueError('nonnegative distance, positive shell hardness and selected99 required')
    combined = (qm_shell_hardness + external_hardness) / 2
    return 1 / sqrt(distance_bohr ** 2 + 1 / combined ** 2)
