# SPDX-License-Identifier: MPL-2.0
"""Selected E4 scientific/software controls over disclosed fixture operands.

No fixture establishes native acquisition, fresh units, qualification or grants.
The parent admission tests independently refuse these unpublished observations.
"""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256
from itertools import product
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_choices as scientific_choices
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import METHODS
from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_selection as original
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as r, selected_e3_e4_science as development
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as p, selected_e4_methods as method
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as owner, selected_e4_revision_preparation as public
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore, ScheduledResponseLossCell
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selection_specification import RevisionCandidateSelection
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.experimental_selection import WholeUnitFold
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_selected_e4_fixtures import selected_e4_populations, selected_bridge, transfer  # noqa: F401
from tests.test_matrix_selected_e3_e4_bridge import campaign_fixture


def pin(name, schema, version="1.0.0"):
    return ObjectIdentity(name, schema, version, sha256(name.encode()).hexdigest())


def fixture_observations(programme, bank, *, revision=None):
    results, observations = [], []
    index=bank.source_index()
    protected = type(programme) is p.SelectedE4PhaseProgramme
    if protected:
        from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
    for case in programme.cases:
        source = bank.source(case.root_id,index=index)
        protocol, panels = bank.response_selection.validate_source(source)
        causal_pin = pin("prefix." + case.root_id,
            native.SelectedE4ProtectedCausalPrefix.SCHEMA if protected else r.SelectedE3E4CausalPrefix.SCHEMA)
        prefix = p.SelectedE4PrefixProjection("projection." + case.root_id, causal_pin, case.source, source.root.root,
            source.policy.cutoff_tick, "2" * 64, "AVAILABLE")
        forecast = pin("account." + case.root_id,
            native.SelectedE4ProtectedAccountSeal.SCHEMA if protected else r.SelectedE3E4AccountSeal.SCHEMA,
            native.SelectedE4ProtectedAccountSeal.VERSION if protected else r.SelectedE3E4AccountSeal.VERSION)
        cells, primary = [], None
        for view, panel, action, predictor, horizon in product(("PRIMARY", "FINE"), panels, protocol.actions, PREDICTORS, protocol.horizon_steps):
            temperature, friction, coupling = case.factor_values
            value = temperature**2 / 10 + friction / 10 + coupling / 10 + D(view == "FINE") / 8
            cells.append(ScheduledResponseLossCell(view, panel.panel_id, action.action_id, predictor, horizon,
                None, None, None, None, value))
            if view == "PRIMARY":
                with localcontext() as context:
                    context.prec = 50
                    primary = (1 + value).ln()
        control = ScheduledResponseTransitionControl("control.disclosed-selected-e4",
            "SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS", D(0), D(".01"), "SATISFIED", 1, 192, (D(0),), ())
        score = ScheduledResponseScore("score." + case.root_id, case.source, causal_pin, forecast,
            pin("physical." + case.root_id, "empirical-lawhood/matrix-scheduled-history/response-forecast"),
            pin("responses." + case.root_id, "empirical-lawhood/matrix-scheduled-history/native-responses"),
            case.root_id, case.independent_group_id, case.role, programme.criterion, (control,), True, "FINITE",
            tuple(sorted(cells, key=lambda row: row.key)), (primary,) * 15, ())
        projected = p.SelectedE4ScoreProjection.from_record(score, protocol, panels, record_id="projected-score." + case.root_id)
        points = tuple((name, (D(0),) * 15) for name in METHODS)
        if protected:
            revision_seal = None if revision is None or revision.models is None else revision.models.forecast(
                programme, case, record_id="revision." + case.root_id)
            result = native.SelectedE4NativeCaseResult(case.root_id, case.source, case.independent_group_id,
                "COMPLETED", "SATISFIED", "FINITE", projected.paired_log_targets, points, forecast, r.identity(score),
                None, (), r.SelectedE3E4CaseResult.unentered(case).native,
                ("disclosed-statistical-fixture-no-native-authority",), prefix, projected, revision_seal, source.coordinate)
        else:
            result = replace(r.SelectedE3E4CaseResult.unentered(case), disposition="COMPLETED", numerical_disposition="SATISFIED",
                score_disposition="FINITE", paired_log_targets=projected.paired_log_targets, original_log_points=points,
                forecast=forecast, score=r.identity(score), reason_codes=("disclosed-statistical-fixture-no-native-authority",))
        results.append(result)
        observations.append(p.SelectedE4ObservedCase(case.root_id, case.source, case.independent_group_id, source.coordinate,
            prefix, projected, result.disposition, result.numerical_disposition, result.forecast,
            getattr(result, "revision_forecast", None), points))
    reduction = (native.SelectedE4NativeReduction("reduction.disclosed-selected-e4." + programme.mode.lower(),
        programme.identity, bank.identity, tuple(results), programme.group_ids, None) if protected else
        development.reduce_cases(programme, tuple(results), record_id="reduction.disclosed-selected-e4"))
    data = p.SelectedE4ObservedData("data.disclosed-selected-e4." + programme.mode.lower(), programme.identity, reduction.identity, tuple(observations))
    return reduction, data


