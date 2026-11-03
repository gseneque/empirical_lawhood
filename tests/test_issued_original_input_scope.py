# SPDX-License-Identifier: MPL-2.0
"""Disclosed software access callbacks around real stored issue/control custody.

These controls create no original scientific grant and never enter a worker.
The existing fixture owns the actual issued package, plan and stored effect grant.
"""
import pytest

from empirical_lawhood.api import current_task_custody as owner
from tests.test_current_native_entry_authority import FutureClock, disclosed_contract
from tests.test_current_result_custody import actual_issued_current_task_controls as actual_issued_current_task_controls


class _DisclosedOriginalScope:
    parents = ()

    def __init__(self, writer):
        self.writer = writer
        self.revoked = False
        self.calls = 0
        self.original_reads = 0
        root = writer.root.verify(for_write=False)
        self.facts = set()
        # Exact real sidecar facts only. No native receipt or scientific
        # permission is manufactured by this disclosed callback fixture.
        for sidecar in root.rglob("*.manifest.json"):
            relative = sidecar.relative_to(root).as_posix().removesuffix(".manifest.json")
            manifest = writer.read_manifest(relative)
            self.facts.add((manifest.logical, manifest.materialization))

    def require_current(self, *, artifact_writer=None):
        if artifact_writer is not None:
            assert artifact_writer.root.contract == self.writer.root.contract
        self.calls += 1
        if self.revoked:
            raise PermissionError("disclosed original read grant expired")

    def require_issued_member(self, manifest):
        self.require_current()
        if (manifest.logical, manifest.materialization) not in self.facts:
            raise PermissionError("disclosed original scope refuses an unknown member")

    def require_original_member(self, manifest):
        self.require_current()
        self.original_reads += 1
        if (manifest.logical, manifest.materialization) not in self.facts:
            raise PermissionError("disclosed original replay refuses an unknown member")


def test_original_scope_controls_survive_own_effect_expiry_but_ready_refuses(
        actual_issued_current_task_controls, monkeypatch):
    f = actual_issued_current_task_controls
    contract = disclosed_contract(f)
    scope = _DisclosedOriginalScope(f.control.service.artifact_plane)
    custody = owner.CurrentIssuedTaskCustody(writer=scope.writer,
        reveal_authority_id=f.control.reveal.authority_id, original_input_access=scope)
    assert custody.current_task(f.context, f.runner)[1] == f.plan
    custody.require_native_entry(f.context, f.runner, prepared_contract=contract)
    calls = scope.calls
    monkeypatch.setattr(owner, "datetime", FutureClock)
    assert custody.current_task(f.context, f.runner)[1] == f.plan
    assert scope.calls > calls
    with pytest.raises(PermissionError, match="expired"):
        custody.require_native_entry(f.context, f.runner, prepared_contract=contract)
    assert not f.control.executor.invocations


def test_original_read_expiry_refuses_controls_before_own_grant_or_body_access(
        actual_issued_current_task_controls, monkeypatch):
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    from empirical_lawhood.infrastructure import artifacts
    f = actual_issued_current_task_controls
    disclosed_contract(f)
    scope = _DisclosedOriginalScope(f.control.service.artifact_plane)
    custody = owner.CurrentIssuedTaskCustody(writer=scope.writer,
        reveal_authority_id=f.control.reveal.authority_id, original_input_access=scope)
    assert custody.current_task(f.context, f.runner)[1] == f.plan
    scope.revoked = True
    paths = {scope.writer.root.resolve(material.relative_path, for_write=False) for _, material in scope.facts}
    original_open = artifacts.os.open

    def refuse_body_open(path, *args, **kwargs):
        from pathlib import Path
        if isinstance(path, (str, Path)) and Path(path) in paths:
            pytest.fail("an original-scoped body was opened after its current read grant expired")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(artifacts.os, "open", refuse_body_open)
    original_load = ExternalStudyOperationAuthorityStore.load
    loads = []

    def observe_load(self, authority_id):
        loads.append(authority_id)
        return original_load(self, authority_id)

    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, "load", observe_load)
    with pytest.raises(PermissionError, match="original read grant expired"):
        custody.current_task(f.context, f.runner)
    assert loads == []
    assert not f.control.executor.invocations


def test_original_replay_uses_explicit_original_member_owner_before_body_and_final_hash(
        actual_issued_current_task_controls, monkeypatch):
    f = actual_issued_current_task_controls
    scope = _DisclosedOriginalScope(f.control.service.artifact_plane)
    custody = owner.CurrentIssuedTaskCustody(writer=scope.writer,
        reveal_authority_id=f.control.reveal.authority_id, original_input_access=scope)
    sidecar = next(scope.writer.root.verify(for_write=False).rglob("*.manifest.json"))
    relative = sidecar.relative_to(scope.writer.root.verify(for_write=False)).as_posix().removesuffix(".manifest.json")
    manifest = scope.writer.read_manifest(relative)

    def no_child_member(_manifest):
        pytest.fail("original replay selected the child's future-input member owner")

    monkeypatch.setattr(scope, 'require_issued_member', no_child_member)
    with custody.original_read_scope() as (reading, _):
        reading.verify_manifest(manifest)
        calls = scope.original_reads
        assert calls > 0
    assert scope.original_reads > calls
    assert not f.control.executor.invocations
