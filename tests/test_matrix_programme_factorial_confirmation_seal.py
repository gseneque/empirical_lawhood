# SPDX-License-Identifier: MPL-2.0
"""Unissued metadata conformance, with no grants, native work or qualification.

All descriptors below are unpublished. The source association receipt is a
pure compiler fixture; public preparation must still authenticate actual
genuine issue, qualified-parent and original acquisition custody.
"""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial_confirmation as method
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial_confirmation_composition as composition
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial_confirmation_custody as custody
from empirical_lawhood.api import matrix_scheduled_factorial_runtime as api
from empirical_lawhood.api import matrix_scheduled_programme as public
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.planning.study_authoring import DesignInputRole, SourceAccessDisposition, SourceMaterializationRef, SourceMaterializationRole
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, ArtifactWriteRequest, ArtifactWriteResult, CanonicalTaskReceipt, LogicalArtifactIdentity, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRegistry, CapabilityRequirement
from empirical_lawhood.runtime.compiler import _config_input, compile_run_plan, lower_run_plan
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, ExecutionPlan, ExecutionTask, PlanLane
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.runtime_platform.test_native_subwork import _plane
from tests.test_matrix_programme_factorial_confirmation import criteria as criteria, _pin
from tests.test_matrix_scheduled_programme_reduction import declared as declared
from tests.test_matrix_scheduled_programme_acquisition import declared_root


def _publication(record, key):
    """Exact declared bytes only; no publication or successful I/O asserted."""
    raw = record.canonical_bytes()
    generic = ArtifactGenericValidation("validator.unpublished.metadata", "1.0.0", "1"*64, record.SCHEMA, ArtifactProfile.CANONICAL_JSON)
    logical = LogicalArtifactIdentity("artifact.unpublished."+key, sha256(raw).hexdigest(), record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND, generic)
    physical = ArtifactMaterialization("materialization.unpublished."+key, logical.logical_artifact_id,
        "storage.unpublished.metadata", "unpublished/"+key+".json", sha256(raw).hexdigest(), len(raw), "none")
    return ArtifactWriteResult(logical, physical, replace(physical, materialization_id=physical.materialization_id+".sidecar",
        relative_path=physical.relative_path+".manifest.json"), False)


def _binding(criteria, *, config_spec_change=None):
    declaration = method.operation_declarations()[0]
    manifest = declaration.manifest()
    config = criteria.configuration
    config_publication, publication = _publication(config, "original-config"), _publication(criteria, "original-criteria")
    node = method.freeze_node_id(config.specification)
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(),
        config_publication.logical.logical_artifact_id)
    config_spec = _config_input(config_ref)
    if config_spec_change:
        config_spec = replace(config_spec, **config_spec_change)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, config_ref,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, manifest.maximum_evidence_ceiling,
        manifest.maximum_outcome_access, manifest.resource_ceiling)
    output = ArtifactOutputSpec(node+".product", publication.logical.logical_artifact_id, publication.materialization.relative_path,
        criteria.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND)
    task = ExecutionTask(node, declaration.stage, requirement, manifest.implementation_sha256, (), (config_spec,), (output,), (),
        declaration.execution_properties.barrier, 1, ("obligation.unpublished.original-criteria",), scientific_inputs=())
    plan = ExecutionPlan("plan.unpublished.original-criteria", PlanLane.PROSPECTIVE,
        _pin("run.unpublished.original-criteria", "empirical-lawhood/runtime/run-plan"), "2"*64, "d"*40, (task,), True,
        candidate=_pin("candidate.unpublished.original-criteria", "empirical-lawhood/planning/draft-study-candidate"),
        issued_extension_set=_pin("extensions.unpublished", "empirical-lawhood/runtime/issued-extension-set"),
        execution_resource_envelope_spec=_pin("resources.unpublished", "empirical-lawhood/runtime/execution-resource-envelope-spec"),
        predevelopment_jit_signature_census=None, jit_graph_signature_manifest=None)
    receipt = CanonicalTaskReceipt("receipt.unpublished.original-criteria", plan.source_plan.object_id, node, "attempt.unpublished",
        plan.implementation_commit, (config_publication.materialization.materialization_id,), (publication.materialization,),
        (publication.logical,), (ReceiptCheck("original-full64-factorial-criteria-freeze", True, ()),), OperationalStatus.SUCCEEDED, ())
    prior = RecursivePriorExecutionBinding("binding.unpublished.original-execution",
        _pin("issue.unpublished", "empirical-lawhood/runtime/issued-executable-study-manifest"),
        _pin("execution.unpublished", "empirical-lawhood/planning/study-operation-authority"),
        _pin("package.unpublished", "empirical-lawhood/api/experiment-package"), ObjectIdentity.from_record(plan.execution_plan_id, plan),
        receipt.run_id, receipt.task_id, ObjectIdentity.from_record(receipt.receipt_id, receipt), publication.logical.logical_artifact_id,
        criteria.identity)
    return method.ScheduledFactorialCriteriaBinding("binding.unpublished.original-criteria", criteria, publication, receipt,
        _publication(receipt, "original-receipt"), plan, _publication(plan, "original-plan"), config_publication, prior)


