# SPDX-License-Identifier: MPL-2.0
"""Supported original first-passage read, export and independent reconstruction."""

from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import FirstPassageEvidence, FirstPassageSelection
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_read import RetainedFirstPassagePath, read_first_passages, validate_first_passage_inputs
from empirical_lawhood.domains.rubisco.rubisco_response.weighted_path_resampling import resample_weighted_paths, assess_weighted_resampling
from empirical_lawhood.api.domain_composition.rubisco_response.native_analysis_export import MEMBERS, export_native_observation_analysis, read_native_observation_analysis


def _text(report):
    lines = ['Conditional physical first-passage analysis', '',
        f"Assigned paths: {report['assigned_paths']}; supplied original results: {report['supplied_results']}.",
        f"Observed first events: {report['observed_events']}; intact horizon-censored paths: {report['horizon_censored_paths']}.",
        'Every original completion, failed attempt, cost and physical grid remains in the path census.',
        'Empirical bounds retain unobserved path values. They are not confidence intervals.',
        'No rate is inferred from a censored mean, an absent reverse event or a resampling step.',
        'Entry-ensemble validity, physical event definitions, step convergence and memorylessness require separate assessment.',
        'Gas concentration alone does not establish dilute association scaling.',
        'Biological predictive validity and independent biological units remain unestablished.', '']
    return '\n'.join(lines).encode('utf-8')


def export_first_passages(*, selection, sources, project_root, artifact_writer, output_relative_path):
    return export_native_observation_analysis(namespace='first-passage', selection=selection, sources=sources,
        project_root=project_root, artifact_writer=artifact_writer, output_relative_path=output_relative_path,
        validate=validate_first_passage_inputs, read=read_first_passages, evidence_kind=FirstPassageEvidence, render=_text)


def read_first_passage_export(*, directory_relative_path, sources, artifact_writer):
    return read_native_observation_analysis(validate=validate_first_passage_inputs, directory_relative_path=directory_relative_path, sources=sources,
        artifact_writer=artifact_writer, selection_kind=FirstPassageSelection, evidence_kind=FirstPassageEvidence,
        read=read_first_passages, render=_text)


__all__ = ('MEMBERS', 'RetainedFirstPassagePath', 'validate_first_passage_inputs', 'read_first_passages',
    'export_first_passages', 'read_first_passage_export', 'resample_weighted_paths', 'assess_weighted_resampling')
