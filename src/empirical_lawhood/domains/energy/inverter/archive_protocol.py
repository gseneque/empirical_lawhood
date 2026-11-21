"""NREL scientific phase, outcome-access, resource and graph declarations."""

from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar, Final
from empirical_lawhood.methods.structured_target import IndependentSubstrateCompleteTargetPanel, IndependentSubstrateStructuredPhaseIssue, IndependentSubstrateTargetPhase
from empirical_lawhood.methods.independent_substrate_grounding import IndependentSubstrateTargetKind
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_sha256, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.capabilities import CapabilityConfigRef, CapabilityKind, CapabilityManifest, CapabilityPermission, CapabilityRegistry
from empirical_lawhood.execution.candidate_compiler import CandidateGraphEdge, CandidateGraphExternalInput, CandidateGraphNode, CandidateScientificGraph, ContentIdentityPolicy, ObligationCoverage, ObligationCoverageBinding, StudyTemplate, ScientificInputRole
from empirical_lawhood.execution.candidate_composition import CandidateCapabilityRegistration
from empirical_lawhood.execution.plans import BarrierKind, OutputTemplate, ProtocolStepTemplate, ProtocolTemplate, ScientificStage
from empirical_lawhood.domains.energy.inverter.archive_contracts import NRELArchiveDecodeResult, NRELArchiveSourceBinding, NRELSafeDecodeProfile

NREL_ARCHIVE_PROTOCOL_VERSION: Final = "1.0.0"

NREL_ARCHIVE_PROVIDER_KEY: Final = "independent-substrate-grounding.nrel-held-archive-provider"

NREL_HELD_TABLE_SCHEMA: Final = 'empirical-lawhood/physical/nrel-inverter-archive/held-table-bytes'

NREL_SOURCE_ARTIFACT_ID: Final = "artifact.independent-substrate-grounding.nrel.source-binding"

NREL_PROFILE_ARTIFACT_ID: Final = "artifact.independent-substrate-grounding.nrel.safe-decode-profile"

NREL_PHASE_ISSUE_ARTIFACT_ID: Final = "artifact.independent-substrate-grounding.nrel.phase-issue"

NREL_HELD_TABLE_ARTIFACT_ID: Final = "artifact.independent-substrate-grounding.nrel.held-table-member"

NREL_DECODE_STEP_ID: Final = "decode-nrel-held-intervention-table"

NREL_REDUCTION_STEP_ID: Final = "reduce-nrel-complete-preparation-panel"

def _decode_key(phase: IndependentSubstrateTargetPhase) -> str:
    if phase is IndependentSubstrateTargetPhase.PROSPECTIVE_VALIDATION:
        raise ValueError("NREL retrospective archive cannot define controller use")
    return f"nrel.safe-decode-independent-substrate-grounding-{phase.value.lower()}-partition"

def _reduction_key(phase: IndependentSubstrateTargetPhase) -> str:
    if phase is IndependentSubstrateTargetPhase.PROSPECTIVE_VALIDATION:
        raise ValueError("NREL retrospective archive cannot define controller use")
    return f"nrel.reduce-independent-substrate-grounding-{phase.value.lower()}-panel"

@dataclass(frozen=True, slots=True)
class NRELPanelReductionConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/physical/nrel-inverter-archive/nrel-panel-reduction-config'

    config_id: str
    phase: IndependentSubstrateTargetPhase
    source_binding: ObjectIdentity
    decode_profile: ObjectIdentity
    phase_issue: ObjectIdentity
    planned_preparation_ids: tuple[str, ...]
    planned_unit_ids: tuple[str, ...]
    maximum_input_bytes: int

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        if self.phase is IndependentSubstrateTargetPhase.PROSPECTIVE_VALIDATION:
            raise ValueError("NREL retrospective archive cannot define controller use")
        if self.source_binding.object_schema != NRELArchiveSourceBinding.SCHEMA:
            raise ValueError("NREL reducer source identity differs")
        if self.decode_profile.object_schema != NRELSafeDecodeProfile.SCHEMA:
            raise ValueError("NREL reducer decode profile identity differs")
        if self.phase_issue.object_schema != IndependentSubstrateStructuredPhaseIssue.SCHEMA:
            raise ValueError("NREL reducer phase issue identity differs")
        require_sorted_unique_strings(
            self.planned_preparation_ids,
            field_name="planned_preparation_ids",
            allow_empty=False,
        )
        require_sorted_unique_strings(
            self.planned_unit_ids,
            field_name="planned_unit_ids",
            allow_empty=False,
        )
        if self.planned_unit_ids != self.planned_preparation_ids:
            raise ValueError("NREL planned units differ from physical preparations")
        if not 0 < self.maximum_input_bytes <= 2 * 1024**3:
            raise ValueError("NREL reducer input bound differs")

