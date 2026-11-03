# SPDX-License-Identifier: MPL-2.0
"""Exposed typed original-record fixtures, never acquisition or qualification."""

from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial as method
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_reduction as reduction_owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_selection as selection
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experimental_factorial import PairInteractionScale
from empirical_lawhood.runtime.experimental_statistics import PairedMeanTAlternative
from tests import test_matrix_programme_selection as fixture_owner
from tests.test_matrix_programme_selection import pin


@pytest.fixture(scope="module")
def exposed():
    return fixture_owner.exposed.__wrapped__()


def _reduce(programme, cases):
    waves = tuple(reduction_owner.ScheduledProgrammeWaveResult(wave.wave_id+".factorial-result", programme.identity,
        wave.wave_id, wave.group_ids, wave.root_ids, tuple(row for row in cases if row.root_id in wave.root_ids))
        for wave in programme.waves)
    return reduction_owner.reduce_programme(programme, waves, reduction_id="reduction.exposed-factorial",
        authenticate_wave=lambda row: None)


def _replace_data(exposed, rows, results=None):
    reduction = exposed.reduction if results is None else _reduce(exposed.programme, results)
    data = replace(exposed.data, reduction=ObjectIdentity.from_record(reduction.reduction_id, reduction), cases=tuple(rows))
    return SimpleNamespace(programme=exposed.programme, reduction=reduction, data=data, specification=exposed.specification)


def _specification(exposed):
    return method.ScheduledFactorialSpecification("factorial.exposed", exposed.programme.identity, exposed.specification.target,
        method.ENDPOINT, PairInteractionScale.SIGNED_MEAN_DIFFERENCE,
        tuple(method.ScheduledFactorialComparison(name, PairedMeanTAlternative.TWO_SIDED_POINT_NULL,
            Decimal(0), Decimal(".2")) for name in method.E4_COMPARISONS),
        Decimal(".05"), method.PROCEDURE, method.mean_t_requirement("requirement.exposed-common-normal"), (),
        "REQUIRE_COMPLETE_ASSIGNED_WHOLE_GROUPS")


@pytest.fixture(scope="module")
def polynomial(exposed):
    """Synthetic original-shaped records with known varying polynomial contrasts.

    Source/native/receipt pins remain exposed test metadata. No simulator,
    authentic population, issue, native contact or qualification is fabricated.
    """
    rows, results = [], []
    for case, row, result in zip(exposed.programme.cases, exposed.data.cases, exposed.reduction.cases, strict=True):
        group = Decimal(exposed.programme.group_ids.index(case.independent_group_id))
        x, y, z = tuple(-1 if value == 1 else 1 if value == 3 else 0 for value in case.factor_values)
        with localcontext() as context:
            context.prec = 50
            endpoint = (10+(1+group/100)*x+(2+group/200)*y+(3+group/300)*z
                +(Decimal(".4")+group/400)*x*y+(Decimal(".5")+group/500)*x*z
                +(Decimal(".6")+group/600)*y*z+(Decimal(".7")+group/700)*x*y*z
                +(Decimal(".8")+group/800)*Decimal(x == y == z == 0))
            primary_raw = (endpoint-Decimal(".1")).exp()-1
            fine_raw = endpoint.exp()-1
            primary = (1+primary_raw).ln()
        score = replace(row.score, cells=tuple(replace(cell, normalized_error=fine_raw if cell.view == "FINE" else primary_raw)
            for cell in row.score.cells), cumulative_log_errors=(primary,)*15)
        rows.append(replace(row, score=score))
        results.append(replace(result, score=identity(score), cumulative_log_errors=score.cumulative_log_errors))
    value = _replace_data(exposed, rows, tuple(results))
    return SimpleNamespace(**vars(value), factorial_specification=_specification(value))


@pytest.fixture(scope="module")
def assessment(polynomial):
    return method.assess_programme_factorial(polynomial.factorial_specification, polynomial.programme,
        polynomial.reduction, polynomial.data, assessment_id="assessment.exposed-factorial")


