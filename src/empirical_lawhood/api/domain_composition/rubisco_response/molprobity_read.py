# SPDX-License-Identifier: MPL-2.0
"""Independent adjudication of a complete, coordinate-bound CCTBX component return."""

from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations
import json
import math

from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_projection import strict_json


COMPONENTS = ("ramalyze", "rotalyze", "cbetadev", "omegalyze", "bonds", "angles", "clashscore")
RESIDUE = COMPONENTS[:4]
SIDECHAIN_REFERENCE = frozenset("ARG ASN ASP CYS GLN GLU HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL".split())


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("External structural result lacks a finite numerical value")
    return value


def eligible_residue(component, r):
    if r["role"] != "PROTEIN":
        return False
    if component == "ramalyze":
        return 1 < r["position"] < r["chain_length"]
    if component == "omegalyze":
        return r["position"] > 1
    if component == "rotalyze":
        return r["component"] in SIDECHAIN_REFERENCE
    return r["component"] != "GLY"


def dimensions(table):
    rs = table["residues"]
    reskey = {(r["chain"], r["seq"], r["component"]): i for i, r in enumerate(rs)}
    atomkey = {(ri, name): i for i, (ri, name, _) in enumerate(table["atoms"])}
    if len(reskey) != len(rs) or len(atomkey) != len(table["atoms"]):
        raise ValueError("Ambiguous original material-to-report mapping")
    bonds = {tuple(x) for x in table["heavy_covalent_bonds"]}
    neighbors = defaultdict(set)
    for a, b in bonds:
        neighbors[a].add(b)
        neighbors[b].add(a)
    angles = {(a, mid, b) for mid, partners in neighbors.items() for a, b in combinations(sorted(partners), 2)}
    return reskey, atomkey, {"bonds": bonds, "angles": angles}


def select_residue(row, keys, *, prefix=""):
    if str(row[prefix + "altloc"]).strip() or str(row[prefix + "icode"]).strip():
        raise ValueError("External row substituted an alternate or insertion")
    key = (row[prefix + "chain_id"].strip(), int(row[prefix + "resseq"]), row[prefix + "resname"].strip())
    if key not in keys:
        raise ValueError("External row names a residue absent from the original exported material")
    return keys[key]


def row_atoms(row, component, reskey, atomkey):
    if component == "clashscore":
        return tuple(atomkey[select_residue(row, reskey, prefix=p), row[p + "name"].strip()] for p in ("", "target_"))
    count = 2 if component == "bonds" else 3
    fields = ("chain_id", "resseq", "resname", "altloc", "icode", "name")
    if any(len(row["atoms_" + field]) != count for field in fields):
        raise ValueError("External covalent row has an incorrect atom census")
    atoms = []
    for i in range(count):
        sub = {field: row["atoms_" + field][i] for field in fields}
        atoms.append(atomkey[select_residue(sub, reskey), sub["name"].strip()])
    return tuple(atoms)


def assessed_result(component, row, reskey, atomkey):
    if type(row["outlier"]) is not bool:
        raise ValueError("External validation classification is missing")
    native = row["outlier"]
    if component in RESIDUE:
        ri = select_residue(row, reskey)
        if component == "ramalyze":
            category = row["rama_type"].upper()
            if category not in {"FAVORED", "ALLOWED", "OUTLIER"} or native != (category == "OUTLIER"):
                raise ValueError("Unclassified or inconsistent original Ramachandran result")
        elif component == "rotalyze":
            category = row["evaluation"].upper()
            if category not in {"FAVORED", "ALLOWED", "OUTLIER"} or native != (category == "OUTLIER"):
                raise ValueError("Unclassified or incomplete original rotamer result")
        elif component == "cbetadev":
            if native != (finite(row["deviation"]) >= 0.25):
                raise ValueError("Inconsistent C-beta deviation classification")
            category = "OUTLIER" if native else "IN_RANGE"
        else:
            category = row["omega_type"].upper()
            if category not in ("TRANS", "CIS", "TWISTED"):
                raise ValueError("Unclassified peptide conformation")
            if category == "CIS" and row["resname"].strip() == "PRO":
                category = "CIS_PRO"
            native = category in {"CIS", "TWISTED"}
        return ri, (ri,), native, category
    atoms = row_atoms(row, component, reskey, atomkey)
    if len(set(atoms)) != len(atoms):
        raise ValueError("External structural term repeats one atom")
    # Pair/triple direction is arbitrary, the middle atom of an angle is fixed.
    key = min(atoms, atoms[::-1])
    if component == "clashscore":
        flag = finite(row["overlap"]) <= -0.4
    else:
        flag = abs(finite(row["score"])) >= 4.0
    if flag != native:
        raise ValueError("External geometric threshold disagrees with its primary value")
    return key, (), flag, "OUTLIER" if flag else "IN_RANGE"


