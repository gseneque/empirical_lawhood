# SPDX-License-Identifier: MPL-2.0
"""Shared public E3 read projection with explicit version-specific validators.

This verifies retained results independently of the production statistic worker.
Historical and configured facades retain their original arithmetic/identity owners.
"""
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_value
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability
from empirical_lawhood.runtime.experimental_statistics import split_upper_calibration


def _identity(record):
    return ObjectIdentity.from_record(record.record_id, record)


def scientific_projection(specification, allocation, calibration, frozen, assessment, adjudication, *, execution_plan, run_id, receipts, conditional_reasons, adjudication_task_id, statistical_task_id):
    """Check original arithmetic and retain every assigned adverse/nonuse row."""
    reasons = conditional_reasons(specification, allocation, assessment)
    calibration.__post_init__()
    frozen.__post_init__()
    expected_cal = allocation.unit_ids('calibration')
    ranked = split_upper_calibration(tuple(score for _, score, _ in calibration.scores), specification.calibration_alpha)
    matched = getattr(specification.measurement, 'is_matched', False)
    if matched and (not calibration.model_calibrations or assessment.amended_inference is None):
        raise PermissionError('PROTECTED_E3_READ_SEPARATE_MATCHED_CALIBRATION_AND_PRIMARY_TEST_REQUIRED')
    if ((calibration.specification, calibration.allocation) != (specification.identity, allocation.identity)
            or tuple(row[0] for row in calibration.scores) != expected_cal
            or (frozen.specification, frozen.allocation) != (specification.identity, allocation.identity)
            or frozen.calibration != _identity(calibration) or frozen.models != calibration.models
            or frozen.model_freeze != calibration.model_freeze or assessment.calibrated_freeze != _identity(frozen)
            or calibration.rank != ranked.rank
            or calibration.radius != (None if ranked.radius.is_infinite() else ranked.radius)):
        raise PermissionError('PROTECTED_E3_READ_COMPLETE_CALIBRATION_AND_FREEZE_REQUIRED')
    adjudication_task = adjudication_task_id(specification.identity, allocation.identity)
    assessment_task = statistical_task_id(specification.identity, allocation.identity, 'assess')
    receipt = receipts[adjudication_task]
    if (adjudication.run_id != run_id or adjudication.adjudication_task_id != adjudication_task
            or adjudication.execution_plan != execution_plan
            or adjudication.input_materialization_ids != receipt.input_materialization_ids
            or adjudication.output_logical_artifact_ids != tuple(row.logical_artifact_id for row in receipt.output_logical_artifacts)
            or adjudication.required_receipt_ids != (receipts[assessment_task].receipt_id,)
            or adjudication.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
            or adjudication.plumbing_only or adjudication.fixture_scope_id is not None
            or adjudication.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
            or adjudication.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or adjudication.evaluability is not AdjudicationEvaluability.UNEVALUABLE
            or adjudication.scientific_status is not ScientificStatus.UNEVALUABLE
            or adjudication.admission_status is not AdmissionStatus.UNEVALUABLE
            or adjudication.reason_codes != reasons):
        raise PermissionError('PROTECTED_E3_READ_EXACT_TERMINAL_ADJUDICATION_REQUIRED')
    return canonical_value({'scientific_status': adjudication.scientific_status.value,
        'admission_status': adjudication.admission_status.value, 'evaluability': adjudication.evaluability.value,
        'qualification': 'NOT_ESTABLISHED', 'conditional_criterion_met': assessment.criterion_met,
        'calibration_radius_kind': 'INFINITE' if calibration.radius is None else 'FINITE',
        'reason_codes': adjudication.reason_codes,
        'denominators': {'calibration': {'assigned_units': len(expected_cal),
            'usable_units': sum(score is not None for _, score, _ in calibration.scores),
            'units': expected_cal}, 'confirmation': {'assigned_units': len(assessment.decisions),
                'usable_units': assessment.usable_units, 'successes': assessment.successes,
                'units': tuple(row.unit_id for row in assessment.decisions)}},
        'calibration': calibration, 'assessment': assessment, 'adjudication': adjudication,
        **({'admission_owner': 'S0', 'separate_model_calibrations': calibration.model_calibrations,
            'amended_primary_test': assessment.amended_inference} if matched else {})})

