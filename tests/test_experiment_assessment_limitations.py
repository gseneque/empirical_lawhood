# SPDX-License-Identifier: MPL-2.0
"""Outcome-limit classification controls; no scientific execution or authority."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial_confirmation import ScheduledFactorialCriteriaBinding
from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import prepare_protected_factorial_experiment
from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_specification import (
    ProtectedFactorialAcquisitionRoster,
    ProtectedFactorialExperimentSpecification,
)
from empirical_lawhood.api.experiment_preparation import author_prepared_experiment, experiment_preparation_report
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_entry import StudyDefinition
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind,
    ExecutionSelection,
    ExperimentCensus,
    ExperimentDependency,
    ExperimentPreparation,
)


ROOT = Path(__file__).resolve().parents[1]


def _limitation(code="assessment.sampling"):
    return ExperimentDependency(code, DependencyKind.SCIENTIFIC_EVIDENCE,
        "UNEVALUABLE: SAMPLING_ASSUMPTION_NOT_AUTHENTICATED", "source.selected")


@pytest.fixture
def preparation():
    # This existing exposed draft supplies typed graph structure only. These
    # metadata controls do not authorize or run any of its operations.
    payload = (ROOT / "programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/draft.json").read_bytes()
    draft = decode_canonical_bytes(payload, RecursiveStudyDraft, maximum_bytes=len(payload))
    source = ObjectIdentity("source.exposed-fixture", "empirical-lawhood/testing/source", "1.0.0", "a" * 64)
    allocation = UnitAllocation("allocation.exposed-fixture", (source,),
        (IndependentUnit("unit.exposed", source.object_id, "family.fixture", ("view.original",), True),),
        (UnitRoleAssignment("unit.exposed", "exposed"),))
    census = ExperimentCensus((("exposed", 1),), (("exposed", 1),), (("assessment", 1),), (("report", 1),), 0)
    return ExperimentPreparation(source, census, (), allocation, draft, execution=ExecutionSelection(workers=1))


def test_expected_unevaluable_assessment_limit_does_not_block_pure_preparation(preparation):
    original = (preparation.draft.canonical_bytes(), preparation.allocation.canonical_bytes())
    assert preparation.assessment_limitations == ()
    assert experiment_preparation_report(preparation)["assessment_limitations"] == []
    limitation = _limitation()
    prepared = replace(preparation, assessment_limitations=(limitation,))
    report = experiment_preparation_report(prepared)
    assert prepared.executable and report["executable"]
    assert report["dependencies"] == []
    assert report["assessment_limitations"] == [{"code": limitation.code, "kind": "SCIENTIFIC_EVIDENCE",
        "detail": limitation.detail, "source_key": limitation.source_key}]
    assert (prepared.draft.canonical_bytes(), prepared.allocation.canonical_bytes()) == original
    assert report["scientific_execution_performed"] is False
    assert report["scientific_authority"] == "NONE"


@pytest.mark.parametrize("kind", tuple(DependencyKind))
def test_every_actual_entry_dependency_still_blocks_with_outcome_limit(preparation, kind, tmp_path):
    dependency = ExperimentDependency("entry.missing", kind, "The actual entry prerequisite is unavailable.")
    blocked = replace(preparation, dependencies=(dependency,), assessment_limitations=(_limitation(),))
    report = experiment_preparation_report(blocked)
    assert not blocked.executable and not report["executable"]
    assert blocked.dependencies == (dependency,)
    assert report["dependencies"][0]["kind"] == kind.value
    with pytest.raises(ValueError, match="experiment authoring retains unresolved prerequisites"):
        author_prepared_experiment(preparation=blocked, project_root=tmp_path,
            artifact_writer=object(), output_dir=tmp_path / "uncreated")
    assert not tuple(tmp_path.iterdir())


@pytest.mark.parametrize("kind", tuple(kind for kind in DependencyKind if kind is not DependencyKind.SCIENTIFIC_EVIDENCE))
def test_entry_kinds_cannot_be_reclassified_as_assessment_limitations(preparation, kind):
    dependency = ExperimentDependency("entry.missing", kind, "Still a required entry prerequisite.")
    with pytest.raises(ValueError, match="only scientific-evidence outcome limits"):
        replace(preparation, assessment_limitations=(dependency,))


class _DependencySubclass(ExperimentDependency):
    pass


class _TupleSubclass(tuple):
    pass


@pytest.mark.parametrize("rows", (
    [_limitation()],
    _TupleSubclass((_limitation(),)),
    ({"code": "untyped", "kind": "SCIENTIFIC_EVIDENCE"},),
    (_DependencySubclass("assessment.subclass", DependencyKind.SCIENTIFIC_EVIDENCE, "Outcome limit."),),
    (_limitation(), _limitation()),
    (_limitation("assessment.z"), _limitation("assessment.a")),
))
def test_assessment_limitations_require_exact_sorted_unique_typed_tuple(preparation, rows):
    with pytest.raises(ValueError, match="exact typed, sorted and uniquely identified"):
        replace(preparation, assessment_limitations=rows)


def test_outcome_limitation_does_not_supply_a_missing_graph(preparation):
    incomplete = replace(preparation, draft=None, assessment_limitations=(_limitation(),))
    assert not incomplete.executable


def test_protected_partial_preparation_keeps_all_missing_entry_facts_separate():
    # Exact type/revision references are unresolved metadata, not fabricated
    # original source records, scientific evidence or qualifying authorities.
    def reference(name, record_type, digest):
        return ObjectIdentity(name, record_type.SCHEMA, record_type.VERSION, digest * 64)

    specification = ProtectedFactorialExperimentSpecification("specification.unresolved",
        reference("original.unresolved", StudyDefinition, "a"),
        reference("criteria.unresolved", ScheduledFactorialCriteriaBinding, "b"),
        reference("acquisitions.unresolved", ProtectedFactorialAcquisitionRoster, "c"),
        "Assess the unchanged original protected confirmation selection.")
    original_bytes = specification.canonical_bytes()
    prepared = prepare_protected_factorial_experiment(specification, scientific_inputs={}, execution=ExecutionSelection())
    assert not prepared.executable and prepared.draft is None
    assert {(row.code.removeprefix("matrix.protected-factorial."), row.kind) for row in prepared.dependencies} == {
        ("original.missing", DependencyKind.EXTERNAL_INPUT),
        ("preparation.missing", DependencyKind.EXTERNAL_INPUT),
        ("environment.missing", DependencyKind.ENVIRONMENT),
        ("output-root.missing", DependencyKind.STORAGE),
        ("source-snapshot.missing", DependencyKind.ENVIRONMENT),
        ("owning-api-composition", DependencyKind.SOFTWARE),
        ("resource-projection", DependencyKind.SOFTWARE),
    }
    limitation, = prepared.assessment_limitations
    assert limitation.code == "matrix.protected-factorial.sampling-warrant"
    assert limitation.kind is DependencyKind.SCIENTIFIC_EVIDENCE
    assert "UNEVALUABLE: SAMPLING_ASSUMPTION_NOT_AUTHENTICATED" in limitation.detail
    assert specification.canonical_bytes() == original_bytes
    assert prepared.census.role_counts == (("acquisition-waves", 16), ("comparison-family-slots", 12),
        ("independent-groups", 64), ("paired-cases", 576))
    assert prepared.census.native_effect_count == 0
