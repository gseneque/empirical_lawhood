# SPDX-License-Identifier: MPL-2.0
"""Cold and adverse export/uncertainty controls; no scientific acquisition."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_structure import contracts as c, independent_assessment as independent
from tests.test_rubisco_structure_independent import exposed  # noqa: F401


@pytest.fixture(scope="module")
def source_spelled(exposed):  # noqa: F811 - the imported fixture is registered by pytest
    source, _, products = exposed
    members = {row.filename:row.raw_utf8 for row in source.source_members}
    atoms = tuple(atom for pdb in ("1BWV", "3ZXW") for atom in independent.original_assembly(pdb, members[pdb.lower()+".cif"])[0])
    return source, replace(products["inventory"], atoms=atoms), products["coordinates"]


@pytest.mark.parametrize("category,item,reason", [
    ("_entity_poly", "entity_id", "polymer map"),
    ("_struct_asym", "entity_id", "asymmetry map"),
    ("_pdbx_struct_mod_residue", "parent_comp_id", "activation/modification map"),
    ("_pdbx_poly_seq_scheme", "auth_seq_num", "residue map"),
])
def test_rehashed_export_cannot_substitute_source_metadata(source_spelled, category, item, reason):
    source, inventory, coordinates = source_spelled
    name, _, text = coordinates.files[0]
    original = category+"."+item
    assert original in text
    text = text.replace(original, category+".changed_item", 1)
    changed = replace(coordinates, files=((name, sha256(text.encode()).hexdigest(), text), coordinates.files[1]))
    with pytest.raises(ValueError, match=reason):
        independent.validate_coordinate_export(source, inventory, changed)


def test_shell_boundary_is_unknown_and_missing_query_never_creates_distances():
    residues = tuple((i, str(i+17), ".", "ILE" if i == 95 else "ALA", ("CA",) if i == 95 else ()) for i in range(1,139))
    chain = c.AssemblyChain("1BWV", "1", "A", "A", "1", "A"*94+"I"+"A"*43, residues)
    auxiliary = c.AssemblyChain("1BWV", "1", "B", "B", "2", "A", ((1,"1",".","ALA",("CA",)),))
    query = c.AssemblyAtom("1BWV", "1", "1", "A", "A", "1", "95", "112", ".", "ILE", "CA", "C", ".", D(1), (D(0),D(0),D(0)))
    other = c.AssemblyAtom("1BWV", "1", "2", "B", "B", "2", "1", "1", ".", "ALA", "CA", "C", ".", D(1), (D(3),D(0),D(0)))
    view = c.SiteNeighborhood(chain.chain_id, 95, "112", "ILE", 1, tuple((radius,(other.chain_id+".2",)) for radius in (D(3),D(5),D(8))), ((auxiliary.chain_id,D(3)),), ())
    inventory = SimpleNamespace(atoms=(query,other), chains=(chain,auxiliary), neighborhoods=(view,))
    maximum, ambiguities = independent._check_neighborhoods(inventory,(D(3),D(5),D(8)))
    assert maximum == 0 and ambiguities == ((chain.chain_id, other.chain_id+".2", D(3)),)
    # Either binary64 spelling at an exact boundary is uncertainty, not a
    # fabricated geometrical falsification or newly admitted shell member.
    inventory.neighborhoods = (replace(view, shells=((D(3),()), *view.shells[1:])),)
    assert independent._check_neighborhoods(inventory,(D(3),D(5),D(8)))[1] == ambiguities
    inventory.atoms = (replace(query, occupancy=D(0)),other)
    inventory.neighborhoods = (replace(view, query_atom_count=0, shells=tuple((r,()) for r in (D(3),D(5),D(8))), other_chain_minima_angstrom=((auxiliary.chain_id,None),)),)
    assert independent._check_neighborhoods(inventory,(D(3),D(5),D(8))) == (D(0),())


def test_independent_assessor_import_is_cold_and_has_no_producer_or_native_dependency():
    subprocess.run([sys.executable,"-c", """
import importlib.abc, sys
class Refuse(importlib.abc.MetaPathFinder):
 def find_spec(self, name, path=None, target=None):
  if name.split('.')[0] in ('numpy','openmm','pdbfixer','parmed','pybamm') or name.endswith('rubisco_insilico_structure.science'):
   raise AssertionError(name)
sys.meta_path.insert(0, Refuse())
from empirical_lawhood.adapters.methods.rubisco_insilico_structure import independent_assessment, integrity_records
assert independent_assessment.DISTANCE_TOLERANCE.is_finite()
"""], check=True)
