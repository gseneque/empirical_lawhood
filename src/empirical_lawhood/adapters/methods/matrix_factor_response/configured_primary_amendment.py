# SPDX-License-Identifier: MPL-2.0
"""Explicit primary alpha/family amendment over unchanged native TRAIN science."""
from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
from .configured_protected_specification import ConfiguredProtectedE3Specification
from .configured_specification import ConfiguredE3Assessment
from .native_training_records import NativeTrainingAcquisitionRequest, NativeTrainingAcquisitionSpecification, NativeTrainingAcquisitionSeal

SCOPE = "ONLY_PRIMARY_ASSESSMENT_ALPHA_AND_DECLARED_FAMILY_CHANGED_NATIVE_MEASUREMENT_METHODS_LABELS_RESERVATION_UNCHANGED"


def _pin(value, kind):
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise TypeError("primary amendment substitutes an exact original native operand edition")
    value.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixE3PrimaryFamilyAmendment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/primary-family-amendment"
    record_id: str
    original_candidate: ConfiguredProtectedE3Specification
    assessment: ConfiguredE3Assessment
    original_native_request: ObjectIdentity
    original_native_specification: ObjectIdentity
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.original_candidate) is not ConfiguredProtectedE3Specification or type(self.assessment) is not ConfiguredE3Assessment or self.scope != SCOPE:
            raise TypeError("primary amendment requires exact candidate/assessment and explicit alpha-only scope")
        self.original_candidate.__post_init__(); self.assessment.__post_init__()
        _pin(self.original_native_request, NativeTrainingAcquisitionRequest)
        _pin(self.original_native_specification, NativeTrainingAcquisitionSpecification)
        old = self.original_candidate.assessment
        if replace(old, alpha_numerator=self.assessment.alpha_numerator, alpha_denominator=self.assessment.alpha_denominator,
                comparison_ids=self.assessment.comparison_ids) != self.assessment:
            raise ValueError("primary amendment changes a non-alpha assessment selection")
        if (not set(old.comparison_ids) <= set(self.assessment.comparison_ids)
                or old.alpha * len(old.comparison_ids) != self.assessment.alpha * len(self.assessment.comparison_ids)
                or self.assessment.alpha > old.alpha or self.assessment == old):
            raise ValueError("primary amendment must preserve the exact family budget without dropping a frozen claim")

    @property
    def identity(self): return ObjectIdentity.from_record(self.record_id, self)

    @property
    def candidate(self): return replace(self.original_candidate, assessment=self.assessment)

    def validate_native(self, specification, request):
        self.__post_init__()
        if (type(specification) is not NativeTrainingAcquisitionSpecification or type(request) is not NativeTrainingAcquisitionRequest
                or specification.identity != self.original_native_specification or request.identity != self.original_native_request
                or request.candidate_specification != self.original_candidate or specification.candidate != self.original_candidate.identity
                or specification.measurement != self.original_candidate.measurement
                or specification.future_reservation != ObjectIdentity.from_record(request.future_manifest.reservation.reservation_id, request.future_manifest.reservation)):
            raise ValueError("primary amendment changes the exact original native candidate, measurement or reservation")


def _publication(publication, pin, *, access, ceiling):
    if type(publication) is not ArtifactWriteResult:
        raise TypeError("primary amendment requires actual immutable original publication handles")
    publication.__post_init__()
    logical, physical = publication.logical, publication.materialization
    if (logical.payload_schema, logical.content_sha256, physical.physical_sha256, logical.profile, logical.media_type,
            logical.outcome_access, logical.visibility_ceiling) != (pin.object_schema, pin.object_fingerprint, pin.object_fingerprint,
                ArtifactProfile.CANONICAL_JSON, "application/json", access, ceiling):
        raise ValueError("primary amendment changes original native publication bytes or exposure")


