# SPDX-License-Identifier: MPL-2.0
"""Synthetic source-format and arithmetic conformance; no authentic admission."""

from dataclasses import FrozenInstanceError, replace
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics import rr_amber_nonbonded as a
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


def native_flag(name, tokens, kind="I", width=8, count=10):
    precision = ".8" if kind == "E" else ""
    lines = [f"%FLAG {name}".ljust(80), f"%FORMAT({count}{kind}{width}{precision})"]
    for i in range(0, len(tokens), count):
        lines.append("".join(f"{token:>{width}}" for token in tokens[i:i+count]))
    return "\n".join(lines) + "\n"


def synthetic_source(overrides=None):
    pointers = [0]*31
    for i, v in {0: 8, 1: 2, 6: 3, 10: 9, 14: 2, 17: 2}.items():
        pointers[i] = v
    rows = {
        "POINTERS": (tuple(map(str, pointers)), "I", 8, 10),
        "ATOM_NAME": (("C1", "C2", "O1", "H1", "N1", "C3", "O2", "H2"), "A", 4, 20),
        "AMBER_ATOM_TYPE": (("c", "c", "o", "h", "n", "c", "o", "h"), "A", 4, 20),
        "ATOM_TYPE_INDEX": (("1", "2", "2", "1", "2", "1", "2", "1"), "I", 8, 10),
        "NUMBER_EXCLUDED_ATOMS": (("1", "2", "1", "1", "1", "1", "1", "1"), "I", 8, 10),
        "EXCLUDED_ATOMS_LIST": (("0", "1", "+0004", "0", "0", "8", "0", "0", "0"), "I", 8, 10),
        "NONBONDED_PARM_INDEX": (("1", "2", "2", "3"), "I", 8, 10),
        "LENNARD_JONES_ACOEF": (("4.00000000E+00", "1.23000000E+02", "0.00000000E+00"), "E", 16, 5),
        "LENNARD_JONES_BCOEF": (("2.00000000E+00", "4.50000000D+01", "-0.00000000E+00"), "E", 16, 5),
        "SCEE_SCALE_FACTOR": (("1.20000000E+00", "2.00000000E+00"), "E", 16, 5),
        "SCNB_SCALE_FACTOR": (("2.00000000E+00", "3.00000000E+00"), "E", 16, 5),
        "DIHEDRALS_INC_HYDROGEN": (("0", "3", "6", "9", "1", "0", "3", "-000006", "9", "2", "0", "3", "6", "9", "1"), "I", 8, 10),
        "DIHEDRALS_WITHOUT_HYDROGEN": (("0", "3", "6", "-9", "2", "0", "3", "12", "21", "1"), "I", 8, 10),
    }
    if overrides:
        rows.update(overrides)
    return ("%VERSION VERSION_STAMP = V0001.000  DATE = synthetic exposed software\n" + "".join(native_flag(name, *values) for name, values in rows.items())).encode("ascii")


def project(raw=None, selected=4):
    raw = synthetic_source() if raw is None else raw
    return a._project((raw,), sha256(raw).hexdigest(), len(raw), selected)


def fixture_pins(monkeypatch, raw):
    """Only exposed synthetic source pins change; genuine source bytes never enter."""
    monkeypatch.setattr(a, "SOURCE_BYTES", len(raw))
    monkeypatch.setattr(a, "SOURCE_SHA256", sha256(raw).hexdigest())
    monkeypatch.setattr(a, "SELECTED_DRY_ATOMS", 4)


def test_exact_type_matrix_and_native_lexical_decimal_are_not_combination_rules():
    p = project()
    pair = p.original_lj_pair(1, 2)
    assert pair.parameter_index_1based == 2
    assert pair.native_a_token == "1.23000000E+02"
    assert pair.native_b_token == "4.50000000D+01"
    # Hand-selected pair table differs from combining self coefficients.
    assert pair.a_kcal_mol_angstrom12 == Decimal(123)
    assert pair.b_kcal_mol_angstrom6 == Decimal(45)
    assert p.original_lj_pair(2, 1).native_a_token == pair.native_a_token
    zero = p.original_lj_pair(2, 3)
    assert zero.native_b_token == "-0.00000000E+00" and zero.b_kcal_mol_angstrom6.is_signed()
    with localcontext(Context(prec=2, rounding=ROUND_DOWN)):
        assert pair.a_kcal_mol_angstrom12 == Decimal(123)
        assert pair.b_kcal_mol_angstrom6 == Decimal(45)


