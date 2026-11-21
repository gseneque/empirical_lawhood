# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.reactor.reactor_regime_response.provider import RegimeMethodProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.domains.reactor.reactor_regime_response.law_terminal import RegimeJointLawResult
from empirical_lawhood.domains.reactor.reactor_regime_response.control_prospective_plan import ReactorRegimeResponsePreparedProspectivePlanBundle
from empirical_lawhood.domains.reactor.reactor_regime_response.control_prospective_closeout import RegimeDRootSealResult
from empirical_lawhood.domains.reactor.reactor_regime_response.control_prospective_reveal import RegimeDRootRevealResult
from empirical_lawhood.domains.reactor.reactor_regime_response.control_prospective_cohort import ReactorRegimeResponseCohortProspective
from empirical_lawhood.domains.reactor.reactor_regime_response.prospective_records import RegimeDNativeRoot
from empirical_lawhood.domains.reactor.reactor_regime_response.prospective_decision import CausalValidityRegimeAssignment
from empirical_lawhood.domains.reactor.reactor_regime_response.discovery_records import RegimeDiscoveryTraining, RegimeDiscoveryDevelopment
from empirical_lawhood.domains.reactor.reactor_regime_response.discovery_diagnostics import RegimePhaseDiagnostics, RegimeDiscoveryConfirmation
from empirical_lawhood.domains.reactor.reactor_regime_response.preassay_readout import RegimePreassayReadout, RegimeOpportunityReadout
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind

from empirical_lawhood.domains.reactor.reactor_regime_response.config import ReactorRegimeResponseDesign
from empirical_lawhood.domains.reactor.reactor_regime_response.calibration_pipeline import RegimeCalibrationPackage
from empirical_lawhood.domains.reactor.reactor_regime_response.model_records import RegimeFitPackage
from empirical_lawhood.domains.reactor.reactor_regime_response.nomination_records import RegimeNominationPackage
from empirical_lawhood.domains.reactor.reactor_regime_response.qualification_pipeline import RegimeQualificationPackage
from empirical_lawhood.domains.reactor.reactor_regime_response.records import RegimeAssayPanel, RegimeCausalPreparation, RegimePredictionSeal, RegimePrivatePreparation

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="terminal-bench-science-regime.fit-and-seal",
    kind=CapabilityKind.EVALUATOR,
    maximum_evidence_ceiling=EvidenceCeiling.CONTROLLER_USE,
    maximum_outcome_access=OutcomeAccess.EVALUATOR_REVEAL,
    permissions=tuple(
        sorted(
            (
                CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
                CapabilityPermission.READ_SEALED_OUTCOMES,
                CapabilityPermission.REVEAL_OUTCOMES,
            )
        )
    ),
    config_schema=ReactorRegimeResponseDesign.SCHEMA,
    config_schema_sha256=sha256(ReactorRegimeResponseDesign.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            (
                ReactorRegimeResponseDesign.SCHEMA,
                RegimeCausalPreparation.SCHEMA,
                RegimePredictionSeal.SCHEMA,
                RegimeAssayPanel.SCHEMA,
                RegimeFitPackage.SCHEMA,
                RegimeDiscoveryTraining.SCHEMA,
                RegimeDiscoveryDevelopment.SCHEMA,
                RegimePhaseDiagnostics.SCHEMA,
                RegimeDiscoveryConfirmation.SCHEMA,
                RegimePreassayReadout.SCHEMA,
                RegimeNominationPackage.SCHEMA,
                RegimeCalibrationPackage.SCHEMA,
                RegimeQualificationPackage.SCHEMA,
                RegimeJointLawResult.SCHEMA,
                RegimePrivatePreparation.SCHEMA,
                CausalValidityRegimeAssignment.SCHEMA,
                RegimeDNativeRoot.SCHEMA,
                ReactorRegimeResponsePreparedProspectivePlanBundle.SCHEMA,
                RegimeDRootSealResult.SCHEMA,
                RegimeDRootRevealResult.SCHEMA,
                ReactorRegimeResponseCohortProspective.SCHEMA,
            )
        )
    ),
    output_schema_ids=tuple(sorted((
        RegimePredictionSeal.SCHEMA,
        RegimeFitPackage.SCHEMA,
        RegimeDiscoveryTraining.SCHEMA,
        RegimeDiscoveryDevelopment.SCHEMA,
        RegimePhaseDiagnostics.SCHEMA,
        RegimeDiscoveryConfirmation.SCHEMA,
        RegimePreassayReadout.SCHEMA,
        RegimeOpportunityReadout.SCHEMA,
        RegimeNominationPackage.SCHEMA,
        RegimeCalibrationPackage.SCHEMA,
        RegimeQualificationPackage.SCHEMA,
        RegimeJointLawResult.SCHEMA,
        CausalValidityRegimeAssignment.SCHEMA,
        ReactorRegimeResponsePreparedProspectivePlanBundle.SCHEMA,
        RegimeDRootSealResult.SCHEMA,
        RegimeDRootRevealResult.SCHEMA,
        ReactorRegimeResponseCohortProspective.SCHEMA,
        ScientificAdjudicationRecord.SCHEMA,
    ))),
    implementation_sha256=sha256(
        b"reactor-regime-method:fit-seals-nomination-calibration-sole-owner-qualification-adjudication"
    ).hexdigest(),
    runtime_id="cpython-reactor-regime",
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 7200, 8 * 1024**3, 256 * 1024**2),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "fit-and-seal",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (ReactorRegimeResponseDesign,),
    None,
    namespace="reactor-regime-response",
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast

