"""Native NREL archive decoding, complete-unit reduction runners and held-source ports."""

from __future__ import annotations
from empirical_lawhood.domains.energy.inverter.archive_protocol import NRELPanelReductionConfig as _science_NRELPanelReductionConfig, NREL_ARCHIVE_PROTOCOL_VERSION as _science_NREL_ARCHIVE_PROTOCOL_VERSION, NREL_HELD_TABLE_ARTIFACT_ID as _science_NREL_HELD_TABLE_ARTIFACT_ID, NREL_HELD_TABLE_SCHEMA as _science_NREL_HELD_TABLE_SCHEMA, NREL_PHASE_ISSUE_ARTIFACT_ID as _science_NREL_PHASE_ISSUE_ARTIFACT_ID, NREL_PROFILE_ARTIFACT_ID as _science_NREL_PROFILE_ARTIFACT_ID, NREL_SOURCE_ARTIFACT_ID as _science_NREL_SOURCE_ARTIFACT_ID, _decode_key, _reduction_key, nrel_nrel_inverter_archive_registry as _science_nrel_nrel_inverter_archive_registry

from collections.abc import Callable
from dataclasses import fields

from empirical_lawhood.methods.structured_target import IndependentSubstrateCompleteTargetPanel, IndependentSubstrateStructuredPhaseIssue, IndependentSubstrateTargetPhase
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityManifest, CapabilityRegistry
from empirical_lawhood.execution.execution import RunnerResult, TaskContext, TaskOutputPayload, TaskRunner
from empirical_lawhood.execution.plans import ProtocolExecutionPlan
from empirical_lawhood.execution.providers import MAX_EXTERNAL_INPUT_CHUNK_BYTES, CapabilityOutputSemanticContract, CampaignRuntimeProvider, ExternalInputPayload, ExternalInputSource

from empirical_lawhood.domains.energy.inverter.analysis import build_nrel_panel
from empirical_lawhood.domains.energy.inverter.archive_contracts import NRELArchiveDecodeResult, NRELArchiveSourceBinding, NRELSafeDecodeProfile
from empirical_lawhood.adapters.physical.nrel_inverter_archive.safe_decode import safe_decode_nrel_table


class _NRELSafeDecodeRunner:
    def __init__(self, manifest: CapabilityManifest) -> None:
        self.manifest = manifest

    def execute(self, context: TaskContext) -> RunnerResult:
        sources = tuple(
            decode_canonical_bytes(
                port.read(), NRELArchiveSourceBinding, maximum_bytes=port.size_bytes
            )
            for port in context.input_ports
            if port.payload_schema == NRELArchiveSourceBinding.SCHEMA
        )
        profiles = tuple(
            decode_canonical_bytes(
                port.read(), NRELSafeDecodeProfile, maximum_bytes=port.size_bytes
            )
            for port in context.input_ports
            if port.payload_schema == NRELSafeDecodeProfile.SCHEMA
        )
        issues = tuple(
            decode_canonical_bytes(
                port.read(), IndependentSubstrateStructuredPhaseIssue, maximum_bytes=port.size_bytes
            )
            for port in context.input_ports
            if port.payload_schema == IndependentSubstrateStructuredPhaseIssue.SCHEMA
        )
        payloads = tuple(
            port.read()
            for port in context.input_ports
            if port.payload_schema == _science_NREL_HELD_TABLE_SCHEMA
        )
        if len(sources) != 1 or len(profiles) != 1 or len(issues) != 1 or len(payloads) != 1:
            raise ValueError("NREL decoder requires one source/profile/issue/member")
        profile = profiles[0]
        if (
            self.manifest.capability_key != _decode_key(profile.phase)
            or issues[0].phase is not profile.phase
            or issues[0].source_binding
            != ObjectIdentity.from_record(sources[0].binding_id, sources[0])
            or issues[0].planned_unit_ids != profile.included_preparation_ids
        ):
            raise ValueError("NREL decoder phase selects another capability")
        result = safe_decode_nrel_table(
            payload=payloads[0],
            source=sources[0],
            profile=profile,
            sealed_evaluation_decode_authorized=(
                profile.phase is IndependentSubstrateTargetPhase.EVALUATION
                and context.outcome_access is OutcomeAccess.EVALUATION_SEALED
            ),
        )
        if {value.payload_schema for value in context.output_ports} != {
            NRELArchiveDecodeResult.SCHEMA
        }:
            raise ValueError("NREL safe decode output schema differs")
        return RunnerResult(
            outputs=tuple(
                TaskOutputPayload(
                    output_id=port.output_id,
                    payload=result.canonical_bytes(),
                )
                for port in context.output_ports
            ),
            checks=(
                ReceiptCheck("nrel-member-hash-stable", True, ()),
                ReceiptCheck("nrel-no-object-deserialization", True, ()),
                ReceiptCheck("nrel-preparation-filter-exact", True, ()),
            ),
        )