def test_original32_whole_groups_288_nested_cases_and_exact_independent_polynomial_oracle(polynomial, assessment):
    assert len(assessment.groups) == 32 and sum(len(row.root_endpoints) for row in assessment.groups) == 288
    for index, row in enumerate(assessment.groups):
        # Orthogonal averaging of the coded polynomial gives 2*each main/pair
        # coefficient; center-minuscornermean is its separate center indicator.
        group = Fraction(index)
        expected = (2*(1+group/100), 2*(2+group/200), 2*(3+group/300),
            2*(Fraction(2, 5)+group/400), 2*(Fraction(1, 2)+group/500),
            2*(Fraction(3, 5)+group/600), Fraction(4, 5)+group/800)
        assert row.disposition == "FINITE" and row.missing_root_ids == row.nonfinite_root_ids == ()
        assert all(abs(actual.fraction-wanted) < Fraction(1, 10**45) for actual, wanted in zip(row.contrasts, expected, strict=True))
        assert abs(row.three_way_descriptive.fraction-2*(Fraction(7, 10)+group/700)) < Fraction(1, 10**45)
    assert all(row.assigned_groups == row.finite_groups == 32 and row.degrees_of_freedom == 31 for row in assessment.tests)
    assert assessment.programme == polynomial.programme.identity
    assert assessment.reduction == ObjectIdentity.from_record(polynomial.reduction.reduction_id, polynomial.reduction)
    assert assessment.data == polynomial.data.identity


def test_exact_moments_preserve_group_denominator_and_log_endpoint_rounding(assessment):
    first = assessment.tests[0]
    # Independently sum the retained original root endpoints with high-minus-low
    # weights; each nine-setting group contributes exactly one difference.
    values = tuple(row.contrasts[0].fraction for row in assessment.groups)
    mean = sum(values)/32
    variance = (sum(value*value for value in values)-32*mean*mean)/31
    assert first.mean.fraction == mean and first.sample_variance.fraction == variance
    assert abs(mean-Fraction(231, 100)) < Fraction(1, 10**45)
    assert abs(variance-Fraction(44, 1250)) < Fraction(1, 10**45)


def test_real_paired_fine_cells_are_worst_endpoint_and_original_primary_stays_distinct(polynomial, assessment):
    original = polynomial.data.cases[0]
    with localcontext() as context:
        context.prec = 50
        wanted = (1+next(cell.normalized_error for cell in original.score.cells if cell.view == "FINE")).ln()
    assert dict(assessment.groups[0].root_endpoints)[original.root_id] == wanted
    assert wanted != original.score.cumulative_log_errors[0]


def test_all_twelve_slots_retained_without_caller_pvalues_or_optional_branch_invention(assessment):
    assert tuple(row.comparison_id for row in assessment.family_slots) == method.FAMILY_IDS
    assert len(assessment.tests) == 7 and len(assessment.family_slots) == 12
    absent = tuple(row for row in assessment.family_slots if row.comparison_id not in method.E4_COMPARISONS)
    assert len(absent) == 5
    assert all(row.p_value is row.adjusted_p_value is None and row.conditional_disposition == "UNEVALUABLE"
        and row.reason_codes == (method.MISSING_COMPARISON,) for row in absent)
    assert all(row.p_value > 0 and row.mean is not None for row in assessment.tests)
    smallest = min(assessment.tests, key=lambda row: (row.p_value, row.comparison.comparison_id))
    assert smallest.adjusted_p_value.fraction == 12*Fraction(smallest.p_value)
    assert assessment.three_way_scope == "DESCRIPTIVE_ONLY"


def test_four_preparation_families_remain_descriptive_with_distinct_means(assessment):
    assert len(assessment.family_descriptions) == 4
    assert all(len(row.group_ids) == row.complete_groups == 8 and row.scope == "DESCRIPTIVE_ONLY_NO_STRATUM_TESTS"
        for row in assessment.family_descriptions)
    assert len({row.means[0] for row in assessment.family_descriptions}) == 4
    assert all(len(row.means) == len(row.sample_variances) == 7 for row in assessment.family_descriptions)
    assert len(assessment.tests) == 7  # No 28 additional stratum tests.


def test_named_sampling_requirement_and_supplied_reference_never_authenticate_assumption(polynomial, assessment):
    assert assessment.specification.sampling_requirement.condition == method.SAMPLING_REQUIREMENT
    assert assessment.authority == "NONE" and assessment.sampling_assumption_status == method.ASSUMPTION_STATUS
    assert assessment.standing == "EXPLORATORY_EXPOSED_DEVELOPMENT"
    specification = replace(polynomial.factorial_specification, assumption_references=(pin("reference.exposed-assumption"),))
    value = method.assess_programme_factorial(specification, polynomial.programme, polynomial.reduction, polynomial.data,
        assessment_id="assessment.with-reference")
    assert value.sampling_assumption_status == method.ASSUMPTION_STATUS and value.authority == "NONE"