def nrel_panel_reduction_config(
    *,
    source: NRELArchiveSourceBinding,
    profile: NRELSafeDecodeProfile,
    phase_issue: IndependentSubstrateStructuredPhaseIssue,
) -> NRELPanelReductionConfig:
    if profile.source_binding != ObjectIdentity.from_record(source.binding_id, source):
        raise ValueError("NREL reducer profile names another source")
    if (
        phase_issue.slot is not IndependentSubstrateTargetKind.NREL_INVERTER
        or phase_issue.phase is not profile.phase
        or phase_issue.source_binding != profile.source_binding
        or phase_issue.planned_unit_ids != profile.included_preparation_ids
    ):
        raise ValueError("NREL reducer profile differs from the frozen phase issue")
    return NRELPanelReductionConfig(
        config_id=f"config.independent-substrate-grounding.nrel.{profile.phase.value.lower()}-panel-reduction",
        phase=profile.phase,
        source_binding=profile.source_binding,
        decode_profile=ObjectIdentity.from_record(profile.profile_id, profile),
        phase_issue=ObjectIdentity.from_record(phase_issue.issue_id, phase_issue),
        planned_preparation_ids=profile.included_preparation_ids,
        planned_unit_ids=profile.included_preparation_ids,
        maximum_input_bytes=2 * 1024**3,
    )

def _decode_budget() -> ResourceBudget:
    return ResourceBudget(
        cpu_cores=2,
        memory_bytes=8 * 1024**3,
        gpu_devices=0,
        wall_time_seconds=2 * 60 * 60,
        source_scan_bytes=64 * 1024**3,
        output_bytes=2 * 1024**3,
    )

def _reduction_budget() -> ResourceBudget:
    return ResourceBudget(
        cpu_cores=2,
        memory_bytes=8 * 1024**3,
        gpu_devices=0,
        wall_time_seconds=30 * 60,
        source_scan_bytes=2 * 1024**3,
        output_bytes=512 * 1024**2,
    )

