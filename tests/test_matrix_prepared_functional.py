# SPDX-License-Identifier: MPL-2.0
"""Literal endpoint controls, without native arrays, custody or qualification.

These isolate the guarded numerical reduction. They do not establish a complete
programme, a valid sampled group, source eligibility or response applicability.
"""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_functional as method
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixCouplingRecipe, MatrixPreparationArrays, MatrixPreparationInitialState, MatrixPreparationSource
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_composition import MatrixPreparedAssayProgramme
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_forecast import MatrixPreparedMechanicalForecast
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPointDesign, MatrixPreparedPointFeature, MatrixPreparedPointSeal
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import MatrixPreparedCausalPrefix
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_response_science import MatrixPreparedForecastArrays, MatrixPreparedResponsePanel, MatrixPreparedResponseReadout
from empirical_lawhood.adapters.methods.matrix_experimental_programme.records import PACKAGE_ROLES, MatrixFrozenConsumerPackage, MatrixProgrammeCase, MatrixProgrammeRoster
from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS, identity as model_identity
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_factor_response.response_population_statistics import STRATA
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledRoot
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseLossCell, branch_census
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from tests.test_matrix_later_programme import criterion
from tests.test_matrix_parameter_history import source as parameter_template
from tests.test_matrix_prepared_assay_method import literal_protocol


def reference(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, sha256(name.encode()).hexdigest())


