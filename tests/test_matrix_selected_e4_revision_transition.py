# SPDX-License-Identifier: MPL-2.0
"""Public transition software controls; fixtures have no native source authority."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_experiment as original
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_revision_transition as domain
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
from empirical_lawhood.api import selected_e4_method_runtime as runtime
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.artifacts import ExternalRootContract
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_matrix_selected_e4_methods import selected_revision, selected_e4_populations, selected_bridge, transfer, pin  # noqa: F401
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture


ROOT = Path(__file__).resolve().parents[1]


def _real_plane(path):
    assert path.resolve().is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    path.mkdir()
    contract = ExternalRootContract("matrix-transition-public-control", "Exposed transition software custody",
        str(path.resolve()), "/media/chevre/EL", "empirical-lawhood/testing/matrix-transition", 1,
        allowed_filesystem_types=("ext4",))
    plane = ExternalArtifactPlane(GuardedExternalRoot(contract))
    assert plane.root.diagnostic().write_ready
    return plane


def transition_files(f, directory, writer, selection_type=ExperimentInputSelection):
    assert directory.resolve().is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    directory.mkdir(exist_ok=True)
    editable = replace(f.editable, trigger=replace(f.editable.trigger, threshold=Decimal("999")))
    specification = domain.SelectedE4RevisionAcquisitionSpecification("specification.transition.public", editable)
    resources = methods.SelectedE4MethodResources("resources.transition.public",
        tuple((phase, ResourceBudget(1, 1024**3, 0, None, None, None)) for phase in ("revision-fit", "revision-freeze")))
    records = {"allocation": original.allocation(f.programme), "campaign": campaign_fixture()[0].campaign,
        "source": domain.SelectedE4RevisionAcquisitionSource("source.transition", "unpublished/original-dev", False),
        "resources": resources}
    bindings = []
    ids = {"allocation": "allocation_id", "campaign": "campaign_id", "source": "record_id", "resources": "record_id"}
    for name, record in sorted(records.items()):
        raw = record.canonical_bytes()
        path = directory / (name + ".json")
        path.write_bytes(raw)
        bindings.append(ExperimentInputBinding(name, ObjectIdentity.from_record(getattr(record, ids[name]), record),
            path.name, len(raw)))
    arguments = ((),) if selection_type is ExperimentFileInputSelection else ()
    selection = selection_type("sources.transition.public", domain.PROTOCOL_ID, tuple(bindings), *arguments)
    sources = directory / "sources.json"
    sources.write_bytes(selection.canonical_bytes())
    bound = load_experiment_inputs(specification, sources)
    execution = ExecutionSelection(workers=1, environment_id="main-locked", output_root=writer.root.contract.canonical_path,
        source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", implementation_binding(ROOT)))
    preparation = prepare_experiment(specification, scientific_inputs=bound.scientific_inputs, method_inputs=bound.method_inputs,
        execution=execution)
    return specification, records, preparation


def test_copied_wrapper_specification_is_canonical_and_has_no_implicit_scientific_values():
    path = ROOT / "programmes/foundations/emergent-structure/workflows/matrix-selected-e4-revision/specification.json"
    raw = path.read_bytes()
    value = decode_canonical_bytes(raw, domain.SelectedE4RevisionAcquisitionSpecification, maximum_bytes=None)
    assert value.canonical_bytes() == raw
    assert value.revision.fold_count == 2 and len(value.revision.folds) == 16
    assert value.revision.maximum_fit_calls == 5
    assert value.revision.trigger is None and not value.revision.revision_candidates
    assert value.revision.matched_selection.penalties == (Decimal(1), Decimal(10))
    declaration = domain.protocol_declaration()
    assert declaration.programme_record_type is domain.SelectedE4RevisionAcquisitionProgramme
    assert not declaration.requires_development_runtime_binding and not declaration.requires_prospective_runtime_binding


def test_partial_revision_export_reopens_through_registered_public_input_loader(tmp_path, monkeypatch):
    """Real publication/consumer contract with explicitly absent acquisition data."""
    raw = (ROOT / "programmes/foundations/emergent-structure/workflows/matrix-selected-e4-revision/specification.json").read_bytes()
    specification = decode_canonical_bytes(raw, domain.SelectedE4RevisionAcquisitionSpecification, maximum_bytes=len(raw))
    writer = _real_plane(tmp_path / "selected")
    campaign = campaign_fixture()[0].campaign
    resources = methods.SelectedE4MethodResources("resources.partial-export.public",
        tuple((phase, ResourceBudget(1, 1024**3, 0, None, None, None)) for phase in ("revision-fit", "revision-freeze")))
    monkeypatch.setattr(runtime, "selected_e4_revision_inputs_from_acquisition", lambda **_kwargs: {})
    report = runtime.export_selected_e4_revision_inputs_from_acquisition(directory=tmp_path / "absent-original-acquisition",
        artifact_writer=writer, output_directory=Path(writer.root.contract.canonical_path) / "exported",
        campaign=campaign, resources=resources, allow_partial=True)
    bound = load_experiment_inputs(specification.revision, Path(report["sources_path"]))
    assert type(report["selection"]) is ExperimentInputSelection
    assert bound.scientific_inputs == {} and bound.method_inputs.programme is None
    assert bound.method_inputs.campaign == campaign and bound.method_inputs.resources == resources
    assert bound.method_inputs.acquisition is None and bound.method_inputs.data is None
    assert report["native_contact"] == "none" and report["qualification"] == "NOT_ESTABLISHED"


@pytest.mark.parametrize("selection_type", (ExperimentInputSelection, ExperimentFileInputSelection))
def test_actual_public_transition_refuses_unpublished_original_acquisition_before_component_authoring(selected_revision, tmp_path, selection_type):  # noqa: F811
    writer = _real_plane(tmp_path / "selected")
    _, _, preparation = transition_files(selected_revision, tmp_path / "copied-inputs", writer, selection_type)
    assert preparation.executable and preparation.draft is None
    assert preparation.programme.specification.revision.trigger.threshold == Decimal("999")
    from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding
    binding = experiment_runtime_binding(domain.protocol_declaration())
    assert binding.bind_handoff is None and binding.bind_development_runtime is None and callable(binding.programme_service_factory)
    output = Path(writer.root.contract.canonical_path) / "new-transition"
    with pytest.raises((OSError, ValueError, PermissionError)):
        ExperimentProgrammeService(ROOT, writer).author(preparation=preparation, output_dir=output)
    assert not (output / "revision-component" / "authored-wave.json").exists()
    assert not (output / "experiment-programme.json").exists()


@pytest.mark.parametrize("selection_type", (ExperimentInputSelection, ExperimentFileInputSelection))
def test_disclosed_projection_control_exercises_real_author_export_coldread_without_native_or_fit(selected_revision, tmp_path, monkeypatch, selection_type):  # noqa: F811
    # Only unavailable original native acquisition is replaced with disclosed
    # numerical fixture rows. No parent-custody admission or scientific work is
    # simulated; the real original reader is tested separately for refusal.
    f = selected_revision
    writer = _real_plane(tmp_path / "selected")
    _, records, preparation = transition_files(f, tmp_path / "copied-inputs", writer, selection_type)
    locator = methods.SelectedE4DevelopmentAcquisition("acquisition.transition.disclosed", records["source"].authored_directory,
        "run.disclosed", pin("plan.disclosed", "empirical-lawhood/runtime/development-execution-plan"),
        pin("receipt.disclosed", "empirical-lawhood/runtime/canonical-task-receipt"), False)
    monkeypatch.setattr(runtime, "selected_e4_revision_inputs_from_acquisition", lambda **_: {
        "programme": f.programme, "bank": f.bank, "acquisition": locator, "reduction": f.reduction, "data": f.data})
    service = ExperimentProgrammeService(ROOT, writer)
    output = Path(writer.root.contract.canonical_path) / "new-transition"
    report = service.author(preparation=preparation, output_dir=output)
    assert report["status"] == "AUTHORED" and report["native_contact"] == "none"
    assert report["qualification"] == "NOT_ESTABLISHED"
    bound = load_experiment_inputs(preparation.programme.specification.revision, Path(report["sources_path"]))
    assert bound.method_inputs.data == f.data and bound.method_inputs.acquisition == locator
    read = service.read(directory=output, allow_partial=True)
    assert read["assigned_groups"] == 32 and read["scientific_disposition"] is None
    assert read["new_native_contact_count"] == 0 and read["qualification"] == "NOT_ESTABLISHED"
    from empirical_lawhood.api.composite_experiment_programme import selected_composite_programme_service
    selected = selected_composite_programme_service(service=service, directory=output)
    retained = selected._retained(output)
    assert retained.resolved_source == locator and retained.child_packet is not None
    assert retained.child_plan is not None and retained.child_instance is not None
    with pytest.raises(ValueError, match="worker"):
        selected.run(directory=output, maximum_parallel_tasks=4)
    # Fresh actual parent custody would refuse locator before fit; deriving a
    # public companion never authenticates the original native acquisition.
    with pytest.raises((OSError, ValueError, PermissionError)):
        runtime.original_development_products(writer=writer, locator=locator, programme=f.programme, bank=f.bank,
            data_id=f.data.record_id)


def test_transition_missing_input_stops_preserve_declared_group_census(selected_revision):  # noqa: F811
    specification = domain.SelectedE4RevisionAcquisitionSpecification("specification.transition.missing", selected_revision.editable)
    preparation = domain.prepare(specification, scientific_inputs={}, execution=ExecutionSelection())
    assert preparation.programme is None and not preparation.executable
    assert dict(preparation.census.role_counts)["development-groups"] == 32
    assert {row.source_key for row in preparation.dependencies} >= {"allocation", "source", "campaign", "resources", "workers"}


def test_transition_rejects_undeclared_files_before_binding_records():
    raw = (ROOT / "programmes/foundations/emergent-structure/workflows/matrix-selected-e4-revision/specification.json").read_bytes()
    specification = decode_canonical_bytes(raw, domain.SelectedE4RevisionAcquisitionSpecification, maximum_bytes=len(raw))
    with pytest.raises(ValueError, match="no file inputs"):
        domain.bind_inputs(specification, {}, files={"undeclared": object()})


@pytest.mark.parametrize("damage", (None, "missing-entry-receipt", "callback-source", "wrong-config", "missing-operation", "wrong-lane"))
def test_complete_revision_derivation_uses_one_disclosed_reader_and_refuses_changed_source(selected_revision, selected_bridge, tmp_path, monkeypatch, damage):  # noqa: F811
    """One public derivation over disclosed decoded products, not native custody acceptance."""
    from types import SimpleNamespace
    from empirical_lawhood.api import matrix_selected_e3_e4_read as original_reader
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as acquisition
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as records
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
    from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
    f = selected_revision
    writer = _real_plane(tmp_path / "selected")
    directory = Path(writer.root.contract.canonical_path) / "original-dev"
    directory.mkdir()
    key = acquisition.NAMESPACE + ".entry"
    operation = SimpleNamespace(node_id="task.disclosed-derivation.entry", selection=SimpleNamespace(capability_key=key))
    config = acquisition.SelectedE3E4EntryConfig("config." + acquisition.global_node(f.programme, "entry"),
        f.programme, f.bank, ObjectIdentity("evidence.disclosed-derivation", records.SelectedE3E4Evidence.SCHEMA, records.SelectedE3E4Evidence.VERSION, "a"*64), 1, selected_bridge.evidence.produced_input_parents, secondary_readout=f.populations.secondary_readout)
    plan = SimpleNamespace(execution_plan_id="plan.disclosed-derivation", SCHEMA=DevelopmentExecutionPlan.SCHEMA,
        VERSION=DevelopmentExecutionPlan.VERSION, fingerprint=lambda: "a" * 64,
        tasks=(SimpleNamespace(task_id=operation.node_id, capability=SimpleNamespace(capability_key=key)),))
    draft = SimpleNamespace(operations=() if damage == "missing-operation" else (operation,),
        development_study=None if damage == "wrong-lane" else object(), prospective_draft=None)
    packet = SimpleNamespace(fingerprint=lambda: "c" * 64)
    run = SimpleNamespace(run_plan_id="run.disclosed-derivation")
    receipt = SimpleNamespace(receipt_id="receipt.disclosed-derivation", SCHEMA=CanonicalTaskReceipt.SCHEMA,
        VERSION=CanonicalTaskReceipt.VERSION, fingerprint=lambda: "b" * 64)
    products = {"receipts": {} if damage == "missing-entry-receipt" else {operation.node_id: receipt}}
    counts = {"read": 0, "products": 0, "science_finisher": 0}
    def forbidden(**_):
        pytest.fail("complete derivation re-entered an old full read or metadata load")
    monkeypatch.setattr(runtime, "describe_selected_e4_development_acquisition", forbidden)
    monkeypatch.setattr(runtime, "load_authored_wave", forbidden)
    monkeypatch.setattr(runtime, "original_development_products", forbidden)
    def decode(*_):
        if damage in ("missing-operation", "wrong-lane"):
            pytest.fail("malformed source reached config field access")
        return SimpleNamespace(record=object() if damage == "wrong-config" else config)
    monkeypatch.setattr(runtime, "decode_recursive_config_input", decode)
    def read(*, directory, artifact_writer, allow_partial, _validate_authored, _consume_original):
        counts["read"] += 1
        assert allow_partial is False and artifact_writer.root is writer.root
        assert artifact_writer._read_verification.context_depth == 1
        _validate_authored(packet=packet, draft=draft, run=run, plan=plan)
        counts["products"] += 1
        _consume_original(products=products, plan=plan, draft=draft, entry=config, bank=f.bank,
            run_id="run.foreign" if damage == "callback-source" else run.run_plan_id)
        return {"run_id": run.run_plan_id, "packet_sha256": packet.fingerprint(), "reduction": f.reduction.to_document()}
    monkeypatch.setattr(original_reader, "_read_selected_e3_e4_development", read)
    def observations(**values):
        # This is the explicit supplied-products seam; original receipt/score
        # science is covered by its unchanged finisher and real custody controls.
        counts["science_finisher"] += 1
        assert values["products"] is products and values["plan"] is plan
        assert values["programme"] == f.programme and values["bank"] == f.bank
        assert values["reduction"] == f.reduction and values["report"]["run_id"] == run.run_plan_id
        assert values["locator"].execution_plan == ObjectIdentity.from_record(plan.execution_plan_id, plan)
        assert values["locator"].entry_receipt == ObjectIdentity.from_record(receipt.receipt_id, receipt)
        assert values["data_id"] == "observed." + f.programme.programme_id
        return f.reduction, f.data
    monkeypatch.setattr(runtime, "_original_development_observations", observations)
    if damage is not None:
        reason = ("source/read callback" if damage == "callback-source" else "successful original source entry"
            if damage == "missing-entry-receipt" else "original entry owner" if damage == "wrong-config" else "truthful DEV declaration")
        with pytest.raises(PermissionError, match=reason):
            runtime.selected_e4_revision_inputs_from_acquisition(directory=directory, artifact_writer=writer, allow_partial=False)
        assert counts == {"read": 1, "products": int(damage in ("callback-source", "missing-entry-receipt")), "science_finisher": 0}
    else:
        actual = runtime.selected_e4_revision_inputs_from_acquisition(directory=directory, artifact_writer=writer, allow_partial=False)
        assert counts == {"read": 1, "products": 1, "science_finisher": 1}
        assert actual["programme"] == f.programme and actual["bank"] == f.bank
        assert actual["reduction"].canonical_bytes() == f.reduction.canonical_bytes()
        assert actual["data"].canonical_bytes() == f.data.canonical_bytes()
        assert actual["acquisition"].allow_partial is False


def test_partial_revision_derivation_preserves_original_separate_custody_route(selected_revision, tmp_path, monkeypatch):  # noqa: F811
    """Disclosed call-order seam only; no complete reader context admitted to partial science."""
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as acquisition
    f = selected_revision
    calls, locator = [], object()
    operation = SimpleNamespace(selection=SimpleNamespace(capability_key=acquisition.NAMESPACE + ".entry"))
    draft = SimpleNamespace(operations=(operation,))
    def describe(**arguments):
        calls.append("describe")
        assert arguments["allow_partial"] is True
        return locator
    def load(**arguments):
        calls.append("metadata")
        assert arguments["lazy_payloads"] is True
        return None, draft, None, None
    def decode(*arguments):
        calls.append("decode")
        return SimpleNamespace(record=SimpleNamespace(programme=f.programme, bank=f.bank))
    def observations(**arguments):
        calls.append("original-products")
        assert arguments["locator"] is locator and arguments["programme"] == f.programme
        assert arguments["data_id"] == "observed." + f.programme.programme_id
        return f.reduction, f.data
    monkeypatch.setattr(runtime, "describe_selected_e4_development_acquisition", describe)
    monkeypatch.setattr(runtime, "load_authored_wave", load)
    monkeypatch.setattr(runtime, "decode_recursive_config_input", decode)
    monkeypatch.setattr(runtime, "original_development_products", observations)
    monkeypatch.setattr(runtime, "_complete_selected_e4_revision_inputs_from_acquisition", lambda **_: pytest.fail("partial route reused complete context"))
    actual = runtime.selected_e4_revision_inputs_from_acquisition(directory=tmp_path, artifact_writer=object(), allow_partial=True)
    assert calls == ["describe", "metadata", "decode", "original-products"]
    assert actual == {"programme": f.programme, "bank": f.bank, "acquisition": locator, "reduction": f.reduction, "data": f.data}
