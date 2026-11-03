# SPDX-License-Identifier: MPL-2.0
"""Declarative E1 facade over the original prospective confirmation owner.

Inputs retain the actual stock scientific root, original sources, qualification,
formal entry and resource selections. This facade derives no permission or proof.
"""
from collections import Counter
from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.experiment_entry import ExperimentEntryPackage
from empirical_lawhood.planning.formal_analysis import FormalGapSourceCapabilityInventory, FormalMethodCatalog
from empirical_lawhood.planning.study_authoring import DesignInputRecord, MaterializationQualificationReceipt, StudyDraft
from empirical_lawhood.runtime.execution_envelope import (ChildResourceTokenLimit, ExecutionResourceEnvelopeSpec,
    ExecutionResourceTaskCellSpec, NonTimeResourceBudget, ProgressLivenessContract)
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection
from empirical_lawhood.runtime.experiment_preparation import (DependencyKind, ExperimentCensus, ExperimentDependency,
    ExperimentPreparation, PreparedExperimentInputs)
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec, RecursiveProspectiveDesignInputs, RecursiveProspectiveOperand
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig
from . import compact_bindings as owner
from .compact_bindings import BUDGET,confirmation_draft,operation_registrations
from .compact_records import E1CompactManifest,sources_for_manifest,identity

PROTOCOL_ID = 'matrix.factor-confirmation.compact-prospective'
RESOURCE_BINDING_DEPENDENCY = 'e1.compact-resource-projection'
RESOURCE_PHASES = ('adjudicate','check','commit','history','measure','numerical')


@dataclass(frozen=True, slots=True)
class E1CompactExperimentSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-experiment-specification'
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
                not in tuple((kind.SCHEMA,kind.VERSION) for kind in selection_types())):
            raise ValueError('E1 specification requires its exact scientific/entry selection')

    @property
    def identity(self): return ObjectIdentity.from_record(self.specification_id,self)


@dataclass(frozen=True, slots=True)
class E1CompactExperimentSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-experiment-selection'
    record_id: str
    root: StudyDraft
    manifest: E1CompactManifest
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
        for value,kind in ((self.root,StudyDraft),(self.manifest,E1CompactManifest)):
            if type(value) is not kind: raise TypeError('E1 requires its original exact stock scientific records')
            value.__post_init__()
        for rows in (self.proof_owners,self.task_budgets):
            if type(rows) is not tuple or any(type(row) is not tuple or len(row)!=2 for row in rows):
                raise TypeError('E1 proof/resource selections require immutable exact pairs')
        if self.proof_owners!=tuple(sorted(set(self.proof_owners))) or len({name for name,_ in self.proof_owners})!=len(self.proof_owners):
            raise ValueError('E1 proof obligations require one explicit owner each')
        if tuple(name for name,_ in self.task_budgets)!=tuple(sorted({name for name,_ in self.task_budgets})):
            raise ValueError('E1 resources require one explicit budget per actual task')
        for name,proof_owner in self.proof_owners: validate_stable_id(name);validate_stable_id(proof_owner)
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


