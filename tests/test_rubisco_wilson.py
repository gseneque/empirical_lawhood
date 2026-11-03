"""Synthetic primary table/parent bytes test exact construct and source scopes."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from html import escape

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics.genbank import (
    NativeTeParentConstructV1, decode_te_parent_genbank,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import (
    DOI, NativeWilsonTableV1, WilsonMutantPanelV1, apply_reported_edits,
    build_wilson2017_panel, decode_wilson2017_html,
)
from empirical_lawhood.kernel.decoding import decode_canonical_record


def parent_fixture():
    lsu = ["A"] * 475
    ssu = ["A"] * 118
    for position, residue in {1: "M", 74: "L", 300: "V", 345: "F", 393: "I", 397: "D", 398: "A", 414: "A", 415: "P", 451: "W"}.items():
        lsu[position-1] = residue
    for position, residue in {1: "M", 36: "Y", 37: "H", 48: "A", 51: "R", 98: "V", 112: "G"}.items():
        ssu[position-1] = residue
    lsu, ssu = "".join(lsu), "".join(ssu)
    codon = {"M": "ATG", "A": "GCT", "L": "CTG", "V": "GTT", "F": "TTT", "I": "ATT", "D": "GAT",
             "P": "CCT", "W": "TGG", "Y": "TAT", "H": "CAT", "R": "CGT", "G": "GGT"}
    dna = "".join(codon[a] for a in lsu) + "TAA" + "A" * 65 + "".join(codon[a] for a in ssu) + "TAA"
    assert len(dna) == 1850
    lines = ["LOCUS       MG000148                1850 bp    DNA     linear   SYN",
             "ACCESSION   MG000148", "VERSION     MG000148.1", "FEATURES             Location/Qualifiers"]
    for gene, location, protein_id, sequence in (("rbcL", "1..1428", "ATN39932.1", lsu), ("rbcS", "1494..1850", "ATN39933.1", ssu)):
        lines.extend([f"     CDS             {location}", f'                     /gene="{gene}"',
                      "                     /codon_start=1", "                     /transl_table=11",
                      f'                     /protein_id="{protein_id}"', f'                     /translation="{sequence}"'])
    lines.append("ORIGIN")
    for start in range(0, len(dna), 60):
        lines.append(f"{start+1:9d} " + " ".join(dna[i:i+10].lower() for i in range(start, min(start+60, len(dna)), 10)))
    return ("\n".join(lines) + "\n//\n\n").encode()


def table_fixture():
    header = ("Rubisco", "Mutant library", "Amino acid mutation(s)", "Expression (% (w/w) sol E. coli protein)",
              "kcatc", "Kc21% O2", "kcatc/Kc21%O2", "SC/O", "Tma")
    units = ("", "", "", "", "", "s−1", "μm", "mm−1 s−1", "mol mol−1", "°C")
    counts = ("n = biological samples, technical replicates", "", "", "", "3–5, 2", "3–9, 2", "3–5, 2", "3–5", "3, 3", "1,3")
    rows = [header, ("RbcL", "RbcS"), units, counts]
    for name, edits in (("Se-LS(WT)", "None"), ("Se-F345I", "F345I"), ("Se-F140I", "F137I"), ("Se-V186I", "V189I")):
        rows.append((name, "NA", edits, "None", "1.0 ± 0.1", "10.0 ± 0.2", "100 ± 2", "100 ± 3", "50.0 ± 0.3", "NM"))
    rows.append(("Te-LS (WT)", "NA", "None", "None", "1.0 ± 0.1", "10.0 ± 0.2", "100 ± 2", "100 ± 3", "50.0 ± 0.3", "70 ± 1"))
    rows.extend([("",), ("First generation Te-rbcL–RDE2 mutants", *("",) * 9)])
    for name, edits in (("Te-F345I", "F345I"), ("Te-P415A", "P415A"), ("Te-V300A", "V300A"), ("Te-FIPA", "F345I, P415A")):
        rows.append((name, "1G", edits, "None", "1.0 ± 0.1*", "10.0 ± 0.2**", "100 ± 2", "100 ± 3", "50.0 ± 0.3", "70 ± 1"))
    rows.extend([("",), ("Second generation Te-rbcLS–RDE2 mutants", *("",) * 9)])
    mutations = (("P415A", "V98M"), ("P415A", "A48V"), ("P415A", "H37L"), ("P415A", "Y36N, G112D"),
                 ("P415A", "Y36N, R51H"), ("A398T, P415A", "A48V"), ("L74M, D397N, P415A", "None"),
                 ("A414T, P415A", "None"), ("I393M, P415A", "None"), ("A398T, P415A", "None"))
    for index, (l_edit, s_edit) in enumerate(mutations):
        rows.append((f"Te-2G{chr(97+index)} ({index+1})", "2G", l_edit, s_edit, "1.0 ± 0.1", "10.0 ± 0.2**",
                     "100 ± 2", "100 ± 3", "50.0 ± 0.3*", "NM"))
    table = []
    for index, row in enumerate(rows):
        cells = []
        for column, token in enumerate(row):
            spans = ' rowspan="2"' if index == 0 and column != 2 else ' colspan="2"' if index == 0 else ''
            if len(row) == 1:
                spans = ' colspan="10"'
            cells.append(f'<{"th" if index < 2 else "td"}{spans}>{escape(token)}</{"th" if index < 2 else "td"}>')
        table.append("<tr>" + "".join(cells) + "</tr>")
    return (f'<!DOCTYPE html><html><head><meta name="citation_doi" content="{DOI}"></head><body>'
            '<script>throw new Error("never executed");</script><section id="T1">'
            '<p>Parameters at 25 °C; means ± S.E. of biological samples assayed in duplicate or triplicate.</p>'
            '<table>' + "".join(table) + '</table></section></body></html>').encode()


def parse_parent(payload=None):
    payload = payload if payload is not None else parent_fixture()
    return decode_te_parent_genbank(payload, expected_sha256=sha256(payload).hexdigest())


def parse_table(payload=None):
    payload = payload if payload is not None else table_fixture()
    return decode_wilson2017_html(payload, expected_sha256=sha256(payload).hexdigest())


def test_complete_panel_parent_translation_subunits_and_declared_standard_errors():
    parent = parse_parent()
    table = parse_table()
    panel = build_wilson2017_panel(table, parent)
    assert len(panel.rows) == 19 and sum(r.name.startswith("Te-") for r in panel.rows) == 15
    assert len(parent.coding_sequence("rbcL").protein_sequence) == 475
    assert len(parent.coding_sequence("rbcS").protein_sequence) == 118
    selected = next(r for r in panel.rows if r.name == "Te-2Ga (1)")
    spec = selected.te_protein_specification
    assert spec.large_subunit_sequence[414] == "A" and spec.small_subunit_sequence[97] == "M"
    assert parent.coding_sequence("rbcL").protein_sequence[414] == "P"
    assert parent.coding_sequence("rbcL").protein_sequence[450] == "W"
    assert spec.nucleotide_scope == "DERIVED_AMINO_ACID_RECIPE_NO_MUTANT_DNA_ADMITTED"
    assert selected.endpoint("KCAT_C").standard_error == Decimal("0.2")
    assert selected.endpoint("KCAT_C").significance_suffix == "**"
    assert selected.endpoint("KCAT_C").replication.biological_minimum == 3
    assert selected.endpoint("KCAT_C").replication.biological_maximum == 9
    assert selected.endpoint("KCAT_C").replication.technical_replicates == 2
    assert selected.endpoint("SPECIFICITY_CO").replication.technical_replicates == 3
    assert selected.endpoint("K_C_AIR").unit == "micromolar"
    assert selected.endpoint("THERMAL_MIDPOINT").mean is None
    assert panel.rows[2].name == "Se-F140I" and panel.rows[2].native_rbcl_edits == "F137I"
    assert panel.rows[2].te_protein_specification is None
    assert decode_canonical_record(parent.to_document(), NativeTeParentConstructV1) == parent
    assert decode_canonical_record(table.to_document(), NativeWilsonTableV1) == table
    assert decode_canonical_record(panel.to_document(), WilsonMutantPanelV1) == panel


def test_wrong_compiled_mutation_number_duplicate_edit_and_foreign_parent_refused():
    parent = parse_parent()
    with pytest.raises(ValueError, match="ancestral residue"):
        apply_reported_edits(parent.coding_sequence("rbcL").protein_sequence, "P451A", subunit="rbcl")
    with pytest.raises(ValueError, match="duplicate"):
        apply_reported_edits(parent.coding_sequence("rbcL").protein_sequence, "P415A, P415V", subunit="rbcl")
    panel = build_wilson2017_panel(parse_table(), parent)
    with pytest.raises(ValueError, match="Se"):
        replace(panel.rows[0], te_protein_specification=panel.rows[4].te_protein_specification)
    with pytest.raises(ValueError, match="recipe"):
        replace(panel.rows[4].te_protein_specification, small_subunit_sequence="A" * 118)
    with pytest.raises(ValueError, match="all fifteen"):
        replace(panel, rows=panel.rows[:-1])
    first = panel.rows[0]
    with pytest.raises(ValueError, match="endpoint roles"):
        replace(first, endpoints=(first.endpoints[0], replace(first.endpoints[1],
            kind="SPECIFICITY_CO", unit="dimensionless"), *first.endpoints[2:]))
    altered = replace(first, endpoints=(first.endpoints[0], replace(first.endpoints[1],
        replication=first.endpoints[4].replication), *first.endpoints[2:]))
    with pytest.raises(ValueError, match="replication"):
        replace(panel, rows=(altered, *panel.rows[1:]))


@pytest.mark.parametrize("change", [
    lambda p: p.replace(b"MG000148.1", b"MG000148.2"),
    lambda p: p.replace(b"/transl_table=11", b"/transl_table=1"),
    lambda p: p.replace(b"1..1428", b"complement(1..1428)"),
    lambda p: p.replace(b"/translation=\"M", b"/translation=\"A", 1),
    lambda p: p.replace(b"        1 ", b"        2 "),
    lambda p: p + b"LOCUS invalid\n//\n",
])
def test_changed_genbank_identity_location_translation_and_native_numbering_refused(change):
    with pytest.raises(ValueError):
        parse_parent(change(parent_fixture()))


@pytest.mark.parametrize("change", [
    lambda p: p.replace(DOI.encode(), b"wrong-doi"),
    lambda p: p.replace(b'<!DOCTYPE html>', b'<!DOCTYPE html [<!ENTITY e "expanded">]>'),
    lambda p: p.replace(b'<table>', b'<table><table>'),
    lambda p: p.replace(b'rowspan="2"', b'rowspan="999"'),
    lambda p: p.replace(b'</table>', b'</table><table><tr><td>duplicate</td></tr></table>'),
    lambda p: p + b"\x00",
])
def test_hostile_or_changed_primary_html_refused(change):
    with pytest.raises(ValueError):
        parse_table(change(table_fixture()))


def test_unit_error_semantics_and_ancestral_label_changes_do_not_silently_correct():
    for old, new in (("s−1", "min−1"), ("means ± S.E.", "means ± S.D."), ("P415A", "P451A")):
        with pytest.raises(ValueError):
            build_wilson2017_panel(parse_table(table_fixture().replace(old.encode(), new.encode())), parse_parent())