@pytest.fixture(scope="module")
def selected(criteria):
    binding = _binding(criteria)
    programme, specification = criteria.configuration.programme, criteria.configuration.specification
    acquisitions = tuple(method.ScheduledFactorialAcquisitionLocator(wave.wave_id, "run.unpublished."+wave.wave_id,
        _pin("issue.unpublished."+wave.wave_id, "empirical-lawhood/runtime/issued-executable-study-manifest"),
        _pin("execution.unpublished."+wave.wave_id, "empirical-lawhood/planning/study-operation-authority"),
        _pin("package.unpublished."+wave.wave_id, "empirical-lawhood/api/experiment-package"),
        _pin("plan.unpublished."+wave.wave_id, ExecutionPlan.SCHEMA)) for wave in programme.waves)
    config = method.ScheduledFactorialConfirmationConfig("config."+method.assess_node_id(specification), programme, specification,
        programme.bank, binding, acquisitions, None, None)
    root = declared_root(programme)
    budget = ResourceBudget(1, 256*1024**2, 0, 30, 64*1024**2, 16*1024**2)
    aggregate = ResourceBudget.aggregate((budget, budget))
    clock = replace(root.system.clocks[0], clock_id=programme.cases[0].information_cutoff.clock_id)
    system = replace(root.system, clocks=tuple(sorted((*root.system.clocks, clock), key=lambda row: row.clock_id)),
        authority_policy=replace(root.system.authority_policy, budget_ceiling=aggregate))
    campaign = replace(root.campaign, nodes=tuple(replace(node,
        object_identity=ObjectIdentity.from_record(root.experiment.experiment_id, root.experiment))
        if node.object_identity.object_id == root.experiment.experiment_id else replace(node,
        object_identity=ObjectIdentity.from_record(system.system_id, system))
        if node.object_identity.object_id == system.system_id else node for node in root.campaign.nodes))
    root = replace(root, system=system, campaign=campaign, resource_ceiling=aggregate)
    template = root.design_inputs[0]
    pins = (specification.identity, criteria.identity, ObjectIdentity.from_record(binding.receipt.receipt_id, binding.receipt), binding.identity)
    designs = tuple(sorted((*root.design_inputs, *(replace(template, input_id="design.unpublished.seal."+str(index),
        object_identity=pin, materialization_sha256=pin.object_fingerprint, role=DesignInputRole.READINESS_METADATA,
        physical_unit_ids=(), seed_ids=())
        for index, pin in enumerate(pins))), key=lambda row: row.input_id))
    root = replace(root, design_inputs=designs, design_origin=replace(root.design_origin,
        declared_input_ids=tuple(row.input_id for row in designs)))
    bank = ArtifactIdentity(programme.bank.object_id, "unpublished-original-bank-metadata", programme.bank.object_schema,
        programme.bank.object_fingerprint, "application/json", 1)
    lowered = composition.lower_factorial_confirmation(root=root, criteria=binding, acquisitions=acquisitions,
        bank_artifact=bank, operational_budget=budget)
    return SimpleNamespace(config=config, binding=binding, root=root, bank=bank, lowered=lowered)


def _catalog():
    declarations = method.operation_declarations()
    return (tuple(row.registration() for row in declarations), CapabilityRegistry("registry.unissued.factorial-seal",
        tuple(sorted((row.manifest() for row in declarations), key=lambda row: row.registry_id))),
        {schema: codec for row in declarations for schema, codec in row.record_codecs.items()})


