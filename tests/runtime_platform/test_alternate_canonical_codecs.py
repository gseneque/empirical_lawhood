# SPDX-License-Identifier: MPL-2.0
"""Disclosed codec-dispatch conformance; no scientific qualification or execution."""

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalizationError, CanonicalRecord
from empirical_lawhood.runtime.static_codecs import (
    MAX_STATIC_CODEC_REGISTRATIONS,
    CanonicalRecordCodecRegistration,
    CanonicalRecordCodecRegistry,
)


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


@pytest.mark.parametrize("maximum", (0, -1, True, False, 1.5, "128", None))
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


def _author_descriptors():
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring import executable_binding as legacy
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded32 import executable_binding as bounded
    from scripts.generate_executable_binding_aggregate import LoadedExecutableDescriptor
    return tuple(LoadedExecutableDescriptor(Path(module.__file__), module.__name__,
        module.EXECUTABLE_BINDING_CONTRIBUTION, module.EXECUTABLE_BINDING_FACTORIES,
        module.EXECUTABLE_RECORD_TYPES) for module in (legacy, bounded))


def _codec_pools(descriptors, bindings=None):
    from scripts.generate_executable_binding_aggregate import _codec_registrations
    roster = tuple(binding for descriptor in descriptors for binding in descriptor.contribution.bindings)
    return _codec_registrations(descriptors, SimpleNamespace(bindings=roster if bindings is None else bindings))


def test_generator_preserves_primary_canonical_bytes_with_a_distinct_additional_decoder():
    legacy, bounded = _author_descriptors()
    assert len(legacy.record_types) == 1 and bounded.record_types == ()
    old_primary, old_additional, old_types = _codec_pools((legacy,))
    primary, additional, record_types = _codec_pools((legacy, bounded))
    assert len(primary) == len(additional) == 1
    assert old_additional == () and record_types == old_types == legacy.record_types
    assert tuple(value.canonical_bytes() for value in primary) == tuple(value.canonical_bytes() for value in old_primary)
    assert primary[0].codec_id == "executable-canonical-json." + primary[0].record_schema.replace("/", ".").replace("_", "-")
    assert primary[0].maximum_bytes == 16 * 1024**2
    assert additional[0].maximum_bytes == 32 * 1024**2
    assert additional[0].codec_id != primary[0].codec_id
    decoder = bounded.contribution.bindings[0].issued_decoder_registrations[0]
    assert additional[0].codec_id == primary[0].codec_id + ".decoder-" + decoder.fingerprint()
    assert (additional[0].decoder_key, additional[0].decoder_version,
        additional[0].decoder_implementation_sha256) == (
        decoder.decoder_key, decoder.decoder_version, decoder.implementation_sha256)
    assert _codec_pools((bounded, legacy)) == (primary, additional, record_types)


def test_real_scientific_selection_default_refuses_sixteen_mib_plus_one_before_parsing():
    from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection
    primary, additional, record_types = _codec_pools(_author_descriptors())
    registry = CanonicalRecordCodecRegistry("canonical-codecs.testing.legacy-bound", primary,
        {value.SCHEMA: value for value in record_types}, additional_registrations=additional)
    assert registry.registration(RecursiveScientificSelection.SCHEMA).maximum_bytes == 16 * 1024**2
    # Invalid UTF-8 makes the precise bounded refusal distinguishable from parsing.
    payload = b"\xff" * (16 * 1024**2 + 1)
    with pytest.raises(CanonicalizationError, match="exceeds its bounded contract"):
        registry.decode(payload, expected_schema=RecursiveScientificSelection.SCHEMA)


def test_generator_deduplicates_one_exact_issued_decoder_shared_by_consumers():
    descriptors = _author_descriptors()
    bindings = tuple(descriptor.contribution.bindings[0] for descriptor in descriptors)
    assert _codec_pools(descriptors, (*bindings, bindings[1])) == _codec_pools(descriptors)


@pytest.mark.parametrize("changed", ("maximum_payload_bytes", "config_sha256", "registration_id"))
def test_generator_refuses_conflicting_full_issued_records_at_one_decoder_key(changed):
    descriptors = _author_descriptors()
    bindings = tuple(descriptor.contribution.bindings[0] for descriptor in descriptors)
    decoder = bindings[1].issued_decoder_registrations[0]
    replacement = {"maximum_payload_bytes": decoder.maximum_payload_bytes - 1,
        "config_sha256": "a" * 64, "registration_id": decoder.registration_id + ".other"}[changed]
    conflicting = replace(bindings[1], issued_decoder_registrations=(replace(decoder, **{changed: replacement}),))
    with pytest.raises(ValueError):
        _codec_pools(descriptors, (*bindings, conflicting))


@pytest.mark.parametrize("mutation", ("missing-owner", "duplicate-owner", "wrong-version"))
def test_generator_requires_one_descriptor_owner_of_the_original_record_type(mutation):
    legacy, bounded = _author_descriptors()
    if mutation == "missing-owner":
        descriptors = (replace(legacy, record_types=()), bounded)
    elif mutation == "duplicate-owner":
        descriptors = (legacy, replace(bounded, record_types=legacy.record_types))
    else:
        class WrongRevision(legacy.record_types[0]):
            VERSION = "2.0.0"
        descriptors = (replace(legacy, record_types=(WrongRevision,)), bounded)
    with pytest.raises(ValueError):
        _codec_pools(descriptors)


