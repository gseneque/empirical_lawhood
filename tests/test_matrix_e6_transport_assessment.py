# SPDX-License-Identifier: MPL-2.0
"""Independent E6 arithmetic/adverse controls over disclosed literal records.

The small complete rosters, frozen model/calibration records and response cells
are synthetic software operands. They create no commitment custody, scientific
qualification, source access, native contact, response acquisition or new fit.
"""

from dataclasses import fields, replace
from decimal import Decimal as D, Rounded, localcontext
from fractions import Fraction
from inspect import signature
from math import comb
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import e6_transport_records as records
from empirical_lawhood.adapters.methods.matrix_experimental_programme import e6_transport_science as science
from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_package import ConfiguredMatrixSelectedFrozenPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_package import POINT_ONLY
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as e3
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import NativeTrainingFeatureBank, NativeTrainingOutcomeBank
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_specification as configured
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_inputs import ConfiguredProtectedE3PreFitJoin
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
from empirical_lawhood.adapters.methods.matrix_factor_response import e3_numerical_methods as original
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import FAMILY_IDS
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as scheduled_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import AvailabilitySpec
from empirical_lawhood.runtime.experimental_statistics import split_upper_calibration
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, lineage_parent_sort_key
from tests.test_matrix_selected_package import reference
from tests.test_matrix_selected_protected import transfer_case
from tests.test_matrix_selected_opportunity import literal_observations


def exposed_parent_census(programme):
    """Declare the already exposed literal model bodies for pure graph controls.

    These four record pins have no producing receipts or actual grant custody.
    The independent API/runtime census check would refuse them as real parents.
    """
    package = programme.point_design.package
    return tuple(sorted((ArtifactLineageParent(record if type(record) is ObjectIdentity else
        ObjectIdentity.from_record(record.record_id, record),
        VisibilityCeiling.OUTCOME_VISIBLE, OutcomeAccess.EVALUATION_REVEALED)
        for record in (package.models, package.model_freeze, package.calibration, package.calibrated_freeze)),
        key=lineage_parent_sort_key))


FRESH_FAMILY = tuple(sorted((*FAMILY_IDS, "e1.recurrence-survival", "e2.utility")))