def _qualified_projection(selected):
    """Hypothetical source association metadata only, never an issue credential."""
    draft = selected.lowered.draft
    root, reference = draft.prospective_draft, _fixture()[1].qualifications[0]
    records = dict(selected.lowered.input_records)
    materials, qualifications = [], []
    for index, external in enumerate(draft.external_inputs):
        version = selected.config.bank.object_version if external.logical_artifact_id == selected.config.bank.object_id else records[external.logical_artifact_id].VERSION
        pin = ObjectIdentity(external.logical_artifact_id, external.payload_schema, version, external.expected_content_sha256)
        q = replace(reference, receipt_id="qualification.unpublished.seal."+str(index), source_id=external.input_id,
            materialization=pin, content_sha256=pin.object_fingerprint, outcome_access=external.outcome_access,
            visibility_ceiling=external.visibility_ceiling, clock_ids=tuple(row.clock_id for row in root.system.clocks))
        qualifications.append(q)
        materials.append(SourceMaterializationRef(external.input_id, SourceMaterializationRole.OBSERVATION_STREAM,
            root.system.world.world_id, pin, pin.object_fingerprint, pin.object_fingerprint, q.observation_operator,
            q.numerical_view_ids, ObjectIdentity.from_record(q.receipt_id, q), SourceAccessDisposition.VERIFIED_ACCESS))
    return replace(draft, prospective_draft=replace(root, source_materializations=tuple(sorted(materials,
        key=lambda row: row.source_id)))), tuple(sorted(qualifications, key=lambda row: row.receipt_id))


def test_real_compiler_config_projection_is_an_optional_constraint_and_original_publication_stays_exact(criteria):
    binding = _binding(criteria)
    spec, = binding.execution_plan.tasks[0].external_inputs
    assert spec == _config_input(binding.execution_plan.tasks[0].capability.config)
    assert (spec.expected_size_bytes, spec.expected_media_type, spec.expected_outcome_access, spec.expected_visibility_ceiling) == (None,)*4
    custody.validate_criteria_binding(binding)
    assert binding.configuration_publication.logical.outcome_access is Access.OUTCOME_BLIND


@pytest.mark.parametrize("change", ({"expected_size_bytes": 1}, {"expected_media_type": "text/plain"},
    {"expected_outcome_access": Access.DEVELOPMENT_VISIBLE}, {"expected_visibility_ceiling": Visibility.DEVELOPMENT_ONLY},
    {"expected_payload_schema": "empirical-lawhood/testing/foreign"}, {"expected_content_sha256": "3"*64}))
def test_original_criteria_binding_rejects_each_explicit_wrong_compiled_config_constraint(criteria, change):
    with pytest.raises(ValueError, match="blind configuration"):
        _binding(criteria, config_spec_change=change)


@pytest.mark.parametrize("damage", (None, "size", "media", "access", "visibility", "observed-access", "raw-bytes"))
def test_original_config_reader_joins_actual_durable_blind_publication_to_compiler_projection(criteria, tmp_path, damage):
    binding = _binding(criteria)
    config, task = criteria.configuration, binding.execution_plan.tasks[0]
    run_id = binding.receipt.run_id
    plane = _plane(tmp_path / "bounded-config-custody")
    publication = plane.write(ArtifactWriteRequest(task.capability.config.artifact_id,
        f"runs/{run_id}/inputs/{task.capability.config.artifact_id}.bin", config.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "publication.unissued.original-config", f"runs/{run_id}/inputs", config.canonical_bytes(),
        Visibility.PROSPECTIVE, (), Access.EVALUATION_SEALED if damage == "observed-access" else Access.OUTCOME_BLIND))
    spec, = task.external_inputs
    changes = {"size": {"expected_size_bytes": publication.materialization.size_bytes+1},
        "media": {"expected_media_type": "text/plain"}, "access": {"expected_outcome_access": Access.DEVELOPMENT_VISIBLE},
        "visibility": {"expected_visibility_ceiling": Visibility.DEVELOPMENT_ONLY}}
    if damage in changes:
        task = replace(task, external_inputs=(replace(spec, **changes[damage]),))
    if damage == "raw-bytes":
        path = plane.root.resolve(publication.materialization.relative_path, for_write=False)
        path.write_bytes(config.canonical_bytes()+b" ")
    if damage is None:
        actual, observed = api._original_config(plane, run_id, task, type(config))
        assert actual == config and (observed.logical, observed.materialization) == (publication.logical, publication.materialization)
    else:
        with pytest.raises((ValueError, PermissionError, RuntimeError)):
            api._original_config(plane, run_id, task, type(config))


