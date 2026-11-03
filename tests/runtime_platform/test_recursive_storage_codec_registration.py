# SPDX-License-Identifier: MPL-2.0
"""Disclosed binary-codec conformance fixtures, without execution or authority."""

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import struct
from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
from empirical_lawhood.infrastructure.artifact_validation import validate_jsonl_stream
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityRegistry
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificInputRole, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract, compile_recursive_wave
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveOperationProviderFactory, recursive_operation_binding,
)
from empirical_lawhood.runtime.recursive_storage_codecs import (
    RecursiveStorageCodec, resolve_storage_codec, storage_codec_census,
)
from tests.runtime_platform.test_recursive_compiler import (
    BUDGET, PERMISSIONS, Config, SourceConfig, UseConfig, fixture,
)


SCHEMA = "empirical-lawhood/testing/independently-framed-binary"
MEDIA = "application/octet-stream"
MAGIC = b"EL-DISCLOSED-CODEC\x00"
OTHER_MEDIA = "application/vnd.empirical-lawhood.disclosed-binary"
OTHER_MAGIC = b"EL-OTHER-WIRE-FORMAT\x00"
FORMAT_VERSION = "1.0.0"
MAXIMUM_BYTES = 128


@pytest.mark.parametrize("sequence", (False, True, "0", None))
def test_jsonl_sequence_requires_exact_integers(sequence):
    payload = canonical_json_bytes({"schema": SCHEMA, "sequence": sequence})
    with pytest.raises(ArtifactIdentityConflict, match="sequence"):
        validate_jsonl_stream(BytesIO(payload), SimpleNamespace(payload_schema=SCHEMA), size=len(payload))


@pytest.mark.parametrize("version", (None, "0.9.0", "1.0.1", 1, True))
def test_registered_jsonl_version_cannot_change_its_original_record_contract(version):
    payload = canonical_json_bytes({"schema": SCHEMA, "sequence": 0, "version": version})
    with pytest.raises(ArtifactIdentityConflict, match="version"):
        validate_jsonl_stream(BytesIO(payload), SimpleNamespace(payload_schema=SCHEMA),
                              size=len(payload), record_version=FORMAT_VERSION)


def test_jsonl_retains_versionless_flat_frames_and_exact_declared_record_versions():
    for version in (None, FORMAT_VERSION):
        records = ({"schema": SCHEMA, "sequence": sequence,
                    **({"version": version} if version is not None else {})} for sequence in range(3))
        payload = b"".join(canonical_json_bytes(record) for record in records)
        validate_jsonl_stream(BytesIO(payload), SimpleNamespace(payload_schema=SCHEMA),
                              size=len(payload), record_version=version)


def test_jsonl_second_sequence_cannot_substitute_true_for_one():
    payload = b"".join(canonical_json_bytes({"schema": SCHEMA, "sequence": sequence}) for sequence in (0, True))
    with pytest.raises(ArtifactIdentityConflict, match="sequence"):
        validate_jsonl_stream(BytesIO(payload), SimpleNamespace(payload_schema=SCHEMA), size=len(payload))


def _framed(payload=b"independent fixture bytes"):
    return MAGIC + struct.pack("<I", len(payload)) + payload + sha256(payload).digest()


def _validate_fixture_stream(source, request, *, size):
    """An explicit miniature domain format; no arbitrary deserialization."""
    return _validate_disclosed_frame(source, request, size=size, magic=MAGIC, media=MEDIA)


def _validate_other_fixture_stream(source, request, *, size):
    return _validate_disclosed_frame(source, request, size=size, magic=OTHER_MAGIC, media=OTHER_MEDIA)


def _validate_raw_json_fixture_stream(source, request, *, size):
    """Non-EL source JSON retains its exact original spacing and byte identity."""
    if (request.payload_schema != SCHEMA or request.profile is not ArtifactProfile.RAW_SOURCE_BYTES
            or request.media_type != "application/json" or not 0 < size <= MAXIMUM_BYTES):
        raise ValueError("raw source JSON changes its exact physical contract")
    raw = source.read(size+1)
    if len(raw) != size or json.loads(raw) != {"original": [1, 2]}:
        raise ValueError("raw source JSON changes its complete structural fixture")


def _validate_disclosed_frame(source, request, *, size, magic, media):
    if (request.payload_schema != SCHEMA or request.profile is not ArtifactProfile.RAW_SOURCE_BYTES
            or request.media_type != media):
        raise ValueError("disclosed fixture changes its exact binary transport")
    if source.read(len(magic)) != magic:
        raise ValueError("disclosed fixture changes its magic header")
    length_bytes = source.read(4)
    if len(length_bytes) != 4:
        raise ValueError("disclosed fixture truncates its length header")
    count, = struct.unpack("<I", length_bytes)
    if len(magic) + 4 + count + 32 != size:
        raise ValueError("disclosed fixture changes its complete byte denominator")
    digest, remaining = sha256(), count
    while remaining:
        payload = source.read(min(16, remaining))
        if type(payload) is not bytes or not payload or len(payload) > min(16, remaining):
            raise ValueError("disclosed fixture truncates its bounded body")
        digest.update(payload)
        remaining -= len(payload)
    if source.read(32) != digest.digest() or source.read(1):
        raise ValueError("disclosed fixture changes its complete byte payload or footer")