class _NRELReductionRunner:
    def __init__(self, manifest: CapabilityManifest) -> None:
        self.manifest = manifest

    def execute(self, context: TaskContext) -> RunnerResult:
        configs = tuple(
            decode_canonical_bytes(
                port.read(), _science_NRELPanelReductionConfig, maximum_bytes=port.size_bytes
            )
            for port in context.input_ports
            if port.payload_schema == _science_NRELPanelReductionConfig.SCHEMA
        )
        sources = tuple(
            decode_canonical_bytes(
                port.read(), NRELArchiveSourceBinding, maximum_bytes=port.size_bytes
            )
            for port in context.input_ports
            if port.payload_schema == NRELArchiveSourceBinding.SCHEMA
        )
        profiles = tuple(
            decode_canonical_bytes(
                port.read(), NRELSafeDecodeProfile, maximum_bytes=port.size_bytes
            )
            for port in context.input_ports
            if port.payload_schema == NRELSafeDecodeProfile.SCHEMA
        )
        issues = tuple(
            decode_canonical_bytes(
                port.read(), IndependentSubstrateStructuredPhaseIssue, maximum_bytes=port.size_bytes
            )
            for port in context.input_ports
            if port.payload_schema == IndependentSubstrateStructuredPhaseIssue.SCHEMA
        )
        results = tuple(
            decode_canonical_bytes(
                port.read(), NRELArchiveDecodeResult, maximum_bytes=port.size_bytes
            )
            for port in context.input_ports
            if port.payload_schema == NRELArchiveDecodeResult.SCHEMA
        )
        if not (len(configs) == len(sources) == len(profiles) == len(issues) == len(results) == 1):
            raise ValueError("NREL reducer requires one config/source/profile/issue/result")
        config, source, profile, result = (
            configs[0],
            sources[0],
            profiles[0],
            results[0],
        )
        if (
            self.manifest.capability_key != _reduction_key(config.phase)
            or config.source_binding != ObjectIdentity.from_record(source.binding_id, source)
            or config.decode_profile != ObjectIdentity.from_record(profile.profile_id, profile)
            or config.phase_issue != ObjectIdentity.from_record(issues[0].issue_id, issues[0])
        ):
            raise ValueError("NREL reducer config/source/profile differs")
        panel = build_nrel_panel(source=source, profile=profile, result=result)
        if panel.planned_unit_ids != config.planned_unit_ids:
            raise ValueError("NREL reducer output denominator differs from issue")
        if {value.payload_schema for value in context.output_ports} != {
            IndependentSubstrateCompleteTargetPanel.SCHEMA
        }:
            raise ValueError("NREL reduction output schema differs")
        return RunnerResult(
            outputs=tuple(
                TaskOutputPayload(
                    output_id=port.output_id,
                    payload=panel.canonical_bytes(),
                )
                for port in context.output_ports
            ),
            checks=(
                ReceiptCheck("nrel-issued-preparations-retained", True, ()),
                ReceiptCheck("nrel-rows-and-channels-not-units", True, ()),
                ReceiptCheck("nrel-retrospective-prospective-controller-evaluation-excluded", True, ()),
            ),
        )


def nrel_nrel_inverter_archive_runners(*, registry: CapabilityRegistry) -> tuple[TaskRunner, ...]:
    return tuple(
        runner
        for phase in (IndependentSubstrateTargetPhase.DEVELOPMENT, IndependentSubstrateTargetPhase.EVALUATION)
        for runner in (
            _NRELSafeDecodeRunner(registry.resolve(_decode_key(phase), _science_NREL_ARCHIVE_PROTOCOL_VERSION)),
            _NRELReductionRunner(registry.resolve(_reduction_key(phase), _science_NREL_ARCHIVE_PROTOCOL_VERSION)),
        )
    )