def test_seal_is_distinct_blind_metadata_and_lowerer_retains_original_criteria_full_census(selected):
    result, config = selected.lowered, selected.config
    seal = method.confirmation_input_seal(config)
    assert decode_canonical_bytes(seal.canonical_bytes(), type(seal), maximum_bytes=None) == seal
    assert seal.SCHEMA != method.ScheduledFactorialFrozenCriteria.SCHEMA
    assert seal.configuration.assessment == config and seal.configuration.criteria == selected.binding
    assert len(config.programme.cases) == 576 and len(config.programme.group_ids) == 64 and len(config.acquisitions) == 16
    assert len(seal.family_ids) == 12 and result.executable
    assert len(result.draft.operations) == 2
    blind = method.operation_declarations()[2]
    assert {port.port_id for port in blind.input_ports} == {"bank", "criteria", "programme", "specification"}
    assert all(value.outcome_access is Access.OUTCOME_BLIND for value in result.draft.external_inputs)
    internal, = (row for row in result.draft.links if row.consumer_input_id == "input-seal")
    assert (internal.producer_node_id, internal.producer_output_id, internal.external_input_id, internal.scientific_role) == (
        method.input_seal_node_id(config.specification), "product", None, "SOURCE")
    composition.validate_factorial_prospective_draft(config, result.draft, result.bank_artifact)
    bank = SimpleNamespace(SCHEMA=config.bank.object_schema, fingerprint=lambda: config.bank.object_fingerprint, canonical_bytes=lambda: b"x")
    public._assert_actual_declaration(result.draft, config.programme, bank, None,
        qualified_parent=config.criteria.record.configuration.qualified_parent)


def test_paired_reference_lowering_seals_exact_selection_without_reading_outcomes_or_imposing_carrier_ceiling(selected):
    references = {name: ArtifactIdentity("unpublished.paired."+name, "unpublished-outcome-reference", kind.SCHEMA,
        "5"*64, "application/json", size) for name, kind, size in (("reduction", api.ScheduledProgrammeReduction, 3*1024**2),
            ("data", api.ScheduledRevisionDataBank, 23*1024**2))}
    lowered = composition.lower_factorial_confirmation(root=selected.root, criteria=selected.binding,
        acquisitions=selected.config.acquisitions, bank_artifact=selected.bank,
        operational_budget=selected.lowered.draft.operations[0].resource_budget, **references)
    operation = next(row for row in lowered.draft.operations if row.config_identity.object_schema == method.ScheduledFactorialConfirmationConfig.SCHEMA)
    config = decode_canonical_bytes(operation.config_payload.encode(), method.ScheduledFactorialConfirmationConfig, maximum_bytes=None)
    composition.validate_factorial_prospective_draft(config, lowered.draft, selected.bank)
    assert {row.logical_artifact_id: row.maximum_size_bytes for row in lowered.draft.external_inputs
        if row.outcome_access is Access.EVALUATION_SEALED} == {row.artifact_id: row.size_bytes for row in references.values()}
    assert not any(record.SCHEMA in {api.ScheduledProgrammeReduction.SCHEMA, api.ScheduledRevisionDataBank.SCHEMA}
        for _, record in lowered.input_records)
    assert not any(row.consumer_node_id == method.input_seal_node_id(config.specification) and row.consumer_input_id in {"data", "reduction"}
        for row in lowered.draft.links)
    with pytest.raises(ValueError, match="paired artifact reference"):
        composition.lower_factorial_confirmation(root=selected.root, criteria=selected.binding,
            acquisitions=selected.config.acquisitions, bank_artifact=selected.bank,
            operational_budget=selected.lowered.draft.operations[0].resource_budget,
            reduction=references["reduction"], data=replace(references["data"], size_bytes=0))


