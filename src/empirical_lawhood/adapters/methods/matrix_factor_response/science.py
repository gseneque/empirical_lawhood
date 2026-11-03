"""Shared mechanical response kernels; acquisition and products have current owners."""

import numpy as np
from empirical_lawhood.adapters.simulators.six_matrix_response.factor_bridge import factor_frame_sha256
from empirical_lawhood.adapters.simulators.six_matrix_response.gradients import SixMatrixParameters, analytic_gradient_terms
from empirical_lawhood.adapters.simulators.six_matrix_response.shooting import hermitian_basis
from .records import PREDICTORS, identity


def frame_axes(frame):
    frame = np.asarray(frame)
    if (frame.shape != (3, 4, 4) or frame.dtype != np.dtype('complex128') or not np.isfinite(frame).all()
            or not np.allclose(frame, frame.swapaxes(-1, -2).conj(), atol=1e-12, rtol=0)
            or not np.allclose(np.einsum('iab,jab->ij', frame.conj(), frame), np.eye(3), atol=1e-12, rtol=0)
            or not np.allclose(np.trace(frame, axis1=-2, axis2=-1), 0, atol=1e-12, rtol=0)):
        raise ValueError('matrix response frame is nonfinite, unidentified, nonorthonormal or contains trace')
    return np.concatenate((np.eye(4, dtype='<c16')[None]/2, frame))



def native_position_coordinates(values):
    return np.einsum('kab,sjab->sjk', hermitian_basis(4).conj(), values).real.reshape(96)



def native_position_lift(values):
    return np.einsum('sjk,kab->sjab', np.asarray(values).reshape(2, 3, 16), hermitian_basis(4))



def _instrument(design, frame, templates):
    axes = frame_axes(frame)
    generic = np.asarray(templates['generic_basis'])
    frame_axes(generic)
    coefficients = np.asarray(templates['force_coefficients'])
    trace_coefficients = np.asarray(templates['trace_coefficients'])
    complement = generic - np.einsum('ic,cab->iab', np.einsum('cab,iab->ic', axes.conj(), generic).real, axes)
    gram = np.einsum('iab,jab->ij', complement.conj(), complement).real
    eigenvalues, eigenvectors = np.linalg.eigh(gram)
    if eigenvalues[0] <= 1e-12:
        raise ValueError('comparison force loses its three-dimensional complement span')
    inverse_sqrt = (eigenvectors / np.sqrt(eigenvalues)) @ eigenvectors.T
    complement = np.einsum('ij,jab->iab', inverse_sqrt, complement)
    bases = {'FACTOR': frame, 'COMPLEMENT': complement, 'GENERIC': generic}
    forces = []
    for action in design.actions:
        force = (trace_coefficients[..., None, None]*axes[0] if action.role == 'TRACE'
                 else np.einsum('sjc,cab->sjab', coefficients, bases[action.role]))
        length = np.linalg.norm(force)
        if not np.isfinite(length) or length == 0:
            raise ValueError('comparison force has no resolved physical norm')
        forces.append(force * float(action.force_norm)/length)
    receivers = np.einsum('rpsjc,cab->rpsjab', templates['receiver_coefficients'], axes)
    return np.asarray(forces, dtype='<c16'), np.asarray(receivers, dtype='<c16')



def validate_origin_arrays(origin, arrays):
    d = origin.design
    expected = {'positions', 'momenta', 'frame', 'forces', 'receivers'}
    if set(arrays) - expected not in (set(), {'prefix_noise'}) or not expected <= set(arrays):
        raise ValueError('matrix origin changes complete causal state/frame/instrument census')
    if (arrays['positions'].shape != (d.origin_tick+1, 2, 3, 4, 4) or arrays['momenta'].shape != arrays['positions'].shape
            or arrays['forces'].shape != (4, 2, 3, 4, 4)
            or arrays['receivers'].shape != (d.receiver_count, 2, 2, 3, 4, 4)
            or factor_frame_sha256(arrays['frame']) != origin.frame_sha256):
        raise ValueError('matrix origin substitutes frame, receiver, action or full native state')
    frame_axes(arrays['frame'])
    for index, action in enumerate(d.actions):
        if not np.isclose(np.linalg.norm(arrays['forces'][index]), float(action.force_norm), atol=1e-12, rtol=1e-12):
            raise ValueError('matrix origin changes requested/applied native force norm')



