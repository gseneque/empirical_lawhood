# SPDX-License-Identifier: MPL-2.0
"""Bounded independent reconstruction of original constrained electronic states."""

from hashlib import sha256
from io import BytesIO
import json
import math
from pathlib import PurePosixPath
from types import SimpleNamespace

from empirical_lawhood.adapters.matrix_storage.matrix_array_io import matrix_npy_layout
from empirical_lawhood.adapters.rubisco.rubisco_response.constrained_electronic_native import STATE_ARRAYS
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_states import ElectronicStateCriteria
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_read import authenticate_probe_files, read_periodic_probe
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import ConstrainedPeriodicForceSettings
from empirical_lawhood.domains.rubisco.electronic.spin_orbit import SOC_ARRAYS


def _array(raw, *, description, maximum_bytes):
    import numpy as np
    shape = description.get('shape')
    if (type(shape) is not list or not shape or len(shape) > 3
            or any(type(x) is not int or x <= 0 for x in shape)
            or description.get('dtype') != '<f8' or math.prod(shape)*8 > maximum_bytes):
        raise ValueError('original electronic matrix changes its bounded finite-real layout')
    stream = BytesIO(raw)
    kind = matrix_npy_layout(stream, SimpleNamespace(file_size=len(raw), flag_bits=0),
        dtype='<f8', shape=tuple(shape))
    payload = stream.read()
    if sha256(payload).hexdigest() != description.get('sha256'):
        raise ValueError('original electronic matrix changes its exact recorded array bytes')
    a = np.frombuffer(payload, dtype=kind).reshape(tuple(shape))
    if not np.isfinite(a).all():
        raise ValueError('original electronic matrix contains nonfinite values')
    return a


def assess_electronic_arrays(*, state, metadata, arrays, criteria):
    """Numerical consistency only; original custody is owned by the caller."""
    import numpy as np
    exact(criteria, ElectronicStateCriteria)
    tolerance = float(criteria.matrix_tolerance)
    expected = set(STATE_ARRAYS) | (set(SOC_ARRAYS) if state.spin_orbit is not None else set())
    if set(arrays) != expected:
        raise ValueError('electronic return changes the complete selected matrix census')
    s, c, o = (arrays[k] for k in ('ao-overlap', 'mo-coefficients', 'mo-occupations'))
    density, projectors, multipliers, potential = (arrays[k] for k in (
        'density', 'constraint-projectors', 'constraint-multipliers', 'constraint-potential'))
    n, m = len(s), len(state.constraints)
    shapes = {'ao-overlap':(n, n), 'mo-coefficients':(2, n, n), 'mo-occupations':(2, n),
        'mo-energies':(2, n), 'density':(2, n, n), 'constraint-projectors':(m, n, n),
        'constraint-multipliers':(m,), 'constraint-potential':(2, n, n),
        **({name:(3, n, n) for name in SOC_ARRAYS} if state.spin_orbit is not None else {})}
    if any(a.shape != shapes[k] or not np.isfinite(a).all() for k, a in arrays.items()):
        raise ValueError('electronic return changes the complete AO, orbital or constraint dimensions')
    if 8*n*n*(64+4*m) > criteria.maximum_workspace_bytes:
        raise ValueError('electronic matrix assessment exceeds its selected complete workspace')
    errors = {}
    def close(name, actual, expected):
        error = float(np.max(np.abs(actual-expected)))
        errors[name] = error
        return error <= tolerance
    numerical = close('overlap_symmetry', s, s.T)
    eigen = np.linalg.eigvalsh(s)
    if np.min(eigen) <= 0:
        raise ValueError('original AO metric is not positive definite')
    if not np.isin(o, (0, 1)).all():
        raise ValueError('constrained determinant has nonbinary or incomplete original occupations')
    counts = tuple(int(x) for x in o.sum(axis=1))
    if (list(counts) != metadata['alpha_beta_electrons'] or sum(counts) != metadata['electrons']
            or counts[0]-counts[1] != state.spin_multiplicity-1
            or sum(metadata['atom_charges'])-state.qm_formal_charge != sum(counts)
            or len(metadata['ao_labels']) != n):
        raise ValueError('electronic return changes its exact electron, spin-projection or AO denominator')
    numerical &= close('orbital_orthonormality', c.transpose(0, 2, 1)@s@c, np.eye(n))
    reconstructed = (c*o[:, None, :])@c.transpose(0, 2, 1)
    numerical &= close('occupied_density', density, reconstructed)
    numerical &= close('projector_symmetry', projectors, projectors.transpose(0, 2, 1))
    # Projected Lowdin MINAO groups are S-metric projectors, including unions
    # of physical atom groups. This tests the original matrices algebraically.
    numerical &= close('projector_idempotence', projectors@np.linalg.solve(s, projectors), projectors)
    expected_potential = np.zeros_like(potential)
    populations = []
    for i, row in enumerate(state.solver_order):
        sign = 1 if row.kind == 'ELECTRON_POPULATION' else -1
        expected_potential[0] += multipliers[i]*projectors[i]
        expected_potential[1] += sign*multipliers[i]*projectors[i]
        populations.append(float(np.trace((density[0]+sign*density[1])@projectors[i])))
    numerical &= close('constraint_potential', potential, expected_potential)
    residuals = [v-float(r.target_electrons) for v, r in zip(populations, state.solver_order, strict=True)]
    numerical &= max(abs(v) for v in residuals) <= float(state.population_tolerance_electrons)
    ca, cb = c[0][:, o[0] == 1], c[1][:, o[1] == 1]
    spin_square = .25*(counts[0]-counts[1])**2+.5*sum(counts)-float(np.sum(np.abs(ca.T@s@cb)**2))
    spin = .5*(state.spin_multiplicity-1)
    excess = spin_square-spin*(spin+1)
    diag = metadata['diagnostics']
    numerical &= close('observed_constraint_populations', np.asarray(populations), np.asarray(diag['observed_electrons']))
    numerical &= close('observed_spin_square', np.asarray(spin_square), np.asarray(diag['spin_square']))
    numerical &= close('observed_multipliers', multipliers, np.asarray(diag['lagrange_multipliers_hartree']))
    numerical &= close('observed_electron_counts', np.asarray(counts), np.asarray(diag['alpha_beta_electron_counts']))
    spin_status = 'SATISFIED' if -tolerance <= excess <= float(criteria.maximum_spin_square_excess) else 'FALSIFIED'
    if state.spin_orbit is not None:
        record = metadata['spin_orbit']
        spin_sum = np.asarray(density.sum(axis=0), dtype='<f8', order='C')
        if (record['settings'] != state.spin_orbit.to_document()
                or record['density_sha256'] != sha256(spin_sum.tobytes()).hexdigest()
                or record['coefficient'] != 'IMAGINARY_SPATIAL_HARTREE_MULTIPLY_BY_I_AND_PAULI_OVER_TWO'
                or record['physical_spin_admission'] != 'UNEVALUABLE'):
            raise ValueError('spin-orbit return substitutes its selected operator or original density')
        for name in SOC_ARRAYS:
            numerical &= close(name+'_antisymmetry', arrays[name], -arrays[name].transpose(0, 2, 1))
    return dict(selected_matrix_criteria='SATISFIED' if numerical else 'FALSIFIED',
        selected_spin_square_criteria=spin_status, matrix_errors=errors,
        constraint_populations_electrons=populations, constraint_residuals_electrons=residuals,
        spin_square=spin_square, nominal_spin_square=spin*(spin+1), spin_square_excess=excess,
        higher_spin_weight_upper_bound=max(0., excess)/(2*(spin+1)) if excess >= -tolerance else None,
        minimum_overlap_eigenvalue=float(np.min(eigen)), original_electrons=sum(counts),
        interpretation='CONDITIONAL_COLLINEAR_DETERMINANT', physical_diabat_admission='UNEVALUABLE')


