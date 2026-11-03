# SPDX-License-Identifier: MPL-2.0
"""Software controls only: exposed in-memory authority fixtures are not evidence."""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods import matrix_source_evidence as owner
from empirical_lawhood.adapters.methods.backbone_structural_transport import source_free_property_transport_source_input_parts as exposed
from empirical_lawhood.adapters.methods.backbone_structural_transport.source_free_property_transport_contracts import source_free_property_transport_capability_registry
from empirical_lawhood.api import matrix_source_runtime as runtime
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.evidence_profiles import EvidenceProfileSelection
from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceGateEvidence
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, ArtifactWriteResult, artifact_publication_batch_id, artifact_publication_commit_relative_path, artifact_publication_member
from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
from tests.test_matrix_sampling_admission import evidence_for, request_for


@pytest.fixture
def source_case():
    # Reuse disclosed software fixtures, including their in-memory test signer.
    # Nothing is stored, issued or admitted as real source/scientific authority.
    profile, source_manifest, registry, datasets = exposed._profile(label="exposed-matrix-control")
    compilation = exposed._compile(profile, source_manifest, registry, datasets)
    execution = exposed._execution_evidence(profile, compilation)
    pipeline = owner.MatrixSourcePipelineConfig("config.exposed.matrix-pipeline", profile, source_manifest,
        registry, datasets, compilation.dataset_operation_request, execution,
        "source-pipeline-decision-clock", "2026-08-23T01:00:00Z")
    receipt = pipeline.assess()
    selection = EvidenceProfileSelection("selection.exposed.matrix-source", "draft.exposed.matrix-source",
        "registry.exposed", "a"*64, "world.exposed", "1.0.0", "b"*64,
        "objective.exposed", "1.0.0", "c"*64, ())
    request = request_for()
    supplied = evidence_for(request)
    spec = replace(supplied.qualification_specification, source_pipeline_profile=owner.reference(profile, "profile_id"),
        source_pipeline_qualification=owner.reference(receipt, "receipt_id"),
        evidence_profile_selection=owner.reference(selection, "selection_id"),
        source_materialization=receipt.output_artifact, observation_operator=profile.observation_operator,
        numerical_view=replace(request.scope.population, object_id=profile.numerical_view_ids[0]),
        causal_cutoff=profile.causal_cutoff)
    gate = replace(supplied.qualification_result.gate_evidence[0], qualification_spec=owner.reference(spec, "spec_id"))
    installed = source_free_property_transport_capability_registry().capabilities[0]
    assessor = replace(installed, capability_key=request.method.capability_key,
        capability_version=request.method.capability_version, config_schema=request.scope.SCHEMA,
        input_schema_ids=tuple(sorted({value.object_schema for value in request.scope.operands})),
        output_schema_ids=(ScientificSourceGateEvidence.SCHEMA,),
        implementation_sha256=request.method.implementation_sha256)
    qualification = owner.MatrixSourceQualificationConfig("config.exposed.matrix-scientific-source", spec, receipt,
        CapabilityRegistry("registry.exposed.matrix-gate", (assessor,)), (gate,))
    evidence = owner.MatrixSourcePipelineEvidence("evidence.exposed.matrix-pipeline", pipeline, receipt, qualification, selection)
    return evidence, qualification.assess()


def test_generic_qualifiers_replay_actual_existing_services_and_canonical_records(source_case):
    evidence, result = source_case
    assert evidence.pipeline_config.assess() == evidence.receipt
    assert evidence.qualification_config.assess() == result
    assert result.evidence_links != (evidence.qualification_config.gate_evidence[0].publication,)
    for record in (evidence.pipeline_config, evidence.qualification_config, evidence):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    declarations = owner.source_declarations()[:2]
    assert tuple(value.capability_key for value in declarations) == ("matrix-source.pipeline-qualify", "matrix-source.scientific-qualify")
    assert all(value.manifest().maximum_outcome_access is OutcomeAccess.OUTCOME_BLIND for value in declarations)


