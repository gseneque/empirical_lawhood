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

from empirical_lawhood.domains.materials.electron_gas.analytic_contracts import UniformElectronGasAnalyticPanel
from empirical_lawhood.domains.materials.electron_gas.native_quickstart import UniformElectronGasAnalyticReferenceConfig

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="uniform-electron-gas-analytic-reference.native-panel",
    kind=CapabilityKind.SIMULATOR,
    config_schema=UniformElectronGasAnalyticReferenceConfig.SCHEMA,
    config_schema_sha256=sha256(UniformElectronGasAnalyticReferenceConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=(UniformElectronGasAnalyticReferenceConfig.SCHEMA,),
    output_schema_ids=(UniformElectronGasAnalyticPanel.SCHEMA,),
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    maximum_outcome_access=OutcomeAccess.EVALUATION_SEALED,
    resource_ceiling=ResourceBudget(1, 1024**3, 0, 120, 128 * 1024, 1024**2),
    implementation_sha256=sha256(
        b"uniform-electron-gas-analytic-reference:one-synthetic-si-q-action-slab-panel"
    ).hexdigest(),
    runtime_id="cpython-3.11-scipy-1.17.1-uniform-electron-gas-analytic-reference",
    conformance_check_ids=(
        "one-synthetic-acquisition-twenty-nested-conditions",
        "requested-accepted-applied-realized-si-action",
        "static-transverse-current-and-slab-profile",
    ),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "analytic-panel",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (UniformElectronGasAnalyticReferenceConfig,),
    None,
    namespace="uniform-electron-gas-analytic-reference",
)


# Executable roles.

from dataclasses import dataclass

from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort


from empirical_lawhood.domains.materials.electron_gas.native_quickstart import UniformElectronGasAnalyticReferenceConfig
from empirical_lawhood.adapters.simulators.uniform_electron_gas_response.runtime_provider import UniformElectronGasAnalyticSourceProvider

BINDING = executable(CAPABILITY, COMPONENTS, (UniformElectronGasAnalyticReferenceConfig,))


@dataclass(frozen=True, slots=True)
class UniformElectronGasAnalyticSourceFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> UniformElectronGasAnalyticSourceProvider:
        if len(records) != 1 or not isinstance(records[0], UniformElectronGasAnalyticReferenceConfig):
            raise ValueError(
                "uniform electron gas analytic native factory requires its exact issued config"
            )
        if platform_ports:
            raise ValueError(
                "uniform electron gas analytic source cannot accept a physical platform port"
            )
        return UniformElectronGasAnalyticSourceProvider(registry, records[0])


_EXECUTABLE_ID = "executable-contribution.uniform-electron-gas-analytic-reference.native-panel"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (UniformElectronGasAnalyticSourceFactory(),)
_ISSUED_RECORD_TYPES = (UniformElectronGasAnalyticReferenceConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
