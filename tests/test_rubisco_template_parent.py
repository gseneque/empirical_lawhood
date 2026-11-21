# SPDX-License-Identifier: MPL-2.0
"""Independent structural refusals for pure, explicitly unrelaxed geometry."""
from copy import deepcopy
from dataclasses import replace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.gp_template_geometry import GpTemplateGeometryIntegrity, METHOD, SCOPE, TEMPLATE_NAMES, check_construction_invariants
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence, SourceMember
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.contracts import StructuralSourceMember
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from tests.test_rubisco_terminal_templates import construct, fixture


def test_independent_reader_checks_the_complete_derivation_without_reconstruction(monkeypatch):
    text, origin, libraries = fixture()
    result, _, _ = construct(text, origin, libraries)
    def forbidden(*args, **kwargs):
        raise AssertionError("a retained structural read must not reconstruct coordinates")
    monkeypatch.setattr("empirical_lawhood.domains.rubisco.rubisco_response.terminal_templates.build_terminals", forbidden)
    geometry, peptides, nontrans = check_construction_invariants(text, result, origin)
    assert geometry["atom_count"] == 16 and peptides == 2 and nontrans == 0
    assert not geometry["backbone_anomalies_squared_angstrom"]
    assert not geometry["stereochemistry_anomalies_angstrom3"]


@pytest.mark.parametrize("change", ("observed", "serial", "record", "missing", "origin"))
def test_template_reader_refuses_coordinate_identity_and_census_substitutions(change):
    text, origin, libraries = fixture()
    result, _, _ = construct(text, origin, libraries)
    lines = result.splitlines(keepends=True)
    if change == "observed":
        i = next(i for i, line in enumerate(lines) if line.startswith("ATOM") and int(line[22:26]) == 2)
        lines[i] = lines[i][:30] + f"{99.:8.3f}" + lines[i][38:]
    elif change == "serial":
        lines[1] = lines[1][:6] + f"{90:5d}" + lines[1][11:]
    elif change == "record":
        lines[0] = "REMARK SUBSTITUTED ORIGINAL RECORD\n"
    elif change == "missing":
        del lines[1]
    else:
        origin = deepcopy(origin)
        origin["complete_heavy_atoms"][0]["source_origin"] = {"exposed": True}
    with pytest.raises(ValueError):
        check_construction_invariants(text, "".join(lines), origin)


def test_retained_constructed_distortion_is_a_negative_result_not_physical_acceptance():
    text, origin, libraries = fixture()
    result, _, _ = construct(text, origin, libraries)
    lines = result.splitlines(keepends=True)
    ca = next(line for line in lines if line.startswith("ATOM") and line[12:16].strip() == "CA" and int(line[22:26]) == 1)
    i = next(i for i, line in enumerate(lines) if line.startswith("ATOM") and line[12:16].strip() == "CB" and int(line[22:26]) == 1)
    lines[i] = lines[i][:30] + ca[30:54] + lines[i][54:]
    geometry, _, _ = check_construction_invariants(text, "".join(lines), origin)
    assert geometry["short_contacts_squared_angstrom"]
    assert geometry["stereochemistry_anomalies_angstrom3"]
    assert geometry["physical_geometry_admission"] == "UNEVALUABLE"


def test_pure_assessment_has_its_own_identity_and_cannot_claim_a_native_minimum():
    from tests.test_rubisco_preamber_geometry_integrity import selected_assessment
    old = selected_assessment()
    identity = lambda name, schema: ObjectIdentity(name, schema, "1.0.0", "0"*64)
    current = GpTemplateGeometryIntegrity("assessment.exposed-template", old,
        identity("source.exposed-gp", StructuralSourceMember.SCHEMA),
        tuple(identity("source.gp-terminal-template."+name.lower(), SourceMember.SCHEMA) for name in TEMPLATE_NAMES),
        FileEvidence("template.gp.wt.m1/complete-heavy.pdb", 1, "0"*64), old.origin_file,
        old.atom_count, old.inherited_atom_count, old.constructed_atom_count, 0, 0, 0, 0, 0, A.SATISFIED)
    assert current.method == METHOD and current.scope == SCOPE
    assert not hasattr(current, "geometry_receipt")
    assert decode_canonical_bytes(current.canonical_bytes(), type(current), maximum_bytes=2**20) == current
    for field in ("minimization_disposition", "ensemble_disposition", "rate_disposition"):
        with pytest.raises(ValueError, match="physical admission"):
            replace(current, **{field: A.SATISFIED})
    with pytest.raises(ValueError, match="physical admission"):
        replace(current, new_native_calls=1)
    negative = replace(current, short_contact_count=1, structural_disposition=A.FALSIFIED)
    assert negative.minimization_disposition is A.UNEVALUABLE
    with pytest.raises(ValueError, match="physical admission"):
        replace(negative, structural_disposition=A.SATISFIED)
