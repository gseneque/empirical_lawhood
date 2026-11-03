# SPDX-License-Identifier: MPL-2.0
"""Specification editing and immutable association, using exposed metadata only."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import experiment_preparation as public, load_authoring
from empirical_lawhood.adapters.methods.matrix_scheduled_history import factorial_preparation as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial as method
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection
from empirical_lawhood.runtime.experimental_factorial import PairInteractionScale
from tests.test_matrix_programme_factorial import exposed as exposed_builder, polynomial as polynomial_builder
from tests.test_matrix_programme_selection import pin

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def case():
    exposed = exposed_builder.__wrapped__()
    polynomial = polynomial_builder.__wrapped__(exposed)
    campaign = replace(load_authoring(ROOT/"tests/fixtures/reference-campaign.json").campaign,
        budget=method.operation_declarations()[0].resources)
    return SimpleNamespace(specification=polynomial.factorial_specification, records={"campaign": campaign,
        "programme": polynomial.programme, "reduction": polynomial.reduction, "data": polynomial.data})


@pytest.fixture(autouse=True)
def no_effects(monkeypatch):
    from empirical_lawhood.api import recursive_authoring
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor

    def forbidden(*args, **kwargs):
        pytest.fail("pure factorial preparation entered assessment, custody publication or an actual worker")

    monkeypatch.setattr(method, "assess_programme_factorial", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "preflight", forbidden)
    monkeypatch.setattr(recursive_authoring, "author_recursive_wave", forbidden)
    monkeypatch.setattr(recursive_authoring, "implementation_binding", forbidden)


def _execution():
    return ExecutionSelection(workers=1, environment_id="fixture.locked-main", source_snapshot=pin("snapshot.exposed"),
        output_root="/explicit/unentered-factorial-preparation")


def _prepare(specification, records):
    resolved = owner.bind_factorial_inputs(specification, records)
    return public.prepare_experiment(specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=_execution())


def test_installed_factorial_protocol_uses_editable_method_specification_and_existing_four_sources(case, tmp_path):
    protocol, = (row for row in public.experiment_protocols() if row.protocol_id == owner.PROTOCOL_ID)
    assert protocol.specification_type is method.ScheduledFactorialSpecification
    assert set(protocol.input_record_types) == set(owner.INPUT_TYPES.values())
    path = tmp_path/"factorial-selection.json"
    path.write_bytes(case.specification.canonical_bytes())
    assert public.load_experiment_specification(path) == case.specification


def test_edits_derive_configurations_and_complete_graph_without_changing_original_sources(case):
    original = case.specification
    changed_null = replace(original, comparisons=tuple(replace(row, null_value=Decimal(".01")) for row in original.comparisons))
    changed_scale = replace(original, pair_scale=PairInteractionScale.DIFFERENCE_OF_DIFFERENCES, alpha=Decimal(".1"))
    before = {key: record.fingerprint() for key, record in case.records.items()}
    preparations = tuple(_prepare(specification, case.records) for specification in (original, changed_null, changed_scale))
    for specification, preparation in zip((original, changed_null, changed_scale), preparations, strict=True):
        assert preparation.executable and preparation.dependencies == ()
        assert preparation.specification_record is specification
        assert len(preparation.allocation.units) == 32
        assert all(row.exposed and row.numerical_view_ids == ("fine", "primary") for row in preparation.allocation.units)
        assert dict(preparation.census.role_counts) == {"development-groups": 32}
        assert dict(preparation.census.operation_counts) == {"factorial-assess": 1}
        assert dict(preparation.census.output_counts) == {"assigned-cases": 288, "conditional-tests": 7,
            "family-slots": 12, "paired-targets-per-case": 30, "retained-source-rows": 288}
        assert preparation.census.native_effect_count == 0
        assert len(preparation.draft.operations) == 1 and len(preparation.input_records) == len(preparation.design_records) == 4
        assert owner.validate_factorial_experiment_instance(specification=specification, allocation=preparation.allocation,
            draft=preparation.draft, source_records=preparation.design_records) is None
    assert len({row.draft.fingerprint() for row in preparations}) == 3
    assert len({row.draft.operations[0].node_id for row in preparations}) == 3
    assert all(row.allocation == preparations[0].allocation for row in preparations)
    assert {key: record.fingerprint() for key, record in case.records.items()} == before


@pytest.mark.parametrize("absent", (1, 9, 288))
def test_absent_source_rows_remain_executable_as_complete_assigned_unevaluable_denominators(case, absent):
    records = {**case.records, "data": replace(case.records["data"], cases=case.records["data"].cases[absent:])}
    preparation = _prepare(case.specification, records)
    assert preparation.executable and preparation.dependencies == ()
    assert len(preparation.allocation.units) == 32
    assert dict(preparation.census.output_counts)["assigned-cases"] == 288
    assert dict(preparation.census.output_counts)["retained-source-rows"] == 288-absent
    assert dict(preparation.census.output_counts)["family-slots"] == 12


@pytest.mark.parametrize("missing", tuple(owner.INPUT_TYPES))
def test_missing_original_record_stays_named_external_dependency(case, missing):
    preparation = _prepare(case.specification, {key: record for key, record in case.records.items() if key != missing})
    dependency, = (row for row in preparation.dependencies if row.code == "matrix.e4.factorial."+missing+".missing")
    assert dependency.kind is DependencyKind.EXTERNAL_INPUT and dependency.source_key == missing
    assert not preparation.executable and preparation.draft is None


def test_broken_source_join_remains_scientific_evidence_dependency(case):
    data = replace(case.records["data"], reduction=replace(case.records["data"].reduction, object_id="reduction.unrelated"))
    preparation = _prepare(case.specification, {**case.records, "data": data})
    assert not preparation.executable and preparation.draft is None
    assert any(row.kind is DependencyKind.SCIENTIFIC_EVIDENCE and row.source_key == "data" for row in preparation.dependencies)


def test_instance_cannot_substitute_a_different_design_or_omit_original_source(case):
    preparation = _prepare(case.specification, case.records)
    changed = replace(case.specification, alpha=Decimal(".1"))
    with pytest.raises(ValueError, match="decouples"):
        owner.validate_factorial_experiment_instance(specification=changed, allocation=preparation.allocation,
            draft=preparation.draft, source_records=preparation.design_records)
    with pytest.raises(ValueError, match="omits"):
        owner.validate_factorial_experiment_instance(specification=case.specification, allocation=preparation.allocation,
            draft=preparation.draft, source_records=preparation.design_records[1:])
