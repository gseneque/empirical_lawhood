# SPDX-License-Identifier: MPL-2.0
"""Concrete future-source metadata and its exact finite identity transform.

Rows declare assigned pending native acquisitions. They never assert valid
future outcomes. Materialization validation is distinct from instrument and
sampling qualification.
"""
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as phase
from empirical_lawhood.kernel.authority import ResourceBudget, SourceAccessClass
from empirical_lawhood.kernel.evidence import EvidenceCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactManifest
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityManifest, CapabilityPermission
from empirical_lawhood.runtime.sources import SourceCapabilityManifest, SourceMode
from .matrix_finite_dt_source_records import BLIND, NAMESPACE, pin


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtPendingSourceRow(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-source/finite-dt-pending-source-row"
    root_id: str
    group_id: str
    source: ObjectIdentity
    invalid_disposition: str = "ASSIGNED_NATIVE_ACQUISITION_NOT_YET_OBSERVED"
    requested_action_status: str = "NO_NATIVE_ACTION_REQUESTED"
    receiver_status: str = "NO_NATIVE_RECEIVER_OBSERVED"

    def __post_init__(self):
        validate_stable_id(self.root_id)
        validate_stable_id(self.group_id)
        if (self.invalid_disposition != "ASSIGNED_NATIVE_ACQUISITION_NOT_YET_OBSERVED"
                or self.requested_action_status != "NO_NATIVE_ACTION_REQUESTED"
                or self.receiver_status != "NO_NATIVE_RECEIVER_OBSERVED"):
            raise ValueError("finite-dt source metadata cannot predict a future outcome or hide nonuse")


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtPendingSourceRows(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-source/finite-dt-pending-source-rows"
    record_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    rows: tuple[MatrixFiniteDtPendingSourceRow, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        require_sorted_unique_ids(self.rows, attribute="root_id", field_name="complete pending acquisition roster")
        if not self.rows or any(type(value) is not MatrixFiniteDtPendingSourceRow for value in self.rows):
            raise ValueError("finite-dt source requires every assigned future source")
        for value in self.rows:
            value.__post_init__()

    @property
    def identity(self):
        return pin(self)

    @classmethod
    def from_bank(cls, programme, bank, *, record_id):
        phase.validate_selected_phase_bank(programme, bank)
        return cls(record_id, programme.identity, bank.identity, tuple(MatrixFiniteDtPendingSourceRow(
            value.root_id, value.independent_group_id, value.source) for value in programme.cases))


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtSourceValidationRule(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-source/finite-dt-source-validation-rule"
    record_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    rows: ObjectIdentity
    operation: str = "EXACT_CANONICAL_IDENTITY_TRANSFORM_COMPLETE_ASSIGNED_PENDING_SOURCES"

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.programme.object_schema != phase.SelectedE4PhaseProgramme.SCHEMA
                or self.bank.object_schema != phase.SelectedE4PhaseBank.SCHEMA
                or self.rows.object_schema != MatrixFiniteDtPendingSourceRows.SCHEMA
                or self.operation != "EXACT_CANONICAL_IDENTITY_TRANSFORM_COMPLETE_ASSIGNED_PENDING_SOURCES"):
            raise ValueError("finite-dt source cannot select an arbitrary transform or semantic validator")

    @property
    def identity(self):
        return pin(self)


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtSourceVerification(CanonicalRecord):
    """Actual bounded-byte comparison by the source owner, never a task receipt."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-source/finite-dt-source-verification"
    record_id: str
    rule: ObjectIdentity
    source_manifest: ObjectIdentity
    output_manifest: ObjectIdentity
    rows: ObjectIdentity
    row_count: int
    physical_unit_count: int
    operation: str = "BOTH_COMMITTED_MANIFESTS_VERIFIED_CANONICAL_BYTES_EQUAL_COMPLETE_TYPED_SOURCE_ROSTER"

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.rule.object_schema != MatrixFiniteDtSourceValidationRule.SCHEMA
                or self.source_manifest.object_schema != ArtifactManifest.SCHEMA
                or self.output_manifest.object_schema != ArtifactManifest.SCHEMA
                or self.rows.object_schema != MatrixFiniteDtPendingSourceRows.SCHEMA
                or type(self.row_count) is not int or self.row_count < 1
                or type(self.physical_unit_count) is not int or self.physical_unit_count < 1
                or self.row_count < self.physical_unit_count
                or self.operation != "BOTH_COMMITTED_MANIFESTS_VERIFIED_CANONICAL_BYTES_EQUAL_COMPLETE_TYPED_SOURCE_ROSTER"):
            raise ValueError("finite-dt source verification loses actual bounded publication and complete rows")

    @property
    def identity(self):
        return pin(self)


def validate_source_rows(programme, bank, rows, rule):
    """Replay the sole implemented transform before source or output effects."""
    if (type(rows) is not MatrixFiniteDtPendingSourceRows or type(rule) is not MatrixFiniteDtSourceValidationRule
            or rows != MatrixFiniteDtPendingSourceRows.from_bank(programme, bank, record_id=rows.record_id)
            or (rule.programme, rule.bank, rule.rows) != (programme.identity, bank.identity, rows.identity)):
        raise ValueError("finite-dt identity transform changes complete current source/group/pending-state census")


SOURCE_KEY = NAMESPACE + ".pending-source"
TRANSFORM_KEY = NAMESPACE + ".identity-transform"
FORMAT_ID = "matrix-finite-dt-complete-pending-source-roster"


def source_capability(resources):
    if type(resources) is not ResourceBudget:
        raise TypeError("finite-dt source registration needs explicit resources")
    resources.__post_init__()
    return SourceCapabilityManifest(SOURCE_KEY, "1.0.0", SourceMode.SIMULATED, SourceAccessClass.NONE,
        (MatrixFiniteDtPendingSourceRows.SCHEMA,), EvidenceCeiling.MEASUREMENT, BLIND, True,
        sha256((SOURCE_KEY + ".guarded-published-canonical-roster.v1").encode()).hexdigest(), resources)


def transform_capability(resources):
    if type(resources) is not ResourceBudget:
        raise TypeError("finite-dt identity transform needs explicit resources")
    resources.__post_init__()
    return CapabilityManifest(TRANSFORM_KEY, "1.0.0", CapabilityKind.TRANSFORM,
        MatrixFiniteDtSourceValidationRule.SCHEMA, sha256(MatrixFiniteDtSourceValidationRule.SCHEMA.encode()).hexdigest(),
        (MatrixFiniteDtPendingSourceRows.SCHEMA,), (MatrixFiniteDtPendingSourceRows.SCHEMA,),
        (CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS),
        EvidenceCeiling.MEASUREMENT, BLIND, resources, True, False, "python", "python-current", False, True, False,
        ("finite-dt-complete-pending-roster-canonical-identity",),
        sha256((TRANSFORM_KEY + ".complete-canonical-no-thinning.v1").encode()).hexdigest())


def metadata_records_for(scope, pipeline):
    """Otherwise-nested canonical metadata required by the existing source owner.

    Task configs and shared operands retain their actual provider-input custody;
    this census never duplicates them or creates a scientific receipt.
    """
    from .matrix_finite_dt_source_records import qualification_specification
    if scope.profile != pipeline.profile or scope.pipeline_receipt != pipeline.assess():
        raise ValueError("finite-dt metadata changes its actual original source pipeline")
    publication = pipeline.execution_evidence.output_manifest.publication
    if publication is None:
        raise ValueError("finite-dt metadata requires its actual atomic source publication")
    values = ((scope.profile, "profile_id"), (scope.evidence_profile, "selection_id"),
        (qualification_specification(scope), "spec_id"), (publication, "publication_batch_id"))
    return tuple(sorted(((pin(value, field), value) for value, field in values), key=lambda row: row[0].object_id))