@dataclass(frozen=True, slots=True)
class MatrixE3PrimaryFamilyAmendmentBinding(CanonicalRecord):
    """Reference-only original native controls and unchanged bank publications."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/primary-family-amendment-binding"
    record_id: str
    amendment: MatrixE3PrimaryFamilyAmendment
    native_specification_publication: ArtifactWriteResult
    native_training_locator: MatrixFiniteDtTrainingLocator
    entry_receipt: ObjectIdentity
    acquisition: ObjectIdentity
    acquisition_publication: ArtifactWriteResult
    native_bank_publications: tuple[ArtifactWriteResult, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.amendment) is not MatrixE3PrimaryFamilyAmendment:
            raise TypeError("primary binding loses its exact scientific amendment")
        self.amendment.__post_init__(); _pin(self.acquisition, NativeTrainingAcquisitionSeal)
        _pin(self.entry_receipt, CanonicalTaskReceipt)
        if type(self.native_training_locator) is not MatrixFiniteDtTrainingLocator:
            raise TypeError("primary binding requires the actual original native plan locator")
        self.native_training_locator.__post_init__()
        _publication(self.native_specification_publication, self.amendment.original_native_specification,
            access=OutcomeAccess.OUTCOME_BLIND, ceiling=VisibilityCeiling.PROSPECTIVE)
        _publication(self.acquisition_publication, self.acquisition,
            access=OutcomeAccess.DEVELOPMENT_VISIBLE, ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
        from .native_training_records import native_training_bank_types
        if type(self.native_bank_publications) is not tuple or len(self.native_bank_publications) != 2:
            raise ValueError("primary amendment needs both complete original native bank publications")
        for publication, kind in zip(self.native_bank_publications, native_training_bank_types(), strict=True):
            if type(publication) is not ArtifactWriteResult or publication.logical.payload_schema != kind.SCHEMA:
                raise TypeError("primary amendment swaps exact native feature/outcome bank publications")
            pin = ObjectIdentity(publication.logical.logical_artifact_id, kind.SCHEMA, kind.VERSION, publication.logical.content_sha256)
            _publication(publication, pin, access=OutcomeAccess.DEVELOPMENT_VISIBLE, ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)

    @property
    def identity(self): return ObjectIdentity.from_record(self.record_id, self)

    def validate_selection(self, selection):
        self.__post_init__()
        candidate = self.amendment.candidate
        if (selection.fit_config.specification != candidate.identity
                or any(value.specification != candidate.identity for value in selection.projections)
                or selection.response_selection.specification != candidate.identity):
            raise ValueError("primary amendment substitutes the actual current candidate projections")
        for artifact, publication in zip((selection.training_features, selection.training_outcomes), self.native_bank_publications, strict=True):
            if (artifact.artifact_id, artifact.payload_schema, artifact.sha256, artifact.size_bytes, artifact.media_type) != (
                    publication.logical.logical_artifact_id, publication.logical.payload_schema, publication.logical.content_sha256, publication.materialization.size_bytes, publication.logical.media_type):
                raise ValueError("primary amendment changes an original native bank operand")


def primary_amendment_root(selection, binding):
    """Bind the actual amendment before current candidate/entry construction."""
    binding.validate_selection(selection)
    root = selection.root; pin = binding.identity
    row = DesignInputRecord(selection.selection_id + ".primary-family-amendment", pin, pin.object_fingerprint,
        selection.fit_config.fit_cutoff, DesignInputRole.READINESS_METADATA, OutcomeAccess.OUTCOME_BLIND,
        VisibilityCeiling.PROSPECTIVE, root.system.authority_policy.delegate_id)
    if any(value.input_id == row.input_id for value in root.design_inputs):
        raise ValueError("primary amendment conflicts with an existing frozen design input")
    design = tuple(sorted((*root.design_inputs, row), key=lambda value: value.input_id))
    return replace(root, design_inputs=design, design_origin=replace(root.design_origin, declared_input_ids=tuple(value.input_id for value in design)))


def bind_primary_amendment(selection, binding):
    from .configured_protected_preparation import ConfiguredProtectedE3PreparationSelection
    if type(selection) is not ConfiguredProtectedE3PreparationSelection:
        raise TypeError("primary binding requires the exact current configured preparation")
    root = primary_amendment_root(selection, binding)
    entry = replace(selection.entry_package, checklist=replace(selection.entry_package.checklist, draft=ObjectIdentity.from_record(root.draft_id, root)))
    return replace(selection, root=root, entry_package=entry, primary_amendment=binding)
