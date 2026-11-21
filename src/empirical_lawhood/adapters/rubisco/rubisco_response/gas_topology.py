# SPDX-License-Identifier: MPL-2.0
"""Append source-selected gas parameters without changing a complete host.

The explicit transformation imports ParmEd only when invoked. It builds no
provider, force Context or trajectory. Independent raw-table assessment must
accept the result before it can become a candidate molecular input.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from io import StringIO
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import assigned_census_supported_inactive14, read_prmtop
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preparation import _prepi_rows
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256
from empirical_lawhood.domains.rubisco.rubisco_response.gas_amber_stock import GasAmberStock, assess_gas_amber_stock
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


PARMED_VERSION = '4.3.1'
SCOPE = 'SOURCE_BOUND_GAS_TOPOLOGY_TRANSFORMATION_NOT_CHEMICAL_OR_ENSEMBLE_ADMISSION'


def gas_template_atoms(stock):
    """Retain the original PREP atom order, names, charges and parent edges."""
    exact(stock, GasAmberStock)
    rows = tuple(tuple(token.group() for token in tokens)
        for _, tokens in _prepi_rows(stock.scoped_prepi_utf8))
    atoms = tuple((int(r[0]), r[1], r[2], int(r[4]), Decimal(r[10]))
        for r in rows if r[2] != 'DU')
    expected = ('O1', 'C1', 'O2') if stock.gas == 'CO2' else ('O1', 'O2')
    if (tuple(r[1] for r in atoms) != expected
            or tuple(r[0] for r in atoms) != tuple(range(4, 4+len(expected)))):
        raise ValueError('gas topology changes the original PREP atom order')
    return atoms


def _source_pair(sections, first, second):
    count = sections['POINTERS'][1]
    slot = sections['NONBONDED_PARM_INDEX'][first*count+second]-1
    return tuple(sections[key][slot] for key in ('LENNARD_JONES_ACOEF', 'LENNARD_JONES_BCOEF'))


def _retain_host_lj_tables(original, combined, original_count):
    """Preserve printed host coefficients after ParmEd recomputes mixing.

    ParmEd's supported combination recalculates the complete LJ table. Restore
    every original host pair from its raw table, using the actual old/new type
    correspondence. A merge of unequal source pairs is refused.
    """
    mapping = set(zip((i-1 for i in original['ATOM_TYPE_INDEX']),
        (i-1 for i in combined.parm_data['ATOM_TYPE_INDEX'][:original_count]), strict=True))
    if {old for old, _ in mapping} != set(range(original['POINTERS'][1])):
        raise ValueError('gas append cannot discard an unused original host LJ type')
    count = combined.parm_data['POINTERS'][1]
    written = {}
    for first, mapped_first in sorted(mapping):
        for second, mapped_second in sorted(mapping):
            slot = combined.parm_data['NONBONDED_PARM_INDEX'][mapped_first*count+mapped_second]-1
            values = _source_pair(original, first, second)
            if written.setdefault(slot, values) != values:
                raise ValueError('gas append merges unequal original host LJ pairs')
            for key, value in zip(('LENNARD_JONES_ACOEF', 'LENNARD_JONES_BCOEF'), values, strict=True):
                combined.parm_data[key][slot] = float(value)


def _retain_host_bonded_tables(original, combined, original_count):
    """Copy every original parameter slot, including unused/inactive slots.

    The native combination prunes unused types. The serialized successor
    retains the original tables and signed rows verbatim in value/order and
    appends only the native gas terms, with their parameter indices rebased.
    """
    data = combined.parm_data
    classes = (
        (15, 3, ('BOND_FORCE_CONSTANT', 'BOND_EQUIL_VALUE'),
            ('BONDS_INC_HYDROGEN', 'BONDS_WITHOUT_HYDROGEN')),
        (16, 4, ('ANGLE_FORCE_CONSTANT', 'ANGLE_EQUIL_VALUE'),
            ('ANGLES_INC_HYDROGEN', 'ANGLES_WITHOUT_HYDROGEN')),
        (17, 5, ('DIHEDRAL_FORCE_CONSTANT', 'DIHEDRAL_PERIODICITY', 'DIHEDRAL_PHASE',
            'SCEE_SCALE_FACTOR', 'SCNB_SCALE_FACTOR'),
            ('DIHEDRALS_INC_HYDROGEN', 'DIHEDRALS_WITHOUT_HYDROGEN')),
    )
    for pointer, width, parameters, row_names in classes:
        extra, rows = {}, {}
        original_length = len(original[parameters[0]])
        for key in row_names:
            appended = []
            values = data[key]
            for start in range(0, len(values), width):
                row = values[start:start+width]
                atoms = tuple(abs(i)//3 for i in row[:-1])
                if all(i < original_count for i in atoms):
                    continue
                if not all(i >= original_count for i in atoms):
                    raise ValueError('gas append creates a mixed bonded term')
                selected = row[-1]-1
                if selected not in extra:
                    extra[selected] = tuple(data[p][selected] for p in parameters)
                appended.extend((*row[:-1], original_length+tuple(extra).index(selected)+1))
            rows[key] = list(original[key])+appended
        for column, name in enumerate(parameters):
            data[name] = [float(v) for v in original[name]]+[values[column] for values in extra.values()]
        data.update(rows)
        data['POINTERS'][pointer] = original_length+len(extra)


def append_gas_parameter_tables(*, original_topology_bytes, stock):
    """Transform complete raw parameter tables with the selected ParmEd API.

    This function performs no I/O, energy evaluation or scientific admission.
    Retain its raw return before invoking the independent complete-table
    assessor. The selected caller owns source custody, actual native-library
    contact accounting and numerical provenance.
    """
    if type(original_topology_bytes) is not bytes or not original_topology_bytes:
        raise ValueError('gas append requires complete original Amber bytes')
    original = read_prmtop(original_topology_bytes.decode('ascii'))
    census = assigned_census_supported_inactive14(original)
    assess_gas_amber_stock(stock, existing_atom_types=tuple(set(census['atom_types'])))

    # The base environment and static discovery do not import this dependency.
    import parmed
    if parmed.__version__ != PARMED_VERSION:
        raise ValueError('gas append requires the separately selected ParmEd 4.3.1 environment')
    parameters = parmed.amber.AmberParameterSet(StringIO(stock.scoped_frcmod_utf8))
    gas = parmed.Structure()
    by_source = {}
    for source_index, name, typ, _, charge in gas_template_atoms(stock):
        atom_type = parameters.atom_types_str[typ]
        number = 6 if name == 'C1' else 8
        if atom_type.atomic_number != number:
            raise ValueError('gas stock changes a selected native element')
        atom = parmed.Atom(name=name, type=typ, atomic_number=number,
            mass=atom_type.mass, charge=float(charge))
        atom.atom_type = atom_type
        gas.add_atom(atom, stock.gas, 1)
        by_source[source_index] = atom
    for source_index, _, _, parent, _ in gas_template_atoms(stock):
        if parent in by_source:
            first, second = by_source[parent], by_source[source_index]
            kind = parameters.bond_types[first.type, second.type]
            if kind not in gas.bond_types:
                gas.bond_types.append(kind)
            gas.bonds.append(parmed.Bond(first, second, type=kind))
    if stock.gas == 'CO2':
        kind = parameters.angle_types[tuple(a.type for a in gas.atoms)]
        gas.angle_types.append(kind)
        gas.angles.append(parmed.Angle(*gas.atoms, type=kind))
    gas.bond_types.claim()
    gas.angle_types.claim()

    host = parmed.amber.AmberParm(StringIO(original_topology_bytes.decode('ascii')))
    original_count = len(host.atoms)
    if original_count != census['term_census']['atoms'] or host.combining_rule != 'lorentz':
        raise ValueError('gas append requires the complete original Lorentz-Berthelot host')
    host += gas
    _retain_host_lj_tables(original, host, original_count)
    _retain_host_bonded_tables(original, host, original_count)
    output = StringIO()
    # AmberParm.write_parm would prune the restored unused slots again.
    # The raw format writer serializes the explicitly selected tables.
    parmed.amber.AmberFormat.write_parm(host, output)
    raw = output.getvalue().encode('ascii')
    return raw


@dataclass(frozen=True, slots=True)
class GasTopologyAugmentation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-topology-augmentation'
    original_representation: ObjectIdentity
    preparation: ObjectIdentity
    selected_seed: ObjectIdentity
    selected_site: ObjectIdentity
    encounter: ObjectIdentity
    stock: GasAmberStock
    original_cell: ObjectIdentity
    original_topology: ObjectIdentity
    original_coordinate_sha256: str
    expanded_seed_coordinate_sha256: str
    augmented_topology: ObjectIdentity
    augmented_coordinates: ObjectIdentity
    original_atom_count: int
    # PREP name, original source geometry ordinal, appended physical index.
    gas_atom_correspondence: tuple[tuple[str, int, int], ...]
    native_parameter_product: ObjectIdentity
    scope: str = SCOPE

    def __post_init__(self):
        for value in (self.original_representation, self.preparation, self.selected_seed,
                self.selected_site, self.encounter, self.original_cell, self.original_topology,
                self.augmented_topology, self.augmented_coordinates, self.native_parameter_product):
            exact(value, ObjectIdentity)
        exact(self.stock, GasAmberStock)
        for value in (self.original_coordinate_sha256, self.expanded_seed_coordinate_sha256):
            validate_sha256(value)
        if type(self.original_atom_count) is not int or self.original_atom_count <= 0 or self.scope != SCOPE:
            raise ValueError('gas augmentation changes its original denominator or interpretation')
        expected = (('O1', 63), ('C1', 57), ('O2', 64)) if self.stock.gas == 'CO2' else (('O1', 162), ('O2', 168))
        if self.gas_atom_correspondence != tuple((name, source, self.original_atom_count+i)
                for i, (name, source) in enumerate(expected)):
            raise ValueError('gas augmentation changes the source-to-PREP atom correspondence')
        if (self.native_parameter_product.object_schema != 'empirical-lawhood/rubisco-response/gas-parameter-unit-product'
                or self.native_parameter_product.object_version != '1.0.0'):
            raise ValueError('gas augmentation requires its original native parameter product')

    @property
    def identity(self):
        return ObjectIdentity.from_record('gas-topology.'+self.fingerprint(), self)


def prepare_gas_topology_augmentation(*, representation, preparation, seed, cell,
        encounter, source_projection, stock, coordinate_bytes, original_topology_bytes,
        augmented_topology_bytes, parameter_source, parameter_product):
    """Bind an original native return to its complete target without native work."""
    from empirical_lawhood.domains.rubisco.rubisco_response.carbon_encounter import CarbonEncounterGeometry, assess_carbon_encounter
    from empirical_lawhood.domains.rubisco.rubisco_response.oxygen_encounter import OxygenEncounterGeometry, assess_oxygen_encounter, selected_gas_free_target
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import validate_amber_atom_correspondence
    from empirical_lawhood.domains.rubisco.rubisco_response.gas_topology_assessment import validate_parameter_return_binding
    import numpy as np

    exact(stock, GasAmberStock)
    kind = CarbonEncounterGeometry if stock.gas == 'CO2' else OxygenEncounterGeometry
    exact(encounter, kind)
    site, _, target = selected_gas_free_target(representation=representation,
        preparation=preparation, seed=seed, coordinate_bytes=coordinate_bytes, cell=cell)
    environment = target['environment']
    assess_encounter = assess_carbon_encounter if stock.gas == 'CO2' else assess_oxygen_encounter
    assess_encounter(result=encounter, source=source_projection, representation=representation,
        preparation=preparation, seed=seed, coordinate_bytes=coordinate_bytes, cell=cell)
    if (encounter.representation, encounter.preparation, encounter.selected_seed, encounter.selected_site,
            encounter.cell, encounter.original_coordinate_sha256, encounter.expanded_seed_coordinate_sha256,
            encounter.retained_physical_atom_count) != (
            representation.identity, preparation.identity, seed.identity, site.identity, cell.identity,
            sha256(coordinate_bytes).hexdigest(), sha256(environment.astype('<f8').tobytes()).hexdigest(), len(environment)):
        raise ValueError('gas augmentation substitutes its selected original target or encounter')
    validate_amber_atom_correspondence(representation, original_topology_bytes)
    validate_parameter_return_binding(source=parameter_source, product=parameter_product, stock=stock,
        original_topology_bytes=original_topology_bytes, augmented_topology_bytes=augmented_topology_bytes)
    raw = augmented_topology_bytes
    points = dict(zip(encounter.source_gas_indices_1based, encounter.gas_coordinates_angstrom, strict=True))
    gas_order = (('O1', 63), ('C1', 57), ('O2', 64)) if stock.gas == 'CO2' else (('O1', 162), ('O2', 168))
    joined = np.concatenate((environment, np.asarray([points[i] for _, i in gas_order], dtype='<f8'))).astype('<f8').tobytes()
    original_expanded = environment.astype('<f8').tobytes()
    if joined[:len(original_expanded)] != original_expanded:
        raise ValueError('gas augmentation changes a host coordinate')
    def raw_identity(kind, payload):
        digest = sha256(payload).hexdigest()
        schema = 'native-amber-topology-bytes' if kind == 'topology' else 'native-cartesian-f64-bytes'
        return ObjectIdentity('native.gas-amber.'+kind+'.'+digest,
            'empirical-lawhood/rubisco-response/'+schema, '1.0.0', digest)
    result = GasTopologyAugmentation(representation.identity, preparation.identity, seed.identity,
        site.identity, encounter.identity, stock, cell.identity, representation.raw_topology,
        encounter.original_coordinate_sha256, encounter.expanded_seed_coordinate_sha256,
        raw_identity('topology', raw), raw_identity('coordinates', joined), len(environment),
        tuple((name, source, len(environment)+i) for i, (name, source) in enumerate(gas_order)),
        parameter_product.identity)
    return dict(augmentation=result, topology_bytes=raw, coordinate_bytes=joined,
        parameter_assessment=None, native_parameter_product=parameter_product.identity,
        new_native_calls=0,
        force_evaluations=0, geometry_or_electronic_admission='UNEVALUABLE')