def _installed_aggregate(*, include_external=False):
    from empirical_lawhood.adapters.composition.generated_extension_bundles import EXTENSION_BUNDLE_CONTRIBUTIONS
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded32.extension_bundle import EXTENSION_BUNDLE_CONTRIBUTION
    from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution, compose_executable_binding_aggregate
    from empirical_lawhood.runtime.extension_bundles import compose_extension_bundle_aggregate
    discovery_contributions = {value.contribution_id: value for value in EXTENSION_BUNDLE_CONTRIBUTIONS}
    discovery_contributions[EXTENSION_BUNDLE_CONTRIBUTION.contribution_id] = EXTENSION_BUNDLE_CONTRIBUTION
    contributions = [descriptor.contribution for descriptor in _author_descriptors()]
    if include_external:
        external, discovery = _external_operation_binding()
        contributions.append(ExecutableBindingContribution("executable-contribution.testing.codec-operation", "1.0.0", (external,)))
        discovery_contributions[discovery.contribution_id] = discovery
    discovery = compose_extension_bundle_aggregate(tuple(discovery_contributions.values()))
    return compose_executable_binding_aggregate(tuple(contributions), discovery_aggregate=discovery), discovery


def test_descriptor_composition_keeps_its_four_item_primary_only_contract(monkeypatch):
    import scripts.generate_executable_binding_aggregate as generator
    descriptors = _author_descriptors()
    _aggregate, discovery = _installed_aggregate()
    monkeypatch.setattr(generator, "GENERATED_EXTENSION_BUNDLE_AGGREGATE", discovery)
    composed = generator.compose_loaded_descriptors(descriptors)
    assert len(composed) == 4
    assert composed[2:] == (_codec_pools(descriptors)[0], descriptors[0].record_types)
    rendered = generator.render_generated_module(tuple(value.path for value in descriptors))
    assert "additional_registrations=" in rendered
    assert _codec_pools(descriptors)[1][0].codec_id in rendered


def _external_operation_binding():
    from empirical_lawhood.adapters.composition.discovery import component
    from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection
    from empirical_lawhood.runtime.executable_bindings import ExecutableBindingRole, ExternalConfigExecutableCapabilityBinding
    from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionComponentKind, ExtensionContributionKind
    implementation = sha256(b"disclosed stateless codec consumer").hexdigest()
    provider = component("operation", ExtensionComponentKind.RUNTIME_PROVIDER,
        (RecursiveScientificSelection.SCHEMA,), (RecursiveScientificSelection.SCHEMA,), implementation, "testing-codec")
    binding = ExternalConfigExecutableCapabilityBinding(
        "executable.testing.codec-operation", provider.component_key, "1.0.0", implementation,
        ExecutableBindingRole.CAMPAIGN_RUNTIME_PROVIDER, provider.component_key, "1.0.0", implementation,
        False, (provider,), (), (), (), (), (), (RecursiveScientificSelection.SCHEMA,),
        (RecursiveScientificSelection.SCHEMA,), (), ("testing.codec.input",), False, False, False, False)
    contribution = ExtensionBundleContribution("extension-contribution.testing.codec-operation", "1.0.0",
        ExtensionContributionKind.STRUCTURAL, (), (), (), (), (), (), (), (),
        (ObjectIdentity.from_record(provider.registration_id, provider),), (), False, False)
    return binding, contribution


@pytest.fixture(scope="module", params=(0, 1), ids=("legacy16", "bounded32"))
def issued_selection(request, tmp_path_factory):
    from tests.issued_study_support import build_issued_study_fixture
    from tests.runtime_platform.test_recursive_compiler import prospective_fixture
    selection = prospective_fixture()[0].selected_scientific_projection
    descriptor = _author_descriptors()[request.param]
    registration = descriptor.contribution.bindings[0].issued_decoder_registrations[0]
    fixture = build_issued_study_fixture(tmp_path_factory.mktemp("issued-alternate-codec"),
        additional_extensions=((selection, registration),), include_fixed_round_extension=False)
    return SimpleNamespace(record=selection, manifest=fixture.package.issued_study,
        owner=descriptor.contribution.bindings[0], decoder=registration)


class _ObservedPayloadSource:
    def __init__(self, case):
        self.case, self.reads = case, []

    def read_member(self, *, issue_id, member, maximum_bytes):
        payload = self.case.record.canonical_bytes()
        assert issue_id == self.case.manifest.issue_id
        assert member.physical_sha256 == sha256(payload).hexdigest()
        assert len(payload) <= maximum_bytes
        self.reads.append((member.member_id, maximum_bytes))
        return payload


