# SPDX-License-Identifier: MPL-2.0
"""Small exposed ParmEd parameter-append control, never physical evidence.

Invoke with the separately selected ParmEd interpreter, repository path and a
fresh output directory. This avoids installing a native dependency in base.
"""

from io import StringIO
import json
from pathlib import Path
import sys


def main():
    project, output = (Path(value).resolve() for value in sys.argv[1:3])
    split_host = sys.argv[3:] == ['split-host-type']
    if sys.argv[3:] and not split_host:
        raise ValueError('Select only the explicit exposed host-type split control')
    output.mkdir()
    sys.path.insert(0, str(project/'src'))
    import parmed
    from empirical_lawhood.domains.rubisco.rubisco_response.gas_amber_stock import prepare_gas_amber_stock
    from empirical_lawhood.adapters.rubisco.rubisco_response.gas_topology import append_gas_parameter_tables
    from empirical_lawhood.domains.rubisco.rubisco_response.gas_topology_assessment import assess_gas_parameter_tables
    source = parmed.Structure()
    typ = parmed.AtomType('CT', 1, 12.01, 6)
    typ.set_lj_params(0.1094, 1.9080)
    for index in range(4):
        atom = parmed.Atom(name='C'+str(index+1), type='CT', atomic_number=6, mass=12.01,
            charge=(0.1, -0.1, 0.0, 0.0)[index])
        atom.atom_type = typ
        source.add_atom(atom, 'TST', 1)
    bond = parmed.BondType(310, 1.54)
    source.bond_types.append(bond)
    for i in range(3):
        source.bonds.append(parmed.Bond(source.atoms[i], source.atoms[i+1], type=bond))
    angle = parmed.AngleType(40, 109.5)
    source.angle_types.append(angle)
    for i in range(2):
        source.angles.append(parmed.Angle(*source.atoms[i:i+3], type=angle))
    torsion = parmed.DihedralType(0.15, 3, 180, scee=1.2, scnb=2)
    source.dihedral_types.append(torsion)
    source.dihedrals.append(parmed.Dihedral(*source.atoms, type=torsion))
    for rows in (source.bond_types, source.angle_types, source.dihedral_types):
        rows.claim()
    host = parmed.amber.AmberParm.from_structure(source)
    # Retain unused original slots, including inactive zero 1-4 scales.
    for key, value in (('BOND_FORCE_CONSTANT', 123.456), ('BOND_EQUIL_VALUE', 1.234),
            ('DIHEDRAL_FORCE_CONSTANT', 0.0), ('DIHEDRAL_PERIODICITY', 2.0),
            ('DIHEDRAL_PHASE', 0.0), ('SCEE_SCALE_FACTOR', 0.0), ('SCNB_SCALE_FACTOR', 0.0)):
        host.parm_data[key].append(value)
    host.parm_data['POINTERS'][15] += 1
    host.parm_data['POINTERS'][17] += 1
    if split_host:
        # Amber can share one LJ index between distinct chemical type names.
        # ParmEd creates separate indices for these names when combining.
        host.parm_data['AMBER_ATOM_TYPE'][1] = 'CX'
    stream = StringIO()
    parmed.amber.AmberFormat.write_parm(host, stream)
    original = stream.getvalue().encode('ascii')
    (output/'host.prmtop').write_bytes(original)
    fixtures = project/'tests/fixtures/rubisco/amber-templates'
    results = []
    for gas in ('CO2', 'O2'):
        stock = prepare_gas_amber_stock(gas=gas,
            original_prepi_bytes=(fixtures/(gas.lower()+'.prepi')).read_bytes(),
            original_frcmod_bytes=(fixtures/(gas.lower()+'.frcmod')).read_bytes(), existing_atom_types=('CT', 'CX'))
        raw = append_gas_parameter_tables(original_topology_bytes=original, stock=stock)
        (output/(gas.lower()+'.prmtop')).write_bytes(raw)
        (output/(gas.lower()+'.stock.json')).write_bytes(stock.canonical_bytes())
        assessment = assess_gas_parameter_tables(original_topology_bytes=original,
            augmented_topology_bytes=raw, stock=stock)
        assert assessment['original_atoms'] == 4 and not assessment['physical_or_chemical_admission']
        results.append(assessment)
    (output/'result.json').write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps(dict(status='EXPOSED_SOFTWARE_CONTROL_PASSED', results=results)))


if __name__ == '__main__':
    main()
