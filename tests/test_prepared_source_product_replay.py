# SPDX-License-Identifier: MPL-2.0
"""Owning-source replay and pure worker controls, never scientific qualification.

The generic controls use actual stored software issue/receipt owners. The gate
controls disclose an unissued mathematical source and exact parent metadata;
they exercise no native acquisition or original source admission.
"""
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_qualified_parents as replay
from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader
from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
from empirical_lawhood.adapters.reference_worlds.runtime import ReferenceAdjudicationFixture
from tests.runtime_platform.test_recursive_compiler import Config
from tests.test_issued_original_input_scope import _DisclosedOriginalScope
from tests.test_issued_provider_input_custody import completed  # noqa: F401


def _binding(control, plan, closure):
    # This actual fixture's adjudication_id is outside the prior-product
    # contract. Select its real Config output with the supported config_id;
    # the complete replay still includes the sealed adjudication sibling.
    outputs = tuple((receipt, logical) for task_id, receipt in sorted(closure.by_task.items())
        for logical in receipt.output_logical_artifacts if logical.payload_schema == Config.SCHEMA
        and logical.outcome_access is OutcomeAccess.OUTCOME_BLIND)
    assert outputs
    receipt, logical = outputs[0]
    physical, = (value for value in receipt.output_materializations
        if value.logical_artifact_id == logical.logical_artifact_id)
    raw = control.plane.root.resolve(physical.relative_path, for_write=False).read_bytes()
    record = decode_canonical_bytes(raw, Config, maximum_bytes=physical.size_bytes)
    assert record.canonical_bytes() == raw and record.fingerprint() == logical.content_sha256
    binding = RecursivePriorExecutionBinding("binding.disclosed.owned-source-product",
        ObjectIdentity.from_record(control.package.issued_study.issue_id, control.package.issued_study),
        ObjectIdentity.from_record(control.package.execution_authority.authority_id, control.package.execution_authority),
        ObjectIdentity.from_record(control.package.package_id, control.package),
        ObjectIdentity.from_record(plan.execution_plan_id, plan), control.package.run_plan_id, receipt.task_id,
        ObjectIdentity.from_record(receipt.receipt_id, receipt), logical.logical_artifact_id,
        ObjectIdentity.from_record(record.config_id, record), record_id_field="config_id")
    return binding, receipt, logical, record


@pytest.mark.parametrize("missing", ("custody", "validator", "foreign-type"))
def test_owned_source_product_requires_the_paired_exact_context_before_any_storage(tmp_path, monkeypatch, missing):
    from tests.test_recursive_public_service import _plane
    plane = _plane(tmp_path / "paired-context")
    custody = CurrentIssuedTaskCustody(writer=plane)
    kwargs = {"product_custody": custody, "product_validator": lambda **_: None}
    kwargs["product_custody" if missing != "validator" else "product_validator"] = (
        SimpleNamespace() if missing == "foreign-type" else None)
    monkeypatch.setattr(plane, "read_manifest", lambda *_a, **_k: pytest.fail("unpaired context reached storage"))
    with pytest.raises(PermissionError, match="paired current custody"):
        replay._authenticate_prior_execution(None, plane, {}, scope_validator=lambda **_: None,
            parent_evidence=None, **kwargs)


