# SPDX-License-Identifier: MPL-2.0
"""Complete selected preparation alternatives and adverse retained joins."""

from dataclasses import replace
from decimal import Decimal as D

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoCaseSet
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_assessment import MolecularPreparationCriteria, assess_molecular_preparation
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_preparation import MolecularPreparationCensus, MolecularPreparationSelection, RetainedPreparationMember, assess_preparation_census
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_transform import derive_atomic_transformation
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from tests.rubisco_response_molecular_fixture import (
    chemical_graphs, common_atoms, geometry_files, ligand_bindings, representation,
)


@pytest.fixture(scope="module")
def selected():
    supplied = disclosed_supply()
    case, source = supplied.case, supplied.case.sources[0]
    other = replace(case, case_id="case.disclosed.view-two",
        parent=replace(case.parent, material_id="material.view-two.wt", processing_view="view-two"),
        mutant=replace(case.mutant, material_id="material.view-two.mutant", processing_view="view-two"))
    cases = RubiscoCaseSet("cases.disclosed.preparation", (case, other), (source,))
    chemistry, graphs = chemical_graphs(supplied.context.chemistry)
    chemistries = (chemistry, replace(chemistry, protocol_id=chemistry.protocol_id + ".alternative"))
    parameters = tuple(ObjectIdentity("parameter.disclosed." + str(i), source.object_schema,
        source.object_version, source.object_fingerprint) for i in range(2))
    sources = tuple(sorted({source, cases.identity, *parameters, *(c.identity for c in chemistries),
        *(s for c in chemistries for s in c.sources)}, key=lambda row: row.object_id))
    selection = MolecularPreparationSelection("preparation.disclosed", cases, chemistries, parameters,
        source, D("298.15"), sources, ("requirement.disclosed.selection-support",))
    criteria = MolecularPreparationCriteria("criteria.disclosed.census", D(100), D("0.01"),
        source, ("requirement.disclosed.criteria-support",))
    members = []
    for i, slot in enumerate(selection.slots):
        if i < 2:
            material = case.mutant if slot.arm == "mutant" else case.parent
            model, top, xyz = representation(material, chemistry, name="molecular.census." + slot.arm)
            model = replace(model, parameter_model=parameters[0],
                sources=tuple(sorted((*model.sources, parameters[0]), key=lambda row: row.object_id)))
            geometry, files = geometry_files(model, top, xyz)
            assessed = assess_molecular_preparation(model, geometry, criteria, raw_files=files,
                assessor_source=source, assessment_id="assessment.census." + slot.arm,
                ligand_graphs=graphs, ligand_bindings=ligand_bindings(model))
            members.append(RetainedPreparationMember(slot, "AVAILABLE", model, assessed,
                tuple(sorted((model.raw_topology, model.raw_coordinates), key=lambda row: row.object_id))))
        else:
            state = "UNKNOWN" if i in (2, 3) else "FAILED" if i == 4 else "NOT_ENTERED"
            members.append(RetainedPreparationMember(slot, state, None, None,
                () if state == "NOT_ENTERED" else (source,)))
    mutant, wild_type = members[:2]
    transformation = derive_atomic_transformation(wild_type.representation, mutant.representation,
        transformation_id="transformation.census", kind="FINITE_SEQUENCE_SUBSTITUTION",
        common_atoms=common_atoms(wild_type.representation, mutant.representation), protocol=source, sources=(source,), case=case)
    return selection, tuple(members), (transformation,)


def assess(selected):
    return assess_preparation_census(*selected, census_id="census.disclosed")


def test_complete_views_states_parameters_and_endpoints_keep_unknown_negative_and_unentered(selected):
    result = assess(selected)
    assert len(result.members) == 16  # two views * two chemistries * two parameters * two arms
    assert result.state_counts == (("AVAILABLE", 2), ("FAILED", 1), ("UNKNOWN", 2), ("NOT_ENTERED", 11))
    assert {row.slot.processing_view for row in result.members} == {"complete", "view-two"}
    assert result.members[0].geometry_gate is A.SATISFIED
    assert all(row.force_gate is A.UNEVALUABLE for row in result.members)
    assert result.physical_and_chemical_admission is A.UNEVALUABLE
    assert result.independent_biological_units == result.new_native_calls == 0
    assert "requirement.disclosed.selection-support" in result.unresolved_requirement_ids
    assert "requirement.molecular.independent-chemical-admission" in result.unresolved_requirement_ids
    assert len([key for key in result.unresolved_requirement_ids if key.endswith(".matched-finite-transformation")]) == 7
    assert decode_canonical_bytes(result.canonical_bytes(), MolecularPreparationCensus, maximum_bytes=250_000) == result


@pytest.mark.parametrize("change", ("omit", "reorder", "drop-requirements", "admit"))
def test_selected_denominator_and_open_scientific_boundaries_cannot_be_pruned(selected, change):
    result = assess(selected)
    with pytest.raises(ValueError):
        if change == "omit":
            replace(result, members=result.members[:-1])
        elif change == "reorder":
            replace(result, members=tuple(reversed(result.members)))
        elif change == "drop-requirements":
            replace(result, unresolved_requirement_ids=())
        else:
            replace(result, physical_and_chemical_admission=A.SATISFIED)


def test_complete_atom_transform_is_independently_rechecked(selected):
    selection, members, transformations = selected
    altered = replace(transformations[0], added_atom_indices=())
    with pytest.raises(ValueError, match="complete independent"):
        assess_preparation_census(selection, members, (altered,), census_id="census.bad-transform")
    with pytest.raises(ValueError, match="omits a finite endpoint"):
        assess_preparation_census(selection, members, (), census_id="census.no-transform")


def test_pairing_cannot_cross_temperature_parameter_chemistry_or_original_evidence(selected):
    selection, members, _ = selected
    row = members[0]
    with pytest.raises(ValueError, match="another endpoint"):
        replace(row, assessment=members[1].assessment)
    for model in (replace(row.representation, temperature_k=D("298")),
                  replace(row.representation, parameter_model=selection.preparation_protocol)):
        with pytest.raises(ValueError, match="full endpoint"):
            replace(row, representation=model, assessment=None)
    with pytest.raises(ValueError, match="topology or coordinate"):
        replace(row, original_evidence=row.original_evidence[:1])
    with pytest.raises(ValueError, match="availability"):
        replace(row, original_state="NOT_ENTERED")


def test_all_unentered_selection_is_complete_honest_stop_without_a_backend(selected):
    selection = selected[0]
    members = tuple(RetainedPreparationMember(slot, "NOT_ENTERED", None, None, ()) for slot in selection.slots)
    result = assess_preparation_census(selection, members, (), census_id="census.unentered")
    assert result.state_counts[-1] == ("NOT_ENTERED", 16)
    assert all(row.geometry_gate is row.force_gate is A.UNEVALUABLE for row in result.members)
    assert result.transformations == ()
    with pytest.raises(ValueError, match="complete derived slot"):
        assess_preparation_census(selection, members[:-1], (), census_id="census.omitted")
