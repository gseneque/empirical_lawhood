# SPDX-License-Identifier: MPL-2.0
"""Tiny metadata-only owner refusals and unchanged allocation byte identity."""

from dataclasses import dataclass
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import science
from empirical_lawhood.adapters.methods.matrix_experimental_programme.source_selection_metadata import _validate_source_metadata
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord


@dataclass(frozen=True, slots=True)
class ExposedProjectionFixture(CanonicalRecord):
    """An explicit test subject, never an original scheduled source schema."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/tests/exposed-unit-projection"
    allocation_id: str
    phase: str


def test_old_public_source_owner_rejects_duck_specification_before_any_metadata():
    for candidate in (None, object(), SimpleNamespace(phase="E5_OPPORTUNITY", expected_groups=16),
            ExposedProjectionFixture("allocation.literal-wrong-owner", "E5_OPPORTUNITY")):
        with pytest.raises(TypeError, match="exact typed selection"):
            science.validate_sources(candidate, None, None)


def test_private_metadata_helper_refuses_foreign_original_record_owners():
    with pytest.raises(TypeError, match="exact original roster"):
        _validate_source_metadata(phase="E5_OPPORTUNITY", roster_reference=None, package_reference=None,
            expected_groups=16, arm_ids=("hold", "recipe.a", "recipe.b"), transfer_regime_ids=(),
            selection_sha256="a" * 64, roster=SimpleNamespace(cases=()), package=None)


def test_unchanged_old_allocation_projection_retains_exact_fingerprint_and_whole_unit():
    selected = ExposedProjectionFixture("allocation.literal-original-projection", "E5_OPPORTUNITY")
    original = ObjectIdentity.from_record(selected.allocation_id, selected)
    root = MatrixProgrammeRoot("root.literal-projection", "group.literal-projection", "regime.literal-projection",
        "coordinate.literal-projection", MatrixProgrammeRole.DEVELOPMENT, "clock.literal-projection")
    public = SimpleNamespace(root=root, allocation=original, coordinate=SimpleNamespace(
        primary_view=SimpleNamespace(view_id="view.primary"), fine_view=SimpleNamespace(view_id="view.fine")))
    case = SimpleNamespace(unit_id=root.independent_group_id, public_source=public)
    projected = science.source_allocation(selected, SimpleNamespace(allocations=(selected,), cases=(case,)))
    expected = UnitAllocation("allocation.matrix-later." + selected.fingerprint(), (original,),
        (IndependentUnit(root.independent_group_id, selected.allocation_id, root.regime_id, ("view.fine", "view.primary"), True),),
        (UnitRoleAssignment(root.independent_group_id, "opportunity"),))
    assert projected.canonical_bytes() == expected.canonical_bytes()
    # The projection primitive grants no assessment entry to this test subject.
    with pytest.raises(TypeError, match="exact typed selection"):
        science.validate_sources(selected, SimpleNamespace(cases=(case,)), None)