def _forbidden(*_args, **_kwargs):
    raise AssertionError("cold codec discovery invoked a runner or structural validator")


def _codec(**changes):
    values = dict(codec_id="testing.storage.independent-frame", payload_schema=SCHEMA,
        record_version=FORMAT_VERSION, profile=ArtifactProfile.RAW_SOURCE_BYTES,
        media_type=MEDIA, filename_suffix=".blob", validate_stream=_validate_fixture_stream,
        maximum_bytes=MAXIMUM_BYTES)
    values.update(changes)
    return RecursiveStorageCodec(**values)


def _declaration(node, codec, *, output_limit=None, consumer_limit=MAXIMUM_BYTES):
    configuration_type = SourceConfig if node == "source" else UseConfig
    return RecursiveOperationDeclaration(
        capability_key="testing.storage." + node, capability_version="1.0.0",
        implementation_id="testing.storage." + node + ".v1", kind=CapabilityKind.TRANSFORM,
        config_record_type=configuration_type, stage=ScientificStage.TRANSFORM,
        input_ports=() if node == "source" else (
            RecursivePortContract("operand", codec.payload_schema, codec.media_type, consumer_limit),),
        outputs=(OutputTemplate("result", codec.payload_schema, codec.profile, codec.media_type, codec.filename_suffix),)
            if node == "source" else (
                OutputTemplate("result", Config.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                               "application/json", ".json"),),
        permissions=PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=replace(BUDGET, output_bytes=output_limit),
        conformance_check_ids=("check.disclosed-storage-conformance",), runner_factory=_forbidden,
        record_codecs={Config.SCHEMA: Config, configuration_type.SCHEMA: configuration_type},
        storage_codecs=(codec,),
    )


def _compile(*, codec=None, output_limit=None, consumer_limit=MAXIMUM_BYTES,
             omit_source_codec=False, omit_consumer_codec=False, output_changes=None,
             output_codecs_supplied=True):
    selected = _codec() if codec is None else codec
    declarations = (_declaration("source", selected),
                    _declaration("use", selected, consumer_limit=consumer_limit))
    registrations = tuple(declaration.registration() for declaration in declarations)
    if omit_source_codec:
        registrations = (replace(registrations[0], storage_codecs=()), registrations[1])
    if omit_consumer_codec:
        registrations = (registrations[0], replace(registrations[1], storage_codecs=()))
    if output_changes:
        registrations = (replace(registrations[0], outputs=(replace(registrations[0].outputs[0],
                                                                   **output_changes),)), registrations[1])
    draft, _, _ = fixture()
    draft = replace(draft, operations=tuple(replace(operation, selection=registration.selection,
        resource_budget=replace(operation.resource_budget, output_bytes=output_limit if index == 0 else None))
        for index, (operation, registration) in enumerate(zip(draft.operations, registrations, strict=True))))
    registry = CapabilityRegistry("registry.disclosed-storage", tuple(sorted(
        (declaration.manifest() for declaration in declarations), key=lambda value: value.registry_id)))
    return compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit="1" * 40,
        output_codecs={Config.SCHEMA: Config} if output_codecs_supplied else None), declarations