@pytest.mark.parametrize("damage", ("none", "foreign-reader", "foreign-winner", "expired-before-body", "validator-verdict"))
def test_actual_retained_product_replay_keeps_winning_receipt_and_fresh_guard(completed, monkeypatch, damage):  # noqa: F811
    c = completed
    access = _DisclosedOriginalScope(c.plane)
    custody = CurrentIssuedTaskCustody(writer=c.plane, reveal_authority_id=c.reveal.authority_id,
        original_input_access=access)
    with c.plane.read_context() as controls:
        reader = CurrentResultPlanReader(controls)
        plan = reader.authenticate_execution_plan(package=c.package, issued=c.package.issued_study,
            run_id=c.package.run_plan_id)
        prefixes = tuple(sorted(value.capability_key for value in c.package.registry.capabilities))
        closure = reader.collect_receipt_closure(package=c.package, execution_plan=plan, reveal=None,
            capability_prefixes=prefixes)
        scope = replay._ParentReadScope(controls, plan_reader=reader)
        scope.closures[(c.package.fingerprint(), id(plan), None, prefixes)] = closure
        binding, expected_receipt, expected_logical, expected_record = _binding(c, plan, closure)
        codecs = {kind.SCHEMA: kind for kind in (Config, ScientificAdjudicationRecord, ReferenceAdjudicationFixture)}
        assert set(codecs) == {output.payload_schema for task in plan.tasks for output in task.outputs}
        called = []
        def validator(**kwargs):
            called.append(kwargs["receipt"])
            assert kwargs["receipt"] == expected_receipt
            assert kwargs["logical"] == expected_logical
            if damage == "expired-before-body":
                access.revoked = True
            return True if damage == "validator-verdict" else None
        with custody.retained_binding(package=c.package, execution_plan=plan, control_reader=reader,
                receipt_closure=closure, require_current_read=access.require_current):
            target = controls.read_manifest(expected_receipt.output_materializations[0].relative_path)
            if damage == "foreign-reader":
                scope = replay._ParentReadScope(controls)
            elif damage == "foreign-winner":
                binding = replace(binding, receipt=replace(binding.receipt, object_fingerprint="f" * 64))
            if damage in ("expired-before-body", "validator-verdict"):
                monkeypatch.setattr(replay, "_verify_receipt_closure",
                    lambda *_: pytest.fail("bad owner verdict/expired access reached scientific body verification"))
            kwargs = dict(scope_validator=lambda **_: None, parent_evidence=None, read_scope=scope,
                product_custody=custody, product_validator=validator)
            if damage == "none":
                result = replay._authenticate_prior_execution(binding, controls,
                    codecs, **kwargs)
                assert result.product.payload == expected_record.canonical_bytes()
                assert called == [expected_receipt]
                assert result.receipts == tuple(closure.by_task[key] for key in sorted(closure.by_task))
                assert custody.require_input_member(target) is None
            else:
                pattern = {"foreign-reader": "live retained", "foreign-winner": "successful original producing receipt",
                    "expired-before-body": "grant expired", "validator-verdict": "return None"}[damage]
                with pytest.raises(PermissionError, match=pattern):
                    replay._authenticate_prior_execution(binding, controls,
                        codecs, **kwargs)
                # Restore only the disclosed clock so context cleanup can prove
                # exact snapshots; no real authority record is changed.
                access.revoked = False


