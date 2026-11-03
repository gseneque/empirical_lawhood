# SPDX-License-Identifier: MPL-2.0
"""Actual published metadata access, separate from any scientific source warrant."""
from dataclasses import replace

import pytest

from empirical_lawhood.api import derived_metadata_access as owner
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.test_matrix_source_evidence import source_case  # noqa: F401


@pytest.fixture
def metadata(tmp_path, source_case):  # noqa: F811
    writer, _ = _publication(tmp_path, count=1)
    root, _ = _fixture()
    profile = replace(source_case[0].pipeline_config.profile, evidence_world_id=root.system.world.world_id)
    record = ObjectIdentity("derived.metadata.subject", ObjectIdentity.SCHEMA, "1.0.0", "c" * 64)
    publication = writer.write(ArtifactWriteRequest("derived.metadata.actual", "derived/metadata.json", record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "derived.metadata", "derived", record.canonical_bytes(),
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    external = RecursiveExternalInput("source.derived.metadata", "derived.metadata.actual", record.SCHEMA,
        "application/json", len(record.canonical_bytes()), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE,
        record.fingerprint())
    return writer, root, profile, record, publication, external


@pytest.mark.parametrize("role, expected", (("SOURCE", "OBSERVATION_STREAM"), ("QUALIFICATION", "CALIBRATION")))
def test_new_current_metadata_access_reads_actual_publication_then_cold_replays_every_semantic_field(metadata, role, expected):
    writer, root, profile, record, publication, external = metadata
    external = replace(external, scientific_role=role)
    config, qualification = owner.derive_canonical_metadata_access(writer=writer, publication=publication, record=record,
        external=external, root=root, source_profile=profile)
    owner.validate_derived_metadata_access(external=external, root=root, source_profile=profile,
        version=record.VERSION, config=config, qualification=qualification)
    from empirical_lawhood.planning.study_authoring import SourceMaterializationRole
    assert config.role is SourceMaterializationRole(expected)
    assert qualification.materialization.object_fingerprint == record.fingerprint()
    assert qualification.materialization.object_id == external.logical_artifact_id
    assert qualification.clock_ids == tuple(value.clock_id for value in root.system.clocks)
    assert qualification.numerical_view_ids == tuple(value.view_id for value in root.system.numerical_views)
    assert qualification.observation_operator == profile.observation_operator
    # No ScientificSourceQualificationResult, issue, grant or reveal is emitted.
    assert qualification.SCHEMA.endswith("/materialization-qualification-receipt")
    with pytest.raises(ValueError, match="exact bytes"):
        owner.validate_derived_metadata_access(external=external, root=root, source_profile=profile,
            version=record.VERSION, config=config, qualification=replace(qualification, content_sha256="d" * 64))


def test_changed_actual_metadata_bytes_cannot_reuse_a_prior_access_receipt(metadata):
    writer, root, profile, record, publication, external = metadata
    path = writer.root.resolve(publication.materialization.relative_path, for_write=False)
    path.write_bytes(replace(record, object_id="derived.metadata.changed").canonical_bytes())
    with pytest.raises((ValueError, RuntimeError, ArtifactIdentityConflict)):
        owner.derive_canonical_metadata_access(writer=writer, publication=publication, record=record,
            external=external, root=root, source_profile=profile)


def test_metadata_access_needs_no_pipeline_for_an_actual_selected_observation(metadata):
    writer, root, profile, record, publication, external = metadata
    legacy = owner.derive_canonical_metadata_access(writer=writer, publication=publication, record=record,
        external=external, root=root, source_profile=profile)
    current = owner.derive_canonical_metadata_access(writer=writer, publication=publication, record=record,
        external=external, root=root, observation_operator=profile.observation_operator)
    assert tuple(value.canonical_bytes() for value in current) == tuple(value.canonical_bytes() for value in legacy)
    config, qualification = current
    owner.validate_derived_metadata_access(external=external, root=root,
        observation_operator=profile.observation_operator, version=record.VERSION,
        config=config, qualification=qualification)
    with pytest.raises(ValueError, match="semantic scope"):
        owner.validate_derived_metadata_access(external=external, root=root,
            observation_operator=replace(profile.observation_operator, object_fingerprint="d" * 64),
            version=record.VERSION, config=config, qualification=qualification)
    path = writer.root.resolve(publication.materialization.relative_path, for_write=False)
    path.write_bytes(replace(record, object_id="derived.metadata.changed-direct").canonical_bytes())
    with pytest.raises((ValueError, RuntimeError, ArtifactIdentityConflict)):
        owner.derive_canonical_metadata_access(writer=writer, publication=publication, record=record,
            external=external, root=root, observation_operator=profile.observation_operator)


@pytest.mark.parametrize("scope", ("absent", "untyped", "ambiguous"))
def test_metadata_access_requires_one_exact_observation_context_before_io(metadata, scope):
    _, root, profile, record, publication, external = metadata
    selected = {} if scope == "absent" else {"observation_operator": object()}
    if scope == "ambiguous":
        selected = {"source_profile": profile, "observation_operator": profile.observation_operator}
    class Forbidden:
        def __getattr__(self, name):
            pytest.fail("refused metadata context contacted writer: " + name)
    with pytest.raises(TypeError, match="observation"):
        owner.derive_canonical_metadata_access(writer=Forbidden(), publication=publication, record=record,
            external=external, root=root, **selected)


@pytest.mark.parametrize("change", ("world", "outcome", "fingerprint", "logical-alias"))
def test_metadata_access_refuses_reinterpretation_before_any_writer_contact(metadata, change):
    _, root, profile, record, publication, external = metadata
    if change == "world":
        profile = replace(profile, evidence_world_id="world.different")
    elif change == "outcome":
        external = replace(external, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    elif change == "logical-alias":
        external = replace(external, logical_artifact_id="derived.metadata.identical-bytes-other-source")
    else:
        external = replace(external, expected_content_sha256="e" * 64)
    class Forbidden:
        def __getattr__(self, name):
            pytest.fail("refused metadata selection contacted writer: " + name)
    with pytest.raises(ValueError):
        owner.derive_canonical_metadata_access(writer=Forbidden(), publication=publication, record=record,
            external=external, root=root, source_profile=profile)


def test_published_retained_metadata_passes_actual_sealed_history_source_guard(metadata):
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import _source_projection
    from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
    from empirical_lawhood.planning.study_authoring import SourceMaterializationRole
    from empirical_lawhood.runtime.candidate_compiler import (
        CandidateGraphExternalInput, ContentIdentityPolicy, ScientificInputRole, _source_diagnostics,
    )
    from empirical_lawhood.runtime.capabilities import CapabilityPermission

    writer, root, profile, record, _, external = metadata
    publication = writer.write(ArtifactWriteRequest("derived.metadata.retained", "derived/history.json", record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "derived.history", "derived", record.canonical_bytes(),
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.EVALUATION_SEALED))
    external = replace(external, logical_artifact_id=publication.logical.logical_artifact_id,
        scientific_role="HISTORY", outcome_access=OutcomeAccess.EVALUATION_SEALED)
    config, qualification = owner.derive_canonical_metadata_access(writer=writer, publication=publication, record=record,
        external=external, root=root, source_profile=profile)
    assert config.role is SourceMaterializationRole.RETAINED_HISTORY
    owner.validate_derived_metadata_access(external=external, root=root, source_profile=profile,
        version=record.VERSION, config=config, qualification=qualification)
    recursive = RecursiveStudyDraft("draft.retained-metadata", root.question, root.campaign,
        (), (), (), (), (external,), (), (), prospective_draft=root)
    selection = SimpleNamespace(source_configs=(config,), qualifications=(qualification,))
    projected = _source_projection(recursive, selection, {external.logical_artifact_id:record.VERSION})
    source = projected.prospective_draft.source_materializations[0]
    assert source.role is SourceMaterializationRole.RETAINED_HISTORY
    assert source.source_config_sha256 == config.fingerprint()
    assert source.qualification_receipt == ObjectIdentity.from_record(qualification.receipt_id, qualification)

    _, context = _fixture()
    template = context.templates[0]
    original_edge = next(value for value in template.graph.edges if value.external_input_id is not None)
    consumer = original_edge.consumer_node_id
    external_input = CandidateGraphExternalInput(external.input_id, ScientificInputRole.HISTORY,
        external.logical_artifact_id, ContentIdentityPolicy.EXACT_SHA256, external.expected_content_sha256,
        external.payload_schema, external.media_type, external.maximum_size_bytes,
        external.outcome_access, external.visibility_ceiling)
    edge = replace(original_edge, external_input_id=external.input_id, scientific_role=ScientificInputRole.HISTORY,
        logical_artifact_id=external.logical_artifact_id, payload_schema=external.payload_schema,
        media_type=external.media_type, maximum_size_bytes=external.maximum_size_bytes,
        outcome_access=external.outcome_access, visibility_ceiling=external.visibility_ceiling)
    graph = replace(template.graph, external_inputs=(external_input,),
        edges=tuple(edge if value==original_edge else value for value in template.graph.edges))
    protocol = replace(template.protocol, steps=tuple(replace(value,
        required_permissions=tuple(sorted({*value.required_permissions, CapabilityPermission.READ_SEALED_OUTCOMES})))
        if value.step_id==consumer else value for value in template.protocol.steps))
    def protocol_graph(graph, protocol):
        steps = {value.step_id:value for value in protocol.steps}
        return replace(graph, nodes=tuple(replace(value, protocol_step_sha256=steps[value.node_id].fingerprint())
            for value in graph.nodes))
    graph = protocol_graph(graph, protocol)
    template = replace(template, graph=graph, protocol=protocol)
    context = replace(context, qualifications=(qualification,), templates=(template,))
    diagnostics, accepted = _source_diagnostics(projected.prospective_draft, context, template)
    assert diagnostics == []
    assert accepted == (source.qualification_receipt,)

    # Source selection cannot turn sealed historical observations into ordinary streams.
    wrong_selection = SimpleNamespace(source_configs=(replace(config, role=SourceMaterializationRole.OBSERVATION_STREAM),),
        qualifications=(qualification,))
    with pytest.raises(ValueError, match="role"):
        _source_projection(recursive, wrong_selection, {external.logical_artifact_id:record.VERSION})
    source_external = replace(external, scientific_role="SOURCE")
    source_config, source_qualification = owner.derive_canonical_metadata_access(writer=writer, publication=publication,
        record=record, external=source_external, root=root, source_profile=profile)
    source_draft = _source_projection(replace(recursive, external_inputs=(source_external,)),
        SimpleNamespace(source_configs=(source_config,), qualifications=(source_qualification,)),
        {external.logical_artifact_id:record.VERSION}).prospective_draft
    source_graph = replace(graph, external_inputs=(replace(external_input, scientific_role=ScientificInputRole.SOURCE),),
        edges=tuple(replace(value, scientific_role=ScientificInputRole.SOURCE) if value==edge else value
            for value in graph.edges))
    refused, _ = _source_diagnostics(source_draft, replace(context, qualifications=(source_qualification,)),
        replace(template, graph=source_graph))
    assert any(value.field_path.endswith(".sealed-model") for value in refused)

    # Exact HISTORY still needs a sealed-runtime consumer and its exact receipt.
    no_permission = replace(protocol, steps=tuple(replace(value,
        required_permissions=tuple(permission for permission in value.required_permissions
            if permission is not CapabilityPermission.READ_SEALED_OUTCOMES))
        if value.step_id==consumer else value for value in protocol.steps))
    refused, _ = _source_diagnostics(projected.prospective_draft, context,
        replace(template, protocol=no_permission, graph=protocol_graph(graph, no_permission)))
    assert any(value.field_path.endswith(".sealed-model") for value in refused)
    refused, accepted = _source_diagnostics(projected.prospective_draft,
        replace(context, qualifications=(replace(qualification, content_sha256="e"*64),)), template)
    assert any(value.field_path.endswith(".qualification_receipt") for value in refused)
    assert accepted == ()


@pytest.mark.parametrize("damage", (None, "body", "parents", "before-read", "after-authentication", "after-read"))
def test_produced_history_authenticates_actual_publication_and_fresh_boundaries_without_source_qualification(metadata, damage, monkeypatch):
    """Real publication/decoder controls; the callback claims no real grant."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import inherit_external_inputs
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative import derivation
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent
    writer, root, profile, record, _, external = metadata
    parents = (ArtifactLineageParent(record, VisibilityCeiling.OUTCOME_VISIBLE, OutcomeAccess.EVALUATION_REVEALED),)
    external, = inherit_external_inputs((external,), ((external.input_id, record),), parents, retained_history=True)
    external = replace(external, logical_artifact_id=external.logical_artifact_id + ".retained")
    actual_parents = parents
    if damage == "parents":
        actual_parents = (replace(parents[0], identity=replace(record, object_fingerprint="f" * 64)),)
    publication = writer.write(ArtifactWriteRequest(external.logical_artifact_id,
        "retained/history.json", record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
        "retained.history", "retained", record.canonical_bytes(), external.visibility_ceiling,
        tuple(value.visibility_ceiling for value in actual_parents), external.outcome_access,
        lineage_parents=actual_parents))
    path = writer.root.resolve(publication.materialization.relative_path, for_write=False)
    if damage == "body":
        path.write_bytes(replace(record, object_id="derived.metadata.changed-history").canonical_bytes())
    from empirical_lawhood.infrastructure import publication_metadata
    events, calls = [], []
    authenticate = publication_metadata.authenticate_published_materialization
    decode = owner._read_canonical_metadata_binding
    def authenticate_actual(*args, **kwargs):
        events.append("authenticate")
        return authenticate(*args, **kwargs)
    def decode_actual(*args, **kwargs):
        events.append("decode")
        return decode(*args, **kwargs)
    monkeypatch.setattr(publication_metadata, "authenticate_published_materialization", authenticate_actual)
    monkeypatch.setattr(owner, "_read_canonical_metadata_binding", decode_actual)
    def require_current():
        calls.append(len(calls) + 1)
        events.append("current")
        refused_at = {"before-read": 1, "after-authentication": 2, "after-read": 3}.get(damage)
        if len(calls) == refused_at:
            raise PermissionError("actual current access refused")
    kwargs = dict(writer=writer, publication=publication, record=record, external=external,
        parents=parents, root=root, source_profile=profile, require_current=require_current)
    if damage is None:
        assert derivation._authenticate_produced_history_publication(**kwargs) is None
        assert calls == [1, 2, 3] and publication.logical.lineage_parents == parents
        assert events == ["current", "authenticate", "current", "decode", "current"]
        with pytest.raises(ValueError, match="cannot reveal"):
            owner._semantic_access(external=external, root=root, source_profile=profile, version=record.VERSION)
    else:
        with pytest.raises((PermissionError, ValueError, RuntimeError, ArtifactIdentityConflict)):
            derivation._authenticate_produced_history_publication(**kwargs)
        if damage == "before-read":
            assert calls == [1] and events == ["current"]
        elif damage == "after-authentication":
            assert calls == [1, 2] and events == ["current", "authenticate", "current"]
        elif damage == "after-read":
            assert calls == [1, 2, 3] and events == ["current", "authenticate", "current", "decode", "current"]
        elif damage == "parents":
            assert events == []
        else:
            assert events == ["current", "authenticate"]


@pytest.mark.parametrize("claim", ("configuration", "qualification", "both"))
def test_selected_history_rejects_stray_ordinary_source_claims_before_input_body_reads(metadata, monkeypatch, claim):
    """Actual typed ordinary-access rows must not be silently dropped by planning."""
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import inherit_external_inputs
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative import derivation
    from empirical_lawhood.infrastructure import bounded_io
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent
    writer, root, profile, record, publication, external = metadata
    config, qualification = owner.derive_canonical_metadata_access(writer=writer, publication=publication,
        record=record, external=external, root=root, source_profile=profile)
    parents = (ArtifactLineageParent(record, VisibilityCeiling.OUTCOME_VISIBLE, OutcomeAccess.EVALUATION_REVEALED),)
    history, = inherit_external_inputs((external,), ((external.input_id, record),), parents, retained_history=True)
    lowered = SimpleNamespace(input_records=((history.input_id, record),),
        draft=SimpleNamespace(external_inputs=(history,)))
    selected = SimpleNamespace(request=SimpleNamespace(produced_input_parents=parents,
        source_configs=(config,) if claim in ("configuration", "both") else (),
        qualifications=(qualification,) if claim in ("qualification", "both") else ()),
        programme=SimpleNamespace(sources=None, assay=SimpleNamespace(template_artifact=record)),
        evidence=SimpleNamespace(pipeline=SimpleNamespace(pipeline_config=SimpleNamespace(profile=profile))))
    # Only the pure domain projection is disclosed; its real typed ancestry and
    # planning admission predicates execute. This control creates no authority.
    monkeypatch.setattr(derivation.domain, "lower", lambda specification, selection: lowered)
    monkeypatch.setattr(derivation.domain, "project_root", lambda specification, selection: root)
    monkeypatch.setattr(derivation.domain, "source_arms", lambda specification, sources: ())
    def refuse_body_read(*args, **kwargs):
        pytest.fail("stray retained-HISTORY source claims reached input body I/O")
    monkeypatch.setattr(bounded_io, "read_bounded_bytes", refuse_body_read)
    with pytest.raises(ValueError, match="undeclared foreign source IDs"):
        derivation.plan_current_metadata(SimpleNamespace(phase="E6_TRANSFER"), selected,
            relative="unentered", files={})
