# SPDX-License-Identifier: MPL-2.0
"""Disclosed prepared-source conformance; literal pins establish no real custody.

These controls exercise the installed contracts and metadata producer. They
never certify an actual DEV run, acquire trajectories, or create qualification.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods import matrix_prepared_source_records as r
from empirical_lawhood.adapters.methods import matrix_prepared_source_bindings as bindings
from empirical_lawhood.adapters.methods import matrix_prepared_source_pipeline as rows_owner
from empirical_lawhood.adapters.methods import matrix_prepared_source_experiment as public
from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_records as preparation
from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_prefix
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_forecast import MatrixPreparedMechanicalForecast
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_response_science import MatrixPreparedResponseReadout
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_development_product import MatrixSelectedDevelopmentProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_opportunity_future import MatrixSelectedOpportunityFutureHistory
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as train
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, DevelopmentRunPlan
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
from tests.test_matrix_finite_dt_source import _unexecuted
from tests.test_matrix_selected_opportunity import opportunity, literal_observations  # noqa: F401
from tests.test_matrix_selected_protected import transfer, confirmation, unpublished  # noqa: F401


def prepared_bank(programme, *, publisher=None):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import corpus_artifact, exposure_support
    closure = programme.sources.closure
    # Default descriptors remain deliberately unexecuted. Custody controls can
    # explicitly publish these same scientific records on their ordinary plane.
    publish_record = unpublished if publisher is None else publisher
    census = closure.audit.census
    audit = replace(closure.audit, census=census, prior_corpus=(publish_record(census,'corpus.disclosed.prepared'),))
    audit_publication = publish_record(audit,'audit.disclosed.prepared')
    allocation = replace(closure.reservation.allocation, exposure=replace(closure.reservation.allocation.exposure,
        census=census, scheduled_audit=corpus_artifact(audit_publication)))
    reservation = replace(closure.reservation,allocation=allocation,publication=publish_record(allocation,'allocation.disclosed.prepared'))
    selection = replace(closure.specification.selection,reservation=scheduled.identity(reservation))
    specification = replace(closure.specification,selection=selection,publication=publish_record(selection,'selection.disclosed.prepared'))
    source_index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=closure.provenances)
    references = tuple(source_index.reference(source_id=value.source_id, root_id=value.root_id,
        provenance=value.provenance) for value in closure.descriptors)
    closure=replace(closure,reservation=reservation,specification=specification,audit=audit,audit_publication=audit_publication,
        descriptors=references,
        numerical_scope=scheduled.identity(specification.selection.numerical_design))
    support=exposure_support(audit)
    from tests.matrix_selected_commitment_fixture import unpublished_programme_commitments
    commitment=unpublished_programme_commitments(census,'commitments.unexecuted.disclosed.prepared')
    return r.MatrixPreparedSourceBank('bank.disclosed.prepared.' + programme.phase.lower(),
        replace(programme.sources,closure=closure),programme.assay,programme.panels,support,commitment)


def disclosed_control(bank, source, *, available=True):
    branch_count = len(branch_census(bank.protocol(source), dict(bank.panels)[source.root.root.independent_group_id]))
    return r.MatrixPreparedSourceControl(source.identity, source.root.root.root_id, source.root.root.independent_group_id,
        source.recipe.identity, source.initial, source.provenance.identity, scheduled.identity(source.numerical_design),
        scheduled.identity(source.original.policy.factor_numerical_design), r.instrument_signature(bank.protocol(source)),
        _unexecuted(source.source_id + '.history', preparation.MatrixPreparationHistory),
        _unexecuted(source.source_id + '.assessment', preparation.MatrixPreparationAssessment),
        _unexecuted(source.source_id + '.witness', prepared_prefix.MatrixPreparedFactorWitness),
        _unexecuted(source.source_id + '.frames', prepared_prefix.MatrixPreparedFrameAssessment),
        _unexecuted(source.source_id + '.causal', prepared_prefix.MatrixPreparedCausalPrefix),
        _unexecuted(source.source_id + '.mechanical', MatrixPreparedMechanicalForecast),
        _unexecuted(source.source_id + '.responses', MatrixSelectedOpportunityFutureHistory),
        _unexecuted(source.source_id + '.score', MatrixPreparedResponseReadout),
        (_unexecuted(source.source_id + '.receipt', CanonicalTaskReceipt),), True, available, False, available,
        branch_count if available else 0, 'AVAILABLE' if available else 'NO_ORIGIN', 'COMPLETED' if available else 'NO_ORIGIN')


def disclosed_certificate(bank, opportunity):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_opportunity import nominate_selected_opportunity
    _, nomination = nominate_selected_opportunity(opportunity, literal_observations(opportunity), result_id='nomination.disclosed.prepared-source')
    publication = unpublished(nomination, 'publication.disclosed.prepared-source')
    publication = replace(publication, logical=replace(publication.logical, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY))
    run = _unexecuted('dev.run', DevelopmentRunPlan)
    locator = MatrixSelectedDevelopmentProduct('binding.disclosed.prepared-source', 'unexecuted/disclosed',
        _unexecuted('dev.packet', AuthoredRecursiveWave), run, _unexecuted('dev.plan', DevelopmentExecutionPlan),
        run.object_id, 'task.disclosed.nominate', _unexecuted('dev.receipt', CanonicalTaskReceipt),
        publication.logical.logical_artifact_id, nomination.identity, publication)
    native = r.prior.MatrixFiniteDtTrainingLocator('unexecuted/disclosed/native', 'run.disclosed.native',
        _unexecuted('native.packet', AuthoredRecursiveWave), _unexecuted('native.plan', DevelopmentExecutionPlan))
    # These exact values are disclosed mathematical control examples, not a
    # projection from an executed DEV graph. Real acceptance reconstructs all
    # source/receipt rows through certify_prepared_source_instrument.
    controls = tuple(sorted((replace(disclosed_control(bank, source), group_id='group.disclosed.prior-dev')
        for _, source in bank.source_arms()), key=lambda row: row.source.object_id))
    roles = ('CALIBRATION', 'EVALUATION', 'TRANSFER_NEARBY', 'TRANSFER_SHIFTED')
    return r.MatrixPreparedInstrumentCertificate('certificate.disclosed.prepared-source', locator, native,
        _unexecuted('native.request', train.NativeTrainingAcquisitionRequest),
        _unexecuted('native.acquisition', train.NativeTrainingAcquisitionSeal),
        scheduled.identity(bank.reservation), opportunity.identity, bank.input_commitments.record,
        ('group.disclosed.prior-dev',), controls, (1,), (2,),
        tuple((role, _unexecuted('future.' + role.lower(), ScheduledResponseSelection)) for role in roles),
        bank.identity, bank.group_ids, InformationCutoff('cutoff.disclosed.prepared-source',
            bank.source_arms()[0][1].coordinate.clock_id, CausalPhase.PREPARATION, None))


def test_prepared_instrument_requires_exercised_recipe_start_and_every_actual_control(confirmation, opportunity):  # noqa: F811
    bank = prepared_bank(confirmation)
    cert = disclosed_certificate(bank, opportunity)
    assert r.prepared_instrument_controls_supported(bank, cert)
    assert decode_canonical_bytes(cert.canonical_bytes(), type(cert), maximum_bytes=None) == cert
    first, *rest = cert.controls
    for damage in ({'numerical_pass': False}, {'frame_controls_pass': False}, {'frame_controls_violated': True, 'frame_controls_pass': False},
            {'response_controls_pass': False}, {'response_control_count': first.response_control_count - 1}):
        changed = replace(cert, controls=(replace(first, **damage), *rest))
        assert not r.prepared_instrument_controls_supported(bank, changed)
    nonuse = replace(first, frame_controls_pass=False, response_controls_pass=False, response_control_count=0,
        causal_disposition='NO_ORIGIN', response_disposition='NO_ORIGIN')
    assert not r.prepared_instrument_controls_supported(bank, replace(cert, controls=(nonuse, *rest)))
    # Neither another literal state nor a new recipe ID is evidence it was run.
    changed_initial = replace(first.initial, array_artifact=replace(first.initial.array_artifact, sha256='f' * 64))
    assert not r.prepared_instrument_controls_supported(bank, replace(cert, controls=(replace(first, initial=changed_initial), *rest)))
    assert not r.prepared_instrument_controls_supported(bank, replace(cert, controls=(replace(first,
        recipe=replace(first.recipe, object_id=first.recipe.object_id + '.unexercised')), *rest)))
    assert nonuse.score in replace(cert, controls=(nonuse, *rest)).original_evidence_links


def test_prepared_source_preserves_nonuse_and_rejects_invented_completed_controls(confirmation, opportunity):  # noqa: F811
    bank = prepared_bank(confirmation)
    cert = disclosed_certificate(bank, opportunity)
    row = cert.controls[0]
    with pytest.raises(ValueError, match='adverse/nonuse'):
        replace(row, response_disposition='NO_ORIGIN')
    with pytest.raises(ValueError, match='actual.*future-panel'):
        replace(cert, original_future_panels=cert.original_future_panels[:-1])
    no_origin = tuple(replace(value, frame_controls_pass=False, response_controls_pass=False,
        response_control_count=0, causal_disposition='NO_ORIGIN', response_disposition='NO_ORIGIN') for value in cert.controls)
    assert not r.prepared_instrument_controls_supported(bank, replace(cert, controls=no_origin))
    assert tuple(value.response_disposition for value in no_origin) == ('NO_ORIGIN',) * len(cert.controls)


def test_installed_prepared_methods_declare_every_real_phase_specific_operand():
    from empirical_lawhood.runtime.candidate_compiler import _ALLOWED_STAGE_KINDS
    declarations = bindings.gate_declarations()
    assert len(declarations) == 12 and len({value.capability_key for value in declarations}) == 12
    for phase in ('E5_CONFIRMATION', 'E6_TRANSFER'):
        kinds = bindings.input_kinds(phase)
        assert len(kinds) == 9 and {'source', 'preparation', 'assay', 'numerical', 'original-reservation'} <= set(kinds)
        assert kinds['numerical'] is MatrixParameterNumericalDesign
        for kind in r.GATES:
            declaration = bindings.gate_declaration(kind, phase)
            assert declaration.manifest().kind in _ALLOWED_STAGE_KINDS[declaration.stage]
            assert {value.port_id: value.payload_schema for value in declaration.input_ports} == {
                name: record.SCHEMA for name, record in kinds.items()}
            assert not declaration.execution_properties.native_effect
            with pytest.raises(PermissionError, match='current API custody'):
                bindings.prepare_for_invocation(object(), declaration.runner_factory())


def test_public_prepared_source_first_stop_is_static_and_four_worker_selected(tmp_path):
    from empirical_lawhood.api.experiment_preparation import load_experiment_specification, prepare_experiment
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
    specification = public.MatrixPreparedSourceQualificationSpecification('specification.disclosed.prepared-source',
        _unexecuted('selection.prepared-source', public.MatrixPreparedSourceQualificationSelection), 4)
    path = tmp_path / 'prepared-source-specification.json'
    path.write_bytes(specification.canonical_bytes())
    actual = load_experiment_specification(path)
    assert actual == specification
    report = prepare_experiment(actual, execution=ExecutionSelection(workers=4))
    assert not report.executable and report.census.native_effect_count == 0
    assert tuple(value.source_key for value in report.dependencies) == ('selection',)


def test_prepared_roster_keeps_hold_recipe_nested_units_and_actual_metadata_owner(confirmation):  # noqa: F811
    from empirical_lawhood.api.matrix_finite_dt_dataset_metadata import select_rows_owner, dataset_registries
    from empirical_lawhood.kernel.authority import ResourceBudget
    bank = prepared_bank(confirmation)
    rows = rows_owner.MatrixPreparedPendingSourceRows.from_bank(bank, bank, record_id='rows.disclosed.prepared-source')
    rule = rows_owner.MatrixPreparedSourceValidationRule('rule.disclosed.prepared-source', bank.identity, bank.identity, rows.identity)
    rows_owner.validate_source_rows(bank, bank, rows, rule)
    assert len(rows.rows) == 2 * len(bank.group_ids)
    assert {value.arm_id for value in rows.rows} == set(dict(bank.sources.recipes))
    assert all(value.invalid_disposition == 'ASSIGNED_NATIVE_ACQUISITION_NOT_YET_OBSERVED' for value in rows.rows)
    with pytest.raises(ValueError, match='complete current source'):
        rows_owner.validate_source_rows(bank, bank, replace(rows, rows=rows.rows[:-1]), rule)
    assert select_rows_owner(type(rows)) is rows_owner
    registry, datasets = dataset_registries(ResourceBudget(1, 1024**3, 0, None, 1024**2, 1024**2),
        maximum_rows=len(rows.rows), row_kind=type(rows))
    assert registry.capabilities and datasets.inspectors[0].capability_key.startswith(r.NAMESPACE)
    for row_kind in (None, SimpleNamespace):
        with pytest.raises(TypeError, match='exact installed source row family'):
            select_rows_owner(row_kind)


def test_prepared_pending_metadata_uses_actual_installed_inspector_verifier_and_byte_replay(tmp_path, confirmation):  # noqa: F811
    from empirical_lawhood.api.matrix_finite_dt_source_pipeline import _read_rows, authenticate_finite_dt_source_materialization
    from tests.test_matrix_finite_dt_source_production import _materialization
    from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case
    case = fresh_training_metadata_case(tmp_path)
    bank = prepared_bank(confirmation)
    future = SimpleNamespace(namespace='prepared.metadata.disclosed', writer=case.plane, bank=bank, programme=bank,
        cutoff=InformationCutoff('cutoff.prepared.metadata', bank.source_arms()[0][1].coordinate.clock_id, CausalPhase.PREPARATION, None))
    materialized, rule = _materialization(future, rows_module=rows_owner)
    assert type(materialized.rows) is rows_owner.MatrixPreparedPendingSourceRows
    assert type(materialized.verification) is rows_owner.MatrixPreparedSourceVerification
    assert materialized.verification.row_count == len(bank.source_arms())
    assert materialized.verification.physical_unit_count == len(bank.group_ids)
    raw, _ = _read_rows(case.plane, materialized.output_publication, materialized.rows)
    assert raw == materialized.rows.canonical_bytes()
    rows_owner.validate_source_rows(bank, bank, materialized.rows, rule)
    profile, registry = materialized.config.profile, materialized.config.dataset_registry
    unsupported = 'unsupported-pending-source-format'
    edge = replace(profile.transform_edges[0], source_format_profile_id=unsupported,
        destination_format_profile_id=unsupported)
    changed = replace(materialized.config,
        profile=replace(profile, source_format_profile_id=unsupported, transform_edges=(edge,)),
        dataset_registry=replace(registry, inspectors=(), evidence_verifiers=()))
    with pytest.raises(PermissionError, match='actual installed pending inspector'):
        authenticate_finite_dt_source_materialization(writer=case.plane, programme=bank, bank=bank,
            rows=materialized.rows, rule=rule,
            pipeline=SimpleNamespace(pipeline_config=changed, receipt=materialized.config.assess()),
            source_publication=materialized.source_publication, output_publication=materialized.output_publication,
            verification=materialized.verification, verification_publication=materialized.verification_publication)


def prepared_public_case(tmp_path, bank, certificate, writer):
    """Actual complete public compiler/prepare contract with disclosed TEST pins.

    The certificate has deliberately unexecuted locators. This helper does not
    claim actual certificate admission, issue or execution; that owner must
    refuse until an original completed E5 DEV run is supplied.
    """
    from decimal import Decimal
    from pathlib import Path
    from unittest.mock import patch
    from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineEvidence
    from empirical_lawhood.api.matrix_finite_dt_source_pipeline import publish_finite_dt_source_metadata
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.api.recursive_prospective_authoring import preview_recursive_prospective_candidate
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import _source_projection
    from empirical_lawhood.kernel.authority import ResourceBudget
    from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
    from empirical_lawhood.planning.evidence_profiles import EvidenceWorldKind, bind_profile_selection, build_observation_evidence_world_registry
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
    from empirical_lawhood.runtime.experiment_resources import bind_execution_resources
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs, RecursiveProspectiveOperand
    from tests import matrix_selected_source_predecessor as existing
    from tests.experiment_entry_support import standard_authoring_for_draft
    from tests.matrix_selected_e4_public_fixture import _source_admissions
    from tests.test_matrix_finite_dt_source_production import _materialization, _source_test_template
    namespace = 'prepared.public.disclosed'
    future = SimpleNamespace(namespace=namespace, writer=writer, bank=bank, programme=bank, cutoff=certificate.cutoff)
    materialized, rule = _materialization(future, rows_module=rows_owner)
    profiles = build_observation_evidence_world_registry()
    world, = (value for value in profiles.world_profiles if value.world_kind is EvidenceWorldKind.DETERMINISTIC_SIMULATOR)
    evidence_profile = bind_profile_selection(selection_id='selection.source.' + namespace, draft_id='draft.' + namespace,
        registry=profiles, world_profile_id=world.profile_id, objective_profile_id='objective.observation-order', requested_rungs=())
    budget = ResourceBudget(1, 2 * 1024**3, 0, None, 128 * 1024**2, 64 * 1024**2)
    scope = r.MatrixPreparedSourceScope('scope.' + namespace, bank.identity, bank.sources.closure.identity,
        bank.sources.identity, bank.assay.identity, bank.sources.closure.numerical_scope, scheduled.identity(bank.reservation),
        certificate.identity, certificate.cutoff, bank.group_ids, materialized.config.profile, materialized.config.assess(),
        evidence_profile, materialized.verification.identity, materialized.verification.identity, budget)
    metadata = publish_finite_dt_source_metadata(writer=writer, scope=scope, materialization=materialized,
        output_directory=Path(writer.root.contract.canonical_path) / 'prepared-public-controls' / namespace / 'metadata')
    operands = {'scope':scope, 'bank':bank, 'source':bank.sources.closure, 'preparation':bank.sources,
        'original-reservation':bank.reservation, 'assay':bank.assay, 'numerical':bank.specification.selection.numerical_design,
        'cutoff':scope.cutoff, 'certificate':certificate}
    training = UnitAllocation('allocation.source-contract.' + namespace, (certificate.native_training_request,),
        tuple(IndependentUnit(group, certificate.native_training_request.object_id, 'family.disclosed-control', ('fine','primary'), True)
            for group in certificate.development_group_ids),
        tuple(UnitRoleAssignment(group,'development') for group in certificate.development_group_ids))
    metadata_programme = SimpleNamespace(group_ids=bank.group_ids,
        cases=tuple(SimpleNamespace(root_id=value.root_id) for value in bank.sources.closure.descriptors),
        design=SimpleNamespace(confidence=Decimal('.95')))
    with patch.object(existing, 'original_preparation', return_value=SimpleNamespace(root=_source_test_template(), training_allocation=training)), patch.object(existing, 'KEY', r.NAMESPACE + '.' + bank.phase.lower()):
        root = existing._source_root(object(), metadata_programme, scope, namespace=namespace,
            budget=ResourceBudget.aggregate((budget,) * (len(r.GATES) + 3)))
    terminals = tuple((name,budget) for name in ('adjudicate','pipeline','qualification'))
    draft, records, qualification, result = public.compose_source_draft(scope=scope, scientific_operands=operands,
        pipeline=materialized.config, root=root, campaign=root.campaign, draft_id='draft.' + namespace, terminal_budgets=terminals,
        operand_access={name: (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
            if name in ('bank', 'source', 'preparation') else (OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
            for name in operands})
    source_configs, qualifications = _source_admissions(draft, records, (), root=root, prefix=namespace,
        observation_operator=bank.assay.identity)
    draft = _source_projection(draft, SimpleNamespace(source_configs=source_configs, qualifications=qualifications),
        {value.logical_artifact_id:dict(records)[value.input_id].VERSION for value in draft.external_inputs})
    project = Path(__file__).resolve().parents[1]
    registrations, registry, codecs = operation_catalog()
    implementation = implementation_binding(project)
    compilation = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit=implementation.observed_git_head, qualifications=qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs, output_codecs=codecs,
        implementation_sha256=implementation.code_sources_sha256)
    standard, formal = standard_authoring_for_draft(compilation.candidate_draft, compilation.candidate_context,
        formal_method_capability_key=bindings.gate_declaration(r.GATES[0], bank.phase).capability_key)
    inputs = tmp_path / 'prepared-source-inputs'
    inputs.mkdir()
    paths=[]
    for external_id, record in records:
        external, = (value for value in draft.external_inputs if value.input_id == external_id)
        path = inputs / (record.fingerprint() + '.json')
        path.write_bytes(record.canonical_bytes())
        paths.append((external.logical_artifact_id,path))
    for config in source_configs:
        path = inputs / (config.fingerprint() + '.json')
        path.write_bytes(config.canonical_bytes())
        paths.append((config.fingerprint(),path))
    design = RecursiveProspectiveDesignInputs('prospective.' + namespace, draft, standard.entry_package,
        formal.formal_methods, formal.source_inventories, qualifications, draft.prospective_draft.design_inputs,
        tuple(sorted((RecursiveProspectiveOperand(value.logical_artifact_id, value.expected_content_sha256,
            value.maximum_size_bytes, value.payload_schema, value.media_type, value.outcome_access, value.visibility_ceiling)
            for value in draft.external_inputs), key=lambda value:value.logical_artifact_id)))
    preview = preview_recursive_prospective_candidate(design_inputs=design, project_root=project, artifact_writer=writer,
        input_bindings=tuple(paths))
    controls=SimpleNamespace(workers=4, memory_bytes_per_task=budget.memory_bytes,
        source_bytes_per_task=budget.source_scan_bytes, output_bytes_per_task=budget.output_bytes)
    authoring=design.bind_resources(bind_execution_resources(existing._resources(draft,controls,namespace), issued_extensions=preview.issued_extensions))
    support=bank.exposure_support
    selection=public.MatrixPreparedSourceQualificationSelection('selection.' + namespace,scope,bank,bank.reservation,
        certificate,materialized.rows,rule,materialized.source_publication,materialized.output_publication,
        materialized.verification,materialized.verification_publication,materialized.config,authoring,
        tuple(sorted(source_configs,key=lambda value:value.fingerprint())),support,metadata,terminals)
    specification=public.MatrixPreparedSourceQualificationSpecification('specification.' + namespace,selection.identity,4)
    execution=ExecutionSelection(4,'main-locked',ObjectIdentity.from_record('recursive-member.implementation',implementation),writer.root.contract.canonical_path)
    preparation=public.prepare(specification,scientific_inputs={'source':public.source_allocation(selection)},method_inputs=selection,execution=execution)
    return SimpleNamespace(selection=selection,specification=specification,preparation=preparation,records=records,
        compilation=compilation,result=result,qualification=qualification,evidence=MatrixSourcePipelineEvidence(
            'evidence.' + namespace,materialized.config,scope.pipeline_receipt,qualification,evidence_profile))


def test_disclosed_prepared_source_projection_compiles_but_public_bootstrap_refuses_missing_locators(tmp_path, confirmation, opportunity):  # noqa: F811
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, load_experiment_specification, prepare_experiment
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
    from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case
    (tmp_path / 'training').mkdir()
    training=fresh_training_metadata_case(tmp_path / 'training')
    bank=prepared_bank(confirmation)
    case=prepared_public_case(tmp_path,bank,disclosed_certificate(bank,opportunity),training.plane)
    assert case.preparation.executable and len(case.preparation.draft.operations)==len(r.GATES)+3
    for config in r.gate_configs(case.selection.scope):
        node=public.node_id(case.selection.scope,config.gate_kind.value.lower())
        assert {edge.consumer_input_id for edge in case.preparation.draft.links if edge.consumer_node_id==node}==set(bindings.input_kinds(bank.phase))
    public.validate_instance(specification=case.specification,allocation=case.preparation.allocation,draft=case.preparation.draft,
        source_records=case.preparation.design_records)
    copied=tmp_path/'copied-prepared-source'
    copied.mkdir()
    (copied/'selection.json').write_bytes(case.selection.canonical_bytes())
    selector=ExperimentFileInputSelection('sources.prepared.disclosed',public.PROTOCOL_ID,
        (ExperimentInputBinding('selection',case.selection.identity,'selection.json',len(case.selection.canonical_bytes())),),())
    (copied/'sources.json').write_bytes(selector.canonical_bytes())
    (copied/'specification.json').write_bytes(case.specification.canonical_bytes())
    loaded=load_experiment_specification(copied/'specification.json')
    # The same exact mathematical projection remains reproducible. The
    # intentionally unexecuted locator fixture cannot supply public custody.
    cold=prepare_experiment(loaded,scientific_inputs={'source':public.source_allocation(case.selection)},
        method_inputs=case.selection,execution=case.preparation.execution)
    assert cold==case.preparation
    with pytest.raises(PermissionError,match='companion census'):
        load_experiment_inputs(loaded,copied/'sources.json',artifact_writer=training.plane)


def test_pure_certificate_does_not_bypass_actual_original_dev_or_native_custody(tmp_path, confirmation, opportunity):  # noqa: F811
    from empirical_lawhood.api.matrix_prepared_source_runtime import authenticate_prepared_source_certificate
    from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case
    case = fresh_training_metadata_case(tmp_path)
    bank = prepared_bank(confirmation)
    with pytest.raises((FileNotFoundError, PermissionError, ValueError)):
        authenticate_prepared_source_certificate(writer=case.plane, certificate=disclosed_certificate(bank, opportunity), bank=bank, maximum_source_bytes=128 * 1024**2)


def test_actual_consumer_must_use_exact_qualified_source_assay_and_future_panels(confirmation):  # noqa: F811
    from hashlib import sha256
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPublicSource
    from empirical_lawhood.api.matrix_prepared_source_runtime import _validate_consumer_programme
    bank = prepared_bank(confirmation)
    point = replace(confirmation.point_design, sources=tuple(sorted(((arm, MatrixPreparedPublicSource.from_source(source))
        for arm, source in bank.source_arms()), key=lambda row: row[1].source.object_id)))
    consumer = replace(confirmation, sources=bank.sources, point_design=point)
    _validate_consumer_programme(bank, consumer)
    group, panels = consumer.panels[0]
    changed = tuple(replace(panel, streams=tuple(replace(stream,
        digest_sha256=sha256(('DISCLOSED.SUBSTITUTED.CONSUMER.' + group + stream.purpose).encode()).hexdigest())
        for stream in panel.streams)) if panel.role == 'INDEPENDENT_FUTURE' else panel for panel in panels)
    substituted = replace(consumer, panels=((group, changed), *consumer.panels[1:]))
    substituted.__post_init__()  # A valid standalone consumer, but another commitment.
    with pytest.raises(PermissionError, match='consumer|panel|assay'):
        _validate_consumer_programme(bank, substituted)
    altered_assay = replace(consumer, assay=replace(consumer.assay,
        native_reference_tolerance=consumer.assay.native_reference_tolerance * 2))
    with pytest.raises(PermissionError, match='consumer|panel|assay'):
        _validate_consumer_programme(bank, altered_assay)


def test_e6_prepared_cutoffs_keep_both_original_regime_clocks_and_refuse_invalid_mapping(transfer):  # noqa: F811
    from decimal import Decimal
    bank=prepared_bank(transfer)
    sources=tuple(source for _,source in bank.source_arms())
    assert len({source.coordinate.clock_id for source in sources})==2
    anchor=InformationCutoff('cutoff.disclosed.actual-e6-clocks',sources[0].coordinate.clock_id,
        CausalPhase.PREPARATION,Decimal(0))
    original=anchor.canonical_bytes()
    actual=r.prepared_source_cutoffs(sources,anchor)
    assert {value.clock_id for value in actual}=={source.coordinate.clock_id for source in sources}
    assert anchor in actual and anchor.canonical_bytes()==original
    assert all(value.coordinate==Decimal(0) and value.phase is CausalPhase.PREPARATION for value in actual)
    assert decode_canonical_bytes(original,InformationCutoff,maximum_bytes=None)==anchor
    for change,message in (({'clock_id':'clock.foreign-e6-source'},'outside.*bank'),
            ({'phase':CausalPhase.ACTION_REQUESTED},'pre-action'),
            ({'coordinate':Decimal(-1)},'handoff'),
            ({'coordinate':max(source.coordinate.physical_time(source.total_ticks) for source in sources)+Decimal(1)},'handoff')):
        with pytest.raises(ValueError,match=message):
            r.prepared_source_cutoffs(sources,replace(anchor,**change))
    # The actual native view owner rejects a foreign unit before a source
    # coordinate can exist. Do not bypass that contract to manufacture a
    # supposedly supported mixed-unit source for the cutoff helper.
    for view in (sources[-1].primary_view,sources[-1].fine_view):
        with pytest.raises(ValueError,match='one dimensionless Langevin clock'):
            replace(view,time_unit='different-physical-time-unit')


def test_e6_source_scientific_root_retains_each_exact_original_physical_cutoff(transfer,opportunity):  # noqa: F811
    from decimal import Decimal
    from empirical_lawhood.api.domain_composition.matrix_prepared_source_assembly.assembly import source_root_from_e3
    from empirical_lawhood.kernel.authority import ResourceBudget
    from empirical_lawhood.kernel.experiments import validate_experiment_against_system
    from tests.test_matrix_finite_dt_source_production import _source_test_template
    bank=prepared_bank(transfer)
    certificate=disclosed_certificate(bank,opportunity)
    sources=tuple(source for _,source in bank.source_arms())
    original=_source_test_template()
    clocks={value.clock_id:value for value in original.system.clocks}
    for source in sources:
        clocks[source.coordinate.clock_id]=replace(original.system.clocks[0],
            clock_id=source.coordinate.clock_id,time_unit=source.primary_view.time_unit,
            nominal_period=source.primary_view.timestep)
    original=replace(original,system=replace(original.system,clocks=tuple(clocks[key] for key in sorted(clocks))))
    cutoff=certificate.cutoff
    root=source_root_from_e3(original=original,programme=bank,bank=bank,certificate=certificate,cutoff=cutoff,
        computability=original.experiment.obligations.computability,budget=ResourceBudget(1,1,0,1,1,1),
        namespace='disclosed.two-regime-source-root',scientific_pins=(bank.identity,certificate.identity),
        confidence=Decimal('.95'),discrepancy_tolerance=Decimal('.001'))
    validate_experiment_against_system(root.experiment,root.system)
    assert root.experiment.information_cutoffs==r.prepared_source_cutoffs(sources,cutoff)
    assert {value.clock_id for value in root.experiment.information_cutoffs}=={source.coordinate.clock_id for source in sources}
    assert root.experiment.obligations.support.information_cutoff_id==cutoff.cutoff_id
    assert cutoff in root.experiment.information_cutoffs and certificate.cutoff==cutoff
    assert all(value.information_cutoff==cutoff for value in root.design_inputs)
