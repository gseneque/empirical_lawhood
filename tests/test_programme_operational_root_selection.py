# SPDX-License-Identifier: MPL-2.0
"""Explicit retained logical IDs retain exact selected physical policy."""
from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.api.composition import create_api
from empirical_lawhood.api.integration_handoffs import integration_artifact_profile_validators
from empirical_lawhood.runtime.operator_profile import resolve_external_root_contract
from tests.test_programme_catalog_selection import CATALOG, ROOT, operator  # noqa: F401


def selected(profile):
    expected = resolve_external_root_contract(profile, repo_root=ROOT, home_root=Path.home())
    return replace(expected, storage_root_id="synthetic.original.logical-root",
        logical_name="Current operational access to retained conformance evidence")


@pytest.mark.parametrize("field,value", (
    ("canonical_path", "/different-artifact-root"), ("required_mount_path", "/different-mount"),
    ("minimum_free_bytes", 2), ("expected_mount_source", "/dev/different"),
    ("expected_volume_identity", "different-volume"), ("allowed_filesystem_types", ("xfs",)),
    ("mount_contract_schema", "empirical-lawhood/other-profile"),
))
def test_selected_root_cannot_change_physical_policy(operator, field, value):  # noqa: F811
    with pytest.raises(ValueError, match="physical policy"):
        resolve_external_root_contract(operator, repo_root=ROOT, home_root=Path.home(),
            selected_contract=replace(selected(operator), **{field: value}))


@pytest.mark.parametrize('mode', ('reduced', 'strict'))
def test_actual_api_uses_declared_original_id_and_exact_installed_matrix_codecs(operator, mode):  # noqa: F811
    profile = replace(operator, maximum_parallel_tasks=4)
    contract = selected(profile)
    validators = integration_artifact_profile_validators()
    api = create_api(repo_root=ROOT, operator_storage_profile=profile,
        operator_artifact_root_contract=contract, artifact_profile_validators=validators,
        catalog_relative_path=CATALOG, maximum_parallel_tasks=profile.maximum_parallel_tasks,
        artifact_verification=mode)
    service = api._execution_service
    assert service.artifact_plane.root.contract == contract
    assert service.artifact_plane.validators is validators
    assert service.artifact_plane.artifact_verification == mode
    assert service.artifact_plane.with_semantic_validation_registry(
        service.artifact_plane.semantic_validations).artifact_verification == mode
    assert service.maximum_parallel_tasks == profile.maximum_parallel_tasks
    assert api.check_catalog().succeeded and not api.check_catalog().payload.present
    assert not service.catalog_path.exists()


def test_explicit_root_requires_profile_instead_of_injected_service():
    with pytest.raises(ValueError, match="operator profile"):
        create_api(repo_root=ROOT, operator_artifact_root_contract=object())


@pytest.mark.parametrize('mode', ('reduced', 'strict'))
def test_cli_storage_owner_uses_configured_contract_and_installed_codecs(tmp_path, operator, monkeypatch, mode):  # noqa: F811
    from empirical_lawhood.api.configuration import validate_configuration
    from empirical_lawhood.cli import integrations, platform

    contract = selected(operator)
    profile_path = tmp_path / "operator.json"
    contract_path = tmp_path / "operational-root.json"
    profile_path.write_bytes(operator.canonical_bytes())
    contract_path.write_bytes(contract.canonical_bytes())
    report = validate_configuration(contract_path, consumer="operator-artifact-root-access")
    assert report["status"] == "VALIDATED" and report["validation_scope"] == "typed values"
    assert not report["authority_granted"]
    monkeypatch.setattr(platform, "CLI_PROJECT_ROOT", ROOT)
    monkeypatch.setattr(platform, "CLI_OPERATOR_PROFILE", profile_path)
    monkeypatch.setattr(platform, "CLI_ARTIFACT_ROOT_CONTRACT", contract_path)
    monkeypatch.setattr(platform, 'CLI_ARTIFACT_VERIFICATION', mode)
    source, profile, plane = integrations._storage()
    assert source == ROOT and profile == operator and plane.root.contract == contract
    assert plane.artifact_verification == mode
    expected = integration_artifact_profile_validators()
    assert plane.validators.binary_codecs == expected.binary_codecs
    for codec in expected.binary_codecs:
        assert plane.validators.generic_validation(profile=codec.profile, payload_schema=codec.payload_schema) == (
            expected.generic_validation(profile=codec.profile, payload_schema=codec.payload_schema))


def test_global_contract_option_is_discoverable_without_storage_contact(monkeypatch):
    from empirical_lawhood.infrastructure.artifacts import GuardedExternalRoot
    from empirical_lawhood.cli.app import app
    from typer.testing import CliRunner

    def no_probe(*_arguments, **_options):
        pytest.fail("help inspected storage")
    monkeypatch.setattr(GuardedExternalRoot, "verify", no_probe)
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0 and "--artifact-root-contract" in result.stdout
