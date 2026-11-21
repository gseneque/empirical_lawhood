# SPDX-License-Identifier: MPL-2.0
"""Paired sequence and original-receipt controls; synthetic custody only."""

from dataclasses import replace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoCaseSet, SubunitChain, homogeneous_material, paired_case
from empirical_lawhood.domains.rubisco.rubisco_response.nomination_reuse import assess_retained_nomination
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, CanonicalTaskReceipt, LogicalArtifactIdentity, ReceiptCheck
from tests.rubisco_nomination_fixture import nominee


@pytest.fixture(scope="module")
def exposed_nomination():
    _, dossier = nominee()
    logical = LogicalArtifactIdentity("artifact.exposed.dossier", dossier.fingerprint(), dossier.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", VisibilityCeiling.DEVELOPMENT_ONLY, (),
        OutcomeAccess.DEVELOPMENT_VISIBLE, ArtifactGenericValidation("validator.exposed.json", "1.0.0",
            "1" * 64, dossier.SCHEMA, ArtifactProfile.CANONICAL_JSON))
    physical = ArtifactMaterialization("materialization.exposed.dossier", logical.logical_artifact_id,
        "storage.exposed", "dossier.json", dossier.fingerprint(), len(dossier.canonical_bytes()), "none")
    receipt = CanonicalTaskReceipt("receipt.exposed.dossier", "run.exposed",
        "rubisco-nomination-preparation.prepare", "attempt.exposed", "2" * 40, (), (physical,),
        (logical,), (ReceiptCheck("exposed-only", True, ()),), OperationalStatus.SUCCEEDED, ())
    return dossier, receipt


def test_source_derived_cases_retain_m1_v1_all_eight_edits_and_matched_donor(exposed_nomination):
    dossier, receipt = exposed_nomination
    assessment = assess_retained_nomination(dossier, receipt, assessment_id="assessment.exposed.nomination")
    assert len(assessment.source_member_sha256s) == 14
    assert len(assessment.cases.cases) == 5
    assert assessment.assembly_and_kinetic_admission == "NOT_ESTABLISHED"
    for case in assessment.cases.cases:
        assert len(case.parent.chains) == len(case.mutant.chains) == 16
        assert [(c.chain_id, c.sequence) for c in case.parent.chains if c.subunit == "LSU"] == [
            (c.chain_id, c.sequence) for c in case.mutant.chains if c.subunit == "LSU"]
        if case.case_role == "NO_CHANGE":
            assert case.parent == case.mutant and not case.substitutions
        else:
            assert len(case.substitutions) == 8
            expected = (98, "V", "M") if case.case_role == "DONOR" else (95, "I", "M")
            assert all((s.position_1based, s.before, s.after) == expected for s in case.substitutions)
    raw = assessment.cases.canonical_bytes()
    assert decode_canonical_bytes(raw, RubiscoCaseSet, maximum_bytes=256 * 1024) == assessment.cases


@pytest.mark.parametrize("change", ["receipt-task", "digest", "size", "missing", "failed"])
def test_nomination_adoption_refuses_substituted_receipt_custody(exposed_nomination, change):
    dossier, receipt = exposed_nomination
    if change == "receipt-task":
        receipt = replace(receipt, task_id="another.producer")
    elif change == "digest":
        receipt = replace(receipt, output_materializations=(
            replace(receipt.output_materializations[0], physical_sha256="a" * 64),))
    elif change == "size":
        receipt = replace(receipt, output_materializations=(
            replace(receipt.output_materializations[0], size_bytes=7),))
    elif change == "missing":
        receipt = replace(receipt, output_logical_artifacts=(), output_materializations=())
    else:
        receipt = replace(receipt, operational_status=OperationalStatus.FAILED, reason_codes=("EXPOSED_FAILURE",))
    with pytest.raises(ValueError, match="receipt"):
        assess_retained_nomination(dossier, receipt, assessment_id="assessment.refused")


def test_finite_case_checks_complete_edits_and_never_shifts_processing_numbering(exposed_nomination):
    dossier, receipt = exposed_nomination
    case = assess_retained_nomination(dossier, receipt, assessment_id="assessment.control").cases.cases[0]
    with pytest.raises(ValueError, match="finite sequence"):
        replace(case, substitutions=case.substitutions[:-1])
    with pytest.raises(ValueError, match="finite sequence"):
        replace(case, substitutions=(replace(case.substitutions[0], position_1based=94), *case.substitutions[1:]))
    with pytest.raises(ValueError, match="processing"):
        replace(case, mutant=replace(case.mutant, processing_view="unmatched"))
    with pytest.raises(ValueError, match="sixteen"):
        replace(case.parent, chains=case.parent.chains[:-1])


def test_material_interface_supports_another_explicit_substitution_without_dossier_special_cases():
    source = ObjectIdentity("source.exposed", "empirical-lawhood/rubisco-response/disclosed-assumption", "1.0.0", "4" * 64)
    parent = homogeneous_material(material_id="material.other.wt", organism="Exposed organism",
        processing_view="complete", lsu="MAK", ssu="MIL", sources=(source,))
    child = homogeneous_material(material_id="material.other.mutant", organism="Exposed organism",
        processing_view="complete", lsu="MAK", ssu="MAL", sources=(source,))
    case = paired_case(case_id="case.other", parent=parent, mutant=child, case_role="CANDIDATE",
        exposure_group="exposure.software", sources=(source,))
    assert all(row.position_1based == 2 and row.before == "I" and row.after == "A" for row in case.substitutions)
    assert len(case.substitutions) == 8
    with pytest.raises(ValueError, match="finite edits"):
        replace(case, case_role="NO_CHANGE")
    with pytest.raises(ValueError, match="amino-acid"):
        SubunitChain("ssu.invalid", "SSU", "M?L")
