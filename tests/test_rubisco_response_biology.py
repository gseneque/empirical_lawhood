# SPDX-License-Identifier: MPL-2.0
"""Retained source joins and adverse controls, with no biological qualification."""

from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction as F

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import EndpointValues
from empirical_lawhood.domains.rubisco.rubisco_response.biological_sources import ExposedBiologicalSources, read_exposed_biological_sources
from empirical_lawhood.domains.rubisco.rubisco_response.biological_support import BiologicalAnchorUse, BiologicalSupportSelection, PredictiveSupportAssessment, assess_predictive_support, selection_from_study
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_study
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoCaseSet, homogeneous_material, paired_case
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from tests.rubisco_nomination_fixture import sources as original_sources
from tests.test_rubisco_response_materials import exposed_nomination  # noqa: F401


@pytest.fixture(scope="module")
def biology(exposed_nomination):  # noqa: F811
    _, macro = original_sources()
    dossier, receipt = exposed_nomination
    sources = read_exposed_biological_sources(macro, dossier, receipt, evidence_id="biology.exposed")
    cases = sources.nomination.cases
    selection = BiologicalSupportSelection("biology.selection.exposed", cases, disclosed_study().acceptance,
        (None,) * len(cases.cases), ((),) * len(cases.cases))
    return macro, dossier, receipt, sources, selection


def assess(biology, *, selection=None, sources=None):
    return assess_predictive_support(selection or biology[4], sources or biology[3], assessment_id="biology.result.exposed")


def test_complete_original_sources_keep_unmeasured_gp_and_full_wilson_error_semantics(biology):
    *_, sources, _ = biology
    assert len(sources.candidates) == 32 and len(sources.wilson_panel.rows) == 19
    assert sum(row.te_protein_specification is None for row in sources.wilson_panel.rows) == 4
    before, after = sources.matched_donor_rows
    assert (before.endpoint("KCAT_C").mean, after.endpoint("KCAT_C").mean) == (D("6.9"), D("9.5"))
    assert (before.endpoint("SPECIFICITY_CO").mean, after.endpoint("SPECIFICITY_CO").mean) == (D("52.6"), D("56.3"))
    assert before.endpoint("KCAT_C").standard_error is not None
    assert "NOT_PER_ENZYME" in before.endpoint("KCAT_C").replication.scope
    assert sources.assay_proposal.actual_assay_ids == () and sources.new_biological_units == 0
    gp = next(row for row in sources.candidates if row.candidate_id == "gp.i95m")
    assert gp.turnover_s_inv is None and gp.specificity_dimensionless is None
    with pytest.raises(ValueError, match="drops an adverse"):
        replace(sources, candidates=sources.candidates[:-1])
    with pytest.raises(ValueError, match="validation units"):
        replace(sources, new_biological_units=6)


def test_original_macro_identity_and_producing_receipt_are_required(biology):
    macro, dossier, receipt, _, _ = biology
    with pytest.raises(ValueError, match="exact original macro source"):
        read_exposed_biological_sources(replace(macro, selected_candidate_ids=("gp.wt",)), dossier, receipt, evidence_id="bad.source")
    with pytest.raises(ValueError, match="producer receipt"):
        read_exposed_biological_sources(macro, dossier, replace(receipt, task_id="replacement.producer"), evidence_id="bad.receipt")


def test_all_views_and_nochange_keep_descriptive_ratios_without_joint_uncertainty(biology):
    result = assess(biology)
    assert len(result.cases) == 5
    donor = next(row for row in result.cases if row.case.object_id == "case.te-p415a-ssu-v98m")
    assert tuple(row.fraction for row in donor.source_mean_ratios) == (F(95, 69), F(563, 526))
    assert "NOT_JOINT_UNCERTAINTY" in donor.contrast_scope
    gp = [row for row in result.cases if row.case.object_id.startswith("case.gp-i95m.")]
    assert len(gp) == 2 and all(row.source_mean_ratios is None for row in gp)
    assert gp[0].parent_source == gp[1].parent_source and gp[0].mutant_source == gp[1].mutant_source
    controls = [row for row in result.cases if "no-change" in row.case.object_id]
    assert all(tuple(value.fraction for value in row.source_mean_ratios) == (1, 1) for row in controls)
    assert all(row.contrast_scope == "SELF_COMPARISON_NOT_MUTATION_EVIDENCE" for row in controls)
    assert all(row.independent_biological_unit_count is None for row in result.cases)
    assert result.new_biological_units == result.new_native_calls == 0
    assert result.biological_candidate_action == "HOLD" and result.combined_milestone == "OPEN"
    assert decode_canonical_bytes(result.canonical_bytes(), PredictiveSupportAssessment, maximum_bytes=2_000_000) == result
    with pytest.raises(ValueError, match="validation units"):
        replace(donor, independent_biological_unit_count=3)


