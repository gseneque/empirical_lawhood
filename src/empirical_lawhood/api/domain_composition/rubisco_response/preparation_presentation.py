# SPDX-License-Identifier: MPL-2.0
"""Project original local preparation findings without calculating new science."""

from empirical_lawhood.api.application_contracts import ApplicationError
from empirical_lawhood.api.application_development import load_bounded_development
from empirical_lawhood.api.application_presentations import PresentationData
from empirical_lawhood.api.application_exploration_contracts import EXPLORATION_SCHEMA, EXPLORATION_VERSION
from empirical_lawhood.science.identity.provenance import ObjectIdentity

MAX_DRAFT = 64 * 2**20
SCOPE = 'ONE_MATCHED_CONSTRUCTION_FOUR_NESTED_POSITIONS_ZERO_BIOLOGICAL_REPLICATES_NO_KINETIC_ADMISSION'


def selected(draft):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import CAPABILITY as prefix, GPU_CAPABILITY as gpu_prefix
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import CAPABILITY as continued, GPU_CAPABILITY as gpu_continued
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import CAPABILITY as point, GPU_CAPABILITY as gpu_point
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_operation import CAPABILITY as analysis, ENVIRONMENT_CAPABILITY as environmental_analysis
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_supply import CAPABILITY as supply
    allowed = {prefix, gpu_prefix, continued, gpu_continued, point, gpu_point, analysis, environmental_analysis, supply}
    return (1 <= len(draft.operations) <= 20 and set(draft.selected_operation_ids) == {o.node_id for o in draft.operations}
        and all(o.selection.capability_key in allowed and o.selection.capability_version == '1.0.0' for o in draft.operations))


def load_selected(*, context, directory, artifact_writer):
    if context.read_access_paths:
        raise ApplicationError('UNSUPPORTED_ACCESS_SELECTION', 'This local preparation route accepts its original exposed custody only.')
    return load_bounded_development(directory=directory, plane=artifact_writer,
        maximum_draft_bytes=MAX_DRAFT, accept_draft=selected, refusal_code='UNSUPPORTED_PREPARATION_RESPONSE_WAVE')


def question_rows(assessment):
    """Map all six independently assessed findings, preserving exact quantities."""
    counts = {state: sum(r.state == state for r in assessment.coverage)
        for state in ('AVAILABLE', 'UNAVAILABLE', 'NOT_ENTERED', 'NOT_SELECTED')}
    return tuple(dict(question_id=q.question_id, label=q.label,
        acquisition_state=counts, authentication_state='ORIGINAL_COMPLETE_OPERANDS_REOPENED',
        assessment_state='INDEPENDENTLY_RECONSTRUCTED', disposition=q.disposition,
        quantity=[dict(name=r.name, model_name=r.model_name, position=r.position,
            value=None if r.value is None else str(r.value), unit=r.unit) for r in q.quantities],
        uncertainty=q.uncertainty, denominator=dict(assigned_comparisons=q.assigned_comparisons,
            assessable_comparisons=q.assessable_comparisons, nested_state_positions=q.nested_state_positions,
            independent_biological_replicates=q.independent_biological_replicates,
            original_material_count=q.original_material_count, original_site_count=q.original_site_count,
            original_starting_hypotheses=q.original_starting_hypotheses),
        evidence=[p.to_document() for p in q.evidence], consequence=q.consequence) for q in assessment.questions)


def pending_questions(design, acquisition_state):
    """Keep the frozen questions visible before an original assessment exists."""
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment_records import LABELS, UNCERTAINTY
    return tuple(dict(question_id='Q' + str(i), label=label, acquisition_state=acquisition_state,
        authentication_state='ORIGINAL_DESIGN_AUTHENTICATED', assessment_state='NOT_YET_ASSESSED',
        disposition='UNAVAILABLE_PENDING_ORIGINAL_ASSESSMENT', quantity=[], uncertainty=UNCERTAINTY,
        denominator=dict(assigned_comparisons=assigned, assessable_comparisons=0, nested_state_positions=4,
            independent_biological_replicates=0, original_material_count=4, original_site_count=32,
            original_starting_hypotheses=384), evidence=[design.identity.to_document()],
        consequence='Retain this question and its denominator until the original independent analysis is available.')
        for i, (label, assigned) in enumerate(zip(LABELS, (6, 4, 2, 4, 2, 2), strict=True), 1))


