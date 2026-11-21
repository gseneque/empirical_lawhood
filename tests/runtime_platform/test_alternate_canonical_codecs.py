# SPDX-License-Identifier: MPL-2.0
"""Disclosed codec-dispatch conformance; no scientific qualification or execution."""

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.static_codecs import MAX_STATIC_CODEC_REGISTRATIONS, CanonicalRecordCodecRegistration, CanonicalRecordCodecRegistry


@dataclass(frozen=True, slots=True)
class SmallRecord(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/alternate-codec"
    record_id: str
    text: str


class OtherRecord(SmallRecord):
    SCHEMA = "empirical-lawhood/testing/other-alternate-codec"


class DerivedRegistration(CanonicalRecordCodecRegistration):
    pass


def _registration(**changes):
    values = dict(codec_id="codec.testing.primary", record_schema=SmallRecord.SCHEMA,
        record_version=SmallRecord.VERSION, maximum_bytes=128,
        decoder_key="decoder.testing.primary", decoder_version="1.0.0",
        decoder_implementation_sha256=sha256(b"disclosed primary decoder").hexdigest())
    values.update(changes)
    return CanonicalRecordCodecRegistration(**values)


def _additional(**changes):
    return _registration(**dict(dict(codec_id="codec.testing.additional", maximum_bytes=512,
        decoder_key="decoder.testing.additional",
        decoder_implementation_sha256=sha256(b"disclosed additional decoder").hexdigest()), **changes))


def _registry(*, primary=None, additional=()):
    return CanonicalRecordCodecRegistry(registry_id="canonical-codecs.testing.alternatives",
        registrations=(_registration(),) if primary is None else primary,
        record_types={SmallRecord.SCHEMA: SmallRecord}, additional_registrations=additional)


def test_additional_codec_is_explicit_and_does_not_raise_the_legacy_default():
    legacy, alternate = _registration(), _additional()
    before = legacy.canonical_bytes()
    assert _registry().additional_registrations == ()
    registry = _registry(additional=(alternate,))
    assert registry.registrations == (legacy,)
    assert registry.registration(SmallRecord.SCHEMA) == legacy
    assert registry.registration(SmallRecord.SCHEMA,
        decoder_key=legacy.decoder_key, decoder_version=legacy.decoder_version) == legacy
    assert registry.registration(SmallRecord.SCHEMA,
        decoder_key=alternate.decoder_key, decoder_version=alternate.decoder_version) == alternate
    assert registry.registration(SmallRecord.SCHEMA).canonical_bytes() == before
    payload = SmallRecord("record.disclosed", "x" * 200).canonical_bytes()
    assert legacy.maximum_bytes < len(payload) < alternate.maximum_bytes
    with pytest.raises(ValueError):
        registry.decode(payload, expected_schema=SmallRecord.SCHEMA)
    selected = registry.registration(SmallRecord.SCHEMA,
        decoder_key=alternate.decoder_key, decoder_version=alternate.decoder_version)
    assert decode_canonical_bytes(payload, registry.record_types[SmallRecord.SCHEMA],
        maximum_bytes=selected.maximum_bytes).canonical_bytes() == payload


@pytest.mark.parametrize("keys", (
    {"decoder_key": "decoder.testing.additional"}, {"decoder_version": "1.0.0"},
    {"decoder_key": "decoder.testing.additional", "decoder_version": "2.0.0"},
    {"decoder_key": "decoder.testing.forged", "decoder_version": "1.0.0"},
    {"decoder_key": True, "decoder_version": "1.0.0"},
    {"decoder_key": "decoder.testing.additional", "decoder_version": False},
))
def test_keyed_lookup_refuses_partial_unknown_and_untyped_decoder_identities(keys):
    with pytest.raises((KeyError, TypeError, ValueError)):
        _registry(additional=(_additional(),)).registration(SmallRecord.SCHEMA, **keys)


def test_keyed_lookup_cannot_apply_an_installed_decoder_to_another_schema():
    with pytest.raises(KeyError):
        _registry(additional=(_additional(),)).registration(OtherRecord.SCHEMA,
            decoder_key="decoder.testing.additional", decoder_version="1.0.0")


@pytest.mark.parametrize("maximum", (0, -1, True, False, 1.5, "128"))
def test_canonical_codec_byte_bound_is_an_exact_positive_integer(maximum):
    with pytest.raises((TypeError, ValueError)):
        _registration(maximum_bytes=maximum)


@pytest.mark.parametrize("pool", ("primary", "additional"))
@pytest.mark.parametrize("form", ("list", "duck-record", "subclass"))
def test_registry_accepts_only_tuples_of_exact_registration_records(pool, form):
    valid = _registration() if pool == "primary" else _additional()
    if form == "list":
        supplied = [valid]
    else:
        values = {name: getattr(valid, name) for name in valid.__dataclass_fields__ if name != "SCHEMA"}
        forged = SimpleNamespace(**values) if form == "duck-record" else DerivedRegistration(**values)
        supplied = (forged,)
    with pytest.raises((TypeError, ValueError)):
        _registry(**{pool: supplied})


@pytest.mark.parametrize("changes", (
    {"record_schema": OtherRecord.SCHEMA}, {"record_version": "2.0.0"},
    {"codec_id": "codec.testing.primary"},
    {"decoder_key": "decoder.testing.primary", "decoder_version": "1.0.0"},
))
def test_additional_codec_cannot_change_type_revision_or_overlap_primary_identity(changes):
    with pytest.raises((TypeError, ValueError)):
        _registry(additional=(_additional(**changes),))


@pytest.mark.parametrize("mutation", ("unsorted", "duplicate-id", "duplicate-key"))
def test_additional_pool_has_unique_sorted_codec_ids_and_full_decoder_keys(mutation):
    first = _additional(codec_id="codec.testing.additional-a")
    second = _additional(codec_id="codec.testing.additional-b", decoder_key="decoder.testing.other")
    if mutation == "unsorted":
        values = (second, first)
    elif mutation == "duplicate-id":
        values = (first, replace(second, codec_id=first.codec_id))
    else:
        values = (first, replace(second, decoder_key=first.decoder_key))
    with pytest.raises((TypeError, ValueError)):
        _registry(additional=values)


def test_combined_primary_and_additional_pool_obeys_the_existing_closed_capacity():
    additional = tuple(_additional(codec_id=f"codec.testing.additional-{number:03d}",
        decoder_key=f"decoder.testing.additional-{number:03d}")
        for number in range(MAX_STATIC_CODEC_REGISTRATIONS))
    at_limit = _registry(additional=additional[:-1])
    assert len(at_limit.registrations) + len(at_limit.additional_registrations) == 256
    with pytest.raises(ValueError):
        _registry(additional=additional)


def test_current_recursive_codec_has_one_exact_unbounded_owner():
    from empirical_lawhood.methods.recursive_scientific_authoring import extension
    from scripts.generate_executable_binding_aggregate import LoadedExecutableDescriptor, _codec_registrations
    descriptor = LoadedExecutableDescriptor(Path(extension.__file__), extension.__name__,
        extension.EXTENSION.executable, extension.EXTENSION.factories, extension.EXTENSION.record_types)
    bindings = descriptor.contribution.bindings
    primary, additional, record_types = _codec_registrations((descriptor,), SimpleNamespace(bindings=bindings))
    assert len(primary) == 1 and not additional
    assert primary[0].maximum_bytes is None
    assert record_types == descriptor.record_types
    assert _codec_registrations((descriptor,), SimpleNamespace(bindings=(*bindings, *bindings))) == (primary, additional, record_types)


def test_optional_codec_limit_preserves_explicit_subcaps():
    row = _registration()
    assert replace(row, maximum_bytes=None).maximum_bytes is None
    assert replace(row, maximum_bytes=2**40).maximum_bytes == 2**40
