# SPDX-License-Identifier: MPL-2.0
"""Synthetic geometric contracts; no copyrighted originals or kinetic labels."""

from dataclasses import replace
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import json
import os
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics import fm23_preparation as fm
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


def atom(element, x, y, z, digits=4):
    return fm.GeometryAtomV1(element, tuple(format(Decimal(v), f".{digits}f") for v in (x, y, z)))


def simple_atoms():
    # Independently chosen orthogonal axes make each source-like distance exact.
    return (atom("C", 0, 0, 0), atom("C", "1.37", 0, 0),
            atom("O", "1.37", "1.32", 0), atom("O", 0, 0, "2.78"),
            atom("O", "1.24", 0, "2.78"), atom("O", "1.37", 0, "-3.19"),
            atom("Mg", 0, -8, 0))


TARGETS = ("1.24", "2.78", "1.37", "1.32", "3.19")


@pytest.fixture(scope="module")
def synthetic_source():
    """Temporary alternate seals exercise intake, never actual-source execution.

    The real source pins remain in production. This synthetic packet uses the
    same24 count/label roster but invented coordinates, no article or endpoints.
    Only byte/atom projection pins are replaced during these software checks.
    """
    patch = pytest.MonkeyPatch()
    rows, pins = [], []
    for n, (pathway, label, count, _) in enumerate(fm.GEOMETRY_PINS):
        state = min(n, 6)
        oo, gas, cc, co, water = (row[state] for row in fm.OXYGEN_TARGETS)
        atoms = [atom("H", 50 + i * 20, 70, 80) for i in range(count)]
        for index, value in {
            158: atom("C", 0, 0, 0), 159: atom("C", cc, 0, 0),
            165: atom("O", cc, co, 0), 162: atom("O", 0, 0, gas),
            168: atom("O", oo, 0, gas), 209: atom("O", cc, 0, "-" + water),
            156: atom("Mg", 0, -8, 0),
        }.items():
            atoms[index - 1] = value
        pin = fm.native_atom_projection_sha256(tuple(atoms))
        pins.append((pathway, label, count, pin))
        rows.append({"ordinal": n + 1, "native_pathway": pathway, "native_state_label": label,
                     "native_header_atom_count": count, "projected_atom_count": count,
                     "atom_projection_sha256": pin,
                     "atoms": [{"element": a.element, "xyz_native_decimal_tokens": list(a.coordinate_tokens)}
                               for a in atoms]})
    pdf = b"%PDF-SYNTHETIC-SOFTWARE-FIXTURE-NO-ARTICLE\n"
    projection = json.dumps({"geometries": rows}, sort_keys=True).encode()
    patch.setattr(fm, "GEOMETRY_PINS", tuple(pins))
    patch.setattr(fm, "PDF_SHA256", sha256(pdf).hexdigest())
    patch.setattr(fm, "PDF_BYTES", len(pdf))
    patch.setattr(fm, "PROJECTION_SHA256", sha256(projection).hexdigest())
    patch.setattr(fm, "PROJECTION_BYTES", len(projection))
    source = fm.decode_fm23_projection(pdf, projection)
    protocol = fm.Fm23PreparationProtocolV1(original_pdf_sha256=fm.PDF_SHA256,
                                           reviewed_projection_sha256=fm.PROJECTION_SHA256)
    prepared = fm.prepare_fm23_encounters(source, protocol)
    yield pdf, projection, source, protocol, prepared
    patch.undo()


def test_coordinate_tokens_preserve_signed_zero_and_printed_precision():
    a = fm.GeometryAtomV1("O", ("-0.0000", "+1.0000", "2.00"))
    decoded = decode_canonical_bytes(a.canonical_bytes(), fm.GeometryAtomV1, maximum_bytes=1024)
    assert decoded.coordinate_tokens == ("-0.0000", "+1.0000", "2.00")
    assert decoded.fingerprint() != replace(a, coordinate_tokens=("0.0000", "+1.0000", "2.00")).fingerprint()
    for bad in ((0, "1.0", "2.0"), ("NaN", "1.0", "2.0"), ("1e0", "1.0", "2.0")):
        with pytest.raises(ValueError):
            fm.GeometryAtomV1("O", bad)


