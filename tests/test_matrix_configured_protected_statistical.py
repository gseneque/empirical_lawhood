# SPDX-License-Identifier: MPL-2.0
"""Versioned configured statistical workers over exposed actual port controls.

Fixture custody authenticates bytes only. No real issue, qualification, native
acquisition, sampling or prospective outcome access is established.
"""
from collections import defaultdict
from dataclasses import fields, replace
from functools import partial
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_statistical_bindings as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as science
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_originals as originals
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_tasks import NAMESPACE
from empirical_lawhood.api.domain_composition.matrix_configured_protected_response import scientific_read as reader
from empirical_lawhood.api.matrix_training_provenance import fitted_training_provenance
from empirical_lawhood.infrastructure.execution import prepare_worker_invocation
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.runtime.recursive_compiler import RegisteredPublicationRequirement
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.worker_configuration_support import freeze_worker_configuration
from tests.test_matrix_configured_protected_e3 import selected, original_metadata
from tests.test_matrix_e3_original_publications import case as original_case  # noqa: F401
from tests.test_matrix_e3_response_lifecycle import compiled_response_output


def exposed_root(config, context):
    config.__post_init__()
    if context.node_id != owner.statistical_task_id(config.specification, config.allocation,
            config.operation, mode=config.mode, root=config.root):
        raise ValueError("configured literal root changes its exact node")


def response_task(root_id, *, operation):
    return NAMESPACE + "." + root_id + "." + operation


def declarations():
    return owner.statistical_declarations(publication_requirement=RegisteredPublicationRequirement(
        "configured-e3.original-publication-control", originals.authenticate_configured_original_publications),
        scientific_root_validator=exposed_root, outcome_task_id=partial(response_task, operation="response-score"))


@pytest.fixture(scope="module")
def case(original_case):  # noqa: F811
    inputs, allocation = selected(original_case)
    publications, custody = original_metadata(original_case, inputs, allocation)
    literal = SimpleNamespace(inputs=inputs, allocation=allocation, manifest=original_case.manifest,
        plane=original_case.plane, train_features=original_case.train_features, train_outcomes=original_case.train_outcomes,
        saved_train_features=original_case.train_features, saved_train_outcomes=original_case.train_outcomes,
        provenance=original_case.provenance, fit_cutoff=original_case.fit_cutoff, originals=custody, counter=0,
        publications=tuple((row.key, row.publication, row.availability) for row in publications))
    return _native_bank_context(literal, "configured-statistical")


def config(case, operation, *, mode="", root=None):
    task = owner.statistical_task_id(case.inputs.specification.identity, case.allocation.identity, operation, mode=mode, root=root)
    census = tuple((role, len(case.allocation.unit_ids(role))) for role in ("calibration", "evaluation"))
    if operation == "fit":
        return owner.ConfiguredProtectedE3FitConfig("config." + task, case.inputs.specification.identity, case.allocation.identity,
            census, ObjectIdentity.from_record(case.manifest.record_id, case.manifest), case.inputs.training_allocation.identity,
            case.fit_cutoff, case.publications, case.inputs.training_coordinates, case.originals)
    return owner.ConfiguredProtectedE3StatisticalConfig("config." + task, operation, case.inputs.specification.identity,
        case.allocation.identity, census, mode, root)

