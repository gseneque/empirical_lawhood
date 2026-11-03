# SPDX-License-Identifier: MPL-2.0
"""Explicit newly declared release recipes, never missing historical E3 evidence."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import ProtectedE3PreparationSelection
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id


@dataclass(frozen=True, slots=True)
class SelectedE4ReleasePreparationRecipe(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/selected-e4-release-preparation-recipe"
    record_id: str
    prototype: ObjectIdentity
    coordinates: tuple[MatrixParameterCoordinate, ...]
    disclosure: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.prototype) is not ObjectIdentity or self.prototype.object_schema != MatrixParameterCoordinate.SCHEMA
                or type(self.coordinates) is not tuple or any(type(value) is not MatrixParameterCoordinate for value in self.coordinates)
                or tuple(value.family_id for value in self.coordinates) != tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
                or len({value.coordinate_id for value in self.coordinates}) != len(self.coordinates)
                or self.disclosure != "NEW_EXPOSED_RELEASE_RECIPES_NOT_HISTORICAL_E3_FAMILIES"):
            raise ValueError("E4 release recipes require all four explicitly declared native preparation rules")
        self.prototype.__post_init__()
        for value in self.coordinates:
            value.__post_init__()
            if old.coordinate_identity(value) == self.prototype:
                raise ValueError("new E4 recipes must retain their distinct declared identities")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def validate_original(self, original):
        if type(original) is not ProtectedE3PreparationSelection:
            raise TypeError("release recipes require actual authenticated original preparation")
        original.__post_init__()
        rows = tuple(value for value in original.manifest.reservation.allocation.coordinates
            if old.coordinate_identity(value) == self.prototype)
        if len(rows) != 1:
            raise ValueError("release recipe prototype is absent from exact original E3 coordinates")
        prototype, = rows
        for coordinate in self.coordinates:
            # All native scientific schedule fields remain explicit in the
            # copied recipe. Preserve the original member/view/clock operands;
            # family-specific starts and couplings belong to the native owner.
            if (coordinate.member, coordinate.primary_view, coordinate.fine_view, coordinate.clock_id,
                    coordinate.q, coordinate.initial_state_rule_id, coordinate.preparation_rule_id) != (
                    prototype.member, prototype.primary_view, prototype.fine_view, prototype.clock_id,
                    prototype.q, prototype.initial_state_rule_id, prototype.preparation_rule_id):
                raise ValueError("new release recipe substitutes original native numerical or initial/preparation convention")
        return self


def load_preparation_recipe(path, original):
    from pathlib import Path
    selected = Path(path)
    if not selected.is_absolute() or selected.is_symlink():
        raise ValueError("release preparation recipes need an explicit unlinked absolute copied file")
    raw = read_bounded_bytes(selected, maximum_bytes=1024**2)
    recipe = decode_canonical_bytes(raw, SelectedE4ReleasePreparationRecipe, maximum_bytes=1024**2)
    if recipe.canonical_bytes() != raw:
        raise ValueError("release recipe must retain exact canonical configuration bytes")
    return recipe.validate_original(original)
