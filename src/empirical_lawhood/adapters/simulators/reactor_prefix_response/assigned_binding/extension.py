# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0

# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind

from empirical_lawhood.domains.reactor.reactor_prefix_response.native_assigned import ReactorAssignedPrefixConfig, ReactorAssignedPrefixPanel
from empirical_lawhood.adapters.simulators.reactor_prefix_response.extension import CAPABILITY as PUBLIC_CAPABILITY
from empirical_lawhood.domains.reactor.reactor_prefix_response.native_panel import ReactorSourceBundle

CAPABILITY = replace(
    PUBLIC_CAPABILITY,
    capability_key="assigned-reactor-prefix-response",
    config_schema=ReactorAssignedPrefixConfig.SCHEMA,
    config_schema_sha256=sha256(
        ReactorAssignedPrefixConfig.SCHEMA.encode()
    ).hexdigest(),
    input_schema_ids=tuple(
        sorted((ReactorAssignedPrefixConfig.SCHEMA, ReactorSourceBundle.SCHEMA))
    ),
    output_schema_ids=(ReactorAssignedPrefixPanel.SCHEMA,),
    implementation_sha256=sha256(
        b"assigned-reactor-prefix:actual-native-seed-nested-paired-views"
    ).hexdigest(),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "assigned-reactor-prefix",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (ReactorAssignedPrefixConfig,),
    None,
    namespace="assigned-reactor-prefix-response",
)


# SPDX-License-Identifier: MPL-2.0

# Executable roles.

from dataclasses import dataclass, replace

from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.execution.providers import ExternalInputPayload

from empirical_lawhood.domains.reactor.reactor_prefix_response.native_assigned import ReactorAssignedPrefixConfig, ReactorAssignedPrefixPanel
from empirical_lawhood.adapters.simulators.reactor_prefix_response.provider import ReactorPrefixProvider, ReactorPrefixRunner


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (ReactorAssignedPrefixConfig,)),
    required_platform_port_keys=("tbs-reactor-source-input",),
)


class ReactorAssignedPrefixRunner(ReactorPrefixRunner):
    manifest = CAPABILITY
    panel_type = ReactorAssignedPrefixPanel


class ReactorAssignedPrefixProvider(ReactorPrefixProvider):
    manifest = CAPABILITY
    panel_type = ReactorAssignedPrefixPanel
    runner_type = ReactorAssignedPrefixRunner


@dataclass(frozen=True, slots=True)
class ReactorAssignedPrefixFactory:
    binding = BINDING

    def build_provider(self, *, registry, records, platform_ports):
        if (
            len(records) != 1
            or type(records[0]) is not ReactorAssignedPrefixConfig
            or tuple(p.port_key for p in platform_ports)
            != BINDING.required_platform_port_keys
            or not isinstance(platform_ports[0].port, ExternalInputPayload)
        ):
            raise ValueError("REACTOR_ASSIGNED_FACTORY_EXACT_INPUTS_REQUIRED")
        return ReactorAssignedPrefixProvider(
            registry, records[0], platform_ports[0].port
        )


_EXECUTABLE_ID = "executable-contribution.assigned-reactor-prefix-response"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (ReactorAssignedPrefixFactory(),)
_ISSUED_RECORD_TYPES = (ReactorAssignedPrefixConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION', 'ReactorAssignedPrefixProvider']
