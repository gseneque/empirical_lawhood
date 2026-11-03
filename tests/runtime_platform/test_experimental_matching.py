# SPDX-License-Identifier: MPL-2.0
"""Independent declared-census and actual byte joins; no fresh science or authority."""

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from hashlib import sha256
from typing import ClassVar

import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.experimental_matching import (
    MatchedArmDesign, MatchedCoordinate, ParameterAxisScale, ParameterGrid, ParameterGridAxis,
    ParameterGridSetting, PopulationReservationBinding,
)
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from empirical_lawhood.runtime.experimental_matching import (
    require_reserved_population, validate_matched_arms, validate_parameter_grid,
)
from tests.numerical_provenance_fixtures import numerical_plane


D = Decimal


def _identity(name):
    return ObjectIdentity(name, "empirical-lawhood/tests/exposed-matched-source", "1.0.0", sha256(name.encode()).hexdigest())


def _matched(groups=2, arms=("hold", "recipe"), *, views=("view.fine", "view.primary")):
    source = _identity("source.exposed")
    ids = tuple(f"unit.{index:03d}" for index in range(groups))
    allocation = UnitAllocation("allocation.exposed", (source,),
        tuple(IndependentUnit(unit, source.object_id, "family.exposed", views, True) for unit in ids),
        tuple(UnitRoleAssignment(unit, "development") for unit in ids))
    coordinates = tuple(MatchedCoordinate(unit, arm, _identity("row." + unit + "." + arm), (
        ("bath", D("1.25")), ("noise", 100 + index), ("preparation", arm)))
        for index, unit in enumerate(ids) for arm in arms)
    design = MatchedArmDesign("design.exposed", allocation.identity, arms,
        ("bath", "noise", "preparation"), ("preparation",), coordinates)
    return allocation, design


@pytest.mark.parametrize("groups", (1, 2, 7))
@pytest.mark.parametrize("arms", (("hold", "recipe"), ("hold", "recipe_a", "recipe_b")))
def test_declared_preparation_variation_retains_complete_whole_groups(groups, arms):
    allocation, design = _matched(groups, arms)
    result = validate_matched_arms(design, allocation)
    assert result.independent_unit_count == groups
    assert result.nested_coordinate_count == groups * len(arms)
    assert tuple(group.unit_id for group in result.groups) == allocation.unit_ids()
    assert all(tuple(row.arm_id for row in group.coordinates) == arms for group in result.groups)
    assert result.allocation == allocation.identity
    raw = design.canonical_bytes()
    assert decode_canonical_bytes(raw, MatchedArmDesign, maximum_bytes=len(raw)) == design


def test_more_nested_views_do_not_create_independent_groups():
    allocation, design = _matched(3, views=tuple(f"view.{index:03d}" for index in range(128)))
    assert sum(len(unit.numerical_view_ids) for unit in allocation.units) == 384
    result = validate_matched_arms(design, allocation)
    assert result.independent_unit_count == 3 and result.nested_coordinate_count == 6


@pytest.mark.parametrize("damage", ("missing-arm", "missing-whole-group", "extra-group", "duplicate-cell",
    "foreign-allocation", "undeclared-value", "undeclared-arm", "noise", "bath", "forbidden-preparation"))
