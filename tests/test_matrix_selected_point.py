# SPDX-License-Identifier: MPL-2.0
"""Selected E5/E6 seedless point consumers with in-memory metadata only."""

from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_point as point
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixCouplingRecipe, MatrixPreparationInitialState, MatrixPreparationSource
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPublicSource, MatrixPreparedRecipeInterpretation
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import MatrixPreparedCausalPrefix
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1FactorRule
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import ScalarClosureSpec
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterFactorNumericalDesign, MatrixParameterScalarDefinition
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledPrefixPolicy, ScheduledSource
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.references import ArtifactIdentity
from tests.test_matrix_selected_package import package, reference


def selected_design(phase="E5_OPPORTUNITY", *, transfer_count=1):
    selected = package(transfer_count=transfer_count)
    path = Path(__file__).parents[1] / "programmes/foundations/emergent-structure/records/matrix-e2-e3-candidate/matrix.e3.deanneal.nominal.canonical.json"
    nominal = decode_canonical_bytes(path.read_bytes(), MatrixParameterCoordinate, maximum_bytes=None)
    scalar = MatrixParameterScalarDefinition("scalar.selected-point-control")
    scalar_ref = ArtifactIdentity(scalar.definition_id, "in-memory-software-control", scalar.SCHEMA,
        scalar.fingerprint(), "application/json", len(scalar.canonical_bytes()))
    rule = E1FactorRule("rule.selected-point-control", ("X", "Y"), tuple(range(0, 257, 16)), D(".001"), 0, 0,
        D(".05"), D(".05"), D(15), D(15), D(30), D("1e-10"), D("1e-20"), D(".5"),
        ScalarClosureSpec("scalar-rule.selected-point-control", scalar_ref, D(".30")))
    policy = ScheduledPrefixPolicy("policy.selected-point-control", 256, rule,
        MatrixParameterFactorNumericalDesign("numerical.selected-point-control", *((D("1e-9"),) * 6)),
        "Y", "FIXED_DECLARED_CUTOFF_CAUSALLY_ADMITTED_PRIMARY_FRAME")
    coupling = tuple(D(repr(float(value))) for value in nominal.couplings(256))
    hold = MatrixCouplingRecipe("recipe.selected-hold", "HOLD", 256, (coupling,) * 513,
        "HALF_TICK_COUPLING_TOTAL_VARIATION_L1", "coupling-path-length")
    recipes = {"hold": hold}
    if phase != "E6_TRANSFER":
        recipes["fixed-a"] = replace(hold, recipe_id="recipe.selected-fixed-a", kind="FIXED_COUPLING",
            half_tick_couplings=(coupling, (D(2), D(2)), *((coupling,) * 511)))
    if phase == "E5_OPPORTUNITY":
        recipes["fixed-b"] = replace(hold, recipe_id="recipe.selected-fixed-b", kind="FIXED_COUPLING",
            half_tick_couplings=(coupling, (D(3), D(3)), *((coupling,) * 511)))
    sources = []
    groups = tuple(sorted((*selected.allocation.unit_ids("transfer_nearby"), *selected.allocation.unit_ids("transfer_shifted")))) if phase == "E6_TRANSFER" else ("group.selected-fresh",)
    role = {"E5_OPPORTUNITY": MatrixProgrammeRole.DEVELOPMENT, "E5_CONFIRMATION": MatrixProgrammeRole.CONFIRMATION,
        "E6_TRANSFER": MatrixProgrammeRole.WITHHELD_TRANSFER}[phase]
    for index, group in enumerate(groups):
        coordinate = nominal
        regime = index
        if phase == "E6_TRANSFER":
            nearby = group in selected.allocation.unit_ids("transfer_nearby")
            name = "e6-nearby" if nearby else "e6-shifted"
            regime = 0 if nearby else 1
            coordinate = decode_canonical_bytes(path.with_name("matrix.e3.deanneal." + name + ".canonical.json").read_bytes(), MatrixParameterCoordinate, maximum_bytes=None)
        root = MatrixProgrammeRoot("root." + group, group, "regime.selected." + str(regime), coordinate.coordinate_id, role, coordinate.clock_id)
        original = ScheduledPublicSource(reference("source." + group, ScheduledSource), root, coordinate, policy,
            selected.prefit.original_allocation, selected.prefit.reservation)
        for arm, recipe in recipes.items():
            public = MatrixPreparedPublicSource(reference("prepared." + arm + "." + group, MatrixPreparationSource), original,
                recipe.identity, reference("initial." + group, MatrixPreparationInitialState))
            sources.append((arm, public))
    return point.MatrixSelectedPointDesign("design.selected-point-control", selected, phase, transfer_count if phase == "E6_TRANSFER" else 1, tuple(sorted(recipes.items())),
        tuple(sorted(sources, key=lambda row: row[1].source.object_id)), tuple(MatrixPreparedRecipeInterpretation(recipe.identity,
            "cc1.history.de-anneal", reference("premise." + arm, MatrixCouplingRecipe)) for arm, recipe in sorted(recipes.items(), key=lambda row: row[1].recipe_id)))


