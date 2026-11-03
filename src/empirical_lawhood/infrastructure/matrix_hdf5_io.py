# SPDX-License-Identifier: MPL-2.0
"""Checked same-descriptor HDF5 reads; no scientific interpretation or authority.

The original container is authenticated by the shared named-array session. HDF5
can seek only through that session, and a successful exit seals the current
complete physical container. No retained source is copied or reopened by path.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from math import prod
from pathlib import Path
from types import MappingProxyType
import os

from empirical_lawhood.kernel.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import validate_relative_locator
from empirical_lawhood.runtime.array_datasets import HDF5ReadLimits
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputPort
from .bounded_io import _identity, _open_contained_regular
from .dataset_readers import ArrayDatasetReader, AuthenticatedBlockByteSource


class _ProcessAllocationScope:
    """A selected bound rechecked against this process's actual kernel limits."""
    __slots__ = ("selected_bytes", "process_id")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("HDF5 actual process allocation binding is read-only")
        object.__setattr__(self, name, value)

    def __init__(self, selected_bytes):
        self.selected_bytes, self.process_id = selected_bytes, os.getpid()
        self.check()

    def check(self):
        import resource
        from .execution import ResourceAdmissionError
        if not hasattr(resource, "RLIMIT_AS"):
            raise ResourceAdmissionError("HDF5 processing requires an enforced address-space limit")
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        if (os.getpid() != self.process_id or type(self.selected_bytes) is not int
                or not 0 < soft <= hard <= self.selected_bytes):
            raise ResourceAdmissionError("HDF5 actual soft/hard address-space limits exceed the selected task budget")


def require_hdf5_process_budget(task_context):
    """Admit no hidden native allocation before the real worker bound exists."""
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
    from .execution import ResourceAdmissionError
    if (type(task_context) is not TaskContext
            or type(task_context.prepared_invocation) is not PreparedInvocationContract
            or type(task_context.resource_budget.memory_bytes) is not int
            or task_context.resource_budget.memory_bytes < 1):
        raise ResourceAdmissionError("HDF5 processing requires its original prepared task and finite memory selection")
    task_context.prepared_invocation.validate_context(task_context)
    return _ProcessAllocationScope(task_context.resource_budget.memory_bytes)


@dataclass(frozen=True, slots=True)
class HDF5MemberMetadata:
    name: str
    dtype: str
    shape: tuple[int, ...]
    itemsize: int
    chunks: tuple[int, ...] | None

    @property
    def size_bytes(self):
        return prod(self.shape) * self.itemsize


@dataclass(frozen=True, slots=True)
class HDF5AttributeMetadata:
    owner: str
    name: str
    dtype: str
    shape: tuple[int, ...]
    decoded_bytes: int | None
    variable_string: bool


class _ContainerSource:
    """Actual one-open regular descriptor, with no label-based immutability."""
    __slots__ = ("descriptor", "before", "chunk_bytes", "closed", "bytes_read", "read_calls")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("HDF5 original descriptor and selected bounds are read-only")
        object.__setattr__(self, name, value)

    def __init__(self, descriptor, before, chunk_bytes):
        self.descriptor, self.before, self.chunk_bytes, self.closed = descriptor, before, chunk_bytes, False
        self.bytes_read, self.read_calls = 0, 0

    def check(self):
        if self.closed or _identity(os.fstat(self.descriptor)) != _identity(self.before):
            raise ValueError("HDF5 original descriptor changed its exact opened binding")

    def open_member(self, name):
        self.check()
        for start in range(0, self.before.st_size, self.chunk_bytes):
            yield self.read_member_range(name, start, min(start + self.chunk_bytes, self.before.st_size))
        self.check()

    def read_member_range(self, name, start, stop):
        self.check()
        if (name != "container.bytes" or type(start) is not int or type(stop) is not int
                or not 0 <= start <= stop <= self.before.st_size):
            raise ValueError("HDF5 physical byte request changes its original exact container")
        raw = os.pread(self.descriptor, stop - start, start)
        self.check()
        if len(raw) != stop - start:
            raise ValueError("HDF5 physical byte request truncates its original container")
        object.__setattr__(self, "bytes_read", self.bytes_read + len(raw))
        object.__setattr__(self, "read_calls", self.read_calls + 1)
        return raw

    def close(self):
        if not self.closed:
            object.__setattr__(self, "closed", True)
            os.close(self.descriptor)


