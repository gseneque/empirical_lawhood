# SPDX-License-Identifier: MPL-2.0
"""Pure custody boundaries and actual selected nomination replay.

The durable readers below are replaced only at their I/O boundary. Synthetic
descriptors establish neither original custody, qualification nor authority.
"""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity as science
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_bindings as method
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_development_product import MatrixSelectedDevelopmentProduct
from empirical_lawhood.api import current_task_custody as custody_owner
from empirical_lawhood.api import matrix_selected_opportunity_runtime as owner
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactManifest, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityPermission, CapabilityRegistry
from empirical_lawhood.runtime.input_access import validate_planned_input_access
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, DevelopmentRunPlan, PlanLane
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_selected_opportunity import opportunity, transfer, evidence_for, committed_evidence_for, literal_observations  # noqa: F401
from tests.test_matrix_selected_opportunity_workers import invocation
from tests.test_matrix_selected_package import reference
from tests.test_matrix_selected_protected import unpublished


def test_development_parent_requires_actual_current_task_before_any_original_or_scientific_read(monkeypatch):
    calls = []
    class RefusingCurrent:
        def current_task(self, context, runner):
            calls.append("actual-authored-development-task")
            raise PermissionError("actual authored packet absent")
        def task_inputs(self, *args):
            pytest.fail("refused current development task reached scientific input reads")
    supplier = object.__new__(owner.SelectedOpportunityRuntimeInputSupplier)
    supplier.custody = RefusingCurrent()
    monkeypatch.setattr(owner, "_authenticate_original_products", lambda *args: pytest.fail("original sealed read preceded current custody"))
    supplier.original_input_access = SimpleNamespace(require_current=lambda: calls.append("fresh-original-access"))
    declaration = next(row for row in method.operation_declarations() if row.capability_key == method.COMMITTED_DESIGN_KEY)
    with pytest.raises(PermissionError, match="actual authored packet"):
        supplier.prepare_selected_opportunity(SimpleNamespace(), declaration.runner_factory())
    assert calls == ["fresh-original-access", "actual-authored-development-task"]
    with pytest.raises(TypeError, match="actual retained"):
        custody_owner.CurrentDevelopmentTaskCustody(writer=object(), directory="unused", plan=object())


@pytest.mark.parametrize("changed", (None, "models", "calibration"))
def test_original_four_product_batch_keeps_exact_scientific_scope_and_parent_calibration(opportunity, monkeypatch, changed):  # noqa: F811
    from empirical_lawhood.api import matrix_sampling_runtime, matrix_selected_producer_scope
    from empirical_lawhood.api import matrix_prepared_original_commitments
    projected = science.public_programme(opportunity)
    evidence, _ = committed_evidence_for(opportunity)
    package, writer, codecs = opportunity.point_design.package, object(), {}
    records = {science.identity(record): record for record in
        (package.models, package.model_freeze, package.calibration, package.calibrated_freeze)}
    calls = []
    def batch(actual_writer, originals, actual_codecs, *, scope_validator):
        assert actual_writer is writer and actual_codecs is codecs
        assert originals == tuple((product, product.record) for product in evidence.upstream_products)
        assert len(originals) == 4
        assert scope_validator.func is matrix_selected_producer_scope.validate_selected_original_producer
        assert scope_validator.keywords == {"programme": projected}
        calls.append("one-complete-original-custody-batch")
        result = []
        for product, _ in originals:
            record = records[product.record]
            if changed == "calibration" and record is package.calibration:
                record = replace(record, record_id="calibration.foreign")
            raw = record.canonical_bytes()
            if changed == "models" and record is package.models:
                raw = b"foreign original model bytes"
            result.append(raw)
        return tuple(result)
    expected_commitment_call = (writer, projected, evidence, 128 * 1024**2)
    def commitments(*, writer, programme, evidence, source_scan_bytes):
        assert (writer, programme, evidence, source_scan_bytes) == expected_commitment_call
        calls.append("current-original-commitments")
    monkeypatch.setattr(matrix_prepared_original_commitments, "authenticate_prepared_original_commitments", commitments)
    monkeypatch.setattr(matrix_sampling_runtime, "_original_products", batch)
    if changed is None:
        assert owner._authenticate_original_products(writer, projected, evidence, codecs, source_scan_bytes=128 * 1024**2) == opportunity
        assert b'"scores"' not in projected.canonical_bytes()
    else:
        with pytest.raises(PermissionError, match="actual original"):
            owner._authenticate_original_products(writer, projected, evidence, codecs, source_scan_bytes=128 * 1024**2)
    assert calls == ["current-original-commitments", "one-complete-original-custody-batch"]


