# SPDX-License-Identifier: MPL-2.0
"""Finite response with retained nonlinear coordinates and a quadratic environment.

Equation numbers refer to the derivation in docs/development/retained-gaussian-response.md.
These are float64 numerical methods, not canonical evidence or scientific admission.
Potential, operator, domain and measure assumptions belong to the supplying adapter.
No function performs I/O, constructs a native provider or obtains a residual certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import logsumexp, roots_hermitenorm


FloatArray = NDArray[np.float64]
ScalarFunction = Callable[[FloatArray], float]
VectorAction = Callable[[FloatArray], ArrayLike]
ResidualApplication = Literal["none", "endpoint", "finite-grid", "both"]


def _scalar(value, name, *, positive=False, nonnegative=False):
    if isinstance(value, (bool, np.bool_)) or np.iscomplexobj(value):
        raise ValueError(f"{name} must be a finite real number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if (not math.isfinite(result) or (positive and result <= 0)
            or (nonnegative and result < 0)):
        raise ValueError(f"{name} is outside its finite real domain")
    return result


def _array(values, ndim, name):
    original = np.asarray(values)
    if original.dtype.kind not in "iuf" or original.ndim != ndim:
        raise ValueError(f"{name} needs a real {ndim}-dimensional numerical array")
    result = np.asarray(original, dtype=np.float64)
    if not result.size or not np.isfinite(result).all():
        raise ValueError(f"{name} needs nonempty finite real values")
    # Immutable backing bytes also prevent callers from re-enabling writes.
    return np.frombuffer(result.tobytes(), dtype=np.float64).reshape(result.shape)


def _symmetric(values, name):
    result = _array(values, 2, name)
    scale = float(np.max(abs(result)))
    if (result.shape[0] != result.shape[1]
            or not np.allclose(result, result.T, rtol=0, atol=64*np.finfo(float).eps*scale)):
        raise ValueError(f"{name} must be symmetric")
    return _array((result+result.T)/2, 2, name)


def _spd(values, name):
    result = _symmetric(values, name)
    try:
        np.linalg.cholesky(result)
    except np.linalg.LinAlgError as exc:
        raise ValueError(f"{name} must be positive definite") from exc
    return result


def _action(action, vector, name):
    result = _array(action(vector), 1, name)
    if result.shape != vector.shape:
        raise ValueError(f"{name} changes the physical coordinate dimension")
    return result


def _same_reference(left, right):
    return (left.beta == right.beta and np.array_equal(left.mean, right.mean)
            and np.array_equal(left.compliance, right.compliance))


@dataclass(frozen=True, eq=False)
class GaussianReference:
    """Normalized N(mean, compliance/beta), with a fixed Cartesian measure."""

    mean: FloatArray
    compliance: FloatArray
    beta: float

    def __post_init__(self):
        mean = _array(self.mean, 1, "reference mean")
        compliance = _spd(self.compliance, "retained compliance")
        if compliance.shape != (len(mean), len(mean)):
            raise ValueError("reference mean and compliance dimensions differ")
        object.__setattr__(self, "mean", mean)
        object.__setattr__(self, "compliance", compliance)
        object.__setattr__(self, "beta", _scalar(self.beta, "beta", positive=True))

    @property
    def covariance(self):
        return self.compliance/self.beta


@dataclass(frozen=True, eq=False)
class RetainedReduction:
    """Equations 4 and 10; inverse_actions must represent K^{-1}S."""

    origin: FloatArray
    coordinates: FloatArray
    inverse_actions: FloatArray
    reference: GaussianReference

    def __post_init__(self):
        origin = _array(self.origin, 1, "physical origin")
        coordinates = _array(self.coordinates, 2, "retained coordinate map")
        actions = _array(self.inverse_actions, 2, "inverse actions")
        if (coordinates.shape != actions.shape or coordinates.shape[0] != len(origin)
                or np.linalg.matrix_rank(coordinates) != coordinates.shape[1]):
            raise ValueError("retained coordinates need independent columns and matching inverse actions")
        expected = GaussianReference(coordinates.T@origin, coordinates.T@actions, self.reference.beta)
        if not _same_reference(expected, self.reference):
            raise ValueError("retained reference does not match its physical inverse actions")
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "coordinates", coordinates)
        object.__setattr__(self, "inverse_actions", actions)

    def lift(self, retained):
        """Minimum quadratic-energy configuration at S.T @ x = retained."""
        point = _array(retained, 1, "retained point")
        if point.shape != self.reference.mean.shape:
            raise ValueError("retained point has the wrong dimension")
        return self.origin+self.inverse_actions@np.linalg.solve(
            self.reference.compliance, point-self.reference.mean)

    def lifted_potential(self, native_energy: ScalarFunction) -> ScalarFunction:
        """Equation 11. Each call evaluates the supplied energy once at the lift."""
        def potential(point):
            physical = self.lift(point)
            delta = np.asarray(point)-self.reference.mean
            reference_energy = .5*delta@np.linalg.solve(self.reference.compliance, delta)
            return _scalar(native_energy(physical), "native energy")-reference_energy
        return potential

    def residual(self, physical, native_energy: ScalarFunction, stiffness_action: VectorAction):
        """Equation 12 at one point. A sampled residual is not a uniform bound."""
        point = _array(physical, 1, "physical point")
        if point.shape != self.origin.shape:
            raise ValueError("physical point has the wrong dimension")
        delta = point-self.origin
        quadratic = .5*delta@_action(stiffness_action, delta, "stiffness action")
        return (_scalar(native_energy(point), "native energy")-quadratic
                -self.lifted_potential(native_energy)(self.coordinates.T@point))


def reduce_from_actions(origin, coordinates, inverse_actions, *, beta):
    """Build the reduction from supplied inverse actions without a dense K.

    The supplier owns inverse-action accuracy and the positive-reference contract.
    Symmetry and positivity of the projected matrix alone do not verify that contract.
    """
    x0 = _array(origin, 1, "physical origin")
    s = _array(coordinates, 2, "retained coordinate map")
    actions = _array(inverse_actions, 2, "inverse actions")
    if s.shape != actions.shape or s.shape[0] != len(x0):
        raise ValueError("inverse actions and retained coordinate dimensions differ")
    return RetainedReduction(x0, s, actions, GaussianReference(s.T@x0, s.T@actions, beta))


def reduce_reference(origin, coordinates, inverse_action: VectorAction, *, beta):
    """Request one inverse action for each retained direction, equation 4."""
    s = _array(coordinates, 2, "retained coordinate map")
    x0 = _array(origin, 1, "physical origin")
    if s.shape[0] != len(x0) or np.linalg.matrix_rank(s) != s.shape[1]:
        raise ValueError("retained coordinates need independent physical directions")
    _scalar(beta, "beta", positive=True)
    actions = np.column_stack([_action(inverse_action, v, "inverse action") for v in s.T])
    return reduce_from_actions(x0, s, actions, beta=beta)


def reduce_dense_reference(stiffness, origin, coordinates, *, beta):
    """Small-system control; molecular suppliers should use inverse actions."""
    k = _spd(stiffness, "reference stiffness")
    x0 = _array(origin, 1, "physical origin")
    if k.shape != (len(x0), len(x0)):
        raise ValueError("reference stiffness and origin dimensions differ")
    return reduce_reference(x0, coordinates, lambda v: np.linalg.solve(k, v), beta=beta)


def enlarge_reduction(reduction, direction, inverse_action: VectorAction):
    """Equation 20: retain prior actions and request only the added direction."""
    u = _array(direction, 1, "new retained direction")
    if u.shape != reduction.origin.shape:
        raise ValueError("new retained direction has the wrong dimension")
    s = np.column_stack((reduction.coordinates, u))
    if np.linalg.matrix_rank(s) != s.shape[1]:
        raise ValueError("new retained direction must be independent")
    actions = np.column_stack((reduction.inverse_actions, _action(inverse_action, u, "inverse action")))
    return reduce_from_actions(reduction.origin, s, actions, beta=reduction.reference.beta)


def conditional_reference(reference, observed_indices, observed_values):
    """Equation 8; unobserved coordinates retain their original order."""
    indices = tuple(observed_indices)
    n = len(reference.mean)
    if (not indices or len(indices) >= n or len(set(indices)) != len(indices)
            or any(type(i) is not int or not 0 <= i < n for i in indices)):
        raise ValueError("conditioning needs a proper, unique subset of coordinate indices")
    values = _array(observed_values, 1, "conditioning values")
    if len(values) != len(indices):
        raise ValueError("conditioning values do not match the selected coordinates")
    remaining = tuple(i for i in range(n) if i not in indices)
    rr = reference.compliance[np.ix_(indices, indices)]
    mr = reference.compliance[np.ix_(remaining, indices)]
    mean = reference.mean[list(remaining)]+mr@np.linalg.solve(rr, values-reference.mean[list(indices)])
    covariance_parameter = reference.compliance[np.ix_(remaining, remaining)]-mr@np.linalg.solve(rr, mr.T)
    return GaussianReference(mean, covariance_parameter, reference.beta)


@dataclass(frozen=True, eq=False)
class QuadraticUpdate:
    """Equation 19 plus the full log normalization relative to the old reference."""

    original: GaussianReference
    updated: GaussianReference
    log_normalization: float


def quadratic_update(reference, quadratic, linear, *, constant=0.):
    """Absorb .5*z.T@D@z - f.T@z + constant, preserving its partition factor."""
    d = _symmetric(quadratic, "quadratic update")
    f = _array(linear, 1, "linear update")
    c = _scalar(constant, "constant energy")
    n = len(reference.mean)
    if d.shape != (n, n) or f.shape != (n,):
        raise ValueError("quadratic update changes the retained dimension")
    precision = np.linalg.solve(reference.compliance, np.eye(n))
    updated_precision = _spd(precision+d, "updated precision")
    h = precision@reference.mean+f
    mean = np.linalg.solve(updated_precision, h)
    updated = GaussianReference(mean, np.linalg.solve(updated_precision, np.eye(n)), reference.beta)
    log_factor = (.5*(np.linalg.slogdet(updated.compliance)[1]
                     -np.linalg.slogdet(reference.compliance)[1])
                  +reference.beta*(.5*(mean@h-reference.mean@precision@reference.mean)-c))
    return QuadraticUpdate(reference, updated, _scalar(log_factor, "log normalization"))


def linear_restraint_update(reference, direction, center, stiffness, *, offset=0.):
    """Absorb k*(a.T@z + offset - center)**2/2 for an affine receiver only."""
    a = _array(direction, 1, "receiver direction")
    if a.shape != reference.mean.shape:
        raise ValueError("receiver direction has the wrong dimension")
    k = _scalar(stiffness, "restraint stiffness", positive=True)
    shift = _scalar(center, "restraint center")-_scalar(offset, "receiver offset")
    return quadratic_update(reference, k*np.outer(a, a), k*shift*a, constant=.5*k*shift*shift)


@dataclass(frozen=True, eq=False)
class GaussianQuadrature:
    """Finite positive quadrature of a normalized Gaussian; no error certificate."""

    reference: GaussianReference
    points: FloatArray
    log_weights: FloatArray

    def __post_init__(self):
        points = _array(self.points, 2, "quadrature points")
        weights = _array(self.log_weights, 1, "quadrature log weights")
        if points.shape != (len(weights), len(self.reference.mean)):
            raise ValueError("quadrature points and weights have incompatible dimensions")
        if abs(float(logsumexp(weights))) > 1e-12:
            raise ValueError("Gaussian quadrature weights must sum to one")
        object.__setattr__(self, "points", points)
        object.__setattr__(self, "log_weights", weights)


def gaussian_quadrature(reference, *, order, maximum_points):
    """Tensor Gauss-Hermite rule with an explicit pre-allocation point limit.

    Select and compare orders explicitly. Agreement of orders is not a rigorous
    error enclosure. Tensor cost grows exponentially with the retained dimension.
    """
    n = len(reference.mean)
    orders = (order,)*n if type(order) is int else tuple(order)
    if (len(orders) != n or any(type(v) is not int or v < 2 for v in orders)
            or type(maximum_points) is not int or maximum_points < 1):
        raise ValueError("quadrature needs integer orders >= 2 and a positive point limit")
    if math.prod(orders) > maximum_points:
        raise ValueError("quadrature exceeds the selected maximum_points before allocation")
    axes, logarithms = [], []
    for count in orders:
        nodes, weights = roots_hermitenorm(count)
        positive = weights > 0
        axes.append(nodes[positive])
        logarithms.append(np.log(weights[positive])-.5*math.log(2*math.pi))
    standard = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, n)
    log_weights = np.sum(np.stack(np.meshgrid(*logarithms, indexing="ij")), axis=0).ravel()
    points = reference.mean+standard@np.linalg.cholesky(reference.covariance).T
    return GaussianQuadrature(reference, points, log_weights)


@dataclass(frozen=True, eq=False)
class RetainedSamples:
    """Reusable native-energy and receiver values on one declared Gaussian rule."""

    quadrature: GaussianQuadrature
    energies: FloatArray
    receiver: FloatArray

    def __post_init__(self):
        energies = _array(self.energies, 1, "retained energies")
        receiver = _array(self.receiver, 1, "receiver values")
        if energies.shape != receiver.shape or len(energies) != len(self.quadrature.points):
            raise ValueError("every quadrature point needs its energy and receiver value")
        object.__setattr__(self, "energies", energies)
        object.__setattr__(self, "receiver", receiver)


def sample_potential(quadrature, potential: ScalarFunction, receiver: ScalarFunction):
    """Evaluate each supplied function once per point. Failures cannot drop nodes."""
    energies, values = [], []
    for point in quadrature.points:
        energies.append(_scalar(potential(point), "retained energy"))
        values.append(_scalar(receiver(point), "receiver value"))
    return RetainedSamples(quadrature, energies, values)


def compose_potentials(*potentials: ScalarFunction) -> ScalarFunction:
    """Equation 16: add finite energies, without assuming additive free energies."""
    if not potentials or any(not callable(value) for value in potentials):
        raise ValueError("composition needs one or more potential functions")
    return lambda point: math.fsum(_scalar(value(point), "potential term") for value in potentials)


@dataclass(frozen=True, eq=False)
class ParameterResponse:
    free_energy_gradient: FloatArray
    free_energy_hessian: FloatArray
    receiver_gradient: FloatArray


@dataclass(frozen=True, eq=False)
class BoltzmannIntegral:
    """Normalized moments and log J. All values are quadrature estimates."""

    reference: GaussianReference
    log_partition: float
    probabilities: FloatArray
    receiver: FloatArray
    log_partition_remainder: float
    energy_offset: float

    @property
    def free_energy(self):
        return _scalar(self.energy_offset-self.log_partition_remainder/self.reference.beta, "free energy")

    @property
    def mean(self):
        return _scalar(self.probabilities@self.receiver, "receiver mean")

    @property
    def variance(self):
        return _scalar(self.probabilities@(self.receiver-self.mean)**2, "receiver variance", nonnegative=True)

    @property
    def third_central_moment(self):
        return _scalar(self.probabilities@(self.receiver-self.mean)**3, "receiver third moment")

    def parameter_response(self, modification_values):
        """Equations 17-18 for W columns on this integral's original point order."""
        values = _array(modification_values, 2, "modification values")
        if len(values) != len(self.probabilities):
            raise ValueError("modifications must preserve every original quadrature point")
        means = self.probabilities@values
        centered = values-means
        covariance = (centered.T*self.probabilities)@centered
        cross = (self.probabilities*(self.receiver-self.mean))@centered
        return ParameterResponse(_array(means, 1, "gradient"),
                                 _array(-self.reference.beta*covariance, 2, "Hessian"),
                                 _array(-self.reference.beta*cross, 1, "receiver derivative"))


