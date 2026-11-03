# SPDX-License-Identifier: MPL-2.0
"""Real synthetic issued-parent custody; no scientific qualification or native work."""

from dataclasses import replace
from datetime import UTC, datetime
from collections import Counter
import sys

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.api import matrix_sampling_runtime as owner, recursive_qualified_parents as parents
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane, _has_stock_manifest_reads
from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
from tests.runtime_platform.test_recursive_prospective_parents import parent_fixture as parent_fixture


def _selected(fixture):
    package, plan = fixture.package, fixture.execution_plan
    prefixes = tuple(sorted(value.capability_key for value in package.registry.capabilities))
    semantic = parents._semantic_writer(package, plan, fixture.plane, fixture.handoff.compilation.output_codecs)
    closure = parents._collect_receipt_closure(package, plan, semantic, fixture.reveal, prefixes)
    selected = []
    for task in plan.tasks[:4]:
        receipt = closure.by_task[task.task_id]
        logical = receipt.output_logical_artifacts[0]
        record = ObjectIdentity(logical.logical_artifact_id, logical.payload_schema, "1.0.0", logical.content_sha256)
        binding = RecursivePriorExecutionBinding("prior." + task.task_id,
            ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study),
            ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority),
            ObjectIdentity.from_record(package.package_id, package),
            ObjectIdentity.from_record(plan.execution_plan_id, plan), receipt.run_id, receipt.task_id,
            ObjectIdentity.from_record(receipt.receipt_id, receipt), logical.logical_artifact_id, record)
        selected.append((MatrixSelectedOriginalProduct(binding,
            ObjectIdentity.from_record(fixture.reveal.authority_id, fixture.reveal)), record))
    assert len(selected) == 4
    return tuple(selected), closure


def _read(fixture, selected, **kwargs):
    return owner._original_products(fixture.plane, selected, fixture.handoff.compilation.output_codecs, **kwargs)


def test_actual_four_products_stream_one_complete_closure_with_fresh_grants_and_custom_writer(
        parent_fixture, monkeypatch):
    fixture = parent_fixture
    selected, _ = _selected(fixture)
    expected = tuple(owner._original_product(fixture.plane, original, pin,
        fixture.handoff.compilation.output_codecs) for original, pin in selected)
    calls = {"payload_passes": 0, "metadata_passes": 0, "fresh_authority": 0}
    for module, name, key in ((parents, "_verify_receipt_closure", "payload_passes"),
            (parents, "_collect_receipt_closure", "metadata_passes"),
            (owner, "_replay_parent_authority", "fresh_authority")):
        actual = getattr(module, name)
        def counted(*args, _actual=actual, _key=key, **kwargs):
            calls[_key] += 1
            return _actual(*args, **kwargs)
        monkeypatch.setattr(module, name, counted)
    seen = []
    def scope(**kwargs):
        seen.append((kwargs["binding"].task_id, kwargs["receipt"].task_id))
        assert kwargs["writer"].root is fixture.plane.root
    assert _read(fixture, selected, scope_validator=scope) == expected
    assert len(seen) == 4
    assert calls == {"payload_passes": 1, "metadata_passes": 2, "fresh_authority": 8}
    assert fixture.executor.invocations == 5


def test_missing_unselected_dependency_refuses_before_any_product(parent_fixture, monkeypatch):
    fixture = parent_fixture
    selected, _ = _selected(fixture)
    missing = fixture.execution_plan.tasks[-1].task_id
    assert missing not in {value.prior_execution.task_id for value, _ in selected}
    actual = ExternalTaskReceiptStore.read_by_receipt_id
    monkeypatch.setattr(ExternalTaskReceiptStore, "read_by_receipt_id",
        lambda self, run, task, receipt: None if task == missing else actual(self, run, task, receipt))
    monkeypatch.setattr(owner, "_output_payload", lambda *args: pytest.fail("payload before complete original receipts"))
    with pytest.raises(PermissionError, match="dependency"):
        _read(fixture, selected)


