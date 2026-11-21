# SPDX-License-Identifier: MPL-2.0
"""Hand-calculated exposed reduction falsifiers, never molecular qualification."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction as F

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact as Q
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import ANCHORED_LOG_AXES, RAW_LOG_AXES, EndpointValues, JointLogCovariance, PairedJointValue, anchor_joint_value
from empirical_lawhood.domains.rubisco.rubisco_response import reduction_controls as controls
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_study, disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.reduction_error import PARITY_FIELDS, STAGES, JointErrorDecomposition, JointErrorStage, SupplierComparisonParity, assess_joint_error_decomposition
from empirical_lawhood.domains.rubisco.rubisco_response.reduction_target import assess_reduction_target
from empirical_lawhood.domains.rubisco.rubisco_response.study import exposed_source_allocation
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from tests.test_recursive_inquiry_policy import obj
from tests.test_rubisco_response_report import report


def vector(*values):
    return tuple(Q.of(value) for value in values)


def matrix(*rows):
    return tuple(vector(*row) for row in rows)


def driven(*, changing=False):
    row = controls.DrivenControlStep(matrix((1, 1), (1, 1)), matrix((1,), (2,)), matrix((1, 0), (2, 0)), matrix((3,), (4,)))
    steps = (row, replace(row, a=matrix((2, 1), (1, 1))) if changing else row, row)
    return controls.DrivenResponseControl("control.exposed", steps, (vector(1),) * 3, vector(1, 2), (obj("exposed.equations"),))


def scalar(control_id, *, derivative=False):
    # Every operand has a nonzero derivative, including preparation and drive.
    row = controls.DrivenControlStep(matrix((1,)), matrix((1,)), matrix((1,), (2,)), matrix((1,), (3,)))
    return controls.DrivenResponseControl(control_id, (row,) * 2, (vector(1),) * 2, vector(1),
        (obj("exposed.direction" if derivative else "exposed.scalar"),))


def propagate(control, name="trajectory.exposed"):
    return controls.propagate_control(control, trajectory_id=name)


def assess(control, trajectory):
    return controls.assess_control_trajectory(control, trajectory, assessment_id="assessment.exposed.balance")


def forbidden(*args, **kwargs):
    pytest.fail("independent retained assessment entered the original producer")


def test_receiver_containment_does_not_remove_omitted_return_initial_or_driving_terms():
    control = driven()
    full = propagate(control)
    assert full.states == tuple(vector(*row) for row in ((1, 2), (4, 5), (10, 11), (22, 23)))
    assert full.outputs == tuple(vector(*row) for row in ((4, 6), (7, 12), (13, 24)))
    projected = propagate(controls.projected_control(control, (0,), control_id="control.projected"))
    assert projected.outputs == tuple(vector(*row) for row in ((4, 6), (5, 8), (6, 10)))
    # Both receiver rows contain only the retained coordinate, yet feedback matters.
    assert all(row.c[0][1] == row.c[1][1] == Q.of(0) for row in control.steps)
    memory, parts = controls.eliminate_control_memory(control, (0,), trajectory_id="trajectory.memory")
    assert memory.states == full.states and memory.outputs == full.outputs
    assert (parts[2].initial, parts[2].drive, parts[2].returned_history) == (vector(2), vector(4), vector(5))
    assert assess(control, memory).disposition is A.SATISFIED


def test_changing_dynamics_falsifies_frozen_control_but_complete_memory_retains_them():
    control = driven(changing=True)
    full = propagate(control)
    frozen = propagate(controls.frozen_control(control, control_id="control.frozen"))
    assert full.outputs[-1] == vector(17, 32) and frozen.outputs[-1] == vector(13, 24)
    assert assess(control, replace(frozen, control=control.identity)).disposition is A.FALSIFIED
    memory, _ = controls.eliminate_control_memory(control, (0,), trajectory_id="trajectory.updated-memory")
    assert memory.outputs == full.outputs and assess(control, memory).disposition is A.SATISFIED


def test_finite_response_includes_initial_direct_drive_and_parameter_terms(monkeypatch):
    base, direction = scalar("control.base"), scalar("control.direction", derivative=True)
    finite = controls.finite_perturbed_control(base, direction, Q.of(1), control_id="control.finite")
    tangent = controls.tangent_control(base, direction, control_id="control.tangent")
    y0, y1, dy = propagate(base), propagate(finite, "trajectory.finite"), propagate(tangent, "trajectory.tangent")
    assert y0.outputs == (vector(2, 5), vector(3, 7))
    assert y1.outputs == (vector(8, 20), vector(20, 44))
    assert dy.outputs == (vector(4, 10), vector(8, 18))
    monkeypatch.setattr(controls, "propagate_control", forbidden)
    with localcontext() as context:
        context.prec = 2
        remainder = controls.finite_response_remainders(base, direction, Q.of(1), y0, y1, dy)
    assert remainder == (vector(2, 5), vector(9, 19))
    assert controls.finite_response_remainders(base, direction, Q.of(1), y0,
        replace(y1, original_state="UNKNOWN"), dy) is None
    assert controls.finite_response_remainders(base, direction, Q.of(1), y0, y1,
        replace(dy, outputs=(vector(0, 0),) * 2)) is None


def test_retained_assessor_never_replays_and_preserves_failed_partial_or_wrong_source(monkeypatch):
    control = driven()
    result = propagate(control)
    monkeypatch.setattr(controls, "propagate_control", forbidden)
    monkeypatch.setattr(controls, "eliminate_control_memory", forbidden)
    assert assess(control, result).disposition is A.SATISFIED
    wrong = replace(result, outputs=(vector(99, 99), *result.outputs[1:]))
    assert assess(control, wrong).disposition is A.FALSIFIED
    assert assess(control, wrong).residuals[2][0] == vector(95, 93)
    for state in ("FAILED", "UNKNOWN"):
        partial = replace(result, original_state=state, states=result.states[:1], outputs=())
        checked = assess(control, partial)
        assert checked.disposition is A.UNEVALUABLE and checked.residuals is None
        assert checked.trajectory == partial
    assert assess(control, replace(result, control=obj("wrong.control"))).disposition is A.FALSIFIED
    assert assess(control, replace(result, states=result.states[:1])).disposition is A.FALSIFIED


def test_control_contracts_refuse_physical_relabelling_and_unbounded_dimensions():
    control = driven()
    for changed in ({"units": "s^-1"}, {"clock": "physical-time"}, {"steps": control.steps * 11}, {"inputs": control.inputs[:1]}):
        with pytest.raises(ValueError):
            replace(control, **changed)
    for indices in ((), (0, 1), (1, 0), (0, 0), (2,), (True,)):
        with pytest.raises(ValueError):
            controls.projected_control(control, indices, control_id="invalid.partition")
    with pytest.raises(ValueError):
        replace(control.steps[0], c=matrix((1, 0)))


def parity():
    operands = {name: obj("operand." + name) for name in ("case", "context", *PARITY_FIELDS,
        "reference_method", "conventional_method", "approximation_method")}
    return SupplierComparisonParity("parity.exposed", **operands,
        sources=tuple(sorted(operands.values(), key=lambda row: row.object_id)))


def joint(wt=2, mutant=3):
    return PairedJointValue("point.exposed", EndpointValues.of(wt, 10 * wt), EndpointValues.of(mutant, 10 * mutant))


def stages(*, anchor=False):
    selected = parity()
    values = (joint(), joint(1), joint(), joint(), joint(), joint())
    baseline = joint(2, 2)
    if anchor:
        values = tuple(anchor_joint_value(value, EndpointValues.of(10, 100)) for value in values)
        baseline = anchor_joint_value(baseline, EndpointValues.of(10, 100))
    rows = tuple(JointErrorStage(role, selected.identity,
        selected.reference_method if role == "REFERENCE" else selected.approximation_method if role == "APPROXIMATION" else obj("method." + role.lower()),
        "AVAILABLE", value, (obj("exposed.results"),), ()) for role, value in zip(STAGES, values, strict=True))
    conventional = JointErrorStage("CONVENTIONAL", selected.identity, selected.conventional_method, "AVAILABLE", baseline, (obj("exposed.results"),), ())
    return selected, rows, conventional


def decomposition(selected=None, rows=None, conventional=None, *, anchor=False, tolerances=None):
    if selected is None:
        selected, rows, conventional = stages(anchor=anchor)
    return assess_joint_error_decomposition(selected, rows, conventional, scenario_id="scenario.exposed", point_id="point.exposed",
        scale="ANCHORED" if anchor else "RAW", log_tolerances=tolerances or (D("0.1"),) * 6, assessment_id="error.exposed")


def test_signed_error_preserves_cancellation_all_six_axes_and_conventional_error():
    result = decomposition()
    assert result.terms[0].ratio_factors == vector(2, 2, 1, 1, F(1, 2), F(1, 2))
    assert result.terms[1].ratio_factors == vector(F(1, 2), F(1, 2), 1, 1, 2, 2)
    assert result.terms[0].signed_log_bounds[0][0] > 0 and result.terms[0].signed_log_bounds[4][1] < 0
    assert result.total.ratio_factors == result.telescoping_product == vector(1, 1, 1, 1, 1, 1)
    assert result.total.normalized_absolute_error_bounds == ((Q.of(0), Q.of(0)),) * 6
    assert result.conventional_error.ratio_factors == vector(1, 1, F(3, 2), F(3, 2), F(3, 2), F(3, 2))
    assert result.chemical_model_discrepancy == "OUTSIDE_THE_SHARED_MODEL_COMPARISON_NOT_ASSESSED"
    assert decode_canonical_bytes(result.canonical_bytes(), JointErrorDecomposition, maximum_bytes=200_000) == result


@pytest.mark.parametrize("state", ["FAILED", "UNKNOWN", "NOT_ENTERED"])
def test_missing_stage_never_becomes_zero_but_available_total_is_retained(state):
    selected, rows, conventional = stages()
    missing = replace(rows[2], original_state=state, value=None, reason_codes=("ORIGINAL_" + state,))
    result = decomposition(selected, (*rows[:2], missing, *rows[3:]), conventional)
    assert result.terms[1].ratio_factors is result.terms[2].ratio_factors is result.telescoping_product is None
    assert result.total.ratio_factors == vector(1, 1, 1, 1, 1, 1)
    failed_final = replace(rows[-1], original_state="FAILED", reason_codes=("ORIGINAL_FAILED",))
    result = decomposition(selected, (*rows[:-1], failed_final), conventional)
    assert result.total.ratio_factors is None and result.stages[-1].value is not None


def test_anchor_dependence_is_retained_without_inventing_cross_stage_covariance():
    selected, rows, conventional = stages(anchor=True)
    covariance = JointLogCovariance(ANCHORED_LOG_AXES,
        tuple((D("0.01"),) * 6 for _ in range(6)), rows[0].sources)
    rows = (replace(rows[0], covariance=covariance), *rows[1:])
    result = decomposition(selected, rows, conventional, anchor=True)
    assert result.stages[0].covariance is covariance
    assert result.terms[0].ratio_factors == vector(1, 1, F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    assert result.cross_stage_covariance == "NOT_IDENTIFIED_FROM_WITHIN_STAGE_COVARIANCES"
    raw = JointLogCovariance(RAW_LOG_AXES, tuple((D("0.01"),) * 4 for _ in range(4)), rows[0].sources)
    with pytest.raises(ValueError, match="shared-reference"):
        replace(rows[0], covariance=raw)
    with pytest.raises(ValueError, match="covariance sources"):
        replace(rows[0], sources=(obj("other.source"),))
    with pytest.raises(ValueError, match="shared WT reference"):
        decomposition(anchor=True, selected=parity(), rows=stages()[1], conventional=stages()[2])


def test_error_account_rejects_changed_model_methods_point_or_complete_term_census():
    selected, rows, conventional = stages()
    for changed in (replace(rows[1], parity=obj("other.model")), replace(rows[1], value=replace(rows[1].value, value_id="other.point"))):
        with pytest.raises(ValueError, match="substitutes"):
            decomposition(selected, (rows[0], changed, *rows[2:]), conventional)
    with pytest.raises(ValueError, match="selected comparison methods"):
        decomposition(selected, rows, replace(conventional, method=obj("other.method")))
    with pytest.raises(ValueError, match="all declared intermediates"):
        decomposition(selected, rows[:-1], conventional)
    result = decomposition()
    with pytest.raises(ValueError, match="drops a term"):
        replace(result, terms=result.terms[:-1])
    with pytest.raises(ValueError, match="chemical-model accuracy"):
        replace(result, biological_validation="ESTABLISHED")


def test_error_bounds_require_exact_types_and_ignore_ambient_decimal_rounding():
    with localcontext() as context:
        context.prec = 2
        low = decomposition()
    assert low == decomposition()
    with pytest.raises(ValueError):
        decomposition(tolerances=(D(0),) * 6)
    term = low.total
    with pytest.raises((TypeError, ValueError)):
        replace(term, signed_log_bounds=((0.0, 0.0),) * 6)
    with pytest.raises(ValueError, match="nonnegative ordered"):
        replace(term, normalized_absolute_error_bounds=((Q.of(-1), Q.of(0)),) * 6)
    with pytest.raises(ValueError, match="original exact ratio"):
        replace(term, signed_log_bounds=((D(1), D(1)),) * 6)


@pytest.fixture(scope="module")
def target_report():
    return report()


def test_no_target_can_be_selected_from_conditional_sensitivity_and_unknown_cost(target_report):
    result = assess_reduction_target(target_report, assessment_id="target.exposed")
    assert len(result.candidates) == 16 and result.selected_target is None
    assert result.disposition == "HOLD_NO_JUSTIFIED_PRODUCTION_SUPPLIER"
    assert {row.parameter for row in result.candidates} == {"a", "b", "c", "d_c", "d_o", "o", "r_c", "r_o"}
    assert any(row.local_meaning == "LOCALLY_ZERO_NOT_GLOBAL_EXCLUSION" for row in result.candidates)
    assert target_report.study.acceptance.matrix_handoff_requirement_id in result.remaining_requirement_ids
    assert all(any("actual-supplier-cost-or-consequential-uncertainty" in requirement for requirement in row.missing_requirement_ids)
               for row in result.candidates)
    with pytest.raises(ValueError, match="production approximation target"):
        replace(result, selected_target=obj("convenient.matrix"))
    with pytest.raises(ValueError, match="drops zero"):
        replace(result, candidates=result.candidates[:1])


def test_target_census_preserves_failed_and_unknown_supplier_alternatives():
    study = disclosed_study()
    supplies = (disclosed_supply(scenario_states=("AVAILABLE", "FAILED", "UNKNOWN")), study.supplies[1])
    study = replace(study, supplies=supplies, allocation=exposed_source_allocation(study.cases, supplies))
    result = assess_reduction_target(report(study), assessment_id="target.incomplete")
    assert len(result.candidates) == 32
    missing = [row for row in result.candidates if row.original_scenario_state != "AVAILABLE"]
    assert len(missing) == 16 and all(row.local_meaning == "UNKNOWN" and row.local_sensitivity is None for row in missing)
    assert result.selected_target is None