def test_new_entry_requires_original_commitments_before_any_original_product_read(opportunity, monkeypatch):  # noqa: F811
    from empirical_lawhood.api import matrix_sampling_runtime

    monkeypatch.setattr(matrix_sampling_runtime, '_original_products',
        lambda *args, **kwargs: pytest.fail('missing commitments reached original outcomes'))
    with pytest.raises(ValueError, match='Original commitment evidence is missing'):
        owner._authenticate_original_products(object(), science.public_programme(opportunity), evidence_for(opportunity), {}, source_scan_bytes=128 * 1024**2)


def test_typed_synthetic_commitments_require_the_actual_training_publication(opportunity, monkeypatch):  # noqa: F811
    from empirical_lawhood.api import matrix_prepared_source_runtime, matrix_sampling_runtime
    from tests.matrix_selected_commitment_fixture import unpublished_committed_evidence

    evidence = unpublished_committed_evidence(evidence_for(opportunity))
    observed = []
    def absent_training(writer, locator):
        assert locator == evidence.original_commitments.native_training_locator
        observed.append(locator)
        raise PermissionError('actual native TRAIN publication is absent')
    monkeypatch.setattr(matrix_prepared_source_runtime, '_native_training_prerequisite', absent_training)
    monkeypatch.setattr(matrix_sampling_runtime, '_original_products',
        lambda *args, **kwargs: pytest.fail('unpublished training commitments reached original outcomes'))
    with pytest.raises(PermissionError, match='native TRAIN publication is absent'):
        owner._authenticate_original_products(object(), science.public_programme(opportunity), evidence, {}, source_scan_bytes=128 * 1024**2)
    assert observed == [evidence.original_commitments.native_training_locator]


