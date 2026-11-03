"""Synthetic raw numerical operands only; no solver, source admission or force."""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
import struct
import subprocess
import sys

import numpy as np
import pytest

from empirical_lawhood.adapters.simulators.rubisco_electronic import coupled_return as r


def join(count=2):
    return r.CoupledReturnJoinV1(
        1, 'optimization', tuple(f'atom:{i}' for i in range(count)), ('H',) * count,
        123, '1' * 64, '2' * 64, '3' * 64, (('source', 456, '4' * 64),),
    )


def decoded(energy, gradient, j=None, **kwargs):
    return json.loads(r.encode_unverified_coupled_return(
        energy, gradient, j or join(), **kwargs))


def numeric(token):
    return struct.unpack('>d', bytes.fromhex(token['binary64_be']))[0]


def test_finite_full_native_array_preserves_binary_values_source_units_and_order():
    gradient = np.array([[.1, -0., 3.], [4., 5., 6.]])
    record = decoded(np.float64(-2.3), gradient)
    assert numeric(record['energy']) == -2.3
    assert record['energy']['type'] == 'numpy.float64'
    assert record['gradient']['native_array_shape'] == [2, 3]
    assert record['gradient']['native_array_dtype'] == 'float64'
    assert record['gradient']['native_array_value_bytes_hex'] == gradient.tobytes(order='C').hex()
    assert [[numeric(v) for v in row['items']]
            for row in record['gradient']['items']] == gradient.tolist()
    assert record['gradient']['items'][0]['items'][1]['binary64_be'] == '8000000000000000'
    assert record['physical_atom_ids'] == ['atom:0', 'atom:1']
    assert record['input_snapshot'] == {'bytes': 123, 'sha256': '1' * 64}
    assert record['source_bindings'] == [['source', 456, '4' * 64]]
    assert record['units']['ASH_Bohr_angstrom'] == '0.5291772109303'
    assert record['units']['raw_gradient_conversion_applied'] is False
    assert record['scientific_operand_admitted'] is False
    assert record['raw_scalar_token_count'] == 7
    assert record['energy']['native_scalar_value_bytes_hex'] == np.float64(-2.3).tobytes().hex()


def test_signed_nonfinite_and_nan_payload_are_strings_not_invalid_json_numbers():
    nan = struct.unpack('>d', bytes.fromhex('7ff8000000000042'))[0]
    record = decoded(nan, [[float('inf'), -float('inf'), nan], [1e99, 0., 0.]])
    assert record['energy']['binary64_be'] == '7ff8000000000042'
    tokens = record['gradient']['items'][0]['items']
    assert [v['hex'] for v in tokens] == ['inf', '-inf', 'nan']
    assert numeric(record['gradient']['items'][1]['items'][0]) == 1e99


def test_native_array_nan_payload_endian_and_noncontiguous_value_bytes_preserved():
    bits = np.array([0x7ff8000000000042, 0x8000000000000000,
                     0x7ff0000000000000, 0, 0, 0], dtype=np.uint64)
    native = bits.view(np.float64).reshape((2, 3))[:, ::-1]
    record = decoded(1., native)
    retained = record['gradient']
    assert retained['native_array_value_bytes_hex'] == native.tobytes(order='C').hex()
    assert retained['native_array_dtype_str'] == native.dtype.str
    assert retained['native_array_shape'] == [2, 3]
    assert retained['native_array_byte_order'] == 'C-logical-value-order'
    big_endian = native.astype('>f8')
    retained = decoded(1., big_endian)['gradient']
    assert retained['native_array_dtype_str'] == '>f8'
    assert retained['native_array_value_bytes_hex'] == big_endian.tobytes(order='C').hex()


def test_decimal_nonfinite_and_large_finite_token_preserve_original_spelling():
    record = decoded(Decimal('-Infinity'), [[Decimal('NaN42'), Decimal('1E+900'), Decimal('-0')]])
    assert record['energy']['token'] == '-Infinity'
    assert [v['token'] for v in record['gradient']['items'][0]['items']] == ['NaN42', '1E+900', '-0']


@pytest.mark.parametrize('gradient', [[[1., 2.]], [1., 2., 3.], [[1., 2., 3.], []]])
def test_bad_scientific_shape_is_completely_encoded_before_later_admission(gradient):
    record = decoded(1., gradient)
    assert len(record['gradient']['items']) == len(gradient)
    assert record['status'] == 'COMPLETE_UNVERIFIED_COUPLED_RETURN'
    assert record['scientific_operand_admitted'] is False


def test_serialization_limit_is_exact_and_never_returns_truncated_bytes():
    raw = r.encode_unverified_coupled_return(1., [[0., 0., 0.]], join(1))
    assert r.encode_unverified_coupled_return(1., [[0., 0., 0.]], join(1),
                                              maximum_bytes=len(raw)) == raw
    with pytest.raises(ValueError, match='serialization bound'):
        r.encode_unverified_coupled_return(1., [[0., 0., 0.]], join(1),
                                           maximum_bytes=len(raw) - 1)
    assert r.unverified_return_binding(raw) == {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}


def test_encoding_census_is_bounded_and_unsupported_objects_are_not_repr_fallbacks():
    with pytest.raises(ValueError, match='depth'):
        decoded(1., [[[[[1.]]]]])
    with pytest.raises(ValueError, match='length'):
        decoded(1., [0.] * (r.MAXIMUM_SCALARS + 1))
    with pytest.raises(ValueError, match='unsupported raw scalar'):
        decoded(1., [[object()]])
    with pytest.raises(ValueError, match='unsupported raw scalar'):
        decoded(np.longdouble('1.234567891234567891'), [[0., 0., 0.]])


def test_join_refuses_missing_or_reordered_source_atom_denominator():
    with pytest.raises(ValueError, match='joins'):
        replace(join(), physical_elements=('H',))
    with pytest.raises(ValueError, match='joins'):
        replace(join(), physical_atom_ids=('atom:0', 'atom:0'))
    with pytest.raises(ValueError, match='roles'):
        replace(join(), source_bindings=(('same', 1, '4' * 64), ('same', 2, '5' * 64)))


def test_encoder_import_is_cold_in_fresh_process():
    code = '''import sys
class Guard:
 def find_spec(self,name,*args):
  if name.split('.')[0] in ('numpy','pyscf','openmm','ash','scipy'):
   raise RuntimeError('forbidden native dependency '+name)
sys.meta_path.insert(0,Guard())
from empirical_lawhood.adapters.simulators.rubisco_electronic import coupled_return
assert 'numpy' not in sys.modules
'''
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
