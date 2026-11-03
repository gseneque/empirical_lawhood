# SPDX-License-Identifier: MPL-2.0
"""Supplied-noise equivalence controls, not acquired science or qualification."""
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_records as records
from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_science as prepared
from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_initialization_science as initialization
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPublicSource
from empirical_lawhood.adapters.methods.matrix_experimental_programme.protected_preparation_records import MatrixReservedTransferSources
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import SelectedPreparedProtectedSpecification
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import expected_members
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as scheduled_identity
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history as original
from empirical_lawhood.adapters.simulators.six_matrix_response.simulation import BAOABGradientCache
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_matrix_preparation_initialization import forbid_contact, source_for_family
from tests.test_matrix_selected_point import selected_design
from tests.test_matrix_selected_protected import transfer  # noqa: F401
from tests.test_matrix_later_programme import criterion


def supplied_innovations(count):
    # Literal deterministic nonzero Hermitian values, with distinct bridges.
    # These are disclosed mathematical controls and select no RNG stream.
    values = np.arange(count * 2 * 3 * 4 * 4, dtype="<f8").reshape(count, 2, 3, 4, 4)
    real = (values % 17 - 8) / 256
    imaginary = (values % 13 - 6) / 512
    coarse = ((real + real.swapaxes(-1, -2)) + 1j * (imaginary - imaginary.swapaxes(-1, -2))).astype("<c16")
    bridge = ((real + real.swapaxes(-1, -2)) / 3 - 1j * (imaginary - imaginary.swapaxes(-1, -2)) / 2).astype("<c16")
    return coarse, bridge


def original_prefix(coordinate, count, coarse, bridge):
    """Independent original producer route; no prepared storage or step helper."""
    arrays = {name: np.empty(shape, dtype=dtype) for name, (dtype, shape) in expected_members(SimpleNamespace(total_ticks=count)).items()}
    primary = original.initial_parameter_state(coordinate)
    fine = original.initial_parameter_state(coordinate)
    for view, refinement in (("primary", 1), ("fine", 2)):
        arrays[view + "_ticks"][:] = np.arange(refinement * count + 1, dtype="<i8")
        arrays[view + "_alpha_tilde"][:] = np.asarray(tuple(coordinate.couplings(tick, refinement=refinement)
            for tick in range(refinement * count + 1)), dtype="<f8")
        arrays[view + "_positions"][0] = primary.positions
        arrays[view + "_momenta"][0] = primary.momenta
    primary_cache, fine_cache = BAOABGradientCache(), BAOABGradientCache()
    for tick in range(1, count + 1):
        primary, middle, fine = original.advance_parameter_pair(primary, fine, coordinate=coordinate, coarse_step=tick,
            coarse_noise=coarse[tick - 1], bridge_noise=bridge[tick - 1],
            primary_cache=primary_cache, fine_cache=fine_cache)
        arrays["primary_positions"][tick], arrays["primary_momenta"][tick] = primary.positions, primary.momenta
        arrays["fine_positions"][2 * tick - 1], arrays["fine_momenta"][2 * tick - 1] = middle.positions, middle.momenta
        arrays["fine_positions"][2 * tick], arrays["fine_momenta"][2 * tick] = fine.positions, fine.momenta
        arrays["primary_innovations"][tick - 1] = coarse[tick - 1]
        arrays["bridge_innovations"][tick - 1] = bridge[tick - 1]
        arrays["fine_innovations"][2 * tick - 2:2 * tick] = original.split_parameter_innovations(coordinate, coarse[tick - 1], bridge[tick - 1])
    return arrays


def prepared_original(source):
    initial, raw = initialization.initialize_source(source, source.provenance,
        state_id="initial.disclosed.original-schedule", artifact_id="array.disclosed.original-schedule")
    recipe = records.original_schedule_recipe(source.coordinate, source.policy.cutoff_tick,
        recipe_id="recipe.disclosed.original-schedule", effort_unit="coupling-path-length")
    prepared_source = records.MatrixPreparationSource("source.disclosed.original-schedule", ScheduledPublicSource.from_source(source),
        source.root, initial, recipe, source.provenance, source.numerical_design)
    return prepared_source, raw


