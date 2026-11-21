# SPDX-License-Identifier: MPL-2.0
"""Original source joins and chemically adverse controls; no native calls."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import SourceMember
from empirical_lawhood.domains.rubisco.rubisco_response.amber_template import AmberResidueTemplate, assess_initial_templates, read_amber_template
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from tests.test_rubisco_rubp_preparation import prepared


ROOT = Path(__file__).parent / "fixtures/rubisco/amber-templates"
HASHES = {"rubp.prepi": "02be1fe3eb91d441bae005eaad3baabf5057f082e5db724fbb1c1760003b7e53",
          "kcx.prepin": "574632057ea612a287a9ba974b87f69c45b3756bf37baa06d0c6a87abacef201"}
URL = "https://raw.githubusercontent.com/kacarlab/RuBisCO_evolution/e6c621656ca1a8eb7e09381d6405da5d412274a1/data/systems_for_MD/parameters/"


def source(name, text=None):
    original = (ROOT / name).read_bytes()
    assert sha256(original).hexdigest() == HASHES[name]
    raw = original if text is None else text.encode()
    return SourceMember("source.test." + name, URL + name, sha256(raw).hexdigest(), raw.decode())


def templates():
    return tuple(read_amber_template(source(n), template_id="template.test." + n) for n in HASHES)


def test_exact_original_templates_join_every_atom_edge_charge_and_hydrogen_name():
    rubp, kcx = templates()
    result = assess_initial_templates(rubp, kcx, prepared())
    assert (result["rubp_atoms"], result["rubp_bonds"], result["rubp_charge_e"]) == (26, 25, "-3.999998")
    assert (result["kcx_atoms"], result["kcx_bonds"], result["kcx_charge_e"]) == (23, 22, "-1.000000")
    assert result["graph_correspondence"] == "SATISFIED"
    assert result["parameter_accuracy"] == result["reactive_states"] == "UNEVALUABLE"
    assert dict(result["ligand_name_map"])["H3"] == "HC3"
    assert len(result["ligand_name_map"]) == 26
    assert decode_canonical_bytes(rubp.canonical_bytes(), AmberResidueTemplate, maximum_bytes=64 * 1024) == rubp
    assert sha256((ROOT / "LICENSE").read_bytes()).hexdigest() == "e0507c94a9f74f8340523b18426e3485647553eb3dff782e1a40344455518ec0"


@pytest.mark.parametrize("before,after", (
    ("CORRECT     OMIT DU   BEG", "CHANGE OMIT DU BEG"),
    ("  0.0000", "  -4.0000"),
    ("DUMM  DU", "DUMM  CT"),
    ("1.540   111.208", "1.540   180.000"),
    ("-0.951527", "NaN"),
    ("LOOP\n\n", "LOOP\nC1 C2\n"),
    ("STOP", ""),
    ("STOP", "STOP\nSTOP"),
    ("STOP", "STOP\nCHARGE -4"),
))
def test_unknown_or_incomplete_source_conventions_refuse(before, after):
    original = source("rubp.prepi").raw_utf8
    assert before in original
    with pytest.raises((ValueError, ArithmeticError)):
        read_amber_template(source("rubp.prepi", original.replace(before, after, 1)), template_id="template.changed")


@pytest.mark.parametrize("kind", ("phosphate-proton", "wrong-hydrogen", "neutral-charge", "carbonyl-type", "carbamate-type"))
def test_chemically_wrong_source_preserves_denominator_and_refuses_use(kind):
    rubp, kcx = templates()
    if kind == "wrong-hydrogen":
        edges = set(rubp.bonds)
        edges.remove(("HO3", "O3"))
        edges.add(("HO3", "O4"))
        rubp = replace(rubp, bonds=tuple(sorted(edges)))
    elif kind == "phosphate-proton":
        edges = set(rubp.bonds)
        edges.remove(("HO3", "O3"))
        edges.add(("HO3", "O2P"))
        rubp = replace(rubp, bonds=tuple(sorted(edges)))
    elif kind == "neutral-charge":
        atoms = (replace(rubp.atoms[0], partial_charge_e=rubp.atoms[0].partial_charge_e + 4), *rubp.atoms[1:])
        rubp = replace(rubp, atoms=atoms, partial_charge_e=rubp.partial_charge_e + 4)
    elif kind == "carbonyl-type":
        rubp = replace(rubp, atoms=tuple(replace(a, atom_type="c3") if a.name == "C2" else a for a in rubp.atoms))
    else:
        kcx = replace(kcx, atoms=tuple(replace(a, atom_type="CT") if a.name == "CX" else a for a in kcx.atoms))
    with pytest.raises(ValueError):
        assess_initial_templates(rubp, kcx, prepared())


def test_reactive_graph_cannot_borrow_keto_template_when_connectivity_is_unchanged():
    rubp, kcx = templates()
    ligand = prepared()
    graph = ligand.chemical_graph
    bonds = tuple(replace(b, order=D(1)) if
        {graph.atoms[b.first].native_atom_name, graph.atoms[b.second].native_atom_name} == {"C2", "O2"}
        else b for b in graph.bonds)
    changed = replace(ligand, chemical_graph=replace(graph, bonds=bonds))
    with pytest.raises(ValueError, match="independently assessed keto"):
        assess_initial_templates(rubp, kcx, changed)


def test_retained_correspondence_assessment_does_not_parse_or_construct_templates(monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import amber_template
    rubp, kcx = templates()
    def forbidden(*args, **kwargs):
        raise AssertionError("retained template comparison invoked its source reader")
    monkeypatch.setattr(amber_template, "read_amber_template", forbidden)
    assert assess_initial_templates(rubp, kcx, prepared())["graph_correspondence"] == "SATISFIED"