def stored(case, record, name, *, access=Access.OUTCOME_BLIND, ceiling=Visibility.PROSPECTIVE,
        task=None, output="product", receipt=None, publication=None, logical_id=None):
    if publication is None:
        name = getattr(case, "fixture_namespace", "") + name
        publication = case.plane.write(ArtifactWriteRequest("literal.statistical." + name if logical_id is None else logical_id,
            "configured-statistical/" + name + ".record.json", record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
            "literal-statistical", "configured-statistical", record.canonical_bytes(), ceiling, (), access))
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
    capability_key = (owner.fit_capability_key(operands["features"].record.SCHEMA, operands["outcomes"].record.SCHEMA)
        if phase == "fit" else NAMESPACE + "." + phase)
    declaration = next(row for row in declarations() if row.capability_key == capability_key)
    runner, manifest = declaration.runner_factory(), declaration.manifest()
    case.counter += 1
    prefix = getattr(case, "fixture_namespace", "") + "case." + str(case.counter)
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
            "configured-statistical/" + prefix + "." + port.output_id.rsplit(".", 1)[-1] + ".json", port.payload_schema,
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
            "configured-statistical/" + selected.prefix + "." + name + ".json", port.payload_schema, port.profile,
            port.media_type, "literal-statistical", "configured-statistical", payload.payload,
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

def test_actual_versioned_fit_and_model_freeze_consume_explicit_parameters_and_exact_current_receipts(case, monkeypatch):
    operands = sources(case)
    invocation = prepared(case, config(case, "fit"), operands)
    originals.authenticate_configured_original_publications(case.plane, (SimpleNamespace(record=invocation.config),))
    train = {operands[name].publication.logical.logical_artifact_id: name for name in ("features", "outcomes")}
    events, read, require = [], owner._read, owner.require_e3_reserved_fit_inputs
    def joined_originals(*args, **kwargs):
        result = require(*args, **kwargs)
        events.append("joined-originals")
        return result
    def observe(port, *args, **kwargs):
        if port.artifact_id in train:
            assert events[0] == "joined-originals"
            events.append(train[port.artifact_id])
        return read(port, *args, **kwargs)
    with monkeypatch.context() as controls:
        controls.setattr(owner, "require_e3_reserved_fit_inputs", joined_originals)
        controls.setattr(owner, "_read", observe)
        products = execute(case, invocation)
    assert events == ["joined-originals", "features", "outcomes"]
    model = products["product"].record
    joined = products["prefit-join"].record
    assert type(model) is science.ConfiguredProtectedE3ModelSet
    assert model.specification == case.inputs.specification.identity
    assert model.reservation_join == joined.identity
    assert model == science.fit_protected_e3_models(case.inputs, joined, case.train_features, case.train_outcomes,
        record_id=model.record_id)
    common = {key: operands[key] for key in ("specification", "allocation")}
    frozen = execute(case, prepared(case, config(case, "freeze", mode="model"),
        {**common, "models": products["product"], "prefit-join": products["prefit-join"]}))["product"].record
    assert frozen == science.freeze_protected_e3(case.inputs.specification, case.allocation, model, record_id=frozen.record_id)
    assert frozen.specification.object_version == "3.0.0"
    actual, custody = reader._product(case.plane, None, {products["product"].receipt.task_id: products["product"].receipt},
        products["product"].receipt.task_id, science.ConfiguredProtectedE3ModelSet)
    report = fitted_training_provenance(case.inputs.specification, case.allocation, actual, frozen)
    assert report["bank_edition"] == "NATIVE_BANKS"
    assert report["data_origin"] == "NOT_REESTABLISHED_BY_THIS_READ"
    assert report["feature_bank"] == model.training_features.to_document()
    assert report["units"] == list(case.allocation.unit_ids("train"))
    assert custody["receipt"] == ObjectIdentity.from_record(products["product"].receipt.receipt_id, products["product"].receipt).to_document()
    with pytest.raises(PermissionError, match="EXACT_FITTED_TRAINING"):
        fitted_training_provenance(case.inputs.specification, case.allocation, replace(actual, record_id=actual.record_id + ".foreign"), frozen)
    path = case.plane.root.resolve(products["product"].publication.materialization.relative_path, for_write=False)
    raw = path.read_bytes()
    try:
        path.write_bytes(raw + b" ")
        with pytest.raises((PermissionError, ValueError, RuntimeError)):
            reader._product(case.plane, None, {products["product"].receipt.task_id: products["product"].receipt},
                products["product"].receipt.task_id, science.ConfiguredProtectedE3ModelSet)
    finally:
        path.write_bytes(raw)