def evaluate_boltzmann(samples, *, extra_energy=None, normalization: QuadraticUpdate | None = None):
    """Equations 5 and 9. A quadratic update includes its complete log factor.

    Pass extra_energy to compose finite modifications on the existing energy grid.
    Keeping the restraint here implements equations 34-35 with a fixed reference.
    """
    # Remove the common native-energy zero before adding a center-dependent
    # restraint. Otherwise a large harmless constant can erase that restraint.
    energy_offset = float(np.min(samples.energies))
    energy = samples.energies-energy_offset
    if extra_energy is not None:
        extra = _array(extra_energy, 1, "extra energy")
        if extra.shape != energy.shape:
            raise ValueError("extra energy must preserve every original quadrature point")
        energy = energy+extra
    reference = samples.quadrature.reference
    log_factor = 0.
    if normalization is not None:
        if not _same_reference(reference, normalization.updated):
            raise ValueError("quadratic normalization belongs to a different Gaussian reference")
        reference = normalization.original
        log_factor = normalization.log_normalization
    with np.errstate(over="raise", invalid="raise"):
        try:
            logs = samples.quadrature.log_weights-reference.beta*energy
            log_sum = float(logsumexp(logs))
            remainder = _scalar(log_sum+log_factor, "log partition remainder")
            log_partition = _scalar(remainder-reference.beta*energy_offset, "log partition")
            probabilities = _array(np.exp(logs-log_sum), 1, "Boltzmann probabilities")
        except FloatingPointError as exc:
            raise ValueError("Boltzmann weights exceed finite numerical capacity") from exc
    return BoltzmannIntegral(reference, log_partition, probabilities, samples.receiver, remainder, energy_offset)


