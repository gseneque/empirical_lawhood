# SPDX-License-Identifier: MPL-2.0
"""Independent authority/port pins for the consolidated current declarations."""

from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_prospective import operation_bindings as prospective
from empirical_lawhood.adapters.methods.matrix_scheduled_history import (
    calibration_bindings as calibration,
    compact_bindings as compact,
    operation_bindings as scheduled,
    programme_acquisition_bindings as acquisition,
    programme_bindings as programme,
    programme_calibration_bindings as global_calibration,
    programme_confirmation as confirmation,
    programme_global as global_freeze,
    programme_tail_freeze as tail,
    response_bindings as response,
    revision_calibrated_future_bindings as calibrated_future,
    revision_forecast_bindings as revision_forecast,
    revision_future_bindings as revision_future,
)
from empirical_lawhood.runtime.capabilities import CapabilityPermission as Permission
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner
from empirical_lawhood.runtime.plans import BarrierKind, ScientificStage


# These rosters and implementation labels are copied from the preserved 3eb56810
# handwritten contracts, independently of the new declaration projections.
CORE_ROLES = frozenset((
    'prefix', 'numerical', 'measure', 'check', 'project', 'forecast',
    'forecast-calibrated', 'continue', 'full-numerical', 'continue-development',
    'full-numerical-development', 'commit',
))
RESPONSE_ROLES = frozenset((
    'physical-forecast', 'responses', 'response-score', 'responses-development',
    'response-score-development',
))
CALIBRATION_ROLES = frozenset(('calibrate', 'calibration-qualify'))
ALL_ROLES = CORE_ROLES | RESPONSE_ROLES | CALIBRATION_ROLES
WAVE_ROLES = (ALL_ROLES - {'commit', *CALIBRATION_ROLES}) | {
    'open', 'collect', 'collect-development',
}


def declarations(owner):
    return owner.calibration_declarations() if owner in (calibration, global_calibration) else (
        owner.response_declarations() if owner is response else owner.operation_declarations())


def by_role(owner):
    rows = declarations(owner)
    result = {row.capability_key.rsplit('.', 1)[-1]: row for row in rows}
    assert len(result) == len(rows)
    return result


@pytest.mark.parametrize('owner,roles,label', (
    (prospective, {'origin', 'forecast', 'futures', 'assess'}, 'matrix-prospective.exposed-causal-{role}-v1'),
    (compact, ALL_ROLES, 'matrix-scheduled-history-compact.shared-original-subject-{role}.v2'),
    (programme, WAVE_ROLES, None),
    (acquisition, WAVE_ROLES, None),
    (revision_future, {'continue', 'responses'}, 'matrix-scheduled-revision-future.prior-revision-seal-original-v2-{role}'),
    (calibrated_future, {'continue', 'responses'}, 'matrix-scheduled-revision-calibrated-future.{role}.original-calibration-and-seal.v1'),
    (global_freeze, {'global-commit'}, 'bounded-actual-global-freeze.v1'),
    (confirmation, {'confirmation-global-commit'}, 'genuine-qualified-parent-confirmation-freeze.v1'),
    (tail, {'tail-custody-freeze'}, 'fixed-current-tail-metadata-before-reduction-reveal.v1'),
    (revision_forecast, {'seal'}, 'matrix-scheduled-revision-future.physical-grid-frozen-model-prediction'),
    (global_calibration, CALIBRATION_ROLES, 'complete-global64-calibration-{role}.v1'),
))
def test_current_operation_rosters_and_original_implementation_pins(owner, roles, label):
    rows = by_role(owner)
    assert set(rows) == set(roles)
    for role, row in rows.items():
        expected = label
        if owner in (programme, acquisition):
            own = role in {'open', 'collect', 'collect-development'}
            namespace = 'matrix-scheduled-programme' + ('-acquisition' if owner is acquisition else '')
            suffix = ('local-acquisition-original-v2-state-' if own else 'acquisition-original-v2-') if owner is acquisition else (
                'actual-admission-original-v2-state-' if own else 'admitted-original-v2-')
            expected = namespace + '.' + suffix + role
        expected = expected.format(role=role)
        assert row.implementation_id == expected
        assert row.capability_version == '1.0.0'
        assert row.manifest().implementation_sha256 == sha256((row.capability_key + '.' + expected).encode()).hexdigest()


def test_original_scheduled_implementation_pins_cover_all_three_scientific_families():
    rows = by_role(scheduled)
    assert set(rows) == ALL_ROLES
    for role, row in rows.items():
        group = 'original-scheduled-' if role in CORE_ROLES else (
            'scheduled-original-' if role in RESPONSE_ROLES else 'original-whole-group-')
        expected = 'matrix-scheduled-history.' + group + role + '.v1'
        assert row.implementation_id == expected
        assert row.manifest().implementation_sha256 == sha256((row.capability_key + '.' + expected).encode()).hexdigest()


