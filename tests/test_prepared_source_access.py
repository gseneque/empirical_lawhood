# SPDX-License-Identifier: MPL-2.0
"""Closed source bootstrap controls; disclosed spies establish no real authority.

The model envelope in ordering tests is deliberately undecodable. Genuine
TRAIN/DEV source admission and native lifecycle remain independent acceptance.
"""
from dataclasses import fields, replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods import matrix_prepared_source_experiment as domain
from empirical_lawhood.adapters.methods import matrix_prepared_source_bindings as gates
from empirical_lawhood.adapters.methods.matrix_prepared_source_assembly import MatrixPreparedSourceAssemblyRequest
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
from empirical_lawhood.api import prepared_source_access as owner
from empirical_lawhood.api import selected_prepared_access as original
from empirical_lawhood.api.matrix_source_input_assembly import publish_source_input_record
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, ArtifactWriteRequest
from tests.test_matrix_finite_dt_source_assembly import c_backed_source_case, selected_request  # noqa: F401
from tests.test_matrix_prepared_source import disclosed_certificate, prepared_bank
from tests.test_matrix_selected_opportunity import opportunity  # noqa: F401
from tests.test_matrix_selected_protected import confirmation, transfer  # noqa: F401
from tests.test_recursive_public_service import _plane
from tests.test_current_result_custody import actual_issued_current_task_controls  # noqa: F401


@pytest.fixture
def source_literals(c_backed_source_case, confirmation, opportunity):  # noqa: F811
    finite = selected_request(c_backed_source_case)
    certificate = disclosed_certificate(prepared_bank(confirmation), opportunity)
    values = {field.name: getattr(finite, field.name) for field in fields(MatrixPreparedSourceAssemblyRequest)
        if hasattr(finite, field.name)}
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support
    values.update(prepared_programme=confirmation.identity, development_product=certificate.locator.identity,
        exposure_support=exposure_support(c_backed_source_case.committed.exposure_audit))
    # The request is canonical disclosed metadata. No original I/O or grant is
    # asserted by constructing it, and no fitted body is admitted as a locator.
    request = MatrixPreparedSourceAssemblyRequest(**values)
    return request, certificate.locator


def _selected_case(tmp_path, source_literals, monkeypatch, *, sibling=False):
    request, development = source_literals
    plane = _plane(tmp_path / "source-boundary")
    parents = request.original_e3.publication.logical.lineage_parents
    if not parents:
        from empirical_lawhood.runtime.artifacts import ArtifactLineageParent
        parents = (ArtifactLineageParent(request.original_products[0].record,
            VisibilityCeiling.PROSPECTIVE, OutcomeAccess.EVALUATION_SEALED),)
    # Disclosed exact parent metadata only, never an actual permission context.
    scope = owner.PreparedSourceOriginalInputAccess(plane, request.original_products, request.original_products,
        (development,), parents, (), (), None)
    clock = {"current": True, "calls": 0}
    def current(self, **kwargs):
        clock["calls"] += 1
        if not clock["current"]:
            raise PermissionError("DISCLOSED_ORIGINAL_GRANT_EXPIRED")
    monkeypatch.setattr(original.SelectedPreparedOriginalInputAccess, "require_current", current)
    captured = []
    def actual_scope(**kwargs):
        captured.append(kwargs["read_access"])
        scope.require_current()
        return scope
    monkeypatch.setattr(owner, "_original_access", actual_scope)
    raw = canonical_json_document_bytes({"schema": domain.MatrixPreparedSourceQualificationSelection.SCHEMA,
        "version": domain.MatrixPreparedSourceQualificationSelection.VERSION,
        "value": {"disclosed": "MODEL BODY MUST NOT BE DECODED BY BOOTSTRAP"}})
    pin = ObjectIdentity("selection.disclosed.source-bootstrap", domain.MatrixPreparedSourceQualificationSelection.SCHEMA,
        domain.MatrixPreparedSourceQualificationSelection.VERSION, sha256(raw).hexdigest())
    specification = domain.MatrixPreparedSourceQualificationSpecification("specification.disclosed.source-bootstrap", pin, 1)
    pair = produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY, parents=parents)
    def model(identifier, path):
        return ArtifactWriteRequest(identifier, path, pin.object_schema, ArtifactProfile.CANONICAL_JSON,
            "application/json", "source-boundary", ".", raw, pair[1],
            tuple(parent.visibility_ceiling for parent in parents), pair[0], lineage_parents=parents)
    if sibling:
        plane.write_batch((model("source.selection", "selection.json"), model("alien.same-parent", "alien.json")))
    else:
        plane.write(model("source.selection", "selection.json"))
    records = {"source-request": request, "development.0": development}
    bindings = [ExperimentInputBinding("selection", pin, "selection.json", len(raw))]
    for key, value in records.items():
        publish_source_input_record(writer=plane, prefix="companions", namespace="source-boundary", name=key, record=value)
        bindings.append(ExperimentInputBinding(key, value.identity, "companions/" + key + ".json", len(value.canonical_bytes())))
    selector = ExperimentFileInputSelection("sources.disclosed.source-bootstrap", domain.PROTOCOL_ID,
        tuple(sorted(bindings, key=lambda row: row.key)), ())
    selector_path = plane.root.resolve("sources.json", for_write=True)
    selector_path.write_bytes(selector.canonical_bytes())
    decoded = []
    def read_locator(key, reference, kind):
        decoded.append(kind)
        assert kind in domain.locator_record_types()
        value = records[key]
        assert value.identity == reference and type(value) is kind
        return value
    return SimpleNamespace(plane=plane, scope=scope, clock=clock, captured=captured, specification=specification,
        selector=selector, selector_path=selector_path, read_locator=read_locator, decoded=decoded,
        request=request, development=development)


