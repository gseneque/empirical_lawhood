# SPDX-License-Identifier: MPL-2.0
"""One preregistered stock-fragment hypothesis for unresolved Gp parent termini."""

from decimal import Decimal
from hashlib import sha256
import json
import math
import re

import numpy as np
from scipy.spatial import cKDTree

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import (
    assigned_census_supported_inactive14,
    read_prmtop,
)
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.coordinate_plan import THREE
from empirical_lawhood.domains.rubisco.rubisco_response.gp_active_scaffold import proper_rigid_fit
from empirical_lawhood.domains.rubisco.rubisco_response.gp_constructed_geometry import (
    origin_mobility,
    replace_heavy_coordinates,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_heavy_geometry import heavy_stereochemistry
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import heavy_pdb_rows
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import (
    _residues,
    read_initial_coordinates,
)


METHOD = "AMBER_FF14SB_STOCK_FRAGMENTS_PPII_MET1_OPENMM_MINIMIZATION"
TEMPLATE = "pdbfixer/templates/MET.pdb"
STOCK = tuple(
    sorted(
        "toolchain/dat/leap/" + n
        for n in (
            "cmd/leaprc.protein.ff14SB",
            "parm/parm10.dat",
            "parm/frcmod.ff14SB",
            "lib/amino12.lib",
            "lib/aminoct12.lib",
            "lib/aminont12.lib",
        )
    )
)
PHI, PSI = -75.0, 145.0
MAX_ANCHOR_RMSD, MAX_ANCHOR_ERROR = 0.15, 0.25
PACKING_ANGSTROM = 2.0
MAXIMUM_BUNDLE_BYTES = 4 * 2**20
MET_NAMES = ("CG", "SD", "CE")
MAX_FRAGMENT_SECONDS = 30


class TerminalCandidateRejected(ValueError):
    def __init__(self, reasons, diagnostics):
        self.diagnostics = diagnostics
        super().__init__("Selected terminal candidate refused: " + ", ".join(reasons))


def terminal_stock_pins(engine):
    selected = tuple(
        sorted((r.relative_path, r.byte_count, r.sha256) for r in engine.files if r.relative_path in STOCK)
    )
    if tuple(row[0] for row in selected) != STOCK or any(row[1] <= 0 for row in selected):
        raise ValueError(
            "Terminal fragments require the selected protein leaprc, force parameters and all three amino-acid libraries"
        )
    return selected


def met_template_pin(engine):
    (pin,) = (r for r in engine.files if r.relative_path == TEMPLATE)
    return pin.relative_path, pin.byte_count, pin.sha256


def plans(origin):
    chains = origin["complete_chains"]
    large = tuple(c for c in chains if c["subunit"] == "lsu")
    small = tuple(c for c in chains if c["subunit"] == "ssu")
    if (
        len(chains) != 16
        or len(large) != 8
        or len(small) != 8
        or len({c["chain"] for c in chains}) != 16
        or len({c["sequence"] for c in large}) != 1
        or len(large[0]["sequence"]) != 493
        or any(c["sequence"][0] != "M" for c in small)
    ):
        raise ValueError("Stock-terminal selection requires the exact M1-WT L8S8 source")
    sequence = large[0]["sequence"]
    return {"lsu-n": sequence[:16], "lsu-c": sequence[484:]}, large, small


def fragment_script(sequence):
    if len(sequence) < 3 or any(letter not in THREE for letter in sequence):
        raise ValueError("Amber terminal fragment needs a complete unambiguous standard peptide sequence")
    components = ["HIE" if x == "H" else THREE[x] for x in sequence]
    components[0] = "N" + components[0]
    components[-1] = "C" + components[-1]
    links = list(range(1, len(sequence)))
    adjustable = [i for i in links if sequence[i] != "P"]
    # LEaP attaches a Pro ring with a native, ring-dependent phi. Imposing
    # the ordinary phi on it deforms the closed ring. Preserve that linkage.
    positions = " ".join(map(str, links))
    phi_positions = " ".join(map(str, adjustable))
    lines = [
        "source leaprc.protein.ff14SB",
        "q = sequence { " + " ".join(components) + " }",
        "impose q { " + positions + ' } { { "N" "CA" "C" "N" 145.0 } }',
    ]
    if adjustable:
        lines.append("impose q { " + phi_positions + ' } { { "C" "N" "CA" "C" -75.0 } }')
    return "\n".join((*lines, "saveAmberParm q fragment.prmtop fragment.inpcrd", "quit", ""))


def _fragment_geometry(sequence, record):
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_assessment import (
        _omega_degrees,
    )

    charge = sum(sequence.count(a) for a in "KR") - sum(sequence.count(a) for a in "DE")
    warning_lines = re.findall(r"^.*: Warning!\n([^\n]+)", record["stdout"], re.MULTILINE)
    expected = [] if not charge else [f"The unperturbed charge of the unit ({charge:.6f}) is not zero."]
    summary = re.search(r"Exiting LEaP: Errors = 0; Warnings = (\d+); Notes = \d+\.\s*$", record["stdout"])
    if (
        record["script"] != fragment_script(sequence)
        or record["return_code"] != 0
        or record["timed_out"]
        or record["stderr"].strip()
        or warning_lines != expected
        or summary is None
        or int(summary[1]) != len(expected)
    ):
        raise ValueError(
            "Returned Amber fragment has a changed script, missing result or unaccounted LEaP warning"
        )
    top = read_prmtop(record["topology"])
    census = assigned_census_supported_inactive14(top)
    net = sum(census["charges_scaled"]) / Decimal("18.2223")
    if abs(net - Decimal(charge)) > Decimal("0.0005"):
        raise ValueError("Returned Amber fragment changes its declared sequence and terminal net charge")
    xyz, _ = read_initial_coordinates(record["restart"], census["term_census"]["atoms"], periodic=False)
    native = _residues(census)
    if [name for name, _ in native] != [("HIE" if a == "H" else THREE[a]) for a in sequence]:
        raise ValueError("Amber stock topology changes a selected fragment's sequence")
    points, names = {}, {}
    rows = []
    for p, (component, atoms) in enumerate(native, 1):
        for name, i in atoms.items():
            z = census["atomic_numbers"][i]
            if z == 1:
                continue
            key = p, name
            names[i] = key
            rows.append(("A", p, component, name, str(z), xyz[i]))
            points[key] = np.array(xyz[i], dtype=float)
    centres, bad = heavy_stereochemistry(rows, minimum_volume=Decimal("0.01"))
    if not centres or bad:
        raise ValueError("Original stock fragment has inverted or indeterminate amino-acid stereochemistry")
    bonds = {}
    for a, b, k in census["indexed_bonded_terms"]["BONDS_WITHOUT_HYDROGEN"]:
        ia, ib = a // 3, b // 3
        pair = tuple(sorted((names[ia], names[ib])))
        target = float(top["BOND_EQUIL_VALUE"][k - 1])
        if pair in bonds or abs(np.linalg.norm(points[pair[0]] - points[pair[1]]) - target) > 0.15:
            raise ValueError(
                "Amber fragment has duplicate or grossly strained native heavy covalent geometry"
            )
        bonds[pair] = target

    def torsion(keys):
        return _omega_degrees([points[k] for k in keys])

    for i in range(1, len(sequence)):
        phi = torsion(((i, "C"), (i + 1, "N"), (i + 1, "CA"), (i + 1, "C")))
        psi = torsion(((i, "N"), (i, "CA"), (i, "C"), (i + 1, "N")))
        omega = torsion(((i, "CA"), (i, "C"), (i + 1, "N"), (i + 1, "CA")))
        phi_ok = -85 <= phi <= -50 if sequence[i] == "P" else abs(math.remainder(phi - PHI, 360)) <= 0.25
        if (
            not phi_ok
            or abs(math.remainder(psi - PSI, 360)) > 0.25
            or abs(math.remainder(omega - 180, 360)) > 0.25
        ):
            raise ValueError("Original fragment failed the selected phi/psi and trans peptide torsion census")
    return (
        points,
        bonds,
        dict(
            residues=len(native),
            heavy_atoms=len(points),
            heavy_bonds=len(bonds),
            signed_stereocentres=centres,
            checked_backbone_dihedrals=3 * (len(sequence) - 1),
            signed_net_charge_e=str(net),
            declared_charge_warning=bool(expected),
        ),
    )


def _met_points(text, engine):
    _, count, reference = met_template_pin(engine)
    raw = text.encode("ascii")
    if len(raw) != count or sha256(raw).hexdigest() != reference:
        raise ValueError("Returned methionine template differs from the selected PDBFixer installation")
    points = {}
    for line in text.splitlines():
        if line.startswith("ATOM  "):
            name = line[12:16].strip()
            if name in points or line[17:20] != "MET" or int(line[22:26]) != 1:
                raise ValueError("PDBFixer MET template changes residue or atom identity")
            points[name] = np.array([float(line[i : i + 8]) for i in (30, 38, 46)])
    if set(points) != {"N", "CA", "C", "O", "CB", *MET_NAMES} or not all(
        np.isfinite(p).all() for p in points.values()
    ):
        raise ValueError("PDBFixer MET template has an incomplete finite heavy census")
    return points


def aligned_copy(fragment, original, anchors, keys):
    """Named source/target points; proper rigid transforms only, no post-fit adjustment."""
    reference = np.array([fragment[k] for k in anchors])
    target = np.array([original[k] for k in anchors])
    rotation, translation, rmsd = proper_rigid_fit(reference, target)
    det = float(np.linalg.det(rotation))
    errors = np.linalg.norm(reference @ rotation + translation - target, axis=1)
    if not np.isclose(det, 1, atol=1e-10, rtol=0) or not np.allclose(
        rotation.T @ rotation, np.eye(3), atol=1e-10, rtol=0
    ):
        raise ValueError("Fragment alignment lost proper rotation")
    return {key: fragment[key] @ rotation + translation for key in keys}, dict(
        anchor_keys=[list(k) for k in anchors],
        rotation=rotation.tolist(),
        translation_angstrom=translation.tolist(),
        determinant=det,
        anchor_rmsd_angstrom=rmsd,
        maximum_anchor_error_angstrom=float(np.max(errors)),
    )


def _packing(points, placed, bonded):
    keys = sorted(points)
    indices = {k: i for i, k in enumerate(keys)}
    xyz = np.array([points[k] for k in keys], dtype=float)
    tree = cKDTree(xyz)
    contacts = []
    for key in sorted(placed):
        i = indices[key]
        for j in sorted(tree.query_ball_point(xyz[i], PACKING_ANGSTROM)):
            other = keys[j]
            if key == other or (other in placed and other < key) or tuple(sorted((key, other))) in bonded:
                continue
            distance = float(np.linalg.norm(xyz[i] - xyz[j]))
            if distance < PACKING_ANGSTROM:
                contacts.append(dict(first=list(key), second=list(other), distance_angstrom=distance))
    return contacts


def _check_stock_shape(sequence, points, stocks):
    from empirical_lawhood.domains.rubisco.rubisco_response.terminal_templates import read_templates

    templates = {}
    for name in ("amino12", "aminoct12", "aminont12"):
        templates.update(read_templates(stocks["toolchain/dat/leap/lib/" + name + ".lib"]))
    worst = 0.0
    for p, letter in enumerate(sequence, 1):
        code = ("N" if p == 1 else "C" if p == len(sequence) else "") + (
            "HIE" if letter == "H" else THREE[letter]
        )
        reference, _ = templates[code]
        observed = {name: value for (index, name), value in points.items() if index == p}
        if set(reference) != set(observed):
            raise ValueError("Amber sequence product changes the selected OFF heavy-atom census")
        anchors = ("N", "CA", "C")
        rotation, translation, _ = proper_rigid_fit(
            [reference[n] for n in anchors], [observed[n] for n in anchors]
        )
        # O and OXT follow the independently imposed next peptide psi.
        error = max(
            float(np.linalg.norm(reference[n] @ rotation + translation - observed[n]))
            for n in observed
            if n not in ("O", "OXT")
        )
        if error > 0.15:
            raise ValueError("Amber fragment changes the selected stock side-chain shape")
        worst = max(error, worst)
    return worst


def _joined_candidate(source, origin, fragment_records, template, stocks):
    selected, large, small = plans(origin)
    if set(fragment_records) != set(selected):
        raise ValueError("Terminal selection is missing its complete two fragment census")
    atoms, constructed = origin_mobility(source.heavy_pdb, origin)
    native_points = {(a["chain"], a["position"], a["atom"]): np.array(a["xyz"], float) for a in atoms}
    components = {(a["chain"], a["position"]): a["component"] for a in atoms}
    permitted = set(constructed)
    placed, bonded, transforms, junctions, logs = {}, set(), [], [], {}
    geometries = {n: _fragment_geometry(seq, fragment_records[n]) for n, seq in selected.items()}
    for name, (lo, anchor, span, anchor_atoms) in (
        ("lsu-n", (1, 15, range(1, 15), ("N", "CA", "C"))),
        ("lsu-c", (485, 486, range(487, 494), ("CA", "C", "O"))),
    ):
        coords, bonds, logs[name] = geometries[name]
        logs[name]["maximum_stock_residue_shape_error_angstrom"] = _check_stock_shape(
            selected[name], coords, stocks
        )
        for row in large:
            ch = row["chain"]
            chain_points = {(ch, lo + p - 1, n): x for (p, n), x in coords.items()}
            movable = sorted(k for k in chain_points if k[1] in span)
            anchor_keys = [(ch, anchor, n) for n in anchor_atoms]
            if set(movable) - permitted or any(k in permitted for k in anchor_keys):
                raise ValueError(
                    "Parent terminal selection substitutes an observed atom or lacks its inherited anchor"
                )
            for p in span:
                if components.get((ch, p)) != (
                    "HIS" if row["sequence"][p - 1] == "H" else THREE[row["sequence"][p - 1]]
                ):
                    raise ValueError("Amber fragment differs from original classified heavy component")
            added, transform = aligned_copy(chain_points, native_points, anchor_keys, movable)
            placed.update(added)
            transforms.append(dict(fragment=name, chain=ch, constructed=len(added), **transform))
            for ((p, a), (q, b)), distance in bonds.items():
                ka, kb = (ch, lo + p - 1, a), (ch, lo + q - 1, b)
                bonded.add(tuple(sorted((ka, kb))))
                if abs(ka[1] - kb[1]) == 1 and ((ka in permitted) != (kb in permitted)):
                    junctions.append((ka, kb, distance))
    met = _met_points(template, source.numeric_engine)
    met_bonds = {
        frozenset((a, b)): v
        for ((p, a), (q, b)), v in geometries["lsu-n"][1].items()
        if p == q == 1 and ({a, b} & set(MET_NAMES))
    }
    if set(met_bonds) != {frozenset(("CB", "CG")), frozenset(("CG", "SD")), frozenset(("SD", "CE"))}:
        raise ValueError(
            "Selected N-Met library does not identify the original distal side chain connectivity"
        )
    for row in small:
        ch = row["chain"]
        if components.get((ch, 1)) != "MET":
            raise ValueError("SSU Met1 template cannot substitute another source residue")
        fragment = {(ch, 1, name): point for name, point in met.items()}
        anchor_keys = [(ch, 1, n) for n in ("N", "CA", "C", "CB")]
        move = [(ch, 1, n) for n in MET_NAMES]
        if any(k in permitted for k in anchor_keys) or not set(move) <= permitted:
            raise ValueError("SSU template changes its strictly selected atom population")
        added, transform = aligned_copy(fragment, native_points, anchor_keys, move)
        placed.update(added)
        transforms.append(dict(fragment="ssu-met1", chain=ch, constructed=len(added), **transform))
        for pair, distance in met_bonds.items():
            a, b = sorted(pair)
            ka, kb = (ch, 1, a), (ch, 1, b)
            bonded.add(tuple(sorted((ka, kb))))
            if (ka in permitted) != (kb in permitted):
                junctions.append((ka, kb, distance))
    if set(placed) != permitted or len(junctions) != 24:
        raise ValueError("Terminal construction changed the complete movable or covalent junction census")
    candidate = replace_heavy_coordinates(source.heavy_pdb, placed, constructed)
    rows = heavy_pdb_rows(candidate)
    actual = {(c, p, n): np.array(x, float) for c, p, _, n, _, x in rows}
    contacts = _packing(actual, permitted, bonded)
    junction_report = []
    for a, b, equilibrium in junctions:
        distance = float(np.linalg.norm(actual[a] - actual[b]))
        junction_report.append(
            dict(
                first=list(a),
                second=list(b),
                amber_equilibrium_angstrom=equilibrium,
                distance_angstrom=distance,
                absolute_error_angstrom=abs(distance - equilibrium),
            )
        )
    measured, invalid = heavy_stereochemistry(rows, minimum_volume=Decimal("0.01"))
    reasons = []
    if any(
        x["anchor_rmsd_angstrom"] > MAX_ANCHOR_RMSD or x["maximum_anchor_error_angstrom"] > MAX_ANCHOR_ERROR
        for x in transforms
    ):
        reasons.append("anchor residual")
    if any(x["absolute_error_angstrom"] > 0.15 for x in junction_report):
        reasons.append("covalent fragment junction")
    if contacts:
        reasons.append("nonbonded heavy packing")
    if not measured or invalid:
        reasons.append("signed heavy stereocentre")
    details = dict(
        kind="original-stock-peptides-with-proper-anchor-placement",
        method=METHOD,
        declared_phi_psi_degrees=[PHI, PSI],
        proline_phi="native Amber closed-ring linkage [-85,-50] degrees",
        packing_floor_angstrom=PACKING_ANGSTROM,
        copies=transforms,
        fragment_censuses=logs,
        junctions=junction_report,
        packing_contacts=contacts,
        full_signed_stereocentres=measured,
        invalid_chiral_centres=[(list(k), str(volume)) for k, volume in invalid],
    )
    if reasons:
        raise TerminalCandidateRejected(reasons, details)
    return candidate, (details,), constructed


def replay_terminal_fragments(source, bundle_raw):
    """Rebuild the selected geometry from immutable returned operands without a native call."""
    if not isinstance(bundle_raw, bytes) or not 0 < len(bundle_raw) <= MAXIMUM_BUNDLE_BYTES:
        raise ValueError("Invalid bounded terminal fragment operand")

    def unique(items):
        result = dict(items)
        if len(result) != len(items):
            raise ValueError("Terminal fragment receipt repeats a field")
        return result

    try:
        data = json.loads(bundle_raw, object_pairs_hook=unique)
        return _replay_operand(source, data)
    except (KeyError, IndexError, AttributeError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("Malformed terminal fragment or native result field") from error


def _replay_operand(source, data):
    required = {
        "method",
        "source",
        "amber_engine",
        "numerical_engine",
        "stock_pins",
        "met_template_pin",
        "stock_bytes",
        "met_template",
        "fragments",
    }
    if not isinstance(data, dict) or set(data) not in (required, required | {"refusal"}):
        raise ValueError("Terminal fragment receipt changes its selected operand fields")
    if (
        data["method"] != METHOD
        or data["source"] != source.identity.to_document()
        or data["amber_engine"] != source.amber_engine.identity.to_document()
        or data["numerical_engine"] != source.numeric_engine.fingerprint()
        or data["stock_pins"] != [list(row) for row in terminal_stock_pins(source.amber_engine)]
        or data["met_template_pin"] != list(met_template_pin(source.numeric_engine))
    ):
        raise ValueError("Terminal fragment read substitutes its source, tool or selected chemical library")
    stocks = data["stock_bytes"]
    if set(stocks) != set(STOCK) or any(
        len(stocks[p].encode("ascii")) != n or sha256(stocks[p].encode("ascii")).hexdigest() != h
        for p, n, h in terminal_stock_pins(source.amber_engine)
    ):
        raise ValueError(
            "Terminal fragment read substituted an original installed force or amino-acid library"
        )
    try:
        result = _joined_candidate(
            source, json.loads(source.origin_json), data["fragments"], data["met_template"], stocks
        )
    except TerminalCandidateRejected as error:
        expected = dict(
            error_type=type(error).__name__, message=str(error), candidate_diagnostics=error.diagnostics
        )
        if "refusal" in data and data["refusal"] != json.loads(json.dumps(expected, allow_nan=False)):
            raise ValueError("Terminal refusal differs from reconstructed candidate diagnostics") from error
        raise
    if "refusal" in data:
        raise ValueError("Terminal refusal contradicts a successfully reconstructed candidate")
    return result
