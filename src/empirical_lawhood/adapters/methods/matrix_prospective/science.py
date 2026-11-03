# SPDX-License-Identifier: MPL-2.0
"""Native exposed trajectories, causal baseline and independent numerical assay.

No producer rerun is called an assessment. The assessor differentiates the
potential in a Hermitian basis and implements its own BAOAB composition. Its
tolerance is a numerical check, not fitted uncertainty or lifetime coverage.
"""

from decimal import Decimal
from hashlib import sha256

from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MatrixPurposeSeed, SavedMatrixArrays
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition

from .records import (
    BRANCHES, MatrixBranchAssessment, MatrixCausalForecast, MatrixCausalOrigin,
    MatrixIndependentAssessment, MatrixNativeBranch, MatrixNativeFutures, identity,
)


def array_product(arrays, *, allocation, producers, artifact_id, operand_id):
    from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
    raw, members = encode_matrix_arrays(arrays)
    artifact = ArtifactIdentity(artifact_id, "matrix-arrays", MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), "application/x-npz", len(raw))
    saved = SavedMatrixArrays(operand_id, allocation, artifact, members,
        tuple(sorted(set(producers), key=lambda v: v.object_id)))
    return raw, saved


def initial_state(protocol):
    from empirical_lawhood.adapters.simulators.six_matrix_response.model import ideal_state
    return ideal_state(q=2, alpha_tilde_x=float(protocol.alpha_x),
        alpha_tilde_y=float(protocol.alpha_y), constitution="11")


def prefix(source):
    import numpy as np
    from empirical_lawhood.adapters.simulators.six_matrix_response.simulation import baoab_step_with_hermitian_noise, hermitian_noise
    p = source.protocol
    seed = source.allocation.streams.roots[0].seed_for("prefix")
    rng = np.random.Generator(np.random.PCG64(seed))
    state = initial_state(p)
    positions, momenta = [state.positions.copy()], [state.momenta.copy()]
    for _ in range(p.prefix_steps):
        noise = hermitian_noise(rng=rng, q=2)
        state = baoab_step_with_hermitian_noise(state, member=p.member, numerical_view=p.view,
            next_alpha_tilde_x=float(p.alpha_x), next_alpha_tilde_y=float(p.alpha_y),
            standardized_noise=noise)
        positions.append(state.positions.copy())
        momenta.append(state.momenta.copy())
    return {"momenta": np.asarray(momenta, dtype="<c16"),
            "positions": np.asarray(positions, dtype="<c16")}


def forecast(origin, prefix_arrays, *, artifact_id):
    # No source allocation or future seed/realised path is an argument.
    p = origin.protocol
    horizon = float(p.view.timestep * p.horizon_steps)
    expected = prefix_arrays["positions"][-1] + horizon * prefix_arrays["momenta"][-1]
    arrays = {branch: expected.copy() for branch in BRANCHES}
    raw, saved = array_product(arrays, allocation=p.allocation,
        producers=(identity(origin), identity(p.calibration_scope), identity(p.preparation_scope)),
        artifact_id=artifact_id, operand_id="arrays.forecast." + p.protocol_id)
    record = MatrixCausalForecast("forecast." + p.protocol_id, identity(origin), identity(p),
        p.cutoff, identity(p.calibration_scope), identity(p.preparation_scope), saved)
    record.validate_origin(origin)
    return raw, record


def branch_contract(source, purpose):
    if purpose not in BRANCHES:
        raise ValueError("unselected native matrix branch")
    root = source.allocation.streams.roots[0]
    stream = next(s for s in root.scientific_seeds if s.purpose_id == purpose)
    p = source.protocol
    return MatrixNativeBranch(purpose, stream,
        p.alpha_x + (Decimal("0.05") if purpose == "future-2" else Decimal(0)), p.alpha_y)