def nrel_nrel_inverter_archive_registry(*, implementation_sha256: str) -> CapabilityRegistry:
    validate_sha256(implementation_sha256, field_name="implementation_sha256")
    capabilities: list[CapabilityManifest] = []
    for phase in (IndependentSubstrateTargetPhase.DEVELOPMENT, IndependentSubstrateTargetPhase.EVALUATION):
        decode_permissions = tuple(
            sorted(
                (
                    CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                    CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
                    *(
                        (CapabilityPermission.READ_DEVELOPMENT,)
                        if phase is IndependentSubstrateTargetPhase.DEVELOPMENT
                        else (CapabilityPermission.READ_SEALED_OUTCOMES,)
                    ),
                ),
                key=lambda value: value.value,
            )
        )
        reducer_permissions = tuple(
            sorted(
                (
                    CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                    CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
                    *(
                        (CapabilityPermission.READ_DEVELOPMENT,)
                        if phase is IndependentSubstrateTargetPhase.DEVELOPMENT
                        else (
                            CapabilityPermission.READ_SEALED_OUTCOMES,
                            CapabilityPermission.REVEAL_OUTCOMES,
                        )
                    ),
                ),
                key=lambda value: value.value,
            )
        )
        capabilities.extend(
            (
                CapabilityManifest(
                    capability_key=_decode_key(phase),
                    capability_version=NREL_ARCHIVE_PROTOCOL_VERSION,
                    kind=CapabilityKind.TRANSFORM,
                    config_schema=NRELSafeDecodeProfile.SCHEMA,
                    config_schema_sha256=sha256(
                        NRELSafeDecodeProfile.SCHEMA.encode("ascii")
                    ).hexdigest(),
                    input_schema_ids=tuple(
                        sorted(
                            (
                                NRELArchiveSourceBinding.SCHEMA,
                                NREL_HELD_TABLE_SCHEMA,
                                NRELSafeDecodeProfile.SCHEMA,
                                IndependentSubstrateStructuredPhaseIssue.SCHEMA,
                            )
                        )
                    ),
                    output_schema_ids=(NRELArchiveDecodeResult.SCHEMA,),
                    permissions=decode_permissions,
                    maximum_evidence_ceiling=EvidenceCeiling.LOCAL_LAW,
                    maximum_outcome_access=(
                        OutcomeAccess.DEVELOPMENT_VISIBLE
                        if phase is IndependentSubstrateTargetPhase.DEVELOPMENT
                        else OutcomeAccess.EVALUATION_SEALED
                    ),
                    resource_ceiling=_decode_budget(),
                    deterministic=True,
                    seed_required=False,
                    language_id="python",
                    runtime_id="nrel-bounded-utf8-table-decoder",
                    requires_clean_commit=True,
                    requires_active_mount=True,
                    requires_network=False,
                    conformance_check_ids=tuple(
                        sorted(
                            (
                                "exact-held-member-hash-before-and-after-decode",
                                "no-executable-or-object-deserialization",
                                "preparation-filter-frozen-before-receiver-decode",
                                "strict-header-unit-clock-action-roster",
                            )
                        )
                    ),
                    implementation_sha256=implementation_sha256,
                ),
                CapabilityManifest(
                    capability_key=_reduction_key(phase),
                    capability_version=NREL_ARCHIVE_PROTOCOL_VERSION,
                    kind=(
                        CapabilityKind.TRANSFORM
                        if phase is IndependentSubstrateTargetPhase.DEVELOPMENT
                        else CapabilityKind.EVALUATOR
                    ),
                    config_schema=NRELPanelReductionConfig.SCHEMA,
                    config_schema_sha256=sha256(
                        NRELPanelReductionConfig.SCHEMA.encode("ascii")
                    ).hexdigest(),
                    input_schema_ids=tuple(
                        sorted(
                            (
                                NRELArchiveDecodeResult.SCHEMA,
                                NRELArchiveSourceBinding.SCHEMA,
                                NRELPanelReductionConfig.SCHEMA,
                                NRELSafeDecodeProfile.SCHEMA,
                                IndependentSubstrateStructuredPhaseIssue.SCHEMA,
                            )
                        )
                    ),
                    output_schema_ids=(IndependentSubstrateCompleteTargetPanel.SCHEMA,),
                    permissions=reducer_permissions,
                    maximum_evidence_ceiling=EvidenceCeiling.LOCAL_LAW,
                    maximum_outcome_access=(
                        OutcomeAccess.DEVELOPMENT_VISIBLE
                        if phase is IndependentSubstrateTargetPhase.DEVELOPMENT
                        else OutcomeAccess.EVALUATOR_REVEAL
                    ),
                    resource_ceiling=_reduction_budget(),
                    deterministic=True,
                    seed_required=False,
                    language_id="python",
                    runtime_id="nrel-complete-preparation-reducer",
                    requires_clean_commit=True,
                    requires_active_mount=True,
                    requires_network=False,
                    conformance_check_ids=tuple(
                        sorted(
                            (
                                "action-clock-missingness-retained",
                                "apparatus-preparation-is-complete-unit",
                                "receiver-backaction-is-source-bound",
                                "rows-and-channels-do-not-inflate-replication",
                            )
                        )
                    ),
                    implementation_sha256=implementation_sha256,
                ),
            )
        )
    return CapabilityRegistry(
        registry_id="independent-substrate-grounding-nrel-held-archive-registry",
        capabilities=tuple(sorted(capabilities, key=lambda value: value.registry_id)),
    )

