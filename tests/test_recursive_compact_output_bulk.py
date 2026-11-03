# SPDX-License-Identifier: MPL-2.0
"""Actual PURE compact reads batch bodies without executing a consumer or native work."""
from contextlib import nullcontext
from dataclasses import replace
import os
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.infrastructure import recursive_custody as owner
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from tests.test_recursive_report_projection import ROOT, wave as wave  # noqa: F401


@pytest.fixture(scope="module")
def compact_wave(wave):
    # This is the existing registered six-task Rubisco PURE software workflow,
    # not a constructed scientific issue, native acquisition or qualification.
    from empirical_lawhood.adapters.methods.rubisco_historical.recursive_translation import historical_recursive_draft
    from tests.test_rubisco_historical_recursive import _inputs

    model, slices = _inputs()
    root = wave.directory.parent
    # Unlike a synthetic storage inspector, the positive bulk control uses
    # the actual mounted filesystem through the unchanged stock read owner.
    mount = next(path for path in (root, *root.parents) if os.path.ismount(path))
    contract = replace(wave.plane.root.contract, required_mount_path=str(mount))
    plane = artifacts.ExternalArtifactPlane(artifacts.GuardedExternalRoot(contract),
        validators=wave.plane.validators, semantic_validations=wave.plane.semantic_validations)
    with plane.verification_scope() as stock:
        assert type(stock.root) is artifacts.GuardedExternalRoot
        assert type(stock.root.inspector) is artifacts.LocalFilesystemInspector
        assert execution._read_only_custody_policy(stock) == (
            stock.root, stock.root.inspector, stock.root.contract, stock.validators, stock.semantic_validations, stock.custody_limits)
    bindings = []
    for record in slices:
        path = root / ("bulk-" + record.slice_id + ".json")
        path.write_bytes(record.canonical_bytes())
        bindings.append(("external." + record.slice_id, path))
    directory = root / "compact-bulk-history"
    author.author_recursive_wave(draft=historical_recursive_draft(model, slices), project_root=ROOT,
        artifact_writer=plane, output_dir=directory, input_bindings=tuple(bindings))
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(LocalProcessExecutor, "execute", wave.executor_execute)
        result = execution.run_recursive_wave(directory=directory, project_root=ROOT,
            artifact_writer=plane, terminal_product_format="references")
    assert result["status"] == "SUCCEEDED" and result["new_native_contact_count"] == 0
    compact = execution.read_recursive_wave(directory=directory, artifact_writer=plane,
        include_products=True, terminal_product_format="compact")
    full = execution.read_recursive_wave(directory=directory, artifact_writer=plane, include_products=True)
    assert len(compact[1]["product_index"]) > 2
    first = next(iter(compact[1]["outputs"].values()))
    publication = plane.read_manifest(first.materialization.relative_path).publication
    assert publication is not None
    return SimpleNamespace(directory=directory, plane=plane, compact=compact, full=full,
        first=first, publication=publication)


def _read(selected, plane, *, full=False):
    return execution.read_recursive_wave(directory=selected.directory, artifact_writer=plane,
        include_products=True, terminal_product_format="documents" if full else "compact")


