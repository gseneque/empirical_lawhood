# SPDX-License-Identifier: MPL-2.0
"""Exposed DIIS storage controls; no enzyme or forecast qualification."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response import pyscf_periodic_diis as owner
from tests.test_rubisco_periodic_density_reuse import numeric_operator as numeric_operator

pytestmark = pytest.mark.native('pyscf')


def instance(*, filename=None, observe=None):
    from pyscf.scf.diis import CDIIS
    holder = SimpleNamespace(DIIS=CDIIS, diis=True)
    owner.bind_checked_diis(holder, observe=observe)
    return holder.DIIS(None, filename)


@pytest.mark.parametrize('complex_values', [False, True])
@pytest.mark.parametrize('spin_channels', [1, 2])
@pytest.mark.parametrize('rollback', [0, 2])
def test_stock_cdiis_vectors_matrices_and_mixing_match_through_slot_reuse(
        tmp_path, complex_values, spin_channels, rollback):
    from pyscf.lib import diis as original
    from pyscf.scf.diis import CDIIS
    stock = CDIIS()
    rows = []
    candidate = instance(filename=str(tmp_path/'vectors.h5'), observe=rows.append)
    stock.space = candidate.space = 3
    stock.rollback = candidate.rollback = rollback
    stock.damp = candidate.damp = .13
    stock.Corth = candidate.Corth = np.eye(7)
    # Even the old per-instance in-core option cannot defeat this explicitly
    # bound periodic storage policy. No global threshold or class is modified.
    candidate.incore = True
    threshold = original.INCORE_SIZE
    rng = np.random.default_rng(29107)
    previous = None
    shape = (7, 7) if spin_channels == 1 else (2, 7, 7)
    try:
        for step in range(11):
            values = []
            for _ in range(2):
                value = rng.normal(size=shape)
                if complex_values:
                    value = value+1j*rng.normal(size=shape)
                values.append(value+value.swapaxes(-1, -2).conj())
            density, fock = values
            kwargs = dict(f_prev=previous) if previous is not None else {}
            expected = stock.update(np.eye(7), density, fock, **kwargs)
            actual = candidate.update(np.eye(7), density, fock, **kwargs)
            np.testing.assert_array_equal(actual, expected)
            np.testing.assert_array_equal(candidate._H, stock._H)
            assert candidate._head == stock._head and candidate._bookkeep == stock._bookkeep
            assert candidate._buffer == {} and set(candidate._diisfile) == set(stock._buffer)
            for key, value in stock._buffer.items():
                saved = candidate._diisfile[key]
                assert saved.shape == value.shape and saved.dtype == value.dtype
                np.testing.assert_array_equal(saved[:], value)
            assert rows[-1]['in_memory_vector_count'] == 0
            assert rows[-1]['stored_bytes'] == sum(value.nbytes for value in stock._buffer.values())
            assert rows[-1]['stored_vectors'] <= 2*stock.space
            previous = expected.copy()
        assert original.INCORE_SIZE == threshold and CDIIS._store is original.DIIS._store
        assert len(rows) == 22 and all(row['event'] == 'diis-vector-storage' for row in rows)
    finally:
        candidate._diisfile.close()


def test_temporary_vectors_use_selected_scratch_and_are_separate_and_removed(tmp_path, monkeypatch):
    from pyscf.lib import param
    monkeypatch.setattr(param, 'TMPDIR', str(tmp_path))
    first, second = instance(), instance()
    paths = []
    for obj in (first, second):
        obj._store('x0', np.arange(13, dtype=float))
        path = Path(obj._diisfile.filename)
        assert path.parent == tmp_path and path.is_file()
        paths.append(path)
    assert paths[0] != paths[1]
    for obj in (first, second):
        obj._diisfile.close()
    assert all(not path.exists() for path in paths)


def test_disk_creation_failure_propagates_without_in_memory_fallback(monkeypatch):
    from pyscf.lib import diis as original
    rows, calls = [], []
    obj = instance(observe=rows.append)
    def refuse(*args, **kwargs):
        calls.append((args, kwargs))
        raise OSError('exposed scratch refusal')
    monkeypatch.setattr(original.misc, 'H5TmpFile', refuse)
    with pytest.raises(OSError, match='exposed scratch refusal'):
        obj._store('x0', np.arange(13, dtype=float))
    assert len(calls) == 1 and obj._buffer == {} and obj._diisfile is None and rows == []


def test_preexisting_memory_vectors_refuse_without_creating_scratch():
    obj = instance()
    original = np.arange(13, dtype=float)
    obj._buffer['x0'] = original
    with pytest.raises(ValueError, match='restored in-memory vectors'):
        obj._store('e0', original)
    assert obj._buffer['x0'] is original and obj._diisfile is None


@pytest.mark.parametrize('family', ['generic', 'ediis', 'adiis', 'existing-instance'])
def test_other_diis_families_or_existing_instances_are_not_silently_rebound(family):
    from pyscf.lib.diis import DIIS
    from pyscf.scf.diis import ADIIS, CDIIS, EDIIS
    cls = {'generic': DIIS, 'ediis': EDIIS, 'adiis': ADIIS, 'existing-instance': CDIIS}[family]
    prior = CDIIS() if family == 'existing-instance' else True
    holder = SimpleNamespace(DIIS=cls, diis=prior)
    with pytest.raises(ValueError, match='new original CDIIS instance'):
        owner.bind_checked_diis(holder)
    assert holder.DIIS is cls and holder.diis is prior


def recovery_instance(tmp_path, matrix):
    rows = []
    obj = instance(filename=str(tmp_path/'recovery-vectors.h5'), observe=rows.append)
    vectors = np.arange((len(matrix)-1)*13, dtype=float).reshape(len(matrix)-1, 13)/17
    obj._H = matrix.copy()
    obj._bookkeep = list(range(len(vectors)))
    obj._head = len(vectors)
    for index, vector in enumerate(vectors):
        obj._store('x'+str(index), vector)
    rows.clear()
    return obj, rows, vectors


@pytest.mark.parametrize('diagonal', [1., 0.])
def test_checked_eigenpair_recovery_mixes_original_disk_vectors(tmp_path, monkeypatch, diagonal):
    import scipy.linalg
    matrix = np.eye(7)*diagonal
    matrix[0, 0] = 0
    matrix[1:, 0] = matrix[0, 1:] = 1
    obj, rows, vectors = recovery_instance(tmp_path, matrix)
    expected = vectors.mean(axis=0)
    actual_eigh = scipy.linalg.eigh
    calls = []
    def fail_once(h, **kwargs):
        calls.append(kwargs.get('driver', 'evr'))
        if len(calls) == 1:
            raise np.linalg.LinAlgError('Internal Error.')
        return actual_eigh(h, **kwargs)
    try:
        np.testing.assert_allclose(obj.extrapolate(), expected, rtol=0, atol=1e-12)
        monkeypatch.setattr(scipy.linalg, 'eigh', fail_once)
        np.testing.assert_allclose(obj.extrapolate(), expected, rtol=0, atol=1e-12)
        assert calls == ['evr', 'ev']
        assert [row['event'] for row in rows] == ['diis-eigensolver-error', 'diis-eigensolver-recovery']
        np.testing.assert_array_equal(obj._H, matrix)
        assert obj._buffer == {}
    finally:
        obj._diisfile.close()


@pytest.mark.parametrize('failure', ['nonfinite', 'nonhermitian', 'invalid-eigenpairs', 'unrelated-error'])
def test_invalid_recovery_or_unrelated_error_still_refuses(tmp_path, monkeypatch, failure):
    import scipy.linalg
    matrix = np.eye(4)
    matrix[0, 0] = 0
    matrix[1:, 0] = matrix[0, 1:] = 1
    if failure == 'nonfinite':
        matrix[1, 1] = np.inf
    elif failure == 'nonhermitian':
        matrix[1, 0] += .1
    obj, rows, _ = recovery_instance(tmp_path, matrix)
    actual_eigh, calls = scipy.linalg.eigh, []
    def refuse(h, **kwargs):
        calls.append(kwargs.get('driver', 'evr'))
        if len(calls) == 1:
            raise np.linalg.LinAlgError('Singular matrix' if failure == 'unrelated-error' else 'Internal Error.')
        if failure == 'invalid-eigenpairs':
            return np.ones(len(h)), np.ones_like(h)
        return actual_eigh(h, **kwargs)
    monkeypatch.setattr(scipy.linalg, 'eigh', refuse)
    try:
        if failure == 'unrelated-error':
            with pytest.raises(np.linalg.LinAlgError, match='Singular matrix'):
                obj.extrapolate()
            assert calls == ['evr'] and rows == []
        else:
            message = 'eigenpairs fail' if failure == 'invalid-eigenpairs' else 'finite Hermitian matrix'
            with pytest.raises(ValueError, match=message):
                obj.extrapolate()
            assert calls == (['evr', 'ev'] if failure == 'invalid-eigenpairs' else ['evr'])
            assert [row['event'] for row in rows] == ['diis-eigensolver-error']
    finally:
        obj._diisfile.close()


@pytest.mark.native('openmm')
@pytest.mark.parametrize('flavour', ['RKS', 'UKS'])
def test_complete_periodic_force_matches_original_diis_storage(numeric_operator, monkeypatch, flavour):
    from pyscf.lib.diis import DIIS
    selected_bind = owner.bind_checked_diis
    def original_storage(mf, *, observe=None):
        selected_bind(mf, observe=observe)
        # Disclosed baseline: the exact installed _store method with the same
        # checked mixing class. This affects this fresh control process only.
        mf.DIIS._store = DIIS._store
        return mf
    baseline, xyz, original_rows = numeric_operator(flavour, False)
    monkeypatch.setattr(owner, 'bind_checked_diis', original_storage)
    expected = baseline.evaluate(xyz)
    monkeypatch.setattr(owner, 'bind_checked_diis', selected_bind)
    candidate, candidate_xyz, rows = numeric_operator(flavour, False)
    np.testing.assert_array_equal(candidate_xyz, xyz)
    actual = candidate.evaluate(candidate_xyz)
    energy_error = abs(actual['energy_hartree']-expected['energy_hartree'])
    gradient_error = float(np.max(np.abs(actual['gradient_hartree_per_bohr']-expected['gradient_hartree_per_bohr'])))
    assert energy_error < 1e-10 and gradient_error < 3e-9
    assert actual['orbital_gradient_norm'] < 1e-7 and expected['orbital_gradient_norm'] < 1e-7
    assert sum(row['event'] == 'return' for row in rows) == sum(row['event'] == 'return' for row in original_rows) == 1
    assert not any(row['event'] in ('diis-vector-storage', 'diis-eigensolver-error') for row in original_rows)
    stored = [row for row in rows if row['event'] == 'diis-vector-storage']
    assert stored and all(row['in_memory_vector_count'] == 0 for row in stored)
    assert not any(row['event'] == 'diis-eigensolver-error' for row in rows)
    print(json.dumps(dict(control='complete-periodic-DIIS-storage', flavour=flavour,
        complete_energy_gradient_calls=2, energy_error_hartree=energy_error,
        maximum_gradient_error_hartree_per_bohr=gradient_error,
        original_energy_hartree=expected['energy_hartree'], candidate_energy_hartree=actual['energy_hartree'],
        original_gradient_hartree_per_bohr=expected['gradient_hartree_per_bohr'].tolist(),
        candidate_gradient_hartree_per_bohr=actual['gradient_hartree_per_bohr'].tolist(),
        original_iterations=sum(row['event'] == 'scf-iteration' for row in original_rows),
        candidate_iterations=sum(row['event'] == 'scf-iteration' for row in rows),
        candidate_maximum_vector_bytes=max(row['stored_bytes'] for row in stored),
        constructor_and_enzyme_admission=False)))
