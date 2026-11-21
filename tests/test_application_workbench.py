# SPDX-License-Identifier: MPL-2.0
"""Application-only boundary checks. No scientific acquisition or campaign fixture."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from empirical_lawhood.api import application as owner
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationError, ApplicationRequest, error_result, load_application_json, response_bytes
from empirical_lawhood.api.application_projections import execution_projection, page
from empirical_lawhood.api.results import ApiResult, OperationStatus


def context(name="ctx.one"):
    return ApplicationContext(name, name, Path("/selected/bin/python"))


def request(operation="recursive.execution", name="ctx.one", **parameters):
    return ApplicationRequest("request.one", name, operation, tuple(sorted(parameters.items())))


def execution():
    return dict(run_id="run.original", status="SUCCEEDED", execution_plan={"object_fingerprint": "a"*64},
        task_count=3, read_scope="EXECUTION_RECORDS", scientific_completion="DEFERRED_TO_FULL_READ",
        scientific_qualification="NOT_ESTABLISHED", new_native_contact_count=0,
        operational_census=(
            dict(task_id="a", ordinal=1, operational_status="FAILED", reason_code="ORIGINAL_FAILURE"),
            dict(task_id="a", ordinal=2, operational_status="SUCCEEDED"),
            dict(task_id="b", ordinal=1, operational_status="UNKNOWN"),
            dict(task_id="c", ordinal=None, operational_status="UNENTERED")))


def test_context_roundtrip_and_exact_selections_do_not_cache_access():
    selected = replace(context(), operator_profile=Path("/external/profile.json"),
        read_access_paths=(Path("/external/current-access.json"),), maximum_parallel_tasks=4)
    assert ApplicationContext.from_document(load_application_json(json.dumps(selected.to_document()).encode())) == selected
    assert selected.fingerprint() != replace(selected, maximum_parallel_tasks=2).fingerprint()
    assert "grant" not in selected.to_document()["value"]
    with pytest.raises(FrozenInstanceError):
        selected.context_id = "changed"


@pytest.mark.parametrize("raw", (b'{"a":1,"a":2}', b'{"a":1.1}', b'{"a":NaN}', b'[] trailing'))
def test_wire_parser_refuses_ambiguous_or_inexact_input(raw):
    with pytest.raises(ApplicationError):
        load_application_json(raw)


def test_request_version_paths_and_scalar_boundaries():
    original = request(directory="/external/retained")
    assert ApplicationRequest.from_document(original.to_document()) == original
    document = original.to_document() | {"version": "99.0.0"}
    with pytest.raises(ApplicationError, match="contract"):
        ApplicationRequest.from_document(document)
    with pytest.raises(ApplicationError):
        replace(context(), project_root=Path("/external/../other"))
    with pytest.raises(ApplicationError):
        request(arbitrary={"mutable": []})
    with pytest.raises(ApplicationError):
        replace(context(), maximum_parallel_tasks=True)


def test_exact_values_and_payload_bounds_preserve_source_operands():
    value = {"threshold": Decimal("0.1000000000000000000000000000000000001"),
        "identifier": 9007199254740993123456789, "unknown": None}
    result = ApiResult("inspect", OperationStatus.SUCCEEDED, value)
    decoded = load_application_json(response_bytes(result))
    assert decoded["payload"] == {"threshold": {"decimal": str(value["threshold"])},
        "identifier": {"integer": str(value["identifier"])}, "unknown": None}
    assert value["threshold"] == Decimal("0.1000000000000000000000000000000000001")
    with pytest.raises(ApplicationError, match="smaller"):
        response_bytes(result, maximum_bytes=80)
    with pytest.raises(ApplicationError, match="byte limit"):
        load_application_json(b"{}", maximum_bytes=1)


def test_cursor_is_bound_to_all_rows_context_operation_and_filter():
    selected = request(limit=1)
    rows = ({"id": "one"}, {"id": "two"}, {"id": "three"})
    first = page(rows, request=selected, identity="original", parameters={"limit": 1})
    parameters = {"limit": 1, "cursor": first["next_cursor"]}
    assert page(rows, request=selected, identity="original", parameters=parameters)["rows"] == [{"id": "two"}]
    cases = ((rows[:2]+({"id": "changed-unseen"},), selected, "original", parameters),
        (rows, replace(selected, context_id="ctx.other"), "original", parameters),
        (rows, replace(selected, operation="rc.findings"), "original", parameters),
        (rows, selected, "changed", parameters), (rows, selected, "original", parameters | {"filter": "two"}))
    for census, req, identity, selection in cases:
        with pytest.raises(ApplicationError, match="census"):
            page(census, request=req, identity=identity, parameters=selection)


def test_projection_keeps_complete_denominators_and_failed_attempts():
    result = execution_projection(execution(), request=request(), parameters={"filter": "FAILED"})
    assert result["summary"]["assigned_tasks"] == 3
    assert result["summary"]["attempt_records"] == 4
    assert result["summary"]["observed_task_statuses"] == {"SUCCEEDED": 1, "UNKNOWN": 1, "UNENTERED": 1}
    assert result["page"]["total"] == 4 and result["page"]["matching_total"] == 1
    assert result["page"]["rows"][0]["reason_code"] == "ORIGINAL_FAILURE"
    assert result["summary"]["scientific_completion"] == "DEFERRED_TO_FULL_READ"


def test_static_discovery_and_unavailable_routes_never_inspect_storage(monkeypatch):
    monkeypatch.setattr(owner, "application_storage", lambda *a, **k: pytest.fail("static/effect route opened storage"))
    result = owner.execute_application(context(), request("workflow.list", limit=1))
    assert result.succeeded and result.payload["page"]["total"] > 1
    assert load_application_json(response_bytes(result))["payload"]["page"]["returned_count"] == 1
    assert result.payload["summary"]["prerequisites_inspected"] is False
    for name, parameters in (("catalog.query", {}), ("unknown.action", {})):
        result = owner.execute_application(context(), request(name, **parameters))
        assert result.status is OperationStatus.BLOCKED
    # Effects require the reviewed package digest before any storage or owner.
    assert owner.execute_application(context(), request("recursive.run", directory="/external/run")).reason_codes == ("INVALID_FIELDS",)
    assert owner.execute_application(context(), request(name="ctx.other")).reason_codes == ("CONTEXT_MISMATCH",)


def test_each_read_reopens_current_access_and_contexts_do_not_cross(monkeypatch):
    from empirical_lawhood.api import experiment_execution_read
    observations = []
    refused = set()
    def storage(selected):
        return selected.project_root, selected.operator_profile, selected.context_id
    def access(selected, **kwargs):
        observations.append((selected.context_id, kwargs["artifact_writer"], selected.read_access_paths))
        if selected.context_id in refused:
            raise PermissionError("PRIVATE original operand and grant bytes")
        return (selected.context_id, len(observations))
    def read(**kwargs):
        assert kwargs["read_access"][0] == kwargs["artifact_writer"]
        return execution()
    monkeypatch.setattr(owner, "application_storage", storage)
    monkeypatch.setattr(owner, "application_read_access", access)
    monkeypatch.setattr(experiment_execution_read, "read_development_execution", read)
    def call(name):
        ctx = replace(context(name), operator_profile=Path("/"+name+"/profile.json"),
            read_access_paths=(Path("/"+name+"/access.json"),))
        return owner.execute_application(ctx, request(name=name, directory="/external/run"))
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert all(result.succeeded for result in pool.map(call, ("one", "two")))
    refused.add("one")
    denied = call("one")
    assert denied.status is OperationStatus.BLOCKED
    assert b"PRIVATE" not in response_bytes(denied) and denied.payload is None
    assert len(observations) == 3
    assert all(name == plane and paths == (Path("/"+name+"/access.json"),) for name, plane, paths in observations)


def test_errors_do_not_echo_protected_values_or_acquire_scientific_status():
    for error in (ValueError("secret-input"), PermissionError("secret-grant"), RuntimeError("secret-payload")):
        result = error_result("inspect", error)
        assert not result.succeeded and result.payload is None
        assert b"secret" not in response_bytes(result)
