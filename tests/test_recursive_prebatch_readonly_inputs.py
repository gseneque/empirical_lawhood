# SPDX-License-Identifier: MPL-2.0
"""Actual exposed PURE reads: stock phase batching, byte counts and refusals.

The two valid original fold selections are software workloads, never biological units,
new Matrix coordinates, RNG reservations, native acquisitions or qualification.
"""
from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
import json
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.infrastructure import artifacts, bounded_io, recursive_custody as owner
from empirical_lawhood.infrastructure import recovery as recovery_owner, task_receipts
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile
from tests.test_recursive_compact_output_bulk import compact_wave as compact_wave  # noqa: F401
from tests.test_recursive_report_projection import ROOT, wave as wave  # noqa: F401


def _workloads():
    """Two valid existing exposed study selections; no new sample identities."""
    from tests.test_rubisco_historical_recursive import _inputs
    original, slices = _inputs()
    return tuple((count, replace(original, science_id=f"science.exposed.prebatch-{count}",
        folds=original.folds[:count]), tuple(value for value in slices
            if value.fold_id in {fold.fold_id for fold in original.folds[:count]})) for count in (1, 2))


@pytest.fixture(scope="module")
def scale_cases(compact_wave, wave):
    from empirical_lawhood.adapters.methods.rubisco_historical.recursive_translation import historical_recursive_draft
    cases = []
    for count, science, selected_slices in _workloads():
        draft = historical_recursive_draft(science, tuple(sorted(selected_slices, key=lambda value: value.slice_id)),
            draft_id=f"draft.exposed.prebatch-{count}")
        assert len(draft.operations) == 2 * count + 2
        root = compact_wave.directory.parent / f"prebatch-software-{count}"
        root.mkdir()
        bindings = []
        for value in selected_slices:
            path = root / (value.slice_id + ".json")
            path.write_bytes(value.canonical_bytes())
            bindings.append(("external." + value.slice_id, path))
        directory = root / "authored"
        # Actual settled-source admission and all real registered owners remain
        # active. Only the existing PURE executor fixture is restored here.
        author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=compact_wave.plane,
            output_dir=directory, input_bindings=tuple(bindings))
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(LocalProcessExecutor, "execute", wave.executor_execute)
            result = execution.run_recursive_wave(directory=directory, project_root=ROOT,
                artifact_writer=compact_wave.plane, terminal_product_format="compact")
        assert result["status"] == "SUCCEEDED" and result["new_native_contact_count"] == 0
        compact = execution.read_recursive_wave(directory=directory, artifact_writer=compact_wave.plane,
            include_products=True, terminal_product_format="compact")
        full = execution.read_recursive_wave(directory=directory, artifact_writer=compact_wave.plane,
            include_products=True)
        cases.append(SimpleNamespace(directory=directory, plane=compact_wave.plane,
            compact=compact, full=full, tasks=2 * count + 2))
    return tuple(cases)


def _read(case, *, plane=None, full=False):
    return execution.read_recursive_wave(directory=case.directory,
        artifact_writer=case.plane if plane is None else plane, include_products=True,
        terminal_product_format="documents" if full else "compact")


@contextmanager
def _profile(callback):
    previous = sys.getprofile()
    def observe(frame, event, arg):
        callback(frame, event, arg)
        if previous is not None:
            previous(frame, event, arg)
    sys.setprofile(observe)
    try:
        yield
    finally:
        sys.setprofile(previous)


def _measure(case, monkeypatch, *, serial=False, full=False):
    inputs, assemble = execution._external_inputs, owner._assemble_read_products
    phase, counts = [], Counter()
    guard_code = artifacts.ExternalArtifactPlane._require_verification_snapshot_paths.__code__
    seal_code = artifacts.ExternalArtifactPlane._track_verification_snapshot.__code__
    physical_code = artifacts.ExternalArtifactPlane._verify_manifest_snapshot.__code__
    extra_code = bounded_io.bounded_file_sha256.__code__
    def input_phase(**kwargs):
        phase.append("input")
        try:
            return inputs(**kwargs)
        finally:
            phase.pop()
    def output_phase(**kwargs):
        phase.append("output")
        try:
            return assemble(**kwargs)
        finally:
            phase.pop()
    def observe(frame, event, arg):
        if event != "call":
            return
        part = phase[-1] if phase else 'outer'
        if frame.f_code is guard_code:
            counts[part + ".snapshot_calls"] += 1
            counts[part + ".snapshot_rows"] += len(frame.f_locals["snapshots"])
        if frame.f_code is physical_code:
            counts[part + ".owner_hashes"] += 1
            counts[part + ".owner_hash_bytes"] += frame.f_locals["manifest"].materialization.size_bytes
        if frame.f_code is extra_code:
            caller = frame.f_back.f_code
            kind = "snapshot" if caller is guard_code else "snapshot_seal" if caller is seal_code else "extra"
            counts[part + "." + kind + "_hashes"] += 1
            counts[part + "." + kind + "_hash_bytes"] += frame.f_locals["maximum_bytes"]
    with monkeypatch.context() as patch:
        patch.setattr(execution, "_external_inputs", input_phase)
        patch.setattr(owner, "_assemble_read_products", output_phase)
        if serial:
            patch.setattr(execution, "_can_batch_readonly_inputs", lambda **kwargs: False)
            patch.setattr(owner, "_can_batch_compact_output_custody", lambda **kwargs: False)
        with _profile(observe):
            result = _read(case, full=full)
    return result, counts


