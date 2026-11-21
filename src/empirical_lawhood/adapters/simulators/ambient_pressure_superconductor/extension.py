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

from empirical_lawhood.domains.materials.synthetic_material_method.contracts import SyntheticMaterialResponseMethodConfig, SyntheticMaterialResponseMethodPanel

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="synthetic-material-response-method.fixture-producer",
    kind=CapabilityKind.SIMULATOR,
    config_schema=SyntheticMaterialResponseMethodConfig.SCHEMA,
    config_schema_sha256=sha256(SyntheticMaterialResponseMethodConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=(SyntheticMaterialResponseMethodConfig.SCHEMA,),
    output_schema_ids=(SyntheticMaterialResponseMethodPanel.SCHEMA,),
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    maximum_outcome_access=OutcomeAccess.EVALUATION_SEALED,
    resource_ceiling=ResourceBudget(1, 1024**3, 0, 600, 128 * 1024, 1024**2),
    implementation_sha256=sha256(
        b"synthetic-material-response-method:one-synthetic-nine-fixture-gauge-covariant-suite"
    ).hexdigest(),
    runtime_id="cpython-3.11-numpy-synthetic-material-response-method",
    conformance_check_ids=tuple(
        sorted(
            (
                "one-synthetic-suite-nine-nested-fixtures",
                "requested-accepted-applied-lattice-probe",
                "signed-current-normal-ward-and-two-mesh-interval",
            )
        )
    ),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "fixture-producer",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (SyntheticMaterialResponseMethodConfig,),
    None,
    namespace="synthetic-material-response-method",
)


# Executable roles.

from dataclasses import dataclass

from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort


from empirical_lawhood.domains.materials.synthetic_material_method.contracts import SyntheticMaterialResponseMethodConfig
from empirical_lawhood.adapters.simulators.ambient_pressure_superconductor.synthetic_material_method_provider import SyntheticMaterialResponseMethodProvider

BINDING = executable(CAPABILITY, COMPONENTS, (SyntheticMaterialResponseMethodConfig,))


@dataclass(frozen=True, slots=True)
class SyntheticMaterialResponseMethodFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> SyntheticMaterialResponseMethodProvider:
        if len(records) != 1 or not isinstance(records[0], SyntheticMaterialResponseMethodConfig):
            raise ValueError(
                'ambient pressure superconductor gauge covariant response method native factory requires its exact issued config'
            )
        if platform_ports:
            raise ValueError(
                'ambient pressure superconductor gauge covariant response method source cannot accept a physical platform port'
            )
        return SyntheticMaterialResponseMethodProvider(registry, records[0])


_EXECUTABLE_ID = "executable-contribution.synthetic-material-response-method.native-panel"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (SyntheticMaterialResponseMethodFactory(),)
_ISSUED_RECORD_TYPES = (SyntheticMaterialResponseMethodConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
