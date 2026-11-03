# SPDX-License-Identifier: MPL-2.0
"""Real stored software issue/provider custody, without native or qualification.

The original-read callback is explicitly disclosed software metadata. Actual
issued package/plan/receipts and ordinary provider persistence remain real owners.
"""
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import replace
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import current_task_custody as owner
from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader, _current_control
from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent
from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind
from empirical_lawhood.runtime.plans import RunPlan
from empirical_lawhood.runtime.providers import ExternalInputPayload
from tests.test_current_result_custody import actual_issued_current_task_controls as actual_issued_current_task_controls
from tests.test_issued_original_input_scope import _DisclosedOriginalScope


def _source(writer, package):
    return _current_control(writer=writer, run_id=package.run_plan_id, name="run-plan", record_type=RunPlan,
        maximum_bytes=writer.custody_limits.control_record_bytes)


@pytest.fixture
def copies(request, monkeypatch):
    f = request.getfixturevalue("actual_issued_current_task_controls")
    service, package, plan = f.control.service, f.control.package, f.plan
    writer = service.artifact_plane
    # Freeze the closed software-original roster BEFORE provider copies exist.
    scope = _DisclosedOriginalScope(writer)
    custody = owner.CurrentIssuedTaskCustody(writer=writer,
        reveal_authority_id=f.control.reveal.authority_id, original_input_access=scope)
    custody.bind_current_run(package.run_plan_id, package=package, source_plan=_source(writer, package),
        execution_plan=plan, require_current_source=service._check_identity)
    provider = service.provider_resolver.resolve(package.registry, platform_ports=service.executable_platform_ports)
    payloads = provider.external_inputs(plan)
    inputs = service._persist_provider_inputs(package.run_plan_id, payloads, minimum_free_bytes=1,
        original_input_access=custody)
    assert all((value.logical, value.materialization) not in scope.facts for value in inputs)
    return SimpleNamespace(fixture=f, writer=writer, package=package, plan=plan, scope=scope,
        custody=custody, payloads=payloads, inputs=inputs)


def _bind(c):
    c.custody.bind_provider_inputs(execution_plan=c.plan, payloads=c.payloads, inputs=c.inputs)


def _observe_body_opens(monkeypatch, writer, inputs, callback):
    paths = {writer.root.resolve(value.materialization.relative_path, for_write=False) for value in inputs}
    original = artifacts.os.open
    def opening(path, *args, **kwargs):
        if isinstance(path, (str, Path)) and Path(path) in paths:
            callback(Path(path))
        return original(path, *args, **kwargs)
    monkeypatch.setattr(artifacts.os, "open", opening)


def test_actual_provider_copies_are_joined_before_first_open_and_every_final_rehash(copies, monkeypatch):
    c = copies
    monkeypatch.setattr(ExternalInputPayload, "chunks", lambda self: pytest.fail("closed provider source reopened"))
    # The genuine current prospective source deliberately has no frozen byte
    # width. Its exact positive width must come from actual provider persistence.
    assert any(spec.expected_size_bytes is None for task in c.plan.tasks for spec in task.external_inputs)
    _bind(c)
    observed = []
    last = 0
    def opened(path):
        nonlocal last
        assert c.scope.calls > last
        last = c.scope.calls
        observed.append(path)
    _observe_body_opens(monkeypatch, c.writer, c.inputs, opened)
    with c.custody.verification_scope():
        bindings = tuple(WorkerInputBinding.from_verified(value, kind=WorkerInputKind.EXTERNAL) for value in c.inputs)
        ports = c.writer.open_many(c.inputs, bindings=bindings, maximum_bytes=None,
            before_member=c.custody.require_input_member)
        try:
            assert all(port.read(port.size_bytes + 1) for port in ports)
        finally:
            for port in ports:
                port.close()
    assert observed
    assert not c.fixture.control.executor.invocations


