# SPDX-License-Identifier: MPL-2.0
"""A closed shared-node view of unchanged canonical control bytes.

The view is auxiliary. Its original record, every typed invariant and the
original byte comparison remain required. References identify node content,
never external files, code or scientific authority.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import ClassVar

from .provenance import ObjectIdentity
from .serialization import CanonicalRecord, CanonicalizationError, _canonical_documents, validate_sha256

MAX_CONTROL_BYTES = 256 * 1024**2


def _json(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(',', ':'))


def _invalid(message):
    raise CanonicalizationError('normalised control ' + message)


def _content_tree(value, identities):
    """Hash references by content identity, independently of table position."""
    if type(value) is dict:
        if set(value) == {'$ref'}:
            return {'$ref': identities[value['$ref']]}
        return {key: _content_tree(item, identities) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_content_tree(item, identities) for item in value]
    return value


def _document(graph_json, original_size):
    """Validate the complete DAG before typed construction, without expansion."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                _invalid('repeats a graph field')
            result[key] = value
        return result

    try:
        graph = json.loads(graph_json, object_pairs_hook=unique,
            parse_float=lambda _: _invalid('contains a binary number'),
            parse_constant=lambda _: _invalid('contains a non-finite number'))
        if type(graph) is not dict or set(graph) != {'nodes', 'root'} or _json(graph) != graph_json:
            _invalid('graph is not canonical')
        nodes, root = graph['nodes'], graph['root']
        if type(nodes) is not list or not nodes or type(root) is not int or not 0 <= root < len(nodes):
            _invalid('requires a complete node census and root')
        resolved, sizes, edges, identities, seen = [], [], [], [], set()

        def value(entry, dependencies):
            if type(entry) in (str, int, bool, type(None)):
                size = len(_json(entry))
                if size >= original_size:
                    _invalid('expansion exceeds its original byte bound')
                return entry, size
            if type(entry) is dict and set(entry) == {'$ref'}:
                index = entry['$ref']
                if type(index) is not int or not 0 <= index < len(resolved):
                    _invalid('has a missing, cyclic or forward reference')
                dependencies.add(index)
                return resolved[index], sizes[index]
            if type(entry) is dict:
                entries = entry['$literal'] if set(entry) == {'$literal'} else sorted(entry.items())
                if type(entries) is not list:
                    _invalid('has an invalid literal mapping')
                result, keys = {}, []
                size = 2 + max(0, len(entries) - 1)
                for pair in entries:
                    if type(pair) not in (list, tuple) or len(pair) != 2 or type(pair[0]) is not str:
                        _invalid('has an invalid mapping entry')
                    key, operand = pair
                    item, item_size = value(operand, dependencies)
                    result[key] = item
                    keys.append(key)
                    size += len(_json(key)) + 1 + item_size
                if keys != sorted(set(keys)):
                    _invalid('repeats or reorders mapping keys')
            elif type(entry) is list:
                result = []
                size = 2 + max(0, len(entry) - 1)
                for operand in entry:
                    item, item_size = value(operand, dependencies)
                    result.append(item)
                    size += item_size
            else:
                _invalid('has an unknown node type')
            if size >= original_size:
                _invalid('expansion exceeds its original byte bound')
            return result, size

        for row in nodes:
            if type(row) is not list or len(row) != 2 or type(row[0]) is not str:
                _invalid('has an invalid node')
            digest, body = row
            validate_sha256(digest)
            dependencies = set()
            result, size = value(body, dependencies)
            if digest in seen or sha256(_json(_content_tree(body, identities)).encode('ascii')).hexdigest() != digest:
                _invalid('repeats or changes node content')
            resolved.append(result)
            sizes.append(size)
            edges.append(dependencies)
            identities.append(digest)
            seen.add(digest)
        if sizes[root] + 1 != original_size:
            _invalid('changes its original expanded size')
        reached, pending = set(), [root]
        while pending:
            selected = pending.pop()
            if selected not in reached:
                reached.add(selected)
                pending.extend(edges[selected])
        if len(reached) != len(nodes):
            _invalid('contains unused nodes')
        return resolved[root]
    except (RecursionError, UnicodeError, TypeError) as error:
        raise CanonicalizationError('normalised control exceeds its graph contract') from error


