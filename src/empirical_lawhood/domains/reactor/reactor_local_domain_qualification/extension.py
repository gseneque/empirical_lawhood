# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.provider import LocalMethodProvider


# Scientific registration and configuration.

from dataclasses import replace
from hashlib import sha256
from empirical_lawhood.methods.backbone_finite_action.extension import FINITE_ACTION_MANIFEST
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.config import LocalQualificationDesign
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.records import LocalRootEvidence
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.scoring import LocalCalibration
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.terminal import LocalQualificationResult

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="terminal-bench-science-local.local-qualification",
    kind=CapabilityKind.EVALUATOR,
    maximum_evidence_ceiling=EvidenceCeiling.LOCAL_LAW,
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
    config_schema=LocalQualificationDesign.SCHEMA,
    config_schema_sha256=sha256(LocalQualificationDesign.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            (
                LocalQualificationDesign.SCHEMA,
                LocalRootEvidence.SCHEMA,
                LocalCalibration.SCHEMA,
                LocalQualificationResult.SCHEMA,
            )
        )
    ),
    output_schema_ids=tuple(
        sorted(
            (
                LocalCalibration.SCHEMA,
                LocalQualificationResult.SCHEMA,
                ScientificAdjudicationRecord.SCHEMA,
            )
        )
    ),
    implementation_sha256=sha256(
        b"reactor-local-qualification:receiver-domain-conditional-root-maxima-existing-law-owner"
    ).hexdigest(),
    runtime_id="cpython-reactor-local",
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 7200, 8 * 1024**3, 128 * 1024**2),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "local-qualification",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (LocalQualificationDesign,),
    None,
    namespace="reactor-local-domain-qualification",
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast
from empirical_lawhood.methods.law_assessment import CandidatePayloadPublisher, CandidatePayloadReader
from empirical_lawhood.domains.reactor.reactor_causal_response.resource_contract import EmpiricalResourceGuard
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.config import LocalQualificationDesign


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (LocalQualificationDesign,)),
    required_platform_port_keys=(
        "candidate-payload-publisher",
        "candidate-payload-reader",
        "dependency-custody-reader",
        "reactor-local-resource-guard",
    ),
)


@dataclass(frozen=True, slots=True)
class LocalMethodFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> LocalMethodProvider:
        from empirical_lawhood.domains.reactor.reactor_causal_response.provider import DependencyCustodyReader
        from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.provider import LocalMethodProvider
        if len(records) != 1 or not isinstance(records[0], LocalQualificationDesign):
            raise ValueError("local factory requires its exact configuration")
        ports = {p.port_key: p.port for p in platform_ports}
        if tuple(sorted(ports)) != self.binding.required_platform_port_keys or len(ports) != len(
            platform_ports
        ):
            raise ValueError("local factory port roster differs")
        if not callable(
            getattr(ports["candidate-payload-publisher"], "publish_candidate_payload", None)
        ):
            raise TypeError("local factory port contract differs: candidate-payload-publisher")
        if not callable(getattr(ports["candidate-payload-reader"], "read_candidate_payload", None)):
            raise TypeError("local factory port contract differs: candidate-payload-reader")
        if not callable(getattr(ports["dependency-custody-reader"], "read_dependency", None)):
            raise TypeError("local factory port contract differs: dependency-custody-reader")
        if not callable(getattr(ports["reactor-local-resource-guard"], "task", None)):
            raise TypeError("local factory port contract differs: reactor-local-resource-guard")
        return LocalMethodProvider(
            registry,
            records[0],
            cast(DependencyCustodyReader, ports["dependency-custody-reader"]),
            cast(CandidatePayloadPublisher, ports["candidate-payload-publisher"]),
            cast(CandidatePayloadReader, ports["candidate-payload-reader"]),
            cast(EmpiricalResourceGuard, ports["reactor-local-resource-guard"]),
        )


_EXECUTABLE_ID = "executable-contribution.terminal-bench-science-local.methods"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (LocalMethodFactory(),)
_ISSUED_RECORD_TYPES = (LocalQualificationDesign,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