def _bootstrap(case, *, selection=None, read_access=None):
    return owner.bootstrap_selected_input_access(specification=case.specification,
        selection=case.selector if selection is None else selection, read_locator=case.read_locator,
        artifact_writer=case.plane, selection_path=case.selector_path, read_access=read_access)


def test_source_bootstrap_reads_only_automatic_locators_and_refreshes_returned_guard(tmp_path, source_literals, monkeypatch):
    case = _selected_case(tmp_path, source_literals, monkeypatch)
    raw = case.request.canonical_bytes()
    guard = _bootstrap(case)
    assert set(case.decoded) <= set(domain.locator_record_types())
    assert domain.MatrixPreparedSourceQualificationSelection not in case.decoded
    assert case.request.canonical_bytes() == raw
    assert guard() is None
    case.clock["current"] = False
    with pytest.raises(PermissionError, match="EXPIRED"):
        guard()


@pytest.mark.parametrize("damage", ("missing", "duplicate", "model-as-locator", "foreign-selection"))
def test_source_bootstrap_refuses_bad_closed_census_before_model_hash(tmp_path, source_literals, monkeypatch, damage):
    case = _selected_case(tmp_path, source_literals, monkeypatch)
    rows = case.selector.bindings
    if damage == "missing":
        rows = tuple(row for row in rows if row.key != "development.0")
    elif damage == "duplicate":
        with pytest.raises(ValueError):
            replace(case.selector, bindings=(*rows, rows[0]))
        return
    elif damage == "model-as-locator":
        rows = tuple(replace(row, identity=case.specification.selection) if row.key == "development.0" else row for row in rows)
    else:
        rows = tuple(replace(row, identity=replace(row.identity, object_fingerprint="f" * 64))
            if row.key == "selection" else row for row in rows)
    selector = replace(case.selector, bindings=rows)
    monkeypatch.setattr(case.plane, "verify_manifest", lambda *_args, **_kwargs: pytest.fail("bad census reached model hash"))
    with pytest.raises(PermissionError, match="census|DEV locator|selection"):
        _bootstrap(case, selection=selector)


