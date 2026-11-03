# SPDX-License-Identifier: MPL-2.0
"""Code-owned exact binary contracts for recursive operations and custody.

These operational declarations do not change logical evidence identity. A codec
establishes physical structure; its domain consumer still establishes scientific
meaning, complete members and compatibility.
"""

from dataclasses import dataclass
from types import FunctionType
from typing import Callable

from empirical_lawhood.kernel.serialization import (
    validate_schema, validate_semantic_version, validate_stable_id,
)
from .artifacts import ArtifactProfile


@dataclass(frozen=True, slots=True)
class RecursiveStorageCodec:
    codec_id: str
    payload_schema: str
    record_version: str
    profile: ArtifactProfile
    media_type: str
    filename_suffix: str
    validate_stream: Callable
    maximum_bytes: int | None = None

    def __post_init__(self):
        validate_stable_id(self.codec_id)
        validate_schema(self.payload_schema)
        validate_semantic_version(self.record_version)
        if (type(self.profile) is not ArtifactProfile or self.profile is ArtifactProfile.CANONICAL_JSON
                or type(self.media_type) is not str or not self.media_type
                or type(self.filename_suffix) is not str or not self.filename_suffix.startswith('.')
                or not self.filename_suffix[1:].isalnum()
                or type(self.validate_stream) is not FunctionType
                or self.maximum_bytes is not None and (type(self.maximum_bytes) is not int or self.maximum_bytes <= 0)):
            raise ValueError('storage codec needs an exact binary contract and code-owned stream validator')

    @property
    def key(self):
        return self.payload_schema, self.profile, self.media_type


def validate_storage_codecs(codecs):
    if (type(codecs) is not tuple or any(type(codec) is not RecursiveStorageCodec for codec in codecs)
            or tuple(codec.codec_id for codec in codecs) != tuple(sorted({codec.codec_id for codec in codecs}))
            or len({codec.key for codec in codecs}) != len(codecs)):
        raise ValueError('storage codecs need sorted unique exact code-owned declarations')
    return codecs


def storage_codec_census(registrations):
    """Collect explicit operation contracts, refusing conflicting declarations."""
    by_id, by_key = {}, {}
    for registration in registrations:
        for codec in validate_storage_codecs(registration.storage_codecs):
            if by_id.setdefault(codec.codec_id, codec) != codec or by_key.setdefault(codec.key, codec) != codec:
                raise ValueError('registered operations disagree on an exact storage codec')
    return tuple(by_id[key] for key in sorted(by_id))


def resolve_storage_codec(codecs, *, payload_schema, profile=None, media_type=None, record_version=None):
    """Resolve a closed installed contract; record values cannot import a codec."""
    validate_storage_codecs(codecs)
    if (type(payload_schema) is not str or (profile is not None and type(profile) is not ArtifactProfile)
            or (media_type is not None and (type(media_type) is not str or not media_type))
            or (record_version is not None and type(record_version) is not str)):
        raise ValueError('storage codec selection needs exact typed schema/profile/media/version fields')
    validate_schema(payload_schema)
    if record_version is not None:
        validate_semantic_version(record_version)
    matches = tuple(codec for codec in codecs if codec.payload_schema == payload_schema
                    and (profile is None or codec.profile is profile)
                    and (media_type is None or codec.media_type == media_type)
                    and (record_version is None or codec.record_version == record_version))
    if len(matches) > 1:
        raise ValueError('storage codec selection is ambiguous without its exact physical contract')
    return matches[0] if matches else None
