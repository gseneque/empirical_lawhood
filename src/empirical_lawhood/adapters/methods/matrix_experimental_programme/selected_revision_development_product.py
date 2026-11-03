# SPDX-License-Identifier: MPL-2.0
"""Original development nomination locators, without issue or reveal authority."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt, derived_outcome_access
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, DevelopmentRunPlan
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave

from .selected_revision_results import MatrixRevisionProgrammeAssessment


@dataclass(frozen=True, slots=True)
class MatrixRevisionDevelopmentProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/revision-development-product"
    binding_id: str
    authoring_relative_path: str
    authored_wave: ObjectIdentity
    run_plan: ObjectIdentity
    execution_plan: ObjectIdentity
    run_id: str
    task_id: str
    receipt: ObjectIdentity
    logical_artifact_id: str
    record: ObjectIdentity
    publication: ArtifactWriteResult

    def __post_init__(self):
        for name in (self.binding_id, self.run_id, self.task_id, self.logical_artifact_id):
            validate_stable_id(name)
        validate_relative_locator(self.authoring_relative_path)
        for pin, kind in ((self.authored_wave, AuthoredRecursiveWave), (self.run_plan, DevelopmentRunPlan),
                (self.execution_plan, DevelopmentExecutionPlan), (self.receipt, CanonicalTaskReceipt), (self.record, MatrixRevisionProgrammeAssessment)):
            if type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION):
                raise TypeError("selected development product requires exact authored/plan/receipt/scientific locators")
            pin.__post_init__()
        if type(self.publication) is not ArtifactWriteResult:
            raise TypeError("selected development requires its actual publication metadata")
        parents = self.publication.logical.lineage_parents
        expected_access = derived_outcome_access(OutcomeAccess.DEVELOPMENT_VISIBLE,
            *(value.outcome_access for value in parents))
        expected_visibility = inherited_visibility((VisibilityCeiling.DEVELOPMENT_ONLY,
            *(value.visibility_ceiling for value in parents)), expected_access)
        if (self.run_plan.object_id != self.run_id or type(self.publication) is not ArtifactWriteResult
                or self.publication.logical.logical_artifact_id != self.logical_artifact_id
                or self.publication.logical.profile is not ArtifactProfile.CANONICAL_JSON
                or self.publication.logical.media_type != "application/json"
                or self.publication.logical.payload_schema != self.record.object_schema
                or self.publication.logical.content_sha256 != self.record.object_fingerprint
                or self.publication.materialization.physical_sha256 != self.record.object_fingerprint
                or self.publication.logical.outcome_access is not expected_access
                or self.publication.logical.visibility_ceiling is not expected_visibility):
            raise ValueError("selected development product changes its original publication or exposed development lane")
        self.publication.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.binding_id, self)