def test_explicit_alternative_pair_scale_and_margin_are_actual_calculation_operands(polynomial, assessment):
    comparisons = tuple(replace(row, alternative=PairedMeanTAlternative.GREATER, null_value=Decimal(".01"),
        practical_threshold=None) for row in polynomial.factorial_specification.comparisons)
    spec = replace(polynomial.factorial_specification, pair_scale=PairInteractionScale.DIFFERENCE_OF_DIFFERENCES,
        comparisons=comparisons)
    value = method.assess_programme_factorial(spec, polynomial.programme, polynomial.reduction, polynomial.data,
        assessment_id="assessment.different-explicit-method")
    assert value.groups[0].contrasts[:3] == assessment.groups[0].contrasts[:3]
    assert all(new.fraction == 2*old.fraction for new, old in zip(value.groups[0].contrasts[3:6], assessment.groups[0].contrasts[3:6], strict=True))
    assert value.tests[3].p_value != assessment.tests[3].p_value
    assert value.tests[0].comparison.null_value == Decimal(".01")


@pytest.mark.parametrize("damage", ("fine-missing", "fine-cell-none", "prefix-missing"))
def test_one_bad_coordinate_keeps_original_finite_neighbors_full_denominator_and_all_tests_ue(polynomial, damage):
    rows = list(polynomial.data.cases)
    original = rows[0]
    result_rows = list(polynomial.reduction.cases)
    if damage == "prefix-missing":
        rows[0] = replace(original, causal_prefix=None, score=None)
    else:
        score = replace(original.score, cells=tuple(cell for cell in original.score.cells if cell.view != "FINE")
            if damage == "fine-missing" else tuple(replace(cell, normalized_error=None) if cell.view == "FINE" else cell for cell in original.score.cells))
        rows[0] = replace(original, score=score)
        result_rows[0] = replace(result_rows[0], score=identity(score))
    changed = _replace_data(polynomial, rows, tuple(result_rows))
    value = method.assess_programme_factorial(polynomial.factorial_specification, changed.programme, changed.reduction,
        changed.data, assessment_id="assessment.missing-original-coordinate")
    first = value.groups[0]
    assert first.missing_root_ids == (original.root_id,) and first.contrasts == (None,)*7
    assert sum(endpoint is not None for _, endpoint in first.root_endpoints) == 8
    assert len(value.groups) == 32 and all(row.assigned_groups == 32 and row.finite_groups == 31 for row in value.tests)
    assert all(row.p_value is row.mean is row.sample_variance is None and row.missing_group_ids == (first.group_id,)
        for row in value.tests)
    assert all(slot.adjusted_p_value is None for slot in value.family_slots)
    affected = next(row for row in value.family_descriptions if first.group_id in row.group_ids)
    assert len(affected.group_ids) == 8 and affected.complete_groups == 7 and affected.means == (None,)*7


@pytest.mark.parametrize("absent", ((0,), (287,), tuple(range(9)), tuple(range(288))))
def test_absent_actual_source_rows_keep_assigned_roster_and_full_unevaluable_family(polynomial, absent):
    """Absence of an evidence record does not remove its assigned coordinate."""
    retained = tuple(row for index, row in enumerate(polynomial.data.cases) if index not in absent)
    data = replace(polynomial.data, cases=retained)
    result = method.assess_programme_factorial(polynomial.factorial_specification, polynomial.programme,
        polynomial.reduction, data, assessment_id="assessment.actual-absent-source-row")
    original = tuple(polynomial.programme.cases[index] for index in absent)
    absent_groups = tuple(sorted({row.independent_group_id for row in original}))
    assert len(result.groups) == 32 and sum(len(row.root_endpoints) for row in result.groups) == 288
    assert tuple(root for row in result.groups for root, _ in row.root_endpoints) == tuple(
        row.root_id for row in polynomial.programme.cases)
    assert result.reduction == ObjectIdentity.from_record(polynomial.reduction.reduction_id, polynomial.reduction)
    for group in result.groups:
        missing = tuple(row.root_id for row in original if row.independent_group_id == group.group_id)
        assert group.missing_root_ids == missing
        assert group.disposition == ("UNEVALUABLE" if missing else "FINITE")
        if missing:
            assert group.contrasts == (None,)*7
            assert sum(value is not None for _, value in group.root_endpoints) == 9-len(missing)
    assert all(test.assigned_groups == 32 and test.finite_groups == 32-len(absent_groups)
        and test.missing_group_ids == absent_groups and test.mean is test.sample_variance is test.p_value is None
        for test in result.tests)
    assert len(result.family_slots) == 12
    assert all(slot.p_value is slot.adjusted_p_value is None and slot.conditional_disposition == "UNEVALUABLE"
        for slot in result.family_slots)