def feature(design, public):
    values = {name: D(".5") for name in point.FEATURES}
    values.update({"cutoff": D(".256"), "family-de-anneal": D(1), "family-x-first": D(0), "family-y-first": D(0)})
    return point.MatrixSelectedPreparedFeature("feature." + public.source.object_id, design.identity, public,
        reference("prefix." + public.source.object_id, MatrixPreparedCausalPrefix), "b" * 64, "AVAILABLE", tuple(sorted(values.items())))


@pytest.mark.parametrize("phase", point.DOWNSTREAM_PHASES)
def test_selected_design_consumes_actual_e3_points_without_old_model_or_applied_bound(phase):
    design = selected_design(phase)
    for _, public in design.sources:
        observed = feature(design, public)
        seal = point.forecast_selected_point(design, observed, record_id="forecast." + public.source.object_id)
        assert seal.package == design.package.identity
        assert seal.original_calibration == point.identity(design.package.calibration)
        assert seal.uncertainty_status == point.POINT_ONLY
        assert dict(seal.log_points)["SPECTRAL_RIDGE"] == (D(0), D(2), D(2)) * 5
        assert decode_canonical_bytes(seal.canonical_bytes(), type(seal), maximum_bytes=None) == seal
        assert all(word not in design.canonical_bytes().decode() for word in ("effective_seed", "generator_state", '"streams"'))


@pytest.mark.parametrize("damage", ("missing-arm", "same-recipe", "initial", "selection", "role", "clock"))
def test_selected_preparation_preserves_whole_groups_actual_matching_and_original_science(damage):
    design = selected_design()
    with pytest.raises((ValueError, TypeError)):
        if damage == "missing-arm":
            replace(design, sources=design.sources[:-1])
        elif damage == "same-recipe":
            replace(design, arms=tuple((arm, design.arms[0][1]) for arm, _ in design.arms))
        elif damage == "initial":
            arm, public = design.sources[0]
            replace(design, sources=((arm, replace(public, initial=reference("initial.changed", MatrixPreparationInitialState))), *design.sources[1:]))
        elif damage == "selection":
            replace(design, package=replace(design.package, selection_unit_ids=tuple(sorted((*design.package.selection_unit_ids, "group.selected-fresh")))))
        elif damage == "role":
            arm, public = design.sources[0]
            replace(design, sources=((arm, replace(public, original=replace(public.original,
                root=replace(public.original.root, role=MatrixProgrammeRole.CALIBRATION)))), *design.sources[1:]))
        else:
            arm, public = design.sources[0]
            coordinate = public.original.coordinate
            changed = replace(coordinate, primary_view=replace(coordinate.primary_view, timestep=D(".002")))
            replace(design, sources=((arm, replace(public, original=replace(public.original, coordinate=changed))), *design.sources[1:]))


