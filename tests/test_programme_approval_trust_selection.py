# SPDX-License-Identifier: MPL-2.0
"""Explicit existing checker trust at programme composition; software only.

Only the existing deterministic test signer is used. A valid checker signature
tests registry selection, not programme approval, execution, reveal or scientific
qualification. Full original-publication CLI replay remains a separate gate.
"""

from decimal import Decimal
from pathlib import Path

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.cli.app import app
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.planning.approval import ApprovalCheckerRegistry, AttestationResult, issue_approval_gate_attestation
from tests.approval_support import deterministic_approval_signer
from tests.runtime_platform.test_study_approval import _checker_registrations
from tests.test_programme_catalog_selection import (
    CATALOG, ROOT, _cli_arguments, _cli_fixture, _service, _source_catalog_census,
    operator, prospective_selection,  # noqa: F401
)


def _trust(profile):
    registrations = _checker_registrations(("clean-implementation",))
    registry = ApprovalCheckerRegistry("synthetic.programme.existing-checkers", registrations)
    directory = Path(profile.external_root_locator) / "private-checker-trust"
    directory.mkdir(mode=0o700)
    path = directory / "existing-checkers.json"
    path.write_bytes(registry.canonical_bytes())
    path.chmod(0o600)
    registration, = registrations
    at = "2026-10-07T00:00:00Z"
    attestation = issue_approval_gate_attestation(registration=registration,
        signer=deterministic_approval_signer(registration.gate_id),
        attestation_id="synthetic.programme.existing-attestation",
        authorization_id="synthetic.programme.unissued-authorization",
        subject=ObjectIdentity("synthetic.programme.fixture-subject",
            "empirical-lawhood/testing/unissued-subject", "1.0.0", "a" * 64),
        result=AttestationResult.PASSED, checked_at_utc=at, issued_at_utc=at,
        information_cutoff=InformationCutoff("synthetic.programme.cutoff", "synthetic.programme.clock",
            CausalPhase.PREPARATION, Decimal("0")))
    return path, registry, attestation


@pytest.mark.parametrize("lifecycle", ("run", "read", "recover"))
def test_actual_programme_api_requires_selected_existing_checker_trust(
        prospective_selection, operator, lifecycle):  # noqa: F811
    selection = prospective_selection
    path, registry, attestation = _trust(operator)
    before = path.read_bytes()
    recovery_options = {"recovery_run_id": "run.synthetic.absent"} if lifecycle == "recover" else {}
    default = _service(selection, operator, catalog_relative_path=CATALOG)
    _, untrusted = default._prospective_context(selection.directory, lifecycle=lifecycle, **recovery_options)
    with pytest.raises(ValueError, match="unregistered approval gate"):
        untrusted._approval_service._checker_registry.validate(attestation)
    selected = _service(selection, operator, catalog_relative_path=CATALOG, approval_checker_trust_path=path)
    _, api = selected._prospective_context(selection.directory, lifecycle=lifecycle, **recovery_options)
    assert api._approval_service._checker_registry == registry
    api._approval_service._checker_registry.validate(attestation)
    assert path.read_bytes() == before
    assert not api._execution_service.catalog_path.exists()


def test_explicit_missing_trust_never_silently_uses_empty_registry(prospective_selection, operator):  # noqa: F811
    selection = prospective_selection
    directory = Path(operator.external_root_locator) / "private-checker-trust"
    directory.mkdir(mode=0o700)
    service = _service(selection, operator, catalog_relative_path=CATALOG,
        approval_checker_trust_path=directory / "absent-trust.json")
    with pytest.raises(FileNotFoundError):
        service._prospective_context(selection.directory, lifecycle="read")
    assert list(directory.iterdir()) == []


def test_optional_trust_preserves_legacy_composition_keyword_set(prospective_selection, operator, monkeypatch):  # noqa: F811
    from empirical_lawhood.api import composition

    options = []
    actual = composition.create_api

    def compose(**arguments):
        options.append(arguments)
        return actual(**arguments)

    monkeypatch.setattr(composition, "create_api", compose)
    _service(prospective_selection, operator)._prospective_context(prospective_selection.directory, lifecycle="read")
    assert "approval_checker_trust_path" not in options[-1]


def test_trust_and_injected_factory_refuse_before_loading_or_callback():
    def forbidden(**_arguments):
        pytest.fail("conflicting checker trust entered an injected owner")

    with pytest.raises(ValueError, match="approval_checker_trust_path.*prospective_api_factory"):
        ExperimentProgrammeService(Path("/unused"), object(), object(), forbidden, forbidden,
            approval_checker_trust_path=Path("/unused/checkers.json"))


@pytest.mark.parametrize("lifecycle", ("run", "read", "recover"))
def test_actual_cli_forwards_existing_trust_and_refuses_wrong_owner_permissions(
        prospective_selection, operator, monkeypatch, lifecycle):  # noqa: F811
    selection = prospective_selection
    _cli_fixture(monkeypatch, selection, operator)
    path, _, _ = _trust(operator)
    path.chmod(0o644)
    before = _source_catalog_census(ROOT)
    result = CliRunner().invoke(app, ["--catalog-relative-path", CATALOG,
        "--approval-checker-trust", str(path), "campaign", "experiment-" + lifecycle,
        "--authoring-dir", str(selection.directory), *_cli_arguments(selection, operator, lifecycle)])
    assert result.exit_code == 2, result.output
    assert "bounded owner-only 0600 file" in result.output
    assert _source_catalog_census(ROOT) == before
    assert list((Path(operator.external_root_locator) / "scratch").iterdir()) == []