@pytest.mark.parametrize("damage", ("missing", "path", "hash", "lineage"))
def test_actual_provider_binding_refuses_missing_or_substituted_metadata_before_body(copies, monkeypatch, damage):
    c = copies
    values = c.inputs
    if damage == "missing":
        values = values[:-1]
    else:
        first = values[0]
        if damage == "path":
            first = replace(first, materialization=replace(first.materialization, relative_path="foreign/provider.bin"))
        elif damage == "hash":
            first = replace(first, logical=replace(first.logical, content_sha256="f"*64))
        else:
            parent = ArtifactLineageParent(ObjectIdentity("foreign.original", ObjectIdentity.SCHEMA,
                "1.0.0", "e"*64), VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND)
            first = replace(first, logical=replace(first.logical, lineage_parents=(parent,),
                parent_visibility_ceilings=(VisibilityCeiling.PROSPECTIVE,)))
        values = first, *values[1:]
    _observe_body_opens(monkeypatch, c.writer, c.inputs, lambda path: pytest.fail("invalid input body opened"))
    with pytest.raises(PermissionError, match="census|materialization|source bytes|parent lineage"):
        c.custody.bind_provider_inputs(execution_plan=c.plan, payloads=c.payloads, inputs=values)
    assert not c.fixture.control.executor.invocations


@pytest.mark.parametrize("field", ("expected_content_sha256", "expected_payload_schema", "expected_media_type",
    "expected_outcome_access", "expected_visibility_ceiling"))
def test_scoped_provider_census_refuses_null_frozen_contract_fields(copies, field):
    c = copies
    task = next(row for row in c.plan.tasks if any(spec.expected_size_bytes is None for spec in row.external_inputs))
    spec = next(spec for spec in task.external_inputs if spec.expected_size_bytes is None)
    changes = {field: None}
    if field == "expected_content_sha256":
        changes["identity_scope_sha256"] = "e"*64
    altered = replace(task, external_inputs=tuple(replace(row, **changes) if row is spec else row
        for row in task.external_inputs))
    plan = replace(c.plan, tasks=tuple(altered if row is task else row for row in c.plan.tasks))
    with pytest.raises(PermissionError, match="complete frozen external specification"):
        owner._provider_input_specs(plan)


@pytest.mark.parametrize("width", (None, 0))
def test_scoped_provider_census_keeps_exact_compiler_configuration_width(copies, width):
    c = copies
    task = next(row for row in c.plan.tasks if any(spec.input_id == "config" for spec in row.external_inputs))
    spec = next(spec for spec in task.external_inputs if spec.input_id == "config")
    altered = replace(task, external_inputs=tuple(replace(row, expected_size_bytes=width) if row is spec else row
        for row in task.external_inputs))
    plan = replace(c.plan, tasks=tuple(altered if row is task else row for row in c.plan.tasks))
    with pytest.raises(ValueError, match="exact CONFIGURATION size"):
        owner._provider_input_specs(plan)


@pytest.mark.parametrize("side", ("payload", "copy"))
def test_nullable_scientific_width_requires_actual_positive_persisted_fact(copies, monkeypatch, side):
    c = copies
    index = next(i for i, value in enumerate(c.inputs) if any(
        spec.logical_artifact_id == value.artifact_id and spec.expected_size_bytes is None
        for task in c.plan.tasks for spec in task.external_inputs))
    payloads, inputs = c.payloads, c.inputs
    if side == "payload":
        payloads = tuple(replace(value, size_bytes=0) if i == index else value for i, value in enumerate(payloads))
    else:
        inputs = tuple(replace(value, materialization=replace(value.materialization, size_bytes=0))
            if i == index else value for i, value in enumerate(inputs))
    _observe_body_opens(monkeypatch, c.writer, c.inputs, lambda path: pytest.fail("unproved width body opened"))
    with pytest.raises(PermissionError, match="actual positive source byte width"):
        c.custody.bind_provider_inputs(execution_plan=c.plan, payloads=payloads, inputs=inputs)
    assert not c.fixture.control.executor.invocations


def test_nullable_width_cannot_adopt_caller_substituted_payload_and_copy_facts(copies, monkeypatch):
    c = copies
    index = next(i for i, value in enumerate(c.inputs) if any(
        spec.logical_artifact_id == value.artifact_id and spec.expected_size_bytes is None
        for task in c.plan.tasks for spec in task.external_inputs))
    width = c.inputs[index].materialization.size_bytes + 1
    # Even mutually agreeing typed caller metadata cannot replace the exact
    # sidecar already committed by ordinary provider persistence.
    payloads = tuple(replace(value, size_bytes=width, maximum_bytes=width) if i == index else value
        for i, value in enumerate(c.payloads))
    inputs = tuple(replace(value, materialization=replace(value.materialization, size_bytes=width))
        if i == index else value for i, value in enumerate(c.inputs))
    _observe_body_opens(monkeypatch, c.writer, c.inputs, lambda path: pytest.fail("substituted source body opened"))
    with pytest.raises(PermissionError, match="frozen input or deterministic publication"):
        c.custody.bind_provider_inputs(execution_plan=c.plan, payloads=payloads, inputs=inputs)
    assert not c.fixture.control.executor.invocations


