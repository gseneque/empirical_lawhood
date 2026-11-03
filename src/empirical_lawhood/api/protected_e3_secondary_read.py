# SPDX-License-Identifier: MPL-2.0
"""Read exact already-consumed E3 diagnostics inside the existing verified plan.

The caller has authenticated current issue/execution/reveal and all receipts.
This adds no parent read, task invocation, plan compilation or authority cache.
"""
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as legacy
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as configured
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_secondary_readout import secondary_response_projection
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore
from empirical_lawhood.kernel.provenance import ObjectIdentity


def _pin(record):
    return ObjectIdentity.from_record(record.record_id, record)


def consumed_response_rows(*, specification, allocation, calibration, assessment,
        writer, plan, receipts, product_reader, statistical_task_id, custody, configured_edition=False):
    """Join the exact global CAL/CONF inputs to their original root score products."""
    owner = configured if configured_edition else legacy
    outcome_kind = owner.ConfiguredProtectedE3PairedOutcome if configured_edition else owner.ProtectedE3PairedOutcome
    forecast_kind = owner.ConfiguredProtectedE3Forecast if configured_edition else owner.ProtectedE3Forecast
    by_task = {task.task_id: task for task in plan.tasks}

    def consumed_rows():
        for role, operation, terminal in (("calibration", "calibrate", calibration), ("evaluation", "assess", assessment)):
            task_id = statistical_task_id(specification.identity, allocation.identity, operation)
            task = by_task.get(task_id)
            if task is None or task_id not in receipts:
                raise PermissionError("E3 secondary read lacks its actual complete original statistic task")
            consumed = {}
            for kind in (outcome_kind, forecast_kind):
                edges = tuple(edge for edge in task.scientific_inputs if edge.payload_schema == kind.SCHEMA)
                if len(edges) != len(allocation.unit_ids(role)):
                    raise PermissionError("E3 secondary read drops its complete consumed forecast/outcome census")
                values = {}
                for edge in edges:
                    from .configured_e3_retained_read import consumed_parent
                    producer, _, logical, _ = consumed_parent(writer=writer, plan=plan, receipts=receipts, task=task, edge=edge)
                    if logical.payload_schema != kind.SCHEMA:
                        raise PermissionError("E3 secondary read changes the actual consumed typed output")
                    record, publication = product_reader(writer, plan, receipts, producer, kind)
                    unit = record.unit_id if kind is outcome_kind else record.feature.unit_id
                    if unit in values:
                        raise PermissionError("E3 secondary read duplicates one assigned original unit")
                    values[unit] = (record, producer, publication)
                expected_pins = terminal.outcomes if kind is outcome_kind else terminal.forecasts
                if (set(values) != set(allocation.unit_ids(role))
                        or tuple(_pin(values[unit][0]) for unit in allocation.unit_ids(role)) != expected_pins):
                    raise PermissionError("E3 secondary read changes exact terminal consumed forecast/outcome pins")
                consumed[kind] = values
            for unit in allocation.unit_ids(role):
                outcome, producer, outcome_custody = consumed[outcome_kind][unit]
                forecast, _, forecast_custody = consumed[forecast_kind][unit]
                score, score_custody = product_reader(writer, plan, receipts, producer, ScheduledResponseScore)
                yield role, outcome, forecast, score
                custody.append({"role": role, "unit_id": unit, "outcome": outcome_custody,
                    "forecast": forecast_custody, "score": score_custody})
    yield from consumed_rows()


def read_secondary_response(*, specification, allocation, calibration, assessment,
        writer, plan, receipts, product_reader, statistical_task_id, normalized_tolerance, target_origin, configured_edition=False):
    custody = []
    rows = consumed_response_rows(specification=specification, allocation=allocation, calibration=calibration,
        assessment=assessment, writer=writer, plan=plan, receipts=receipts, product_reader=product_reader,
        statistical_task_id=statistical_task_id, custody=custody, configured_edition=configured_edition)
    return secondary_response_projection(specification, allocation, rows,
        normalized_tolerance=normalized_tolerance, target_origin=target_origin), tuple(custody)


