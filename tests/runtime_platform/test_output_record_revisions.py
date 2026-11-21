# SPDX-License-Identifier: MPL-2.0
"""Disclosed revision-dispatch controls; no scientific qualification or native work."""

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import ClassVar

import pytest

from empirical_lawhood.api.recursive_operation_index import OperationRecordCodecs
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.study_authoring import CapabilitySelection
from empirical_lawhood.storage.contracts.record_codecs import AmbiguousRecordRevision, OperationOutputRecordBinding, RecordCodecCatalog, UnsupportedRecordRevision, record_envelope_key, resolve_operation_output_codec, resolve_record_codec, snapshot_record_codecs
from empirical_lawhood.execution.static_codecs import build_canonical_record_codec_registry


@dataclass(frozen=True, slots=True)
class Earlier(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/revisioned-output'
    record_id: str
    mass_kg: Decimal


@dataclass(frozen=True, slots=True)
class Current(CanonicalRecord):
    SCHEMA: ClassVar[str] = Earlier.SCHEMA
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    mass_kg: Decimal
    uncertainty_kg: Decimal


@dataclass(frozen=True, slots=True)
class ForeignMeaning(CanonicalRecord):
    SCHEMA: ClassVar[str] = Earlier.SCHEMA
    record_id: str
    volume_litre: Decimal


A = CapabilitySelection('testing.revision-producer', '1.0.0', 'a'*64)
B = CapabilitySelection('testing.revision-producer', '2.0.0', 'b'*64)
BINDINGS = (OperationOutputRecordBinding(A, Earlier.SCHEMA, Earlier.VERSION),
    OperationOutputRecordBinding(B, Current.SCHEMA, Current.VERSION))


def catalogue():
    return RecordCodecCatalog((Earlier, Current), output_bindings=BINDINGS)


def test_both_exact_revisions_coexist_without_a_schema_default():
    codecs = catalogue()
    assert len(codecs) == 2 and set(codecs.values()) == {Earlier, Current}
    assert set(codecs) == {(Earlier.SCHEMA, '1.0.0'), (Earlier.SCHEMA, '2.0.0')}
    with pytest.raises(AmbiguousRecordRevision, match='1.0.0, 2.0.0'):
        codecs.get(Earlier.SCHEMA)
    assert codecs.for_operation(A, Earlier.SCHEMA) is Earlier
    assert codecs.for_operation(B, Current.SCHEMA) is Current
    assert resolve_record_codec(codecs, Earlier.SCHEMA, '1.0.0') is Earlier
    assert snapshot_record_codecs(codecs) is codecs
    assert codecs.with_record_types((Earlier,)).output_selection_keys == codecs.output_selection_keys


def test_old_and_new_canonical_bytes_keep_distinct_exact_decoders():
    codecs = catalogue()
    records = (Earlier('original.a', Decimal('1.25')), Current('new.b', Decimal('1.25'), Decimal('.02')))
    for record in records:
        before = record.canonical_bytes()
        key = record_envelope_key(before, expected_schema=Earlier.SCHEMA)
        decoded = decode_canonical_bytes(before, codecs.resolve(*key), maximum_bytes=4096)
        assert type(decoded) is type(record) and decoded.canonical_bytes() == before
        assert decoded.fingerprint() == record.fingerprint()
    with pytest.raises(UnsupportedRecordRevision, match='unsupported.*9.0.0.*1.0.0, 2.0.0'):
        codecs.resolve(Earlier.SCHEMA, '9.0.0')


@pytest.mark.parametrize('selection', (replace(A, implementation_sha256='f'*64), replace(B, capability_version='3.0.0')))
def test_known_producer_cannot_substitute_another_implementation_or_revision(selection):
    for permit_legacy in (False, True):
        with pytest.raises(UnsupportedRecordRevision, match='original compatible reader'):
            catalogue().for_operation(selection, Earlier.SCHEMA, allow_unbound_unique=permit_legacy)


def test_legacy_singleton_is_explicit_and_never_resolves_a_multirevision_family():
    unique = RecordCodecCatalog((Earlier,), output_bindings=BINDINGS[:1])
    legacy = CapabilitySelection('testing.historical-nonrecursive', '1.0.0', 'c'*64)
    assert unique[Earlier.SCHEMA] is Earlier
    with pytest.raises(UnsupportedRecordRevision):
        unique.for_operation(legacy, Earlier.SCHEMA)
    assert unique.for_operation(legacy, Earlier.SCHEMA, allow_unbound_unique=True) is Earlier
    with pytest.raises(UnsupportedRecordRevision):
        catalogue().for_operation(legacy, Earlier.SCHEMA, allow_unbound_unique=True)
    with pytest.raises(UnsupportedRecordRevision, match='retain the installed producer catalogue'):
        resolve_operation_output_codec(dict(catalogue()), A, Earlier.SCHEMA)


def test_same_class_reuse_is_allowed_but_same_revision_with_changed_meaning_refuses():
    assert len(RecordCodecCatalog((Earlier, Earlier))) == 1
    with pytest.raises(ValueError, match='disagree'):
        RecordCodecCatalog((Earlier, ForeignMeaning))
    with pytest.raises(ValueError, match='changes its exact'):
        RecordCodecCatalog({(Earlier.SCHEMA, Current.VERSION): Earlier})
    with pytest.raises(ValueError, match='conflicting output revisions'):
        RecordCodecCatalog((Earlier, Current), output_bindings=(BINDINGS[0],
            OperationOutputRecordBinding(A, Current.SCHEMA, Current.VERSION)))


def test_lazy_catalogue_resolves_only_the_selected_revision(monkeypatch):
    import empirical_lawhood.api.recursive_operation_index as index
    calls = []
    def resolve(module, name):
        calls.append((module, name))
        return {'Earlier': Earlier, 'Current': Current}[name]
    monkeypatch.setattr(index, '_resolve', resolve)
    rows = tuple((kind.SCHEMA, kind.VERSION, 'closed.testing.owner', kind.__name__) for kind in (Earlier, Current))
    selections = tuple((row.selection.capability_key, row.selection.capability_version,
        row.selection.implementation_sha256, row.record_schema, row.record_version) for row in BINDINGS)
    codecs = OperationRecordCodecs(rows, selections)
    assert calls == [] and set(codecs) == set(catalogue())
    assert codecs.for_operation(A, Earlier.SCHEMA) is Earlier
    assert calls == [('closed.testing.owner', 'Earlier')]
    assert codecs.for_operation(B, Current.SCHEMA) is Current
    assert calls[-1] == ('closed.testing.owner', 'Current')
    with pytest.raises(ValueError, match='repeat a schema/revision'):
        OperationRecordCodecs((*rows, rows[0]), selections)


def test_static_registry_selects_exact_revision_and_keeps_individual_byte_bounds():
    registry = build_canonical_record_codec_registry(registry_id='testing.revision-codecs',
        record_types=(Earlier, Current), maximum_bytes_by_schema={
            (Earlier.SCHEMA, Earlier.VERSION): 256, (Current.SCHEMA, Current.VERSION): 1024},
        decoder_implementation_sha256='d'*64)
    for record in (Earlier('original.a', Decimal('1')), Current('new.b', Decimal('1'), Decimal('.1'))):
        raw = record.canonical_bytes()
        assert registry.decode(raw, expected_schema=record.SCHEMA) == record
        assert registry.record_type(record.SCHEMA, record.VERSION) is type(record)
    with pytest.raises(AmbiguousRecordRevision):
        registry.registration(Earlier.SCHEMA)
    assert registry.registration(Earlier.SCHEMA, record_version='1.0.0').maximum_bytes == 256
    with pytest.raises(ValueError):
        registry.decode(Earlier('a'*256, Decimal(1)).canonical_bytes(), expected_schema=Earlier.SCHEMA)
    with pytest.raises(ValueError):
        registry.decode(Earlier('original.a', Decimal(1)).canonical_bytes(),
            expected_schema=Earlier.SCHEMA, expected_version=Current.VERSION)


def test_compiler_uses_supplier_revision_instead_of_an_installed_newer_output():
    from tests.runtime_platform.test_recursive_compiler import Config, fixture
    from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
    class NewConfig(Config):
        VERSION = '2.0.0'
    draft, registrations, registry = fixture()
    registrations = (registrations[0], replace(registrations[1], input_record_types=(Config,)))
    codecs = RecordCodecCatalog((Config, NewConfig), output_bindings=(
        OperationOutputRecordBinding(registrations[0].selection, Config.SCHEMA, Config.VERSION),
        OperationOutputRecordBinding(registrations[1].selection, Config.SCHEMA, NewConfig.VERSION)))
    compiled = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit='1'*40, output_codecs=codecs)
    assert compiled.output_codecs is codecs
    assert len(compiled.execution_plan.tasks) == 2
    with pytest.raises(ValueError, match='outside its selected declared consumer contract'):
        compile_recursive_wave(draft=draft, registrations=(registrations[0],
            replace(registrations[1], input_record_types=(NewConfig,))), registry=registry,
            implementation_commit='1'*40, output_codecs=codecs)


