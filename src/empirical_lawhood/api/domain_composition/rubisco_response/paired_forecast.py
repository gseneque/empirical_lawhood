# SPDX-License-Identifier: MPL-2.0
"""Prepare, independently read and export conditional paired supplier joins."""

from dataclasses import replace

from empirical_lawhood.domains.rubisco.rubisco_response.paired_forecast_records import ForecastCase, ForecastOperand, ForecastRatePair, ForecastSupplier, PairedForecastEvidence, PairedForecastSelection
from empirical_lawhood.domains.rubisco.rubisco_response.paired_forecast_read import read_paired_forecast, validate_paired_forecast_inputs
from empirical_lawhood.api.domain_composition.rubisco_response.native_analysis_export import export_native_observation_analysis, read_native_observation_analysis


def prepare_paired_forecast(*, suppliers, cases, dependence_source, maximum_analysis_bytes, assumptions, sources):
    candidate = PairedForecastSelection('forecast.pending',suppliers,cases,dependence_source,maximum_analysis_bytes,assumptions)
    selected = replace(candidate,selection_id='forecast.'+candidate.fingerprint())
    validate_paired_forecast_inputs(selected,sources)
    return selected


def _text(report):
    lines = ['Conditional paired supplier forecast','',
        'Owner criteria: turnover ratio > 1 and specificity ratio >= 1.',
        'The full WT waiting interval is retained. No gain or confidence threshold is added.',
        'Supplier numerical criteria, physical admission and biological validity remain distinct.','']
    for name,row in report['cases'].items():
        lines.append(name+': conditional forecast '+row['conditional_forecast_status']+
            '; endpoint arithmetic '+row['owner_criteria']+'; supplier assessment '+row['supplier_assessment']+
            '; missing operands '+str(len(row['missing_operands'])))
    lines.extend(('', 'Joint point criteria: '+report['joint']['point_criteria']+'.',
        f"Joint realizations retained: {report['joint']['retained_replicates']}; incomplete: {len(report['joint']['failed_replicates'])}.",
        'Original supplier analyses retain all failures, unobserved alternatives, controls and original costs.',
        'Nested reports reference a single deduplicated original carrier census. Do not sum shared costs twice.',
        'Physical and biological admission: UNEVALUABLE.',''))
    return '\n'.join(lines).encode('utf-8')


def export_paired_forecast(*, selection, sources, project_root, artifact_writer, output_relative_path):
    return export_native_observation_analysis(namespace='paired-forecast',selection=selection,sources=sources,
        project_root=project_root,artifact_writer=artifact_writer,output_relative_path=output_relative_path,
        validate=validate_paired_forecast_inputs,read=read_paired_forecast,
        evidence_kind=PairedForecastEvidence,render=_text)


def read_paired_forecast_export(*, directory_relative_path, sources, artifact_writer):
    return read_native_observation_analysis(validate=validate_paired_forecast_inputs, directory_relative_path=directory_relative_path,sources=sources,
        artifact_writer=artifact_writer,selection_kind=PairedForecastSelection,evidence_kind=PairedForecastEvidence,
        read=read_paired_forecast,render=_text)


__all__ = ('ForecastCase','ForecastOperand','ForecastRatePair','ForecastSupplier','PairedForecastSelection',
    'prepare_paired_forecast','validate_paired_forecast_inputs','read_paired_forecast',
    'export_paired_forecast','read_paired_forecast_export')