def _centers(values, minimum=1):
    centers = _array(values, 1, "restraint centers")
    if len(centers) < minimum or np.any(np.diff(centers) <= 0):
        raise ValueError("restraint centers must be complete and strictly increasing")
    return centers


@dataclass(frozen=True, eq=False)
class RestrainedSeries:
    centers: FloatArray
    stiffness: float
    integrals: tuple[BoltzmannIntegral, ...]

    def __post_init__(self):
        centers = _centers(self.centers)
        stiffness = _scalar(self.stiffness, "restraint stiffness", positive=True)
        if (not self.integrals or len(centers) != len(self.integrals)
                or any(not _same_reference(v.reference, self.integrals[0].reference) for v in self.integrals)):
            raise ValueError("each center needs an integral relative to the same fixed arm reference")
        object.__setattr__(self, "centers", centers)
        object.__setattr__(self, "stiffness", stiffness)

    @property
    def beta(self):
        return self.integrals[0].reference.beta

    @property
    def means(self):
        return np.array([v.mean for v in self.integrals])

    @property
    def mean_forces(self):
        return self.stiffness*(self.centers-self.means)

    @property
    def endpoint_difference(self):
        first, last = self.integrals[0], self.integrals[-1]
        return _scalar((last.energy_offset-first.energy_offset)
                       -(last.log_partition_remainder-first.log_partition_remainder)/self.beta,
                       "endpoint free-energy difference")

    @property
    def mean_force_derivatives(self):
        """Equation 38: first and second derivatives at the selected centers."""
        variances = np.array([v.variance for v in self.integrals])
        thirds = np.array([v.third_central_moment for v in self.integrals])
        k = self.stiffness
        return k-self.beta*k*k*variances, -self.beta**2*k**3*thirds


