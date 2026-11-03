# SPDX-License-Identifier: MPL-2.0
"""Declarative E1 facade over the original prospective confirmation owner.

Inputs retain the actual stock scientific root, original sources, qualification,
formal entry and resource selections. This facade derives no permission or proof.
"""
from collections import Counter
from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.experiment_entry import ExperimentEntryPackage
from empirical_lawhood.planning.formal_analysis import FormalGapSourceCapabilityInventory, FormalMethodCatalog
from empirical_lawhood.planning.study_authoring import DesignInputRecord, MaterializationQualificationReceipt, StudyDraft
from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeSpec
from empirical_lawhood.runtime.experiment_preparation import (DependencyKind, ExperimentCensus, ExperimentDependency,
    ExperimentPreparation, PreparedExperimentInputs)
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec, RecursiveProspectiveOperand
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig
from .operation_bindings import BUDGET, confirmation_draft, operation_registrations
from .records import E1HistorySource, identity

PROTOCOL_ID = 'matrix.factor-confirmation.prospective'


@dataclass(frozen=True, slots=True)
class E1ConfirmationSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/experiment-specification'
    specification_id: str
    question: str
    root_ids: tuple[str, ...]
    selection: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (not self.question or type(self.root_ids) is not tuple or not self.root_ids
                or self.root_ids != tuple(sorted(set(self.root_ids)))):
            raise ValueError('E1 specification requires its explicit question and complete ordered root census')
        for root in self.root_ids: validate_stable_id(root)
        if (type(self.selection) is not ObjectIdentity or (self.selection.object_schema,self.selection.object_version)
                != (E1ConfirmationSelection.SCHEMA,E1ConfirmationSelection.VERSION)):
            raise ValueError('E1 specification requires its exact scientific/entry selection')

    @property
    def identity(self): return ObjectIdentity.from_record(self.specification_id,self)


@dataclass(frozen=True, slots=True)
class E1ConfirmationSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/experiment-selection'
    record_id: str
    root: StudyDraft
    sources: tuple[E1HistorySource, ...]
    scalar_definition: MatrixParameterScalarDefinition
    proof_owners: tuple[tuple[str, str], ...]
    task_budgets: tuple[tuple[str, ResourceBudget], ...]
    qualifications: tuple[MaterializationQualificationReceipt, ...]
    known_design_inputs: tuple[DesignInputRecord, ...]
    source_configs: tuple[SourceMaterializationConfig, ...]
    entry_package: ExperimentEntryPackage | None
    formal_methods: FormalMethodCatalog | None
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...]
    resources: ExecutionResourceEnvelopeSpec | None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value,kind in ((self.root,StudyDraft),(self.scalar_definition,MatrixParameterScalarDefinition)):
            if type(value) is not kind: raise TypeError('E1 requires its original exact stock scientific records')
            value.__post_init__()
        if (type(self.sources) is not tuple or not self.sources or any(type(value) is not E1HistorySource for value in self.sources)
                or tuple(value.root_id for value in self.sources) != tuple(sorted({value.root_id for value in self.sources}))):
            raise ValueError('E1 requires its complete sorted original source census')
        for value in self.sources: value.__post_init__()
        for rows in (self.proof_owners,self.task_budgets):
            if type(rows) is not tuple or any(type(row) is not tuple or len(row)!=2 for row in rows):
                raise TypeError('E1 proof/resource selections require immutable exact pairs')
        if self.proof_owners!=tuple(sorted(set(self.proof_owners))) or len({name for name,_ in self.proof_owners})!=len(self.proof_owners):
            raise ValueError('E1 proof obligations require one explicit owner each')
        if tuple(name for name,_ in self.task_budgets)!=tuple(sorted({name for name,_ in self.task_budgets})):
            raise ValueError('E1 resources require one explicit budget per actual task')
        for name,owner in self.proof_owners: validate_stable_id(name);validate_stable_id(owner)
        for name,budget in self.task_budgets:
            validate_stable_id(name)
            if type(budget) is not ResourceBudget or not BUDGET.contains(budget): raise ValueError('E1 task exceeds its installed resource ceiling')
            budget.__post_init__()
        for rows,kind,key in ((self.qualifications,MaterializationQualificationReceipt,'receipt_id'),
                (self.known_design_inputs,DesignInputRecord,'input_id'),
                (self.formal_source_inventories,FormalGapSourceCapabilityInventory,'denominator_id')):
            if (type(rows) is not tuple or any(type(value) is not kind for value in rows)
                    or tuple(getattr(value,key) for value in rows)!=tuple(sorted({getattr(value,key) for value in rows}))):
                raise TypeError('E1 retains exact sorted original qualification/design/formal records')
            for value in rows: value.__post_init__()
        if (type(self.source_configs) is not tuple or any(type(value) is not SourceMaterializationConfig for value in self.source_configs)
                or tuple(value.fingerprint() for value in self.source_configs)!=tuple(sorted({value.fingerprint() for value in self.source_configs}))):
            raise ValueError('E1 source configurations require their canonical SHA roster')
        for value,kind in ((self.entry_package,ExperimentEntryPackage),(self.formal_methods,FormalMethodCatalog),
                           (self.resources,ExecutionResourceEnvelopeSpec)):
            if value is not None:
                if type(value) is not kind: raise TypeError('E1 entry/resources retain their existing typed owner')
                value.__post_init__()

    @property
    def identity(self): return ObjectIdentity.from_record(self.record_id,self)


