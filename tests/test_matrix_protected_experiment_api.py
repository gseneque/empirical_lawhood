# SPDX-License-Identifier: MPL-2.0
"""Standalone API conformance with exposed metadata and tiny original custody.

Routing stubs below exercise delegation/refusal order only. They are explicitly
not genuine parent/issue/acquisition evidence. No scientific worker is entered.
The guarded-bank tests use actual tiny files and the actual content resolver.
"""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import ScheduledCompactBank
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_confirmation import ScheduledProgrammeAuthenticatedParent
from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import derive_protected_factorial_experiment
from empirical_lawhood.api import matrix_protected_experiment as owner
from empirical_lawhood.api import recursive_prospective_authoring as prospective_owner
from empirical_lawhood.api.matrix_scheduled_programme_runtime import ProgrammeRuntimeInputSupplier
from empirical_lawhood.infrastructure.candidate_sources import ExternalCandidateInputPublisher, ExternalContentAddressedInputResolver
from empirical_lawhood.infrastructure.recursive_prospective_inputs import RecursiveContentInputSupplier
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.planning.study_authoring import DesignInputRole
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure, SourceClosureKind
from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
from empirical_lawhood.runtime.recursive_prospective import RecursiveCandidateContextProvider
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort, recursive_input_port_key
from empirical_lawhood.runtime.source_resolution import CandidateSourceResolutionService
from tests.test_matrix_programme_factorial_confirmation import _pin
from tests.test_matrix_programme_factorial_confirmation_seal import _catalog
from tests.test_matrix_protected_factorial_preparation import (
    selected as selected, seal_selected as seal_selected, tiny_scheduled as tiny_scheduled,
    criteria as criteria, declared as declared, stock as stock, provenance as provenance,
)
from tests.test_matrix_scheduled_history_bindings import bank as scheduled_bank


@pytest.fixture
def routing(selected, tiny_scheduled, monkeypatch):
    plane, *_ = tiny_scheduled
    allocation, draft, _, spec = derive_protected_factorial_experiment(selected.specification, selected.original, selected.selection)
    registrations, registry, codecs = _catalog()
    closure = ImplementationSourceClosure(spec.spec_id + ".source-closure", SourceClosureKind.CLEAN_GIT_COMMIT,
        "d" * 40, "a" * 64, "b" * 64, True)
    compilation, authoring, _, _ = prospective_owner._compile(spec, closure, composition=(registrations, registry, codecs))
    context = RecursiveCandidateContextProvider(compilation, CandidateSourceResolutionService(ExternalContentAddressedInputResolver(plane.root)),
        spec.formal_methods, spec.formal_source_inventories)
    supplier = RecursiveContentInputSupplier(root=plane.root, operands=spec.external_operands)
    ports = tuple(sorted((ExecutablePlatformPort(recursive_input_port_key(selection), RecursiveOperationInputPort(supplier))
        for selection in {row.selection for row in compilation.operations}), key=lambda row: row.port_key))
    handoff = prospective_owner.RecursiveProspectiveApplicationHandoff(selected.directory, compilation, authoring, context,
        object(), spec.resources, ports)
    source_records = tuple(sorted(((selected.original.source_id, selected.original),
        (selected.selection.selection_id, selected.selection))))
    declaration = selected.original.criteria.record.configuration.qualified_parent
    parent = ScheduledProgrammeAuthenticatedParent(declaration.identity,
        selected.original.criteria.record.configuration.bank,
        _pin("package.unpublished.original", "empirical-lawhood/api/experiment-package"),
        _pin("plan.unpublished.original", "empirical-lawhood/runtime/execution-plan"),
        _pin("receipt.unpublished.original", "empirical-lawhood/runtime/canonical-task-receipt"),
        _pin("receipt.unpublished.qualification", "empirical-lawhood/runtime/canonical-task-receipt"),
        declaration.binding.adjudication, declaration.evidence)
    events = []
    bank = object()
    monkeypatch.setattr(owner, "_original_bank", lambda *args: events.append("bank") or bank)
    monkeypatch.setattr(owner.programme, "_assert_actual_declaration", lambda *args, **kwargs: events.append("declaration"))
    monkeypatch.setattr(owner.programme, "_actual_programme_entry", lambda *args, **kwargs: events.append("entry-parent") or parent)
    monkeypatch.setattr(owner, "authenticate_programme_qualified_parent", lambda *args: events.append("late-parent") or parent)
    pin = ObjectIdentity.from_record(selected.original.study.draft.draft_id, selected.original.study.draft)
    template = selected.original.study.draft.design_inputs[0]
    global_pin = replace(template, input_id="design.unpublished.original-global", object_identity=pin,
        materialization_sha256=pin.object_fingerprint, role=DesignInputRole.READINESS_METADATA,
        physical_unit_ids=(), seed_ids=())
    issued_root = replace(selected.original.study.draft, design_inputs=tuple(sorted(
        (*selected.original.study.draft.design_inputs, global_pin), key=lambda row: row.input_id)))
    package = SimpleNamespace(run_plan_id="run.unpublished.original", issued_study=SimpleNamespace(candidate=
        SimpleNamespace(authoring_package=SimpleNamespace(base=SimpleNamespace(draft=issued_root)))))
    monkeypatch.setattr(owner.factorial, "_ordinary_product", lambda *args: events.append("criteria") or package)

    def metadata(writer, locator, config, actual_bank, root, **kwargs):
        assert actual_bank is bank and root is selected.original.study.draft
        events.append(locator.wave_id)
        wave, = (row for row in config.programme.waves if row.wave_id == locator.wave_id)
        plan = SimpleNamespace(tasks=(SimpleNamespace(task_id=wave.wave_id + ".open"),))
        return package, plan, wave, None, None, None, package

    monkeypatch.setattr(owner.factorial, "_wave_metadata", metadata)
    monkeypatch.setattr(owner.factorial, "_original_config", lambda *args: (
        SimpleNamespace(scope=SimpleNamespace(global_root=selected.original.study.draft)), object()))
    monkeypatch.setattr(owner.factorial, "_live_package", lambda *args: events.append("live-original") or package)

    def no_outcomes(*args, **kwargs):
        pytest.fail("standalone handoff read confirmation outcomes or recovered a run")

    for name in ("_wave", "_task_state", "_output_payload", "ExternalRunRecoveryStore", "reduce_programme", "validate_factorial_inputs"):
        monkeypatch.setattr(owner.factorial, name, no_outcomes)
    return SimpleNamespace(selected=selected, plane=plane, handoff=handoff, allocation=allocation,
        source_records=source_records, parent=parent, package=package, events=events, supplier=supplier)


