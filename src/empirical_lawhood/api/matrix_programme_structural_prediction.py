# SPDX-License-Identifier: MPL-2.0
"""Compose the selected descriptive comparison from authenticated phase reads."""
from contextlib import ExitStack

from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import (
    E4StructuralPredictionCase, E4MatchedRelationSelection, structural_prediction_comparison,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4DevelopmentProgramme
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PhaseProgramme
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes, canonical_value


def programme_structural_prediction(context, *, revision=None):
    """No acquisition, grant construction or phase advancement occurs here."""
    if type(context.design.e4_structure.prediction) is E4MatchedRelationSelection:
        return _frozen_relation(context, revision=revision)
    development = context.observations.get('e4.development')
    report = {} if development is None else development.report
    structure = report.get('scientific_result', report).get('structure')
    if not isinstance(structure, dict) or structure.get('scientific_completion') != 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS':
        return {'status': 'DEPENDENCIES_REQUIRED', 'required_phase': 'e4.development',
            'scope': 'FROZEN_DESCRIPTIVE_PHYSICAL_VERSUS_PHYSICAL_PLUS_STRUCTURE'}
    if 'original_programme' not in structure or 'prediction_cases' not in structure:
        raise PermissionError('completed structural phase omits its original programme or causal prediction cases')
    from .matrix_programme_products import _current_grants
    with ExitStack() as lifetime:
        # Reuse the delivery owner's current original grant checks. Model work
        # must not extend a reveal beyond its actual expiry or revocation.
        authorities = lifetime.enter_context(context.writer.read_context())
        current = _current_grants(context, authorities)
        decoded = {}
        for phase in ('e4.development', 'e4.calibration', 'e4.confirmation'):
            observation = context.observations.get(phase)
            if observation is None:
                continue
            structure = observation.report.get('scientific_result', observation.report).get('structure')
            if not isinstance(structure, dict) or structure.get('scientific_completion') != 'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS':
                continue
            if 'original_programme' not in structure or 'prediction_cases' not in structure:
                raise PermissionError('completed structural phase omits its original programme or causal prediction cases')
            def decode(value, kind):
                return decode_canonical_bytes(canonical_json_document_bytes(value), kind,
                    maximum_bytes=context.plan.specification.operations.metadata_budget.source_scan_bytes)
            kind = SelectedE3E4DevelopmentProgramme if phase == 'e4.development' else SelectedE4PhaseProgramme
            programme = decode(structure['original_programme'], kind)
            cases = tuple(decode(value, E4StructuralPredictionCase) for value in structure['prediction_cases'])
            if structure['assigned_groups'] != len(programme.group_ids) or structure['assigned_cases'] != len(cases):
                raise PermissionError('structural comparison changes the original complete assigned denominator')
            decoded[phase] = programme, cases
        evaluation = tuple((label, *decoded[phase]) for phase, label in
            (('e4.calibration', 'CALIBRATION'), ('e4.confirmation', 'CONFIRMATION')) if phase in decoded)
        result = structural_prediction_comparison(context.design.e4_structure.prediction, context.design.e4_revision,
            *decoded['e4.development'], evaluation=evaluation)
        current()
        return result


def _frozen_relation(context, *, revision=None):
    """Deliver the actual original fit and consumed CONF policies without refitting."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as methods
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PublicCalibration
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import relation_loss_readout
    from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
    from .matrix_researcher_programme_e4_lineage import programme_revision_read
    from .matrix_researcher_programme_lineage import _issued_e4_record
    from .matrix_programme_products import _current_grants
    observed = context.observations.get('e4.revision')
    scope = 'ACTUAL_FROZEN_SR_BR_WITH_ORIGINAL_CAL_NO_CONFIRMATION_SELECTION'
    if observed is None or not observed.complete:
        return {'status': 'DEPENDENCIES_REQUIRED', 'required_phase': 'e4.revision', 'scope': scope}
    with context.writer.read_context() as authorities:
        current = _current_grants(context, authorities)
        revision = programme_revision_read(context) if revision is None else revision
        decision, development, nomination, frozen = revision.decision, revision.development, revision.nomination, revision.frozen
        if (nomination.relation_fit is None
                or nomination.relation_fit.selection != context.design.e4_structure.prediction
                or decision.relation_fit != nomination.relation_fit.identity):
            raise PermissionError('programme relation report substitutes its actual original DEV fit or predeclared mathematics')
        methods.validate_frozen_revision(development, nomination, frozen)
        calibration, downstream, calibration_families = None, None, ()
        if (observed_cal := context.observations.get('e4.calibration')) is not None and observed_cal.complete:
            calibration, _ = _issued_e4_record(context, 'e4.calibration', methods.SelectedE4Calibration.SCHEMA)
            if calibration.relation_fit != decision.relation_fit or calibration.specification.frozen_models != frozen.identity:
                raise PermissionError('programme relation report substitutes its separate original CAL or frozen relation')
            programme = context.method_inputs('e4.calibration').plan.declaration.programme
            if calibration.specification.calibration_programme != programme.identity or calibration.group_ids != programme.group_ids:
                raise PermissionError('programme relation report changes the actual assigned CAL family census')
            family_by_group = {case.independent_group_id: case.family_id for case in programme.cases}
            calibration_families = tuple((family, sum(value == family for value in family_by_group.values()))
                for family in sorted(FOUR_FAMILY_PREPARATION_IDS))
        if (observed_conf := context.observations.get('e4.confirmation')) is not None and observed_conf.complete:
            downstream, _ = _issued_e4_record(context, 'e4.confirmation', methods.SelectedE4DownstreamNomination.SCHEMA)
            if (calibration is None or downstream.frozen_product.relation_fit != decision.relation_fit
                    or downstream.frozen_revision != frozen.identity or downstream.calibration != calibration.identity
                    or downstream.calibration_product != SelectedE4PublicCalibration.from_calibration(calibration,
                        record_id=downstream.calibration_product.record_id)):
                raise PermissionError('programme relation report changes its actual consumed CONF freeze or original CAL')
        confirmation = None if downstream is None else downstream.confirmation_product
        result = {'status': 'FROZEN_RELATION_RETAINED' if decision.fit_available else 'REQUIRED_MODEL_PREREQUISITE_FAILURE',
            'scope': scope, 'fit': nomination.relation_fit.to_document(), 'nomination': nomination.identity.to_document(),
            'freeze': frozen.to_document(), 'endpoint_fit_calls': nomination.endpoint_fit_calls,
            'calibration': None if calibration is None else {
                'original': calibration.identity.to_document(), 'assigned_group_ids': calibration.group_ids,
                'realised_family_group_counts': calibration_families,
                'separate_model_calibrations': canonical_value(calibration.model_calibrations)},
            'confirmation': None if confirmation is None else {
                'original': confirmation.identity.to_document(), 'primary_inference': canonical_value(confirmation.amended_inference),
                'group_decisions': canonical_value(confirmation.relation_decisions),
                'separate_model_coverage': canonical_value(confirmation.model_coverage),
                'realised_family_group_counts': tuple((family, sum(row.family_id == family
                    for row in confirmation.factorial_assessment.groups)) for family in sorted(FOUR_FAMILY_PREPARATION_IDS)),
                'physical_contrasts': confirmation.factorial_assessment.to_document(),
                'losses': canonical_value(relation_loss_readout(confirmation.relation_cases, confirmation.relation_decisions)),
                'unchanged_e3_reference_log_losses': canonical_value(confirmation.original_point_losses),
                'unchanged_e3_reference_duration_error_counts': canonical_value(confirmation.original_duration_error_counts)},
            'downstream_account': None if downstream is None else downstream.selected,
            'qualification': 'NOT_ESTABLISHED', 'new_native_contact_count': 0}
        if nomination.relation_fit.selection.is_curve_primary:
            from empirical_lawhood.adapters.methods.matrix_factor_response.curve_duration import (
                duration_diagnostic_summary, evaluation_median_K,
            )
            result['DEV_K_diagnostics'] = canonical_value(tuple((model.method_key, duration_diagnostic_summary(model))
                for model in nomination.relation_fit.models))
            if confirmation is not None:
                result['confirmation']['DEV_median_K'] = canonical_value(evaluation_median_K(
                    nomination.relation_fit.models[0], tuple(row.independent_group_id for row in confirmation.groups),
                    tuple((case.root_id, case.group_id, case.errors, not case.reasons)
                        for case in confirmation.relation_cases), coordinate_count=9))
        current()
        return result
