# SPDX-License-Identifier: MPL-2.0
"""Closed revision selection for operation inputs, separate from output codecs."""

import json

from empirical_lawhood.kernel.serialization import CanonicalRecord


def validate_input_record_types(record_types):
    if (type(record_types) is not tuple or any(not isinstance(kind, type)
            or not issubclass(kind, CanonicalRecord) for kind in record_types)):
        raise TypeError('operation input codecs require immutable code-owned record types')
    keys = tuple((kind.SCHEMA, kind.VERSION) for kind in record_types)
    if keys != tuple(sorted(set(keys))):
        raise ValueError('operation input codecs need sorted unique exact schema/revision identities')
    return record_types


def input_record_type_census(registrations, *, legacy_codecs):
    """Refuse ambiguous installed meanings for one exact schema and revision."""
    by_key = {(kind.SCHEMA, kind.VERSION): kind for kind in legacy_codecs.values()}
    for registration in registrations:
        for kind in validate_input_record_types(registration.input_record_types):
            key = kind.SCHEMA, kind.VERSION
            if by_key.setdefault(key, kind) is not kind:
                raise ValueError('registered operations disagree on one strict input schema/revision codec')
    from .artifacts import is_canonical_json_media_type
    canonical_schemas = {schema for schema, _ in by_key}
    if any(codec.payload_schema in canonical_schemas and is_canonical_json_media_type(codec.media_type)
           for registration in registrations for codec in registration.storage_codecs):
        raise ValueError('registered raw JSON storage conflicts with a strict canonical record schema')
    return tuple(by_key[key] for key in sorted(by_key))


def _input_consumers(draft, external, registrations):
    selected = set(draft.selected_operation_ids)
    operations = {row.node_id: row for row in draft.operations}
    by_selection = {row.selection.selection_id: row for row in registrations}
    consumers = {link.consumer_node_id for link in draft.links
        if link.consumer_node_id in selected and link.external_input_id == external.input_id}
    if not consumers:
        raise ValueError('operation input lacks its selected declared consumer')
    return tuple(by_selection[operations[node].selection.selection_id] for node in sorted(consumers))


def requires_declared_input_record(*, draft, external, registrations):
    return any(kind.SCHEMA == external.payload_schema
        for row in _input_consumers(draft, external, registrations) for kind in row.input_record_types)


def validate_declared_recursive_input_payload(*, draft, registrations, fallback_codecs,
                                             logical_artifact_id, payload):
    """Enforce explicitly declared record revisions before publication or delivery.

    Historical externally qualified source formats without a record declaration
    retain their own source validators. Their JSON media type alone does not
    impose a new canonical record envelope or scientific revision.
    """
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.runtime.artifacts import is_canonical_json_media_type

    for external in draft.external_inputs:
        if external.logical_artifact_id != logical_artifact_id or external.parent_substitution:
            continue
        selected = any(link.external_input_id == external.input_id
            and link.consumer_node_id in draft.selected_operation_ids for link in draft.links)
        if not selected:
            continue
        if not requires_declared_input_record(draft=draft, external=external, registrations=registrations):
            continue
        if not is_canonical_json_media_type(external.media_type):
            raise ValueError('declared canonical input record changes its JSON media contract')
        codec = resolve_recursive_input_codec(draft=draft, external=external,
            registrations=registrations, fallback_codecs=fallback_codecs, payload=payload)
        decode_canonical_bytes(payload, codec, maximum_bytes=external.maximum_size_bytes)


def resolve_recursive_input_codec(*, draft, external, registrations, fallback_codecs, payload):
    """Select one declared revision accepted by every selected input consumer.

    Envelope values select among installed types only. The caller must still
    perform strict canonical decoding, exact byte authentication and the domain
    source/role/cutoff checks. No input decoder enters the global output census.
    """
    try:
        envelope = json.loads(payload)
    except (ValueError, TypeError, UnicodeDecodeError) as error:
        raise ValueError('operation input lacks its canonical record envelope') from error
    if (not isinstance(envelope, dict) or envelope.get('schema') != external.payload_schema
            or type(envelope.get('version')) is not str):
        raise ValueError('operation input substitutes its declared schema/revision envelope')
    revision = envelope['version']
    resolved = None
    for registration in _input_consumers(draft, external, registrations):
        declared = tuple(kind for kind in registration.input_record_types if kind.SCHEMA == external.payload_schema)
        if declared:
            candidates = tuple(kind for kind in declared if kind.VERSION == revision)
            if len(candidates) != 1:
                raise ValueError('operation input revision is outside its selected declared consumer contract')
            codec = candidates[0]
        else:
            codec = fallback_codecs.get(external.payload_schema)
            if codec is None or codec.VERSION != revision:
                raise ValueError('operation input lacks an installed strict schema/revision codec')
        if resolved is not None and resolved is not codec:
            raise ValueError('operation consumers disagree on one strict input schema/revision codec')
        resolved = codec
    return resolved
