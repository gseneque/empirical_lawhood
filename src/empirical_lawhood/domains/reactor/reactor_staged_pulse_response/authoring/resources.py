"""Per-stage native resource assignments on the shared progress envelope."""

from decimal import Decimal as D
from empirical_lawhood.execution.task_resources import progress_resource_envelope
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.config import ClassicalStage
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.execution_envelope import ExecutionResourceEnvelopeSpec
from empirical_lawhood.execution.plans import ProtocolTemplate


def resource_envelope(
    stage: ClassicalStage, protocol: ProtocolTemplate, issued_extensions: ObjectIdentity
) -> ExecutionResourceEnvelopeSpec:
    prefixes = ("classical.prepare.", "classical.assay.", "classical.action.")
    native = tuple(
        (s.step_id, s.step_id.removeprefix(p), f"{s.step_id.removeprefix(p)}.initial-state")
        for s in protocol.steps
        for p in prefixes
        if s.step_id.startswith(p)
    )
    return progress_resource_envelope(
        prefix=stage.config_id,
        design=stage,
        protocol=protocol,
        issued_extensions=issued_extensions,
        # Historical cpu_seconds is the fixed one-core protocol reservation.
        summed_wall_time_ceiling_seconds=stage.cpu_seconds,
        native_preparations=native,
        progress_counter="reactor-completed-native-decisions",
        heartbeat_seconds=D(60),
        maximum_concurrency=4,
        maximum_memory_bytes=32 * 1024**3,
        terminal_failure_codes=(
            "NATIVE_NUMERICAL_FAILURE",
            "NATIVE_OBSERVER_FAILURE",
            "WORKER_PROGRESS_STALLED",
            "RESOURCE_COMPUTABILITY_UNAVAILABLE",
            "RETRY_BUDGET_EXHAUSTED",
        ),
    )