def read_matched_response(*, specification, allocation, models, model_freeze, calibrated_freeze,
        calibration, assessment, source_selection, writer, plan, receipts, product_reader, statistical_task_id):
    """Reproduce matched fitting outputs, targets, CAL and CONF from consumed rows.

    The received fitted parameters are replayed on the original causal features;
    fitting, native acquisition and authority never run in this read.
    """
    from hashlib import sha256
    from empirical_lawhood.kernel.serialization import canonical_json_bytes, canonical_value
    from empirical_lawhood.adapters.methods.matrix_factor_response import e3_numerical_methods as numerical
    from empirical_lawhood.adapters.methods.matrix_factor_response import matched_response_prediction as matched

    if not specification.measurement.is_matched:
        raise ValueError('matched response read requires the selected paired58 specification')
    custody, forecasts, outcomes = [], {'calibration': [], 'evaluation': []}, {'calibration': [], 'evaluation': []}
    mechanism = []
    protocols = {row.public_source.root.root_id: row for row in source_selection.protocols}
    sources = {row.root_id: row for row in source_selection.sources}
    all_panels = {ObjectIdentity.from_record(row.panel_id, row): row for row in source_selection.panels}
    rows = consumed_response_rows(specification=specification, allocation=allocation, calibration=calibration,
        assessment=assessment, writer=writer, plan=plan, receipts=receipts, product_reader=product_reader,
        statistical_task_id=statistical_task_id, custody=custody, configured_edition=True)
    for role, outcome, forecast, score in rows:
        root = forecast.feature.public_source.root.root_id
        protocol, source = protocols[root], sources[root]
        panels = tuple(all_panels[pin] for pin in outcome.panels)
        if (outcome.original_score != ObjectIdentity.from_record(score.score_id, score)
                or outcome.original_cells_sha256 != sha256(canonical_json_bytes(score.cells)).hexdigest()
                or outcome.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                or score.error_forecast != _pin(forecast) or score.causal_prefix != forecast.feature.prefix
                or score.source != forecast.feature.public_source.source
                or (score.root_id, score.independent_group_id) != (root, forecast.feature.unit_id)):
            raise PermissionError('MATCHED_E3_READ_ORIGINAL_SCORE_FORECAST_AND_CAUSAL_PARENTS_REQUIRED')
        views, disposition = configured.paired_response_view_values(specification, source, protocol, panels, score)
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_unknown_response import ConfiguredProtectedE3UnknownResponseAvailability
        if score.responses.object_schema == ConfiguredProtectedE3UnknownResponseAvailability.SCHEMA:
            from dataclasses import replace
            if (score.reason_codes != ('UNKNOWN_CONTACT',) or disposition != 'UNEVALUABLE'
                    or any(value is not None for view in views for value in view.errors)):
                raise PermissionError('MATCHED_E3_READ_UNKNOWN_CONTACT_INVENTS_OBSERVED_TARGETS')
            views = tuple(replace(view, dispositions=('UNKNOWN_CONTACT',) * len(view.errors)) for view in views)
        if (outcome.views, outcome.numerical_disposition) != (views, disposition):
            raise PermissionError('MATCHED_E3_READ_COMPLETE_DENSE_TARGET_REDUCTION_DIFFERS')
        expected = configured.forecast_protected_e3(specification, allocation, models,
            model_freeze if role == 'calibration' else calibrated_freeze, forecast.feature,
            role=role, record_id=forecast.record_id, calibration=None if role == 'calibration' else calibration)
        if expected != forecast:
            raise PermissionError('MATCHED_E3_READ_ORIGINAL_FITTED_CURVES_UPPER_BOUNDS_AND_POLICIES_DIFFER')
        forecasts[role].append(forecast)
        outcomes[role].append(outcome)
        if specification.is_curve_primary:
            from .matrix_mechanism_read import configured_e3_mechanism
            mechanism.append({'role': role, **configured_e3_mechanism(writer=writer, plan=plan, receipts=receipts,
                protocol=protocol, outcome=outcome, forecast=forecast, score=score, panels=panels,
                product_reader=product_reader, retention=getattr(source_selection, 'retention', None))})
    recalibrated = configured.calibrate_protected_e3(specification, allocation, models, model_freeze,
        tuple(forecasts['calibration']), tuple(outcomes['calibration']), record_id=calibration.record_id)
    reassessed = configured.assess_protected_e3(specification, allocation, calibrated_freeze,
        tuple(forecasts['evaluation']), tuple(outcomes['evaluation']), record_id=assessment.record_id)
    if recalibrated != calibration or reassessed != assessment:
        raise PermissionError('MATCHED_E3_READ_COMPLETE_CALIBRATION_OR_CONFIRMATION_REDUCTION_DIFFERS')
    loss_rows = []
    for forecast, outcome in zip(forecasts['evaluation'], outcomes['evaluation'], strict=True):
        reasons = numerical.outcome_reasons(specification, outcome)
        loss_rows.append(matched.matched_loss_readout(forecast.feature.unit_id, dict(forecast.log_points), outcome, reasons,
            curve_primary=specification.is_curve_primary))
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_prediction import curve_loss_summary
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_duration import duration_diagnostic_summary, evaluation_median_K
    return canonical_value({'status': 'REPRODUCED',
        'basis': 'ORIGINAL_CONSUMED_FORECASTS_AND_COMPLETE_DENSE_SCORE_CELLS',
        'admission_owner': 'S0', 'losses': tuple(loss_rows),
        'loss_summary': (curve_loss_summary if specification.is_curve_primary else matched.matched_loss_summary)(reassessed.decisions),
        **({'same_bank_mechanism': tuple(mechanism),
            'training_K_diagnostics': tuple((model.method_key, duration_diagnostic_summary(model)) for model in models.models),
            'TRAIN_median_K_confirmation': evaluation_median_K(models.models[0], allocation.unit_ids('evaluation'),
                tuple((outcome.unit_id, outcome.unit_id, matched.paired_factor_targets(outcome),
                    not numerical.outcome_reasons(specification, outcome)) for outcome in outcomes['evaluation']))}
            if specification.is_curve_primary else {}),
        'admission_risk': matched.matched_admission_risk(tuple(forecasts['evaluation']), tuple(outcomes['evaluation']))}), tuple(custody)
