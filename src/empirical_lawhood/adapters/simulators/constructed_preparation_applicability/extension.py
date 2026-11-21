# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.domains.matrix.constructed_preparation_applicability.config import ConstructedPreparationStage, ConstructedPreparationNativeConfig, ConstructedPreparationSource
from empirical_lawhood.domains.matrix.constructed_preparation_applicability.records import ConstructedPreparationSelection, ConstructedPreparationMeasuredRoot
from empirical_lawhood.domains.matrix.constructed_preparation_applicability.records import ConstructedPreparationLowerSeal
from empirical_lawhood.domains.matrix.constructed_preparation_applicability.phase_records import ConstructedPreparationParents
from empirical_lawhood.domains.matrix.constructed_preparation_applicability.records import ConstructedPreparationReport
from empirical_lawhood.domains.matrix.finite_response_law.original_f import OriginalFiniteResponseLaw
from empirical_lawhood.domains.matrix.constructed_preparation_applicability.phase_records import ConstructedPreparationPrefix, ConstructedPreparationPanel

OUTPUT_RECORDS = (
    ConstructedPreparationPrefix,
    ConstructedPreparationParents,
    ConstructedPreparationPanel,
)
CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="constructed-preparation-applicability.native",
    kind=CapabilityKind.SIMULATOR,
    config_schema=ConstructedPreparationNativeConfig.SCHEMA,
    config_schema_sha256=sha256(ConstructedPreparationNativeConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            {
                r.SCHEMA
                for r in (
                    ConstructedPreparationSource,
                    ConstructedPreparationStage,
                    ConstructedPreparationNativeConfig,
                    ConstructedPreparationSelection,
                    ConstructedPreparationLowerSeal,
                    ConstructedPreparationMeasuredRoot,
                    ConstructedPreparationReport,
                    OriginalFiniteResponseLaw,
                    ConstructedPreparationPrefix,
                    ConstructedPreparationPanel,
                    ConstructedPreparationParents,
                )
            }
        )
    ),
    output_schema_ids=tuple(sorted(r.SCHEMA for r in OUTPUT_RECORDS)),
    permissions=tuple(
        sorted(
            (
                CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
                CapabilityPermission.READ_SEALED_OUTCOMES,
                CapabilityPermission.READ_FROZEN_MODELS,
            )
        )
    ),
    maximum_evidence_ceiling=EvidenceCeiling.RESPONSE,
    maximum_outcome_access=OutcomeAccess.EVALUATION_SEALED,
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 3600, 4 * 1024**3, 128 * 1024**2),
    implementation_sha256=sha256(
        b"constructed-preparation-applicability.native:prescribed-mean-fresh-native-preparations-qualified-boundary-unchanged-F"
    ).hexdigest(),
    runtime_id="cpython-constructed-preparation-applicability",
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "native",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (ConstructedPreparationNativeConfig,),
    None,
    namespace="constructed-preparation-applicability",
)


# Executable roles.

from typing import Any


from dataclasses import dataclass, replace
from empirical_lawhood.execution.closed_provider_ports import closed_ports, input_payloads
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.domains.matrix.constructed_preparation_applicability.config import ConstructedPreparationNativeConfig


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (ConstructedPreparationNativeConfig,)),
    required_platform_port_keys=tuple(
        sorted(("bp-native-inputs", "bp-native-custody", "bp-native-limits"))
    ),
)


@dataclass(frozen=True, slots=True)
class Factory:
    binding = BINDING

    def build_provider(self, *, registry: Any, records: Any, platform_ports: Any) -> Any:
        from empirical_lawhood.adapters.simulators.constructed_preparation_applicability.provider import ConstructedPreparationNativeRunner, ConstructedPreparationNativeProvider
        config, ports = closed_ports(
            self.binding, records, ConstructedPreparationNativeConfig, platform_ports
        )
        runner = ConstructedPreparationNativeRunner(
            config, ports["bp-native-custody"], ports["bp-native-limits"]
        )
        return ConstructedPreparationNativeProvider(
            registry, runner, input_payloads(ports["bp-native-inputs"])
        )


_EXECUTABLE_ID = "executable-contribution.constructed-preparation-applicability.native"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (Factory(),)
_ISSUED_RECORD_TYPES = (ConstructedPreparationNativeConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION', 'OUTPUT_RECORDS']
