"""Strict, bounded decoding for canonical scientific records."""

from __future__ import annotations

import json
import re
import types
from collections import OrderedDict
from contextlib import contextmanager
from contextvars import ContextVar
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha256
from decimal import Decimal, DecimalException, InvalidOperation, getcontext
from enum import Enum
from functools import lru_cache
from types import MappingProxyType
from typing import Any, TypeVar, Union, get_args, get_origin, get_type_hints

from .parsed_nodes import ParsedNodeInterner
from .serialization import CanonicalizationError, CanonicalRecord, validate_document_shape

RecordT = TypeVar("RecordT", bound=CanonicalRecord)
_decoded_records: ContextVar[dict[tuple[type[CanonicalRecord], int], CanonicalRecord] | None] = (
    ContextVar("decoded_records", default=None)
)
_decoded_validations: ContextVar[OrderedDict | None] = ContextVar('decoded_local_validations', default=None)
_MAX_LOCAL_VALIDATIONS = 4096
_record_validation_lifetime: ContextVar[object | None] = ContextVar("record_validation_lifetime", default=None)
_IDENTITY_METHODS = tuple((name, getattr(CanonicalRecord, name)) for name in (
    'canonical_bytes', 'canonical_chunks', 'canonical_equals', '_encoding', '_is_cacheable', 'fingerprint'))


class _RecordValidationLifetime:
    __slots__ = ("active",)

    def __init__(self):
        self.active = True


@contextmanager
def record_validation_scope():
    """Reuse pure intrinsic checks within one finite immutable read.

    Proofs live on their existing deeply immutable records. The lifetime keeps
    no records alive and retains no permission, source or contextual verdict.
    A later operation, validator or Decimal context validates afresh.
    """
    current = _record_validation_lifetime.get()
    if current is not None and current.active:
        yield
        return
    lifetime = _RecordValidationLifetime()
    token = _record_validation_lifetime.set(lifetime)
    try:
        yield
    finally:
        lifetime.active = False
        _record_validation_lifetime.reset(token)

_exact_decimal_tokens: ContextVar[bool] = ContextVar("exact_decimal_tokens", default=False)
_CANONICAL_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?")


def decimal_context_key():
    """Settings affecting typed validation; sticky observation flags are excluded."""
    context=getcontext()
    return (context.prec,context.rounding,context.Emin,context.Emax,context.clamp,context.capitals,
        tuple(sorted((signal.__name__,enabled) for signal,enabled in context.traps.items())))


def validate_record_fields(record: CanonicalRecord) -> None:
    """Recheck pure local invariants within the owning immutable read.

    Exact-type and contextual joins remain with the calling owner. Mutable
    operands, a changed validator/Decimal context, and calls outside this
    finite read always validate afresh. No access/source verdict is retained.
    """
    validator = type(record).__post_init__
    memo = _decoded_validations.get()
    key = (validator, decimal_context_key())
    lifetime = _record_validation_lifetime.get()
    if lifetime is not None and lifetime.active:
        accepted = getattr(record, '_canonical_validation', None)
        if accepted is not None and accepted[0] is lifetime and accepted[1:] == key:
            return
    if memo is not None:
        accepted = memo.get(id(record))
        if accepted is not None and accepted[0] is record and accepted[1:] == key:
            memo.move_to_end(id(record))
            return
    validator(record)
    _remember_local_validation(record, validator)


def _remember_local_validation(record, validator):
    memo = _decoded_validations.get()
    lifetime = _record_validation_lifetime.get()
    if (memo is not None or lifetime is not None) and validator is not None and record._is_cacheable():
        key = validator, decimal_context_key()
        if lifetime is not None and lifetime.active:
            object.__setattr__(record, '_canonical_validation', (lifetime, *key))
        if memo is not None:
            memo[id(record)] = (record, *key)
            memo.move_to_end(id(record))
            if len(memo) > _MAX_LOCAL_VALIDATIONS:
                memo.popitem(last=False)


@lru_cache(maxsize=1024)
def record_annotations(record_type: type[CanonicalRecord]) -> Mapping[str, object]:
    """Cache installed type metadata; decode and validate every payload afresh."""

    return MappingProxyType(get_type_hints(record_type))


@lru_cache(maxsize=1024)
def _record_layout(record_type):
    annotations = record_annotations(record_type)
    layout = tuple((field.name, annotations[field.name]) for field in fields(record_type))
    return frozenset(name for name, _ in layout), layout


@lru_cache(maxsize=2048)
def _annotation_shape(annotation):
    return get_origin(annotation), get_args(annotation)