@pytest.mark.parametrize("mode", ("scoped", "public-default", "unscoped", "full", "custom-policy", "foreign-store", "low-request-limit", "custom-root", "custom-inspector", "custom-limits"))
def test_actual_pure_bulk_compact_parity_and_strict_serial_fallback(compact_wave, monkeypatch, mode):
    selected = compact_wave
    original = owner._assemble_read_products
    member_calls = []
    members = artifacts._ScopedArtifactPlane.verify_manifests_members
    inside = []

    def observe_members(self, *args, **kwargs):
        if inside:
            member_calls.append(True)
        return members(self, *args, **kwargs)

    class ForeignStore(ExternalTaskReceiptStore):
        pass

    def assemble(**kwargs):
        plane = kwargs["plane"]
        previous = plane.custody_limits
        if mode == "foreign-store":
            kwargs["store"] = ForeignStore(plane)
        if mode == "low-request-limit":
            count = len(selected.compact[1]["product_index"])
            assert len(selected.publication.members) < count
            plane.custody_limits = replace(previous, publication_members=count - 1)
        inside.append(True)
        try:
            return original(**kwargs)
        finally:
            inside.pop()
            plane.custody_limits = previous

    monkeypatch.setattr(artifacts._ScopedArtifactPlane, "verify_manifests_members", observe_members)
    monkeypatch.setattr(owner, "_assemble_read_products", assemble)
    with (nullcontext(selected.plane) if mode in ("public-default", "unscoped") else selected.plane.verification_scope()) as plane:
        if mode == "custom-policy":
            plane.verify_manifest = plane.verify_manifest
        if mode == "custom-root":
            class ObservedRoot(artifacts.GuardedExternalRoot):
                def resolve(self, *args, **kwargs):
                    root_calls.append(True)
                    return super().resolve(*args, **kwargs)
            root_calls = []
            plane.root = ObservedRoot(plane.root.contract, plane.root.inspector)
            assert execution._read_only_custody_policy(plane) is None
        if mode == "custom-inspector":
            root_calls = []
            class ObservedInspector(artifacts.LocalFilesystemInspector):
                def inspect_bound(self, contract):
                    root_calls.append(True)
                    return super().inspect_bound(contract)
            plane.root = artifacts.GuardedExternalRoot(plane.root.contract, ObservedInspector())
            assert execution._read_only_custody_policy(plane) is None
        if mode == "custom-limits":
            from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits
            class ObservedLimits(ArtifactCustodyLimits):
                def exceeds(self, *args, **kwargs):
                    limit_calls.append(True)
                    return super().exceeds(*args, **kwargs)
            limit_calls = []
            plane.custody_limits = ObservedLimits(**{
                name: getattr(plane.custody_limits, name) for name in plane.custody_limits.__dataclass_fields__})
            assert execution._read_only_custody_policy(plane) is None
        if mode == "unscoped":
            # The lower owner remains serial if its caller intentionally omits
            # a scope. The public-default case separately proves API selection.
            actual, _, _ = execution._read_recursive_wave_with_roots(directory=selected.directory,
                artifact_writer=plane, include_products=True, terminal_product_format="compact")
        else:
            actual = _read(selected, plane, full=mode == "full")
        if mode in ("custom-root", "custom-inspector"):
            assert root_calls
        if mode == "custom-limits":
            assert limit_calls
    assert actual == (selected.full if mode == "full" else selected.compact)
    assert len(member_calls) == (1 if mode in ("scoped", "public-default") else 0)
    assert actual[0]["new_native_contact_count"] == 0
    if mode != "full":
        assert actual[0]["typed_product_validation"] == "DEFERRED"
        assert actual[0]["scientific_completion"] == "NOT_ASSESSED_BY_COMPACT_CUSTODY"


def test_actual_small_output_stock_compact_read_keeps_serial_route(wave, compact_wave, monkeypatch):
    options = dict(directory=wave.directory, include_products=True, terminal_product_format="compact")
    expected = execution.read_recursive_wave(artifact_writer=compact_wave.plane, **options)
    assert 0 < len(expected[1]["product_index"]) <= 2
    original = owner._assemble_read_products
    members = artifacts._ScopedArtifactPlane.verify_manifests_members
    inside, member_calls = [], []

    def assemble(**kwargs):
        inside.append(True)
        try:
            return original(**kwargs)
        finally:
            inside.pop()

    def observe_members(self, *args, **kwargs):
        if inside:
            member_calls.append(True)
        return members(self, *args, **kwargs)

    monkeypatch.setattr(owner, "_assemble_read_products", assemble)
    monkeypatch.setattr(artifacts._ScopedArtifactPlane, "verify_manifests_members", observe_members)
    with compact_wave.plane.verification_scope() as plane:
        assert execution._read_only_custody_policy(plane) is not None
        assert execution.read_recursive_wave(artifact_writer=plane, **options) == expected
    assert member_calls == []