def test_exclusion_direction_zero_sentinel_and_native_positive_spelling_preserved():
    p = project()
    assert p.selected_atoms[1].native_exclusion_tokens == ("1", "+0004")
    assert p.selected_atoms[0].native_exclusion_tokens == ("0",)
    assert p.original_lj_pair(1, 2).source_excluded
    assert p.original_lj_pair(4, 2).source_excluded
    assert not p.original_lj_pair(1, 3).source_excluded
    assert p.full_exclusion_token_count == 9


def test_complete_native_dihedral_signed_indices_scaling_multiplicity_and_omissions():
    p = project()
    assert p.full_dihedral_counts == (3, 2)
    assert p.selected_dihedral_counts == (3, 1)
    assert p.omitted_dihedral_counts == (0, 1)
    assert len(p.selected_dihedrals) == 4
    ignored = p.selected_dihedrals[1]
    assert ignored.native_tokens == ("0", "3", "-000006", "9", "2")
    assert ignored.atom_indices_1based == (1, 2, 3, 4) and not ignored.source_14_enabled
    improper = p.selected_dihedrals[3]
    assert improper.is_improper and not improper.source_14_enabled
    assert tuple(v.native_row_1based for v in p.source_14_terms) == (1, 3)
    assert p.source_14_terms[0].electrostatic_divisor == Decimal("1.2")
    assert p.source_14_terms[0].vdw_divisor == Decimal(2)
    assert ignored.vdw_divisor == Decimal(3)
    assert tuple(v.native_flag_ordinal_1based for v in p.native_parameter_flag_order) == (1, 7, 8, 9, 10, 11)


def test_disabled_zero_scaling_preserves_full_signed_roster_and_lexical_operands():
    raw = synthetic_source({
        "SCEE_SCALE_FACTOR": (("1.20000000E+00", "-0.00000000E+00"), "E", 16, 5),
        "SCNB_SCALE_FACTOR": (("2.00000000E+00", "0.00000000D+00"), "E", 16, 5),
    })
    p = project(raw)
    assert p.full_dihedral_counts == (3, 2)
    assert p.selected_dihedral_counts == (3, 1)
    assert p.omitted_dihedral_counts == (0, 1)
    assert len(p.selected_dihedrals) == 4
    disabled = (p.selected_dihedrals[1], p.selected_dihedrals[3])
    assert tuple(row.native_tokens for row in disabled) == (
        ("0", "3", "-000006", "9", "2"),
        ("0", "3", "6", "-9", "2"),
    )
    for row in disabled:
        assert not row.source_14_enabled
        assert row.native_scee_token == "-0.00000000E+00"
        assert row.native_scnb_token == "0.00000000D+00"
        assert row.electrostatic_divisor == row.vdw_divisor == Decimal(0)
        assert row.electrostatic_divisor.is_signed()
    assert tuple(row.native_row_1based for row in p.source_14_terms) == (1, 3)
    assert all(row.electrostatic_divisor > 0 and row.vdw_divisor > 0 for row in p.source_14_terms)
    assert decode_canonical_bytes(p.canonical_bytes(), type(p), maximum_bytes=1024**2) == p


@pytest.mark.parametrize("signed_atoms", [
    ("0", "3", "-000006", "9", "1"),
    ("0", "3", "6", "-9", "1"),
    ("0", "3", "-6", "-9", "1"),
])
@pytest.mark.parametrize("scales", [
    ("0.00000000E+00", "0.00000000E+00"),
    ("-0.00000000E+00", "2.00000000E+00"),
    ("1.20000000E+00", "0.00000000D+00"),
])
def test_each_native_disable_sign_preserves_zero_without_default_substitution(signed_atoms, scales):
    row = a.AmberDihedral14V1("DIHEDRALS_INC_HYDROGEN", 1, signed_atoms, *scales)
    assert not row.source_14_enabled
    assert row.native_tokens == signed_atoms
    assert (row.native_scee_token, row.native_scnb_token) == scales
    assert row.electrostatic_divisor == Decimal(scales[0])
    assert row.vdw_divisor == Decimal(scales[1].replace("D", "E"))
    assert decode_canonical_bytes(row.canonical_bytes(), type(row), maximum_bytes=4096) == row


@pytest.mark.parametrize("scales", [
    ("0.00000000E+00", "2.00000000E+00"),
    ("1.20000000E+00", "-0.00000000E+00"),
    ("0.00000000E+00", "0.00000000E+00"),
])
def test_enabled_zero_scaling_still_refuses(scales):
    with pytest.raises(ValueError, match="must be positive"):
        a.AmberDihedral14V1("DIHEDRALS_INC_HYDROGEN", 1, ("0", "3", "6", "9", "1"), *scales)


