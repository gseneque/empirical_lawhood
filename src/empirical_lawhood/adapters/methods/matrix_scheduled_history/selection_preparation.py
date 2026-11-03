# SPDX-License-Identifier: MPL-2.0
"""Public preparation of the bounded, exposed E4 revision checkpoint.

This route selects no trigger, tuning, split or scientific margin for the
researcher. It lowers their explicit selection over the original development
programme. Later calibration and confirmation retain separate frozen inputs.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency,
    ExperimentPreparation, PreparedExperimentInputs,
)

from .programme_records import ScheduledProgramme
from .programme_reduction import ScheduledProgrammeReduction
from .programme_selection import (
    ScheduledRevisionDataBank, _validate_data,
    lower_exposed_programme_selection, programme_selection_allocation,
)
from .selection_specification import ScheduledRevisionExperimentSpecification, derive_revision_specification

PROTOCOL_ID = "matrix.e4.exposed-declared-revision"
INPUT_TYPES = {"campaign": CampaignSpec, "programme": ScheduledProgramme,
    "reduction": ScheduledProgrammeReduction, "data": ScheduledRevisionDataBank}
_ID_FIELDS = {"campaign": "campaign_id", "programme": "programme_id",
    "reduction": "reduction_id", "data": "bank_id"}


@dataclass(frozen=True, slots=True)
class ProgrammeSelectionInputs:
    campaign: CampaignSpec | None = None
    programme: ScheduledProgramme | None = None
    reduction: ScheduledProgrammeReduction | None = None
    data: ScheduledRevisionDataBank | None = None

    def __post_init__(self):
        for key, kind in INPUT_TYPES.items():
            record = getattr(self, key)
            if record is not None:
                if type(record) is not kind:
                    raise TypeError("E4 selection input " + key + " has the wrong closed type")
                record.__post_init__()


def bind_selection_inputs(specification, records):
    if type(specification) is not ScheduledRevisionExperimentSpecification:
        raise TypeError("E4 preparation requires its exact declared selection specification")
    specification.__post_init__()
    return bind_programme_inputs(records)


def bind_programme_inputs(records):
    """Bind the same original four records for development programme methods."""
    if not isinstance(records, Mapping) or set(records) - set(INPUT_TYPES):
        raise ValueError("E4 selection accepts only its four declared original input keys")
    inputs = ProgrammeSelectionInputs(**records)
    allocation = {} if inputs.programme is None else {
        "development": programme_selection_allocation(inputs.programme)}
    return PreparedExperimentInputs(allocation, inputs)


def _scientific_selection(specification, scientific_inputs, method_inputs):
    if type(specification) is not ScheduledRevisionExperimentSpecification:
        raise TypeError("E4 preparation requires its exact declared selection specification")
    specification.__post_init__()
    if not isinstance(scientific_inputs, Mapping):
        raise TypeError("E4 preparation requires its typed original allocation mapping")
    dependencies = []

    def dependency(code, kind, detail, source_key=None):
        dependencies.append(ExperimentDependency("matrix.e4.selection." + code, kind, detail, source_key))

    if set(scientific_inputs) - {"development"}:
        dependency("unknown-allocation", DependencyKind.EXTERNAL_INPUT,
            "Only the original whole-group development allocation is supported here.")
    if method_inputs is None:
        inputs = ProgrammeSelectionInputs()
    elif type(method_inputs) is ProgrammeSelectionInputs:
        inputs = method_inputs
        inputs.__post_init__()
    else:
        dependency("method-inputs", DependencyKind.EXTERNAL_INPUT,
            "Supply the typed original campaign, programme, reduction and paired data bank.")
        inputs = ProgrammeSelectionInputs()
    for key in INPUT_TYPES:
        if getattr(inputs, key) is None:
            dependency(key + ".missing", DependencyKind.EXTERNAL_INPUT,
                "Supply the actual complete original " + key + " record; a specification invents no observations.", key)
    allocation, method_specification = None, None
    if inputs.programme is not None:
        try:
            allocation = programme_selection_allocation(inputs.programme)
            if scientific_inputs.get("development") != allocation:
                dependency("allocation", DependencyKind.SCIENTIFIC_EVIDENCE,
                    "Retain the exact original whole-group allocation; nested cases and paired views create no extra units.", "programme")
            method_specification = derive_revision_specification(specification, inputs.programme)
            method_specification.validate_programme(inputs.programme)
        except (ValueError, TypeError) as error:
            dependency("programme.invalid", DependencyKind.SCIENTIFIC_EVIDENCE, str(error), "programme")
    if (method_specification is not None and all(getattr(inputs, key) is not None
            for key in ("programme", "reduction", "data"))):
        try:
            _validate_data(method_specification, inputs.programme, inputs.reduction, inputs.data)
        except (ValueError, TypeError) as error:
            dependency("original-data.invalid", DependencyKind.SCIENTIFIC_EVIDENCE, str(error), "data")
    if all(getattr(inputs, key) is not None for key in INPUT_TYPES):
        try:
            identities = tuple(ObjectIdentity.from_record(getattr(getattr(inputs, key), _ID_FIELDS[key]),
                getattr(inputs, key)) for key in INPUT_TYPES)
            if len({row.object_id for row in identities}) != len(identities):
                raise ValueError("E4 original scientific records alias different source identities")
        except (ValueError, TypeError) as error:
            dependency("original-source-alias", DependencyKind.SCIENTIFIC_EVIDENCE, str(error))
    return inputs, allocation, dependencies, method_specification


def prepare_selection_experiment(specification, *, scientific_inputs, execution,
                                 protocol_bytes=None, method_inputs=None):
    inputs, allocation, dependencies, method_specification = _scientific_selection(specification, scientific_inputs, method_inputs)
    if type(execution) is not ExecutionSelection:
        raise TypeError("E4 selection requires its separate typed execution selection")
    execution.__post_init__()
    for key, attribute, kind, detail in (
        ("environment", "environment_id", DependencyKind.ENVIRONMENT, "Select the existing locked Matrix profile; no environment is synchronized."),
        ("source-snapshot", "source_snapshot", DependencyKind.ENVIRONMENT, "Select the actual producing implementation snapshot before authoring."),
        ("output-root", "output_root", DependencyKind.STORAGE, "Select explicit guarded custody before authoring."),
    ):
        if getattr(execution, attribute) is None:
            dependencies.append(ExperimentDependency("matrix.e4.selection." + key, kind, detail))
    if protocol_bytes is not None:
        dependencies.append(ExperimentDependency("matrix.e4.selection.unselected-protocol", DependencyKind.EXTERNAL_INPUT,
            "The original programme and explicit selection own this checkpoint; no additional protocol-file override is declared."))
    lowered = None
    if not dependencies and allocation is not None:
        lowered = lower_exposed_programme_selection(method_specification, inputs.programme,
            inputs.reduction, inputs.data, campaign=inputs.campaign)
    groups = len(specification.folds)
    # Fold rows name whole independent units. Each group's nine settings and
    # both numerical views remain nested observations of that same unit.
    actual_groups = 0 if allocation is None else len(allocation.units)
    census = ExperimentCensus((("development-groups", groups),),
        (("development-groups", actual_groups),), (("freeze-revision", 1), ("select-revision", 1)),
        tuple(sorted((("assigned-cases", 0 if inputs.programme is None else len(inputs.programme.cases)),
            ("paired-targets-per-case", 30), ("permitted-final-models", 2),
            ("reserved-candidate-fold-fits", 2 * specification.maximum_fit_calls)))), 0)
    design_records = ()
    if (all(getattr(inputs, key) is not None for key in INPUT_TYPES)
            and len({getattr(getattr(inputs, key), _ID_FIELDS[key]) for key in INPUT_TYPES}) == len(INPUT_TYPES)):
        design_records = tuple(sorted((getattr(getattr(inputs, key), _ID_FIELDS[key]), getattr(inputs, key))
            for key in INPUT_TYPES))
    return ExperimentPreparation(specification.identity, census,
        tuple(sorted(dependencies, key=lambda row: row.code)), allocation=allocation,
        draft=None if lowered is None else lowered.draft,
        input_records=() if lowered is None else lowered.input_records,
        execution=execution, design_records=design_records)


def validate_selection_experiment_instance(*, specification, allocation, draft, source_records):
    """Reconstruct the exact source/specification association, without execution."""
    if (type(source_records) is not tuple
            or tuple(key for key, _ in source_records) != tuple(sorted({key for key, _ in source_records}))):
        raise ValueError("E4 instance requires its complete unique original source-record census")
    by_type = {}
    for key, record in source_records:
        matches = tuple(name for name, kind in INPUT_TYPES.items() if type(record) is kind)
        if len(matches) != 1 or matches[0] in by_type or key != getattr(record, _ID_FIELDS[matches[0]]):
            raise ValueError("E4 instance substitutes or duplicates an original scientific source")
        by_type[matches[0]] = record
    if set(by_type) != set(INPUT_TYPES):
        raise ValueError("E4 instance omits an original scientific source")
    resolved = bind_selection_inputs(specification, by_type)
    inputs, expected_allocation, dependencies, method_specification = _scientific_selection(specification,
        resolved.scientific_inputs, resolved.method_inputs)
    if dependencies or expected_allocation is None:
        raise ValueError("E4 instance changes its declared original scientific sources")
    expected = lower_exposed_programme_selection(method_specification, inputs.programme, inputs.reduction,
        inputs.data, campaign=inputs.campaign)
    if allocation != expected_allocation or draft != expected.draft:
        raise ValueError("E4 instance decouples its exact selection, allocation, programme or causal graph")
