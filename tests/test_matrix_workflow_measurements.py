# SPDX-License-Identifier: MPL-2.0
"""Actual descriptor reads and failure retention for release observations."""

import json

import pytest

from empirical_lawhood.infrastructure import bounded_io
from tests.matrix_workflow_measurements import WorkflowMeasurements


def test_actual_bounded_bytes_and_repeated_opens_are_observed_without_payload_retention(tmp_path, monkeypatch):
    payload = b"private-payload-marker" * 4096
    source = tmp_path / "source.bin"
    source.write_bytes(payload)
    destination = tmp_path / "observations.json"
    observed = WorkflowMeasurements(destination, monkeypatch, selection="two-complete-reads")

    def read_twice():
        for _ in range(2):
            assert bounded_io.read_bounded_bytes(source, maximum_bytes=len(payload)) == payload

    observed.call("actual_reads", read_twice)
    observed.finish()
    report = json.loads(destination.read_bytes())
    row, = report["phases"]
    assert row["status"] == report["status"] == "SUCCEEDED"
    assert row["parent_callbacks_and_bounded_io"]["bounded_read_bytes"] == 2 * len(payload)
    assert row["distinct_bounded_paths"] == 1 and row["maximum_bounded_opens_for_one_path"] == 2
    assert row["samples"] >= 2
    assert b"private-payload-marker" not in destination.read_bytes()


def test_failed_read_retains_original_exception_and_nonpassing_observation(tmp_path, monkeypatch):
    source = tmp_path / "too-large.bin"
    source.write_bytes(b"too large")
    destination = tmp_path / "failed.json"
    observed = WorkflowMeasurements(destination, monkeypatch, selection="actual-refusal")
    with pytest.raises(bounded_io.BoundedFileIOError):
        observed.call("refused_read", bounded_io.read_bounded_bytes, source, maximum_bytes=1)
    report = json.loads(destination.read_bytes())
    assert report["status"] == report["phases"][0]["status"] == "FAILED"
    assert report["phases"][0]["exception_type"] == "BoundedFileIOError"
    with pytest.raises(ValueError, match="cannot be finalized"):
        observed.finish()


def test_existing_evidence_is_not_overwritten_and_running_is_nonterminal(tmp_path, monkeypatch):
    destination = tmp_path / "existing.json"
    observed = WorkflowMeasurements(destination, monkeypatch, selection="not-complete")
    original = destination.read_bytes()
    assert json.loads(original)["status"] == "RUNNING"
    with pytest.raises(ValueError, match="new absolute"):
        WorkflowMeasurements(destination, monkeypatch, selection="collision")
    assert destination.read_bytes() == original
    observed.call("complete-phase", lambda: None)
    assert json.loads(destination.read_bytes())["status"] == "RUNNING"
