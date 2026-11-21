"""Native acquisition and external-format binding for the domain science."""

from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_mm_precision import (
    PREFIX as _science_PREFIX,
)

def retain_molecular_precision(*, system, context, coordinates_angstrom, directory):
    """Retain two complete MM returns without changing the producing context."""
    import numpy as np
    import openmm as mm
    from openmm import unit
    from empirical_lawhood.adapters.rubisco.rubisco_response.amber_system_copy import clone_amber_system, native_system_sha256

    root = Path(directory)
    xyz = np.asarray(coordinates_angstrom, dtype='<f8')
    count = system.getNumParticles()
    if xyz.shape != (count, 3) or not np.isfinite(xyz).all():
        raise ValueError('molecular precision requires all finite physical coordinates')
    platform = context.getPlatform()
    properties = {'Precision': 'double', 'DeviceIndex': '0', 'DeterministicForces': 'true'}
    if platform.getName() != 'CUDA' or any(platform.getPropertyValue(context, k) != v for k, v in properties.items()):
        raise ValueError('molecular precision requires the original CUDA double context')
    copied, digest = clone_amber_system(system, mm=mm, unit=unit)
    original_nb = [force for force in system.getForces() if type(force).__name__ == 'NonbondedForce']
    copied_nb = [force for force in copied.getForces() if type(force).__name__ == 'NonbondedForce']
    if len(original_nb) != 1 or len(copied_nb) != 1:
        raise ValueError('molecular precision requires one complete nonbonded population')
    method = original_nb[0].getNonbondedMethod()
    mesh = None
    if method == mm.NonbondedForce.PME:
        alpha, nx, ny, nz = original_nb[0].getPMEParametersInContext(context)
        alpha = float(alpha.value_in_unit(unit.nanometer**-1) if unit.is_quantity(alpha) else alpha)
        mesh = [alpha, int(nx), int(ny), int(nz)]
        copied_nb[0].setPMEParameters(*mesh)
    elif method != mm.NonbondedForce.Ewald:
        raise ValueError('molecular precision requires the selected periodic Ewald or PME system')
    request = dict(version='1.0.0', physical_atom_count=count,
        coordinate_sha256=sha256(xyz.tobytes(order='C')).hexdigest(),
        remainder_parameter_sha256=digest, reference_parameter_sha256=native_system_sha256(copied, unit),
        cuda_properties=properties, method='PME' if mesh is not None else 'Ewald', matched_pme=mesh,
        scope='SAME_GEOMETRY_COMPLETE_MM_CUDA_REFERENCE', electronic_evaluations=0)
    with (root/(_science_PREFIX+'request.json')).open('x') as stream:
        json.dump(request, stream, sort_keys=True, allow_nan=False)
    timings = {}

    def capture(label, selected):
        started = perf_counter()
        selected.setPositions(xyz*.1*unit.nanometer)
        state = selected.getState(getEnergy=True, getForces=True)
        values = (np.asarray(state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole), dtype='<f8'),
            np.asarray(state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer), dtype='<f8'))
        for quantity, value in zip(('energy-kj-mol', 'forces-kj-mol-nm'), values, strict=True):
            with (root/(_science_PREFIX+label+'-'+quantity+'.npy')).open('xb') as stream:
                np.save(stream, value, allow_pickle=False)
        timings[label] = perf_counter()-started
        if not all(np.isfinite(value).all() for value in values):
            raise ValueError('molecular precision returned nonfinite original MM operands')

    capture('cuda', context)
    integrator = mm.VerletIntegrator(.0005)
    reference = mm.Context(copied, integrator, mm.Platform.getPlatformByName('Reference'))
    try:
        capture('reference', reference)
        if mesh is not None:
            actual = copied_nb[0].getPMEParametersInContext(reference)
            actual_alpha = actual[0]
            actual_alpha = float(actual_alpha.value_in_unit(unit.nanometer**-1) if unit.is_quantity(actual_alpha) else actual_alpha)
            if [actual_alpha, *map(int, actual[1:])] != mesh:
                raise ValueError('molecular precision reference changed the selected CUDA PME allocation')
    finally:
        del reference, integrator
    if native_system_sha256(system, unit) != digest:
        raise ValueError('molecular precision changed the original complete MM system')
    with (root/(_science_PREFIX+'completion.json')).open('x') as stream:
        json.dump(dict(version='1.0.0', request_sha256=sha256((root/(_science_PREFIX+'request.json')).read_bytes()).hexdigest(),
            platforms=['CUDA', 'Reference'], completed_mm_evaluations=2, electronic_evaluations=0,
            wall_seconds=timings, original_system_unchanged=True), stream, sort_keys=True, allow_nan=False)
