# SPDX-License-Identifier: MPL-2.0
"""Actual prepared statistical ports and stored receipts over exposed literals.

Authored feature/outcome producers and publication availability are conformance
fixtures, not source qualification, native science or real issue authority.
"""

from collections import defaultdict
from dataclasses import fields, replace
from decimal import Decimal as D
from functools import partial
from hashlib import sha256
import pickle
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as science
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_statistical_bindings as owner
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import project_protected_e3_allocation
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import NAMESPACE, identity
from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.time import AvailabilitySpec, CausalPhase, InformationCutoff
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityPermission, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, ParentPreparedTaskRunner, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort, prepare_task_runner
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.runtime.recursive_compiler import RegisteredPublicationRequirement
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.worker_configuration_support import freeze_worker_configuration
from tests.test_matrix_e3_protected_methods import causal, outcome
from tests.test_matrix_e3_protected_source_records import fixture as source_fixture
from tests.test_matrix_e3_protected_prefix_science import forbid_native as forbid_native  # noqa: F401
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance_fixture, publish, stock as stock_fixture
from tests.test_matrix_scheduled_history import scheduled as scheduled_fixture
from tests.test_matrix_experiment_methods import fixture as mathematical_fixture, selected_input_records
from tests.test_matrix_e3_response_lifecycle import compiled_response_output


def exposed_publications(plane, config_inputs):
    """Verify disclosed actual bytes/availability; no eligibility is asserted."""
    for row in config_inputs:
        config = row.record
        if type(config) is not owner.ProtectedE3FitConfig:
            raise ValueError("literal publication check received another operation")
        for _, publication, availability in config.publications:
            config.fit_cutoff.require_allows(availability)
            raw = plane.root.resolve(publication.materialization.relative_path, for_write=False).read_bytes()
            assert sha256(raw).hexdigest() == publication.logical.content_sha256
            assert len(raw) == publication.materialization.size_bytes


def exposed_root(config, context):
    config.__post_init__()
    if context.node_id != owner.statistical_task_id(config.specification, config.allocation,
            config.operation, mode=config.mode, root=config.root):
        raise ValueError("literal statistical root changed its exact current node")


def response_task(root_id, *, operation):
    assert operation == "response-score"
    return NAMESPACE + "." + root_id + "." + operation


OUTCOME = partial(response_task, operation="response-score")


def declarations():
    return owner.statistical_declarations(publication_requirement=RegisteredPublicationRequirement(
        "literal.e3-statistical.actual-publication-bytes", exposed_publications),
        scientific_root_validator=exposed_root, outcome_task_id=OUTCOME)


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    return build_statistical_case(tmp_path_factory)


def build_statistical_case(tmp_path_factory, *, selected64=False):
    directory = tmp_path_factory.mktemp("literal-statistical")
    provenance = provenance_fixture.__wrapped__()
    scheduled = scheduled_fixture.__wrapped__(stock_fixture.__wrapped__(directory, provenance))
    selected = source_fixture(scheduled, selected64=selected64)
    inputs = replace(selected.inputs, reservation=selected.manifest.reservation,
        native_specification=selected.manifest.native_specification)
    _, training_sources, _, methods = mathematical_fixture(**dict(selected64=True, train_count=64,
        cal_count=64, eval_count=64, minimum_usable=58)) if selected64 else mathematical_fixture()
    banks = selected_input_records(training_sources, methods)
    allocation = project_protected_e3_allocation(inputs)
    roles = publish(selected.plane, allocation, "literal.statistical.roles")
    pubs = (selected.manifest.reservation.publication, selected.manifest.native_specification.publication,
        selected.manifest.reservation_publication, roles)
    availability = AvailabilitySpec("clock.literal.statistical.publications", CausalPhase.PREPARATION, Access.OUTCOME_BLIND, D(0))
    cutoff = InformationCutoff("cutoff.literal.statistical.before-train", availability.clock_id, CausalPhase.PREPARATION, D(1))
    return SimpleNamespace(inputs=inputs, manifest=selected.manifest, plane=selected.plane, allocation=allocation,
        train_features=banks["train-features"], train_outcomes=banks["train-outcomes"], provenance=provenance,
        fit_cutoff=cutoff, publications=tuple((key, pub, availability)
            for key, pub in zip(owner.PUBLICATION_KEYS, pubs, strict=True)), counter=0)


