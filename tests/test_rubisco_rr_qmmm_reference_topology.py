# SPDX-License-Identifier: MPL-2.0
"""Synthetic mapping/donor controls only; no authentic source constructions."""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
import os
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics import rr_qmmm_reference_topology as m
from empirical_lawhood.adapters.physical.rubisco_kinetics.rr_coupled_preparation import (
    BoundaryCapV1, CoreAtomV1, PreparedAtomV1,
)


def prepared(i, name, element="C", component="KCX", position=191, chain="A"):
    return PreparedAtomV1(f"amber:{i}", chain, position, component, name, element,
                         (Decimal(i), Decimal(0), Decimal(0)), i, "synthetic-exposed-index-fixture")


def index_fixture():
    physical = (
        prepared(1, "CA"), prepared(2, "CB"), prepared(3, "HB2", "H"),
        prepared(4, "HB3", "H"), prepared(5, "CG"),
        prepared(6, "MG", "Mg", "MG", 468),
        prepared(7, "P1", "P", "RUB", 469),
        prepared(8, "O3", "O", "RUB", 469),
        prepared(9, "Ha", "H", "RUB", 469), prepared(10, "O", "O", "ASN", 192),
    )
    cap = PreparedAtomV1("cap:A:191:CA-CB", "A", 191, "CAP", "HL191", "H",
                         (Decimal("1.91"), Decimal(0), Decimal(0)), None,
                         "modeled-boundary-link-H-not-parent-nucleus")
    qm = physical[1:9] + (cap,)
    bond = lambda a, b: tuple(sorted((a, b)))
    graph = tuple(sorted(bond(a, b) for a, b in (("amber:2", "amber:3"), ("amber:2", "amber:4"),
        ("amber:2", "amber:5"), ("amber:2", cap.atom_id), ("amber:8", "amber:9"))))
    caps = (BoundaryCapV1(191, cap.atom_id, "amber:2", "amber:1", 1.09, .91),)
    return physical, qm, graph, caps


def test_index_bijections_links_and_restored_cuts_have_no_cap_duplication():
    physical, qm, graph, caps = index_fixture()
    result = m.derive_reference_indices(physical, qm, graph, caps)
    assert result.full_physical_ids == tuple(f"amber:{i}" for i in range(1, 11))
    assert result.real_qm_full_indices_0based == tuple(range(1, 9))
    assert result.generated_link_ids == ("cap:A:191:CA-CB",)
    assert result.generated_link_quantum_indices_0based == (8,)
    assert result.restored_cut_pairs == (("amber:1", "amber:2"),)
    assert ("amber:1", "amber:2") in result.physical_bonds
    assert not any("cap:" in atom for pair in result.physical_bonds for atom in pair)
    assert result.mm_full_indices_0based == (0, 9)
    with pytest.raises(FrozenInstanceError):
        result.full_physical_ids = ()


def test_role_freezing_leaves_transferred_h_mobile_and_freezes_cb_attached_h_only():
    result = m.derive_reference_indices(*index_fixture())
    assert result.fixed_real_qm_ids == ("amber:2", "amber:3", "amber:4", "amber:6", "amber:7")
    assert result.mobile_real_qm_ids == ("amber:5", "amber:8", "amber:9")
    assert set(result.mobile_full_indices_0based).isdisjoint(result.fixed_full_indices_0based)
    assert result.mobile_full_indices_0based == (4, 7, 8)


@pytest.mark.parametrize("defect", ["duplicate-physical", "fake-qm", "duplicate-cap", "missing-link-edge", "already-restored", "wrong-cut-name"])
def test_index_graph_and_atom_identity_defects_refuse(defect):
    physical, qm, graph, caps = index_fixture()
    if defect == "duplicate-physical":
        physical += (physical[0],)
    elif defect == "fake-qm":
        qm = (replace(qm[0], coordinates=(Decimal(99), Decimal(0), Decimal(0))),)+qm[1:]
    elif defect == "duplicate-cap":
        caps += caps
    elif defect == "missing-link-edge":
        graph = tuple(pair for pair in graph if caps[0].cap_atom_id not in pair)
    elif defect == "already-restored":
        graph = tuple(sorted(graph + (("amber:1", "amber:2"),)))
    else:
        physical = (replace(physical[0], name="N"),)+physical[1:]
    with pytest.raises(ValueError):
        m.derive_reference_indices(physical, qm, graph, caps)


