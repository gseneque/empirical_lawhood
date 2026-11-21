# SPDX-License-Identifier: MPL-2.0
"""Actual pytest selection separates numerical oracles from software controls."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


def test_ordinary_pytest_loads_purpose_classification(request):
    assert request.config.pluginmanager.hasplugin("scripts.test_purposes")
    assert request.config._el_test_purposes[request.node.nodeid] == {
        "purpose": "conformance", "oracle": None}
    assert request.node.get_closest_marker("conformance") is not None


def collect(tmp_path, body, expression):
    (tmp_path / "purpose_fixture.py").write_bytes(
        (Path(__file__).resolve().parents[1] / "scripts/test_purposes.py").read_bytes())
    (tmp_path / "test_controls.py").write_text("import pytest\n" + body)
    output = tmp_path / "purposes.json"
    (tmp_path / "report_purposes.py").write_text(
        "import json\nfrom pathlib import Path\n"
        "def pytest_collection_finish(session):\n"
        "    Path('purposes.json').write_text(json.dumps({item.nodeid: "
        "session.config._el_test_purposes[item.nodeid] for item in session.items}))\n")
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider",
         "-p", "purpose_fixture", "-p", "report_purposes", "-m", expression],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
        env=dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTEST_ADDOPTS=""))
    return result, json.loads(output.read_text()) if output.exists() else None


def test_purpose_selection_keeps_independent_reference_and_contract_groups_disjoint(tmp_path):
    body = ("@pytest.mark.numerical(oracle='Exact rational partition function')\n"
            "def test_number(): raise AssertionError('collection only')\n"
            "def test_contract(): raise AssertionError('collection only')\n")
    result, numerical = collect(tmp_path, body, "numerical")
    assert result.returncode == 0, result.stdout + result.stderr
    assert numerical == {"test_controls.py::test_number": {
        "purpose": "numerical", "oracle": "Exact rational partition function"}}
    result, conformance = collect(tmp_path, body, "conformance")
    assert result.returncode == 0, result.stdout + result.stderr
    assert conformance == {"test_controls.py::test_contract": {"purpose": "conformance", "oracle": None}}


@pytest.mark.parametrize("declaration", [
    "@pytest.mark.numerical", "@pytest.mark.numerical(oracle='')",
    "@pytest.mark.numerical('unowned reference')", "@pytest.mark.numerical(oracle=1)",
    "@pytest.mark.numerical(oracle='equation', extra='ambiguous')",
    "@pytest.mark.conformance\n@pytest.mark.numerical(oracle='equation')",
    "@pytest.mark.numerical(oracle='one')\n@pytest.mark.numerical(oracle='two')",
])
def test_an_unowned_or_conflicting_numerical_claim_refuses_collection(tmp_path, declaration):
    result, _ = collect(tmp_path, declaration + "\ndef test_bad(): pass\n", "numerical")
    assert result.returncode != 0
    assert "numerical requires one nonempty oracle" in result.stdout + result.stderr


def test_native_input_boundary_is_independent_of_numerical_purpose(tmp_path):
    body = ("@pytest.mark.native('unavailable-solver')\n"
            "@pytest.mark.numerical(oracle='Closed-form trajectory')\n"
            "def test_native_number(): raise AssertionError('no contact')\n"
            "@pytest.mark.numerical(oracle='Exact integer sum')\n"
            "def test_portable_number(): pass\n")
    result, selected = collect(tmp_path, body, "numerical and not native and not held")
    assert result.returncode == 0, result.stdout + result.stderr
    assert list(selected) == ["test_controls.py::test_portable_number"]


def test_ci_cannot_silently_demote_a_required_numerical_reference():
    from scripts import test_profiles

    record = test_profiles.selection_record(sorted(test_profiles.CI_REQUIRED_CASES), "ci")
    record["verification_purposes"] = {node: {"purpose": "numerical", "oracle": "Independent reference"}
                                       for node in test_profiles.CI_NUMERICAL_REQUIRED_CASES}
    test_profiles.require_ci_contracts(record)
    for node in test_profiles.CI_NUMERICAL_REQUIRED_CASES:
        actual = record["verification_purposes"][node]
        record["verification_purposes"][node] = {"purpose": "conformance", "oracle": None}
        with pytest.raises(ValueError, match="missing required independent numerical"):
            test_profiles.require_ci_contracts(record)
        record["verification_purposes"][node] = actual
