# SPDX-License-Identifier: MPL-2.0
"""Actual NPZ access aliases; disclosed records assert no source/reveal authority."""
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import expected_members
from empirical_lawhood.adapters.methods.matrix_scheduled_history.continuation import ScheduledFullArrays
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from empirical_lawhood.api import derived_array_access as owner
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.test_recursive_public_service import _plane


@pytest.fixture
def full_array_access(tmp_path):
    writer = _plane(tmp_path / "full-array-access")
    root, _ = _fixture()
    # Full complete retained member geometry with literal software values.
    values = {name: np.zeros(shape, dtype=dtype)
        for name, (dtype, shape) in expected_members(SimpleNamespace(total_ticks=2)).items()}
    raw, members = encode_matrix_arrays(values)
    artifact = ArtifactIdentity("array.disclosed.sealed-full-history", "disclosed-software-values", MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), "application/x-npz", len(raw))
    source = ObjectIdentity("source.disclosed.full-history", ScheduledSource.SCHEMA, ScheduledSource.VERSION, "a" * 64)
    arrays = ScheduledFullArrays("operand.disclosed.full-history", source, artifact, members, (source,),
        OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE)
    external = RecursiveExternalInput("source.disclosed.revealed-analysis", "alias.disclosed.revealed-analysis", MATRIX_ARRAY_SCHEMA,
        "application/x-npz", len(raw), OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, artifact.sha256)
    publication = writer.write(ArtifactWriteRequest(external.logical_artifact_id, "full-history/revealed-analysis.npz", MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, external.media_type, "full-array.disclosed-publication", "full-history", raw,
        external.visibility_ceiling, (), external.outcome_access))
    observation = ObjectIdentity("measurement.disclosed.full-history", "empirical-lawhood/testing/full-factor-measurement", "1.0.0", "b" * 64)
    return writer, root, arrays, external, publication, observation, values


def test_actual_full_array_owner_keeps_original_sealed_metadata_and_exact_alias_bytes(full_array_access):
    writer, root, arrays, external, publication, observation, _ = full_array_access
    before = arrays.canonical_bytes()
    config, qualification = owner.derive_matrix_array_access(writer=writer, publication=publication, arrays=arrays,
        external=external, root=root, observation_operator=observation)
    owner.validate_derived_matrix_array_access(arrays=arrays, external=external, root=root,
        observation_operator=observation, config=config, qualification=qualification)
    assert arrays.canonical_bytes() == before and type(arrays) is ScheduledFullArrays
    assert arrays.outcome_access is OutcomeAccess.EVALUATION_SEALED
    assert arrays.visibility_ceiling is VisibilityCeiling.PROSPECTIVE
    assert qualification.materialization.object_id == external.logical_artifact_id != arrays.array_artifact.artifact_id
    assert qualification.content_sha256 == arrays.array_artifact.sha256
    assert qualification.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    assert qualification.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
    # This access helper does not create original issue/reveal/source authority.
    assert qualification.observation_operator == observation


@pytest.mark.parametrize("damage", ("member", "shape", "values"))
def test_full_array_alias_refuses_republished_bytes_that_change_original_members(full_array_access, damage):
    writer, root, arrays, external, _, observation, original = full_array_access
    values = {name: value.copy() for name, value in original.items()}
    if damage == "member": values["undeclared"] = np.zeros((1,), dtype="<f8")
    elif damage == "shape": values["primary_positions"] = np.zeros((2, 2, 3, 4, 4), dtype="<c16")
    else: values["primary_positions"].flat[0] = 1
    raw, _ = encode_matrix_arrays(values)
    artifact = replace(arrays.array_artifact, sha256=sha256(raw).hexdigest(), size_bytes=len(raw))
    changed = replace(arrays, array_artifact=artifact)  # Original complete members remain pinned.
    external = replace(external, expected_content_sha256=artifact.sha256, maximum_size_bytes=artifact.size_bytes)
    publication = writer.write(ArtifactWriteRequest(external.logical_artifact_id + "." + damage,
        "full-history/changed-" + damage + ".npz", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ,
        external.media_type, "full-array.disclosed-change", "full-history", raw,
        external.visibility_ceiling, (), external.outcome_access))
    external = replace(external, logical_artifact_id=publication.logical.logical_artifact_id)
    with pytest.raises(ValueError, match="members|axes|values|census"):
        owner.derive_matrix_array_access(writer=writer, publication=publication, arrays=changed,
            external=external, root=root, observation_operator=observation)