@pytest.fixture
def endpoint():
    protocol, _ = literal_protocol()
    public = protocol.public_source
    parameter = parameter_template()
    target = tuple(D(str(value)) for value in public.coordinate.couplings(public.policy.cutoff_tick))
    initial = MatrixPreparationInitialState("state.literal-endpoint", reference("history.literal-endpoint", MatrixPreparationArrays),
        reference("assessment.literal-endpoint", MatrixPreparationArrays),
        ArtifactIdentity("array.literal-endpoint-initial", "literal-metadata-only", MATRIX_ARRAY_SCHEMA, "a" * 64, "application/x-npz", 1),
        tuple(MatrixArrayMember(name, "<c16", (2, 3, 4, 4), "b" * 64) for name in ("momenta", "positions")), target)
    recipe = MatrixCouplingRecipe("recipe.literal-endpoint", "HOLD", public.policy.cutoff_tick,
        (target,) * (2 * public.policy.cutoff_tick + 1), "HALF_TICK_COUPLING_TOTAL_VARIATION_L1", "effort.literal-endpoint")
    root = ScheduledRoot(public.root, ObjectIdentity.from_record(public.coordinate.coordinate_id, public.coordinate), parameter.root.streams)
    source = MatrixPreparationSource("source.literal-endpoint", public, root, initial, recipe, parameter.provenance, parameter.numerical_design)
    package = MatrixFrozenConsumerPackage("package.literal-endpoint", reference("freeze.literal-endpoint", MatrixFrozenConsumerPackage),
        tuple((role, protocol.criterion if role == "criterion" else reference("component.literal-endpoint." + role, MatrixFrozenConsumerPackage)) for role in PACKAGE_ROLES),
        public.reservation, ("group.original-training",), ("group.original-selection",), "OBSERVATION_ASSISTED_SEALED_BEFORE_FUTURE")
    assay = MatrixPreparedAssayMethod.from_protocol("method.literal-endpoint", protocol)
    case = MatrixProgrammeCase("case.literal-endpoint", "hold", recipe.identity, public, initial.array_artifact,
        source.duration, recipe.effort, ObjectIdentity.from_record(public.coordinate.coordinate_id, public.coordinate), assay.identity, ())
    specification = method.MatrixPreparedFunctionalSpecification("functional.literal-endpoint", "E5_OPPORTUNITY",
        reference("assay.literal-endpoint", MatrixPreparedAssayProgramme), assay.identity,
        reference("roster.literal-endpoint", MatrixProgrammeRoster), package.identity, ((case.case_id, source.identity),),
        replace(criterion(64), effort_unit=recipe.effort_unit), 1, ("hold", "recipe-a", "recipe-b"), "hold", None, 1, "LEXICAL_ARM_ID", (), ())
    causal = reference("causal.literal-endpoint", MatrixPreparedCausalPrefix)
    preparation = reference("preparation.literal-endpoint", MatrixPreparationArrays)
    feature = MatrixPreparedPointFeature("feature.literal-endpoint", source.identity, causal,
        reference("design.literal-endpoint", MatrixPreparedPointDesign), public.root.root_id, case.unit_id, STRATA[0], public.root.clock_id,
        source.duration, None, "AVAILABLE", tuple((name, D(0)) for name in FEATURES))
    point = MatrixPreparedPointSeal("point.literal-endpoint", feature, package.identity, package.component("model"), protocol.criterion,
        (D(".01"),) * 15, (D(".01"),) * 15, (None,) * 15, None)
    operand = MatrixPreparedForecastArrays("forecast.literal-endpoint", source.identity, preparation,
        ObjectIdentity.from_record(protocol.protocol_id, protocol),
        ArtifactIdentity("array.literal-endpoint-predictions", "literal-metadata-only", MATRIX_ARRAY_SCHEMA, "c" * 64, "application/x-npz", 1),
        (MatrixArrayMember("literal", "<f8", (1,), "d" * 64),))
    mechanical = MatrixPreparedMechanicalForecast("mechanical.literal-endpoint", source.identity, causal, operand.original_protocol,
        model_identity(protocol.mechanical_model), operand, "AVAILABLE",
        tuple((view, predictor, "AVAILABLE", None) for view in ("PRIMARY", "FINE") for predictor in PREDICTORS))
    panels = tuple(MatrixPreparedResponsePanel("panel.literal-endpoint." + label, case.unit_id, role,
        root.streams if role == "COMMON_NOISE_PANEL" else tuple(MatrixHistorySeed(purpose,
            sha256(("literal-endpoint-independent." + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES))
        for label, role in (("common", "COMMON_NOISE_PANEL"), ("independent", "INDEPENDENT_FUTURE")))
    cells = tuple(sorted((ScheduledResponseLossCell(view, panel.panel_id, action.action_id, predictor, horizon,
        (D(0),) * 48, (D(".01"),) * 48, (D(".01"),) * 48, (None,) * 48, D(".01"))
        for view in ("PRIMARY", "FINE") for panel in panels for action in protocol.actions for predictor in PREDICTORS
        for horizon in protocol.horizon_steps), key=lambda row: row.key))
    controls = tuple(ScheduledResponseTransitionControl("control.prepared." + source.source_id + "." + branch,
        "SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS", D(0), protocol.native_reference_tolerance, "SATISFIED",
        (1 if view == "PRIMARY" else 2) * 128, 192, (D(0),) * ((1 if view == "PRIMARY" else 2) * 128), ())
        for branch, view, *_ in branch_census(protocol, panels))
    with localcontext() as context:
        context.prec = 50
        cumulative = ((D(1) + D(".01")).ln(),) * 15
    readout = MatrixPreparedResponseReadout("readout.literal-endpoint", source.identity, preparation, operand.identity,
        operand.original_protocol, tuple(panel.identity for panel in panels), controls, cells, True, "FINITE", cumulative)
    observed = method.MatrixPreparedFunctionalObservation(case.case_id, point, mechanical, readout, None)
    return specification, package, case, source, protocol, panels, observed


def reduce_endpoint(endpoint, observed=None):
    specification, package, case, source, protocol, panels, original = endpoint
    return method.prepared_case_result(specification, package, case, source, original if observed is None else observed, protocol=protocol, panels=panels)


def test_literal_full_endpoint_preserves_unbounded_applicability_and_original_math(endpoint):
    result = reduce_endpoint(endpoint)
    assert result.disposition == "FINITE" and result.functional_reliable and result.actual_error == D(".01")
    assert result.error_upper is None and not result.conditional_admission and result.covered is None
    assert result.source_support == "UNESTABLISHED" and result.absolute_comparator_log_error is None
    with localcontext() as context:
        context.prec = 80
        assert result.absolute_forecast_log_error == abs((D(1) + D(".01")).ln() - D(".01"))
    specification, package, case, source, protocol, panels, _ = endpoint
    missing = method.prepared_case_result(specification, package, case, source, None, protocol=protocol, panels=panels)
    assert missing.disposition == "MISSING" and not missing.functional_reliable and missing.preparation_effort == source.recipe.effort


@pytest.mark.parametrize("damage", ("receiver", "panel", "control-steps", "control-branch", "cumulative", "protocol"))
def test_endpoint_refuses_original_denominator_or_subject_substitution(endpoint, damage):
    observed = endpoint[-1]
    score = observed.readout
    if damage == "receiver":
        first = score.cells[0]
        score = replace(score, cells=(replace(first, actual_odd_responses=first.actual_odd_responses[:-1]), *score.cells[1:]))
    elif damage == "panel":
        score = replace(score, panels=(replace(score.panels[0], object_id="panel.foreign-endpoint"), score.panels[1]))
    elif damage in ("control-steps", "control-branch"):
        first = score.controls[0]
        changed = replace(first, denominator_steps=1, measured_errors=(D(0),)) if damage == "control-steps" else replace(first, control_id=first.control_id + ".foreign")
        score = replace(score, controls=(changed, *score.controls[1:]))
    elif damage == "cumulative":
        score = replace(score, cumulative_log_errors=(D(0),) * 15)
    else:
        score = replace(score, original_protocol=replace(score.original_protocol, object_fingerprint="f" * 64))
    with pytest.raises(ValueError):
        reduce_endpoint(endpoint, replace(observed, readout=score))


def test_paired_discrepancy_and_failed_original_control_keep_unusable_case(endpoint):
    observed = endpoint[-1]
    first = observed.readout.cells[0]
    assert first.view == "FINE"
    damaged = replace(observed, readout=replace(observed.readout,
        cells=(replace(first, normalized_error=D(".02")), *observed.readout.cells[1:])))
    result = reduce_endpoint(endpoint, damaged)
    assert result.disposition == "UNEVALUABLE" and "PAIRED_VIEW_DISCREPANCY" in result.reasons
    control = observed.readout.controls[0]
    measured = (D(1), *control.measured_errors[1:])
    failed = replace(control, error=D(1), disposition="VIOLATED", measured_errors=measured, failed_steps=(1,))
    score = replace(observed.readout, controls=(failed, *observed.readout.controls[1:]), numerical_pass=False,
        disposition="NATIVE_CROSSCHECK_FAILED", cumulative_log_errors=(None,) * 15)
    result = reduce_endpoint(endpoint, replace(observed, readout=score))
    assert result.disposition == "UNEVALUABLE" and not result.functional_reliable and result.actual_error is None
