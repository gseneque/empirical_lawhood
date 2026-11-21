"""Exercise the documented disposable RC extension and method-only branch.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.domains.circuits.rc_ladder_numerical_comparison.contracts import ResistorCapacitorLadderEvaluationConfig
from empirical_lawhood.domains.circuits.rc_ladder.campaign import check_native_views
from empirical_lawhood.domains.circuits.rc_ladder.contracts import ResistorCapacitorLadderNativePanel, ResistorCapacitorLadderStudyConfig
from empirical_lawhood.science.records.decoding import decode_canonical_bytes

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def local_boundary(tmp_path_factory):
    temporary = tmp_path_factory.mktemp("worked-rc-copy")
    guide = (ROOT / "docs/development/extending-the-engine.md").read_text()
    region = guide.split("<!-- BEGIN WORKED RC PYTHON -->", 1)[1].split(
        "<!-- END WORKED RC PYTHON -->", 1
    )[0]
    source = region.split("```python\n", 1)[1].split("```", 1)[0]
    path = temporary / "local_rc_extension.py"
    path.write_text(source)
    spec = importlib.util.spec_from_file_location("local_rc_extension", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    study = module.local_study()
    panels = module.local_panels(study)
    (temporary / "study.json").write_bytes(study.canonical_bytes())
    for panel in panels:
        (temporary / f"{panel.view_id}.json").write_bytes(panel.canonical_bytes())
    return temporary, module, study, panels


def test_disposable_local_boundary_matches_an_independent_equation(local_boundary):
    temporary, _, study, panels = local_boundary
    assert (
        decode_canonical_bytes(
            (temporary / "study.json").read_bytes(),
            ResistorCapacitorLadderStudyConfig,
            maximum_bytes=65536,
        )
        == study
    )
    assert study.model.scale_cells == 1
    for panel in panels:
        recovered = decode_canonical_bytes(
            (temporary / f"{panel.view_id}.json").read_bytes(),
            ResistorCapacitorLadderNativePanel,
            maximum_bytes=512 * 1024,
        )
        assert recovered == panel
        assert panel.unit_id == study.unit_id
        assert panel.times_seconds == study.model.output_times_seconds
        allowance = 1e-12 if panel.view_id == "matrix-exponential" else 2e-4
        for clock, row in zip(
            panel.times_seconds, panel.node_voltages_volts, strict=True
        ):
            # Independent KCL, not another evaluation of the production solver.
            expected = (1 - math.exp(-2 * float(clock))) / 2
            assert float(row[0]) == pytest.approx(expected, abs=allowance)
            assert Decimal(0) <= row[0] < Decimal("0.5")
    assert check_native_views(study, panels).independent_unit_count == 1
    assert check_native_views(study, panels).nested_view_count == 2


def test_method_only_consumes_exposed_typed_panels_without_new_source(
    local_boundary, monkeypatch
):
    temporary, module, study, panels = local_boundary

    def refuse(*args, **kwargs):
        raise AssertionError("method attempted another native execution")

    monkeypatch.setattr(module, "run_native_view", refuse)
    monkeypatch.setattr(
        "empirical_lawhood.domains.circuits.rc_ladder.campaign.run_native_view",
        refuse,
    )
    monkeypatch.setattr(
        "empirical_lawhood.domains.circuits.rc_ladder.matrix_exponential.solve_matrix_exponential",
        refuse,
    )
    monkeypatch.setattr(
        "empirical_lawhood.domains.circuits.rc_ladder.refinement.solve_backward_euler",
        refuse,
    )
    config = ResistorCapacitorLadderEvaluationConfig(
        "rc-worked.evaluation-config", study, True
    )
    recovered = decode_canonical_bytes(
        config.canonical_bytes(),
        ResistorCapacitorLadderEvaluationConfig,
        maximum_bytes=512 * 1024,
    )
    result = check_native_views(recovered.study, panels)
    (temporary / "method-check.json").write_bytes(result.canonical_bytes())
    assert result.converged
    assert result.independent_unit_count == 1
    tighter = replace(
        config, study=replace(study, maximum_view_defect_volts=Decimal("1e-8"))
    )
    negative = check_native_views(tighter.study, panels)
    assert not negative.converged
    assert "VOLTAGE_VIEW_DEFECT_ABOVE_FROZEN_LIMIT" in negative.reason_codes
    with pytest.raises(ValueError, match="cannot claim physical-board"):
        replace(config, numerical_only=False)
    with pytest.raises(ValueError, match="two exact solver views"):
        check_native_views(study, (panels[0], panels[0]))


def test_invalid_component_refuses_before_solver(local_boundary, monkeypatch):
    _, module, study, _ = local_boundary
    monkeypatch.setattr(
        module, "run_native_view", lambda *a: pytest.fail("native contact")
    )
    with pytest.raises(ValueError, match="must be positive"):
        invalid_model = replace(study.model, capacitances_farads=(Decimal(0),))
        module.local_panels(replace(study, model=invalid_model))


@pytest.mark.parametrize("broken", (False, True))
def test_documented_command_verifies_the_selected_file_and_retains_its_identity(local_boundary, tmp_path, broken):
    original, _, _, _ = local_boundary
    source = (original / "local_rc_extension.py").read_text()
    if broken:
        source = source.replace('capacitances_farads=(Decimal("1"),)', 'capacitances_farads=(Decimal("2"),)')
    # This copy refuses a second preparation even if a verifier obtains a
    # correct first result. It tests actual calls, not a reported count alone.
    source += '''\n_original_study = local_study
_preparations = 0
def local_study():
    global _preparations
    _preparations += 1
    if _preparations != 1:
        raise AssertionError("model prepared more than once")
    return _original_study()
'''
    selected = tmp_path / "actual_contributor_file.py"
    selected.write_text(source)
    output = tmp_path / "selected-results"
    result = subprocess.run([sys.executable, str(ROOT / "scripts/check_worked_rc_extension.py"),
                             "--module", str(selected), "--output-dir", str(output)],
                            cwd=ROOT, capture_output=True, text=True)
    report = json.loads((output / "verification.json").read_text())
    assert report["module_path"] == str(selected)
    assert report["module_sha256"] == sha256(selected.read_bytes()).hexdigest()
    assert report["model_preparation_calls"] == 1
    assert not (tmp_path / "__pycache__").exists()
    if broken:
        assert result.returncode == 1 and report["status"] == "FAILED"
        assert "independent circuit equation" in report["error"]["message"]
    else:
        assert result.returncode == 0, result.stderr
        assert report["status"] == "PASSED" and report["independent_unit_count"] == 1
        assert (output / "method-check.json").is_file() and (output / "negative-check.json").is_file()


def test_selected_file_verifier_disables_native_calls_during_evaluation(local_boundary, tmp_path, monkeypatch):
    from scripts import check_worked_rc_extension as verifier

    original, _, _, _ = local_boundary
    selected = original / "local_rc_extension.py"

    def illicit_evaluator(study, panels):
        verifier.campaign.run_native_view(study, verifier.campaign.VIEWS[0])

    monkeypatch.setattr(verifier.campaign, "check_native_views", illicit_evaluator)
    with pytest.raises(RuntimeError, match="evaluation-only"):
        verifier.verify_selected_file(selected, tmp_path / "failed-evaluator")