def _issued_resolver(case, *, codec_change=None):
    from empirical_lawhood.runtime.issued_extension_payloads import IssuedExtensionPayloadResolver
    primary, additional, record_types = _codec_pools(_author_descriptors())
    if codec_change:
        primary = tuple(replace(value, **codec_change) if value.decoder_key == case.decoder.decoder_key else value for value in primary)
        additional = tuple(replace(value, **codec_change) if value.decoder_key == case.decoder.decoder_key else value for value in additional)
    registry = CanonicalRecordCodecRegistry("canonical-codecs.testing.issued-alternatives", primary,
        {value.SCHEMA: value for value in record_types}, additional_registrations=additional)
    source = _ObservedPayloadSource(case)
    return IssuedExtensionPayloadResolver(source=source, codecs=registry), source


def _replay(resolver, case, route, *, manifest=None):
    aggregate, _discovery = _installed_aggregate(include_external=route == "external-config")
    manifest = case.manifest if manifest is None else manifest
    if route == "declared":
        resolved = resolver.resolve_declared_records(manifest=manifest, aggregate=aggregate,
            required_schema_ids=(case.record.SCHEMA,))
        return resolved.records, resolved.payloads
    selected = ("executable.testing.codec-operation",) if route == "external-config" else (case.owner.binding_id,)
    resolved = resolver.resolve(manifest=manifest, aggregate=aggregate, selected_binding_ids=selected)
    assert not resolved.replay_set.executed and not resolved.replay_set.grants_authority
    return resolved.records, resolved.replay_set.payloads


@pytest.mark.parametrize("route", ("selected-owner", "declared", "external-config"))
def test_issued_replay_selects_the_full_decoder_owner_with_both_capacities_installed(issued_selection, route):
    resolver, source = _issued_resolver(issued_selection)
    records, payloads = _replay(resolver, issued_selection, route)
    assert tuple(value.canonical_bytes() for value in records) == (issued_selection.record.canonical_bytes(),)
    assert len(source.reads) == len(payloads) == 1
    replay = payloads[0]
    assert replay.executable_binding == ObjectIdentity.from_record(issued_selection.owner.binding_id, issued_selection.owner)
    assert replay.decoder_registration == ObjectIdentity.from_record(issued_selection.decoder.registration_id, issued_selection.decoder)
    codec = resolver.codecs.registration(issued_selection.record.SCHEMA,
        decoder_key=issued_selection.decoder.decoder_key, decoder_version=issued_selection.decoder.decoder_version)
    assert replay.canonical_codec_registration == ObjectIdentity.from_record(codec.codec_id, codec)
    assert replay.byte_count == len(issued_selection.record.canonical_bytes())
    assert replay.consumed and not replay.grants_authority


@pytest.mark.parametrize("route", ("selected-owner", "declared", "external-config"))
@pytest.mark.parametrize("mismatch", ("implementation", "upward-bound"))
def test_issued_replay_refuses_codec_implementation_or_upward_byte_forgery_before_read(issued_selection, route, mismatch):
    change = {"decoder_implementation_sha256": "f" * 64} if mismatch == "implementation" else {
        "maximum_bytes": issued_selection.decoder.maximum_payload_bytes + 1}
    resolver, source = _issued_resolver(issued_selection, codec_change=change)
    with pytest.raises(ValueError):
        _replay(resolver, issued_selection, route)
    assert source.reads == []


@pytest.mark.parametrize("route", ("selected-owner", "declared", "external-config"))
def test_installed_codec_can_intentionally_tighten_the_issued_decoder_read_bound(issued_selection, route):
    bound = len(issued_selection.record.canonical_bytes())
    assert bound < issued_selection.decoder.maximum_payload_bytes
    resolver, source = _issued_resolver(issued_selection, codec_change={"maximum_bytes": bound})
    records, _payloads = _replay(resolver, issued_selection, route)
    assert records == (issued_selection.record,)
    assert source.reads[0][1] == bound


@pytest.mark.parametrize("route", ("selected-owner", "declared", "external-config"))
@pytest.mark.parametrize("mismatch", ("lower-bound", "foreign-config"))
def test_issued_replay_refuses_a_changed_full_decoder_identity_before_read(issued_selection, route, mismatch):
    decoder = issued_selection.decoder
    changed = replace(decoder, **({"maximum_payload_bytes": decoder.maximum_payload_bytes - 1}
        if mismatch == "lower-bound" else {"config_sha256": "e" * 64}))
    binding = issued_selection.manifest.issued_extensions.bindings[0]
    extensions = replace(issued_selection.manifest.issued_extensions, bindings=(replace(binding,
        decoder_registration=ObjectIdentity.from_record(changed.registration_id, changed)),))
    # Keep the outer record structurally valid while making its decoder join hostile.
    validation = replace(issued_selection.manifest.extension_validation,
        issued_extension_set=ObjectIdentity.from_record(extensions.issued_extension_set_id, extensions))
    manifest = replace(issued_selection.manifest, issued_extensions=extensions, extension_validation=validation)
    resolver, source = _issued_resolver(issued_selection)
    with pytest.raises(ValueError):
        _replay(resolver, issued_selection, route, manifest=manifest)
    assert source.reads == []