def _bind(routing, **kwargs):
    return owner.bind_protected_factorial_experiment_handoff(routing.handoff,
        specification=routing.selected.specification, allocation=routing.allocation,
        source_records=routing.source_records, artifact_writer=routing.plane, **kwargs)


def test_standalone_owner_replays_all_metadata_then_late_parent_and_preserves_handoff(routing):
    bound = _bind(routing, reveal_authority_id="reveal.future.explicitly-selected")
    assert bound is not routing.handoff
    for field in ("directory", "compilation", "authoring", "context", "projection", "resources"):
        assert getattr(bound, field) is getattr(routing.handoff, field)
    for before, after in zip(routing.handoff.platform_ports, bound.platform_ports, strict=True):
        assert before.port_key == after.port_key
        assert type(after.port.supplier) is ProgrammeRuntimeInputSupplier
        assert after.port.supplier.supplier is routing.supplier
        assert after.port.supplier.reveal_authority_id == "reveal.future.explicitly-selected"
        assert callable(after.port.supplier.prepare_factorial_task)
    assert routing.events == ["bank", "declaration", "entry-parent", "criteria",
        *(row.wave_id for row in routing.selected.original.acquisitions.acquisitions), "live-original", "late-parent"]


@pytest.mark.parametrize("damage", ("entry-parent-none", "entry-parent-bank", "expired-after-waves", "changed-after-waves", "original-expired", "global-root", "global-pin"))
def test_standalone_owner_refuses_original_authority_or_exact_global_binding_changes(routing, monkeypatch, damage):
    if damage.startswith("entry-parent"):
        parent = None if damage == "entry-parent-none" else replace(routing.parent, bank=_pin("bank.other", routing.parent.bank.object_schema))
        monkeypatch.setattr(owner.programme, "_actual_programme_entry", lambda *args, **kwargs: parent)
    elif damage == "expired-after-waves":
        def expired(*args):
            assert all(row.wave_id in routing.events for row in routing.selected.original.acquisitions.acquisitions)
            raise PermissionError("original qualified parent expired after metadata")
        monkeypatch.setattr(owner, "authenticate_programme_qualified_parent", expired)
    elif damage == "changed-after-waves":
        monkeypatch.setattr(owner, "authenticate_programme_qualified_parent", lambda *args: replace(routing.parent,
            package=_pin("package.changed", routing.parent.package.object_schema)))
    elif damage == "original-expired":
        monkeypatch.setattr(owner.factorial, "_live_package", lambda *args: None)
    elif damage == "global-root":
        changed = replace(routing.selected.original.study.draft, dag_template_key="template.same-science-different-original")
        monkeypatch.setattr(owner.factorial, "_original_config", lambda *args: (
            SimpleNamespace(scope=SimpleNamespace(global_root=changed)), object()))
    else:
        root = routing.package.issued_study.candidate.authoring_package.base.draft
        root = replace(root, design_inputs=tuple(row for row in root.design_inputs
            if row.input_id != "design.unpublished.original-global"))
        routing.package.issued_study.candidate.authoring_package.base.draft = root
    with pytest.raises(PermissionError):
        _bind(routing)


