# SPDX-License-Identifier: MPL-2.0
"""Copied expanded E6 metadata controls with explicitly disclosed custody.

Unsigned public loading/derivation must refuse. Typed binding, deterministic
V3-to-V5 science, real immutable metadata publication and direct-input lowering
use named TEST original/permission boundaries. They establish no public positive
lifecycle, original custody, scientific qualification or execution authority.
No study is issued, native worker launched, or selected future acquired.
"""

from dataclasses import fields, replace
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_prepared_choices as scientific_choices
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as domain
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import project_e6_frozen_calibration, validate_e6_calibration_projection, validate_e6_transport_scope
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_operational_resources import MatrixSelectedOperationalResources
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_operational_resources import SelectedE4OperationalResources
from empirical_lawhood.api import matrix_selected_runtime
from empirical_lawhood.api.domain_composition.matrix_selected_declarative import derivation as api
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, load_experiment_specification
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, PreparedExperimentFile
from tests.test_matrix_e6_transport_assessment import fixture_case
from tests.test_matrix_e3_protected_public_lowering import resource_selection
from tests.test_matrix_factor_confirmation_eligibility import _matrix_plane
from tests.test_matrix_selected_declarative_preparation import (
    _protected_formal_graph, _protected_formal_request, disclosed_commitments,
    disclosed_produced_parents, disclose_produced_parent_seam)
from tests.test_matrix_selected_entry_scope import entry_shape
from tests.test_matrix_source_evidence import source_case  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]


def configured_request(case, pipeline):
    """Complete typed source/formal inputs; every original locator is TEST-only."""
    original = case.programme
    graph = _protected_formal_graph(original)
    root = graph.draft.prospective_draft
    # Keep the disclosed source evidence world explicit in the actual root.
    world = replace(root.system.world, world_id=pipeline.pipeline_config.profile.evidence_world_id)
    root = replace(root, system=replace(root.system, world=world,
        numerical_views=tuple(replace(view, world_id=world.world_id) for view in root.system.numerical_views)))
    entry = entry_shape(original, pipeline)
    spec = scientific_choices.SelectedPreparedProtectedSpecification("specification.e6.disclosed-transport", "ORIGINAL_E3",
        "E6_TRANSFER", original.point_design.expected_groups, original.point_design.arms, original.criterion,
        None, None, original.transfer_domain_claims)
    budget = ResourceBudget(1, 2*1024**3, 0, None, 2*1024**3, 2*1024**3)
    resources = MatrixSelectedOperationalResources("resources.e6.disclosed-transport", "PROTECTED",
        tuple((phase, budget) for phase in sorted(owner.PHASES)))
    rules = resource_selection(maximum_parallel_tasks=4)
    operational = SelectedE4OperationalResources("operational.e6.disclosed-transport",
        replace(rules.resources, aggregate_memory_ceiling_bytes=8*1024**3),
        tuple((phase, 100) for phase in sorted(owner.PHASES)), rules.native_progress, 1)
    selected = domain.SelectedPreparedDerivationRequestV3(request_id="request.e6.disclosed-transport",
        development_sources=None, protected_sources=original.sources, reservation=original.sources.closure.reservation,
        original_e3=ConfiguredMatrixSelectedPublicPackage.from_package(original.point_design.package),
        original_e3_products=entry.upstream_products, interpretations=tuple(scientific_choices.SelectedPreparedRecipeFamily(arm,
            next(value.family_id for value in original.point_design.interpretations if value.recipe == recipe.identity),
            next(value.scientific_premise for value in original.point_design.interpretations if value.recipe == recipe.identity))
            for arm, recipe in original.point_design.arms), original_e3_source=entry, original_e3_nomination=None,
        revision=None, revision_evidence=None, assay=original.assay, panels=original.panels, campaign=root.campaign,
        root=root, cutoff=InformationCutoff("cutoff.e6.disclosed-transport", original.sources.source_arms()[0][1].coordinate.clock_id,
            CausalPhase.PREPARATION, D(0)), operator_id="operator.disclosed-e6-software-control",
        entry=None, formal_methods=None, formal_source_inventories=(), qualifications=(), source_configs=(),
        phase_resources=resources, operational_resources=operational, original_commitments=disclosed_commitments(),
        produced_input_parents=disclosed_produced_parents(entry.upstream_products),
        transport_policy=case.policy)
    programme, evidence = domain.make_programme(spec, selected, e3_package=original.point_design.package)
    projection = project_e6_frozen_calibration(case.policy, original.point_design.package, record_id="projection.e6.disclosed-public")
    selection = domain.SelectedPreparedDerivedSelectionV5("selection.e6.disclosed-public", spec.identity,
        selected, programme, evidence, projection)
    lowered = domain.lower(spec, selection)
    formal = _protected_formal_request(SimpleNamespace(owner=owner), lowered.draft)
    selected = replace(selected, entry=formal.entry, formal_methods=formal.formal_methods,
        formal_source_inventories=formal.formal_source_inventories)
    return SimpleNamespace(case=case, specification=spec, request=selected, original=original,
        root=root, initial_lowered=lowered)