def test_missing_nested_cells_or_undeclared_matching_changes_are_refused(damage):
    allocation, design = _matched()
    with pytest.raises((ValueError, TypeError)):
        if damage == "missing-arm":
            design = replace(design, coordinates=design.coordinates[:-1])
        elif damage == "missing-whole-group":
            design = replace(design, coordinates=design.coordinates[:2])
        elif damage == "extra-group":
            design = replace(design, coordinates=(*design.coordinates,
                replace(design.coordinates[-1], unit_id="unit.999")))
        elif damage == "duplicate-cell":
            design = replace(design, coordinates=(*design.coordinates, design.coordinates[-1]))
        elif damage == "foreign-allocation":
            allocation = replace(allocation, allocation_id="allocation.foreign")
        elif damage == "undeclared-value":
            row = replace(design.coordinates[-1], values=(*design.coordinates[-1].values, ("unselected", 1)))
            design = replace(design, coordinates=(*design.coordinates[:-1], row))
        elif damage == "undeclared-arm":
            design = replace(design, coordinates=(*design.coordinates[:-1],
                replace(design.coordinates[-1], arm_id="recipe_new")))
        elif damage == "forbidden-preparation":
            design = replace(design, varying_coordinate_names=())
        else:
            row = design.coordinates[-1]
            field = "noise" if damage == "noise" else "bath"
            values = tuple((name, value + 1 if name == field else value) for name, value in row.values)
            design = replace(design, coordinates=(*design.coordinates[:-1], replace(row, values=values)))
        validate_matched_arms(design, allocation)


@pytest.mark.parametrize("value", (True, False, 1.0, float("inf"), D("NaN"), D("Infinity"), [1], None))
def test_matching_rejects_untyped_or_nonfinite_scalars(value):
    with pytest.raises((TypeError, ValueError)):
        MatchedCoordinate("unit.exposed", "hold", _identity("source.exposed"), (("coordinate", value),))


def test_integer_and_decimal_equality_does_not_alias_an_invariant_coordinate():
    allocation, design = _matched(1)
    row = design.coordinates[-1]
    row = replace(row, values=tuple((name, D(value) if name == "noise" else value) for name, value in row.values))
    assert 100 == D(100)
    with pytest.raises(ValueError, match="scalar type"):
        validate_matched_arms(replace(design, coordinates=(design.coordinates[0], row)), allocation)


def _grid():
    # Hand-enumerated eight corners, with independently stated center. These
    # values are not derived by the implementation's Cartesian-product helper.
    corners = ((D(1), D(10), D(-3)), (D(1), D(10), D(7)),
        (D(1), D(30), D(-3)), (D(1), D(30), D(7)),
        (D(9), D(10), D(-3)), (D(9), D(10), D(7)),
        (D(9), D(30), D(-3)), (D(9), D(30), D(7)))
    axes = (ParameterGridAxis("first", (D(1), D(3), D(9)), ParameterAxisScale.LOG),
        ParameterGridAxis("second", (D(10), D(20), D(30)), ParameterAxisScale.LINEAR),
        ParameterGridAxis("third", (D(-3), D(2), D(7)), ParameterAxisScale.LINEAR))
    return ParameterGrid("grid.exposed", axes,
        tuple(ParameterGridSetting(f"setting.{index}", values)
            for index, values in enumerate((*corners, (D(3), D(20), D(2))))))


def test_explicit_linear_and_log_parameter_grid_has_all_corners_and_actual_center():
    grid = _grid()
    assert validate_parameter_grid(grid) is grid
    raw = grid.canonical_bytes()
    assert decode_canonical_bytes(raw, ParameterGrid, maximum_bytes=len(raw)) == grid


@pytest.mark.parametrize("damage", ("missing", "duplicate-values", "duplicate-id", "wrong-corner", "false-linear-center",
    "false-log-center", "axis-order", "wrong-width", "nonpositive-log", "float", "bool"))
