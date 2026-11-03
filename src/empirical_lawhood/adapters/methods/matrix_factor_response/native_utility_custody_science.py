# SPDX-License-Identifier: MPL-2.0
"""Exact original E2 primary arithmetic with explicit missing whole roots."""
from fractions import Fraction

from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_custody_records import (
    NativeUtilityCustodyAssessment, NativeUtilityMissingRoot,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experimental_statistics import binomial_upper_tail
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from empirical_lawhood.runtime.recovery import (
    DevelopmentRunRecoveryIndex, DevelopmentRunRecoveryTerminalEvent, RecoveryTerminalDisposition,
)


def _closure(specification, *, run_id, execution_plan, recovery_index, operational_terminal):
    if (type(execution_plan) is not DevelopmentExecutionPlan
            or type(recovery_index) is not DevelopmentRunRecoveryIndex
            or type(operational_terminal) is not DevelopmentRunRecoveryTerminalEvent):
        raise TypeError("native E2 closed reduction requires exact original development plan/index/terminal editions")
    for record in (execution_plan, recovery_index, operational_terminal):
        record.__post_init__()
    index_pin = ObjectIdentity.from_record(recovery_index.recovery_index_id, recovery_index)
    plan_pin = ObjectIdentity.from_record(execution_plan.execution_plan_id, execution_plan)
    recovery_index.validate_plan(execution_plan)
    if (run_id != execution_plan.source_plan.object_id or recovery_index.run_id != run_id
            or recovery_index.execution_plan != plan_pin or operational_terminal.recovery_index != index_pin
            or operational_terminal.run_id != run_id
            or operational_terminal.operational_status not in ("BLOCKED", "FAILED")):
        raise ValueError("native E2 closed reduction substitutes its original run/plan/index/terminal")
    latest = {row.task_id: row for row in operational_terminal.attempts}
    tasks = {task.task_id: task for task in execution_plan.tasks}
    scope = {owner.entry_task_id(specification), owner.terminal_task_id(specification),
        *(owner.task_id(root, phase) for root in specification.root_ids for phase in r.PHASES)}
    if (set(latest) != scope or set(tasks) != scope
            or latest[owner.entry_task_id(specification)].disposition is not RecoveryTerminalDisposition.SUCCEEDED):
        raise ValueError("native E2 closed reduction lacks its settled original complete task/acquisition census")
    return latest, tasks, index_pin, plan_pin


def assess_closed_custody(specification, acquisition, *, run_id, execution_plan, recovery_index,
        operational_terminal, outcomes, missing_roots):
    """Reduce the original roster once; operational gaps cannot create scores.

    The API owns fresh artifact/contact/receipt authentication. This pure owner
    additionally checks every supplied gap against the passed original terminal
    and plan, including all non-success phases and successful outcome ancestry.
    """
    if type(specification) is not r.NativeUtilitySpecification or type(acquisition) is not r.NativeUtilityAcquisitionSeal:
        raise TypeError("native E2 closed reduction requires its unchanged original scientific inputs")
    specification.__post_init__()
    acquisition.__post_init__()
    latest, tasks, index_pin, plan_pin = _closure(specification, run_id=run_id, execution_plan=execution_plan,
        recovery_index=recovery_index, operational_terminal=operational_terminal)
    criterion = specification.criterion
    if criterion is None:
        raise ValueError("native E2 closed reduction lacks its original prespecified criterion")
    if (type(outcomes) is not tuple or any(type(row) is not r.NativeUtilityOutcome for row in outcomes)
            or type(missing_roots) is not tuple or any(type(row) is not NativeUtilityMissingRoot for row in missing_roots)):
        raise TypeError("native E2 closed reduction substitutes actual or missing whole-root record editions")
    rows = tuple(sorted(outcomes, key=lambda value: value.unit_id))
    missing = tuple(sorted(missing_roots, key=lambda value: value.unit_id))
    roster = tuple((value.root_id, value.unit_id, value.source) for value in (*rows, *missing))
    if (len(roster) != len(specification.root_ids)
            or tuple(sorted(value[0] for value in roster)) != specification.root_ids
            or len({value[1] for value in roster}) != len(roster)
            or tuple(sorted(roster, key=lambda value: value[0])) != acquisition.source_roster
            or any((value.specification, value.acquisition) != (specification.identity, acquisition.identity)
                for value in (*rows, *missing))):
        raise ValueError("native E2 closed reduction omits, duplicates or swaps an original whole root/source")
    for value in rows:
        value.__post_init__()
        if any(latest[owner.task_id(value.root_id, phase)].disposition is not RecoveryTerminalDisposition.SUCCEEDED
                for phase in r.PHASES):
            raise ValueError("native E2 actual outcome contradicts its unsuccessful original root terminal ancestry")
    for value in missing:
        value.__post_init__()
        root_tasks = {owner.task_id(value.root_id, phase) for phase in r.PHASES}
        expected = {key for key in root_tasks if latest[key].disposition is not RecoveryTerminalDisposition.SUCCEEDED}
        if (owner.task_id(value.root_id, "response-score") not in expected
                or {gap.task.object_id for gap in value.gaps} != expected):
            raise ValueError("native E2 missing root omits or substitutes an original non-success phase")
        for gap in value.gaps:
            key = gap.task.object_id
            if (gap.task != ObjectIdentity.from_record(key, tasks[key])
                    or gap.terminal_attempt != latest[key]
                    or gap.recovery_event.run_id != run_id or gap.recovery_event.recovery_index != index_pin):
                raise ValueError("native E2 missing gap changes its actual latest terminal row/task/run/index")
            candidate = next((row for row in recovery_index.task(key).attempts
                if row.attempt_id == gap.terminal_attempt.attempt_id), None)
            if candidate is not None and (gap.recovery_event.attempt_id != candidate.attempt_id
                    or gap.recovery_event.attempt_ordinal != candidate.ordinal):
                raise ValueError("native E2 missing gap substitutes its exact original executable candidate")
            if gap.native_contact is not None:
                contact = gap.native_contact
                contact.__post_init__()
                if (contact.execution_plan != plan_pin or contact.execution_task != gap.task
                        or contact.implementation_commit != execution_plan.implementation_commit
                        or contact.run_id != run_id or contact.attempt_id != gap.terminal_attempt.attempt_id):
                    raise ValueError("native E2 missing contact substitutes its original execution/source ancestry")
    if missing and latest[owner.terminal_task_id(specification)].disposition is RecoveryTerminalDisposition.SUCCEEDED:
        raise ValueError("native E2 missing reduction contradicts a successful original complete summary")
    successes = sum(value.success for value in rows)
    usable = sum(value.usable for value in rows)
    tail = binomial_upper_tail(len(roster), successes,
        Fraction(criterion.null_success_numerator, criterion.null_success_denominator))
    return NativeUtilityCustodyAssessment("custody-assessment." + specification.specification_id,
        specification.identity, acquisition.identity, run_id, plan_pin, index_pin,
        ObjectIdentity.from_record(operational_terminal.terminal_event_id, operational_terminal),
        operational_terminal.operational_status, rows, missing, len(roster), usable, successes,
        tail.numerator, tail.denominator,
        usable >= criterion.minimum_usable_units and tail <= Fraction(criterion.alpha_numerator, criterion.alpha_denominator),
        amended=r.amended_utility_inference(rows, tuple(row.unit_id for row in missing))
            if type(criterion) is r.NativeAmendedUtilityCriterion else None)
