# SPDX-License-Identifier: MPL-2.0
"""Canonical software controls only: actual PURE custody, never native science."""
from dataclasses import replace
import json
import os
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.infrastructure import artifacts, recursive_custody as owner
from empirical_lawhood.infrastructure import recovery as recovery_owner, task_receipts as receipt_owner
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.runtime.execution import TaskBlockReason
from empirical_lawhood.runtime.recovery import RecoveryTerminalDisposition
from tests.test_recursive_compact_output_bulk import compact_wave as compact_wave  # noqa: F401
from tests.test_recursive_report_projection import ROOT, wave as wave  # noqa: F401
from tests.test_artifact_read_context import _work


@pytest.fixture(scope="module")
def control_case(compact_wave):
    packet, draft, source, payloads = author.load_authored_wave(
        directory=compact_wave.directory, artifact_writer=compact_wave.plane, lazy_payloads=True)
    run, plan, index = execution._retained_plans(payloads, draft)
    store = receipt_owner.ExternalTaskReceiptStore(compact_wave.plane)
    recovery = recovery_owner.ExternalRunRecoveryStore(compact_wave.plane)
    terminal = recovery.read_terminal(index)
    first = next(binding for binding in index.tasks if store.read(index.run_id,
        binding.task_id, binding.attempts[0].attempt_id) is not None)
    candidate = first.attempts[0]
    return SimpleNamespace(selected=compact_wave, run=run, plan=plan, index=index, terminal=terminal,
        receipt_path=compact_wave.plane.root.resolve(candidate.receipt_relative_path, for_write=False),
        event_path=compact_wave.plane.root.resolve(candidate.event_relative_path, for_write=False))


def _read(value, *, plane=None, full=False, partial=False):
    return execution.read_recursive_wave(directory=value.selected.directory,
        artifact_writer=value.selected.plane if plane is None else plane, include_products=True,
        terminal_product_format="documents" if full else "compact", allow_partial=partial)


@pytest.mark.parametrize('lifetime', ('verification_scope', 'read_context'))
def test_complete_control_batch_uses_actual_installed_codecs_without_api_singleton(control_case, lifetime):
    """Match the actual C25 plane composition; no native/scientific evidence."""
    from empirical_lawhood.api.integration_artifact_profiles import INTEGRATION_ARTIFACT_PROFILE_VALIDATORS
    from empirical_lawhood.api.recursive_operations import operation_storage_codecs
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry

    original = control_case.selected.plane
    validators = ArtifactProfileValidatorRegistry(binary_codecs=operation_storage_codecs())
    assert validators is not INTEGRATION_ARTIFACT_PROFILE_VALIDATORS
    plane = artifacts.ExternalArtifactPlane(original.root, validators, original.semantic_validations,
        custody_limits=original.custody_limits)
    branches = []
    census = []
    selector = owner._can_batch_compact_control_custody.__code__
    batch = owner._read_compact_control_census.__code__
    def observe(frame, event, arg):
        if event == 'return' and frame.f_code is selector:
            branches.append(arg)
        elif event == 'call' and frame.f_code is batch:
            census.append(True)
    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        with getattr(plane, lifetime)() as reading:
            policy = execution._read_only_custody_policy(reading)
            assert policy is not None and policy[3] is validators
            actual = _read(control_case, plane=reading)
    finally:
        sys.setprofile(previous)
    assert actual == control_case.selected.compact
    # Revalidate policy at the existing boundaries; only the complete census
    # itself should be consumed once. A fixed selector-call count is not a gate.
    assert branches and all(branches) and census == [True]


