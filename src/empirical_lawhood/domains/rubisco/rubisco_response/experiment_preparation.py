# SPDX-License-Identifier: MPL-2.0
"""Pure copied-input preparation; runtime and access checks stay at entry."""

from collections.abc import Mapping
from dataclasses import dataclass, replace

from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_specification import RubiscoResponseExperimentSpecification, select_response_study
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.operation_bindings import NAMESPACE
from empirical_lawhood.domains.rubisco.rubisco_response.paired_prediction import source_union
from empirical_lawhood.domains.rubisco.rubisco_response.recursive_translation import response_draft
from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy


@dataclass(frozen=True, slots=True)
class ResponseExperimentInputs:
    study: RubiscoResponseStudy | None = None

    def __post_init__(self):
        if self.study is not None:
            exact(self.study, RubiscoResponseStudy)


def bind_response_inputs(specification, records):
    exact(specification, RubiscoResponseExperimentSpecification)
    if not isinstance(records, Mapping) or set(records) - {"study"}:
        raise ValueError("response input binding requires only its declared original study key")
    inputs = ResponseExperimentInputs(**records)
    return PreparedExperimentInputs({} if inputs.study is None else {"study": inputs.study.allocation}, inputs)


def scientific_selection(specification, scientific_inputs, method_inputs):
    exact(specification, RubiscoResponseExperimentSpecification)
    if not isinstance(scientific_inputs, Mapping):
        raise TypeError("response preparation requires its typed source allocations")
    dependencies = []
    def dependency(code, kind, detail):
        dependencies.append(ExperimentDependency("rubisco.response." + code, kind, detail, "study"))
    if set(scientific_inputs) - {"study"}:
        dependency("unknown-allocation", DependencyKind.SCIENTIFIC_EVIDENCE, "Only the exact original study allocation is declared.")
    if method_inputs is None:
        inputs = ResponseExperimentInputs()
    else:
        exact(method_inputs, ResponseExperimentInputs)
        inputs = method_inputs
    selected, allocation = None, None
    if inputs.study is None:
        dependency("study.missing", DependencyKind.EXTERNAL_INPUT, "Supply the actual original study bytes; a selected identity is insufficient.")
    else:
        original = inputs.study
        if original.allocation != scientific_inputs.get("study"):
            dependency("study.allocation", DependencyKind.SCIENTIFIC_EVIDENCE,
                "Preserve original exposure groups and every nested case, scenario and point.")
        try:
            selected = select_response_study(specification, original)
        except ValueError as error:
            dependency("study.selection", DependencyKind.SCIENTIFIC_EVIDENCE, str(error))
        if not dependencies and selected is not None:
            allocation = replace(original.allocation,
                allocation_id="allocation.rubisco-response." + specification.fingerprint(),
                sources=source_union(original.allocation.sources, (original.identity, specification.identity)))
    return inputs, selected, allocation, dependencies


def lower_response(specification, original, selected):
    draft = response_draft(original, selected,
        draft_id="draft.rubisco-response." + specification.fingerprint(),
        permitted_refinement_id=specification.permitted_refinement_id)
    return draft, ((f"external.{NAMESPACE}.study", original),)