def bind_inputs(specification,records,*,files=None):
    if set(records)-{'selection'} or files: raise ValueError('E1 accepts only its explicit canonical selection')
    selection=records.get('selection')
    if selection is not None:
        if type(selection) is not E1ConfirmationSelection or selection.identity!=specification.selection:
            raise ValueError('E1 input substitutes its frozen scientific/entry selection')
    return PreparedExperimentInputs({},selection)


def _derive(specification,selection):
    selection.__post_init__()
    if (selection.identity!=specification.selection or tuple(value.root_id for value in selection.sources)!=specification.root_ids
            or selection.root.question!=specification.question):
        raise ValueError('E1 facade changes question, complete roots or original entry selection')
    draft=confirmation_draft(root=selection.root,sources=selection.sources,scalar_definition=selection.scalar_definition,
        proof_owners=selection.proof_owners,draft_id='draft.'+specification.specification_id)
    budgets=dict(selection.task_budgets)
    if set(budgets)!=set(draft.selected_operation_ids): raise ValueError('E1 budgets omit or add an actual confirmation task')
    draft=replace(draft,operations=tuple(replace(value,resource_budget=budgets[value.node_id]) for value in draft.operations))
    records=[selection.scalar_definition]
    for source in selection.sources:
        records.extend((source,source.allocation,source.specification.selection,source.coordinate,source.provenance,*source.root.streams))
    inputs=[]
    for external in draft.external_inputs:
        matches=tuple(value for value in records if value.SCHEMA==external.payload_schema and value.fingerprint()==external.expected_content_sha256)
        if not matches: raise ValueError('E1 derived external lacks its actual original canonical operand')
        if any(value.canonical_bytes()!=matches[0].canonical_bytes() for value in matches): raise ValueError('E1 external aliases conflicting records')
        inputs.append((external.input_id,matches[0]))
    sources=tuple(sorted((identity(value) for value in selection.sources),key=lambda value:value.object_id))
    units=tuple(sorted((IndependentUnit(value.root.root.independent_group_id,identity(value).object_id,
        value.coordinate.family_id,tuple(sorted((value.coordinate.primary_view.view_id,value.coordinate.fine_view.view_id))),False) for value in selection.sources),key=lambda value:value.unit_id))
    allocation=UnitAllocation('allocation.'+specification.specification_id,sources,units,
        tuple(UnitRoleAssignment(value.unit_id,'confirmation') for value in units))
    return draft,allocation,tuple(inputs)


