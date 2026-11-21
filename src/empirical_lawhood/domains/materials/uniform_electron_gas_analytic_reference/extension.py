# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.materials.uniform_electron_gas_analytic_reference.provider import UniformElectronGasAnalyticEvaluationProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.domains.materials.electron_gas.analytic_contracts import UniformElectronGasAnalyticCheck, UniformElectronGasAnalyticEvaluationConfig, UniformElectronGasAnalyticPanel
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="uniform-electron-gas-analytic-reference.finite-q-check",
    kind=CapabilityKind.EVALUATOR,
    config_schema=UniformElectronGasAnalyticEvaluationConfig.SCHEMA,
    config_schema_sha256=sha256(
        UniformElectronGasAnalyticEvaluationConfig.SCHEMA.encode()
    ).hexdigest(),
    input_schema_ids=(UniformElectronGasAnalyticPanel.SCHEMA,),
    output_schema_ids=tuple(
        sorted((UniformElectronGasAnalyticCheck.SCHEMA, ScientificAdjudicationRecord.SCHEMA))
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
        b"uniform-electron-gas-analytic-reference:realized-action-finite-q-slab-falsifier"
    ).hexdigest(),
    runtime_id="cpython-3.11-scipy-1.17.1-uniform-electron-gas-analytic-check",
    conformance_check_ids=(
        "finite-q-intercept-and-slab-falsifier",
        "realized-si-action-and-receiver-clock",
        "synthetic-reference-nonpromotable",
    ),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "finite-q-check",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (UniformElectronGasAnalyticEvaluationConfig,),
    None,
    namespace="uniform-electron-gas-analytic-reference",
)


# Executable roles.

from dataclasses import dataclass

from empirical_lawhood.domains.materials.electron_gas.analytic_contracts import UniformElectronGasAnalyticEvaluationConfig
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort



BINDING = executable(CAPABILITY, COMPONENTS, (UniformElectronGasAnalyticEvaluationConfig,))


@dataclass(frozen=True, slots=True)
class UniformElectronGasAnalyticEvaluationFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> UniformElectronGasAnalyticEvaluationProvider:
        from empirical_lawhood.domains.materials.uniform_electron_gas_analytic_reference.provider import UniformElectronGasAnalyticEvaluationProvider
        if len(records) != 1 or not isinstance(
            records[0], UniformElectronGasAnalyticEvaluationConfig
        ):
            raise ValueError(
                "uniform electron gas analytic check needs its exact issued evaluation config"
            )
        if platform_ports:
            raise ValueError("uniform electron gas analytic check cannot accept a platform port")
        return UniformElectronGasAnalyticEvaluationProvider(registry, records[0])


_EXECUTABLE_ID = "executable-contribution.uniform-electron-gas-analytic-reference.finite-q-check"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (UniformElectronGasAnalyticEvaluationFactory(),)
_ISSUED_RECORD_TYPES = (UniformElectronGasAnalyticEvaluationConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