def test_distance_matches_independent_pythagoras_and_rounding_boxes():
    a, b = atom("C", 0, 0, 0, digits=1), atom("O", 3, 4, 0, digits=1)
    center, lower, upper = fm.distance_bounds(a, b)
    assert center == 5
    with localcontext(Context(prec=80)):
        reference_lower = (Decimal("2.9") ** 2 + Decimal("3.9") ** 2).sqrt()
        reference_upper = (Decimal("3.1") ** 2 + Decimal("4.1") ** 2 + Decimal("0.1") ** 2).sqrt()
    assert lower <= reference_lower and upper >= reference_upper
    assert reference_lower - lower < Decimal("1e-75")
    assert upper - reference_upper < Decimal("1e-75")
    with localcontext(Context(prec=3, rounding=ROUND_DOWN)):
        assert fm.distance_bounds(a, b) == (center, lower, upper)
        with pytest.raises(ValueError):
            fm.GeometryAtomV1("O", ("10000.0001", "0.0", "0.0"))


def test_printed_coordinate_precision_changes_geometric_admissibility():
    coarse = (atom("C", 0, 0, 0, digits=1), atom("O", 1, 0, 0, digits=1))
    fine = (atom("C", 0, 0, 0), atom("O", 1, 0, 0))
    assert fm.geometric_distance(coarse, 1, 2, "1.04").matches_native_rounding
    assert not fm.geometric_distance(fine, 1, 2, "1.04").matches_native_rounding
    with pytest.raises(ValueError):
        fm.geometric_distance(fine, True, 2)


def test_independent_role_identification_retains_complete_candidate_denominators():
    roles, census = fm.infer_role_candidates(simple_atoms(), TARGETS)
    assert roles == fm.Fm23RoleMapV1(1, 2, 3, 4, 5, 6, 7)
    assert census.oo_pairs_screened == 6 and census.directed_cc_pairs_screened == 2
    assert census.matching_cc == ((1, 2), (2, 1))
    assert census.cco_trials_screened == 8
    assert census.matching_cco == ((1, 2, 3),)
    assert census.gas_trials_screened == 2 and census.water_trials_screened == 4
    assert census.matching_complete == ((1, 2, 3, 4, 5, 6),)


def test_absent_ambiguous_and_excessive_role_candidates_refuse():
    atoms = simple_atoms()
    with pytest.raises(ValueError, match="absent or ambiguous"):
        fm.infer_role_candidates(atoms + (atoms[5],), TARGETS)
    with pytest.raises(ValueError, match="absent or ambiguous"):
        fm.infer_role_candidates(atoms[:3] + (replace(atoms[3], element="N"),) + atoms[4:], TARGETS)
    with pytest.raises(ValueError, match="exactly one Mg"):
        fm.infer_role_candidates(atoms + (atoms[6],), TARGETS)
    many = (atom("Mg", 0, 0, 0),) + tuple(atom("O", 0, 0, 0) for _ in range(511))
    with pytest.raises(ValueError, match="finite trial bound"):
        fm.infer_role_candidates(many, TARGETS)


def test_linear_encounter_orientations_match_independent_hand_construction():
    atoms = simple_atoms()
    roles, _ = fm.infer_role_candidates(atoms, TARGETS)
    first = fm.construct_encounter_atoms(atoms, roles, "original-axis")
    second = fm.construct_encounter_atoms(atoms, roles, "rotated-axis")
    retained = tuple(a for i, a in enumerate(atoms, 1) if i not in (4, 5))
    assert first[:-3] == second[:-3] == retained
    assert tuple(a.element for a in first[-3:]) == ("C", "O", "O")
    values = lambda rows: tuple(tuple(Decimal(v) for v in a.coordinate_tokens) for a in rows)
    assert values(first[-3:]) == ((0, 0, Decimal("3.1")), (Decimal("1.17"), 0, Decimal("3.1")),
                                  (Decimal("-1.17"), 0, Decimal("3.1")))
    assert values(second[-3:]) == ((0, 0, Decimal("3.1")), (0, Decimal("1.17"), Decimal("3.1")),
                                   (0, Decimal("-1.17"), Decimal("3.1")))


