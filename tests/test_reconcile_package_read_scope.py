# SPDX-License-Identifier: MPL-2.0
"""Scope-bound package reuse over real disclosed public recovery metadata.

The existing fixture issues software-only canonical records and interrupts an
inline PURE callback. Real artifacts, package parsing, facade joins, current
operation checks and recovery writes remain owning implementation paths. The
programme test supplies its already-authenticated outer candidate/presentation
ports so this file measures the package lifetime independently of authoring.
No native acquisition, live scientific history or qualification is exercised.
"""

from copy import copy
from dataclasses import replace
from decimal import getcontext, localcontext
from pathlib import Path
from types import SimpleNamespace
from threading import Thread

import pytest

from empirical_lawhood.api import execution as execution_owner
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.results import ResumeCampaignRequest
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.infrastructure.artifacts import ArtifactPlaneError
from tests import test_reconcile_campaign_history as history

case = history.interrupted


def _counter(monkeypatch):
    original = execution_owner.loads_campaign_package_authoring
    calls = []

    def parse(*args, **kwargs):
        calls.append(len(args[0]))
        return original(*args, **kwargs)

    monkeypatch.setattr(execution_owner, "loads_campaign_package_authoring", parse)
    return calls


def _request(value):
    return ResumeCampaignRequest(value.index.run_id, confirmed=True,
        reconcile_only=True, reveal_authority_id=value.control.reveal.authority_id)


def _programme(value, monkeypatch, *, custom_factory=False):
    candidate = value.package.issued_study.candidate
    selected = SimpleNamespace(association=SimpleNamespace(
        candidate=ObjectIdentity.from_record(candidate.candidate_id, candidate)))
    # These are disclosed surrounding programme ports. They return the actual
    # fixture API/service and expected canonical candidate, never a package or
    # replacement reconciliation result. The entire facade and service run.
    monkeypatch.setattr(ExperimentProgrammeService, "_prospective_context",
        lambda _self, *_args, **_kwargs: (selected, value.control.api))
    monkeypatch.setattr(ExperimentProgrammeService, "_prospective_report",
        staticmethod(lambda result, _selected: result))
    return ExperimentProgrammeService(value.control.service.repo_root,
        value.plane, SimpleNamespace(maximum_parallel_tasks=1),
        prospective_api_factory=(lambda **_kwargs: value.control.api) if custom_factory else None)


def _paths(value):
    root = Path(value.plane.root.contract.canonical_path)
    body = value.plane.root.resolve(
        f"runs/{value.index.run_id}/plans/campaign-package.json", for_write=False)
    manifest = value.plane.read_manifest(body.relative_to(root).as_posix())
    return body, Path(str(body) + ".manifest.json"), value.plane.root.resolve(
        manifest.publication.commit_marker_relative_path, for_write=False)


def test_public_programme_reconciliation_parses_package_once(case, monkeypatch):
    calls = _counter(monkeypatch)
    original_service = case.control.api._execution_service
    original_plane = original_service.artifact_plane
    programme = _programme(case, monkeypatch)
    before_entries = tuple(case.executor.calls)
    result = programme.recover(directory=case.control.catalog.parent,
        maximum_parallel_tasks=1, request=_request(case))
    assert result.succeeded, (result.reason_codes, result.errors)
    assert result.payload.closure_only and result.payload.worker_entries == 0
    assert len(calls) == 1
    assert tuple(case.executor.calls) == before_entries
    assert case.control.api._execution_service is original_service
    assert original_service.artifact_plane is original_plane
    assert "_reconciliation_package_read" not in vars(original_service)


def test_direct_package_reads_keep_their_existing_uncached_path(case, monkeypatch):
    calls = _counter(monkeypatch)
    service = case.control.service
    first = service.load_persisted_package(case.index.run_id)
    second = service.load_persisted_package(case.index.run_id)
    assert first == second and first is not second
    assert len(calls) == 2


def test_scope_reuses_owned_record_and_closes_on_success(case, monkeypatch):
    calls = _counter(monkeypatch)
    service = case.control.service
    with service._reconciliation_package_read_scope(case.index.run_id) as selected:
        assert selected is not service
        first = selected.load_persisted_package(case.index.run_id)
        second = selected.load_persisted_package(case.index.run_id)
        assert first is second and len(calls) == 1
    assert selected._reconciliation_package_read.entry is None
    with pytest.raises(execution_owner.CampaignIdentityError, match="lifetime changed or ended"):
        selected.load_persisted_package(case.index.run_id)
    with service._reconciliation_package_read_scope(case.index.run_id) as later:
        assert later.load_persisted_package(case.index.run_id) is not first
    assert len(calls) == 2


