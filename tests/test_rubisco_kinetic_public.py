# SPDX-License-Identifier: MPL-2.0
"""Installed W1 copied-input/service acceptance; disclosed development only."""

import json
from pathlib import Path

import pytest

from empirical_lawhood.api.configuration import validate_configuration
from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding, load_recursive_draft
from empirical_lawhood.api.recursive_execution import read_recursive_wave, run_recursive_wave
from empirical_lawhood.api import matrix_numerical_provenance as provenance_owner
from empirical_lawhood.api.workflows import show_workflow
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_assay_bridge import KineticJointTargetAssessment
from scripts.generate_rubisco_kinetic_example import examples
from tests.test_recursive_public_service import _plane

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "programmes/biology/photosynthesis/workflows/rubisco-kinetic-join"


def test_public_inputs_are_strict_declared_and_exposed_not_measured():
    workflow = show_workflow("rubisco-kinetic-join")
    assert {str(EXAMPLE / name) for name in examples()} <= {str(ROOT / row.path) for row in workflow.inputs}
    assert "zero fresh biological units" in workflow.scientific_ceiling
    for name, payload in examples().items():
        assert (EXAMPLE / name).read_bytes() == payload
        consumer = "recursive-inquiry" if name == "draft.json" else "rubisco-kinetic-" + name.removesuffix(".json")
        report = validate_configuration(EXAMPLE / name, consumer=consumer)
        assert report["consumer_byte_ready"] and not report["authority_granted"]
        assert not report["external_prerequisites_checked"]


def test_installed_service_keeps_complete_adverse_roster_and_recovers(tmp_path, monkeypatch):
    # One frozen exposed software source snapshot; current-owner substitutions
    # are separately refused. This seam creates no fresh scientific qualification.
    source = implementation_binding(ROOT)
    from empirical_lawhood.api import recursive_authoring as author, recursive_execution as execute
    observed = provenance_owner.capture_matrix_provenance(project_root=ROOT)
    monkeypatch.setattr(author, "implementation_binding", lambda root, **kwargs: source)
    monkeypatch.setattr(execute, "implementation_binding", lambda root, **kwargs: source)
    monkeypatch.setattr(provenance_owner, "capture_matrix_provenance", lambda **kwargs: observed)
    plane = _plane(tmp_path / "custody")
    directory = tmp_path / "custody/w1"
    draft = load_recursive_draft(EXAMPLE / "draft.json")
    bindings = tuple((f"external.rubisco-kinetic-join.{name}", EXAMPLE / (name + ".json"))
                     for name in ("supply", "query", "comparison"))
    authored = author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane,
        output_dir=directory, input_bindings=bindings)
    assert authored["native_contact"] == "none" and authored["task_count"] == 2
    report = run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane)
    assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 0
    terminal = next(iter(report["terminal_products"].values()))
    assessment_doc = next(value for value in terminal.values() if value["schema"] == KineticJointTargetAssessment.SCHEMA)
    # The retained public report is a decoded JSON document, with JSON lists;
    # encode that document exactly rather than treating it as a typed record.
    raw = (json.dumps(assessment_doc, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                     allow_nan=False) + "\n").encode("utf-8")
    assessment = decode_canonical_bytes(raw, KineticJointTargetAssessment, maximum_bytes=None)
    assert len(assessment.member_dispositions) == 3
    assert assessment.robust_conditional_target_disposition == "UNEVALUABLE"
    assert assessment.nomination_readiness == "NOT_ESTABLISHED" and assessment.probability_of_joint_success is None
    assert len(assessment.assay_bridge.member_results) == 3
    assert assessment.assay_bridge.assay_solver_calls == 1
    assert assessment.assay_bridge.molecular_native_contacts == 0
    def no_repeat(*args, **kwargs):
        raise AssertionError("completed evidence reacquired")
    monkeypatch.setattr(LocalProcessExecutor, "execute", no_repeat)
    assert read_recursive_wave(directory=directory, artifact_writer=plane) == report
    assert run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane) == report


def test_supplied_member_substitution_refuses_before_execution(tmp_path):
    plane = _plane(tmp_path / "custody")
    changed = tmp_path / "changed.json"
    changed.write_bytes((EXAMPLE / "supply.json").read_bytes().replace(b'"DISCLOSED_SYNTHETIC"', b'"CONDITIONAL_MODEL"'))
    bindings = tuple((f"external.rubisco-kinetic-join.{name}", changed if name == "supply" else EXAMPLE / (name + ".json"))
                     for name in ("supply", "query", "comparison"))
    with pytest.raises(ValueError, match="selected digest"):
        author_recursive_wave(draft=load_recursive_draft(EXAMPLE / "draft.json"), project_root=ROOT,
            artifact_writer=plane, output_dir=tmp_path / "custody/unentered", input_bindings=bindings)
    assert not (tmp_path / "custody/unentered").exists()