@pytest.mark.parametrize("damage", ("missing-parents", "plain-label", "foreign-member"))
def test_source_manifest_role_refuses_substitution_before_body(tmp_path, source_literals, monkeypatch, damage):
    case = _selected_case(tmp_path, source_literals, monkeypatch)
    actual = case.plane.read_manifest
    def metadata(path, **kwargs):
        manifest = actual(path, **kwargs)
        if path != "selection.json":
            return manifest
        logical = manifest.logical
        if damage == "missing-parents":
            logical = replace(logical, lineage_parents=(), parent_visibility_ceilings=(),
                outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
        elif damage == "plain-label":
            logical = replace(logical, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
        else:
            return ArtifactManifest(logical, replace(manifest.materialization, relative_path="foreign.json"))
        return ArtifactManifest(logical, manifest.materialization)
    monkeypatch.setattr(case.plane, "read_manifest", metadata)
    monkeypatch.setattr(case.plane, "verify_manifest", lambda *_args, **_kwargs: pytest.fail("bad source metadata reached body hash"))
    with pytest.raises(PermissionError, match="ancestry|custody|manifest"):
        _bootstrap(case)


def test_source_bootstrap_unknown_same_parent_publication_sibling_is_unopened(tmp_path, source_literals, monkeypatch):
    import os
    case = _selected_case(tmp_path, source_literals, monkeypatch, sibling=True)
    opened = []
    actual = os.open
    def opening(path, *args, **kwargs):
        opened.append(str(path))
        return actual(path, *args, **kwargs)
    monkeypatch.setattr(os, "open", opening)
    with pytest.raises(PermissionError, match="unselected sibling"):
        _bootstrap(case)
    assert not any(path.endswith("/alien.json") or path == "alien.json" for path in opened)


def test_source_current_replacement_is_forwarded_without_changing_original_request(tmp_path, source_literals, monkeypatch):
    case = _selected_case(tmp_path, source_literals, monkeypatch)
    originals = tuple(replace(value, reveal_authority=replace(value.reveal_authority,
        object_id="authority.disclosed.replacement", object_fingerprint="d" * 64)) for value in case.request.original_products)
    current = original.SelectedPreparedCurrentAccess(originals)
    before = case.request.canonical_bytes()
    _bootstrap(case, read_access=current)
    assert case.captured == [current]
    assert case.request.canonical_bytes() == before


def test_source_grant_expiry_during_manifest_replay_refuses_before_caller_decode(tmp_path, source_literals, monkeypatch):
    case = _selected_case(tmp_path, source_literals, monkeypatch)
    actual = case.plane.verify_manifest
    def verified(manifest, **kwargs):
        result = actual(manifest, **kwargs)
        case.clock["current"] = False
        return result
    monkeypatch.setattr(case.plane, "verify_manifest", verified)
    with pytest.raises(PermissionError, match="EXPIRED"):
        _bootstrap(case)
    assert domain.MatrixPreparedSourceQualificationSelection not in case.decoded


@pytest.mark.parametrize("phase", ("E5_CONFIRMATION", "E6_TRANSFER"))
def test_actual_source_declaration_supports_exact_input_lanes_without_reveal_authority(phase):
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement, input_access_allowed
    from empirical_lawhood.runtime.plans import ScientificStage
    for declaration in (gates.gate_declaration(gates.r.GATES[0], phase), gates.closeout_declaration()):
        manifest = declaration.manifest()
        config = CapabilityConfigRef("config.disclosed.source-permission", declaration.config_record_type.SCHEMA,
            manifest.config_schema_sha256, "a" * 64, "config.disclosed.source-permission")
        requirement = CapabilityRequirement(declaration.capability_key, declaration.capability_version,
            manifest.kind, config, (config.config_schema,), tuple(sorted({row.payload_schema for row in declaration.outputs})),
            declaration.permissions, declaration.evidence_ceiling, declaration.outcome_access, declaration.resources)
        assert declaration.stage in (ScientificStage.QUALIFY, ScientificStage.REPORT)
        assert declaration.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
        for access in (OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.DEVELOPMENT_VISIBLE, OutcomeAccess.EVALUATION_SEALED):
            assert input_access_allowed(requirement, access)
        for access in (OutcomeAccess.EVALUATION_REVEALED, OutcomeAccess.EVALUATOR_REVEAL, OutcomeAccess.PRIVILEGED_TRUTH):
            assert not input_access_allowed(requirement, access)


@pytest.mark.parametrize("model_input", (False, True))
def test_explicit_model_publication_preserves_mixed_seal_and_all_eleven_parents(tmp_path, model_input):
    from decimal import Decimal
    from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, derived_outcome_access, lineage_parent_sort_key
    plane = _plane(tmp_path / "model-publication")
    record = InformationCutoff("cutoff.disclosed.model-publication", "clock.disclosed.model-publication", CausalPhase.PREPARATION, Decimal(0))
    parents = tuple(sorted((ArtifactLineageParent(ObjectIdentity("parent.disclosed." + str(index),
        "empirical-lawhood/testing/disclosed-source-parent", "1.0.0", format(index, "064x")),
        VisibilityCeiling.PROSPECTIVE if index < 8 else VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.EVALUATION_SEALED if index < 8 else OutcomeAccess.DEVELOPMENT_VISIBLE)
        for index in range(11)), key=lineage_parent_sort_key))
    first, observed = publish_source_input_record(writer=plane, prefix="inputs", namespace="disclosed-model",
        name="model-input", record=record, lineage_parents=parents, model_input=model_input)
    _, repeated = publish_source_input_record(writer=plane, prefix="inputs", namespace="disclosed-model",
        name="model-input", record=record, lineage_parents=parents, model_input=model_input)
    assert len(observed.logical.lineage_parents) == 11 and observed.logical.lineage_parents == parents
    assert observed.logical.outcome_access is (OutcomeAccess.EVALUATION_SEALED if model_input else
        derived_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(row.outcome_access for row in parents)))
    assert first.created and observed.canonical_bytes() == repeated.canonical_bytes()
    assert plane.root.resolve(observed.materialization.relative_path, for_write=False).read_bytes() == record.canonical_bytes()
    _, intrinsic = publish_source_input_record(writer=plane, prefix="inputs", namespace="disclosed-model", name="locator", record=record)
    assert intrinsic.logical.lineage_parents == ()
    assert (intrinsic.logical.outcome_access, intrinsic.logical.visibility_ceiling) == (OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    with pytest.raises(ValueError, match="nonempty"):
        publish_source_input_record(writer=plane, prefix="inputs", namespace="disclosed-model", name="bad-model", record=record, model_input=True)


@pytest.mark.parametrize("damage", ("missing", "substituted", "complete"))
def test_source_gate_config_contract_is_checked_before_any_control_body(actual_issued_current_task_controls, monkeypatch, damage):  # noqa: F811
    """Disclosed custody spies isolate CONFIG ordering; no scientific admission."""
    from empirical_lawhood.api import matrix_prepared_source_runtime as runtime
    from empirical_lawhood.runtime.plans import ScientificInputRole
    case = actual_issued_current_task_controls
    task = next(row for row in case.plan.tasks if row.task_id == case.context.task_id)
    config_edge, = (row for row in task.scientific_inputs if row.scientific_role is ScientificInputRole.CONFIGURATION)
    if damage == "missing":
        task = replace(task, scientific_inputs=tuple(row for row in task.scientific_inputs if row is not config_edge))
    elif damage == "substituted":
        task = replace(task, scientific_inputs=tuple(replace(row, edge_id="edge.foreign.disclosed-config")
            if row is config_edge else row for row in task.scientific_inputs))
    monkeypatch.setattr(case.custody, "current_task", lambda *_: (None, None, task))
    calls = []
    member = SimpleNamespace(materialization=SimpleNamespace(size_bytes=1))
    monkeypatch.setattr(case.custody, "task_inputs", lambda *_: ({}, {case.context.config.artifact_id: member}))
    def body(*_args, **kwargs):
        calls.append(kwargs)
        raise PermissionError("DISCLOSED_FIRST_CONTROL_BODY_BOUNDARY")
    monkeypatch.setattr(case.custody, "control_record", body)
    monkeypatch.setattr(case.custody, "immutable_control_record", body)
    supplier = runtime.MatrixPreparedSourceRuntimeInputSupplier(SimpleNamespace(), custody=case.custody)
    gate = gates.MatrixPreparedSourceGateWorker(gates.r.GATES[0], "E6_TRANSFER")
    if damage == "complete":
        with pytest.raises(PermissionError, match="FIRST_CONTROL_BODY"):
            supplier._prepare_matrix_prepared_source_gate(case.context, gate)
        spec, = (row for row in task.external_inputs if row.input_id == "config")
        assert calls == [{"expected_outcome_access": spec.expected_outcome_access,
            "expected_visibility_ceiling": spec.expected_visibility_ceiling}]
    else:
        with pytest.raises(ValueError, match="CONFIGURATION"):
            supplier._prepare_matrix_prepared_source_gate(case.context, gate)
        assert calls == []


@pytest.mark.parametrize("reversed_lifetime", (False, True))
def test_source_training_member_scope_remains_live_through_actual_final_rehash(tmp_path, source_literals, monkeypatch, reversed_lifetime):
    """Real artifact snapshots, disclosed exact metadata owner, no TRAIN verdict."""
    from contextlib import contextmanager
    from empirical_lawhood.api import native_training_read_scope as training_owner
    case = _selected_case(tmp_path, source_literals, monkeypatch)
    member = case.plane.read_manifest("companions/source-request.json")
    fact = member.logical, member.materialization
    events = []
    @contextmanager
    def metadata_scope(*, artifact_writer, locator):
        assert locator == case.request.native_training_locator
        assert artifact_writer.root.contract == case.plane.root.contract
        with artifact_writer.verification_scope() as live:
            def require_member(manifest):
                events.append("metadata-member")
                live.require_active_verification_scope()
                if (manifest.logical, manifest.materialization) != fact:
                    raise PermissionError("DISCLOSED_FOREIGN_TRAIN_METADATA")
            yield SimpleNamespace(require_member=require_member)
        events.append("metadata-closed")
    monkeypatch.setattr(training_owner, "authenticated_native_training_read_scope", metadata_scope)
    if reversed_lifetime:
        # This deliberately invalid caller ordering must fail its real outer
        # snapshot; a retained exact-member fact cannot extend its lifetime.
        with pytest.raises((ValueError, PermissionError, ArtifactIdentityConflict), match="scope has ended"):
            with case.plane.verification_scope(before_member=lambda manifest: bound.require_original_member(manifest)) as reader:
                with owner.authenticated_prepared_source_access(scope=case.scope,
                        locator=case.request.native_training_locator) as bound:
                    reader.verify_manifest(member)
        assert "metadata-closed" in events
        assert events[-1] == "metadata-member"
    else:
        with owner.authenticated_prepared_source_access(scope=case.scope,
                locator=case.request.native_training_locator) as bound:
            with case.plane.verification_scope(before_member=bound.require_original_member) as reader:
                reader.verify_manifest(member)
                before_exit = events.count("metadata-member")
            assert events.count("metadata-member") > before_exit
        assert events[-1] == "metadata-closed"


@pytest.mark.parametrize("damage", ("none", "request", "programme", "model-as-dev"))
def test_initial_source_assembly_uses_the_same_closed_locators_before_programme_body(tmp_path, source_literals, confirmation, monkeypatch, damage):  # noqa: F811
    from empirical_lawhood.adapters.methods import matrix_prepared_source_assembly as assembly
    case = _selected_case(tmp_path, source_literals, monkeypatch)
    pair = produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY, parents=case.scope.parents)
    raw = confirmation.canonical_bytes()
    publication = case.plane.write(ArtifactWriteRequest("model.disclosed.prepared-programme", "programme.json", confirmation.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "assembly-boundary", ".", raw, pair[1],
        tuple(row.visibility_ceiling for row in case.scope.parents), pair[0], lineage_parents=case.scope.parents))
    assert publication.logical.content_sha256 == case.request.prepared_programme.object_fingerprint
    rows = tuple(sorted((ExperimentInputBinding("request", case.request.identity, "companions/source-request.json", len(case.request.canonical_bytes())),
        ExperimentInputBinding("prepared-programme", case.request.prepared_programme, "programme.json", len(raw)),
        ExperimentInputBinding("development-product", case.development.identity, "companions/development.0.json", len(case.development.canonical_bytes()))),
        key=lambda row: row.key))
    specification = assembly.MatrixPreparedSourceAssemblySpecification("assembly.disclosed.bootstrap", case.request.identity)
    if damage == "request":
        rows = tuple(replace(row, identity=replace(row.identity, object_fingerprint="f" * 64)) if row.key == "request" else row for row in rows)
    elif damage == "programme":
        rows = tuple(replace(row, identity=replace(row.identity, object_fingerprint="f" * 64)) if row.key == "prepared-programme" else row for row in rows)
    elif damage == "model-as-dev":
        rows = tuple(replace(row, identity=case.request.prepared_programme) if row.key == "development-product" else row for row in rows)
    selection = ExperimentFileInputSelection("sources.disclosed.assembly", assembly.PROTOCOL_ID, rows, ())
    reads = []
    def locator(key, pin, kind):
        reads.append(kind)
        assert kind in domain.locator_record_types()
        value = case.request if key == "request" else case.development
        assert type(value) is kind and value.identity == pin
        return value
    if damage != "none":
        monkeypatch.setattr(case.plane, "verify_manifest", lambda *_args, **_kwargs: pytest.fail("bad initial input reached body hash"))
        with pytest.raises(PermissionError, match="request|programme|DEV locator"):
            owner.bootstrap_assembly_selected_input_access(specification=specification, selection=selection,
                read_locator=locator, artifact_writer=case.plane, selection_path=case.selector_path)
    else:
        current = owner.bootstrap_assembly_selected_input_access(specification=specification, selection=selection,
            read_locator=locator, artifact_writer=case.plane, selection_path=case.selector_path)
        assert current() is None
    assert domain.MatrixPreparedSourceQualificationSelection not in reads


@pytest.mark.parametrize("damage", ("none", "unknown-locator", "foreign-same-schema"))
def test_source_request_prospective_membership_uses_its_actual_closed_locator_owner(tmp_path, source_literals, confirmation, monkeypatch, damage):  # noqa: F811
    """Real source-request bytes and packet sidecars; no issued/science verdict.

    The model envelope stays deliberately undecodable, as in the before-body
    controls above. Exact member admission precedes later scientific decoding.
    """
    from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
    from empirical_lawhood.runtime.prospective_experiment import ProspectiveExperimentAssociation, instance_identity, source_filename
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveImplementationBinding, RecursiveWaveMember
    from tests.test_recursive_public_service import _draft
    case = _selected_case(tmp_path, source_literals, monkeypatch)
    directory = case.plane.root.resolve("issued-source", for_write=True)
    directory.mkdir()
    scope = replace(case.scope, issued_specification=case.specification)
    draft = _draft()
    sources = (("empirical_lawhood/__init__.py", "0" * 64),)
    implementation = RecursiveImplementationBinding(sources, sha256(canonical_json_bytes(sources)).hexdigest(), "1" * 64, "a" * 40, True)
    records = {"draft.json": draft, "implementation.json": implementation}
    members = tuple(RecursiveWaveMember(name, ObjectIdentity.from_record("disclosed.source." + name.removesuffix(".json"), record),
        len(record.canonical_bytes())) for name, record in sorted(records.items()))
    by_name = {member.filename: member.identity for member in members}
    packet = AuthoredRecursiveWave("packet.disclosed.source-members", by_name["draft.json"], by_name["implementation.json"], members)
    bank = prepared_bank(confirmation)
    allocation = UnitAllocation("allocation.disclosed.source-members", (case.request.prepared_programme,),
        tuple(IndependentUnit(group, case.request.prepared_programme.object_id, "family.disclosed.source-members", ("fine", "primary"), False)
            for group in bank.group_ids), tuple(UnitRoleAssignment(group, "source") for group in bank.group_ids))
    request_pin = ObjectIdentity.from_record("source-request", case.request)
    development_pin = ObjectIdentity.from_record("development.0", case.development)
    companion_inputs = {source_filename(case.specification.selection): (case.specification.selection,
            case.plane.root.resolve("selection.json", for_write=False).read_bytes(), domain.MatrixPreparedSourceQualificationSelection.SCHEMA),
        source_filename(request_pin): (request_pin, case.request.canonical_bytes(), case.request.SCHEMA),
        source_filename(development_pin): (development_pin, case.development.canonical_bytes(), case.development.SCHEMA)}
    input_pins = [case.specification.selection, request_pin, development_pin]
    if damage == "unknown-locator":
        cutoff = case.request.physical_cutoff
        unknown = ObjectIdentity.from_record("unknown.locator", cutoff)
        companion_inputs[source_filename(unknown)] = unknown, cutoff.canonical_bytes(), cutoff.SCHEMA
        input_pins.append(unknown)
    instance = ExperimentInstanceBinding(case.specification.identity, allocation.identity, packet.draft,
        ObjectIdentity("projection.disclosed.source-members", draft.SCHEMA, draft.VERSION, "b" * 64),
        ObjectIdentity.from_record(draft.campaign.campaign_id, draft.campaign), tuple(sorted(input_pins, key=lambda pin: pin.object_id)))
    companions = {"experiment-specification.json": (case.specification.identity, case.specification.canonical_bytes(), case.specification.SCHEMA),
        "experiment-allocation.json": (allocation.identity, allocation.canonical_bytes(), allocation.SCHEMA),
        "experiment-instance.json": (instance_identity(instance), instance.canonical_bytes(), instance.SCHEMA), **companion_inputs}
    companion_members = tuple(RecursiveWaveMember(name, pin, len(raw)) for name, (pin, raw, _) in sorted(companions.items()))
    candidate = ObjectIdentity("candidate.disclosed.source-members", ExecutableStudyCandidate.SCHEMA, ExecutableStudyCandidate.VERSION, "a" * 64)
    association = ProspectiveExperimentAssociation("association.disclosed.source-members", ObjectIdentity.from_record(packet.packet_id, packet),
        candidate, instance_identity(instance), companion_members)
    manifests = []
    for lane, data in (("prospective", {name: (record.canonical_bytes(), record.SCHEMA)
            for name, record in {**records, "authored-wave.json": packet}.items()}),
            ("experiment", {**{name: (raw, schema) for name, (_, raw, schema) in companions.items()},
                "experiment-association.json": (association.canonical_bytes(), association.SCHEMA)})):
        for name, (raw, schema) in sorted(data.items()):
            parents = scope.parents if name in ("draft.json", source_filename(case.specification.selection)) else ()
            pair = produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE if parents else OutcomeAccess.OUTCOME_BLIND,
                declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY if parents else VisibilityCeiling.PROSPECTIVE, parents=parents)
            relative = "issued-source/" + lane + "/" + name
            publication = case.plane.write(ArtifactWriteRequest("disclosed.source." + lane + "." + name.removesuffix(".json"),
                relative, schema, ArtifactProfile.CANONICAL_JSON, "application/json", "disclosed.source." + lane,
                "issued-source/" + lane, raw, pair[1], tuple(row.visibility_ceiling for row in parents), pair[0], lineage_parents=parents))
            manifests.append(case.plane.read_manifest(publication.materialization.relative_path))
    # The real source request is outside the selected-declarative locator list;
    # only the actual source owner's closed codec projection admits it.
    assert case.request.SCHEMA not in {kind.SCHEMA for kind in original.domain.locator_record_types()}
    request_manifest = next(row for row in manifests if row.materialization.relative_path.endswith(source_filename(request_pin)))
    assert request_manifest.logical.content_sha256 == case.request.fingerprint()
    assert request_manifest.materialization.size_bytes == len(case.request.canonical_bytes())
    monkeypatch.setattr(case.plane, "verify_manifest", lambda *_args, **_kwargs: pytest.fail("member preflight opened a body"))
    if damage == "unknown-locator":
        with pytest.raises(PermissionError, match="intrinsic locator/control"):
            scope.bind_issued_members(tuple(manifests), packet=packet, association=association, directory=directory)
        return
    bound = scope.bind_issued_members(tuple(manifests), packet=packet, association=association, directory=directory)
    bound.require_issued_member(request_manifest)
    if damage == "foreign-same-schema":
        # Valid adverse metadata envelope: same schema/hash/size/pair, but no
        # stale publication binding and a different exact logical member.
        foreign = ArtifactManifest(replace(request_manifest.logical, logical_artifact_id="foreign.source-request"),
            replace(request_manifest.materialization, logical_artifact_id="foreign.source-request"))
        with pytest.raises(PermissionError, match="outside|foreign"):
            bound.require_issued_member(foreign)
    assert case.request.canonical_bytes() == source_literals[0].canonical_bytes()