@pytest.mark.parametrize('owner', (
    scheduled, compact, programme, acquisition, global_freeze, confirmation,
    tail, revision_forecast, revision_future, calibrated_future, global_calibration,
    prospective,
))
def test_exact_original_permissions_are_not_inferred_from_implementation_labels(owner):
    for role, row in by_role(owner).items():
        read = Permission.READ_FROZEN_MODELS
        if owner is prospective or role.endswith('-development'):
            read = Permission.READ_DEVELOPMENT
        elif role in {'continue', 'full-numerical', 'forecast-calibrated', 'responses',
                'response-score', 'calibrate', 'calibration-qualify', 'collect'}:
            read = Permission.READ_SEALED_OUTCOMES
        expected = (Permission.READ_EXTERNAL_ARTIFACTS, Permission.WRITE_EXTERNAL_ARTIFACTS, read)
        if role == 'calibration-qualify':
            expected += (Permission.REVEAL_OUTCOMES,)
        expected = tuple(sorted(expected))
        assert row.permissions == expected
        assert row.manifest().permissions == expected
        assert row.registration().required_permissions == expected


@pytest.mark.parametrize('owner', (scheduled, compact, global_calibration))
def test_qualification_retains_separate_reveal_barrier_and_adjudication(owner):
    row = by_role(owner)['calibration-qualify']
    assert row.stage is ScientificStage.REVEAL
    assert row.execution_properties.barrier is BarrierKind.REVEAL
    assert row.scientific_hooks.adjudication_output_id == 'adjudication'
    assert tuple(output.output_id for output in row.outputs) == ('adjudication',)
    assert row.execution_properties.native_effect is False


@pytest.mark.parametrize('owner', (scheduled, compact))
def test_native_stream_and_checkpoint_ports_preserve_complete_current_census(owner):
    rows = by_role(owner)
    prefix = {port.port_id: port for port in rows['prefix'].input_ports}
    pulses = {port.port_id: port for port in rows['responses'].input_ports}
    assert (prefix['streams'].minimum_count, prefix['streams'].maximum_count) == (4, None)
    assert (pulses['streams'].minimum_count, pulses['streams'].maximum_count) == (
        (8, 8) if owner is scheduled else (8, None))
    assert {output.output_id for output in rows['prefix'].outputs} == {'product', 'arrays', 'checkpoint'}
    assert {output.output_id for output in rows['project'].outputs} == {'product', 'arrays', 'feature'}
    assert {output.output_id for output in rows['physical-forecast'].outputs} == {'product', 'arrays'}


@pytest.mark.parametrize('owner', (programme, acquisition))
def test_real_admission_replaces_only_commitment_port_and_retains_global_custody(owner):
    rows = by_role(owner)
    expected_admission = 'empirical-lawhood/matrix-scheduled-programme/' + (
        'acquisition-admission' if owner is acquisition else 'wave-admission')
    for role in WAVE_ROLES - {'open', 'collect', 'collect-development'}:
        ports = {port.port_id: port for port in rows[role].input_ports}
        if 'commitment' in {port.port_id for port in by_role(compact)[role].input_ports}:
            assert ports['admission'].payload_schema == expected_admission
            assert 'commitment' not in ports
    opener = {port.port_id: port for port in rows['open'].input_ports}
    assert set(opener) == ({'bank', 'global-parent', 'confirmation-global-parent', 'global-parent-receipt'}
        if owner is acquisition else {'bank', 'global-parent', 'global-parent-receipt'})
    assert opener['global-parent-receipt'].minimum_count == 1
    assert opener['global-parent'].minimum_count == (0 if owner is acquisition else 1)
    if owner is acquisition:
        assert opener['confirmation-global-parent'].minimum_count == 0
    collector = {port.port_id: port for port in rows['collect'].input_ports}
    assert len(collector) == 13
    assert all((port.minimum_count, port.maximum_count) == (1, None)
        for key, port in collector.items() if key.startswith('products.'))


def test_global_calibration_preserves_all_sixteen_wave_and_receipt_inputs():
    row = by_role(global_calibration)['calibrate']
    ports = {port.port_id: port for port in row.input_ports}
    assert set(ports) == {'bank', 'tail-freeze', 'waves', 'wave-custody', 'acquisition-wave-custody',
        'wave-receipts', 'wave-configurations', 'acquisition-wave-configurations'}
    assert (ports['waves'].minimum_count, ports['waves'].maximum_count) == (16, 16)
    assert (ports['wave-receipts'].minimum_count, ports['wave-receipts'].maximum_count) == (16, 16)
    for key in ('wave-custody', 'acquisition-wave-custody', 'wave-configurations', 'acquisition-wave-configurations'):
        assert (ports[key].minimum_count, ports[key].maximum_count) == (0, 16)


