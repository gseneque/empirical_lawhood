# SPDX-License-Identifier: MPL-2.0
"""Independent raw-table checks for appending one source-selected gas.

No ParmEd or molecular engine is imported. All original atoms, signed bonded
terms, LJ pairs and exclusions survive; new terms must be precisely the gas
stock and Lorentz-Berthelot cross interactions. This is parameter assignment,
without a physical or reactive accuracy claim.
"""

from collections import Counter
from decimal import Decimal as D, localcontext
from hashlib import sha256
from math import isclose, isfinite, pi

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import assigned_census_supported_inactive14, read_prmtop
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preparation import _frcmod_sections, _prepi_rows
from empirical_lawhood.domains.rubisco.rubisco_response.gas_amber_stock import assess_gas_amber_stock


def _pair(sections, first, second):
    n = sections['POINTERS'][1]
    slot = sections['NONBONDED_PARM_INDEX'][first*n+second]-1
    return tuple(sections[key][slot] for key in ('LENNARD_JONES_ACOEF', 'LENNARD_JONES_BCOEF'))


def _terms(sections, census):
    result = {}
    for key, rows in census['indexed_bonded_terms'].items():
        if key.startswith('BONDS'):
            parameters = ('BOND_FORCE_CONSTANT', 'BOND_EQUIL_VALUE')
        elif key.startswith('ANGLES'):
            parameters = ('ANGLE_FORCE_CONSTANT', 'ANGLE_EQUIL_VALUE')
        else:
            parameters = ('DIHEDRAL_FORCE_CONSTANT', 'DIHEDRAL_PERIODICITY', 'DIHEDRAL_PHASE',
                'SCEE_SCALE_FACTOR', 'SCNB_SCALE_FACTOR')
        # Keep signed raw atom offsets: they control impropers and 1-4 terms.
        result[key] = Counter((tuple(row[:-1]), tuple(sections[p][row[-1]-1] for p in parameters)) for row in rows)
    return result


def _exclusions(census):
    result, offset = [], 0
    for count in census['exclusion_counts']:
        values = census['exclusions'][offset:offset+count]
        if len(set(values)) != len(values):
            raise ValueError('gas topology duplicates an exclusion entry')
        result.append(tuple(sorted(values)))
        offset += count
    return tuple(result)


def _close(actual, expected, label):
    # Amber prints eight decimal places in scientific notation. This tolerance
    # covers only new printed coefficients, not a change to any host term.
    actual, expected = float(actual), float(expected)
    if not isfinite(actual) or not isfinite(expected) or not isclose(actual, expected, rel_tol=1e-8, abs_tol=0):
        raise ValueError('gas topology changes source-assigned '+label)


