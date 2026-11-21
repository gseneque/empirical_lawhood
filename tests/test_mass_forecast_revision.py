# SPDX-License-Identifier: MPL-2.0
"""Bounded exposed record controls; installed custody acceptance remains separate."""

from dataclasses import replace
from decimal import Decimal, localcontext
from hashlib import sha256
from types import SimpleNamespace

import pytest

from scripts.examples.mass_forecast_conformance import CONFORMANCE_SELECTION, disclosed_source
from empirical_lawhood.methods.mass_balance_revision import bindings, design, experiment, science
from empirical_lawhood.methods.mass_balance_revision.records import MAX_BYTES, ForecastUpgradeSource, ForecastUpgradeSpecification, GramPrediction, MassForecastV2
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.experiment_preparation import ExecutionSelection
from empirical_lawhood.execution.extension_conformance import ConformanceProfile, inspect_extension_contracts
from empirical_lawhood.storage.contracts.record_codecs import OperationOutputRecordBinding, RecordCodecCatalog
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave


def selected(case='adverse'):
    source = disclosed_source(case)
    spec = ForecastUpgradeSpecification('disclosed.upgrade.' + case, source.identity,
        source.forecast.config.scope, source.forecast.config.independent_unit_ids)
    return source, spec, design.config_for(spec)


@pytest.mark.parametrize('case,disposition', (('positive', 'SATISFIED'), ('adverse', 'FALSIFIED'), ('unevaluable', 'UNEVALUABLE')))
def test_explicit_conversion_keeps_all_original_bytes_units_and_adverse_findings(case, disposition):
    source, _, config = selected(case)
    before = source.canonical_bytes()
    with localcontext() as context:
        context.prec = 8
        converted = science.convert(config, source)
    assert converted.original_source.canonical_bytes() == before
    assert converted.original_source.assessment.rows[0].disposition == disposition
    assert tuple(row.final_g for row in converted.rows) == (Decimal('3000.000000000000000000000000001'), Decimal(3000), Decimal(10))
    assert tuple(row.unit_id for row in converted.rows) == source.forecast.config.independent_unit_ids
    assert converted.SCHEMA == source.forecast.SCHEMA and converted.VERSION == '2.0.0'
    assert decode_canonical_bytes(converted.canonical_bytes(), MassForecastV2, maximum_bytes=MAX_BYTES) == converted
    assert decode_canonical_bytes(source.canonical_bytes(), ForecastUpgradeSource, maximum_bytes=MAX_BYTES) == source
    assert len(converted.canonical_bytes()) < MAX_BYTES


def test_independent_rational_check_refuses_physically_wrong_but_well_typed_values():
    with pytest.raises(ValueError, match='independent exact'):
        GramPrediction('unit.one', Decimal(1), Decimal(1))
    with pytest.raises(ValueError, match='independent exact'):
        GramPrediction('unit.one', Decimal(1), Decimal(1000), units='kg')
    assert GramPrediction('unit.one', Decimal('2e9'), Decimal('2e12')).units == 'g'
    assert GramPrediction('unit.one', Decimal('1e-30'), Decimal('1e-27')).final_g == Decimal('1e-27')


@pytest.mark.parametrize('damage', ('receipt', 'original-assessment', 'scope', 'units', 'conversion'))
def test_revision_operand_substitution_refuses(damage):
    source, spec, _ = selected()
    with pytest.raises((ValueError, TypeError)):
        if damage == 'receipt':
            replace(source, producing_receipts=source.producing_receipts[:1])
        elif damage == 'original-assessment':
            replace(source, assessment=disclosed_source('positive').assessment)
        elif damage == 'scope':
            experiment.bind_inputs(replace(spec, scope=replace(spec.scope, receiver_id='receiver.other')), {'original':source})
        elif damage == 'units':
            replace(spec, scope=replace(spec.scope, units='g'))
        else:
            replace(spec, conversion='invent-new-observation')