def read_constrained_electronic_state(*, config, representation, original_result,
        native_subwork, assessor_source, criteria):
    exact(criteria, ElectronicStateCriteria)
    exact(config.selection.electronic, ConstrainedPeriodicForceSettings)
    state = config.selection.electronic.state
    readout = read_periodic_probe(config=config, representation=representation,
        original_result=original_result, native_subwork=native_subwork, assessor_source=assessor_source,
        readout_id='constrained.'+original_result.definition.subwork_id)
    returned = original_result.returned
    base = dict(state=state.to_document(), original_probe=readout.to_document(),
        native_error=returned.error,
        assessment=None, energy_hartree=None, metadata=None, complete=False)
    names = {PurePosixPath(row.relative_path).name for row in returned.files.files}
    prefix = 'electronic.0000000000000001.'
    if prefix+'state.json' not in names:
        if returned.error is None:
            raise ValueError('successful constrained probe omits its complete original electronic state')
        return base, {}
    selected = {}
    authenticate_probe_files(native_subwork, original_result.definition, returned,
        member_validators={prefix+'state.json':(2**20, lambda raw:selected.update(json.loads(raw))),
            **({'native-return-metadata.json':(2**20, lambda raw:base.update(native_metadata=json.loads(raw)))}
                if 'native-return-metadata.json' in names else {})})
    if (selected.get('state') != state.to_document() or selected.get('evaluation') != 1
            or type(selected.get('arrays')) is not dict):
        raise ValueError('electronic state capture substitutes the original selected state or evaluation')
    expected = set(STATE_ARRAYS) | (set(SOC_ARRAYS) if state.spin_orbit is not None else set())
    if set(selected['arrays']) != expected:
        raise ValueError('electronic state capture changes its full selected matrix census')
    total = sum(math.prod(d.get('shape', []))*8 for d in selected['arrays'].values())
    if total*8 > criteria.maximum_workspace_bytes:
        raise ValueError('complete original electronic arrays exceed the selected analysis allocation')
    arrays = {}
    validators = {}
    for name, description in selected['arrays'].items():
        def read(raw, name=name, description=description):
            arrays[name] = _array(raw, description=description, maximum_bytes=criteria.maximum_workspace_bytes//8)
        validators[prefix+name+'.npy'] = (criteria.maximum_workspace_bytes//8+10000, read)
    authenticate_probe_files(native_subwork, original_result.definition, returned, member_validators=validators)
    assessment = assess_electronic_arrays(state=state, metadata=selected, arrays=arrays, criteria=criteria)
    native = base.pop('native_metadata', None)
    complete = (returned.error is None and native is not None
        and assessment['selected_matrix_criteria'] == 'SATISFIED')
    base.update(assessment=assessment, metadata=selected, complete=complete,
        energy_hartree=native['energy_hartree'] if native is not None else None)
    # Closing read rechecks every original result and array after reductions.
    if read_periodic_probe(config=config, representation=representation,
            original_result=original_result, native_subwork=native_subwork, assessor_source=assessor_source,
            readout_id=readout.readout_id) != readout:
        raise ValueError('constrained electronic original changes during independent assessment')
    return base, arrays
