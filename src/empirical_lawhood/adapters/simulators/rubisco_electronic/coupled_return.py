# SPDX-License-Identifier: MPL-2.0
"""Pure, bounded ordinary encoding of an *unverified* coupled native return.

This is raw interpretation, not a finite scientific record or a receipt. The
caller owns source admission, execution and writing these bytes before numerical
admission. No filesystem, solver, NumPy or custody provider is imported here.
"""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from numbers import Integral
import re
import struct

MAXIMUM_BYTES = 16 * 1024**2
MAXIMUM_ATOMS = 16384
MAXIMUM_SCALARS = 8 * MAXIMUM_ATOMS + 1
ASH_BOHR_ANGSTROM = '0.5291772109303'
LEGACY_BOHR_ANGSTROM = '0.52917726'


def _digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


@dataclass(frozen=True, slots=True)
class CoupledReturnJoinV1:
    """Previously admitted call/source joins; this class grants no authority."""
    ordinal: int
    phase: str
    physical_atom_ids: tuple[str, ...]
    physical_elements: tuple[str, ...]
    input_snapshot_bytes: int
    input_snapshot_sha256: str
    protocol_sha256: str
    assessment_sha256: str
    # role, bytes, SHA256; paths and I/O remain with the selected caller.
    source_bindings: tuple[tuple[str, int, str], ...]

    def __post_init__(self):
        if (type(self.ordinal) is not int or not 1 <= self.ordinal <= 101
                or self.phase not in ('optimization', 'fresh-final-gradient')
                or type(self.physical_atom_ids) is not tuple
                or not 1 <= len(self.physical_atom_ids) <= MAXIMUM_ATOMS
                or any(type(v) is not str or not 0 < len(v) <= 128
                       for v in self.physical_atom_ids)
                or len(set(self.physical_atom_ids)) != len(self.physical_atom_ids)
                or type(self.physical_elements) is not tuple
                or len(self.physical_elements) != len(self.physical_atom_ids)
                or any(type(v) is not str or re.fullmatch('[A-Z][a-z]?', v) is None
                       for v in self.physical_elements)
                or type(self.input_snapshot_bytes) is not int
                or not 0 < self.input_snapshot_bytes <= MAXIMUM_BYTES
                or not all(_digest(v) for v in (self.input_snapshot_sha256,
                                               self.protocol_sha256,
                                               self.assessment_sha256))
                or type(self.source_bindings) is not tuple
                or not 1 <= len(self.source_bindings) <= 32):
            raise ValueError('bounded exact call/atom/unit/source joins required')
        names = []
        for row in self.source_bindings:
            if (type(row) is not tuple or len(row) != 3
                    or type(row[0]) is not str or not 0 < len(row[0]) <= 128
                    or type(row[1]) is not int or not 0 < row[1] <= 64 * 1024**2
                    or not _digest(row[2])):
                raise ValueError('bounded source byte bindings required')
            names.append(row[0])
        if len(set(names)) != len(names):
            raise ValueError('source binding roles must be unique')


def _number(value):
    """No finite/value-cap checks: preserve the native numeric representation."""
    typename = type(value).__module__ + '.' + type(value).__qualname__
    if len(typename) > 256:
        raise ValueError('raw scalar type token exceeds encoding bound')
    if type(value) is bool:
        return {'kind': 'boolean', 'value': value, 'type': typename}
    if type(value) is Decimal:
        token = str(value)
        if len(token) > 4096:
            raise ValueError('raw Decimal token exceeds encoding bound')
        return {'kind': 'decimal', 'token': token, 'type': typename}
    if isinstance(value, Integral):
        integer = int(value)
        if integer.bit_length() > 4096:
            raise ValueError('raw integer token exceeds encoding bound')
        return {'kind': 'integer', 'token': str(integer), 'type': typename}
    if type(value) is float or typename in ('numpy.float16', 'numpy.float32', 'numpy.float64'):
        binary = float(value)
        # The big-endian binary64 token preserves signed zero and NaN payloads;
        # widening native float32 preserves its numeric value and source type.
        result = {'kind': 'binary-real', 'binary64_be': struct.pack('>d', binary).hex(),
                  'hex': binary.hex(), 'type': typename}
        if typename.startswith('numpy.'):
            result.update(native_scalar_dtype_str=value.dtype.str,
                          native_scalar_value_bytes_hex=value.tobytes().hex())
        return result
    if value is None:
        return {'kind': 'null'}
    if type(value) is str and len(value) <= 4096:
        return {'kind': 'text', 'token': value, 'type': typename}
    raise ValueError('unsupported raw scalar; complete capture refused')


