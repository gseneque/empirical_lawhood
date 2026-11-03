# SPDX-License-Identifier: MPL-2.0
"""Declared primary family configuration; no acquisition or qualification."""
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction

import pytest
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import ConfiguredE3Assessment
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import FAMILY_IDS
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_matrix_later_programme import criterion


def assessment():
    return ConfiguredE3Assessment(improvement_margin=Decimal(".0002"), null_success_numerator=1,
        null_success_denominator=2, alpha_numerator=1, alpha_denominator=240,
        minimum_usable_units=58, comparison_ids=FAMILY_IDS)


@pytest.mark.parametrize("kind", ("e3", "functional"))
def test_explicit_extended_family_retains_exact_old_configuration_and_budget(kind):
    old = assessment() if kind == "e3" else criterion()
    before = old.canonical_bytes()
    field = "comparison_ids" if kind == "e3" else "family_slots"
    family = tuple(sorted((*FAMILY_IDS, "e1.recurrence-survival", "e2.utility")))
    current = replace(old, alpha_denominator=280, **{field: family})
    assert current.alpha == Fraction(1, 280)
    assert current.alpha * len(family) == old.alpha * len(FAMILY_IDS) == Fraction(1, 20)
    assert decode_canonical_bytes(current.canonical_bytes(), type(current), maximum_bytes=None) == current
    assert decode_canonical_bytes(before, type(old), maximum_bytes=None).canonical_bytes() == before
    assert old.canonical_bytes() == before
    for changed in ((), (*family, family[-1]), tuple(reversed(family))):
        with pytest.raises(ValueError): replace(current, **{field: changed})
    # Existing comparisons cannot be dropped under a new name.
    with pytest.raises(ValueError): replace(current, **{field: tuple(value for value in family if value != "e3.model")})
