# SPDX-License-Identifier: MPL-2.0
"""Adverse composition controls for newly retained construction endpoints."""
from decimal import Decimal as D
from hashlib import sha256
from io import BytesIO
import json
import math
from types import SimpleNamespace as NS

import numpy as np
import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response.library_construction import amber_restart_text
from empirical_lawhood.domains.rubisco.rubisco_response import amber_construction_admission as owner
from empirical_lawhood.domains.rubisco.rubisco_response.amber_construction_log import assess_leap_diagnostics
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import GeometryTerms, MolecularGeometryPolicy, assess_molecular_geometry


def test_leap_exit_zero_and_geometry_warning_do_not_admit_the_output():
    raw = b"WARNING: Close contact of 0.349 angstroms between protein hydrogens.\nExiting LEaP: Errors = 0; Warnings = 1; Notes = 0.\n"
    assert assess_leap_diagnostics(raw, b"")["disposition"] == "REJECTED"
    explained = assess_leap_diagnostics(raw, b"", complete_endpoint_satisfied=True)
    assert explained["disposition"] == "SCREEN_PASSED"
    assert len(explained["resolved_by_complete_endpoint"]) == 1
    assert explained["stdout_sha256"] == sha256(raw).hexdigest()


@pytest.mark.parametrize("line", ("WARNING: Could not find a bond parameter.", "WARNING: Unknown residue.",
    "WARNING: Missing parameter.", "FATAL: Close contact cannot be resolved."))
def test_geometry_or_charge_success_never_waives_parameter_errors(line):
    raw = (line+"\nExiting LEaP: Errors = 0; Warnings = 1; Notes = 0.\n").encode()
    report = assess_leap_diagnostics(raw, b"", complete_endpoint_satisfied=True, final_charge_balanced=True)
    assert report["disposition"] == "REJECTED" and report["unresolved_diagnostics"]


def test_missing_or_unexplained_warning_population_cannot_be_waived():
    assert assess_leap_diagnostics(b"", b"")["disposition"] == "REJECTED"
    report = assess_leap_diagnostics(b"Exiting LEaP: Errors = 0; Warnings = 2; Notes = 0.\n", b"", complete_endpoint_satisfied=True)
    assert report["disposition"] == "REJECTED"


def test_unsolvated_integral_charge_requires_its_explicit_selected_context():
    raw = b"WARNING: The unperturbed charge of the unit is not zero.\nExiting LEaP: Errors = 0; Warnings = 1; Notes = 0.\n"
    assert assess_leap_diagnostics(raw, b"", complete_endpoint_satisfied=True)["disposition"] == "REJECTED"
    assert assess_leap_diagnostics(raw, b"", selected_integral_dry_charge=True)["disposition"] == "SCREEN_PASSED"


def endpoint(monkeypatch, *, separation=2., gradient=.1):
    # Raw Amber→complete force assignment has independent tests. Here the
    # boundary fixture isolates composition of the retained force/geometry gates.
    terms = GeometryTerms((1, 1), (), (), ())
    monkeypatch.setattr(owner, "geometry_terms_from_amber", lambda raw: terms)
    monkeypatch.setattr(owner, "assess_retained_force_assignment", lambda *args:{"fixture": "complete-assignment"})
    source = NS(geometry_quality=MolecularGeometryPolicy(), maximum_minimization_iterations=17,
        maximum_minimization_gradient_kj_mol_nm=D(1), minimization_nonbonded_cutoff_angstrom=D(10),
        minimization_ewald_tolerance=D("0.000001"), construction_platform="CPU", construction_threads=2)
    model = NS(identity=NS(to_document=lambda:{"identity":"exposed-endpoint-control"}))
    points = np.array(((0., 0., 0.), (separation, 0., 0.)))
    box = tuple(D(x) for x in (30, 30, 30, 90, 90, 90))
    raw = amber_restart_text(points, box).encode()
    forces = np.zeros((2, 3), dtype=np.float64); forces[-1, -1] = gradient
    stream = BytesIO(); np.save(stream, forces, allow_pickle=False)
    quality = assess_molecular_geometry(points, terms, policy=source.geometry_quality, cell_angstrom=(30., 30., 30.))
    report = {"numerical_method":"OPENMM_LOCAL_ENERGY_MINIMIZER_COMPLETE_AMBER_V1", "model":model.identity.to_document(),
        "platform":"CPU", "threads":2, "platform_properties":{"Threads":"2", "DeterministicForces":"true"},
        "all_original_force_groups":True, "projected_pair_kernel":False,
        "iteration_limit_is_convergence":False, "maximum_iterations":17, "relaxed_coordinates_sha256":sha256(raw).hexdigest(),
        "final_force_coordinates":"EXACT_RETAINED_RELAXED_INPCRD", "atom_count":2, "all_atoms_mobile":True,
        "constraints":"NONE", "rigid_water":False, "nonbonded_cutoff_angstrom":"10", "ewald_error_tolerance":"0.000001",
        "ensemble_admission":"UNEVALUABLE", "force_accuracy_admission":"UNEVALUABLE", "rate_admission":"UNEVALUABLE",
        "maximum_mobile_gradient_kj_mol_nm":gradient, "rms_mobile_gradient_kj_mol_nm":gradient/math.sqrt(6),
        "requested_openmm_rms_tolerance_kj_mol_nm":1/math.sqrt(6), "final_geometry":quality,
        "success":gradient <= 1 and quality["disposition"] == "SCREEN_PASSED"}
    files = {"relaxed.inpcrd":raw, "final-forces-kj-mol-nm.npy":stream.getvalue(), "model.prmtop":b"exposed-native-boundary",
        "force-assignment.json":b"{}", "relaxation.json":json.dumps(report).encode()}
    return source, model, files, box


