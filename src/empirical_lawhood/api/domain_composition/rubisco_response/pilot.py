# SPDX-License-Identifier: MPL-2.0
"""Supported retained-cost preparation and closed export, without native entry."""

from empirical_lawhood.domains.rubisco.rubisco_response.pilot_allocation import PilotAllocationEvidence, PilotAllocationRule
from empirical_lawhood.domains.rubisco.rubisco_response.pilot_allocation_read import read_pilot_allocation, validate_pilot_sources
from empirical_lawhood.api.domain_composition.rubisco_response.native_analysis_export import export_native_observation_analysis, read_native_observation_analysis


def _render(report):
    return ('Prospective Rubisco pilot cost selection\n'
        +'Disposition: '+report['disposition']+'\n'
        +'Candidate: '+str(report['selected_candidate'])+'\n'
        +'Original calibration cases: '+str(len(report['original_calibrations']))+'\n'
        +'The estimate grants no spending, scientific admission or native execution.\n').encode()


def export_pilot_allocation(*, selection, sources, project_root, artifact_writer, output_relative_path):
    return export_native_observation_analysis(namespace='pilot-cost', selection=selection, sources=sources,
        project_root=project_root, artifact_writer=artifact_writer, output_relative_path=output_relative_path,
        validate=validate_pilot_sources, read=read_pilot_allocation, evidence_kind=PilotAllocationEvidence, render=_render)


def read_pilot_allocation_export(*, directory_relative_path, sources, artifact_writer):
    return read_native_observation_analysis(validate=validate_pilot_sources, directory_relative_path=directory_relative_path, sources=sources,
        artifact_writer=artifact_writer, selection_kind=PilotAllocationRule,
        evidence_kind=PilotAllocationEvidence, read=read_pilot_allocation, render=_render)