def test_pipeline_replay_refuses_hidden_row_loss_and_invalid_original_authority_time(source_case):
    evidence, _ = source_case
    config = evidence.pipeline_config
    accounting = replace(config.execution_evidence.edge_accounting[0], dropped_without_disposition_count=1)
    changed = replace(config, execution_evidence=replace(config.execution_evidence, edge_accounting=(accounting,)))
    with pytest.raises(ValueError, match="hid row dropping"):
        changed.assess()
    with pytest.raises(PermissionError, match="expired"):
        replace(config, decision_time_utc="2100-01-01T00:00:00Z").assess()


def test_shared_source_helper_refuses_missing_actual_producers_before_any_reads(source_case):
    evidence, result = source_case
    with pytest.raises(PermissionError, match="complete original pipeline"):
        runtime.authenticate_matrix_source_qualification(writer=None,
            specification=evidence.qualification_config.specification, result=result, pipeline=evidence,
            executions=(), publications=(), codecs={}, read_scope=None)


@pytest.mark.parametrize("field", ("source_materialization", "observation_operator", "causal_cutoff"))
def test_shared_source_helper_refuses_profile_and_source_join_substitution_before_reads(source_case, field):
    evidence, result = source_case
    spec = evidence.qualification_config.specification
    changed = replace(spec, **{field: replace(getattr(spec, field), object_fingerprint="f"*64)})
    with pytest.raises(PermissionError, match="actual profile/source"):
        runtime.authenticate_matrix_source_qualification(writer=None, specification=changed, result=result,
            pipeline=evidence, executions=(), publications=(), codecs={}, read_scope=None)


