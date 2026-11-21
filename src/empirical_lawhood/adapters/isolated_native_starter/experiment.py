# SPDX-License-Identifier: MPL-2.0
"""Canonical preparation through the existing experiment lifecycle."""

from empirical_lawhood.science.experiments.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs

from empirical_lawhood.adapters.isolated_native_starter.design import lower
from empirical_lawhood.adapters.isolated_native_starter.records import NAMESPACE, UNIT, SquareInput


def allocation_for(operand):
    return UnitAllocation("allocation." + NAMESPACE + "." + operand.fingerprint(), (operand.identity,),
        (IndependentUnit(UNIT, operand.record_id, "family." + NAMESPACE, (), True),),
        (UnitRoleAssignment(UNIT, "development"),))


def bind_inputs(specification, records, *, files=None):
    specification.__post_init__()
    if set(records) - {"operand", "provenance"} or files:
        raise ValueError("isolated starter adds an undeclared source role")
    for name, kind in (("operand", SquareInput), ("provenance", NumericalProducingProvenance)):
        value = records.get(name)
        if value is not None:
            if type(value) is not kind or value.identity != getattr(specification, name):
                raise ValueError("isolated starter changes an original input identity or revision")
            value.__post_init__()
    scientific = {} if "operand" not in records else {"operand": allocation_for(records["operand"])}
    return PreparedExperimentInputs(scientific, records)


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    execution.__post_init__()
    records = {} if method_inputs is None else method_inputs
    bound = bind_inputs(specification, records)
    if scientific_inputs != bound.scientific_inputs or protocol_bytes is not None:
        raise ValueError("isolated starter changes its scientific input census or adds protocol bytes")
    dependencies = [ExperimentDependency(NAMESPACE + "." + name, DependencyKind.EXTERNAL_INPUT,
        "Supply the original " + name + ".", name) for name in ("operand", "provenance") if name not in records]
    dependencies.extend(ExperimentDependency(NAMESPACE + ".execution." + name, DependencyKind.ENVIRONMENT,
        "Select explicit " + name + ".") for name in ("environment_id", "source_snapshot", "output_root", "workers")
        if getattr(execution, name) is None)
    allocation, draft, inputs = None, None, ()
    if not dependencies:
        allocation = allocation_for(records["operand"])
        draft, inputs = lower(specification, records["operand"], records["provenance"])
    return ExperimentPreparation(specification.identity,
        ExperimentCensus((("independent-units", 1),), (("independent-units", 0 if allocation is None else 1),),
            (("operations", 1),), (("canonical-products", 1),), 1), tuple(sorted(dependencies, key=lambda r: r.code)),
        allocation=allocation, draft=draft, input_records=inputs, execution=execution, specification_record=specification,
        design_records=tuple(sorted((value.identity.object_id, value) for value in records.values())))


def validate_instance(*, specification, allocation, draft, source_records):
    if len(source_records) != 2:
        raise ValueError("isolated starter requires its complete original source census")
    by_type = {type(value): (object_id, value) for object_id, value in source_records}
    if set(by_type) != {SquareInput, NumericalProducingProvenance}:
        raise ValueError("isolated starter substitutes its exact source roles")
    records = {"operand": by_type[SquareInput][1], "provenance": by_type[NumericalProducingProvenance][1]}
    bind_inputs(specification, records)
    if (any(name != value.identity.object_id for name, value in source_records)
            or allocation != allocation_for(records["operand"])
            or draft != lower(specification, records["operand"], records["provenance"])[0]):
        raise ValueError("isolated starter changes its code-derived original design")
