# SPDX-License-Identifier: MPL-2.0
"""Exposed scheduled calibration/forecast conformance; no real qualification."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import (
    calibration, calibration_bindings as cb, commitment as c, forecast as f,
    operation_bindings as b, qualification as q, records as r,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.composition import history_draft
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.study_authoring import (
    DesignInputRecord, DesignInputRole, SourceAccessDisposition, SourceMaterializationRef, SourceMaterializationRole,
)
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest, ArtifactProfile
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_scheduled_history_bindings import (
    TEST_BUDGET, bank as bank, scheduled as scheduled, provenance as provenance, stock as stock,
)
from tests.test_matrix_scheduled_response_bindings import response_bank as response_bank


def calibration_fixture(bank, *, unavailable=False):
    """Synthetic finite/nonuse labels; this fixture is never qualified evidence."""
    _, sources, commitment = bank[:3]
    selected = q.selected_sources(commitment)
    cases = tuple(f.ScheduledCalibrationCase(source.root_id, source.root.root.independent_group_id,
        r.identity(source), ObjectIdentity.from_record(source.coordinate.coordinate_id, source.coordinate),
        source.coordinate.physical_time(source.policy.cutoff_tick),
        ObjectIdentity('score.'+source.root_id, 'empirical-lawhood/matrix-scheduled-history/response-score', '1.0.0', 'a'*64),
        ObjectIdentity('seal.'+source.root_id, f.ScheduledForecastSeal.SCHEMA, '1.0.0', 'b'*64),
        'receipt.score.'+source.root_id, 'receipt.forecast.'+source.root_id,
        'materialization.score.'+source.root_id, 'materialization.forecast.'+source.root_id,
        'UNEVALUABLE' if unavailable and index == 1 else 'FINITE',
        (None if unavailable and index == 1 else D(1),)*15, (D('.5'),)*15)
        for index, source in enumerate(selected))
    criterion = commitment.response_selection.calibration_criterion
    return f.ScheduledCalibration('calibration.software.scheduled', r.identity(selected[0].reservation),
        commitment.forecast_design.model, commitment.forecast_design.criterion, r.identity(selected[0].allocation),
        criterion.identity, criterion.independent_unit_id, tuple(sorted({source.coordinate.family_id for source in selected})),
        cases, tuple(sorted({case.independent_group_id for case in cases})), calibration.reduce_cases(cases),
        tuple(sorted((case.score for case in cases), key=lambda value: value.object_id)), f._case_digest(cases))


def query_fixture(response_bank, *, unavailable=False, alpha=D('.5')):
    import numpy as np
    from tests.test_matrix_scheduled_response_forecast import causal_record, pauli
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
    plane, sources, commitment, _ = response_bank
    value = calibration_fixture(response_bank, unavailable=unavailable)
    pub = plane.write(ArtifactWriteRequest(value.calibration_id, 'calibration/'+value.calibration_id+'.json', value.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'software-sealed-calibration', 'calibration', value.canonical_bytes(),
        Visibility.PROSPECTIVE, (), Access.EVALUATION_SEALED))
    selected = tuple(source for source in sources if source.root.root.role.value == 'CONFIRMATION')
    design = replace(commitment.forecast_design, source_scopes=tuple((source.root_id, f.CALIBRATED_QUERY) for source in selected),
        calibration=r.identity(value), calibration_publication=pub, calibration_reservation=r.identity(selected[0].reservation),
        population_alpha=alpha)
    source = selected[0]
    arrays = {'primary_ticks': np.arange(7, dtype='<i8'), 'fine_ticks': np.arange(13, dtype='<i8'),
        'frame': np.asarray([np.kron(matrix, np.eye(2))/2 for matrix in pauli()], dtype='<c16')}
    for view, count in (('primary', 7), ('fine', 13)):
        arrays[view+'_positions'] = np.zeros((count, 2, 3, 4, 4), dtype='<c16')
        arrays[view+'_momenta'] = np.zeros((count, 2, 3, 4, 4), dtype='<c16')
        arrays[view+'_phase'] = np.zeros(count, dtype='<i8')
        arrays[view+'_alpha_tilde'] = np.ones((count, 2), dtype='<f8')
    causal = causal_record(source, arrays)
    feature = f.ScheduledForecastFeature('feature.software.query', r.identity(source), r.identity(causal), source.root_id,
        source.root.root.independent_group_id, f.FAMILY_MAP[source.coordinate.family_id], source.coordinate.clock_id,
        source.coordinate.physical_time(source.policy.cutoff_tick), causal.frame_sha256, 'AVAILABLE', tuple((name, D(0)) for name in FEATURES))
    return value, design, source, causal, feature


def prospective_bank(bank, *, response=False):
    """Real compiler operands over explicitly hypothetical source qualifications."""
    plane, sources, commitment = bank[:3]
    root, original = _fixture()
    original_cutoffs = {cutoff.cutoff_id for cutoff in root.experiment.information_cutoffs}
    if response:
        selection = replace(commitment.response_selection, calibration_criterion=replace(
            commitment.response_selection.calibration_criterion,
            independent_unit_id=root.experiment.independent_unit_id))
        commitment = replace(commitment, response_selection=selection,
            response_selection_publication=publish(plane, selection, 'software.calibration.public-selection'))
    selected = q.selected_sources(commitment)
    world = replace(root.system.world, kind=WorldKind.NUMERICAL_SIMULATOR,
        label='Exposed scheduled numerical software controls', unrepresented_physics=('physical-transfer',))
    clocks = {clock.clock_id: clock for clock in root.system.clocks}
    views = {view.view_id: view for view in root.system.numerical_views}
    for source in sources:
        co = source.coordinate
        clocks[co.clock_id] = replace(root.system.clocks[0], clock_id=co.clock_id,
            nominal_period=co.primary_view.timestep, time_unit=co.primary_view.time_unit)
        for index, view in enumerate((co.primary_view, co.fine_view)):
            views[view.view_id] = replace(root.system.numerical_views[index], view_id=view.view_id,
                coordinates=tuple(replace(coord, value=view.timestep) for coord in root.system.numerical_views[index].coordinates))
    system = replace(root.system, world=world,
        clocks=tuple(clocks[key] for key in sorted(clocks)), numerical_views=tuple(views[key] for key in sorted(views)),
        authority_policy=replace(root.system.authority_policy, budget_ceiling=b.BUDGET))
    cutoffs = q.cutoffs(commitment)
    experiment = replace(root.experiment, information_cutoffs=cutoffs,
        obligations=replace(root.experiment.obligations, support=replace(root.experiment.obligations.support,
            information_cutoff_id=cutoffs[0].cutoff_id)))
    operands = {operand for source in sources for operand in b.source_operands(source)}
    operands |= {r.identity(commitment), r.identity(commitment.audit), r.identity(commitment.forecast_design),
        *(ObjectIdentity.from_record('public.'+source.root_id, f.ScheduledPublicSource.from_source(source)) for source in selected)}
    for record in (commitment.audit.census, *commitment.audit.prior_scheduled_coordinates):
        pub, = (pub for pub in commitment.audit.prior_corpus if
            (pub.logical.payload_schema, pub.logical.content_sha256) == (record.SCHEMA, record.fingerprint()))
        operands.add(ObjectIdentity.from_record(pub.logical.logical_artifact_id, record))
    if response:
        operands |= {commitment.response_selection.identity, *(ObjectIdentity.from_record(protocol.protocol_id, protocol)
            for protocol in commitment.response_selection.protocols)}
    operands = tuple(sorted(operands, key=lambda value: value.object_id))
    designs = tuple(DesignInputRecord(f'design.software.scheduled.{index:03}', operand, operand.object_fingerprint,
        root.experiment.information_cutoffs[0], DesignInputRole.READINESS_METADATA, Access.OUTCOME_BLIND,
        Visibility.PROSPECTIVE, 'human.owner') for index, operand in enumerate(operands))
    campaign = replace(root.campaign, nodes=tuple(replace(node, object_identity=ObjectIdentity.from_record(experiment.experiment_id, experiment))
        if node.object_identity.object_id == experiment.experiment_id else node for node in root.campaign.nodes))
    root = replace(root, system=system, experiment=experiment, campaign=campaign, design_inputs=designs,
        design_origin=replace(root.design_origin, declared_input_ids=tuple(row.input_id for row in designs)),
        development_unit_ids=(), evaluation_unit_ids=tuple(sorted({source.root.root.independent_group_id for source in selected})), resource_ceiling=b.BUDGET)
    roles = ('prefix', 'numerical', 'measure', 'check', 'project', 'forecast', 'continue', 'full-numerical')
    if response:
        roles += ('physical-forecast', 'responses', 'response-score')
    nodes = (c.COMMIT_KEY, *(r.NAMESPACE+'.'+source.root_id+'.'+role for source in selected for role in roles),
        *((cb.CALIBRATE_KEY, cb.QUALIFY_KEY) if response else ()))
    owners = [('obligation.scheduled.'+str(index), node) for index, node in enumerate(nodes)]
    terminal = cb.QUALIFY_KEY if response else r.NAMESPACE+'.'+selected[-1].root_id+'.full-numerical'
    owners += [(row.obligation_id, terminal) for row in original.templates[0].coverage.bindings if row.obligation_id not in original_cutoffs]
    owners += [(cutoff.cutoff_id, r.NAMESPACE+'.'+cutoff.cutoff_id.removeprefix('cutoff.')+'.prefix') for cutoff in cutoffs]
    templates = {commitment.response_selection.protocols[0].templates.array_artifact.artifact_id: bank[3]} if response else None
    draft, records = history_draft(root=root, commitment=commitment, proof_owners=tuple(sorted(set(owners))),
        operational_budgets={node: TEST_BUDGET for node in nodes}, draft_id='draft.software.scheduled', template_bytes=templates)
    materials, qualifications = [], []
    for index, external in enumerate(draft.external_inputs):
        record = records[external.logical_artifact_id]
        if type(record) is bytes:
            assert external.payload_schema == MATRIX_ARRAY_SCHEMA
            assert sha256(record).hexdigest() == external.expected_content_sha256
            material = ObjectIdentity(external.logical_artifact_id, MATRIX_ARRAY_SCHEMA, '1.0.0', external.expected_content_sha256)
        else:
            assert (record.SCHEMA, record.fingerprint()) == (external.payload_schema, external.expected_content_sha256)
            material = ObjectIdentity.from_record(external.logical_artifact_id, record)
        qualification = replace(original.qualifications[0], receipt_id=f'qualification.scheduled.{index:03}',
            source_id=external.input_id, materialization=material, content_sha256=external.expected_content_sha256,
            numerical_view_ids=tuple(view.view_id for view in system.numerical_views),
            clock_ids=tuple(clock.clock_id for clock in system.clocks))
        qualifications.append(qualification)
        materials.append(SourceMaterializationRef(external.input_id, SourceMaterializationRole.OBSERVATION_STREAM,
            world.world_id, material, external.expected_content_sha256, external.expected_content_sha256,
            qualification.observation_operator, qualification.numerical_view_ids,
            ObjectIdentity.from_record(qualification.receipt_id, qualification), SourceAccessDisposition.VERIFIED_ACCESS))
    root = replace(root, source_materializations=tuple(sorted(materials, key=lambda row: row.source_id)))
    return replace(draft, prospective_draft=root), tuple(qualifications), records, commitment


def compile_bank(draft, qualifications):
    factories = b.operation_factories()
    registry = CapabilityRegistry('registry.software.scheduled', tuple(sorted((factory.manifest for factory in factories), key=lambda value: value.registry_id)))
    return compile_recursive_wave(draft=draft, registrations=tuple(factory.registration for factory in factories),
        registry=registry, implementation_commit='d'*40, qualifications=qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs,
        output_codecs={schema: cls for factory in factories for schema, cls in factory.output_codecs.items()})


@pytest.mark.parametrize('response', (False, True))
def test_actual_scheduled_compiler_retains_complete_group_forecast_and_calibration_phases(bank, response_bank, response):
    draft, qualifications, _, _ = prospective_bank(response_bank if response else bank, response=response)
    compiled = compile_bank(draft, qualifications)
    assert compiled.candidate_report.candidate is not None, compiled.candidate_report.diagnostics
    assert len(compiled.template.protocol.steps) == (25 if response else 17)
    if response:
        for operation in draft.operations:
            if operation.node_id.endswith('.continue'):
                incoming = tuple(link for link in draft.links if link.consumer_node_id == operation.node_id)
                assert any(link.consumer_input_id == 'physical-forecast' for link in incoming)
        qualification = next(step for step in compiled.template.protocol.steps if step.step_id == cb.QUALIFY_KEY)
        assert qualification.barrier.value == 'REVEAL'


@pytest.mark.parametrize('entry', ('source', 'config', 'forecast'))
def test_unrelated_pre_fit_reservation_refuses_at_every_forecast_entry(bank, entry):
    _, sources, commitment = bank
    source = next(source for source in sources if source.root_id == commitment.selected_root_ids[0])
    public = f.ScheduledPublicSource.from_source(source)
    foreign = replace(public, reservation=replace(public.reservation, object_fingerprint='f'*64))
    with pytest.raises(ValueError, match='reservation'):
        if entry == 'source':
            commitment.forecast_design.validate_public_source(foreign)
        elif entry == 'config':
            f.ScheduledForecastConfig('config.'+r.NAMESPACE+'.'+source.root_id+'.forecast', foreign, commitment.forecast_design)
        else:
            f.forecast_public(commitment.forecast_design, foreign, None, None, seal_id='software.refused-seal')


def test_physical_model_implementation_substitution_refuses_before_computation(response_bank):
    protocol = response_bank[2].response_selection.protocols[0]
    with pytest.raises(ValueError, match='scheduled response'):
        replace(protocol, mechanical_model=replace(protocol.mechanical_model,
            implementation=replace(protocol.mechanical_model.implementation, object_fingerprint='f'*64)))


@pytest.mark.parametrize('unavailable,alpha,radius', ((False, D('.5'), D('.5')), (False, D('.1'), None), (True, D('.5'), None)))
def test_sealed_calibration_query_retains_whole_group_rank_and_nonuse(response_bank, unavailable, alpha, radius):
    value, design, source, causal, feature = query_fixture(response_bank, unavailable=unavailable, alpha=alpha)
    assert design.validate_source(source) == f.CALIBRATED_QUERY
    public = f.ScheduledPublicSource.from_source(source)
    config = f.ScheduledCalibratedForecastConfig('config.'+r.NAMESPACE+'.'+source.root_id+'.forecast-calibrated', public, design)
    assert b'cumulative_log_errors' not in config.canonical_bytes()
    assert all(str(stream.effective_seed).encode() not in config.canonical_bytes() for stream in source.root.streams)
    result = f.forecast_public(design, public, causal, feature, seal_id='seal.software.query', calibration_record=value)
    assert result.radius == radius and result.calibration == r.identity(value)
    assert result.log_error_uppers == (None if radius is None else D(1),)*15
    with pytest.raises(ValueError, match='complete score package'):
        f.forecast_public(design, public, causal, feature, seal_id='seal.software.query')
    with pytest.raises(ValueError, match='role/scope'):
        f.forecast_public(design, public, causal, feature, seal_id='seal.software.query', scope=f.CALIBRATION_POINT)


@pytest.mark.parametrize('field', ('source', 'coordinate', 'cutoff', 'independent_group_id'))
def test_calibration_qualification_refuses_case_source_and_cutoff_substitution(response_bank, field):
    value = calibration_fixture(response_bank)
    calibration.validate_calibration_sources(response_bank[2], value)
    case = value.cases[0]
    if field in ('source', 'coordinate'):
        changed = replace(case, **{field: replace(getattr(case, field), object_fingerprint='f'*64)})
    elif field == 'cutoff':
        changed = replace(case, cutoff=case.cutoff+D('.001'))
    else:
        changed = replace(case, independent_group_id='foreign.group')
    cases = (changed, *value.cases[1:])
    revised = replace(value, cases=cases, outcome_sha256=f._case_digest(cases),
        group_ids=tuple(sorted({case.independent_group_id for case in cases})), scores=calibration.reduce_cases(cases))
    with pytest.raises(ValueError, match='source|scope'):
        calibration.validate_calibration_sources(response_bank[2], revised)
