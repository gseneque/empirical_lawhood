"""Compact discovery preserves selection facts and complete JSON inspection."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api import CapabilityListRequest, EmpiricalLawhoodApi, create_inspection_api
from empirical_lawhood.cli import platform
from empirical_lawhood.cli.app import app


ROOT = Path(__file__).resolve().parents[1]


def test_deferred_factories_are_selected_once_and_bound_to_the_displayed_catalog(monkeypatch):
    from empirical_lawhood.api import inspection

    load_bindings = inspection.load_installed_executable_bindings
    load_factories = inspection.load_installed_executable_factories
    bindings, providers = [], []

    def select_bindings():
        bindings.append(load_bindings())
        return bindings[-1]

    def select_factories():
        providers.append(load_factories())
        return providers[-1]

    monkeypatch.setattr(inspection, "load_installed_executable_bindings", select_bindings)
    monkeypatch.setattr(inspection, "load_installed_executable_factories", select_factories)
    api = create_inspection_api(repo_root=ROOT)
    assert api.doctor().payload is not None and not bindings and not providers
    request = CapabilityListRequest(limit=5)
    first = api.list_capabilities(request)
    assert first.payload is not None and api.list_capabilities(request) == first
    assert len(bindings) == 1 and not providers
    assert api._executable_factory_registry.aggregate is bindings[0]
    assert api._executable_factory_registry is providers[0] and len(providers) == 1

    foreign = replace(inspection.GENERATED_EXTENSION_BUNDLE_AGGREGATE, aggregate_id="discovery.foreign")
    altered = EmpiricalLawhoodApi(repo_root=ROOT, external_root=None, extension_bundle_aggregate=foreign,
                                  executable_binding_loader=lambda: bindings[0])
    refused = altered.list_capabilities(request)
    assert refused.payload is None and refused.reason_codes == ("CAPABILITY_QUERY_INVALID",)
    assert "executable and discovery aggregates differ" in refused.errors[0].message

    alternate = replace(bindings[0], aggregate_id="bindings.alternate")
    mismatched = EmpiricalLawhoodApi(repo_root=ROOT, external_root=None,
        extension_bundle_aggregate=inspection.GENERATED_EXTENSION_BUNDLE_AGGREGATE,
        executable_binding_loader=lambda: alternate, executable_factory_loader=lambda: providers[0])
    with pytest.raises(ValueError, match="factory registry differs"):
        _ = mismatched._executable_factory_registry


@pytest.mark.parametrize("installed", (False, True))
def test_compact_discovery_preserves_page_selection_and_inspection(
    monkeypatch, installed
):
    inspection = create_inspection_api(repo_root=ROOT)
    api = (
        inspection
        if installed
        else EmpiricalLawhoodApi(
            repo_root=ROOT,
            external_root=None,
            extension_bundle_aggregate=inspection._extension_bundle_aggregate,
        )
    )
    monkeypatch.setattr(platform, "API_FACTORY", lambda: api)
    page = api.list_capabilities(CapabilityListRequest(limit=5)).payload
    runner = CliRunner()
    first = runner.invoke(app, ["capability", "list", "--limit", "5"])
    assert first.exit_code == 0, first.output
    assert len(first.stdout.splitlines()) <= 20
    assert len(first.stdout.encode()) <= 24 * 1024
    assert page.next_cursor in first.stdout
    assert "neither readiness nor authority" in first.stdout
    for registration in page.registrations:
        assert registration.manifest.registry_id in first.stdout
    assert (
        "Binding: installed" if installed else "availability not composed"
    ) in first.stdout

    second = runner.invoke(
        app,
        [
            "capability",
            "list",
            "--limit",
            "5",
            "--cursor",
            page.next_cursor,
            "--format",
            "json",
        ],
    )
    assert second.exit_code == 0, second.output
    following = json.loads(second.stdout)["payload"]["value"]
    assert following["returned_count"] == 5
    first_keys = {value.manifest.capability_key for value in page.registrations}
    assert not first_keys.intersection(
        value["value"]["manifest"]["value"]["capability_key"]
        for value in following["registrations"]
    )
    manifest = page.registrations[0].manifest
    arguments = [
        "capability",
        "show",
        manifest.capability_key,
        "--version",
        manifest.capability_version,
    ]
    shown = runner.invoke(app, arguments)
    complete = runner.invoke(app, [*arguments, "--format", "json"])
    assert shown.exit_code == complete.exit_code == 0
    assert manifest.registry_id in shown.stdout
    assert manifest.config_schema in shown.stdout
    assert "Permissions:" in shown.stdout and "Evidence limit:" in shown.stdout
    assert (
        json.loads(complete.stdout)
        == api.show_capability(
            platform.CapabilityShowRequest(
                manifest.capability_key, manifest.capability_version
            )
        ).to_mapping()
    )


def test_compact_discovery_keeps_refusal_status_and_machine_diagnostics(monkeypatch):
    api = create_inspection_api(repo_root=ROOT)
    monkeypatch.setattr(platform, "API_FACTORY", lambda: api)
    arguments = ["--no-progress", "capability", "show", "missing.capability", "--version", "1.0.0"]
    runner = CliRunner()
    text = runner.invoke(app, arguments)
    machine = runner.invoke(app, [*arguments, "--format", "json"])
    assert text.exit_code == machine.exit_code == 7
    assert text.stdout == machine.stdout == ""
    assert "CAPABILITY_NOT_FOUND" in text.stderr
    assert json.loads(machine.stderr)["reason_codes"] == ["CAPABILITY_NOT_FOUND"]
