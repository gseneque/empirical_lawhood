# SPDX-License-Identifier: MPL-2.0
"""Actual selected software workers refuse exposed incomplete molecular inputs.

The selected current callers, scientific predicates, producing observations and
filesystem inspection are unmodified. Parent fixtures disclose exposed software
custody; these negative controls establish no molecular or biological result.
Run against a frozen selected checkout when collecting producing-source proof.
"""

from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import empirical_lawhood

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as c
from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding
from empirical_lawhood.api.recursive_execution import read_recursive_wave, run_recursive_wave
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, prepare_worker_invocation
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.numerical_provenance import capture_numerical_provenance
from empirical_lawhood.infrastructure.prepared_native_invocation import NativeInputPublication, prepare_native_invocation
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ExternalRootContract
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.runtime.execution import TaskContext, WorkerIsolationProfile, WorkerOutputPort
from tests.runtime_platform.test_worker_preflight import _original_task
from tests.test_rubisco_geometry_reuse import original as original  # noqa: F401
from tests.test_rubisco_closed_raw_model_admission import closed as closed, known_derived as known_derived  # noqa: F401
from tests.test_rubisco_serialized_nve_custody import (
    admitted as admitted, durable_admitted as durable_admitted, reuse_admitted as reuse_admitted)  # noqa: F401


ROOT = Path(empirical_lawhood.__file__).resolve().parents[2]
ACCESS = OutcomeAccess.DEVELOPMENT_VISIBLE
VISIBILITY = VisibilityCeiling.DEVELOPMENT_ONLY


def _plane(path):
    from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
    path.mkdir()
    return ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "rubisco-exposed-negative-custody", "Actual exposed no-contact software control", str(path),
        str(next(parent for parent in (path, *path.parents) if parent.is_mount())),
        "empirical-lawhood/testing/recursive-custody", 0)),
        validators=integration_artifact_profile_validators())


def _environment():
    selected = {name: os.environ[name] for name in ("PATH", "HOME", "LANG", "LC_ALL") if name in os.environ}
    selected.update(PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    selected.update({name: "1" for name in ("OPENMM_CPU_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS",
        "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")})
    return tuple(sorted(selected.items()))


def _source(original, name):
    # A separately selected operational destination does not revise original
    # supplier bytes or create fresh scientific evidence.
    return replace(original.source, native_workdir=c.NATIVE_WORK_ROOT + "/exposed-c2-public09-" + name)


def _selected_plan(original, source, observed, *, name):
    return replace(original.plan, plan_id="plan.exposed.c2-public09." + name,
        source=c.identity(source), workdir=source.native_workdir,
        interpreter_path=sys.executable, interpreter_sha256=sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
        tleap_path=sys.executable, tleap_sha256=sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
        code_sources=observed.package_sources, dependency_lock_sha256=observed.dependency_lock_sha256)


def _public_refusal(tmp_path, draft, records, *, expected_code):
    by_identity = {identity: record for identity, record in records}
    plane = _plane(tmp_path / "custody")
    bindings = []
    for external in draft.external_inputs:
        identity = next(row for row in by_identity if row.object_id == external.logical_artifact_id)
        raw = by_identity[identity].canonical_bytes()
        assert sha256(raw).hexdigest() == external.expected_content_sha256
        path = tmp_path / (sha256(external.input_id.encode()).hexdigest() + ".json")
        path.write_bytes(raw)
        bindings.append((external.input_id, path))
    directory = tmp_path / "custody/authored"
    authored = author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane,
        output_dir=directory, input_bindings=tuple(bindings))
    assert authored["native_contact"] == "none" and authored["task_count"] == 1
    result = _retained_public_task_diagnostic(directory, plane, tmp_path)
    assert not result.ready
    assert result.producing_provenance.code_sources_sha256 == expected_code
    assert not any(row.operand_id.startswith(("worker.source", "worker.interpreter", "worker.prefix"))
        for row in result.mismatches)
    assert not any(marker in row.reason for row in result.mismatches
        for marker in ("SOFTWARE:", "AttributeError", "unsupported canonical"))
    report = run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane)
    assert report["status"] != "SUCCEEDED"
    assert report["new_native_contact_count"] == 0 and report["native_contact"] == "none"
    assert report["producing_code_sha256"] == expected_code
    assert report["scientific_authority"] == "NONE" and report["qualification"] == "NOT_ESTABLISHED"
    assert report["terminal_products"] == {}
    assert read_recursive_wave(directory=directory, artifact_writer=plane, terminal_product_format="compact") == report
    retained, _, _, plan = read_recursive_wave(directory=directory, artifact_writer=plane, include_products=True, terminal_product_format="compact")
    assert retained == report
    contacts = ExternalNativeEffectContactStore(plane=plane,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=VISIBILITY, outcome_access=ACCESS)
    assert all(contacts.read(report["run_id"], task.task_id) is None for task in plan.tasks)
    (tmp_path / "actual-public-refusal.json").write_text(json.dumps(report, sort_keys=True, default=str) + "\n")
    return report


