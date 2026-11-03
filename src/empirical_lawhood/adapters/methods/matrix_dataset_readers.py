# SPDX-License-Identifier: MPL-2.0
"""Original Matrix array custody through the shared bounded logical reader.

NPZ validation remains infrastructure-owned. Container identities stay outside
logical dataset identities; genuine source, allocation and producer references
remain inside. Neither this bridge nor a verified read grants qualification.
"""

from collections.abc import Mapping
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from hashlib import sha256
from math import prod
from types import MappingProxyType

from empirical_lawhood.infrastructure.dataset_readers import ArrayDatasetReader, AuthenticatedBlockByteSource
from empirical_lawhood.infrastructure.matrix_array_io import MatrixArtifactSource, MatrixNPZSource, NPZMemberSelection, NPZMemberSource
from empirical_lawhood.kernel.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, SavedMatrixArrays
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.execution import WorkerInputPort

from .matrix_array_chunks import ChunkedMatrixArrays, FRAMED_ARRAY_MEDIA, FRAMED_ARRAY_SCHEMA, framed_size
from .matrix_factor_response.eligibility import EligibleMatrixArrays
from .matrix_factor_response.records import MatrixResponseArrays
from .matrix_factor_lifetime.records import FactorTrace

_SAVED_TYPES = (SavedMatrixArrays, MatrixResponseArrays, EligibleMatrixArrays)


def _scheduled_types():
    # Keep discovery of the existing reader independent of scheduled providers.
    from .matrix_scheduled_history.records import ScheduledArrays
    from .matrix_scheduled_history.response_records import ScheduledResponseArrays
    from .matrix_scheduled_history.continuation import ScheduledFullArrays
    from .matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Arrays
    from .matrix_scheduled_history.selected_e4_native_records import SelectedE4ProtectedArrays
    return ScheduledArrays, ScheduledResponseArrays, ScheduledFullArrays, SelectedE3E4Arrays, SelectedE4ProtectedArrays


def _saved_types():
    return (*_SAVED_TYPES, *_scheduled_types())


def _references(values):
    selected = {}
    for value in values:
        if type(value) is not ObjectIdentity:
            raise TypeError("Matrix dataset requires exact original scientific identities")
        value.__post_init__()
        if selected.setdefault(value.object_id, value) != value:
            raise ValueError("Matrix dataset aliases differing original scientific identities")
    return tuple(sorted(selected.values(), key=lambda value: value.object_id))


def _logical_manifest(original, scientific_references):
    if type(original) is FactorTrace:
        references = _references((original.root.source, original.rule,
            ObjectIdentity.from_record(original.root.root_id, original.root), *scientific_references))
        members = tuple(ArrayDatasetMember(value.name, value.dtype, value.shape, value.sha256, value.finite_required)
            for value in original.diagnostic_members)
        # Original nested scientific view/sector labels matter even if their
        # diagnostic bytes happen to agree. Packaging is not a scientific ref.
        subject = ".".join((original.root.root_id, original.view, original.sector))
        label = "dataset.matrix.factor." + sha256(subject.encode()).hexdigest()
        return ArrayDatasetManifest(label, members, references)
    references = [*original.producers, *scientific_references]
    if type(original) in _scheduled_types():
        references.append(original.source)
    elif type(original) is not MatrixResponseArrays:
        references.append(original.allocation)
    if type(original) is SavedMatrixArrays:
        references.extend(original.source_receipts)
        references.extend(ObjectIdentity.from_record(value.artifact_id, value) for value in original.source_artifacts)
        if original.original_f is not None:
            references.append(original.original_f)
    elif type(original) in (ChunkedMatrixArrays, EligibleMatrixArrays):
        references.append(original.source)
    members = tuple(ArrayDatasetMember(value.name, value.dtype, value.shape, value.sha256, value.finite_required)
        for value in original.members)
    # Deterministic identity depends only on exact logical values and sources.
    provisional = ArrayDatasetManifest("dataset.matrix.logical", members, _references(references))
    return ArrayDatasetManifest("dataset.matrix." + provisional.fingerprint(), members, provisional.scientific_references)