def test_full_and_generated_catalogues_agree_on_every_exact_producer():
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.api.recursive_operation_index import operation_record_codecs
    full, lazy = operation_catalog()[2], operation_record_codecs()
    assert dict(full) == dict(lazy)
    assert full.output_selection_keys == lazy.output_selection_keys
    for binding in full._output_binding_records:
        assert full.for_operation(binding.selection, binding.record_schema) is lazy.for_operation(
            binding.selection, binding.record_schema)


def _issued_owners():
    from hashlib import sha256
    from pathlib import Path
    from empirical_lawhood.execution.declaration_helpers import component
    from empirical_lawhood.execution.generated_extension_bundles import EXTENSION_BUNDLE_CONTRIBUTIONS
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.execution.executable_bindings import ExecutableBindingContribution, ExecutableBindingRole, ExecutableCapabilityBinding, ExecutableRecordTypeBinding, compose_executable_binding_aggregate
    from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionComponentKind, ExtensionContributionKind, compose_extension_bundle_aggregate
    from empirical_lawhood.execution.study_issue import StudyExtensionDecoderRegistration
    from scripts.generate_executable_binding_aggregate import LoadedExecutableDescriptor, _codec_registrations
    bindings, descriptors, discoveries = [], [], []
    for suffix, kind in (('a', Earlier), ('b', Current)):
        implementation = sha256(('disclosed revision owner '+suffix).encode()).hexdigest()
        decoder = component('decode-'+suffix, ExtensionComponentKind.CONFIG_DECODER,
            (kind.SCHEMA,), (kind.SCHEMA,), implementation, 'testing-revision')
        registration = StudyExtensionDecoderRegistration('decoder-registration.testing-'+suffix,
            decoder.component_key, decoder.component_version, kind.SCHEMA, kind.VERSION,
            sha256(('disclosed config '+suffix).encode()).hexdigest(), implementation, 4096)
        binding = ExecutableCapabilityBinding('executable.testing-revision-'+suffix,
            decoder.component_key, '1.0.0', implementation, ExecutableBindingRole.PROGRAMME_AUTHOR,
            decoder.component_key, '1.0.0', implementation, False, (decoder,), (),
            (ExecutableRecordTypeBinding(kind.SCHEMA, kind.VERSION),), (kind.SCHEMA,),
            (ObjectIdentity.from_record(decoder.registration_id, decoder),), (registration,),
            (kind.SCHEMA,), (kind.SCHEMA,), (), (), False, False, False, False)
        contribution = ExecutableBindingContribution('executable-contribution.testing-revision-'+suffix,
            '1.0.0', (binding,))
        descriptors.append(LoadedExecutableDescriptor(Path(__file__), __name__, contribution, (), (kind,)))
        discoveries.append(ExtensionBundleContribution('extension-contribution.testing-revision-'+suffix,
            '1.0.0', ExtensionContributionKind.STRUCTURAL, (), (), (), (), (), (),
            (ObjectIdentity.from_record(decoder.registration_id, decoder),), (), (), (), False, False))
        bindings.append(binding)
    discovery = compose_extension_bundle_aggregate(EXTENSION_BUNDLE_CONTRIBUTIONS + tuple(discoveries))
    aggregate = compose_executable_binding_aggregate(tuple(d.contribution for d in descriptors), discovery_aggregate=discovery)
    primary, additional, kinds = _codec_registrations(tuple(descriptors), aggregate)
    from empirical_lawhood.execution.static_codecs import CanonicalRecordCodecRegistry
    codecs = CanonicalRecordCodecRegistry('testing.issued-revisions', primary,
        {(kind.SCHEMA, kind.VERSION):kind for kind in kinds}, additional)
    return aggregate, tuple(bindings), codecs


