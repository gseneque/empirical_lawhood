# SPDX-License-Identifier: MPL-2.0
"""Independent synthetic electronic arithmetic; no chemistry solver executes."""

from copy import deepcopy
from hashlib import sha256
from math import sqrt
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.simulators.rubisco_electronic import core as e


def software_xyz():
    # Deliberately synthetic coordinates. These tests admit no original
    # preparation, Hamiltonian result or independent biological observation.
    lines = ["14", "Synthetic software operand; not an original enolate"]
    for element in ("C",) * 4 + ("O",) * 3 + ("H",) * 7:
        lines.append(f"  {element}   -0.1250  +1.2500  2.00000000")
    return ("\n".join(lines) + "\n").encode("ascii")


def software_populations(*, enolate):
    # All fourteen atom slots remain present, and the complete vector sums
    # to one. Carbon and oxygen directions are independently specified.
    values = [0.0] * 14
    values[0] = 0.2
    if enolate == 2:
        values[1], values[2], values[4], values[5] = 0.1, 0.4, 0.2, 0.1
    else:
        values[1], values[2], values[4], values[5] = 0.4, 0.1, 0.1, 0.2
    return {"lowdin_by_atom": list(values), "mulliken_by_atom": list(values)}


def software_results():
    return {
        case: {"status": "converged", "populations": software_populations(enolate=int(case[-1]))}
        for case in ("B2", "B3", "W2", "W3")
    }