class _PopulationSource:
    __slots__ = ("original", "leaves", "physical", "intervals")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("Matrix complete population source and intervals are read-only")
        object.__setattr__(self, name, value)

    def __init__(self, original, leaves, physical):
        self.original, self.leaves, self.physical = original, tuple(leaves), tuple(physical)
        members = original.diagnostic_members if type(original) is FactorTrace else original.members
        intervals = {member.name: [] for member in members}
        if type(original) in (*_saved_types(), FactorTrace):
            for member in members:
                intervals[member.name].append((0, member.size_bytes, leaves[0]))
        else:
            whole = {member.name: member for member in original.members}
            for chunk, leaf in zip(original.chunks, leaves, strict=True):
                for interval in chunk.intervals:
                    member = whole[interval.name]
                    row_bytes = prod(member.shape[1:]) * ArrayDatasetMember(member.name, member.dtype,
                        member.shape, member.sha256, member.finite_required).itemsize if member.shape else member.size_bytes
                    intervals[member.name].append((interval.start * row_bytes, interval.stop * row_bytes, leaf))
        self.intervals = MappingProxyType({name: tuple(values) for name, values in intervals.items()})

    def open_member(self, name):
        for _, _, leaf in self.intervals[name]:
            yield from leaf.open_member(name)

    def read_member_range(self, name, start, stop):
        pieces = []
        for begin, end, leaf in self.intervals[name]:
            low, high = max(start, begin), min(stop, end)
            if low < high:
                pieces.append(leaf.read_member_range(name, low - begin, high - begin))
        raw = b"".join(pieces)
        if len(raw) != stop - start:
            raise ValueError("Matrix dataset range omits an original owned interval")
        return raw

    def close(self):
        for leaf in self.leaves:
            leaf.close()
        for physical in self.physical:
            physical.close()


class _ArrayMapping(Mapping):
    __slots__ = ("reader", "names")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("Matrix complete bounded array mapping is read-only")
        object.__setattr__(self, name, value)

    def __init__(self, reader):
        self.reader, self.names = reader, tuple(member.name for member in reader.manifest.members)

    def __iter__(self):
        return iter(self.names)

    def __len__(self):
        return len(self.names)

    def __getitem__(self, name):
        if name not in self.names:
            raise KeyError(name)
        return self.reader.read_array(name)


class MatrixArrayRows:
    """Read-only shape/dtype/row interface; whole-population coercion refuses."""
    __slots__ = ("reader", "name", "shape", "dtype", "_row_bytes", "_buffer_bytes", "_start", "_payload", "_row_index", "_row_value")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("Matrix row bindings and explicit working bounds are read-only")
        object.__setattr__(self, name, value)

    def __init__(self, reader, member):
        import numpy as np
        self.reader, self.name, self.shape, self.dtype = reader, member.name, member.shape, np.dtype(member.dtype)
        self._row_bytes = prod(member.shape[1:]) * member.itemsize
        self._buffer_bytes = reader.maximum_slice_bytes // member.itemsize * member.itemsize
        self._start, self._payload = -1, b""
        self._row_index, self._row_value = -1, None

    def __array__(self, *args, **kwargs):
        raise TypeError("Matrix row view refuses whole-population array materialization")

    @property
    def ndim(self):
        return len(self.shape)

    def __getitem__(self, index):
        if type(index) is tuple:
            if not index:
                raise IndexError("Matrix row view requires its declared first-axis row")
            return self[index[0]][index[1:]]
        if type(index) is not int or not self.shape or not 0 <= index < self.shape[0]:
            raise IndexError("Matrix row view requires an exact declared first-axis row")
        # Empty delivery checks the owning session lifetime and admitted index
        # without rereading a value block on a bounded snapshot-cache hit.
        self.reader.read_member_bytes(self.name, 0, 0)
        if index == self._row_index:
            return self._row_value
        import numpy as np
        begin, stop = index * self._row_bytes, (index + 1) * self._row_bytes
        parts = []
        while begin < stop:
            if not self._start <= begin < self._start + len(self._payload):
                start = begin // self._buffer_bytes * self._buffer_bytes
                payload = self.reader.read_member_bytes(self.name, start,
                    min(start + self._buffer_bytes, self.shape[0] * self._row_bytes))
                object.__setattr__(self, "_start", start)
                object.__setattr__(self, "_payload", payload)
            end = min(stop, self._start + len(self._payload))
            parts.append(self._payload[begin - self._start:end - self._start])
            begin = end
        # Only this original row is copied. A retained origin/adjacent basis
        # cannot pin a complete old byte block after the bounded cache advances.
        value = np.frombuffer(b"".join(parts), dtype=self.dtype).reshape(self.shape[1:])
        object.__setattr__(self, "_row_index", index)
        object.__setattr__(self, "_row_value", value)
        return value