def test_request_only_assembly_first_stop_uses_no_locator_body_or_writer(tmp_path, source_literals, monkeypatch):
    """Actual public request decoding reports missing science without authority."""
    from empirical_lawhood.adapters.methods import matrix_prepared_source_assembly as assembly
    from empirical_lawhood.api import experiment_preparation as preparation
    from empirical_lawhood.api.experiment_runtime_bindings import bootstrap_selected_experiment_inputs
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
    request, _ = source_literals
    specification = assembly.MatrixPreparedSourceAssemblySpecification("assembly.disclosed.first-stop", request.identity)
    selector = ExperimentFileInputSelection("sources.disclosed.first-stop", assembly.PROTOCOL_ID,
        (ExperimentInputBinding("request", request.identity, "request.json", len(request.canonical_bytes())),), ())
    selected = tmp_path / "sources.json"
    (tmp_path / "request.json").write_bytes(request.canonical_bytes())
    selected.write_bytes(selector.canonical_bytes())
    def forbidden(*_args, **_kwargs):
        pytest.fail("request-only bootstrap opened an input body")
    guard = bootstrap_selected_experiment_inputs(declaration=preparation._protocol(specification),
        specification=specification, selection=selector, read_record=forbidden, artifact_writer=None,
        selection_path=selected)
    assert guard() is None
    monkeypatch.setattr(owner, "_original_access", forbidden)
    loaded = preparation.load_experiment_inputs(specification, selected)
    assert loaded.method_inputs.request == request
    assert loaded.method_inputs.prepared_programme is None
    assert loaded.method_inputs.development_product is None
    report = preparation.prepare_experiment(specification, method_inputs=loaded.method_inputs,
        execution=ExecutionSelection(workers=4))
    assert not report.executable and report.census.native_effect_count == 0
    assert {row.source_key for row in report.dependencies if row.source_key} == {
        "prepared-programme", "development-product"}
    assert "prepared-source-assembly.derive" not in {row.code for row in report.dependencies}
    assert (tmp_path / "request.json").read_bytes() == request.canonical_bytes()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["request.json", "sources.json"]