def declaration(programme, *, threshold=D(".1")):
    target = original.ScheduledRevisionTarget("target.disclosed-selected-e4", programme.criterion, (16, 64, 128),
        ("PRIMARY", "FINE"), "CUMULATIVE_LOG1P_NORMALIZED_RESPONSE_ERROR_ALL15")
    candidates = {}
    for role in ("revision", "baseline"):
        features = original.FEATURES if role == "revision" else tuple(sorted(original.PHYSICAL))
        candidates[role] = tuple(RevisionCandidateSelection(f"candidate.{role}.{index}",
            original.ScheduledRevisionTuning(f"tuning.{role}.{index}", original.FAMILY, features, penalty, False, len(features) + 1))
            for index, penalty in enumerate((D(1), D(10))))
    return method.SelectedE4RevisionExperimentSpecification("specification.disclosed-selected-e4", programme.identity,
        target, original.ScheduledRevisionTrigger("trigger.disclosed-selected-e4", "MEAN_COMPLETE_GROUP_MAX_PAIRED_LOG_ERROR",
            "GREATER_THAN", threshold),
        tuple(WholeUnitFold(group, index % 2) for index, group in enumerate(programme.group_ids)), 2, 5,
        candidates["revision"], candidates["baseline"], tuple(row.candidate_id for row in candidates["revision"]),
        tuple(row.candidate_id for row in candidates["baseline"]))


@pytest.fixture(scope="module")
def selected_revision(selected_e4_populations):  # noqa: F811
    f = selected_e4_populations
    reduction, data = fixture_observations(f.development, f.development_bank)
    editable = declaration(f.development)
    specification = method.derive_revision_specification(editable, f.development)
    nomination = method.select_revision(specification, f.development, f.development_bank, reduction, data,
        nomination_id="nomination.disclosed-selected-e4")
    frozen = method.freeze_revision(f.development, nomination, freeze_id="freeze.disclosed-selected-e4")
    return SimpleNamespace(populations=f, programme=f.development, bank=f.development_bank, reduction=reduction, data=data,
        editable=editable, specification=specification, nomination=nomination, frozen=frozen)


def test_actual_selected_fit_freeze_preserves_explicit_choices_and_full_denominators(selected_revision):
    f = selected_revision
    assert f.nomination.trigger_disposition == "TRIGGERED"
    assert f.nomination.endpoint_fit_calls == 300
    for model in (f.nomination.revision_model, f.nomination.baseline_model):
        assert model.training_groups == f.programme.group_ids
        assert all(row.training_rows == row.fitted_rows == 288 for row in model.parameters)
    assert f.nomination.revision_model.tuning.feature_names == original.FEATURES
    assert f.nomination.baseline_model.tuning.feature_names == tuple(sorted(original.PHYSICAL))
    assert f.frozen.revision.fitted_model == f.nomination.revision_model.identity
    assert f.frozen.baseline.fitted_model == f.nomination.baseline_model.identity
    for value in (f.specification, f.nomination, f.frozen):
        assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value


