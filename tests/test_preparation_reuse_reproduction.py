# SPDX-License-Identifier: MPL-2.0
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from empirical_lawhood.api.preparation_reuse_operands import (
    ReleasedOperands,
    WORKFLOW,
    open_released_operands,
)
from empirical_lawhood.api.preparation_reuse_reproduction import reproduce_preparation_reuse

OPERANDS = Path(__file__).resolve().parents[1] / WORKFLOW / "operands"


@pytest.mark.parametrize("study", ("r23", "r24", "r25", "r26", "r27"))
def test_released_experiment_recomputes_the_scientific_readout(study):
    report = reproduce_preparation_reuse(study=study, operand_directory=OPERANDS)
    assert report["scope"] == "EXPOSED_NUMERICAL_REPRODUCTION"
    assert not report["new_qualification"] and report["new_native_acquisitions"] == 0
    result = report["result"]
    if study == "r23":
        assert result["Q"]["constructor_crossings"] == 7
        assert len(result["interrupted_qualification"]["authenticated_prefixes"]) == 8
        assert result["E"]["report"]["value"]["covered_counts"] == [0, 7966, 0]
        assert result["E"]["diagnostics"]["counterfactuals"]["support_bypassed_F"]["joint_pairs_H_N_P"] == [
            7914,
            7966,
            7951,
        ]
        assert result["historical"]["covered_pairs"] == [0, 7965, 0]
    elif study == "r24":
        assert len(result["interrupted"]["roots"]) == 64
        for cohort, joint, cached, p in (("retained", 62, 60, 0.25), ("disjoint", 58, 57, 0.5)):
            report = result[cohort]
            stats = report["statistics"]
            assert (stats["joint_successes"], stats["method_joint_success_counts"]["cached"]) == (
                joint,
                cached,
            )
            assert stats["false_admission_episodes"] == 0 and stats["added_use_one_sided_exact_p"] == p
            assert len(report["roots"]) == 64
            assert report["handoff_errors"]["response-x"]["handoff_error"]["scored_cells"] == 1024
    elif study == "r25":
        assert result["statistics"]["covered_pairs"] == [7038, 7333, 7050]
        assert result["statistics"]["optimistic_headroom"]["mean"] == 295 / 8192
        assert (
            len(result["roots"]) == 32 and result["original_operation"]["source_terminal_status"] == "BLOCKED"
        )
    elif study == "r26":
        key = "high-temperature.joint-increasing"
        assert [result["slots"][key + "." + k]["delivered"] for k in ("triggered", "fixed")] == [97, 83]
        assert result["paired_structural_delivery"][key + ".triggered_vs_fixed"]["harm"] == 10
        assert len(result["roots"]) == 128 and all(len(r["slots"]) == 12 for r in result["roots"])
    else:
        assert result["joint_successes"] == [5966, 5963]
        assert result["headroom_roots"] == 0 and result["folds"] == 4
        assert len(result["roots"]) == 24 and not result["eligible"]


def test_released_members_reject_substitution_and_missing_roots(tmp_path):
    members = {"root": {"size": 1, "sha256": sha256(b"a").hexdigest()}}
    (tmp_path / "r25.json").write_text(
        json.dumps({"study": "r25", "format": 1, "context": {}, "members": members})
    )
    with ZipFile(tmp_path / "r25.zip", "w") as archive:
        archive.writestr("root", b"b")
    with ZipFile(tmp_path / "r25.zip") as archive, pytest.raises(ValueError, match="digest"):
        ReleasedOperands({"context": {}, "members": members}, archive).raw("root")
    with ZipFile(tmp_path / "r25.zip", "w") as archive, pytest.raises(ValueError, match="census"):
        ReleasedOperands({"context": {}, "members": members}, archive)
    with pytest.raises(ValueError, match="manifest"), open_released_operands(tmp_path, "r25"):
        pass


def test_closed_panel_refuses_missing_acquisition_or_entered_reduction():
    from types import SimpleNamespace
    from empirical_lawhood.api.closed_matrix_panels import refusal_checks

    plan = SimpleNamespace(source_plan=SimpleNamespace(object_id="run"))
    terminal = SimpleNamespace(run_id="run", operational_status="BLOCKED")
    with pytest.raises(ValueError, match="acquisition"):
        refusal_checks(None, terminal, [], {"acquire"}, {"analyse"}, plan, control=False)
    attempt = {"task_id": "analyse", "receipt_sha256": "present", "operational_status": "FAILED"}
    with pytest.raises(ValueError, match="receipt-free"):
        refusal_checks(None, terminal, [attempt], {"analyse"}, {"analyse"}, plan, control=False)


def test_native_reproduction_cannot_open_a_held_cohort(tmp_path):
    from empirical_lawhood.api.preparation_reuse_native import reproduce_native_roots

    with pytest.raises(ValueError, match="published"):
        reproduce_native_roots(study="r27", cohort="confirmation", directory=tmp_path)