def config(case, operation, *, mode="", root=None, late=False):
    task = owner.statistical_task_id(case.inputs.specification.identity, case.allocation.identity, operation, mode=mode, root=root)
    census = tuple((role, len(case.allocation.unit_ids(role))) for role in ("calibration", "evaluation"))
    if operation == "fit":
        pubs = tuple((key, publication, replace(availability, available_at=D(2)) if late and key == "reservation" else availability)
            for key, publication, availability in case.publications)
        return owner.ProtectedE3FitConfig("config." + task, case.inputs.specification.identity, case.allocation.identity,
            census, identity(case.manifest), case.inputs.training_allocation.identity, case.fit_cutoff, pubs)
    return owner.ProtectedE3StatisticalConfig("config." + task, operation, case.inputs.specification.identity,
        case.allocation.identity, census, mode, root)


def stored(case, record, name, *, access=Access.OUTCOME_BLIND, ceiling=Visibility.PROSPECTIVE,
        task=None, output="product", receipt=None, publication=None, logical_id=None):
    if publication is None:
        publication = case.plane.write(ArtifactWriteRequest("literal.statistical." + name if logical_id is None else logical_id,
            "statistical/" + name + ".record.json", record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
            "literal-statistical", "statistical", record.canonical_bytes(), ceiling, (), access))
    if task is not None and receipt is None:
        receipt = CanonicalTaskReceipt("receipt.literal.statistical." + name, "run.literal.statistical", task,
            "attempt.literal.statistical." + name, case.provenance.observed_git_head, (),
            (publication.materialization,), (publication.logical,), (), OperationalStatus.SUCCEEDED, ())
        ExternalTaskReceiptStore(case.plane).commit(receipt, visibility_ceiling=ceiling, outcome_access=access)
    return SimpleNamespace(record=record, publication=publication, receipt=receipt, output=output)


def sources(case):
    records = {"specification": case.inputs.specification, "allocation": case.allocation,
        "manifest": case.manifest, "training-allocation": case.inputs.training_allocation,
        "original-allocation": case.manifest.reservation.allocation,
        "native-selection": case.manifest.native_specification.selection, "reservation": case.manifest.reservation,
        "features": case.train_features, "outcomes": case.train_outcomes}
    pubs = {key: publication for key, publication, _ in case.publications}
    return {name: stored(case, record, "source." + name,
        access=Access.DEVELOPMENT_VISIBLE if name in ("features", "outcomes") else Access.OUTCOME_BLIND,
        ceiling=Visibility.DEVELOPMENT_ONLY if name in ("features", "outcomes") else Visibility.PROSPECTIVE,
        publication=pubs.get({"original-allocation": "allocation", "allocation": "roles"}.get(name, name)))
        for name, record in records.items()}