def test_independent_normal_equation_oracle_preserves_actual_standardization_and_penalty(selected_revision):
    f = selected_revision
    model = f.nomination.revision_model
    x = np.asarray([[float(original.revision_case_features(f.programme, case)[name]) for name in model.tuning.feature_names]
        for case in f.programme.cases])
    y = np.asarray([float(row.score.paired_log_targets[0]) for row in f.data.cases])
    means, scales = x.mean(axis=0), x.std(axis=0)
    scales[scales == 0] = 1
    z = np.column_stack((np.ones(len(x)), (x - means) / scales))
    penalty = np.eye(z.shape[1]) * float(model.tuning.penalty)
    penalty[0, 0] = 0
    expected = np.linalg.solve(z.T @ z + penalty, z.T @ y)
    actual = np.asarray([float(value) for value in model.parameters[0].coefficients])
    assert np.allclose(actual, expected, rtol=1e-11, atol=1e-12)


@pytest.mark.parametrize("branch", ("missing", "nontriggered"))
def test_adverse_or_untriggered_branch_retains_whole_groups_and_zero_fits(selected_revision, branch):
    f = selected_revision
    data, reduction = f.data, f.reduction
    specification = f.specification
    if branch == "missing":
        missing = r.SelectedE3E4CaseResult.unentered(f.programme.cases[0])
        reduction = development.reduce_cases(f.programme, (missing, *reduction.cases[1:]),
            record_id=reduction.record_id)
        first = data.cases[0]
        data = replace(data, reduction=reduction.identity, cases=(replace(first, causal_prefix=None, score=None,
            disposition=missing.disposition, numerical_disposition=missing.numerical_disposition,
            forecast=missing.forecast, original_log_points=missing.original_log_points), *data.cases[1:]))
    else:
        specification = method.derive_revision_specification(declaration(f.programme, threshold=D(999)), f.programme)
    nomination = method.select_revision(specification, f.programme, f.bank, reduction, data, nomination_id="nomination.adverse")
    assert nomination.trigger_disposition == ("UNEVALUABLE" if branch == "missing" else "NOT_TRIGGERED")
    assert nomination.endpoint_fit_calls == 0
    assert len(nomination.revision_selection.scores) == len(specification.revision_design.candidates) * len(f.programme.group_ids)
    frozen = method.freeze_revision(f.programme, nomination, freeze_id="freeze.adverse")
    export = p.SelectedE4RevisionExport.from_products(f.programme, nomination, frozen, record_id="export.adverse")
    assert export.models is None and export.decision.frozen_disposition == "UNENTERED"


def test_public_projection_is_compact_exact_and_excludes_raw_dev_and_cal_banks(selected_revision):
    f = selected_revision
    export = p.SelectedE4RevisionExport.from_products(f.programme, f.nomination, f.frozen, record_id="export.disclosed")
    assert export.models.revision_model == f.nomination.revision_model
    assert export.models.baseline_model == f.nomination.baseline_model
    assert export.decision.nomination == f.nomination.identity
    assert export.decision.frozen == f.frozen.identity
    assert b'"scores"' not in export.canonical_bytes()
    assert b'"cases"' not in export.canonical_bytes()
    assert len(export.canonical_bytes()) < len(f.data.canonical_bytes())
    assert decode_canonical_bytes(export.canonical_bytes(), type(export), maximum_bytes=None) == export