def test_module_import_is_cold_in_a_fresh_process():
    script = """
import importlib.abc, sys
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy', 'scipy', 'pyscf', 'horton', 'chemtools'}:
            raise AssertionError('native or numerical import during cold discovery: ' + fullname)
sys.meta_path.insert(0, Refuse())
import empirical_lawhood.adapters.simulators.rubisco_electronic.core
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script], cwd=Path(__file__).parent.parent,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_reduced_source_retains_exact_tokens_title_and_original_identity():
    payload = software_xyz()
    geometry = e.decode_reduced_xyz(payload)
    assert len(geometry.atoms) == 14
    assert tuple(atom.element for atom in geometry.atoms) == ("C",) * 4 + ("O",) * 3 + ("H",) * 7
    assert geometry.atoms[0].coordinate_tokens == ("-0.1250", "+1.2500", "2.00000000")
    assert geometry.native_title == "Synthetic software operand; not an original enolate"
    assert geometry.source_sha256 == sha256(payload).hexdigest()
    assert geometry.source_bytes == len(payload)
    spacing_changed = payload.replace(b"  C   ", b" C ", 1)
    changed = e.decode_reduced_xyz(spacing_changed)
    assert changed.atoms == geometry.atoms
    assert changed.source_sha256 != geometry.source_sha256
    assert changed.source_bytes == len(spacing_changed)


@pytest.mark.parametrize("bad_token", ["nan", "inf", "1e-3", "1", "1.2.3", "10000.1"])
def test_source_refuses_nonfinite_or_out_of_contract_numeric_grammar(bad_token):
    altered = software_xyz().replace(b"-0.1250", bad_token.encode("ascii"), 1)
    with pytest.raises(ValueError):
        e.decode_reduced_xyz(altered)


@pytest.mark.parametrize("change", [
    lambda p: p.replace(b"14\n", b"13\n", 1),
    lambda p: b"\n".join(p.splitlines()[:-1]) + b"\n",
    lambda p: p + b"H 0.0 0.0 0.0\n",
    lambda p: p.replace(b"  O   ", b"  M1   ", 1),
    lambda p: p.replace(b"  C   ", b"  H   ", 1),
    lambda p: p.replace(b"-0.1250  +1.2500  2.00000000", b"0.0 0.0", 1),
    lambda p: p.replace(b"-0.1250  +1.2500  2.00000000", b"0.0 0.0 0.0 0.0", 1),
    lambda p: p.replace(b"Synthetic", b"\xffynthetic", 1),
])
def test_source_refuses_incomplete_extra_or_spoofed_atom_census(change):
    with pytest.raises(ValueError):
        e.decode_reduced_xyz(change(software_xyz()))


@pytest.mark.native("numpy")
def test_diagonal_overlap_uses_metric_normalization_and_one_electron_density():
    result = e.homo_populations(((4.0, 0.0), (0.0, 9.0)), (0.3, 4 / 15), (0, 1), 2)
    # Metric norm is 4*(3/10)^2 + 9*(4/15)^2 = 1. Euclidean
    # normalization, coefficient squares and a two-electron factor differ.
    assert result["overlap_eigenvalues"] == pytest.approx((4, 9), abs=1e-13)
    assert result["one_electron_metric_norm"] == pytest.approx(1, abs=1e-13)
    assert result["lowdin_by_atom"] == pytest.approx((0.36, 0.64), abs=1e-13)
    assert result["mulliken_by_atom"] == pytest.approx((0.36, 0.64), abs=1e-13)


@pytest.mark.native("numpy")
def test_nontrivial_overlap_has_independently_known_distinct_partitions():
    result = e.homo_populations(((1.0, 0.6), (0.6, 1.0)), (1.0, 0.0), (0, 1), 2)
    # The symmetric square root is [[3,1],[1,3]]/sqrt(10).
    # Squaring its first column gives (.9,.1), unlike S*c or c alone.
    assert result["lowdin_by_atom"] == pytest.approx((0.9, 0.1), abs=1e-13)
    assert result["mulliken_by_atom"] == pytest.approx((1, 0), abs=1e-13)


@pytest.mark.native("numpy")
def test_negative_mulliken_is_retained_and_homo_phase_does_not_change_density():
    overlap = ((1.0, 0.6), (0.6, 1.0))
    coefficient = (1 / sqrt(2.6), -2 / sqrt(2.6))
    result = e.homo_populations(overlap, coefficient, (0, 1), 2)
    reversed_phase = e.homo_populations(overlap, tuple(-v for v in coefficient), (0, 1), 2)
    # Independent hand calculation: S^(1/2)*c = (1,-5)/sqrt(26).
    assert result["lowdin_by_atom"] == pytest.approx((1 / 26, 25 / 26), abs=1e-13)
    assert result["mulliken_by_atom"] == pytest.approx((-1 / 13, 14 / 13), abs=1e-13)
    for key in ("lowdin_by_atom", "mulliken_by_atom"):
        assert reversed_phase[key] == pytest.approx(result[key], abs=1e-13)
        assert sum(result[key]) == pytest.approx(1, abs=1e-13)


@pytest.mark.native("numpy")
def test_ao_condensation_preserves_complete_atom_mass_and_ao_permutation():
    overlap = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    result = e.homo_populations(overlap, (1 / 3, 2 / 3, 2 / 3), (0, 0, 1), 2)
    permuted = e.homo_populations(overlap, (2 / 3, 1 / 3, 2 / 3), (1, 0, 0), 2)
    for key in ("lowdin_by_atom", "mulliken_by_atom"):
        assert result[key] == pytest.approx((5 / 9, 4 / 9), abs=1e-13)
        assert permuted[key] == pytest.approx(result[key], abs=1e-13)


@pytest.mark.native("numpy")
@pytest.mark.parametrize("overlap", [
    ((1.0, 2.0), (2.0, 1.0)),  # indefinite
    ((1.0, 1.0), (1.0, 1.0)),  # singular
    ((1.0, 0.0), (0.0, 1e-14)),  # numerically singular
    ((1.0, 0.6), (0.2, 1.0)),  # asymmetric; eigh alone would hide this
    ((1.0, float("nan")), (float("nan"), 1.0)),
])
def test_nonphysical_or_nonfinite_overlap_refuses_without_eigenvalue_clipping(overlap):
    with pytest.raises(ValueError):
        e.homo_populations(overlap, (1.0, 0.0), (0, 1), 2)


@pytest.mark.native("numpy")
@pytest.mark.parametrize("coefficient,census,natoms", [
    ((2.0, 0.0), (0, 1), 2),  # a nonunit orbital must not be renormalized
    ((float("inf"), 0.0), (0, 1), 2),
    ((1.0, 0.0, 0.0), (0, 1), 2),
    ((1.0, 0.0), (0,), 2),
    ((1.0, 0.0), (0, 0), 2),  # atom1 omitted despite a normalized AO vector
    ((1.0, 0.0), (0, 2), 2),
    ((1.0, 0.0), (0, True), 2),
    ((1.0, 0.0), (0, 1), True),
])
def test_orbital_norm_shape_and_complete_ao_atom_coverage_are_guarded(coefficient, census, natoms):
    with pytest.raises(ValueError):
        e.homo_populations(((1.0, 0.0), (0.0, 1.0)), coefficient, census, natoms)


def test_complete_carbon_criterion_and_all_site_directions_are_retained():
    result = e.assess_carbon_ordering(software_results())
    assert result["assigned_anion_cases"] == ["B2", "B3", "W2", "W3"]
    assert result["assigned_anion_denominator"] == result["evaluable_anion_count"] == 4
    assert result["primary_entry_pass"]
    assert result["primary_family_pass"] == {"B": True, "W": True}
    for partition in ("lowdin", "mulliken"):
        assert set(result["carbon_ordering"][partition]) == {"B2", "B3", "W2", "W3"}
        for family in ("B", "W"):
            changes = result["site_changes"][partition][family]
            assert set(changes) == {"C2", "O2", "C3", "O3"}
            assert all(row["evaluable"] and row["direction_pass"] for row in changes.values())
            assert changes["C2"]["enolate3_minus2"] == pytest.approx(0.3)
            assert changes["O2"]["enolate3_minus2"] == pytest.approx(-0.1)
            assert changes["C3"]["enolate3_minus2"] == pytest.approx(-0.3)
            assert changes["O3"]["enolate3_minus2"] == pytest.approx(0.1)


@pytest.mark.parametrize("status", ["scf_nonconverged", "resource_limited", "not_started"])
def test_failed_case_never_shrinks_denominator_or_borrows_its_partial_populations(status):
    cases = software_results()
    cases["B3"]["status"] = status
    result = e.assess_carbon_ordering(cases)
    assert result["assigned_anion_denominator"] == 4
    assert result["evaluable_anion_count"] == 3
    assert not result["primary_entry_pass"]
    assert result["primary_family_pass"] == {"B": False, "W": True}
    for partition in ("lowdin", "mulliken"):
        assert result["carbon_ordering"][partition]["B3"] == {"evaluable": False, "criterion_pass": False}
        assert all(not row["evaluable"] for row in result["site_changes"][partition]["B"].values())
        assert all(row["evaluable"] for row in result["site_changes"][partition]["W"].values())


def test_exact_carbon_tie_fails_primary_and_secondary_cannot_replace_it():
    cases = software_results()
    primary = cases["W3"]["populations"]["lowdin_by_atom"]
    primary[1], primary[2] = 0.25, 0.25
    result = e.assess_carbon_ordering(cases)
    assert not result["primary_entry_pass"]
    assert result["primary_family_pass"] == {"B": True, "W": False}
    assert not result["carbon_ordering"]["lowdin"]["W3"]["criterion_pass"]
    assert result["carbon_ordering"]["mulliken"]["W3"]["criterion_pass"]
    # Conversely, a failed secondary partition is retained without replacing
    # the fixed primary outcome.
    cases = software_results()
    secondary = cases["B2"]["populations"]["mulliken_by_atom"]
    secondary[1], secondary[2] = secondary[2], secondary[1]
    result = e.assess_carbon_ordering(cases)
    assert result["primary_entry_pass"]
    assert not result["carbon_ordering"]["mulliken"]["B2"]["criterion_pass"]


@pytest.mark.parametrize("mutation", ["missing", "extra", "short", "nonfinite", "nonunit"])
def test_assessment_refuses_wrong_roster_or_incomplete_spoofed_population(mutation):
    cases = deepcopy(software_results())
    if mutation == "missing":
        cases.pop("B3")
    elif mutation == "extra":
        cases["extra"] = cases["B3"]
    else:
        values = cases["B3"]["populations"]["lowdin_by_atom"]
        if mutation == "short":
            values.pop()
        elif mutation == "nonfinite":
            values[0] = float("nan")
        else:
            values[0] += 0.2
    with pytest.raises(ValueError):
        e.assess_carbon_ordering(cases)
