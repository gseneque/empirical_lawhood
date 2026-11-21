# SPDX-License-Identifier: MPL-2.0
"""Conservative hosted capacity derived from the shared frozen execution plan."""

from empirical_lawhood.science.identity.authority import ResourceBudget


REMOTE_CONTROLLER_RESERVE_BYTES = 512 * 1024**2


class RemotePlacementUnsupported(ValueError):
    """An explicit capability reason, never permission to change the science."""

    def __init__(self, reason_code: str, detail: str):
        self.reason_code = reason_code
        super().__init__(reason_code + ': ' + detail)


def size_runpod_resources(plan, *, payload_bytes: int, resource_spec=None,
                         cpu_cores=None, memory_bytes=None) -> ResourceBudget:
    """Size the current single-GPU host without changing task requirements.

    An envelope bounds concurrent reservations when supplied. Otherwise the
    complete task census is a conservative upper bound on ready tasks. The
    local scheduler still serializes reservations of the sole GPU. Source and
    output allowances include every selected task and every retained attempt.
    Host CPU/RAM overrides must contain the derived reservation; frozen task
    settings and per-task numerical thread counts are not rewritten.
    """
    from empirical_lawhood.execution.local.execution import selected_execution_resource_budgets
    from empirical_lawhood.execution.plans import ProtocolExecutionPlan

    if not isinstance(plan, ProtocolExecutionPlan):
        raise TypeError('hosted sizing requires a complete typed execution plan')
    plan.__post_init__()
    if type(payload_bytes) is not int or payload_bytes < 1:
        raise ValueError('hosted sizing requires the observed nonempty payload size')
    expected_envelope = getattr(plan, 'execution_resource_envelope_spec', None)
    if expected_envelope is not None:
        if resource_spec is None:
            raise RemotePlacementUnsupported('HOSTED_RESOURCE_ENVELOPE_REQUIRED',
                'supply the exact resource envelope already bound by this plan')
        from empirical_lawhood.science.identity.provenance import ObjectIdentity
        from empirical_lawhood.execution.execution_envelope import ExecutionResourceEnvelopeSpec
        if (type(resource_spec) is not ExecutionResourceEnvelopeSpec
                or ObjectIdentity.from_record(resource_spec.envelope_spec_id, resource_spec) != expected_envelope):
            raise RemotePlacementUnsupported('HOSTED_RESOURCE_ENVELOPE_MISMATCH',
                'selected resource envelope differs from the plan commitment')
    budgets = selected_execution_resource_budgets(plan, resource_spec)
    for task, budget in zip(plan.tasks, budgets, strict=True):
        values = (budget.cpu_cores, budget.memory_bytes, budget.gpu_devices,
                  budget.source_scan_bytes, budget.output_bytes)
        if any(type(value) is not int for value in values):
            raise RemotePlacementUnsupported('HOSTED_FINITE_RESOURCES_REQUIRED',
                task.task_id + ' needs exact CPU, memory, GPU, source and output allowances')
        if (budget.cpu_cores < 1 or budget.memory_bytes < 1 or budget.gpu_devices < 0
                or budget.source_scan_bytes < 0 or budget.output_bytes < 0):
            raise RemotePlacementUnsupported('HOSTED_INVALID_RESOURCE_REQUIREMENT', task.task_id)
    gpu_count = max(budget.gpu_devices for budget in budgets)
    if gpu_count != 1:
        raise RemotePlacementUnsupported('HOSTED_SINGLE_GPU_CAPABILITY_REQUIRED',
            f'current Runpod route requires one declared GPU per GPU task; observed maximum {gpu_count}')
    parallel = (len(budgets) if resource_spec is None
                else min(len(budgets), resource_spec.maximum_parallel_tasks))
    required_cpu = sum(sorted((budget.cpu_cores for budget in budgets), reverse=True)[:parallel])
    task_memory = sum(sorted((budget.memory_bytes for budget in budgets), reverse=True)[:parallel])
    if resource_spec is not None:
        task_memory = min(task_memory, resource_spec.aggregate_memory_ceiling_bytes)
    required_memory = task_memory + REMOTE_CONTROLLER_RESERVE_BYTES
    for name, selected, required in (('cpu_cores', cpu_cores, required_cpu),
                                     ('memory_bytes', memory_bytes, required_memory)):
        if selected is not None and (type(selected) is not int or selected < required):
            raise RemotePlacementUnsupported('HOSTED_OVERRIDE_BELOW_REQUIREMENT',
                f'{name}: requested {selected!r}, required at least {required}')
    return ResourceBudget(
        cpu_cores=required_cpu if cpu_cores is None else cpu_cores,
        memory_bytes=required_memory if memory_bytes is None else memory_bytes,
        gpu_devices=gpu_count,
        wall_time_seconds=None,
        source_scan_bytes=max(payload_bytes, sum(budget.source_scan_bytes for budget in budgets)),
        output_bytes=max(1, sum(budget.output_bytes * task.maximum_attempts
                               for task, budget in zip(plan.tasks, budgets, strict=True))),
    )