def test_late_reservation_refuses_before_any_train_port_read(case, monkeypatch):
    from decimal import Decimal
    selected = config(case, "fit")
    selected = replace(selected, publications=tuple((key, publication,
        replace(availability, available_at=Decimal(2)) if key == "reservation" else availability)
        for key, publication, availability in selected.publications))
    operands = sources(case)
    invocation = prepared(case, selected, operands)
    train = {operands[name].publication.logical.logical_artifact_id for name in ("features", "outcomes")}
    reads, read = [], owner._read
    def observe(port, *args, **kwargs):
        if port.artifact_id in train:
            reads.append(port.artifact_id)
        return read(port, *args, **kwargs)
    monkeypatch.setattr(owner, "_read", observe)
    with pytest.raises(ValueError):
        invocation.runner.execute(invocation.context)
    assert reads == []


def test_versioned_fit_has_no_temperature_role_inference_and_keeps_full_train_census(case):
    selected = config(case, "fit")
    assert selected.training_coordinates == case.inputs.training_coordinates
    assert tuple(row[0] for row in selected.training_coordinates.assignments) == case.inputs.training_allocation.unit_ids()
    changed = replace(selected.training_coordinates, assignments=selected.training_coordinates.assignments[:-1])
    with pytest.raises(ValueError, match="TRAIN coordinate census"):
        source = replace(case.inputs, training_coordinates=changed)
        source.__post_init__()


def test_versioned_statistical_declarations_refuse_missing_parent_before_any_train_read():
    rows = declarations()
    assert {row.capability_key for row in rows} == {*(NAMESPACE + "." + phase for phase in owner.PHASES if phase != "fit"), NAMESPACE + ".native-fit"}
    assert all(not row.execution_properties.native_effect for row in rows)
    fit = next(row for row in rows if row.capability_key.endswith(".native-fit"))
    assert fit.capability_version == "1.0.0"
    assert fit.implementation_id == NAMESPACE + ".native-fit.native-statistical-owner.v1"
    assert tuple(fit.record_codecs[kind.SCHEMA] for kind in science.native_training_bank_types()) == science.native_training_bank_types()
    assert all(kind.SCHEMA not in fit.record_codecs for kind in
        (science.exposed.MatrixE3FeatureBank, science.exposed.MatrixE3OutcomeBank))
    with pytest.raises(PermissionError, match="parent custody"):
        owner.prepare_for_invocation(object(), fit.runner_factory())
    assert all(row.config_record_type.SCHEMA.startswith("empirical-lawhood/matrix-response-experiment/configured-") for row in rows)
    assert all(row.manifest().capability_key.startswith("matrix-e3-configured-protected.") for row in rows)


def test_protected_protocol_declares_native_banks_and_retained_outputs_without_exposed_banks():
    from empirical_lawhood.adapters.methods.matrix_factor_response.extension_bundle import EXPERIMENT_PROTOCOL_DECLARATIONS
    protocols = {row.protocol_id: row for row in EXPERIMENT_PROTOCOL_DECLARATIONS}
    files = protocols["matrix.response-error.configured-protected-v2"].input_file_record_types
    assert set(science.native_training_bank_types()) <= set(files)
    assert science.exposed.MatrixE3FeatureBank not in files and science.exposed.MatrixE3OutcomeBank not in files
    exposed = protocols["matrix.response-error.origin-only.configured-v2"].input_record_types
    assert science.exposed.MatrixE3FeatureBank in exposed and science.exposed.MatrixE3OutcomeBank in exposed