@pytest.mark.parametrize("family", original.FOUR_FAMILY_PREPARATION_IDS)
def test_original_schedule_matches_every_original_paired_state_with_supplied_noise(transfer, monkeypatch, family):  # noqa: F811
    source = source_for_family(transfer, family)
    subject, initial_raw = prepared_original(source)
    forbid_contact(monkeypatch)
    coarse, bridge = supplied_innovations(subject.total_ticks)
    actual = prepared.propagate_preparation(subject, initial_raw, coarse_innovations=coarse, bridge_innovations=bridge)
    expected = original_prefix(source.coordinate, subject.total_ticks, coarse, bridge)
    assert set(actual) == set(expected)
    for name in expected:
        assert (actual[name].dtype.str, actual[name].shape, actual[name].tobytes()) == (
            expected[name].dtype.str, expected[name].shape, expected[name].tobytes()), name
    assert subject.recipe.kind == "ORIGINAL_SCHEDULE_BASELINE" and records.is_baseline_recipe(subject.recipe)
    assert subject.recipe.SCHEMA != records.MatrixCouplingRecipe.SCHEMA
    assert subject.recipe.effort == records.exact_decimal(sum((abs(Fraction(y) - Fraction(x))
        for before, after in zip(subject.recipe.half_tick_couplings, subject.recipe.half_tick_couplings[1:])
        for x, y in zip(before, after, strict=True)), Fraction(0)))
    assert decode_canonical_bytes(subject.canonical_bytes(), records.MatrixPreparationSource, maximum_bytes=None) == subject
    raw, operand = prepared.preparation_array_product(subject, initial_raw, actual, artifact_id="array.disclosed.parity")
    assert operand.recipe == subject.recipe.identity
    assert prepared.consume_preparation_arrays(subject, initial_raw, operand, raw)["fine_positions"].tobytes() == expected["fine_positions"].tobytes()


def test_full_schedule_not_just_endpoints_and_preparation_stream_clock_are_required(transfer):  # noqa: F811
    original_source = transfer.sources.closure.original(transfer.sources.closure.descriptors[0],
        index=transfer.sources.closure.source_index())
    subject, _ = prepared_original(original_source)
    couplings = subject.recipe.half_tick_couplings
    changed = replace(subject.recipe, half_tick_couplings=(couplings[0],
        (couplings[1][0] + Decimal(".125"), couplings[1][1]), *couplings[2:]))
    assert changed.half_tick_couplings[0] == couplings[0] and changed.half_tick_couplings[-1] == couplings[-1]
    with pytest.raises(ValueError, match="original half tick"):
        replace(subject, recipe=changed)
    with pytest.raises(ValueError, match="preparation-stream ramp"):
        records.original_schedule_recipe(subject.coordinate, subject.coordinate.ramp_ticks + 1,
            recipe_id="recipe.invalid.autonomous-stream", effort_unit=subject.recipe.effort_unit)
    with pytest.raises(ValueError, match="endpoint clock"):
        records.validate_original_schedule_recipe(subject.recipe, subject.coordinate, subject.total_ticks - 1)
    with pytest.raises(ValueError, match="clock/root"):
        replace(subject.initial, cutoff=replace(subject.initial.cutoff, clock_id="clock.foreign"))
    public = MatrixPreparedPublicSource.from_source(subject)
    with pytest.raises(ValueError): replace(public, recipe=replace(public.recipe, object_version="99.0.0"))


def test_original_transfer_keeps_both_actual_regimes_initials_and_nonzero_baseline_effort(transfer):  # noqa: F811
    closure = transfer.sources.closure
    index = closure.source_index()
    states = []
    recipes = {}
    for descriptor in closure.descriptors:
        source = closure.original(descriptor, index=index)
        subject, _ = prepared_original(source)
        states.append((descriptor.root_id, subject.initial))
        recipes[descriptor.coordinate] = subject.recipe
    derived = replace(closure, initial_states=tuple(sorted(states)))
    sources = MatrixReservedTransferSources("sources.disclosed.original-schedule", derived,
        tuple(sorted(recipes.items(), key=lambda row: row[0].object_id)), "hold")
    rows = sources.source_arms()
    assert len(rows) == len(closure.descriptors) == 2
    assert len({source.root.root.regime_id for _, source in rows}) == 2
    assert all(source.initial.alpha_tilde == (Decimal(8), Decimal(8)) and source.recipe.effort > 0 for _, source in rows)
    assert all(source.original.reservation == scheduled_identity(closure.reservation) for _, source in rows)
    assert all(source.root == closure.original(descriptor, index=index).root
        for descriptor in closure.descriptors for _, source in rows if source.root.root.root_id == descriptor.root_id)