def restrained_series(samples, centers, stiffness):
    """Default: keep the complete nonlinear restraint inside equations 34-35.

    Reuses the same energy and receiver evaluations at every restraint center.
    No Gaussian-update determinant or energy constant is discarded.
    """
    selected = _centers(centers)
    k = _scalar(stiffness, "restraint stiffness", positive=True)
    return RestrainedSeries(selected, k, tuple(evaluate_boltzmann(
        samples, extra_energy=.5*k*(samples.receiver-s)**2) for s in selected))


def absorbed_linear_restraint_series(reference, potential, direction, centers, stiffness,
                                     *, order, maximum_points, offset=0.):
    """Alternative normalization path, restricted to an affine receiver.

    Each center has a different Gaussian rule and therefore new energy evaluations.
    For nonlinear receivers use restrained_series, which retains the full restraint.
    """
    selected = _centers(centers)
    k = _scalar(stiffness, "restraint stiffness", positive=True)
    a = _array(direction, 1, "receiver direction")
    b = _scalar(offset, "receiver offset")
    integrals = []
    for center in selected:
        update = linear_restraint_update(reference, a, center, k, offset=b)
        rule = gaussian_quadrature(update.updated, order=order, maximum_points=maximum_points)
        samples = sample_potential(rule, potential, lambda point: float(a@point+b))
        integrals.append(evaluate_boltzmann(samples, normalization=update))
    return RestrainedSeries(selected, k, tuple(integrals))


