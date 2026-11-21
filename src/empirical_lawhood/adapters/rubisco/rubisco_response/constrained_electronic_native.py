"""Native acquisition and external-format binding for the domain science."""

from hashlib import sha256
import json
import math
from pathlib import Path
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_states import constraint_groups

from empirical_lawhood.domains.rubisco.rubisco_response.constrained_observations import (
    UPSTREAM_FILES as _science_UPSTREAM_FILES,
)

STATE_ARRAYS = ('ao-overlap', 'mo-coefficients', 'mo-occupations', 'mo-energies',
    'density', 'constraint-projectors', 'constraint-multipliers', 'constraint-potential')


def build_constrained_mean_field(mol, state, *, gpu):
    if gpu is None:
        raise ValueError('the selected constrained solver requires its explicit GPU backend')
    import numpy as np
    import gpu4pyscf
    from gpu4pyscf.dft.ucdft import CDFT_UKS
    root = Path(gpu4pyscf.__file__).parent
    if gpu4pyscf.__version__ != '1.8.1' or any(
            sha256((root/name).read_bytes()).hexdigest() != digest for name, digest in _science_UPSTREAM_FILES.items()):
        raise ValueError('constrained solver or analytic projector gradient differs from the selected upstream source')
    charge, spin = constraint_groups(state)
    mf = CDFT_UKS(mol, charge_constraints=charge, spin_constraints=spin,
        method='lagrange', projection_method='minao')
    mf.micro_tol = float(state.multiplier_root_tolerance)
    mf.micro_max_cycle = state.multiplier_micro_steps
    initial = dict(zip((row.constraint_id for row in state.constraints), state.initial_multipliers_hartree, strict=True))
    mf.v_lagrange = np.asarray([float(initial[row.constraint_id]) for row in state.solver_order])
    return mf


def constraint_populations(mf, density=None):
    """Observe the actual upstream projectors without another SCF or transfer."""
    import cupy as cp
    dm = mf.make_rdm1() if density is None else density
    projectors = mf.build_projectors()
    values = []
    for i, weight in enumerate(projectors):
        density = dm[0]+dm[1] if i < len(mf.charge_targets) else dm[0]-dm[1]
        value = cp.trace(density @ weight)
        if abs(float(value.imag)) > 1e-10 or not math.isfinite(float(value.real)):
            raise ValueError('projected charge/spin population is nonreal or nonfinite')
        values.append(float(value.real))
    return tuple(values)


def constraint_residuals(mf, density=None):
    return tuple(value-float(target) for value, target in zip(
        constraint_populations(mf, density), (*mf.charge_targets, *mf.spin_targets), strict=True))


def constrained_diagnostics(mf, *, state):
    import cupy as cp
    observed = constraint_populations(mf)
    target = tuple(float(row.target_electrons) for row in state.solver_order)
    density, overlap = mf.make_rdm1(), mf.get_ovlp()
    populations = tuple(float(cp.trace(part @ overlap).real) for part in density)
    spin_square, effective_multiplicity = mf.spin_square()
    values = (*observed, *populations, float(spin_square), float(effective_multiplicity))
    if not all(math.isfinite(v) for v in values):
        raise ValueError('constrained electronic state has nonfinite population or spin diagnostics')
    return dict(state=state.identity.to_document(),
        constraint_ids=[row.constraint_id for row in state.solver_order],
        observed_electrons=list(observed), target_electrons=list(target),
        residual_electrons=[a-b for a, b in zip(observed, target, strict=True)],
        lagrange_multipliers_hartree=[float(v) for v in mf.v_lagrange],
        alpha_beta_electron_counts=list(populations), spin_square=float(spin_square),
        effective_multiplicity=float(effective_multiplicity), spin_purity_admission='UNEVALUABLE',
        projection=state.projection, upstream_files=_science_UPSTREAM_FILES)


def record_constrained_state(directory, *, mf, gpu, state, evaluation, diagnostics, name_prefix=''):
    """Retain original matrices, including solver multipliers, before gradients."""
    import numpy as np
    if type(evaluation) is not int or evaluation <= 0:
        raise ValueError('constrained capture omits the original force evaluation ordinal')
    root = Path(directory)
    if name_prefix:
        from empirical_lawhood.science.records.serialization import validate_stable_id
        validate_stable_id(name_prefix.rstrip('.'))
        if not name_prefix.endswith('.'):
            raise ValueError('electronic capture requires a separated prospective filename prefix')
    prefix = name_prefix+f'electronic.{evaluation:016d}.'
    values = (mf.get_ovlp(), mf.mo_coeff, mf.mo_occ, mf.mo_energy, mf.make_rdm1(),
        gpu.cp.asarray(mf.build_projectors()), mf.v_lagrange,
        mf.get_constraint_potential(mf.v_lagrange))
    members = {}
    def write(name, value):
        array = np.asarray(gpu.to_host(gpu.cp.asarray(value)))
        if np.iscomplexobj(array) or not np.isfinite(array).all():
            raise ValueError('selected collinear constrained state requires finite real original arrays')
        array = np.asarray(array, dtype='<f8', order='C')
        with (root/(prefix+name+'.npy')).open('xb') as stream:
            np.save(stream, array, allow_pickle=False)
        members[name] = dict(shape=list(array.shape), dtype=array.dtype.str,
            sha256=sha256(array.tobytes()).hexdigest())
    for name, value in zip(STATE_ARRAYS, values, strict=True):
        write(name, value)
    spin_orbit = None
    if state.spin_orbit is not None:
        from empirical_lawhood.adapters.rubisco.rubisco_response.spin_orbit_native import breit_pauli_mean_field
        spin_orbit, terms = breit_pauli_mean_field(mf.mol,
            gpu.to_host(mf.make_rdm1()).sum(axis=0), settings=state.spin_orbit)
        for name, value in terms.items():
            write(name, value)
    with (root/(prefix+'state.json')).open('x') as stream:
        json.dump(dict(evaluation=evaluation, state=state.to_document(),
            diagnostics=diagnostics, arrays=members, spin_orbit=spin_orbit,
            ao_labels=list(mf.mol.ao_labels()), atom_charges=mf.mol.atom_charges().tolist(),
            atom_coordinates_bohr=mf.mol.atom_coords().tolist(),
            electrons=int(mf.mol.nelectron), alpha_beta_electrons=[int(v) for v in mf.mol.nelec]),
            stream, sort_keys=True, allow_nan=False)
        stream.write('\n')