class _RowMapping(_ArrayMapping):
    __slots__ = ("views",)

    def __init__(self, reader):
        super().__init__(reader)
        self.views = MappingProxyType({member.name: MatrixArrayRows(reader, member) for member in reader.manifest.members})

    def __getitem__(self, name):
        if name not in self.names:
            raise KeyError(name)
        return self.views[name]


@dataclass(frozen=True, slots=True)
class MatrixDatasetBridge:
    original: CanonicalRecord
    reader: ArrayDatasetReader
    physical_artifacts: tuple[ArtifactIdentity, ...]
    _source: _PopulationSource = field(repr=False, compare=False)

    def require_original(self, original, *, scientific_references=()):
        """Join a lossless encoding to its original declared scientific values."""
        if type(original) not in (*_saved_types(), ChunkedMatrixArrays, FactorTrace):
            raise TypeError("Matrix dataset association needs its exact original scientific owner")
        original.__post_init__()
        if self.reader.manifest != _logical_manifest(original, scientific_references):
            raise ValueError("Matrix dataset substitutes original scientific values or source associations")

    def array_mapping(self, reader=None):
        selected = self.reader if reader is None else reader
        if selected.manifest.identity != self.reader.manifest.identity:
            raise ValueError("Matrix mapping substitutes its original complete logical dataset")
        return _ArrayMapping(selected)

    def row_mapping(self, reader):
        if reader.manifest.identity != self.reader.manifest.identity:
            raise ValueError("Matrix row mapping substitutes its original complete logical dataset")
        return _RowMapping(reader)

    def iter_chunk_arrays(self, reader=None, *, original=None):
        owner = self.original if original is None else original
        if type(owner) is not ChunkedMatrixArrays:
            raise ValueError("Matrix chunk delivery requires its original interval manifest")
        self.require_original(owner)
        selected = self.reader if reader is None else reader
        if selected.manifest.identity != self.reader.manifest.identity:
            raise ValueError("Matrix interval delivery substitutes its original complete logical dataset")
        for chunk in owner.chunks:
            yield chunk, {interval.name: selected.read_array_slice(interval.name, interval.start, interval.stop)
                for interval in chunk.intervals}

    def close(self):
        self._source.close()


def _bridge(original, leaves, physical, *, maximum_chunk_bytes, maximum_slice_bytes, scientific_references):
    source = _PopulationSource(original, leaves, physical)
    manifest = _logical_manifest(original, scientific_references)
    wrapped = AuthenticatedBlockByteSource(source, read_range=source.read_member_range, close=source.close)
    reader = ArrayDatasetReader(manifest, wrapped, maximum_chunk_bytes=maximum_chunk_bytes, maximum_slice_bytes=maximum_slice_bytes)
    return MatrixDatasetBridge(original, reader, tuple(value.artifact for value in physical), source)


