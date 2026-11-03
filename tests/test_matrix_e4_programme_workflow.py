# SPDX-License-Identifier: MPL-2.0
"""Pure exposed E4 phase/confirmation controls, without issue or execution."""

from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial as factorial
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_reduction as rr
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_selection as selection
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_workflow as workflow
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgrammeWave
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration import forecast_revision_cases
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_programme_factorial import _specification
from tests.test_matrix_revision_calibration import calibrated  # noqa: F401
from tests.test_matrix_programme_selection import exposed, _prefix, _score, pin  # noqa: F401


def rule(**changes):
    values = dict(rule_id="rule.e4.exposed", priority=("REVISION", "ORIGINAL_E3"),
        revision_baseline_null=Decimal(0), minimum_original_covered_groups=64,
        minimum_revision_covered_groups=64, maximum_revision_radius=Decimal(10),
        required_rejected_comparisons=(workflow.REVISION_COMPARISON,), endpoint=workflow.ENDPOINT)
    values.update(changes)
    return workflow.ScheduledE4NominationRule(**values)


@pytest.fixture(scope="module")
def complete(calibrated):  # noqa: F811
    original_rows = {row.root_id: row for row in calibrated.data.cases}
    original_results = {row.root_id: row for row in calibrated.reduction.cases}
    cases, rows, results = [], [], []
    for original in calibrated.programme.cases:
        root = original.root_id.replace("calibration", "confirmation")
        source = pin("source." + root, original.source.object_schema,original.source.object_version)
        case = replace(original, root_id=root, independent_group_id=original.independent_group_id.replace("calibration", "confirmation"),
            source=source,role="CONFIRMATION",
            streams_sha256=pin("streams." + root.rsplit(".", 1)[0]).object_fingerprint,
            information_cutoff=replace(original.information_cutoff, cutoff_id="cutoff." + root))
        coordinate = original_rows[original.root_id].coordinate
        prefix = _prefix(case, coordinate)
        prefix = replace(prefix, root=replace(prefix.root, role=MatrixProgrammeRole.CONFIRMATION))
        score = _score(case, prefix, calibrated.programme.criterion)
        cases.append(case)
        rows.append(selection.ScheduledRevisionCaseData(root, coordinate, prefix, score))
        results.append(replace(original_results[original.root_id], root_id=root, source=source,
            independent_group_id=case.independent_group_id, score=identity(score), forecast=score.error_forecast,
            cumulative_log_errors=score.cumulative_log_errors))
    groups = tuple(sorted({case.independent_group_id for case in cases}))
    waves = tuple(ScheduledProgrammeWave(f"wave.confirmation.{i:02}", groups[i:i+4],
        tuple(case.root_id for case in cases if case.independent_group_id in groups[i:i+4])) for i in range(0, 64, 4))
    programme = replace(calibrated.programme, programme_id="programme.confirmation-control", mode="E4_CONFIRMATION",
        bank=pin("bank.confirmation-control", calibrated.programme.bank.object_schema, calibrated.programme.bank.object_version),
        allocation=pin("allocation.confirmation-control", calibrated.programme.allocation.object_schema),
        cases=tuple(cases), source_census=tuple(sorted((case.source for case in cases), key=lambda value: value.object_id)), waves=waves)
    wave_results = tuple(rr.ScheduledProgrammeWaveResult(wave.wave_id + ".result", programme.identity, wave.wave_id,
        wave.group_ids, wave.root_ids, tuple(row for row in results if row.root_id in wave.root_ids)) for wave in waves)
    reduction = rr.reduce_programme(programme, wave_results, reduction_id="reduction.confirmation-control", authenticate_wave=lambda row: None)
    data = selection.ScheduledRevisionDataBank("data.confirmation-control", programme.identity,
        ObjectIdentity.from_record(reduction.reduction_id, reduction), tuple(rows))
    confirmation_context = SimpleNamespace(programme=programme, specification=calibrated.nomination.specification)
    factorial_spec = _specification(confirmation_context)
    assessment = factorial.assess_programme_factorial(factorial_spec, programme, reduction, data, assessment_id="factorial.confirmation-control")
    forecasts = forecast_revision_cases(calibrated.development, calibrated.nomination, calibrated.frozen, programme,
        record_prefix="forecast.confirmation-control")
    specification = workflow.ScheduledE4ProgrammeSpecification("specification.e4.control", pin("package.original-e3"), pin("model.original-e3"),
        calibrated.development.identity, calibrated.programme.identity, programme.identity, rule())
    return SimpleNamespace(prior=calibrated, programme=programme, reduction=reduction, data=data, factorial=assessment,
        forecasts=forecasts, specification=specification)


def assess(case, **changes):
    values = dict(specification=case.specification, development=case.prior.development,
        calibration_programme=case.prior.programme, programme=case.programme,
        nomination=case.prior.nomination, frozen=case.prior.frozen, calibration=case.prior.result,
        reduction=case.reduction, data=case.data, forecasts=case.forecasts, factorial=case.factorial,
        record_id="confirmation.e4.control")
    values.update(changes)
    return workflow.assess_e4_confirmation(**values)