def prepared(case, selected_config, operands, *, foreign_models=False, output_ceiling=None, qualified_outputs=True):
    """Real guarded ports and current stored receipt bindings, no child process."""
    phase = owner._phase(selected_config)
    declaration = next(row for row in declarations() if row.capability_key == NAMESPACE + "." + phase)
    runner, manifest = declaration.runner_factory(), declaration.manifest()
    case.counter += 1
    prefix = "case." + str(case.counter)
    automatic = stored(case, selected_config, prefix + ".config", logical_id=selected_config.record_id)
    rows = [("automatic", automatic)] + [(name, value) for name, values in operands.items()
        for value in (values if type(values) is tuple else (values,))]
    verified = tuple(sorted((VerifiedArtifactInput(value.publication.logical, value.publication.materialization)
        for _, value in rows), key=lambda row: row.artifact_id))
    by_alias = {value.publication.logical.logical_artifact_id: (name, value) for name, value in rows}
    bindings = tuple(WorkerInputBinding.from_verified(value, kind=WorkerInputKind.DEPENDENCY
        if by_alias[value.artifact_id][1].receipt is not None and not(foreign_models and by_alias[value.artifact_id][0] == "models")
        else WorkerInputKind.EXTERNAL) for value in verified)
    ports = case.plane.open_many(verified, bindings=bindings, maximum_bytes=None)
    receipts = defaultdict(list)
    receipt_records = {}
    for binding in bindings:
        record = by_alias[binding.artifact_id][1]
        if binding.kind is WorkerInputKind.DEPENDENCY:
            receipts[record.receipt.receipt_id].append(binding.materialization_id)
            receipt_records[record.receipt.receipt_id] = record.receipt
    dependencies = tuple(DependencyReceiptBinding(key, receipt_records[key].task_id, tuple(sorted(values)))
        for key, values in sorted(receipts.items()))
    task_id = owner.statistical_task_id(selected_config.specification, selected_config.allocation,
        selected_config.operation, mode=selected_config.mode, root=selected_config.root)
    reference = CapabilityConfigRef(selected_config.record_id, selected_config.SCHEMA, manifest.config_schema_sha256,
        selected_config.fingerprint(), automatic.publication.logical.logical_artifact_id)
    outputs = tuple(WorkerOutputPort(task_id + "." + template.output_id, template.payload_schema, template.profile,
        template.media_type, "ordinary.statistical." + prefix + "." + template.output_id) for template in declaration.outputs)
    context = TaskContext("run.literal.statistical", task_id, "attempt.literal.statistical." + prefix, reference,
        bindings, ports, outputs, manifest.permissions, declaration.outcome_access, owner.BUDGET,
        WorkerIsolationProfile.TRUSTED_LOCAL, dependencies)
    incoming = []
    for binding in bindings:
        name, value = by_alias[binding.artifact_id]
        if name == "automatic":
            continue
        dependency = binding.kind is WorkerInputKind.DEPENDENCY
        input_id = (name + "." + value.record.feature.public_source.root.root_id
            if phase in ("calibrate", "assess") and name in ("forecasts", "outcomes") else name)
        incoming.append(ScientificInputSpec("edge." + prefix + "." + name + "." + str(len(incoming)), input_id,
            ScientificInputRole.MODEL if dependency else ScientificInputRole.SOURCE,
            value.receipt.task_id if dependency else None,
            (value.receipt.task_id + "." + value.output if qualified_outputs else value.output) if dependency else None,
            None if dependency else "external." + name, "scientific." + prefix + "." + str(len(incoming)),
            binding.artifact_id, binding.payload_schema, binding.media_type, binding.size_bytes,
            binding.outcome_access, binding.visibility_ceiling, BarrierKind.NONE))
    external = tuple(ExternalInputSpec("input." + value.artifact_id, value.artifact_id,
        value.logical.content_sha256, value.logical.payload_schema, value.logical.media_type,
        value.materialization.size_bytes, value.logical.visibility_ceiling, value.logical.outcome_access, None)
        for value, binding in zip(verified, bindings, strict=True) if binding.kind is WorkerInputKind.EXTERNAL)
    # Sealed lane comes from the actual shared compiler fixture over a fitted
    # development parent, not a selected PROSPECTIVE publication label.
    compiled = compiled_response_output(declaration.outcome_access) if declaration.outcome_access is Access.EVALUATION_SEALED else None
    ceiling = (compiled.visibility_ceiling if compiled else
        inherited_visibility(tuple(binding.visibility_ceiling for binding in bindings), declaration.outcome_access))
    if output_ceiling is not None:
        ceiling = output_ceiling
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, reference,
        manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, EvidenceCeiling.RESPONSE,
        declaration.outcome_access, owner.BUDGET)
    task = ExecutionTask(task_id, declaration.stage, requirement, manifest.implementation_sha256,
        tuple(sorted(row.task_id for row in dependencies)), external,
        tuple(ArtifactOutputSpec(port.output_id, port.logical_artifact_id,
            "statistical/" + prefix + "." + port.output_id.rsplit(".", 1)[-1] + ".json", port.payload_schema,
            port.profile, port.media_type, ceiling, tuple(binding.visibility_ceiling for binding in bindings),
            declaration.outcome_access) for port in outputs), (), declaration.execution_properties.barrier, 1,
        ("obligation.literal.statistical",), scientific_inputs=tuple(sorted(incoming, key=lambda row: row.edge_id)))
    task = freeze_worker_configuration(task)
    provenance = case.provenance
    implementation = RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, provenance.observed_git_head, provenance.observed_checkout_clean)
    contract = prepare_worker_invocation(runner, context, verified, implementation=implementation,
        execution_plan=ObjectIdentity("plan.literal.statistical", "empirical-lawhood/runtime/execution-plan", "1.0.0", "e" * 64),
        execution_task=ObjectIdentity.from_record(task_id, task), execution_task_record=task)
    return SimpleNamespace(context=replace(context, prepared_invocation=contract), runner=runner,
        declaration=declaration, config=selected_config, task=task, prefix=prefix)


