# SPDX-License-Identifier: MPL-2.0
"""Client parity and retained origin diagnostics without protected data leaks."""

from dataclasses import replace
import json
from pathlib import Path
import sys

from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest, error_result, response_bytes
from empirical_lawhood.api.application_invocation import run_application_invocation
from empirical_lawhood.workbench.engine import ENGINE_SCHEMA, ENGINE_VERSION, describe_engine, invoke


def _selection():
    context = ApplicationContext("diagnostic.fixture", "Diagnostic fixture", Path(sys.executable).absolute())
    request = ApplicationRequest("authored.question.one", context.context_id, "workflow.list", (("not_allowed", True),))
    return context, request


def test_cli_and_workbench_receive_same_authored_contract_explanation():
    context, request = _selection()
    document = {"schema": ENGINE_SCHEMA, "version": ENGINE_VERSION,
        "context": context.to_document(), "request": request.to_document(),
        "expected_engine": describe_engine()["identity_sha256"]}
    terminal = invoke({**document, "client": "cli"})
    browser = invoke({**document, "client": "browser"})
    assert response_bytes(terminal) == response_bytes(browser)
    diagnostic = terminal.errors[0].diagnostic
    assert diagnostic.authored_object == request.request_id
    assert diagnostic.operation == request.operation
    assert diagnostic.contract == "INVALID_FIELDS"
    assert diagnostic.owner == "api" and diagnostic.remediation == "investigation"
    assert "application_contracts:exact_mapping:" in diagnostic.implementation
    assert "allowed:" in diagnostic.expected
    assert diagnostic.trace


def test_durable_failure_retains_same_diagnostic_and_attempt_ancestry(tmp_path):
    context, request = _selection()
    directory = tmp_path / "selected-invocation"
    directory.mkdir()
    result, body = run_application_invocation(context, request, directory=directory, handle="fixture")
    diagnostic = result.errors[0].diagnostic
    retained = Path(diagnostic.evidence)
    assert retained == directory / "attempt/contract-diagnostic.json"
    assert json.loads(retained.read_bytes()) == json.loads(body)["errors"][0]["diagnostic"]
    attempt = json.loads((directory / "attempt/invocation.json").read_bytes())
    assert attempt["application_handle"] == "fixture"
    assert attempt["contract_diagnostic"]["path"] == retained.name
    assert attempt["state"] == "FAILED" and attempt["native_contact"] == "none"


def test_diagnostic_never_copies_exception_payload_or_frame_locals():
    secret = "PRIVATE_SEALED_INPUT_DO_NOT_DISCLOSE"
    try:
        raise ValueError(secret)
    except ValueError as error:
        result = error_result("fixture.contract", error, authored_object="question.one")
    assert secret.encode() not in response_bytes(result)
    assert result.errors[0].diagnostic.expected == "The declared contract must be satisfied."
    assert "not disclosed" in result.errors[0].diagnostic.actual


def test_context_failure_explains_request_without_opening_scientific_storage():
    context, request = _selection()
    result = execute_application(replace(context, context_id="other.context"), request)
    assert result.errors[0].diagnostic.authored_object == request.request_id
    assert result.errors[0].diagnostic.evidence is None


def test_actual_terminal_wrapper_emits_identical_structured_error(monkeypatch):
    import typer
    import uuid
    from typer.testing import CliRunner
    from empirical_lawhood.cli import application as terminal

    context, request = _selection()
    monkeypatch.setattr(terminal, "application_context_from_cli", lambda: context)
    monkeypatch.setattr(uuid, "uuid4", lambda: request.request_id)
    command = typer.Typer()

    @command.command()
    def selected():
        terminal.invoke_selected_application(request.operation, dict(request.parameters), root=None)

    result = CliRunner().invoke(command, [])
    expected = execute_application(context, request)
    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr.encode() == response_bytes(expected)
    assert json.loads(result.stderr)["errors"][0]["diagnostic"]["contract"] == "INVALID_FIELDS"


def test_actual_recursive_result_cli_preserves_diagnostic_fields(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from empirical_lawhood.cli.app import app
    from empirical_lawhood.cli import application as terminal

    context, _ = _selection()
    monkeypatch.setattr(terminal, "application_context_from_cli", lambda: context)
    result = CliRunner().invoke(app, ["--no-progress", "campaign", "recursive-development-result", "--authoring-dir", str(tmp_path)])
    assert result.exit_code == 2
    diagnostic = json.loads(result.stderr)["errors"][0]["diagnostic"]
    assert diagnostic["authored_object"] == "cli.recursive-result"
    assert diagnostic["operation"] == "recursive.result"
    assert diagnostic["owner"] in {"api", "storage"}
    assert diagnostic["implementation"] and diagnostic["expected"] and diagnostic["actual"]
