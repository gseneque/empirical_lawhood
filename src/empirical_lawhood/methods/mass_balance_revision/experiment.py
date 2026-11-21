# SPDX-License-Identifier: MPL-2.0
"""Bind and prepare one explicit conversion with its complete retained source."""

from empirical_lawhood.science.experiments.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs

from empirical_lawhood.methods.mass_balance_revision.design import lower
from empirical_lawhood.methods.mass_balance_revision.records import ForecastUpgradeSource


def allocation_for(source):
    units = source.forecast.config.independent_unit_ids
    return UnitAllocation('allocation.mass-balance.upgrade.' + source.fingerprint(), (source.identity,),
        tuple(IndependentUnit(unit, source.record_id, 'family.mass-balance.original-case', (), True) for unit in units),
        tuple(UnitRoleAssignment(unit, 'development') for unit in units))


def bind_inputs(specification, records, *, files=None):
    specification.__post_init__()
    if set(records) - {'original'} or files:
        raise ValueError('forecast upgrade adds an undeclared source operand')
    source = records.get('original')
    if source is not None:
        if (type(source) is not ForecastUpgradeSource or source.identity != specification.source
                or source.forecast.config.scope != specification.scope
                or source.forecast.config.independent_unit_ids != specification.independent_unit_ids):
            raise ValueError('forecast upgrade changes its retained source, scope or complete original unit census')
        source.__post_init__()
    return PreparedExperimentInputs({} if source is None else {'original':allocation_for(source)}, records)


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    records = {} if method_inputs is None else method_inputs
    bound = bind_inputs(specification, records)
    execution.__post_init__()
    if scientific_inputs != bound.scientific_inputs or protocol_bytes is not None:
        raise ValueError('forecast upgrade changes its exact selected input contract')
    dependencies = [] if 'original' in records else [ExperimentDependency('mass-balance.upgrade.original',
        DependencyKind.EXTERNAL_INPUT, 'Select the authenticated original forecast and assessment source.', 'original')]
    dependencies.extend(ExperimentDependency('mass-balance.upgrade.execution.' + name, DependencyKind.ENVIRONMENT,
        'Select explicit ' + name + '.') for name in ('environment_id', 'source_snapshot', 'output_root', 'workers')
        if getattr(execution, name) is None)
    allocation, draft, inputs = None, None, ()
    if not dependencies:
        allocation = allocation_for(records['original'])
        draft, inputs = lower(specification, records['original'])
    count = len(specification.independent_unit_ids)
    return ExperimentPreparation(specification.identity,
        ExperimentCensus((('original-independent-units', count),),
            (('original-independent-units', count if allocation is not None else 0),),
            (('operations', 1),), (('canonical-products', 1),), 0),
        tuple(sorted(dependencies, key=lambda value:value.code)), allocation=allocation, draft=draft,
        input_records=inputs, execution=execution, specification_record=specification,
        design_records=() if 'original' not in records else ((records['original'].record_id, records['original']),))


def validate_instance(*, specification, allocation, draft, source_records):
    if len(source_records) != 1:
        raise ValueError('forecast upgrade requires its one complete original source')
    record_id, source = source_records[0]
    bind_inputs(specification, {'original':source})
    if record_id != source.record_id or allocation != allocation_for(source) or draft != lower(specification, source)[0]:
        raise ValueError('forecast upgrade changes its separately admitted complete original design')
