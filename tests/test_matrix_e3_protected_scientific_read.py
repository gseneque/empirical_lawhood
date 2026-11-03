# SPDX-License-Identifier: MPL-2.0
"""Independent public read projections over disclosed immutable science controls.

The statistical and evaluator declarations produce the actual typed products.
These literals, publication receipts and synthetic context establish software
conformance; they supply no genuine sampling warrant or protected authority.
"""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.domain_composition.matrix_protected_response import scientific_read as owner
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.experiment_scientific_read import read_prepared_experiment_science
from empirical_lawhood.api.results import ApiResult, CampaignStatusRequest, OperationStatus
from empirical_lawhood.api.matrix_training_provenance import fitted_training_provenance
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import (
    ArtifactProfile, ArtifactSemanticValidationRegistry, ArtifactWriteRequest, CanonicalTaskReceipt,
)
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
from tests.test_matrix_e3_protected_adjudication import prepared as adjudication_prepared
from tests.test_matrix_e3_statistical_bindings import case as case, fitted as fitted
from tests.test_matrix_e3_statistical_bindings_independent_review import sequence as sequence


class _NoInputs:
    def resolve_input(self, spec):
        raise AssertionError('retained semantic declaration inspection requested scientific inputs')


@pytest.fixture(scope='module')
def readout(case, fitted, sequence):
    current = adjudication_prepared(case, fitted, sequence.assessment)
    result = current.runner.execute(current.context)
    adjudication = decode_canonical_bytes(result.outputs[0].payload, ScientificAdjudicationRecord, maximum_bytes=None)
    # Use the producing declaration/provider's actual immutable output contract.
    # Generic-only manifests here previously hid the completed public reader's
    # missing semantic registry even though all actual workers had succeeded.
    registry = CapabilityRegistry('registry.literal.scientific-read', (current.runner.manifest,))
    factory = current.declaration.provider_factory()
    provider = factory.build_provider(registry=registry, records=(), platform_ports=(ExecutablePlatformPort(
        factory.binding.required_platform_port_keys[0], RecursiveOperationInputPort(_NoInputs())),))
    contract, = provider.output_semantic_contracts(registry)
    registration = contract.artifact_validation_registration(
        logical_artifact_id=adjudication.output_logical_artifact_ids[0], task_id=current.context.task_id,
        output_id=current.context.output_ports[0].output_id)
    writer = case.plane.with_semantic_validation_registry(ArtifactSemanticValidationRegistry.from_registrations(
        registry_id='semantics.literal.scientific-read-producing', registrations=(registration,)))
    product = writer.write(ArtifactWriteRequest(adjudication.output_logical_artifact_ids[0],
        'scientific-read/adjudication.json', adjudication.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json',
        'scientific-read.adjudication', 'scientific-read', adjudication.canonical_bytes(),
        VisibilityCeiling.OUTCOME_VISIBLE, (), OutcomeAccess.EVALUATION_REVEALED,
        semantic_validation=registration.validation))
    receipt = CanonicalTaskReceipt('receipt.literal.scientific-read', adjudication.run_id,
        adjudication.adjudication_task_id, 'attempt.literal.scientific-read', case.provenance.observed_git_head,
        adjudication.input_materialization_ids, (product.materialization,), (product.logical,),
        (), OperationalStatus.SUCCEEDED, ())
    task = current.context.prepared_invocation.execution_task_record
    plan = SimpleNamespace(execution_plan_id='plan.literal.scientific-read', tasks=(task,))
    return SimpleNamespace(calibration=sequence.calibration.record, frozen=sequence.sealed.record,
        assessment=sequence.assessment.record, adjudication=adjudication,
        writer=writer, product=product, task=task, plan=plan, package=SimpleNamespace(registry=registry),
        producing_registration=registration,
        receipts={adjudication.adjudication_task_id: receipt,
            sequence.assessment.receipt.task_id: sequence.assessment.receipt})


def project(case, readout, **changes):
    values = {name: getattr(readout, name) for name in ('calibration', 'frozen', 'assessment', 'adjudication')}
    values.update(changes)
    return owner._scientific_projection(case.inputs.specification, case.allocation,
        **values, execution_plan=readout.adjudication.execution_plan,
        run_id=readout.adjudication.run_id, receipts=readout.receipts)


def test_plain_reader_refuses_actual_declaration_semantics_before_trusted_registration(case, readout):
    logical = readout.product.logical
    assert logical.generic_validation is not None
    assert logical.semantic_validation == readout.producing_registration.validation
    assert logical.semantic_validation.validator_key == 'matrix-e3-protected.adjudicate'
    with pytest.raises(ArtifactIdentityConflict, match='immutable registered semantic validator'):
        owner._product(case.plane, readout.plan, readout.receipts,
            readout.adjudication.adjudication_task_id, ScientificAdjudicationRecord)
    record, _ = owner._product(readout.writer, readout.plan, readout.receipts,
        readout.adjudication.adjudication_task_id, ScientificAdjudicationRecord)
    assert record.canonical_bytes() == readout.adjudication.canonical_bytes()


