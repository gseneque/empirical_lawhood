# SPDX-License-Identifier: MPL-2.0
"""In-memory original-producer controls; no real issue or custody is supplied."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import revision_calibration_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import revision_calibrated_future_bindings as future
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration_custody import validate_calibration_producer
from empirical_lawhood.api import matrix_revision_calibration_runtime as runtime
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactProfile, LogicalArtifactIdentity, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRegistry, CapabilityRequirement
from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
from empirical_lawhood.runtime.plans import (
    ArtifactOutputSpec, BarrierKind, ExecutionPlan, ExecutionTask, ExternalInputSpec, PlanLane, ScientificInputRole, ScientificInputSpec,
)
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
from tests.test_matrix_e4_revision_bindings import custody as seal_custody
from tests.test_matrix_revision_calibration import calibrated  # noqa: F401
from tests.test_matrix_programme_selection import exposed, pin  # noqa: F401
from tests.test_matrix_sampling_follow_on import prior_product
from tests.test_matrix_scheduled_programme_acquisition import declared_root


@pytest.fixture(scope="module")
def selected(calibrated):  # noqa: F811
    selected = owner.ScheduledRevisionCalibrationScope("scope.exposed.calibration-producer", calibrated.specification,
        owner.ScheduledRevisionFutureScope("scope.exposed.calibration-futures", calibrated.development,
            calibrated.nomination, calibrated.frozen, calibrated.programme))
    config = owner.ScheduledRevisionCalibrationConfig("config." + owner.calibration_task_id(selected.identity),
        selected.identity, pin("sources.exposed.calibration-producer", owner.ScheduledRevisionCalibrationSources.SCHEMA),
        calibrated.programme.bank, calibrated.programme.group_ids, calibrated.reduction.reduction_id,
        calibrated.data.bank_id, calibrated.result.record_id)
    return SimpleNamespace(scope=selected, config=config, inputs=owner.RevisionCalibrationInputs(
        calibrated.reduction, calibrated.data, calibrated.forecasts), original=calibrated)


def producer(selected):
    config = selected.config
    declaration, = owner.operation_declarations()
    manifest = declaration.manifest()
    task_id = owner.calibration_task_id(config.scope)
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), "input.exposed.revision-config")
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind,
        config_ref, manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions,
        declaration.evidence_ceiling, Access.EVALUATION_SEALED, declaration.resources)
    identities = (("config", config.identity, len(config.canonical_bytes())), ("scope", config.scope, len(selected.scope.canonical_bytes())),
        ("sources", config.sources, 1), ("bank", config.bank, 1))
    external, edges = [], []
    for name, identity, size in identities:
        artifact = config_ref.artifact_id if name == "config" else "input.exposed.revision-" + name
        access = Access.EVALUATION_SEALED if name == "config" else Access.OUTCOME_BLIND
        external.append(ExternalInputSpec("external." + name, artifact, identity.object_fingerprint, identity.object_schema,
            "application/json", size, Visibility.PROSPECTIVE, access, None))
        if name != "config":
            edges.append(ScientificInputSpec("edge." + name, name, ScientificInputRole.SOURCE, None, None,
                "external." + name, artifact, artifact, identity.object_schema, "application/json", size,
                access, Visibility.PROSPECTIVE, BarrierKind.NONE))
    output = ArtifactOutputSpec(task_id + ".product", "output.exposed.revision-calibration", "exposed/calibration.json",
        selected.original.result.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", Visibility.PROSPECTIVE, (), Access.EVALUATION_SEALED)
    task = ExecutionTask(task_id, declaration.stage, requirement, manifest.implementation_sha256, (), tuple(sorted(external, key=lambda value: value.input_id)),
        (output,), (), BarrierKind.NONE, 1, ("obligation.exposed.revision-calibration",), scientific_inputs=tuple(sorted(edges, key=lambda value: value.edge_id)))
    plan = ExecutionPlan("execution.exposed.calibration", PlanLane.PROSPECTIVE, pin("source.exposed.calibration"),
        "a"*64, "b"*40, (task,), True, candidate=pin("candidate.exposed.calibration"),
        issued_extension_set=pin("extensions.exposed.calibration", "empirical-lawhood/runtime/issued-extension-set"),
        execution_resource_envelope_spec=pin("resource.exposed.calibration", "empirical-lawhood/runtime/execution-resource-envelope-spec"),
        predevelopment_jit_signature_census=None, jit_graph_signature_manifest=None)
    root = declared_root(selected.original.programme)
    package = SimpleNamespace(issued_study=SimpleNamespace(candidate=SimpleNamespace(authoring_package=SimpleNamespace(base=SimpleNamespace(draft=root)))))
    generic = ArtifactGenericValidation("validation.exposed.calibration", "1.0.0", "c"*64, output.payload_schema, output.profile)
    logical = LogicalArtifactIdentity(output.logical_artifact_id, selected.original.result.fingerprint(), output.payload_schema,
        output.profile, output.media_type, output.visibility_ceiling, (), output.outcome_access, generic)
    binding = replace(prior_product(selected.original.result.identity).prior_execution,
        task_id=task_id, logical_artifact_id=logical.logical_artifact_id)
    receipt = SimpleNamespace(task_id=task_id, implementation_commit=plan.implementation_commit,
        checks=(ReceiptCheck(owner.CHECK, True, ()),), output_logical_artifacts=(logical,))
    return dict(config=config, binding=binding, package=package, execution_plan=plan, receipt=receipt, logical=logical)


def test_actual_typed_execution_plan_and_installed_calibration_producer_accept(selected):
    arguments = producer(selected)
    assert type(arguments["execution_plan"]) is ExecutionPlan
    assert not hasattr(arguments["execution_plan"], "world_kind")
    validate_calibration_producer(**arguments)
    actual = selected.inputs.assess(selected.config, selected.scope)
    assert actual == selected.original.result
    assert len(actual.group_ids) == len(actual.revision_scores) == len(actual.baseline_scores) == 64
    assert len(actual.forecasts) == 576 and actual.rank == 62


@pytest.mark.parametrize("damage", ("key", "version", "implementation", "access", "schema", "configuration", "source", "unit", "input", "output"))
def test_original_producer_refuses_same_schema_relabelling_and_substitution(selected, damage):
    arguments = producer(selected)
    plan = arguments["execution_plan"]
    task, = plan.tasks
    if damage in ("key", "version", "access", "schema", "configuration"):
        changes = {"key": {"capability_key": "foreign.same-schema"}, "version": {"capability_version": "2.0.0"},
            "access": {"requested_outcome_access": Access.DEVELOPMENT_VISIBLE},
            "schema": {"config": replace(task.capability.config, config_schema="empirical-lawhood/testing/foreign-config")},
            "configuration": {"config": replace(task.capability.config, content_sha256="f"*64)}}[damage]
        task = replace(task, capability=replace(task.capability, **changes))
    elif damage == "implementation":
        task = replace(task, capability_implementation_sha256="f"*64)
    elif damage == "source":
        plan = replace(plan, implementation_commit="f"*40)
    elif damage == "unit":
        base = arguments["package"].issued_study.candidate.authoring_package.base
        base.draft = replace(base.draft, evaluation_unit_ids=base.draft.evaluation_unit_ids[:-1])
    elif damage == "input":
        task = replace(task, external_inputs=task.external_inputs[:-1])
    else:
        arguments["logical"] = replace(arguments["logical"], content_sha256="f"*64)
    arguments["execution_plan"] = replace(plan, tasks=(task,))
    with pytest.raises(PermissionError):
        validate_calibration_producer(**arguments)


def test_actual_calibration_method_retains_missing_groups_as_unbounded_not_complete_cases(selected):
    missing = set(selected.original.programme.group_ids[:3])
    data = replace(selected.inputs.data, cases=tuple(value for value in selected.inputs.data.cases
        if next(case for case in selected.original.programme.cases if case.root_id == value.root_id).independent_group_id not in missing))
    actual = replace(selected.inputs, data=data).assess(selected.config, selected.scope)
    assert len(actual.group_ids) == 64 and len(actual.forecasts) == 576
    assert sum(value is None for _, value in actual.revision_scores) == 3
    assert actual.revision_radius is actual.baseline_radius is None


@pytest.mark.parametrize("damage", ("score", "forecast", "data-identity", "reduction-identity"))
def test_original_scientific_score_or_frozen_prediction_substitution_refuses(selected, damage):
    inputs = selected.inputs
    if damage == "score":
        first, *rest = inputs.data.cases
        changed = replace(first, score=replace(first.score, source=pin("source.foreign", first.score.source.object_schema,
            first.score.source.object_version)))
        inputs = replace(inputs, data=replace(inputs.data, cases=(changed, *rest)))
    elif damage == "forecast":
        first, *rest = inputs.forecasts
        inputs = replace(inputs, forecasts=(replace(first, revision_predictions=(first.revision_predictions[0] + 1, *first.revision_predictions[1:])), *rest))
    elif damage == "data-identity":
        inputs = replace(inputs, data=replace(inputs.data, bank_id="data.foreign"))
    else:
        inputs = replace(inputs, reduction=replace(inputs.reduction, reduction_id="reduction.foreign"))
    with pytest.raises(ValueError):
        inputs.assess(selected.config, selected.scope)


def test_three_new_factories_build_actual_installed_manifest_bound_runners():
    factories = (*owner.operation_factories(), *future.operation_factories())
    for factory in factories:
        registry = CapabilityRegistry("registry.exposed.revision", (factory.manifest,))
        provider = factory.build_provider(registry=registry, records=(), platform_ports=(ExecutablePlatformPort(
            factory.binding.required_platform_port_keys[0], RecursiveOperationInputPort(SimpleNamespace(resolve_input=lambda _: None,
                prepare_revision_future=lambda *_args, **_kwargs: None,
                prepare_revision_calibration=lambda *_args, **_kwargs: None))),))
        runner, = provider.runners(registry)
        assert runner.manifest == factory.manifest
        assert provider.runner_preparation_factory is not None


def test_calibration_preparation_uses_actual_parent_supplier_without_entering_custody_at_discovery(monkeypatch):
    from empirical_lawhood.api.matrix_scheduled_programme_runtime import ProgrammeRuntimeInputSupplier

    calls = []
    supplier = ProgrammeRuntimeInputSupplier(SimpleNamespace(), writer=None, output_codecs={})
    runner = owner.ScheduledRevisionCalibrationWorker()
    monkeypatch.setattr(runtime, "prepare_revision_calibration",
        lambda actual_supplier, context, actual_runner: calls.append((actual_supplier, context, actual_runner)) or runner)
    prepared = owner.prepare_for_invocation(supplier, runner)
    assert calls == [] and prepared.manifest == runner.manifest and not prepared.native_effect
    context = object()
    assert prepared.prepare_execution(context) is runner
    assert calls == [(supplier, context, runner)]


def test_calibration_preparation_refuses_missing_parent_supplier_callback():
    with pytest.raises(PermissionError, match="actual current and original issued custody"):
        owner.prepare_for_invocation(SimpleNamespace(), owner.ScheduledRevisionCalibrationWorker())


def test_current_authority_refusal_precedes_any_original_calibration_read(monkeypatch):
    monkeypatch.setattr(runtime.CurrentIssuedTaskCustody, "current_task", lambda *_: (_ for _ in ()).throw(PermissionError("no current grant")))
    monkeypatch.setattr(runtime, "reconstruct_revision_calibration", lambda **_: pytest.fail("original source was read"))
    supplier = SimpleNamespace(writer=None, reveal_authority_id=None)
    with pytest.raises(PermissionError, match="no current grant"):
        runtime.prepare_revision_calibration(supplier, object(), owner.ScheduledRevisionCalibrationWorker())


def test_unprepared_calibration_worker_refuses_before_input_reads():
    class ForbiddenPort:
        def close(self):
            pass
        def read(self, *_):
            pytest.fail("unprepared worker read an input")
    with pytest.raises(PermissionError, match="actual issued"):
        owner.ScheduledRevisionCalibrationWorker().execute(SimpleNamespace(prepared_invocation=None, input_ports=(ForbiddenPort(),)))


def test_closed_calibration_sources_reject_mutable_or_incomplete_outer_census():
    with pytest.raises(ValueError, match="exactly16"):
        owner.ScheduledRevisionCalibrationSources("sources.exposed", [], ())


def test_reconstructed_input_view_rejects_mutable_forecasts(selected):
    with pytest.raises(TypeError, match="immutable reconstructed"):
        replace(selected.inputs, forecasts=list(selected.inputs.forecasts))


def test_calibrated_native_variants_keep_original_mathematical_and_native_work_owners():
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import revision_future_bindings as original
    old = {value.registration.selection.capability_key.rsplit(".", 1)[-1]: value for value in original.operation_factories()}
    for factory in future.operation_factories():
        role = factory.manifest.capability_key.rsplit(".", 1)[-1]
        assert factory.registration.config_record_type is old[role].registration.config_record_type
        assert factory.registration.native_work_preparer is old[role].registration.native_work_preparer
        assert factory.registration.native_effect
        assert {value.port_id for value in factory.registration.input_ports} - {value.port_id for value in old[role].registration.input_ports} == {
            "revision-calibration-custody"}


def test_actual_native_seal_custody_remains_public_and_bound_to_one_original_case(selected):
    custody = seal_custody(selected.scope.future)
    assert custody.forecast == selected.scope.future.forecast(custody.forecast.case_id, record_id=custody.forecast.record_id)
    with pytest.raises(ValueError):
        replace(custody, forecast=replace(custody.forecast, source=pin("source.foreign", custody.forecast.source.object_schema,
            custody.forecast.source.object_version)))