NAMES = "N H CA HA CB HB2 HB3 CG ND1 HD1 CE1 HE1 NE2 CD2 HD2 C O".split()
INTERNAL_EDGES = (
    ("N", "H"), ("N", "CA"), ("CA", "HA"), ("CA", "CB"), ("CA", "C"),
    ("C", "O"), ("CB", "HB2"), ("CB", "HB3"), ("CB", "CG"),
    ("CG", "ND1"), ("ND1", "HD1"), ("ND1", "CE1"), ("CE1", "HE1"),
    ("CE1", "NE2"), ("NE2", "CD2"), ("CD2", "HD2"), ("CD2", "CG"),
)


def core_atom(i, name, component, position, scaled="0.00000000E+00"):
    element = "H" if name.startswith("H") else name[0]
    number = {"H": 1, "C": 6, "N": 7, "O": 8}[element]
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        charge = str(Decimal(scaled)/Decimal("18.2223"))
    row = (i, 1, name, element, number, "h" if element == "H" else element.lower(),
           1, "1.00800000E+00" if element == "H" else "1.20000000E+01", scaled, charge,
           "   0.0000000", "   0.0000000", "   0.0000000", "synthetic-source", None)
    return CoreAtomV1(row, "B", position, component)


def native_bond(first, second, parameter=1):
    return (first, second, parameter, "BONDS_INC_HYDROGEN", str((first-1)*3),
            str((second-1)*3), str(parameter), "3.00000000E+02", "1.01000000E+00")


def spectator_fixture():
    target = tuple(core_atom(i+1, "HE2" if name == "HD1" else name, "HIE", 287,
                             "3.64446000E+00" if name == "NE2" else "0.00000000E+00")
                   for i, name in enumerate(NAMES))
    donor = tuple(core_atom(i+101, name, "HID", 91,
                            "1.82223000E+00" if name == "ND1" else "0.00000000E+00")
                  for i, name in enumerate(NAMES))
    external = (core_atom(201, "C", "ALA", 90), core_atom(202, "N", "ALA", 92),
                core_atom(203, "C", "ALA", 286), core_atom(204, "N", "ALA", 288))
    named = {a.name: a.index for a in target}
    donated = {a.name: a.index for a in donor}
    old_edges = tuple(("NE2", "HE2") if pair == ("ND1", "HD1") else pair for pair in INTERNAL_EDGES)
    rows = tuple(native_bond(named[a], named[b]) for a, b in old_edges) + tuple(
        native_bond(donated[a], donated[b], 2) for a, b in INTERNAL_EDGES) + (
            native_bond(201, donated["N"]), native_bond(donated["C"], 202),
            native_bond(203, named["N"]), native_bond(named["C"], 204))
    source = target+donor+external
    physical = tuple(PreparedAtomV1(f"amber:{a.index}", "B", a.author_position,
        "HID" if a.author_position == 287 else a.component,
        "HD1" if a.author_position == 287 and a.name == "HE2" else a.name,
        a.element, a.coordinates, a.index, "synthetic-prepared") for a in source)
    by_name = {a.name: a.atom_id for a in physical if a.author_position == 287}
    graph = tuple(sorted(tuple(sorted((by_name[a], by_name[b]))) for a, b in INTERNAL_EDGES)) + (("amber:203", by_name["N"]), tuple(sorted((by_name["C"], "amber:204"))))
    graph = tuple(sorted(tuple(sorted(pair)) for pair in graph))
    return source, rows, physical, graph


def test_complete_spectator_inventory_graph_types_charge_and_h_nucleus_lineage():
    result = m.derive_spectator_hid_splice(*spectator_fixture())
    assert len(result.atom_joins) == 17 and len(result.donor_internal_bond_witnesses) == 17
    assert len(result.donor_external_bond_witnesses) == 2
    assert len(result.target_original_external_bond_witnesses) == 2
    assert result.target_prepared_external_bonds == (("amber:1", "amber:203"), ("amber:16", "amber:204"))
    moved = next(r for r in result.atom_joins if r.target_prepared_name == "HD1")
    assert (moved.target_physical_id, moved.target_previous_native_name, moved.donor_native_atom_index_1based) == ("amber:10", "HE2", 110)
    assert moved.donor_native_tokens[2] == "HD1"
    assert result.removed_target_bonds == (("amber:10", "amber:13"),)
    assert result.added_target_bonds == (("amber:10", "amber:9"),)
    assert result.donor_internal_bonds_mapped_to_target == result.target_prepared_internal_bonds
    assert result.original_source_partial_charge.as_fraction() == Fraction(1, 5)
    assert result.assigned_donor_partial_charge.as_fraction() == Fraction(1, 10)
    assert not result.bonded_parameter_splice_complete