class NRELHeldArchiveRuntimeProvider(CampaignRuntimeProvider):
    """Bind held member bytes through an injected bounded source, never a path."""

    def __init__(
        self,
        *,
        registry: CapabilityRegistry,
        source: NRELArchiveSourceBinding,
        profile: NRELSafeDecodeProfile,
        phase_issue: IndependentSubstrateStructuredPhaseIssue,
        reduction_config: _science_NRELPanelReductionConfig,
        held_member_source_factory: Callable[[], ExternalInputSource],
    ) -> None:
        implementation_hashes = {value.implementation_sha256 for value in registry.capabilities}
        if len(implementation_hashes) != 1 or registry != _science_nrel_nrel_inverter_archive_registry(
            implementation_sha256=next(iter(implementation_hashes))
        ):
            raise ValueError("NREL runtime provider registry differs")
        source_identity = ObjectIdentity.from_record(source.binding_id, source)
        profile_identity = ObjectIdentity.from_record(profile.profile_id, profile)
        if (
            profile.source_binding != source_identity
            or reduction_config.source_binding != source_identity
            or reduction_config.decode_profile != profile_identity
            or reduction_config.phase_issue
            != ObjectIdentity.from_record(phase_issue.issue_id, phase_issue)
            or reduction_config.phase is not profile.phase
        ):
            raise ValueError("NREL runtime provider source/profile scope differs")
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
            raise ValueError("NREL runtime provider member differs")
        self.registry = registry
        self.registry_sha256 = registry.fingerprint()
        self.source = source
        self.profile = profile
        self.phase_issue = phase_issue
        self.reduction_config = reduction_config
        self.member = member
        self._held_member_source_factory = held_member_source_factory
        self._runners = nrel_nrel_inverter_archive_runners(registry=registry)
        self.capability_count = len(self._runners)

    def runners(
        self,
        registry: CapabilityRegistry,
        source_records: tuple[CanonicalRecord, ...] = (),
    ) -> tuple[TaskRunner, ...]:
        if registry != self.registry or source_records:
            raise ValueError("NREL runtime provider registry/source differs")
        return self._runners

    def external_inputs(
        self,
        plan: ProtocolExecutionPlan,
        source_records: tuple[CanonicalRecord, ...] = (),
    ) -> tuple[ExternalInputPayload, ...]:
        if plan.registry_sha256 != self.registry_sha256 or source_records:
            raise ValueError("NREL runtime provider plan/source differs")
        specs = {
            value.logical_artifact_id: value
            for task in plan.tasks
            for value in task.external_inputs
        }
        records: dict[str, CanonicalRecord] = {
            _science_NREL_SOURCE_ARTIFACT_ID: self.source,
            _science_NREL_PROFILE_ARTIFACT_ID: self.profile,
            _science_NREL_PHASE_ISSUE_ARTIFACT_ID: self.phase_issue,
        }
        by_hash: dict[str, CanonicalRecord] = {
            self.profile.fingerprint(): self.profile,
            self.reduction_config.fingerprint(): self.reduction_config,
        }
        for task in plan.tasks:
            try:
                records[task.capability.config.artifact_id] = by_hash[
                    task.capability.config.content_sha256
                ]
            except KeyError as error:
                raise ValueError("NREL plan references an unknown config") from error
        canonical_spec_ids = set(specs) - {_science_NREL_HELD_TABLE_ARTIFACT_ID}
        if set(records) != canonical_spec_ids or _science_NREL_HELD_TABLE_ARTIFACT_ID not in specs:
            raise ValueError("NREL runtime external input roster differs")
        values: list[ExternalInputPayload] = []
        for artifact_id, record in sorted(records.items()):
            spec = specs[artifact_id]
            record_id = next(
                getattr(record, attribute)
                for attribute in (
                    "profile_id",
                    "config_id",
                    "binding_id",
                    "issue_id",
                )
                if hasattr(record, attribute)
            )
            parent = ArtifactLineageParent(
                identity=ObjectIdentity.from_record(record_id, record),
                visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                outcome_access=OutcomeAccess.OUTCOME_BLIND,
            )
            values.append(
                ExternalInputPayload.from_bytes(
                    logical_artifact_id=artifact_id,
                    payload_schema=record.SCHEMA,
                    profile=ArtifactProfile.CANONICAL_JSON,
                    media_type="application/vnd.empirical-lawhood.canonical+json",
                    payload=record.canonical_bytes(),
                    visibility_ceiling=(
                        spec.expected_visibility_ceiling or VisibilityCeiling.PROSPECTIVE
                    ),
                    outcome_access=(spec.expected_outcome_access or OutcomeAccess.OUTCOME_BLIND),
                    parent_visibility_ceilings=(parent.visibility_ceiling,),
                    lineage_parents=(parent,),
                    logical_content_sha256=spec.expected_content_sha256,
                )
            )
        raw_spec = specs[_science_NREL_HELD_TABLE_ARTIFACT_ID]
        raw_parent = ArtifactLineageParent(
            identity=ObjectIdentity.from_record(self.member.member_id, self.member),
            visibility_ceiling=(
                raw_spec.expected_visibility_ceiling or VisibilityCeiling.PROSPECTIVE
            ),
            outcome_access=(raw_spec.expected_outcome_access or self.profile.outcome_access),
        )
        values.append(
            ExternalInputPayload(
                logical_artifact_id=_science_NREL_HELD_TABLE_ARTIFACT_ID,
                payload_schema=_science_NREL_HELD_TABLE_SCHEMA,
                profile=ArtifactProfile.TEXT_PARAMETERS,
                media_type=(
                    "text/csv" if self.profile.delimiter == "," else "text/tab-separated-values"
                ),
                source=self._held_member_source_factory(),
                size_bytes=self.member.size_bytes,
                source_sha256=self.member.content_sha256,
                maximum_bytes=self.profile.maximum_payload_bytes,
                maximum_chunk_bytes=min(
                    MAX_EXTERNAL_INPUT_CHUNK_BYTES,
                    self.profile.maximum_payload_bytes,
                ),
                visibility_ceiling=raw_parent.visibility_ceiling,
                outcome_access=raw_parent.outcome_access,
                parent_visibility_ceilings=(raw_parent.visibility_ceiling,),
                lineage_parents=(raw_parent,),
                logical_content_sha256=raw_spec.expected_content_sha256,
            )
        )
        return tuple(sorted(values, key=lambda value: value.logical_artifact_id))

    def output_semantic_contracts(
        self,
        registry: CapabilityRegistry,
        execution_plan: ProtocolExecutionPlan | None = None,
    ) -> tuple[CapabilityOutputSemanticContract, ...]:
        if registry != self.registry:
            raise ValueError("NREL semantic registry differs")
        planned = None
        if execution_plan is not None:
            planned = {
                (task.capability.capability_key, output.payload_schema, output.profile)
                for task in execution_plan.tasks
                for output in task.outputs
            }
        record_types = {
            NRELArchiveDecodeResult.SCHEMA: NRELArchiveDecodeResult,
            IndependentSubstrateCompleteTargetPanel.SCHEMA: IndependentSubstrateCompleteTargetPanel,
        }
        values = []
        for manifest in registry.capabilities:
            for schema in manifest.output_schema_ids:
                key = (manifest.capability_key, schema, ArtifactProfile.CANONICAL_JSON)
                if planned is not None and key not in planned:
                    continue
                record_type = record_types[schema]
                values.append(
                    CapabilityOutputSemanticContract.from_manifest(
                        manifest,
                        payload_schema=schema,
                        profile=ArtifactProfile.CANONICAL_JSON,
                        top_level_keys=("schema", "value", "version"),
                        value_keys=tuple(sorted(value.name for value in fields(record_type))),
                    )
                )
        return tuple(sorted(values, key=lambda value: (value.capability_key, value.payload_schema)))

    def scientific_adjudication_contract(
        self,
        registry: CapabilityRegistry,
        execution_plan: ProtocolExecutionPlan | None = None,
    ) -> None:
        if registry != self.registry:
            raise ValueError("NREL adjudication registry differs")
        del execution_plan
        return None


__all__ = ['NRELHeldArchiveRuntimeProvider', 'nrel_nrel_inverter_archive_runners']
