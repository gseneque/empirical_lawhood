# SPDX-License-Identifier: MPL-2.0
"""Pure preparation through the public experiment protocol."""
from empirical_lawhood.science.experiments.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs, PreparedExperimentFile
from . import design
from .records import Acquisition, Calibration, NAMESPACE, SeriesSpecification


def allocation_for(specification):
    return UnitAllocation("allocation." + NAMESPACE + "." + specification.fingerprint(), (specification.identity,),
        tuple(IndependentUnit(row.unit_id, specification.specification_id, "family.matrix.classical",
            ("view.primary", "view.refined"), specification.mode == "reanalysis") for row in specification.assignments),
        tuple(UnitRoleAssignment(row.unit_id, row.role) for row in specification.assignments))


def bind_inputs(specification, records, *, files=None):
    if type(specification) is not SeriesSpecification:
        raise TypeError("classical series requires its exact authored specification")
    specification.__post_init__()
    selected = {p.key: p for p in specification.retained_inputs}
    files = files or {}
    array_selection = {p.key: p for p in specification.retained_arrays}
    if set(records) - set(selected) or set(files) - set(array_selection):
        raise ValueError("classical series supplied undeclared scientific operands")
    assigned = {row.unit_id: row for row in specification.assignments}
    for key, value in records.items():
        expected_type = Calibration if key == "calibration" else Acquisition
        if type(value) is not expected_type or value.identity != selected[key].identity:
            raise ValueError("reanalysis changes an original retained product identity")
        value.__post_init__()
        if type(value) is Calibration:
            if value.config.assignments != tuple(row for row in specification.assignments if row.role != "confirmation"):
                raise ValueError("reanalysis changes the original TRAIN/CAL root allocation")
        elif key not in assigned or value.config.assignments != (assigned[key],):
            raise ValueError("reanalysis changes the original CONF root assignment")
        # Analysis-only phase selection may change. All original acquisition
        # choices remain fixed; source updates never rewrite producing identity.
        original = value.config.settings.copy()
        current = specification.settings.copy()
        original.pop("phases", None)
        current.pop("phases", None)
        if original != current:
            raise ValueError("reanalysis cannot change the original numerical acquisition settings")
    if specification.mode == "reanalysis" and "calibration" in records:
        frozen = records["calibration"]
        for key, value in records.items():
            if type(value) is Acquisition and (value.calibration != frozen.identity
                    or value.config.specification != frozen.config.specification):
                raise ValueError("reanalysis substitutes the original CONF calibration commitment")
    for key, file in files.items():
        if file.identity != array_selection[key].identity:
            raise ValueError("reanalysis binary companion differs from the original selected artifact")
        product = records.get(key.removeprefix("arrays."))
        if product is not None and product.array_artifact != file.identity:
            raise ValueError("reanalysis array bytes belong to a different native root")
    return PreparedExperimentInputs({"allocation": allocation_for(specification)}, (records, files))


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    execution.__post_init__()
    records, files = ({}, {}) if method_inputs is None else method_inputs
    bound = bind_inputs(specification, records, files=files)
    if scientific_inputs != bound.scientific_inputs or protocol_bytes is not None:
        raise ValueError("classical series changes its declared scientific inputs")
    dependencies = [ExperimentDependency(NAMESPACE + ".input." + p.key, DependencyKind.EXTERNAL_INPUT,
        "Supply the exact authenticated retained product for " + p.key + ".", p.key)
        for p in specification.retained_inputs if p.key not in records]
    dependencies.extend(ExperimentDependency(NAMESPACE + ".input." + p.key, DependencyKind.EXTERNAL_INPUT,
        "Supply the exact original binary matrix arrays for " + p.key + ".", p.key)
        for p in specification.retained_arrays if p.key not in files)
    dependencies.extend(ExperimentDependency(NAMESPACE + ".execution." + key, DependencyKind.ENVIRONMENT,
        "Select explicit " + key + ".") for key in ("environment_id", "source_snapshot", "output_root", "workers")
        if getattr(execution, key) is None)
    allocation, draft, inputs, input_files = None, None, (), ()
    if not dependencies:
        allocation = allocation_for(specification)
        draft, inputs = design.lower(specification, records)
        input_files = tuple(sorted(("external." + key,
            PreparedExperimentFile(value.identity, "1.0.0", value.path, value.identity.size_bytes))
            for key, value in files.items()))
    count = len(design.configs_for(specification))
    roles = tuple(sorted((role + "-roots", sum(r.role == role for r in specification.assignments))
        for role in ("training", "calibration", "confirmation")))
    return ExperimentPreparation(specification.identity,
        ExperimentCensus(roles, tuple((key, value if allocation is not None else 0) for key, value in roles),
            (("operations", count),), (("canonical-products", count), ("native-array-containers", 0 if specification.mode == "reanalysis" else len(specification.assignments))), 0),
        tuple(sorted(dependencies, key=lambda d: d.code)), allocation=allocation, draft=draft,
        input_records=inputs, input_files=input_files, execution=execution, specification_record=specification,
        design_records=tuple(sorted((value.record_id, value) for value in records.values())))


def validate_instance(*, specification, allocation, draft, source_records):
    by_id = {r.identity.object_id: r for _, r in source_records}
    if len(by_id) != len(source_records):
        raise ValueError("retained source roster duplicates a product")
    records = {p.key: by_id[p.identity.object_id] for p in specification.retained_inputs if p.identity.object_id in by_id}
    if len(records) != len(source_records) or len(records) != len(specification.retained_inputs):
        raise ValueError("classical series loses its complete retained input roster")
    bind_inputs(specification, records)
    if allocation != allocation_for(specification) or draft != design.lower(specification, records)[0]:
        raise ValueError("classical series changes the original allocation or code-derived graph")