def test_retired_saved_bank_fit_owner_refuses_before_any_input_read(case, monkeypatch):
    invocation = prepared(case, config(case, "fit"), sources(case))
    retired = replace(invocation.runner.manifest, capability_key=NAMESPACE + ".fit")
    runner = owner.ConfiguredProtectedE3StatisticalRunner("fit", retired,
        partial(response_task, operation="response-score"))
    monkeypatch.setattr(owner, "_read", lambda *_: pytest.fail("retired owner reached input decoding"))
    with pytest.raises(ValueError, match="prepared declaration"):
        runner.execute(invocation.context)


def test_versioned_worker_rejects_foreign_current_fit_dependency_and_prepared_contract(case):
    operands = sources(case)
    fitted = execute(case, prepared(case, config(case, "fit"), operands))
    common = {key: operands[key] for key in ("specification", "allocation")}
    broken = prepared(case, config(case, "freeze", mode="model"),
        {**common, "models": fitted["product"], "prefit-join": fitted["prefit-join"]}, foreign_models=True)
    with pytest.raises(ValueError, match="current producer"):
        broken.runner.execute(broken.context)


def test_typed_configured_protocol_projects_exact_geometry_without_old_candidate_prose(case):
    from pathlib import Path
    import json
    from empirical_lawhood.kernel.decoding import decode_canonical_record
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_protocol as protocol
    original = json.loads((Path(__file__).resolve().parents[1] / "programmes/foundations/emergent-structure/records/matrix-e2-e3-candidate/candidate-design02.json").read_bytes())
    mathematical = decode_canonical_record(original["target"]["original_mathematical_protocol"], MatrixResponseFrontierProtocol)
    full_rule = mathematical.factor_rule_compatibilities[0].target
    policy = case.manifest.native_specification.selection.prefix_policies[0]
    raw = (Path(__file__).resolve().parents[1] / "src/empirical_lawhood/adapters/simulators/six_matrix_response/response_observer.py").read_bytes()
    parameters = dict(specification=case.inputs.specification, nominal=case.inputs.nominal, nearby=case.inputs.nearby,
        shifted=case.inputs.shifted, mathematical_protocol=mathematical, original_factor_rule=full_rule, prefix_policy=policy,
        scalar_definition=case.manifest.scalar_definition, normalization_source=full_rule.scalar_closure.normalization_owner,
        normalization_source_bytes=raw, record_id="projection.configured-protected-control")
    projected = protocol.project_protected_e3_protocol(**parameters)
    assert projected.specification == case.inputs.specification.identity
    assert projected.protocol_sha256 == case.inputs.specification.protocol_sha256
    assert projected.protocol_size_bytes == len(case.inputs.specification.protocol.canonical_bytes())
    assert decode_canonical_bytes(projected.canonical_bytes(), type(projected), maximum_bytes=None) == projected
    with pytest.raises(ValueError, match="explicit original role coordinate"):
        protocol.project_protected_e3_protocol(**{**parameters, "nominal": case.inputs.nearby})
    changed = replace(case.inputs.specification, calibration_alpha=case.inputs.specification.calibration_alpha / 2)
    alternate = protocol.project_protected_e3_protocol(**{**parameters, "specification": changed})
    assert alternate.specification != projected.specification
    assert alternate.mathematical_protocol == projected.mathematical_protocol
    assert alternate.protocol_sha256 == projected.protocol_sha256


def test_configured_forecast_refuses_coordinate_relabelling_before_prediction(case):
    from tests.test_matrix_configured_protected_e3 import causal
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
    operands = sources(case)
    fitted = execute(case, prepared(case, config(case, "fit"), operands))
    models, join = fitted["product"].record, fitted["prefit-join"]
    common = {key: operands[key] for key in ("specification", "allocation")}
    frozen = execute(case, prepared(case, config(case, "freeze", mode="model"),
        {**common, "models": fitted["product"], "prefit-join": join}))["product"].record
    _, feature = causal(case, case.allocation.unit_ids("calibration")[0])
    public = feature.public_source
    coordinate = case.inputs.nearby
    other = ScheduledPublicSource(public.source, replace(public.root, coordinate_id=coordinate.coordinate_id, clock_id=coordinate.clock_id),
        coordinate, public.policy, public.allocation, public.reservation)
    changed = replace(feature, public_source=other)
    with pytest.raises(ValueError, match="allocated causal role"):
        science.forecast_protected_e3(case.inputs.specification, case.allocation, models, frozen, changed,
            role="calibration", record_id="forecast.refused-coordinate")