@dataclass(frozen=True, slots=True)
class E1CompactExperimentSelectionV2(CanonicalRecord):
    """Scientific operands and six finite phase budgets, without task/proof maps."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/compact-declarative-selection'
    record_id: str
    root: StudyDraft
    manifest: E1CompactManifest
    phase_budgets: tuple[tuple[str, NonTimeResourceBudget], ...]
    resources: ExecutionResourceSelection
    native_progress: ProgressLivenessContract
    qualifications: tuple[MaterializationQualificationReceipt, ...]
    known_design_inputs: tuple[DesignInputRecord, ...]
    source_configs: tuple[SourceMaterializationConfig, ...]
    entry_package: ExperimentEntryPackage | None
    formal_methods: FormalMethodCatalog | None
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value,kind in ((self.root,StudyDraft),(self.manifest,E1CompactManifest),
                (self.resources,ExecutionResourceSelection),(self.native_progress,ProgressLivenessContract)):
            if type(value) is not kind:raise TypeError('compact E1 declarative selection changes an exact shared operand')
            value.__post_init__()
        if (type(self.phase_budgets) is not tuple or any(type(row) is not tuple or len(row)!=2 for row in self.phase_budgets)
                or tuple(phase for phase,_ in self.phase_budgets)!=RESOURCE_PHASES
                or any(type(budget) is not NonTimeResourceBudget for _,budget in self.phase_budgets)):
            raise ValueError('compact E1 requires its complete six finite phase-wide budgets')
        for _,budget in self.phase_budgets:
            budget.__post_init__()
            if not BUDGET.contains(_operation_budget(budget)):raise ValueError('compact E1 phase exceeds its installed resource ceiling')
        if self.root.system is None or self.root.experiment is None or self.root.campaign is None:
            raise ValueError('compact E1 requires its actual complete stock scientific root')
        controls=self.resources
        if (controls.task_cells or len(controls.child_token_limits)!=1 or controls.roster_capacity_branches
                or controls.predevelopment_jit_signature_census is not None or controls.jit_graph_signature_manifest is not None
                or controls.child_token_limits[0].retry_token_limit!=0):
            raise ValueError('compact E1 uses empty task cells, one explicit capacity and no retry/JIT/branch roster')
        for rows,kind,key in ((self.qualifications,MaterializationQualificationReceipt,'receipt_id'),
                (self.known_design_inputs,DesignInputRecord,'input_id'),
                (self.formal_source_inventories,FormalGapSourceCapabilityInventory,'denominator_id')):
            if (type(rows) is not tuple or any(type(value) is not kind for value in rows)
                    or tuple(getattr(value,key) for value in rows)!=tuple(sorted({getattr(value,key) for value in rows}))):
                raise TypeError('compact E1 retains exact sorted qualification/design/formal records')
            for value in rows:value.__post_init__()
        if (type(self.source_configs) is not tuple or any(type(value) is not SourceMaterializationConfig for value in self.source_configs)
                or tuple(value.fingerprint() for value in self.source_configs)!=tuple(sorted({value.fingerprint() for value in self.source_configs}))):
            raise ValueError('compact E1 source configurations require their exact canonical SHA roster')
        for value,kind in ((self.entry_package,ExperimentEntryPackage),(self.formal_methods,FormalMethodCatalog)):
            if value is not None:
                if type(value) is not kind:raise TypeError('compact E1 retains its actual entry/formal owners')
                value.__post_init__()

    @property
    def identity(self):return ObjectIdentity.from_record(self.record_id,self)


def selection_types():return E1CompactExperimentSelection,E1CompactExperimentSelectionV2


def _operation_budget(budget):
    return ResourceBudget(budget.cpu_cores,budget.memory_bytes,0,None,budget.source_byte_limit,budget.output_bytes)


def selection_proof_owners(selection,sources=None):
    if type(selection) is E1CompactExperimentSelection:return selection.proof_owners
    from empirical_lawhood.runtime.candidate_compiler import _required_obligation_ids
    if type(selection) is not E1CompactExperimentSelectionV2:raise TypeError('compact E1 requires an exact installed selection edition')
    sources=sources_for_manifest(selection.manifest) if sources is None else sources
    root=selection.root
    if root.experiment is None:raise ValueError('compact E1 requires its actual root scientific obligation contract')
    terminal=owner.E1CompactAdjudicationConfig('config.'+owner.KEY,sources[0].manifest,
        selection.manifest.specification.selection.criterion,sources)
    cutoffs=owner.cutoffs(terminal)
    if root.experiment.information_cutoffs!=cutoffs:
        raise ValueError('compact E1 root omits or changes an exact selected causal cutoff')
    history={cutoff.cutoff_id:owner.NAMESPACE+'.'+source.root_id+'.history'
        for cutoff,source in zip(cutoffs,sources,strict=True)}
    nodes=(owner.COMMIT_KEY,owner.KEY,*(owner.NAMESPACE+'.'+source.root_id+'.'+phase
        for source in sources for phase in ('history','numerical','measure','check')))
    required=_required_obligation_ids(root.experiment)
    result=[(obligation,history.get(obligation,owner.KEY)) for obligation in required]
    generated=tuple(('obligation.'+node+'.complete-selected-scope',node) for node in nodes)
    if set(required)&{obligation for obligation,_ in generated}:raise ValueError('compact E1 root aliases a generated operation obligation')
    return tuple(sorted((*result,*generated)))


def selection_task_budgets(selection,sources=None):
    if type(selection) is E1CompactExperimentSelection:return selection.task_budgets
    if type(selection) is not E1CompactExperimentSelectionV2:raise TypeError('compact E1 requires an exact installed selection edition')
    sources=sources_for_manifest(selection.manifest) if sources is None else sources
    budgets=dict(selection.phase_budgets)
    result=[(owner.COMMIT_KEY,_operation_budget(budgets['commit'])),(owner.KEY,_operation_budget(budgets['adjudicate']))]
    result.extend((owner.NAMESPACE+'.'+source.root_id+'.'+phase,_operation_budget(budgets[phase]))
        for source in sources for phase in ('history','numerical','measure','check'))
    return tuple(sorted(result))


def bind_inputs(specification,records,*,files=None):
    if set(records)-{'selection'} or files: raise ValueError('E1 accepts only its explicit canonical selection')
    selection=records.get('selection')
    if selection is not None:
        if type(selection) not in selection_types() or selection.identity!=specification.selection:
            raise ValueError('E1 input substitutes its frozen scientific/entry selection')
    return PreparedExperimentInputs({},selection)


def _derive(specification,selection):
    selection.__post_init__()
    sources=sources_for_manifest(selection.manifest)
    if (selection.identity!=specification.selection or tuple(value.root_id for value in sources)!=specification.root_ids
            or selection.root.question!=specification.question):
        raise ValueError('E1 facade changes question, complete roots or original entry selection')
    draft=confirmation_draft(root=selection.root,manifest=selection.manifest,
        proof_owners=selection_proof_owners(selection,sources),draft_id='draft.'+specification.specification_id)
    budgets=dict(selection_task_budgets(selection,sources))
    if set(budgets)!=set(draft.selected_operation_ids): raise ValueError('E1 budgets omit or add an actual confirmation task')
    draft=replace(draft,operations=tuple(replace(value,resource_budget=budgets[value.node_id]) for value in draft.operations))
    records=[selection.manifest,selection.manifest.scalar_definition,selection.manifest.provenance]
    for source in sources:records.extend((source,source.coordinate,*source.root.streams))
    by_content={}
    for record in records:
        key=record.SCHEMA,record.fingerprint()
        previous=by_content.setdefault(key,record)
        if previous is not record and previous.canonical_bytes()!=record.canonical_bytes():raise ValueError('compact E1 external aliases conflicting canonical records')
    inputs=[]
    for external in draft.external_inputs:
        record=by_content.get((external.payload_schema,external.expected_content_sha256))
        if record is None:raise ValueError('compact E1 derived external lacks its actual exact canonical operand')
        inputs.append((external.input_id,record))
    if type(selection) is E1CompactExperimentSelectionV2:
        # The actual metadata-access owner needs exact physical byte bounds.
        # Derive them from these already matched canonical operands, preserving
        # the historical V1 lowering and every original scientific identity.
        sizes={name:len(record.canonical_bytes()) for name,record in inputs}
        draft=replace(draft,external_inputs=tuple(replace(value,maximum_size_bytes=sizes[value.input_id])
            for value in draft.external_inputs))
    return draft,population_allocation(specification,sources),tuple(inputs)


def population_allocation(specification,sources):
    source_pins=tuple(sorted((identity(value) for value in sources),key=lambda value:value.object_id))
    units=tuple(sorted((IndependentUnit(value.root.root.independent_group_id,identity(value).object_id,
        value.coordinate.family_id,tuple(sorted((value.coordinate.primary_view.view_id,value.coordinate.fine_view.view_id))),False) for value in sources),key=lambda value:value.unit_id))
    allocation=UnitAllocation('allocation.'+specification.specification_id,source_pins,units,
        tuple(UnitRoleAssignment(value.unit_id,'confirmation') for value in units))
    return allocation


def prepare(specification,*,execution,method_inputs=None,**_kwargs):
    specification.__post_init__()
    counts=(('confirmation',len(specification.root_ids)),)
    if method_inputs is None:
        return ExperimentPreparation(specification.identity,ExperimentCensus(counts,(('confirmation',0),),(),(),0),
            (ExperimentDependency('e1.compact-selection',DependencyKind.EXTERNAL_INPUT,
             'Supply the actual stock StudyDraft, shared compact manifest, explicit proof owners and existing entry/qualification/resource records.','selection'),),
            execution=execution,specification_record=specification)
    if type(method_inputs) not in selection_types(): raise TypeError('E1 requires its registered exact input selection')
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
    if type(selected) is E1CompactExperimentSelectionV2:
        resolved=derive_resource_selection(selected,draft)
        if selected.source_configs and set(value.source_id for value in selected.source_configs)!=set(value.input_id for value in draft.external_inputs):
            raise ValueError('compact E1 source configuration census differs from actual derived external inputs')
        if execution.workers is not None and execution.workers!=resolved.maximum_parallel_tasks:
            dependencies.append(ExperimentDependency('e1.worker-resource-selection',DependencyKind.ENVIRONMENT,
                'Workers differ from the explicit compact E1 resource selection.'))
        requested=replace(selected.root.resource_ceiling,cpu_cores=resolved.maximum_parallel_tasks,
            memory_bytes=resolved.aggregate_memory_ceiling_bytes)
        if (not selected.root.resource_ceiling.contains(requested) or not all(
                selected.root.system.authority_policy.budget_ceiling.contains(value) for value in
                (draft.campaign.budget,selected.root.resource_ceiling,requested))):
            dependencies.append(ExperimentDependency('e1.authority-resource-budget',DependencyKind.AUTHORITY,
                'The actual authority policy must cover both the complete campaign and candidate resource ceilings.'))
        dependencies.append(ExperimentDependency(RESOURCE_BINDING_DEPENDENCY,DependencyKind.SOFTWARE,
            'Bind the generated complete resource roster to the actual public candidate preview during authoring.'))
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
    selected=tuple(value for _,value in source_records if type(value) in selection_types())
    if len(selected)!=1: raise ValueError('E1 companion must retain exactly its original scientific/entry selection')
    expected,expected_allocation,_=_derive(specification,selected[0])
    if draft!=expected or allocation!=expected_allocation: raise ValueError('E1 companion substitutes original derived graph or independent roots')


def derive_resource_selection(selection,draft):
    """Resolve only caller-selected operational ceilings onto the actual graph."""
    if type(selection) is not E1CompactExperimentSelectionV2:raise TypeError('compact E1 requires its declarative resource selection')
    controls=selection.resources;capacity,=controls.child_token_limits
    budgets=dict(selection.phase_budgets)
    sources=sources_for_manifest(selection.manifest)
    history={owner.NAMESPACE+'.'+source.root_id+'.history':source for source in sources}
    cells=[]
    for operation in draft.operations:
        node=operation.node_id;phase=operation.selection.capability_key.rsplit('.',1)[-1]
        native=node in history
        if (phase not in budgets or native!=(phase=='history') or operation.maximum_attempts!=1
                or operation.resource_budget!=_operation_budget(budgets[phase])):
            raise ValueError('compact E1 resource projection changes the actual complete phase/native budget contract')
        unit=history[node].root.root.independent_group_id if native else None
        cells.append(ExecutionResourceTaskCellSpec('cell.'+node,node,capacity.child_id,unit,
            'preparation.'+node if native else None,1,int(native),int(native),native,
            replace(budgets[phase],budget_id='budget.'+node),
            replace(selection.native_progress,contract_id='liveness.'+node) if native else None,None,None))
    if (len(cells)!=4*len(sources)+2 or len(history)!=sum(cell.native_simulator_launch for cell in cells)
            or {cell.task_id for cell in cells}!={node for node,_ in selection_task_budgets(selection,sources)}):
        raise ValueError('compact E1 resource projection omits an actual selected root/phase/global task')
    if len(history)>capacity.physical_execution_token_limit:raise ValueError('compact E1 explicit native token capacity does not contain the complete selected population')
    if any(cell.resource_budget.memory_bytes>controls.aggregate_memory_ceiling_bytes for cell in cells):
        raise ValueError('compact E1 phase budget exceeds the explicit aggregate memory ceiling')
    return replace(controls,task_cells=tuple(cells),child_token_limits=(ChildResourceTokenLimit(capacity.child_id,len(history),0),))


def derive_design_inputs(preparation):
    from empirical_lawhood.planning.experiment_entry import validate_experiment_entry
    selected,=(record for _,record in preparation.design_records if type(record) is E1CompactExperimentSelectionV2)
    validate_experiment_entry(selected.root,selected.entry_package,for_issue=False)
    records=dict(preparation.input_records)
    operands=tuple(RecursiveProspectiveOperand(value.logical_artifact_id,value.expected_content_sha256,
        len(records[value.input_id].canonical_bytes()),value.payload_schema,value.media_type,
        value.outcome_access,value.visibility_ceiling) for value in sorted(preparation.draft.external_inputs,key=lambda value:value.logical_artifact_id))
    return RecursiveProspectiveDesignInputs('prospective.'+preparation.specification_record.specification_id,preparation.draft,
        selected.entry_package,selected.formal_methods,selected.formal_source_inventories,selected.qualifications,
        selected.known_design_inputs,operands)