@pytest.fixture
def public_case(source_case):  # noqa: F811
    return configured_request(fixture_case(), source_case[0])


def disclosed_original_boundaries(monkeypatch, case):
    disclose_produced_parent_seam(monkeypatch)
    calls = []
    head = case.original.sources.closure.provenances[0].observed_git_head
    admitted = SimpleNamespace(implementation_commit=head, implementation_sha256="a"*64)
    monkeypatch.setattr(api, "capture_admitted_target_source", lambda root: admitted)
    def current(root, source):
        # The same disclosed source seam covers its final recheck; actual
        # committed-source authentication has separate public C controls.
        assert root == ROOT and source is admitted
        return source
    monkeypatch.setattr(api, 'require_admitted_target_source_current', current)
    def original(writer, request, codecs, *, read_access=None):
        assert read_access is None  # This disclosed control has no current grant selection.
        assert request.original_e3 == case.request.original_e3
        assert request.original_e3_products == case.request.original_e3_products
        calls.append("REOPEN_EXACT_ORIGINAL_CAL")
        return case.original.point_design.package
    def authenticated(writer, programme, evidence, codecs, *, source_scan_bytes,
            transport_policy=None, current_access=None):
        assert current_access is None  # No real source/issue permission is asserted.
        assert type(source_scan_bytes) is int
        assert source_scan_bytes == dict(case.request.phase_resources.phase_budgets)["entry"].source_scan_bytes
        transport_policy.__post_init__()
        validate_e6_transport_scope(transport_policy, programme)
        assert transport_policy == case.request.transport_policy
        assert evidence.upstream_products == case.request.original_e3_products
        domain.validate_evidence(programme, evidence)
        calls.append("AUTHENTICATE_PRETRAIN_POLICY_AND_ORIGINAL_ENTRY")
    monkeypatch.setattr(api, "original_e3_package", original)
    monkeypatch.setattr(matrix_selected_runtime, "_authenticate_entry", authenticated)
    return calls


def copied_request(case, directory):
    writer = _matrix_plane(directory)
    directory = Path(writer.root.contract.canonical_path)
    (directory/"specification.json").write_bytes(case.specification.canonical_bytes())
    (directory/"request.json").write_bytes(case.request.canonical_bytes())
    initial, _ = encode_matrix_arrays({"positions": np.zeros((2, 3, 4, 4), dtype="<c16"),
        "momenta": np.zeros((2, 3, 4, 4), dtype="<c16")})
    template, _ = encode_matrix_arrays({"generic_basis": np.zeros((3, 4, 4), dtype="<c16"),
        "force_coefficients": np.zeros((2, 3, 3), dtype="<f8"), "trace_coefficients": np.zeros((2, 3), dtype="<f8"),
        "receiver_coefficients": np.zeros((48, 2, 2, 3, 4), dtype="<f8")})
    values = {source.initial.array_artifact: initial for _, source in case.original.sources.source_arms()}
    values[case.original.assay.template_artifact] = template
    files = []
    for index, (artifact, raw) in enumerate(values.items()):
        assert (sha256(raw).hexdigest(), len(raw)) == (artifact.sha256, artifact.size_bytes)
        name = "original-file."+str(index)+".npz"
        (directory/name).write_bytes(raw)
        files.append(ExperimentFileInputBinding("file."+str(index), artifact, "1.0.0", name, len(raw)))
    selector = ExperimentFileInputSelection("sources.e6.disclosed-request", domain.PROTECTED_PROTOCOL_ID,
        (ExperimentInputBinding("request", case.request.identity, "request.json", len(case.request.canonical_bytes())),), tuple(files))
    (directory/"sources.json").write_bytes(selector.canonical_bytes())
    return writer, directory