@pytest.fixture(scope='module')
def issued_pair(tmp_path_factory):
    from types import SimpleNamespace
    from tests.issued_study_support import build_issued_study_fixture
    aggregate, bindings, codecs = _issued_owners()
    records = (Earlier('original.a', Decimal('1.2')), Current('new.b', Decimal('1.2'), Decimal('.02')))
    fixture = build_issued_study_fixture(tmp_path_factory.mktemp('disclosed-issued-revisions'),
        additional_extensions=tuple((record, binding.issued_decoder_registrations[0])
            for record, binding in zip(records, bindings, strict=True)), include_fixed_round_extension=False)
    return SimpleNamespace(aggregate=aggregate, bindings=bindings, codecs=codecs, records=records,
        manifest=fixture.package.issued_study)


def _issued_resolver(case):
    from empirical_lawhood.execution.issued_extension_payloads import IssuedExtensionPayloadResolver
    class Source:
        def __init__(self):
            self.reads = []
        def read_member(self, *, issue_id, member, maximum_bytes):
            assert issue_id == case.manifest.issue_id
            record, = (record for record in case.records if record.fingerprint() == member.logical_content_sha256)
            raw = record.canonical_bytes()
            assert len(raw) <= maximum_bytes
            self.reads.append(record.VERSION)
            return raw
    source = Source()
    return IssuedExtensionPayloadResolver(source=source, codecs=case.codecs), source


