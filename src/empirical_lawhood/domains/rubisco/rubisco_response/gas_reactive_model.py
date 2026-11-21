# SPDX-License-Identifier: MPL-2.0
"""Complete neutral-gas reactant candidates for the existing periodic owners.

This is preparation, not chemical admission. Original binary64 coordinates
remain bound separately from the explicitly rounded Amber input successor.
An oxygen triplet candidate supplies no charge-transfer or spin-crossing rate.
"""

from dataclasses import dataclass, replace
from decimal import Decimal as D, localcontext
from hashlib import sha256
import re
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import assigned_census_supported_inactive14, read_prmtop
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import PreparedCatalyticSite
from empirical_lawhood.domains.rubisco.rubisco_response.catalytic_path_selection import CatalyticPathSelection, validate_catalytic_path_selection
from empirical_lawhood.domains.rubisco.rubisco_response.gas_amber_stock import GasAmberStock
from empirical_lawhood.adapters.rubisco.rubisco_response.gas_topology import GasTopologyAugmentation
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import read_initial_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularAtom, MolecularRepresentation, MolecularResidue, NativeTopologyBond, validate_amber_atom_correspondence
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import AmberPeriodicCell, PeriodicForceSettings, read_amber_periodic_cell


_PRECISION = D('0.00000005')
_SCOPE = 'NEUTRAL_GAS_REACTANT_CANDIDATE_NOT_POPULATED_ENCOUNTER_OR_KINETIC_ADMISSION'


def _ordered(values):
    return tuple(sorted(set(values), key=lambda row: row.object_id))


