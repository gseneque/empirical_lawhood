# SPDX-License-Identifier: MPL-2.0
"""Explicit chemical alternatives and complete conditional sampling contracts."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    validate_sha256,
    validate_stable_id,
)

NAMESPACE = "rubisco-insilico-free-energy"
UNIT = "rubisco.exposed-gp-te-structural-family"
QUESTION = "What conditional gas-addition free-energy contrasts survive explicit reactive-state, embedding, spin and numerical alternatives in exact full donor/recipient models?"
GAS_SPINS = (("co2", 0), ("o2", 0), ("o2", 2))
# Chemical elements admitted by this finite reactive subsystem contract.
# This is an electron-count check, not a parameter or oxidation-state model.
ATOMIC_NUMBERS = {
    "H": 1,
    "C": 6,
    "N": 7,
    "O": 8,
    "F": 9,
    "Na": 11,
    "Mg": 12,
    "P": 15,
    "S": 16,
    "Cl": 17,
    "K": 19,
    "Ca": 20,
    "Fe": 26,
    "Zn": 30,
}


def positive(value, label):
    if type(value) is not Decimal or not value.is_finite() or value <= 0:
        raise ValueError(label + " must be an explicit finite positive Decimal")


@dataclass(frozen=True, slots=True)
class ChemicalAlternative(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-free-energy/chemical-alternative"
    )
    alternative_id: str
    chemical_state_id: str
    source_members: tuple[ObjectIdentity, ...]
    source_interpretation: str
    kcx_proton_atom_id: str | None
    substrate_proton_atom_id: str | None
    histidine_proton_atom_ids: tuple[str, ...]
    water_atom_ids: tuple[str, ...]
    formal_charge: int
    # Exact ordered atoms/bond orders for reactant and product, not a coarse P state.
    atom_ids: tuple[str, ...]
    elements: tuple[str, ...]
    reactant_bonds: tuple[tuple[str, str, Decimal], ...]
    product_bonds: tuple[tuple[str, str, Decimal], ...]
    gas: str
    spin: int

    def __post_init__(self):
        validate_stable_id(self.alternative_id)
        validate_stable_id(self.chemical_state_id)
        if (
            not self.source_members
            or not self.source_interpretation
            or (self.gas, self.spin) not in GAS_SPINS
        ):
            raise ValueError(
                "chemical alternative requires source support and explicit gas/spin"
            )
        if (
            type(self.formal_charge) is not int
            or not self.atom_ids
            or len(self.atom_ids) != len(set(self.atom_ids))
            or len(self.atom_ids) != len(self.elements)
        ):
            raise ValueError("reactive state omits exact charge/full atom denominator")
        if any(e not in ATOMIC_NUMBERS for e in self.elements):
            raise ValueError("reactive element has no declared electron-count contract")
        electrons = sum(ATOMIC_NUMBERS[e] for e in self.elements) - self.formal_charge
        if (
            type(self.spin) is not int
            or electrons <= 0
            or self.spin > electrons
            or electrons % 2 != self.spin % 2
        ):
            raise ValueError("reactive charge/elements/spin electron census differs")
        members = set(self.atom_ids)
        referenced = (
            *self.histidine_proton_atom_ids,
            *self.water_atom_ids,
            *(() if self.kcx_proton_atom_id is None else (self.kcx_proton_atom_id,)),
            *(
                ()
                if self.substrate_proton_atom_id is None
                else (self.substrate_proton_atom_id,)
            ),
        )
        if any(x not in members for x in referenced):
            raise ValueError("reactive proton/water identity is absent")
        if not self.reactant_bonds or not self.product_bonds:
            raise ValueError(
                "reactive endpoints require exact atom/bond correspondence"
            )
        for bonds in (self.reactant_bonds, self.product_bonds):
            if len({tuple(sorted((a, b))) for a, b, _ in bonds}) != len(bonds):
                raise ValueError("duplicate reactive bond")
            for a, b, order in bonds:
                positive(order, "bond order")
                if a not in members or b not in members or a == b:
                    raise ValueError("reactive bond substitutes atom identity")


@dataclass(frozen=True, slots=True)
class EngineBinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-free-energy/engine-binding"
    )
    interpreter: str
    source_inventory: tuple[tuple[str, int, str], ...]
    electronic_method: str
    basis: str
    scf_energy_tolerance: Decimal
    scf_maximum_iterations: int
    gradient_tolerance: Decimal
    density_grid_level: int
    threads: int

    def __post_init__(self):
        if (
            not self.interpreter.startswith("/")
            or not self.electronic_method
            or not self.basis
            or not self.source_inventory
        ):
            raise ValueError(
                "reactive engine requires exact selected executable/source/method"
            )
        if tuple(r[0] for r in self.source_inventory) != tuple(
            sorted({r[0] for r in self.source_inventory})
        ):
            raise ValueError(
                "engine source inventory is incomplete/duplicated/unordered"
            )
        for path, size, digest in self.source_inventory:
            validate_sha256(digest)
            if not path.startswith("/") or type(size) is not int or size <= 0:
                raise ValueError("engine file custody is not exact")
        positive(self.scf_energy_tolerance, "SCF energy tolerance")
        positive(self.gradient_tolerance, "gradient tolerance")
        if (
            type(self.scf_maximum_iterations) is not int
            or self.scf_maximum_iterations <= 0
            or type(self.threads) is not int
            or self.threads <= 0
            or type(self.density_grid_level) is not int
            or self.density_grid_level < 0
        ):
            raise ValueError("engine numerical settings must be explicit integers")


@dataclass(frozen=True, slots=True)
class ReactiveModel(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-free-energy/reactive-model"
    )
    model_id: str
    original_assets: ObjectIdentity
    preparation_assessment: ObjectIdentity
    alternative: ChemicalAlternative
    full_assembly_atom_ids: tuple[str, ...]
    qm_atom_ids: tuple[str, ...]
    qm_coordinates_angstrom: tuple[tuple[Decimal, Decimal, Decimal], ...]
    # Full exact surrounding field with declared Gaussian widths; no point-charge singularity default.
    embedding: tuple[
        tuple[str, Decimal, tuple[Decimal, Decimal, Decimal], Decimal], ...
    ]
    link_atom_ids: tuple[str, ...]
    boundary_definition: str
    # Complete non-electrostatic complement and exact construction proof are required.
    complement: ObjectIdentity
    transformation: ObjectIdentity
    environment_scope: str

    def __post_init__(self):
        validate_stable_id(self.model_id)
        self.alternative.__post_init__()
        if not self.full_assembly_atom_ids or len(
            set(self.full_assembly_atom_ids)
        ) != len(self.full_assembly_atom_ids):
            raise ValueError("full assembly atom census omitted/duplicated")
        if self.qm_atom_ids != self.alternative.atom_ids or len(
            self.qm_coordinates_angstrom
        ) != len(self.qm_atom_ids):
            raise ValueError("QM state changes exact reactive atom/geometry census")
        if (
            not self.boundary_definition
            or self.environment_scope != "FIXED_FULL_ASSEMBLY_EMBEDDING_CONDITIONAL"
        ):
            raise ValueError("reactive environment scope must be explicit")
        field = tuple(r[0] for r in self.embedding)
        if (
            len(self.link_atom_ids) != len(set(self.link_atom_ids))
            or not set(self.link_atom_ids) <= set(self.qm_atom_ids)
            or set(self.link_atom_ids) & set(self.full_assembly_atom_ids)
        ):
            raise ValueError("link atoms must be distinct nonphysical QM atoms")
        physical_qm = set(self.qm_atom_ids) - set(self.link_atom_ids)
        if (
            len(set(field)) != len(field)
            or set(field) & physical_qm
            or physical_qm | set(field) != set(self.full_assembly_atom_ids)
        ):
            raise ValueError(
                "QM/MM partition omits/duplicates complete actual surrounding assembly"
            )
        for _, charge, xyz, width in self.embedding:
            positive(width, "embedding Gaussian radius")
            if not charge.is_finite() or any(not x.is_finite() for x in xyz):
                raise ValueError("embedding quantities unknown/nonfinite")
        if any(not x.is_finite() for xyz in self.qm_coordinates_angstrom for x in xyz):
            raise ValueError("reactive coordinates unknown/nonfinite")


@dataclass(frozen=True, slots=True)
class UmbrellaWindow(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-free-energy/umbrella-window"
    )
    window_id: str
    model_id: str
    initialization: str
    cv_atom_ids: tuple[tuple[str, ...], ...]
    cv_kinds: tuple[str, ...]
    centers: tuple[Decimal, ...]
    force_constants: tuple[Decimal, ...]
    equilibration_steps: int
    sampling_steps: int
    sample_interval: int
    random_seed: int
    proposal_angstrom: Decimal

    def __post_init__(self):
        validate_stable_id(self.window_id)
        if self.initialization not in ("REACTANT", "PRODUCT"):
            raise ValueError("independent directional initialization must be declared")
        if (
            not self.centers
            or len(
                {
                    len(self.centers),
                    len(self.force_constants),
                    len(self.cv_atom_ids),
                    len(self.cv_kinds),
                }
            )
            != 1
        ):
            raise ValueError("umbrella omits full selected CV/restraint census")
        if any(type(x) is not Decimal or not x.is_finite() for x in self.centers):
            raise ValueError("umbrella centers require explicit finite Decimals")
        if any(
            k not in ("DISTANCE", "DISTANCE_DIFFERENCE", "IMPROPER_DIHEDRAL")
            for k in self.cv_kinds
        ):
            raise ValueError("unknown reactive CV")
        for k, ids in zip(self.cv_kinds, self.cv_atom_ids, strict=True):
            if len(ids) != (
                {"DISTANCE": 2, "DISTANCE_DIFFERENCE": 3, "IMPROPER_DIHEDRAL": 4}[k]
            ) or len(set(ids)) != len(ids):
                raise ValueError("CV changes ordered atom identities")
        for k in self.force_constants:
            positive(k, "umbrella force constant")
        positive(self.proposal_angstrom, "Metropolis proposal")
        if (
            any(
                type(x) is not int or x < 0
                for x in (
                    self.equilibration_steps,
                    self.sampling_steps,
                    self.random_seed,
                )
            )
            or self.sampling_steps <= 0
            or type(self.sample_interval) is not int
            or self.sample_interval <= 0
        ):
            raise ValueError(
                "sampling requires explicit complete step/seed declarations"
            )


@dataclass(frozen=True, slots=True)
class FreeEnergySelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-free-energy/selection"
    selection_id: str
    actual_mechanism: ObjectIdentity
    actual_preparation: ObjectIdentity
    original_assets_roster: tuple[ObjectIdentity, ...]
    chemical_states: tuple[str, ...]
    models: tuple[ReactiveModel, ...]
    engine: EngineBinding
    windows: tuple[UmbrellaWindow, ...]
    temperature_kelvin: Decimal
    standard_state_definition: str
    standard_state_correction: ObjectIdentity
    independent_refinement: ObjectIdentity
    minimum_effective_samples: Decimal
    minimum_adjacent_overlap: Decimal
    maximum_block_disagreement_kcal: Decimal
    maximum_refinement_disagreement_kcal: Decimal
    native_workdir: str

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        self.engine.__post_init__()
        positive(self.temperature_kelvin, "temperature")
        for x in (
            self.minimum_effective_samples,
            self.minimum_adjacent_overlap,
            self.maximum_block_disagreement_kcal,
            self.maximum_refinement_disagreement_kcal,
        ):
            positive(x, "free-energy admission threshold")
        if (
            self.minimum_adjacent_overlap >= 1
            or not self.standard_state_definition
            or not self.native_workdir.startswith(
                "/media/chevre/SEMIOS/empirical-lawhood-applied-el/20261011/reopen01/rubisco-insilico01/working/"
            )
        ):
            raise ValueError(
                "conditional standard state/workdir/overlap scope is not explicit"
            )
        ids = tuple(m.model_id for m in self.models)
        if not ids or ids != tuple(sorted(set(ids))):
            raise ValueError("reactive model roster omitted/duplicated/unordered")
        for m in self.models:
            m.__post_init__()
        if (
            not self.original_assets_roster
            or len(set(self.original_assets_roster)) != len(self.original_assets_roster)
            or {m.original_assets for m in self.models}
            != set(self.original_assets_roster)
        ):
            raise ValueError("reactive models change complete original asset census")
        if not self.chemical_states or self.chemical_states != tuple(
            sorted(set(self.chemical_states))
        ):
            raise ValueError("chemical alternative census omitted/duplicated/unordered")
        for state in self.chemical_states:
            validate_stable_id(state)
        required = {
            (original, state, gas, spin)
            for original in self.original_assets_roster
            for state in self.chemical_states
            for gas, spin in GAS_SPINS
        }
        actual = tuple(
            (
                m.original_assets,
                m.alternative.chemical_state_id,
                m.alternative.gas,
                m.alternative.spin,
            )
            for m in self.models
        )
        if len(set(actual)) != len(actual) or set(actual) != required:
            raise ValueError(
                "every full model/state must retain both gases and oxygen spin surfaces"
            )
        wids = tuple(w.window_id for w in self.windows)
        if not wids or wids != tuple(sorted(set(wids))):
            raise ValueError("complete window census omitted/duplicated/unordered")
        for w in self.windows:
            w.__post_init__()
            if w.model_id not in ids:
                raise ValueError("umbrella substitutes selected reactive model")
            model = next(m for m in self.models if m.model_id == w.model_id)
            if any(
                atom not in model.qm_atom_ids
                for atoms in w.cv_atom_ids
                for atom in atoms
            ):
                raise ValueError("umbrella substitutes actual reactive atom identity")
        if {w.model_id for w in self.windows} != set(ids):
            raise ValueError("reactive model has no selected sampling windows")
        for model in ids:
            if {w.initialization for w in self.windows if w.model_id == model} != {
                "REACTANT",
                "PRODUCT",
            }:
                raise ValueError(
                    "reactive model omits reversible directional initialization"
                )


@dataclass(frozen=True, slots=True)
class WindowTrace(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-free-energy/window-trace"
    )
    trace_id: str
    selection: ObjectIdentity
    window: UmbrellaWindow
    # Every retained production observation: actual ordinal, physical energy in kcal/mol, full CV vector.
    observations: tuple[tuple[int, Decimal, tuple[Decimal, ...]], ...]
    attempted_energy_calls: int
    completed_energy_calls: int
    disposition: A
    reason_codes: tuple[str, ...]
    cpu_seconds: Decimal | None
    wall_seconds: Decimal | None
    raw_files: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.trace_id)
        self.window.__post_init__()
        if (
            type(self.attempted_energy_calls) is not int
            or type(self.completed_energy_calls) is not int
            or not 0 <= self.completed_energy_calls <= self.attempted_energy_calls
        ):
            raise ValueError("quantum-call ledger omits/forges attempts")
        for cost in (self.cpu_seconds, self.wall_seconds):
            if cost is not None and (not cost.is_finite() or cost < 0):
                raise ValueError("unknown native cost must remain unknown")
        if self.disposition is A.SATISFIED and (
            not self.observations
            or not self.raw_files
            or not self.attempted_energy_calls
            or self.completed_energy_calls != self.attempted_energy_calls
        ):
            raise ValueError(
                "successful window has no complete actual samples/SCF/custody"
            )
        ordinals = tuple(r[0] for r in self.observations)
        if ordinals != tuple(sorted(set(ordinals))):
            raise ValueError("sampling observations repeat or reorder actual ordinals")
        for _, energy, cv in self.observations:
            if (
                not energy.is_finite()
                or len(cv) != len(self.window.centers)
                or any(not x.is_finite() for x in cv)
            ):
                raise ValueError("sample lacks full finite energy/CV observation")


def identity(record):
    for name in (
        "selection_id",
        "model_id",
        "trace_id",
        "product_id",
        "alternative_id",
        "window_id",
    ):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError("unknown reactive record identity")
