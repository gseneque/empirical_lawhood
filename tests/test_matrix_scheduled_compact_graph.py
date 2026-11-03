# SPDX-License-Identifier: MPL-2.0
"""Compact scheduled graph conformance over exposed software qualifications.

These fixtures exercise actual graph compilation. They do not qualify the
source declarations or produce fresh scientific evidence or native contact.
"""

from dataclasses import replace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import (
    compact_bindings as b, compact_composition as c,
    compact_records as r, records as original_records,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.planning.study_authoring import (
    DesignInputRecord, DesignInputRole, SourceAccessDisposition, SourceMaterializationRef, SourceMaterializationRole,
)
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_matrix_scheduled_calibration import (
    bank as bank, prospective_bank, provenance as provenance,
    response_bank as response_bank, scheduled as scheduled, stock as stock,
)


def compact_bank(bank, *, response=False):
    legacy, qualifications, old_records, commitment = prospective_bank(bank, response=response)
    owners = tuple(sorted((obligation, operation.node_id.replace(original_records.NAMESPACE, r.NAMESPACE, 1))
        for operation in legacy.operations for obligation in operation.obligation_ids))
    budgets = {operation.node_id.replace(original_records.NAMESPACE, r.NAMESPACE, 1): operation.resource_budget
        for operation in legacy.operations}
    templates = {key: value for key, value in old_records.items() if type(value) is bytes}
    draft, records = c.history_draft(root=legacy.prospective_draft, commitment=commitment,
        proof_owners=owners, operational_budgets=budgets, draft_id='draft.software.compact-scheduled',
        template_bytes=templates)
    draft, qualifications = qualify_compact_draft(draft, records, qualifications[0])
    return draft, qualifications, records, commitment


def qualify_compact_draft(draft, records, reference):
    root = draft.prospective_draft
    assert len({value.information_cutoff.canonical_bytes() for value in root.design_inputs}) == 1
    additions = tuple(DesignInputRecord(f'design.software.compact-scheduled.{index:03}',
        ObjectIdentity.from_record(value.bank_id if type(value) is r.ScheduledCompactBank else value.source_id, value),
        value.fingerprint(), root.design_inputs[0].information_cutoff, DesignInputRole.READINESS_METADATA,
        reference.outcome_access, reference.visibility_ceiling, 'human.owner')
        for index, value in enumerate(records.values()) if type(value) in (r.ScheduledCompactBank, original_records.ScheduledSource)
        and ObjectIdentity.from_record(value.bank_id if type(value) is r.ScheduledCompactBank else value.source_id, value)
            not in {row.object_identity for row in root.design_inputs})
    designs = tuple(sorted((*root.design_inputs, *additions), key=lambda value: value.input_id))
    root = replace(root, design_inputs=designs, design_origin=replace(root.design_origin,
        declared_input_ids=tuple(value.input_id for value in designs)))
    materials, qualifications = [], []
    for index, external in enumerate(draft.external_inputs):
        version = '1.0.0' if type(records[external.logical_artifact_id]) is bytes else records[external.logical_artifact_id].VERSION
        identity = ObjectIdentity(external.logical_artifact_id, external.payload_schema, version, external.expected_content_sha256)
        # New hypothetical credentials explicitly bind the new physical records;
        # old full-source credentials cannot authenticate compact descriptors.
        qualification = replace(reference, receipt_id=f'qualification.software.compact-scheduled.{index:03}',
            source_id=external.input_id, materialization=identity, content_sha256=external.expected_content_sha256,
            outcome_access=external.outcome_access, visibility_ceiling=external.visibility_ceiling)
        qualifications.append(qualification)
        materials.append(SourceMaterializationRef(external.input_id, SourceMaterializationRole.OBSERVATION_STREAM,
            root.system.world.world_id, identity, external.expected_content_sha256, external.expected_content_sha256,
            qualification.observation_operator, qualification.numerical_view_ids,
            ObjectIdentity.from_record(qualification.receipt_id, qualification), SourceAccessDisposition.VERIFIED_ACCESS))
    root = replace(root, source_materializations=tuple(sorted(materials, key=lambda value: value.source_id)))
    return replace(draft, prospective_draft=root), tuple(qualifications)


def compile_bank(draft, qualifications):
    factories = b.operation_factories()
    registry = CapabilityRegistry('registry.software.compact-scheduled', tuple(sorted(
        (factory.manifest for factory in factories), key=lambda value: value.registry_id)))
    return compile_recursive_wave(draft=draft, registrations=tuple(factory.registration for factory in factories),
        registry=registry, implementation_commit='d'*40, qualifications=qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs,
        output_codecs={schema: cls for factory in factories for schema, cls in factory.output_codecs.items()})


@pytest.mark.parametrize('response', (False, True))
def test_compact_graph_preserves_all_scientific_subjects_and_complete_phase_census(bank, response_bank, monkeypatch, response):
    draft, qualifications, records, commitment = compact_bank(response_bank if response else bank, response=response)

    def blocked(*args, **kwargs):
        pytest.fail('compact graph construction or source validation entered numerical science')

    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    compiled = compile_bank(draft, qualifications)
    assert compiled.candidate_report.candidate is not None, compiled.candidate_report.diagnostics
    assert len(compiled.template.protocol.steps) == (25 if response else 17)
    assert len(compiled.selected_scientific_projection.canonical_bytes()) < 16*1024**2
    if response:
        joins = tuple(edge for edge in draft.links if edge.consumer_input_id.startswith('full-numericals.'))
        assert tuple(sorted(edge.consumer_input_id.removeprefix('full-numericals.') for edge in joins)) == commitment.selected_root_ids
    shared, = (value for value in records.values() if type(value) is r.ScheduledCompactBank)
    assert shared.commitment_config() == commitment
    assert shared.selected_root_ids == commitment.selected_root_ids
    assert shared.sources == commitment.sources
    assert {value.identity for value in records.values() if type(value) is original_records.ScheduledSource} == {
        reference.identity for reference in shared.sources}
    assert len(shared.forecast_design.training_record.population.selections) == 256
    assert len(shared.forecast_design.model_record.training_root_ids) == 128
    assert {value.expected_content_sha256 for value in draft.external_inputs if value.payload_schema == original_records.ScheduledSource.SCHEMA} == {
        value.fingerprint() for value in shared.sources}
    for operation in draft.operations:
        if operation.selection.capability_key.endswith(('.forecast', '.forecast-calibrated', '.physical-forecast')):
            inputs = {edge.consumer_input_id for edge in draft.links if edge.consumer_node_id == operation.node_id}
            assert not inputs & {'bank', 'source', 'allocation', 'selection', 'provenance', 'checkpoint'}
            assert not any(name.startswith('streams.') for name in inputs)


def test_compact_graph_refuses_thinned_root_phase_census(bank):
    draft, qualifications, _, _ = compact_bank(bank)
    removed = next(operation for operation in draft.operations if operation.node_id.endswith('.full-numerical'))
    draft = replace(draft, operations=tuple(operation for operation in draft.operations if operation != removed),
        selected_operation_ids=tuple(value for value in draft.selected_operation_ids if value != removed.node_id),
        links=tuple(edge for edge in draft.links if edge.consumer_node_id != removed.node_id and edge.producer_node_id != removed.node_id))
    with pytest.raises(ValueError, match='complete selected root|qualified ordinary input|undeclared scientific input|qualification changes|complete actual source/dependency'):
        compile_bank(draft, qualifications)


@pytest.mark.parametrize('mutation', ('bank-substitution', 'forecast-private-bank', 'future-stream-substitution', 'old-source-qualification', 'old-census-qualification', 'full-numerical-join-omission'))
def test_compact_graph_rejects_substituted_shared_custody_and_predictor_future_inputs(response_bank, mutation):
    draft, qualifications, _, _ = compact_bank(response_bank, response=True)
    if mutation == 'bank-substitution':
        target = next(edge for edge in draft.links if edge.consumer_input_id == 'bank')
        foreign = next(value.input_id for value in draft.external_inputs if value.payload_schema == original_records.ScheduledSource.SCHEMA)
        draft = replace(draft, links=tuple(replace(edge, external_input_id=foreign) if edge == target else edge for edge in draft.links))
    elif mutation == 'forecast-private-bank':
        target = next(operation.node_id for operation in draft.operations if operation.node_id.endswith('.forecast'))
        bank = next(value.input_id for value in draft.external_inputs if value.payload_schema == r.ScheduledCompactBank.SCHEMA)
        from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink
        extra = RecursiveInputLink('edge.software.illegal-private-bank', target, 'bank', external_input_id=bank, scientific_role='SOURCE')
        draft = replace(draft, links=tuple(sorted((*draft.links, extra), key=lambda value: value.edge_id)))
    elif mutation == 'future-stream-substitution':
        target = next(edge for edge in draft.links if edge.consumer_input_id.startswith('streams.future.'))
        current = next(edge.external_input_id for edge in draft.links
            if edge.consumer_node_id == target.consumer_node_id and edge.consumer_input_id == target.consumer_input_id.replace('streams.future.', 'streams.'))
        draft = replace(draft, links=tuple(replace(edge, external_input_id=current) if edge == target else edge for edge in draft.links))
    elif mutation == 'full-numerical-join-omission':
        target = next(edge for edge in draft.links if edge.consumer_input_id.startswith('full-numericals.'))
        draft = replace(draft, links=tuple(edge for edge in draft.links if edge != target))
    elif mutation == 'old-source-qualification':
        target = next(value for value in qualifications if value.materialization.object_schema == original_records.ScheduledSource.SCHEMA)
        old = ObjectIdentity(target.materialization.object_id, original_records.ScheduledSource.SCHEMA, '1.0.0', target.content_sha256)
        qualifications = tuple(replace(value, materialization=old) if value == target else value for value in qualifications)
    else:
        target = next(value for value in qualifications if value.materialization.object_schema == response_bank[2].audit.census.SCHEMA)
        old = replace(target.materialization, object_version='1.0.0')
        qualifications = tuple(replace(value, materialization=old) if value == target else value for value in qualifications)
    with pytest.raises(ValueError, match='complete selected root|qualified ordinary input|undeclared scientific input|qualification changes|complete actual source/dependency'):
        compile_bank(draft, qualifications)


def calibration64_bank(response_bank, *, cases_per_group=1, programme_only=False):
    """Declare exposed software64, preserving full physical/training operands.

    Each of four original preparation families receives 16 independent groups
    and one coordinate case. No trajectories are acquired and this declaration
    is never a fresh scientific allocation or source qualification.
    """
    from decimal import Decimal
    from itertools import product
    from hashlib import sha256
    from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
    from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import commitment as commit_records, forecast, response_records, response_selection
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.operation_bindings import source_operands
    from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from tests.test_matrix_factor_confirmation_eligibility import publish

    if cases_per_group not in (1, 9):
        raise ValueError('software scaling control retains one or complete nine coordinates')
    label = 'compact64' if cases_per_group == 1 else 'compact576'
    plane, old_sources, old_commit, raw = response_bank
    legacy, qualifications, _, old_commit = prospective_bank(response_bank, response=True)
    base = next(source for source in old_sources if source.root_id in old_commit.selected_root_ids)
    role = MatrixProgrammeRole.CALIBRATION
    settings = ((base.coordinate.primary_view.bath_temperature, base.coordinate.primary_view.friction_gamma,
        base.coordinate.member.cross_coupling_gamma),) if cases_per_group == 1 else (
        *product((Decimal(1), Decimal(3)), (Decimal('.5'), Decimal('1.5')), (Decimal('.5'), Decimal('1.5'))),
        (Decimal(2), Decimal(1), Decimal(1)))
    coordinates, rows, scopes = [], [], []
    for index, family in enumerate(FOUR_FAMILY_PREPARATION_IDS):
        family_coordinates = tuple(replace(base.coordinate,
            coordinate_id=f'coordinate.software.{label}.family.{index}.{case}', family_id=family,
            member=replace(base.coordinate.member, member_id=f'member.software.{label}.{index}.{case}', cross_coupling_gamma=coupling),
            primary_view=replace(base.coordinate.primary_view, view_id=f'primary.software.{label}.{index}.{case}',
                bath_temperature=temperature, friction_gamma=friction),
            fine_view=replace(base.coordinate.fine_view, view_id=f'fine.software.{label}.{index}.{case}',
                bath_temperature=temperature, friction_gamma=friction))
            for case, (temperature, friction, coupling) in enumerate(settings))
        coordinates.extend(family_coordinates)
        groups = tuple(f'group.software.{label}.{index}.{unit:02}' for unit in range(16))
        for unit, group in enumerate(groups):
            streams = tuple(MatrixHistorySeed(purpose, sha256(('EXPOSED-SOFTWARE-'+label+'-'+group+'-'+purpose).encode()).hexdigest())
                for purpose in HISTORY_PURPOSES)
            for case, coordinate in enumerate(family_coordinates):
                root = replace(base.root.root, root_id=f'root.software.{label}.{index}.{unit:02}.{case}',
                    independent_group_id=group, regime_id=f'regime.software.{label}.family.{index}.{case}', coordinate_id=coordinate.coordinate_id)
                rows.append(original_records.ScheduledRoot(root, ObjectIdentity.from_record(coordinate.coordinate_id, coordinate), streams))
        scopes.append(replace(next(scope for scope in base.allocation.matched_scopes if scope.role is role),
            scope_id=f'scope.software.{label}.family.{index}', independent_group_ids=groups,
            coordinates=tuple(ObjectIdentity.from_record(co.coordinate_id, co) for co in family_coordinates)))
    retained = tuple(source for source in old_sources if source.root.root.role is not role)
    old_coordinate_ids = {source.coordinate.coordinate_id for source in retained}
    allocation = replace(base.allocation, allocation_id='allocation.software.'+label,
        coordinates=tuple(sorted((*coordinates, *(coordinate for coordinate in base.allocation.coordinates
            if coordinate.coordinate_id in old_coordinate_ids)), key=lambda value: value.coordinate_id)),
        roots=tuple(sorted((*rows, *(source.root for source in retained)), key=lambda value: value.root.root_id)),
        matched_scopes=tuple(sorted((*scopes, *(scope for scope in base.allocation.matched_scopes if scope.role is not role)),
            key=lambda value: value.scope_id)))
    reservation = replace(base.reservation, reservation_id='reservation.software.'+label, allocation=allocation,
        publication=publish(plane, allocation, 'software.'+label+'.original-allocation'))
    selection = replace(base.specification.selection, selection_id='selection.software.'+label, reservation=original_records.identity(reservation),
        coordinate_policies=tuple((ObjectIdentity.from_record(coordinate.coordinate_id, coordinate), original_records.identity(base.policy))
            for coordinate in allocation.coordinates))
    specification = replace(base.specification, specification_id='specification.software.'+label, selection=selection,
        publication=publish(plane, selection, 'software.'+label+'.original-selection'))
    source_index = ScheduledSourceIndex.from_shared(reservation=reservation,
        specification=specification, provenances=(base.provenance,))
    references = tuple(source_index.reference(source_id='source.'+row.root.root_id,
        root_id=row.root.root_id, provenance=base.provenance.identity) for row in allocation.roots)
    sources = tuple(source_index.resolve(reference) for reference in references)
    selected = tuple(source for source in sources if source.root.root.role is role)
    training = replace(old_commit.forecast_design.training_record, future_regime_reservation=original_records.identity(reservation),
        future_reservation_publication=commit_records.corpus_artifact(publish(plane, reservation, 'software.'+label+'.original-reservation')))
    model = replace(old_commit.forecast_design.model_record, spec=training.identity, reservation=original_records.identity(reservation))
    design = replace(old_commit.forecast_design, allocation=original_records.identity(allocation), training_record=training,
        model_record=model, training_publication=publish(plane, training, 'software.'+label+'.original-training'),
        model_publication=publish(plane, model, 'software.'+label+'.original-model'),
        source_scopes=tuple((source.root_id, forecast.CALIBRATION_POINT) for source in selected),
        calibration_group_ids=tuple(sorted({source.root.root.independent_group_id for source in selected})),
        population_alpha=Decimal('.05') if programme_only else old_commit.forecast_design.population_alpha)
    prototype = old_commit.response_selection.protocols[0]
    protocols, panels = [], []
    seen_groups = set()
    for source in selected:
        protocol = replace(prototype, protocol_id='protocol.'+source.root_id, public_source=forecast.ScheduledPublicSource.from_source(source),
            templates=replace(prototype.templates, operand_id='templates.'+source.root_id, source=original_records.identity(source),
                producers=(original_records.identity(source),)))
        protocols.append(protocol)
        group = source.root.root.independent_group_id
        if group in seen_groups:
            continue
        seen_groups.add(group)
        future = tuple(MatrixHistorySeed(purpose, sha256(('EXPOSED-SOFTWARE-'+label+'-FUTURE-'+group+'-'+purpose).encode()).hexdigest())
            for purpose in HISTORY_PURPOSES)
        values = (response_records.ScheduledResponsePanel('panel.common.'+group, group, 'COMMON_NOISE_PANEL',
                'ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES', source.root.streams),
            response_records.ScheduledResponsePanel('panel.independent.'+group, group, 'INDEPENDENT_FUTURE',
                'FRESH_DECLARED_FUTURE_START_AT_CUTOFF', future))
        panels.append((group, values))
    responses = response_selection.ScheduledResponseSelection('selection.software.'+label+'.response', ObjectIdentity.from_record(allocation.allocation_id, allocation), tuple(protocols), tuple(panels),
        old_commit.response_selection.template_publications, replace(old_commit.response_selection.calibration_criterion,
            minimum_group_count=64, required_family_ids=tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))))
    responses.validate_allocation(allocation)
    commitment = replace(old_commit, reservation=reservation, specification=specification,
        provenances=(base.provenance,), sources=references,
        selected_root_ids=tuple(source.root_id for source in selected), forecast_design=design,
        response_selection=responses, response_selection_publication=publish(plane, responses, 'software.'+label+'.original-response-selection'))
    if programme_only:
        return r.ScheduledCompactBank.from_commitment(commitment), {responses.protocols[0].templates.array_artifact.artifact_id: raw}
    root = legacy.prospective_draft
    views = {value.view_id: value for value in root.system.numerical_views}
    for coordinate in coordinates:
        for index, view in enumerate((coordinate.primary_view, coordinate.fine_view)):
            views[view.view_id] = replace(root.system.numerical_views[index], view_id=view.view_id,
                coordinates=tuple(replace(value, value=view.timestep) for value in root.system.numerical_views[index].coordinates))
    system = replace(root.system, numerical_views=tuple(views[key] for key in sorted(views)))
    root = replace(root, system=system)
    qualifications = tuple(replace(value, numerical_view_ids=tuple(view.view_id for view in system.numerical_views)) for value in qualifications)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.qualification import cutoffs
    cutoffs = cutoffs(commitment)
    experiment = replace(root.experiment, information_cutoffs=cutoffs,
        obligations=replace(root.experiment.obligations, support=replace(root.experiment.obligations.support, information_cutoff_id=cutoffs[0].cutoff_id)))
    campaign = replace(root.campaign, nodes=tuple(replace(node, object_identity=ObjectIdentity.from_record(experiment.experiment_id, experiment))
        if node.object_identity.object_id == experiment.experiment_id else node for node in root.campaign.nodes))
    operands = {operand for source in sources for operand in source_operands(source)}
    operands |= {original_records.identity(commitment), original_records.identity(commitment.audit), original_records.identity(design), responses.identity,
        *(ObjectIdentity.from_record(protocol.protocol_id, protocol) for protocol in protocols),
        *(ObjectIdentity.from_record('public.'+source.root_id, forecast.ScheduledPublicSource.from_source(source)) for source in selected)}
    for record in (commitment.audit.census, *commitment.audit.prior_scheduled_coordinates):
        pub, = (pub for pub in commitment.audit.prior_corpus if
            (pub.logical.payload_schema, pub.logical.content_sha256) == (record.SCHEMA, record.fingerprint()))
        operands.add(ObjectIdentity.from_record(pub.logical.logical_artifact_id, record))
    designs = tuple(DesignInputRecord(f'design.software.{label}.{index:06}', operand, operand.object_fingerprint, root.design_inputs[0].information_cutoff,
        DesignInputRole.READINESS_METADATA, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, 'human.owner')
        for index, operand in enumerate(sorted(operands, key=lambda value: value.object_id)))
    root = replace(root, experiment=experiment, campaign=campaign, design_inputs=designs,
        design_origin=replace(root.design_origin, declared_input_ids=tuple(value.input_id for value in designs)),
        evaluation_unit_ids=tuple(sorted({source.root.root.independent_group_id for source in selected})), source_materializations=())
    roles = ('prefix', 'numerical', 'measure', 'check', 'project', 'forecast', 'continue', 'full-numerical', 'physical-forecast', 'responses', 'response-score')
    nodes = (c.COMMIT_KEY, *(r.NAMESPACE+'.'+source.root_id+'.'+name for source in selected for name in roles),
        r.NAMESPACE+'.calibrate', r.NAMESPACE+'.calibration-qualify')
    owners = [(f'obligation.software.{label}.{index:04}', node) for index, node in enumerate(nodes)]
    original_obligations = {name for operation in legacy.operations for name in operation.obligation_ids
        if not name.startswith(('cutoff.', 'obligation.scheduled.'))}
    owners += [(name, r.NAMESPACE+'.calibration-qualify') for name in original_obligations]
    owners += [(cutoff.cutoff_id, r.NAMESPACE+'.'+cutoff.cutoff_id.removeprefix('cutoff.')+'.prefix') for cutoff in cutoffs]
    draft, records = c.history_draft(root=root, commitment=commitment, proof_owners=tuple(sorted(owners)),
        operational_budgets={node: legacy.operations[0].resource_budget for node in nodes}, draft_id='draft.software.'+label,
        template_bytes={responses.protocols[0].templates.array_artifact.artifact_id: raw})
    draft, qualifications = qualify_compact_draft(draft, records, qualifications[0])
    return draft, qualifications, records, commitment


