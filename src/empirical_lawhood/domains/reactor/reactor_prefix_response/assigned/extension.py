# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0

# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.domains.reactor.reactor_prefix_response.native_assigned import ReactorAssignedPrefixPanel
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind

from empirical_lawhood.domains.reactor.reactor_prefix_response.extension import CAPABILITY as PUBLIC_CAPABILITY
from empirical_lawhood.domains.reactor.reactor_prefix_response.assigned.records import ReactorAssignedScienceDesign, ReactorAssignedScienceResult

INPUT_TYPES = (ReactorAssignedScienceDesign, ReactorAssignedPrefixPanel)
OUTPUT_TYPES = (ReactorAssignedScienceResult, ScientificAdjudicationRecord)
CAPABILITY = replace(
    PUBLIC_CAPABILITY,
    capability_key="assigned-reactor-finite-chain",
    config_schema=ReactorAssignedScienceDesign.SCHEMA,
    config_schema_sha256=sha256(
        ReactorAssignedScienceDesign.SCHEMA.encode()
    ).hexdigest(),
    input_schema_ids=tuple(sorted(t.SCHEMA for t in INPUT_TYPES)),
    output_schema_ids=tuple(sorted(t.SCHEMA for t in OUTPUT_TYPES)),
    implementation_sha256=sha256(
        b"assigned-finite-chain:five-unit-custody-existing-finite-owner"
    ).hexdigest(),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "assigned-finite-chain",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (ReactorAssignedScienceDesign,),
    None,
    namespace="assigned-reactor-prefix-response",
)


# SPDX-License-Identifier: MPL-2.0

# Executable roles.

from dataclasses import dataclass, replace

from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.domains.reactor.reactor_prefix_response.native_assigned import ReactorAssignedPrefixPanel

from empirical_lawhood.domains.reactor.reactor_prefix_response.provider import FiniteChainProvider, FiniteChainRunner

from empirical_lawhood.domains.reactor.reactor_prefix_response.assigned.records import ReactorAssignedNativeCustody, ReactorAssignedScienceDesign, ReactorAssignedScienceResult

BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (ReactorAssignedScienceDesign,)),
    required_platform_port_keys=(
        "candidate-payload-publisher",
        "candidate-payload-reader",
        "dependency-custody-reader",
    ),
)


class AssignedFiniteChainRunner(FiniteChainRunner):
    manifest = CAPABILITY
    input_types = INPUT_TYPES
    output_types = OUTPUT_TYPES
    panel_type = ReactorAssignedPrefixPanel
    result_type = ReactorAssignedScienceResult

    def native_custody(self, receipts):
        return ReactorAssignedNativeCustody(receipts, self.config.native)


class AssignedFiniteChainProvider(FiniteChainProvider):
    manifest = CAPABILITY
    output_types = OUTPUT_TYPES
    runner_type = AssignedFiniteChainRunner


@dataclass(frozen=True, slots=True)
class AssignedFiniteChainFactory:
    binding = BINDING

    def build_provider(self, *, registry, records, platform_ports):
        ports = {p.port_key: p.port for p in platform_ports}
        if (
            len(records) != 1
            or type(records[0]) is not ReactorAssignedScienceDesign
            or len(platform_ports) != 3
            or tuple(sorted(ports)) != BINDING.required_platform_port_keys
        ):
            raise ValueError("REACTOR_ASSIGNED_FINITE_CHAIN_INPUTS_REQUIRED")
        for key, method in (
            ("candidate-payload-publisher", "publish_candidate_payload"),
            ("candidate-payload-reader", "read_candidate_payload"),
            ("dependency-custody-reader", "read_dependency"),
        ):
            if not callable(getattr(ports[key], method, None)):
                raise TypeError("REACTOR_ASSIGNED_FINITE_CHAIN_PORT_PROTOCOL")
        return AssignedFiniteChainProvider(
            registry,
            records[0],
            *(ports[key] for key in BINDING.required_platform_port_keys),
        )


_EXECUTABLE_ID = "executable-contribution.assigned-reactor-finite-chain"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (AssignedFiniteChainFactory(),)
_ISSUED_RECORD_TYPES = (ReactorAssignedScienceDesign,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['AssignedFiniteChainProvider', 'BINDING', 'CAPABILITY', 'EXTENSION']
