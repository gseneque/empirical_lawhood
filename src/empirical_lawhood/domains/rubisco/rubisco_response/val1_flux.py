# SPDX-License-Identifier: MPL-2.0
"""Classical thermal crossing flux for a tagged gas at a substrate-centred sphere."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
import math
from typing import Literal, NotRequired, TypedDict
import numpy as np
from scipy.spatial import cKDTree
from scipy.special import logsumexp

from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_science import thermal_energy
from empirical_lawhood.domains.rubisco.rubisco_response.transition_state_rates import AVOGADRO_MOL


@dataclass(frozen=True)
class TaggedGasFluxMeasure:
    """The natural-unit surface and solvent bath selected together for the two insertion ensembles."""

    temperature_kelvin: Decimal
    radius_angstrom: Decimal
    bulk_clearance_angstrom: Decimal
    bath_radius_angstrom: Decimal

    def __post_init__(self):
        values = (self.temperature_kelvin, self.radius_angstrom, self.bulk_clearance_angstrom, self.bath_radius_angstrom)
        if (any(type(v) is not Decimal or not v.is_finite() or not 0 < float(v) < math.inf for v in values)
                or max(self.radius_angstrom, self.bulk_clearance_angstrom) >= self.bath_radius_angstrom):
            raise ValueError("select positive physical measures and a solvent bath containing the selected surface")


VAL1_MEASURE = TaggedGasFluxMeasure(Decimal("298.15"), Decimal("4"), Decimal("8"), Decimal("48"))


def sample_tagged_flux_host(*, initial_angstrom, masses_dalton, evaluate, dynamics, burn_in, draws,
                           relaxation_evaluations, random_seed, capture, measure: TaggedGasFluxMeasure = VAL1_MEASURE):
    """Prepare a fixed-cell host chain for the selected tagged-gas measure from complete reference forces."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import (
        PYSCF_BOHR_ANGSTROM, REFERENCE_HARTREE_KJ_MOL, reference_force_units,
    )
    from empirical_lawhood.methods.electronic_structure.fixed_cell_sampling import sample_fixed_cell_hamiltonian

    if type(dynamics) is not ReferenceDynamicsSettings or type(measure) is not TaggedGasFluxMeasure:
        raise TypeError("select the reference integration settings and tagged-gas measure")
    if type(random_seed) is not int or random_seed < 0 or not callable(evaluate):
        raise ValueError("select an explicit nonnegative PCG64 seed and a reference force callback")

    def energy_gradient(coordinates):
        returned = evaluate(coordinates)
        reference_force_units(returned)
        return returned["energy_hartree"], returned["gradient_hartree_per_bohr"]

    result = sample_fixed_cell_hamiltonian(
        initial_angstrom=initial_angstrom, masses_dalton=masses_dalton, energy_gradient=energy_gradient,
        bohr_angstrom=PYSCF_BOHR_ANGSTROM, hartree_kj_mol=REFERENCE_HARTREE_KJ_MOL,
        thermal_energy_kj_mol=thermal_energy(measure.temperature_kelvin), step_ps=dynamics.step_picoseconds,
        steps_per_proposal=dynamics.steps, burn_in=burn_in, draws=draws, relaxation_evaluations=relaxation_evaluations,
        rng=np.random.Generator(np.random.PCG64(random_seed)), capture=capture,
    )
    return dict(result, dynamics=dynamics.identity.to_document(), temperature_kelvin=str(measure.temperature_kelvin),
                random_generator="PCG64", random_seed=random_seed)


class TaggedPathReturn(TypedDict):
    outcome: str


class TaggedGasFluxTrial(TypedDict):
    """One assigned draw, including unavailable insertion or unresolved transmission."""

    log_bulk: float | Decimal | None
    log_surface: float | Decimal | None
    bulk_volume_fraction: float | Decimal | None
    maxwell_mean_positive_nm_ps: float | Decimal | None
    transmission: NotRequired[Literal["PRODUCT", "ZERO", "UNRESOLVED"]]
    back: NotRequired[TaggedPathReturn | None]
    forward: NotRequired[TaggedPathReturn | None]


