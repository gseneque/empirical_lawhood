# SPDX-License-Identifier: MPL-2.0
"""One original neutral-gas input, separate from the gas-free state census."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import ActivePreparationProtocol, PreparedCatalyticSite
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import ActiveRelaxationSettings
from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import CatalyticStateSeed
from empirical_lawhood.domains.rubisco.rubisco_response.gas_reactive_model import GasCoordinateEncoding, GasModelConvention, NeutralGasElectronicSelection
from empirical_lawhood.adapters.rubisco.rubisco_response.gas_topology import GasTopologyAugmentation
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection, validate_periodic_probe_model
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import PeriodicForceSettings


SCOPE = 'ONE_NEUTRAL_GAS_START_UNRESTRAINED_MINIMIZATION_WITHOUT_BASIN_POPULATION_OR_RATE_ADMISSION'


@dataclass(frozen=True, slots=True)
class GasRelaxationSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-relaxation-selection'
    prototype: PeriodicProbeSelection
    augmentation: GasTopologyAugmentation
    encoding: GasCoordinateEncoding
    convention: GasModelConvention
    electronic_state: NeutralGasElectronicSelection
    site: PreparedCatalyticSite
    seed: CatalyticStateSeed
    protocol: ActivePreparationProtocol
    settings: ActiveRelaxationSettings
    scope: str = SCOPE

    def __post_init__(self):
        for value, kind in ((self.prototype, PeriodicProbeSelection), (self.augmentation, GasTopologyAugmentation),
                (self.encoding, GasCoordinateEncoding), (self.convention, GasModelConvention),
                (self.electronic_state, NeutralGasElectronicSelection), (self.site, PreparedCatalyticSite),
                (self.seed, CatalyticStateSeed), (self.protocol, ActivePreparationProtocol),
                (self.settings, ActiveRelaxationSettings)):
            exact(value, kind)
        prototype, augmentation = self.prototype, self.augmentation
        exact(prototype.electronic, PeriodicForceSettings)
        path, host = prototype.path, self.site.path
        gas_indices = tuple(row[2] for row in augmentation.gas_atom_correspondence)
        if (self.scope != SCOPE or augmentation.selected_site != self.site.identity
                or augmentation.selected_seed != self.seed.identity or self.seed.site != self.site.identity
                or self.seed.protocol != self.protocol.identity or self.site.protocol != self.protocol.identity
                or self.seed.graph not in {g.identity for g in self.protocol.graphs}
                or next(g.label for g in self.protocol.graphs if g.identity == self.seed.graph) != self.seed.state_label
                or self.seed.construction_findings
                or augmentation.original_representation != host.representation
                or augmentation.original_atom_count != host.physical_atom_count
                or self.seed.physical_atom_count != host.physical_atom_count
                or self.seed.original_coordinate_sha256 != augmentation.original_coordinate_sha256
                or self.seed.expanded_coordinate_sha256 != augmentation.expanded_seed_coordinate_sha256):
            raise ValueError('gas relaxation changes its exact original host, selected seed or complete graph')
        if (self.encoding.augmentation != augmentation.identity
                or self.encoding.original_coordinates != augmentation.augmented_coordinates
                or self.encoding.amber_coordinates != prototype.cell.raw_coordinates
                or self.encoding.coordinate_array != prototype.coordinates.identity
                or self.encoding.physical_atom_count != prototype.physical_atom_count
                or prototype.cell.raw_topology != augmentation.augmented_topology
                or prototype.physical_atom_count != augmentation.original_atom_count+len(gas_indices)
                or self.convention.gas_stock != augmentation.stock.identity):
            raise ValueError('gas relaxation changes its exact topology, coordinate conversion or complete denominator')
        if (self.electronic_state.augmentation != augmentation.identity
                or self.electronic_state.original_path != host.identity
                or self.electronic_state.selected_seed != self.seed.identity
                or self.electronic_state.gas != augmentation.stock.gas
                or self.electronic_state.host_formal_charge != host.qm_formal_charge
                or self.electronic_state.host_multiplicity != host.spin_multiplicity
                or path.qm_formal_charge != self.electronic_state.total_formal_charge
                or path.spin_multiplicity != self.electronic_state.total_multiplicity
                or path.gas != augmentation.stock.gas or host.gas != 'NONE'
                or path.gas == 'O2' and prototype.electronic.ks_flavour != 'UKS'
                or path.gas_atom_indices != gas_indices
                or path.qm_atom_indices != host.qm_atom_indices+gas_indices
                or path.mm_atom_indices != host.mm_atom_indices
                or path.boundaries != host.boundaries
                or path.protein_regions != host.protein_regions
                or path.embedding_method != host.embedding_method
                or path.complement_hamiltonian != host.complement_hamiltonian
                or path.environment_mode != host.environment_mode
                or path.reactive_site_id != host.reactive_site_id
                or path.oxygenation_assumption is not None):
            raise ValueError('gas relaxation changes its complete QM/MM partition or neutral-reactant electronic hypothesis')
        required = {augmentation.identity, self.encoding.identity, self.convention.identity,
            self.electronic_state.identity, self.seed.identity, self.site.identity,
            augmentation.native_parameter_product, augmentation.original_representation}
        if not required.issubset(prototype.sources):
            raise ValueError('gas relaxation loses original preparation and native parameter ancestry')

    @property
    def identity(self):
        return ObjectIdentity.from_record('selection.gas-relaxation.'+self.fingerprint(), self)


def validate_gas_relaxation_model(selection, representation):
    """Join the actual complete gas model without reconstructing its preparation."""
    exact(selection, GasRelaxationSelection)
    validate_periodic_probe_model(selection.prototype, representation)
    augmentation, convention = selection.augmentation, selection.convention
    n = augmentation.original_atom_count
    gas = representation.atoms[n:]
    if (representation.preparation_protocol != convention.identity
            or representation.parameter_model != convention.identity
            or tuple(a.name for a in gas) != tuple(row[0] for row in augmentation.gas_atom_correspondence)
            or tuple(a.source_atom_id for a in gas) != tuple(str(i+1) for i in range(n, len(representation.atoms)))
            or any(a.source != augmentation.augmented_topology for a in gas)
            or augmentation.original_representation not in representation.sources
            or any(i >= n for i in selection.site.path.qm_atom_indices+selection.site.path.mm_atom_indices)):
        raise ValueError('gas relaxation substitutes its complete original host or appended gas atom identities')
    return selection


def prepare_gas_relaxation_selection(*, representation, prototype, augmentation, encoding, convention,
        electronic_state, site, seed, protocol, settings):
    """Bind a single existing input; never widen the original 384-start contract."""
    selection = GasRelaxationSelection(prototype, augmentation, encoding, convention, electronic_state,
        site, seed, protocol, settings)
    return validate_gas_relaxation_model(selection, representation)
