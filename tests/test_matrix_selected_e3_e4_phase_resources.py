# SPDX-License-Identifier: MPL-2.0
"""Configured phase reservations; no native workload sizing or authority claim."""

from tests.matrix_e4_structure_support import disclosed_structure
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_experiment as public
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_selected_e3_e4_bridge import (
    selected_bridge, transfer, disclosed_operational_resources,  # noqa: F401 - disclosed fixture
)


@pytest.mark.parametrize("damage", ("missing", "extra", "ceiling"))
def test_phase_config_requires_exact_complete_supported_reservations(damage):
    selection = disclosed_operational_resources()
    phases = selection.phase_budgets
    if damage == "missing":
        phases = phases[:-1]
    elif damage == "extra":
        phases = tuple(sorted((*phases, ("undeclared-phase", phases[0][1]))))
    else:
        phases = ((phases[0][0], replace(phases[0][1], cpu_cores=owner.BUDGET.cpu_cores + 1)), *phases[1:])
    with pytest.raises(ValueError, match="complete exact phase census"):
        replace(selection, phase_budgets=phases)


def test_public_input_binding_derives_every_task_without_operator_task_ids(selected_bridge):  # noqa: F811
    f, campaign = selected_bridge, campaign_fixture()[0].campaign
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    spec = public.SelectedE3E4ExperimentSpecification("experiment.selected-e4.phase-reservations",
        f.programme.identity, f.bank.identity, f.evidence.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign),
        *disclosed_structure(f.bank, budget=dict(disclosed_operational_resources().phase_budgets)["collect"]))
    resources = disclosed_operational_resources()
    cold = decode_canonical_bytes(resources.canonical_bytes(), type(resources), maximum_bytes=None)
    records = {"programme": f.programme, "bank": f.bank, "evidence": f.evidence, "campaign": campaign, "resources": cold, "secondary_readout": f.secondary_readout}
    bound = public.bind_inputs(spec, records)
    tasks = owner.operational_tasks(f.programme, f.bank, evidence=f.evidence)
    budgets = dict(bound.method_inputs.operational_budgets)
    assert set(budgets) == {task for task, _ in tasks}
    assert all(budgets[task] == dict(resources.phase_budgets)[phase] for task, phase in tasks)
    assert resources in (records["resources"],)
    assert public.SelectedE3E4OperationalSelection in public.input_record_types()
    first = next(iter(budgets))
    budgets[first] = replace(budgets[first], memory_bytes=budgets[first].memory_bytes + 1)
    with pytest.raises(ValueError, match="explicit phase selection"):
        public.select_operational_budgets(bound.method_inputs, budgets)
    absent = public.bind_inputs(spec, {key: value for key, value in records.items() if key != "resources"})
    assert not absent.method_inputs.operational_budgets


def test_resources_configuration_validates_standalone_without_preparation(tmp_path, monkeypatch):
    from pathlib import Path
    from empirical_lawhood.api.configuration import validate_configuration
    assert tmp_path.resolve().is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    selection = disclosed_operational_resources()
    path = tmp_path / "resources.json"
    path.write_bytes(selection.canonical_bytes())
    monkeypatch.setattr(public, "prepare", lambda *_args, **_kwargs: pytest.fail("config validation entered preparation"))
    monkeypatch.setattr(owner, "operational_tasks", lambda *_args, **_kwargs: pytest.fail("config validation entered scientific source projection"))
    report = validate_configuration(path, consumer="matrix-selected-e3-e4-resources")
    assert report["status"] == "VALIDATED" and report["consumer_byte_ready"]