def origin_hessian(origin, past):
    """Additive model-consistent derivative; the historical fixed Hessian is untouched."""
    d = origin.design
    position = past['positions'][-1]
    parameters = SixMatrixParameters(2, float(d.member.mass_x), float(d.member.mass_y),
        float(d.member.cross_coupling_gamma), float(d.alpha_x), float(d.alpha_y))
    epsilon = float(d.hessian_difference_step)
    hessian = np.empty((96, 96))
    for column in range(96):
        direction = native_position_lift(np.eye(96)[column])
        image = (analytic_gradient_terms(position+epsilon*direction, parameters).total
                 - analytic_gradient_terms(position-epsilon*direction, parameters).total)/(2*epsilon)
        hessian[:, column] = native_position_coordinates(image)
    if not np.isfinite(hessian).all():
        raise ValueError('origin native Hessian is nonfinite')
    return (hessian+hessian.T)/2



def _block_modes(axes_by_matrix):
    columns = []
    for index, axes in enumerate(axes_by_matrix):
        for axis in axes:
            native = np.zeros((2, 3, 4, 4), dtype='<c16')
            native.reshape(6, 4, 4)[index] = axis
            columns.append(native_position_coordinates(native))
    return np.asarray(columns).T



def reduction_modes(origin, past, hessian):
    d = origin.design
    modes = {'FACTOR': _block_modes([frame_axes(past['frame'])]*6), 'FULL_COUPLED': np.eye(96)}
    unavailable = {}
    radial, spectra = [], []
    for matrix in past['positions'][-1].reshape(6, 4, 4):
        traceless = matrix - np.trace(matrix)*np.eye(4)/4
        length = np.linalg.norm(traceless)
        if length <= 1e-12:
            unavailable['NORM_RADIUS'] = 'ORIGIN_RADIAL_DIRECTION_UNRESOLVED'
        else:
            radial.append(np.stack((np.eye(4)/2, traceless/length)))
        values, vectors = np.linalg.eigh(matrix)
        if np.min(np.diff(values)) <= float(d.spectral_gap_minimum):
            unavailable['SPECTRA'] = 'ORIGIN_NATIVE_MATRIX_SPECTRUM_DEGENERATE'
        spectra.append(np.asarray([np.outer(v, v.conj()) for v in vectors.T]))
    if 'NORM_RADIUS' not in unavailable:
        modes['NORM_RADIUS'] = _block_modes(radial)
    if 'SPECTRA' not in unavailable:
        modes['SPECTRA'] = _block_modes(spectra)
    values, vectors = np.linalg.eigh(hessian)
    order = np.argsort(np.abs(values), kind='stable')
    if abs(values[order[24]])-abs(values[order[23]]) <= float(d.generic_gap_minimum):
        unavailable['GENERIC_SLOW'] = 'ORIGIN_NATIVE_SLOW_MODE_CUTOFF_DEGENERATE'
    else:
        modes['GENERIC_SLOW'] = vectors[:, order[:24]]
    return modes, unavailable



def _linear_response(d, modes, hessian, force, receivers, action):
    """Discrete origin-linearized BAOAB odd response, including both force kicks.

    Native position advances with installed momentum directly. The model's
    mass fields enter its potential coefficients, not an invented inverse-mass
    velocity. Conditional common innovation means cancel in this linear map.
    """
    dt, decay = float(d.view.timestep), np.exp(-float(d.view.friction_gamma*d.view.timestep))
    reduced_hessian = modes.T @ hessian @ modes
    return _linear_response_from_reduced(d, modes, reduced_hessian, force, receivers, action, dt, decay)



def _linear_responses(d, modes, hessian, forces, receivers, actions):
    """Reuse only one fixed reduced operator across this action iteration."""
    values, reduced_hessian = [], None
    for force, action in zip(forces, actions, strict=True):
        dt, decay = float(d.view.timestep), np.exp(-float(d.view.friction_gamma*d.view.timestep))
        if reduced_hessian is None:
            reduced_hessian = modes.T @ hessian @ modes
        values.append(_linear_response_from_reduced(d, modes, reduced_hessian, force, receivers, action, dt, decay))
    return values