@pytest.mark.parametrize("damage", ("unknown", "reordered", "duplicate"))
def test_absent_row_policy_cannot_replace_reorder_or_duplicate_actual_sources(polynomial, damage):
    rows = polynomial.data.cases
    with pytest.raises(ValueError):
        if damage == "unknown":
            rows = (*rows[:-1], replace(rows[-1], root_id="zzzz.foreign-source"))
        elif damage == "reordered":
            rows = (rows[1], rows[0], *rows[2:])
        else:
            rows = (rows[0], *rows)
        method.assess_programme_factorial(polynomial.factorial_specification, polynomial.programme,
            polynomial.reduction, replace(polynomial.data, cases=rows), assessment_id="assessment.refused-source-census")


def test_empty_evidence_bank_cannot_enter_existing_strict_development_selection(polynomial, monkeypatch):
    monkeypatch.setattr(selection, "fit_standardized_ridge", lambda *args, **kwargs: pytest.fail("empty evidence entered fitting"))
    empty = replace(polynomial.data, cases=())
    assert decode_canonical_bytes(empty.canonical_bytes(), selection.ScheduledRevisionDataBank, maximum_bytes=None) == empty
    with pytest.raises(ValueError, match="full groups or source bank"):
        selection.select_programme_revision(polynomial.specification, polynomial.programme, polynomial.reduction,
            empty, nomination_id="nomination.empty-evidence")


@pytest.mark.parametrize("policy", (None, True, "", "DROP_MISSING", "strict"))
def test_missing_record_policy_is_explicit_closed_and_not_an_implicit_complete_case_option(polynomial, policy):
    with pytest.raises(ValueError, match="explicit closed missing-record policy"):
        selection.validate_programme_paired_data(polynomial.programme, polynomial.reduction, polynomial.data,
            polynomial.factorial_specification.target, mode="E4_DEVELOPMENT", missing_record_policy=policy)


def test_numerical_violation_is_retained_as_whole_group_unevaluable(polynomial):
    row, retained = polynomial.data.cases[0], polynomial.reduction.cases[0]
    score = replace(row.score, numerical_pass=False, disposition="NATIVE_CROSSCHECK_FAILED",
        controls=(replace(row.score.controls[0], error=Decimal(1), measured_errors=(Decimal(1),), failed_steps=(1,), disposition="VIOLATED"),),
        cumulative_log_errors=(None,)*15, reason_codes=("EXPOSED_NUMERICAL_VIOLATION",))
    retained = replace(retained, score=identity(score), numerical_disposition="VIOLATED", score_disposition="NATIVE_CROSSCHECK_FAILED",
        cumulative_log_errors=(None,)*15, reason_codes=("EXPOSED_NUMERICAL_VIOLATION",))
    changed = _replace_data(polynomial, (replace(row, score=score), *polynomial.data.cases[1:]), (retained, *polynomial.reduction.cases[1:]))
    value = method.assess_programme_factorial(polynomial.factorial_specification, changed.programme, changed.reduction, changed.data,
        assessment_id="assessment.numerical-negative")
    assert value.groups[0].missing_root_ids == (row.root_id,)
    assert all(test.finite_groups == 31 and test.p_value is None for test in value.tests)


