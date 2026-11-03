# SPDX-License-Identifier: MPL-2.0
"""Pure contact contracts over actual lowered DEV tasks; no acquired science."""
from dataclasses import fields, replace
from hashlib import sha256

import pytest

from empirical_lawhood.api import recursive_execution as api
from empirical_lawhood.api.matrix_native_read_custody import _expected_contact
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as records
from empirical_lawhood.infrastructure.execution import LocalScheduler
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import (ArtifactGenericValidation, ArtifactMaterialization,
    CanonicalTaskReceipt, LogicalArtifactIdentity)
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution import (OperationalAttempt, TaskAttemptDisposition,
    VerifiedArtifactInput, dependency_artifact_inputs)
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, ExecutionTask, ProtocolExecutionTask
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_matrix_native_utility import utility_case


def _artifact(identifier, schema, profile, media_type, digest=None):
    # Typed disclosed arithmetic operands only. These headers are never published
    # or admitted as task receipts, trajectories, native contacts or qualification.
    digest = digest or sha256(("DISCLOSED.CONTACT.HEADER." + identifier).encode()).hexdigest()
    generic = ArtifactGenericValidation("validator.disclosed.contact", "1.0.0", "a" * 64, schema, profile)
    logical = LogicalArtifactIdentity(identifier, digest, schema, profile, media_type,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE, generic)
    material = ArtifactMaterialization("material." + identifier, identifier, "root.disclosed.contact",
        "disclosed/" + identifier, digest, 1, "none")
    return VerifiedArtifactInput(logical, material)


@pytest.fixture
def lowered_contact_case(tmp_path):
    case = utility_case(tmp_path)
    bound = owner.bind_inputs(case.specification, {"request": case.request}, files=case.template_files)
    prepared = owner.prepare(case.specification, method_inputs=bound.method_inputs, execution=ExecutionSelection(4, "environment.disclosed-contact",
        case.source.provenance.identity, str(tmp_path)))
    assert prepared.executable
    declarations = bindings.operation_declarations()
    registry = CapabilityRegistry("registry.disclosed.contact", tuple(sorted(
        (row.manifest() for row in declarations), key=lambda row: row.registry_id)))
    compiled = compile_recursive_wave(draft=prepared.draft,
        registrations=tuple(row.registration() for row in declarations), registry=registry,
        implementation_commit=case.source.provenance.observed_git_head,
        output_codecs={key: codec for row in declarations for key, codec in row.record_codecs.items()})
    plan = compiled.execution_plan
    assert type(plan) is DevelopmentExecutionPlan and all(type(task) is ExecutionTask for task in plan.tasks)
    run_id = plan.source_plan.object_id
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run_id,
        wave_id="wave.development", authority_identities=())
    receipts, outputs, by_task = {}, {}, {}
    for task in plan.tasks:
        values = tuple(_artifact(row.logical_artifact_id, row.payload_schema, row.profile, row.media_type)
            for row in task.outputs)
        values = tuple(sorted(values, key=lambda row: row.materialization.materialization_id))
        by_task[task.task_id] = values
        outputs.update((row.logical.logical_artifact_id, row) for row in values)
        receipts[task.task_id] = CanonicalTaskReceipt("receipt.disclosed." + task.task_id, run_id,
            task.task_id, index.task(task.task_id).attempts[0].attempt_id, plan.implementation_commit, (),
            tuple(row.materialization for row in values),
            tuple(sorted((row.logical for row in values), key=lambda row: row.logical_artifact_id)),
            (), OperationalStatus.SUCCEEDED, ())
    external = {}
    for task in plan.tasks:
        for spec in task.external_inputs:
            profile, _ = api._external_storage_contract(payload_schema=spec.expected_payload_schema,
                media_type=spec.expected_media_type)
            external[spec.logical_artifact_id] = _artifact(spec.logical_artifact_id,
                spec.expected_payload_schema, profile, spec.expected_media_type, spec.expected_content_sha256)
    products = {"receipts": receipts, "outputs": outputs, "external_inputs": tuple(external.values())}
    response = next(task for task in plan.tasks if task.task_id == owner.task_id(case.specification.root_ids[0], "responses"))
    return case, plan, index, response, by_task, products


