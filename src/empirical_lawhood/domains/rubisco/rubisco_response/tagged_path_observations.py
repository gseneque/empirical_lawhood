# SPDX-License-Identifier: MPL-2.0
"""Tagged-gas first passages on an original fixed-cell trajectory."""

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from hashlib import sha256
import math
from numbers import Real
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike

from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import minimum_image
from empirical_lawhood.domains.rubisco.rubisco_response.bound_products import bound_products
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
from empirical_lawhood.domains.rubisco.rubisco_response.val1_flux import TaggedGasFluxMeasure
from empirical_lawhood.science.records.serialization import validate_sha256


@dataclass(frozen=True, slots=True)
class TaggedPathSites:
    """Physical atom order, fixed cell and native site selections for one path."""

    elements: tuple[str, ...]
    box_angstrom: tuple[float, float, float]
    magnesium: int
    phosphorus: tuple[int, int]
    backbone: tuple[int, int]
    gas_atoms: tuple[int, ...]
    solute_heavy: tuple[int, ...]
    water_oxygens: tuple[int, ...]
    coordinating_water: int

    def __post_init__(self):
        if type(self.elements) is not tuple or not self.elements or any(type(e) is not str or not e for e in self.elements):
            raise ValueError("select the complete physical atom order")
        if (type(self.box_angstrom) is not tuple or len(self.box_angstrom) != 3
                or any(isinstance(v, bool) or not isinstance(v, Real) or not 0 < v < math.inf for v in self.box_angstrom)):
            raise ValueError("select three finite positive orthorhombic cell lengths in angstrom")
        roles = (self.phosphorus, self.backbone, self.gas_atoms, self.solute_heavy, self.water_oxygens,
                 (self.magnesium,), (self.coordinating_water,))
        for indices in roles:
            if (type(indices) is not tuple or not indices
                    or any(type(i) is not int or not 0 <= i < len(self.elements) for i in indices)
                    or len(set(indices)) != len(indices)):
                raise ValueError("select unique original atom indices for each tagged-path role")
        symbols = self.elements.__getitem__
        if (symbols(self.magnesium) != "Mg" or tuple(map(symbols, self.phosphorus)) != ("P", "P")
                or tuple(map(symbols, self.backbone)) != ("C", "C")
                or tuple(map(symbols, self.gas_atoms)) not in (("C", "O", "O"), ("O", "O"))
                or any(symbols(i) != "O" for i in self.water_oxygens)
                or self.coordinating_water not in self.water_oxygens
                or any(symbols(i) == "H" for i in self.solute_heavy)
                or not set((*self.phosphorus, *self.backbone)) <= set(self.solute_heavy)
                or not set(self.solute_heavy).isdisjoint((*self.gas_atoms, *self.water_oxygens))
                or not set(self.water_oxygens).isdisjoint(self.gas_atoms)):
            raise ValueError("the gas, ligand, magnesium, solute and original water assignments disagree")


@dataclass(frozen=True, slots=True)
class TaggedReservoirCharacter:
    """A charge and spin observation on the selected electronic surface and geometry."""

    source_sha256: str
    coordinate_sha256: str
    gas_atoms: tuple[int, ...]
    surface: Literal["S", "T"]
    charge_e: float
    spin_e: float

    def __post_init__(self):
        validate_sha256(self.source_sha256)
        validate_sha256(self.coordinate_sha256)
        if (self.surface not in ("S", "T") or type(self.gas_atoms) is not tuple or len(self.gas_atoms) not in (2, 3)
                or any(type(i) is not int or i < 0 for i in self.gas_atoms) or len(set(self.gas_atoms)) != len(self.gas_atoms)):
            raise ValueError("select the original gas atom order and reservoir surface")
        if any(isinstance(v, bool) or not isinstance(v, Real) or not math.isfinite(v) for v in (self.charge_e, self.spin_e)):
            raise ValueError("select the finite measured gas charge and spin in electron units")


@dataclass(frozen=True, slots=True)
class TaggedPathFrame:
    step: int
    positions_angstrom: ArrayLike
    active_surface: Literal["S", "T"]
    reservoir: TaggedReservoirCharacter | None = None


