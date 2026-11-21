# SPDX-License-Identifier: MPL-2.0
"""Exercise the actual final SCF gate with exposed callbacks, no native engines."""
import sys
from types import ModuleType, SimpleNamespace as NS

import numpy as np
import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_images, periodic_mm_remainder
from tests.test_rubisco_periodic_record_memory import ExposedAtom, ExposedModel


class ExposedDerivativeBoundary(Exception):
    pass


@pytest.mark.parametrize('residual', (float('nan'), float('inf'), -float('inf'), 1e-7, 0.))
def test_final_recomputed_orbital_residual_must_be_finite_before_differentiation(monkeypatch, residual):
    def derivative():
        raise ExposedDerivativeBoundary('actual electronic gate admitted the finite residual')
    for suffix, attributes in {
        'pyscf_periodic_dft': ('MemoryBoundedNumInt', 'bind_bounded_gradient'),
        'pyscf_periodic_jk': ('bind_bounded_jk', 'bind_bounded_jk_gradient'),
        'pyscf_periodic_diis': ('bind_checked_diis',),
    }.items():
        name = 'empirical_lawhood.adapters.rubisco.rubisco_response.'+suffix
        module = ModuleType(name)
        for attribute in attributes:
            setattr(module, attribute, lambda *args, **kwargs: None)
        monkeypatch.setitem(sys.modules, name, module)
    model = ExposedModel(tuple(ExposedAtom(z) for z in (8, 1, 1)))
    operator = object.__new__(periodic_qmmm.PeriodicCoupledOperator)
    operator.np, operator.unit = np, None
    operator.context = object()
    operator.physical_count = len(model.atoms)
    operator.numbers = [atom.atomic_number for atom in model.atoms[:2]]
    operator.qm_charge, operator.multiplicity = 0, 1
    operator.representation = model
    operator.settings = NS(memory_megabytes=64, direct_field_cutoff_angstrom=6., basis='EXPOSED',
        ks_flavour='RKS', functional='EXPOSED', grid_level=1, reciprocal_mesh=(3, 3, 3),
        real_cutoff_angstrom=9., ewald_eta_inverse_bohr=.25, ewald_precision=1e-8,
        energy_tolerance_hartree=1e-9, orbital_gradient_tolerance=1e-7, maximum_scf_cycles=3)
    operator.selection = NS(qm_formal_charge=0, spin_multiplicity=1)
    operator.qm, operator.mm_indices, operator.links = (0, 1), (2,), ()
    operator.coupling, operator.images = periodic_mm_remainder, periodic_images
    operator.lattice, operator.embedding = np.eye(3)*20, np.zeros(1)
    operator.bohr_angstrom, operator.evaluations = .52917721092, 0
    rows = []; operator.observe = rows.append
    mol = NS(nao=2, ao_loc_nr=lambda: np.asarray((0, 1, 2)))
    operator.gto = NS(M=lambda **kwargs: mol)
    # The kernel's earlier convergence flag cannot license a nonfinite final
    # recomputation. No force, embedding, or MM engine may be reached in that case.
    mf = NS(grids=NS(level=0), _numint=None, mm_mol=NS(), mo_coeff=None, mo_occ=None,
        converged=True, kernel=lambda: -2., get_grad=lambda *args: np.asarray((residual,)),
        nuc_grad_method=derivative)
    operator.dft = NS(RKS=lambda unused: mf)
    operator.electronic = NS(add_mm_charges=lambda base, *args, **kwargs: base)
    xyz = np.asarray(((0., 0., 0.), (.77, 0., .6), (3.5, 1., 0.)))
    if residual == 0:
        with pytest.raises(ExposedDerivativeBoundary):
            operator.evaluate(xyz)
    else:
        with pytest.raises(ValueError, match='selected energy and orbital criteria'):
            operator.evaluate(xyz)
    assert any(r['event'] == 'electronic-return' for r in rows)
    assert not any(r['event'] in ('qm-gradient-entry', 'return') for r in rows)