def prepare(specification,*,execution,method_inputs=None,**_kwargs):
    specification.__post_init__()
    counts=(('confirmation',len(specification.root_ids)),)
    if method_inputs is None:
        return ExperimentPreparation(specification.identity,ExperimentCensus(counts,(('confirmation',0),),(),(),0),
            (ExperimentDependency('e1.selection',DependencyKind.EXTERNAL_INPUT,
             'Supply the actual stock StudyDraft, protected sources, scalar definition, explicit proof owners and existing entry/qualification/resource records.','selection'),),
            execution=execution,specification_record=specification)
    if type(method_inputs) is not E1ConfirmationSelection: raise TypeError('E1 requires its registered exact input selection')
    selected=method_inputs
    draft,allocation,inputs=_derive(specification,selected)
    dependencies=[]
    for name,kind in (('workers',DependencyKind.ENVIRONMENT),('environment_id',DependencyKind.ENVIRONMENT),
            ('source_snapshot',DependencyKind.ENVIRONMENT),('output_root',DependencyKind.STORAGE)):
        if getattr(execution,name) is None: dependencies.append(ExperimentDependency('e1.execution.'+name.replace('_','-'),kind,'Select explicit '+name+'.'))
    for name,value,kind in (('entry',selected.entry_package,DependencyKind.SCIENTIFIC_EVIDENCE),
            ('formal-methods',selected.formal_methods,DependencyKind.SCIENTIFIC_EVIDENCE),
            ('formal-sources',selected.formal_source_inventories,DependencyKind.SCIENTIFIC_EVIDENCE),
            ('qualifications',selected.qualifications,DependencyKind.SCIENTIFIC_EVIDENCE),
            ('source-configs',selected.source_configs,DependencyKind.EXTERNAL_INPUT),
            ('resources',selected.resources,DependencyKind.ENVIRONMENT)):
        if not value: dependencies.append(ExperimentDependency('e1.'+name,kind,'Supply the actual existing E1 '+name+' contract.','selection'))
    prospective=None
    if not dependencies:
        if set(value.source_id for value in selected.source_configs)!=set(value.input_id for value in draft.external_inputs):
            raise ValueError('E1 source configuration census differs from actual derived external inputs')
        if {value.task_id for value in selected.resources.task_cells}!=set(draft.selected_operation_ids):
            raise ValueError('E1 envelope task census differs from its complete derived graph')
        if execution.workers!=selected.resources.maximum_parallel_tasks:
            raise ValueError('E1 workers differ from their exact selected resource envelope')
        prospective=RecursiveProspectiveAuthoringSpec('prospective.'+specification.specification_id,draft,
            selected.entry_package,selected.formal_methods,selected.formal_source_inventories,selected.qualifications,
            selected.known_design_inputs,selected.resources,tuple(RecursiveProspectiveOperand(value.logical_artifact_id,
                value.expected_content_sha256,len(record.canonical_bytes()),value.payload_schema,value.media_type,
                value.outcome_access,value.visibility_ceiling) for value,(_,record) in zip(draft.external_inputs,inputs,strict=True)))
    registrations={value.selection.selection_id:value for value in operation_registrations()}
    operations=Counter(value.node_id.rsplit('.',1)[-1] for value in draft.operations)
    outputs=Counter(output.output_id for value in draft.operations for output in registrations[value.selection.selection_id].outputs)
    census=ExperimentCensus(counts,counts,tuple(sorted(operations.items())),tuple(sorted(outputs.items())),
        sum(registrations[value.selection.selection_id].native_effect for value in draft.operations))
    return ExperimentPreparation(specification.identity,census,tuple(sorted(dependencies,key=lambda value:value.code)),
        allocation,draft,inputs,execution,specification,(('selection',selected),),prospective_spec=prospective,
        source_configs=selected.source_configs if prospective is not None else ())


def validate_instance(*,specification,allocation,draft,source_records):
    selected=tuple(value for _,value in source_records if type(value) is E1ConfirmationSelection)
    if len(selected)!=1: raise ValueError('E1 companion must retain exactly its original scientific/entry selection')
    expected,expected_allocation,_=_derive(specification,selected[0])
    if draft!=expected or allocation!=expected_allocation: raise ValueError('E1 companion substitutes original derived graph or independent roots')