def test_retained_science_registers_original_semantics_without_current_discovery(case, readout, monkeypatch):
    from empirical_lawhood.api import experiment_preparation, matrix_numerical_provenance, recursive_operations
    from empirical_lawhood.runtime import compiler, recursive_compiler, recursive_provider

    def forbidden(*args, **kwargs):
        raise AssertionError('retained semantic read attempted current compilation, provider or source discovery')

    monkeypatch.setattr(experiment_preparation, 'experiment_protocols', forbidden)
    monkeypatch.setattr(recursive_operations, 'operation_catalog', forbidden)
    monkeypatch.setattr(matrix_numerical_provenance, 'capture_matrix_provenance', forbidden)
    monkeypatch.setattr(recursive_provider.RecursiveOperationDeclaration, 'manifest', forbidden)
    monkeypatch.setattr(recursive_provider.RecursiveOperationProviderFactory, 'build_provider', forbidden)
    monkeypatch.setattr(recursive_compiler, 'compile_recursive_wave', forbidden)
    monkeypatch.setattr(compiler, 'compile_run_plan', forbidden)
    monkeypatch.setattr(compiler, 'compile_preissue_run_plan', forbidden)
    writer = owner._retained_scientific_writer(readout.package, readout.plan, case.plane)
    record, custody = owner._product(writer, readout.plan, readout.receipts,
        readout.adjudication.adjudication_task_id, ScientificAdjudicationRecord)
    assert record.canonical_bytes() == readout.adjudication.canonical_bytes()
    assert custody['logical_artifact'] == readout.product.logical.to_document()
    assert writer.validators is case.plane.validators
    assert writer.semantic_validations.resolve(readout.product.logical.logical_artifact_id,
        readout.product.logical.semantic_validation) == readout.producing_registration.validation


@pytest.mark.parametrize('field,value', (
    ('validator_key', 'foreign.scientific-validator'),
    ('validator_implementation_sha256', 'f' * 64),
))
def test_retained_read_never_adopts_a_published_foreign_validator(case, readout, field, value):
    original = readout.producing_registration
    logical_id = 'scientific-read.foreign.' + field.replace('_', '-')
    altered = replace(original, logical_artifact_id=logical_id,
        validation=replace(original.validation, **{field: value}))
    forged_writer = case.plane.with_semantic_validation_registry(ArtifactSemanticValidationRegistry.from_registrations(
        registry_id='semantics.literal.foreign.' + field.replace('_', '-'), registrations=(altered,)))
    publication = forged_writer.write(ArtifactWriteRequest(logical_id,
        'scientific-read/' + logical_id + '.json', ScientificAdjudicationRecord.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', logical_id, 'scientific-read',
        readout.adjudication.canonical_bytes(), VisibilityCeiling.OUTCOME_VISIBLE, (),
        OutcomeAccess.EVALUATION_REVEALED, semantic_validation=altered.validation))
    task = replace(readout.task, outputs=tuple(replace(output, logical_artifact_id=logical_id)
        for output in readout.task.outputs))
    plan = SimpleNamespace(execution_plan_id='plan.literal.foreign-validator', tasks=(task,))
    receipt = replace(readout.receipts[task.task_id], output_logical_artifacts=(publication.logical,),
        output_materializations=(publication.materialization,))
    writer = owner._retained_scientific_writer(readout.package, plan, case.plane)
    with pytest.raises(ArtifactIdentityConflict, match='semantic validator (identity|implementation) differs'):
        owner._product(writer, plan, {task.task_id: receipt}, task.task_id, ScientificAdjudicationRecord)


def test_scientific_read_retains_all_cal20_conf8_and_adverse_decisions(case, readout):
    report = project(case, readout)
    assert report['scientific_status'] == report['admission_status'] == 'UNEVALUABLE'
    assert report['qualification'] == 'NOT_ESTABLISHED'
    assert report['denominators']['calibration']['assigned_units'] == 20
    assert report['denominators']['confirmation'] == {'assigned_units': 8, 'usable_units': 7,
        'successes': readout.assessment.successes, 'units': list(case.allocation.unit_ids('evaluation'))}
    assert len(report['calibration']['value']['scores']) == 20
    assert len(report['assessment']['value']['decisions']) == 8
    assert not report['assessment']['value']['decisions'][-1]['value']['usable']
    assert 'UNKNOWN_CONTACT' in report['assessment']['value']['decisions'][-1]['value']['reasons']
    assert report['assessment'] == readout.assessment.to_document()
    assert report['adjudication'] == readout.adjudication.to_document()


