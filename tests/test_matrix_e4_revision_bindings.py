# SPDX-License-Identifier: MPL-2.0
"""Pure actual-port E4 controls; synthetic metadata grants no effect authority."""

from dataclasses import replace
from io import BytesIO
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_acquisition_bindings as original
from empirical_lawhood.adapters.methods.matrix_scheduled_history import revision_forecast_bindings as forecast
from empirical_lawhood.adapters.methods.matrix_scheduled_history import revision_future_bindings as future
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_public import ScheduledRevisionPublicCalibration
from empirical_lawhood.api import matrix_revision_runtime
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import (
    ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, ArtifactWriteResult,
    CanonicalTaskReceipt, LogicalArtifactIdentity, ReceiptCheck,
)
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
from tests.test_matrix_e4_programme_workflow import complete  # noqa: F401
from tests.test_matrix_revision_calibration import calibrated  # noqa: F401
from tests.test_matrix_programme_selection import exposed, pin  # noqa: F401


class MemoryReader:
    def __init__(self, payload):
        self.payload, self.stream = payload, BytesIO(payload)
        self.bytes_read = 0

    def read(self, size=-1):
        result = self.stream.read(size)
        self.bytes_read += len(result)
        return result

    def cursor(self):
        return MemoryReader(self.payload)

    def close(self):
        self.stream.close()


def publication(record, logical_id):
    schema, digest = record.SCHEMA, record.fingerprint()
    validation = ArtifactGenericValidation("exposed.canonical", "1.0.0", "a" * 64, schema, ArtifactProfile.CANONICAL_JSON)
    logical = LogicalArtifactIdentity(logical_id, digest, schema, ArtifactProfile.CANONICAL_JSON, "application/json",
        future.PROSPECTIVE, (), future.BLIND, validation)
    physical = ArtifactMaterialization("materialization." + logical_id, logical_id, "exposed.memory", logical_id + ".json",
        digest, len(record.canonical_bytes()), "none")
    manifest = replace(physical, materialization_id="manifest." + logical_id, relative_path=logical_id + ".manifest.json")
    return ArtifactWriteResult(logical, physical, manifest, False)


def port(record, logical_id):
    raw = record.canonical_bytes()
    return WorkerInputPort(WorkerInputBinding(logical_id, "materialization." + logical_id, record.SCHEMA,
        "application/json", len(raw), future.PROSPECTIVE, future.BLIND, WorkerInputKind.EXTERNAL), MemoryReader(raw))


def scope(case):
    return future.ScheduledRevisionFutureScope("scope.e4.exposed", case.prior.development, case.prior.nomination,
        case.prior.frozen, case.programme, case.prior.programme,
        ScheduledRevisionPublicCalibration.from_calibration(case.prior.result), case.specification.nomination_rule)


def custody(selected):
    case = selected.programme.cases[0]
    seal = selected.forecast(case.root_id, record_id="forecast.exposed." + case.root_id)
    published = publication(seal, "published." + seal.record_id)
    task = future.forecast_task_id(case.root_id)
    receipt = CanonicalTaskReceipt("receipt.exposed.seal", "run.exposed.seal", task, "attempt.exposed.seal", "a" * 40, (),
        (published.materialization,), (published.logical,), (ReceiptCheck(future.SEAL_CHECK, True, ()),), OperationalStatus.SUCCEEDED, ())
    request = RecursivePriorExecutionBinding("prior.exposed.seal",
        pin("issued.exposed", "empirical-lawhood/runtime/issued-executable-study-manifest"),
        pin("grant.exposed", "empirical-lawhood/planning/study-operation-authority"),
        pin("package.exposed", "empirical-lawhood/api/experiment-package"), pin("plan.exposed", "empirical-lawhood/runtime/execution-plan"),
        receipt.run_id, task, ObjectIdentity.from_record(receipt.receipt_id, receipt), published.logical.logical_artifact_id, seal.identity)
    return future.ScheduledRevisionSealCustody("custody.e4.exposed", seal, published, receipt,
        publication(receipt, "published." + receipt.receipt_id), request)