def _request(payload=None, **changes):
    values = dict(logical_artifact_id="artifact.disclosed-codec-fixture",
        relative_path="disclosed/fixture.fixture-bin", payload_schema=SCHEMA,
        profile=ArtifactProfile.RAW_SOURCE_BYTES, media_type=MEDIA,
        publication_scope_id="publication.disclosed-codec-fixture",
        publication_scope_relative_root="disclosed", payload=_framed() if payload is None else payload,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, parent_visibility_ceilings=(),
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    values.update(changes)
    return ArtifactWriteRequest(**values)


def test_local_domain_declaration_projects_its_codec_without_native_or_validation_work():
    codec = _codec(validate_stream=_forbidden)
    declaration = _declaration("source", codec)
    registration = declaration.registration()
    factory = declaration.provider_factory()
    assert registration.storage_codecs == (codec,)
    assert factory.registration.storage_codecs == (codec,)
    assert factory.runner_factory is _forbidden
    assert storage_codec_census((registration, factory.registration)) == (codec,)


@pytest.mark.parametrize("field,value", (
    ("codec_id", ""), ("payload_schema", ""), ("record_version", ""),
    ("profile", "RAW_SOURCE_BYTES"), ("profile", ArtifactProfile.CANONICAL_JSON),
    ("media_type", ""), ("filename_suffix", ""), ("filename_suffix", "../unsafe.bin"),
    ("maximum_bytes", 0), ("maximum_bytes", -1), ("maximum_bytes", True),
    ("maximum_bytes", 1.5), ("maximum_bytes", "128"), ("validate_stream", None),
    ("validate_stream", "module:validator"), ("validate_stream", len),
))
def test_cold_codec_contract_refuses_untyped_or_unsafe_fields(field, value):
    with pytest.raises((TypeError, ValueError)):
        _codec(**{field: value})


def test_cold_codec_contract_refuses_callable_objects_as_code_owned_functions():
    class CallableLabel:
        def __call__(self, source, request, *, size):
            raise AssertionError("callable label was invoked")
    with pytest.raises((TypeError, ValueError)):
        _codec(validate_stream=CallableLabel())


def test_exact_lookup_is_schema_profile_media_and_version_scoped():
    codec = _codec(validate_stream=_forbidden)
    assert resolve_storage_codec((codec,), payload_schema=SCHEMA, profile=codec.profile,
        media_type=MEDIA, record_version=FORMAT_VERSION) is codec
    assert resolve_storage_codec((codec,), payload_schema=SCHEMA, media_type=MEDIA) is codec
    for fields in (
        {"payload_schema": SCHEMA + "-other"}, {"payload_schema": SCHEMA, "profile": ArtifactProfile.MATRIX_ARRAY_NPZ},
        {"payload_schema": SCHEMA, "media_type": "application/x-npz"},
        {"payload_schema": SCHEMA, "record_version": "2.0.0"},
    ):
        assert resolve_storage_codec((codec,), **fields) is None


def test_ambiguous_lookup_and_conflicting_census_refuse_without_calling_callbacks():
    first = _codec(validate_stream=_forbidden)
    other_profile = _codec(codec_id="testing.storage.other-profile", profile=ArtifactProfile.MATRIX_ARRAY_NPZ)
    with pytest.raises(ValueError):
        resolve_storage_codec((first, other_profile), payload_schema=SCHEMA, media_type=MEDIA)
    registration = _declaration("source", first).registration()
    conflict = replace(first, maximum_bytes=MAXIMUM_BYTES + 1)
    with pytest.raises(ValueError):
        storage_codec_census((registration, replace(registration, storage_codecs=(conflict,))))


@pytest.mark.parametrize("output_limit,expected", ((None, 128), (7, 7), (1000, 128)))
def test_arbitrary_registered_domain_binary_reaches_the_shared_compiler_and_bound(output_limit, expected):
    compiled, declarations = _compile(output_limit=output_limit)
    operand, = (edge for edge in compiled.template.graph.edges if edge.edge_id == "edge.operand")
    assert (operand.producer_node_id, operand.producer_output_id,
        operand.consumer_node_id, operand.consumer_input_id) == ("source", "result", "use", "operand")
    assert operand.scientific_role is ScientificInputRole.HISTORY
    assert operand.payload_schema == SCHEMA
    assert operand.maximum_size_bytes == expected
    consumer = next(task for task in compiled.execution_plan.tasks if task.task_id == "use")
    selected, = (edge for edge in consumer.scientific_inputs if edge.edge_id == operand.edge_id)
    assert selected.scientific_role is ScientificInputRole.HISTORY
    assert selected.producer_task_id == "source" and selected.consumer_input_id == "operand"
    assert selected.payload_schema == SCHEMA
    assert selected.maximum_size_bytes == expected
    assert compiled.template.protocol.steps[0].resource_budget.output_bytes == output_limit
    assert storage_codec_census(tuple(declaration.registration() for declaration in declarations)) == (_codec(),)


def test_registered_binary_contract_can_be_unbounded_without_an_invented_transport_ceiling():
    compiled, _ = _compile(codec=_codec(maximum_bytes=None), consumer_limit=None)
    operand, = (edge for edge in compiled.template.graph.edges if edge.edge_id == "edge.operand")
    assert operand.scientific_role is ScientificInputRole.HISTORY
    assert operand.payload_schema == SCHEMA
    assert operand.maximum_size_bytes is None


def test_unbounded_registered_codec_streams_a_larger_body_without_a_hidden_shared_limit(tmp_path):
    payload = _framed(bytes(range(256)) * 2)
    assert len(payload) > MAXIMUM_BYTES
    request = _request(payload)
    registry = ArtifactProfileValidatorRegistry(binary_codecs=(_codec(maximum_bytes=None),))
    registry.validate(request)
    path = tmp_path / "larger-disclosed-body.blob"
    path.write_bytes(payload)
    registry.validate_file(path, request)


def test_unregistered_binary_output_refuses_even_when_consumer_declares_its_codec():
    with pytest.raises(ValueError):
        _compile(omit_source_codec=True)


def test_omitting_optional_json_codecs_cannot_bypass_binary_registration_refusal():
    with pytest.raises(ValueError):
        _compile(omit_source_codec=True, output_limit=7, output_codecs_supplied=False)


def test_a_json_record_codec_cannot_substitute_for_an_unregistered_binary_profile():
    draft, registrations, registry = fixture()
    source = replace(registrations[0], outputs=(replace(registrations[0].outputs[0],
        profile=ArtifactProfile.RAW_SOURCE_BYTES),))
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=draft, registrations=(source, registrations[1]), registry=registry,
            implementation_commit="1" * 40, output_codecs={Config.SCHEMA: Config})