def assert_transport_graph(case, lowered):
    operations = {row.node_id: row for row in lowered.draft.operations}
    sources = tuple(source for _, source in case.original.sources.source_arms())
    response_nodes = {owner.node_id(source, "responses") for source in sources}
    assert {row.node_id for row in operations.values()
        if row.selection.capability_key.endswith(".responses.empirical-transport")} == response_nodes
    assert all(operations[node].selection.capability_version == "3.0.0" for node in response_nodes)
    assert all(any(link.consumer_node_id == node and link.consumer_input_id == "decision"
        and link.producer_node_id == owner.node_id(source, "point") and link.producer_output_id == "decision"
        for link in lowered.draft.links) for source, node in zip(sources,
            (owner.node_id(source, "responses") for source in sources), strict=True))
    assert all(row.selection.capability_version == "2.0.0" for row in operations.values()
        if row.selection.capability_key.endswith((".point.empirical-transport", ".response-score.empirical-transport")))
    assert {row.node_id for row in operations.values() if row.selection.capability_key.endswith(".history.direct-inputs")} == {
        owner.preparation.node_id(source, "history") for source in sources}


@pytest.mark.parametrize("infinite_radius", (False, True))
def test_pure_lowering_keeps_every_reserved_native_root_and_actual_phase_formal_owner(source_case, infinite_radius):  # noqa: F811
    case = configured_request(fixture_case(missing_calibration=1 if infinite_radius else 0), source_case[0])
    assert_transport_graph(case, case.initial_lowered)
    if infinite_radius:
        assert all(row.admission == "ABSTAIN" for row in case.case.decisions.values())
    entry, inventories = domain._protected_formal_entry(case.initial_lowered.draft, case.request, owner)
    assessor, declaration = domain._protected_assessor(case.initial_lowered.draft, owner)
    assert declaration.capability_version == "2.0.0"
    assert declaration.config_record_type.SCHEMA.endswith("/selected-transport-root-config")
    assert entry.coverage.candidate_act_id == case.initial_lowered.draft.prospective_draft.draft_id
    assert all(row.output_ids == ("adjudication", "product") and row.adjudication_owner_ids == (assessor.node_id,)
        for row in entry.coverage.assignments)
    assert inventories[0].independent_unit_ids == case.initial_lowered.draft.prospective_draft.evaluation_unit_ids