@pytest.mark.parametrize("defect", ["missing-donor", "duplicate-donor-name", "wrong-donor-element", "lost-H-id", "wrong-H-attachment", "missing-donor-bond", "dangling-source-bond", "missing-target-peptide-bond", "rounded-native-index", "nonfinite-force"])
def test_spectator_source_and_graph_splice_defects_refuse(defect):
    source, rows, physical, graph = spectator_fixture()
    if defect == "missing-donor":
        source = tuple(a for a in source if a.index != 110)
    elif defect == "duplicate-donor-name":
        source += (core_atom(205, "ND1", "HID", 91),)
    elif defect == "wrong-donor-element":
        row = list(source[26].native_tokens)
        row[3], row[4] = "C", 6
        source = source[:26]+(replace(source[26], native_tokens=tuple(row)),)+source[27:]
    elif defect == "lost-H-id":
        physical = tuple(replace(a, atom_id="amber:205", parent_atom_index=205) if a.atom_id == "amber:10" else a for a in physical)
    elif defect == "wrong-H-attachment":
        graph = tuple(sorted(tuple(sorted(("amber:10", "amber:13"))) if set(pair) == {"amber:10", "amber:9"} else pair for pair in graph))
    elif defect == "missing-donor-bond":
        rows = tuple(row for row in rows if set(row[:2]) != {109, 110})
    elif defect == "dangling-source-bond":
        rows += (native_bond(110, 500),)
    elif defect == "missing-target-peptide-bond":
        graph = tuple(pair for pair in graph if set(pair) != {"amber:1", "amber:203"})
    else:
        altered = list(rows[0])
        altered[4 if defect == "rounded-native-index" else 7] = "1" if defect == "rounded-native-index" else "NaN"
        rows = (tuple(altered),)+rows[1:]
    with pytest.raises(ValueError):
        m.derive_spectator_hid_splice(source, rows, physical, graph)


def test_plan_scope_refuses_untyped_inputs_and_exposes_missing_runtime_contract():
    with pytest.raises(ValueError, match="exact existing typed"):
        m.derive_rr_reference_topology(None, None, None)
    assert "ORIGINAL_SOURCE_TYPES" in m.QM_LJ_TYPE_POLICY
    assert "extract-donor-internal-angle-and-dihedral-constants-and-native-multiplicity" in m.RUNTIME_SPLICE_REQUIREMENTS
    assert "zero-QM-classical-particle-and-exception-charge-products-preserve-cross-LJ" in m.RUNTIME_SPLICE_REQUIREMENTS


def test_ordinary_index_records_reject_mutable_rosters_and_incorrect_bijections():
    result = m.derive_reference_indices(*index_fixture())
    with pytest.raises(ValueError, match="immutable"):
        replace(result, full_physical_ids=list(result.full_physical_ids))
    with pytest.raises(ValueError, match="bijection"):
        replace(result, real_qm_full_indices_0based=result.real_qm_full_indices_0based[::-1])
    with pytest.raises(ValueError, match="appended exactly once"):
        replace(result, generated_link_quantum_indices_0based=(99,))


def test_cold_import_has_no_native_packages_or_processes():
    code = """
import importlib.abc
import subprocess
import sys
class NoNative(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy','scipy','openmm','parmed','ash','xtb','Bio','pyscf'}:
            raise AssertionError(fullname)
sys.meta_path.insert(0, NoNative())
subprocess.Popen = lambda *a, **k: (_ for _ in ()).throw(AssertionError('native effect'))
from empirical_lawhood.adapters.physical.rubisco_kinetics import rr_qmmm_reference_topology
assert rr_qmmm_reference_topology.PLAN_ID.endswith('v1')
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1]/"src")
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
