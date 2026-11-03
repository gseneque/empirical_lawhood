# SPDX-License-Identifier: MPL-2.0
"""Disclosed software custody controls; no native science or fresh qualification."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as records
from empirical_lawhood.api import recursive_execution as api
from empirical_lawhood.api.experiment_preparation import author_prepared_experiment
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.recursive_authoring import load_authored_wave
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, LocalScheduler, ResourceAdmissionError
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore, RunRecoveryError, settled_recovery_tasks
from empirical_lawhood.infrastructure.sql import create_catalog_engine, upgrade_catalog, SQLiteOperationalRepository
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.runtime.execution import TaskBlockReason
from tests.test_matrix_native_utility import copied_preparation, utility_case

ROOT = Path(__file__).parents[1]


class DisclosedStop(RuntimeError):
    pass


def _forbidden(*args, **kwargs):
    pytest.fail("custody-only recovery entered task/native execution")


@pytest.fixture
def unclosed_case(tmp_path, monkeypatch):
    """Reproduce an original closure defect using only potential-contact fixtures."""
    def build(*, unentered=False):
        case = utility_case(tmp_path, root_count=2)
        case.specification = replace(case.specification, criterion=replace(case.specification.criterion,
            alpha_numerator=1, alpha_denominator=280))
        case.acquisition = records.acquisition_seal(case.specification, case.request)
        prepared = copied_preparation(case, tmp_path / "copied")
        directory = Path(case.plane.root.contract.canonical_path) / "unclosed-initial-e2"
        author_prepared_experiment(preparation=prepared, project_root=ROOT, artifact_writer=case.plane, output_dir=directory)
        first, second = case.specification.root_ids
        execute = LocalProcessExecutor.execute
        from empirical_lawhood.infrastructure import source_closure
        archives, git = [], source_closure._git
        def observe_git(root, *arguments):
            if arguments[0] == "archive":
                archives.append(arguments)
            return git(root, *arguments)
        with monkeypatch.context() as control:
            control.setattr(source_closure, "_git", observe_git)
            control.setattr(bindings, "execute_parameter_native_work", _forbidden)
            control.setattr(bindings, "execute_paired_response_native_work", _forbidden)
            if unentered:
                control.setattr(LocalScheduler, "execute", lambda *args, **kwargs: (_ for _ in ()).throw(DisclosedStop()))
                with pytest.raises(DisclosedStop):
                    api.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=case.plane,
                        maximum_parallel_tasks=4)
            else:
                dispatched = []
                def stop_native(self, runner, context, **kwargs):
                    if context.task_id in (owner.task_id(first, "prefix"), owner.task_id(second, "prefix")):
                        # This ordinary DEV path uses execute, with the actual
                        # prepared contract and parent-entry callback. No native
                        # task is forwarded to a process or scientific body.
                        assert kwargs["prepared_contract"].native_effect
                        assert callable(kwargs["native_entry"])
                        dispatched.append(context.task_id)
                        if context.task_id == owner.task_id(first, "prefix"):
                            contact, _ = kwargs["native_entry"]()
                            assert (contact.run_id, contact.task_id, contact.attempt_id) == (
                                context.run_id, context.task_id, context.attempt_id)
                            raise ResourceAdmissionError("disclosed potential contact, no native executor")
                        raise ResourceAdmissionError("disclosed no-contact exhausted refusal")
                    return execute(self, runner, context, **kwargs)
                control.setattr(LocalProcessExecutor, "execute", stop_native)
                # Refuse any unexpected resource-envelope transport before it
                # can launch a child; this fixture supplies no such envelope.
                control.setattr(LocalProcessExecutor, "_execute_deadline_free", _forbidden)
                # Omit terminal publication while keeping the real attempts,
                # PURE entry receipt and one potential-contact marker intact.
                control.setattr(ExternalRunRecoveryStore, "record_terminal", lambda *args, **kwargs: None)
                partial = api.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=case.plane,
                    maximum_parallel_tasks=4)
                assert sorted(dispatched) == sorted(owner.task_id(root, "prefix") for root in (first, second))
                assert partial["status"] == "PARTIAL" and partial["operational_terminal"] == "ABSENT"
                assert partial["terminal_product_format"] == "compact" and partial["typed_product_validation"] == "DEFERRED"
                assert partial["scientific_completion"] == "NOT_ASSESSED_BY_COMPACT_CUSTODY"
                assert partial["qualification"] == "NOT_ESTABLISHED"
                # Potential parent entry is not a scientific/native result.
                assert partial["native_contact"] == "possible" and partial["new_native_contact_count"] == 1
                census = {row["task_id"]: row for row in partial["task_census"]}
                assert partial["task_count"] == len(census) == 18
                assert sum(row["operational_status"] == "SUCCEEDED" for row in census.values()) == 1
                assert (census[owner.task_id(first, "prefix")]["operational_status"],
                    census[owner.task_id(first, "prefix")]["reason_code"]) == ("BLOCKED", TaskBlockReason.UNKNOWN_COMPLETION.value)
                assert (census[owner.task_id(second, "prefix")]["operational_status"],
                    census[owner.task_id(second, "prefix")]["reason_code"]) == ("BLOCKED", TaskBlockReason.RESOURCE_COMPUTABILITY_UNAVAILABLE.value)
                assert sum(row["operational_status"] == "NO_COMPLETION_RECEIPT" for row in census.values()) == 15
        assert len(archives) == 1
        _, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=case.plane, lazy_payloads=True)
        run, plan, index = api._retained_plans(payloads, draft)
        assert ExternalRunRecoveryStore(case.plane).read_terminal(index) is None
        assert all(index.task(owner.task_id(root, "prefix")).maximum_attempts == 1 for root in (first, second))
        return SimpleNamespace(case=case, directory=directory, plan=plan, index=index, run=run)
    return build


def _recover(value):
    return api.recover_recursive_custody(directory=value.directory, project_root=ROOT, artifact_writer=value.case.plane)


def _attempts(value):
    engine = create_catalog_engine("sqlite+pysqlite:///:memory:")
    try:
        upgrade_catalog(engine)
        repository = SQLiteOperationalRepository(engine)
        ExternalRunRecoveryStore(value.case.plane).reconcile(value.index, value.plan, repository,
            ExternalTaskReceiptStore(value.case.plane), repair_missing_events=False)
        return repository.attempts(value.index.run_id)
    finally:
        engine.dispose()


def test_public_custody_only_closes_exhausted_dependency_chain_without_executor_or_new_contact(unclosed_case, monkeypatch):
    value = unclosed_case()
    original = api._custody_control_pins(value.case.plane, value.index)
    from empirical_lawhood.infrastructure import source_closure
    archives, git = [], source_closure._git
    def observe_git(root, *arguments):
        if arguments[0] == "archive":
            archives.append(arguments)
        return git(root, *arguments)
    monkeypatch.setattr(source_closure, "_git", observe_git)
    monkeypatch.setattr(LocalProcessExecutor, "__init__", _forbidden)
    monkeypatch.setattr(LocalScheduler, "__init__", _forbidden)
    monkeypatch.setattr(api, "operation_runners", _forbidden)
    monkeypatch.setattr(bindings, "execute_parameter_native_work", _forbidden)
    monkeypatch.setattr(bindings, "execute_paired_response_native_work", _forbidden)
    report = ExperimentProgrammeService(ROOT, value.case.plane).recover(directory=value.directory, custody_only=True)
    assert report["status"] == "BLOCKED" and report["operational_terminal"] == "AUTHENTICATED"
    assert report["completed_task_count"] == 1 and report["closed_non_success_task_count"] == 17
    assert len(report["proved_unreachable_task_ids"]) == 15
    assert report["new_native_contact_count"] == 0 and report["scientific_execution_performed"] is False
    assert report["scientific_completion"] == "DEFERRED_TO_EXPLICIT_FULL_READ"
    assert report["qualification"] == "NOT_ESTABLISHED"
    assert len(archives) == 1
    assert report["read_side_source_before"]["tracked_files"] == report["read_side_source_after"]["tracked_files"]
    after = api._custody_control_pins(value.case.plane, value.index)
    allowed = {value.index.terminal_event_relative_path,
        *(value.index.task(key).nonattempt_event_relative_path for key in report["proved_unreachable_task_ids"])}
    allowed |= {path + ".manifest.json" for path in tuple(allowed)}
    assert tuple(row for row in original if row[0] not in allowed) == tuple(row for row in after if row[0] not in allowed)
    replay = _recover(value)
    assert len(archives) == 2
    assert replay["terminal"] == report["terminal"]
    assert api._custody_control_pins(value.case.plane, value.index) == after
    full = ExperimentProgrammeService(ROOT, value.case.plane).read(directory=value.directory)
    counts = full["scientific_result"]["denominators"]["native-utility"]
    assert counts["assigned_units"] == counts["missing_units"] == 2
    assert counts["successes"] == counts["usable_units"] == 0


def test_custody_only_refuses_independent_unentered_task_before_any_publication(unclosed_case, monkeypatch):
    value = unclosed_case(unentered=True)
    before = api._custody_control_pins(value.case.plane, value.index)
    monkeypatch.setattr(LocalProcessExecutor, "__init__", _forbidden)
    monkeypatch.setattr(LocalScheduler, "__init__", _forbidden)
    monkeypatch.setattr(ExternalRunRecoveryStore, "record_terminal", _forbidden)
    with pytest.raises(PermissionError, match="eligible or unsettled"):
        _recover(value)
    assert api._custody_control_pins(value.case.plane, value.index) == before


@pytest.mark.parametrize("mode", ("unentered-resource", "remaining-candidate"))
def test_pure_closure_preserves_resource_preflight_and_remaining_attempts_as_pending(unclosed_case, mode):
    value = unclosed_case()
    rows = _attempts(value)
    second = owner.task_id(value.case.specification.root_ids[1], "prefix")
    row = next(row for row in rows if row.task_id == second)
    index = value.index
    if mode == "unentered-resource":
        row = replace(row, attempt_id=f"{index.run_id}.{second}.block-{row.ordinal:03d}",
            reason_code=TaskBlockReason.RESOURCE_COMPUTABILITY_UNAVAILABLE.value)
    else:
        binding = index.task(second)
        candidate = binding.attempts[0]
        later = replace(candidate, attempt_id=candidate.attempt_id.replace("attempt-001", "attempt-002"), ordinal=2,
            receipt_relative_path=candidate.receipt_relative_path + ".disclosed-second",
            event_relative_path=candidate.event_relative_path + ".disclosed-second")
        index = replace(index, tasks=tuple(replace(item, maximum_attempts=2, attempts=(candidate, later))
            if item.task_id == second else item for item in index.tasks))
    rows = tuple(row if item.task_id == second else item for item in rows)
    _, _, _, pending = settled_recovery_tasks(index, rows)
    assert second in pending


@pytest.mark.parametrize("defect", ("missing", "source", "materialization", "run"))
def test_custody_only_rechecks_unknown_contact_and_exact_original_ancestry_before_publication(unclosed_case, monkeypatch, defect):
    value = unclosed_case()
    task = owner.task_id(value.case.specification.root_ids[0], "prefix")
    read = ExternalNativeEffectContactStore.read
    def altered(self, run_id, task_id):
        contact = read(self, run_id, task_id)
        if task_id != task or contact is None:
            return contact
        if defect == "missing":
            return None
        changes = {"source": {"implementation_commit": "0" * 40},
            "materialization": {"input_materialization_ids": ("material.foreign",)},
            "run": {"run_id": "run.foreign"}}
        return replace(contact, **changes[defect])
    monkeypatch.setattr(ExternalNativeEffectContactStore, "read", altered)
    monkeypatch.setattr(ExternalRunRecoveryStore, "record_terminal", _forbidden)
    with pytest.raises(PermissionError, match="contact|source/stream"):
        _recover(value)
    assert ExternalRunRecoveryStore(value.case.plane).read_terminal(value.index) is None


def test_custody_only_missing_real_fixture_receipt_refuses_without_manufacturing_one(unclosed_case, monkeypatch):
    value = unclosed_case()
    entry = owner.entry_task_id(value.case.specification)
    candidate = value.index.task(entry).attempts[0]
    # Only this isolated disclosed software fixture is corrupted adversarially.
    for relative in (candidate.receipt_relative_path, candidate.receipt_relative_path + ".manifest.json"):
        value.case.plane.root.resolve(relative, for_write=False).unlink()
    before = api._custody_control_pins(value.case.plane, value.index)
    monkeypatch.setattr(ExternalRunRecoveryStore, "record_terminal", _forbidden)
    with pytest.raises(RunRecoveryError, match="receipt-free|receipt|custody"):
        _recover(value)
    assert api._custody_control_pins(value.case.plane, value.index) == before


def test_initial_custody_loader_refuses_inquiry_before_array_or_catalog_open(unclosed_case, monkeypatch):
    value = unclosed_case()
    (value.directory / "inquiry-admission.json").write_text("disclosed-invalid-initial-fixture")
    monkeypatch.setattr(api, "_external_inputs", _forbidden)
    import empirical_lawhood.infrastructure.sql as sql
    monkeypatch.setattr(sql, "create_catalog_engine", _forbidden)
    with pytest.raises(ValueError, match="inquiry"):
        _recover(value)


def test_initial_scope_boolean_refuses_before_filesystem():
    with pytest.raises(TypeError, match="exact boolean"):
        load_authored_wave(directory="not-opened", artifact_writer=None, require_initial_experiment=1)


def test_ordinary_run_source_guard_is_preserved(unclosed_case, monkeypatch):
    value = unclosed_case()
    observe = api.implementation_binding
    monkeypatch.setattr(api, "implementation_binding", lambda root, **_kwargs: replace(observe(root), observed_git_head="0" * 40))
    monkeypatch.setattr(LocalProcessExecutor, "__init__", _forbidden)
    with pytest.raises(ValueError, match="source or lock changed"):
        api.run_recursive_wave(directory=value.directory, project_root=ROOT, artifact_writer=value.case.plane)


def test_pure_closure_rejects_duplicate_attempts_and_foreign_run(unclosed_case):
    value = unclosed_case()
    rows = _attempts(value)
    with pytest.raises(RunRecoveryError, match="repeats"):
        settled_recovery_tasks(value.index, (*rows, rows[0]))
    with pytest.raises(RunRecoveryError, match="run or task"):
        settled_recovery_tasks(value.index, (replace(rows[0], run_id="run.foreign"), *rows[1:]))


@pytest.mark.parametrize("defect", ("foreign-success", "foreign-failure", "foreign-block", "ordinal-gap"))
def test_pure_closure_rejects_foreign_entered_candidates_before_success_classification(unclosed_case, defect):
    from empirical_lawhood.runtime.execution import TaskAttemptDisposition
    value = unclosed_case()
    rows = _attempts(value)
    row = rows[0]
    if defect == "ordinal-gap":
        changed = replace(row, ordinal=row.ordinal + 1)
    elif defect == "foreign-success":
        changed = replace(row, attempt_id="attempt.foreign.success", disposition=TaskAttemptDisposition.SUCCEEDED, reason_code=None)
    elif defect == "foreign-failure":
        changed = replace(row, attempt_id="attempt.foreign.failure", disposition=TaskAttemptDisposition.FAILED,
            reason_code="retry-exhaustion")
    else:
        changed = replace(row, attempt_id="attempt.foreign.block", disposition=TaskAttemptDisposition.BLOCKED,
            reason_code=TaskBlockReason.UNKNOWN_COMPLETION.value)
    with pytest.raises(RunRecoveryError, match="candidate|operational history|nonattempt"):
        settled_recovery_tasks(value.index, (changed, *rows[1:]))


def test_pure_closure_preserves_candidate_ordinal_after_known_operational_nonattempt(unclosed_case):
    from empirical_lawhood.runtime.execution import OperationalAttempt, TaskAttemptDisposition
    value = unclosed_case()
    rows = _attempts(value)
    task = owner.task_id(value.case.specification.root_ids[0], "prefix")
    original = next(row for row in rows if row.task_id == task)
    block = OperationalAttempt(f"{value.index.run_id}.{task}.block-001", value.index.run_id, task, 1,
        TaskAttemptDisposition.BLOCKED, TaskBlockReason.RESOURCE_LOCK_UNAVAILABLE.value, None, None)
    changed = tuple(replace(row, ordinal=2) if row.task_id == task else row for row in rows)
    completed, closed, _, pending = settled_recovery_tasks(value.index, (block, *changed))
    assert original.attempt_id == value.index.task(task).attempts[0].attempt_id
    assert task in closed and completed and not pending
