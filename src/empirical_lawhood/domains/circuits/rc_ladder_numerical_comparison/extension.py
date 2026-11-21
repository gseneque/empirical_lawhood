# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.circuits.rc_ladder_numerical_comparison.provider import ResistorCapacitorLadderNumericalProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.domains.circuits.rc_ladder.contracts import ResistorCapacitorLadderNativePanel, ResistorCapacitorLadderNumericalCheck
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind

from empirical_lawhood.domains.circuits.rc_ladder_numerical_comparison.contracts import ResistorCapacitorLadderEvaluationConfig

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="rc-ladder-response.numerical-check",
    kind=CapabilityKind.EVALUATOR,
    config_schema=ResistorCapacitorLadderEvaluationConfig.SCHEMA,
    config_schema_sha256=sha256(ResistorCapacitorLadderEvaluationConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=(ResistorCapacitorLadderNativePanel.SCHEMA,),
    output_schema_ids=tuple(
        sorted((ResistorCapacitorLadderNumericalCheck.SCHEMA, ScientificAdjudicationRecord.SCHEMA))
    ),
    permissions=tuple(
        sorted(
            (
                CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
                CapabilityPermission.READ_SEALED_OUTCOMES,
                CapabilityPermission.REVEAL_OUTCOMES,
            ),
            key=lambda permission: permission.value,
        )
    ),
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    maximum_outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
    resource_ceiling=ResourceBudget(1, 1024**3, 0, 120, 512 * 1024, 1024**2),
    implementation_sha256=sha256(
        b"rc-ladder-response:two-view-numerical-check-and-grid-charge-falsifier"
    ).hexdigest(),
    runtime_id="cpython-3.11-rc-ladder-response-numerical-check",
    conformance_check_ids=(
        "frozen-voltage-and-charge-limits",
        "one-model-unit-two-native-views",
        "synthetic-numerical-ceiling",
    ),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "numerical-check",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (ResistorCapacitorLadderEvaluationConfig,),
    None,
    namespace="rc-ladder-response",
)


# Executable roles.

from dataclasses import dataclass

from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort

from empirical_lawhood.domains.circuits.rc_ladder_numerical_comparison.contracts import ResistorCapacitorLadderEvaluationConfig


BINDING = executable(CAPABILITY, COMPONENTS, (ResistorCapacitorLadderEvaluationConfig,))


@dataclass(frozen=True, slots=True)
class ResistorCapacitorLadderNumericalFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> ResistorCapacitorLadderNumericalProvider:
        from empirical_lawhood.domains.circuits.rc_ladder_numerical_comparison.provider import ResistorCapacitorLadderNumericalProvider
        if len(records) != 1 or not isinstance(records[0], ResistorCapacitorLadderEvaluationConfig):
            raise ValueError("RC evaluator factory requires its exact issued config")
        if platform_ports:
            raise ValueError(
                "RC numerical evaluator cannot accept external platform ports"
            )
        return ResistorCapacitorLadderNumericalProvider(registry, records[0])


_EXECUTABLE_ID = "executable-contribution.rc-ladder-response.numerical-check"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (ResistorCapacitorLadderNumericalFactory(),)
_ISSUED_RECORD_TYPES = (ResistorCapacitorLadderEvaluationConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