def test_issued_both_revisions_select_their_original_decoders_and_constructor_owners(issued_pair):
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    case = issued_pair
    resolver, source = _issued_resolver(case)
    result = resolver.resolve(manifest=case.manifest, aggregate=case.aggregate,
        selected_binding_ids=tuple(binding.binding_id for binding in case.bindings))
    assert set(source.reads) == {'1.0.0', '2.0.0'}
    assert set(result.records) == set(case.records)
    for replay in result.replay_set.payloads:
        binding, = (binding for binding in case.bindings if replay.decoded_record.object_version in
            {version for _, version in binding.construction_record_type_keys})
        assert replay.executable_binding == ObjectIdentity.from_record(binding.binding_id, binding)
        assert replay.decoder_registration == ObjectIdentity.from_record(
            binding.issued_decoder_registrations[0].registration_id, binding.issued_decoder_registrations[0])


def test_declared_issued_evidence_requires_explicit_revision_when_the_schema_is_ambiguous(issued_pair):
    case = issued_pair
    resolver, source = _issued_resolver(case)
    with pytest.raises(AmbiguousRecordRevision, match='requires an exact revision'):
        resolver.resolve_declared_records(manifest=case.manifest, aggregate=case.aggregate,
            required_schema_ids=(Earlier.SCHEMA,))
    assert source.reads == []
    for record in case.records:
        result = resolver.resolve_declared_records(manifest=case.manifest, aggregate=case.aggregate,
            required_record_keys=((record.SCHEMA, record.VERSION),))
        assert result.records == (record,) and source.reads[-1] == record.VERSION
    before = tuple(source.reads)
    with pytest.raises(ValueError, match='missing.*9.0.0'):
        resolver.resolve_declared_records(manifest=case.manifest, aggregate=case.aggregate,
            required_record_keys=((Earlier.SCHEMA, '9.0.0'),))
    assert tuple(source.reads) == before


