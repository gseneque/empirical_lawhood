"""Canonical, infrastructure-free serialization for scientific value objects."""

from __future__ import annotations

from contextvars import ContextVar

import hashlib
import json
import math
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from enum import Enum
from functools import lru_cache
from typing import ClassVar, Final, cast
from collections.abc import Hashable

_STABLE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SCHEMA = re.compile(
    r"^empirical-lawhood/[a-z0-9][a-z0-9._-]*(?:/[a-z0-9][a-z0-9._-]*)*$"
)
_SEMANTIC_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_LOCATOR_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
MAX_RELATIVE_LOCATOR_BYTES: Final[int] = 2048
MAX_RELATIVE_LOCATOR_SEGMENT_BYTES: Final[int] = 255
MAX_RELATIVE_LOCATOR_SEGMENTS: Final[int] = 64


class CanonicalizationError(ValueError):
    """Raised when a value cannot enter a canonical scientific document."""


def validate_relative_locator(value: str) -> str:
    """Validate one bounded, normalized external-root-relative POSIX locator."""

    if not isinstance(value, str) or not value:
        raise ValueError("relative locator must be a nonempty string")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("relative locator must be valid UTF-8 text") from error
    if len(encoded) > MAX_RELATIVE_LOCATOR_BYTES:
        raise ValueError("relative locator exceeds its UTF-8 byte limit")
    if unicodedata.normalize("NFC", value) != value:
        raise ValueError("relative locator must use NFC-normalized Unicode")
    if "\\" in value:
        raise ValueError("relative locator must use POSIX separators")
    if _LOCATOR_CONTROL.search(value) is not None:
        raise ValueError("relative locator cannot contain control characters")

    if value.startswith("/"):
        raise ValueError("relative locator cannot be an absolute path")
    segments = value.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError("relative locator cannot contain empty/current/parent segments")
    if len(segments) > MAX_RELATIVE_LOCATOR_SEGMENTS:
        raise ValueError("relative locator exceeds its segment-count limit")
    if any(
        len(segment.encode("utf-8")) > MAX_RELATIVE_LOCATOR_SEGMENT_BYTES for segment in segments
    ):
        raise ValueError("relative locator segment exceeds its UTF-8 byte limit")
    return value


def validate_stable_id(value: str, *, field_name: str = "id") -> str:
    """Validate a lowercase, portable semantic identifier."""

    if not isinstance(value, str) or _STABLE_ID.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase stable identifier, got {value!r}")
    return value


def validate_nonempty(value: str, *, field_name: str) -> str:
    """Validate nonempty, trimmed human/scientific text."""

    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be nonempty and trimmed")
    return value


def validate_schema(value: str) -> str:
    """Validate an owned format identity independently of its revision."""

    if not isinstance(value, str) or _SCHEMA.fullmatch(value) is None:
        raise ValueError(f"invalid schema identity: {value!r}")
    if any(
        segment == "latest" or re.fullmatch(r"v[0-9]+", segment)
        for segment in value.split("/")[1:]
    ):
        raise ValueError(f"invalid schema identity: {value!r}")
    return value


def validate_document_shape(
    document: Mapping[str, object],
    *,
    expected_schema: str,
    expected_version: str,
    field_names: frozenset[str],
) -> Mapping[str, object]:
    """Fail closed on an unsupported canonical document envelope or field set."""

    if set(document) != {"schema", "value", "version"}:
        raise CanonicalizationError("canonical document envelope fields differ")
    if document["schema"] != expected_schema:
        raise CanonicalizationError("unsupported canonical document schema")
    if document["version"] != expected_version:
        raise CanonicalizationError("unsupported canonical document version")
    value = document["value"]
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise CanonicalizationError("canonical document value must be a mapping")
    if set(value) != field_names:
        raise CanonicalizationError("canonical document fields differ")
    return value


def validate_semantic_version(value: str) -> str:
    if _SEMANTIC_VERSION.fullmatch(value) is None:
        raise ValueError(f"invalid semantic version: {value!r}")
    return value


def validate_sha256(value: str, *, field_name: str = "sha256") -> str:
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def validate_decimal(value: Decimal, *, field_name: str, minimum: Decimal | None = None) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    if minimum is not None and value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return value


def require_sorted_unique_strings(
    values: tuple[str, ...], *, field_name: str, allow_empty: bool = True
) -> None:
    """Require a set-like string tuple to have one canonical ordering."""

    if not allow_empty and not values:
        raise ValueError(f"{field_name} must not be empty")
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError(f"{field_name} must contain nonempty strings")
    if tuple(sorted(set(values))) != values:
        raise ValueError(f"{field_name} must be sorted and unique")