def test_actual_prospective_candidate_and_unissued_plan_have_exact_typed_upstream_input_seal(selected):
    draft, qualifications = _qualified_projection(selected)
    registrations, registry, codecs = _catalog()
    compiled = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry, output_codecs=codecs,
        implementation_commit="d"*40, qualifications=qualifications, known_design_inputs=draft.prospective_draft.design_inputs)
    candidate = compiled.candidate_report.candidate
    assert candidate is not None, compiled.candidate_report.diagnostics
    plan = compile_run_plan(run_plan_id="run.unissued.factorial-seal", campaign=candidate.campaign, system=candidate.system,
        experiment=candidate.experiment, frozen_proposal=None, authorization=None, approval_service=None,
        template=candidate.protocol, registry=registry, implementation_commit="d"*40, scientific_graph=candidate.scientific_graph,
        candidate=ObjectIdentity.from_record(candidate.candidate_id, candidate), preissue_candidate=candidate)
    execution = lower_run_plan(plan, registry)
    assessing = next(row for row in execution.tasks if row.task_id == method.assess_node_id(selected.config.specification))
    assert assessing.dependency_task_ids == (method.input_seal_node_id(selected.config.specification),)
    dependency, = (row for row in assessing.scientific_inputs if row.producer_task_id is not None)
    assert dependency.payload_schema == method.ScheduledFactorialConfirmationInputSeal.SCHEMA
    assert all(output.payload_schema != method.ScheduledFactorialFrozenCriteria.SCHEMA for row in execution.tasks for output in row.outputs)
    with pytest.raises(ValueError, match="upstream freeze barrier"):
        replace(execution, tasks=(replace(assessing, dependency_task_ids=(), scientific_inputs=()),))


@pytest.mark.parametrize("change", ({"role": DesignInputRole.CLAIM_DERIVATION},
    {"outcome_access": Access.EVALUATION_SEALED}, {"visibility_ceiling": Visibility.DEVELOPMENT_ONLY},
    {"physical_unit_ids": ("observed.unpublished.unit",)}, {"seed_ids": ("observed.unpublished.seed",)},
    {"materialization_sha256": "4"*64}))
def test_original_criteria_readiness_pins_refuse_outcome_roles_visibility_and_observed_value_units(selected, change):
    identity = ObjectIdentity.from_record(selected.binding.receipt.receipt_id, selected.binding.receipt)
    root = selected.root
    root = replace(root, design_inputs=tuple(replace(row, **change) if row.object_identity == identity else row for row in root.design_inputs))
    with pytest.raises(PermissionError, match="not frozen in the original"):
        custody.require_original_criteria_design(root, selected.binding)


@pytest.mark.parametrize("damage", ("missing-dependency", "external-seal", "seal-config", "same-wave-criteria", "prior-receipt-pin", "locator-roster"))
def test_exact_lowerer_and_actual_compiler_refuse_seal_chronology_and_roster_changes(selected, damage):
    draft, qualifications = _qualified_projection(selected)
    if damage == "missing-dependency":
        draft = replace(draft, links=tuple(row for row in draft.links if row.consumer_input_id != "input-seal"))
    elif damage == "external-seal":
        edge = next(row for row in draft.links if row.consumer_input_id == "input-seal")
        draft = replace(draft, links=tuple(replace(row, producer_node_id=None, producer_output_id=None,
            external_input_id=draft.external_inputs[0].input_id) if row is edge else row for row in draft.links))
    elif damage in ("seal-config", "locator-roster"):
        operation = next(row for row in draft.operations if row.config_identity.object_schema == method.ScheduledFactorialConfirmationSealConfig.SCHEMA)
        config = method.confirmation_input_seal(selected.config).configuration
        if damage == "seal-config":
            altered = replace(config.assessment, acquisitions=tuple(replace(row, run_id="run.other."+row.wave_id) for row in config.assessment.acquisitions))
        else:
            with pytest.raises(ValueError, match="full acquisition roster"):
                replace(config.assessment, acquisitions=config.assessment.acquisitions[:-1])
            return
        changed = replace(config, assessment=altered)
        draft = replace(draft, operations=tuple(replace(row, config_payload=changed.canonical_bytes().decode())
            if row is operation else row for row in draft.operations))
    elif damage == "same-wave-criteria":
        draft = replace(draft, links=tuple(replace(row, producer_node_id=method.input_seal_node_id(selected.config.specification),
            producer_output_id="product", external_input_id=None)
            if row.consumer_node_id == method.assess_node_id(selected.config.specification) and row.consumer_input_id == "criteria"
            else row for row in draft.links))
    else:
        receipt = ObjectIdentity.from_record(selected.binding.receipt.receipt_id, selected.binding.receipt)
        root = draft.prospective_draft
        designs = tuple(row for row in root.design_inputs if row.object_identity != receipt)
        draft = replace(draft, prospective_draft=replace(root, design_inputs=designs,
            design_origin=replace(root.design_origin, declared_input_ids=tuple(row.input_id for row in designs))))
    with pytest.raises((ValueError, PermissionError)):
        composition.validate_factorial_prospective_draft(selected.config, draft, selected.bank)
    registrations, registry, codecs = _catalog()
    with pytest.raises((ValueError, PermissionError)):
        compile_recursive_wave(draft=draft, registrations=registrations, registry=registry, output_codecs=codecs,
            implementation_commit="d"*40, qualifications=qualifications, known_design_inputs=draft.prospective_draft.design_inputs)