def test_public_selected_baseline_successor_and_declarative_roles_keep_explicit_edition():
    design = selected_design("E6_TRANSFER")
    coordinate = design.sources[0][1].original.coordinate
    baseline = records.original_schedule_recipe(coordinate, coordinate.ramp_ticks,
        recipe_id="recipe.disclosed.selected-original-schedule", effort_unit=design.arms[0][1].effort_unit)
    updated = replace(design, arms=(("hold", baseline),), sources=tuple((arm, replace(public, recipe=baseline.identity))
        for arm, public in design.sources), interpretations=(replace(design.interpretations[0], recipe=baseline.identity),))
    assert len(updated.sources) == 2
    assert decode_canonical_bytes(updated.canonical_bytes(), type(updated), maximum_bytes=None) == updated
    criterion_record = replace(criterion(1), effort_unit=baseline.effort_unit)
    specification = SelectedPreparedProtectedSpecification("specification.disclosed.original-schedule", "ORIGINAL_E3", "E6_TRANSFER",
        1, (("hold", baseline),), criterion_record, None, None,
        ("INTERPOLATION_WITHIN_ASSESSED_DOMAIN", "EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN"))
    assert records.is_baseline_recipe(specification.arms[0][1])
    bad = replace(baseline, half_tick_couplings=(baseline.half_tick_couplings[0],
        (Decimal(7), Decimal(7)), *baseline.half_tick_couplings[2:]))
    with pytest.raises(ValueError, match="original half tick"):
        replace(updated, arms=(("hold", bad),), sources=tuple((arm, replace(public, recipe=bad.identity))
            for arm, public in updated.sources), interpretations=(replace(updated.interpretations[0], recipe=bad.identity),))


def test_v1_hold_bytes_and_constant_interpretation_are_unchanged(transfer):  # noqa: F811
    for _, source in transfer.sources.source_arms():
        recipe = source.recipe
        before = recipe.canonical_bytes()
        assert type(recipe) is records.MatrixCouplingRecipe and recipe.kind == "HOLD"
        assert records.is_baseline_recipe(recipe) and recipe.effort == 0
        assert decode_canonical_bytes(before, records.MatrixCouplingRecipe, maximum_bytes=None).canonical_bytes() == before
        with pytest.raises(ValueError, match="hidden preparation intervention"):
            replace(recipe, half_tick_couplings=(recipe.half_tick_couplings[0], (Decimal(8), Decimal(8)), *recipe.half_tick_couplings[2:]))
        with pytest.raises(ValueError):
            records.MatrixOriginalScheduleRecipe(recipe.recipe_id, "HOLD", recipe.primary_steps,
                recipe.half_tick_couplings, recipe.effort_rule, recipe.effort_unit)


def test_revision_point_can_retain_original_schedule_nonuse_without_changing_recipe_edition():
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4PointModels, SelectedE4RevisionPoint
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import MatrixPreparedCausalPrefix
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
    public = selected_design("E6_TRANSFER").sources[0][1]
    coordinate = public.original.coordinate
    recipe = records.original_schedule_recipe(coordinate, coordinate.ramp_ticks,
        recipe_id="recipe.disclosed.revision-original-schedule", effort_unit="coupling-path-length")
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4DownstreamNomination
    pin = lambda name, schema, version="1.0.0": ObjectIdentity(name, schema, version, "a" * 64)
    point = SelectedE4RevisionPoint("point.disclosed.original-schedule",
        pin("nomination.disclosed", SelectedE4DownstreamNomination.SCHEMA, SelectedE4DownstreamNomination.VERSION),
        pin("models.disclosed", SelectedE4PointModels.SCHEMA, SelectedE4PointModels.VERSION), None, public.source, recipe.identity,
        ObjectIdentity.from_record(coordinate.coordinate_id, coordinate), pin("causal.disclosed", MatrixPreparedCausalPrefix.SCHEMA),
        InformationCutoff("cutoff." + public.source.object_id, coordinate.clock_id, CausalPhase.PRE_ACTION,
            coordinate.physical_time(recipe.primary_steps)), None, "UNEVALUABLE", (None,) * 30, (None,) * 30)
    assert decode_canonical_bytes(point.canonical_bytes(), SelectedE4RevisionPoint, maximum_bytes=None) == point
    assert point.recipe == recipe.identity and point.uncertainty_status == "POINT_ONLY_DOWNSTREAM_UNCERTAINTY_UNEVALUABLE"
    with pytest.raises(ValueError, match="recipe edition"):
        replace(point, recipe=replace(recipe.identity, object_version="99.0.0"))