@pytest.mark.parametrize("mode", ("bulk", "full", "partial", "no-policy", "receipt-instance", "receipt-class", "event-class", "receipt-path-class", "event-path-class", "low-limit"))
def test_actual_closed_pure_census_matches_serial_and_preserves_hook_fallback(control_case, monkeypatch, mode):
    actual_census = owner._operational_census
    actual_batch = artifacts._ScopedArtifactPlane.verify_manifests_members
    receipt_read = receipt_owner.ExternalTaskReceiptStore.read
    event_read = recovery_owner.ExternalRunRecoveryStore.read_event
    original_receipt_path = receipt_owner.ExternalTaskReceiptStore._relative_path
    original_event_path = recovery_owner.ExternalRunRecoveryStore._event_path
    inside, batches, hooks = [], [], []

    def observed_batch(self, *args, **kwargs):
        if inside:
            batches.append(True)
        return actual_batch(self, *args, **kwargs)

    def read_receipt(self, *args, **kwargs):
        if inside:
            hooks.append("receipt")
        return receipt_read(self, *args, **kwargs)

    def read_event(self, *args, **kwargs):
        if inside:
            hooks.append("event")
        return event_read(self, *args, **kwargs)

    def receipt_path(*args, **kwargs):
        if inside:
            hooks.append("receipt-path")
        return original_receipt_path(*args, **kwargs)

    def event_path(*args, **kwargs):
        if inside:
            hooks.append("event-path")
        return original_event_path(*args, **kwargs)

    def census(**kwargs):
        if mode == "no-policy":
            kwargs["_read_policy"] = None
        if mode == "receipt-instance":
            store = kwargs["store"]
            store.read = lambda *args, **options: read_receipt(store, *args, **options)
        old_limit = kwargs["store"].plane.custody_limits
        if mode == "low-limit":
            kwargs["store"].plane.custody_limits = replace(old_limit, publication_members=2)
        inside.append(True)
        try:
            return actual_census(**kwargs)
        finally:
            inside.pop()
            kwargs["store"].plane.custody_limits = old_limit

    if mode == "receipt-class":
        monkeypatch.setattr(receipt_owner.ExternalTaskReceiptStore, "read", read_receipt)
    if mode == "event-class":
        monkeypatch.setattr(recovery_owner.ExternalRunRecoveryStore, "read_event", read_event)
    if mode == "receipt-path-class":
        monkeypatch.setattr(receipt_owner.ExternalTaskReceiptStore, "_relative_path", staticmethod(receipt_path))
    if mode == "event-path-class":
        monkeypatch.setattr(recovery_owner.ExternalRunRecoveryStore, "_event_path", staticmethod(event_path))
    monkeypatch.setattr(owner, "_operational_census", census)
    monkeypatch.setattr(artifacts._ScopedArtifactPlane, "verify_manifests_members", observed_batch)
    with control_case.selected.plane.verification_scope() as plane:
        result = _read(control_case, plane=plane, full=mode == "full", partial=mode == "partial")
    assert result == (control_case.selected.full if mode == "full" else control_case.selected.compact)
    assert len(batches) == (2 if mode == "bulk" else 0)
    if mode in ("receipt-instance", "receipt-class", "event-class", "receipt-path-class", "event-path-class"):
        assert hooks
    assert result[0]["new_native_contact_count"] == 0


def test_control_batches_reduce_snapshot_traversals_without_skipping_decodes(control_case, monkeypatch):
    actual_census, eligible = owner._operational_census, owner._can_batch_compact_control_custody
    guard = artifacts.ExternalArtifactPlane._require_verification_snapshot_paths
    decode_receipt, decode_event = receipt_owner.decode_task_receipt, recovery_owner.decode_task_recovery_event
    inside, counts = [], {}

    def census(**kwargs):
        inside.append(True)
        try:
            return actual_census(**kwargs)
        finally:
            inside.pop()

    observations = []
    def observe_guard(self, snapshots, *, reason):
        if inside:
            observations.append("guard")
        return guard(self, snapshots, reason=reason)

    def receipt(*args, **kwargs):
        if inside:
            observations.append("receipt")
        return decode_receipt(*args, **kwargs)

    def event(*args, **kwargs):
        if inside:
            observations.append("event")
        return decode_event(*args, **kwargs)

    monkeypatch.setattr(owner, "_operational_census", census)
    monkeypatch.setattr(artifacts.ExternalArtifactPlane, "_require_verification_snapshot_paths", observe_guard)
    monkeypatch.setattr(receipt_owner, "decode_task_receipt", receipt)
    monkeypatch.setattr(recovery_owner, "decode_task_recovery_event", event)
    for mode in ("serial", "bulk"):
        monkeypatch.setattr(owner, "_can_batch_compact_control_custody", (lambda **kwargs: False) if mode == "serial" else eligible)
        observations.clear()
        with control_case.selected.plane.verification_scope() as plane:
            assert _read(control_case, plane=plane) == control_case.selected.compact
        counts[mode] = tuple(observations.count(name) for name in ("guard", "receipt", "event"))
    assert counts["bulk"][0] < counts["serial"][0]
    assert counts["bulk"][1:] == counts["serial"][1:] == (len(control_case.index.tasks), len(control_case.index.tasks))


