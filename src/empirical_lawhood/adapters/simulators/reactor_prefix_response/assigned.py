"""Native acquisition, external-format translation and custody integration."""


from empirical_lawhood.domains.reactor.reactor_prefix_response.native_assigned import (
    ReactorPrefixAssignedUnit as _science_ReactorPrefixAssignedUnit,
)

class AssignedPrefixBridge:
    """Construct only the installed native bridge, with a typed actual seed."""

    @staticmethod
    def create(*, unit: _science_ReactorPrefixAssignedUnit, **kwargs):
        from empirical_lawhood.adapters.simulators.reactor_prefix_response.bridge import ReactorBridge

        bridge = ReactorBridge(scenario_id=unit.public_scenario, **kwargs)
        bridge._scenario = {**bridge._scenario, "seed": unit.noise_seed}
        return bridge