@pytest.mark.parametrize("actual_access,actual_visibility", (
    (OutcomeAccess.OUTCOME_BLIND, runtime.VisibilityCeiling.PROSPECTIVE),
    (OutcomeAccess.EVALUATION_SEALED, runtime.VisibilityCeiling.PROSPECTIVE),
    (OutcomeAccess.EVALUATION_REVEALED, runtime.VisibilityCeiling.OUTCOME_VISIBLE),
))
def test_source_owner_requires_actual_declared_registered_implementation_and_config(
        source_case, tmp_path, monkeypatch, actual_access, actual_visibility):
    from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
    from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
    from empirical_lawhood.runtime.plans import ExternalInputSpec
    from tests.test_recursive_public_service import _plane

    evidence, _ = source_case
    declaration = owner.source_declarations()[0]
    manifest = declaration.manifest()
    config, receipt = evidence.pipeline_config, evidence.receipt
    binding = SimpleNamespace(run_id="run.exposed-source-owner", task_id="task.exposed",
        record=owner.reference(receipt, "receipt_id"), record_id_field="receipt_id")
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), "artifact.exposed.config")
    # Actual issued lowering omits these optional fields. They must never
    # broaden the actual stored configuration's blind/prospective lane.
    external = ExternalInputSpec("config", config_ref.artifact_id, config.fingerprint(), config.SCHEMA,
        None, None, None, None, None)
    task = SimpleNamespace(task_id=binding.task_id, capability=SimpleNamespace(capability_key=manifest.capability_key,
        capability_version=manifest.capability_version, config=config_ref),
        capability_implementation_sha256=manifest.implementation_sha256, dependency_task_ids=(), external_inputs=(external,))
    writer = _plane(tmp_path / "source-owner-custody")
    relative, scope, relative_root = provider_input_location(writer, binding.run_id, config_ref.artifact_id)
    writer.write(ArtifactWriteRequest(config_ref.artifact_id, relative, config.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", scope, relative_root, config.canonical_bytes(), actual_visibility, (), actual_access))
    # Isolate this disclosed producer shape; configuration custody below uses
    # the actual guarded writer, provider locator and current control reader.
    monkeypatch.setattr(runtime, "_genuine_context", lambda *_: None)
    reads = []
    read_control = CurrentIssuedTaskCustody.control_record
    def observe_control(self, *args, **kwargs):
        reads.append(None)
        return read_control(self, *args, **kwargs)
    monkeypatch.setattr(CurrentIssuedTaskCustody, "control_record", observe_control)
    arguments = dict(parent_evidence=(config, receipt, declaration, ("unit.a", "unit.b")), binding=binding,
        package=None, execution_plan=SimpleNamespace(tasks=(task,)), writer=writer)
    if actual_access is not OutcomeAccess.OUTCOME_BLIND:
        with pytest.raises(PermissionError):
            runtime._owner_scope(**arguments)
        assert not reads
        return
    runtime._owner_scope(**arguments)
    assert len(reads) == 1
    for field, value in (("expected_media_type", "application/octet-stream"),
            ("expected_outcome_access", OutcomeAccess.EVALUATION_SEALED)):
        task.external_inputs = (replace(external, **{field: value}),)
        with pytest.raises(PermissionError, match="complete original configuration"):
            runtime._owner_scope(**arguments)
        assert len(reads) == 1
    task.external_inputs = (external,)
    task.capability_implementation_sha256 = "f" * 64
    with pytest.raises(PermissionError, match="installed method"):
        runtime._owner_scope(**arguments)
    assert len(reads) == 1
    task.capability_implementation_sha256 = manifest.implementation_sha256
    writer.root.resolve(relative, for_write=False).write_bytes(b"changed original configuration")
    with pytest.raises((PermissionError, ArtifactIdentityConflict, ValueError)):
        runtime._owner_scope(**arguments)


def test_native_pipeline_output_uses_existing_guarded_codec_without_json_decode(source_case):
    evidence, _ = source_case
    manifest = evidence.pipeline_config.execution_evidence.output_manifest
    assert manifest.logical.profile is ArtifactProfile.PARQUET
    calls = []
    writer = SimpleNamespace(verify=lambda value: calls.append(("source", value)),
        verify_manifest=lambda value: calls.append(("manifest", value)))
    runtime._authenticate_pipeline_output(writer, evidence)
    assert calls == [("source", evidence.pipeline_config.execution_evidence.source_result.materialization),
        ("manifest", manifest)]
    changed = replace(evidence, receipt=replace(evidence.receipt, output_content_sha256="f"*64),
        qualification_config=replace(evidence.qualification_config,
            pipeline_receipt=replace(evidence.receipt, output_content_sha256="f"*64)))
    with pytest.raises(PermissionError, match="native output contract"):
        runtime._authenticate_pipeline_output(writer, changed)


def test_original_native_publication_bytes_do_not_require_canonical_json_headers(source_case, monkeypatch):
    evidence, _ = source_case
    raw = b"PAR1\x00exposed-in-memory-codec-control"
    digest = sha256(raw).hexdigest()
    old = evidence.pipeline_config.execution_evidence.output_manifest
    logical = replace(old.logical, content_sha256=digest)
    physical = replace(old.materialization, physical_sha256=digest, size_bytes=len(raw))
    members = (artifact_publication_member(logical, physical),)
    batch = artifact_publication_batch_id(old.publication.publication_scope, members)
    publication = replace(old.publication, publication_batch_id=batch, members=members,
        commit_marker_relative_path=artifact_publication_commit_relative_path(old.publication.publication_scope, batch))
    manifest = ArtifactManifest(logical, physical, publication)
    receipt = replace(evidence.receipt, output_artifact=ObjectIdentity.from_record(logical.logical_artifact_id, manifest),
        output_content_sha256=digest, publication=ObjectIdentity.from_record(batch, publication))
    config = replace(evidence.pipeline_config,
        execution_evidence=replace(evidence.pipeline_config.execution_evidence, output_manifest=manifest))
    pipeline = replace(evidence, pipeline_config=config, receipt=receipt,
        qualification_config=replace(evidence.qualification_config, pipeline_receipt=receipt))
    stored = ArtifactWriteResult(logical, physical, replace(physical,
        materialization_id=physical.materialization_id + ".manifest", relative_path=physical.relative_path + ".manifest.json"), False)
    calls = []
    writer = SimpleNamespace(root=SimpleNamespace(resolve=lambda *_args, **_kwargs: "/no-io"),
        verify=lambda value: calls.append(value), verify_manifest=lambda value: calls.append(value))
    monkeypatch.setattr(runtime, "authenticate_publication", lambda *_args: None)
    monkeypatch.setattr(runtime, "read_bounded_bytes", lambda *_args, **_kwargs: raw)
    pin = ObjectIdentity("native.exposed.dataset", logical.payload_schema, "1.0.0", digest)
    runtime._authenticate_source_publication(writer, pin, stored, pipeline)
    assert calls[-1] == manifest
    foreign = replace(stored, logical=replace(logical, logical_artifact_id="native.foreign"),
        materialization=replace(physical, logical_artifact_id="native.foreign"))
    with pytest.raises(PermissionError, match="registered native dataset"):
        runtime._authenticate_source_publication(writer, pin, foreign, pipeline)


@pytest.mark.parametrize("phase", (0, 1))
def test_real_source_qualifier_factory_builds_manifest_bound_installed_runner(phase):
    declaration = owner.source_declarations()[phase]
    manifest = declaration.manifest()
    registry = CapabilityRegistry("registry.exposed.source-qualifier", (manifest,))
    factory = declaration.provider_factory()
    supplier = SimpleNamespace(resolve_input=lambda _spec: None)
    provider = factory.build_provider(registry=registry, records=(), platform_ports=(ExecutablePlatformPort(
        factory.binding.required_platform_port_keys[0], RecursiveOperationInputPort(supplier)),))
    runner, = provider.runners(registry)
    assert runner.manifest == manifest
    with pytest.raises(PermissionError, match="actual issued task context"):
        runner.execute(SimpleNamespace())


def source_memory_context(declaration, config):
    from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, LogicalArtifactIdentity
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
    from empirical_lawhood.runtime.execution import TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
    from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificStage
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeInputContract, PreparedWorkerEnvironment
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
    from tests.test_matrix_sampling_follow_on import MemoryReader, pin

    manifest = declaration.manifest()
    raw = config.canonical_bytes()
    generic = ArtifactGenericValidation("validation.exposed.source-config", "1.0.0", "1"*64, config.SCHEMA, ArtifactProfile.CANONICAL_JSON)
    logical = LogicalArtifactIdentity("artifact.exposed.source-config", config.fingerprint(), config.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", runtime.VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND, generic)
    binding = WorkerInputBinding(logical.logical_artifact_id, "materialization.exposed.source-config", config.SCHEMA,
        "application/json", len(raw), runtime.VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND, WorkerInputKind.EXTERNAL)
    port = WorkerInputPort(binding, MemoryReader(raw))
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), logical.logical_artifact_id)
    task_id = "task.exposed.matrix-source"
    output = WorkerOutputPort(task_id + ".product", declaration.outputs[0].payload_schema,
        ArtifactProfile.CANONICAL_JSON, "application/json", "output.exposed.source")
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind,
        config_ref, manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions,
        declaration.evidence_ceiling, OutcomeAccess.OUTCOME_BLIND, declaration.resources)
    task = ExecutionTask(task_id, ScientificStage.QUALIFY, requirement, manifest.implementation_sha256, (),
        (ExternalInputSpec("config", logical.logical_artifact_id, config.fingerprint(), config.SCHEMA, "application/json",
            len(raw), runtime.VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND, None),),
        (ArtifactOutputSpec(output.output_id, output.logical_artifact_id, "exposed/source-result.json", output.payload_schema,
            output.profile, output.media_type, runtime.VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND),),
        (), BarrierKind.NONE, 1, ("obligation.exposed.source-qualifier",), scientific_inputs=())
    context = TaskContext("run.exposed.matrix-source", task_id, "attempt.exposed.matrix-source", config_ref,
        (binding,), (port,), (output,), manifest.permissions, OutcomeAccess.OUTCOME_BLIND,
        declaration.resources, WorkerIsolationProfile.TRUSTED_LOCAL)
    sources = (("synthetic/exposed.py", "1"*64),)
    implementation = RecursiveImplementationBinding(sources, sha256(canonical_json_bytes(sources)).hexdigest(),
        "2"*64, "3"*40, True)
    prepared = PreparedInvocationContract("prepared.exposed.matrix-source", manifest, implementation,
        PreparedWorkerEnvironment("/synthetic/python", "4"*64, "/synthetic", ()), context.run_id, task_id,
        context.attempt_id, config_ref, (PreparedNativeInputContract(logical, binding, config.fingerprint()),),
        (output,), manifest.permissions, OutcomeAccess.OUTCOME_BLIND, declaration.resources,
        WorkerIsolationProfile.TRUSTED_LOCAL, execution_plan=pin("plan.exposed.source", "empirical-lawhood/runtime/execution-plan"),
        execution_task=ObjectIdentity.from_record(task_id, task), execution_task_record=task,
        required_input_artifact_ids=(logical.logical_artifact_id,))
    return replace(context, prepared_invocation=prepared)


