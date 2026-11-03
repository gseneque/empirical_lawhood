# SPDX-License-Identifier: MPL-2.0
"""Independent public E4 editing/association checks over exposed metadata only.

No worker, native contact, publication, genuine source qualification or large
source-file copy occurs. Synthetic original-shaped programme/data pins remain
explicit software fixtures; a dependency-free preparation is not scientific
eligibility or actual-worker readiness.
"""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import experiment_preparation as public, load_authoring
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_selection as method
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selection_preparation as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selection_specification import (
    RevisionCandidateSelection, ScheduledRevisionExperimentSpecification, derive_revision_specification,
)
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection
from tests.test_matrix_programme_selection import exposed as exposed_builder, pin


ROOT = Path(__file__).parents[1]


def _outer(exposed):
    original = exposed.specification
    tunings = {row.identity: row for row in original.tunings}
    return ScheduledRevisionExperimentSpecification("experiment.exposed-e4-editable", original.programme,
        original.target, original.trigger, original.revision_design.folds, original.revision_design.fold_count,
        original.revision_design.maximum_fit_calls,
        tuple(RevisionCandidateSelection(row.candidate_id, tunings[row.tuning]) for row in original.revision_design.candidates),
        tuple(RevisionCandidateSelection(row.candidate_id, tunings[row.tuning]) for row in original.baseline_design.candidates),
        original.revision_design.tie_order, original.baseline_design.tie_order)


@pytest.fixture(scope="module")
def case():
    exposed = exposed_builder.__wrapped__()
    campaign = replace(load_authoring(ROOT/"tests/fixtures/reference-campaign.json").campaign,
        budget=method.operation_declarations()[0].resources)
    return SimpleNamespace(exposed=exposed, specification=_outer(exposed), records={"campaign": campaign,
        "programme": exposed.programme, "reduction": exposed.reduction, "data": exposed.data})


@pytest.fixture(autouse=True)
def no_effects(monkeypatch):
    from empirical_lawhood.api import recursive_authoring
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    def forbidden(*args, **kwargs):
        pytest.fail("pure E4 preparation entered fitting, custody publication or actual workers")
    monkeypatch.setattr(method, "fit_standardized_ridge", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "preflight", forbidden)
    monkeypatch.setattr(recursive_authoring, "author_recursive_wave", forbidden)
    monkeypatch.setattr(recursive_authoring, "implementation_binding", forbidden)


def _execution():
    # Explicit selectors for a pure compilation fixture, not runtime observations.
    return ExecutionSelection(workers=1, environment_id="fixture.locked-main", source_snapshot=pin("snapshot.exposed"),
        output_root="/explicit/unentered-e4-preparation-fixture")


def _prepare(specification, records, *, execution=None, **kwargs):
    resolved = owner.bind_selection_inputs(specification, records)
    return public.prepare_experiment(specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=execution or _execution(), **kwargs)


def _dependencies(preparation):
    return {row.code.removeprefix("matrix.e4.selection."): row for row in preparation.dependencies}


def test_installed_public_protocol_and_specification_decode_are_cold(case, tmp_path, monkeypatch):
    protocol, = (row for row in public.experiment_protocols() if row.protocol_id == owner.PROTOCOL_ID)
    assert protocol.specification_type is ScheduledRevisionExperimentSpecification
    assert protocol.consumer_id == "matrix-e4-declared-selection"
    assert set(protocol.input_record_types) == set(owner.INPUT_TYPES.values())
    def forbidden(*args, **kwargs):
        pytest.fail("cold discovery or configuration decode prepared scientific evidence")
    monkeypatch.setattr(owner, "_scientific_selection", forbidden)
    for specification in (case.specification, replace(case.specification, trigger=replace(case.specification.trigger, threshold=Decimal(100)))):
        path = tmp_path/(specification.fingerprint()+".json")
        path.write_bytes(specification.canonical_bytes())
        assert public.load_experiment_specification(path) == specification
        assert decode_canonical_bytes(path.read_bytes(), ScheduledRevisionExperimentSpecification, maximum_bytes=None) == specification


