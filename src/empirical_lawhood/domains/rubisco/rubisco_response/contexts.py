# SPDX-License-Identifier: MPL-2.0
"""Selected assay meanings and all-site chemistry, without physical admission."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_nonempty, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoPairedCase, exact, identities

SITE_LIGANDS = ("CABP", "EMPTY", "RUBP", "RUBP_ENEDIOL", "CO2_ADDUCT", "O2_ADDUCT", "PRODUCTS")


@dataclass(frozen=True, slots=True)
class ActiveSiteSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/active-site-selection"
    site_id: str
    lsu_chain_id: str
    catalytic_lysine_position_1based: int
    carbamylated: bool
    magnesium_bound: bool
    ligand_state: str
    protonation_and_tautomers: ObjectIdentity
    metal_coordination: ObjectIdentity
    ligand_chemical_graph: ObjectIdentity

    def __post_init__(self):
        for name in ("site_id", "lsu_chain_id"):
            validate_stable_id(getattr(self, name))
        if (type(self.catalytic_lysine_position_1based) is not int
                or self.catalytic_lysine_position_1based <= 0):
            raise ValueError("catalytic lysine needs its positive complete-sequence position")
        if any(type(getattr(self, name)) is not bool for name in ("carbamylated", "magnesium_bound")):
            raise TypeError("activation and magnesium selections must be explicit")
        if self.ligand_state not in SITE_LIGANDS:
            raise ValueError("active site must retain its selected ligand chemistry")
        for record in (self.protonation_and_tautomers, self.metal_coordination, self.ligand_chemical_graph):
            exact(record, ObjectIdentity)


@dataclass(frozen=True, slots=True)
class ChemicalProtocol(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/chemical-protocol"
    protocol_id: str
    sites: tuple[ActiveSiteSelection, ...]
    other_site_model: str
    solvent_and_ions: ObjectIdentity
    sources: tuple[ObjectIdentity, ...]
    unresolved_requirement_ids: tuple[str, ...]
    interpretation: str = "SELECTED_CHEMISTRY_NOT_PHYSICAL_ADMISSION"

    def __post_init__(self):
        validate_stable_id(self.protocol_id)
        if type(self.sites) is not tuple or len(self.sites) != 8:
            raise ValueError("all eight active-site assignments are mandatory")
        require_sorted_unique_ids(self.sites, attribute="site_id", field_name="sites")
        for site in self.sites:
            exact(site, ActiveSiteSelection)
        if len({site.lsu_chain_id for site in self.sites}) != 8:
            raise ValueError("chemical protocol must assign each LSU active site exactly once")
        if self.other_site_model not in {"EXCHANGEABLE", "FIXED_OCCUPANCY", "COUPLED_STATES"}:
            raise ValueError("other-site coupling must be selected explicitly")
        exact(self.solvent_and_ions, ObjectIdentity)
        identities(self.sources)
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")
        required = {self.solvent_and_ions}
        required.update(record for site in self.sites for record in
                        (site.protonation_and_tautomers, site.metal_coordination, site.ligand_chemical_graph))
        if not required.issubset(self.sources):
            raise ValueError("all-site chemistry loses its source closure")
        if self.interpretation != "SELECTED_CHEMISTRY_NOT_PHYSICAL_ADMISSION":
            raise ValueError("chemical selections cannot admit geometry, forces or rates")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.protocol_id, self)

    @property
    def active_ensemble_selected(self):
        return all(site.carbamylated and site.magnesium_bound and site.ligand_state != "CABP"
                   for site in self.sites)


def validate_paired_chemical_selection(case, protocol):
    """Join every site to both full sequences; no coordinate/native operation."""
    exact(case, RubiscoPairedCase)
    exact(protocol, ChemicalProtocol)
    for material in (case.parent, case.mutant):
        chains = {chain.chain_id: chain for chain in material.chains if chain.subunit == "LSU"}
        if set(chains) != {site.lsu_chain_id for site in protocol.sites}:
            raise ValueError("chemical protocol changes the exact paired LSU census")
        for site in protocol.sites:
            sequence = chains[site.lsu_chain_id].sequence
            position = site.catalytic_lysine_position_1based
            if position > len(sequence) or sequence[position - 1] != "K":
                raise ValueError("selected carbamylation site is not the mapped catalytic lysine")


@dataclass(frozen=True, slots=True)
class RubiscoAssayContext(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/assay-context"
    context_id: str
    temperature_k: Decimal
    ph_interval: tuple[Decimal, Decimal]
    ph_treatment: str
    chemistry: ChemicalProtocol
    product_handling: str
    sources: tuple[ObjectIdentity, ...]
    temperature_selection: str
    temperature_conversion_assessment: ObjectIdentity | None = None
    rubp_regime: str = "SATURATING_RUBP_CONDITIONAL"
    gas_convention: str = "FREE_DISSOLVED_BULK_MICROMOLAR"
    normalization: str = "CARBOXYLATION_EVENTS_PER_ACTIVE_SITE"
    physical_clock_unit: str = "s"

    def __post_init__(self):
        validate_stable_id(self.context_id)
        validate_decimal(self.temperature_k, field_name="temperature_k", minimum=Decimal(0))
        if self.temperature_k == 0:
            raise ValueError("assay temperature must be positive")
        if type(self.ph_interval) is not tuple or len(self.ph_interval) != 2:
            raise ValueError("pH treatment needs an explicit interval")
        for value in self.ph_interval:
            validate_decimal(value, field_name="ph")
        if not 0 <= self.ph_interval[0] <= self.ph_interval[1] <= 14:
            raise ValueError("pH interval must be ordered within [0, 14]")
        for name in ("ph_treatment", "product_handling"):
            validate_nonempty(getattr(self, name), field_name=name)
        exact(self.chemistry, ChemicalProtocol)
        if not self.chemistry.active_ensemble_selected:
            raise ValueError("inhibited or partly unactivated sites cannot alias an active assay ensemble")
        identities(self.sources)
        if self.temperature_selection not in {"NEW_SELECTION", "ASSESSED_CONVERSION"}:
            raise ValueError("temperature must be a new selection or an assessed conversion")
        if (self.temperature_selection == "ASSESSED_CONVERSION") != (self.temperature_conversion_assessment is not None):
            raise ValueError("temperature conversion needs its separate assessment")
        if self.temperature_conversion_assessment is not None:
            exact(self.temperature_conversion_assessment, ObjectIdentity)
            if self.temperature_conversion_assessment not in self.sources:
                raise ValueError("temperature conversion is absent from the assay source closure")
        if (self.rubp_regime != "SATURATING_RUBP_CONDITIONAL"
                or self.gas_convention != "FREE_DISSOLVED_BULK_MICROMOLAR"
                or self.normalization != "CARBOXYLATION_EVENTS_PER_ACTIVE_SITE"
                or self.physical_clock_unit != "s"):
            raise ValueError("assay changes the kinetic clock, substrate, gas or event meaning")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.context_id, self)