def test_real_selected_development_compiler_and_cold_budget_join(selected_revision):
    f = selected_revision
    acquisition = owner.SelectedE4DevelopmentAcquisition("acquisition.disclosed", "original/disclosed-native-dev", "run.disclosed",
        pin("plan.disclosed", "empirical-lawhood/runtime/development-execution-plan"),
        pin("receipt.disclosed", "empirical-lawhood/runtime/canonical-task-receipt"), False)
    resources = owner.SelectedE4MethodResources("resources.disclosed", tuple((name, ResourceBudget(1, 1024**3, 0, None, None, None))
        for name in ("revision-fit", "revision-freeze")))
    inputs = public.SelectedE4RevisionInputs(campaign_fixture()[0].campaign, f.programme, f.bank, acquisition, f.reduction, f.data, resources)
    draft, records = public.lower_development(f.editable, inputs)
    assert len(draft.operations) == 2
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave, validate_recursive_scientific_roots
    declarations = owner.operation_declarations()
    registry = CapabilityRegistry("registry.selected-e4.methods.disclosed", tuple(row.manifest() for row in declarations))
    registrations = tuple(row.registration() for row in declarations)
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
    registrations_by_node = {operation.node_id: next(row for row in registrations if row.selection == operation.selection)
        for operation in draft.operations}
    configs = tuple(decode_recursive_config_input(operation, registrations_by_node[operation.node_id]) for operation in draft.operations)
    validate_recursive_scientific_roots(root=draft.development_study, config_inputs=configs,
        registrations_for_node=registrations_by_node, requirements=(), connections=(), qualifications=(),
        known_design_inputs=(), links=draft.links, external_inputs=draft.external_inputs)
    compiled = compile_recursive_wave(draft=draft, registry=registry, registrations=registrations,
        implementation_commit="a" * 40, output_codecs={schema: kind for row in declarations for schema, kind in row.record_codecs.items()})
    assert len(compiled.execution_plan.tasks) == 2
    cold = decode_canonical_bytes(draft.canonical_bytes(), type(draft), maximum_bytes=None)
    assert cold == draft
    companions = tuple(sorted((getattr(value, public.ID_FIELDS[name]), value) for name, value in {
        "campaign": inputs.campaign, "programme": f.programme, "bank": f.bank, "acquisition": acquisition,
        "reduction": f.reduction, "data": f.data}.items()))
    public.validate_instance(specification=f.editable, allocation=method.selection_allocation(f.programme), draft=draft, source_records=companions)
    assert records
    first = draft.operations[0]
    with pytest.raises(ValueError, match="reservation"):
        public.validate_instance(specification=f.editable, allocation=method.selection_allocation(f.programme),
            draft=replace(draft, operations=(replace(first, resource_budget=ResourceBudget(1, 2 * 1024**3, 0, None, None, None)),
                *draft.operations[1:])), source_records=companions)


def test_observed_companion_alone_cannot_create_actual_native_source_custody(selected_revision):
    from empirical_lawhood.api.selected_e4_method_runtime import original_development_products
    with pytest.raises(TypeError, match="locator"):
        original_development_products(writer=None, locator=selected_revision.data, programme=selected_revision.programme,
            bank=selected_revision.bank, data_id="data.refused")


def test_paired_projection_has_complete_four_action_census_without_full_vectors(selected_revision):
    score = selected_revision.data.cases[0].score
    assert len(score.paired_log_targets) == 30
    assert b'"cells"' not in score.canonical_bytes()
    assert b'"observed_values"' not in score.canonical_bytes()
    assert score.original != score.identity


@pytest.fixture(scope="module")
def selected_calibrated(selected_revision):  # noqa: F811
    f = selected_revision
    populations = f.populations
    export = p.SelectedE4RevisionExport.from_products(f.programme, f.nomination, f.frozen, record_id="export.calibration")
    reduction, data = fixture_observations(populations.calibration, populations.calibration_bank, revision=export)
    forecasts = p.SelectedE4ForecastBank("forecasts.calibration", populations.calibration.identity,
        tuple(case.revision_seal for case in reduction.cases))
    specification = p.SelectedE4CalibrationSpecification("specification.calibration", f.programme.identity,
        populations.calibration.identity, f.nomination.identity, f.frozen.identity, D(".05"),
        "WHOLE_GROUP_MAX_POSITIVE_PAIRED_LOG_RESIDUAL_NINE_COORDINATES_ALL30")
    result = method.calibrate_revision_public(specification, export, populations.calibration, populations.calibration_bank,
        reduction, data, forecasts, record_id="calibration.selected-e4.disclosed")
    return SimpleNamespace(revision=f, export=export, programme=populations.calibration, bank=populations.calibration_bank,
        reduction=reduction, data=data, forecasts=forecasts, specification=specification, result=result)


