# SPDX-License-Identifier: MPL-2.0
"""Supported original physical-rate reduction, closed export and reconstruction."""

from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_records import PhysicalRateSelection, PhysicalRateEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_read import validate_physical_rate_inputs, read_physical_rates
from empirical_lawhood.domains.rubisco.rubisco_response.physical_gas_concentration import prepare_periodic_gas_concentration
from empirical_lawhood.api.domain_composition.rubisco_response.native_analysis_export import MEMBERS, export_native_observation_analysis, read_native_observation_analysis


def _text(report):
    lines = ['Conditional physical-rate assessment', '',
        'Every original path, competing exit, failed weight and cost remains in the complete source analysis.',
        'Whole-run draws remain shared across all paired conditions. Descendants and sites add no independent units.',
        'Unobserved causes remain unidentified. Computational loss is not independent censoring.',
        'Rate estimates require the stated constant-hazard model and actual selected numerical controls.',
        'Resampling intervals describe empirical conditional variation; they do not certify coverage or physical accuracy.', '']
    for key,row in report['cases'].items():
        lines.append(key+': '+row['conditional_rate_assessment'])
        for event,value in row['fit']['cause_rates_per_second'].items():
            lines.append('  '+event+': '+(value+' s^-1' if value is not None else 'UNIDENTIFIED'))
    lines.extend(('', 'Entry-ensemble, chemical-model, transport and biological admission remain separate requirements.', ''))
    return '\n'.join(lines).encode('utf-8')


def export_physical_rates(*, selection, sources, project_root, artifact_writer, output_relative_path):
    return export_native_observation_analysis(namespace='physical-rate',selection=selection,sources=sources,
        project_root=project_root,artifact_writer=artifact_writer,output_relative_path=output_relative_path,
        validate=validate_physical_rate_inputs,read=read_physical_rates,evidence_kind=PhysicalRateEvidence,render=_text)


def read_physical_rate_export(*, directory_relative_path, sources, artifact_writer):
    return read_native_observation_analysis(validate=validate_physical_rate_inputs, directory_relative_path=directory_relative_path,sources=sources,
        artifact_writer=artifact_writer,selection_kind=PhysicalRateSelection,evidence_kind=PhysicalRateEvidence,
        read=read_physical_rates,render=_text)


__all__ = ('MEMBERS','prepare_periodic_gas_concentration','validate_physical_rate_inputs','read_physical_rates',
    'export_physical_rates','read_physical_rate_export')
