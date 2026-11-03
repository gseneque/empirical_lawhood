# SPDX-License-Identifier: MPL-2.0
"""Original exposed publication bytes exercise software source admission only.

These tests supply no signers, experimental receipts, independent samples,
prospective authority or biochemical qualification.
"""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics import mcdonald2026 as source
from empirical_lawhood.adapters.physical.rubisco_kinetics.direct_panels import _diagnostics
from empirical_lawhood.kernel.decoding import decode_canonical_bytes

FIXTURES = Path(__file__).parent / "fixtures" / "rubisco" / "mcdonald2026"


@pytest.fixture(scope="module")
def original_bytes():
    return tuple((FIXTURES / name).read_bytes() for name in (
        "primary.xml", "sciadv.aeh3246_table_s4.xlsx", "sciadv.aeh3246_table_s5.xlsx", "sciadv.aeh3246_table_s8.xlsx",
    ))


@pytest.fixture(scope="module")
def panel(original_bytes):
    return source.decode_mcdonald2026(*original_bytes)


def test_exact_originals_full_denominators_missingness_and_quantities(panel, original_bytes):
    metadata = json.loads((FIXTURES / "source-metadata.json").read_text())
    assert metadata["license"].startswith("CC BY 4.0")
    assert [sha256(b).hexdigest() for b in original_bytes] == [f["sha256"] for f in metadata["files"]]
    assert tuple(c.name_cell.token for c in panel.contexts) == source.CONTEXT_NAMES
    assert len(panel.contexts) == 12 and sum(c.joint_complete for c in panel.contexts) == 11
    assert sum(c.table1_row is not None for c in panel.contexts) == 10
    assert sum(len(c.quantity("KCAT_C").raw_values) for c in panel.contexts) == 55
    assert sum(len(c.quantity("SPECIFICITY_CO").raw_values) for c in panel.contexts) == 39
    assert not any(q.diagnostic_flags for c in panel.contexts for q in c.quantities)
    leaf = panel.context("N. tabacum leaf")
    assert leaf.protein_recipe is None and not leaf.joint_complete
    assert leaf.quantity("SPECIFICITY_CO").count_cell.token == "n.m."
    assert leaf.quantity("SPECIFICITY_CO").measurement_count is None
    assert leaf.quantity("SPECIFICITY_CO").raw_values == ()
    assert len(panel.screened_variants) == 949
    assert len({v.mutation_cell.token for v in panel.screened_variants}) == 949
    assert len({re.search(r"[0-9]+", v.mutation_cell.token)[0] for v in panel.screened_variants}) == 50
    controls = [v.mutation_cell.token for v in panel.screened_variants if v.mutation_cell.token.startswith("K201")]
    assert len(controls) == 18 and "K201M" not in controls
    assert sum(v.disposition_cell is not None and v.disposition_cell.token == "Selected for rescreening"
               for v in panel.screened_variants) == 20
    assert panel.s5.worksheet("Enrichment frequencies").cell("Q3").token == "Total possible variants"
    assert panel.s5.worksheet("Enrichment frequencies").cell("R3").token == "931"
    # Retained native enrichment, absent outcomes and source booleans are not
    # transformed into additional intrinsic endpoint measurements.
    assert all(v.role == "SELECTION_OR_ENRICHMENT_NOT_INTRINSIC_KINETIC_LABELS" for v in panel.screened_variants)


def test_endpoint_mean_uncertainty_native_formulas_and_measurement_unit_limits(panel):
    wt = panel.context("NtRbcL")
    mutant = panel.context("NtRbcL T391I")
    kcat = mutant.quantity("KCAT_C")
    specificity = mutant.quantity("SPECIFICITY_CO")
    assert kcat.mean == Decimal("4.4967499999999996")
    assert kcat.sd == Decimal("0.41324841197517032") and kcat.measurement_count == 4
    assert specificity.mean == Decimal("79.850000000000009")
    assert specificity.sd == Decimal("3.0675071312060513") and specificity.measurement_count == 3
    assert kcat.role == specificity.role == "SOURCE_REPORTED_MEASURED"
    assert mutant.quantity("KC_AIR").unit == "micromolar"
    assert mutant.quantity("CARBOXYLATION_EFFICIENCY_AIR").role == "SOURCE_REPORTED_DERIVED_RATIO"
    assert kcat.summary_mean_cell.token == kcat.mean_cell.token
    assert kcat.summary_mean_cell.formula is None  # Source has equal typed values, not a formula join.
    assert all(q.independent_biological_n is None and q.paired_sample_ids == () for c in panel.contexts for q in c.quantities)
    assert wt.quantity("KCAT_C").measurement_count == 18
    assert wt.quantity("SPECIFICITY_CO").measurement_count == 10
    # Equal XLSX row numbers are deliberately not a paired preparation unit.
    raw = panel.s4.worksheets[0]
    assert raw.cell("P27").token != raw.cell("AB27").token
    assert "1.3 μM RuBP" in "".join(panel.article.method_sections[-1][1])
    assert panel.metrology_role == "LITERAL_SOURCE_METHOD_RECONSTRUCTION_UNRESOLVED"
    assert any("RUBP" in v for v in panel.limitations)