def test_stock_full_read_batches_complete_output_custody_before_typed_consumption(compact_wave, monkeypatch):
    import sys

    assemble = owner._assemble_read_products
    def serial(**options):
        options['_read_policy'] = None
        return assemble(**options)
    with monkeypatch.context() as patch:
        patch.setattr(owner, '_assemble_read_products', serial)
        expected = _read(compact_wave, compact_wave.plane, full=True)
    selected_paths = {row['relative_path'] for row in expected[1]['product_index']}
    batches, typed = [], []
    verify = artifacts.ExternalArtifactPlane._verify_manifests.__code__
    decode = owner.decode_canonical_bytes.__code__
    kinds = {type(record) for rows in expected[1]['records'].values() for record in rows.values()}
    previous = sys.getprofile()
    def observe(frame, event, _argument):
        if event == 'call' and frame.f_code is verify:
            paths = {row.materialization.relative_path for row in frame.f_locals['manifests']}
            if paths == selected_paths:
                assert typed == []
                batches.append(paths)
        elif event == 'call' and frame.f_code is decode and frame.f_locals['record_type'] in kinds:
            assert len(batches) == 1
            typed.append(frame.f_locals['record_type'])
    sys.setprofile(observe)
    try:
        actual = _read(compact_wave, compact_wave.plane, full=True)
    finally:
        sys.setprofile(previous)
    assert actual == expected and len(batches) == 1 and typed


def test_full_output_batch_retains_final_mutation_refusal(compact_wave, monkeypatch):
    expected = compact_wave.full
    products = expected[1]
    kinds = {type(record) for rows in products['records'].values() for record in rows.values()}
    count = sum(len(rows) for rows in products['records'].values())
    selected = next(iter(products['outputs'].values()))
    path = compact_wave.plane.root.resolve(selected.materialization.relative_path, for_write=False)
    before = path.read_bytes()
    original, consumed = owner.decode_canonical_bytes, []
    def decode(raw, kind, **options):
        value = original(raw, kind, **options)
        if kind in kinds:
            consumed.append(value)
            if len(consumed) == count:
                path.write_bytes(b'X' + before[1:])
        return value
    monkeypatch.setattr(owner, 'decode_canonical_bytes', decode)
    try:
        with pytest.raises(artifacts.ArtifactIdentityConflict):
            _read(compact_wave, compact_wave.plane, full=True)
    finally:
        path.write_bytes(before)
    assert len(consumed) == count


def test_actual_bulk_reduces_whole_snapshot_traversals_but_keeps_each_independent_body_hash(compact_wave, monkeypatch):
    original = owner._assemble_read_products
    guard = artifacts.ExternalArtifactPlane._require_verification_snapshot_paths
    body = owner._verified_product_path
    eligible = owner._can_batch_compact_output_custody
    inside, observations = [], []

    def assemble(**kwargs):
        inside.append(True)
        try:
            return original(**kwargs)
        finally:
            inside.pop()

    def observe_guard(self, snapshots, *, reason):
        if inside:
            observations.append("snapshot")
        return guard(self, snapshots, reason=reason)

    def observe_body(**kwargs):
        if inside:
            observations.append("body")
        return body(**kwargs)

    monkeypatch.setattr(owner, "_assemble_read_products", assemble)
    # This custom guard keeps the old explicit-hash route. Default-stock
    # work is counted separately without replacing any selected read method.
    monkeypatch.setattr(artifacts.ExternalArtifactPlane, "_require_verification_snapshot_paths", observe_guard)
    monkeypatch.setattr(owner, "_verified_product_path", observe_body)
    counts = {}
    for mode in ("serial", "bulk"):
        # The comparison chooses the existing strict serial route; source,
        # receipt/publication/native guards are unchanged in both actual reads.
        monkeypatch.setattr(owner, "_can_batch_compact_output_custody",
            (lambda **kwargs: False) if mode == "serial" else eligible)
        observations.clear()
        with compact_wave.plane.verification_scope() as plane:
            assert _read(compact_wave, plane) == compact_wave.compact
        counts[mode] = (observations.count("snapshot"), observations.count("body"))
    output_count = len(compact_wave.compact[1]["product_index"])
    assert counts["serial"][1] == counts["bulk"][1] == output_count
    assert counts["serial"][0] - counts["bulk"][0] == 2 * output_count - 4
    assert counts["bulk"][0] < counts["serial"][0]


