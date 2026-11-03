# SPDX-License-Identifier: MPL-2.0
"""Current E1 scientific context and C-backed input-assembly intent.

The context contains mathematical declarations, never an earlier StudyDraft,
source admission, authorization, candidate, or completion receipt. Assembly
rebuilds those operational bindings from the actual published programme C.
"""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.evidence import ClaimSpec
from empirical_lawhood.kernel.experiments import AssignmentSpec, ControlSpec, PrecisionGoal
from empirical_lawhood.kernel.obligations import ScientificObligations
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id,
)
from empirical_lawhood.kernel.systems import SystemSpec
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.planning.experiment_entry import ExperimentEntryPackage
from empirical_lawhood.planning.formal_analysis import FormalGapSourceCapabilityInventory, FormalMethodCatalog
from empirical_lawhood.runtime.execution_envelope import NonTimeResourceBudget, ProgressLivenessContract
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs,
)
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection
from .known_inputs import MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput

PROTOCOL_ID = 'matrix.programme.e1-input-assembly'
RESOURCE_PHASES = ('adjudicate', 'check', 'commit', 'history', 'measure', 'numerical')


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE1ScientificContext(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e1-scientific-context'
    context_id: str
    question: str
    alternative_ids: tuple[str, ...]
    system: SystemSpec
    claims: tuple[ClaimSpec, ...]
    assignment: AssignmentSpec
    measurement_quantity_ids: tuple[str, ...]
    controls: tuple[ControlSpec, ...]
    precision_goals: tuple[PrecisionGoal, ...]
    obligations: ScientificObligations
    observation_operator: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.context_id)
        if not self.question:
            raise ValueError('programme E1 requires its explicit scientific question')
        require_sorted_unique_strings(self.alternative_ids, field_name='alternative_ids', allow_empty=False)
        require_sorted_unique_strings(self.measurement_quantity_ids, field_name='measurement_quantity_ids', allow_empty=False)
        for value, kind in ((self.system, SystemSpec), (self.assignment, AssignmentSpec),
                (self.obligations, ScientificObligations), (self.observation_operator, ObjectIdentity)):
            if type(value) is not kind:
                raise TypeError('programme E1 context requires exact current mathematical records')
            value.__post_init__()
        for values, kind, attribute in ((self.claims, ClaimSpec, 'claim_id'),
                (self.controls, ControlSpec, 'control_id'), (self.precision_goals, PrecisionGoal, 'goal_id')):
            if type(values) is not tuple or not values or any(type(value) is not kind for value in values):
                raise TypeError('programme E1 context requires its complete explicit scientific choices')
            require_sorted_unique_ids(values, attribute=attribute, field_name=attribute)
            for value in values:
                value.__post_init__()
        if self.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR:
            raise ValueError('programme E1 context requires its numerical scientific world')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.context_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE1AssemblySelection(CanonicalRecord):
    VERSION: ClassVar[str] = '2.0.0'
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e1-assembly-selection'
    record_id: str
    scientific_context: MatrixProgrammeE1ScientificContext
    campaign: CampaignSpec
    phase_budgets: tuple[tuple[str, NonTimeResourceBudget], ...]
    resources: ExecutionResourceSelection
    native_progress: ProgressLivenessContract
    entry_package: ExperimentEntryPackage | None
    formal_methods: FormalMethodCatalog | None
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.scientific_context, MatrixProgrammeE1ScientificContext), (self.campaign, CampaignSpec),
                (self.resources, ExecutionResourceSelection), (self.native_progress, ProgressLivenessContract)):
            if type(value) is not kind:
                raise TypeError('programme E1 assembly requires its actual current scientific and operational selections')
            value.__post_init__()
        if (self.resources.task_cells or len(self.resources.child_token_limits) != 1
                or self.resources.child_token_limits[0].retry_token_limit != 0
                or self.resources.roster_capacity_branches or self.resources.predevelopment_jit_signature_census is not None
                or self.resources.jit_graph_signature_manifest is not None):
            raise ValueError('programme E1 requires declarative capacity without task maps, retry or JIT branches')
        policy = self.scientific_context.system.authority_policy
        if (self.campaign.authority_policy != ObjectIdentity.from_record(policy.policy_id, policy)
                or any(right.authority_policy_id != policy.policy_id for right in self.campaign.decision_rights)):
            raise ValueError('programme E1 campaign changes the explicit current authority policy')
        if (type(self.phase_budgets) is not tuple
                or any(type(row) is not tuple or len(row) != 2 for row in self.phase_budgets)
                or tuple(phase for phase, _ in self.phase_budgets) != RESOURCE_PHASES
                or any(type(budget) is not NonTimeResourceBudget for _, budget in self.phase_budgets)):
            raise ValueError('programme E1 requires all six explicit phase budgets')
        for _, budget in self.phase_budgets:
            budget.__post_init__()
        if not any(budget.source_byte_limit > 0 for _, budget in self.phase_budgets):
            raise ValueError('programme E1 requires a positive selected source byte limit for C authentication')
        for value, kind in ((self.entry_package, ExperimentEntryPackage), (self.formal_methods, FormalMethodCatalog)):
            if value is not None:
                if type(value) is not kind:
                    raise TypeError('programme E1 retains only exact current entry/formal records')
                value.__post_init__()
        values = self.formal_source_inventories
        if type(values) is not tuple or any(type(value) is not FormalGapSourceCapabilityInventory for value in values):
            raise TypeError('programme E1 requires explicit current formal source inventories')
        require_sorted_unique_ids(values, attribute='denominator_id', field_name='formal_source_inventories')
        for value in values:
            value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE1AssemblySpecification(CanonicalRecord):
    VERSION: ClassVar[str] = '2.0.0'
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e1-assembly-specification'
    specification_id: str
    selection: ObjectIdentity
    input_commitments: MatrixProgrammePublishedInput

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (type(self.selection) is not ObjectIdentity or (self.selection.object_schema, self.selection.object_version)
                != (MatrixProgrammeE1AssemblySelection.SCHEMA, MatrixProgrammeE1AssemblySelection.VERSION)):
            raise ValueError('programme E1 assembly substitutes the exact current selection')
        self.selection.__post_init__()
        if type(self.input_commitments) is not MatrixProgrammePublishedInput:
            raise TypeError('programme assembly requires its actual programme commitment')
        self.input_commitments.__post_init__()
        self.input_commitments.require_kind(MatrixProgrammeInputCommitments)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