def test_native_parent_recipe_and_tag_plant_scope_are_distinct(panel):
    wt = panel.context("NtRbcL").protein_recipe
    mutant = panel.context("NtRbcL T391I").protein_recipe
    assert len(wt.translated_lsu) == 477 and wt.translated_lsu[368] == "A" and wt.translated_lsu[390] == "T"
    assert len(wt.translated_ssu) == 123 and wt.translated_ssu.startswith("MQVW")
    assert mutant.translated_lsu[390] == "I" and mutant.translated_lsu[368] == "A"
    assert [(i + 1, a, b) for i, (a, b) in enumerate(zip(wt.translated_lsu, mutant.translated_lsu, strict=True))
            if a != b] == [(391, "T", "I")]
    revert = panel.context("NtRbcL A369V").protein_recipe
    assert revert.translated_lsu[368] == "V" and revert.edit == "A369V"
    assert all(c.protein_recipe.mutant_dna is None for c in panel.contexts if c.protein_recipe is not None)
    assert panel.parent_lsu.start_1based == 4021 and panel.parent_lsu.end_1based_including_stop == 5454
    assert len(panel.tagged_ssu.translated_protein) == 219
    assert panel.tagged_ssu.translated_protein[96:] == wt.translated_ssu == panel.declared_ssu_cleavage_product
    assert panel.tagged_ssu.translated_protein[:96].endswith("LRLRGG")
    assert len(panel.plant_fusion.translated_protein) == 540
    assert panel.plant_fusion.translated_protein[57 + 368] == "V"
    assert panel.plant_fusion.translated_protein.endswith("HHHHHH")
    assert panel.plant_endogenous_ssu_census is None
    assert panel.processing_role == "DECLARED_CLEAVAGE_SEQUENCE_CONSEQUENCE_NOT_MEASURED_TERMINUS"


def test_closed_canonical_roundtrip(panel):
    decoded = decode_canonical_bytes(panel.canonical_bytes(), source.Mcdonald2026PanelV1, maximum_bytes=4 * 1024**2)
    assert decoded == panel and decoded.fingerprint() == panel.fingerprint()


@pytest.mark.parametrize("index", range(4))
def test_each_original_byte_hash_is_mandatory(original_bytes, index):
    altered = list(original_bytes)
    altered[index] = altered[index] + b" "
    with pytest.raises(ValueError, match="custody"):
        source.decode_mcdonald2026(*altered)


def test_hostile_article_xml_refuses_even_with_deliberately_overridden_fixture_digest(original_bytes, monkeypatch):
    hostile = b'<!DOCTYPE article [<!ENTITY invented "value">]>' + original_bytes[0]
    monkeypatch.setattr(source, "ARTICLE_SHA256", sha256(hostile).hexdigest())
    with pytest.raises(ValueError, match="DTD/entity"):
        source._article(hostile)


def test_coherent_native_cell_changes_cannot_keep_authentic_source_identity(panel):
    raw = panel.s4.worksheets[0]
    original = raw.cell("AG6")
    forged = replace(original, token="40", xml_v_token="40")
    worksheet = replace(raw, cells=tuple(forged if c.address == "AG6" else c for c in raw.cells))
    # The generic native record preserves local consistency. The exact science
    # intake additionally seals the full source projection.
    workbook = replace(panel.s4, worksheets=(worksheet, panel.s4.worksheets[1]))
    assert workbook.source_sha256 == source.S4_SHA256 and workbook.fingerprint() != source.S4_FINGERPRINT
    with pytest.raises(ValueError, match="native-cell projection"):
        replace(panel, s4=workbook)
    with pytest.raises(ValueError, match="article projection"):
        replace(panel.article, table1_caption=panel.article.table1_caption.replace("SD", "SE"))


