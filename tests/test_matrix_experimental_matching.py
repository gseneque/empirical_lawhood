# SPDX-License-Identifier: MPL-2.0
"""Real Matrix structural consumers under exposed metadata/byte conformance.

These tests acquire no scientific histories, fit no models and reserve no genuine
fresh population. Original Matrix record revisions and canonical bytes persist.
"""

from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import eligibility as eligibility
from empirical_lawhood.adapters.methods.matrix_parameter_response import paired_grid
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.experimental_matching import MatchedArmDesign
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from empirical_lawhood.runtime.experimental_matching import validate_matched_arms
from tests.test_matrix_factor_confirmation_eligibility import (
    provenance as provenance, publish, stock as stock,
)
from tests.test_matrix_parameter_paired_response import grid_allocation


@pytest.mark.parametrize("groups", (2, 5))
def test_actual_matrix_grid_uses_shared_groups_without_changing_original_record_bytes(groups):
    original, levels = grid_allocation(groups)
    saved = original.canonical_bytes()
    grid = paired_grid.declare_grid(original, grid_id="software.shared-grid", phase="EXPOSED_SOFTWARE",
        levels=levels, axis_scales=("LINEAR",) * 3)
    # Explicit original envelope/field census witnesses that extraction adds no
    # field or revision to the retained Matrix grid contract.
    expected = canonical_json_bytes({"schema": "empirical-lawhood/matrix-parameter-paired/nine-setting-grid",
        "version": "1.0.0", "value": {
            "grid_id": grid.grid_id, "allocation": grid.allocation, "phase": "EXPOSED_SOFTWARE",
            "levels": levels, "axis_scales": ("LINEAR",) * 3,
            "coordinates": grid.coordinates, "matched_groups": grid.matched_groups,
            "standing": "UNENTERED_DECLARED_DESIGN_NO_FRESHNESS_OR_ENTRY_AUTHORITY"}})
    assert grid.canonical_bytes() == expected
    allocation, design = paired_grid.matched_design_projection(grid, original)
    result = validate_matched_arms(design, allocation)
    assert allocation.sources == (grid.allocation,)
    assert allocation.unit_ids() == tuple(group for group, _ in grid.matched_groups)
    assert result.independent_unit_count == groups
    assert result.nested_coordinate_count == 9 * groups
    assert sum(len(unit.numerical_view_ids) for unit in allocation.units) == 18 * groups
    assert all(unit.exposed for unit in allocation.units)
    assert allocation.role_counts == (("development", groups),)
    assert tuple(row.source_record.object_id for row in design.coordinates) == tuple(root.root.root_id for root in original.roots)
    assert design.varying_coordinate_names == tuple(sorted(paired_grid.FACTORS))
    raw = design.canonical_bytes()
    assert decode_canonical_bytes(raw, MatchedArmDesign, maximum_bytes=len(raw)) == design
    assert original.canonical_bytes() == saved


def test_future_confirmation_label_does_not_reclassify_exposed_development_sources():
    original, levels = grid_allocation(64)
    grid = paired_grid.declare_grid(original, grid_id="software.confirmation-intent", phase="CONFIRMATION",
        levels=levels, axis_scales=("LINEAR",) * 3)
    allocation, design = paired_grid.matched_design_projection(grid, original)
    assert allocation.role_counts == (("development", 64),)
    assert all(unit.exposed for unit in allocation.units)
    assert validate_matched_arms(design, allocation).independent_unit_count == 64
    assert not grid.unentered_census(original).complete_independent_groups


def test_shared_matrix_matching_cannot_allow_a_changed_noise_purpose_as_preparation_variation():
    original, levels = grid_allocation(2)
    grid = paired_grid.declare_grid(original, grid_id="software.fixed-noise", phase="EXPOSED_SOFTWARE",
        levels=levels, axis_scales=("LINEAR",) * 3)
    root = original.roots[0]
    stream = replace(root.streams[0], digest_sha256=f"{root.streams[0].effective_seed + 99999:032x}" + "0" * 32)
    changed = replace(original, roots=(replace(root, streams=(stream, *root.streams[1:])), *original.roots[1:]))
    changed_grid = replace(grid, allocation=paired_grid.history_identity(changed))
    with pytest.raises(ValueError, match="invariant"):
        changed_grid.validate_allocation(changed)


def test_actual_matrix_prefit_join_preserves_original_allocation_reservation_and_fit_records(stock):
    plane, source = stock
    reservation = source.reservation
    scope = source.specification.selection.fits[1]
    saved = tuple(record.canonical_bytes() for record in (source.allocation, reservation, scope))
    projected, binding = eligibility.reservation_design_projection(reservation, consuming_role=scope.role)
    assert projected.sources == (source.allocation.identity,)
    assert projected.unit_ids() == tuple(sorted({root.independent_group_id for root in source.allocation.roots}))
    assert projected.role_counts == (("calibration", 1), ("confirmation", 1), ("development", 1), ("withheld_transfer", 1))
    assert binding.publication.sha256 == reservation.publication.logical.content_sha256
    assert binding.materialization_id == reservation.publication.materialization.materialization_id
    assert binding.protected_roles == ("calibration", "confirmation", "withheld_transfer")
    port = plane.open(VerifiedArtifactInput(reservation.publication.logical, reservation.publication.materialization), maximum_bytes=None)
    try:
        eligibility.require_reserved_fit_input(scope, reservation, port)
        assert port.tell() == 0
        assert port.read() == saved[0]
    finally:
        port.close()
    assert tuple(record.canonical_bytes() for record in (source.allocation, reservation, scope)) == saved


def test_prefit_consumer_refuses_partial_nested_group_then_accepts_its_complete_census(stock):
    plane, source = stock
    scope = source.specification.selection.fits[1]
    original = source.allocation
    root = next(root for root in original.roots if root.root_id in scope.root_ids)
    nested = replace(root, root_id=root.root_id + ".nested", streams=tuple(replace(stream,
        seed=stream.seed + 999999) for stream in root.streams))
    allocation = replace(original, roots=tuple(sorted((*original.roots, nested), key=lambda root: root.root_id)))
    reservation = eligibility.MatrixAllocationReservation("reservation.software.nested", allocation,
        publish(plane, allocation, "allocation.nested"))
    partial = replace(scope, reservation=eligibility.identity(reservation))
    complete = replace(partial, root_ids=tuple(sorted((root.root_id, nested.root_id))))
    projected, _ = eligibility.reservation_design_projection(reservation, consuming_role=scope.role)
    assert len(allocation.roots) == 5 and len(projected.units) == 4
    port = plane.open(VerifiedArtifactInput(reservation.publication.logical, reservation.publication.materialization), maximum_bytes=None)
    try:
        with pytest.raises(ValueError, match="nested members"):
            eligibility.require_reserved_fit_input(partial, reservation, port)
        assert port.tell() == 0
        eligibility.require_reserved_fit_input(complete, reservation, port)
        assert port.tell() == 0
    finally:
        port.close()
