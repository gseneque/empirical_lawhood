# SPDX-License-Identifier: MPL-2.0
"""Positive and adverse exact-library controls without constructing a Gp parent."""

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np
import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response.amber_terminal_fragments import (
    initialize_amber_terminal_fragments,
    run_sequence,
)
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.coordinate_plan import THREE
from empirical_lawhood.domains.rubisco.rubisco_response.terminal_fragment_placement import (
    METHOD,
    STOCK,
    TEMPLATE,
    TerminalCandidateRejected,
    _check_stock_shape,
    _fragment_geometry,
    _met_points,
    _packing,
    aligned_copy,
    fragment_script,
    replay_terminal_fragments,
    terminal_stock_pins,
)


def test_script_keeps_closed_proline_ring_and_selects_exact_terminal_library_units():
    script = fragment_script("AITPMA")
    assert "NALA ILE THR PRO MET CALA" in script
    assert 'impose q { 1 2 4 5 } { { "C" "N" "CA" "C" -75.0 } }' in script
    assert 'impose q { 1 2 3 4 5 } { { "N" "CA" "C" "N" 145.0 } }' in script
    with pytest.raises(ValueError, match="unambiguous"):
        fragment_script("AX?")


def test_anchor_alignment_preserves_signed_frames_and_never_moves_input():
    xyz = {
        (1, n): np.array(v, float)
        for n, v in {"N": (1, 0, 0), "CA": (0, 0, 0), "C": (0, 1, 0), "CB": (0, 0, 1)}.items()
    }
    rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], float)
    trans = np.array([8, -4, 2], float)
    actual = {k: v @ rotation + trans for k, v in xyz.items()}
    go, report = aligned_copy(xyz, actual, [(1, k) for k in ("N", "CA", "C")], [(1, "CB")])
    assert report["determinant"] == pytest.approx(1) and report["anchor_rmsd_angstrom"] < 1e-12
    assert go[(1, "CB")] == pytest.approx(actual[1, "CB"])
    assert np.array_equal(xyz[1, "CB"], [0, 0, 1])
    with pytest.raises(ValueError, match="collinear"):
        aligned_copy(xyz, {k: np.zeros(3) for k in xyz}, [(1, k) for k in ("N", "CA", "C")], [(1, "CB")])


def test_packing_refuses_only_strictly_close_true_nonbonded_pairs_and_retains_identity():
    keys = [("A", 1, "CA"), ("A", 1, "CB"), ("B", 4, "O"), ("Z", 8, "MG")]
    pts = {k: np.asarray([x, 0, 0]) for k, x in zip(keys, (0.0, 1.4, -1.9, 2.0), strict=True)}
    bad = _packing(pts, {keys[0]}, {tuple(sorted(keys[:2]))})
    assert len(bad) == 1 and (bad[0]["first"], bad[0]["second"]) == (list(keys[0]), list(keys[2]))
    assert bad[0]["distance_angstrom"] == 1.9


@pytest.fixture(scope="module")
def engines():
    selected = os.environ.get("EL_AMBER_TERMINAL_TEST_PREFIX")
    if not selected:
        pytest.skip("Select the locked installed Amber/PDBFixer composition for this native control")
    from empirical_lawhood.api.domain_composition.rubisco_response.construction_preparation import (
        select_gp_amber_engine,
    )
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    import pdbfixer

    base = Path(__file__).resolve().parents[1]
    manifest = json.loads((base / "configs/native/ambertools24-linux-x86_64.json").read_bytes())
    files = tuple(FileEvidence(r["path"], r["size_bytes"], r["sha256"]) for r in manifest["files"])
    engine = select_gp_amber_engine(directory=Path(selected), files=files)
    sites = Path(pdbfixer.__file__).resolve().parent.parent
    raw = (sites / TEMPLATE).read_bytes()
    met = NS(relative_path=TEMPLATE, sha256=sha256(raw).hexdigest(), byte_count=len(raw))
    numeric = NS(files=(met,), site_packages=str(sites), fingerprint=lambda: "b" * 64)
    identity = ObjectIdentity(
        "source.development-terminal", "empirical-lawhood/test/terminal-source", "1.0.0", "a" * 64
    )
    return engine, numeric, identity