def test_every_frozen_requirement_and_case_remains_in_the_assessment(biology):
    selection = biology[4]
    keys = ("requirement.independent.joint-error", "requirement.independent.predictive-coverage")
    selection = replace(selection, acceptance=replace(selection.acceptance, predictive_evidence_requirement_ids=keys))
    result = assess(biology, selection=selection)
    assert result.remaining_requirement_ids == tuple(sorted((*keys, selection.acceptance.gp_applicability_requirement_id)))
    assert all(row.case_ids == tuple(case.case_id for case in selection.cases.cases) for row in result.requirements)
    assert all(row.disposition is A.UNEVALUABLE for row in result.requirements)
    with pytest.raises(ValueError, match="drops a frozen"):
        replace(result, requirements=result.requirements[:-1])
    with pytest.raises(ValueError, match="complete source"):
        replace(result, cases=result.cases[:-1])
    with pytest.raises(ValueError, match="statistically falsify"):
        replace(result.requirements[0], disposition=A.FALSIFIED)


def test_source_anchoring_is_separate_from_validation_and_checks_original_values(biology):
    selection = biology[4]
    parent = next(row for row in biology[3].candidates if row.candidate_id == "gp.wt")
    anchor = BiologicalAnchorUse(ObjectIdentity.from_record(parent.candidate_id, parent),
        EndpointValues(Exact.of(F(8, 5)), Exact.of(238)))
    uses = tuple((anchor,) if case.case_id.startswith("case.gp") else () for case in selection.cases.cases)
    result = assess(biology, selection=replace(selection, anchor_uses=uses))
    anchors = [value for row in result.cases for value in row.anchors]
    assert len(anchors) == 4
    assert all(row.exact_source_mean_join is A.SATISFIED and row.independent_validation is A.UNEVALUABLE for row in anchors)
    assert all(row.disposition is A.UNEVALUABLE for row in result.requirements)
    wrong = replace(anchor, values=EndpointValues(Exact.of(2), Exact.of(238)))
    changed = ((wrong,), *uses[1:])
    rejected = assess(biology, selection=replace(selection, anchor_uses=changed))
    assert rejected.cases[0].anchors[0].exact_source_mean_join is A.FALSIFIED
    assert any("CLAIMED_ANCHOR_SOURCE_OR_VALUE_CONTRADICTED" in row.reason_codes for row in rejected.requirements)
    alias = replace(anchor, source=replace(anchor.source, object_fingerprint="f" * 64))
    rejected = assess(biology, selection=replace(selection, anchor_uses=((alias,), *uses[1:])))
    assert rejected.cases[0].anchors[0].exact_source_mean_join is A.FALSIFIED


def assay_context(case, *, temperature="298.15", ph=("8", "8")):
    original = disclosed_study().supplies[0].context
    chains = {row.chain_id: row for row in case.parent.chains}
    sites = tuple(replace(site, catalytic_lysine_position_1based=chains[site.lsu_chain_id].sequence.index("K") + 1)
        for site in original.chemistry.sites)
    return replace(original, temperature_k=D(temperature), ph_interval=tuple(map(D, ph)),
                   chemistry=replace(original.chemistry, sites=sites))


