"""Reservation arithmetic is distinct from elapsed time and observed CPU use."""

from decimal import Decimal

import pytest

from empirical_lawhood.execution.task_resources import progress_resource_envelope
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.capabilities import CapabilityConfigRef
from empirical_lawhood.execution.isolated_native_subwork import IsolatedInvocationMemory
from empirical_lawhood.execution.plans import BarrierKind, OutputTemplate, ProtocolStepTemplate, ProtocolTemplate, ScientificStage


def envelope(*, cores, concurrency, wall, ceiling):
    budget = ResourceBudget(cores, 1024, 0, wall, 0, 1024)
    config = CapabilityConfigRef("exposed.config", budget.SCHEMA, "0" * 64, "1" * 64, "exposed.input")
    steps = tuple(ProtocolStepTemplate(
        name, ScientificStage.TRANSFORM, "exposed.metadata", "1.0.0", config, (),
        (OutputTemplate("exposed.output", budget.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                        "application/json", ".json"),),
        (), OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        budget, (), BarrierKind.NONE, 1, ("exposed.obligation",),
    ) for name in ("exposed.a", "exposed.b"))
    return progress_resource_envelope(
        prefix="exposed.resources", design=budget,
        protocol=ProtocolTemplate("exposed.protocol", "1.0.0", steps, False, False, True),
        issued_extensions=ObjectIdentity("exposed.issued", "empirical-lawhood/runtime/issued-extension-set",
                                         "1.0.0", "2" * 64),
        summed_wall_time_ceiling_seconds=ceiling, native_preparations=(),
        progress_counter="exposed.completed", heartbeat_seconds=Decimal(1),
        maximum_concurrency=concurrency, maximum_memory_bytes=2048, terminal_failure_codes=(),
    )


@pytest.mark.parametrize(("cores", "concurrency"), [(1, 1), (4, 1), (4, 2)])
def test_wall_reservations_do_not_become_cpu_use_or_a_concurrent_deadline(cores, concurrency):
    result = envelope(cores=cores, concurrency=concurrency, wall=10, ceiling=20)
    assert result.maximum_parallel_tasks == concurrency
    assert all(cell.resource_budget.cpu_cores == cores for cell in result.task_cells)
    assert result.elapsed_time_has_no_control_effect
    with pytest.raises(ValueError, match="summed task wall-time reservations"):
        envelope(cores=cores, concurrency=concurrency, wall=10, ceiling=19)


def test_unlimited_reservation_keeps_its_original_unlimited_meaning():
    result = envelope(cores=4, concurrency=2, wall=None, ceiling=None)
    assert result.elapsed_time_has_no_control_effect
    with pytest.raises(ValueError, match="summed task wall-time reservations"):
        envelope(cores=4, concurrency=2, wall=None, ceiling=100)


def test_complete_backing_concurrent_copies_and_unknown_worker_memory_are_distinct():
    mib = 1024**2
    unknown = IsolatedInvocationMemory(12 * mib, concurrent_copies=3)
    assert unknown.known_bytes == 42 * mib  # Three 12 MiB backings and six 1 MiB frames.
    assert unknown.total_bytes is None
    measured = IsolatedInvocationMemory(12 * mib, concurrent_copies=3, worker_peak_bytes=5 * mib)
    assert measured.total_bytes == 57 * mib
    measured.require_known_capacity(57 * mib)
    with pytest.raises(ValueError, match="complete isolated invocation backing"):
        measured.require_known_capacity(57 * mib - 1)
    with pytest.raises(ValueError, match="complete isolated invocation backing"):
        unknown.require_known_capacity(42 * mib - 1)