def test_versioned_prefix_and_feature_schemas_do_not_replace_historical_owners():
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_prefix_bindings as current
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_prefix_records as records
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_records as original
    rows = current.prefix_declarations()
    assert len(rows) == 5
    assert {row.capability_key for row in rows if row.execution_properties.native_effect} == {"matrix-e3-configured-protected.prefix"}
    for name in ("PrefixHistory", "NumericalAssessment", "PrefixWitness", "FrameAssessment", "CausalPrefix"):
        selected = getattr(records, "ConfiguredProtectedE3" + name)
        retained = getattr(original, "ProtectedE3" + name)
        assert selected.SCHEMA != retained.SCHEMA
    prefix = next(row for row in rows if row.execution_properties.native_effect)
    runner = prefix.runner_factory()
    with pytest.raises(PermissionError, match="actual complete prepared"):
        runner.execute_with_native_subwork(object(), object())
    with pytest.raises(TypeError, match="exact worker context"):
        current.prepare_native_work(runner=runner, context=object(), expected_parent=object())


def test_versioned_response_declarations_keep_forecast_prerequisite_and_refuse_unprepared_native_entry():
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_response_bindings as current
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_feature_bindings as feature
    rows = current.response_declarations(publication_requirement=originals.ORIGINAL_PUBLICATION_REQUIREMENT,
        scientific_root_validator=exposed_root)
    assert len(rows) == 3 and feature.feature_task_id("root.control") == owner.feature_task_id("root.control")
    native = next(row for row in rows if row.execution_properties.native_effect)
    assert native.capability_key == "matrix-e3-configured-protected.responses"
    names = {port.port_id for port in native.input_ports}
    assert {"error", "models", "allocation", "frozen"} <= names
    assert any(port.payload_schema == science.ConfiguredProtectedE3Forecast.SCHEMA for port in native.input_ports)
    with pytest.raises(PermissionError, match="actual complete prepared"):
        native.runner_factory().execute_with_native_subwork(object(), object())


