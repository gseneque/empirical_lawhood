# SPDX-License-Identifier: MPL-2.0
"""Actual public file preparation/author/coldload; no scientific worker entry."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as owner, selected_e4_methods as science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_revision_preparation as public
from empirical_lawhood.api.experiment_preparation import author_prepared_experiment, load_experiment_inputs, prepare_experiment
from empirical_lawhood.api.recursive_authoring import implementation_binding, load_authored_wave
from empirical_lawhood.api.recursive_execution import _retained_plans
from empirical_lawhood.api.current_task_custody import CurrentDevelopmentTaskCustody
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, ExperimentInstanceBinding
from tests.test_matrix_selected_e4_methods import selected_revision, selected_e4_populations, selected_bridge, transfer, pin  # noqa: F401
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_selected_e4_revision_transition import _real_plane

ROOT = Path(__file__).resolve().parents[1]


def test_actual_public_files_prepare_author_coldload_and_runtime_binding(selected_revision, tmp_path):  # noqa: F811
    f = selected_revision
    # This supported researcher edit is frozen into actual authored config and
    # independently replayed on cold load, without running a scientific worker.
    editable = replace(f.editable, trigger=replace(f.editable.trigger, threshold=Decimal("999")))
    assert editable != f.editable
    selected_root = tmp_path / "selected-e4-revision-public"
    assert selected_root.resolve().is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    writer = _real_plane(selected_root)
    resources = owner.SelectedE4MethodResources("resources.public", tuple((phase, ResourceBudget(1, 1024**3, 0, None, None, None))
        for phase in ("revision-fit", "revision-freeze")))
    acquisition = owner.SelectedE4DevelopmentAcquisition("acquisition.unpublished", "unpublished/native-dev", "run.unpublished",
        pin("plan.unpublished", "empirical-lawhood/runtime/development-execution-plan"),
        pin("receipt.unpublished", "empirical-lawhood/runtime/canonical-task-receipt"), False)
    records = {"campaign": campaign_fixture()[0].campaign, "programme": f.programme, "bank": f.bank,
        "acquisition": acquisition, "reduction": f.reduction, "data": f.data, "resources": resources}
    bindings = []
    for name, value in sorted(records.items()):
        raw = value.canonical_bytes()
        member = selected_root / (name + ".json")
        member.write_bytes(raw)
        identity = ObjectIdentity.from_record(getattr(value, public.ID_FIELDS[name]), value)
        bindings.append(ExperimentInputBinding(name, identity, member.name, len(raw)))
    selection = ExperimentInputSelection("inputs.public.selected-e4-revision", public.PROTOCOL_ID, tuple(bindings))
    input_path = selected_root / "sources.json"
    input_path.write_bytes(selection.canonical_bytes())
    bound = load_experiment_inputs(editable, input_path)
    assert bound.method_inputs.resources == resources
    snapshot = implementation_binding(ROOT)
    execution = ExecutionSelection(workers=1, environment_id="main-locked",
        source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", snapshot), output_root=str(selected_root))
    preparation = prepare_experiment(editable, scientific_inputs=bound.scientific_inputs,
        method_inputs=bound.method_inputs, execution=execution)
    assert preparation.executable
    directory = selected_root / "authored"
    report = author_prepared_experiment(preparation=preparation, project_root=ROOT, artifact_writer=writer, output_dir=directory)
    assert report["status"] == "AUTHORED" and report["native_contact"] == "none"
    packet, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=writer, lazy_payloads=True)
    assert draft == preparation.draft and len(draft.operations) == 2
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
    declarations = {row.capability_key: row for row in owner.operation_declarations()}
    fit = next(row for row in draft.operations if row.selection.capability_key.endswith(".revision-fit"))
    fit_config = decode_recursive_config_input(fit, declarations[fit.selection.capability_key].registration()).record
    selected_specification = science.derive_revision_specification(editable, f.programme)
    assert dict(fit_config.external_operands)["specification"] == selected_specification.identity
    assert selected_specification.trigger.threshold == Decimal("999")
    instance = decode_canonical_bytes(payloads["experiment-instance.json"], ExperimentInstanceBinding, maximum_bytes=None)
    assert instance.specification == editable.identity and instance.allocation == science.selection_allocation(f.programme).identity
    public.validate_instance(specification=editable, allocation=preparation.allocation, draft=draft,
        source_records=preparation.design_records)
    _, plan, _ = _retained_plans(payloads, draft)
    with pytest.raises(ValueError, match="retained input materialization"):
        CurrentDevelopmentTaskCustody(writer=writer, directory=directory, plan=plan)
    # Initialize exact committed run inputs through the stock owner only. This
    # performs no scheduler, worker, native acquisition or completed-study act.
    from empirical_lawhood.api.recursive_execution import _external_inputs
    from empirical_lawhood.runtime.execution import VerifiedArtifactInput
    initialized = _external_inputs(plane=writer, plan=plan, draft=draft,
        payloads=payloads, read_only=False)
    expected_inputs = {value.logical_artifact_id: value
        for task in plan.tasks for value in task.external_inputs}
    assert len(initialized) == len(expected_inputs)
    assert all(type(value) is VerifiedArtifactInput for value in initialized)
    assert {value.logical.logical_artifact_id for value in initialized} == set(expected_inputs)
    for value in initialized:
        expected = expected_inputs[value.logical.logical_artifact_id]
        assert (value.logical.payload_schema, value.logical.content_sha256, value.logical.media_type) == (
            expected.expected_payload_schema, expected.expected_content_sha256, expected.expected_media_type)
    custody = CurrentDevelopmentTaskCustody(writer=writer, directory=directory, plan=plan)
    assert custody.packet == packet
    assert all(task.capability.requested_resources.memory_bytes == 1024**3 for task in plan.tasks)
    from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding
    binding = experiment_runtime_binding(public.protocol_declaration())
    assert binding.bind_handoff is None and callable(binding.bind_development_runtime)
    supplier = binding.bind_development_runtime(supplier=object(), writer=writer, directory=directory, plan=plan,
        output_codecs={kind.SCHEMA: kind for row in owner.operation_declarations() for kind in row.record_codecs.values()})
    assert supplier.custody.plan == plan
    # Deliberately unpublished native acquisition locator is not accepted merely
    # because authoring and the complete observation companion are well formed.
    from empirical_lawhood.api.selected_e4_method_runtime import original_development_products
    with pytest.raises((OSError, ValueError, PermissionError)):
        original_development_products(writer=writer, locator=acquisition, programme=f.programme, bank=f.bank, data_id=f.data.record_id)
    with pytest.raises(ValueError, match="reservation"):
        first = draft.operations[0]
        public.validate_instance(specification=editable, allocation=preparation.allocation,
            draft=replace(draft, operations=(replace(first, resource_budget=ResourceBudget(1, 2*1024**3, 0, None, None, None)),
                *draft.operations[1:])), source_records=preparation.design_records)


def test_editable_phase_resources_validate_without_native_prerequisite_contacts(tmp_path, monkeypatch):
    from empirical_lawhood.api.configuration import validate_configuration
    assert tmp_path.resolve().is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    resources = owner.SelectedE4MethodResources("resources.offline", tuple((name, ResourceBudget(1, 1024**3, 0, None, None, None))
        for name in ("revision-fit", "revision-freeze")))
    path = tmp_path / "method-resources.json"
    path.write_bytes(resources.canonical_bytes())
    monkeypatch.setattr(public, "prepare", lambda *_args, **_kwargs: pytest.fail("offline validation entered preparation"))
    monkeypatch.setattr(owner, "method_rows", lambda *_args, **_kwargs: pytest.fail("offline validation entered lowering"))
    report = validate_configuration(path, consumer="matrix-selected-e4-revision-resources")
    assert report["status"] == "VALIDATED" and report["consumer_byte_ready"]
