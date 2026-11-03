# SPDX-License-Identifier: MPL-2.0
"""Same registered experiment seam for retained E5/E6 scientific assessments."""

from collections.abc import Mapping
from dataclasses import dataclass

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentPreparation,
    PreparedExperimentInputs,
)

from .operation_bindings import lower_later_experiment
from .records import MatrixFrozenConsumerPackage, MatrixLaterExperimentSpecification, MatrixProgrammeEvidence, MatrixProgrammeRoster
from .science import MatrixPreparationNomination, source_allocation
from .selection_metadata import validate_later_selection


INPUT_TYPES = {"roster": MatrixProgrammeRoster, "package": MatrixFrozenConsumerPackage,
    "evidence": MatrixProgrammeEvidence, "campaign": CampaignSpec, "nomination": MatrixPreparationNomination}
ID_FIELDS = {"roster": "roster_id", "package": "package_id", "evidence": "bank_id", "campaign": "campaign_id", "nomination": "result_id"}


@dataclass(frozen=True, slots=True)
class MatrixLaterInputs:
    roster: MatrixProgrammeRoster | None = None
    package: MatrixFrozenConsumerPackage | None = None
    evidence: MatrixProgrammeEvidence | None = None
    campaign: CampaignSpec | None = None
    nomination: MatrixPreparationNomination | None = None

    def __post_init__(self):
        for key, kind in INPUT_TYPES.items():
            value = getattr(self, key)
            if value is not None:
                if type(value) is not kind:
                    raise TypeError("later Matrix input " + key + " has the wrong closed original record type")
                value.__post_init__()


def input_record_types():
    return tuple(INPUT_TYPES.values())


def bind_later_inputs(specification, records):
    if type(specification) is not MatrixLaterExperimentSpecification:
        raise TypeError("later Matrix binding needs its exact phase specification")
    specification.__post_init__()
    if not isinstance(records, Mapping) or set(records) - set(INPUT_TYPES):
        raise ValueError("later Matrix binding includes an undeclared original input key")
    inputs = MatrixLaterInputs(**records)
    allocations = {} if inputs.roster is None else {"roster": source_allocation(specification, inputs.roster)}
    return PreparedExperimentInputs(allocations, inputs)


def scientific_selection(specification, scientific_inputs, method_inputs):
    if type(specification) is not MatrixLaterExperimentSpecification:
        raise TypeError("later Matrix preparation needs its exact phase specification")
    specification.__post_init__()
    if not isinstance(scientific_inputs, Mapping):
        raise TypeError("later Matrix preparation needs its original allocation mapping")
    inputs = MatrixLaterInputs() if method_inputs is None else method_inputs
    if type(inputs) is not MatrixLaterInputs:
        raise TypeError("later Matrix preparation needs its typed original input handle")
    inputs.__post_init__()
    dependencies = []

    def dependency(code, kind, detail, source_key=None):
        dependencies.append(ExperimentDependency("matrix.later." + code, kind, detail, source_key))

    if set(scientific_inputs) - {"roster"}:
        dependency("unknown-allocation", DependencyKind.EXTERNAL_INPUT, "Select only the actual original source roster allocation.")
    required = tuple(key for key in INPUT_TYPES if key != "nomination" or specification.phase == "E5_CONFIRMATION")
    for key in required:
        record = getattr(inputs, key)
        if record is None:
            dependency(key + ".missing", DependencyKind.EXTERNAL_INPUT,
                "Supply the actual original " + key + " record; a phase selection creates no source, recipe or observation.", key)
        elif ObjectIdentity.from_record(getattr(record, ID_FIELDS[key]), record) != getattr(specification, key):
            dependency(key + ".identity", DependencyKind.SCIENTIFIC_EVIDENCE,
                "The original " + key + " differs from its exact frozen selection.", key)
    if inputs.nomination is not None and specification.phase != "E5_CONFIRMATION":
        dependency("unselected-nomination", DependencyKind.EXTERNAL_INPUT,
            "Opportunity and transfer outcomes cannot import a later recipe-selection result.", "nomination")
    allocation = None
    if inputs.roster is not None:
        allocation = source_allocation(specification, inputs.roster)
        if scientific_inputs.get("roster") != allocation:
            dependency("allocation", DependencyKind.SCIENTIFIC_EVIDENCE,
                "Retain the exact original whole-group roster; arms, views and regimes create no extra units.", "roster")
    if all(getattr(inputs, key) is not None for key in required):
        try:
            validate_later_selection(specification, inputs.roster, inputs.package, inputs.evidence, inputs.nomination)
        except (ValueError, TypeError) as error:
            dependency("scientific-join", DependencyKind.SCIENTIFIC_EVIDENCE, str(error))
    return inputs, allocation, dependencies