def execute(case, selected):
    result = selected.runner.execute(selected.context)
    publications, decoded = [], {}
    by_id = {port.output_id: port for port in selected.context.output_ports}
    for payload in result.outputs:
        port = by_id[payload.output_id]
        name = port.output_id.rsplit(".", 1)[-1]
        record = decode_canonical_bytes(payload.payload, selected.declaration.record_codecs[port.payload_schema], maximum_bytes=None)
        publication = case.plane.write(ArtifactWriteRequest(port.logical_artifact_id,
            "statistical/" + selected.prefix + "." + name + ".json", port.payload_schema, port.profile,
            port.media_type, "literal-statistical", "statistical", payload.payload,
            selected.task.outputs[0].visibility_ceiling, (), selected.context.outcome_access))
        publications.append(publication)
        decoded[name] = (record, publication)
    receipt = CanonicalTaskReceipt("receipt." + selected.context.attempt_id, selected.context.run_id,
        selected.context.task_id, selected.context.attempt_id, case.provenance.observed_git_head,
        selected.context.input_materialization_ids, tuple(sorted((p.materialization for p in publications), key=lambda p: p.materialization_id)),
        tuple(sorted((p.logical for p in publications), key=lambda p: p.logical_artifact_id)), result.checks, OperationalStatus.SUCCEEDED, ())
    ExternalTaskReceiptStore(case.plane).commit(receipt, visibility_ceiling=selected.task.outputs[0].visibility_ceiling,
        outcome_access=selected.context.outcome_access)
    return {name: stored(case, record, selected.prefix + "." + name, publication=publication, receipt=receipt,
        output=name) for name, (record, publication) in decoded.items()}


@pytest.fixture(scope="module")
def fitted(case):
    operands = sources(case)
    selected = prepared(case, config(case, "fit"), operands)
    exposed_publications(case.plane, (SimpleNamespace(record=selected.config),))
    products = execute(case, selected)
    common = {key: operands[key] for key in ("specification", "allocation")}
    frozen = execute(case, prepared(case, config(case, "freeze", mode="model"),
        {**common, "models": products["product"], "prefit-join": products["prefit-join"]}))["product"]
    return SimpleNamespace(common=common, models=products["product"], joined=products["prefit-join"], frozen=frozen)


def test_required_global_hooks_and_six_cold_declarations_are_picklable():
    with pytest.raises(TypeError):
        owner.statistical_declarations()
    with pytest.raises(TypeError, match="module-global"):
        owner.statistical_declarations(publication_requirement=RegisteredPublicationRequirement("literal.bad", exposed_publications),
            scientific_root_validator=lambda *args: None, outcome_task_id=OUTCOME)
    rows = declarations()
    assert len(rows) == 6 and {row.capability_key.rsplit(".", 1)[-1] for row in rows} == set(owner.PHASES)
    for row in rows:
        assert not row.execution_properties.native_effect
        assert row.scientific_hooks.scientific_root_validator is exposed_root
        assert pickle.loads(pickle.dumps(row.runner_factory())).manifest == row.manifest()
        assert CapabilityPermission.REVEAL_OUTCOMES not in row.permissions


@pytest.mark.parametrize("qualified_outputs", (False, True))
def test_actual_fit_and_model_freeze_publish_join_and_keep_original_math(case, fitted, qualified_outputs):
    model = fitted.models.record
    assert model.reservation_join == fitted.joined.record.identity
    assert fitted.models.receipt == fitted.joined.receipt
    expected = science.fit_protected_e3_models(case.inputs, fitted.joined.record, case.train_features, case.train_outcomes,
        record_id=model.record_id)
    assert expected.canonical_bytes() == model.canonical_bytes()
    assert fitted.frozen.record.models == science.identity(model)
    assert fitted.frozen.publication.logical.outcome_access is Access.DEVELOPMENT_VISIBLE
    assert fitted.frozen.publication.logical.visibility_ceiling is Visibility.DEVELOPMENT_ONLY
    selected = prepared(case, config(case, "freeze", mode="model"),
        {**fitted.common, "models": fitted.models, "prefit-join": fitted.joined}, qualified_outputs=qualified_outputs)
    result = selected.runner.execute(selected.context)
    frozen = decode_canonical_bytes(result.outputs[0].payload, science.ProtectedE3FrozenProducts, maximum_bytes=None)
    assert frozen.models == fitted.frozen.record.models
    assert frozen.reservation_join == fitted.frozen.record.reservation_join


