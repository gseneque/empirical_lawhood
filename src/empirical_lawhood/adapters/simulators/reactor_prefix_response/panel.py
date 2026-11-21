"""Native acquisition, external-format translation and custody integration."""

from collections.abc import Callable
from decimal import Decimal
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import ReactorCommand

from empirical_lawhood.domains.reactor.reactor_prefix_response.native_panel import (
    ARMS as _science_ARMS,
    ReactorPrefixConfig as _science_ReactorPrefixConfig,
    ReactorPrefixEpisode as _science_ReactorPrefixEpisode,
    ReactorPrefixPanel as _science_ReactorPrefixPanel,
    ReactorSourceBundle as _science_ReactorSourceBundle,
    VIEWS as _science_VIEWS,
    native_task_id as _science_native_task_id,
)

def acquire_prefix_branch(
    config: _science_ReactorPrefixConfig,
    source: _science_ReactorSourceBundle,
    branch: tuple[str, str, str],
    progress: Callable[[int], None] | None = None,
) -> _science_ReactorPrefixPanel:
    """Native runner body, called only after execution closure and input authority."""
    import platform
    from importlib.metadata import version

    from empirical_lawhood.adapters.simulators.reactor_prefix_response.bridge import ReactorBridge, ReactorWorkerStopError

    if (
        version("numpy") != config.numpy_version
        or platform.python_version() != config.python_version
    ):
        raise ValueError(
            "reactor numerical runtime differs before native source execution"
        )
    scenario, view, arm = branch
    _science_native_task_id(*branch, config=config)
    dt, jacket = dict(_science_VIEWS)[view], dict(_science_ARMS)[arm]
    first = None
    deliveries = []
    failure = None
    completed = 0
    from empirical_lawhood.adapters.simulators.reactor_prefix_response.assigned import AssignedPrefixBridge
    from empirical_lawhood.domains.reactor.reactor_prefix_response.native_assigned import ReactorAssignedPrefixConfig, ReactorAssignedPrefixEpisode, ReactorAssignedPrefixPanel

    assigned = type(config) is ReactorAssignedPrefixConfig
    unit = (
        next(u for u in config.assignment.units if u.unit_id == scenario)
        if assigned
        else None
    )
    bridge_inputs = {
        "plant_bytes": source.plant_source.encode(),
        "params_bytes": source.plant_params.encode(),
        "public_scenarios_bytes": source.public_scenarios.encode(),
        "plant_dt_s": dt,
    }
    try:
        bridge = (
            AssignedPrefixBridge.create(unit=unit, **bridge_inputs)
            if assigned
            else ReactorBridge(scenario_id=scenario, **bridge_inputs)
        )
        with bridge:
            first = bridge.start()
            for index, value in enumerate((jacket, Decimal(316))):
                deliveries.append(
                    bridge.deliver(
                        ReactorCommand(
                            f"decision.{scenario}.{view}.{arm}.{index}",
                            Decimal(10 * index),
                            Decimal(0),
                            value,
                        )
                    )
                )
                completed += len(deliveries[-1].exposures)
                if progress is not None:
                    progress(completed)
    except ReactorWorkerStopError:
        raise
    except (ValueError, RuntimeError):
        # No retry, substitute branch, dropped unit or fabricated end state.
        failure = "REACTOR_NATIVE_PREFIX_FAILED"
    if assigned:
        episode = ReactorAssignedPrefixEpisode(
            scenario, view, arm, first, tuple(deliveries), failure, unit
        )
        return ReactorAssignedPrefixPanel(config, (episode,), branch)
    episode = _science_ReactorPrefixEpisode(
        scenario, view, arm, first, tuple(deliveries), failure
    )
    return _science_ReactorPrefixPanel(config, (episode,), branch)
