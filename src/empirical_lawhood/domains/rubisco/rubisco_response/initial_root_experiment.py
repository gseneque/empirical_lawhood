# SPDX-License-Identifier: MPL-2.0
"""Copied exposed inputs and code-owned preparation for the initial joint root."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.experiments.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root import calculate_initial_root
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootAnalysisInputs
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import QUESTION, analysis_arguments, analytic_units, nested_views
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_translation import ANALYSIS_INPUT, initial_root_draft
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact

PROTOCOL_ID = 'rubisco-initial-root-experiment-v1'


@dataclass(frozen=True, slots=True)
class InitialRootExperimentSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-experiment-specification'
    specification_id: str
    analysis: ObjectIdentity
    expected_case_ids: tuple[str, ...]
    expected_exposure_groups: tuple[str, ...]
    expected_processing_views: tuple[str, ...]
    question: str = QUESTION
    evidence_scope: str = 'EXPOSED_CONDITIONAL'

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        exact(self.analysis, ObjectIdentity)
        if (self.analysis.object_schema, self.analysis.object_version) != (InitialRootAnalysisInputs.SCHEMA, InitialRootAnalysisInputs.VERSION):
            raise ValueError('initial root experiment changes its exact frozen analysis revision')
        for field in ('expected_case_ids', 'expected_exposure_groups', 'expected_processing_views'):
            require_sorted_unique_strings(getattr(self, field), field_name=field, allow_empty=False)
        if self.question != QUESTION or self.evidence_scope != 'EXPOSED_CONDITIONAL':
            raise ValueError('initial root experiment changes its conditional question or exposed evidence lane')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


def initial_root_experiment_specification(analysis):
    exact(analysis, InitialRootAnalysisInputs)
    return InitialRootExperimentSpecification('specification.rubisco-initial-root.' + analysis.fingerprint(),
        analysis.identity, tuple(row.case_id for row in analysis.model.cases), analytic_units(analysis), nested_views(analysis))


def allocation_for(analysis):
    exact(analysis, InitialRootAnalysisInputs)
    groups = analytic_units(analysis)
    return UnitAllocation('allocation.rubisco-initial-root.' + analysis.fingerprint(), (analysis.identity,),
        tuple(IndependentUnit(group, analysis.identity.object_id, 'family.rubisco.original-exposure',
            tuple(sorted({row.case.parent.processing_view for row in analysis.model.cases if row.case.exposure_group == group})),
            True) for group in groups), tuple(UnitRoleAssignment(group, 'analytical-exposed') for group in groups))


def bind_inputs(specification, records, *, files=None):
    exact(specification, InitialRootExperimentSpecification)
    if set(records) - {'analysis'} or files:
        raise ValueError('initial root experiment accepts only its complete frozen analysis input')
    analysis = records.get('analysis')
    if analysis is not None and initial_root_experiment_specification(analysis) != specification:
        raise ValueError('initial root experiment changes original source, consumer, exposure or complete case census')
    return PreparedExperimentInputs({} if analysis is None else {'analysis': allocation_for(analysis)}, records)


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    exact(execution, ExecutionSelection)
    records = {} if method_inputs is None else method_inputs
    bound = bind_inputs(specification, records)
    if scientific_inputs != bound.scientific_inputs or protocol_bytes is not None:
        raise ValueError('initial root preparation changes its declared allocation or supplies unselected protocol bytes')
    dependencies = []
    if records.get('analysis') is None:
        dependencies.append(ExperimentDependency('rubisco.initial-root.analysis', DependencyKind.EXTERNAL_INPUT,
            'Capture the exact original selection, evidence and source-conditioned reviews through their guarded reader.', 'analysis'))
    for field, kind in (('environment_id', DependencyKind.ENVIRONMENT), ('source_snapshot', DependencyKind.ENVIRONMENT),
            ('output_root', DependencyKind.STORAGE), ('workers', DependencyKind.ENVIRONMENT)):
        if getattr(execution, field) is None:
            dependencies.append(ExperimentDependency('rubisco.initial-root.execution.' + field, kind, 'Select explicit ' + field + '.'))
    analysis = records.get('analysis')
    allocation, draft, inputs = None, None, ()
    limitations = ()
    if analysis is not None:
        result = calculate_initial_root(**analysis_arguments(analysis))
        limitations = tuple(ExperimentDependency(key, DependencyKind.SCIENTIFIC_EVIDENCE,
            'Unresolved original conditional-root input: ' + key + '.') for key in result.decision_requirement_ids)
    if not dependencies:
        allocation = allocation_for(analysis)
        draft = initial_root_draft(analysis, draft_id='draft.rubisco-initial-root.' + specification.fingerprint())
        inputs = ((ANALYSIS_INPUT, analysis),)
    expected = (('analytical-exposure-groups', len(specification.expected_exposure_groups)),
        ('biological-units', 0), ('cases', len(specification.expected_case_ids)),
        ('processing-views', len(specification.expected_processing_views)))
    resolved = tuple((key, value if analysis is not None else 0) for key, value in expected)
    return ExperimentPreparation(specification.identity, ExperimentCensus(expected, resolved,
        (('assessment', 1), ('calculation', 1)), (('canonical-products', 2),), 0),
        tuple(sorted(dependencies, key=lambda row: row.code)), allocation=allocation, draft=draft, input_records=inputs,
        execution=execution, specification_record=specification,
        design_records=() if analysis is None else ((analysis.identity.object_id, analysis),), assessment_limitations=limitations)


def validate_instance(*, specification, allocation, draft, source_records):
    exact(specification, InitialRootExperimentSpecification)
    if len(source_records) != 1 or source_records[0][0] != specification.analysis.object_id:
        raise ValueError('initial root instance changes its complete original source census')
    analysis = source_records[0][1]
    bind_inputs(specification, {'analysis': analysis})
    if (allocation != allocation_for(analysis) or draft != initial_root_draft(analysis,
            draft_id='draft.rubisco-initial-root.' + specification.fingerprint())):
        raise ValueError('initial root instance changes its code-owned source/specification lowering')
