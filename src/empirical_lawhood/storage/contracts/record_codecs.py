# SPDX-License-Identifier: MPL-2.0
"""Exact installed record revisions and explicitly selected output producers.

An envelope can select an installed decoder. It cannot select a producer,
change an original output contract, import code or choose a newer revision.
"""

from collections.abc import Mapping
from dataclasses import dataclass
import json
from types import MappingProxyType

from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_schema, validate_semantic_version
from empirical_lawhood.design.study_authoring import CapabilitySelection


RecordKey = tuple[str, str]


class UnsupportedRecordRevision(ValueError):
    """The selected exact revision is unavailable; no implicit conversion exists."""


class AmbiguousRecordRevision(ValueError):
    """A schema alone cannot select among several installed revisions."""


@dataclass(frozen=True, slots=True)
class OperationOutputRecordBinding:
    """Runtime-only projection from one installed producer to its output revision."""

    selection: CapabilitySelection
    record_schema: str
    record_version: str

    def __post_init__(self):
        if type(self.selection) is not CapabilitySelection:
            raise TypeError('output record binding requires its exact capability selection')
        self.selection.__post_init__()
        validate_schema(self.record_schema)
        validate_semantic_version(self.record_version)

    @property
    def key(self):
        return self.selection.selection_id, self.selection.implementation_sha256, self.record_schema


class RecordCodecCatalog(Mapping):
    """Immutable complete decoder census, with optional exact producer bindings.

    A unique schema keeps its historical string lookup. A family with multiple
    revisions exposes exact tuple keys and refuses schema-only lookup. Iteration
    therefore retains every decoder without inventing a default revision.
    """

    def __init__(self, record_types, *, output_bindings=()):
        if isinstance(record_types, Mapping):
            for key, kind in record_types.items():
                if (not isinstance(kind, type) or not issubclass(kind, CanonicalRecord)
                        or key not in (kind.SCHEMA, (kind.SCHEMA, kind.VERSION))):
                    raise ValueError('record codec mapping changes its exact schema/revision key')
        kinds = record_types.values() if isinstance(record_types, Mapping) else record_types
        exact = {}
        for kind in kinds:
            if not isinstance(kind, type) or not issubclass(kind, CanonicalRecord):
                raise TypeError('record codec census requires code-owned canonical types')
            key = kind.SCHEMA, kind.VERSION
            if exact.setdefault(key, kind) is not kind:
                raise ValueError('installed codecs disagree on one exact record schema/revision')
        self._types = MappingProxyType(exact)
        self._initialize(tuple(exact), output_bindings)

    def _initialize(self, record_keys, output_bindings):
        """Allow the API's closed generated index to retain lazy type loading."""
        keys = tuple(sorted(record_keys))
        if len(set(keys)) != len(keys):
            raise ValueError('record codec census repeats an exact schema/revision')
        versions = {}
        for schema, version in keys:
            validate_schema(schema)
            validate_semantic_version(version)
            versions.setdefault(schema, []).append(version)
        self._record_keys = frozenset(keys)
        self._versions = MappingProxyType({schema:tuple(values) for schema, values in versions.items()})
        self._lookup_keys = tuple(schema if len(versions[schema]) == 1 else (schema, version)
            for schema, version in keys)
        output_bindings = tuple(output_bindings)
        self._output_binding_records = output_bindings
        selected = {}
        producer_keys = set()
        for binding in output_bindings:
            if type(binding) is not OperationOutputRecordBinding:
                raise TypeError('producer codec selection requires its typed binding')
            binding.__post_init__()
            record_key = binding.record_schema, binding.record_version
            if record_key not in self._record_keys:
                raise ValueError('selected producer output lacks its installed exact decoder')
            if selected.setdefault(binding.key, record_key) != record_key:
                raise ValueError('one selected producer advertises conflicting output revisions')
            producer_keys.add(binding.selection.capability_key)
        self._output_bindings = MappingProxyType(selected)
        self._producer_keys = frozenset(producer_keys)

    @property
    def output_selection_keys(self):
        return tuple(sorted(self._output_bindings.items()))

    def with_record_types(self, record_types):
        return RecordCodecCatalog((*self.values(), *record_types), output_bindings=self._output_binding_records)

    def __len__(self):
        return len(self._lookup_keys)

    def __iter__(self):
        return iter(self._lookup_keys)

    def _record_type(self, key):
        return self._types[key]

    def versions(self, schema):
        return self._versions.get(schema, ())

    def __getitem__(self, key):
        if isinstance(key, str):
            versions = self.versions(key)
            if not versions:
                raise KeyError(key)
            if len(versions) != 1:
                raise AmbiguousRecordRevision(
                    f'record schema {key} requires an exact revision; installed revisions: {", ".join(versions)}')
            key = key, versions[0]
        if (type(key) is not tuple or len(key) != 2 or any(type(value) is not str for value in key)
                or key not in self._record_keys):
            raise KeyError(key)
        kind = self._record_type(key)
        if (not isinstance(kind, type) or not issubclass(kind, CanonicalRecord)
                or (kind.SCHEMA, kind.VERSION) != key):
            raise ValueError('installed record codec differs from its exact declared schema/revision')
        return kind

    def resolve(self, schema, version):
        try:
            return self[schema, version]
        except KeyError as error:
            supported = ', '.join(self.versions(schema)) or 'none'
            raise UnsupportedRecordRevision(
                f'unsupported record revision {schema}@{version}; installed revisions: {supported}; '
                'select a compatible reader or an explicit retained-record conversion') from error

    def for_operation(self, selection, schema, *, allow_unbound_unique=False):
        if type(selection) is not CapabilitySelection:
            raise TypeError('output decoding requires its original exact capability selection')
        key = selection.selection_id, selection.implementation_sha256, schema
        record_key = self._output_bindings.get(key)
        if record_key is None:
            # Historical nonrecursive owners have no generated producer row.
            # Preserve their sole installed shape only when explicitly requested
            # after authentication. Never substitute a revision for a known owner.
            if (allow_unbound_unique and selection.capability_key not in self._producer_keys
                    and len(self.versions(schema)) == 1):
                return self.resolve(schema, self.versions(schema)[0])
            raise UnsupportedRecordRevision(
                f'no installed output revision for {selection.selection_id}, implementation '
                f'{selection.implementation_sha256}, schema {schema}; select the original compatible reader')
        return self.resolve(*record_key)


