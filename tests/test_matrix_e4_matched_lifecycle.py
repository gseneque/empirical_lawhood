# SPDX-License-Identifier: MPL-2.0
"""Exposed DEV16/CAL20/CONF32 controls using the actual public scientific owners.

Original case/feature/score pins are disclosed software premises. No fixture
asserts native acquisition, protected access, sampling authority or freshness.
"""
from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_primary_family import AMENDED_PRIMARY_FAMILY
from empirical_lawhood.adapters.methods.matrix_factor_response.curve_contract import CURVE_RELATION_LOSS_RULE, MECHANISM_FEATURES
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_science as dev
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as p
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as method
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
from empirical_lawhood.adapters.methods.matrix_scheduled_history import e4_structural_prediction as relation
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.experimental_selection import WholeUnitFold
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experimental_factorial import PairInteractionScale
from tests.test_matrix_e4_matched_relation import causal
from tests.test_matrix_matched_protected_e3 import original_case, matched_e3_products  # noqa: F401
from tests.test_matrix_selected_e3_e4_bridge import build_selected_bridge, transfer  # noqa: F401
from tests.test_matrix_selected_e4_fixtures import build_selected_e4_populations


def pin(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, sha256(name.encode()).hexdigest())


def causal_values(factors, family, *, curve_primary):
    values = causal(factors, family)
    return tuple(sorted((*values, *((name, D('.001')) for name in MECHANISM_FEATURES)))) if curve_primary else values


@pytest.fixture(scope='module')
def populations(matched_e3_products, transfer, tmp_path_factory):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_package import ConfiguredMatrixSelectedFrozenPackage
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
    f = matched_e3_products
    package = ConfiguredMatrixSelectedFrozenPackage('test.e4.original-e3', f.specification, f.allocation, f.joined,
        f.models, f.frozen, f.calibration, f.sealed,
        tuple(sorted((*f.allocation.unit_ids('calibration'), *f.allocation.unit_ids('evaluation')))))
    bridge = build_selected_bridge(transfer, tmp_path_factory,
        public_package=ConfiguredMatrixSelectedPublicPackage.from_package(package))
    return build_selected_e4_populations(bridge, counts=(16, 20, 32),
        family_counts={'DEV': (4, 4, 4, 4), 'CAL': (0, 4, 7, 9), 'CONF': (5, 9, 10, 8)})