def prepare_response_experiment(specification, *, scientific_inputs, execution, protocol_bytes=None, method_inputs=None):
    inputs, selected, allocation, dependencies = scientific_selection(specification, scientific_inputs, method_inputs)
    exact(execution, ExecutionSelection)
    for code, missing, kind, detail in (
        ("environment", execution.environment_id is None, DependencyKind.ENVIRONMENT,
         "Select the locked numerical environment; actual producing provenance is checked at execution."),
        ("source-snapshot", execution.source_snapshot is None, DependencyKind.ENVIRONMENT,
         "Select the actual producing implementation snapshot."),
        ("output-root", execution.output_root is None, DependencyKind.STORAGE,
         "Select explicit guarded output custody."),
        ("single-worker", execution.workers not in {None, 1}, DependencyKind.ENVIRONMENT,
         "This bounded conditional route selects one worker."),
        ("unselected-protocol", protocol_bytes is not None, DependencyKind.EXTERNAL_INPUT,
         "The installed conditional method owns this protocol; no extra protocol file is declared."),
    ):
        if missing:
            dependencies.append(ExperimentDependency("rubisco.response." + code, kind, detail))
    if specification.evidence_scope == "PROSPECTIVE_REQUIRED":
        dependencies.extend((
            ExperimentDependency("rubisco.response.prospective-science", DependencyKind.SCIENTIFIC_EVIDENCE,
                "Bind admitted physical state and rate evidence, actual predictive validation and Gp applicability; exposed controls cannot supply these."),
            ExperimentDependency("rubisco.response.prospective-authority", DependencyKind.AUTHORITY,
                "Bind the actual protected source, approval, issue, execution and reveal prerequisites at their separate boundaries."),
            ExperimentDependency("rubisco.response.prospective-lowering", DependencyKind.SOFTWARE,
                "Select a separate prospective scientific operation binding; this declaration owns exposed conditional computation."),
        ))
    original = inputs.study
    cases = () if original is None else original.cases.cases
    supplies = () if original is None else original.supplies
    scenarios = tuple(row for supply in supplies for row in supply.scenarios)
    points = sum(len(row.points) for row in scenarios)
    roles = (("analytical", len(specification.expected_analytical_unit_ids)), ("biological", 0),
             ("cases", len(specification.expected_case_ids)), ("scenarios", sum(len(ids) for _, ids in specification.expected_scenarios)))
    resolved = (("analytical", len({row.exposure_group for row in cases})), ("biological", 0),
                ("cases", len(cases)), ("scenarios", len(scenarios)))
    census = ExperimentCensus(roles, resolved, (("assess", 1), ("predict", 1)),
        (("assessment-products", 1), ("case-assessments", len(specification.expected_case_ids)),
         ("failed-scenarios", sum(row.original_state == "FAILED" for row in scenarios)),
         ("paired-points", points), ("prediction-products", 1), ("supplied-solver-calls", 2 * points),
         ("unknown-scenarios", sum(row.original_state == "UNKNOWN" for row in scenarios))), 0)
    draft, input_records = (None, ())
    if not dependencies and allocation is not None:
        draft, input_records = lower_response(specification, original, selected)
    limitations = tuple(ExperimentDependency("rubisco.response.limit." + name, DependencyKind.SCIENTIFIC_EVIDENCE, detail)
        for name, detail in (
            ("biological-prediction", "Independent experimental prediction accuracy and Gp applicability remain unestablished."),
            ("computational-benefit", "Prospective service, false admission and complete comparative cost remain unestablished."),
            ("matrix-handoff", "An eligible Matrix programme scientific handoff remains a separate required source."),
            ("physical-admission", "Selected chemical/rate records do not admit molecular state, Hamiltonian or rate validity."),
        ))
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)),
        allocation=allocation, draft=draft, input_records=input_records, execution=execution,
        design_records=() if original is None else ((original.study_id, original),), assessment_limitations=limitations)


def validate_response_instance(*, specification, allocation, draft, source_records):
    exact(specification, RubiscoResponseExperimentSpecification)
    if specification.evidence_scope != "EXPOSED_CONDITIONAL":
        raise ValueError("response instance changes its exposed conditional scientific lane")
    if (type(source_records) is not tuple or len(source_records) != 1
            or source_records[0][0] != specification.study.object_id):
        raise ValueError("response instance changes its exact original source census")
    resolved = bind_response_inputs(specification, {"study": source_records[0][1]})
    inputs, selected, expected_allocation, dependencies = scientific_selection(
        specification, resolved.scientific_inputs, resolved.method_inputs)
    if dependencies or expected_allocation is None:
        raise ValueError("response instance changes original source/scenario/criterion bindings")
    expected_draft, _ = lower_response(specification, inputs.study, selected)
    if expected_allocation != allocation or expected_draft != draft:
        raise ValueError("response instance differs from its owned source/specification lowering")