class _PortContainerSource:
    """One independent same-sealed-FD cursor; the original port stays unread."""
    __slots__ = ("cursor", "size", "chunk_bytes", "closed", "allocation_scope", "bytes_read", "read_calls")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("HDF5 sealed port and selected bounds are read-only")
        object.__setattr__(self, name, value)

    def __init__(self, artifact, port, chunk_bytes, allocation_scope):
        if type(allocation_scope) is not _ProcessAllocationScope:
            raise TypeError("HDF5 port admission requires its actual process allocation scope")
        allocation_scope.check()
        if type(port) is not WorkerInputPort or (port.artifact_id, port.payload_schema, port.media_type, port.size_bytes) != (
                artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.size_bytes):
            raise ValueError("HDF5 worker port changes its original artifact/schema/media/extent")
        self.cursor, self.size = port.cursor(), artifact.size_bytes
        self.chunk_bytes, self.allocation_scope, self.closed = chunk_bytes, allocation_scope, False
        self.bytes_read, self.read_calls = 0, 0

    def check(self):
        if self.closed:
            raise ValueError("HDF5 sealed input cursor lifetime is closed")
        self.allocation_scope.check()
        self.cursor.tell()

    def open_member(self, name):
        self.check()
        for start in range(0, self.size, self.chunk_bytes):
            yield self.read_member_range(name, start, min(start + self.chunk_bytes, self.size))
        self.check()

    def read_member_range(self, name, start, stop):
        self.check()
        if (name != "container.bytes" or type(start) is not int or type(stop) is not int
                or not 0 <= start <= stop <= self.size):
            raise ValueError("HDF5 physical request changes its original sealed byte interval")
        self.cursor.seek(start)
        raw = self.cursor.read(stop - start)
        if len(raw) != stop - start:
            raise ValueError("HDF5 sealed worker operand is truncated")
        object.__setattr__(self, "bytes_read", self.bytes_read + len(raw))
        object.__setattr__(self, "read_calls", self.read_calls + 1)
        self.check()
        return raw

    def close(self):
        if not self.closed:
            object.__setattr__(self, "closed", True)
            self.cursor.close()


class _CheckedCursor:
    __slots__ = ("reader", "size", "bound", "position", "closed")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("HDF5 checked cursor binding and bounds are read-only")
        object.__setattr__(self, name, value)

    def __init__(self, reader, size, maximum_read_bytes):
        self.reader, self.size, self.bound, self.position, self.closed = reader, size, maximum_read_bytes, 0, False

    def _check(self):
        if self.closed:
            raise ValueError("HDF5 checked cursor lifetime is closed")

    def read(self, size=-1):
        self._check()
        if type(size) is not int or size < -1:
            raise ValueError("HDF5 physical read requires an exact byte count")
        size = self.size - self.position if size == -1 else min(size, self.size - self.position)
        if size > self.bound:
            raise ValueError("HDF5 physical request exceeds its selected working-memory bound")
        raw = self.reader.read_member_bytes("container.bytes", self.position, self.position + size)
        object.__setattr__(self, "position", self.position + len(raw))
        return raw

    def readinto(self, output):
        target = memoryview(output).cast("B")
        raw = self.read(target.nbytes)
        target[:len(raw)] = raw
        return len(raw)

    def seek(self, offset, whence=0):
        self._check()
        if type(offset) is not int or type(whence) is not int or whence not in (0, 1, 2):
            raise ValueError("HDF5 physical seek requires exact original byte coordinates")
        position = offset + (self.position if whence == 1 else self.size if whence == 2 else 0)
        if not 0 <= position <= self.size:
            raise ValueError("HDF5 physical seek leaves its original authenticated container")
        object.__setattr__(self, "position", position)
        return position

    def tell(self):
        self._check()
        return self.position

    def close(self):
        object.__setattr__(self, "closed", True)


