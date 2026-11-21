# SPDX-License-Identifier: MPL-2.0
"""Tiny retained numerical/chemical counterexamples; no enzyme/native results."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import json

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_assessment import MolecularPreparationAssessment, MolecularPreparationCriteria, assess_molecular_preparation, assess_retained_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_chemistry import validate_ligand_correspondence
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from tests.rubisco_response_molecular_fixture import chemical_graphs, geometry_files, ligand_bindings, representation


@pytest.fixture(scope="module")
def selected():
    supply = disclosed_supply()
    chemistry, graphs = chemical_graphs(supply.context.chemistry)
    model, top, xyz = representation(supply.case.parent, chemistry, name="molecular.assessed.disclosed")
    geometry, files = geometry_files(model, top, xyz)
    criteria = MolecularPreparationCriteria("criteria.disclosed.preparation", D(100), D("0.01"),
        supply.case.sources[0], ("requirement.disclosed.criteria-support",))
    return model, graphs, geometry, files, criteria


def assess(selected, **kwargs):
    model, graphs, geometry, files, criteria = selected
    return assess_molecular_preparation(model, geometry, criteria, raw_files=files,
        assessor_source=model.material.sources[0], assessment_id="assessment.disclosed.molecular",
        ligand_graphs=graphs, ligand_bindings=ligand_bindings(model), **kwargs)


def test_all_site_graph_and_complete_geometry_reduction_keeps_scientific_gaps(selected, monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics import parameter_audit
    monkeypatch.setattr(parameter_audit, "assigned_parameter_inventory", lambda *a, **k: pytest.fail("producer entered"))
    model, graphs, _, _, _ = selected
    assert len(validate_ligand_correspondence(model, graphs, ligand_bindings(model))) == 8
    result = assess(selected)
    assert result.geometry.atom_count == len(model.atoms)
    assert sum(count for _, count in result.geometry.pair_counts) == len(model.atoms) * (len(model.atoms) - 1) // 2
    assert result.geometry_gate is A.SATISFIED
    assert result.force_gate is result.physical_and_chemical_admission is A.UNEVALUABLE
    assert len(result.ligand_graph_findings) == 8
    assert result.new_native_calls == result.independent_biological_units == 0
    assert "requirement.molecular.total-force-return" in result.unresolved_requirement_ids
    assert "requirement.disclosed.criteria-support" in result.unresolved_requirement_ids
    assert decode_canonical_bytes(result.canonical_bytes(), MolecularPreparationAssessment, maximum_bytes=200_000) == result
    with pytest.raises(ValueError, match="invent physical"):
        replace(result, physical_and_chemical_admission=A.SATISFIED)


def test_coincident_and_severe_contacts_are_negative_with_full_geometry_population(selected):
    original, graphs, _, _, criteria = selected
    model, top, xyz = representation(original.material, original.chemistry, name="molecular.coincident.disclosed", coincident=True)
    geometry, files = geometry_files(model, top, xyz)
    result = assess((model, graphs, geometry, files, criteria))
    assert result.geometry.hard_geometry_disposition is result.geometry_gate is A.FALSIFIED
    assert result.geometry.coincident_unwrapped_pair_count == 1
    assert result.geometry.atom_count == len(original.atoms)
    assert "requirement.molecular.resolve-severe-contacts" in result.unresolved_requirement_ids
    assert result.force_gate is A.UNEVALUABLE


def test_missing_chemical_graphs_remain_explicit_and_never_alias_zero_atoms(selected):
    model, _, geometry, files, criteria = selected
    result = assess_molecular_preparation(model, geometry, criteria, raw_files=files,
        assessor_source=model.material.sources[0], assessment_id="assessment.missing.graphs")
    assert result.ligand_graph_findings == ()
    assert "requirement.molecular.complete-ligand-graphs" in result.unresolved_requirement_ids


@pytest.mark.parametrize("change", ("binding", "element", "state", "order", "source"))
def test_ligand_relabeling_incomplete_site_census_and_chemical_changes_refuse(selected, change):
    model, graphs, _, _, _ = selected
    bindings = ligand_bindings(model)
    if change == "binding":
        bindings = bindings[:-1]
    elif change == "source":
        graphs = ()
    else:
        graph = graphs[0]
        if change == "element":
            graph = replace(graph, atoms=(replace(graph.atoms[0], atomic_number=7), graph.atoms[1]))
        elif change == "state":
            graph = replace(graph, ligand_state="CABP")
        else:
            graph = replace(graph, bonds=(replace(graph.bonds[0], order=D(2)),))
        chemistry = replace(model.chemistry,
            sites=tuple(replace(row, ligand_chemical_graph=graph.identity) for row in model.chemistry.sites),
            sources=tuple(sorted((value for value in (*model.chemistry.sources, graph.identity)
                if value != graphs[0].identity), key=lambda row: row.object_id)))
        model = replace(model, chemistry=chemistry,
            sites=tuple(replace(row, chemical_graph=graph.identity) for row in model.sites),
            sources=tuple(sorted((value for value in (*model.sources, graph.identity)
                if value != graphs[0].identity), key=lambda row: row.object_id)))
        graphs = (graph,)
        bindings = ligand_bindings(model)
    with pytest.raises(ValueError, match="site|census|correspondence|relabels|bond orders"):
        validate_ligand_correspondence(model, graphs, bindings)


@pytest.mark.parametrize("change", ("bytes", "author", "coordinate-array", "origin"))
def test_retained_raw_geometry_independently_refuses_source_and_mapping_substitutions(selected, change):
    model, _, geometry, original, _ = selected
    files = dict(original)
    if change == "bytes":
        files["topology"] += b"\n"
    elif change == "author":
        residues = list(model.residues)
        residues[0] = replace(residues[0], author_number=999)
        model = replace(model, residues=tuple(residues))
        geometry = replace(geometry, representation=model.identity)
    elif change == "coordinate-array":
        member = replace(model.arrays.members[0], sha256="a" * 64)
        model = replace(model, arrays=replace(model.arrays, members=(member,)))
        geometry = replace(geometry, representation=model.identity)
    else:
        origin = json.loads(files["origins"])
        origin["amber_realization"]["atoms"].pop()
        files["origins"] = json.dumps(origin).encode()
        geometry = replace(geometry, origins=replace(geometry.origins,
            byte_count=len(files["origins"]), sha256=sha256(files["origins"]).hexdigest()))
    with pytest.raises(ValueError, match="raw bytes|author numbering|coordinate array|full physical"):
        assess_retained_geometry(model, geometry, **files)
