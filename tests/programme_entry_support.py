# SPDX-License-Identifier: MPL-2.0
"""Exposed full-programme scientific metadata for software entry controls.

The qualifications produced here are explicit hypothetical test credentials.
They neither select a real scientific population nor authorize issue/native
execution/reveal or turn the programme into a scientifically qualified parent.
"""

from dataclasses import replace

from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import compact_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.operation_bindings import source_operands
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.study_authoring import (
    DesignInputRecord, DesignInputRole, SourceAccessDisposition,
    SourceMaterializationRef, SourceMaterializationRole,
)
from tests.test_matrix_scheduled_calibration import prospective_bank


def programme_scientific_root(response_bank, programme, bank):
    """Retain the real full64 fixture root and complete immutable source scope."""
    legacy, qualifications, _, _ = prospective_bank(response_bank, response=True)
    prototype = legacy.prospective_draft
    views = {v.view_id: v for v in prototype.system.numerical_views}
    for coordinate in bank.reservation.allocation.coordinates:
        for index, view in enumerate((coordinate.primary_view, coordinate.fine_view)):
            views[view.view_id] = replace(prototype.system.numerical_views[index], view_id=view.view_id,
                coordinates=tuple(replace(value, value=view.timestep) for value in prototype.system.numerical_views[index].coordinates))
    system = replace(prototype.system, numerical_views=tuple(views[key] for key in sorted(views)))
    cutoffs = tuple(case.information_cutoff for case in programme.cases)
    experiment = replace(prototype.experiment, information_cutoffs=cutoffs,
        obligations=replace(prototype.experiment.obligations, support=replace(prototype.experiment.obligations.support,
            information_cutoff_id=cutoffs[0].cutoff_id)))
    campaign = replace(prototype.campaign, nodes=tuple(replace(node,
        object_identity=ObjectIdentity.from_record(experiment.experiment_id, experiment))
        if node.object_identity.object_id == experiment.experiment_id else replace(node,
        object_identity=ObjectIdentity.from_record(system.system_id, system))
        if node.object_identity.object_id == system.system_id else node for node in prototype.campaign.nodes))
    scientific = bank.commitment_config()
    source_index = ScheduledSourceIndex.from_shared(reservation=scientific.reservation,
        specification=scientific.specification, provenances=scientific.provenances)
    sources = tuple(source_index.resolve(reference) for reference in scientific.sources)
    operands = {operand for source in sources for operand in source_operands(source)}
    operands.update((programme.identity, compact_identity(bank), programme.forecast_design, programme.response_selection,
        programme.criterion, *programme.source_census, *(compact_identity(d) for d in bank.sources)))
    operands.update(ObjectIdentity.from_record('public.'+source.root_id, ScheduledPublicSource.from_source(source))
        for source in sources if source.root_id in bank.selected_root_ids)
    operands.update(ObjectIdentity.from_record(p.protocol_id, p) for p in bank.response_selection.protocols)
    designs = tuple(DesignInputRecord(f'design.software.programme-global.{index:04}', operand, operand.object_fingerprint,
        prototype.design_inputs[0].information_cutoff, DesignInputRole.READINESS_METADATA,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, 'human.owner')
        for index, operand in enumerate(sorted(operands, key=lambda value: (value.object_id, value.object_schema, value.object_fingerprint))))
    root = replace(prototype, system=system, experiment=experiment, campaign=campaign, design_inputs=designs,
        design_origin=replace(prototype.design_origin, declared_input_ids=tuple(d.input_id for d in designs)),
        development_unit_ids=programme.group_ids if programme.mode == 'E4_DEVELOPMENT' else (),
        evaluation_unit_ids=() if programme.mode == 'E4_DEVELOPMENT' else programme.group_ids, source_materializations=())
    reference = replace(qualifications[0], numerical_view_ids=tuple(v.view_id for v in system.numerical_views))
    return root, reference


def qualify_programme_draft(draft, records, reference):
    """Bind every actual bounded external record to labelled software credentials."""
    materials, qualifications = [], []
    for index, external in enumerate(draft.external_inputs):
        record = records[external.logical_artifact_id]
        version = '1.0.0' if type(record) is bytes else record.VERSION
        pin = ObjectIdentity(external.logical_artifact_id, external.payload_schema, version, external.expected_content_sha256)
        qualification = replace(reference, receipt_id=f'qualification.software.programme.{index:04}',
            source_id=external.input_id, materialization=pin, content_sha256=external.expected_content_sha256,
            outcome_access=external.outcome_access, visibility_ceiling=external.visibility_ceiling)
        qualifications.append(qualification)
        materials.append(SourceMaterializationRef(external.input_id, SourceMaterializationRole.OBSERVATION_STREAM,
            draft.prospective_draft.system.world.world_id, pin, external.expected_content_sha256, external.expected_content_sha256,
            qualification.observation_operator, qualification.numerical_view_ids,
            ObjectIdentity.from_record(qualification.receipt_id, qualification), SourceAccessDisposition.VERIFIED_ACCESS))
    return replace(draft, prospective_draft=replace(draft.prospective_draft,
        source_materializations=tuple(sorted(materials, key=lambda material: material.source_id)))), tuple(qualifications)