def test_all_three_actual_populations_are_required_and_cal_conf_overlap_refuses(complete):
    case = complete
    case.specification.validate(case.prior.development, case.prior.programme, case.programme)
    with pytest.raises(ValueError, match="32DEV"):
        workflow.validate_e4_populations(case.prior.development, case.prior.programme, case.prior.programme)
    original = case.programme.cases[0]
    for attribute, replacement in (("source", case.prior.programme.cases[0].source),
            ("streams_sha256", case.prior.programme.cases[0].streams_sha256)):
        changed = tuple(replace(row, **{attribute: replacement}) if (
            row.root_id == original.root_id if attribute == "source" else row.independent_group_id == original.independent_group_id) else row
            for row in case.programme.cases)
        programme = replace(case.programme, cases=changed,
            source_census=tuple(sorted((row.source for row in changed), key=lambda value: value.object_id)))
        with pytest.raises(ValueError, match="reuse"):
            workflow.validate_e4_populations(case.prior.development, case.prior.programme, programme)


def test_readiness_is_derived_from_actual_products_and_future_skips_refuse(complete):
    case = complete
    args = (case.specification, case.prior.development, case.prior.programme, case.programme)
    assert workflow.e4_phase_readiness(*args).next_phase == "DEVELOPMENT"
    assert workflow.e4_phase_readiness(*args, nomination=case.prior.nomination).next_phase == "FREEZE"
    assert workflow.e4_phase_readiness(*args, nomination=case.prior.nomination, frozen=case.prior.frozen).next_phase == "CALIBRATION"
    assert workflow.e4_phase_readiness(*args, nomination=case.prior.nomination, frozen=case.prior.frozen,
        calibration=case.prior.result).next_phase == "CONFIRMATION"
    with pytest.raises(ValueError, match="precede"):
        workflow.e4_phase_readiness(*args, calibration=case.prior.result)
    with pytest.raises(ValueError, match="typed complete"):
        workflow.e4_phase_readiness(*args, confirmation=object())


def test_missing_rule_is_named_scientific_choice_without_defaults(complete):
    specification = replace(complete.specification, nomination_rule=None)
    dependency, = specification.scientific_dependencies
    assert dependency.kind.value == "SCIENTIFIC_EVIDENCE" and "SCIENTIFIC_CHOICE" in dependency.detail
    with pytest.raises(ValueError, match="SCIENTIFIC_CHOICE"):
        assess(complete, specification=specification)


def test_complete_confirmation_recomputes_whole_group_losses_and_preserves_all12_slots(complete):
    result = assess(complete)
    assert len(result.groups) == 64 and tuple(row.comparison_id for row in result.family_slots) == factorial.FAMILY_IDS
    targets, _ = selection.validate_programme_paired_data(complete.programme, complete.reduction, complete.data,
        complete.prior.nomination.specification.target, mode="E4_CONFIRMATION", missing_record_policy="ALLOW_ABSENT_DECLARED_ROWS")
    expected = max(abs(Fraction(actual) - Fraction(point))
        for row in complete.data.cases[:9] for actual, point in zip(
            targets[row.root_id],
            next(seal for seal in complete.forecasts if seal.case_id == row.root_id).revision_predictions, strict=True))
    assert Fraction(result.groups[0].revision_loss) == expected
    assert result.assumption_status == factorial.ASSUMPTION_STATUS
    assert all(row.p_value is None for row in result.family_slots if row.comparison_id in ("e3.model", "e5.preparation", "e6.nearby", "e6.shifted"))
    assert decode_canonical_bytes(result.canonical_bytes(), workflow.ScheduledE4Confirmation,
        maximum_bytes=len(result.canonical_bytes())) == result


def test_forecast_substitution_refuses_before_confirmation(complete):
    first, *rest = complete.forecasts
    changed = replace(first, revision_predictions=(first.revision_predictions[0] + 1, *first.revision_predictions[1:]))
    with pytest.raises(ValueError, match="pre-outcome"):
        assess(complete, forecasts=(changed, *rest))


def test_nomination_retains_both_dispositions_and_does_not_refit(complete, monkeypatch):
    confirmation = assess(complete)
    monkeypatch.setattr(selection, "fit_standardized_ridge", lambda *a, **k: pytest.fail("confirmation cannot refit"))
    result = workflow.nominate_e4_downstream(complete.specification, confirmation, complete.prior.frozen,
        complete.prior.result, record_id="downstream.e4.control")
    assert tuple(name for name, _ in result.dispositions) == ("ORIGINAL_E3", "REVISION")
    assert result.original_e3_package == complete.specification.original_e3_package
    assert result.frozen_revision == complete.prior.frozen.identity
    with pytest.raises(ValueError, match="complete twelve-slot"):
        replace(confirmation, family_slots=confirmation.family_slots[:-1])


def test_low_decimal_precision_does_not_round_confirmation_losses(complete):
    expected = assess(complete)
    with localcontext() as context:
        context.prec = 2
        actual = assess(complete)
    assert actual.groups == expected.groups


@pytest.mark.parametrize("changes", ({"priority": ["ORIGINAL_E3", "REVISION"]}, {"minimum_revision_covered_groups": True},
    {"maximum_revision_radius": Decimal("Infinity")}, {"required_rejected_comparisons": ("undeclared",)}, {"endpoint": "chosen-after-outcome"}))
def test_nomination_scientific_operands_are_explicit_typed_and_closed(changes):
    with pytest.raises(ValueError):
        rule(**changes)