def test_default_public_two_sizes_preserve_all_results_and_reduce_snapshot_and_hash_work(
        scale_cases, monkeypatch, tmp_path):
    observations = []
    for case in scale_cases:
        serial_result, serial = _measure(case, monkeypatch, serial=True)
        result, stock = _measure(case, monkeypatch)
        assert result == serial_result == case.compact
        input_values = result[1]["external_inputs"]
        input_count = len(input_values)
        output_count = len(result[1]["outputs"])
        assert len(result[0]["task_census"]) == case.tasks
        assert result[0]["new_native_contact_count"] == 0
        assert stock["input.owner_hashes"] == serial["input.owner_hashes"] == input_count
        assert stock["input.extra_hashes"] == 0 and serial["input.extra_hashes"] == input_count
        assert stock["input.owner_hash_bytes"] == sum(value.materialization.size_bytes for value in input_values)
        assert stock["output.owner_hashes"] == serial["output.owner_hashes"] == output_count
        assert stock["output.extra_hashes"] == 0 and serial["output.extra_hashes"] == output_count
        assert stock["output.owner_hash_bytes"] == sum(value.materialization.size_bytes
            for value in result[1]["outputs"].values())
        assert stock["input.snapshot_calls"] <= serial["input.snapshot_calls"]
        assert stock["output.snapshot_calls"] <= serial["output.snapshot_calls"]
        assert stock["input.snapshot_rows"] <= serial["input.snapshot_rows"]
        assert stock["output.snapshot_rows"] <= serial["output.snapshot_rows"]
        # The shared public read now owns the complete final byte guard after
        # both phase callbacks return. Count that real boundary as well.
        for measured in (stock, serial):
            assert measured['outer.snapshot_hashes']
            assert measured['outer.snapshot_hash_bytes'] >= sum(value.materialization.size_bytes
                for value in (*input_values, *result[1]['outputs'].values()))
        assert stock["input.snapshot_hash_bytes"] <= serial["input.snapshot_hash_bytes"]
        assert stock["output.snapshot_hash_bytes"] <= serial["output.snapshot_hash_bytes"]
        observations.append({"tasks": case.tasks, "inputs": input_count, "outputs": output_count,
            "stock": dict(stock), "serial": dict(serial)})
    assert observations[0]["tasks"] == 4 and observations[1]["tasks"] == 6
    assert observations[0]["inputs"] < observations[1]["inputs"]
    assert observations[0]["stock"].get("input.snapshot_calls", 0) == observations[1]["stock"].get("input.snapshot_calls", 0)
    assert observations[0]["stock"].get("output.snapshot_calls", 0) == observations[1]["stock"].get("output.snapshot_calls", 0)
    (tmp_path / "actual-two-size-counts.json").write_text(json.dumps(observations, indent=2, sort_keys=True) + "\n")


def test_default_full_read_batches_inputs_and_outputs_and_keeps_typed_consumer(scale_cases, monkeypatch):
    for case in scale_cases:
        result, stock = _measure(case, monkeypatch, full=True)
        assert result == case.full
        assert stock["input.owner_hashes"] == len(result[1]["external_inputs"])
        assert stock["input.extra_hashes"] == 0
        assert stock["output.owner_hashes"] == len(result[1]["outputs"])
        assert stock["output.extra_hashes"] == 0
        assert stock['outer.snapshot_hashes']
        assert result[1]["records"] == case.full[1]["records"]


def _input_case(case, *, plane=None, lazy=True):
    plane = case.plane if plane is None else plane
    _, draft, _, payloads = author.load_authored_wave(directory=case.directory,
        artifact_writer=plane, lazy_payloads=lazy)
    _, plan, _ = execution._retained_plans(payloads, draft)
    relative = f"runs/{plan.source_plan.object_id}/inputs/input-0000.json"
    manifest = plane.read_manifest(relative)
    return draft, plan, payloads, manifest