def nrel_nrel_inverter_archive_candidate_registrations(
    *,
    implementation_sha256: str,
) -> tuple[CandidateCapabilityRegistration, ...]:
    return tuple(
        CandidateCapabilityRegistration(
            manifest=manifest,
            provider_key=NREL_ARCHIVE_PROVIDER_KEY,
            provider_version=NREL_ARCHIVE_PROTOCOL_VERSION,
            config_media_type="application/vnd.empirical-lawhood.canonical+json",
            maximum_config_bytes=2 * 1024**2,
        )
        for manifest in nrel_nrel_inverter_archive_registry(
            implementation_sha256=implementation_sha256
        ).capabilities
    )

def _validate_ref(
    *,
    record: CanonicalRecord,
    record_id: str,
    ref: CapabilityConfigRef,
    manifest: CapabilityManifest,
) -> None:
    if (
        ref.config_id != record_id
        or ref.config_schema != record.SCHEMA
        or ref.config_schema_sha256 != manifest.config_schema_sha256
        or ref.content_sha256 != record.fingerprint()
    ):
        raise ValueError("NREL capability config reference differs")

def build_nrel_phase_protocol(
    *,
    registry: CapabilityRegistry,
    profile: NRELSafeDecodeProfile,
    phase_issue: IndependentSubstrateStructuredPhaseIssue,
    profile_config_ref: CapabilityConfigRef,
    reduction_config: NRELPanelReductionConfig,
    reduction_config_ref: CapabilityConfigRef,
) -> ProtocolTemplate:
    if (
        reduction_config.phase is not profile.phase
        or reduction_config.decode_profile
        != ObjectIdentity.from_record(profile.profile_id, profile)
        or reduction_config.phase_issue
        != ObjectIdentity.from_record(phase_issue.issue_id, phase_issue)
    ):
        raise ValueError("NREL protocol profile/reduction phase differs")
    decode_manifest = registry.resolve(_decode_key(profile.phase), NREL_ARCHIVE_PROTOCOL_VERSION)
    reducer_manifest = registry.resolve(_reduction_key(profile.phase), NREL_ARCHIVE_PROTOCOL_VERSION)
    _validate_ref(
        record=profile,
        record_id=profile.profile_id,
        ref=profile_config_ref,
        manifest=decode_manifest,
    )
    _validate_ref(
        record=reduction_config,
        record_id=reduction_config.config_id,
        ref=reduction_config_ref,
        manifest=reducer_manifest,
    )
    development = profile.phase is IndependentSubstrateTargetPhase.DEVELOPMENT
    decoder = ProtocolStepTemplate(
        step_id=NREL_DECODE_STEP_ID,
        stage=ScientificStage.TRANSFORM,
        capability_key=decode_manifest.capability_key,
        capability_version=decode_manifest.capability_version,
        config=profile_config_ref,
        dependency_step_ids=(),
        outputs=(
            OutputTemplate(
                output_id="safe-decode-result",
                payload_schema=NRELArchiveDecodeResult.SCHEMA,
                profile=ArtifactProfile.CANONICAL_JSON,
                media_type="application/vnd.empirical-lawhood.canonical+json",
                filename_suffix=".json",
            ),
        ),
        required_permissions=decode_manifest.permissions,
        requested_outcome_access=(
            OutcomeAccess.DEVELOPMENT_VISIBLE if development else OutcomeAccess.EVALUATION_SEALED
        ),
        visibility_ceiling=(
            VisibilityCeiling.DEVELOPMENT_ONLY if development else VisibilityCeiling.PROSPECTIVE
        ),
        resource_budget=decode_manifest.resource_ceiling,
        resource_lock_ids=("nrel-held-member-decoder",),
        barrier=BarrierKind.NONE if development else BarrierKind.FREEZE,
        maximum_attempts=2,
        obligation_ids=(
            "nrel-exact-held-member-and-safe-decoder",
            "nrel-frozen-row-partition-before-receiver-decode",
        ),
    )
    reducer = ProtocolStepTemplate(
        step_id=NREL_REDUCTION_STEP_ID,
        stage=ScientificStage.DEVELOP if development else ScientificStage.REVEAL,
        capability_key=reducer_manifest.capability_key,
        capability_version=reducer_manifest.capability_version,
        config=reduction_config_ref,
        dependency_step_ids=(decoder.step_id,),
        outputs=(
            OutputTemplate(
                output_id="complete-preparation-panel",
                payload_schema=IndependentSubstrateCompleteTargetPanel.SCHEMA,
                profile=ArtifactProfile.CANONICAL_JSON,
                media_type="application/vnd.empirical-lawhood.canonical+json",
                filename_suffix=".json",
            ),
        ),
        required_permissions=reducer_manifest.permissions,
        requested_outcome_access=(
            OutcomeAccess.DEVELOPMENT_VISIBLE if development else OutcomeAccess.EVALUATOR_REVEAL
        ),
        visibility_ceiling=(
            VisibilityCeiling.DEVELOPMENT_ONLY if development else VisibilityCeiling.OUTCOME_VISIBLE
        ),
        resource_budget=reducer_manifest.resource_ceiling,
        resource_lock_ids=("nrel-complete-preparation-reducer",),
        barrier=BarrierKind.NONE if development else BarrierKind.REVEAL,
        maximum_attempts=2,
        obligation_ids=(
            "nrel-action-and-receiver-missingness-retained",
            "nrel-complete-preparation-resampling-unit",
            "nrel-one-apparatus-physical-ceiling",
            "nrel-retrospective-no-prospective-controller-evaluation-promotion",
        ),
    )
    return ProtocolTemplate(
        template_id=f"independent-substrate-grounding-nrel-{profile.phase.value.lower()}-phase",
        template_version=NREL_ARCHIVE_PROTOCOL_VERSION,
        steps=(decoder, reducer),
        requires_model_set=False,
        requests_controller=False,
        nonactuating=True,
    )