def test_installed_fit_requires_parent_custody_before_train_delivery(case):
    rows = declarations()
    fit = next(row for row in rows if row.capability_key == NAMESPACE + ".fit")
    assert fit.execution_properties.runner_preparation_factory is owner.prepare_for_invocation
    assert fit.provider_factory().runner_preparation_factory is owner.prepare_for_invocation
    assert all(row.execution_properties.runner_preparation_factory is None for row in rows if row is not fit)
    selected = prepared(case, config(case, "fit"), sources(case))
    calls = []
    class Supplier:
        def prepare_protected_e3_fit(self, context, runner):
            assert context is selected.context and runner is selected.runner
            assert all(port.bytes_read == 0 for port in context.input_ports)
            calls.append(context.task_id)
            return runner
    wrapper = fit.provider_factory().runner_preparation_factory(Supplier(), selected.runner)
    assert type(wrapper) is ParentPreparedTaskRunner and calls == []
    with pytest.raises(PermissionError, match="PARENT_RUNNER_PREPARATION_REQUIRED"):
        wrapper.execute(selected.context)
    plain = prepare_task_runner(wrapper, selected.context)
    assert calls == [selected.context.task_id] and plain is selected.runner
    assert set(vars(plain)) == {"phase", "manifest", "outcome_task_id"}
    assert pickle.loads(pickle.dumps(plain)).manifest == wrapper.manifest
    for port in selected.context.input_ports:
        port.close()


def test_missing_or_refused_parent_custody_never_reads_train(case):
    selected = prepared(case, config(case, "fit"), sources(case))
    with pytest.raises(PermissionError, match="installed parent custody"):
        owner.prepare_for_invocation(object(), selected.runner)
    class Supplier:
        def prepare_protected_e3_fit(self, context, runner):
            raise PermissionError("literal missing current issue custody")
    wrapper = owner.prepare_for_invocation(Supplier(), selected.runner)
    with pytest.raises(PermissionError, match="current issue custody"):
        prepare_task_runner(wrapper, selected.context)
    assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    with pytest.raises(TypeError, match="exact current fit"):
        owner.prepare_for_invocation(Supplier(), next(row for row in declarations()
            if row.capability_key == NAMESPACE + ".model-freeze").runner_factory())
    for port in selected.context.input_ports:
        port.close()


def test_fit_reads_train_only_after_the_complete_original_join(case, monkeypatch):
    operands = sources(case)
    selected = prepared(case, config(case, "fit"), operands)
    train = {operands[name].publication.logical.logical_artifact_id: name for name in ("features", "outcomes")}
    events, read, require = [], owner._read, owner.require_e3_reserved_fit_inputs
    def joined(*args, **kwargs):
        result = require(*args, **kwargs)
        events.append("joined-originals")
        return result
    def observe(port, *args, **kwargs):
        if port.artifact_id in train:
            assert events[0] == "joined-originals"
            events.append(train[port.artifact_id])
        return read(port, *args, **kwargs)
    monkeypatch.setattr(owner, "require_e3_reserved_fit_inputs", joined)
    monkeypatch.setattr(owner, "_read", observe)
    selected.runner.execute(selected.context)
    assert events == ["joined-originals", "features", "outcomes"]


def test_late_reservation_refuses_before_any_train_port_read(case, monkeypatch):
    operands = sources(case)
    selected = prepared(case, config(case, "fit", late=True), operands)
    train = {operands[name].publication.logical.logical_artifact_id for name in ("features", "outcomes")}
    reads, original = [], owner._read
    def observe(port, *args, **kwargs):
        if port.artifact_id in train:
            reads.append(port.artifact_id)
        return original(port, *args, **kwargs)
    monkeypatch.setattr(owner, "_read", observe)
    with pytest.raises(ValueError):
        selected.runner.execute(selected.context)
    assert reads == []


