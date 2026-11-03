# SPDX-License-Identifier: MPL-2.0
"""Actual E4 producers and source locators for revision downstream entry."""
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceQualificationSpec, ScientificSourceQualificationResult
from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineEvidence
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4DevelopmentProduct
from .selected_entry import MatrixSelectedOriginalProduct
from .selected_revision_development_product import MatrixRevisionDevelopmentProduct
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PublicCalibration
from .selected_revision_programme import MatrixRevisionPreparedProgramme


@dataclass(frozen=True, slots=True)
class MatrixRevisionEntryEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/revision-entry-evidence"
    record_id: str
    programme: ObjectIdentity
    revision_fit: SelectedE4DevelopmentProduct
    revision_freeze: SelectedE4DevelopmentProduct
    downstream_nomination: MatrixSelectedOriginalProduct
    calibration: MatrixSelectedOriginalProduct
    revision_export: ObjectIdentity
    public_calibration: SelectedE4PublicCalibration
    original_e3_package: ObjectIdentity
    source_specification: ScientificSourceQualificationSpec | None
    pipeline: MatrixSourcePipelineEvidence | None
    source_result: ScientificSourceQualificationResult | None
    qualification_executions: tuple[RecursivePriorExecutionBinding, ...]
    publications: tuple[tuple[ObjectIdentity, ArtifactWriteResult], ...]
    preparation_nomination: MatrixRevisionDevelopmentProduct | None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != MatrixRevisionPreparedProgramme.SCHEMA
                or type(self.revision_fit) is not SelectedE4DevelopmentProduct or type(self.revision_freeze) is not SelectedE4DevelopmentProduct
                or type(self.downstream_nomination) is not MatrixSelectedOriginalProduct
                or type(self.calibration) is not MatrixSelectedOriginalProduct
                or type(self.revision_export) is not ObjectIdentity or self.revision_export.object_schema != "empirical-lawhood/matrix-selected-e4/revision-export"
                or type(self.public_calibration) is not SelectedE4PublicCalibration or type(self.original_e3_package) is not ObjectIdentity
                or self.preparation_nomination is not None and type(self.preparation_nomination) is not MatrixRevisionDevelopmentProduct
                or type(self.qualification_executions) is not tuple
                or any(type(value) is not RecursivePriorExecutionBinding for value in self.qualification_executions)
                or type(self.publications) is not tuple):
            raise TypeError("revision entry needs exact original DEV/CONF/CAL and source custody locators")
        for value in (self.programme, self.revision_fit, self.revision_freeze, self.downstream_nomination, self.calibration, self.revision_export, self.public_calibration, self.original_e3_package,
                *self.qualification_executions):
            value.__post_init__()
        optional = (self.source_specification, self.pipeline, self.source_result)
        kinds = (ScientificSourceQualificationSpec, MatrixSourcePipelineEvidence, ScientificSourceQualificationResult)
        if any(value is None for value in optional) != all(value is None for value in optional):
            raise ValueError("revision entry cannot supply a partial source-qualification chain")
        for value, kind in zip(optional, kinds, strict=True):
            if value is not None:
                if type(value) is not kind:
                    raise TypeError("revision source evidence changes its exact existing qualification owner")
                value.__post_init__()
        pins = []
        for row in self.publications:
            if type(row) is not tuple or len(row) != 2 or type(row[0]) is not ObjectIdentity or type(row[1]) is not ArtifactWriteResult:
                raise TypeError("revision source publications require exact original pin/publication pairs")
            pin, publication = row
            pin.__post_init__(); publication.__post_init__()
            if (pin.object_schema, pin.object_fingerprint) != (publication.logical.payload_schema, publication.logical.content_sha256):
                raise ValueError("revision source publication substitutes exact original bytes")
            pins.append(pin.object_id)
        if tuple(pins) != tuple(sorted(set(pins))):
            raise ValueError("revision source publications require a complete sorted unique census")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def validate_entry_evidence(evidence, programme):
    from .selected_original_commitments import MatrixRevisionEntryEvidenceV2
    if type(evidence) not in (MatrixRevisionEntryEvidence, MatrixRevisionEntryEvidenceV2) or type(programme) is not MatrixRevisionPreparedProgramme:
        raise TypeError("revision entry requires its exact supplied programme and evidence")
    evidence.__post_init__(); programme.__post_init__()
    package = programme.selected_package
    if (evidence.programme != programme.identity or evidence.downstream_nomination.record != package.nomination
            or evidence.calibration.record != package.original_calibration
            or evidence.public_calibration.original != package.original_calibration
            or package.models.relation_fit is not None and package.frozen_calibration != evidence.public_calibration
            or package.reference_package is not None and package.reference_package.original_package != evidence.original_e3_package
            or evidence.revision_fit.record != package.models.development_nomination
            or evidence.revision_freeze.record != package.models.frozen):
        raise ValueError("revision entry substitutes original model freeze, CONF selection or CAL producer")
    if programme.phase == "E5_OPPORTUNITY":
        if evidence.source_specification is not None or evidence.preparation_nomination is not None:
            raise ValueError("development opportunity cannot assert a protected source/recipe authority")
    elif evidence.source_specification is None:
        raise ValueError("protected revision entry requires genuine complete source qualification")
    if (programme.preparation_nomination is None) != (evidence.preparation_nomination is None):
        raise ValueError("revision CONF loses its actual separate development recipe producer")
    if evidence.preparation_nomination is not None and evidence.preparation_nomination.record != programme.preparation_nomination:
        raise ValueError("revision CONF substitutes its original development recipe nomination")
