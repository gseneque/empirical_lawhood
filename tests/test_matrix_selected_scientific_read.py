# SPDX-License-Identifier: MPL-2.0
"""Retained protected-reader controls over disclosed software science.

Literal Matrix observations prove reduction/custody conformance only. The small
reference parent supplies actual software issue/reveal controls for refusal and
partial-read ordering; neither fixture supplies Matrix qualification or native
acquisition authority.
"""
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_selected_scientific_read as reader
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import forecast_selected_point
from empirical_lawhood.api.experiment_scientific_read import read_prepared_experiment_science
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.test_current_result_custody import actual_issued_current_task_controls  # noqa: F401
from tests.test_matrix_selected_protected import transfer, confirmation  # noqa: F401
from tests.test_matrix_selected_revision_native import (  # noqa: F401
    revision_case, observations, selected_calibrated, selected_revision, selected_e4_populations, selected_bridge, opportunity,
)  # noqa: F401
from tests.test_matrix_selected_opportunity import literal_observations
from tests.test_recursive_public_service import _plane
from tests.selected_reader_configuration_support import freeze_reader_terminal


def _literal_plan(tasks):
    return SimpleNamespace(execution_plan_id="plan.disclosed.selected-read", tasks=tuple(tasks),
        SCHEMA="empirical-lawhood/runtime/execution-plan", VERSION="1.0.0", fingerprint=lambda: "b" * 64)