def native_branch(source, origin, prefix_arrays, branch):
    import numpy as np
    from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState
    from empirical_lawhood.adapters.simulators.six_matrix_response.simulation import baoab_step_with_hermitian_noise, hermitian_noise
    p = source.protocol
    if (origin.source != identity(source) or origin.protocol != p
            or branch != branch_contract(source, branch.branch_id)):
        raise ValueError("matrix native branch changes source/root/stream/model/action")
    rng = np.random.Generator(np.random.PCG64(branch.stream.seed))
    state = SixMatrixState(2, prefix_arrays["positions"][-1].copy(),
        prefix_arrays["momenta"][-1].copy(), p.prefix_steps, float(p.alpha_x), float(p.alpha_y))
    positions, momenta, noises = [state.positions.copy()], [state.momenta.copy()], []
    for _ in range(p.horizon_steps):
        noise = hermitian_noise(rng=rng, q=2)
        state = baoab_step_with_hermitian_noise(state, member=p.member, numerical_view=p.view,
            next_alpha_tilde_x=float(branch.alpha_x), next_alpha_tilde_y=float(branch.alpha_y),
            standardized_noise=noise)
        positions.append(state.positions.copy())
        momenta.append(state.momenta.copy())
        noises.append(noise)
    return {"momenta": np.asarray(momenta, dtype="<c16"),
            "noise": np.asarray(noises, dtype="<c16"),
            "positions": np.asarray(positions, dtype="<c16")}


def futures(source, origin, commitment, branch_arrays, *, artifact_id):
    commitment.validate_origin(origin)
    if tuple(sorted(branch_arrays)) != BRANCHES:
        raise ValueError("matrix future publication omits selected branches")
    arrays = {f"{branch}.{name}": value for branch in BRANCHES
              for name, value in branch_arrays[branch].items()}
    raw, saved = array_product(arrays, allocation=source.protocol.allocation,
        producers=(identity(origin), identity(commitment), identity(source)),
        artifact_id=artifact_id, operand_id="arrays.future." + source.protocol.protocol_id)
    return raw, MatrixNativeFutures("futures." + source.protocol.protocol_id, identity(origin),
        identity(commitment), identity(source.protocol),
        tuple(branch_contract(source, branch) for branch in BRANCHES), saved)


def _potential_gradient(positions, parameters):
    """Differentiate the potential independently in the full 96-real-axis basis."""
    import numpy as np
    from empirical_lawhood.adapters.simulators.six_matrix_response.gradients import reference_action_terms
    epsilon = 2e-6
    result = np.zeros_like(positions)
    n = positions.shape[-1]
    for sector in range(2):
        for matrix in range(3):
            for row in range(n):
                for col in range(row, n):
                    for imaginary in ((False,) if row == col else (False, True)):
                        direction = np.zeros_like(positions)
                        if row == col:
                            direction[sector, matrix, row, col] = 1
                        else:
                            value = (1j if imaginary else 1) / np.sqrt(2)
                            direction[sector, matrix, row, col] = value
                            direction[sector, matrix, col, row] = value.conjugate()
                        plus = reference_action_terms(positions + epsilon * direction, parameters).total
                        minus = reference_action_terms(positions - epsilon * direction, parameters).total
                        result += ((plus - minus) / (2 * epsilon)) * direction
    return result


def _independent_branch(protocol, initial_arrays, branch, noise):
    import numpy as np
    from empirical_lawhood.adapters.simulators.six_matrix_response.gradients import SixMatrixParameters
    from empirical_lawhood.adapters.simulators.six_matrix_response.model import hermitian_part
    x, momentum = initial_arrays["positions"][-1].copy(), initial_arrays["momenta"][-1].copy()
    dt, friction, temperature = map(float, (protocol.view.timestep, protocol.view.friction_gamma,
                                         protocol.view.bath_temperature))
    alpha_x, alpha_y = map(float, (protocol.alpha_x, protocol.alpha_y))
    member = protocol.member
    xs, ps = [x.copy()], [momentum.copy()]
    for increment in noise:
        before = SixMatrixParameters(2, float(member.mass_x), float(member.mass_y),
            float(member.cross_coupling_gamma), alpha_x, alpha_y)
        momentum = hermitian_part(momentum - dt / 2 * _potential_gradient(x, before))
        x = hermitian_part(x + dt / 2 * momentum)
        decay = np.exp(-friction * dt)
        momentum = hermitian_part(decay * momentum + np.sqrt(temperature * (1 - decay**2)) * increment)
        x = hermitian_part(x + dt / 2 * momentum)
        after = SixMatrixParameters(2, float(member.mass_x), float(member.mass_y),
            float(member.cross_coupling_gamma), float(branch.alpha_x), float(branch.alpha_y))
        momentum = hermitian_part(momentum - dt / 2 * _potential_gradient(x, after))
        alpha_x, alpha_y = float(branch.alpha_x), float(branch.alpha_y)
        xs.append(x.copy())
        ps.append(momentum.copy())
    return {"positions": np.asarray(xs), "momenta": np.asarray(ps)}