def exploration(*, design, question, summary, findings, questions, coverage, assessment=None):
    from empirical_lawhood.api.domain_composition.rubisco_response.application_methods import preparation_response_methods
    methods = preparation_response_methods()
    method_ids = [row['id'] for row in methods]
    source = design.identity.to_document()
    root = 'preparation-response.question.' + design.fingerprint()
    nodes = [dict(id=root, label=question, role='root', state={'physical': 'UNRESOLVED', 'biological': 'NOT_ESTABLISHED'},
        source=source, record=design.to_document(), children=[], method_ids=method_ids, group='local-investigation')]
    edges = []
    if assessment is not None:
        pin = assessment.identity.to_document()
        for row in assessment.questions:
            key = root + '.' + row.question_id.lower()
            nodes[0]['children'].append(key)
            nodes.append(dict(id=key, label=row.label, role='requirement', state={'assessment': row.disposition},
                source=ObjectIdentity.from_record(assessment.assessment_id + '.' + row.question_id.lower(), row).to_document(),
                record=row.to_document(), children=[], method_ids=method_ids, group='six-questions'))
            edges.append(dict(id=key + '.requires', **{'from': root, 'to': key}, kind='REQUIRES',
                label='requires local interpretation', scope=SCOPE, source=pin))
    return dict(schema=EXPLORATION_SCHEMA, version=EXPLORATION_VERSION, question=question, root_id=root,
        nodes=nodes, edges=edges, summary=summary, findings=findings, question_readouts=questions,
        work_coverage=coverage, methods=methods, layout={'kind': 'generic', 'original_root_assessment': design.root_assessment.to_document()},
        coverage={'total_nodes': len(nodes), 'total_edges': len(edges), 'complete_requirements': False},
        pending_bindings=[] if assessment is not None else [{'owner': 'original-six-question-analysis',
            'status': 'NOT_YET_ASSESSED', 'reader': 'read_response_analysis'}])