@dataclass(frozen=True)
class ResidualEnvelope:
    """Supplied uniform bounds on R over the full declared integration domain.

    Construction validates numbers, not the physical truth or coverage of the bounds.
    """

    lower: float
    upper: float

    def __post_init__(self):
        lower = _scalar(self.lower, "residual lower bound")
        upper = _scalar(self.upper, "residual upper bound")
        if upper < lower:
            raise ValueError("residual bounds are reversed")
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)

    @property
    def oscillation(self):
        return self.upper-self.lower


def endpoint_residual_error(wt: ResidualEnvelope, mutant: ResidualEnvelope):
    """Equation 24, for the paired endpoint contrast only; constants cancel."""
    return wt.oscillation+mutant.oscillation


def receiver_residual_error(variance, residual: ResidualEnvelope, *, beta):
    """Equation 25. Supply the reduced variance or a valid upper bound on it.

    A quadrature variance produces an estimated conditional error contribution.
    This function supplies no variance, tail, quadrature or physical certificate.
    """
    var = _scalar(variance, "receiver variance", nonnegative=True)
    inverse_temperature = _scalar(beta, "beta", positive=True)
    if var == 0 or residual.oscillation == 0:
        return 0.
    try:
        return math.sqrt(var)*math.sinh(inverse_temperature*residual.oscillation/2)
    except OverflowError:
        return math.inf