def test_selected_transfer_retains_both_reserves_and_does_not_accept_renamed_original():
    design = selected_design("E6_TRANSFER")
    assert len(design.sources) == 2 and len({public.original.root.regime_id for _, public in design.sources}) == 2
    with pytest.raises(ValueError, match="regimes"):
        replace(design, sources=design.sources[:1])
    arm, public = design.sources[0]
    with pytest.raises(ValueError, match="regimes"):
        replace(design, sources=((arm, replace(public, original=replace(public.original,
            reservation=replace(public.original.reservation, object_id="renamed.actual-reserve")))), *design.sources[1:]))


def test_unavailable_selected_observation_retains_all_endpoints_and_rejects_family_substitution():
    design = selected_design()
    observed = feature(design, design.sources[0][1])
    absent = replace(observed, disposition="NO_CAUSAL_ORIGIN", values=(), frame_sha256=None)
    seal = point.forecast_selected_point(design, absent, record_id="forecast.no-origin")
    assert all(values == (None,) * 15 for _, values in seal.log_points)
    wrong = replace(observed, values=tuple((name, D(0)) if name == "family-de-anneal" else (name, value) for name, value in observed.values))
    with pytest.raises(ValueError, match="interpretation"):
        point.forecast_selected_point(design, wrong, record_id="forecast.wrong-family")


def literal_unavailable_measurement(phase="E5_OPPORTUNITY"):
    import numpy as np
    from hashlib import sha256
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationArrays, MatrixPreparationAssessment
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import MatrixPreparedFactorWitness, MatrixPreparedFrameAssessment, MatrixPreparedPrefixArrays
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorObservation
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import lifetime
    from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import METHODS, MatrixParameterFactorControl
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledPrefixTrace, identity
    from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA

    design = selected_design(phase)
    public = design.sources[0][1]
    policy, coordinate = public.original.policy, public.original.coordinate
    observations = tuple(FactorObservation(tick, "UNAVAILABLE", None, None, None, None, None, None, None, None, None,
        False, "UNAVAILABLE") for tick in policy.factor_rule.lattice)
    traces = tuple(ScheduledPrefixTrace(policy.factor_rule.identity, view, sector, observations,
        lifetime(observations, policy.factor_rule), lifetime(observations, policy.factor_rule, origin_fixed=True))
        for view in ("PRIMARY", "FINE") for sector in ("X", "Y"))
    diagnostics = {}
    shapes = {"spectrum": (15,), "projector": (15, 15), "basis": (15, 3), "factor": (3, 4, 4), "aligned_factor": (3, 4, 4)}
    for trace in traces:
        stem = trace.view.lower() + "_" + trace.sector.lower() + "_"
        diagnostics[stem + "ticks"] = np.asarray(policy.factor_rule.lattice, dtype="<i8")
        for name in ("available", "identifiable"):
            diagnostics[stem + name] = np.zeros(len(observations), dtype="|b1")
        for name, shape in shapes.items():
            diagnostics[stem + name] = np.full((len(observations), *shape), np.nan, dtype="<c16" if "factor" in name else "<f8")
    prep = reference("preparation.literal-selected-point", MatrixPreparationArrays)
    numerical = reference("numerical.literal-selected-point", MatrixPreparationAssessment)
    def operand(name, role, arrays, producers):
        raw, members = encode_matrix_arrays(arrays, nonfinite_members=tuple(sorted(key for key, values in arrays.items() if not np.isfinite(values).all())))
        artifact = ArtifactIdentity(name, "literal-in-memory-arrays", MATRIX_ARRAY_SCHEMA,
            sha256(raw).hexdigest(), "application/x-npz", len(raw))
        return raw, MatrixPreparedPrefixArrays(name, public.source, role, artifact, members,
            tuple(sorted(producers, key=lambda row: row.object_id)))
    diagnostic_raw, diagnostic = operand("arrays.literal-selected-diagnostics", "DIAGNOSTICS", diagnostics,
        (public.source, prep, numerical))
    witness = MatrixPreparedFactorWitness("witness.literal-selected-point", public.source, prep, numerical,
        identity(policy), traces, diagnostic)
    controls = tuple(MatrixParameterFactorControl(method, (None,), D("1e-9"), 1, "UNASSESSED", (True,)) for method in METHODS)
    frames = MatrixPreparedFrameAssessment("frames.literal-selected-point", public.source, point.identity(witness),
        identity(policy.factor_numerical_design), controls, False)
    arrays = {"frame": np.full((3, 4, 4), np.nan, dtype="<c16")}
    for view, count, refinement in (("primary", 257, 1), ("fine", 513, 2)):
        arrays[view + "_ticks"] = np.arange(count, dtype="<i8")
        arrays[view + "_alpha_tilde"] = np.asarray(tuple(coordinate.couplings(tick, refinement=refinement) for tick in range(count)), dtype="<f8")
        for name in ("positions", "momenta"):
            arrays[view + "_" + name] = np.zeros((count, 2, 3, 4, 4), dtype="<c16")
    causal_raw, causal_arrays = operand("arrays.literal-selected-causal", "CAUSAL_STATE", arrays,
        (public.source, prep, point.identity(witness), point.identity(frames)))
    causal = MatrixPreparedCausalPrefix("prefix.literal-selected-point", public.source, prep, numerical,
        point.identity(witness), point.identity(frames), identity(policy), 256, None, "UNEVALUABLE",
        "PREFIX_NUMERICAL_CONTROLS_NOT_SATISFIED", causal_arrays)
    return design, public, causal, witness, frames, causal_raw, diagnostic_raw