@pytest.fixture(params=("original-conf", "original-transfer", "revision-conf", "revision-transfer"))
def science(request, transfer, confirmation, tmp_path, monkeypatch):  # noqa: F811
    is_revision = request.param.startswith("revision")
    base = transfer if request.param.endswith("transfer") else confirmation
    if is_revision:
        revision_case = request.getfixturevalue("revision_case")
        programme = replace(revision_case.programme, record_id="programme.disclosed.selected-read." + request.param,
            phase=base.phase, sources=base.sources, reservation=base.sources.closure.reservation,
            arms=base.point_design.arms, expected_groups=base.point_design.expected_groups, assay=base.assay,
            panels=base.panels, criterion=base.criterion, transfer_domain_claims=base.transfer_domain_claims,
            preparation_nomination=None if base.phase == "E6_TRANSFER" else ObjectIdentity("nomination.disclosed.selected-read",
                reader.revision.MatrixRevisionProgrammeAssessment.SCHEMA, "1.0.0", "a" * 64))
        values = observations(SimpleNamespace(programme=programme, original=base))
    else:
        programme = reader.original.MatrixSelectedPublicProgramme.from_programme(base)
        values = literal_observations(base)
    # One actual adverse numerical control remains in the complete census. For
    # revision transfer choose the supported point, leaving the unsupported
    # point's independently usable native functional result visible.
    bad = next((key for key, (point, _, _) in values.items() if not is_revision or point.disposition == "PREDICTED"), next(iter(values)))
    point, mechanical, readout = values[bad]
    control = readout.controls[0]
    errors = (2 * control.tolerance, *control.measured_errors[1:])
    control = replace(control, error=max(errors), measured_errors=errors, failed_steps=(1,), disposition="VIOLATED")
    values[bad] = point, mechanical, replace(readout, controls=(control, *readout.controls[1:]),
        numerical_pass=False, disposition="NATIVE_CROSSCHECK_FAILED", cumulative_log_errors=(None,) * 15)
    if not is_revision:
        # The native assay remains observed when the frozen point model cannot
        # consume this causal feature. Historical reduction remains unchanged.
        key = next(key for key in values if key != bad)
        point, mechanical, readout = values[key]
        feature = replace(point.feature, disposition="UNAVAILABLE", values=())
        values[key] = forecast_selected_point(programme.point_design, feature, record_id=point.record_id), mechanical, readout
    owner = reader.revision if is_revision else reader.original
    final_id = owner.global_node(programme, "assess-programme")
    entry_id = owner.global_node(programme, "entry")
    allocation = base.point_design.package.allocation if is_revision else None
    replay = (reader.assess_revision_programme(programme, values, result_id="result." + final_id, original_allocation=allocation)
        if is_revision else reader.assess_selected_programme(programme, values, result_id="result." + final_id))
    plane, tasks, receipts = _plane(tmp_path / "custody"), {}, {}
    products = {}
    edges = []
    run = "run.disclosed.selected-read"

    def publish(task_id, outputs, inputs=()):
        outputs = tuple(sorted(outputs))
        publications = tuple(plane.write(ArtifactWriteRequest("artifact." + task_id + "." + name,
            "selected-read/" + sha256((task_id + "." + name).encode()).hexdigest() + ".json", value.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            "application/json", "publication." + task_id + "." + name, "selected-read", value.canonical_bytes(),
            VisibilityCeiling.OUTCOME_VISIBLE, (), OutcomeAccess.EVALUATION_REVEALED)) for name, value in outputs)
        specs = tuple(SimpleNamespace(output_id=task_id + "." + name, logical_artifact_id=publication.logical.logical_artifact_id,
            payload_schema=value.SCHEMA) for (name, value), publication in zip(outputs, publications, strict=True))
        receipts[task_id] = CanonicalTaskReceipt("receipt." + task_id, run, task_id, "attempt." + task_id, "c" * 40,
            tuple(sorted(inputs)), tuple(publication.materialization for publication in publications),
            tuple(sorted((publication.logical for publication in publications), key=lambda row: row.logical_artifact_id)),
            (), OperationalStatus.SUCCEEDED, ())
        task = SimpleNamespace(task_id=task_id, outputs=specs)
        tasks[task_id] = task
        for (name, value), publication in zip(outputs, publications, strict=True):
            products[task_id, name] = value, publication
        return task

    seal = reader.revision_entry_seal(programme) if is_revision else reader.entry_seal(programme)
    entry_outputs = (("product", seal), ("original-allocation", allocation)) if is_revision else (("product", seal),)
    entry_task = publish(entry_id, entry_outputs)

    def consume(name, task, output="product"):
        spec, = (row for row in task.outputs if row.output_id == task.task_id + "." + output)
        edges.append(SimpleNamespace(consumer_input_id=name, producer_task_id=task.task_id,
            producer_output_id=spec.output_id, operational_logical_artifact_id=spec.logical_artifact_id))

    consume("entry", entry_task)
    if is_revision:
        consume("original-allocation", entry_task, "original-allocation")
    for case_id, row in sorted(values.items()):
        source_id = case_id.removeprefix("case.")
        for port, value in zip(("points", "mechanicals", "readouts"), row, strict=True):
            task = publish("task.disclosed." + port + "." + source_id, (("product", value),))
            consume(port + "." + source_id, task)
    dependencies = tuple(sorted(tasks))
    input_ids = tuple(sorted(material.materialization_id for receipt in receipts.values() for material in receipt.output_materializations))
    plan = _literal_plan(())
    root, _ = _fixture()
    package = SimpleNamespace(run_plan_id=run, system=replace(root.system, world=replace(root.system.world,
        kind=WorldKind.NUMERICAL_SIMULATOR, unrepresented_physics=("disclosed-software-world",))), experiment=root.experiment)
    adjudication = reader.ScientificAdjudicationRecord("adjudication." + final_id, run, final_id,
        reader._pin(plan, "execution_plan_id"), input_ids,
        tuple(sorted("artifact." + final_id + "." + name for name in ("manifest", "product", "adjudication"))),
        tuple(sorted(receipts[parent].receipt_id for parent in dependencies)), package.system.world.world_id,
        package.system.world.kind, reader._pin(package.experiment.relation, "relation_id"), package.experiment.independent_unit_id,
        tuple(reader._pin(cutoff, "cutoff_id") for cutoff in package.experiment.information_cutoffs),
        VisibilityCeiling.OUTCOME_VISIBLE, OutcomeAccess.EVALUATION_REVEALED, reader.AdjudicationEvaluability.UNEVALUABLE,
        reader.ScientificStatus.UNEVALUABLE, reader.AdmissionStatus.UNEVALUABLE,
        ("DOWNSTREAM_PREPARATION_OR_TRANSFER_CALIBRATION_APPLICABILITY_NOT_ESTABLISHED",))
    final = publish(final_id, (("manifest", replay[0]), ("product", replay[1]), ("adjudication", adjudication)), input_ids)
    final.scientific_inputs = tuple(edges)
    final.dependency_task_ids = dependencies
    final.capability = SimpleNamespace(capability_key=owner.capability_key("assess-programme", "PROTECTED" if is_revision else "1.0.0"))
    config=(owner.MatrixRevisionRootConfig('config.'+final_id,programme,'assess-programme') if is_revision
        else owner.MatrixSelectedProtectedRootConfig('config.'+final_id,programme,'assess-programme'))
    declaration,=(value for value in owner.operation_declarations()
        if value.capability_key==owner.capability_key('assess-programme','PROTECTED' if is_revision else '1.0.0'))
    final=freeze_reader_terminal(plane=plane,task=final,config=config,
        declaration=declaration,receipts=receipts)
    tasks[final_id]=final
    plan.tasks = tuple(tasks.values())
    entry = SimpleNamespace(programme=programme)
    monkeypatch.setattr(reader, "_configuration", lambda *args: SimpleNamespace(programme=programme, phase="assess-programme"))

    def read():
        with plane.verification_scope() as writer:
            result = reader._terminal_science(writer, package, plan, receipts, entry_task, entry, is_revision, allocation)
            writer.require_verification_snapshot()
            return result
    return SimpleNamespace(read=read, plane=plane, plan=plan, final=final, receipts=receipts, programme=programme,
        replay=replay, products=products, is_revision=is_revision, bad=bad)