def assess_component(directory, name, returned, census, table, indices, *, ramalyze_rows=None):
    """Publish optional Ramachandran rows only after their complete native stream passes."""
    if ramalyze_rows is not None and (name != "ramalyze" or ramalyze_rows):
        raise ValueError("Select an empty row collection for the original ramalyze component")
    selected_rows = {} if ramalyze_rows is not None else None
    parse_row = strict_json if selected_rows is not None else json.loads
    if returned.get("status") != "RETURNED":
        return dict(status="UNEVALUABLE", detail=returned)
    reskey, atomkey, covalent = indices
    rs, atoms = table["residues"], table["atoms"]
    expected = {i for i, r in enumerate(rs) if eligible_residue(name, r)} if name in RESIDUE else covalent.get(name, set())
    found, seen, outliers, groups, protected_hits = set(), set(), [], Counter(), Counter()
    other_heavy = []
    critical = sorted({mark for r in rs for mark in r["critical"]})
    digest, count, size = sha256(), 0, 0
    path = directory / (name + ".jsonl")
    if path.is_symlink() or not path.is_file():
        raise ValueError("Original structural component rows are missing")
    with path.open("rb") as stream:
        for raw in stream:
            if len(raw) > 256 * 1024:
                raise ValueError("Oversize original structural component row")
            digest.update(raw)
            size += len(raw)
            count += 1
            row = parse_row(raw)
            if str(row["model_id"]).strip() != census["model_id"]:
                raise ValueError("External row substitutes another coordinate model")
            key, residue_ids, flag, category = assessed_result(name, row, reskey, atomkey)
            if key in seen:
                raise ValueError("Duplicated original structural component row")
            seen.add(key)
            if selected_rows is not None:
                selected_rows[key] = row
            if key in expected:
                found.add(key)
            if (name in covalent and key not in expected and all(
                    atoms[i][2] != "H" and rs[atoms[i][0]]["role"] in ("PROTEIN", "LIGAND") for i in key)):
                other_heavy.append(key)
            if name not in RESIDUE:
                residue_ids = tuple({atoms[index][0] for index in key})
            protected = sorted({mark for i in residue_ids for mark in rs[i]["critical"]})
            for mark in protected:
                protected_hits[mark] += 1
            groups[category] += 1
            if flag:
                outliers.append(dict(row=count, native_key=key, residues=sorted(rs[i]["id"] for i in residue_ids),
                                     critical=protected, category=category))
    if (digest.hexdigest(), size, count) != (returned["sha256"], returned["bytes"], returned["rows"]):
        raise ValueError("Original structural rows differ from the authenticated returned component")
    # Clashscore is an outlier list over Probe's own contact selection. Empty is
    # only meaningful when the H-retained used model and a finite score exist.
    used = name not in ("bonds", "angles", "clashscore") or returned.get("used_atom_census") == census
    if name == "clashscore":
        score = finite(returned["clashscore"])
        expected_atoms = sum(rs[a[0]]["role"] != "WATER" for a in atoms)
        native_atoms, native_clashes = returned["native_nonwater_atoms"], returned["native_serious_clashes"]
        if type(native_atoms) is not int or type(native_clashes) is not int or native_atoms < 1 or native_clashes != count:
            raise ValueError("Clashscore substituted its original all-atom denominator or serious contact census")
        used = used and native_atoms == expected_atoms
        if score < 0 or not math.isclose(score, 1000 * native_clashes / native_atoms, rel_tol=1e-9, abs_tol=1e-12):
            raise ValueError("Clashscore differs from the reported overlap population")
    missing = sorted(expected - found)
    protected_missing = Counter()
    for key in missing:
        residue_ids = (key,) if name in RESIDUE else {atoms[index][0] for index in key}
        protected_missing.update({mark for i in residue_ids for mark in rs[i]["critical"]})
    scope = {}
    for mark in critical:
        scope[mark] = dict(reported_touching=protected_hits[mark], missing_assigned=protected_missing[mark],
                           outliers=sum(mark in row["critical"] for row in outliers))
    status = "UNEVALUABLE" if missing or other_heavy or not used else ("REVIEW_OUTLIERS" if outliers else "COVERED")
    if selected_rows is not None:
        ramalyze_rows.update(selected_rows)
    return dict(status=status, raw_rows=count, categories=dict(groups), expected=len(expected) if name != "clashscore" else None,
                joined=len(found) if name != "clashscore" else None, missing_native_keys=missing,
                protected_scope=scope, additional_organic_heavy_terms=other_heavy,
                reported_outlier_fraction=len(outliers)/count if count else None,
                used_atom_identity_verified=used if name not in RESIDUE else None, outliers=outliers,
                clashscore=score if name == "clashscore" else None,
                probe_source_nonwater_atoms=native_atoms if name == "clashscore" else None)