def _retained_public_task_diagnostic(directory, plane, tmp_path):
    """Inspect the exact public frozen task and inputs before any effect entry."""
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import _retained_plans, _external_inputs
    from empirical_lawhood.api.recursive_operations import operation_catalog, operation_runners
    from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind

    _, draft, source, payloads = load_authored_wave(directory=directory, artifact_writer=plane, lazy_payloads=True)
    run, plan, _ = _retained_plans(payloads, draft)
    inputs = _external_inputs(plane=plane, plan=plan, draft=draft, payloads=payloads, read_only=False)
    registrations, registry, _ = operation_catalog()
    task, = plan.tasks
    runner = operation_runners(registry=registry, plan=plan).resolve(task)
    registration = next(row for row in registrations if row.selection.capability_key == task.capability.capability_key)
    bindings = tuple(WorkerInputBinding.from_verified(row, kind=WorkerInputKind.EXTERNAL) for row in inputs)
    ports = plane.open_many(inputs, bindings=bindings, maximum_bytes=None)
    try:
        context = TaskContext(run.run_plan_id, task.task_id, run.run_plan_id + "." + task.task_id + ".attempt-001",
            task.capability.config, bindings, ports,
            tuple(WorkerOutputPort(row.output_id, row.payload_schema, row.profile, row.media_type, row.logical_artifact_id)
                for row in task.outputs), task.capability.required_permissions, task.capability.requested_outcome_access,
            task.capability.requested_resources, WorkerIsolationProfile.TRUSTED_LOCAL)
        contract = prepare_worker_invocation(runner, context, inputs, implementation=source,
            execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
            execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task,
            native_effect=True, native_work_preparer=registration.native_work_preparer,
            provenance_requirements=registration.provenance_requirements)
        (tmp_path / "actual-public-task-invocation.json").write_bytes(contract.canonical_bytes())
        result = LocalProcessExecutor(scratch_root=plane.root).preflight(runner, context, prepared_contract=contract,
            native_work_preparer=registration.native_work_preparer, provenance_requirements=registration.provenance_requirements)
        (tmp_path / "actual-public-task-diagnostic.json").write_bytes(result.canonical_bytes())
        reasons = tuple(row.reason for row in result.mismatches)
        if task.task_id.endswith("nve-control"):
            assert any("interpreter" in reason or "No such file" in reason for reason in reasons)
        else:
            assert any("preparation omits/reorders exact source stock" in reason for reason in reasons)
            assert contract.native_work is not None and contract.native_work.isolated_diagnostics
            child = contract.native_work.isolated_diagnostics[-1]
            assert not child.ready and child.producing_provenance is not None
            assert child.producing_provenance.code_sources_sha256 == source.code_sources_sha256
            assert any("preparation omits/reorders exact source stock" in row.reason for row in child.mismatches)
        return result
    finally:
        for port in ports:
            port.close()


def test_actual_public_durable_control_reaches_selected_child_and_refuses_original_incomplete_stock(tmp_path, original):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import durable_operation_bindings as ob
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_recursive_translation import preparation_control_draft
    observed = capture_numerical_provenance(project_root=ROOT)
    source = _source(original, "durable")
    plan = _selected_plan(original, source, observed, name="durable")
    config = ob.DurablePreparationConfig("config." + ob.NODE, plan, source, observed.identity,
        str(ROOT), str(tmp_path / "selected-invocation.json"), _environment())
    records = ((plan.identity, plan), (c.identity(source), source), (c.identity(original.nomination), original.nomination),
        (c.identity(original.inventory), original.inventory), (c.identity(original.coordinates), original.coordinates),
        (observed.identity, observed))
    _public_refusal(tmp_path, preparation_control_draft(config), records, expected_code=observed.code_sources_sha256)
    assert not Path(plan.workdir).exists()
    assert Path(config.invocation_path).exists()  # operational input only, never a contact witness


