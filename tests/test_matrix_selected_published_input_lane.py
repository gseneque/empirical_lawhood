# SPDX-License-Identifier: MPL-2.0
"""Actual local control custody; these publications provide no issue authority."""

import pytest

from empirical_lawhood.api import current_task_custody
from empirical_lawhood.api.matrix_selected_runtime import _published_input
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.plans import ExternalInputSpec
from tests.runtime_platform.test_recursive_compiler import Config
from tests.test_recursive_public_service import _plane


@pytest.mark.parametrize("actual_access,actual_visibility,selected_access,selected_visibility,allowed", (
    (Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, None, None, True),
    (Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, Access.OUTCOME_BLIND, None, True),
    (Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, None, Visibility.PROSPECTIVE, True),
    (Access.EVALUATION_SEALED, Visibility.PROSPECTIVE, None, None, False),
    (Access.DEVELOPMENT_VISIBLE, Visibility.DEVELOPMENT_ONLY, None, None, False),
    (Access.EVALUATION_SEALED, Visibility.PROSPECTIVE, Access.EVALUATION_SEALED, Visibility.PROSPECTIVE, True),
    (Access.DEVELOPMENT_VISIBLE, Visibility.DEVELOPMENT_ONLY,
        Access.DEVELOPMENT_VISIBLE, Visibility.DEVELOPMENT_ONLY, True),
    (Access.DEVELOPMENT_VISIBLE, Visibility.DEVELOPMENT_ONLY, Access.DEVELOPMENT_VISIBLE, None, False),
    (Access.EVALUATION_SEALED, Visibility.PROSPECTIVE, None, Visibility.PROSPECTIVE, False),
    (Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, Access.EVALUATION_SEALED, Visibility.PROSPECTIVE, False),
))
def test_actual_published_control_preserves_blind_legacy_defaults_and_exact_explicit_lanes(
        tmp_path, monkeypatch, actual_access, actual_visibility, selected_access, selected_visibility, allowed):
    writer = _plane(tmp_path / "plane")
    run_id, logical_id = "run.disclosed.control-lane", "input.disclosed.control-lane"
    relative, scope_id, scope_root = provider_input_location(writer, run_id, logical_id)
    record = Config("config.disclosed.control-lane", 3)
    raw = record.canonical_bytes()
    writer.write(ArtifactWriteRequest(logical_id, relative, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", scope_id, scope_root, raw, actual_visibility, (), actual_access))
    spec = ExternalInputSpec("selected.control", logical_id, record.fingerprint(), record.SCHEMA,
        "application/json", len(raw), selected_visibility, selected_access, None)
    reads = []
    original = current_task_custody.read_bounded_bytes
    def observe(path, **kwargs):
        reads.append(path)
        return original(path, **kwargs)
    monkeypatch.setattr(current_task_custody, "read_bounded_bytes", observe)
    if allowed:
        assert _published_input(writer, run_id, spec, Config) == record
        assert reads == [writer.root.resolve(relative, for_write=False)]
    else:
        with pytest.raises(PermissionError, match="exact issued access|plan-selected persisted control"):
            _published_input(writer, run_id, spec, Config)
        assert reads == []
