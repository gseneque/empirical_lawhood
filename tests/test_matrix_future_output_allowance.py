# SPDX-License-Identifier: MPL-2.0
"""Exposed operational controls; no scientific outcomes or acquisition."""
from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme import source_continuation as domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixResearchProgrammeSpecification
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_matrix_programme_source_continuation import _plans, metadata_case  # noqa: F401
from tests.test_matrix_completed_e4_continuation import _pin

ROOT = Path(__file__).parents[1]


@pytest.fixture
def selections():
    programme = decode_canonical_bytes((ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-programme/specification.example.json').read_bytes(),
        MatrixResearchProgrammeSpecification, maximum_bytes=None)
    request = decode_canonical_bytes((ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-programme/source-continuation.example.json').read_bytes(),
        domain.MatrixProgrammeSourceContinuationSpecification, maximum_bytes=None)
    selected = domain.MatrixProgrammeOutputContinuationSpecification(request.specification_id,
        request.predecessor, request.directory, 256 * 1024**2)
    return programme.operations, request, selected


def test_future_allowance_changes_only_three_unentered_pure_output_fields(selections):
    original, _, request = selections
    before = original.canonical_bytes()
    selected = domain.continued_operations(original, request, completed_phases=domain.COMPLETED_E4_PHASES)
    assert replace(selected, e4=original.e4, prepared=original.prepared) == original
    assert replace(selected.e4, native_budgets=original.e4.native_budgets) == original.e4
    assert replace(selected.prepared, opportunity_resources=original.prepared.opportunity_resources,
        protected_resources=original.prepared.protected_resources) == original.prepared
    for prior, current in ((original.e4.native_budgets, selected.e4.native_budgets),
            (original.prepared.opportunity_resources, selected.prepared.opportunity_resources),
            (original.prepared.protected_resources, selected.prepared.protected_resources)):
        assert replace(current, phase_budgets=prior.phase_budgets) == prior
        old, new = dict(prior.phase_budgets), dict(current.phase_budgets)
        assert old.keys() == new.keys()
        assert new['response-score'].output_bytes == request.output_bytes
        assert replace(new['response-score'], output_bytes=old['response-score'].output_bytes) == old['response-score']
        assert all(new[phase] == budget for phase, budget in old.items() if phase != 'response-score')
    assert original.canonical_bytes() == before
    assert decode_canonical_bytes(selected.canonical_bytes(), type(selected), maximum_bytes=None) == selected


@pytest.mark.parametrize('phases', (domain.RETAINED_PHASES, domain.COMPLETED_PHASES, (),
    (*domain.COMPLETED_E4_PHASES, 'e4.revision')))
def test_future_allowance_requires_exact_completed_e4_frontier(selections, phases):
    original, _, request = selections
    with pytest.raises(PermissionError, match='complete original E4'):
        domain.continued_operations(original, request, completed_phases=phases)


@pytest.mark.parametrize('value', (True, 0, -1, 1.5, 256 * 1024**2 + 1))
def test_future_allowance_has_an_explicit_finite_cap(selections, value):
    with pytest.raises(ValueError, match='within 256 MiB'):
        replace(selections[2], output_bytes=value)


@pytest.mark.parametrize('value', (32 * 1024**2, 64 * 1024**2))
def test_future_allowance_cannot_lower_or_reselect_unchanged_budgets(selections, value):
    original, _, request = selections
    with pytest.raises(ValueError, match='lower|must increase'):
        domain.continued_operations(original, replace(request, output_bytes=value), completed_phases=domain.COMPLETED_E4_PHASES)


def test_future_allowance_keeps_the_original_memory_ceiling(selections):
    original, _, request = selections
    resources = original.e4.native_budgets
    budgets = tuple((phase, replace(budget, memory_bytes=128 * 1024**2) if phase == 'response-score' else budget)
        for phase, budget in resources.phase_budgets)
    original = replace(original, e4=replace(original.e4, native_budgets=replace(resources, phase_budgets=budgets)))
    with pytest.raises(ValueError, match='original memory'):
        domain.continued_operations(original, request, completed_phases=domain.COMPLETED_E4_PHASES)


def test_ordinary_continuation_retains_exact_original_operations(selections):
    original, request, _ = selections
    before = request.canonical_bytes()
    for phases in (domain.RETAINED_PHASES, domain.COMPLETED_PHASES, domain.COMPLETED_E4_PHASES):
        assert domain.continued_operations(original, request, completed_phases=phases) is original
    assert request.canonical_bytes() == before


@pytest.mark.parametrize('native_continuation', (False, True))
def test_completed_output_record_reopens_both_original_terminal_contracts(metadata_case, native_continuation):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixProgrammePhaseBinding
    from empirical_lawhood.api.matrix_programme_completed_continuation import read_source_continuation
    from empirical_lawhood.api.matrix_researcher_programme import _publish
    from empirical_lawhood.runtime.development_controller_repair import DevelopmentControllerRepairTerminalEvent
    from empirical_lawhood.runtime.native_continuation_execution import DevelopmentNativeContinuationTerminalEvent
    from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent
    original, request, target = _plans(metadata_case)
    selected = domain.MatrixProgrammeOutputContinuationSpecification(request.specification_id,
        request.predecessor, request.directory, 256 * 1024**2)
    operations = domain.continued_operations(original.specification.operations, selected,
        completed_phases=domain.COMPLETED_E4_PHASES)
    target = replace(target, specification=replace(target.specification,
        continuation_request=selected.identity, operations=operations))
    bindings = tuple((phase, _pin('binding.' + phase, MatrixProgrammePhaseBinding)) for phase in domain.COMPLETED_E4_PHASES)
    kinds = (RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent,
        RunRecoveryTerminalEvent, DevelopmentNativeContinuationTerminalEvent if native_continuation else DevelopmentControllerRepairTerminalEvent)
    terminals = tuple((phase, _pin('terminal.' + phase, kind))
        for phase, kind in zip(domain.COMPLETED_E4_PHASES, kinds, strict=True))
    record = domain.MatrixProgrammeCompletedE4OutputContinuation('continuation.exposed-output', selected,
        target, bindings, terminals, _pin('terminal.structure', DevelopmentRunRecoveryTerminalEvent))
    assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    writer = metadata_case.case.writer
    relative = 'disclosed-future-output/' + str(native_continuation) + '/source-continuation.json'
    _publish(writer, Path(writer.root.contract.canonical_path) / relative, record)
    assert read_source_continuation(writer, relative, 64 * 1024**2) == record
    with pytest.raises(TypeError, match='exact selection'):
        replace(record, specification=request)
    with pytest.raises(TypeError, match='structural development terminal'):
        replace(record, completed_e4_structure_terminal=terminals[0][1])