def observations(programme, bank, *, export=None, calibration=None, missing_groups=()):
    protected = type(programme) is p.SelectedE4PhaseProgramme
    prefix_type = native.SelectedE4ProtectedCausalPrefix if protected else r.SelectedE3E4CausalPrefix
    account_type = native.SelectedE4ProtectedAccountSeal if protected else r.SelectedE3E4AccountSeal
    feature_type = native.SelectedE4ProtectedFeature if protected else r.SelectedE3E4Feature
    physical_type = native.SelectedE4ProtectedMechanicalForecast if protected else r.SelectedE3E4MechanicalForecast
    results, rows, seals = [], [], []
    index = bank.source_index()
    for case in programme.cases:
        source = bank.source(case.root_id, index=index)
        missing = case.independent_group_id in missing_groups
        prefix_pin, account_pin = pin('causal.' + case.root_id, prefix_type), pin('account.' + case.root_id, account_type)
        prefix = p.SelectedE4PrefixProjection('prefix-projection.' + case.root_id, prefix_pin, case.source,
            source.root.root, source.policy.cutoff_tick, '2' * 64, 'AVAILABLE')
        feature = p.SelectedE4CausalFeatureProjection('feature-projection.' + case.root_id, account_pin,
            pin('feature.' + case.root_id, feature_type), case.source, prefix_pin, case.root_id,
            case.independent_group_id, case.information_cutoff.clock_id, case.information_cutoff.coordinate,
            'AVAILABLE', causal_values(case.factor_values, case.family_id,
                curve_primary=bank.forecast_design.package.specification.is_curve_primary),
            pin('physical.' + case.root_id, physical_type), D('.001'))
        original_points = bank.forecast_design.package.predict(values=feature.values, disposition=feature.disposition)
        seal = None if export is None else export.models.forecast(programme, case, record_id='forecast.' + case.root_id,
            feature=feature, calibration=calibration)
        if seal is not None:
            seals.append(seal)
        # Synthetic targets are supplied only after the actual forecast owner.
        errors = (None if missing else D('.02'),) * 58
        with localcontext() as context:
            context.prec = 60
            logs = tuple(None if value is None else (1 + value).ln() for value in errors)
        projected = p.SelectedE4ScoreProjection('score-projection.' + case.root_id, pin('score.' + case.root_id, ScheduledResponseScore),
            case.source, case.root_id, case.independent_group_id, case.role, programme.criterion, prefix_pin, account_pin,
            'UNEVALUABLE' if missing else 'FINITE', not missing, logs, 'MATCHED_FACTOR58', errors)
        unentered = r.SelectedE3E4CaseResult.unentered(case, target_contract='MATCHED_FACTOR58')
        if protected:
            result = native.SelectedE4NativeCaseResult(case.root_id, case.source, case.independent_group_id,
                'COMPLETED', 'UNKNOWN' if missing else 'SATISFIED', projected.disposition, logs, original_points,
                account_pin, projected.original, None, (), unentered.native, ('DISCLOSED_SOFTWARE_PREMISES',),
                prefix, projected, seal, source.coordinate, 'MATCHED_FACTOR58', feature)
        else:
            result = replace(unentered, disposition='COMPLETED', numerical_disposition='UNKNOWN' if missing else 'SATISFIED',
                score_disposition=projected.disposition, paired_log_targets=logs, original_log_points=original_points,
                forecast=account_pin, score=projected.original, reason_codes=('DISCLOSED_SOFTWARE_PREMISES',))
        results.append(result)
        rows.append(p.SelectedE4ObservedCase(case.root_id, case.source, case.independent_group_id, source.coordinate,
            prefix, projected, result.disposition, result.numerical_disposition, account_pin,
            None if seal is None else seal.identity, original_points, 'MATCHED_FACTOR58', feature))
    reduction = (native.SelectedE4NativeReduction('reduction.' + programme.programme_id, programme.identity,
        bank.identity, tuple(results), programme.group_ids, None) if protected else dev.reduce_cases(programme,
            tuple(results), record_id='reduction.' + programme.programme_id))
    data = p.SelectedE4ObservedData('data.' + programme.programme_id, programme.identity, reduction.identity, tuple(rows))
    forecasts = p.SelectedE4ForecastBank('forecasts.' + programme.programme_id, programme.identity, tuple(seals)) if protected else None
    return reduction, data, forecasts


@pytest.fixture(scope='module')
def fitted(populations):
    f = populations
    target = relation.E4MatchedRelationTarget('test.e4.target', f.development.criterion)
    selected = relation.E4MatchedRelationSelection('test.e4.selection', D(2), D(2), D(2))
    if f.development_bank.forecast_design.package.specification.is_curve_primary:
        selected = replace(selected, loss=CURVE_RELATION_LOSS_RULE)
    folds = tuple(WholeUnitFold(group, index % 2) for index, group in enumerate(f.development.group_ids))
    declaration = method.SelectedE4RevisionExperimentSpecification('test.e4.declaration', f.development.identity,
        target, None, folds, 2, 5, (), (), (), (), selected)
    specification = method.derive_revision_specification(declaration, f.development)
    reduction, data, _ = observations(f.development, f.development_bank)
    nomination = method.select_revision(specification, f.development, f.development_bank, reduction, data,
        nomination_id='test.e4.fit')
    frozen = method.freeze_revision(f.development, nomination, freeze_id='test.e4.freeze')
    export = p.SelectedE4RevisionExport.from_products(f.development, nomination, frozen, record_id='test.e4.export')
    return SimpleNamespace(populations=f, target=target, specification=specification, reduction=reduction, data=data,
        nomination=nomination, frozen=frozen, export=export)


