# SPDX-License-Identifier: MPL-2.0
"""Full E4 storage-wave conformance over explicitly exposed software inputs."""

from dataclasses import replace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import (
    compact_records as compact, programme_composition as composition,
    programme_qualification as qualification, programme_records as records,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_scheduled_calibration import TEST_BUDGET
from tests.test_matrix_scheduled_compact_graph import (
    bank as bank, calibration64_bank, provenance as provenance, response_bank as response_bank,
    scheduled as scheduled, stock as stock,
)


def programme576_bank(response_bank):
    """Expose the full original fixture population without a scientific graph."""
    bank, templates = calibration64_bank(response_bank, cases_per_group=9, programme_only=True)
    programme = records.ScheduledProgramme.from_bank(bank, programme_id='programme.software.complete-e4',
        mode='E4_REVISION_CALIBRATION', wave_group_count=4)
    return programme, bank, templates


def compile_wave(programme, bank, templates, wave):
    tasks = composition.programme_wave_task_ids(programme, bank, wave.wave_id)
    owners = tuple((f'obligation.software.programme.{wave.wave_id}.{index:03}', task) for index, task in enumerate(tasks))
    return composition.compile_programme_wave(programme=programme, bank=bank, wave_id=wave.wave_id,
        proof_owners=owners, operational_budgets=dict.fromkeys(tasks, TEST_BUDGET), template_bytes=templates)


def test_full576_programme_compiles_bounded_whole_group_waves_and_refuses_substitution(response_bank, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import response_error_prediction
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast, response_science
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments, parameter_source
    from empirical_lawhood.runtime.recursive_prospective import recursive_selection_decoder_registration

    def blocked(*args, **kwargs):
        pytest.fail('programme declaration conformance entered native science or fitting')

    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    monkeypatch.setattr(parameter_history_segments, 'acquire_parameter_segment', blocked)
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', blocked)
    monkeypatch.setattr(response_science, 'native_responses', blocked)
    monkeypatch.setattr(response_forecast, 'forecast', blocked)
    monkeypatch.setattr(response_error_prediction, 'fit_error_model', blocked)
    monkeypatch.setattr(response_error_prediction, 'fit_scheduled_error_model', blocked)
    programme, bank, templates = programme576_bank(response_bank)
    assert len(programme.cases) == 576
    assert len(programme.group_ids) == 64
    assert len(programme.source_census) == len(bank.sources) == 582
    assert programme.order_statistic_rank == 62
    assert len(bank.forecast_design.training_record.population.selections) == 256
    assert len(bank.forecast_design.model_record.training_root_ids) == 128
    assert len(bank.canonical_bytes()) <= records.MAXIMUM_PROGRAMME_BYTES
    assert len(programme.canonical_bytes()) <= records.MAXIMUM_PROGRAMME_BYTES
    assert len(programme.waves) == 16
    plans, reports = [], []
    for wave in programme.waves:
        plan, operands = compile_wave(programme, bank, templates, wave)
        report = qualification.validate_programme_wave(plan, programme, bank, templates)
        assert decode_canonical_bytes(plan.canonical_bytes(), composition.ScheduledProgrammeWavePlan,
            maximum_bytes=composition.MAXIMUM_WAVE_PLAN_BYTES) == plan
        assert len(plan.canonical_bytes()) < 16*1024**2
        assert len(plan.operations) == 396
        assert len(plan.native_contracts) == len(plan.collector_inputs) == 108
        assert len(plan.task_ids) == 397
        assert operands[bank.bank_id] is bank
        assert not any(type(value) is compact.ScheduledCompactCommitmentConfig for value in operands.values())
        assert all(operation.config_identity.object_schema != compact.ScheduledCompactCommitmentConfig.SCHEMA
            and not operation.selection.capability_key.endswith(('.calibrate', '.calibration-qualify', '.commit'))
            for operation in plan.operations)
        assert report.scientific_authority == 'NONE'
        assert report.collector_provider_available is report.issued_execution_proved is False
        plans.append(plan)
        reports.append(report)
    assert len({operation.node_id for plan in plans for operation in plan.operations}) == 6336
    assert len({native.task_id for plan in plans for native in plan.native_contracts}) == 1728
    assert len({plan.global_commitment for plan in plans}) == 1
    assert len({plan.model_parents for plan in plans}) == 1
    assert tuple(sorted(root for plan in plans for root in plan.wave.root_ids)) == tuple(case.root_id for case in programme.cases)
    assert recursive_selection_decoder_registration(implementation_sha256='a'*64).maximum_payload_bytes == 16*1024**2

    plan = plans[0]
    # Mutations preserve enough record shape to exercise exact conformance;
    # omitted whole-group/collector/native census fails even before validation.
    with pytest.raises(ValueError, match='nine cases'):
        replace(plan.wave, root_ids=plan.wave.root_ids[:-1])
    with pytest.raises(ValueError, match='terminal census'):
        replace(plan, collector_inputs=plan.collector_inputs[:-1])
    with pytest.raises(ValueError, match='three native'):
        replace(plan, native_contracts=plan.native_contracts[:-1])
    changed_bank = replace(plan.bank, object_fingerprint='e'*64)
    changed_parent = replace(plan.global_commitment, object_fingerprint='e'*64)
    future = next(e for e in plan.links if e.consumer_input_id.startswith('streams.future.'))
    current = next(e.external_input_id for e in plan.links if e.consumer_node_id == future.consumer_node_id
        and e.consumer_input_id == future.consumer_input_id.replace('streams.future.', 'streams.'))
    native = plan.native_contracts[0]
    native_id = ObjectIdentity(native.configuration.object_id, native.configuration.object_schema,
        native.configuration.object_version, 'e'*64)
    corruptions = (
        replace(plan, bank=changed_bank), replace(plan, global_commitment=changed_parent),
        replace(plan, links=tuple(replace(e, external_input_id=current) if e == future else e for e in plan.links)),
        replace(plan, native_contracts=(replace(native, configuration=native_id), *plan.native_contracts[1:])),
    )
    for corruption in corruptions:
        with pytest.raises(ValueError, match='substitutes|exact source'):
            qualification.validate_programme_wave(corruption, programme, bank, templates)
