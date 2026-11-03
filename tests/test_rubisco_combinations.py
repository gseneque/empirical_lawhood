# SPDX-License-Identifier: MPL-2.0
"""Exposed quartet point arithmetic, sealed source roles and negative outcomes."""

from dataclasses import replace
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import json
import math

import pytest

from empirical_lawhood.adapters.methods.rubisco_combinations import records as r
from empirical_lawhood.adapters.methods.rubisco_combinations.analysis import (
    commit, evaluate, predict, prepare_roles, wilson_quartet_science,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.genbank import decode_te_parent_genbank
from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import (
    DOI, NativeArticleParagraphV1, NativeHTMLCellV1, NativeHTMLTableRowV1,
    NativeWilsonTableV1, TeProteinSpecificationV1, apply_reported_edits, build_wilson2017_panel,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity


def software_parent():
    # Minimal deposited-profile-shaped software DNA; never a biological source.
    lsu = "M" + "A" * 413 + "P" + "A" * 60
    ssu = "M" + "A" * 117
    codon = {"M": "ATG", "A": "GCT", "P": "CCT"}
    dna = "".join(codon[a] for a in lsu) + "TAA" + "A" * 65 + "".join(codon[a] for a in ssu) + "TAA"
    lines = ["LOCUS       MG000148                1850 bp    DNA     linear   SYN",
             "ACCESSION   MG000148", "VERSION     MG000148.1", "FEATURES             Location/Qualifiers"]
    for gene, location, accession, protein in (("rbcL", "1..1428", "ATN39932.1", lsu),
                                               ("rbcS", "1494..1850", "ATN39933.1", ssu)):
        lines.extend((f"     CDS             {location}", f'                     /gene="{gene}"',
                      "                     /codon_start=1", "                     /transl_table=11",
                      f'                     /protein_id="{accession}"', f'                     /translation="{protein}"'))
    lines.append("ORIGIN")
    for start in range(0, len(dna), 60):
        lines.append(f"{start+1:9d} " + " ".join(dna[i:i+10].lower() for i in range(start, min(start+60, len(dna)), 10)))
    payload = ("\n".join(lines) + "\n//\n").encode()
    return decode_te_parent_genbank(payload, expected_sha256=sha256(payload).hexdigest())


def software_table():
    header = ("Rubisco", "Mutant library", "Amino acid mutation(s)", "Expression (% (w/w) sol E. coli protein)",
              "kcatc", "Kc21% O2", "kcatc/Kc21%O2", "SC/O", "Tma")
    units = ("", "", "", "", "", "s−1", "μm", "mm−1 s−1", "mol mol−1", "°C")
    counts = ("n = biological samples, technical replicates", "", "", "", "3–5, 2", "3–9, 2", "3–5, 2", "3–5", "3, 3", "1,3")
    cells = [header, ("RbcL", "RbcS"), units, counts]
    by_ordinal = dict(r.SOURCE_ROSTER)
    selected = {spec[0]: role for role, spec in r.CORNER_SPECS.items()}
    # Literal means are previously exposed arithmetic operands in this software
    # fixture. Only fixture hashes below are replaced; no receipt is recreated.
    points = {12: ("6.9", "52.6"), 18: ("8.8", "48.0"), 22: ("8.1", "45.5"), 26: ("6.4", "50.5")}
    for ordinal in range(4, 27):
        if ordinal in (9, 15):
            cells.append(("",))
        elif ordinal in (10, 16):
            cells.append(("First generation" if ordinal == 10 else "Second generation", *("",) * 9))
        else:
            lsu, ssu = r.CORNER_NATIVE_EDITS[selected[ordinal]] if ordinal in selected else ("None", "None")
            turnover, specificity = points.get(ordinal, ("10.0", "50.0"))
            cells.append((by_ordinal[ordinal], "synthetic", lsu, ssu, "1.0 ± 0.1", turnover + " ± 0.2",
                          "100 ± 2", "100 ± 3", specificity + " ± 0.3", "NM"))
    rows = tuple(NativeHTMLTableRowV1(index, tuple(NativeHTMLCellV1("td", token, 1, 1, ()) for token in row))
                 for index, row in enumerate(cells))
    caption = NativeArticleParagraphV1(0, ("T1",), "At 25 °C, means ± S.E. biological samples assayed in duplicate or triplicate.")
    return NativeWilsonTableV1("b" * 64, DOI, "section#T1/table", rows, (caption,))


@pytest.fixture
def quartet(monkeypatch):
    parent, table = software_parent(), software_table()
    panel = build_wilson2017_panel(table, parent)
    # Explicit software-world pins. The installed actual source profile keeps
    # its authentic published panel/parent/member digests without these patches.
    monkeypatch.setattr(r, "SOURCE_PANEL_FINGERPRINT", panel.fingerprint())
    monkeypatch.setattr(r, "PARENT_FINGERPRINT", parent.fingerprint())
    monkeypatch.setattr(r, "SOURCE_ARTICLE_SHA256", table.source_sha256)
    monkeypatch.setattr(r, "DEPOSITED_PARENT_SHA256", parent.source_sha256)
    monkeypatch.setattr(r, "SOURCE_MEMBER_FINGERPRINTS", {row.native_table_row.ordinal_0based: row.fingerprint() for row in panel.rows})
    return panel, prepare_roles(panel)


def test_complete_source_retained_and_selected_roles_have_no_target_label_values(quartet):
    panel, (science, training, features, labels) = quartet
    assert len(panel.rows) == len(science.source_roster) == 19
    assert sum(member.disposition.startswith("SELECTED_") for member in science.source_roster) == 4
    assert {member.native_name for member in science.source_roster if member.native_name.startswith("Se-")} == {
        "Se-LS(WT)", "Se-F345I", "Se-F140I", "Se-V186I"}
    assert tuple(value.sample_id for value in training.observations) == r.TRAINING_IDS
    assert labels.target.sample_id == r.TARGET_ID
    for record in (science, features):
        for key in (b'"endpoints"', b'"native_cells"', b'"standard_error"', b'"mean"'):
            assert key not in record.canonical_bytes()
    assert features.target.protein_recipe.large_subunit_sequence[397] == "T"
    assert features.target.protein_recipe.small_subunit_sequence[47] == "V"
    assert science.protocol_sha256 == r.PROTOCOL_SHA256


def test_conventional_hand_arithmetic_continuous_errors_and_adverse_joint_direction(quartet):
    _, (science, training, features, labels) = quartet
    forecast = predict(science, training, features)
    evaluation = evaluate(science, commit(science, forecast), labels)
    assert float(forecast.additive_point.turnover_s_inv) == pytest.approx(6.4 * 8.8 / 6.9)
    assert float(forecast.additive_point.specificity_dimensionless) == pytest.approx(50.5 * 48 / 52.6)
    # Independent log addition is a second formula, not the implementation's
    # reference function. It establishes the assumed zero interaction only.
    assert float(forecast.additive_point.turnover_s_inv) == pytest.approx(math.exp(math.log(6.4) + math.log(8.8) - math.log(6.9)))
    assert float(forecast.additive_point.specificity_dimensionless) == pytest.approx(math.exp(math.log(50.5) + math.log(48) - math.log(52.6)))
    additive, baseline = evaluation.errors
    assert tuple(float(value) for value in additive.relative_errors) == pytest.approx((.007693684022186438, .0128274767058037))
    assert tuple(float(value) for value in baseline.relative_errors) == pytest.approx((.14814814814814814, .15604395604395604))
    assert evaluation.predicted_parent_log_contrasts[0] > 0 > evaluation.predicted_parent_log_contrasts[1]
    assert evaluation.observed_parent_log_contrasts[0] > 0 > evaluation.observed_parent_log_contrasts[1]
    assert all(value < 0 for value in evaluation.log_interaction_residual)
    assert not evaluation.predicted_joint_point_improvement and not evaluation.observed_joint_point_improvement
    assert evaluation.source_panel_contrasts == 1
    assert evaluation.independent_biological_units is evaluation.calibrated_joint_coverage is None
    assert not evaluation.candidate_nomination_established and not evaluation.el_advantage_established
    assert not any(b'"' + name + b'"' in evaluation.canonical_bytes()
                   for name in (b"jointly_within_point_tolerance", b"turnover_relative_tolerance", b"specificity_relative_tolerance"))


def test_unrestricted_interaction_is_unidentified_by_three_corners(quartet):
    _, (science, training, features, _) = quartet
    forecast = predict(science, training, features)
    base = float(forecast.additive_point.turnover_s_inv)
    # A response f(xL,xS)=log(parent)+a*xL+b*xS+gamma*xL*xS
    # has the exact same three training corners for every gamma. The fourth
    # cannot be determined without the declared zero-interaction assumption.
    for gamma in (-1.0, 0.0, 1.0):
        assert all(gamma * lsu * ssu == 0 for lsu, ssu in ((0, 0), (1, 0), (0, 1)))
        alternative_fourth = base * math.exp(gamma)
        assert alternative_fourth > 0
        assert (alternative_fourth == base) == (gamma == 0)
    assert forecast.prediction_scope == r.SCOPE


def test_target_labels_cannot_enter_predictor_or_training_roster(quartet):
    _, (science, training, features, labels) = quartet
    with pytest.raises(ValueError, match="three training corners"):
        predict(science, training, labels)
    with pytest.raises(ValueError, match="never target labels"):
        replace(training, observations=(*training.observations, labels.target))
    with pytest.raises(ValueError, match="never target labels"):
        replace(training, observations=(training.observations[0], training.observations[1], labels.target))
    document = json.loads(features.canonical_bytes())
    document["value"]["target_labels"] = labels.to_document()
    with pytest.raises(ValueError):
        decode_canonical_bytes(json.dumps(document).encode(), r.CombinationFeaturesV1, maximum_bytes=1024**2)


@pytest.mark.parametrize("field", ("mean", "standard_error"))
def test_valid_positive_fabricated_native_endpoint_refuses_training_and_target_roles(quartet, field):
    _, (_, training, _, labels) = quartet
    for observation in (training.observations[0], labels.target):
        original = observation.turnover
        mean = Decimal("123.4") if field == "mean" else original.mean
        se = Decimal("9.9") if field == "standard_error" else original.standard_error
        forged = replace(original, mean=mean, standard_error=se,
                         native_token=f"{mean} ± {se}{original.significance_suffix}")
        assert forged.mean > 0 and forged.standard_error > 0  # valid native record, wrong source projection
        with pytest.raises(ValueError, match="exact native source-row projection"):
            replace(observation, turnover=forged)


def test_coherently_rewritten_native_row_and_forged_roster_are_refused(quartet):
    _, (science, training, _, labels) = quartet
    for observation in (training.observations[0], labels.target):
        forged = replace(observation.turnover, mean=Decimal("123.4"), native_token="123.4 ± 0.2")
        native = observation.native_row
        cells = tuple(replace(cell, raw_text=forged.native_token) if index == 5 else cell
                      for index, cell in enumerate(native.native_table_row.cells))
        endpoints = tuple(forged if endpoint.kind == "KCAT_C" else endpoint for endpoint in native.endpoints)
        valid_native_row = replace(native, native_table_row=replace(native.native_table_row, cells=cells), endpoints=endpoints)
        assert valid_native_row.endpoint("KCAT_C").mean == Decimal("123.4")
        with pytest.raises(ValueError, match="exact native source-row projection"):
            replace(observation, native_row=valid_native_row, turnover=forged)
    member = science.source_roster[0]
    with pytest.raises(ValueError, match="exact native member"):
        replace(member, source_member=replace(member.source_member, object_fingerprint="c" * 64))


def test_source_parent_protocol_census_and_paired_recipe_substitution_refuse(quartet):
    panel, (science, _, features, _) = quartet
    with pytest.raises(ValueError, match="nineteen-row source"):
        replace(science, source_panel=replace(science.source_panel, object_fingerprint="c" * 64))
    with pytest.raises(ValueError, match="nineteen-row source denominator"):
        replace(science, source_roster=science.source_roster[:-1])
    with pytest.raises(ValueError, match="parent or protocol"):
        replace(science, protocol_sha256="c" * 64)
    with pytest.raises(ValueError, match="parent or protocol"):
        replace(science, parent=replace(science.parent, object_fingerprint="c" * 64))
    with pytest.raises(ValueError, match="exact full native panel"):
        wilson_quartet_science(replace(panel, table=replace(panel.table, source_sha256="c" * 64)))
    recipe = features.target.protein_recipe
    for native_lsu, native_ssu in (("P415A", "A48V"), ("A398T, P415A", "None"), ("P415A, A398T", "A48V")):
        lsu, l_edits = apply_reported_edits(recipe.parent.coding_sequence("rbcL").protein_sequence, native_lsu, subunit="rbcl")
        ssu, s_edits = apply_reported_edits(recipe.parent.coding_sequence("rbcS").protein_sequence, native_ssu, subunit="rbcs")
        valid_recipe = TeProteinSpecificationV1(recipe.parent, native_lsu, native_ssu, l_edits, s_edits, lsu, ssu)
        with pytest.raises(ValueError, match="exact recipe"):
            replace(features.target, protein_recipe=valid_recipe)


def test_complete_commitment_validation_precedes_any_label_inspection(quartet):
    _, (science, training, features, _) = quartet
    foreign = replace(training.science, object_fingerprint="c" * 64)
    foreign_forecast = r.CombinationForecastV1(r.PREFIX + ".forecast", foreign,
        replace(training, science=foreign), replace(features, science=foreign), *r.predicted_points(training))
    bad_commit = r.CombinationCommitmentV1(r.PREFIX + ".commitment", foreign,
        ObjectIdentity.from_record(foreign_forecast.forecast_id, foreign_forecast), foreign_forecast)
    class ForbiddenLabels:
        def __getattribute__(self, name):
            raise AssertionError("label object entered before complete commitment validation")
    with pytest.raises(ValueError, match="source/science/target recipe"):
        evaluate(science, bad_commit, ForbiddenLabels())


def test_caller_decimal_context_cannot_change_frozen_forecasts_or_errors(quartet):
    _, (science, training, features, labels) = quartet
    expected_forecast = predict(science, training, features)
    expected = evaluate(science, commit(science, expected_forecast), labels)
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        actual_forecast = predict(science, training, features)
        actual = evaluate(science, commit(science, actual_forecast), labels)
    assert actual_forecast == expected_forecast and actual == expected


def test_canonical_round_trip_refuses_imputed_coverage_and_outcome_promotions(quartet):
    _, (science, training, features, labels) = quartet
    forecast = predict(science, training, features)
    commitment = commit(science, forecast)
    evaluation = evaluate(science, commitment, labels)
    for record in (science, training, features, labels, forecast, commitment, evaluation):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=1024**2) == record
    for field, value in (("calibrated_joint_coverage", Decimal(".95")), ("independent_biological_units", 4),
                         ("candidate_nomination_established", True), ("el_advantage_established", True)):
        with pytest.raises(ValueError, match="cannot invent"):
            replace(evaluation, **{field: value})
    with pytest.raises(ValueError, match="complete two-method point census"):
        replace(evaluation, errors=evaluation.errors[:1])
    with pytest.raises(ValueError, match="direction or interaction"):
        replace(evaluation, observed_joint_point_improvement=True)
