# SPDX-License-Identifier: MPL-2.0
# ruff: noqa: F811
"""Collector completion pins over disclosed typed metadata, without native work.

Literal completion publications are software premises, not acquired evidence,
scientific qualification or authority to enter an actual response workflow.
"""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import (
    METHODS,
    MatrixParameterHistoryControl,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as common
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as development
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_science as development_science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as protected
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_science as protected_science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as programme
from empirical_lawhood.adapters.methods.matrix_scheduled_history.continuation import ScheduledFullArrays
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import (
    ScheduledResponseScore,
    branch_census,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion
from tests.native_completion_fixtures import literal_completion, receipt_with_completion
from tests.test_matrix_e4_response_nonentry import no_native, response_case  # noqa: F401
from tests.test_matrix_selected_e4_fixtures import selected_bridge, selected_e4_populations, transfer  # noqa: F401
from tests.test_matrix_selected_e4_methods import selected_revision  # noqa: F401


def _literal_event(original, phase, access):
    """Distinct exact completion/receipt bodies, still unpublished metadata."""
    original_parent = original.definition.parent_contact
    parent_task = original_parent.task_id.rsplit(".", 1)[0] + "." + phase
    parent = replace(original_parent, task_id=parent_task,
        execution_task=replace(original_parent.execution_task, object_id=parent_task))
    definition = replace(original.definition, parent_contact=parent,
        subwork_id=phase + ".literal-collector", operation_id="literal.unpublished." + phase)
    task = "native-subwork." + sha256((parent.task_id + ":" + definition.subwork_id).encode()).hexdigest()
    completion = replace(original.completion, definition=definition.identity,
        contact=replace(original.completion.contact, object_id=task + ".contact"))
    publication = literal_completion(completion, task,
        visibility=original.receipt.output_logical_artifacts[0].visibility_ceiling,
        access=access)
    # A collector consumes these exact completion records; the focused control
    # deliberately does not simulate native array acquisition or publication.
    receipt = replace(original.receipt, task_id=task, receipt_id="receipt." + task,
        attempt_id=parent.run_id + "." + task + ".attempt-001",
        output_logical_artifacts=(), output_materializations=())
    receipt = receipt_with_completion(receipt, publication)
    return common.ScheduledNativeEvidence(definition, completion, receipt)


def collector_operands(fixture, population, response_used):
    available = "AVAILABLE" if response_used else "NO_ORIGIN"
    literal = response_case(fixture, population, available, available)
    try:
        records, config = literal.records, literal.config
        kinds = development if population == "development" else protected
        history, account, causal = records["prefix"], records["account"], records["causal"]
        source = config.source.descriptor.identity
        case = SimpleNamespace(root_id=config.source.root_id, source=source,
            independent_group_id=config.source.public.root.independent_group_id,
            coordinate=config.source.coordinate)
        outcome_access = (OutcomeAccess.DEVELOPMENT_VISIBLE if population == "development"
            else OutcomeAccess.EVALUATION_SEALED)
        event = _literal_event(history.native, "continue", outcome_access)
        arrays = ScheduledFullArrays("arrays.literal-collector-full", source, history.arrays.array_artifact,
            history.arrays.members, history.arrays.producers,
            outcome_access, history.arrays.visibility_ceiling)
        full_kind = (kinds.SelectedE3E4FullHistory if population == "development"
            else kinds.SelectedE4ProtectedFullHistory)
        full = full_kind("history.literal-collector-full", source, common.identity(history),
            common.identity(history.checkpoint), account.identity, arrays, event, 1, 2)
        response_kind = (kinds.SelectedE3E4Responses if population == "development"
            else kinds.SelectedE4ProtectedResponses)
        response = response_kind("responses.literal-collector", source, common.identity(causal),
            common.identity(records["mechanical"]), account.identity,
            ObjectIdentity.from_record(config.protocol.protocol_id, config.protocol),
            replace(records["mechanical"].arrays, role="RESPONSES", outcome_access=outcome_access),
            tuple(row[0] for row in branch_census(config.protocol, config.panels)),
            (_literal_event(history.native, "responses", outcome_access),) if response_used else (),
            "COMPLETED" if response_used else "NO_ORIGIN", ())
        methods = ("PRIMARY_FULL192_TRACE_POLYNOMIAL_BAOAB_ALL_STEPS",
            "FINE_FULL192_TRACE_POLYNOMIAL_BAOAB_ALL_STEPS",
            "WEIGHTED_OU_FULL192_ORIGINAL_COARSE_AND_BRIDGE_ALL_STEPS",
            "WEIGHTED_OU_FULL96_BATH_SCALED_COMPOSED_IMPULSE_ALL_STEPS")
        controls = tuple(MatrixParameterHistoryControl(name, method, Decimal(0), Decimal(1), "SATISFIED",
            steps, coordinates, (Decimal(0),) * steps, ())
            for name, method, steps, coordinates in zip(METHODS, methods, (1, 2, 1, 1), (192, 192, 192, 96), strict=True))
        numerical_kind = (kinds.SelectedE3E4NumericalAssessment if population == "development"
            else kinds.SelectedE4ProtectedNumericalAssessment)
        numerical = numerical_kind("numerical.literal-collector-full", "full", source,
            common.identity(full), common.identity(config.source.numerical_design), controls, True)
        # Adverse/null scientific outcomes remain adverse even when native
        # operational completion is supplied as a literal typed premise.
        score = ScheduledResponseScore("score.literal-collector", source, common.identity(causal), account.identity,
            common.identity(records["mechanical"]), common.identity(response), case.root_id, case.independent_group_id,
            config.source.public.root.role.value, config.protocol.criterion, (), False,
            "UNEVALUABLE" if response_used else "NO_ORIGIN", (), (None,) * 15, ("literal-software-premise",))
        return SimpleNamespace(case=case, protocol=config.protocol, panels=config.panels, account=account,
            prefix=history, full=full, responses=response, numerical=numerical, score=score, causal=causal)
    finally:
        for port in literal.context.input_ports:
            port.close()


@pytest.mark.parametrize("population", ("development", "protected"))
@pytest.mark.parametrize("response_used", (False, True))
def test_actual_collectors_pin_exact_native_completion_publications(
        selected_bridge, selected_revision, population, response_used):
    operands = collector_operands(selected_bridge if population == "development" else selected_revision,
        population, response_used)
    kwargs = dict(account_seal=operands.account, score=operands.score, full_numerical=operands.numerical,
        prefix=operands.prefix, full=operands.full, responses=operands.responses, receipts=())
    if population == "development":
        result = development_science.completed_case(operands.case, operands.protocol, operands.panels, **kwargs)
    else:
        projection = programme.SelectedE4ScoreProjection.from_record(operands.score, operands.protocol,
            operands.panels, record_id="score-projection." + operands.case.root_id)
        result = protected_science.completed_case(operands.case, operands.protocol, operands.panels,
            score_projection=projection, causal=operands.causal, **kwargs)
    assert result.disposition == "COMPLETED"
    assert result.score_disposition == operands.score.disposition
    assert result.paired_log_targets == (None,) * 30
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    events = {"prefix": operands.prefix.native, "continue": operands.full.native,
        "responses": operands.responses.native[0] if response_used else None}
    for summary in result.native:
        event = events[summary.phase]
        if event is None:
            assert summary.disposition == "NOT_USED"
            assert summary.definition is summary.completion is summary.receipt is None
            assert summary.reason_codes == ("actual-no-causal-origin-or-instrument-nonuse",)
            continue
        assert type(event.completion) is NativeSubworkCompletion
        logical, = (value for value in event.receipt.output_logical_artifacts
            if value.payload_schema == NativeSubworkCompletion.SCHEMA)
        assert summary.disposition == "COMPLETED"
        assert summary.definition == event.definition.identity
        assert summary.completion.object_id == logical.logical_artifact_id == event.receipt.task_id + ".completion"
        assert summary.completion.object_schema == NativeSubworkCompletion.SCHEMA
        assert summary.completion.object_fingerprint == logical.content_sha256 == sha256(event.completion.canonical_bytes()).hexdigest()
        assert summary.receipt == ObjectIdentity.from_record(event.receipt.receipt_id, event.receipt)
