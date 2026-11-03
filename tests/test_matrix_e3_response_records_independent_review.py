# SPDX-License-Identifier: MPL-2.0
"""Independent local joins, using disclosed producer metadata only.

The reused fixture has literal qualification metadata and a deliberately
incomplete native archive. It authenticates no scientific source or authority,
and the complete cold array reader must continue to refuse its native bytes.
"""
from empirical_lawhood.kernel.provenance import ObjectIdentity

from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_records as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_source_records as sources
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_bindings import unpack_native
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from tests.test_matrix_e3_protected_source_records import response_fixture
from tests.test_matrix_e3_response_records import (
    arguments,
    case as _producer_case,
    completed_metadata,
    forbid_native,  # noqa: F401 -- guards native, RNG and fitting entry points
    publication,
    qualification,
)

# Expose the disclosed producer fixture under its pytest name without making
# every test parameter shadow an imported Python name.
case = _producer_case


@pytest.mark.parametrize("container_kind", ("direct", "references", "historical"))
def test_profile_uses_actual_container_and_transport_alias_without_promoting_access(case, container_kind):
    if container_kind == "references":
        protocol, container = case.protocol, case.selection
    else:
        protocol = case.protocols[-1]
        group = protocol.public_source.root.independent_group_id
        panels = tuple(row for row in response_fixture(case.originals)[2] if row.independent_group_id == group)
        container = protocol if container_kind == "direct" else ScheduledResponseSelection(
            "selection.literal.independent", ObjectIdentity.from_record(case.manifest.reservation.allocation.allocation_id, case.manifest.reservation.allocation), (protocol,),
            ((group, panels),), case.selection.template_publications, None)
    if type(container) is ScheduledResponseSelection:
        container.validate_allocation(case.manifest.reservation.allocation)
    pub = publication(case, container, "independent." + container_kind,
        access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility=VisibilityCeiling.DEVELOPMENT_ONLY)
    q = qualification(container, pub, "independent." + container_kind)
    assert pub.logical.logical_artifact_id != owner._object(container).object_id
    profile = owner.project_protected_e3_response_numerics(protocol,
        provenance=container, publication=pub, qualification=q)
    profile.validate_original(protocol, provenance=container, publication=pub, qualification=q)
    assert profile.original_protocol == owner._object(protocol)
    assert profile.provenance_container == owner._object(container)
    assert profile.provenance_publication == pub
    assert tuple(getattr(profile, name).as_tuple() for name in owner.NUMERICAL_FIELDS) == tuple(
        getattr(protocol, name).as_tuple() for name in owner.NUMERICAL_FIELDS)
    assert profile.provenance_publication.logical.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    assert profile.provenance_publication.logical.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY


def test_identical_container_bytes_do_not_retarget_qualification_to_another_publication(case):
    first = publication(case, case.protocol, "independent.qualification.first")
    second = publication(case, case.protocol, "independent.qualification.second")
    q = qualification(case.protocol, first, "independent.original")
    assert first.logical.content_sha256 == second.logical.content_sha256
    assert q.materialization.object_id != second.logical.logical_artifact_id
    with pytest.raises(ValueError, match="publication or qualification"):
        owner.project_protected_e3_response_numerics(case.protocol,
            provenance=case.protocol, publication=second, qualification=q)


def test_full_native_metadata_allows_ordinary_alias_but_does_not_accept_incomplete_arrays(case):
    response, args, raw = completed_metadata(case)
    assert response.validate_source(case.native_config, **args) is case.source
    assert response.arrays.array_artifact.artifact_id != response.native[0].receipt.task_id + ".output.arrays"
    assert len(response.arrays.members) == 246
    with pytest.raises(ValueError, match="complete member census"):
        unpack_native(raw, case.protocol, case.panels)


@pytest.mark.parametrize("damage", ("sha256", "size"))
def test_native_completion_publication_must_describe_actual_completion(case, damage):
    response, args, _ = completed_metadata(case)
    event = response.native[0]
    control_id = event.receipt.task_id + ".completion"
    logical = tuple(replace(row, content_sha256="e" * 64)
        if row.logical_artifact_id == control_id and damage == "sha256" else row
        for row in event.receipt.output_logical_artifacts)
    physical = tuple(replace(row, **({"physical_sha256": "e" * 64} if damage == "sha256"
        else {"size_bytes": row.size_bytes + 1})) if row.logical_artifact_id == control_id else row
        for row in event.receipt.output_materializations)
    receipt = replace(event.receipt, output_logical_artifacts=logical, output_materializations=physical)
    with pytest.raises(ValueError):
        changed = replace(response, native=(replace(event, receipt=receipt),))
        assert changed.native[0].completion == event.completion
        changed.validate_source(case.native_config, **args)


@pytest.mark.parametrize("evidence_name", ("numerical", "witness", "frame_assessment"))
def test_error_feature_evidence_must_equal_supplied_current_causal_dependencies(case, evidence_name):
    original = getattr(case.causal, evidence_name)
    evidence = tuple(replace(ref, object_fingerprint="e" * 64) if ref == original else ref
        for ref in case.error.feature.evidence)
    assert evidence != case.error.feature.evidence
    feature = replace(case.error.feature, evidence=evidence)
    error = replace(case.error, feature=feature)
    old_error, new_error = sources.identity(case.error), sources.identity(error)
    arrays = replace(case.response.arrays,
        producers=tuple(new_error if ref == old_error else ref for ref in case.response.arrays.producers))
    changed = replace(case.response, error_forecast=new_error, arrays=arrays)
    assert feature.prefix == sources.identity(case.causal)
    with pytest.raises(ValueError):
        changed.validate_source(case.native_config, **arguments(case, error=error))
