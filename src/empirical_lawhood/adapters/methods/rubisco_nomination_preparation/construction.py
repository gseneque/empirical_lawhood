# SPDX-License-Identifier: MPL-2.0
"""Independent source DNA, complete coding units and matched construct checks.

These checks establish an authored sequence specification, not expression,
processing, assembly, active sites or biochemical performance. Source scripts
are retained bytes and are never executed by the method.
"""

from hashlib import sha256
from itertools import product
import json

# Standard table11 elongation; native ATG/GTG initiation is explicitly M.
CODONS = dict(
    zip(
        ("".join(c) for c in product("TCAG", repeat=3)),
        "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG",
        strict=True,
    )
)


def original_dna(raw):
    rows = raw.splitlines()
    first = next(
        (i for i, line in enumerate(rows) if line.startswith(("SQ ", "ORIGIN"))), None
    )
    if first is None:
        raise ValueError("construction lacks original nucleotide sequence section")
    sequence = "".join(
        c
        for line in rows[first + 1 :]
        if not line.startswith("//")
        for c in line
        if c.isalpha()
    ).upper()
    if not sequence or set(sequence) - set("ACGT"):
        raise ValueError("construction original DNA is incomplete or ambiguous")
    return sequence


def translate(dna):
    if (
        not dna
        or set(dna) - set("ACGT")
        or len(dna) % 3
        or dna[:3] not in ("ATG", "GTG")
    ):
        raise ValueError("construction coding unit changes complete native initiation")
    aa = "".join(CODONS[dna[i : i + 3]] for i in range(0, len(dna), 3))
    if aa[-1] != "*" or "*" in aa[:-1]:
        raise ValueError(
            "construction coding unit loses terminal stop or introduces internal stop"
        )
    return "M" + aa[1:-1]


def interval(sequence, coordinates):
    if len(coordinates) != 2 or not 1 <= coordinates[0] <= coordinates[1] <= len(
        sequence
    ):
        raise ValueError("construction interval exceeds its exact source sequence")
    return sequence[coordinates[0] - 1 : coordinates[1]]