def _decimal_text(value: Decimal) -> str:
    """Encode the numerical value exactly, independently of arithmetic context.

    Formatting a Decimal in fixed-point notation is exact. In particular, do
    not normalize it arithmetically: normalize() rounds before stripping zeros.
    Signed zero and trailing fractional zeros have one canonical spelling.
    """
    if not value.is_finite():
        raise CanonicalizationError("non-finite Decimal is forbidden")
    if value.is_zero():
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"-0", ""}:
        return "0"
    return text


def canonical_value(value: object) -> object:
    """Convert supported immutable values to a deterministic JSON value."""

    if isinstance(value, CanonicalRecord):
        return value.to_document()
    if isinstance(value, Enum):
        return canonical_value(value.value)
    if isinstance(value, Decimal):
        return {"decimal": _decimal_text(value)}
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError("non-finite float is forbidden")
        raise CanonicalizationError("binary float is forbidden; use Decimal")
    if isinstance(value, tuple):
        return [canonical_value(item) for item in value]
    if isinstance(value, frozenset):
        converted = [canonical_value(item) for item in value]
        return sorted(converted, key=canonical_json_bytes)
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise CanonicalizationError("canonical mapping keys must be strings")
        return {key: canonical_value(value[key]) for key in sorted(value)}
    if is_dataclass(value):
        raise CanonicalizationError(
            f"dataclass {type(value).__name__} must inherit CanonicalRecord"
        )
    raise CanonicalizationError(f"unsupported canonical value type: {type(value).__name__}")


_canonical_documents: ContextVar[dict[int, tuple[object, dict[str, object]]] | None] = ContextVar(
    "canonical_documents", default=None
)