def test_compact_single_coordinate_calibration64_preserves_full_census_below_existing_decoder(response_bank, monkeypatch):
    draft, qualifications, records, commitment = calibration64_bank(response_bank)
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments

    def blocked(*args, **kwargs):
        pytest.fail('64-group compact graph entered native science or fitting')

    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    monkeypatch.setattr(parameter_history_segments, 'acquire_parameter_segment', blocked)
    compiled = compile_bank(draft, qualifications)
    assert compiled.candidate_report.candidate is not None, compiled.candidate_report.diagnostics
    shared, = (value for value in records.values() if type(value) is r.ScheduledCompactBank)
    assert shared.commitment_config() == commitment
    assert len(compiled.template.protocol.steps) == 707
    assert len(shared.selected_root_ids) == len(draft.prospective_draft.evaluation_unit_ids) == 64
    assert len(shared.sources) == 70
    assert len(compiled.selected_scientific_projection.canonical_bytes()) < 16*1024**2
    assert len(shared.forecast_design.training_record.population.selections) == 256
    assert len(shared.forecast_design.model_record.training_root_ids) == 128
    assert shared.provenances == (response_bank[1][0].provenance,)



def test_complete_nine_coordinate_calibration64_capacity_is_explicitly_refused(response_bank, monkeypatch):
    """The full576-case declaration cannot pass the unchanged public decoder."""
    from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection
    from empirical_lawhood.runtime.recursive_prospective import recursive_selection_decoder_registration, recursive_selection_proposal

    def blocked(*args, **kwargs):
        pytest.fail('576-case capacity declaration entered numerical science')

    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    draft, _, records, commitment = calibration64_bank(response_bank, cases_per_group=9)
    selection = RecursiveScientificSelection('selection.'+draft.draft_id, draft.requirements, draft.connections,
        draft.operations, draft.external_inputs, draft.links, (), ObjectIdentity.from_record(draft.prospective_draft.draft_id, draft.prospective_draft))
    shared, = (value for value in records.values() if type(value) is r.ScheduledCompactBank)
    assert shared.commitment_config() == commitment
    assert len(draft.operations) == 6339
    assert len(shared.selected_root_ids) == 576
    assert len(draft.prospective_draft.evaluation_unit_ids) == 64
    assert all(len(scope.coordinates) == 9 and len(scope.independent_group_ids) == 16
        for scope in shared.reservation.allocation.matched_scopes if scope.role.value == 'CALIBRATION')
    assert len(selection.canonical_bytes()) > 16*1024**2
    registration = recursive_selection_decoder_registration(implementation_sha256='a'*64)
    assert registration.maximum_payload_bytes == 16*1024**2
    with pytest.raises(ValueError, match='allowlisted decoder'):
        recursive_selection_proposal(selection=selection, registration=registration)
