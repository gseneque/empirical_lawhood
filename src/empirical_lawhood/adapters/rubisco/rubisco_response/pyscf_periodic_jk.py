# SPDX-License-Identifier: MPL-2.0
"""Instance-local complete J/K contractions with observed memory headroom.

The selected environment must carry the exact-source complete-output cache
correction. This module changes thread concurrency, never integral selection,
screening, density matrices, components or the electronic Hamiltonian.
"""
from contextlib import contextmanager
import ctypes
import gc
from types import MethodType

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_memory import memory_observation
from empirical_lawhood.domains.rubisco.rubisco_response.pyscf_cvhf_allocation import ALLOCATION_MARKER


def select_jk_threads(*, nao, nbas, ncomp, contractions, maximum_threads,
        integral_workspace_elements, available_bytes):
    """Reserve complete outputs, reordered densities, tiles and integral work.

    Three output copies cover native return and gradient sign conversion.
    Shell-pair screening and fresh OpenMP stacks are also included. Half the
    remaining headroom stays available for other native temporaries.
    """
    positive = (nao, nbas, ncomp, contractions, maximum_threads)
    if (any(type(value) is not int or value < 1 for value in positive)
            or type(integral_workspace_elements) is not int or integral_workspace_elements < 0
            or type(available_bytes) is not int or available_bytes < 0):
        raise ValueError('complete J/K workspace requires positive dimensions and nonnegative headroom')
    # At most one shell per tile is a safe bound for both partial and full tiles.
    tile_index_bytes = 8*nbas**2*contractions
    fixed = 8*nao**2*contractions*(3*ncomp+2)+8*nbas**2*(contractions+4)
    per_thread = 8*nao**2*ncomp*contractions+tile_index_bytes+8*integral_workspace_elements+8*2**20
    selected = min(maximum_threads, (available_bytes-fixed)//(2*per_thread))
    if selected < 1:
        raise MemoryError('Not enough memory for one complete J/K contraction thread: '
            f'fixed_bytes={fixed}, per_thread_bytes={per_thread}, available_bytes={available_bytes}')
    return dict(threads=selected, maximum_threads=maximum_threads,
        fixed_workspace_bytes=fixed, per_thread_workspace_bytes=per_thread)


def _release_unused_pages():
    # Local native allocator maintenance. No framework state or limit changes.
    gc.collect()
    try:
        trim = ctypes.CDLL(None).malloc_trim
    except (AttributeError, OSError):
        return
    trim.argtypes, trim.restype = (ctypes.c_size_t,), ctypes.c_int
    trim(0)


def _require_complete_output_allocator(library):
    try:
        marker = getattr(library, ALLOCATION_MARKER)
    except AttributeError as error:
        raise ValueError('periodic J/K requires the selected complete-output CVHF allocation build') from error
    marker.argtypes, marker.restype = (), ctypes.c_int
    if marker() != 1:
        raise ValueError('periodic J/K allocation build marker disagrees')


def _integral_workspace(mol, ncomp, omega):
    from pyscf.scf import _vhf
    slices = (ctypes.c_int*8)(*([0, mol.nbas]*4))
    maximum_cache = _vhf.libcvhf.GTOmax_cache_size
    maximum_cache.restype = ctypes.c_size_t
    maximum_cache.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.c_int,
        ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)
    intor = mol._add_suffix('int2e' if ncomp == 1 else 'int2e_ip1')
    with mol.with_range_coulomb(omega):
        cache = int(maximum_cache(_vhf._fpointer(intor), slices, 4,
            mol._atm.ctypes.data_as(ctypes.c_void_p), mol.natm,
            mol._bas.ctypes.data_as(ctypes.c_void_p), mol.nbas,
            mol._env.ctypes.data_as(ctypes.c_void_p)))
    di = int(max(mol.ao_loc_nr()[1:]-mol.ao_loc_nr()[:-1]))
    return di**4*ncomp+2*di**2+cache


@contextmanager
def _workspace(mol, dm, *, ncomp, operators, omega, memory_megabytes, observe):
    import numpy as np
    from pyscf import lib
    density = np.asarray(dm)
    if (density.ndim < 2 or density.shape[-2:] != (mol.nao, mol.nao)
            or density.dtype.kind != 'f' or not np.isfinite(density).all()):
        raise ValueError('complete J/K requires finite real density matrices in the original AO basis')
    count = int(density.size//mol.nao**2)*operators
    _release_unused_pages()
    observed = memory_observation(memory_megabytes)
    workspace = _integral_workspace(mol, ncomp, omega)
    selection = select_jk_threads(nao=int(mol.nao), nbas=int(mol.nbas), ncomp=ncomp,
        contractions=count, maximum_threads=lib.num_threads(), integral_workspace_elements=workspace,
        available_bytes=observed['available_bytes'])
    if observe is not None:
        observe(dict(event='jk-thread-selection', basis_functions=int(mol.nao), components=ncomp,
            contractions=count, omega=omega, integral_workspace_elements=workspace, memory=observed, **selection))
    with lib.with_omp_threads(selection['threads']):
        yield


def bind_bounded_jk(mean_field, *, memory_megabytes, observe=None):
    """Bind only this mean-field instance, preserving the original call."""
    from pyscf.scf import _vhf
    _require_complete_output_allocator(_vhf.libcvhf)
    original = mean_field.get_jk

    def get_jk(self, mol=None, dm=None, hermi=1, with_j=True, with_k=True, omega=None):
        mol = self.mol if mol is None else mol
        dm = self.make_rdm1() if dm is None else dm
        if not with_j and not with_k:
            return original(mol, dm, hermi, with_j, with_k, omega)
        with _workspace(mol, dm, ncomp=1, operators=int(with_j)+int(with_k), omega=omega,
                memory_megabytes=memory_megabytes, observe=observe):
            return original(mol, dm, hermi, with_j, with_k, omega)

    mean_field.get_jk = MethodType(get_jk, mean_field)
    return mean_field


def bind_bounded_jk_gradient(derivative, *, memory_megabytes, observe=None):
    """Gradient J and K bypass get_jk; bind all three original routes."""
    from pyscf.scf import _vhf
    _require_complete_output_allocator(_vhf.libcvhf)

    def wrap(original, operators):
        def invoke(self, mol=None, dm=None, hermi=0, omega=None):
            mol = self.mol if mol is None else mol
            dm = self.base.make_rdm1() if dm is None else dm
            with _workspace(mol, dm, ncomp=3, operators=operators, omega=omega,
                    memory_megabytes=memory_megabytes, observe=observe):
                return original(mol, dm, hermi, omega)
        return MethodType(invoke, derivative)

    for name, operators in (('get_jk', 2), ('get_j', 1), ('get_k', 1)):
        setattr(derivative, name, wrap(getattr(derivative, name), operators))
    return derivative