def test_separate_preparation_and_compiler_keep_the_exact_one_operation_census(tmp_path):
    source, spec, config = selected()
    bound = experiment.bind_inputs(spec, {'original':source})
    unresolved = experiment.prepare(spec, scientific_inputs=bound.scientific_inputs,
        execution=ExecutionSelection(), method_inputs=bound.method_inputs)
    assert len(unresolved.dependencies) == 4 and unresolved.draft is None
    prepared = experiment.prepare(spec, scientific_inputs=bound.scientific_inputs,
        execution=ExecutionSelection(workers=1, environment_id='disclosed.environment', output_root=str(tmp_path),
            source_snapshot=ObjectIdentity('disclosed.source', 'empirical-lawhood/testing/source', '1.0.0', 'a'*64)),
        method_inputs=bound.method_inputs)
    experiment.validate_instance(specification=spec, allocation=prepared.allocation,
        draft=prepared.draft, source_records=prepared.design_records)
    operation, = bindings.operation_declarations()
    codecs = RecordCodecCatalog(operation.record_codecs.values(), output_bindings=(
        OperationOutputRecordBinding(operation.registration().selection, MassForecastV2.SCHEMA, MassForecastV2.VERSION),))
    compiled = compile_recursive_wave(draft=prepared.draft, registrations=(operation.registration(),),
        registry=CapabilityRegistry('disclosed.upgrade', (operation.manifest(),)), output_codecs=codecs,
        implementation_commit='a'*40)
    assert len(compiled.execution_plan.tasks) == 1 and compiled.execution_plan.tasks[0].task_id == config.node_id
    assert prepared.census.native_effect_count == 0 and len(prepared.allocation.units) == 3
    assert compiled.output_codecs.for_operation(operation.registration().selection, MassForecastV2.SCHEMA) is MassForecastV2
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=replace(prepared.draft, links=()), registrations=(operation.registration(),),
            registry=compiled.registry, output_codecs=codecs, implementation_commit='a'*40)


def test_retained_derivative_read_keeps_original_falsification_without_another_conversion(monkeypatch):
    from empirical_lawhood.api.mass_forecast_revision import read_result
    from empirical_lawhood.methods.mass_balance_starter import science as original_science
    from empirical_lawhood.execution.recursive_provider import RecursiveOperationProvider
    source, spec, config = selected()
    product = science.convert(config, source)
    def refuse(*args, **kwargs):
        pytest.fail('retained reader entered a producer or scientific calculation')
    monkeypatch.setattr(science, 'convert', refuse)
    monkeypatch.setattr(original_science, 'predict', refuse)
    monkeypatch.setattr(original_science, 'assess', refuse)
    monkeypatch.setattr(RecursiveOperationProvider, 'runners', refuse)
    source_name = 'experiment-source-' + sha256(source.record_id.encode()).hexdigest() + '.json'
    run = 'disclosed.retained-upgrade'
    result = read_result(directory=None, artifact_writer=None, specification=spec,
        instance=SimpleNamespace(specification=spec.identity), payloads={source_name:source.canonical_bytes()},
        report={'run_id':run}, products={'receipts':{config.node_id:SimpleNamespace(operational_status=OperationalStatus.SUCCEEDED)},
            'records':{config.node_id:{config.node_id+'.product':product}}}, draft=None,
        plan=SimpleNamespace(tasks=(SimpleNamespace(task_id=config.node_id),), source_plan=SimpleNamespace(object_id=run)))
    assert result['representation_disposition'] == 'SATISFIED' and result['original_claim_disposition'] == 'FALSIFIED'
    assert result['original_counts'] == {'SATISFIED':2, 'FALSIFIED':1, 'UNEVALUABLE':0}
    assert result['new_measurements'] == 0 and not result['scientific_reconstruction_performed']
    assert len(result['findings']) == 3 and result['qualification'] == 'NOT_ESTABLISHED'


def test_revision_conformance_requires_every_revision_and_explicit_unsupported_refusal():
    assert inspect_extension_contracts(CONFORMANCE_SELECTION)['profile'] == 'record-revisions'
    with pytest.raises(ValueError, match='every coexisting'):
        inspect_extension_contracts(replace(CONFORMANCE_SELECTION, cases=CONFORMANCE_SELECTION.cases[1:]))
    with pytest.raises(ValueError, match='unsupported-producer refusal'):
        inspect_extension_contracts(replace(CONFORMANCE_SELECTION, cases=CONFORMANCE_SELECTION.cases[:-1]))
    from empirical_lawhood.api.extension_conformance import run_extension_conformance
    report = run_extension_conformance(CONFORMANCE_SELECTION, source={'scope':'disclosed-software-only'})
    assert report['status'] == 'PASSED_SELECTED_CHECKS', report
    assert report['contact_attempts'] == [] and not report['full_installed_lifecycle']
    refused = run_extension_conformance(replace(CONFORMANCE_SELECTION, profile=ConformanceProfile.ORDINARY_DEVELOPMENT),
        source={'scope':'disclosed-software-only'})
    assert refused['status'] == 'FAILED' and 'profile' in refused['failure']['message']
