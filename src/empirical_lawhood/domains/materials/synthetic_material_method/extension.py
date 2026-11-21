# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.materials.synthetic_material_method.provider import SyntheticMaterialResponseMethodEvaluationProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.domains.materials.synthetic_material_method.contracts import SyntheticMaterialResponseMethodCheck, SyntheticMaterialResponseMethodEvaluationConfig, SyntheticMaterialResponseMethodPanel
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="synthetic-material-response-method.fixture-check",
    kind=CapabilityKind.EVALUATOR,
    config_schema=SyntheticMaterialResponseMethodEvaluationConfig.SCHEMA,
    config_schema_sha256=sha256(
        SyntheticMaterialResponseMethodEvaluationConfig.SCHEMA.encode()
    ).hexdigest(),
    input_schema_ids=(SyntheticMaterialResponseMethodPanel.SCHEMA,),
    output_schema_ids=tuple(
        sorted((SyntheticMaterialResponseMethodCheck.SCHEMA, ScientificAdjudicationRecord.SCHEMA))
    ),
    permissions=tuple(
        sorted(
            (
                CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
                CapabilityPermission.READ_SEALED_OUTCOMES,
                CapabilityPermission.REVEAL_OUTCOMES,
            ),
            key=lambda value: value.value,
        )
    ),
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    maximum_outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
    resource_ceiling=ResourceBudget(1, 1024**3, 0, 120, 1024**2, 1024**2),
    implementation_sha256=sha256(
        b"synthetic-material-response-method:strict-nine-fixture-adjudication"
    ).hexdigest(),
    runtime_id="cpython-3.11-numpy-synthetic-material-response-method-check",
    conformance_check_ids=tuple(
        sorted(
            (
                "nine-fixture-accept-reject-intersection",
                "normal-ward-sign-and-view-falsifiers",
                "method-fixture-only-nonpromotable",
            )
        )
    ),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "fixture-check",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (SyntheticMaterialResponseMethodEvaluationConfig,),
    None,
    namespace="synthetic-material-response-method",
)


# Executable roles.

from dataclasses import dataclass

from empirical_lawhood.domains.materials.synthetic_material_method.contracts import SyntheticMaterialResponseMethodEvaluationConfig
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort



BINDING = executable(CAPABILITY, COMPONENTS, (SyntheticMaterialResponseMethodEvaluationConfig,))


@dataclass(frozen=True, slots=True)
class SyntheticMaterialResponseMethodEvaluationFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> SyntheticMaterialResponseMethodEvaluationProvider:
        from empirical_lawhood.domains.materials.synthetic_material_method.provider import SyntheticMaterialResponseMethodEvaluationProvider
        if len(records) != 1 or not isinstance(
            records[0], SyntheticMaterialResponseMethodEvaluationConfig
        ):
            raise ValueError(
                'ambient pressure superconductor gauge covariant response method check needs its exact issued evaluation config'
            )
        if platform_ports:
            raise ValueError('ambient pressure superconductor gauge covariant response method check cannot accept a platform port')
        return SyntheticMaterialResponseMethodEvaluationProvider(registry, records[0])


_EXECUTABLE_ID = "executable-contribution.synthetic-material-response-method.finite-q-check"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (SyntheticMaterialResponseMethodEvaluationFactory(),)
_ISSUED_RECORD_TYPES = (SyntheticMaterialResponseMethodEvaluationConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