def test_request_only_exception_cannot_open_model_unknown_file_or_foreign_input(source_literals):
    from empirical_lawhood.adapters.methods import matrix_prepared_source_assembly as assembly
    from empirical_lawhood.api import experiment_preparation as preparation
    from empirical_lawhood.api.experiment_runtime_bindings import bootstrap_selected_experiment_inputs
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
    request, development = source_literals
    specification = assembly.MatrixPreparedSourceAssemblySpecification("assembly.disclosed.first-stop-negative", request.identity)
    request_row = ExperimentInputBinding("request", request.identity, "request.json", len(request.canonical_bytes()))
    programme_row = ExperimentInputBinding("prepared-programme", request.prepared_programme, "model.json", 1)
    development_row = ExperimentInputBinding("development-product", development.identity, "development.json", len(development.canonical_bytes()))
    unknown_row = ExperimentInputBinding("unknown", development.identity, "unknown.json", len(development.canonical_bytes()))
    file = ExperimentFileInputBinding("original-file", ArtifactIdentity("file.disclosed.first-stop", "source",
        "empirical-lawhood/disclosed-first-stop-file", "f" * 64, "application/octet-stream", 1),
        "1.0.0", "never-open.bin", 1)
    cases = [
        ((request_row, programme_row), ()),
        ((request_row, programme_row, development_row), ()),
        ((request_row, unknown_row), ()),
        ((request_row,), (file,)),
        ((replace(request_row, identity=replace(request.identity, object_fingerprint="f" * 64)),), ()),
        ((replace(request_row, identity=replace(request.identity, object_schema=development.SCHEMA)),), ()),
        ((replace(request_row, identity=replace(request.identity, object_version="9.0.0")),), ()),
    ]
    calls = []
    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        pytest.fail("invalid copied selector reached a locator or model body")
    declaration = preparation._protocol(specification)
    for rows, files in cases:
        selector = ExperimentFileInputSelection("sources.disclosed.first-stop-negative", assembly.PROTOCOL_ID,
            tuple(sorted(rows, key=lambda row: row.key)), files)
        with pytest.raises(PermissionError, match="metadata protocol|census|exact request|artifact writer"):
            bootstrap_selected_experiment_inputs(declaration=declaration, specification=specification,
                selection=selector, read_record=forbidden, artifact_writer=None)
    assert calls == []