def prepare_later_experiment(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    inputs, allocation, dependencies = scientific_selection(specification, scientific_inputs, method_inputs)
    if type(execution) is not ExecutionSelection:
        raise TypeError("later Matrix requires its separate operational source/environment/custody selection")
    execution.__post_init__()
    for key, attribute, kind in (("environment", "environment_id", DependencyKind.ENVIRONMENT),
            ("source-snapshot", "source_snapshot", DependencyKind.ENVIRONMENT), ("output-root", "output_root", DependencyKind.STORAGE)):
        if getattr(execution, attribute) is None:
            dependencies.append(ExperimentDependency("matrix.later." + key, kind,
                "Select the existing actual " + key + " before authoring or execution; no dependencies are synchronized."))
    if protocol_bytes is not None:
        dependencies.append(ExperimentDependency("matrix.later.unselected-protocol", DependencyKind.EXTERNAL_INPUT,
            "The explicit frozen criterion and original source records own this phase; no protocol override is selected."))
    if specification.mode == "ACQUIRE_AND_ASSESS":
        dependencies.append(ExperimentDependency('matrix.later.software.saved-route-native-lowering', DependencyKind.SOFTWARE,
            'This protocol supports RETAINED_CONDITIONAL_ASSESSMENT only; native acquisition is unsupported.'))
        dependencies.extend((ExperimentDependency("matrix.later.actual-scientific-entry", DependencyKind.SCIENTIFIC_EVIDENCE,
            "Actual eligible whole-regime/source evidence, pre-fit reservation custody, independently supported numerical scope and original frozen package remain scientific entry predicates."),
            ExperimentDependency("matrix.later.actual-authority", DependencyKind.AUTHORITY,
                "Scientific acquisition and protected outcomes require their genuine source/issue/execution/reveal acts; this retained conditional calculation supplies none.")))
    lowered = None
    if not dependencies and allocation is not None:
        lowered = lower_later_experiment(specification, inputs.roster, inputs.package, inputs.evidence,
            allocation=allocation, campaign=inputs.campaign, nomination=inputs.nomination)
    groups = specification.expected_groups * (2 if specification.phase == "E6_TRANSFER" else 1)
    actual_cases = 0 if inputs.roster is None else len(inputs.roster.cases)
    census = ExperimentCensus((("assigned-groups", groups),),
        (("assigned-groups", 0 if allocation is None else len(allocation.units)),),
        (("conditional-functional-assessment", 1),),
        (("assigned-cases", groups * len(specification.arm_ids)), ("original-cases-resolved", actual_cases),
            ("primary-family-slots", len(specification.criterion.family_slots)), ("scientific-products", 1)), 0)
    design = tuple(sorted((getattr(getattr(inputs, key), ID_FIELDS[key]), getattr(inputs, key))
        for key in INPUT_TYPES if getattr(inputs, key) is not None))
    if len({key for key, _ in design}) != len(design):
        raise ValueError("later Matrix original design records alias different source identities")
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)),
        allocation=allocation, draft=None if lowered is None else lowered.draft,
        input_records=() if lowered is None else lowered.input_records, execution=execution,
        specification_record=specification, design_records=design,
        assessment_limitations=(ExperimentDependency('matrix.later.saved-assessment-route', DependencyKind.SCIENTIFIC_EVIDENCE,
            'RETAINED_CONDITIONAL_ASSESSMENT establishes no native acquisition, freshness, source qualification, '
            'issue or reveal authority.'),))


def validate_later_instance(*, specification, allocation, draft, source_records):
    if (type(source_records) is not tuple or tuple(key for key, _ in source_records) != tuple(sorted({key for key, _ in source_records}))):
        raise ValueError("later instance changes its original source-record census")
    records = {}
    for key, record in source_records:
        names = tuple(name for name, kind in INPUT_TYPES.items() if type(record) is kind)
        if len(names) != 1 or names[0] in records or key != getattr(record, ID_FIELDS[names[0]]):
            raise ValueError("later instance substitutes or aliases an original scientific record")
        records[names[0]] = record
    resolved = bind_later_inputs(specification, records)
    inputs, actual_allocation, dependencies = scientific_selection(specification, resolved.scientific_inputs, resolved.method_inputs)
    if dependencies or actual_allocation is None or specification.mode != "RETAINED_CONDITIONAL_ASSESSMENT":
        raise ValueError("later instance has an incomplete original source/selection join")
    expected = lower_later_experiment(specification, inputs.roster, inputs.package, inputs.evidence,
        allocation=actual_allocation, campaign=inputs.campaign, nomination=inputs.nomination)
    if allocation != actual_allocation or draft != expected.draft:
        raise ValueError("later instance differs from its exact derived original phase/specification/whole-group graph")