def test_selected_issued_owner_cannot_consume_another_revision_by_schema_alone(issued_pair):
    resolver, source = _issued_resolver(issued_pair)
    with pytest.raises(ValueError, match='unconsumed'):
        resolver.resolve(manifest=issued_pair.manifest, aggregate=issued_pair.aggregate,
            selected_binding_ids=(issued_pair.bindings[0].binding_id,))
    assert source.reads == []


def test_constructor_routing_keeps_revision_ownership_and_refuses_before_factory_entry():
    from empirical_lawhood.execution.generated_extension_bundles import EXTENSION_BUNDLE_CONTRIBUTIONS
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.execution.executable_bindings import ExecutableBindingContribution, ExecutableBindingRole, ExecutableCapabilityProviderFactoryRegistry, LayeredCampaignRuntimeProviderResolver, compose_executable_binding_aggregate
    from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind, compose_extension_bundle_aggregate
    from empirical_lawhood.execution.providers import CampaignRuntimeProvider, CampaignRuntimeProviderRegistry
    from tests.runtime_platform.test_recursive_compiler import fixture
    registry = fixture()[2]
    _, owners, _ = _issued_owners()
    registry = replace(registry, capabilities=tuple(replace(manifest,
        config_schema=owner.accepted_config_types[0].record_schema,
        input_schema_ids=owner.input_schema_ids, output_schema_ids=owner.output_schema_ids)
        for owner, manifest in zip(owners, registry.capabilities, strict=True)))
    bindings = tuple(replace(owner, role=ExecutableBindingRole.CAMPAIGN_RUNTIME_PROVIDER,
        capability_backed=True, capability_key=manifest.capability_key,
        capability_version=manifest.capability_version, capability_implementation_sha256=manifest.implementation_sha256)
        for owner, manifest in zip(owners, registry.capabilities, strict=True))
    discovery = compose_extension_bundle_aggregate(EXTENSION_BUNDLE_CONTRIBUTIONS + (ExtensionBundleContribution(
        'testing.revision-routing', '1.0.0', ExtensionContributionKind.STRUCTURAL,
        (), registry.capabilities, (), (), (), (), tuple(sorted((
            ObjectIdentity.from_record(component.registration_id, component)
            for binding in bindings for component in binding.discovery_components), key=lambda value:value.object_id)),
        (), (), (), False, False),))
    observed = []
    class Provider(CampaignRuntimeProvider):
        issued_source_schema_ids = ()
        capability_count = 1
        def __init__(self, registry):
            self.registry_sha256 = registry.fingerprint()
    @dataclass(frozen=True)
    class Factory:
        binding: object
        def build_provider(self, *, registry, records, platform_ports):
            observed.append((self.binding.binding_id, records, platform_ports))
            return Provider(registry)
    def resolver(selected):
        aggregate = compose_executable_binding_aggregate((ExecutableBindingContribution(
            'testing.revision-routing', '1.0.0', selected),), discovery_aggregate=discovery)
        return LayeredCampaignRuntimeProviderResolver(precomposed=CampaignRuntimeProviderRegistry(()),
            factories=ExecutableCapabilityProviderFactoryRegistry(aggregate=aggregate,
                factories=tuple(Factory(binding) for binding in selected)))
    records = (Earlier('original.a', Decimal(1)), Current('new.b', Decimal(1), Decimal('.1')))
    provider = resolver(bindings).resolve(registry, decoded_records=records)
    assert provider.capability_count == 2
    assert observed == [(bindings[0].binding_id, (records[0],), ()), (bindings[1].binding_id, (records[1],), ())]
    observed.clear()
    class Unknown(Earlier):
        VERSION = '9.0.0'
    with pytest.raises(ValueError, match='unconsumed.*9.0.0'):
        resolver(bindings).resolve(registry, decoded_records=(Unknown('unknown', Decimal(1)),))
    assert observed == []
    with pytest.raises(ValueError, match='overlap decoded-payload ownership'):
        resolver((bindings[0], replace(bindings[1], accepted_config_types=bindings[0].accepted_config_types))).resolve(
            registry, decoded_records=records)
    assert observed == []