@pytest.mark.parametrize("damage", ("clock", "frame", "coordinate", "source", "criterion", "role", "foreign-programme", "foreign-reduction"))
def test_original_association_cannot_be_relabelled_to_rescue_factorial_evidence(polynomial, damage):
    row = polynomial.data.cases[0]
    data, reduction = polynomial.data, polynomial.reduction
    if damage == "clock":
        row = replace(row, causal_prefix=replace(row.causal_prefix, cutoff_tick=2))
    elif damage == "frame":
        row = replace(row, causal_prefix=replace(row.causal_prefix, frame_sha256="3"*64))
    elif damage == "coordinate":
        row = replace(row, coordinate=replace(row.coordinate, coordinate_id="coordinate.foreign"))
    elif damage in ("source", "criterion"):
        row = replace(row, score=replace(row.score, **{damage: replace(getattr(row.score, damage), object_fingerprint="3"*64)}))
    elif damage == "role":
        row = replace(row, score=replace(row.score, role="CONFIRMATION"))
    elif damage == "foreign-programme":
        data = replace(data, programme=replace(data.programme, object_fingerprint="3"*64))
    else:
        data = replace(data, reduction=replace(data.reduction, object_fingerprint="3"*64))
    if damage not in ("foreign-programme", "foreign-reduction"):
        data = replace(data, cases=(row, *data.cases[1:]))
    with pytest.raises(ValueError):
        method.assess_programme_factorial(polynomial.factorial_specification, polynomial.programme, reduction, data,
            assessment_id="assessment.refused-substitution")


def test_same_group_cannot_change_fixed_remaining_physics_even_with_consistent_original_coordinate_pins(polynomial):
    row, case = polynomial.data.cases[0], polynomial.programme.cases[0]
    coordinate = replace(row.coordinate, target_x=row.coordinate.target_x+Decimal(".01"))
    programme = replace(polynomial.programme, cases=(replace(case, coordinate=ObjectIdentity.from_record(coordinate.coordinate_id, coordinate)),
        *polynomial.programme.cases[1:]))
    reduction = replace(polynomial.reduction, programme=programme.identity)
    data = replace(polynomial.data, programme=programme.identity, reduction=ObjectIdentity.from_record(reduction.reduction_id, reduction),
        cases=(replace(row, coordinate=coordinate), *polynomial.data.cases[1:]))
    specification = replace(polynomial.factorial_specification, programme=programme.identity)
    with pytest.raises(ValueError, match="fixed preparation"):
        method.assess_programme_factorial(specification, programme, reduction, data, assessment_id="assessment.invalid-matched-physics")


@pytest.mark.parametrize("damage", ("missing-comparison", "comparison-order", "duplicate-comparison", "weaken-assumption", "wrong-procedure",
    "wrong-endpoint", "bool-alpha", "nonfinite-alpha", "float-margin", "bool-margin", "negative-practical"))
def test_scientific_choices_and_complete_family_have_no_defaults_or_weakened_aliases(polynomial, damage):
    specification = polynomial.factorial_specification
    with pytest.raises((TypeError, ValueError)):
        if damage == "missing-comparison":
            replace(specification, comparisons=specification.comparisons[:-1])
        elif damage == "comparison-order":
            replace(specification, comparisons=tuple(reversed(specification.comparisons)))
        elif damage == "duplicate-comparison":
            replace(specification, comparisons=(specification.comparisons[0],)*7)
        elif damage == "weaken-assumption":
            replace(specification, sampling_requirement=replace(specification.sampling_requirement, condition="NORMAL_LABEL_ONLY"))
        elif damage == "wrong-procedure":
            replace(specification, procedure="FINITE_ONLY_T")
        elif damage == "wrong-endpoint":
            replace(specification, endpoint="PRIMARY_ONLY")
        elif damage in ("bool-alpha", "nonfinite-alpha"):
            replace(specification, alpha=True if damage == "bool-alpha" else Decimal("NaN"))
        else:
            change = {"practical_threshold": Decimal(-1)} if damage == "negative-practical" else {"null_value": .1 if damage == "float-margin" else True}
            replace(specification.comparisons[0], **change)


def test_canonical_output_preserves_exact_fractions_and_all_adverse_scope(assessment):
    raw = assessment.canonical_bytes()
    assert decode_canonical_bytes(raw, method.ScheduledFactorialAssessment, maximum_bytes=None) == assessment
    with pytest.raises(ValueError):
        replace(assessment, groups=assessment.groups[:-1])
    with pytest.raises(ValueError):
        replace(assessment, authority="QUALIFIED")
    with pytest.raises(ValueError):
        replace(assessment, family_slots=assessment.family_slots[:-1])


def test_cold_declaration_is_pure_falsify_exposed_development_nonpromotable(monkeypatch):
    from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.plans import ScientificStage
    monkeypatch.setattr(method, "assess_programme_factorial", lambda *a, **kw: pytest.fail("cold discovery executed scientific analysis"))
    declaration, = method.operation_declarations()
    assert declaration.capability_key == method.OPERATION and declaration.stage is ScientificStage.FALSIFY
    assert declaration.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    assert declaration.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
    assert declaration.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
    assert declaration.registration().input_record_types == declaration.input_record_types
    assert not declaration.execution_properties.native_effect
    assert len(declaration.input_ports) == 4