def test_terminal_projection_retains_complete_adverse_and_native_functional_science(science):
    result = science.read()
    assert result["manifest"] == science.replay[0].to_document()
    assert result["assessment"] == science.replay[1].to_document()
    assert result["scientific_status"] == result["admission_status"] == "UNEVALUABLE"
    assert result["qualification"] == "NOT_ESTABLISHED" and result["downstream_uncertainty"] == "NOT_ESTABLISHED"
    assert sum(row["assigned_cases"] for row in result["denominators"].values()) == len(science.programme.roster.cases)
    assert sum(row["case_dispositions"]["UNEVALUABLE"] for row in result["denominators"].values()) >= 1
    secondary = result["secondary_all_horizon_readout"]
    assert len(secondary["adequacy"]) == len(science.programme.roster.cases) * 30
    assert sum(row["assigned_cases"] for row in secondary["counts"]) == len(science.programme.roster.cases)
    assert secondary["point_uncertainty"] == secondary["admission"] == "UNESTABLISHED"
    assert all(row["actual_error"] is None for row in secondary["adequacy"] if row["case_id"] == science.bad)
    native = result["native_functional_diagnostic"]
    assert native["scope"] == "NATIVE_ASSAY_ONLY_NO_POINT_OR_ADMISSION_CLAIM"
    assert len(native["cases"]) == len(native["readouts"]) == len(science.programme.roster.cases)
    assert sum(row["native_functional_usable_cases"] for row in result["denominators"].values()) == 1
    if not science.is_revision:
        # Both terminal cases have no point-conditioned error, while one actual
        # native functional assay is finite and retained independently.
        assert all(row.actual_error is None for row in science.replay[1].cases)
        assert sum(row["value"]["actual_error"] is not None for row in native["cases"]) == 1
    if science.programme.phase == "E6_TRANSFER":
        assert len(result["denominators"]) == 2
        assert all(row["assigned_units"] == 1 for row in result["denominators"].values())
        if science.is_revision:
            result_rows = science.replay[1].cases
            unsupported = tuple(row for row in result_rows if "REVISION_POINT_UNSUPPORTED_DECLARED_GRID" in row.functional.reasons)
            assert unsupported and all(row.functional.actual_error is not None for row in unsupported)
            assert all(row.revision_log_predictions == (None,) * 30 for row in unsupported)
            ids = {row.case_id for row in unsupported}
            assert all(row["actual_error"] is not None for row in secondary["adequacy"] if row["case_id"] in ids)
            assert all(row["decision"] == "FORECAST_NONUSE" for row in secondary["failure_detection"] if row["case_id"] in ids)