def test_actual_design_custody_uses_raw_original_reader_and_rechecks_current_task(opportunity, monkeypatch):  # noqa: F811
    programme = science.public_programme(opportunity)
    evidence, parents = committed_evidence_for(opportunity)
    config = method.MatrixSelectedOpportunityRootConfigV2("config." + method.global_node(programme, "design"), programme, "design",
        evidence.identity, len(evidence.canonical_bytes()), parents)
    runner, context = invocation(config, {"evidence": evidence}, {})
    runner = owner.SelectedOpportunityWorker(runner.phase, runner.manifest)
    task = context.prepared_invocation.execution_task_record
    plan = DevelopmentExecutionPlan("plan.raw-development-originals.exposed", PlanLane.DEVELOPMENT,
        reference(context.run_id, DevelopmentRunPlan), "a" * 64, "b" * 40, (task,), True)
    config_publication = unpublished(config, "raw-development-config.exposed")
    evidence_publication = unpublished(evidence, "raw-development-evidence.exposed")
    controls = {context.config.artifact_id: config_publication, "evidence": evidence_publication}
    records = {config.SCHEMA: config, evidence.SCHEMA: evidence}
    reads, original_reads, writer = [], [], object()
    class CurrentCustody:
        def current_task(self, selected_context, selected_runner):
            assert selected_context is context and selected_runner is runner
            reads.append("fresh-current-task")
            return None, plan, task
        def task_inputs(self, selected_context, selected_task):
            assert selected_context is context and selected_task is task
            return {}, controls
        def control_record(self, manifest, kind, maximum_bytes):
            assert maximum_bytes == manifest.materialization.size_bytes
            return records[kind.SCHEMA]
    def originals(actual_writer, actual_programme, actual_evidence, codecs, *, source_scan_bytes, current_access):
        assert actual_writer is writer and actual_programme == programme and actual_evidence == evidence
        assert source_scan_bytes == context.resource_budget.source_scan_bytes and current_access is None
        assert actual_evidence.original_commitments == evidence.original_commitments
        original_reads.append("raw-original-authentication")
        return opportunity
    monkeypatch.setattr(owner, "_authenticate_original_products", originals)
    supplier = object.__new__(owner.SelectedOpportunityRuntimeInputSupplier)
    supplier.writer, supplier.output_codecs, supplier.custody = writer, {}, CurrentCustody()
    supplier.design_task, supplier.design_config = task, config
    supplier.current_access = None
    supplier.original_input_access = SimpleNamespace(require_current=lambda: reads.append("fresh-original-access"))
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative import derivation
    def require_parents(actual_writer, actual_parents, actual_evidence, *, read_access):
        assert actual_writer is writer and actual_parents == parents and actual_evidence == evidence
        assert read_access is None
        original_reads.append("exact-produced-parent-census")
    monkeypatch.setattr(derivation, "require_evidence_produced_input_parents", require_parents)
    prepared = supplier.prepare_selected_opportunity(context, runner)
    assert prepared.prepared_scope == (context.run_id, context.task_id, context.input_materialization_ids,
        ObjectIdentity.from_record(plan.execution_plan_id, plan))
    assert reads == ["fresh-original-access", "fresh-current-task", "fresh-current-task", "fresh-original-access"]
    assert original_reads == ["raw-original-authentication", "exact-produced-parent-census"]


@pytest.mark.parametrize("changed", (None, "package", "design", "programme"))
def test_development_parent_reconstructs_actual_original_calibration_only_in_parent(opportunity, changed):  # noqa: F811
    projected = science.public_programme(opportunity)
    if changed == "package":
        package = projected.point_design.package
        projected = replace(projected, point_design=replace(projected.point_design,
            package=replace(package, original_package=replace(package.original_package, object_fingerprint="f" * 64))))
    elif changed == "design":
        design = projected.point_design
        projected = replace(projected, point_design=replace(design, original_design=replace(design.original_design, object_fingerprint="f" * 64)))
    elif changed == "programme":
        projected = replace(projected, original_programme=replace(projected.original_programme, object_fingerprint="f" * 64))
    if changed is None:
        assert owner.reconstruct_opportunity_programme(projected, opportunity.point_design.package.calibration) == opportunity
        assert b'"scores"' not in projected.canonical_bytes()
    else:
        with pytest.raises(PermissionError, match="original.*package"):
            owner.reconstruct_opportunity_programme(projected, opportunity.point_design.package.calibration)