def test_actual_selected64_calibration_maximizes_both_views_all30_and_nine_cases(selected_calibrated):
    from fractions import Fraction
    f = selected_calibrated
    scores = []
    for group in f.programme.group_ids:
        pairs = tuple((actual, predicted) for case, seal in zip(f.data.cases, f.forecasts.forecasts, strict=True)
            if case.group_id == group for actual, predicted in zip(case.score.paired_log_targets, seal.revision_predictions, strict=True))
        scores.append((group, max(Fraction(0), *(Fraction(actual) - Fraction(predicted) for actual, predicted in pairs))))
        assert len(pairs) == 9 * 30
    assert len(scores) == len(f.result.group_ids) == 64
    assert tuple((group, Fraction(score)) for group, score in f.result.revision_scores) == tuple(scores)
    assert f.result.rank == 62
    assert Fraction(f.result.revision_radius) == sorted(value for _, value in scores)[61]
    assert decode_canonical_bytes(f.result.canonical_bytes(), type(f.result), maximum_bytes=None) == f.result
    public_cal = p.SelectedE4PublicCalibration.from_calibration(f.result, record_id="public.calibration")
    assert b'"revision_scores"' not in public_cal.canonical_bytes()
    assert b'"baseline_scores"' not in public_cal.canonical_bytes()
    assert public_cal.original == f.result.identity
    assert decode_canonical_bytes(public_cal.canonical_bytes(), type(public_cal), maximum_bytes=None) == public_cal


@pytest.mark.parametrize("field", ("programme", "source"))
def test_selected_forecast_refuses_retired_programme_or_source_version(selected_calibrated, field):
    forecast = selected_calibrated.forecasts.forecasts[0]
    with pytest.raises(ValueError, match="exact versioned scientific operand"):
        replace(forecast, **{field: replace(getattr(forecast, field), object_version="1.0.0")})


def test_three_missing_calibration_groups_preserve64_denominator_and_unbounded_radius(selected_calibrated):
    f = selected_calibrated
    absent = set(f.programme.group_ids[:3])
    data = replace(f.data, cases=tuple(row for row in f.data.cases if row.group_id not in absent))
    result = method.calibrate_revision_public(f.specification, f.export, f.programme, f.bank, f.reduction, data, f.forecasts,
        record_id="calibration.missing-three")
    assert result.group_ids == f.programme.group_ids and result.rank == 62
    assert result.revision_radius is result.baseline_radius is None
    assert {group for group, score in result.revision_scores if score is None} == absent
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


@pytest.mark.parametrize("damage", ("forecast", "alpha", "source", "cutoff", "case-census"))
def test_selected_calibration_refuses_changed_original_phase_operands(selected_calibrated, damage):
    f = selected_calibrated
    specification, data, forecasts = f.specification, f.data, f.forecasts
    if damage == "alpha":
        specification = replace(specification, alpha=D(".1"))
    elif damage == "case-census":
        forecasts = replace(forecasts, forecasts=forecasts.forecasts[:-1])
    elif damage == "forecast":
        first = forecasts.forecasts[0]
        forecasts = replace(forecasts, forecasts=(replace(first, revision_predictions=(first.revision_predictions[0] + 1,
            *first.revision_predictions[1:])), *forecasts.forecasts[1:]))
    else:
        first = data.cases[0]
        prefix = replace(first.causal_prefix, source=pin("source.foreign", first.source.object_schema,
            first.source.object_version)) if damage == "source" else replace(
            first.causal_prefix, cutoff_tick=first.causal_prefix.cutoff_tick + 1)
        data = replace(data, cases=(replace(first, causal_prefix=prefix), *data.cases[1:]))
    with pytest.raises((ValueError, TypeError), match="alpha|forecast|source|cutoff|population"):
        method.calibrate_revision_public(specification, f.export, f.programme, f.bank, f.reduction, data, forecasts,
            record_id="calibration.refused")


