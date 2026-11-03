# SPDX-License-Identifier: MPL-2.0
"""Exposed differential/adverse controls; no authentic native molecule is run."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import os
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import (
    physical_preparation_geometry as old_geometry,
    preparation_integrity as old_assignment,
    serialized_preparation_assessment as selected,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_rubisco_preamber_geometry_integrity import ter
from tests.test_rubisco_physical_preparation_geometry import (
    POINTS, heavy_pdb, inpcrd, origins, stock,
)
from tests.test_rubisco_preparation_integrity import (
    amber_text, exposed_preparation, full_exposed_origins,
)


def serialized_full_origins():
    model, census, origin, raw, atoms, chains = full_exposed_origins()
    rows, serial = [], 0
    original = raw.splitlines()
    for index, line in enumerate(original):
        serial += 1
        rows.append(line[:6] + f"{serial:5d}" + line[11:] + "\n")
        if index == len(original) - 1 or line[21] != original[index + 1][21]:
            serial += 1
            rows.append(ter(serial, line[21], int(line[22:26]), line[17:20]))
    return model, census, origin, "".join(rows), atoms, chains


def test_original_full5048_math_is_unchanged_with_justified_ter_serials():
    old_args = full_exposed_origins()
    assert old_assignment.validate_origins(*old_args, set()) == (5048, 5048)
    new_args = serialized_full_origins()
    before = dict(old_assignment.validate_origins.__globals__)
    assert selected.validate_origins(*new_args, set()) == (5048, 5048)
    assert old_assignment.validate_origins.__globals__ == before
    with pytest.raises(ValueError, match="denominator"):
        old_assignment.validate_origins(*new_args, set())
    assert old_assignment.validate_origins(*old_args, set()) == (5048, 5048)


@pytest.mark.parametrize("change", ("unjustified-gap", "wrong-ter", "duplicate-ter",
    "missing-realization", "dropped-realization", "changed-element", "wrong-genotype", "wrong-origin"))
def test_full_ter_origins_cannot_hide_missing_or_changed_actual_rows(change):
    model, census, origin, raw, atoms, chains = serialized_full_origins()
    if change == "unjustified-gap":
        raw = raw.replace("TER     494", "TER     495", 1)
    if change == "wrong-ter":
        raw = raw.replace("TER     494      ALA A 493", "TER     494      ALA B 493", 1)
    if change == "duplicate-ter":
        first = next(line for line in raw.splitlines() if line.startswith("TER"))
        raw = raw.replace(first + "\n", first + "\n" + first + "\n", 1)
    if change == "missing-realization":
        origin.pop("amber_realization")
    if change == "dropped-realization":
        origin["amber_realization"]["atoms"].pop()
    if change == "changed-element":
        census["atomic_numbers"] = (8,) + census["atomic_numbers"][1:]
    if change == "wrong-genotype":
        origin["amber_realization"]["complete_chains"][0]["actual_residue_names"][0] = "GLY"
    if change == "wrong-origin":
        origin["complete_heavy_atoms"][0]["source_origin"]["source"][2] = "substituted"
    with pytest.raises(ValueError):
        selected.validate_origins(model, census, origin, raw, atoms, chains, set())


@pytest.mark.parametrize("verdict", (A.NOT_ATTEMPTED, A.UNEVALUABLE, A.UNSUPPORTED, A.REFUSED, A.FALSIFIED))
def test_complete24_adverse_denominator_and_legacy_bytes_remain_distinct(verdict):
    source, preparation, assets = exposed_preparation(verdict)
    legacy = old_assignment.assess(source, preparation, assets, (), (), {})
    legacy_bytes = legacy.canonical_bytes()
    result = selected.assess(source, preparation, assets, (), (), {})
    assert type(result) is selected.SerializedPreparationIntegrity
    assert result.VERSION == "1.1.0" and result.method == selected.ASSIGNMENT_METHOD
    assert result.legacy_math_method == old_assignment.METHOD
    assert result.pdb_reader_method == selected.READER_METHOD
    assert result.model_dispositions == legacy.model_dispositions
    assert result.disposition_counts == legacy.disposition_counts
    assert result.assignment_disposition is verdict
    assert sum(number for _, number in result.disposition_counts) == 24
    assert result.physical_independent_units == 0
    assert result.geometry_disposition is result.kinetic_disposition is A.UNEVALUABLE
    encoded = result.canonical_bytes()
    assert decode_canonical_bytes(encoded, selected.SerializedPreparationIntegrity, maximum_bytes=len(encoded)) == result
    with pytest.raises(ValueError):
        decode_canonical_bytes(encoded, old_assignment.PreparationIntegrity, maximum_bytes=len(encoded))
    assert old_assignment.assess(source, preparation, assets, (), (), {}).canonical_bytes() == legacy_bytes
    before = dict(old_geometry.assess_geometry.__globals__)
    geometry = selected.assess_geometry(source, preparation, assets, result)
    assert old_geometry.assess_geometry.__globals__ == before
    assert type(geometry) is selected.SerializedPreparationGeometry
    assert geometry.assignment_integrity.object_version == "1.1.0"
    assert len(geometry.models) == 24
    assert all(row.assignment_disposition is verdict for row in geometry.models)
    assert geometry.geometry_adequacy is geometry.force_adequacy is A.UNEVALUABLE
    geometry_bytes = geometry.canonical_bytes()
    assert decode_canonical_bytes(geometry_bytes, selected.SerializedPreparationGeometry,
        maximum_bytes=len(geometry_bytes)) == geometry
    with pytest.raises(ValueError):
        selected.assess_geometry(source, preparation, assets, legacy)


@pytest.mark.parametrize("field", ("method", "legacy_math_method", "pdb_reader_method",
    "geometry_disposition", "native_coverage_disposition", "dynamics_disposition", "kinetic_disposition"))
def test_assignment_revision_cannot_relabel_reader_method_or_downstream_admission(field):
    source, preparation, assets = exposed_preparation()
    result = selected.assess(source, preparation, assets, (), (), {})
    changed = old_assignment.METHOD if field == "method" else selected.ASSIGNMENT_METHOD if field in (
        "legacy_math_method", "pdb_reader_method") else A.SATISFIED
    with pytest.raises(ValueError):
        replace(result, **{field: changed})


@pytest.mark.parametrize("field", ("method", "legacy_math_method", "pdb_reader_method",
    "geometry_adequacy", "native_coverage", "force_adequacy", "relaxation_adequacy"))
def test_geometry_revision_cannot_relabel_reader_method_or_physical_admission(field):
    source, preparation, assets = exposed_preparation()
    integrity = selected.assess(source, preparation, assets, (), (), {})
    result = selected.assess_geometry(source, preparation, assets, integrity)
    changed = old_geometry.METHOD if field == "method" else selected.GEOMETRY_METHOD if field in (
        "legacy_math_method", "pdb_reader_method") else A.SATISFIED
    with pytest.raises(ValueError):
        replace(result, **{field: changed})


@pytest.mark.parametrize("points", (POINTS,
    (POINTS[0], POINTS[1], (Decimal('.5'), Decimal('.5'), Decimal(0)), POINTS[3]),
    (POINTS[0], POINTS[1], POINTS[0], POINTS[3])))
def test_exact_pair_bond_energy_and_singularity_math_matches_original(points):
    raw = heavy_pdb(points)
    with_ter = raw + ter(4)
    operands = (amber_text(stock()), inpcrd(points))
    original = old_geometry.diagnose_geometry(*operands, raw, origins())
    before = dict(old_geometry.diagnose_geometry.__globals__)
    successor = selected.diagnose_geometry(*operands, with_ter, origins())
    assert successor.canonical_bytes() == original.canonical_bytes()
    assert old_geometry.diagnose_geometry.__globals__ == before
    assert old_geometry.diagnose_geometry(*operands, raw, origins()).canonical_bytes() == original.canonical_bytes()


def test_serialized_geometry_refuses_bad_ter_references_and_changed_coordinates():
    raw = heavy_pdb() + ter(4)
    topology = amber_text(stock())
    for changed in (raw.replace("TER       4", "TER       5"), raw + "CONECT    1    4\n"):
        with pytest.raises(ValueError):
            selected.diagnose_geometry(topology, inpcrd(), changed, origins())
    moved = deepcopy(origins())
    moved["amber_realization"]["atoms"][0]["amber_atom_index"] = 1
    with pytest.raises(ValueError):
        selected.diagnose_geometry(topology, inpcrd(), raw, moved)


def test_selected_assessment_imports_cold_without_native_or_producer(tmp_path):
    source = Path(__file__).resolve().parents[1] / "src"
    code = '''
import importlib.abc
import sys
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        blocked = ('numpy','parmed','openmm','pdbfixer','empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.native','empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.parameter_audit','empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.coordinate_plan','empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.science','empirical_lawhood.adapters.methods.rubisco_insilico_structure.science')
        if any(fullname == name or fullname.startswith(name+'.') for name in blocked):
            raise AssertionError('producer/native import refused: '+fullname)
sys.meta_path.insert(0,Refuse())
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import serialized_preparation_assessment as selected
assert selected.SerializedPreparationIntegrity.VERSION == '1.1.0'
assert selected.SerializedPreparationGeometry.VERSION == '1.1.0'
assert selected.assignment_math.PreparationIntegrity.VERSION == '1.0.0'
assert selected.geometry_math.PhysicalPreparationGeometry.VERSION == '1.0.0'
'''
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path,
        env=dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE="1"),
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