def test_configured_protected_public_missing_originals_retains_full_census_without_lowering(case, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_preparation as preparation
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_lowering as lowering
    from empirical_lawhood.api.experiment_preparation import prepare_experiment
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
    monkeypatch.setattr(lowering, "lower_protected_matrix_response_error", lambda *args: pytest.fail("lowering missing source evidence"))
    result = prepare_experiment(case.inputs.specification, scientific_inputs={}, execution=ExecutionSelection())
    assert not result.executable and result.draft is None
    expected = sum(case.inputs.specification.population(role).expected_units for role in ("CALIBRATION", "EVALUATION"))
    assert result.census.native_effect_count == 2 * expected
    assert sum(count for _, count in result.census.operation_counts) == 10 * expected + 6
    assert any(row.source_key == "protected-selection" for row in result.dependencies)
    assert preparation.ConfiguredProtectedE3PreparationSelection.SCHEMA != "empirical-lawhood/matrix-response-experiment/protected-preparation-selection"


def _native_training_allocation(allocation):
    """Declared TEST request reference; never an authenticated acquisition."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import NativeTrainingAcquisitionRequest

    request = ObjectIdentity("request.configured-fit-control", NativeTrainingAcquisitionRequest.SCHEMA,
        NativeTrainingAcquisitionRequest.VERSION, "d" * 64)
    roles = tuple(replace(role, role="train") for role in allocation.roles)
    if (request in allocation.sources and all(unit.source_id == request.object_id for unit in allocation.units)
            and allocation.roles == roles):
        return allocation, request
    sources = {value.object_id:value for value in (*allocation.sources, request)}
    return (replace(allocation, allocation_id=allocation.allocation_id + ".native-control",
        sources=tuple(sorted(sources.values(), key=lambda value: value.object_id)),
        units=tuple(replace(unit, source_id=request.object_id) for unit in allocation.units), roles=roles), request)


def _native_bank_control(case):
    """Typed dispatch fixtures only; these arithmetic rows prove no acquisition."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import (
        NativeTrainingFeature, NativeTrainingFeatureBank, NativeTrainingOutcome, NativeTrainingOutcomeBank,
        NativeTrainingAcquisitionSeal, NativeTrainingCausalPrefix,
    )
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource

    allocation, request = _native_training_allocation(case.inputs.training_allocation)
    acquisition = ObjectIdentity("acquisition.configured-fit-control", NativeTrainingAcquisitionSeal.SCHEMA,
        NativeTrainingAcquisitionSeal.VERSION, "a" * 64)
    def fields_for(row, kind):
        values = {field.name: getattr(row, field.name) for field in fields(kind) if hasattr(row, field.name)}
        values.update(source_manifest=request,
            native_source=ObjectIdentity("source.native-control." + row.unit_id,
                ScheduledSource.SCHEMA, ScheduledSource.VERSION, "b" * 64),
            origin=ObjectIdentity("prefix.native-control." + row.unit_id,
                NativeTrainingCausalPrefix.SCHEMA, NativeTrainingCausalPrefix.VERSION, "c" * 64))
        return values
    feature_rows = tuple(NativeTrainingFeature(**fields_for(row, NativeTrainingFeature)) for row in case.train_features.rows)
    outcome_rows = tuple(NativeTrainingOutcome(**fields_for(row, NativeTrainingOutcome)) for row in case.train_outcomes.rows)
    return (NativeTrainingFeatureBank("bank.native-control.features", allocation.identity, "train", feature_rows, acquisition),
        NativeTrainingOutcomeBank("bank.native-control.outcomes", allocation.identity, "train", outcome_rows, acquisition))


def _native_bank_context(case, namespace):
    """Actual TEST allocation custody, with declared arithmetic native-schema rows.

    Request/source/prefix pins are disclosed fixture references. Their schemas
    exercise dispatch; no native acquisition seal or scientific warrant is made.
    """
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_inputs import project_protected_e3_allocation
    from tests.test_matrix_factor_confirmation_eligibility import publish

    if (type(case.train_features), type(case.train_outcomes)) == science.native_training_bank_types():
        science.validate_native_training_banks(case.inputs.specification, case.inputs.training_allocation,
            case.train_features, case.train_outcomes)
        return SimpleNamespace(**{**vars(case), "counter":0, "fixture_namespace":namespace + "."})
    training, _ = _native_training_allocation(case.inputs.training_allocation)
    features, outcomes = _native_bank_control(case)
    sources = {row.unit_id:row.native_source for row in features.rows}
    coordinates = replace(case.inputs.training_coordinates,
        record_id=case.inputs.training_coordinates.record_id + ".native-control",
        assignments=tuple((unit, sources[unit], coordinate)
            for unit, _, coordinate in case.inputs.training_coordinates.assignments))
    inputs = replace(case.inputs, training_allocation=training, training_coordinates=coordinates)
    allocation = project_protected_e3_allocation(inputs)
    training_publication = publish(case.plane, training, "configured-native-control.training." + training.fingerprint())
    roles_publication = publish(case.plane, allocation, "configured-native-control.roles." + allocation.fingerprint())
    originals = replace(case.originals, training_allocation=training.identity,
        training_allocation_publication=training_publication)
    publications = tuple((key, roles_publication if key == "roles" else publication, availability)
        for key, publication, availability in case.publications)
    return SimpleNamespace(**{**vars(case), "inputs":inputs, "allocation":allocation,
        "train_features":features, "train_outcomes":outcomes, "originals":originals,
        "publications":publications, "counter":0, "fixture_namespace":namespace + "."})