def test_guard_refresh_after_heavy_verification_precedes_direct_payload_open(tmp_path, monkeypatch):
    from empirical_lawhood.kernel.time import InformationCutoff, CausalPhase
    from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest, ArtifactProfile
    from decimal import Decimal
    from tests.test_recursive_public_service import _plane
    plane = _plane(tmp_path / "raw-open-boundary")
    record = InformationCutoff("cutoff.disclosed.owned-product", "clock.disclosed.owned-product",
        CausalPhase.PREPARATION, Decimal(0))
    publication = plane.write(ArtifactWriteRequest("output.disclosed.owned-product", "product.json", record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "disclosed-product", ".", record.canonical_bytes(),
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    receipt = SimpleNamespace(output_materializations=(publication.materialization,))
    state = {"current": True}
    def guard(manifest):
        assert (manifest.logical, manifest.materialization) == (publication.logical, publication.materialization)
        if not state["current"]:
            raise PermissionError("DISCLOSED_PRODUCT_ACCESS_EXPIRED")
    actual = plane.verify_manifest
    def verified(manifest, **kwargs):
        result = actual(manifest, **kwargs)
        state["current"] = False
        return result
    monkeypatch.setattr(plane, "verify_manifest", verified)
    monkeypatch.setattr(replay, "read_bounded_bytes", lambda *_a, **_k: pytest.fail("expired product raw body opened"))
    with pytest.raises(PermissionError, match="ACCESS_EXPIRED"):
        replay._output_payload(plane, receipt, publication.logical, publication.materialization.size_bytes,
            before_member=guard)


@pytest.fixture
def gate_case(tmp_path, confirmation, opportunity, monkeypatch):  # noqa: F811
    """Full exposed mathematical census and disclosed CONFIG-only ancestry.

    The eleven synthetic parents belong only to this CONFIG metadata control;
    they are not represented as actual E3/DEV parents of the exposed operands.
    NonCONFIG inputs retain their actual compiled authoring access pairs. The
    original metadata callback creates no E3/TRAIN grant or source admission.
    Current-issued scope/receipt lifetime is tested independently above.
    """
    from empirical_lawhood.adapters.methods import matrix_prepared_source_experiment as domain
    from empirical_lawhood.adapters.methods import matrix_prepared_source_bindings as gates
    from empirical_lawhood.api import matrix_prepared_source_runtime as runtime
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, lineage_parent_sort_key
    from tests.test_recursive_public_service import _plane
    from tests.test_matrix_prepared_source import prepared_bank, disclosed_certificate, prepared_public_case
    plane = _plane(tmp_path / "gate-contract")
    bank = prepared_bank(confirmation)
    case = prepared_public_case(tmp_path, bank, disclosed_certificate(bank, opportunity), plane)
    selection = case.selection
    config = gates.r.gate_configs(selection.scope)[0]
    records = domain.operands(selection)
    parents = tuple(sorted((ArtifactLineageParent(ObjectIdentity("parent.disclosed.gate." + str(index),
        "empirical-lawhood/testing/disclosed-original-parent", "1.0.0", format(index, "064x")),
        VisibilityCeiling.PROSPECTIVE if index < 8 else VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.EVALUATION_SEALED if index < 8 else OutcomeAccess.DEVELOPMENT_VISIBLE)
        for index in range(11)), key=lineage_parent_sort_key))
    state = {"current": True}
    def current():
        if not state["current"]:
            raise PermissionError("DISCLOSED_GATE_ORIGINAL_EXPIRED")
    def record_parents(value):
        return parents if type(value) is type(config) and value == config else ()
    access = SimpleNamespace(record_parents=record_parents, parents=parents, require_current=current)
    monkeypatch.setattr(runtime, "_prepared_gate_product_context", lambda **_: (current(), access)[1])
    declaration = gates.gate_declaration(config.gate_kind, bank.phase)
    return SimpleNamespace(plane=plane, selection=selection, config=config, records=records, parents=parents,
        state=state, access=access, declaration=declaration, runtime=runtime, gates=gates,
        produced_access=produced_access, case=case)


# The scientific fixture imports remain explicit: no project conftest mutation.
from tests.test_matrix_selected_protected import confirmation, transfer  # noqa: E402,F401
from tests.test_matrix_selected_opportunity import opportunity  # noqa: E402,F401


def _gate_invocation(f, *, config_damage=None):
    from empirical_lawhood.adapters.methods import matrix_prepared_source_experiment as domain
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_experiment import operand_access_from_authoring
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from empirical_lawhood.kernel.evidence import EvidenceCeiling, inherited_visibility
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, lineage_parent_sort_key
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
    from empirical_lawhood.runtime.execution import TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
    from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeInputContract, PreparedWorkerEnvironment
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
    from tests.worker_configuration_support import freeze_worker_configuration
    from tests.test_matrix_selected_protected_worker import MemoryReader
    run_id, task_id = "run.disclosed.prepared-gate", domain.node_id(f.selection.scope, f.config.gate_kind.value.lower())
    manifest = f.declaration.manifest()
    ports, contracts, specs, edges, published = [], [], [], [], {}
    operand_pairs = operand_access_from_authoring(operands=f.records, authoring=f.selection.authoring)
    for name, record in sorted({"config": f.config, **f.records}.items()):
        artifact = f.config.config_id if name == "config" else "operand.disclosed.prepared-gate." + name
        parents = f.access.record_parents(record)
        pair = (f.produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY, parents=parents)
            if name == "config" else operand_pairs[name])
        relative, scope, root = provider_input_location(f.plane, run_id, artifact)
        publication = f.plane.write(ArtifactWriteRequest(artifact, relative, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            "application/json", scope, root, record.canonical_bytes(), pair[1],
            tuple(row.visibility_ceiling for row in parents), pair[0], lineage_parents=parents))
        published[name] = publication
        binding = WorkerInputBinding(artifact, publication.materialization.materialization_id, record.SCHEMA,
            "application/json", len(record.canonical_bytes()), pair[1], pair[0], WorkerInputKind.EXTERNAL)
        ports.append(WorkerInputPort(binding, MemoryReader(record.canonical_bytes())))
        contracts.append(PreparedNativeInputContract(publication.logical, binding, record.fingerprint()))
        specs.append(ExternalInputSpec("external." + name, artifact, record.fingerprint(), record.SCHEMA,
            "application/json", len(record.canonical_bytes()), pair[1], pair[0], None))
        if name != "config":
            edges.append(ScientificInputSpec("edge.disclosed.prepared-gate." + name, name, ScientificInputRole.QUALIFICATION,
                None, None, "external." + name, artifact, artifact, record.SCHEMA, "application/json",
                len(record.canonical_bytes()), pair[0], pair[1], BarrierKind.NONE))
    access = OutcomeAccess.EVALUATION_SEALED
    visibility = inherited_visibility(tuple(row.visibility_ceiling for row in ports), access)
    config = CapabilityConfigRef(f.config.config_id, f.config.SCHEMA, manifest.config_schema_sha256,
        f.config.fingerprint(), f.config.config_id)
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, config,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.NON_PROMOTABLE,
        f.declaration.outcome_access, f.config.resource_budget)
    product = f.gates.r.validate_gate_operands(f.config, f.selection.scope, f.records)
    output = ArtifactOutputSpec(task_id + ".product", "output.disclosed.prepared-gate", "gate-result.json", product.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", visibility, tuple(row.visibility_ceiling for row in ports), access)
    task = ExecutionTask(task_id, f.declaration.stage, requirement, manifest.implementation_sha256, (), tuple(specs), (output,),
        (), BarrierKind.NONE, 1, ("obligation.disclosed.prepared-gate",), scientific_inputs=tuple(edges))
    task = freeze_worker_configuration(task)
    if config_damage is not None:
        task = replace(task, scientific_inputs=tuple(sorted((replace(row, edge_id="edge.foreign.prepared-config")
            if row.consumer_input_id == "config" else row for row in task.scientific_inputs),
            key=lambda row: row.edge_id)))
    inputs = tuple(sorted(ports, key=lambda row: row.artifact_id))
    output_port = WorkerOutputPort(output.output_id, output.payload_schema, output.profile, output.media_type, output.logical_artifact_id)
    packages = (("synthetic/disclosed-prepared-gate.py", "1" * 64),)
    implementation = RecursiveImplementationBinding(packages, sha256(canonical_json_bytes(packages)).hexdigest(), "2" * 64, "3" * 40, False)
    context = TaskContext(run_id, task_id, "attempt.disclosed.prepared-gate", config, tuple(row.binding for row in inputs), inputs,
        (output_port,), manifest.permissions, f.declaration.outcome_access, f.config.resource_budget, WorkerIsolationProfile.TRUSTED_LOCAL)
    plan = ObjectIdentity("plan.disclosed.prepared-gate", "empirical-lawhood/runtime/execution-plan", "1.0.0", "a" * 64)
    prepared = PreparedInvocationContract("prepared.disclosed.prepared-gate", manifest, implementation,
        PreparedWorkerEnvironment("/synthetic/python", "4" * 64, "/synthetic", ()), run_id, task_id, context.attempt_id,
        config, tuple(sorted(contracts, key=lambda row: row.artifact_id)), (output_port,), manifest.permissions,
        f.declaration.outcome_access, f.config.resource_budget, WorkerIsolationProfile.TRUSTED_LOCAL,
        execution_plan=plan, execution_task=ObjectIdentity.from_record(task_id, task), execution_task_record=task,
        required_input_artifact_ids=tuple(row.artifact_id for row in inputs))
    context = replace(context, prepared_invocation=prepared)
    output_parents = tuple(sorted((ArtifactLineageParent(ObjectIdentity.from_record(value.logical.logical_artifact_id, value.logical),
        value.logical.visibility_ceiling, value.logical.outcome_access) for value in published.values()), key=lineage_parent_sort_key))
    publication = f.plane.write(ArtifactWriteRequest(output.logical_artifact_id, output.relative_path, product.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "disclosed-gate-output", ".", product.canonical_bytes(), visibility,
        tuple(row.visibility_ceiling for row in output_parents), access, lineage_parents=output_parents))
    return SimpleNamespace(task=task, context=context, product=product, publication=publication, published=published,
        output_parents=output_parents)


@pytest.mark.parametrize("damage", ("none", "foreign-parents", "changed-frozen-input", "expired"))
def test_prepared_product_pair_comes_from_exact_config_all_operands_and_full_parent_census(gate_case, monkeypatch, damage):
    f, actual = gate_case, _gate_invocation(gate_case)
    task = actual.task
    if damage == "changed-frozen-input":
        task = replace(task, external_inputs=tuple(replace(row, expected_content_sha256="f" * 64)
            if row.logical_artifact_id == actual.published["bank"].logical.logical_artifact_id else row for row in task.external_inputs))
    reader = SimpleNamespace(writer=f.plane, execution_task=lambda **_: task)
    scope = SimpleNamespace(plan_reader=reader)
    custody = CurrentIssuedTaskCustody(writer=f.plane)
    facts = {(row.logical, row.materialization) for row in actual.published.values()}
    def member(manifest):
        f.access.require_current()
        if (manifest.logical, manifest.materialization) not in facts:
            raise PermissionError("DISCLOSED_UNKNOWN_INPUT_MEMBER")
    monkeypatch.setattr(custody, "require_input_member", member)
    if damage == "foreign-parents":
        # Change the disclosed selected parent census, retaining the actual
        # canonical input publication unchanged. No stale sidecar/publication
        # masks the exact complete-parent comparison under test.
        f.access.parents = (replace(f.parents[0], identity=replace(f.parents[0].identity,
            object_id="parent.foreign.disclosed-source")), *f.parents[1:])
    if damage == "expired":
        f.state["current"] = False
    # The owner validator must settle metadata before any scientific body hash.
    monkeypatch.setattr(f.plane, "verify_manifest", lambda *_a, **_k: pytest.fail("owner metadata check hashed a body"))
    binding = SimpleNamespace(task_id=task.task_id, run_id=actual.context.run_id,
        record=ObjectIdentity.from_record(actual.product.evidence_id, actual.product), record_id_field="evidence_id",
        scope_output_schema_ids=(), additional_output_schema_ids=())
    kwargs = dict(selection=f.selection, binding=binding, package=SimpleNamespace(run_plan_id=actual.context.run_id),
        execution_plan=object(), receipt=SimpleNamespace(task_id=task.task_id, run_id=actual.context.run_id),
        logical=actual.publication.logical, read_scope=scope, product_custody=custody)
    if damage == "none":
        assert f.runtime.validate_prepared_gate_product(**kwargs) is None
        assert len(actual.published) == len(f.records) + 1
        assert actual.published["config"].logical.lineage_parents == f.parents and len(f.parents) == 11
        assert actual.publication.logical.outcome_access is OutcomeAccess.EVALUATION_SEALED
    else:
        with pytest.raises(PermissionError, match="parent census|canonical config or scientific operand|EXPIRED"):
            f.runtime.validate_prepared_gate_product(**kwargs)


@pytest.mark.parametrize("damage", ("none", "foreign-config-edge"))
def test_actual_prepared_worker_accepts_its_sealed_frozen_config_and_refuses_substitution_before_body(gate_case, monkeypatch, damage):
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_workers
    f = gate_case
    actual = _gate_invocation(f, config_damage=None if damage == "none" else damage)
    assert actual.context.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
    config_port, = (row for row in actual.context.input_ports if row.artifact_id == f.config.config_id)
    assert config_port.outcome_access is OutcomeAccess.EVALUATION_SEALED
    runner = f.gates.MatrixPreparedSourceGateWorker(f.config.gate_kind, f.selection.bank.phase).with_prepared_scope(
        f.gates.PreparedMatrixSourceGateScope(actual.context.run_id, actual.task.task_id,
            f.config.identity, f.selection.scope.identity, f.selection.certificate.identity))
    if damage == "none":
        result = runner.execute(actual.context)
        assert result.outputs[0].payload == actual.product.canonical_bytes()
    else:
        monkeypatch.setattr(protected_prefix_workers, "_read", lambda *_a, **_k: pytest.fail("foreign CONFIG reached first body"))
        with pytest.raises(ValueError, match="CONFIGURATION"):
            runner.execute(actual.context)
