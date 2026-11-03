# SPDX-License-Identifier: MPL-2.0
"""Actual PURE receipt reuse retains fresh complete custody; no native work."""
from collections import Counter
from contextlib import nullcontext
from dataclasses import replace

import pytest

from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.infrastructure import recursive_custody as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from tests.test_recursive_report_projection import wave as wave  # noqa: F401


@pytest.mark.parametrize("format", ("documents", "references", "compact"))
@pytest.mark.parametrize("mode", ("unscoped", "scoped", "custom-policy", "foreign-store"))
def test_actual_pure_reports_reuse_only_exact_scoped_attempt_receipts(wave, monkeypatch, format, mode):
    arguments = dict(directory=wave.directory, include_products=True, terminal_product_format=format)
    expected = execution.read_recursive_wave(artifact_writer=wave.plane, **arguments)
    calls = []
    original_read = ExternalTaskReceiptStore.read
    def read(self, run, task, attempt):
        value = original_read(self, run, task, attempt)
        if value is not None:
            calls.append((task, attempt))
        return value
    monkeypatch.setattr(ExternalTaskReceiptStore, "read", read)
    if mode == "foreign-store":
        assemble = owner._assemble_read_products
        class ForeignStore(ExternalTaskReceiptStore):
            pass
        def foreign(**kwargs):
            kwargs["store"] = ForeignStore(kwargs["plane"])
            return assemble(**kwargs)
        monkeypatch.setattr(owner, "_assemble_read_products", foreign)
    with (nullcontext(wave.plane) if mode == "unscoped" else wave.plane.verification_scope()) as plane:
        if mode == "custom-policy":
            plane.verify_manifest = plane.verify_manifest
        actual = execution.read_recursive_wave(artifact_writer=plane, **arguments)
    assert actual == expected
    expected_calls = 1 if mode == "scoped" else 2
    assert Counter(calls) == Counter({(receipt.task_id, receipt.attempt_id): expected_calls
        for receipt in actual[1]["receipts"].values()})
    assert actual[0]["new_native_contact_count"] == 0


@pytest.mark.parametrize("format", ("compact", "documents"))
@pytest.mark.parametrize("member", ("receipt", "sidecar"))
def test_changed_receipt_after_actual_census_refuses_before_any_product_bytes(wave, monkeypatch, member, format):
    census = owner._operational_census
    changed = []
    digest = owner.bounded_file_sha256
    def mutate(**kwargs):
        result = census(**kwargs)
        receipt = next(iter(result[2].values()))
        relative = ExternalTaskReceiptStore._relative_path(receipt.run_id, receipt.task_id, receipt.attempt_id)
        path = kwargs["store"].plane.root.resolve(relative + (".manifest.json" if member == "sidecar" else ""), for_write=False)
        raw = path.read_bytes()
        changed.append((path, raw))
        path.write_bytes(raw + b" ")
        return result
    def no_products(*args, **kwargs):
        if changed:
            pytest.fail("changed receipt reached product-byte consumption")
        return digest(*args, **kwargs)
    monkeypatch.setattr(owner, "_operational_census", mutate)
    monkeypatch.setattr(owner, "bounded_file_sha256", no_products)
    try:
        with pytest.raises(ArtifactIdentityConflict, match="changed"):
            with (wave.plane.read_context() if format == "documents" else wave.plane.verification_scope()) as plane:
                execution.read_recursive_wave(directory=wave.directory, artifact_writer=plane,
                    include_products=True, terminal_product_format=format)
    finally:
        for path, raw in changed:
            path.write_bytes(raw)
    assert len(changed) == 1


@pytest.mark.parametrize("damage", ("missing", "foreign-attempt", "untyped"))
def test_scoped_attempt_map_substitution_refuses_without_a_fresh_read_fallback(wave, monkeypatch, damage):
    census = owner._operational_census
    after = []
    read = ExternalTaskReceiptStore.read
    def admitted(**kwargs):
        rows, events, receipts = census(**kwargs)
        copied = dict(receipts)
        key = next(iter(copied))
        if damage == "missing":
            del copied[key]
        elif damage == "foreign-attempt":
            copied[key] = replace(copied[key], attempt_id=copied[key].attempt_id + ".foreign")
        else:
            copied[key] = object()
        after.append(True)
        return rows, events, copied
    def no_fallback(self, *args, **kwargs):
        if after:
            pytest.fail("invalid authenticated attempt map fell back to another store read")
        return read(self, *args, **kwargs)
    monkeypatch.setattr(owner, "_operational_census", admitted)
    monkeypatch.setattr(ExternalTaskReceiptStore, "read", no_fallback)
    with pytest.raises(ValueError, match="authenticated attempt census"):
        with wave.plane.verification_scope() as plane:
            execution.read_recursive_wave(directory=wave.directory, artifact_writer=plane,
                include_products=True, terminal_product_format="compact")
    assert after == [True]