def test_encounter_translation_equivariance_and_degenerate_directions():
    atoms = simple_atoms()
    roles, _ = fm.infer_role_candidates(atoms, TARGETS)
    translation = (Decimal(5), Decimal(-2), Decimal(1))
    shifted = tuple(fm.GeometryAtomV1(a.element, tuple(format(Decimal(v) + t, ".4f")
                                                      for v, t in zip(a.coordinate_tokens, translation))) for a in atoms)
    for orientation in fm.ORIENTATIONS:
        original = fm.construct_encounter_atoms(atoms, roles, orientation)
        new = fm.construct_encounter_atoms(shifted, roles, orientation)
        assert all(tuple(Decimal(v) + t for v, t in zip(a.coordinate_tokens, translation))
                   == tuple(Decimal(v) for v in b.coordinate_tokens) for a, b in zip(original, new))
    same_center = atoms[:3] + (replace(atoms[3], coordinate_tokens=atoms[0].coordinate_tokens),) + atoms[4:]
    with pytest.raises(ValueError, match="degenerate"):
        fm.construct_encounter_atoms(same_center, roles, "original-axis")
    with pytest.raises(ValueError, match="declared orientation"):
        fm.construct_encounter_atoms(atoms, roles, "posthoc-axis")


def test_hash_first_two_input_admission_and_complete_source_roundtrip(synthetic_source):
    pdf, projection, source, _, _ = synthetic_source
    assert len(source.geometries) == 24
    assert sum(len(g.atoms) for g in source.geometries) == 5994
    assert source.coordinate_role == fm.SOURCE_ROLE
    decoded = decode_canonical_bytes(source.canonical_bytes(), fm.Fm23ReviewedSourceV1, maximum_bytes=2 * 1024**2)
    assert decoded == source and decoded.fingerprint() == source.fingerprint()
    for bad_pdf, bad_projection in ((pdf + b" ", projection), (pdf, projection + b" "),
                                   (pdf, b"{malformed"), (memoryview(pdf), projection)):
        with pytest.raises(ValueError, match="exact bounded"):
            fm.decode_fm23_projection(bad_pdf, bad_projection)


def test_manual_source_projection_and_role_spoofs_refuse(synthetic_source):
    _, _, source, _, _ = synthetic_source
    geometry = source.geometries[0]
    c3 = geometry.atoms[158]
    numerically_equal = replace(c3, coordinate_tokens=("1.370", *c3.coordinate_tokens[1:]))
    with pytest.raises(ValueError, match="atom tokens or projection"):
        replace(geometry, atoms=geometry.atoms[:158] + (numerically_equal,) + geometry.atoms[159:])
    with pytest.raises(ValueError, match="atom tokens or projection"):
        replace(geometry, atoms=tuple(reversed(geometry.atoms)))
    with pytest.raises(ValueError, match="source metadata"):
        replace(geometry, coordinate_role="ORIGINAL_MACHINE_READABLE_XYZ")
    with pytest.raises(ValueError, match="all24"):
        replace(source, geometries=source.geometries[:-1])
    with pytest.raises(ValueError, match="all24"):
        replace(source, geometries=source.geometries[:-1] + (source.geometries[0],))