def test_missing_same_plan_seal_refuses_before_any_original_custody_io(selected):
    supplier = SimpleNamespace(writer=SimpleNamespace())
    with pytest.raises(PermissionError, match="internal input-design seal dependency"):
        api._current_input_seal(supplier, object(), object(), selected.config, {})


@pytest.mark.parametrize("damage", ("expired", "changed-parent"))
def test_seal_rechecks_parent_after_all_blind_metadata_without_reading_confirmation_outcomes(selected, monkeypatch, damage):
    """Unpublished routing stubs test a refusal, never a prepared authority view."""
    config = method.confirmation_input_seal(selected.config).configuration
    events = []
    bank = object()
    values = {config.SCHEMA: config, api.ScheduledCompactBank.SCHEMA: bank,
        config.programme.SCHEMA: config.programme, config.specification.SCHEMA: config.specification, config.criteria.SCHEMA: config.criteria}
    controls = {config.config_id if schema == config.SCHEMA else "control."+str(index):
        SimpleNamespace(logical=SimpleNamespace(payload_schema=schema), materialization=SimpleNamespace(size_bytes=1))
        for index, schema in enumerate(values)}
    controls[config.bank.object_id] = controls.pop(next(key for key, value in controls.items()
        if value.logical.payload_schema == api.ScheduledCompactBank.SCHEMA))
    original = SimpleNamespace(run_plan_id="run.unpublished.original")
    package = SimpleNamespace(issued_study=SimpleNamespace(candidate=SimpleNamespace(authoring_package=
        SimpleNamespace(base=SimpleNamespace(draft=selected.root)))))
    supplier = SimpleNamespace(writer=object(), output_codecs={},
        _inputs=lambda *args: ({}, controls), _control=lambda manifest, *args: values[manifest.logical.payload_schema],
        _current=lambda *args: pytest.fail("changed parent reached handoff"))
    context = SimpleNamespace(config=SimpleNamespace(artifact_id=config.config_id), input_materialization_ids=(), dependency_receipt_ids=())
    parent = SimpleNamespace(declaration=config.criteria.record.configuration.qualified_parent.identity)
    def authenticate(*args):
        events.append("parent")
        if events.count("parent") == 1:
            return parent
        if damage == "expired":
            raise PermissionError("original qualified parent authority expired")
        return SimpleNamespace(declaration=_pin("parent.changed", parent.declaration.object_schema))
    def metadata(writer, locator, *args, **kwargs):
        events.append(locator.wave_id)
        return original, None, None, None, None, None, original
    def no_outcomes(*args, **kwargs):
        pytest.fail("blind input seal read confirmation outcome/recovery/reduction data")
    monkeypatch.setattr(api, "authenticate_programme_qualified_parent", authenticate)
    monkeypatch.setattr(api, "_ordinary_product", lambda *args: original)
    monkeypatch.setattr(api, "_wave_metadata", metadata)
    monkeypatch.setattr(api, "_live_package", lambda *args: original)
    for name in ("_wave", "_output_payload", "ExternalRunRecoveryStore", "reduce_programme", "validate_factorial_inputs"):
        monkeypatch.setattr(api, name, no_outcomes)
    with pytest.raises(PermissionError, match="expired|parent changed"):
        api._prepare_factorial_task(supplier, context, method.ScheduledFactorialProtectedWorker("seal"),
            (package, object(), object()), parent_writer=object(), parent_plan_reader=object())
    assert events == ["parent", *(row.wave_id for row in selected.config.acquisitions), "parent"]


