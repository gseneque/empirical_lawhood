# SPDX-License-Identifier: MPL-2.0
"""Closed generated operation selection; document values never supply imports."""

from functools import lru_cache
from importlib import import_module
from types import MappingProxyType

from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.study_authoring import CapabilitySelection
from empirical_lawhood.storage.contracts.record_codecs import OperationOutputRecordBinding, RecordCodecCatalog


class UnknownOperationSelection(ValueError):
    """A selected key is absent from the installed closed factory roster."""


def _generated():
    from empirical_lawhood.adapters.composition import generated_recursive_operations
    return generated_recursive_operations


def _resolve(module, name):
    value = import_module(module)
    for part in name.split('.'):
        value = getattr(value, part)
    return value


class OperationRecordCodecs(RecordCodecCatalog):
    """Complete exact revisions and producers, resolving only requested types."""

    def __init__(self, rows, output_selections=()):
        self._rows = MappingProxyType({(schema, version): (module, name)
            for schema, version, module, name in rows})
        if len(self._rows) != len(rows):
            raise ValueError('generated operation codecs repeat a schema/revision')
        bindings = tuple(OperationOutputRecordBinding(CapabilitySelection(capability, capability_version, implementation),
            schema, version) for capability, capability_version, implementation, schema, version in output_selections)
        self._initialize(tuple(self._rows), bindings)

    def _record_type(self, key):
        module, name = self._rows[key]
        kind = _resolve(module, name)
        if (not isinstance(kind, type) or not issubclass(kind, CanonicalRecord)
                or (kind.SCHEMA, kind.VERSION) != key):
            raise ValueError('selected operation codec differs from its generated schema/revision')
        return kind


@lru_cache(maxsize=1)
def operation_record_codecs():
    index = _generated()
    return OperationRecordCodecs(index.OUTPUT_RECORD_TYPES, index.OUTPUT_CODEC_SELECTIONS)


@lru_cache(maxsize=1)
def operation_registry():
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes_with_identity
    from empirical_lawhood.execution.capabilities import CapabilityRegistry
    index = _generated()
    return decode_canonical_bytes_with_identity(index.REGISTRY_BYTES, CapabilityRegistry,
        maximum_bytes=len(index.REGISTRY_BYTES), expected_sha256=index.REGISTRY_SHA256).record


def selected_factories(selection_ids):
    """Resolve exact code-owned keys and check the selected live descriptor."""
    from empirical_lawhood.execution.recursive_provider import RecursiveOperationProviderFactory
    from empirical_lawhood.execution.extensions import descriptor_projection
    index = _generated()
    by_selection = {row[0]: row[1:] for row in index.OPERATIONS}
    selected = tuple(sorted(set(selection_ids)))
    factories = []
    inputs = {(schema, version): (module, name) for schema, version, module, name in index.INPUT_RECORD_TYPES}
    for selection in selected:
        try:
            module, binding_id, binding_sha256, manifest_sha256 = by_selection[selection]
        except KeyError as error:
            raise UnknownOperationSelection('selected operation lacks its installed executable factory') from error
        matches = tuple(factory for factory in descriptor_projection(import_module(module), "EXECUTABLE_BINDING_FACTORIES", ())
            if factory.binding.binding_id == binding_id)
        if len(matches) != 1 or not isinstance(matches[0], RecursiveOperationProviderFactory):
            raise ValueError('selected operation changes its generated factory census')
        factory = matches[0]
        if (factory.registration.selection.selection_id != selection
                or factory.binding.fingerprint() != binding_sha256
                or factory.manifest.fingerprint() != manifest_sha256):
            raise ValueError('selected operation differs from its generated binding and manifest')
        codecs = operation_record_codecs()
        for schema, kind in factory.output_codecs.items():
            if codecs.resolve(schema, kind.VERSION) is not kind:
                raise ValueError('registered recursive factories disagree on a strict output codec')
        from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
        for output in factory.registration.outputs:
            if (output.profile is ArtifactProfile.CANONICAL_JSON
                    and codecs.for_operation(factory.registration.selection, output.payload_schema)
                    is not factory.output_codecs[output.payload_schema]):
                raise ValueError('selected producer differs from its generated exact output revision')
        for kind in factory.registration.input_record_types:
            location = inputs.get((kind.SCHEMA, kind.VERSION))
            if location is None or _resolve(*location) is not kind:
                raise ValueError('registered operations disagree on one strict input schema/revision codec')
        factories.append(factory)
    return tuple(factories)


@lru_cache(maxsize=1)
def operation_storage_codecs():
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
    from empirical_lawhood.storage.contracts.recursive_storage_codecs import RecursiveStorageCodec, validate_storage_codecs
    return validate_storage_codecs(tuple(RecursiveStorageCodec(
        codec_id, schema, version, ArtifactProfile(profile), media, suffix,
        _resolve(module, name), maximum_bytes, allow_empty) for
        codec_id, schema, version, profile, media, suffix, module, name, maximum_bytes, allow_empty
        in _generated().STORAGE_CODECS))
