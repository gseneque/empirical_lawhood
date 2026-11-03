# SPDX-License-Identifier: MPL-2.0
"""Scoped battery producer storage substitution through existing native custody.

The selected solver, acquisition loop, contact/roster owners and scientific
denominators remain explicit unchanged operands. Only raw/full array storage
is replaced. Every physical output has the newly declared storage schema.
"""

from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from . import lossless_segment_arrays as codec
from . import lossless_segment_records as records
from . import segmented_native as native


class _RawCarrier:
    SCHEMA, VERSION = native.RawReturnedSegment.SCHEMA, native.RawReturnedSegment.VERSION
    def __init__(self, index, sources):
        self.index, self.sources = index, sources
        self.raw_id = index.decoded_subject.object_id

    def fingerprint(self):
        return self.index.decoded_subject.object_fingerprint


class _FullCarrier:
    SCHEMA, VERSION = native.FullStateSegment.SCHEMA, native.FullStateSegment.VERSION
    def __init__(self, index):
        self.index = index
        self.segment_id = index.decoded_subject.object_id
        self.returned_model_expression_sha256 = index.returned_model_expression_sha256

    def fingerprint(self):
        return self.index.decoded_subject.object_fingerprint


def observe_raw_return(solution, protocol, request, returned):
    """Retain actual C-order buffers; never construct native bytes_hex strings."""
    import numpy as np
    present = tuple(sorted(name for name in ("all_ts", "all_ys", "all_yps") if hasattr(solution, name)))
    counts, declarations, sources = [], [], {}
    raw_id = request.request_id + ".raw-return"
    provisional = ObjectIdentity(raw_id, native.RawReturnedSegment.SCHEMA, "1.0.0", "0" * 64)
    for role in ("all_ts", "all_ys", "all_yps"):
        value = getattr(solution, role, None)
        counts.append(None if value is None else len(value))
        for at, block in enumerate(value or ()):
            original = np.asarray(block)
            array = np.ascontiguousarray(original).reshape(original.shape)
            # A retained contiguous owner keeps raw object/nonfinite bytes even
            # when the separate numerical interpreter must fail.
            buffer = memoryview(array).cast("B")
            def chunks(view=buffer, owner=array):
                for offset in range(0, len(view), codec.CHUNK_BYTES):
                    yield bytes(view[offset:offset + codec.CHUNK_BYTES])
            def read_at(offset, size, view=buffer, owner=array):
                return bytes(view[offset:offset + size])
            digest = sha256()
            for chunk in chunks():
                digest.update(chunk)
            declaration = codec.LosslessArrayDeclaration(raw_id + "." + role.replace("_", "-") + "." + str(at),
                provisional, role, at, array.dtype.str, tuple(array.shape), array.dtype.itemsize, digest.hexdigest())
            declarations.append(declaration)
            sources[declaration.array_id] = chunks, read_at
    array_subjects = tuple((row, sources[row.array_id][0]) for row in declarations)
    subject = records.digest_fragments(records.raw_subject_fragments(raw_id, native._identity(protocol, "protocol_id"),
        request.identity, native._identity(returned, "return_id"), present, tuple(counts), array_subjects))
    exact = replace(provisional, object_fingerprint=subject)
    declarations = tuple(replace(row, source=exact) for row in declarations)
    index = records.RawSegmentIndex(raw_id + ".storage-index", exact, native._identity(protocol, "protocol_id"),
        request.identity, native._identity(returned, "return_id"), present, tuple(counts), declarations)
    return _RawCarrier(index, sources)


def observe_full_segment(solution, protocol, layout, request, returned, raw_return):
    """Interpret all original buffers and hash exact old float.hex subject bytes."""
    if type(raw_return) is not _RawCarrier:
        raise ValueError("lossless full capture lacks actual raw storage carrier")
    counts = raw_return.index.block_counts
    if (getattr(solution, "variables_returned", False) or not counts[0] or counts[0] != counts[1]
            or len(solution.all_models) != counts[0] or len(solution.all_inputs) != counts[0]):
        raise ValueError("lossless full capture requires complete original state/model/input blocks")
    full_id = request.request_id + ".full-state"
    provisional = ObjectIdentity(full_id, native.FullStateSegment.SCHEMA, "1.0.0", "0" * 64)
    index = records.FullSegmentIndex(full_id + ".storage-index", provisional,
        native._identity(protocol, "protocol_id"), native._identity(layout, "layout_id"), request.identity,
        native._identity(returned, "return_id"), records.identity(raw_return.index, "index_id"), raw_return.index.decoded_subject,
        tuple(layout.differential_count + layout.algebraic_count for _ in range(counts[0])),
        tuple(native.passive._model_digest(model, ("rhs", "algebraic")) for model in solution.all_models),
        canonical_json_bytes(native.passive._freeze(solution.all_inputs)).decode(), str(solution.termination))
    # Build the exact same lazy representation as the independent reader. Its
    # constructor verifies the final SHA, which is not known until this pass.
    # The provisional hash is never published or admitted.
    actual = _full_hash(index, raw_return.index, raw_return.sources)
    index = replace(index, decoded_subject=replace(provisional, object_fingerprint=actual))
    records.DecodedFullSegment(index, raw_return.index, raw_return.sources)
    return _FullCarrier(index)