@pytest.mark.parametrize("separation,gradient,finding", ((2., .1, None), (.348895, .1, "whole-system-final-geometry"),
    (2., 123246.77444, "whole-system-final-gradient")))
def test_good_force_cannot_hide_bad_geometry_and_good_geometry_cannot_hide_bad_force(monkeypatch, separation, gradient, finding):
    source, model, files, box = endpoint(monkeypatch, separation=separation, gradient=gradient)
    points, findings, report = owner.assess_retained_endpoint(source, model, files, 2, box)
    assert len(points) == 2 and report["maximum_gradient_kj_mol_nm"] == gradient
    assert findings == (() if finding is None else (finding,))


@pytest.mark.parametrize("change", ("claimed-success", "loose-rms", "wrong-restart", "partial-forces", "wrong-force-value", "wrong-method", "wrong-platform", "wrong-threads", "wrong-properties", "omitted-force-groups"))
def test_changed_native_summary_or_operand_never_promotes_an_endpoint(monkeypatch, change):
    source, model, files, box = endpoint(monkeypatch, gradient=2.)
    report = json.loads(files["relaxation.json"])
    if change == "claimed-success": report["success"] = True
    elif change == "loose-rms": report["requested_openmm_rms_tolerance_kj_mol_nm"] = 1.
    elif change == "wrong-restart": report["relaxed_coordinates_sha256"] = "0"*64
    elif change == "wrong-force-value": report["maximum_mobile_gradient_kj_mol_nm"] = .1
    elif change == "wrong-method": report["numerical_method"] = "CUSTOM_PROJECTED_MINIMIZER"
    elif change == "wrong-platform": report["platform"] = "CUDA"
    elif change == "wrong-threads": report["threads"] = 1
    elif change == "wrong-properties": report["platform_properties"]["DeterministicForces"] = "false"
    elif change == "omitted-force-groups": report["all_original_force_groups"] = False
    else:
        stream = BytesIO(); np.save(stream, np.zeros((1, 3)), allow_pickle=False)
        files["final-forces-kj-mol-nm.npy"] = stream.getvalue()
    files["relaxation.json"] = json.dumps(report).encode()
    with pytest.raises(ValueError):
        owner.assess_retained_endpoint(source, model, files, 2, box)


def test_duplicate_json_keys_cannot_rewrite_the_recorded_scientific_disposition():
    with pytest.raises(ValueError, match="duplicates"):
        owner._document(b'{"success":false,"success":true}')


@pytest.mark.parametrize("change,accepted", (("tiny-plane-roundoff", True), ("large-plane-change", False), ("threshold-disagreement", False)))
def test_float_diagnostic_roundoff_never_changes_independent_geometry_admission(monkeypatch, change, accepted):
    source, model, files, box = endpoint(monkeypatch)
    report = json.loads(files["relaxation.json"])
    geometry = report["final_geometry"]
    if change == "tiny-plane-roundoff": geometry["metrics"]["maximum_planar_improper_distance_angstrom"] += 1e-13
    elif change == "large-plane-change": geometry["metrics"]["maximum_planar_improper_distance_angstrom"] += .01
    else:
        geometry["disposition"] = "REJECTED"
        geometry["findings"] = ["whole-molecule-planar-improper-deviation"]
    files["relaxation.json"] = json.dumps(report).encode()
    if accepted:
        assert owner.assess_retained_endpoint(source, model, files, 2, box)[1] == ()
    else:
        with pytest.raises(ValueError): owner.assess_retained_endpoint(source, model, files, 2, box)


def test_downstream_mapping_uses_final_restart_and_keeps_premin_atom_origin_correspondence():
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_molecular import read_initial_molecular_coordinates
    from tests.test_rubisco_gp_initial_topology import coordinates
    census = dict(residue_starts=(1, 3), residue_names=("ALA", "WAT"),
        atom_names=("C", "N", "O", "H1", "H2"), atomic_numbers=(6, 7, 8, 1, 1), term_census={"atoms":5})
    dry = np.array(((0.,0.,0.),(1.5,0.,0.),(20.,0.,0.),(20.95,0.,0.),(20.,.95,0.)))
    solvated = dry+np.array((10.,10.,10.))
    final = solvated.copy(); final[:2] += np.array((2.,0.,0.)); final[2:] += np.array((5.,0.,0.))
    box = (60.,60.,60.,90.,90.,90.)
    files = {"dry.inpcrd":coordinates(tuple(map(str, dry.ravel())), count=5).encode(),
        "model.inpcrd":amber_restart_text(solvated, box).encode(), "relaxed.inpcrd":amber_restart_text(final, box).encode()}
    identity, selected, _, origins = read_initial_molecular_coordinates(files, census, census)
    assert np.array_equal(np.asarray(selected, float), final)
    assert identity.object_fingerprint == sha256(files["relaxed.inpcrd"]).hexdigest()
    assert identity.object_fingerprint != sha256(files["model.inpcrd"]).hexdigest()
    assert origins.original_to_solvated_atoms == tuple(range(5))
    assert origins.translation_angstrom == (D(10),)*3
