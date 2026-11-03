# SPDX-License-Identifier: MPL-2.0
"""Operational counters preserve actual preparation and custody decisions."""

from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import selected_deanneal_specification
from empirical_lawhood.api.experiment_preparation import experiment_preparation_report, prepare_experiment
from empirical_lawhood.api.prospective_experiment import load_prepared_prospective_experiment
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.infrastructure.candidate_sources import ExternalCandidateInputPublisher
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.progress import progress_reporting
from tests.test_unrestricted_source_resolution import _root


class _Recorder:
    def __init__(self, *, broken=False):
        self.events = []
        self.broken = broken

    def update(self, **event):
        self.events.append(event)
        if self.broken:
            raise OSError("exposed unavailable telemetry destination")


def _events(recorder, phase):
    return [event for event in recorder.events if event["phase"] == phase]


def _publication(tmp_path, count=3):
    plane = ExternalArtifactPlane(_root(tmp_path))
    requests = []
    for index in range(count):
        subject = ObjectIdentity.from_record(f"exposed.subject.{index}",
            selected_deanneal_specification(protocol_sha256=sha256(b"exposed protocol").hexdigest()))
        requests.append(ArtifactWriteRequest(f"exposed.member.{index}", f"outputs/member-{index}.json",
            ObjectIdentity.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.complete-batch", "outputs",
            subject.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    results = plane.write_batch(tuple(requests))
    manifests = tuple(decode_artifact_manifest(plane.root.resolve(
        row.manifest_materialization.relative_path, for_write=False).read_bytes()) for row in results)
    return plane, manifests


@pytest.mark.parametrize("broken_reporter", (False, True))
def test_preparation_progress_preserves_report_and_specification_bytes(broken_reporter):
    specification = selected_deanneal_specification(protocol_sha256=sha256(b"exposed protocol").hexdigest())
    original = specification.canonical_bytes()
    baseline = prepare_experiment(specification)
    recorder = _Recorder(broken=broken_reporter)
    with progress_reporting(recorder):
        observed = prepare_experiment(specification)
    assert observed == baseline
    assert experiment_preparation_report(observed) == experiment_preparation_report(baseline)
    assert specification.canonical_bytes() == original
    assert [(event["done"], event["total"], event["failed"]) for event in recorder.events] == [(0, 1, 0), (1, 1, 0)]
    assert {event["phase"] for event in recorder.events} == {"prepare_specification"}


def test_preparation_and_loader_refusals_never_report_success():
    recorder = _Recorder()
    with progress_reporting(recorder):
        with pytest.raises(ValueError, match="installed domain protocol"):
            prepare_experiment(object())
        with pytest.raises(TypeError, match="explicit boolean"):
            load_prepared_prospective_experiment(directory="unused", project_root="unused",
                storage_profile=None, artifact_writer=None, require_current_source="not a boolean")
    assert _events(recorder, "prepare_specification")[-1] == {
        "phase": "prepare_specification", "done": 1, "total": 1, "failed": 1}
    # Invalid API options refuse before an experiment load starts.
    assert _events(recorder, "load_experiment") == []


def test_publication_reports_only_synced_windows_and_preserves_exact_replay(tmp_path, monkeypatch):
    publisher = ExternalCandidateInputPublisher(_root(tmp_path))
    payloads = (b"exposed first", b"exposed second", b"exposed third")
    recorder = _Recorder()
    original_sync = publisher._sync_directories
    synced = []

    def sync(directories):
        original_sync(directories)
        synced.append(len(_events(recorder, "publish_inputs")))

    monkeypatch.setattr(publisher, "_sync_directories", sync)

    def selected():
        yield payloads[0]
        assert [(event["done"], event["total"]) for event in recorder.events] == [(0, None)]
        yield payloads[1]
        assert [(event["done"], event["total"]) for event in recorder.events] == [(0, None), (2, None)]
        assert synced == [1]
        yield payloads[2]

    with progress_reporting(recorder):
        results = publisher.publish_many(selected(), batch_size=2)
    assert [(event["done"], event["total"]) for event in recorder.events] == [(0, None), (2, None), (3, 3)]
    assert synced == [1, 2]
    paths = tuple(tmp_path / row.relative_locator for row in results)
    before = [(path.read_bytes(), path.stat().st_mtime_ns) for path in paths]
    assert tuple(raw for raw, _mtime in before) == payloads
    with progress_reporting(_Recorder(broken=True)):
        replay = publisher.publish_many(iter(payloads), batch_size=2)
    assert all(row.replayed for row in replay)
    assert [(row.content_sha256, row.size_bytes, row.relative_locator) for row in replay] == [
        (row.content_sha256, row.size_bytes, row.relative_locator) for row in results]
    assert [(path.read_bytes(), path.stat().st_mtime_ns) for path in paths] == before


@pytest.mark.parametrize("failure", ("iterator", "sync"))
def test_publication_failure_never_reports_durable_completion(tmp_path, monkeypatch, failure):
    publisher = ExternalCandidateInputPublisher(_root(tmp_path))
    recorder = _Recorder()
    failure_object = OSError("exposed selected operation failure")

    def payloads():
        yield b"exposed completed prefix"
        if failure == "iterator":
            raise failure_object

    if failure == "sync":
        def refuse_sync(_directories):
            raise failure_object
        monkeypatch.setattr(publisher, "_sync_directories", refuse_sync)
    with progress_reporting(recorder), pytest.raises(OSError) as raised:
        publisher.publish_many(payloads(), batch_size=2)
    assert raised.value is failure_object
    assert recorder.events[0]["done"] == 0
    assert all(event["total"] is None for event in recorder.events)
    assert recorder.events[-1]["failed"] == 1


def test_artifact_completion_follows_consumer_and_final_snapshot_without_extra_decodes(tmp_path, monkeypatch):
    plane, manifests = _publication(tmp_path)
    recorder = _Recorder()
    reads = []
    original_read = plane._read_current_manifest

    def read(path, **kwargs):
        reads.append(path)
        return original_read(path, **kwargs)

    monkeypatch.setattr(plane, "_read_current_manifest", read)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    def consume(members):
        assert len(members) == len(manifests)
        assert recorder.events[-1]["done"] == len(manifests) - 1
        assert all(event["done"] != event["total"] for event in recorder.events)
        return tuple(members)

    with progress_reporting(recorder):
        result = plane.verify_manifest_members(manifests[0], validate_members=consume)
    assert set(result) == {row.materialization.relative_path for row in manifests}
    assert len(reads) == len(manifests) + 1
    assert [event["done"] for event in recorder.events] == [0, 1, 2, 3]
    assert recorder.events[-1] == {"phase": "verify_artifact_members", "done": 3, "total": 3, "failed": 0}
    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.parametrize("failure", ("sibling", "callback-mutation"))
def test_artifact_refusal_never_emits_guarded_completion(tmp_path, failure):
    plane, manifests = _publication(tmp_path)
    recorder = _Recorder()
    changed = plane.root.resolve(manifests[-1].materialization.relative_path, for_write=False)
    if failure == "sibling":
        changed.write_bytes(b"exposed corrupt sibling")
    entered = []

    def consume(_members):
        entered.append(True)
        changed.write_bytes(b"exposed concurrent mutation")

    with progress_reporting(recorder), pytest.raises(ArtifactIdentityConflict):
        plane.verify_manifest_members(manifests[0], validate_members=consume)
    assert entered == ([True] if failure == "callback-mutation" else [])
    assert not any(event["done"] == event["total"] for event in recorder.events)
    assert recorder.events[-1]["failed"] == 1


def test_scoped_verification_reports_work_once_and_new_calls_remain_fresh(tmp_path):
    plane, manifests = _publication(tmp_path)
    recorder = _Recorder()
    with progress_reporting(recorder), plane.verification_scope() as scoped:
        scoped.verify_manifests(manifests)
        first = len(recorder.events)
        scoped.verify_manifests(manifests)
    assert recorder.events[first:] == [
        {"phase": "verify_artifact_members", "done": 0, "total": None, "failed": 0},
        {"phase": "verify_artifact_members", "done": 0, "total": 0, "failed": 0}]
    recorder.events.clear()
    with progress_reporting(recorder):
        plane.verify_manifest(manifests[0])
    assert recorder.events[-1]["done"] == len(manifests)
