# SPDX-License-Identifier: MPL-2.0
"""Prepare and revalidate the small domain through the ordinary experiment owner."""

from empirical_lawhood.science.experiments.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs

from empirical_lawhood.methods.mass_balance_starter.design import lower
from empirical_lawhood.methods.mass_balance_starter.records import NAMESPACE, PROTOCOL_ID as PROTOCOL_ID, MassEvidence, MassSpecification as MassSpecification


def allocation_for(evidence):
    return UnitAllocation("allocation." + NAMESPACE + "." + evidence.fingerprint(), (evidence.identity,),
        tuple(IndependentUnit(unit, evidence.record_id, "family." + NAMESPACE, (), True) for unit in evidence.independent_unit_ids),
        tuple(UnitRoleAssignment(unit, "development") for unit in evidence.independent_unit_ids))


def bind_inputs(specification, records, *, files=None):
    specification.__post_init__()
    if set(records) - {"evidence"} or files:
        raise ValueError("starter binding adds unselected scientific operands")
    evidence = records.get("evidence")
    if evidence is not None:
        if (type(evidence) is not MassEvidence or evidence.identity != specification.evidence
                or evidence.scope != specification.scope or evidence.independent_unit_ids != specification.independent_unit_ids):
            raise ValueError("starter changes original evidence identity, scope or complete independent-unit census")
        evidence.__post_init__()
    return PreparedExperimentInputs({} if evidence is None else {"evidence": allocation_for(evidence)}, records)


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    execution.__post_init__()
    records = {} if method_inputs is None else method_inputs
    bound = bind_inputs(specification, records)
    if scientific_inputs != bound.scientific_inputs or protocol_bytes is not None:
        raise ValueError("starter changes its declared scientific inputs or supplies unsupported protocol bytes")
    dependencies = [ExperimentDependency("mass-balance.evidence", DependencyKind.EXTERNAL_INPUT,
        "Supply the exact original exposed evidence.", "evidence")] if "evidence" not in records else []
    dependencies.extend(ExperimentDependency("mass-balance.execution." + key, DependencyKind.ENVIRONMENT,
        "Select explicit " + key + ".") for key in ("environment_id", "source_snapshot", "output_root", "workers")
        if getattr(execution, key) is None)
    allocation, draft, inputs = None, None, ()
    if not dependencies:
        evidence = records["evidence"]
        allocation, (draft, inputs) = allocation_for(evidence), lower(specification, evidence)
    count = len(specification.independent_unit_ids)
    return ExperimentPreparation(specification.identity,
        ExperimentCensus((("independent-units", count),), (("independent-units", 0 if allocation is None else count),),
            (("operations", 2),), (("canonical-products", 2),), 0), tuple(sorted(dependencies, key=lambda d: d.code)),
        allocation=allocation, draft=draft, input_records=inputs, execution=execution,
        specification_record=specification,
        design_records=() if "evidence" not in records else ((records["evidence"].record_id, records["evidence"]),))


def validate_instance(*, specification, allocation, draft, source_records):
    if len(source_records) != 1:
        raise ValueError("starter instance requires its one original evidence record")
    object_id, evidence = source_records[0]
    bind_inputs(specification, {"evidence": evidence})
    if (object_id != evidence.record_id or allocation != allocation_for(evidence)
            or draft != lower(specification, evidence)[0]):
        raise ValueError("starter instance changes its original evidence or code-derived complete design")