def confirmation_products(calibrated, *, required=()):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial as factorial
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_workflow as workflow
    from empirical_lawhood.runtime.experimental_factorial import PairInteractionScale
    from empirical_lawhood.runtime.experimental_statistics import PairedMeanTAlternative
    f = calibrated.revision.populations
    reduction, data = fixture_observations(f.confirmation, f.confirmation_bank, revision=calibrated.export)
    forecasts = p.SelectedE4ForecastBank("forecasts.confirmation", f.confirmation.identity,
        tuple(case.revision_seal for case in reduction.cases))
    factorial_spec = method.SelectedE4FactorialSpecification("factorial.confirmation", f.confirmation.identity,
        calibrated.export.models.target, factorial.ENDPOINT, PairInteractionScale.SIGNED_MEAN_DIFFERENCE,
        tuple(factorial.ScheduledFactorialComparison(name, PairedMeanTAlternative.TWO_SIDED_POINT_NULL, D(0), None)
            for name in factorial.E4_COMPARISONS), D(".05"), factorial.PROCEDURE,
        factorial.mean_t_requirement("requirement.confirmation"), (), "REQUIRE_COMPLETE_ASSIGNED_WHOLE_GROUPS", factorial.FAMILY_IDS)
    factorial_result = method.assess_factorial(factorial_spec, f.confirmation, f.confirmation_bank, reduction, data,
        assessment_id="factorial-result.confirmation")
    rule = method.SelectedE4NominationRule("rule.confirmation.disclosed", ("REVISION", "ORIGINAL_E3"), D(0), 64, 0,
        D(100), tuple(required), workflow.ENDPOINT, 64, PairedMeanTAlternative.LESS)
    specification = method.SelectedE4ProgrammeSpecification("programme-specification.confirmation",
        f.development_bank.forecast_design.package.original_package, r.identity(f.development_bank.forecast_design.package.models),
        f.development.identity, f.calibration.identity, f.confirmation.identity, rule, factorial.FAMILY_IDS)
    public_cal = p.SelectedE4PublicCalibration.from_calibration(calibrated.result, record_id="public.calibration.for-confirmation")
    result = method.assess_confirmation_public(specification, f.confirmation, f.confirmation_bank, calibrated.export,
        public_cal, reduction, data, forecasts, factorial_result, record_id="confirmation.disclosed")
    return SimpleNamespace(result=result, specification=specification, rule=rule, public_calibration=public_cal,
        factorial=factorial_result, programme=f.confirmation, bank=f.confirmation_bank, reduction=reduction,
        data=data, forecasts=forecasts)


def test_actual_selected64_confirmation_reduces_all12_slots_without_inventing_e3_scope(selected_calibrated):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import FAMILY_IDS
    f = confirmation_products(selected_calibrated)
    assert len(f.result.groups) == 64 and len(f.result.factorial_assessment.groups) == 64
    assert tuple(row.comparison_id for row in f.result.family_slots) == FAMILY_IDS
    assert all(row.original_covered is None for row in f.result.groups)
    assert all(len(losses) == 3 for _, losses in f.result.original_point_losses)
    assert f.result.assumption_status == "NOT_AUTHENTICATED_BY_THIS_CALCULATION"
    assert decode_canonical_bytes(f.result.canonical_bytes(), type(f.result), maximum_bytes=None) == f.result
    nomination = method.nominate_downstream(f.specification, f.result, selected_calibrated.export,
        f.public_calibration, record_id="downstream.nomination.disclosed")
    assert nomination.selected == "REVISION"
    assert dict(nomination.dispositions) == {"ORIGINAL_E3": "UNEVALUABLE", "REVISION": "ELIGIBLE"}
    assert nomination.standing == "CONDITIONAL_COMPLETE_E4_PROGRAMME_NO_QUALIFICATION_OR_DOWNSTREAM_AUTHORITY"
    assert decode_canonical_bytes(nomination.canonical_bytes(), type(nomination), maximum_bytes=None) == nomination


def test_declared_unevaluable_required_comparison_prevents_nomination_without_dropping_cases(selected_calibrated):
    f = confirmation_products(selected_calibrated, required=("e4.revision-baseline",))
    nomination = method.nominate_downstream(f.specification, f.result, selected_calibrated.export,
        f.public_calibration, record_id="downstream.nomination.unevaluable")
    assert len(f.result.groups) == 64
    assert nomination.selected is None
    assert dict(nomination.dispositions)["REVISION"] == "UNEVALUABLE"


