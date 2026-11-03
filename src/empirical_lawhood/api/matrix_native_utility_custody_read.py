# SPDX-License-Identifier: MPL-2.0
"""Fresh owner-authenticated scientific projection of closed, incomplete E2 custody."""
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_custody_records import (
    NativeUtilityCustodyGap, NativeUtilityMissingRoot,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_custody_science import assess_closed_custody
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_science import amended_primary_report
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.api.matrix_native_read_custody import _expected_contact
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.recovery import (
    DevelopmentRunRecoveryIndex, DevelopmentRunRecoveryTerminalEvent, RecoveryTerminalDisposition,
)


def _closed_context(*, artifact_writer, report, products, plan):
    """Reopen original control custody; a progress file never proves closure."""
    terminal = products["terminal"]
    if type(terminal) is not DevelopmentRunRecoveryTerminalEvent:
        raise PermissionError("native E2 incomplete scientific read requires its actual closed operational terminal")
    terminal.__post_init__()
    run_id = plan.source_plan.object_id
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run_id,
        wave_id="wave.development", authority_identities=())
    recovery = ExternalRunRecoveryStore(artifact_writer)
    index_pin = ObjectIdentity.from_record(index.recovery_index_id, index)
    if (terminal.run_id != run_id or terminal.recovery_index != index_pin
            or terminal.operational_status not in ("BLOCKED", "FAILED")
            or report.get("status") != terminal.operational_status or report.get("run_id") != run_id
            or report.get("task_count") != len(plan.tasks)
            or report.get("execution_plan_sha256") != plan.fingerprint()
            or recovery.read_index(index.index_relative_path, expected_schema=index.SCHEMA) != index
            or recovery.read_terminal(index) != terminal):
        raise PermissionError("native E2 closed scientific read changes its actual run/plan/index/terminal")
    latest = {}
    for row in terminal.attempts:
        latest[row.task_id] = row
    tasks = {task.task_id: task for task in plan.tasks}
    dispositions = {row["task_id"]: row for row in products["dispositions"]}
    expected = set(tasks)
    if (set(latest) != expected or set(dispositions) != expected
            or len(dispositions) != len(products["dispositions"])
            or any(dispositions[key] != {"task_id": key, "operational_status": row.disposition.value,
                "reason_code": row.reason_code} for key, row in latest.items())
            or set(products["receipts"]) != {key for key, row in latest.items()
                if row.disposition is RecoveryTerminalDisposition.SUCCEEDED}):
        raise PermissionError("native E2 incomplete scientific read lacks an exact settled whole-task census")
    contacts = ExternalNativeEffectContactStore(plane=artifact_writer,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    return index, recovery, terminal, latest, contacts


def _gap(*, task, summary, index, recovery, contacts, products, plan, receipts):
    """Preserve current contact/refusal/event separately, never manufacture a score."""
    if task.task_id in products["receipts"] or receipts.read(index.run_id, task.task_id, summary.attempt_id) is not None:
        raise PermissionError("native E2 missing task contradicts its original completion receipt")
    binding = index.task(task.task_id)
    candidate = next((value for value in binding.attempts if value.attempt_id == summary.attempt_id), None)
    event_path = binding.nonattempt_event_relative_path if candidate is None else candidate.event_relative_path
    event = recovery.read_event(index, event_path)
    if (event is None or products["recovery_events"].get(summary.attempt_id) != event
            or event.recovery_index != ObjectIdentity.from_record(index.recovery_index_id, index)
            or event.run_id != index.run_id or event.task_id != task.task_id
            or event.reason_codes != (summary.reason_code,)):
        raise PermissionError("native E2 missing task changes its original authenticated recovery event")
    native = task.capability.capability_key in (r.NAMESPACE + ".prefix", r.NAMESPACE + ".responses")
    contact = contacts.read(index.run_id, task.task_id)
    if contact is not None:
        if not native or candidate is None or contact != _expected_contact(task=task, plan=plan,
                run_id=index.run_id, attempt_id=candidate.attempt_id, products=products):
            raise PermissionError("native E2 missing contact changes its source/stream/materialization/attempt ancestry")
        disposition = ("UNKNOWN_PARENT_COMPLETION" if summary.reason_code == "unknown-completion"
            else "CONTACTED_PARENT_NON_SUCCESS")
    elif summary.reason_code == "unknown-completion":
        raise PermissionError("native E2 UNKNOWN task has lost its original durable native contact")
    elif summary.reason_code == "resource-computability-unavailable":
        disposition = "NO_CONTACT_RESOURCE_REFUSAL"
    elif summary.disposition is RecoveryTerminalDisposition.FAILED:
        disposition = "NO_CONTACT_OPERATIONAL_FAILURE"
    elif summary.reason_code in ("dependency-blocked", "dependency-failed", "dependency-not-succeeded"):
        disposition = "DEPENDENCY_BLOCKED"
    else:
        disposition = "NO_CONTACT_PRECONDITION_BLOCK"
    return NativeUtilityCustodyGap(ObjectIdentity.from_record(task.task_id, task), summary, event, contact, disposition)


def read_closed_partial_result(*, directory, artifact_writer, specification, instance, payloads,
        report, products, draft, plan):
    """Full read of actual outcomes and missingness under the original criterion.

    The public caller keeps compact/allow_partial reads deferred before this
    function. A closed operational terminal is mandatory even when every gap
    already has an event. This projection creates no new execution or authority.
    """
    from empirical_lawhood.api import matrix_native_utility_read as reader
    request = reader._request(specification, instance, payloads)
    configs, tasks = reader._graph(specification, request, draft, plan)
    index, recovery, terminal, latest, contacts = _closed_context(artifact_writer=artifact_writer,
        report=report, products=products, plan=plan)
    reader.authenticate_request(artifact_writer, request)
    source_index = ScheduledSourceIndex.from_shared(reservation=request.source_manifest.reservation,
        specification=request.source_manifest.native_specification, provenances=request.source_manifest.provenances)
    source_index.require_roster(request.sources, expected_root_ids=specification.root_ids)
    seal = reader._record(products, tasks, index.run_id, owner.entry_task_id(specification), r.NativeUtilityAcquisitionSeal)
    if seal != r.acquisition_seal(specification, request):
        raise PermissionError("native E2 closed read changes its actual pre-contact acquisition freeze")
    receipts = ExternalTaskReceiptStore(artifact_writer)
    actual, missing = [], []
    template_arrays = {}
    roster = {root: (unit, source) for root, unit, source in seal.source_roster}
    for root_id in specification.root_ids:
        score_task = owner.task_id(root_id, "response-score")
        root_tasks = tuple(owner.task_id(root_id, phase) for phase in r.PHASES)
        if latest[score_task].disposition is RecoveryTerminalDisposition.SUCCEEDED:
            if any(latest[key].disposition is not RecoveryTerminalDisposition.SUCCEEDED for key in root_tasks):
                raise PermissionError("native E2 actual score has an unsuccessful original causal root task")
            actual.append(reader._root(specification, request, seal, root_id, configs, products, tasks, index.run_id,
                source_index=source_index, artifact_writer=artifact_writer, plan=plan, template_arrays=template_arrays))
            continue
        gaps = tuple(_gap(task=tasks[key], summary=latest[key], index=index, recovery=recovery,
            contacts=contacts, products=products, plan=plan, receipts=receipts)
            for key in sorted(root_tasks) if latest[key].disposition is not RecoveryTerminalDisposition.SUCCEEDED)
        unit, source = roster[root_id]
        missing.append(NativeUtilityMissingRoot("missing." + r.NAMESPACE + "." + root_id,
            specification.identity, seal.identity, root_id, unit, source, gaps))
    if latest[owner.terminal_task_id(specification)].disposition is RecoveryTerminalDisposition.SUCCEEDED:
        raise PermissionError("native E2 incomplete read contradicts a successful original complete summary")
    assessment = assess_closed_custody(specification, seal, run_id=index.run_id, execution_plan=plan,
        recovery_index=index, operational_terminal=terminal, outcomes=tuple(actual), missing_roots=tuple(missing))
    # This also ensures that a read cannot turn a control publication edit into
    # fresh missingness or silently replace its original exact source/contact.
    if recovery.read_terminal(index) != terminal:
        raise PermissionError("native E2 closed terminal changed during scientific reading")
    for row in missing:
        for gap in row.gaps:
            if contacts.read(index.run_id, gap.task.object_id) != gap.native_contact:
                raise PermissionError("native E2 contact changed during closed scientific reading")
    return {"scientific_completion": "INCOMPLETE_NATIVE_UTILITY_ASSESSMENT_WITH_CLOSED_WHOLE_ROSTER_REDUCTION",
        "state": "CLOSED_CUSTODY_AWARE_NATIVE_UTILITY_RESULT_RETAINED", "scientific_status": assessment.scientific_status,
        "qualification": assessment.qualification, "sampling_warrant": assessment.sampling_warrant,
        "numerical_scope": assessment.numerical_scope, "operational_status": terminal.operational_status,
        "criterion": specification.criterion.to_document(), "conditional_criterion_met": assessment.conditional_criterion_met,
        "conditional_tail": {"numerator": assessment.tail_numerator, "denominator": assessment.tail_denominator},
        "amended_primary_tests": amended_primary_report(assessment.amended),
        "denominators": {"native-utility": {"assigned_units": assessment.assigned_units,
            "usable_units": assessment.usable_units, "successes": assessment.successes,
            "adverse_units": sum(value.usable and not value.success for value in assessment.outcomes),
            "unevaluable_units": sum(not value.usable for value in assessment.outcomes) + len(assessment.missing_roots),
            "missing_units": len(assessment.missing_roots)}},
        "source_request": seal.request.to_document(), "acquisition": seal.identity.to_document(),
        "assessment": assessment.to_document(), "new_native_contact_count": 0}
