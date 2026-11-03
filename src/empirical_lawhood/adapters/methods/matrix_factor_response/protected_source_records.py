# SPDX-License-Identifier: MPL-2.0
"""Compact original E3 sources and reference-only response selections.

These are uninstalled scientific operands. Byte/publication consistency does
not authenticate custody, chronology, source eligibility, issue or execution.
The source manifest owns the original allocation exactly once, through its
reservation. Predictor inputs must not contain this manifest or its streams.
"""

from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ResolvedScheduledSource, ScheduledSourceIndex
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import (
    ScheduledReservation, ScheduledSpecification, _publication, identity as source_identity,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel, ScheduledResponseProtocol
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult

from .experiment_specification import MatrixResponseErrorSpecification

NAMESPACE = "matrix-e3-protected"


def identity(record: CanonicalRecord) -> ObjectIdentity:
    return ObjectIdentity.from_record(record.record_id, record)


def _reference(reference, kind):
    if (type(reference) is not ObjectIdentity
            or (reference.object_schema, reference.object_version) != (kind.SCHEMA, kind.VERSION)):
        raise ValueError("protected E3 substitutes an exact scientific type or revision")
    reference.__post_init__()


def _selected(specification):
    if type(specification) is not MatrixResponseErrorSpecification:
        raise TypeError("protected E3 requires its exact selected specification")
    specification.__post_init__()
    if (specification.evidence_scope != "PROSPECTIVE_REQUIRED"
            or specification.calibration_target_view != "MAX_PAIRED_VIEWS"):
        raise ValueError("protected E3 changes its selected paired-view scientific scope")


@dataclass(frozen=True, slots=True)
class ProtectedE3NativeSourceManifest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-native-source-manifest"
    record_id: str
    reservation: ScheduledReservation
    native_specification: ScheduledSpecification
    provenances: tuple[NumericalProducingProvenance, ...]
    audit: ScheduledExposureAudit
    audit_publication: ArtifactWriteResult
    reservation_publication: ArtifactWriteResult
    scalar_definition: MatrixParameterScalarDefinition
    scalar_definition_publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.reservation, ScheduledReservation),
                (self.native_specification, ScheduledSpecification), (self.audit, ScheduledExposureAudit),
                (self.scalar_definition, MatrixParameterScalarDefinition)):
            if type(value) is not kind:
                raise TypeError("protected E3 manifest requires exact original source records")
            value.__post_init__()
        self.reservation.allocation.__post_init__()
        if (type(self.provenances) is not tuple or not self.provenances
                or any(type(row) is not NumericalProducingProvenance for row in self.provenances)
                or tuple(row.fingerprint() for row in self.provenances) !=
                   tuple(sorted({row.fingerprint() for row in self.provenances}))
                or self.native_specification.selection.reservation != source_identity(self.reservation)):
            raise ValueError("protected E3 manifest aliases provenance or substitutes original reservation")
        for row in self.provenances:
            row.__post_init__()
        for publication, record in ((self.audit_publication, self.audit),
                (self.reservation_publication, self.reservation),
                (self.scalar_definition_publication, self.scalar_definition)):
            if type(publication) is not ArtifactWriteResult:
                raise TypeError("protected E3 manifest requires exact original publications")
            _publication(publication, record)
        exposure = self.reservation.allocation.exposure
        if (self.audit.census != exposure.census
                or self.audit.prior_scheduled_coordinates != exposure.prior_scheduled_coordinates
                or (exposure.scheduled_audit.payload_schema, exposure.scheduled_audit.media_type, exposure.scheduled_audit.sha256,
                    exposure.scheduled_audit.size_bytes) !=
                   (self.audit.SCHEMA, self.audit_publication.logical.media_type,
                    self.audit.fingerprint(), len(self.audit.canonical_bytes()))
                or self.audit_publication.logical.logical_artifact_id != exposure.scheduled_audit.artifact_id):
            raise ValueError("protected E3 manifest substitutes original exposure audit publication")
        publication = self.scalar_definition_publication
        for policy in self.native_specification.selection.prefix_policies:
            owner = policy.factor_rule.scalar_closure.normalization_owner
            if (owner.artifact_id, owner.payload_schema, owner.sha256, owner.media_type, owner.size_bytes) != (
                    publication.logical.logical_artifact_id, self.scalar_definition.SCHEMA,
                    self.scalar_definition.fingerprint(), "application/json", len(self.scalar_definition.canonical_bytes())):
                raise ValueError("protected E3 prefix scalar owner differs from actual typed definition publication")


class ProtectedE3SourcePhase(StrEnum):
    PREFIX = "prefix"
    NUMERICAL = "numerical"
    MEASURE = "measure"
    CHECK = "check"
    PROJECT = "project"


