"""Public RC discovery and exact receipt recovery, with exposed test failures.

SPDX-License-Identifier: MPL-2.0
"""

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from typer.testing import CliRunner

from empirical_lawhood.adapters.methods.rc_prerequisite_chain import science
from empirical_lawhood.api import rc_prerequisite_chain as api
from empirical_lawhood.api.configuration import prepare_configuration, validate_configuration
from empirical_lawhood.api.workflows import show_workflow
from empirical_lawhood.cli.app import app
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ExternalRootContract
from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "1" * 40


@pytest.fixture
def plane(tmp_path):
    directory = tmp_path / "synthetic-rc-store"
    directory.mkdir()
    return ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "synthetic.rc-store", "software conformance storage", str(directory),
        str(next(parent for parent in directory.parents if parent.is_mount())),
        OperatorStorageProfile.SCHEMA, 1, None, None, (),
    )))


@pytest.fixture
def config():
    original = science.default_chain_config()
    return replace(original, protocol=replace(original.protocol, minimum_free_bytes=1))


@pytest.fixture
def numerical_boundary(monkeypatch):
    # This explicit synthetic provenance is software-only. Native runtime/source
    # authentication has its own selected owner and regression tests.
    sources = (("synthetic.py", "2" * 64),)
    runtime = canonical_json_bytes({
        "machine": "x86_64", "numpy": "2.4.6", "python": "3.11.14",
        "scipy": "1.17.1", "system": "linux", "threadpools": (),
    }).decode()
    provenance = NumericalProducingProvenance(
        runtime, "3" * 64, sources, sha256(canonical_json_bytes(sources)).hexdigest(), COMMIT, False,
    )
    monkeypatch.setattr(api, "capture_matrix_provenance", lambda **_: provenance)
    monkeypatch.setattr(api, "numerical_package_code_sha256", lambda: provenance.code_sources_sha256)
    monkeypatch.setattr(api, "selected_dependency_lock_sha256", lambda _: provenance.dependency_lock_sha256)
    calls = Counter()

    def explicit_failure(selected, unit_id):
        calls[unit_id] += 1
        return science.failed_unit_result(selected, unit_id)

    monkeypatch.setattr(science, "evaluate_unit", explicit_failure)
    return provenance, calls


def _run(config, plane, **kwargs):
    return api.run_rc_chain(
        config=config, artifact_writer=plane, project_root=ROOT,
        implementation_commit=COMMIT, **kwargs,
    )


def _bytes(plane):
    root = Path(plane.root.contract.canonical_path)
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def test_public_copy_prepare_prove_preserves_complete_design_without_native_contact(tmp_path, monkeypatch):
    original = ROOT / "programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/input.json"
    edited = tmp_path / "edited.json"
    edited.write_text(json.dumps(json.loads(original.read_bytes()), indent=2) + "\n")
    before = edited.read_bytes()
    report = validate_configuration(edited, consumer="rc-prerequisite-chain")
    assert report["preparation_required"] and not report["external_prerequisites_checked"]
    prepared = tmp_path / "prepared.json"
    prepare_configuration(edited, prepared, consumer="rc-prerequisite-chain")
    assert edited.read_bytes() == before
    assert prepared.read_bytes() == original.read_bytes()
    monkeypatch.setattr(science, "evaluate_unit", lambda *_: pytest.fail("proof acquired native data"))
    result = CliRunner().invoke(app, ["campaign", "rc-chain-prove", "--input", str(prepared)])
    assert result.exit_code == 0, result.output
    proof = json.loads(result.stdout)
    assert proof["unit_count"] == 11 and proof["variant_count"] == 10
    assert proof["maximum_native_steps"] <= 2_000_000
    assert proof["native_contact"] == "none" and not proof["scientific_execution_performed"]
    assert proof["scientific_authority"] == "NONE"
    assert show_workflow("rc-prerequisite-chain").scientific_ceiling


def test_scientific_proof_imports_no_numerical_stack_from_an_unrelated_directory(tmp_path):
    script = """
import builtins
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'numpy', 'scipy'}:
        raise AssertionError('proof imported numerical stack: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.science import default_chain_config, prove_chain
assert prove_chain(default_chain_config()).unit_count == 11
"""
    process = subprocess.run([sys.executable, "-c", script], cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
        text=True, capture_output=True, check=False)
    assert process.returncode == 0, process.stderr
    assert not tuple(tmp_path.iterdir())