@pytest.mark.parametrize("damage", ("source", "protocol", "panels"))
def test_native_functional_diagnostic_refuses_foreign_assay_inputs(transfer, damage):  # noqa: F811
    programme = reader.original.MatrixSelectedPublicProgramme.from_programme(transfer)
    case = programme.roster.cases[0]
    source = next(source for _, source in programme.sources.source_arms() if "case." + source.source_id == case.case_id)
    score = literal_observations(programme)[case.case_id][2]
    field = {"source": "source", "protocol": "original_protocol", "panels": "panels"}[damage]
    old = getattr(score, field)
    value = (replace(old[0], object_fingerprint="f" * 64), old[1]) if damage == "panels" else replace(old, object_fingerprint="f" * 64)
    score = replace(score, **{field: value})
    with pytest.raises(ValueError, match="original source, protocol or panels"):
        reader.native_functional_case(programme.criterion, case, source, score,
            protocol=programme.protocol(source), panels=dict(programme.panels)[case.unit_id])


def test_native_functional_missing_case_cannot_create_point_or_admission(transfer):  # noqa: F811
    programme = reader.original.MatrixSelectedPublicProgramme.from_programme(transfer)
    case = programme.roster.cases[0]
    source = next(source for _, source in programme.sources.source_arms() if "case." + source.source_id == case.case_id)
    result = reader.native_functional_case(programme.criterion, case, source, None,
        protocol=programme.protocol(source), panels=dict(programme.panels)[case.unit_id])
    assert result.disposition == "MISSING" and result.actual_error is None
    assert result.error_point is result.error_upper is result.covered is None
    assert not (result.functional_reliable or result.conditional_admission or result.false_admission)


@pytest.mark.parametrize("damage", ("manifest-census", "comparison", "adjudication", "consumed-edge", "bytes"))
def test_terminal_science_refuses_consistent_republication_and_consumed_or_byte_substitution(science, damage):
    if damage == "consumed-edge":
        edge=next(row for row in science.final.scientific_inputs if row.consumer_input_id=='entry')
        science.final=replace(science.final,scientific_inputs=tuple(
            replace(row,consumer_input_id='foreign.entry') if row is edge else row
            for row in science.final.scientific_inputs))
        science.plan.tasks=tuple(science.final if row.task_id==science.final.task_id else row for row in science.plan.tasks)
    elif damage == "bytes":
        _, publication = science.products[science.final.task_id, "product"]
        science.plane.root.resolve(publication.materialization.relative_path, for_write=False).write_bytes(b"changed")
    else:
        # Canonical records are independently republished through actual guarded
        # custody. Altered content must fail the scientific replay, not its hash.
        output = {"manifest-census": "manifest", "comparison": "product", "adjudication": "adjudication"}[damage]
        value, old = science.products[science.final.task_id, output]
        if damage == "manifest-census":
            value = replace(value, rows=value.rows[:-1])
        elif damage == "adjudication":
            value = replace(value, required_receipt_ids=("receipt.foreign",))
        else:
            functional = value.functional if science.is_revision else value
            first = functional.comparisons[0]
            functional = replace(functional, comparisons=(replace(first,
                criterion_met_conditionally=not first.criterion_met_conditionally), *functional.comparisons[1:]))
            value = replace(value, functional=functional) if science.is_revision else functional
        publication = science.plane.write(ArtifactWriteRequest(old.logical.logical_artifact_id + ".changed",
            old.materialization.relative_path + ".changed.json", value.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            "application/json", "publication.changed." + output, "selected-read", value.canonical_bytes(),
            VisibilityCeiling.OUTCOME_VISIBLE, (), OutcomeAccess.EVALUATION_REVEALED))
        receipt = science.receipts[science.final.task_id]
        science.receipts[science.final.task_id] = replace(receipt,
            output_materializations=tuple(publication.materialization if row == old.materialization else row
                for row in receipt.output_materializations),
            output_logical_artifacts=tuple(sorted((publication.logical if row == old.logical else row
                for row in receipt.output_logical_artifacts), key=lambda row: row.logical_artifact_id)))
        spec, = (row for row in science.final.outputs if row.output_id == science.final.task_id + "." + output)
        science.final=replace(science.final,outputs=tuple(
            replace(row,logical_artifact_id=publication.logical.logical_artifact_id,
                relative_path=publication.materialization.relative_path) if row is spec else row
            for row in science.final.outputs))
        science.plan.tasks=tuple(science.final if row.task_id==science.final.task_id else row for row in science.plan.tasks)
    with pytest.raises((PermissionError, ArtifactIdentityConflict, ValueError)):
        science.read()