@pytest.mark.parametrize('owner,extra', (
    (revision_future, {'revision-scope', 'revision-seal', 'revision-custody', 'revision-seal-receipt'}),
    (calibrated_future, {'revision-scope', 'revision-seal', 'revision-custody', 'revision-seal-receipt', 'revision-calibration-custody'}),
))
def test_prior_revision_variants_preserve_actual_external_custody_and_native_preparation(owner, extra):
    for role, row in by_role(owner).items():
        base = by_role(acquisition)[role]
        assert {port.port_id for port in row.input_ports} == {port.port_id for port in base.input_ports} | extra
        assert row.execution_properties.native_work_preparer is base.execution_properties.native_work_preparer
        assert row.execution_properties.runner_preparation_factory is revision_future.prepare_for_invocation
        assert row.execution_properties.native_effect is True
        assert tuple((kind.SCHEMA, kind.VERSION) for kind in row.input_record_types) == tuple(sorted(
            (kind.SCHEMA, kind.VERSION) for kind in row.input_record_types))


def test_discovery_and_factory_projection_never_construct_science_runners(monkeypatch):
    def refused(*args, **kwargs):
        pytest.fail('declaration projection constructed a scientific runner')

    for owner, names in (
        (scheduled, ('ScheduledCommitter', 'ScheduledNativeRunner', 'ScheduledRunner')),
        (response, ('ScheduledPulseNativeRunner', 'ScheduledResponseRunner')),
        (calibration, ('ScheduledCalibrator',)),
        (programme, ('ProgrammeWaveOpener', 'ProgrammeWaveCollector')),
        (acquisition, ('ProgrammeAcquisitionOpener', 'ProgrammeAcquisitionCollector')),
        (global_freeze, ('ScheduledProgrammeGlobalCommitter',)),
        (confirmation, ('ScheduledProgrammeConfirmationGlobalCommitter',)),
        (tail, ('ScheduledProgrammeTailCustodyFreezer',)),
        (revision_forecast, ('ScheduledRevisionForecaster',)),
        (global_calibration, ('ScheduledProgrammeCalibrator',)),
        (prospective, ('MatrixRunner', 'MatrixFutureRunner')),
    ):
        for name in names:
            monkeypatch.setattr(owner, name, refused)
    for owner in (scheduled, compact, programme, acquisition, global_freeze, confirmation, tail,
            revision_forecast, revision_future, calibrated_future, global_calibration, prospective):
        for row in declarations(owner):
            factory = row.provider_factory()
            assert factory.manifest == row.manifest()
            assert factory.registration == row.registration()
            assert callable(factory.runner_factory)


def test_current_native_callbacks_and_inquiry_identity_keep_their_owning_functions():
    for owner in (scheduled, compact, programme, acquisition):
        rows = by_role(owner)
        assert rows['prefix'].execution_properties.native_work_preparer is scheduled.prepare_native_work
        assert rows['responses'].execution_properties.native_work_preparer is response.prepare_native_work
        assert rows['prefix'].execution_properties.complete_unit_census is True
        assert rows['responses'].execution_properties.complete_unit_census is True
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_qualified_parent
    calibrated = by_role(acquisition)['forecast-calibrated'].scientific_hooks
    assert calibrated.qualified_parent_assessor is programme_qualified_parent.qualified_parent_assessor
    assert calibrated.qualified_parent_evidence_schema_ids == (
        global_calibration.ScheduledProgrammeCalibrationEvidence.SCHEMA,)
    assert calibrated.qualified_parent_prior_execution_bindings is programme_qualified_parent.prior_execution_bindings
    assert calibrated.qualified_parent_prior_execution_scope_validator is programme_qualified_parent.prior_execution_scope_validator
    for row in prospective.operation_declarations():
        assert row.inquiry_hooks.inquiry_record_identity is prospective.identity


@pytest.mark.parametrize('owner,role', (
    (confirmation, 'confirmation-global-commit'),
    (global_calibration, 'calibration-qualify'),
))
def test_parent_preparation_dispatches_exact_current_supplier_before_any_execution(owner, role):
    row = by_role(owner)[role]
    raw_runner = row.runner_factory()
    calls = []
    # This is a routing marker, not a TaskContext, grant or scientific fixture.
    # The real current supplier remains responsible for custody and refuses here.
    marker = object()

    class RefusingSupplier:
        def prepare_programme_task(self, context, runner):
            calls.append((context, runner))
            raise PermissionError('actual parent custody is not supplied')

    prepare = row.execution_properties.runner_preparation_factory
    assert callable(prepare)
    wrapped = prepare(RefusingSupplier(), raw_runner)
    assert type(wrapped) is ParentPreparedTaskRunner
    assert wrapped.manifest == raw_runner.manifest == row.manifest()
    assert wrapped.native_effect is False
    assert calls == []
    with pytest.raises(PermissionError, match='PARENT_RUNNER_PREPARATION_REQUIRED'):
        wrapped.execute(marker)
    assert calls == []
    with pytest.raises(PermissionError, match='actual parent custody is not supplied'):
        wrapped.prepare_execution(marker)
    assert calls == [(marker, raw_runner)]