def test_direct_factory_cannot_substitute_a_json_codec_for_an_unregistered_binary_profile():
    _, registrations, registry = fixture()
    registration = replace(registrations[0], outputs=(replace(registrations[0].outputs[0],
        profile=ArtifactProfile.RAW_SOURCE_BYTES),))
    manifest = registry.resolve(registration.selection.capability_key, registration.selection.capability_version)
    binding = recursive_operation_binding(registration=registration, manifest=manifest)
    with pytest.raises(ValueError):
        RecursiveOperationProviderFactory(binding, registration, manifest, _forbidden,
                                          {Config.SCHEMA: Config})


def test_binary_consumer_requires_its_own_descriptor_even_with_a_registered_producer():
    with pytest.raises(ValueError):
        _compile(omit_consumer_codec=True, output_limit=7)


def test_direct_factory_requires_the_binary_input_descriptor_at_cold_construction():
    declaration = _declaration("use", _codec(validate_stream=_forbidden))
    registration = replace(declaration.registration(), storage_codecs=())
    manifest = declaration.manifest()
    binding = recursive_operation_binding(registration=registration, manifest=manifest)
    with pytest.raises(ValueError):
        RecursiveOperationProviderFactory(binding, registration, manifest, _forbidden,
                                          declaration.record_codecs)


@pytest.mark.parametrize("json_record_masquerade", (False, True))
def test_external_binary_input_requires_the_consumer_descriptor(json_record_masquerade):
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink

    codec = _codec(payload_schema=Config.SCHEMA) if json_record_masquerade else _codec()
    declaration = _declaration("use", codec)
    registration = replace(declaration.registration(), storage_codecs=())
    original, _, _ = fixture()
    external = RecursiveExternalInput("input.unregistered-disclosed", "artifact.unregistered-disclosed",
        codec.payload_schema, codec.media_type, 7, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, sha256(b"fixture").hexdigest())
    operation = replace(original.operations[1], selection=registration.selection,
                        resource_budget=replace(BUDGET, output_bytes=None))
    draft = replace(original, draft_id="draft.unregistered-external-binary", requirements=(), connections=(),
        suppliers=(), operations=(operation,), external_inputs=(external,), links=(
            RecursiveInputLink("edge.unregistered-source", "use", "operand",
                external_input_id=external.input_id, scientific_role="SOURCE"),),
        selected_operation_ids=("use",))
    registry = CapabilityRegistry("registry.unregistered-external-binary", (declaration.manifest(),))
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=draft, registrations=(registration,), registry=registry,
            implementation_commit="1" * 40, output_codecs={Config.SCHEMA: Config})


@pytest.mark.parametrize("output_changes", (
    {"payload_schema": SCHEMA + "-other"}, {"profile": ArtifactProfile.MATRIX_ARRAY_NPZ},
    {"media_type": "application/x-npz"},
))
def test_registered_binary_output_cannot_change_any_exact_transport_coordinate(output_changes):
    with pytest.raises(ValueError):
        _compile(output_changes=output_changes)


def test_declared_maximum_still_must_fit_a_tighter_consumer_contract():
    with pytest.raises(ValueError, match="incompatible with registered port"):
        _compile(consumer_limit=127)


def test_default_artifact_registry_does_not_admit_an_arbitrary_raw_binary_schema():
    with pytest.raises((ValueError, RuntimeError)):
        ArtifactProfileValidatorRegistry().validate(_request())


def test_explicit_codec_structural_validator_handles_memory_and_file_paths(tmp_path):
    calls = []
    def recorded(source, request, *, size):
        calls.append((request.payload_schema, request.profile, request.media_type, size))
        return _validate_fixture_stream(source, request, size=size)
    registry = ArtifactProfileValidatorRegistry(binary_codecs=(_codec(validate_stream=recorded),))
    request = _request()
    registry.validate(request)
    path = tmp_path / "fixture.fixture-bin"
    path.write_bytes(request.payload)
    registry.validate_file(path, request)
    assert calls == [(SCHEMA, ArtifactProfile.RAW_SOURCE_BYTES, MEDIA, len(request.payload))] * 2


@pytest.mark.parametrize("damage", ("header", "truncated", "length", "payload", "footer", "trailing"))
def test_registered_stream_validator_refuses_structural_damage_in_both_paths(tmp_path, damage):
    original = _framed()
    if damage == "header":
        changed = bytes((original[0] ^ 1,)) + original[1:]
    elif damage == "truncated":
        changed = original[:len(MAGIC) + 2]
    elif damage == "length":
        changed = MAGIC + struct.pack("<I", 1) + original[len(MAGIC) + 4:]
    elif damage == "payload":
        at = len(MAGIC) + 4
        changed = original[:at] + bytes((original[at] ^ 1,)) + original[at + 1:]
    elif damage == "footer":
        changed = original[:-1] + bytes((original[-1] ^ 1,))
    else:
        changed = original + b"unselected trailing bytes"
    request = _request(changed)
    registry = ArtifactProfileValidatorRegistry(binary_codecs=(_codec(),))
    with pytest.raises((ValueError, RuntimeError)):
        registry.validate(request)
    path = tmp_path / "damaged.fixture-bin"
    path.write_bytes(changed)
    with pytest.raises((ValueError, RuntimeError)):
        registry.validate_file(path, request)