def test_scope_rereads_provider_sidecars_and_refuses_missing_publication_before_open(copies, monkeypatch):
    c = copies
    _bind(c)
    value = c.inputs[0]
    relative, _, _ = provider_input_location(c.writer, c.package.run_plan_id, value.artifact_id)
    c.writer.root.resolve(relative+".manifest.json", for_write=False).unlink()
    _observe_body_opens(monkeypatch, c.writer, c.inputs, lambda path: pytest.fail("missing sidecar body opened"))
    with pytest.raises((OSError, artifacts.ArtifactPlaneError)):
        with c.custody.verification_scope():
            pytest.fail("missing provider sidecar admitted")


def test_revoked_original_read_refuses_provider_copy_before_body(copies, monkeypatch):
    c = copies
    _bind(c)
    c.scope.revoked = True
    _observe_body_opens(monkeypatch, c.writer, c.inputs, lambda path: pytest.fail("revoked original body opened"))
    with pytest.raises(PermissionError, match="original read grant expired"):
        with c.custody.verification_scope():
            pytest.fail("revoked scope admitted")


@pytest.fixture
def completed(tmp_path, monkeypatch):
    from tests.runtime_platform.test_recursive_prospective_workflow import _public_run_handoff_fixture
    return _public_run_handoff_fixture(tmp_path, monkeypatch)


def _retained_parts(control, controls, *, allow_partial=False):
    reader = CurrentResultPlanReader(controls)
    package = control.package
    plan = reader.authenticate_execution_plan(package=package, issued=package.issued_study,
        run_id=package.run_plan_id)
    prefixes = tuple(sorted(row.capability_key for row in package.registry.capabilities))
    assert any(spec.expected_size_bytes is None for task in plan.tasks for spec in task.external_inputs)
    closure = reader.collect_receipt_closure(package=package, execution_plan=plan, reveal=control.reveal,
        capability_prefixes=prefixes, allow_partial=allow_partial)
    return reader, plan, closure


def test_retained_binding_uses_exact_reader_closure_and_guard_survives_outer_finalization(completed, monkeypatch):
    c = completed
    scope = _DisclosedOriginalScope(c.plane)
    custody = owner.CurrentIssuedTaskCustody(writer=c.plane,
        reveal_authority_id=c.reveal.authority_id, original_input_access=scope)
    reads = []
    def current_read():
        scope.require_current()
        reads.append("current")
    with c.plane.read_context() as controls:
        reader, plan, closure = _retained_parts(c, controls)
        spec = next(row for task in plan.tasks for row in task.external_inputs if row.input_id == "config")
        relative, _, _ = provider_input_location(controls, c.package.run_plan_id, spec.logical_artifact_id)
        manifest = controls.read_manifest(relative)
        scope.facts.discard((manifest.logical, manifest.materialization))
        with custody.retained_binding(package=c.package, execution_plan=plan, control_reader=reader,
                receipt_closure=closure, require_current_read=current_read) as actual:
            assert actual is custody
            retained_guard = reader._input_member_guard
            config_type = reader.execution_task(execution_plan=plan,
                task_id=next(task.task_id for task in plan.tasks if spec in task.external_inputs)).capability.config.config_schema
            from tests.runtime_platform.test_recursive_compiler import Config
            assert config_type == Config.SCHEMA
            assert reader.read_control(manifest, Config, manifest.materialization.size_bytes).SCHEMA == Config.SCHEMA
        count = len(reads)
        # The binding has restored its temporary state; exact per-path facts
        # still refresh actual read permission in the enclosing final verifier.
        controls.require_verification_snapshot()
        assert len(reads) > count
    assert reads
    count = len(reads)
    # Finalizers can retain exact facts after binding state restoration, but
    # neither those facts nor the callback outlive the actual enclosing scope.
    with pytest.raises(artifacts.ArtifactIdentityConflict, match="scope has ended"):
        retained_guard(manifest)
    assert len(reads) == count