def test_parameter_grid_refuses_an_incomplete_or_inconsistent_declaration(damage):
    grid = _grid()
    with pytest.raises((ValueError, TypeError)):
        if damage == "missing":
            grid = replace(grid, settings=grid.settings[:-1])
        elif damage == "duplicate-values":
            grid = replace(grid, settings=(*grid.settings[:-1], replace(grid.settings[-1], values=grid.settings[0].values)))
        elif damage == "duplicate-id":
            grid = replace(grid, settings=(*grid.settings[:-1], replace(grid.settings[-1], setting_id=grid.settings[0].setting_id)))
        elif damage == "wrong-corner":
            grid = replace(grid, settings=(replace(grid.settings[0], values=(D(2), D(10), D(-3))), *grid.settings[1:]))
        elif damage in ("false-linear-center", "false-log-center"):
            index = 1 if damage == "false-linear-center" else 0
            axis = replace(grid.axes[index], levels=(grid.axes[index].levels[0], D(21) if index else D(4), grid.axes[index].levels[2]))
            grid = replace(grid, axes=tuple(axis if ordinal == index else value for ordinal, value in enumerate(grid.axes)))
        elif damage == "axis-order":
            grid = replace(grid, axes=(grid.axes[1], grid.axes[0], grid.axes[2]))
        elif damage == "wrong-width":
            grid = replace(grid, settings=(replace(grid.settings[0], values=(D(1),)), *grid.settings[1:]))
        elif damage == "nonpositive-log":
            grid = replace(grid, axes=(replace(grid.axes[0], levels=(D(0), D(3), D(9))), *grid.axes[1:]))
        else:
            value = 1.0 if damage == "float" else True
            grid = replace(grid, settings=(replace(grid.settings[0], values=(value, D(10), D(-3))), *grid.settings[1:]))
        validate_parameter_grid(grid)


def test_grid_count_refuses_before_enumerating_an_exponential_missing_census():
    grid = ParameterGrid("grid.incomplete-large", tuple(ParameterGridAxis(f"axis.{index}",
        (D(0), D(1), D(2)), ParameterAxisScale.LINEAR) for index in range(1000)),
        (ParameterGridSetting("setting.center", (D(1),) * 1000),))
    with pytest.raises(ValueError, match="complete corner/center"):
        validate_parameter_grid(grid)


def test_log_midpoint_uses_exact_rational_values_despite_a_low_decimal_context():
    with localcontext() as context:
        context.prec = 2
        axis = ParameterGridAxis("axis.log", (D("1e50"), D("2e50"), D("4e50")), ParameterAxisScale.LOG)
        grid = ParameterGrid("grid.log", (axis,), tuple(ParameterGridSetting(f"setting.{index}", (value,))
            for index, value in enumerate(axis.levels)))
        assert validate_parameter_grid(grid) is grid
        false_center = D("200000000000000000000000000000000000000000000000001")
        changed = replace(grid, axes=(replace(axis, levels=(axis.levels[0], false_center, axis.levels[2])),))
        with pytest.raises(ValueError, match="exact center"):
            validate_parameter_grid(changed)