from empirical_lawhood.methods.law_assessment import CandidatePayloadPublisher, CandidatePayloadReader
from empirical_lawhood.domains.reactor.reactor_causal_response.resource_contract import EmpiricalResourceGuard
from empirical_lawhood.domains.reactor.reactor_causal_response.campaign_records import EmpiricalStudySource
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort

from empirical_lawhood.domains.reactor.reactor_regime_response.config import ReactorRegimeResponseDesign

from empirical_lawhood.domains.reactor.reactor_regime_response.prior import RegimePriorArtifact
from empirical_lawhood.domains.reactor.reactor_regime_response.continuation import RegimeCContinuation, RegimeRetainedInputsPort
from empirical_lawhood.domains.reactor.reactor_regime_response.preassay_readout import RegimeReferenceComparators

BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (ReactorRegimeResponseDesign,)),
    required_platform_port_keys=(
        "candidate-payload-publisher",
        "candidate-payload-reader",
        "reactor-regime-method-control-custody",
        "reactor-regime-method-d-binding",
        "reactor-regime-method-dependency-reader",
        "reactor-regime-method-prior-artifacts",
        "reactor-regime-method-reference-comparators",
        "reactor-regime-method-resource-guard",
        "reactor-regime-method-retained-inputs",
        "reactor-regime-method-source",
    ),
)


@dataclass(frozen=True, slots=True)
class RegimeMethodFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> RegimeMethodProvider:
        from empirical_lawhood.domains.reactor.reactor_causal_response.provider import DependencyCustodyReader
        from empirical_lawhood.domains.reactor.reactor_regime_response.provider import RegimeDMethodBinding, RegimeDMethodCustodyPort, RegimeMethodProvider
        if len(records) != 1 or not isinstance(
            records[0], ReactorRegimeResponseDesign
        ):
            raise ValueError("reactor method factory requires its exact design")
        ports = {port.port_key: port.port for port in platform_ports}
        if tuple(sorted(ports)) != self.binding.required_platform_port_keys or len(
            ports
        ) != len(platform_ports):
            raise ValueError("reactor method factory port roster differs")
        if not callable(
            getattr(
                ports["reactor-regime-method-dependency-reader"],
                "read_dependency",
                None,
            )
        ) or not callable(
            getattr(ports["reactor-regime-method-resource-guard"], "task", None)
        ):
            raise TypeError("reactor method factory lacks custody or task limits")
        if not callable(
            getattr(
                ports["candidate-payload-publisher"], "publish_candidate_payload", None
            )
        ):
            raise TypeError("reactor method factory lacks candidate publication")
        if not callable(
            getattr(ports["candidate-payload-reader"], "read_candidate_payload", None)
        ):
            raise TypeError("reactor method factory lacks candidate payload custody")
        priors = ports["reactor-regime-method-prior-artifacts"]
        if not isinstance(priors, tuple) or any(
            not isinstance(value, RegimePriorArtifact) for value in priors
        ):
            raise TypeError("reactor method factory prior B package custody differs")
        d_binding = ports["reactor-regime-method-d-binding"]
        d_source = ports["reactor-regime-method-source"]
        d_custody = ports["reactor-regime-method-control-custody"]
        references = ports["reactor-regime-method-reference-comparators"]
        retained = ports["reactor-regime-method-retained-inputs"]
        if (
            not callable(getattr(retained, "create_source", None))
            or not hasattr(retained, "continuation")
            or retained.continuation is not None
            and not isinstance(retained.continuation, RegimeCContinuation)
        ):
            raise TypeError("reactor method retained-input port lacks its declaration")
        if references is not None and not isinstance(
            references, RegimeReferenceComparators
        ):
            raise TypeError("retained comparator port lacks pinned canonical operands")
        if d_binding is not None and not isinstance(d_binding, RegimeDMethodBinding):
            raise TypeError("reactor method D authority binding differs")
        if d_source is not None and not isinstance(d_source, EmpiricalStudySource):
            raise TypeError("reactor method D source differs")
        if d_custody is not None and (
            not callable(getattr(d_custody, "open_prepared_store", None))
            or not callable(getattr(d_custody, "event_clock", None))
        ):
            raise TypeError("reactor method D prepared-event custody differs")
        return RegimeMethodProvider(
            registry,
            records[0],
            cast(
                DependencyCustodyReader,
                ports["reactor-regime-method-dependency-reader"],
            ),
            cast(EmpiricalResourceGuard, ports["reactor-regime-method-resource-guard"]),
            cast(CandidatePayloadPublisher, ports["candidate-payload-publisher"]),
            cast(CandidatePayloadReader, ports["candidate-payload-reader"]),
            cast(tuple[RegimePriorArtifact, ...], priors),
            d_binding,
            d_source,
            cast(RegimeDMethodCustodyPort | None, d_custody),
            references,
            cast(RegimeRetainedInputsPort, retained),
        )


_EXECUTABLE_ID = "executable-contribution.terminal-bench-science-regime.methods"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (RegimeMethodFactory(),)
_ISSUED_RECORD_TYPES = (ReactorRegimeResponseDesign,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
