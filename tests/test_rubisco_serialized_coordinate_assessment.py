# SPDX-License-Identifier: MPL-2.0
"""Composed exposed producer/readback checks; no native or molecular evidence."""

import ast
from copy import deepcopy
from decimal import Decimal as D
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import (
    amber_parameters as parameters,
    parameter_audit as producer,
    preparation_integrity as historical,
    physical_preparation_geometry as geometry,
    serialized_coordinate_assessment as selected,
)
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_rubisco_coordinate_origin_validation import exposed
from tests.test_rubisco_preamber_geometry_integrity import ter
from tests.test_rubisco_physical_preparation_geometry import stock
from tests.test_rubisco_preparation_integrity import amber_text


def serialized_exposed():
    args = exposed()
    lines, serial = [], 0
    original = args[3].splitlines()
    for index, line in enumerate(original):
        serial += 1
        lines.append(line[:6] + f"{serial:5d}" + line[11:] + "\n")
        if index == len(original) - 1 or line[21] != original[index + 1][21]:
            serial += 1
            lines.append(ter(serial, line[21], int(line[22:26]), line[17:20]))
    args[3] = "".join(lines)
    return args


def structure(census):
    residues, atoms = [], []
    for index, (name, atom_name, number) in enumerate(zip(census['residue_names'],
            census['atom_names'], census['atomic_numbers'], strict=True)):
        residue = SimpleNamespace(idx=index, name=name, atoms=[])
        atom = SimpleNamespace(idx=index, name=atom_name, atomic_number=number, residue=residue)
        residue.atoms.append(atom)
        residues.append(residue)
        atoms.append(atom)
    return SimpleNamespace(residues=residues, atoms=atoms, bonds=[])


def topology(census):
    rows = stock()
    n = census['term_census']['atoms']
    rows['POINTERS'][0] = rows['POINTERS'][11] = n
    for name, values in (('ATOM_NAME', census['atom_names']), ('ATOMIC_NUMBER', census['atomic_numbers']),
            ('RESIDUE_LABEL', census['residue_names']), ('RESIDUE_POINTER', census['residue_starts'])):
        rows[name] = list(values)
    rows.update(AMBER_ATOM_TYPE=['C'] * n, MASS=[D(12)] * n, CHARGE=[D(0)] * n,
        ATOM_TYPE_INDEX=[1] * n, BOX_DIMENSIONS=[D(90), D(2000), D(2000), D(2000)],
        SCEE_SCALE_FACTOR=[D('0E-8')], SCNB_SCALE_FACTOR=[D('0E-8')])
    rows['NUMBER_EXCLUDED_ATOMS'].extend([0] * (n - 4))
    return rows


@pytest.mark.parametrize('entry_name', ('native', 'durable_native_entry', 'geometry_reuse_native_entry'))
def test_actual_producer_call_serializes_permuted_origins_for_independent_reader(tmp_path, entry_name):
    args = serialized_exposed()
    directory = tmp_path
    (directory / 'complete-heavy.pdb').write_text(args[3])
    (directory / 'model.inpcrd').write_text(args[4])
    source = Path(producer.__file__).with_name(entry_name + '.py')
    tree = ast.parse(source.read_text())
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name)
            and target.value.id == 'origin' and isinstance(target.slice, ast.Constant)
            and target.slice.value == 'amber_realization' for target in node.targets)]
    assert len(calls) == 1
    # Execute the actual production call with complete exposed native-shaped
    # operands, then serialize and independently consume its actual result.
    namespace = dict(directory=directory, structure=structure(args[1]), origin=deepcopy(args[2]),
        realized_atom_origins=producer.realized_atom_origins,
        realized_atom_origins_from_coordinates=producer.realized_atom_origins_from_coordinates)
    exec(compile(ast.Module(body=calls, type_ignores=[]), str(source), 'exec'), namespace)
    raw = json.dumps(namespace['origin'], sort_keys=True, separators=(',', ':')) + '\n'
    (directory / 'origin.json').write_text(raw)
    args[2] = json.loads((directory / 'origin.json').read_bytes())
    result = selected.validate_origins_from_coordinates(*args)
    assert result.method == selected.ORIGIN_METHOD != historical.COORDINATE_ORIGIN_METHOD
    assert result.complete_heavy_atom_count == 5050
    assert result.chemical_residue_map == (('Z', 1, 5049), ('Z', 2, 5048))
    assert (directory / 'complete-heavy.pdb').read_text() == args[3]
    with pytest.raises(ValueError, match='denominator'):
        historical.validate_origins_from_coordinates(*args)


def test_complete_serialized_permutation_and_inactive_scales_compose_without_global_changes():
    args = serialized_exposed()
    raw = amber_text(topology(args[1]))
    before = (historical.read_heavy_pdb, geometry.read_heavy_pdb, geometry.assigned_census)
    args[1] = parameters.assigned_census_supported_inactive14(parameters.read_prmtop(raw))
    proof = selected.validate_origins_from_coordinates(*args)
    result = selected.diagnose_geometry_supported_inactive14(raw, args[4], args[3], args[2])
    assert proof.complete_heavy_atom_count == result.diagnostic.heavy_atom_count == 5050
    assert result.method == selected.GEOMETRY_METHOD
    assert sum(count for _, count in result.diagnostic.pair_counts) == 5050 * 5049 // 2
    assert result.diagnostic.geometry_adequacy is A.UNEVALUABLE
    assert (historical.read_heavy_pdb, geometry.read_heavy_pdb, geometry.assigned_census) == before
    with pytest.raises(ValueError, match='denominator'):
        geometry.diagnose_geometry_supported_inactive14(raw, args[4], args[3], args[2])


@pytest.mark.parametrize('mutation', ('unjustified-gap', 'wrong-ter', 'false-map', 'active-zero'))
def test_composed_reader_preserves_serial_origin_and_scale_refusals(mutation):
    args = serialized_exposed()
    rows = topology(args[1])
    if mutation == 'unjustified-gap':
        args[3] = args[3].replace('TER', 'REM', 1)
    elif mutation == 'wrong-ter':
        args[3] = args[3].replace('TER     494      ALA A 493', 'TER     494      ALA B 493', 1)
    elif mutation == 'false-map':
        args[2]['amber_realization']['chemical_residue_map'][0]['amber_residue_index'] = 5048
    else:
        rows['DIHEDRALS_WITHOUT_HYDROGEN'] = [0, 3, 6, 9, 1]
    with pytest.raises(ValueError):
        args[1] = parameters.assigned_census_supported_inactive14(parameters.read_prmtop(amber_text(rows)))
        selected.validate_origins_from_coordinates(*args)