def test_current_fit_products_cannot_be_replaced_by_external_fitted_labels(case, fitted, monkeypatch):
    selected = prepared(case, config(case, "freeze", mode="model"),
        {**fitted.common, "models": fitted.models, "prefit-join": fitted.joined}, foreign_models=True)
    monkeypatch.setattr(science, "freeze_protected_e3", lambda *args, **kwargs: pytest.fail("foreign model reached arithmetic"))
    with pytest.raises(ValueError, match="current producer"):
        selected.runner.execute(selected.context)


def test_seedless_forecast_config_has_no_source_or_training_payload(case):
    root = causal(case, case.allocation.unit_ids("calibration")[0])[0].root.root
    value = config(case, "forecast", mode="calibration", root=root)
    assert tuple(field.name for field in fields(value)) == (
        "record_id", "operation", "specification", "allocation", "query_census", "mode", "root")
    assert pickle.loads(pickle.dumps(value)) == value


def test_complete_current_statistical_sequence_retains_original_paired_math(case, fitted):
    models, model_freeze = fitted.models, fitted.frozen
    forecast_rows, outcome_rows = {}, {}
    calibration = calibrated_freeze = None
    for role in ("calibration", "evaluation"):
        forecasts, outcomes = [], []
        for unit in case.allocation.unit_ids(role):
            source, feature = causal(case, unit)
            feature_input = stored(case, feature, "feature." + unit,
                task=owner.feature_task_id(source.root_id))
            operands = {**fitted.common, "models": models,
                "frozen": model_freeze if role == "calibration" else calibrated_freeze, "feature": feature_input}
            if role == "evaluation":
                operands.update(calibration=calibration, **{"model-freeze": model_freeze})
            selected = prepared(case, config(case, "forecast", mode=role, root=source.root.root), operands)
            current = execute(case, selected)["product"]
            expected = science.forecast_protected_e3(case.inputs.specification, case.allocation, models.record,
                operands["frozen"].record, feature, role=role, record_id=current.record.record_id,
                calibration=None if role == "calibration" else calibration.record)
            assert current.record.canonical_bytes() == expected.canonical_bytes()
            assert current.publication.logical.outcome_access is Access.EVALUATION_SEALED
            assert current.publication.logical.visibility_ceiling is Visibility.DEVELOPMENT_ONLY
            forecasts.append(current)
            paired = outcome(current.record, missing=unit == case.allocation.unit_ids(role)[0])
            outcomes.append(stored(case, paired, "outcome." + unit, access=Access.EVALUATION_SEALED,
                ceiling=Visibility.DEVELOPMENT_ONLY, task=OUTCOME(source.root_id), output="outcome"))
        forecast_rows[role], outcome_rows[role] = tuple(forecasts), tuple(outcomes)
        if role == "calibration":
            calibration = execute(case, prepared(case, config(case, "calibrate"),
                {**fitted.common, "models": models, "frozen": model_freeze,
                    "forecasts": tuple(forecasts), "outcomes": tuple(outcomes)}))["product"]
            expected = science.calibrate_protected_e3(case.inputs.specification, case.allocation, models.record,
                model_freeze.record, tuple(row.record for row in forecasts), tuple(row.record for row in outcomes),
                record_id=calibration.record.record_id)
            assert calibration.record.canonical_bytes() == expected.canonical_bytes()
            calibrated_freeze = execute(case, prepared(case, config(case, "freeze", mode="calibration"),
                {**fitted.common, "models": models, "model-freeze": model_freeze, "calibration": calibration}))["product"]
    assessment = execute(case, prepared(case, config(case, "assess"),
        {**fitted.common, "frozen": calibrated_freeze, "forecasts": forecast_rows["evaluation"],
            "outcomes": outcome_rows["evaluation"]}))["product"]
    expected = science.assess_protected_e3(case.inputs.specification, case.allocation, calibrated_freeze.record,
        tuple(row.record for row in forecast_rows["evaluation"]), tuple(row.record for row in outcome_rows["evaluation"]),
        record_id=assessment.record.record_id)
    assert assessment.record.canonical_bytes() == expected.canonical_bytes()
    assert len(assessment.record.decisions) == len(case.allocation.unit_ids("evaluation"))
    assert not assessment.record.decisions[0].usable
