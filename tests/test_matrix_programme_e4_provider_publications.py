# SPDX-License-Identifier: MPL-2.0
# ruff: noqa: F811
"""Real frozen input/provider checks around disclosed unissued producer I/O.

Task, CONFIG, specs, canonical source records and committed provider bytes are
actual typed controls. Original package/plan/authority lookup is an explicit
injected metadata premise: no E3 receipt, issue, reveal, native work or scientific
qualification is established. The owning assay authenticator remains real.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_programme_e4_inputs as api
from empirical_lawhood.api import current_result_custody as current
from empirical_lawhood.api import recursive_qualified_parents as parents
from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement, CapabilityRegistry
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionPlan, ExecutionTask, ExternalInputSpec, PlanLane, RunPlan, ScientificInputRole, ScientificInputSpec
from tests.test_matrix_finite_dt_source_assembly import c_backed_source_case, selected_request  # noqa: F401
from tests.worker_configuration_support import freeze_worker_configuration


def _provider_case(case, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_records import ConfiguredProtectedE3PhysicalForecastConfig
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_preparation import response_task_id
    assay, criterion = case.assay, case.preparation.mathematical_protocol
    template = case.committed.scientific_design.training_assay.array_artifact
    source_file, = (value for value in case.training.template_files.values() if value.identity == template)
    raw_template = source_file.path.read_bytes()
    assert (len(raw_template), sha256(raw_template).hexdigest()) == (template.size_bytes, template.sha256)
    family = selected_e3_product_family(case.public.specification)
    declaration, = (value for value in family.operation_declarations()
        if value.capability_key == family.namespace + ".physical-forecast")
    manifest = declaration.manifest()
    numerical, = (value for value in case.preparation.numerical_profiles
        if value.original_protocol.object_fingerprint == assay.fingerprint())
    task_id = response_task_id(assay.public_source.root.root_id, "physical-forecast")
    config = ConfiguredProtectedE3PhysicalForecastConfig("config." + task_id, assay.public_source.root.root_id,
        case.public.specification.identity, ObjectIdentity.from_record(assay.protocol_id, assay),
        ObjectIdentity.from_record(numerical.record_id, numerical))
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), config.config_id)
    rows = (("automatic", config.config_id, config.SCHEMA, "application/json", config.canonical_bytes(), ArtifactProfile.CANONICAL_JSON),
        ("protocol", assay.protocol_id, assay.SCHEMA, "application/json", assay.canonical_bytes(), ArtifactProfile.CANONICAL_JSON),
        ("mathematical-protocol", criterion.protocol_id, criterion.SCHEMA, "application/json", criterion.canonical_bytes(), ArtifactProfile.CANONICAL_JSON),
        ("templates-arrays", template.artifact_id, template.payload_schema, template.media_type, raw_template, ArtifactProfile.MATRIX_ARRAY_NPZ))
    specs, edges = [], []
    for name, identifier, schema, media, raw, _ in rows:
        specs.append(ExternalInputSpec("external." + name, identifier, sha256(raw).hexdigest(), schema, media,
            len(raw), VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND, None))
        if name != "automatic":
            edges.append(ScientificInputSpec("edge." + name, name, ScientificInputRole.SOURCE,
                None, None, "external." + name, "scientific." + name, identifier, schema, media, len(raw),
                OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, BarrierKind.NONE))
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind,
        config_ref, manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions,
        EvidenceCeiling.NON_PROMOTABLE, declaration.outcome_access, declaration.resources)
    outputs = tuple(ArtifactOutputSpec(task_id + "." + row.output_id, "unentered." + row.output_id,
        "unentered/" + row.output_id + row.filename_suffix, row.payload_schema, row.profile, row.media_type,
        declaration.visibility_ceiling, (), declaration.outcome_access) for row in declaration.outputs)
    task = freeze_worker_configuration(ExecutionTask(task_id, declaration.stage, requirement,
        manifest.implementation_sha256, (), tuple(sorted(specs, key=lambda value: value.input_id)), outputs, (), BarrierKind.NONE, 1,
        ("obligation.disclosed-provider-control",), scientific_inputs=tuple(sorted(edges, key=lambda value: value.edge_id))))
    registry = CapabilityRegistry("registry.disclosed-e4-assay-provider", (manifest,))
    model = next(value for value in case.original_products if value.record.object_fingerprint == case.public.models.fingerprint())
    run_id = model.prior_execution.run_id
    def pin(identifier, schema):
        return ObjectIdentity(identifier, schema, "1.0.0", "a" * 64)
    plan = ExecutionPlan("execution." + run_id, PlanLane.PROSPECTIVE,
        ObjectIdentity(run_id, RunPlan.SCHEMA, RunPlan.VERSION, "a" * 64),
        registry.fingerprint(), "b" * 40, (task,), True,
        candidate=pin("candidate.disclosed-provider", "empirical-lawhood/runtime/executable-study-candidate"),
        issued_extension_set=pin("extensions.disclosed-provider", "empirical-lawhood/runtime/issued-extension-set"),
        execution_resource_envelope_spec=pin("envelope.disclosed-provider", "empirical-lawhood/runtime/execution-resource-envelope-spec"),
        predevelopment_jit_signature_census=None, jit_graph_signature_manifest=None)
    # Closed original lookup is explicitly disclosed, not a canonical package
    # or issued custody. All records below the two lookup seams remain actual.
    package_pin = model.prior_execution.package
    package = SimpleNamespace(package_id=package_pin.object_id, SCHEMA=package_pin.object_schema,
        VERSION=package_pin.object_version, fingerprint=lambda: package_pin.object_fingerprint, registry=registry)
    products = tuple(replace(value, prior_execution=replace(value.prior_execution,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan))) for value in case.original_products)
    issued = object()
    monkeypatch.setattr(api, "_original_product_metadata", lambda *_, **_kw: (package, issued, None, None, None, ()))
    monkeypatch.setattr(current, "authenticate_current_execution_plan", lambda **_: plan)
    monkeypatch.setattr(parents, "_actual_package", lambda *_args, **_kwargs: package)
    monkeypatch.setattr(parents, "_replay_parent_authority", lambda *_: (issued, None))
    publications, exports = {}, {}
    for name, identifier, schema, media, raw, profile in rows:
        relative, scope, prefix = provider_input_location(case.plane, run_id, identifier)
        publications[name] = case.plane.write(ArtifactWriteRequest(identifier, relative, schema, profile, media,
            scope, prefix, raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        if name in ("protocol", "templates-arrays"):
            exports[name] = case.plane.write(ArtifactWriteRequest(identifier, "exported-provider-controls/" + name + ".bin",
                schema, profile, media, "disclosed-exported-copy", "exported-provider-controls", raw,
                VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    calls = []
    def require_current():
        calls.append("fresh-original")
    return SimpleNamespace(case=case, plane=case.plane, assay=assay, template=template, criterion=criterion,
        task=task, plan=plan, package=package, products=products, publications=publications, exports=exports,
        calls=calls, require_current=require_current)


def _resolve(f, *, require_current=None):
    return api._original_assay_provider_publications(writer=f.plane, public=f.case.public,
        original_products=f.products, assay=f.assay, template=f.template,
        require_current=f.require_current if require_current is None else require_current)


def test_exact_frozen_provider_publications_feed_unchanged_assay_owner(c_backed_source_case, monkeypatch):
    f = _provider_case(c_backed_source_case, monkeypatch)
    assay, template = _resolve(f)
    assert (assay.logical, assay.materialization) == (f.publications["protocol"].logical, f.publications["protocol"].materialization)
    assert template.materialization.relative_path == f.publications["templates-arrays"].materialization.relative_path
    assert assay.materialization.relative_path != f.exports["protocol"].materialization.relative_path
    assert template.materialization.relative_path != f.exports["templates-arrays"].materialization.relative_path
    criterion = api.authenticate_selected_e3_assay(public=f.case.public, upstream_products=f.products,
        assay=f.assay, assay_publication=assay, template_publication=template, criterion=f.criterion, writer=f.plane)
    assert criterion.logical.content_sha256 == f.criterion.fingerprint()
    assert f.calls


@pytest.mark.parametrize("role", ("protocol", "templates-arrays"))
def test_equal_bytes_exported_publication_cannot_replace_actual_provider_before_body(c_backed_source_case,
        monkeypatch, role):
    import os
    f = _provider_case(c_backed_source_case, monkeypatch)
    original, foreign = f.publications[role], f.exports[role]
    target = f.plane.root.resolve(original.materialization.relative_path + ".manifest.json", for_write=False)
    saved = target.read_bytes()
    alias = f.plane.root.resolve(foreign.materialization.relative_path + ".manifest.json", for_write=False)
    body = f.plane.root.resolve(original.materialization.relative_path, for_write=False)
    opening = os.open
    def guard(path, *args, **kwargs):
        if not isinstance(path, int) and Path(path) == body:
            pytest.fail("foreign publication path opened the original selected body")
        return opening(path, *args, **kwargs)
    monkeypatch.setattr(os, "open", guard)
    try:
        target.write_bytes(alias.read_bytes())
        with pytest.raises((ValueError, PermissionError, RuntimeError)):
            _resolve(f)
    finally:
        target.write_bytes(saved)


@pytest.mark.parametrize("damage", ("missing", "foreign-edge"))
def test_frozen_configuration_substitution_refuses_before_any_provider_body(c_backed_source_case, monkeypatch, damage):
    f = _provider_case(c_backed_source_case, monkeypatch)
    config_edge, = (value for value in f.task.scientific_inputs if value.scientific_role is ScientificInputRole.CONFIGURATION)
    edges = tuple(value for value in f.task.scientific_inputs if value is not config_edge)
    if damage == "foreign-edge":
        edges = tuple(sorted((*edges, replace(config_edge, edge_id="edge.foreign.config")), key=lambda value: value.edge_id))
    plan = replace(f.plan, tasks=(replace(f.task, scientific_inputs=edges),))
    products = tuple(replace(value, prior_execution=replace(value.prior_execution,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan))) for value in f.products)
    monkeypatch.setattr(current, "authenticate_current_execution_plan", lambda **_: plan)
    monkeypatch.setattr(api, "_publication_from_manifest", lambda *_: pytest.fail("invalid CONFIG reached provider body verification"))
    with pytest.raises(ValueError, match="CONFIGURATION"):
        api._original_assay_provider_publications(writer=f.plane, public=f.case.public, original_products=products,
            assay=f.assay, template=f.template, require_current=f.require_current)


@pytest.mark.parametrize("boundary", (1, 3))
def test_current_original_refusal_precedes_provider_body_verification(c_backed_source_case, monkeypatch, boundary):
    f = _provider_case(c_backed_source_case, monkeypatch)
    calls = []
    def expired():
        calls.append("current")
        if len(calls) == boundary:
            raise PermissionError("DISCLOSED_ORIGINAL_ACCESS_EXPIRED")
    monkeypatch.setattr(api, "_publication_from_manifest", lambda *_: pytest.fail("expired access opened provider bodies"))
    with pytest.raises(PermissionError, match="ORIGINAL_ACCESS_EXPIRED"):
        _resolve(f, require_current=expired)
    assert len(calls) == boundary


def test_public_e4_context_passes_resolved_provider_handles_to_real_assay_owner(c_backed_source_case, monkeypatch):
    f = _provider_case(c_backed_source_case, monkeypatch)
    request = replace(selected_request(f.case), original_products=f.products)
    locator = request.native_training_locator
    packet = SimpleNamespace(packet_id=locator.packet.object_id, SCHEMA=locator.packet.object_schema,
        VERSION=locator.packet.object_version, fingerprint=lambda: locator.packet.object_fingerprint)
    training_plan = SimpleNamespace(execution_plan_id=locator.execution_plan.object_id,
        SCHEMA=locator.execution_plan.object_schema, VERSION=locator.execution_plan.object_version,
        fingerprint=lambda: locator.execution_plan.object_fingerprint)
    monkeypatch.setattr(api, "load_authored_wave", lambda **_: (packet, object(), object(), object()))
    monkeypatch.setattr(api, "_retained_plans", lambda *_: (SimpleNamespace(run_plan_id=locator.run_id), training_plan, object()))
    monkeypatch.setattr(api, "_read_instance", lambda *_: (f.case.training.specification, f.case.training.request, object()))
    def training_operands(writer, selected_locator):
        assert selected_locator == locator
        return f.case.training.specification, f.case.training.request
    monkeypatch.setattr(api, '_recorded_training_operands', training_operands)
    monkeypatch.setattr(api, "authenticate_selected_e3_public_package", lambda **_: None)
    monkeypatch.setattr(api, "authenticate_selected_e3_training_banks", lambda **_: None)
    monkeypatch.setattr(api, "_require_original_e3_access", lambda **_: f.require_current())
    owning, seen = api.authenticate_selected_e3_assay, []
    def authenticate(**kwargs):
        assert kwargs["assay_publication"].materialization.relative_path == f.publications["protocol"].materialization.relative_path
        assert kwargs["template_publication"].materialization.relative_path == f.publications["templates-arrays"].materialization.relative_path
        seen.append(kwargs["assay_publication"])
        return owning(**kwargs)
    monkeypatch.setattr(api, "authenticate_selected_e3_assay", authenticate)
    with api.authenticated_programme_e4_banks(artifact_writer=f.plane, input_commitments=request.input_commitments,
            original_e3=request.original_e3, original_preparation=request.original_preparation,
            original_assay=request.original_assay, original_products=request.original_products,
            native_training_locator=locator, maximum_source_bytes=request.source_budget.source_scan_bytes) as result:
        assert tuple(name for name, _ in result.banks) == ("DEVELOPMENT", "CALIBRATION", "CONFIRMATION")
    assert len(seen) == 1
