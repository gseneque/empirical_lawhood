# SPDX-License-Identifier: MPL-2.0
"""Bind the prospective descriptive readout to already authenticated operands.

The enclosing public read owns current access, original native custody and
complete denominators. This module creates no authority or scientific receipt.
"""
from empirical_lawhood.kernel.provenance import ObjectIdentity


def bound_mechanism(*, protocol, source, causal_record, physical_record, response_record,
        causal_arrays, frozen_arrays, response_arrays, panels, numerical_status, feature,
        score, subject_id, group_id, retain_instrument=False):
    from empirical_lawhood.adapters.methods.matrix_factor_response.mechanism_readout import same_bank_mechanism, compact_instrument
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_contract import MECHANISM_FEATURES

    result = same_bank_mechanism(protocol, causal_arrays, frozen_arrays, response_arrays,
        panel_ids=tuple(sorted(panel.panel_id for panel in panels)), numerical_status=numerical_status,
        feature_disposition=causal_record.disposition)
    primary = result['causal_features'][0]
    if feature.disposition == 'AVAILABLE' and (primary.reasons or primary.values != tuple(
            (name, dict(feature.values)[name]) for name in MECHANISM_FEATURES)):
        raise PermissionError('MECHANISM_READ_DIFFERS_FROM_SEALED_PRIMARY_CAUSAL_HESSIAN_FEATURES')
    if not retain_instrument:
        result['instrument'] = compact_instrument(result['instrument'])
    return {'subject_id': subject_id, 'group_id': group_id,
        'source': source, 'protocol': ObjectIdentity.from_record(protocol.protocol_id, protocol),
        'causal_array': causal_record.arrays, 'physical_array': physical_record.arrays,
        'response_array': response_record.arrays,
        'score': ObjectIdentity.from_record(getattr(score, 'score_id', None) or score.record_id, score), **result}


