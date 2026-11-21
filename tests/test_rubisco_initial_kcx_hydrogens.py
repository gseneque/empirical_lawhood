# SPDX-License-Identifier: MPL-2.0
"""Independent controls for the retained bespoke KCX distance derivation."""
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import construct_kcx_hydrogen_distances


def source():
    template = (Path(__file__).parent/"fixtures/rubisco/amber-templates/kcx.prepin").read_text()
    # Exposed exact source coefficients, not a fitted or actual enzyme model.
    parameters = "Exposed KCX bond-equilibrium control\nBOND\nN -H    434.0  1.0100\nCT-H1   340.0  1.0900\nCT-HC   340.0  1.0900\n"
    return template, parameters


@pytest.mark.numerical(oracle="The independently authored N-H equilibrium is1.0100Å and both CT-H1/CT-HC are1.0900Å. Only eleven terminal-H distance tokens may be replaced; all topology, charge, angle, dihedral and heavy tokens stay exact.")
def test_kcx_hydrogen_distances_use_the_actual_assigned_parent_bond_only():
    template, parameters = source()
    revised, report = construct_kcx_hydrogen_distances(template, parameters)
    changed, hydrogens = 0, 0
    for old, new in zip(template.splitlines(), revised.splitlines(), strict=True):
        before, after = old.split(), new.split()
        is_atom = len(before) == 11 and before[0].isdigit()
        if not is_atom or before[2] not in {"H", "H1", "HC"}:
            assert old == new
            continue
        hydrogens += 1
        assert before[:7] == after[:7] and before[8:] == after[8:]
        assert D(after[7]) == (D("1.0100") if before[2] == "H" else D("1.0900"))
        changed += D(before[7]) != D(after[7])
    assert hydrogens == 11 and changed == 10
    assert len(report["changes"]) == 11
    assert report["original_template_sha256"] == sha256(template.encode()).hexdigest()
    assert report["original_parameters_sha256"] == sha256(parameters.encode()).hexdigest()
    assert report["derived_template_sha256"] == sha256(revised.encode()).hexdigest()


@pytest.mark.parametrize("change", ("missing-parameter", "conflicting-parameter", "nonpositive-equilibrium", "hydrogen-parent", "nonterminal-hydrogen"))
def test_ambiguous_or_chemically_wrong_distance_derivation_is_refused(change):
    template, parameters = source()
    if change == "missing-parameter": parameters = parameters.replace("CT-H1   340.0  1.0900\n", "")
    elif change == "conflicting-parameter": parameters += "CT-HC   340.0  1.0800\n"
    elif change == "nonpositive-equilibrium": parameters = parameters.replace("1.0900", "-1.0900")
    elif change == "hydrogen-parent": template = template.replace("7  HA    H1    E    6", "7  HA    H1    E    5")
    else: template = template.replace("5  HN1   H     E", "5  HN1   H     M")
    with pytest.raises(ValueError): construct_kcx_hydrogen_distances(template, parameters)