class HDF5DatasetSource:
    """Bounded actual values and metadata; domain callers still validate science."""
    __slots__ = ("_handle", "limits", "_physical", "_closed", "members", "attributes", "_members", "_allocation_scope",
        "value_bytes_read", "value_read_calls")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("HDF5 admitted handle, metadata and selected bounds are read-only")
        object.__setattr__(self, name, value)

    def __init__(self, handle, limits, physical_source, allocation_scope=None):
        if allocation_scope is not None:
            if type(allocation_scope) is not _ProcessAllocationScope:
                raise TypeError("HDF5 values require their actual process allocation scope")
            allocation_scope.check()
        import h5py
        self._handle, self.limits, self._physical = handle, limits, physical_source
        self._allocation_scope = allocation_scope
        self._closed = False
        self.value_bytes_read, self.value_read_calls = 0, 0
        members, attributes, groups = {}, [], [0]

        def attrs(owner, label):
            if len(owner.attrs) + len(attributes) > limits.maximum_attributes:
                raise ValueError("HDF5 attribute census exceeds its selected metadata bound")
            for name in owner.attrs:
                if len(name.encode()) > limits.maximum_path_bytes:
                    raise ValueError("HDF5 attribute name exceeds its selected metadata bound")
                selected = owner.attrs.get_id(name)
                kind, space = selected.get_type(), selected.get_space()
                try:
                    shape = tuple(space.get_simple_extent_dims())
                    variable = kind.get_class() == h5py.h5t.STRING and kind.is_variable_str()
                    if kind.detect_class(h5py.h5t.REFERENCE) or kind.detect_class(h5py.h5t.VLEN) and not variable:
                        raise ValueError("HDF5 attribute contains unsupported object references or variable arrays")
                    if variable and shape:
                        raise ValueError("HDF5 variable strings support only the original scalar attribute contract")
                    count = prod(shape)
                    size = None if variable else count * kind.get_size()
                    if count > limits.maximum_attribute_bytes or size is not None and size > limits.maximum_attribute_bytes:
                        raise ValueError("HDF5 attribute decoded bytes exceed its selected metadata bound")
                    if selected.dtype.hasobject and not variable:
                        raise ValueError("HDF5 attribute contains unsupported object data")
                    attributes.append(HDF5AttributeMetadata(label, name, selected.dtype.str, shape, size, variable))
                finally:
                    kind.close()
                    space.close()
                    selected.close()

        def visit(group, prefix):
            if group.id.get_num_objs() > limits.maximum_groups + limits.maximum_members:
                raise ValueError("HDF5 link census exceeds its selected metadata bound")
            attrs(group, prefix)
            for name in group:
                path = prefix + "/" + name if prefix else name
                if len(path.encode()) > limits.maximum_path_bytes:
                    raise ValueError("HDF5 member path exceeds its selected metadata bound")
                if type(group.get(name, getlink=True)) is not h5py.HardLink:
                    raise ValueError("HDF5 source refuses soft or external links")
                value = group[name]
                if type(value) is h5py.Group:
                    groups[0] += 1
                    if groups[0] > limits.maximum_groups:
                        raise ValueError("HDF5 group census exceeds its selected metadata bound")
                    visit(value, path)
                    continue
                if type(value) is not h5py.Dataset or len(members) >= limits.maximum_members:
                    raise ValueError("HDF5 member census exceeds its selected metadata bound")
                if value.shape is None or value.dtype.hasobject or value.dtype.fields or value.dtype.kind not in "biufc" or value.is_virtual or value.external:
                    raise ValueError("HDF5 source refuses object, virtual or external data")
                chunks = value.chunks
                if chunks is not None and prod(chunks) * value.dtype.itemsize > limits.maximum_decoded_chunk_bytes:
                    raise ValueError("HDF5 physical chunk exceeds its selected decoded working-memory bound")
                plist = value.id.get_create_plist()
                try:
                    if any(plist.get_filter(at)[0] not in (1, 2, 3) for at in range(plist.get_nfilters())):
                        raise ValueError("HDF5 source refuses an undeclared filter plugin")
                finally:
                    plist.close()
                attrs(value, path)
                members[path] = HDF5MemberMetadata(path, value.dtype.str, value.shape, value.dtype.itemsize, chunks)

        visit(handle, "")
        self.members = tuple(members[name] for name in sorted(members))
        self.attributes = tuple(attributes)
        self._members = MappingProxyType(members)

    def _check(self):
        if self._closed:
            raise ValueError("HDF5 dataset source lifetime is closed")
        if self._allocation_scope is not None:
            self._allocation_scope.check()
        self._physical.check()

    def read_attribute(self, name, *, owner=""):
        self._check()
        selected = next(row for row in self.attributes if (row.owner, row.name) == (owner, name))
        if selected.variable_string and self._allocation_scope is None:
            raise ValueError("HDF5 scalar variable string decoded-length admission remains unsupported software")
        group = self._handle if owner == "" else self._handle[owner]
        result = group.attrs[name]
        self._check()
        if selected.variable_string:
            size = len(result.encode("utf-8")) if isinstance(result, str) else len(result)
            if size > self.limits.maximum_attribute_bytes:
                raise ValueError("HDF5 variable string exceeds its selected decoded metadata bound")
        return result

    def read_array_slice(self, name, start, stop):
        import numpy as np
        self._check()
        member = self._members[name]
        extent = member.shape[0] if member.shape else 1
        if (type(start) is not int or type(stop) is not int or not 0 <= start <= stop <= extent
                or not member.shape and (start, stop) != (0, 1)):
            raise ValueError("HDF5 slice changes its exact original first-axis interval")
        size = (stop - start) * prod(member.shape[1:]) * member.itemsize
        if size > self.limits.maximum_slice_bytes:
            raise ValueError("HDF5 value slice exceeds its selected working-memory bound")
        value = self._handle[name][()] if not member.shape else self._handle[name][start:stop]
        self._check()
        shape = () if not member.shape else (stop - start, *member.shape[1:])
        raw = value.tobytes(order="C")
        object.__setattr__(self, "value_bytes_read", self.value_bytes_read + len(raw))
        object.__setattr__(self, "value_read_calls", self.value_read_calls + 1)
        return np.frombuffer(raw, dtype=member.dtype).reshape(shape)

    @property
    def read_statistics(self):
        """Actual physical and decoded requests, readable after final close."""
        return (self._physical.bytes_read, self._physical.read_calls, self.value_bytes_read, self.value_read_calls)

    def open_member(self, name):
        member = self._members[name]
        if not member.shape:
            yield self.read_array_slice(name, 0, 1).tobytes()
            return
        row_bytes = prod(member.shape[1:]) * member.itemsize
        stream_bound = min(self.limits.maximum_chunk_bytes, self.limits.maximum_slice_bytes)
        if row_bytes > stream_bound:
            raise ValueError("HDF5 complete row exceeds its selected streaming working-memory bound")
        rows = max(1, stream_bound // max(row_bytes, 1))
        for start in range(0, member.shape[0], rows):
            yield self.read_array_slice(name, start, min(start + rows, member.shape[0])).tobytes(order="C")

    def read_member_range(self, name, start, stop):
        """Bounded logical C bytes, including partial primitive/row edges."""
        self._check()
        member = self._members[name]
        if (type(start) is not int or type(stop) is not int or not 0 <= start <= stop <= member.size_bytes
                or stop - start > self.limits.maximum_chunk_bytes):
            raise ValueError("HDF5 byte range exceeds its exact member or selected working bound")
        if start == stop:
            return b""
        row_bytes = prod(member.shape[1:]) * member.itemsize if member.shape else member.itemsize
        first, last = start // row_bytes, (stop + row_bytes - 1) // row_bytes
        value = self.read_array_slice(name, first, last).tobytes(order="C")
        return value[start - first * row_bytes:stop - first * row_bytes]


@contextmanager
def open_verified_hdf5(artifact, *, root: Path, relative_path: str, limits: HDF5ReadLimits):
    """Metadata/source prototype; successful exit always seals all actual bytes."""
    if type(artifact) is not ArtifactIdentity or type(limits) is not HDF5ReadLimits:
        raise TypeError("HDF5 selection requires exact original artifact and operational limits")
    artifact.__post_init__()
    limits.__post_init__()
    validate_relative_locator(relative_path)
    descriptor, before = _open_contained_regular(root, root / relative_path, artifact.size_bytes)
    physical = _ContainerSource(descriptor, before, limits.maximum_chunk_bytes)
    if before.st_size != artifact.size_bytes:
        physical.close()
        raise ValueError("HDF5 container omits its original exact physical byte census")
    with _open_container(artifact, physical, limits) as selected:
        yield selected


@contextmanager
def open_verified_hdf5_port(artifact, port, *, limits: HDF5ReadLimits, task_context):
    """Actual PURE worker scope, including original scalar variable strings."""
    # Validate the exact selected schema/budget before opening HDF5 or its data.
    if type(artifact) is not ArtifactIdentity or type(limits) is not HDF5ReadLimits:
        raise TypeError("HDF5 selection requires exact original artifact and operational limits")
    artifact.__post_init__()
    limits.__post_init__()
    allocation_scope = require_hdf5_process_budget(task_context)
    physical = _PortContainerSource(artifact, port, limits.maximum_chunk_bytes, allocation_scope)
    with _open_container(artifact, physical, limits, allocation_scope) as selected:
        yield selected


@contextmanager
def _open_container(artifact, physical, limits, allocation_scope=None):
    import h5py
    reference = ObjectIdentity.from_record(artifact.artifact_id, artifact)
    manifest = ArrayDatasetManifest("dataset.hdf5.container." + sha256(artifact.canonical_bytes()).hexdigest(),
        (ArrayDatasetMember("container.bytes", "|u1", (artifact.size_bytes,), artifact.sha256, False),), (reference,))
    source = AuthenticatedBlockByteSource(physical, read_range=physical.read_member_range, close=physical.close)
    reader = ArrayDatasetReader(manifest, source, maximum_chunk_bytes=limits.maximum_chunk_bytes,
        maximum_slice_bytes=limits.maximum_slice_bytes)
    try:
        with reader.verified_session(block_size_bytes=limits.maximum_chunk_bytes) as session:
            cursor = _CheckedCursor(session, artifact.size_bytes, limits.maximum_slice_bytes)
            fapl = h5py.h5p.create(h5py.h5p.FILE_ACCESS)
            selected, file_id = None, None
            try:
                fapl.set_fileobj_driver(h5py.h5fd.fileobj_driver, cursor)
                fapl.set_cache(0, limits.maximum_cache_slots, limits.maximum_raw_chunk_cache_bytes, 1.0)
                cache = fapl.get_mdc_config()
                cache.set_initial_size = 1
                cache.initial_size = cache.min_size = cache.max_size = limits.maximum_metadata_cache_bytes
                fapl.set_mdc_config(cache)
                file_id = h5py.h5f.open(b"checked-hdf5-container", h5py.h5f.ACC_RDONLY, fapl=fapl)
                with h5py.File(file_id) as handle:
                    selected = HDF5DatasetSource(handle, limits, physical, allocation_scope)
                    yield selected
            finally:
                if selected is not None:
                    object.__setattr__(selected, "_closed", True)
                if file_id is not None:
                    file_id.close()
                fapl.close()
                cursor.close()
    finally:
        source.close()