def test_actual_public_geometry_control_preserves_original_suppliers_and_refuses_stock(tmp_path, original):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_operation_bindings import GeometryReuseConfig, NODE
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_recursive_translation import geometry_reuse_draft
    from tests.test_rubisco_geometry_reuse import fresh
    observed = capture_numerical_provenance(project_root=ROOT)
    source, plan = fresh(original)
    # Keep the original selected archive destinations and choose only a fresh
    # sibling operational work directory. The retained supplier bytes and
    # complete archive-input identities remain unchanged.
    source = replace(source, native_workdir=str(Path(source.native_workdir).with_name("native-work-public11")))
    plan = replace(plan, source=c.identity(source), workdir=source.native_workdir,
        code_sources=observed.package_sources, dependency_lock_sha256=observed.dependency_lock_sha256,
        interpreter_path=sys.executable, interpreter_sha256=sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
        tleap_path=sys.executable, tleap_sha256=sha256(Path(sys.executable).resolve().read_bytes()).hexdigest())
    config = GeometryReuseConfig("config." + NODE, plan, source, (original.supply,), (original.assessment,),
        str(ROOT), str(tmp_path / "selected-invocation.json"), _environment())
    records = ((plan.identity, plan), (c.identity(source), source), (c.identity(original.nomination), original.nomination),
        (c.identity(original.inventory), original.inventory), (c.identity(original.coordinates), original.coordinates),
        (original.supply.identity, original.supply), (original.supply.independent_integrity, original.assessment))
    originals = (original.supply.canonical_bytes(), original.assessment.canonical_bytes())
    _public_refusal(tmp_path, geometry_reuse_draft(config, draft_id="draft.exposed-public09.geometry"), records,
        expected_code=observed.code_sources_sha256)
    assert originals == (original.supply.canonical_bytes(), original.assessment.canonical_bytes())
    assert not Path(plan.workdir).exists()


