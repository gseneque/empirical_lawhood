# SPDX-License-Identifier: MPL-2.0
"""Synthetic cold reduction controls; no scientific qualification evidence."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from itertools import product
import json
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_records as records
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_reduction as reduction
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import MatrixResponseFrontierProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore
from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import ScheduledCompactBank
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.runtime.execution import DependencyReceiptBinding


def _synthetic(key, schema, version='1.0.0'):
    return ObjectIdentity(key, schema, version, sha256(key.encode()).hexdigest())


@pytest.fixture(scope='module')
def declared():
    # Every pin is a declared synthetic fixture, never an authenticated run.
    mode = 'E4_REVISION_CALIBRATION'
    factors = tuple(records.ScheduledProgrammeFactor(name, 'LINEAR', Decimal(1), Decimal(2), Decimal(3))
        for name in ('temperature', 'friction', 'coupling'))
    grid = (*product((Decimal(1), Decimal(3)), repeat=3), (Decimal(2),)*3)
    families = tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
    cases = []
    for group in range(64):
        for index, values in enumerate(grid):
            root = f'synthetic.root.{group:03}.{index}'
            source = _synthetic('synthetic.source.'+root, ScheduledSource.SCHEMA, ScheduledSource.VERSION)
            cases.append(records.ScheduledProgrammeCase(root, f'synthetic.group.{group:03}', families[group//16],
                records.MODES[mode][0], source,
                _synthetic('synthetic.coordinate.'+root, MatrixParameterCoordinate.SCHEMA),
                values, sha256(f'synthetic.streams.{group}'.encode()).hexdigest(),
                InformationCutoff('cutoff.'+root, 'synthetic.clock', CausalPhase.PRE_ACTION, Decimal(1))))
    groups = tuple(sorted({case.independent_group_id for case in cases}))
    waves = tuple(records.ScheduledProgrammeWave(f'synthetic.wave.{i//4:02}', groups[i:i+4],
        tuple(c.root_id for c in cases if c.independent_group_id in groups[i:i+4])) for i in range(0, 64, 4))
    programme = records.ScheduledProgramme('synthetic.programme', mode,
        _synthetic('synthetic.bank', ScheduledCompactBank.SCHEMA, ScheduledCompactBank.VERSION),
        _synthetic('synthetic.reservation', 'empirical-lawhood/matrix-scheduled-history/reservation'),
        _synthetic('synthetic.allocation', 'empirical-lawhood/matrix-scheduled-history/allocation'),
        _synthetic('synthetic.specification', 'empirical-lawhood/matrix-scheduled-history/specification'),
        _synthetic('synthetic.forecast-design', 'empirical-lawhood/matrix-scheduled-history/forecast-design'),
        _synthetic('synthetic.response-selection', 'empirical-lawhood/matrix-scheduled-history/response-selection'),
        _synthetic('synthetic.criterion', MatrixResponseFrontierProtocol.SCHEMA),
        _synthetic('synthetic.calibration-criterion', 'empirical-lawhood/matrix-scheduled-history/calibration-criterion'),
        factors, tuple(cases), tuple(sorted((c.source for c in cases), key=lambda c: c.object_id)), waves, Decimal('.95'), 64)
    completed = []
    for index, case in enumerate(cases):
        value = Decimal(index//9+1) + Decimal(index % 9)/100
        native = tuple(reduction.ScheduledProgrammeNativeDisposition(phase, 'COMPLETED',
            _synthetic(case.root_id+'.'+phase+'.definition', 'empirical-lawhood/runtime/native-subwork-definition'),
            _synthetic(case.root_id+'.'+phase+'.completion', 'empirical-lawhood/runtime/native-subwork-completion'),
            _synthetic('receipt.'+case.root_id+'.'+phase, 'empirical-lawhood/runtime/canonical-task-receipt'), ())
            for phase in reduction.NATIVE_PHASES)
        completed.append(reduction.ScheduledProgrammeCaseResult(case.root_id, case.source, case.independent_group_id,
            'COMPLETED', 'SATISFIED', 'FINITE', (value,)*15, (Decimal(0),)*15, (None,)*15,
            _synthetic(case.root_id+'.forecast', 'empirical-lawhood/matrix-scheduled-history/forecast-seal'),
            _synthetic(case.root_id+'.score', ScheduledResponseScore.SCHEMA, ScheduledResponseScore.VERSION),
            _synthetic(case.root_id+'.full', 'empirical-lawhood/matrix-scheduled-history/full-assessment'),
            tuple(_synthetic(f'receipt.{case.root_id}.stage.{i:02}', 'empirical-lawhood/runtime/canonical-task-receipt')
                for i in range(11)), native, ()))
    return programme, tuple(completed)


def _waves(programme, cases):
    by_root = {case.root_id: case for case in cases}
    return tuple(reduction.ScheduledProgrammeWaveResult(wave.wave_id+'.result', programme.identity, wave.wave_id,
        wave.group_ids, wave.root_ids, tuple(by_root[root] for root in wave.root_ids)) for wave in programme.waves)


def _reduce(programme, cases):
    return reduction.reduce_programme(programme, _waves(programme, cases), reduction_id='synthetic.reduction',
        authenticate_wave=lambda wave: None)


def test_cold_reduction_recomputes_global_rank62_max135_and_counts(declared):
    programme, cases = declared
    result = _reduce(programme, cases)
    assert result.group_scores[0] == ('synthetic.group.000', Decimal('1.08'))
    assert result.order_statistic_rank == 62 and result.radius == Decimal('62.08')
    assert dict(result.disposition_counts)['COMPLETED'] == 576
    assert dict(result.native_disposition_counts)['COMPLETED'] == 1728
    assert result.numerical_disposition == 'SATISFIED' and result.qualification_disposition == 'UNENTERED'
    assert decode_canonical_bytes(result.canonical_bytes(), reduction.ScheduledProgrammeReduction, maximum_bytes=8*1024**2) == result
    for key, bad in (('order_statistic_rank', 61), ('radius', '999'), ('numerical_disposition', 'VIOLATED'),
            ('disposition_counts', [['COMPLETED', 999]]), ('group_scores', [['synthetic.group.000', '123']])):
        document = json.loads(result.canonical_bytes())
        document['value'][key] = bad
        with pytest.raises(ValueError):
            decode_canonical_bytes(json.dumps(document, sort_keys=True, separators=(',', ':')).encode(), reduction.ScheduledProgrammeReduction, maximum_bytes=8*1024**2)
    with pytest.raises(ValueError, match='scores, counts'):
        replace(result, group_scores=(('synthetic.group.000', Decimal(999)), *result.group_scores[1:]))
    with pytest.raises(ValueError, match='scores, counts'):
        replace(result, mode='E4_CONFIRMATION')
    confirmation = replace(result, mode='E4_CONFIRMATION', radius=None)
    assert confirmation.radius is None


def test_any_violation_unknown_or_unentered_is_preserved(declared):
    programme, cases = declared
    violated = replace(cases[0], numerical_disposition='VIOLATED', reason_codes=('synthetic-prefix-control-violated',))
    result = _reduce(programme, (violated, *cases[1:]))
    assert result.numerical_disposition == 'VIOLATED' and result.group_scores[0][1] is None
    with pytest.raises(ValueError, match='scores, counts'):
        replace(result, numerical_disposition='SATISFIED')
    unentered = reduction.ScheduledProgrammeCaseResult.unentered(programme.cases[0])
    unknown = replace(unentered, disposition='UNKNOWN', numerical_disposition='UNKNOWN', score_disposition='UNKNOWN',
        native=tuple(replace(n, disposition='UNKNOWN', reason_codes=('synthetic-contact-unknown',)) for n in unentered.native),
        reason_codes=('synthetic-contact-unknown',))
    result = _reduce(programme, (unknown, *cases[1:]))
    assert result.numerical_disposition == 'UNKNOWN' and result.group_scores[0][1] is None
    assert dict(result.disposition_counts)['UNKNOWN'] == 1 and dict(result.native_disposition_counts)['UNKNOWN'] == 3
    assert _reduce(programme, (unentered, *cases[1:])).numerical_disposition == 'UNENTERED'


@pytest.mark.parametrize('disposition', ('NO_ORIGIN', 'UNEVALUABLE', 'INSTRUMENT_UNRESOLVED', 'UNKNOWN', 'UNENTERED', 'FAILED', 'PARTIAL'))
def test_cold_score_disposition_cannot_relabel_finite_endpoints(declared, disposition):
    _, cases = declared
    document = json.loads(cases[0].canonical_bytes())
    document['value']['score_disposition'] = disposition
    with pytest.raises(ValueError, match='nonuse|partial'):
        decode_canonical_bytes(json.dumps(document, sort_keys=True, separators=(',', ':')).encode(), reduction.ScheduledProgrammeCaseResult, maximum_bytes=1024**2)


def test_completed_cannot_hide_unknown_native_or_nonuse_as_pass(declared):
    programme, cases = declared
    case = cases[0]
    unknown = replace(case.native[0], disposition='UNKNOWN', reason_codes=('synthetic-contact-unknown',))
    with pytest.raises(ValueError, match='eleven-stage custody'):
        replace(case, native=(unknown, *case.native[1:]))
    with pytest.raises(ValueError, match='closed scientific'):
        replace(case.native[0], definition=_synthetic('synthetic.foreign', 'empirical-lawhood/foreign'))
    nonuse = reduction.ScheduledProgrammeNativeDisposition('responses', 'NOT_USED', None, None, None, ('NO_ORIGIN',))
    with pytest.raises(ValueError, match='nonuse'):
        replace(case, native=(*case.native[:2], nonuse), score_disposition='NO_ORIGIN', cumulative_log_errors=(None,)*15)
    retained = replace(case, native=(*case.native[:2], nonuse), score_disposition='NO_ORIGIN',
        cumulative_log_errors=(None,)*15, numerical_disposition='UNKNOWN', reason_codes=('NO_ORIGIN',))
    result = _reduce(programme, (retained, *cases[1:]))
    assert result.numerical_disposition == 'UNKNOWN' and dict(result.native_disposition_counts)['NOT_USED'] == 1


def test_dependency_header_reference_keeps_opaque_custody_without_fake_hash(declared):
    _, cases = declared
    case = cases[0]
    headers = tuple(DependencyReceiptBinding(r.object_id, f'synthetic.task.{i:02}', (f'synthetic.output.{i:02}',))
        for i, r in enumerate(case.ordinary_receipts))
    references = tuple(reduction.ScheduledProgrammeReceiptReference.from_binding(header) for header in headers)
    assert [(r.receipt_id, r.task_id, r.output_materialization_ids) for r in references] == [
        (h.receipt_id, h.task_id, h.output_materialization_ids) for h in headers]
    retained = replace(case, ordinary_receipts=references)
    assert decode_canonical_bytes(retained.canonical_bytes(), reduction.ScheduledProgrammeCaseResult, maximum_bytes=1024**2) == retained
    assert ObjectIdentity.from_record(references[0].receipt_id, references[0]).object_schema == reduction.ScheduledProgrammeReceiptReference.SCHEMA
    with pytest.raises(ValueError, match='actual dependency header'):
        reduction.ScheduledProgrammeReceiptReference.from_binding(SimpleNamespace(receipt_id=headers[0].receipt_id,
            task_id=headers[0].task_id, output_materialization_ids=headers[0].output_materialization_ids))


def test_programme_aware_cold_validator_checks_sources_groups_and_waves(declared):
    programme, cases = declared
    result = _reduce(programme, cases)
    waves = _waves(programme, cases)
    assert reduction.validate_programme_reduction(programme, result, wave_results=waves) == result
    foreign = replace(cases[0], source=_synthetic('synthetic.foreign-source', cases[0].source.object_schema,
        cases[0].source.object_version))
    changed = replace(result, cases=(foreign, *cases[1:]))
    with pytest.raises(ValueError, match='source/group census'):
        reduction.validate_programme_reduction(programme, changed, wave_results=waves)
    with pytest.raises(ValueError, match='wave identities'):
        reduction.validate_programme_reduction(programme, result, wave_results=waves[::-1])
    with pytest.raises(ValueError, match='global scope'):
        reduction.validate_programme_reduction(programme, replace(result, mode='E4_CONFIRMATION', radius=None), wave_results=waves)


def test_collector_numerical_status_preserves_prefix_full_frame_pulse_and_nonuse():
    passed = SimpleNamespace(numerical_pass=True)
    failed = SimpleNamespace(numerical_pass=False)
    pulse = SimpleNamespace(numerical_pass=True, disposition='FINITE', controls=())
    assert reduction.programme_numerical_disposition(passed, passed, pulse) == 'SATISFIED'
    assert reduction.programme_numerical_disposition(failed, passed, pulse) == 'VIOLATED'
    assert reduction.programme_numerical_disposition(passed, failed, pulse) == 'VIOLATED'
    assert reduction.programme_numerical_disposition(passed, passed, pulse, frame_numerical=failed) == 'VIOLATED'
    pulse = SimpleNamespace(numerical_pass=False, disposition='NATIVE_CROSSCHECK_FAILED', controls=())
    assert reduction.programme_numerical_disposition(passed, passed, pulse) == 'VIOLATED'
    nonuse = SimpleNamespace(numerical_pass=False, disposition='NO_ORIGIN', controls=())
    assert reduction.programme_numerical_disposition(passed, passed, nonuse) == 'UNKNOWN'
