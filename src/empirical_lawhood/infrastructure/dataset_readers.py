# SPDX-License-Identifier: MPL-2.0
"""Bounded logical array reads over code-owned authenticated physical sources.

Ordinary deliveries use fresh complete checks. Verified sessions reuse actual
sealed descriptors or authenticate every touched block against a complete
verified index. Successful session exit performs the final seal. No result
grants outcome access, source eligibility or scientific qualification.
"""

from collections import OrderedDict
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from math import prod
from types import MappingProxyType
import fcntl
import os
import stat

from empirical_lawhood.kernel.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.runtime.array_datasets import DatasetByteSource, DatasetVerification


def _permuted_interval(member, axis_order, start, stop, maximum_bytes):
    if (type(axis_order) is not tuple or any(type(axis) is not int for axis in axis_order)
            or tuple(sorted(axis_order)) != tuple(range(len(member.shape)))):
        raise ValueError("dataset view requires an exact bijective axis permutation")
    if type(start) is not int or type(stop) is not int or not 0 <= start <= stop <= member.size_bytes:
        raise ValueError("permuted dataset byte selection changes its exact member interval")
    if stop - start > maximum_bytes:
        raise ValueError("permuted dataset byte selection exceeds its explicitly selected value byte bound")


def _permuted_logical_runs(member, axis_order, start, stop):
    """Bounded output-order byte runs in the unchanged original logical C view."""
    if start == stop:
        return
    width = member.itemsize
    shape = tuple(member.shape[axis] for axis in axis_order)
    strides = tuple(prod(member.shape[axis + 1:]) for axis in axis_order)
    divisors = tuple(prod(shape[position + 1:]) for position in range(len(shape)))
    run_start = run_stop = None
    for element in range(start // width, (stop - 1) // width + 1):
        original = sum((element // divisor % size) * stride
            for size, stride, divisor in zip(shape, strides, divisors, strict=True))
        low = original * width + max(0, start - element * width)
        high = original * width + min(width, stop - element * width)
        if run_stop == low:
            run_stop = high
        else:
            if run_start is not None:
                yield run_start, run_stop
            run_start, run_stop = low, high
    if run_start is not None:
        yield run_start, run_stop


@dataclass(frozen=True, slots=True)
class DatasetFDMember:
    """Operational raw C-value interval within an already existing descriptor."""

    descriptor: int
    offset: int
    length: int
    extent_bytes: int

    def __post_init__(self):
        if (any(type(value) is not int or value < 0 for value in
                (self.descriptor, self.offset, self.length, self.extent_bytes))
                or self.offset + self.length > self.extent_bytes):
            raise ValueError("dataset descriptor changes its exact selected value interval")


class SealedFDByteSource:
    """Own duplicated sealed descriptors; reuse their bytes without copying.

    Physical codecs validate their headers and exact logical member intervals
    before constructing this source. An ordinary read-only file is insufficient:
    actual kernel WRITE, GROW, SHRINK and SEAL protections are required.
    """

    __slots__ = ("_members", "_admitted_members", "_descriptors", "_closed", "_maximum_chunk_bytes")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("sealed dataset descriptor bindings and selected bounds are read-only")
        object.__setattr__(self, name, value)

    def __init__(self, members, *, maximum_chunk_bytes: int):
        if type(maximum_chunk_bytes) is not int or maximum_chunk_bytes < 1:
            raise ValueError("sealed dataset source needs an explicit value block bound")
        self._closed, self._maximum_chunk_bytes, self._descriptors = False, maximum_chunk_bytes, {}
        selected = {}
        try:
            for name, member in members.items():
                if type(member) is not DatasetFDMember:
                    raise TypeError("sealed dataset source needs exact descriptor member selections")
                member.__post_init__()
                descriptor = self._descriptors.get(member.descriptor)
                if descriptor is None:
                    descriptor = os.dup(member.descriptor)
                    self._descriptors[member.descriptor] = descriptor
                selected[name] = DatasetFDMember(descriptor, member.offset, member.length, member.extent_bytes)
            self._members = MappingProxyType(selected)
            self._admitted_members = self._members
            object.__setattr__(self, "_descriptors", MappingProxyType(self._descriptors))
            self.verify_binding()
        except BaseException:
            self.close()
            raise

    def _ensure_open(self):
        if self._closed:
            raise ValueError("dataset descriptor lease is closed")
        if self._members is not self._admitted_members:
            raise ValueError("sealed dataset admitted descriptor bindings were replaced")

    def verify_binding(self):
        self._ensure_open()
        for member in self._members.values():
            try:
                observed = os.fstat(member.descriptor)
                seals = fcntl.fcntl(member.descriptor, getattr(fcntl, "F_GET_SEALS", 1034))
            except OSError as error:
                raise ValueError("dataset lease lacks actual immutable descriptor protections") from error
            if not stat.S_ISREG(observed.st_mode) or observed.st_size != member.extent_bytes or seals & 15 != 15:
                raise ValueError("dataset lease changes exact extent or lacks complete immutable descriptor seals")

    def validate_manifest(self, manifest):
        if (set(self._members) != {member.name for member in manifest.members}
                or any(self._members[member.name].length != member.size_bytes for member in manifest.members)):
            raise ValueError("sealed dataset intervals differ from the complete logical member census")

    def read_member_range(self, name, start, stop):
        self.verify_binding()
        member = self._members[name]
        if not 0 <= start <= stop <= member.length:
            raise ValueError("sealed dataset range changes its declared member extent")
        result = os.pread(member.descriptor, stop - start, member.offset + start)
        if len(result) != stop - start:
            raise ValueError("sealed dataset range truncates exact immutable bytes")
        return result

    def open_member(self, name):
        self._ensure_open()
        member = self._members[name]
        for start in range(0, member.length, self._maximum_chunk_bytes):
            yield self.read_member_range(name, start, min(start + self._maximum_chunk_bytes, member.length))

    def acquire_lease(self, maximum_chunk_bytes):
        self.verify_binding()
        return SealedFDByteSource(self._members, maximum_chunk_bytes=maximum_chunk_bytes)

    def close(self):
        if not self._closed:
            object.__setattr__(self, "_closed", True)
            for descriptor in self._descriptors.values():
                os.close(descriptor)


class AuthenticatedBlockByteSource:
    """Code-owned random access authenticated by the session's actual scan.

    ``read_range`` supplies exact logical C bytes from existing regular files or
    working handles. No immutable label is trusted: the session creates its own
    complete contiguous digest index and rechecks every touched block. ``close``
    closes the leases owned by this source; the source is consumed by one session.
    """

    def __init__(self, source, *, read_range, close):
        if not all(callable(value) for value in (getattr(source, "open_member", None), read_range, close)):
            raise TypeError("authenticated block source requires code-owned byte access and lease closure")
        self._source, self._read_range, self._close = source, read_range, close
        self._closed, self._leased = False, False

    def _ensure_open(self):
        if self._closed:
            raise ValueError("authenticated dataset block lease is closed")

    def open_member(self, name):
        self._ensure_open()
        return self._source.open_member(name)

    def read_member_range(self, name, start, stop):
        self._ensure_open()
        return self._read_range(name, start, stop)

    def acquire_lease(self, maximum_chunk_bytes):
        self._ensure_open()
        if self._leased:
            raise ValueError("authenticated block source lease was already selected")
        self._leased = True
        return self

    def close(self):
        if not self._closed:
            self._closed = True
            self._close()


@dataclass(frozen=True, slots=True)
class _PhysicalBinding:
    member: ArrayDatasetMember
    descriptor: DatasetFDMember
    axis_order: tuple[int, ...]
    storage_shape: tuple[int, ...]
    device: int
    inode: int


_TRANSFORM_MINT = object()


class VerifiedArrayTransform:
    """One-shot owned scratch lease minted only by actual transform admission.

    The logical hash derives from ingested bytes; the physical index derives
    from the exact mapped write bytes and has been checked against the actual
    descriptor. This operational witness is never a canonical source receipt.
    """

    __slots__ = ("_manifest", "_binding", "_blocks", "_spent")

    def __setattr__(self, name, value):
        raise AttributeError("admitted transform proof and lease state are read-only")

    def __init__(self, token, manifest, binding, blocks):
        if token is not _TRANSFORM_MINT:
            raise TypeError("transform witnesses are minted by actual admitted byte transforms")
        for name, value in (("_manifest", manifest), ("_binding", binding), ("_blocks", blocks), ("_spent", False)):
            object.__setattr__(self, name, value)

    @property
    def manifest(self):
        return self._manifest

    @property
    def member_name(self):
        return self._binding.member.name

    def _consume(self):
        if self._spent:
            raise ValueError("transform witness lease is closed or already consumed")
        object.__setattr__(self, "_spent", True)
        return self._binding, self._blocks

    def close(self):
        if not self._spent:
            object.__setattr__(self, "_spent", True)
            os.close(self._binding.descriptor.descriptor)


def _descriptor_binding(binding):
    observed = os.fstat(binding.descriptor.descriptor)
    if (not stat.S_ISREG(observed.st_mode) or observed.st_size != binding.descriptor.extent_bytes
            or (observed.st_dev, observed.st_ino) != (binding.device, binding.inode)):
        raise ValueError("physical dataset lease changes its actual descriptor binding or exact extent")


def _physical_block_interval(binding, block_size_bytes, byte):
    # A block never crosses a storage row. Thus every fixed permutation row
    # receives its mapped bytes monotonically from a logical C-order stream.
    row_bytes = (binding.storage_shape[-1] if binding.storage_shape else 1) * binding.member.itemsize
    row, within = divmod(byte, row_bytes)
    start = row * row_bytes + within // block_size_bytes * block_size_bytes
    return start, min(start + block_size_bytes, (row + 1) * row_bytes)


@dataclass(frozen=True, slots=True)
class _TransformDigestState:
    digest: object
    count: int


class ArrayTransformWriter:
    """Authenticate an exact axis transpose into selected decoded scratch.

    No new population is created. The caller supplies its existing full raw
    scratch descriptor; this writer owns a duplicate and writes every value
    byte exactly once. Expected block digests use incremental hash states,
    bounded byte tiles and metadata, never retained population values.
    """

    __slots__ = ("_manifest", "_binding", "_block_size_bytes", "_maximum_chunk_bytes", "_digest", "_count",
        "_carry", "_mapped_elements", "_closed", "_refused", "__states", "__blocks")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("array transform proof, counters and selected bounds are read-only")
        object.__setattr__(self, name, value)

    @property
    def _states(self):
        return MappingProxyType(self.__states)

    @property
    def _blocks(self):
        return MappingProxyType(self.__blocks)

    def __init__(self, manifest, name, descriptor, *, axis_order, block_size_bytes, maximum_chunk_bytes):
        if type(manifest) is not ArrayDatasetManifest or type(descriptor) is not DatasetFDMember:
            raise TypeError("array transform requires exact logical manifest and decoded scratch descriptor")
        manifest.__post_init__()
        members = {member.name: member for member in manifest.members}
        if name not in members:
            raise ValueError("array transform selects an undeclared original member")
        member = members[name]
        if (type(axis_order) is not tuple or any(type(axis) is not int for axis in axis_order)
                or tuple(sorted(axis_order)) != tuple(range(len(member.shape)))):
            raise ValueError("array transform requires an exact bijective axis permutation")
        if (type(block_size_bytes) is not int or block_size_bytes < member.itemsize
                or block_size_bytes % member.itemsize or type(maximum_chunk_bytes) is not int
                or maximum_chunk_bytes < member.itemsize):
            raise ValueError("array transform requires explicit aligned block and incoming tile bounds")
        if (descriptor.offset != 0 or descriptor.length != member.size_bytes
                or descriptor.extent_bytes != member.size_bytes):
            raise ValueError("array transform writes only its selected complete decoded scratch population")
        owned = os.dup(descriptor.descriptor)
        try:
            observed = os.fstat(owned)
            binding = _PhysicalBinding(member, DatasetFDMember(owned, 0, descriptor.length, descriptor.extent_bytes),
                axis_order, tuple(member.shape[axis] for axis in axis_order), observed.st_dev, observed.st_ino)
            _descriptor_binding(binding)
        except BaseException:
            os.close(owned)
            raise
        self._manifest, self._binding = manifest, binding
        self._block_size_bytes, self._maximum_chunk_bytes = block_size_bytes, maximum_chunk_bytes
        self._digest, self._count, self._carry, self._mapped_elements = sha256(), 0, b"", 0
        self.__states, self.__blocks, self._closed, self._refused = {}, {}, False, False

    def _ensure_active(self):
        if self._closed or self._refused:
            raise ValueError("array transform writer is closed or refused")

    def write(self, payload):
        self._ensure_active()
        member = self._binding.member
        try:
            if type(payload) is not bytes or not payload or len(payload) > self._maximum_chunk_bytes:
                raise ValueError("array transform changes its bounded nonempty original byte tile")
            object.__setattr__(self, "_count", self._count + len(payload))
            if self._count > member.size_bytes:
                raise ValueError("array transform exceeds its complete original byte census")
            self._digest.update(payload)
            combined = self._carry + payload
            stop = len(combined) // member.itemsize * member.itemsize
            aligned = combined[:stop]
            object.__setattr__(self, "_carry", combined[stop:])
            ArrayDatasetReader._finite(aligned, member)
            if aligned:
                self._write_mapped(aligned)
        except Exception:
            object.__setattr__(self, "_refused", True)
            raise
        return len(payload)

    def _write_mapped(self, raw):
        import numpy as np
        binding, member = self._binding, self._binding.member
        count = len(raw) // member.itemsize
        logical = np.arange(self._mapped_elements, self._mapped_elements + count, dtype=np.int64)
        physical = np.zeros(count, dtype=np.int64)
        for position, axis in enumerate(binding.axis_order):
            logical_stride = prod(member.shape[axis + 1:])
            storage_stride = prod(binding.storage_shape[position + 1:])
            physical += (logical // logical_stride % member.shape[axis]) * storage_stride
        if not member.shape:
            physical[:] = 0
        order = np.argsort(physical, kind="stable")
        selected = physical[order]
        # Void values copy all IEEE payload and endian bits without arithmetic.
        payload = np.frombuffer(raw, dtype=f"V{member.itemsize}")[order].tobytes()
        first = 0
        while first < count:
            end = first + 1
            while end < count and selected[end] == selected[end - 1] + 1:
                end += 1
            cursor, stop = int(selected[first]) * member.itemsize, int(selected[end - 1] + 1) * member.itemsize
            payload_offset = first * member.itemsize
            while cursor < stop:
                block_start, block_stop = _physical_block_interval(binding, self._block_size_bytes, cursor)
                state = self.__states.get(block_start)
                if state is None:
                    if block_start in self.__blocks:
                        raise ValueError("array transform repeats a completed physical block")
                    state = _TransformDigestState(sha256(), 0)
                    self.__states[block_start] = state
                if cursor != block_start + state.count:
                    raise ValueError("array transform reorders or omits exact mapped physical bytes")
                part_size = min(stop, block_stop) - cursor
                part = memoryview(payload)[payload_offset:payload_offset + part_size]
                if os.pwrite(binding.descriptor.descriptor, part, cursor) != part_size:
                    raise ValueError("array transform truncates its exact mapped write")
                state.digest.update(part)
                count_written = state.count + part_size
                if count_written == block_stop - block_start:
                    self.__blocks[block_start] = _MemberBlock(block_start, block_stop, state.digest.hexdigest())
                    del self.__states[block_start]
                else:
                    self.__states[block_start] = _TransformDigestState(state.digest, count_written)
                cursor += part_size
                payload_offset += part_size
            first = end
        object.__setattr__(self, "_mapped_elements", self._mapped_elements + count)

    def finish(self):
        """Admit the actual complete scratch bytes, then transfer one owned lease."""
        self._ensure_active()
        member = self._binding.member
        try:
            if (self._carry or self.__states or self._count != member.size_bytes
                    or self._digest.hexdigest() != member.sha256
                    or self._mapped_elements * member.itemsize != member.size_bytes):
                raise ValueError("array transform original logical hash or complete mapped byte census differs")
            _descriptor_binding(self._binding)
            blocks = tuple(self.__blocks[start] for start in sorted(self.__blocks))
            cursor = 0
            for block in blocks:
                if block.start != cursor:
                    raise ValueError("array transform physical digest index omits its complete population")
                raw = os.pread(self._binding.descriptor.descriptor, block.stop - block.start, block.start)
                if len(raw) != block.stop - block.start or sha256(raw).hexdigest() != block.sha256:
                    raise ValueError("array transform actual physical bytes differ from exact mapped write evidence")
                cursor = block.stop
            if cursor != member.size_bytes:
                raise ValueError("array transform physical digest index omits its complete population")
            _descriptor_binding(self._binding)
            witness = VerifiedArrayTransform(_TRANSFORM_MINT, self._manifest.identity, self._binding, blocks)
            object.__setattr__(self, "_closed", True)  # descriptor ownership transfers to the witness
            return witness
        except Exception:
            object.__setattr__(self, "_refused", True)
            raise

    def close(self):
        if not self._closed:
            object.__setattr__(self, "_closed", True)
            os.close(self._binding.descriptor.descriptor)


class PhysicalFDByteSource:
    """Consume admitted exact transform leases with bounded snapshot buffers.

    Cached bytes are immutable authenticated baseline blocks. Final verification
    rehashes every current physical block, including unused or cached blocks.
    Cache hits establish that baseline snapshot, not a current-byte assertion.
    """

    __slots__ = ("_manifest", "_bindings", "_indexes", "_starts", "_admitted_bindings", "_admitted_indexes",
        "_admitted_starts", "_maximum_chunk_bytes", "_maximum_cache_bytes", "_closed", "_leased", "_cache", "_cache_bytes")

    _READ_ONLY_FIELDS = frozenset(("_manifest", "_bindings", "_indexes", "_starts", "_admitted_bindings",
        "_admitted_indexes", "_admitted_starts", "_maximum_chunk_bytes", "_maximum_cache_bytes", "_closed", "_leased"))

    def __setattr__(self, name, value):
        if name in self._READ_ONLY_FIELDS and hasattr(self, name):
            raise AttributeError("admitted physical source proof, bounds and lease state are read-only")
        object.__setattr__(self, name, value)

    def __init__(self, manifest, transforms, *, maximum_chunk_bytes, maximum_cache_bytes):
        if type(manifest) is not ArrayDatasetManifest:
            raise TypeError("physical array source needs its exact original logical manifest")
        manifest.__post_init__()
        if (type(maximum_chunk_bytes) is not int or maximum_chunk_bytes < 1
                or type(maximum_cache_bytes) is not int or maximum_cache_bytes < 0):
            raise ValueError("physical array source requires explicit streaming and snapshot cache bounds")
        if set(transforms) != {member.name for member in manifest.members}:
            raise ValueError("physical source needs its complete original logical member census")
        self._bindings, self._indexes, self._starts, self._manifest = {}, {}, {}, manifest.identity
        self._maximum_chunk_bytes, self._maximum_cache_bytes = maximum_chunk_bytes, maximum_cache_bytes
        self._cache, self._cache_bytes, self._closed, self._leased = OrderedDict(), 0, False, False
        try:
            for name, witness in transforms.items():
                if type(witness) is not VerifiedArrayTransform or witness.member_name != name:
                    raise TypeError("physical source needs an actual unspent transform witness for each member")
                if witness.manifest != self._manifest:
                    raise ValueError("physical source mixes original logical manifests or source associations")
                binding, blocks = witness._consume()
                self._bindings[name], self._indexes[name] = binding, blocks
                self._starts[name] = tuple(block.start for block in blocks)
                _descriptor_binding(binding)
            for name in ("_bindings", "_indexes", "_starts"):
                selected = MappingProxyType(getattr(self, name))
                object.__setattr__(self, name, selected)
                object.__setattr__(self, "_admitted" + name, selected)
        except BaseException:
            self.close()
            raise

    def _ensure_open(self):
        if self._closed:
            raise ValueError("physical array descriptor lease is closed")
        if (self._bindings is not self._admitted_bindings or self._indexes is not self._admitted_indexes
                or self._starts is not self._admitted_starts):
            raise ValueError("physical array admitted proof or binding was replaced")

    def validate_manifest(self, manifest):
        self._ensure_open()
        if (self._manifest != manifest.identity or set(self._bindings) != {member.name for member in manifest.members}
                or any(self._bindings[member.name].member != member for member in manifest.members)):
            raise ValueError("physical source changes its original complete manifest or scientific associations")
        for binding in self._bindings.values():
            _descriptor_binding(binding)

    def acquire_lease(self, maximum_chunk_bytes):
        self._ensure_open()
        if self._leased:
            raise ValueError("physical array transform lease was already selected")
        object.__setattr__(self, "_leased", True)
        object.__setattr__(self, "_maximum_chunk_bytes", maximum_chunk_bytes)
        return self

    def _block(self, name, ordinal):
        self._ensure_open()
        binding, block = self._bindings[name], self._indexes[name][ordinal]
        key = name, ordinal
        cached = self._cache.get(key)
        if cached is not None:
            if type(cached) is not _VerifiedPhysicalBlock or cached.block is not block:
                raise ValueError("physical array snapshot cache substitutes an unadmitted block")
            self._cache.move_to_end(key)
            return cached.payload
        raw = os.pread(binding.descriptor.descriptor, block.stop - block.start, block.start)
        if len(raw) != block.stop - block.start or sha256(raw).hexdigest() != block.sha256:
            raise ValueError("physical array touched block changes its admitted mapped bytes")
        if len(raw) <= self._maximum_cache_bytes:
            while self._cache_bytes + len(raw) > self._maximum_cache_bytes:
                _, previous = self._cache.popitem(last=False)
                self._cache_bytes -= len(previous.payload)
            self._cache[key] = _VerifiedPhysicalBlock(_TRANSFORM_MINT, block, raw)
            self._cache_bytes += len(raw)
        return raw

    def read_member_range(self, name, start, stop):
        import numpy as np
        from bisect import bisect_right
        self._ensure_open()
        binding = self._bindings[name]
        _descriptor_binding(binding)
        member = binding.member
        if type(start) is not int or type(stop) is not int or not 0 <= start <= stop <= member.size_bytes:
            raise ValueError("physical logical range changes its exact original value interval")
        if start == stop:
            return b""
        if binding.axis_order == tuple(range(len(member.shape))):
            return self.read_permuted_member_range(name, binding.axis_order, start, stop)
        first, last = start // member.itemsize, (stop - 1) // member.itemsize
        logical = np.arange(first, last + 1, dtype=np.int64)
        physical = np.zeros(last - first + 1, dtype=np.int64)
        for position, axis in enumerate(binding.axis_order):
            physical += (logical // prod(member.shape[axis + 1:]) % member.shape[axis]) * prod(binding.storage_shape[position + 1:])
        output = bytearray(len(logical) * member.itemsize)
        for at, element in enumerate(physical):
            byte = int(element) * member.itemsize
            ordinal = bisect_right(self._starts[name], byte) - 1
            block = self._indexes[name][ordinal]
            raw = self._block(name, ordinal)
            offset = byte - block.start
            output[at * member.itemsize:(at + 1) * member.itemsize] = memoryview(raw)[offset:offset + member.itemsize]
        begin = start % member.itemsize
        return bytes(output[begin:begin + stop - start])

    def read_permuted_member_range(self, name, axis_order, start, stop):
        """Fast path only for the exact physically admitted logical transpose."""
        from bisect import bisect_right

        self._ensure_open()
        binding = self._bindings[name]
        _permuted_interval(binding.member, axis_order, start, stop, binding.member.size_bytes)
        if axis_order != binding.axis_order:
            return None
        _descriptor_binding(binding)
        if start == stop:
            return b""
        output = bytearray(stop - start)
        ordinal = bisect_right(self._starts[name], start) - 1
        while ordinal < len(self._indexes[name]):
            block = self._indexes[name][ordinal]
            if block.start >= stop:
                break
            low, high = max(start, block.start), min(stop, block.stop)
            raw = self._block(name, ordinal)
            output[low - start:high - start] = memoryview(raw)[low - block.start:high - block.start]
            ordinal += 1
        return bytes(output)

    def open_member(self, name):
        self._ensure_open()
        size = self._bindings[name].member.size_bytes
        for start in range(0, size, self._maximum_chunk_bytes):
            yield self.read_member_range(name, start, min(start + self._maximum_chunk_bytes, size))

    def verify_physical_complete(self):
        self._ensure_open()
        for name, binding in self._bindings.items():
            _descriptor_binding(binding)
            for block in self._indexes[name]:
                raw = os.pread(binding.descriptor.descriptor, block.stop - block.start, block.start)
                if len(raw) != block.stop - block.start or sha256(raw).hexdigest() != block.sha256:
                    raise ValueError("physical array final whole seal changes admitted mapped bytes")
            _descriptor_binding(binding)

    def close(self):
        if not self._closed:
            object.__setattr__(self, "_closed", True)
            for binding in self._bindings.values():
                os.close(binding.descriptor.descriptor)
            self._cache.clear()
            self._cache_bytes = 0


@dataclass(frozen=True, slots=True, init=False)
class _VerifiedPhysicalBlock:
    block: "_MemberBlock"
    payload: bytes

    def __init__(self, token, block, payload):
        if token is not _TRANSFORM_MINT:
            raise TypeError("physical snapshot blocks are minted after actual byte authentication")
        object.__setattr__(self, "block", block)
        object.__setattr__(self, "payload", payload)


class ArrayDatasetReader:
    """Read immutable selected arrays without retaining a complete population.

    ``maximum_chunk_bytes`` bounds each incoming value block; alignment carry
    uses at most one primitive value. ``maximum_slice_bytes`` bounds the returned
    value payload. During immutable output construction the selected payload
    has one temporary copy; working memory otherwise uses one bounded block,
    one finite-check mask and the selected slice. NumPy is imported only on use.
    """

    __slots__ = ("_manifest", "_source", "_maximum_chunk_bytes", "_maximum_slice_bytes", "_members")

    def __setattr__(self, name, value):
        if name in self.__slots__ and hasattr(self, name):
            raise AttributeError("array reader source, manifest and selected bounds are read-only")
        object.__setattr__(self, name, value)

    def __init__(self, manifest: ArrayDatasetManifest, source: DatasetByteSource, *, maximum_chunk_bytes: int, maximum_slice_bytes: int):
        if type(manifest) is not ArrayDatasetManifest:
            raise TypeError("array reader requires its typed complete logical manifest")
        manifest.__post_init__()
        if not callable(getattr(source, "open_member", None)):
            raise TypeError("array reader requires a code-owned fresh member byte source")
        if (type(maximum_chunk_bytes) is not int or maximum_chunk_bytes < max((member.itemsize for member in manifest.members), default=1)
                or type(maximum_slice_bytes) is not int or maximum_slice_bytes < 1):
            raise ValueError("array reader needs explicit chunk and selected-slice byte bounds")
        self._manifest, self._source = manifest, source
        self._maximum_chunk_bytes, self._maximum_slice_bytes = maximum_chunk_bytes, maximum_slice_bytes
        self._members = MappingProxyType({member.name: member for member in manifest.members})

    @property
    def manifest(self):
        return self._manifest

    @property
    def maximum_chunk_bytes(self):
        return self._maximum_chunk_bytes

    @property
    def maximum_slice_bytes(self):
        return self._maximum_slice_bytes

    def _member(self, name: str) -> ArrayDatasetMember:
        try:
            return self._members[name]
        except (KeyError, TypeError) as error:
            raise ValueError("array reader refuses an undeclared member") from error

    @staticmethod
    def _finite(payload, member):
        if not member.finite_required or member.dtype[1] not in ("f", "c") or not payload:
            return
        import numpy as np
        if not np.isfinite(np.frombuffer(payload, dtype=member.dtype)).all():
            raise ValueError("array dataset required finite values differ from its declared member")

    def _checked_member_bytes(self, member: ArrayDatasetMember) -> Iterator[bytes]:
        digest, count, carry = sha256(), 0, b""
        try:
            stream = iter(self._source.open_member(member.name))
        except KeyError as error:
            raise ValueError("array dataset omits a declared member") from error
        try:
            for payload in stream:
                if type(payload) is not bytes or not payload or len(payload) > self.maximum_chunk_bytes:
                    raise ValueError("array source changes its explicit bounded nonempty byte-block contract")
                count += len(payload)
                if count > member.size_bytes:
                    raise ValueError("array source exceeds its complete declared member byte count")
                digest.update(payload)
                offset = 0
                if carry:
                    needed = member.itemsize - len(carry)
                    if len(payload) < needed:
                        carry += payload
                        yield payload
                        continue
                    self._finite(carry + payload[:needed], member)
                    offset, carry = needed, b""
                aligned_stop = offset + (len(payload) - offset) // member.itemsize * member.itemsize
                self._finite(memoryview(payload)[offset:aligned_stop], member)
                carry = payload[aligned_stop:]
                yield payload
        except KeyError as error:
            raise ValueError("array dataset omits a declared member") from error
        finally:
            close = getattr(stream, "close", None)
            if close is not None:
                close()
        if carry or count != member.size_bytes or digest.hexdigest() != member.sha256:
            raise ValueError("array dataset complete member size or value hash verification failed")

    def verify_complete(self) -> DatasetVerification:
        """Verify every current member without collecting any value population."""
        if type(self._source) is PhysicalFDByteSource:
            self._source.validate_manifest(self.manifest)
            self._source.verify_physical_complete()
        else:
            for member in self.manifest.members:
                for _ in self._checked_member_bytes(member):
                    pass
        return DatasetVerification(self.manifest.identity, tuple((member.name, member.sha256) for member in self.manifest.members),
            self.manifest.size_bytes)

    def iter_member_bytes(self, name: str) -> Iterator[bytes]:
        """Deliver no prefix before complete preverification; exhaust for seal."""
        member = self._member(name)
        self.verify_complete()
        yield from self._checked_member_bytes(member)
        if type(self._source) is PhysicalFDByteSource:
            self._source.verify_physical_complete()

    def read_array_slice(self, name: str, start: int, stop: int):
        """Read the exact bounded first axis; ordinary reads seal full members."""
        member = self._member(name)
        if (type(start) is not int or type(stop) is not int or not 0 <= start <= stop <= member.first_axis_extent
                or not member.shape and (start, stop) != (0, 1)):
            raise ValueError("array slice changes its exact declared first-axis interval")
        row_bytes = prod(member.shape[1:]) * member.itemsize if member.shape else member.itemsize
        begin, end = start * row_bytes, stop * row_bytes
        if end - begin > self.maximum_slice_bytes:
            raise ValueError("array slice exceeds its explicitly selected value byte bound")
        raw = self.read_member_bytes(name, begin, end)
        import numpy as np
        shape = (stop - start, *member.shape[1:]) if member.shape else ()
        return np.frombuffer(raw, dtype=member.dtype).reshape(shape)

    def read_member_bytes(self, name: str, start: int, stop: int) -> bytes:
        member = self._member(name)
        if type(start) is not int or type(stop) is not int or not 0 <= start <= stop <= member.size_bytes:
            raise ValueError("dataset byte selection changes its exact member interval")
        if stop - start > self.maximum_slice_bytes:
            raise ValueError("dataset byte selection exceeds its explicitly selected value byte bound")
        output = bytearray(stop - start)
        cursor = 0
        for payload in self.iter_member_bytes(name):
            overlap_start, overlap_stop = max(start, cursor), min(stop, cursor + len(payload))
            if overlap_start < overlap_stop:
                output[overlap_start - start:overlap_stop - start] = memoryview(payload)[overlap_start - cursor:overlap_stop - cursor]
            cursor += len(payload)
        return bytes(output)

    def read_elements(self, name: str, start: int, stop: int):
        member = self._member(name)
        if (type(start) is not int or type(stop) is not int
                or not 0 <= start <= stop <= member.size_bytes // member.itemsize):
            raise ValueError("dataset element selection changes its exact flat C interval")
        raw = self.read_member_bytes(name, start * member.itemsize, stop * member.itemsize)
        import numpy as np
        return np.frombuffer(raw, dtype=member.dtype)

    def read_permuted_member_bytes(self, name, axis_order, start, stop):
        """Read a bounded byte interval of ``transpose(axis_order).ravel(C)``.

        Byte edges may split primitive values. Each contiguous source run is
        read through the same authenticated logical boundary; no whole-array
        transpose or new scientific identity is constructed.
        """
        member = self._member(name)
        _permuted_interval(member, axis_order, start, stop, self.maximum_slice_bytes)
        if axis_order == tuple(range(len(member.shape))):
            return self.read_member_bytes(name, start, stop)
        output = bytearray()
        for low, high in _permuted_logical_runs(member, axis_order, start, stop):
            output.extend(self.read_member_bytes(name, low, high))
        return bytes(output)

    def read_array(self, name: str):
        member = self._member(name)
        return self.read_array_slice(name, 0, member.first_axis_extent)

    @contextmanager
    def verified_session(self, *, block_size_bytes: int):
        """Own a checked lease; final verification terminates further delivery.

        Sealed descriptors need one full scan. Authenticated block leases need
        initial and final full scans plus bounded touched-block reads. Plain
        mutable sources retain the fresh complete checks of ordinary reads.
        Physical transforms include their admission scan in ``writer.finish``;
        their one-shot session reuses that proof and performs the final scan.
        """
        if (type(block_size_bytes) is not int
                or block_size_bytes < max((member.itemsize for member in self.manifest.members), default=1)):
            raise ValueError("dataset session requires its explicitly selected complete primitive block bound")
        mode = ("sealed" if type(self._source) is SealedFDByteSource else "blocks" if type(self._source) is AuthenticatedBlockByteSource
            else "physical" if type(self._source) is PhysicalFDByteSource else "mutable")
        lease = self._source if mode == "mutable" else self._source.acquire_lease(self.maximum_chunk_bytes)
        session = _VerifiedDatasetSession(self.manifest, lease, maximum_chunk_bytes=self.maximum_chunk_bytes,
            maximum_slice_bytes=self.maximum_slice_bytes, block_size_bytes=block_size_bytes, mode=mode)
        try:
            session.initialise()
            yield session
            session.verify_complete()
        finally:
            session.close()


@dataclass(frozen=True, slots=True)
class _MemberBlock:
    start: int
    stop: int
    sha256: str


class _VerifiedDatasetSession(ArrayDatasetReader):
    __slots__ = ("_mode", "_block_size_bytes", "_closed", "_refused", "_initial", "_final", "_index", "_authenticated_index")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("dataset admitted session proof, source and lease state are read-only")
        object.__setattr__(self, name, value)

    def __init__(self, manifest, source, *, maximum_chunk_bytes, maximum_slice_bytes, block_size_bytes, mode):
        super().__init__(manifest, source, maximum_chunk_bytes=maximum_chunk_bytes, maximum_slice_bytes=maximum_slice_bytes)
        self._mode, self._block_size_bytes, self._closed, self._refused = mode, block_size_bytes, False, False
        self._initial, self._final, self._index, self._authenticated_index = None, None, None, None

    @property
    def final_verification(self):
        return self._final

    def _ensure_active(self):
        if self._closed or self._refused or self._final is not None:
            raise ValueError("dataset verification session is closed, refused or already sealed")

    def initialise(self):
        self._ensure_active()
        if self._mode == "physical":
            self._source.validate_manifest(self.manifest)
            object.__setattr__(self, "_initial", DatasetVerification(self.manifest.identity,
                tuple((member.name, member.sha256) for member in self.manifest.members), self.manifest.size_bytes))
            return
        if self._mode == "sealed":
            self._source.verify_binding()
            self._source.validate_manifest(self.manifest)
        if self._mode != "blocks":
            object.__setattr__(self, "_initial", ArrayDatasetReader.verify_complete(self))
            return
        index = {}
        for member in self.manifest.members:
            blocks, pending, cursor = [], bytearray(), 0
            for payload in self._checked_member_bytes(member):
                offset = 0
                while offset < len(payload):
                    count = min(self._block_size_bytes - len(pending), len(payload) - offset)
                    pending.extend(memoryview(payload)[offset:offset + count])
                    offset += count
                    if len(pending) == self._block_size_bytes:
                        blocks.append(_MemberBlock(cursor, cursor + len(pending), sha256(pending).hexdigest()))
                        cursor += len(pending)
                        pending.clear()
            if pending:
                blocks.append(_MemberBlock(cursor, cursor + len(pending), sha256(pending).hexdigest()))
                cursor += len(pending)
            if cursor != member.size_bytes:
                raise ValueError("authenticated block index omits the complete verified member")
            index[member.name] = tuple(blocks)
        admitted = MappingProxyType(index)
        object.__setattr__(self, "_index", admitted)
        object.__setattr__(self, "_authenticated_index", admitted)
        object.__setattr__(self, "_initial", DatasetVerification(self.manifest.identity,
            tuple((member.name, member.sha256) for member in self.manifest.members), self.manifest.size_bytes))

    def verify_complete(self):
        if self._closed or self._refused:
            raise ValueError("dataset verification session is closed or refused")
        if self._final is not None:
            return self._final
        try:
            if self._mode == "sealed":
                self._source.verify_binding()
                object.__setattr__(self, "_final", self._initial)
            elif self._mode == "physical":
                self._source.verify_physical_complete()
                object.__setattr__(self, "_final", self._initial)
            else:
                if self._mode == "blocks" and self._index is not self._authenticated_index:
                    raise ValueError("authenticated block index was replaced or forged")
                object.__setattr__(self, "_final", ArrayDatasetReader.verify_complete(self))
            return self._final
        except Exception:
            object.__setattr__(self, "_refused", True)
            raise

    def read_member_bytes(self, name, start, stop):
        self._ensure_active()
        member = self._member(name)
        if type(start) is not int or type(stop) is not int or not 0 <= start <= stop <= member.size_bytes:
            raise ValueError("dataset byte selection changes its exact member interval")
        if stop - start > self.maximum_slice_bytes:
            raise ValueError("dataset byte selection exceeds its explicitly selected value byte bound")
        try:
            return self._read_verified_range(name, start, stop)
        except Exception:
            object.__setattr__(self, "_refused", True)
            raise

    def read_permuted_member_bytes(self, name, axis_order, start, stop):
        self._ensure_active()
        member = self._member(name)
        _permuted_interval(member, axis_order, start, stop, self.maximum_slice_bytes)
        try:
            if self._mode == "physical":
                raw = self._source.read_permuted_member_range(name, axis_order, start, stop)
                if raw is not None:
                    if type(raw) is not bytes or len(raw) != stop - start:
                        raise ValueError("admitted permuted dataset range changes its exact byte count")
                    return raw
            return super().read_permuted_member_bytes(name, axis_order, start, stop)
        except Exception:
            object.__setattr__(self, "_refused", True)
            raise

    def _read_verified_range(self, name, start, stop):
        self._ensure_active()
        if self._mode == "mutable":
            return ArrayDatasetReader.read_member_bytes(self, name, start, stop)
        if self._mode in ("sealed", "physical"):
            raw = self._source.read_member_range(name, start, stop)
            if type(raw) is not bytes or len(raw) != stop - start:
                raise ValueError("admitted dataset range changes its exact value byte count")
            return raw
        if self._index is not self._authenticated_index:
            raise ValueError("authenticated block index was replaced or forged")
        output = bytearray(stop - start)
        if start == stop:
            return bytes(output)
        blocks = self._index[name]
        for ordinal in range(start // self._block_size_bytes, (stop - 1) // self._block_size_bytes + 1):
            block = blocks[ordinal]
            raw = self._source.read_member_range(name, block.start, block.stop)
            if type(raw) is not bytes or len(raw) != block.stop - block.start or sha256(raw).hexdigest() != block.sha256:
                raise ValueError("authenticated dataset touched block changes its verified value bytes")
            begin, end = max(start, block.start), min(stop, block.stop)
            output[begin - start:end - start] = memoryview(raw)[begin - block.start:end - block.start]
        return bytes(output)

    def iter_member_bytes(self, name):
        self._ensure_active()
        member = self._member(name)
        try:
            if self._mode == "mutable":
                ArrayDatasetReader.verify_complete(self)
                for payload in self._checked_member_bytes(member):
                    self._ensure_active()
                    yield payload
            elif self._mode == "sealed":
                self._source.verify_binding()
                for payload in self._checked_member_bytes(member):
                    self._ensure_active()
                    yield payload
            else:
                for start in range(0, member.size_bytes, self.maximum_chunk_bytes):
                    # The member iterator's block payload is a streaming buffer;
                    # it does not consume the selected materialized-slice bound.
                    stop = min(start + self.maximum_chunk_bytes, member.size_bytes)
                    yield self._read_verified_range(name, start, stop)
        except Exception:
            object.__setattr__(self, "_refused", True)
            raise

    def close(self):
        if not self._closed:
            object.__setattr__(self, "_closed", True)
            if self._mode != "mutable":
                self._source.close()