def canonical_json_bytes(value: object) -> bytes:
    """Serialize a supported value as canonical UTF-8 JSON plus newline."""

    if isinstance(value, CanonicalRecord):
        return value.canonical_bytes()

    token = _canonical_documents.set({})
    try:
        converted = canonical_value(value)
    finally:
        _canonical_documents.reset(token)
    return (
        json.dumps(
            converted,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def canonical_json_document_bytes(value: object) -> bytes:
    """Encode parsed JSON or JSON-facing API projections without changing records.

    Parsed arrays use lists; API projections can retain tuples and enum scalars.
    Freeze those containers before using the existing serializer. Scientific
    records still require their original types and binary floats remain forbidden.
    """
    def freeze(item):
        if type(item) in (list, tuple):
            return tuple(freeze(member) for member in item)
        if isinstance(item, Enum):
            return freeze(item.value)
        if type(item) is dict and all(type(key) is str for key in item):
            return {key: freeze(member) for key, member in item.items()}
        if type(item) in (str, int, bool, type(None)):
            return item
        raise CanonicalizationError("decoded canonical JSON requires only objects, arrays, strings, integers, booleans and null")

    return canonical_json_bytes(freeze(value))


@lru_cache(maxsize=2048)
def _record_field_names(record_type: Hashable) -> tuple[str, ...]:
    if not is_dataclass(record_type):
        raise TypeError("CanonicalRecord subclasses must be dataclasses")
    parameters = getattr(record_type, "__dataclass_params__", None)
    if parameters is None or not parameters.frozen:
        raise TypeError("CanonicalRecord dataclasses must be frozen")
    return tuple(sorted(field.name for field in fields(record_type)))


class _CanonicalRope:
    """Shared canonical fragments, without a full byte copy at every ancestor."""

    __slots__ = ("parts", "size")

    def __init__(self, parts, size):
        self.parts = parts
        self.size = size

    def chunks(self):
        pending = [iter(self.parts)]
        while pending:
            part = next(pending[-1], None)
            if part is None:
                pending.pop()
            elif isinstance(part, bytes):
                yield part
            else:
                pending.append(iter(part.parts))


def _canonical_join(parts):
    parts = tuple(parts)
    size = sum(len(part) if isinstance(part, bytes) else part.size for part in parts)
    if size <= 64 * 1024:
        return b"".join(part if isinstance(part, bytes) else b"".join(part.chunks()) for part in parts)
    # Coalesce small adjacent literals so a large tuple of scalars does not
    # require one Python iterator/hash call per comma on every later encoding.
    # Large child ropes remain shared rather than copied into their ancestors.
    chunks, pending, pending_size = [], [], 0
    for part in parts:
        if isinstance(part, _CanonicalRope) or len(part) > 64 * 1024:
            if pending:
                chunks.append(b"".join(pending))
                pending, pending_size = [], 0
            chunks.append(part)
        else:
            if pending_size + len(part) > 64 * 1024:
                chunks.append(b"".join(pending))
                pending, pending_size = [], 0
            pending.append(part)
            pending_size += len(part)
    if pending:
        chunks.append(b"".join(pending))
    return _CanonicalRope(tuple(chunks), size)


def _piece_bytes(piece):
    return piece if isinstance(piece, bytes) else b"".join(piece.chunks())


def _separated_parts(values):
    for index, value in enumerate(values):
        if index:
            yield b","
        yield _canonical_piece(value)


def _canonical_fragment(value: object) -> bytes:
    return _piece_bytes(_canonical_piece(value))


def _canonical_piece(value):
    """Preserve canonical bytes while sharing large immutable child encodings."""
    if isinstance(value, CanonicalRecord):
        if type(value).canonical_bytes is _STANDARD_CANONICAL_BYTES:
            return value._encoding()
        return value.canonical_bytes()[:-1]
    if isinstance(value, Enum):
        return _canonical_piece(value.value)
    if isinstance(value, Decimal):
        return b'{"decimal":' + _canonical_fragment(_decimal_text(value)) + b"}"
    if value is None:
        return b"null"
    if isinstance(value, str):
        # The same stdlib C string encoder used by json.dumps, without creating
        # a JSONEncoder for every scalar in a large immutable control graph.
        return json.encoder.encode_basestring_ascii(value).encode("ascii")
    if isinstance(value, bool):
        return b"true" if value else b"false"
    if isinstance(value, int):
        return int.__repr__(value).encode("ascii")
    if isinstance(value, tuple):
        return _canonical_join((b"[", *_separated_parts(value), b"]"))
    if isinstance(value, frozenset):
        return b"[" + b",".join(sorted(_canonical_fragment(item) for item in value)) + b"]"
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise CanonicalizationError("canonical mapping keys must be strings")
        parts = [b"{"]
        for index, key in enumerate(sorted(value)):
            if index:
                parts.append(b",")
            parts.extend((_canonical_fragment(key), b":", _canonical_piece(value[key])))
        return _canonical_join((*parts, b"}"))
    # Preserve the established errors for floats, mutable/unregistered values.
    canonical_value(value)
    raise CanonicalizationError(f"unsupported canonical value type: {type(value).__name__}")


def _immutable_encoding(value: object) -> bool:
    # A frozen dataclass can contain a mutable mapping. Never cache through one,
    # including MappingProxyType whose backing mapping can change elsewhere.
    if isinstance(value, CanonicalRecord):
        return value._is_cacheable()
    if isinstance(value, Enum):
        return _immutable_encoding(value.value)
    if value is None or isinstance(value, (str, bool, int, Decimal)):
        return True
    if isinstance(value, (tuple, frozenset)):
        return all(_immutable_encoding(item) for item in value)
    return False


@lru_cache(maxsize=2048)
def _record_encoding_layout(record_type, schema, version):
    names = _record_field_names(record_type)
    validate_schema(schema)
    validate_semantic_version(version)
    return (
        b'{"schema":' + _canonical_fragment(schema) + b',"value":{',
        tuple((name, (b"," if index else b"") + _canonical_fragment(name) + b":")
            for index, name in enumerate(names)),
        b'},"version":' + _canonical_fragment(version) + b"}",
    )


class CanonicalRecord:
    """Mixin for immutable, schema-versioned scientific value objects."""

    __slots__ = (
        "__weakref__",
        "_canonical_cacheable",
        "_canonical_encoding",
        "_canonical_fingerprint",
        "_canonical_validation",
    )

    _canonical_cacheable: bool
    _canonical_encoding: bytes | _CanonicalRope
    _canonical_fingerprint: str
    SCHEMA: ClassVar[str]
    VERSION: ClassVar[str] = "1.0.0"

    def to_document(self) -> dict[str, object]:
        cache = _canonical_documents.get()
        if cache is not None and id(self) in cache:
            return cache[id(self)][1]
        if not is_dataclass(self):
            raise TypeError("CanonicalRecord subclasses must be dataclasses")
        parameters = getattr(type(self), "__dataclass_params__", None)
        if parameters is None or not parameters.frozen:
            raise TypeError("CanonicalRecord dataclasses must be frozen")
        validate_schema(self.SCHEMA)
        validate_semantic_version(self.VERSION)
        values = {field.name: canonical_value(getattr(self, field.name)) for field in fields(self)}
        document = {
            "schema": self.SCHEMA,
            "value": values,
            "version": self.VERSION,
        }
        if cache is not None:
            cache[id(self)] = (self, document)
        return document

    def _is_cacheable(self) -> bool:
        try:
            return self._canonical_cacheable
        except AttributeError:
            names = _record_field_names(cast(Hashable, type(self)))
            safe = all(_immutable_encoding(getattr(self, name)) for name in names)
            object.__setattr__(self, "_canonical_cacheable", safe)
            return safe

    def canonical_bytes(self) -> bytes:
        body = self._encoding()
        if isinstance(body, bytes):
            return body + b"\n"
        return b"".join((*body.chunks(), b"\n"))

    def canonical_size_bytes(self) -> int:
        """Exact encoded length including LF, without flattening shared fragments."""
        if type(self).canonical_bytes is not _STANDARD_CANONICAL_BYTES:
            return len(self.canonical_bytes())
        body = self._encoding()
        return (len(body) if isinstance(body, bytes) else body.size) + 1

    def canonical_chunks(self):
        """Yield the unchanged canonical document, including its terminal LF."""
        if type(self).canonical_bytes is not _STANDARD_CANONICAL_BYTES:
            yield self.canonical_bytes()
            return
        body = self._encoding()
        yield from (body,) if isinstance(body, bytes) else body.chunks()
        yield b"\n"

    def canonical_equals(self, payload: bytes) -> bool:
        """Compare every exact byte without allocating a second full document."""
        if not isinstance(payload, bytes):
            raise TypeError("canonical comparison requires immutable bytes")
        offset = 0
        for chunk in self.canonical_chunks():
            if not payload.startswith(chunk, offset):
                return False
            offset += len(chunk)
        return offset == len(payload)

    def _encoding(self):
        try:
            return self._canonical_encoding
        except AttributeError:
            pass
        header, fields_, footer = _record_encoding_layout(type(self), self.SCHEMA, self.VERSION)
        parts = [header]
        for name, prefix in fields_:
            parts.extend((prefix, _canonical_piece(getattr(self, name))))
        body = _canonical_join((*parts, footer))
        if self._is_cacheable():
            # Encoding a parent needs each child's bytes, not every child's
            # independent digest. Keep those separate to avoid hashing large
            # shared descendants once per unrequested ancestor identity.
            object.__setattr__(self, "_canonical_encoding", body)
        return body

    def fingerprint(self) -> str:
        try:
            return self._canonical_fingerprint
        except AttributeError:
            pass
        if type(self).canonical_bytes is _STANDARD_CANONICAL_BYTES:
            digest = hashlib.sha256()
            for chunk in self.canonical_chunks():
                digest.update(chunk)
            result = digest.hexdigest()
        else:
            result = hashlib.sha256(self.canonical_bytes()).hexdigest()
        if self._is_cacheable():
            object.__setattr__(self, "_canonical_fingerprint", result)
        return result


_STANDARD_CANONICAL_BYTES = CanonicalRecord.canonical_bytes


def require_unique_ids(values: tuple[object, ...], *, attribute: str, field_name: str) -> None:
    identifiers = [getattr(value, attribute) for value in values]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"{field_name} contains duplicate {attribute} values")


def require_sorted_unique_ids(
    values: tuple[object, ...], *, attribute: str, field_name: str
) -> None:
    identifiers = tuple(getattr(value, attribute) for value in values)
    if tuple(sorted(set(identifiers))) != identifiers:
        raise ValueError(f"{field_name} must have sorted, unique {attribute} values")


@dataclass(frozen=True, slots=True)
class ExtensionBinding(CanonicalRecord):
    """Namespaced, schema-bound reference to an optional extension payload."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/kernel/extension-binding'

    namespace: str
    schema: str
    payload_sha256: str

    def __post_init__(self) -> None:
        validate_stable_id(self.namespace, field_name="namespace")
        validate_schema(self.schema)
        validate_sha256(self.payload_sha256, field_name="payload_sha256")


def require_extensions(values: tuple[ExtensionBinding, ...]) -> None:
    """Validate extension namespace uniqueness and canonical order."""

    namespaces = tuple(value.namespace for value in values)
    if tuple(sorted(set(namespaces))) != namespaces:
        raise ValueError("extensions must have sorted, unique namespaces")