def test_single_embedded_penalty_and_trigger_edits_derive_all_internal_hashes_without_changing_sources(case):
    original = case.specification
    changed_penalty = replace(original, revision_candidates=(replace(original.revision_candidates[0],
        tuning=replace(original.revision_candidates[0].tuning, penalty=Decimal(2))), *original.revision_candidates[1:]))
    changed_trigger = replace(original, trigger=replace(original.trigger, threshold=Decimal(100)))
    preparations = tuple(_prepare(specification, case.records) for specification in (original, changed_penalty, changed_trigger))
    original_source_identities = {key: (record.SCHEMA, record.fingerprint()) for key, record in case.records.items()}
    allocation = preparations[0].allocation
    for specification, preparation in zip((original, changed_penalty, changed_trigger), preparations, strict=True):
        assert preparation.executable and preparation.dependencies == ()
        assert preparation.specification_record is specification and preparation.specification == specification.identity
        assert preparation.allocation == allocation and len(allocation.units) == 32
        assert all(unit.numerical_view_ids == ("fine", "primary") and unit.exposed for unit in allocation.units)
        assert dict(preparation.census.role_counts) == dict(preparation.census.resolved_role_counts) == {"development-groups": 32}
        assert dict(preparation.census.output_counts)["assigned-cases"] == 288
        assert dict(preparation.census.output_counts)["paired-targets-per-case"] == 30
        assert dict(preparation.census.operation_counts) == {"freeze-revision": 1, "select-revision": 1}
        assert preparation.census.native_effect_count == 0
        assert len(preparation.input_records) == 4 and len(preparation.design_records) == 4
        inner = derive_revision_specification(specification, case.exposed.programme)
        configs = tuple(decode_canonical_bytes(row.config_payload.encode(), method.ScheduledRevisionOperationConfig,
            maximum_bytes=None) for row in preparation.draft.operations)
        assert all(config.specification == inner for config in configs)
        assert all(config.reduction == case.exposed.data.reduction and config.data == case.exposed.data.identity for config in configs)
        assert owner.validate_selection_experiment_instance(specification=specification, allocation=preparation.allocation,
            draft=preparation.draft, source_records=preparation.design_records) is None
    first, penalty, trigger = preparations
    assert {row.node_id for row in first.draft.operations}.isdisjoint(row.node_id for row in penalty.draft.operations)
    assert first.allocation.identity == penalty.allocation.identity == trigger.allocation.identity
    assert {key: (record.SCHEMA, record.fingerprint()) for key, record in case.records.items()} == original_source_identities
    inner = derive_revision_specification(changed_penalty, case.exposed.programme)
    assert inner.revision_design.candidates[0].tuning == changed_penalty.revision_candidates[0].tuning.identity
    assert changed_penalty.revision_candidates[0].tuning.penalty == Decimal(2)
    assert inner.baseline_design.candidates == derive_revision_specification(original, case.exposed.programme).baseline_design.candidates


def test_all_original_inputs_and_execution_dependencies_are_reported_together(case):
    preparation = public.prepare_experiment(case.specification)
    findings = _dependencies(preparation)
    assert set(findings) == {"campaign.missing", "programme.missing", "reduction.missing", "data.missing",
        "environment", "source-snapshot", "output-root", "experiment.workers"}
    assert {key: row.source_key for key, row in findings.items() if key.endswith(".missing")} == {
        key+".missing": key for key in owner.INPUT_TYPES}
    assert all(findings[key+".missing"].kind is DependencyKind.EXTERNAL_INPUT for key in owner.INPUT_TYPES)
    assert findings["environment"].kind is findings["source-snapshot"].kind is DependencyKind.ENVIRONMENT
    assert findings["output-root"].kind is DependencyKind.STORAGE
    assert not preparation.executable and preparation.draft is None and not preparation.input_records
    assert dict(preparation.census.role_counts) == {"development-groups": 32}
    assert dict(preparation.census.resolved_role_counts) == {"development-groups": 0}
    report = public.experiment_preparation_report(preparation)
    assert report["scientific_authority"] == "NONE" and report["qualification"] == "NOT_ESTABLISHED"
    assert report["native_contact"] == "NONE" and not report["scientific_execution_performed"]


def test_missing_campaign_does_not_hide_known_incompatible_original_science(case):
    records = {key: value for key, value in case.records.items() if key != "campaign"}
    records["data"] = replace(records["data"], programme=replace(records["data"].programme, object_fingerprint="f"*64))
    resolved = owner.bind_selection_inputs(case.specification, records)
    prepared = public.prepare_experiment(case.specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs)
    findings = _dependencies(prepared)
    assert {"campaign.missing", "original-data.invalid", "environment", "source-snapshot", "output-root"} <= set(findings)
    assert findings["original-data.invalid"].kind is DependencyKind.SCIENTIFIC_EVIDENCE
    assert not prepared.executable and prepared.draft is None
    assert dict(prepared.census.resolved_role_counts) == {"development-groups": 32}
    assert dict(prepared.census.output_counts)["assigned-cases"] == 288