def _full_hash(index, raw, sources):
    # Use the exact consumer shape/order/finite checks, apart from the final
    # equality whose prospective operand is computed in this producer pass.
    counts = raw.block_counts
    if counts[0] != counts[1] or counts[0] != len(index.state_rows) or counts[2] not in (None, 0, counts[0]):
        raise ValueError("lossless full capture changes original derivative availability")
    lookup = {(row.role, row.block_index): row for row in raw.arrays}
    blocks = []
    for at, rows in enumerate(index.state_rows):
        clock, state = lookup[("all_ts", at)], lookup[("all_ys", at)]
        if len(clock.shape) != 1 or not clock.shape[0] or state.shape != (rows, clock.shape[0]):
            raise ValueError("lossless full capture changes complete native dimensions")
        clocks = tuple(records.Binary64View(clock, sources[clock.array_id][1]))
        if any(a >= b for a, b in zip(map(float.fromhex, clocks), map(float.fromhex, clocks[1:]))):
            raise ValueError("lossless full capture changes strict native clock order")
        derivative = None
        if counts[2]:
            d = lookup[("all_yps", at)]
            if d.shape != state.shape:
                raise ValueError("lossless full capture changes derivative dimensions")
            derivative = records.Binary64View(d, sources[d.array_id][1])
        blocks.append(records.DecodedFullBlock(clocks, rows, records.Binary64View(state, sources[state.array_id][1]), derivative))
    return records.digest_fragments(records.full_subject_fragments(index, blocks))


def segment_outputs():
    original = _original_outputs()
    return tuple(replace(row, payload_schema=records.RawSegmentStreamLine.SCHEMA, profile=ArtifactProfile.JSONL_CHUNKS,
        media_type="application/x-ndjson") if row.output_id == "raw-return" else
        replace(row, payload_schema=records.FullSegmentIndex.SCHEMA) if row.output_id == "full-state" else row
        for row in original)


_original_outputs = native.segment_outputs


@contextmanager
def native_storage_scope():
    """Explicit scoped storage substitution; restore owners even after failure."""
    old_raw, old_full, old_outputs = native.observe_raw_return, native.observe_full_segment, native.segment_outputs
    old_publish = native._SegmentChain._publish

    def publish_carrier(chain, entry, name, record):
        if type(record) is _RawCarrier:
            if name != "raw-return":
                raise ValueError("lossless raw carrier changed its declared output role")
            def payloads():
                return records.encode_raw_segment(record.index, record.sources)
            # Exact measured byte count is physical accounting, not a ceiling
            # on arrays or an operational truncation of the scientific roster.
            size, digest = 0, sha256()
            for piece in payloads():
                size += len(piece)
                digest.update(piece)
            manifest = chain.progress.publish_output(entry, name, payloads(), maximum_bytes=size,
                maximum_chunk_bytes=3 * codec.CHUNK_BYTES, expected_size_bytes=size,
                expected_physical_sha256=digest.hexdigest())
        elif type(record) is _FullCarrier:
            if name != "full-state":
                raise ValueError("lossless full carrier changed its declared output role")
            manifest = native.passive._publish(chain.progress, entry, name, record.index)
        chain.retained_bytes += manifest.materialization.size_bytes
        return manifest

    def publish(chain, entry, name, record):
        if type(record) not in (_RawCarrier, _FullCarrier):
            return old_publish(chain, entry, name, record)
        try:
            return publish_carrier(chain, entry, name, record)
        except Exception as error:
            # A custody refusal after contact remains uncertain. It cannot be
            # turned into a known solver/extraction failure by the native loop.
            raise native._CustodyFailure("actual lossless segment custody publication failed") from error

    native.observe_raw_return, native.observe_full_segment, native.segment_outputs = observe_raw_return, observe_full_segment, segment_outputs
    native._SegmentChain._publish = publish
    try:
        yield
    finally:
        native.observe_raw_return, native.observe_full_segment, native.segment_outputs = old_raw, old_full, old_outputs
        native._SegmentChain._publish = old_publish
