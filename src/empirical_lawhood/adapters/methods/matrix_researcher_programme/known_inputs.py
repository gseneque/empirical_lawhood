# SPDX-License-Identifier: MPL-2.0
"""Bounded prospective programme inputs, separate from later scientific results.

These records bind actual publications. They do not establish freshness,
sampling, source qualification, issue, execution or outcome-access authority.
The ordinary guarded reader must authenticate and join the referenced bodies.
"""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_streams import SelectedE4StreamRecipe
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult

PHASE_INPUT_ROLES = (
    "e1", "e2", "train", "e3.calibration", "e3.confirmation",
    "e4.development", "e4.calibration", "e4.confirmation",
    "e5.development", "e5.confirmation", "e6.nearby", "e6.shifted",
)


@dataclass(frozen=True, slots=True)
class MatrixProgrammePublishedInput(CanonicalRecord):
    """One exact canonical record and its actual blind publication handle."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-programme/published-input"
    record: ObjectIdentity
    publication: ArtifactWriteResult

    def __post_init__(self):
        if type(self.record) is not ObjectIdentity or type(self.publication) is not ArtifactWriteResult:
            raise TypeError("programme inputs require exact typed identities and actual publications")
        self.record.__post_init__()
        self.publication.__post_init__()
        logical, material = self.publication.logical, self.publication.materialization
        if ((logical.payload_schema, logical.profile, logical.media_type, logical.content_sha256,
                logical.outcome_access, logical.visibility_ceiling, material.physical_sha256,
                material.compression, material.logical_artifact_id) !=
                (self.record.object_schema, ArtifactProfile.CANONICAL_JSON, "application/json",
                    self.record.object_fingerprint, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE,
                    self.record.object_fingerprint, "none", logical.logical_artifact_id)
                or material.size_bytes < 1):
            raise ValueError("programme inputs require exact uncompressed blind canonical publication custody")

    def require_kind(self, kind):
        if (self.record.object_schema, self.record.object_version) != (kind.SCHEMA, kind.VERSION):
            raise ValueError("programme input substitutes its exact current scientific record edition")

    def require_record(self, record, identity):
        """Join a body after ordinary custody authentication, without creating authority."""
        self.require_kind(type(record))
        if (identity != self.record or record.fingerprint() != self.record.object_fingerprint
                or len(record.canonical_bytes()) != self.publication.materialization.size_bytes):
            raise ValueError("programme input changes its exact original identity or byte bound")

    @property
    def identity(self):
        """Identify the complete handle separately from its referenced record."""
        return ObjectIdentity.from_record('published-input.' + self.fingerprint(), self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeProducedInput(CanonicalRecord):
    """An actual produced record retaining its original publication access.

    This handle is neither a blind pre-TRAIN commitment nor permission to read
    protected bytes. The ordinary producing/consuming reader authenticates the
    original authority, complete lineage and current access separately.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/produced-input'
    record: ObjectIdentity
    publication: ArtifactWriteResult

    def __post_init__(self):
        if type(self.record) is not ObjectIdentity or type(self.publication) is not ArtifactWriteResult:
            raise TypeError('programme produced input requires its exact record and actual publication')
        self.record.__post_init__()
        self.publication.__post_init__()
        logical, material = self.publication.logical, self.publication.materialization
        if ((logical.payload_schema, logical.profile, logical.media_type, logical.content_sha256,
                material.physical_sha256, material.compression, material.logical_artifact_id) !=
                (self.record.object_schema, ArtifactProfile.CANONICAL_JSON, 'application/json',
                    self.record.object_fingerprint, self.record.object_fingerprint, 'none', logical.logical_artifact_id)
                or material.size_bytes < 1):
            raise ValueError('programme produced input changes exact uncompressed canonical custody')

    def require_kind(self, kind):
        if (self.record.object_schema, self.record.object_version) != (kind.SCHEMA, kind.VERSION):
            raise ValueError('programme produced input substitutes its exact current record edition')

    def require_record(self, record, identity):
        self.require_kind(type(record))
        if (identity != self.record or record.fingerprint() != self.record.object_fingerprint
                or len(record.canonical_bytes()) != self.publication.materialization.size_bytes):
            raise ValueError('programme produced input changes its original identity or byte bound')