@dataclass(frozen=True, slots=True)
class GasModelConvention(CanonicalRecord):
    """Shared preparation/parameter selection, distinct from each native return."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-model-convention'
    host_preparation_protocol: ObjectIdentity
    host_parameter_model: ObjectIdentity
    gas_stock: ObjectIdentity
    coordinate_format: str = 'AMBER_ASCII_F12.7_NO_VELOCITIES'
    host_selection: str = 'EXACT_COMPLETE_SELECTED_GAS_FREE_SEED'
    gas_selection: str = 'ONE_SOURCE_BOUND_GAS_AT_SELECTED_FOCAL_SITE'

    def __post_init__(self):
        for value in (self.host_preparation_protocol, self.host_parameter_model, self.gas_stock):
            exact(value, ObjectIdentity)
        if (self.gas_stock.object_schema != GasAmberStock.SCHEMA
                or self.coordinate_format != 'AMBER_ASCII_F12.7_NO_VELOCITIES'
                or self.host_selection != 'EXACT_COMPLETE_SELECTED_GAS_FREE_SEED'
                or self.gas_selection != 'ONE_SOURCE_BOUND_GAS_AT_SELECTED_FOCAL_SITE'):
            raise ValueError('gas model convention changes its original parameter or preparation selection')

    @property
    def identity(self):
        return ObjectIdentity.from_record('gas-model-convention.'+self.fingerprint(), self)


@dataclass(frozen=True, slots=True)
class GasCoordinateEncoding(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-coordinate-encoding'
    augmentation: ObjectIdentity
    original_coordinates: ObjectIdentity
    amber_coordinates: ObjectIdentity
    coordinate_array: ObjectIdentity
    physical_atom_count: int
    changed_binary64_components: int
    maximum_binary64_change_angstrom: D
    maximum_printing_error_angstrom: D
    format: str = 'AMBER_ASCII_F12.7_NO_VELOCITIES'

    def __post_init__(self):
        for row in (self.augmentation, self.original_coordinates,
                self.amber_coordinates, self.coordinate_array):
            exact(row, ObjectIdentity)
        if (type(self.physical_atom_count) is not int or self.physical_atom_count <= 0
                or type(self.changed_binary64_components) is not int
                or not 0 <= self.changed_binary64_components <= self.physical_atom_count*3
                or self.format != 'AMBER_ASCII_F12.7_NO_VELOCITIES'):
            raise ValueError('gas coordinate encoding changes its complete census or explicit format')
        validate_decimal(self.maximum_binary64_change_angstrom,
            field_name='maximum_binary64_change_angstrom', minimum=D(0))
        validate_decimal(self.maximum_printing_error_angstrom,
            field_name='maximum_printing_error_angstrom', minimum=D(0))
        if self.maximum_printing_error_angstrom > _PRECISION:
            raise ValueError('gas coordinate encoding exceeds the selected F12.7 rounding bound')
        if (self.changed_binary64_components == 0) != (self.maximum_binary64_change_angstrom == 0):
            raise ValueError('gas coordinate encoding conceals a changed coordinate component')

    @property
    def identity(self):
        return ObjectIdentity.from_record('gas-coordinate-encoding.'+self.fingerprint(), self)


@dataclass(frozen=True, slots=True)
class NeutralGasElectronicSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/neutral-gas-electronic-selection'
    augmentation: ObjectIdentity
    original_path: ObjectIdentity
    selected_seed: ObjectIdentity
    gas: str
    host_formal_charge: int
    host_multiplicity: int
    gas_formal_charge: int
    gas_multiplicity: int
    total_formal_charge: int
    total_multiplicity: int
    scope: str = _SCOPE

    def __post_init__(self):
        for row in (self.augmentation, self.original_path, self.selected_seed):
            exact(row, ObjectIdentity)
        values = (self.host_formal_charge, self.host_multiplicity, self.gas_formal_charge,
            self.gas_multiplicity, self.total_formal_charge, self.total_multiplicity)
        if (any(type(v) is not int for v in values) or self.gas not in {'CO2', 'O2'}
                or self.host_multiplicity != 1 or self.gas_formal_charge != 0
                or self.gas_multiplicity != {'CO2': 1, 'O2': 3}[self.gas]
                or self.total_formal_charge != self.host_formal_charge
                or self.total_multiplicity != self.gas_multiplicity or self.scope != _SCOPE):
            raise ValueError('neutral gas candidate changes its singlet host, neutral gas or coupled spin selection')

    @property
    def identity(self):
        return ObjectIdentity.from_record('neutral-gas-electronic.'+self.fingerprint(), self)


def _raw_identity(kind, payload):
    digest = sha256(payload).hexdigest()
    return ObjectIdentity('gas-reactant.'+kind+'.'+digest,
        'empirical-lawhood/rubisco-response/'+kind+'-bytes', '1.0.0', digest)


def encode_gas_amber_coordinates(*, augmentation, coordinate_bytes, original_cell):
    """Create a disclosed F12.7 successor, retaining the exact input identity."""
    import numpy as np

    exact(augmentation, GasTopologyAugmentation)
    exact(original_cell, AmberPeriodicCell)
    n = augmentation.original_atom_count+len(augmentation.gas_atom_correspondence)
    if (type(coordinate_bytes) is not bytes or len(coordinate_bytes) != n*24
            or sha256(coordinate_bytes).hexdigest() != augmentation.augmented_coordinates.object_fingerprint
            or sha256(coordinate_bytes[:augmentation.original_atom_count*24]).hexdigest()
                != augmentation.expanded_seed_coordinate_sha256
            or original_cell.identity != augmentation.original_cell
            or original_cell.physical_atom_count != augmentation.original_atom_count):
        raise ValueError('gas coordinate encoding substitutes its exact original array or cell')
    points = np.frombuffer(coordinate_bytes, dtype='<f8').reshape((n, 3))
    if not np.isfinite(points).all():
        raise ValueError('gas coordinate encoding requires finite complete physical coordinates')
    tokens = tuple(f'{float(v):12.7f}' for v in points.flat)
    box = tuple(f'{v:12.7f}' for v in (*original_cell.lengths_angstrom, *original_cell.angles_degrees))
    if any(len(v) != 12 for v in (*tokens, *box)):
        raise ValueError('gas coordinate exceeds the selected Amber twelve-column format')
    if tuple(D(v) for v in box) != (*original_cell.lengths_angstrom, *original_cell.angles_degrees):
        raise ValueError('gas coordinate encoding would change an exact original cell component')
    raw = ('Source-bound neutral gas candidate; original binary64 coordinates retained\n'
        +str(n)+'\n'+'\n'.join(''.join(tokens[i:i+6]) for i in range(0, len(tokens), 6))
        +'\n'+''.join(box)+'\n').encode('ascii')
    parsed, _ = read_initial_coordinates(raw.decode('ascii'), n, periodic=True)
    encoded = np.asarray(parsed, dtype='<f8').tobytes()
    # Decimal.from_float compares the exact binary64 input to the printed
    # decimal, without adding an arbitrary tolerance to the F12.7 half-unit.
    changed, maximum, printing = _encoding_changes(points, parsed)
    raw_identity = _raw_identity('amber-coordinate', raw)
    array_id = sha256((augmentation.augmented_topology.object_fingerprint+raw_identity.object_fingerprint).encode('ascii')).hexdigest()
    arrays = ArrayDatasetManifest('arrays.gas-reactant.'+array_id,
        (ArrayDatasetMember('coordinates-angstrom', '<f8', (n, 3), sha256(encoded).hexdigest()),),
        _ordered((augmentation.augmented_topology, raw_identity)))
    encoding = GasCoordinateEncoding(augmentation.identity, augmentation.augmented_coordinates,
        raw_identity, arrays.identity, n, changed, maximum, printing)
    return raw, encoded, arrays, encoding


def _encoding_changes(points, parsed):
    """Exact errors from each binary64 value and each retained decimal token."""
    changed, maximum, printing = 0, D(0), D(0)
    # Includes subnormals, without depending on the caller's Decimal context.
    with localcontext() as context:
        context.prec = 1100
        for original, row in zip(points, parsed, strict=True):
            for before, token in zip(original, row, strict=True):
                before = D.from_float(float(before))
                after = D.from_float(float(token))
                difference = abs(after-before)
                changed += bool(difference)
                maximum = max(maximum, difference)
                printing = max(printing, abs(token-before))
    return changed, maximum, printing


def prepare_gas_reactive_candidate(*, representation, prepared_site, original_cell, electronic_settings,
        augmentation, augmented_topology_bytes, augmented_coordinate_bytes):
    """Derive full correspondence from an original-bound augmentation.

    The caller authenticates and assesses the original augmentation and its
    native parameter return through the existing preparation reader. This
    function grants neither that custody nor scientific/native admission.
    """
    exact(representation, MolecularRepresentation)
    exact(augmentation, GasTopologyAugmentation)
    exact(prepared_site, PreparedCatalyticSite)
    parent_path = prepared_site.path
    exact(parent_path, CatalyticPathSelection)
    exact(original_cell, AmberPeriodicCell)
    exact(electronic_settings, PeriodicForceSettings)
    validate_catalytic_path_selection(parent_path, representation)
    n = len(representation.atoms)
    site = next(s for s in representation.sites if s.site_id == parent_path.reactive_site_id)
    if (augmentation.original_representation != representation.identity
            or augmentation.original_topology != representation.raw_topology
            or augmentation.original_atom_count != n or augmentation.original_cell != original_cell.identity
            or augmentation.selected_site != prepared_site.identity
            or original_cell.raw_topology != representation.raw_topology
            or original_cell.raw_coordinates != representation.raw_coordinates
            or parent_path.gas != 'NONE' or site.gas_atom_indices
            or parent_path.spin_multiplicity != 1):
        raise ValueError('gas candidate substitutes its complete original singlet gas-free host')
    if (type(augmented_topology_bytes) is not bytes
            or sha256(augmented_topology_bytes).hexdigest() != augmentation.augmented_topology.object_fingerprint):
        raise ValueError('gas candidate substitutes its exact retained Amber topology')
    raw, coordinates, arrays, encoding = encode_gas_amber_coordinates(augmentation=augmentation,
        coordinate_bytes=augmented_coordinate_bytes, original_cell=original_cell)
    table = read_prmtop(augmented_topology_bytes.decode('ascii'))
    census = assigned_census_supported_inactive14(table)
    gas_indices = tuple(row[2] for row in augmentation.gas_atom_correspondence)
    if (census['term_census']['atoms'] != n+len(gas_indices)
            or tuple(census['atom_names'][n:]) != tuple(row[0] for row in augmentation.gas_atom_correspondence)
            or census['residue_names'][-1] != augmentation.stock.gas
            or census['residue_starts'][-1] != n+1):
        raise ValueError('gas candidate changes the appended gas atom or residue correspondence')
    gas = augmentation.stock.gas
    if gas == 'O2' and electronic_settings.ks_flavour != 'UKS':
        raise ValueError('neutral oxygen triplet requires explicitly selected unrestricted settings')
    electronic = NeutralGasElectronicSelection(augmentation.identity, parent_path.identity,
        augmentation.selected_seed, gas, parent_path.qm_formal_charge, parent_path.spin_multiplicity,
        0, 1 if gas == 'CO2' else 3, parent_path.qm_formal_charge, 1 if gas == 'CO2' else 3)
    convention = GasModelConvention(representation.preparation_protocol,
        representation.parameter_model, augmentation.stock.identity)
    # Corresponding gas atoms keep the same named site/residue roles in WT
    # and mutant. Their different native indices and producing returns remain
    # explicit source operands, rather than changes to physical atom identity.
    residue_id = 'residue.gas-reactant.'+site.site_id+'.'+gas.lower()
    residue = MolecularResidue(residue_id, gas, 'GAS', None, None, None, None, None, '',
        augmentation.stock.identity, site.site_id)
    atoms = tuple(MolecularAtom(residue_id+'.'+census['atom_names'][i].lower(), residue_id,
        census['atom_names'][i], census['atomic_numbers'][i], census['masses'][i],
        census['charges_scaled'][i], D('18.2223'), census['atom_types'][i],
        augmentation.augmented_topology, str(i+1)) for i in gas_indices)
    gas_edges = set()
    for name in ('BONDS_INC_HYDROGEN', 'BONDS_WITHOUT_HYDROGEN'):
        for row in census['indexed_bonded_terms'][name]:
            first, second = sorted((row[0]//3, row[1]//3))
            if first >= n:
                gas_edges.add((first, second))
            elif second >= n:
                raise ValueError('gas candidate invents a bonded gas-host connection')
    sources = _ordered((*representation.sources, representation.identity, parent_path.identity,
        augmentation.identity, augmentation.stock.identity, augmentation.encounter,
        augmentation.preparation, augmentation.selected_seed, augmentation.selected_site,
        augmentation.native_parameter_product, augmentation.augmented_topology,
        augmentation.augmented_coordinates, encoding.identity, encoding.amber_coordinates,
        original_cell.identity, electronic.identity, electronic_settings.identity, convention.identity))
    model_id = sha256(''.join(row.object_fingerprint for row in sources).encode('ascii')).hexdigest()
    model = replace(representation, representation_id='molecular.gas-reactant.'+model_id,
        preparation_protocol=convention.identity, parameter_model=convention.identity,
        raw_topology=augmentation.augmented_topology, raw_coordinates=encoding.amber_coordinates,
        residues=tuple(sorted((*representation.residues, residue), key=lambda r: r.residue_id)),
        atoms=representation.atoms+atoms,
        bonds=tuple(sorted((*representation.bonds, *(NativeTopologyBond(a, b) for a, b in gas_edges)),
            key=lambda r: (r.first, r.second))),
        sites=tuple(replace(s, gas_atom_indices=gas_indices) if s.site_id == site.site_id else s
            for s in representation.sites), arrays=arrays, sources=sources)
    validate_amber_atom_correspondence(model, augmented_topology_bytes)
    cell = read_amber_periodic_cell(model, augmented_topology_bytes, raw)
    if (cell.lengths_angstrom, cell.angles_degrees) != (original_cell.lengths_angstrom, original_cell.angles_degrees):
        raise ValueError('gas candidate changes the original periodic environment')
    path = replace(parent_path, selection_id='path.gas-reactant.'+model.fingerprint(),
        representation=model.identity, physical_atom_count=len(model.atoms),
        qm_atom_indices=parent_path.qm_atom_indices+gas_indices,
        gas=gas, gas_atom_indices=gas_indices, spin_multiplicity=electronic.total_multiplicity,
        electronic_approximation=electronic_settings.identity,
        # The neutral reactant hypothesis supplies no oxygen crossing mechanism.
        oxygenation_assumption=None,
        sources=_ordered((*parent_path.sources, *model.sources, model.identity, electronic.identity)))
    remaining = validate_catalytic_path_selection(path, model)
    return dict(representation=model, path=path, cell=cell, encoding=encoding, convention=convention,
        electronic_selection=electronic, electronic_settings=electronic_settings,
        raw_coordinate_bytes=raw, coordinate_bytes=coordinates,
        required=remaining, physical_or_chemical_admission=False)


def assess_gas_reactive_candidate(*, candidate, representation, prepared_site, original_cell, electronic_settings,
        augmentation, augmented_topology_bytes, augmented_coordinate_bytes):
    """Check the retained complete model without calling either constructor.

    Raw parameter/encounter assessment remains the original augmentation
    reader's responsibility. This check cannot turn its candidate into an
    equilibrated, charge-transfer, crossing or rate observation.
    """
    import numpy as np

    if type(candidate) is not dict or set(candidate) != {'representation', 'path', 'cell', 'encoding', 'convention',
            'electronic_selection', 'electronic_settings', 'raw_coordinate_bytes', 'coordinate_bytes', 'required',
            'physical_or_chemical_admission'} or candidate['physical_or_chemical_admission'] is not False:
        raise ValueError('gas model readout changes its exact candidate contract')
    for value, kind in ((representation, MolecularRepresentation), (prepared_site, PreparedCatalyticSite),
            (original_cell, AmberPeriodicCell), (augmentation, GasTopologyAugmentation),
            (electronic_settings, PeriodicForceSettings)):
        exact(value, kind)
    model, path, cell, encoding, electronic = (candidate[k] for k in
        ('representation', 'path', 'cell', 'encoding', 'electronic_selection'))
    convention = candidate['convention']
    for value, kind in ((model, MolecularRepresentation), (path, CatalyticPathSelection),
            (cell, AmberPeriodicCell), (encoding, GasCoordinateEncoding),
            (electronic, NeutralGasElectronicSelection), (convention, GasModelConvention)):
        exact(value, kind)
    n = len(representation.atoms)
    parent = prepared_site.path
    gas = augmentation.stock.gas
    gas_indices = tuple(i for _, _, i in augmentation.gas_atom_correspondence)
    if (augmentation.original_representation, augmentation.selected_site, augmentation.original_cell,
            augmentation.original_topology, augmentation.original_atom_count) != (
            representation.identity, prepared_site.identity, original_cell.identity, representation.raw_topology, n):
        raise ValueError('gas model readout substitutes its original host, prepared site or cell')
    validate_catalytic_path_selection(parent, representation)
    if parent.gas != 'NONE' or parent.spin_multiplicity != 1:
        raise ValueError('gas model readout requires its original singlet gas-free parent')
    if (model.material, model.chemistry, model.temperature_k, model.atoms[:n]) != (
            representation.material, representation.chemistry, representation.temperature_k, representation.atoms):
        raise ValueError('gas model readout changes an original host atom, material or chemical context')
    old_residues = {r.residue_id: r for r in representation.residues}
    new_residues = {r.residue_id: r for r in model.residues}
    if (any(new_residues.get(key) != row for key, row in old_residues.items())
            or len(new_residues) != len(old_residues)+1
            or tuple(b for b in model.bonds if b.second < n) != representation.bonds):
        raise ValueError('gas model readout changes an original residue or host bond')
    extra, = (r for r in model.residues if r.residue_id not in old_residues)
    if (extra.residue_id != 'residue.gas-reactant.'+parent.reactive_site_id+'.'+gas.lower()
            or (extra.role, extra.component, extra.site_id, extra.source, extra.chain_id,
            extra.sequence_position_1based, extra.sequence_letter, extra.author_chain,
            extra.author_number, extra.insertion_code) != (
            'GAS', gas, parent.reactive_site_id, augmentation.stock.identity,
            None, None, None, None, None, '')):
        raise ValueError('gas model readout changes the source-to-site gas residue')
    if (len(model.atoms) != n+len(gas_indices)
            or tuple(a.name for a in model.atoms[n:]) != tuple(r[0] for r in augmentation.gas_atom_correspondence)
            or any((model.atoms[i].residue_id, model.atoms[i].source, model.atoms[i].source_atom_id)
                != (extra.residue_id, augmentation.augmented_topology, str(i+1)) for i in gas_indices)):
        raise ValueError('gas model readout changes a complete gas atom origin')
    for before, after in zip(representation.sites, model.sites, strict=True):
        wanted = replace(before, gas_atom_indices=gas_indices) if before.site_id == parent.reactive_site_id else before
        if after != wanted:
            raise ValueError('gas model readout changes an original focal or nonfocal site')
    if ((convention.host_preparation_protocol, convention.host_parameter_model, convention.gas_stock) != (
                representation.preparation_protocol, representation.parameter_model, augmentation.stock.identity)
            or model.raw_topology != augmentation.augmented_topology
            or model.preparation_protocol != convention.identity
            or model.parameter_model != convention.identity
            or not {*representation.sources, representation.identity, parent.identity,
                augmentation.identity, augmentation.stock.identity, augmentation.encounter,
                augmentation.preparation, augmentation.selected_seed, augmentation.selected_site,
                augmentation.native_parameter_product, augmentation.augmented_coordinates,
                encoding.identity, original_cell.identity, electronic.identity,
                electronic_settings.identity, convention.identity}.issubset(model.sources)):
        raise ValueError('gas model readout drops its complete source or parameter closure')
    validate_amber_atom_correspondence(model, augmented_topology_bytes)
    raw, coordinates = candidate['raw_coordinate_bytes'], candidate['coordinate_bytes']
    if any(type(value) is not bytes for value in (raw, coordinates, augmented_coordinate_bytes)):
        raise ValueError('gas model readout requires retained original and successor coordinate bytes')
    if (sha256(augmented_coordinate_bytes).hexdigest() != augmentation.augmented_coordinates.object_fingerprint
            or len(augmented_coordinate_bytes) != len(model.atoms)*24
            or sha256(augmented_coordinate_bytes[:n*24]).hexdigest() != augmentation.expanded_seed_coordinate_sha256
            or sha256(raw).hexdigest() != model.raw_coordinates.object_fingerprint):
        raise ValueError('gas model readout substitutes a retained original or successor coordinate source')
    points, _ = read_initial_coordinates(raw.decode('ascii'), len(model.atoms), periodic=True)
    for line in raw.decode('ascii').splitlines()[2:]:
        if len(line) % 12 or any(re.fullmatch(r' *-?[0-9]+\.[0-9]{7}', line[i:i+12]) is None
                for i in range(0, len(line), 12)):
            raise ValueError('gas model readout changes its declared F12.7 coordinate format')
    if (coordinates != np.asarray(points, dtype='<f8').tobytes()
            or sha256(coordinates).hexdigest() != model.arrays.members[0].sha256):
        raise ValueError('gas model readout changes the Amber-to-binary64 array join')
    changed, maximum, printing = _encoding_changes(
        np.frombuffer(augmented_coordinate_bytes, dtype='<f8').reshape((-1, 3)), points)
    if (encoding.augmentation, encoding.original_coordinates, encoding.amber_coordinates,
            encoding.coordinate_array, encoding.physical_atom_count, encoding.changed_binary64_components,
            encoding.maximum_binary64_change_angstrom, encoding.maximum_printing_error_angstrom) != (
            augmentation.identity, augmentation.augmented_coordinates, model.raw_coordinates,
            model.arrays.identity, len(model.atoms), changed, maximum, printing):
        raise ValueError('gas model readout changes its measured coordinate encoding loss')
    if (cell != read_amber_periodic_cell(model, augmented_topology_bytes, raw)
            or (cell.lengths_angstrom, cell.angles_degrees)
                != (original_cell.lengths_angstrom, original_cell.angles_degrees)):
        raise ValueError('gas model readout changes the original physical cell')
    if (electronic.augmentation, electronic.original_path, electronic.selected_seed,
            electronic.gas, electronic.host_formal_charge, electronic.host_multiplicity) != (
            augmentation.identity, parent.identity, augmentation.selected_seed,
            gas, parent.qm_formal_charge, parent.spin_multiplicity):
        raise ValueError('gas model readout substitutes its neutral-reactant electronic hypothesis')
    for name in ('mm_atom_indices', 'protein_regions', 'boundaries', 'qm_formal_charge',
            'embedding_method', 'complement_hamiltonian', 'environment_mode'):
        if getattr(path, name) != getattr(parent, name):
            raise ValueError('gas model readout changes the original host partition or operator selection')
    if (path.representation, path.physical_atom_count, path.reactive_site_id, path.qm_atom_indices,
            path.gas, path.gas_atom_indices, path.spin_multiplicity, path.oxygenation_assumption,
            path.electronic_approximation, candidate['electronic_settings']) != (
            model.identity, len(model.atoms), parent.reactive_site_id, parent.qm_atom_indices+gas_indices,
            gas, gas_indices, electronic.total_multiplicity, None, electronic_settings.identity, electronic_settings):
        raise ValueError('gas model readout substitutes its complete gas-QM partition or selected spin')
    if gas == 'O2' and electronic_settings.ks_flavour != 'UKS':
        raise ValueError('gas model readout substitutes the explicit unrestricted oxygen settings')
    remaining = validate_catalytic_path_selection(path, model)
    if candidate['required'] != remaining:
        raise ValueError('gas model readout conceals remaining reactive model requirements')
    electrons = sum(model.atoms[i].atomic_number for i in path.qm_atom_indices)+len(path.boundaries)-path.qm_formal_charge
    return dict(status='COMPLETE_NEUTRAL_GAS_REACTANT_CORRESPONDENCE_CHECKED',
        retained_host_atoms=n, appended_gas_atoms=len(gas_indices), physical_atoms=len(model.atoms),
        physical_qm_atoms=len(path.qm_atom_indices), boundary_caps=len(path.boundaries),
        qm_electrons=electrons, formal_charge=path.qm_formal_charge, spin_multiplicity=path.spin_multiplicity,
        changed_binary64_components=changed, maximum_binary64_change_angstrom=str(maximum),
        maximum_printing_error_angstrom=str(printing), native_calls=0, physical_or_chemical_admission=False,
        required=remaining)
