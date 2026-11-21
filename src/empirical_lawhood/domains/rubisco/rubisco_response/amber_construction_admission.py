# SPDX-License-Identifier: MPL-2.0
"""Independent admission of a complete Amber construction's retained endpoint.

These checks consume original native bytes. They never invoke a minimizer and
never equate minimization, assignment or a geometry screen with an ensemble.
"""

from hashlib import sha256
from io import BytesIO
import json
import math

import numpy as np

from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import heavy_pdb_rows, initial_heavy_pdb
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import assess_molecular_geometry, geometry_terms_from_amber


INITIAL_ASSESSMENT_FILES = tuple(sorted((
    "dry.prmtop", "dry.inpcrd", "model.prmtop", "model.inpcrd", "stdout.txt", "stderr.txt",
    "library-heavy.pdb", "relaxed.inpcrd", "relaxation.json", "final-forces-kj-mol-nm.npy",
    "mutation-construction.json", "force-assignment.json")))


def _document(raw):
    def refuse(value):
        raise ValueError("construction diagnostic contains nonfinite JSON: "+value)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("construction diagnostic duplicates a JSON key")
            result[key] = value
        return result
    result = json.loads(raw, parse_constant=refuse, object_pairs_hook=unique)
    if type(result) is not dict:
        raise ValueError("construction diagnostic must retain its complete document")
    return result


def library_heavy_correspondence(model, files, *, construction_seed, construction_platform="CPU", construction_threads=1):
    """Only declared I95M CG/SD/CE coordinates may change before Amber.

    Atom names, elements, residue identities, anchors and protected chemistry
    remain exact. Whole-system displacement is allowed only in the separately
    retained and independently assessed final minimization endpoint.
    """
    original = heavy_pdb_rows(initial_heavy_pdb(model))
    revised = heavy_pdb_rows(files["library-heavy.pdb"].decode("ascii"))
    if tuple(row[:5] for row in revised) != tuple(row[:5] for row in original):
        raise ValueError("library construction changes the selected heavy chemical census")
    small = {chain.chain_id for chain in model.material.chains if chain.subunit == "SSU"}
    chains = tuple(physical for physical, sequence in model.chain_map if sequence in small)
    mutations = chains if model.name.endswith("i95m") else ()
    allowed = {(chain, 95, atom) for chain in mutations for atom in ("CG", "SD", "CE")}
    if mutations and (len(mutations) != 8 or len(set(mutations)) != 8):
        raise ValueError("library mutation loses the all-eight SSU population")
    observed = set()
    for before, after in zip(original, revised, strict=True):
        key = before[0], before[1], before[3]
        if key in allowed:
            if before[2] != "MET":
                raise ValueError("library mutation changes its declared mutant chemistry")
            observed.add(key)
        elif before[5] != after[5]:
            raise ValueError("library mutation moves an inherited or protected heavy atom")
    if observed != allowed:
        raise ValueError("library mutation omits a selected mutant sidechain atom")
    report = _document(files["mutation-construction.json"])
    expected = "PDBFIXER_APPLY_MUTATIONS_ILE95MET" if mutations else "WT_NO_MUTATION"
    if (report.get("method") != expected
            or report.get("mutations") != [[chain, "ILE-95-MET"] for chain in mutations]
            or report.get("seed") != construction_seed
            or mutations and (report.get("constructed_sidechain_atom_count") != len(allowed)
                or report.get("protected_atom_count") != len(original)-len(allowed)
                or report.get("platform") != construction_platform
                or type(report.get("threads")) is not int
                or report.get("threads") != construction_threads
                or report.get("replace_nonstandard_residues") is not False
                or report.get("remove_heterogens") is not False)):
        raise ValueError("library mutation diagnostic changes its declared scope")
    return revised


def assess_retained_force_assignment(raw_topology, raw_assignment):
    from empirical_lawhood.domains.rubisco.rubisco_response.amber_mm_assignment import assess_amber_force_assignment
    assignment = _document(raw_assignment)
    if set(assignment) != {"snapshot", "masses_dalton", "assessment"}:
        raise ValueError("construction force assignment loses its complete raw comparison")
    checked = assess_amber_force_assignment(raw_topology, assignment["snapshot"], assignment["masses_dalton"])
    if assignment["assessment"] != json.loads(json.dumps(checked)):
        raise ValueError("construction force assignment differs from independent raw assessment")
    return checked