def origin_io_system(design, hessian, forces, receivers, actions):
    """The native 192-state instrument in fixed nominal-actuator coordinates.

    This boundary serves the amended origin forecast and its independent
    reader. It does not replace any retained historical five-model forecast.
    """
    from decimal import Decimal
    from .origin_mechanics import scaled_origin_system

    dt = design.view.timestep
    if (dt not in (Decimal('0.001'), Decimal('0.0005')) or not design.horizon_steps
            or dt * design.horizon_steps[-1] != Decimal('0.128')
            or len(actions) != 4 or any(a.amplitude != Decimal('0.01')
                or dt * a.pulse_steps != Decimal('0.016') for a in actions)
            or len({a.force_norm for a in actions}) != 1
            or hessian.shape != (96, 96) or forces.shape != (4, 2, 3, 4, 4)
            or receivers.shape != (48, 2, 2, 3, 4, 4)
            or forces.dtype.str != '<c16' or receivers.dtype.str != '<c16'
            or not np.isfinite(forces).all() or not np.isfinite(receivers).all()
            or not np.allclose(forces, forces.conj().swapaxes(-1, -2), rtol=0, atol=1e-12)
            or not np.allclose(receivers, receivers.conj().swapaxes(-1, -2), rtol=0, atol=1e-12)
            or any(not np.isclose(np.linalg.norm(f), float(a.force_norm), rtol=0, atol=1e-12)
                for f, a in zip(forces, actions, strict=True))):
        raise ValueError('origin IO system changes the declared native assay, forces or physical clock')
    force_inputs = np.stack([native_position_coordinates(f) * float(a.amplitude)
        for f, a in zip(forces, actions, strict=True)], axis=1)
    receiver_map = np.einsum('kab,rpsjab->rpsjk', hermitian_basis(4).conj(), receivers).real.reshape(48, 192)
    if not np.allclose(receiver_map @ receiver_map.T, np.eye(48), rtol=0, atol=1e-12):
        raise ValueError('origin IO system loses its original HS24 receiver metric')
    impulse = actions[0].amplitude * actions[0].force_norm * dt * actions[0].pulse_steps
    position_scale = impulse * (Decimal('0.128') - dt * actions[0].pulse_steps / 2)
    return scaled_origin_system(hessian, force_inputs, receiver_map, timestep=float(dt),
        decay=np.exp(-float(design.view.friction_gamma * dt)),
        position_scale=float(position_scale), momentum_scale=float(impulse))



def _linear_response_from_reduced(d, modes, reduced_hessian, force, receivers, action, dt, decay):
    reduced_force = modes.T @ native_position_coordinates(force) * float(action.amplitude)
    x = np.zeros(modes.shape[1]); p = np.zeros_like(x)
    output = []
    for tick in range(1, d.horizon_steps[-1]+1):
        kick = dt/2*reduced_force if tick <= action.pulse_steps else np.zeros_like(p)
        p += kick
        p -= dt/2 * (reduced_hessian @ x)
        x += dt/2 * p
        p *= decay
        x += dt/2 * p
        p -= dt/2 * (reduced_hessian @ x)
        p += kick
        if tick in d.horizon_steps:
            native = np.stack((native_position_lift(modes@x), native_position_lift(modes@p)))
            output.append(np.einsum('rpsjab,psjab->r', receivers.conj(), native).real)
    return np.asarray(output, dtype='<f8')



def forecast_values(origin, past, model):
    """Schema-independent numerical predictions; canonical wrappers own identity."""
    validate_origin_arrays(origin, past)
    if identity(model) != origin.design.model:
        raise ValueError('matrix forecast changes its frozen complete mechanistic model')
    hessian = origin_hessian(origin, past)
    modes, unavailable = reduction_modes(origin, past, hessian)
    arrays, dispositions = {'origin_hessian': hessian}, []
    for name in PREDICTORS:
        if name in unavailable:
            arrays[name.lower()] = np.full((4, len(origin.design.horizon_steps), origin.design.receiver_count), np.nan)
            dispositions.append((name, 'UNRESOLVED', unavailable[name]))
        else:
            arrays[name.lower()] = np.asarray(_linear_responses(origin.design, modes[name], hessian, past['forces'],
                past['receivers'], origin.design.actions))
            dispositions.append((name, 'AVAILABLE', None))
    return arrays, tuple(dispositions), tuple(n.lower() for n in unavailable)