@pytest.mark.parametrize("damage", ("body", "sidecar", "receipt", "marker", "ancestor", "body-then-error"))
def test_bulk_final_guard_refuses_mutation_before_any_rows_or_later_consumer_escape(compact_wave, monkeypatch, damage):
    selected = compact_wave
    body = owner._verified_product_path
    first = selected.first
    receipt = next(iter(selected.compact[1]["receipts"].values()))
    relative = first.materialization.relative_path
    if damage == "sidecar":
        relative += ".manifest.json"
    elif damage == "receipt":
        relative = ExternalTaskReceiptStore._relative_path(receipt.run_id, receipt.task_id, receipt.attempt_id)
    elif damage == "marker":
        relative = selected.publication.commit_marker_relative_path
    path = selected.plane.root.resolve(relative, for_write=False)
    changed, later_consumer = [], []

    def mutate(**kwargs):
        result = body(**kwargs)
        if not changed:
            if damage == "ancestor":
                directory = path.parent
                held = directory.with_name(directory.name + "-bulk-held")
                assert not held.exists()
                directory.rename(held)
                directory.symlink_to(held.name, target_is_directory=True)
                changed.append((directory, held))
            else:
                raw = path.read_bytes()
                assert raw
                path.write_bytes(raw[:-1] + bytes((raw[-1] ^ 1,)))  # Same size.
                changed.append((path, raw))
            if damage == "body-then-error":
                raise PermissionError("literal read refusal after actual mutation")
        return result

    monkeypatch.setattr(owner, "_verified_product_path", mutate)
    refusal = artifacts.ExternalRootUnavailable if damage == "ancestor" else artifacts.ArtifactIdentityConflict
    try:
        with pytest.raises(refusal):
            # Real public entry creates the stock scope; none is injected here.
            result = _read(selected, selected.plane)
            later_consumer.append(result)
    finally:
        for target, previous in changed:
            if damage == "ancestor":
                target.unlink()
                previous.rename(target)
            else:
                target.write_bytes(previous)
    assert changed and later_consumer == []


def test_bulk_read_error_preserves_exception_and_never_returns_rows(compact_wave, monkeypatch):
    refusal = PermissionError("literal output reader refusal")
    later_consumer = []

    def refused(**kwargs):
        raise refusal

    monkeypatch.setattr(owner, "_verified_product_path", refused)
    with pytest.raises(PermissionError) as caught:
        later_consumer.append(_read(compact_wave, compact_wave.plane))
    assert caught.value is refusal and later_consumer == []


def test_bulk_metadata_codec_refusal_precedes_all_explicit_body_hashes(compact_wave, monkeypatch):
    original = owner._assemble_read_products
    ordered = tuple(compact_wave.compact[1]["outputs"].values())
    schema = next(value.logical.payload_schema for value in ordered
        if value.logical.payload_schema != ordered[0].logical.payload_schema)
    bodies = []

    def assemble(**kwargs):
        codecs = dict(kwargs["output_codecs"])
        del codecs[schema]
        kwargs["output_codecs"] = codecs
        return original(**kwargs)

    def forbidden(**kwargs):
        bodies.append(True)
        pytest.fail("metadata fault reached explicit output-body consumption")

    monkeypatch.setattr(owner, "_assemble_read_products", assemble)
    monkeypatch.setattr(owner, "_verified_product_path", forbidden)
    with pytest.raises(ValueError, match="registered strict record codec"):
        with compact_wave.plane.verification_scope() as plane:
            _read(compact_wave, plane)
    assert bodies == []


