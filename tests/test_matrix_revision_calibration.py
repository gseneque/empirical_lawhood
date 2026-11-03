# SPDX-License-Identifier: MPL-2.0
"""Whole-group E4 calibration with typed in-memory exposed controls only."""

from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_reduction as rr
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_selection as selection
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgrammeWave
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration import (
    SCORE_RULE, ScheduledRevisionCalibration, ScheduledRevisionCalibrationSpecification,
    calibrate_revision, forecast_revision_cases,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_programme_selection import exposed, _prefix, _score, pin  # noqa: F401


@pytest.fixture(scope="module")
def calibrated(exposed):  # noqa: F811 - imported module-scoped fixture
    development = exposed.programme
    nomination = selection.select_programme_revision(exposed.specification, development, exposed.reduction, exposed.data,
        nomination_id="nomination.calibration-control")
    frozen = selection.freeze_programme_revision(development, nomination, freeze_id="freeze.calibration-control")
    original_rows = {row.root_id: row for row in exposed.data.cases}
    original_results = {row.root_id: row for row in exposed.reduction.cases}
    cases, rows, results = [], [], []
    for repeat in range(2):
        for original in development.cases:
            root = f"root.calibration.{repeat}." + original.root_id
            source = pin("source." + root, original.source.object_schema, original.source.object_version)
            case = replace(original, root_id=root, independent_group_id=f"group.calibration.{repeat}." + original.independent_group_id,
                source=source,
                role="CALIBRATION", streams_sha256=pin("streams." + root.rsplit(".", 1)[0]).object_fingerprint,
                information_cutoff=replace(original.information_cutoff, cutoff_id="cutoff." + root))
            coordinate = original_rows[original.root_id].coordinate
            prefix = _prefix(case, coordinate)
            prefix = replace(prefix, root=replace(prefix.root, role=MatrixProgrammeRole.CALIBRATION))
            score = _score(case, prefix, development.criterion)
            cases.append(case)
            rows.append(selection.ScheduledRevisionCaseData(root, coordinate, prefix, score))
            results.append(replace(original_results[original.root_id], root_id=root, source=source,
                independent_group_id=case.independent_group_id, score=identity(score), forecast=score.error_forecast,
                cumulative_log_errors=score.cumulative_log_errors))
    groups = tuple(sorted({case.independent_group_id for case in cases}))
    waves = tuple(ScheduledProgrammeWave(f"wave.calibration.{i:02}", groups[i:i+4],
        tuple(case.root_id for case in cases if case.independent_group_id in groups[i:i+4])) for i in range(0, 64, 4))
    programme = replace(development, programme_id="programme.calibration-control", mode="E4_REVISION_CALIBRATION",
        bank=pin("bank.calibration-control", development.bank.object_schema, development.bank.object_version),
        allocation=pin("allocation.calibration-control", development.allocation.object_schema),
        cases=tuple(cases), source_census=tuple(sorted((case.source for case in cases), key=lambda value: value.object_id)),
        waves=waves, minimum_group_count=64)
    wave_results = tuple(rr.ScheduledProgrammeWaveResult(wave.wave_id + ".result", programme.identity, wave.wave_id,
        wave.group_ids, wave.root_ids, tuple(row for row in results if row.root_id in wave.root_ids)) for wave in waves)
    reduction = rr.reduce_programme(programme, wave_results, reduction_id="reduction.calibration-control", authenticate_wave=lambda row: None)
    data = selection.ScheduledRevisionDataBank("data.calibration-control", programme.identity,
        ObjectIdentity.from_record(reduction.reduction_id, reduction), tuple(rows))
    specification = ScheduledRevisionCalibrationSpecification("specification.calibration-control", development.identity,
        programme.identity, nomination.identity, frozen.identity, Decimal(".05"), SCORE_RULE)
    forecasts = forecast_revision_cases(development, nomination, frozen, programme, record_prefix="forecast.calibration-control")
    result = calibrate_revision(specification, development, nomination, frozen, programme, reduction, data, forecasts,
        record_id="calibration.control")
    return SimpleNamespace(development=development, nomination=nomination, frozen=frozen, programme=programme,
        reduction=reduction, data=data, specification=specification, forecasts=forecasts, result=result)


def _calibrate(case, **changes):
    selected = {name: getattr(case, name) for name in (
        "specification", "development", "nomination", "frozen", "programme", "reduction", "data", "forecasts")}
    selected.update(changes)
    return calibrate_revision(**selected, record_id="calibration.alternative")


def test_one_maximum_per_whole_group_covers_all_nine_coordinates_and_both_views(calibrated):
    case = calibrated
    assert len(case.forecasts) == 576 and len(case.result.group_ids) == 64
    assert case.result.rank == 62
    manual = {group: Fraction(0) for group in case.programme.group_ids}
    for declaration, forecast in zip(case.programme.cases, case.forecasts, strict=True):
        temperature, friction, coupling = declaration.factor_values
        # Independent literal equation for this fixture's original response cells.
        with localcontext() as context:
            context.prec = 50
            targets = tuple((1 + temperature**2 / 10 + friction / 10 + coupling / 10 + Decimal(view) / 8).ln()
                            for view in (0, 1))
        residual = max(Fraction(0), *(Fraction(target) - Fraction(point)
            for target, points in zip(targets, (forecast.revision_predictions[:15], forecast.revision_predictions[15:]), strict=True)
            for point in points))
        manual[declaration.independent_group_id] = max(manual[declaration.independent_group_id], residual)
    assert tuple((group, Fraction(score)) for group, score in case.result.revision_scores) == tuple(sorted(manual.items()))
    assert Fraction(case.result.revision_radius) == sorted(manual.values())[61]
    assert case.result.revision_model is case.nomination.revision_model
    assert case.result.baseline_model is case.nomination.baseline_model
    assert decode_canonical_bytes(case.result.canonical_bytes(), ScheduledRevisionCalibration,
        maximum_bytes=len(case.result.canonical_bytes())) == case.result


@pytest.mark.parametrize("field", ("programme", "source"))
def test_forecast_refuses_retired_programme_or_source_version(calibrated, field):
    forecast = calibrated.forecasts[0]
    with pytest.raises(ValueError, match="exact scientific input type"):
        replace(forecast, **{field: replace(getattr(forecast, field), object_version="1.0.0")})


def test_three_missing_groups_retain_canonical_unbounded_result_without_reducing_denominator(calibrated):
    absent = set(calibrated.programme.group_ids[:3])
    data = replace(calibrated.data, cases=tuple(row for row in calibrated.data.cases
        if row.causal_prefix.root.independent_group_id not in absent))
    result = _calibrate(calibrated, data=data)
    assert len(result.group_ids) == 64 and result.rank == 62
    assert result.revision_radius is result.baseline_radius is None
    assert {group for group, score in result.revision_scores if score is None} == absent
    assert decode_canonical_bytes(result.canonical_bytes(), ScheduledRevisionCalibration,
        maximum_bytes=len(result.canonical_bytes())) == result
    assert result.identity.object_fingerprint == result.fingerprint()


@pytest.mark.parametrize("radius", (Decimal("Infinity"), Decimal("NaN"), Decimal("-Infinity")))
def test_calibration_refuses_noncanonical_nonfinite_radius(calibrated, radius):
    with pytest.raises(ValueError, match="rank or bound"):
        replace(calibrated.result, revision_radius=radius)


@pytest.mark.parametrize("damage", ("prediction", "source", "cutoff", "omit", "order"))
def test_substituted_or_missing_forecast_seals_refuse(calibrated, damage):
    first, *rest = calibrated.forecasts
    if damage == "prediction":
        first = replace(first, revision_predictions=(first.revision_predictions[0] + 1, *first.revision_predictions[1:]))
    elif damage == "source":
        first = replace(first, source=pin("source.foreign", first.source.object_schema, first.source.object_version))
    elif damage == "cutoff":
        first = replace(first, cutoff=replace(first.cutoff, coordinate=first.cutoff.coordinate + 1))
    forecasts = tuple(rest) if damage == "omit" else tuple(reversed(calibrated.forecasts)) if damage == "order" else (first, *rest)
    with pytest.raises(ValueError, match="forecast|prediction"):
        _calibrate(calibrated, forecasts=forecasts)


def test_confirmation_cannot_be_used_as_calibration_and_alpha_is_explicit(calibrated):
    with pytest.raises(ValueError, match="phase"):
        _calibrate(calibrated, programme=calibrated.development)
    with pytest.raises(ValueError, match="confidence"):
        _calibrate(calibrated, specification=replace(calibrated.specification, alpha=Decimal(".1")))


def test_rank_or_bound_substitution_is_rejected_by_the_output_record(calibrated):
    for changes in ({"rank": 61}, {"revision_radius": calibrated.result.revision_radius + 1}):
        with pytest.raises(ValueError, match="rank or bound"):
            replace(calibrated.result, **changes)


@pytest.mark.parametrize("field", ("revision_scores", "baseline_scores", "forecasts"))
def test_calibration_cannot_hide_mutable_sequences_in_a_frozen_record(calibrated, field):
    with pytest.raises(ValueError):
        replace(calibrated.result, **{field: list(getattr(calibrated.result, field))})
    if field != "forecasts":
        values = getattr(calibrated.result, field)
        with pytest.raises(ValueError):
            replace(calibrated.result, **{field: (list(values[0]), *values[1:])})


def test_calibration_output_itself_refuses_training_overlap(calibrated):
    groups = calibrated.result.group_ids[:32]
    with pytest.raises(ValueError, match="fitted groups"):
        replace(calibrated.result,
            revision_model=replace(calibrated.result.revision_model, training_groups=groups),
            baseline_model=replace(calibrated.result.baseline_model, training_groups=groups))


def test_forecast_population_uses_one_shared_set_of_exact_model_and_programme_pins(calibrated):
    for field in ("programme", "frozen_models", "revision_model", "baseline_model", "target"):
        assert len({id(getattr(seal, field)) for seal in calibrated.forecasts}) == 1


@pytest.mark.parametrize("field", ("source", "coordinate", "target"))
def test_forecast_pin_types_are_checked_at_construction(calibrated, field):
    with pytest.raises(ValueError, match="scientific input type"):
        replace(calibrated.forecasts[0], **{field: pin("foreign." + field)})