def test_actual_installed_ordinary_worker_reports_stock_refusal_without_inventing_parent_contributions(tmp_path, original):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import operation_bindings as ob
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.ordinary_preparation import prepare_native_work
    observed = capture_numerical_provenance(project_root=ROOT)
    source = _source(original, "ordinary")
    operands = tuple(sorted((c.identity(row) for row in (source, original.nomination, original.inventory, original.coordinates)),
        key=lambda row: row.object_id))
    config = c.PreparationOperationConfig("config." + c.NAMESPACE + ".prepare", "prepare", source,
        original.nomination.scope, operands)
    runner = ob.PreparationRunner("prepare")
    plane = _plane(tmp_path / "custody")
    records = ((config.config_id, config), *((identity.object_id, record) for identity, record in zip(operands,
        sorted((source, original.nomination, original.inventory, original.coordinates), key=lambda row: c.identity(row).object_id), strict=True)))
    bundle = prepare_native_invocation(plane, publications=tuple(NativeInputPublication(name, row) for name, row in records),
        visibility=VISIBILITY, access=ACCESS)
    try:
        outputs = tuple(WorkerOutputPort(c.NAMESPACE + ".prepare." + name, kind.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.logical." + name) for name, kind in ob.operation_outputs("prepare"))
        context = TaskContext("exposed.ordinary.run", c.NAMESPACE + ".prepare", "exposed.ordinary.attempt",
            CapabilityConfigRef(config.config_id, config.SCHEMA, runner.manifest.config_schema_sha256,
                config.fingerprint(), config.config_id), bundle.input_bindings, bundle.input_ports, outputs,
            runner.manifest.permissions, ACCESS, ob.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL)
        task = _original_task(runner, context, bundle)
        contract = prepare_worker_invocation(runner, context, bundle.verified_inputs,
            implementation=implementation_binding(ROOT),
            execution_plan=ObjectIdentity("exposed.ordinary.plan", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "1" * 64),
            execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task,
            native_effect=True, native_work_preparer=prepare_native_work)
        result = LocalProcessExecutor(scratch_root=plane.root).preflight(runner, context,
            prepared_contract=contract, native_work_preparer=prepare_native_work)
        assert not result.ready
        assert result.producing_provenance.code_sources_sha256 == observed.code_sources_sha256
        assert "preparation omits/reorders exact source stock" in str(result.mismatches)
        assert not any(row.operand_id.startswith(("worker.source", "worker.interpreter", "worker.prefix")) for row in result.mismatches)
        (tmp_path / "actual-worker-refusal.json").write_bytes(result.canonical_bytes())
        contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=contract.execution_plan,
            visibility_ceiling=VISIBILITY, outcome_access=ACCESS)
        assert contacts.read(context.run_id, context.task_id) is None
        assert not Path(source.native_workdir).exists()
    finally:
        bundle.close()


def _sampling_config(plan, source, operation, tmp_path):
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.operation_bindings import SamplingOperationConfig
    environment = dict(_environment(), OPENMM_PLUGIN_DIR=str(tmp_path / "explicit-unavailable-plugins"))
    return SamplingOperationConfig("config.rubisco-insilico-sampling." + operation, operation,
        plan.canonical_bytes().decode(), source, str(ROOT), str(tmp_path / "selected-invocation.json"),
        tuple(sorted(environment.items())))


def test_actual_public_chemical14_keeps_instance_custody_and_refuses_unavailable_stock(tmp_path, closed):
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.closed_raw_model_admission import ordinary_instance_records
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.recursive_translation import sampling_control_draft
    from tests.test_rubisco_closed_raw_model_admission import operands
    observed = capture_numerical_provenance(project_root=ROOT)
    plan, source, inputs, _, _, assets, _ = operands(closed)
    original = tuple(record.canonical_bytes() for _, record in ordinary_instance_records(inputs))
    # Retained five-owner source manifests use their original checkout labels.
    # The current plan includes every selected package file under those labels.
    plan = replace(plan, plan_id="config.exposed.public09.chemical",
        workdir=c.NATIVE_WORK_ROOT + "/exposed-c2-public09-chemical",
        interpreter_path=sys.executable, interpreter_sha256=sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
        code_sources=tuple(("src/empirical_lawhood/" + name, digest) for name, digest in observed.package_sources),
        dependency_lock_sha256=observed.dependency_lock_sha256)
    config = _sampling_config(plan, source, "chemical-force", tmp_path)
    records = (*ordinary_instance_records(inputs), (plan.identity, plan), (c.identity(source), source),
        *((identity, asset) for (_, identity), asset in zip(plan.selected_assets, assets, strict=True)))
    _public_refusal(tmp_path, sampling_control_draft(config, draft_id="draft.exposed-public09.chemical"), records,
        expected_code=observed.code_sources_sha256)
    assert original == tuple(record.canonical_bytes() for _, record in ordinary_instance_records(inputs))
    assert not Path(plan.workdir).exists()


def test_actual_public_nve12_preserves_old_chemical_and_refuses_unavailable_selected_interpreter(tmp_path, admitted):
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.recursive_translation import sampling_control_draft
    observed = capture_numerical_provenance(project_root=ROOT)
    chemical = admitted.plan.chemical_controls
    old = chemical.canonical_bytes()
    plan = replace(admitted.plan, plan_id="config.exposed.public09.nve",
        workdir=c.NATIVE_WORK_ROOT + "/exposed-c2-public09-nve",
        code_sources=observed.package_sources, dependency_lock_sha256=observed.dependency_lock_sha256)
    config = _sampling_config(plan, admitted.source, "nve-control", tmp_path)
    records = tuple((record.identity if hasattr(record, "identity") else c.identity(record), record)
        for record in (plan, chemical, admitted.source, admitted.relaxed, admitted.envelope))
    _public_refusal(tmp_path, sampling_control_draft(config, draft_id="draft.exposed-public09.nve"), records,
        expected_code=observed.code_sources_sha256)
    assert chemical.VERSION == "1.2.0" and chemical.canonical_bytes() == old
    assert not Path(plan.workdir).exists()