@pytest.mark.parametrize("damage", ("missing-input", "input-lineage"))
def test_bulk_metadata_preflight_keeps_exact_external_input_and_lineage_guards(compact_wave, monkeypatch, damage):
    original = owner._assemble_read_products
    bodies = []

    def assemble(**kwargs):
        plan = kwargs["plan"]
        task = next(task for task in plan.tasks if task.task_id == plan.topological_task_ids()[0])
        assert task.external_inputs
        key = task.external_inputs[0].logical_artifact_id
        external = dict(kwargs["external_by_id"])
        value = external[key]
        if damage == "missing-input":
            del external[key]
        else:
            assert value.logical.content_sha256 != "0" * 64
            external[key] = replace(value, logical=replace(value.logical, content_sha256="0" * 64))
        kwargs["external_by_id"] = external
        return original(**kwargs)

    def forbidden(**kwargs):
        bodies.append(True)
        pytest.fail("changed input metadata reached explicit output-body consumption")

    monkeypatch.setattr(owner, "_assemble_read_products", assemble)
    monkeypatch.setattr(owner, "_verified_product_path", forbidden)
    message = ("authenticated external input" if damage == "missing-input"
        else "exact scientific input lineage")
    with pytest.raises(ValueError, match=message):
        with compact_wave.plane.verification_scope() as plane:
            _read(compact_wave, plane)
    assert bodies == []


def test_same_registry_class_custom_binary_validator_keeps_serial_admission_and_mutation_guard(compact_wave, monkeypatch):
    from empirical_lawhood.api.integration_artifact_profiles import INTEGRATION_ARTIFACT_PROFILE_VALIDATORS
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
    from empirical_lawhood.runtime.recursive_storage_codecs import RecursiveStorageCodec

    selected = compact_wave
    target = selected.plane.root.resolve(selected.first.materialization.relative_path, for_write=False)
    original_bytes = target.read_bytes()
    armed, calls = [], []

    def validate_stream(source, request, *, size):
        while source.read(65536):
            pass
        if armed:
            calls.append(size)
            target.write_bytes(original_bytes[:-1] + bytes((original_bytes[-1] ^ 1,)))

    codec = RecursiveStorageCodec("test.compact.custom-binary", "empirical-lawhood/test/compact-custom-binary",
        "1.0.0", ArtifactProfile.RAW_SOURCE_BYTES, "application/octet-stream", ".bin", validate_stream)
    codecs = tuple(sorted((*INTEGRATION_ARTIFACT_PROFILE_VALIDATORS.binary_codecs, codec), key=lambda value: value.codec_id))
    validators = ArtifactProfileValidatorRegistry(binary_codecs=codecs)
    assert type(validators) is type(INTEGRATION_ARTIFACT_PROFILE_VALIDATORS)
    assert validators is not INTEGRATION_ARTIFACT_PROFILE_VALIDATORS
    custom = artifacts.ExternalArtifactPlane(selected.plane.root, validators,
        selected.plane.semantic_validations, custody_limits=selected.plane.custody_limits)
    result = custom.write(ArtifactWriteRequest("test.compact.custom-operand", "bulk-custom/operand.bin",
        codec.payload_schema, codec.profile, codec.media_type, "test.compact.custom-publication", "bulk-custom",
        b"actual opaque software-control publication", VisibilityCeiling.DEVELOPMENT_ONLY, (),
        OutcomeAccess.DEVELOPMENT_VISIBLE))
    binary = custom.read_manifest(result.materialization.relative_path)
    first = custom.read_manifest(selected.first.materialization.relative_path)
    assemble = owner._assemble_read_products
    entered = []

    def serial(**kwargs):
        entered.append(kwargs.get("_read_policy"))
        assert kwargs.get("_read_policy") is None
        return assemble(**kwargs)

    monkeypatch.setattr(owner, "_assemble_read_products", serial)
    with custom.verification_scope() as plane:
        assert execution._read_only_custody_policy(plane) is None
        assert _read(selected, plane) == selected.compact
    assert entered == [None] and calls == []
    later_consumer = []
    try:
        with pytest.raises(artifacts.ArtifactIdentityConflict):
            with custom.verification_scope() as plane:
                plane.verify_manifest(first)
                armed.append(True)
                # This actual registered FunctionType validator can mutate an
                # earlier publication. It is not certified pure by its class.
                plane.verify_manifest(binary)
                later_consumer.append(True)
    finally:
        target.write_bytes(original_bytes)
    assert calls and later_consumer == []