@pytest.mark.parametrize("hook", ("instance-verify", "class-verify", "class-read", "class-resolve", "class-inspector", "class-verify-raise", "class-consume", "low-limit", "nonlazy", "write"))
def test_custom_and_nonreadonly_input_routes_keep_serial_owner_and_extra_hashes(scale_cases, monkeypatch, hook):
    case = scale_cases[0]
    with case.plane.verification_scope() as plane:
        draft, plan, payloads, _ = _input_case(case, plane=plane, lazy=hook != "nonlazy")
        seen = Counter()
        original_verify = artifacts._ScopedArtifactPlane.verify_manifest
        original_read = artifacts._ScopedArtifactPlane.read_manifest
        original_resolve = artifacts.GuardedExternalRoot.resolve
        original_inspect = artifacts.LocalFilesystemInspector.inspect_bound
        original_consume = artifacts._ScopedArtifactPlane._consume_verified_manifests_members
        refusal = PermissionError("actual custom inherited verify hook refusal")
        def verify(self, *args, **kwargs):
            seen["hook"] += 1
            return original_verify(self, *args, **kwargs)
        def verify_raises(self, *args, **kwargs):
            seen["hook"] += 1
            raise refusal
        def consume(self, *args, **kwargs):
            seen["hook"] += 1
            return original_consume(self, *args, **kwargs)
        def read(self, *args, **kwargs):
            seen["hook"] += 1
            return original_read(self, *args, **kwargs)
        def resolve(self, *args, **kwargs):
            seen["hook"] += 1
            return original_resolve(self, *args, **kwargs)
        def inspect(self, *args, **kwargs):
            seen["hook"] += 1
            return original_inspect(self, *args, **kwargs)
        with monkeypatch.context() as patch:
            if hook == "instance-verify":
                patch.setattr(plane, "verify_manifest", lambda *args, **kwargs: verify(plane, *args, **kwargs))
            if hook == "class-verify":
                patch.setattr(artifacts._ScopedArtifactPlane, "verify_manifest", verify)
            if hook == "class-verify-raise":
                patch.setattr(artifacts._ScopedArtifactPlane, "verify_manifest", verify_raises)
            if hook == "class-consume":
                patch.setattr(artifacts._ScopedArtifactPlane, "_consume_verified_manifests_members", consume)
            if hook == "class-read":
                patch.setattr(artifacts._ScopedArtifactPlane, "read_manifest", read)
            if hook == "class-resolve":
                patch.setattr(artifacts.GuardedExternalRoot, "resolve", resolve)
            if hook == "class-inspector":
                patch.setattr(artifacts.LocalFilesystemInspector, "inspect_bound", inspect)
            if hook == "low-limit":
                patch.setattr(plane, "custody_limits", replace(plane.custody_limits, publication_members=1))
            def observe(frame, event, arg):
                if event == "call" and frame.f_code is bounded_io.bounded_file_sha256.__code__:
                    if frame.f_back.f_code in (
                            artifacts.ExternalArtifactPlane._require_verification_snapshot_paths.__code__,
                            artifacts.ExternalArtifactPlane._track_verification_snapshot.__code__):
                        seen["snapshot"] += 1
                    else:
                        seen["extra"] += 1
            if hook == "class-verify-raise":
                with pytest.raises(PermissionError) as caught:
                    execution._external_inputs(plane=plane, plan=plan, draft=draft,
                        payloads=payloads, read_only=True)
                assert caught.value is refusal and seen["hook"]
                return
            if hook == 'low-limit':
                # Run inputs now retain atomic groups. A smaller later read
                # allowance cannot split their original closed membership.
                with pytest.raises(artifacts.ArtifactIdentityConflict, match='selected member bound'):
                    execution._external_inputs(plane=plane, plan=plan, draft=draft,
                        payloads=payloads, read_only=True)
                return
            with _profile(observe):
                actual = execution._external_inputs(plane=plane, plan=plan, draft=draft,
                    payloads=payloads, read_only=hook != "write")
            assert actual == case.compact[1]["external_inputs"]
            # Eager inputs use their original exact raw reader instead.
            if hook != "nonlazy":
                assert seen["extra"] == len(actual)
            if hook in ("instance-verify", "class-verify", "class-resolve"):
                assert seen["hook"]


