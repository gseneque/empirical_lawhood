# SPDX-License-Identifier: MPL-2.0
"""Exact later native history records, downstream of original prefix/seal."""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import METHODS, MatrixParameterHistoryControl
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile

from .forecast import ScheduledForecastSeal
from .records import ScheduledNativeEvidence, ScheduledPrefixHistory, ScheduledSource, identity


def full_access(source):
    return OutcomeAccess.DEVELOPMENT_VISIBLE if source.root.root.role is MatrixProgrammeRole.DEVELOPMENT else OutcomeAccess.EVALUATION_SEALED


def full_visibility(source):
    return VisibilityCeiling.DEVELOPMENT_ONLY if source.root.root.role is MatrixProgrammeRole.DEVELOPMENT else VisibilityCeiling.PROSPECTIVE


@dataclass(frozen=True, slots=True)
class ScheduledFullArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/full-arrays'
    operand_id: str
    source: ObjectIdentity
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    producers: tuple[ObjectIdentity, ...]
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        require_sorted_unique_ids(self.members, attribute='name', field_name='members')
        require_sorted_unique_ids(self.producers, attribute='object_id', field_name='producers')
        if (self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA or self.array_artifact.media_type != 'application/x-npz'
                or self.source.object_schema != ScheduledSource.SCHEMA
                or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or not self.members or any(not m.finite_required for m in self.members)
                or (self.outcome_access, self.visibility_ceiling) not in
                   ((OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY),
                    (OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE))):
            raise ValueError('scheduled full arrays change actual development/protected boundary')


@dataclass(frozen=True, slots=True)
class ScheduledFullHistory(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/full-history'
    history_id: str
    source: ObjectIdentity
    prefix: ObjectIdentity
    checkpoint: ObjectIdentity
    forecast: ObjectIdentity
    arrays: ScheduledFullArrays
    native: ScheduledNativeEvidence
    completed_primary_steps: int
    completed_fine_steps: int
    physical_forecast: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.history_id)
        if (self.prefix.object_schema != ScheduledPrefixHistory.SCHEMA or self.forecast.object_schema != ScheduledForecastSeal.SCHEMA
                or self.arrays.source != self.source or type(self.native) is not ScheduledNativeEvidence
                or type(self.completed_primary_steps) is not int or self.completed_primary_steps < 1
                or self.completed_fine_steps != 2*self.completed_primary_steps):
            raise ValueError('scheduled continuation changes original prefix/seal/full paired clock lineage')

    def validate_source(self, source, prefix, causal, seal, physical=None, *, native_context=None):
        from .source_index import ScheduledNativeSourceContext
        prefix.validate_source(source, native_context=native_context)
        role = 'continue-development' if source.root.root.role is MatrixProgrammeRole.DEVELOPMENT else 'continue'
        if type(native_context) is not ScheduledNativeSourceContext or native_context.source != source:
            raise ValueError('scheduled continuation requires its actual authenticated native configuration context')
        configuration, parent_task, operation, shared_sources = native_context.contract(role)
        validate_full_native_evidence(self, source, prefix, causal, seal, physical,
            configuration=configuration, parent_task=parent_task, operation=operation, shared_sources=shared_sources)


def validate_full_native_evidence(self, source, prefix, causal, seal, physical, *,
        configuration, parent_task, operation, shared_sources):
    """Original complete continuation proof with explicit typed-owner expectations."""
    definition = self.native.definition
    task = 'native-subwork.'+sha256((definition.parent_contact.task_id+':'+definition.subwork_id).encode()).hexdigest()
    c, start = source.coordinate, source.policy.cutoff_tick
    consumed = tuple(sorted((source.root.stream_identity(s) for s in source.root.streams if
        s.purpose.startswith('preparation') and start < c.ramp_ticks or s.purpose.startswith('autonomous') and c.total_ticks > max(start, c.ramp_ticks)), key=lambda x: x.object_id))
    physical_sources = set() if physical is None else {identity(physical)}
    if (self.source != identity(source) or self.prefix != identity(prefix) or self.checkpoint != identity(prefix.checkpoint)
            or self.physical_forecast != (identity(physical) if physical is not None else None)
            or physical is not None and (physical.source != identity(source) or physical.causal_prefix != identity(causal))
            or self.forecast != identity(seal) or seal.source != identity(source) or seal.prefix != identity(causal)
            or causal.history != identity(prefix) or causal.source != identity(source)
            or self.arrays.outcome_access is not full_access(source) or self.arrays.visibility_ceiling is not full_visibility(source)
            or definition.configuration != configuration or definition.subwork_id != 'continue.'+source.root_id
            or definition.operation_id != operation
            or definition.parent_contact.task_id != parent_task
            or definition.parent_contact.implementation_commit != source.provenance.observed_git_head
            or definition.parent_contact.run_id != prefix.native.definition.parent_contact.run_id
            or definition.code_sources_sha256 != source.provenance.code_sources_sha256
            or definition.dependency_lock_sha256 != source.provenance.dependency_lock_sha256
            or definition.streams != tuple(sorted((source.root.stream_identity(s) for s in source.root.streams), key=lambda x: x.object_id))
            or self.native.completion.consumed_streams != consumed
            or set(definition.sources) != set(shared_sources) | {
                identity(prefix), identity(prefix.checkpoint), identity(causal), identity(seal)} | physical_sources
            or self.completed_primary_steps != c.total_ticks
            or tuple((o.output_id, o.payload_schema, o.profile, o.media_type) for o in definition.outputs) !=
               (('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'),)
            or (self.native.receipt.run_id, self.native.receipt.task_id, self.native.receipt.attempt_id) !=
               (definition.parent_contact.run_id, task, definition.parent_contact.run_id+'.'+task+'.attempt-001')):
        raise ValueError('scheduled full history changes exact original source/checkpoint/seal/native custody')
    artifacts = tuple(a for a in self.native.receipt.output_logical_artifacts if a.logical_artifact_id == task+'.output.arrays')
    physical = tuple(p for p in self.native.receipt.output_materializations if p.logical_artifact_id == task+'.output.arrays')
    if (len(artifacts) != 1 or len(physical) != 1 or artifacts[0].content_sha256 != self.arrays.array_artifact.sha256
            or artifacts[0].outcome_access is not full_access(source) or artifacts[0].visibility_ceiling is not full_visibility(source)
            or (physical[0].physical_sha256, physical[0].size_bytes) != (self.arrays.array_artifact.sha256, self.arrays.array_artifact.size_bytes)):
        raise ValueError('scheduled continuation lacks exact original native array publication')


@dataclass(frozen=True, slots=True)
class ScheduledFullAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-history/full-assessment'
    assessment_id: str
    source: ObjectIdentity
    history: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterHistoryControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (self.history.object_schema != ScheduledFullHistory.SCHEMA or tuple(c.control_id for c in self.controls) != METHODS
                or type(self.numerical_pass) is not bool or self.numerical_pass != all(c.disposition == 'SATISFIED' for c in self.controls)):
            raise ValueError('scheduled full assessment loses complete independent history controls')
