# SPDX-License-Identifier: MPL-2.0
"""Complete no-native comparison preparation and immutable source selections."""

from dataclasses import replace
from decimal import Decimal as D

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.comparison_preparation import ARMS, COST_ARMS, ComparisonWorkAllocation, ResponseComparisonDesign, comparison_design, prepare_response_comparison
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_study, disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_specification import response_experiment_specification, select_response_study
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_preparation import MolecularPreparationSelection, RetainedPreparationMember, assess_preparation_census
from empirical_lawhood.domains.rubisco.rubisco_response.reduction_error import PARITY_FIELDS, SupplierComparisonParity
from empirical_lawhood.domains.rubisco.rubisco_response.reduction_target import assess_reduction_target
from empirical_lawhood.domains.rubisco.rubisco_response.recursive_translation import response_draft, scientific_work
from empirical_lawhood.domains.rubisco.rubisco_response.study import exposed_source_allocation
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExecutionSelection
from tests.test_recursive_inquiry_policy import obj
from tests.test_rubisco_response_policy import selection
from tests.test_rubisco_response_report import report


def design(*, original=None, with_policies=True, with_parity=True):
    original = disclosed_study() if original is None else original
    template = selection(supplier=False, refinements=False)
    spec = response_experiment_specification(original, acceptance=template.study.acceptance)
    study = select_response_study(spec, original)
    policies = tuple(replace(template, policy_id="policy." + case.case_id, study=study, case_id=case.case_id) for case in study.cases.cases)
    parities = []
    for supply in study.supplies:
        operands = {name: obj("shared." + name) for name in PARITY_FIELDS}
        operands.update(case=supply.case.identity, context=supply.context.identity,
            reference_method=study.acceptance.reference_method, conventional_method=study.acceptance.conventional_baseline,
            approximation_method=obj("method.exposed.approximation"))
        parities.append(SupplierComparisonParity("parity." + supply.case.case_id, **operands,
            sources=tuple(sorted(set(operands.values()), key=lambda row: row.object_id))))
    return comparison_design(original, spec, design_id="comparison.exposed", policies=policies if with_policies else (),
        parities=tuple(parities) if with_parity else (), false_admission_denominator="ALL_ASSIGNED_UNITS", scale="RAW")


def execution():
    return ExecutionSelection(1, "environment.exposed", obj("source.exposed"), "/selected/exposed/custody")


def test_preparation_uses_existing_lowering_but_retains_actual_native_boundaries():
    selected = design()
    prepared = prepare_response_comparison(selected, execution=execution())
    assert not prepared.conditional_preparation.dependencies
    assert prepared.conditional_preparation.draft is not None
    assert prepared.conditional_preparation.census.native_effect_count == 0
    assert len(prepared.assignments) == 6 and {row.arm for row in prepared.assignments} == set(ARMS)
    assert len({row.unit_id for row in prepared.assignments}) == 1
    assert prepared.native_entry_status == "NOT_READY" and prepared.new_native_calls == 0
    codes = {row.code.removeprefix("rubisco.comparison.") for row in prepared.native_entry_prerequisites}
    assert {"actual-entry-authority", "actual-source-admission", "actual-resource-capacity", "actual-storage",
        "actual-specialist-environment", "installed-native-lowering", "installed-settled-source-acceptance",
        "justified-supplier", "active-state-and-reference", "native-parity", "indicator-and-sequential-validity", "matrix-transfer"} <= codes
    assert {row.kind for row in prepared.native_entry_prerequisites} == set(DependencyKind)
    assert decode_canonical_bytes(selected.canonical_bytes(), ResponseComparisonDesign, maximum_bytes=2_000_000) == selected
    with pytest.raises(ValueError, match="entry boundary"):
        replace(prepared, native_entry_prerequisites=())
    with pytest.raises(ValueError, match="authorize"):
        replace(prepared, native_entry_status="READY")


def test_every_original_failed_or_unknown_scenario_has_all_three_arm_assignments():
    original = disclosed_study()
    supplies = (disclosed_supply(scenario_states=("AVAILABLE", "FAILED", "UNKNOWN")), original.supplies[1])
    original = replace(original, supplies=supplies, allocation=exposed_source_allocation(original.cases, supplies))
    selected = design(original=original)
    rows = selected.assignments
    assert len(rows) == 12
    missing = [row for row in rows if row.original_scenario_state != "AVAILABLE"]
    assert len(missing) == 6 and all(row.point_id is None for row in missing)
    assert {row.original_scenario_state for row in missing} == {"FAILED", "UNKNOWN"}
    assert len({row.unit_id for row in rows}) == 1
    prepared = prepare_response_comparison(selected, execution=execution())
    with pytest.raises(ValueError, match="assignment"):
        replace(prepared, assignments=rows[:3])
    with pytest.raises(ValueError, match="candidate, control"):
        replace(selected, cases=selected.cases[:1])


