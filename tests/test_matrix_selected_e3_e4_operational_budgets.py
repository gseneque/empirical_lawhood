# SPDX-License-Identifier: MPL-2.0
"""Finite DEV budget projection controls; no native memory adequacy claim."""

from tests.matrix_e4_structure_support import disclosed_structure
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_experiment as public
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_selected_e3_e4_bridge import selected_bridge, transfer, disclosed_operational_budgets, disclosed_operational_resources  # noqa: F401 - disclosed metadata


def lower(f, budgets):
    return owner.lower_selected_e3_e4_development(f.programme, f.bank, evidence=f.evidence,
        campaign=campaign_fixture()[0].campaign, draft_id="draft.selected-e4.operational-budgets",
        operational_budgets=budgets, secondary_target=f.secondary_target, secondary_readout=f.secondary_readout)


def test_finite_selection_survives_actual_compiler_and_cold_draft(selected_bridge):  # noqa: F811
    f = selected_bridge
    selected = disclosed_operational_budgets(f)
    tasks = owner.operational_tasks(f.programme, f.bank, evidence=f.evidence)
    assert len(tasks) == 3458 and {phase for _, phase in tasks} == set(owner.PHASES)
    inputs = public.SelectedE3E4Inputs(f.programme, f.bank, f.evidence, campaign_fixture()[0].campaign, secondary_readout=f.secondary_readout)
    bound = public.select_operational_budgets(inputs, selected)
    assert not inputs.operational_budgets
    assert dict(bound.operational_budgets) == selected
    lowered = lower(f, selected)
    assert {value.node_id: value.resource_budget for value in lowered.draft.operations} == selected
    cold = decode_canonical_bytes(lowered.draft.canonical_bytes(), RecursiveStudyDraft, maximum_bytes=None)
    assert cold == lowered.draft
    declarations = owner.operation_declarations()
    registry = CapabilityRegistry("registry.selected-e4.budget-control", tuple(row.manifest() for row in declarations))
    compiled = compile_recursive_wave(draft=cold, registry=registry, registrations=tuple(row.registration() for row in declarations),
        implementation_commit="a" * 40, output_codecs={schema: kind for row in declarations for schema, kind in row.record_codecs.items()})
    assert {task.task_id: task.capability.requested_resources for task in compiled.execution_plan.tasks} == selected
    changed = dict(selected)
    node = tasks[0][0]
    changed[node] = replace(selected[node], memory_bytes=selected[node].memory_bytes + 1)
    changed_draft = lower(f, changed).draft
    assert changed_draft.fingerprint() != cold.fingerprint()
    assert tuple(value.config_identity for value in changed_draft.operations) == tuple(value.config_identity for value in cold.operations)
    assert changed_draft.development_study == cold.development_study


@pytest.mark.parametrize("damage", ("missing", "extra", "cpu-ceiling", "gpu-ceiling", "wrong-owner"))
def test_operational_selection_refuses_incomplete_or_outside_ceiling(selected_bridge, damage):  # noqa: F811
    f = selected_bridge
    selected = disclosed_operational_budgets(f)
    node = next(iter(selected))
    if damage == "missing":
        selected.pop(node)
    elif damage == "extra":
        selected["task.unselected-operational-budget"] = selected[node]
    elif damage == "cpu-ceiling":
        selected[node] = replace(selected[node], cpu_cores=owner.BUDGET.cpu_cores + 1)
    elif damage == "gpu-ceiling":
        selected[node] = replace(selected[node], gpu_devices=1)
    else:
        selected[node] = "asserted-budget"
    with pytest.raises((TypeError, ValueError), match="task census|capability ceiling"):
        lower(f, selected)
    inputs = public.SelectedE3E4Inputs(f.programme, f.bank, f.evidence, campaign_fixture()[0].campaign, secondary_readout=f.secondary_readout)
    with pytest.raises((TypeError, ValueError), match="task census|capability ceiling"):
        public.select_operational_budgets(inputs, selected)


def test_missing_operator_selection_is_a_dependency_before_authoring(selected_bridge):  # noqa: F811
    f, campaign = selected_bridge, campaign_fixture()[0].campaign
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    spec = public.SelectedE3E4ExperimentSpecification("experiment.selected-e4.missing-operational-budget",
        f.programme.identity, f.bank.identity, f.evidence.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign),
        *disclosed_structure(f.bank, budget=dict(disclosed_operational_resources().phase_budgets)["collect"]))
    inputs = public.SelectedE3E4Inputs(f.programme, f.bank, f.evidence, campaign, secondary_readout=f.secondary_readout)
    preparation = public.prepare(spec, scientific_inputs={"programme": public.allocation(f.programme)},
        execution=ExecutionSelection(), method_inputs=inputs)
    assert not preparation.executable and preparation.draft is None
    assert "matrix.selected-e4.operational-budgets" in {value.code for value in preparation.dependencies}
