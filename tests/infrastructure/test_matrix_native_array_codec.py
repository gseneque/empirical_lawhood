# SPDX-License-Identifier: MPL-2.0
"""The native-return transport boundary has one bounded physical decoder."""

from io import BytesIO
import zipfile

import numpy as np
import pytest

from empirical_lawhood.infrastructure.matrix_array_io import decode_native_matrix_arrays


def archive(arrays):
    stream = BytesIO()
    np.savez_compressed(stream, **arrays)
    return stream.getvalue()


def test_native_decode_retains_exact_read_only_values_without_numpy_archive_loading(monkeypatch):
    values = {'complex': np.arange(24, dtype='<f8').view('<c16').reshape(3, 4),
        'ticks': np.arange(3, dtype='<i8')}
    raw = archive(values)
    monkeypatch.setattr(np, 'load', lambda *args, **kwargs: pytest.fail('second eager archive decoder'))
    result = decode_native_matrix_arrays(raw, {name: (value.dtype.str, value.shape) for name, value in values.items()})
    for name, original in values.items():
        assert result[name].dtype == original.dtype
        assert np.array_equal(result[name], original)
        assert not result[name].flags.writeable
    with pytest.raises(TypeError):
        result['extra'] = np.zeros(1)


@pytest.mark.parametrize('mutation', ('missing', 'extra', 'wrong-shape', 'wrong-dtype', 'fortran', 'object', 'duplicate'))
def test_native_decode_refuses_closed_member_and_header_mutations(mutation):
    values = {'positions': np.arange(6, dtype='<f8').reshape(2, 3)}
    if mutation == 'missing':
        values = {'other': values['positions']}
    elif mutation == 'extra':
        values['extra'] = np.zeros(1)
    elif mutation == 'wrong-shape':
        values['positions'] = values['positions'].reshape(3, 2)
    elif mutation == 'wrong-dtype':
        values['positions'] = values['positions'].astype('<i8')
    elif mutation == 'fortran':
        values['positions'] = np.asfortranarray(values['positions'])
    elif mutation == 'object':
        values['positions'] = np.array([[object()] * 3] * 2)
    raw = archive(values)
    if mutation == 'duplicate':
        stream = BytesIO(raw)
        with zipfile.ZipFile(stream, 'a') as package:
            with pytest.warns(UserWarning, match='Duplicate name'):
                package.writestr('positions.npy', package.read('positions.npy'))
        raw = stream.getvalue()
    with pytest.raises(ValueError):
        decode_native_matrix_arrays(raw, {'positions': ('<f8', (2, 3))})


def test_native_decode_bounds_declared_expansion_before_allocating(monkeypatch):
    raw = archive({'value': np.zeros(1, dtype='<f8')})
    monkeypatch.setattr(np, 'frombuffer', lambda *args, **kwargs: pytest.fail('expanded invalid declaration'))
    with pytest.raises(ValueError, match='expanded byte bound'):
        decode_native_matrix_arrays(raw, {'value': ('<f8', (2**30,))})


def test_native_decoder_leaves_nonfinite_scientific_interpretation_to_its_owner():
    raw = archive({'value': np.array([np.inf, np.nan], dtype='<f8')})
    result = decode_native_matrix_arrays(raw, {'value': ('<f8', (2,))})
    assert np.isinf(result['value'][0]) and np.isnan(result['value'][1])


def test_native_decoder_preserves_empty_and_scalar_member_layouts():
    values = {'empty': np.empty((0, 3), dtype='<c16'), 'scalar': np.asarray(5, dtype='<i8')}
    result = decode_native_matrix_arrays(archive(values), {name: (value.dtype.str, value.shape)
        for name, value in values.items()})
    assert result['empty'].shape == (0, 3) and result['scalar'].shape == ()
    assert result['scalar'].item() == 5
