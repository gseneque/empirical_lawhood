# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind

from empirical_lawhood.domains.circuits.rc_ladder.contracts import ResistorCapacitorLadderNativePanel, ResistorCapacitorLadderStudyConfig

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="rc-ladder-response.native-view",
    kind=CapabilityKind.SIMULATOR,
    config_schema=ResistorCapacitorLadderStudyConfig.SCHEMA,
    config_schema_sha256=sha256(ResistorCapacitorLadderStudyConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=(ResistorCapacitorLadderStudyConfig.SCHEMA,),
    output_schema_ids=(ResistorCapacitorLadderNativePanel.SCHEMA,),
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    maximum_outcome_access=OutcomeAccess.EVALUATION_SEALED,
    resource_ceiling=ResourceBudget(1, 1024**3, 0, 120, 128 * 1024, 1024**2),
    implementation_sha256=sha256(
        b"rc-ladder-response:source-impedance-piecewise-matrix-and-backward-euler"
    ).hexdigest(),
    runtime_id="cpython-3.11-numpy-2.4.6-scipy-1.17.1-rc-ladder-response",
    conformance_check_ids=(
        "frozen-native-model-and-action",
        "one-model-two-nested-views",
        "output-grid-charge-balance",
    ),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "native-view",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (ResistorCapacitorLadderStudyConfig,),
    None,
    namespace="rc-ladder-response",
)


# Executable roles.

from dataclasses import dataclass

from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.providers import CampaignRuntimeProvider

from empirical_lawhood.domains.circuits.rc_ladder.contracts import ResistorCapacitorLadderStudyConfig

BINDING = executable(CAPABILITY, COMPONENTS, (ResistorCapacitorLadderStudyConfig,))


@dataclass(frozen=True, slots=True)
class ResistorCapacitorLadderNativeFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> CampaignRuntimeProvider:
        if len(records) != 1 or not isinstance(records[0], ResistorCapacitorLadderStudyConfig):
            raise ValueError("RC native factory requires its exact issued study")
        if platform_ports:
            raise ValueError("local RC model cannot accept an external platform port")
        from empirical_lawhood.adapters.simulators.rc_ladder_response.runtime_provider import ResistorCapacitorLadderNativeProvider
        return ResistorCapacitorLadderNativeProvider(registry, records[0])


_EXECUTABLE_ID = "executable-contribution.rc-ladder-response.native-view"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (ResistorCapacitorLadderNativeFactory(),)
_ISSUED_RECORD_TYPES = (ResistorCapacitorLadderStudyConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION', 'ResistorCapacitorLadderNativeFactory']