@pytest.mark.parametrize("kind,partial", (("receipt", False), ("event", False), ("receipt", True), ("event", True)))
def test_actual_control_corruption_or_partial_pair_refuses_before_products(control_case, monkeypatch, kind, partial):
    path = control_case.receipt_path if kind == "receipt" else control_case.event_path
    raw = path.read_bytes()
    monkeypatch.setattr(owner, "_assemble_read_products", lambda **kwargs: pytest.fail("invalid controls reached products"))
    try:
        if partial:
            path.unlink()
        else:
            path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
        error = (artifacts.ArtifactIdentityConflict,) if kind == "receipt" else (recovery_owner.RunRecoveryError, artifacts.ArtifactIdentityConflict)
        with pytest.raises(error):
            with control_case.selected.plane.verification_scope() as plane:
                _read(control_case, plane=plane)
    finally:
        path.write_bytes(raw)


@pytest.mark.parametrize("kind", ("receipt", "event", "ancestor"))
def test_callback_time_control_or_ancestor_drift_refuses_before_products(control_case, monkeypatch, kind):
    original = artifacts._ScopedArtifactPlane.verify_manifests_members
    census = owner._operational_census
    inside, touched = [], []
    path = control_case.receipt_path if kind != "event" else control_case.event_path
    raw = path.read_bytes()
    held = path.parent.with_name(path.parent.name + "-held-control")

    def selected_census(**kwargs):
        inside.append(True)
        try:
            return census(**kwargs)
        finally:
            inside.pop()

    def changed(self, manifests, *, validate_members):
        should_change = bool(inside and not touched and manifests
            and manifests[0].logical.payload_schema == (receipt_owner.CanonicalTaskReceipt.SCHEMA if kind != "event" else control_case.index.TASK_EVENT_SCHEMA))
        def consume(authenticated):
            if should_change:
                touched.append(True)
                if kind == "ancestor":
                    path.parent.rename(held)
                    path.parent.symlink_to(held, target_is_directory=True)
                else:
                    path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
            return validate_members(authenticated)
        return original(self, manifests, validate_members=consume)

    monkeypatch.setattr(owner, "_operational_census", selected_census)
    monkeypatch.setattr(owner, "_assemble_read_products", lambda **kwargs: pytest.fail("changed controls reached products"))
    monkeypatch.setattr(artifacts._ScopedArtifactPlane, "verify_manifests_members", changed)
    expected_error = {"receipt": artifacts.ArtifactIdentityConflict,
        "event": (recovery_owner.RunRecoveryError, artifacts.ArtifactIdentityConflict), "ancestor": artifacts.ExternalRootUnavailable}[kind]
    try:
        with pytest.raises(expected_error):
            with control_case.selected.plane.verification_scope() as plane:
                _read(control_case, plane=plane)
        assert touched
    finally:
        if kind == "ancestor" and path.parent.is_symlink():
            path.parent.unlink()
            held.rename(path.parent)
        elif kind != "ancestor":
            path.write_bytes(raw)


