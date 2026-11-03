# SPDX-License-Identifier: MPL-2.0
"""Exact configured response selection, with unchanged original physical inputs."""
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol, ScheduledResponsePanel
from .configured_protected_specification import ConfiguredProtectedE3Specification as MatrixResponseErrorSpecification
from .protected_source_records import ProtectedE3NativeSourceManifest, _reference

@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3ResponseSelection(CanonicalRecord):
    """Exact references; canonical protocol/panel members are separate inputs."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-response-selection"
    record_id: str
    specification: ObjectIdentity
    source_manifest: ObjectIdentity
    root_protocols: tuple[tuple[str, ObjectIdentity], ...]
    group_panels: tuple[tuple[str, tuple[ObjectIdentity, ...]], ...]
    template_publications: tuple[ArtifactWriteResult, ...]
    protocol_projections: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        from .configured_protected_protocol import ConfiguredProtectedE3ProtocolProjection
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
            _reference(reference, ConfiguredProtectedE3ProtocolProjection)