@contextmanager
def verified_array_mappings(owners, datasets):
    """Join each historical owner and verify every complete operand first."""
    if type(owners) is not tuple or type(datasets) is not tuple or not owners or len(owners) != len(datasets):
        raise ValueError("Matrix assessment omits its exact complete dataset operand tuple")
    readers = []
    for original, dataset in zip(owners, datasets, strict=True):
        if type(dataset) is MatrixDatasetBridge:
            dataset.require_original(original)
            readers.append(dataset.reader)
        elif type(dataset) is ArrayDatasetReader:
            if type(original) not in (*_saved_types(), ChunkedMatrixArrays, FactorTrace):
                raise TypeError("Matrix dataset association needs its exact original scientific owner")
            original.__post_init__()
            if dataset.manifest != _logical_manifest(original, ()):
                raise ValueError("Matrix dataset substitutes original scientific values or source associations")
            readers.append(dataset)
        else:
            raise TypeError("Matrix assessment needs exact original typed array datasets")
    with ExitStack() as stack:
        sessions = tuple(stack.enter_context(reader.verified_session(block_size_bytes=reader.maximum_chunk_bytes))
            for reader in readers)
        yield tuple(_ArrayMapping(session) for session in sessions)


@contextmanager
def retained_array_mappings(owners, fetch, *, maximum_chunk_bytes, maximum_slice_bytes):
    """Read original retained operands, closing earlier leases on late refusal."""
    with ExitStack() as stack:
        datasets = []
        for original in owners:
            supplied = fetch(original.array_artifact)
            if type(supplied) in (MatrixDatasetBridge, ArrayDatasetReader):
                dataset = supplied
            else:
                dataset = bridge_saved_arrays(original, supplied,
                    maximum_chunk_bytes=maximum_chunk_bytes, maximum_slice_bytes=maximum_slice_bytes)
                stack.callback(dataset.close)
            datasets.append(dataset)
        with verified_array_mappings(owners, tuple(datasets)) as values:
            yield values