@pytest.mark.parametrize("change", (
    {"payload_schema": SCHEMA + "-other"}, {"profile": ArtifactProfile.MATRIX_ARRAY_NPZ},
    {"media_type": "application/x-npz"},
))
def test_mismatched_artifact_contract_refuses_before_selected_validator(change):
    registry = ArtifactProfileValidatorRegistry(binary_codecs=(_codec(validate_stream=_forbidden),))
    with pytest.raises((ValueError, RuntimeError)):
        registry.validate(_request(**change))


def test_declared_codec_limit_refuses_before_structural_callback():
    registry = ArtifactProfileValidatorRegistry(binary_codecs=(
        _codec(maximum_bytes=8, validate_stream=_forbidden),))
    with pytest.raises((ValueError, RuntimeError)):
        registry.validate(_request())


@pytest.mark.parametrize("result", (True, False, "VALIDATED", b"validated", object()))
def test_structural_callback_must_return_none_or_raise_instead_of_a_proof_label(result):
    def labelled(_source, _request, *, size):
        return result
    registry = ArtifactProfileValidatorRegistry(binary_codecs=(_codec(validate_stream=labelled),))
    with pytest.raises((ValueError, RuntimeError)):
        registry.validate(_request())


def test_exact_callback_refusal_propagates_without_a_fallback():
    refusal = ValueError("independent structural refusal")
    def refuse(_source, _request, *, size):
        raise refusal
    registry = ArtifactProfileValidatorRegistry(binary_codecs=(_codec(validate_stream=refuse),))
    with pytest.raises(ValueError) as observed:
        registry.validate(_request())
    assert observed.value is refusal


