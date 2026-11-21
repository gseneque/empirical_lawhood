# SPDX-License-Identifier: MPL-2.0
from hashlib import sha256
import json

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import (
    initial_leap_script,
)
from empirical_lawhood.adapters.rubisco.rubisco_response.forecast_core import (
    build_case,
    observed_residues,
)


def test_standard_forecast_deck_and_original_deck_have_distinct_ion_and_check_choices():
    original = initial_leap_script()
    fresh = initial_leap_script(
        random_solvent_replacement=True, explicit_solvated_check=False
    )
    assert original.count("check model\n") == 2 and original.count("addIons model") == 2
    assert (
        original.replace("addIons model", "addIonsRand model").replace(
            "model Cl- 0\ncheck model\nsaveAmberParm", "model Cl- 0\nsaveAmberParm"
        )
        == fresh
    )
    assert fresh.index("check model") < fresh.index("solvateBox")
    assert "saveAmberParm model model.prmtop model.inpcrd" in fresh


def test_parent_residue_origin_preserves_insertion_identity():
    def atom(i, code):
        return f"ATOM  {i:5d}  CA  VAL A  10{code}     23.000  15.000   5.000  1.00  0.00           C  "

    groups = observed_residues("\n".join([atom(1, " "), atom(2, "A"), atom(3, "B")]))
    assert [key[:3] for key, _ in groups] == [
        ("A", 10, " "),
        ("A", 10, "A"),
        ("A", 10, "B"),
    ]


def test_changed_original_refuses_before_amber_entry_and_retains_failure(tmp_path):
    source = tmp_path / "original"
    source.write_bytes(b"recorded")
    selected = {"path": str(source), "sha256": sha256(b"recorded").hexdigest()}
    selection = {"core": selected, "met1": {**selected, "sha256": sha256(b"other").hexdigest()}}
    output = tmp_path / "new-build"
    with pytest.raises(ValueError, match="Changed selected input met1"):
        build_case(selection, "V1-WT", output)
    assert json.loads((output / "build-failure.json").read_bytes())["case"] == "V1-WT"
    assert set(file.name for file in output.iterdir()) == {"build-failure.json"}
