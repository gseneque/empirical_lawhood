# SPDX-License-Identifier: MPL-2.0
"""Supported retained equilibrium analysis, closed export and independent reread."""

from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_records import EquilibriumReweightingEvidence, EquilibriumReweightingSelection
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_read import RetainedEquilibriumTrace, read_equilibrium_reweighting, validate_reweighting_inputs
from empirical_lawhood.api.domain_composition.rubisco_response.native_analysis_export import MEMBERS, export_native_observation_analysis, read_native_observation_analysis


def _text(report):
    statistics = report['statistics']
    lines = ['Conditional equilibrium free-energy analysis', '',
        f"Selected numerical sampling criteria: {statistics['selected_numerical_sampling_criteria']}.",
        f"Assigned traces: {report['assigned_traces']}; supplied original results: {report['supplied_results']}; complete windows: {report['complete_window_traces']}.",
        f"Assigned ensembles: {report['assigned_ensembles']}; declared dependence groups: {report['declared_dependence_groups']}.",
        'Signed free-energy contrasts (kJ/mol):']
    lines.extend(f'  {name}: {value if value is not None else "UNEVALUABLE"}'
        for name,value in zip(statistics['contrast_ids'], statistics['contrasts_kj_mol'], strict=True))
    bootstrap = statistics['bootstrap']
    lines.extend(['', f"Joint bootstrap draws retained: {bootstrap['retained_replicates']}/{bootstrap['requested_replicates']}; failed: {len(bootstrap['failed_replicates'])}.",
        'The readout retains all draws, signed contrasts, covariance and simultaneous conditional intervals.',
        'These estimates assume the declared stationary sampling and dependence model.',
        'Numerical diagnostics do not prove equilibration or the absence of hidden slow coordinates.',
        'Chemical accuracy, ensemble admission, physical rates and biological prediction remain UNEVALUABLE.',
        'Every original completion and cost remains in the trace census. No new native call occurred.', ''])
    return '\n'.join(lines).encode('utf-8')


def export_equilibrium_reweighting(*, selection, sources, project_root, artifact_writer, output_relative_path):
    return export_native_observation_analysis(namespace='equilibrium-reweighting', selection=selection, sources=sources,
        project_root=project_root, artifact_writer=artifact_writer, output_relative_path=output_relative_path,
        validate=validate_reweighting_inputs, read=read_equilibrium_reweighting,
        evidence_kind=EquilibriumReweightingEvidence, render=_text)


def read_equilibrium_reweighting_export(*, directory_relative_path, sources, artifact_writer):
    return read_native_observation_analysis(validate=validate_reweighting_inputs, directory_relative_path=directory_relative_path, sources=sources,
        artifact_writer=artifact_writer, selection_kind=EquilibriumReweightingSelection,
        evidence_kind=EquilibriumReweightingEvidence, read=read_equilibrium_reweighting, render=_text)


__all__ = ('MEMBERS', 'RetainedEquilibriumTrace', 'validate_reweighting_inputs', 'read_equilibrium_reweighting',
    'export_equilibrium_reweighting', 'read_equilibrium_reweighting_export')