@dataclass(frozen=True, slots=True)
class OriginalUnit(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tests/exposed-original-unit"
    unit_id: str
    role: str
    exposed: bool


@dataclass(frozen=True, slots=True)
class OriginalAllocation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tests/exposed-original-allocation"
    allocation_id: str
    units: tuple[OriginalUnit, ...]


def _reservation(tmp_path, *, exposed=False):
    # Literal exposed software records model the metadata refusal boundary.
    # A False field is not scientific source-freshness evidence.
    original = OriginalAllocation("original.exposed", (
        OriginalUnit("unit.far", "e6_far", exposed), OriginalUnit("unit.fit", "train", True),
        OriginalUnit("unit.near", "e6_near", exposed)))
    source = ObjectIdentity.from_record(original.allocation_id, original)
    allocation = UnitAllocation("allocation.projected", (source,),
        tuple(IndependentUnit(row.unit_id, source.object_id, "regime." + row.role,
            ("view.fine", "view.primary"), row.exposed) for row in original.units),
        tuple(UnitRoleAssignment(row.unit_id, row.role) for row in original.units))
    plane = numerical_plane(tmp_path / "custody")
    publication = plane.write(ArtifactWriteRequest("publication.original-allocation", "inputs/original.json",
        original.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.original-allocation", "inputs",
        original.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    artifact = ArtifactIdentity(publication.logical.logical_artifact_id, "original-reserve", original.SCHEMA,
        publication.logical.content_sha256, "application/json", publication.materialization.size_bytes)
    binding = PopulationReservationBinding("reservation.exposed", allocation.identity, source, "allocation_id",
        artifact, publication.materialization.materialization_id, ("e6_far", "e6_near"))
    port = plane.open(VerifiedArtifactInput(publication.logical, publication.materialization), maximum_bytes=None)
    return original, allocation, binding, port


def test_actual_original_reserved_publication_joins_without_mutating_source_bytes_or_consuming_parent_cursor(tmp_path):
    original, allocation, binding, port = _reservation(tmp_path)
    saved = original.canonical_bytes()
    try:
        assert require_reserved_population(binding, allocation, original, port, fitting_unit_ids=("unit.fit",)) == (
            "unit.far", "unit.near")
        assert port.tell() == 0 and port.read() == saved
        assert original.canonical_bytes() == saved
        raw = binding.canonical_bytes()
        assert decode_canonical_bytes(raw, PopulationReservationBinding, maximum_bytes=len(raw)) == binding
    finally:
        port.close()


@pytest.mark.parametrize("damage", ("source-id", "source-field", "source-record", "allocation", "source-membership",
    "publication-id", "materialization", "schema", "size", "access", "visibility", "untyped-access", "untyped-visibility",
    "untyped-kind", "role", "fit-overlap",
    "fit-unallocated", "fit-duplicate", "exposed", "attempted-unexpose"))
def test_actual_reservation_join_refuses_substitution_exposure_or_fit_leakage(tmp_path, damage):
    original, allocation, binding, port = _reservation(tmp_path, exposed=damage in ("exposed", "attempted-unexpose"))
    fitting = ("unit.fit",)
    try:
        with pytest.raises((TypeError, ValueError)):
            if damage == "source-id":
                binding = replace(binding, source_allocation=replace(binding.source_allocation, object_id="source.renamed"))
            elif damage == "source-field":
                binding = replace(binding, source_id_field="unknown_field")
            elif damage == "source-record":
                original = replace(original, allocation_id="source.renamed")
            elif damage == "allocation":
                allocation = replace(allocation, allocation_id="allocation.renamed")
            elif damage == "source-membership":
                other = _identity("source.foreign")
                allocation = replace(allocation, sources=(other,), units=tuple(replace(unit, source_id=other.object_id)
                    for unit in allocation.units))
                binding = replace(binding, allocation=allocation.identity)
            elif damage in ("publication-id", "materialization", "schema", "size", "access", "visibility",
                    "untyped-access", "untyped-visibility", "untyped-kind"):
                changes = {"publication-id": {"artifact_id": "publication.foreign"},
                    "materialization": {"materialization_id": "materialization.foreign"},
                    "schema": {"payload_schema": OriginalUnit.SCHEMA}, "size": {"size_bytes": port.size_bytes + 1},
                    "access": {"outcome_access": OutcomeAccess.DEVELOPMENT_VISIBLE},
                    "visibility": {"visibility_ceiling": VisibilityCeiling.DEVELOPMENT_ONLY},
                    "untyped-access": {"outcome_access": OutcomeAccess.OUTCOME_BLIND.value},
                    "untyped-visibility": {"visibility_ceiling": VisibilityCeiling.PROSPECTIVE.value},
                    "untyped-kind": {"kind": port.kind.value}}[damage]
                port = replace(port, binding=replace(port.binding, **changes))
            elif damage == "role":
                binding = replace(binding, protected_roles=("e6_missing",))
            elif damage == "fit-overlap":
                fitting = ("unit.fit", "unit.near")
            elif damage == "fit-unallocated":
                fitting = ("unit.unknown",)
            elif damage == "fit-duplicate":
                fitting = ("unit.fit", "unit.fit")
            elif damage == "attempted-unexpose":
                allocation = replace(allocation, units=tuple(replace(unit, exposed=False) for unit in allocation.units))
                # The immutable original binding continues to own exposure.
            require_reserved_population(binding, allocation, original, port, fitting_unit_ids=fitting)
    finally:
        port.close()