@pytest.mark.parametrize("phase", (0, 1))
def test_registered_source_worker_executes_actual_services_with_complete_in_memory_contract(source_case, phase):
    evidence, result = source_case
    config = (evidence.pipeline_config, evidence.qualification_config)[phase]
    expected = (evidence.receipt, result)[phase]
    declaration = owner.source_declarations()[phase]
    context = source_memory_context(declaration, config)
    worker = declaration.runner_factory()
    executed = worker.execute(context)
    assert decode_canonical_bytes(executed.outputs[0].payload, type(expected), maximum_bytes=None) == expected
    assert context.input_ports[0]._reader.stream.closed


def test_genuine_source_helper_refuses_exposed_development_and_fixture_roots():
    package = SimpleNamespace(issued_study=SimpleNamespace(candidate=SimpleNamespace(
        authoring_package=SimpleNamespace(base=SimpleNamespace(draft=SimpleNamespace(evaluation_unit_ids=("unit.a",)))))))
    with pytest.raises(PermissionError, match="fixture or source-free"):
        runtime._genuine_context(package, SimpleNamespace(), ("unit.a",))


def test_prior_identifier_allowlist_adds_only_actual_pipeline_receipt_field():
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
    from tests.test_matrix_sampling_follow_on import prior_product
    pin = ObjectIdentity("source-receipt.exposed", "empirical-lawhood/planning/source-pipeline-qualification-receipt", "1.0.0", "a"*64)
    prior = prior_product(pin).prior_execution
    assert replace(prior, record_id_field="receipt_id").record_id_field == "receipt_id"
    for value in ("publication_id", None, 2):
        with pytest.raises(ValueError, match="identifier field"):
            replace(prior, record_id_field=value)
    assert RecursivePriorExecutionBinding.__dataclass_fields__["record_id_field"].default == "record_id"


def test_explicit_blind_prior_contract_preserves_legacy_default_and_genuine_custody(monkeypatch):
    from inspect import signature
    from empirical_lawhood.api import recursive_qualified_parents as prior
    from tests.test_matrix_sampling_follow_on import prior_product
    from tests.test_matrix_sampling_admission import pin

    binding = prior_product(pin("record.exposed")).prior_execution
    assert signature(prior._authenticate_prior_execution).parameters["required_outcome_access"].default is OutcomeAccess.EVALUATION_SEALED
    with pytest.raises(PermissionError, match="explicit blind or legacy sealed"):
        prior._prior_execution_entry(binding, None, {}, None, OutcomeAccess.DEVELOPMENT_VISIBLE)
    def no_actual_package(*_, **options):
        raise PermissionError("actual original package still required")
    monkeypatch.setattr(prior, "_actual_package", no_actual_package)
    with pytest.raises(PermissionError, match="actual original package still required"):
        prior._prior_execution_entry(binding, None, {}, SimpleNamespace(plan_reader=None), OutcomeAccess.OUTCOME_BLIND)