def test_prepared_gate_parents_join_every_actual_selected_config_field(source_literals, confirmation, opportunity):  # noqa: F811
    """Closed mathematical scope with an explicit unexecuted source-authority stop."""
    from empirical_lawhood.adapters.methods import matrix_prepared_source_records as records
    from empirical_lawhood.adapters.methods import matrix_prepared_source_pipeline as row_owner
    from empirical_lawhood.adapters.methods.backbone_structural_transport import source_free_property_transport_source_input_parts as pipeline
    from empirical_lawhood.planning.evidence_profiles import build_observation_evidence_world_registry, bind_profile_selection, EvidenceWorldKind
    from empirical_lawhood.planning.source_pipelines import SourcePipelineQualificationDisposition, SourcePipelineQualificationReceipt
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent
    request, development = source_literals
    bank = prepared_bank(confirmation)
    certificate = disclosed_certificate(bank, opportunity)
    profile, _, _, _ = pipeline._profile(label="prepared-parent-projection-unexecuted")
    profile = replace(profile, observation_operator=bank.assay.identity,
        causal_cutoff=records.pin(certificate.cutoff, "cutoff_id"),
        numerical_view_ids=(bank.sources.closure.numerical_scope.object_id,))
    receipt = SourcePipelineQualificationReceipt("receipt.disclosed.no-source-authority",
        records.pin(profile, "profile_id"), SourcePipelineQualificationDisposition.AUTHORITY_REQUIRED,
        None, (), None, None, (), None, None, ("DISCLOSED_NO_SOURCE_AUTHORITY",),
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    profiles = build_observation_evidence_world_registry()
    world, = (value for value in profiles.world_profiles if value.world_kind is EvidenceWorldKind.DETERMINISTIC_SIMULATOR)
    evidence = bind_profile_selection(selection_id="selection.disclosed.parent-projection", draft_id="draft.disclosed.parent-projection",
        registry=profiles, world_profile_id=world.profile_id, objective_profile_id="objective.observation-order", requested_rungs=())
    unpublished = ObjectIdentity("unexecuted.source-verification", row_owner.MatrixPreparedSourceVerification.SCHEMA,
        row_owner.MatrixPreparedSourceVerification.VERSION, "0" * 64)
    scope = records.MatrixPreparedSourceScope("scope.disclosed.parent-projection", bank.identity,
        bank.sources.closure.identity, bank.sources.identity, bank.assay.identity,
        bank.sources.closure.numerical_scope, certificate.original_future_reservation,
        certificate.identity, certificate.cutoff, bank.group_ids, profile, receipt, evidence,
        unpublished, unpublished, request.source_budget)
    parents = tuple(sorted((ArtifactLineageParent(request.original_products[0].record,
        VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE),
        ArtifactLineageParent(request.original_products[1].record,
        VisibilityCeiling.PROSPECTIVE, OutcomeAccess.EVALUATION_SEALED)), key=lambda row: row.identity.object_id))
    access = owner.PreparedSourceOriginalInputAccess(None, request.original_products, request.original_products,
        (development,), parents, (), (), None, source_scope=scope)
    configs = records.gate_configs(scope)
    assert len(configs) == len(records.GATES)
    for config in configs:
        assert access.record_parents(config) is access.parents
    config = configs[0]
    damages = (
        {"config_id": config.config_id + ".foreign"},
        {"scope": replace(config.scope, object_fingerprint="f" * 64)},
        {"phase": "E6_TRANSFER" if config.phase == "E5_CONFIRMATION" else "E5_CONFIRMATION"},
        {"gate_kind": configs[1].gate_kind},
        {"group_ids": tuple(sorted((*config.group_ids, "group.foreign.parent-projection")))},
        {"resource_budget": replace(config.resource_budget, output_bytes=config.resource_budget.output_bytes + 1)},
    )
    for damage in damages:
        with pytest.raises(PermissionError, match="exact selected source scope"):
            access.record_parents(replace(config, **damage))
    with pytest.raises(PermissionError, match="exact selected source scope"):
        replace(access, source_scope=None).record_parents(config)
    with pytest.raises(TypeError, match="exact immutable selected scope"):
        replace(access, source_scope=SimpleNamespace())
    assert not hasattr(access, "canonical_bytes")
    assert receipt.disposition is SourcePipelineQualificationDisposition.AUTHORITY_REQUIRED