@pytest.mark.parametrize("signed_atoms", [
    ("0", "3", "6", "9", "1"),
    ("0", "3", "-6", "9", "1"),
    ("0", "3", "6", "-9", "1"),
])
@pytest.mark.parametrize("scales", [
    ("-1.20000000E+00", "2.00000000E+00"),
    ("1.20000000E+00", "-2.00000000E+00"),
])
def test_negative_scaling_refuses_for_enabled_and_disabled_rows(signed_atoms, scales):
    with pytest.raises(ValueError, match="must be nonnegative"):
        a.AmberDihedral14V1("DIHEDRALS_INC_HYDROGEN", 1, signed_atoms, *scales)


def test_enabled_zero_scaling_outside_dry_selection_still_refuses_full_source():
    raw = synthetic_source({
        "SCEE_SCALE_FACTOR": (("1.20000000E+00", "0.00000000E+00"), "E", 16, 5),
        "SCNB_SCALE_FACTOR": (("2.00000000E+00", "0.00000000E+00"), "E", 16, 5),
        "DIHEDRALS_WITHOUT_HYDROGEN": (("0", "3", "6", "-9", "2", "0", "3", "12", "21", "2"), "I", 8, 10),
    })
    with pytest.raises(ValueError, match="must be positive"):
        project(raw, selected=4)


def test_hash_first_chunked_wrapper_and_partition_independent_projection(monkeypatch):
    raw = synthetic_source()
    fixture_pins(monkeypatch, raw)
    one = a.decode_rr_amber_nonbonded((raw,))
    chunks = tuple(raw[i:i+77] for i in range(0, len(raw), 77))
    many = a.decode_rr_amber_nonbonded(chunks)
    assert one.projection == many.projection
    assert one.projection.fingerprint() == many.projection.fingerprint()
    assert many.chunk_bindings == tuple((i+1, len(v), sha256(v).hexdigest()) for i, v in enumerate(chunks))
    assert one.CLAIM_SCOPE.startswith("ORIGINAL_KETO_SOURCE_ONLY")
    with pytest.raises(FrozenInstanceError):
        one.projection = project()

    def forbidden(*args):
        raise AssertionError("format reader must not enter before hash seal")

    monkeypatch.setattr(a, "_read_flags", forbidden)
    for supplied in ((raw[::-1],), (raw[:-1],), (raw[:40], raw[41:]), tuple(reversed(chunks))):
        with pytest.raises(ValueError, match="before parsing"):
            a.decode_rr_amber_nonbonded(supplied)


def test_source_chunk_bounds_and_mutable_containers_refuse_before_format_reader(monkeypatch):
    monkeypatch.setattr(a, "_read_flags", lambda *args: pytest.fail("reader entered"))
    for chunks in ([b"x"], (), (bytearray(b"x"),), (b"",), (b"x",)*65):
        with pytest.raises(ValueError):
            a.decode_rr_amber_nonbonded(chunks)
    monkeypatch.setattr(a, "CHUNK_MAXIMUM_BYTES", 4)
    with pytest.raises(ValueError, match="chunk byte bound"):
        a.decode_rr_amber_nonbonded((b"12345",))
    monkeypatch.setattr(a, "SOURCE_MAXIMUM_BYTES", 5)
    with pytest.raises(ValueError, match="total byte bound"):
        a.decode_rr_amber_nonbonded((b"123", b"456"))


def test_chunk_boundary_crlf_and_no_final_newline_preserve_tokens():
    raw = synthetic_source().replace(b"%VERSION VERSION_STAMP", b"%VERSION  VERSION_STAMP").replace(b"\n", b"\r\n").rstrip(b"\r\n")
    split = raw.index(b"%FORMAT") + 7
    assert a._project((raw[:split], raw[split:split+9], raw[split+9:]), sha256(raw).hexdigest(), len(raw), 4) == project(raw)


