# SPDX-License-Identifier: MPL-2.0
"""Finite loopback/process controls. The mocked engine never runs science."""

from dataclasses import replace
import http.client
import json
from pathlib import Path
import sys
import threading

import pytest

from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationError, ApplicationRequest, application_result, response_bytes
from empirical_lawhood.workbench import broker as owner
from empirical_lawhood.workbench.engine import ENGINE_SCHEMA, ENGINE_VERSION, describe_engine, invoke
from empirical_lawhood.workbench.launcher import SelectedEngine, invoke_engine, negotiate_engine


def context():
    return ApplicationContext("test", "Bounded software control", Path(sys.executable).absolute())


def request(name="read.one", operation="workflow.list"):
    return ApplicationRequest(name, "test", operation)


def test_actual_selected_engine_negotiates_and_transports_static_discovery_only():
    selected = negotiate_engine(context())
    result, body = invoke_engine(selected, request())
    assert result["status"] == "SUCCEEDED" and json.loads(body) == result
    assert result["payload"]["summary"]["prerequisites_inspected"] is False
    assert result["payload"]["page"]["total"] > 1
    assert selected.description["python_executable"] == str(Path(sys.executable).absolute())


def test_engine_change_interpreter_substitution_and_disabled_handler_refuse_before_entry(monkeypatch):
    from empirical_lawhood.api import application
    monkeypatch.setattr(application, "execute_application", lambda *a, **k: pytest.fail("engine crossed refusal"))
    body = {"schema": ENGINE_SCHEMA, "version": ENGINE_VERSION, "context": context().to_document(),
        "request": request().to_document(), "client": "browser", "expected_engine": "wrong"}
    with pytest.raises(ApplicationError, match="changed"):
        invoke(body)
    body["expected_engine"] = describe_engine()["identity_sha256"]
    body["context"] = replace(context(), python_executable=Path("/another/environment/bin/python")).to_document()
    with pytest.raises(ApplicationError, match="interpreter"):
        invoke(body)
    body["context"] = context().to_document()
    body["request"] = request(operation="recursive.run").to_document()
    with pytest.raises(ApplicationError, match="durable invocation"):
        invoke(body)


@pytest.fixture
def server(tmp_path, monkeypatch):
    calls = []
    selected = SelectedEngine(context(), "c"*64, {"operations": [{"operation_id": "workflow.list", "browser_available": True}]})
    monkeypatch.setattr(owner, "negotiate_engine", lambda selected_context: selected)
    def execute(engine, selected_request):
        calls.append((engine, selected_request))
        body = response_bytes(application_result(selected_request.operation, {"value": "one explicit read"}))
        return json.loads(body), body
    monkeypatch.setattr(owner, "invoke_engine", execute)
    service = owner.Broker((context(),), tmp_path/"session")
    server = owner.LocalServer(("127.0.0.1", 0), service)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield server, calls
    finally:
        server.shutdown(); server.server_close(); thread.join(2)


def http_request(server, *, method="POST", path="/api/execute", body=None, headers=None):
    body = json.dumps(request().to_document()).encode() if body is None else body
    base = {"Host": server.expected_host, "Origin": server.origin,
        "X-EL-Session": server.broker.session, "Content-Type": "application/json"}
    if headers:
        for key, value in headers.items():
            if value is None:
                base.pop(key, None)
            else:
                base[key] = value
    connection = http.client.HTTPConnection(*server.server_address, timeout=3)
    try:
        connection.request(method, path, body=body, headers=base)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_http_origin_session_media_limits_and_methods_refuse_without_dispatch(server):
    server, calls = server
    cases = (({"Host": "attacker.example"}, 403), ({"Origin": "https://attacker.example"}, 403),
        ({"Origin": None}, 403), ({"X-EL-Session": "wrong"}, 403),
        ({"Content-Type": "text/plain"}, 415), ({"Transfer-Encoding": "chunked"}, 415),
        ({"Content-Length": str(256*1024+1)}, 413), ({"Sec-Fetch-Site": "cross-site"}, 403))
    for headers, expected in cases:
        assert http_request(server, headers=headers)[0] == expected
    assert http_request(server, method="PUT")[0] == 405
    assert http_request(server, path="/api/execute?session=secret")[0] == 404
    assert http_request(server, body=b'{"a":1,"a":2}')[0] == 400
    assert calls == []


def test_one_dispatch_has_no_store_headers_and_duplicate_cannot_repeat(server):
    server, calls = server
    status, headers, body = http_request(server)
    assert status == 200 and len(calls) == 1
    assert headers["Cache-Control"] == "no-store"
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert json.loads(body)["payload"]["value"] == "one explicit read"
    status, _, body = http_request(server)
    assert status == 409 and len(calls) == 1
    assert json.loads(body)["reason_codes"] == ["REQUEST_ALREADY_OBSERVED"]
    for path in server.broker.output_directory.glob("*.json"):
        raw = path.read_bytes()
        assert server.broker.session.encode() not in raw and b"one explicit read" not in raw
    returned = list(server.broker.output_directory.glob("*.return.json"))
    assert len(returned) == 1 and json.loads(returned[0].read_text())["state"] == "RETURNED"


def test_configuration_requires_session_and_busy_context_is_not_reentered(server):
    server, calls = server
    assert http_request(server, method="GET", path="/api/context", headers={"X-EL-Session": None})[0] == 403
    assert http_request(server, method="GET", path="/api/context")[0] == 200
    with server.broker.locks["test"]:
        status, _, body = http_request(server)
    assert status == 409 and json.loads(body)["reason_codes"] == ["CONTEXT_BUSY"]
    assert calls == []