def test_native_train_fit_uses_exact_new_ports_and_retains_truthful_bank_pins(case):
    original_features, original_outcomes = case.saved_train_features, case.saved_train_outcomes
    saved_bytes = original_features.canonical_bytes(), original_outcomes.canonical_bytes()
    # Preserve the unchanged numerical owner on the original literal values;
    # retired protected saved-bank execution is not used as an oracle.
    expected = tuple(science.exposed.MatrixE3EstimatorModel(*values) for values in
        science.numerical.fit_estimator_values(case.inputs.specification, case.allocation.unit_ids("train"),
            {row.unit_id: row for row in original_features.rows}, {row.unit_id: row for row in original_outcomes.rows}))
    case = _native_bank_context(case, "native-finite")
    operands = sources(case)
    features, outcomes = _native_bank_control(case)
    for name, record in (("features", features), ("outcomes", outcomes)):
        operands[name] = stored(case, record, "source.native." + name,
            access=Access.DEVELOPMENT_VISIBLE, ceiling=Visibility.DEVELOPMENT_ONLY)
    invocation = prepared(case, config(case, "fit"), operands)
    assert invocation.declaration.capability_key == NAMESPACE + ".native-fit"
    assert {port.port_id: port.payload_schema for port in invocation.declaration.input_ports}["features"] == features.SCHEMA
    assert {port.port_id: port.payload_schema for port in invocation.declaration.input_ports}["outcomes"] == outcomes.SCHEMA
    originals.authenticate_configured_original_publications(case.plane, (SimpleNamespace(record=invocation.config),))
    fit_products = execute(case, invocation)
    fitted = fit_products["product"].record
    actual, custody = reader._product(case.plane, None,
        {fit_products["product"].receipt.task_id: fit_products["product"].receipt}, fit_products["product"].receipt.task_id,
        science.ConfiguredProtectedE3ModelSet)
    common = {key: operands[key] for key in ("specification", "allocation")}
    frozen = execute(case, prepared(case, config(case, "freeze", mode="model"),
        {**common, "models": fit_products["product"], "prefit-join": fit_products["prefit-join"]}))["product"].record
    report = fitted_training_provenance(case.inputs.specification, case.allocation, actual, frozen)
    assert report["bank_edition"] == "NATIVE_BANKS"
    assert report["assigned_units"] == len(case.allocation.unit_ids("train"))
    assert report["units"] == list(case.allocation.unit_ids("train"))
    assert report["feature_bank"] == science.identity(features).to_document()
    assert report["outcome_bank"] == science.identity(outcomes).to_document()
    assert report["finite_endpoint_counts"] == [[model.method_key, list(model.finite_counts)] for model in fitted.models]
    assert custody["logical_artifact"] == fit_products["product"].publication.logical.to_document()
    assert fitted.models == expected
    assert (fitted.training_features, fitted.training_outcomes) == (science.identity(features), science.identity(outcomes))
    assert fitted.training_features != science.identity(original_features) and fitted.training_outcomes != science.identity(original_outcomes)
    assert decode_canonical_bytes(fitted.canonical_bytes(), type(fitted), maximum_bytes=None) == fitted
    assert saved_bytes == (original_features.canonical_bytes(), original_outcomes.canonical_bytes())
    for bank in (original_features, original_outcomes, features, outcomes):
        assert decode_canonical_bytes(bank.canonical_bytes(), type(bank), maximum_bytes=None).canonical_bytes() == bank.canonical_bytes()
    with pytest.raises(ValueError, match="exact native TRAIN bank pair"):
        replace(fitted, training_outcomes=science.identity(original_outcomes))


