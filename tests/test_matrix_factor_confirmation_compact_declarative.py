# SPDX-License-Identifier: MPL-2.0
"""Disclosed compiler/metadata controls; no issue, acquisition or qualification."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import (
    compact_bindings as owner,compact_preparation as domain,compact_records as r,
)
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding,ExperimentInputSelection
from empirical_lawhood.planning.study_authoring import (
    DesignInputRecord,DesignInputRole,SourceAccessDisposition,SourceMaterializationRef,SourceMaterializationRole,
)
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution_envelope import (
    ChildResourceTokenLimit,NonTimeResourceBudget,ProgressHeartbeat,ProgressLivenessContract,
)
from empirical_lawhood.runtime.experiment_preparation import DependencyKind,ExecutionSelection
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig,SourceReadMode
from tests.experiment_entry_support import standard_authoring_for_draft
from tests.test_matrix_factor_confirmation_adjudication import prospective
from tests.test_matrix_factor_confirmation_compact_core import compact_case
from tests.test_matrix_factor_confirmation_eligibility import publish,provenance as provenance,stock as stock  # noqa: F401
from tests.test_matrix_factor_confirmation_history import e1 as e1  # noqa: F401

ROOT=Path(__file__).resolve().parents[1]


def _compile(draft,qualifications):
    declarations=owner.operation_declarations()
    registry=CapabilityRegistry('registry.disclosed.compact-v2',tuple(sorted(
        (row.manifest() for row in declarations),key=lambda row:row.registry_id)))
    return compile_recursive_wave(draft=draft,registrations=tuple(row.registration() for row in declarations),
        registry=registry,implementation_commit='a'*40,qualifications=qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs,
        output_codecs={key:value for row in declarations for key,value in row.record_codecs.items()})


def _case(e1):
    plane,_,_=e1
    prior,old_qualifications=prospective(e1)
    root=prior.prospective_draft
    manifest,_=compact_case(e1)
    scientific=manifest.specification.selection
    criterion=replace(scientific.criterion,system_id=root.system.system_id,world_id=root.system.world.world_id,
        relation=ObjectIdentity.from_record(root.experiment.relation.relation_id,root.experiment.relation),
        independent_unit_id=root.experiment.independent_unit_id)
    scientific=replace(scientific,criterion=criterion)
    frozen=replace(manifest.specification,selection=scientific,publication=publish(plane,scientific,'compact.v2.selection'))
    manifest=replace(manifest,specification=frozen)
    sources=r.sources_for_manifest(manifest)
    config=owner.E1CompactAdjudicationConfig('config.'+owner.KEY,manifest.identity,criterion,sources)
    cutoffs=owner.cutoffs(config)
    experiment=replace(root.experiment,information_cutoffs=cutoffs,
        obligations=replace(root.experiment.obligations,support=replace(root.experiment.obligations.support,information_cutoff_id=cutoffs[0].cutoff_id)))
    operands=tuple(sorted({operand for source in sources for operand in owner.source_operands(source)},key=lambda row:row.object_id))
    design=tuple(DesignInputRecord('input.compact-v2.'+str(index).zfill(3),operand,operand.object_fingerprint,
        cutoffs[0],DesignInputRole.READINESS_METADATA,OutcomeAccess.OUTCOME_BLIND,VisibilityCeiling.PROSPECTIVE,'human.owner')
        for index,operand in enumerate(operands))
    root=replace(root,experiment=experiment,design_inputs=design,
        design_origin=replace(root.design_origin,declared_input_ids=tuple(row.input_id for row in design)))
    phase_budgets=tuple((phase,NonTimeResourceBudget('budget.disclosed.'+phase,1,1024**3,64*1024**2,100,64*1024**2)) for phase in domain.RESOURCE_PHASES)
    resources=ExecutionResourceSelection('resources.disclosed.compact-v2',(),
        (ChildResourceTokenLimit('child.disclosed.compact-v2',len(sources),0),),(),(),(),None,None,
        1,1024**3,(),(),'f'*64,True,True,True,True)
    progress=ProgressLivenessContract('progress.disclosed.compact-v2',ProgressHeartbeat.SCHEMA,
        'disclosed-native-work',Decimal(10),True,True)
    selected=domain.E1CompactExperimentSelectionV2('selection.disclosed.compact-v2',root,manifest,phase_budgets,
        resources,progress,(),design,(),None,None,())
    spec=domain.E1CompactExperimentSpecification('experiment.disclosed.compact-v2',root.question,
        tuple(source.root_id for source in sources),selected.identity)
    draft,_,records=domain._derive(spec,selected)
    records=dict(records);qualifications=[];materials=[];configs=[]
    for index,external in enumerate(draft.external_inputs):
        record=records[external.input_id];raw=record.canonical_bytes()
        material=ObjectIdentity(external.logical_artifact_id,record.SCHEMA,record.VERSION,record.fingerprint())
        qualification=replace(old_qualifications[0],receipt_id='qualification.compact-v2.'+str(index),
            source_id=external.input_id,materialization=material,content_sha256=record.fingerprint(),
            clock_ids=tuple(row.clock_id for row in root.system.clocks))
        source_config=SourceMaterializationConfig('source-config.compact-v2.'+str(index),external.input_id,
            SourceMaterializationRole.OBSERVATION_STREAM,record.fingerprint(),len(raw),len(raw),record.SCHEMA,
            external.media_type,SourceReadMode.ORDINARY_BOUNDED,external.outcome_access,external.visibility_ceiling)
        qualifications.append(qualification);configs.append(source_config)
        materials.append(SourceMaterializationRef(source_id=external.input_id,role=SourceMaterializationRole.OBSERVATION_STREAM,
            evidence_world_id=root.system.world.world_id,materialization=material,content_sha256=record.fingerprint(),
            source_config_sha256=source_config.fingerprint(),observation_operator=qualification.observation_operator,
            numerical_view_ids=qualification.numerical_view_ids,qualification_receipt=ObjectIdentity.from_record(qualification.receipt_id,qualification),
            access_disposition=SourceAccessDisposition.VERIFIED_ACCESS))
    campaign=replace(root.campaign,budget=ResourceBudget.aggregate(row.resource_budget for row in draft.operations),
        nodes=tuple(replace(row,object_identity=ObjectIdentity.from_record(experiment.experiment_id,experiment))
            if row.object_identity.object_id==experiment.experiment_id else row for row in root.campaign.nodes))
    root=replace(root,campaign=campaign,source_materializations=tuple(sorted(materials,key=lambda row:row.source_id)))
    selected=replace(selected,root=root,qualifications=tuple(sorted(qualifications,key=lambda row:row.receipt_id)),
        source_configs=tuple(sorted(configs,key=lambda row:row.fingerprint())))
    spec=replace(spec,selection=selected.identity)
    draft,_,_=domain._derive(spec,selected)
    compiled=_compile(draft,selected.qualifications)
    assert compiled.candidate_report.candidate is not None,compiled.candidate_report.diagnostics
    # The explicit selected stock root freezes the normal compiler projection;
    # no public runtime hook rewrites scientific inputs or invents an entry.
    selected=replace(selected,root=compiled.candidate_draft)
    standard,formal=standard_authoring_for_draft(compiled.candidate_draft,compiled.candidate_context,
        formal_method_capability_key=owner.KEY)
    selected=replace(selected,entry_package=standard.entry_package,formal_methods=formal.formal_methods,
        formal_source_inventories=formal.source_inventories)
    return replace(spec,selection=selected.identity),selected,compiled


def test_actual_compiler_derives_every_task_cell_and_canonical_obligation_without_task_maps(e1):  # noqa: F811
    spec,selected,_=_case(e1)
    assert not hasattr(selected,'task_budgets') and not hasattr(selected,'proof_owners')
    assert decode_canonical_bytes(selected.canonical_bytes(),type(selected),maximum_bytes=None)==selected
    draft,_,records=domain._derive(spec,selected)
    records=dict(records)
    assert all(external.maximum_size_bytes==len(records[external.input_id].canonical_bytes()) for external in draft.external_inputs)
    # Real publication, bounded read and canonical decode own this new access
    # receipt; it establishes metadata access, never scientific qualification.
    from empirical_lawhood.api.derived_metadata_access import derive_canonical_metadata_access
    external=next(row for row in draft.external_inputs if row.payload_schema==r.E1CompactManifest.SCHEMA)
    record=records[external.input_id]
    publication=publish(e1[0],record,external.logical_artifact_id)
    config,access=derive_canonical_metadata_access(writer=e1[0],publication=publication,record=record,
        external=external,root=selected.root,observation_operator=selected.qualifications[0].observation_operator)
    assert config.expected_size_bytes==len(record.canonical_bytes()) and access.content_sha256==record.fingerprint()
    with pytest.raises(ValueError,match='canonical input'):
        derive_canonical_metadata_access(writer=e1[0],publication=publication,record=record,
            external=replace(external,maximum_size_bytes=None),root=selected.root,
            observation_operator=selected.qualifications[0].observation_operator)
    compiled=_compile(draft,selected.qualifications)
    assert compiled.candidate_report.candidate is not None,compiled.candidate_report.diagnostics
    resolved=domain.derive_resource_selection(selected,draft)
    n=len(spec.root_ids)
    assert len(draft.operations)==len(resolved.task_cells)==4*n+2
    assert len(selected.phase_budgets)==6 and selected.resources.task_cells==()
    qualifications={row.source_id:row for row in selected.qualifications}
    configs={row.source_id:row for row in selected.source_configs}
    assert all(row.content_sha256==qualifications[row.source_id].content_sha256
        and row.source_config_sha256==configs[row.source_id].fingerprint() for row in selected.root.source_materializations)
    assert resolved.child_token_limits==(ChildResourceTokenLimit('child.disclosed.compact-v2',n,0),)
    assert sum(row.native_simulator_launch for row in resolved.task_cells)==n
    assert all((row.progress_liveness is not None)==row.native_simulator_launch for row in resolved.task_cells)
    expected=dict(domain.selection_proof_owners(selected))
    assert {row.obligation_id:row.proof_owner_node_id for row in compiled.template.coverage.bindings}==expected
    for cutoff in selected.root.experiment.information_cutoffs:
        assert expected[cutoff.cutoff_id]==owner.NAMESPACE+'.'+cutoff.cutoff_id.removeprefix('cutoff.')+'.history'


class ReachedActualPreview(RuntimeError):pass


def test_copied_public_v2_author_reaches_registered_preview_after_real_publication_checks(e1,monkeypatch):  # noqa: F811
    spec,selected,_=_case(e1)
    directory=Path(e1[0].root.contract.canonical_path)
    (directory/'compact-v2-selection.json').write_bytes(selected.canonical_bytes())
    path=directory/'compact-v2-inputs.json'
    path.write_bytes(ExperimentInputSelection('inputs.disclosed.compact-v2',domain.PROTOCOL_ID,
        (ExperimentInputBinding('selection',selected.identity,'compact-v2-selection.json',len(selected.canonical_bytes())),)).canonical_bytes())
    copied=load_experiment_inputs(spec,path)
    service=ExperimentProgrammeService(ROOT,e1[0])
    execution=ExecutionSelection(1,'main-locked',selected.manifest.provenance.identity,str(directory))
    prepared=service.prepare(spec,method_inputs=copied.method_inputs,execution=execution)
    assert tuple((row.code,row.kind) for row in prepared.dependencies)==((domain.RESOURCE_BINDING_DEPENDENCY,DependencyKind.SOFTWARE),)
    observed=[]
    def preview(**kwargs):
        assert kwargs['preparation']==prepared
        assert kwargs['design_inputs'].draft==prepared.draft
        observed.append(kwargs)
        raise ReachedActualPreview('actual registered compact candidate preview')
    from empirical_lawhood.api import prospective_experiment
    monkeypatch.setattr(prospective_experiment,'preview_prepared_prospective_experiment_candidate',preview)
    output=directory/'compact-v2-author'
    with pytest.raises(ReachedActualPreview):service.author(preparation=prepared,output_dir=output)
    assert len(observed)==1 and not output.exists()


@pytest.mark.parametrize('change',('foreign-cutoff','missing-cutoff','capacity','missing-phase'))
def test_declarative_changes_refuse_before_public_authoring_effects(e1,change):  # noqa: F811
    spec,selected,_=_case(e1)
    with pytest.raises(ValueError,match='compact E1|six finite'):
        if change=='missing-phase':replace(selected,phase_budgets=selected.phase_budgets[:-1])
        elif change=='capacity':
            selected=replace(selected,resources=replace(selected.resources,child_token_limits=(ChildResourceTokenLimit('child.disclosed.compact-v2',1,0),)))
            draft,_,_=domain._derive(replace(spec,selection=selected.identity),selected)
            domain.derive_resource_selection(selected,draft)
        else:
            cutoffs=selected.root.experiment.information_cutoffs
            changed=cutoffs[:-1] if change=='missing-cutoff' else (replace(cutoffs[0],cutoff_id='cutoff.foreign'),*cutoffs[1:])
            changed=tuple(sorted(changed,key=lambda row:row.cutoff_id))
            selected=replace(selected,root=replace(selected.root,experiment=replace(selected.root.experiment,information_cutoffs=changed)))
            domain._derive(replace(spec,selection=selected.identity),selected)
