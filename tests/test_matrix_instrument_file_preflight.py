# SPDX-License-Identifier: MPL-2.0
"""FILE-preflight ordering over actual authored metadata and physical bytes.

The certificate records are explicitly unexecuted mathematical fixtures. The
expensive scientific producer is the sole stubbed admission boundary; its return
value conveys no real TRAIN/DEV completion, source qualification or authority.
The metadata loader, exact request/packet join, FILE hashing and scoped final
checks remain actual. Real completed TRAIN replay has a separate retained test.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_finite_dt_source_runtime as finite
from empirical_lawhood.api import matrix_prepared_source_runtime as prepared
from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader
from empirical_lawhood.api.experiment_preparation import author_prepared_experiment
from empirical_lawhood.api.recursive_authoring import load_authored_wave
from empirical_lawhood.api.recursive_execution import _retained_plans
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as training_records
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from tests.test_matrix_finite_dt_source import _certificate, _control
from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case
from tests.test_matrix_native_training_public_lifecycle import _copied_preparation
from tests.test_matrix_prepared_source import disclosed_certificate, prepared_bank
from tests.test_matrix_selected_opportunity import opportunity  # noqa: F401
from tests.test_matrix_selected_protected import confirmation, transfer  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def metadata(tmp_path_factory):
    directory = tmp_path_factory.mktemp("instrument-file-preflight")
    case = fresh_training_metadata_case(directory)
    census = case.request.future_manifest.audit.census
    future_bytes = case.request.future_manifest.canonical_bytes()
    prior_corpus = case.request.future_manifest.audit.prior_corpus
    mandatory = training_records.future_response_support(case.request)
    assert len(mandatory) == 7
    (artifact, publication), = exposure_support(case.request.future_manifest.audit)
    assert (artifact, publication) in case.request.exposure_support
    original = case.plane.root.resolve(publication.materialization.relative_path, for_write=False)
    raw = original.read_bytes()
    assert raw == census.canonical_bytes()
    assert (sha256(raw).hexdigest(), len(raw)) == (artifact.sha256, artifact.size_bytes)
    manifest = case.plane.read_manifest(publication.materialization.relative_path)
    case.plane.verify_manifest(manifest)
    assert (manifest.logical, manifest.materialization) == (publication.logical, publication.materialization)
    sidecar = case.plane.root.resolve(publication.manifest_materialization.relative_path, for_write=False)
    marker = case.plane.root.resolve(manifest.publication.commit_marker_relative_path, for_write=False)
    sidecar_raw, marker_raw = sidecar.read_bytes(), marker.read_bytes()
    relative = "native-file-support/exposure-census.json"
    copied = case.plane.root.resolve(relative, for_write=True)
    copied.parent.mkdir()
    copied.write_bytes(raw)
    assert copied != original and copied.read_bytes() == raw
    assert (sha256(copied.read_bytes()).hexdigest(), copied.stat().st_size) == (artifact.sha256, artifact.size_bytes)
    assert not Path(str(copied) + ".manifest.json").exists()
    assert tuple(path.name for path in copied.parent.iterdir()) == (copied.name,)
    assert not (copied.parent / ".publication-batches").exists()
    binding = ExperimentFileInputBinding("file." + artifact.artifact_id, artifact, census.VERSION, relative, len(raw))
    case.request = replace(case.request, exposure_support=tuple(
        (value, binding if value == artifact else custody) for value, custody in case.request.exposure_support))
    assert training_records.future_response_support(case.request) == mandatory
    assert case.request.future_manifest.canonical_bytes() == future_bytes
    assert case.request.future_manifest.audit.prior_corpus == prior_corpus
    assert original.read_bytes() == raw and sidecar.read_bytes() == sidecar_raw and marker.read_bytes() == marker_raw
    case.acquisition = training_records.acquisition_seal(case.specification, case.request)
    preparation = _copied_preparation(case, directory / "copied")
    authored = Path(case.plane.root.contract.canonical_path) / "authored-only"
    author_prepared_experiment(preparation=preparation, project_root=ROOT,
        artifact_writer=case.plane, output_dir=authored)
    packet, draft, _, payloads = load_authored_wave(directory=authored,
        artifact_writer=case.plane, lazy_payloads=True)
    run, plan, _ = _retained_plans(payloads, draft)
    locator = finite.r.MatrixFiniteDtTrainingLocator("authored-only", run.run_plan_id,
        ObjectIdentity.from_record(packet.packet_id, packet),
        ObjectIdentity.from_record(plan.execution_plan_id, plan))
    certificate = replace(_certificate(case, (_control(case, 0, available=False),)), locator=locator)
    raw = b"disclosed separate current DEV FILE support"
    current_path = Path(case.plane.root.contract.canonical_path) / "support/current-dev.bin"
    current_path.write_bytes(raw)
    current = ArtifactIdentity("support.current-dev", "disclosed-file-ordering",
        "empirical-lawhood/source/checksummed-uninterpreted-public-bytes", sha256(raw).hexdigest(),
        "text/plain", len(raw))
    binding = ExperimentFileInputBinding("current-dev", current, "1.0.0", "support/current-dev.bin", len(raw))
    return SimpleNamespace(case=case, certificate=certificate, current=(current, binding))


@pytest.fixture(params=("finite", "prepared"))
def control(request, metadata, confirmation, opportunity):  # noqa: F811
    case = metadata.case
    if request.param == "finite":
        return SimpleNamespace(owner=finite, call=finite.authenticate_instrument_certificate,
            producer="certify_native_training_instrument", certificate=metadata.certificate,
            native_locator=metadata.certificate.locator,
            operands=dict(programme=case.specification, bank=case.request,
                original_future_reservation=case.request.future_manifest.reservation), metadata=metadata)
    bank = prepared_bank(confirmation)
    certificate = replace(disclosed_certificate(bank, opportunity),
        native_training_locator=metadata.certificate.locator, native_training_request=case.request.identity)
    # This explicitly disclosed bank boundary supplies one real current FILE;
    # the scientific producer is stubbed below, not admitted by this control.
    bank_boundary = SimpleNamespace(fingerprint=bank.fingerprint,
        exposure_support=(metadata.current,))
    return SimpleNamespace(owner=prepared, call=prepared.authenticate_prepared_source_certificate,
        producer="certify_prepared_source_instrument", certificate=certificate,
        native_locator=certificate.native_training_locator,
        operands=dict(bank=bank_boundary, maximum_source_bytes=128 * 1024**2), metadata=metadata)


def producer(monkeypatch, control, after=None):
    calls = []
    def disclosed(**kwargs):
        calls.append(kwargs)
        if after is not None:
            after()
        return control.certificate
    monkeypatch.setattr(control.owner, control.producer, disclosed)
    return calls


def native_path(control):
    (artifact, binding), = tuple(row for row in control.metadata.case.request.exposure_support
        if type(row[1]) is ExperimentFileInputBinding)
    return control.metadata.case.plane.root.resolve(binding.relative_path, for_write=False), artifact


def test_cold_bad_native_file_refuses_before_scientific_reconstruction(control, monkeypatch):
    calls = producer(monkeypatch, control)
    path, artifact = native_path(control)
    raw = path.read_bytes()
    try:
        path.write_bytes(b"x" * artifact.size_bytes)
        with pytest.raises(ValueError, match="FILE differs"):
            control.call(writer=control.metadata.case.plane, certificate=control.certificate, **control.operands)
        assert calls == []
    finally:
        path.write_bytes(raw)


def test_cold_and_warm_positive_reuse_keeps_raw_file_preflight(control, monkeypatch):
    calls = producer(monkeypatch, control)
    path, artifact = native_path(control)
    raw = path.read_bytes()
    with control.metadata.case.plane.verification_scope() as writer:
        reader = CurrentResultPlanReader(writer)
        for _ in range(2):
            control.call(writer=writer, control_reader=reader, certificate=control.certificate, **control.operands)
        assert len(calls) == 1
        try:
            path.write_bytes(b"x" * artifact.size_bytes)
            with pytest.raises(ValueError, match="FILE differs"):
                control.call(writer=writer, control_reader=reader, certificate=control.certificate, **control.operands)
            assert len(calls) == 1
        finally:
            path.write_bytes(raw)


def test_file_mutation_during_reconstruction_still_refuses_at_final_check(control, monkeypatch):
    path, artifact = native_path(control)
    raw = path.read_bytes()
    calls = producer(monkeypatch, control, lambda: path.write_bytes(b"x" * artifact.size_bytes))
    try:
        with pytest.raises(ValueError, match="FILE differs"):
            control.call(writer=control.metadata.case.plane, certificate=control.certificate, **control.operands)
        assert len(calls) == 1
    finally:
        path.write_bytes(raw)


@pytest.mark.parametrize("changed", ("request", "packet"))
def test_cold_preflight_joins_actual_authored_request_and_locator_before_producer(control, monkeypatch, changed):
    calls = producer(monkeypatch, control)
    if changed == "packet":
        altered_locator = replace(control.native_locator,
            packet=replace(control.native_locator.packet, object_fingerprint="2" * 64))
        key = "locator" if control.owner is finite else "native_training_locator"
        certificate = replace(control.certificate, **{key: altered_locator})
    else:
        key = "request" if control.owner is finite else "native_training_request"
        original = getattr(control.certificate, key)
        certificate = replace(control.certificate, **{key: replace(original, object_fingerprint="2" * 64)})
    with pytest.raises(PermissionError, match="authenticated original request"):
        control.call(writer=control.metadata.case.plane, certificate=certificate, **control.operands)
    assert calls == []


@pytest.mark.parametrize("when", ("before", "during"))
def test_prepared_separate_current_file_is_checked_on_both_sides_of_reconstruction(metadata, confirmation, opportunity, monkeypatch, when):  # noqa: F811
    bank = prepared_bank(confirmation)
    certificate = replace(disclosed_certificate(bank, opportunity),
        native_training_locator=metadata.certificate.locator, native_training_request=metadata.case.request.identity)
    bank_boundary = SimpleNamespace(fingerprint=bank.fingerprint, exposure_support=(metadata.current,))
    artifact, binding = metadata.current
    path = metadata.case.plane.root.resolve(binding.relative_path, for_write=False)
    raw = path.read_bytes()
    calls = []
    def disclosed(**kwargs):
        calls.append(kwargs)
        if when == "during":
            path.write_bytes(b"x" * artifact.size_bytes)
        return certificate
    monkeypatch.setattr(prepared, "certify_prepared_source_instrument", disclosed)
    try:
        if when == "before":
            path.write_bytes(b"x" * artifact.size_bytes)
        with pytest.raises(ValueError, match="FILE differs"):
            prepared.authenticate_prepared_source_certificate(writer=metadata.case.plane,
                certificate=certificate, bank=bank_boundary, maximum_source_bytes=128 * 1024**2)
        assert len(calls) == (0 if when == "before" else 1)
    finally:
        path.write_bytes(raw)