def test_unsigned_copy_refuses_while_disclosed_v3_v5_science_and_real_metadata_roundtrip(public_case, tmp_path, monkeypatch):
    calls = disclosed_original_boundaries(monkeypatch, public_case)
    writer, directory = copied_request(public_case, tmp_path/"plane")
    spec = load_experiment_specification(directory/"specification.json")
    with pytest.raises(PermissionError, match="actual selected artifact writer"):
        load_experiment_inputs(spec, directory/"sources.json")
    # Copied fixture labels cannot satisfy the genuine public bootstrap, even
    # with a real writer. Keep this as a refusal, never a public positive case.
    with pytest.raises(PermissionError, match="complete canonical locator roster"):
        api.derive_inputs(specification=spec, source_selection_path=directory/"sources.json",
            project_root=ROOT, artifact_writer=writer, metadata_directory=directory/"derived",
            output_selection_path=directory/"current-sources.json", execution=ExecutionSelection(workers=4))
    assert not (directory/"derived").exists() and not (directory/"current-sources.json").exists()
    assert calls == []

    raw_request = (directory/"request.json").read_bytes()
    request = decode_canonical_bytes(raw_request, domain.SelectedPreparedDerivationRequestV3, maximum_bytes=None)
    assert request.canonical_bytes() == raw_request == public_case.request.canonical_bytes()
    typed = domain.bind_inputs(spec, {"request":request})
    first = api.derive_authenticated_selection(spec, typed.method_inputs.request, writer=writer, project_root=ROOT)
    second = api.derive_authenticated_selection(spec, typed.method_inputs.request, writer=writer, project_root=ROOT)
    assert type(first) is domain.SelectedPreparedDerivedSelectionV5 and first == second
    assert calls == ["REOPEN_EXACT_ORIGINAL_CAL", "AUTHENTICATE_PRETRAIN_POLICY_AND_ORIGINAL_ENTRY"]*2
    validate_e6_calibration_projection(first.transport_calibration, public_case.case.policy,
        public_case.original.point_design.package)
    assert first.transport_calibration.radius == public_case.original.point_design.package.calibration.radius
    assert first.request.transport_policy.canonical_bytes() == public_case.case.policy.canonical_bytes()

    selector_raw = (directory/"sources.json").read_bytes()
    selector = decode_canonical_bytes(selector_raw, ExperimentFileInputSelection, maximum_bytes=None)
    handles = {value.identity:PreparedExperimentFile(value.identity, value.record_version,
        directory/value.relative_path, value.maximum_bytes) for value in selector.files}
    current, planned = api.plan_current_metadata(spec, first, relative="disclosed-metadata", files=handles)
    checks = []
    with writer.verification_scope() as scoped:
        def disclosed_permission():
            # A test-only boundary marker, not an issued/reveal authority.
            assert current.request.produced_input_parents == public_case.request.produced_input_parents
            checks.append("DISCLOSED_PERMISSION_ONLY")
            scoped.require_verification_snapshot()
        publications = api.publish_current_metadata(spec, current, writer=scoped, planned=planned,
            require_current=disclosed_permission)
        assert len(publications) == len(planned) > 0 and len(checks) >= len(planned)
        parents = current.request.produced_input_parents
        raw = current.canonical_bytes()
        publication = scoped.write(ArtifactWriteRequest(current.record_id,
            "disclosed-metadata/selection.json", current.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
            "disclosed.e6.selection", "disclosed-metadata", raw, VisibilityCeiling.OUTCOME_VISIBLE,
            tuple(value.visibility_ceiling for value in parents), OutcomeAccess.EVALUATION_REVEALED, lineage_parents=parents))
        disclosed_permission()
        authenticate_published_materialization(scoped, publication)
        retained = read_bounded_bytes(scoped.root.resolve(publication.materialization.relative_path, for_write=False), maximum_bytes=len(raw))
        cold = decode_canonical_bytes(retained, domain.SelectedPreparedDerivedSelectionV5, maximum_bytes=len(raw))
        assert cold.canonical_bytes() == retained == raw and cold == current
        disclosed_permission()
    api.validate_current_metadata(spec, cold)
    assert cold.transport_calibration == first.transport_calibration
    assert cold.request.transport_policy.canonical_bytes() == public_case.case.policy.canonical_bytes()
    lowered = domain.lower(spec, cold)
    bound = domain.bind_inputs(spec, {"selection":cold}, files={key:handles[artifact] for key,artifact in lowered.input_artifacts})
    assert bound.method_inputs.selection == cold
    assert_transport_graph(public_case, lowered)
    declarations = {row.registration().selection:row for row in owner.operation_declarations()}
    assert sum(declarations[row.selection].execution_properties.native_effect for row in lowered.draft.operations) == 8


def test_request_has_no_editable_radius_and_real_scope_rejects_changed_policy(public_case, tmp_path, monkeypatch):
    disclosed_original_boundaries(monkeypatch, public_case)
    document = json.loads(public_case.request.canonical_bytes())
    document["value"]["transport_calibration"] = public_case.case.projection.to_document()
    with pytest.raises((ValueError, TypeError)):
        decode_canonical_bytes(canonical_json_bytes(document), domain.SelectedPreparedDerivationRequestV3, maximum_bytes=None)
    changed = replace(public_case.request.transport_policy, criterion=replace(public_case.specification.criterion,
        normalized_error_maximum=D(9)))
    writer = _matrix_plane(tmp_path/"foreign-policy")
    with pytest.raises((ValueError, PermissionError)):
        api.derive_authenticated_selection(public_case.specification,
            replace(public_case.request, transport_policy=changed), writer=writer, project_root=ROOT)


def test_original_e3_e6_refuses_a_request_without_its_pretrain_policy(public_case):
    current = public_case.request
    point_request = domain.SelectedPreparedDerivationRequestV2(**{
        field.name: getattr(current, field.name) for field in fields(domain.SelectedPreparedDerivationRequestV2)})
    with pytest.raises(TypeError, match="preTRAIN transport policy"):
        domain.make_programme(public_case.specification, point_request,
            e3_package=public_case.original.point_design.package)
    assert current == public_case.request
    assert decode_canonical_bytes(current.canonical_bytes(), type(current), maximum_bytes=None) == current