@pytest.mark.native("openmm", "pdbfixer")
def test_native_closed_proline_stock_stereochemistry_and_charged_peptide(engines, tmp_path):
    engine, _, _ = engines
    seq = "AITPMED"
    raw = run_sequence(engine, seq, tmp_path)
    points, _, read = _fragment_geometry(seq, raw)
    top = {p: (Path(engine.root) / p).read_text() for p in STOCK}
    assert _check_stock_shape(seq, points, top) < 0.15
    assert read["signed_stereocentres"] == 9 and read["checked_backbone_dihedrals"] == 18
    assert read["declared_charge_warning"] and abs(float(read["signed_net_charge_e"]) + 2) < 1e-6
    bad = deepcopy(raw)
    bad["stdout"] = bad["stdout"].replace(
        "is not zero.", "is not zero.\nother tool: Warning!\nadditional warning"
    )
    with pytest.raises(ValueError, match="warning"):
        _fragment_geometry(seq, bad)
    bad = deepcopy(raw)
    bad["script"] = bad["script"].replace("-75.0", "-175.0")
    with pytest.raises(ValueError, match="script"):
        _fragment_geometry(seq, bad)
    with pytest.raises(ValueError, match="all three"):
        terminal_stock_pins(NS(files=engine.files[0:1]))