def assess_construction(preparation, macro, candidates):
    members = {m.filename: m for m in preparation.source_members}
    doc = json.loads(members["sequence-defined-construction.json"].raw_utf8)
    material = json.loads(members["construct-options.json"].raw_utf8)
    if material.get("complete_construction") != doc:
        raise ValueError(
            "construction source differs from exact selected material design"
        )
    for filename in ("sharwood2008-radiometric-method.html", "sharwood2016-maize.html"):
        if members[filename].raw_utf8.encode() != macro.named(filename):
            raise ValueError(
                "construction paired-assay method replaces original admitted source"
            )
    if (
        doc.get("schema")
        != "rubisco-nomination01/sequence-defined-construction-addendum"
        or doc.get("version") != "1.0.0"
        or doc.get("actual_mutant_turnover") is not None
        or doc.get("actual_mutant_specificity") is not None
        or any(
            doc.get(k) != 0
            for k in (
                "native_contacts",
                "registered_scientific_operations",
                "new_biological_units",
                "external_synthesis_or_submission",
            )
        )
    ):
        raise ValueError(
            "construction document fabricates realized material or biological execution"
        )
    backbone_member = members["pUC19-M77789.2-original.embl"]
    backbone = original_dna(backbone_member.raw_utf8)
    helper_source = original_dna(members["pcc7002-D13971.1.embl"].raw_utf8)
    helper = doc["helper_original_CDS"]
    helper_dna = interval(helper_source, (2447, 2851))
    helper_aa = json.loads(members["rbcX-Q44177.json"].raw_utf8)["sequence"]["value"]
    if (
        doc["original_backbone_accession"] != "M77789.2"
        or doc["original_backbone_source_sha256"] != backbone_member.source_sha256
        or doc["original_backbone_sequence_ascii"] != backbone
        or doc["original_backbone_length_nt"] != len(backbone)
        or doc["original_backbone_sequence_sha256_ascii"]
        != sha256(backbone.encode()).hexdigest()
        or helper["coding_DNA_ascii"] != helper_dna
        or helper["source_CDS_1based"] != [2447, 2851]
        or helper["translation_table"] != 11
        or helper["reported_translation_ascii"] != helper_aa
        or translate(helper_dna) != helper_aa
        or helper["length_nt_including_stop"] != 405
        or helper["length_aa"] != 134
    ):
        raise ValueError(
            "construction substitutes original backbone or full native helper"
        )
    archival = doc["original_Gp_operon_archival"]
    original_gp = original_dna(macro.named("galdieria-AB018008.1.txt").decode())
    if archival["WT_1970bp_ascii"] != original_gp:
        raise ValueError("construction replaces authentic original Gp operon")
    lsu_dna = interval(original_gp, (20, 1501))
    wt_ssu_dna = interval(original_gp, (1550, 1966))
    mutant_ssu_dna = wt_ssu_dna[:284] + "G" + wt_ssu_dna[285:]
    if wt_ssu_dna[282:285] != "ATA" or mutant_ssu_dna[282:285] != "ATG":
        raise ValueError("construction I95M is not the source ATA to ATG edit")
    archival_mutant = original_gp[:1833] + "G" + original_gp[1834:]
    if archival["proposed_I95M_1970bp_ascii"] != archival_mutant or archival[
        "sole_native_operon_candidate_edit_1based"
    ] != [1834, "A", "G"]:
        raise ValueError("construction alters archival candidate beyond exact I95M")
    leader, rbs, spacer = "TAACTAACTAA", "AGGAGG", "TTAATT"
    if (
        doc["leader_stop_all_frames"] != leader
        or doc["synthetic_RBS_each_ORF"] != rbs
        or doc["synthetic_six_nt_spacer_each_ORF"] != spacer
        or doc["native_interval_replaced_1based"] != [239, 283]
        or interval(backbone, [233, 238]) != "AAGCTT"
        or interval(backbone, [284, 289]) != "GAATTC"
    ):
        raise ValueError(
            "construction changes selected backbone junctions or noncoding design"
        )
    designs = doc["designs"]
    if tuple(d["design_id"] for d in designs) != (
        "pUC19-GpI95M-RbcX-M1-proposed",
        "pUC19-GpWT-RbcX-M1-control-proposed",
    ):
        raise ValueError("construction omits exact candidate or matched control")
    plasmids = []
    for design, ssu_dna, ssu_aa in zip(
        designs,
        (mutant_ssu_dna, wt_ssu_dna),
        (
            preparation.proposed_m1_ssu_sequence,
            dict(candidates["gp.wt"].ssu_sequence_views)["m1"],
        ),
        strict=True,
    ):
        if design["status"] != "AUTHOR_PROPOSED_NOT_ENTERED" or any(
            design[k] is not False
            for k in (
                "assembly_qualified",
                "expression_qualified",
                "material_constructed",
            )
        ):
            raise ValueError(
                "construction promotes authored sequences to demonstrated material"
            )
        dna = (lsu_dna, helper_dna, ssu_dna)
        expected_cassette = leader + "".join(rbs + spacer + x for x in dna)
        expected_plasmid = backbone[:238] + expected_cassette + backbone[283:]
        for key, expected in (
            ("cassette", expected_cassette),
            ("full_circular_plasmid", expected_plasmid),
        ):
            selected = design[key]
            if (
                selected["sequence_ascii"] != expected
                or selected["length_nt"] != len(expected)
                or selected["sequence_sha256_ascii"]
                != sha256(expected.encode()).hexdigest()
            ):
                raise ValueError(
                    "construction changes full coding cassette or original vector bytes"
                )
        features = design["coding_features"]
        if len(features) != 3:
            raise ValueError("construction omits complete three-cistron coding census")
        for feature, coding, protein, gene in zip(
            features,
            dna,
            (preparation.lsu_sequence, helper_aa, ssu_aa),
            ("gp.rbcL", "pcc7002.rbcX", "gp.rbcS"),
            strict=True,
        ):
            cds = feature["CDS_1based"]
            if (
                feature["gene"] != gene
                or feature["strand"] != 1
                or feature["translation_table"] != 11
                or feature["complete_ORF"] is not True
                or feature["coding_DNA_ascii"] != coding
                or feature["translation_ascii"] != protein
                or translate(coding) != protein
                or feature["plasmid_CDS_1based"] != [x + 238 for x in cds]
                or interval(expected_cassette, cds) != coding
                or interval(expected_cassette, feature["RBS_1based"]) != rbs
                or interval(expected_cassette, feature["spacer_1based"]) != spacer
                or feature["initiation_codon"] != coding[:3]
                or feature["terminal_stop_codon"] != coding[-3:]
                or feature["internal_stop_codons"] != 0
                or feature["protein_added_tags_or_scars"] != "NONE"
            ):
                raise ValueError(
                    "construction coding/translation/source or full-coordinate mismatch"
                )
        plasmids.append(expected_plasmid)
    differences = [
        [i + 1, a, b]
        for i, (a, b) in enumerate(zip(plasmids[1], plasmids[0], strict=True))
        if a != b
    ]
    if (
        differences != [[2457, "A", "G"]]
        or doc["whole_plasmid_candidate_control_difference_1based"] != differences
    ):
        raise ValueError(
            "construction candidate/control changes more than exact I95M nucleotide"
        )