def configured_e3_mechanism(*, writer, plan, receipts, protocol, outcome, forecast, score, panels, product_reader, retention=None):
    """Follow actual score inputs, including their original consumed materializations."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_prefix_records import ConfiguredProtectedE3CausalPrefix
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_records import (
        ConfiguredProtectedE3PhysicalForecast, ConfiguredProtectedE3NativeResponse,
    )
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_preparation import response_task_id
    from empirical_lawhood.api.recursive_qualified_parents import _output_payload
    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_continued_response import ConfiguredE3ContinuedNativeResponse

    from .configured_e3_retained_read import producing_custody
    score_task = response_task_id(protocol.public_source.root.root_id, 'response-score')
    old = producing_custody(writer, plan, score_task)
    read_writer, read_plan, read_receipts = writer, plan, receipts
    if old is not None:
        writer, plan, receipts = old.writer, old.plan, old.receipts
        retention = old.selection.retention
    tasks = {task.task_id: task for task in plan.tasks}
    task = tasks[score_task]
    if task.capability.capability_key == 'matrix-e3-configured-protected.missing-response-score':
        # The enclosing continued-response read has checked the exact original
        # contact and PURE missing products. There is no native response array.
        return {'subject_id': protocol.public_source.root.root_id, 'group_id': forecast.feature.unit_id,
            'source': score.source, 'protocol': ObjectIdentity.from_record(protocol.protocol_id, protocol),
            'score': ObjectIdentity.from_record(score.score_id, score), 'availability': score.responses,
            'status': 'UNKNOWN_CONTACT', 'reason_codes': ('UNKNOWN_CONTACT',),
            'causal_feature': forecast.feature, 'response_array': None, 'instrument': None}

    def consumed(name):
        from .configured_e3_retained_read import consumed_parent
        edges = tuple(edge for edge in task.scientific_inputs if edge.consumer_input_id == name)
        if len(edges) != 1:
            raise PermissionError('MECHANISM_READ_REQUIRES_ORIGINAL_CONSUMED_PRODUCER')
        edge, = edges
        return edge, consumed_parent(writer=writer, plan=plan, receipts=receipts, task=task, edge=edge)

    records = {}
    response_type = ConfiguredProtectedE3NativeResponse if retention is None else ConfiguredE3ContinuedNativeResponse
    for name, kind in (('causal', ConfiguredProtectedE3CausalPrefix), ('physical', ConfiguredProtectedE3PhysicalForecast),
            ('responses', response_type)):
        _, (producer, _, logical, _) = consumed(name)
        if logical.payload_schema != kind.SCHEMA:
            raise PermissionError('MECHANISM_READ_CHANGES_ORIGINAL_TYPED_INPUT')
        records[name] = product_reader(read_writer, read_plan, read_receipts, producer, kind)[0]
    causal, physical, response = (records[name] for name in ('causal', 'physical', 'responses'))
    if retention is not None and (response.continuation != retention.identity
            or plan.source_plan.object_id != retention.continued_run_id):
        raise PermissionError('MECHANISM_READ_CHANGES_RETAINED_RESPONSE_EXECUTION')
    causal_pin = ObjectIdentity.from_record(causal.record_id, causal)
    physical_pin = ObjectIdentity.from_record(physical.forecast_id, physical)
    if (forecast.feature.prefix != causal_pin or forecast.feature.physical_forecast != physical_pin
            or response.causal_prefix != causal_pin or response.physical_forecast != physical_pin
            or response.error_forecast != ObjectIdentity.from_record(forecast.record_id, forecast)
            or response.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or response.source != forecast.feature.public_source.source):
        raise PermissionError('MECHANISM_READ_CHANGES_SEALED_SOURCE_FEATURE_OR_INSTRUMENT')
    arrays = []
    for name, record in (('causal-arrays', causal), ('physical-arrays', physical), ('response-arrays', response)):
        edge, (producer, receipt, logical, source_writer) = consumed(name)
        artifact = record.arrays.array_artifact
        expected_id = artifact.artifact_id
        if retention is not None and name != 'response-arrays':
            if dict(retention.retained_arrays).get(producer) != artifact:
                raise PermissionError('MECHANISM_READ_CHANGES_RETAINED_ORIGINAL_ARRAY_PRODUCER')
            expected_id = ('artifact.' + retention.continued_run_id + '.' + producer + '.arrays'
                if edge.producer_task_id is not None else logical.logical_artifact_id)
        if (logical.logical_artifact_id, logical.content_sha256, logical.payload_schema, logical.media_type,
                logical.outcome_access, logical.visibility_ceiling) != (
                expected_id, artifact.sha256, artifact.payload_schema, artifact.media_type,
                record.arrays.outcome_access, record.arrays.visibility_ceiling):
            raise PermissionError('MECHANISM_READ_CHANGES_ORIGINAL_NAMED_ARRAY')
        arrays.append(decode_matrix_arrays(_output_payload(source_writer, receipt, logical, artifact.size_bytes), record.arrays))
    return bound_mechanism(protocol=protocol, source=response.source, causal_record=causal, physical_record=physical,
        response_record=response, causal_arrays=arrays[0], frozen_arrays=arrays[1], response_arrays=arrays[2],
        panels=panels, numerical_status=outcome.numerical_disposition, feature=forecast.feature, score=score,
        subject_id=protocol.public_source.root.root_id, group_id=forecast.feature.unit_id)


def prepared_mechanism_projection(programme, rows):
    """Keep every assigned arm, and report native-frame map changes against HOLD."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.mechanism_readout import instrument_change, compact_instrument
    from empirical_lawhood.kernel.serialization import canonical_value

    fit = programme.selected_package.models.relation_fit
    if fit is None or not fit.selection.is_curve_primary:
        return {}
    cases = programme.roster.cases
    if set(rows) - {case.case_id for case in cases}:
        raise ValueError('mechanism report adds an unassigned prepared case')
    by_pair = {(case.unit_id, case.arm_id): rows.get(case.case_id) for case in cases}
    changes = []
    for case in cases:
        if case.arm_id == programme.hold_arm_id:
            continue
        baseline, selected = by_pair[case.unit_id, programme.hold_arm_id], by_pair[case.unit_id, case.arm_id]
        changes.append({'unit_id': case.unit_id, 'arm_id': case.arm_id,
            **instrument_change(None if baseline is None else baseline['instrument'],
                None if selected is None else selected['instrument'])})
    compact = {case: {**row, 'instrument': compact_instrument(row['instrument'])} for case, row in rows.items() if row is not None}
    return {'same_bank_mechanism': canonical_value({'assigned_cases': len(cases),
        'cases': tuple({'case_id': case.case_id, 'unit_id': case.unit_id, 'arm_id': case.arm_id,
            'readout': compact.get(case.case_id), 'status': 'FUTURE_UNAVAILABLE' if rows.get(case.case_id) is None else 'READ'} for case in cases),
        'instrument_changes': tuple(changes), 'estimand': 'UNCHANGED_STATE_CONDITIONED_ASSAY_CONSTRUCTION',
        'mechanism_transport': 'DESCRIPTIVE_AFTER_REVEAL_SEPARATE_FROM_FROZEN_PREDICTIVE_TRANSPORT'})}
