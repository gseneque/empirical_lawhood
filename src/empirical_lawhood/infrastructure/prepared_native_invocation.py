# SPDX-License-Identifier: MPL-2.0
"""Explicit native input publication and authenticated preparation.

Scientific identities come from selected records/operands. The existing guarded
artifact plane owns their bytes and ports; this helper owns no execution effects.
"""

from dataclasses import dataclass

from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.native_subwork_inputs import (
    NativeSubworkInputError, validate_native_subwork_inputs, verify_native_record_envelope,
)
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeInput, PreparedNativeInvocation


@dataclass(frozen=True, slots=True)
class NativeInputPublication:
    """One record and optional transport alias; historical identity is retained."""

    object_id: str
    record: CanonicalRecord
    artifact_id: str | None = None
    lineage_parents: tuple[ArtifactLineageParent, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.object_id, field_name="object_id")
        if self.artifact_id is not None:
            validate_stable_id(self.artifact_id, field_name="artifact_id")
        if not isinstance(self.record, CanonicalRecord):
            raise ValueError("native publication requires its selected canonical record")
        self.record.canonical_bytes()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.object_id, self.record)

    def request(self, *, relative_root, publication_scope_id, visibility, access,
                minimum_free_bytes=0, relative_path=None):
        identity = self.identity
        artifact_id = self.artifact_id or identity.object_id
        return ArtifactWriteRequest(artifact_id, relative_path or relative_root + "/" + artifact_id + ".json",
            identity.object_schema, ArtifactProfile.CANONICAL_JSON, "application/json",
            publication_scope_id, relative_root, self.record.canonical_bytes(), visibility,
            tuple(parent.visibility_ceiling for parent in self.lineage_parents), access,
            lineage_parents=self.lineage_parents, minimum_free_bytes=minimum_free_bytes)


def prepare_native_invocation(plane, *, publications=(), existing_inputs=(),
                              relative_root="inputs", publication_scope_id="selected.inputs",
                              visibility, access, minimum_free_bytes=0):
    """Publish selected controls and join every available identity/manifest/port.

Existing inputs are explicit ``(ObjectIdentity, ArtifactManifest)`` pairs, such
as a conditional parent's authenticated outputs. Their source/storage ownership
is checked by the existing plane instead of being inferred from a string ID.
All opened ports are closed on refusal; successful callers own their lifetime.
"""
    publications = tuple(publications)
    requests = tuple(value.request(relative_root=relative_root,
        publication_scope_id=publication_scope_id, visibility=visibility, access=access,
        minimum_free_bytes=minimum_free_bytes) for value in publications)
    selected = list(existing_inputs)
    if requests:
        results = plane.write_batch(requests)
        for publication, result in zip(publications, results, strict=True):
            manifest_path = plane.root.resolve(result.materialization.relative_path + ".manifest.json",
                for_write=False)
            manifest = decode_artifact_manifest(read_bounded_bytes(manifest_path,
                maximum_bytes=plane.custody_limits.manifest_bytes),
                maximum_bytes=plane.custody_limits.manifest_bytes)
            selected.append((publication.identity, manifest))
    selected.sort(key=lambda value: value[1].logical.logical_artifact_id)
    for identity, manifest in selected:
        plane.verify_manifest(manifest)
        if (manifest.logical.visibility_ceiling is not visibility
                or manifest.logical.outcome_access is not access):
            raise ValueError("prepared native input changes its selected access boundary")
        if manifest.logical.profile is ArtifactProfile.CANONICAL_JSON:
            verify_native_record_envelope(plane, manifest, identity)
    verified = tuple(VerifiedArtifactInput(manifest.logical, manifest.materialization)
        for _, manifest in selected)
    bindings = tuple(WorkerInputBinding.from_verified(value, kind=WorkerInputKind.EXTERNAL)
        for value in verified)
    ports = plane.open_many(verified, bindings=bindings, maximum_bytes=None)
    try:
        return PreparedNativeInvocation(tuple(PreparedNativeInput(identity, manifest, port)
            for (identity, manifest), port in zip(selected, ports, strict=True)))
    except Exception:
        for port in ports:
            port.close()
        raise


def validate_prepared_native_invocation(plane, prepared, definitions, *, visibility, access):
    """Retain mismatches for every available definition before parent contact."""
    prepared.__post_init__()
    mismatches = []
    for definition in definitions:
        try:
            validate_native_subwork_inputs(plane, definition, prepared.manifests,
                visibility=visibility, access=access)
        except NativeSubworkInputError as error:
            mismatches.extend(error.mismatches)
    if mismatches:
        raise NativeSubworkInputError(tuple(mismatches))
