# SPDX-License-Identifier: MPL-2.0
"""Declared Matrix primary comparison families; no statistical data or authority."""
from empirical_lawhood.kernel.serialization import validate_stable_id

AMENDED_PRIMARY_FAMILY = tuple(sorted(('e1.map', 'e2.adequacy', 'e2.structure', 'e3.forecast',
    'e4.relation', 'e5.preparation', 'e6.nearby', 'e6.shifted')))


def validate_declared_primary_family(family, *, required):
    if (type(family) is not tuple or not family or any(type(value) is not str for value in family)
            or family != tuple(sorted(set(family))) or not set(required) <= set(family)):
        raise ValueError("primary family must retain every actual programme comparison, including unused slots")
    for value in family:
        validate_stable_id(value)
    return family
