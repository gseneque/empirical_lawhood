# SPDX-License-Identifier: MPL-2.0
"""Revision-native controls over disclosed typed release fixtures only.

Literal observations and unpublished locators establish no source eligibility,
native acquisition, issue, reveal or scientific qualification.
"""
from dataclasses import fields, replace
from decimal import Decimal as D, localcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_bindings as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import (
    MatrixRevisionSelectedPackage, MatrixRevisionPreparedProgramme,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_entry import MatrixRevisionEntryEvidence
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_results import assess_revision_programme
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_workers import SelectedRevisionWorker
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_operational_resources import MatrixSelectedOperationalResources
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as e4
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4PointModels, SelectedE4RevisionPoint, POINT_ONLY
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4DevelopmentProduct
from empirical_lawhood.api import matrix_selected_revision_runtime as runtime
from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from tests.test_matrix_selected_e4_methods import selected_calibrated, selected_revision, selected_e4_populations, selected_bridge, transfer, confirmation_products, pin  # noqa: F401
from tests.test_matrix_selected_opportunity import opportunity, literal_observations, unpublished, campaign_fixture  # noqa: F401
from tests.test_matrix_sampling_follow_on import prior_product


def _original(pin):
    value = prior_product(pin)
    return MatrixSelectedOriginalProduct(value.prior_execution, value.reveal_authority)


def _development(record, task):
    reference = record.identity
    return SelectedE4DevelopmentProduct(reference, "unpublished/e4-development", "run.unpublished-e4-development",
        pin("plan.unpublished-e4-development", DevelopmentExecutionPlan.SCHEMA), task,
        pin("receipt." + task, CanonicalTaskReceipt.SCHEMA), unpublished(record, "publication." + task))


@pytest.fixture(scope="module")
def revision_case(selected_calibrated, opportunity, transfer):  # noqa: F811
    f = selected_calibrated
    confirmation = confirmation_products(f)
    nomination = e4.nominate_downstream(confirmation.specification, confirmation.result, f.export,
        confirmation.public_calibration, record_id="downstream.nomination.revision-native-control")
    assert nomination.selected == "REVISION"
    models = SelectedE4PointModels.from_models(f.export.models, record_id="models.revision-native-control")
    selected = MatrixRevisionSelectedPackage("package.revision-native-control", models, nomination.identity, f.result.identity)
    original_e3 = f.revision.bank.forecast_design.package
    groups = tuple(sorted({*original_e3.training_unit_ids, *original_e3.selection_unit_ids,
        *f.revision.programme.group_ids, *f.programme.group_ids, *confirmation.programme.group_ids}))
    programme = MatrixRevisionPreparedProgramme("programme.revision-native-control", "E5_OPPORTUNITY", selected,
        opportunity.sources, opportunity.reservation, opportunity.point_design.arms, 1, opportunity.assay,
        opportunity.panels, opportunity.criterion, groups, opportunity.minimum_recoverable_groups,
        opportunity.tie_policy, (), None)
    evidence = MatrixRevisionEntryEvidence("evidence.revision-native-control", programme.identity,
        _development(f.revision.nomination, "task.original-revision-fit"), _development(f.revision.frozen, "task.original-revision-freeze"),
        _original(nomination.identity), _original(f.result.identity), f.export.identity, confirmation.public_calibration,
        nomination.original_e3_package, None, None, None, (), (), None)
    resources = MatrixSelectedOperationalResources("resources.revision-native-control", "OPPORTUNITY",
        tuple((phase, ResourceBudget(1, 2 * 1024**3, 0, None, 2 * 1024**3, None))
            for phase in sorted(("design", "history", "assess", "measure", "frames", "project", "point", "mechanical", "responses", "response-score", "nominate"))))
    return SimpleNamespace(programme=programme, evidence=evidence, resources=resources, original=opportunity, transfer=transfer)



def committed_graph(case):
    """Disclosed current graph metadata; no actual original-parent custody."""
    from tests.matrix_selected_commitment_fixture import unpublished_committed_evidence
    from tests.test_matrix_selected_declarative_preparation import disclosed_produced_parents
    evidence = unpublished_committed_evidence(case.evidence)
    parents = disclosed_produced_parents((evidence.downstream_nomination, evidence.calibration),
        (evidence.revision_fit, evidence.revision_freeze,
            *((evidence.preparation_nomination,) if evidence.preparation_nomination is not None else ())))
    return owner.contracts(case.programme, evidence.identity, len(evidence.canonical_bytes()), produced_input_parents=parents)


def observations(case):
    programme = case.programme
    result = {}
    for name, (_, mechanical, readout) in literal_observations(case.original).items():
        source = next(source for _, source in programme.source_arms() if "case." + source.source_id == name)
        disposition, revision, baseline = programme.selected_package.models.predict(source.coordinate)
        point = SelectedE4RevisionPoint("point.revision." + source.source_id, programme.selected_package.nomination,
            programme.selected_package.models.identity, programme.selected_package.original_calibration, source.identity,
            source.recipe.identity, ObjectIdentity.from_record(source.coordinate.coordinate_id, source.coordinate),
            mechanical.causal, InformationCutoff("cutoff." + source.source_id, source.coordinate.clock_id,
                CausalPhase.PRE_ACTION, source.coordinate.physical_time(source.total_ticks)), "b" * 64,
            disposition, revision, baseline)
        # Physical reference and score use the exact unchanged native assay.
        protocol = programme.protocol(source)
        physical_pin = ObjectIdentity.from_record(protocol.protocol_id, protocol)
        arrays = replace(mechanical.arrays, original_protocol=physical_pin)
        mechanical = replace(mechanical, original_protocol=physical_pin, arrays=arrays)
        readout = replace(readout, original_protocol=physical_pin, forecast=arrays.identity)
        result[name] = point, mechanical, readout
    return result


def test_raw_paired30_reducer_uses_original_target_decimal_equation_and_complete_cases(revision_case):
    case = revision_case
    actual = observations(case)
    manifest, result = assess_revision_programme(case.programme, actual, result_id="result.revision-native")
    assert len(result.cases) == len(manifest.rows) == 3
    for row in result.cases:
        point, _, readout = actual[row.case_id]
        with localcontext() as context:
            context.prec = 50
            expected = tuple((D(1) + max(cell.normalized_error for cell in readout.cells
                if cell.view == view and cell.predictor == predictor and cell.horizon_tick <= horizon)).ln()
                for view in ("PRIMARY", "FINE") for predictor in PREDICTORS
                for horizon in case.programme.selected_package.models.target.horizon_ticks)
        assert row.actual_log_targets == expected
        assert row.revision_log_predictions == point.revision_predictions
        assert row.baseline_log_predictions == point.baseline_predictions
        assert len(row.absolute_revision_errors) == len(row.absolute_baseline_errors) == 30
        assert row.uncertainty_status == POINT_ONLY and row.functional.error_upper is None
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    del actual[next(iter(actual))]
    _, missing = assess_revision_programme(case.programme, actual, result_id="result.revision-missing")
    assert len(missing.cases) == 3 and sum(row.functional.disposition == "MISSING" for row in missing.cases) == 1


def test_unsupported_grid_keeps_independent_functional_assay_and_never_uses_e3(revision_case):
    old = revision_case.transfer
    programme = replace(revision_case.programme, record_id="programme.revision-unsupported-transfer", phase="E6_TRANSFER",
        sources=old.sources, reservation=old.sources.closure.reservation, arms=old.point_design.arms,
        expected_groups=old.point_design.expected_groups, assay=old.assay, panels=old.panels, criterion=old.criterion,
        transfer_domain_claims=old.transfer_domain_claims)
    selected = SimpleNamespace(programme=programme, original=old)
    values = observations(selected)
    unsupported = {name for name, (point, _, _) in values.items() if point.disposition == "UNSUPPORTED_DECLARED_GRID"}
    supported = {name for name, (point, _, _) in values.items() if point.disposition == "PREDICTED"}
    assert unsupported and supported
    assert unsupported | supported == set(values)
    _, result = assess_revision_programme(programme, values, result_id="result.revision-nonuse",
        original_allocation=old.point_design.package.allocation)
    sources = {"case." + source.source_id: source for _, source in programme.source_arms()}
    assert {row.case_id for row in result.cases} == set(values)
    for row in result.cases:
        assert row.functional.disposition == "FINITE"
        if row.case_id in unsupported:
            assert row.revision_log_predictions == row.baseline_log_predictions == (None,) * 30
            assert row.absolute_revision_errors == row.absolute_baseline_errors == (None,) * 30
            assert not row.functional.conditional_admission
            assert "REVISION_POINT_UNSUPPORTED_DECLARED_GRID" in row.functional.reasons
        else:
            disposition, revision, baseline = programme.selected_package.models.predict(sources[row.case_id].coordinate)
            assert disposition == "PREDICTED"
            assert row.revision_log_predictions == revision == values[row.case_id][0].revision_predictions
            assert row.baseline_log_predictions == baseline == values[row.case_id][0].baseline_predictions
            with localcontext() as context:
                context.prec = 80
                for predictions, errors in ((revision, row.absolute_revision_errors), (baseline, row.absolute_baseline_errors)):
                    assert errors == tuple(abs(actual - prediction)
                        for actual, prediction in zip(row.actual_log_targets, predictions, strict=True))


def test_graph_has_actual_revision_point_before_every_native_future_and_no_forecast_rng(revision_case):
    configs, _, links, _, _ = committed_graph(revision_case)
    for node, config in configs:
        if config.phase in owner.NATIVE:
            old_type = owner.preparation.MatrixPreparationOperationConfig if config.phase == "history" else owner.MatrixRevisionFutureConfig
            obsolete = old_type(**{field.name: getattr(config, field.name) for field in fields(config)})
            with pytest.raises(ValueError, match="current direct-input"):
                owner.phase_of(obsolete)
        if config.phase == "responses":
            edges = tuple(link for link in links if link.consumer_node_id == node and link.consumer_input_id == "point")
            assert len(edges) == 1 and edges[0].producer_node_id.endswith(".point")
        if config.phase == "point":
            assert set(owner.INPUTS["point"]) == {"point-package", "protocol", "causal", "witness", "causal-arrays",
                "diagnostic-arrays", "mechanical", "mechanical-arrays", "entry"}
            for port in ('mechanical', 'mechanical-arrays'):
                edge, = (link for link in links if link.consumer_node_id == node and link.consumer_input_id == port)
                assert edge.producer_node_id.endswith('.mechanical')
            assert owner.PHASES.index('mechanical') < owner.PHASES.index('point')
            assert not hasattr(config.public_source, "streams")
    final = next(node for node, config in configs if config.phase == "assess-programme")
    entry = next(node for node, config in configs if config.phase == "entry")
    allocation_edge, = (row for row in links if row.consumer_node_id == final and row.consumer_input_id == "original-allocation")
    assert allocation_edge.external_input_id is None
    assert (allocation_edge.producer_node_id, allocation_edge.producer_output_id) == (entry, "original-allocation")
    declarations = owner.operation_declarations()
    phases = ("entry", "history", "assess", "measure", "frames", "project", "point", "mechanical",
        "responses", "response-score", "assess-programme")
    expected = {(f"matrix-selected-revision-prepared.{lane}.{phase}", owner.phase_version(phase))
        for lane in ("development", "protected") for phase in phases if phase not in ("entry", *owner.NATIVE)}
    expected.update((f"matrix-selected-revision-prepared.{lane}.entry-original-commitments", "2.0.0")
        for lane in ("development", "protected"))
    expected.update((f"matrix-selected-revision-prepared.{lane}.{phase}.direct-inputs", "2.0.0")
        for lane in ("development", "protected") for phase in ("history", "responses"))
    assert len(declarations) == len(expected) == 22
    assert {(row.capability_key, row.capability_version) for row in declarations} == expected
    for lane in ("DEVELOPMENT", "PROTECTED"):
        with pytest.raises(ValueError, match="installed original entry edition"):
            owner.capability_key("entry", lane)
        for phase in owner.NATIVE:
            with pytest.raises(ValueError, match="installed original entry edition"):
                owner.capability_key(phase, lane)
            with pytest.raises(ValueError, match="current direct-input"):
                owner.phase_inputs(phase)
    for declaration in declarations:
        if declaration.runner_factory().phase == "entry":
            from empirical_lawhood.kernel.experimental_design import UnitAllocation
            assert next(row for row in declaration.outputs if row.output_id == "original-allocation").payload_schema == UnitAllocation.SCHEMA
        if declaration.capability_key.endswith(".direct-inputs"):
            phase = declaration.runner_factory().phase
            expected_config = owner.preparation.MatrixPreparationOperationConfigV2 if phase == "history" else owner.MatrixRevisionFutureConfigV2
            assert declaration.config_record_type is expected_config
            streams, = (row for row in declaration.input_ports if row.port_id == "native-stream")
            assert streams.minimum_count == streams.maximum_count == (2 if phase == "history" else 4)
            assert any(row.port_id == "native-provenance" for row in declaration.input_ports)
    assert {row.runner_factory().phase for row in declarations if row.execution_properties.native_effect} == {"history", "responses"}
    assert all(row.execution_properties.runner_preparation_factory is not None for row in declarations)




def test_fresh_current_admission_refusal_precedes_original_science_or_native_contact(tmp_path, monkeypatch):
    from empirical_lawhood.api import recursive_authoring
    from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads
    from tests.test_recursive_public_service import _plane

    calls = []
    class OriginalAccess:
        def require_current(self):
            calls.append("fresh-original-access")
        def require_member(self, manifest):
            pytest.fail("current-task refusal opened original scientific members")
    writer = _plane(tmp_path / "current-admission")
    directory = Path(writer.root.contract.canonical_path) / "unread"
    # Empty typed members are a loader seam, never actual authored custody.
    access = OriginalAccess()
    payloads = AuthenticatedRecursivePayloads(plane=writer, directory=directory, members=(), original_input_access=access)
    calls.clear()  # Observe supplier admission after fixture construction.
    def load(**kwargs):
        assert kwargs == dict(directory=directory, artifact_writer=writer, lazy_payloads=True, read_access=None)
        calls.append("typed-loader-seam")
        return None, None, None, payloads
    def refuse(*args):
        calls.append("current")
        raise PermissionError("genuine current task required")
    def custody(**kwargs):
        assert kwargs["writer"] is writer and kwargs["directory"] == directory
        assert kwargs["payloads"] is payloads and kwargs["original_input_access"] is access
        return SimpleNamespace(current_task=refuse)
    monkeypatch.setattr(recursive_authoring, "load_authored_wave", load)
    monkeypatch.setattr(runtime, "CurrentDevelopmentTaskCustody", custody)
    monkeypatch.setattr(runtime, "authenticate_revision_entry", lambda *args, **kwargs: pytest.fail("read original scientific evidence before current admission"))
    supplier = runtime.RevisionRuntimeInputSupplier(object(), writer=writer, output_codecs={}, directory=directory, plan=object())
    declaration = next(row for row in owner.operation_declarations() if row.capability_key == owner.capability_key("history", "DEVELOPMENT", "2.0.0"))
    runner = SelectedRevisionWorker("history", "DEVELOPMENT", declaration.manifest())
    with pytest.raises(PermissionError, match="genuine current task"):
        supplier.prepare_selected_revision(object(), runner)
    assert calls == ["typed-loader-seam", "fresh-original-access", "fresh-original-access", "current"]
    with pytest.raises(PermissionError, match="actual native lifecycle"):
        runner.execute(SimpleNamespace(input_ports=()))




def test_revision_point_package_and_evidence_mismatch_refuse_before_any_native_body(revision_case, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_entry import validate_entry_evidence
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_native_body
    monkeypatch.setattr(prepared_native_body, "_execute_future_native", lambda *args, **kwargs: pytest.fail("native entry"))
    changed = replace(revision_case.evidence, programme=replace(revision_case.programme.identity, object_fingerprint="f" * 64))
    with pytest.raises(ValueError, match="original model freeze"):
        validate_entry_evidence(changed, revision_case.programme)
    values = observations(revision_case)
    name = next(iter(values))
    point, mechanical, readout = values[name]
    changed_point = replace(point, models=replace(point.models, object_fingerprint="f" * 64))
    with pytest.raises(ValueError, match="actual selected pre-future"):
        assess_revision_programme(revision_case.programme, {**values, name: (changed_point, mechanical, readout)}, result_id="result.refused")


def test_resource_consumer_and_runtime_lifecycles_are_exact_installed_selections():
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as public
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.extension_bundle import EXPERIMENT_PROTOCOL_DECLARATIONS
    from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding
    protocols = tuple(row for row in EXPERIMENT_PROTOCOL_DECLARATIONS
        if row.protocol_id in (public.DEVELOPMENT_PROTOCOL_ID, public.PROTECTED_PROTOCOL_ID))
    assert len(protocols) == 2
    configurations = {row.consumer_id: row for protocol in protocols for row in protocol.configuration_inputs}
    assert "matrix-selected-phase-resources" in configurations
    for protocol in protocols:
        binding = experiment_runtime_binding(protocol)
        if protocol.protocol_id == public.DEVELOPMENT_PROTOCOL_ID:
            assert callable(binding.bind_development_runtime) and binding.bind_handoff is None
        else:
            assert callable(binding.bind_handoff) and binding.bind_development_runtime is None


def _relabelled_revision_transfer(case):
    """Disclosed typed metadata only; this does not authenticate a reservation."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as original
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
    old = case.transfer
    semantic = old.point_design.package.allocation
    nearby = set(semantic.unit_ids("transfer_nearby"))
    closure = old.sources.closure
    allocation = replace(closure.reservation.allocation, roots=tuple(replace(row, root=replace(row.root,
        regime_id="z.actual-nearby" if row.root.independent_group_id in nearby else "a.actual-shifted"))
        for row in closure.reservation.allocation.roots))
    reservation = replace(closure.reservation, allocation=allocation,
        publication=unpublished(allocation, "publication.relabelled-transfer-allocation"))
    selection = replace(closure.specification.selection, reservation=original.identity(reservation))
    specification = replace(closure.specification, selection=selection,
        publication=unpublished(selection, "publication.relabelled-transfer-selection"))
    source_index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=closure.provenances)
    descriptors = tuple(source_index.reference(source_id="source." + row.root.root_id,
        root_id=row.root.root_id, provenance=closure.provenances[0].identity) for row in allocation.roots)
    closure = replace(closure, reservation=reservation, specification=specification,
        descriptors=descriptors)
    programme = replace(case.programme, record_id="programme.revision-semantic-role-control", phase="E6_TRANSFER",
        sources=replace(old.sources, closure=closure), reservation=reservation, arms=old.point_design.arms,
        expected_groups=old.point_design.expected_groups, assay=old.assay, panels=old.panels, criterion=old.criterion,
        transfer_domain_claims=("INTERPOLATION_WITHIN_ASSESSED_DOMAIN", "EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN"))
    return programme, semantic


def test_revision_transfer_uses_original_roles_with_reversed_labels_and_unequal_claims(revision_case):
    programme, allocation = _relabelled_revision_transfer(revision_case)
    _, result = assess_revision_programme(programme, {}, result_id="result.revision-semantic-roles",
        original_allocation=allocation)
    assert all(row.functional.disposition == "MISSING" for row in result.cases)
    assert tuple((row.comparison_id, row.transfer_regime_id, row.transfer_domain_claim, row.assigned_group_ids)
        for row in result.functional.comparisons) == (
        ("e6.nearby", "z.actual-nearby", "INTERPOLATION_WITHIN_ASSESSED_DOMAIN", allocation.unit_ids("transfer_nearby")),
        ("e6.shifted", "a.actual-shifted", "EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN", allocation.unit_ids("transfer_shifted")))


def test_revision_transfer_refuses_absent_or_incomplete_original_role_partition(revision_case):
    programme, allocation = _relabelled_revision_transfer(revision_case)
    with pytest.raises(TypeError, match="actual original semantic allocation"):
        assess_revision_programme(programme, {}, result_id="result.missing-original-allocation")
    changed = replace(allocation, roles=tuple(replace(row, role="unused-transfer")
        if row.role == "transfer_shifted" else row for row in allocation.roles))
    with pytest.raises(ValueError, match="original complete nearby/shifted role partition"):
        assess_revision_programme(programme, {}, result_id="result.missing-original-role", original_allocation=changed)


def test_revision_transfer_allocation_edge_requires_actual_entry_producer(revision_case):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import entry_seal
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_workers import _dependencies
    f = revision_case
    configs, _, links, _, _ = committed_graph(f)
    node, config = next((node, config) for node, config in configs if config.phase == "assess-programme")
    link, = (row for row in links if row.consumer_node_id == node and row.consumer_input_id == "original-allocation")
    edge = SimpleNamespace(consumer_input_id=link.consumer_input_id, producer_task_id=link.producer_node_id,
        producer_output_id=link.producer_node_id + "." + link.producer_output_id)
    received = {"entry": entry_seal(f.programme)}
    _dependencies(None, config, received, (edge,))
    for task, output in ((None, None), ("task.foreign-entry", edge.producer_output_id),
            (edge.producer_task_id, edge.producer_task_id + ".product")):
        changed = SimpleNamespace(consumer_input_id=edge.consumer_input_id, producer_task_id=task, producer_output_id=output)
        with pytest.raises(ValueError, match="exact actual ordinary producer"):
            _dependencies(None, config, received, (changed,))