def test_preparation_retains_full_checks_unchanged_scaffold_and_failed_carbon_geometry(synthetic_source):
    _, _, source, protocol, prepared = synthetic_source
    assert prepared.roles == fm.Fm23RoleMapV1(158, 159, 165, 162, 168, 209, 156)
    assert len(prepared.oxygen_checks) == 35 and all(c.distance.matches_native_rounding for c in prepared.oxygen_checks)
    assert len(prepared.scaffold.atoms) == 246
    assert tuple(p.orientation for p in prepared.poses) == fm.ORIENTATIONS
    for old, new in zip(prepared.scaffold.source_indices_1based, prepared.scaffold.atoms):
        assert new.coordinate_tokens == source.geometries[0].atoms[old - 1].coordinate_tokens
    for pose in prepared.poses:
        assert len(pose.atoms) == 249 and pose.atoms[:246] == prepared.scaffold.atoms
        assert len(pose.gas_scaffold_distances) == 738
        assert tuple(c.role for c in pose.carbon_checks if not c.distance.matches_native_rounding) == (
            "C2-C3", "C3-O3", "C3-waterO")
        assert pose.native_carbon_reproduction is False and pose.coordinate_role == fm.NEW_ROLE
    assert prepared.protocol_identity.object_fingerprint == protocol.fingerprint()
    assert prepared.source_identity.object_fingerprint == source.fingerprint()
    decoded = decode_canonical_bytes(prepared.canonical_bytes(), fm.Fm23PreparationV1, maximum_bytes=6 * 1024**2)
    assert decoded == prepared and decoded.fingerprint() == prepared.fingerprint()


def test_constructed_records_cannot_attach_forged_coordinates_or_checks(synthetic_source):
    _, _, _, _, prepared = synthetic_source
    pose = prepared.poses[0]
    gas = replace(pose.atoms[-3], coordinate_tokens=("99.0000000000", "0.0000000000", "0.0000000000"))
    with pytest.raises(ValueError, match="new atom tokens"):
        replace(pose, atoms=pose.atoms[:-3] + (gas,) + pose.atoms[-2:])
    with pytest.raises(ValueError, match="carbon checks"):
        replace(pose, carbon_checks=pose.carbon_checks[:-1])
    with pytest.raises(ValueError, match="738"):
        replace(pose, gas_scaffold_distances=pose.gas_scaffold_distances[:-1])
    with pytest.raises(ValueError, match="source mapping"):
        replace(prepared.scaffold, source_indices_1based=tuple(reversed(prepared.scaffold.source_indices_1based)))
    with pytest.raises(ValueError, match="new atom tokens"):
        replace(pose, native_carbon_reproduction=True)


def test_complete_preparation_identities_census_and_case_order_are_closed(synthetic_source):
    _, _, _, protocol, prepared = synthetic_source
    with pytest.raises(ValueError, match="canonical identities"):
        replace(prepared, source_identity=replace(prepared.source_identity, object_fingerprint="0" * 64))
    with pytest.raises(ValueError, match="pose roster"):
        replace(prepared, poses=tuple(reversed(prepared.poses)))
    with pytest.raises(ValueError, match="census"):
        replace(prepared, oxygen_checks=prepared.oxygen_checks[:-1])
    with pytest.raises(ValueError, match="limits"):
        replace(prepared, limitations=())
    with pytest.raises(ValueError, match="construction choices"):
        replace(protocol, orientations=("original-axis",))


def test_preparation_canonical_output_is_independent_of_ambient_decimal_context(synthetic_source):
    _, _, source, protocol, prepared = synthetic_source
    with localcontext(Context(prec=3, rounding=ROUND_DOWN)):
        repeated = fm.prepare_fm23_encounters(source, protocol)
        assert repeated.canonical_bytes() == prepared.canonical_bytes()


def test_cold_import_and_protocol_construction_need_no_optional_scientific_packages():
    script = """
import importlib.abc
import sys
class RefuseOptional(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy','scipy','sympy','mpmath','pyscf','openmm','rdkit','PIL','torch','pypdf'}:
            raise AssertionError('optional import: ' + fullname)
sys.meta_path.insert(0, RefuseOptional())
from empirical_lawhood.adapters.physical.rubisco_kinetics.fm23_preparation import Fm23PreparationProtocolV1
assert Fm23PreparationProtocolV1().canonical_bytes()
"""
    result = subprocess.run([sys.executable, "-c", script], env=os.environ.copy(), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