def test_bounded_revision_point_preserves_all30_predictions_and_explicit_unsupported_nonuse(selected_calibrated):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4PointModels
    models = selected_calibrated.export.models
    payload = SelectedE4PointModels.from_models(models, record_id="point-models.disclosed")
    f = selected_calibrated
    case = f.programme.cases[0]
    coordinate = f.bank.source(case.root_id,index=f.bank.source_index()).coordinate
    disposition, revision, baseline = payload.predict(coordinate)
    seal = models.forecast(f.programme, case, record_id="forecast.point-parity")
    assert disposition == "PREDICTED"
    assert (revision, baseline) == (seal.revision_predictions, seal.baseline_predictions)
    assert len(revision) == len(baseline) == 30
    assert b'"training_groups"' not in payload.canonical_bytes()
    assert b'"group_ids"' not in payload.canonical_bytes()
    assert b'"scores"' not in payload.canonical_bytes()
    changed = replace(coordinate, primary_view=replace(coordinate.primary_view, bath_temperature=D("2.5")),
        fine_view=replace(coordinate.fine_view, bath_temperature=D("2.5")))
    assert payload.predict(changed) == ("UNSUPPORTED_DECLARED_GRID", (None,) * 30, (None,) * 30)


def test_declared14_primary_family_replays_factorial_and_confirmation_without_changing_calibration(selected_calibrated):
    from empirical_lawhood.kernel.decoding import decode_canonical_record
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial as factorial
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as bindings
    f = confirmation_products(selected_calibrated)
    old = f.factorial.specification
    original = old.canonical_bytes()
    family = tuple(sorted((*factorial.FAMILY_IDS, "e1.recurrence-survival", "e2.utility")))
    amended = replace(old, family_ids=family)
    assessed = method.assess_factorial(amended, f.programme, f.bank, f.reduction, f.data,
        assessment_id="factorial-result.confirmation.family14")
    assert tuple(row.comparison_id for row in assessed.family_slots) == family
    assert all(row.p_value is None and row.conditional_disposition == "UNEVALUABLE"
        for row in assessed.family_slots if row.comparison_id in ("e1.recurrence-survival", "e2.utility"))
    old_slots = {row.comparison_id: row for row in f.factorial.family_slots}
    for row in assessed.family_slots:
        if row.p_value is not None:
            assert row.adjusted_p_value.fraction >= old_slots[row.comparison_id].adjusted_p_value.fraction
    assert decode_canonical_bytes(assessed.canonical_bytes(), type(assessed), maximum_bytes=None) == assessed
    specification = replace(f.specification, family_ids=family)
    result = method.assess_confirmation_public(specification, f.programme, f.bank, selected_calibrated.export,
        f.public_calibration, f.reduction, f.data, f.forecasts, assessed, record_id="confirmation.family14")
    assert tuple(row.comparison_id for row in result.family_slots) == family
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    assert selected_calibrated.result.specification.alpha == D(".05")
    assert old.canonical_bytes() == original and old.VERSION == amended.VERSION == "3.0.0"
    assert decode_canonical_bytes(amended.canonical_bytes(), type(old), maximum_bytes=None) == amended
    retired = old.to_document()
    retired["version"] = "1.0.0"
    retired["value"].pop("family_ids")
    with pytest.raises(ValueError, match="version"):
        decode_canonical_record(retired, type(old))
    declaration = next(row for row in bindings.operation_declarations() if row.capability_key.endswith(".factorial-assess"))
    assert tuple(kind for kind in declaration.input_record_types if kind.SCHEMA == old.SCHEMA) == (type(old),)
    choices = scientific_choices.SelectedE4FactorialChoices("choices.family14", amended.target, amended.endpoint,
        amended.pair_scale, amended.comparisons, amended.alpha, amended.procedure, amended.sampling_requirement,
        amended.assumption_references, amended.missing_policy, family)
    assert decode_canonical_bytes(choices.canonical_bytes(), type(choices), maximum_bytes=None) == choices
    assert choices.bind(old.programme).family_ids == family
    retired_choices = choices.to_document()
    retired_choices["version"] = "1.0.0"
    retired_choices["value"].pop("family_ids")
    with pytest.raises(ValueError, match="version"):
        decode_canonical_record(retired_choices, type(choices))
    with pytest.raises(ValueError, match="family"):
        method.assess_confirmation_public(f.specification, f.programme, f.bank, selected_calibrated.export,
            f.public_calibration, f.reduction, f.data, f.forecasts, assessed, record_id="confirmation.changed-family")
    with pytest.raises(ValueError, match="family"):
        replace(amended, family_ids=tuple(name for name in family if name != "e3.model"))