def test_literal_array_measurement_authenticates_bytes_and_preserves_unavailable_origin():
    design, public, causal, witness, frames, causal_raw, diagnostic_raw = literal_unavailable_measurement()
    measured = point.measure_selected_point(design, public, causal, witness, frames, causal_raw, diagnostic_raw,
        record_id="feature.literal-selected-arrays")
    assert measured.disposition == "UNAVAILABLE" and measured.values == ()
    assert measured.prefix == point.identity(causal) and measured.public_source == public
    sealed = point.forecast_selected_point(design, measured, record_id="forecast.literal-selected-arrays")
    assert all(values == (None,) * 15 for _, values in sealed.log_points)
    with pytest.raises(ValueError):
        point.measure_selected_point(design, public, causal, witness, frames, causal_raw, diagnostic_raw[:-1],
            record_id="feature.corrupt-selected-arrays")


def test_public_point_projection_preserves_exact_model_values_without_calibration_score_bank():
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPointPayload
    design = selected_design("E5_CONFIRMATION")
    payload = MatrixSelectedPointPayload.from_design(design)
    before = feature(design, design.sources[0][1])
    original = point.forecast_selected_point(design, before, record_id="point.original-projection-control")
    projected = point.forecast_selected_point(payload, replace(before, design=payload.identity), record_id="point.public-projection-control")
    assert projected.log_points == original.log_points
    assert (projected.package, projected.original_calibration) == (original.package, original.original_calibration)
    assert payload.package.models.canonical_bytes() == design.package.models.canonical_bytes()
    raw = payload.canonical_bytes()
    assert all(token not in raw for token in (b'"scores"', b'"forecasts"', b'"outcomes"', b'"streams"', b'"effective_seed"'))
    assert payload.identity != payload.original_design and payload.package.identity != payload.package.original_package
    assert decode_canonical_bytes(raw, MatrixSelectedPointPayload, maximum_bytes=None) == payload
    for values, disposition in ((before.values, "UNAVAILABLE"), ((), "UNDECLARED")):
        with pytest.raises(ValueError, match="explicit causal availability|complete original seedless causal features"):
            payload.package.predict(values=values, disposition=disposition)
