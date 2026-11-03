# SPDX-License-Identifier: MPL-2.0
"""Retained publication replay from actual verified inputs; no native work."""
from dataclasses import replace
from decimal import Decimal

import pytest

from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.time import AvailabilitySpec, CausalPhase
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from tests.test_matrix_factor_confirmation_eligibility import _matrix_plane


def test_publication_replay_accepts_verified_input_and_retains_full_manifest_guard(tmp_path):
    plane = _matrix_plane(tmp_path / "selected")
    record = AvailabilitySpec("clock.replay-control", CausalPhase.PREPARATION,
        OutcomeAccess.OUTCOME_BLIND, Decimal(1))
    original = plane.write(ArtifactWriteRequest("availability.replay-control", "inputs/availability.json",
        record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "replay-control", "inputs",
        record.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    manifest = plane.read_manifest(original.materialization.relative_path)
    verified = VerifiedArtifactInput(manifest.logical, manifest.materialization)
    replayed = _publication_from_manifest(plane, verified)
    assert (replayed.logical, replayed.materialization) == (original.logical, original.materialization)
    assert replayed.created is False
    assert _publication_from_manifest(plane, manifest) == replayed
    assert manifest.publication is not None
    for changed in (replace(verified, logical=replace(verified.logical, content_sha256="e" * 64)),
            replace(verified, materialization=replace(verified.materialization, physical_sha256="e" * 64)),
            replace(manifest, publication=None)):
        with pytest.raises(PermissionError, match="manifest changed"):
            _publication_from_manifest(plane, changed)
    assert plane.read_manifest(original.materialization.relative_path) == manifest