@pytest.mark.parametrize("damage", (None, "seal-bytes", "prior-receipt", "roster", "missing-receipt", "wrong-check"))
def test_current_input_seal_authenticates_real_small_custody_and_exact_original_selection(selected, tmp_path, damage):
    """Unissued bounded files exercise custody joins; no worker is entered."""
    config = selected.config
    seal = method.confirmation_input_seal(config)
    if damage == "roster":
        changed = replace(config, acquisitions=tuple(replace(row, run_id="run.changed."+row.wave_id) for row in config.acquisitions))
        seal = method.confirmation_input_seal(changed)
    elif damage == "prior-receipt":
        receipt = replace(config.criteria.receipt, receipt_id="receipt.unpublished.altered-original")
        changed_binding = replace(config.criteria, receipt=receipt, receipt_publication=_publication(receipt, "altered-original-receipt"),
            prior_execution=replace(config.criteria.prior_execution, receipt=ObjectIdentity.from_record(receipt.receipt_id, receipt)))
        seal = method.confirmation_input_seal(replace(config, criteria=changed_binding))
    node, declaration = method.input_seal_node_id(config.specification), method.operation_declarations()[2]
    manifest = declaration.manifest()
    plane = _plane(tmp_path / "bounded-seal-custody")
    run_id = "run.unissued.input-seal"
    def publish(record, artifact_id, relative):
        return plane.write(ArtifactWriteRequest(artifact_id, relative, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            "application/json", "publication.unissued.input-seal", f"runs/{run_id}", record.canonical_bytes(),
            Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
    config_publication = publish(seal.configuration, seal.configuration.config_id,
        f"runs/{run_id}/inputs/{seal.configuration.config_id}.bin")
    product = publish(seal, "artifact.unissued.input-seal", f"runs/{run_id}/outputs/input-seal.json")
    config_ref = CapabilityConfigRef(seal.configuration.config_id, seal.configuration.SCHEMA, manifest.config_schema_sha256,
        seal.configuration.fingerprint(), config_publication.logical.logical_artifact_id)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, config_ref,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, manifest.maximum_evidence_ceiling,
        manifest.maximum_outcome_access, manifest.resource_ceiling)
    output = ArtifactOutputSpec(node+".product", product.logical.logical_artifact_id, product.materialization.relative_path,
        seal.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND)
    task = ExecutionTask(node, declaration.stage, requirement, manifest.implementation_sha256, (), (_config_input(config_ref),),
        (output,), (), declaration.execution_properties.barrier, 1, ("obligation.unissued.input-seal",), scientific_inputs=())
    plan = replace(selected.binding.execution_plan, execution_plan_id="plan.unissued.input-seal",
        source_plan=_pin(run_id, "empirical-lawhood/runtime/run-plan"), tasks=(task,))
    receipt = CanonicalTaskReceipt("receipt.unissued.input-seal", run_id, node, "attempt.unissued.input-seal", plan.implementation_commit,
        (config_publication.materialization.materialization_id,), (product.materialization,), (product.logical,),
        (ReceiptCheck("wrong-seal-check" if damage == "wrong-check" else "original-full64-factorial-confirmation-input-design-seal", True, ()),),
        OperationalStatus.SUCCEEDED, ())
    dependencies = {} if damage == "missing-receipt" else {node: receipt}
    if damage == "seal-bytes":
        plane.root.resolve(product.materialization.relative_path, for_write=False).write_bytes(seal.canonical_bytes()+b" ")
    from empirical_lawhood.api.matrix_scheduled_programme_runtime import ProgrammeRuntimeInputSupplier
    supplier = ProgrammeRuntimeInputSupplier(None, writer=plane, output_codecs={})
    context = SimpleNamespace(run_id=run_id)
    if damage is None:
        assert api._current_input_seal(supplier, context, plan, config, dependencies) == seal.identity
    else:
        with pytest.raises((ValueError, PermissionError, RuntimeError)):
            api._current_input_seal(supplier, context, plan, config, dependencies)