def bind_inputs(specification, records, *, files=None):
    if type(specification) is not MatrixProgrammeE1AssemblySpecification:
        raise TypeError('programme E1 assembly requires its exact current specification')
    specification.__post_init__()
    if files or set(records) - {'selection'}:
        raise ValueError('programme E1 assembly accepts only its current explicit selection')
    selected = records.get('selection')
    if selected is not None:
        if type(selected) is not MatrixProgrammeE1AssemblySelection or selected.identity != specification.selection:
            raise ValueError('programme E1 assembly changes its frozen selection')
        selected.__post_init__()
    return PreparedExperimentInputs({}, selected)


def prepare(specification, *, execution, method_inputs=None, **_kwargs):
    specification.__post_init__()
    dependencies = []
    for name, kind in (('workers', DependencyKind.ENVIRONMENT), ('environment_id', DependencyKind.ENVIRONMENT),
            ('source_snapshot', DependencyKind.ENVIRONMENT), ('output_root', DependencyKind.STORAGE)):
        if getattr(execution, name) is None:
            dependencies.append(ExperimentDependency('programme-e1.execution.' + name.replace('_', '-'), kind,
                'Select explicit ' + name + '.'))
    if method_inputs is None:
        dependencies.append(ExperimentDependency('programme-e1.selection', DependencyKind.EXTERNAL_INPUT,
            'Supply the compact scientific context and explicit current operational selections.', 'selection'))
    else:
        bind_inputs(specification, {'selection': method_inputs})
        if execution.workers != method_inputs.resources.maximum_parallel_tasks:
            dependencies.append(ExperimentDependency('programme-e1.worker-selection', DependencyKind.ENVIRONMENT,
                'Assembly and E1 must retain the same explicit worker count.'))
        dependencies.append(ExperimentDependency('programme-e1.derive', DependencyKind.EXTERNAL_INPUT,
            'Use experiment-derive-inputs to authenticate C and assemble the ordinary compact E1 inputs.'))
    return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0),
        tuple(sorted(dependencies, key=lambda value: value.code)), execution=execution, specification_record=specification)
