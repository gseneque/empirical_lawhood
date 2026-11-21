# SPDX-License-Identifier: MPL-2.0
"""Refuse selected OpenMM PME implementation limits before electronic work.

OpenMM 8.3.1 allocates each PME grid as two binary64 elements per grid point.
CudaContext::addAutoclearBuffer accepts its byte count as a signed C++ int.
An oversized count can leave the charge-spreading grid uncleared and produce
finite but incorrect energies. This admission check changes no PME selection.
The original Reference implementation uses signed-int indices and reset bounds.
A separately built, source-bound library can advertise the index-width repair.
"""

from math import prod


def _grid_points(mesh):
    if (type(mesh) is not tuple or len(mesh) != 3
            or any(type(n) is not int or n <= 0 for n in mesh)):
        raise ValueError('PME admission requires its actual three-dimensional grid')
    return prod(mesh)


def validate_cuda_pme_grid(mesh):
    size = _grid_points(mesh)*16
    if size > 2**31-1:
        raise ValueError('selected OpenMM CUDA PME grid exceeds its signed buffer-clear byte count: '
            f'{mesh}, {size} bytes; select an explicit supported MM backend')
    return size


def validate_reference_pme_grid(mesh, *, index_bits=32, host_memory_bytes=None):
    points = _grid_points(mesh)
    if type(index_bits) is not int or index_bits not in (32, 64):
        raise ValueError('Reference PME requires an observed supported grid-index width')
    if index_bits == 32 and points > 2**31-1:
        raise ValueError('selected OpenMM Reference PME grid exceeds its signed grid-index range: '
            f'{mesh}, {points} grid points; the selected refinement requires a supported numerical engine')
    size = points*16
    if size > 2**63-1:
        raise ValueError('Reference PME grid exceeds its addressable byte range')
    if host_memory_bytes is not None and (type(host_memory_bytes) is not int or host_memory_bytes <= 0):
        raise ValueError('Reference PME requires a positive selected host-memory allocation')
    if points > 2**31-1 and host_memory_bytes is None:
        raise ValueError('large Reference PME grid requires its explicit host-memory allocation')
    if host_memory_bytes is not None and size > host_memory_bytes:
        raise ValueError('Reference PME complex grid alone exceeds the selected host-memory allocation: '
            f'{size} grid bytes, {host_memory_bytes} selected bytes')
    return points


def admit_cuda_mm_context(system, context, mm):
    _admit_mm_context(system, context, mm, validate_cuda_pme_grid)


def reference_pme_index_bits(mm):
    """Inspect the actual loaded extension's dependency, only at native entry."""
    import ctypes
    native = ctypes.CDLL(mm._openmm.__file__)
    try:
        capability = native.empirical_lawhood_reference_pme_index_bits
    except AttributeError:
        return 32
    capability.argtypes = []
    capability.restype = ctypes.c_int
    bits = capability()
    if bits != 64:
        raise ValueError('selected OpenMM library advertises an unsupported Reference PME index width')
    return bits


def admit_reference_mm_context(system, context, mm, *, host_memory_bytes=None):
    bits = reference_pme_index_bits(mm)
    meshes = _admit_mm_context(system, context, mm, lambda mesh: validate_reference_pme_grid(
        mesh, index_bits=bits, host_memory_bytes=host_memory_bytes))
    return dict(index_bits=bits, host_memory_allocation_bytes=host_memory_bytes,
        grids=[dict(mesh=mesh, complex_grid_bytes=_grid_points(mesh)*16) for mesh in meshes])


def _admit_mm_context(system, context, mm, validate):
    meshes = []
    for force in system.getForces():
        if type(force).__name__ == 'NonbondedForce' and force.getNonbondedMethod() == mm.NonbondedForce.PME:
            _, nx, ny, nz = force.getPMEParametersInContext(context)
            mesh = (int(nx), int(ny), int(nz))
            validate(mesh)
            meshes.append(mesh)
    return tuple(meshes)
