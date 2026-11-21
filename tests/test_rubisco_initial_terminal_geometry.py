# SPDX-License-Identifier: MPL-2.0
"""Initial heavy stereo/peptide and ordinary repair dispatch controls."""

from hashlib import sha256
from decimal import Decimal
import json
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response import gp_geometry_repair_native as native
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair import (
    AMBER_FRAGMENT_PROTOCOL, GpAmberFragmentRepairInput, GpCarboxylateRepairInput, GpGeometryRepairInput,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_assessment import (
    AMBER_FRAGMENT_ASSESSMENT_FILES, ASSESSMENT_FILES, CARBOXYLATE_ASSESSMENT_FILES,
    GpAmberFragmentRepairAssessment, GpCarboxylateRepairAssessment, GpRepairPlanarityAssessment, read_initial_terminal_geometry,
)
from empirical_lawhood.domains.rubisco.rubisco_response import gp_geometry_repair_operation as operation
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import (
    AMBER_FRAGMENT_CAPABILITY, operation_declaration, repair_assessment_files, repair_capability,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_terminal_geometry import (
    INITIAL_REJECTION, TERMINAL_GEOMETRY_FILE, initial_terminal_geometry, require_initial_terminal_geometry, terminal_geometry_bytes,
)
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from scripts.operate_gp_construction import FIELDS, validate_request


def two_alanines(*, first_cb_z=1, second_ca_y=-1, component="ALA"):
    residues = [
        ("ALA", (("N", (-1, 1, 0)), ("CA", (0, 1, 0)), ("C", (0, 0, 0)), ("CB", (0, 1, first_cb_z)))),
        (component, (("N", (1, 0, 0)), ("CA", (1, second_ca_y, 0)), ("C", (2, -1, 0)), ("CB", (1, -1, -1)))),
    ]
    lines, origins = [], []
    for position, (resname, points) in enumerate(residues, 1):
        for name, (x, y, z) in points:
            lines.append(f"ATOM  {len(lines)+1:5d} {' '+name:<4s} {resname} A{position:4d}    "
                         f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {name[0]:>2s}  \n")
            constructed = position == 1
            origins.append(dict(chain="A", position=position, atom=name, component=resname, element=name[0],
                status="DECLARED_CONSTRUCTED_MUTANT_OR_MISSING_ATOM" if constructed else "INHERITED_OBSERVED_SOURCE",
                source_origin=None if constructed else {"exposed": True}))
    return "".join(lines) + "END\n", dict(complete_heavy_atoms=origins)


def initial(heavy_pdb, origin):
    return initial_terminal_geometry(heavy_pdb, origin, origin_sha256=sha256(json.dumps(origin).encode()).hexdigest())


@pytest.mark.numerical(oracle="The named CA determinant is +1/-1/0 A^3. The planar trans quartet is 180 degrees and cis is zero.")
def test_initial_chirality_and_omega_have_distinct_original_denominators():
    heavy, origin = two_alanines()
    valid = initial(heavy, origin)
    assert valid["protein_stereocentres"] == 2
    assert valid["construction_affected_stereocentres"] == valid["construction_affected_nonpro_peptides"] == 1
    require_initial_terminal_geometry(valid)
    for cb in (0, -1):
        report = initial(*two_alanines(first_cb_z=cb))
        assert Decimal(report["stereocentre_violations"][0]["signed_volume_angstrom3"]) == cb
        assert report["stereocentre_violations"][0]["centre"] == ["A", 1, "CA"]
        assert report["peptide_violations"] == []
    cis = initial(*two_alanines(second_ca_y=1))
    assert cis["peptide_violations"][0]["omega_degrees"] == 0
    assert cis["peptide_violations"][0]["reason"] == "outside-trans-range"
    degenerate = initial(*two_alanines(second_ca_y=0))
    assert degenerate["peptide_violations"][0]["omega_degrees"] is None
    assert degenerate["peptide_violations"][0]["reason"] == "undefined-dihedral"
    assert initial(*two_alanines(second_ca_y=1, component="PRO"))["construction_affected_nonpro_peptides"] == 0
    origin["complete_heavy_atoms"].pop()
    with pytest.raises(ValueError, match="atom-origin census"):
        initial(heavy, origin)


def test_independent_initial_read_refuses_changed_diagnostic_or_coordinates():
    heavy, origin = two_alanines()
    files = {"initialized-heavy.pdb": heavy.encode(), "atom-origin-provenance.json": json.dumps(origin).encode(),
             TERMINAL_GEOMETRY_FILE: terminal_geometry_bytes(initial(heavy, origin))}
    require_initial_terminal_geometry(read_initial_terminal_geometry(files, origin))
    with pytest.raises(ValueError, match="independently read"):
        read_initial_terminal_geometry({**files, TERMINAL_GEOMETRY_FILE: b"{}"}, origin)
    with pytest.raises(ValueError, match="independently read"):
        read_initial_terminal_geometry({**files, "initialized-heavy.pdb": two_alanines(first_cb_z=-1)[0].encode()}, origin)


def test_public_fragment_selection_and_versioned_raw_censuses(tmp_path):
    fragment = operation_declaration(amber_fragments=True)
    assert fragment.manifest().registry_id == AMBER_FRAGMENT_CAPABILITY+"@5.0.0"
    assert fragment.input_record_types == (GpAmberFragmentRepairInput,)
    assert set(CARBOXYLATE_ASSESSMENT_FILES) - set(ASSESSMENT_FILES) == {TERMINAL_GEOMETRY_FILE}
    assert set(AMBER_FRAGMENT_ASSESSMENT_FILES) - set(CARBOXYLATE_ASSESSMENT_FILES) == {"terminal-fragments.json"}
    for kind, roster in ((GpGeometryRepairInput, ASSESSMENT_FILES), (GpCarboxylateRepairInput, CARBOXYLATE_ASSESSMENT_FILES),
                          (GpAmberFragmentRepairInput, AMBER_FRAGMENT_ASSESSMENT_FILES)):
        identity = SimpleNamespace(object_version=kind.VERSION)
        assert repair_assessment_files(identity) == roster
    assert repair_capability(object.__new__(GpAmberFragmentRepairInput)) == AMBER_FRAGMENT_CAPABILITY
    request = {key: str(tmp_path/key) for key in ("output_directory", *FIELDS["prepare-parent"])}
    with pytest.raises(ValueError, match="displacement"):
        validate_request("prepare-parent", {**request, "parent_repair_protocol": AMBER_FRAGMENT_PROTOCOL})
    fresh = {**request, "parent_repair_protocol": AMBER_FRAGMENT_PROTOCOL, "maximum_refined_displacement_angstrom": "0.25"}
    validate_request("prepare-parent", fresh)
    for changes in (dict(maximum_iterations=None), dict(maximum_iterations=False), dict(maximum_iterations=0),
                    dict(construction_seed=20261115), dict(construction_seed=20261114.0)):
        with pytest.raises(ValueError, match="iteration budget"):
            validate_request("prepare-parent", {**fresh, **changes})


def test_fragment_assessment_demands_the_versioned_complete_raw_roster():
    source = ObjectIdentity("input.exposed-parent", GpGeometryRepairInput.SCHEMA, "5.0.0", "4"*64)
    keys = [(chain, 213, atom) for chain in "ACEGIKMO" for atom in ("CD", "OE1", "OE2")]
    terms = GpRepairPlanarityAssessment(12, 10, 0, 2, 10, 10, 0, 0, 0, Decimal(".08"))
    def assessment(roster):
        return GpAmberFragmentRepairAssessment("assessment.exposed", source, tuple((n, "5"*64) for n in roster),
            124, 80, 20, 90, Decimal(0), Decimal(0), Decimal(2), 0, 0, 0, 0, (), AssessmentDisposition.SATISFIED,
            refined_inherited_heavy_atoms=24, largest_refined_displacement_angstrom=Decimal(".2"),
            refined_displacements_angstrom=tuple((*k,(Decimal(".2"), Decimal(0), Decimal(0))) for k in keys),
            fixed_bonds_checked=80, planarity=terms)
    record = assessment(AMBER_FRAGMENT_ASSESSMENT_FILES)
    assert decode_canonical_bytes(record.canonical_bytes(), GpAmberFragmentRepairAssessment, maximum_bytes=8192) == record
    with pytest.raises(ValueError):
        decode_canonical_bytes(record.canonical_bytes(), GpCarboxylateRepairAssessment, maximum_bytes=8192)
    with pytest.raises(ValueError):
        assessment(CARBOXYLATE_ASSESSMENT_FILES)


@pytest.mark.parametrize("kind", (GpCarboxylateRepairInput, GpAmberFragmentRepairInput))
def test_scoped_native_call_retains_failed_gate_before_full_amber(tmp_path, monkeypatch, kind):
    from empirical_lawhood.adapters.rubisco.rubisco_insilico_dynamics import native as amber
    from empirical_lawhood.adapters.rubisco.rubisco_response import amber_terminal_fragments, library_construction
    heavy, origin = two_alanines(first_cb_z=-1)
    selected = object.__new__(kind)
    for name, value in dict(heavy_pdb=heavy, origin_json=json.dumps(origin), construction_seed=1,
                            construction_platform="CPU", construction_threads=1, numeric_engine=None).items():
        object.__setattr__(selected, name, value)
    monkeypatch.setattr(native, "authenticate_numeric_engine", lambda *args, **kwargs: None)
    monkeypatch.setattr(native, "parameter_files", lambda source: {})
    monkeypatch.setattr(amber, "_leap_script", lambda *args: "check model\n")
    def forbidden(*args, **kwargs):
        pytest.fail("reached the wrong initializer or complete Amber/OpenMM before the gate")
    def selected_initializer(*args, **kwargs):
        return heavy, (), tuple(("A", 1, name) for name in ("C", "CA", "CB", "N"))
    is_fragment = kind is GpAmberFragmentRepairInput
    monkeypatch.setattr(library_construction, "complete_constructed_heavy_atoms", forbidden if is_fragment else selected_initializer)
    monkeypatch.setattr(amber_terminal_fragments, "initialize_amber_terminal_fragments", selected_initializer if is_fragment else forbidden)
    monkeypatch.setattr(native.subprocess, "run", forbidden)
    monkeypatch.setattr(library_construction, "complete_amber_minimization", forbidden)
    with pytest.raises(ValueError, match=INITIAL_REJECTION):
        native.execute_repair(selected, tmp_path)
    report = json.loads((tmp_path/TERMINAL_GEOMETRY_FILE).read_bytes())
    assert report["disposition"] == "REJECTED" and len(report["stereocentre_violations"]) == 1
    assert (tmp_path/"initialized-heavy.pdb").read_text() == heavy
    assert not (tmp_path/"amber.stdout").exists()


def test_retained_failed_preflight_rechecks_original_error_report_and_point_of_refusal(monkeypatch):
    source = object.__new__(GpCarboxylateRepairInput)
    heavy, origin = two_alanines(first_cb_z=-1)
    object.__setattr__(source, "origin_json", json.dumps(origin))
    report = initial(heavy, origin)
    with pytest.raises(ValueError) as expected:
        require_initial_terminal_geometry(report)
    error = "ValueError: " + str(expected.value) + "\n"
    files = {TERMINAL_GEOMETRY_FILE: terminal_geometry_bytes(report), "initialized-heavy.pdb": heavy.encode(),
             "atom-origin-provenance.json": source.origin_json.encode(), "native-error.txt": error.encode()}
    def verify(required_files, **kwargs):
        return {name: files[name] for name in required_files}
    monkeypatch.setattr(operation, "read_repair_files", lambda *args, required_files: verify(required_files))
    def read():
        census = SimpleNamespace(files=tuple(SimpleNamespace(relative_path="unit/"+name) for name in files))
        returned = SimpleNamespace(files=census,error=error)
        operation._read_failed_repair(source, None, returned, None)
    read()
    files["dry.inpcrd"] = b"unexpected"
    with pytest.raises(ValueError, match="entered work"):
        read()
    files.pop("dry.inpcrd")
    files[TERMINAL_GEOMETRY_FILE] = b"{}"
    with pytest.raises(ValueError, match="independently read"):
        read()
    files.pop(TERMINAL_GEOMETRY_FILE)
    with pytest.raises(ValueError, match="without its independently rejected"):
        read()
    files["native-error.txt"] = b"changed"
    with pytest.raises(ValueError, match="original native error"):
        read()


def test_failed_fragment_reconstructs_complete_candidate_preserves_partial_contacts(monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import terminal_fragment_placement as placement
    identity = SimpleNamespace(to_document=lambda: {"sha256": "a"*64})
    source = SimpleNamespace(identity=identity, amber_engine=SimpleNamespace(identity=identity),
                             numeric_engine=SimpleNamespace(fingerprint=lambda: "b"*64))
    measured = {"packing_contacts": [{"atom": 1}], "full_signed_stereocentres": 17}
    rejection = placement.TerminalCandidateRejected(["nonbonded heavy packing"], measured)
    def reject(*args):
        raise rejection
    monkeypatch.setattr(placement, "replay_terminal_fragments", reject)
    bundle = dict(method=placement.METHOD, source=identity.to_document(), amber_engine=identity.to_document(),
                  numerical_engine="b"*64, refusal=dict(error_type=type(rejection).__name__,
                  message=str(rejection), candidate_diagnostics=measured))
    def read(error):
        files = {"terminal-fragments.json": json.dumps(bundle).encode(), "native-error.txt": error.encode()}
        operation._read_failed_fragment(source, files, set(files), error)
    error = type(rejection).__name__ + ": " + str(rejection)
    read(error)
    bundle["refusal"]["candidate_diagnostics"] = {}
    with pytest.raises(ValueError, match="independently reconstructed"):
        read(error)
    monkeypatch.setattr(placement, "replay_terminal_fragments", lambda *args: None)
    with pytest.raises(ValueError, match="accepted initial candidate"):
        read(error)
    bundle["refusal"] = dict(error_type="ValueError",message="Selected Amber sequence fragment failed: lsu-n")
    read("ValueError: Selected Amber sequence fragment failed: lsu-n")
    with pytest.raises(ValueError, match="original refusal"):
        read("ValueError: some other outcome")
