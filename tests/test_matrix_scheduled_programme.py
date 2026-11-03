# SPDX-License-Identifier: MPL-2.0
"""Public bounded E4 preflight and complete reduction software controls.

The full576 population is an exposed hypothetical fixture. Test receipt pins
below are synthetic declarations, never qualification or scientific evidence.
"""

from dataclasses import replace
from decimal import Decimal, localcontext
from hashlib import sha256

import pytest

from empirical_lawhood.api import matrix_scheduled_programme as api
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_records as records, programme_reduction as reduction
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.infrastructure.artifacts import ArtifactPlaneError
from tests.test_matrix_scheduled_programme_graph import (
    bank as bank, compile_wave, programme576_bank, provenance as provenance,
    response_bank as response_bank, scheduled as scheduled, stock as stock,
)


def test_programme_exact_factor_arithmetic_and_cold_constructor_bounds():
    with pytest.raises(ValueError, match='distinct positive'):
        records.ScheduledProgrammeFactor('temperature', 'LINEAR', Decimal(0), Decimal(1), Decimal(2))
    with localcontext() as context:
        context.prec = 2
        # This exact symmetric grid remains valid under an adverse context.
        factor = records.ScheduledProgrammeFactor('temperature', 'LINEAR', Decimal('1.00001'), Decimal('2.00001'), Decimal('3.00001'))
        assert decode_canonical_bytes(factor.canonical_bytes(), records.ScheduledProgrammeFactor, maximum_bytes=16*1024**2) == factor
        with pytest.raises(ValueError, match='not symmetric'):
            records.ScheduledProgrammeFactor('coupling', 'LOG', Decimal('1.00001'), Decimal(2), Decimal('4.00001'))
    groups = tuple(f'group.{i:02}' for i in range(9))
    roots = tuple(f'root.{i:03}' for i in range(81))
    with pytest.raises(ValueError, match='nine cases'):
        records.ScheduledProgrammeWave('wave.oversized', groups, roots)


def _synthetic_identity(key, schema, version='1.0.0'):
    return ObjectIdentity(key, schema, version, sha256(key.encode()).hexdigest())


def _synthetic_cases(programme):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore
    groups = {group: index+1 for index, group in enumerate(programme.group_ids)}
    seen = {}
    result = []
    for case in programme.cases:
        index = seen.get(case.independent_group_id, 0)
        seen[case.independent_group_id] = index+1
        value = Decimal(groups[case.independent_group_id])+Decimal(index)/100
        native = tuple(reduction.ScheduledProgrammeNativeDisposition(phase, 'COMPLETED',
            _synthetic_identity(f'synthetic.{case.root_id}.{phase}.definition', 'empirical-lawhood/runtime/native-subwork-definition'),
            _synthetic_identity(f'synthetic.{case.root_id}.{phase}.completion', 'empirical-lawhood/runtime/native-subwork-completion'),
            _synthetic_identity(f'receipt.synthetic.{case.root_id}.{phase}', 'empirical-lawhood/runtime/canonical-task-receipt'), ())
            for phase in reduction.NATIVE_PHASES)
        result.append(reduction.ScheduledProgrammeCaseResult(case.root_id, case.source, case.independent_group_id, 'COMPLETED', 'SATISFIED', 'FINITE',
            (value,)*15, (Decimal(0),)*15, (None,)*15,
            _synthetic_identity(f'forecast.synthetic.{case.root_id}', 'empirical-lawhood/matrix-scheduled-history/forecast-seal'),
            _synthetic_identity(f'score.synthetic.{case.root_id}', ScheduledResponseScore.SCHEMA, ScheduledResponseScore.VERSION),
            _synthetic_identity(f'full.synthetic.{case.root_id}', 'empirical-lawhood/matrix-scheduled-history/full-assessment'),
            tuple(_synthetic_identity(f'receipt.synthetic.{case.root_id}.stage.{i:02}', 'empirical-lawhood/runtime/canonical-task-receipt') for i in range(11)),
            native, ()))
    return tuple(result)


def _waves(programme, cases):
    by_root = {case.root_id: case for case in cases}
    return tuple(reduction.ScheduledProgrammeWaveResult(wave.wave_id+'.synthetic-result', programme.identity,
        wave.wave_id, wave.group_ids, wave.root_ids, tuple(by_root[root] for root in wave.root_ids)) for wave in programme.waves)


