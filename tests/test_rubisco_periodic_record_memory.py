# SPDX-License-Identifier: MPL-2.0
"""Exposed pre-electronic entry controls; no native engine is imported or called."""
from dataclasses import dataclass
from decimal import Decimal
import sys
from types import ModuleType, SimpleNamespace
from typing import ClassVar

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import periodic_images, periodic_mm_remainder
from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm
from empirical_lawhood.execution.resources import process_memory
from empirical_lawhood.science.records.serialization import CanonicalRecord


@dataclass(frozen=True, slots=True)
class ExposedAtom(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/exposed-memory-atom'
    atomic_number: int


@dataclass(frozen=True, slots=True)
class ExposedModel(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/exposed-memory-model'
    atoms: tuple[ExposedAtom, ...]


@pytest.fixture(autouse=True)
def unentered_electronic_helpers(monkeypatch):
    # Evaluation imports these native helpers before the first backend call.
    # Their disclosed sentinels keep this pre-entry control independent of
    # optional engines and fail if any numerical helper is actually reached.
    def forbidden(*args, **kwargs):
        pytest.fail('pre-electronic control entered a native numerical helper')
    names = {
        'pyscf_periodic_dft': ('MemoryBoundedNumInt', 'bind_bounded_gradient'),
        'pyscf_periodic_jk': ('bind_bounded_jk', 'bind_bounded_jk_gradient'),
        'pyscf_periodic_diis': ('bind_checked_diis',),
    }
    for suffix, attributes in names.items():
        name = 'empirical_lawhood.adapters.rubisco.rubisco_response.'+suffix
        module = ModuleType(name)
        for attribute in attributes:
            setattr(module, attribute, forbidden)
        monkeypatch.setitem(sys.modules, name, module)


def exposed_entry(monkeypatch):
    # This deliberate constructor bypass tests the evaluation boundary only.
    # Its three literal atoms cannot stand for a qualified Rubisco model.
    model = ExposedModel(tuple(ExposedAtom(z) for z in (8, 1, 1)))
    expected = model.canonical_bytes()
    operator = object.__new__(periodic_qmmm.PeriodicCoupledOperator)
    operator.np, operator.unit = np, None
    operator.context = object()
    operator.physical_count = len(model.atoms)
    operator.numbers = [atom.atomic_number for atom in model.atoms[:2]]
    operator.qm_charge, operator.multiplicity = 0, 1
    operator.representation = model
    operator.settings = SimpleNamespace(memory_megabytes=64, direct_field_cutoff_angstrom=Decimal(6), basis='def2-svpd')
    operator.selection = SimpleNamespace(qm_formal_charge=0, spin_multiplicity=1)
    operator.qm, operator.mm_indices, operator.links = (0, 1), (2,), ()
    operator.coupling, operator.images = periodic_mm_remainder, periodic_images
    operator.lattice = np.eye(3)*20
    operator.evaluations = 0
    rows, phases = [], []
    operator.observe = rows.append
    def release_pages():
        assert not hasattr(model, '_canonical_encoding')
        assert all(not hasattr(atom, '_canonical_encoding') for atom in model.atoms)
        phases.append('allocator-release')
    monkeypatch.setattr(process_memory, 'release_unused_process_memory', release_pages)
    def refuse_electronic_construction(**kwargs):
        assert phases == ['allocator-release']
        assert not hasattr(model, '_canonical_encoding')
        assert kwargs['basis'] == 'def2-svpd' and kwargs['charge'] == 0 and kwargs['spin'] == 0
        assert tuple(z for z, _ in kwargs['atom']) == (8, 1)
        phases.append('exposed-backend-refusal')
        raise ArithmeticError('exposed refusal before electronic work')
    operator.gto = SimpleNamespace(M=refuse_electronic_construction)
    xyz = np.asarray([[0., 0., 0.], [.77, 0., .6], [3.5, 1., 0.]])
    return operator, model, expected, xyz, rows, phases


def test_first_entry_releases_only_caches_before_backend_and_preserves_failure(monkeypatch):
    operator, model, expected, xyz, rows, phases = exposed_entry(monkeypatch)
    with pytest.raises(ArithmeticError, match='exposed refusal'):
        operator.evaluate(xyz)
    assert [row['event'] for row in rows] == ['entry', 'record-encoding-release', 'error']
    assert rows[1]['released_record_encodings'] == 4 and rows[1]['evaluation'] == 1
    assert phases == ['allocator-release', 'exposed-backend-refusal']
    assert operator.evaluations == 1 and model.canonical_bytes() == expected


def test_invalid_coordinates_refuse_before_cache_release_and_entry(monkeypatch):
    operator, model, expected, xyz, rows, phases = exposed_entry(monkeypatch)
    with pytest.raises(ValueError, match='all finite physical coordinates'):
        operator.evaluate(xyz[:-1])
    assert hasattr(model, '_canonical_encoding') and model.canonical_bytes() == expected
    assert operator.evaluations == 0 and rows == [] and phases == []


def test_release_failure_cannot_return_success_or_enter_electronic_backend(monkeypatch):
    operator, model, expected, xyz, rows, phases = exposed_entry(monkeypatch)
    def fail(value):
        assert value is model
        raise MemoryError('exposed cache-release allocation failure')
    monkeypatch.setattr(periodic_qmmm, 'release_canonical_encodings', fail)
    with pytest.raises(MemoryError, match='exposed cache-release'):
        operator.evaluate(xyz)
    assert [row['event'] for row in rows] == ['entry', 'error']
    assert phases == [] and model.canonical_bytes() == expected


def test_later_entry_does_not_repeat_full_record_graph_walk(monkeypatch):
    operator, model, expected, xyz, rows, phases = exposed_entry(monkeypatch)
    with pytest.raises(ArithmeticError, match='exposed refusal'):
        operator.evaluate(xyz)
    assert model.canonical_bytes() == expected  # Explicitly rebuild for this control.
    def refuse_again(**kwargs):
        assert hasattr(model, '_canonical_encoding')
        raise ArithmeticError('second exposed refusal')
    operator.gto = SimpleNamespace(M=refuse_again)
    with pytest.raises(ArithmeticError, match='second exposed refusal'):
        operator.evaluate(xyz)
    assert [row['event'] for row in rows].count('record-encoding-release') == 1
    assert [row['event'] for row in rows].count('error') == 2
    assert operator.evaluations == 2 and phases == ['allocator-release', 'exposed-backend-refusal']