@pytest.mark.parametrize('damage', ('none', 'receipt', 'disposition', 'freeze', 'access'))
def test_completed_export_reads_original_fit_and_freeze_without_dev_replay(fitted, tmp_path, monkeypatch, damage):
    from empirical_lawhood.api.matrix_programme_export_checkpoints import ProgrammeExportCheckpoints
    from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api import matrix_researcher_programme_e4_lineage as lineage
    from empirical_lawhood.api import selected_e4_native_runtime
    from empirical_lawhood.api.matrix_programme_structural_prediction import programme_structural_prediction
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import MatrixProgrammeObservation
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest, ArtifactProfile, CanonicalTaskReceipt
    from tests.test_recursive_public_service import ROOT, _plane

    plane = _plane(tmp_path / 'saved-revision')
    run_id = 'run.disclosed-saved-revision'
    manifests, rows = {}, []
    for name, record in (('fit', fitted.nomination), ('freeze', fitted.frozen)):
        task_id = 'task.' + name
        relative = 'runs/' + run_id + '/outputs/' + task_id + '/product.json'
        output = plane.write(ArtifactWriteRequest('output.' + name, relative, record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.' + name,
            str(plane.root.resolve(relative, for_write=False).parent.relative_to(plane.root.contract.canonical_path)),
            record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        receipt = CanonicalTaskReceipt('receipt.' + run_id + '.' + task_id + '.attempt-001', run_id,
            task_id, run_id + '.' + task_id + '.attempt-001', 'a' * 40, (),
            (output.materialization,), (output.logical,), (), OperationalStatus.SUCCEEDED, ())
        ExternalTaskReceiptStore(plane).commit(receipt, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
        manifests[relative] = plane.read_manifest(relative)
        rows.append({'schema': record.SCHEMA, 'task_id': task_id, 'relative_path': relative,
            'producing_receipt': ObjectIdentity.from_record(receipt.receipt_id, receipt).to_document(),
            'logical_artifact_id': output.logical.logical_artifact_id, 'sha256': record.fingerprint(),
            'size_bytes': output.materialization.size_bytes})
    report = {'run_id': run_id, 'retained_product_index': rows,
        'scientific_disposition': fitted.nomination.trigger_disposition, 'joint_freeze': fitted.frozen.to_document()}
    if damage == 'receipt':
        rows[0]['producing_receipt'] = rows[1]['producing_receipt']
    elif damage == 'disposition':
        report['scientific_disposition'] = 'FIT_UNAVAILABLE'
    elif damage == 'freeze':
        report['joint_freeze'] = None
    inputs = SimpleNamespace(commitments=SimpleNamespace(namespace='disclosed.saved'),
        scientific_design=SimpleNamespace(e4_structure=SimpleNamespace(prediction=fitted.nomination.relation_fit.selection)))
    observations = {'e4.development': MatrixProgrammeObservation('e4.development',
        {'structure': {'original_programme': fitted.populations.development.to_document()}}, True),
        'e4.revision': MatrixProgrammeObservation('e4.revision', report, True)}
    with plane.read_context() as reading:
        context = MatrixProgrammeProjectionContext(ExperimentProgrammeService(ROOT, reading), None,
            inputs, tmp_path, {}, observations)
        checkpoints = ProgrammeExportCheckpoints.__new__(ProgrammeExportCheckpoints)
        checkpoints.reading, checkpoints.manifests = reading, manifests
        checkpoints.completed = dict.fromkeys(observations)
        accesses = []
        def current():
            accesses.append(True)
            if damage == 'access':
                raise PermissionError('current original access revoked')
        monkeypatch.setattr(selected_e4_native_runtime, 'development_products',
            lambda *args, **kwargs: pytest.fail('completed export replayed DEV'))
        monkeypatch.setattr(lineage, 'programme_revision_read',
            lambda *args, **kwargs: pytest.fail('completed export reopened the revision reader'))
        if damage != 'none':
            with pytest.raises((PermissionError, ValueError)):
                checkpoints.revision_read(context, current)
        else:
            revision = checkpoints.revision_read(context, current)
            assert revision.nomination == fitted.nomination and revision.frozen == fitted.frozen
            actual = programme_structural_prediction(context, revision=revision)
            monkeypatch.setattr(lineage, 'programme_revision_read', lambda context: revision)
            assert canonical_json_document_bytes(actual) == canonical_json_document_bytes(programme_structural_prediction(context))
            assert observations['e4.revision'].revision_trigger == fitted.nomination.trigger_disposition
        assert accesses


def test_actual_matched_public_fit_calibration_confirmation_and_fixed_downstream(fitted, monkeypatch):
    f, populations = fitted, fitted.populations
    assert f.nomination.trigger_disposition == 'FIT_AVAILABLE' and f.export.decision.fit_available
    assert f.nomination.endpoint_fit_calls == 4 * 5 * 58
    assert all(len(model.complete_group_ids) == 16 for model in f.nomination.relation_fit.models)
    cal_programme, cal_bank = populations.calibration, populations.calibration_bank
    cal_reduction, cal_data, cal_forecasts = observations(cal_programme, cal_bank, export=f.export,
        missing_groups=cal_programme.group_ids[:1])
    cal_spec = p.SelectedE4CalibrationSpecification('test.e4.cal-spec', populations.development.identity,
        cal_programme.identity, f.nomination.identity, f.frozen.identity, D('.05'), relation.RELATION_SCORE_RULE)
    calibrated = method.calibrate_revision_public(cal_spec, f.export, cal_programme, cal_bank,
        cal_reduction, cal_data, cal_forecasts, record_id='test.e4.calibration')
    public_cal = p.SelectedE4PublicCalibration.from_calibration(calibrated, record_id='test.e4.public-calibration')
    assert calibrated.rank == 20 and calibrated.revision_radius is calibrated.baseline_radius is None
    assert all(policy.bound_kind == 'UNCALIBRATED' for seal in cal_forecasts.forecasts for policy in seal.policies)
    conf, conf_bank = populations.confirmation, populations.confirmation_bank
    reduction, data, forecasts = observations(conf, conf_bank, export=f.export, calibration=public_cal,
        missing_groups=conf.group_ids[:1])
    factorial_spec = method.SelectedE4FactorialSpecification('test.e4.factorial', conf.identity, f.target,
        'MAX_PAIRED_LOG1P_CUMULATIVE_FACTOR_ERROR58', PairInteractionScale.SIGNED_MEAN_DIFFERENCE, (), None,
        'DESCRIPTIVE_MAIN_PAIR_AGGREGATE_CURVATURE_THREE_WAY_NO_SIGNIFICANCE_TESTS', None, (),
        'REQUIRE_COMPLETE_ASSIGNED_WHOLE_GROUPS', AMENDED_PRIMARY_FAMILY)
    factorial = method.assess_factorial(factorial_spec, conf, conf_bank, reduction, data, assessment_id='test.e4.descriptions')
    original = populations.development_bank.forecast_design.package
    rule = method.SelectedE4MatchedRelationRule('test.e4.rule', 32)
    if f.nomination.relation_fit.selection.is_curve_primary:
        rule = replace(rule, account_rule='FROZEN_SR_BR_CURVE_AFTER_ELIGIBLE_DEV_NO_CONFIRMATION_SELECTION',
            margin_denominator=10)
    spec = method.SelectedE4ProgrammeSpecification('test.e4.programme', original.original_package, r.identity(original.models),
        populations.development.identity, cal_programme.identity, conf.identity, rule, AMENDED_PRIMARY_FAMILY)
    spec.validate(populations.development, cal_programme, conf,
        banks=(populations.development_bank, cal_bank, conf_bank))
    result = method.assess_confirmation_public(spec, conf, conf_bank, f.export, public_cal,
        reduction, data, forecasts, factorial, record_id='test.e4.confirmation')
    assert len(result.groups) == 32 and result.amended_inference.critical_successes == 24
    assert result.amended_inference.unknowns == 1 and not result.amended_inference.criterion_met
    assert not result.family_slots and not factorial.tests
    assert tuple(row.bound_kind for row in result.model_coverage[:2]) == ('UNAVAILABLE',) * 2
    assert all(row.bound_kind == 'INFINITE' and row.covered for row in result.model_coverage[2:])
    assert all(policy.bound_kind == 'INFINITE' and not any(policy.admissions) for seal in forecasts.forecasts for policy in seal.policies)
    downstream = method.nominate_downstream(spec, result, f.export, public_cal, record_id='test.e4.downstream')
    assert downstream.selected == 'REVISION' and downstream.frozen_revision == f.frozen.identity
    assert downstream.calibration == calibrated.identity and downstream.frozen_product.relation_fit == f.nomination.relation_fit.identity
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4PointModels
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import MatrixRevisionSelectedPackage
    payload = SelectedE4PointModels.from_models(f.export.models, record_id='test.e4.downstream-models')
    package = MatrixRevisionSelectedPackage('test.e4.downstream-package', payload, downstream.identity, calibrated.identity,
        public_cal, populations.development_bank.forecast_design.package)
    coordinate = data.cases[0].coordinate
    off_grid = replace(coordinate, primary_view=replace(coordinate.primary_view, bath_temperature=D('1.125')),
        fine_view=replace(coordinate.fine_view, bath_temperature=D('1.125')))
    values = causal_values((D('1.125'), coordinate.primary_view.friction_gamma, coordinate.member.cross_coupling_gamma),
        coordinate.family_id, curve_primary=f.nomination.relation_fit.selection.is_curve_primary)
    actual = payload.predict(off_grid, feature=SimpleNamespace(values=values, disposition='AVAILABLE'))
    expected = dict(relation.relation_point_values(f.nomination.relation_fit, values, 'AVAILABLE',
        factor_values=(D('1.125'), coordinate.primary_view.friction_gamma, coordinate.member.cross_coupling_gamma), family_id=coordinate.family_id))
    assert actual == ('PREDICTED', expected['SR'], expected['BR']) and package.frozen_calibration == public_cal
    assert relation.relation_loss_readout(result.relation_cases, result.relation_decisions)['unknown_group_ids'] == conf.group_ids[:1]
    for record in (f.nomination, f.frozen, f.export, calibrated, public_cal, forecasts.forecasts[0], result, downstream, package):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    with pytest.raises(TypeError, match='original E4 calibration'):
        replace(package, frozen_calibration=None)
    with pytest.raises(ValueError, match='retain the original eligible'):
        replace(downstream, selected='ORIGINAL_E3')
    with pytest.raises((ValueError, TypeError), match='calibration'):
        method.validate_public_forecasts(f.export, conf, data, forecasts)
    # Disclosed post-authentication report operands. This tests the formatter's
    # account provenance and no-refit rule, not current protected authority.
    from contextlib import nullcontext
    from empirical_lawhood.api import matrix_programme_structural_prediction as reporting
    from empirical_lawhood.api import matrix_researcher_programme_e4_lineage, matrix_researcher_programme_lineage
    from empirical_lawhood.api import matrix_programme_products
    monkeypatch.setattr(matrix_programme_products, '_current_grants', lambda *args: lambda: None)
    monkeypatch.setattr(matrix_researcher_programme_e4_lineage, 'programme_revision_read',
        lambda context: matrix_researcher_programme_e4_lineage.MatrixProgrammeRevisionRead(
            'disclosed-fit', 'disclosed-freeze', populations.development, f.nomination, f.frozen, f.export.decision))
    monkeypatch.setattr(matrix_researcher_programme_lineage, '_issued_e4_record', lambda context, phase, schema:
        (calibrated if phase == 'e4.calibration' else downstream, None))
    monkeypatch.setattr(relation, 'fit_relation_values', lambda *args, **kwargs: pytest.fail('a report cannot fit a new relation'))
    context = SimpleNamespace(design=SimpleNamespace(e4_structure=SimpleNamespace(prediction=f.nomination.relation_fit.selection)),
        writer=SimpleNamespace(read_context=lambda: nullcontext()),
        observations={phase: SimpleNamespace(complete=True) for phase in ('e4.revision', 'e4.calibration', 'e4.confirmation')},
        method_inputs=lambda phase: SimpleNamespace(plan=SimpleNamespace(declaration=SimpleNamespace(programme=cal_programme))))
    report = reporting.programme_structural_prediction(context)
    assert report['fit'] == f.nomination.relation_fit.to_document() and report['downstream_account'] == 'REVISION'
    assert tuple(count for _, count in report['calibration']['realised_family_group_counts']) == (0, 4, 7, 9)
    assert tuple(count for _, count in report['confirmation']['realised_family_group_counts']) == (5, 9, 10, 8)


def test_required_absent_model_is_prerequisite_failure_and_never_fallback(fitted):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import MatrixProgrammeObservation, programme_frontier
    f = fitted
    missing = f.populations.development.group_ids[:5]
    reduction, data, _ = observations(f.populations.development, f.populations.development_bank, missing_groups=missing)
    nomination = method.select_revision(f.specification, f.populations.development, f.populations.development_bank,
        reduction, data, nomination_id='test.e4.failed-fit')
    frozen = method.freeze_revision(f.populations.development, nomination, freeze_id='test.e4.failed-freeze')
    export = p.SelectedE4RevisionExport.from_products(f.populations.development, nomination, frozen, record_id='test.e4.failed-export')
    assert nomination.trigger_disposition == 'FIT_UNAVAILABLE' and export.models is None
    assert nomination.relation_fit and not export.decision.fit_available
    observations_map = {'e4.revision': MatrixProgrammeObservation('e4.revision', {}, True, 'FIT_UNAVAILABLE')}
    frontier = programme_frontier(observations_map, downstream_account='REVISION')
    skipped = dict(frontier.unentered)
    assert all(phase in skipped for phase in ('e4.source-cal', 'e4.calibration', 'e4.source-conf', 'e4.confirmation', 'e6'))
    assert set(skipped.values()) == {'UNENTERED_REQUIRED_SR_BR_FIT_UNAVAILABLE'}