@dataclass(frozen=True, slots=True)
class NormalizedCanonicalControl(CanonicalRecord):
    """Versioned auxiliary DAG, bound to one complete original record."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/kernel/normalized-canonical-control'

    original: ObjectIdentity
    original_size_bytes: int
    graph_json: str

    def __post_init__(self):
        if type(self.original) is not ObjectIdentity:
            _invalid('requires an exact original identity')
        if type(self.original_size_bytes) is not int or not 0 < self.original_size_bytes <= MAX_CONTROL_BYTES:
            _invalid('requires a bounded original size')
        if type(self.graph_json) is not str or not 0 < len(self.graph_json) <= MAX_CONTROL_BYTES:
            _invalid('requires bounded graph text')
        _document(self.graph_json, self.original_size_bytes)

    @classmethod
    def from_record(cls, object_id, record):
        size = record.canonical_size_bytes()
        if size > MAX_CONTROL_BYTES:
            _invalid('exceeds the supported original size')
        # Preserve shared typed operands during conversion as well as encoding.
        token = _canonical_documents.set({})
        try:
            document = record.to_document()
        finally:
            _canonical_documents.reset(token)
        bodies, uses, sizes, memo, scalars = {}, {}, {}, {}, {}

        def reference(digest):
            uses[digest] = uses.get(digest, 0) + 1
            return digest

        def visit(item):
            if type(item) in (str, int, bool, type(None)):
                key = type(item), item
                if key not in scalars:
                    body = ['atom', item]
                    digest = sha256(_json(body).encode('ascii')).hexdigest()
                    scalars[key] = digest
                    bodies[digest], sizes[digest] = body, len(_json(item))
                return reference(scalars[key])
            if id(item) in memo:
                return reference(memo[id(item)])
            if type(item) is dict:
                body = ['map', [[key, visit(item[key])] for key in sorted(item)]]
            elif type(item) is list:
                body = ['seq', [visit(child) for child in item]]
            else:
                _invalid('contains an unsupported original value')
            digest = sha256(_json(body).encode('ascii')).hexdigest()
            if digest not in bodies:
                bodies[digest] = body
                sizes[digest] = 2 + max(0, len(body[1]) - 1) + (
                    sum(len(_json(key)) + 1 + sizes[entry] for key, entry in body[1])
                    if body[0] == 'map' else sum(sizes[entry] for entry in body[1]))
            memo[id(item)] = digest
            return reference(digest)

        root = visit(document)
        nodes, shared, identities = [], {}, []

        def compact_value(digest):
            if uses[digest] > 1 and sizes[digest] >= 96:
                return {'$ref': store(digest)}
            return compact_body(digest)

        def compact_body(digest):
            tag, entries = bodies[digest]
            if tag == 'atom':
                return entries
            if tag == 'seq':
                return [compact_value(entry) for entry in entries]
            result = {key: compact_value(entry) for key, entry in entries}
            return {'$literal': sorted(result.items())} if set(result) in ({'$ref'}, {'$literal'}) else result

        def store(digest):
            if digest not in shared:
                body = compact_body(digest)
                identity = sha256(_json(_content_tree(body, identities)).encode('ascii')).hexdigest()
                shared[digest] = len(nodes)
                nodes.append([identity, body])
                identities.append(identity)
            return shared[digest]

        root = store(root)
        return cls(ObjectIdentity.from_record(object_id, record), size, _json({'nodes': nodes, 'root': root}))

    def restore(self, payload, record_type, *, maximum_bytes):
        """Run ordinary typed validation and compare every original byte."""
        from .decoding import _decode_canonical_document

        if (type(payload) is not bytes or type(maximum_bytes) is not int or maximum_bytes <= 0
                or len(payload) > maximum_bytes or len(payload) != self.original_size_bytes
                or sha256(payload).hexdigest() != self.original.object_fingerprint
                or (record_type.SCHEMA, record_type.VERSION) !=
                    (self.original.object_schema, self.original.object_version)):
            _invalid('changes its original bytes, type or consumer bound')
        record = _decode_canonical_document(_document(self.graph_json, len(payload)), record_type, payload)
        from .decoded_record_store import current_decoded_record_store, record_store_key
        store = current_decoded_record_store()
        if store is not None:
            store.put(record_store_key(record_type, self.original.object_fingerprint, len(payload)), record)
        return record