def original_package(programme, *, missing=0):
    """Disclosed fresh-family metadata; use original freeze/join owners exactly."""
    package = programme.point_design.package
    old = package.specification
    measurement = configured.ConfiguredE3Measurement(**{field.name: getattr(old.measurement, field.name)
        for field in fields(old.measurement)}, target_contract='PAIRED15')
    assessment = configured.ConfiguredE3Assessment(improvement_margin=old.assessment.improvement_margin,
        null_success_numerator=1, null_success_denominator=2, alpha_numerator=1, alpha_denominator=280,
        minimum_usable_units=old.assessment.minimum_usable_units, comparison_ids=FRESH_FAMILY)
    nominal = decode_canonical_bytes((Path(__file__).parents[1] /
        "programmes/foundations/emergent-structure/records/matrix-e2-e3-candidate/matrix.e3.deanneal.nominal.canonical.json").read_bytes(),
        MatrixParameterCoordinate, maximum_bytes=None)
    role_coordinates = {role: coordinate_identity(nominal) for role in configured.POPULATION_ROLES}
    for _, public in programme.point_design.sources:
        role = "TRANSFER_NEARBY" if public.original.root.independent_group_id in package.allocation.unit_ids("transfer_nearby") else "TRANSFER_SHIFTED"
        role_coordinates[role] = coordinate_identity(public.original.coordinate)
    specification = ConfiguredProtectedE3Specification(old.specification_id+".configured", old.question,
        configured.ConfiguredE3Protocol("protocol.e6.disclosed", measurement), old.populations,
        tuple(configured.ConfiguredE3Estimator(**{field.name: getattr(row, field.name)
            for field in fields(configured.ConfiguredE3Estimator)}) for row in old.methods), assessment,
        old.calibration_alpha, tuple((role, role_coordinates[role]) for role in configured.POPULATION_ROLES),
        evidence_scope=old.evidence_scope, calibration_target_view=old.calibration_target_view)
    prefit = ConfiguredProtectedE3PreFitJoin(**{field.name: (specification.identity if field.name == "specification"
        else getattr(package.prefit, field.name)) for field in fields(ConfiguredProtectedE3PreFitJoin)})
    models = []
    for model in package.models.models:
        if model.method_key == "ALL_ORIGIN_RIDGE":
            parameters = tuple(replace(parameter, coefficients=(D((0, 3, 4)[index % 3]),
                *parameter.coefficients[1:])) for index, parameter in enumerate(model.ridge_parameters))
            model = replace(model, ridge_parameters=parameters)
        models.append(model)
    models = e3.ConfiguredProtectedE3ModelSet(package.models.record_id+".configured", specification.identity,
        package.allocation.identity, prefit.identity,
        reference(package.models.training_features.object_id + ".native-control", NativeTrainingFeatureBank),
        reference(package.models.training_outcomes.object_id + ".native-control", NativeTrainingOutcomeBank), tuple(models))
    frozen = e3.freeze_protected_e3(specification, package.allocation, models, record_id=package.model_freeze.record_id)
    scores = tuple((unit, None, ("MISSING_POINT_OR_TARGET",)) if index < missing else row
        for index, row in enumerate(package.calibration.scores) for unit in (row[0],))
    calibration = e3.ConfiguredProtectedE3Calibration(package.calibration.record_id+".configured", specification.identity,
        package.allocation.identity, e3.identity(models), e3.identity(frozen), scores, package.calibration.rank,
        None if missing else package.calibration.radius,
        tuple(reference(row.object_id+".configured", e3.ConfiguredProtectedE3Forecast) for row in package.calibration.forecasts),
        tuple(reference(row.object_id+".configured", e3.ConfiguredProtectedE3PairedOutcome) for row in package.calibration.outcomes))
    calibrated = e3.freeze_protected_e3(specification, package.allocation, models,
        record_id=package.calibrated_freeze.record_id, model_freeze=frozen, calibration=calibration)
    return ConfiguredMatrixSelectedFrozenPackage(package.record_id+".configured", specification,
        package.allocation, prefit, models, frozen, calibration, calibrated, package.selection_unit_ids)


def fixture_case(*, error_maximum=D(10), missing_calibration=0, groups_per_regime=2):
    programme = transfer_case(groups_per_regime=groups_per_regime)
    package = original_package(programme, missing=missing_calibration)
    programme = replace(programme, point_design=replace(programme.point_design, package=package),
        criterion=replace(programme.criterion, family_slots=FRESH_FAMILY, alpha_denominator=280,
            normalized_error_maximum=error_maximum))
    rows = []
    for _, source in programme.sources.source_arms():
        root = source.original.root
        role = "TRANSFER_NEARBY" if root.independent_group_id in package.allocation.unit_ids("transfer_nearby") else "TRANSFER_SHIFTED"
        rows.append((role, root.regime_id, root.root_id, root.independent_group_id, source.original.source))
    policy = records.MatrixE6EmpiricalTransportPolicy("policy.e6.disclosed", package.specification.identity,
        scheduled_identity(programme.sources.closure.reservation), tuple((role, reference("selection.e6.disclosed."+role.lower(),
            ScheduledResponseSelection)) for role in ("CALIBRATION", "EVALUATION", *records.TRANSFER_ROLES)),
        reference("availability.e6.disclosed", AvailabilitySpec), programme.criterion,
        tuple((description, horizon) for description in package.specification.measurement.descriptions
            for horizon in package.specification.measurement.horizons), package.specification.calibration_alpha,
        tuple(sorted(rows, key=lambda row: (row[0], row[2]))))
    projection = science.project_e6_frozen_calibration(policy, package, record_id="projection.e6.disclosed")
    observations = literal_observations(programme, hold_error=D(".01"))
    decisions = {case_id: decide(policy, projection, point) for case_id, (point, _, _) in observations.items()}
    return SimpleNamespace(programme=programme, policy=policy, projection=projection,
        observations=observations, decisions=decisions)


def decide(policy, projection, point):
    return science.decide_e6_transport(policy, projection, point, source=point.feature.public_source,
        record_id="decision."+point.record_id)


