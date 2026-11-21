# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.adapters.simulators.reactor_regime_response.provider import RegimeNativeProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.domains.reactor.reactor_causal_response.campaign_records import EmpiricalStudySource
from empirical_lawhood.domains.reactor.reactor_regime_response.records import RegimeAssayPanel, RegimeCausalPreparation, RegimePredictionSeal, RegimePrivatePreparation
from empirical_lawhood.domains.reactor.reactor_regime_response.nomination_records import RegimeNominationPackage
from empirical_lawhood.domains.reactor.reactor_regime_response.calibration_pipeline import RegimeCalibrationPackage
from empirical_lawhood.domains.reactor.reactor_regime_response.qualification_pipeline import RegimeQualificationPackage
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.domains.reactor.reactor_regime_response.law_terminal import RegimeJointLawResult
from empirical_lawhood.domains.reactor.reactor_regime_response.control_prospective_plan import ReactorRegimeResponsePreparedProspectivePlanBundle
from empirical_lawhood.domains.reactor.reactor_regime_response.prospective_decision import CausalValidityRegimeAssignment
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind

from empirical_lawhood.domains.reactor.reactor_regime_response.native_config import ReactorRegimeNativeConfig
from empirical_lawhood.domains.reactor.reactor_regime_response.prospective_records import RegimeDNativeRoot

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="terminal-bench-science-regime.native-assay",
    kind=CapabilityKind.SIMULATOR,
    maximum_outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
    maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT,
    permissions=tuple(
        sorted((
            *FINITE_ACTION_MANIFEST.permissions,
            CapabilityPermission.READ_FROZEN_MODELS,
            CapabilityPermission.READ_SEALED_OUTCOMES,
        ))
    ),
    config_schema=ReactorRegimeNativeConfig.SCHEMA,
    config_schema_sha256=sha256(ReactorRegimeNativeConfig.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            (
                ReactorRegimeNativeConfig.SCHEMA,
                EmpiricalStudySource.SCHEMA,
                RegimeCausalPreparation.SCHEMA,
                RegimePrivatePreparation.SCHEMA,
                RegimePredictionSeal.SCHEMA,
                RegimeNominationPackage.SCHEMA,
                RegimeCalibrationPackage.SCHEMA,
                RegimeQualificationPackage.SCHEMA,
                RegimeJointLawResult.SCHEMA,
                CausalValidityRegimeAssignment.SCHEMA,
                ReactorRegimeResponsePreparedProspectivePlanBundle.SCHEMA,
            )
        )
    ),
    output_schema_ids=tuple(
        sorted(
            (
                RegimeCausalPreparation.SCHEMA,
                RegimePrivatePreparation.SCHEMA,
                RegimeAssayPanel.SCHEMA,
                RegimeDNativeRoot.SCHEMA,
            )
        )
    ),
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 7200, 2 * 1024**3, 256 * 1024**2),
    implementation_sha256=sha256(
        b"reactor-regime-native:sealed-panel-and-selected-prospective-preparation"
    ).hexdigest(),
    runtime_id="cpython-reactor-regime",
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "native-assay",
    ExtensionContributionKind.SOURCE,
    CAPABILITY,
    (ReactorRegimeNativeConfig,),
    None,
    namespace="reactor-regime-response",
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast

from empirical_lawhood.domains.reactor.reactor_causal_response.resource_contract import EmpiricalResourceGuard
from empirical_lawhood.domains.reactor.reactor_regime_response.prior import RegimePriorArtifact
from empirical_lawhood.methods.law_assessment import CandidatePayloadReader
from empirical_lawhood.domains.reactor.reactor_regime_response.continuation import RegimeCContinuation, RegimeRetainedInputsPort
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.providers import ExternalInputPayload

from empirical_lawhood.domains.reactor.reactor_regime_response.native_config import ReactorRegimeNativeConfig


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (ReactorRegimeNativeConfig,)),
    required_platform_port_keys=(
        "reactor-regime-native-control-custody",
        "reactor-regime-native-dependency-reader",
        "reactor-regime-native-law-reader",
        "reactor-regime-native-prior-artifacts",
        "reactor-regime-native-resource-guard",
        "reactor-regime-native-retained-inputs",
        "reactor-regime-native-source-input",
    ),
)


@dataclass(frozen=True, slots=True)
class RegimeNativeFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> RegimeNativeProvider:
        from empirical_lawhood.domains.reactor.reactor_causal_response.provider import DependencyCustodyReader
        from empirical_lawhood.adapters.simulators.reactor_regime_response.provider import RegimeNativeProvider, RegimeControlCustodyPort
        if len(records) != 1 or not isinstance(records[0], ReactorRegimeNativeConfig):
            raise ValueError("reactor native factory requires its exact config")
        ports = {port.port_key: port.port for port in platform_ports}
        if tuple(sorted(ports)) != self.binding.required_platform_port_keys or len(ports) != len(
            platform_ports
        ):
            raise ValueError("reactor native factory port roster differs")
        if not callable(
            getattr(ports["reactor-regime-native-dependency-reader"], "read_dependency", None)
        ) or not callable(getattr(ports["reactor-regime-native-resource-guard"], "task", None)):
            raise TypeError("reactor native factory lacks custody or task limits")
        if not isinstance(ports["reactor-regime-native-source-input"], ExternalInputPayload):
            raise TypeError("reactor native factory source input differs")
        control = ports["reactor-regime-native-control-custody"]
        law_reader = ports["reactor-regime-native-law-reader"]
        if (control is None) != (law_reader is None):
            raise TypeError("reactor native control custody/law reader must be paired")
        if control is not None and (
            not callable(getattr(control, "open_control_store", None))
            or not callable(getattr(control, "open_prepared_store", None))
            or not callable(getattr(control, "freeze_clock", None))
            or not isinstance(getattr(control, "authority", None), ObjectIdentity)
            or not isinstance(getattr(control, "resources", None), ObjectIdentity)
            or not isinstance(getattr(control, 'issued_study', None), ObjectIdentity)
            or not callable(getattr(law_reader, "read_candidate_payload", None))
        ):
            raise TypeError("reactor native finite controller ports differ")
        prior = ports["reactor-regime-native-prior-artifacts"]
        retained = ports["reactor-regime-native-retained-inputs"]
        if (not callable(getattr(retained, "create_source", None))
                or not hasattr(retained, "continuation")
                or retained.continuation is not None
                and not isinstance(retained.continuation, RegimeCContinuation)):
            raise TypeError("reactor native retained-input port lacks its declaration")
        if not isinstance(prior, tuple) or any(
            not isinstance(value, RegimePriorArtifact) for value in prior
        ):
            raise TypeError("reactor native factory prior-phase custody differs")
        return RegimeNativeProvider(
            registry,
            records[0],
            ports["reactor-regime-native-source-input"],
            cast(DependencyCustodyReader, ports["reactor-regime-native-dependency-reader"]),
            cast(EmpiricalResourceGuard, ports["reactor-regime-native-resource-guard"]),
            prior,
            cast(RegimeControlCustodyPort | None, control),
            cast(CandidatePayloadReader | None, law_reader),
            cast(RegimeRetainedInputsPort, retained),
        )


_EXECUTABLE_ID = "executable-contribution.terminal-bench-science-regime.simulators"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (RegimeNativeFactory(),)
_ISSUED_RECORD_TYPES = (ReactorRegimeNativeConfig,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
