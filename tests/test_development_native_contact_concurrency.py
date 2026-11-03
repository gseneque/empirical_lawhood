# SPDX-License-Identifier: MPL-2.0
"""Legacy native contact admission with real custody and synthetic workers only."""

import multiprocessing
import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_development_native_custody import SyntheticConfig, SyntheticResult
from empirical_lawhood.api.matrix_native_custody import MatrixNativeCustody
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.development_native_custody import DevelopmentNativeCustody
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ExternalRootContract
from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile


RUN = "synthetic.legacy-contact"
TASK = "unit-one"
CLASSES = {"development": DevelopmentNativeCustody, "matrix": MatrixNativeCustody}


def _custody(path, kind, *, read_only=False):
    path = Path(path)
    path.mkdir(exist_ok=True)
    mount = next(parent for parent in (path, *path.parents) if os.path.ismount(parent))
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "synthetic.legacy-contact", "software conformance only", str(path), str(mount),
        OperatorStorageProfile.SCHEMA, 1, None, None, ())))
    return CLASSES[kind](writer=plane, config=SyntheticConfig(), run_id=RUN,
        implementation_commit="0" * 40, minimum_free_bytes=1,
        maximum_output_bytes=4096, read_only=read_only)


def _marker_relative():
    return f"runs/{RUN}/inputs/effects/{TASK}.json"


def _marker_request(custody, marker):
    return ArtifactWriteRequest(f"{RUN}.{TASK}.effect-input", _marker_relative(),
        marker.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
        f"{RUN}.effect-inputs", f"runs/{RUN}/inputs/effects", marker.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (VisibilityCeiling.DEVELOPMENT_ONLY,),
        OutcomeAccess.DEVELOPMENT_VISIBLE, lineage_parents=(custody.parent,),
        minimum_free_bytes=1)


def _inventory(path):
    return {str(value.relative_to(path)): (value.read_bytes(), value.stat().st_mtime_ns)
            for value in path.rglob("*") if value.is_file()}


def _launch(path, kind, launcher, barrier, queue):
    """Two independent instances observe absence before either can publish."""
    result = {"launcher": launcher, "synthetic_worker_entries": 0,
              "publications_created": [], "native_acquisitions": 0}
    try:
        custody = _custody(path, kind)
        original_manifest, original_write = custody._manifest, custody.writer.write
        first_read = True

        def stale_absence(relative):
            nonlocal first_read
            manifest = original_manifest(relative)
            if relative == _marker_relative() and first_read:
                first_read = False
                assert manifest is None
                barrier.wait(timeout=30)
            return manifest

        def capture_publication(request):
            publication = original_write(request)
            if request.relative_path == _marker_relative():
                result["publications_created"].append(publication.created)
            return publication

        custody._manifest, custody.writer.write = stale_absence, capture_publication
        custody.begin_native_effect(TASK)
        # This is the only synthetic effect boundary. No native adapter is used.
        result["synthetic_worker_entries"] = 1
        (path / f"synthetic-worker-{launcher}.txt").write_text("entered\n")
        custody.retain(TASK, SyntheticResult())
        result["status"] = "SUCCEEDED"
    except Exception as error:
        result["error_type"], result["error"] = type(error).__name__, str(error)
    finally:
        queue.put(result)


def _race_results(path, kind):
    _custody(path, kind)
    context = multiprocessing.get_context("spawn")
    barrier, queue = context.Barrier(2), context.Queue()
    children = [context.Process(target=_launch, args=(path, kind, i, barrier, queue))
                for i in range(2)]
    try:
        for child in children:
            child.start()
        results = [queue.get(timeout=60) for _ in children]
        for child in children:
            child.join(timeout=10)
            assert child.exitcode == 0
        return sorted(results, key=lambda result: result["launcher"])
    finally:
        for child in children:
            if child.is_alive():
                child.terminate()
                child.join(timeout=10)
        queue.close()


@pytest.mark.parametrize("kind", CLASSES)
def test_false_created_matching_publication_never_admits_worker(tmp_path, kind, monkeypatch):
    custody = _custody(tmp_path, kind)
    monkeypatch.setattr(custody.writer, "write", lambda _request: SimpleNamespace(created=False))
    worker_entries = []
    with pytest.raises(ValueError, match="reus|creat|already"):
        custody.begin_native_effect(TASK)
        worker_entries.append(TASK)
    assert worker_entries == []


@pytest.mark.parametrize("kind", CLASSES)
def test_stale_absence_cannot_reuse_another_instances_real_publication(tmp_path, kind, monkeypatch):
    owner = _custody(tmp_path, kind)
    owner.begin_native_effect(TASK)
    before = _inventory(tmp_path)
    contender = _custody(tmp_path, kind)
    original_manifest = contender._manifest
    first_read = True

    def stale_absence(relative):
        nonlocal first_read
        if relative == _marker_relative() and first_read:
            first_read = False
            return None
        return original_manifest(relative)

    monkeypatch.setattr(contender, "_manifest", stale_absence)
    with pytest.raises(ValueError, match="reus|creat|already"):
        contender.begin_native_effect(TASK)
    assert _inventory(tmp_path) == before


