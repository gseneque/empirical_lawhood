# SPDX-License-Identifier: MPL-2.0
"""Editable conditional E4 factorial design through the common programme API.

The method specification is the researcher selection. Preparation derives its
configurations and graph from the four original records; it invents no sampling
evidence and grants no protected access.
"""

from collections.abc import Mapping

from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentPreparation,
)

from .programme_factorial import (
    E4_COMPARISONS, FAMILY_IDS, ScheduledFactorialSpecification,
    lower_exposed_programme_factorial, validate_factorial_inputs,
)
from .programme_records import MODES
from .programme_selection import programme_selection_allocation
from .selection_preparation import INPUT_TYPES, _ID_FIELDS, ProgrammeSelectionInputs, bind_programme_inputs

PROTOCOL_ID = "matrix.e4.exposed-factorial"


def bind_factorial_inputs(specification, records):
    if type(specification) is not ScheduledFactorialSpecification:
        raise TypeError("factorial preparation requires its exact editable method specification")
    specification.__post_init__()
    return bind_programme_inputs(records)


def _scientific_inputs(specification, scientific_inputs, method_inputs):
    if type(specification) is not ScheduledFactorialSpecification:
        raise TypeError("factorial preparation requires its exact editable method specification")
    specification.__post_init__()
    if not isinstance(scientific_inputs, Mapping):
        raise TypeError("factorial preparation requires its original allocation mapping")
    if method_inputs is not None and type(method_inputs) is not ProgrammeSelectionInputs:
        raise TypeError("factorial preparation requires the typed original programme inputs")
    inputs = ProgrammeSelectionInputs() if method_inputs is None else method_inputs
    inputs.__post_init__()
    dependencies = []

    def dependency(code, kind, detail, key=None):
        dependencies.append(ExperimentDependency("matrix.e4.factorial."+code, kind, detail, key))

    if set(scientific_inputs) - {"development"}:
        dependency("unknown-allocation", DependencyKind.EXTERNAL_INPUT,
            "This exposed factorial method uses the original development allocation.")
    for key in INPUT_TYPES:
        if getattr(inputs, key) is None:
            dependency(key+".missing", DependencyKind.EXTERNAL_INPUT,
                "Supply the original "+key+" record; an editable design invents no observations.", key)
    allocation = None
    if inputs.programme is not None:
        try:
            allocation = programme_selection_allocation(inputs.programme)
            if (specification.programme != inputs.programme.identity
                    or specification.target.criterion != inputs.programme.criterion):
                raise ValueError("factorial design changes its original programme or criterion")
            if scientific_inputs.get("development") != allocation:
                raise ValueError("factorial design must retain the original independent whole groups and nested views")
        except (ValueError, TypeError) as error:
            dependency("programme.invalid", DependencyKind.SCIENTIFIC_EVIDENCE, str(error), "programme")
    if all(getattr(inputs, key) is not None for key in ("programme", "reduction", "data")):
        try:
            validate_factorial_inputs(specification, inputs.programme, inputs.reduction, inputs.data)
        except (ValueError, TypeError) as error:
            dependency("original-data.invalid", DependencyKind.SCIENTIFIC_EVIDENCE, str(error), "data")
    sources = tuple((getattr(record, _ID_FIELDS[key]), record) for key in INPUT_TYPES
                    if (record := getattr(inputs, key)) is not None)
    if len({key for key, _ in sources}) != len(sources):
        dependency("original-source-alias", DependencyKind.SCIENTIFIC_EVIDENCE,
            "Distinct original records cannot share a scientific source identity.")
        sources = ()
    return inputs, allocation, dependencies, tuple(sorted(sources))


def prepare_factorial_experiment(specification, *, scientific_inputs, execution,
        protocol_bytes=None, method_inputs=None):
    inputs, allocation, dependencies, sources = _scientific_inputs(specification, scientific_inputs, method_inputs)
    if type(execution) is not ExecutionSelection:
        raise TypeError("factorial preparation requires its separate execution selection")
    execution.__post_init__()
    for key, attribute, kind, detail in (
        ("environment", "environment_id", DependencyKind.ENVIRONMENT, "Select the existing locked Matrix profile."),
        ("source-snapshot", "source_snapshot", DependencyKind.ENVIRONMENT, "Select the actual immutable producing source."),
        ("output-root", "output_root", DependencyKind.STORAGE, "Select explicit guarded output custody."),
    ):
        if getattr(execution, attribute) is None:
            dependencies.append(ExperimentDependency("matrix.e4.factorial."+key, kind, detail))
    if protocol_bytes is not None:
        dependencies.append(ExperimentDependency("matrix.e4.factorial.unselected-protocol", DependencyKind.EXTERNAL_INPUT,
            "The explicit method specification owns this conditional calculation; no protocol override is declared."))
    lowered = None
    if not dependencies:
        lowered = lower_exposed_programme_factorial(specification, inputs.programme, inputs.reduction,
            inputs.data, campaign=inputs.campaign)
    census = ExperimentCensus((("development-groups", MODES["E4_DEVELOPMENT"][1]),),
        (("development-groups", 0 if allocation is None else len(allocation.units)),), (("factorial-assess", 1),),
        tuple(sorted((("assigned-cases", 0 if inputs.programme is None else len(inputs.programme.cases)),
            ("conditional-tests", len(E4_COMPARISONS)), ("family-slots", len(FAMILY_IDS)),
            ("paired-targets-per-case", 30), ("retained-source-rows", 0 if inputs.data is None else len(inputs.data.cases))))), 0)
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)),
        allocation=allocation, draft=None if lowered is None else lowered.draft,
        input_records=() if lowered is None else lowered.input_records, execution=execution,
        design_records=sources if len(sources) == len(INPUT_TYPES) else ())


def validate_factorial_experiment_instance(*, specification, allocation, draft, source_records):
    """Reconstruct the exact selection/source/graph association on retained reads."""
    if (type(source_records) is not tuple
            or tuple(key for key, _ in source_records) != tuple(sorted({key for key, _ in source_records}))):
        raise ValueError("factorial instance requires its unique complete original source census")
    records = {}
    for key, record in source_records:
        matches = tuple(name for name, kind in INPUT_TYPES.items() if type(record) is kind)
        if len(matches) != 1 or matches[0] in records or key != getattr(record, _ID_FIELDS[matches[0]]):
            raise ValueError("factorial instance substitutes or duplicates an original source")
        records[matches[0]] = record
    if set(records) != set(INPUT_TYPES):
        raise ValueError("factorial instance omits an original scientific source")
    resolved = bind_factorial_inputs(specification, records)
    inputs, expected_allocation, dependencies, _ = _scientific_inputs(specification,
        resolved.scientific_inputs, resolved.method_inputs)
    if dependencies or expected_allocation is None:
        raise ValueError("factorial instance changes its declared original scientific sources")
    expected = lower_exposed_programme_factorial(specification, inputs.programme, inputs.reduction,
        inputs.data, campaign=inputs.campaign)
    if allocation != expected_allocation or draft != expected.draft:
        raise ValueError("factorial instance decouples its exact design, allocation or causal graph")