@pytest.mark.parametrize("damage", ("duplicate", "foreign-block"))
def test_terminal_identity_refuses_before_any_batch_or_control_read(control_case, monkeypatch, damage):
    terminal = control_case.terminal
    if damage == "duplicate":
        first, second, *rest = terminal.attempts
        rows = (first, replace(second, attempt_id=first.attempt_id), *rest)
        altered = replace(terminal, attempts=rows)
    else:
        first, *rest = terminal.attempts
        foreign = replace(first, task_id="task.foreign.control", attempt_id=control_case.index.run_id + ".task.foreign.control.block-001",
            ordinal=1, disposition=RecoveryTerminalDisposition.BLOCKED, reason_code=TaskBlockReason.DEPENDENCY_FAILED.value,
            receipt_id=None, receipt_sha256=None)
        altered = replace(terminal, operational_status="BLOCKED", attempts=tuple(sorted((*rest, foreign), key=lambda value:(value.task_id,value.ordinal))),
            completed_task_ids=tuple(value for value in terminal.completed_task_ids if value != first.task_id),
            blocked_task_ids=(foreign.task_id,))
    altered.__post_init__()
    def forbidden(*args, **kwargs):
        pytest.fail("invalid terminal opened control bytes or entered batch")
    monkeypatch.setattr(owner, "_read_compact_control_census", forbidden)
    monkeypatch.setattr(receipt_owner, "_read_control_plane_json", forbidden)
    monkeypatch.setattr(recovery_owner, "read_bounded_bytes", forbidden)
    with control_case.selected.plane.verification_scope() as plane:
        reason = "duplicates an attempt identity" if damage == "duplicate" else "exact nonattempt identity or receipt"
        with pytest.raises(ValueError, match=reason):
            owner._operational_census(recovery=recovery_owner.ExternalRunRecoveryStore(plane),
                store=receipt_owner.ExternalTaskReceiptStore(plane), plan=control_case.plan, index=control_case.index,
                terminal=altered, decode_products=False, _read_policy=execution._read_only_custody_policy(plane))


@pytest.fixture(scope="module")
def failed_control_case(compact_wave):
    """New PURE metadata fixture, all worker bodies explicitly refused; no native fixture."""
    from empirical_lawhood.adapters.methods.rubisco_historical.recursive_translation import historical_recursive_draft
    from tests.test_rubisco_historical_recursive import _inputs
    model, slices = _inputs()
    root = compact_wave.directory.parent
    directory = root / "compact-control-failed-pure"
    bindings = tuple(("external." + record.slice_id, root / ("bulk-" + record.slice_id + ".json")) for record in slices)
    draft = historical_recursive_draft(model, slices, draft_id="draft.exposed.compact-control.failed-pure")
    assert draft.draft_id != compact_wave.compact[2].draft_id
    author.author_recursive_wave(draft=draft, project_root=ROOT,
        artifact_writer=compact_wave.plane, output_dir=directory, input_bindings=bindings)
    def refuse(*args, **kwargs):
        raise RuntimeError("disclosed PURE software worker failure; no science entered")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(LocalProcessExecutor, "execute", refuse)
        report = execution.run_recursive_wave(directory=directory, project_root=ROOT,
            artifact_writer=compact_wave.plane, terminal_product_format="compact")
    assert report["status"] in ("FAILED", "BLOCKED") and report["new_native_contact_count"] == 0
    assert report["run_id"] != compact_wave.compact[0]["run_id"]
    _, draft, _, payloads = author.load_authored_wave(directory=directory,
        artifact_writer=compact_wave.plane, lazy_payloads=True)
    run, plan, index = execution._retained_plans(payloads, draft)
    terminal = recovery_owner.ExternalRunRecoveryStore(compact_wave.plane).read_terminal(index)
    candidates = {candidate.attempt_id for binding in index.tasks for candidate in binding.attempts}
    nonattempt = next(row for row in terminal.attempts if row.attempt_id not in candidates)
    missing_receipt = compact_wave.plane.root.resolve(receipt_owner.ExternalTaskReceiptStore._relative_path(
        index.run_id, nonattempt.task_id, nonattempt.attempt_id), for_write=False)
    missing_event = compact_wave.plane.root.resolve(next(binding.nonattempt_event_relative_path for binding in index.tasks
        if not compact_wave.plane.root.resolve(binding.nonattempt_event_relative_path, for_write=False).exists()), for_write=False)
    return SimpleNamespace(directory=directory, plane=compact_wave.plane, report=report,
        missing_receipt=missing_receipt, missing_event=missing_event,
        plan=plan, index=index, terminal=terminal)