def synthetic_parent(engines, root):
    # Two genuine stock fragments mapped into independent, synthetic frames.
    # The 469 intervening Gly per LSU supply explicit original residue/atom identities.
    engine, numeric, identity = engines
    seq = "M" + "A" * 15 + "G" * 468 + "FVETPTANI"
    complete_chains = []
    atoms = []
    origin = []
    coords_by_end = {}
    for name, peptide in (("lsu-n", seq[:16]), ("lsu-c", seq[484:])):
        scratch = root / name
        scratch.mkdir()
        coords_by_end[name] = _fragment_geometry(peptide, run_sequence(engine, peptide, scratch))[0]
    met = _met_points((Path(numeric.site_packages) / TEMPLATE).read_text(), numeric)

    def residue(ch, seqpos, comp, rows, change):
        for name, point in rows.items():
            z = name[0]
            if name in change:
                point = point + np.array((0.831, -0.72, 0.23))
            atoms.append(
                f"ATOM  {len(atoms) + 1:5d} {' ' + name:<4s} {comp:>3s} {ch}{seqpos:4d}    "
                + "".join(f"{v:8.3f}" for v in point)
                + f"  1.00  0.00          {z:>2s}  \n"
            )
            origin.append(
                dict(
                    chain=ch,
                    position=seqpos,
                    component=comp,
                    atom=name,
                    element=z,
                    status="DECLARED_CONSTRUCTED_MUTANT_OR_MISSING_ATOM"
                    if name in change
                    else "INHERITED_OBSERVED_SOURCE",
                    source_origin=None if name in change else {"development_control": True},
                )
            )

    for j, (l, s) in enumerate(zip("ACEGIKMO", "BDFHJLNP", strict=True)):
        origin_shift = np.array([j * 85.0, 0.0, 0.0])
        complete_chains.append(dict(chain=l, subunit="lsu", sequence=seq))
        for pos in range(1, 494):
            if pos <= 16 or pos >= 485:
                lo, name, extra = (
                    (1, "lsu-n", np.zeros(3)) if pos <= 16 else (485, "lsu-c", np.array([0.0, 95.0, 0.0]))
                )
                group = {
                    n: v + origin_shift + extra
                    for (k, n), v in coords_by_end[name].items()
                    if k == pos - lo + 1
                }
            else:
                center = origin_shift + np.array([0.0, 50.0, 2.9 * (pos % 100) + 170.0 * (pos // 100)])
                group = {
                    n: center + v
                    for n, v in {
                        "N": [-1.3, 0, 0],
                        "CA": [0, 0, 0],
                        "C": [0.4, 1.4, 0],
                        "O": [0.8, 2.13, 0],
                    }.items()
                }
            residue(l, pos, THREE[seq[pos - 1]], group, group if pos <= 14 or pos >= 487 else ())
        complete_chains.append(dict(chain=s, subunit="ssu", sequence="M"))
        group = {n: p + origin_shift + np.array([0.0, -85.0, 0.0]) for n, p in met.items()}
        residue(s, 1, "MET", group, ("CG", "SD", "CE"))
    return NS(
        amber_engine=engine,
        numeric_engine=numeric,
        identity=identity,
        heavy_pdb="".join((*atoms, "END\n")),
        origin_json=json.dumps(dict(complete_chains=complete_chains, complete_heavy_atoms=origin)),
    )


@pytest.mark.native("openmm", "pdbfixer")
def test_native_synthetic_complete_census_replay_refusal_and_immutability(engines, tmp_path):
    source = synthetic_parent(engines, tmp_path)
    run = tmp_path / "attempt"
    run.mkdir()
    initial, transforms, constructed = initialize_amber_terminal_fragments(source, run)
    raw = (run / "terminal-fragments.json").read_bytes()
    assert replay_terminal_fragments(source, raw) == (initial, transforms, constructed)
    (receipt,) = transforms
    assert receipt["method"] == METHOD and len(receipt["copies"]) == 24 and len(receipt["junctions"]) == 24
    assert not receipt["packing_contacts"] and not receipt["invalid_chiral_centres"]
    assert len(source.heavy_pdb.splitlines()) == len(initial.splitlines())
    for before, after in zip(source.heavy_pdb.splitlines(), initial.splitlines(), strict=True):
        if before != after:
            assert before[:30] == after[:30] and before[54:] == after[54:]
    forged = json.loads(raw)
    forged["stock_bytes"][STOCK[0]] += " "
    with pytest.raises(ValueError, match="original installed force"):
        replay_terminal_fragments(source, json.dumps(forged).encode())
    forged = json.loads(raw)
    del forged["fragments"]["lsu-c"]["restart"]
    with pytest.raises(ValueError, match="Malformed"):
        replay_terminal_fragments(source, json.dumps(forged).encode())
    forged = json.loads(raw)
    forged["refusal"] = {"error_type": "ValueError", "message": "invented"}
    with pytest.raises(ValueError, match="contradicts"):
        replay_terminal_fragments(source, json.dumps(forged).encode())
    # Move a fixed synthetic foreign atom atop an observed constructed candidate;
    # preserve the failed surface and all actual returned fragments for the original reader.
    target = next(l[30:54] for l in initial.splitlines() if l[21:26] == "A   1" and l[12:16].strip() == "CG")
    lines = source.heavy_pdb.splitlines(keepends=True)
    idx = next(i for i, l in enumerate(lines) if l[21:26] == "A 300" and l[12:16].strip() == "O")
    lines[idx] = lines[idx][:30] + target + lines[idx][54:]
    source.heavy_pdb = "".join(lines)
    failed = tmp_path / "failed"
    failed.mkdir()
    with pytest.raises(TerminalCandidateRejected, match="packing"):
        initialize_amber_terminal_fragments(source, failed)
    rejected = json.loads((failed / "terminal-fragments.json").read_bytes())
    assert list(sorted(rejected["fragments"])) == ["lsu-c", "lsu-n"]
    assert rejected["refusal"]["candidate_diagnostics"]["packing_contacts"]
    with pytest.raises(TerminalCandidateRejected, match="packing"):
        replay_terminal_fragments(source, (failed / "terminal-fragments.json").read_bytes())
    rejected["refusal"]["candidate_diagnostics"]["packing_contacts"] = []
    with pytest.raises(ValueError, match="reconstructed candidate diagnostics"):
        replay_terminal_fragments(source, json.dumps(rejected).encode())


@pytest.mark.native("openmm", "pdbfixer")
@pytest.mark.parametrize(
    "label,first,last,anchor,residues,anchor_names,expected",
    (
        ("n", 2, 17, 16, range(2, 16), ("N", "CA", "C"), (115, 38.07756, 37.75670, 0)),
        ("c", 452, 460, 453, range(454, 461), ("CA", "C", "O"), (45, 14.98717, 15.74797, 42)),
    ),
)
def test_observed_9rub_masked_terminal_accuracy_and_packing(
    engines, tmp_path, label, first, last, anchor, residues, anchor_names, expected
):
    from scipy.spatial import cKDTree
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_assessment import (
        _omega_degrees,
    )

    path = Path(__file__).resolve().parent / "fixtures/rubisco/rr9rub/9RUB.pdb"
    original = path.read_bytes()
    assert sha256(original).hexdigest() == "80dcc3cfdcd12154f1d7c21e9438b9e6b0e9d887381aeeef6f2350b3e1b41fd5"
    observed, components = {}, {}
    for line in original.decode("ascii").splitlines():
        if (
            not line.startswith(("ATOM  ", "HETATM"))
            or line[16] not in (" ", "A")
            or line[76:78].strip() in ("H", "D")
        ):
            continue
        key = line[21], int(line[22:26]), line[12:16].strip()
        assert line[26] == " " and key not in observed
        observed[key] = np.array([float(line[i : i + 8]) for i in (30, 38, 46)])
        components[key[:2]] = line[17:20]

    letters = {three: one for one, three in THREE.items()}
    sequence = "".join(letters[components["A", p]] for p in range(first, last + 1))
    engine, _, _ = engines
    record = run_sequence(engine, sequence, tmp_path)
    points, bonds, census = _fragment_geometry(sequence, record)
    stocks = {p: (Path(engine.root) / p).read_text() for p in STOCK}
    census["maximum_stock_residue_shape_error_angstrom"] = _check_stock_shape(sequence, points, stocks)
    source = {("A", first + p - 1, n): x for (p, n), x in points.items()}
    generated = sorted(k for k in source if k[1] in residues)
    mask = {k for k in observed if k[0] == "A" and k[1] in residues}
    fixed = {k: x for k, x in observed.items() if k not in mask}
    placed, transform = aligned_copy(source, fixed, [("A", anchor, n) for n in anchor_names], generated)
    common = sorted(mask & set(generated))
    excluded = {tuple(sorted((("A", first + p - 1, a), ("A", first + q - 1, b)))) for (p, a), (q, b) in bonds}

    def packing(selected):
        restored = fixed | {k: placed[k] for k in selected}
        close = _packing(restored, set(selected), excluded)
        keys = sorted(restored)
        tree = cKDTree(np.array([restored[k] for k in keys]))
        nearest = []
        for key in selected:
            # At most four native covalent neighbors and self are excluded.
            distances, indices = tree.query(restored[key], k=6)
            nearest.append(
                min(
                    float(d)
                    for d, i in zip(distances, indices, strict=True)
                    if key != keys[i] and tuple(sorted((key, keys[i]))) not in excluded
                )
            )
        return dict(close_pairs=close, minimum_nonbonded_angstrom=min(nearest))

    displacements = {k: float(np.linalg.norm(observed[k] - placed[k])) for k in common}
    calpha = {p: displacements["A", p, "CA"] for p in residues}
    next_pos = anchor if label == "n" else anchor + 1
    at = lambda p, n: placed[("A", p, n)] if ("A", p, n) in placed else fixed[("A", p, n)]
    cn = float(np.linalg.norm(at(next_pos - 1, "C") - at(next_pos, "N")))
    omega = _omega_degrees(
        [at(p, n) for p, n in ((next_pos - 1, "CA"), (next_pos - 1, "C"), (next_pos, "N"), (next_pos, "CA"))]
    )
    ca_error = float(np.sqrt(np.mean(np.square(list(calpha.values())))))
    heavy_error = float(np.sqrt(np.mean(np.square(list(displacements.values())))))
    common_packing, all_packing = packing(common), packing(generated)
    result = dict(
        pdb_sha256=sha256(original).hexdigest(),
        amber_identity=engine.identity.to_document(),
        selected_stock_pins=terminal_stock_pins(engine),
        chain="A",
        end=label,
        sequence=sequence,
        native_result=dict(return_code=record["return_code"], timed_out=record["timed_out"]),
        operand_sha256={
            key: sha256(record[key].encode("ascii")).hexdigest()
            for key in ("script", "topology", "restart", "stdout", "stderr")
        },
        total_original_heavy_atoms=len(observed),
        hidden_original_heavy_atoms=len(mask),
        fixed_heavy_atoms=len(fixed),
        placed_heavy_atoms=len(generated),
        held_out_common_heavy_atoms=len(common),
        predicted_only=[list(k) for k in sorted(set(generated) - mask)],
        observed_only=[list(k) for k in sorted(mask - set(generated))],
        transform=transform,
        native_census=census,
        ca_rmsd_angstrom=ca_error,
        common_heavy_rmsd_angstrom=heavy_error,
        ca_displacements_angstrom=calpha,
        junction_cn_angstrom=cn,
        junction_omega_degrees=omega,
        common_heavy_packing=common_packing,
        all_predicted_heavy_packing=all_packing,
    )
    (tmp_path / "control.read.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    assert (len(common), len(common_packing["close_pairs"])) == (expected[0], expected[3])
    assert ca_error == pytest.approx(expected[1], abs=0.0001)
    assert heavy_error == pytest.approx(expected[2], abs=0.0001)
    assert transform["determinant"] == pytest.approx(1) and transform["anchor_rmsd_angstrom"] < 0.15
    assert abs(cn - 1.33) < 0.02 and abs(abs(omega) - 180) < 4
