# SPDX-License-Identifier: MPL-2.0
"""Consume required retained decisions independently of retrospective reports."""


def source_assessment(context, phase):
    """Authenticate the original source decision at its consuming boundary."""
    from .results import CampaignStatusRequest
    result = context.report(phase).get('scientific_result')
    if not isinstance(result, dict):
        _, _, authority, _, run, _ = context.authority(phase)
        report = context.service.read(directory=context.child_directory(phase),
            request=CampaignStatusRequest(run.run_plan_id), reveal_authority_id=authority.reveal_authority_id)
        result = report.get('scientific_result')
    if not isinstance(result, dict) or result.get('scientific_completion') != 'COMPLETE_SOURCE_INSTRUMENT_ASSESSMENT':
        raise PermissionError('programme entry requires its actual completed source instrument assessment')
    return result


def development_assessment(context):
    """Join complete E5 nomination inputs and receipts without array replay."""
    from .experiment_scientific_read import _development_runtime_context
    from .matrix_selected_development_scientific_read import read_development_result
    from .recursive_execution import _read_recursive_wave_with_retained_roots
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
    result = context.report('e5.development').get('scientific_result')
    if not isinstance(result, dict):
        def consume(**values):
            selected = _development_runtime_context(payloads=values['payloads'], draft=values['draft'],
                callback_name='read_development_result')
            if selected is None:
                raise PermissionError('programme nomination lacks its actual original development companion')
            _, specification, instance = selected
            if specification.identity != context.binding('e5.development').specification.identity:
                raise PermissionError('programme nomination substitutes its selected original specification')
            return read_development_result(specification=specification, instance=instance,
                decision_only=not scientific_reconstruction_enabled(), **values)
        report, _ = _read_recursive_wave_with_retained_roots(directory=context.child_directory('e5.development'),
            artifact_writer=context.writer, include_products=True,
            terminal_product_format='documents' if scientific_reconstruction_enabled() else 'compact',
            _scientific_consumer=consume)
        result = report[0].get('scientific_result')
    if not isinstance(result, dict) or not (
            result.get('scientific_completion') == 'COMPLETE_ASSIGNED_E5_DEVELOPMENT_CENSUS'
            or result.get('decision_consumption') == 'COMPLETE_RETAINED_E5_NOMINATION'
            and result.get('scientific_completion') == 'DEFERRED_TO_FULL_READ'
            and result.get('scientific_reconstruction') == 'OFF'):
        raise PermissionError('programme nomination requires its complete actual retained E5 decision')
    return result