@pytest.mark.parametrize("damage", ("selected-programme", "data-programme", "reduction-programme", "score-association"))
def test_original_source_mismatches_remain_dependencies_before_execution(case, damage):
    specification, records = case.specification, dict(case.records)
    if damage == "selected-programme":
        specification = replace(specification, programme=replace(specification.programme, object_fingerprint="f"*64))
    elif damage == "data-programme":
        records["data"] = replace(records["data"], programme=replace(records["data"].programme, object_fingerprint="f"*64))
    elif damage == "reduction-programme":
        records["reduction"] = replace(records["reduction"], programme=replace(records["reduction"].programme, object_fingerprint="f"*64))
    else:
        row = records["data"].cases[0]
        changed = replace(row, score=replace(row.score, criterion=replace(row.score.criterion, object_fingerprint="f"*64)))
        records["data"] = replace(records["data"], cases=(changed, *records["data"].cases[1:]))
    prepared = _prepare(specification, records)
    assert not prepared.executable and prepared.draft is None and not prepared.input_records
    assert any(row.kind is DependencyKind.SCIENTIFIC_EVIDENCE for row in prepared.dependencies)
    assert dict(prepared.census.resolved_role_counts) == {"development-groups": 32}
    assert dict(prepared.census.output_counts)["assigned-cases"] == 288


def test_invalid31_selected_folds_keeps_actual32_groups_and288_cases(case):
    specification = replace(case.specification, folds=case.specification.folds[:-1])
    prepared = _prepare(specification, case.records)
    assert "programme.invalid" in _dependencies(prepared)
    assert not prepared.executable and prepared.draft is None
    assert dict(prepared.census.role_counts) == {"development-groups": 31}
    assert dict(prepared.census.resolved_role_counts) == {"development-groups": 32}
    assert dict(prepared.census.output_counts)["assigned-cases"] == 288


@pytest.mark.parametrize("phase", ("E4_REVISION_CALIBRATION", "E4_CONFIRMATION"))
def test_future_population_cannot_relabel_original32_development_groups(case, phase):
    # The original owning record refuses this count/phase substitution; no
    # invented64-group bank is needed to demonstrate the negative boundary.
    with pytest.raises(ValueError, match="global|case|role|denominator"):
        programme = replace(case.exposed.programme, mode=phase)
        owner.bind_selection_inputs(case.specification, {**case.records, "programme": programme})


@pytest.mark.parametrize("key", ("calibration", "future", "undeclared"))
def test_undeclared_scientific_input_keys_refuse(case, key):
    with pytest.raises(ValueError, match="four declared original input keys"):
        owner.bind_selection_inputs(case.specification, {**case.records, key: case.exposed.data})


def test_wrong_input_type_and_extra_protocol_override_cannot_become_executable(case):
    with pytest.raises(TypeError, match="wrong closed type"):
        owner.bind_selection_inputs(case.specification, {**case.records, "data": case.exposed.reduction})
    prepared = _prepare(case.specification, case.records, protocol_bytes=b"{}")
    assert not prepared.executable and "unselected-protocol" in _dependencies(prepared)


def test_original_source_ids_cannot_alias_and_hide_dependency_in_design_records(case):
    campaign = replace(case.records["campaign"], campaign_id=case.exposed.programme.programme_id)
    prepared = _prepare(case.specification, {**case.records, "campaign": campaign})
    assert not prepared.executable and "original-source-alias" in _dependencies(prepared)
    assert prepared.design_records == ()


@pytest.mark.parametrize("damage", ("draft", "specification", "data", "campaign", "allocation", "missing-source", "duplicate-source"))
def test_instance_validation_refuses_decoupled_specification_sources_allocation_or_graph(case, damage):
    specification = case.specification
    prepared = _prepare(specification, case.records)
    allocation, draft, source_records = prepared.allocation, prepared.draft, prepared.design_records
    if damage == "draft":
        draft = replace(draft, question="A changed query without its derived scientific graph")
    elif damage == "specification":
        specification = replace(specification, trigger=replace(specification.trigger, threshold=Decimal(100)))
    elif damage == "data":
        data = replace(case.exposed.data, programme=replace(case.exposed.data.programme, object_fingerprint="f"*64))
        source_records = tuple((key, data if type(record) is owner.ScheduledRevisionDataBank else record) for key, record in source_records)
    elif damage == "campaign":
        campaign = replace(case.records["campaign"], budget=ResourceBudget(2, None, 0, None, None, None))
        source_records = tuple((key, campaign if type(record) is owner.CampaignSpec else record) for key, record in source_records)
    elif damage == "allocation":
        allocation = replace(allocation, allocation_id="allocation.foreign")
    elif damage == "missing-source":
        source_records = source_records[:-1]
    else:
        source_records = (*source_records, source_records[-1])
    with pytest.raises((ValueError, TypeError), match="E4|selection|instance|original|source|allocation"):
        owner.validate_selection_experiment_instance(specification=specification, allocation=allocation,
            draft=draft, source_records=source_records)