def test_missing_cal_score_retains_complete_denominator_and_infinite_radius(case, readout):
    scores = (*readout.calibration.scores[:-1], (readout.calibration.scores[-1][0], None, ('UNKNOWN_CONTACT',)))
    calibration = replace(readout.calibration, scores=scores, radius=None)
    frozen = replace(readout.frozen, calibration=owner._identity(calibration))
    assessment = replace(readout.assessment, calibrated_freeze=owner._identity(frozen))
    report = project(case, readout, calibration=calibration, frozen=frozen, assessment=assessment)
    assert report['calibration']['value']['rank'] == 20
    assert report['calibration']['value']['radius'] is None
    assert report['calibration']['value']['scores'][-1][1:] == [None, ['UNKNOWN_CONTACT']]
    assert report['denominators']['calibration']['assigned_units'] == 20
    assert report['denominators']['calibration']['usable_units'] == 19


def test_omitted_calibration_unit_is_refused(case, readout):
    calibration = replace(readout.calibration, scores=readout.calibration.scores[:-1],
        forecasts=readout.calibration.forecasts[:-1], outcomes=readout.calibration.outcomes[:-1])
    with pytest.raises(PermissionError, match='COMPLETE_CALIBRATION'):
        project(case, readout, calibration=calibration)


def test_omitted_confirmation_unit_is_refused_even_when_counts_are_repaired(case, readout):
    assessment = readout.assessment
    decisions = assessment.decisions[:-1]
    assessment = replace(assessment, decisions=decisions, forecasts=assessment.forecasts[:-1],
        outcomes=assessment.outcomes[:-1], coverage=assessment.coverage[:-1],
        coverage_bound_kinds=assessment.coverage_bound_kinds[:-1],
        successes=sum(row.success for row in decisions), usable_units=sum(row.usable for row in decisions))
    with pytest.raises(ValueError, match='complete assigned original denominator'):
        project(case, readout, assessment=assessment)


@pytest.mark.parametrize('change', [
    {'run_id': 'run.literal.substituted'},
    {'required_receipt_ids': ('receipt.literal.substituted',)},
    {'reason_codes': ('SAMPLING_ASSUMPTION_NOT_AUTHENTICATED',)},
])
def test_terminal_adjudication_must_match_actual_execution_and_assessment(case, readout, change):
    with pytest.raises(PermissionError, match='EXACT_TERMINAL_ADJUDICATION'):
        project(case, readout, adjudication=replace(readout.adjudication, **change))


def test_tampered_or_missing_retained_scientific_bytes_refuse(case, sequence):
    original = sequence.assessment
    physical = original.publication.materialization
    path = case.plane.root.resolve(physical.relative_path, for_write=False)
    raw = path.read_bytes()
    try:
        path.write_bytes(raw.replace(b'"criterion_met":false', b'"criterion_met":true'))
        if path.read_bytes() == raw:
            path.write_bytes(raw + b' ')
        with pytest.raises((PermissionError, ValueError, ArtifactIdentityConflict)):
            owner._product(case.plane, None, {original.receipt.task_id: original.receipt},
                original.receipt.task_id, owner.ProtectedE3Assessment)
        path.unlink()
        with pytest.raises((OSError, ArtifactIdentityConflict)):
            owner._product(case.plane, None, {original.receipt.task_id: original.receipt},
                original.receipt.task_id, owner.ProtectedE3Assessment)
    finally:
        path.write_bytes(raw)


def test_protected_read_requires_explicit_current_reveal_before_science(case):
    with pytest.raises(PermissionError, match='REVEAL_AUTHORITY_REQUIRED'):
        owner._authorize(case.plane, None, None)