def _selected_reference(f):
    return SimpleNamespace(association=SimpleNamespace(candidate=reader._pin(f.control.package.issued_study.candidate, "candidate_id")),
        implementation=f.control.package.issued_study.source_closure, projection=f.plan)


def test_actual_software_issued_partial_read_defers_before_protected_products(actual_issued_current_task_controls, transfer, monkeypatch):  # noqa: F811
    f = actual_issued_current_task_controls
    monkeypatch.setattr(reader, "_design", lambda selected: (
        SimpleNamespace(account='ORIGINAL_E3', criterion=transfer.criterion), reader.declarative.allocation(transfer)))
    def forbidden(*args, **kwargs):
        pytest.fail("partial read entered protected or original-source payload")
    monkeypatch.setattr(reader, "_entry", forbidden)
    monkeypatch.setattr(reader, "_product", forbidden)
    from empirical_lawhood.api import recursive_operations
    monkeypatch.setattr(recursive_operations, "operation_catalog", forbidden)
    result = reader.read_selected_protected_result(selected=_selected_reference(f), artifact_writer=f.control.service.artifact_plane,
        run_id=f.context.run_id, allow_partial=True)
    assert result["assessment"] is result["adjudication"] is None
    assert result["typed_product_validation"] == "DEFERRED" and result["new_native_contact_count"] == 0
    assert len(result["denominators"]) == 2


@pytest.mark.parametrize("damage", ("missing-reveal", "changed-grant", "foreign-source"))
def test_actual_software_issue_refuses_before_scientific_payload(actual_issued_current_task_controls, transfer, monkeypatch, damage):  # noqa: F811
    f = actual_issued_current_task_controls
    selected = _selected_reference(f)
    monkeypatch.setattr(reader, "_design", lambda selected: (
        SimpleNamespace(account='ORIGINAL_E3', criterion=transfer.criterion), reader.declarative.allocation(transfer)))
    monkeypatch.setattr(reader, "_entry", lambda *args: pytest.fail("invalid current authority read science"))
    if damage == "foreign-source":
        selected.implementation = replace(selected.implementation, source_closure_id=selected.implementation.source_closure_id + ".foreign")
    elif damage == "changed-grant":
        load = ExternalStudyOperationAuthorityStore.load
        def changed(store, authority_id):
            value = load(store, authority_id)
            return replace(value, expires_at_utc="2026-08-23T20:43:00Z") if authority_id == f.control.package.execution_authority.authority_id else value
        monkeypatch.setattr(ExternalStudyOperationAuthorityStore, "load", changed)
    with pytest.raises(PermissionError):
        reader.read_selected_protected_result(selected=selected, artifact_writer=f.control.service.artifact_plane,
            run_id=f.context.run_id, reveal_authority_id=None if damage == "missing-reveal" else f.control.reveal.authority_id)