def test_fixture_structural_validator_independently_checks_a_literal_exact_frame():
    # The expected length and footer are independent known bytes, not a mirror
    # of a production domain encoder. SHA256("abc") is its published test vector.
    literal = MAGIC + b"\x03\x00\x00\x00abc" + bytes.fromhex(
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
    assert _validate_fixture_stream(BytesIO(literal), _request(literal), size=len(literal)) is None


def test_public_operation_census_uses_local_factories_without_invoking_their_runners(monkeypatch):
    from empirical_lawhood.api import recursive_operations

    codec = _codec(validate_stream=_forbidden)
    factories = tuple(_declaration(node, codec).provider_factory() for node in ("source", "use"))
    monkeypatch.setattr(recursive_operations, "operation_factories", lambda: factories)
    assert recursive_operations.operation_storage_codecs() == (codec,)
    registrations, registry, record_codecs = recursive_operations.operation_catalog()
    assert {row.selection.capability_key for row in registrations} == {"testing.storage.source", "testing.storage.use"}
    assert len(registry.capabilities) == 2
    assert record_codecs[Config.SCHEMA] is Config


def test_registered_arbitrary_binary_crosses_real_guarded_stream_custody_and_manifest_read(tmp_path):
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
    from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
    from tests.test_recursive_public_service import _plane

    calls = []
    def recorded(source, request, *, size):
        calls.append(size)
        return _validate_fixture_stream(source, request, size=size)
    registry = ArtifactProfileValidatorRegistry(binary_codecs=(_codec(validate_stream=recorded),))
    base = _plane(tmp_path / "explicit-disclosed-custody")
    plane = ExternalArtifactPlane(base.root, validators=registry)
    request = _request()
    result = plane.write_stream(request.as_stream())
    assert result.logical.payload_schema == SCHEMA
    assert result.logical.profile is ArtifactProfile.RAW_SOURCE_BYTES
    assert result.logical.content_sha256 == sha256(request.payload).hexdigest()
    assert result.materialization.size_bytes == len(request.payload)
    assert (tmp_path / "explicit-disclosed-custody" / request.relative_path).read_bytes() == request.payload
    manifest_path = tmp_path / "explicit-disclosed-custody" / (request.relative_path + ".manifest.json")
    plane.verify_manifest(decode_artifact_manifest(manifest_path.read_bytes()))
    assert len(calls) >= 2 and set(calls) == {len(request.payload)}


@pytest.mark.parametrize("transport", ("npz", "framed"))
def test_default_registry_has_no_implicit_matrix_binary_allowance(transport):
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_FRAMED_CODEC, MATRIX_NPZ_CODEC
    from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
    import numpy as np

    if transport == "npz":
        codec = MATRIX_NPZ_CODEC
        payload, _ = encode_matrix_arrays({"samples": np.asarray((1., -0., 3.), dtype="<f8")})
    else:
        codec, payload = MATRIX_FRAMED_CODEC, b"disclosed opaque framed fixture bytes"
    request = _request(payload, payload_schema=codec.payload_schema, profile=codec.profile,
                       media_type=codec.media_type)
    with pytest.raises((ValueError, RuntimeError)):
        ArtifactProfileValidatorRegistry().validate(request)


@pytest.mark.parametrize("transport", ("npz", "framed"))
def test_known_matrix_labels_do_not_exempt_an_unregistered_binary_compiler_output(transport):
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_FRAMED_CODEC, MATRIX_NPZ_CODEC

    codec = MATRIX_NPZ_CODEC if transport == "npz" else MATRIX_FRAMED_CODEC
    with pytest.raises(ValueError):
        _compile(codec=codec, consumer_limit=None, omit_source_codec=True)


@pytest.mark.parametrize("output_limit", (None, 4096, 128 * 1024**2))
def test_registered_matrix_npz_keeps_its_original_exact_closed_byte_limit(output_limit):
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_NPZ_CODEC
    from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES

    assert MATRIX_NPZ_CODEC.maximum_bytes == MAXIMUM_MATRIX_ARRAY_BYTES
    compiled, _ = _compile(codec=MATRIX_NPZ_CODEC, output_limit=output_limit,
                           consumer_limit=MAXIMUM_MATRIX_ARRAY_BYTES)
    expected = MAXIMUM_MATRIX_ARRAY_BYTES if output_limit is None else min(output_limit, MAXIMUM_MATRIX_ARRAY_BYTES)
    operand, = (edge for edge in compiled.template.graph.edges if edge.edge_id == "edge.operand")
    assert operand.scientific_role is ScientificInputRole.HISTORY
    assert operand.payload_schema == MATRIX_NPZ_CODEC.payload_schema
    assert operand.maximum_size_bytes == expected


def test_registered_matrix_npz_cannot_raise_its_closed_limit_by_using_the_callback_directly():
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_NPZ_CODEC
    from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES

    request = _request(b"", payload_schema=MATRIX_NPZ_CODEC.payload_schema,
                       profile=MATRIX_NPZ_CODEC.profile, media_type=MATRIX_NPZ_CODEC.media_type)
    with pytest.raises((ValueError, RuntimeError)):
        MATRIX_NPZ_CODEC.validate_stream(BytesIO(b""), request, size=MAXIMUM_MATRIX_ARRAY_BYTES + 1)


@pytest.mark.parametrize("fields", (
    {"payload_schema": False}, {"payload_schema": SCHEMA, "profile": "RAW_SOURCE_BYTES"},
    {"payload_schema": SCHEMA, "profile": False}, {"payload_schema": SCHEMA, "media_type": False},
    {"payload_schema": SCHEMA, "record_version": False},
))
def test_lookup_rejects_untyped_selection_coordinates_instead_of_treating_them_as_absent(fields):
    with pytest.raises((TypeError, ValueError)):
        resolve_storage_codec((_codec(),), **fields)


@pytest.mark.parametrize("changes", (
    {"payload_schema": SCHEMA + "-other"}, {"profile": ArtifactProfile.MATRIX_ARRAY_NPZ},
    {"media_type": "application/x-npz"},
))
def test_cold_declaration_refuses_changed_output_contract_before_native_or_structural_work(changes):
    declaration = _declaration("source", _codec(validate_stream=_forbidden))
    with pytest.raises(ValueError):
        replace(declaration, outputs=(replace(declaration.outputs[0], **changes),))


def test_cold_binary_consumer_requires_its_own_exact_declared_codec():
    declaration = _declaration("use", _codec(validate_stream=_forbidden))
    with pytest.raises(ValueError):
        replace(declaration, storage_codecs=())


@pytest.mark.parametrize("fields", (
    {"record_version": "2.0.0"}, {"maximum_bytes": MAXIMUM_BYTES + 1},
    {"media_type": "application/vnd.disclosed.fixture"},
))
def test_producing_validator_stamp_preserves_current_codec_revision_media_and_limit(fields, tmp_path):
    producing = ArtifactProfileValidatorRegistry(binary_codecs=(_codec(),)).generic_validation(
        profile=ArtifactProfile.RAW_SOURCE_BYTES, payload_schema=SCHEMA)
    codec = _codec(**fields)
    current = ArtifactProfileValidatorRegistry(binary_codecs=(codec,))
    written_now = current.generic_validation(profile=ArtifactProfile.RAW_SOURCE_BYTES, payload_schema=SCHEMA)
    assert written_now != producing
    # Disclosed provenance from another producing implementation, not a listed
    # predecessor or permission to skip the current decoder/contract.
    observed = replace(producing, validator_version="0.9.0",
        validator_implementation_sha256=sha256(b"disclosed independently producing validator source").hexdigest())
    assert current.require_generic_validation(observed) is observed
    assert current.generic_validation(profile=ArtifactProfile.RAW_SOURCE_BYTES, payload_schema=SCHEMA) == written_now

    request = _request()
    path = tmp_path / "current-contract.blob"
    path.write_bytes(request.payload)
    if "media_type" in fields:
        # A producing stamp cannot make the original, now-unregistered media
        # enter the decoder registered for a different actual wire format.
        assert resolve_storage_codec(current.binary_codecs, payload_schema=SCHEMA,
            profile=request.profile, media_type=request.media_type) is None
        with pytest.raises((ValueError, RuntimeError)):
            current.validate(request)
        with pytest.raises((ValueError, RuntimeError)):
            current.validate_file(path, request)
        return

    current.validate(request)
    current.validate_file(path, request)
    if "record_version" in fields:
        # This framed format has no embedded version field. Exact typed member
        # revision lookup, rather than a validator source hash, binds its reader.
        assert resolve_storage_codec(current.binary_codecs, payload_schema=SCHEMA,
            profile=request.profile, media_type=request.media_type, record_version=FORMAT_VERSION) is None
        assert resolve_storage_codec(current.binary_codecs, payload_schema=SCHEMA,
            profile=request.profile, media_type=request.media_type, record_version=codec.record_version) is codec
    else:
        oversized = _request(_framed(b"x" * codec.maximum_bytes))
        assert len(oversized.payload) > codec.maximum_bytes
        path.write_bytes(oversized.payload)
        with pytest.raises((ValueError, RuntimeError), match="byte contract"):
            current.validate(oversized)
        with pytest.raises((ValueError, RuntimeError), match="byte contract"):
            current.validate_file(path, oversized)


def test_same_schema_profile_keeps_current_media_guards_independent_of_producing_codec_roster(tmp_path):
    calls = []
    def first(source, request, *, size):
        calls.append(("first", request.media_type))
        return _validate_fixture_stream(source, request, size=size)
    def second(source, request, *, size):
        calls.append(("second", request.media_type))
        return _validate_other_fixture_stream(source, request, size=size)
    codecs = (_codec(validate_stream=first), _codec(codec_id="testing.storage.other-media",
        media_type=OTHER_MEDIA, validate_stream=second))
    registry = ArtifactProfileValidatorRegistry(binary_codecs=codecs)
    first_request = _request()
    body = b"independent second wire format"
    second_payload = OTHER_MAGIC + struct.pack("<I", len(body)) + body + sha256(body).digest()
    second_request = _request(second_payload, media_type=OTHER_MEDIA)
    for ordinal, request in enumerate((first_request, second_request)):
        assert resolve_storage_codec(codecs, payload_schema=SCHEMA, profile=request.profile,
                                     media_type=request.media_type) is codecs[ordinal]
        registry.validate(request)
        path = tmp_path / ("format-" + str(ordinal) + ".blob")
        path.write_bytes(request.payload)
        registry.validate_file(path, request)
    assert calls == [("first", MEDIA), ("first", MEDIA), ("second", OTHER_MEDIA), ("second", OTHER_MEDIA)]
    with pytest.raises(ValueError, match="ambiguous"):
        resolve_storage_codec(codecs, payload_schema=SCHEMA, profile=ArtifactProfile.RAW_SOURCE_BYTES)
    with pytest.raises(ValueError, match="magic header"):
        registry.validate(replace(first_request, media_type=OTHER_MEDIA))
    original = registry.generic_validation(profile=ArtifactProfile.RAW_SOURCE_BYTES, payload_schema=SCHEMA)
    one_format = ArtifactProfileValidatorRegistry(binary_codecs=(codecs[0],))
    changed_second = ArtifactProfileValidatorRegistry(binary_codecs=(codecs[0], replace(codecs[1], record_version="2.0.0")))
    for changed in (one_format, changed_second):
        assert changed.generic_validation(profile=ArtifactProfile.RAW_SOURCE_BYTES, payload_schema=SCHEMA) != original
        assert changed.require_generic_validation(original) is original
        changed.validate(first_request)
        changed.validate_file(tmp_path / "format-0.blob", first_request)
    # Adding an unused format also leaves the supported actual media readable.
    first_only = one_format.generic_validation(profile=ArtifactProfile.RAW_SOURCE_BYTES, payload_schema=SCHEMA)
    assert registry.require_generic_validation(first_only) is first_only
    registry.validate(first_request)
    registry.validate_file(tmp_path / "format-0.blob", first_request)

    # Removing the format being consumed refuses despite accepting producing
    # provenance. Cross-format magic and typed record revisions remain exact.
    with pytest.raises((ValueError, RuntimeError)):
        one_format.validate(second_request)
    with pytest.raises((ValueError, RuntimeError)):
        one_format.validate_file(tmp_path / "format-1.blob", second_request)
    with pytest.raises(ValueError, match="magic header"):
        registry.validate_file(tmp_path / "format-0.blob", replace(first_request, media_type=OTHER_MEDIA))
    assert resolve_storage_codec(changed_second.binary_codecs, payload_schema=SCHEMA,
        profile=ArtifactProfile.RAW_SOURCE_BYTES, media_type=OTHER_MEDIA, record_version=FORMAT_VERSION) is None
    assert resolve_storage_codec(changed_second.binary_codecs, payload_schema=SCHEMA,
        profile=ArtifactProfile.RAW_SOURCE_BYTES, media_type=OTHER_MEDIA, record_version="2.0.0") is changed_second.binary_codecs[1]


@pytest.mark.parametrize("transport", ("framed", "raw-json"))
def test_public_author_and_retained_reader_accept_new_domain_binary_using_its_declaration(tmp_path, monkeypatch, transport):
    from empirical_lawhood.api import recursive_authoring, recursive_operations
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink
    from tests.test_recursive_public_service import _plane

    codec = (_codec() if transport == "framed" else _codec(media_type="application/json",
        validate_stream=_validate_raw_json_fixture_stream))
    declaration = _declaration("use", codec)
    factory = declaration.provider_factory()
    monkeypatch.setattr(recursive_operations, "operation_factories", lambda: (factory,))
    original, _, _ = fixture()
    payload = _framed() if transport == "framed" else b'{ "original" : [1, 2] }\n'
    input_id = "input.disclosed-domain-binary"
    external = RecursiveExternalInput(input_id, "artifact.disclosed-source", SCHEMA, codec.media_type, MAXIMUM_BYTES,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, sha256(payload).hexdigest())
    operation = replace(original.operations[1], selection=factory.registration.selection,
                        resource_budget=replace(BUDGET, output_bytes=None))
    draft = replace(original, draft_id="draft.disclosed-domain-binary", requirements=(), connections=(),
        suppliers=(), operations=(operation,), external_inputs=(external,), links=(
            RecursiveInputLink("edge.disclosed-source", "use", "operand", external_input_id=input_id,
                               scientific_role="SOURCE"),), selected_operation_ids=("use",))
    root = Path(__file__).resolve().parents[2]
    # Retain one actual current source observation for this authoring conformance
    # case. Source changes during real authoring retain their independent guard.
    observed = recursive_authoring.implementation_binding(root)
    monkeypatch.setattr(recursive_authoring, "implementation_binding", lambda _root: observed)
    source_path = tmp_path / "explicit-disclosed-source.blob"
    source_path.write_bytes(payload)
    base = _plane(tmp_path / "explicit-disclosed-public-custody")
    plane = ExternalArtifactPlane(base.root, validators=ArtifactProfileValidatorRegistry(binary_codecs=(codec,)))
    directory = tmp_path / "explicit-disclosed-public-custody" / "authored"
    report = recursive_authoring.author_recursive_wave(draft=draft, project_root=root, artifact_writer=plane,
        output_dir=directory, input_bindings=((input_id, source_path),))
    assert report["native_contact"] == "none" and report["task_count"] == 1
    assert report["scientific_authority"] == "NONE" and report["qualification"] == "NOT_ESTABLISHED"
    packet, retained_draft, retained_source, payloads = recursive_authoring.load_authored_wave(
        directory=directory, artifact_writer=plane)
    members = tuple(member for member in packet.members if member.identity.object_schema == SCHEMA)
    assert len(members) == 1 and members[0].filename.endswith(".blob")
    assert members[0].identity.object_version == FORMAT_VERSION
    assert payloads[members[0].filename] == payload
    assert retained_draft == draft and retained_source == observed
    assert source_path.read_bytes() == payload


@pytest.mark.parametrize("contract", ("missing", "wrong-media", "wrong-profile", "canonical-collision"))
def test_raw_json_input_cannot_bypass_exact_storage_or_canonical_record_contract(contract):
    codec = _codec(media_type="application/json", validate_stream=_forbidden)
    declaration = _declaration("use", codec)
    if contract == "missing":
        changes = {"storage_codecs": ()}
    elif contract == "wrong-media":
        changes = {"storage_codecs": (_codec(validate_stream=_forbidden),)}
    elif contract == "wrong-profile":
        changes = {"storage_codecs": (replace(codec, profile=ArtifactProfile.MATRIX_ARRAY_NPZ),)}
    else:
        changes = {"input_ports": (replace(declaration.input_ports[0], payload_schema=Config.SCHEMA),),
            "storage_codecs": (replace(codec, payload_schema=Config.SCHEMA),)}
    with pytest.raises(ValueError, match="strict record codec|ambiguously"):
        replace(declaration, **changes)


def test_raw_json_codec_cannot_change_another_registered_operations_canonical_meaning():
    from empirical_lawhood.runtime.recursive_record_codecs import input_record_type_census

    class CanonicalMeaning(Config):
        SCHEMA = globals()["SCHEMA"]

    raw = _declaration("use", _codec(media_type="application/json", validate_stream=_forbidden)).registration()
    with pytest.raises(ValueError, match="raw JSON storage conflicts"):
        input_record_type_census((raw,), legacy_codecs={SCHEMA: CanonicalMeaning})
    # The existing distinct-media physical contract remains separate.
    binary = _declaration("use", _codec(validate_stream=_forbidden)).registration()
    assert input_record_type_census((binary,), legacy_codecs={SCHEMA: CanonicalMeaning}) == (CanonicalMeaning,)