def paired_path_transmission(back: TaggedPathReturn | None, forward: TaggedPathReturn | None):
    """Classify a completed pair of tagged trajectories under the original reservoir convention."""
    unresolved = {"UNRESOLVED", "HORIZON", "WATER_PARTITION_UNRESOLVED", "DISSOCIATED_ELECTRONIC_STATE_UNRESOLVED"}
    for returned, terminal in ((back, {"RECROSS", "BULK"}), (forward, {"PRODUCT", "BULK"})):
        if returned is not None and (not isinstance(returned, Mapping) or type(returned.get("outcome")) is not str
                                     or returned["outcome"] not in terminal | unresolved):
            raise ValueError("select a recorded tagged path disposition on its original side")
    if back is None or forward is None:
        return "UNRESOLVED"
    if back["outcome"] == "RECROSS" or forward["outcome"] == "BULK":
        return "ZERO"
    if back["outcome"] == "BULK" and forward["outcome"] == "PRODUCT":
        return "PRODUCT"
    return "UNRESOLVED"


def unit_vectors(rng, n):
    u = rng.normal(size=(n, 3))
    lengths = np.linalg.norm(u, axis=1)
    if not np.all(np.isfinite(lengths) & (lengths > 0)):
        raise ValueError("thermal proposal has an undefined orientation")
    return u / lengths[:, None]


def poses(x, box, solute, heavy, c2, gas, rng, *, bulk, trials=512, measure: TaggedGasFluxMeasure = VAL1_MEASURE):
    """Configurational-bias insertion. Keep positive proposal support and correct its selection.

    Internal lengths have lognormal proposal densities. The CO2 bending angle
    has an exponential density in cosine. Common orientation constants cancel.
    The anchor is C in CO2 and one labelled O in O2 throughout.
    """
    if type(trials) is not int or trials < 2 or gas not in ("O2", "CO2") or type(bulk) is not bool:
        raise ValueError("Select a gas and at least two integration proposals")
    x, box = np.asarray(x), np.asarray(box)
    if (x.ndim != 2 or x.shape[1] != 3 or x.dtype.kind not in "iuf" or not np.isfinite(x).all()
            or box.shape != (3,) or box.dtype.kind not in "iuf" or not np.isfinite(box).all()
            or np.min(box) <= 2 * float(measure.bath_radius_angstrom)
            or not isinstance(c2, (int, np.integer)) or isinstance(c2, (bool, np.bool_)) or not 0 <= c2 < len(x)):
        raise ValueError("select finite physical coordinates and a periodic cell containing a single solvent bath")
    solute, heavy = np.asarray(solute), np.asarray(heavy)
    for indices in (solute, heavy):
        if (indices.ndim != 1 or not len(indices) or indices.dtype.kind not in "iu" or np.min(indices) < 0
                or np.max(indices) >= len(x) or len(np.unique(indices)) != len(indices)):
            raise ValueError("select complete physical-atom index populations for the solvent bath and gas clearance")
    site = x[c2]
    vectors = unit_vectors(rng, trials)
    if bulk:
        # Restricted homogeneous solvent shell keeps both QM fragments inside
        # the declared direct-field radius. Integrate per unit free solvent volume.
        centers = site + float(measure.bath_radius_angstrom) * rng.uniform(size=(trials, 1)) ** (1 / 3) * vectors
        dist = cKDTree(x[solute] % box, boxsize=box).query(centers % box)[0]
        centers = centers[dist > float(measure.bulk_clearance_angstrom)]
        if not len(centers):
            raise ValueError("No bulk solvent in the selected bath quadrature")
    else:
        centers = site + float(measure.radius_angstrom) * vectors
    n = len(centers)
    length0 = 1.172 if gas == "CO2" else 1.21
    sigma = 0.035
    axis = unit_vectors(rng, n)

    def bond():
        z = rng.normal(size=n)
        lengths = length0 * np.exp(sigma * z)
        # l^2 dl / q(l)dl, dropping constants common to bulk and surface.
        return lengths, 3 * np.log(lengths) + 0.5 * z * z

    l1, log_j = bond()
    atomic = [centers, centers + l1[:, None] * axis]
    if gas == "CO2":
        l2, j2 = bond()
        tangent = unit_vectors(rng, n)
        tangent -= (axis * tangent).sum(axis=1)[:, None] * axis
        lengths = np.linalg.norm(tangent, axis=1)
        if not np.all(np.isfinite(lengths) & (lengths > 0)):
            raise ValueError("the carbon dioxide proposal has an undefined bending plane")
        tangent /= lengths[:, None]
        kappa = 100.0
        cosine = -1.0 - np.log1p(-rng.uniform(size=n) * (-np.expm1(-2 * kappa))) / kappa
        bend = cosine[:, None] * axis + np.sqrt(1 - cosine * cosine)[:, None] * tangent
        atomic.append(centers + l2[:, None] * bend)
        log_j += j2 + kappa * (cosine + 1)
    atomic = np.stack(atomic, axis=1)
    clearance = cKDTree(x[heavy] % box, boxsize=box).query(atomic.reshape(-1, 3) % box)[
        0
    ]
    clearance = clearance.reshape(n, -1).min(axis=1)
    # Pure proposal efficiency. A uniform component keeps every point selectable.
    log_bias = -np.minimum(60.0, 8.0 * np.maximum(0.0, 2.85 - clearance) ** 2)
    probs = 0.99 * np.exp(log_bias - logsumexp(log_bias)) + 0.01 / n
    j = int(rng.choice(n, p=probs))
    return atomic[j], dict(
        trials=trials,
        eligible=n,
        selected=j,
        clearance_A=float(clearance[j]),
        selection_probability=float(probs[j]),
        log_measure=float(log_j[j] - np.log(n * probs[j])),
        tag_distance_A=float(np.linalg.norm(centers[j] - site)),
    )