def observe_tagged_geometry(sites: TaggedPathSites, frame: TaggedPathFrame, measure: TaggedGasFluxMeasure):
    """Measure the covalent product, gas integrity, distances and nearest Mg water in one frame."""
    if type(sites) is not TaggedPathSites or type(frame) is not TaggedPathFrame or type(measure) is not TaggedGasFluxMeasure:
        raise TypeError("select exact tagged-path sites, an observed frame and its gas flux measure")
    xyz = np.asarray(frame.positions_angstrom)
    oxygen = len(sites.gas_atoms) == 2
    if (type(frame.step) is not int or frame.step < 0 or xyz.shape != (len(sites.elements), 3)
            or xyz.dtype.kind not in "iuf" or not np.isfinite(xyz).all()
            or frame.active_surface not in ("S", "T") or (not oxygen and frame.active_surface != "S")):
        raise ValueError("select one complete finite native geometry on the selected gas surface")
    xyz = np.array(xyz, dtype="<f8", order="C", copy=True)
    if not np.isfinite(xyz).all():
        raise ValueError("native positions exceed the supported float64 range")
    box = np.asarray(sites.box_angstrom)
    tag = list(sites.gas_atoms)
    local = minimum_image(xyz - xyz[sites.magnesium], box)
    nearest = np.flatnonzero(np.linalg.norm(local, axis=1) < 18.0)
    kept = np.unique(np.r_[nearest, tag, sites.phosphorus, sites.backbone])
    local_index = {int(atom): index for index, atom in enumerate(kept)}
    product = bound_products(tuple(sites.elements[i] for i in kept), local[kept],
        tuple(map(local_index.__getitem__, sites.phosphorus)), tuple(map(local_index.__getitem__, tag)),
        tuple(map(local_index.__getitem__, sites.backbone)), singlet=frame.active_surface == "S")
    anchor = xyz[tag[0]]
    bonds = np.linalg.norm(minimum_image(xyz[tag[1:]] - anchor, box), axis=1)
    intact = (frame.active_surface == "T" and 1.0 < bonds[0] < 1.42) if oxygen else np.all((0.9 < bonds) & (bonds < 1.45))
    solute_distance = float(np.min(np.linalg.norm(minimum_image(xyz[list(sites.solute_heavy)] - anchor, box), axis=1)))
    water_distances = np.linalg.norm(local[list(sites.water_oxygens)], axis=1)
    nearest_water = int(np.argmin(water_distances))
    return dict(coordinate_sha256=sha256(xyz.tobytes()).hexdigest(), step=frame.step, active_surface=frame.active_surface,
        gas_intact=bool(intact), product=product,
        bulk_geometry=bool(intact and solute_distance > float(measure.bulk_clearance_angstrom)),
        tag_c2_angstrom=float(np.linalg.norm(minimum_image(anchor - xyz[sites.backbone[0]], box))),
        solute_distance_angstrom=solute_distance, nearest_water_oxygen=sites.water_oxygens[nearest_water],
        nearest_water_distance_angstrom=float(water_distances[nearest_water]),
        replaced_water=bool(sites.water_oxygens[nearest_water] != sites.coordinating_water and water_distances[nearest_water] < 2.6))


def read_tagged_path_endpoint(*, sites: TaggedPathSites, frames: Iterable[TaggedPathFrame],
                             dynamics: ReferenceDynamicsSettings, side: Literal["back", "forward"],
                             measure: TaggedGasFluxMeasure, reservoir_source_sha256: str, residence_steps: int = 4):
    """Read consecutive original frames up to the first physical endpoint or the selected horizon."""
    if type(sites) is not TaggedPathSites or type(dynamics) is not ReferenceDynamicsSettings or type(measure) is not TaggedGasFluxMeasure:
        raise TypeError("select the original tagged path, physical clock and gas flux measure")
    if side not in ("back", "forward") or type(residence_steps) is not int or residence_steps < 0:
        raise ValueError("select a trajectory direction and a nonnegative product residence in physical steps")
    validate_sha256(reservoir_source_sha256)
    reservoir_surface = "T" if len(sites.gas_atoms) == 2 else "S"
    product_frames, count, observation = 0, 0, None
    outcome, reason = "UNRESOLVED", "incomplete physical trajectory"
    for frame in frames:
        if type(frame) is not TaggedPathFrame or type(frame.step) is not int or frame.step != count:
            raise ValueError("tagged trajectory frames must start at zero and follow the complete physical clock")
        observation = observe_tagged_geometry(sites, frame, measure)
        count += 1
        character = frame.reservoir
        neutral = False
        if character is not None:
            if (type(character) is not TaggedReservoirCharacter or character.source_sha256 != reservoir_source_sha256
                    or character.coordinate_sha256 != observation["coordinate_sha256"]
                    or character.gas_atoms != sites.gas_atoms or character.surface != reservoir_surface):
                raise ValueError("reservoir charge and spin must come from this geometry, gas and electronic source")
            neutral = abs(character.charge_e) <= 0.35 and abs(character.spin_e - (2 if reservoir_surface == "T" else 0)) <= 0.4
        observation["reservoir_charge_e"] = None if character is None else character.charge_e
        observation["reservoir_spin_e"] = None if character is None else character.spin_e
        product_frames = product_frames + 1 if observation["product"] is not None else 0
        if observation["replaced_water"]:
            outcome, reason = "WATER_PARTITION_UNRESOLVED", "another water oxygen entered the Mg coordination shell"
        elif observation["bulk_geometry"] and neutral:
            outcome, reason = "BULK", "intact gas returned to the selected electronic reservoir"
        elif side == "back" and frame.step and observation["tag_c2_angstrom"] < float(measure.radius_angstrom):
            outcome, reason = "RECROSS", "backward gas anchor crossed inside the dividing surface"
        elif side == "forward" and product_frames > residence_steps:
            outcome, reason = "PRODUCT", "bound product persisted for the selected physical residence"
        elif observation["bulk_geometry"]:
            outcome = "DISSOCIATED_ELECTRONIC_STATE_UNRESOLVED"
            reason = "missing reservoir charge and spin" if character is None else "reservoir charge or spin outside tolerance"
        elif frame.step == dynamics.steps:
            outcome, reason = "HORIZON", "physical horizon reached"
        else:
            continue
        break
    last = count - 1 if count else None
    return dict(outcome=outcome, reason=reason, side=side, frames_read=count, last_step=last,
                physical_time_seconds=None if last is None else str(dynamics.time_at_step(last)),
                dynamics=dynamics.identity.to_document(), reservoir_source_sha256=reservoir_source_sha256,
                gas_atoms=sites.gas_atoms, measure={name: str(value) for name, value in asdict(measure).items()},
                residence_steps=residence_steps,
                consecutive_product_frames=product_frames, last_geometry=observation)