def test_missing_policy_and_parity_are_explicit_for_each_case_not_inferred():
    selected = design(with_policies=False, with_parity=False)
    prepared = prepare_response_comparison(selected, execution=ExecutionSelection())
    assert prepared.conditional_preparation.draft is None
    assert {row.code for row in prepared.conditional_preparation.dependencies} == {
        "rubisco.response.environment", "rubisco.response.output-root", "rubisco.response.source-snapshot"}
    assert sum(row.code.endswith(".policy-selection") for row in prepared.native_entry_prerequisites) == 2
    assert sum(row.code.endswith(".parity-selection") for row in prepared.native_entry_prerequisites) == 2
    assert all(row.method is None for row in prepared.assignments if row.arm == "reduced")


def test_changed_criteria_require_new_policy_and_keep_original_sources():
    selected = design()
    criterion = replace(selected.specification.acceptance, minimum_useful_service=D("0.9"))
    spec = replace(selected.specification, acceptance=criterion)
    with pytest.raises(ValueError, match="frozen sources"):
        replace(selected, specification=spec)
    edited = comparison_design(selected.original_study, spec, design_id="comparison.edited",
        false_admission_denominator="ADMITTED_UNITS", scale="RAW")
    assert edited.study.supplies == selected.study.supplies and edited.original_study == selected.original_study
    assert edited.study.acceptance.minimum_useful_service == D("0.9")
    assert edited.study.identity != selected.study.identity
    with pytest.raises(ValueError, match="original source study"):
        replace(selected, original_study=replace(selected.original_study, study_id="substituted.original"))


def test_parity_cannot_substitute_context_or_conventional_method():
    selected = design()
    row = selected.cases[0]
    for field in ("context", "conventional_method"):
        changed = obj("substituted." + field)
        parity = replace(row.parity, **{field: changed}, sources=tuple(sorted({*row.parity.sources, changed}, key=lambda item: item.object_id)))
        with pytest.raises(ValueError, match="parity changes"):
            replace(selected, cases=(replace(row, parity=parity), selected.cases[1]))
    with pytest.raises(ValueError, match="exposed preparation"):
        replace(selected, evidence_scope="HELD_PROSPECTIVE")
    with pytest.raises(ValueError, match="exposed preparation"):
        replace(selected, reference_audit="SUCCESSFUL_CASES_ONLY")


def test_complete_preparation_and_target_records_cannot_discharge_physical_admission():
    selected = design()
    study = selected.study
    chemistry = study.supplies[0].context.chemistry
    source, parameter = obj("preparation.original"), obj("parameter.original")
    sources = tuple(sorted({study.cases.identity, source, parameter, chemistry.identity,
        *study.cases.sources, *chemistry.sources}, key=lambda row: row.object_id))
    molecular = MolecularPreparationSelection("preparation.exposed.comparison", study.cases, (chemistry,), (parameter,),
        source, D("298.15"), sources, ())
    census = assess_preparation_census(molecular, tuple(RetainedPreparationMember(slot, "NOT_ENTERED", None, None, ())
        for slot in molecular.slots), (), census_id="census.exposed.comparison")
    target = assess_reduction_target(report(study), assessment_id="target.exposed.comparison")
    prepared = prepare_response_comparison(selected, execution=execution(), molecular_preparation=census, target_assessment=target)
    codes = {row.code for row in prepared.native_entry_prerequisites}
    assert "rubisco.comparison.preparation-census" not in codes and "rubisco.comparison.target-assessment" not in codes
    assert "rubisco.comparison.active-state-and-reference" in codes and "rubisco.comparison.justified-supplier" in codes
    assert prepared.molecular_preparation == census and prepared.target_assessment == target
    other = assess_reduction_target(report(selected.original_study), assessment_id="target.other.criteria")
    with pytest.raises(ValueError, match="different scientific selections"):
        prepare_response_comparison(selected, execution=execution(), target_assessment=other)


def test_actual_work_cost_selection_requires_complete_science_and_equal_audit_burden():
    selected = design()
    draft = response_draft(selected.original_study, selected.study)
    work = scientific_work(draft, "rubisco-response.predict")
    allocation = ComparisonWorkAllocation(work, "AUDIT", COST_ARMS)
    assert replace(selected, cost_work=(allocation,)).cost_work == (allocation,)
    with pytest.raises(ValueError, match="same burden"):
        replace(allocation, charged_arms=("reduced",))
    with pytest.raises(ValueError, match="complete selected scientific operands"):
        replace(selected, cost_work=(replace(allocation, work=replace(work, scientific_operands=(obj("unrelated"),))),))
    with pytest.raises(ValueError, match="repeats"):
        replace(selected, cost_work=(allocation, allocation))
