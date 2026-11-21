# SPDX-License-Identifier: MPL-2.0
"""Source, selection and exact-coordinate controls for inherited-site proposals."""

from decimal import localcontext
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.gp_crystal_sites import (
    select_gp_crystal_sites,
)


def test_unknown_selection_and_changed_source():
    with pytest.raises(ValueError, match="registered"):
        select_gp_crystal_sites(b"", b"", "all-waters")
    with pytest.raises(ValueError, match="coordinate bytes"):
        select_gp_crystal_sites(b"changed", b"", "first-shell")


@pytest.mark.held
@pytest.mark.parametrize(
    ("selection", "count", "digest"),
    [
        (
            "acid-sidechains",
            72,
            "7960153a16b066a1af27ea5a9f75d17fd36ff262b82648fd13d558257b4fa572",
        ),
        (
            "first-shell",
            408,
            "ed42999a86a3b393e53810d2ff5566ed479c587af12e7ce8925c9faf70d9cbcc",
        ),
    ],
)
def test_pinned_original_bytes_and_decimal_context(selection, count, digest):
    deposition = os.getenv("EL_GP_1BWV_CIF")
    refinement = os.getenv("EL_GP_1BWV_REDO_CIF")
    if not deposition or not refinement:
        pytest.skip("select both retained crystallographic source models")
    d, r = Path(deposition).read_bytes(), Path(refinement).read_bytes()
    with pytest.raises(ValueError, match="coordinate bytes"):
        select_gp_crystal_sites(d, r + b"\n", selection)
    with localcontext() as ctx:
        ctx.prec = 4
        raw = select_gp_crystal_sites(d, r, selection)
    assert sha256(raw).hexdigest() == digest
    packet = json.loads(raw)
    assert packet["assembly_atoms"] == 40076
    edits = packet["edits"]
    assert (
        len(edits)
        == len({(e["operator"], e["deposited_atom_id"]) for e in edits})
        == count
    )
    assert {e["author_atom"][0] for e in edits} == set("ACEG")
    assert {e["operator"] for e in edits} == {"1", "2"}
    assert all(e["author_atom"][3] != "HOH" for e in edits)