def test_current_reveal_is_replayed_after_the_complete_read(parent_fixture, monkeypatch):
    fixture = parent_fixture
    selected, _ = _selected(fixture)
    actual = owner._replay_parent_authority
    calls = 0
    def expires(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls > len(selected):
            raise PermissionError("actual original reveal expired")
        return actual(*args, **kwargs)
    monkeypatch.setattr(owner, "_replay_parent_authority", expires)
    with pytest.raises(PermissionError, match="reveal expired"):
        _read(fixture, selected)


def test_nonselected_payload_mutation_during_products_refuses_before_return(parent_fixture, monkeypatch):
    fixture = parent_fixture
    selected, closure = _selected(fixture)
    producing = closure.by_task[fixture.execution_plan.tasks[-1].task_id]
    path = fixture.plane.root.resolve(producing.output_materializations[0].relative_path, for_write=False)
    before = path.read_bytes()
    actual = owner._output_payload
    calls = 0
    def changes_after_last(*args):
        nonlocal calls
        result = actual(*args)
        calls += 1
        if calls == len(selected):
            path.write_bytes(before + b" ")
        return result
    monkeypatch.setattr(owner, "_output_payload", changes_after_last)
    try:
        with pytest.raises((ArtifactIdentityConflict, PermissionError)):
            _read(fixture, selected)
    finally:
        path.write_bytes(before)


def test_changed_receipt_census_after_products_refuses_without_second_payload_pass(parent_fixture, monkeypatch):
    fixture = parent_fixture
    selected, _ = _selected(fixture)
    actual = parents._collect_receipt_closure
    calls = 0
    def changed(*args):
        nonlocal calls
        value = actual(*args)
        calls += 1
        return value if calls == 1 else replace(value, manifests=value.manifests[:-1])
    monkeypatch.setattr(parents, "_collect_receipt_closure", changed)
    with pytest.raises(PermissionError, match="receipt closure changed"):
        _read(fixture, selected)


def test_guarded_writer_semantic_admission_cannot_be_bypassed(parent_fixture, monkeypatch):
    fixture = parent_fixture
    selected, _ = _selected(fixture)
    def refuse(*args, **kwargs):
        raise PermissionError("actual selected writer rejects semantic admission")
    monkeypatch.setattr(type(fixture.plane), "with_semantic_validation_registry", refuse)
    with pytest.raises(PermissionError, match="selected writer rejects"):
        _read(fixture, selected)


@pytest.mark.parametrize("change", ("duplicate", "foreign-run", "false-scope"))
def test_batch_refuses_alias_foreign_run_and_false_scope_before_return(parent_fixture, change):
    selected, _ = _selected(parent_fixture)
    kwargs = {}
    if change == "duplicate":
        selected = (*selected[:-1], selected[0])
    elif change == "foreign-run":
        original, expected = selected[0]
        selected = ((replace(original, prior_execution=replace(original.prior_execution,
            run_id="run.other-original")), expected), *selected[1:])
    else:
        kwargs["scope_validator"] = lambda **kwargs: True
    with pytest.raises(PermissionError):
        _read(parent_fixture, selected, **kwargs)


def _issued_compilation_report(fixture):
    """Select the actual pinned publication member, not a neighboring file."""
    report, = (member for member in fixture.package.issued_study.base.members
        if member.relative_path.endswith("/standard-compilation-report.json"))
    manifest = fixture.plane.read_manifest(report.relative_path)
    assert manifest.logical.logical_artifact_id == report.member_id
    assert manifest.materialization.size_bytes == report.size_bytes
    assert manifest.materialization.physical_sha256 == report.physical_sha256
    assert manifest.publication is not None
    return report, manifest


@pytest.mark.parametrize("damage", ("report", "sidecar", "commit"))
def test_original_control_finalization_refuses_same_size_publication_mutation(parent_fixture, monkeypatch, damage):
    """Disclosed issued controls remain exact through the last product read."""
    fixture = parent_fixture
    selected, _ = _selected(fixture)
    report, manifest = _issued_compilation_report(fixture)
    relative = (manifest.publication.commit_marker_relative_path if damage == "commit"
        else report.relative_path + (".manifest.json" if damage == "sidecar" else ""))
    path = fixture.plane.root.resolve(relative, for_write=False)
    before = path.read_bytes()
    changed = bytes((before[0] ^ 1,)) + before[1:]
    assert len(changed) == len(before) and changed != before
    actual = owner._output_payload
    calls = 0
    def mutate_after_last_product(*args):
        nonlocal calls
        result = actual(*args)
        calls += 1
        if calls == len(selected):
            path.write_bytes(changed)
        return result
    monkeypatch.setattr(owner, "_output_payload", mutate_after_last_product)
    try:
        with pytest.raises(ArtifactIdentityConflict):
            _read(fixture, selected)
        assert calls == len(selected)
    finally:
        path.write_bytes(before)
        assert path.read_bytes() == before
    assert fixture.executor.invocations == 5


def test_original_reveal_expiring_during_final_control_hash_refuses_return(parent_fixture, monkeypatch):
    """The final byte scan cannot turn an earlier current grant into a verdict."""
    fixture = parent_fixture
    selected, _ = _selected(fixture)
    report, _ = _issued_compilation_report(fixture)
    report_path = fixture.plane.root.resolve(report.relative_path, for_write=False)
    snapshot = ExternalArtifactPlane._require_verification_snapshot_paths.__code__
    authority_replay = parents._replay_parent_authority.__code__
    state = {"replays": 0, "expired_after_control_snapshot": False}
    class AccessClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2030 if state["expired_after_control_snapshot"] else 2026, 10, 21, tzinfo=UTC)
    monkeypatch.setattr(parents, "datetime", AccessClock)
    def observe(frame, event, _arg):
        if event == "return" and frame.f_code is authority_replay:
            state["replays"] += 1
        elif (event == "return" and frame.f_code is snapshot
                and state["replays"] == 2 * len(selected)
                and report_path in frame.f_locals["snapshots"]):
            state["expired_after_control_snapshot"] = True
    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        with pytest.raises(PermissionError, match="expired"):
            _read(fixture, selected)
    finally:
        sys.setprofile(previous)
    assert state == {"replays": 8, "expired_after_control_snapshot": True}
    assert fixture.executor.invocations == 5