def test_native_train_fit_retains_nonuse_without_fabricating_a_frame_or_dropping_units(case):
    case = _native_bank_context(case, "native-missing")
    features, outcomes = _native_bank_control(case)
    missing_feature = replace(features.rows[0], frame_sha256=None, disposition="UNAVAILABLE", values=())
    missing_outcome = replace(outcomes.rows[0], frame_sha256=None, numerical_disposition="UNEVALUABLE",
        views=tuple(replace(view, errors=(None,) * 15, dispositions=("UNAVAILABLE",) * 15)
            for view in outcomes.rows[0].views))
    features = replace(features, rows=(missing_feature, *features.rows[1:]))
    outcomes = replace(outcomes, rows=(missing_outcome, *outcomes.rows[1:]))
    operands = sources(case)
    for name, record in (("features", features), ("outcomes", outcomes)):
        operands[name] = stored(case, record, "source.native-missing." + name,
            access=Access.DEVELOPMENT_VISIBLE, ceiling=Visibility.DEVELOPMENT_ONLY)
    fitted = execute(case, prepared(case, config(case, "fit"), operands))["product"].record
    units = case.inputs.training_allocation.unit_ids()
    assert tuple(row.unit_id for row in features.rows) == tuple(row.unit_id for row in outcomes.rows) == units
    assert missing_feature.frame_sha256 is missing_outcome.frame_sha256 is None
    assert all(model.training_unit_ids == units and model.finite_counts == (len(units) - 1,) * 15 for model in fitted.models)
    with pytest.raises(ValueError):
        replace(features.rows[1], frame_sha256=None)
    with pytest.raises(ValueError):
        replace(outcomes.rows[1], frame_sha256=None)


@pytest.mark.parametrize("feature_native", (False, True))
def test_native_train_fit_refuses_mixed_editions_before_reading_either_bank(case, feature_native):
    features, outcomes = _native_bank_control(case)
    feature = features if feature_native else case.saved_train_features
    outcome = case.saved_train_outcomes if feature_native else outcomes
    with pytest.raises(ValueError, match="exact native TRAIN bank pair"):
        owner.fit_capability_key(feature.SCHEMA, outcome.SCHEMA)


def test_protected_fit_refuses_saved_banks_before_fitting_or_payload_reads(case, monkeypatch):
    banks = case.saved_train_features, case.saved_train_outcomes
    before = tuple(bank.canonical_bytes() for bank in banks)
    monkeypatch.setattr(science.numerical, "fit_estimator_values",
        lambda *_: pytest.fail("saved-bank refusal reached numerical fitting"))
    with pytest.raises(ValueError, match="exact native TRAIN bank pair"):
        owner.fit_capability_key(*(bank.SCHEMA for bank in banks))
    with pytest.raises(ValueError, match="exact native TRAIN bank pair"):
        science.training_bank_types(*(bank.SCHEMA for bank in banks))
    assert tuple(bank.canonical_bytes() for bank in banks) == before


def test_native_train_fit_refuses_partial_denominator_and_different_acquisition(case):
    case = _native_bank_context(case, "native-partial")
    features, outcomes = _native_bank_control(case)
    inputs, allocation = case.inputs, case.allocation
    # Reuse the actual original-publication join; no alternate fit or source is invented.
    products = execute(case, prepared(case, config(case, "fit"), sources(case)))
    joined = products["prefit-join"].record
    with pytest.raises(ValueError):
        science.fit_protected_e3_models(inputs, joined, replace(features, rows=features.rows[:-1]), outcomes,
            record_id="model.native-partial.refused")
    with pytest.raises(ValueError):
        science.fit_protected_e3_models(inputs, joined, features,
            replace(outcomes, acquisition=replace(outcomes.acquisition, object_id="acquisition.other-control")),
            record_id="model.native-acquisition.refused")
    assert allocation.unit_ids("train") == inputs.training_allocation.unit_ids()