def source_task_id(root_id: str, phase: ProtectedE3SourcePhase) -> str:
    validate_stable_id(root_id)
    if type(phase) is not ProtectedE3SourcePhase:
        raise TypeError("protected E3 source task requires its closed phase")
    return NAMESPACE + "." + root_id + "." + phase.value


def prefix_native_operation_id() -> str:
    return NAMESPACE + ".prefix-before-continuation.v1"


@dataclass(frozen=True, slots=True)
class ProtectedE3SourceConfig(CanonicalRecord):
    """Native/source phases only; contains one root's actual four streams."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-source-config"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    phase: ProtectedE3SourcePhase
    specification: ObjectIdentity
    source_manifest: ObjectIdentity
    source: ScheduledSource

    def __post_init__(self):
        _reference(self.specification, MatrixResponseErrorSpecification)
        _reference(self.source_manifest, ProtectedE3NativeSourceManifest)
        if type(self.source) is not ScheduledSource:
            raise TypeError("protected E3 config requires an exact compact original source")
        self.source.__post_init__()
        if (self.source.root.root.role not in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION)
                or self.record_id != "config." + source_task_id(self.source.root_id, self.phase)):
            raise ValueError("protected E3 config changes its declaration-owned root/phase identity")


def bind_protected_e3_source(config: ProtectedE3SourceConfig, manifest: ProtectedE3NativeSourceManifest,
        *, specification: MatrixResponseErrorSpecification) -> ResolvedScheduledSource:
    """Resolve the bounded source against its exact shared scientific parents.

    The complete candidate/role projection is a separate root validation. This
    local join establishes exact supplied originals, not their qualification.
    """
    _selected(specification)
    if type(config) is not ProtectedE3SourceConfig or type(manifest) is not ProtectedE3NativeSourceManifest:
        raise TypeError("protected E3 source binding requires exact compact config and manifest")
    config.__post_init__()
    manifest.__post_init__()
    if config.specification != specification.identity or config.source_manifest != identity(manifest):
        raise ValueError("protected E3 source binding changes selected specification or shared manifest")
    index = ScheduledSourceIndex.from_shared(reservation=manifest.reservation,
        specification=manifest.native_specification, provenances=manifest.provenances)
    return index.resolve(config.source)


@dataclass(frozen=True, slots=True)
class ProtectedE3ResponseSelection(CanonicalRecord):
    """Exact references; canonical protocol/panel members are separate inputs."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-response-selection"
    record_id: str
    specification: ObjectIdentity
    source_manifest: ObjectIdentity
    root_protocols: tuple[tuple[str, ObjectIdentity], ...]
    group_panels: tuple[tuple[str, tuple[ObjectIdentity, ...]], ...]
    template_publications: tuple[ArtifactWriteResult, ...]
    protocol_projections: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        from .protected_protocol import ProtectedE3ProtocolProjection
        validate_stable_id(self.record_id)
        _reference(self.specification, MatrixResponseErrorSpecification)
        _reference(self.source_manifest, ProtectedE3NativeSourceManifest)
        for rows in (self.root_protocols, self.group_panels):
            if (type(rows) is not tuple or not rows
                    or tuple(row[0] for row in rows) != tuple(sorted({row[0] for row in rows}))):
                raise ValueError("protected E3 response selection aliases or empties its complete census")
            for key, _ in rows:
                validate_stable_id(key)
        for _, reference in self.root_protocols:
            _reference(reference, ScheduledResponseProtocol)
        if len({reference.object_id for _, reference in self.root_protocols}) != len(self.root_protocols):
            raise ValueError("protected E3 response selection aliases protocol identities across roots")
        for _, panels in self.group_panels:
            if type(panels) is not tuple or len(panels) != 2 or tuple(p.object_id for p in panels) != tuple(sorted({p.object_id for p in panels})):
                raise ValueError("protected E3 response selection requires both distinct declared panels")
            for reference in panels:
                _reference(reference, ScheduledResponsePanel)
        panel_ids = tuple(reference.object_id for _, panels in self.group_panels for reference in panels)
        if len(set(panel_ids)) != len(panel_ids):
            raise ValueError("protected E3 response selection aliases panel identities across groups")
        if (type(self.template_publications) is not tuple or not self.template_publications
                or any(type(p) is not ArtifactWriteResult for p in self.template_publications)
                or tuple(p.logical.logical_artifact_id for p in self.template_publications) !=
                   tuple(sorted({p.logical.logical_artifact_id for p in self.template_publications}))
                or type(self.protocol_projections) is not tuple or not self.protocol_projections
                or tuple(p.object_id for p in self.protocol_projections) != tuple(sorted({p.object_id for p in self.protocol_projections}))):
            raise ValueError("protected E3 response selection aliases or omits publications/projections")
        for reference in self.protocol_projections:
            _reference(reference, ProtectedE3ProtocolProjection)