def assess(case, *, observations=None, decisions=None):
    return science.assess_e6_transport(case.programme, case.policy, case.projection,
        case.observations if observations is None else observations,
        case.decisions if decisions is None else decisions, result_id="assessment.e6.disclosed")


def with_cells(readout, cells, *, disposition=None):
    """Exact literal PRIMARY projection, independently assembled for a control."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
    cumulative = []
    for predictor in PREDICTORS:
        for horizon in (16, 64, 128):
            values = tuple(row.normalized_error for row in cells
                if row.view == "PRIMARY" and row.predictor == predictor and row.horizon_tick <= horizon)
            with localcontext() as context:
                context.prec = 50
                cumulative.append(None if any(value is None for value in values) else (D(1)+max(values)).ln())
    return replace(readout, cells=cells, cumulative_log_errors=tuple(cumulative),
        **({} if disposition is None else {"disposition": disposition}))


@pytest.fixture(scope="module")
def finite():
    return fixture_case()


def test_frozen_upper_and_both_baselines_use_exact_original_points_without_refit(finite, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("E6 frozen projection/decision/assessment acquired, fit or drew")
    monkeypatch.setattr(np.random, "Generator", forbidden)
    monkeypatch.setattr(e3, "fit_protected_e3_models", forbidden)
    monkeypatch.setattr(original, "fit_estimator_values", forbidden)
    assert set(signature(science.decide_e6_transport).parameters) == {"policy", "projection", "point", "source", "record_id"}
    _, result = assess(finite)
    assert result.qualification == "NOT_ESTABLISHED"
    assert len(result.cases) == 4
    for case_id, (point, _, _) in finite.observations.items():
        before = point.canonical_bytes()
        decision = decide(finite.policy, finite.projection, point)
        assert decision == finite.decisions[case_id]
        assert not decision.original_support and decision.admission == "ADMIT"
        assert point.canonical_bytes() == before and point.uncertainty_status == POINT_ONLY
        assert len(decision.error_uppers) == len(finite.policy.endpoint_order) == 15
        with localcontext() as context:
            context.prec = 50
            expected = tuple((value+finite.projection.radius).exp()-D(1) for value in dict(point.log_points)["SPECTRAL_RIDGE"])
        assert decision.error_uppers == expected
        outcome = next(row for row in result.cases if row.case_id == case_id)
        assert outcome.joint_service and outcome.whole_menu_coverage == "COVERED"
        for index, endpoint in enumerate(outcome.endpoints):
            assert endpoint.primary_error == endpoint.fine_error == endpoint.paired_error == D(".01")
            assert tuple(row[0] for row in endpoint.comparisons) == records.METHODS
            for method, primary_absolute, primary_log, fine_absolute, fine_log in endpoint.comparisons:
                log_point = dict(point.log_points)[method][index]
                with localcontext() as context:
                    context.prec = 50
                    expected_absolute = abs(D(".01")-(log_point.exp()-D(1)))
                    expected_log = abs((D("1.01")).ln()-log_point)
                assert primary_absolute == fine_absolute == expected_absolute
                assert primary_log == fine_log == expected_log
        assert dict(point.log_points)["SPECTRAL_RIDGE"] != dict(point.log_points)["ALL_ORIGIN_RIDGE"]
        assert dict(point.log_points)["SPECTRAL_RIDGE"] != dict(point.log_points)["RAW_TRAIN_MEDIAN"]
        assert len(outcome.lifetimes) == 10
        assert all(row.last_definite_pass == 128 and row.first_definite_failure is None
            for row in outcome.lifetimes)
        assert all(dict(row.point_failure_horizons) == {"ALL_ORIGIN_RIDGE": 64,
            "RAW_TRAIN_MEDIAN": None, "SPECTRAL_RIDGE": None} for row in outcome.lifetimes)
        primary = outcome.endpoints[finite.policy.endpoint_order.index((finite.policy.criterion.predictor,
            finite.policy.criterion.horizon_tick))]
        errors = {method: (primary_absolute, fine_absolute) for method, primary_absolute, _, fine_absolute, _ in primary.comparisons}
        with localcontext() as context:
            context.prec = 50
            improvements = tuple((method, *(value-candidate for value, candidate in zip(errors[method],
                errors["SPECTRAL_RIDGE"], strict=True))) for method in records.METHODS[:2])
        assert outcome.primary_comparator_improvements == improvements
        assert outcome.beats_both_comparators is False
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


def test_coverage_reduces_every_menu_panel_action_view_and_preceding_horizon(finite):
    case_id, (point, mechanical, readout) = next(iter(finite.observations.items()))
    description = finite.policy.endpoint_order[0][0]
    cells = tuple(replace(row, normalized_error=D(".03")) if row.view == "FINE" and row.predictor == description
        and row.horizon_tick == 16 and row.panel_id == readout.cells[0].panel_id
        and row.action_id == readout.cells[0].action_id else row for row in readout.cells)
    observations = {**finite.observations, case_id: (point, mechanical, replace(readout, cells=cells))}
    _, result = assess(finite, observations=observations)
    row = next(row for row in result.cases if row.case_id == case_id)
    # A discrepancy is adverse at all later cumulative horizons; supplied
    # cumulative_log_errors remains unchanged and cannot conceal literal cells.
    assert all(endpoint.paired_error is None for endpoint in row.endpoints[:3])
    assert row.whole_menu_coverage == "UNAVAILABLE"
    both = tuple(replace(cell, normalized_error=D(".03")) if cell.predictor == description
        and cell.horizon_tick == 16 and cell.panel_id == readout.cells[0].panel_id
        and cell.action_id == readout.cells[0].action_id else cell for cell in readout.cells)
    with pytest.raises(ValueError, match="cumulative projection"):
        assess(finite, observations={**finite.observations, case_id: (point, mechanical, replace(readout, cells=both))})
    _, result = assess(finite, observations={**finite.observations, case_id: (point, mechanical, with_cells(readout, both))})
    row = next(row for row in result.cases if row.case_id == case_id)
    assert all(endpoint.primary_error == endpoint.fine_error == D(".03") for endpoint in row.endpoints[:3])
    assert row.endpoints[0].coverage == "UNCOVERED" and row.whole_menu_coverage == "UNCOVERED"
    assert all(endpoint.coverage == "COVERED" for endpoint in row.endpoints[3:])


def test_missing_decision_and_partial_future_keep_complete_adverse_root_counts(finite):
    first, second = tuple(finite.observations)[:2]
    missing_decision = {key: value for key, value in finite.decisions.items() if key != first}
    _, result = assess(finite, decisions=missing_decision)
    row = next(row for row in result.cases if row.case_id == first)
    assert row.admission == "MISSING_DECISION" and not row.delivered_service and not row.joint_service
    assert row.whole_menu_coverage == "UNAVAILABLE" and row.point is not None and row.readout is not None
    point, mechanical, _ = finite.observations[second]
    manifest, result = assess(finite, observations={**finite.observations, second: (point, mechanical, None)})
    row = next(row for row in result.cases if row.case_id == second)
    assert row.admission == "ADMIT" and row.outcome_disposition == "MISSING" and row.point == science.identity(point)
    assert row.false_admission_unresolved and not row.false_admission_known and not row.joint_service
    assert len(result.cases) == len(manifest.rows) == 4
    comparison = next(row for row in result.comparisons if second in {case.case_id for case in result.cases
        if case.unit_id in row.assigned_group_ids})
    assert len(comparison.assigned_group_ids) == 2 and comparison.successes == 1
    assert comparison.false_admissions_unresolved == 1 and not comparison.criterion_met_conditionally


@pytest.mark.parametrize("primary_error", (D(".01"), D(11)))
def test_partial_menu_preserves_known_primary_result_without_inventing_service(finite, primary_error):
    case_id, (point, mechanical, readout) = next(iter(finite.observations.items()))
    primary = finite.policy.criterion.predictor
    unresolved = next(description for description, _ in finite.policy.endpoint_order if description != primary)
    cells = tuple(replace(row, actual_odd_responses=None, signed_errors=None, absolute_errors=None,
        relative_errors=None, normalized_error=None) if row.predictor == unresolved else
        replace(row, signed_errors=(primary_error,)*48, absolute_errors=(primary_error,)*48,
            normalized_error=primary_error) if row.predictor == primary else row for row in readout.cells)
    changed = with_cells(readout, cells, disposition="PARTIAL")
    _, result = assess(finite, observations={**finite.observations, case_id: (point, mechanical, changed)})
    row = next(row for row in result.cases if row.case_id == case_id)
    assert row.outcome_disposition == "OBSERVATION_FAILED"
    assert row.whole_menu_coverage == ("UNCOVERED" if primary_error > finite.policy.criterion.normalized_error_maximum else "UNAVAILABLE")
    assert row.functional_reliable == (primary_error <= finite.policy.criterion.normalized_error_maximum)
    assert row.false_admission_known == (primary_error > finite.policy.criterion.normalized_error_maximum)
    assert not row.false_admission_unresolved and not row.delivered_service and not row.joint_service
    assert "PRIMARY_OBSERVED_WITH_INCOMPLETE_MENU" in row.reasons


def test_retained_mechanical_source_cannot_be_substituted_when_future_is_missing(finite):
    (case_id, (point, _, _)), (_, (_, foreign, _)) = tuple(finite.observations.items())[:2]
    with pytest.raises(ValueError, match="mechanical|source|ancestry"):
        assess(finite, observations={**finite.observations, case_id: (point, foreign, None)})


def test_known_nonuse_keeps_original_root_and_every_unentered_branch(finite):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import forecast_selected_point
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPointPayload
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
    case_id, (point, mechanical, readout) = next(iter(finite.observations.items()))
    feature = replace(point.feature, disposition="NO_CAUSAL_ORIGIN", frame_sha256=None, values=())
    point = forecast_selected_point(MatrixSelectedPointPayload.from_design(finite.programme.point_design),
        feature, record_id=point.record_id)
    decision = decide(finite.policy, finite.projection, point)
    source = next(source for _, source in finite.programme.sources.source_arms() if "case."+source.source_id == case_id)
    protocol, panels = finite.programme.protocol(source), dict(finite.programme.panels)[source.root.root.independent_group_id]
    cells = tuple(replace(row, actual_odd_responses=None, signed_errors=None, absolute_errors=None,
        relative_errors=None, normalized_error=None) for row in readout.cells)
    nonuse = replace(readout, forecast=None, controls=(), cells=cells, numerical_pass=False, disposition="NO_ORIGIN",
        cumulative_log_errors=(None,)*15, unentered_branch_ids=tuple(sorted(branch for branch, *_ in branch_census(protocol, panels))))
    mechanical = replace(mechanical, disposition="NO_ORIGIN",
        predictor_dispositions=tuple((view, predictor, "UNRESOLVED", "disclosed-no-causal-origin")
            for view, predictor, _, _ in mechanical.predictor_dispositions))
    _, result = assess(finite, observations={**finite.observations, case_id: (point, mechanical, nonuse)},
        decisions={**finite.decisions, case_id: decision})
    row = next(row for row in result.cases if row.case_id == case_id)
    assert row.admission == "ABSTAIN" and row.outcome_disposition == "NO_ORIGIN"
    assert not row.joint_service and not row.false_admission_known and not row.false_admission_unresolved
    assert row.whole_menu_coverage == "UNAVAILABLE" and len(nonuse.unentered_branch_ids) == 48
    assert all(value.first_nonuse == 16 for value in row.lifetimes)
    assert all(all(value == "KNOWN_NONUSE" for value in detection[1:])
        for endpoint in row.endpoints for detection in endpoint.failure_detection)
    assert sum(len(value.assigned_group_ids) for value in result.comparisons) == len(result.cases) == 4


def test_infinite_original_radius_is_vacuous_coverage_abstention_and_zero_service():
    case = fixture_case(missing_calibration=1)
    _, result = assess(case)
    assert case.projection.radius_kind == "INFINITE" and case.projection.radius is None
    assert len(case.projection.calibration_unit_ids) == 20 and case.projection.rank == 20
    assert all(row.admission == "ABSTAIN" and row.whole_menu_coverage == "VACUOUS"
        and row.functional_reliable and not row.joint_service for row in result.cases)
    assert all(row.error_uppers == (None,)*15 for row in case.decisions.values())
    assert all(row.successes == row.admitted_groups == 0 and row.vacuous_coverage_groups == 2
        and row.usable_groups == row.functional_successes == 2 for row in result.comparisons)


@pytest.mark.parametrize("damage", ("radius", "rank", "policy", "endpoint", "source", "panel", "criterion"))
def test_actual_consumers_reject_changed_frozen_scope_even_when_outer_records_are_resealed(finite, damage):
    case_id, (point, mechanical, readout) = next(iter(finite.observations.items()))
    with pytest.raises((ValueError, TypeError)):
        if damage in ("radius", "rank"):
            changed = replace(finite.projection, **({"radius": D(".018")} if damage == "radius" else {"rank": 19}))
            science.validate_e6_calibration_projection(changed, finite.policy, finite.programme.point_design.package)
        elif damage == "policy":
            science.validate_e6_public_calibration_projection(finite.projection,
                replace(finite.policy, availability=replace(finite.policy.availability, object_fingerprint="f"*64)),
                finite.programme.point_design.package)
        elif damage == "endpoint":
            science.validate_e6_public_calibration_projection(replace(finite.projection,
                endpoint_order=finite.projection.endpoint_order[:-1]), finite.policy, finite.programme.point_design.package)
        elif damage == "source":
            other = tuple(finite.observations.values())[1][0]
            science.decide_e6_transport(finite.policy, finite.projection, point, source=other.feature.public_source,
                record_id="decision.changed-source")
        elif damage == "panel":
            changed = replace(readout, panels=(replace(readout.panels[0], object_fingerprint="f"*64), *readout.panels[1:]))
            assess(finite, observations={**finite.observations, case_id: (point, mechanical, changed)})
        else:
            science.validate_e6_transport_scope(replace(finite.policy, criterion=replace(finite.policy.criterion,
                normalized_error_maximum=D(9))), finite.programme)


def test_frozen_fourteen_family_has_only_two_e6_slots_and_exact_n64_threshold(finite):
    _, result = assess(finite)
    assert result.criterion.family_slots == FRESH_FAMILY and len(FRESH_FAMILY) == 14
    assert result.criterion.alpha == Fraction(1, 280)
    assert tuple(row.comparison_id for row in result.comparisons) == ("e6.nearby", "e6.shifted")
    assert result.unused_family_slots == tuple(slot for slot in FRESH_FAMILY if slot not in ("e6.nearby", "e6.shifted"))
    tails = {k: Fraction(sum(comb(64, j) for j in range(k, 65)), 2**64) for k in (43, 44, 64)}
    assert tails[44] <= Fraction(1, 280) < tails[43]
    assert tails[44] == Fraction(34033913325232549, 18446744073709551616)
    assert tails[64] == Fraction(1, 2**64)
    assert all(not row.criterion_met_conditionally for row in result.comparisons)


def test_original_n64_calibration_keeps_rank62_and_missing_scores_in_whole_roster():
    finite = tuple(D(index)/D(100) for index in range(64))
    full = split_upper_calibration(finite, D(".05"))
    assert full.unit_count == 64 and full.rank == 62 and full.radius == D(".61")
    two_missing = split_upper_calibration((None, None, *finite[2:]), D(".05"))
    assert two_missing.unit_count == 64 and two_missing.rank == 62 and two_missing.radius == D(".63")
    three_missing = split_upper_calibration((None, None, None, *finite[3:]), D(".05"))
    assert three_missing.unit_count == 64 and three_missing.rank == 62 and three_missing.radius.is_infinite()


def test_expanded_contract_cache_repeats_cold_decimal_policy_refusals(finite):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as owner
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPublicProgramme
    public = MatrixSelectedPublicProgramme.from_programme(finite.programme)
    args = public, reference("evidence.e6.disclosed-cache", owner.MatrixSelectedEntryEvidenceV3), 1
    kwargs = {"transport_policy": finite.policy, "transport_calibration": finite.projection,
        "produced_input_parents": exposed_parent_census(public)}
    owner.contracts.cache_clear()
    assert owner.contracts(*args, **kwargs)[0]
    with localcontext() as context:
        context.prec = 1
        context.traps[Rounded] = True
        with pytest.raises(Rounded):
            owner.contracts.__wrapped__(*args, **kwargs)
        with pytest.raises(Rounded):
            owner.contracts(*args, **kwargs)
