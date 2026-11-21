# SPDX-License-Identifier: MPL-2.0
"""Public ligand source and altered-graph controls; no enzyme or rate evidence."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.contracts import StructuralSourceMember
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation import REQUIREMENTS, RuBPTetraanionPreparation, prepare_rubp_tetraanion
from empirical_lawhood.domains.rubisco.rubisco_response.rubp_preparation_assessment import RuBPTetraanionAssessment, assess_rubp_tetraanion
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A


SOURCE = Path(__file__).parent / "fixtures/rubisco/rubp/RUB.cif"
SOURCE_SHA256 = "f2082cdcf018061317e258742a92d6b4c4a7af9888bae02ac70e6557709c18c6"


def source():
    raw = SOURCE.read_bytes()
    assert sha256(raw).hexdigest() == SOURCE_SHA256
    return StructuralSourceMember("RUB.cif", "https://files.rcsb.org/ligands/download/RUB.cif", SOURCE_SHA256, raw.decode())


def prepared():
    return prepare_rubp_tetraanion(source(), preparation_id="preparation.test.rubp")


def assess(value):
    return assess_rubp_tetraanion(value, assessment_id="assessment.test.rubp")


def test_constructs_fourfold_deprotonation_with_explicit_stereochemistry_and_no_enzyme_claim():
    result = prepared()
    graph = result.chemical_graph
    checked = assess(result)
    assert (len(graph.atoms), len(graph.bonds), graph.formal_charge) == (26, 25, -4)
    assert checked.graph_disposition is A.SATISFIED and checked.electron_count == 160
    assert checked.enzyme_preparation_admission is checked.parameter_admission is A.UNEVALUABLE
    assert result.new_native_calls == checked.new_native_calls == 0
    assert result.unresolved_requirement_ids == REQUIREMENTS
    assert result.removed_source_proton_names == ("HOP2", "HOP3", "HOP5", "HOP6")
    assert {atom.native_atom_name for atom in graph.atoms if atom.formal_charge == -1} == {"O2P", "O3P", "O5P", "O6P"}
    assert all(value.fraction < 0 for _, value in checked.stereocentre_signed_volumes_angstrom3)
    for value, kind in ((result, RuBPTetraanionPreparation), (checked, RuBPTetraanionAssessment)):
        assert decode_canonical_bytes(value.canonical_bytes(), kind, maximum_bytes=64 * 1024) == value


def test_independent_assessor_does_not_use_constructor_or_its_cif_parser(monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_insilico_structure import science
    from empirical_lawhood.domains.rubisco.rubisco_response import rubp_preparation
    value = prepared()

    def forbidden(*args, **kwargs):
        raise AssertionError("retained assessment must not enter construction")

    monkeypatch.setattr(rubp_preparation, "prepare_rubp_tetraanion", forbidden)
    monkeypatch.setattr(science, "cif_tables", forbidden)
    assert assess(value).graph_disposition is A.SATISFIED


@pytest.mark.parametrize("change,finding", (
    ("charge", "atom-element-charge-or-origin"),
    ("carbonyl", "keto-state"),
    ("element", "tetraanion-formula"),
    ("mirror", "template-stereochemistry"),
    ("coordinates", "original-template-coordinate-correspondence"),
))
def test_altered_retained_ligand_is_falsified_without_renormalizing_it(change, finding):
    value = prepared()
    graph = value.chemical_graph
    if change == "charge":
        atoms = tuple(replace(atom, formal_charge=0 if atom.native_atom_name == "O2P" else -1)
                      if atom.native_atom_name in {"O2P", "C1"} else atom for atom in graph.atoms)
        value = replace(value, chemical_graph=replace(graph, atoms=atoms))
    elif change == "element":
        atoms = (replace(graph.atoms[0], atomic_number=7), *graph.atoms[1:])
        value = replace(value, chemical_graph=replace(graph, atoms=atoms))
    elif change == "carbonyl":
        bonds = tuple(replace(bond, order=D(1)) if
                      {graph.atoms[bond.first].native_atom_name, graph.atoms[bond.second].native_atom_name} == {"C2", "O2"}
                      else bond for bond in graph.bonds)
        value = replace(value, chemical_graph=replace(graph, bonds=bonds))
    elif change == "mirror":
        value = replace(value, template_coordinates_angstrom=tuple((name, (-xyz[0], xyz[1], xyz[2]))
                        for name, xyz in value.template_coordinates_angstrom))
    else:
        value = replace(value, template_coordinates_angstrom=tuple((name, (xyz[0] + 1, xyz[1], xyz[2]))
                        for name, xyz in value.template_coordinates_angstrom))
    checked = assess(value)
    assert checked.graph_disposition is A.FALSIFIED and finding in checked.findings
    assert checked.atom_count == len(graph.atoms) and checked.bond_count == len(graph.bonds)
    assert checked.enzyme_preparation_admission is A.UNEVALUABLE


def test_neutral_ligand_cannot_be_promoted_to_selected_tetraanion():
    value = prepared()
    graph = replace(value.chemical_graph, atoms=tuple(replace(atom, formal_charge=0)
                    for atom in value.chemical_graph.atoms), formal_charge=0)
    checked = assess(replace(value, chemical_graph=graph))
    assert checked.graph_disposition is A.FALSIFIED
    assert "tetraanion-charge-electron-count" in checked.findings
    assert checked.electron_count == 156


def test_source_substitution_and_evidence_promotion_are_refused():
    with pytest.raises(ValueError, match="original bytes"):
        replace(source(), raw_utf8=source().raw_utf8 + "\n")
    value = prepared()
    for kwargs in ({"selected_multiplicity": 3}, {"coordinate_scope": "RELAXED_ENZYME"},
                   {"unresolved_requirement_ids": ()}, {"new_native_calls": 1}):
        with pytest.raises(ValueError, match="cannot establish"):
            replace(value, **kwargs)
    for field in ("enzyme_preparation_admission", "parameter_admission"):
        with pytest.raises(ValueError, match="cannot admit"):
            replace(assess(value), **{field: A.SATISFIED})
    with pytest.raises(ValueError, match="satisfied RuBP assessment"):
        replace(assess(value), electron_count=156)


def writer_for(root):
    from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
    root.mkdir()
    mount = next(path for path in (root, *root.parents) if path.is_mount())
    return ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract("rubp-template.test",
        "Public source ligand template control", str(root), str(mount), "empirical-lawhood/testing/rubp-template", 1)))


def test_public_preparation_returns_atomic_custody_paths_without_native_entry(tmp_path, monkeypatch):
    from empirical_lawhood.api.domain_composition.rubisco_response.molecular_preparation import PREPARATION_MEMBERS, prepare_rubp_template, read_rubp_template
    from empirical_lawhood.execution.local.execution import LocalProcessExecutor
    monkeypatch.setattr(LocalProcessExecutor, "execute", lambda *a, **k: pytest.fail("native executor entered"))
    writer = writer_for(tmp_path / "custody")
    result = prepare_rubp_template(component_path=SOURCE, component_sha256=SOURCE_SHA256,
        output_relative_path="ligand/template", artifact_writer=writer)
    assert tuple(result["paths"]) == PREPARATION_MEMBERS and len(result["publications"]) == len(PREPARATION_MEMBERS)
    for path in result["paths"].values():
        assert Path(path).is_file() and Path(path + ".manifest.json").is_file()
    retained = decode_canonical_bytes(Path(result["paths"]["preparation.json"]).read_bytes(),
                                     RuBPTetraanionPreparation, maximum_bytes=64 * 1024)
    assert retained.original_component == source()
    assert assess(retained).graph_disposition is A.SATISFIED
    assert Path(result["paths"]["source.cif"]).read_bytes() == SOURCE.read_bytes()
    assert result["new_native_calls"] == 0 and result["parameter_admission"] == "UNEVALUABLE"
    from empirical_lawhood.api.domain_composition.rubisco_response import molecular_preparation as api
    monkeypatch.setattr(api, "prepare_rubp_tetraanion", lambda *a, **k: pytest.fail("retained read repeated construction"))
    for _ in range(2):
        read = read_rubp_template(directory_relative_path="ligand/template", component_sha256=SOURCE_SHA256,
                                 artifact_writer=writer)
        assert read["preparation"] == retained and read["assessment"].graph_disposition is A.SATISFIED
        assert read["new_native_calls"] == 0
    # A changed sibling must refuse even though the requested preparation body
    # still has its original bytes and manifest.
    Path(result["paths"]["source.cif"]).write_bytes(SOURCE.read_bytes() + b"\n")
    with pytest.raises((ValueError, RuntimeError)):
        read_rubp_template(directory_relative_path="ligand/template", component_sha256=SOURCE_SHA256,
                           artifact_writer=writer)


def test_changed_original_refuses_before_any_preparation_member_is_published(tmp_path, monkeypatch):
    from empirical_lawhood.api.domain_composition.rubisco_response import molecular_preparation as api
    raw = tmp_path / "source.cif"
    raw.write_bytes(SOURCE.read_bytes())
    writer = writer_for(tmp_path / "custody")
    original = api.assess_rubp_tetraanion

    def change_source(*args, **kwargs):
        result = original(*args, **kwargs)
        raw.write_bytes(raw.read_bytes() + b"\n")
        return result

    monkeypatch.setattr(api, "assess_rubp_tetraanion", change_source)
    with pytest.raises(ValueError, match="changed before"):
        api.prepare_rubp_template(component_path=raw, component_sha256=SOURCE_SHA256,
            output_relative_path="refused/template", artifact_writer=writer)
    assert not (tmp_path / "custody/refused/template/preparation.json").exists()


def test_public_preparation_refuses_wrong_digest_and_output_escape(tmp_path):
    from empirical_lawhood.api.domain_composition.rubisco_response.molecular_preparation import prepare_rubp_template
    writer = writer_for(tmp_path / "custody")
    with pytest.raises(ValueError, match="retained digest"):
        prepare_rubp_template(component_path=SOURCE, component_sha256="a" * 64,
            output_relative_path="refused/digest", artifact_writer=writer)
    with pytest.raises(ValueError):
        prepare_rubp_template(component_path=SOURCE, component_sha256=SOURCE_SHA256,
            output_relative_path="../escape", artifact_writer=writer)
