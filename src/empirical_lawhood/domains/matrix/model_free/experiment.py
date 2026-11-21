# SPDX-License-Identifier: MPL-2.0
"""Preparation, exact retained selection, and unchanged public lifecycle."""
from empirical_lawhood.science.experiments.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs, PreparedExperimentFile
from . import design
from .records import NAMESPACE, Product, Specification, selection_key
from .retained_analysis import validate_reanalysis_settings
from .settings import require_assigned_receiver_inputs, require_current_settings


def allocation_for(specification):
    return UnitAllocation("allocation." + NAMESPACE + "." + specification.fingerprint(), (specification.identity,),
        tuple(IndependentUnit(r.unit_id, specification.specification_id, "family.matrix.classical", ("view.primary",),
            specification.mode == "reanalysis") for r in specification.assignments),
        tuple(UnitRoleAssignment(r.unit_id, r.role) for r in specification.assignments))


def bind_inputs(specification, records, *, files=None):
    if type(specification) is not Specification:
        raise TypeError("model-free inquiry needs its exact authored specification")
    specification.__post_init__()
    current = require_current_settings(specification.settings_json)
    require_assigned_receiver_inputs(current, specification.assignments)
    selected = {p.key: p for p in specification.retained_inputs}
    arrays = {p.key: p for p in specification.retained_arrays}
    files = files or {}
    if set(records) - set(selected) or set(files) - set(arrays):
        raise ValueError("undeclared scientific inputs")
    assignments = {selection_key(m, r): r for r in specification.assignments for m in r.modules}
    for key, value in records.items():
        if type(value) is not Product or value.identity != selected[key].identity or value.config.phase != "acquire":
            raise ValueError("reanalysis changes its original acquired product")
        if value.config.specification != specification.parent_lineage.parent_specification:
            raise ValueError("retained acquisition changes its authenticated parent specification")
        original = value.config.assignments[0]
        current = assignments[key]
        if (original.seed, original.role) != (current.seed, current.role) or value.config.module not in current.modules:
            raise ValueError("reanalysis changes independent roots, exposure or module")
        validate_reanalysis_settings(value.config.settings, specification.settings,
            {m for row in specification.assignments for m in row.modules})
        if value.array_artifact != arrays["arrays." + key].identity:
            raise ValueError("reanalysis substitutes the original binary operands")
    for key, file in files.items():
        if file.identity != arrays[key].identity:
            raise ValueError("retained array differs from the exact selected artifact")
    return PreparedExperimentInputs({"allocation": allocation_for(specification)}, (records, files))


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    execution.__post_init__()
    records, files = ({}, {}) if method_inputs is None else method_inputs
    bound = bind_inputs(specification, records, files=files)
    if scientific_inputs != bound.scientific_inputs or protocol_bytes is not None:
        raise ValueError("model-free scientific inputs differ from the declaration")
    dependencies = [ExperimentDependency(NAMESPACE + ".input." + p.key, DependencyKind.EXTERNAL_INPUT,
        "Supply the original authenticated acquisition for " + p.key, p.key) for p in specification.retained_inputs if p.key not in records]
    dependencies.extend(ExperimentDependency(NAMESPACE + ".input." + p.key, DependencyKind.EXTERNAL_INPUT,
        "Supply the original exact native array companion for " + p.key, p.key) for p in specification.retained_arrays if p.key not in files)
    dependencies.extend(ExperimentDependency(NAMESPACE + ".execution." + key, DependencyKind.ENVIRONMENT,
        "Select explicit " + key) for key in ("environment_id", "source_snapshot", "output_root", "workers") if getattr(execution, key) is None)
    allocation, draft, inputs, input_files = None, None, (), ()
    if not dependencies:
        allocation = allocation_for(specification)
        draft, inputs = design.lower(specification, records)
        input_files = tuple(sorted(("external." + key, PreparedExperimentFile(value.identity, "1.0.0", value.path, max(1, value.identity.size_bytes))) for key, value in files.items()))
    configs = design.configs_for(specification)
    census = tuple((m.lower() + "-assigned-roots", sum(m in r.modules for r in specification.assignments)) for m in sorted({m for r in specification.assignments for m in r.modules}))
    return ExperimentPreparation(specification.identity,
        ExperimentCensus(census, tuple((k, v if allocation else 0) for k, v in census), (("operations", len(configs)),),
            (("canonical-products", len(configs)), ("native-array-containers", sum(c.phase == "acquire" for c in configs))), 0),
        tuple(sorted(dependencies, key=lambda d: d.code)), allocation=allocation, draft=draft, input_records=inputs,
        input_files=input_files, execution=execution, specification_record=specification,
        design_records=tuple(sorted((r.record_id, r) for r in records.values())))


def validate_instance(*, specification, allocation, draft, source_records):
    by_id = {r.identity.object_id: r for _, r in source_records}
    records = {p.key: by_id[p.identity.object_id] for p in specification.retained_inputs if p.identity.object_id in by_id}
    if len(by_id) != len(source_records) or len(records) != len(source_records) or len(records) != len(specification.retained_inputs):
        raise ValueError("model-free authoring loses its complete original operand roster")
    bind_inputs(specification, records)
    if allocation != allocation_for(specification) or draft != design.lower(specification, records)[0]:
        raise ValueError("model-free instance changes its code-derived scientific graph")