def test_public_service_uses_registered_scientific_reader_not_status_only(case, readout, monkeypatch, tmp_path):
    from empirical_lawhood.api import generated_experiment_runtime_bindings as bindings
    from empirical_lawhood.api.domain_composition.matrix_protected_response.experiment_binding import EXPERIMENT_RUNTIME_BINDING
    from empirical_lawhood.api import experiment_preparation

    science = project(case, readout)
    calls = []
    def read(**arguments):
        calls.append(arguments)
        return science
    monkeypatch.setattr(bindings, 'EXPERIMENT_RUNTIME_BINDINGS', (replace(EXPERIMENT_RUNTIME_BINDING, read_result=read),))
    def forbidden(*args, **kwargs):
        raise AssertionError('scientific read attempted current source discovery')
    monkeypatch.setattr(experiment_preparation, 'experiment_protocols', forbidden)
    selected = SimpleNamespace(instance=SimpleNamespace(specification=case.inputs.specification.identity),
        association=SimpleNamespace(identity=case.inputs.specification.identity, candidate=case.inputs.specification.identity),
        projection=SimpleNamespace(tasks=('one',)), handoff=SimpleNamespace(projection=SimpleNamespace(tasks=('one',))))
    result = ApiResult('campaign.status', OperationStatus.SUCCEEDED)
    monkeypatch.setattr(ExperimentProgrammeService, '_prospective_context', lambda *args, **kwargs:
        (selected, SimpleNamespace(campaign_status=lambda *args, **kwargs: result)))
    report = ExperimentProgrammeService(tmp_path, case.plane).read(directory=tmp_path,
        request=CampaignStatusRequest('run.literal.statistical'), reveal_authority_id='authority.literal.reveal')
    assert report['scientific_result']['assessment'] == readout.assessment.to_document()
    assert report['scientific_result']['adjudication'] == readout.adjudication.to_document()
    assert calls[0]['reveal_authority_id'] == 'authority.literal.reveal'
    assert calls[0]['allow_partial'] is False
    assert read_prepared_experiment_science(selected=selected, artifact_writer=case.plane,
        run_id='run.literal.statistical', allow_partial=True) == science
    unknown = SimpleNamespace(instance=SimpleNamespace(specification=replace(
        case.inputs.specification.identity, object_version='99.0.0')))
    with pytest.raises(ValueError, match='exact installed specification revision'):
        read_prepared_experiment_science(selected=unknown, artifact_writer=case.plane,
            run_id='run.literal.statistical', allow_partial=True)


@pytest.mark.parametrize('damage', ('tampered', 'missing'))
def test_public_service_refuses_changed_or_missing_scientific_output(case, readout, sequence, monkeypatch, tmp_path, damage):
    """Exercise public dispatch and actual guarded product reads, without issue."""
    from empirical_lawhood.api import generated_experiment_runtime_bindings as bindings
    from empirical_lawhood.api.domain_composition.matrix_protected_response.experiment_binding import EXPERIMENT_RUNTIME_BINDING

    original = sequence.assessment
    def read(**arguments):
        owner._product(arguments['artifact_writer'], None, {original.receipt.task_id: original.receipt},
            original.receipt.task_id, owner.ProtectedE3Assessment)
        return project(case, readout)
    monkeypatch.setattr(bindings, 'EXPERIMENT_RUNTIME_BINDINGS', (replace(EXPERIMENT_RUNTIME_BINDING, read_result=read),))
    selected = SimpleNamespace(instance=SimpleNamespace(specification=case.inputs.specification.identity),
        association=SimpleNamespace(identity=case.inputs.specification.identity, candidate=case.inputs.specification.identity),
        handoff=SimpleNamespace(projection=SimpleNamespace(tasks=('one',))))
    result = ApiResult('campaign.status', OperationStatus.SUCCEEDED)
    monkeypatch.setattr(ExperimentProgrammeService, '_prospective_context', lambda *args, **kwargs:
        (selected, SimpleNamespace(campaign_status=lambda *args, **kwargs: result)))
    programme = ExperimentProgrammeService(tmp_path, case.plane)
    request = CampaignStatusRequest('run.literal.statistical')
    assert programme.read(directory=tmp_path, request=request,
        reveal_authority_id='authority.literal.reveal')['scientific_result']['assessment'] == original.record.to_document()
    path = case.plane.root.resolve(original.publication.materialization.relative_path, for_write=False)
    raw = path.read_bytes()
    try:
        if damage == 'tampered':
            path.write_bytes(raw + b' ')
        else:
            path.unlink()
        with pytest.raises((OSError, ValueError, ArtifactIdentityConflict)):
            programme.read(directory=tmp_path, request=request, reveal_authority_id='authority.literal.reveal')
    finally:
        path.write_bytes(raw)


def test_retained_fit_read_reports_legacy_bank_contract_without_inventing_synthetic_origin(case, fitted, readout):  # noqa: F811
    model, custody = owner._product(case.plane, None, {fitted.models.receipt.task_id: fitted.models.receipt},
        fitted.models.receipt.task_id, owner.ProtectedE3ModelSet)
    provenance = fitted_training_provenance(case.inputs.specification, case.allocation, model, readout.frozen)
    assert provenance["bank_edition"] == "LEGACY_BANKS"
    assert provenance["data_origin"] == "NOT_REESTABLISHED_BY_THIS_READ"
    assert provenance["feature_bank"] == model.training_features.to_document()
    assert provenance["assigned_units"] == len(case.allocation.unit_ids("train"))
    assert provenance["units"] == list(case.allocation.unit_ids("train"))
    assert custody["logical_artifact"] == fitted.models.publication.logical.to_document()
    with pytest.raises(PermissionError, match="EXACT_FITTED_TRAINING"):
        fitted_training_provenance(case.inputs.specification, case.allocation,
            replace(model, record_id=model.record_id + '.foreign'), readout.frozen)
