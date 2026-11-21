# SPDX-License-Identifier: MPL-2.0
"""Thin PySCF integral adapter for the selected all-QM BP-SOMF operator.

The one- and two-electron conventions follow PySCF's SOC integral example
and Hess et al., DOI 10.1016/0009-2614(96)00228-2. Direct PySCF contractions
avoid materializing a four-AO tensor. No additional mean-field solve occurs.
"""

from hashlib import sha256
import time

from empirical_lawhood.domains.rubisco.rubisco_response.electronic_states import SpinOrbitMeanFieldSettings
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


from empirical_lawhood.domains.rubisco.electronic.spin_orbit import combine_breit_pauli_integrals


def breit_pauli_mean_field(mol, density, *, settings):
    import numpy as np
    from pyscf.lib.parameters import LIGHT_SPEED
    from pyscf.scf import jk
    exact(settings, SpinOrbitMeanFieldSettings)
    dm = np.asarray(density, dtype='<f8')
    n = mol.nao_nr()
    if (mol.cart or mol.has_ecp() or dm.shape != (n, n) or not np.isfinite(dm).all()
            or not np.allclose(dm, dm.T, rtol=0, atol=1e-10)):
        raise ValueError('BP-SOMF requires the original finite real density in its all-electron spherical AO basis')
    if 40*n*n*8 > settings.memory_megabytes*10**6:
        raise ValueError('BP-SOMF working arrays exceed the selected integral allocation')
    started = time.perf_counter()
    original_memory = mol.max_memory
    mol.max_memory = settings.memory_megabytes
    try:
        with mol.with_integral_screen(float(settings.integral_tolerance)):
            one = np.zeros((3, n, n))
            for atom in range(mol.natm):
                with mol.with_rinv_origin(mol.atom_coord(atom)):
                    one += mol.atom_charge(atom)*mol.intor('int1e_prinvxp_sph', comp=3)
            j, k1, k2 = jk.get_jk(mol, (dm, dm, dm),
                scripts=('ijkl,lk->ij', 'ijkl,jk->il', 'ijkl,li->kj'),
                intor='int2e_p1vxp1_sph', aosym='s1', comp=3, hermi=0)
        terms = combine_breit_pauli_integrals(
            one, j, k1, k2, light_speed_atomic_units=LIGHT_SPEED,
        )
        return dict(settings=settings.to_document(), density_sha256=sha256(dm.tobytes()).hexdigest(),
            light_speed_atomic_units=LIGHT_SPEED, coefficient='IMAGINARY_SPATIAL_HARTREE_MULTIPLY_BY_I_AND_PAULI_OVER_TWO',
            elapsed_seconds=time.perf_counter()-started, integral_engine='PYSCF_LIBCINT_DIRECT_SHELL_CONTRACTIONS',
            physical_spin_admission='UNEVALUABLE'), terms
    finally:
        mol.max_memory = original_memory