def context(selected):
    case = selected.programme.cases[0]
    task = future.forecast_task_id(case.root_id)
    config = forecast.ScheduledRevisionForecastConfig("config." + task, selected.identity, case.root_id,
        case.independent_group_id, "forecast.exposed." + case.root_id)
    selected_manifest, = forecast.operation_manifests()
    ports = tuple(sorted((port(config, config.config_id), port(selected, selected.record_id)), key=lambda row: row.artifact_id))
    return TaskContext("run.exposed.e4", task, "attempt.exposed.e4",
        CapabilityConfigRef(config.config_id, config.SCHEMA, selected_manifest.config_schema_sha256, config.fingerprint(), config.config_id),
        tuple(row.binding for row in ports), ports,
        (WorkerOutputPort(task + ".product", future.ScheduledRevisionForecastSeal.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            "application/json", "published." + config.forecast_id),), selected_manifest.permissions, future.BLIND,
        forecast.core.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL)


def test_installed_additive_factories_keep_original_native_mathematical_configurations():
    originals = {row.registration.selection.capability_key.rsplit(".", 1)[-1]: row for row in original.operation_factories()}
    factories = future.operation_factories()
    assert len(factories) == 2
    for factory in factories:
        role = factory.manifest.capability_key.rsplit(".", 1)[-1]
        old = originals[role]
        assert factory.registration.native_effect and factory.registration.config_record_type is old.registration.config_record_type
        assert factory.registration.native_work_preparer is old.registration.native_work_preparer
        assert callable(factory.registration.native_effect_slot_ids) and callable(old.registration.native_effect_slot_ids)
        assert {row.port_id for row in factory.registration.input_ports} - {row.port_id for row in old.registration.input_ports} == {
            "revision-scope", "revision-seal", "revision-custody", "revision-seal-receipt"}
        assert factory.runner_preparation_factory is future.prepare_for_invocation


def test_installed_discovery_contains_the_actual_new_declarations():
    from empirical_lawhood.adapters.methods.matrix_scheduled_programme import executable_binding, extension_bundle
    expected = {row.manifest.capability_key for row in (*forecast.operation_factories(), *future.operation_factories())}
    assert expected <= {row.manifest.capability_key for row in executable_binding.EXECUTABLE_BINDING_FACTORIES}
    assert expected <= {row.capability_key for row in extension_bundle.MANIFESTS}


def test_actual_pure_forecast_worker_publishes_only_the_frozen_case_prediction(complete):  # noqa: F811
    selected = scope(complete)
    ctx = context(selected)
    factory, = forecast.operation_factories()
    result = factory.runner_factory().execute(ctx)
    assert result.outputs[0].payload == selected.forecast(selected.programme.cases[0].root_id,
        record_id="forecast.exposed." + selected.programme.cases[0].root_id).canonical_bytes()
    assert result.checks == (ReceiptCheck(future.SEAL_CHECK, True, ()),)
    assert all(row.bytes_read == 0 for row in ctx.input_ports)


def test_pure_seal_wave_declares_all_nine_cases_per_group_as_actual_operations(complete):  # noqa: F811
    from tests.test_matrix_scheduled_programme_acquisition import declared_root
    selected = scope(complete)
    wave = selected.programme.waves[0]
    tasks = tuple(future.forecast_task_id(case) for case in wave.root_ids)
    draft, operands = forecast.revision_forecast_draft(root=declared_root(selected.programme), scope=selected,
        wave_id=wave.wave_id, proof_owners=tuple(("obligation.exposed.e4", task) for task in tasks),
        operational_budgets={task: forecast.core.BUDGET for task in tasks}, draft_id="draft.exposed.e4.seals",
        forecast_prefix="forecast.exposed.e4")
    assert tuple(row.node_id for row in draft.operations) == tasks and len(tasks) == 36
    assert len(draft.external_inputs) == 1 and operands == {selected.record_id: selected}
    assert len(draft.links) == 36 and all(row.producer_node_id is None and row.consumer_input_id == "revision-scope" for row in draft.links)
    assert all(len(row.config_payload) < 1500 for row in draft.operations)


def test_confirmation_future_scope_independently_requires_separate_actual_calibration(complete):  # noqa: F811
    selected = scope(complete)
    with pytest.raises(ValueError, match="32DEV"):
        replace(selected, calibration_programme=None)
    with pytest.raises(TypeError, match="public calibration metadata"):
        replace(selected, calibration=None)
    with pytest.raises(ValueError, match="SCIENTIFIC_CHOICE"):
        replace(selected, nomination_rule=None)
    raw = selected.canonical_bytes()
    assert b'"revision_scores"' not in raw and b'"baseline_scores"' not in raw
    assert selected.calibration.original == complete.prior.result.identity