def incoming_velocity(masses, c2, tag, normal, rng, *, measure: TaggedGasFluxMeasure = VAL1_MEASURE):
    """Maxwell distribution biased by inward normal speed, conserving pair COM."""
    m = np.asarray(masses)
    normal = np.asarray(normal)
    if (m.ndim != 1 or m.dtype.kind not in "iuf" or not np.all(np.isfinite(m) & (m > 0))
            or normal.shape != (3,) or normal.dtype.kind not in "iuf" or not np.isfinite(normal).all()
            or abs(np.linalg.norm(normal) - 1) > 1e-10 or c2 == tag
            or any(not isinstance(i, (int, np.integer)) or isinstance(i, (bool, np.bool_)) or not 0 <= i < len(m) for i in (c2, tag))):
        raise ValueError("Invalid normal or physical mass")
    kt = thermal_energy(measure.temperature_kelvin)
    v = rng.normal(size=(len(m), 3)) * np.sqrt(kt / m)[:, None]
    reduced = 1 / (1 / m[c2] + 1 / m[tag])
    speed = math.sqrt(-2 * kt / reduced * math.log1p(-rng.uniform()))
    delta = (-speed - np.dot(v[tag] - v[c2], normal)) * normal
    v[tag] += reduced / m[tag] * delta
    v[c2] -= reduced / m[c2] * delta
    return v, speed, math.sqrt(kt / (2 * math.pi * reduced))


def log_insertion(log_proposal_measure, energy, host_energy, hartree_kj_mol, *, measure: TaggedGasFluxMeasure = VAL1_MEASURE):
    values = (log_proposal_measure, energy, host_energy, hartree_kj_mol)
    if any(isinstance(v, (bool, np.bool_)) or not math.isfinite(v) for v in values) or hartree_kj_mol <= 0:
        raise ValueError("select finite insertion energies and a positive Hartree conversion")
    value = log_proposal_measure - (energy - host_energy) * hartree_kj_mol / thermal_energy(measure.temperature_kelvin)
    if not math.isfinite(value):
        raise ValueError("Nonfinite insertion weight")
    return value