def test_existing_development_selection_outputs_keep_exact_feature_and_paired_target_values(polynomial):
    allocation, features, old_targets, missing = selection._validate_data(polynomial.specification, polynomial.programme,
        polynomial.reduction, polynomial.data)
    targets, missing_frozen = selection.validate_programme_paired_data(polynomial.programme, polynomial.reduction,
        polynomial.data, polynomial.specification.target, mode="E4_DEVELOPMENT", missing_record_policy="STRICT")
    assert targets == old_targets and missing == set(missing_frozen) == set()
    assert allocation == selection.programme_selection_allocation(polynomial.programme)
    first = polynomial.programme.cases[0]
    assert features[first.root_id] == {"temperature": Decimal(1), "friction": Decimal(1), "coupling": Decimal(1),
        "pair.temperature-friction": Decimal(1), "pair.temperature-coupling": Decimal(1), "pair.friction-coupling": Decimal(1),
        "aggregate-curvature": Decimal(0)}


@pytest.mark.parametrize("mode", ("E4_REVISION_CALIBRATION", "CONFIRMATION", "E4_CONFIRMATION", None))
def test_development_data_cannot_be_relabelled_as_calibration_or_confirmation(polynomial, mode):
    with pytest.raises(ValueError, match="phase or target"):
        selection.validate_programme_paired_data(polynomial.programme, polynomial.reduction, polynomial.data,
            polynomial.factorial_specification.target, mode=mode, missing_record_policy="STRICT")


def _compiled(exposed):
    from pathlib import Path
    from empirical_lawhood.api import load_authoring
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    declaration, = method.operation_declarations()
    campaign = replace(load_authoring(Path(__file__).parents[1]/"tests/fixtures/reference-campaign.json").campaign,
        budget=declaration.resources)
    specification = _specification(exposed)
    lowered = method.lower_exposed_programme_factorial(specification, exposed.programme, exposed.reduction,
        exposed.data, campaign=campaign)
    registry = CapabilityRegistry("registry.exposed-factorial", (declaration.manifest(),))
    options = dict(registrations=(declaration.registration(),), registry=registry,
        implementation_commit="a"*40, output_codecs=declaration.record_codecs)
    return lowered, options, compile_recursive_wave(draft=lowered.draft, **options)


def test_existing_recursive_compiler_uses_real_declared_exposed_factorial_consumer(exposed):
    from empirical_lawhood.runtime.plans import ScientificStage
    lowered, _, compiled = _compiled(exposed)
    task, = compiled.execution_plan.tasks
    assert task.stage is ScientificStage.FALSIFY
    assert not task.dependency_task_ids
    assert lowered.draft.development_study.assigned_unit_ids == exposed.programme.group_ids
    assert len(lowered.input_records) == 4


@pytest.mark.parametrize("damage", ("thinned-root", "wrong-source-link", "missing-source-link", "swapped-input-role", "protected-input", "wrong-config"))
def test_public_compiler_cannot_bypass_original_exposed_root_inputs_or_access(exposed, damage):
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    lowered, options, _ = _compiled(exposed)
    draft = lowered.draft
    if damage == "thinned-root":
        draft = replace(draft, development_study=replace(draft.development_study,
            assigned_unit_ids=draft.development_study.assigned_unit_ids[:-1]))
    elif damage == "wrong-source-link":
        draft = replace(draft, links=(replace(draft.links[0], external_input_id=draft.external_inputs[-1].input_id), *draft.links[1:]))
    elif damage == "missing-source-link":
        draft = replace(draft, links=draft.links[:-1])
    elif damage == "swapped-input-role":
        draft = replace(draft, links=(replace(draft.links[0], scientific_role="MODEL"), *draft.links[1:]))
    elif damage == "protected-input":
        draft = replace(draft, external_inputs=(replace(draft.external_inputs[0], outcome_access=OutcomeAccess.EVALUATION_SEALED,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE), *draft.external_inputs[1:]))
    else:
        operation, = draft.operations
        original = decode_canonical_bytes(operation.config_payload.encode(), method.ScheduledFactorialOperationConfig, maximum_bytes=None)
        config = replace(original, data=replace(original.data, object_fingerprint="3"*64))
        operation = replace(operation, config_payload=config.canonical_bytes().decode())
        draft = replace(draft, operations=(operation,))
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=draft, **options)


