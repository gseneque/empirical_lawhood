# SPDX-License-Identifier: MPL-2.0
"""Bounded full-read receipt custody on actual exposed PURE workloads."""
import pytest

from empirical_lawhood.infrastructure import artifacts, recursive_custody as owner
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from tests.test_recursive_compact_output_bulk import compact_wave as compact_wave  # noqa: F401
from tests.test_recursive_report_projection import wave as wave  # noqa: F401
from tests.test_recursive_prebatch_readonly_inputs import (
    _profile, _read, scale_cases as scale_cases,  # noqa: F401
)


@pytest.mark.parametrize("damage", ("receipt", "sidecar", "marker", "output"))
def test_full_read_refuses_changed_custody_after_typed_decode_before_scientific_consumption(
        scale_cases, monkeypatch, damage):
    case = scale_cases[0]
    receipt = next(iter(case.full[1]["receipts"].values()))
    relative = ExternalTaskReceiptStore._relative_path(receipt.run_id, receipt.task_id, receipt.attempt_id)
    manifest = case.plane.read_manifest(relative)
    output = next(iter(case.full[1]["outputs"].values()))
    target = case.plane.root.resolve({"receipt": relative, "sidecar": relative + ".manifest.json",
        "marker": manifest.publication.commit_marker_relative_path,
        "output": output.materialization.relative_path}[damage], for_write=False)
    original = target.read_bytes()
    changed, escaped = [], []
    assemble_code = owner._assemble_read_products.__code__
    decode_code = owner.decode_canonical_bytes.__code__
    def observe(frame, event, arg):
        if (event == "return" and frame.f_code is decode_code and not changed
                and frame.f_back.f_code is assemble_code):
            changed.append(True)
            target.write_bytes(b"x" + original[1:])
    def no_native_inspection(**kwargs):
        pytest.fail("changed custody reached native observation or later scientific assessment")
    monkeypatch.setattr(owner, "_inspect_native_observations", no_native_inspection)
    try:
        with pytest.raises((ValueError, artifacts.ArtifactIdentityConflict)):
            with _profile(observe):
                escaped.append(_read(case, full=True))
        assert changed == [True] and not escaped
    finally:
        target.write_bytes(original)


def test_full_read_refuses_receipt_policy_change_inside_bounded_window(scale_cases, monkeypatch):
    case = scale_cases[0]
    original = ExternalTaskReceiptStore.read
    decode_code = owner.decode_canonical_bytes.__code__
    assemble_code = owner._assemble_read_products.__code__
    changed = []
    def observe(frame, event, arg):
        if (event == "return" and frame.f_code is decode_code and not changed
                and frame.f_back.f_code is assemble_code):
            changed.append(True)
            monkeypatch.setattr(ExternalTaskReceiptStore, "read", lambda self, *args, **kwargs: original(self, *args, **kwargs))
    with pytest.raises(ValueError, match="full receipt/byte policy changed"):
        with _profile(observe):
            _read(case, full=True)
    assert changed == [True]