def _tree(value, budget, depth=0):
    # Actual ASH returns a NumPy ndarray; recognize it without importing NumPy.
    array = type(value).__module__ == 'numpy' and type(value).__name__ == 'ndarray'
    array_bytes = None
    if array and depth == 0:
        if value.dtype.kind not in 'biuf' or value.nbytes > MAXIMUM_BYTES:
            raise ValueError('unsupported or oversized native array byte representation')
        # C-order logical value bytes preserve original dtype/endian/NaN bits,
        # including a non-contiguous view. This is not the backing allocation.
        array_bytes = value.tobytes(order='C').hex()
    if array and value.ndim == 0:
        return {'kind': 'native-zero-dimensional-array',
                'native_array_shape': [], 'native_array_dtype': str(value.dtype),
                'native_array_dtype_str': value.dtype.str,
                'native_array_value_bytes_hex': array_bytes,
                'native_array_byte_order': 'C-logical-value-order'}
    if type(value) in (tuple, list) or array:
        if depth >= 4 or len(value) > MAXIMUM_SCALARS:
            raise ValueError('raw sequence depth/length exceeds encoding bound')
        budget[1] += len(value)
        if budget[1] > 2 * MAXIMUM_SCALARS:
            raise ValueError('raw container census exceeds encoding bound')
        items = [_tree(v, budget, depth + 1) for v in value]
        result = {'kind': 'sequence', 'items': items}
        if array:
            result.update(native_array_shape=list(value.shape),
                          native_array_dtype=str(value.dtype))
            if depth == 0:
                result.update(native_array_dtype_str=value.dtype.str,
                              native_array_value_bytes_hex=array_bytes,
                              native_array_byte_order='C-logical-value-order')
        return result
    budget[0] += 1
    if budget[0] > MAXIMUM_SCALARS:
        raise ValueError('raw scalar census exceeds encoding bound')
    return _number(value)


def encode_unverified_coupled_return(energy, gradient, join, *, maximum_bytes=MAXIMUM_BYTES):
    """Return complete ordinary JSON bytes or refuse; never truncate an operand.

    Malformed shape, nonfinite and over-cap values remain raw tokens. Subsequent
    numerical admission belongs to the consumer. A serialization refusal is a
    capture failure, not evidence that the native function did not return.
    """
    if (type(join) is not CoupledReturnJoinV1 or type(maximum_bytes) is not int
            or not 1 <= maximum_bytes <= MAXIMUM_BYTES):
        raise ValueError('exact joined bounded raw encoding selection required')
    budget = [0, 0]
    record = {
        'schema': 'ordinary-complete-unverified-coupled-return-v1',
        'status': 'COMPLETE_UNVERIFIED_COUPLED_RETURN',
        'scientific_operand_admitted': False,
        'ordinal': join.ordinal, 'phase': join.phase,
        'physical_atom_ids': join.physical_atom_ids,
        'physical_elements': join.physical_elements,
        'input_snapshot': {'bytes': join.input_snapshot_bytes,
                           'sha256': join.input_snapshot_sha256},
        'protocol_sha256': join.protocol_sha256,
        'assessment_sha256': join.assessment_sha256,
        'source_bindings': join.source_bindings,
        'units': {'energy': 'Eh', 'gradient': 'Eh/ASH-Bohr',
                  'input_coordinates': 'angstrom',
                  'ASH_Bohr_angstrom': ASH_BOHR_ANGSTROM,
                  'native_legacy_Bohr_angstrom': LEGACY_BOHR_ANGSTROM,
                  'raw_gradient_conversion_applied': False},
        'energy': _tree(energy, budget), 'gradient': _tree(gradient, budget),
        'raw_scalar_token_count': budget[0],
    }
    encoder = json.JSONEncoder(sort_keys=True, separators=(',', ':'), allow_nan=False,
                               ensure_ascii=True)
    raw = bytearray()
    for chunk in encoder.iterencode(record):
        encoded = chunk.encode('ascii')
        if len(raw) + len(encoded) + 1 > maximum_bytes:
            raise ValueError('complete raw return exceeds selected serialization bound')
        raw.extend(encoded)
    raw.extend(b'\n')
    return bytes(raw)


def unverified_return_binding(raw):
    """Pure content identity, never a receipt or numerical acceptance claim."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAXIMUM_BYTES:
        raise ValueError('bounded encoded raw bytes required')
    return {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}