def _record_input(
    *,
    input_id: str,
    role: ScientificInputRole,
    artifact_id: str,
    record: CanonicalRecord,
) -> CandidateGraphExternalInput:
    return CandidateGraphExternalInput(
        input_id=input_id,
        scientific_role=role,
        logical_artifact_id=artifact_id,
        content_identity_policy=ContentIdentityPolicy.EXACT_SHA256,
        expected_content_sha256=record.fingerprint(),
        payload_schema=record.SCHEMA,
        media_type="application/vnd.empirical-lawhood.canonical+json",
        maximum_size_bytes=2 * 1024**2,
        outcome_access=OutcomeAccess.OUTCOME_BLIND,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
    )

def nrel_phase_scientific_graph(
    *,
    protocol: ProtocolTemplate,
    registry: CapabilityRegistry,
    source: NRELArchiveSourceBinding,
    profile: NRELSafeDecodeProfile,
    phase_issue: IndependentSubstrateStructuredPhaseIssue,
) -> CandidateScientificGraph:
    if (
        profile.source_binding != ObjectIdentity.from_record(source.binding_id, source)
        or phase_issue.slot is not IndependentSubstrateTargetKind.NREL_INVERTER
        or phase_issue.phase is not profile.phase
        or phase_issue.source_binding != profile.source_binding
        or phase_issue.planned_unit_ids != profile.included_preparation_ids
    ):
        raise ValueError("NREL graph profile/source differs")
    decoder = next(value for value in protocol.steps if value.step_id == NREL_DECODE_STEP_ID)
    reducer = next(value for value in protocol.steps if value.step_id == NREL_REDUCTION_STEP_ID)
    member = next(
        (
            value
            for value in source.members
            if value.member_id == profile.member.object_id
            and ObjectIdentity.from_record(value.member_id, value) == profile.member
        ),
        None,
    )
    if member is None:
        raise ValueError("NREL graph profile member differs from source")
    source_input = _record_input(
        input_id="input.independent-substrate-grounding.nrel.source-binding",
        role=ScientificInputRole.SOURCE,
        artifact_id=NREL_SOURCE_ARTIFACT_ID,
        record=source,
    )
    profile_input = _record_input(
        input_id="input.independent-substrate-grounding.nrel.safe-decode-profile",
        role=ScientificInputRole.QUALIFICATION,
        artifact_id=NREL_PROFILE_ARTIFACT_ID,
        record=profile,
    )
    issue_input = _record_input(
        input_id="input.independent-substrate-grounding.nrel.phase-issue",
        role=ScientificInputRole.QUALIFICATION,
        artifact_id=NREL_PHASE_ISSUE_ARTIFACT_ID,
        record=phase_issue,
    )
    raw_input = CandidateGraphExternalInput(
        input_id="input.independent-substrate-grounding.nrel.held-table-member",
        scientific_role=ScientificInputRole.OUTCOME,
        logical_artifact_id=NREL_HELD_TABLE_ARTIFACT_ID,
        content_identity_policy=ContentIdentityPolicy.EXACT_SHA256,
        expected_content_sha256=member.content_sha256,
        payload_schema=NREL_HELD_TABLE_SCHEMA,
        media_type=("text/csv" if profile.delimiter == "," else "text/tab-separated-values"),
        maximum_size_bytes=profile.maximum_payload_bytes,
        outcome_access=profile.outcome_access,
        visibility_ceiling=(
            VisibilityCeiling.DEVELOPMENT_ONLY
            if profile.phase is IndependentSubstrateTargetPhase.DEVELOPMENT
            else VisibilityCeiling.PROSPECTIVE
        ),
    )
    nodes = tuple(
        CandidateGraphNode(
            node_id=step.step_id,
            stage=step.stage,
            capability_key=step.capability_key,
            capability_version=step.capability_version,
            implementation_sha256=registry.resolve(
                step.capability_key,
                step.capability_version,
            ).implementation_sha256,
            protocol_step_sha256=step.fingerprint(),
            obligation_ids=step.obligation_ids,
            outcome_access=step.requested_outcome_access,
            visibility_ceiling=step.visibility_ceiling,
            resource_budget=step.resource_budget,
        )
        for step in protocol.steps
    )
    edges = (
        CandidateGraphEdge(
            edge_id="edge.nrel.source.decoder",
            producer_node_id=None,
            producer_output_id=None,
            external_input_id=source_input.input_id,
            consumer_node_id=decoder.step_id,
            consumer_input_id="frozen-source-binding",
            scientific_role=source_input.scientific_role,
            logical_artifact_id=source_input.logical_artifact_id,
            payload_schema=source_input.payload_schema,
            media_type=source_input.media_type,
            maximum_size_bytes=source_input.maximum_size_bytes,
            outcome_access=source_input.outcome_access,
            visibility_ceiling=source_input.visibility_ceiling,
            barrier=decoder.barrier,
        ),
        CandidateGraphEdge(
            edge_id="edge.nrel.held-member.decoder",
            producer_node_id=None,
            producer_output_id=None,
            external_input_id=raw_input.input_id,
            consumer_node_id=decoder.step_id,
            consumer_input_id="held-table-bytes",
            scientific_role=raw_input.scientific_role,
            logical_artifact_id=raw_input.logical_artifact_id,
            payload_schema=raw_input.payload_schema,
            media_type=raw_input.media_type,
            maximum_size_bytes=raw_input.maximum_size_bytes,
            outcome_access=raw_input.outcome_access,
            visibility_ceiling=raw_input.visibility_ceiling,
            barrier=decoder.barrier,
        ),
        CandidateGraphEdge(
            edge_id="edge.nrel.phase-issue.decoder",
            producer_node_id=None,
            producer_output_id=None,
            external_input_id=issue_input.input_id,
            consumer_node_id=decoder.step_id,
            consumer_input_id="frozen-phase-issue",
            scientific_role=issue_input.scientific_role,
            logical_artifact_id=issue_input.logical_artifact_id,
            payload_schema=issue_input.payload_schema,
            media_type=issue_input.media_type,
            maximum_size_bytes=issue_input.maximum_size_bytes,
            outcome_access=issue_input.outcome_access,
            visibility_ceiling=issue_input.visibility_ceiling,
            barrier=decoder.barrier,
        ),
        CandidateGraphEdge(
            edge_id="edge.nrel.decode-result.reducer",
            producer_node_id=decoder.step_id,
            producer_output_id="safe-decode-result",
            external_input_id=None,
            consumer_node_id=reducer.step_id,
            consumer_input_id="safe-decode-result",
            scientific_role=ScientificInputRole.OUTCOME,
            logical_artifact_id="artifact.independent-substrate-grounding.nrel.safe-decode-result",
            payload_schema=NRELArchiveDecodeResult.SCHEMA,
            media_type="application/vnd.empirical-lawhood.canonical+json",
            maximum_size_bytes=2 * 1024**3,
            outcome_access=decoder.requested_outcome_access,
            visibility_ceiling=decoder.visibility_ceiling,
            barrier=reducer.barrier,
        ),
        CandidateGraphEdge(
            edge_id="edge.nrel.profile.reducer",
            producer_node_id=None,
            producer_output_id=None,
            external_input_id=profile_input.input_id,
            consumer_node_id=reducer.step_id,
            consumer_input_id="frozen-decode-profile",
            scientific_role=profile_input.scientific_role,
            logical_artifact_id=profile_input.logical_artifact_id,
            payload_schema=profile_input.payload_schema,
            media_type=profile_input.media_type,
            maximum_size_bytes=profile_input.maximum_size_bytes,
            outcome_access=profile_input.outcome_access,
            visibility_ceiling=profile_input.visibility_ceiling,
            barrier=reducer.barrier,
        ),
        CandidateGraphEdge(
            edge_id="edge.nrel.phase-issue.reducer",
            producer_node_id=None,
            producer_output_id=None,
            external_input_id=issue_input.input_id,
            consumer_node_id=reducer.step_id,
            consumer_input_id="frozen-phase-issue",
            scientific_role=issue_input.scientific_role,
            logical_artifact_id=issue_input.logical_artifact_id,
            payload_schema=issue_input.payload_schema,
            media_type=issue_input.media_type,
            maximum_size_bytes=issue_input.maximum_size_bytes,
            outcome_access=issue_input.outcome_access,
            visibility_ceiling=issue_input.visibility_ceiling,
            barrier=reducer.barrier,
        ),
        CandidateGraphEdge(
            edge_id="edge.nrel.source.reducer",
            producer_node_id=None,
            producer_output_id=None,
            external_input_id=source_input.input_id,
            consumer_node_id=reducer.step_id,
            consumer_input_id="frozen-source-binding",
            scientific_role=source_input.scientific_role,
            logical_artifact_id=source_input.logical_artifact_id,
            payload_schema=source_input.payload_schema,
            media_type=source_input.media_type,
            maximum_size_bytes=source_input.maximum_size_bytes,
            outcome_access=source_input.outcome_access,
            visibility_ceiling=source_input.visibility_ceiling,
            barrier=reducer.barrier,
        ),
    )
    return CandidateScientificGraph(
        graph_id=f"graph.{protocol.template_id}",
        external_inputs=tuple(
            sorted(
                (source_input, profile_input, issue_input, raw_input),
                key=lambda value: value.input_id,
            )
        ),
        nodes=tuple(sorted(nodes, key=lambda value: value.node_id)),
        edges=tuple(sorted(edges, key=lambda value: value.edge_id)),
    )

def nrel_phase_study_template(
    *,
    protocol: ProtocolTemplate,
    graph: CandidateScientificGraph,
) -> StudyTemplate:
    steps = {value.step_id: value for value in protocol.steps}
    bindings = tuple(
        sorted(
            (
                ObligationCoverageBinding(
                    obligation_id=obligation_id,
                    proof_owner_node_id=node.node_id,
                    required_output_id=steps[node.node_id].outputs[0].output_id,
                    contributor_edge_ids=tuple(
                        sorted(
                            edge.edge_id
                            for edge in graph.edges
                            if edge.consumer_node_id == node.node_id
                        )
                    ),
                )
                for node in graph.nodes
                for obligation_id in node.obligation_ids
            ),
            key=lambda value: value.obligation_id,
        )
    )
    return StudyTemplate(
        template_key=protocol.template_id,
        template_version=protocol.template_version,
        protocol=protocol,
        graph=graph,
        coverage=ObligationCoverage(
            coverage_id=f"coverage.{protocol.template_id}",
            bindings=bindings,
        ),
    )