def trapezoid_weights(centers):
    selected = _centers(centers, minimum=2)
    weights = np.zeros(len(selected))
    widths = np.diff(selected)/2
    weights[:-1] += widths
    weights[1:] += widths
    return weights


@dataclass(frozen=True, eq=False)
class PairedResponse:
    """Distinct equation-36 and equation-37 outputs, in the input energy units."""

    centers: FloatArray
    weights: FloatArray
    paired_mean_forces: FloatArray
    finite_grid: float
    endpoint: float
    endpoint_residual_error: float | None
    finite_grid_residual_error: float | None
    residual_variance_source: str | None


def paired_response(wt, mutant, *, weights=None, residual_application: ResidualApplication = "none",
                    residuals=None, receiver_variance_bounds=None):
    """Equations 36-37, with separately selected equation-24/25 applications.

    Arm dimensions and atom counts may differ. Centers, beta, stiffness, receiver
    meaning and units must agree; only the first three are numerically checked here.
    Error contributions exclude numerical integration, inverse actions and tails.
    """
    centers = _centers(wt.centers, minimum=2)
    if (not np.array_equal(centers, mutant.centers) or wt.beta != mutant.beta
            or wt.stiffness != mutant.stiffness):
        raise ValueError("paired arms must share centers, beta and stiffness")
    omega = _array(trapezoid_weights(centers) if weights is None else weights, 1, "quadrature weights")
    if omega.shape != centers.shape:
        raise ValueError("quadrature weights must retain every selected center")
    if residual_application not in ("none", "endpoint", "finite-grid", "both"):
        raise ValueError("unknown residual application")
    if residual_application == "none":
        if residuals is not None or receiver_variance_bounds is not None:
            raise ValueError("select the residual application explicitly")
    elif (not isinstance(residuals, tuple) or len(residuals) != 2
          or any(not isinstance(v, ResidualEnvelope) for v in residuals)):
        raise ValueError("residual applications need both WT and mutant envelopes")
    if receiver_variance_bounds is not None and residual_application not in ("finite-grid", "both"):
        raise ValueError("receiver variance bounds apply to the finite-grid error only")
    paired = mutant.mean_forces-wt.mean_forces
    endpoint = mutant.endpoint_difference-wt.endpoint_difference
    endpoint_error = grid_error = variance_source = None
    if residual_application in ("endpoint", "both"):
        endpoint_error = endpoint_residual_error(*residuals)
    if residual_application in ("finite-grid", "both"):
        if receiver_variance_bounds is None:
            variances = tuple(np.array([v.variance for v in arm.integrals]) for arm in (wt, mutant))
            variance_source = "QUADRATURE_ESTIMATES_NOT_CERTIFIED_VARIANCE_BOUNDS"
        else:
            if len(receiver_variance_bounds) != 2:
                raise ValueError("variance bounds need both complete arms")
            variances = tuple(_array(v, 1, "variance bounds") for v in receiver_variance_bounds)
            if any(v.shape != centers.shape or np.any(v < 0) for v in variances):
                raise ValueError("variance bounds must cover every selected center")
            variance_source = "SUPPLIED_VARIANCE_BOUNDS_REQUIRING_EXTERNAL_JUSTIFICATION"
        contributions = (abs(weight)*receiver_residual_error(var, residual, beta=wt.beta)
                         for values, residual in zip(variances, residuals, strict=True)
                         for weight, var in zip(omega, values, strict=True) if weight != 0)
        grid_error = wt.stiffness*math.fsum(contributions)
    return PairedResponse(centers, omega, _array(paired, 1, "paired mean forces"),
                          _scalar(omega@paired, "paired finite-grid response"),
                          _scalar(endpoint, "paired endpoint response"), endpoint_error, grid_error, variance_source)