def require_geometry_report_correspondence(declared, independent):
    """Compare semantic findings exactly and allow only numerical roundoff.

    SVD plane residuals and accumulated trigonometric diagnostics are not a
    bitwise portable replay contract. Relative tolerance is 1e-12. Absolute
    floors are 1e-12 Angstrom/dimensionless, 1e-10 degree and 1e-9 kJ/mol for
    the complete torsion sum. Diagnostic values use 1e-10 in their named units.
    These bounds never alter admission thresholds: dispositions, findings,
    counts, affected atoms and policy must agree exactly before comparison.
    """
    expected = json.loads(json.dumps(independent))
    def same(actual, value):
        if type(actual) is not type(value):
            return False
        if type(value) is dict:
            return set(actual) == set(value) and all(same(actual[key], value[key]) for key in value)
        if type(value) is list:
            return len(actual) == len(value) and all(same(a, b) for a, b in zip(actual, value, strict=True))
        return actual == value
    if type(declared) is not dict or set(declared) != set(expected):
        raise ValueError("construction geometry changes its complete diagnostic schema")
    semantic = set(expected)-{"metrics", "diagnostics"}
    if any(not same(declared[key], expected[key]) for key in semantic):
        raise ValueError("construction geometry changes its independent disposition, findings, census or policy")
    floors = {"maximum_angle_deviation_degrees": 1e-10, "torsion_energy_kj_mol": 1e-9}
    actual_metrics, metrics = declared["metrics"], expected["metrics"]
    if type(actual_metrics) is not dict or set(actual_metrics) != set(metrics):
        raise ValueError("construction geometry changes its complete metric census")
    def number(actual, value, absolute):
        return (type(actual) in (int, float) and math.isfinite(actual)
            and math.isclose(actual, value, rel_tol=1e-12, abs_tol=absolute))
    for key, value in metrics.items():
        if type(value) is int:
            matched = type(actual_metrics[key]) is int and actual_metrics[key] == value
        else:
            matched = number(actual_metrics[key], value, floors.get(key, 1e-12))
        if not matched:
            raise ValueError("construction geometry metric exceeds its numerical roundoff contract: "+key)
    diagnostics = declared["diagnostics"]
    if type(diagnostics) is not list or len(diagnostics) != len(expected["diagnostics"]):
        raise ValueError("construction geometry changes its complete retained diagnostic census")
    for actual, value in zip(diagnostics, expected["diagnostics"], strict=True):
        if (type(actual) is not dict or set(actual) != set(value)
                or any(actual[key] != value[key] for key in value if key != "value")
                or not number(actual["value"], value["value"], 1e-10)):
            raise ValueError("construction geometry diagnostic differs beyond numerical roundoff")


def assess_retained_endpoint(source, model, files, atom_count, original_box):
    """Recompute full geometry, gradient and force-assignment admission."""
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import read_initial_coordinates

    points, box = read_initial_coordinates(files["relaxed.inpcrd"].decode("ascii"), atom_count, periodic=True)
    if box != original_box:
        raise ValueError("construction minimization changes the declared periodic cell")
    stream = BytesIO(files["final-forces-kj-mol-nm.npy"])
    forces = np.load(stream, allow_pickle=False)
    if (forces.shape != (atom_count, 3) or forces.dtype != np.dtype("float64")
            or not np.isfinite(forces).all() or stream.read(1)):
        raise ValueError("construction endpoint loses complete finite double forces")
    maximum = float(np.max(np.abs(forces)))
    rms = float(np.sqrt(np.mean(forces**2)))
    quality = assess_molecular_geometry(np.asarray(points, float), geometry_terms_from_amber(files["model.prmtop"]),
        policy=source.geometry_quality, cell_angstrom=tuple(float(v) for v in box[:3]))
    checked_assignment = assess_retained_force_assignment(files["model.prmtop"], files["force-assignment.json"])
    report = _document(files["relaxation.json"])
    expected = {"numerical_method": "OPENMM_LOCAL_ENERGY_MINIMIZER_COMPLETE_AMBER_V1",
        "model": model.identity.to_document(), "platform": source.construction_platform,
        "threads": source.construction_threads,
        "platform_properties": {"Threads": str(source.construction_threads), "DeterministicForces": "true"} if source.construction_platform == "CPU" else {},
        "all_original_force_groups": True,
        "projected_pair_kernel": False, "iteration_limit_is_convergence": False,
        "maximum_iterations": source.maximum_minimization_iterations,
        "relaxed_coordinates_sha256": sha256(files["relaxed.inpcrd"]).hexdigest(),
        "final_force_coordinates": "EXACT_RETAINED_RELAXED_INPCRD", "atom_count": atom_count,
        "all_atoms_mobile": True, "constraints": "NONE", "rigid_water": False,
        "nonbonded_cutoff_angstrom": str(source.minimization_nonbonded_cutoff_angstrom),
        "ewald_error_tolerance": str(source.minimization_ewald_tolerance),
        "ensemble_admission": "UNEVALUABLE", "force_accuracy_admission": "UNEVALUABLE", "rate_admission": "UNEVALUABLE"}
    if (type(report.get("threads")) is not int
            or any(report.get(key) != json.loads(json.dumps(value)) for key, value in expected.items())):
        raise ValueError("construction endpoint diagnostic changes its selected method or exact source binding")
    for key, value in (("maximum_mobile_gradient_kj_mol_nm", maximum), ("rms_mobile_gradient_kj_mol_nm", rms)):
        if type(report.get(key)) not in (float, int) or not math.isclose(report[key], value, rel_tol=1e-13, abs_tol=0):
            raise ValueError("construction endpoint gradient differs from retained complete forces")
    tolerance = report.get("requested_openmm_rms_tolerance_kj_mol_nm")
    bound = float(source.maximum_minimization_gradient_kj_mol_nm)/math.sqrt(3*atom_count)
    if type(tolerance) not in (float, int) or not math.isfinite(tolerance) or not 0 < tolerance <= bound:
        raise ValueError("construction minimizer's RMS target cannot bound the selected maximum gradient")
    require_geometry_report_correspondence(report.get("final_geometry"), quality)
    findings = set()
    if maximum > float(source.maximum_minimization_gradient_kj_mol_nm):
        findings.add("whole-system-final-gradient")
    if quality["disposition"] != "SCREEN_PASSED":
        findings.add("whole-system-final-geometry")
    if report.get("success") is not (not findings):
        raise ValueError("construction success disagrees with its independently measured endpoint")
    return points, tuple(sorted(findings)), {"maximum_gradient_kj_mol_nm": maximum,
        "rms_gradient_kj_mol_nm": rms, "geometry": quality, "force_assignment": checked_assignment}
