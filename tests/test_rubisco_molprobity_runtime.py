# SPDX-License-Identifier: MPL-2.0
from hashlib import sha256
import json

import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response import molprobity_runtime as runtime


def _install(prefix):
    python = prefix / "bin" / "python3"
    python.parent.mkdir()
    python.write_bytes(b"interpreter")
    (python.parent / "python").symlink_to("python3")
    grids = prefix / "tables"
    grids.mkdir()
    (grids / "rama.data").write_bytes(b"grid")
    raw = json.dumps(dict(
        schema="empirical-lawhood/molprobity-runtime-installation/v1",
        prefix=str(prefix), lock_sha256=runtime.LOCK_SHA256, chem_data_sha256=runtime.CHEM_DATA_SHA256,
        reference_selection=runtime.DATA_SELECTION, cctbx_version=runtime.VERSION,
        inventory=runtime.runtime_inventory(prefix),
    )).encode()
    (prefix / runtime.RECEIPT).write_bytes(raw)
    return sha256(raw).hexdigest()


@pytest.mark.parametrize("change", ("grid", "executable", "mode", "extra", "remove", "link", "receipt"))
def test_runtime_reauthenticates_scoring_tables_program_and_complete_inventory(tmp_path, change):
    digest = _install(tmp_path)
    assert runtime.verify_runtime(tmp_path, receipt_sha256=digest)["python"] == str(tmp_path / "bin/python")
    grid, program = tmp_path / "tables/rama.data", tmp_path / "bin/python3"
    if change == "grid":
        grid.write_bytes(b"GriD")
    elif change == "executable":
        program.write_bytes(b"wrong_program")
    elif change == "mode":
        program.chmod(program.stat().st_mode ^ 0o100)
    elif change == "extra":
        (grid.parent / "unselected").write_bytes(b"")
    elif change == "remove":
        grid.unlink()
    elif change == "link":
        (tmp_path / "bin/python").unlink()
        (tmp_path / "bin/python").symlink_to(tmp_path.parent)
    else:
        (tmp_path / runtime.RECEIPT).write_bytes(b"{}")
    with pytest.raises(ValueError):
        runtime.verify_runtime(tmp_path, receipt_sha256=digest)


def test_installer_selects_required_links_and_dictionaries_for_both_chemical_states():
    from scripts.prepare_molprobity_runtime import chemistry_member
    assert chemistry_member("site-packages/chem_data/geostd/rna_dna/chain_link_rna2p.cif")
    for comp in ("KCX", "RUB", "CAP", "ILE", "MET"):
        assert chemistry_member(f"site-packages/chem_data/geostd/{comp[0].lower()}/data_{comp}.cif")
    assert not chemistry_member("site-packages/chem_data/geostd/q/data_Q6G.cif")
    with pytest.raises(ValueError, match="unexpected archive path"):
        chemistry_member("site-packages/chem_data/../not-the-selected-data")


def test_overall_molprobity_score_needs_three_complete_matching_components():
    import math
    from empirical_lawhood.api.domain_composition.rubisco_response.molprobity_read import assess_overall_score
    score = 0.5 + 0.426 * math.log(11) + 0.33 * math.log(2) + 0.25 * math.log(4)
    raw = dict(cctbx_molprobity_score=score, components={
        "ramalyze": {"native_favored": 95, "native_total": 100},
        "rotalyze": {"native_outliers": 2, "native_total": 100},
    })
    rows = {"ramalyze": dict(status="REVIEW_OUTLIERS", raw_rows=100, joined=100, expected=100, categories={"FAVORED": 95}),
            "rotalyze": dict(status="REVIEW_OUTLIERS", raw_rows=100, joined=100, expected=100, categories={"OUTLIER": 2}),
            "clashscore": dict(status="REVIEW_OUTLIERS", clashscore=10.)}
    complete = assess_overall_score(raw, rows)
    assert complete["score"] == score and complete["status"] == "RECONSTRUCTED"
    rows["ramalyze"].update(expected=124, status="UNEVALUABLE")
    partial = assess_overall_score(raw, rows)
    assert partial["status"] == "RECONSTRUCTED_NATIVE_POPULATION_ONLY"
    assert partial["score"] is None and partial["reported_population_score"] == score
    assert partial["residue_populations"]["ramalyze"] == {"reported": 100, "assigned": 124}
    with pytest.raises(ValueError, match="independent component"):
        assess_overall_score(dict(raw, cctbx_molprobity_score=0.5), rows)
    rows["ramalyze"]["joined"] = 99
    with pytest.raises(ValueError, match="outside the selected source"):
        assess_overall_score(raw, rows)
    rows["ramalyze"]["joined"] = 100
    rows["rotalyze"]["raw_rows"] = 98
    with pytest.raises(ValueError, match="denominator"):
        assess_overall_score(raw, rows)
    rows["clashscore"]["status"] = "UNEVALUABLE"
    assert assess_overall_score(raw, rows) == {"status": "UNEVALUABLE", "score": None}