def bridge_worker_arrays(ports, original, *, expected_producers, maximum_chunk_bytes, maximum_slice_bytes,
                         source=None, origin=None):
    """Retain exact old exposed/eligible worker guards without population reads."""
    from .matrix_factor_response.eligibility import validate_eligible_array_input
    port = ports.get(original.array_artifact.artifact_id)
    expected_producers = tuple(sorted(expected_producers, key=lambda value:value.object_id))
    if type(original) is EligibleMatrixArrays:
        public = source.eligible if source is not None else origin.eligible_source
        validate_eligible_array_input(port, original, public,
            expected_members=tuple((member.name, member.dtype, member.shape) for member in original.members),
            expected_producers=expected_producers, allocation=None if origin is None else origin.allocation,
            root_id=None if origin is None else origin.root_id)
    elif (not isinstance(port, WorkerInputPort) or original.producers != expected_producers
            or port.artifact_id != original.array_artifact.artifact_id or port.payload_schema != MATRIX_ARRAY_SCHEMA
            or port.media_type != "application/x-npz" or port.size_bytes != original.array_artifact.size_bytes
            or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
        raise ValueError("matrix exposed array port/source/full member contract differs")
    return bridge_saved_arrays(original, port, maximum_chunk_bytes=maximum_chunk_bytes, maximum_slice_bytes=maximum_slice_bytes)


def bridge_saved_arrays(original, source, *, maximum_chunk_bytes, maximum_slice_bytes, scientific_references=()):
    if type(original) not in _saved_types():
        raise TypeError("Matrix NPZ bridge requires its exact original saved operand")
    original.__post_init__()
    physical = MatrixArtifactSource(original.array_artifact, source, maximum_chunk_bytes)
    try:
        leaf = MatrixNPZSource(original, physical, maximum_chunk_bytes)
        return _bridge(original, (leaf,), (physical,), maximum_chunk_bytes=maximum_chunk_bytes,
            maximum_slice_bytes=maximum_slice_bytes, scientific_references=scientific_references)
    except BaseException:
        physical.close()
        raise


def bridge_factor_diagnostics(original, source, *, maximum_chunk_bytes, maximum_slice_bytes, scientific_references=()):
    """Original FactorTrace NPZ, without relabelling or inventing an allocation."""
    if type(original) is not FactorTrace:
        raise TypeError("factor diagnostic bridge requires its original typed trace")
    original.__post_init__()
    if original.diagnostics is None or original.diagnostics.media_type != "application/zip":
        raise ValueError("factor diagnostic bridge requires its declared original ZIP artifact")
    selection = NPZMemberSelection(original.diagnostics, original.diagnostic_members)
    physical = MatrixArtifactSource(original.diagnostics, source, maximum_chunk_bytes)
    try:
        leaf = NPZMemberSource(selection, physical, maximum_chunk_bytes,
            maximum_open_members=len(original.diagnostic_members))
        return _bridge(original, (leaf,), (physical,), maximum_chunk_bytes=maximum_chunk_bytes,
            maximum_slice_bytes=maximum_slice_bytes, scientific_references=scientific_references)
    except BaseException:
        physical.close()
        raise


def bridge_chunked_arrays(original, sources, *, maximum_chunk_bytes, maximum_slice_bytes, scientific_references=()):
    if type(original) is not ChunkedMatrixArrays:
        raise TypeError("Matrix chunk bridge requires its exact original complete operand")
    original.__post_init__()
    if not isinstance(sources, Mapping) or set(sources) != {chunk.array_artifact.artifact_id for chunk in original.chunks}:
        raise ValueError("Matrix chunk inputs omit or add an original physical leaf")
    physical, leaves = [], []
    try:
        for chunk in original.chunks:
            selection = MatrixArtifactSource(chunk.array_artifact, sources[chunk.array_artifact.artifact_id], maximum_chunk_bytes)
            physical.append(selection)
            leaves.append(MatrixNPZSource(chunk, selection, maximum_chunk_bytes))
        return _bridge(original, leaves, physical, maximum_chunk_bytes=maximum_chunk_bytes,
            maximum_slice_bytes=maximum_slice_bytes, scientific_references=scientific_references)
    except BaseException:
        for selection in physical:
            selection.close()
        raise


def bridge_framed_arrays(original, container, source, *, maximum_chunk_bytes, maximum_slice_bytes, scientific_references=()):
    if type(original) is not ChunkedMatrixArrays:
        raise TypeError("Matrix framed bridge requires its exact original complete operand")
    original.__post_init__()
    if ((container.payload_schema, container.media_type, container.size_bytes)
            != (FRAMED_ARRAY_SCHEMA, FRAMED_ARRAY_MEDIA, framed_size(original))):
        raise ValueError("Matrix frame changes its original complete container contract")
    physical = MatrixArtifactSource(container, source, maximum_chunk_bytes)
    leaves = []
    try:
        with physical.cursor() as cursor:
            for chunk in original.chunks:
                header = cursor.read(8)
                if len(header) != 8 or int.from_bytes(header, "big") != chunk.array_artifact.size_bytes:
                    raise ValueError("Matrix frame changes an original leaf length or order")
                offset, digest, remaining = cursor.tell(), sha256(), chunk.array_artifact.size_bytes
                while remaining:
                    raw = cursor.read(min(maximum_chunk_bytes, remaining))
                    if not raw:
                        raise ValueError("Matrix frame omits an original leaf")
                    digest.update(raw)
                    remaining -= len(raw)
                if digest.hexdigest() != chunk.array_artifact.sha256:
                    raise ValueError("Matrix frame changes an original physical leaf digest")
                leaves.append(MatrixNPZSource(chunk, physical, maximum_chunk_bytes, offset=offset))
            if cursor.read(1):
                raise ValueError("Matrix frame adds a leaf outside the complete original census")
        return _bridge(original, leaves, (physical,), maximum_chunk_bytes=maximum_chunk_bytes,
            maximum_slice_bytes=maximum_slice_bytes, scientific_references=scientific_references)
    except BaseException:
        physical.close()
        raise