def test_prior_custody_metadata_requires_actual_receipt_output_and_exact_issued_locator(complete):  # noqa: F811
    retained = custody(scope(complete))
    with pytest.raises(ValueError, match="producer locator"):
        replace(retained, prior_execution=replace(retained.prior_execution, run_id="run.other"))
    with pytest.raises(ValueError, match="pre-future"):
        changed = replace(retained.receipt, checks=())
        replace(retained, receipt=changed, receipt_publication=publication(changed, "published." + changed.receipt_id),
            prior_execution=replace(retained.prior_execution, receipt=ObjectIdentity.from_record(changed.receipt_id, changed)))
    with pytest.raises(ValueError, match="publication"):
        replace(retained, publication=replace(retained.publication,
            materialization=replace(retained.publication.materialization, physical_sha256="b" * 64)))


def test_native_parent_hook_refuses_missing_current_supplier_without_reads():
    runner = future.operation_factories()[0].runner_factory()
    with pytest.raises(PermissionError, match="actual current"):
        future.prepare_for_invocation(SimpleNamespace(), runner)
    with pytest.raises(PermissionError, match="TaskContext"):
        future.require_revision_future(SimpleNamespace(), runner.role)


def test_current_grant_refusal_precedes_control_or_prior_reads(monkeypatch):
    runner = future.operation_factories()[0].runner_factory()

    class RefusingCurrent:
        def __init__(self, **kwargs):
            pass

        def current_task(self, context, runner):
            raise PermissionError("actual current grant refused")

        def task_inputs(self, *args):
            pytest.fail("no controls before current authority")

    monkeypatch.setattr(matrix_revision_runtime, "issued_custody_for_supplier", lambda _supplier: RefusingCurrent())
    monkeypatch.setattr(matrix_revision_runtime, "_authenticate_prior_execution", lambda *a, **k: pytest.fail("no prior read before current authority"))
    with pytest.raises(PermissionError, match="current grant refused"):
        matrix_revision_runtime.prepare_revision_future(SimpleNamespace(writer=object(), reveal_authority_id=None), object(), runner)


def test_public_calibration_shape_cannot_replace_genuine_original_cal_producer(monkeypatch):
    runner = future.operation_factories()[0].runner_factory()
    manifest = SimpleNamespace(logical=SimpleNamespace(payload_schema=future.ScheduledRevisionFutureScope.SCHEMA))
    task = SimpleNamespace(scientific_inputs=(SimpleNamespace(consumer_input_id="revision-scope", operational_logical_artifact_id="actual.scope"),))

    class Current:
        def __init__(self, **kwargs):
            pass

        def current_task(self, context, runner):
            return object(), object(), task

        def task_inputs(self, context, task):
            return {}, {"actual.scope": manifest}

        def control_record(self, manifest, kind, maximum):
            return SimpleNamespace(calibration=object())

    monkeypatch.setattr(matrix_revision_runtime, "issued_custody_for_supplier", lambda _supplier: Current())
    monkeypatch.setattr(matrix_revision_runtime, "_authenticate_prior_execution", lambda *a, **k:
        pytest.fail("prediction receipt cannot replace original CAL producer"))
    with pytest.raises(PermissionError, match="SOFTWARE: genuine original E4 revision-CAL producer custody"):
        matrix_revision_runtime.prepare_revision_future(SimpleNamespace(writer=object(), reveal_authority_id=None), object(), runner)


def test_original_publication_transport_contract_cannot_alias_physical_bytes(complete):  # noqa: F811
    retained = custody(scope(complete))
    input_port = port(retained.forecast, retained.publication.logical.logical_artifact_id)
    contract = SimpleNamespace(binding=input_port.binding, logical=retained.publication.logical,
        physical_sha256=retained.publication.materialization.physical_sha256)
    ctx = SimpleNamespace(prepared_invocation=SimpleNamespace(inputs=(contract,)))
    future._require_publication_contract(ctx, input_port, retained.publication)
    with pytest.raises(ValueError, match="preopened"):
        future._require_publication_contract(ctx, input_port, replace(retained.publication,
            materialization=replace(retained.publication.materialization, physical_sha256="b" * 64)))
