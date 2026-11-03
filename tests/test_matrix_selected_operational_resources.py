# SPDX-License-Identifier: MPL-2.0
"""Explicit resources through copied public inputs and cold selected E5/E6 graphs."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_bindings as opportunity_owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as public
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as protected_owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_operational_resources import MatrixSelectedOperationalResources
from empirical_lawhood.api.configuration import validate_configuration
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, PreparedExperimentFile
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_selected_entry_scope import entry_shape, source_case  # noqa: F401
from tests.test_matrix_selected_entry_v2 import v2_shape
from tests.test_matrix_selected_opportunity import opportunity, evidence_for  # noqa: F401
from tests.test_matrix_selected_package import reference
from tests.test_matrix_selected_protected import confirmation, transfer, root_inputs  # noqa: F401


def resources(family, *, memory=None):
    owner = opportunity_owner if family == "OPPORTUNITY" else protected_owner
    return MatrixSelectedOperationalResources("resources.exposed." + family.lower(), family,
        tuple((phase, ResourceBudget(1, memory, 0, None, None, None)) for phase in sorted(owner.PHASES)))


def prepared(opportunity, tmp_path, selected):  # noqa: F811
    from tests.test_matrix_selected_declarative_preparation import science, request, selection
    specification = science(opportunity)
    current = selection(specification, replace(request(opportunity), phase_resources=selected), opportunity)
    records = {"selection": current}
    bindings = []
    for key, record in sorted(records.items()):
        path = tmp_path / (key + ".json")
        path.write_bytes(record.canonical_bytes())
        bindings.append(ExperimentInputBinding(key, record.identity, path.name, path.stat().st_size))
    sources = ExperimentInputSelection("selection.resources.exposed", public.DEVELOPMENT_PROTOCOL_ID, tuple(bindings))
    path = tmp_path / "sources.json"
    path.write_bytes(sources.canonical_bytes())
    with pytest.raises(PermissionError, match="actual selected artifact writer"):
        load_experiment_inputs(specification, path)
    # Cold graph construction retains budgets and supplies no input authority.
    cold = decode_canonical_bytes((tmp_path / "selection.json").read_bytes(), type(current), maximum_bytes=None)
    bound = public.bind_inputs(specification, {"selection": cold})
    assert bound.method_inputs.selection.request.phase_resources == selected
    artifacts = dict(public.lower(specification, current).input_artifacts)
    files = tuple(sorted((name, PreparedExperimentFile(artifact, "1.0.0",
        Path("/not-contacted/preparation-only") / str(index), artifact.size_bytes))
        for index, (name, artifact) in enumerate(artifacts.items())))
    inputs = replace(bound.method_inputs, files=files)
    result = public.prepare(specification,
        scientific_inputs=bound.scientific_inputs, method_inputs=inputs,
        execution=ExecutionSelection(workers=4, environment_id="main-locked",
            source_snapshot=reference("source.resources.exposed", type(current.request.campaign)),
            output_root=str(tmp_path)))
    return specification, bound, inputs, result


def test_cold_resource_graph_preserves_budgets_and_refuses_tampering(opportunity, tmp_path):  # noqa: F811
    selected = resources("OPPORTUNITY", memory=8 * 1024**2)
    specification, _bound, _inputs, result = prepared(opportunity, tmp_path, selected)
    assert result.executable
    assert {row.resource_budget.memory_bytes for row in result.draft.operations} == {8 * 1024**2}
    public.validate_instance(specification=specification, allocation=result.allocation,
        draft=result.draft, source_records=result.design_records)
    first = result.draft.operations[0]
    changed = replace(first, resource_budget=replace(first.resource_budget, memory_bytes=9 * 1024**2))
    with pytest.raises(ValueError, match="graph"):
        public.validate_instance(specification=specification, allocation=result.allocation,
            draft=replace(result.draft, operations=(changed, *result.draft.operations[1:])),
            source_records=result.design_records)


def test_missing_current_derivation_refuses_before_lowering_and_retains_full_requested_census(opportunity, tmp_path, monkeypatch):  # noqa: F811
    specification, _bound, _inputs, original = prepared(opportunity, tmp_path, resources("OPPORTUNITY"))
    monkeypatch.setattr(public, "lower", lambda *a, **k: pytest.fail("missing current derivation reached lowering"))
    result = public.prepare(specification,
        scientific_inputs={}, method_inputs=None,
        execution=original.execution)
    assert result.draft is None and not result.executable
    assert "matrix.selected-declarative.derivation" in {row.code for row in result.dependencies}
    assert result.census.role_counts == original.census.role_counts
    assert dict(result.census.resolved_role_counts) == {"groups": 0, "sources": 0}


@pytest.mark.parametrize("version", ("original", "development-nomination-v2"))
def test_protected_lowering_uses_every_explicit_phase_budget_and_preserves_original_science(transfer, confirmation, source_case, version):  # noqa: F811
    programme = transfer if version == "original" else confirmation
    from tests.matrix_selected_commitment_fixture import unpublished_committed_evidence
    from tests.test_matrix_selected_declarative_preparation import disclosed_produced_parents
    original = entry_shape(programme, source_case[0]) if version == "original" else v2_shape(programme, source_case[0])
    evidence = unpublished_committed_evidence(original)
    parents = disclosed_produced_parents(evidence.upstream_products,
        () if evidence.development_nomination is None else (evidence.development_nomination,))
    arguments = root_inputs(programme)
    campaign = campaign_fixture()[0].campaign
    kwargs = {"root": arguments["root"], "campaign": campaign, "draft_id": "draft.resources.exposed", "entry_evidence": evidence, "produced_input_parents": parents}
    legacy = protected_owner.lower_selected_protected_programme(programme, **kwargs)
    selected = resources("PROTECTED", memory=16 * 1024**2)
    explicit = protected_owner.lower_selected_protected_programme(programme, **kwargs, resources=selected)
    assert explicit.input_records == legacy.input_records and explicit.input_artifacts == legacy.input_artifacts
    assert explicit.draft.links == legacy.draft.links and explicit.draft.external_inputs == legacy.draft.external_inputs
    assert len(explicit.draft.operations) == len(legacy.draft.operations)
    assert all(new.resource_budget.memory_bytes == 16 * 1024**2 for new in explicit.draft.operations)
    assert all(replace(new, resource_budget=old.resource_budget) == old
        for new, old in zip(explicit.draft.operations, legacy.draft.operations, strict=True))
    with pytest.raises(ValueError, match="different operation family"):
        protected_owner.lower_selected_protected_programme(programme, **kwargs, resources=resources("OPPORTUNITY"))


@pytest.mark.parametrize("family", ("OPPORTUNITY", "PROTECTED"))
def test_declared_resource_consumer_validates_typed_values_without_authority(tmp_path, family):
    consumer = "matrix-selected-phase-resources"
    path = tmp_path / "resources.json"
    path.write_bytes(resources(family).canonical_bytes())
    result = validate_configuration(path, consumer=consumer)
    assert result["status"] == "VALIDATED"
    assert result["authority_granted"] is result["external_prerequisites_checked"] is False


@pytest.mark.parametrize("damage", ("missing-phase", "duplicate-phase", "foreign-phase", "cpu-bool", "memory-bool", "exceeds-ceiling", "untyped"))
def test_phase_selection_refuses_ambiguous_or_unsupported_operational_parameters(damage):
    selected = resources("OPPORTUNITY")
    rows = list(selected.phase_budgets)
    if damage == "missing-phase":
        rows.pop()
    elif damage == "duplicate-phase":
        rows[-1] = rows[0]
    elif damage == "foreign-phase":
        rows[-1] = ("uninstalled-phase", rows[-1][1])
    else:
        phase, budget = rows[0]
        if damage == "untyped":
            budget = object()
        else:
            budget = replace(budget, **({"cpu_cores": True} if damage == "cpu-bool" else
                {"memory_bytes": True} if damage == "memory-bool" else {"cpu_cores": 2}))
        rows[0] = phase, budget
    with pytest.raises((TypeError, ValueError)):
        replace(selected, phase_budgets=tuple(rows))


def test_shared_resource_consumer_is_registered_once_and_each_workflow_enforces_its_family(opportunity):  # noqa: F811
    from empirical_lawhood.api import configuration_registry
    from tests.test_matrix_selected_declarative_preparation import science, request, selection

    consumers = tuple(configuration_registry.CONSUMERS)
    selected = tuple(value for value in consumers if value.consumer == "matrix-selected-phase-resources")
    assert len(selected) == 1
    assert len(selected[0].supplied_inputs) == 2
    with pytest.raises(ValueError, match="different operation family"):
        specification = science(opportunity)
        current = selection(specification, replace(request(opportunity), phase_resources=resources("PROTECTED")), opportunity)
        public.lower(specification, current)
    # The independent protected lowerer retains its own exact resource family.
    with pytest.raises(ValueError, match="different operation family"):
        resources("OPPORTUNITY").for_family("PROTECTED")


@pytest.mark.parametrize("damage", ("different-bound", "base-consumer-collision"))
def test_shared_input_consumer_reuse_refuses_conflicting_owners(monkeypatch, damage):
    from empirical_lawhood.api import configuration_registry, experiment_preparation
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import extension_bundle

    owners = tuple(value for value in extension_bundle.EXPERIMENT_PROTOCOL_DECLARATIONS if value.configuration_inputs)
    first, second = owners[:2]
    selected, = (value for value in second.configuration_inputs if value.consumer_id == "matrix-selected-phase-resources")
    if damage == "different-bound":
        selected = replace(selected, maximum_config_bytes=selected.maximum_config_bytes + 1)
    else:
        selected = replace(selected, consumer_id=configuration_registry._BASE_CONSUMERS[0].consumer)
    changed = replace(second, configuration_inputs=tuple(selected if value.consumer_id == "matrix-selected-phase-resources"
        else value for value in second.configuration_inputs))
    monkeypatch.setattr(experiment_preparation, "experiment_protocols", lambda: (first, changed))
    with pytest.raises(ValueError, match="conflict"):
        configuration_registry._configuration_consumers()