@pytest.mark.parametrize("kind", CLASSES)
def test_creator_requires_exact_surviving_marker_readback(tmp_path, kind, monkeypatch):
    custody = _custody(tmp_path, kind)
    original_write = custody.writer.write
    marker = custody.effect_input_type(RUN, TASK, custody.parent.identity)
    wrong = replace(marker, configuration=ObjectIdentity.from_record("other.config", SyntheticConfig(choice=2)))

    def wrong_payload(request):
        return original_write(replace(request, payload=wrong.canonical_bytes()))

    monkeypatch.setattr(custody.writer, "write", wrong_payload)
    worker_entries = []
    with pytest.raises(ValueError, match="marker|publication|exact|differ"):
        custody.begin_native_effect(TASK)
        worker_entries.append(TASK)
    assert worker_entries == []
    before = _inventory(tmp_path)
    fresh = _custody(tmp_path, kind)
    with pytest.raises(ValueError, match="uncertain effects"):
        fresh.load(TASK, SyntheticResult)
    with pytest.raises(ValueError, match="no retry|already"):
        fresh.begin_native_effect(TASK)
    assert _inventory(tmp_path) == before


@pytest.mark.parametrize("kind", CLASSES)
def test_two_process_launches_enter_one_synthetic_worker_and_preserve_winner_receipt(tmp_path, kind):
    results = _race_results(tmp_path, kind)
    assert sum(result["synthetic_worker_entries"] for result in results) == 1, results
    assert sorted(result["publications_created"] for result in results) == [[False], [True]], results
    winner = next(result for result in results if result["synthetic_worker_entries"] == 1)
    loser = next(result for result in results if result["synthetic_worker_entries"] == 0)
    assert winner["status"] == "SUCCEEDED" and loser["error_type"] == "ValueError", results
    assert all(result["native_acquisitions"] == 0 for result in results)
    assert len(tuple(tmp_path.glob("synthetic-worker-*.txt"))) == 1
    reader = _custody(tmp_path, kind, read_only=True)
    before = _inventory(tmp_path)
    assert reader.load(TASK, SyntheticResult) == SyntheticResult()
    receipt = reader.store.read_by_receipt_id(RUN, TASK, f"receipt.{RUN}.{TASK}.attempt-001")
    assert receipt is not None and receipt.operational_status.value == "SUCCEEDED"
    assert reader._manifest(_marker_relative()) is not None
    raw = (tmp_path / _marker_relative()).read_bytes()
    assert raw == reader.effect_input_type(RUN, TASK, reader.parent.identity).canonical_bytes()
    assert _inventory(tmp_path) == before


@pytest.mark.parametrize("kind", CLASSES)
def test_mismatched_retained_contact_refuses_without_worker_or_republication(tmp_path, kind):
    custody = _custody(tmp_path, kind)
    marker = custody.effect_input_type(RUN, TASK, custody.parent.identity)
    wrong = replace(marker, configuration=ObjectIdentity.from_record("other.config", SyntheticConfig(choice=2)))
    custody.writer.write(_marker_request(custody, wrong))
    before = _inventory(tmp_path)
    with pytest.raises(ValueError, match="no retry|already"):
        custody.begin_native_effect(TASK)
    with pytest.raises(ValueError, match="uncertain effects"):
        custody.load(TASK, SyntheticResult)
    assert _inventory(tmp_path) == before


@pytest.mark.parametrize("kind", CLASSES)
def test_partial_retained_contact_refuses_without_repair_or_retry(tmp_path, kind):
    custody = _custody(tmp_path, kind)
    path = custody.writer.root.resolve(_marker_relative(), for_write=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(custody.effect_input_type(RUN, TASK, custody.parent.identity).canonical_bytes())
    before = _inventory(tmp_path)
    for operation in (lambda: custody.begin_native_effect(TASK),
                      lambda: custody.load(TASK, SyntheticResult)):
        with pytest.raises(ValueError, match="partial"):
            operation()
    assert _inventory(tmp_path) == before


@pytest.mark.parametrize("kind", CLASSES)
def test_exception_after_marker_publication_remains_uncertain_and_cannot_retry(tmp_path, kind, monkeypatch):
    custody = _custody(tmp_path, kind)
    original_write = custody.writer.write

    def committed_then_interrupted(request):
        original_write(request)
        raise RuntimeError("synthetic interruption after contact publication")

    monkeypatch.setattr(custody.writer, "write", committed_then_interrupted)
    with pytest.raises(RuntimeError, match="synthetic interruption"):
        custody.begin_native_effect(TASK)
    before = _inventory(tmp_path)
    fresh = _custody(tmp_path, kind)
    with pytest.raises(ValueError, match="uncertain effects"):
        fresh.load(TASK, SyntheticResult)
    with pytest.raises(ValueError, match="no retry|already"):
        fresh.begin_native_effect(TASK)
    assert _inventory(tmp_path) == before


@pytest.mark.parametrize("kind", CLASSES)
def test_completed_receipt_replay_preserves_exact_marker_bytes_and_mtime(tmp_path, kind):
    custody = _custody(tmp_path, kind)
    custody.begin_native_effect(TASK)
    custody.retain(TASK, SyntheticResult())
    before = _inventory(tmp_path)
    fresh = _custody(tmp_path, kind)
    assert fresh.load(TASK, SyntheticResult) == SyntheticResult()
    with pytest.raises(ValueError, match="no retry|already"):
        fresh.begin_native_effect(TASK)
    assert _inventory(tmp_path) == before