def test_coherent_endpoint_projection_cannot_attach_genuine_source_cells(panel):
    context = panel.context("NtRbcL T391I")
    observed = context.quantity("KCAT_C")
    fake_mean = replace(observed.mean_cell, token="9", xml_v_token="9")
    fake_summary = replace(observed.summary_mean_cell, token="9", xml_v_token="9")
    mean, sd, flags = _diagnostics(Decimal(9), observed.sd, Decimal(observed.sem_cell.token),
                                  observed.measurement_count, observed.raw_values)
    forged = replace(observed, mean=Decimal(9), mean_cell=fake_mean, summary_mean_cell=fake_summary,
                     recomputed_raw_mean=mean, recomputed_raw_sample_sd=sd, diagnostic_flags=flags)
    forged_context = replace(context, quantities=tuple(forged if q.kind == "KCAT_C" else q for q in context.quantities))
    with pytest.raises(ValueError, match="coherent endpoint/recipe projection"):
        replace(panel, contexts=tuple(forged_context if c == context else c for c in panel.contexts))
    with pytest.raises(ValueError, match="screening denominator"):
        replace(panel, screened_variants=panel.screened_variants[:-1])


@pytest.mark.parametrize("changes", [
    {"independent_biological_n": 4}, {"measurement_count": True}, {"paired_sample_ids": ("batch1",)},
    {"kind": "KO"}, {"kind": "KCAT_O"}, {"role": "QUALIFIED_MEASUREMENT"},
])
def test_invented_units_roles_biological_n_and_pairing_refuse(panel, changes):
    with pytest.raises(ValueError):
        replace(panel.context("NtRbcL T391I").quantity("KCAT_C"), **changes)


def test_hidden_parent_plant_conflation_processing_and_clone_claims_refuse(panel):
    recipe = panel.context("NtRbcL").protein_recipe
    native_v = recipe.immediate_parent_lsu[:368] + "V" + recipe.immediate_parent_lsu[369:]
    with pytest.raises(ValueError, match="A369"):
        replace(recipe, immediate_parent_lsu=native_v, translated_lsu=native_v)
    for changes in ({"mutant_dna": "ATG"}, {"observed_terminal_processing_verified": True},
                    {"assembly_view": "PLANT_CHLOROPLAST"}):
        with pytest.raises(ValueError, match="cannot invent"):
            replace(recipe, **changes)
    for changes in ({"parent_lsu": panel.plant_fusion}, {"biological_independent_n": 11},
                    {"endpoint_preparation_pairing": "PAIRED"}, {"plant_endogenous_ssu_census": ("inferred",)},
                    {"metrology_role": "QUALIFIED"}, {"limitations": ()}):
        with pytest.raises(ValueError):
            replace(panel, **changes)
    with pytest.raises(ValueError, match="cannot invent"):
        replace(recipe, edit="A369V", native_name="NtRbcL A369V", translated_lsu=recipe.translated_lsu)
    with pytest.raises(ValueError, match="not an admitted"):
        panel.context("NtRbcL T391I").quantity("KO")


def test_no_synthesized_leaf_specificity_or_efficiency_as_specificity(panel):
    leaf = panel.context("N. tabacum leaf")
    with pytest.raises(ValueError, match="missing specificity"):
        replace(leaf.quantity("SPECIFICITY_CO"), mean=Decimal(79), sd=Decimal(1), measurement_count=3)
    context = panel.context("NtRbcL T391I")
    efficiency = context.quantity("CARBOXYLATION_EFFICIENCY_AIR")
    forged = replace(efficiency, kind="SPECIFICITY_CO", unit="dimensionless", role="SOURCE_REPORTED_MEASURED")
    forged_context = replace(context, quantities=(forged, *context.quantities[1:]))
    with pytest.raises(ValueError, match="coherent endpoint/recipe projection"):
        replace(panel, contexts=tuple(forged_context if c == context else c for c in panel.contexts))