def test_actual_source_assay_mismatches_are_kept_even_when_recipes_match(biology):
    selection = biology[4]
    contexts = tuple(assay_context(case, temperature="298") for case in selection.cases.cases)
    result = assess(biology, selection=replace(selection, contexts=contexts))
    donor = result.cases[-1]
    assert "REPORTED_TEMPERATURE_MISMATCH" in donor.assay_flags
    assert "REPORTED_TURNOVER_PH_OUTSIDE_TARGET_INTERVAL" in donor.assay_flags
    assert "REPORTED_SPECIFICITY_PH_OUTSIDE_TARGET_INTERVAL" in donor.assay_flags
    compatible_numbers = tuple(assay_context(case, ph=("8", "8.1")) for case in selection.cases.cases)
    result = assess(biology, selection=replace(selection, contexts=compatible_numbers))
    donor = result.cases[-1]
    assert not any("MISMATCH" in flag or "OUTSIDE" in flag for flag in donor.assay_flags)
    assert "TURNOVER_SOLUBLE_EXTRACT_SPECIFICITY_PURIFIED_NOT_PAIRED" in donor.assay_flags
    assert donor.predictive_eligibility is A.UNEVALUABLE


def test_missing_sources_and_disclosed_constructs_never_borrow_real_enzyme_labels(biology):
    selection = selection_from_study(disclosed_study())
    for sources in (None, biology[3]):
        result = assess_predictive_support(selection, sources, assessment_id="biology.absent")
        assert len(result.cases) == 2 and all(row.parent_source is None and row.mutant_source is None for row in result.cases)
        assert all(row.source_mean_ratios is None for row in result.cases)
        assert all(row.disposition is A.UNEVALUABLE for row in result.requirements)
    with pytest.raises(ValueError, match="every case"):
        replace(selection, contexts=())


def test_actual_adverse_source_contrasts_are_retained_as_descriptions(biology):
    # The full source denominator includes adverse source-mean contrasts. They
    # remain visible even though none supplies independent Gp validation.
    sources = biology[3]
    parent_row = next(row for row in sources.candidates if row.candidate_id == "wilson2017-row8")
    adverse = next(row for row in sources.candidates if row.background == "te"
        and row.turnover_s_inv < parent_row.turnover_s_inv and row.specificity_dimensionless < parent_row.specificity_dimensionless)
    def material(row):
        return homogeneous_material(material_id="material." + row.candidate_id, organism="Thermosynechococcus elongatus",
            processing_view="reported", lsu=row.lsu_sequence, ssu=row.ssu_sequence_views[0][1], sources=(sources.source_audit,))
    case = paired_case(case_id="case.exposed.adverse", parent=material(parent_row), mutant=material(adverse),
        case_role="CANDIDATE", exposure_group="exposure.wilson2017-development", sources=(sources.source_audit,))
    cases = RubiscoCaseSet("selection.exposed.adverse", (case,), (sources.source_audit,))
    selection = BiologicalSupportSelection("biology.adverse", cases, biology[4].acceptance, (None,), ((),))
    result = assess(biology, selection=selection)
    assert all(value.fraction < 1 for value in result.cases[0].source_mean_ratios)
    assert result.cases[0].mutant_source == adverse
    assert result.cases[0].predictive_eligibility is A.UNEVALUABLE


def test_source_reader_does_not_execute_archived_or_original_scientific_producers(biology, monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_nomination_preparation import science
    from empirical_lawhood.domains.rubisco.rubisco_prediction import kinetic_model
    monkeypatch.setattr(science, "prepare", lambda *a, **k: pytest.fail("original nomination producer entered"))
    monkeypatch.setattr(kinetic_model, "solve_four_state", lambda *a, **k: pytest.fail("original response producer entered"))
    macro, dossier, receipt, _, _ = biology
    result = read_exposed_biological_sources(macro, dossier, receipt, evidence_id="biology.read.only")
    assert result.new_biological_units == 0 and result.matched_donor_rows == biology[3].matched_donor_rows
    assert decode_canonical_bytes(result.canonical_bytes(), ExposedBiologicalSources, maximum_bytes=2_000_000) == result


def test_public_biological_reader_requires_complete_sources_and_actual_postoutcome_cutoff():
    from empirical_lawhood.api.domain_composition.rubisco_response.biology import read_biological_analysis
    from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
    cutoff = InformationCutoff("cutoff.before", "clock.rubisco.physical-seconds", CausalPhase.PRE_ACTION, D(0))
    with pytest.raises(ValueError, match="complete original audit"):
        read_biological_analysis(directory="absent", information_cutoff=cutoff, artifact_writer=None, source_audit=object())
    with pytest.raises(ValueError, match="post-outcome"):
        read_biological_analysis(directory="absent", information_cutoff=cutoff, artifact_writer=None)