def test_actual_lowered_response_contact_selects_causal_product_without_unconsumed_archive(lowered_contact_case):
    case, plan, index, task, by_task, products = lowered_contact_case
    original = plan.canonical_bytes()
    selected = dependency_artifact_inputs(task, by_task)
    selected_logicals = {row.logical.logical_artifact_id for row in selected}
    declared_logicals = {row.operational_logical_artifact_id for row in task.scientific_inputs if row.producer_task_id}
    assert selected_logicals == declared_logicals
    project = next(row for row in plan.tasks if row.task_id == owner.task_id(case.specification.root_ids[0], "project"))
    causal_product = next(row.logical_artifact_id for row in project.outputs if row.output_id.endswith(".product"))
    causal_arrays = next(row.logical_artifact_id for row in project.outputs if row.output_id.endswith(".arrays"))
    assert causal_product in selected_logicals and causal_arrays not in selected_logicals
    all_direct = {row.materialization.materialization_id for key in task.dependency_task_ids for row in by_task[key]}
    assert {row.materialization.materialization_id for row in selected} < all_direct
    assert LocalScheduler._dependency_outputs(task, by_task) == selected
    dependency_bindings = LocalScheduler._dependency_receipt_bindings(task,
        dependency_outputs=selected, receipts=products["receipts"])
    attempt = index.task(task.task_id).attempts[0].attempt_id
    contact = _expected_contact(task=task, plan=plan, run_id=index.run_id, attempt_id=attempt, products=products)
    external = {row.logical.logical_artifact_id: row for row in products["external_inputs"]}
    expected_materials = {row.materialization.materialization_id for row in selected}
    expected_materials.update(external[row.logical_artifact_id].materialization.materialization_id for row in task.external_inputs)
    assert contact == NativeEffectContact(index.run_id, task.task_id, attempt,
        ObjectIdentity.from_record(plan.execution_plan_id, plan), ObjectIdentity.from_record(task.task_id, task),
        plan.implementation_commit, tuple(sorted(expected_materials)), tuple(sorted(row.receipt_id for row in dependency_bindings)))
    assert contact.dependency_receipt_ids == tuple(sorted(products["receipts"][key].receipt_id for key in task.dependency_task_ids))
    assert plan.canonical_bytes() == original


@pytest.mark.parametrize("defect", ("missing-dependency", "missing-selected", "duplicate-selected", "media", "schema"))
def test_pure_dependency_contract_refuses_selected_operand_substitutions(lowered_contact_case, defect):
    _, _, _, task, by_task, _ = lowered_contact_case
    edge = next(row for row in task.scientific_inputs if row.producer_task_id)
    values = dict(by_task)
    if defect == "missing-dependency":
        del values[edge.producer_task_id]
    else:
        rows = list(values[edge.producer_task_id])
        selected = next(row for row in rows if row.logical.logical_artifact_id == edge.operational_logical_artifact_id)
        if defect == "missing-selected":
            rows.remove(selected)
        elif defect == "duplicate-selected":
            rows.append(selected)
        elif defect == "media":
            rows[rows.index(selected)] = replace(selected, logical=replace(selected.logical, media_type="text/plain"))
        else:
            schema = "empirical-lawhood/testing/disclosed-wrong-schema"
            logical = replace(selected.logical, payload_schema=schema,
                generic_validation=replace(selected.logical.generic_validation, payload_schema=schema))
            rows[rows.index(selected)] = replace(selected, logical=logical)
        values[edge.producer_task_id] = tuple(rows)
    with pytest.raises(ValueError, match="dependency|scientific"):
        dependency_artifact_inputs(task, values)


def test_legacy_exact_task_retains_all_outputs_and_unknown_subclasses_refuse(lowered_contact_case):
    _, plan, index, task, by_task, products = lowered_contact_case
    legacy = ProtocolExecutionTask(**{field.name: getattr(task, field.name) for field in fields(ProtocolExecutionTask)})
    assert dependency_artifact_inputs(legacy, by_task) == tuple(sorted(
        (row for key in task.dependency_task_ids for row in by_task[key]),
        key=lambda row: row.materialization.materialization_id))
    class ForeignTask(ExecutionTask):
        pass
    foreign = ForeignTask(**{field.name: getattr(task, field.name) for field in fields(ExecutionTask)})
    with pytest.raises(TypeError, match="supported exact"):
        dependency_artifact_inputs(foreign, by_task)
    with pytest.raises(TypeError, match="exact original development"):
        _expected_contact(task=legacy, plan=plan, run_id=index.run_id,
            attempt_id=index.task(task.task_id).attempts[0].attempt_id, products=products)


def test_custody_contact_join_reuses_exact_selected_materials_and_original_source(lowered_contact_case):
    _, plan, index, _, _, products = lowered_contact_case
    native_keys = frozenset((records.NAMESPACE + ".prefix", records.NAMESPACE + ".responses"))
    attempts = tuple(OperationalAttempt(index.task(task.task_id).attempts[0].attempt_id, index.run_id,
        task.task_id, 1, TaskAttemptDisposition.SUCCEEDED, None, None, None) for task in plan.tasks)
    contacts = {task.task_id: _expected_contact(task=task, plan=plan, run_id=index.run_id,
        attempt_id=index.task(task.task_id).attempts[0].attempt_id, products=products)
        for task in plan.tasks if task.capability.capability_key in native_keys}
    class Contacts:
        def read(self, run_id, task_id):
            assert run_id == index.run_id
            return contacts.get(task_id)
    result = api._custody_contacts(plan=plan, index=index, contacts=Contacts(),
        receipts=tuple(products["receipts"].values()), external_inputs=products["external_inputs"],
        attempts=attempts, native_keys=native_keys)
    assert {key: value for key, value in result if value is not None} == contacts
    with pytest.raises(PermissionError, match="original source/stream"):
        api._custody_contacts(plan=replace(plan, implementation_commit="f" * 40), index=index,
            contacts=Contacts(), receipts=tuple(products["receipts"].values()),
            external_inputs=products["external_inputs"], attempts=attempts, native_keys=native_keys)
