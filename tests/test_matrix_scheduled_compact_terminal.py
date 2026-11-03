# SPDX-License-Identifier: MPL-2.0
"""Exposed terminal numerical census controls; no issue or qualification."""

from dataclasses import replace
from decimal import Decimal

import pytest

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import METHODS, MatrixParameterHistoryControl
from empirical_lawhood.adapters.methods.matrix_scheduled_history import calibration_bindings as calibration, compact_bindings as b, compact_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history.continuation import ScheduledFullAssessment, ScheduledFullHistory
from empirical_lawhood.adapters.methods.matrix_scheduled_history.qualification import cutoffs
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationContext
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from tests.test_matrix_scheduled_calibration import calibration_fixture
from tests.test_matrix_scheduled_compact_workers import compact_context, run_compact_commit
from tests.test_matrix_scheduled_history_bindings import (
    bank as bank, provenance as provenance, scheduled as scheduled, stock as stock, write,
)
from tests.test_matrix_scheduled_response_bindings import response_bank as response_bank


def full_assessment(source, *, violated=False):
    methods = ('PRIMARY_FULL192_TRACE_POLYNOMIAL_BAOAB_ALL_STEPS', 'FINE_FULL192_TRACE_POLYNOMIAL_BAOAB_ALL_STEPS',
        'WEIGHTED_OU_FULL192_ORIGINAL_COARSE_AND_BRIDGE_ALL_STEPS', 'WEIGHTED_OU_FULL96_BATH_SCALED_COMPOSED_IMPULSE_ALL_STEPS')
    controls = tuple(MatrixParameterHistoryControl(control, method, Decimal(int(violated and index == 0)), Decimal(0),
        'VIOLATED' if violated and index == 0 else 'SATISFIED', 1, 192, (Decimal(int(violated and index == 0)),),
        (1,) if violated and index == 0 else ()) for index, (control, method) in enumerate(zip(METHODS, methods, strict=True)))
    return ScheduledFullAssessment('full-assessment.'+source.root_id, identity(source),
        ObjectIdentity('full-history.'+source.root_id, ScheduledFullHistory.SCHEMA, '1.0.0', 'a'*64),
        identity(source.numerical_design), controls, not violated)


def terminal_context(response_bank, *, violated=False, missing=False):
    plane, sources, original = response_bank[:3]
    shared, receipt, commit_outputs = run_compact_commit(response_bank)
    value = calibration_fixture(response_bank)
    inputs = [*commit_outputs, write(plane, shared.bank_id, shared.canonical_bytes(), shared.SCHEMA)]
    dependencies = [receipt]
    for index, source in enumerate(s for s in sources if s.root_id in original.selected_root_ids):
        if missing and index == 0:
            continue
        assessment = full_assessment(source, violated=violated and index == 0)
        task = r.NAMESPACE+'.'+source.root_id+'.full-numerical'
        manifest = write(plane, 'ordinary.'+task+'.product', assessment.canonical_bytes(), assessment.SCHEMA,
            access=OutcomeAccess.EVALUATION_SEALED, phase='terminal-assessments')
        attempt = 'run.software.compact.'+task+'.attempt-001'
        dependencies.append(CanonicalTaskReceipt('receipt.'+attempt, 'run.software.compact', task, attempt,
            source.provenance.observed_git_head, (), (manifest.materialization,), (manifest.logical,), (), OperationalStatus.SUCCEEDED, ()))
        inputs.append(manifest)
    calibration_task = r.NAMESPACE+'.calibrate'
    manifest = write(plane, 'ordinary.'+calibration_task+'.product', value.canonical_bytes(), value.SCHEMA,
        access=OutcomeAccess.EVALUATION_SEALED, phase='terminal-calibration')
    attempt = 'run.software.compact.'+calibration_task+'.attempt-001'
    dependencies.append(CanonicalTaskReceipt('receipt.'+attempt, 'run.software.compact', calibration_task, attempt,
        sources[0].provenance.observed_git_head, (), (manifest.materialization,), (manifest.logical,), (), OperationalStatus.SUCCEEDED, ()))
    inputs.append(manifest)
    groups = tuple(sorted({source.root.root.independent_group_id for source in sources if source.root_id in original.selected_root_ids}))
    config = r.ScheduledCompactCalibrationConfig('config.'+r.NAMESPACE+'.calibration-qualify', r.compact_identity(shared), value.calibration_id, True, groups)
    context, _ = compact_context(plane, config, 'calibration-qualify', tuple(inputs), tuple(dependencies))
    authority = ScientificAdjudicationContext(ObjectIdentity('plan.software.compact.terminal', 'empirical-lawhood/runtime/candidate-execution-plan',
        '1.0.0', 'b'*64), 'world.software.compact', WorldKind.NUMERICAL_SIMULATOR,
        ObjectIdentity('relation.software.compact', 'empirical-lawhood/tests/relation', '1.0.0', 'c'*64),
        value.independent_unit_id, tuple(ObjectIdentity.from_record(cutoff.cutoff_id, cutoff) for cutoff in cutoffs(original)),
        VisibilityCeiling.OUTCOME_VISIBLE, OutcomeAccess.EVALUATION_REVEALED)
    return replace(context, scientific_adjudication_context=authority), value


def test_compact_terminal_refuses_missing_full_history_numerical_case(response_bank):
    context, _ = terminal_context(response_bank, missing=True)
    with pytest.raises(ValueError, match='complete full-history numerical census'):
        b.decode_calibration(context, 'calibration-qualify')


@pytest.mark.parametrize('violated,status', ((False, ScientificStatus.SUPPORTED), (True, ScientificStatus.NOT_SUPPORTED)))
def test_compact_terminal_retains_negative_independent_full_history_assessment(response_bank, violated, status):
    context, value = terminal_context(response_bank, violated=violated)
    config, _, _ = b.decode_calibration(context, 'calibration-qualify')
    assert len(config.full_assessments) == len(config.commitment.selected_root_ids)
    assert any(not assessment.numerical_pass for assessment in config.full_assessments) is violated
    product = calibration.make_adjudication(context, config, value)
    assert product.scientific_status is status