def rate_interval(rows: Iterable[TaggedGasFluxTrial], *, measure: TaggedGasFluxMeasure = VAL1_MEASURE):
    """Finite-panel identified interval; no pseudocount or sampling CI."""
    resolved = []
    for row in rows:
        if "back" in row or "forward" in row:
            disposition = paired_path_transmission(row.get("back"), row.get("forward"))
            if "transmission" in row and row["transmission"] != disposition:
                raise ValueError("tagged transmission differs from the original pair of path returns")
            row = {**row, "transmission": disposition}
        resolved.append(row)
    rows = tuple(resolved)
    fields = ("log_bulk", "log_surface", "bulk_volume_fraction", "maxwell_mean_positive_nm_ps")
    if any(r.get(key) is not None and (isinstance(r[key], (bool, np.bool_)) or not math.isfinite(r[key]))
           for r in rows for key in fields):
        raise ValueError("nonfinite or nonphysical tagged-gas flux observation")
    if any((r.get("maxwell_mean_positive_nm_ps") is not None and r["maxwell_mean_positive_nm_ps"] <= 0)
           or (r.get("bulk_volume_fraction") is not None and not 0 < r["bulk_volume_fraction"] <= 1) for r in rows):
        raise ValueError("a flux trial requires positive thermal speed and free-volume fraction")
    census = {state: sum(r.get("transmission") == state for r in rows) for state in ("PRODUCT", "ZERO", "UNRESOLVED")}
    census["unmeasured"] = sum(r.get("transmission") is None for r in rows)
    if sum(census.values()) != len(rows):
        raise ValueError("unknown tagged-gas transmission disposition")
    if not rows or any(r.get(k) is None for r in rows for k in fields):
        return dict(
            log_lower=None,
            log_upper=None,
            upper_unbounded=True,
            reason="missing insertion weight, bath measure or thermal flux",
            assigned_draws=len(rows),
            transmission_census=census,
        )
    b = np.array([r["log_bulk"] for r in rows], dtype=float)
    s = np.array([r["log_surface"] for r in rows], dtype=float)
    volumes = np.array([r["bulk_volume_fraction"] for r in rows], dtype=float)
    if census["unmeasured"]:
        raise ValueError("a weighted draw needs an explicit transmission disposition")
    observed = np.array([r["transmission"] == "PRODUCT" for r in rows])
    pending = np.array([r["transmission"] == "UNRESOLVED" for r in rows])
    # nm/ps = .01 Å/fs. Convert Å^3/fs to L/(mol s).
    log_area_conversion = (math.log(4 * math.pi) + 2 * math.log(float(measure.radius_angstrom))
                           + math.log(0.01) + math.log(float(AVOGADRO_MOL * Decimal("1e-12"))))
    factor = log_area_conversion + np.log([float(r["maxwell_mean_positive_nm_ps"]) for r in rows])

    def endpoint(mask):
        return (
            float(
                logsumexp((s + factor)[mask])
                - np.log(len(rows))
                - logsumexp(b + np.log(volumes))
                + np.log(volumes.sum())
            )
            if mask.any()
            else None
        )

    def ess(w):
        return float(1 / np.square(np.exp(w - logsumexp(w))).sum())

    return dict(
        assigned_draws=len(rows),
        transmission_census=census,
        log_lower=endpoint(observed),
        log_upper=endpoint(observed | pending),
        upper_unbounded=False,
        zero_lower=not observed.any(),
        zero_upper=not (observed | pending).any(),
        surface_effective_draws=ess(s),
        bulk_effective_draws=ess(b),
        unresolved_surface_weight=float(np.exp(s - logsumexp(s))[pending].sum()),
        unit="L mol^-1 s^-1",
        scope="realized finite panel conditional on host, bath and Hamiltonian",
    )
