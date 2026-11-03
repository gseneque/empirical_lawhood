# SPDX-License-Identifier: MPL-2.0
"""Explicit family derivation controls; no native acquisition or qualification."""
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import initial_parameter_state
from tests.matrix_selected_e4_preparation_recipe import SelectedE4ReleasePreparationRecipe
from tests.test_matrix_selected_protected import transfer  # noqa: F401
from tests.test_matrix_selected_point import selected_design


def recipe_and_prototype():
    prototype = selected_design().sources[0][1].original.coordinate
    coordinates = tuple(replace(prototype, coordinate_id="recipe.disclosed." + str(index), family_id=family)
        for index, family in enumerate(sorted(FOUR_FAMILY_PREPARATION_IDS)))
    return SelectedE4ReleasePreparationRecipe("recipe.disclosed.release", old.coordinate_identity(prototype), coordinates,
        "NEW_EXPOSED_RELEASE_RECIPES_NOT_HISTORICAL_E3_FAMILIES"), prototype


def test_new_four_family_recipe_executes_each_existing_declared_initial_and_coupling_rule():
    recipe, prototype = recipe_and_prototype()
    original_bytes = prototype.canonical_bytes()
    assert len({value.family_id for value in recipe.coordinates}) == 4
    starts = {value.family_id: initial_parameter_state(value) for value in recipe.coordinates}
    decreasing = "matrix-history.joint-decreasing-coupling"
    assert starts[decreasing].alpha_tilde_x == float(prototype.decreasing_start)
    assert starts[decreasing].alpha_tilde_y == float(prototype.decreasing_start)
    assert all(value.alpha_tilde_x == value.alpha_tilde_y == 0 for key, value in starts.items() if key != decreasing)
    for value in recipe.coordinates:
        assert value.couplings(value.ramp_ticks) == pytest.approx(
            (float(value.target_x), float(value.target_y)), rel=0, abs=1e-14)
        assert old.coordinate_identity(value) != recipe.prototype
    assert prototype.canonical_bytes() == original_bytes


def test_release_recipe_refuses_missing_extra_or_relabelled_historical_family():
    recipe, prototype = recipe_and_prototype()
    with pytest.raises(ValueError, match="all four"):
        replace(recipe, coordinates=recipe.coordinates[:-1])
    with pytest.raises(ValueError, match="all four"):
        replace(recipe, coordinates=(*recipe.coordinates, recipe.coordinates[0]))
    with pytest.raises(ValueError, match="distinct declared"):
        replace(recipe, coordinates=tuple(prototype if value.family_id == prototype.family_id else value for value in recipe.coordinates))