def test_scope_closes_after_exception_and_nested_use_does_not_escape(case):
    with pytest.raises(RuntimeError, match="disclosed scope interruption"):
        with case.control.service._reconciliation_package_read_scope(case.index.run_id) as selected:
            first = selected.load_persisted_package(case.index.run_id)
            with selected._reconciliation_package_read_scope(case.index.run_id) as nested:
                assert nested is selected
                assert nested.load_persisted_package(case.index.run_id) is first
            raise RuntimeError("disclosed scope interruption")
    assert selected._reconciliation_package_read.entry is None
    with pytest.raises(execution_owner.CampaignIdentityError, match="lifetime changed or ended"):
        selected.load_persisted_package(case.index.run_id)


def test_decimal_context_does_not_reuse_another_semantic_parse(case, monkeypatch):
    calls = _counter(monkeypatch)
    with case.control.service._reconciliation_package_read_scope(case.index.run_id) as selected:
        original = selected.load_persisted_package(case.index.run_id)
        with localcontext() as context:
            context.prec = getcontext().prec + 1
            changed = selected.load_persisted_package(case.index.run_id)
        assert changed is not original and changed == original
    assert len(calls) == 2


@pytest.mark.parametrize("target", ("body", "body-replaced", "body-mode", "body-link", "sidecar", "marker"))
def test_mutated_positive_custody_refuses_scope_reuse(case, target):
    body, sidecar, marker = _paths(case)
    selected_path = {"sidecar": sidecar, "marker": marker}.get(target, body)
    payload, mode = selected_path.read_bytes(), selected_path.stat().st_mode & 0o777
    retained = selected_path.with_name(selected_path.name + ".disclosed-read-scope-backup")
    assert not retained.exists()
    stages = []
    try:
        with case.control.service._reconciliation_package_read_scope(case.index.run_id) as selected:
            selected.load_persisted_package(case.index.run_id)
            stages.append("authenticated")
            if target == "body-mode":
                selected_path.chmod(mode ^ 0o100)
            elif target in ("body-replaced", "body-link"):
                selected_path.rename(retained)
                if target == "body-link":
                    selected_path.symlink_to(retained)
                else:
                    selected_path.write_bytes(payload)
            else:
                # Keep size equal so this cannot pass on a size-only check.
                selected_path.write_bytes(payload[:-1] + (b"X" if payload[-1:] != b"X" else b"Y"))
            stages.append("mutated")
            with pytest.raises(ArtifactPlaneError):
                selected.load_persisted_package(case.index.run_id)
            stages.append("reuse_refused")
            # Scope exit itself also refuses a changed positive union.
            with pytest.raises(ArtifactPlaneError):
                selected._require_reconciliation_package_snapshot()
            stages.append("snapshot_refused")
            # Restore only after both actual guards have refused. The final
            # guard retains ctime/identity and still refuses restored bytes.
    except ArtifactPlaneError:
        pass
    finally:
        if retained.exists():
            selected_path.unlink()
            retained.rename(selected_path)
        else:
            selected_path.write_bytes(payload)
        selected_path.chmod(mode)
    assert stages == ["authenticated", "mutated", "reuse_refused", "snapshot_refused"]


def test_changed_package_before_effects_refuses_without_opening_catalog(case, monkeypatch):
    body, _, _ = _paths(case)
    payload = body.read_bytes()
    calls = []
    phases = []
    service = case.control.service
    original_check = execution_owner.CampaignExecutionService._validate_issued_reveal_authority

    def after_current_reveal(self, package, **options):
        result = original_check(self, package, **options)
        phases.append("current_reveal_passed")
        body.write_bytes(payload[:-1] + b"X")
        return result

    monkeypatch.setattr(execution_owner.CampaignExecutionService,
        "_validate_issued_reveal_authority", after_current_reveal)
    monkeypatch.setattr(service, "engine_factory", lambda: calls.append("catalog") or pytest.fail("catalog opened after changed package"))
    try:
        with pytest.raises(ArtifactPlaneError):
            with service._reconciliation_package_read_scope(case.index.run_id) as selected:
                selected.reconcile_failed_history(case.index.run_id,
                    at_utc=case.control.api._study_issue_clock.now_utc(),
                    reveal_authority_id=case.control.reveal.authority_id)
    finally:
        body.write_bytes(payload)
    assert calls == [] and phases == ["current_reveal_passed"]