def test_public_config_refuses_confirmation_even_before_a_protected_factory_exists(exposed):
    specification = _specification(exposed)
    # Invalid synthetic phase substitution: deliberately avoid constructing a
    # valid64 source, because no outcome authority should reach this public op.
    programme = object.__new__(type(exposed.programme))
    for name in exposed.programme.__dataclass_fields__:
        if name not in ("SCHEMA", "VERSION"):
            object.__setattr__(programme, name, getattr(exposed.programme, name))
    object.__setattr__(programme, "mode", "E4_CONFIRMATION")
    with pytest.raises(ValueError, match="no confirmation access bypass"):
        method.ScheduledFactorialOperationConfig("config."+method.factorial_node_id(specification), programme, specification,
            ObjectIdentity.from_record(exposed.reduction.reduction_id, exposed.reduction), exposed.data.identity)


def test_pure64_confirmation_shaped_fixture_retains_conditional_status_and_cannot_enter_public_factory(polynomial):
    """A newly constructed synthetic64 fixture has no source freshness/authority.

    Repeated deterministic endpoint patterns are disclosed fixture data, not
    genuine new independent scientific units. This checks the full64 software
    census without claiming that the sampling assumption holds for this fixture.
    """
    from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgrammeWave
    cases, rows, results = [], [], []
    for group_index, group_id in enumerate(polynomial.programme.group_ids):
        originals = tuple((case, row, result) for case, row, result in zip(polynomial.programme.cases,
            polynomial.data.cases, polynomial.reduction.cases, strict=True) if case.independent_group_id == group_id)
        for copy in range(2):
            new_group = f"group.synthetic-confirmation.{2*group_index+copy:02}"
            for index, (case, row, result) in enumerate(originals):
                root = f"root.synthetic-confirmation.{2*group_index+copy:02}.{index}"
                source = pin("source."+root, case.source.object_schema, case.source.object_version)
                cutoff = replace(case.information_cutoff, cutoff_id="cutoff."+root)
                new_case = replace(case, root_id=root, independent_group_id=new_group, role="CONFIRMATION", source=source,
                    information_cutoff=cutoff)
                prefix = replace(row.causal_prefix, prefix_id="prefix."+root, source=source,
                    root=replace(row.causal_prefix.root, root_id=root, independent_group_id=new_group, role=MatrixProgrammeRole.CONFIRMATION),
                    arrays=replace(row.causal_prefix.arrays, operand_id="arrays."+root, source=source))
                score = replace(row.score, score_id="score."+root, source=source, causal_prefix=identity(prefix), root_id=root,
                    independent_group_id=new_group, role="CONFIRMATION")
                cases.append(new_case)
                rows.append(replace(row, root_id=root, causal_prefix=prefix, score=score))
                results.append(replace(result, root_id=root, independent_group_id=new_group, source=source, score=identity(score)))
    groups = tuple(sorted({case.independent_group_id for case in cases}))
    waves = tuple(ScheduledProgrammeWave(f"wave.synthetic-confirmation.{index//8}", groups[index:index+8],
        tuple(case.root_id for case in cases if case.independent_group_id in groups[index:index+8])) for index in range(0, 64, 8))
    programme = replace(polynomial.programme, programme_id="programme.synthetic-confirmation", mode="E4_CONFIRMATION",
        cases=tuple(cases), source_census=tuple(case.source for case in cases), waves=waves, minimum_group_count=64)
    reduction = _reduce(programme, tuple(results))
    data = replace(polynomial.data, bank_id="data.synthetic-confirmation", programme=programme.identity,
        reduction=ObjectIdentity.from_record(reduction.reduction_id, reduction), cases=tuple(rows))
    specification = replace(polynomial.factorial_specification, programme=programme.identity)
    actual = method.assess_programme_factorial(specification, programme, reduction, data, assessment_id="assessment.synthetic-confirmation")
    assert len(actual.groups) == 64 and sum(len(row.root_endpoints) for row in actual.groups) == 576
    assert all(row.assigned_groups == row.finite_groups == 64 and row.degrees_of_freedom == 63 for row in actual.tests)
    assert actual.authority == "NONE" and actual.standing == "CONDITIONAL_CONFIRMATION_NUMBERS_NO_AUTHORITY"
    assert actual.sampling_assumption_status == method.ASSUMPTION_STATUS
    with pytest.raises(ValueError, match="no confirmation access bypass"):
        method.ScheduledFactorialOperationConfig("config."+method.factorial_node_id(specification), programme, specification,
            ObjectIdentity.from_record(reduction.reduction_id, reduction), data.identity)