@pytest.mark.parametrize("changed,message", [
    ({"NONBONDED_PARM_INDEX": (("1", "-1", "-1", "3"), "I", 8, 10)}, "10-12"),
    ({"NONBONDED_PARM_INDEX": (("1", "0", "0", "3"), "I", 8, 10)}, "absent native LJ"),
    ({"NONBONDED_PARM_INDEX": (("1", "2", "3", "3"), "I", 8, 10)}, "asymmetric"),
    ({"NONBONDED_PARM_INDEX": (("1", "4", "4", "3"), "I", 8, 10)}, "out-of-range"),
    ({"SCEE_SCALE_FACTOR": (("1.20000000E+00",), "E", 16, 5)}, "scale census"),
    ({"SCNB_SCALE_FACTOR": (("0.00000000E+00", "3.00000000E+00"), "E", 16, 5)}, "positive"),
    ({"LENNARD_JONES_ACOEF": (("-1.00000000E+00", "1.23000000E+02", "0.00000000E+00"), "E", 16, 5)}, "coefficient census"),
    ({"LENNARD_JONES_BCOEF": (("NaN", "4.50000000E+01", "0.00000000E+00"), "E", 16, 5)}, "Decimal token"),
])
def test_native_parameter_shape_and_unsupported_physics_refuse(changed, message):
    with pytest.raises(ValueError, match=message):
        project(synthetic_source(changed))


def test_full_source_outside_selection_is_validated_before_dry_projection():
    changed = {"ATOM_TYPE_INDEX": (("1", "2", "2", "1", "2", "1", "2", "3"), "I", 8, 10)}
    with pytest.raises(ValueError, match="full native atom/exclusion"):
        project(synthetic_source(changed))
    raw = synthetic_source({"DIHEDRALS_WITHOUT_HYDROGEN": (("0", "3", "6", "-9", "2", "0", "3", "12", "24", "1"), "I", 8, 10)})
    with pytest.raises(ValueError, match="full native dihedral atom"):
        project(raw)
    raw = synthetic_source({"NUMBER_EXCLUDED_ATOMS": (("1", "2", "1", "1", "1", "1", "1", "2"), "I", 8, 10)})
    with pytest.raises(ValueError, match="full native exclusion census"):
        project(raw)


def test_native_parser_rejects_duplicate_missing_and_malformed_fields():
    raw = synthetic_source()
    with pytest.raises(ValueError, match="duplicate or invalid native flag"):
        project(raw + native_flag("ATOM_NAME", ("C",), "A", 4, 20).encode())
    with pytest.raises(ValueError, match="flags are missing"):
        project(raw[:raw.index(b"%FLAG DIHEDRALS_WITHOUT_HYDROGEN")])
    with pytest.raises(ValueError, match="extended native LJ"):
        project(raw + native_flag("LENNARD_JONES_DCOEF", ("0.00000000E+00",), "E", 16, 5).encode())
    with pytest.raises(ValueError, match="declared format"):
        project(raw.replace(b"%FORMAT(10I8)", b"%FORMAT(10I7)", 1))
    with pytest.raises(ValueError, match="line byte bound"):
        a._read_flags((b"x"*(a.MAXIMUM_LINE_BYTES+1),))


def test_canonical_roundtrip_deep_immutability_and_semantic_joins():
    p = project()
    assert decode_canonical_bytes(p.canonical_bytes(), type(p), maximum_bytes=1024**2) == p
    for record in (p.parameter_flags[0], p.selected_atoms[0], p.selected_dihedrals[0], p.original_lj_pair(1, 2)):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=1024**2) == record
    with pytest.raises(ValueError, match="immutable tuple"):
        replace(p.selected_atoms[0], native_exclusion_tokens=["0"])
    with pytest.raises(ValueError, match="dihedral parameter join"):
        replace(p, selected_dihedrals=(replace(p.selected_dihedrals[0], native_scnb_token="3.00000000E+00"),)+p.selected_dihedrals[1:])
    with pytest.raises(ValueError, match="POINTERS census mismatch"):
        replace(p, full_exclusion_token_count=10)
    with pytest.raises(ValueError, match="selected original atom roster"):
        replace(p, selected_atoms=p.selected_atoms[::-1])
    with pytest.raises(ValueError, match="outside selected native"):
        p.original_lj_pair(True, 1)


def test_cold_import_blocks_optional_families_and_native_effects():
    code = """
import importlib.abc
import subprocess
import sys
class NoNative(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy','scipy','openmm','parmed','ash','xtb','Bio'}:
            raise AssertionError(fullname)
sys.meta_path.insert(0, NoNative())
subprocess.Popen = lambda *a, **k: (_ for _ in ()).throw(AssertionError('native effect'))
from empirical_lawhood.adapters.physical.rubisco_kinetics import rr_amber_nonbonded
assert rr_amber_nonbonded.SELECTED_DRY_ATOMS == 13828
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1]/"src")
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
