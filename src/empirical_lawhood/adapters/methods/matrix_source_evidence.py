# SPDX-License-Identifier: MPL-2.0
"""Original Matrix source-pipeline inputs; constructing these grants nothing.

These generic records replay the existing source and scientific-qualification
owners. Source-free demonstration media are deliberately absent from this route.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id
from empirical_lawhood.planning.dataset_authority import DatasetOperationRequest
from empirical_lawhood.planning.evidence_profiles import EvidenceProfileSelection
from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceGateEvidence, ScientificSourceQualificationSpec
from empirical_lawhood.planning.source_pipelines import SourcePipelineProfile, SourcePipelineQualificationReceipt
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.datasets import DatasetCapabilityRegistry
from empirical_lawhood.runtime.scientific_source_qualification import ScientificSourceQualificationService
from empirical_lawhood.runtime.source_pipelines import SourcePipelineExecutionEvidence, compile_source_pipeline, qualify_source_pipeline
from empirical_lawhood.runtime.sources import SourceCapabilityManifest


def reference(record, field):
    return ObjectIdentity.from_record(getattr(record, field), record)


@dataclass(frozen=True, slots=True)
class MatrixSourcePipelineConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/source-pipeline-config"
    config_id: str
    profile: SourcePipelineProfile
    source_manifest: SourceCapabilityManifest
    capability_registry: CapabilityRegistry
    dataset_registry: DatasetCapabilityRegistry
    dataset_operation_request: DatasetOperationRequest
    execution_evidence: SourcePipelineExecutionEvidence
    decision_clock_id: str
    decision_time_utc: str

    def __post_init__(self):
        validate_stable_id(self.config_id)
        validate_stable_id(self.decision_clock_id)
        for value, kind in ((self.profile, SourcePipelineProfile), (self.source_manifest, SourceCapabilityManifest),
                (self.capability_registry, CapabilityRegistry), (self.dataset_registry, DatasetCapabilityRegistry),
                (self.dataset_operation_request, DatasetOperationRequest), (self.execution_evidence, SourcePipelineExecutionEvidence)):
            if type(value) is not kind:
                raise TypeError("Matrix source replay requires original typed pipeline inputs")
            value.__post_init__()
        if type(self.decision_time_utc) is not str:
            raise TypeError("Matrix source replay requires the original authority decision time")

    @property
    def identity(self):
        return reference(self, "config_id")

    def assess(self):
        compilation = compile_source_pipeline(self.profile, source_manifest=self.source_manifest,
            capability_registry=self.capability_registry, dataset_registry=self.dataset_registry,
            dataset_operation_request=self.dataset_operation_request)
        clock = _OriginalDecisionClock(self.decision_clock_id, self.decision_time_utc)
        return qualify_source_pipeline(self.profile, compilation, self.execution_evidence,
            source_manifest=self.source_manifest, decision_clock=clock)


@dataclass(frozen=True, slots=True)
class _OriginalDecisionClock:
    """Replay the decision bound inside an authenticated original configuration."""
    clock_id: str
    timestamp: str

    def now_utc(self):
        return self.timestamp


@dataclass(frozen=True, slots=True)
class MatrixSourceQualificationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/scientific-source-qualification-config"
    config_id: str
    specification: ScientificSourceQualificationSpec
    pipeline_receipt: SourcePipelineQualificationReceipt
    capability_registry: CapabilityRegistry
    gate_evidence: tuple[ScientificSourceGateEvidence, ...]

    def __post_init__(self):
        validate_stable_id(self.config_id)
        for value, kind in ((self.specification, ScientificSourceQualificationSpec),
                (self.pipeline_receipt, SourcePipelineQualificationReceipt), (self.capability_registry, CapabilityRegistry)):
            if type(value) is not kind:
                raise TypeError("Matrix source qualification requires original typed scientific inputs")
            value.__post_init__()
        if type(self.gate_evidence) is not tuple or any(type(value) is not ScientificSourceGateEvidence for value in self.gate_evidence):
            raise TypeError("Matrix source qualification requires immutable original gate evidence")
        require_sorted_unique_ids(self.gate_evidence, attribute="evidence_id", field_name="Matrix original source gates")
        for value in self.gate_evidence:
            value.__post_init__()

    @property
    def identity(self):
        return reference(self, "config_id")

    def assess(self):
        return ScientificSourceQualificationService(self.capability_registry).finalize(
            spec=self.specification, pipeline_receipt=self.pipeline_receipt, gate_evidence=self.gate_evidence)


@dataclass(frozen=True, slots=True)
class MatrixSourcePipelineEvidence(CanonicalRecord):
    """Actual source-owner inputs and output, without an authentication verdict."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/source-pipeline-evidence"
    record_id: str
    pipeline_config: MatrixSourcePipelineConfig
    receipt: SourcePipelineQualificationReceipt
    qualification_config: MatrixSourceQualificationConfig
    evidence_profile: EvidenceProfileSelection

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.pipeline_config, MatrixSourcePipelineConfig), (self.receipt, SourcePipelineQualificationReceipt),
                (self.qualification_config, MatrixSourceQualificationConfig), (self.evidence_profile, EvidenceProfileSelection)):
            if type(value) is not kind:
                raise TypeError("Matrix source custody requires original generic pipeline and qualification inputs")
            value.__post_init__()
        if self.qualification_config.pipeline_receipt != self.receipt:
            raise ValueError("Matrix source custody substitutes its original pipeline receipt")

    @property
    def identity(self):
        return reference(self, "record_id")


def source_declarations():
    """Cold registered projections for the shared genuine record qualifiers."""
    from .matrix_source_bindings import source_declarations as declarations
    return declarations()
