# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from empirical_lawhood.domains.reactor.reactor_prepared_feed_qualification.provider import FeedMethodProvider


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
from empirical_lawhood.domains.reactor.reactor_prepared_feed_qualification.config import FeedQualificationDesign
from empirical_lawhood.domains.reactor.reactor_prepared_feed_qualification.records import FeedRootEvidence
from empirical_lawhood.domains.reactor.reactor_prepared_feed_qualification.scoring import FeedCalibration
from empirical_lawhood.domains.reactor.reactor_prepared_feed_qualification.terminal import FeedQualificationResult

CAPABILITY = replace(
    FINITE_ACTION_MANIFEST,
    capability_key="terminal-bench-science-feed.local-qualification",
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
    config_schema=FeedQualificationDesign.SCHEMA,
    config_schema_sha256=sha256(FeedQualificationDesign.SCHEMA.encode()).hexdigest(),
    input_schema_ids=tuple(
        sorted(
            (
                FeedQualificationDesign.SCHEMA,
                FeedRootEvidence.SCHEMA,
                FeedCalibration.SCHEMA,
                FeedQualificationResult.SCHEMA,
            )
        )
    ),
    output_schema_ids=tuple(
        sorted(
            (
                FeedCalibration.SCHEMA,
                FeedQualificationResult.SCHEMA,
                ScientificAdjudicationRecord.SCHEMA,
            )
        )
    ),
    implementation_sha256=sha256(
        b"reactor-feed-qualification:receiver-domain-conditional-root-maxima-existing-law-owner"
    ).hexdigest(),
    runtime_id="cpython-reactor-feed",
    resource_ceiling=ResourceBudget(1, 8 * 1024**3, 0, 7200, 8 * 1024**3, 128 * 1024**2),
)
_DISCOVERY_CONTRIBUTION, COMPONENTS = bundle(
    "local-qualification",
    ExtensionContributionKind.METHOD,
    CAPABILITY,
    (FeedQualificationDesign,),
    None,
    namespace="reactor-prepared-feed-qualification",
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
from empirical_lawhood.domains.reactor.reactor_prepared_feed_qualification.config import FeedQualificationDesign


BINDING = replace(
    executable(CAPABILITY, COMPONENTS, (FeedQualificationDesign,)),
    required_platform_port_keys=(
        "candidate-payload-publisher",
        "candidate-payload-reader",
        "dependency-custody-reader",
        "reactor-feed-resource-guard",
    ),
)


@dataclass(frozen=True, slots=True)
class FeedMethodFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> FeedMethodProvider:
        from empirical_lawhood.domains.reactor.reactor_causal_response.provider import DependencyCustodyReader
        from empirical_lawhood.domains.reactor.reactor_prepared_feed_qualification.provider import FeedMethodProvider
        if len(records) != 1 or not isinstance(records[0], FeedQualificationDesign):
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
        if not callable(getattr(ports["reactor-feed-resource-guard"], "task", None)):
            raise TypeError("local factory port contract differs: reactor-feed-resource-guard")
        return FeedMethodProvider(
            registry,
            records[0],
            cast(DependencyCustodyReader, ports["dependency-custody-reader"]),
            cast(CandidatePayloadPublisher, ports["candidate-payload-publisher"]),
            cast(CandidatePayloadReader, ports["candidate-payload-reader"]),
            cast(EmpiricalResourceGuard, ports["reactor-feed-resource-guard"]),
        )


_EXECUTABLE_ID = "executable-contribution.terminal-bench-science-feed.methods"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (FeedMethodFactory(),)
_ISSUED_RECORD_TYPES = (FeedQualificationDesign,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDING', 'CAPABILITY', 'EXTENSION']
