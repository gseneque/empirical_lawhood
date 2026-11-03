# SPDX-License-Identifier: MPL-2.0
"""Cheap original publication/receipt controls; no native work or qualification."""

from dataclasses import replace
from types import SimpleNamespace
import os

import pytest

from empirical_lawhood.api.native_training_banks import _receipt_product
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.infrastructure.artifacts import ArtifactPlaneError, ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt, ExternalRootContract


@pytest.fixture
def receipted_product(tmp_path):
    """Actual committed bytes; disclosed task/plan metadata tests only the join."""
    path = (tmp_path / "custody").resolve()
    path.mkdir()
    mount = next(value for value in (path, *path.parents) if os.path.ismount(value))
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "test.native-training-custody", "Exposed receipt/source conformance", str(path), str(mount),
        "empirical-lawhood/testing/native-training-custody", 1)))
    value = ObjectIdentity("source.test.native-training", "empirical-lawhood/testing/original", "1.0.0", "a" * 64)
    publication = plane.write(ArtifactWriteRequest("product.native-training", "outputs/product.json", value.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "test.native-training", "outputs", value.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    manifest = decode_artifact_manifest(plane.root.resolve(publication.manifest_materialization.relative_path,
        for_write=False).read_bytes())
    task_id, run_id = "task.native-training", "run.native-training"
    task = SimpleNamespace(task_id=task_id, outputs=(SimpleNamespace(output_id=task_id + ".product",
        logical_artifact_id=manifest.logical.logical_artifact_id, payload_schema=value.SCHEMA),))
    plan = SimpleNamespace(source_plan=ObjectIdentity(run_id, "empirical-lawhood/testing/plan", "1.0.0", "b" * 64),
        tasks=(task,))
    attempt = run_id + "." + task_id + ".attempt-001"
    receipt = CanonicalTaskReceipt("receipt." + attempt, run_id, task_id, attempt, "c" * 40, (),
        (manifest.materialization,), (manifest.logical,), (), OperationalStatus.SUCCEEDED, ())
    products = {"receipts": {task_id: receipt}, "outputs": {manifest.logical.logical_artifact_id: manifest}}
    return plane, products, plan, task_id, value


def test_export_reads_actual_committed_product_without_native_entry(receipted_product):
    plane, products, plan, task_id, expected = receipted_product
    actual, receipt = _receipt_product(plane, products, plan, task_id, ObjectIdentity)
    assert actual == expected and receipt is products["receipts"][task_id]


@pytest.mark.parametrize("changed", ("receipt-task", "receipt-run", "missing", "foreign-output", "source-bytes"))
def test_export_refuses_substituted_receipt_source_or_missing_unit(receipted_product, changed):
    plane, products, plan, task_id, _ = receipted_product
    receipt = products["receipts"][task_id]
    if changed == "receipt-task":
        products["receipts"][task_id] = replace(receipt, task_id="task.foreign")
    elif changed == "receipt-run":
        products["receipts"][task_id] = replace(receipt, run_id="run.foreign")
    elif changed == "missing":
        products["receipts"].pop(task_id)
    elif changed == "foreign-output":
        products["outputs"].clear()
    else:
        plane.root.resolve("outputs/product.json", for_write=False).write_bytes(b"changed after publication")
    with pytest.raises((PermissionError, ValueError, OSError, ArtifactPlaneError)):
        _receipt_product(plane, products, plan, task_id, ObjectIdentity)


def _fresh_publications(tmp_path):
    from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_acquisition import entry_task_id
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_bindings import NativeTrainingEntryConfig

    case = fresh_training_metadata_case(tmp_path)
    entry = NativeTrainingEntryConfig("config." + entry_task_id(case.specification), case.specification, case.request)
    # The shared dispatcher authenticates full RecursiveConfigInputs. This
    # disclosed row envelope isolates the actual registered publication callback.
    return case, (SimpleNamespace(record=entry),)


def test_registered_training_callback_reads_actual_complete_prior_publications(tmp_path):
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import (
        authenticate_request, authenticate_training_publications,
    )
    case, rows = _fresh_publications(tmp_path)
    assert authenticate_request(case.plane, case.request) == tuple((role, case.programme_inputs.phase(slot).responses)
        for role, slot in (("CALIBRATION", "e3.calibration"), ("EVALUATION", "e3.confirmation"),
            ("TRANSFER_NEARBY", "e6.nearby"), ("TRANSFER_SHIFTED", "e6.shifted")))
    assert authenticate_training_publications(case.plane, rows) is None
    with pytest.raises(PermissionError, match="one exact complete"):
        authenticate_training_publications(case.plane, ())
    with pytest.raises(PermissionError, match="one exact complete"):
        authenticate_training_publications(case.plane, rows * 2)


@pytest.mark.parametrize("changed", ("missing-commit", "missing-corpus", "changed-reservation",
    "missing-support", "changed-support"))
def test_actual_missing_or_changed_prior_facts_refuse_before_training_effects(tmp_path, changed):
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import (
        authenticate_training_publications,
    )
    case, rows = _fresh_publications(tmp_path)
    assert authenticate_training_publications(case.plane, rows) is None
    manifest = case.request.future_manifest
    if changed in ("missing-support", "changed-support"):
        from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
        _, custody = case.request.exposure_support[0]
        relative = custody.materialization.relative_path if type(custody) is ArtifactWriteResult else custody.relative_path
        member = case.plane.root.resolve(relative, for_write=False)
        if changed == "missing-support":
            member.unlink()
        else:
            member.write_bytes(member.read_bytes() + b" ")
    elif changed == "missing-corpus":
        publication = manifest.audit.prior_corpus[0]
        case.plane.root.resolve(publication.materialization.relative_path, for_write=False).unlink()
    elif changed == "missing-commit":
        publication = manifest.reservation_publication
        sidecar = decode_artifact_manifest(case.plane.root.resolve(
            publication.manifest_materialization.relative_path, for_write=False).read_bytes())
        assert sidecar.publication is not None
        case.plane.root.resolve(sidecar.publication.commit_marker_relative_path, for_write=False).unlink()
    else:
        publication = manifest.reservation_publication
        member = case.plane.root.resolve(publication.materialization.relative_path, for_write=False)
        raw = member.read_bytes()
        member.write_bytes(raw[:-1] + b" ")
    with pytest.raises((PermissionError, ValueError, OSError, ArtifactPlaneError)):
        authenticate_training_publications(case.plane, rows)