def _independent_noise(stream, horizon):
    """Check the declared driver without calling the native noise producer."""
    import numpy as np
    rng = np.random.Generator(np.random.PCG64(stream.seed))
    values = np.zeros((horizon, 2, 3, 4, 4), dtype="<c16")
    for time_slice in values:
        for sector in time_slice:
            for matrix in sector:
                diagonal = rng.normal(size=4)
                real, imaginary = rng.normal(size=6), rng.normal(size=6)
                matrix[np.diag_indices(4)] = diagonal
                index = 0
                for row in range(4):
                    for column in range(row + 1, 4):
                        value = (real[index] + 1j * imaginary[index]) / np.sqrt(2)
                        matrix[row, column], matrix[column, row] = value, value.conjugate()
                        index += 1
    return values


def assess(source, origin, commitment, native, prefix_arrays, forecast_arrays, future_arrays):
    import numpy as np
    commitment.validate_origin(origin)
    p = source.protocol
    if (origin.source != identity(source) or origin.protocol != p
            or native.origin != identity(origin) or native.forecast != identity(commitment)
            or native.protocol != identity(p) or native.arrays.allocation != p.allocation
            or native.branches != tuple(branch_contract(source, b) for b in BRANCHES)):
        raise ValueError("independent matrix assessment changes exact source/commitment/branch joins")
    expected_names = {f"{b}.{name}" for b in BRANCHES for name in ("momenta", "noise", "positions")}
    if set(future_arrays) != expected_names or set(forecast_arrays) != set(BRANCHES):
        raise ValueError("independent matrix assessment lacks its complete array denominator")
    scores = []
    for branch in native.branches:
        b = branch.branch_id
        actual = {name: future_arrays[f"{b}.{name}"] for name in ("momenta", "noise", "positions")}
        if (actual["positions"].shape != (p.horizon_steps + 1, 2, 3, 4, 4)
                or actual["momenta"].shape != actual["positions"].shape
                or actual["noise"].shape != (p.horizon_steps, 2, 3, 4, 4)
                or not np.array_equal(actual["positions"][0], prefix_arrays["positions"][-1])
                or not np.array_equal(actual["momenta"][0], prefix_arrays["momenta"][-1])):
            raise ValueError("independent matrix assessment changes full horizon or initial handoff")
        expected_noise = _independent_noise(branch.stream, p.horizon_steps)
        reference = _independent_branch(p, prefix_arrays, branch, expected_noise)
        native_error = max(float(np.linalg.norm(actual[n] - reference[n])) for n in ("positions", "momenta"))
        prediction_error = float(np.linalg.norm(actual["positions"][-1] - forecast_arrays[b]))
        native_disposition = (AssessmentDisposition.SATISFIED if native_error <= float(p.native_reference_tolerance)
                              and np.array_equal(actual["noise"], expected_noise)
                              else AssessmentDisposition.FALSIFIED)
        forecast_disposition = (AssessmentDisposition.UNEVALUABLE if native_disposition is not AssessmentDisposition.SATISFIED
            else AssessmentDisposition.SATISFIED if prediction_error <= float(p.forecast_precision)
            else AssessmentDisposition.FALSIFIED)
        scores.append(MatrixBranchAssessment(b, Decimal(str(native_error)), Decimal(str(prediction_error)),
            native_disposition, forecast_disposition))
    return MatrixIndependentAssessment("assessment." + p.protocol_id, identity(origin),
        identity(commitment), identity(native), tuple(scores))


def origin_record(source, arrays, *, artifact_id):
    raw, saved = array_product(arrays, allocation=source.protocol.allocation,
        producers=(identity(source), identity(source.protocol)), artifact_id=artifact_id,
        operand_id="arrays.origin." + source.protocol.protocol_id)
    seed = source.allocation.streams.roots[0].seed_for("prefix")
    return raw, MatrixCausalOrigin("origin." + source.protocol.protocol_id, identity(source),
        source.protocol, MatrixPurposeSeed("prefix", seed), saved)