def trapezoid_error_bound(centers, second_derivative_suprema):
    """Equation 39; supplied interval suprema cannot be replaced by sampled maxima."""
    selected = _centers(centers, minimum=2)
    suprema = _array(second_derivative_suprema, 1, "second-derivative suprema")
    if suprema.shape != (len(selected)-1,) or np.any(suprema < 0):
        raise ValueError("one nonnegative derivative supremum is required per center interval")
    return float(np.sum(np.diff(selected)**3*suprema/12))


@dataclass(frozen=True, eq=False)
class GalerkinCompliance:
    inverse_actions: FloatArray
    residual: FloatArray
    lower: FloatArray
    upper: FloatArray
    declared_lower_eigenvalue: float


def galerkin_compliance(coordinates, basis, stiffness_action: VectorAction, *, lower_eigenvalue_bound):
    """Equations 21-22, conditional on K >= m I and accurate linear actions.

    The supplied m is not inferred from Ritz values. Roundoff and inexact actions
    need separate enclosures before these floating-point matrices certify anything.
    A singular lower matrix is useful diagnostic output but cannot enter equation 23.
    """
    s = _array(coordinates, 2, "retained coordinate map")
    q = _array(basis, 2, "Galerkin basis")
    m = _scalar(lower_eigenvalue_bound, "lower eigenvalue bound", positive=True)
    if (s.shape[0] != q.shape[0] or np.linalg.matrix_rank(s) != s.shape[1]
            or not np.allclose(q.T@q, np.eye(q.shape[1]), rtol=0, atol=1e-12)):
        raise ValueError("Galerkin basis must be orthonormal in the physical coordinate space")
    kq = np.column_stack([_action(stiffness_action, v, "stiffness action") for v in q.T])
    projected = _spd(q.T@kq, "Galerkin stiffness")
    coefficients = np.linalg.solve(projected, q.T@s)
    actions = q@coefficients
    residual = s-kq@coefficients
    lower = _symmetric(s.T@actions, "Galerkin compliance")
    upper = lower+residual.T@residual/m
    return GalerkinCompliance(_array(actions, 2, "inverse actions"), _array(residual, 2, "residual"),
                             lower, _array(upper, 2, "upper compliance"), m)


def covariance_log_integral_bounds(lower, upper, *, log_lower_integral_bound, log_upper_integral_bound):
    """Equation 23 in log space, with the same mean, beta, potential and measure.

    Supply a lower bound on log I(G_minus) and an upper bound on log I(G_plus).
    Passing quadrature estimates yields estimates of the conditional enclosure.
    The numerical function cannot authenticate the common potential or input bounds.
    """
    if (lower.beta != upper.beta or not np.array_equal(lower.mean, upper.mean)):
        raise ValueError("covariance enclosure requires the same mean and beta")
    difference = upper.compliance-lower.compliance
    if np.linalg.eigvalsh(difference)[0] < 0:
        raise ValueError("covariance bounds are not ordered in the positive-semidefinite sense")
    lo = _scalar(log_lower_integral_bound, "lower log integral bound")
    hi = _scalar(log_upper_integral_bound, "upper log integral bound")
    shift = .5*(np.linalg.slogdet(upper.compliance)[1]-np.linalg.slogdet(lower.compliance)[1])
    result = (float(lo-shift), float(hi+shift))
    if result[0] > result[1]:
        raise ValueError("supplied integral bounds produce an empty enclosure")
    return result


