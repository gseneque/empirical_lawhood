# SPDX-License-Identifier: MPL-2.0
"""Join authenticated failure records to their original authored operations.

This is an application projection, not another journal, validator, retry policy
or source of scientific evidence. Callers supply the records from their active
custody read. No artifact is opened and no scientific calculation is performed.
"""

from __future__ import annotations

from empirical_lawhood.api.diagnostics import OperationDiagnostic
from empirical_lawhood.execution.execution import OperationalFailureClass
from empirical_lawhood.execution.recovery import ProtocolTaskRecoveryEvent, TaskRecoveryDisposition
from empirical_lawhood.science.identity.provenance import ObjectIdentity


def retained_failure_diagnostics(*, plan, index, events, authored_object=None, draft=None):
    """Explain every retained unsuccessful attempt without inferring a cause.

An execution-only read can identify the original draft and task without opening
scientific input bodies. A full read additionally supplies configuration and
installed implementation locations. A location is never substituted for the
original implementation digest. Historical events lacking a causal diagnostic
remain explicit. UNKNOWN native completion never acquires replay permission.
"""
    failures = tuple(event for event in events.values()
        if isinstance(event, ProtocolTaskRecoveryEvent)
        and event.disposition is not TaskRecoveryDisposition.SUCCEEDED)
    if not failures:
        return ()
    tasks = {task.task_id: task for task in plan.tasks}
    if len(tasks) != len(plan.tasks):
        raise ValueError("diagnostic projection requires a unique original task census")
    trace = {}
    if draft is not None:
        from empirical_lawhood.api.investigation_trace import authored_operation_trace
        nodes = tuple(sorted({event.task_id for event in failures}))
        trace = {row["operation_id"]: row for row in authored_operation_trace(draft, operation_ids=nodes)}
        authored_object = authored_object or ObjectIdentity.from_record(draft.draft_id, draft)
    origin = authored_object or plan.source_plan
    if type(origin) is not ObjectIdentity:
        raise TypeError("retained diagnostic origin requires an exact scientific identity")
    result = []
    seen = set()
    for event in sorted(failures, key=lambda row: (row.task_id, row.attempt_ordinal or 0, row.event_id)):
        if event.event_id in seen:
            raise ValueError("diagnostic projection repeats a retained failure event")
        seen.add(event.event_id)
        task = tasks.get(event.task_id)
        if task is None or event.run_id != index.run_id:
            raise ValueError("diagnostic event is outside its original task census")
        event_owner = getattr(index, "event_owner", lambda _task: index)(event.task_id)
        if event.recovery_index != ObjectIdentity.from_record(event_owner.recovery_index_id, event_owner):
            raise ValueError("diagnostic event changes its original recovery owner")
        binding = event_owner.task(event.task_id)
        if event.attempt_id is None:
            location = binding.nonattempt_event_relative_path
        else:
            candidates = tuple(row for row in binding.attempts if row.attempt_id == event.attempt_id)
            if len(candidates) != 1 or candidates[0].ordinal != event.attempt_ordinal:
                raise ValueError("diagnostic event changes its original attempt ancestry")
            location = candidates[0].event_relative_path
        failure = getattr(event, "failure", None)
        actual = event.disposition.value + ": " + ", ".join(event.reason_codes)
        if failure is not None:
            actual += "; " + (failure.sanitized_exception_type or "exception type not retained")
            actual += "; " + (failure.sanitized_message or "operand values not retained")
        else:
            actual += "; causal details were not retained by this original event"
        implementation = (task.capability.capability_key + "@" + task.capability.capability_version
            + "#" + task.capability_implementation_sha256)
        diagnostic = OperationDiagnostic(
            authored_object=origin.object_id, operation=task.task_id,
            owner="execution", contract=event.reason_codes[0],
            expected="The selected task completes under its frozen input, output and resource contracts.",
            actual=actual, implementation=implementation, evidence=location, remediation="platform")
        # A scheduler classification identifies the failed boundary, not a
        # proven bug in the selected scientific implementation. Keep both facts.
        selected = trace.get(task.task_id)
        if selected is not None:
            expected = selected["implementation"]
            if (expected["capability_key"], expected["capability_version"], expected["implementation_sha256"]) != (
                    task.capability.capability_key, task.capability.capability_version,
                    task.capability_implementation_sha256):
                raise ValueError("diagnostic joins a substituted authored implementation")
        unknown = "unknown-completion" in event.reason_codes
        result.append({**diagnostic.to_mapping(),
            "authored_identity": origin.to_document(),
            "authored_trace": selected,
            "attempt_id": event.attempt_id, "attempt_ordinal": event.attempt_ordinal,
            "retained_event": ObjectIdentity.from_record(event.event_id, event).to_document(),
            "failure_class": None if failure is None else failure.failure_class.value,
            "declared_resources": task.capability.requested_resources.to_document(),
            "required_output_schemas": task.capability.required_output_schema_ids,
            "retry_policy": ("READ_ONLY_RECONCILIATION" if unknown else
                "OWNING_RECOVERY_CONTRACT_REQUIRED"),
            "automatic_replay_authorized": False,
            "recorded_failure_retryable": None if failure is None else failure.retryable,
            "scientific_evidence": False,
            "cause_status": ("NATIVE_COMPLETION_UNCERTAIN" if unknown else
                "RETAINED_CLASSIFICATION_ONLY"),
            "remediation_detail": ("Reconcile original native contact and publication; do not replay." if unknown else
                "Inspect the frozen resource selection and current capacity." if failure is not None
                    and failure.failure_class is OperationalFailureClass.RESOURCE_REFUSAL else
                "Use the retained classification and selected implementation; no operand-level cause is inferred."),
        })
    return tuple(result)