def test_complete_failure_census_reads_original_producer_after_reader_commit_changes(config, plane, numerical_boundary, monkeypatch):
    provenance, calls = numerical_boundary
    report = _run(config, plane)
    assert calls == Counter({unit.unit_id: 1 for unit in config.units})
    summary = report["summary"]
    assert summary["unit_count"] == 11 and summary["nested_variant_count"] == 110
    assert len(summary["unit_result_sha256s"]) == 11
    counts = [row["value"] for row in summary["outcome_counts"]]
    assert all(row["count"] == 11 for row in counts if row["state"] == "UNEVALUABLE")
    original = _bytes(plane)
    monkeypatch.setattr(science, "evaluate_unit", lambda *_: pytest.fail("retained read reacquired native observations"))
    monkeypatch.setattr(api, "capture_matrix_provenance", lambda **_: pytest.fail("retained read inspected reader runtime"))
    assert api.read_rc_chain(config=config, artifact_writer=plane) == report
    assert api.run_rc_chain(config=config, artifact_writer=plane, project_root=ROOT,
        implementation_commit="f" * 40) == report
    assert report["observed_producing_git_head"] == provenance.observed_git_head == COMMIT
    assert _bytes(plane) == original


def test_receipt_recovery_keeps_completed_unit_and_reduces_complete_denominator(config, plane, numerical_boundary):
    _, calls = numerical_boundary

    def interrupt_between_units(done, total):
        assert total == 11
        if done == 1:
            raise RuntimeError("software test interruption between completed units")

    with pytest.raises(RuntimeError, match="between completed"):
        _run(config, plane, progress=interrupt_between_units)
    first_path = f"runs/{api.rc_chain_run_id(config)}/outputs/{config.units[0].unit_id}.json"
    before = _bytes(plane)[first_path]
    report = _run(config, plane)
    assert calls == Counter({unit.unit_id: 1 for unit in config.units})
    assert _bytes(plane)[first_path] == before
    assert report["summary"]["unit_count"] == len(config.units)


def test_unknown_contact_refuses_repetition_without_hiding_previous_receipts(config, plane, numerical_boundary):
    _, calls = numerical_boundary
    custody = api._custody(config, plane, COMMIT)
    custody.begin_native_effect(config.units[0].unit_id)
    with pytest.raises(ValueError, match="interrupted contact"):
        _run(config, plane)
    assert not calls


def test_source_drift_refuses_before_first_native_effect(config, plane, numerical_boundary, monkeypatch):
    _, calls = numerical_boundary
    monkeypatch.setattr(api, "numerical_package_code_sha256", lambda: "f" * 64)
    with pytest.raises(ValueError, match="source or dependency lock changed"):
        _run(config, plane)
    assert not calls
    assert not any("/inputs/effects/" in name for name in _bytes(plane))


def test_walltime_budget_refuses_before_first_native_effect(config, plane, numerical_boundary, monkeypatch):
    _, calls = numerical_boundary
    observations = iter((0, 601))
    monkeypatch.setattr(api, "monotonic", lambda: next(observations))
    with pytest.raises(ValueError, match="wall-time budget"):
        _run(config, plane)
    assert not calls
    assert not any("/inputs/effects/" in name for name in _bytes(plane))


def test_changed_unit_bytes_and_incomplete_census_refuse_retained_read(config, plane, numerical_boundary):
    _run(config, plane)
    path = Path(plane.root.contract.canonical_path) / f"runs/{api.rc_chain_run_id(config)}/outputs/{config.units[-1].unit_id}.json"
    original = path.read_bytes()
    path.write_bytes(original + b" ")
    with pytest.raises((ValueError, RuntimeError)):
        api.read_rc_chain(config=config, artifact_writer=plane)
    path.write_bytes(original)
    path.unlink()
    with pytest.raises((ValueError, RuntimeError)):
        api.read_rc_chain(config=config, artifact_writer=plane)