def assess_overall_score(report, components):
    """Reconstruct the official score on its native population and disclose its coverage."""
    unavailable = dict(status="UNEVALUABLE", score=None)
    native_score = report.get("cctbx_molprobity_score")
    if native_score is None or components["clashscore"]["status"] == "UNEVALUABLE":
        return unavailable
    percents = []
    populations = {}
    for name, category, field in (("ramalyze", "FAVORED", "native_favored"),
                                  ("rotalyze", "OUTLIER", "native_outliers")):
        row = components[name]
        if "raw_rows" not in row:
            return unavailable
        native = report["components"][name]
        total = row["raw_rows"]
        count = row["categories"].get(category, 0)
        if total <= 0 or total != native["native_total"] or count != native[field]:
            raise ValueError("MolProbity score has an inconsistent original residue denominator or numerator")
        if row["joined"] != total:
            raise ValueError("MolProbity score includes residues outside the selected source population")
        populations[name] = dict(reported=total, assigned=row["expected"])
        percents.append(100 * count / total)
    rama_favored, rotamer_outliers = percents
    clashscore = components["clashscore"]["clashscore"]
    score = (0.5 + 0.426 * math.log1p(clashscore) + 0.33 * math.log1p(max(0., rotamer_outliers - 1.))
             + 0.25 * math.log1p(max(0., 98. - rama_favored)))
    if not math.isclose(score, finite(native_score), rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("CCTBX MolProbity score differs from the independent component reconstruction")
    complete = all(pop["reported"] == pop["assigned"] for pop in populations.values())
    return dict(status="RECONSTRUCTED" if complete else "RECONSTRUCTED_NATIVE_POPULATION_ONLY",
                score=native_score if complete else None, reported_population_score=native_score,
                residue_populations=populations, clashscore=clashscore,
                rama_favored_percent=rama_favored, rotamer_outlier_percent=rotamer_outliers)


def assess_model(directory, table, report):
    census = report["input_census"]
    if (census["atom_count"] != len(table["atoms"]) or census["coordinate_array_sha256"] != table["coordinate_array_sha256"]
            or type(census["model_id"]) is not str or set(report["components"]) - set(COMPONENTS)):
        raise ValueError("External validator read a different selected native atom population")
    indices = dimensions(table)
    results = {name: assess_component(directory, name, report["components"].get(name, {"status": "NOT_RETURNED"}),
                                      census, table, indices) for name in COMPONENTS}
    incomplete = [name for name, row in results.items() if row["status"] == "UNEVALUABLE"]
    adverse = [name for name, row in results.items() if row.get("outliers")]
    return dict(status="UNEVALUABLE" if incomplete else ("REVIEW_OUTLIERS" if adverse else "COVERED"),
                incomplete_components=incomplete, components_with_outliers=adverse, components=results,
                molprobity_score=assess_overall_score(report, results),
                interpretation="EMPIRICAL_GEOMETRY_TRIAGE_ONLY", metal_coordination_and_ligand_chemistry="UNEVALUABLE",
                catalysis_and_paired_forecast="UNEVALUABLE")