def _forged_input_manifest(manifest, damage):
    logical, material = manifest.logical, manifest.materialization
    if damage == "identity":
        logical = replace(logical, logical_artifact_id=logical.logical_artifact_id + ".other")
        material = replace(material, logical_artifact_id=logical.logical_artifact_id)
    elif damage == "schema":
        schema = "empirical-lawhood/testing/wrong-input"
        logical = replace(logical, payload_schema=schema,
            generic_validation=replace(logical.generic_validation, payload_schema=schema), semantic_validation=None)
    elif damage == "media":
        logical = replace(logical, media_type="application/octet-stream")
    elif damage == "profile":
        logical = replace(logical, profile=ArtifactProfile.RAW_SOURCE_BYTES,
            generic_validation=replace(logical.generic_validation, profile=ArtifactProfile.RAW_SOURCE_BYTES), semantic_validation=None)
    elif damage == "access":
        logical = replace(logical, visibility_ceiling=VisibilityCeiling.PRIVILEGED_TRUTH,
            outcome_access=OutcomeAccess.PRIVILEGED_TRUTH)
    elif damage == "lineage":
        logical = replace(logical, lineage_parents=(), parent_visibility_ceilings=())
    elif damage == "parent":
        logical = replace(logical, lineage_parents=(replace(logical.lineage_parents[0],
            identity=replace(logical.lineage_parents[0].identity, object_fingerprint="f" * 64)),))
    elif damage == "size":
        material = replace(material, size_bytes=material.size_bytes + 1)
    else:
        logical = replace(logical, content_sha256="f" * 64)
    forged = ArtifactManifest(logical, material)
    # This is an internally valid disclosed decoder seam. The negative must
    # reach the real frozen scientific guard, not fail during fixture creation.
    assert forged.logical.logical_artifact_id == forged.materialization.logical_artifact_id
    return forged


@pytest.mark.parametrize("damage", ("identity", "schema", "media", "profile", "access", "lineage", "parent", "size", "logical-sha"))
def test_exact_input_scientific_metadata_refuses_before_any_product_consumer(scale_cases, monkeypatch, damage):
    case = scale_cases[0]
    _, _, _, manifest = _input_case(case)
    forged = _forged_input_manifest(manifest, damage)
    actual_read = artifacts._ScopedArtifactPlane.read_manifest
    def read(self, relative, **kwargs):
        value = actual_read(self, relative, **kwargs)
        return forged if relative == manifest.materialization.relative_path else value
    def forbidden(**kwargs):
        pytest.fail("invalid scientific input metadata reached product/native/scientific consumers")
    monkeypatch.setattr(artifacts._ScopedArtifactPlane, "read_manifest", read)
    monkeypatch.setattr(owner, "read_recursive_products", forbidden)
    with pytest.raises(ValueError, match="frozen scientific identity"):
        _read(case)


def _paths(case):
    _, _, _, manifest = _input_case(case)
    body = case.plane.root.resolve(manifest.materialization.relative_path, for_write=False)
    sidecar = case.plane.root.resolve(manifest.materialization.relative_path + ".manifest.json", for_write=False)
    marker = case.plane.root.resolve(manifest.publication.commit_marker_relative_path, for_write=False)
    receipt = next(iter(case.compact[1]["receipts"].values()))
    receipt_path = case.plane.root.resolve(task_receipts.ExternalTaskReceiptStore._relative_path(
        receipt.run_id, receipt.task_id, receipt.attempt_id), for_write=False)
    output = next(iter(case.compact[1]["outputs"].values()))
    return {"body": body, "sidecar": sidecar, "marker": marker, "receipt": receipt_path,
        "output": case.plane.root.resolve(output.materialization.relative_path, for_write=False)}


@pytest.mark.parametrize("damage", ("body", "sidecar", "marker", "missing-body", "missing-sidecar", "physical-sha"))
def test_actual_input_bytes_or_custody_corruption_refuses_before_products(scale_cases, monkeypatch, damage):
    case = scale_cases[0]
    paths = _paths(case)
    target = paths[damage.removeprefix("missing-")] if damage != "physical-sha" else paths["sidecar"]
    raw = target.read_bytes()
    try:
        if damage.startswith("missing-"):
            target.unlink()
        elif damage == "physical-sha":
            document = json.loads(raw)
            document["value"]["materialization"]["value"]["physical_sha256"] = "f" * 64
            target.write_text(json.dumps(document, separators=(",", ":"), sort_keys=True))
        else:
            target.write_bytes(b"x" + raw[1:])
        def forbidden(**kwargs):
            pytest.fail("corrupt input escaped to later products")
        monkeypatch.setattr(owner, "read_recursive_products", forbidden)
        with pytest.raises((ValueError, RuntimeError, OSError)):
            _read(case)
    finally:
        target.write_bytes(raw)