def test_real_actual_entry_returns_fresh_authenticated_parent_after_unchanged_source_guards(routing, monkeypatch):
    # Only routing owners are substituted; no result is a scientific credential.
    from empirical_lawhood.api import matrix_scheduled_programme_runtime
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_qualified_parent
    monkeypatch.undo()
    events = []
    monkeypatch.setattr(owner.programme, "validate_programme_bank", lambda *args: events.append("bank"))
    monkeypatch.setattr(programme_qualified_parent, "validate_qualified_parent_declaration", lambda *args: events.append("declaration"))
    monkeypatch.setattr(owner.programme, "_authenticate_blind_bank", lambda *args: events.append("blind-custody"))
    monkeypatch.setattr(matrix_scheduled_programme_runtime, "authenticate_programme_qualified_parent",
        lambda *args: events.append("current-parent") or routing.parent)
    config = routing.selected.original.criteria.record.configuration
    assert owner.programme._actual_programme_entry(config.programme, object(), routing.plane, None,
        qualified_parent=config.qualified_parent) is routing.parent
    assert events == ["bank", "declaration", "blind-custody", "current-parent"]


@pytest.mark.parametrize("damage", ("missing-source", "allocation-exposure", "other-candidate-root", "reveal-id"))
def test_standalone_selected_instance_refuses_before_any_original_metadata_read(routing, damage):
    kwargs = {}
    if damage == "missing-source":
        routing.source_records = routing.source_records[:-1]
    elif damage == "allocation-exposure":
        first = routing.allocation.units[0]
        routing.allocation = replace(routing.allocation, units=(replace(first, exposed=True), *routing.allocation.units[1:]))
    elif damage == "other-candidate-root":
        root = replace(routing.handoff.authoring.base.draft, question="A different scientific root?")
        base = replace(routing.handoff.authoring.base, draft=root, entry_package=replace(
            routing.handoff.authoring.base.entry_package, checklist=replace(routing.handoff.authoring.base.entry_package.checklist,
                draft=ObjectIdentity.from_record(root.draft_id, root))))
        # This remains a typed handoff, but its retained authoring root changed.
        routing.handoff = replace(routing.handoff, authoring=SimpleNamespace(base=base))
    else:
        kwargs["reveal_authority_id"] = "invalid authority with spaces"
    with pytest.raises((ValueError, PermissionError)):
        _bind(routing, **kwargs)
    assert routing.events == []


@pytest.mark.parametrize("damage", (None, "wrong-root", "wrong-sha", "wrong-size"))
def test_actual_tiny_blind_bank_uses_existing_exact_content_resolver(tiny_scheduled, monkeypatch, tmp_path, damage):
    plane, _, original = scheduled_bank.__wrapped__(tiny_scheduled)
    bank = ScheduledCompactBank.from_commitment(original)
    raw = bank.canonical_bytes()
    ExternalCandidateInputPublisher(plane.root).publish(raw, maximum_bytes=len(raw))
    artifact = ArtifactIdentity(bank.bank_id, "exposed-tiny-original-metadata", bank.SCHEMA,
        bank.fingerprint(), "application/json", len(raw))
    resolver = ExternalContentAddressedInputResolver(plane.root)
    service = CandidateSourceResolutionService(resolver)
    handoff = SimpleNamespace(context=SimpleNamespace(source_resolution_service=service))
    if damage == "wrong-root":
        from tests.runtime_platform.test_native_subwork import _plane
        handoff.context.source_resolution_service = CandidateSourceResolutionService(ExternalContentAddressedInputResolver(_plane(tmp_path / "other").root))
    elif damage == "wrong-sha":
        artifact = replace(artifact, sha256="b" * 64)
    elif damage == "wrong-size":
        artifact = replace(artifact, size_bytes=artifact.size_bytes + 1)
    if damage is None:
        assert owner._original_bank(handoff, SimpleNamespace(bank=artifact), plane) == bank
    else:
        with pytest.raises((PermissionError, RuntimeError)):
            owner._original_bank(handoff, SimpleNamespace(bank=artifact), plane)
