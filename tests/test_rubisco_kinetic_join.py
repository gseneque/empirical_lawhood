# SPDX-License-Identifier: MPL-2.0
"""Real registered compiler/worker joins with disclosed synthetic operands."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_assay_bridge import (
    KineticAssayBridgeResult, KineticJointTargetAssessment,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.executable_binding import EXECUTABLE_BINDING_FACTORIES
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.operation_bindings import (
    BUDGET, MEDIA, NAMESPACE, PHASES, KineticJoinConfig, KineticJoinRunner,
    operation_manifests, operation_registrations, output_codecs,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.recursive_translation import kinetic_join_draft, scientific_work
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_supply import JointKineticSupply, KineticSupportInterval
from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRegistry
from empirical_lawhood.runtime.execution import (
    DependencyReceiptBinding, TaskContext, WorkerInputBinding, WorkerInputKind,
    WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort,
)
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_rubisco_kinetic_supply import comparison, supply


def operands():
    source = supply()
    query = AssayQuery(Decimal(10), Decimal(250), Decimal("2.5"))
    target = comparison(source)
    draft = kinetic_join_draft(source, query, target, relative_tolerance=Decimal("1e-10"))
    config = decode_canonical_bytes(draft.operations[0].config_payload.encode(), KineticJoinConfig, maximum_bytes=None)
    return source, query, target, draft, config.science


def compile_draft(draft):
    return compile_recursive_wave(draft=draft, registrations=operation_registrations(),
        registry=CapabilityRegistry("registry.kinetic-join-software-fixture",
            tuple(sorted(operation_manifests(), key=lambda row: row.registry_id))),
        implementation_commit="a" * 40, output_codecs=output_codecs())


def worker(role, science, records):
    config = KineticJoinConfig(f"config.{NAMESPACE}.{role}", role, science)
    rows = [(config.config_id, config), *records]
    ports, readers, receipts = [], {}, []
    for artifact, record in sorted(rows):
        payload = record.canonical_bytes()
        material = "material." + artifact
        kind = WorkerInputKind.DEPENDENCY if type(record) is KineticAssayBridgeResult else WorkerInputKind.EXTERNAL
        readers[artifact] = BytesIO(payload)
        binding = WorkerInputBinding(artifact, material, record.SCHEMA, MEDIA, len(payload),
            VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE, kind)
        ports.append(WorkerInputPort(binding, readers[artifact]))
        if kind is WorkerInputKind.DEPENDENCY:
            receipts.append(DependencyReceiptBinding("receipt.assay", NAMESPACE + ".assay", (material,)))
    output = next(row[2] for row in PHASES if row[0] == role)
    ref = CapabilityConfigRef(config.config_id, config.SCHEMA, sha256(config.SCHEMA.encode()).hexdigest(),
        config.fingerprint(), config.config_id)
    runner = KineticJoinRunner(role)
    context = TaskContext("run.kinetic-join-software-fixture", NAMESPACE + "." + role,
        f"{NAMESPACE}.{role}.attempt-001", ref, tuple(port.binding for port in ports), tuple(ports),
        (WorkerOutputPort(f"{NAMESPACE}.{role}.product", output.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA),),
        runner.manifest.permissions, OutcomeAccess.DEVELOPMENT_VISIBLE, BUDGET,
        WorkerIsolationProfile.TRUSTED_LOCAL, tuple(receipts))
    return runner, context, readers


def decode_result(result, kind):
    return decode_canonical_bytes(result.outputs[0].payload, kind, maximum_bytes=None)


def test_registered_graph_has_real_typed_source_assay_independent_assessment():
    source, query, target, draft, science = operands()
    compiled = compile_draft(draft)
    tasks = {task.task_id: task for task in compiled.execution_plan.tasks}
    assert len(tasks) == 2
    assert tasks[NAMESPACE + ".assay"].dependency_task_ids == ()
    assert tasks[NAMESPACE + ".assess"].dependency_task_ids == (NAMESPACE + ".assay",)
    assert all(not row.native_effect for row in operation_registrations())
    assert {row.expected_content_sha256 for row in draft.external_inputs} == {
        source.fingerprint(), query.fingerprint(), target.fingerprint()}
    runner, context, readers = worker("assay", science, [(science.supply.object_id, source), (science.query.object_id, query)])
    numerical = decode_result(runner.execute(context), KineticAssayBridgeResult)
    assert all(reader.closed for reader in readers.values())
    runner, context, readers = worker("assess", science, [(NAMESPACE + ".assay.product", numerical),
        (science.comparison.object_id, target)])
    assessed = decode_result(runner.execute(context), KineticJointTargetAssessment)
    assert assessed.assay_bridge == numerical
    assert assessed.robust_conditional_target_disposition is AssessmentDisposition.SATISFIED
    assert assessed.nomination_readiness == "NOT_ESTABLISHED"
    assert assessed.probability_of_joint_success is None
    assert all(reader.closed for reader in readers.values())
    joins = tuple(factory for factory in EXECUTABLE_BINDING_FACTORIES
        if factory.registration.config_record_type is KineticJoinConfig)
    assert len(joins) == 2
    assert all(factory.inquiry_work_projector is scientific_work for factory in joins)


def test_changing_unused_target_keeps_assay_work_and_changes_assessment_work():
    source, query, target, draft, _ = operands()
    revised = kinetic_join_draft(source, query,
        replace(target, gp_specificity=KineticSupportInterval(Decimal(241), Decimal(241))),
        relative_tolerance=Decimal("1e-10"), draft_id="draft.revised-target")
    assert scientific_work(draft, NAMESPACE + ".assay") == scientific_work(revised, NAMESPACE + ".assay")
    assert scientific_work(draft, NAMESPACE + ".assess") != scientific_work(revised, NAMESPACE + ".assess")
    changed_query = kinetic_join_draft(source, replace(query, co2_um=Decimal(20)), target,
        relative_tolerance=Decimal("1e-10"), draft_id="draft.revised-query")
    assert scientific_work(draft, NAMESPACE + ".assay") != scientific_work(changed_query, NAMESPACE + ".assay")


@pytest.mark.parametrize("change", ["missing-link", "wrong-role", "comparison-to-assay", "omitted-operation"])
def test_compiler_refuses_missing_or_substituted_scientific_roles(change):
    *_, draft, _science = operands()
    if change == "missing-link":
        draft = replace(draft, links=draft.links[:-1])
    elif change == "wrong-role":
        draft = replace(draft, links=tuple(replace(row, scientific_role="OUTCOME") if row.consumer_input_id == "query"
            else row for row in draft.links))
    elif change == "comparison-to-assay":
        draft = replace(draft, links=tuple(replace(row, consumer_node_id=NAMESPACE + ".assay")
            if row.consumer_input_id == "comparison" else row for row in draft.links))
    else:
        draft = replace(draft, selected_operation_ids=(NAMESPACE + ".assay",))
    with pytest.raises(ValueError):
        compile_draft(draft)
    with pytest.raises(ValueError):
        scientific_work(draft, NAMESPACE + ".assay")


def test_worker_refuses_stale_configuration_before_solver_and_closes_ports(monkeypatch):
    source, query, _target, _draft, science = operands()
    runner, context, readers = worker("assay", science, [(science.supply.object_id, source), (science.query.object_id, query)])
    def forbidden(*args, **kwargs):
        raise AssertionError("bad configuration entered numerical work")
    from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join import operation_bindings
    monkeypatch.setattr(operation_bindings, "execute_kinetic_assay_bridge", forbidden)
    with pytest.raises(ValueError, match="immutable"):
        runner.execute(replace(context, config=replace(context.config, content_sha256="0" * 64)))
    assert all(reader.closed for reader in readers.values())


def test_assessment_rejects_wrong_predecessor_receipt_before_reading_comparison():
    source, query, target, _draft, science = operands()
    runner, context, _ = worker("assay", science, [(science.supply.object_id, source), (science.query.object_id, query)])
    numerical = decode_result(runner.execute(context), KineticAssayBridgeResult)
    runner, context, readers = worker("assess", science, [(NAMESPACE + ".assay.product", numerical),
        (science.comparison.object_id, target)])
    wrong = replace(context.dependency_receipts[0], task_id="task.other")
    with pytest.raises(ValueError, match="receipt"):
        runner.execute(replace(context, dependency_receipts=(wrong,)))
    assert all(reader.closed for reader in readers.values())


def test_unidentified_kinetics_stay_unentered_through_registered_consumers():
    source, query, target, _draft, _science = operands()
    partial = replace(source.members[0], constants=None, unresolved_terms=("oxygenation-kinetics",))
    source = replace(source, members=(partial,))
    draft = kinetic_join_draft(source, query, target, relative_tolerance=Decimal("1e-10"))
    science = decode_canonical_bytes(draft.operations[0].config_payload.encode(), KineticJoinConfig, maximum_bytes=None).science
    runner, context, _ = worker("assay", science, [(science.supply.object_id, source), (science.query.object_id, query)])
    numerical = decode_result(runner.execute(context), KineticAssayBridgeResult)
    assert numerical.assay_solver_calls == 0
    runner, context, _ = worker("assess", science, [(NAMESPACE + ".assay.product", numerical),
        (science.comparison.object_id, target)])
    assessed = decode_result(runner.execute(context), KineticJointTargetAssessment)
    assert assessed.robust_conditional_target_disposition is AssessmentDisposition.UNEVALUABLE


def test_cold_descriptor_import_does_not_initialize_numerical_or_molecular_engines():
    code = (
        "import sys; import empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.executable_binding; "
        "assert not {'numpy','scipy','openmm','pyscf','ash','pybamm'} & set(sys.modules)"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_existing_composition_exports_resolve_to_the_same_explicit_owner():
    import empirical_lawhood.adapters.composition as compositions
    from empirical_lawhood.adapters.composition import acquisition_recurrence_margin_contracts as owner
    assert all(getattr(compositions, name) is getattr(owner, name) for name in compositions.__all__)
    with pytest.raises(AttributeError):
        compositions.unregistered_export


def test_source_canonical_identity_remains_exact_and_nonpromotable():
    source, query, target, draft, science = operands()
    changed = replace(source, context=replace(source.context, temperature_k=Decimal("300")))
    with pytest.raises(ValueError):
        kinetic_join_draft(changed, query, target, relative_tolerance=Decimal("1e-10"))
    with pytest.raises(ValueError, match="material/query"):
        runner, context, _ = worker("assay", science,
            [(science.supply.object_id, replace(source, supply_id="supply.substituted")), (science.query.object_id, query)])
        runner.execute(context)
    assert decode_canonical_bytes(source.canonical_bytes(), JointKineticSupply, maximum_bytes=None) == source
    assert "zero fresh biological units" in draft.development_study.claims[0].estimand