def test_original_report_hash_work_is_bounded_while_actual_authorities_stay_fresh(parent_fixture):
    """Observe real hash/load calls without replacing the stock custody policy."""
    fixture = parent_fixture
    selected, _ = _selected(fixture)
    report, _ = _issued_compilation_report(fixture)
    report_path = fixture.plane.root.resolve(report.relative_path, for_write=False)
    physical = ExternalArtifactPlane._verify_manifest_snapshot.__code__
    digest = bounded_file_sha256.__code__
    grant = ExternalStudyOperationAuthorityStore.load.__code__
    replay = parents._replay_parent_authority.__code__
    assert _has_stock_manifest_reads(fixture.plane)
    observations = {}
    for count in (1, 4):
        calls = Counter()
        def observe(frame, event, _arg):
            if event != "call":
                return
            if frame.f_code is physical and frame.f_locals["manifest"].materialization.relative_path == report.relative_path:
                calls["report_physical_hashes"] += 1
            elif frame.f_code is digest and frame.f_locals["path"] == report_path:
                calls["report_snapshot_hashes"] += 1
            elif frame.f_code is replay:
                calls["authority_replays"] += 1
            elif frame.f_code is grant:
                authority = frame.f_locals["authority_id"]
                if authority == fixture.reveal.authority_id:
                    calls["stored_reveal_loads"] += 1
                elif authority == fixture.package.execution_authority.authority_id:
                    calls["stored_execution_loads"] += 1
        previous = sys.getprofile()
        sys.setprofile(observe)
        try:
            values = _read(fixture, selected[:count])
        finally:
            sys.setprofile(previous)
        assert len(values) == count
        observations[count] = calls
        assert calls["report_physical_hashes"] == 1
        assert 0 < calls["report_snapshot_hashes"] <= 8
        assert calls["authority_replays"] == 2 * count
        # Before/after every publication replay, plus one final plural check.
        assert calls["stored_reveal_loads"] >= 4 * count + 1
        assert calls["stored_execution_loads"] >= 4 * count + 1
    assert observations[4]["report_snapshot_hashes"] == observations[1]["report_snapshot_hashes"]
    assert observations[4]["stored_reveal_loads"] > observations[1]["stored_reveal_loads"]
    assert fixture.executor.invocations == 5