@pytest.mark.parametrize("kind,sidecar", (("receipt", False), ("receipt", True), ("event", False), ("event", True)))
def test_initially_absent_control_pair_cannot_appear_during_batch(failed_control_case, monkeypatch, kind, sidecar):
    selected = failed_control_case
    path = selected.missing_receipt if kind == "receipt" else selected.missing_event
    if sidecar:
        path = path.with_name(path.name + ".manifest.json")
    original = artifacts._ScopedArtifactPlane.verify_manifests_members
    census, inside, touched = owner._operational_census, [], []
    def read_census(**kwargs):
        inside.append(True)
        try:
            return census(**kwargs)
        finally:
            inside.pop()
    def batch(self, manifests, *, validate_members):
        def consume(authenticated):
            if inside and not touched:
                touched.append(True)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"disclosed newly appearing control")
            return validate_members(authenticated)
        return original(self, manifests, validate_members=consume)
    monkeypatch.setattr(owner, "_operational_census", read_census)
    monkeypatch.setattr(owner, "_assemble_read_products", lambda **kwargs: pytest.fail("appearing control reached products"))
    monkeypatch.setattr(artifacts._ScopedArtifactPlane, "verify_manifests_members", batch)
    try:
        with pytest.raises((artifacts.ArtifactIdentityConflict, recovery_owner.RunRecoveryError), match="appeared"):
            with selected.plane.verification_scope() as plane:
                execution.read_recursive_wave(directory=selected.directory, artifact_writer=plane,
                    terminal_product_format="compact")
        assert touched
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.parametrize("damage", ("run", "task", "attempt", "logical", "schema"))
@pytest.mark.parametrize("route", ("serial", "plural"))
def test_actual_receipt_owner_semantic_checks_survive_shared_body(control_case, tmp_path, damage, route):
    # Exact disclosed software receipt bytes are published under a new test
    # root. This is a refusal control, never historical/scientific custody.
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
    selected = control_case.selected
    receipt = next(iter(selected.compact[1]["attempt_receipts"].values()))
    index = control_case.index
    event = recovery_owner.ExternalRunRecoveryStore(selected.plane).read_event(index,
        next(binding.attempts[0].event_relative_path for binding in index.tasks
            if binding.task_id == receipt.task_id))
    root = tmp_path / "receipt-semantic"; root.mkdir()
    contract = replace(selected.plane.root.contract, canonical_path=str(root), storage_root_id="software.receipt.semantic")
    plane = artifacts.ExternalArtifactPlane(artifacts.GuardedExternalRoot(contract), validators=selected.plane.validators)
    key = (receipt.run_id, receipt.task_id, receipt.attempt_id)
    if damage == "run":
        key = ("run.foreign.control", key[1], key[2])
    elif damage == "task":
        key = (key[0], "task.foreign.control", key[2])
    elif damage == "attempt":
        key = (key[0], key[1], "attempt.foreign.control")
    relative = receipt_owner.ExternalTaskReceiptStore._relative_path(*key)
    record = event if damage == "schema" else receipt
    logical = "task-receipt.wrong.control" if damage == "logical" else "task-receipt." + receipt.receipt_id
    plane.write(ArtifactWriteRequest(logical, relative, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "software.receipt.semantic", relative.rsplit("/", 1)[0], record.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    with plane.verification_scope() as scoped:
        store = receipt_owner.ExternalTaskReceiptStore(scoped)
        with pytest.raises(artifacts.ArtifactIdentityConflict):
            if route == "serial":
                store.read(*key)
            else:
                path, manifest = store._read_envelope(*key)
                scoped.verify_manifests_members((manifest,), validate_members=lambda authenticated:
                    store._read_body(*key, path, authenticated[relative]))


@pytest.mark.parametrize("damage", ("index", "run", "path", "schema"))
@pytest.mark.parametrize("route", ("serial", "plural"))
def test_actual_event_owner_semantic_checks_survive_shared_body(control_case, tmp_path, damage, route):
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
    selected, index = control_case.selected, control_case.index
    relative = index.tasks[0].attempts[0].event_relative_path
    event = recovery_owner.ExternalRunRecoveryStore(selected.plane).read_event(index, relative)
    record = event
    if damage == "index":
        index = replace(index, recovery_index_id="index.foreign.control")
    elif damage == "run":
        record = replace(event, run_id="run.foreign.control")
    elif damage == "path":
        relative += ".foreign"
    else:
        record = next(iter(selected.compact[1]["attempt_receipts"].values()))
    root = tmp_path / "event-semantic"; root.mkdir()
    contract = replace(selected.plane.root.contract, canonical_path=str(root), storage_root_id="software.event.semantic")
    plane = artifacts.ExternalArtifactPlane(artifacts.GuardedExternalRoot(contract), validators=selected.plane.validators)
    plane.write(ArtifactWriteRequest("software.event.semantic", relative, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "software.event.semantic", relative.rsplit("/", 1)[0], record.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    with plane.verification_scope() as scoped:
        recovery = recovery_owner.ExternalRunRecoveryStore(scoped)
        with pytest.raises(recovery_owner.RunRecoveryError):
            if route == "serial":
                recovery.read_event(index, relative)
            else:
                path, manifest = recovery._read_payload_envelope(relative, expected_schema=index.TASK_EVENT_SCHEMA,
                    maximum_bytes=scoped.custody_limits.recovery_event_bytes)
                def decode(authenticated):
                    payload = recovery._read_payload_body(path, authenticated[relative])
                    return recovery._decode_event_payload(index, relative, payload)
                scoped.verify_manifests_members((manifest,), validate_members=decode)


class _OriginalControlAccess:
    """Literal access seam, not a grant or scientific authority fixture."""

    def __init__(self):
        self.current_checks = 0
        self.members = []
        self.expired = False

    def require_current(self):
        self.current_checks += 1
        if self.expired:
            raise PermissionError("original control access expired before body consumption")

    def require_member(self, manifest):
        self.members.append(manifest)
        self.require_current()


def _guarded_census(case, plane, access, *, policy=True):
    return owner._operational_census(
        recovery=recovery_owner.ExternalRunRecoveryStore(plane),
        store=receipt_owner.ExternalTaskReceiptStore(plane), plan=case.plan,
        index=case.index, terminal=case.terminal, decode_products=False,
        _read_policy=execution._read_only_custody_policy(plane) if policy else None,
        original_input_access=access)


@pytest.mark.parametrize("context", ("verification_scope", "read_context"))
def test_original_aware_control_batch_preserves_complete_serial_census(control_case, context):
    counts, results = {}, {}
    for mode in ("serial", "batch"):
        access = _OriginalControlAccess()
        with _work() as work:
            with getattr(control_case.selected.plane, context)() as plane:
                results[mode] = _guarded_census(control_case, plane, access, policy=mode == "batch")
        counts[mode] = dict(work)
        assert access.current_checks > 2 * len(control_case.index.tasks)
        assert access.members == []  # Each singleton is an exact selected control.
    assert results["batch"] == results["serial"]
    assert len(results["batch"][1]) == len(results["batch"][2]) == len(control_case.index.tasks)
    if context == "verification_scope":
        assert counts["batch"]["snapshot_calls"] < counts["serial"]["snapshot_calls"]
        assert counts["batch"]["snapshot_paths"] < counts["serial"]["snapshot_paths"]
    else:
        # Serial read_context already guards each pending closure locally.
        # The batch adds one final union check before product admission:
        # receipt + event, each with body, sidecar and publication marker.
        # This safety check increases current-path work; it is not evidence
        # of lower latency. The separate doubled-roster test checks scaling.
        assert counts["batch"]["snapshot_calls"] <= counts["serial"]["snapshot_calls"] + 1
        final_union_paths = 6 * len(control_case.index.tasks)
        assert counts["batch"]["snapshot_paths"] <= counts["serial"]["snapshot_paths"] + final_union_paths


def test_original_control_batch_keeps_failed_missing_and_nonattempt_denominators(failed_control_case):
    results = {}
    for mode in ("serial", "batch"):
        with failed_control_case.plane.read_context() as plane:
            results[mode] = _guarded_census(failed_control_case, plane, _OriginalControlAccess(), policy=mode == "batch")
    assert results["batch"] == results["serial"]
    rows, events, receipts = results["batch"]
    assert len(rows) == len(failed_control_case.terminal.attempts)
    assert {row["task_id"] for row in rows} == {task.task_id for task in failed_control_case.plan.tasks}
    assert {row["operational_status"] for row in rows} <= {"FAILED", "BLOCKED"}
    assert events and receipts == {}
    assert not failed_control_case.missing_receipt.exists()
    assert not failed_control_case.missing_event.exists()


@pytest.mark.parametrize("kind,hook", (("receipt", "_read_body"), ("receipt", "_read_envelope"),
    ("event", "_read_payload_body"), ("event", "_read_payload_envelope"),
    ("custody", "verify_manifest_members")))
def test_original_control_batch_preserves_custom_owner_serial_hooks(control_case, monkeypatch, kind, hook):
    cls = {"receipt": receipt_owner.ExternalTaskReceiptStore,
        "event": recovery_owner.ExternalRunRecoveryStore, "custody": artifacts._ScopedArtifactPlane}[kind]
    original = getattr(cls, hook)
    seen, batches = [], []
    def called(self, *args, **kwargs):
        seen.append(True)
        return original(self, *args, **kwargs)
    def observe(frame, event, arg):
        if frame.f_code is owner._read_compact_control_census.__code__ and event == "call":
            batches.append(True)
    with control_case.selected.plane.read_context() as plane:
        expected = _guarded_census(control_case, plane, _OriginalControlAccess(), policy=False)
    monkeypatch.setattr(cls, hook, called)
    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        with control_case.selected.plane.read_context() as plane:
            actual = _guarded_census(control_case, plane, _OriginalControlAccess())
    finally:
        sys.setprofile(previous)
    assert actual == expected and seen and batches == []


def test_original_control_complete_small_and_doubled_rosters_have_linear_custody_work(control_case, tmp_path):
    """Closed metadata plans only; no acquisition or scientific result projection.

    Each new test plan is a complete topological prefix with its own exact
    recovery index and event publications. Its full declared control roster is
    consumed, rather than relabelling a partial original scientific report.
    """
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.provenance import ObjectIdentity

    counts = {}
    for task_count in (2, 4):
        root = tmp_path / ("original-control-roster-" + str(task_count))
        root.mkdir()
        contract = replace(control_case.selected.plane.root.contract, canonical_path=str(root),
            storage_root_id="software.original-control-roster." + str(task_count))
        plane = artifacts.ExternalArtifactPlane(artifacts.GuardedExternalRoot(contract),
            validators=control_case.selected.plane.validators,
            semantic_validations=control_case.selected.plane.semantic_validations)
        selected_ids = frozenset(control_case.plan.topological_task_ids()[:task_count])
        plan = replace(control_case.plan,
            execution_plan_id="plan.software.original-control-roster." + str(task_count),
            tasks=tuple(task for task in control_case.plan.tasks if task.task_id in selected_ids))
        index = type(control_case.index).from_execution_plan(plan, run_id=control_case.index.run_id,
            wave_id="wave.original-control-roster." + str(task_count))
        index.validate_plan(plan)
        index_pin = ObjectIdentity.from_record(index.recovery_index_id, index)
        terminal = replace(control_case.terminal, recovery_index=index_pin,
            attempts=tuple(row for row in control_case.terminal.attempts if row.task_id in selected_ids),
            completed_task_ids=tuple(sorted(selected_ids)))
        receipts = control_case.selected.compact[1]["attempt_receipts"]
        store = receipt_owner.ExternalTaskReceiptStore(plane)
        recovery = recovery_owner.ExternalRunRecoveryStore(plane)
        for binding in index.tasks:
            assert len(binding.attempts) == 1
            receipt = receipts[binding.attempts[0].attempt_id]
            store.commit(receipt, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
                outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
            recovery.record_receipt(index, receipt)
        case = SimpleNamespace(plan=plan, index=index, terminal=terminal)
        access = _OriginalControlAccess()
        with _work() as work:
            with plane.read_context() as reading:
                rows, events, actual_receipts = _guarded_census(case, reading, access)
        assert len(rows) == len(events) == len(actual_receipts) == task_count
        assert {row["task_id"] for row in rows} == selected_ids
        counts[task_count] = {**dict(work), "current_checks": access.current_checks,
            "tasks": task_count, "control_bodies": 2 * task_count}
    assert counts[4]["payloads"] == 2 * counts[2]["payloads"]
    assert counts[4]["snapshot_calls"] == counts[2]["snapshot_calls"]
    assert counts[4]["snapshot_paths"] == 2 * counts[2]["snapshot_paths"]
    assert counts[4]["current_checks"] <= 2 * counts[2]["current_checks"]
    (tmp_path / "original-control-roster-work.json").write_text(json.dumps({
        "claim": "complete synthetic control custody only; no scientific qualification",
        "acquisition_started": False, "observations": counts,
    }, sort_keys=True) + "\n")


@pytest.mark.parametrize("kind", ("receipt", "event"))
@pytest.mark.parametrize("moment", ("before-body", "after-body"))
def test_original_control_access_refreshes_at_each_body(control_case, kind, moment):
    access = _OriginalControlAccess()
    body = (receipt_owner.ExternalTaskReceiptStore._read_body if kind == "receipt"
        else recovery_owner.ExternalRunRecoveryStore._read_payload_body).__code__
    entered, previous_check = [], [0]

    def observe(frame, event, arg):
        if frame.f_code is body and event == "call":
            assert access.current_checks > previous_check[0]
            assert not access.expired, "protected control body reopened after expiry"
            entered.append(True)
            previous_check[0] = access.current_checks
        if moment == "before-body" and event == "call" and frame.f_code.co_name == (
                "consume_receipts" if kind == "receipt" else "consume_events"):
            access.expired = True
        if moment == "after-body" and frame.f_code is body and event == "return":
            access.expired = True

    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        with pytest.raises(PermissionError, match="original control access expired"):
            with control_case.selected.plane.read_context() as plane:
                _guarded_census(control_case, plane, access)
    finally:
        sys.setprofile(previous)
    assert bool(entered) is (moment == "after-body")


@pytest.mark.parametrize("kind", ("receipt", "event"))
@pytest.mark.parametrize("damage", ("body", "sidecar", "marker"))
def test_original_control_final_union_guard_rejects_same_stat_change(control_case, monkeypatch, kind, damage):
    path = control_case.receipt_path if kind == "receipt" else control_case.event_path
    manifest = control_case.selected.plane.read_manifest(path.relative_to(
        control_case.selected.plane.root.contract.canonical_path).as_posix())
    if damage == "sidecar":
        path = path.with_name(path.name + ".manifest.json")
    elif damage == "marker":
        path = control_case.selected.plane.root.resolve(manifest.publication.commit_marker_relative_path, for_write=False)
    raw, pinned = path.read_bytes(), path.stat()
    actual_stat = os.stat
    changed, escaped = [], []

    def same_stat(*args, **kwargs):
        # Model coarse metadata for this inode only. All content reads and
        # every custody method retain their actual stock implementations.
        observed = actual_stat(*args, **kwargs)
        if (observed.st_dev, observed.st_ino) == (pinned.st_dev, pinned.st_ino):
            return pinned
        return observed

    def mutate(frame, event, arg):
        if (frame.f_code.co_name == "consume_events" and event == "return"
                and frame.f_code.co_filename == owner.__file__ and not changed):
            path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
            changed.append(True)

    monkeypatch.setattr(os, "stat", same_stat)
    previous = sys.getprofile()
    try:
        sys.setprofile(mutate)
        with pytest.raises(artifacts.ArtifactIdentityConflict, match="changed"):
            with control_case.selected.plane.read_context() as plane:
                result = _guarded_census(control_case, plane, _OriginalControlAccess())
            escaped.append(result)
    finally:
        sys.setprofile(previous)
        path.write_bytes(raw)
    assert changed and escaped == []