def assess_gas_parameter_tables(*, original_topology_bytes, augmented_topology_bytes, stock):
    """Compare complete original bytes and all appended gas parameter tables."""
    if any(type(raw) is not bytes or not raw for raw in (original_topology_bytes, augmented_topology_bytes)):
        raise ValueError('gas assessment requires complete raw topology bytes')
    original, added = (read_prmtop(raw.decode('ascii')) for raw in (original_topology_bytes, augmented_topology_bytes))
    before, after = (assigned_census_supported_inactive14(value) for value in (original, added))
    assess_gas_amber_stock(stock, existing_atom_types=tuple(set(before['atom_types'])))
    n, gas_count = before['term_census']['atoms'], 3 if stock.gas == 'CO2' else 2
    if after['term_census']['atoms'] != n+gas_count:
        raise ValueError('gas topology changes the complete physical atom count')
    for key in ('atom_names', 'atom_types', 'atomic_numbers', 'masses', 'charges_scaled'):
        if after[key][:n] != before[key]:
            raise ValueError('gas topology changes an original host '+key)
    if (after['residue_names'] != before['residue_names']+(stock.gas,)
            or after['residue_starts'] != before['residue_starts']+(n+1,)):
        raise ValueError('gas topology changes an original residue boundary or gas residue')
    # Complete parameter slots remain exact even if no original term uses one.
    for keys, appended in (
            (('BOND_FORCE_CONSTANT', 'BOND_EQUIL_VALUE'), 1),
            (('ANGLE_FORCE_CONSTANT', 'ANGLE_EQUIL_VALUE'), int(stock.gas == 'CO2')),
            (('DIHEDRAL_FORCE_CONSTANT', 'DIHEDRAL_PERIODICITY', 'DIHEDRAL_PHASE',
                'SCEE_SCALE_FACTOR', 'SCNB_SCALE_FACTOR'), 0)):
        for key in keys:
            if added[key][:len(original[key])] != original[key] or len(added[key]) != len(original[key])+appended:
                raise ValueError('gas topology changes a complete original parameter table or appends an unselected slot')
    if (original['POINTERS'][27] != added['POINTERS'][27]
            or original.get('BOX_DIMENSIONS') != added.get('BOX_DIMENSIONS')):
        raise ValueError('gas topology changes the original periodic cell')
    if original['POINTERS'][27]:
        if (added.get('ATOMS_PER_MOLECULE') != original.get('ATOMS_PER_MOLECULE', ())+(gas_count,)
                or added.get('SOLVENT_POINTERS') != (original['SOLVENT_POINTERS'][0],
                    original['SOLVENT_POINTERS'][1]+1, original['SOLVENT_POINTERS'][2])):
            raise ValueError('gas topology changes the original molecule/solvent partition')

    old_terms, new_terms = _terms(original, before), _terms(added, after)
    gas_terms = {}
    for key, terms in new_terms.items():
        host, gas = Counter(), Counter()
        for (indices, parameters), count in terms.items():
            atoms = tuple(abs(i)//3 for i in indices)
            if all(i < n for i in atoms):
                host[indices, parameters] += count
            elif all(i >= n for i in atoms):
                gas[indices, parameters] += count
            else:
                raise ValueError('gas topology adds a bonded gas-host interaction')
        if host != old_terms[key]:
            raise ValueError('gas topology changes an original signed bonded term or parameter')
        gas_terms[key] = gas
    excluded_before, excluded_after = _exclusions(before), _exclusions(after)
    if excluded_after[:n] != excluded_before:
        raise ValueError('gas topology changes an original host exclusion')
    expected_exclusions = tuple(tuple(range(n+i+2, n+gas_count+1)) or (0,) for i in range(gas_count))
    if excluded_after[n:] != expected_exclusions:
        raise ValueError('gas topology changes the complete intragas exclusions')

    # Correspondence uses every host atom, not an assumed unchanged type ordinal.
    mapping = set(zip((i-1 for i in original['ATOM_TYPE_INDEX']),
        (i-1 for i in added['ATOM_TYPE_INDEX'][:n]), strict=True))
    if {old for old, _ in mapping} != set(range(original['POINTERS'][1])):
        raise ValueError('gas topology omits an original LJ type')
    for first, mapped_first in sorted(mapping):
        for second, mapped_second in sorted(mapping):
            if _pair(original, first, second) != _pair(added, mapped_first, mapped_second):
                raise ValueError('gas topology changes an original host LJ coefficient')

    rows = tuple(tuple(t.group() for t in tokens) for _, tokens in _prepi_rows(stock.scoped_prepi_utf8))
    gas_atoms = tuple(row for row in rows if row[2] != 'DU')
    sections = _frcmod_sections(stock.scoped_frcmod_utf8)
    mass = {row.split()[0]: D(row.split()[1]) for row in sections['MASS']}
    nonbonded = {row.split()[0]: tuple(D(v) for v in row.split()[1:3]) for row in sections['NONBON']}
    radii = {}
    for i, row in enumerate(gas_atoms, n):
        _, name, typ = row[:3]
        if (after['atom_names'][i], after['atom_types'][i], after['atomic_numbers'][i], after['masses'][i]) != (
                name, typ, 6 if name == 'C1' else 8, mass[typ]):
            raise ValueError('gas topology changes a complete source gas atom')
        with localcontext() as context:
            context.prec = 60
            expected_charge = D(row[10])*D('18.2223')
        _close(after['charges_scaled'][i], expected_charge, 'gas charge')
        # Rmin/2 and epsilon in the source's Angstrom/kcal convention.
        rmin_half, epsilon = nonbonded[typ]
        native_type = added['ATOM_TYPE_INDEX'][i]-1
        selected = float(rmin_half), float(epsilon)
        if radii.setdefault(native_type, selected) != selected or native_type in {new for _, new in mapping}:
            raise ValueError('gas topology merges a new gas type with an original host type')
    for old, new in sorted(mapping):
        a, b = (float(v) for v in _pair(original, old, old))
        if not a or not b:
            if a or b:
                raise ValueError('gas topology cannot represent a one-sided original LJ type')
            selected = 0.5, 0.0
        else:
            selected = (2*a/b)**(1/6)/2, b*b/(4*a)
        if radii.setdefault(new, selected) != selected:
            raise ValueError('gas topology merges different original LJ diagonals')
    if set(radii) != set(range(added['POINTERS'][1])):
        raise ValueError('gas topology adds unselected parameter types')
    gas_types = {added['ATOM_TYPE_INDEX'][i]-1 for i in range(n, n+gas_count)}
    cross_count = 0
    for first, (radius1, epsilon1) in radii.items():
        for second, (radius2, epsilon2) in radii.items():
            if first not in gas_types and second not in gas_types:
                continue
            minimum = radius1+radius2
            depth = (epsilon1*epsilon2)**0.5
            a, b = _pair(added, first, second)
            _close(a, depth*minimum**12, 'new LJ A coefficient')
            _close(b, 2*depth*minimum**6, 'new LJ B coefficient')
            cross_count += 1

    source_bonds = {}
    for row in sections['BOND']:
        types = tuple(t.strip() for t in row[:5].split('-'))
        values = tuple(D(v) for v in row[5:].split()[:2])
        source_bonds[types] = source_bonds[types[::-1]] = values
    ordinals = {int(row[0]): n+i for i, row in enumerate(gas_atoms)}
    expected_bonds = Counter()
    for row in gas_atoms:
        parent = int(row[4])
        if parent in ordinals:
            first, second = ordinals[parent], ordinals[int(row[0])]
            expected_bonds[(3*first, 3*second), source_bonds[after['atom_types'][first], after['atom_types'][second]]] += 1
    if gas_terms['BONDS_WITHOUT_HYDROGEN'] != expected_bonds:
        raise ValueError('gas topology changes a source intragas bond')
    expected_angle_count = int(stock.gas == 'CO2')
    if sum(gas_terms['ANGLES_WITHOUT_HYDROGEN'].values()) != expected_angle_count:
        raise ValueError('gas topology changes the source angle count')
    if expected_angle_count:
        ((indices, values), count), = gas_terms['ANGLES_WITHOUT_HYDROGEN'].items()
        source = sections['ANGLE'][0][8:].split()
        if indices != tuple(3*i for i in range(n, n+3)) or count != 1 or values[0] != D(source[0]):
            raise ValueError('gas topology changes the source gas angle')
        _close(values[1], float(source[1])*pi/180, 'gas angle equilibrium')
    if any(gas_terms[key] for key in gas_terms if key not in ('BONDS_WITHOUT_HYDROGEN', 'ANGLES_WITHOUT_HYDROGEN')):
        raise ValueError('gas topology adds an unselected gas hydrogen or torsion term')
    return dict(status='COMPLETE_GAS_PARAMETER_ASSIGNMENT_CHECKED',
        original_topology_sha256=sha256(original_topology_bytes).hexdigest(),
        augmented_topology_sha256=sha256(augmented_topology_bytes).hexdigest(),
        original_atoms=n, appended_atoms=gas_count, original_signed_bonded_terms=before['term_census'],
        original_lj_ordered_pairs=len({old for old, _ in mapping})**2, new_lj_ordered_pairs=cross_count,
        original_exclusion_rows=n, gas_exclusion_rows=gas_count,
        original_host_parameters='EXACT_PRINTED_VALUES_PRESERVED',
        new_parameter_printing_relative_tolerance='1e-8', force_evaluations=0,
        physical_or_chemical_admission=False)


def _coordinate_assignment(*, result, augmented_coordinate_bytes, host_prefix, original_gas):
    """Check an exact retained extension against separately selected positions."""
    import numpy as np

    n = result.original_atom_count
    if (type(augmented_coordinate_bytes) is not bytes or type(host_prefix) is not bytes
            or len(host_prefix) != n*24
            or result.expanded_seed_coordinate_sha256 != sha256(host_prefix).hexdigest()
            or result.augmented_coordinates.object_fingerprint != sha256(augmented_coordinate_bytes).hexdigest()
            or len(augmented_coordinate_bytes) != (n+len(result.gas_atom_correspondence))*24
            or augmented_coordinate_bytes[:len(host_prefix)] != host_prefix):
        raise ValueError('gas readout changes its retained coordinate denominator or host prefix')
    points = np.frombuffer(augmented_coordinate_bytes, dtype='<f8').reshape((-1, 3))
    if not np.isfinite(points).all():
        raise ValueError('gas readout contains a nonfinite coordinate')
    expected_names = ('O1', 'C1', 'O2') if result.stock.gas == 'CO2' else ('O1', 'O2')
    expected_ordinals = (63, 57, 64) if result.stock.gas == 'CO2' else (162, 168)
    expected_map = tuple((name, ordinal, n+i)
        for i, (name, ordinal) in enumerate(zip(expected_names, expected_ordinals, strict=True)))
    if set(original_gas) != set(expected_ordinals) or result.gas_atom_correspondence != expected_map or any(
            not np.array_equal(points[index], np.asarray(original_gas[ordinal], dtype='<f8'))
            for _, ordinal, index in expected_map):
        raise ValueError('gas readout changes a source gas atom or its selected position')
    return len(expected_map)


def validate_parameter_return_binding(*, source, product, stock, original_topology_bytes, augmented_topology_bytes):
    """Join exact raw bytes to the previously authenticated native unit product."""
    from empirical_lawhood.domains.rubisco.rubisco_response.gas_parameter_operation import GasParameterUnitProduct
    from empirical_lawhood.domains.rubisco.rubisco_response.gas_parameter_records import GasParameterSource
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
    exact(source, GasParameterSource)
    exact(product, GasParameterUnitProduct)
    files = {row.relative_path: row for row in product.returned.files.files}
    file = files.get(product.definition.subwork_id+'/gas.prmtop')
    if (type(augmented_topology_bytes) is not bytes or type(original_topology_bytes) is not bytes
            or source.topology_ascii.encode('ascii') != original_topology_bytes
            or source.identity != product.returned.source or product.returned.gas != stock.gas
            or stock not in source.stocks or product.returned.error is not None
            or product.assessment_json is None or product.assessment_error is not None
            or file is None or (file.byte_count, file.sha256)
                != (len(augmented_topology_bytes), sha256(augmented_topology_bytes).hexdigest())):
        raise ValueError('gas candidate substitutes its original assessed native parameter return')


def assess_gas_topology_augmentation(*, result, augmented_topology_bytes, augmented_coordinate_bytes,
        representation, preparation, seed, cell, encounter, source_projection, stock,
        coordinate_bytes, original_topology_bytes, parameter_source, parameter_product):
    """Read a retained candidate against every original operand, without ParmEd.

    Validate all source-to-PREP positions and the unchanged full host coordinate
    prefix as well as the complete raw parameter tables. No producer replay,
    energy/geometry qualification or reactive-state admission occurs here.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.carbon_encounter import assess_carbon_encounter
    from empirical_lawhood.adapters.rubisco.rubisco_response.gas_topology import GasTopologyAugmentation
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import validate_amber_atom_correspondence
    from empirical_lawhood.domains.rubisco.rubisco_response.oxygen_encounter import assess_oxygen_encounter, selected_gas_free_target

    exact(result, GasTopologyAugmentation)
    validate_parameter_return_binding(source=parameter_source, product=parameter_product, stock=stock,
        original_topology_bytes=original_topology_bytes, augmented_topology_bytes=augmented_topology_bytes)
    if result.native_parameter_product != parameter_product.identity:
        raise ValueError('gas readout substitutes its original native parameter product')
    site, _, target = selected_gas_free_target(representation=representation,
        preparation=preparation, seed=seed, coordinate_bytes=coordinate_bytes, cell=cell)
    assess_encounter = assess_carbon_encounter if stock.gas == 'CO2' else assess_oxygen_encounter
    assess_encounter(result=encounter, source=source_projection, representation=representation,
        preparation=preparation, seed=seed, coordinate_bytes=coordinate_bytes, cell=cell)
    validate_amber_atom_correspondence(representation, original_topology_bytes)
    prefix = target['environment'].astype('<f8').tobytes()
    if (result.original_representation, result.preparation, result.selected_seed, result.selected_site,
            result.encounter, result.stock, result.original_cell, result.original_topology,
            result.original_coordinate_sha256, result.expanded_seed_coordinate_sha256,
            result.original_atom_count) != (
            representation.identity, preparation.identity, seed.identity, site.identity, encounter.identity,
            stock, cell.identity, representation.raw_topology, sha256(coordinate_bytes).hexdigest(),
            sha256(prefix).hexdigest(), len(representation.atoms)):
        raise ValueError('gas readout substitutes the complete original target or source selection')
    if any(type(raw) is not bytes for raw in (augmented_topology_bytes, augmented_coordinate_bytes)):
        raise ValueError('gas readout requires original retained byte payloads')
    if result.augmented_topology.object_fingerprint != sha256(augmented_topology_bytes).hexdigest():
        raise ValueError('gas readout changes its retained topology tables')
    original_gas = dict(zip(encounter.source_gas_indices_1based, encounter.gas_coordinates_angstrom, strict=True))
    appended = _coordinate_assignment(result=result, augmented_coordinate_bytes=augmented_coordinate_bytes,
        host_prefix=prefix, original_gas=original_gas)
    parameters = assess_gas_parameter_tables(original_topology_bytes=original_topology_bytes,
        augmented_topology_bytes=augmented_topology_bytes, stock=stock)
    return dict(status='COMPLETE_GAS_TOPOLOGY_AND_COORDINATE_ASSIGNMENT_CHECKED',
        parameters=parameters, retained_host_coordinates=result.original_atom_count,
        appended_coordinates=appended, host_coordinate_values='EXACT_BINARY64_PREFIX_PRESERVED',
        force_evaluations=0, physical_or_chemical_admission=False,
        required=('RELAXED_TARGET_AND_GAS_ENCOUNTER', 'REACTIVE_QM_REGION_AND_COMPLETE_MM_EXCLUSIONS',
            'TOTAL_CHARGE_SPIN_AND_PROTON_ALLOCATION', 'COUPLED_FORCE_AND_GEOMETRY_ASSESSMENT',
            'BULK_ACCESS_TRANSMISSION_AND_PRODUCTIVE_COMMITMENT'))