def _sealed_context(case, *, damage=None):
    """In-process runner conformance with actual sealed inputs; no worker proof."""
    import os
    from empirical_lawhood.infrastructure.artifact_stream_primitives import (
        _anonymous_input_descriptor, _PreopenedBoundedReader, _seal_anonymous_input,
    )
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
    from empirical_lawhood.runtime.execution import (
        TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort,
    )
    declaration, = method.operation_declarations()
    manifest = declaration.manifest()
    specification = case.factorial_specification
    node = method.factorial_node_id(specification)
    config = method.ScheduledFactorialOperationConfig("config."+node, case.programme, specification,
        ObjectIdentity.from_record(case.reduction.reduction_id, case.reduction), case.data.identity)
    records = ((config.config_id, config), ("operand.programme", case.programme), ("operand.specification", specification),
        ("operand.reduction", case.reduction), ("operand.data", case.data))
    ports = []
    try:
        for artifact_id, record in records:
            if damage == "missing-input" and artifact_id == "operand.data":
                continue
            raw = record.canonical_bytes()
            descriptor = _anonymous_input_descriptor()
            try:
                position = 0
                while position < len(raw):
                    position += os.write(descriptor, raw[position:])
                _seal_anonymous_input(descriptor)
                protected = damage == "protected-input" and artifact_id == "operand.data"
                binding = WorkerInputBinding(artifact_id, "materialization."+artifact_id, record.SCHEMA, "application/json", len(raw),
                    VisibilityCeiling.PROSPECTIVE if protected else VisibilityCeiling.DEVELOPMENT_ONLY,
                    OutcomeAccess.EVALUATION_SEALED if protected else OutcomeAccess.DEVELOPMENT_VISIBLE, WorkerInputKind.EXTERNAL)
                ports.append(WorkerInputPort(binding, _PreopenedBoundedReader(descriptor, maximum_bytes=len(raw))))
            except BaseException:
                os.close(descriptor)
                raise
        ports = tuple(sorted(ports, key=lambda row: row.artifact_id))
        output = WorkerOutputPort(node+".product", method.ScheduledFactorialAssessment.SCHEMA,
            declaration.outputs[0].profile, "application/json", node+".product")
        if damage == "wrong-output":
            output = replace(output, payload_schema=selection.ScheduledRevisionNomination.SCHEMA)
        context = TaskContext("run.exposed-factorial", node, node+".attempt-001",
            CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config.config_id),
            tuple(port.binding for port in ports), ports, (output,), manifest.permissions, manifest.maximum_outcome_access,
            declaration.resources, WorkerIsolationProfile.TRUSTED_LOCAL, ())
        return declaration, context
    except BaseException:
        for port in ports:
            port.close()
        raise


def test_in_process_registered_runner_preflights_twice_and_executes_same_actual_sealed_original_records(polynomial, assessment):
    declaration, context = _sealed_context(polynomial)
    try:
        runner = declaration.provider_factory().runner_factory()
        assert runner.preflight(context) is None and runner.preflight(context) is None
        assert all(port.bytes_read == 0 for port in context.input_ports)
        product, = runner.execute(context).outputs
        actual = decode_canonical_bytes(product.payload, method.ScheduledFactorialAssessment, maximum_bytes=None)
        assert actual == replace(assessment, assessment_id="assessment."+polynomial.factorial_specification.specification_id)
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        for port in context.input_ports:
            port.close()


@pytest.mark.parametrize("damage", ("protected-input", "missing-input", "wrong-output"))
def test_in_process_registered_runner_refuses_input_or_output_contract_before_any_calculation(polynomial, monkeypatch, damage):
    declaration, context = _sealed_context(polynomial, damage=damage)
    monkeypatch.setattr(method, "assess_programme_factorial", lambda *args, **kwargs: pytest.fail("invalid contract entered factorial calculation"))
    try:
        runner = declaration.provider_factory().runner_factory()
        with pytest.raises(ValueError):
            runner.preflight(context)
        with pytest.raises(ValueError):
            runner.execute(context)
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        for port in context.input_ports:
            port.close()