def test_current_protected_protocol_dispatches_the_ordinary_scientific_reader(monkeypatch):
    from empirical_lawhood.api import generated_experiment_runtime_bindings as generated
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.experiment_binding import EXPERIMENT_RUNTIME_BINDING as declarative
    bindings = (declarative,)
    monkeypatch.setattr(generated, "EXPERIMENT_RUNTIME_BINDINGS", bindings)
    calls = []
    def read(**kwargs):
        calls.append(kwargs)
        return {"assessment": "typed-dispatch-control", "qualification": "NOT_ESTABLISHED"}
    monkeypatch.setattr(reader, "read_selected_protected_result", read)
    for binding in bindings:
        schemas = tuple((schema, version) for schema, version, protocol in generated.EXPERIMENT_SPECIFICATION_PROTOCOLS
            if protocol == binding.protocol_id)
        assert len(schemas) == 1 and schemas[0][0] == binding.specification_schema
        schema, version = schemas[0]
        selected = SimpleNamespace(instance=SimpleNamespace(specification=ObjectIdentity("specification.disclosed.selected-read", schema, version, "a" * 64)))
        assert read_prepared_experiment_science(selected=selected, artifact_writer=object(), run_id="run.disclosed.selected-read",
            reveal_authority_id="authority.disclosed.selected-read")["assessment"] == "typed-dispatch-control"
        wrong = SimpleNamespace(instance=SimpleNamespace(specification=replace(selected.instance.specification, object_version="99.0.0")))
        with pytest.raises(ValueError, match="exact installed specification revision"):
            read_prepared_experiment_science(selected=wrong, artifact_writer=object(), run_id="run.disclosed.selected-read")
    assert len(calls) == 1 and not calls[0]["allow_partial"]


@pytest.mark.parametrize('damage',(None,'missing-config','foreign-config','config-alias'))
def test_issued_configuration_lane_uses_exact_frozen_census_before_body(science,monkeypatch,damage):
    """Actual ExecutionTask metadata, not a permission or native-entry claim."""
    from empirical_lawhood.api import matrix_selected_runtime as runtime
    from empirical_lawhood.runtime.plans import ScientificInputRole
    task=science.final
    config,=(edge for edge in task.scientific_inputs
        if edge.scientific_role is ScientificInputRole.CONFIGURATION)
    if damage=='missing-config':
        task=replace(task,scientific_inputs=tuple(edge for edge in task.scientific_inputs if edge is not config))
    elif damage=='foreign-config':
        task=replace(task,scientific_inputs=tuple(replace(edge,external_input_id='compiler.configuration.foreign')
            if edge is config else edge for edge in task.scientific_inputs))
    elif damage=='config-alias':
        ordinary=next(edge for edge in task.scientific_inputs if edge is not config)
        task=replace(task,scientific_inputs=tuple(replace(edge,
            operational_logical_artifact_id=task.capability.config.artifact_id) if edge is ordinary else edge
            for edge in task.scientific_inputs))
    monkeypatch.setattr(runtime,'read_bounded_bytes',lambda *args,**kwargs:pytest.fail('configuration metadata check opened a body'))
    if damage is None:
        spec,=(row for row in task.external_inputs if row.input_id=='config')
        assert runtime._issued_configuration_lane(task)=={
            'expected_outcome_access':spec.expected_outcome_access,
            'expected_visibility_ceiling':spec.expected_visibility_ceiling}
    else:
        with pytest.raises(ValueError,match='CONFIGURATION|configuration'):
            runtime._issued_configuration_lane(task)