@dataclass(frozen=True, slots=True)
class MatrixProgrammePhaseInputs(CanonicalRecord):
    """One role's original reservation, numerical selection and future panels."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-programme/phase-inputs"
    role: str
    reservation: MatrixProgrammePublishedInput
    native_specification: MatrixProgrammePublishedInput | None
    responses: MatrixProgrammePublishedInput | None

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1AllocationReservation
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation, ScheduledSpecification
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
        if self.role not in PHASE_INPUT_ROLES or type(self.reservation) is not MatrixProgrammePublishedInput:
            raise TypeError("programme inputs require their closed actual phase role and reservation")
        self.reservation.__post_init__()
        self.reservation.require_kind(E1AllocationReservation if self.role == "e1" else ScheduledReservation)
        if self.role == "e1":
            if self.native_specification is not None or self.responses is not None:
                raise ValueError("E1 commits full histories without invented response or prefix selections")
            return
        for value, kind in ((self.native_specification, ScheduledSpecification),
                (self.responses, ScheduledResponseSelection)):
            if type(value) is not MatrixProgrammePublishedInput:
                raise TypeError("programme inputs omit an actual pre-acquisition source or future selection")
            value.__post_init__()
            value.require_kind(kind)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeInputCommitments(CanonicalRecord):
    """Settled known inputs C; no fitted products, nominations or active phase."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-programme/input-commitments"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    namespace: str
    scientific_design: MatrixProgrammePublishedInput
    exposure_census: MatrixProgrammePublishedInput
    exposure_audit: MatrixProgrammePublishedInput
    producing_provenance: MatrixProgrammePublishedInput
    scalar_definitions: tuple[MatrixProgrammePublishedInput, ...]
    support_files: tuple[tuple[ArtifactIdentity, ArtifactWriteResult], ...]
    phases: tuple[MatrixProgrammePhaseInputs, ...]
    revision_folds: tuple[tuple[str, int], ...]
    availability: MatrixProgrammePublishedInput
    e6_policy: MatrixProgrammePublishedInput
    e4_streams: SelectedE4StreamRecipe

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_records import MatrixE6EmpiricalTransportPolicy
        from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit
        from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
        from empirical_lawhood.kernel.time import AvailabilitySpec
        from .scientific_design import MatrixProgrammeScientificDesign
        validate_stable_id(self.record_id)
        validate_stable_id(self.namespace)
        if type(self.e4_streams) is not SelectedE4StreamRecipe:
            raise TypeError('programme commitments require the original E4 history, future and family-draw recipe')
        self.e4_streams.__post_init__()
        for value, kind in ((self.scientific_design, MatrixProgrammeScientificDesign),
                (self.exposure_census, MatrixFactorExposureCensus), (self.exposure_audit, ScheduledExposureAudit),
                (self.producing_provenance, NumericalProducingProvenance), (self.availability, AvailabilitySpec),
                (self.e6_policy, MatrixE6EmpiricalTransportPolicy)):
            if type(value) is not MatrixProgrammePublishedInput:
                raise TypeError("programme commitments require actual design, census, availability and E6 policy publications")
            value.__post_init__()
            value.require_kind(kind)
        if (type(self.scalar_definitions) is not tuple or not self.scalar_definitions
                or any(type(value) is not MatrixProgrammePublishedInput for value in self.scalar_definitions)
                or tuple(value.record.object_id for value in self.scalar_definitions) !=
                    tuple(sorted({value.record.object_id for value in self.scalar_definitions}))):
            raise ValueError("programme commitments require each exact original typed scalar publication once")
        for value in self.scalar_definitions:
            value.__post_init__()
            value.require_kind(MatrixParameterScalarDefinition)
        if (type(self.support_files) is not tuple or not self.support_files
                or any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not ArtifactIdentity
                    or type(row[1]) is not ArtifactWriteResult for row in self.support_files)
                or tuple(artifact.artifact_id for artifact, _ in self.support_files) !=
                    tuple(sorted({artifact.artifact_id for artifact, _ in self.support_files}))):
            raise ValueError("programme commitments require their exact sorted original support FILE publications")
        for artifact, publication in self.support_files:
            from .retained_training_continuation import retained_source_types
            from .completed_source import MatrixCompletedE3InputSource
            artifact.__post_init__()
            publication.__post_init__()
            logical, material = publication.logical, publication.materialization
            retained = artifact.payload_schema in {kind.SCHEMA for kind in (*retained_source_types(), MatrixCompletedE3InputSource)}
            profile = ArtifactProfile.CANONICAL_JSON if retained else ArtifactProfile.RAW_SOURCE_BYTES
            if retained and artifact.media_type != 'application/json':
                raise ValueError('retained source lineage requires its exact canonical JSON publication')
            if ((artifact.artifact_id, artifact.payload_schema, artifact.sha256, artifact.media_type, artifact.size_bytes,
                    profile, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE,
                    artifact.sha256, "none") !=
                    (logical.logical_artifact_id, logical.payload_schema, logical.content_sha256, logical.media_type,
                        material.size_bytes, logical.profile, logical.outcome_access, logical.visibility_ceiling,
                        material.physical_sha256, material.compression)
                    or material.logical_artifact_id != logical.logical_artifact_id):
                raise ValueError("programme support changes its exact original blind FILE custody profile or bytes")
        if (type(self.phases) is not tuple or any(type(value) is not MatrixProgrammePhaseInputs for value in self.phases)
                or tuple(value.role for value in self.phases) != PHASE_INPUT_ROLES):
            raise ValueError("programme commitments omit or reorder the complete E1-E6 input-role census")
        for value in self.phases:
            value.__post_init__()
        if (type(self.revision_folds) is not tuple or not self.revision_folds
                or any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not str
                    or type(row[1]) is not int or row[1] < 0 for row in self.revision_folds)
                or tuple(group for group, _ in self.revision_folds) !=
                    tuple(sorted({group for group, _ in self.revision_folds}))):
            raise ValueError("programme commitments require one explicit original whole-group revision fold per DEV group")
        for group, _ in self.revision_folds:
            validate_stable_id(group)
        # An actual availability record has no intrinsic ID. Its exact logical
        # publication identity is the selected identity, as in the E6 owner.
        if self.availability.record.object_id != self.availability.publication.logical.logical_artifact_id:
            raise ValueError("programme commitments substitute the actual availability publication identity")
        # Repeated shared parents are legitimate. A physical path cannot name
        # two different records, and one record cannot have conflicting custody.
        by_path, by_identity = {}, {}
        for value in self.publications():
            path = value.publication.materialization.relative_path
            if (by_path.setdefault(path, value) != value
                    or by_identity.setdefault(value.record, value.publication) != value.publication):
                raise ValueError("programme commitments alias different originals through shared publication custody")
        raw_by_path = {}
        for artifact, publication in self.support_files:
            path = publication.materialization.relative_path
            if path in by_path or raw_by_path.setdefault(path, (artifact, publication)) != (artifact, publication):
                raise ValueError("programme raw FILE aliases a different original input publication")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def phase(self, role):
        for value in self.phases:
            if value.role == role:
                return value
        raise ValueError("unknown committed programme input role: " + str(role))

    def publications(self):
        yield self.scientific_design
        yield self.exposure_census
        yield self.exposure_audit
        yield self.producing_provenance
        yield from self.scalar_definitions
        for phase in self.phases:
            yield phase.reservation
            if phase.native_specification is not None:
                yield phase.native_specification
            if phase.responses is not None:
                yield phase.responses
        yield self.availability
        yield self.e6_policy