@pytest.mark.parametrize("phase,damage", (("input", "body"), ("input", "sidecar"), ("input", "marker"),
    ("input", "ancestor"), ("input", "body-then-error"), ("input", "error-only"),
    ("output", "receipt"), ("output", "output"), ("output", "output-then-error")))
def test_stock_final_guard_rejects_mid_callback_mutation_and_preserves_exception_without_escape(
        scale_cases, phase, damage):
    case = scale_cases[0]
    paths = _paths(case)
    key = "body" if damage == "body-then-error" else "output" if damage == "output-then-error" else damage
    target = paths["body"] if damage in ("ancestor", "error-only") else paths[key]
    original = target.read_bytes()
    moved = target.parent.with_name(target.parent.name + ".moved-for-control")
    seen, escaped = [], []
    refusal = PermissionError("controlled readonly callback failure")
    prefix = "_external_inputs.<locals>.consume" if phase == "input" else "_assemble_read_products.<locals>.consume"
    def observe(frame, event, arg):
        if event != "call" or frame.f_code.co_qualname != prefix or seen:
            return
        seen.append(True)
        if damage == "ancestor":
            target.parent.rename(moved)
            target.parent.symlink_to(moved, target_is_directory=True)
        elif damage != "error-only":
            target.write_bytes(b"x" + original[1:])
        if damage.endswith("error") or damage == "error-only":
            raise refusal
    try:
        expected = PermissionError if damage == "error-only" else (artifacts.ArtifactIdentityConflict, artifacts.ExternalRootUnavailable)
        with pytest.raises(expected) as caught:
            with _profile(observe):
                escaped.append(_read(case))
        if damage == "error-only":
            assert caught.value is refusal
        assert seen and not escaped
    finally:
        if damage == "ancestor" and target.parent.is_symlink():
            target.parent.unlink()
            moved.rename(target.parent)
        else:
            target.write_bytes(original)


@pytest.mark.parametrize("full", (False, True))
def test_custom_receipt_validator_keeps_per_row_guard_and_refuses_changed_prior_receipt(scale_cases, monkeypatch, full):
    case = scale_cases[0]
    path = _paths(case)["receipt"]
    raw = path.read_bytes()
    assemble = owner._assemble_read_products
    validate = recovery_owner.ExternalRunRecoveryStore._validate_receipt_static
    inside, changed, escaped = [], [], []
    def read_products(**kwargs):
        inside.append(True)
        try:
            return assemble(**kwargs)
        finally:
            inside.pop()
    def custom_validator(*args, **kwargs):
        value = validate(*args, **kwargs)
        if inside and not changed:
            changed.append(True)
            path.write_bytes(b"x" + raw[1:])
        return value
    monkeypatch.setattr(owner, "_assemble_read_products", read_products)
    monkeypatch.setattr(recovery_owner.ExternalRunRecoveryStore, "_validate_receipt_static", staticmethod(custom_validator))
    try:
        with pytest.raises((ValueError, RuntimeError, OSError)):
            escaped.append(_read(case, full=full))
        assert changed and not escaped
    finally:
        path.write_bytes(raw)


@pytest.mark.parametrize("selected_class", (artifacts.ExternalArtifactPlane, artifacts._ScopedArtifactPlane))
def test_custom_descriptor_identity_keeps_independent_serial_hash_and_detects_changed_bytes(
        scale_cases, monkeypatch, selected_class):
    case = scale_cases[0]
    path = _paths(case)["body"]
    raw = path.read_bytes()
    _, _, _, manifest = _input_case(case)
    relative = manifest.materialization.relative_path
    changed, escaped = [], []
    code = artifacts.ExternalArtifactPlane._verify_manifest_snapshot.__code__
    def observe(frame, event, arg):
        if (event == "return" and frame.f_code is code and not changed
                and frame.f_locals["manifest"].materialization.relative_path == relative):
            changed.append(True)
            path.write_bytes(b"x" + raw[1:])
    with monkeypatch.context() as patch:
        # Keep the byte bound truthful while disabling identity/timestamp
        # change detection. Either exact byte guard must still refuse mutation.
        patch.setattr(selected_class, "_descriptor_identity",
            staticmethod(lambda value: (0, 0, value.st_size, 0, 0)))
        try:
            with pytest.raises((ValueError, artifacts.ArtifactIdentityConflict),
                    match="recursive retained input differs from its authored bytes|artifact changed during its verification scope"):
                with _profile(observe):
                    escaped.append(_read(case))
            assert changed and not escaped
        finally:
            path.write_bytes(raw)