def _mapping(value: object, *, where: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise CanonicalizationError(f"{where} must be a string-keyed mapping")
    return value


def _decode_decimal(value: object, *, where: str) -> Decimal:
    raw = _mapping(value, where=where)
    if set(raw) != {"decimal"} or not isinstance(raw["decimal"], str):
        raise CanonicalizationError(f"{where} must be an exact tagged decimal")
    text = raw["decimal"]
    if _exact_decimal_tokens.get() and (text == "-0" or _CANONICAL_DECIMAL.fullmatch(text) is None):
        # Fixed-point canonical spellings cannot hide an expanding exponent.
        # The broader document decoder deliberately retains its old acceptance.
        raise CanonicalizationError(f"{where} decimal spelling is not canonical")
    try:
        result = Decimal(text)
    except InvalidOperation as error:
        raise CanonicalizationError(f"{where} contains an invalid decimal") from error
    if not result.is_finite():
        raise CanonicalizationError(f"{where} decimal must be finite")
    return result


def _decode(value: object, annotation: object, *, where: str) -> object:
    # Scalars dominate large metadata records. Their exact checks need no
    # repeated typing reflection, dataclass census or union dispatch.
    if annotation is str:
        if not isinstance(value, str):
            raise CanonicalizationError(f"{where} must be a string")
        return value
    if annotation is int:
        if type(value) is not int:
            raise CanonicalizationError(f"{where} must be an integer")
        return value
    if annotation is bool:
        if type(value) is not bool:
            raise CanonicalizationError(f"{where} must be boolean")
        return value
    if annotation is Decimal:
        return _decode_decimal(value, where=where)
    origin, arguments = _annotation_shape(annotation)
    if annotation is Any or annotation is object:
        raise CanonicalizationError(f"{where} has an unbounded canonical type")
    if annotation is type(None):
        if value is not None:
            raise CanonicalizationError(f"{where} must be null")
        return None
    if origin in {Union, types.UnionType}:
        errors: list[str] = []
        for option in arguments:
            try:
                return _decode(value, option, where=where)
            except (CanonicalizationError, TypeError, ValueError) as error:
                errors.append(str(error))
        raise CanonicalizationError(f"{where} does not match its closed union: {errors}")
    if origin is tuple:
        if not isinstance(value, list):
            raise CanonicalizationError(f"{where} must be a sequence")
        if len(arguments) == 2 and arguments[1] is Ellipsis:
            return tuple(
                _decode(item, arguments[0], where=f"{where}[{index}]")
                for index, item in enumerate(value)
            )
        if len(value) != len(arguments):
            raise CanonicalizationError(f"{where} has the wrong tuple length")
        return tuple(
            _decode(item, expected, where=f"{where}[{index}]")
            for index, (item, expected) in enumerate(zip(value, arguments, strict=True))
        )
    if origin is frozenset:
        if not isinstance(value, list):
            raise CanonicalizationError(f"{where} must be a sequence")
        return frozenset(
            _decode(item, arguments[0], where=f"{where}[{index}]")
            for index, item in enumerate(value)
        )
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        if not isinstance(value, str):
            raise CanonicalizationError(f"{where} enum value must be a string")
        try:
            return annotation(value)
        except ValueError as error:
            raise CanonicalizationError(f"{where} has an unknown enum value") from error
    if isinstance(annotation, type) and issubclass(annotation, CanonicalRecord):
        return decode_canonical_record(value, annotation, where=where)
    raise CanonicalizationError(f"{where} uses unsupported canonical type {annotation!r}")


def decode_canonical_record(
    document: object,
    record_type: type[RecordT],
    *,
    where: str = "document",
) -> RecordT:
    """Decode one closed canonical dataclass with exact schema and fields."""

    if not is_dataclass(record_type):
        raise TypeError("canonical record types must be dataclasses")
    cache = _decoded_records.get()
    cache_key = (record_type, id(document))
    if cache is not None and cache_key in cache:
        from typing import cast

        return cast(RecordT, cache[cache_key])
    raw = _mapping(document, where=where)
    names, layout = _record_layout(record_type)
    values = validate_document_shape(
        raw,
        expected_schema=record_type.SCHEMA,
        expected_version=record_type.VERSION,
        field_names=names,
    )
    decoded = {
        name: _decode(
            values[name],
            annotation,
            where=f"{where}.value.{name}",
        )
        for name, annotation in layout
    }
    try:
        result = record_type(**decoded)
        if cache is not None:
            cache[cache_key] = result
        _remember_local_validation(result, getattr(record_type, '__post_init__', None))
        return result
    except (TypeError, ValueError) as error:
        raise CanonicalizationError(f"{where} failed semantic validation: {error}") from error


@dataclass(frozen=True, slots=True)
class DecodedCanonicalRecord:
    """Exact typed-byte correspondence, never custody or access authority."""

    record: CanonicalRecord
    size_bytes: int
    content_sha256: str


def decode_canonical_bytes(
    payload: bytes,
    record_type: type[RecordT],
    *,
    maximum_bytes: int | None,
) -> RecordT:
    """Decode exact canonical JSON without accepting duplicates or binary numbers."""

    return _decode_canonical_bytes(payload, record_type, maximum_bytes=maximum_bytes)


def decode_canonical_bytes_with_identity(payload, record_type, *, maximum_bytes,
        inspect_document=None, maximum_integer_bytes=None, expected_sha256=None) -> DecodedCanonicalRecord:
    """Check an immutable body once, including optional stricter format checks.

    The inspection callback can add structural constraints; it cannot suppress
    typed validation or exact canonical comparison. The digest is computed
    from those actual bytes and can seed the immutable record's own identity.
    """
    if not isinstance(payload, bytes):
        raise CanonicalizationError('canonical payload must be immutable bytes')
    if maximum_bytes is not None and (maximum_bytes <= 0 or len(payload) > maximum_bytes):
        raise CanonicalizationError('canonical payload exceeds its bounded contract')
    digest = sha256(payload).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise CanonicalizationError('canonical payload differs from its expected byte identity')
    record = _decode_canonical_bytes(payload, record_type, maximum_bytes=maximum_bytes,
        inspect_document=inspect_document, maximum_integer_bytes=maximum_integer_bytes)
    if (all(getattr(type(record), name) is method for name, method in _IDENTITY_METHODS)
            and record._is_cacheable()):
        object.__setattr__(record, '_canonical_fingerprint', digest)
    return DecodedCanonicalRecord(record, len(payload), digest)


def _decode_canonical_bytes(payload, record_type, *, maximum_bytes,
        inspect_document=None, maximum_integer_bytes=None):

    if not isinstance(payload, bytes):
        raise CanonicalizationError("canonical payload must be immutable bytes")
    if maximum_bytes is not None and maximum_bytes <= 0:
        raise ValueError("canonical decode byte limit must be positive")
    if maximum_bytes is not None and len(payload) > maximum_bytes:
        raise CanonicalizationError("canonical payload exceeds its bounded contract")
    if maximum_integer_bytes is not None and (type(maximum_integer_bytes) is not int or maximum_integer_bytes <= 0):
        raise ValueError('canonical integer byte limit must be positive')
    if inspect_document is not None and not callable(inspect_document):
        raise TypeError('canonical document inspection must be callable')
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CanonicalizationError("canonical payload must be UTF-8") from error

    # Hash-cons only within this parse. Every occurrence still undergoes JSON
    # duplicate-key/number checks. Equal immutable subrecords can then undergo
    # the same typed semantic validation once, without changing canonical bytes.
    interner = ParsedNodeInterner()

    def reject_duplicates(pairs: list[tuple[str, object]], *, _interner=interner) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise CanonicalizationError(f"duplicate canonical mapping key: {key}")
            result[key] = value
        return _interner.mapping(result)

    def integer(text):
        if maximum_integer_bytes is not None and len(text) > maximum_integer_bytes:
            raise CanonicalizationError('canonical integer exceeds its byte bound')
        return int(text)

    try:
        document = json.loads(
            text,
            object_pairs_hook=reject_duplicates,
            parse_int=integer,
            parse_float=lambda _value: (_ for _ in ()).throw(
                CanonicalizationError("canonical binary numbers are forbidden; use tagged decimals")
            ),
            parse_constant=lambda _value: (_ for _ in ()).throw(
                CanonicalizationError("non-finite canonical numbers are forbidden")
            ),
        )
    except CanonicalizationError:
        raise
    except ValueError as error:
        # Includes the interpreter's integer-token digit refusal. Keep that
        # process-level safeguard enabled and translate only this parse's error.
        raise CanonicalizationError("canonical payload is not valid JSON") from error
    except RecursionError as error:
        raise CanonicalizationError("canonical payload nesting exceeds decoder capacity") from error
    # The parsed document owns its shared nodes now. Keeping the source text
    # and structural intern table during typed construction duplicates the
    # largest transient representations without supplying another check.
    del text, reject_duplicates, interner
    if inspect_document is not None:
        inspect_document(document)
    return _decode_canonical_document(document, record_type, payload)


def _decode_canonical_document(document, record_type, payload):
    """Construct shared parsed nodes with the ordinary exact-byte contract.

    A normalised operational view can supply the parsed graph. It cannot
    suppress current typed validators or comparison against the original bytes.
    """
    token = _decoded_records.set({})
    validation_token = _decoded_validations.set(OrderedDict())
    decimal_token = _exact_decimal_tokens.set(True)
    try:
        with record_validation_scope():
            record = decode_canonical_record(document, record_type)
        if not record.canonical_equals(payload):
            raise CanonicalizationError("canonical payload bytes are not canonical")
        return record
    except DecimalException as error:
        raise CanonicalizationError("canonical payload failed Decimal arithmetic") from error
    except RecursionError as error:
        raise CanonicalizationError("canonical payload nesting exceeds decoder capacity") from error
    finally:
        _decoded_validations.reset(validation_token)
        _exact_decimal_tokens.reset(decimal_token)
        _decoded_records.reset(token)
