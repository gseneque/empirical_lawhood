"""Small closed registries for bounded canonical scientific-record codecs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar, TypeVar

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.serialization import CanonicalRecord, CanonicalizationError, require_sorted_unique_ids, validate_schema, validate_semantic_version, validate_sha256, validate_stable_id
from empirical_lawhood.storage.contracts.record_codecs import AmbiguousRecordRevision, RecordCodecCatalog, record_envelope_key, resolve_record_codec


RecordT = TypeVar("RecordT", bound=CanonicalRecord)
MAX_STATIC_CODEC_REGISTRATIONS = 256


@dataclass(frozen=True, slots=True)
class CanonicalRecordCodecRegistration(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/canonical-record-codec-registration'

    codec_id: str
    record_schema: str
    record_version: str
    maximum_bytes: int | None
    decoder_key: str
    decoder_version: str
    decoder_implementation_sha256: str

    def __post_init__(self) -> None:
        validate_stable_id(self.codec_id, field_name="codec_id")
        validate_schema(self.record_schema)
        validate_semantic_version(self.record_version)
        if self.maximum_bytes is not None and (type(self.maximum_bytes) is not int or self.maximum_bytes < 1):
            raise ValueError("canonical codec byte ceiling must be positive")
        validate_stable_id(self.decoder_key, field_name="decoder_key")
        validate_semantic_version(self.decoder_version)
        validate_sha256(
            self.decoder_implementation_sha256,
            field_name="decoder_implementation_sha256",
        )


@dataclass(frozen=True, slots=True)
class CanonicalRecordCodecRegistry:
    """Runtime-only type closure paired with canonical registration evidence."""

    registry_id: str
    registrations: tuple[CanonicalRecordCodecRegistration, ...]
    record_types: Mapping[str | tuple[str, str], type[CanonicalRecord]]
    additional_registrations: tuple[CanonicalRecordCodecRegistration, ...] = ()

    def __post_init__(self) -> None:
        validate_stable_id(self.registry_id, field_name="registry_id")
        for name in ("registrations", "additional_registrations"):
            values = getattr(self, name)
            if type(values) is not tuple or any(type(value) is not CanonicalRecordCodecRegistration for value in values):
                raise ValueError("static codec registry requires exact canonical registration tuples")
            for value in values:
                value.__post_init__()
        primary_keys = tuple((value.record_schema, value.record_version) for value in self.registrations)
        if primary_keys != tuple(sorted(set(primary_keys))):
            raise ValueError('static codec registrations require sorted unique schema/revision pairs')
        require_sorted_unique_ids(
            self.additional_registrations,
            attribute="codec_id",
            field_name="additional_registrations",
        )
        complete = (*self.registrations, *self.additional_registrations)
        if not self.registrations or len(complete) > MAX_STATIC_CODEC_REGISTRATIONS:
            raise ValueError("static codec registry has an invalid closed size")
        if len({value.codec_id for value in complete}) != len(complete):
            raise ValueError("static codec registry duplicates a canonical codec ID")
        if len({(value.record_schema, value.record_version, value.decoder_key, value.decoder_version) for value in complete}) != len(complete):
            raise ValueError("static codec registry duplicates an exact canonical decoder key/version")
        snapshot = RecordCodecCatalog(self.record_types)
        if {(kind.SCHEMA, kind.VERSION) for kind in snapshot.values()} != set(primary_keys):
            raise ValueError("static codec types differ from canonical registrations")
        if not {(value.record_schema, value.record_version) for value in self.additional_registrations}.issubset(primary_keys):
            raise ValueError("additional canonical codec lacks its primary record type")
        for registration in complete:
            record_type = snapshot.resolve(registration.record_schema, registration.record_version)
            if (
                not isinstance(record_type, type)
                or not issubclass(record_type, CanonicalRecord)
                or record_type.SCHEMA != registration.record_schema
                or record_type.VERSION != registration.record_version
            ):
                raise ValueError("static codec registration differs from its record type")
        object.__setattr__(self, "record_types", snapshot)

    def registration(self, record_schema: str, *, decoder_key: str | None = None,
                     decoder_version: str | None = None,
                     record_version: str | None = None) -> CanonicalRecordCodecRegistration:
        validate_schema(record_schema)
        if record_version is not None:
            validate_semantic_version(record_version)
        if (decoder_key is None) != (decoder_version is None):
            raise ValueError("canonical codec lookup requires both decoder key and version")
        if decoder_key is not None:
            validate_stable_id(decoder_key, field_name="decoder_key")
            validate_semantic_version(decoder_version)
        selected = self.registrations if decoder_key is None else (*self.registrations, *self.additional_registrations)
        matches = tuple(value for value in selected if value.record_schema == record_schema
            and (record_version is None or value.record_version == record_version)
            and (decoder_key is None or (value.decoder_key, value.decoder_version) == (decoder_key, decoder_version)))
        if len(matches) > 1:
            raise AmbiguousRecordRevision(
                f'canonical decoder {record_schema} requires an exact record revision; '
                f'installed revisions: {", ".join(sorted({value.record_version for value in matches}))}')
        if matches:
            return matches[0]
        if decoder_key is not None:
            raise KeyError(f"unregistered canonical decoder: {record_schema} {decoder_key}@{decoder_version}")
        revisions = sorted({kind.VERSION for kind in self.record_types.values() if kind.SCHEMA == record_schema})
        raise KeyError(f"unregistered canonical record schema/revision: {record_schema}@{record_version}; "
            f"installed revisions: {', '.join(revisions) or 'none'}")

    def record_type(self, schema: str, version: str) -> type[CanonicalRecord]:
        return resolve_record_codec(self.record_types, schema, version)

    def decode(self, payload: bytes, *, expected_schema: str,
               expected_version: str | None = None) -> CanonicalRecord:
        if expected_version is None:
            ceilings = tuple(value.maximum_bytes for value in self.registrations
                if value.record_schema == expected_schema)
            maximum = None if None in ceilings else max(ceilings, default=0)
            if type(payload) is not bytes or (maximum is not None and len(payload) > maximum):
                raise CanonicalizationError('canonical payload exceeds its bounded contract')
            _, expected_version = record_envelope_key(payload, expected_schema=expected_schema)
        registration = self.registration(expected_schema, record_version=expected_version)
        return decode_canonical_bytes(
            payload,
            self.record_type(expected_schema, expected_version),
            maximum_bytes=registration.maximum_bytes,
        )


def build_canonical_record_codec_registry(
    *,
    registry_id: str,
    record_types: tuple[type[CanonicalRecord], ...],
    maximum_bytes_by_schema: Mapping[str | tuple[str, str], int],
    decoder_implementation_sha256: str,
) -> CanonicalRecordCodecRegistry:
    catalogue = RecordCodecCatalog(record_types)
    if set(maximum_bytes_by_schema) != set(catalogue):
        raise ValueError("static codec byte ceilings differ from the type roster")
    registrations = tuple(
        sorted(
            (
                CanonicalRecordCodecRegistration(
                    codec_id=(f"canonical-json.{record_type.SCHEMA.replace('/', '.').replace('_', '-')}"
                        + ('' if record_type.VERSION == '1.0.0' else '.revision-' + record_type.VERSION)),
                    record_schema=record_type.SCHEMA,
                    record_version=record_type.VERSION,
                    maximum_bytes=maximum_bytes_by_schema[key],
                    decoder_key="kernel.canonical-json-decoder",
                    decoder_version="1.0.0",
                    decoder_implementation_sha256=decoder_implementation_sha256,
                )
                for key, record_type in catalogue.items()
            ),
            key=lambda value: (value.record_schema, value.record_version),
        )
    )
    return CanonicalRecordCodecRegistry(
        registry_id=registry_id,
        registrations=registrations,
        record_types=catalogue,
    )


__all__ = [
    'CanonicalRecordCodecRegistration',
    "CanonicalRecordCodecRegistry",
    "build_canonical_record_codec_registry",
]