def transverse_residual_envelope(force_mismatch_bound, curvature_mismatch_bound, radius):
    """Equation 26 inside a supplied tube; supplies no omitted-tail control."""
    force = _scalar(force_mismatch_bound, "transverse force bound", nonnegative=True)
    curvature = _scalar(curvature_mismatch_bound, "transverse curvature bound", nonnegative=True)
    width = _scalar(radius, "tube radius", nonnegative=True)
    bound = force*width+.5*curvature*width*width
    return ResidualEnvelope(-bound, bound)


@dataclass(frozen=True, eq=False)
class HarmonicBath:
    """Equations 27-32 in mass-weighted coordinates with an orthogonal split.

    This evaluates the memory, preparation and dynamic-stiffness operands, not a
    molecular trajectory or a Markov approximation. Nonlinear retained forces
    remain explicit in equation 28. Dense bath matrices are small-system controls.
    """

    retained_stiffness: FloatArray
    coupling: FloatArray
    bath_stiffness: FloatArray

    def __post_init__(self):
        zz = _symmetric(self.retained_stiffness, "retained stiffness")
        b = _array(self.coupling, 2, "bath coupling")
        qq = _spd(self.bath_stiffness, "bath stiffness")
        if b.shape != (len(zz), len(qq)):
            raise ValueError("bath coupling dimensions do not match the two coordinate blocks")
        object.__setattr__(self, "retained_stiffness", zz)
        object.__setattr__(self, "coupling", b)
        object.__setattr__(self, "bath_stiffness", qq)

    @property
    def effective_stiffness(self):
        return self.retained_stiffness-self.coupling@np.linalg.solve(self.bath_stiffness, self.coupling.T)

    def memory(self, time):
        t = _scalar(time, "memory time")
        values, vectors = np.linalg.eigh(self.bath_stiffness)
        ports = self.coupling@vectors
        return (ports*(np.cos(np.sqrt(values)*t)/values))@ports.T

    def initial_force(self, time, retained_position, bath_position, bath_velocity):
        t = _scalar(time, "preparation time")
        z = _array(retained_position, 1, "initial retained position")
        q = _array(bath_position, 1, "initial bath position")
        velocity = _array(bath_velocity, 1, "initial bath velocity")
        if z.shape != (len(self.retained_stiffness),) or q.shape != (len(self.bath_stiffness),) or velocity.shape != q.shape:
            raise ValueError("initial preparation does not match the bath coordinate blocks")
        values, vectors = np.linalg.eigh(self.bath_stiffness)
        omega = np.sqrt(values)
        displaced = q+np.linalg.solve(self.bath_stiffness, self.coupling.T@z)
        force = (np.cos(omega*t)*(vectors.T@displaced)
                 +np.sin(omega*t)/omega*(vectors.T@velocity))
        return -self.coupling@vectors@force

    def dynamic_stiffness(self, laplace_frequency):
        if isinstance(laplace_frequency, (bool, np.bool_)):
            raise ValueError("Laplace frequency must be finite")
        p = complex(laplace_frequency)
        if not math.isfinite(p.real) or not math.isfinite(p.imag):
            raise ValueError("Laplace frequency must be finite")
        return (p*p*np.eye(len(self.retained_stiffness))+self.retained_stiffness
                -self.coupling@np.linalg.solve(
                    p*p*np.eye(len(self.bath_stiffness))+self.bath_stiffness, self.coupling.T))

    def thermal_force_covariance(self, time, other_time, *, beta):
        """Conditional-equilibrium initial bath only; no claim for other preparations."""
        inverse_temperature = _scalar(beta, "beta", positive=True)
        return self.memory(_scalar(time, "time")-_scalar(other_time, "other time"))/inverse_temperature