def read(context, directory, artifact_writer):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import config_types
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_operation import config_types as analysis_config_types
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_operation import PreparationSupplyConfig
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_policy import supply_owners
    from empirical_lawhood.api.experiment_execution_read import read_development_execution
    from empirical_lawhood.api.domain_composition.rubisco_response.preparation_response_analysis import read_preparation_stage, read_response_stage, read_response_analysis
    packet, draft, source, _ = load_selected(context=context, directory=directory, artifact_writer=artifact_writer)
    schema = draft.operations[0].config_identity.object_schema
    assessment, questions = None, ()
    execution = read_development_execution(directory=directory, artifact_writer=artifact_writer)
    if execution['status'] != 'SUCCEEDED':
        configs, _, _, _ = supply_owners(draft)
        first = configs[0]
        prefix = schema in {c.SCHEMA for c in config_types()}
        design = (first.scientific_context.design if prefix else first.analysis.design
            if schema in {c.SCHEMA for c in analysis_config_types()} else first.selection.design
            if schema == PreparationSupplyConfig.SCHEMA else first.protocol)
        questions = pending_questions(design, execution['status'])
        findings, rows = [], questions
        coverage = {'operational_census': execution['operational_census']}
        summary = {'question_count': 6, 'scientific_completion': 'ORIGINAL_PUBLICATION_INCOMPLETE'}
        report, original = {'execution': execution}, {'report': execution}
    elif schema == PreparationSupplyConfig.SCHEMA:
        from empirical_lawhood.api.domain_composition.rubisco_response.preparation_supply import read_preparation_supply
        original = read_preparation_supply(directory=directory, artifact_writer=artifact_writer)
        supply = original['assessment']
        design, assessment = supply.selection.design, supply.selection.response
        questions = (pending_questions(design, 'ORIGINAL_PREPARATION_ADMISSION_ASSESSED') if assessment is None else
            tuple(dict(q, authentication_state='ORIGINAL_ASSESSMENT_CONTRIBUTION_REOPENED',
                assessment_state='ORIGINAL_INDEPENDENT_FINDING_RETAINED') for q in question_rows(assessment)))
        findings, rows = [r.to_document() for r in original['connection_assessments']], questions
        coverage = {'local_supply_assessments': findings}
        summary = {'next_supplier_decision': supply.next_supplier_decision, 'question_count': 6,
            'scientific_completion': 'LOCAL_DESTINATION_SUPPLY_ASSESSED',
            'checkpoint_dispositions': {name: value.value for name, value in supply.checkpoint_dispositions},
            'response_supply_disposition': None if supply.response_disposition is None else supply.response_disposition.value}
        report = supply.to_document()
    elif schema in {c.SCHEMA for c in analysis_config_types()}:
        original = read_response_analysis(directory=directory, artifact_writer=artifact_writer)
        assessment = original['assessment']
        design = assessment.design
        questions = question_rows(assessment)
        findings = [q.to_document() for q in assessment.questions]
        rows = questions
        coverage = {'effects': [r.to_document() for r in assessment.coverage],
            'complete_action_arrays': original['action_manifest'].logical.to_document()}
        summary = {'next_supplier_decision': assessment.next_supplier_decision,
            'question_count': 6, 'scientific_completion': 'INDEPENDENTLY_ASSESSED'}
        report = assessment.to_document()
    elif schema in {c.SCHEMA for c in config_types()}:
        original = read_preparation_stage(directory=directory, artifact_writer=artifact_writer)
        design = original['checkpoints']['design']
        readouts = tuple(original['checkpoints']['original_readouts'].values())
        findings = [r.to_document() for r in readouts]
        rows = tuple(dict(model_name=r.original_result.model_name, position=position,
            disposition='UNAVAILABLE_READ_REFUSED' if r.assessment is None else p.disposition,
            checkpoint=None if r.assessment is None or p.checkpoint is None else p.checkpoint.to_document(),
            readout=r.identity.to_document()) for r in readouts for position in ('initial', 'later')
            for p in (None if r.assessment is None else next(p for p in r.assessment.positions if p.position == position),))
        coverage = {'positions': list(rows), 'read_errors': [r.assessment_error for r in readouts]}
        summary = {'checkpoint_status': original['checkpoints']['checkpoint_status'],
            'question_count': 6, 'scientific_completion': 'PREPARATION_READ_RESPONSE_UNASSESSED'}
        questions = pending_questions(design, original['checkpoints']['checkpoint_status'])
        report = {'original_readouts': findings}
    else:
        original = read_response_stage(directory=directory, artifact_writer=artifact_writer)
        design = original['configs'][0].protocol
        readouts = {r.point.effect.effect_id: r for r in original['readouts']}
        rows = tuple(dict(effect=c.point.effect.to_document(), disposition='ORIGINAL_READOUT_PUBLISHED'
            if c.point.effect.effect_id in readouts else 'UNAVAILABLE',
            readout=readouts[c.point.effect.effect_id].identity.to_document() if c.point.effect.effect_id in readouts else None)
            for c in original['configs'])
        findings, coverage = [], {'effects': list(rows)}
        summary = {'selected_effects': len(rows), 'published_readouts': len(readouts),
            'question_count': 6, 'scientific_completion': 'POINT_PUBLICATIONS_RESPONSE_UNASSESSED'}
        questions = pending_questions(design, {'selected_effects': len(rows), 'published_readouts': len(readouts)})
        report = {'original_point_readouts': [r.identity.to_document() for r in original['readouts']]}
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import is_environmental
    if is_environmental(design):
        nomination = None if assessment is None else assessment.nomination
        summary.update(experiment_variant='RECEIVER_ENVIRONMENT_DEPENDENCE',
            environmental_region=design.environment.region, eligible_common_atoms=len(design.environment.atom_pairs),
            nomination_disposition='NOT_YET_ASSESSED' if nomination is None else nomination.disposition,
            frozen_nomination=None if nomination is None else nomination.identity.to_document())
    summary.update(independent_biological_units=0, nested_state_positions=4,
        original_material_count=4, original_site_count=32, original_starting_hypotheses=384,
        execution_status=original['report']['status'], assigned_tasks=original['report']['task_count'],
        qualification='NOT_ESTABLISHED', incurred_monetary_total=None)
    identity = ObjectIdentity.from_record(packet.packet_id, packet).to_document()
    return PresentationData(identity, SCOPE, summary, tuple(rows), report,
        {'packet': identity, 'implementation': source.to_document(), 'design': design.identity.to_document(),
            'original_root_assessment': design.root_assessment.to_document(), 'run_id': original['report']['run_id']},
        'Original signed quantities, empirical sensitivity, missing outcomes and nested denominators; no physical or kinetic admission.',
        exploration(design=design, question=draft.question, summary=summary, findings=findings, questions=questions,
            coverage=coverage, assessment=assessment))
