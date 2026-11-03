# SPDX-License-Identifier: MPL-2.0
"""Exposed original-shaped E4 records and real numerical fitting; no native work."""

from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
from itertools import product
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_selection as method
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_records as pr, programme_reduction as rr
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledArrays, ScheduledCausalPrefix, ScheduledSource, identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import ScheduledCompactBank
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseLossCell, ScheduledResponseScore
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.adapters.methods.matrix_factor_response.records import ACTION_ROLES, PREDICTORS
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_selection import DeclaredCandidate, DeclaredSelectionDesign, WholeUnitFold
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from tests.test_matrix_parameter_native import coordinate


def pin(name, schema="empirical-lawhood/testing/exposed-selection-pin", version="1.0.0"):
    return ObjectIdentity(name, schema, version, sha256(name.encode()).hexdigest())


def _prefix(case, coordinate):
    root = MatrixProgrammeRoot(case.root_id, case.independent_group_id, "regime.exposed", coordinate.coordinate_id,
        MatrixProgrammeRole.DEVELOPMENT, coordinate.clock_id)
    arrays = ScheduledArrays("arrays."+case.root_id, case.source, "CAUSAL_STATE",
        ArtifactIdentity("array."+case.root_id, "exposed-no-native-arrays", MATRIX_ARRAY_SCHEMA, "1"*64, "application/x-npz", 8),
        (MatrixArrayMember("positions", "<f8", (1,), "1"*64, True),), (case.source,),
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    return ScheduledCausalPrefix("prefix."+case.root_id, case.source,
        pin("history."+case.root_id, "empirical-lawhood/matrix-scheduled-history/prefix-history"),
        pin("numerical."+case.root_id, "empirical-lawhood/matrix-scheduled-history/numerical-assessment"),
        pin("witness."+case.root_id, "empirical-lawhood/matrix-scheduled-history/prefix-witness"),
        pin("frame."+case.root_id, "empirical-lawhood/matrix-scheduled-history/frame-assessment"),
        pin("policy."+case.root_id, "empirical-lawhood/matrix-scheduled-history/prefix-policy"),
        root, 1, "2"*64, "AVAILABLE", None, arrays)


def _score(case, prefix, criterion):
    controls = (ScheduledResponseTransitionControl("control.exposed", "SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS",
        Decimal(0), Decimal(".01"), "SATISFIED", 1, 192, (Decimal(0),), ()),)
    values = []
    for view, panel, action, predictor, horizon in product(method.VIEWS, ("panel.common", "panel.fresh"),
            tuple("action.exposed." + role.lower() for role in ACTION_ROLES), PREDICTORS, (1, 2, 3)):
        temperature, friction, coupling = case.factor_values
        normalized = temperature**2/10 + friction/10 + coupling/10 + Decimal(view == "FINE")/8
        values.append(ScheduledResponseLossCell(view, panel, action, predictor, horizon, None, None, None, None, normalized))
    values.sort(key=lambda row: row.key)
    normalized = values[0].normalized_error  # The first sorted view is FINE.
    with localcontext() as context:
        context.prec = 50
        primary = (Decimal(1)+normalized-Decimal(1)/8).ln()
    return ScheduledResponseScore("score."+case.root_id, case.source, identity(prefix),
        pin("forecast."+case.root_id, "empirical-lawhood/matrix-scheduled-history/forecast-seal"),
        pin("physical."+case.root_id, "empirical-lawhood/matrix-scheduled-history/response-forecast"),
        pin("responses."+case.root_id, "empirical-lawhood/matrix-scheduled-history/native-responses"),
        case.root_id, case.independent_group_id, case.role, criterion, controls, True, "FINITE", tuple(values), (primary,)*15, ())


@pytest.fixture(scope="module")
def exposed():
    """Only typed fixture records: no simulation, population generator or signers."""
    factors = tuple(pr.ScheduledProgrammeFactor(name, "LINEAR", Decimal(1), Decimal(2), Decimal(3)) for name in method.PHYSICAL)
    families = tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
    grid = (*product((Decimal(1), Decimal(3)), repeat=3), (Decimal(2),)*3)
    cases, rows, results = [], [], []
    criterion = pin("criterion.original", MatrixResponseFrontierProtocol.SCHEMA)
    for group in range(32):
        for index, (temperature, friction, coupling) in enumerate(grid):
            root_id = f"root.exposed.{group:02}.{index}"
            original = coordinate((".5", str(coupling), str(friction), str(temperature)), family=FOUR_FAMILY_PREPARATION_IDS.index(families[group//8]))
            original = replace(original, coordinate_id=f"coordinate.exposed.{group//8}.{index}")
            coord = ObjectIdentity.from_record(original.coordinate_id, original)
            source = pin("source."+root_id, ScheduledSource.SCHEMA, ScheduledSource.VERSION)
            case = pr.ScheduledProgrammeCase(root_id, f"group.exposed.{group:02}", families[group//8], "DEVELOPMENT", source,
                coord,
                (temperature, friction, coupling), sha256(f"exposed-streams.{group}".encode()).hexdigest(),
                InformationCutoff("cutoff."+root_id, original.clock_id, CausalPhase.PRE_ACTION, original.physical_time(1)))
            prefix = _prefix(case, original)
            score = _score(case, prefix, criterion)
            cases.append(case)
            rows.append(method.ScheduledRevisionCaseData(root_id, original, prefix, score))
            native = tuple(rr.ScheduledProgrammeNativeDisposition(phase, "COMPLETED",
                pin(root_id+"."+phase+".definition", "empirical-lawhood/runtime/native-subwork-definition"),
                pin(root_id+"."+phase+".completion", "empirical-lawhood/runtime/native-subwork-completion"),
                pin(root_id+"."+phase+".receipt", "empirical-lawhood/runtime/canonical-task-receipt"), ()) for phase in rr.NATIVE_PHASES)
            results.append(rr.ScheduledProgrammeCaseResult(root_id, source, case.independent_group_id, "COMPLETED", "SATISFIED", "FINITE",
                score.cumulative_log_errors, (Decimal(0),)*15, (None,)*15, score.error_forecast, identity(score),
                pin(root_id+".assessment", "empirical-lawhood/matrix-scheduled-history/full-assessment"),
                tuple(pin(root_id+f".receipt.{i:02}", "empirical-lawhood/runtime/canonical-task-receipt") for i in range(11)), native, ()))
    groups = tuple(sorted({case.independent_group_id for case in cases}))
    waves = tuple(pr.ScheduledProgrammeWave(f"wave.exposed.{i//8}", groups[i:i+8],
        tuple(case.root_id for case in cases if case.independent_group_id in groups[i:i+8])) for i in range(0, 32, 8))
    programme = pr.ScheduledProgramme("programme.exposed-selection", "E4_DEVELOPMENT",
        pin("bank.original", ScheduledCompactBank.SCHEMA, ScheduledCompactBank.VERSION),
        pin("reservation.original", "empirical-lawhood/matrix-scheduled-history/reservation"),
        pin("allocation.original", "empirical-lawhood/matrix-scheduled-history/allocation"),
        pin("specification.original", "empirical-lawhood/matrix-scheduled-history/specification"),
        pin("forecast-design.original", "empirical-lawhood/matrix-scheduled-history/forecast-design"),
        pin("response-selection.original", "empirical-lawhood/matrix-scheduled-history/response-selection"), criterion, None,
        factors, tuple(cases), tuple(case.source for case in cases), waves, Decimal(".95"), 32)
    wave_results = tuple(rr.ScheduledProgrammeWaveResult(wave.wave_id+".result", programme.identity, wave.wave_id,
        wave.group_ids, wave.root_ids, tuple(row for row in results if row.root_id in wave.root_ids)) for wave in waves)
    reduction = rr.reduce_programme(programme, wave_results, reduction_id="reduction.exposed", authenticate_wave=lambda row: None)
    data = method.ScheduledRevisionDataBank("data.exposed", programme.identity, ObjectIdentity.from_record(reduction.reduction_id, reduction), tuple(rows))
    allocation = method.programme_selection_allocation(programme)
    target = method.ScheduledRevisionTarget("target.original", criterion, (1, 2, 3), method.VIEWS,
        "CUMULATIVE_LOG1P_NORMALIZED_RESPONSE_ERROR_ALL15")
    tunings = tuple(method.ScheduledRevisionTuning("tuning."+kind+str(i), method.FAMILY, tuple(sorted(method.PHYSICAL)),
        penalty, False, 4) for kind in ("baseline", "revision") for i, penalty in enumerate((Decimal(1), Decimal(10))))
    designs = []
    for kind in ("revision", "baseline"):
        candidates = tuple(DeclaredCandidate(kind+str(i), method.FAMILY, next(row.identity for row in tunings if row.tuning_id == "tuning."+kind+str(i))) for i in range(2))
        designs.append(DeclaredSelectionDesign("design."+kind, allocation.identity, "development", candidates,
            tuple(WholeUnitFold(group, i % 2) for i, group in enumerate(groups)), 2, 5,
            tuple(row.candidate_id for row in candidates), "MINIMIZE", "REQUIRE_COMPLETE", target.identity, criterion,
            method.feature_definition(programme).identity))
    specification = method.ScheduledRevisionSpecification("specification.exposed-selection", programme.identity, target,
        method.ScheduledRevisionTrigger("trigger.explicit", "MEAN_COMPLETE_GROUP_MAX_PAIRED_LOG_ERROR", "GREATER_THAN", Decimal(".1")),
        *designs, tunings)
    return SimpleNamespace(programme=programme, reduction=reduction, data=data, specification=specification)


@pytest.fixture(scope="module")
def nominated(exposed):
    return method.select_programme_revision(exposed.specification, exposed.programme, exposed.reduction, exposed.data,
        nomination_id="nomination."+exposed.specification.specification_id)


def test_actual_e4_consumer_fits_declared_penalties_whole_groups_and_frozen_baseline(exposed, nominated):
    assert nominated.trigger_disposition == "TRIGGERED" and nominated.missing_groups == ()
    assert nominated.endpoint_fit_calls == 300
    assert nominated.revision_selection.fit_calls == nominated.baseline_selection.fit_calls == 4
    assert all(row.assigned_units == row.finite_units == 32 for row in nominated.revision_selection.summaries)
    assert nominated.revision_model.training_groups == exposed.programme.group_ids
    assert nominated.revision_model.tuning.penalty == Decimal(1)
    assert nominated.baseline_model.tuning.penalty == Decimal(1)
    assert all(row.training_rows == row.fitted_rows == 288 for row in nominated.revision_model.parameters)
    package = method.freeze_programme_revision(exposed.programme, nominated, freeze_id="frozen.exposed")
    assert package.revision.fitted_model == nominated.revision_model.identity
    assert package.baseline.fitted_model == nominated.baseline_model.identity
    assert package.revision.target == exposed.specification.target.identity
    assert decode_canonical_bytes(package.canonical_bytes(), method.ScheduledRevisionFrozenPackage, maximum_bytes=16384) == package


def test_independent_normal_equation_oracle_for_actual_original_paired_endpoint_fit(exposed, nominated):
    cases = exposed.programme.cases
    x = np.array([[float(value) for _, value in sorted(zip(method.PHYSICAL, case.factor_values, strict=True))] for case in cases])
    mean, scale = x.mean(axis=0), x.std(axis=0)
    z = np.column_stack((np.ones(len(x)), (x-mean)/scale))
    targets = np.array([float(row.score.cumulative_log_errors[0]) for row in exposed.data.cases])
    penalty = np.diag([0.0, 1.0, 1.0, 1.0])
    # This independently constructs the actual full-data normal equations.
    expected = np.linalg.solve(z.T @ z + penalty, z.T @ targets)
    actual = nominated.revision_model.parameters[0]
    assert np.allclose([float(value) for value in actual.coefficients], expected, rtol=1e-13, atol=1e-13)
    assert np.allclose([float(value) for value in actual.means], mean, rtol=0, atol=0)
    assert nominated.revision_model.parameters[15] != actual


def test_fine_targets_come_from_actual_cells_and_primary_matches_original_reduction(exposed):
    row = exposed.data.cases[0]
    targets = method._paired_targets(exposed.specification.target, row.score)
    assert targets[:15] == row.score.cumulative_log_errors
    with localcontext() as context:
        context.prec = 50
        assert targets[15] == (Decimal(1)+Decimal(".3")+Decimal(1)/8).ln()
    assert targets[15] != targets[0]
    bad = replace(row.score, cumulative_log_errors=(Decimal(9),)*15)
    with pytest.raises(ValueError, match="original primary score"):
        method._paired_targets(exposed.specification.target, bad)


@pytest.mark.parametrize("damage", ("missing-fine-cells", "fine-none", "missing-prefix"))
def test_one_missing_nested_coordinate_or_view_keeps_whole32_denominator_and_zero_fits(exposed, monkeypatch, damage):
    row = exposed.data.cases[0]
    if damage == "missing-fine-cells":
        score = replace(row.score, cells=tuple(cell for cell in row.score.cells if cell.view != "FINE"))
        row = replace(row, score=score)
    elif damage == "fine-none":
        score = replace(row.score, cells=tuple(replace(cell, normalized_error=None) if cell.view == "FINE" else cell for cell in row.score.cells))
        row = replace(row, score=score)
    else:
        row = replace(row, causal_prefix=None, score=None)
        score = None
    cases = ((exposed.reduction.cases[0] if score is None else replace(exposed.reduction.cases[0], score=identity(score))), *exposed.reduction.cases[1:])
    # Complete retained source/case values stay fixed; the original score pin is
    # consistently rebound only for this newly declared exposed adverse fixture.
    reduction = replace(exposed.reduction, cases=cases)
    data = replace(exposed.data, reduction=ObjectIdentity.from_record(reduction.reduction_id, reduction), cases=(row, *exposed.data.cases[1:]))
    def forbidden(*args, **kwargs):
        pytest.fail("incomplete whole-group selection entered fitting")
    monkeypatch.setattr(method, "fit_standardized_ridge", forbidden)
    result = method.select_programme_revision(exposed.specification, exposed.programme, reduction, data, nomination_id="nomination.incomplete")
    assert result.trigger_disposition == "UNEVALUABLE" and result.endpoint_fit_calls == 0
    assert result.missing_groups == (exposed.programme.group_ids[0],)
    assert all(row.assigned_units == 32 and row.finite_units == 0 for row in result.revision_selection.summaries)
    assert result.revision_selection.fit_calls == 0
    assert method.freeze_programme_revision(exposed.programme, result, freeze_id="frozen.unentered").disposition == "UNENTERED"


def test_nontriggered_revision_keeps_reserved_candidates_and_never_fits(exposed, monkeypatch):
    specification = replace(exposed.specification, trigger=replace(exposed.specification.trigger, threshold=Decimal(100)))
    monkeypatch.setattr(method, "fit_standardized_ridge", lambda *args, **kwargs: pytest.fail("nontriggered revision fitted"))
    result = method.select_programme_revision(specification, exposed.programme, exposed.reduction, exposed.data, nomination_id="nomination.unentered")
    assert result.trigger_disposition == "NOT_TRIGGERED" and result.endpoint_fit_calls == 0
    assert result.revision_selection.fit_calls == result.baseline_selection.fit_calls == 0
    assert len(result.revision_selection.scores) == 64 and result.revision_model is None


@pytest.mark.parametrize("damage", ("clock", "frame", "coordinate", "family", "criterion", "source", "role", "whole-group"))
def test_consistently_supplied_source_bank_cannot_bypass_original_association(exposed, damage):
    row = exposed.data.cases[0]
    if damage == "clock":
        row = replace(row, causal_prefix=replace(row.causal_prefix, cutoff_tick=2))
    elif damage == "frame":
        row = replace(row, causal_prefix=replace(row.causal_prefix, frame_sha256="3"*64))
    elif damage == "coordinate":
        row = replace(row, coordinate=replace(row.coordinate, coordinate_id="coordinate.foreign"))
    elif damage == "family":
        row = replace(row, coordinate=replace(row.coordinate, family_id=next(family for family in FOUR_FAMILY_PREPARATION_IDS if family != row.coordinate.family_id)))
    elif damage == "criterion":
        row = replace(row, score=replace(row.score, criterion=replace(row.score.criterion, object_fingerprint="3"*64)))
    elif damage == "source":
        row = replace(row, score=replace(row.score, source=replace(row.score.source, object_fingerprint="3"*64)))
    elif damage == "role":
        row = replace(row, causal_prefix=replace(row.causal_prefix, root=replace(row.causal_prefix.root, role=MatrixProgrammeRole.CONFIRMATION)))
    else:
        row = replace(row, causal_prefix=replace(row.causal_prefix, root=replace(row.causal_prefix.root, independent_group_id="group.foreign")))
    data = replace(exposed.data, cases=(row, *exposed.data.cases[1:]))
    with pytest.raises(ValueError, match="revision|original|causal|E4"):
        method.select_programme_revision(exposed.specification, exposed.programme, exposed.reduction, data, nomination_id="nomination.refused")


@pytest.mark.parametrize("phase", ("CALIBRATION", "CONFIRMATION", "TRANSFER"))
def test_exact_frozen_revision_and_baseline_are_required_before_future_and_target_change(exposed, nominated, phase):
    package = method.freeze_programme_revision(exposed.programme, nominated, freeze_id="frozen.exposed")
    fields = dict(phase=phase, model=nominated.revision_model, target=exposed.specification.target.identity,
        criterion=exposed.programme.criterion, features=exposed.specification.revision_design.features)
    assert method.require_revision_for_future_phase(exposed.programme, nominated, package, **fields) == package.revision
    with pytest.raises(ValueError, match="model, target, tolerance or feature"):
        method.require_revision_for_future_phase(exposed.programme, nominated, package, **(fields | {"target": pin("target.foreign")}))
    with pytest.raises(ValueError, match="joint revision/baseline freeze"):
        method.require_revision_for_future_phase(exposed.programme, nominated,
            replace(package, baseline=replace(package.baseline, fitted_model=pin("model.foreign"))), **fields)


def test_two_single_declarations_are_cold_and_preserve_old_record_bytes(exposed, monkeypatch):
    originals = tuple(record.canonical_bytes() for record in (exposed.programme, exposed.reduction))
    def forbidden(*args, **kwargs):
        pytest.fail("cold operation metadata constructed science")
    monkeypatch.setattr(method.ScheduledRevisionWorker, "__init__", forbidden)
    declarations = method.operation_declarations()
    assert len(declarations) == 2
    assert not any(row.registration().native_effect for row in declarations)
    assert {row.stage.value for row in declarations} == {"DEVELOP", "FREEZE"}
    assert tuple(record.canonical_bytes() for record in (exposed.programme, exposed.reduction)) == originals


def test_trigger_requires_explicit_finite_threshold_and_forbids_quiet_target_or_family_revision(exposed):
    with pytest.raises(ValueError):
        replace(exposed.specification.trigger, threshold=Decimal("NaN"))
    with pytest.raises(ValueError):
        replace(exposed.specification.target, numerical_views=("PRIMARY",))
    with pytest.raises(ValueError):
        replace(exposed.specification.tunings[0], family_id="pretend-ridge-penalty")
    with pytest.raises(ValueError, match="same information"):
        replace(exposed.specification, baseline_design=replace(exposed.specification.baseline_design, maximum_fit_calls=6))


def test_fraction_to_decimal_loss_keeps_exact_spelling_under_small_context():
    with localcontext() as context:
        context.prec = 2
        assert method._exact_decimal(Fraction(123456789, 10**8)) == Decimal("1.23456789")


def _compiled(exposed):
    """Use the owning domain lowerer and ordinary existing recursive compiler."""
    from pathlib import Path
    from empirical_lawhood.api import load_authoring
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    declarations = method.operation_declarations()
    campaign = replace(load_authoring(Path(__file__).parents[1]/"tests/fixtures/reference-campaign.json").campaign,
        budget=declarations[0].resources)
    lowered = method.lower_exposed_programme_selection(exposed.specification, exposed.programme, exposed.reduction,
        exposed.data, campaign=campaign)
    registry = CapabilityRegistry("registry.exposed-e4-selection", tuple(sorted((row.manifest() for row in declarations), key=lambda row: row.registry_id)))
    options = dict(registrations=tuple(row.registration() for row in declarations), registry=registry,
        implementation_commit="a"*40, output_codecs={schema: kind for row in declarations for schema, kind in row.record_codecs.items()})
    return lowered, options, compile_recursive_wave(draft=lowered.draft, **options)


def test_existing_compiler_preserves_actual_development_selection_then_independent_freeze(exposed):
    from empirical_lawhood.runtime.plans import BarrierKind
    lowered, _, compiled = _compiled(exposed)
    tasks = {row.task_id: row for row in compiled.execution_plan.tasks}
    select = tasks[method.selection_node_id(exposed.specification, "select-revision")]
    freeze = tasks[method.selection_node_id(exposed.specification, "freeze-revision")]
    assert len(tasks) == 2 and not select.dependency_task_ids and freeze.dependency_task_ids == (select.task_id,)
    assert freeze.barrier is BarrierKind.FREEZE
    assert lowered.draft.development_study.assigned_unit_ids == exposed.programme.group_ids
    assert len(lowered.input_records) == 4


@pytest.mark.parametrize("damage", ("future-root", "missing-freeze", "nomination-external", "future-data-port", "source-substitution"))
def test_actual_compiler_refuses_future_selection_and_freeze_dependency_bypass(exposed, damage):
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    lowered, options, _ = _compiled(exposed)
    draft = lowered.draft
    if damage == "future-root":
        root = replace(draft.development_study, assigned_unit_ids=draft.development_study.assigned_unit_ids[:-1])
        draft = replace(draft, development_study=root)
    elif damage == "missing-freeze":
        select = method.selection_node_id(exposed.specification, "select-revision")
        draft = replace(draft, selected_operation_ids=(select,))
    elif damage == "nomination-external":
        external = RecursiveExternalInput("external.bypassed-nomination", "input.bypassed-nomination", method.ScheduledRevisionNomination.SCHEMA,
            "application/json", 1, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, "1"*64)
        links = tuple(replace(row, producer_node_id=None, producer_output_id=None, external_input_id=external.input_id)
            if row.consumer_input_id == "nomination" else row for row in draft.links)
        draft = replace(draft, external_inputs=tuple(sorted((*draft.external_inputs, external), key=lambda row: row.input_id)), links=links)
    elif damage == "future-data-port":
        selected = method.selection_node_id(exposed.specification, "select-revision")
        draft = replace(draft, links=tuple(replace(row, consumer_input_id="calibration-outcomes")
            if row.consumer_node_id == selected and row.consumer_input_id == "data" else row for row in draft.links))
    else:
        draft = replace(draft, links=tuple(replace(row, external_input_id=method.selection_external_id(exposed.specification, "data"))
            if row.consumer_input_id == "programme" else row for row in draft.links))
    with pytest.raises(ValueError, match="E4|selection|input|port|scientific|unit|selected|canonical"):
        compile_recursive_wave(draft=draft, **options)


def _sealed_context(config, declaration, records):
    """Actual kernel-sealed operand cursors, no paths or replacement contexts."""
    import os
    from empirical_lawhood.infrastructure.artifact_stream_primitives import _anonymous_input_descriptor, _PreopenedBoundedReader, _seal_anonymous_input
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
    from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
    manifest = declaration.manifest()
    node = method.selection_node_id(config.specification, config.operation)
    records = ((config.config_id, config, WorkerInputKind.EXTERNAL),
        ("operand.programme", config.programme, WorkerInputKind.EXTERNAL),
        ("operand.specification", config.specification, WorkerInputKind.EXTERNAL), *records)
    ports = []
    try:
        for artifact_id, record, kind in records:
            raw = record.canonical_bytes()
            descriptor = _anonymous_input_descriptor()
            try:
                position = 0
                while position < len(raw):
                    position += os.write(descriptor, raw[position:])
                _seal_anonymous_input(descriptor)
                binding = WorkerInputBinding(artifact_id, "materialization."+artifact_id, record.SCHEMA, "application/json", len(raw),
                    VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE, kind)
                ports.append(WorkerInputPort(binding, _PreopenedBoundedReader(descriptor, maximum_bytes=len(raw))))
            except BaseException:
                os.close(descriptor)
                raise
        ports = tuple(sorted(ports, key=lambda row: row.artifact_id))
        materializations = tuple(sorted(port.materialization_id for port in ports if port.kind is WorkerInputKind.DEPENDENCY))
        receipts = () if not materializations else (DependencyReceiptBinding("receipt.exposed-selection",
            method.selection_node_id(config.specification, "select-revision"), materializations),)
        return TaskContext("run.exposed-selection", node, node+".attempt-001",
            CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config.config_id),
            tuple(port.binding for port in ports), ports,
            (WorkerOutputPort(node+".product", declaration.outputs[0].payload_schema, declaration.outputs[0].profile, "application/json", node+".product"),),
            manifest.permissions, manifest.maximum_outcome_access, declaration.resources, WorkerIsolationProfile.TRUSTED_LOCAL, receipts)
    except BaseException:
        for port in ports:
            port.close()
        raise


def test_real_registered_freeze_worker_uses_independent_sealed_cursors_twice_and_exact_paired_model(exposed, nominated):
    declarations = method.operation_declarations()
    declaration = next(row for row in declarations if row.capability_key.endswith(".freeze-revision"))
    node = method.selection_node_id(exposed.specification, "freeze-revision")
    config = method.ScheduledRevisionOperationConfig("config."+node, "freeze-revision", exposed.programme,
        exposed.specification, ObjectIdentity.from_record(exposed.reduction.reduction_id, exposed.reduction), exposed.data.identity)
    from empirical_lawhood.runtime.execution import WorkerInputKind
    context = _sealed_context(config, declaration, (("operand.nomination", nominated, WorkerInputKind.DEPENDENCY),))
    try:
        runner = declaration.provider_factory().runner_factory()
        assert runner.preflight(context) is None and runner.preflight(context) is None
        assert all(port.bytes_read == 0 for port in context.input_ports)
        result = runner.execute(context)
        package = decode_canonical_bytes(result.outputs[0].payload, method.ScheduledRevisionFrozenPackage, maximum_bytes=None)
        assert package == method.freeze_programme_revision(exposed.programme, nominated,
            freeze_id="frozen."+exposed.specification.specification_id)
        assert package.revision.fitted_model == nominated.revision_model.identity
        assert package.baseline.fitted_model == nominated.baseline_model.identity
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        for port in context.input_ports:
            port.close()


def test_real_registered_select_worker_fits_both_budgets_and_preserves_exact_original_source_records(exposed, nominated):
    from empirical_lawhood.runtime.execution import WorkerInputKind
    declaration = next(row for row in method.operation_declarations() if row.capability_key.endswith(".select-revision"))
    node = method.selection_node_id(exposed.specification, "select-revision")
    config = method.ScheduledRevisionOperationConfig("config."+node, "select-revision", exposed.programme,
        exposed.specification, ObjectIdentity.from_record(exposed.reduction.reduction_id, exposed.reduction), exposed.data.identity)
    context = _sealed_context(config, declaration, (("operand.reduction", exposed.reduction, WorkerInputKind.EXTERNAL),
        ("operand.data", exposed.data, WorkerInputKind.EXTERNAL)))
    try:
        runner = declaration.provider_factory().runner_factory()
        assert runner.preflight(context) is None
        assert all(port.bytes_read == 0 for port in context.input_ports)
        result = runner.execute(context)
        actual = decode_canonical_bytes(result.outputs[0].payload, method.ScheduledRevisionNomination, maximum_bytes=None)
        assert actual == nominated
        assert actual.endpoint_fit_calls == 300
        assert all(port.bytes_read == 0 for port in context.input_ports)
    finally:
        for port in context.input_ports:
            port.close()



def test_complete_case_census_cannot_drop_a_coordinate_before_selection(exposed, monkeypatch):
    data = replace(exposed.data, cases=exposed.data.cases[:-1])
    monkeypatch.setattr(method, "fit_standardized_ridge", lambda *args, **kwargs: pytest.fail("thinned source bank entered fitting"))
    with pytest.raises(ValueError, match="full groups or source bank"):
        method.select_programme_revision(exposed.specification, exposed.programme, exposed.reduction, data, nomination_id="nomination.thinned")


def test_actual_numerical_violation_is_a_complete_unevaluable_group_without_fitting(exposed, monkeypatch):
    original = exposed.data.cases[0]
    score = replace(original.score, numerical_pass=False, disposition="NATIVE_CROSSCHECK_FAILED",
        controls=(replace(original.score.controls[0], error=Decimal(1), measured_errors=(Decimal(1),), failed_steps=(1,), disposition="VIOLATED"),),
        cumulative_log_errors=(None,)*15, reason_codes=("EXPOSED_NUMERICAL_VIOLATION",))
    row = replace(original, score=score)
    retained = replace(exposed.reduction.cases[0], numerical_disposition="VIOLATED", score_disposition="NATIVE_CROSSCHECK_FAILED",
        cumulative_log_errors=(None,)*15, score=identity(score), reason_codes=("EXPOSED_NUMERICAL_VIOLATION",))
    cases = (retained, *exposed.reduction.cases[1:])
    waves = tuple(rr.ScheduledProgrammeWaveResult(wave.wave_id+".adverse-result", exposed.programme.identity, wave.wave_id,
        wave.group_ids, wave.root_ids, tuple(case for case in cases if case.root_id in wave.root_ids)) for wave in exposed.programme.waves)
    reduction = rr.reduce_programme(exposed.programme, waves, reduction_id=exposed.reduction.reduction_id, authenticate_wave=lambda row: None)
    data = replace(exposed.data, reduction=ObjectIdentity.from_record(reduction.reduction_id, reduction), cases=(row, *exposed.data.cases[1:]))
    monkeypatch.setattr(method, "fit_standardized_ridge", lambda *args, **kwargs: pytest.fail("numerically violated group entered fitting"))
    result = method.select_programme_revision(exposed.specification, exposed.programme, reduction, data, nomination_id="nomination.numerical")
    assert result.trigger_disposition == "UNEVALUABLE" and result.endpoint_fit_calls == 0
    assert result.missing_groups == (original.causal_prefix.root.independent_group_id,)
    assert all(summary.assigned_units == 32 and summary.mean is None for summary in result.revision_selection.summaries)
    assert method._paired_targets(exposed.specification.target, score) == (None,)*30
