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
from empirical_lawhood.domains.matrix.preparation_applicability.config import PreparationApplicabilityStage, PreparationApplicabilityNativeConfig, PreparationApplicabilitySource
from empirical_lawhood.domains.matrix.preparation_applicability.records import PreparationApplicabilitySelection, PreparationApplicabilityMeasuredRoot
from empirical_lawhood.domains.matrix.preparation_applicability.seals import PreparationApplicabilityLowerSeal
from empirical_lawhood.domains.matrix.preparation_applicability.seals import PreparationApplicabilityParents
from empirical_lawhood.domains.matrix.preparation_applicability.readout import PreparationApplicabilityScreenReport
from empirical_lawhood.domains.matrix.finite_response_law.original_f import OriginalFiniteResponseLaw
from empirical_lawhood.domains.matrix.preparation_applicability.phase_records import PreparationApplicabilityPrefix, PreparationApplicabilityPanel

OUTPUT_RECORDS = (
    PreparationApplicabilityPrefix,
    PreparationApplicabilityParents,
    PreparationApplicabilityPanel,
)
CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="preparation-applicability.native",
    kind=CapabilityKind.SIMULATOR,
    config_schema=PreparationApplicabilityNativeConfig.SCHEMA,
    config_schema_sha256=sha256(PreparationApplicabilityNativeConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            {
                r.SCHEMA
                for r in (
                    PreparationApplicabilitySource,
                    PreparationApplicabilityStage,
                    PreparationApplicabilityNativeConfig,
                    PreparationApplicabilitySelection,
                    PreparationApplicabilityLowerSeal,
                    PreparationApplicabilityMeasuredRoot,
                    PreparationApplicabilityScreenReport,
                    OriginalFiniteResponseLaw,
                    PreparationApplicabilityPrefix,
                    PreparationApplicabilityPanel,
                    PreparationApplicabilityParents,
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
        b"preparation-applicability.native:prescribed-mean-fresh-native-preparations-qualified-boundary-unchanged-F"
    ).hexdigest(),
    runtime_id="cpython-preparation-applicability",
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "native",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (PreparationApplicabilityNativeConfig,),
    None,
    namespace="preparation-applicability",
)


# Executable roles.

from typing import Any


from dataclasses import dataclass, replace
from empirical_lawhood.execution.closed_provider_ports import closed_ports, input_payloads
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.domains.matrix.preparation_applicability.config import PreparationApplicabilityNativeConfig


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (PreparationApplicabilityNativeConfig,)),
    required_platform_port_keys=tuple(
        sorted(("pa-native-inputs", "pa-native-custody", "pa-native-limits"))
    ),
)


@dataclass(frozen=True, slots=True)
class Factory:
    binding = BINDING

    def build_provider(self, *, registry: Any, records: Any, platform_ports: Any) -> Any:
        from empirical_lawhood.adapters.simulators.preparation_applicability.provider import PreparationApplicabilityNativeRunner, PreparationApplicabilityNativeProvider
        config, ports = closed_ports(
            self.binding, records, PreparationApplicabilityNativeConfig, platform_ports
        )
        runner = PreparationApplicabilityNativeRunner(
            config, ports["pa-native-custody"], ports["pa-native-limits"]
        )
        return PreparationApplicabilityNativeProvider(
            registry, runner, input_payloads(ports["pa-native-inputs"])
        )


_EXECUTABLE_ID = "executable-contribution.preparation-applicability.native"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (Factory(),)
_ISSUED_RECORD_TYPES = (PreparationApplicabilityNativeConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION', 'OUTPUT_RECORDS']