def test_current_execution_authority_is_not_a_package_cache_verdict(case, monkeypatch):
    service = case.control.service
    original_store = service.study_authority_store
    calls = []

    class SubstitutedCurrentAuthority:
        def load(self, identity):
            record = original_store.load(identity)
            if identity == case.package.execution_authority.authority_id:
                return replace(record, authority_id="authority.disclosed.foreign-current")
            return record

    with service._reconciliation_package_read_scope(case.index.run_id) as selected:
        selected.load_persisted_package(case.index.run_id)
        selected.study_authority_store = SubstitutedCurrentAuthority()
        selected.engine_factory = lambda: calls.append("catalog") or pytest.fail("catalog opened with a substituted current grant")
        with pytest.raises(execution_owner.CampaignValidationError, match="execution authority replay failed"):
            selected.reconcile_failed_history(case.index.run_id,
                at_utc=case.control.api._study_issue_clock.now_utc(),
                reveal_authority_id=case.control.reveal.authority_id)
    assert calls == []


def test_custody_plane_source_and_run_cannot_be_substituted(case):
    with case.control.service._reconciliation_package_read_scope(case.index.run_id) as selected:
        selected.load_persisted_package(case.index.run_id)
        with pytest.raises(execution_owner.CampaignIdentityError, match="original run"):
            selected.load_persisted_package("run.disclosed.foreign")
        selected.artifact_plane = case.control.service.artifact_plane
        with pytest.raises(execution_owner.CampaignIdentityError, match="lifetime changed or ended"):
            selected.load_persisted_package(case.index.run_id)
        # Restore the exact owner so this test can finish its valid scope.
        selected.artifact_plane = selected._reconciliation_package_read.plane


@pytest.mark.parametrize("hook", ("service", "plane", "factory"))
def test_custom_paths_keep_existing_validation_and_parse_behavior(case, monkeypatch, hook):
    service = case.control.service
    plane = service.artifact_plane
    calls = _counter(monkeypatch)
    validations = []
    original_service_attributes = set(vars(service))
    original_plane_attributes = set(vars(plane))
    try:
        # Undoing setattr(instance, inherited_method, ...) restores a bound
        # method as an instance attribute. Keep that ordinary pytest behavior
        # local, then remove ONLY attributes absent before this disclosed hook.
        with monkeypatch.context() as hooks:
            if hook == "service":
                original = service._load_package
                hooks.setattr(service, "_load_package",
                    lambda run: validations.append(run) or original(run))
            elif hook == "plane":
                original = plane.verify_manifest
                hooks.setattr(plane, "verify_manifest",
                    lambda manifest: validations.append(manifest) or original(manifest))
            if hook == "factory":
                programme = _programme(case, hooks, custom_factory=True)
                result = programme.recover(directory=case.control.catalog.parent,
                    maximum_parallel_tasks=1, request=_request(case))
                assert result.succeeded, (result.reason_codes, result.errors)
                assert len(calls) == 3
            else:
                with service._reconciliation_package_read_scope(case.index.run_id) as selected:
                    assert selected is service
                    selected.load_persisted_package(case.index.run_id)
                    selected.load_persisted_package(case.index.run_id)
                assert len(calls) == 2 and len(validations) >= 2
    finally:
        if "_load_package" not in original_service_attributes:
            vars(service).pop("_load_package", None)
        if "verify_manifest" not in original_plane_attributes:
            vars(plane).pop("verify_manifest", None)
    assert set(vars(service)) == original_service_attributes
    assert set(vars(plane)) == original_plane_attributes


def test_an_expected_package_or_fabricated_scope_is_not_cache_provenance(case):
    selected = copy(case.control.service)
    selected._reconciliation_package_read = SimpleNamespace(
        entry=(None, None, case.package), active=True)
    with pytest.raises(execution_owner.CampaignIdentityError, match="not its owned scope"):
        selected.load_persisted_package(case.index.run_id)


def test_scope_is_owned_by_one_thread_and_independent_scopes_do_not_share(case):
    results = []
    with case.control.service._reconciliation_package_read_scope(case.index.run_id) as selected:
        original = selected.load_persisted_package(case.index.run_id)

        def foreign_use():
            try:
                selected.load_persisted_package(case.index.run_id)
            except execution_owner.CampaignIdentityError as error:
                results.append(str(error))
            else:
                results.append("incorrectly accepted a foreign thread")

        worker = Thread(target=foreign_use)
        worker.start()
        worker.join(timeout=10)
        assert not worker.is_alive()
        assert len(results) == 1 and "lifetime changed or ended" in results[0]
        with case.control.service._reconciliation_package_read_scope(case.index.run_id) as other:
            assert other is not selected
            assert other.load_persisted_package(case.index.run_id) is not original
        assert selected.load_persisted_package(case.index.run_id) is original
