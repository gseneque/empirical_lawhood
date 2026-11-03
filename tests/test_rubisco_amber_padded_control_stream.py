# SPDX-License-Identifier: MPL-2.0
"""Exposed format/stream controls; no authentic molecular population is read."""

from decimal import Decimal

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.amber_parameters import (
    assigned_census, read_prmtop, read_prmtop_lines,
)
from tests.test_rubisco_preparation_integrity import amber_text, topology


def padded(text):
    return "\n".join(line.ljust(80) if line.startswith(("%FLAG ", "%FORMAT")) else line
                     for line in text.splitlines()) + "\n"


def test_actual80_column_controls_preserve_complete_literal_population_and_values():
    original = amber_text(topology())
    result = read_prmtop(padded(original))
    assert result == read_prmtop(original)
    assert result["CHARGE"] == (Decimal("9.11115000"), Decimal("-9.11115000"), Decimal(0), Decimal(0))
    assert assigned_census(result)["term_census"] == dict(atoms=4, bonds=2, angles=1, dihedrals=1)


def test_selected_single_pass_stream_retains_every_requested_atom_and_residue():
    selected = ("POINTERS", "ATOM_NAME", "ATOMIC_NUMBER", "RESIDUE_LABEL", "RESIDUE_POINTER")
    text = padded(amber_text(topology()))
    iterator = iter(text.splitlines(keepends=True))
    result = read_prmtop_lines(iterator, selected_flags=selected)
    assert result == {key: read_prmtop(text)[key] for key in selected}
    assert result["ATOM_NAME"] == ("C", "N", "CA", "H")
    assert result["ATOMIC_NUMBER"] == (6, 7, 6, 1)
    assert next(iterator, None) is None


@pytest.mark.parametrize("change", ("scale", "suffix", "overwide-data", "missing-format",
                                     "blank-format", "duplicate", "unknown-extension", "missing-selected"))
def test_stream_format_repair_cannot_weaken_existing_controls(change):
    text = padded(amber_text(topology()))
    selected = ("ATOM_NAME", "ATOMIC_NUMBER", "RESIDUE_LABEL", "RESIDUE_POINTER")
    if change == "scale":
        text = text.replace("%FORMAT(10i8)", "%FORMAT(1P10i8)", 1)
    elif change == "suffix":
        text = text.replace("%FORMAT(20a4)", "%FORMAT(20a4)JUNK", 1)
    elif change == "overwide-data":
        text = text.replace("C   N   CA  H   \n", "X" * 81 + "\n", 1)
    elif change == "missing-format":
        text += "%FLAG TITLE2\n"
    elif change == "blank-format":
        text = text.replace("%FORMAT(20a4)", "\n%FORMAT(20a4)", 1)
    elif change == "duplicate":
        text += "%FLAG ATOM_NAME\n%FORMAT(20a4)\nC\n"
    elif change == "unknown-extension":
        text += "%FLAG CMAP_COUNT\n%FORMAT(10I8)\n       1\n"
    elif change == "missing-selected":
        selected += ("RESIDUE_NUMBER",)
    with pytest.raises(ValueError):
        read_prmtop_lines(iter(text.splitlines()), selected_flags=selected)


def test_selected_stream_does_not_claim_validation_of_unselected_force_values():
    text = "%VERSION exposed\n%FLAG ATOM_NAME\n%FORMAT(20a4)\nC\n%FLAG CHARGE\n%FORMAT(5E16.8)\nnot-a-number\n"
    assert read_prmtop_lines(iter(text.splitlines()), selected_flags=("ATOM_NAME",)) == {"ATOM_NAME": ("C",)}
    with pytest.raises(ValueError, match="numeric"):
        read_prmtop(text)
