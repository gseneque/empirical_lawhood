# SPDX-License-Identifier: MPL-2.0
"""Read-only native BEGIN input validation, also usable before parent contact.

This authenticates available operands. It neither writes progress nor grants
execution, recovery, scientific qualification or authority.
"""

from hashlib import sha256
import json
import os

from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactPlaneError
from empirical_lawhood.infrastructure.bounded_io import (
    BoundedFileIOError, CONTROL_PLANE_CHUNK_BYTES, _open_regular,
    _stable_descriptor, read_bounded_bytes,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkDefinition, NativeSubworkInputError, NativeSubworkInputMismatch,
)


def verify_native_record_envelope(plane, manifest, identity):
    """Check exact record version and hash with bounded descriptor memory."""
    encode = lambda value: json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode()
    prefix = b'{"schema":' + encode(identity.object_schema) + b',"value":'
    suffix = b',"version":' + encode(identity.object_version) + b'}\n'
    path = plane.root.resolve(manifest.materialization.relative_path, for_write=False)
    descriptor, before = _open_regular(path, maximum_bytes=manifest.materialization.size_bytes)
    with _stable_descriptor(descriptor, before, operation="native input identity verification"):
        if before.st_size < len(prefix) + len(suffix) or os.read(descriptor, len(prefix)) != prefix:
            raise ValueError("native subwork source does not carry its exact canonical record envelope")
        os.lseek(descriptor, -len(suffix), os.SEEK_END)
        if os.read(descriptor, len(suffix)) != suffix:
            raise ValueError("native subwork substitutes its source/config/stream record version")
        os.lseek(descriptor, 0, os.SEEK_SET)
        digest, count = sha256(), 0
        while count < before.st_size:
            chunk = os.read(descriptor, min(CONTROL_PLANE_CHUNK_BYTES, before.st_size - count))
            if not chunk:
                raise BoundedFileIOError("native subwork input was truncated during identity verification")
            count += len(chunk)
            digest.update(chunk)
        if os.read(descriptor, 1) or digest.hexdigest() != identity.object_fingerprint:
            raise ValueError("native subwork record bytes changed during exact identity verification")


def validate_native_subwork_inputs(
    plane: ExternalArtifactPlane,
    definition: NativeSubworkDefinition,
    inputs: tuple[ArtifactManifest, ...],
    *,
    visibility: VisibilityCeiling,
    access: OutcomeAccess,
    frozen_parent_inputs: tuple[ArtifactManifest, ...] | None = None,
) -> None:
    """Run the same full input/source contract before preparation and BEGIN.

The definition may name a prospective parent. Authenticating its actual live
creator and selected roster remains the progress store's responsibility.
Only metadata and the bounded producing-provenance record are retained.
"""
    definition.__post_init__()
    problems = []

    def mismatch(operand_id, reason):
        problems.append(NativeSubworkInputMismatch(operand_id, reason))

    frozen_by_id = {}
    if frozen_parent_inputs is not None:
        if (type(frozen_parent_inputs) is not tuple
                or any(type(value) is not ArtifactManifest for value in frozen_parent_inputs)):
            raise TypeError("native subwork requires typed frozen parent input manifests")
        frozen_ids = tuple(sorted(value.materialization.materialization_id
            for value in frozen_parent_inputs))
        if frozen_ids != definition.parent_contact.input_materialization_ids:
            mismatch(definition.subwork_id,
                "native subwork frozen input boundaries differ from its complete parent census")
        for value in frozen_parent_inputs:
            key = value.materialization.materialization_id
            if key in frozen_by_id:
                mismatch(key, "native subwork frozen input boundary is ambiguous")
            frozen_by_id[key] = value

    actual_ids = tuple(sorted(m.materialization.materialization_id for m in inputs))
    if actual_ids != definition.input_materialization_ids:
        mismatch(definition.subwork_id, "native subwork changes its complete input materialization census")
        for value in sorted(set(definition.input_materialization_ids) - set(actual_ids)):
            mismatch(value, "declared input materialization is missing")
        for value in sorted(set(actual_ids) - set(definition.input_materialization_ids)):
            mismatch(value, "input materialization is undeclared")
    for manifest in inputs:
        operand_id = manifest.materialization.materialization_id
        try:
            plane.verify_manifest(manifest)
        except (ValueError, OSError, BoundedFileIOError, ArtifactPlaneError) as error:
            mismatch(operand_id, str(error))
        frozen = frozen_by_id.get(operand_id)
        if frozen is not None:
            # The ordinary executor already qualified this exact input, and
            # the progress coordinator checked its actual worker binding.
            # Its input scope need not equal the later task's output scope.
            if manifest != frozen:
                mismatch(operand_id, "native subwork input substitutes its frozen parent boundary")
        elif (manifest.logical.visibility_ceiling is not visibility
                or manifest.logical.outcome_access is not access):
            # Explicit conditional operands retain the existing parent scope.
            # A missing held boundary never grants a different access role.
            mismatch(operand_id, "native subwork input changes its access boundary")
    for identity in (definition.configuration, *definition.sources, *definition.streams):
        matches = tuple(manifest for manifest in inputs
            if (manifest.logical.payload_schema, manifest.logical.content_sha256)
            == (identity.object_schema, identity.object_fingerprint))
        if not matches:
            mismatch(identity.object_id, "native subwork config/source/stream lacks authenticated input bytes")
        elif matches[0].logical.profile is ArtifactProfile.CANONICAL_JSON:
            try:
                verify_native_record_envelope(plane, matches[0], identity)
            except (ValueError, OSError, BoundedFileIOError, ArtifactPlaneError) as error:
                mismatch(identity.object_id, str(error))
    provenance_sources = tuple(identity for identity in definition.sources
        if identity.object_schema == NumericalProducingProvenance.SCHEMA)
    if len(provenance_sources) != 1:
        mismatch(definition.subwork_id, "native subwork requires its exact authenticated producing provenance")
    else:
        provenance_identity = provenance_sources[0]
        candidates = tuple(manifest for manifest in inputs
            if (manifest.logical.payload_schema, manifest.logical.content_sha256)
            == (provenance_identity.object_schema, provenance_identity.object_fingerprint))
        if len(candidates) != 1:
            mismatch(provenance_identity.object_id, "native subwork producing provenance is ambiguous")
        else:
            manifest = candidates[0]
            if plane.custody_limits.exceeds("control_record_bytes", manifest.materialization.size_bytes):
                mismatch(provenance_identity.object_id,
                    "native subwork producing provenance exceeds its selected metadata allowance")
            else:
                try:
                    provenance = decode_canonical_bytes(read_bounded_bytes(plane.root.resolve(
                        manifest.materialization.relative_path, for_write=False),
                        maximum_bytes=manifest.materialization.size_bytes), NumericalProducingProvenance,
                        maximum_bytes=manifest.materialization.size_bytes)
                    for actual, selected, operand in (
                            (provenance.identity, provenance_identity, "provenance identity"),
                            (provenance.code_sources_sha256, definition.code_sources_sha256, "code source"),
                            (provenance.dependency_lock_sha256, definition.dependency_lock_sha256, "dependency lock"),
                            (provenance.observed_git_head, definition.parent_contact.implementation_commit, "Git source")):
                        if actual != selected:
                            mismatch(provenance_identity.object_id,
                                "native subwork substitutes its actual producing source or dependency lock: " + operand)
                except (ValueError, OSError, BoundedFileIOError, ArtifactPlaneError) as error:
                    mismatch(provenance_identity.object_id, str(error))
    if problems:
        raise NativeSubworkInputError(tuple(problems))
