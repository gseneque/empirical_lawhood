# SPDX-License-Identifier: MPL-2.0
"""One staging call's accepted payload format, separate from byte custody."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.recursive_storage_codecs import resolve_storage_codec

from .artifact_validation import ArtifactProfileValidatorRegistry, stock_payload_validation_policy

_selected = ContextVar('publication_payload_validation', default=None)


def _policy(plane, request):
    from .artifacts import ExternalArtifactPlane, _has_stock_artifact_plane_state, _STOCK_PREPARE_METHOD

    if (type(plane) is not ExternalArtifactPlane or not _has_stock_artifact_plane_state(plane)
            or type(plane)._prepare is not _STOCK_PREPARE_METHOD
            or type(request) is not ArtifactWriteRequest or type(request.payload) is not bytes
            or type(plane.validators) is not ArtifactProfileValidatorRegistry
            or request.profile not in plane.validators.enabled_profiles
            or request.profile is not ArtifactProfile.CANONICAL_JSON
            or request.compression != 'none' or request.partition_selector is not None
            or not stock_payload_validation_policy()
            or resolve_storage_codec(plane.validators.binary_codecs, payload_schema=request.payload_schema,
                profile=request.profile, media_type=request.media_type) is not None):
        return None
    return (plane.validators, plane.validators.enabled_profiles, plane.custody_limits, request.profile, request.payload_schema,
        request.media_type, request.semantic_validation, request.compression, request.partition_selector)


@dataclass(slots=True)
class _PayloadFormatProof:
    plane: object
    request: object
    policy: object
    accepted: tuple | None = None
    active: bool = True

    def require_same_bytes_and_policy(self, size, digest):
        return (self.active and self.policy is not None and self.accepted == (size, digest)
            and _policy(self.plane, self.request) == self.policy)


@contextmanager
def capture_payload_validation(plane, request):
    """A producer-local proof; it cannot escape staging or authorize a write."""
    proof = _PayloadFormatProof(plane, request, _policy(plane, request))
    token = _selected.set(proof)
    try:
        yield proof
    finally:
        proof.active = False
        proof.accepted = None
        _selected.reset(token)


def remember_payload_validation(plane, request, *, size, digest):
    """Called only after the ordinary in-memory validator actually succeeds."""
    proof = _selected.get()
    if (proof is not None and proof.active and proof.plane is plane and proof.request is request
            and proof.policy is not None and _policy(plane, request) == proof.policy):
        proof.accepted = (size, digest)