def test_public_full576_preflight_and_complete_crosswave_negative_census(response_bank, tmp_path, monkeypatch):
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments
    from empirical_lawhood.adapters.methods.matrix_factor_response import response_error_prediction

    def blocked(*args, **kwargs):
        pytest.fail('bounded programme preflight or reduction entered numerical science')

    monkeypatch.setattr(parameter_history_segments, 'acquire_parameter_segment', blocked)
    monkeypatch.setattr(response_error_prediction, 'fit_error_model', blocked)
    monkeypatch.setattr(response_error_prediction, 'fit_scheduled_error_model', blocked)
    programme, bank, templates = programme576_bank(response_bank)
    plane = response_bank[0]
    plans = tuple(compile_wave(programme, bank, templates, wave)[0] for wave in programme.waves)
    total_wave_bytes = sum(len(plan.canonical_bytes()) for plan in plans)
    assert all(len(plan.canonical_bytes()) < 16*1024**2 for plan in plans)
    assert total_wave_bytes < 256*1024**2
    package = api.author_scheduled_programme_preflight(programme=programme, bank=bank, wave_plans=plans,
        template_bytes=templates, artifact_plane=plane, output_directory=tmp_path/'preflight')
    assert package.manifest.aggregate_bytes < 512*1024**2
    assert len(package.proof.logical_task_ids) == 6339
    assert len(package.proof.native_task_ids) == 1728
    assert package.proof.effects_blocked
    assert package.proof.qualification_disposition == package.proof.issued_execution_disposition == 'UNENTERED'
    loaded = api.load_scheduled_programme_preflight(directory=package.directory, artifact_plane=plane)
    assert (loaded.manifest, loaded.programme, loaded.bank, loaded.proof) == (package.manifest, programme, bank, package.proof)
    assert loaded.proof.source_census == programme.source_census

    # A missing/foreign local carrier refuses before any apparent programme
    # success; restoring bytes lets us exercise actual original publications.
    wave_path = package.directory/'wave.000.json'
    original_wave = wave_path.read_bytes()
    wave_path.write_bytes(original_wave[:-1]+b' ')
    with pytest.raises(ValueError, match='actual bytes'):
        api.load_scheduled_programme_preflight(directory=package.directory, artifact_plane=plane)
    wave_path.write_bytes(original_wave)
    original_allocation = plane.root.resolve(bank.reservation.publication.materialization.relative_path, for_write=False)
    allocation_bytes = original_allocation.read_bytes()
    original_allocation.write_bytes(allocation_bytes[:-1]+b' ')
    try:
        with pytest.raises((ValueError, ArtifactPlaneError)):
            api.author_scheduled_programme_preflight(programme=programme, bank=bank, wave_plans=plans,
                template_bytes=templates, artifact_plane=plane, output_directory=tmp_path/'refused')
        assert not (tmp_path/'refused').exists()
        with pytest.raises((ValueError, ArtifactPlaneError)):
            api.load_scheduled_programme_preflight(directory=package.directory, artifact_plane=plane)
    finally:
        original_allocation.write_bytes(allocation_bytes)

    cases = _synthetic_cases(programme)
    seen = []
    result = reduction.reduce_programme(programme, _waves(programme, cases), reduction_id='reduction.software.e4',
        authenticate_wave=lambda wave: seen.append(wave.wave_id))
    assert len(seen) == 16 and len(result.cases) == 576 and len(result.group_scores) == 64
    assert result.order_statistic_rank == 62 and result.radius == Decimal('62.08')
    assert result.numerical_disposition == 'SATISFIED' and result.qualification_disposition == 'UNENTERED'
    assert dict(result.native_disposition_counts)['COMPLETED'] == 1728
    assert all(len(row.cumulative_log_errors) == 15 for row in result.cases)
    with pytest.raises(ValueError, match='missing or duplicated'):
        reduction.reduce_programme(programme, _waves(programme, cases)[:-1], reduction_id='reduction.refused', authenticate_wave=lambda wave: None)
    violated = replace(cases[0], numerical_disposition='VIOLATED', reason_codes=('synthetic-full-numerical-violation',))
    refused = reduction.reduce_programme(programme, _waves(programme, (violated, *cases[1:])),
        reduction_id='reduction.software.violated', authenticate_wave=lambda wave: None)
    assert refused.numerical_disposition == 'VIOLATED' and refused.group_scores[0][1] is None
    unknown = replace(reduction.ScheduledProgrammeCaseResult.unentered(programme.cases[0]),
        disposition='UNKNOWN', numerical_disposition='UNKNOWN', score_disposition='UNKNOWN',
        native=tuple(replace(n, disposition='UNKNOWN', reason_codes=('synthetic-entered-cost-unknown',)) for n in reduction.ScheduledProgrammeCaseResult.unentered(programme.cases[0]).native),
        reason_codes=('synthetic-unknown-requires-retained-replay',))
    failed = replace(reduction.ScheduledProgrammeCaseResult.unentered(programme.cases[1]), disposition='FAILED',
        numerical_disposition='UNKNOWN', score_disposition='FAILED', reason_codes=('synthetic-native-failure',))
    unentered = reduction.ScheduledProgrammeCaseResult.unentered(programme.cases[2])
    incomplete = reduction.reduce_programme(programme, _waves(programme, (unknown, failed, unentered, *cases[3:])),
        reduction_id='reduction.software.incomplete', authenticate_wave=lambda wave: None)
    assert dict(incomplete.disposition_counts) == {'COMPLETED': 573, 'FAILED': 1, 'UNKNOWN': 1, 'UNENTERED': 1}
    assert sum(count for _, count in incomplete.native_disposition_counts) == 1728
    assert incomplete.numerical_disposition == 'UNKNOWN' and incomplete.group_scores[0][1] is None
    assert incomplete.qualification_disposition == 'UNENTERED'
    with pytest.raises(PermissionError, match='actual custody'):
        reduction.reduce_programme(programme, _waves(programme, cases), reduction_id='reduction.custody.refused',
            authenticate_wave=lambda wave: (_ for _ in ()).throw(PermissionError('actual custody refused')))
    with pytest.raises(ValueError, match='complete actual eleven-stage'):
        reduction.collect_completed_programme_case(programme, bank, programme.cases[0], products={}, receipts=(), authenticate_receipt=lambda receipt: None)