def test_caller_cloned_closure_cannot_admit_provider_inputs(completed):
    with completed.plane.read_context() as controls:
        reader, plan, closure = _retained_parts(completed, controls)
        with pytest.raises(PermissionError, match="actual reader/package/plan binding"):
            reader.require_receipt_closure(package=completed.package, execution_plan=plan,
                receipt_closure=replace(closure))
        second = CurrentResultPlanReader(controls)
        with pytest.raises(PermissionError, match="actual reader/package/plan binding"):
            second.require_receipt_closure(package=completed.package, execution_plan=plan, receipt_closure=closure)


def test_parallel_consumers_share_one_exact_receipt_join_without_false_recursion(completed, monkeypatch):
    c = completed
    scope = _DisclosedOriginalScope(c.plane)
    custody = owner.CurrentIssuedTaskCustody(writer=c.plane,
        reveal_authority_id=c.reveal.authority_id, original_input_access=scope)
    with c.plane.read_context() as controls:
        reader, plan, closure = _retained_parts(c, controls)
        with custody.retained_binding(package=c.package, execution_plan=plan, control_reader=reader,
                receipt_closure=closure, require_current_read=scope.require_current):
            task = next(task for task in plan.tasks if task.outputs)
            target = next(manifest for manifest in closure.manifests
                if manifest.logical.logical_artifact_id == task.outputs[0].logical_artifact_id)
            custody._original_member_facts.discard((target.logical, target.materialization))
            original = reader.read_receipted_output_metadata
            entered, release, second_started = Event(), Event(), Event()
            calls = []
            def joined(**kwargs):
                calls.append(kwargs["task_id"])
                entered.set()
                assert release.wait(3)
                return original(**kwargs)
            monkeypatch.setattr(reader, "read_receipted_output_metadata", joined)
            def second():
                second_started.set()
                custody.require_input_member(target)
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(custody.require_input_member, target)
                assert entered.wait(3)
                later = pool.submit(second)
                assert second_started.wait(3)
                try:
                    with pytest.raises(FutureTimeoutError):
                        later.result(timeout=.05)
                    assert len(calls) == 1
                finally:
                    release.set()
                first.result(timeout=5)
                later.result(timeout=5)
            assert calls.count(task.task_id) == 1


def test_actual_partial_successful_closure_admits_only_its_reachable_inputs(tmp_path, monkeypatch):
    from empirical_lawhood.api.results import RunCampaignRequest
    from tests.runtime_platform.test_recursive_prospective_workflow import (
        _public_issued_handoff_fixture, _run_public_handoff,
    )
    parts = _public_issued_handoff_fixture(tmp_path, monkeypatch)
    control = _run_public_handoff(tmp_path, issued_parts=parts, prepare_only=True)
    stopped = control.api.run_campaign(RunCampaignRequest(control.package_path, confirmed=True))
    assert not stopped.succeeded and stopped.reason_codes == ("OUTCOME_REVEAL_AUTHORITY_REQUIRED",)
    assert control.executor.invocations == 4
    fixture = SimpleNamespace(plane=control.service.artifact_plane, package=control.package, reveal=control.reveal)
    scope = _DisclosedOriginalScope(fixture.plane)
    custody = owner.CurrentIssuedTaskCustody(writer=fixture.plane, original_input_access=scope)
    with fixture.plane.read_context() as controls:
        reader, plan, closure = _retained_parts(fixture, controls, allow_partial=True)
        assert 0 < len(closure.by_task) < len(plan.tasks)
        task = next(task for task in plan.tasks if task.task_id in closure.by_task)
        spec = next(row for row in task.external_inputs if row.input_id == "config")
        relative, _, _ = provider_input_location(controls, fixture.package.run_plan_id, spec.logical_artifact_id)
        manifest = controls.read_manifest(relative)
        scope.facts.discard((manifest.logical, manifest.materialization))
        from tests.runtime_platform.test_recursive_compiler import Config
        with custody.retained_binding(package=fixture.package, execution_plan=plan, control_reader=reader,
                receipt_closure=closure, require_current_read=scope.require_current):
            reader.read_control(manifest, Config, manifest.materialization.size_bytes)
        assert control.executor.invocations == 4