def resolve_record_codec(codecs, schema, version):
    """Keep explicit legacy mappings exact while accepting revision catalogues."""
    if isinstance(codecs, RecordCodecCatalog):
        return codecs.resolve(schema, version)
    kind = codecs.get((schema, version))
    if kind is None:
        kind = codecs.get(schema)
    if kind is None or (kind.SCHEMA, kind.VERSION) != (schema, version):
        supported = sorted({kind.VERSION for kind in codecs.values() if kind.SCHEMA == schema})
        raise UnsupportedRecordRevision(
            f'unsupported record revision {schema}@{version}; installed revisions: {", ".join(supported) or "none"}')
    return kind


def snapshot_record_codecs(codecs):
    """Retain immutable producer bindings when a runtime captures its decoders."""
    return codecs if isinstance(codecs, RecordCodecCatalog) else MappingProxyType(dict(codecs))


def resolve_operation_output_codec(codecs, selection, schema, *, allow_unbound_unique=False):
    """Use the original selected producer; a global newer decoder is irrelevant."""
    if isinstance(codecs, RecordCodecCatalog):
        return codecs.for_operation(selection, schema, allow_unbound_unique=allow_unbound_unique)
    selected = codecs.get(schema)
    if selected is not None:
        if selected.SCHEMA != schema:
            raise ValueError('selected output codec changes its declared schema')
        return selected
    # Old explicitly composed mappings select one codec themselves. A copied
    # multi-revision census cannot recover its lost producer bindings by guess.
    matches = {kind for kind in codecs.values() if kind.SCHEMA == schema}
    if len(matches) != 1:
        raise UnsupportedRecordRevision(
            f'output {schema} requires the exact codec binding of {selection.selection_id}; '
            'retain the installed producer catalogue instead of a schema-only copy')
    return next(iter(matches))


def record_envelope_key(payload, *, expected_schema):
    """Inspect only a bounded caller-owned body; strict decoding still follows."""
    def pairs(values):
        result = {}
        for name, value in values:
            if name in result:
                raise ValueError('record envelope contains a duplicate key')
            result[name] = value
        return result
    try:
        document = json.loads(payload, object_pairs_hook=pairs)
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('record lacks a supported canonical envelope') from error
    if (type(document) is not dict or set(document) != {'schema', 'version', 'value'}
            or document['schema'] != expected_schema or type(document['version']) is not str):
        raise ValueError('record changes its selected schema/revision envelope')
    validate_semantic_version(document['version'])
    return expected_schema, document['version']


__all__ = ['AmbiguousRecordRevision', 'OperationOutputRecordBinding', 'RecordCodecCatalog',
           'UnsupportedRecordRevision', 'record_envelope_key', 'resolve_operation_output_codec', 'resolve_record_codec',
           'snapshot_record_codecs']