@pytest.mark.parametrize("changed", (None, "run", "manifest", "plan"))
def test_current_development_task_matches_exact_typed_run_manifest_and_plan(opportunity, changed):  # noqa: F811
    programme = science.public_programme(opportunity)
    evidence, parents = committed_evidence_for(opportunity)
    config = method.MatrixSelectedOpportunityRootConfigV2("config." + method.global_node(programme, "design"), programme, "design",
        evidence.identity, len(evidence.canonical_bytes()), parents)
    runner, context = invocation(config, {"evidence": evidence}, {})
    task = context.prepared_invocation.execution_task_record
    plan = DevelopmentExecutionPlan("plan.current-development.exposed", PlanLane.DEVELOPMENT,
        reference(context.run_id, DevelopmentRunPlan), "a" * 64, "b" * 40, (task,), True)
    prepared = replace(context.prepared_invocation, execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan))
    context = replace(context, prepared_invocation=prepared)
    # Isolate fresh task matching after the separately tested authenticated
    # constructor boundary; no durable read is substituted with a true flag.
    custody = object.__new__(custody_owner.CurrentDevelopmentTaskCustody)
    custody.plan, custody.run = plan, SimpleNamespace(run_plan_id=context.run_id)
    from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
    custody.index = DevelopmentRunRecoveryIndex.from_execution_plan(plan,
        run_id=context.run_id, wave_id='wave.exposed-development')
    custody.access_pair = (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    custody.packet = reference("packet.current-development.exposed", AuthoredRecursiveWave)
    publication = unpublished(config, "packet.current-development.exposed")
    custody.packet_manifest = ArtifactManifest(publication.logical, publication.materialization)
    custody._manifest = lambda relative: custody.packet_manifest
    if changed == "run":
        context = replace(context, run_id="run.foreign", prepared_invocation=None)
    elif changed == "manifest":
        runner = SimpleNamespace(manifest=replace(runner.manifest, implementation_sha256="f" * 64))
    elif changed == "plan":
        context = replace(context, prepared_invocation=replace(prepared, execution_plan=replace(prepared.execution_plan, object_fingerprint="f" * 64)))
    if changed is None:
        assert custody.current_task(context, runner) == (custody.packet, plan, task)
    else:
        with pytest.raises(PermissionError, match="actual|original"):
            custody.current_task(context, runner)


@pytest.fixture(scope="module")
def development_case(opportunity):  # noqa: F811
    declarations = method.operation_declarations()
    evidence, parents = committed_evidence_for(opportunity)
    lowered = method.lower_selected_opportunity(opportunity, evidence=evidence, campaign=campaign_fixture()[0].campaign,
        draft_id="draft.opportunity.original-producer.exposed", produced_input_parents=parents)
    registry = CapabilityRegistry("registry.opportunity.original-producer.exposed",
        tuple(sorted((row.manifest() for row in declarations), key=lambda value: value.registry_id)))
    compiled = compile_recursive_wave(draft=lowered.draft, registry=registry, registrations=tuple(row.registration() for row in declarations),
        implementation_commit="a" * 40, output_codecs={schema: kind for row in declarations for schema, kind in row.record_codecs.items()})
    observations = literal_observations(opportunity)
    _, nomination = science.nominate_selected_opportunity(opportunity, observations, result_id="nomination." + opportunity.fingerprint())
    task_id = method.global_node(opportunity, "nominate")
    publication = unpublished(nomination, "nomination.original-producer.exposed")
    publication = replace(publication, logical=replace(publication.logical, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY))
    receipt = CanonicalTaskReceipt("receipt.original-producer.exposed", compiled.run_plan.run_plan_id, task_id, "attempt.original-producer.exposed",
        "a" * 40, (), (publication.materialization,), (publication.logical,), (), OperationalStatus.SUCCEEDED, ())
    draft_pin = ObjectIdentity.from_record(lowered.draft.draft_id, lowered.draft)
    implementation = reference("implementation.original-producer.exposed", AuthoredRecursiveWave)
    packet = AuthoredRecursiveWave("packet.original-producer.exposed", draft_pin, implementation,
        (RecursiveWaveMember("draft.json", draft_pin, len(lowered.draft.canonical_bytes())), RecursiveWaveMember("implementation.json", implementation, 1)))
    binding = MatrixSelectedDevelopmentProduct("development.original-producer.exposed", "unpublished/opportunity", ObjectIdentity.from_record(packet.packet_id, packet),
        ObjectIdentity.from_record(compiled.run_plan.run_plan_id, compiled.run_plan), ObjectIdentity.from_record(compiled.execution_plan.execution_plan_id, compiled.execution_plan),
        receipt.run_id, task_id, ObjectIdentity.from_record(receipt.receipt_id, receipt), publication.logical.logical_artifact_id, nomination.identity, publication)
    records = {task_id: {task_id + ".product": nomination}}
    for case_id, values in observations.items():
        for phase, value in zip(("point", "mechanical", "response-score"), values, strict=True):
            node = method.NAMESPACE + "." + case_id.removeprefix("case.") + "." + phase
            records[node] = {node + ".product": value}
    products = {"receipts": {task_id: receipt}, "outputs": {publication.logical.logical_artifact_id: ArtifactManifest(publication.logical, publication.materialization)}, "records": records}
    return SimpleNamespace(programme=opportunity, compiled=compiled, packet=packet, binding=binding, nomination=nomination, products=products)


@pytest.mark.parametrize("changed", (None, "whole-groups", "receipt", "endpoint"))
def test_original_development_nomination_replays_exact_producer_and_numerical_outcomes(development_case, monkeypatch, changed):
    from empirical_lawhood.api import recursive_execution
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import commitment
    case = development_case
    # Explicit metadata/products seam; real producer checks and endpoint replay remain.
    source, index = object(), object()
    roots = (case.packet, case.compiled.draft, source, case.compiled.run_plan, case.compiled.execution_plan, index)
    reads = []
    products = case.products
    if changed == "receipt":
        receipt = products["receipts"][case.binding.task_id]
        products = {**products, "receipts": {case.binding.task_id: replace(receipt, receipt_id="receipt.foreign")}}
    elif changed == "endpoint":
        actual = replace(case.nomination, result_id="nomination.foreign")
        products = {**products, "records": {**products["records"], case.binding.task_id: {case.binding.task_id + ".product": actual}}}
    def complete_read(**kwargs):
        preflight = kwargs["validate_authored"](packet=case.packet, draft=case.compiled.draft,
            source=source, payloads={}, run=case.compiled.run_plan, plan=case.compiled.execution_plan, index=index)
        reads.append("supplied-development-products")
        result = ({"packet_sha256": case.packet.fingerprint()}, products, case.compiled.draft, case.compiled.execution_plan)
        return result, roots, preflight
    monkeypatch.setattr(recursive_execution, "_read_recursive_wave_with_roots", complete_read)
    monkeypatch.setattr(commitment, "authenticate_publication", lambda *args: reads.append("actual-original-nomination-publication"))
    writer = SimpleNamespace(root=SimpleNamespace(resolve=lambda *args, **kwargs: "unpublished/opportunity"))
    arguments = dict(writer=writer, binding=case.binding, package=case.programme.point_design.package, criterion=case.programme.criterion,
        nomination_pin=case.nomination.identity, expected_groups=16 if changed == "whole-groups" else 1)
    if changed is None:
        plan = case.compiled.execution_plan
        assert all(task.capability.requested_outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE for task in plan.tasks)
        history = next(task for task in plan.tasks if task.capability.capability_key == method.capability_key("history", "2.0.0"))
        assert all(output.outcome_access is OutcomeAccess.EVALUATION_REVEALED for output in history.outputs)
        assess = next(task for task in plan.tasks if task.capability.capability_key == method.capability_key("assess"))
        assert CapabilityPermission.READ_OUTCOME_VISIBLE in assess.capability.required_permissions
        unreadable = replace(assess, capability=replace(assess.capability, required_permissions=tuple(
            value for value in assess.capability.required_permissions if value is not CapabilityPermission.READ_OUTCOME_VISIBLE)))
        changed_plan = replace(plan, tasks=tuple(unreadable if task is assess else task for task in plan.tasks))
        with pytest.raises(ValueError, match="lacks read permission for planned input"):
            validate_planned_input_access(changed_plan)
        nomination, receipt, publication = owner.authenticate_selected_development_nomination(**arguments)
        assert nomination == case.nomination and receipt == case.products["receipts"][case.binding.task_id] and publication == case.binding.publication
        assert reads == ["supplied-development-products", "actual-original-nomination-publication"]
    else:
        with pytest.raises(PermissionError, match="scope|receipt|reduction|census"):
            owner.authenticate_selected_development_nomination(**arguments)
        if changed == "whole-groups":
            assert not reads
