# SPDX-License-Identifier: MPL-2.0
"""Historical application reads of disclosed small source-custody fixtures."""

from dataclasses import replace
from pathlib import Path
import shutil

import pytest

from empirical_lawhood.api import application_continuing as owner
from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest, load_application_json, response_bytes
from empirical_lawhood.storage.continuing_source import ExternalContinuingSourceStore
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from tests.test_continuing_source import case, operation, packet


def context():
    return ApplicationContext("history", "Exposed software control", Path("/selected/python"))


def read(selected, monkeypatch, name="continuing.session", **parameters):
    monkeypatch.setattr(owner, "application_storage", lambda *a, **k: (None, None, selected.plane))
    request = ApplicationRequest("history.read", "history", name, tuple({
        "directory": str(Path(selected.plane.root.contract.canonical_path) / selected.store.relative_root),
        **parameters}.items()))
    return execute_application(context(), request)


def wire(result):
    assert result.succeeded, result
    return load_application_json(response_bytes(result))["payload"]


def test_closed_history_keeps_uncertain_effect_without_live_owner_or_repeated_submission(tmp_path, monkeypatch):
    with case(tmp_path) as selected:
        op, payload = operation(selected)
        selected.effect.failure = TimeoutError("original lost reply")
        selected.a.execute(op, payload)
    selected.access.revoked = True
    monkeypatch.setattr(selected.effect, "submit", lambda *a: pytest.fail("historical read submitted an effect"))
    monkeypatch.setattr(selected.effect, "observe", lambda *a: pytest.fail("historical read contacted a source"))
    monkeypatch.setattr(ExternalContinuingSourceStore, "owner_lock", lambda *a: pytest.fail("read acquired live ownership"))
    result = wire(read(selected, monkeypatch, "continuing.operation", request_id=op.request_id))
    assert result["summary"]["effect_disposition"] == "UNKNOWN_EFFECT_DO_NOT_REPEAT"
    assert result["summary"]["retained_disposition"] == "CLOSED_NOT_SCIENTIFICALLY_ASSESSED"
    assert result["summary"]["current_actor_access"] == "NOT_GRANTED_BY_HISTORY"
    assert result["continuing"]["operation"] == op.to_document()
    assert result["continuing"]["receipt"] is None and result["continuing"]["possible_contact"] is True
    assert len(selected.effect.calls) == 1
    missing = read(selected, monkeypatch, "continuing.operation", request_id="request.absent")
    assert missing.reason_codes == ("FINITE_REQUEST_NOT_RETAINED",) and missing.payload is None


def test_selected_windows_preserve_delayed_coordinates_gap_and_shared_dependence(tmp_path, monkeypatch):
    with case(tmp_path) as selected:
        first = packet(selected, 1, sampled=5, available=9)
        selected.owner.ingest((first, packet(selected, 3)))
    result = wire(read(selected, monkeypatch, segment_count=2, filter="EVENT_SEGMENT"))
    # The original lifecycle reader reports closure, not event completeness.
    # The separate original window keeps both the gap and missing segment.
    assert result["summary"]["retained_disposition"] == "CLOSED_NOT_SCIENTIFICALLY_ASSESSED"
    assert result["summary"]["complete_selected_event_window"] is False
    assert result["summary"]["whole_session_complete"] is False
    assert result["page"]["total"] > result["page"]["matching_total"] == 1
    assert result["continuing"]["event_window"]["missing_segment_indices"] == [2]
    assert len(result["continuing"]["event_window"]["sequence_gaps"]) == 1
    event = result["continuing"]["event_window"]["segments"][0]["value"]["events"][0]
    assert event == first.observation.to_document()
    assert result["provenance"]["dependence_root"] == selected.session.dependence_root.to_document()
    assert {row["value"]["actor_id"] for row in result["continuing"]["actor_leases"]} == {"actor.a", "actor.b"}
    assert all(row["value"]["session"] == selected.session.identity.to_document()
        for row in result["continuing"]["actor_leases"])


def test_historical_actor_reader_refuses_foreign_session_and_identity(tmp_path):
    with case(tmp_path) as selected:
        original = selected.a.lease
        assert selected.store.read_actor_lease(original.identity) == original
        with pytest.raises(ValueError, match="lease identity"):
            selected.store.read_actor_lease(selected.package.identity)
        foreign_session = replace(selected.session, session_id="another.session")
        foreign = replace(original, session=foreign_session.identity)
        # A disclosed malformed fixture retains exact bytes under this session;
        # the typed reader must still reject its foreign scientific session.
        selected.store._publish(selected.store._record_path(foreign.identity), foreign.identity, foreign.canonical_bytes())
        with pytest.raises(ValueError, match="session or identity"):
            selected.store.read_actor_lease(foreign.identity)


def test_outcome_blind_session_cannot_use_exposed_history_route(tmp_path, monkeypatch):
    with case(tmp_path) as selected:
        session = replace(selected.session, session_id="protected.session", visibility=VisibilityCeiling.PROSPECTIVE,
            outcome_access=OutcomeAccess.OUTCOME_BLIND)
        protected = ExternalContinuingSourceStore(plane=selected.plane, session=session, relative_root="protected")
        with protected.owner_lock():
            protected.initialize(selected.package.identity, selected.package.canonical_bytes())
    path = str(Path(selected.plane.root.contract.canonical_path) / protected.relative_root)
    result = read(selected, monkeypatch, directory=path)
    assert result.reason_codes == ("CURRENT_CUSTODY_REFUSED",) and result.payload is None
    assert b"protected.session" not in response_bytes(result)


def test_changed_original_after_projection_refuses_the_entire_historical_view(tmp_path, monkeypatch):
    with case(tmp_path) as selected:
        first = packet(selected, 1)
        selected.owner.ingest((first,))
    assert read(selected, monkeypatch).succeeded
    original = owner.projection
    path = selected.store._path(selected.store._record_path(first.observation.payload))
    def change(**kwargs):
        result = original(**kwargs)
        path.write_bytes(path.read_bytes().replace(b'"value":1', b'"value":9'))
        return result
    monkeypatch.setattr(owner, "projection", change)
    result = read(selected, monkeypatch)
    assert not result.succeeded and result.payload is None


def test_substituted_session_directory_never_becomes_another_historical_identity(tmp_path, monkeypatch):
    with case(tmp_path) as selected:
        selected.owner.ingest((packet(selected, 1),))
    original = Path(selected.plane.root.contract.canonical_path) / selected.store.relative_root
    substitute = original.parent / "substituted"
    shutil.copytree(original, substitute)
    result = read(selected, monkeypatch, directory=str(substitute))
    assert not result.succeeded and result.payload is None


def test_invalid_window_and_access_selections_refuse_before_opening_history(monkeypatch):
    monkeypatch.setattr(owner, "application_storage", lambda *a, **k: pytest.fail("invalid request opened storage"))
    for values in ({"segment_count": 17}, {"first_segment": 0}, {"boundary_count": True}, {"first_boundary": -1}):
        request = ApplicationRequest("history.invalid", "history", "continuing.session",
            tuple({"directory": "/original/history", **values}.items()))
        assert execute_application(context(), request).reason_codes == ("INVALID_HISTORY_WINDOW",)
    selected = replace(context(), read_access_paths=(Path("/protected/access"),))
    request = ApplicationRequest("history.access", "history", "continuing.session", (("directory", "/original/history"),))
    assert execute_application(selected, request).reason_codes == ("UNSUPPORTED_ACCESS_SELECTION",)
